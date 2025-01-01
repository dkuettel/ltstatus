from __future__ import annotations

from dataclasses import dataclass, field
from queue import Empty, Queue
from threading import Event, Thread
from typing import Callable, Optional

NurseryFn = Callable[[], None]


@dataclass
class Nursery:
    """context manager to run and cleanup threads

    While in the context, start new threads with 'run'.
    All threads will be joined when leaving the context.
    All threads must react to the 'exit' event.
    Threads can be waiting in 'queue.put' when it is full.
    The queue will be emptied while stopping the nursery to unblock threads.

    Dont reuse nurseries.
    """

    exit: Event
    queue: Optional[Queue] = None
    threads: list[Thread] = field(default_factory=list)

    def run(self, fn: NurseryFn):
        t = Thread(target=fn)
        self.threads.append(t)
        t.start()

    def __enter__(self) -> Nursery:
        return self

    def __exit__(self, *_) -> bool:
        self.exit.set()
        for t in self.threads:
            while t.is_alive():
                self._flush_queue()
                t.join(0.1)
        return False

    def _flush_queue(self):
        if self.queue is None:
            return
        try:
            for _ in range(len(self.threads)):
                self.queue.get_nowait()
        except Empty:
            pass
