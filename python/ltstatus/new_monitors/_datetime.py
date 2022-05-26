import time
from dataclasses import dataclass

from ..alternative import RealtimeContext, RealtimeMonitor


@dataclass
class Monitor(RealtimeMonitor):
    name: str = "datetime"
    format: str = r"%Y-%m-%d %a %H:%M"

    def run(self, context: RealtimeContext):
        while not context.should_exit():
            t = time.localtime()
            context.send(time.strftime(self.format, t))
            t = time.localtime()
            context.sleep(60 - t.tm_sec + 1)