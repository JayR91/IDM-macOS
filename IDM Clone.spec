# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='IDM Clone',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    # Receives web links dropped on the Dock icon in the frozen macOS app.
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='IDM Clone',
)
app = BUNDLE(
    coll,
    name='IDM Clone.app',
    icon='AppIcon.icns',
    bundle_identifier='com.idmclone.app',
    info_plist={
        'CFBundleDisplayName': 'IDM Clone',
        'CFBundleURLTypes': [{
            'CFBundleURLName': 'Download URL',
            'CFBundleURLSchemes': ['http', 'https'],
        }],
    },
)
