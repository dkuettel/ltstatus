#!ltstatus
from pathlib import Path

from ltstatus import formats, monitors as m, outputs, run

sound = m.Sound(
    aliases={
        "Starship/Matisse HD Audio Controller Analog Stereo": "speakers",
        "Starship/Matisse HD Audio Controller Pro": "speakers",
        "iFi (by AMR) HD USB Audio Pro": "ifi",
    },
)

diskspace_alerts = m.DiskspaceAlerts(
    limits={
        Path("/var/lib/docker"): 2.0,
        Path("/"): 10.0,
        Path("~"): 5.0,
    },
)

process_alerts = m.ProcessAlerts(flags={"steam": r".*steam.*"})

run(
    monitors=[
        m.Spotify(),
        m.Redshift(format=m.redshift.format_period),
        m.Bluetooth(),
        sound,
        m.Dropbox(),
        diskspace_alerts,
        m.Cpu(),
        m.Nvidia(),
        m.Datetime(),
        process_alerts,
    ],
    polling_interval=1,
    format=formats.tmux(),
    output=outputs.stdout(),
)
