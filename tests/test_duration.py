import pytest

from alarmclock.domain.duration import (
    format_hms,
    format_stopwatch,
    parse_duration,
)
from alarmclock.domain.errors import ValidationError


@pytest.mark.parametrize(
    "text,seconds",
    [
        ("30s", 30),
        ("5m", 300),
        ("1h30m", 5400),
        ("1h", 3600),
        ("90", 90),
        ("10:00", 600),
        ("01:30:00", 5400),
        ("2:05", 125),
    ],
)
def test_parse_valid(text, seconds):
    assert parse_duration(text) == seconds


@pytest.mark.parametrize("text", ["", "abc", "0", "0s", "5x", "10:99", "1:2:3:4"])
def test_parse_invalid(text):
    with pytest.raises(ValidationError):
        parse_duration(text)


@pytest.mark.parametrize(
    "seconds,expected",
    [(0, "00:00:00"), (1, "00:00:01"), (59, "00:00:59"), (3661, "01:01:01")],
)
def test_format_hms_rounds_up(seconds, expected):
    assert format_hms(seconds) == expected


def test_format_hms_ceils_fraction():
    # 0.4s remaining should still display as 1 second on a countdown.
    assert format_hms(0.4) == "00:00:01"
    assert format_hms(0.0) == "00:00:00"


def test_format_stopwatch_shows_tenths():
    assert format_stopwatch(0) == "00:00:00.0"
    assert format_stopwatch(75.3) == "00:01:15.3"
    assert format_stopwatch(3661.9) == "01:01:01.9"
