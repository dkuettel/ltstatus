from __future__ import annotations

import time
from dataclasses import dataclass


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
