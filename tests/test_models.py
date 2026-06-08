import pytest

from alarmclock.core.models import (
    Alarm,
    ValidationError,
    parse_repeat,
    parse_time,
)


@pytest.mark.parametrize(
    "raw,expected",
    [("08:30", "08:30"), ("8:5", "08:05"), ("23:59", "23:59"), ("00:00", "00:00")],
)
def test_parse_time_valid(raw, expected):
    assert parse_time(raw) == expected


@pytest.mark.parametrize("raw", ["24:00", "12:60", "abc", "1230", "", "12:", ":30"])
def test_parse_time_invalid(raw):
    with pytest.raises(ValidationError):
        parse_time(raw)


def test_parse_repeat_normalises_order_and_dedupes():
    assert parse_repeat("fri,mon,mon") == ["mon", "fri"]


def test_parse_repeat_empty_is_one_off():
    assert parse_repeat("") == []
    assert parse_repeat(None) == []


def test_parse_repeat_rejects_unknown():
    with pytest.raises(ValidationError):
        parse_repeat("mon,funday")


def test_alarm_roundtrip_dict():
    a = Alarm(time="07:00", label="Wake", repeat=["mon", "fri"])
    restored = Alarm.from_dict(a.to_dict())
    assert restored.to_dict() == a.to_dict()


def test_repeat_and_status_display():
    daily = Alarm(time="06:00", repeat=list(["mon", "tue", "wed", "thu", "fri", "sat", "sun"]))
    assert daily.repeat_display() == "daily"
    once = Alarm(time="06:00")
    assert once.repeat_display() == "once"
    assert once.status_display() == "armed"
    once.enabled = False
    assert once.status_display() == "disabled"
