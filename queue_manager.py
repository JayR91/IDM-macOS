import threading
import time
from typing import Optional, Callable

from engine import DownloadTask, TokenBucket, Status
from focus_guard import CRAWL_BYTES_PER_SEC, POLICY_CRAWL, POLICY_HOLD, POLICY_OFF


class QueueManager:
    def __init__(self, max_concurrent: int = 3, global_speed_limit: Optional[int] = None):
        self.max_concurrent = max_concurrent
        self.bucket = TokenBucket(global_speed_limit)
        self.tasks = []
        self.lock = threading.Lock()
        self._on_update: Optional[Callable] = None
        self.user_limit = global_speed_limit
        self.focus_policy = POLICY_OFF

    def set_speed_limit(self, bytes_per_sec: Optional[int]):
        self.user_limit = bytes_per_sec
        self._apply_bucket()

    def _apply_bucket(self):
        focus_cap = CRAWL_BYTES_PER_SEC if self.focus_policy == POLICY_CRAWL else None
        limits = [n for n in (self.user_limit, focus_cap) if n]
        self.bucket.set_rate(min(limits) if limits else None)

    def apply_focus_policy(self, policy: str):
        previous = self.focus_policy
        self.focus_policy = policy
        self._apply_bucket()
        with self.lock:
            tasks = list(self.tasks)
        if policy == POLICY_HOLD:
            for t in tasks:
                if hasattr(t, "hold_for_focus"):
                    t.hold_for_focus()
            return
        if previous == POLICY_HOLD:
            for t in tasks:
                if hasattr(t, "release_from_focus"):
                    t.release_from_focus()
            self._maybe_start()

    def set_update_callback(self, cb: Callable):
        self._on_update = cb

    def add(self, url: str, dest_path: str, num_segments: int = 8, headers: Optional[dict] = None) -> DownloadTask:
        task = DownloadTask(
            url=url,
            dest_path=dest_path,
            num_segments=num_segments,
            headers=headers,
            bucket=self.bucket,
            progress_cb=self._notify,
            status_cb=self._notify_and_advance,
        )
        with self.lock:
            self.tasks.append(task)
        self._notify(task)
        self._maybe_start()
        return task

    def schedule(self, url: str, dest_path: str, start_at: float, num_segments: int = 8, headers: Optional[dict] = None) -> DownloadTask:
        """Add a task which becomes queueable at an absolute Unix timestamp."""
        task = DownloadTask(url, dest_path, num_segments=num_segments, headers=headers,
                            bucket=self.bucket, progress_cb=self._notify,
                            status_cb=self._notify_and_advance)
        task.scheduled_for = start_at
        task._set_status(Status.SCHEDULED)
        with self.lock:
            self.tasks.append(task)
        self._notify(task)

        def wait_then_queue():
            while not task.cancel_event.is_set():
                remaining = start_at - time.time()
                if remaining <= 0:
                    task._set_status(Status.QUEUED)
                    self._maybe_start()
                    return
                time.sleep(min(remaining, 30))
        threading.Thread(target=wait_then_queue, daemon=True).start()
        return task

    def _notify(self, task):
        if self._on_update:
            self._on_update(task)

    def _notify_and_advance(self, task):
        self._notify(task)
        if task.status in (Status.COMPLETED, Status.ERROR, Status.CANCELLED):
            self._maybe_start()

    def _maybe_start(self):
        if self.focus_policy == POLICY_HOLD:
            return
        with self.lock:
            active = sum(1 for t in self.tasks if t.status in (Status.CONNECTING, Status.DOWNLOADING))
            queued = [t for t in self.tasks if t.status == Status.QUEUED]
            to_start = []
            for t in queued:
                if active >= self.max_concurrent:
                    break
                to_start.append(t)
                active += 1
        for t in to_start:
            t.start()

    def pause(self, task: DownloadTask):
        task.pause()

    def resume(self, task: DownloadTask):
        task.resume()

    def cancel(self, task: DownloadTask):
        task.cancel()
        self._maybe_start()

    def remove(self, task: DownloadTask):
        task.cancel()
        with self.lock:
            if task in self.tasks:
                self.tasks.remove(task)
