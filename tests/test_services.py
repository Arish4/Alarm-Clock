import pytest

from alarmclock.application.services import AlarmService
from alarmclock.domain.alarm import Alarm
from alarmclock.domain.errors import AlarmNotFoundError


class InMemoryRepository:
    """A fake repository so the service is tested without disk."""

    def __init__(self) -> None:
        self._alarms: list[Alarm] = []

    def load(self) -> list[Alarm]:
        # Return copies-by-reference semantics like the real repo (fresh list).
        return list(self._alarms)

    def save(self, alarms: list[Alarm]) -> None:
        self._alarms = list(alarms)


@pytest.fixture
def service() -> AlarmService:
    return AlarmService(InMemoryRepository())


def test_add_and_list(service):
    service.add("08:30", label="Wake", repeat="weekdays", tags=["home"])
    alarms = service.list()
    assert len(alarms) == 1
    assert alarms[0].label == "Wake"
    assert alarms[0].repeat.describe() == "weekdays"


def test_list_filters_by_tag(service):
    service.add("08:30", label="A", tags=["work"])
    service.add("09:00", label="B", tags=["home"])
    assert [a.label for a in service.list(tag="work")] == ["A"]


def test_get_unknown_raises(service):
    with pytest.raises(AlarmNotFoundError):
        service.get("nope")


def test_edit_updates_fields(service):
    a = service.add("08:30", label="Old")
    service.edit(a.id, time="09:15", label="New", repeat="daily")
    updated = service.get(a.id)
    assert str(updated.time) == "09:15"
    assert updated.label == "New"
    assert updated.repeat.describe() == "daily"


def test_set_enabled_clears_snooze(service):
    a = service.add("08:30")
    service.set_enabled(a.id, False)
    assert service.get(a.id).enabled is False
    service.set_enabled(a.id, True)
    assert service.get(a.id).enabled is True


def test_set_all_enabled(service):
    service.add("08:30")
    service.add("09:00")
    assert service.set_all_enabled(False) == 2
    assert all(not a.enabled for a in service.list())


def test_delete_removes(service):
    a = service.add("08:30")
    service.delete(a.id)
    assert service.list() == []


def test_delete_unknown_raises(service):
    with pytest.raises(AlarmNotFoundError):
        service.delete("nope")
