"""A pure stopwatch model.

Holds accumulated time plus an optional running segment; ``elapsed(now)`` is a
pure function of the injected ``now`` so it is fully testable without real time.
"""

from __future__ import annotations

from datetime import datetime


class Stopwatch:
    def __init__(self) -> None:
        self._accumulated = 0.0
        self._running = False
        self._started_at: datetime | None = None
        self.laps: list[float] = []

    @property
    def running(self) -> bool:
        return self._running

    def start(self, now: datetime) -> None:
        if not self._running:
            self._running = True
            self._started_at = now

    def stop(self, now: datetime) -> None:
        if self._running and self._started_at is not None:
            self._accumulated += (now - self._started_at).total_seconds()
            self._running = False
            self._started_at = None

    def toggle(self, now: datetime) -> None:
        if self._running:
            self.stop(now)
        else:
            self.start(now)

    def reset(self) -> None:
        self._accumulated = 0.0
        self._running = False
        self._started_at = None
        self.laps = []

    def elapsed(self, now: datetime) -> float:
        total = self._accumulated
        if self._running and self._started_at is not None:
            total += (now - self._started_at).total_seconds()
        return total

    def lap(self, now: datetime) -> float:
        marked = self.elapsed(now)
        self.laps.append(marked)
        return marked
