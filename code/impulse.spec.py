# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['impulse.py'],
    pathex=[],
    binaries=[],
    datas=[
    ('C:\\Users\\bee1812a\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\dash_daq\\package-info.json', 'dash_daq'),
    ('C:\\Users\\bee1812a\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\dash_daq\\metadata.json', 'dash_daq'),
    ('C:\\Users\\bee1812a\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\dash_daq\\dash_daq.min.js', 'dash_daq'),
    ],

    hiddenimports=['dash_daq'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='impulse',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='impulse',
)
