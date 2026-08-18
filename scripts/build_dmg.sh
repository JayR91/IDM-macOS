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

# Bundle ffmpeg (from this build machine's own install -- not downloaded
# from the internet here) so video downloads that need to merge separate
# video/audio streams work out of the box, without end users needing
# Homebrew or ffmpeg installed themselves. video_capture.py looks for it
# next to the frozen executable via yt-dlp's ffmpeg_location option.
FFMPEG_BIN="$(command -v ffmpeg || true)"
if [ -n "$FFMPEG_BIN" ]; then
  echo "==> Bundling ffmpeg from $FFMPEG_BIN"
  cp "$FFMPEG_BIN" "dist/$APP_NAME.app/Contents/MacOS/ffmpeg"
else
  echo "==> WARNING: ffmpeg not found on this machine (brew install ffmpeg)." >&2
  echo "    Building without it -- video merging will fail for anyone" >&2
  echo "    who installs this app unless they separately install ffmpeg." >&2
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
