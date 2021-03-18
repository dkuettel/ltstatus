import math
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List

import psutil

from ltstatus import CallbackMonitor, State, ffield


@dataclass
class Monitor(CallbackMonitor):
    name: str = "cpu"

    def get_updates(self):

        compute = round(psutil.cpu_percent())
        memory = psutil.virtual_memory()

        # using GiB=2**30 instead of GB=1e9, because thats what most other tools show
        content = (
            f"{compute:2}% {round(memory.used/2**30)}/{round(memory.total/2**30)}G"
        )
        return State.from_one(self.name, content)


class Usage(IntEnum):
    idle = 0
    low = 1
    medium = 2
    high = 3

    @classmethod
    def from_brackets(cls, value: float, brackets: List[float]):
        for usage, threshold in zip(cls, brackets + [math.inf]):
            if value < threshold:
                return usage
        raise Exception()


@dataclass
class Calm(CallbackMonitor):
    """show a calm low-detail cpu status
    output with increasing usage:
    - cpu idle  # all idle
    - cpu 1@lo  # 1 core is at low usage
    - cpu m@me  # memory is at medium usage
    - cpu 8@hi  # 8 cores are at high usage
    - cpu #@hi  # more than 9 cores are at high usage
    - cpu *@hi  # multiple things are at high usage (cpu and memory)
    """

    name: str = "cpu"
    # percentage thresholds to separate idle, low, medium, and high cpu compute usage per core
    compute_brackets: List[float] = ffield(lambda: [10, 33, 66])
    # percentage thresholds to separate idle, low, medium, and high cpu memory usage
    memory_brackets: List[float] = ffield(lambda: [10, 33, 66])
    names: Dict[Usage, str] = ffield(
        lambda: {
            Usage.idle: "idle",
            Usage.low: "lo",
            Usage.medium: "me",
            Usage.high: "hi",
        }
    )

    def __post_init__(self):
        assert len(self.compute_brackets) == 3
        assert self.compute_brackets == sorted(self.compute_brackets)
        assert len(self.memory_brackets) == 3
        assert self.memory_brackets == sorted(self.memory_brackets)

    def get_updates(self):
        # TODO this is run as regular updates, but psutil allows blocking calls, so we could also do Threaded
        # the benefit is this would explicitely measure the usage during the blocked time
        # plus it would be easier to implement a super calm hysterisis

        compute_usages = [
            Usage.from_brackets(
                value=v,
                brackets=self.compute_brackets,
            )
            for v in psutil.cpu_percent(percpu=True)
        ]
        max_compute_usage = max(compute_usages)
        max_compute_count = sum(c == max_compute_usage for c in compute_usages)

        memory_usage = Usage.from_brackets(
            value=psutil.virtual_memory().percent,
            brackets=self.memory_brackets,
        )

        if {max_compute_usage, memory_usage} == {Usage.idle}:
            content = f"cpu {self.names[Usage.idle]}"

        elif max_compute_usage == memory_usage:
            content = f"cpu *@{self.names[memory_usage]}"

        elif max_compute_usage > memory_usage:
            if max_compute_count < 10:
                content = f"cpu {max_compute_count}@{self.names[max_compute_usage]}"
            else:
                content = f"cpu #@{self.names[max_compute_usage]}"

        elif memory_usage > max_compute_usage:
            content = f"cpu m@{self.names[memory_usage]}"

        else:
            assert False

        return State.from_one(self.name, content)
