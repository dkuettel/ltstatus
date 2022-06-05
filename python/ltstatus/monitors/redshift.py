import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from ltstatus import RealtimeContext, RealtimeMonitor
from ltstatus.tools import ffield, tail_file


@dataclass
class RedshiftState:
    # true=enabled
    status: Optional[bool] = None
    # "day-ness": 1.0=day, 0.0=night, in-between=in-transition
    period: Optional[float] = None
    # temperature in kelvin
    temperature: Optional[int] = None
    brightness: Optional[float] = None


def format_brightness(state: RedshiftState) -> str:
    """shows like 'redshift@0.75'"""
    if None in {state.status, state.brightness}:
        return "redshift@???"
    if not state.status:
        return "redshift off"
    return f"redshift@{state.brightness:.2f}"


def format_temperature(state: RedshiftState) -> str:
    """shows like 'redshift@4500K'"""
    if None in {state.status, state.temperature}:
        return "redshift@???"
    if not state.status:
        return "redshift off"
    return f"redshift@{state.temperature}K"


def format_period(state: RedshiftState) -> str:
    """shows like 'redshift day' -> 'redshift 78% day' -> 'redshift night'"""
    if None in {state.status, state.period}:
        return "redshift@???"
    if not state.status:
        return "redshift off"
    if state.period == 1.0:
        return "redshift day"
    if state.period == 0.0:
        return "redshift night"
    return f"redshift {round(state.period*100)}% day"


@dataclass
class Monitor(RealtimeMonitor):
    name: str = "redshift"
    log_file: Path = ffield(lambda: Path("~/.log-redshift"))
    format: Callable = format_period

    def run(self, context: RealtimeContext):

        parsers = [
            StatusParser(),
            PeriodParser(),
            TemperatureParser(),
            BrightnessParser(),
        ]

        state = RedshiftState()

        while not context.should_exit():
            with tail_file(self.log_file.expanduser()) as log:
                while not context.should_exit():
                    if log.returncode() is not None:
                        context.send("reshift@!!!")
                        context.sleep(1)
                        break
                    lines = list(log.get_some_lines(timeout=1))
                    if len(lines) == 0:
                        continue
                    for line in lines:
                        for p in parsers:
                            p.update_from_line(state=state, line=line)
                    context.send(self.format(state))


@dataclass
class Parser:
    pattern: re.Pattern

    def update_from_line(self, state: RedshiftState, line: str):
        match = self.pattern.fullmatch(line)
        if match:
            self.update_from_match(state, match)

    def update_from_match(self, state: RedshiftState, match: re.Match):
        raise NotImplementedError()


@dataclass
class StatusParser(Parser):
    pattern: re.Pattern = re.compile(r".*Status: (?P<status>Enabled|Disabled)")

    def update_from_match(self, state, match):
        state.status = match["status"] == "Enabled"


@dataclass
class PeriodParser(Parser):
    pattern: re.Pattern = re.compile(
        r".*Period: (?P<period>Daytime|Night|Transition \((?P<percentage>[0-9.]+)% day\))"
    )

    def update_from_match(self, state, match):
        if match["period"] == "Daytime":
            state.period = 1.0
        elif match["period"] == "Night":
            state.period = 0.0
        else:
            state.period = float(match["percentage"]) / 100


@dataclass
class TemperatureParser(Parser):
    pattern: re.Pattern = re.compile(r".*Color temperature: (?P<temperature>\d+)K")

    def update_from_match(self, state, match):
        state.temperature = int(match["temperature"])


@dataclass
class BrightnessParser(Parser):
    pattern: re.Pattern = re.compile(r".*Brightness: (?P<brightness>[0-9.]+)")

    def update_from_match(self, state, match):
        state.brightness = float(match["brightness"])
