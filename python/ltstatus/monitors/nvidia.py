from dataclasses import dataclass

from pynvml import (
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetMemoryInfo,
    nvmlDeviceGetUtilizationRates,
    nvmlInit,
    nvmlShutdown,
)

from ltstatus import ThreadedMonitor


# TODO this should be CallbackMonitor, probably
@dataclass
class Monitor(ThreadedMonitor):
    name: str = "nvidia"
    interval: float = 1

    def run(self):
        # TODO how to not have unavailable status? test before and not even add it?
        nvmlInit()
        handle = nvmlDeviceGetHandleByIndex(0)

        while not self.exit.is_set():
            # memory has .total, .used, .free; in bytes
            memory = nvmlDeviceGetMemoryInfo(handle)
            # compute has .gpu, .memory; in percent
            compute = nvmlDeviceGetUtilizationRates(handle)
            # using GiB=2**30 instead of GB=1e9, because thats also what nvidia-smi shows
            content = f"{compute.gpu:2}% {round(memory.used/2**30)}/{round(memory.total/2**30)}G"
            self.queue.put({self.name: content})
            self.exit.wait(self.interval)
        nvmlShutdown()
