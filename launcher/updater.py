"""Core update logic - no GUI dependencies, fully testable."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error
import zipfile
from typing import Optional, Tuple, Callable

from launcher.config import (
    API_URL, GAME_EXE, GAME_SCRIPT, VERSION_FILE, SAVES_DIR,
    STAGING_DIR, BACKUP_DIR, REQUEST_TIMEOUT, MAX_RETRIES,
    MIN_LAUNCHER_VERSION, LAUNCHER_VERSION,
)


def get_local_version() -> str:
    """Read local version from version.txt."""
    try:
        with open(VERSION_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except (FileNotFoundError, OSError):
        return '0.0.0'


def parse_semver(v: str) -> Tuple[int, int, int]:
    """Parse a version string like '1.6.0' or 'v1.6.0' into (major, minor, patch)."""
    parts = v.lstrip('v').split('.')
    nums = []
    for p in parts[:3]:
        try:
            nums.append(int(p))
        except ValueError:
            nums.append(0)
    while len(nums) < 3:
        nums.append(0)
    return (nums[0], nums[1], nums[2])


def compare_versions(a: str, b: str) -> int:
    """Compare two semver strings. Returns -1, 0, or 1."""
    ta, tb = parse_semver(a), parse_semver(b)
    if ta < tb:
        return -1
    if ta > tb:
        return 1
    return 0


def fetch_latest_release() -> dict:
    """Fetch latest release info from GitHub API.
    Returns dict with keys: version, download_url, sha256, size, min_launcher_version.
    Raises RuntimeError on failure.
    """
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                API_URL,
                headers={
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'BoxheadLauncher/1.0',
                },
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                data = json.loads(resp.read().decode('utf-8'))

            tag = data.get('tag_name', '').lstrip('v')
            assets = {a['name']: a for a in data.get('assets', [])}

            # Fetch update.json manifest if present
            update_manifest = None
            if 'update.json' in assets:
                manifest_url = assets['update.json']['browser_download_url']
                req2 = urllib.request.Request(
                    manifest_url,
                    headers={'User-Agent': 'BoxheadLauncher/1.0'},
                )
                with urllib.request.urlopen(req2, timeout=REQUEST_TIMEOUT) as resp2:
                    update_manifest = json.loads(resp2.read().decode('utf-8'))

            # Find the win64 ZIP asset
            zip_asset = None
            for name, asset in assets.items():
                if name.endswith('.zip') and 'win64' in name:
                    zip_asset = asset
                    break
            if not zip_asset and update_manifest:
                fname = update_manifest.get('filename', '')
                if fname in assets:
                    zip_asset = assets[fname]

            if not zip_asset:
                raise RuntimeError(f'No win64 ZIP found in release {tag}')

            return {
                'version': update_manifest.get('version', tag) if update_manifest else tag,
                'download_url': zip_asset['browser_download_url'],
                'size': zip_asset.get('size', 0),
                'sha256': update_manifest.get('sha256', '') if update_manifest else '',
                'min_launcher_version': (
                    update_manifest.get('min_launcher_version', '1.0.0')
                    if update_manifest else '1.0.0'
                ),
            }

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(
                f'Failed to fetch release after {MAX_RETRIES} attempts: {e}'
            )
    raise RuntimeError('Unreachable')


def sha256_file(path: str) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def validate_zip_entries(zip_path: str, target_dir: str) -> None:
    """Check all ZIP entries resolve within target_dir.
    Raises ValueError on path traversal attempt.
    """
    abs_target = os.path.realpath(target_dir)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for info in zf.infolist():
            member_path = os.path.realpath(
                os.path.join(target_dir, info.filename)
            )
            if (
                not member_path.startswith(abs_target + os.sep)
                and member_path != abs_target
            ):
                raise ValueError(
                    f'ZIP path traversal detected: {info.filename}'
                )


def is_game_running() -> bool:
    """Check if the game process is running (Windows only)."""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', f'IMAGENAME eq {GAME_EXE}', '/NH'],
            capture_output=True, text=True, timeout=5,
        )
        return GAME_EXE.lower() in result.stdout.lower()
    except (subprocess.SubprocessError, OSError):
        return False


def download_file(
    url: str,
    dest: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> None:
    """Download url to dest via a temporary .part file."""
    part_path = dest + '.part'
    try:
        req = urllib.request.Request(
            url, headers={'User-Agent': 'BoxheadLauncher/1.0'}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get('Content-Length', 0))
            downloaded = 0
            with open(part_path, 'wb') as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)
        os.replace(part_path, dest)
    except Exception:
        if os.path.exists(part_path):
            os.remove(part_path)
        raise


def perform_update(zip_path: str, install_dir: str) -> None:
    """Extract update to staging, backup old installation, apply atomically.
    Rolls back on any error. Never touches saves/ directory.
    """
    staging = os.path.join(install_dir, STAGING_DIR)
    backup = os.path.join(install_dir, BACKUP_DIR)

    # Clean previous staging/backup
    for d in [staging, backup]:
        if os.path.exists(d):
            shutil.rmtree(d)

    try:
        # Validate ZIP for path traversal
        validate_zip_entries(zip_path, staging)

        # Extract to staging
        os.makedirs(staging, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(staging)

        # Backup current files (exclude saves, staging, backup)
        os.makedirs(backup, exist_ok=True)
        excluded = {
            SAVES_DIR, STAGING_DIR, BACKUP_DIR,
            os.path.basename(zip_path),
        }
        for item in os.listdir(install_dir):
            if item in excluded or item.endswith('.part'):
                continue
            src = os.path.join(install_dir, item)
            dst = os.path.join(backup, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        # Apply staged files to install dir
        for item in os.listdir(staging):
            src = os.path.join(staging, item)
            dst = os.path.join(install_dir, item)
            if item == SAVES_DIR:
                continue
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            elif os.path.exists(dst):
                os.remove(dst)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        # Cleanup on success
        shutil.rmtree(staging, ignore_errors=True)
        shutil.rmtree(backup, ignore_errors=True)
        if os.path.exists(zip_path):
            os.remove(zip_path)

    except Exception:
        # Rollback: restore from backup
        if os.path.exists(backup):
            for item in os.listdir(backup):
                src = os.path.join(backup, item)
                dst = os.path.join(install_dir, item)
                try:
                    if os.path.isdir(dst):
                        shutil.rmtree(dst)
                    elif os.path.exists(dst):
                        os.remove(dst)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                except OSError:
                    pass
            shutil.rmtree(backup, ignore_errors=True)
        shutil.rmtree(staging, ignore_errors=True)
        raise


def launch_game(install_dir: str) -> None:
    """Launch the game executable or script."""
    exe_path = os.path.join(install_dir, GAME_EXE)
    script_path = os.path.join(install_dir, GAME_SCRIPT)

    if os.path.exists(exe_path):
        subprocess.Popen([exe_path], cwd=install_dir)
    elif os.path.exists(script_path):
        subprocess.Popen([sys.executable, script_path], cwd=install_dir)
    else:
        raise FileNotFoundError('Game executable not found')
