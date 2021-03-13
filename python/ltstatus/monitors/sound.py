import re
from dataclasses import dataclass
from typing import Dict

from ltstatus import CallbackMonitor, State
from ltstatus.tools import ffield, run_cmd

re_default_sink = re.compile(r" +\* index: \d+\n(?P<default_sink>(\t.+\n)+)")
re_volume = re.compile(r"\tvolume: .*: \d+ / +(?P<volume>\d+%)")
re_muted = re.compile(r"\tmuted: (?P<muted>no|yes)")
re_name = re.compile(r"\tdevice\.description = \"(?P<name>.*)\"")


@dataclass
class Monitor(CallbackMonitor):
    name: str = "sound"
    aliases: Dict[str, str] = ffield(dict)

    def get_updates(self):

        sinks = run_cmd("pacmd list-sinks")

        try:
            sink = re_default_sink.search(sinks)["default_sink"]
            volume = re_volume.search(sink)["volume"]
            muted = re_muted.search(sink)["muted"] == "yes"
            name = re_name.search(sink)["name"]
        except TypeError:
            return State.from_one(self.name, "?")

        sign = "#" if muted else "="
        name = self.aliases.get(name, name)
        content = f"{name}{sign}{volume}"

        return State.from_one(self.name, content)
