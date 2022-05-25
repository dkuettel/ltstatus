from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Optional, Union

from .core import Format, Output, State, UpdateContext, UpdateThread, run_update_threads


@dataclass
class RealtimeContext:
    update_context: UpdateContext
    name: str

    def should_exit(self) -> bool:
        return self.update_context.should_exit()

    def sleep(self, seconds: float):
        self.update_context.sleep(seconds)

    def send(self, update: str):
        self.update_context.send(State.from_one(self.name, update))


@dataclass
class RealtimeMonitor(ABC):
    name: str

    @abstractmethod
    def run(self, context: RealtimeContext):
        """check exit regularly and send updates whenever necessary"""


@dataclass
class RealtimeThread(UpdateThread):
    monitor: RealtimeMonitor

    def run(self, context: UpdateContext):
        self.monitor.run(RealtimeContext(context, self.monitor.name))


@dataclass
class PollingMonitor(ABC):
    name: str

    @abstractmethod
    def updates(self) -> Iterator[str]:
        """This iterator needs to be infinite"""


@dataclass
class PollingThread(UpdateThread):
    monitors: list[PollingMonitor]
    interval: float = 1.0

    def run(self, context: UpdateContext):
        updates = {m.name: m.updates() for m in self.monitors}
        while not context.should_exit():
            batch = State.from_empty()
            for name, update in updates.items():
                batch.update(State.from_one(name, next(update)))
            context.send(batch)
            context.sleep(self.interval)


def run(
    monitors: list[Union[RealtimeMonitor, PollingMonitor]],
    polling_interval: float = 1.0,
    format: Optional[Format] = None,
    output: Optional[Output] = None,
):

    if format is None:
        from . import formats

        format = formats.plain()

    if output is None:
        from . import outputs

        output = outputs.stdout()

    # TODO still not super happy about the need for names for identifying
    # people can mess it up. for meta info and debug it's fine, but not for ordering and state keys
    names = [m.name for m in monitors]
    assert len(names) == len(set(names))

    realtime = [m for m in monitors if isinstance(m, RealtimeMonitor)]
    polling = [m for m in monitors if isinstance(m, PollingMonitor)]
    assert len(realtime) + len(polling) == len(monitors)

    threads: list[UpdateThread] = [RealtimeThread(m) for m in realtime]

    if len(polling) > 0:
        threads.append(PollingThread(polling, polling_interval))

    run_update_threads(
        state=State.from_empty(names),
        threads=threads,
        format=format,
        output=output,
    )


def test():
    from ltstatus import formats, outputs
    from ltstatus.new_monitors import polling as p, realtime as rt

    run(
        monitors=[p.cpu()],
        polling_interval=1,
        format=formats.tmux(),
        output=outputs.stdout(),
    )


if __name__ == "__main__":
    from . import alternative

    alternative.test()
