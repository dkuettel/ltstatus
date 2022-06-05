#!ltstatus

from ltstatus import formats, monitors as m, outputs, run

process_alerts = m.ProcessAlerts(flags={"steam": r".*steam.*"})

sound = m.Sound(
    aliases={
        "Starship/Matisse HD Audio Controller Analog Stereo": "speakers",
        "Starship/Matisse HD Audio Controller Pro": "speakers",
        "iFi (by AMR) HD USB Audio Pro": "ifi",
    },
)

run(
    monitors=[
        m.Spotify(),
        process_alerts,
        m.Redshift(format=m.redshift.format_period),
        m.Bluetooth(),
        sound,
        m.Datetime(),
    ],
    polling_interval=3,
    format=formats.dwm(),
    output=outputs.dwm(),
)
