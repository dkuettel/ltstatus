from __future__ import annotations

import multiprocessing as mp
import queue
import threading
from contextlib import contextmanager

import psutil


def watch(stop: threading.Event, states: mp.Queue[str]):
    short = 1  # seconds
    long = 5  # seconds

    old_times: object | None = None
    watching: bool = False

    while not stop.is_set():
        new_times: object = psutil.cpu_times()

        if old_times is None:
            old_times = new_times
            stop.wait(long)
            continue

        deltas = psutil._cpu_times_deltas(old_times, new_times)  # pyright: ignore[reportAttributeAccessIssue]
        cores: float = (
            psutil.cpu_count()
            * psutil._cpu_busy_time(deltas)  # pyright: ignore[reportAttributeAccessIssue]
            / psutil._cpu_tot_time(deltas)  # pyright: ignore[reportAttributeAccessIssue]
        )

        # TODO trying active for now, available might be better?
        memory: float = psutil.virtual_memory().active / psutil.virtual_memory().total

        if (cores >= 1) or (memory > 0.7):
            if watching:
                heavy_processes = {
                    f"{p.name()}@{p.info['memory_info'].rss/1e9:.0f}gb{p.info['cpu_percent']/100:.0f}c"
                    for p in psutil.process_iter(attrs=["cpu_percent", "memory_info"])
                    if (p.info["cpu_percent"] >= 50)
                    or (p.info["memory_info"].rss / 1e9 > 2)
                }
                states.put(",".join(sorted(heavy_processes)))
                stop.wait(long)
                continue
            watching = True
            for p in psutil.process_iter():
                p.cpu_percent()
            states.put("")
            stop.wait(short)
            continue

        watching = False
        states.put("")
        stop.wait(long)


@contextmanager
def monitor():
    stop = mp.Event()
    states: mp.Queue[str] = mp.Queue()
    state = ""

    process = mp.Process(target=watch, args=(stop, states))
    process.start()

    def fn() -> str:
        nonlocal states, state
        try:
            while True:
                state = states.get_nowait()
        except queue.Empty:
            pass
        return state

    try:
        yield fn
    finally:
        # TODO not sure if this ends properly on ctrl-c or other things
        stop.set()
        process.join()
