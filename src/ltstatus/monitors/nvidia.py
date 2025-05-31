from __future__ import annotations

from contextlib import contextmanager
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
from ltstatus.monitors.cpu import ratio


@dataclass
class Monitor(PollingMonitor):
    name: str = "nvidia"
    compute: RatioIndicator = RatioIndicator(bin_themes["LMH"])
    memory: RatioIndicator = RatioIndicator(bin_themes["LMH"])
    prefix: str = "gpu"
    missing: str = "??"
    icons: bool = False

    def with_icons(self) -> Monitor:
        self.compute = RatioIndicator(bin_themes["thermometer"])
        self.memory = RatioIndicator(bin_themes["battery!"])
        self.prefix = ""
        self.missing = ""
        return self

    def updates(self) -> Iterator[str]:
        while True:
            yield from self.connected_updates()
            yield f"{self.prefix}{self.missing}"

    def connected_updates(self) -> Iterator[str]:
        try:
            # https://docs.nvidia.com/deploy/nvml-api/index.html
            nvmlInit()

            handle = nvmlDeviceGetHandleByIndex(0)

            while True:
                # compute has .gpu, .memory; in percent
                # https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g540824faa6cef45500e0d1dc2f50b321
                compute = nvmlDeviceGetUtilizationRates(handle)
                ind_compute = self.compute.format(compute.gpu / 100)

                # memory has .free, .total, .used; in bytes
                # https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g2dfeb1db82aa1de91aa6edf941c85ca8
                memory = nvmlDeviceGetMemoryInfo(handle)
                ind_memory = self.memory.format(memory.used / memory.total)

                yield f"{self.prefix}{ind_compute}{ind_memory}"

        finally:
            nvmlShutdown()


@contextmanager
def monitor():
    # https://docs.nvidia.com/deploy/nvml-api/index.html
    nvmlInit()

    try:
        handle = nvmlDeviceGetHandleByIndex(0)

        def fn() -> str:
            # compute has .gpu, .memory; in percent
            # https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g540824faa6cef45500e0d1dc2f50b321
            compute = nvmlDeviceGetUtilizationRates(handle)
            c = ratio(compute.gpu / 100)  # pyright: ignore[reportOperatorIssue]

            # memory has .free, .total, .used; in bytes
            # https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g2dfeb1db82aa1de91aa6edf941c85ca8
            memory = nvmlDeviceGetMemoryInfo(handle)
            m = ratio(memory.used / memory.total)  # pyright: ignore[reportUnusedVariable, reportOperatorIssue]

            return f"{m}m {c}c"

        yield fn

    finally:
        # NOTE we might not be the only one using that, but hard to coordinate that
        nvmlShutdown()
