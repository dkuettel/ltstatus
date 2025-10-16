from __future__ import annotations

from contextlib import contextmanager

from pynvml import (
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetMemoryInfo,
    nvmlDeviceGetUtilizationRates,
    nvmlInit,
    nvmlShutdown,
)


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
            gpu_usage: int = round(compute.gpu / 10) * 10  # pyright: ignore[reportArgumentType, reportOperatorIssue]

            # memory has .free, .total, .used; in bytes
            # https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g2dfeb1db82aa1de91aa6edf941c85ca8
            memory = nvmlDeviceGetMemoryInfo(handle)
            memory_usage: int = round(memory.used / memory.total * 10) * 10  # pyright: ignore[reportUnusedVariable, reportOperatorIssue]

            return f"{gpu_usage: 2}% {memory_usage: 2}%"

        yield fn

    finally:
        # NOTE we might not be the only one using that, but hard to coordinate that
        nvmlShutdown()
