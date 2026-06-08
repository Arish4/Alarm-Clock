# alarmclock

A small, **SOLID**, **stdlib-only** command-line alarm clock.

Run it with no arguments (or `alarmclock run`) to open a **full-screen
interactive terminal menu** — a live **Clock**, a **Stopwatch**, a countdown
**Timer**, and the **Alarm** manager. Or drive everything from one-shot
subcommands: set alarms (one-off, daily, weekdays, weekends or specific days),
tag and edit them, see when each next fires, and watch a loop that rings — with
snooze limits and a recorded event history.

```
$ alarmclock            # (or: alarmclock run)
  alarmclock
  ==========

    1. Clock
    2. Stopwatch
    3. Timer
    4. Alarm

    q. quit

  choose:
```

Pick a number and that feature takes over the screen (live-updating, `q` to go
back). The Timer beeps when it reaches zero; the Stopwatch supports
pause/lap/reset.

```
$ alarmclock add 8:30am --label "Wake up" --repeat weekdays --tag morning
added alarm 1a2b3c4d  08:30  Wake up  [weekdays]

$ alarmclock list
ID        TIME   LABEL    REPEAT    TAGS     STATUS
--------  -----  -------  --------  -------  ------
1a2b3c4d  08:30  Wake up  weekdays  morning  armed

$ alarmclock next
ID        LABEL    NEXT FIRE
--------  -------  --------------------
1a2b3c4d  Wake up  Mon 2026-06-15 08:30

$ alarmclock run --snooze-minutes 9 --max-snoozes 3
alarmclock running (now 08:29). press Ctrl-C to stop.
============================================
  ⏰  ALARM  08:30  —  Wake up
============================================
[s]nooze / [d]ismiss?
```

## Features

- **Interactive menu** — `alarmclock` (or `alarmclock run`) opens a terminal
  menu with four live screens:
  - **Clock** — current time and date, updating every tick.
  - **Stopwatch** — count up with `[space]` start/pause, `[l]` lap, `[r]` reset.
  - **Timer** — enter a duration (`30s`, `5m`, `1h30m`, `10:00`); counts down
    and beeps at zero, with `[space]` pause/resume.
  - **Alarm** — view alarms with their next fire time, add/delete, or start the
    watch loop.
- **Flexible times** — `HH:MM` (24h) or `8:30am` / `2:00pm` (12h).
- **Repeat policies** — `once`, `daily`, `weekdays`, `weekends`, or specific
  days like `mon,wed,fri`.
- **Tags** — attach tags and filter with `list --tag work`.
- **`edit`** — change an alarm's time, label, repeat or tags in place.
- **`next`** — show when each alarm will next fire.
- **Bulk toggles** — `enable-all` / `disable-all`.
- **Snooze control** — `--snooze-minutes` and `--max-snoozes` (auto-dismiss
  after N snoozes).
- **Event history** — every ring / snooze / dismiss is logged; view with
  `history`.
- **Pluggable sound** — `--sound auto|none|bell|beep`, degrading silently to
  the visual banner if audio fails.
- **JSON output** — `list --json` / `next --json` for scripting.

## Install

Requires Python 3.10+. From the project root:

```bash
python -m pip install -e ".[dev]"   # editable install + pytest
```

This puts an `alarmclock` command on your PATH. You can also run without
installing:

```bash
python -m alarmclock list
```

## Usage

| Command | What it does |
| --- | --- |
| `run` (or no command) | Open the interactive menu (Clock / Stopwatch / Timer / Alarm). |
| `add TIME [--label L] [--repeat R] [--tag t1,t2]` | Add an alarm. `R` = `once`/`daily`/`weekdays`/`weekends`/`mon,fri`. |
| `list [--tag T] [--json]` | List alarms (optionally filtered / as JSON). |
| `next [--json]` | Show each alarm's next fire time. |
| `edit ID [--time] [--label] [--repeat] [--tag]` | Modify an existing alarm. |
| `enable ID` / `disable ID` | Arm or disarm one alarm. |
| `enable-all` / `disable-all` | Toggle every alarm. |
| `delete ID` | Remove an alarm. |
| `watch [--snooze-minutes N] [--max-snoozes M] [--sound B] [--no-sound]` | Blocking alarm watch loop (no menu). |
| `history [--limit N]` | Show recent ring/snooze/dismiss events. |

Alarms live at `~/.alarmclock/alarms.json` and history at
`~/.alarmclock/history.jsonl`. Override paths with `--config` / `--history`, or
the `ALARMCLOCK_CONFIG` / `ALARMCLOCK_HISTORY` environment variables.

## Architecture & SOLID

The code is organised into four layers; each depends only on the ones beneath
it, and dependencies always point **inward** toward the pure domain.

