import os
import threading
import sys
import tkinter as tk


def _ensure_homebrew_path():
    """Apps launched from the Dock/Finder don't inherit a Terminal's PATH,
    so Homebrew-installed tools (ffmpeg, deno) silently can't be found even
    though they're on the machine -- only running via Terminal happened to
    work. Add their usual install locations explicitly, before anything
    else (video_capture/yt-dlp) might shell out to them."""
    if sys.platform != "darwin":
        return
    extra = ["/opt/homebrew/bin", "/opt/homebrew/sbin", "/usr/local/bin"]
    parts = os.environ.get("PATH", "").split(os.pathsep)
    for p in extra:
        if p not in parts and os.path.isdir(p):
            parts.append(p)
    os.environ["PATH"] = os.pathsep.join(parts)


_ensure_homebrew_path()

from queue_manager import QueueManager
from server import create_server, DEFAULT_PORT
from gui import App, DEFAULT_DIR


def main():
    os.makedirs(DEFAULT_DIR, exist_ok=True)
    qm = QueueManager(max_concurrent=3, global_speed_limit=None)

    root = tk.Tk()
    app = App(root, qm)
    # py2app's argv emulation passes links dropped on the Dock icon here.
    for arg in sys.argv[1:]:
        if arg.startswith(("http://", "https://")):
            root.after(0, lambda url=arg: app.add_url_from_drop(url))

    flask_app = create_server(qm, DEFAULT_DIR, video_queue_fn=app.queue_video)

    def run_server():
        try:
            flask_app.run(host="127.0.0.1", port=DEFAULT_PORT, debug=False, use_reloader=False)
        except Exception as e:
            print(f"Local server failed to start: {e}")
            root.after(0, lambda: app.set_server_status(
                f"Local server failed to start ({e}) — browser extension won't work.", "red"))
            return

    threading.Thread(target=run_server, daemon=True).start()
    app.set_server_status(
        f"Local server running on http://127.0.0.1:{DEFAULT_PORT} — browser extension can connect.", "green")

    root.mainloop()


if __name__ == "__main__":
    main()
