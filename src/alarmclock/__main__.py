"""Enable ``python -m alarmclock``."""

from .cli.app import main

if __name__ == "__main__":
    raise SystemExit(main())
