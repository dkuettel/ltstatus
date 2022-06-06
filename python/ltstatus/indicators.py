import math
from dataclasses import dataclass

# browse at www.utf8icons.com or www.w3schools.com/charsets
bin_themes = {
    "bar": tuple(" ▁▂▃▄▅▆▇█"),
    "pie": tuple("○◔◑◕●"),
    "moon": tuple("🌕🌔🌓🌒🌑"),
    "triangle": tuple("·▸►▶"),
    "stack": tuple("·−=≡≣"),
    "arrow": tuple("·→⇉⇶"),
    "ascii-arrows": ("---", ">--", ">>-", ">>>"),
    "LMH": tuple(".LMH"),
    "lmh": tuple(".lmh"),
}


@dataclass(frozen=True)
class RatioIndicator:
    bins: list[str] = bin_themes["pie"]

    def format(self, ratio: float) -> str:
        index = math.floor(ratio * len(self.bins))
        index = min(index, len(self.bins) - 1)
        return self.bins[index]


@dataclass(frozen=True)
class HistogramIndicator:
    length: int = 3
    ratio: RatioIndicator = RatioIndicator(bin_themes["bar"])

    def format(self, ratios: list[float]) -> str:
        hist = [0] * self.length
        for ratio in ratios:
            index = min(math.floor(ratio * self.length), self.length - 1)
            hist[index] += 1
        hist = [i / len(ratios) for i in hist]
        return "".join(self.ratio.format(i) for i in hist)
