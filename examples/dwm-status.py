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
        RegularGroupMonitor(
            interval=2,
            monitors=[
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

status = XsetrootStatus(
    monitor=monitor,
    order=[
        "spotify",
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
