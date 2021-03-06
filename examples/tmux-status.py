#!bin/run-ltstatus

""" tmux example

1) write your own tmux-status.py file similar to this file
   note: tmux does not update the status more than 1/sec no matter what

2) add it to the tmux configuration, some possibilities are:

   a) set-option -g status-right ' #(run-ltstatus path/to/tmux-status.py) '
      and make sure ltstatus is in the path, or type out the full path

   b) set-option -g status-right ' #(path/to/tmux-status.py) '
      and make tmux-status.py executable
      by using a hashbang #!run-ltstatus or similar

   bin/run-ltstatus makes sure you run it in the correct virtual env
   but you can take care of that yourself and then do without run-ltstatus

"""

from ltstatus import RateLimitedMonitors, RegularGroupMonitor, StdoutStatus, monitors

monitor = RateLimitedMonitors(
    rate=1,
    monitors=[
        monitors.nvidia.Monitor(),
        monitors.dropbox.Monitor(),
        RegularGroupMonitor(
            interval=1,
            monitors=[
                monitors.cpu.Monitor(),
                monitors.diskspace_alerts.Monitor(),
            ],
        ),
    ],
)

status = StdoutStatus(
    monitor=monitor,
    order=[
        "diskspace-alerts",
        "dropbox",
        "cpu",
        "nvidia",
    ],
)

status.run()
