"""Ringer implementations.

``ConsoleRinger`` composes a :class:`Notifier` (visual) and a ``SoundPlayer``
(audible) — favouring composition over inheritance and keeping each piece
single-purpose. ``RecordingRinger`` is the test double.
"""

from __future__ import annotations

import sys
from typing import TextIO

from ..application.interfaces import Notifier, SoundPlayer
from ..domain.alarm import Alarm
from .sound import NullSoundPlayer


class BannerNotifier:
    """Prints a prominent banner to a stream."""

    def __init__(self, stream: TextIO | None = None):
        self._stream = stream or sys.stdout

    def notify(self, alarm: Alarm) -> None:
        label = alarm.label or "(no label)"
        rule = "=" * 44
        fancy = f"\n{rule}\n  ⏰  ALARM  {alarm.time}  —  {label}\n{rule}"
        try:
            print(fancy, file=self._stream)
        except UnicodeEncodeError:
            # Console can't render the emoji/dash (e.g. Windows cp1252):
            # degrade to a plain-ASCII banner rather than crash the loop.
            ascii_banner = f"\n{rule}\n  >> ALARM  {alarm.time}  -  {label}\n{rule}"
            print(ascii_banner, file=self._stream)


class ConsoleRinger:
    """Rings by notifying visually and then playing a sound."""

    def __init__(
        self,
        notifier: Notifier | None = None,
        sound: SoundPlayer | None = None,
    ):
        self._notifier = notifier or BannerNotifier()
        self._sound = sound or NullSoundPlayer()

    def ring(self, alarm: Alarm) -> None:
        self._notifier.notify(alarm)
        self._sound.play()


class RecordingRinger:
    """Test double: records every ring instead of producing output."""

    def __init__(self) -> None:
        self.rings: list[Alarm] = []

    def ring(self, alarm: Alarm) -> None:
        self.rings.append(alarm)
