# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('liewa/liewa_cli/recources','liewa/liewa_cli/recources'),
        ('liewa/liewa_gui/icon.png','liewa/liewa_gui'),
        ('LICENSE','.'),
        ('NOTICE.md','.'),
        ('THIRD_PARTY_NOTICES.md','.'),
        ('ASSET_SOURCES.md','.'),
        ('ACKNOWLEDGEMENTS.md','.'),
    ],
    hiddenimports=[
        'bs4',
        'soupsieve',      # bs4 的依赖，必须加上
        'PIL',
        'requests',
        'numpy',          # 你的项目用了 numpy
        'cv2',            # opencv-python
        'PyQt5',          # 你的项目用了 PyQt5
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'yaml',
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
    [],
    exclude_binaries=True,
    name='EwaGEO',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EwaGEO',
)
app = BUNDLE(
        coll,
        name='EwaGEO.app',
        icon='icon.ico',
        bundle_identifier=None
)
