"""
The funding-currency features -- signal-triage ST-5 (docs/change-order-signal-
triage-2026-09-25.md section 2.2.2; SR-2, SR-4; st-t2-rates, 18 Oct 2026).

    python -m altdata.funding_currency compute [--as-of T] [--from DAY] [--dry-run]
    python -m altdata.funding_currency show [--as-of T]

Computed from the store, written as calc.* rows by the features pass (it rides
altdata/market_features.compute after ST-4's absorption features, never fatal),
and read by the Monthly's Factor IV and China lines
(daily_cascade/absorption_block.py). DISPLAY AND MODIFIER ONLY, as the order
grants: nothing here enters a composite, a trigger or the market-state object.
The settings are session-set in config/funding_currency.yaml, each with its
reason, until ST-8's gates calibrate them.

THE YEN (SR-2's four metrics, and the realized vol the fourth needs)
  calc.jp_front_diff       US 2-year (DGS2) less the JGB 2-year (MoF), bp
  calc.jp_front_diff_60d   its change over 60 sessions, bp (the velocity)
  calc.jpy_pos_z           CFTC yen net non-commercial position (instrument JPY,
                           available at the Friday release) as a z against its
                           trailing 156 weekly reports (52 before the first)
  calc.jp_hedged_carry     10-year UST less (the 3-month bill, DTB3, less Japan's
                           3-month interbank rate, OECD monthly carried 70 days):
                           what a hedged Japanese buyer of Treasuries earns, %
  calc.usdjpy_rvol_20d     USDJPY's 20-session realized vol, annualised, %
  calc.jpy_unwind          1 when USDJPY fell 3% or more over 5 sessions while its
                           realized vol is at least 1.5x its 250-session median

THE YUAN (SR-4)
  calc.cny_fix_dev         the fix against the previous session's onshore close
                           (CNY=X), bp: negative is a fix leaning against weakness
  calc.uscn_10y_spread     10-year UST less the CGB 10-year (CFETS), bp
  calc.deval_tell          1 when the tell's first two legs both hold: the fix's
                           lean gone (5-observation mean of calc.cny_fix_dev at or
                           above -10 bp) AND the CNH-CNY gap wide and widening
                           (5-observation mean at or above +30 bp, and 20 bp
                           wider than 20 observations earlier)

  THE NO-VERDICT RULE (ruling 6, 18 Oct): the tell prints "2 of 3 legs tracked"
  with each leg's state, and never a verdict word while a leg is not tracked
  (verdict_allowed()); deval_legs() is what the Monthly's line reads.

  THE THIRD LEG IS NOT TRACKED (rule 30). "State banks stop selling dollars" was a
  by-hand input (G-21; the by-hand key state_bank_dollar_selling, dropped 16 Oct)
  and no keyless source within terms reports state-bank FX flows. So a 1 here is
  two of three legs, never the full tell, and every reader says so.

  calc.cnh_cny_gap, the order's name for the offshore gap, is NOT a second series:
  calc.cnh_cny_bp (altdata/market_features.py, AQ-3, 11 Oct) is that gap, and the
  tell's second leg computes it through the same cfets.gap_bp.

THE CANDIDATE CONTRADICTION ROWS (G-10): carry_vs_vol and fix_vs_offshore are
declared in config/funding_currency.yaml in the table's own form and are not in
the table; candidate_rows() computes each one's divergence z through
contradictions.gap_z for the Monthly's lines. No row opens.
"""

from __future__ import annotations

import logging
import math
import statistics
from pathlib import Path
from typing import Optional

import yaml

from . import observations
from .absorption import latest_avail, series

log = logging.getLogger(__name__)

CONFIG = Path(__file__).resolve().parent.parent / "config" / "funding_currency.yaml"

US_2Y, JGB_2Y = "fred.yield_2y", "mof.jgb_2y"
UST_10Y, BILL_3M, JP_3M = "fred.yield_10y", "fred.tbill_3m", "fred.jp_3m"
CFTC_NET, CFTC_JPY = "cftc.noncomm_net", "JPY"
USDJPY = "yfinance.mkt_usdjpy"
FIX, CNY, CNH, CGB_10Y = "cfets.cny_fix", "yfinance.mkt_usdcny", "cnh.usdcnh", "cfets.cgb_10y"

