"""
The 10-year attribution on speed-flag days, and its event ledger (signal-triage
Batch 14 item 65, written as 58; ST-R6.65a; ruled 20 Oct 2026 with filing
amendments F1-F8; a57-batch14-b1). Item 52's event pattern
(altdata/vol_event.py), applied to rates.

    python -m altdata.speed_attribution show [--date D]     # the session's read
    python -m altdata.speed_attribution seed --date D       # a ledger row by hand
    python -m altdata.speed_attribution resolve             # attribution and outcomes

THE TRIGGER is the speed flag as it stands: SR-35, the move screen's 10-year
companion (altdata/move_screen.companion_10y) -- the two-week or one-month change
at 2 sigma on a twenty-year window. The screen's own stored result is read; it is
computed in memory only where none is stored, exactly as the reports read it.

THE ATTRIBUTION, over the flag's lead horizon (the larger |z| of the two): each
term-structure model's change in the 10-year term premium against the 10-year's
own change, in basis points, the remainder being expected short rates. A model
"carried" the move on the term premium when its premium share exceeds one half,
on expected short rates when it falls short (rates_attribution's definition;
not a tuned threshold). The models that are read and lean the same way name the
leg; when they disagree the line says so.

F5: A MODEL IS READ ONLY WHEN ITS OBSERVATION ON THE FLAG DAY IS STORED. A model
publishes after the yield does, so on the day the read is usually "awaiting",
and `resolve` (the EOD pass, after vol_event's) writes the attribution once the
inputs land -- a new vintage of the ledger row, never an overwrite.

THE LEDGER (`rates.speed_event_ledger`, instrument = the flag day): the trigger,
the attribution and the 10-year's realised change over the next 5 and 20
sessions. Its pre-registration is docs/ledgers/speed-attribution-preregistration-
2026-10.md.

RIGHTS: none new. The speed flag keeps its rights; this is a report. Nothing here
enters a composite or the market-state object.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "speed_attribution.yaml"
LEDGER_KEY = "rates.speed_event_ledger"
SOURCE = "speed_attribution"
TITLE = "10-year speed flag: what carried the move"


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# The trigger
# ---------------------------------------------------------------------------
def trigger(screen: Optional[dict]) -> dict:
    """SR-35's companion, as the screen holds it: fired when printed, with its lead
    horizon (the larger |z| of the two-week and one-month changes)."""
    comp = (screen or {}).get("companion_10y") or {}
    zs = {int(k[1:]): v for k, v in comp.items()
          if k.startswith("z") and k[1:].isdigit() and v is not None}
    if not comp.get("printed") or not zs:
        return {"fired": False, "line": comp.get("line")}
    h = max(zs, key=lambda k: abs(zs[k]))
    return {"fired": True, "horizon": h, "z": zs[h], "line": comp.get("line"),
            "zs": zs}


# ---------------------------------------------------------------------------
# The attribution
# ---------------------------------------------------------------------------
def _at_or_before(pts: list[tuple[str, float]], day: str) -> Optional[tuple[str, float]]:
    best = None
    for d, v in pts:
        if d <= day:
            best = (d, v)
        else:
            break
    return best


def attribute(series: dict, day: str, horizon: int, cfg: dict) -> dict:
    """The split of the 10-year's move over `horizon` sessions to `day`, per model.
    `series` holds "yield" and each model id, as sorted [(day, percent)]."""
    y = [(d, v) for d, v in series.get("yield") or [] if d <= day]
    if not y or y[-1][0] != day or len(y) <= horizon:
        return {"state": "absent", "models": [],
                "line": f"the 10-year is not stored on {day} with {horizon} sessions "
                        f"before it"}
    start, y0, y1 = y[-1 - horizon][0], y[-1 - horizon][1], y[-1][1]
    move = (y1 - y0) * 100.0
    tol = int(cfg.get("start_tolerance_days") or 4)
    rows, awaiting = [], []
    for m in cfg["models"]:
        pts = series.get(m["id"]) or []
        end = _at_or_before(pts, day)
        if not end or end[0] != day:
            awaiting.append(f"{m['label']} (stored through {end[0] if end else 'nothing'})")
            rows.append({"model": m["id"], "label": m["label"], "state": "awaiting",
                         "stored_through": end[0] if end else None})
            continue
        beg = _at_or_before(pts, start)
        if not beg or (dt.date.fromisoformat(start)
                       - dt.date.fromisoformat(beg[0])).days > tol:
            rows.append({"model": m["id"], "label": m["label"], "state": "absent",
                         "reason": f"no {m['label']} observation within {tol} days "
                                   f"before {start}"})
            continue
        tp = (end[1] - beg[1]) * 100.0
        row: dict[str, Any] = {"model": m["id"], "label": m["label"], "state": "computed",
                               "as_of": end[0], "premium_bp": round(tp, 1),
                               "path_bp": round(move - tp, 1)}
        if abs(move) < 1e-9:
            row.update(carried="no move", premium_share=None)
        else:
            share = tp / move
            row.update(premium_share=round(share, 2),
                       carried=("the term premium" if share > 0.5 else
                                "expected short rates" if share < 0.5 else "neither leg"))
        rows.append(row)
    read = [r for r in rows if r["state"] == "computed"]
    if not read:
        state = "awaiting"
        verdict = ("awaiting the term-structure models' inputs for " + day + ": "
                   + "; ".join(awaiting or [r.get("reason") or r["label"] for r in rows]))
    else:
        legs = {r["carried"] for r in read}
        names = " and ".join(r["label"] for r in read)
        if len(legs) == 1:
            leg = legs.pop()
            verdict = (f"{leg} carried the move "
                       f"({names}{' agree' if len(read) > 1 else ''})")
        else:
            verdict = "the models disagree: " + "; ".join(
                f"{r['label']} {r['carried']}" for r in read)
        if awaiting:
            verdict += "; awaiting " + ", ".join(awaiting)
        state = "computed" if not awaiting else "partial"
    return {"state": state, "start": start, "end": day, "horizon": horizon,
            "move_bp": round(move, 1), "models": rows, "line": verdict}


def table(att: dict) -> dict:
    rows = []
    for r in att.get("models") or []:
        if r["state"] == "computed":
            rows.append([r["label"], f"{att['move_bp']:+.0f} bp",
                         f"{r['path_bp']:+.0f} bp", f"{r['premium_bp']:+.0f} bp",
                         "—" if r["premium_share"] is None else f"{r['premium_share']:.2f}",
                         r["carried"], r["as_of"]])
        else:
            rows.append([r["label"], f"{att.get('move_bp', 0):+.0f} bp", "—", "—", "—",
                         ("awaiting (stored through " + str(r.get("stored_through"))
                          + ")") if r["state"] == "awaiting" else r.get("reason"), "—"])
    return {"columns": ["Model (nominal 10-year)", "10-year move", "Expected short rates",
                        "Term premium", "Premium share", "Carried", "As of"],
            "rows": rows}


def evaluate(series: dict, screen: Optional[dict], day: str,
             cfg: Optional[dict] = None) -> dict:
    cfg = cfg or config()
    tr = trigger(screen)
    out: dict[str, Any] = {"day": day, "fired": tr["fired"], "trigger": tr}
    if not tr["fired"]:
        return out
    att = attribute(series, day, tr["horizon"], cfg)
    out.update(attribution=att, table=table(att), state=att["state"],
               line=(f"The 10-year speed flag ({tr['line']}): over {tr['horizon']} "
                     f"sessions from {att.get('start')}, {att['line']}."
                     if att["state"] != "absent" else
                     f"The 10-year speed flag ({tr['line']}): {att['line']}."))
    return out


def block(ev: dict) -> Optional[dict]:
    """The Mechanics sub-section on a flag day, else None (silent)."""
    if not ev.get("fired"):
        return None
    return {"title": TITLE, "table": ev.get("table"), "paragraph_wanted": False,
            "lines": [ev["line"], "A report: the speed flag's rights stand, and none "
                                  "is added (F5)."]}


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------
def read_series(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    from . import st_r5_rates                                   # noqa: PLC0415
    cfg = cfg or config()
    out = {"yield": st_r5_rates._pts(st, cfg["yield_key"], cutoff)}
    for m in cfg["models"]:
        out[m["id"]] = st_r5_rates._pts(st, m["key"], cutoff)
    return out


def for_session(st, day: str, cutoff: str, screen: Optional[dict] = None,
                cfg: Optional[dict] = None) -> dict:
    """The session's read: the stored move screen (else computed in memory, as the
    reports read it), then the attribution on a flag day."""
    if screen is None:
        from . import move_screen                               # noqa: PLC0415
        screen = move_screen.result_for(st, day, cutoff)
    return evaluate(read_series(st, cutoff, cfg), screen, day, cfg)


def outcomes(day: str, yld: list[tuple[str, float]], move_bp: Optional[float],
             cfg: Optional[dict] = None) -> dict:
    """The 10-year's realised change over the next 5 and 20 sessions, bp; a horizon
    not yet stored is None. `continued` is the change's sign against the move's."""
    cfg = cfg or config()
    days = [d for d, _ in yld]
    vals = dict(yld)
    out: dict[str, Any] = {}
    if day not in vals:
        for f in cfg["forward_sessions"]:
            out[f"y10_{int(f)}d_bp"] = None
        out["resolved"] = False
        return out
    i = days.index(day)
    for f in cfg["forward_sessions"]:
        f = int(f)
        out[f"y10_{f}d_bp"] = (round((vals[days[i + f]] - vals[day]) * 100.0, 1)
                               if i + f < len(days) else None)
    last = out.get(f"y10_{int(cfg['forward_sessions'][-1])}d_bp")
    out["continued"] = (None if last is None or not move_bp else
                        (last > 0) == (move_bp > 0) and last != 0)
    out["resolved"] = all(out[f"y10_{int(f)}d_bp"] is not None
                          for f in cfg["forward_sessions"])
    return out


def ledger_row(ev: dict, now: str, oc: Optional[dict] = None) -> dict:
    att = ev.get("attribution") or {}
    body = {"day": ev["day"], "horizon": ev["trigger"].get("horizon"),
            "z": ev["trigger"].get("z"), "trigger_line": ev["trigger"].get("line"),
            "state": att.get("state"), "move_bp": att.get("move_bp"),
            "start": att.get("start"),
            "models": att.get("models"), "verdict": att.get("line"), "outcomes": oc}
    return {"registry_key": LEDGER_KEY, "instrument": ev["day"], "observed_at": ev["day"],
            "available_at": now, "value": json.dumps(body, sort_keys=True, default=str),
            "source": SOURCE}


def resolve_rows(bodies: list[dict], series: dict, cfg: dict, now: str) -> list[dict]:
    """A new vintage for each ledger row whose attribution was awaiting and is now
    readable, or whose outcomes moved; nothing for a row that is unchanged."""
    out = []
    for body in bodies:
        if (body.get("outcomes") or {}).get("resolved") and body.get("state") == "computed":
            continue
        new = dict(body)
        if body.get("state") in ("awaiting", "partial") and body.get("horizon"):
            att = attribute(series, body["day"], int(body["horizon"]), cfg)
            if att["state"] in ("computed", "partial"):
                new.update(state=att["state"], move_bp=att["move_bp"], start=att["start"],
                           models=att["models"], verdict=att["line"])
        new["outcomes"] = outcomes(body["day"], series.get("yield") or [],
                                   new.get("move_bp"), cfg)
        if new != body:
            out.append({"registry_key": LEDGER_KEY, "instrument": body["day"],
                        "observed_at": body["day"], "available_at": now,
                        "value": json.dumps(new, sort_keys=True, default=str),
                        "source": SOURCE})
    return out


def _latest_bodies(st, cutoff: str) -> list[dict]:
    by: dict[str, dict] = {}
    for r in st.as_of(LEDGER_KEY, cutoff):
        try:
            by[str(r["instrument"])] = json.loads(r["value_text"])
        except (TypeError, ValueError):
            continue
    return [by[k] for k in sorted(by)]


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from . import observations, session                         # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.speed_attribution")
    ap.add_argument("cmd", choices=["show", "seed", "resolve"])
    ap.add_argument("--date", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    cfg = config()
    now = session.utc_iso()
    day = a.date or session.session_date()
    if a.cmd == "resolve":
        with observations.ObservationStore() as st:
            rows = resolve_rows(_latest_bodies(st, now), read_series(st, now, cfg), cfg, now)
            if rows and not a.dry_run:
                st.write_many(rows)
        print(f"resolved rows {'that would be ' if a.dry_run else ''}written: {len(rows)}")
        return 0
    with observations.ObservationStore() as st:
        ev = for_session(st, day, now, cfg=cfg)
    if not ev["fired"]:
        print(f"{day}: the speed flag did not fire"
              + (f" ({ev['trigger']['line']})" if ev["trigger"].get("line") else ""))
        return 0 if a.cmd == "show" else 1
    print(ev["line"])
    for r in ev["table"]["rows"]:
        print("  " + " | ".join(str(x) for x in r))
    if a.cmd == "seed":
        with observations.ObservationStore() as st:
            ser = read_series(st, now, cfg)
            row = ledger_row(ev, now, outcomes(day, ser["yield"],
                                               ev["attribution"].get("move_bp"), cfg))
            if not a.dry_run:
                st.write_many([row])
        print(f"{'would seed' if a.dry_run else 'seeded'} {LEDGER_KEY} for {day}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
