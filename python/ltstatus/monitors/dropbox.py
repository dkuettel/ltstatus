import re
from contextlib import contextmanager
from dataclasses import dataclass
from io import FileIO
from pathlib import Path
from socket import AF_UNIX, SOCK_STREAM, socket as new_socket

from ltstatus import State, ThreadedMonitor
from ltstatus.tools import ffield

pattern_1file = re.compile(r'(Syncing|Indexing|Uploading) ".[^"]".*')
pattern_files = re.compile(r"(Syncing|Indexing|Uploading) (?P<count>\d+) files.*")
pattern_done = re.compile(r"Up to date")


@dataclass
class DropboxClient:
    stream: FileIO

    @classmethod
    @contextmanager
    def as_context(cls, command_socket: Path):

        command_socket = command_socket.expanduser()

        socket = new_socket(AF_UNIX, SOCK_STREAM)
        socket.connect(str(command_socket))
        stream = socket.makefile("rw")

        try:
            yield cls(stream=stream)

        finally:
            stream.close()
            socket.close()

    def get_status(self) -> bool:

        # the protocol is:
        # send request newline, done newline
        # then receive ok newline, reply tab-separated values newline, done newline
        # the socket stream is not closed and can be reused

        self.stream.write("get_dropbox_status\ndone\n")
        self.stream.flush()

        assert self.stream.readline().rstrip("\n") == "ok"
        messages = self.stream.readline().rstrip("\n").split("\t")
        assert self.stream.readline().rstrip("\n") == "done"

        idle = False
        count = 0

        for message in messages:
            if pattern_done.fullmatch(message):
                idle = True
            if pattern_1file.fullmatch(message):
                count = max(count, 1)
            if m := pattern_files.fullmatch(message):
                count = max(count, int(m["count"]))

        return idle, count


# TODO threaded now but not realtime, the dropbox control socket does not support notifications
@dataclass
class Monitor(ThreadedMonitor):
    name: str = "dropbox"
    interval: float = 1.0
    command_socket: Path = ffield(lambda: Path("~/.dropbox/command_socket"))

    def run(self):
        try:
            with DropboxClient.as_context(command_socket=self.command_socket) as dc:
                while not self.exit.is_set():
                    idle, count = dc.get_status()
                    if idle:
                        content = "dbox"
                    else:
                        content = f"db{count:02d}"
                    self.queue.put({self.name: content})
                    self.exit.wait(self.interval)
        except FileNotFoundError:
            self.queue.put(State.from_one(self.name, None))
        except ConnectionRefusedError:
            self.queue.put(State.from_one(self.name, "?"))