```
cli/            argument parsing, command dispatch, composition root
  app.py          builds the parser from a command registry and dispatches
  commands.py     one class per command (Command pattern)
  context.py      composition root — wires concrete infra to the app layer
  presenter.py    output formatting (tables / JSON)
application/     use cases + orchestration, depends only on abstractions
  interfaces.py   ports: Clock, AlarmRepository, Ringer, SoundPlayer,
                  Notifier, EventSink, EventReader, Responder, Console
  scheduler.py    pure due-logic + next-occurrence (no clock/sleep/IO)
  services.py     AlarmService use cases (add/list/edit/delete/toggle)
  runner.py       the alarm watch loop (sleeps via the Clock port)
  features.py     interactive screens: Clock / Stopwatch / Timer / Alarm
  menu.py         InteractiveMenu — lists and dispatches to features
infrastructure/  concrete adapters implementing the ports
  json_repository.py  atomic JSON storage + corrupt-file recovery
  clock.py            SystemClock / FakeClock
  console.py          TerminalConsole (live keys) / ScriptedConsole (tests)
  sound.py            SoundPlayer strategies + factory
  ringer.py           ConsoleRinger (Notifier + SoundPlayer) / RecordingRinger
  event_log.py        Jsonl / InMemory / Null event sinks
  responder.py        Console / Scripted responders
domain/          pure entities and rules, zero I/O
  alarm.py        Alarm entity (snooze/dismiss behaviour lives here)
  repeat.py       RepeatPolicy strategy hierarchy + registry
  time_of_day.py  TimeOfDay value object (parsing/validation)
  duration.py     duration parsing + HH:MM:SS / tenths formatting
  stopwatch.py    pure Stopwatch model (elapsed is a function of 'now')
  timer.py        pure Countdown model
  events.py       AlarmEvent / EventKind
  errors.py       domain exceptions
```

How each SOLID principle shows up:

- **Single Responsibility** — every class has one reason to change:
  `TimeOfDay` parses time, `Scheduler` answers timing questions, `AlarmService`
  runs use cases, `JsonAlarmRepository` does storage, each `Command` does one
  command.
- **Open/Closed** — extension without modification. New recurrence rule? Add a
  `RepeatPolicy` subclass and `register_repeat`. New audio backend? Add a
  `SoundPlayer` and `register_sound_player`. New command? Add a `Command` and
  register it — the dispatcher never changes.
- **Liskov Substitution** — every `RepeatPolicy`, `SoundPlayer` and `Command`
  honours its base contract and is freely interchangeable; tests swap real
  implementations for fakes with no special-casing.
- **Interface Segregation** — ports are tiny and focused. A `SoundPlayer` only
  `play()`s; a `Notifier` only `notify()`s; write (`EventSink`) and read
  (`EventReader`) are separate. Nothing depends on methods it doesn't use.
- **Dependency Inversion** — the application layer depends only on abstractions
  in `interfaces.py`. Concrete infrastructure is wired in exactly one place,
  the composition root (`cli/context.py`), and injected everywhere else. The
  interactive features take a `Console` port, so the whole TUI is tested with a
  `ScriptedConsole` and `FakeClock` — no real terminal or sleeping required.

The interactive menu reuses the same principles: each screen is a `Feature`
subclass (Clock, Stopwatch, Timer, Alarm), the `InteractiveMenu` lists and
dispatches to them without knowing what they are, and a new screen is one new
class — the menu never changes.

### Firing logic

The loop ticks once per second. An alarm is *due* when the current `HH:MM`
matches and (for repeats) today's weekday is in its set, and it hasn't already
fired this minute — a per-alarm "last fired minute" guard so it rings once, not
60×. Snoozed alarms fire when `now >= snoozed_until`; the normal schedule is
suppressed until the snooze elapses. `--max-snoozes` converts a snooze request
into an auto-dismiss once the limit is reached.

### Error handling

- Invalid time/weekday → clear validation error, non-zero exit, no partial write.
- Unknown alarm id → friendly error, exit code 1.
- Corrupt or missing JSON → treated as empty with a warning, never a crash.
- Atomic saves (temp file + `os.replace`) prevent mid-write corruption.
- Sound failure, or a console that can't render the banner's Unicode, degrades
  gracefully (silent audio / ASCII banner).

## Testing

The suite is pure and fast — **no real sleeping, no real sound, no shared
state**. Because every boundary is an injected port, tests use a `FakeClock`,
`RecordingRinger`, `ScriptedResponder`, `InMemoryEventSink` and an in-memory
repository.

```bash
python -m pytest        # 126 tests
```

Coverage spans every layer: time parsing (12h/24h), duration parsing and
formatting, repeat strategies and the registry, the `Alarm`/`Stopwatch`/
`Countdown` models, the scheduler's due-logic and next-occurrence, the
`AlarmService` use cases, the alarm watch loop (single ring per minute, snooze
re-arm, max-snooze auto-dismiss), the interactive features and menu (driven by a
`ScriptedConsole`), atomic storage with corrupt-file recovery, the event log,
the sound factory, the banner's encoding fallback, and the CLI end-to-end
through an injected context.

## License

[MIT](LICENSE).
