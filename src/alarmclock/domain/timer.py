"""A pure countdown timer model, built on the stopwatch."""

from __future__ import annotations

from datetime import datetime

from .errors import ValidationError
from .stopwatch import Stopwatch


class Countdown:
    def __init__(self, duration_seconds: float):
        if duration_seconds <= 0:
            raise ValidationError("a timer duration must be greater than zero")
        self.duration = float(duration_seconds)
        self._watch = Stopwatch()

    @property
    def running(self) -> bool:
        return self._watch.running

    def start(self, now: datetime) -> None:
        self._watch.start(now)

    def toggle(self, now: datetime) -> None:
        self._watch.toggle(now)

    def remaining(self, now: datetime) -> float:
        return max(0.0, self.duration - self._watch.elapsed(now))

    def is_finished(self, now: datetime) -> bool:
        return self._watch.elapsed(now) >= self.duration
