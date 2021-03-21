from dataclasses import dataclass
from typing import Optional

import psutil

from ltstatus import CallbackMonitor, State, ffield
from ltstatus.indicators import HistogramIndicator, RatioIndicator, bin_themes


@dataclass
class Monitor(CallbackMonitor):
    name: str = "cpu"
    cores: Optional[HistogramIndicator] = None
    total_compute: RatioIndicator = ffield(lambda: RatioIndicator(bin_themes["pie"]))
    single_compute: RatioIndicator = ffield(lambda: RatioIndicator(bin_themes["arrow"]))
    memory: RatioIndicator = ffield(lambda: RatioIndicator(bin_themes["pie"]))

    def get_updates(self):

        # TODO psutil measures since last call
        # since last call in this thread or this process?
        # what if another monitor uses it?
        cpus = [i / 100 for i in psutil.cpu_percent(percpu=True)]

        # TODO would like to make cpu core hist a separate monitor
        # but because psutil sampling issue above we cannot yet
        if self.cores is None:
            ind_cores = ""
        else:
            ind_cores = self.cores.format(cpus)

        ind_total = self.total_compute.format(sum(cpus) / len(cpus))
        ind_single = self.single_compute.format(max(cpus))

        ind_memory = self.memory.format(
            psutil.virtual_memory().percent / 100,
        )

        return State.from_one(
            self.name, f"{ind_cores}{ind_total}{ind_single}cpu{ind_memory}"
        )
