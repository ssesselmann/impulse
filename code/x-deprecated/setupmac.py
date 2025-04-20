from setuptools import setup, find_packages
import os
import sys

# Universal architecture flags for Apple Silicon + Intel
if sys.platform == 'darwin':
    os.environ['ARCHFLAGS'] = '-arch x86_64 -arch arm64'

setup(
    name='impulse',
    version='2.3.0',
    packages=find_packages(),
    install_requires=[
        'dash',
        'dash_bootstrap_components',
        'dash_daq',
        'numpy',
        'pandas',
        'plotly',
        'pyaudio',
        'Pillow',
        'requests',
        'scipy',
        'serial',
        'chardet',
        'jaraco.text',
        'packaging'
    ],
    app=['impulse.py'],
    data_files=[],
    options={
        'py2app': {
            
            # Critical security settings
            'argv_emulation': False,
            'semi_standalone': False,
            'compressed': False,
            'optimize': 0,
            'strip': False,  # Preserve signatures
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
                'sys',
                'os',
                'codecs',
                'encodings',
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
                'typing_extensions',
                'packaging'
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
                'LSMinimumSystemVersion': '11.0',
                'NSMicrophoneUsageDescription': 'Required for audio analysis',
                'PyRuntimeLocations': [
                    '@executable_path/../Frameworks/Python.framework/Versions/3.10/Python'
                ]
            },
        }
    },
    setup_requires=['py2app'],
)