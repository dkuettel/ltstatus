from dataclasses import dataclass
from subprocess import CalledProcessError

from ltstatus import CallbackMonitor
from ltstatus.tools import run_cmd


@dataclass
class Monitor(CallbackMonitor):
    name: str = "bluetooth"

    def get_updates(self):

        try:
            # pylint: disable=unsupported-membership-test
            if "Powered: yes" in run_cmd("bluetoothctl show"):
                macs = [
                    line.split(" ")[1]
                    for line in run_cmd("bluetoothctl devices").split("\n")[:-1]
                ]
                count = sum(
                    "Connected: yes" in run_cmd(["bluetoothctl", "info", mac])
                    for mac in macs
                )
                content = f"bt@{count}"

            else:
                content = "bt off"

        except CalledProcessError:
            content = "?"
        return {self.name: content}
