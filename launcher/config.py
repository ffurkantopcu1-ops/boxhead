"""Launcher configuration - single source for repo and paths."""
import os

GITHUB_OWNER = "ffurkantopcu1-ops"
GITHUB_REPO = "boxhead"
API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
LATEST_DOWNLOAD_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest/download"
UPDATE_MANIFEST_URL = f"{LATEST_DOWNLOAD_URL}/update.json"

GAME_EXE = "Boxhead.exe"
GAME_SCRIPT = "main.py"
VERSION_FILE = "version.txt"
SAVES_DIR = "saves"
STAGING_DIR = "_update_staging"
BACKUP_DIR = "_update_backup"

REQUEST_TIMEOUT = 4
MAX_RETRIES = 1
RETRY_DELAY = 0.35
# Bu iki değer release workflow'u tarafından update.json'a yazılır
# (elle sabit yazılıyordu ve mekanizma hiç çalışmıyordu).
#
# MIN_LAUNCHER_VERSION: bundan eskisi oyunu başlatamaz (sert kilit).
#   Yalnızca launcher'sız çalışmayacak bir değişiklikte artır — artırmak
#   mevcut TÜM oyuncuları elle indirmeye zorlar.
# LAUNCHER_VERSION: bu yayındaki Launcher.exe'nin sürümü. Oyuncu daha
#   eskisini kullanıyorsa engellenmeden bilgilendirilir.
MIN_LAUNCHER_VERSION = "1.0.0"
# 1.1.0: görev çubuğu düğmesi düzeltmesi (v1.13.1) + uygulama ikonu (v1.13.2)
LAUNCHER_VERSION = "1.1.0"
