"""CLI commands (Command pattern).

Each command is a self-contained class that knows how to configure its own
arguments and execute itself against an :class:`AppContext`. The dispatcher
iterates a registry, so adding a command never means editing the dispatcher
(Open/Closed).
"""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod

from . import presenter
from .context import AppContext


def _split_tags(value: str | None) -> list[str]:
    if not value:
        return []
    return [t.strip() for t in value.split(",") if t.strip()]


class Command(ABC):
    """Base class for every CLI sub-command."""

    name: str
    help: str

    def configure(self, parser: argparse.ArgumentParser) -> None:
        """Add this command's arguments. Default: no extra arguments."""

    @abstractmethod
    def execute(self, args: argparse.Namespace, ctx: AppContext) -> int:
        """Run the command; return a process exit code."""

    def _print(self, ctx: AppContext, text: str) -> None:
        print(text, file=ctx.out)


class AddCommand(Command):
    name = "add"
    help = "add a new alarm"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("time", help="time: HH:MM (24h) or H:MMam/pm")
        parser.add_argument("--label", default="", help="a label for the alarm")
        parser.add_argument(
            "--repeat",
            default="",
            help="once | daily | weekdays | weekends | mon,tue,...",
        )
        parser.add_argument("--tag", default="", help="comma-separated tags")

    def execute(self, args: argparse.Namespace, ctx: AppContext) -> int:
        alarm = ctx.service.add(
            time=args.time,
            label=args.label,
            repeat=args.repeat,
            tags=_split_tags(args.tag),
        )
        self._print(
            ctx,
            f"added alarm {alarm.id}  {alarm.time}  "
            f"{alarm.label or '(no label)'}  [{alarm.repeat.describe()}]",
        )
        return 0


class ListCommand(Command):
    name = "list"
    help = "list alarms"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--tag", help="only show alarms with this tag")
        parser.add_argument(
            "--json", action="store_true", help="machine-readable output"
        )

    def execute(self, args: argparse.Namespace, ctx: AppContext) -> int:
        alarms = ctx.service.list(tag=args.tag)
        if args.json:
            self._print(ctx, presenter.alarms_json(alarms))
            return 0
        if not alarms:
            self._print(
                ctx,
                "no alarms set. add one with: "
                "alarmclock add 08:30 --label 'Wake up'",
            )
            return 0
        self._print(ctx, presenter.alarms_table(alarms))
        return 0


class NextCommand(Command):
    name = "next"
    help = "show when each alarm will next fire"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--json", action="store_true", help="machine-readable output"
        )

    def execute(self, args: argparse.Namespace, ctx: AppContext) -> int:
        alarms = ctx.service.list()
        now = ctx.clock.now()
        if args.json:
            self._print(ctx, presenter.next_json(alarms, ctx.scheduler, now))
            return 0
        if not alarms:
            self._print(ctx, "no alarms set.")
            return 0
        self._print(ctx, presenter.next_table(alarms, ctx.scheduler, now))
        return 0


class EditCommand(Command):
    name = "edit"
    help = "edit an existing alarm"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("id")
        parser.add_argument("--time", help="new time")
        parser.add_argument("--label", help="new label")
        parser.add_argument("--repeat", help="new repeat spec")
        parser.add_argument("--tag", help="replace tags (comma-separated)")

    def execute(self, args: argparse.Namespace, ctx: AppContext) -> int:
        alarm = ctx.service.edit(
            args.id,
            time=args.time,
            label=args.label,
            repeat=args.repeat,
            tags=_split_tags(args.tag) if args.tag is not None else None,
        )
        self._print(ctx, f"updated alarm {alarm.id}")
        return 0


class EnableCommand(Command):
    name = "enable"
    help = "enable an alarm"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("id")

    def execute(self, args: argparse.Namespace, ctx: AppContext) -> int:
        alarm = ctx.service.set_enabled(args.id, True)
        self._print(ctx, f"alarm {alarm.id} enabled")
        return 0


