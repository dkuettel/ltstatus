#!bin/ltstatus

from ltstatus import (
    RateLimitedMonitors,
    RegularGroupMonitor,
    StdoutStatus,
    XsetrootStatus,
    monitors,
)

monitor = RateLimitedMonitors(
    rate=30,
    monitors=[
        monitors.datetime.Monitor(),
        monitors.redshift.Monitor(
            # format=monitors.redshift.format_brightness,
            # format=monitors.redshift.format_temperature,
            format=monitors.redshift.format_period,
        ),
        monitors.bluetooth.Monitor(),
        monitors.sound.Monitor(
            aliases={
                "Starship/Matisse HD Audio Controller Analog Stereo": "speakers",
                "Starship/Matisse HD Audio Controller Pro": "speakers",
                "iFi (by AMR) HD USB Audio Pro": "ifi",
            },
        ),
        monitors.spotify.Monitor(),
        RegularGroupMonitor(
            interval=3,
            monitors=[
                monitors.process_alerts.Monitor(flags={"steam": r".*steam.*"}),
            ],
        ),
    ],
)

status = XsetrootStatus(
    monitor=monitor,
    order=[
        "spotify",
        "process-alerts",
        "redshift",
        "bluetooth",
        "sound",
        "datetime",
    ],
    separator="|",
    prefix=" ",
    postfix=" ",
    waiting="...",
)

status.run()
