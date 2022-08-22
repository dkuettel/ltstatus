#!/usr/bin/env ltstatus
from pathlib import Path

from ltstatus import formats, monitors as m, outputs, run

# switch this off if you dont have nerdfont or something compatible
# (see https://www.nerdfonts.com/)
icons = True

monitors = [
    m.DiskspaceAlerts(
        limits={
            Path("/var/lib/docker"): 2.0,
            Path("/"): 10.0,
            Path("~"): 5.0,
        },
    ),
    m.Dropbox(ignored_patterns=[r"\w+\.osh"]),
    m.Cores(),
    m.Cpu(),
    m.Nvidia(),
]

if icons:
    monitors = [m.with_icons() for m in monitors]

run(
    monitors=monitors,
    # NOTE tmux as of around version 3.3 does not update more often than once a second
    polling_interval=1,
    format=formats.tmux_with_icons() if icons else formats.tmux(),
    output=outputs.stdout(),
)
