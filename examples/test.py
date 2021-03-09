#!bin/ltstatus
from pathlib import Path

from ltstatus import RateLimitedMonitors, RegularGroupMonitor, StdoutStatus, monitors

monitor = RateLimitedMonitors(
    monitors=[
        monitors.nvidia.Monitor(),
        monitors.datetime.Monitor(),
        monitors.redshift.Monitor(
            format=monitors.redshift.format_period,
        ),
        monitors.dropbox.Monitor(),
        monitors.bluetooth.Monitor(),
        RegularGroupMonitor(
            monitors=[
                monitors.cpu.Monitor(),
                monitors.diskspace_alerts.Monitor(
                    limits={
                        Path("/var/lib/docker"): 2.0,
                        Path("/"): 10.0,
                        Path("~"): 5.0,
                    },
                ),
                monitors.spotify.Monitor(),
                monitors.sound.Monitor(
                    aliases={
                        "Starship/Matisse HD Audio Controller Analog Stereo": "speakers",
                    },
                ),
            ],
        ),
    ],
)

status = StdoutStatus(
    monitor=monitor,
    order=[
        "spotify",
        "redshift",
        "bluetooth",
        "sound",
        "dropbox",
        "diskspace-alerts",
        "cpu",
        "nvidia",
        "datetime",
    ],
)

status.run()
