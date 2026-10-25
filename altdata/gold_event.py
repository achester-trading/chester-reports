"""
The gold event trigger and its attribution, with its own event ledger (signal-
triage Batch 15 item 73, written as 66; ST-R6.73a; ruled 23 Oct 2026 with filing
amendments G1-G6; a58-batch15-1). Item 52's event pattern applied to gold.

    python -m altdata.gold_event show [--date D]          # the session's read
    python -m altdata.gold_event resolve [--dry-run]      # awaiting legs and outcomes
    python -m altdata.gold_event history [--write] [--out FILE]   # the first edition

THE TRIGGER (RULED): gold's one-day move of 2.5% or more either way, or its 5-day
move beyond its 95th percentile. The five-day move is a log change, two-sided, and
its percentile is over the five years of sessions before the day (a57's flag
window), nearest rank. Gold is the series item 38 and AQ-8a already read (GC=F).

THE ATTRIBUTION, over the trigger's horizon (one session when the one-day arm
fires, else five): the real 10-year (DFII10), DXY and Brent, each its change; gold-
ETF flows "not tracked" (item 72's WGC line failed its source check); the central-
bank trend from the IMF IFS series the system stores; and one residual line, which
counts the read legs that moved the way the order's mechanism ties to the move's
sign and attributes the rest to nothing. No leg is fitted.

THE LEDGER (`gold.event_ledger`, instrument = the day): the trigger, the legs and
gold's realised change over the next 5 and 20 sessions. The close writes a row on
a fired day; `resolve` (the EOD pass) writes later vintages; `history` builds the
first edition from the stored series only, and says per row where its history is
short.

FLAGS ONLY: nothing here enters a composite or the market-state object.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, Optional

from . import asset_event as ae

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "gold_event.yaml"
LEDGER_KEY = "gold.event_ledger"
SOURCE = "gold_event"
TITLE = "Gold event"


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# The trigger
# ---------------------------------------------------------------------------
def five_cache(gold: list[tuple[str, float]], cfg: dict) -> dict:
    """Every close's five-day |log change|, %, computed once (the history pass)."""
    n5 = int(cfg["trigger"]["five_day_sessions"])
    return {"days": [d for d, _ in gold], "vals": [v for _, v in gold],
            "abs5": [abs(math.log(gold[i][1] / gold[i - n5][1]) * 100.0) if i >= n5 else None
                     for i in range(len(gold))]}


def trigger(gold: list[tuple[str, float]], day: str, cfg: dict,
            cache: Optional[dict] = None) -> dict:
    """Both arms on `day`, from the series up to and including it."""
    import bisect                                               # noqa: PLC0415
    t = cfg["trigger"]
    if cache is None:
        cache = five_cache([(d, v) for d, v in gold if d <= day], cfg)
    days, vals = cache["days"], cache["vals"]
    i = bisect.bisect_right(days, day) - 1
    if i < 1 or days[i] != day:
        return {"fired": False, "state": "absent",
                "line": f"Gold: no close stored for {day}"}
    one = (vals[i] / vals[i - 1] - 1.0) * 100.0
    one_fired = abs(one) >= float(t["one_day_pct"])
    n5 = int(t["five_day_sessions"])
    out: dict[str, Any] = {"day": day, "one_day_pct": round(one, 2), "one_day_fired": one_fired}
    if i < n5:
        out.update(five_day_state="not read", five_day_reason="fewer than six closes stored",
                   five_day_fired=False)
    else:
        five = math.log(vals[i] / vals[i - n5]) * 100.0
        start = ae.years_back(day, int(t["window_years"]))
        lo = max(bisect.bisect_right(days, start), n5)
        hist = cache["abs5"][lo:i]
        out["five_day_log_pct"] = round(five, 2)
        out["five_day_n"] = len(hist)
        out["five_day_short"] = bool(days[0] > start)
        if len(hist) < int(t["min_history"]):
            out.update(five_day_state="not read", five_day_fired=False,
                       five_day_reason=f"history short: {len(hist)} prior five-day changes, "
                                       f"fewer than {t['min_history']}")
        else:
            q = ae.threshold(hist, float(t["five_day_percentile"]))
            out.update(five_day_state="read", five_day_threshold=round(q, 2),
                       five_day_fired=abs(five) > q)
    out["fired"] = bool(out["one_day_fired"] or out["five_day_fired"])
    out["horizon"] = 1 if out["one_day_fired"] else n5
    out["move_pct"] = (out["one_day_pct"] if out["one_day_fired"] else
                       out.get("five_day_log_pct"))
    out["line"] = trigger_line(out, cfg)
    return out


