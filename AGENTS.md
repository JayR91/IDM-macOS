# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## What this is

VDR ("Video Downloader") is a desktop download manager built in Python: a
Tkinter GUI, a segmented/resumable HTTP download engine, yt-dlp-based video capture, a local Flask
server for a companion Chrome extension, and macOS-specific integration (Dock badge, native
notifications, a menu-bar URL drop target, and a "Focus Guard" that adapts download behavior to
battery/idle state).

**Note:** `laser_wars/` is a separate, unrelated turn-based strategy game living in this same
directory — it is not part of the download manager and has its own `README.md`/`requirements.txt`.
Do not conflate the two when asked to work on "this project."

## Commands

```bash
# Setup
pip install -r requirements.txt      # requests, flask, yt-dlp (+ optional macOS: pyobjc, py2app, pyinstaller)

# Run
python main.py                       # opens the Tk window + starts the local server on :27182

# Build a double-clickable macOS .app (either flow works; the repo has configs for both)
PYINSTALLER_CONFIG_DIR=/private/tmp/vdr-pyinstaller-cache \
  pyinstaller --noconfirm "VDR.spec"
python setup.py py2app                # alternative: py2app packaging
```

There is no automated test suite, linter, or formatter configured in this repo. The README's
"What's been tested" section documents manual/ad-hoc verification (segmented-download checksum
integrity, pause/resume byte-freeze correctness, resume-after-restart, throttling, retry/error
handling) rather than a `pytest` suite — there's nothing to invoke for "run the tests."

To exercise engine/queue behavior directly (e.g. for regression-testing pause/resume), the most
reliable approach used in this repo's history is a standalone script that imports `QueueManager`
directly and drives `pause()`/`resume()`/`cancel()` against a real local file server (Flask +
`send_file(..., conditional=True)` gives working `Accept-Ranges` support) rather than a public
test endpoint, which tends to be flaky/rate-limited.

## Architecture

