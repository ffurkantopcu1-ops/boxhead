"""Launcher configuration - single source for repo and paths."""
import os

GITHUB_OWNER = "ffurkantopcu1-ops"
GITHUB_REPO = "boxhead"
API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

GAME_EXE = "Boxhead.exe"
GAME_SCRIPT = "main.py"
VERSION_FILE = "version.txt"
SAVES_DIR = "saves"
STAGING_DIR = "_update_staging"
BACKUP_DIR = "_update_backup"

REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
MIN_LAUNCHER_VERSION = "1.0.0"
LAUNCHER_VERSION = "1.0.0"
