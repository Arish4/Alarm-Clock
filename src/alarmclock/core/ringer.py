"""Ringer interface + implementations. The only sound/output side effects.

Tests inject a ``RecordingRinger`` so no real sound plays and rings can be
asserted exactly.
"""

from __future__ import annotations

import sys
from typing import Protocol

from .models import Alarm


class Ringer(Protocol):
    """Anything that can announce a ringing alarm."""

    def ring(self, alarm: Alarm) -> None:  # pragma: no cover - protocol
        ...


def _banner(alarm: Alarm) -> str:
    label = alarm.label or "(no label)"
    line = "=" * 44
    return (
        f"\n{line}\n"
        f"  ⏰  ALARM  {alarm.time}  —  {label}\n"
        f"{line}"
    )


class ConsoleRinger:
    """Prints a banner and attempts a sound; degrades to visual on failure."""

    def __init__(self, sound: bool = True):
        self.sound = sound

    def ring(self, alarm: Alarm) -> None:
        print(_banner(alarm))
        if not self.sound:
            return
        try:
            self._beep()
        except Exception:  # noqa: BLE001 - sound is best-effort only
            # Sound failure silently degrades to the visual banner.
            pass

    def _beep(self) -> None:
        # Best-effort cross-platform beep. winsound on Windows, else BEL.
        try:
            import winsound  # type: ignore

            winsound.Beep(880, 600)
            return
        except Exception:
            pass
        sys.stdout.write("\a")
        sys.stdout.flush()


class RecordingRinger:
    """Test double that records every ring instead of making noise."""

    def __init__(self) -> None:
        self.rings: list[Alarm] = []

    def ring(self, alarm: Alarm) -> None:
        self.rings.append(alarm)
