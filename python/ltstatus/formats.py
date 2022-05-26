from __future__ import annotations

from dataclasses import dataclass

from .core import Format, State


@dataclass
class Segments(Format):
    prefix: str = ""
    postfix: str = ""
    separator: str = ", "
    waiting: str = ""  # alternatives: ..., , …

    def apply(self, state: State) -> str:
        decorated = (
            f"{self.prefix}{self.waiting if value is None else value}{self.postfix}"
            for value in state.values()
            if value != ""
        )
        return self.separator.join(decorated)


def plain() -> Format:
    return Segments()


def tmux() -> Format:
    return Segments(prefix="[", postfix="]", separator=" ")


def dwm() -> Format:
    return Segments(prefix="", postfix="", separator=" | ")
