from __future__ import annotations

import signal
import subprocess
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import Iterable, Iterator, List, Optional, Union


def ffield(factory):
    return field(default_factory=factory)


def run_cmd(cmd: Union[str, List[str]]) -> str:

    if type(cmd) is str:
        args = cmd.split(" ")
    elif type(cmd) is list:
        args = cmd
    else:
        assert False, type(cmd)

    return str(
        subprocess.run(args=args, capture_output=True, text=True, check=True).stdout
    )


def iter_available_from_queue(queue: Queue) -> Iterable:
    """wait for at least one element and then return all additional elements that are ready before the iterator stops"""
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
    """
    Neither subprocess nor file-like objects offer a way to read with a timeout.
    Usually we need TailCommand inside a RealtimeMonitor,
    where we need to check if we should exit.
    This can then be stuck in waiting for output from a tail command.
    That's why it's a separate thread that puts it in a queue.
    A queue can be read with timeout.
    And the queue and the command are stopped from outside.
    This then also terminates the helper thread.
    With async we could get around this.
    """

    process: subprocess.Popen
    queue: Queue

    def get_some_lines(self) -> Iterable[str]:
        """get as many lines as are available right now, but wait for at least one line"""
        for line in iter_available_from_queue(self.queue):
            if type(line) is str:
                yield line
                continue
            assert type(line) is int
            if line == 0:
                # TODO that should be normal, just stop the iterator?
                raise TailCommandExited()
            raise TailCommandFailed(self)

    def run(self):
        try:
            # TODO what about stderr?
            assert self.process.stdout is not None
            for line in self.process.stdout:
                self.queue.put(line.rstrip("\n"))
        finally:
            code = self.process.wait()
            self.queue.put(code)

    @classmethod
    @contextmanager
    def as_context(cls, args: Union[str, List[str]], buffer: int = 1000):

        if type(args) is str:
            args = args.split(" ")
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
class NewTailCommand:
    args: list[str]
    stop: StopTailCommand
    line_buffer_size: int = 1000

    def returncode(self) -> Optional[int]:
        return self.process.poll()

    def wait_for_chatter(self, timeout: Optional[float] = None) -> bool:
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
        try:
            yield self.queue.get(timeout=timeout)
            while True:
                yield self.queue.get_nowait()
        except Empty:
            pass

    def __enter__(self) -> NewTailCommand:
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
    return NewTailCommand(
        args=[
            "tail",
            "--lines=+0",
            "-F",
            str(path),
        ],
        stop=StopBySigInt(),
    )
