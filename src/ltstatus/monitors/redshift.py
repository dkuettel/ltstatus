from __future__ import annotations

import re
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def monitor():
    log_file = Path("~/.log-redshift").expanduser()

    re_status = re.compile(r".*Status: (?P<status>Enabled|Disabled)")
    re_period = re.compile(
        r".*Period: (?P<period>Daytime|Night|Transition \((?P<percentage>[0-9.]+)% day\))"
    )
    # NOTE alternatives states from log
    # re_temperature = re.compile(r".*Color temperature: (?P<temperature>\d+)K")
    # re_brightness = re.compile(r".*Brightness: (?P<brightness>[0-9.]+)")

    # TODO could also do it less often, doesnt change so fast usually, unless manual switches
    def fn() -> str:
        enabled: None | bool = None
        day: None | float = None

        with log_file.open("rt") as file:
            for event in file:
                event = event.strip()
                match re_status.fullmatch(event):
                    case re.Match() as match:
                        enabled = match["status"] == "Enabled"
                        continue
                match re_period.fullmatch(event):
                    case re.Match() as match:
                        if match["period"] == "Daytime":
                            day = 1.0
                        elif match["period"] == "Night":
                            day = 0.0
                        else:
                            day = float(match["percentage"]) / 100
                        continue

        if (enabled is None) or (day is None):
            return "redshift error"

        if enabled:
            if day == 1.0:
                return "day"
            if day == 0.0:
                return "night"
            if day >= 0.5:
                return f"day@{day:.0%}"
            if day < 0.5:
                return f"night@{1-day:.0%}"
            assert False, day

        return "light"

    yield fn
