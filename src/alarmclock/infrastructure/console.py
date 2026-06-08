"""Console adapters implementing the ``Console`` port.

``TerminalConsole`` drives a real terminal with cross-platform non-blocking key
reads. ``ScriptedConsole`` replays predetermined keys/lines and records output
so the interactive features can be tested with no real terminal.
"""

from __future__ import annotations

import os
import sys
from typing import TextIO

try:  # Windows
    import msvcrt  # type: ignore
except ImportError:  # pragma: no cover - non-Windows
    msvcrt = None


class TerminalConsole:
    """A real terminal. Clears with ANSI and reads keys without Enter."""

    def __init__(self, stream: TextIO | None = None):
        self._out = stream or sys.stdout
        self._enable_ansi_on_windows()

    @staticmethod
    def _enable_ansi_on_windows() -> None:
        if os.name != "nt":
            return
        try:  # pragma: no cover - platform specific
            import ctypes

            kernel32 = ctypes.windll.kernel32
            # ENABLE_PROCESSED_OUTPUT | ENABLE_WRAP | ENABLE_VT_PROCESSING
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass

    def clear(self) -> None:
        try:
            self._out.write("\033[2J\033[H")
            self._out.flush()
        except Exception:  # pragma: no cover - degrade silently
            pass

    def write_line(self, text: str = "") -> None:
        print(text, file=self._out)

    def read_line(self, prompt: str = "") -> str:
        try:
            return input(prompt)
        except EOFError:
            return ""

    def read_key(self) -> str | None:
        if msvcrt is not None:  # pragma: no cover - Windows path
            if msvcrt.kbhit():
                return msvcrt.getwch()
            return None
        return self._read_key_posix()

    @staticmethod
    def _read_key_posix() -> str | None:  # pragma: no cover - POSIX path
        import select
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            ready, _, _ = select.select([sys.stdin], [], [], 0)
            if ready:
                return sys.stdin.read(1)
            return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


class ScriptedConsole:
    """Test double: replays queued keys/lines and captures output.

    ``read_key`` returns ``"q"`` once its queue is exhausted so live loops in
    tests always terminate.
    """

    def __init__(
        self,
        keys: list[str | None] | None = None,
        lines: list[str] | None = None,
    ):
        self.keys: list[str | None] = list(keys or [])
        self.lines: list[str] = list(lines or [])
        self.output: list[str] = []

    def clear(self) -> None:
        self.output.append("<clear>")

    def write_line(self, text: str = "") -> None:
        self.output.append(text)

    def read_line(self, prompt: str = "") -> str:
        return self.lines.pop(0) if self.lines else ""

    def read_key(self) -> str | None:
        if self.keys:
            return self.keys.pop(0)
        return "q"

    @property
    def text(self) -> str:
        return "\n".join(self.output)
