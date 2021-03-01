from dataclasses import dataclass
from subprocess import PIPE, CalledProcessError, Popen

from ltstatus import CallbackMonitor, ThreadedMonitor
from ltstatus.tools import run_cmd


@dataclass
class PollingMonitor(CallbackMonitor):
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


@dataclass
class Monitor(ThreadedMonitor):
    name: str = "bluetooth"

    # TODO gdbus works easy, or try pure python?
    # anyway check when at desktop if notification also comes in for connections, not just for power
    # or can I monitor a property that counts connected devices?
    # > dbus-monitor
    # > gdbus monitor --system --dest org.bluez
    # https://pypi.org/project/bluezero/
    # https://stackoverflow.com/questions/11544836/monitoring-dbus-messages-by-python

    def run(self):
        # TODO this is a cheap (but low-cpu) realtime version
        # we simply check when bluetoothctl announces a change, and then call the original callback for a full state
        # in theory the output of bluetoothctl directly informs us, could also parse that and incrementally track the state
        p = Popen(
            args=["bluetoothctl"],
            text=True,
            stdout=PIPE,
            stderr=PIPE,
        )
        monitor = PollingMonitor(name=self.name)
        self.queue.put(monitor.get_updates())
        while not self.exit.is_set():
            p.stdout.readline()
            self.queue.put(monitor.get_updates())
