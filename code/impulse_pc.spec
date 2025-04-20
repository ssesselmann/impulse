# -*- mode: python ; coding: utf-8 -*-
# This file is used for creating a Windows executable package impulse.exe
# From the command line enter >> pyinstaller impulse.spec

a = Analysis(
    ['impulse.py'],
    pathex=[],
    binaries=[
        ('C:\\Users\\bee1812a\\AppData\\Local\\Programs\\Python\\Python310\\Lib\\site-packages\\pyaudio\\_portaudio.cp310-win_amd64.pyd', '.'),
    ],
    datas=[
        ('C:\\Users\\bee1812a\\AppData\\Local\\Programs\\Python\\Python310\\Lib\\site-packages\\dash_daq\\package-info.json', 'dash_daq'),
        ('C:\\Users\\bee1812a\\AppData\\Local\\Programs\\Python\\Python310\\Lib\\site-packages\\dash_daq\\metadata.json', 'dash_daq'),
        ('C:\\Users\\bee1812a\\AppData\\Local\\Programs\\Python\\Python310\\Lib\\site-packages\\dash_daq\\dash_daq.min.js', 'dash_daq'),
        ('i', 'i'),
        ('assets', 'assets'),  # Include the CSS folder
    ],
    hiddenimports=['dash_daq', 'pyaudio', 'serial', 'scipy._lib.array_api_compat.numpy.fft'],
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
    console=False,
    icon='favicon.ico', 

)
