from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

import psutil

from ltstatus import PollingMonitor
from ltstatus.indicators import RatioIndicator, bin_themes


@dataclass
class Monitor(PollingMonitor):
    name: str = "cpu"
    compute: RatioIndicator = RatioIndicator(bin_themes["LMH"])
    memory: RatioIndicator = RatioIndicator(bin_themes["LMH"])
    prefix: str = "cpu"
    waiting: str = ".."

    def with_icons(self) -> Monitor:
        self.compute = RatioIndicator(bin_themes["thermometer"])
        self.memory = RatioIndicator(bin_themes["battery!"])
        self.prefix = ""
        self.waiting = ""
        return self

    def updates(self) -> Iterator[str]:
        last_times = psutil.cpu_times()
        yield f"{self.prefix}{self.waiting}"

        while True:
            current_times = psutil.cpu_times()
            dt = psutil._cpu_times_deltas(last_times, current_times)
            compute = psutil._cpu_busy_time(dt) / psutil._cpu_tot_time(dt)
            last_times = current_times

            memory = psutil.virtual_memory().percent / 100

            yield f"{self.prefix}{self.compute.format(compute)}{self.memory.format(memory)}"


# TODO put this for everyone to use
def ratio(v: float) -> str:
    """return a compact ratio with one digit"""
    i = round(10 * v)
    if 0 <= i <= 9:
        return f".{i}"
    if i == 10:
        return "1."
    return f"{v:.1f}"


@contextmanager
def monitor():
    times: object | None = None

    def fn() -> str:
        nonlocal times
        new_times: object = psutil.cpu_times()
        if times is None:
            times = new_times
            return "--m -c"

        deltas = psutil._cpu_times_deltas(times, new_times)  # pyright: ignore[reportAttributeAccessIssue]
        cores: float = (
            psutil.cpu_count()
            * psutil._cpu_busy_time(deltas)  # pyright: ignore[reportAttributeAccessIssue]
            / psutil._cpu_tot_time(deltas)  # pyright: ignore[reportAttributeAccessIssue]
        )
        # TODO trying active for now, available might be better?
        memory: float = psutil.virtual_memory().active / psutil.virtual_memory().total

        times = new_times

        return f"{ratio(memory)}m {cores:.0f}c"

    yield fn
