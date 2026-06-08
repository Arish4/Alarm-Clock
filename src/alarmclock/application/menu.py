"""The interactive main menu.

Knows nothing about specific features — it lists whatever :class:`Feature`
objects it is given and dispatches to them, so new features need no menu
changes (Open/Closed).
"""

from __future__ import annotations

from typing import Sequence

from .features import Feature
from .interfaces import Console


class InteractiveMenu:
    def __init__(self, features: Sequence[Feature], title: str = "alarmclock"):
        self._features = list(features)
        self._title = title

    def run(self, console: Console) -> None:
        while True:
            self._render(console)
            choice = console.read_line("  choose: ").strip().lower()
            if choice in ("q", "quit", "exit", ""):
                console.write_line("  bye!")
                return
            feature = self._select(choice)
            if feature is None:
                continue
            feature.run(console)

    def _render(self, console: Console) -> None:
        console.clear()
        console.write_line(f"  {self._title}")
        console.write_line("  " + "=" * len(self._title))
        console.write_line()
        for index, feature in enumerate(self._features, start=1):
            console.write_line(f"    {index}. {feature.name}")
        console.write_line()
        console.write_line("    q. quit")
        console.write_line()

    def _select(self, choice: str) -> Feature | None:
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(self._features):
                return self._features[index]
        for feature in self._features:
            if choice == feature.name.lower():
                return feature
        return None
