# setup_mac.py

# This is a setup.py script for mac generated by py2applet

# Usage: python3 setup.py py2app

from setuptools import setup, find_packages

setup(
    name='impulse',
    version='1.0',

    packages=find_packages(),
    install_requires=['pyaudio'],
    app=['impulse.py'],
    options={
        'py2app': {
            'argv_emulation': True,
            'iconfile': 'favicon',
            'plist': {
                'CFBundleName': 'Impulse',
                'CFBundleDisplayName': 'Impulse',
                'NSMicrophoneUsageDescription': 'Impulse requires microphone access for data analysis'
            },
            'includes': [
                'dash',
                'dash_daq',
                'datetime',
                'flask',
                'jason',
                'numpy',
                'pandas',
                'pathlib',
                'plotly',
                'wave',
                'pyaudio',
                'scipy',
                'requests'
                'logging',
                'threading',
                'platform'
            ],
            'resources': [
                ('i', 'i')  # Include the 'i' folder and its contents
            ]
        }
    },
    setup_requires=['py2app'],
)
