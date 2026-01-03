from __future__ import annotations

import os
import re
import select
import subprocess
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from copy import copy
from dataclasses import dataclass
from pathlib import Path

# NOTE alternatives states from log
# re_temperature = re.compile(r".*Color temperature: (?P<temperature>\d+)K")
# re_brightness = re.compile(r".*Brightness: (?P<brightness>[0-9.]+)")
re_status = re.compile(r".*Status: (?P<status>Enabled|Disabled)")
re_period = re.compile(
    r".*Period: (?P<period>Daytime|Night|Transition \((?P<percentage>[0-9.]+)% day\))"
)
re_exited = re.compile(r".*exited .*")


def tail(path: Path, stop: int) -> Iterator[list[str | None]]:
    """
    data comes in batches
    str are lines without new lines ending, None is when the file disappeared
    """

    with subprocess.Popen(
        [
            "inotifywait",
            "--quiet",
            "--monitor",
            "--event",
            "create,modify,move,delete",
            str(path.parent),
            "--include",
            str(path.name),
        ],
        text=True,
        stdout=subprocess.PIPE,
    ) as p:
        assert p.stdout is not None
        f = None
        try:
            while True:
                if f is None:
                    try:
                        f = path.open("rt")
                    except:
                        pass

                if f is not None:
                    batch: list[str | None] = [l.rstrip("\n") for l in f]
                    if len(batch) > 0:
                        yield batch

                    else:
                        current = os.stat(f.fileno())
                        if current.st_size < f.tell():
                            # most likely new data since file has been truncated
                            yield [None]
                            f.close()
                            f = None
                            continue

                        try:
                            fresh = os.stat(path)
                            if (current.st_dev, current.st_ino) != (
                                fresh.st_dev,
                                fresh.st_ino,
                            ):
                                # not the same file anymore
                                yield [None]
                                f.close()
                                f = None
                                continue

                        except:
                            # file is not there anymore
                            yield [None]
                            f.close()
                            f = None
                            continue

                r, _, _ = select.select([p.stdout, stop], [], [], None)
                while len(r) > 0:
                    if stop in r:
                        return
                    p.stdout.readline()
                    r, _, _ = select.select([p.stdout], [], [], 0.1)

        finally:
            if f is not None:
                f.close()
                f = None


@dataclass
class State:
    running: bool = False
    enabled: None | bool = None
    day: None | float = None


def keep_reading_log(
    event: threading.Event,
    path: Path,
    lock: threading.Lock,
    state: State,
    stop: int,
):
    for batch in tail(path, stop):
        with lock:
            old = copy(state)

            for entry in batch:
                if entry is None:
                    state.running = False
                    continue

                match re_exited.fullmatch(entry):
                    case re.Match() as match:
                        state.running = False
                        continue

                state.running = True

                match re_status.fullmatch(entry):
                    case re.Match() as match:
                        state.enabled = match["status"] == "Enabled"
                        continue

                match re_period.fullmatch(entry):
                    case re.Match() as match:
                        if match["period"] == "Daytime":
                            day = 1.0
                        elif match["period"] == "Night":
                            day = 0.0
                        else:
                            day = float(match["percentage"]) / 100
                        state.day = day
                        continue

            if old != state:
                event.set()


@contextmanager
def monitor(event: threading.Event):
    log_file = Path("~/.log-redshift").expanduser()

    lock = threading.Lock()
    state = State()

    stop_read, stop_write = os.pipe()

    thread = threading.Thread(
        target=keep_reading_log,
        args=(event, log_file, lock, state, stop_read),
    )
    thread.start()

    def fn() -> str:
        with lock:
            # print(state)
            if not state.running:
                return ""

            if (state.enabled is None) or (state.day is None):
                return "redshift error"

            if state.enabled:
                if state.day == 1.0:
                    return ""
                if state.day == 0.0:
                    return "night"
                return f"night@{1 - state.day:.0%}"

            return "light"

    try:
        yield fn
    finally:
        os.write(stop_write, b"stop")
        thread.join()
