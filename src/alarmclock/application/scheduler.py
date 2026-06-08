"""Pure scheduling logic: given 'now', which alarms are due, and when next?

No clock, no sleep, no I/O — this is the most subtle and most tested part of
the system, so it is deliberately free of side effects (Single Responsibility:
it only answers timing questions).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from ..domain.alarm import Alarm


def minute_key(now: datetime) -> str:
    """Identifies the current minute; used as a fired-once-per-minute guard."""
    return now.strftime("%Y-%m-%dT%H:%M")


class Scheduler:
    """Answers timing questions about alarms. Stateless and pure."""

    #: how many days ahead :meth:`next_occurrence` will search.
    SEARCH_HORIZON_DAYS = 8

    def is_due(self, alarm: Alarm, now: datetime) -> bool:
        """Whether an alarm should ring at ``now`` (ignoring the fired guard)."""
        if not alarm.enabled:
            return False
        if alarm.snoozed_until is not None:
            # While snoozed, the normal schedule is suppressed until the
            # snooze elapses.
            return now >= alarm.snoozed_until
        return alarm.time.matches(now) and alarm.repeat.occurs_on(now.date())

    def due(
        self,
        alarms: list[Alarm],
        now: datetime,
        fired: dict[str, str] | None = None,
    ) -> list[Alarm]:
        """Alarms that should ring at ``now``, respecting the per-minute guard.

        ``fired`` maps alarm id -> last minute it fired, so an alarm rings once
        per minute rather than 60× as the loop ticks every second.
        """
        fired = fired or {}
        current = minute_key(now)
        return [
            alarm
            for alarm in alarms
            if self.is_due(alarm, now) and fired.get(alarm.id) != current
        ]

    def next_occurrence(self, alarm: Alarm, now: datetime) -> datetime | None:
        """The next datetime the alarm will fire, or ``None`` if never."""
        if not alarm.enabled:
            return None
        if alarm.snoozed_until is not None:
            return alarm.snoozed_until
        base = now.replace(second=0, microsecond=0)
        for offset in range(self.SEARCH_HORIZON_DAYS):
            day = (base + timedelta(days=offset)).date()
            if not alarm.repeat.occurs_on(day):
                continue
            candidate = datetime(
                day.year, day.month, day.day, alarm.time.hour, alarm.time.minute
            )
            if candidate >= base:
                return candidate
        return None
