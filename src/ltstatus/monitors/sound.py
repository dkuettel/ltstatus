from __future__ import annotations

import re
import selectors
import subprocess
import threading
from contextlib import contextmanager
from typing import assert_never

from ltstatus.monitors.bluetooth import run_cmd


def trigger_events(event: threading.Event, stop: threading.Event):
    # TODO we could even cache the last state if there was no change event?

    with (
        subprocess.Popen(
            args=["pactl", "subscribe"], stdout=subprocess.PIPE, text=True
        ) as process,
        selectors.DefaultSelector() as selector,
    ):
        assert process.stdout is not None
        selector.register(process.stdout, selectors.EVENT_READ, None)
        while not stop.is_set():
            if selector.select(1):  # wait
                while selector.select(0.01):  # read all that is ready
                    # NOTE the state check in monitor actually causes events too, and that would cause a feedback loop
                    # it seems sufficient to just look at "change" events
                    if process.stdout.readline().startswith("Event 'change'"):
                        event.set()


@contextmanager
def monitor(event: threading.Event, aliases: dict[str, str] | None = None):
    if aliases is None:
        aliases = dict()

    re_default_sink = re.compile(r"^Default Sink: (?P<value>.+)$", re.MULTILINE)
    re_name = re.compile(r"^\tName: (?P<value>.+)$", re.MULTILINE)
    re_description = re.compile(r"^\tDescription: (?P<value>.+)$", re.MULTILINE)
    re_mute = re.compile(r"\tMute: (?P<value>.+)$", re.MULTILINE)
    re_volume = re.compile(r"\tVolume: .* (?P<value>\d+)% .*$", re.MULTILINE)

    def fn() -> str:
        """
        we use only 'pactl', and not 'pacmd'
        for people that use PipeWire to replace pulseaudio
        'pactl' still works, but 'pacmd' doesnt
        """

        # NOTE we dont react kindly to anything that we cant parse

        match re_default_sink.search(run_cmd(["pactl", "info"])):
            case re.Match() as m:
                default_sink = m["value"]
            case None:
                return "sound unknown1"
            case _ as never:
                assert_never(never)

        sinks = run_cmd(["pactl", "list", "sinks"])

        for name in re_name.finditer(sinks):
            if name["value"] == default_sink:
                name, pos = name["value"], name.end()
                break
        else:
            return "sound unknown2"

        match re_description.search(sinks, pos):
            case re.Match() as m:
                description, pos = m["value"], m.end()
            case None:
                return "sound unknown3"
            case _ as never:
                assert_never(never)

        match re_mute.search(sinks, pos):
            case re.Match() as m:
                mute, pos = m["value"] == "yes", m.end()
            case None:
                return "sound unknown4"
            case _ as never:
                assert_never(never)

        match re_volume.search(sinks, pos):
            case re.Match() as m:
                volume, pos = int(m["value"]), m.end()
            case None:
                return "sound unknown5"
            case _ as never:
                assert_never(never)

        # show nothing if we are in the happy state
        if (description in aliases) and (not mute) and (volume == 100):
            return ""

        description = aliases.get(description, description)

        if mute:
            return f"{description}@mute"
        return f"{description}@{volume}%"

    stop = threading.Event()

    thread = threading.Thread(target=trigger_events, args=(event, stop))
    thread.start()

    try:
        yield fn
    finally:
        stop.set()
        thread.join()
