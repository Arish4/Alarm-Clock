from datetime import datetime

from alarmclock.application.interfaces import Decision
from alarmclock.application.runner import AlarmRunner
from alarmclock.domain.alarm import Alarm
from alarmclock.domain.events import EventKind
from alarmclock.domain.repeat import Once, Weekly
from alarmclock.domain.time_of_day import TimeOfDay
from alarmclock.infrastructure.clock import FakeClock
from alarmclock.infrastructure.event_log import InMemoryEventSink
from alarmclock.infrastructure.json_repository import JsonAlarmRepository
from alarmclock.infrastructure.responder import ScriptedResponder
from alarmclock.infrastructure.ringer import RecordingRinger

MON_0830 = datetime(2024, 1, 1, 8, 30, 0)


def build(tmp_path, decisions, *, snooze=9, max_snoozes=None):
    repo = JsonAlarmRepository(tmp_path / "alarms.json")
    clock = FakeClock(MON_0830)
    ringer = RecordingRinger()
    events = InMemoryEventSink()
    responder = ScriptedResponder(decisions)
    runner = AlarmRunner(
        repository=repo,
        clock=clock,
        ringer=ringer,
        responder=responder,
        events=events,
        snooze_minutes=snooze,
        max_snoozes=max_snoozes,
    )
    return repo, clock, ringer, events, runner


def test_single_tick_rings_exactly_once(tmp_path):
    repo, clock, ringer, events, runner = build(tmp_path, [Decision.DISMISS])
    alarms = [Alarm(time=TimeOfDay(8, 30), label="Wake")]
    repo.save(alarms)

    runner.tick(alarms)
    assert len(ringer.rings) == 1
    runner.tick(alarms)  # same minute -> guarded
    assert len(ringer.rings) == 1
    assert events.events[0].kind == EventKind.RANG


def test_one_off_auto_disables_after_dismiss(tmp_path):
    repo, clock, ringer, events, runner = build(tmp_path, [Decision.DISMISS])
    alarms = [Alarm(time=TimeOfDay(8, 30), repeat=Once())]
    runner.tick(alarms)
    assert alarms[0].enabled is False
    assert repo.load()[0].enabled is False


def test_snooze_rearms_and_rings_again(tmp_path):
    repo, clock, ringer, events, runner = build(
        tmp_path, [Decision.SNOOZE, Decision.DISMISS], snooze=9
    )
    alarms = [Alarm(time=TimeOfDay(8, 30))]
    runner.tick(alarms)
    assert alarms[0].snoozed_until == datetime(2024, 1, 1, 8, 39)
    assert events.events[-1].kind == EventKind.SNOOZED

    clock.advance(9 * 60)
    runner.tick(alarms)
    assert len(ringer.rings) == 2


def test_max_snoozes_auto_dismisses(tmp_path):
    repo, clock, ringer, events, runner = build(
        tmp_path, [Decision.SNOOZE], snooze=1, max_snoozes=0
    )
    alarms = [Alarm(time=TimeOfDay(8, 30), repeat=Once())]
    runner.tick(alarms)
    # Wanted to snooze but limit is 0 -> auto-dismissed.
    assert alarms[0].is_snoozed is False
    assert events.events[-1].kind == EventKind.AUTO_DISMISSED


def test_run_loop_with_fake_clock_no_real_sleep(tmp_path):
    repo, clock, ringer, events, runner = build(tmp_path, [Decision.DISMISS])
    repo.save([Alarm(time=TimeOfDay(8, 30))])

    runner.run(max_ticks=3, tick_seconds=1.0)
    assert len(ringer.rings) == 1
    assert clock.sleeps == [1.0, 1.0, 1.0]


def test_weekly_alarm_only_rings_on_its_day(tmp_path):
    repo, clock, ringer, events, runner = build(tmp_path, [Decision.DISMISS])
    # Tuesday-only alarm, but "now" is Monday.
    alarms = [Alarm(time=TimeOfDay(8, 30), repeat=Weekly({1}))]
    repo.save(alarms)
    runner.tick(alarms)
    assert ringer.rings == []
