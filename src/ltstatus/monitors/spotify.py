from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

from jeepney import DBusAddress, MatchRule, MessageType, Properties, message_bus
from jeepney.io.blocking import open_dbus_connection


def format_plain(state: None | SpotifyState) -> str:
    if state is None:
        return ""
    return f"{state.artist} {'-' if state.playing else '#'} {state.title}"


@dataclass
class SpotifyState:
    playing: bool
    artist: str
    title: str


class SpotifyBus:
    def __enter__(self) -> SpotifyBus:
        self.con = open_dbus_connection()
        rule_properties_changed = MatchRule(
            type="signal",
            interface="org.freedesktop.DBus.Properties",
            member="PropertiesChanged",
            path="/org/mpris/MediaPlayer2",
        )
        self.con.send(message_bus.AddMatch(rule_properties_changed))
        rule_owner_changed = MatchRule(
            type="signal",
            sender="org.freedesktop.DBus",
            interface="org.freedesktop.DBus",
            member="NameOwnerChanged",
            path="/org/freedesktop/DBus",
        )
        self.con.send(message_bus.AddMatch(rule_owner_changed))
        return self

    def __exit__(self, *_) -> bool:
        self.con.close()
        del self.con
        return False

    def wait_for_chatter(self, timeout: None | float = None) -> bool:
        try:
            self.con.receive(timeout=timeout)
            return True
        except TimeoutError:
            # jeepney.io.threading.ReceiveStopped can also happen
            return False

    def get_state(self) -> None | SpotifyState:
        properties = Properties(
            obj=DBusAddress(
                "/org/mpris/MediaPlayer2",
                "org.mpris.MediaPlayer2.spotify",
                "org.mpris.MediaPlayer2.Player",
            ),
        )

        playback_status = self.con.send_and_get_reply(properties.get("PlaybackStatus"))
        metadata = self.con.send_and_get_reply(properties.get("Metadata"))

        if {playback_status.header.message_type, metadata.header.message_type} != {
            MessageType.method_return
        }:
            return None

        return SpotifyState(
            playing=playback_status.body[0][1] == "Playing",
            artist=",".join(metadata.body[0][1]["xesam:artist"][1]) or "?",
            title=metadata.body[0][1]["xesam:title"][1] or "?",
        )


@contextmanager
def monitor():
    with SpotifyBus() as bus:

        def fn() -> str:
            return format_plain(bus.get_state())

        yield fn
