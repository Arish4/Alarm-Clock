"""``TimeOfDay`` value object — an immutable wall-clock time with parsing.

Single Responsibility: this type knows how to represent, parse and compare a
24-hour time, and nothing else.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from .errors import ValidationError

_TWENTY_FOUR = re.compile(r"^(\d{1,2}):(\d{1,2})$")
_TWELVE = re.compile(r"^(\d{1,2}):(\d{2})\s*([ap])\.?m\.?$", re.IGNORECASE)


@dataclass(frozen=True, order=True)
class TimeOfDay:
    """An hour/minute pair, validated to a real 24-hour time."""

    hour: int
    minute: int

    def __post_init__(self) -> None:
        if not (0 <= self.hour <= 23 and 0 <= self.minute <= 59):
            raise ValidationError(
                f"time {self.hour:02d}:{self.minute:02d} is out of range"
            )

    @classmethod
    def parse(cls, text: str) -> "TimeOfDay":
        """Parse ``HH:MM`` (24h) or ``H:MMam``/``H:MMpm`` (12h)."""
        if text is None:
            raise ValidationError("missing time")
        raw = text.strip()

        twelve = _TWELVE.match(raw)
        if twelve:
            hour = int(twelve.group(1))
            minute = int(twelve.group(2))
            meridiem = twelve.group(3).lower()
            if not (1 <= hour <= 12):
                raise ValidationError(f"invalid 12-hour time {text!r}")
            if meridiem == "a":
                hour = 0 if hour == 12 else hour
            else:  # pm
                hour = 12 if hour == 12 else hour + 12
            return cls(hour, minute)

        military = _TWENTY_FOUR.match(raw)
        if military:
            return cls(int(military.group(1)), int(military.group(2)))

        raise ValidationError(
            f"invalid time {text!r}: expected HH:MM (24h) or H:MMam/pm"
        )

    def matches(self, moment: datetime) -> bool:
        """True when ``moment`` falls within this minute."""
        return moment.hour == self.hour and moment.minute == self.minute

    def __str__(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"
