# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files


block_cipher = None

# Collecting the data required for the validation
datas = [
    ('./app/schema/*', './app/schema/'),
]
datas += collect_data_files('openapi_spec_validator')
datas += collect_data_files('openapi_schema_validator')

a = Analysis(['gui.py'],
             pathex=['.'],
             binaries=[],
             datas=datas,
             hiddenimports=[
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='msr-endorser',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon='app/resources/mcp.ico')
