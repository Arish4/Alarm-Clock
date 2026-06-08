"""Infrastructure layer: concrete adapters implementing the application ports."""

from .clock import FakeClock, SystemClock
from .event_log import InMemoryEventSink, JsonlEventSink, NullEventSink
from .json_repository import JsonAlarmRepository, default_config_path
from .responder import ConsoleResponder, ScriptedResponder
from .ringer import BannerNotifier, ConsoleRinger, RecordingRinger
from .sound import (
    NullSoundPlayer,
    TerminalBellPlayer,
    WinsoundPlayer,
    available_backends,
    create_sound_player,
)

__all__ = [
    "FakeClock",
    "SystemClock",
    "InMemoryEventSink",
    "JsonlEventSink",
    "NullEventSink",
    "JsonAlarmRepository",
    "default_config_path",
    "ConsoleResponder",
    "ScriptedResponder",
    "BannerNotifier",
    "ConsoleRinger",
    "RecordingRinger",
    "NullSoundPlayer",
    "TerminalBellPlayer",
    "WinsoundPlayer",
    "available_backends",
    "create_sound_player",
]
