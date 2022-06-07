from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from socket import AF_UNIX, SOCK_STREAM, socket as new_socket
from typing import Iterator

from ltstatus import PollingMonitor


@dataclass
class Monitor(PollingMonitor):
    name: str = "dropbox"
    command_socket: Path = Path("~/.dropbox/command_socket")
    idle: str = "dbox"
    sync: str = "sync"
    missing: str = "db??"
    error: str = "db!!"

    def with_icons(self) -> Monitor:
        self.idle = ""
        self.sync = ""
        self.missing = ""
        self.error = ""
        return self

    def updates(self) -> Iterator[str]:
        while True:
            try:
                yield from self.connected_updates()
            except FileNotFoundError:
                yield self.missing
            except ConnectionRefusedError:
                yield self.error

    def connected_updates(self) -> Iterator[str]:
        with DropboxClient(self.command_socket) as c:
            while True:
                yield self.idle if c.is_idle() else self.sync


@dataclass
class DropboxClient:
    """Small reverse-engineered specification based on their own cli client:

    The protocol is text and line based, not binary.
    Request = r"request\ndone\n"
    Reply = r"ok\nvalue\tvalue\t...\ndone\n"; always ok + done, values depends on request
    The command socket is not closed and can be reused.

    For the request "get_dropbox_status\ndone\n" these are the replies:
        2 or more entries.
        Entry 1 is always "status"
        Entry 2 is high-level, seems like an overall state:
            "Up to date"
            "Syncing..."
            "Syncing 4 files"
            "Syncing "file-d"
            "Syncing "file-d" • 1 sec"
            "Syncing 2 files • 2 secs"
            "Syncing 4 files"
        Other entries are low-level, seems like currently running tasks:
            "Uploading "file-d"..."
            "Uploading 2 files..."
            "Uploading 2 files (25,711 KB/sec, 1 sec)"
            "Indexing 5 files..."
            "Downloading "file-b"..."
            "Downloading "file-b" (18,818 KB/sec, 1 sec)"

    Unfortunately so far I didnt find a way to subscribe. We can only poll.
    Also the dropbox daemon in systemd doesnt give log messages.
    I could not find a verbose switch.
    Otherwise we could subscribe to the systemd log messages.
    """

    command_socket: Path = Path("~/.dropbox/command_socket")

    def __enter__(self) -> DropboxClient:
        self.socket = new_socket(AF_UNIX, SOCK_STREAM)
        self.socket.connect(str(self.command_socket.expanduser()))
        self.stream = self.socket.makefile("rw")
        return self

    def __exit__(self, *_) -> bool:
        self.stream.close()
        self.socket.close()
        del self.stream, self.socket
        return False

    def is_idle(self) -> bool:
        self.stream.write("get_dropbox_status\ndone\n")
        self.stream.flush()

        assert self.stream.readline().rstrip("\n") == "ok"
        replies = self.stream.readline().rstrip("\n").split("\t")
        assert self.stream.readline().rstrip("\n") == "done"

        assert len(replies) >= 2
        assert replies[0] == "status"

        return replies[1] == "Up to date"
