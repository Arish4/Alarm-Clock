"""Clock implementations: real OS clock and a deterministic fake for tests."""

from __future__ import annotations

import time as _time
from datetime import datetime, timedelta


class SystemClock:
    """Real clock backed by the operating system."""

    def now(self) -> datetime:
        return datetime.now()

    def sleep(self, seconds: float) -> None:
        _time.sleep(seconds)


class FakeClock:
    """Deterministic clock. ``sleep`` advances fake time instead of blocking."""

    def __init__(self, start: datetime):
        self._now = start
        self.sleeps: list[float] = []

    def now(self) -> datetime:
        return self._now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self._now += timedelta(seconds=seconds)

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)
