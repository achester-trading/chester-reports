"""
The stack's cadences: the daily close, the Weekly and the Monthly. (T2.6)

    cad = cadence.get("monthly")
    cad["period"], cad["budget"]["words"], cad["depth_words"]["deep"]
    w = cadence.Period("month")
    w.on            # "on the month"
    w.col           # "The month"

ONE SECTION CODE, THREE CADENCES. The shared builders, the renderer, the prose
and the budget guard take a cadence and read everything that differs from
config/reporting_stack.yaml under `cadences:` -- the period noun, its column
head, the word budget and chart cap, the reading target, the depth allowances,
how many paragraphs a section keeps and how long each may run, whether a
sub-section keeps its own. A string a section prints about its period ("on the
week", "Opened this month", "Week or prior") is built here from the noun, never
hard-coded beside the figure it describes, so the Monthly passes "monthly" and
no longer rewrites the Weekly's sentences after the fact.
"""

from __future__ import annotations

from typing import Optional

NAMES = ("daily", "weekly", "monthly")


def get(name: str, cfg: Optional[dict] = None) -> dict:
    """One cadence, resolved: the `cadences:` entry, its budget, its reading
    target and its depth allowances. Raises KeyError on an unknown cadence --
    a report naming a cadence the config does not declare is a code fault."""
    if cfg is None:
        from altdata import bars as bars_mod                    # noqa: PLC0415
        cfg = bars_mod.load_config()
    c = dict((cfg.get("cadences") or {})[name])
    c["name"] = name
    c["budget"] = dict((cfg.get("budget") or {}).get(name) or {})
    c["reading_target_minutes"] = (cfg.get("reading_targets_minutes") or {}).get(name)
    c["depth_words"] = dict(cfg.get(c.get("depth_words") or "depth_words") or {})
    c["depth_paragraphs"] = dict(cfg.get("depth_paragraphs") or {})
    return c


def paragraph_cap(cad: dict, depth: Optional[str]) -> int:
    """Words one kept paragraph may run to at `depth`: the cadence's number, or
    the section's allowance when the cadence says "depth"."""
    pw = cad.get("paragraph_words")
    if pw == "depth":
        return int(cad["depth_words"].get(depth or "") or
                   max(cad["depth_words"].values() or [120]))
    return int(pw or 120)


# The cap as the prompts write it: "cite at most SIX figures".
FIGURE_WORDS = {1: "ONE", 2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE", 6: "SIX",
                7: "SEVEN", 8: "EIGHT", 9: "NINE", 10: "TEN", 12: "TWELVE"}


def figure_cap(cad: dict) -> int:
    """The most figures one paragraph after the claim line may cite at this
    cadence (`paragraph_figures`; six where a cadence declares none)."""
    return int(cad.get("paragraph_figures") or 6)


def figure_word(n: int) -> str:
    return FIGURE_WORDS.get(int(n), str(n))


class Period:
    """Every period phrase a section prints, from the one noun. The weekly forms
    are the strings the Weekly has always printed; the others follow them."""

    def __init__(self, period: str = "week", column: Optional[str] = None):
        self.p = period
        self._col = column

    @classmethod
    def of(cls, cadence: str, cfg: Optional[dict] = None) -> "Period":
        c = get(cadence, cfg)
        return cls(c["period"], c.get("column"))

    @property
    def on(self) -> str:                    # "on the week"
        return f"on the {self.p}"

    @property
    def this(self) -> str:                  # "this week"
        return f"this {self.p}"

    @property
    def This(self) -> str:                  # "This week"     # noqa: N802
        return f"This {self.p}"

    @property
    def the(self) -> str:                   # "the week"
        return f"the {self.p}"

    @property
    def poss(self) -> str:                  # "the week's"
        return f"the {self.p}'s"

    @property
    def end(self) -> str:                   # "at the week's end"
        return f"at the {self.p}'s end"

    @property
    def End(self) -> str:                   # "At the week's end"  # noqa: N802
        return f"At the {self.p}'s end"

    @property
    def col(self) -> str:                   # "Week", "The month"
        return self._col or self.p.capitalize()

    @property
    def or_prior(self) -> str:              # "Week or prior"
        return f"{self.p.capitalize()} or prior"

    @property
    def mean(self) -> str:                  # "week mean"
        return f"{self.p} mean"

    @property
    def week_before(self) -> str:
        """The retail-sentiment comparison window is a week whatever the
        cadence: "the week before", or "the week before the month"."""
        return "the week before" if self.p == "week" else f"the week before the {self.p}"

    @property
    def since_report(self) -> str:
        """CFTC's own cadence is weekly, so on the Weekly its change is "since
        the prior report"; on a longer cadence it is the period's change."""
        return "since the prior report" if self.p in ("week", "session") else self.on
