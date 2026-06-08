from datetime import datetime

from alarmclock.domain.events import AlarmEvent, EventKind
from alarmclock.infrastructure.event_log import (
    InMemoryEventSink,
    JsonlEventSink,
    NullEventSink,
)


def make_event(kind=EventKind.RANG) -> AlarmEvent:
    return AlarmEvent(
        at=datetime(2024, 1, 1, 8, 30, 0), alarm_id="abc", kind=kind, label="Wake"
    )


def test_null_sink_records_nothing():
    sink = NullEventSink()
    sink.record(make_event())
    assert sink.recent(10) == []


def test_in_memory_sink_roundtrip():
    sink = InMemoryEventSink()
    sink.record(make_event(EventKind.RANG))
    sink.record(make_event(EventKind.DISMISSED))
    recent = sink.recent(1)
    assert len(recent) == 1
    assert recent[0].kind == EventKind.DISMISSED


def test_jsonl_sink_appends_and_reads(tmp_path):
    sink = JsonlEventSink(tmp_path / "history.jsonl")
    sink.record(make_event(EventKind.RANG))
    sink.record(make_event(EventKind.SNOOZED))
    recent = sink.recent(10)
    assert [e.kind for e in recent] == [EventKind.RANG, EventKind.SNOOZED]


def test_jsonl_sink_limit(tmp_path):
    sink = JsonlEventSink(tmp_path / "history.jsonl")
    for _ in range(5):
        sink.record(make_event())
    assert len(sink.recent(2)) == 2


def test_jsonl_sink_skips_corrupt_lines(tmp_path):
    path = tmp_path / "history.jsonl"
    sink = JsonlEventSink(path)
    sink.record(make_event())
    with path.open("a", encoding="utf-8") as fh:
        fh.write("not json\n")
    assert len(sink.recent(10)) == 1
