from __future__ import annotations

from dataclasses import dataclass

from .core import Format, State


@dataclass
class Segments(Format):
    prefix: str = ""
    postfix: str = ""
    separator: str = ", "
    waiting: str = ""  # alternatives: ..., , …
    head: str = ""
    tail: str = ""

    def apply(self, state: State) -> str:
        decorated = (
            f"{self.prefix}{self.waiting if value is None else value}{self.postfix}"
            for value in state.values()
            if value != ""
        )
        return self.head + self.separator.join(decorated) + self.tail


def plain() -> Format:
    return Segments()


def tmux() -> Format:
    return Segments(prefix="[", postfix="]", separator=" ")


def dwm() -> Format:
    return Segments(prefix="", postfix="", separator=" | ", head=" ", tail=" ")
