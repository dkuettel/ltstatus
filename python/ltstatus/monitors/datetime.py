import time
from dataclasses import dataclass

from ltstatus import ThreadedMonitor, State


@dataclass
class Monitor(ThreadedMonitor):
    name: str = "datetime"

    def run(self):
        while not self.exit.is_set():
            t = time.localtime()
            content = time.strftime(r"%Y-%m-%d %a %H:%M", t)
            self.queue.put(State.from_one(self.name, content))
            t = time.localtime()
            self.exit.wait(60 - t.tm_sec + 1)
