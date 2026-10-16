"""
The rest of Batch 6's Tranche 1 -- where items 31, 32, 38, 39, 42, 43 and 44 print.

    mechanics_subsections(st, now, cadence)
        Mechanics: "Concentration and breadth" (31 and 44, section 4 ruling 3)
        and "The oil-shock signature" (32, ruling 4), the latter where item 24's
        stock-bond correlation sits on session B's branch
    plumbing_subsections(st, now, cadence)
        Plumbing & rates: "Inflation expectations: the composite" (42) and "Real
        10-year yields across countries" (39, the global section)
    currencies_lines(st, now)
        the US-DE and US-JP real differentials, for the Currencies read (the
        Weekly's "Global rates and FX", the Monthly's global-rates bucket)
    allocation_line(st, now)
        item 38's ratio, printed beside item 30's allocation block
    slow_subsections(st, now)
        the Monthly's Slow layers: "Factor V: gold against world equities" (38)
        and "Global policy diffusion" (43, ruling 5)
    ahead_subsection(st, now)
        Ahead: item 43's one line

The reads are altdata/st_r5_t1_rest.py's; this module only lays them out, asks
no paragraph of any sub-section (`paragraph_wanted: False`), and never lets a
fault take a section down. Report-only throughout.
"""

from __future__ import annotations

import logging
from typing import Optional

from altdata import st_r5_t1_rest as tr

log = logging.getLogger(__name__)

CONC_TITLE = "Concentration and breadth"
OIL_TITLE = "The oil-shock signature"
EXP_TITLE = "Inflation expectations: the composite"
REAL_TITLE = "Real 10-year yields across countries"
GOLD_TITLE = "Factor V: gold against world equities"
DIFF_TITLE = "Global policy diffusion"
AHEAD_TITLE = "The growth lead: policy diffusion"
BREADTH_COLUMNS = ["Distance from the 52-week closing high", "Members", "Share"]
EXP_COLUMNS = ["Input", "Latest", "Month", "z", "Window (n)"]
REAL_COLUMNS = ["Country", "Nominal 10-year", "Month", "Real, core CPI",
                "Real, headline CPI", "Linker"]

_CACHE: dict = {}


def reads(st, now: str, cfg: Optional[dict] = None) -> dict:
    """The seven reads once per (store, cutoff): the 20-year correlations are
    the slow part, and four sections ask."""
    k = (id(st), now, id(cfg) if cfg else None)
    if k not in _CACHE:
        _CACHE.clear()
        _CACHE[k] = tr.build(st, now, cfg or tr.config())
    return _CACHE[k]


def _safe(fn, what: str, default):
    try:
        return fn()
    except Exception:                                           # noqa: BLE001
        log.warning("%s faulted", what, exc_info=True)
        return default


def mechanics_subsections(st, now: str, cadence: str = "weekly",
                          cfg: Optional[dict] = None) -> list[dict]:
    def build():
        b = reads(st, now, cfg)
        br, co, oil = b["breadth"], b["concentration"], b["oil_shock"]
        conc = {"title": CONC_TITLE, "not_tracked": [],
                "lines": [tr.concentration_line(co), tr.breadth_line(br)],
                "paragraph_wanted": False,
                "table_note": ("SPY's daily holdings (SSGA) are the S&P 500's "
                               "float-adjusted weights, a second share class "
                               "counted with its issuer. A member's distance is "
                               "its close against its 52-week closing high. "
                               "Today's members only, so survivorship reads the "
                               "past lower than a point-in-time list would. "
                               "Report-only: the gap's ledger (44b) comes first."),
                "data": {"concentration": tr.public(co), "breadth": tr.public(br)}}
        if br["state"] == "read":
            conc["table"] = {"columns": BREADTH_COLUMNS, "rows": tr.breadth_rows(br)}
        oil_sub = {"title": OIL_TITLE, "not_tracked": [], "lines": [tr.oil_shock_line(oil)],
                   "paragraph_wanted": False,
                   "table_note": ("Brent (DCOILBRENTEU) against the S&P 500 and the "
                                  "10-year, daily changes, six-month windows. "
                                  "Report-only: the order rules it an inflation "
                                  "sub-state, which waits on a pre-registered "
                                  "calibration and its ledger (32b)."),
                   "data": {"oil_shock": tr.public(oil)}}
        return [conc, oil_sub]
    return _safe(build, "concentration, breadth and the oil-shock signature", [])


