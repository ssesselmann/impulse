from setuptools import setup, find_packages

setup(
    name='impulse',
    version='2.1.8',
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
                'json',
                'numpy',
                'pandas',
                'pathlib',
                'plotly',
                'wave',
                'pyaudio',
                'scipy',
                'requests',
                'threading',
                'platform'
            ],
            'resources': ["i","assets"], 
        }
    },
    setup_requires=['py2app'],
)
