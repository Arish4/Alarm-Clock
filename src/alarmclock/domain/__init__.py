"""Domain layer: pure business rules with no I/O or framework dependencies."""

from .alarm import Alarm, new_id
from .errors import AlarmClockError, AlarmNotFoundError, ValidationError
from .events import AlarmEvent, EventKind
from .repeat import Daily, Once, RepeatPolicy, Weekly, parse_repeat
from .time_of_day import TimeOfDay

__all__ = [
    "Alarm",
    "new_id",
    "AlarmClockError",
    "AlarmNotFoundError",
    "ValidationError",
    "AlarmEvent",
    "EventKind",
    "RepeatPolicy",
    "Once",
    "Daily",
    "Weekly",
    "parse_repeat",
    "TimeOfDay",
]
