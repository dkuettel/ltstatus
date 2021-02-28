import re
from dataclasses import dataclass
from pathlib import Path
from subprocess import PIPE, Popen

from ltstatus import ThreadedMonitor
from ltstatus.tools import ffield


@dataclass
class Monitor(ThreadedMonitor):
    name: str = "redshift"
    log_file: Path = ffield(lambda: Path("~/.log-redshift"))

    def run(self):

        # TODO can be a context manager, better to shutdown?
        # --lines makes sure we go thru the file from the beginning, but what happens when the log file gets replaced?
        # disable-inotify makes it slower, i guess it's polling, not very nice
        # but now I think we will fail if the log file gets recreated
        # maybe could do direct inotify here with python, no subprocess
        p = Popen(
            args=[
                "tail",
                "--lines=+0",
                "-F",
                # "---disable-inotify",
                str(self.log_file.expanduser()),
            ],
            text=True,
            stdout=PIPE,
            stderr=PIPE,
        )

        status = None
        brightness = None

        re_parse = re.compile(
            r".*Status: (?P<status>Enabled|Disabled)|.*Brightness: (?P<brightness>[0-9.]+)"
        )

        # TODO ExitEvent
        # for line in p.stdout:
        while not self.exit.is_set():
            line = p.stdout.readline()
            match = re_parse.match(line)
            if match is None:
                continue
            if match["status"] is not None:
                status = match["status"] == "Enabled"
            if match["brightness"] is not None:
                brightness = match["brightness"]
            if status is None:
                content = "redshift ???"
            elif status:
                if brightness is None:
                    content = "redshift@???"
                else:
                    content = f"redshift@{brightness}"
            else:
                content = "redshift off"
            self.queue.put({self.name: content})
