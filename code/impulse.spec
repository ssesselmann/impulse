# This file is used with pyinstaller for creating a Windows executable package impulse.exe
# Usage: from the command line enter >> pyinstaller impulse.spec
# The program will generate an exe file.

import os

# Determine the absolute path to the 'i' directory
base_dir = os.path.abspath(os.getcwd())
i_dir = os.path.join(base_dir, 'i')

a = Analysis(
    ['impulse.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('C:\\Users\\bee1812a\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\dash_daq\\package-info.json', 'dash_daq'),
        ('C:\\Users\\bee1812a\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\dash_daq\\metadata.json', 'dash_daq'),
        ('C:\\Users\\bee1812a\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\dash_daq\\dash_daq.min.js', 'dash_daq'),
        (i_dir, 'i')
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
    a.binaries,  # Include binaries in the EXE for onefile mode
    a.datas,
    exclude_binaries=False,  # Change this to False for onefile mode
    name='impulse',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon='favicon.ico',  
    # Additional parameters like disable_windowed_traceback, argv_emulation, etc., can be added if needed
)
