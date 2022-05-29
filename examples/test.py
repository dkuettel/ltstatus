#!ltstatus
from pathlib import Path

from ltstatus import formats, monitors as m, outputs, run

sound = m.sound(
    aliases={
        "Starship/Matisse HD Audio Controller Analog Stereo": "speakers",
        "Starship/Matisse HD Audio Controller Pro": "speakers",
        "iFi (by AMR) HD USB Audio Pro": "ifi",
    },
)

diskspace_alerts = m.diskspace_alerts(
    limits={
        Path("/var/lib/docker"): 2.0,
        Path("/"): 10.0,
        Path("~"): 5.0,
    },
)

process_alerts = m.process_alerts(flags={"steam": r".*steam.*"})

run(
    monitors=[
        m.spotify(),
        m.redshift(format=m._redshift.format_period),
        m.bluetooth(),
        m.sound(
            aliases={"Starship/Matisse HD Audio Controller Analog Stereo": "speakers"}
        ),
        m.dropbox(),
        diskspace_alerts,
        m.cpu(),
        m.nvidia(),
        m.datetime(),
        process_alerts,
    ],
    polling_interval=1,
    format=formats.tmux(),
    output=outputs.stdout(),
)
