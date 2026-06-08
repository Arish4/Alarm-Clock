"""A tiny time-source abstraction so tests can control 'now'."""

from __future__ import annotations

import time as _time
from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Anything that can tell the current local time and sleep."""

    def now(self) -> datetime:  # pragma: no cover - protocol
        ...

    def sleep(self, seconds: float) -> None:  # pragma: no cover - protocol
        ...


class SystemClock:
    """Real clock backed by the operating system."""

    def now(self) -> datetime:
        return datetime.now()

    def sleep(self, seconds: float) -> None:
        _time.sleep(seconds)


class FakeClock:
    """Deterministic clock for tests.

    ``sleep`` advances the fake time instead of blocking, so the run loop can
    be exercised without any real waiting.
    """

    def __init__(self, start: datetime):
        self._now = start
        self.sleeps: list[float] = []

    def now(self) -> datetime:
        return self._now

    def sleep(self, seconds: float) -> None:
        from datetime import timedelta

        self.sleeps.append(seconds)
        self._now = self._now + timedelta(seconds=seconds)

    def advance(self, seconds: float) -> None:
        from datetime import timedelta

        self._now = self._now + timedelta(seconds=seconds)
