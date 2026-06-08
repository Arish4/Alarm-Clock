"""Domain events emitted while the run loop processes alarms."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EventKind(str, Enum):
    RANG = "rang"
    SNOOZED = "snoozed"
    DISMISSED = "dismissed"
    AUTO_DISMISSED = "auto_dismissed"


@dataclass(frozen=True)
class AlarmEvent:
    """A single thing that happened to an alarm at a moment in time."""

    at: datetime
    alarm_id: str
    kind: EventKind
    label: str

    def to_dict(self) -> dict:
        return {
            "at": self.at.isoformat(timespec="seconds"),
            "alarm_id": self.alarm_id,
            "kind": self.kind.value,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AlarmEvent":
        return cls(
            at=datetime.fromisoformat(data["at"]),
            alarm_id=data["alarm_id"],
            kind=EventKind(data["kind"]),
            label=data.get("label", ""),
        )