def trigger_line(tr: dict, cfg: dict) -> str:
    t = cfg["trigger"]
    if not tr.get("fired"):
        return f"Gold: no event ({tr.get('one_day_pct', 0):+.2f}% on the day)"
    arms = []
    if tr["one_day_fired"]:
        arms.append(f"{tr['one_day_pct']:+.2f}% on the day (the ±{t['one_day_pct']}% arm)")
    if tr["five_day_fired"]:
        arms.append(f"{tr['five_day_log_pct']:+.2f}% over five sessions (log), beyond its "
                    f"95th percentile of {tr['five_day_threshold']:.2f}% on five years "
                    f"(n={tr['five_day_n']:,})")
    return "Gold event: " + "; ".join(arms)


# ---------------------------------------------------------------------------
# The attribution
# ---------------------------------------------------------------------------
def central_bank_trend(pts: list[tuple[str, float]], day: str, cfg: dict) -> dict:
    c = cfg["central_banks"]
    m = int(c["months"])
    known = [(d, v) for d, v in pts if d <= day]
    if len(known) < 2 * m:
        return {"state": "absent",
                "reason": f"{len(known)} months stored, fewer than {2 * m}"}
    oz = float(c["oz_per_tonne"])
    last = sum(v for _, v in known[-m:]) / oz
    prior = sum(v for _, v in known[-2 * m:-m]) / oz
    return {"state": "computed", "as_of": known[-1][0], "last_t": round(last, 1),
            "prior_t": round(prior, 1),
            "direction": "rising" if last > prior else "falling" if last < prior else "flat"}


def attribute(series: dict, tr: dict, cfg: dict) -> dict:
    gold = [(d, v) for d, v in series["gold"] if d <= tr["day"]]
    h = int(tr["horizon"])
    start = gold[-1 - h][0]
    tol = int(cfg.get("start_tolerance_days") or 4)
    legs = []
    for lg in cfg["legs"]:
        r = ae.leg_change(series.get(lg["id"]) or [], start, tr["day"], lg["unit"], tol)
        legs.append(dict(r, id=lg["id"], label=lg["label"],
                         gold_against=bool(lg.get("gold_against"))))
    legs.append({"id": "etf_flows", "label": "Gold-ETF flows", "state": "not tracked",
                 "reason": cfg["etf_flows_gap"]})
    cb = central_bank_trend(series.get("central_banks") or [], tr["day"], cfg)
    legs.append(dict(cb, id="central_banks", label=cfg["central_banks"]["label"]))
    return {"start": start, "end": tr["day"], "horizon": h, "legs": legs,
            "residual": residual(legs, tr["move_pct"]),
            "state": ("awaiting" if any(x["state"] == "awaiting" for x in legs
                                        if x["id"] in {lg["id"] for lg in cfg["legs"]})
                      else "computed")}


def residual(legs: list[dict], move: Optional[float]) -> str:
    """How many read legs moved the way the order's mechanism ties to this move."""
    read = [x for x in legs if x.get("gold_against") and x["state"] == "computed"]
    if not read or not move:
        return "Residual: no market leg is read yet, so none of the move is attributed."
    with_ = [x["label"].split(" (")[0] for x in read
             if x["change"] != 0 and (x["change"] > 0) != (move > 0)]
    return (f"Residual: {len(with_)} of {len(read)} read legs moved the way the order's "
            f"mechanism ties to a gold move this way"
            + (f" ({', '.join(with_)})" if with_ else "")
            + "; no leg is fitted, so the rest of the move is not attributed.")


def leg_cell(x: dict) -> str:
    if x["id"] == "central_banks" and x["state"] == "computed":
        return (f"{x['direction']}: {x['last_t']:,.0f} t in the 12 months to {x['as_of'][:7]} "
                f"against {x['prior_t']:,.0f} t the 12 before")
    if x["state"] == "computed":
        return ae.leg_text("", x).strip()
    if x["state"] == "not tracked":
        return x["reason"]
    if x["state"] == "awaiting":
        return f"awaiting (stored through {x.get('stored_through') or 'nothing'})"
    return f"absent ({x.get('reason')})"


def table(att: dict) -> dict:
    return {"columns": ["Leg", f"Change over {att['horizon']} session"
                        + ("s" if att["horizon"] != 1 else "") + f" from {att['start']}"],
            "rows": [[x["label"], leg_cell(x)] for x in att["legs"]]}


