"""Use-case layer: alarm management operations over a repository.

Single Responsibility: each method is one use case. Dependency Inversion: the
service depends on the :class:`AlarmRepository` port, not a concrete store, so
it can be unit-tested against an in-memory fake.
"""

from __future__ import annotations

from ..domain.alarm import Alarm
from ..domain.errors import AlarmNotFoundError
from ..domain.repeat import RepeatPolicy, parse_repeat
from ..domain.time_of_day import TimeOfDay
from .interfaces import AlarmRepository


class AlarmService:
    """Create, read, update and delete alarms."""

    def __init__(self, repository: AlarmRepository):
        self._repo = repository

    def add(
        self,
        time: str,
        label: str = "",
        repeat: str = "",
        tags: list[str] | None = None,
    ) -> Alarm:
        alarm = Alarm(
            time=TimeOfDay.parse(time),
            label=label,
            repeat=parse_repeat(repeat),
            tags=list(tags or []),
        )
        alarms = self._repo.load()
        alarms.append(alarm)
        self._repo.save(alarms)
        return alarm

    def list(self, tag: str | None = None) -> list[Alarm]:
        alarms = self._repo.load()
        if tag:
            alarms = [a for a in alarms if a.has_tag(tag)]
        return alarms

    def get(self, alarm_id: str) -> Alarm:
        for alarm in self._repo.load():
            if alarm.id == alarm_id:
                return alarm
        raise AlarmNotFoundError(alarm_id)

    def edit(
        self,
        alarm_id: str,
        *,
        time: str | None = None,
        label: str | None = None,
        repeat: str | None = None,
        tags: list[str] | None = None,
    ) -> Alarm:
        alarms = self._repo.load()
        target = self._require(alarms, alarm_id)
        if time is not None:
            target.time = TimeOfDay.parse(time)
        if label is not None:
            target.label = label
        if repeat is not None:
            target.repeat = parse_repeat(repeat)
        if tags is not None:
            target.tags = list(tags)
        self._repo.save(alarms)
        return target

    def set_enabled(self, alarm_id: str, enabled: bool) -> Alarm:
        alarms = self._repo.load()
        target = self._require(alarms, alarm_id)
        target.enabled = enabled
        if enabled:
            target.snoozed_until = None
            target.snooze_count = 0
        self._repo.save(alarms)
        return target

    def set_all_enabled(self, enabled: bool) -> int:
        alarms = self._repo.load()
        for alarm in alarms:
            alarm.enabled = enabled
            if enabled:
                alarm.snoozed_until = None
                alarm.snooze_count = 0
        self._repo.save(alarms)
        return len(alarms)

    def delete(self, alarm_id: str) -> None:
        alarms = self._repo.load()
        self._require(alarms, alarm_id)
        self._repo.save([a for a in alarms if a.id != alarm_id])

    @staticmethod
    def _require(alarms: list[Alarm], alarm_id: str) -> Alarm:
        for alarm in alarms:
            if alarm.id == alarm_id:
                return alarm
        raise AlarmNotFoundError(alarm_id)
