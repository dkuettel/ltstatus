from __future__ import annotations

from .core import Output
from .tools import run_cmd


class Print(Output):
    def push(self, status: str):
        print(status, flush=True)


def stdout() -> Output:
    return Print()


class Xsetroot(Output):
    def push(self, status: str):
        run_cmd(["xsetroot", "-name", status])


def dwm() -> Output:
    return Xsetroot()
