"""
The Capitulation Count, signal-triage Batch 17 item 97(a), and the sector
divergence line, 97(c) (docs/change-order-signal-triage-batch-17-2026-10-26.md,
entry 97 and Appendix A; B79, 26 Oct 2026).

    python -m altdata.capitulation_count show [--date D] [--db PATH]
    python -m altdata.capitulation_count ledger --db PATH [--dry-run]

A five-family bottom checklist on a fast clock -- is selling exhausted? days --
printed BESIDE the Top & Bottom verdict (is the regime turning? months) and never
inside it. The order's Appendix A table 3 is the read: the pair, not either alone.

THE COUNT is an integer per session: one point per SCORABLE family, exactly the
order's five tests (config/capitulation_count.yaml `count.families`):
  1  VIX above 30, or VIX/VIX3M above 1
  2  the equity put/call ratio's 20-session mean at or above 0.8
  3  SPY's net GEX flipped negative to positive, with spot above the flip
  4  short interest in the top quintile of its own history while the S&P 500
     holds above its drawdown low, with RSP/SPY above its value at the low
  5  equity ETF flows turned to two weeks of inflow, and AAII bearish peaked
     above 50% and falling
A family whose inputs are missing, or older than `max_age_days` at the cutoff, is
a gap: it scores nothing and lowers the SCORABLE count, which prints beside the
count ("1 of 3 scorable"; J4). The labels are the order's bands on the count
itself: 0-1 none, 2-3 oversold, 4-5 surrender. No decimals, no weights, no
blending. Each family prints its reading; a direction mark compares the count with
the prior session's.

WHAT IT IS NOT. It reads the store as of the cutoff and writes nothing. It is not
a T&B input, not a composite, not a dial and not a dimension of the market-state
object (metrics_registry.yaml market_state_barred); the binary "4 or more" enters
the T&B intake queue only after the calibration ledger
(docs/ledgers/capitulation-count-2026-10-26.md). Report rights; a Book C setup
named in the daily close may cite it.

97(c), THE SECTOR DIVERGENCE LINE: VXN less VIX with its one-year percentile, and
SMH's drawdown from its 52-week high against the S&P 500's (J5: SMH, not SOXX);
SMH flows "not tracked". The close prints it on exception only: the spread above
its 90th percentile, or SMH's drawdown more than twice the index's.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Optional

from altdata.numeral_audit import ordinal

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "capitulation_count.yaml"
PREREG = ROOT / "docs" / "ledgers" / "capitulation-count-2026-10-26.md"
LEDGER_CSV = ROOT / "docs" / "ledgers" / "capitulation-count-2026-10-26.csv"


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8"))


def _fam(cfg: dict, fid: str) -> dict:
    return next(f for f in cfg["count"]["families"] if f["id"] == fid)


# ---------------------------------------------------------------- the store

def pts(st, key: str, cutoff: str, instrument: Optional[str] = None) -> list[tuple[str, float]]:
    """A key's (day, value) points as of the cutoff, one per day (the day's last)."""
    by_day: dict[str, tuple[str, float]] = {}
    for r in st.as_of(key, cutoff, instrument):
        v = r.get("value_num")
        if v is None:
            continue
        ts = str(r["observed_at"])
        day = ts[:10]
        if day not in by_day or ts >= by_day[day][0]:
            by_day[day] = (ts, float(v))
    return sorted((d, tv[1]) for d, tv in by_day.items())


def _fresh(p: list[tuple[str, float]], day: str, max_age: int) -> bool:
    return bool(p) and (dt.date.fromisoformat(day) - dt.date.fromisoformat(p[-1][0])).days <= max_age


def _on_or_before(p: list[tuple[str, float]], day: str) -> Optional[tuple[str, float]]:
    best = None
    for d, v in p:
        if d > day:
            break
        best = (d, v)
    return best


def vix_over_vix3m(fred: dict, calc_vix3m_over_vix: Optional[float]) -> Optional[float]:
    """VIX/VIX3M: FRED's pair first; else the stored calc.vix3m_over_vix, inverted."""
    v, v3 = fred.get("fred.vix"), fred.get("fred.vix3m")
    if v is not None and v3:
        return v / v3
    if calc_vix3m_over_vix:
        return 1.0 / calc_vix3m_over_vix
    return None