def evaluate(series: dict, day: str, cfg: Optional[dict] = None,
             cache: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    tr = trigger(series.get("gold") or [], day, cfg, cache)
    out: dict[str, Any] = {"day": day, "fired": tr["fired"], "trigger": tr, "line": tr["line"]}
    if not tr["fired"]:
        return out
    att = attribute(series, tr, cfg)
    out.update(attribution=att, table=table(att), state=att["state"],
               line=tr["line"] + ". " + att["residual"])
    return out


def block(ev: dict) -> Optional[dict]:
    if not ev.get("fired"):
        return None
    return {"title": TITLE, "table": ev.get("table"), "paragraph_wanted": False,
            "lines": [ev["line"], "A flag: no composite, no market-state input (item 73)."]}


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------
def read_series(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    from . import st_r5_rates                                   # noqa: PLC0415
    cfg = cfg or config()
    out = {"gold": st_r5_rates._pts(st, cfg["gold_key"], cutoff),
           "central_banks": st_r5_rates._pts(st, cfg["central_banks"]["key"], cutoff)}
    for lg in cfg["legs"]:
        out[lg["id"]] = st_r5_rates._pts(st, lg["key"], cutoff)
    return out


def for_session(st, day: str, cutoff: str, cfg: Optional[dict] = None) -> dict:
    return evaluate(read_series(st, cutoff, cfg), day, cfg)


def body(ev: dict, gold: list[tuple[str, float]], cfg: dict,
         note: Optional[str] = None) -> dict:
    tr, att = ev["trigger"], ev.get("attribution") or {}
    b = {"day": ev["day"], "trigger": {k: tr.get(k) for k in (
            "one_day_pct", "one_day_fired", "five_day_log_pct", "five_day_threshold",
            "five_day_n", "five_day_state", "five_day_reason", "five_day_fired",
            "five_day_short", "horizon", "move_pct")},
         "state": att.get("state"), "start": att.get("start"), "legs": att.get("legs"),
         "residual": att.get("residual"),
         "outcomes": ae.forward(gold, ev["day"], cfg["forward_sessions"],
                                tr.get("move_pct"), "gold")}
    if note:
        b["history_note"] = note
    return b


def ledger_row(ev: dict, gold: list[tuple[str, float]], now: str,
               cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    return ae.ledger_row(LEDGER_KEY, ev["day"], ev["day"], body(ev, gold, cfg), now, SOURCE)


def resolve_rows(bodies: dict[str, dict], series: dict, cfg: dict, now: str) -> list[dict]:
    out = []
    for day, b in bodies.items():
        if (b.get("outcomes") or {}).get("resolved") and b.get("state") == "computed":
            continue
        ev = evaluate(series, day, cfg)
        if not ev["fired"]:
            continue
        new = body(ev, series["gold"], cfg, b.get("history_note"))
        if new != b:
            out.append(ae.ledger_row(LEDGER_KEY, day, day, new, now, SOURCE))
    return out


def history(series: dict, cfg: dict) -> list[dict]:
    """Every fired day in the stored series, each read with only what came before
    it; a row whose five-day window is short says so."""
    out = []
    cache = five_cache(series["gold"], cfg)
    for d, _ in series["gold"][1:]:
        ev = evaluate(series, d, cfg, cache)
        if not ev["fired"]:
            continue
        tr = ev["trigger"]
        note = None
        if tr.get("five_day_state") != "read":
            note = f"five-day arm not read: {tr.get('five_day_reason')}"
        elif tr.get("five_day_short"):
            note = (f"five-day percentile on {tr['five_day_n']:,} prior changes: the stored "
                    f"history is shorter than five years")
        out.append(body(ev, series["gold"], cfg, note))
    return out


def edition(bodies: list[dict], cutoff: str) -> str:
    lines = [f"# Gold event ledger, first edition (item 73, ST-R6.73a), stored history to {cutoff}",
             "", f"{len(bodies)} fired days. From the store only; a row whose history is "
             "short says so.", "", "| Day | Trigger | Horizon | Legs read | Gold +5d | Gold +20d | Note |",
             "|---|---|---|---|---|---|---|"]
    for b in bodies:
        t, oc = b["trigger"], b["outcomes"]
        arm = (f"{t['one_day_pct']:+.2f}% 1d" if t["one_day_fired"] else
               f"{t['five_day_log_pct']:+.2f}% 5d")
        read = sum(1 for x in b.get("legs") or [] if x["state"] == "computed")
        f5, f20 = oc.get("gold_5d_pct"), oc.get("gold_20d_pct")
        lines.append(f"| {b['day']} | {arm} | {t['horizon']} | {read} | "
                     f"{'—' if f5 is None else f'{f5:+.2f}%'} | "
                     f"{'—' if f20 is None else f'{f20:+.2f}%'} | {b.get('history_note') or ''} |")
    return "\n".join(lines) + "\n"


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from . import observations, session                         # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.gold_event")
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
            print(edition(bodies, now[:10]) if not a.out else f"{len(bodies)} fired days")
            if a.out:
                Path(a.out).expanduser().write_text(edition(bodies, now[:10]), encoding="utf-8")
            if a.write:
                st.write_many([ae.ledger_row(LEDGER_KEY, b["day"], b["day"], b, now, SOURCE)
                               for b in bodies])
                print(f"written: {len(bodies)} ledger rows")
            return 0
    day = a.date or (series["gold"][-1][0] if series["gold"] else now[:10])
    ev = evaluate(series, day, cfg)
    print(ev["line"])
    for r in (ev.get("table") or {}).get("rows") or []:
        print("  " + " | ".join(str(x) for x in r))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
