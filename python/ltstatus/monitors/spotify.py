from dataclasses import dataclass
from typing import Optional

from jeepney import DBusAddress, MatchRule, MessageType, Properties, message_bus
from jeepney.io.blocking import open_dbus_connection

from ltstatus import State, ThreadedMonitor


@dataclass
class Monitor(ThreadedMonitor):
    name: str = "spotify"
    running: Optional[bool] = None
    playing: Optional[bool] = None
    artist: Optional[str] = None
    title: Optional[str] = None

    def run(self):
        try:
            con = open_dbus_connection()

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

            self.ask_for_state(con)
            last_update = self.get_update()
            self.queue.put(last_update)

            while not self.exit.is_set():

                # note: spotify usually sends the same message 3 or 6 times
                message = con.receive()

                if rule_properties.matches(message):
                    self.read_properties_message(message)
                elif rule_owners.matches(message):
                    self.read_owners_message(message)
                else:
                    raise Exception(f"unknown message: {message}")

                update = self.get_update()
                if update != last_update:
                    self.queue.put(update)
                    last_update = update

        finally:
            con.close()

    def get_update(self) -> Optional[State]:
        if self.running is None:
            return None
        if not self.running:
            return State.from_one(self.name, None)
        if None in {self.artist, self.playing, self.title}:
            return State.from_one(self.name, "spotify starting")
        return State.from_one(
            self.name,
            f"{self.artist} {'-' if self.playing else '#'} {self.title}",
        )

    def ask_for_state(self, con):

        properties = Properties(
            obj=DBusAddress(
                "/org/mpris/MediaPlayer2",
                "org.mpris.MediaPlayer2.spotify",
                "org.mpris.MediaPlayer2.Player",
            ),
        )

        reply = con.send_and_get_reply(properties.get("PlaybackStatus"))
        if reply.header.message_type == MessageType.method_return:
            self.running = True
            self.playing = reply.body[0][1] == "Playing"

            reply = con.send_and_get_reply(properties.get("Metadata"))
            self.artist = ",".join(reply.body[0][1]["xesam:artist"][1])
            self.title = reply.body[0][1]["xesam:title"][1]

        else:
            self.running = False

    def read_properties_message(self, message):

        # I dont know how to filter for signals from spotify only
        # I think there should be a away to do it fith MatchRule above in self.run
        # but it didnt work for me
        # firefox and other media stuff also sends similar PropertiesChanged messages
        # spotify contains PlaybackStatus and Metadata in the same message
        # plus it obviously has spotify trackids, I use this as an ad-hoc filter

        if "PlaybackStatus" not in message.body[1]:
            return
        if "Metadata" not in message.body[1]:
            return
        if "spotify:track:" not in message.body[1]["Metadata"][1]["mpris:trackid"][1]:
            return

        self.playing = message.body[1]["PlaybackStatus"][1] == "Playing"
        self.artist = ",".join(message.body[1]["Metadata"][1]["xesam:artist"][1])
        self.title = message.body[1]["Metadata"][1]["xesam:title"][1]

    def read_owners_message(self, message):
        name, _, new = message.body
        if name == "org.mpris.MediaPlayer2.spotify" and new != "":
            self.running = True
        elif name == "org.mpris.MediaPlayer2.spotify" and new == "":
            self.running = False
            self.playing = None
            self.artist = None
            self.title = None
