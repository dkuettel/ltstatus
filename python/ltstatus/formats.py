from __future__ import annotations

from dataclasses import dataclass

from .core import Format, State


@dataclass
class Segments(Format):
    prefix: str = ""
    postfix: str = ""
    separator: str = ", "

    def apply(self, state: State) -> str:
        decorated = (
            f"{self.prefix}{value}{self.postfix}"
            for value in state.values()
            if value is not None
        )
        return self.separator.join(decorated)


def plain() -> Format:
    return Segments()


def tmux() -> Format:
    return Segments(prefix="[", postfix="]", separator=" ")


def dwm() -> Format:
    return Segments(prefix="", postfix="", separator=" | ")
