from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import psutil

from ltstatus import RealtimeContext, RealtimeMonitor
from ltstatus.indicators import HistogramIndicator, RatioIndicator, bin_themes
from ltstatus.tools import ffield


@dataclass
class Monitor(RealtimeMonitor):
    name: str = "cpu"
    cores: Optional[HistogramIndicator] = None
    total_compute: RatioIndicator = ffield(lambda: RatioIndicator(bin_themes["LMH"]))
    single_compute: RatioIndicator = ffield(lambda: RatioIndicator(bin_themes["lmh"]))
    memory: RatioIndicator = ffield(lambda: RatioIndicator(bin_themes["LMH"]))
    interval: float = 1.0

    def run(self, context: RealtimeContext):
        # TODO it's easier to make it realtime, but it's polling in nature
        # it would make sense to make it polling, and batch it with others
        # makes updates more economical; the issue is how psutil.cpu_percent measures things
        # see https://github.com/giampaolo/psutil/blob/master/psutil/__init__.py#L989
        # could be done manually, and then we are polling again

        while not context.should_exit():

            # TODO this blocks, efficiently, but it's not interruptible like context.sleep
            cpus = [
                i / 100 for i in psutil.cpu_percent(interval=self.interval, percpu=True)
            ]
            # TODO could also be interesting, wait times and stuff
            # psutil.cpu_times_percent()
            # psutil.getloadavg() does not have the problem of "since last call"

            # TODO would like to make cpu core hist a separate monitor
            # but because psutil sampling issue above we cannot yet
            # TODO also a timegraph could be cool
            if self.cores is None:
                ind_cores = ""
            else:
                ind_cores = self.cores.format(cpus)

            ind_total = self.total_compute.format(sum(cpus) / len(cpus))
            ind_single = self.single_compute.format(max(cpus))

            ind_memory = self.memory.format(
                psutil.virtual_memory().percent / 100,
            )

            # TODO overall I'm struggling with how to show it calm
            # but also allow to spot when one cpu is busy
            # show these states?: idle, one busy, all busy, or just busy count?
            # busy means >80%, if we use single char utf8 that can count to 24 or more?
            # or two percentages, one is overall, one is overall*count... ok almost like max
            # pie with one arrow, pie with many arrows for each
            # first arrows, 1,2,3 for how many cores used (>80%) then switch to overall pie or so
            # cpu icon + zz icon, then the upt to 3 arrows, then switch to overall "continuous"
            # see below :) the cpu icon itself could just start to glow, additionally maybe

            # TODO or we do something with true color now?
            # hot colors and cold colors, or grayscale
            # that would be less jumpy to look at, where/how do colors work?
            # tmux just uses normal escape? dwm ignores it?
            # should outputter remove, or formatter not make in the first place
            # also in tmux it's difficult to say how to goes with the theme

            #   ﴮ  
            context.send(f"cpu{ind_cores}{ind_total}{ind_single}{ind_memory}")
