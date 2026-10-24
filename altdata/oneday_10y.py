"""
The one-day 10-year trigger and its event ledger (rulings of 24 Oct 2026, D15;
b59-trigger-sources). The speed flag's attribution (altdata/speed_attribution.py),
run over one session when the 10-year's one-day move is extreme.

    python -m altdata.oneday_10y show [--date D]     # the session's read
    python -m altdata.oneday_10y seed --date D       # a ledger row by hand
    python -m altdata.oneday_10y resolve             # attribution and outcomes

THE TRIGGER: on a Treasury session D, the 10-year's one-day change (FRED DGS10,
the change from the stored observation before D, in bp) against the absolute
one-day changes ending on the stored days before D within five years. It fires
when the absolute change is greater than that window's 97.5th percentile (linear
interpolation, derived.percentile_at), on either sign; with fewer than 1,000
changes in the window it is not read.

THE ATTRIBUTION is speed_attribution.attribute() over one session: each
term-structure model's (KW, ACM) change in the 10-year term premium against the
10-year's move, read only with an observation on D (F5); "awaiting" for a model
whose input for the day is not stored yet. `resolve` (the EOD pass, after the
speed flag's) writes the attribution once the inputs land, and the 10-year's 5-
and 20-session outcomes, each a new vintage of the ledger row.

THE LEDGER (`rates.oneday_event_ledger`, instrument = the trigger day). Its
pre-registration is docs/ledgers/oneday-10y-preregistration-2026-10.md.

RIGHTS: none. A report; nothing here enters a composite or the market-state
object, and the speed flag's own rights and ledger stand apart.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "oneday_10y.yaml"
LEDGER_KEY = "rates.oneday_event_ledger"
SOURCE = "oneday_10y"
TITLE = "10-year one-day move: what carried it"
BLOCK_TITLE = "10-year one-day moves"


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8"))


def _sa_cfg() -> dict:
    from . import speed_attribution as sa                       # noqa: PLC0415
    return sa.config()


# ---------------------------------------------------------------------------
# The trigger
# ---------------------------------------------------------------------------
def _years_back(day: str, years: int) -> str:
    d = dt.date.fromisoformat(day)
    try:
        return d.replace(year=d.year - years).isoformat()
    except ValueError:                                          # 29 February
        return d.replace(year=d.year - years, day=28).isoformat()


def one_day_changes(y: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Each stored day's change from the stored observation before it, in bp."""
    return [(y[i][0], (y[i][1] - y[i - 1][1]) * 100.0) for i in range(1, len(y))]


def trigger(y: list[tuple[str, float]], day: str, cfg: Optional[dict] = None,
            changes: Optional[list[tuple[str, float]]] = None) -> dict:
    """The trigger on `day`: {state, fired, change_bp, threshold_bp, n, from}.
    `state` is "computed", "absent" (no observation on the day) or "not read"
    (under the minimum of prior changes)."""
    from . import derived                                       # noqa: PLC0415
    cfg = cfg or config()
    t = cfg["trigger"]
    ch = changes if changes is not None else one_day_changes(sorted(y))
    today = next((v for d, v in ch if d == day), None)
    if today is None:
        return {"state": "absent", "fired": False, "day": day,
                "line": f"the 10-year has no one-day change stored on {day}"}
    lo = _years_back(day, int(t["window_years"]))
    window = [abs(v) for d, v in ch if lo < d < day]
    if len(window) < int(t["min_changes"]):
        return {"state": "not read", "fired": False, "day": day, "n": len(window),
                "change_bp": round(today, 1),
                "line": f"not read: {len(window)} one-day changes in the five years "
                        f"before {day} (the trigger needs {int(t['min_changes'])})"}
    thr = derived.percentile_at(window, float(t["percentile"]))
    fired = abs(today) > thr
    return {"state": "computed", "fired": fired, "day": day,
            "change_bp": round(today, 1), "threshold_bp": round(thr, 1),
            "n": len(window), "from": next(d for d, _ in ch if lo < d),
            "percentile": float(t["percentile"]),
            "line": (f"{today:+.0f} bp on the day, beyond its five-year threshold "
                     f"of {thr:.1f} bp ({_pct_words(t['percentile'])} of one-day "
                     f"moves were smaller; n={len(window):,})")}


