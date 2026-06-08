"""The `run` loop: ties clock + scheduler + ringer together.

This is the only module that performs real sleeping. The decision of what to
do when an alarm rings (snooze vs dismiss) is delegated to an injectable
``responder`` callable so the loop itself stays testable with a fake clock.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Callable

from .core.clock import Clock
from .core.models import Alarm
from .core.ringer import Ringer
from .core.scheduler import ISO_MINUTE_FMT, due_alarms, minute_key
from .core.store import Store

# A responder is asked, for a ringing alarm, what to do: "snooze" or "dismiss".
Responder = Callable[[Alarm], str]


def default_responder(alarm: Alarm) -> str:
    """Interactive prompt used by the real CLI."""
    while True:
        try:
            choice = input("[s]nooze / [d]ismiss? ").strip().lower()
        except EOFError:
            return "dismiss"
        if choice in ("s", "snooze"):
            return "snooze"
        if choice in ("d", "dismiss", ""):
            return "dismiss"
        print("please enter 's' to snooze or 'd' to dismiss")


class Runner:
    """Watches the clock and rings alarms as they come due."""

    def __init__(
        self,
        store: Store,
        clock: Clock,
        ringer: Ringer,
        snooze_minutes: int = 9,
        responder: Responder = default_responder,
    ):
        self.store = store
        self.clock = clock
        self.ringer = ringer
        self.snooze_minutes = snooze_minutes
        self.responder = responder
        # Maps alarm id -> last minute it fired, so it rings once per minute.
        self._fired: dict[str, str] = {}

    def tick(self, alarms: list[Alarm]) -> list[Alarm]:
        """Process a single instant. Returns the alarms that rang.

        Mutates the alarm list in place (snooze/dismiss state) and persists if
        anything changed.
        """
        now = self.clock.now()
        current = minute_key(now)
        due = due_alarms(alarms, now, self._fired)
        if not due:
            return []

        changed = False
        for alarm in due:
            self.ringer.ring(alarm)
            self._fired[alarm.id] = current
            action = self.responder(alarm)
            if action == "snooze":
                target = now + timedelta(minutes=self.snooze_minutes)
                alarm.snoozed_until = target.strftime(ISO_MINUTE_FMT)
            else:  # dismiss
                # Clearing snooze returns a snoozed alarm to its schedule.
                alarm.snoozed_until = None
                if alarm.is_one_off:
                    alarm.enabled = False
            changed = True

        if changed:
            self.store.save(alarms)
        return due

    def run(self, max_ticks: int | None = None, tick_seconds: float = 1.0) -> None:
        """Blocking watch loop. ``max_ticks`` bounds it for tests."""
        alarms = self.store.load()
        ticks = 0
        while max_ticks is None or ticks < max_ticks:
            self.tick(alarms)
            self.clock.sleep(tick_seconds)
            ticks += 1
