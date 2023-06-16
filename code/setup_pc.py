from setuptools import setup
import py2exe

setup(
    name='impulse',
    version='1.0',
    windows=['impulse.py'],  # Use 'windows' instead of 'app' for py2exe
    options={
        'py2exe': {
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
                'requests',
                'simpleaudio'
            ],
            'bundle_files': 3,  # Modify this option based on your needs
            'compressed': True,
            'optimize': 2
        }
    },
    data_files=[
        ('', ['favicon.ico']),  # Include any additional files you need
        ('i', 'i')  # Include the 'i' folder and its contents
    ],
)
