from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional

import psutil

from ltstatus import PollingMonitor


@dataclass
class Monitor(PollingMonitor):
    name: str = "cores"
    prefix: str = "cores"
    waiting: str = "."
    counters: Optional[list[str]] = None

    def with_icons(self) -> Monitor:
        self.prefix = "󰍛"
        self.waiting = ""
        # NOTE there is also 󰎡 and 
        self.counters = list("󰎤󰎧󰎪󰎭󰎱󰎳󰎶󰎹󰎼󰎿")
        return self

    def updates(self) -> Iterator[str]:

        core_count = psutil.cpu_count()

        last_times = psutil.cpu_times()
        yield f"{self.prefix}{self.waiting}"

        while True:

            current_times = psutil.cpu_times()
            dt = psutil._cpu_times_deltas(last_times, current_times)
            compute = psutil._cpu_busy_time(dt) / psutil._cpu_tot_time(dt)
            last_times = current_times

            cores = round(compute * core_count)

            if self.counters is None:
                cores_str = str(cores)
            else:
                cores_str = self.counters[min(cores, len(self.counters) - 1)]

            yield f"{self.prefix}{cores_str}"