def plumbing_subsections(st, now: str, cadence: str = "weekly",
                         cfg: Optional[dict] = None) -> list[dict]:
    def build():
        b = reads(st, now, cfg)
        e, ry = b["expectations"], b["real_yields"]
        exp = {"title": EXP_TITLE,
               "table": {"columns": EXP_COLUMNS, "rows": tr.expectations_rows(e)},
               "lines": tr.expectations_lines(e), "paragraph_wanted": False,
               "not_tracked": tr.expectations_absent(e),
               "table_note": ("Each input's z is its latest month against its own "
                              "trailing ten years of months; the composite is their "
                              "mean and is not printed on fewer than three. It "
                              "extends the batch-2 de-anchoring flag (SR-24). "
                              "Descriptive; unvalidated."),
               "data": {"expectations": tr.public(e)}}
        real = {"title": REAL_TITLE,
                "table": {"columns": REAL_COLUMNS, "rows": tr.real_yield_rows(ry)},
                "lines": tr.differential_lines(ry), "paragraph_wanted": False,
                "not_tracked": tr.real_yield_absent(ry),
                "table_note": ("Nominal: the OECD 10-year on FRED, a monthly "
                               "average (China: CFETS, the month's average). Real: "
                               "nominal less CPI inflation on the year, core first, "
                               "headline beside it (Eurostat's HICP for the euro "
                               "countries, Sweden and Switzerland; IMF headline for "
                               "the EM screen). Linker: the 10-year TIPS yield, "
                               "monthly average."),
                "data": {"real_yields": tr.public(ry)}}
        return [exp, real]
    return _safe(build, "expectations and real yields", [])


def currencies_lines(st, now: str, cfg: Optional[dict] = None) -> list[str]:
    return _safe(lambda: tr.differential_lines(reads(st, now, cfg)["real_yields"]),
                 "the real-yield differentials", [])


def allocation_line(st, now: str, cfg: Optional[dict] = None) -> Optional[str]:
    return _safe(lambda: tr.gold_equity_line(reads(st, now, cfg)["gold_equity"]),
                 "the gold/equity ratio", None)


def slow_subsections(st, now: str, cfg: Optional[dict] = None) -> list[dict]:
    def build():
        b = reads(st, now, cfg)
        g, d = b["gold_equity"], b["diffusion"]
        gold = {"title": GOLD_TITLE, "lines": [tr.gold_equity_line(g)],
                "paragraph_wanted": False,
                "not_tracked": [g["wfe_gap"]] if g.get("wfe_gap") else [],
                "table_note": ("The World Gold Council's above-ground stock at the "
                               "gold front-month close, over world equity "
                               "capitalisation, which has no free source; the "
                               "by-hand audit, queued, looks for one."),
                "data": {"gold_equity": tr.public(g)}}
        diff = {"title": DIFF_TITLE, "not_tracked": [], "lines": tr.diffusion_lines(d),
                "paragraph_wanted": False,
                "table_note": ("The BIS policy-rate table, month-end: each central "
                               "bank's last move is its latest month-end change of a "
                               "basis point or more; the index is cuts less hikes "
                               "over the banks counted. The G7 leading indicator is "
                               "the OECD's, on FRED. Report-only until its lead "
                               "ledger (43b)."),
                "data": {"diffusion": tr.public(d)}}
        return [gold, diff]
    return _safe(build, "the slow-layer lines", [])


def ahead_subsection(st, now: str, cfg: Optional[dict] = None) -> Optional[dict]:
    def build():
        ln = tr.ahead_line(reads(st, now, cfg)["diffusion"])
        return ({"title": AHEAD_TITLE, "not_tracked": [], "lines": [ln], "paragraph_wanted": False}
                if ln else None)
    return _safe(build, "the ahead line", None)
