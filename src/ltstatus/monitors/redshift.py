from __future__ import annotations

import re
import threading
from contextlib import contextmanager
from pathlib import Path

import inotify.adapters


def trigger_events(event: threading.Event, stop: threading.Event, log_file: Path):
    # TODO selectors can maybe also wait on file descs reading? no inotify? would be better, like a tail
    # but one danger is if the file is not appended, but replaced

    watch = inotify.adapters.Inotify(paths=[str(log_file)], block_duration_s=1)
    while not stop.is_set():
        for _, events, _, _ in watch.event_gen(timeout_s=1, yield_nones=False):  # pyright: ignore[reportGeneralTypeIssues]
            if "IN_MODIFY" in events:
                event.set()


@contextmanager
def monitor(event: threading.Event):
    log_file = Path("~/.log-redshift").expanduser()

    stop = threading.Event()
    thread = threading.Thread(target=trigger_events, args=(event, stop, log_file))
    thread.start()

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
                return ""
            if day == 0.0:
                return "night"
            return f"night@{1-day:.0%}"

        return "light"

    try:
        yield fn
    finally:
        stop.set()
        thread.join()
