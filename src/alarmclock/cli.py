"""Argument parsing, command dispatch and output formatting (kept thin).

All the real work lives in ``core`` and ``runner``; this module only wires
user input to those pieces and formats results.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from . import __version__
from .core.clock import SystemClock
from .core.models import Alarm, ValidationError, parse_repeat, parse_time
from .core.ringer import ConsoleRinger
from .core.store import Store
from .runner import Runner


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alarmclock",
        description="A small, testable CLI alarm clock.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="path to the alarms JSON file (overrides default / env)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a new alarm")
    p_add.add_argument("time", help="alarm time in 24h HH:MM")
    p_add.add_argument("--label", default="", help="a label for the alarm")
    p_add.add_argument(
        "--repeat",
        default="",
        help="comma-separated weekdays e.g. mon,tue,fri (omit for one-off)",
    )

    sub.add_parser("list", help="list all alarms")

    p_enable = sub.add_parser("enable", help="enable an alarm by id")
    p_enable.add_argument("id")
    p_disable = sub.add_parser("disable", help="disable an alarm by id")
    p_disable.add_argument("id")
    p_delete = sub.add_parser("delete", help="delete an alarm by id")
    p_delete.add_argument("id")

    p_run = sub.add_parser("run", help="watch and ring alarms (blocking)")
    p_run.add_argument(
        "--snooze-minutes", type=int, default=9, help="snooze duration"
    )
    p_run.add_argument(
        "--no-sound", action="store_true", help="visual banner only"
    )
    return parser


def _store(args: argparse.Namespace) -> Store:
    return Store(args.config) if args.config else Store()


def _find(alarms: list[Alarm], alarm_id: str) -> Alarm | None:
    for alarm in alarms:
        if alarm.id == alarm_id:
            return alarm
    return None


def cmd_add(args: argparse.Namespace) -> int:
    store = _store(args)
    time = parse_time(args.time)
    repeat = parse_repeat(args.repeat)
    alarm = Alarm(time=time, label=args.label, repeat=repeat)
    alarms = store.load()
    alarms.append(alarm)
    store.save(alarms)
    print(f"added alarm {alarm.id}  {alarm.time}  {alarm.label or '(no label)'}"
          f"  [{alarm.repeat_display()}]")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = _store(args)
    alarms = store.load()
    if not alarms:
        print("no alarms set. add one with: alarmclock add 08:30 --label 'Wake up'")
        return 0
    rows = [("ID", "TIME", "LABEL", "REPEAT", "STATUS")]
    for a in alarms:
        rows.append(
            (a.id, a.time, a.label or "-", a.repeat_display(), a.status_display())
        )
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    for i, row in enumerate(rows):
        line = "  ".join(cell.ljust(widths[j]) for j, cell in enumerate(row))
        print(line)
        if i == 0:
            print("  ".join("-" * widths[j] for j in range(len(widths))))
    return 0


def _set_enabled(args: argparse.Namespace, enabled: bool) -> int:
    store = _store(args)
    alarms = store.load()
    alarm = _find(alarms, args.id)
    if alarm is None:
        print(f"error: no alarm with id {args.id!r}", file=sys.stderr)
        return 1
    alarm.enabled = enabled
    if enabled:
        alarm.snoozed_until = None
    store.save(alarms)
    print(f"alarm {alarm.id} {'enabled' if enabled else 'disabled'}")
    return 0


def cmd_enable(args: argparse.Namespace) -> int:
    return _set_enabled(args, True)


def cmd_disable(args: argparse.Namespace) -> int:
    return _set_enabled(args, False)


def cmd_delete(args: argparse.Namespace) -> int:
    store = _store(args)
    alarms = store.load()
    alarm = _find(alarms, args.id)
    if alarm is None:
        print(f"error: no alarm with id {args.id!r}", file=sys.stderr)
        return 1
    alarms = [a for a in alarms if a.id != args.id]
    store.save(alarms)
    print(f"deleted alarm {args.id}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    store = _store(args)
    ringer = ConsoleRinger(sound=not args.no_sound)
    runner = Runner(
        store=store,
        clock=SystemClock(),
        ringer=ringer,
        snooze_minutes=args.snooze_minutes,
    )
    now = datetime.now().strftime("%H:%M")
    print(f"alarmclock running (now {now}). press Ctrl-C to stop.")
    try:
        runner.run()
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


_COMMANDS = {
    "add": cmd_add,
    "list": cmd_list,
    "enable": cmd_enable,
    "disable": cmd_disable,
    "delete": cmd_delete,
    "run": cmd_run,
}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    handler = _COMMANDS[args.command]
    try:
        return handler(args)
    except ValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
