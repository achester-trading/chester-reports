"""
SR-15 -- the cross-asset rank test and the gold window test (signal-triage ST-7;
st-t2-rates, 18 Oct 2026).

    python tools/calibration/sr15_valuation.py [--box] [--out DIR] [--date D]

THE REGISTER'S GATE (docs/signal-triage-register.md, SR-15). "Cross-asset rank
test -- forward 3y real return of the cheapest-tercile asset vs. the richest,
paired by date; per-asset forward 3y/5y real returns conditional on z > +1.5 and
z < -1. Pass: cheap beats rich in >= 2/3 of paired observations. Window-fragility
test on gold: if its conclusion flips between 1971-start and 1994-start windows,
gold drops to base-rate rights only."

THE FOUR VALUATIONS, as the register's light house version names them, each an
expanding-window z (the mean and standard deviation from the window's start
through that month; 60 months before the first z), monthly:
  gold         log of the real gold price (World Bank Pink Sheet, $/oz, monthly
               average; over CPIAUCNS)
  S&P 500      Shiller's CAPE
  Treasuries   MINUS the real 10-year yield, GS10 less CPI on the year (a high
               real yield is cheap); TIPS start in 2003, so the ex-post real
               yield is used throughout and DFII10 is not mixed in
  commodities  log of the real World Bank total commodity index
A positive z is rich, a negative one cheap, for all four.

WHAT THE FIRST EDITION PRE-REGISTERS, where the register is silent:
  * TERCILES OF FOUR: the cheapest is the lowest z of the month, the richest the
    highest. A pair is the month's two; "cheap beats rich" is the cheapest's
    forward 36-month real return above the richest's. Every month with all four
    z and both returns counts (overlapping: the register says observations); the
    non-overlapping count, every 36th month, is printed beside it.
  * FLOOR: 60 paired months and 5 non-overlapping pairs.
  * THE GOLD CONCLUSION, per window: mean reversion holds when the median forward
    36-month real return with z > +1.5 is below the median with z < -1. Both
    windows are evaluated over the months both cover (from 60 months after
    1994-01), so only the anchor differs. A bucket with fewer than 12 months is
    "undefined"; a flip is two defined conclusions that differ. An undefined one
    leaves the test "not determinable", which keeps gold where it is and says so.
  * The rank test's window is 1971 (the end of Bretton Woods' gold peg).

Real returns: gold's and the commodity index's price changes over CPIAUCNS
(neither earns a yield here; the index is spot, so no roll or collateral);
Shiller's S&P total return; the 10-year par bond's. Point in time: GS10, CPIAUCNS,
the Pink Sheet's monthly averages and Shiller's price and dividend are not
revised in any way that matters here; CAPE uses Shiller's earnings series as
published in today's sheet.
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                           # noqa: E402

ITEM = "SR-15"
BURN = 60
START, START_ALT = "1971-01", "1994-01"
H3, H5 = 36, 60
FLOOR_PAIRS, FLOOR_BLOCKS = 60, 5
MIN_BUCKET = 12
RICH, CHEAP = 1.5, -1.0
HIT = 2.0 / 3.0
ASSETS = ("gold", "spx", "ust", "cmdty")
NAMES = {"gold": "gold", "spx": "S&P 500", "ust": "Treasuries", "cmdty": "commodities"}


def _pink_sheet() -> tuple[dict, dict, str]:
    """(gold $/oz, total index) monthly, and the file's 'Updated on' line,
    through the World Bank writer's link and workbook readers."""
    from altdata.sources import _publication as pub
    from altdata.sources import worldbank as wb
    from altdata.sources._base import http_get_response
    data, _ = http_get_response(pub.find_link(wb.PAGE, wb.LINK), timeout=120)
    book = pub.read_xlsx(data)
    rows, updated = wb.rows_from_table(book[wb.SHEET], "", "observed")
    idx = {r["observed_at"][:7]: r["value"] for r in rows
           if r["registry_key"] == "worldbank.cmo_total"}
    t = book["Monthly Prices"]
    head = next(i for i, r in enumerate(t) if r and "Gold" in [str(c).strip() for c in r])
    j = [str(c).strip() for c in t[head]].index("Gold")
    gold = {}
    for r in t[head + 1:]:
        m = re.fullmatch(r"(\d{4})M(\d{2})", str(r[0] or "")) if r else None
        if m and j < len(r) and isinstance(r[j], (int, float)):
            gold[f"{m.group(1)}-{m.group(2)}"] = float(r[j])
    return gold, idx, updated or "not stated"


def load_public() -> dict:
    from altdata.ledgers import sources as S
    sh = S.shiller()
    gold, idx, updated = _pink_sheet()
    return {"gold": gold, "cmdty": idx, "pink_updated": updated,
            "cape": C.monthly_last(sh["shiller.cape"]),
            "sp_price": C.monthly_last(sh["shiller.sp_price"]),
            "sp_div": C.monthly_last(sh["shiller.sp_dividend"]),
            "gs10": C.monthly_last(S.fred("GS10")),
            "cpi": C.monthly_last(S.fred("CPIAUCNS"))}


