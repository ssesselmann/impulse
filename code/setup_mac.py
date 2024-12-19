from setuptools import setup, find_packages

setup(
    name='impulse',
    version='2.2.5',
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
        'serial',  # for serial.tools.list_ports
    ],
    app=['impulse.py'],
    options={
        'py2app': {
            'argv_emulation': True,
            'iconfile': 'favicon.icns',  # Ensure this is a valid .icns file
            'plist': {
                'CFBundleName': 'Impulse',
                'CFBundleDisplayName': 'Impulse',
                'NSMicrophoneUsageDescription': 'Impulse requires microphone access for data analysis'
            },
            'includes': [
                'audio_spectrum',
                'csv',
                'dash',
                'dash_bootstrap_components',
                'dash_daq',
                'datetime',
                'glob',
                'json',
                'logging',
                'math',
                'numpy',
                'os',
                'pandas',
                'platform',
                'plotly.graph_objects',
                'pyaudio',
                'queue',
                'requests',
                'scipy.io.wavfile',
                'serial.tools.list_ports',
                'shutil',
                'subprocess',
                'sys',
                'threading',
                'time',
                'warnings',
                'wave',
                'webbrowser'
            ],
            'resources': ["i", "assets"],  # Ensure these paths exist and are correctly set up
        }
    },
    setup_requires=['py2app'],
)
