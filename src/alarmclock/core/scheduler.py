"""Pure due-logic: given 'now', which alarms should ring?

No clock, no sleep, no I/O. This is the most subtle part of the program and
the most heavily tested, so it is deliberately side-effect free.
"""

from __future__ import annotations

from datetime import datetime

from .models import WEEKDAYS, Alarm

# Format used for the per-minute fired guard and for snooze timestamps.
MINUTE_FMT = "%Y-%m-%dT%H:%M"
ISO_MINUTE_FMT = "%Y-%m-%dT%H:%M"


def minute_key(now: datetime) -> str:
    """A string identifying the current minute, used as a fired-once guard."""
    return now.strftime(MINUTE_FMT)


def _scheduled_due(alarm: Alarm, now: datetime) -> bool:
    """True if the alarm's configured HH:MM/weekday matches ``now``."""
    if alarm.time != now.strftime("%H:%M"):
        return False
    if alarm.repeat:
        today = WEEKDAYS[now.weekday()]
        return today in alarm.repeat
    return True


def _snooze_due(alarm: Alarm, now: datetime) -> bool:
    """True if a snoozed alarm has reached its re-arm time."""
    if not alarm.snoozed_until:
        return False
    try:
        target = datetime.strptime(alarm.snoozed_until, ISO_MINUTE_FMT)
    except ValueError:
        return False
    return now >= target


def is_due(alarm: Alarm, now: datetime) -> bool:
    """Whether a single alarm is due at ``now`` (ignoring the fired guard)."""
    if not alarm.enabled:
        return False
    if _snooze_due(alarm, now):
        return True
    # A snoozed alarm does not also fire on its normal schedule until the
    # snooze has elapsed and been cleared.
    if alarm.snoozed_until:
        return False
    return _scheduled_due(alarm, now)


def due_alarms(
    alarms: list[Alarm],
    now: datetime,
    fired: dict[str, str] | None = None,
) -> list[Alarm]:
    """Return the alarms that should ring at ``now``.

    ``fired`` maps alarm id -> last minute_key it fired on. It guards against
    an alarm ringing 60× within the same minute as the loop ticks every
    second. Callers update ``fired`` after handling a ring.
    """
    fired = fired or {}
    current = minute_key(now)
    result: list[Alarm] = []
    for alarm in alarms:
        if not is_due(alarm, now):
            continue
        if fired.get(alarm.id) == current:
            continue
        result.append(alarm)
    return result