def _pct_words(p: Any) -> str:
    """'97.5%': the threshold's percentile as a share, never a hand-written
    ordinal (the numeral audit's rule)."""
    return f"{float(p):g}%"


# ---------------------------------------------------------------------------
# The read
# ---------------------------------------------------------------------------
def evaluate(series: dict, day: str, cfg: Optional[dict] = None,
             sa_cfg: Optional[dict] = None, changes=None) -> dict:
    """The session's read: the trigger, and on a trigger day the attribution
    over one session ("awaiting" legs where a model's input is not stored)."""
    from . import speed_attribution as sa                       # noqa: PLC0415
    cfg = cfg or config()
    tr = trigger(series.get("yield") or [], day, cfg, changes)
    out: dict[str, Any] = {"day": day, "fired": tr["fired"], "trigger": tr}
    if not tr["fired"]:
        return out
    att = sa.attribute(series, day, 1, sa_cfg or _sa_cfg())
    out.update(attribution=att, table=sa.table(att), state=att["state"],
               line=f"The 10-year one-day trigger ({tr['line']}): {att['line']}.")
    return out


def flag_line(ev: dict) -> Optional[str]:
    """The close's one line on a trigger day, else None (silent)."""
    return ev["line"] if ev.get("fired") else None


def read_series(st, cutoff: str) -> dict:
    from . import speed_attribution as sa                       # noqa: PLC0415
    return sa.read_series(st, cutoff)


def for_session(st, day: str, cutoff: str, cfg: Optional[dict] = None) -> dict:
    return evaluate(read_series(st, cutoff), day, cfg)


def period_events(series: dict, first: str, last: str, cfg: Optional[dict] = None
                  ) -> tuple[list[dict], int]:
    """Every trigger day from `first` to `last` stored, and the sessions read."""
    cfg = cfg or config()
    sa_cfg = _sa_cfg()
    y = sorted(series.get("yield") or [])
    ch = one_day_changes(y)
    days = [d for d, _ in ch if first <= d <= last]
    evs = [e for e in (evaluate(series, d, cfg, sa_cfg, ch) for d in days) if e["fired"]]
    return evs, len(days)


def _leg(att: dict) -> str:
    read = [m for m in att.get("models") or [] if m["state"] == "computed"]
    if not read:
        return "awaiting"
    legs = {m["carried"] for m in read}
    return legs.pop() if len(legs) == 1 else "the models disagree"


def block(st, cutoff: str, first: str, last: str) -> dict:
    """The Weekly's and the Monthly's block: a table of the trigger days and their
    attribution, or one line that none fired."""
    cfg = config()
    evs, n = period_events(read_series(st, cutoff), first, last, cfg)
    t = cfg["trigger"]
    sub: dict[str, Any] = {"title": BLOCK_TITLE, "paragraph_wanted": False}
    if not evs:
        sub["lines"] = [f"No 10-year one-day move beyond its five-year threshold (the "
                        f"move {_pct_words(t['percentile'])} of one-day moves stay "
                        f"under) in the {n} sessions from {first} to {last} stored (D15)."]
        return sub
    rows = []
    for e in evs:
        att, tr = e["attribution"], e["trigger"]
        by = {m["model"]: m for m in att.get("models") or []}

        def cell(mid: str) -> str:
            m = by.get(mid) or {}
            if m.get("state") == "computed":
                return ("—" if m.get("premium_share") is None
                        else f"{m['premium_share']:.2f} ({m['carried']})")
            return "awaiting" if m.get("state") == "awaiting" else (m.get("reason") or "—")
        rows.append([e["day"], f"{tr['change_bp']:+.0f} bp", f"{tr['threshold_bp']:.1f} bp",
                     cell("kw"), cell("acm"), _leg(att)])
    sub["table"] = {"columns": ["Day", "Move", "Threshold (5 years, 97.5%)", "KW premium share",
                                "ACM premium share", "Carried"], "rows": rows}
    sub["lines"] = ["A report (D15): the trigger runs the attribution and adds no "
                    "right; nothing enters a composite or the market-state object."]
    return sub


