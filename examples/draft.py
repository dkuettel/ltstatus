import time

from ltstatus.monitors.bluetooth import monitor_bluetooth
from ltstatus.monitors.cpu import monitor_cpu
from ltstatus.monitors.datetime import monitor_datetime
from ltstatus.monitors.nvidia import monitor_nvidia
from ltstatus.monitors.redshift import monitor_redshift
from ltstatus.monitors.sound import monitor_sound

sound_aliases = {
    "iFi (by AMR) HD USB Audio Pro": "ifi",
    "apm.zero": "apm",
    "Dummy Output": "none",
}

with (
    monitor_cpu() as cpu,
    monitor_nvidia() as nvidia,
    monitor_bluetooth() as bluetooth,
    monitor_sound(sound_aliases) as sound,
    monitor_redshift() as redshift,
    monitor_datetime() as datetime,
):
    while True:
        time.sleep(1)
        print(
            f"{cpu()} | {nvidia()} | {bluetooth()} | {sound()} | {redshift()} | {datetime()}",
            flush=True,
        )
