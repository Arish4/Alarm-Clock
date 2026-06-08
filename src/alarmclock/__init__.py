"""alarmclock — a small, SOLID, stdlib-only CLI alarm clock.

Layers (each depends only on the ones beneath it):

    cli            -> argument parsing, command dispatch, composition root
    application    -> use cases, scheduler, run loop, ports (abstractions)
    infrastructure -> concrete adapters: storage, clock, sound, ringer, events
    domain         -> pure entities and business rules (no I/O)
"""

__version__ = "0.3.0"
