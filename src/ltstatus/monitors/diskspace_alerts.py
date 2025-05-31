from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from psutil import disk_usage


@contextmanager
def monitor(limits_gb: dict[Path, float]):
    def fn() -> str:
        low = set[Path]()
        for folder, limit_gb in sorted(limits_gb.items()):
            try:
                free_gb = disk_usage(str(folder.expanduser())).free / 1e9
            except FileNotFoundError:
                pass  # TODO or warn?
            else:
                if free_gb < limit_gb:
                    low.add(folder)

        if len(low) == 0:
            return ""

        return "low@{','.join(low)}"

    yield fn
