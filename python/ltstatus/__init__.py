from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Optional, Union

from ltstatus import formats, outputs
from ltstatus.core import (
    Format,
    Output,
    State,
    UpdateContext,
    UpdateThread,
    run_update_threads,
)


@dataclass
class RealtimeContext:
    update_context: UpdateContext
    name: str

    def __post_init__(self):
        self.last_update = None

    def should_exit(self) -> bool:
        return self.update_context.should_exit()

    def sleep(self, seconds: float):
        self.update_context.sleep(seconds)

    def send(self, update: str):
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
        mcontext = RealtimeContext(context, self.monitor.name)
        try:
            self.monitor.run(mcontext)
        except:
            mcontext.send(f"{self.monitor.name} failed")


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
        # TODO this forces an update every interval
        # even if no one really had an update
        # but iterators cannot return something saying "no update"
        # we can only here check if it's still the same?
        # TODO we also dont react nicely here to any exception
        # either set the state of that one, or start skipping? right now state will be stalled
        updates = {m.name: m.updates() for m in self.monitors}
        while not context.should_exit():
            batch = State()
            for name, update in updates.items():
                batch.update({name: next(update)})
            context.send(batch)
            context.sleep(self.interval)


def run(
    monitors: list[Union[RealtimeMonitor, PollingMonitor]],
    polling_interval: float = 1.0,
    format: Optional[Format] = None,
    output: Optional[Output] = None,
):
    format = format or formats.plain()
    output = output or outputs.stdout()

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
        state={name: None for name in names},
        threads=threads,
        format=format,
        output=output,
    )


def test():
    from pathlib import Path

    from ltstatus import formats, monitors as m, outputs, run

    da = m.DiskspaceAlerts(
        limits={
            Path("/var/lib/docker"): 2.0,
            Path("/"): 10.0,
            Path("~"): 5.0,
        },
    )
    pa = m.ProcessAlerts(flags={"steam": r".*steam.*"})

    run(
        monitors=[
            m.Spotify(),
            m.Redshift(),
            m.Bluetooth(),
            m.Sound(),
            m.Dropbox(),
            da,
            m.Cpu(),
            m.Nvidia(),
            m.Datetime(),
            pa,
        ],
        polling_interval=1,
        format=formats.tmux(),
        output=outputs.stdout(),
    )


if __name__ == "__main__":
    test()
