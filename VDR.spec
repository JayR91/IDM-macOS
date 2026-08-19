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
    name='VDR',
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
    name='VDR',
)
app = BUNDLE(
    coll,
    name='VDR.app',
    icon='AppIcon.icns',
    bundle_identifier='com.vdr.app',
    info_plist={
        'CFBundleDisplayName': 'VDR',
        # No Dock icon, no app menu bar, doesn't show in Cmd+Tab -- a
        # background/menu-bar-only app, like Slack's or Dropbox's tray
        # presence. The status-bar icon (macos_integration.py) is the only
        # UI when the window is closed; "Quit VDR" there is the real exit.
        'LSUIElement': True,
        'CFBundleURLTypes': [
            {
                'CFBundleURLName': 'Download URL',
                'CFBundleURLSchemes': ['http', 'https'],
            },
            {
                # Lets the browser extension launch the app when it isn't
                # running, the same way zoommtg:// or slack:// do -- the
                # extension navigates to vdr://launch and macOS starts
                # (or foregrounds) this app in response. This scheme must stay
                # in sync with APP_LAUNCH_URL in browser_extension/background.js
                # and launchAppViaLink() in content.js.
                'CFBundleURLName': 'VDR Launch',
                'CFBundleURLSchemes': ['vdr'],
            },
        ],
    },
)
