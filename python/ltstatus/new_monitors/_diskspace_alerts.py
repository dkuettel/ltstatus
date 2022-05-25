from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, Optional

from psutil import disk_usage

from ..alternative import PollingMonitor
from ..tools import ffield


# TODO maybe alerts could have a different interface and be grouped, so they sort stably?
# TODO plus this behavior has changed a bit, formatter shows all entries, there is no way to say "dont show"
# do we want it? I think for tmux at least, we only want to see it when it's doing something
# allow state as: not-yet-initialized, None for dont show, str for what it is
# yes we definitely need a monitor to be able to say dont show me, independent of alerts anyway
# state sticks with having a mandatory list and actual values, it's up to the formatter how smart it does it?
# the nice thing is then state typing doesnt change, only meaning of None changes
@dataclass
class Monitor(PollingMonitor):
    name: str = "diskspace-alerts"
    # map folders to minimum size in GB (alert when actual < limit)
    limits: Dict[Path, float] = ffield(dict)

    def __post_init__(self):
        self.limits = {path.expanduser(): limit for path, limit in self.limits.items()}

    def updates(self) -> Iterator[Optional[str]]:
        while True:
            yield self.get_state()

    def get_state(self) -> Optional[str]:

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

        if len(alerts) == 0:
            return ""
            # return None
        return ",".join(alerts)
