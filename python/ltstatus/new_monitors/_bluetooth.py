from dataclasses import dataclass
from subprocess import CalledProcessError

from ..alternative import RealtimeContext, RealtimeMonitor
from ..tools import NewTailCommand, StopByCloseStdin, run_cmd


@dataclass
class Monitor(RealtimeMonitor):
    name: str = "bluetooth"

    # TODO dbus notifications could be another solution
    # TODO could think about sending None when there is not bluetooth hardware (and exit the thread (?))

    def run(self, context: RealtimeContext):

        context.send(self.get_state())

        while not context.should_exit():
            with NewTailCommand(args=["bluetoothctl"],stop=StopByCloseStdin()) as tail:
                while not context.should_exit():
                    if tail.returncode() is not None:
                        # TODO is that true? does bluetoothctl fail? what's missing? X is not needed for bluetooth
                        # sometimes early in the x-session bluetoothctl fails, we wait a bit and then retry
                        state = "bt..."
                        context.send(state)
                        context.sleep(1)
                        break
                    if not tail.wait_for_chatter(timeout=1):
                        continue
                    context.send(self.get_state())

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
            return "bt ?"
