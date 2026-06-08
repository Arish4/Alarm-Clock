from alarmclock.core.models import Alarm
from alarmclock.core.store import Store


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "alarms.json"
    store = Store(path)
    alarms = [
        Alarm(time="07:00", label="Wake", repeat=["mon", "fri"]),
        Alarm(time="14:00", label="Meeting"),
    ]
    store.save(alarms)
    loaded = store.load()
    assert [a.to_dict() for a in loaded] == [a.to_dict() for a in alarms]


def test_missing_file_is_empty_list(tmp_path):
    store = Store(tmp_path / "does-not-exist.json")
    assert store.load() == []


def test_corrupt_file_recovers_to_empty(tmp_path, capsys):
    path = tmp_path / "alarms.json"
    path.write_text("{ this is not valid json", encoding="utf-8")
    store = Store(path)
    assert store.load() == []
    assert "warning" in capsys.readouterr().err.lower()


def test_non_array_json_recovers_to_empty(tmp_path, capsys):
    path = tmp_path / "alarms.json"
    path.write_text('{"not": "a list"}', encoding="utf-8")
    store = Store(path)
    assert store.load() == []
    assert "warning" in capsys.readouterr().err.lower()


def test_malformed_entry_is_skipped(tmp_path, capsys):
    path = tmp_path / "alarms.json"
    # One good, one bad (missing required "time").
    path.write_text(
        '[{"time": "08:00", "label": "ok"}, {"label": "broken"}]',
        encoding="utf-8",
    )
    store = Store(path)
    loaded = store.load()
    assert len(loaded) == 1
    assert loaded[0].label == "ok"
    assert "warning" in capsys.readouterr().err.lower()


def test_save_is_atomic_no_temp_left_behind(tmp_path):
    path = tmp_path / "alarms.json"
    store = Store(path)
    store.save([Alarm(time="07:00")])
    leftovers = list(tmp_path.glob(".alarms-*"))
    assert leftovers == []
