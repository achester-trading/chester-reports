"""
Signal-triage Batch 17, items 97(a) and 97(c) (docs/change-order-signal-triage-
batch-17-2026-10-26.md; B79, b79-capitulation-count, 26 Oct 2026): the
Capitulation Count and the sector divergence line.

  A  EACH FAMILY'S TRUE AND FALSE CASE, the order's five tests exactly: VIX above
     30 or VIX/VIX3M above 1; the equity put/call 20-session mean at or above 0.8;
     net GEX flipped negative to positive with spot above the flip (a sign read
     only at net-to-gross 0.10 or more); short interest in its top quintile while
     the low holds and RSP/SPY is above its value at the low; flows in for two
     weeks and AAII bearish peaked above 50% and falling.
  B  A GAP FAMILY lowers the scorable count and scores nothing; family 5 is a gap
     while its flows leg is (J4).
  C  THE LABELS: 0-1 none, 2-3 oversold, 4-5 surrender; "surrender unreachable"
     below 4 scorable; no decimals.
  D  THE PRINT RULES: the direction mark against the prior session; the close on
     exception (the count changed, or 2 or more); table 3's caption, and "not
     built" while no writer stores the T&B verdict.
  E  97(c): the VXN-VIX spread above its 90th percentile, or SMH's drawdown more
     than twice the index's, is an exception; anything else is not.
  F  THE LEDGER: the pre-registration at its SHA-256; the rule's INSUFFICIENT, PASS
     and FAIL on fixtures; a family before its series is "not existent" and not
     scorable.
  G  NOTHING ENTERS THE T&B COMPOSITE OR THE MARKET-STATE OBJECT: no reader of the
     count outside its block, and the module writes nothing.
  H  PLACEMENT: the close's Positioning & flows and the Weekly's; the VIX/VIX3M
     ratio from FRED's pair first, else calc.vix3m_over_vix inverted.

Synthetic fixtures only: no live store, no network, no model.
"""

from __future__ import annotations

import ast
import copy
import datetime as dt
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = FAIL = 0
LIVE_DB = REPO / "data" / "chester.db"
LIVE_DB_AT_START = LIVE_DB.exists()
PREREG = "docs/ledgers/capitulation-count-2026-10-26.md"
PREREG_SHA = "9cc5a283c4c6d1716f44b46e1561797b35536d43e0e9210698519cf45ce74d4e"
DAY = "2026-10-23"


