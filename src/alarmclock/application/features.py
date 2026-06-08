"""Interactive terminal features (Clock, Stopwatch, Timer, Alarm).

Each feature is a self-contained screen implementing the :class:`Feature`
contract, so the menu can list and run any of them interchangeably (Liskov).
Adding a new screen means adding a ``Feature`` subclass and registering it —
the menu never changes (Open/Closed). Every feature depends only on injected
ports (``Console``, ``Clock``, ``SoundPlayer``, ``AlarmService``), never on
concrete infrastructure (Dependency Inversion).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from ..domain.duration import format_hms, format_stopwatch, parse_duration
from ..domain.errors import ValidationError
from ..domain.stopwatch import Stopwatch
from ..domain.timer import Countdown
from .interfaces import Clock, Console, Responder, Ringer, SoundPlayer
from .scheduler import Scheduler
from .services import AlarmService

QUIT_KEYS = {"q", "Q", "\x1b"}  # q or Esc
SPACE = " "

# Frame pacing for live screens (seconds). The clock advances by this each
# redraw; in tests a FakeClock makes it instantaneous.
CLOCK_FRAME = 0.2
TICK_FRAME = 0.1


class Feature(ABC):
    """One selectable interactive screen."""

    name: str

    @abstractmethod
    def run(self, console: Console) -> None:
        """Take over the terminal until the user backs out."""


class ClockFeature(Feature):
    name = "Clock"

    def __init__(self, clock: Clock):
        self._clock = clock

    def run(self, console: Console) -> None:
        while True:
            now = self._clock.now()
            console.clear()
            console.write_line("  CLOCK")
            console.write_line()
            console.write_line("    " + now.strftime("%H:%M:%S"))
            console.write_line("    " + now.strftime("%A, %d %B %Y"))
            console.write_line()
            console.write_line("  [q] back")
            if console.read_key() in QUIT_KEYS:
                return
            self._clock.sleep(CLOCK_FRAME)


class StopwatchFeature(Feature):
    name = "Stopwatch"

    def __init__(self, clock: Clock):
        self._clock = clock

    def run(self, console: Console) -> None:
        watch = Stopwatch()
        watch.start(self._clock.now())
        while True:
            now = self._clock.now()
            console.clear()
            console.write_line("  STOPWATCH")
            console.write_line()
            console.write_line("    " + format_stopwatch(watch.elapsed(now)))
            console.write_line("    " + ("running" if watch.running else "paused"))
            for index, lap in enumerate(watch.laps, start=1):
                console.write_line(f"      lap {index}: {format_stopwatch(lap)}")
            console.write_line()
            console.write_line(
                "  [space] start/pause   [l] lap   [r] reset   [q] back"
            )
            key = console.read_key()
            if key in QUIT_KEYS:
                return
            if key == SPACE:
                watch.toggle(now)
            elif key in ("l", "L"):
                watch.lap(now)
            elif key in ("r", "R"):
                watch.reset()
            self._clock.sleep(TICK_FRAME)


class TimerFeature(Feature):
    name = "Timer"

    def __init__(self, clock: Clock, sound: SoundPlayer):
        self._clock = clock
        self._sound = sound

    def run(self, console: Console) -> None:
        console.clear()
        console.write_line("  TIMER")
        console.write_line()
        raw = console.read_line(
            "  duration (e.g. 30s, 5m, 1h30m, 10:00): "
        )
        try:
            seconds = parse_duration(raw)
        except ValidationError as exc:
            console.write_line(f"  {exc}")
            console.read_line("  press Enter to go back ")
            return

        countdown = Countdown(seconds)
        countdown.start(self._clock.now())
        rung = False
        while True:
            now = self._clock.now()
            console.clear()
            console.write_line("  TIMER")
            console.write_line()
            if countdown.is_finished(now):
                console.write_line("    00:00:00")
                console.write_line()
                console.write_line("    *** TIME'S UP ***")
                if not rung:
                    self._sound.play()
                    rung = True
                console.write_line()
                console.write_line("  [q] back")
                if console.read_key() in QUIT_KEYS:
                    return
                self._clock.sleep(TICK_FRAME)
                continue

            console.write_line("    " + format_hms(countdown.remaining(now)))
            console.write_line("    " + ("running" if countdown.running else "paused"))
            console.write_line()
            console.write_line("  [space] pause/resume   [q] back")
            key = console.read_key()
            if key in QUIT_KEYS:
                return
            if key == SPACE:
                countdown.toggle(now)
            self._clock.sleep(TICK_FRAME)


class AlarmFeature(Feature):
    name = "Alarm"

    def __init__(
        self,
        service: AlarmService,
        scheduler: Scheduler,
        clock: Clock,
        runner_factory: Callable[[], "object"],
    ):
        self._service = service
        self._scheduler = scheduler
        self._clock = clock
        self._runner_factory = runner_factory

    def run(self, console: Console) -> None:
        while True:
            console.clear()
            console.write_line("  ALARM")
            console.write_line()
            self._render_alarms(console)
            console.write_line()
            console.write_line(
                "  [a] add   [d] delete   [s] start watch   [q] back"
            )
            choice = console.read_line("  choose: ").strip().lower()
            if choice in ("q", "quit", ""):
                return
            if choice == "a":
                self._add(console)
            elif choice == "d":
                self._delete(console)
            elif choice == "s":
                self._watch(console)

    def _render_alarms(self, console: Console) -> None:
        alarms = self._service.list()
        if not alarms:
            console.write_line("    (no alarms set)")
            return
        now = self._clock.now()
        for alarm in alarms:
            nxt = self._scheduler.next_occurrence(alarm, now)
            when = nxt.strftime("%a %H:%M") if nxt else "never"
            status = "off" if not alarm.enabled else "on"
            console.write_line(
                f"    {alarm.id}  {alarm.time}  "
                f"{alarm.label or '(no label)':12}  "
                f"[{alarm.repeat.describe()}]  next {when}  ({status})"
            )

    def _add(self, console: Console) -> None:
        time = console.read_line("    time (HH:MM or H:MMam/pm): ").strip()
        label = console.read_line("    label: ").strip()
        repeat = console.read_line(
            "    repeat (once/daily/weekdays/weekends/mon,fri): "
        ).strip()
        try:
            alarm = self._service.add(time=time, label=label, repeat=repeat)
            console.write_line(f"    added {alarm.id}")
        except ValidationError as exc:
            console.write_line(f"    {exc}")
        console.read_line("    press Enter to continue ")

    def _delete(self, console: Console) -> None:
        alarm_id = console.read_line("    id to delete: ").strip()
        try:
            self._service.delete(alarm_id)
            console.write_line(f"    deleted {alarm_id}")
        except Exception as exc:  # noqa: BLE001 - surface message, stay in menu
            console.write_line(f"    {exc}")
        console.read_line("    press Enter to continue ")

    def _watch(self, console: Console) -> None:
        runner = self._runner_factory()
        console.clear()
        console.write_line("  ALARM WATCH — ringing when due. press Ctrl-C to stop.")
        console.write_line()
        try:
            runner.run()  # type: ignore[attr-defined]
        except KeyboardInterrupt:
            console.write_line("\n  stopped.")