def metrics(d: dict) -> dict[str, dict]:
    """The four valuation levels (rich = high) before the z."""
    cpi, infl = d["cpi"], C.yoy_pct(d["cpi"])
    return {
        "gold": {m: math.log(v / cpi[m]) for m, v in d["gold"].items() if cpi.get(m)},
        "spx": dict(d["cape"]),
        "ust": {m: -(y - infl[m]) for m, y in d["gs10"].items() if m in infl},
        "cmdty": {m: math.log(v / cpi[m]) for m, v in d["cmdty"].items() if cpi.get(m)}}


def returns(d: dict) -> dict[str, dict]:
    """Monthly nominal returns per asset."""
    def ratio(s):
        return {m: s[m] / s[C.madd(m, -1)] - 1 for m in s if s.get(C.madd(m, -1))}
    return {"gold": ratio(d["gold"]), "cmdty": ratio(d["cmdty"]),
            "spx": C.equity_tr(d["sp_price"], d["sp_div"]),
            "ust": C.bond_tr(d["gs10"])}


def fwd_real(rets: dict, cpi: dict, a: str, m: str, n: int):
    return C.real(C.compound(rets[a], m, n), cpi, m, n)


def gold_conclusion(z: dict, rets: dict, cpi: dict, months: list[str]) -> dict:
    rich = [fwd_real(rets, cpi, "gold", m, H3) for m in months if z.get(m, 0) > RICH]
    cheap = [fwd_real(rets, cpi, "gold", m, H3) for m in months
             if m in z and z[m] < CHEAP]
    rich = [x for x in rich if x is not None]
    cheap = [x for x in cheap if x is not None]
    if len(rich) < MIN_BUCKET or len(cheap) < MIN_BUCKET:
        return {"n_rich": len(rich), "n_cheap": len(cheap), "rich": C.median(rich),
                "cheap": C.median(cheap), "reverts": None}
    return {"n_rich": len(rich), "n_cheap": len(cheap), "rich": C.median(rich),
            "cheap": C.median(cheap), "reverts": C.median(rich) < C.median(cheap)}


def judge(pairs: list[dict]) -> dict:
    """The rank test's rule over the paired months; the verdict carries its
    inputs."""
    blocks = pairs[::H3]
    n = len(pairs)
    hit = C.share([p["cheap_beats_rich"] for p in pairs])
    hit_b = C.share([p["cheap_beats_rich"] for p in blocks])
    if n < FLOOR_PAIRS or len(blocks) < FLOOR_BLOCKS:
        verdict = (f"{C.INSUFFICIENT} -- {n} paired months, {len(blocks)} "
                   f"non-overlapping; floors {FLOOR_PAIRS} and {FLOOR_BLOCKS}; no rate prints")
    else:
        verdict = (f"{C.PASS if hit >= HIT else C.FAIL} -- cheap beat rich in "
                   f"{C.sh(hit)} of {n} paired months (rule >= 66.7%)")
    return {"blocks": blocks, "n": n, "hit": hit, "hit_b": hit_b, "verdict": verdict}


