"""Sound players (Strategy + Factory).

Open/Closed: adding a new audio backend means adding a ``SoundPlayer`` class and
registering it — nothing else changes. Every player swallows its own errors so a
broken sound backend can never crash the run loop (it degrades to silence and
the caller's visual banner still shows).
"""

from __future__ import annotations

import sys
from typing import Callable

from ..domain.errors import ValidationError


class NullSoundPlayer:
    """Plays nothing (used for ``--no-sound`` and in tests)."""

    def play(self) -> None:
        return None


class TerminalBellPlayer:
    """Emits the ASCII BEL character — works on most terminals."""

    def play(self) -> None:
        try:
            sys.stdout.write("\a")
            sys.stdout.flush()
        except Exception:  # noqa: BLE001 - sound is best-effort only
            pass


class WinsoundPlayer:
    """Beeps via the Windows ``winsound`` API, falling back to the bell."""

    def __init__(self, frequency: int = 880, duration_ms: int = 600):
        self._frequency = frequency
        self._duration_ms = duration_ms
        self._fallback = TerminalBellPlayer()

    def play(self) -> None:
        try:
            import winsound  # type: ignore

            winsound.Beep(self._frequency, self._duration_ms)
        except Exception:  # noqa: BLE001 - degrade to the terminal bell
            self._fallback.play()


_PLAYERS: dict[str, Callable[[], object]] = {
    "none": NullSoundPlayer,
    "bell": TerminalBellPlayer,
    "beep": WinsoundPlayer,
}


def register_sound_player(name: str, factory: Callable[[], object]) -> None:
    """Register a named sound backend (Open/Closed extension point)."""
    _PLAYERS[name] = factory


def available_backends() -> list[str]:
    return sorted(_PLAYERS)


def create_sound_player(name: str = "auto"):
    """Build a sound player by name. ``auto`` picks the best for the platform."""
    if name == "auto":
        name = "beep" if sys.platform.startswith("win") else "bell"
    if name not in _PLAYERS:
        raise ValidationError(
            f"unknown sound backend {name!r}: choose from "
            f"{', '.join(available_backends())} or 'auto'"
        )
    return _PLAYERS[name]()
