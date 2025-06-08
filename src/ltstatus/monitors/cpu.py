from __future__ import annotations

from contextlib import contextmanager

import psutil


# TODO put this for everyone to use
def ratio(v: float) -> str:
    """return a compact ratio with one digit"""
    i = round(10 * v)
    if 0 <= i <= 9:
        return f".{i}"
    if i == 10:
        return "1."
    return f"{v:.1f}"


@contextmanager
def monitor():
    # TODO show the most offending process when high cpu or memory?
    # ah a bit difficult, because we cannot just get the recent one, we would have to wait (cpu)

    # TODO add something separate for tmux, but need to see when tmux restarts the status processes, if we can get pids from inside?
    # top --batch --iterations=5 --delay=1 -o '+RES' -w

    times: object | None = None

    def fn() -> str:
        nonlocal times
        new_times: object = psutil.cpu_times()
        if times is None:
            times = new_times
            return "--m -c"

        deltas = psutil._cpu_times_deltas(times, new_times)  # pyright: ignore[reportAttributeAccessIssue]
        cores: float = (
            psutil.cpu_count()
            * psutil._cpu_busy_time(deltas)  # pyright: ignore[reportAttributeAccessIssue]
            / psutil._cpu_tot_time(deltas)  # pyright: ignore[reportAttributeAccessIssue]
        )
        # TODO trying active for now, available might be better?
        memory: float = psutil.virtual_memory().active / psutil.virtual_memory().total

        times = new_times

        return f"{ratio(memory)}m {cores:.0f}c"

    yield fn
