from datetime import datetime

import pytest

from alarmclock.domain.errors import ValidationError
from alarmclock.domain.time_of_day import TimeOfDay


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("08:30", (8, 30)),
        ("8:5", (8, 5)),
        ("23:59", (23, 59)),
        ("00:00", (0, 0)),
        ("8:30am", (8, 30)),
        ("12:00am", (0, 0)),
        ("12:00pm", (12, 0)),
        ("1:15 PM", (13, 15)),
        ("11:45p.m.", (23, 45)),
    ],
)
def test_parse_valid(raw, expected):
    tod = TimeOfDay.parse(raw)
    assert (tod.hour, tod.minute) == expected


@pytest.mark.parametrize("raw", ["24:00", "12:60", "abc", "1230", "", "13:00pm", "0:00am"])
def test_parse_invalid(raw):
    with pytest.raises(ValidationError):
        TimeOfDay.parse(raw)


def test_str_is_zero_padded_24h():
    assert str(TimeOfDay.parse("8:5")) == "08:05"
    assert str(TimeOfDay.parse("1:15pm")) == "13:15"


def test_matches_moment():
    tod = TimeOfDay(8, 30)
    assert tod.matches(datetime(2024, 1, 1, 8, 30, 59))
    assert not tod.matches(datetime(2024, 1, 1, 8, 31, 0))


def test_ordering():
    assert TimeOfDay(7, 0) < TimeOfDay(8, 30)
