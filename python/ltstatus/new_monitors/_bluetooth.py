from dataclasses import dataclass
from subprocess import CalledProcessError

from ..alternative import RealtimeContext, RealtimeMonitor
from ..tools import TailCommand, TailCommandExited, TailCommandFailed, run_cmd


@dataclass
class Monitor(RealtimeMonitor):
    name: str = "bluetooth"

    # TODO dbus notifications could be another solution

    def run(self, context: RealtimeContext):

        state = self.get_state()
        context.send(state)

        while not context.should_exit():
            try:
                with TailCommand.as_context(args="bluetoothctl") as log:
                    while not context.should_exit():
                        # chatter on bluetoothctl means changes
                        # TODO I think we can be stuck here :/
                        list(log.get_some_lines())
                        # TODO how to abstract this? context.send could be smart?
                        if state != (state := self.get_state()):
                            context.send(state)
            except (TailCommandExited, TailCommandFailed):
                # sometimes early in the x-session bluetoothctl fails, we wait a bit and then retry
                state = "bt..."
                context.send(state)
                context.sleep(1)

    def get_state(self):

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
