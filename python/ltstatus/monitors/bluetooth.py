from __future__ import annotations

from dataclasses import dataclass
from subprocess import CalledProcessError

from ltstatus import RealtimeContext, RealtimeMonitor
from ltstatus.tools import StopByCloseStdin, TailCommand, run_cmd


@dataclass
class Monitor(RealtimeMonitor):
    name: str = "bluetooth"
    waiting: str = "bt..."
    on: str = "bt@"
    off: str = "bt off"
    error: str = "bt?!"

    def with_icons(self) -> Monitor:
        self.waiting = "󰂲"
        self.on = ""
        self.off = "󰂲"
        self.error = "󰂲"
        return self

    # TODO dbus notifications could be another solution
    # TODO could think about sending "" when there is not bluetooth hardware (and exit the thread?)

    def run(self, context: RealtimeContext):

        context.send(self.get_state())

        # TODO overall, in many places with threads, if they fail we are just stuck with the last update
        # should we in the wrapper check the final exception and mark the state?
        # if we return cleanly we should set it to None? or back to missing?

        while not context.should_exit():
            with TailCommand(args=["bluetoothctl"], stop=StopByCloseStdin()) as tail:
                while not context.should_exit():
                    if tail.returncode() is not None:
                        # TODO is that true? does bluetoothctl fail? what's missing? X is not needed for bluetooth
                        # sometimes early in the x-session bluetoothctl fails, we wait a bit and then retry
                        context.send(self.waiting)
                        context.sleep(1)
                        break
                    if not tail.wait_for_chatter(timeout=1):
                        continue
                    context.send(self.get_state())

    def get_state(self) -> str:

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
                return self.on + str(connected)
            else:
                return self.off

        except CalledProcessError:
            return self.error
