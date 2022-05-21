from __future__ import annotations

import time
from dataclasses import dataclass, field
from itertools import zip_longest
from queue import Empty, Queue
from threading import Event, Thread
from typing import Callable, Iterable

from python.ltstatus.tools import run_cmd

State = dict[str, str]


def generate_states(updates: Queue[State], timeout: float = 1 / 30) -> Iterable[State]:
    state = State()
    yield state
    while True:
        state.update(updates.get())
        try:
            deadline = time.perf_counter() + timeout
            remaining = lambda: deadline - time.perf_counter()
            while remaining() > 0:
                state.update(updates.get(timeout=remaining()))
        except Empty:
            pass
        yield state


def format_segments(
    state: State,
    order: list[str] = [],
    separator: str = ", ",
    prefix: str = "[",
    postfix: str = "]",
    waiting: str = "...",
) -> str:
    names = order + sorted(set(state) - set(order))
    values = (f"{name}={state.get(name, waiting)}" for name in names)
    return prefix + separator.join(values) + postfix


def show_stdout(status: str):
    print(status, flush=True)


def show_xsetroot(status: str):
    run_cmd(["xsetroot", "-name", status])


def run(
    states: Iterable[State],
    format=format_segments,
    show=show_stdout,
):
    for state in states:
        show(format(state))


def count_seconds(exit, send):
    for i in range(100):
        time.sleep(1)
        if exit.is_set():
            return
        send({"seconds": str(i)})


def give_time(exit, send):
    for _ in range(30):
        time.sleep(1)
        if exit.is_set():
            return
        send({"time": str(time.time())})


@dataclass
class Nursery:
    updates: Queue[State]
    exit: Event
    threads: list[Thread] = field(default_factory=list)

    def run(self, fn: Callable[[], None]):
        t = Thread(target=fn)
        self.threads.append(t)
        t.start()

    def __enter__(self) -> Nursery:
        return self

    def __exit__(self, *_) -> bool:
        self.exit.set()
        for t in self.threads:
            while t.is_alive():
                try:
                    for _ in range(len(self.threads)):
                        self.updates.get_nowait()
                except Empty:
                    pass
            t.join(0.1)
        return False


def poll_updates(
    exit,
    send,
    interval: float,
    sources: list[Iterable[State]],
):
    for updates in zip_longest(*sources, fillvalue=None):
        batch = State()
        for update in updates:
            batch.update(update)
        send(batch)
        if exit.wait(interval):
            return


def generate_time_updates() -> Iterable[State]:
    while True:
        yield {"ptime": str(time.time())}


def test():
    updates = Queue(maxsize=1000)
    exit = Event()
    sources = [generate_time_updates()]
    with Nursery(updates, exit) as nursery:
        nursery.run(lambda: count_seconds(exit, updates.put))
        nursery.run(lambda: give_time(exit, updates.put))
        nursery.run(lambda: poll_updates(exit, updates.put, 1, sources))
        try:
            run(generate_states(updates, timeout=1 / 30))
        except KeyboardInterrupt:
            print("bye")


if __name__ == "__main__":
    test()
