# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

repo_root = os.path.abspath(os.path.join(SPECPATH, '..', '..'))

hiddenimports = collect_submodules('backend')

datas = [
    (os.path.join(repo_root, 'frontend'), 'frontend'),
    (os.path.join(repo_root, 'agent_config.json'), '.'),
    (os.path.join(repo_root, 'config-example.json'), '.'),
]

if os.path.exists(os.path.join(repo_root, 'qwen-code')):
    datas.append((os.path.join(repo_root, 'qwen-code'), 'qwen-code'))

a = Analysis(
    ['backend_entry.py'],
    pathex=[repo_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter.test', 'unittest', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='flashy-backend',
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
