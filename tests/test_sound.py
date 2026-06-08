import pytest

from alarmclock.domain.errors import ValidationError
from alarmclock.infrastructure.sound import (
    NullSoundPlayer,
    TerminalBellPlayer,
    available_backends,
    create_sound_player,
    register_sound_player,
)


def test_named_backends_build():
    assert isinstance(create_sound_player("none"), NullSoundPlayer)
    assert isinstance(create_sound_player("bell"), TerminalBellPlayer)


def test_auto_selects_something_valid():
    player = create_sound_player("auto")
    # Whatever it picks, it must be playable without raising.
    player.play()


def test_unknown_backend_raises():
    with pytest.raises(ValidationError):
        create_sound_player("triangle")


def test_players_never_raise():
    NullSoundPlayer().play()
    TerminalBellPlayer().play()


def test_register_new_backend_is_open_for_extension():
    class CountingPlayer:
        plays = 0

        def play(self) -> None:
            CountingPlayer.plays += 1

    register_sound_player("counting", CountingPlayer)
    assert "counting" in available_backends()
    create_sound_player("counting").play()
    assert CountingPlayer.plays == 1
