import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import typer

import ltstatus.monitor as m

limits_gb = {
    Path("/var/lib/docker"): 2.0,
    Path("/"): 10.0,
    Path("~"): 5.0,
}

sound_aliases = {
    "iFi (by AMR) HD USB Audio Pro": "ifi",
    "apm.zero": "apm",
    "Dummy Output": "none",
    "MacBook Pro J314 Speakers": "speakers",
}

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode=None,
)


@app.command("run")
def app_run(path: Path):
    exe = sys.executable
    assert exe is not None and exe != "", exe
    os.execl(exe, exe, path)


@app.command("all")
def app_all():
    event = threading.Event()
    with (
        m.diskspace_alerts(limits_gb) as alerts,
        m.top() as top,
        m.cpu() as cpu,
        m.nvidia() as nvidia,
        m.spotify(event) as spotify,
        m.process_alerts(flags={"steam": re.compile(r".*steam.*")}) as alerts,
        m.redshift(event) as redshift,
        m.bluetooth() as bluetooth,
        m.sound(event, sound_aliases) as sound,
        m.datetime() as datetime,
    ):
        while True:
            event.wait(2)
            event.clear()
            segments = [
                alerts(),
                top(),
                cpu(),
                nvidia(),
                spotify(),
                alerts(),
                redshift(),
                bluetooth(),
                sound(),
                datetime(),
            ]
            segments = [s for s in segments if s != ""]
            print(" | ".join(segments), flush=True)


@app.command("tmux")
def app_tmux():
    with (
        m.cpu() as cpu,
        m.nvidia() as nvidia,
        m.diskpie() as diskpie,
    ):
        while True:
            print(
                f"󰬊 {cpu()}󰯾 {nvidia()}{diskpie()[:-1]}",
                flush=True,
            )
            time.sleep(1)


@app.command("tmux2")
def app_tmux2():
    with (
        m.diskspace_alerts(limits_gb) as alerts,
        m.top() as top,
    ):
        while True:
            match alerts():
                case "":
                    print(f"#[fg=red]{top()}", flush=True)
                case _ as a:
                    print(f"#[fg=red]{a}", flush=True)
            time.sleep(1)


@app.command("dwm")
def app_dwm(test: bool = False):
    event = threading.Event()
    try:
        with (
            m.spotify(event) as spotify,
            m.process_alerts(flags={"steam": re.compile(r".*steam.*")}) as alerts,
            m.redshift(event) as redshift,
            m.bluetooth() as bluetooth,
            m.sound(event, sound_aliases) as sound,
            m.datetime() as datetime,
            m.cpu() as cpu,
            m.nvidia() as nvidia,
            m.diskpie() as diskpie,
        ):
            while True:
                segments = [
                    spotify(),
                    alerts(),
                    f"󰬊 {cpu()}󰯾 {nvidia()}{diskpie()[:-1]}",
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
                            " " + " | ".join(segments) + " ",
                        ],
                        check=True,
                    )
                event.wait(1)
                event.clear()
    finally:
        subprocess.run(
            args=[
                "xsetroot",
                "-name",
                "exited",
            ],
            check=True,
        )
