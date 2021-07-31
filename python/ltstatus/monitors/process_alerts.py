import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Union

from psutil import process_iter

from ltstatus import CallbackMonitor, State
from ltstatus.tools import ffield


@dataclass
class Monitor(CallbackMonitor):
    """ notify when certain process are running, like, eg, 'steam' that might continue to run in the background """

    name: str = "process-alerts"
    flags: Dict[str, Union[str, re.Pattern]] = ffield(dict)

    def get_updates(self):
        return State.from_one(self.name, self.get_content())

    def get_content(self) -> str:

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

        if not raised:
            return None

        return ",".join(sorted(raised))
