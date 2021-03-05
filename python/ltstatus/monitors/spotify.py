from dataclasses import dataclass
from subprocess import CalledProcessError

from ltstatus import CallbackMonitor, State
from ltstatus.tools import run_cmd


@dataclass
class Monitor(CallbackMonitor):
    name: str = "spotify"

    def get_updates(self):

        try:
            # TODO will not work without DISPLAY variable
            window_id = run_cmd("xdotool search --onlyvisible --class spotify").strip()
            content = run_cmd(f"xdotool getwindowname {window_id}").strip()
        except CalledProcessError:
            content = None
        return State.from_one(self.name, content)