# ---------------------------------------------------------------------------
# The ledger
# ---------------------------------------------------------------------------
def outcomes(day: str, yld: list[tuple[str, float]], move_bp: Optional[float],
             cfg: Optional[dict] = None) -> dict:
    """The 10-year's change over the next 5 and 20 sessions, bp; `continued` is
    the FIRST horizon's sign against the move's (the registration's rule)."""
    cfg = cfg or config()
    fwd = [int(f) for f in cfg["forward_sessions"]]
    days = [d for d, _ in yld]
    vals = dict(yld)
    out: dict[str, Any] = {}
    if day not in vals:
        out.update({f"y10_{f}d_bp": None for f in fwd}, resolved=False)
        return out
    i = days.index(day)
    for f in fwd:
        out[f"y10_{f}d_bp"] = (round((vals[days[i + f]] - vals[day]) * 100.0, 1)
                               if i + f < len(days) else None)
    first = out[f"y10_{fwd[0]}d_bp"]
    out["continued"] = (None if first is None or not move_bp else
                        (first > 0) == (move_bp > 0) and first != 0)
    out["resolved"] = all(out[f"y10_{f}d_bp"] is not None for f in fwd)
    return out


def ledger_row(ev: dict, now: str, oc: Optional[dict] = None) -> dict:
    att = ev.get("attribution") or {}
    tr = ev["trigger"]
    body = {"day": ev["day"], "change_bp": tr.get("change_bp"),
            "threshold_bp": tr.get("threshold_bp"), "n": tr.get("n"),
            "trigger_line": tr.get("line"), "state": att.get("state"),
            "move_bp": att.get("move_bp"), "start": att.get("start"),
            "models": att.get("models"), "verdict": att.get("line"), "outcomes": oc}
    return {"registry_key": LEDGER_KEY, "instrument": ev["day"], "observed_at": ev["day"],
            "available_at": now, "value": json.dumps(body, sort_keys=True, default=str),
            "source": SOURCE}


def resolve_rows(bodies: list[dict], series: dict, now: str,
                 cfg: Optional[dict] = None) -> list[dict]:
    """A new vintage for each row whose attribution was awaiting and is now
    readable, or whose outcomes moved; nothing for a row that is unchanged."""
    from . import speed_attribution as sa                       # noqa: PLC0415
    cfg = cfg or config()
    sa_cfg = _sa_cfg()
    out = []
    for body in bodies:
        if (body.get("outcomes") or {}).get("resolved") and body.get("state") == "computed":
            continue
        new = dict(body)
        if body.get("state") in ("awaiting", "partial"):
            att = sa.attribute(series, body["day"], 1, sa_cfg)
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
    ap = argparse.ArgumentParser(prog="python -m altdata.oneday_10y")
    ap.add_argument("cmd", choices=["show", "seed", "resolve"])
    ap.add_argument("--date", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    cfg = config()
    now = session.utc_iso()
    day = a.date or session.session_date()
    if a.cmd == "resolve":
        with observations.ObservationStore() as st:
            rows = resolve_rows(_latest_bodies(st, now), read_series(st, now), now, cfg)
            if rows and not a.dry_run:
                st.write_many(rows)
        print(f"resolved rows {'that would be ' if a.dry_run else ''}written: {len(rows)}")
        return 0
    with observations.ObservationStore() as st:
        ser = read_series(st, now)
    ev = evaluate(ser, day, cfg)
    if not ev["fired"]:
        print(f"{day}: the one-day trigger did not fire ({ev['trigger']['line']})")
        return 0 if a.cmd == "show" else 1
    print(ev["line"])
    for r in ev["table"]["rows"]:
        print("  " + " | ".join(str(x) for x in r))
    if a.cmd == "seed":
        row = ledger_row(ev, now, outcomes(day, ser["yield"],
                                           ev["attribution"].get("move_bp"), cfg))
        if not a.dry_run:
            with observations.ObservationStore() as st:
                st.write_many([row])
        print(f"{'would seed' if a.dry_run else 'seeded'} {LEDGER_KEY} for {day}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
