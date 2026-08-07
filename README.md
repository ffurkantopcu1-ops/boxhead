# Boxhead 2.0: Native Evolution

Top-down arena action game built with Python and Pygame.

## Quick Start

### Play from Source
```powershell
pip install -r requirements.txt
python main.py
```

### Use the Launcher (Auto-Update)
```powershell
python launcher/main.py
```

The launcher automatically checks for updates from GitHub Releases, downloads and
verifies them with SHA-256 checksums, and applies them safely without touching your
save files.

## Project Structure

```
├── main.py                 # Game entry point
├── version.txt             # Single source of truth for version (SemVer)
├── launcher/               # Auto-update launcher (Tkinter)
│   ├── config.py           # GitHub repo settings
│   ├── updater.py          # Core update logic (no GUI)
│   └── main.py             # Tkinter GUI
├── logic/                  # Game systems
├── entities/               # Game entities (player, enemies, etc.)
├── scenes/                 # UI screens
├── assets/                 # Sprites and images
├── sounds/                 # Audio files
├── saves/                  # User save data (never committed)
├── tests/                  # Unit tests
├── .github/workflows/      # CI/CD pipelines
│   ├── ci.yml              # Lint + test on push/PR
│   └── release.yml         # Build + release on tag push
├── Boxhead.spec            # PyInstaller build config
├── requirements.txt        # Runtime dependencies
├── requirements-dev.txt    # Build dependencies
└── RELEASE.md              # Detailed release guide
```

## Releasing a New Version

```powershell
# 1. Update version
Set-Content -Path version.txt -Value "1.7.0" -NoNewline -Encoding utf8

# 2. Commit
git add version.txt
git commit -m "release: v1.7.0"
git push

# 3. Tag and push
git tag v1.7.0
git push origin v1.7.0
```

GitHub Actions will automatically build, package, and publish the release.

See [RELEASE.md](RELEASE.md) for detailed instructions including rollback procedures.

## Running Tests

```powershell
pip install pytest
python -m pytest tests/ -v
```

## License

Private project. All rights reserved.
