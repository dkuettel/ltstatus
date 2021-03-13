from dataclasses import dataclass
from subprocess import CalledProcessError

from ltstatus import State, ThreadedMonitor
from ltstatus.tools import TailCommand, TailCommandExited, TailCommandFailed, run_cmd


@dataclass
class Monitor(ThreadedMonitor):
    name: str = "bluetooth"

    # TODO dbus notifications could be another solution

    def run(self):

        last_content = self.get_content()
        self.queue.put(State.from_one(self.name, last_content))

        while not self.exit.is_set():
            try:
                with TailCommand.as_context(args="bluetoothctl") as log:
                    while not self.exit.is_set():
                        # chatter on bluetoothctl means changes
                        list(log.get_some_lines())
                        content = self.get_content()
                        if content != last_content:
                            self.queue.put(State.from_one(self.name, content))
                            last_content = content
            except (TailCommandExited, TailCommandFailed):
                # sometimes early in the x-session bluetoothctl fails, we wait a bit and then retry
                self.exit.wait(1)

    def get_content(self):

        try:
            enabled = "Powered: yes" in run_cmd("bluetoothctl show")
            if enabled:
                devices = [
                    entry.split(" ")[1]
                    for entry in run_cmd("bluetoothctl devices").split("\n")[:-1]
                    # output: lines of "Device XX:XX:XX:XX:XX:XX some device name", with a trailing empty line
                ]
                connected = sum(
                    "Connected: yes" in run_cmd(f"bluetoothctl info {device}")
                    for device in devices
                )
                return f"bt@{connected}"
            else:
                return "bt off"

        except CalledProcessError:
            return "?"
