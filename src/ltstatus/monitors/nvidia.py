from __future__ import annotations

from contextlib import contextmanager

from pynvml import (
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetMemoryInfo,
    nvmlDeviceGetUtilizationRates,
    nvmlInit,
    nvmlShutdown,
)

from ltstatus.monitors.cpu import ratio


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
