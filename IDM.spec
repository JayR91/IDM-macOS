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
    name='IDM',
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
    name='IDM',
)
app = BUNDLE(
    coll,
    name='IDM.app',
    icon='AppIcon.icns',
    bundle_identifier='com.idmclone.app',
    info_plist={
        'CFBundleDisplayName': 'IDM',
        # No Dock icon, no app menu bar, doesn't show in Cmd+Tab -- a
        # background/menu-bar-only app, like Slack's or Dropbox's tray
        # presence. The status-bar icon (macos_integration.py) is the only
        # UI when the window is closed; "Quit IDM" there is the real exit.
        'LSUIElement': True,
        'CFBundleURLTypes': [
            {
                'CFBundleURLName': 'Download URL',
                'CFBundleURLSchemes': ['http', 'https'],
            },
            {
                # Lets the browser extension launch the app when it isn't
                # running, the same way zoommtg:// or slack:// do -- the
                # extension navigates to idmclone://launch and macOS starts
                # (or foregrounds) this app in response. Scheme name kept
                # as-is even after the "IDM Clone" -> "IDM" rename since
                # users may have already granted it OS-level permission.
                'CFBundleURLName': 'IDM Launch',
                'CFBundleURLSchemes': ['idmclone'],
            },
        ],
    },
)
