import re
from dataclasses import dataclass, field

from ltstatus import RealtimeContext, RealtimeMonitor
from ltstatus.tools import StopBySigInt, TailCommand, run_cmd

re_sink_event = re.compile(r"Event '.+' on sink #\d+")

re_default_sink = re.compile(r"^Default Sink: (?P<value>.+)$", re.MULTILINE)
re_name = re.compile(r"^\tName: (?P<value>.+)$", re.MULTILINE)
re_description = re.compile(r"^\tDescription: (?P<value>.+)$", re.MULTILINE)
re_mute = re.compile(r"\tMute: (?P<value>.+)$", re.MULTILINE)
re_volume = re.compile(r"\tVolume: .* (?P<value>\d+)% .*$", re.MULTILINE)


@dataclass
class Monitor(RealtimeMonitor):
    name: str = "sound"
    aliases: dict[str, str] = field(default_factory=dict)

    def run(self, context: RealtimeContext):

        context.send(self.get_state())

        with TailCommand(args=["pactl", "subscribe"], stop=StopBySigInt()) as log:
            while not context.should_exit():
                if log.returncode() is not None:
                    context.send("pactl failed")
                    break
                events = list(log.get_some_lines(timeout=1))
                if len(events) == 0:
                    continue
                sink_event = any(re_sink_event.fullmatch(e) for e in events)
                if not sink_event:
                    continue
                context.send(self.get_state())

    def get_state(self) -> str:
        """
        we use only 'pactl', and not 'pacmd'
        for people that use PipeWire to replace pulseaudio
        'pactl' still works, but 'pacmd' doesnt
        """

        # NOTE we dont react kindly to anything that we cant parse

        default_sink = re_default_sink.search(run_cmd("pactl info"))["value"]

        sinks = run_cmd("pactl list sinks")

        for name in re_name.finditer(sinks):
            if name["value"] == default_sink:
                break
        name, pos = name["value"], name.end()

        description = re_description.search(sinks, pos)
        description, pos = description["value"], description.end()

        mute = re_mute.search(sinks, pos)
        mute, pos = mute["value"] == "yes", mute.end()

        volume = re_volume.search(sinks, pos)
        volume, pos = int(volume["value"]), volume.end()

        sign = "#" if mute else "="
        description = self.aliases.get(description, description)
        content = f"{description}{sign}{volume}%"

        return content