# ---------------------------------------------------------------- the five families
# Each returns {"id", "name", "state": "yes" | "no" | "gap", "reading"}.

def _gap(f: dict, why: str) -> dict:
    return {"id": f["id"], "name": f["name"], "state": "gap", "reading": why}


def _res(f: dict, ok: bool, reading: str) -> dict:
    return {"id": f["id"], "name": f["name"], "state": "yes" if ok else "no", "reading": reading}


def family_vix(f: dict, series: dict, day: str, max_age: int) -> dict:
    vix = series.get("fred.vix") or []
    if not _fresh(vix, day, max_age):
        return _gap(f, "no VIX close within the allowance (fred.vix)")
    fred = {"fred.vix": vix[-1][1]}
    v3 = series.get("fred.vix3m") or []
    if v3 and v3[-1][0] == vix[-1][0]:
        fred["fred.vix3m"] = v3[-1][1]
    calc = series.get("calc.vix3m_over_vix") or []
    c = calc[-1][1] if calc and calc[-1][0] == vix[-1][0] else None
    ratio = vix_over_vix3m(fred, c)
    ok = vix[-1][1] > f["vix_above"] or (ratio is not None and ratio > f["ratio_above"])
    rs = f"{ratio:.2f}" if ratio is not None else "not stored"
    return _res(f, ok, f"VIX {vix[-1][1]:.2f}; VIX/VIX3M {rs}")


def family_put_call(f: dict, series: dict, day: str, max_age: int) -> dict:
    eq = series.get(f["key"]) or []
    if not eq:
        return _gap(f, "no rows (cboe.pc_equity: the Cboe writer is switched off pending its terms ruling)")
    if not _fresh(eq, day, max_age):
        return _gap(f, f"stale: last {eq[-1][0]}")
    n = int(f["sessions"])
    if len(eq) < n:
        return _gap(f, f"accruing ({len(eq)} of {n} sessions)")
    mean = sum(v for _, v in eq[-n:]) / n
    return _res(f, mean >= f["at_least"], f"equity 20-session mean {mean:.2f}; today {eq[-1][1]:.2f}")


def family_gamma(f: dict, series: dict, day: str, max_age: int) -> dict:
    gex = series.get("exposure.net_gex") or []
    if not _fresh(gex, day, max_age):
        return _gap(f, "no SPY capture within the allowance (exposure.net_gex)")
    ntg = dict(series.get("exposure.net_to_gross") or [])
    flip = dict(series.get("exposure.gamma_flip") or [])
    spot = dict(series.get("exposure.spot") or [])
    lim = float(f["min_net_to_gross"])

    def sign(d: str, v: float) -> int:
        r = ntg.get(d)
        if r is None or abs(r) < lim:
            return 0                                           # indeterminate
        return 1 if v > 0 else -1
    d0, v0 = gex[-1]
    now = sign(d0, v0)
    prior = [sign(d, v) for d, v in gex[:-1][-int(f["lookback_sessions"]):]]
    flipped = now > 0 and -1 in prior
    above = d0 in flip and d0 in spot and spot[d0] > flip[d0]
    word = {1: "positive", -1: "negative", 0: "indeterminate"}[now]
    fl = f"{flip[d0]:.2f}" if d0 in flip else "no flip"
    sp = f"{spot[d0]:.2f}" if d0 in spot else "no spot"
    return _res(f, flipped and above,
                f"net GEX {word}{' (flipped from negative)' if flipped else ''}; spot {sp} against flip {fl}")


