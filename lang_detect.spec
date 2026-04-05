# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('samples/input_samples.txt', 'samples')]
binaries = []
hiddenimports = ['lingua', 'fasttext', 'flask', 'docx', 'lxml', 'lxml.etree']

tmp_ret = collect_all('lingua_language_detector')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret2 = collect_all('docx')
datas += tmp_ret2[0]; binaries += tmp_ret2[1]; hiddenimports += tmp_ret2[2]

tmp_ret3 = collect_all('lxml')
datas += tmp_ret3[0]; binaries += tmp_ret3[1]; hiddenimports += tmp_ret3[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='lang_detect',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
