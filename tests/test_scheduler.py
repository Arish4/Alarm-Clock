from datetime import datetime

from alarmclock.core.models import Alarm
from alarmclock.core.scheduler import due_alarms, is_due, minute_key

# 2024-01-01 was a Monday. 08:30.
MON_0830 = datetime(2024, 1, 1, 8, 30, 0)
MON_0831 = datetime(2024, 1, 1, 8, 31, 0)
TUE_0830 = datetime(2024, 1, 2, 8, 30, 0)


def test_one_off_due_at_matching_minute():
    a = Alarm(time="08:30")
    assert is_due(a, MON_0830)
    assert not is_due(a, MON_0831)


def test_disabled_never_due():
    a = Alarm(time="08:30", enabled=False)
    assert not is_due(a, MON_0830)


def test_repeat_due_only_on_listed_weekday():
    a = Alarm(time="08:30", repeat=["mon"])
    assert is_due(a, MON_0830)
    assert not is_due(a, TUE_0830)


def test_repeat_due_on_each_listed_day():
    a = Alarm(time="08:30", repeat=["mon", "tue"])
    assert is_due(a, MON_0830)
    assert is_due(a, TUE_0830)


def test_snoozed_fires_at_target_not_before():
    a = Alarm(time="08:30", snoozed_until="2024-01-01T08:39")
    # Before the snooze target: schedule is suppressed while snoozed.
    assert not is_due(a, MON_0831)
    # At/after the snooze target it fires.
    assert is_due(a, datetime(2024, 1, 1, 8, 39))
    assert is_due(a, datetime(2024, 1, 1, 8, 40))


def test_once_per_minute_guard():
    a = Alarm(time="08:30")
    fired: dict[str, str] = {}
    first = due_alarms([a], MON_0830, fired)
    assert first == [a]
    # Simulate the runner recording the fire, then ticking again same minute.
    fired[a.id] = minute_key(MON_0830)
    second = due_alarms([a], MON_0830, fired)
    assert second == []


def test_due_alarms_filters_mixed_set():
    on = Alarm(time="08:30", label="on")
    off = Alarm(time="08:30", label="off", enabled=False)
    other = Alarm(time="09:00", label="later")
    due = due_alarms([on, off, other], MON_0830, {})
    assert due == [on]
