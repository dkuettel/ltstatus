from __future__ import annotations

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

    def updates(self) -> Iterator[str]:

        last_times = psutil.cpu_times()
        yield "cpu..."

        while True:

            current_times = psutil.cpu_times()
            dt = psutil._cpu_times_deltas(last_times, current_times)
            compute = psutil._cpu_busy_time(dt) / psutil._cpu_tot_time(dt)
            last_times = current_times

            memory = psutil.virtual_memory().percent / 100

            yield f"cpu{self.compute.format(compute)}{self.memory.format(memory)}"