def check(ok: bool, what: str) -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {what}")
    else:
        FAIL += 1
        print(f"  FAIL  {what}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def weekdays(end: str, n: int) -> list[str]:
    d, out = dt.date.fromisoformat(end), []
    while len(out) < n:
        if d.weekday() < 5:
            out.insert(0, d.isoformat())
        d -= dt.timedelta(days=1)
    return out


DAYS = weekdays(DAY, 300)


def cfg():
    from altdata import capitulation_count as cc
    return cc.config()


def fam(c: dict, fid: str) -> dict:
    return next(f for f in c["families"] if f["id"] == fid)


def run(series: dict, day: str = DAY, conf=None) -> dict:
    from altdata import capitulation_count as cc
    return cc.score(series, day, conf or cfg())


def flat(key_vals: dict) -> dict:
    """{key: value or [values]} -> {key: [(day, v)]} ending on DAY."""
    out = {}
    for k, v in key_vals.items():
        vals = v if isinstance(v, list) else [v]
        out[k] = list(zip(DAYS[-len(vals):], vals))
    return out


def price_path(low_ago: int, today_above: bool) -> list[float]:
    """252 closes: a high, a drawdown to a low `low_ago` sessions back, then a rebound."""
    n = 252
    up = [100 + i * 0.1 for i in range(n - 60)]
    hi = up[-1]
    down_len = 60 - low_ago
    down = [hi - (i + 1) * (25 / down_len) for i in range(down_len)]
    low = down[-1]
    after = [low + (i + 1) * (0.5 if today_above else -0.01) for i in range(low_ago)]
    return up + down + after


def group_a():
    head("A  EACH FAMILY'S TRUE AND FALSE CASE")
    r = run(flat({"fred.vix": 31.0}))
    check(fam(r, "vix")["state"] == "yes", "VIX 31: yes")
    r = run(flat({"fred.vix": 19.45, "fred.vix3m": 20.48}))
    check(fam(r, "vix")["state"] == "no" and "0.95" in fam(r, "vix")["reading"],
          "23 Oct 2026, VIX 19.45 and VIX3M 20.48 (ratio 0.95): no")
    r = run(flat({"fred.vix": 25.0, "fred.vix3m": 24.0}))
    check(fam(r, "vix")["state"] == "yes", "VIX 25, VIX3M 24 (ratio above 1): yes")
    r = run(flat({"fred.vix": 25.0, "calc.vix3m_over_vix": 0.9}))
    check(fam(r, "vix")["state"] == "yes", "no FRED VIX3M: calc.vix3m_over_vix 0.9 inverted (1.11): yes")

    r = run(flat({"cboe.pc_equity": [0.85] * 20}))
    check(fam(r, "put_call")["state"] == "yes", "equity put/call 20-session mean 0.85: yes")
    r = run(flat({"cboe.pc_equity": [0.80] * 20}))
    check(fam(r, "put_call")["state"] == "yes", "mean exactly 0.80: yes (at or above)")
    r = run(flat({"cboe.pc_equity": [0.67] * 20}))
    check(fam(r, "put_call")["state"] == "no", "mean 0.67: no")
    r = run(flat({"cboe.pc_equity": [0.9] * 10}))
    check(fam(r, "put_call")["state"] == "gap" and "accruing" in fam(r, "put_call")["reading"],
          "10 sessions: a gap, accruing")

    g = {"exposure.net_gex": [-5.0, -4.0, 2.0], "exposure.net_to_gross": [0.2, 0.2, 0.2],
         "exposure.gamma_flip": [580.0, 580.0, 580.0], "exposure.spot": [575.0, 576.0, 585.0]}
    r = run(flat(g))
    check(fam(r, "gamma")["state"] == "yes", "net GEX negative then positive, spot above the flip: yes")
    g2 = dict(g, **{"exposure.spot": [575.0, 576.0, 579.0]})
    check(fam(run(flat(g2)), "gamma")["state"] == "no", "spot below the flip: no")
    g3 = dict(g, **{"exposure.net_to_gross": [0.2, 0.2, 0.05]})
    check(fam(run(flat(g3)), "gamma")["state"] == "no", "today's net-to-gross 0.05 (indeterminate): no")
    g4 = dict(g, **{"exposure.net_gex": [3.0, 4.0, 2.0]})
    check(fam(run(flat(g4)), "gamma")["state"] == "no", "positive throughout, never flipped: no")

    px = price_path(10, True)
    si = [1e6 + i * 1e4 for i in range(30)]
    base = {"finra.short_interest": si, "yfinance.mkt_gspc": px,
            "calc.breadth_rsp_over_spy": [0.30] * 242 + [0.31] * 10}
    r = run(flat(base))
    check(fam(r, "short_interest")["state"] == "yes",
          "short interest at its 100th percentile, low 10 sessions old and held, RSP/SPY above its value at the low: yes")
    b2 = dict(base, **{"calc.breadth_rsp_over_spy": [0.30] * 242 + [0.29] * 10})
    check(fam(run(flat(b2)), "short_interest")["state"] == "no", "RSP/SPY below its value at the low: no")
    b3 = dict(base, **{"finra.short_interest": [2e6 - i * 1e4 for i in range(30)]})
    check(fam(run(flat(b3)), "short_interest")["state"] == "no", "short interest at the bottom of its history: no")
    b4 = dict(base, **{"yfinance.mkt_gspc": price_path(1, True)})
    check(fam(run(flat(b4)), "short_interest")["state"] == "no", "the low only 1 session old (not held 3): no")

    c2 = copy.deepcopy(cfg())
    f5 = next(f for f in c2["count"]["families"] if f["id"] == "flows")
    f5["flow_keys"], f5["aaii_bearish_key"] = ["etf.flow_test"], "aaii.bearish_test"
    good = {"etf.flow_test": [-5.0, 3.0, 4.0], "aaii.bearish_test": [40.0, 55.0, 48.0]}
    check(fam(run(flat(good), conf=c2), "flows")["state"] == "yes",
          "(with a flows feed) two weeks of inflow, AAII bearish peaked at 55 and falling: yes")
    bad = {"etf.flow_test": [3.0, -1.0, 4.0][-2:] and [-1.0, 4.0], "aaii.bearish_test": [40.0, 45.0, 44.0]}
    check(fam(run(flat(bad), conf=c2), "flows")["state"] == "no",
          "(with a flows feed) an outflow week and a peak of 45: no")


def group_b():
    head("B  A GAP FAMILY LOWERS THE SCORABLE COUNT")
    r = run({})
    check(r["count"] == 0 and r["scorable"] == 0, "nothing stored: 0 of 0 scorable")
    r = run(flat({"fred.vix": 31.0}))
    check(r["count"] == 1 and r["scorable"] == 1, "VIX alone stored and firing: 1 of 1 scorable")
    r = run(flat({"fred.vix": 19.0, "cboe.pc_equity": [0.9] * 20}))
    check(r["count"] == 1 and r["scorable"] == 2, "VIX no, put/call yes: 1 of 2 scorable")
    check(fam(r, "flows")["state"] == "gap" and "J4" in fam(r, "flows")["reading"],
          "family 5 is a gap while its flows leg is (J4)")
    stale = {"fred.vix": [(DAYS[-30], 40.0)]}
    check(fam(run(stale), "vix")["state"] == "gap", "a VIX close older than the allowance is a gap, never carried")


def group_c():
    head("C  THE LABELS")
    from altdata import capitulation_count as cc
    c = cfg()
    want = {0: "none", 1: "none", 2: "oversold", 3: "oversold", 4: "surrender", 5: "surrender"}
    check(all(cc.label(n, c) == w for n, w in want.items()), "0-1 none, 2-3 oversold, 4-5 surrender")
    line = cc.count_line({"count": 1, "scorable": 3, "label": "none", "direction": "up",
                          "prior": {"count": 0, "day": "2026-10-22"}})
    check("1 of 3 scorable" in line and "surrender unreachable at 3 scorable" in line and "▲" in line,
          f"the line: '{line}'")
    check("." not in line.split("(")[0], "no decimals in the count")


class FakeStore:
    def __init__(self, series: dict):
        self.series = series

    def as_of(self, key, cutoff, instrument=None):
        return [{"observed_at": d, "value_num": v} for d, v in self.series.get(key, [])
                if d <= cutoff[:10]]


def group_d():
    head("D  THE PRINT RULES")
    from altdata import capitulation_count as cc
    c = cfg()
    vix = list(zip(DAYS[-3:], [20.0, 20.0, 32.0]))
    b = cc.build(FakeStore({"fred.vix": vix}), f"{DAY}T23:59:00", c, prior_day=DAYS[-2])
    check(b["count"] == 1 and b["prior"]["count"] == 0 and b["direction"] == "up",
          "the count rose from 0 to 1 against the prior session: up")
    check(cc.close_wanted(b, c), "the close prints it: the count changed")
    quiet = cc.build(FakeStore({"fred.vix": list(zip(DAYS[-3:], [20.0] * 3))}),
                     f"{DAY}T23:59:00", c, prior_day=DAYS[-2])
    check(not cc.close_wanted(quiet, c), "unchanged at 0: the close prints nothing")
    two = dict(quiet, count=2, prior={"count": 2, "day": DAYS[-2]})
    check(cc.close_wanted(two, c), "unchanged at 2 (the oversold band): the close prints it")
    cap = cc.table_3_caption(None, quiet, c)
    check("not built" in cap and "table 3" in cap, "no T&B verdict stored: the caption says so")
    sur = dict(quiet, label="surrender")
    check("Mechanical correction" in cc.table_3_caption("NEUTRAL", sur, c),
          "NEUTRAL with 4-5: table 3's mechanical-correction read")
    check("2022-type" in cc.table_3_caption("BOTTOM SIGNAL", dict(quiet, label="none"), c),
          "BOTTOM SIGNAL with 0-1: table 3's 2022-type read")
    px = list(zip(DAYS[-252:], [100.0] * 240 + [94.0] * 12))
    check(cc.weekly_wanted(FakeStore({"yfinance.mkt_gspc": px}), f"{DAY}T23:59:00", c) is not None,
          "the S&P 500 6% below its 52-week high: the Weekly prints it")
    px2 = list(zip(DAYS[-252:], [100.0] * 240 + [96.0] * 12))
    check(cc.weekly_wanted(FakeStore({"yfinance.mkt_gspc": px2}), f"{DAY}T23:59:00", c) is None,
          "4% below: the Weekly does not")


def group_e():
    head("E  97(c): THE SECTOR DIVERGENCE LINE")
    from altdata import capitulation_count as cc
    d = cfg()["divergence"]
    base = {"spread": ("2026-10-23", 8.85), "spread_pct": 80.0, "sector_dd": -15.0,
            "index_dd": -10.0, "flows": "not tracked", "exception": False}
    check(not cc.exception_of(dict(base), d)["exception"], "80th percentile, SMH -15% against -10%: no exception")
    check(cc.exception_of(dict(base, spread_pct=95.0), d)["exception"], "the spread at its 95th percentile: exception")
    check(cc.exception_of(dict(base, sector_dd=-26.0), d)["exception"], "SMH -26% against the index's -10%: exception")
    check(not cc.exception_of(dict(base, index_dd=0.0, sector_dd=-5.0), d)["exception"],
          "the index at its high: the drawdown arm cannot fire")
    vxn = list(zip(DAYS[-260:], [20.0 + (i % 7) for i in range(259)] + [40.0]))
    vix = list(zip(DAYS[-260:], [15.0] * 260))
    v = cc.divergence(FakeStore({"fred.vxn": vxn, "fred.vix": vix}), f"{DAY}T23:59:00")
    check(v["spread_pct"] == 100.0 and v["exception"], "a stored spread at its one-year high: 100th percentile, exception")
    line = cc.divergence_line(v)
    check("SMH flows not tracked" in line, f"SMH flows 'not tracked' (J5, no flows feed): '{line[:70]}...'")
    check(cfg()["divergence"]["sector_key"] == "yfinance.mkt_smh", "the sector leg reads SMH (J5)")


def group_f():
    head("F  THE LEDGER")
    import hashlib
    from altdata import capitulation_count as cc
    sha = hashlib.sha256((REPO / PREREG).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    check(sha == PREREG_SHA and cc.prereg_sha() == PREREG_SHA, f"{PREREG} at its SHA-256 ({sha[:12]}...)")
    rule = cfg()["ledger"]["rule"]

    def row(sc, n, held, r60):
        return {"scorable": sc, "count": n, "four_or_more": n >= 4, "low_held_60": held, "spx_60": r60}
    check(cc.verdict([row(3, 2, True, 5.0)] * 9, rule).startswith("INSUFFICIENT"),
          "fewer than 5 episodes with 4 scorable: INSUFFICIENT")
    check(cc.verdict([row(4, 4, True, 5.0)] * 4 + [row(4, 1, False, -2.0)] * 2, rule).startswith("PASS"),
          "4 firings, all held, all positive: PASS")
    check(cc.verdict([row(4, 4, False, -5.0)] * 4 + [row(4, 1, True, 2.0)] * 2, rule).startswith("FAIL"),
          "4 firings, none held: FAIL")
    c = cfg()
    check(len(c["ledger"]["episodes"]) == 14 and c["ledger"]["exists_from"]["flows"] is None,
          "fourteen episodes; flows not existent at every one")
    rows = cc.ledger_rows(FakeStore({"fred.vix": [("1987-12-03", 35.0), ("1987-12-04", 36.0)]}), c)
    r87 = next(r for r in rows if r["low"] == "1987-12-04")
    check(r87["family_vix"] == "not existent" and r87["scorable"] == 0,
          "1987's low predates the VIX's series (1990): 'not existent', not scorable")


def group_g():
    head("G  NOTHING ENTERS THE T&B COMPOSITE OR THE MARKET-STATE OBJECT")
    readers = []
    for p in list((REPO / "altdata").rglob("*.py")) + list((REPO / "daily_cascade").rglob("*.py")) + \
            [REPO / "regime.py", REPO / "contradictions.py"]:
        if p.name in ("capitulation_count.py", "capitulation_block.py", "cboe_putcall.py"):  # the feed names its reader
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        if ("capitulation_count" in t or "capitulation_block" in t) and \
                p.name not in ("stack.py", "weekly_stack.py"):
            readers.append(p.name)
    check(not readers, f"no reader outside the block and the two hooks ({readers or 'none'})")
    ms = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    check("capitulation" not in ms and "cboe.pc_" not in ms, "config/market_state.yaml names none of it")
    src = (REPO / "altdata" / "capitulation_count.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    check(not (calls & {"open_writer", "insert", "write_rows", "executemany"}),
          "the module writes nothing to a store")
    check("mode=ro" in src, "its CLI opens the store read-only")


def group_h():
    head("H  PLACEMENT AND THE RATIO")
    from altdata import capitulation_count as cc
    st = (REPO / "daily_cascade" / "stack.py").read_text(encoding="utf-8")
    ws = (REPO / "daily_cascade" / "weekly_stack.py").read_text(encoding="utf-8")
    check('built["positioning"]["items"] += capitulation_block.close_items(st, cutoff)' in st,
          "the close: Positioning & flows, on exception")
    check("capitulation_block.weekly_subsection(st, now)" in ws, "the Weekly: Positioning & flows")
    check(abs(cc.vix_over_vix3m({"fred.vix": 19.45, "fred.vix3m": 20.48}, None) - 19.45 / 20.48) < 1e-12,
          "the ratio reads FRED's pair first")
    check(abs(cc.vix_over_vix3m({}, 1.25) - 0.8) < 1e-12, "else calc.vix3m_over_vix, inverted")
    check(cc.vix_over_vix3m({}, None) is None, "neither: no ratio")


def main() -> int:
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h):
        try:
            g()
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(False, f"{g.__name__} raised {type(exc).__name__}: {exc}")
    head("THE GATE RUN")
    check(LIVE_DB.exists() == LIVE_DB_AT_START, "this gate run created no data/chester.db")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
