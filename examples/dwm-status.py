import re
import time
from subprocess import run

import ltstatus.monitor as m

sound_aliases = {
    "iFi (by AMR) HD USB Audio Pro": "ifi",
    "apm.zero": "apm",
    "Dummy Output": "none",
}

with (
    m.spotify() as spotify,
    m.process_alerts(flags={"steam": re.compile(r".*steam.*")}) as alerts,
    m.redshift() as redshift,
    m.bluetooth() as bluetooth,
    m.sound(sound_aliases) as sound,
    m.datetime() as datetime,
):
    while True:
        time.sleep(1)
        segments = [spotify(), alerts(), redshift(), bluetooth(), sound(), datetime()]
        segments = [s for s in segments if s != ""]
        run(
            args=[
                "xsetroot",
                "-name",
                " | ".join(segments),
            ],
            check=True,
        )
        # print(" | ".join(segments), flush=True)
