from __future__ import annotations

import time
from dataclasses import dataclass

from ltstatus import RealtimeContext, RealtimeMonitor


@dataclass
class Monitor(RealtimeMonitor):
    name: str = "datetime"
    format: str = r"%Y-%m-%d %a %H:%M"

    def with_icons(self) -> Monitor:
        return self

    def run(self, context: RealtimeContext):
        while not context.should_exit():
            t = time.localtime()
            context.send(time.strftime(self.format, t))
            t = time.localtime()
            context.sleep(60 - t.tm_sec + 1)
