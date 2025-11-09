from __future__ import annotations

from contextlib import contextmanager

from pynvml import (
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetMemoryInfo,
    nvmlDeviceGetUtilizationRates,
    nvmlInit,
    nvmlShutdown,
    NVMLError_LibraryNotFound,  # pyright: ignore[reportAttributeAccessIssue]
)

def missing():
    return "- - "

@contextmanager
def monitor():
    # https://docs.nvidia.com/deploy/nvml-api/index.html
    try:
        nvmlInit()
    except NVMLError_LibraryNotFound:
        yield missing
        return

    try:
        handle = nvmlDeviceGetHandleByIndex(0)

        def fn() -> str:
            # compute has .gpu, .memory; in percent
            # https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g540824faa6cef45500e0d1dc2f50b321
            compute = nvmlDeviceGetUtilizationRates(handle)
            gpu_usage: int = round(compute.gpu / 100 * 3)  # pyright: ignore[reportArgumentType, reportOperatorIssue]

            # memory has .free, .total, .used; in bytes
            # https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries_1g2dfeb1db82aa1de91aa6edf941c85ca8
            memory = nvmlDeviceGetMemoryInfo(handle)
            memory_usage: int = round(memory.used / memory.total * 6)  # pyright: ignore[reportUnusedVariable, reportOperatorIssue]

            arrows = ["  ", "󰅂 ", "󰄾 ", "󰶻 "]
            hexas = ["󰋙 ", "󰫃 ", "󰫄 ", "󰫅 ", "󰫆 ", "󰫇 ", "󰫈 "]

            return f"{hexas[memory_usage]}{arrows[gpu_usage]}"

        yield fn

    finally:
        # NOTE we might not be the only one using that, but hard to coordinate that
        nvmlShutdown()
