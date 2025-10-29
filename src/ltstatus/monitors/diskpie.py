from __future__ import annotations

import subprocess
from contextlib import contextmanager

from ltstatus.tools import Intervals


@contextmanager
def monitor():
    interval = Intervals.from_seconds(60)
    pies = ["󰄰 ", " 󰪞 ", "󰪟 ", "󰪠 ", "󰪡 ", "󰪢 ", "󰪣 ", "󰪤 ", "󰪥 "]
    state = "  "

    def fn() -> str:
        nonlocal interval, pies, state

        if interval():
            # NOTE assumes there is only one pool
            result = subprocess.run(
                ["zfs", "list", "-d", "0", "-pH", "-o", "avail,used"],
                capture_output=True,
                text=True,
            )
            avail, used = map(int, result.stdout.split())
            ratio = used / (used + avail)
            i = round(ratio * 8)
            state = pies[i]

        return state

    yield fn
