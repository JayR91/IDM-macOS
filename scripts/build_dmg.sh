#!/bin/bash
# Builds "IDM Clone.app" with PyInstaller and packages it into a
# double-clickable .dmg installer. Used both for local builds and by
# .github/workflows/release.yml on every version tag push.
set -euo pipefail

cd "$(dirname "$0")/.."

APP_NAME="IDM Clone"
DMG_NAME="IDM Clone Installer.dmg"
STAGING_DIR="dist/dmg_staging"

echo "==> Building '$APP_NAME.app' with PyInstaller"
rm -rf build dist
pyinstaller --noconfirm "$APP_NAME.spec"

if [ ! -d "dist/$APP_NAME.app" ]; then
  echo "PyInstaller did not produce dist/$APP_NAME.app" >&2
  exit 1
fi

echo "==> Staging DMG contents"
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"
cp -R "dist/$APP_NAME.app" "$STAGING_DIR/"
ln -s /Applications "$STAGING_DIR/Applications"

echo "==> Creating $DMG_NAME"
rm -f "$DMG_NAME"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGING_DIR" -ov -format UDZO "$DMG_NAME"

echo "==> Done: $DMG_NAME"
