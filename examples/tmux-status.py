import time
from pathlib import Path

import ltstatus.monitor as m

limits_gb = {
    Path("/var/lib/docker"): 2.0,
    Path("/"): 10.0,
    Path("~"): 5.0,
}

with (
    m.diskspace_alerts(limits_gb) as alerts,
    m.cpu() as cpu,
    m.nvidia() as nvidia,
):
    while True:
        time.sleep(1)
        match alerts():
            case "":
                print(
                    f"cpu({cpu()}) gpu({nvidia()})",
                    flush=True,
                )
            case _ as a:
                print(a, flush=True)
