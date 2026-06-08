from datetime import date

import pytest

from alarmclock.domain.errors import ValidationError
from alarmclock.domain.repeat import (
    Daily,
    Once,
    Weekly,
    parse_repeat,
)

# 2024-01-01 is a Monday; 2024-01-06 is a Saturday.
MONDAY = date(2024, 1, 1)
SATURDAY = date(2024, 1, 6)


def test_once_is_one_off_and_always_occurs():
    p = Once()
    assert p.is_one_off
    assert p.occurs_on(MONDAY)
    assert p.describe() == "once"


def test_daily_occurs_every_day():
    p = Daily()
    assert not p.is_one_off
    assert p.occurs_on(MONDAY) and p.occurs_on(SATURDAY)


def test_weekly_occurs_only_on_listed_days():
    p = Weekly({0})  # Monday only
    assert p.occurs_on(MONDAY)
    assert not p.occurs_on(SATURDAY)


@pytest.mark.parametrize(
    "spec,describe",
    [
        ("once", "once"),
        ("", "once"),
        ("daily", "daily"),
        ("weekdays", "weekdays"),
        ("weekends", "weekends"),
        ("mon,fri", "mon,fri"),
        ("fri,mon,mon", "mon,fri"),
    ],
)
def test_parse_repeat_specs(spec, describe):
    assert parse_repeat(spec).describe() == describe


def test_parse_repeat_legacy_list():
    assert parse_repeat([]).describe() == "once"
    assert parse_repeat(["mon", "fri"]).describe() == "mon,fri"


def test_parse_repeat_rejects_unknown():
    with pytest.raises(ValidationError):
        parse_repeat("mon,funday")


def test_to_spec_roundtrips():
    for spec in ["once", "daily", "mon,fri"]:
        policy = parse_repeat(spec)
        assert parse_repeat(policy.to_spec()) == policy


def test_weekly_requires_a_day():
    with pytest.raises(ValidationError):
        Weekly(set())
