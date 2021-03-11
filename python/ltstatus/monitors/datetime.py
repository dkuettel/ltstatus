import time
from dataclasses import dataclass

from ltstatus import State, ThreadedMonitor


@dataclass
class Monitor(ThreadedMonitor):
    name: str = "datetime"
    format: str = r"%Y-%m-%d %a %H:%M"

    def run(self):
        while not self.exit.is_set():
            t = time.localtime()
            content = time.strftime(self.format, t)
            self.queue.put(State.from_one(self.name, content))
            t = time.localtime()
            self.exit.wait(60 - t.tm_sec + 1)
