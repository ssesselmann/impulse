from setuptools import setup, find_packages
import os
import sys

# Universal architecture flags for Apple Silicon + Intel
if sys.platform == 'darwin':
    os.environ['ARCHFLAGS'] = '-arch x86_64 -arch arm64'

setup(
    name='impulse',
    version='3.0.0',
    packages=find_packages(),
    install_requires=[
        'dash',
        'dash_bootstrap_components',
        'dash_daq',
        'numpy',
        'pandas',
        'plotly',
        'pyaudio',
        'requests',
        'scipy',
        'serial',
        'chardet'
    ],
    app=['impulse.py'],
    data_files=[],
    options={
        'py2app': {
            # Critical security settings
            'argv_emulation': False,
            'compressed': False,
            'optimize': 0,
            'strip': False,  # Preserve signatures
            
            # Resource handling
            'iconfile': 'assets/favicon.icns',
            'resources': [
                'assets',
                'i'
            ],
            
            # Dependency control
            'packages': [
                'pyaudio',  # Explicitly bundle PortAudio
                'PIL'       # For image lib dependencies
            ],
            'includes': [
                'unittest',
                'audio_spectrum',
                'dash',
                'dash_bootstrap_components',
                'dash_daq',
                'numpy',
                'pandas',
                'plotly.graph_objects',
                'scipy.io.wavfile',
                'serial.tools.list_ports',
                'selenium.webdriver'  # For selenium-manager
            ],
            'excludes': [
                'tkinter',
                'matplotlib',
                'test',
                'unittest',
                'pandas.tests',
                'numpy.testing'
            ],
            
            # Notarization requirements
            'plist': {
                'CFBundleIdentifier': 'com.beejewel.impulse',
                'CFBundleName': 'Impulse',
                'CFBundleDisplayName': 'Impulse',
                'LSRequiresNativeExecution': True,
                'LSMinimumSystemVersion': '12.0',  # Monterey+
                'NSMicrophoneUsageDescription': 'Required for audio analysis',
                'NSBonjourServices': ['_impulse._tcp'],  # If using networking
            },
            
            # Framework linking (Homebrew locations)
            'frameworks': [
                '/opt/homebrew/opt/portaudio/lib/libportaudio.dylib'
            ],
        }
    },
    setup_requires=['py2app'],
)