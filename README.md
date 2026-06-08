# alarmclock

A small, testable, **stdlib-only** command-line alarm clock.

Set alarms (one-off or repeating), list them, enable/disable/delete them, and
run a watch loop that rings when an alarm is due — with snooze and dismiss.

```
$ alarmclock add 08:30 --label "Wake up" --repeat mon,tue,wed,thu,fri
added alarm 1a2b3c4d  08:30  Wake up  [mon,tue,wed,thu,fri]

$ alarmclock list
ID        TIME   LABEL    REPEAT               STATUS
--------  -----  -------  -------------------  ------
1a2b3c4d  08:30  Wake up  mon,tue,wed,thu,fri  armed

$ alarmclock run --snooze-minutes 9
alarmclock running (now 08:29). press Ctrl-C to stop.
============================================
  ⏰  ALARM  08:30  —  Wake up
============================================
[s]nooze / [d]ismiss?
```

## Install

Requires Python 3.10+. From the project root:

```bash
python -m pip install -e ".[dev]"   # editable install + pytest for tests
```

This puts an `alarmclock` command on your PATH. You can also run it without
installing:

```bash
python -m alarmclock list
```

## Usage

| Command | What it does |
| --- | --- |
| `alarmclock add HH:MM [--label L] [--repeat mon,fri]` | Add an alarm. Omit `--repeat` for a one-off. |
| `alarmclock list` | Show all alarms as a table (id, time, label, repeat, status). |
| `alarmclock enable <id>` / `disable <id>` | Arm or disarm an alarm. |
| `alarmclock delete <id>` | Remove an alarm. |
| `alarmclock run [--snooze-minutes N] [--no-sound]` | Blocking watch loop; rings when due. |

When an alarm rings during `run`, you get a banner (plus a beep) and a
`[s]nooze / [d]ismiss` prompt. Snooze re-arms it for N minutes; dismissing a
one-off alarm auto-disables it.

Alarms are stored as JSON at `~/.alarmclock/alarms.json`. Override the path
with `--config PATH` or the `ALARMCLOCK_CONFIG` environment variable (handy for
testing or keeping multiple alarm sets).

## Design rationale

The code is organised in layers so each piece is testable in isolation:

```
cli.py          argument parsing, command dispatch, output formatting (thin)
runner.py       the `run` loop — the only place with real sleeping
core/
  models.py     Alarm dataclass + parsing/validation (pure data, no I/O)
  scheduler.py  "given now, which alarms are due?" (pure logic, no clock/sleep)
  store.py      load/save list[Alarm] <-> JSON (the only file I/O)
  ringer.py     Ringer interface + console/recording impls (the only output)
  clock.py      time-source abstraction (real vs. fake) so tests control "now"
```

The payoff:

- **`scheduler` is pure.** Feed it a fake `now` and assert what's due — no
  sleeping in tests. The subtle once-per-minute fired guard lives here.
- **`store` is the only thing touching disk.** Saves are **atomic** (temp file
  + `os.replace`) so a crash mid-write can't corrupt the store, and a corrupt
  or missing file degrades to an empty list with a warning instead of crashing.
- **`ringer` is an injectable interface.** Tests use a `RecordingRinger` to
  assert exactly one ring; the real `ConsoleRinger` degrades silently to the
  visual banner if sound fails.
- **`clock` is injectable.** A `FakeClock` lets the run loop be exercised
  deterministically — `sleep` advances fake time instead of blocking.

### Firing logic

The loop ticks once per second. An alarm is *due* when the current `HH:MM`
matches and (for repeats) today's weekday is in its set, and it hasn't already
fired this minute — tracked by a per-alarm "last fired minute" guard so it
rings once, not 60×. Snoozed alarms fire when `now >= snoozed_until`, and the
normal schedule is suppressed until the snooze elapses.

### Error handling

- Invalid time/weekday → clear validation error, non-zero exit, no partial write.
- Corrupt or missing JSON → treated as an empty list with a warning.
- Atomic saves prevent mid-write corruption.
- Sound failure silently degrades to the visual banner.

## Testing

The suite is pure and fast — **no real sleeping, no real sound, no global
state**. Tests use a temp config dir, a `FakeClock`, and a `RecordingRinger`.

```bash
python -m pytest        # or just: pytest
```

Coverage includes:

- **Unit** — scheduler due-logic across one-off / repeat / disabled / snoozed
  and the once-per-minute guard; store round-trip and corrupt-file recovery;
  time/weekday parsing.
- **Integration** — `add → list → delete` against a temp config; a full `run`
  tick asserting exactly one ring.

## License

[MIT](LICENSE).
