from __future__ import annotations

import subprocess
from contextlib import contextmanager
from subprocess import CalledProcessError


def run_cmd(args: list[str]) -> str:
    return subprocess.run(args=args, capture_output=True, text=True, check=True).stdout


@contextmanager
def monitor():
    # TODO maybe cache a bit more and dont do it every one second?
    def fn() -> str:
        try:
            enabled = "Powered: yes" in run_cmd(["bluetoothctl", "show"])
            if enabled:
                devices = [
                    entry.split(" ")[1]
                    for entry in run_cmd(["bluetoothctl", "devices"]).split("\n")[:-1]
                    # output: lines of "Device XX:XX:XX:XX:XX:XX some device name", with a trailing empty line
                ]
                connected = sum(
                    "Connected: yes" in run_cmd(["bluetoothctl", "info", f"{device}"])
                    for device in devices
                )
                return f"bt@{connected}"
            else:
                return ""

        except CalledProcessError:
            return "bt@err"

    yield fn
