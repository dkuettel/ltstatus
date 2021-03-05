from __future__ import annotations

import re
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from io import FileIO
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread
from typing import Dict, Iterable, List, Optional, Union

from ltstatus.tools import ffield


@dataclass
class State:
    """ a state maps from a name to a value or an exception """

    states: Dict[str, Union[str, Exception]] = ffield(dict)

    @classmethod
    def from_one(cls, name: str, value: Union[str, Exception]):
        return cls(states={name: value})

    def update(self, other: State):
        """ apply updates, but never clear a previous exception, exceptions stick (the first one) """
        for key, value in other.items():
            if isinstance(self.states.get(key, None), Exception):
                continue
            self.states[key] = value

    def items(
        self,
        order: Optional[List[str]] = None,
        missing: str = "...",
    ) -> Iterable[str, Union[str, Exception]]:
        """ return (key, value) in order and then all remaining in sorted(key) order """
        order = order or []
        order = order + list(sorted(set(self.states) - set(order)))
        for key in order:
            yield key, self.states.get(key, missing)


@dataclass
class StatesQueue:
    """ main channel for 'BaseMonitor's to send updates in form of 'States' to 'Status' """

    queue: Queue = ffield(Queue)

    def put(self, update: State):
        self.queue.put(update)

    def get(self) -> State:
        return self.queue.get()

    def get_merged(self) -> State:
        """ wait until at least one message and then return all available states merged """
        state = State()
        state.update(self.queue.get())
        try:
            while True:
                state.update(self.queue.get_nowait())
        except Empty:
            pass
        return state


class BaseMonitor:
    """ a monitor produces updates relevant to its observation context """

    name: str


@dataclass
class ThreadedMonitor(BaseMonitor):
    name: str
    queue: Optional[StatesQueue] = None
    exit: Optional[Event] = None
    thread: Optional[Thread] = None

    def run(self):
        raise NotImplementedError()

    def start(self, queue: StatesQueue):
        assert self.thread is None
        self.queue = queue
        self.exit = Event()
        self.thread = Thread(target=self._run, daemon=True)
        # TODO daemons dont clean up well
        self.thread.start()

    def _run(self):
        queue = self.queue
        try:
            self.run()
        except BaseException as e:
            queue.put(State.from_one(self.name, e))
            raise

    def stop(self):
        self.exit.set()
        self.thread.join()
        self.queue = None
        self.exit = None
        self.thread = None


@dataclass
class RateLimitedMonitors(ThreadedMonitor):
    name: str = "rate-limited"
    rate: float = 30  # max updates per second
    monitors: List[ThreadedMonitor] = ffield(list)

    def run(self):

        # TODO will there be a problem because this is a hierarchy of daemons?
        queue = StatesQueue()
        for m in self.monitors:
            m.start(queue)

        interval = 1 / self.rate
        while not self.exit.is_set():
            # TODO in this way we never react to self.exit.is_set() while waiting
            state = queue.get_merged()
            self.queue.put(state)
            self.exit.wait(interval)

        for m in self.monitors:
            m.stop()


class CallbackMonitor(BaseMonitor):
    name: str

    def get_updates(self) -> State:
        raise NotImplementedError()


@dataclass
class RegularGroupMonitor(ThreadedMonitor):
    name: str = "regular-group"
    interval: float = 10
    monitors: List[CallbackMonitor] = ffield(list)

    def run(self):
        """ a regular group fails as a whole when one fails """
        while not self.exit.is_set():
            state = State()
            for m in self.monitors:
                state.update(m.get_updates())
            self.queue.put(state)
            self.exit.wait(self.interval)


class Status:
    """ a status transforms a ThreadedMonitor's updates into output of a certain form """


@dataclass
class StdoutStatus(Status):
    """ on every update, ouptut full state on a single line, eg, the way tmux consumes an external status line """

    monitor: ThreadedMonitor
    order: List[str] = ffield(list)
    separator: str = " "
    prefix: str = "["
    postfix: str = "]"
    waiting: str = "..."

    # TODO we never exit, no exit control
    def run(self):

        queue = StatesQueue()
        self.monitor.start(queue)

        state = State()
        while True:
            state.update(queue.get())
            print(self.render_state(state), flush=True)

    def render_state(self, state: State):
        segments = [
            self.render_segment(k, v)
            for k, v in state.items(order=self.order, missing=self.waiting)
            if v is not None
        ]
        return self.separator.join(segments)

    def render_segment(self, key: str, value: Union[str, Exception]):
        if isinstance(value, str):
            return self.prefix + value + self.postfix
        elif isinstance(value, Exception):
            return self.prefix + f"{key} failed" + self.postfix
        else:
            raise Exception(f"wrong type {type(value)}")
