"""Core update logic - no GUI dependencies, fully testable."""
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
import zipfile
from typing import Optional, Tuple, Callable

from launcher.config import (
    API_URL, GAME_EXE, GAME_SCRIPT, VERSION_FILE, SAVES_DIR,
    STAGING_DIR, BACKUP_DIR, REQUEST_TIMEOUT, MAX_RETRIES,
    MIN_LAUNCHER_VERSION, LAUNCHER_VERSION, UPDATE_MANIFEST_URL,
    LATEST_DOWNLOAD_URL, RETRY_DELAY,
)


_ssl_ctx = None


def get_ssl_context():
    """HTTPS doğrulama bağlamı (bir kez kurulur, sonra tekrar kullanılır).

    Sade `urlopen` işletim sisteminin *ortam* güvenine dayanıyordu ve bazı
    kullanıcı makinelerinde zincir tamamlanamıyordu:
    `CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`.
    İki yaygın sebep var ve farklı çözümler gerektiriyorlar:

    1. Kök sertifika o makinede hiç yok. Windows kökleri *talep üzerine*
       CryptoAPI ile indirir; OpenSSL bunu asla tetiklemez. Bu yüzden tarayıcı
       çalışırken launcher aynı PC'de patlar.
    2. Antivirüs / proxy / VPN bağlantıyı kendi köküyle yeniden imzalar. O kök
       yalnızca Windows deposunda bulunur, gömülü bir CA paketinde bulunmaz.

    Bu yüzden sıra önemli: önce `truststore` (Windows'un kendi doğrulayıcısı,
    ikisini de kapsar), sonra gömülü `certifi` paketi, en sonda Python'un
    varsayılanı.
    """
    global _ssl_ctx
    if _ssl_ctx is not None:
        return _ssl_ctx

    import ssl

    try:
        import truststore
        _ssl_ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        return _ssl_ctx
    except Exception:
        pass

    try:
        import certifi
        _ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        return _ssl_ctx
    except Exception:
        pass

    _ssl_ctx = ssl.create_default_context()
    return _ssl_ctx


_system_getaddrinfo = socket.getaddrinfo


def _ipv4_first_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    # Bazı ağlarda AAAA (IPv6) DNS sorgusu yanıtsız kalıp her istekte ~10+ sn
    # bekletiyor; urllib timeout'u DNS aşamasını kapsamadığı için kontrol
    # zaman aşımına uğruyor. Önce IPv4 dene, olmazsa sistem davranışına dön.
    if family in (0, socket.AF_UNSPEC):
        try:
            return _system_getaddrinfo(
                host, port, socket.AF_INET, type, proto, flags
            )
        except socket.gaierror:
            pass
    return _system_getaddrinfo(host, port, family, type, proto, flags)


socket.getaddrinfo = _ipv4_first_getaddrinfo


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


def _request_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            'Accept': 'application/json',
            'User-Agent': f'BoxheadLauncher/{LAUNCHER_VERSION}',
        },
    )
    with urllib.request.urlopen(
            req, timeout=REQUEST_TIMEOUT, context=get_ssl_context()) as resp:
        return json.loads(resp.read().decode('utf-8-sig'))


def _release_from_manifest(manifest: dict) -> dict:
    filename = str(manifest.get('filename', '')).strip()
    version = str(manifest.get('version', '')).lstrip('v').strip()
    if not version or not filename.lower().endswith('.zip') or 'win64' not in filename.lower():
        raise ValueError('Güncelleme manifesti geçersiz veya win64 paketi eksik')

    safe_filename = urllib.parse.quote(filename)
    return {
        'version': version,
        'download_url': f'{LATEST_DOWNLOAD_URL}/{safe_filename}',
        'size': int(manifest.get('size', 0) or 0),
        'sha256': str(manifest.get('sha256', '')).strip().lower(),
        'min_launcher_version': manifest.get('min_launcher_version', '1.0.0'),
    }


def _fetch_release_from_api() -> dict:
    """Eski sürümlerde update.json yoksa GitHub API üzerinden geriye uyumlu kontrol."""
    data = _request_json(API_URL)
    tag = data.get('tag_name', '').lstrip('v')
    assets = {a['name']: a for a in data.get('assets', [])}
    zip_asset = next(
        (asset for name, asset in assets.items()
         if name.lower().endswith('.zip') and 'win64' in name.lower()),
        None,
    )
    if not zip_asset:
        raise RuntimeError(f'No win64 ZIP found in release {tag}')
    return {
        'version': tag,
        'download_url': zip_asset['browser_download_url'],
        'size': zip_asset.get('size', 0),
        'sha256': '',
        'min_launcher_version': '1.0.0',
    }


def fetch_latest_release() -> dict:
    """Fetch latest release info from the single-file release manifest.
    Returns dict with keys: version, download_url, sha256, size, min_launcher_version.
    Raises RuntimeError on failure.
    """
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            return _release_from_manifest(_request_json(UPDATE_MANIFEST_URL))
        except urllib.error.HTTPError as e:
            # update.json kullanılmayan eski release'ler için API'ye yalnızca
            # kesin 404 durumunda düş; ağ kapalıyken ikinci bir uzun yol deneme.
            if e.code == 404:
                try:
                    return _fetch_release_from_api()
                except Exception as api_error:
                    last_error = api_error
                    break
            last_error = e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_error = e
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            # Sunucuya ulaşıldı ama veri bozuksa tekrar beklemek faydasızdır.
            last_error = e
            break
        except Exception as e:
            # Bazı Windows proxy/antivirüs katmanları standart URLError yerine
            # genel hata yükseltebilir; aynı kısa retry bütçesini uygula.
            last_error = e

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)

    raise RuntimeError(
        f'Güncelleme bilgisi alınamadı ({MAX_RETRIES} deneme): {last_error}'
    )


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
        with urllib.request.urlopen(
                req, timeout=60, context=get_ssl_context()) as resp:
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
