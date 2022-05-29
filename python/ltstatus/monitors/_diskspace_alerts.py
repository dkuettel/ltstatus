from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator

from psutil import disk_usage

from .. import PollingMonitor
from ..tools import ffield


# TODO maybe alerts could have a different interface and be grouped, so they sort stably?
@dataclass
class Monitor(PollingMonitor):
    name: str = "diskspace-alerts"
    # map folders to minimum size in GB (alert when actual < limit)
    limits: Dict[Path, float] = ffield(dict)

    def __post_init__(self):
        self.limits = {path.expanduser(): limit for path, limit in self.limits.items()}

    def updates(self) -> Iterator[str]:
        while True:
            yield self.get_state()

    def get_state(self) -> str:

        # using GiB=2**30 instead of GB=1e9, because thats what most other linux tools show
        GiB = 2 ** 30

        alerts = []
        for folder, limit in sorted(self.limits.items()):
            try:
                free = disk_usage(str(folder)).free / GiB
            except FileNotFoundError:
                pass  # TODO or warn?
            else:
                if free < limit:
                    # TODO because of the round the "<" could look stupid :)
                    alerts.append(f"{folder}@{round(free)}<{round(limit)}GiB")

        return ",".join(alerts)
