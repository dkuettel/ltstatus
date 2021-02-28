from __future__ import annotations

import re
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from io import FileIO
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread
from typing import Dict, List, Optional, Union

from ltstatus.tools import ffield


class BaseMonitor:
    """ a monitor produces updates relevant to its observation context """


@dataclass
class ThreadedMonitor(BaseMonitor):
    queue: Optional[Queue] = None
    exit: Optional[Event] = None
    thread: Optional[Thread] = None

    def run(self):
        raise NotImplementedError()

    def start(self, queue: Queue):
        assert self.thread is None
        self.queue = queue
        self.exit = Event()
        self.thread = Thread(target=self.run, daemon=True)
        # TODO daemons dont clean up well
        self.thread.start()

    def stop(self):
        self.exit.set()
        self.thread.join()
        self.queue = None
        self.exit = None
        self.thread = None


@dataclass
class RateLimitedMonitors(ThreadedMonitor):
    rate: float = 30  # max updates per second
    monitors: List[ThreadedMonitor] = ffield(list)

    def run(self):

        # TODO will there be a problem because this is a hierarchy of daemons?
        queue = Queue()
        for m in self.monitors:
            m.start(queue)

        interval = 1 / self.rate
        while not self.exit.is_set():

            # TODO in this way we never react to self.exit.is_set()
            updates = queue.get()
            try:
                while True:
                    updates.update(queue.get_nowait())
            except Empty:
                pass

            self.queue.put(updates)
            self.exit.wait(interval)

        for m in self.monitors:
            m.stop()


class CallbackMonitor(BaseMonitor):
    def get_updates(self) -> Dict[str, str]:
        raise NotImplementedError()


@dataclass
class RegularGroupMonitor(ThreadedMonitor):
    interval: float = 10
    monitors: List[CallbackMonitor] = ffield(list)

    def run(self):
        while not self.exit.is_set():
            updates = dict()
            for m in self.monitors:
                updates.update(m.get_updates())
            self.queue.put(updates)
            self.exit.wait(self.interval)


class Status:
    """ a status transforms a ThreadedMonitor's updates into output of a certain form """


@dataclass
class StdoutStatus(Status):
    monitor: ThreadedMonitor
    order: List[str] = ffield(list)
    separator: str = " "
    prefix: str = "["
    postfix: str = "]"
    waiting: str = "..."

    # TODO we never exit, no exit control
    def run(self):

        queue = Queue()
        self.monitor.start(queue)

        state = dict()
        while True:
            state.update(queue.get())
            print(self.render_state(state), flush=True)

    def render_state(self, state: Dict[str, str]):
        todo = dict(state)
        segments = []
        for k in self.order:
            v = todo.pop(k, self.waiting)
            if v is not None:
                segments.append(self.render_segment(k, v))
        for k, v in todo.items():
            if v is not None:
                segments.append(self.render_segment(k, v))
        return self.separator.join(segments)

    def render_segment(self, key: str, value: str):
        # pylint: disable=unused-argument
        return self.prefix + value + self.postfix


# TODO we would not notice if one thread died, just the state output stays constant
# TODO a debug (or option) to mark in color what changed, what was the reason for the update
# TODO time to setup all those things, especially with vim: pylint, black, isort, configs each of, venv handling
