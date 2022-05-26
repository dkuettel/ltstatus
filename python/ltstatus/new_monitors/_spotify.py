from dataclasses import dataclass
from typing import Optional

from jeepney import DBusAddress, MatchRule, MessageType, Properties, message_bus
from jeepney.io.blocking import open_dbus_connection

from ..alternative import RealtimeContext, RealtimeMonitor


@dataclass
class Monitor(RealtimeMonitor):
    name: str = "spotify"

    def run(self, context: RealtimeContext):
        last_update = None
        for state in watch_and_generate_spotify_states(timeout=1):
            if context.should_exit():
                return
            context.send(state.as_update())


@dataclass
class SpotifyState:
    # TODO what should be the default values
    running: Optional[bool] = None
    playing: Optional[bool] = None
    artist: Optional[str] = None
    title: Optional[str] = None

    # TODO too verbose? let's see how we do the defaults
    @classmethod
    def from_running(cls):
        return cls(running=True)

    @classmethod
    def from_not_running(cls):
        return cls(running=False)

    def as_update(self) -> Optional[str]:
        if self.running is None:
            return "?"
        if not self.running:
            return None
        if None in {self.artist, self.playing, self.title}:
            return "spotify starting"
        return f"{self.artist} {'-' if self.playing else '#'} {self.title}"

    def is_full_state(self) -> bool:
        return self.running == True and None not in {
            self.artist,
            self.playing,
            self.title,
        }


def watch_and_generate_spotify_states(timeout: Optional[float]):
    with open_dbus_connection() as con:

        rule_properties = MatchRule(
            type="signal",
            interface="org.freedesktop.DBus.Properties",
            member="PropertiesChanged",
            path="/org/mpris/MediaPlayer2",
        )
        con.send(message_bus.AddMatch(rule_properties))

        rule_owners = MatchRule(
            type="signal",
            sender="org.freedesktop.DBus",
            interface="org.freedesktop.DBus",
            member="NameOwnerChanged",
            path="/org/freedesktop/DBus",
        )
        con.send(message_bus.AddMatch(rule_owners))

        state = ask_dbus_for_full_state(con)
        _timeout = 0

        should_get_full_state = False

        while True:
            if should_get_full_state:
                state = ask_dbus_for_full_state(con)
                should_get_full_state = not state.is_full_state()
            try:
                message = con.receive(timeout=_timeout)
                _timeout = 0
                # jeepney.io.threading.ReceiveStopped can also happen
            except TimeoutError:
                yield state
                _timeout = timeout
                continue
            if rule_properties.matches(message):
                state = update_state_from_properties_message(message, state)
                continue
            if rule_owners.matches(message):
                state, should_get_full_state = update_state_from_owners_message(
                    message, state
                )
                continue


def ask_dbus_for_full_state(con) -> SpotifyState:

    properties = Properties(
        obj=DBusAddress(
            "/org/mpris/MediaPlayer2",
            "org.mpris.MediaPlayer2.spotify",
            "org.mpris.MediaPlayer2.Player",
        ),
    )

    playback_status = con.send_and_get_reply(properties.get("PlaybackStatus"))
    metadata = con.send_and_get_reply(properties.get("Metadata"))

    if {playback_status.header.message_type, metadata.header.message_type} != {
        MessageType.method_return
    }:
        return SpotifyState.from_not_running()

    return SpotifyState(
        running=True,
        playing=playback_status.body[0][1] == "Playing",
        artist=",".join(metadata.body[0][1]["xesam:artist"][1]) or None,
        title=metadata.body[0][1]["xesam:title"][1] or None,
    )


# TODO seems like this also gets messages from chrome playing stuff, and maybe vlc and things
# how can we make sure we use only spotify messages?
def update_state_from_properties_message(message, state: SpotifyState) -> SpotifyState:

    try:
        state.playing = message.body[1]["PlaybackStatus"][1] == "Playing"
    except:
        pass

    try:
        state.artist = (
            ",".join(message.body[1]["Metadata"][1]["xesam:artist"][1]) or None
        )
    except:
        pass

    try:
        state.title = message.body[1]["Metadata"][1]["xesam:title"][1] or None
    except:
        pass

    return state


def update_state_from_owners_message(
    message, state: SpotifyState
) -> tuple[SpotifyState, bool]:
    """return new state and if it's advisable to get a full state from dbus"""
    name, _, new = message.body
    if name == "org.mpris.MediaPlayer2.spotify" and new != "":
        return SpotifyState.from_running(), True
    if name == "org.mpris.MediaPlayer2.spotify" and new == "":
        return SpotifyState.from_not_running(), False
    return state, False


def debug():
    for state in watch_and_generate_spotify_states(timeout=None):
        print(state)


if __name__ == "__main__":
    debug()
