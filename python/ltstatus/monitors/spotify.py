from dataclasses import dataclass

from jeepney import DBusAddress, MatchRule, MessageType, Properties
from jeepney.bus_messages import DBus
from jeepney.io.blocking import open_dbus_connection

from ltstatus import State, ThreadedMonitor


@dataclass
class Monitor(ThreadedMonitor):
    name: str = "spotify"

    def run(self):
        try:
            con = open_dbus_connection()

            dbus = DBus()
            rule = MatchRule(
                type="signal",
                interface="org.freedesktop.DBus.Properties",
                member="PropertiesChanged",
                path="/org/mpris/MediaPlayer2",
            )
            con.send(dbus.AddMatch(rule))

            properties = Properties(
                obj=DBusAddress(
                    "/org/mpris/MediaPlayer2",
                    "org.mpris.MediaPlayer2.spotify",
                    "org.mpris.MediaPlayer2.Player",
                ),
            )

            reply = con.send_and_get_reply(properties.get("PlaybackStatus"))
            if reply.header.message_type == MessageType.method_return:
                sign = "-" if reply.body[0][1] == "Playing" else "#"

                reply = con.send_and_get_reply(properties.get("Metadata"))
                artist = ",".join(reply.body[0][1]["xesam:artist"][1])
                title = reply.body[0][1]["xesam:title"][1]

                last_content = f"{artist} {sign} {title}"

            else:
                # probably no spotify running right now
                last_content = None

            self.queue.put(State.from_one(self.name, last_content))

            while not self.exit.is_set():
                event = con.receive()
                # TODO could check even.header for better filtering, signal type or other stuff
                if (
                    len(event.body) > 0
                    and event.body[0] == "org.mpris.MediaPlayer2.Player"
                ):
                    # note spotify seems to spam quite a lot of message for a single change
                    # play/pause -> 3 messages
                    # next -> 6 messages
                    # in case they are not all already showing the final state, we might want to wait with sending an update
                    sign = (
                        "-" if event.body[1]["PlaybackStatus"][1] == "Playing" else "#"
                    )
                    artist = ",".join(event.body[1]["Metadata"][1]["xesam:artist"][1])
                    title = event.body[1]["Metadata"][1]["xesam:title"][1]
                    content = f"{artist} {sign} {title}"
                    if content != last_content:
                        self.queue.put(State.from_one(self.name, content))
                        last_content = content

                    # TODO we dont check for messages when spotify exits, and keep on showing the last state

        finally:
            con.close()
