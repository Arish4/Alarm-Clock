"""Repeat policies (Strategy pattern).

Open/Closed: the scheduler asks every policy the same two questions —
"do you occur on this date?" and "how do you describe yourself?" — so adding a
new recurrence rule means adding a subclass and registering it, never editing
the scheduler.

Liskov: every concrete policy honours the :class:`RepeatPolicy` contract and is
freely substitutable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Callable

from .errors import ValidationError

# datetime.weekday(): Monday == 0 ... Sunday == 6
WEEKDAYS: tuple[str, ...] = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
_INDEX = {code: i for i, code in enumerate(WEEKDAYS)}


class RepeatPolicy(ABC):
    """Decides, for a given calendar date, whether an alarm recurs that day."""

    is_one_off: bool = False

    @abstractmethod
    def occurs_on(self, day: date) -> bool:
        """Whether the alarm should be active on ``day``."""

    @abstractmethod
    def describe(self) -> str:
        """Human-readable label for the ``list`` table."""

    @abstractmethod
    def to_spec(self) -> str:
        """Round-trippable token persisted in storage."""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RepeatPolicy) and self.to_spec() == other.to_spec()

    def __hash__(self) -> int:
        return hash(self.to_spec())


class Once(RepeatPolicy):
    """A one-off alarm; auto-disabled after it is dismissed."""

    is_one_off = True

    def occurs_on(self, day: date) -> bool:
        return True

    def describe(self) -> str:
        return "once"

    def to_spec(self) -> str:
        return "once"


class Daily(RepeatPolicy):
    """Fires every day."""

    def occurs_on(self, day: date) -> bool:
        return True

    def describe(self) -> str:
        return "daily"

    def to_spec(self) -> str:
        return "daily"


class Weekly(RepeatPolicy):
    """Fires on a fixed set of weekdays."""

    def __init__(self, days: set[int]):
        if not days:
            raise ValidationError("a weekly repeat needs at least one weekday")
        self.days = frozenset(days)

    def occurs_on(self, day: date) -> bool:
        return day.weekday() in self.days

    def describe(self) -> str:
        if self.days == frozenset(range(7)):
            return "daily"
        if self.days == frozenset(range(5)):
            return "weekdays"
        if self.days == frozenset({5, 6}):
            return "weekends"
        return ",".join(WEEKDAYS[i] for i in sorted(self.days))

    def to_spec(self) -> str:
        return ",".join(WEEKDAYS[i] for i in sorted(self.days))


# --- Registry so named policies can be added without editing the parser ------

_NAMED: dict[str, Callable[[], RepeatPolicy]] = {}


def register_repeat(name: str, factory: Callable[[], RepeatPolicy]) -> None:
    """Register a keyword spec (e.g. ``"weekdays"``) -> policy factory."""
    _NAMED[name] = factory


register_repeat("once", Once)
register_repeat("", Once)
register_repeat("daily", Daily)
register_repeat("everyday", Daily)
register_repeat("weekdays", lambda: Weekly(set(range(5))))
register_repeat("weekends", lambda: Weekly({5, 6}))


def _weekday_index(token: str) -> int:
    code = token.strip().lower()
    if code not in _INDEX:
        raise ValidationError(
            f"invalid weekday {token!r}: expected one of {', '.join(WEEKDAYS)}"
        )
    return _INDEX[code]


def parse_repeat(spec: str | list[str] | None) -> RepeatPolicy:
    """Build a :class:`RepeatPolicy` from a CLI string or stored value.

    Accepts named keywords (``once``/``daily``/``weekdays``/``weekends``), a
    comma-separated list of weekday codes, an empty value (one-off), or a list
    of weekday codes (legacy storage format).
    """
    if spec is None:
        return Once()
    if isinstance(spec, list):
        if not spec:
            return Once()
        return Weekly({_weekday_index(code) for code in spec})

    key = spec.strip().lower()
    if key in _NAMED:
        return _NAMED[key]()
    days = {_weekday_index(tok) for tok in key.split(",") if tok.strip()}
    if not days:
        return Once()
    return Weekly(days)
