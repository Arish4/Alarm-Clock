from datetime import datetime

from alarmclock.application.scheduler import Scheduler, minute_key
from alarmclock.domain.alarm import Alarm
from alarmclock.domain.repeat import Once, Weekly
from alarmclock.domain.time_of_day import TimeOfDay

# 2024-01-01 is a Monday.
MON_0830 = datetime(2024, 1, 1, 8, 30, 0)
MON_0831 = datetime(2024, 1, 1, 8, 31, 0)
TUE_0830 = datetime(2024, 1, 2, 8, 30, 0)


def make(**kw) -> Alarm:
    kw.setdefault("time", TimeOfDay(8, 30))
    return Alarm(**kw)


def setup_scheduler() -> Scheduler:
    return Scheduler()


def test_one_off_due_at_matching_minute():
    s = setup_scheduler()
    a = make(repeat=Once())
    assert s.is_due(a, MON_0830)
    assert not s.is_due(a, MON_0831)


def test_disabled_never_due():
    s = setup_scheduler()
    assert not s.is_due(make(enabled=False), MON_0830)


def test_weekly_due_only_on_listed_weekday():
    s = setup_scheduler()
    a = make(repeat=Weekly({0}))
    assert s.is_due(a, MON_0830)
    assert not s.is_due(a, TUE_0830)


def test_snoozed_fires_at_target_not_before():
    s = setup_scheduler()
    a = make(snoozed_until=datetime(2024, 1, 1, 8, 39))
    assert not s.is_due(a, MON_0831)
    assert s.is_due(a, datetime(2024, 1, 1, 8, 39))
    assert s.is_due(a, datetime(2024, 1, 1, 8, 40))


def test_once_per_minute_guard():
    s = setup_scheduler()
    a = make(repeat=Once())
    fired: dict[str, str] = {}
    assert s.due([a], MON_0830, fired) == [a]
    fired[a.id] = minute_key(MON_0830)
    assert s.due([a], MON_0830, fired) == []


def test_due_filters_mixed_set():
    s = setup_scheduler()
    on = make(label="on")
    off = make(label="off", enabled=False)
    later = make(time=TimeOfDay(9, 0), label="later")
    assert s.due([on, off, later], MON_0830, {}) == [on]


def test_next_occurrence_today_if_future():
    s = setup_scheduler()
    a = make(time=TimeOfDay(9, 0), repeat=Once())
    assert s.next_occurrence(a, MON_0830) == datetime(2024, 1, 1, 9, 0)


def test_next_occurrence_rolls_to_next_matching_weekday():
    s = setup_scheduler()
    a = make(time=TimeOfDay(8, 0), repeat=Weekly({1}))  # Tuesday
    # From Monday 08:30, next Tuesday 08:00.
    assert s.next_occurrence(a, MON_0830) == datetime(2024, 1, 2, 8, 0)


def test_next_occurrence_uses_snooze_time():
    s = setup_scheduler()
    a = make(snoozed_until=datetime(2024, 1, 1, 8, 39))
    assert s.next_occurrence(a, MON_0830) == datetime(2024, 1, 1, 8, 39)


def test_next_occurrence_none_when_disabled():
    s = setup_scheduler()
    assert s.next_occurrence(make(enabled=False), MON_0830) is None
