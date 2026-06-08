from datetime import datetime

from alarmclock.core.clock import FakeClock
from alarmclock.core.models import Alarm
from alarmclock.core.ringer import RecordingRinger
from alarmclock.core.store import Store
from alarmclock.runner import Runner

MON_0830 = datetime(2024, 1, 1, 8, 30, 0)


def _runner(tmp_path, clock, ringer, responder, snooze=9):
    store = Store(tmp_path / "alarms.json")
    return store, Runner(
        store=store,
        clock=clock,
        ringer=ringer,
        snooze_minutes=snooze,
        responder=responder,
    )


def test_single_tick_rings_exactly_once(tmp_path):
    clock = FakeClock(MON_0830)
    ringer = RecordingRinger()
    store, runner = _runner(tmp_path, clock, ringer, lambda a: "dismiss")
    alarms = [Alarm(time="08:30", label="Wake")]
    store.save(alarms)

    runner.tick(alarms)
    assert len(ringer.rings) == 1
    # Same minute, ticking again must NOT ring a second time.
    runner.tick(alarms)
    assert len(ringer.rings) == 1


def test_one_off_auto_disables_after_dismiss(tmp_path):
    clock = FakeClock(MON_0830)
    ringer = RecordingRinger()
    store, runner = _runner(tmp_path, clock, ringer, lambda a: "dismiss")
    alarms = [Alarm(time="08:30")]
    runner.tick(alarms)
    assert alarms[0].enabled is False
    # Persisted to disk too.
    assert store.load()[0].enabled is False


def test_snooze_rearms_and_rings_again(tmp_path):
    clock = FakeClock(MON_0830)
    ringer = RecordingRinger()
    store, runner = _runner(
        tmp_path, clock, ringer, lambda a: "snooze", snooze=9
    )
    alarms = [Alarm(time="08:30")]
    runner.tick(alarms)
    assert ringer.rings and alarms[0].snoozed_until == "2024-01-01T08:39"

    # Advance to the snooze target; it should ring again.
    clock.advance(9 * 60)
    runner.tick(alarms)
    assert len(ringer.rings) == 2


def test_run_loop_with_fake_clock_no_real_sleep(tmp_path):
    clock = FakeClock(MON_0830)
    ringer = RecordingRinger()
    store, runner = _runner(tmp_path, clock, ringer, lambda a: "dismiss")
    store.save([Alarm(time="08:30")])

    runner.run(max_ticks=3, tick_seconds=1.0)
    # Rang once; sleeps advanced the fake clock, no real waiting occurred.
    assert len(ringer.rings) == 1
    assert clock.sleeps == [1.0, 1.0, 1.0]
