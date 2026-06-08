"""Application context + composition root.

The composition root is the single place where concrete infrastructure is wired
to the application layer. Everything else depends only on abstractions, so this
file is where Dependency Inversion is made concrete.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Callable, TextIO

from ..application.features import (
    AlarmFeature,
    ClockFeature,
    StopwatchFeature,
    TimerFeature,
)
from ..application.interfaces import (
    AlarmRepository,
    Clock,
    Console,
    EventReader,
    EventSink,
    Responder,
    Ringer,
)
from ..application.menu import InteractiveMenu
from ..application.runner import AlarmRunner
from ..application.scheduler import Scheduler
from ..application.services import AlarmService
from ..infrastructure.clock import SystemClock
from ..infrastructure.console import TerminalConsole
from ..infrastructure.event_log import JsonlEventSink
from ..infrastructure.json_repository import JsonAlarmRepository
from ..infrastructure.responder import ConsoleResponder
from ..infrastructure.ringer import ConsoleRinger
from ..infrastructure.sound import create_sound_player


@dataclass
class AppContext:
    """Everything the CLI commands need, assembled and injected."""

    service: AlarmService
    scheduler: Scheduler
    repository: AlarmRepository
    clock: Clock
    events: EventSink
    event_reader: EventReader
    out: TextIO
    make_ringer: Callable[[str], Ringer]
    make_responder: Callable[[], Responder]
    make_console: Callable[[], Console] | None = None

    def build_runner(
        self,
        *,
        sound: str,
        snooze_minutes: int,
        max_snoozes: int | None,
    ) -> AlarmRunner:
        return AlarmRunner(
            repository=self.repository,
            clock=self.clock,
            ringer=self.make_ringer(sound),
            responder=self.make_responder(),
            events=self.events,
            scheduler=self.scheduler,
            snooze_minutes=snooze_minutes,
            max_snoozes=max_snoozes,
        )

    def build_menu(
        self,
        *,
        sound: str,
        snooze_minutes: int,
        max_snoozes: int | None,
    ) -> InteractiveMenu:
        """Assemble the interactive menu and its features (Clock/Stopwatch/
        Timer/Alarm), injecting the right ports into each."""
        timer_sound = create_sound_player(sound)

        def runner_factory() -> AlarmRunner:
            return self.build_runner(
                sound=sound,
                snooze_minutes=snooze_minutes,
                max_snoozes=max_snoozes,
            )

        features = [
            ClockFeature(self.clock),
            StopwatchFeature(self.clock),
            TimerFeature(self.clock, timer_sound),
            AlarmFeature(self.service, self.scheduler, self.clock, runner_factory),
        ]
        return InteractiveMenu(features)

    def console(self) -> Console:
        factory = self.make_console or TerminalConsole
        return factory()


def build_context(
    *,
    config_path: str | None = None,
    history_path: str | None = None,
    out: TextIO | None = None,
) -> AppContext:
    """Wire the production object graph (the composition root)."""
    out = out or sys.stdout
    repository = JsonAlarmRepository(config_path)
    events = JsonlEventSink(history_path)
    scheduler = Scheduler()
    service = AlarmService(repository)

    def make_ringer(sound: str) -> Ringer:
        return ConsoleRinger(sound=create_sound_player(sound))

    return AppContext(
        service=service,
        scheduler=scheduler,
        repository=repository,
        clock=SystemClock(),
        events=events,
        event_reader=events,
        out=out,
        make_ringer=make_ringer,
        make_responder=ConsoleResponder,
        make_console=TerminalConsole,
    )
