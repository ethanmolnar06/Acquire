# -*- mode: python ; coding: utf-8 -*-

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true")
options = parser.parse_args()

added_files = [
         ('fonts', 'fonts'),
         ]

a = Analysis( # type: ignore
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure) # type: ignore

if options.debug:
    exe = EXE( # type: ignore
        pyz,
        a.scripts,
        exclude_binaries=True,
        name='Acquire',
        icon="assets/acquire_boxart_glitching.ico",
        debug=True,
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
    coll = COLLECT( # type: ignore
        exe,
        a.binaries,
        a.datas,
        name='Acquire_debug',
    )
else:
    exe = EXE( # type: ignore
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        name='Acquire',
        icon="assets/acquire_boxart_glitching.ico",
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