FEATURES: dict[str, str] = {
    "calc.jp_front_diff": "US 2-year less the JGB 2-year, bp",
    "calc.jp_front_diff_60d": "the front differential's change over 60 sessions, bp",
    "calc.jpy_pos_z": "CFTC yen net non-commercial position, z over 156 weeks",
    "calc.jp_hedged_carry": "10-year UST less (3-month bill less 3-month yen), percent",
    "calc.usdjpy_rvol_20d": "USDJPY 20-session realized vol, annualised, percent",
    "calc.jpy_unwind": "the yen unwind tell, 1 or 0",
    "calc.cny_fix_dev": "the CNY fix against the previous onshore close, bp",
    "calc.uscn_10y_spread": "10-year UST less the CGB 10-year, bp",
    "calc.deval_tell": "the devaluation tell's two tracked legs, 1 or 0",
}
THIRD_LEG_KEY = "state_bank_dollar_selling"


def config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# The arithmetic, each piece reproduced by hand in tools/validate_st_t2_rates.py
# ---------------------------------------------------------------------------
def spread_bp(a: float, b: float) -> float:
    return 100.0 * (a - b)


def zscore(window: list[float]) -> Optional[float]:
    """The last value's z against the window it ends (sample sd)."""
    if len(window) < 3:
        return None
    sd = statistics.stdev(window)
    return None if sd == 0 else (window[-1] - statistics.fmean(window)) / sd


def realized_vol(closes: list[float]) -> Optional[float]:
    """Annualised realized vol of the log returns between these closes, percent."""
    r = [math.log(b / a) for a, b in zip(closes, closes[1:]) if a > 0 and b > 0]
    return None if len(r) < 2 else 100.0 * statistics.stdev(r) * math.sqrt(252)


def carried(s: list[tuple], day: str, days: int) -> Optional[tuple]:
    """The latest point of a slower series on or before `day`, within `days`."""
    import datetime as dt
    best = None
    for x in s:
        if x[0] <= day:
            best = x
        else:
            break
    if best is None or (dt.date.fromisoformat(day)
                        - dt.date.fromisoformat(best[0])).days > days:
        return None
    return best


def fix_dev_bp(fix: float, prev_close: float) -> float:
    """The fix against the previous close, bp: + is the fix weaker (more yuan per
    dollar) than the close, - a fix leaning against weakness."""
    from .sources import cfets                                  # noqa: PLC0415
    return cfets.gap_bp(fix, prev_close)


def offshore_gap_bp(cnh: float, cny: float) -> float:
    """CNH against CNY, bp (+ is CNH weaker): calc.cnh_cny_bp's arithmetic, for a
    reader that must not import a writer (the 12:30 hooks)."""
    return fix_dev_bp(cnh, cny)


def wmax(av: list[str], i: int, n: int) -> str:
    return max(av[max(0, i - n + 1):i + 1])


