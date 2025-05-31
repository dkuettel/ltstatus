from ltstatus.monitors.bluetooth import monitor as bluetooth
from ltstatus.monitors.cpu import monitor as cpu
from ltstatus.monitors.datetime import monitor as datetime
from ltstatus.monitors.nvidia import monitor as nvidia
from ltstatus.monitors.redshift import monitor as redshift
from ltstatus.monitors.sound import monitor as sound

__all__ = [
    "bluetooth",
    "cpu",
    "datetime",
    "nvidia",
    "redshift",
    "sound",
]
