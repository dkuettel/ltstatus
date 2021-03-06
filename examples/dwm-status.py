#!bin/run-ltstatus

from ltstatus import RateLimitedMonitors, RegularGroupMonitor, XsetrootStatus, monitors

monitor = RateLimitedMonitors(
    monitors=[
        monitors.datetime.Monitor(),
        monitors.redshift.Monitor(),
        monitors.bluetooth.Monitor(),
        RegularGroupMonitor(
            monitors=[
                monitors.spotify.Monitor(),
                monitors.sound.Monitor(),
            ],
        ),
    ],
)

status = XsetrootStatus(
    monitor=monitor,
    order=[
        "spotify",
        "redshift",
        "bluetooth",
        "sound",
        "datetime",
    ],
)

status.run()
