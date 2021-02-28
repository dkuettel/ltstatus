from dataclasses import dataclass

import psutil

from ltstatus import CallbackMonitor


@dataclass
class Monitor(CallbackMonitor):
    name: str = "cpu"

    def get_updates(self):

        compute = round(psutil.cpu_percent())
        memory = psutil.virtual_memory()

        # using GiB=2**30 instead of GB=1e9, because thats what most other tools show
        content = (
            f"{compute:2}% {round(memory.used/2**30)}/{round(memory.total/2**30)}G"
        )
        return {self.name: content}
