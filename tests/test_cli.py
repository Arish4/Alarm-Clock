"""Integration tests for the CLI, driven through an injected AppContext.

A fake clock, recording ringer, scripted responder and in-memory events keep
the tests deterministic with no real sleeping or sound.
"""

from __future__ import annotations

import io
from datetime import datetime

import pytest

from alarmclock.application.interfaces import Decision
from alarmclock.application.scheduler import Scheduler
from alarmclock.application.services import AlarmService
from alarmclock.cli.app import main
from alarmclock.cli.context import AppContext
from alarmclock.infrastructure.clock import FakeClock
from alarmclock.infrastructure.event_log import InMemoryEventSink
from alarmclock.infrastructure.json_repository import JsonAlarmRepository
from alarmclock.infrastructure.responder import ScriptedResponder
from alarmclock.infrastructure.ringer import RecordingRinger

MON_0830 = datetime(2024, 1, 1, 8, 30, 0)


@pytest.fixture
def ctx(tmp_path):
    out = io.StringIO()
    repo = JsonAlarmRepository(tmp_path / "alarms.json")
    events = InMemoryEventSink()
    ringer = RecordingRinger()
    context = AppContext(
        service=AlarmService(repo),
        scheduler=Scheduler(),
        repository=repo,
        clock=FakeClock(MON_0830),
        events=events,
        event_reader=events,
        out=out,
        make_ringer=lambda sound: ringer,
        make_responder=lambda: ScriptedResponder([Decision.DISMISS]),
    )
    context._out = out  # convenience handle for assertions
    context._ringer = ringer
    return context


def run(argv, ctx):
    return main(argv, context=ctx)


def test_add_list_edit_delete_flow(ctx):
    assert run(["add", "08:30", "--label", "Wake", "--repeat", "weekdays",
                "--tag", "home"], ctx) == 0
    assert "added alarm" in ctx._out.getvalue()

    assert run(["list"], ctx) == 0
    listing = ctx._out.getvalue()
    assert "Wake" in listing and "weekdays" in listing and "home" in listing

    alarm_id = ctx.service.list()[0].id

    assert run(["edit", alarm_id, "--label", "Get up"], ctx) == 0
    assert ctx.service.get(alarm_id).label == "Get up"

    assert run(["disable", alarm_id], ctx) == 0
    assert ctx.service.get(alarm_id).enabled is False

    assert run(["delete", alarm_id], ctx) == 0
    assert ctx.service.list() == []


def test_list_json_output(ctx):
    run(["add", "08:30", "--label", "Wake"], ctx)
    ctx._out.truncate(0)
    ctx._out.seek(0)
    assert run(["list", "--json"], ctx) == 0
    assert '"label": "Wake"' in ctx._out.getvalue()


def test_next_command(ctx):
    run(["add", "09:00", "--label", "Later"], ctx)
    ctx._out.truncate(0)
    ctx._out.seek(0)
    assert run(["next"], ctx) == 0
    out = ctx._out.getvalue()
    assert "NEXT FIRE" in out and "09:00" in out


def test_enable_all_disable_all(ctx):
    run(["add", "08:30"], ctx)
    run(["add", "09:00"], ctx)
    assert run(["disable-all"], ctx) == 0
    assert all(not a.enabled for a in ctx.service.list())
    assert run(["enable-all"], ctx) == 0
    assert all(a.enabled for a in ctx.service.list())


def test_run_rings_via_injected_context(ctx):
    run(["add", "08:30", "--label", "Wake"], ctx)
    # Build the runner through the context, bounded for the test.
    runner = ctx.build_runner(sound="none", snooze_minutes=9, max_snoozes=None)
    runner.run(max_ticks=2, tick_seconds=0)
    assert len(ctx._ringer.rings) == 1


def test_history_command(ctx):
    run(["add", "08:30", "--label", "Wake"], ctx)
    runner = ctx.build_runner(sound="none", snooze_minutes=9, max_snoozes=None)
    runner.run(max_ticks=1, tick_seconds=0)
    ctx._out.truncate(0)
    ctx._out.seek(0)
    assert run(["history"], ctx) == 0
    assert "rang" in ctx._out.getvalue()


def test_invalid_time_returns_validation_error(ctx, capsys):
    assert run(["add", "25:00"], ctx) == 2
    assert "error" in capsys.readouterr().err.lower()


def test_unknown_id_returns_error(ctx, capsys):
    assert run(["enable", "nope"], ctx) == 1
    assert "no alarm" in capsys.readouterr().err.lower()
