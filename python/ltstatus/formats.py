from __future__ import annotations

from dataclasses import dataclass

from .core import Format, State


@dataclass
class Segments(Format):
    prefix: str = ""
    postfix: str = ""
    separator: str = ", "
    # TODO again need to consider if we allow None in the state, but not in updates?
    # or yes in updates? would allow to at least last-effort let the user know, or timeout
    # if for long no update
    waiting: str = "..."

    def apply(self, state: State) -> str:
        # TODO not using waiting yet for None values
        decorated = (f"{self.prefix}{value}{self.postfix}" for value in state.values())
        return self.separator.join(decorated)


def plain() -> Format:
    return Segments()


def tmux() -> Format:
    return Segments(prefix="[", postfix="]", separator=" ")


def dwm() -> Format:
    return Segments(prefix="", postfix="", separator=" | ")
