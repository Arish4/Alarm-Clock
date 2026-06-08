from datetime import datetime

from alarmclock.domain.alarm import Alarm
from alarmclock.domain.repeat import Once, Weekly, parse_repeat
from alarmclock.domain.time_of_day import TimeOfDay


def make(**kw) -> Alarm:
    kw.setdefault("time", TimeOfDay(8, 30))
    return Alarm(**kw)


def test_snooze_sets_time_and_counts():
    a = make()
    a.snooze(datetime(2024, 1, 1, 8, 39))
    assert a.is_snoozed
    assert a.snoozed_until == datetime(2024, 1, 1, 8, 39)
    assert a.snooze_count == 1


def test_dismiss_clears_snooze_and_disables_one_off():
    a = make(repeat=Once())
    a.snooze(datetime(2024, 1, 1, 8, 39))
    a.dismiss()
    assert not a.is_snoozed
    assert a.snooze_count == 0
    assert a.enabled is False


def test_dismiss_keeps_repeating_alarm_enabled():
    a = make(repeat=Weekly({0}))
    a.dismiss()
    assert a.enabled is True


def test_has_tag_is_case_insensitive():
    a = make(tags=["Work"])
    assert a.has_tag("work")
    assert not a.has_tag("home")


def test_roundtrip_dict_preserves_state():
    a = make(
        label="Wake",
        repeat=parse_repeat("mon,fri"),
        tags=["home"],
        snoozed_until=datetime(2024, 1, 1, 8, 39),
        snooze_count=2,
    )
    restored = Alarm.from_dict(a.to_dict())
    assert restored.to_dict() == a.to_dict()


def test_from_dict_accepts_legacy_list_repeat():
    a = Alarm.from_dict({"time": "08:00", "repeat": ["mon", "fri"]})
    assert a.repeat.describe() == "mon,fri"
