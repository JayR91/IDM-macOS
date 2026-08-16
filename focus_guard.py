"""Focus Guard — adaptive downloads that commercial IDM does not have.

Classic Internet Download Manager can cap speed and schedule by clock time.
It has no idea whether a Mac is on battery, in Low Power Mode, or whether
you are actively using the keyboard and mouse.

Focus Guard watches those signals and:
  - pauses transfers on battery / Low Power Mode
  - crawls (slow cap) while you are using the Mac, so browsing stays snappy
  - runs at full (or your own) speed once the Mac has been idle
"""

from __future__ import annotations

import re
import subprocess
import threading
import time
from typing import Callable, Optional

IDLE_SECONDS = 20
CRAWL_BYTES_PER_SEC = 256 * 1024  # 256 KB/s while you are at the keyboard

POLICY_OFF = "off"
POLICY_FULL = "full"
POLICY_CRAWL = "active"
POLICY_HOLD = "battery"


def decide_policy(enabled: bool, on_battery: bool, low_power: bool, idle_seconds: float) -> str:
    if not enabled:
        return POLICY_OFF
    if on_battery or low_power:
        return POLICY_HOLD
    if idle_seconds < IDLE_SECONDS:
        return POLICY_CRAWL
    return POLICY_FULL


def read_idle_seconds() -> float:
    try:
        out = subprocess.check_output(
            ["ioreg", "-c", "IOHIDSystem", "-d", "4"],
            text=True, timeout=2,
        )
        match = re.search(r'"HIDIdleTime"\s*=\s*(\d+)', out)
        if match:
            return int(match.group(1)) / 1_000_000_000
    except Exception:
        pass
    return 9999.0


def read_power() -> tuple[bool, bool]:
    """Return (on_battery, low_power_mode)."""
    on_battery = False
    low_power = False
    try:
        batt = subprocess.check_output(["pmset", "-g", "batt"], text=True, timeout=2)
        on_battery = "Now drawing from 'Battery Power'" in batt
    except Exception:
        pass
    try:
        info = subprocess.check_output(["pmset", "-g"], text=True, timeout=2)
        match = re.search(r"lowpowermode\s+(\d+)", info)
        if match:
            low_power = match.group(1) != "0"
    except Exception:
        pass
    return on_battery, low_power


class FocusGuard:
    def __init__(self, apply_policy: Callable[[str], None],
                 on_change: Optional[Callable[[str, str], None]] = None):
        self._apply_policy = apply_policy
        self._on_change = on_change
        self.enabled = False
        self.policy = POLICY_OFF
        self.detail = "Off"
        self._stop = threading.Event()
        threading.Thread(target=self._loop, daemon=True).start()

    def set_enabled(self, enabled: bool):
        self.enabled = bool(enabled)
        self._tick(force=True)

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.wait(3):
            self._tick()

    def _tick(self, force: bool = False):
        on_battery, low_power = read_power()
        idle = read_idle_seconds()
        policy = decide_policy(self.enabled, on_battery, low_power, idle)
        if policy == POLICY_OFF:
            detail = "Off — downloads run at your speed limit"
        elif policy == POLICY_HOLD:
            reason = "Low Power Mode" if low_power and not on_battery else "battery"
            detail = f"Paused — Mac is on {reason}"
        elif policy == POLICY_CRAWL:
            detail = "Crawling at 256 KB/s while you use the Mac"
        else:
            detail = "Full speed — Mac is idle and plugged in"

        changed = policy != self.policy
        self.policy = policy
        self.detail = detail
        if changed or force:
            self._apply_policy(policy)
            if self._on_change:
                self._on_change(policy, detail)
