from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from pynvml import (
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetMemoryInfo,
    nvmlDeviceGetUtilizationRates,
    nvmlInit,
    nvmlShutdown,
)

from ltstatus import PollingMonitor
from ltstatus.indicators import RatioIndicator, bin_themes


@dataclass
class Monitor(PollingMonitor):
    name: str = "nvidia"
    total_compute: RatioIndicator = RatioIndicator(bin_themes["LMH"])
    memory: RatioIndicator = RatioIndicator(bin_themes["LMH"])

    def updates(self) -> Iterator[str]:
        while True:
            yield from self.connected_updates()
            yield "gpu??"

    def connected_updates(self) -> Iterator[str]:
        try:
            # https://docs.nvidia.com/deploy/nvml-api/index.html
            nvmlInit()
            handle = nvmlDeviceGetHandleByIndex(0)

            while True:
                # compute has .gpu, .memory; in percent
                # https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g540824faa6cef45500e0d1dc2f50b321
                compute = nvmlDeviceGetUtilizationRates(handle)
                ind_total = self.total_compute.format(compute.gpu / 100)

                # memory has .free, .total, .used; in bytes
                # https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g2dfeb1db82aa1de91aa6edf941c85ca8
                memory = nvmlDeviceGetMemoryInfo(handle)
                ind_memory = self.memory.format(memory.used / memory.total)

                yield f"gpu{ind_total}{ind_memory}"

        finally:
            nvmlShutdown()
