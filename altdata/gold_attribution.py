"""
Gold's five-lens attribution, the 60-day real-yield beta and the exhaustion
checklist (signal-triage Batch 16 items 87 and 88(a), (d); written as round 7's
80 and 81; ruled 25-26 Oct 2026; B75).

    python -m altdata.gold_attribution show [--date D]              # the session's read
    python -m altdata.gold_attribution backfill --dry-run           # counts, writes nothing
    python -m altdata.gold_attribution backfill                     # the stored history
    python -m altdata.gold_attribution ledger [--out FILE]          # the checklist's edition

THE TRIGGER (RULED: "every gold move > 2σ"). The move screen's own sigma and
window (altdata/move_screen.screen_points, config/move_screen.yaml): gold's 1- and
5-day log change as a z against its own five-year history of such changes. It
fires at |z| of 2 or more on either horizon; the lead horizon is the larger z's.

THE FIVE LENSES, each a stored measure read on the day, over the lead horizon:
  real yield    DFII10's change, bp
  breakeven     the 10-year breakeven's change, bp
  dollar        the ICE dollar index's change, %
  liquidation   gold's same-day correlation with the S&P 500 and the Nasdaq-100
                (QQQ, its tracking fund: no index key is stored) over 20 sessions,
                the day's own signs, and filed item 74's squeeze flag ("not
                stored": it is computed at read and stored under no key)
  official bid  the latest dated record the operator enters (config/
                gold_official_bid.yaml), "no record" otherwise; beside it the
                PBoC's monthly net purchase as the IMF IFS stores it
No lens is fitted and none is weighted: the lenses print side by side.

THE BETA: gold's daily log return (%) on DFII10's daily change (bp), OLS over the
last 60 sessions both store, with its window and n.

THE EXHAUSTION CHECKLIST: four tells over the week to the day (oil below $100;
the 10-year falling while oil rises; gold up on an equity-down day; the
liquidation correlation flipping sign). Ticked weekly in the Weekly block; a tell
that flips on a session puts a line in the daily close. Its ledger is pre-
registered (docs/ledgers/gold-exhaustion-preregistration-2026-10.md) and grants
nothing.

STORED (source gold_attribution): `gold.attr.<lens>` on a fired day (instrument
none, observed the day, a JSON body), and `gold.beta_real_60d` each session (a
JSON body: beta, n, window). Report rights only: nothing here enters a composite,
the market-state object, a dial or a packet.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Optional

from . import asset_event as ae

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "gold_attribution.yaml"
SOURCE = "gold_attribution"
LENSES = ("real_yield", "breakeven", "dollar", "liquidation", "official_bid")
ATTR_KEY = "gold.attr.{lens}"
BETA_KEY = "gold.beta_real_60d"
LENS_LABEL = {"real_yield": "Real yield (DFII10)", "breakeven": "Breakeven (10-year)",
              "dollar": "Dollar (DXY)", "liquidation": "Liquidation",
              "official_bid": "Official bid"}


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8"))


def official_records(cfg: dict, path: Optional[Path] = None) -> list[dict]:
    import yaml                                                 # noqa: PLC0415
    p = path or (REPO / cfg["official_bid_records"])
    try:
        recs = (yaml.safe_load(Path(p).read_text(encoding="utf-8")) or {}).get("records")
    except OSError:
        recs = None
    return sorted((r for r in recs or [] if r.get("date")), key=lambda r: str(r["date"]))


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------
def read_series(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    from . import st_r5_rates                                   # noqa: PLC0415
    cfg = cfg or config()
    out = {k: st_r5_rates._pts(st, key, cutoff) for k, key in cfg["keys"].items()}
    w = cfg["weekly"]
    for e in w["etf"]:
        out[e["key"]] = st_r5_rates._pts(st, e["key"], cutoff)
    out[w["holders_13f"]] = st_r5_rates._pts(st, w["holders_13f"], cutoff)
    out["cftc"] = st_r5_rates._pts(st, w["cftc"]["key"], cutoff, w["cftc"]["instrument"])
    out["official_records"] = official_records(cfg)
    return out


# ---------------------------------------------------------------------------
# Small pieces
# ---------------------------------------------------------------------------
def upto(pts: list[tuple[str, float]], day: str) -> list[tuple[str, float]]:
    return [(d, v) for d, v in pts if d <= day]


def log_returns(pts: list[tuple[str, float]]) -> dict[str, float]:
    """day -> the log change from the previous stored day, in percent."""
    out = {}
    for (d0, a), (d1, b) in zip(pts, pts[1:]):
        if a > 0 and b > 0:
            out[d1] = math.log(b / a) * 100.0
    return out


def diffs(pts: list[tuple[str, float]], scale: float = 1.0) -> dict[str, float]:
    return {d1: (b - a) * scale for (d0, a), (d1, b) in zip(pts, pts[1:])}


def corr(xs: list[float], ys: list[float]) -> Optional[float]:
    if len(xs) < 3:
        return None
    try:
        return statistics.correlation(xs, ys)
    except statistics.StatisticsError:
        return None


def paired(a: dict[str, float], b: dict[str, float], day: str, n: int
           ) -> tuple[list[float], list[float], list[str]]:
    """The last `n` days to `day` on which both series moved."""
    days = sorted(d for d in a if d in b and d <= day)[-n:]
    return [a[d] for d in days], [b[d] for d in days], days


# ---------------------------------------------------------------------------
# The trigger: the move screen's sigma and window, the order's 2
# ---------------------------------------------------------------------------
def trigger(gold: list[tuple[str, float]], day: str, cfg: dict,
            ms_cfg: Optional[dict] = None) -> dict:
    from . import move_screen                                   # noqa: PLC0415
    ms = dict(ms_cfg if ms_cfg is not None else move_screen.load_config())
    pts = upto(gold, day)
    if not pts or pts[-1][0] != day:
        return {"day": day, "fired": False, "state": "absent",
                "reason": f"no gold close stored for {day}"}
    sig = float(cfg["trigger"]["sigma"])
    ms["sigma"] = sig
    r = move_screen.screen_points(pts, "log", ms, horizons=cfg["trigger"]["horizons"])
    if r is None:
        return {"day": day, "fired": False, "state": "not read",
                "reason": (f"{len(pts)} closes stored, fewer than the move screen's "
                           f"{ms.get('min_observations') or 500}")}
    z1, z5 = r.get("z1"), r.get("z5")
    lead = r["lead_horizon"]
    ch = r.get(f"change{lead}")
    return {"day": day, "state": "read", "fired": bool(r["flagged"]), "sigma": sig,
            "z1": z1, "z5": z5, "lead": lead,
            "move_pct": None if ch is None else round(ch * 100.0, 2),
            "n_changes": r.get(f"n_changes{lead}")}


def trigger_text(tr: dict) -> str:
    if tr.get("state") != "read":
        return f"Gold: {tr.get('reason')}"
    zs = f"{tr['z1']:+.1f}σ on the day, {tr['z5']:+.1f}σ over five sessions" \
        if tr.get("z1") is not None and tr.get("z5") is not None else "z not read"
    if not tr["fired"]:
        return f"Gold: no 2σ move ({zs})"
    span = "on the day" if tr["lead"] == 1 else "over five sessions"
    return (f"Gold {tr['move_pct']:+.2f}% {span} (log), past {tr['sigma']:.0f}σ "
            f"({zs}; the move screen's five-year window, n={tr['n_changes']:,})")


# ---------------------------------------------------------------------------
# The lenses
# ---------------------------------------------------------------------------
def liquidation(series: dict, day: str, cfg: dict) -> dict:
    lq = cfg["liquidation"]
    g = log_returns(upto(series.get("gold") or [], day))
    out: dict[str, Any] = {"lens": "liquidation", "window": int(lq["window"]),
                           "squeeze": cfg["not_stored"]["squeeze"]}
    if not g:
        out.update(state="not stored", reason="no gold close stored")
        return out
    legs = {}
    for name, sid in (("S&P 500", "spx"), ("Nasdaq-100 (QQQ)", "ndx")):
        e = log_returns(upto(series.get(sid) or [], day))
        if not e:
            legs[name] = {"state": "not stored", "reason": f"{cfg['keys'][sid]} not stored"}
            continue
        xs, ys, days = paired(g, e, day, int(lq["window"]))
        c = corr(xs, ys) if len(xs) >= int(lq["min_pairs"]) else None
        legs[name] = ({"state": "computed", "corr": round(c, 2), "n": len(xs),
                       "from": days[0], "to": days[-1],
                       "same_day": ("both down" if g.get(day, 0) < 0 and e.get(day, 0) < 0
                                    else "both up" if g.get(day, 0) > 0 and e.get(day, 0) > 0
                                    else "apart")}
                      if c is not None else
                      {"state": "absent", "reason": f"{len(xs)} paired sessions, fewer "
                                                    f"than {lq['min_pairs']}"})
    out["legs"] = legs
    out["state"] = ("computed" if any(v["state"] == "computed" for v in legs.values())
                    else "absent")
    return out


def liquidation_text(x: dict) -> str:
    parts = []
    for name, v in (x.get("legs") or {}).items():
        if v["state"] == "computed":
            parts.append(f"{name} {v['corr']:+.2f} ({v['n']} sessions; {v['same_day']} "
                         f"on the day)")
        else:
            parts.append(f"{name} {v['state']} ({v.get('reason')})")
    if not parts:
        parts.append(x.get("reason") or "not stored")
    return ("correlation with " + "; ".join(parts)
            + f"; the hedge-fund squeeze flag {x['squeeze']}")


def official_bid(series: dict, day: str, cfg: dict) -> dict:
    recs = [r for r in series.get("official_records") or [] if str(r["date"]) <= day]
    ifs = upto(series.get("official_ifs_china") or [], day)
    out: dict[str, Any] = {"lens": "official_bid"}
    out["record"] = ({k: recs[-1].get(k) for k in ("date", "source", "figure", "outlet",
                                                    "url")} if recs else None)
    out["ifs_china"] = ({"month": ifs[-1][0][:7],
                         "tonnes": round(ifs[-1][1] / float(cfg["oz_per_tonne"]), 1)}
                        if ifs else None)
    out["state"] = "computed" if (recs or ifs) else "no record"
    return out


def official_text(x: dict) -> str:
    r = x.get("record")
    a = (f"{r['source']} {r['figure']} ({r.get('outlet') or r['source']}, {r['date']})"
         if r else "no record")
    i = x.get("ifs_china")
    b = (f"; the PBoC's net purchase as the IMF IFS stores it {i['tonnes']:+,.1f} t in "
         f"{i['month']}" if i else "; the IMF IFS's China series not stored")
    return a + b


def lenses(series: dict, tr: dict, cfg: dict) -> dict:
    day, h = tr["day"], int(tr["lead"])
    gold = upto(series.get("gold") or [], day)
    start = gold[-1 - h][0] if len(gold) > h else gold[0][0]
    tol = int(cfg["start_tolerance_days"])
    out: dict[str, Any] = {"start": start, "end": day, "horizon": h}
    for lens, sid, unit in (("real_yield", "real_yield", "bp"),
                            ("breakeven", "breakeven", "bp"), ("dollar", "dollar", "pct")):
        pts = series.get(sid) or []
        if not pts:
            out[lens] = {"lens": lens, "state": "not stored",
                         "reason": f"{cfg['keys'][sid]} not stored"}
            continue
        out[lens] = dict(ae.leg_change(pts, start, day, unit, tol), lens=lens,
                         key=cfg["keys"][sid])
    out["liquidation"] = liquidation(series, day, cfg)
    out["official_bid"] = official_bid(series, day, cfg)
    return out


def lens_text(lens: str, x: dict) -> str:
    if lens == "liquidation":
        return liquidation_text(x)
    if lens == "official_bid":
        return official_text(x)
    if x["state"] == "not stored":
        return f"not stored ({x['reason']})"
    return ae.leg_text("", x).strip()


def lenses_line(att: dict) -> str:
    span = f"{att['horizon']} session" + ("s" if att["horizon"] != 1 else "")
    return (f"The five lenses over {span} from {att['start']}: "
            + "; ".join(f"{LENS_LABEL[k].lower()} {lens_text(k, att[k])}" for k in LENSES)
            + ".")


# ---------------------------------------------------------------------------
# The beta
# ---------------------------------------------------------------------------
def beta(series: dict, day: str, cfg: dict) -> dict:
    b = cfg["beta"]
    g = log_returns(upto(series.get("gold") or [], day))
    r = diffs(upto(series.get("real_yield") or [], day), 100.0)
    if not g or not r:
        return {"state": "not stored", "window": int(b["window"]), "n": 0,
                "reason": "gold or DFII10 not stored"}
    ys, xs, days = paired(g, r, day, int(b["window"]))
    if len(xs) < int(b["min_pairs"]):
        return {"state": "absent", "window": int(b["window"]), "n": len(xs),
                "reason": f"{len(xs)} paired sessions, fewer than {b['min_pairs']}"}
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    if vx == 0:
        return {"state": "absent", "window": int(b["window"]), "n": len(xs),
                "reason": "the real yield did not move"}
    bb = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / vx
    return {"state": "computed", "beta": round(bb, 4), "n": len(xs),
            "window": int(b["window"]), "from": days[0], "to": days[-1]}


def beta_text(b: dict) -> str:
    if b["state"] != "computed":
        return f"The 60-day beta of gold to the real yield: {b['state']} ({b.get('reason')})."
    return (f"The 60-day beta of gold to the real yield: {b['beta']:+.3f}% a basis point "
            f"(OLS of gold's daily log return on DFII10's daily change, {b['n']} sessions "
            f"from {b['from']} to {b['to']}).")


# ---------------------------------------------------------------------------
# The exhaustion checklist
# ---------------------------------------------------------------------------
def _week(pts: list[tuple[str, float]], day: str, n: int) -> list[tuple[str, float]]:
    return upto(pts, day)[-(n + 1):]


def tells(series: dict, day: str, cfg: dict) -> dict:
    """tell id -> {state: ticked | clear | not stored, reading}."""
    ex = cfg["exhaustion"]
    n = int(ex["week_sessions"])
    out: dict[str, dict] = {}
    brent = upto(series.get("brent") or [], day)
    out["oil_below_100"] = ({"state": "not stored"} if not brent else
                            {"state": "ticked" if brent[-1][1] < float(ex["oil_below"])
                             else "clear",
                             "reading": f"Brent ${brent[-1][1]:,.2f} on {brent[-1][0]}"})
    y10, bw = _week(series.get("yield_10y") or [], day, n), _week(brent, day, n)
    if len(y10) < 2 or len(bw) < 2:
        out["ten_falling_oil_rising"] = {"state": "not stored"}
    else:
        dy = (y10[-1][1] - y10[0][1]) * 100.0
        do = (bw[-1][1] / bw[0][1] - 1.0) * 100.0
        out["ten_falling_oil_rising"] = {
            "state": "ticked" if dy < 0 and do > 0 else "clear",
            "reading": f"the 10-year {dy:+.0f} bp, Brent {do:+.2f}% over the week"}
    g = log_returns(upto(series.get("gold") or [], day))
    e = log_returns(upto(series.get("spx") or [], day))
    gdays = sorted(d for d in g if d <= day)[-n:]
    if not gdays or not e:
        out["gold_up_equity_down"] = {"state": "not stored"}
    else:
        hits = [d for d in gdays if d in e and g[d] > 0 and e[d] < 0]
        out["gold_up_equity_down"] = {
            "state": "ticked" if hits else "clear",
            "reading": (f"gold up and the S&P 500 down on {', '.join(hits)}" if hits
                        else f"no such session in the {len(gdays)} to {day}")}
    lq = cfg["liquidation"]
    now_c = then_c = None
    if g and e:
        xs, ys, days = paired(g, e, day, int(lq["window"]))
        now_c = corr(xs, ys) if len(xs) >= int(lq["min_pairs"]) else None
        prior = gdays[0] if len(gdays) >= n else None
        prev = sorted(d for d in g if prior and d < prior)
        if prev:
            xs, ys, _ = paired(g, e, prev[-1], int(lq["window"]))
            then_c = corr(xs, ys) if len(xs) >= int(lq["min_pairs"]) else None
    if now_c is None or then_c is None:
        out["liquidation_flip"] = {"state": "not stored" if not (g and e) else "absent"}
    else:
        out["liquidation_flip"] = {
            "state": "ticked" if (now_c > 0) != (then_c > 0) else "clear",
            "reading": f"gold's 20-session correlation with the S&P 500 {then_c:+.2f} a "
                       f"week before, {now_c:+.2f} now"}
    return out


def tells_line(t: dict, cfg: dict) -> str:
    lab = {x["id"]: x["label"] for x in cfg["exhaustion"]["tells"]}
    parts = []
    for tid, x in t.items():
        mark = {"ticked": "ticked", "clear": "clear"}.get(x["state"], x["state"])
        parts.append(f"{lab[tid]}: {mark}" + (f" ({x['reading']})" if x.get("reading") else ""))
    k = sum(1 for x in t.values() if x["state"] == "ticked")
    return f"Exhaustion checklist, {k} of {len(t)} ticked: " + "; ".join(parts) + "."


def flipped(series: dict, day: str, cfg: dict) -> list[str]:
    """The tells whose state changed from the previous stored session's."""
    gold = upto(series.get("gold") or [], day)
    if len(gold) < 2 or gold[-1][0] != day:
        return []
    now, then = tells(series, day, cfg), tells(series, gold[-2][0], cfg)
    return [k for k in now if now[k]["state"] in ("ticked", "clear")
            and then[k]["state"] in ("ticked", "clear")
            and now[k]["state"] != then[k]["state"]]


