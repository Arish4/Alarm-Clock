"""The run loop: orchestrates clock, scheduler, ringer, responder and events.

Dependency Inversion in practice — every collaborator is an injected port, so
the loop is exercised in tests with a ``FakeClock``, ``RecordingRinger``,
``ScriptedResponder`` and ``InMemoryEventSink`` with no real sleeping or sound.
This module is the only place that performs real sleeping (via the clock).
"""

from __future__ import annotations

from datetime import timedelta

from ..domain.alarm import Alarm
from ..domain.events import AlarmEvent, EventKind
from .interfaces import (
    AlarmRepository,
    Clock,
    Decision,
    EventSink,
    Responder,
    Ringer,
)
from .scheduler import Scheduler, minute_key


class AlarmRunner:
    """Watches the clock and rings alarms as they come due."""

    def __init__(
        self,
        repository: AlarmRepository,
        clock: Clock,
        ringer: Ringer,
        responder: Responder,
        events: EventSink,
        scheduler: Scheduler | None = None,
        snooze_minutes: int = 9,
        max_snoozes: int | None = None,
    ):
        self._repo = repository
        self._clock = clock
        self._ringer = ringer
        self._responder = responder
        self._events = events
        self._scheduler = scheduler or Scheduler()
        self._snooze_minutes = snooze_minutes
        self._max_snoozes = max_snoozes
        self._fired: dict[str, str] = {}

    def tick(self, alarms: list[Alarm]) -> list[Alarm]:
        """Process a single instant; returns the alarms that rang."""
        now = self._clock.now()
        current = minute_key(now)
        due = self._scheduler.due(alarms, now, self._fired)
        if not due:
            return []

        for alarm in due:
            self._ringer.ring(alarm)
            self._fired[alarm.id] = current
            self._record(now, alarm, EventKind.RANG)
            self._handle_decision(now, alarm)

        self._repo.save(alarms)
        return due

    def run(self, max_ticks: int | None = None, tick_seconds: float = 1.0) -> None:
        """Blocking watch loop. ``max_ticks`` bounds it for tests."""
        alarms = self._repo.load()
        ticks = 0
        while max_ticks is None or ticks < max_ticks:
            self.tick(alarms)
            self._clock.sleep(tick_seconds)
            ticks += 1

    # --- internals -----------------------------------------------------------

    def _handle_decision(self, now, alarm: Alarm) -> None:
        decision = self._responder.respond(alarm)
        wants_snooze = decision is Decision.SNOOZE
        if wants_snooze and self._snooze_allowed(alarm):
            alarm.snooze(now + timedelta(minutes=self._snooze_minutes))
            self._record(now, alarm, EventKind.SNOOZED)
        else:
            alarm.dismiss()
            kind = EventKind.AUTO_DISMISSED if wants_snooze else EventKind.DISMISSED
            self._record(now, alarm, kind)

    def _snooze_allowed(self, alarm: Alarm) -> bool:
        return self._max_snoozes is None or alarm.snooze_count < self._max_snoozes

    def _record(self, now, alarm: Alarm, kind: EventKind) -> None:
        self._events.record(
            AlarmEvent(at=now, alarm_id=alarm.id, kind=kind, label=alarm.label)
        )
