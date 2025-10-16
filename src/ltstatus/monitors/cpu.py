from __future__ import annotations

from contextlib import contextmanager

import psutil


@contextmanager
def monitor():
    # TODO show the most offending process when high cpu or memory?
    # ah a bit difficult, because we cannot just get the recent one, we would have to wait (cpu)

    # TODO add something separate for tmux, but need to see when tmux restarts the status processes, if we can get pids from inside?
    # top --batch --iterations=5 --delay=1 -o '+RES' -w

    times: object | None = None
    count = psutil.cpu_count()
    assert count is not None
    padding = len(str(count))

    def fn() -> str:
        nonlocal times

        new_times: object = psutil.cpu_times()
        if times is None:
            times = new_times
            return ""

        deltas = psutil._cpu_times_deltas(times, new_times)  # pyright: ignore[reportAttributeAccessIssue]
        times = new_times

        cores: int = round(
            count
            * psutil._cpu_busy_time(deltas)  # pyright: ignore[reportAttributeAccessIssue]
            / psutil._cpu_tot_time(deltas)  # pyright: ignore[reportAttributeAccessIssue]
        )

        memory: int = round(psutil.virtual_memory().percent / 10) * 10

        return f"{cores: {padding}}∕{count} {memory: 2}%"

    yield fn