**Threading model is the load-bearing constraint.** `gui.py`'s `App` follows a strict rule:
background threads (download segment threads, the per-task monitor thread, video-download threads,
Focus Guard's polling thread) *never* touch Tk widgets directly. They only push `(kind, payload)`
tuples onto `App._events` (a `queue.Queue`); only `_drain_events()`/`_refresh()`, driven by
`root.after()` polling on the main thread, touch widgets. This was a deliberate fix for a real
cross-thread Tkinter crash — preserve it for any new async work.

**Two independent download pipelines share one `Status` enum and one Treeview:**

- **Regular file downloads** — `engine.DownloadTask` does real segmented HTTP: probes the URL for
  `Content-Length`/`Accept-Ranges`, splits into up to 32 segments, downloads each in its own thread
  with independent exponential-backoff retry, throttles through a shared `TokenBucket`, and
  checkpoints progress to a `<dest>.vdrstate.json` sidecar so a fresh `DownloadTask` pointed at the
  same path resumes correctly (used both for app-restart resume and for Focus-Guard-triggered
  pause/release). `pause()` is a true instant freeze (clears a `threading.Event` the segment loops
  block on, mid-chunk).
- **Video/stream downloads** — `gui.VideoTask` wraps `video_capture.download_video()` (yt-dlp) and
  duck-types the same interface (`status`, `bytes_downloaded()`, `pause/resume/cancel`) so it can
  sit in the same Treeview and go through the same `QueueManager`-adjacent code paths, but the
  mechanics are different: yt-dlp has no live pause API, so `pause()` raises `video_capture.
  DownloadPaused` from inside the `progress_hook`/`postprocessor_hook` to abort the transfer, and
  `resume()` just re-invokes `download_video()` on the same URL — yt-dlp's default fragment-resume
  behavior picks it back up rather than restarting from zero. `task.dest_path` is only trustworthy
  once a `postprocessor_hook` reports the final merged filepath; `progress_hooks` alone only ever
  see each fragment's temp filename (e.g. `...f251.webm`), which yt-dlp deletes after merging.

**`queue_manager.QueueManager`** owns the task list, concurrency limit, and the shared
`TokenBucket`. It also owns Focus Guard integration: `apply_focus_policy()` takes the effective
minimum of the user's speed limit and Focus Guard's crawl cap, and calls `hold_for_focus()` /
`release_from_focus()` on every task when the policy flips to/from `POLICY_HOLD`.

**`focus_guard.FocusGuard`** polls macOS battery/idle state every 3s via `pmset`/`ioreg` subprocess
calls and derives one of four policies (`off` / `full` / `active` (crawl at 256 KB/s) / `battery`
(hold)). This power/idle-adaptive behaviour is one of VDR's distinguishing features and is
called out in the README.

**`video_capture.download_video()`** tries three format tiers in order and falls back on failure:
H.264+AAC (universally playable, unlike YouTube's default AV1/VP9+Opus "best" streams which many
players — including QuickTime — can't decode), the same format forced through alternate YouTube
"player clients" (dodges a class of HTTP 403 that's specific to which client served the format
URL), then yt-dlp's own unconstrained best. `looks_like_video_url()` here is the single source of
truth for video-site detection, imported by both `server.py` (browser extension traffic) and
`gui.py` (the "+ Add URL" dialog auto-routes video URLs to `queue_video()` instead of trying to
segment-download the webpage itself).

**`organizer.py`** provides post-download category routing (Videos/Documents/Zips/Audio/
Images/Other by extension) plus collision-safe dedupe/rename, shared by `server.py` (incoming
browser-extension URLs) and `gui.py` (completed regular + video files).

**`macos_integration.MacIntegration`** is entirely optional and self-disabling: if not on Darwin or
PyObjC isn't installed, `available` stays `False` and every method becomes a safe no-op (falling
back to `osascript`/`afplay` subprocess calls for notifications/sound where possible even without
PyObjC). Never assume it's present.

**`server.py`** is a Flask app on `127.0.0.1:27182` (localhost-only) for the Chrome extension.
`POST /add` auto-detects video vs. regular URLs and routes accordingly; `main.py` also forwards
`sys.argv` URLs (from py2app/PyInstaller argv-emulation when a link is dropped on the Dock icon)
into the same `add_url_from_drop` path.

**`browser_extension/`** (Manifest V3): `background.js` is the service worker — it intercepts
native Chrome downloads and adds the right-click "Download with VDR" menu. `content.js`
injects a floating "⬇ VDR" button onto YouTube's player (`.html5-video-player`), re-injecting on
`yt-navigate-finish` since YouTube is an SPA, and talks to the local server via
`chrome.runtime.sendMessage` to `background.js` rather than fetching directly — YouTube's page CSP
can block a content script's own `fetch()` to `127.0.0.1` but not the background worker's.

## Non-obvious gotchas

- **`_open_path()`** (Open Folder / double-click-to-open in `gui.py`) must use `subprocess.Popen`,
  never `os.system()` — `os.system()` blocks the entire Tk event loop until the shell it spawns
  exits (~150ms+), which is enough to make every click feel unresponsive and get "double-clicked"
  by an impatient user.
- **Cmd+V / right-click paste don't work by default** in Tk Entry/Text widgets on macOS without an
  app-level Edit menu, even though the underlying `<<Paste>>` virtual event works fine. Both are
  wired manually in `_enable_mac_clipboard_shortcuts()`, bound via `bind_all` at the root so future
  dialogs (`simpledialog`, etc.) inherit them automatically.
- **ttk's native "aqua" theme on macOS ignores `style.map()` hover/pressed colors.** The app
  force-switches to the `"clam"` theme for real hover/press feedback, which means it no longer
  auto-follows system Dark Mode — `App._system_is_dark()` / `_apply_system_theme()` /
  `_sync_system_theme()` poll `defaults read -g AppleInterfaceStyle` every 1.5s and manually
  re-`style.configure(...)` every color to compensate. If you touch button/Treeview styling, update
  both the dark and light branches in `_apply_system_theme()`.
- **The installed `.app` bundle at `~/Applications/VDR.app`** is a hand-built wrapper
  (`Contents/MacOS/vdr_launcher`, a bash script) — separate from the PyInstaller/py2app
  outputs in `build/`/`dist/`. It explicitly prepends `/opt/homebrew/bin` to `PATH` because
  GUI-launched apps (Dock/Finder) don't inherit a Terminal's `PATH`, and the app depends on
  `ffmpeg` (merging) and `deno` (a JS runtime yt-dlp needs for YouTube's signature cipher) both
  being on it. It also redirects stdout/stderr to `~/Library/Logs/VDR/app.log`, since a
  GUI-launched process has no terminal and video-download failures otherwise vanish into an
  unreadable Tk messagebox.
