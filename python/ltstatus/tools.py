import subprocess
from contextlib import contextmanager
from dataclasses import dataclass, field
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


def iter_available_from_queue(queue: Queue) -> Iterable:
    """ wait for at least one element and then return all additional elements that are ready before the iterator stops """
    # TODO what happens to us when the receiver of the yield raises an exception?
    yield queue.get()
    try:
        while True:
            yield queue.get_nowait()
    except Empty:
        pass


class TailCommandExited(Exception):
    pass


class TailCommandFailed(Exception):
    def __init__(self, tail_command):
        self.tail_command = tail_command
        super().__init__()


@dataclass
class TailCommand:
    process: subprocess.Popen
    queue: Queue

    def get_some_lines(self) -> Iterable[str]:
        """ get as many lines as are available right now, but wait for at least one line """
        for line in iter_available_from_queue(self.queue):
            if type(line) is str:
                yield line
                continue
            assert type(line) is int
            if line == 0:
                raise TailCommandExited()
            raise TailCommandFailed(self)

    def run(self):
        try:
            for line in self.process.stdout:
                self.queue.put(line.rstrip("\n"))
        finally:
            code = self.process.wait()
            self.queue.put(code)

    @classmethod
    @contextmanager
    def as_context(cls, args: Union[str, List[str]], buffer: int = 1000):

        if type(args) is str:
            args = [args]
        assert type(args) is list

        queue = Queue(maxsize=buffer)

        with subprocess.Popen(
            args=args,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as process:
            context = cls(process=process, queue=queue)

            thread = Thread(target=context.run, daemon=True)
            thread.start()

            yield context

        thread.join()


def tail_file(path: Union[str, Path]):
    """ tail lines of a file as it grows, non-blocking thru a queue """
    return TailCommand.as_context(
        args=[
            "tail",
            "--lines=+0",
            "-F",
            str(path),
        ]
    )
