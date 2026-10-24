"""
The developed-market equity drawdown screen and its event ledger (signal-triage
Batch 15 item 73, written as 66; ST-R6.73b; ruled 23 Oct 2026 with filing
amendments G1-G6; a58-batch15-1). Item 10's shock screen -- SR-46's EM screen in
altdata/move_screen.py -- extended to the indices source check 2 found.

    python -m altdata.dm_drawdown show [--date D]
    python -m altdata.dm_drawdown resolve [--dry-run]
    python -m altdata.dm_drawdown history [--write] [--out FILE]

THE TRIGGER (RULED): an index's 10- or 20-session drawdown beyond its 95th
percentile. The drawdown is the close's fall from the window's highest close, %;
the percentile is over the five years of sessions before the day (a57's flag
window), nearest rank. Nikkei 225 is FRED's; KOSPI and TAIEX are "ETF proxy"
reads of the country ETFs the store already holds; TOPIX, DAX, CAC 40 and FTSE 100
have no keyless source and print as listed gaps, each by name.

THE ATTRIBUTION, over the window that fired: the local currency, the local 10-year
where a daily keyless series is stored (else "not tracked"), the prior US
session's move, and for Japan the yen carry stack (SR-2) and SR-32's stored early
line; KOSPI and TAIEX also print item 63's capex-chain line.

THE LEDGER (`equity.dm_drawdown_ledger`, instrument = "<index>:<day>").

FLAGS ONLY: nothing here enters a composite or the market-state object.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

from . import asset_event as ae

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "dm_drawdown.yaml"
LEDGER_KEY = "equity.dm_drawdown_ledger"
SOURCE = "dm_drawdown"
TITLE = "Developed-market drawdown"


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8"))


def drawdown(vals: list[float], i: int, n: int) -> Optional[float]:
    """The fall of close i from the highest close of i-n..i, % (0 at a high)."""
    if i < n:
        return None
    peak = max(vals[i - n:i + 1])
    return round((1.0 - vals[i] / peak) * 100.0, 4) if peak else None


def dd_cache(pts: list[tuple[str, float]], cfg: dict) -> dict:
    """Every close's drawdown per window, computed once (the history pass)."""
    vals = [v for _, v in pts]
    return {"days": [d for d, _ in pts],
            **{int(n): [drawdown(vals, j, int(n)) for j in range(len(vals))]
               for n in cfg["trigger"]["windows"]}}


def trigger(pts: list[tuple[str, float]], day: str, cfg: dict,
            cache: Optional[dict] = None) -> dict:
    import bisect                                               # noqa: PLC0415
    t = cfg["trigger"]
    if cache is None:
        pts = [(d, v) for d, v in pts if d <= day]
        cache = dd_cache(pts, cfg)
    days = cache["days"]
    i = bisect.bisect_right(days, day) - 1
    if i < 0 or days[i] != day:
        return {"fired": False, "state": "absent", "windows": {}}
    start = ae.years_back(day, int(t["window_years"]))
    lo = bisect.bisect_right(days, start)
    wins: dict[int, dict] = {}
    for n in t["windows"]:
        n = int(n)
        dd = cache[n][i]
        hist = [x for x in cache[n][max(lo, n):i] if x is not None]
        w: dict[str, Any] = {"drawdown_pct": dd, "n": len(hist),
                             "short": bool(days[0] > start)}
        if dd is None or len(hist) < int(t["min_history"]):
            w.update(state="not read", fired=False,
                     reason=f"history short: {len(hist)} prior {n}-session drawdowns, "
                            f"fewer than {t['min_history']}")
        else:
            q = ae.threshold(hist, float(t["percentile"]))
            w.update(state="read", threshold_pct=round(q, 2), fired=dd > 0 and dd > q)
        wins[n] = w
    fired = [n for n, w in wins.items() if w["fired"]]
    return {"day": day, "fired": bool(fired), "windows": wins,
            "lead": max(fired) if fired else None, "state": "read"}


def _cell(label: str, r: dict) -> list[str]:
    return [label, ae.leg_text("", r).strip() if r["state"] == "computed" else
            (r["reason"] if r["state"] == "not tracked" else
             f"awaiting (stored through {r.get('stored_through') or 'nothing'})"
             if r["state"] == "awaiting" else f"absent ({r.get('reason')})")]


def _level(pts: list[tuple[str, float]], day: str, kind: str) -> dict:
    p = ae.on_or_before(pts, day)
    if not p:
        return {"state": "absent", "reason": "not stored"}
    if kind == "flag":
        txt = "on" if p[1] >= 1 else "off"
    elif kind == "level_bp":
        txt = f"{p[1]:+.0f} bp"
    else:
        txt = f"{p[1]:.2f}%"
    return {"state": "level", "text": f"{txt} ({p[0]})"}


