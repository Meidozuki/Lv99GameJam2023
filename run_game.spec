# -*- mode: python ; coding: utf-8 -*-

from glob import glob

block_cipher = None


a = Analysis(
    ['run_game.py'],
    pathex=[r'D:\jupyter\GameJam2023\VBAO\Lib_VBao\python'],
    binaries=[],
    datas=[('local/font/x16y32pxGridGazer.ttf','local/font/')] + \
        [(png, 'local/img') for png in glob("local/img/*.png")]
        ,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='run_game',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='run_game',
)
