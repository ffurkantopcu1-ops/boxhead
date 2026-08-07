# Boxhead 2.0: Release & Deployment Guide

## Table of Contents
- [Repository Setup](#repository-setup)
- [Creating a Release](#creating-a-release)
- [GitHub Actions Permissions](#github-actions-permissions)
- [Launcher Configuration](#launcher-configuration)
- [Local Build](#local-build)
- [Rollback Procedure](#rollback-procedure)
- [Code Signing](#code-signing)

---

## Repository Setup

### First-Time Push

```powershell
# 1. Initialize git in the project directory
cd C:\Users\PC\Desktop\py\boxhead\Pygame_Versiyonu
git init

# 2. Add remote
git remote add origin https://github.com/ffurkantopcu1-ops/boxhead-updates.git

# 3. Stage files (saves/ and .exe excluded via .gitignore)
git add .

# 4. Initial commit
git commit -m "feat: initial commit with CI/CD and launcher"

# 5. Push to main
git branch -M main
git push -u origin main
```

> **Note:** Make sure `.gitignore` is committed first. It excludes `saves/`, `.exe` files,
> `__pycache__/`, `build/`, `dist/`, and other artifacts.

---

## Creating a Release

### Step 1: Update Version

Edit `version.txt` to contain the new version (e.g., `1.7.0`):

```powershell
Set-Content -Path version.txt -Value "1.7.0" -NoNewline -Encoding utf8
```

### Step 2: Commit the Version Change

```powershell
git add version.txt
git commit -m "release: bump version to 1.7.0"
git push
```

### Step 3: Create and Push Tag

```powershell
git tag v1.7.0
git push origin v1.7.0
```

This triggers the Release workflow which will:
1. Run all CI checks (syntax, import smoke test, unit tests)
2. Validate `version.txt` matches the tag
3. Build `Boxhead.exe` with PyInstaller
4. Build the standalone `Launcher.exe`
5. Package into `Boxhead-1.7.0-win64.zip`
6. Generate SHA-256 checksum
7. Create `update.json` manifest
8. Publish a GitHub Release with all assets

The latest launcher always has this stable direct-download URL:

https://github.com/ffurkantopcu1-ops/boxhead-updates/releases/latest/download/Launcher.exe

### Step 4: Verify

Go to https://github.com/ffurkantopcu1-ops/boxhead-updates/releases and confirm the
release was created with the correct assets.

---

## GitHub Actions Permissions

The workflows use minimal permissions:

| Workflow | Permission | Reason |
|----------|-----------|--------|
| `ci.yml` | `contents: read` | Only reads source code |
| `release.yml` (ci job) | `contents: read` | Runs CI checks |
| `release.yml` (release job) | `contents: write` | Creates GitHub Release |

### Required Repository Settings

1. Go to **Settings → Actions → General**
2. Under **Workflow permissions**, select **Read and write permissions**
3. Check **Allow GitHub Actions to create and approve pull requests** (optional)

---

## Launcher Configuration

The launcher reads its configuration from `launcher/config.py`:

```python
GITHUB_OWNER = "ffurkantopcu1-ops"
GITHUB_REPO = "boxhead-updates"
```

To point the launcher at a different repository, update these values.

### How the Launcher Works

1. Queries GitHub API for the latest release
2. Downloads `update.json` manifest from release assets
3. Compares remote version with local `version.txt` using SemVer
4. If update available:
   - Downloads ZIP to a `.part` temp file
   - Verifies SHA-256 checksum
   - Validates ZIP entries (path traversal protection)
   - Extracts to `_update_staging/`
   - Backs up current files to `_update_backup/`
   - Applies update atomically
   - Rolls back on any error
5. `saves/` directory is **never** touched during updates

### Running the Launcher

```powershell
# From source
python -m launcher.main

# Or directly
python launcher/main.py
```

---

## Local Build

### Prerequisites

```powershell
pip install -r requirements-dev.txt
```

### Build Game

```powershell
pyinstaller Boxhead.spec --noconfirm
# Output: dist/Boxhead.exe
```

### Build Launcher

```powershell
pyinstaller Boxhead_Launcher.spec --noconfirm
# Output: dist/Launcher.exe
```

### Package Manually

```powershell
$ver = (Get-Content version.txt -Raw).Trim()
$zip = "Boxhead-$ver-win64.zip"

New-Item -ItemType Directory -Path release_staging -Force
Copy-Item dist/Boxhead.exe release_staging/
Copy-Item -Recurse assets release_staging/assets
Copy-Item -Recurse sounds release_staging/sounds
Copy-Item version.txt release_staging/

Compress-Archive -Path release_staging/* -DestinationPath $zip -Force
(Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()

Remove-Item -Recurse release_staging
```

---

## Rollback Procedure

### Automatic (Launcher)

If an update fails mid-application, the launcher automatically restores from `_update_backup/`.

### Manual (GitHub)

1. Go to **Releases** page
2. Delete the broken release
3. Users with the broken version can re-download the previous release

### Manual (Git Tag)

```powershell
# Delete remote tag
git push origin --delete v1.7.0

# Delete local tag
git tag -d v1.7.0

# Revert version.txt
Set-Content -Path version.txt -Value "1.6.0" -NoNewline -Encoding utf8
git add version.txt
git commit -m "revert: roll back to 1.6.0"
git push
```

---

## Code Signing

Currently, the built `.exe` files are **not code-signed**. Windows SmartScreen may
show a warning on first run.

### Where to Add Code Signing

1. **In `Boxhead.spec`**: Set `codesign_identity` parameter in the `EXE()` call
2. **In `release.yml`**: Add a step after PyInstaller build:
   ```yaml
   - name: Sign executable
     run: signtool sign /f cert.pfx /p ${{ secrets.CERT_PASSWORD }} dist/Boxhead.exe
   ```
3. Store the certificate as a GitHub Actions secret (Base64-encoded PFX)

### Recommended Providers
- **Azure Trusted Signing** (free tier available)
- **SignPath** (free for open source)
- **DigiCert** / **Sectigo** (paid)
