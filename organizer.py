"""Destination selection and post-download file categorisation."""

import os
import shutil


CATEGORY_EXTENSIONS = {
    "Videos": {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".mpg", ".mpeg"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".epub"},
    "Zips": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".dmg", ".pkg"},
    "Audio": {".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg"},
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".svg"},
}


def _safe_basename(name: str) -> str:
    """Strip any directory components and reject '.'/'..'/empty, so a
    caller-supplied filename (e.g. derived from a URL's last path segment)
    can never place a file outside the category folder it's meant for --
    defense in depth even though today's only callers already sanitize
    first."""
    name = os.path.basename(name or "")
    return name if name not in ("", ".", "..") else "download"


def category_for(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    for category, extensions in CATEGORY_EXTENSIONS.items():
        if ext in extensions:
            return category
    return "Other"


def dedupe_path(path: str) -> str:
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    index = 1
    while os.path.exists(f"{base} ({index}){ext}"):
        index += 1
    return f"{base} ({index}){ext}"


def categorized_destination(download_root: str, filename: str) -> str:
    """Return a safe path in a category folder, creating it if necessary."""
    filename = _safe_basename(filename)
    directory = os.path.join(download_root, category_for(filename))
    os.makedirs(directory, exist_ok=True)
    return dedupe_path(os.path.join(directory, filename))


def organize_completed_file(path: str, download_root: str) -> str:
    """Move a completed file into its category unless it is already there."""
    if not path or not os.path.isfile(path):
        return path
    target_dir = os.path.join(download_root, category_for(path))
    if os.path.abspath(os.path.dirname(path)) == os.path.abspath(target_dir):
        return path
    os.makedirs(target_dir, exist_ok=True)
    target = dedupe_path(os.path.join(target_dir, os.path.basename(path)))
    shutil.move(path, target)
    return target
