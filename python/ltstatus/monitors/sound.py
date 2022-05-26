import re
from dataclasses import dataclass
from typing import Dict

from ltstatus import State, ThreadedMonitor
from ltstatus.tools import TailCommand, ffield, run_cmd

re_sink_event = re.compile(r"Event '.+' on sink #\d+")

re_default_sink = re.compile(r"^Default Sink: (?P<value>.+)$", re.MULTILINE)
re_name = re.compile(r"^\tName: (?P<value>.+)$", re.MULTILINE)
re_description = re.compile(r"^\tDescription: (?P<value>.+)$", re.MULTILINE)
re_mute = re.compile(r"\tMute: (?P<value>.+)$", re.MULTILINE)
re_volume = re.compile(r"\tVolume: .* (?P<value>\d+)% .*$", re.MULTILINE)


@dataclass
class Monitor(ThreadedMonitor):
    name: str = "sound"
    aliases: Dict[str, str] = ffield(dict)

    def run(self):

        last_content = self.get_content()
        self.queue.put(State.from_one(self.name, last_content))

        with TailCommand.as_context("pactl subscribe") as log:
            while not self.exit.is_set():
                # TODO can be stuck forever :/
                events = log.get_some_lines()
                sink_event = any(re_sink_event.fullmatch(e) for e in events)
                if sink_event:
                    content = self.get_content()
                    if content != last_content:
                        self.queue.put(State.from_one(self.name, content))
                        last_content = content

    def get_content(self):
        """
        we use only 'pactl', and not 'pacmd'
        for people that use PipeWire to replace pulseaudio
        'pactl' still works, but 'pacmd' doesnt
        """

        # NOTE we dont react kindly to anything that we cant parse

        default_sink = re_default_sink.search(run_cmd("pactl info"))["value"]

        sinks = run_cmd("pactl list sinks")

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

        sign = "#" if mute else "="
        description = self.aliases.get(description, description)
        content = f"{description}{sign}{volume}%"

        return content
