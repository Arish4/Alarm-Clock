"""CLI entry point: builds the parser from the command registry and dispatches.

The dispatcher is closed for modification — it knows nothing about specific
commands, only the :class:`Command` contract and the registry.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from .. import __version__
from ..domain.errors import AlarmClockError, ValidationError
from .commands import Command, default_commands
from .context import AppContext, build_context


def build_parser(commands: Sequence[Command]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alarmclock", description="A small, SOLID, CLI alarm clock."
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--config", metavar="PATH", help="path to the alarms JSON file"
    )
    parser.add_argument(
        "--history", metavar="PATH", help="path to the event history file"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for command in commands:
        sub_parser = sub.add_parser(command.name, help=command.help)
        command.configure(sub_parser)
        sub_parser.set_defaults(_handler=command)
    return parser


def main(
    argv: list[str] | None = None,
    context: AppContext | None = None,
) -> int:
    """Program entry point. ``context`` can be injected for testing."""
    commands = default_commands()
    parser = build_parser(commands)
    args = parser.parse_args(argv)

    ctx = context or build_context(
        config_path=getattr(args, "config", None),
        history_path=getattr(args, "history", None),
    )

    handler: Command = args._handler
    try:
        return handler.execute(args, ctx)
    except ValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except AlarmClockError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
