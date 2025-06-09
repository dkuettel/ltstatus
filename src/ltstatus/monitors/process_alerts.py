from __future__ import annotations

import re
from contextlib import contextmanager

from psutil import process_iter

from ltstatus.tools import Intervals


@contextmanager
def monitor(flags: dict[str, re.Pattern]):
    interval = Intervals.from_seconds(5)
    raised = set[str]()

    def fn() -> str:
        nonlocal interval, raised

        if interval():
            raised = set[str]()

            # TODO attrs=["name", "exe", "cmdline"] are useful process attributes here
            raised = {
                flag
                for process in process_iter(attrs=["name"])
                for flag, pattern in flags.items()
                # TODO really check all that?
                if any(pattern.fullmatch(v) for v in process.info.values())
            }

        return ",".join(sorted(raised))

    yield fn
