from __future__ import annotations

import time
from contextlib import contextmanager


@contextmanager
def monitor():
    def fn() -> str:
        return time.strftime(r"%Y-%m-%d %a %H:%M", time.localtime())

    yield fn
