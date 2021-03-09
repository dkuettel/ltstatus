import subprocess
from contextlib import contextmanager
from dataclasses import field
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import Iterable, List, Union


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


@contextmanager
def tail_file(path: Union[str, Path], buffered_lines: int = 1000) -> Queue:
    """ tail lines of a file as it grows, non-blocking thru a queue """

    with subprocess.Popen(
        args=[
            "tail",
            "--lines=+0",
            "-F",
            str(path),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as tail:

        queue = Queue(maxsize=buffered_lines)

        def run():
            for line in tail.stdout:
                queue.put(line.rstrip("\n"))

        thread = Thread(target=run, daemon=True)
        thread.start()

        yield queue

    # TODO clean up? run exits when process stdout cant be read? or exit event and join?
    thread.join()


def iter_available_from_queue(queue: Queue) -> Iterable:
    """ wait for at least one element and then return all additional elements that are ready before the iterator stops """
    # TODO what happens to us when the receiver of the yield raises an exception?
    yield queue.get()
    try:
        while True:
            yield queue.get_nowait()
    except Empty:
        pass
