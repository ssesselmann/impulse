# -*- mode: python ; coding: utf-8 -*-
# This file is used for creating a Windows executable package impulse.exe
# From the command line enter >> pyinstaller impulse.spec


a = Analysis(
    ['impulse.py'],
    pathex=[],
    binaries=[],
    datas=[
    ('C:\\Users\\bee1812a\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\dash_daq\\package-info.json', 'dash_daq'),
    ('C:\\Users\\bee1812a\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\dash_daq\\metadata.json', 'dash_daq'),
    ('C:\\Users\\bee1812a\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\dash_daq\\dash_daq.min.js', 'dash_daq'),
    ('i', 'i'), 
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
    a.binaries,
    a.datas,
    exclude_binaries=False,
    name='impulse',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=True,
    icon='favicon.ico',
    manifest='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
        <compatibility>
            <application>
                <!-- Ensure compatibility with Windows 7 and above -->
                <supportedOS Id="{e2011457-1546-43c5-a5fe-008deee3d3f0}"/>
                <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
            </application>
        </compatibility>
    </assembly>'''
)
# exe = EXE(
#     pyz,
#     a.scripts,
#     a.binaries,  # Include binaries in the EXE for onefile mode
#     a.datas,
#     exclude_binaries=False,  # Change this to False for onefile mode
#     name='impulse',
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=True,
#     console=True,
#     icon='favicon.ico',  
#     # Additional parameters like disable_windowed_traceback, argv_emulation, etc., can be added if needed
# )