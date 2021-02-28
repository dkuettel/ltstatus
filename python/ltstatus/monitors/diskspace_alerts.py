from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from psutil import disk_usage

from ltstatus import CallbackMonitor
from ltstatus.tools import ffield


# TODO maybe alerts could have a different interface and be grouped, so they sort stably?
@dataclass
class Monitor(CallbackMonitor):
    name: str = "diskspace-alerts"
    # map folders to minimum size (alert when actual < limit)
    limits: Dict[Path, float] = ffield(
        lambda: {
            Path("/var/lib/docker"): 2.0,
            Path("/"): 10.0,
            Path("/home/dkuettel"): 5.0,
        }
    )

    def get_updates(self):
        return {self.name: self.get_content()}

    def get_content(self) -> str:

        # using GiB=2**30 instead of GB=1e9, because thats what most other linux tools show
        GiB = 2 ** 30

        alerts = []
        for folder, limit in sorted(self.limits.items()):
            try:
                free = disk_usage(folder).free / GiB
            except FileNotFoundError:
                pass  # TODO or warn?
            else:
                if free < limit:
                    # TODO because of the round the "<" could look stupid :)
                    alerts.append(f"{folder}@{round(free)}<{round(limit)}GiB")

        if len(alerts) == 0:
            return None
        return ",".join(alerts)
