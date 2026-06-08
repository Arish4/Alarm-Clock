from alarmclock.cli import main


def _cfg(tmp_path):
    return str(tmp_path / "alarms.json")


def test_add_list_delete_flow(tmp_path, capsys):
    cfg = _cfg(tmp_path)

    assert main(["--config", cfg, "add", "08:30", "--label", "Wake",
                 "--repeat", "mon,fri"]) == 0
    out = capsys.readouterr().out
    assert "added alarm" in out

    assert main(["--config", cfg, "list"]) == 0
    listing = capsys.readouterr().out
    assert "Wake" in listing
    assert "mon,fri" in listing

    # Extract the generated id from the listing's data row.
    line = [l for l in listing.splitlines() if "Wake" in l][0]
    alarm_id = line.split()[0]

    assert main(["--config", cfg, "disable", alarm_id]) == 0
    assert "disabled" in capsys.readouterr().out

    assert main(["--config", cfg, "delete", alarm_id]) == 0
    assert "deleted" in capsys.readouterr().out

    assert main(["--config", cfg, "list"]) == 0
    assert "no alarms" in capsys.readouterr().out


def test_add_invalid_time_returns_error(tmp_path, capsys):
    cfg = _cfg(tmp_path)
    assert main(["--config", cfg, "add", "25:00"]) == 2
    assert "error" in capsys.readouterr().err.lower()


def test_enable_unknown_id_errors(tmp_path, capsys):
    cfg = _cfg(tmp_path)
    assert main(["--config", cfg, "enable", "nope"]) == 1
    assert "no alarm" in capsys.readouterr().err.lower()
