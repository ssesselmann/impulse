from setuptools import setup

setup(
    name='impulse',
    version='1.0',
    py_modules=[
        'distortionchecker',
        'audio_spectrum.py',
        'functions', 
        'launcher', 
        'pulsecatcher', 
        'run',
        'server', 
        'shapecatcher', 
        'tab1', 
        'tab2', 
        'tab3', 
        'tab4',
        'tab5'
    ],
    windows=['run.py'],  # Use 'windows' instead of 'app' for py2exe
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
        }
    },
    setup_requires=['py2exe'],
)
