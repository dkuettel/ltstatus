from ltstatus import RateLimitedMonitors, RegularGroupMonitor, StdoutStatus, monitors

monitor = RateLimitedMonitors(
    monitors=[
        monitors.nvidia.Monitor(),
        monitors.datetime.Monitor(),
        monitors.redshift.Monitor(),
        monitors.dropbox.Monitor(),
        monitors.bluetooth.Monitor(),
        RegularGroupMonitor(
            monitors=[
                monitors.cpu.Monitor(),
                monitors.diskspace_alerts.Monitor(),
                monitors.spotify.Monitor(),
                monitors.sound.Monitor(),
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
