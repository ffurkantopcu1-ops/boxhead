# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['launcher\\main.py'],
    pathex=['.'],
    binaries=[],
    # Launcher, oyun kurulmadan once de calisir; gotik arayuz parcalarini
    # (413 KB) kendi icine gomer, yoksa klasik widget arayuzune duser.
    datas=[
        ('assets/ui/gothic/launcher', 'assets/ui/gothic/launcher'),
        ('assets/boxhead_icon.png', 'assets'),
        ('assets/boxhead_icon.ico', 'assets'),
    ],
    # HTTPS guven zinciri. Ikisi de get_ssl_context icinde tembel import
    # edildigi icin PyInstaller'in statik analizi bulamiyor; certifi hook'u da
    # ancak import gorulurse cacert.pem'i pakete koyar.
    hiddenimports=['truststore', 'certifi'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    icon='assets/boxhead_icon.ico',
    codesign_identity=None,
    entitlements_file=None,
)
