from __future__ import annotations

import re
from contextlib import contextmanager

from psutil import process_iter


@contextmanager
def monitor(flags: dict[str, re.Pattern]):
    # TODO maybe dont do that so often?
    def fn() -> str:
        raised = set[str]()

        # TODO attrs=["name", "exe", "cmdline"] are useful process attributes here
        for process in process_iter(attrs=["name"]):
            for flag, pattern in flags.items():
                # TODO really check all that?
                if any(pattern.fullmatch(v) for v in process.info.values()):
                    raised.add(flag)

        return ",".join(sorted(raised))

    yield fn
