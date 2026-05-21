# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ["../microchop_desktop_app.py"],
    pathex=[".."],
    binaries=[],
    datas=[],
    hiddenimports=[
        "librosa",
        "mido",
        "numpy",
        "PySide6",
        "soundfile",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Melodic Microchop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Melodic Microchop",
)

app = BUNDLE(
    coll,
    name="Melodic Microchop.app",
    icon=None,
    bundle_identifier="com.raphaelmalikian.melodicmicrochop",
)