# ---------------------------------------------------------------------------
# One session
# ---------------------------------------------------------------------------
def evaluate(series: dict, day: str, cfg: Optional[dict] = None,
             ms_cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    tr = trigger(series.get("gold") or [], day, cfg, ms_cfg)
    out: dict[str, Any] = {"day": day, "trigger": tr, "fired": tr["fired"],
                           "beta": beta(series, day, cfg)}
    if tr["fired"]:
        out["lenses"] = lenses(series, tr, cfg)
    return out


def close_line(series: dict, day: str, cfg: Optional[dict] = None,
               ms_cfg: Optional[dict] = None) -> Optional[dict]:
    """The daily close's gold line (item 88(d)): only when the 2σ trigger fires
    or an exhaustion tell flips; None otherwise."""
    cfg = cfg or config()
    ev = evaluate(series, day, cfg, ms_cfg)
    fl = flipped(series, day, cfg)
    if not ev["fired"] and not fl:
        return None
    parts = []
    if ev["fired"]:
        parts += [trigger_text(ev["trigger"]) + ".", lenses_line(ev["lenses"])]
    if fl:
        lab = {x["id"]: x["label"] for x in cfg["exhaustion"]["tells"]}
        t = tells(series, day, cfg)
        parts.append("Exhaustion tell flipped: " + "; ".join(
            f"{lab[k]} now {t[k]['state']}" + (f" ({t[k]['reading']})"
                                               if t[k].get("reading") else "")
            for k in fl) + ".")
    parts.append("Report only: no composite, no market-state input (item 87).")
    return {"event": ev, "flipped": fl, "line": " ".join(parts)}


# ---------------------------------------------------------------------------
# The rows
# ---------------------------------------------------------------------------
def rows_for(ev: dict, now: str) -> list[dict]:
    """The beta's row for the session, and the five lenses' on a fired day."""
    out = []
    day = ev["day"]
    if ev["beta"]["state"] == "computed":
        out.append({"registry_key": BETA_KEY, "instrument": None, "observed_at": day,
                    "available_at": now, "source": SOURCE,
                    "value": json.dumps(ev["beta"], sort_keys=True)})
    if ev.get("fired"):
        att = ev["lenses"]
        for lens in LENSES:
            body = {"day": day, "horizon": att["horizon"], "start": att["start"],
                    "trigger": ev["trigger"], "lens": att[lens]}
            out.append({"registry_key": ATTR_KEY.format(lens=lens), "instrument": None,
                        "observed_at": day, "available_at": now, "source": SOURCE,
                        "value": json.dumps(body, sort_keys=True, default=str)})
    return out


def backfill(series: dict, cfg: dict, now: str, ms_cfg: Optional[dict] = None,
             since: Optional[str] = None) -> dict:
    """Every stored gold session's rows, each read with only what came before it
    (the series to the day). The rows' available_at is the compute instant, so
    nothing is backdated."""
    rows, fired = [], 0
    for d, _ in series.get("gold") or []:
        if since and d < since:
            continue
        ev = evaluate(series, d, cfg, ms_cfg)
        fired += int(bool(ev["fired"]))
        rows += rows_for(ev, now)
    return {"rows": rows, "fired": fired}


# ---------------------------------------------------------------------------
# The checklist's ledger (pre-registered; docs/ledgers/)
# ---------------------------------------------------------------------------
def week_ends(gold: list[tuple[str, float]]) -> list[str]:
    """The last stored session of each ISO week."""
    by: dict[tuple, str] = {}
    for d, _ in gold:
        y, w, _ = dt.date.fromisoformat(d).isocalendar()
        by[(y, w)] = d
    return [by[k] for k in sorted(by)]


def ledger_weeks(series: dict, cfg: dict) -> list[dict]:
    gold = series.get("gold") or []
    fw = [int(x) for x in cfg["exhaustion"]["forward_sessions"]]
    out = []
    for d in week_ends(gold):
        t = tells(series, d, cfg)
        f = ae.forward(gold, d, fw, None, "gold")
        out.append({"week": d, **{k: v["state"] for k, v in t.items()},
                    **{f"gold_{n}d_pct": f.get(f"gold_{n}d_pct") for n in fw}})
    return out


def ledger_stats(weeks: list[dict], cfg: dict, min_n: int = 30, t_min: float = 2.0
                 ) -> dict:
    """Per tell: the ticked weeks' mean forward +20-session gold return against the
    clear weeks', with a Welch t; INSUFFICIENT under `min_n` ticked or clear weeks
    with a +20 reading. The +5 and +60 print beside and decide nothing."""
    out = {}
    for tl in cfg["exhaustion"]["tells"]:
        tid = tl["id"]
        row: dict[str, Any] = {"label": tl["label"]}
        for n in cfg["exhaustion"]["forward_sessions"]:
            k = f"gold_{int(n)}d_pct"
            a = [w[k] for w in weeks if w[tid] == "ticked" and w[k] is not None]
            b = [w[k] for w in weeks if w[tid] == "clear" and w[k] is not None]
            row[f"{n}d"] = {"ticked_n": len(a), "clear_n": len(b),
                            "ticked_mean": round(statistics.fmean(a), 2) if a else None,
                            "clear_mean": round(statistics.fmean(b), 2) if b else None}
        a = [w["gold_20d_pct"] for w in weeks if w[tid] == "ticked"
             and w["gold_20d_pct"] is not None]
        b = [w["gold_20d_pct"] for w in weeks if w[tid] == "clear"
             and w["gold_20d_pct"] is not None]
        if len(a) < min_n or len(b) < min_n:
            row["verdict"], row["t"] = "INSUFFICIENT", None
        else:
            se = math.sqrt(statistics.variance(a) / len(a) + statistics.variance(b) / len(b))
            t = (statistics.fmean(a) - statistics.fmean(b)) / se if se else 0.0
            row["t"] = round(t, 2)
            row["verdict"] = "PASS" if t >= t_min else "FAIL"
        out[tid] = row
    return out


def ledger_md(weeks: list[dict], stats: dict, cfg: dict, as_of: str,
              prereg_sha: str) -> str:
    lines = [f"# The gold exhaustion checklist's ledger, first edition ({as_of[:10]})", "",
             f"*Written by `python -m altdata.gold_attribution ledger` from the store as "
             f"of {as_of}. Never edited: a later edition is a new dated file. The pass "
             f"rule is the pre-registration's "
             f"(`{cfg['exhaustion']['preregistration']}`, SHA-256 `{prereg_sha}`), "
             f"committed before this edition was computed.*", "",
             f"**Window:** the stored gold history, {len(weeks)} weeks"
             + (f" ({weeks[0]['week']} to {weeks[-1]['week']})." if weeks else "."),
             "", "**The statistic:** per tell, the mean +20-session gold return after a "
             "ticked week less after a clear week, Welch t. PASS at t of 2.0 or more with "
             "at least 30 weeks on each side; INSUFFICIENT below; FAIL otherwise. The +5 "
             "and +60 sessions print beside and decide nothing.", "",
             "| Tell | Ticked n (+20) | Clear n (+20) | Ticked +5 / +20 / +60 | "
             "Clear +5 / +20 / +60 | t | Verdict |", "|---|---:|---:|---|---|---:|---|"]

    def m(row, side):
        return " / ".join("—" if row[f"{n}d"][f"{side}_mean"] is None
                          else f"{row[f'{n}d'][f'{side}_mean']:+.2f}%"
                          for n in cfg["exhaustion"]["forward_sessions"])
    for tid, row in stats.items():
        lines.append(f"| {row['label']} | {row['20d']['ticked_n']} | "
                     f"{row['20d']['clear_n']} | {m(row, 'ticked')} | {m(row, 'clear')} | "
                     f"{'—' if row['t'] is None else row['t']} | {row['verdict']} |")
    lines += ["", "**Rights:** none. A PASS reaches the register only as a rule-31 "
              "draft; the checklist stays report-only either way.", ""]
    return "\n".join(lines)


def prereg_sha(cfg: dict) -> str:
    """The pre-registration's SHA-256 over its LF bytes (a Windows checkout
    writes CRLF; the registered bytes are the committed LF ones)."""
    import hashlib                                              # noqa: PLC0415
    raw = (REPO / cfg["exhaustion"]["preregistration"]).read_bytes()
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from . import observations, session                         # noqa: PLC0415
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m altdata.gold_attribution")
    ap.add_argument("cmd", choices=["show", "backfill", "ledger"])
    ap.add_argument("--date")
    ap.add_argument("--db")
    ap.add_argument("--since")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    cfg = config()
    now = session.utc_iso()
    with observations.ObservationStore(a.db) as st:
        series = read_series(st, now, cfg)
        if a.cmd == "show":
            day = a.date or ((series.get("gold") or [(None, None)])[-1][0])
            if not day:
                print("Gold: not stored.")
                return 0
            ev = evaluate(series, day, cfg)
            print(trigger_text(ev["trigger"]))
            if ev["fired"]:
                print(lenses_line(ev["lenses"]))
            print(beta_text(ev["beta"]))
            print(tells_line(tells(series, day, cfg), cfg))
            cl = close_line(series, day, cfg)
            print("Close line: " + (cl["line"] if cl else "none (a quiet day)"))
            return 0
        if a.cmd == "backfill":
            out = backfill(series, cfg, now, since=a.since)
            print(f"sessions read: {len(series.get('gold') or [])}; fired days: "
                  f"{out['fired']}; rows {'that would be ' if a.dry_run else ''}"
                  f"written: {len(out['rows'])}")
            if not a.dry_run and out["rows"]:
                st.write_many(out["rows"])
            return 0
        weeks = ledger_weeks(series, cfg)
        sha = prereg_sha(cfg)
        md = ledger_md(weeks, ledger_stats(weeks, cfg), cfg, now, sha)
        if a.out:
            Path(a.out).write_text(md, encoding="utf-8")
            print(f"written: {a.out} ({len(weeks)} weeks)")
        else:
            print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
