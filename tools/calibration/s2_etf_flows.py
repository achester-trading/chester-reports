"""
S-2's calibration ledger: the spot bitcoin ETF flow extremes (the crypto data-
sources order, 6 Oct 2026, S-2; the a47 chain, 19 Oct 2026).

THE ORDER'S GATE, AS IT STATES IT. "Forward 5/20-day BTC return after extremes,
2024 ->; pass is a non-zero asymmetry at 20 days across >= 8 non-overlapping
episodes." The extreme is the order's: the 5-day sum of total daily flow at or
beyond its 5th or 95th percentile against the full history from January 2024.

WHAT THE FIRST EDITION PRE-REGISTERS (the terms the order leaves open; ruling 2
of 17 Oct: a re-run applies them and may not change them):
  - the percentile is POINT-IN-TIME: each day's 5-day sum ranked against every
    5-day sum up to and including that day, from the 20th sum on (the store's
    calc.etf_5d_pct floor), so no extreme is judged with history it did not have;
  - entry is BTC-USD's close on the calendar day after the flow date (the day
    the T-1 figure is known); the 5- and 20-day returns are calendar days on
    Yahoo's daily BTC-USD closes, and the 20-day max drawdown beside them;
  - an episode is the first extreme day; the next episode in either tail starts
    no sooner than 20 calendar days after its entry (non-overlapping at the
    20-day horizon);
  - "a non-zero asymmetry at 20 days": the mean 20-day return after high
    (>= 95th) episodes minus the mean after low (<= 5th) episodes, with a Welch
    t-statistic of absolute value 2.0 or more; PASS needs >= 8 completed
    episodes in all and >= 3 in each tail, INSUFFICIENT below that, FAIL above
    it with |t| < 2.0.

THE RIGHTS IT WOULD GRANT, STATED AND NOT GRANTED: the narrow flag "ETF flows --
extreme" in the 07:00 anchor's crypto paragraph and the Weekly's flows block. The
flag is stored with gate status "not passed" (altdata/sources/crypto_derived.py)
and no block reads it; a PASS reaches the register only as a rule-31 draft, and
nothing changes until the operator accepts it. Nothing enters a composite.

Public sources only (tools/calibration/README.md): Farside's all-data page through
the writer's own parser, and BTC-USD through the one yfinance import. Never the
store.

    python tools/calibration/s2_etf_flows.py [--box] [--out DIR] [--date D]
"""

from __future__ import annotations

import datetime as dt
import io
import math
import statistics
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                          # noqa: E402

ITEM = "S-2"
TITLE = "Spot bitcoin ETF flow extremes and BTC's forward return"
WINDOW = 5
LOW, HIGH = 5.0, 95.0
MIN_SUMS = 20
HORIZONS = (5, 20)
SPACING = 20
T_MIN = 2.0
MIN_EPISODES, MIN_TAIL = 8, 3
FROM = "2024-01-11"
PASS_RULE = ("Forward 5/20-day BTC return after the 5-day flow sum's 5th/95th-"
             "percentile extremes, 2024 on; pass is a non-zero asymmetry at 20 days "
             "across >= 8 non-overlapping episodes (pre-registered here: the high-tail "
             "minus the low-tail mean 20-day return at an absolute Welch t of 2.0 or more, with >= 3 "
             "episodes in each tail).")


