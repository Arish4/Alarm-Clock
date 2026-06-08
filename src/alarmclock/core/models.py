"""Pure data structures for the alarm clock. No I/O, no side effects."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

# Weekday codes used for repeating alarms, indexed to match
# datetime.weekday() (Monday == 0 ... Sunday == 6).
WEEKDAYS: tuple[str, ...] = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


class ValidationError(ValueError):
    """Raised when user-supplied data fails validation."""


def new_id() -> str:
    """Return a short, human-friendly unique id."""
    return uuid.uuid4().hex[:8]


def parse_time(value: str) -> str:
    """Validate and normalise an ``HH:MM`` 24-hour time string.

    Returns the canonical ``HH:MM`` form (zero padded). Raises
    :class:`ValidationError` for anything that is not a valid time.
    """
    raw = value.strip()
    parts = raw.split(":")
    if len(parts) != 2:
        raise ValidationError(f"invalid time {value!r}: expected HH:MM")
    hh, mm = parts
    if not (hh.isdigit() and mm.isdigit()):
        raise ValidationError(f"invalid time {value!r}: expected digits HH:MM")
    hour, minute = int(hh), int(mm)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValidationError(f"invalid time {value!r}: out of range")
    return f"{hour:02d}:{minute:02d}"


def parse_repeat(value: str | None) -> list[str]:
    """Parse a comma-separated weekday string into a normalised list.

    ``None`` or an empty string means a one-off alarm (empty list). Order is
    preserved as Mon..Sun and duplicates are removed. Raises
    :class:`ValidationError` for unknown weekday codes.
    """
    if not value:
        return []
    seen: set[str] = set()
    for token in value.split(","):
        code = token.strip().lower()
        if not code:
            continue
        if code not in WEEKDAYS:
            raise ValidationError(
                f"invalid weekday {token!r}: expected one of {', '.join(WEEKDAYS)}"
            )
        seen.add(code)
    # Return in canonical Mon..Sun order for stable display/storage.
    return [day for day in WEEKDAYS if day in seen]


@dataclass
class Alarm:
    """A single alarm. Pure data — knows nothing about time or files."""

    time: str
    label: str = ""
    repeat: list[str] = field(default_factory=list)
    enabled: bool = True
    snoozed_until: str | None = None
    id: str = field(default_factory=new_id)

    def to_dict(self) -> dict:
        """Serialise to a plain dict for JSON storage."""
        return {
            "id": self.id,
            "time": self.time,
            "label": self.label,
            "repeat": list(self.repeat),
            "enabled": self.enabled,
            "snoozed_until": self.snoozed_until,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Alarm":
        """Build an Alarm from a stored dict, tolerating missing fields."""
        return cls(
            id=data.get("id") or new_id(),
            time=parse_time(data["time"]),
            label=data.get("label", ""),
            repeat=parse_repeat(",".join(data.get("repeat", []) or [])),
            enabled=bool(data.get("enabled", True)),
            snoozed_until=data.get("snoozed_until"),
        )

    @property
    def is_one_off(self) -> bool:
        return not self.repeat

    def repeat_display(self) -> str:
        """Human-readable repeat column for ``list``."""
        if not self.repeat:
            return "once"
        if len(self.repeat) == 7:
            return "daily"
        return ",".join(self.repeat)

    def status_display(self) -> str:
        if not self.enabled:
            return "disabled"
        if self.snoozed_until:
            return f"snoozed→{self.snoozed_until}"
        return "armed"
