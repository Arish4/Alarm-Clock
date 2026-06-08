"""Responders: how a ringing alarm's snooze/dismiss choice is obtained."""

from __future__ import annotations

from typing import Callable

from ..application.interfaces import Decision
from ..domain.alarm import Alarm


class ConsoleResponder:
    """Interactively prompts the user at the terminal."""

    def __init__(self, prompt: Callable[[str], str] = input):
        self._prompt = prompt

    def respond(self, alarm: Alarm) -> Decision:
        while True:
            try:
                choice = self._prompt("[s]nooze / [d]ismiss? ").strip().lower()
            except EOFError:
                return Decision.DISMISS
            if choice in ("s", "snooze"):
                return Decision.SNOOZE
            if choice in ("d", "dismiss", ""):
                return Decision.DISMISS
            print("please enter 's' to snooze or 'd' to dismiss")


class ScriptedResponder:
    """Returns predetermined decisions (used in tests)."""

    def __init__(self, decisions: list[Decision], default: Decision = Decision.DISMISS):
        self._decisions = list(decisions)
        self._default = default

    def respond(self, alarm: Alarm) -> Decision:
        if self._decisions:
            return self._decisions.pop(0)
        return self._default
