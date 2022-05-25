from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from queue import Empty, Queue
from threading import Event
from typing import Iterator, Optional

from .threading import Nursery


@dataclass
class State:
    entries: dict[str, Optional[str]]

    @classmethod
    def from_empty(cls, names: list[str] = []) -> State:
        return cls({name: None for name in names})

    @classmethod
    def from_one(cls, name: str, value: Optional[str]) -> State:
        return cls({name: value})

    def update(self, other: State):
        self.entries.update(other.entries)

    def update_all(self, others: list[State]):
        for other in others:
            self.update(other)

    def clone(self) -> State:
        return State(dict(self.entries))

    def values(self) -> list[Optional[str]]:
        return list(self.entries.values())


@dataclass
class UpdateContext:
    exit: Event = field(default_factory=Event)
    updates: Queue[State] = field(default_factory=lambda: Queue(maxsize=1000))

    def should_exit(self) -> bool:
        return self.exit.is_set()

    def sleep(self, seconds: float):
        self.exit.wait(seconds)

    def send(self, state: State):
        self.updates.put(state)


class UpdateThread(ABC):
    @abstractmethod
    def run(self, context: UpdateContext):
        pass


class Format(ABC):
    @abstractmethod
    def apply(self, state: State) -> str:
        pass


class Output(ABC):
    @abstractmethod
    def push(self, status: str):
        pass


# TODO reading from a queue (generically) batched with back-off could be utility for monitors
# rewrite and make run_from_states to run_from_queue ?
def generate_states_from_queue(
    state: State,
    updates: Queue[State],
    timeout: float = 1 / 30,
) -> Iterator[State]:
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


def run_from_states(states: Iterator[State], format: Format, output: Output):
    for state in states:
        output.push(format.apply(state))


def run_update_threads(
    state: State,
    threads: list[UpdateThread],
    format: Format,
    output: Output,
):
    c = UpdateContext()
    with Nursery(c.exit, c.updates) as n:
        for t in threads:
            n.run(lambda: t.run(c))
        states = generate_states_from_queue(state, c.updates)
        try:
            run_from_states(states, format, output)
        except KeyboardInterrupt:
            pass
