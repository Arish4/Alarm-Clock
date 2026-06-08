"""Ports: the abstractions the application layer depends on.

Dependency Inversion: high-level policy (scheduler, services, runner) depends
only on these small interfaces, never on concrete infrastructure.

Interface Segregation: each port is intentionally tiny — a ``SoundPlayer`` only
plays, a ``Notifier`` only notifies, an ``EventSink`` only records — so no
implementation is forced to depend on methods it does not use.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Protocol, runtime_checkable

from ..domain.alarm import Alarm
from ..domain.events import AlarmEvent


@runtime_checkable
class Clock(Protocol):
    """A source of the current time that can also wait."""

    def now(self) -> datetime: ...

    def sleep(self, seconds: float) -> None: ...


@runtime_checkable
class AlarmRepository(Protocol):
    """Persistent collection of alarms."""

    def load(self) -> list[Alarm]: ...

    def save(self, alarms: list[Alarm]) -> None: ...


@runtime_checkable
class SoundPlayer(Protocol):
    """Plays an audible alert. Implementations must never raise."""

    def play(self) -> None: ...


@runtime_checkable
class Notifier(Protocol):
    """Shows a visual alert for an alarm."""

    def notify(self, alarm: Alarm) -> None: ...


@runtime_checkable
class Ringer(Protocol):
    """Announces a ringing alarm (typically visual + audible)."""

    def ring(self, alarm: Alarm) -> None: ...


@runtime_checkable
class EventSink(Protocol):
    """Receives domain events (write side)."""

    def record(self, event: AlarmEvent) -> None: ...


@runtime_checkable
class EventReader(Protocol):
    """Reads back recent domain events (read side)."""

    def recent(self, limit: int) -> list[AlarmEvent]: ...


class Decision(str, Enum):
    SNOOZE = "snooze"
    DISMISS = "dismiss"


@runtime_checkable
class Responder(Protocol):
    """Decides what to do when an alarm rings."""

    def respond(self, alarm: Alarm) -> Decision: ...
