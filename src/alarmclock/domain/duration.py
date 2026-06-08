"""Duration parsing and formatting (pure helpers).

Single Responsibility: convert between human duration text and seconds, and
render seconds for display. No I/O.
"""

from __future__ import annotations

import math
import re

from .errors import ValidationError

_UNIT = re.compile(r"(\d+)\s*(h|m|s)", re.IGNORECASE)
_SECONDS_PER = {"h": 3600, "m": 60, "s": 1}


def parse_duration(text: str) -> int:
    """Parse a duration into whole seconds.

    Accepts ``90s``, ``5m``, ``1h30m``, ``MM:SS``, ``HH:MM:SS`` or a bare
    integer number of seconds. Must be greater than zero.
    """
    if text is None:
        raise ValidationError("missing duration")
    raw = text.strip().lower()
    if not raw:
        raise ValidationError("missing duration")

    if ":" in raw:
        total = _parse_colon(raw)
    elif raw.isdigit():
        total = int(raw)
    else:
        total = _parse_units(raw)

    if total <= 0:
        raise ValidationError(f"duration {text!r} must be greater than zero")
    return total


def _parse_colon(raw: str) -> int:
    parts = raw.split(":")
    if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
        raise ValidationError(f"invalid duration {raw!r}: expected MM:SS or HH:MM:SS")
    nums = [int(p) for p in parts]
    if len(nums) == 2:
        hours, minutes, seconds = 0, nums[0], nums[1]
    else:
        hours, minutes, seconds = nums
    if minutes >= 60 or seconds >= 60:
        raise ValidationError(f"invalid duration {raw!r}: minutes/seconds must be < 60")
    return hours * 3600 + minutes * 60 + seconds


def _parse_units(raw: str) -> int:
    matches = list(_UNIT.finditer(raw))
    leftover = _UNIT.sub("", raw).strip()
    if not matches or leftover:
        raise ValidationError(
            f"invalid duration {raw!r}: try e.g. 30s, 5m, 1h30m or 10:00"
        )
    return sum(int(v) * _SECONDS_PER[u.lower()] for v, u in (m.groups() for m in matches))


def format_hms(seconds: float) -> str:
    """Render seconds as ``HH:MM:SS`` (rounded up — good for countdowns)."""
    total = int(math.ceil(max(0.0, seconds) - 1e-9))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_stopwatch(seconds: float) -> str:
    """Render seconds as ``HH:MM:SS.t`` (tenths — good for stopwatches)."""
    tenths = int(max(0.0, seconds) * 10)
    hours, rem = divmod(tenths, 36000)
    minutes, rem = divmod(rem, 600)
    secs, tenth = divmod(rem, 10)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{tenth}"
