from __future__ import annotations

import signal
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import Iterator, Optional, Union


def run_cmd(cmd: Union[str, list[str]]) -> str:

    if type(cmd) is str:
        args = cmd.split(" ")
    elif type(cmd) is list:
        args = cmd
    else:
        assert False, type(cmd)

    return str(
        subprocess.run(args=args, capture_output=True, text=True, check=True).stdout
    )


class StopTailCommand(ABC):
    @abstractmethod
    def request(self, process: subprocess.Popen):
        pass


class StopByCloseStdin(StopTailCommand):
    """This is like ctrl-d."""

    def request(self, process: subprocess.Popen):
        assert process.stdin is not None
        process.stdin.close()


class StopBySigInt(StopTailCommand):
    """This is like ctrl-c."""

    def request(self, process: subprocess.Popen):
        process.send_signal(signal.SIGINT)
        # note: process.returncode will be negative signal integer


@dataclass
class TailCommand:
    args: list[str]
    stop: StopTailCommand
    line_buffer_size: int = 1000

    def returncode(self) -> Optional[int]:
        return self.process.poll()

    def wait_for_chatter(self, timeout: Optional[float] = None) -> bool:
        # TODO this is not robust with timeout=None and an failed or exited process
        # ideally then it will return False
        try:
            self.queue.get(timeout=timeout)
        except Empty:
            return False
        try:
            for _ in range(1000):
                self.queue.get_nowait()
        except Empty:
            pass
        return True

    def get_some_lines(self, timeout: Optional[float] = None) -> Iterator[str]:
        # TODO this is not robust with timeout=None and an failed or exited process
        # ideally then the Iterator will exit
        try:
            yield self.queue.get(timeout=timeout)
            while True:
                yield self.queue.get_nowait()
        except Empty:
            pass

    def __enter__(self) -> TailCommand:
        self.queue = Queue(maxsize=self.line_buffer_size)
        self.process = subprocess.Popen(
            args=self.args,
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.thread = Thread(target=self._tail)
        self.thread.start()
        return self

    def __exit__(self, *_) -> bool:
        self.stop.request(self.process)
        while self.process.poll() is None and self.thread.is_alive():
            self._flush_queue()
            self.process.wait(0.1)
            self.thread.join(0.1)
        return False

    def _tail(self):
        # TODO what about stderr?
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self.queue.put(line.rstrip("\n"))

    def _flush_queue(self):
        try:
            for _ in range(1000):
                self.queue.get_nowait()
        except Empty:
            pass


def tail_file(path: Union[str, Path]):
    """tail lines of a file as it grows, non-blocking thru a queue"""
    return TailCommand(
        args=[
            "tail",
            "--lines=+0",
            "-F",
            str(path),
        ],
        stop=StopBySigInt(),
    )
