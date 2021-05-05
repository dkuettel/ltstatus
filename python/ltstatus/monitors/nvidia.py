from dataclasses import dataclass

from pynvml import (
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetMemoryInfo,
    nvmlDeviceGetUtilizationRates,
    nvmlInit,
    nvmlShutdown,
)

from ltstatus import State, ThreadedMonitor
from ltstatus.indicators import RatioIndicator, bin_themes
from ltstatus.tools import ffield


@dataclass
class Monitor(ThreadedMonitor):
    name: str = "nvidia"
    interval: float = 1.0
    total_compute: RatioIndicator = ffield(lambda: RatioIndicator(bin_themes["pie"]))
    memory: RatioIndicator = ffield(lambda: RatioIndicator(bin_themes["pie"]))

    def run(self):
        # TODO how to not have unavailable status? test before and not even add it?
        # TODO try finally to shut down nvml?

        # https://docs.nvidia.com/deploy/nvml-api/index.html
        nvmlInit()
        handle = nvmlDeviceGetHandleByIndex(0)

        while not self.exit.is_set():

            # compute has .gpu, .memory; in percent
            # https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g540824faa6cef45500e0d1dc2f50b321
            compute = nvmlDeviceGetUtilizationRates(handle)
            ind_total = self.total_compute.format(compute.gpu / 100)

            # memory has .free, .total, .used; in bytes
            # https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g2dfeb1db82aa1de91aa6edf941c85ca8
            memory = nvmlDeviceGetMemoryInfo(handle)
            ind_memory = self.memory.format(memory.used / memory.total)

            self.queue.put(
                State.from_one(self.name, f"gpu{ind_total}{ind_memory}")
            )
            self.exit.wait(self.interval)

        nvmlShutdown()