def drawdown_low(px: list[tuple[str, float]], day: str, high_sessions: int) -> Optional[dict]:
    """The 52-week high to the cutoff, the low since it, and today's close."""
    p = [x for x in px if x[0] <= day][-high_sessions:]
    if len(p) < 2:
        return None
    hi_i = max(range(len(p)), key=lambda i: p[i][1])
    after = p[hi_i:]
    lo_i = min(range(len(after)), key=lambda i: after[i][1])
    return {"high": p[hi_i], "low": after[lo_i], "today": p[-1],
            "sessions_since_low": len(after) - 1 - lo_i,
            "drawdown_pct": 100.0 * (p[-1][1] / p[hi_i][1] - 1.0)}


def family_short_interest(f: dict, series: dict, day: str, max_age: int) -> dict:
    from altdata import derived                                 # noqa: PLC0415
    si = series.get(f["key"]) or []
    if not si:
        return _gap(f, f"no rows ({f['key']}, {f['instrument']})")
    if not _fresh(si, day, 31):                                  # semi-monthly, a fortnight's lag
        return _gap(f, f"stale: last settlement {si[-1][0]}")
    if len(si) < int(f["min_prints"]):
        return _gap(f, f"accruing ({len(si)} of {f['min_prints']} prints)")
    pct = derived.percentile_of([v for _, v in si], si[-1][1])
    px = series.get(f["price_key"]) or []
    dd = drawdown_low(px, day, int(f["high_sessions"])) if _fresh(px, day, max_age) else None
    if dd is None:
        return _gap(f, f"no S&P 500 closes within the allowance ({f['price_key']})")
    br = series.get(f["breadth_key"]) or []
    at_low = _on_or_before(br, dd["low"][0])
    now = _on_or_before(br, day)
    if not at_low or not now:
        return _gap(f, f"no RSP/SPY at the low or today ({f['breadth_key']})")
    holds = dd["sessions_since_low"] >= int(f["hold_sessions"]) and dd["today"][1] > dd["low"][1]
    breadth = now[1] > at_low[1]
    ok = pct >= f["top_percentile"] and holds and breadth
    return _res(f, ok, f"short interest at its {ordinal(pct)} percentile; low {dd['low'][0]} "
                       f"{'held' if holds else 'not held'} ({dd['sessions_since_low']} sessions); "
                       f"RSP/SPY {'above' if breadth else 'not above'} its value at the low")


def family_flows(f: dict, series: dict, day: str, max_age: int) -> dict:
    if not f.get("flow_keys"):
        return _gap(f, "no fund-flow feed (SPY, QQQ, IWM, SMH and ICI are listed gaps; J4)")
    if not f.get("aaii_bearish_key"):
        return _gap(f, "AAII's bearish share is not stored (aaii.bull_bear_spread only)")
    weekly = []
    for k in f["flow_keys"]:
        weekly += series.get(k) or []
    flows = sorted(weekly)[-int(f["inflow_weeks"]):]
    bear = series.get(f["aaii_bearish_key"]) or []
    if len(flows) < int(f["inflow_weeks"]) or len(bear) < 3:
        return _gap(f, "accruing")
    inflow = all(v > 0 for _, v in flows)
    peak = max(v for _, v in bear[-8:])
    falling = bear[-1][1] < peak and peak > f["bearish_peak_above"]
    return _res(f, inflow and falling, f"flows {'in' if inflow else 'not in'} for {f['inflow_weeks']} weeks; "
                                         f"AAII bearish {bear[-1][1]:.1f}% against a peak of {peak:.1f}%")


FAMILIES = {"vix": family_vix, "put_call": family_put_call, "gamma": family_gamma,
            "short_interest": family_short_interest, "flows": family_flows}


def label(count: int, cfg: dict) -> str:
    for b in cfg["count"]["labels"]:
        if count >= int(b["at_least"]):
            return b["label"]
    return "none"


