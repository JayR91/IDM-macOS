"""dmgbuild settings for the installer DMG (see scripts/build_dmg.sh).

A plain `hdiutil create -srcfolder ...` DMG has no window size or icon
layout set at all -- Finder falls back to defaults that often stack the
app and the Applications shortcut on top of each other or open a tiny
window, making it look like nothing is draggable. dmgbuild constructs a
proper .DS_Store directly, so the standard "drag app onto Applications"
layout actually renders as one, with no Finder automation/permissions
needed to build it.
"""

import os

app_name = os.environ["DMG_APP_NAME"]
app_path = os.environ["DMG_APP_PATH"]

format = "UDZO"
files = [app_path]
symlinks = {"Applications": "/Applications"}
icon_locations = {
    f"{app_name}.app": (140, 120),
    "Applications": (360, 120),
}
window_rect = ((200, 200), (500, 300))
icon_size = 100
default_view = "icon-view"
show_icon_preview = True
include_icon_view_settings = True
