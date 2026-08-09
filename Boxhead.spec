# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Collect data files
datas = [
    ('assets', 'assets'),
    ('sounds', 'sounds'),
    ('data', 'data'),
    ('version.txt', '.'),
]

# Hidden imports for dynamic modules
hiddenimports = [
    'entities.warrior_logic',
    'entities.minion',
    'entities.boss',
    'entities.enemy',
    'entities.player',
    'entities.projectile',
    'entities.ground_item',
    'logic.game_logic',
    'logic.card_system',
    'logic.inventory_manager',
    'logic.item_system',
    'logic.save_manager',
    'logic.quest_system',
    'logic.synergy_system',
    'logic.status_effects',
    'logic.crystal_shop',
    'logic.version',
    'scenes.menu_scene',
    'scenes.class_select_scene',
    'scenes.game_scene',
    'scenes.base_scene',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Boxhead',
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