def keys_of(cfg: dict) -> list[tuple[str, Optional[str]]]:
    out: list[tuple[str, Optional[str]]] = [("fred.vix", None), ("fred.vix3m", None),
                                            ("calc.vix3m_over_vix", None)]
    pc = _fam(cfg, "put_call")
    out.append((pc["key"], None))
    g = _fam(cfg, "gamma")
    out += [(k, g["instrument"]) for k in g["keys"]]
    s = _fam(cfg, "short_interest")
    out += [(s["key"], s["instrument"]), (s["price_key"], None), (s["breadth_key"], None)]
    fl = _fam(cfg, "flows")
    out += [(k, None) for k in fl.get("flow_keys") or []]
    if fl.get("aaii_bearish_key"):
        out.append((fl["aaii_bearish_key"], None))
    return out


def load(st, cutoff: str, cfg: dict) -> dict:
    return {k: pts(st, k, cutoff, inst) for k, inst in keys_of(cfg)}


def score(series: dict, day: str, cfg: dict) -> dict:
    """The count for one session from points already cut to it."""
    max_age = int(cfg["count"]["max_age_days"])
    cut = {k: [x for x in v if x[0] <= day] for k, v in series.items()}
    fams = [FAMILIES[f["id"]](f, cut, day, max_age) for f in cfg["count"]["families"]]
    n = sum(1 for x in fams if x["state"] == "yes")
    k = sum(1 for x in fams if x["state"] != "gap")
    return {"day": day, "count": n, "scorable": k, "label": label(n, cfg), "families": fams}


def build(st, cutoff: str, cfg: Optional[dict] = None, prior_day: Optional[str] = None) -> dict:
    cfg = cfg or config()
    day = cutoff[:10]
    series = load(st, cutoff, cfg)
    now = score(series, day, cfg)
    if prior_day is None:
        from altdata import session                             # noqa: PLC0415
        prior_day = str(session.previous_trading_session(dt.date.fromisoformat(day)))
    prev = score(series, prior_day, cfg)
    now["prior"] = {"day": prior_day, "count": prev["count"], "scorable": prev["scorable"]}
    now["direction"] = ("up" if now["count"] > prev["count"] else
                        "down" if now["count"] < prev["count"] else "unchanged")
    return now


MARK = {"up": "▲", "down": "▼", "unchanged": "="}
TICK = {"yes": "✓", "no": "✗", "gap": "—"}


def count_line(c: dict) -> str:
    unreachable = "" if c["scorable"] >= 4 else f"; surrender unreachable at {c['scorable']} scorable"
    return (f"Capitulation Count {c['count']} of {c['scorable']} scorable ({c['label']}{unreachable}) "
            f"{MARK[c['direction']]} against {c['prior']['count']} on {c['prior']['day']}")


def family_lines(c: dict) -> list[str]:
    return [f"{TICK[f['state']]} {f['name']}: {f['reading']}" for f in c["families"]]


def tb_verdict() -> Optional[str]:
    """The T&B verdict, which no writer stores yet (CLAUDE.md: Top & Bottom is not
    built). Read here, never written; None until a writer exists."""
    return None


def table_3_caption(verdict: Optional[str], c: dict, cfg: dict) -> str:
    if verdict is None:
        return ("T&B verdict: not built (no writer stores it); the pair is the read, "
                "not the count alone (Appendix A, table 3)")
    for row in cfg["table_3"]:
        if row["verdict"] == verdict and row["band"] == c["label"]:
            return f"T&B {verdict} with the count {c['label']}: {row['read']}"
    return f"T&B {verdict} with the count {c['label']}: no row of table 3 reads this pair"


def close_wanted(c: dict, cfg: dict) -> bool:
    p = cfg["count"]["print"]
    return (p.get("close_on_change") and c["count"] != c["prior"]["count"]) or \
        c["count"] >= int(p["close_at_least"])


