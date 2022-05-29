#!ltstatus

from ltstatus import formats, monitors as m, outputs, run

process_alerts = m.process_alerts(flags={"steam": r".*steam.*"})

sound = m.sound(
    aliases={
        "Starship/Matisse HD Audio Controller Analog Stereo": "speakers",
        "Starship/Matisse HD Audio Controller Pro": "speakers",
        "iFi (by AMR) HD USB Audio Pro": "ifi",
    },
)

run(
    monitors=[
        m.spotify(),
        process_alerts,
        m.redshift(format=m._redshift.format_period),
        m.bluetooth(),
        sound,
        m.datetime(),
    ],
    polling_interval=3,
    format=formats.dwm(),
    output=outputs.dwm(),
)
