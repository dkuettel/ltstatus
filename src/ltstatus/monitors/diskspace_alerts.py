from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from psutil import disk_usage

from ltstatus.tools import Intervals


def is_low(folder: Path, limit_gb: float) -> bool:
    try:
        free_gb = disk_usage(str(folder.expanduser())).free / 1e9
    except FileNotFoundError:
        return False  # TODO or warn?
    return free_gb < limit_gb


@contextmanager
def monitor(limits_gb: dict[Path, float]):
    interval = Intervals.from_seconds(5)
    low = set[Path]()

    def fn() -> str:
        nonlocal interval, low

        if interval():
            low = {
                folder
                for folder, limit_gb in sorted(limits_gb.items())
                if is_low(folder, limit_gb)
            }

        if len(low) == 0:
            return ""

        return "low@{','.join(low)}"

    yield fn
