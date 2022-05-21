from __future__ import annotations

import time
from dataclasses import dataclass, field
from queue import Empty, Queue
from threading import Event, Thread
from typing import Callable, Iterable, TypeVar, Union

from python.ltstatus.tools import run_cmd


@dataclass
class State:
    elements: dict[str, Union[str, Exception]] = field(default_factory=dict)

    def update(self, u: Update):
        # the first exception sticks, we never clear it
        if isinstance(self.elements.get(u.name, None), Exception):
            return
        if u.state is None:
            self.elements.pop(u.name, None)
            return
        self.elements[u.name] = u.state


@dataclass
class Update:
    name: str
    state: Union[str, Exception, None]


# TODO better to pass timeout or the batched queue instance? and then not even updates itself anymore
def generate_states(updates: Queue[Update], timeout: float = 1 / 30) -> Iterable[State]:
    state = State()
    yield state
    for batch in batched_queue(updates, timeout=timeout):
        for update in batch:
            state.update(update)
        yield state


# TODO how about making this with partial() ? is that better in some way?
@dataclass
class FormatAsSegments:
    order: list[str] = field(default_factory=list)
    separator: str = ", "
    prefix: str = ""
    postfix: str = ""
    waiting: str = "..."

    def __call__(self, state: State) -> str:
        elements = state.elements
        names = self.order + sorted(set(elements) - set(self.order))

        def f(name):
            value = elements.get(name, self.waiting)
            if isinstance(value, Exception):
                return f"{name} failed"
            return value

        return self.prefix + self.separator.join(map(f, names)) + self.postfix


def show_stdout(status: str):
    print(status, flush=True)


def show_xsetroot(status: str):
    run_cmd(["xsetroot", "-name", status])


# TODO does this have to be per generic, or globally once?
T = TypeVar("T")


def batched_queue(updates: Queue[T], timeout: float = 1 / 30) -> Iterable[list[T]]:
    while True:
        batch = [updates.get()]
        try:
            deadline = time.perf_counter() + timeout
            remaining = lambda: deadline - time.perf_counter()
            while remaining() > 0:
                batch.append(updates.get(timeout=remaining()))
        except Empty:
            pass
        yield batch


def run(
    states: Iterable[State],
    format=FormatAsSegments(),
    show=show_stdout,
):
    for state in states:
        show(format(state))


def count_seconds(exit, send):
    for i in range(100):
        time.sleep(1)
        if exit.is_set():
            return
        send(Update("seconds", str(i)))


def give_time(exit, send):
    for _ in range(30):
        time.sleep(1)
        if exit.is_set():
            return
        send(Update("time", str(time.time())))


@dataclass
class Nursery:
    updates: Queue[Update]
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


def test():
    updates = Queue(maxsize=1000)
    exit = Event()
    with Nursery(updates, exit) as nursery:
        nursery.run(lambda: count_seconds(exit, updates.put))
        nursery.run(lambda: give_time(exit, updates.put))
        try:
            run(generate_states(updates, timeout=1 / 30))
        except KeyboardInterrupt:
            print("bye")


if __name__ == "__main__":
    test()
