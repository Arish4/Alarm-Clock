"""Domain-level exceptions."""

from __future__ import annotations


class AlarmClockError(Exception):
    """Base class for all alarmclock errors."""


class ValidationError(AlarmClockError, ValueError):
    """Raised when user-supplied data fails validation."""


class AlarmNotFoundError(AlarmClockError):
    """Raised when an operation references an unknown alarm id."""

    def __init__(self, alarm_id: str):
        super().__init__(f"no alarm with id {alarm_id!r}")
        self.alarm_id = alarm_id
