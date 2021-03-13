import re
from dataclasses import dataclass
from typing import Dict

from ltstatus import State, ThreadedMonitor
from ltstatus.tools import TailCommand, ffield, run_cmd

re_sink_event = re.compile(r"Event '.+' on sink #\d+")
re_default_sink = re.compile(r" +\* index: \d+\n(?P<default_sink>(\t.+\n)+)")
re_volume = re.compile(r"\tvolume: .*: \d+ / +(?P<volume>\d+%)")
re_muted = re.compile(r"\tmuted: (?P<muted>no|yes)")
re_name = re.compile(r"\tdevice\.description = \"(?P<name>.*)\"")


@dataclass
class Monitor(ThreadedMonitor):
    name: str = "sound"
    aliases: Dict[str, str] = ffield(dict)

    def run(self):

        last_content = self.get_content()
        self.queue.put(State.from_one(self.name, last_content))

        with TailCommand.as_context("pactl subscribe") as log:
            while not self.exit.is_set():
                events = log.get_some_lines()
                sink_event = any(re_sink_event.fullmatch(e) for e in events)
                if sink_event:
                    content = self.get_content()
                    if content != last_content:
                        self.queue.put(State.from_one(self.name, content))
                        last_content = content

    def get_content(self):

        sinks = run_cmd("pacmd list-sinks")

        try:
            sink = re_default_sink.search(sinks)["default_sink"]
            volume = re_volume.search(sink)["volume"]
            muted = re_muted.search(sink)["muted"] == "yes"
            name = re_name.search(sink)["name"]
        except TypeError:
            return "?"

        sign = "#" if muted else "="
        name = self.aliases.get(name, name)
        content = f"{name}{sign}{volume}"

        return content