def load_public() -> dict:
    """{flows: [(date, $m)], btc: [(date, close)]} from the public sources."""
    from altdata.sources import farside as F                    # noqa: PLC0415
    from altdata.ledgers import sources as S                    # noqa: PLC0415
    html = F._get("https://farside.co.uk/bitcoin-etf-flow-all-data/")  # noqa: SLF001
    return {"flows": parse_totals(html), "btc": S.yahoo("BTC-USD"),
            "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def parse_totals(html: str) -> list[tuple[str, float]]:
    """Each day's Total, US$ millions, from the all-data table. The issuer columns
    are not checked here (the writer refuses a changed header; a study needs only
    the total)."""
    import pandas as pd                                          # noqa: PLC0415
    from altdata.sources import farside as F                    # noqa: PLC0415
    tables = pd.read_html(io.StringIO(html))
    tbl = next(t for t in tables if any(F._flat(c).lower() == "total"   # noqa: SLF001
                                        for c in t.columns))
    cols = [F._flat(c) for c in tbl.columns]                    # noqa: SLF001
    tot = next(i for i, c in enumerate(cols) if c.lower() == "total")
    out = {}
    for _, r in tbl.iterrows():
        vals = list(r.values)
        d, v = F._date(vals[0]), F._cell(vals[tot])             # noqa: SLF001
        # A row dated the retrieval day (UTC) or later is not final: left out.
        if d and v is not None and FROM <= d < dt.date.today().isoformat():
            out[d] = v
    return sorted(out.items())


def pit_percentile(hist: list[float], x: float) -> float:
    """x's percentile among `hist` (which includes x): the share at or below."""
    return 100.0 * sum(1 for h in hist if h <= x) / len(hist)


def extremes(flows: list[tuple[str, float]]) -> list[dict]:
    """Every day's 5-day sum and its point-in-time percentile, from the 20th sum."""
    out, sums = [], []
    for i in range(WINDOW - 1, len(flows)):
        s = sum(v for _, v in flows[i - WINDOW + 1:i + 1])
        sums.append(s)
        if len(sums) >= MIN_SUMS:
            out.append({"date": flows[i][0], "sum5": s,
                        "pct": pit_percentile(sums, s)})
    return out


def _close_on_or_after(btc: dict, day: str) -> Optional[tuple[str, float]]:
    d = dt.date.fromisoformat(day)
    for k in range(5):
        x = (d + dt.timedelta(days=k)).isoformat()
        if x in btc:
            return x, btc[x]
    return None


def forward(btc: dict, entry_day: str, n: int) -> tuple[Optional[float], Optional[float]]:
    """(return, max drawdown) over n calendar days from the entry close."""
    e = btc.get(entry_day)
    end = (dt.date.fromisoformat(entry_day) + dt.timedelta(days=n)).isoformat()
    if e is None or end not in btc:
        return None, None
    path = [btc[(dt.date.fromisoformat(entry_day) + dt.timedelta(days=k)).isoformat()]
            for k in range(n + 1)
            if (dt.date.fromisoformat(entry_day) + dt.timedelta(days=k)).isoformat() in btc]
    peak, mdd = path[0], 0.0
    for p in path:
        peak = max(peak, p)
        mdd = min(mdd, p / peak - 1.0)
    return btc[end] / e - 1.0, mdd


def episodes(ext: list[dict], btc: dict) -> list[dict]:
    out, last_entry = [], None
    for e in ext:
        tail = "high" if e["pct"] >= HIGH else "low" if e["pct"] <= LOW else None
        if not tail:
            continue
        nxt = (dt.date.fromisoformat(e["date"]) + dt.timedelta(days=1)).isoformat()
        ent = _close_on_or_after(btc, nxt)
        if not ent:
            continue
        if last_entry and (dt.date.fromisoformat(ent[0])
                           - dt.date.fromisoformat(last_entry)).days < SPACING:
            continue
        last_entry = ent[0]
        row = {"flow_date": e["date"], "tail": tail, "sum5_usd_m": round(e["sum5"], 1),
               "percentile": round(e["pct"], 1), "entry": ent[0],
               "entry_close": round(ent[1], 2)}
        for n in HORIZONS:
            r, m = forward(btc, ent[0], n)
            row[f"ret_{n}d"] = None if r is None else round(r, 4)
            row[f"mdd_{n}d"] = None if m is None else round(m, 4)
        row["completed"] = row["ret_20d"] is not None
        out.append(row)
    return out


def welch_t(a: list[float], b: list[float]) -> Optional[float]:
    if len(a) < 2 or len(b) < 2:
        return None
    va, vb = statistics.variance(a), statistics.variance(b)
    se = math.sqrt(va / len(a) + vb / len(b))
    return None if se == 0 else (statistics.mean(a) - statistics.mean(b)) / se


def judge(eps: list[dict]) -> dict:
    done = [e for e in eps if e["completed"]]
    hi = [e["ret_20d"] for e in done if e["tail"] == "high"]
    lo = [e["ret_20d"] for e in done if e["tail"] == "low"]
    n = len(done)
    t = welch_t(hi, lo)
    diff = (statistics.mean(hi) - statistics.mean(lo)) if hi and lo else None
    line = (f"{n} completed episodes ({len(hi)} high, {len(lo)} low); 20-day mean "
            f"after high {C.pct(statistics.mean(hi)) if hi else 'n/a'}, after low "
            f"{C.pct(statistics.mean(lo)) if lo else 'n/a'}; asymmetry "
            f"{C.pct(diff)}; Welch t {'n/a' if t is None else f'{t:+.2f}'}")
    if n < MIN_EPISODES or len(hi) < MIN_TAIL or len(lo) < MIN_TAIL:
        verdict = f"{C.INSUFFICIENT} ({line}; the floor is {MIN_EPISODES} with {MIN_TAIL} a tail)"
    elif t is not None and abs(t) >= T_MIN:
        verdict = f"{C.PASS} ({line})"
    else:
        verdict = f"{C.FAIL} ({line})"
    return {"n": n, "verdict": verdict, "line": line, "t": t, "diff": diff}


def study(d: dict, mode: str) -> dict:
    flows = d["flows"]
    btc = dict(d["btc"])
    ext = extremes(flows)
    eps = episodes(ext, btc)
    j = judge(eps)
    as_of = flows[-1][0] if flows else "none"
    body = [f"- Daily total flows: {len(flows)} sessions, {flows[0][0] if flows else '-'} "
            f"to {as_of}; 5-day sums ranked point-in-time from the {MIN_SUMS}th sum "
            f"({len(ext)} ranked days).",
            f"- Extreme days: {sum(1 for e in ext if e['pct'] >= HIGH)} at or above the "
            f"95th, {sum(1 for e in ext if e['pct'] <= LOW)} at or below the 5th; "
            f"{len(eps)} non-overlapping episodes, {j['n']} with a completed 20-day "
            f"window.", f"- {j['line']}."]
    for h in ("high", "low"):
        for n_ in HORIZONS:
            xs = [e[f"ret_{n_}d"] for e in eps if e["tail"] == h and e[f"ret_{n_}d"] is not None]
            ms = [e[f"mdd_{n_}d"] for e in eps if e["tail"] == h and e[f"mdd_{n_}d"] is not None]
            body.append(f"- After {h} episodes, {n_} days: mean {C.pct(statistics.mean(xs)) if xs else 'n/a'}, "
                        f"median {C.pct(statistics.median(xs)) if xs else 'n/a'}, mean max "
                        f"drawdown {C.pct(statistics.mean(ms)) if ms else 'n/a'} (n={len(xs)}).")
    return {"item": ITEM, "title": TITLE, "as_of": as_of,
            "window": f"{FROM} to {as_of} (flows); BTC-USD closes to {d['btc'][-1][0] if d['btc'] else '-'}",
            "n": j["n"],
            "statistic": "the high-tail minus the low-tail mean 20-day BTC return after the "
                         "5-day flow sum's point-in-time 95th/5th-percentile extremes, "
                         "and its Welch t",
            "pass_rule": PASS_RULE, "verdict": j["verdict"],
            "rights": ("Would grant: the narrow flag \"ETF flows -- extreme\" in the "
                       "07:00 anchor's crypto paragraph and the Weekly's flows block. "
                       "This ledger grants nothing. " + C.RIGHTS_NOTE),
            "sources": [f"Farside Investors, Bitcoin ETF flow, all data "
                        f"(farside.co.uk/bitcoin-etf-flow-all-data/), US$ millions, "
                        f"retrieved {d.get('retrieved', '-')}",
                        "Yahoo Finance BTC-USD daily closes (the one yfinance import)"],
            "source_mode": mode, "body": body, "episodes": eps,
            "caveats": ["Farside revises recent rows; a re-run reads the page as it "
                        "stands.",
                        "Calendar-day horizons on a 24/7 asset; the ETF flows are US "
                        "sessions only."]}


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study))