# ---------------------------------------------------------------------------
def compute_rows(db, as_of: Optional[str] = None, first_day: Optional[str] = None,
                 cfg: Optional[dict] = None) -> list[dict]:
    cfg = cfg or config()
    yen, yuan = cfg["yen"], cfg["yuan"]
    rows: list[dict] = []

    def emit(key: str, day: str, value, available: str) -> None:
        if value is None or (isinstance(value, float) and not math.isfinite(value)) \
                or (first_day and day < first_day):
            return
        rows.append({"registry_key": key, "instrument": None, "observed_at": day,
                     "available_at": available, "value": round(float(value), 6),
                     "source": "calc", "availability_kind": "observed"})

    # The front differential and its velocity.
    jgb = {d: (v, a) for d, v, a in series(db, JGB_2Y, as_of)}
    fd = [(d, spread_bp(v, jgb[d][0]), latest_avail(a, jgb[d][1]))
          for d, v, a in series(db, US_2Y, as_of) if d in jgb]
    n = int(yen["front_change_sessions"])
    for i, (d, v, a) in enumerate(fd):
        emit("calc.jp_front_diff", d, v, a)
        if i >= n:
            emit("calc.jp_front_diff_60d", d, v - fd[i - n][1],
                 latest_avail(a, fd[i - n][2]))

    # Positioning.
    pos = series(db, CFTC_NET, as_of, CFTC_JPY)
    w, lo = int(yen["pos_z_weeks"]), int(yen["pos_z_min_weeks"])
    av = [a for _, _, a in pos]
    for i, (d, v, a) in enumerate(pos):
        win = [x[1] for x in pos[max(0, i - w + 1):i + 1]]
        if len(win) >= lo:
            emit("calc.jpy_pos_z", d, zscore(win), wmax(av, i, w))

    # The hedged carry.
    bill = {d: (v, a) for d, v, a in series(db, BILL_3M, as_of)}
    jp3 = series(db, JP_3M, as_of)
    for d, v, a in series(db, UST_10Y, as_of):
        j = carried(jp3, d, int(yen["carry_days"]))
        if d in bill and j:
            emit("calc.jp_hedged_carry", d, v - (bill[d][0] - j[1]),
                 latest_avail(a, bill[d][1], j[2]))

    # Realized vol and the unwind tell.
    px = series(db, USDJPY, as_of)
    vs, ms, med = int(yen["vol_sessions"]), int(yen["unwind_sessions"]), \
        int(yen["vol_median_sessions"])
    pav = [a for _, _, a in px]
    rv: list[tuple[str, float, str]] = []
    for i in range(vs, len(px)):
        v = realized_vol([x[1] for x in px[i - vs:i + 1]])
        if v is not None:
            rv.append((px[i][0], v, wmax(pav, i, vs + 1)))
            emit("calc.usdjpy_rvol_20d", px[i][0], v, rv[-1][2])
    idx = {d: i for i, (d, _, _) in enumerate(px)}
    for k in range(med, len(rv)):
        d, v, a = rv[k]
        i = idx[d]
        if i < ms:
            continue
        move = 100.0 * (px[i][1] / px[i - ms][1] - 1.0)
        spike = v >= float(yen["vol_spike_ratio"]) * statistics.median(
            x[1] for x in rv[k - med:k])
        emit("calc.jpy_unwind", d,
             1.0 if move <= float(yen["unwind_move_pct"]) and spike else 0.0,
             latest_avail(a, wmax(pav, i, ms + 1)))

    # The yuan.
    cny = series(db, CNY, as_of)
    dev: list[tuple[str, float, str]] = []
    k = -1
    for d, f, a in series(db, FIX, as_of):
        while k + 1 < len(cny) and cny[k + 1][0] < d:
            k += 1
        if k >= 0 and f and cny[k][1]:
            dev.append((d, fix_dev_bp(f, cny[k][1]), latest_avail(a, cny[k][2])))
            emit("calc.cny_fix_dev", d, dev[-1][1], dev[-1][2])
    cgb = {d: (v, a) for d, v, a in series(db, CGB_10Y, as_of)}
    for d, v, a in series(db, UST_10Y, as_of):
        if d in cgb:
            emit("calc.uscn_10y_spread", d, spread_bp(v, cgb[d][0]),
                 latest_avail(a, cgb[d][1]))
    for t in tell_legs(dev, offshore_gap(cny, series(db, CNH, as_of)), yuan):
        emit("calc.deval_tell", t["day"], 1.0 if t["leg1"] and t["leg2"] else 0.0,
             t["available"])
    return rows


def offshore_gap(cny: list[tuple], cnh: list[tuple]) -> list[tuple[str, float, str]]:
    """[(day, CNH-CNY gap bp, available_at)]: calc.cnh_cny_bp's own arithmetic."""
    from .sources import cfets                                  # noqa: PLC0415
    cnyd = {d: (v, a) for d, v, a in cny}
    return [(d, cfets.gap_bp(v, cnyd[d][0]), latest_avail(a, cnyd[d][1]))
            for d, v, a in cnh if d in cnyd and cnyd[d][0]]


def tell_legs(dev: list[tuple], gap: list[tuple], yuan: dict) -> list[dict]:
    """The devaluation tell's two TRACKED legs on each gap date they are readable:
    [{day, leg1, lean_bp, leg2, gap_bp, widen_bp, available}]. The one place the
    legs are computed: calc.deval_tell stores their conjunction and the Monthly's
    line prints each one (deval_legs)."""
    lo_n, g_n, w_n = int(yuan["lean_obs"]), int(yuan["gap_obs"]), int(yuan["gap_widen_obs"])
    gav = [a for _, _, a in gap]
    out, j = [], 0
    for i in range(g_n + w_n - 1, len(gap)):
        d = gap[i][0]
        while j < len(dev) and dev[j][0] <= d:
            j += 1
        lean = dev[max(0, j - lo_n):j]
        if len(lean) < lo_n:
            continue
        now_m = statistics.fmean(x[1] for x in gap[i - g_n + 1:i + 1])
        then_m = statistics.fmean(x[1] for x in gap[i - w_n - g_n + 1:i - w_n + 1]) \
            if i - w_n - g_n + 1 >= 0 else None
        if then_m is None:
            continue
        lean_m = statistics.fmean(x[1] for x in lean)
        out.append({"day": d, "leg1": lean_m >= float(yuan["lean_gone_bp"]),
                    "lean_bp": lean_m,
                    "leg2": now_m >= float(yuan["gap_weak_bp"])
                    and now_m - then_m >= float(yuan["gap_widen_bp"]),
                    "gap_bp": now_m, "widen_bp": now_m - then_m,
                    "available": latest_avail(wmax(gav, i, w_n + g_n),
                                              *(x[2] for x in lean))})
    return out


