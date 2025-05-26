# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

version = "2.3.2"
project_root = Path('.').resolve()
block_cipher = None

a = Analysis(
    ['impulse.py'],
    pathex=[str(project_root)],
    binaries=[
        ('/Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages/pyaudio/__init__.py', '.'),
    ],

    datas=[
        ('assets', 'assets'),
        ('i', 'i'),
        ('/Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages/dash_daq/package-info.json', 'dash_daq'),
        ('/Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages/dash_daq/metadata.json', 'dash_daq'),
        ('/Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages/dash_daq/dash_daq.min.js', 'dash_daq'),
    ],
    hiddenimports=[
        'dash_daq',
        'pyaudio',
        'serial',
        'scipy._lib.array_api_compat.numpy.fft',
    ] + collect_submodules('dash'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Impulse',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/favicon.icns',
)

app = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='Impulse.app',
    icon='assets/favicon.icns',
    bundle_identifier='com.beejewel.impulse',
    info_plist={
        "CFBundleIdentifier": "com.beejewel.impulse",
        "CFBundleName": "Impulse",
        "CFBundleDisplayName": "Impulse",
        f"CFBundleShortVersionString": version,
        "CFBundleVersion": version,
        "NSMicrophoneUsageDescription": "Required for audio analysis",
        "LSMinimumSystemVersion": "11.0",
    }
)
