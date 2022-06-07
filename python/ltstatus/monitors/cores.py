from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import psutil

from ltstatus import PollingMonitor


@dataclass
class Monitor(PollingMonitor):
    name: str = "cores"

    def updates(self) -> Iterator[str]:

        core_count = psutil.cpu_count()

        last_times = psutil.cpu_times()
        yield "cores..."

        while True:

            current_times = psutil.cpu_times()
            dt = psutil._cpu_times_deltas(last_times, current_times)
            compute = psutil._cpu_busy_time(dt) / psutil._cpu_tot_time(dt)
            last_times = current_times

            cores = round(compute * core_count)

            yield f"cores{cores}"
