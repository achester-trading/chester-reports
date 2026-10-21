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


def vendor_zone_notes(vend: dict, zones: list[dict]) -> list[str]:
    """BATCH 11 ITEM 55's vendor annotation, the Weekly's vendor line only: for
    each of the week's SPY cluster zones, whether the vendor's flip and walls fall
    inside it. Words only, no vendor figure; NEVER COUNTED (D3)."""
    out = []
    for z in zones:
        inside = [lab for lab, k in (("flip", "flip"), ("call wall", "call_wall"),
                                     ("put wall", "put_wall"))
                  if isinstance(vend.get(k), (int, float)) and z["low"] <= vend[k] <= z["high"]]
        out.append(f"The vendor's levels against our cluster {z['low']:,.2f} to "
                   f"{z['high']:,.2f}: " + (", ".join(inside) + " inside" if inside
                                             else "none inside")
                   + " (an annotation; never counted).")
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
    # OS-10 (a44-opening-setup): the week's most active names by options volume,
    # after the vendor line below; report-only, no chart, no paragraph.
    from . import opening_setup                                 # noqa: PLC0415
    try:
        week = sorted({str(c.get("session"))[:10] for c in cards or [] if c.get("session")})
        if not week:
            from altdata import session as _s                   # noqa: PLC0415
            d, week = _s.previous_trading_session(ending), [ending]
            while len(week) < 5:
                week.insert(0, d.isoformat())
                d = _s.previous_trading_session(d.isoformat())
        most = opening_setup.most_active(st, week, cutoff)
    except Exception:                                           # noqa: BLE001
        most = None
        out["not_tracked"].append("the most-active names: their table faulted")
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
    # BATCH 11 ITEM 55: H6's running rates beside H1-H5's, as they print.
    from altdata import bars as _bars, level_clusters as _lc   # noqa: PLC0415
    h6_lines, week_zones = [], []
    try:
        day = str(cutoff)[:10]
        with _bars.BarStore(str(st.path)) as _bst:
            h6 = _lc.rates_from_store(st, _bst, cutoff,
                                      _lc.sessions_between("2026-09-01", day))
        h6_lines = h6["lines"]
        week_zones = _lc.in_force(st, "SPY", day, cutoff)
    except Exception:                                           # noqa: BLE001
        out["not_tracked"].append("H6, the level clusters: its rates faulted")
    out["subsections"].append({"title": "Registered hypotheses (the scorecard)",
                               "table": None, "lines": sc["lines"] + h6_lines,
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
                               "lines": fa.vendor_line(vend, prof, day=day)
                               + vendor_zone_notes(vend, week_zones),
                               "paragraph_wanted": False})
    if most:
        out["subsections"].append(most)
    # OS-12 (Batch 13 item 61, a54): the week's relative-volume flags per name and
    # the ledger to date, beside OS-10; report-only, no chart, no paragraph.
    try:
        from . import relative_volume as _rv                    # noqa: PLC0415
        out["subsections"].append(_rv.weekly_subsection(st, week, cutoff))
    except Exception:                                           # noqa: BLE001
        out["not_tracked"].append("relative options volume: its table faulted")
    # OS-8 and OS-5 (a45-opening-setup-2): the setup profiles and the single-name
    # put share, no side; report-only, no chart, no paragraph.
    for build, why in ((lambda: opening_setup.profiles(st, cutoff), "the setup profiles"),
                       (lambda: opening_setup.single_name_puts(st, cutoff),
                        "the single-name put share")):
        try:
            out["subsections"].append(build())
        except Exception:                                       # noqa: BLE001
            out["not_tracked"].append(f"{why}: its table faulted")
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
