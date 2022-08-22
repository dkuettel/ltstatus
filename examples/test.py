#!/usr/bin/env ltstatus
from pathlib import Path

from ltstatus import formats, monitors as m, outputs, run

# switch this off if you dont have nerdfont or something compatible
# (see https://www.nerdfonts.com/)
icons = True

if icons:
    sound_aliases = {
        "iFi (by AMR) HD USB Audio Pro": "ﰝ",
        "apm.zero": "",
        "Dummy Output": "",
    }
else:
    sound_aliases = {
        "iFi (by AMR) HD USB Audio Pro": "ifi",
        "apm.zero": "apm",
        "Dummy Output": "x",
    }


monitors = [
    m.Spotify(),
    m.Redshift(),
    m.Bluetooth(),
    m.Sound(aliases=sound_aliases),
    m.Dropbox(ignored_patterns=[r"\w+\.osh"]),
    m.DiskspaceAlerts(
        limits={
            Path("/var/lib/docker"): 2.0,
            Path("/"): 10.0,
            Path("~"): 5.0,
        },
    ),
    m.Cores(),
    m.Cpu(),
    m.Nvidia(),
    m.Datetime(),
    m.ProcessAlerts(flags={"steam": r".*steam.*"}),
]

if icons:
    monitors = [m.with_icons() for m in monitors]

run(
    monitors=monitors,
    polling_interval=1,
    format=formats.tmux_with_icons() if icons else formats.tmux(),
    output=outputs.stdout(),
)
