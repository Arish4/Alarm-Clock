"""Load/save list[Alarm] <-> JSON. The only module that touches the disk."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from .models import Alarm

DEFAULT_DIRNAME = ".alarmclock"
DEFAULT_FILENAME = "alarms.json"


def default_path() -> Path:
    """Resolve the config path, honouring ``ALARMCLOCK_CONFIG`` for tests."""
    override = os.environ.get("ALARMCLOCK_CONFIG")
    if override:
        return Path(override)
    return Path.home() / DEFAULT_DIRNAME / DEFAULT_FILENAME


class Store:
    """A JSON-file-backed collection of alarms."""

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path is not None else default_path()

    def load(self) -> list[Alarm]:
        """Load alarms. A missing or corrupt file yields an empty list.

        Corruption is reported on stderr as a warning rather than crashing,
        so a single bad byte never makes the tool unusable.
        """
        if not self.path.exists():
            return []
        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, list):
                raise ValueError("expected a JSON array")
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            print(
                f"warning: could not read {self.path} ({exc}); "
                "starting with an empty alarm list",
                file=sys.stderr,
            )
            return []

        alarms: list[Alarm] = []
        for entry in data:
            try:
                alarms.append(Alarm.from_dict(entry))
            except Exception as exc:  # noqa: BLE001 - tolerate one bad record
                print(
                    f"warning: skipping malformed alarm entry ({exc})",
                    file=sys.stderr,
                )
        return alarms

    def save(self, alarms: list[Alarm]) -> None:
        """Atomically persist alarms (write temp file, then replace)."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            [a.to_dict() for a in alarms], indent=2, ensure_ascii=False
        )
        # Write to a temp file in the same directory then atomically replace,
        # so a crash mid-write cannot corrupt the existing store.
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self.path.parent), prefix=".alarms-", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, self.path)
        except BaseException:
            # Clean up the temp file on any failure.
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
