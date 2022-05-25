from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Optional, Union

from .core import Format, Output, State, UpdateContext, UpdateThread, run_update_threads


@dataclass
class RealtimeContext:
    update_context: UpdateContext
    name: str

    def __post_init__(self):
        self.last_update = object()

    def should_exit(self) -> bool:
        return self.update_context.should_exit()

    def sleep(self, seconds: float):
        self.update_context.sleep(seconds)

    def send(self, update: Optional[str]):
        if update == self.last_update:
            return
        self.update_context.send({self.name: update})
        self.last_update = update


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
    def updates(self) -> Iterator[Optional[str]]:
        """This iterator needs to be infinite"""


@dataclass
class PollingThread(UpdateThread):
    monitors: list[PollingMonitor]
    interval: float = 1.0

    def run(self, context: UpdateContext):
        updates = {m.name: m.updates() for m in self.monitors}
        while not context.should_exit():
            batch = State()
            for name, update in updates.items():
                batch.update({name: next(update)})
            context.send(batch)
            context.sleep(self.interval)


@dataclass
class OrderedFormat(Format):
    order: list[str]
    format: Format
    waiting: str = ""  # alternatives: ..., , …

    def apply(self, state: State) -> str:
        ordered_state = {name: state.get(name, self.waiting) for name in self.order}
        return self.format.apply(ordered_state)


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

    ordered_format = OrderedFormat(names, format)

    run_update_threads(
        threads=threads,
        format=ordered_format,
        output=output,
    )


def test():
    from pathlib import Path

    from ltstatus import formats, new_monitors as m, outputs

    da = m.diskspace_alerts(
        limits={
            Path("/var/lib/docker"): 2.0,
            Path("/"): 10.0,
            Path("~"): 5.0,
        }
    )
    run(
        monitors=[da],
        polling_interval=1,
        format=formats.tmux(),
        output=outputs.stdout(),
    )


if __name__ == "__main__":
    from . import alternative

    alternative.test()