def attribute(series: dict, m: dict, tr: dict, cfg: dict) -> dict:
    pts = [(d, v) for d, v in series[m["id"]] if d <= tr["day"]]
    n = int(tr["lead"])
    start = pts[-1 - n][0]
    tol = int(cfg.get("start_tolerance_days") or 4)
    rows: list[list[str]] = []
    legs: dict[str, dict] = {}
    cur = ae.leg_change(series.get(f"{m['id']}:ccy") or [], start, tr["day"], "pct", tol)
    legs["currency"] = cur
    rows.append(_cell(m["currency"]["label"] + (" (inside the proxy's dollar return)"
                                                if m.get("proxy") else ""), cur))
    if m.get("local_10y"):
        r = ae.leg_change(series.get(f"{m['id']}:10y") or [], start, tr["day"], "bp", tol)
        rows.append(_cell(m["local_10y"]["label"], r))
    else:
        r = {"state": "not tracked", "reason": m["local_10y_gap"]}
        rows.append(["Local 10-year", r["reason"]])
    legs["local_10y"] = r
    us = series.get("us") or []
    p1 = ae.before(us, tr["day"])
    p0 = ae.before(us, p1[0]) if p1 else None
    if p1 and p0 and p0[1]:
        u = {"state": "computed", "change": round((p1[1] / p0[1] - 1) * 100, 2), "unit": "pct",
             "to": p1[0]}
        rows.append([cfg["us_session"]["label"] + f" ({p1[0]})", f"{u['change']:+.2f}%"])
    else:
        u = {"state": "absent", "reason": "no US session stored before the day"}
        rows.append([cfg["us_session"]["label"], "absent (no US session stored before the day)"])
    legs["us_session"] = u
    if m.get("japan"):
        for c in cfg["japan"]["carry"]:
            lv = _level(series.get(c["key"]) or [], tr["day"], c["kind"])
            legs[c["key"]] = lv
            rows.append([c["label"], lv.get("text") or f"absent ({lv.get('reason')})"])
        sm = cfg["japan"]["slow_money"]
        r = ae.leg_change(series.get(sm["key"]) or [], start, tr["day"], "bp", tol)
        legs["slow_money"] = r
        rows.append(_cell(sm["label"], r))
    if m.get("capex_chain"):
        cc = series.get("capex_chain_line")
        rows.append(["AI capex chain (item 63)", cc or "absent (the capex-chain line is not read)"])
        legs["capex_chain"] = {"state": "level" if cc else "absent", "text": cc}
    return {"start": start, "end": tr["day"], "window": n, "legs": legs,
            "table": {"columns": ["Leg", f"Over {n} sessions from {start}"], "rows": rows},
            "state": "awaiting" if any(isinstance(x, dict) and x.get("state") == "awaiting"
                                       for x in legs.values()) else "computed"}


def evaluate(series: dict, day: str, cfg: Optional[dict] = None) -> dict:
    """Every index's read on `day`, and the gaps by name."""
    cfg = cfg or config()
    out: dict[str, Any] = {"day": day, "events": [], "quiet": [], "gaps": list(cfg["gaps"].values())}
    for m in cfg["indices"]:
        tr = trigger(series.get(m["id"]) or [], day, cfg)
        if not tr["fired"]:
            out["quiet"].append({"id": m["id"], "state": tr["state"]})
            continue
        w = tr["windows"][tr["lead"]]
        att = attribute(series, m, tr, cfg)
        line = (f"{m['label']} ({m['source_label']}): down {w['drawdown_pct']:.1f}% from its "
                f"{tr['lead']}-session high, beyond its 95th percentile of "
                f"{w['threshold_pct']:.1f}% on five years (n={w['n']:,})")
        out["events"].append({"id": m["id"], "label": m["label"], "trigger": tr,
                              "attribution": att, "line": line})
    out["fired"] = bool(out["events"])
    return out


