from datetime import datetime, timedelta

import pytest

from alarmclock.domain.errors import ValidationError
from alarmclock.domain.stopwatch import Stopwatch
from alarmclock.domain.timer import Countdown

T0 = datetime(2024, 1, 1, 12, 0, 0)


def at(seconds: float) -> datetime:
    return T0 + timedelta(seconds=seconds)


def test_stopwatch_accumulates_while_running():
    sw = Stopwatch()
    sw.start(at(0))
    assert sw.elapsed(at(5)) == 5
    sw.stop(at(5))
    # Paused: time keeps passing but elapsed is frozen.
    assert sw.elapsed(at(10)) == 5


def test_stopwatch_resume_adds_segments():
    sw = Stopwatch()
    sw.start(at(0))
    sw.stop(at(3))
    sw.start(at(10))
    assert sw.elapsed(at(12)) == 5  # 3 + 2


def test_stopwatch_toggle_and_reset():
    sw = Stopwatch()
    sw.toggle(at(0))  # start
    assert sw.running
    sw.toggle(at(2))  # stop
    assert not sw.running
    assert sw.elapsed(at(9)) == 2
    sw.reset()
    assert sw.elapsed(at(9)) == 0
    assert sw.laps == []


def test_stopwatch_laps():
    sw = Stopwatch()
    sw.start(at(0))
    assert sw.lap(at(4)) == 4
    assert sw.lap(at(9)) == 9
    assert sw.laps == [4, 9]


def test_countdown_remaining_and_finished():
    cd = Countdown(10)
    cd.start(at(0))
    assert cd.remaining(at(3)) == 7
    assert not cd.is_finished(at(3))
    assert cd.remaining(at(10)) == 0
    assert cd.is_finished(at(10))
    assert cd.remaining(at(15)) == 0  # never negative


def test_countdown_pause_freezes_remaining():
    cd = Countdown(10)
    cd.start(at(0))
    cd.toggle(at(4))  # pause
    assert cd.remaining(at(100)) == 6


def test_countdown_rejects_non_positive():
    with pytest.raises(ValidationError):
        Countdown(0)
