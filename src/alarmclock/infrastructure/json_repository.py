"""JSON-file alarm repository — the only place that touches alarm storage.

Implements the :class:`AlarmRepository` port. Saves are atomic (temp file +
``os.replace``) and reads tolerate missing/corrupt files.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from ..domain.alarm import Alarm

DEFAULT_DIRNAME = ".alarmclock"
DEFAULT_FILENAME = "alarms.json"


def default_config_path() -> Path:
    """Resolve the alarms path, honouring ``ALARMCLOCK_CONFIG`` for tests."""
    override = os.environ.get("ALARMCLOCK_CONFIG")
    if override:
        return Path(override)
    return Path.home() / DEFAULT_DIRNAME / DEFAULT_FILENAME


class JsonAlarmRepository:
    """A list[Alarm] persisted as a JSON array."""

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path is not None else default_config_path()

    def load(self) -> list[Alarm]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("expected a JSON array")
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            self._warn(
                f"could not read {self.path} ({exc}); starting with no alarms"
            )
            return []

        alarms: list[Alarm] = []
        for entry in data:
            try:
                alarms.append(Alarm.from_dict(entry))
            except Exception as exc:  # noqa: BLE001 - tolerate one bad record
                self._warn(f"skipping malformed alarm entry ({exc})")
        return alarms

    def save(self, alarms: list[Alarm]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            [a.to_dict() for a in alarms], indent=2, ensure_ascii=False
        )
        _atomic_write(self.path, payload)

    @staticmethod
    def _warn(message: str) -> None:
        print(f"warning: {message}", file=sys.stderr)


def _atomic_write(path: Path, payload: str) -> None:
    """Write ``payload`` to ``path`` atomically via a temp file + replace."""
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=".tmp-", suffix=".json"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
