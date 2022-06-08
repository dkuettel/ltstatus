#!/usr/bin/env ltstatus

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
    m.ProcessAlerts(flags={"steam": r".*steam.*"}),
    m.Redshift(),
    m.Bluetooth(),
    m.Sound(aliases=sound_aliases),
    m.Datetime(),
]

if icons:
    monitors = [m.with_icons() for m in monitors]

run(
    monitors=monitors,
    polling_interval=3,
    format=formats.dwm(),
    output=outputs.dwm(),
)
