# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# 收集 esptool 的数据文件（包括 stub flasher JSON 文件）
esptool_datas = collect_data_files('esptool')

a = Analysis(
    ['esp32_flasher.py'],
    pathex=[],
    binaries=[],
    datas=[('config.json', '.')] + esptool_datas,  # 包含配置文件和 esptool 数据文件
    hiddenimports=[
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'esptool',
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AAHUB_Firmware_Flasher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标文件，可以设置为 'icon.ico'
)