# THE NO-VERDICT RULE (ruling 6 of 18 Oct 2026). The tell prints as "2 of 3 legs
# tracked", each leg's state and the untracked leg's key named, and NEVER a verdict
# word (ON, off, fired, tripped) until every leg has a source or the order is
# amended. LEGS_TOTAL is the order's three; the tracked count is read from the
# config's third_leg, so giving the third leg a source is a config change the
# gate sees.
LEGS_TOTAL = 3


def legs_tracked(cfg: Optional[dict] = None) -> int:
    third = str(((cfg or config()).get("yuan") or {}).get("third_leg") or "")
    return 2 if third.strip().lower().startswith("not tracked") else 3


def verdict_allowed(cfg: Optional[dict] = None) -> bool:
    return legs_tracked(cfg) == LEGS_TOTAL


def deval_legs(db, as_of: Optional[str], cfg: Optional[dict] = None) -> Optional[dict]:
    """The newest readable state of each tracked leg, knowable at as_of, or None."""
    cfg = cfg or config()
    cny = series(db, CNY, as_of)
    dev, k = [], -1
    for d, f, a in series(db, FIX, as_of):
        while k + 1 < len(cny) and cny[k + 1][0] < d:
            k += 1
        if k >= 0 and f and cny[k][1]:
            dev.append((d, fix_dev_bp(f, cny[k][1]), latest_avail(a, cny[k][2])))
    legs = tell_legs(dev, offshore_gap(cny, series(db, CNH, as_of)), cfg["yuan"])
    return legs[-1] if legs else None


def candidate_rows(db, as_of: Optional[str], cfg: Optional[dict] = None) -> list[dict]:
    """[{id, magnitude, n, absent_reason}] for the declared candidates, through the
    contradiction table's own statistic. Display only: no persistence, no open."""
    import contradictions                                       # noqa: PLC0415
    import datetime as dt
    cfg = cfg or config()
    spec = cfg["candidate_contradictions"]
    out = []
    for p in spec["pairs"]:
        a, b = (series(db, k, as_of) for k in p["legs"])
        last = max((x[0] for x in a + b), default=None)
        if last:
            start = (dt.date.fromisoformat(last)
                     - dt.timedelta(days=int(spec["window_days"]))).isoformat()
            a, b = ([(d, v) for d, v, _ in s if d >= start] for s in (a, b))
        r = contradictions.gap_z(a, b, *(int(x) for x in p["polarities"])) if a and b \
            else {"magnitude": None, "n": 0,
                  "absent_reason": f"not stored: {' and '.join(p['legs'])}"}
        out.append({"id": p["id"], "legs": p["legs"], "magnitude": r.get("magnitude"),
                    "n": r.get("n"), "last": r.get("aligned_last"),
                    "absent_reason": r.get("absent_reason")})
    return out


def compute(as_of: Optional[str] = None, first_day: Optional[str] = None,
            store: Optional[observations.ObservationStore] = None,
            dry_run: bool = False) -> dict:
    own = store is None
    db = store or observations.ObservationStore()
    try:
        rows = compute_rows(db, as_of, first_day)
        written = 0 if dry_run else db.write_many(observations.drop_unchanged(db, rows))
        by_key: dict[str, int] = {}
        for r in rows:
            by_key[r["registry_key"]] = by_key.get(r["registry_key"], 0) + 1
        return {"computed": len(rows), "written": written, "by_key": by_key}
    finally:
        if own:
            db.close()


def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.funding_currency")
    ap.add_argument("cmd", choices=["compute", "show"])
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--from", dest="first", default=None)
    ap.add_argument("--db", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    with observations.ObservationStore(a.db) as st:
        if a.cmd == "compute":
            r = compute(a.as_of, a.first, st, a.dry_run)
            print(f"{r['computed']} rows computed, {r['written']} written")
            for k in sorted(r["by_key"]):
                print(f"  {k:32} {r['by_key'][k]:>6}")
        else:
            from altdata import session                          # noqa: PLC0415
            from daily_cascade import absorption_block            # noqa: PLC0415
            now = a.as_of or session.utc_iso(timespec="microseconds")
            for ln in absorption_block.factor_lines(st, now) + \
                    absorption_block.china_status(st, now):
                print(ln)
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
