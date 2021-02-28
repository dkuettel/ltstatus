import subprocess
from dataclasses import field
from typing import List, Union


def ffield(factory):
    return field(default_factory=factory)


def run_cmd(cmd: Union[str, List[str]]) -> str:

    if type(cmd) is str:
        args = cmd.split(" ")
    elif type(cmd) is list:
        args = cmd
    else:
        assert False, type(cmd)

    return subprocess.run(args=args, capture_output=True, text=True, check=True).stdout
