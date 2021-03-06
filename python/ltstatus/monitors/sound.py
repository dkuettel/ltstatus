import re
from dataclasses import dataclass
from typing import Dict

from ltstatus import CallbackMonitor, State
from ltstatus.tools import ffield, run_cmd

re_sound = re.compile(
    r"""\* index: \d+
(.*?\n)*?\tvolume: .* (?P<volume>\d+%) .*
(.*?\n)*?\tmuted: (?P<muted>no|yes)
(.*?\n)*?\t\tdevice.description = \"(?P<name>.*)\"
"""
)


@dataclass
class Monitor(CallbackMonitor):
    name: str = "sound"
    aliases: Dict[str, str] = ffield(dict)

    def get_updates(self):

        match = re_sound.search(run_cmd("pacmd list-sinks"))
        if match is None:
            content = "?"
        else:
            sign = "=" if match["muted"] == "no" else "#"
            name = match["name"]
            name = self.aliases.get(name, name)
            content = f"{name}{sign}{match['volume']}"
        return State.from_one(self.name, content)
