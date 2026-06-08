"""The ``Alarm`` entity: data plus the behaviour that belongs with it.

This is a rich domain entity, not an anemic bag of fields — snoozing and
dismissing are operations on the alarm itself, keeping those invariants in one
place (Single Responsibility for "what an alarm is and how its state changes").
It performs no I/O.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from .repeat import Once, RepeatPolicy, parse_repeat
from .time_of_day import TimeOfDay


def new_id() -> str:
    """A short, human-friendly unique id."""
    return uuid.uuid4().hex[:8]


@dataclass
class Alarm:
    time: TimeOfDay
    label: str = ""
    repeat: RepeatPolicy = field(default_factory=Once)
    enabled: bool = True
    tags: list[str] = field(default_factory=list)
    snoozed_until: datetime | None = None
    snooze_count: int = 0
    id: str = field(default_factory=new_id)

    # --- behaviour -----------------------------------------------------------

    @property
    def is_snoozed(self) -> bool:
        return self.snoozed_until is not None

    def snooze(self, until: datetime) -> None:
        """Re-arm the alarm for a later moment and count the snooze."""
        self.snoozed_until = until
        self.snooze_count += 1

    def dismiss(self) -> None:
        """Clear snooze state; auto-disable one-off alarms."""
        self.snoozed_until = None
        self.snooze_count = 0
        if self.repeat.is_one_off:
            self.enabled = False

    def has_tag(self, tag: str) -> bool:
        return tag.lower() in (t.lower() for t in self.tags)

    # --- serialisation -------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "time": str(self.time),
            "label": self.label,
            "repeat": self.repeat.to_spec(),
            "enabled": self.enabled,
            "tags": list(self.tags),
            "snoozed_until": (
                self.snoozed_until.isoformat(timespec="minutes")
                if self.snoozed_until
                else None
            ),
            "snooze_count": self.snooze_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Alarm":
        snoozed_raw = data.get("snoozed_until")
        return cls(
            id=data.get("id") or new_id(),
            time=TimeOfDay.parse(data["time"]),
            label=data.get("label", ""),
            repeat=parse_repeat(data.get("repeat")),
            enabled=bool(data.get("enabled", True)),
            tags=list(data.get("tags", []) or []),
            snoozed_until=(
                datetime.fromisoformat(snoozed_raw) if snoozed_raw else None
            ),
            snooze_count=int(data.get("snooze_count", 0)),
        )