def study(d: dict, mode: str) -> dict:
    lv = metrics(d)
    rets = returns(d)
    cpi = d["cpi"]
    z = {a: C.expanding_z(lv[a], START, BURN) for a in ASSETS}
    common = sorted(set.intersection(*(set(z[a]) for a in ASSETS)))
    pairs = []
    for m in common:
        f = {a: fwd_real(rets, cpi, a, m, H3) for a in ASSETS}
        if any(v is None for v in f.values()):
            continue
        order = sorted(ASSETS, key=lambda a: z[a][m])
        lo, hi = order[0], order[-1]
        pairs.append({"month": m, "cheapest": lo, "z_cheapest": round(z[lo][m], 3),
                      "richest": hi, "z_richest": round(z[hi][m], 3),
                      "real36_cheapest": round(f[lo], 4),
                      "real36_richest": round(f[hi], 4),
                      "cheap_beats_rich": f[lo] > f[hi]})
    j = judge(pairs)
    blocks, n, hit, hit_b, verdict = j["blocks"], j["n"], j["hit"], j["hit_b"], j["verdict"]

    # Per-asset conditional returns (the 1971 window).
    cond = []
    for a in ASSETS:
        for label, test in ((f"z > +{RICH}", lambda v: v > RICH),
                            (f"z < {CHEAP}", lambda v: v < CHEAP)):
            ms = [m for m in sorted(z[a]) if test(z[a][m])]
            r3 = [x for x in (fwd_real(rets, cpi, a, m, H3) for m in ms) if x is not None]
            r5 = [x for x in (fwd_real(rets, cpi, a, m, H5) for m in ms) if x is not None]
            cond.append((NAMES[a], label, len(ms), len(r3), C.median(r3),
                         len(r5), C.median(r5)))

    # Gold's window test.
    z_alt = C.expanding_z(lv["gold"], START_ALT, BURN)
    both = sorted(set(z["gold"]) & set(z_alt))
    g71 = gold_conclusion(z["gold"], rets, cpi, both)
    g94 = gold_conclusion(z_alt, rets, cpi, both)
    if g71["reverts"] is None or g94["reverts"] is None:
        gold_line = ("NOT DETERMINABLE -- a bucket holds fewer than "
                     f"{MIN_BUCKET} months in one window; gold keeps its rights "
                     "as the register states them until a run can decide")
    elif g71["reverts"] != g94["reverts"]:
        gold_line = ("FLIPS -- the 1971 and 1994 windows disagree; under the "
                     "register gold drops to base-rate rights only")
    else:
        gold_line = ("HOLDS -- both windows reach the same conclusion "
                     f"({'reverts' if g71['reverts'] else 'does not revert'})")

    last = max(common) if common else None
    cur = {a: (z[a].get(last)) for a in ASSETS}
    body = [f"Current z (as of {last}): " + ", ".join(
                f"{NAMES[a]} {C.f2(cur[a])}" for a in ASSETS) + ".",
            "",
            f"Rank test, {START} window: {n} paired months "
            f"({pairs[0]['month'] if pairs else 'n/a'} to {pairs[-1]['month'] if pairs else 'n/a'}); "
            f"cheap beat rich in {C.sh(hit)} of them; in {C.sh(hit_b)} of "
            f"{len(blocks)} non-overlapping (every 36th month).",
            "",
            "Per asset, forward real returns by z bucket (1971 window):",
            "",
            "| Asset | Bucket | Months | n 3y | Median 3y | n 5y | Median 5y |",
            "|---|---|---|---|---|---|---|"]
    body += [f"| {a} | {b} | {k} | {n3} | {C.pct(m3)} | {n5} | {C.pct(m5)} |"
             for a, b, k, n3, m3, n5, m5 in cond]
    body += ["",
             f"Gold's window test, over the {len(both)} months both windows cover "
             f"({both[0] if both else 'n/a'} on):",
             "",
             "| Window | n rich | Median 3y, rich | n cheap | Median 3y, cheap | Reverts |",
             "|---|---|---|---|---|---|"]
    for w, g in (("1971 start", g71), ("1994 start", g94)):
        body.append(f"| {w} | {g['n_rich']} | {C.pct(g['rich'])} | {g['n_cheap']} | "
                    f"{C.pct(g['cheap'])} | "
                    f"{'undefined' if g['reverts'] is None else ('yes' if g['reverts'] else 'no')} |")
    body += ["", f"Gold window test: **{gold_line}**."]
    return {
        "item": ITEM, "title": "cross-asset valuation z-scores: the rank test and gold's window",
        "as_of": f"{last} (latest month with all four z); last paired month "
                 f"{pairs[-1]['month'] if pairs else 'n/a'}",
        "window": f"{START} to {last} (z burn-in {BURN} months; the gold test also from {START_ALT})",
        "n": n,
        "statistic": "share of months in which the cheapest asset's forward 36-month "
                     "real return beat the richest's; gold's median forward return "
                     "rich vs cheap in each window",
        "pass_rule": ("the register's: cheap beats rich in >= 2/3 of paired "
                      "observations; gold drops to base-rate rights if its "
                      "conclusion flips between 1971 and 1994 starts. Pre-registered "
                      "by this first edition: lowest vs highest z of four; floors "
                      f"{FLOOR_PAIRS} months and {FLOOR_BLOCKS} non-overlapping; the "
                      f"gold conclusion is median(rich) < median(cheap), buckets of "
                      f">= {MIN_BUCKET} months"),
        "verdict": verdict + f"; gold window test {gold_line.split(' --')[0]}",
        "rights": ("PASS: the Book A rebalancing modifier (toward the lowest-z "
                   "diversifier, sized by |z|) and the Valuation confidence "
                   "modifier; gold at zero rebalancing weight while Factor V is "
                   "active, and at base-rate rights only if its test flips. FAIL: "
                   "the strip is display only. " + C.RIGHTS_NOTE),
        "sources": [f"World Bank Pink Sheet (CMO-Historical-Data-Monthly.xlsx, "
                    f"{d.get('pink_updated')}) through altdata/sources/worldbank.py: "
                    "gold $/oz and the total index",
                    "Shiller's ie_data.xls through altdata/sources/shiller.py: CAPE, "
                    "price, dividend",
                    "FRED graph CSV (no key): GS10, CPIAUCNS"],
        "source_mode": mode, "body": body, "episodes": pairs,
        "caveats": ["The box re-run reads the same public sources (the calibration "
                    "rule), not the store.",
                    "The 10-year real yield is ex post (GS10 less trailing CPI) "
                    "throughout, so its z is not the TIPS yield's.",
                    "Paired months overlap: 36 consecutive months share most of "
                    "their forward window."]}


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study))
