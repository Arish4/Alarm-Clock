from alarmclock.domain.alarm import Alarm
from alarmclock.domain.repeat import parse_repeat
from alarmclock.domain.time_of_day import TimeOfDay
from alarmclock.infrastructure.json_repository import JsonAlarmRepository


def test_save_and_load_roundtrip(tmp_path):
    repo = JsonAlarmRepository(tmp_path / "alarms.json")
    alarms = [
        Alarm(time=TimeOfDay(7, 0), label="Wake", repeat=parse_repeat("mon,fri")),
        Alarm(time=TimeOfDay(14, 0), label="Meeting"),
    ]
    repo.save(alarms)
    loaded = repo.load()
    assert [a.to_dict() for a in loaded] == [a.to_dict() for a in alarms]


def test_missing_file_is_empty(tmp_path):
    repo = JsonAlarmRepository(tmp_path / "nope.json")
    assert repo.load() == []


def test_corrupt_file_recovers(tmp_path, capsys):
    path = tmp_path / "alarms.json"
    path.write_text("{ not valid json", encoding="utf-8")
    assert JsonAlarmRepository(path).load() == []
    assert "warning" in capsys.readouterr().err.lower()


def test_non_array_recovers(tmp_path, capsys):
    path = tmp_path / "alarms.json"
    path.write_text('{"not": "a list"}', encoding="utf-8")
    assert JsonAlarmRepository(path).load() == []
    assert "warning" in capsys.readouterr().err.lower()


def test_malformed_entry_skipped(tmp_path, capsys):
    path = tmp_path / "alarms.json"
    path.write_text(
        '[{"time": "08:00", "label": "ok"}, {"label": "broken"}]',
        encoding="utf-8",
    )
    loaded = JsonAlarmRepository(path).load()
    assert len(loaded) == 1 and loaded[0].label == "ok"
    assert "warning" in capsys.readouterr().err.lower()


def test_save_is_atomic_no_temp_leftover(tmp_path):
    path = tmp_path / "alarms.json"
    repo = JsonAlarmRepository(path)
    repo.save([Alarm(time=TimeOfDay(7, 0))])
    assert list(tmp_path.glob(".tmp-*")) == []
