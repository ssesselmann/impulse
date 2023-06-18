from setuptools import setup
import PyInstaller.__main__ as pyi

setup(
    name='impulse',
    version='1.0',
    # Exclude 'windows' option and specify 'console' for PyInstaller
    
    options={
        'pyinstaller': {
            'console': ['impulse.py'],  # Specify the script to be bundled as a console application
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
    }
)

# Add PyInstaller build command
pyi.run([
    '--name=impulse',  # Specify the name of the bundled executable
    '--onedir',  # Bundle the executable into a single directory
    '--clean',  # Clean any previous build files
    'impulse.py'  # Specify the script to be bundled
])