def weekly_wanted(st, cutoff: str, cfg: dict) -> Optional[dict]:
    p = cfg["count"]["print"]
    dd = drawdown_low(pts(st, p["index_key"], cutoff), cutoff[:10], 252)
    if dd and dd["drawdown_pct"] < -float(p["weekly_below_high_pct"]):
        return dd
    return None


# ---------------------------------------------------------------- 97(c)

def divergence(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    from altdata import derived                                 # noqa: PLC0415
    cfg = cfg or config()
    d = cfg["divergence"]
    day = cutoff[:10]
    vxn = dict(pts(st, d["vxn_key"], cutoff))
    vix = dict(pts(st, d["vix_key"], cutoff))
    spread = sorted((k, vxn[k] - vix[k]) for k in vxn.keys() & vix.keys())
    out: dict = {"day": day, "spread": None, "spread_pct": None, "sector_dd": None,
                 "index_dd": None, "flows": "not tracked", "exception": False}
    if spread:
        out["spread"] = spread[-1]
        win = [v for _, v in spread[-int(d["pct_sessions"]):]]
        if len(win) >= int(d["pct_sessions"]):
            out["spread_pct"] = derived.percentile_of(win, spread[-1][1])
    sdd = drawdown_low(pts(st, d["sector_key"], cutoff), day, int(d["high_sessions"]))
    idd = drawdown_low(pts(st, d["index_key"], cutoff), day, int(d["high_sessions"]))
    out["sector_dd"] = sdd["drawdown_pct"] if sdd else None
    out["index_dd"] = idd["drawdown_pct"] if idd else None
    return exception_of(out, d)


def exception_of(out: dict, d: dict) -> dict:
    hot = out["spread_pct"] is not None and out["spread_pct"] > float(d["spread_pct_above"])
    deep = (out["sector_dd"] is not None and out["index_dd"] is not None and out["index_dd"] < 0
            and out["sector_dd"] < float(d["drawdown_multiple"]) * out["index_dd"])
    out["exception"] = bool(hot or deep)
    return out


def divergence_line(v: dict) -> str:
    sp = (f"VXN less VIX {v['spread'][1]:+.2f} pts"
          + (f" ({ordinal(v['spread_pct'])} percentile, one year)" if v["spread_pct"] is not None
             else " (percentile accruing)")) if v["spread"] else "VXN less VIX not stored"
    dd = (f"SMH {v['sector_dd']:.1f}% from its 52-week high against the S&P 500's {v['index_dd']:.1f}%"
          if v["sector_dd"] is not None and v["index_dd"] is not None else "SMH's drawdown not stored")
    return f"Sector divergence: {sp}; {dd}; SMH flows {v['flows']}"


# ---------------------------------------------------------------- the ledger

def prereg_sha() -> str:
    return hashlib.sha256(PREREG.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def forward(px: list[tuple[str, float]], day: str, n: int) -> Optional[float]:
    i = next((j for j, (d, _) in enumerate(px) if d >= day), None)
    if i is None or px[i][0] != day or i + n >= len(px):
        return None
    return 100.0 * (px[i + n][1] / px[i][1] - 1.0)


def held(px: list[tuple[str, float]], day: str, n: int) -> Optional[bool]:
    i = next((j for j, (d, _) in enumerate(px) if d >= day), None)
    if i is None or px[i][0] != day or i + n >= len(px):
        return None
    return min(v for _, v in px[i + 1:i + n + 1]) >= px[i][1]


def ledger_rows(st, cfg: dict) -> list[dict]:
    led = cfg["ledger"]
    spx = pts(st, led["spx_key"], "9999-12-31")
    qqq = pts(st, led["ndx_proxy_key"], "9999-12-31")
    out = []
    for ep in led["episodes"]:
        day = ep["low"]
        series = load(st, f"{day}T23:59:00-04:00", cfg)
        c = score(series, day, cfg)
        fam = {f["id"]: f["state"] for f in c["families"]}
        for f in cfg["count"]["families"]:
            start = led["exists_from"].get(f["id"])
            if start is None or day < start:
                fam[f["id"]] = "not existent"
        n = sum(1 for v in fam.values() if v == "yes")
        k = sum(1 for v in fam.values() if v in ("yes", "no"))
        out.append({"episode": ep["id"], "kind": ep["kind"], "low": day,
                    "count": n, "scorable": k,
                    "four_or_more": n >= 4,
                    **{f"family_{k}": v for k, v in fam.items()},
                    "spx_20": forward(spx, day, 20), "spx_60": forward(spx, day, 60),
                    "qqq_20": forward(qqq, day, 20), "qqq_60": forward(qqq, day, 60),
                    "low_held_60": held(spx, day, 60)})
    return out


def verdict(rows: list[dict], rule: dict) -> str:
    usable = [r for r in rows if r["scorable"] >= int(rule["min_scorable"])]
    if len(usable) < int(rule["min_episodes"]):
        return f"INSUFFICIENT (n {len(usable)} episodes with {rule['min_scorable']} or more scorable families)"
    fired = [r for r in usable if r["four_or_more"]]
    held_fired = [r for r in fired if r["low_held_60"]]
    pos = [r for r in fired if (r["spx_60"] or 0) > 0]
    ok = (len(fired) >= int(rule["min_firings"])
          and len(held_fired) / len(fired) >= float(rule["held_share"])
          and len(pos) / len(fired) >= float(rule["positive_share"]))
    return ("PASS" if ok else "FAIL") + f" (n {len(usable)}, fired {len(fired)}, held {len(held_fired)}, +60 positive {len(pos)})"


def write_ledger(rows: list[dict], path: Path = LEDGER_CSV) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if v is None else (f"{v:.2f}" if isinstance(v, float) else v)) for k, v in r.items()})
    path.write_bytes(buf.getvalue().encode("utf-8"))
    return buf.getvalue()


