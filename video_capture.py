"""
Video/stream capture support, built on yt-dlp (the actively-maintained,
widely-used open-source extractor library — the same kind of engine real
download managers use for site-specific video capture).

Note: only use this against content you have the right to download
(your own uploads, permitted platforms, content licensed for it, etc.) —
respect the terms of service of whatever site you're pulling from.
"""
import os
from typing import Callable, Optional

import yt_dlp

VIDEO_HOSTS = (
    "youtube.com", "youtu.be", "vimeo.com", "twitch.tv", "dailymotion.com",
    "facebook.com/watch", "tiktok.com", "twitter.com", "x.com",
)


def looks_like_video_url(url: str) -> bool:
    return any(h in url for h in VIDEO_HOSTS)


class DownloadPaused(Exception):
    """Raise from a progress_hook to intentionally abort an in-progress
    download (e.g. the user clicked Pause). yt-dlp's downloader resumes
    from partial fragments by default, so a later call with the same URL
    picks back up rather than starting over."""


def is_supported(url: str) -> bool:
    """Quick check whether yt-dlp recognizes this URL without downloading."""
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "simulate": True}) as ydl:
            ydl.extract_info(url, download=False, process=False)
        return True
    except Exception:
        return False


def get_info(url: str) -> dict:
    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        return ydl.extract_info(url, download=False)


def download_video(
    url: str,
    dest_dir: str,
    quality: str = "best",
    progress_hook: Optional[Callable] = None,
    audio_only: bool = False,
):
    os.makedirs(dest_dir, exist_ok=True)
    base_opts = {
        "outtmpl": os.path.join(dest_dir, "%(title).150B [%(id)s].%(ext)s"),
        "merge_output_format": "mp4",
        "progress_hooks": [progress_hook] if progress_hook else [],
        # progress_hooks only report each fragment's own temp filename (e.g.
        # "...f137.mp4"), which yt-dlp deletes once it's merged. postprocessor_hooks
        # additionally fire with the real final filepath once merging/conversion
        # finishes -- callers need that to know what file actually exists at the end.
        "postprocessor_hooks": [progress_hook] if progress_hook else [],
        "noplaylist": False,
        "quiet": True,
        "no_warnings": True,
    }

    if audio_only:
        attempts = [{"format": "bestaudio/best",
                     "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]}]
    elif quality != "best":
        attempts = [{"format": quality, "postprocessors": []}]
    else:
        # Prefer H.264 video + AAC audio (universally playable, incl. QuickTime)
        # over YouTube's AV1/VP9 + Opus "best" streams, which many players can't
        # decode. Some videos' preferred-format URLs come back HTTP 403 depending
        # on which YouTube "player client" served them, so retry with alternate
        # clients before falling back to whatever format is actually reachable.
        h264_fmt = "bv*[vcodec^=avc1]+ba[acodec^=mp4a]/b[vcodec^=avc1][acodec^=mp4a]"
        attempts = [
            {"format": h264_fmt, "postprocessors": []},
            {"format": h264_fmt, "postprocessors": [],
             "extractor_args": {"youtube": {"player_client": ["android", "web"]}}},
            {"format": "bestvideo+bestaudio/best", "postprocessors": []},
        ]

    last_err = None
    for extra_opts in attempts:
        before = set(os.listdir(dest_dir))
        try:
            with yt_dlp.YoutubeDL({**base_opts, **extra_opts}) as ydl:
                ydl.download([url])
            return
        except DownloadPaused:
            # Intentional stop, not a real failure -- don't fall back to a
            # different format tier, and keep the partial fragments so the
            # next attempt (on Resume) can continue from them.
            raise
        except Exception as e:
            last_err = e
            # A failed attempt shouldn't leave partial fragments behind for
            # the next attempt (or the user) to trip over.
            for name in set(os.listdir(dest_dir)) - before:
                try:
                    os.remove(os.path.join(dest_dir, name))
                except OSError:
                    pass
    raise last_err
