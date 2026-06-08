"""Interactive features and the menu, driven by a ScriptedConsole + FakeClock."""

from __future__ import annotations

from datetime import datetime

from alarmclock.application.features import (
    ClockFeature,
    Feature,
    StopwatchFeature,
    TimerFeature,
)
from alarmclock.application.menu import InteractiveMenu
from alarmclock.infrastructure.clock import FakeClock
from alarmclock.infrastructure.console import ScriptedConsole

T0 = datetime(2024, 1, 1, 9, 30, 0)


def test_clock_feature_renders_then_quits():
    console = ScriptedConsole(keys=["q"])
    ClockFeature(FakeClock(T0)).run(console)
    assert "  CLOCK" in console.output
    assert "    09:30:00" in console.output


def test_stopwatch_feature_pauses_on_space_then_quits():
    # space -> pause, then q -> back. No crash, renders stopwatch.
    console = ScriptedConsole(keys=[" ", "q"])
    StopwatchFeature(FakeClock(T0)).run(console)
    assert "  STOPWATCH" in console.output


def test_timer_feature_rings_when_finished():
    class CountingSound:
        def __init__(self) -> None:
            self.plays = 0

        def play(self) -> None:
            self.plays += 1

    sound = CountingSound()
    # 1-second timer; frames advance the FakeClock by 0.1s via clock.sleep.
    # Plenty of "no key" frames, then the queue empties and read_key -> "q".
    console = ScriptedConsole(keys=[None] * 20, lines=["1s"])
    TimerFeature(FakeClock(T0), sound).run(console)
    assert any("TIME'S UP" in line for line in console.output)
    assert sound.plays == 1


def test_timer_feature_rejects_bad_duration():
    class CountingSound:
        def play(self) -> None:  # pragma: no cover - should not ring
            raise AssertionError("must not ring on invalid input")

    console = ScriptedConsole(lines=["nonsense", ""])
    TimerFeature(FakeClock(T0), CountingSound()).run(console)
    assert any("invalid duration" in line for line in console.output)


class _SpyFeature(Feature):
    name = "Spy"

    def __init__(self) -> None:
        self.ran = 0

    def run(self, console) -> None:
        self.ran += 1


def test_menu_dispatches_to_feature_then_quits():
    spy = _SpyFeature()
    menu = InteractiveMenu([spy])
    # choose "1" -> run spy, then "" -> quit.
    console = ScriptedConsole(lines=["1", ""])
    menu.run(console)
    assert spy.ran == 1
    assert "  alarmclock" in console.output


def test_menu_select_by_name():
    spy = _SpyFeature()
    menu = InteractiveMenu([spy])
    console = ScriptedConsole(lines=["spy", "q"])
    menu.run(console)
    assert spy.ran == 1


def test_menu_unknown_choice_is_ignored():
    spy = _SpyFeature()
    menu = InteractiveMenu([spy])
    console = ScriptedConsole(lines=["zzz", "q"])
    menu.run(console)
    assert spy.ran == 0
