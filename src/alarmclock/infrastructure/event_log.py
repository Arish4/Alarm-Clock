"""Event sinks: where domain events go, and how recent ones are read back.

Each implementation satisfies both the ``EventSink`` (write) and
``EventReader`` (read) ports. They are separate ports by design (Interface
Segregation) but convenient to implement together here.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..domain.events import AlarmEvent


def default_history_path() -> Path:
    override = os.environ.get("ALARMCLOCK_HISTORY")
    if override:
        return Path(override)
    return Path.home() / ".alarmclock" / "history.jsonl"


class NullEventSink:
    """Discards events and reads back nothing."""

    def record(self, event: AlarmEvent) -> None:
        return None

    def recent(self, limit: int) -> list[AlarmEvent]:
        return []


class InMemoryEventSink:
    """Keeps events in a list (used in tests)."""

    def __init__(self) -> None:
        self.events: list[AlarmEvent] = []

    def record(self, event: AlarmEvent) -> None:
        self.events.append(event)

    def recent(self, limit: int) -> list[AlarmEvent]:
        return self.events[-limit:]


class JsonlEventSink:
    """Appends events as JSON lines and reads the tail back."""

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path is not None else default_history_path()

    def record(self, event: AlarmEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    def recent(self, limit: int) -> list[AlarmEvent]:
        if not self.path.exists():
            return []
        events: list[AlarmEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(AlarmEvent.from_dict(json.loads(line)))
            except Exception:  # noqa: BLE001 - skip corrupt lines
                continue
        return events[-limit:]
