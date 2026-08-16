"""Build a double-clickable macOS app with: python setup.py py2app."""
from setuptools import setup

APP = ["main.py"]
OPTIONS = {
    "argv_emulation": True,
    "plist": {
        "CFBundleName": "IDM Clone",
        "CFBundleDisplayName": "IDM Clone",
        "CFBundleIdentifier": "com.idmclone.app",
        "CFBundleURLTypes": [{"CFBundleURLName": "Download URL", "CFBundleURLSchemes": ["http", "https"]}],
    },
}
setup(app=APP, options={"py2app": OPTIONS}, setup_requires=["py2app"])
