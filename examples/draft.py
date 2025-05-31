import time

from ltstatus.monitors.cpu import monitor_cpu
from ltstatus.monitors.nvidia import monitor_nvidia

with (
    monitor_cpu() as cpu,
    monitor_nvidia() as nvidia,
):
    while True:
        time.sleep(1)
        print(f"{cpu()} {nvidia()}", flush=True)