# ---------------------------------------------------------------- CLI

class _ReadOnly:
    """The store opened mode=ro, with the one method the count reads."""

    def __init__(self, path: str):
        import sqlite3                                          # noqa: PLC0415
        self.conn = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
        self.conn.row_factory = sqlite3.Row

    def as_of(self, key, cutoff, instrument=None):
        q = ("SELECT observed_at, value_num FROM observations WHERE registry_key = ? "
             "AND available_at <= ? AND value_num IS NOT NULL")
        args = [key, cutoff if "T" in cutoff else f"{cutoff}T23:59:59"]
        if instrument is not None:
            q += " AND instrument = ?"
            args.append(instrument)
        return [dict(r) for r in self.conn.execute(q + " ORDER BY observed_at, available_at", args)]


def _main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="the Capitulation Count (item 97)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("--date")
    s.add_argument("--db", required=True)
    l = sub.add_parser("ledger")                                # noqa: E741
    l.add_argument("--db", required=True)
    l.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cfg = config()
    st = _ReadOnly(a.db)
    if a.cmd == "show":
        from altdata import session                             # noqa: PLC0415
        day = a.date or str(session.last_completed_session())
        c = build(st, f"{day}T23:59:00", cfg)
        print(count_line(c))
        for ln in family_lines(c):
            print("  " + ln)
        print("  " + table_3_caption(tb_verdict(), c, cfg))
        print("  " + divergence_line(divergence(st, f"{day}T23:59:00", cfg)))
        return 0
    rows = ledger_rows(st, cfg)
    print(f"pre-registration {PREREG.name} sha256 {prereg_sha()}")
    print(f"verdict: {verdict(rows, cfg['ledger']['rule'])}")
    if a.dry_run:
        print(json.dumps(rows, indent=1, default=str)[:4000])
        return 0
    write_ledger(rows)
    print(f"wrote {LEDGER_CSV.relative_to(ROOT).as_posix()} ({len(rows)} episodes)")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
