# IDM — Download Manager

A desktop download manager inspired by Internet Download Manager (IDM), built in Python.
Tested components: segmented downloads, pause/resume, resume-after-restart, retry/error
handling, and bandwidth throttling (see "What's been tested" below).

## Features

- **Multi-threaded / segmented downloads** — splits a file into up to 32 parallel segments
  when the server supports HTTP range requests, for faster downloads.
- **Pause / resume** — pauses instantly, mid-chunk, even while bandwidth-throttled.
- **Resume after app restart** — progress is checkpointed to a small `.idmstate.json`
  sidecar file next to each download, so closing the app and relaunching resumes cleanly.
- **Automatic retry** — each segment retries independently with exponential backoff
  (default 5 retries) before the whole download is marked as failed.
- **Bandwidth throttling** — a global speed cap (KB/s) shared fairly across all active
  downloads and segments, adjustable live with a numeric field or slider.
- **Focus Guard** — unique vs commercial IDM: pauses downloads on battery or
  Low Power Mode, crawls at 256 KB/s while you are using the Mac, and returns
  to full speed once the machine is idle and plugged in. Toggle it in the toolbar.
- **macOS integration** — a live Dock badge, menu-bar drop target, automatic light/dark
  appearance, native completion notifications, and the Glass system chime.
- **Scheduling and organisation** — queue a URL for a future time (blank scheduling time
  means the next midnight); completed files are sorted into Videos, Documents, Zips,
  Audio, Images, or Other folders inside `~/Downloads/IDMClone`.
- **Video/stream capture** — powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp), the
  actively maintained open-source extractor used by many real download tools, for
  YouTube and hundreds of other sites.
- **Browser integration** — a Chrome extension (Manifest V3) that can:
  - intercept the browser's native downloads and hand them to this app instead
    (so you get segmented/resumable downloading for regular browser downloads too)
  - send the current tab, or right-clicked links/videos, to the app via
    "Download with IDM"

## Requirements

- Python 3.9+
- `pip install -r requirements.txt` (installs `requests`, `flask`, `yt-dlp`)
- On Linux, Tkinter needs the system package if it isn't already present:
  `sudo apt install python3-tk`
- For video downloads that need merging (video+audio), `ffmpeg` should be on your PATH.

## Running the app

```bash
pip install -r requirements.txt
python main.py
```

This opens the desktop window and starts a local server on
`http://127.0.0.1:27182` for the browser extension to talk to (only listens on
localhost — nothing external can reach it).

### Using the app

- **+ Add URL** — paste a direct file link, pick a save location and number of
  segments (default 8).
- **+ Add Video/Stream** — paste a video page URL (YouTube, etc.); this uses yt-dlp
  in the background and saves into `~/Downloads/IDMClone`.
- Select a row to **Pause / Resume / Cancel / Remove / Open Folder**.
- Set a global **speed limit** in KB/s (0 = unlimited) and click Apply.
- Turn on **Focus Guard** to pause on battery and slow down while you are at the keyboard.
- **Schedule URL** opens a future-time queue timer. Use a blank time for midnight.
- On macOS, drag an `http`/`https` link onto the `⇩` menu-bar icon to queue it without
  opening the window. The Dock badge shows a single download's percentage or the active
  download count; it clears on completion.

### Building the macOS app

Install the dependencies, then run:

```bash
PYINSTALLER_CONFIG_DIR=/private/tmp/idmclone-pyinstaller-cache \
  pyinstaller --noconfirm "IDM.spec"
```

The resulting `dist/IDM.app` supports Dock URL delivery via macOS argv emulation;
links can be dropped onto its Dock icon after the bundle is launched. The menu-bar drop
target works while running from source as well. `setup.py` remains available for py2app
builds if you prefer that packaging flow.

## Installing the browser extension

1. Open `chrome://extensions` (or `edge://extensions` for Edge).
2. Turn on **Developer mode** (top right).
3. Click **Load unpacked** and select the `browser_extension/` folder.
4. Make sure the desktop app (`main.py`) is running — the extension only works
   while it's open and listening on port 27182.
5. Click the extension icon to:
   - toggle **"Intercept browser downloads"** — when on, downloads you'd normally
     see in Chrome's download bar get sent to IDM instead
   - **"Send this page/video to IDM"** — manually send the current tab
   - or right-click any link/video/audio element → **"Download with IDM"**

## Project structure

```
idm_clone/
  engine.py            # core download engine (segments, resume, retry, throttling)
  queue_manager.py      # manages concurrent downloads + global speed limit
  focus_guard.py        # battery / idle-aware Focus Guard (not in commercial IDM)
  video_capture.py      # yt-dlp wrapper for video/stream downloads
  server.py             # local Flask server for the browser extension
  gui.py                # Tkinter desktop UI
  main.py               # entry point — wires everything together
  requirements.txt
  browser_extension/
    manifest.json
    background.js       # intercepts downloads, adds right-click menu
    popup.html / popup.js
```

## What's been tested

I built and ran an actual test suite against a local HTTP server (not just written
the code) before handing this over:

- **Segmented download integrity** — downloaded a 5MB file across 6 parallel
  segments and verified the SHA-256 checksum matched the source exactly.
- **Pause/resume correctness** — paused mid-download (including mid-throttle-sleep,
  which exposed and fixed a real bug), confirmed byte count froze while paused,
  then resumed and verified the final checksum.
- **Resume after simulated app restart** — paused a download, then created a
  *brand new* task object pointed at the same file (simulating closing and
  reopening the app), and confirmed it picked up from the saved state and
  finished with a correct checksum.
- **Bandwidth throttling** — capped a download at 1MB/s and confirmed it took
  the expected minimum time rather than finishing instantly.
- **Retry/error handling** — requested a nonexistent file and confirmed it
  correctly surfaces as an error after retries rather than hanging or crashing.
- **GUI integration** — ran the actual Tkinter app headlessly, queued a real
  download through it, and confirmed the download completed and the on-screen
  row updated correctly. This also caught and fixed a cross-thread Tkinter
  crash (background threads now only push events onto a thread-safe queue;
  the Tk main loop is the only thing that touches widgets).
- **Local server for the extension** — verified `/ping`, `/add` for a regular
  file, and `/add` for a recognized video URL all respond correctly.

**Not tested here** (no real network access / browser in this environment):
- The Chrome extension loaded in an actual browser.
- yt-dlp against real, live video sites.

## Notes & limitations

- Segmented downloading requires the server to support HTTP range requests
  (`Accept-Ranges: bytes`); if it doesn't, the engine falls back to a single
  connection automatically.
- Only use the video-capture feature on content you have the right to
  download — respect the terms of service of whatever site you're pulling from.
- This is a functional starting point, not a polished consumer product — e.g.
  there's no installer, no system tray integration, and the GUI is intentionally
  simple. Good next steps if you want to keep extending it: a proper icon set
  for the extension, a settings dialog for default segment count/retries, and
  packaging the app with PyInstaller for a double-clickable executable.