class DisableCommand(Command):
    name = "disable"
    help = "disable an alarm"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("id")

    def execute(self, args: argparse.Namespace, ctx: AppContext) -> int:
        alarm = ctx.service.set_enabled(args.id, False)
        self._print(ctx, f"alarm {alarm.id} disabled")
        return 0


class EnableAllCommand(Command):
    name = "enable-all"
    help = "enable every alarm"

    def execute(self, args: argparse.Namespace, ctx: AppContext) -> int:
        count = ctx.service.set_all_enabled(True)
        self._print(ctx, f"enabled {count} alarm(s)")
        return 0


class DisableAllCommand(Command):
    name = "disable-all"
    help = "disable every alarm"

    def execute(self, args: argparse.Namespace, ctx: AppContext) -> int:
        count = ctx.service.set_all_enabled(False)
        self._print(ctx, f"disabled {count} alarm(s)")
        return 0


class DeleteCommand(Command):
    name = "delete"
    help = "delete an alarm"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("id")

    def execute(self, args: argparse.Namespace, ctx: AppContext) -> int:
        ctx.service.delete(args.id)
        self._print(ctx, f"deleted alarm {args.id}")
        return 0


class HistoryCommand(Command):
    name = "history"
    help = "show recent alarm events"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--limit", type=int, default=20, help="how many events to show"
        )

    def execute(self, args: argparse.Namespace, ctx: AppContext) -> int:
        events = ctx.event_reader.recent(args.limit)
        if not events:
            self._print(ctx, "no events recorded yet.")
            return 0
        self._print(ctx, presenter.history_table(events))
        return 0


class RunCommand(Command):
    name = "run"
    help = "open the interactive menu (clock / stopwatch / timer / alarm)"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--snooze-minutes", type=int, default=9, help="alarm snooze duration"
        )
        parser.add_argument(
            "--max-snoozes",
            type=int,
            default=None,
            help="auto-dismiss after this many snoozes",
        )
        parser.add_argument(
            "--sound",
            default="auto",
            help="sound backend: auto | none | bell | beep",
        )
        parser.add_argument(
            "--no-sound", action="store_true", help="visual only, no sound"
        )

    def execute(self, args: argparse.Namespace, ctx: AppContext) -> int:
        sound = "none" if args.no_sound else args.sound
        menu = ctx.build_menu(
            sound=sound,
            snooze_minutes=args.snooze_minutes,
            max_snoozes=args.max_snoozes,
        )
        try:
            menu.run(ctx.console())
        except KeyboardInterrupt:
            self._print(ctx, "\nstopped.")
        return 0


class WatchCommand(Command):
    name = "watch"
    help = "directly watch and ring alarms (blocking, no menu)"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--snooze-minutes", type=int, default=9)
        parser.add_argument("--max-snoozes", type=int, default=None)
        parser.add_argument("--sound", default="auto")
        parser.add_argument("--no-sound", action="store_true")

    def execute(self, args: argparse.Namespace, ctx: AppContext) -> int:
        sound = "none" if args.no_sound else args.sound
        runner = ctx.build_runner(
            sound=sound,
            snooze_minutes=args.snooze_minutes,
            max_snoozes=args.max_snoozes,
        )
        now = ctx.clock.now().strftime("%H:%M")
        self._print(ctx, f"alarmclock watching (now {now}). press Ctrl-C to stop.")
        try:
            runner.run()
        except KeyboardInterrupt:
            self._print(ctx, "\nstopped.")
        return 0


def default_commands() -> list[Command]:
    """The registry of available commands (registration = extension point)."""
    return [
        AddCommand(),
        ListCommand(),
        NextCommand(),
        EditCommand(),
        EnableCommand(),
        DisableCommand(),
        EnableAllCommand(),
        DisableAllCommand(),
        DeleteCommand(),
        HistoryCommand(),
        RunCommand(),
        WatchCommand(),
    ]
