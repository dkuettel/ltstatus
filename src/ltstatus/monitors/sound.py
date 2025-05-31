from __future__ import annotations

import re
from contextlib import contextmanager

from ltstatus.monitors.bluetooth import run_cmd

re_sink_event = re.compile(r"Event '.+' on sink #\d+")

re_default_sink = re.compile(r"^Default Sink: (?P<value>.+)$", re.MULTILINE)
re_name = re.compile(r"^\tName: (?P<value>.+)$", re.MULTILINE)
re_description = re.compile(r"^\tDescription: (?P<value>.+)$", re.MULTILINE)
re_mute = re.compile(r"\tMute: (?P<value>.+)$", re.MULTILINE)
re_volume = re.compile(r"\tVolume: .* (?P<value>\d+)% .*$", re.MULTILINE)


def format_plain(description: str, mute: bool, volume: int) -> str:
    sign = "#" if mute else "="
    return f"{description}{sign}{volume}%"


def format_icons(description: str, mute: bool, volume: int) -> str:
    speaker = "󰝟" if mute else ""
    return f"{description} {speaker} {volume}%"


@contextmanager
def monitor(aliases: dict[str, str] | None = None):
    if aliases is None:
        aliases = dict()

    def fn() -> str:
        """
        we use only 'pactl', and not 'pacmd'
        for people that use PipeWire to replace pulseaudio
        'pactl' still works, but 'pacmd' doesnt
        """

        # NOTE we dont react kindly to anything that we cant parse

        default_sink = re_default_sink.search(run_cmd(["pactl", "info"]))["value"]

        sinks = run_cmd(["pactl", "list", "sinks"])

        for name in re_name.finditer(sinks):
            if name["value"] == default_sink:
                break
        name, pos = name["value"], name.end()

        description = re_description.search(sinks, pos)
        description, pos = description["value"], description.end()

        mute = re_mute.search(sinks, pos)
        mute, pos = mute["value"] == "yes", mute.end()

        volume = re_volume.search(sinks, pos)
        volume, pos = int(volume["value"]), volume.end()

        description = aliases.get(description, description)

        if mute:
            return f"{description}@mute"
        return f"{description}@{volume}%"

    yield fn
