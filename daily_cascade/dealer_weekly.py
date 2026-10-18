"""
The Weekly's dealer additions (6b part 3; brief v2 sections 2 to 5): T3 as a
table, T2 per horizon, the registered hypotheses' running evidence, the vendor
line, and the facts of the three sentences plus the fourth -- the week against
the Monday read, from the scorecard rows.

    from daily_cascade import dealer_weekly
    add = dealer_weekly.mechanics(st, cutoff, ending, cards, computed_dir)

Every figure is read: the week's last settled profile (dealer_block), the stored
scorecard rows (dealer_scorecard), the stored vendor series (sources.flashalpha).
Nothing fetches; nothing here grants a reading -- the matrix ends on "registered
hypotheses: n, none promoted" until the registration's rule promotes one.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from . import dealer_block as db


def week_vs_monday(cards: list[dict], cfg: dict) -> Optional[dict]:
    """The fourth sentence's facts: the Monday read (the week's first stored
    row's morning fields) and the week against it (the last row's close)."""
    cs = sorted(cards or [], key=lambda c: str(c.get("session")))
    if not cs:
        return None
    mon, last = cs[0], cs[-1]
    reg = db.regime(mon.get("net_gex_morning"), mon.get("net_to_gross_morning"), cfg)
    close = last.get("close")
    out = {"monday_session": str(mon.get("session"))[:10],
           "monday_read": reg,
           "monday_zero_gamma": db.price(mon.get("flip_morning")),
           "monday_otm_call_wall": db.price(mon.get("call_wall_otm_morning")),
           "monday_otm_put_wall": db.price(mon.get("put_wall_otm_morning")),
           "week_end_session": str(last.get("session"))[:10],
           "week_end_close": db.price(close)}
    for k, lab in (("flip_morning", "zero_gamma"), ("call_wall_otm_morning", "call_wall"),
                   ("put_wall_otm_morning", "put_wall")):
        v = mon.get(k)
        out[f"week_end_close_vs_monday_{lab}"] = db.dist(v, close) if v and close else "n/a"
    return out


FOURTH_NOTE = (
    "\n\nTHE FOURTH DEALER SENTENCE (the Weekly): after the three, one sentence on "
    "the week against the Monday read, from `dealer_week_vs_monday` only -- the "
    "regime Monday's profile read, where the week closed against Monday's "
    "zero-gamma level and walls -- and the registered hypotheses' running "
    "evidence as `dealer_hypotheses` prints it (k/n, never a rate as a finding: "
    "none is promoted).")


def mechanics(st, cutoff: str, ending: str, cards: list[dict],
              computed_dir: Optional[str], cfg: Optional[dict] = None) -> dict:
    """{"subsections", "data", "not_tracked"} to add to the Weekly's Mechanics."""
    cfg = cfg if cfg is not None else db.config()
    out: dict = {"subsections": [], "data": {}, "not_tracked": []}
    # ST-10 (a43-render, 18 Oct 2026): the Sunday line and the Books' status, where
    # the order's section 7 places them (the Sunday 05:00 edition).
    from . import signal_lines                                  # noqa: PLC0415
    try:
        out["subsections"].append(signal_lines.sunday_subsection(st, cutoff))
    except Exception:                                           # noqa: BLE001
        out["not_tracked"].append("the Sunday line: its block faulted")
    prof = db.newest_settled(ending, "SPY", computed_dir) if computed_dir else None
    if prof and prof.get("horizons"):
        m = db.t3(prof, cfg, db.window_history(st, cutoff, prof), db.implied_vol(st, cutoff))
        out["subsections"].append({"title": "Horizon matrix, SPY", "table": m["table"],
                                   "lines": [m["tail"][0].upper() + m["tail"][1:] + "."],
                                   "paragraph_wanted": False})
        out["subsections"].append({"title": "Key levels by horizon, SPY",
                                   "table": db.t2_by_horizon(prof, cfg),
                                   "paragraph_wanted": False})
        s = db.summary(prof, None, cfg)
        out["data"]["dealer_sentences"] = db.sentence_facts(prof, s, cfg)
    else:
        out["not_tracked"].append("the horizon matrix: no settled dealer profile for "
                                  "the week" if computed_dir else
                                  "the horizon matrix: the profiles are not read here")
    from altdata import dealer_scorecard as dsc                 # noqa: PLC0415
    sc = dsc.from_store(st, cutoff)
    out["subsections"].append({"title": "Registered hypotheses (the scorecard)",
                               "table": None, "lines": sc["lines"],
                               "paragraph_wanted": False})
    out["data"]["dealer_hypotheses"] = sc["lines"]
    out["data"]["_dealer_rates"] = sc["rates"]
    wvm = week_vs_monday(cards, cfg)
    if wvm:
        out["data"]["dealer_week_vs_monday"] = wvm
    from altdata.sources import flashalpha as fa                # noqa: PLC0415
    try:
        vend = fa.stored(st, cutoff, "SPY")
    except Exception:                                           # noqa: BLE001
        vend = {}
    # F-4 (18 Oct 2026): the mechanics table's one vendor row beside the line; from
    # the day after the plan ends, "vendor: plan ended".
    day = str(cutoff)[:10]
    out["subsections"].append({"title": "Vendor line (FlashAlpha)",
                               "table": fa.mechanics_row(vend, day),
                               "lines": fa.vendor_line(vend, prof, day=day),
                               "paragraph_wanted": False})
    # EL-5: THE STATE VECTOR, one row per session (the 16:10 capture's), read
    # from the store; numbers only.
    from altdata import state_vector as sv                      # noqa: PLC0415
    rows = []
    for c in cards:
        day = str(c.get("session"))[:10]
        v = sv.stored(st, day, cutoff)
        if any(x is not None for x in v.values()):
            d = dt.date.fromisoformat(day)
            rows.append(sv.weekly_row(f"{d.strftime('%a')} {d.day}", v))
    out["subsections"].append({
        "title": "State vector by session, SPY (16:10)",
        "table": {"columns": sv.WEEKLY_COLUMNS, "rows": rows} if rows else None,
        "lines": (["Measured variables only, no labels; the dealer legs are inferred, "
                   "not observed; OI as of prior close."] if rows else
                  ["No state vector stored for the week's sessions (stored from 17 "
                   "Oct 2026)."]),
        "paragraph_wanted": False})
    return out
