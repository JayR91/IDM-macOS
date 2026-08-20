import os
from flask import Flask, request, jsonify

from video_capture import looks_like_video_url
from organizer import categorized_destination

DEFAULT_PORT = 27182

# Each browser family uses its own scheme for an extension's origin --
# Chrome/Edge/Brave/Opera/Vivaldi (all Chromium) use chrome-extension://,
# Firefox uses moz-extension://. Safari's is included too even though that
# build isn't shipped yet, so this doesn't need revisiting when it is.
_TRUSTED_EXTENSION_SCHEMES = ("chrome-extension://", "moz-extension://", "safari-web-extension://")


def _is_trusted_origin(origin: str) -> bool:
    return origin.startswith(_TRUSTED_EXTENSION_SCHEMES)


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
        # Only the extension's own chrome-extension:// origin gets CORS
        # access -- a wildcard "*" here would let ANY website the user has
        # open silently POST to this server (it's bound to localhost, but
        # any page's JS can still reach 127.0.0.1) and trigger downloads
        # without the user's knowledge.
        origin = request.headers.get("Origin", "")
        if _is_trusted_origin(origin):
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
            resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            # Chrome's Private Network Access check: a request from a
            # public/unknown-address page or extension to a loopback address
            # like 127.0.0.1 gets a preflight with this header, and Chrome
            # silently blocks the real request unless the response echoes it
            # back -- background.js's fetch then just throws, which reads to
            # the user as "app not running" even though the server is up and
            # `curl` (which doesn't enforce PNA) looks fine the whole time.
            if request.headers.get("Access-Control-Request-Private-Network") == "true":
                resp.headers["Access-Control-Allow-Private-Network"] = "true"
        return resp

    @app.route("/ping", methods=["GET"])
    def ping():
        return jsonify({"status": "ok", "app": "vdr"})

    @app.route("/add", methods=["POST", "OPTIONS"])
    def add():
        if request.method == "OPTIONS":
            return "", 200
        # Defense in depth: CORS headers alone only stop a malicious page's
        # JS from reading the response, not from sending a simple/no-preflight
        # request in the first place. Reject anything not from the extension
        # outright. Requests with no Origin header at all (curl, the popup's
        # own fetch, direct localhost testing) are still allowed.
        origin = request.headers.get("Origin", "")
        if origin and not _is_trusted_origin(origin):
            return jsonify({"error": "forbidden origin"}), 403
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
