#!/usr/bin/env python3
"""Produce per-browser builds of the VDR Connector extension.

`browser_extension/` is the shared source and its manifest.json is the
Chromium one, so it can be loaded there unpacked with no warnings.

Chromium and Firefox disagree on two MV3 details, and each complains about
the other's spelling:

  * background: Chromium wants `service_worker`; Firefox does not support
    service workers in MV3 and wants `scripts`. Chromium warns
    "'background.scripts' requires manifest version of 2 or lower".
  * extension id: Firefox needs `browser_specific_settings.gecko.id` for a
    stable id; Chromium warns "Unrecognized manifest key".

Rather than ship one manifest that warns in both, this writes a Firefox
flavour into dist/ with those two keys swapped.
"""
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "browser_extension"
OUT = ROOT / "dist" / "extension-firefox"

# Chromium records the on-disk path of an unpacked extension and disables it
# outright if that path ever moves -- so loading it straight out of a checkout
# means renaming or relocating the repo silently breaks the extension (and the
# floating button just stops working). Installing a copy somewhere stable and
# loading *that* keeps it working no matter what happens to the source tree.
INSTALL = pathlib.Path.home() / "Library" / "Application Support" / "VDR"

GECKO = {
    "gecko": {
        "id": "vdr-connector@vdr-macos.app",
        "strict_min_version": "109.0",
    }
}


IGNORE = shutil.ignore_patterns("__pycache__", ".DS_Store")


def _firefox_manifest() -> str:
    manifest = json.loads((SRC / "manifest.json").read_text())
    manifest["background"] = {"scripts": ["background.js"]}
    manifest["browser_specific_settings"] = GECKO
    return json.dumps(manifest, indent=2) + "\n"


def _sync(dest: pathlib.Path, firefox: bool) -> pathlib.Path:
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC, dest, ignore=IGNORE)
    if firefox:
        (dest / "manifest.json").write_text(_firefox_manifest())
    return dest


def main() -> None:
    _sync(OUT, firefox=True)
    chrome_install = _sync(INSTALL / "extension-chrome", firefox=False)
    firefox_install = _sync(INSTALL / "extension-firefox", firefox=True)

    print("Load these paths in the browser (they survive moving/renaming the repo):")
    print(f"  Chromium : {chrome_install}")
    print(f"  Firefox  : {firefox_install / 'manifest.json'}")
    print(f"\nBuild-tree copy of the Firefox flavour: {OUT}")


if __name__ == "__main__":
    main()
