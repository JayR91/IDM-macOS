import os
from flask import Flask, request, jsonify

from video_capture import looks_like_video_url
from organizer import categorized_destination

DEFAULT_PORT = 27182


def create_server(queue_manager, dest_dir: str, video_queue_fn=None):
    """
    queue_manager: QueueManager instance to push regular file downloads into.
    dest_dir: default folder new downloads land in.
    video_queue_fn: optional callable(url) invoked for video/stream links
                     (wired up by the GUI to use video_capture.py in a thread).
    """
    app = Flask(__name__)

    @app.after_request
    def add_cors(resp):
        # Local-only, but the extension calls this from page/extension context.
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        return resp

    @app.route("/ping", methods=["GET"])
    def ping():
        return jsonify({"status": "ok", "app": "idm-clone"})

    @app.route("/add", methods=["POST", "OPTIONS"])
    def add():
        if request.method == "OPTIONS":
            return "", 200
        data = request.get_json(force=True, silent=True) or {}
        url = data.get("url")
        if not url:
            return jsonify({"error": "missing url"}), 400

        is_video = bool(data.get("is_video")) or looks_like_video_url(url)
        if is_video and video_queue_fn:
            video_queue_fn(url)
            return jsonify({"status": "queued_video", "url": url})

        filename = data.get("filename") or url.split("/")[-1].split("?")[0] or "download"
        filename = _safe_filename(filename)
        dest_path = categorized_destination(dest_dir, filename)
        queue_manager.add(url, dest_path)
        return jsonify({"status": "queued", "file": os.path.basename(dest_path)})

    return app


def _safe_filename(name: str) -> str:
    keep = "-_.() " + "".join(chr(c) for c in range(48, 58)) + "".join(chr(c) for c in range(65, 91)) + "".join(chr(c) for c in range(97, 123))
    cleaned = "".join(c for c in name if c in keep).strip()
    return cleaned or "download"


def _dedupe_path(path: str) -> str:
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{base} ({i}){ext}"):
        i += 1
    return f"{base} ({i}){ext}"
