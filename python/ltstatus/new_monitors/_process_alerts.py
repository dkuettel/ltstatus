import re
from dataclasses import dataclass
from typing import Dict, Iterator, Union

from psutil import process_iter

from ..alternative import PollingMonitor
from ..tools import ffield


@dataclass
class Monitor(PollingMonitor):
    """notify when certain process are running, like, eg, 'steam' that might continue to run in the background"""

    name: str = "process-alerts"
    flags: Dict[str, Union[str, re.Pattern]] = ffield(dict)

    def updates(self) -> Iterator[str]:
        while True:
            yield self.get_state()

    def get_state(self) -> str:

        raised = set()

        # TODO attrs=["name", "exe", "cmdline"] are useful process attributes here
        for process in process_iter(attrs=["name"]):
            for flag, pattern in self.flags.items():
                if type(pattern) is str:
                    pattern = re.compile(pattern)
                    self.flags[flag] = pattern
                assert type(pattern) == re.Pattern, pattern
                if any(pattern.fullmatch(v) for v in process.info.values()):
                    raised.add(flag)

        return ",".join(sorted(raised))
