#setup script for py2exe


from distutils.core import setup
import py2exe
   
setup(console=['run.py'])



a = Analysis(['run.py'],
             pathex=['C:\\Users\\User\\Desktop\\impulse'],
             binaries=[],
             datas=[
                ('C:\Python39\Lib\site-packages\dash', 'dash'),
                ('C:\Python39\Lib\site-packages\dash_bootstrap_components', 'dash_bootstrap_components'),
                ('C:\Python39\Lib\site-packages\dash_core_components', 'dash_core_components'),
                ('C:\Python39\Lib\site-packages\dash_html_components', 'dash_html_components'),
                ('C:\Python39\Lib\site-packages\dash_table', 'dash_table')
            ],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

