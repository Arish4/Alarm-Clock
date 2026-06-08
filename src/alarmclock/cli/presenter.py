"""Output formatting helpers (kept separate so commands stay thin)."""

from __future__ import annotations

import json
from datetime import datetime

from ..application.scheduler import Scheduler
from ..domain.alarm import Alarm
from ..domain.events import AlarmEvent


def _status(alarm: Alarm) -> str:
    if not alarm.enabled:
        return "disabled"
    if alarm.is_snoozed:
        return "snoozed"
    return "armed"


def render_table(rows: list[tuple[str, ...]]) -> str:
    """Render aligned columns; the first row is treated as a header."""
    if not rows:
        return ""
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    lines = []
    for index, row in enumerate(rows):
        lines.append("  ".join(c.ljust(widths[j]) for j, c in enumerate(row)))
        if index == 0:
            lines.append("  ".join("-" * w for w in widths))
    return "\n".join(lines)


def alarms_table(alarms: list[Alarm]) -> str:
    rows: list[tuple[str, ...]] = [("ID", "TIME", "LABEL", "REPEAT", "TAGS", "STATUS")]
    for a in alarms:
        rows.append(
            (
                a.id,
                str(a.time),
                a.label or "-",
                a.repeat.describe(),
                ",".join(a.tags) or "-",
                _status(a),
            )
        )
    return render_table(rows)


def alarms_json(alarms: list[Alarm]) -> str:
    return json.dumps([a.to_dict() for a in alarms], indent=2, ensure_ascii=False)


def next_table(alarms: list[Alarm], scheduler: Scheduler, now: datetime) -> str:
    rows: list[tuple[str, ...]] = [("ID", "LABEL", "NEXT FIRE")]
    for a in alarms:
        nxt = scheduler.next_occurrence(a, now)
        rows.append(
            (a.id, a.label or "-", nxt.strftime("%a %Y-%m-%d %H:%M") if nxt else "never")
        )
    return render_table(rows)


def next_json(alarms: list[Alarm], scheduler: Scheduler, now: datetime) -> str:
    payload = []
    for a in alarms:
        nxt = scheduler.next_occurrence(a, now)
        payload.append(
            {
                "id": a.id,
                "label": a.label,
                "next_fire": nxt.isoformat(timespec="minutes") if nxt else None,
            }
        )
    return json.dumps(payload, indent=2, ensure_ascii=False)


def history_table(events: list[AlarmEvent]) -> str:
    rows: list[tuple[str, ...]] = [("WHEN", "ALARM", "EVENT", "LABEL")]
    for e in events:
        rows.append(
            (
                e.at.strftime("%Y-%m-%d %H:%M:%S"),
                e.alarm_id,
                e.kind.value,
                e.label or "-",
            )
        )
    return render_table(rows)
