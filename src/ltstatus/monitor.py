from ltstatus.monitors.bluetooth import monitor as bluetooth
from ltstatus.monitors.cpu import monitor as cpu
from ltstatus.monitors.datetime import monitor as datetime
from ltstatus.monitors.diskspace_alerts import monitor as diskspace_alerts
from ltstatus.monitors.nvidia import monitor as nvidia
from ltstatus.monitors.process_alerts import monitor as process_alerts
from ltstatus.monitors.redshift import monitor as redshift
from ltstatus.monitors.sound import monitor as sound
from ltstatus.monitors.spotify import monitor as spotify
from ltstatus.monitors.top import monitor as top

__all__ = [
    "bluetooth",
    "cpu",
    "datetime",
    "diskspace_alerts",
    "nvidia",
    "process_alerts",
    "redshift",
    "sound",
    "spotify",
    "top",
]
