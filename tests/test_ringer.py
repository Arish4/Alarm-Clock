import io

from alarmclock.domain.alarm import Alarm
from alarmclock.domain.time_of_day import TimeOfDay
from alarmclock.infrastructure.ringer import BannerNotifier, ConsoleRinger


class CountingSound:
    def __init__(self) -> None:
        self.plays = 0

    def play(self) -> None:
        self.plays += 1


def make() -> Alarm:
    return Alarm(time=TimeOfDay(8, 30), label="Wake")


def test_console_ringer_notifies_and_plays():
    sound = CountingSound()
    stream = io.StringIO()
    ringer = ConsoleRinger(notifier=BannerNotifier(stream), sound=sound)
    ringer.ring(make())
    assert "ALARM" in stream.getvalue()
    assert sound.plays == 1


class _Cp1252Stream:
    """A stream that rejects non-cp1252 characters, like a Windows console."""

    def __init__(self) -> None:
        self.text = ""

    def write(self, s: str) -> int:
        s.encode("cp1252")  # raises UnicodeEncodeError on the emoji/dash
        self.text += s
        return len(s)

    def flush(self) -> None:  # pragma: no cover - nothing to flush
        pass


def test_banner_degrades_to_ascii_on_encoding_error():
    stream = _Cp1252Stream()
    BannerNotifier(stream).notify(make())
    assert "ALARM" in stream.text
    assert "Wake" in stream.text
    # The fancy emoji must not have survived into the cp1252 stream.
    assert "⏰" not in stream.text
