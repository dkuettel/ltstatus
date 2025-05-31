import re
import subprocess
import time
from pathlib import Path

import typer

import ltstatus.monitor as m

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode=None,
)


@app.command("tmux")
def app_tmux():
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


@app.command("dwm")
def app_dwm(test: bool = False):
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
            segments = [
                spotify(),
                alerts(),
                redshift(),
                bluetooth(),
                sound(),
                datetime(),
            ]
            segments = [s for s in segments if s != ""]
            if test:
                print(" | ".join(segments), flush=True)
            else:
                subprocess.run(
                    args=[
                        "xsetroot",
                        "-name",
                        " | ".join(segments),
                    ],
                    check=True,
                )


if __name__ == "__main__":
    app()