def block(ev: dict) -> Optional[dict]:
    if not ev.get("fired"):
        return None
    rows = []
    for e in ev["events"]:
        rows += [[e["label"]] + r for r in e["attribution"]["table"]["rows"]]
    return {"title": TITLE, "paragraph_wanted": False,
            "table": {"columns": ["Index", "Leg", "Change"], "rows": rows},
            "lines": [e["line"] + "." for e in ev["events"]]
                     + ["A flag: no composite, no market-state input (item 73)."],
            "not_tracked": ev["gaps"]}


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------
def read_series(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    from . import st_r5_rates                                   # noqa: PLC0415
    cfg = cfg or config()
    p = st_r5_rates._pts
    out = {"us": p(st, cfg["us_session"]["key"], cutoff)}
    for m in cfg["indices"]:
        out[m["id"]] = p(st, m["key"], cutoff)
        out[f"{m['id']}:ccy"] = p(st, m["currency"]["key"], cutoff)
        if m.get("local_10y"):
            out[f"{m['id']}:10y"] = p(st, m["local_10y"]["key"], cutoff)
    for c in cfg["japan"]["carry"]:
        out[c["key"]] = p(st, c["key"], cutoff)
    out[cfg["japan"]["slow_money"]["key"]] = p(st, cfg["japan"]["slow_money"]["key"], cutoff)
    try:
        from . import capex_chain                               # noqa: PLC0415
        cl = capex_chain.relative_lines(capex_chain.relative(st, cutoff))
        out["capex_chain_line"] = cl[0] if cl else None
    except Exception:                                           # noqa: BLE001
        out["capex_chain_line"] = None
    return out


def for_session(st, day: str, cutoff: str, cfg: Optional[dict] = None) -> dict:
    return evaluate(read_series(st, cutoff, cfg), day, cfg)


def body(e: dict, series: dict, cfg: dict, note: Optional[str] = None) -> dict:
    tr, att = e["trigger"], e["attribution"]
    w = tr["windows"][tr["lead"]]
    b = {"index": e["id"], "day": tr["day"], "window": tr["lead"],
         "windows": {str(k): v for k, v in tr["windows"].items()},
         "state": att["state"], "start": att["start"], "legs": att["legs"],
         "outcomes": ae.forward(series[e["id"]], tr["day"], cfg["forward_sessions"],
                                -1.0, "index")}
    # "continued" reads a further fall: the move's sign is negative.
    if w.get("short") and not note:
        note = (f"percentile on {w['n']:,} prior drawdowns: the stored history is shorter "
                f"than five years")
    if note:
        b["history_note"] = note
    return b


def ledger_rows(ev: dict, series: dict, now: str, cfg: Optional[dict] = None) -> list[dict]:
    cfg = cfg or config()
    return [ae.ledger_row(LEDGER_KEY, f"{e['id']}:{ev['day']}", ev["day"],
                          body(e, series, cfg), now, SOURCE) for e in ev["events"]]


def resolve_rows(bodies: dict[str, dict], series: dict, cfg: dict, now: str) -> list[dict]:
    out = []
    for inst, b in bodies.items():
        if (b.get("outcomes") or {}).get("resolved") and b.get("state") == "computed":
            continue
        ev = evaluate(series, b["day"], cfg)
        e = next((x for x in ev["events"] if x["id"] == b["index"]), None)
        if not e:
            continue
        new = body(e, series, cfg, b.get("history_note"))
        if new != b:
            out.append(ae.ledger_row(LEDGER_KEY, inst, b["day"], new, now, SOURCE))
    return out


def history(series: dict, cfg: dict) -> list[dict]:
    """Every fired (index, day) in the stored series, each read with only what came
    before it; a row whose history is short says so."""
    out = []
    for m in cfg["indices"]:
        pts = series.get(m["id"]) or []
        cache = dd_cache(pts, cfg)
        for d, _ in pts:
            tr = trigger(pts, d, cfg, cache)
            if not tr["fired"]:
                continue
            att = attribute(series, m, tr, cfg)
            out.append(body({"id": m["id"], "trigger": tr, "attribution": att}, series, cfg))
    return out


def edition(bodies: list[dict], cutoff: str, gaps: list[str]) -> str:
    lines = [f"# Developed-market drawdown ledger, first edition (item 73, ST-R6.73b), "
             f"stored history to {cutoff}", "",
             f"{len(bodies)} fired index-days. From the store only; a row whose history is "
             "short says so.", "", "Not screened: " + "; ".join(gaps), "",
             "| Index | Day | Window | Drawdown | Index +5d | Index +20d | Note |",
             "|---|---|---|---|---|---|---|"]
    for b in bodies:
        w, oc = b["windows"][str(b["window"])], b["outcomes"]
        f5, f20 = oc.get("index_5d_pct"), oc.get("index_20d_pct")
        lines.append(f"| {b['index']} | {b['day']} | {b['window']} | {w['drawdown_pct']:.1f}% | "
                     f"{'—' if f5 is None else f'{f5:+.2f}%'} | "
                     f"{'—' if f20 is None else f'{f20:+.2f}%'} | {b.get('history_note') or ''} |")
    return "\n".join(lines) + "\n"


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from . import observations, session                         # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.dm_drawdown")
    ap.add_argument("cmd", choices=["show", "resolve", "history"])
    ap.add_argument("--date", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    cfg = config()
    now = session.utc_iso()
    with observations.ObservationStore() as st:
        series = read_series(st, now, cfg)
        if a.cmd == "resolve":
            rows = resolve_rows(ae.latest_bodies(st, LEDGER_KEY, now), series, cfg, now)
            if rows and not a.dry_run:
                st.write_many(rows)
            print(f"resolved rows {'that would be ' if a.dry_run else ''}written: {len(rows)}")
            return 0
        if a.cmd == "history":
            bodies = history(series, cfg)
            text = edition(bodies, now[:10], list(cfg["gaps"].values()))
            print(text if not a.out else f"{len(bodies)} fired index-days")
            if a.out:
                Path(a.out).expanduser().write_text(text, encoding="utf-8")
            if a.write:
                st.write_many([ae.ledger_row(LEDGER_KEY, f"{b['index']}:{b['day']}", b["day"],
                                             b, now, SOURCE) for b in bodies])
                print(f"written: {len(bodies)} ledger rows")
            return 0
    day = a.date or now[:10]
    ev = evaluate(series, day, cfg)
    if not ev["fired"]:
        print(f"{day}: no developed-market drawdown event")
    for e in ev["events"]:
        print(e["line"])
        for r in e["attribution"]["table"]["rows"]:
            print("  " + " | ".join(str(x) for x in r))
    for g in ev["gaps"]:
        print("  " + g)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
