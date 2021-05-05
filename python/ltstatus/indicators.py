import math
from dataclasses import dataclass
from typing import List

from ltstatus.tools import ffield

# browse at www.utf8icons.com or www.w3schools.com/charsets
bin_themes = {
    "bar": list(" ▁▂▃▄▅▆▇█"),
    "pie": list("○◔◑◕●"),
    "moon": list("🌕🌔🌓🌒🌑"),
    "triangle": list("·▸►▶"),
    "stack": list("·−=≡≣"),
    "arrow": list("·→⇉⇶"),
    "ascii-arrows": ["---", ">--", ">>-", ">>>"],
    "LMH": list(".LMH"),
    "lmh": list(".lmh"),
}


@dataclass
class RatioIndicator:
    bins: List[str] = ffield(lambda: bin_themes["pie"])

    def format(self, ratio: float) -> str:
        index = math.floor(ratio * len(self.bins))
        index = min(index, len(self.bins) - 1)
        return self.bins[index]


@dataclass
class HistogramIndicator:
    length: int = 3
    ratio: RatioIndicator = ffield(lambda: RatioIndicator(bin_themes["bar"]))

    def format(self, ratios: List[float]) -> str:
        hist = [0] * self.length
        for ratio in ratios:
            index = min(math.floor(ratio * self.length), self.length - 1)
            hist[index] += 1
        hist = [i / len(ratios) for i in hist]
        return "".join(self.ratio.format(i) for i in hist)
