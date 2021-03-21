from contextlib import contextmanager
from dataclasses import dataclass
from io import FileIO
from pathlib import Path
from socket import AF_UNIX, SOCK_STREAM, socket as new_socket

from ltstatus import State, ThreadedMonitor
from ltstatus.tools import ffield


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

    def is_idle(self) -> bool:
        self.stream.write("get_dropbox_status\ndone\n")
        self.stream.flush()

        idle = False
        for l in self.stream:
            if l == "done\n":
                break
            idle |= l == "status\tUp to date\n"

        return idle


# TODO threaded now but not really realtime yet
@dataclass
class Monitor(ThreadedMonitor):
    name: str = "dropbox"
    interval: float = 10.0
    command_socket: Path = ffield(lambda: Path("~/.dropbox/command_socket"))

    def run(self):
        try:
            with DropboxClient.as_context(command_socket=self.command_socket) as dc:
                while not self.exit.is_set():
                    content = "❖" if dc.is_idle() else "⇄"
                    self.queue.put({self.name: content})
                    self.exit.wait(self.interval)
        except FileNotFoundError:
            self.queue.put(State.from_one(self.name, None))
        except ConnectionRefusedError:
            self.queue.put(State.from_one(self.name, "?"))
