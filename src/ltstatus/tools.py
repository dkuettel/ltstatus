from __future__ import annotations

import time
from dataclasses import dataclass


def compact_ratio(v: float) -> str:
    """return a compact ratio with one digit"""
    i = round(10 * v)
    if 0 <= i <= 9:
        return f".{i}"
    if i == 10:
        return "1."
    return f"{v:.1f}"


@dataclass
class Intervals:
    seconds: float
    last: None | float

    @classmethod
    def from_seconds(cls, seconds: float):
        return cls(seconds, None)

    def __call__(self) -> bool:
        """check and maybe reset"""
        now = time.perf_counter()
        if (self.last is None) or (self.last + self.seconds >= now):
            self.last = now
            return True
        return False
