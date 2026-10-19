"""
The ten-section stack on the Weekly. (reporting-stack brief, Tranche T2)

    from daily_cascade import weekly_stack
    out = weekly_stack.produce(weekly_payload, archive_dir=..., dry_run=...)

THE SAME STACK AS THE CLOSE, AT THE WEEKLY'S DEPTHS. Sections, order, claim lines,
change marks, the collapse rule, the budget and the chart rules are the daily
close's (daily_cascade/stack.py), assembled at the matrix's Weekly column
(config/reporting_stack.yaml, `weekly:`). What differs is the window -- every
change is the WEEK's, measured from the same cutoff one week earlier -- and the
Weekly's own blocks:

  Positioning & flows (deep)  CFTC, FINRA short interest, RTAT10, ApeWisdom,
                              TIC and the week's leadership; only series the
                              store holds, the rest "not yet tracked".
  Ahead (deep)                the week's events and the GRADED-CALLS TABLE: the
                              ledger's Brier by source over the last four weeks,
                              the base-rate outlooks on their own line.
  The book (medium)           the register's week, Book Z, the ATTENTION COUNTS
                              (packets approved / 7 from the register; sitting
                              hours / 2 and rulings from docs/attention-log.md)
                              and how often each section-1.1 trigger fired.

Reads only. The prior edition is the archived JSON of the previous Weekly, never
a daily close: a mark says "changed since last Sunday".
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

from altdata import bars as bars_mod, derived, levels as levels_mod, observations, session
from altdata import model_meter

from . import charts as charts_mod
from .cadence import Period
from . import stack as stack_mod
from . import stack_prose, stack_render
from . import weekly_sections as wsec
from .stack import item, _signed, _lvl, _change

log = logging.getLogger("daily_cascade.weekly_stack")

REPO = Path(__file__).resolve().parent.parent
ATTENTION_LOG = REPO / "docs" / "attention-log.md"
PACKETS_PER_WEEK = 7
SITTING_HOURS_PER_WEEK = 2

SECTORS = ("xlk", "xlf", "xle", "xlv", "xli", "xlp", "xly", "xlu", "xlb", "xlre",
           "xlc")
# Style pairs: (label, numerator, denominator). A pair's week return is the
# numerator's minus the denominator's, in points.
STYLE_PAIRS = (("Growth over value (IVW/IVE)", "ivw", "ive"),
               ("Large growth over value (IWF/IWD)", "iwf", "iwd"),
               ("Equal over cap weight (RSP/SPY)", "rsp", "spy"),
               ("Small over large (IWM/SPY)", "iwm", "spy"),
               ("Discretionary over staples (XLY/XLP)", "xly", "xlp"))


def edition_name(ending: str) -> str:
    return f"weekly_tactical_{ending}_stack.json"


def load_prior(prev_ending: str, archive_dir: Optional[str]) -> Optional[dict]:
    if not archive_dir:
        return None
    p = Path(archive_dir) / edition_name(prev_ending)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return None


def week_ago(cutoff: str) -> str:
    t = dt.datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
    return (t - dt.timedelta(days=7)).isoformat()


# ---------------------------------------------------------------------------
# Change over the week, from the store
# ---------------------------------------------------------------------------
# The CFTC contracts the Weekly reads, in print order (altdata/sources/cftc.py).
CFTC_CONTRACTS = (("SP500", "S&P 500 futures"), ("NDX100", "Nasdaq-100 futures"),
                  ("RUSSELL2000", "Russell 2000 futures"),
                  ("UST10Y", "10-year note futures"), ("UST30Y", "30-year bond futures"),
                  ("VIX", "VIX futures"), ("USD_INDEX", "dollar index futures"),
                  ("JPY", "yen futures"), ("GOLD", "gold futures"),
                  ("WTI", "crude oil futures"))


def edition_session(cut: str) -> str:
    """The session a cutoff's edition is of: the last trading session on or
    before the cutoff's Eastern date."""
    from altdata import session as _session                     # noqa: PLC0415
    return _session.last_trading_session(_session.session_date_obj(cut)).isoformat()


def asof_cell(x: dict) -> str:
    """A row's as-of cell: its observation date, or "effective 19 Oct" for a
    declared forward-dated series dated after the edition (W8-9)."""
    if x.get("effective"):
        from . import readability                               # noqa: PLC0415
        return "effective " + readability.prose_date(x["observed_at"])
    return x["observed_at"]


def change_over(st, key: str, now_cut: str, then_cut: str,
                instrument: Optional[str] = None) -> Optional[dict]:
    """{level, prior, change, unit, observed_at} between two cutoffs.

    NO DATE AFTER THE EDITION'S SESSION (W8-9): an observation dated after the
    session a cutoff closes is read only for a series the registry declares
    forward-dated (IORB's effective day), and it then carries `effective`; any
    other series is read at its newest observation on or before the session."""
    def at(cut: str):
        r = st.latest_as_of(key, cut, instrument)
        day = edition_session(cut)
        if r and str(r.get("observed_at"))[:10] > day and not derived.forward_dated(key):
            rows = [x for x in st.as_of(key, cut, instrument)
                    if str(x.get("observed_at"))[:10] <= day]
            r = max(rows, key=lambda x: str(x["observed_at"])) if rows else None
        return r
    a, b = at(now_cut), at(then_cut)
    if not a or a.get("value_num") is None:
        return None
    lv = a["value_num"]
    pv = b.get("value_num") if b else None
    units = derived.level_units_of(key)
    du = derived.delta_unit_for(key)[0]
    if pv is None or str(b.get("observed_at")) == str(a.get("observed_at")):
        ch = None
    elif du == "bps":
        ch = round((lv - pv) * (1.0 if units in ("bps", "bp") else 100.0), 1)
    elif du == "percent" and pv:
        ch = round(100.0 * (lv / pv - 1.0), 2)
    else:
        ch = round(lv - pv, 4)
    out = {"key": key, "level": lv, "prior": pv, "change": ch,
           "unit": "bp" if du == "bps" else ("%" if du == "percent" else ""),
           "level_units": units, "observed_at": str(a["observed_at"])[:10],
           "available_at": str(a.get("available_at") or "")[:10] or None,
           "prior_observed_at": str(b["observed_at"])[:10] if b else None}
    if out["observed_at"] > edition_session(now_cut):
        out["effective"] = True          # W8-9: a declared forward-dated series
    # A RAW change carries its display form (T3.4a): "+42,984" for CFTC
    # contracts, "+29,000" for payrolls -- what the table prints and the audit
    # accepts.
    if ch is not None and du not in ("bps", "percent"):
        from altdata import numeral_audit as na                  # noqa: PLC0415
        disp = na.change_display(ch, units, key)
        if disp:
            out["change_display"] = disp
    return out


def series(st, key: str, cutoff: str, instrument: Optional[str] = None,
           since: Optional[str] = None) -> list[tuple[str, float]]:
    rows = [(str(r["observed_at"])[:10], r["value_num"])
            for r in st.as_of(key, cutoff, instrument)
            if r.get("value_num") is not None]
    rows.sort()
    return [r for r in rows if not since or r[0] >= since]


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------
def labels_metric(k: Optional[str]) -> str:
    from altdata import labels                                   # noqa: PLC0415
    return labels.metric(k)


def mechanics_week(st, sessions: list[str], cutoff: str, wis: dict,
                   cfg: Optional[dict] = None, computed_dir: Optional[str] = None,
                   ending: Optional[str] = None) -> dict:
    dw = wsec.dealer_week(st, sessions, cutoff, cfg or stack_mod.config())
    cards = dw.pop("cards")
    items, nt = [], []
    if cards:
        pos = sum(1 for c in cards if c.get("gamma_regime") == "positive")
        crossed = sum(1 for c in cards if c.get("flip_crossed"))
        pins = sum(1 for c in cards if c.get("pin_max_pain_hit"))
        items.append(item("mech:week", f"SPY over {len(cards)} scored session(s): "
                          f"{pos} in positive net GEX, {len(cards) - pos} in "
                          f"negative; the morning flip crossed on {crossed}; "
                          f"closed at max pain on {pins}.", 1,
                          (pos, crossed, pins, len(cards))))
    else:
        nt.append("the dealer scorecard: the close stores one per session from "
                  "the first stacked close on")
    dials = wis.get("dials_now") or {}
    # The market's names for the three reads -- "dial" is the system's word, and
    # the prose audit refuses it.
    name = {"gamma": "Dealer gamma", "vol": "The volatility regime",
            "macro": "The macro regime"}
    for ch in wis.get("dial_changes") or []:
        it = item(f"mech:dial:{ch.get('dial')}",
                  f"{name.get(ch.get('dial'), str(ch.get('dial')))} moved "
                  f"from {ch.get('from') or 'absent'} to {ch.get('to')}.", 1,
                  (ch.get("from"), ch.get("to")))
        # Printed once, under "Changed since last Weekly" (T2.5 item 1).
        it["show"] = False
        items.append(it)
    items.append(item("mech:dials", "At the week's end: " + "; ".join(
        f"{name.get(k, k).lower() if n else name.get(k, k)} {v}"
        for n, (k, v) in enumerate(sorted(dials.items()))) + ".", 2, dials))
    for dch in wis.get("dimension_changes") or []:
        items.append(item(f"mech:dim:{dch.get('dimension')}",
                          f"Our read on {dch.get('dimension')} moved from "
                          f"{dch.get('from') or 'absent'} to {dch.get('to')} "
                          f"({dch.get('last_changed')}).", 2,
                          (dch.get("from"), dch.get("to"))))
    held = wis.get("dimensions_held") or []
    if held:
        items.append(item("mech:dims_held", "Unchanged on the week: "
                          + ", ".join(held) + ".", 3, held))
    vts = wis.get("vol_term_structure") or {}
    pub = vts.get(vts.get("published_by") or "") or {}
    if pub.get("state"):
        items.append(item("mech:vts", f"The VIX term structure is in {pub['state']} "
                          f"({labels_metric(pub.get('metric'))} at "
                          f"{float(pub.get('ratio') or 0):.2f}).", 2,
                          (pub.get("state"), pub.get("ratio"))))
    # THE DEALER TABLE AND ITS FLAGS (T2.2 item 18): one row per session,
    # flags computed by code; the prose may use a flag word only where set.
    subs = []
    if dw["table"]["rows"]:
        subs.append({"title": "Ranges and flags", "table": dw["ranges_table"],
                     "paragraph_wanted": False})
    vol = wsec.volatility(st, cutoff, wis, week_ago(cutoff))
    subs.append({**vol, "paragraph_wanted": True})
    # SR-38 (batch 4; placement: the revision line weekly in Mechanics),
    # report-only and tagged.
    rv, rv_data = ai_revisions_block(st, cutoff)
    if rv:
        subs.append(rv)
    # SIGNAL-TRIAGE BATCH 6 (16 Oct 2026): concentration and breadth (items 31
    # and 44, section 4 ruling 3) and the oil-shock signature (item 32, ruling 4),
    # report-only, with no paragraph of their own.
    from . import t1_rest_block                                 # noqa: PLC0415
    subs += t1_rest_block.mechanics_subsections(st, cutoff, "weekly")
    # THE GTM BATCH, PART 2 (17 Oct 2026): the concentration twin (GTM-3,
    # report-only) beside item 31's table, then the AI buckets (GTM-4) -- tables
    # only, no paragraph, so the Weekly's budgets hold.
    from . import gtm_block                                     # noqa: PLC0415
    subs = gtm_block.place_mechanics(subs, gtm_block.mechanics_subsections(
        st, cutoff, "weekly"))
    # 6b PART 3: T3, T2 per horizon, the registered hypotheses, the vendor line
    # and the four sentences' facts -- when the payload names the profiles.
    dealer_add = {}
    if computed_dir:
        from . import dealer_weekly                             # noqa: PLC0415
        dealer_add = dealer_weekly.mechanics(st, cutoff, ending or sessions[-1],
                                             cards, computed_dir)
        subs += dealer_add["subsections"]
        nt += dealer_add["not_tracked"]
    # SR-9 AMENDED (ST-R4.24a/b, Batch 5 item 24): the stock-bond correlation,
    # 60 days beside two years, its flag conditioned on the attribution.
    from . import batch5_block                                  # noqa: PLC0415
    sb = batch5_block.mechanics_subsection(st, cutoff)
    if sb:
        subs.append(sb)
    # BATCH 5 ITEMS 18 AND 19 (ST-R4.18a, 19a): the dispersion panel and the
    # cross-asset vol divergence flag, with a line in the read when it is active.
    from . import batch5b_block                                 # noqa: PLC0415
    subs += batch5b_block.mechanics_subsections(st, cutoff)
    for iid, text, val in batch5b_block.read_items(st, cutoff):
        items.append(item(iid, text, 1, val))
    # THE ES BLOCK'S WEEKLY PANEL (ST-R6.45d, Batch 6 item 45): the position
    # window (three months on daily bars) and the week's ES ledger -- levels
    # held, broke or untested, leans resolved or not. Tables only.
    es_sub = None
    try:
        from altdata import bars as bars_mod                    # noqa: PLC0415
        from . import es_read                                   # noqa: PLC0415
        with bars_mod.BarStore(str(st.path)) as bst:
            es_sub = es_read.weekly_subsection(bst, sessions, cutoff)
        subs.append(es_sub)
    except Exception:                                           # noqa: BLE001
        log.warning("ES weekly panel unavailable", exc_info=True)
    return {"items": items, "not_tracked": nt,
            "subsections": subs, "lead_paragraphs": "1",
            "table": dw["table"],
            "table_note": dw["table_note"] if dw["table"]["rows"] else None,
            "data": {"dealer_week": dw["data"]["sessions"], "dials_now": dials,
                     "volatility": vol.get("data"),
                     "dial_changes": wis.get("dial_changes") or [],
                     **({"ai_revisions": rv_data} if rv_data else {}),
                     **(dealer_add.get("data") or {})}}


AI_REVISIONS_TITLE = "Forward-EPS revisions: the AI names"
AI_FCF_TITLE = "The AI FCF transfer: hyperscalers and semiconductors (trailing)"
ATTRIBUTION_TITLE = "The S&P 500's return: earnings against the multiple (trailing)"


def ai_revisions_block(st, cutoff: str) -> tuple[Optional[dict], Optional[dict]]:
    """SR-38's revision line, or (None, None) on a fault: report-only, never
    costing the section."""
    try:
        from altdata import return_attribution as ra            # noqa: PLC0415
        v = ra.revisions(st, cutoff)
    except Exception:                                           # noqa: BLE001
        log.warning("the forward-EPS revision line is unavailable", exc_info=True)
        return None, None
    # The INDEX's line first (S&P DJI's drops, 13 Oct 2026), then the names'.
    return ({"title": AI_REVISIONS_TITLE,
             "lines": [ra.index_revision_line(v["index"], v["tag"]),
                       ra.revision_line(v)],
             "table": ra.revision_table(v), "paragraph_wanted": False},
            {"median": v["median"], "covered": v["covered"], "tag": v["tag"],
             "index_revision": ra.index_revision_data(v)})


def ai_fcf_block(st, cutoff: str) -> tuple[Optional[dict], Optional[dict]]:
    """SR-37's panel (the Monthly's Mechanics), or (None, None) on a fault."""
    try:
        from altdata import ai_fcf                              # noqa: PLC0415
        r = ai_fcf.read(st, cutoff)
    except Exception:                                           # noqa: BLE001
        log.warning("the AI FCF panel is unavailable", exc_info=True)
        return None, None
    return ({"title": AI_FCF_TITLE, "lines": ai_fcf.lines(r), "table": ai_fcf.table(r),
             "paragraph_wanted": False}, ai_fcf.data(r))


def attribution_block(st, cutoff: str) -> tuple[Optional[dict], Optional[dict]]:
    """SR-38's attribution and EY minus the bill (the Monthly's What's priced),
    or (None, None) on a fault."""
    try:
        from altdata import return_attribution as ra            # noqa: PLC0415
        a = ra.attribution(st, cutoff)
    except Exception:                                           # noqa: BLE001
        log.warning("the return attribution is unavailable", exc_info=True)
        return None, None
    return ({"title": ATTRIBUTION_TITLE, "lines": ra.attribution_lines(a),
             "paragraph_wanted": False}, ra.data(a))


def stored_objects(st, now: str) -> list[tuple[str, dict]]:
    """Every stored market-state object knowable at `now`, one per session (its
    latest revision), oldest first -- what the three dates are read from."""
    import regime                                               # noqa: PLC0415
    by: dict[str, dict] = {}
    for r in st.as_of(regime.STORE_KEY, now):
        try:
            by[str(r["observed_at"])[:10]] = json.loads(r["value_text"])
        except (TypeError, ValueError):
            continue
    return sorted(by.items())


def exception_labels(st, eid: str, now: str, cfg: Optional[dict] = None) -> list[str]:
    """W-1.3b item 3.2: a series exception's level / change / extreme labels,
    from its own stored history over the config's window."""
    from . import analytics                                     # noqa: PLC0415
    kind, _, key = str(eid).partition(":")
    if st is None or kind == "contradiction" or "." not in key:
        return []
    cfg = cfg if cfg is not None else analytics.load_config()
    days = int((((cfg.get("exceptions") or {}).get("labels") or {})
                .get("window_days")) or 1825)
    since = (dt.date.fromisoformat(now[:10]) - dt.timedelta(days=days)).isoformat()
    try:
        return analytics.series_labels(series(st, key, now, since=since), cfg)
    except Exception:                                           # noqa: BLE001
        return []


def exception_subsections(now_open: list, wis: dict, dates: Optional[dict],
                          st, now: Optional[str], w) -> tuple[list, list]:
    """W-1.3b item 3.2: the open exceptions as one table per tier, in the tiers'
    order -- potential leading indicator, contemporaneous contradiction, extreme
    without a trade -- each row with its labels and its descriptive resolution
    path, catalyst and invalidation. Returns (sub-sections, row data)."""
    from altdata import labels                                   # noqa: PLC0415
    from . import analytics                                     # noqa: PLC0415
    cfg = analytics.load_config()
    opened = set(wis.get("exceptions_opened") or [])
    by_tier: dict = {}
    data = []
    for e in now_open:
        tier = analytics.exception_tier(e, cfg)
        name = labels.exception(e)
        labs = exception_labels(st, e, now or session.utc_iso(), cfg)
        f = analytics.exception_fields(name, tier, cfg)
        since = ((dates or {}).get(e) or {}).get("exception_since") or "—"
        if e in opened:
            since = f"{since} (opened {w.this})"
        by_tier.setdefault(tier, []).append(
            [name, ", ".join(labs) or "—", since, f["resolution"], f["catalyst"],
             f["invalidation"]])
        data.append({"id": e, "name": name, "tier": tier, "labels": labs, **f})
    subs = []
    for tr in analytics.tier_order(cfg):
        rows = by_tier.get(tr["id"])
        if rows:
            subs.append({"title": f"Exceptions open {w.end}: {tr['title'].lower()}",
                         "tier": tr["id"],
                         "table": {"columns": ["Exception", "Labels",
                                               "Exception since", "Resolution path",
                                               "Catalyst", "Invalidation"],
                                   "rows": rows}})
    return subs, data


def misfit_week(wis: dict, pmb: Optional[dict],
                history: Optional[dict] = None, cadence: str = "weekly",
                screen: Optional[dict] = None,
                dates: Optional[dict] = None, st=None,
                now: Optional[str] = None) -> dict:
    w = Period.of(cadence)
    base = stack_mod.misfit_section({"market_state": {}}, pmb)
    # THE MOVE SCREEN (Audit #4 Category 1 items 1 and 5): the week's last
    # session, whose 5-day change is the week; a single-country shock prints only
    # once it has passed to the basket or EM spreads (SR-46(d)).
    sitems, sdata = stack_mod.screen_items(screen, cadence)
    items = [i for i in base["items"] if i["key"] != "misfit:none"]
    from altdata import labels                                   # noqa: PLC0415
    opened = [c for c in wis.get("contradictions") or []
              if c.get("open_state") == "open"]
    for c in opened:
        items.append(item(f"misfit:{c['id']}", stack_mod.contradiction_line(c), 1,
                          (c.get("persistence_days"), c.get("magnitude"))))
    for e in wis.get("exceptions_opened") or []:
        it = item(f"misfit:exc:{e}", f"Opened {w.this}: {labels.exception(e)}.", 2, e)
        # The exceptions table's "Opened this week" column carries it (T2.5).
        it["show"] = False
        items.append(it)
    for e in wis.get("exceptions_intraweek_only") or []:
        items.append(item(f"misfit:intra:{e}", f"Opened and closed inside "
                          f"{w.the}: {labels.exception(e)}.", 3, e))
    if not items:
        items.append(item("misfit:none", "No contradiction open, no exception "
                          f"opened {w.this}.", 1, "none"))
    data = dict(base["data"])
    now_open = wis.get("exceptions_open_now") or []
    data.update(sdata)
    # THE EXTREMES WITH THEIR PERCENTILE (W-1.1 item 1.0a): What doesn't fit's
    # frame ranks an extreme by its percentile's distance from the median.
    from altdata.numeral_audit import ordinal                     # noqa: PLC0415
    side = wis.get("exceptions_side") or {}
    data["extremes"] = [
        {"name": labels.exception(e), "percentile": side[e]["percentile"],
         "percentile_ordinal": ordinal(side[e]["percentile"]),
         "side": "the low tail" if side[e].get("side") == "low" else "the high tail"}
        for e in now_open if (side.get(e) or {}).get("percentile") is not None]
    data.update({"open_contradictions": [stack_mod.contradiction_data(c)
                                         for c in opened],
                 "exceptions_opened": [labels.exception(e) for e in
                                       wis.get("exceptions_opened") or []],
                 "exceptions_open_now": [labels.exception(e) for e in now_open],
                 # W-1.2 item 2.6: the ids beside the labels, for the collapse
                 # of an extreme the tape already prints (never in a frame).
                 "_exception_ids": list(now_open),
                 "_contradiction_rows": [dict(c) for c in opened]})
    # THE GAP TABLE (T2.2 item 5): each open gap with what each side is saying,
    # its z, direction and count, under a two-line note on how to read it. The
    # contradiction lines move into the table; the items keep the prediction-
    # market disagreements and the week's openings.
    gaps = wsec.gap_table(opened, history or {}, dates)
    data["gaps"] = gaps["data"]
    items = [i for i in items if not any(i["key"] == f"misfit:{c['id']}"
                                         for c in opened)]
    items += sitems
    if not items:
        items.append(item("misfit:none", "No prediction-market disagreement and "
                          f"no exception opened {w.this}.", 1, "none"))
    # EXCEPTION SINCE (W-1.1 item 1.3): the date it became an exception, with
    # "opened this week" beside it -- the status's age, never the gap's. THE
    # THREE TIERS (W-1.3b item 3.2) are the tables' grouping and order.
    subs, exc = exception_subsections(now_open, wis, dates, st, now, w)
    data["exceptions"] = exc
    return {"items": items, "not_tracked": base.get("not_tracked") or [],
            "data": data, "table": gaps["table"] if opened else None,
            # The gap table's how-to-read note is the glossary's "gap z-score"
            # entry already (T2.5 item 3): not printed twice.
            "table_note": None,
            "notes": ([("Exception labels: level -- in its five-year top or bottom "
                        "decile; change -- its seven-day change at a z of 2 or more; "
                        "extreme -- at its five-year bound. Resolution path, "
                        "catalyst and invalidation are descriptive, not forecasts.")]
                      if now_open else []),
            "subsections": subs}


PLUMB = (("fred.yield_2y", "2-year"), ("fred.yield_10y", "10-year"),
         ("fred.yield_30y", "30-year"), ("calc.yield_curve_2s10s", "2s10s"),
         ("fred.hy_oas", "High-yield OAS"),
         ("acm.term_premium_10y", "10-year term premium (ACM)"))


# 6e, the rest: the Weekly's lens table carries Plumbing's series and these.
WEEKLY_LENS_EXTRA = [("fred.ig_oas", "Investment-grade OAS"),
                     ("fred.cpi", "CPI"), ("fred.core_pce", "Core PCE"),
                     ("fred.u3_rate", "Unemployment rate"),
                     ("calc.core_cpi_pce_gap", "Core CPI less core PCE")]


# THE BARS' YIELD FOR THE WEEK'S MOVE (T2 ruling 3, 3 Oct 2026): one 10-year
# change per edition, the tape's -- Friday close to Friday close from the 5-minute
# feed's daily bars. FRED stays the level, the percentile and the history, and
# says its own as-of when it lags the bars.
BAR_YIELDS = {"fred.yield_10y": "y10", "fred.yield_30y": "y30"}


def plumbing_week(st, now: str, then: str, book: Optional[dict] = None,
                  cadence: str = "weekly", liquidity_deltas: bool = False,
                  yudd_line: Optional[bool] = None,
                  auction_block: bool = False) -> dict:
    w = Period.of(cadence)
    items, rows, data = [], [], {}
    frames = {i["id"]: i.get("frame") or {} for i in (book or {}).get("instruments") or []}
    for k, name in PLUMB:
        x = change_over(st, k, now, then)
        fr = frames.get(BAR_YIELDS.get(k, ""), {})
        if k in BAR_YIELDS and fr.get("last") is not None \
                and fr.get("wtd_change_bps") is not None:
            fred_lvl = f"; FRED {_lvl(x)} as of {x['observed_at']}" if x else ""
            data[name] = {"level_bars_pct": fr["last"], "week_change_bp":
                          fr["wtd_change_bps"], "as_of": fr.get("as_of"),
                          "fred": x}
            items.append(item(f"plumb:{k}", f"{name} {fr['last']:.3f}%, "
                              f"{_signed(fr['wtd_change_bps'], 'bp')} {w.on} "
                              f"(Friday to Friday, as of {fr.get('as_of')}{fred_lvl}).",
                              1 if k == "fred.yield_10y" else 2,
                              (fr["last"], fr["wtd_change_bps"])))
            rows.append([name, f"{fr['last']:.3f}%",
                         _signed(fr["wtd_change_bps"], "bp"), fr.get("as_of")])
            continue
        if not x:
            continue
        data[name] = x
        items.append(item(f"plumb:{k}", f"{name} {_lvl(x)}, {_change(x)} {w.on} "
                          f"({window(x)}).",
                          1 if k in ("fred.yield_10y", "fred.hy_oas") else 2,
                          (x["level"], x["change"])))
        rows.append([name, _lvl(x), _change(x), asof_cell(x)])
    rel = tier1_releases(st, now, then)
    for r in rel:
        items.append(item(f"plumb:rel:{r['release']}:{r['series']}",
                          f"{r['release']} ({r['date']}): {r['label']} "
                          f"{r['actual_text']}, prior {r['prior_text']} "
                          f"(as of {r['as_of']}).", 1,
                          (r["actual"], r["prior"])))
        rows.append([f"{r['release']}: {r['label']}", r["actual_text"],
                     f"prior {r['prior_text']}", r["as_of"]])
    # PLUMBING, MADE PLUMBING (T2.3 item 3): liquidity and its legs, SOFR
    # against IORB (in place of the repo footnote), the spreads beside HY, the
    # week's auctions, copper and gold/copper. Global rates and FX below.
    pr = wsec.plumbing_rows(st, now, then, cadence, liquidity_deltas,
                            auctions_in_table=not auction_block)
    rows += pr["rows"]
    fx = wsec.global_fx(st, now, then, cadence)
    subs = [{**fx, "paragraph_wanted": False}]
    nt = list(pr["not_tracked"])
    pdata = {"series": data, "tier1_releases": rel, "plumbing": pr["data"]}
    # YIELDS-UP/DOLLAR-DOWN (AQ-8a; Currencies section 19, Rates S10/S29): one
    # line, the Weekly only, and only when a flagged week became known this week
    # -- otherwise nothing, not even a "did not fire" line.
    if (cadence == "weekly") if yudd_line is None else yudd_line:
        try:
            from altdata import attribution                      # noqa: PLC0415
            yl = attribution.yudd_week_line(st, now, then)
        except Exception as exc:                                 # noqa: BLE001
            log.warning("yields-up/dollar-down line unavailable", exc_info=True)
            yl = None
            nt.append(f"the yields-up/dollar-down line: FAULT {type(exc).__name__}")
        if yl:
            pdata["yields_up_dollar_down"] = {k: v for k, v in yl.items() if k != "text"}
            subs.append({"title": "Yields up, dollar down", "lines": [yl["text"]],
                         "paragraph_wanted": False})
    if auction_block:
        # THE AUCTIONS' OWN TABLE (W-1.1 item 1.4): every field with its
        # two-year percentile; the data carries the stored tail, or None.
        recs = wsec.auction_records(st, now, then)
        pr["data"]["auction_records"] = recs
        if recs:
            subs.append({"title": "Treasury auctions", "table": wsec.auction_table(recs),
                         "table_note": wsec.AUCTION_NOTE, "paragraph_wanted": False})
    # SR-36: the basis-unwind watch, one code-written line (report-only).
    bp = basis_proxy_read(st, now)
    if bp:
        from altdata import basis_proxy                          # noqa: PLC0415
        subs.append({"title": "Treasury basis proxy: the unwind watch",
                     "lines": [basis_proxy.plumbing_line(bp)],
                     "paragraph_wanted": False})
        pdata["basis_unwind_watch"] = basis_proxy_data(bp)
    # SR-43 and SR-49: the 10-year's anchors, the selloff's shape and what moved,
    # and the four voices adjudicated by those measures (report-only).
    rr = rates_read(st, now)
    if rr:
        from altdata import rates_anchors, rates_shape          # noqa: PLC0415
        subs.append({"title": "The 10-year's anchors and the selloff's shape",
                     "lines": [rates_anchors.line(rr["anchors"]),
                               rates_shape.shape_line(rr["shape"])],
                     "paragraph_wanted": False})
        subs.append({"title": "The 10-year top: four voices, read against the measures",
                     "table": rates_shape.voices_table(rr["shape"]),
                     "lines": [f"Verdicts by declared rule, not opinion "
                               f"{rr['anchors'].get('tag') or ''}".rstrip() + "."],
                     "paragraph_wanted": False})
        pdata["rates_anchors"] = rates_data(rr)
    # SIGNAL-TRIAGE BATCH 3, TRANCHE A (13 Oct 2026): the 30y JGB line, SR-30's
    # narrow flag, SR-33's operations, SR-34's fast tells and SR-6 by tenor.
    from . import batch3_block                                  # noqa: PLC0415
    subs += batch3_block.weekly_subsections(st, now, then, cadence)
    # SIGNAL-TRIAGE BATCH 6 (16 Oct 2026): items 34, 36, 37 and 41 under one
    # "Rates transmission" header (the order's section 4, cross-item ruling 1).
    from . import rates_transmission_block                      # noqa: PLC0415
    rt_sub = rates_transmission_block.subsection(st, now, cadence)
    if rt_sub:
        subs.append(rt_sub)
    # SIGNAL-TRIAGE BATCH 6, items 42 and 39: the expectations composite and the
    # cross-country real yields; the US-DE and US-JP real differentials print in
    # the Currencies read, "Global rates and FX".
    from . import t1_rest_block                                 # noqa: PLC0415
    subs += t1_rest_block.plumbing_subsections(st, now, cadence)
    # THE GTM BATCH, PART 1 (17 Oct 2026): GTM-13's fixed-income scenario table
    # (the Monthly rebuilds its own sub-sections and adds GTM-15 and GTM-21).
    from . import gtm_block                                     # noqa: PLC0415
    subs += gtm_block.plumbing_subsections(st, now, "weekly")
    cur = t1_rest_block.currencies_lines(st, now)
    if cur:
        subs[0]["lines"] = list(subs[0].get("lines") or []) + cur
    # BATCH 5 TRANCHE 1 (ST-R4.21b, 26a, 17a): the attribution's term premium
    # and fiscal-bark flag, and net liquidity attributed. Tables and lines only.
    from . import batch5_block                                  # noqa: PLC0415
    subs += batch5_block.plumbing_subsections(st, now, then, cadence)
    # 6E, THE REST (16 Oct 2026): the lens columns the brief left for "later",
    # as one table of Plumbing's series, and the inflation block (the CPI lead
    # composite, the core CPI-PCE gap; Batch 7 items 46 and 48 attach to it).
    # The Weekly's only: tables and lines, no prose word and no chart.
    if cadence == "weekly":
        from . import inflation_block, lens_cells                # noqa: PLC0415
        lt = lens_cells.lens_table(st, now, list(PLUMB) + WEEKLY_LENS_EXTRA)
        if lt:
            subs.append(lt)
        subs += inflation_block.subsections(st, now, cadence)
    # NO BULLETS (T2.2 item 6): the table carries every figure and the prose
    # reads from it; the items stay as the section's data and its change marks.
    return {"items": items, "print_items": False,
            "data": pdata,
            "table": {"columns": ["Series", "Level or actual", w.or_prior,
                                  "As of"], "rows": rows},
            "subsections": subs,
            "not_tracked": nt}


def basis_proxy_read(st, now: str) -> Optional[dict]:
    """SR-36's read as of the Weekly's cutoff, or None (nothing stored, or a
    fault -- the proxy is report-only and never costs a section)."""
    try:
        from altdata import basis_proxy                          # noqa: PLC0415
        return basis_proxy.read(st, cutoff=now)
    except Exception:                                           # noqa: BLE001
        return None


def rates_read(st, now: str) -> Optional[dict]:
    """SR-43 and SR-49 as of the cutoff, or None on a fault: report-only, never
    costing the section."""
    try:
        from altdata import rates_anchors, rates_shape          # noqa: PLC0415
        a = rates_anchors.read(st, now)
        return {"anchors": a, "shape": rates_shape.read(st, now, anchors=a)}
    except Exception:                                           # noqa: BLE001
        log.warning("the rates anchors are unavailable", exc_info=True)
        return None


def rates_data(rr: dict) -> dict:
    """The printed figures, for the section's frame (each as printed)."""
    a, s = rr["anchors"], rr["shape"]
    inf, fis = a["inflation"], a["fiscal"]
    lt = s["selloffs"].get("latest") or {}
    return {"inflation_anchor_pct": inf.get("anchor_pct"),
            "inflation_gap_bp": inf.get("gap_bp"),
            "inflation_residual_bp": inf.get("residual_bp"),
            "twin_deficit_fitted_pct": fis.get("us_fitted_pct"),
            "twin_deficit_gap_bp": fis.get("gap_bp"),
            "shape": s["shape"].get("state"), "latest_selloff": lt.get("label"),
            "voices": [{k: v[k] for k in ("voice", "verdict")} for v in s["voices"]],
            "tag": a.get("tag")}


def basis_proxy_data(r: dict) -> dict:
    """What the section's data carries of the read: the printed figures, as
    printed, and the labels."""
    w = r["watch"]
    return {"as_of": r["day"], "ten_year_net_short_oi_pct": round(r["ten_year_short_oi"], 1)
            if r.get("ten_year_short_oi") is not None else None,
            "six_contract_net_short_oi_pct": round(r["lev_short_oi"], 1)
            if r.get("lev_short_oi") is not None else None,
            "ten_year_tier": r.get("ten_year_tier"), "aggregate_tier": r.get("aggregate_tier"),
            "oi_change": r.get("oi_change"), "unwind_watch": "on" if w["on"] else "off",
            "cosignals_on": w["cosignals_on"], "absent": w["absent"]}


def tier1_releases(st, now: str, then: str) -> list[dict]:
    """The week's tier-1 releases that occurred, each with its HEADLINE figures'
    actual, prior and as-of from the store (T2.1 item 13; T2.2: the headline
    series declared in config/release_calendar.yaml `tier1_headlines`, under
    their plain labels -- never every series the release revises). A release is
    matched when its name starts with the declared one."""
    from altdata import events                                  # noqa: PLC0415
    heads = (wsec.load_calendar().get("tier1_headlines") or {})
    out = []
    try:
        with events.EventStore(str(st.path)) as ev:
            rows = ev.conn.execute(
                "SELECT observed_at, title, payload FROM events WHERE type = "
                "'release' AND observed_at > ? AND observed_at <= ? AND "
                "available_at <= ? ORDER BY observed_at", (then, now, now)).fetchall()
    except Exception:                                           # noqa: BLE001
        return out
    seen = set()
    for obs_at, title, payload in rows:
        name = str(title).split(" -- ")[0].strip()
        rel = next((k for k in heads if name.lower().startswith(k.lower())), None)
        if not rel:
            continue
        for h in heads[rel]:
            key, form = h["key"], h.get("form") or "level"
            if (rel, key, form) in seen:
                continue
            seen.add((rel, key, form))
            pts = [r for r in st.as_of(key, now) if r.get("value_num") is not None]
            pts.sort(key=lambda r: str(r["observed_at"]))
            got = headline_form([r["value_num"] for r in pts], form)
            if not got or not h.get("label"):
                continue
            out.append({"release": rel, "date": str(obs_at)[:10], "series": key,
                        "form": form, "label": h["label"], "actual": got[0],
                        "prior": got[1], "actual_text": form_text(got[0], form, key),
                        "prior_text": form_text(got[1], form, key),
                        "as_of": str(pts[-1]["observed_at"])[:10]})
    return out


def headline_form(vals: list, form: str) -> Optional[tuple]:
    """(actual, prior) in the declared form, or None when the store holds too
    few prints to compute it (rulings of 5 Oct, item 1)."""
    need = {"level": 1, "change": 2, "mom": 2, "yoy": 13, "annualised": 2}[form]

    def at(k: int) -> Optional[float]:
        """The form `k` prints back (0 = latest)."""
        n = len(vals) - 1 - k
        if n - (need - 1) < 0:
            return None
        v = vals[n]
        if form == "level":
            return v
        if form == "change":
            return v - vals[n - 1]
        if form == "mom":
            return 100.0 * (v / vals[n - 1] - 1.0) if vals[n - 1] else None
        if form == "yoy":
            return 100.0 * (v / vals[n - 12] - 1.0) if vals[n - 12] else None
        if form == "annualised":
            return (100.0 * ((v / vals[n - 1]) ** 4 - 1.0)) if vals[n - 1] else None
        return None
    a = at(0)
    return None if a is None else (a, at(1))


def form_text(v: Optional[float], form: str, key: str) -> str:
    if v is None:
        return "n/a"
    if form == "change":
        # IN THE SERIES' OWN SCALE, WRITTEN (5 Oct): payrolls are stored in
        # thousands, so +29 prints "+29k" -- the model then has nothing to rescale,
        # and "+29" read as 29,000 was withheld by the audit.
        # T3.4a: one change form for every report, numeral_audit.change_display
        # -- "+29,000" for payrolls' +29 thousand, "+12,500" for a plain count,
        # each accepted by the audit as the payload's own display.
        units = derived.level_units_of(key)
        from altdata import numeral_audit as na                  # noqa: PLC0415
        return na.change_display(v, units, key) or f"{v:+,.0f}"
    if form in ("mom",):
        return f"{v:+.1f}%"
    if form in ("yoy", "annualised"):
        return f"{v:.1f}%"
    units = derived.level_units_of(key)
    return f"{v:,.1f}%" if units in ("%", "percent") else f"{v:,.0f}"


def _week_return(st, sym: str, now: str, then: str) -> Optional[float]:
    x = change_over(st, f"yfinance.mkt_{sym}", now, then)
    return x.get("change") if x else None


def leadership(st, now: str, then: str) -> list[tuple[str, float]]:
    out = []
    for s in SECTORS:
        r = _week_return(st, s, now, then)
        if r is not None:
            out.append((s.upper(), r))
    for lab, a, b in STYLE_PAIRS:
        ra, rb = _week_return(st, a, now, then), _week_return(st, b, now, then)
        if ra is not None and rb is not None:
            out.append((lab, round(ra - rb, 2)))
    return out


def positioning_week(st, now: str, then: str, cadence: str = "weekly") -> dict:
    w = Period.of(cadence)
    items, data, nt, rows = [], {}, [], []
    two_years = (dt.date.fromisoformat(now[:10]) - dt.timedelta(days=730)).isoformat()
    cftc = {}
    missing = []
    for inst, name in CFTC_CONTRACTS:
        x = change_over(st, "cftc.noncomm_net", now, then, inst)
        if not x:
            missing.append(name)
            continue
        hist = [v for _, v in series(st, "cftc.noncomm_net", now, inst, two_years)]
        z = derived.z_of(hist, x["level"]) if len(hist) > 20 else None
        pct = derived.percentile_of(hist, x["level"]) if len(hist) > 20 else None
        cftc[name] = series(st, "cftc.noncomm_net", now, inst, two_years)
        # W-1.3b item 3.3: the positioning-change score -- the four-week change
        # as a z against two years' four-week changes, beside the level z.
        from . import analytics                                 # noqa: PLC0415
        cz = analytics.change_z(cftc[name], int(analytics.load_config()
                                                .get("positioning", {})
                                                .get("change_weeks") or 4))
        data[f"cftc:{inst}"] = {**x, "z_2y": None if z is None else round(z, 1),
                                "percentile_2y": pct,
                                "change_4w": None if not cz else cz[0],
                                "change_z_4w": (None if not cz or cz[1] is None
                                                else round(cz[1], 1))}
        items.append(item(f"pos:cftc:{inst}", f"Speculators' net {name}: "
                          f"{x['level']:,.0f} contracts ({_change(x)} {w.since_report}, "
                          f"as of {x['observed_at']})"
                          + (f", z {z:+.1f} over two years" if z is not None else "")
                          + ".", 2, (x["level"], x["observed_at"])))
        rows.append(["CFTC " + name, f"{x['level']:,.0f}", _change(x), x["observed_at"]])
    # The contracts not yet stored are the CFTC sub-section's own footnote;
    # listing them here too printed them twice (T2.5 item 1).
    for sym in ("SPY", "QQQ", "IWM"):
        x = change_over(st, "finra.short_interest_days_to_cover", now, then, sym)
        if x:
            x["dp"] = 2          # W8-8: the change to the level's two decimals
            data[f"finra:{sym}"] = x
            items.append(item(f"pos:si:{sym}", f"{sym} short interest: {x['level']:,.2f} "
                              f"days to cover ({_change(x)}, settlement "
                              f"{x['observed_at']}).", 3, (x["level"], x["observed_at"])))
            rows.append([f"{sym} days to cover", f"{x['level']:,.2f}", _change(x),
                         x["observed_at"]])
    for sym in ("SPY", "QQQ", "IWM", "NVDA", "TSLA"):
        wk = [v for d, v in series(st, "ndl.rtat10_sentiment", now, sym)
              if d > then[:10]]
        prev = [v for d, v in series(st, "ndl.rtat10_sentiment", then, sym)
                if d > week_ago(then)[:10]]
        if wk:
            m, pm = sum(wk) / len(wk), (sum(prev) / len(prev) if prev else None)
            data[f"rtat:{sym}"] = {"week_mean": round(m, 2), "prior_week_mean":
                                   None if pm is None else round(pm, 2), "n": len(wk)}
            items.append(item(f"pos:rtat:{sym}", f"Retail sentiment in {sym} (RTAT10) "
                              f"averaged {m:+.2f} over {len(wk)} session(s)"
                              + (f" against {pm:+.2f} {w.week_before}" if pm is not None
                                 else "") + ".", 3, round(m, 2)))
    for sym in ("SPY", "QQQ", "NVDA", "TSLA"):
        x = change_over(st, "apewisdom.mentions", now, then, f"{sym}@wallstreetbets")
        if x:
            data[f"ape:{sym}"] = x
            items.append(item(f"pos:ape:{sym}", f"{sym} mentions on WallStreetBets: "
                              f"{x['level']:,.0f} ({_change(x)} {w.on}).", 4,
                              (x["level"], x["observed_at"])))
    for k, name in (("tic.flow_net_foreign", "Net foreign purchases of US long-term "
                     "securities"), ("tic.flow_total", "Total net TIC flows")):
        x = change_over(st, k, now, then)
        if x:
            from altdata.numeral_audit import scaled_display    # noqa: PLC0415
            disp = scaled_display(x["level"], x.get("level_units") or "usd") \
                or (f"${x['level']:,.0f}"         # W-1.2 item 2.8: its unit
                    if (x.get("level_units") or "usd") == "usd"
                    else f"{x['level']:,.0f}")
            data[k] = {**x, "level_display": disp}
            items.append(item(f"pos:{k}", f"{name}: {disp} for "
                              f"{x['observed_at'][:7]} (TIC, monthly).", 4,
                              (x["level"], x["observed_at"])))
    lead = leadership(st, now, then)
    if lead:
        srt = sorted([r for r in lead if len(r[0]) <= 4], key=lambda r: -r[1])
        if len(srt) >= 4:
            items.insert(0, item("pos:leadership", f"Leadership {w.on}: "
                                 + ", ".join(f"{n} {_signed(v, '%')}" for n, v in srt[:3])
                                 + "; lagging " + ", ".join(f"{n} {_signed(v, '%')}"
                                                           for n, v in srt[-3:]) + ".",
                                 1, srt))
        for lab, v in lead:
            if len(lab) > 4:
                items.append(item(f"pos:style:{lab}", f"{lab}: {_signed(v, '%')} "
                                  f"{w.on}.", 2, v))
        data["leadership"] = [{"name": n, "week_return_pct": v} for n, v in lead]
    else:
        nt.append(f"{w.poss} sector and style-pair returns (no closes stored)")
    subs = positioning_subsections(st, now, then, data, lead, rows, cadence)
    # THE CORRELATION LAYER'S ONE LINE (AQ-5, change order 10 Oct 2026, section
    # 9): the Weekly only, and only in a week a 30-vs-120-day break or a shift
    # on a NAMED ROW fired (config/correlation.yaml weekly.shift_pairs, ruled 10
    # Oct) -- otherwise nothing, not even a "no breaks" line. All-pairs shifts
    # are the Monthly's top five, in its slow layers.
    if cadence == "weekly":
        try:
            from altdata import correlation                      # noqa: PLC0415
            cl = correlation.weekly_line(st, now, then)
        except Exception as exc:                                 # noqa: BLE001
            log.warning("correlation line unavailable", exc_info=True)
            cl = None
            nt.append(f"the correlation layer's line: FAULT {type(exc).__name__}")
        if cl:
            data["correlations"] = {k: cl[k] for k in
                                    ("breaks", "shifts", "credit_sensitive_away")}
            subs.append({"title": "Cross-asset correlations", "lines": [cl["text"]],
                         "paragraph_wanted": False})
    # SIGNAL-TRIAGE BATCH 6 item 30 (amends SR-12; section 4 ruling 3): the
    # three-panel investor-allocation block.
    from . import index_carry_block as icb                      # noqa: PLC0415
    alloc = icb.positioning_subsection(st, now)
    if alloc:
        # Batch 6 item 38: the gold/equity ratio, printed beside the allocation
        # block ("record equity allocation and gold still low as a share of
        # financial wealth are one observation from two sides").
        from . import t1_rest_block                             # noqa: PLC0415
        gl = t1_rest_block.allocation_line(st, now)
        if gl:
            alloc["lines"] = list(alloc.get("lines") or []) + [gl]
        subs.append(alloc)
    return {"items": items, "not_tracked": nt, "data": data, "print_items": False,
            "subsections": subs, "_cftc_series": cftc, "_leadership": lead}


def positioning_subsections(st, now: str, then: str, data: dict, lead: list,
                            rows: list, cadence: str = "weekly") -> list[dict]:
    """T2.2 item 7: five sub-sections, each with its table and one paragraph."""
    from altdata import labels                                   # noqa: PLC0415
    w = Period.of(cadence)
    out = []
    # THE WEEK, ONE MONTH AND THREE MONTHS, and the 50/200-day count (T2.3
    # item 6), sector names from the display labels.
    sec = wsec.sector_table(st, now, then, lead, cadence)
    data["sectors_above_50d"] = sec["above_50d"]
    data["sectors_above_200d"] = sec["above_200d"]
    # THE GTM BATCH, PART 2 (GTM-10, 17 Oct 2026): the Weekly's leadership table
    # gains the one-year correlation to the 10-year as a column (a table cell,
    # within the budget); the Monthly's keeps its columns and carries the full
    # sector rows -- ours over one and five years, the Guide's beside -- as a
    # second table.
    from . import gtm_block                                     # noqa: PLC0415
    gtm10 = []
    if cadence == "weekly" and sec["table"]["rows"]:
        sec["table"] = {"columns": [*sec["table"]["columns"],
                                    gtm_block.SECTOR_CORR_COLUMN],
                        "rows": gtm_block.sector_corr_column(st, now,
                                                             sec["table"]["rows"])}
    elif cadence == "monthly":
        t10 = gtm_block.sector_table(st, now)
        if t10:
            gtm10 = [{"columns": t10["columns"], "rows": t10["rows"]}]
            note10 = t10["note"]
    out.append({"title": "Sector rotation and leadership", "table": sec["table"],
                "lines": [sec["line"]] if sec["line"] else [],
                **({"tables": gtm10, "table_note": note10} if gtm10 else {}),
                "not_tracked": [] if sec["table"]["rows"] else
                [f"{w.poss} sector returns"]})
    cf = []
    for inst, name in CFTC_CONTRACTS:
        x = data.get(f"cftc:{inst}")
        if x:
            cf.append([name[0].upper() + name[1:], f"{x['level']:,.0f}", _change(x),
                       "—" if x.get("z_2y") is None else f"{x['z_2y']:+.1f}",
                       "—" if x.get("change_z_4w") is None
                       else f"{x['change_z_4w']:+.1f}",
                       x["observed_at"]])
    # SR-36: the Treasury basis proxy, one code-written line under the CFTC table
    # (report-only; "(descriptive; unvalidated, n=0)").
    bp = basis_proxy_read(st, now)
    if bp:
        from altdata import basis_proxy                          # noqa: PLC0415
        data["basis_proxy"] = basis_proxy_data(bp)
    out.append({"title": "Speculative positioning (CFTC)",
                "table": {"columns": ["Contract", "Net speculative contracts",
                                      "Change", "Level z, two years",
                                      "Four-week change z", "As of"], "rows": cf},
                **({"lines": [basis_proxy.positioning_line(bp)]} if bp else {}),
                "not_tracked": [n for i, n in CFTC_CONTRACTS
                                if f"cftc:{i}" not in data]})
    # BATCH 5 ITEM 27 (ST-R4.27a): Treasury moves split overnight and session,
    # under the CFTC table and SR-36's line -- a co-signal of the Japan
    # slow-money set and of SR-36's unwind watch, never a flag of its own. The
    # Weekly's only, like the 10A blocks: the Monthly's Positioning keeps its
    # five read blocks (T3.1 item 10).
    if cadence == "weekly":
        from . import batch5b_block                             # noqa: PLC0415
        on = batch5b_block.positioning_subsection(st, now)
        if on:
            out.append(on)
    si = [[f"{sym} days to cover", f"{data[f'finra:{sym}']['level']:,.2f}",
           _change(data[f"finra:{sym}"]), data[f"finra:{sym}"]["observed_at"]]
          for sym in ("SPY", "QQQ", "IWM") if data.get(f"finra:{sym}")]
    # W-1.3b item 3.3: the section 10A standard -- TFF categories as a percent of
    # open interest -- and the ETF share counts, each with its level z and its
    # four-week change z. The Weekly's (the change order's scope); the Monthly's
    # Positioning keeps its five read blocks.
    if cadence == "weekly":
        out += positioning_10a(st, now, data, cadence)
    out.append({"title": "Short interest",
                "table": {"columns": ["Series", "Level", "Change", "Settlement"],
                          "rows": si}})
    rs = []
    from . import analytics as _an                              # noqa: PLC0415
    min_n = int((_an.load_config().get("positioning") or {}).get("sentiment_min_n") or 4)
    for sym in ("SPY", "QQQ", "IWM", "NVDA", "TSLA"):
        r = data.get(f"rtat:{sym}")
        if r:
            # W-1.3b item 3.3: below the sample threshold the row says so and
            # stays out of any composite.
            from . import analytics                             # noqa: PLC0415
            thin = analytics.thin_cell(int(r.get("n") or 0), min_n)
            r["thin"] = bool(thin)
            # W-1.2 item 2.8: each row names its unit.
            rs.append([f"{sym} retail sentiment (RTAT10 score, {w.mean})",
                       thin or f"{r['week_mean']:+.2f}",
                       "—" if r.get("prior_week_mean") is None
                       else f"{r['prior_week_mean']:+.2f}", f"n={r['n']}"])
    for sym in ("SPY", "QQQ", "NVDA", "TSLA"):
        x = data.get(f"ape:{sym}")
        if x:
            rs.append([f"{sym} WallStreetBets mentions (count)", f"{x['level']:,.0f}",
                       _change(x), x["observed_at"]])
    aaii = change_over(st, "aaii.bull_bear_spread", now, then)
    if aaii:
        data["aaii"] = aaii
        # SOURCE AND AS-OF ON THE ROW (rulings of 5 Oct, item 4).
        rs.append(["AAII bull-bear spread, points (source: AAII Sentiment Survey, "
                   f"weekly; as of {aaii['observed_at']})", f"{aaii['level']:+.1f}",
                   "—" if aaii.get("prior") is None
                   else f"{aaii['level'] - aaii['prior']:+.1f}", aaii["observed_at"]])
    data["sentiment_composite_members"] = [
        k for k, v in data.items() if k.startswith("rtat:")
        and v in _an.composite_members([v], min_n)]
    out.append({"title": "Retail sentiment",
                "table": {"columns": ["Series", w.This, "Prior or change",
                                      "As of"], "rows": rs},
                "not_tracked": [] if aaii else ["the AAII bull-bear spread"]})
    # A DECLARED LAG, NOT A STALE ROW (W-1.1 item 1.2): "lag: monthly (July,
    # released 2026-09-18)".
    tic = [[("Net foreign purchases of US long-term securities"
             if k == "tic.flow_net_foreign" else "Total net TIC flows"),
            data[k]["level_display"],
            wsec.lag_label(k, data[k]["observed_at"], data[k].get("available_at"))
            or data[k]["observed_at"][:7]]
           for k in ("tic.flow_net_foreign", "tic.flow_total") if data.get(k)]
    out.append({"title": "Foreign flows (TIC)",
                "table": {"columns": ["Series", "Level", "Period"], "rows": tic}})
    return out


def positioning_10a(st, now: str, data: dict, cadence: str = "weekly") -> list[dict]:
    """W-1.3b item 3.3: the TFF categories (leveraged funds, asset managers,
    dealers) for the financial futures the store holds, as a percent of open
    interest, and the ETF share counts; each with its level z and its four-week
    change z against two years. Series the store does not hold yet are named."""
    from . import analytics                                     # noqa: PLC0415
    cfg = analytics.load_config().get("positioning") or {}
    weeks = int(cfg.get("change_weeks") or 4)
    since = (dt.date.fromisoformat(now[:10])
             - dt.timedelta(days=int(cfg.get("z_window_days") or 730))).isoformat()
    tff = cfg.get("tff") or {}
    rows, tdata = [], []
    for c in tff.get("contracts") or []:
        for cat in tff.get("categories") or []:
            pts = series(st, f"cftc.tff_{cat['id']}_net_oi", now, c, since)
            if not pts:
                continue
            lvl = pts[-1][1]
            lz = analytics._z([v for _, v in pts[:-1]], lvl)
            cz = analytics.change_z(pts, weeks)
            czz = None if not cz else cz[1]
            rows.append([f"{c} futures", cat["label"], f"{lvl:+.1f}%",
                         analytics.zfmt(lz), analytics.zfmt(czz), pts[-1][0]])
            tdata.append({"contract": c, "category": cat["id"], "net_oi_pct": lvl,
                          "level_z": lz, "change_z_4w": czz, "as_of": pts[-1][0]})
    data["tff"] = tdata
    out = [{"title": "Futures positioning by trader type (CFTC TFF, % of open interest)",
            "table": {"columns": ["Contract", "Trader type", "Net, % of open interest",
                                  "Level z, two years", "Four-week change z", "As of"],
                      "rows": rows},
            "not_tracked": [] if rows else
            ["the CFTC TFF categories (leveraged funds, asset managers, dealers) "
             "as a percent of open interest: not stored yet"]}]
    erows, edata, missing = [], [], []
    for e in cfg.get("etf_shares") or []:
        pts = series(st, e["key"], now, None, since)
        if not pts:
            missing.append(e["label"])
            continue
        lvl = pts[-1][1]
        cz = analytics.change_z(pts, weeks)
        erows.append([e["label"], f"{lvl / 1e6:,.1f}m shares",
                      "—" if not cz else f"{cz[0] / 1e6:+,.1f}m shares",
                      analytics.zfmt(analytics._z([v for _, v in pts[:-1]], lvl)),
                      analytics.zfmt(None if not cz else cz[1]), pts[-1][0]])
        edata.append({"key": e["key"], "shares": lvl,
                      "change_4w": None if not cz else cz[0],
                      "change_z_4w": None if not cz else cz[1]})
    data["etf_shares"] = edata
    out.append({"title": "ETF share counts",
                "table": {"columns": ["Fund", "Shares", "Four-week change",
                                      "Level z, two years", "Four-week change z",
                                      "As of"], "rows": erows},
                "not_tracked": ([f"share counts not stored yet: {', '.join(missing)}"]
                                if missing else [])})
    return out


def analytics_blocks(built: dict, pmb: Optional[dict], fed: Optional[dict],
                     cfg: dict) -> None:
    """W-1.3b items 3.4 and 3.5, over the built sections: the event x venue
    matrix in What's priced for Ahead's tier-1 events, and the code-built
    playbook in the top event's slot (its frame sentences are written after
    the prose, in playbook_pass)."""
    from altdata import prediction_markets as pmk               # noqa: PLC0415
    from . import ahead, analytics                              # noqa: PLC0415
    acfg = analytics.load_config()
    cal = (built["ahead"].get("data") or {}).get("calendar") or []
    top = [r for r in cal if r.get("tier") == 1]
    markets = (pmb or {}).get("markets") or []
    th = float((((cfg.get("prediction_markets") or {}).get("disagreement_points")
                 or {}).get("venue_vs_fed_funds_implied")) or 15)
    mx = analytics.matrix(top, markets, fed, pmk.fomc_venue_odds(markets), th, acfg)
    pr = built["priced"]
    pr.setdefault("data", {})["matrix"] = mx["data"]
    # The matrix sits in the prediction-market block, as its second table: the
    # section keeps its three sub-chapters.
    pm = next((ss for ss in pr.get("subsections") or []
               if ss.get("title") == "Prediction markets"), None)
    if pm is None:
        pm = {"title": "Prediction markets"}
        pr.setdefault("subsections", []).append(pm)
    if mx["table"]["rows"]:
        pm.setdefault("tables", []).append(mx["table"])
    else:
        pr.setdefault("notes", []).append(
            "No tier-1 event of a priced class is scheduled in the coming week, so "
            "there is no matrix of the markets' prices.")
    slot = (built["ahead"].get("data") or {}).get("playbook")
    z_min = float(ahead.load_config().get("amplifier_z") or 1.5)
    pb = analytics.playbook(slot, (built.get("positioning") or {}).get("data"),
                            z_min, acfg, fed=fed)
    if pb:
        built["ahead"]["data"]["playbook"] = {**slot, "outcomes": pb["rows"],
                                              "playbook": pb}
        for ss in built["ahead"].get("subsections") or []:
            if ss.get("playbook"):
                ss["table"] = analytics.playbook_table(pb)
                ss["playbook"] = pb


def playbook_pass(ed: dict, *, client=None, model: Optional[str] = None) -> None:
    """W-1.3b item 3.5: one audited call for the playbook's three frame
    sentences, after the sections' prose; the code-built cells stand either way."""
    from . import analytics                                     # noqa: PLC0415
    ah = next((s for s in ed["sections"] if s["id"] == "ahead"), None)
    if not ah:
        return
    for ss in ah.get("subsections") or []:
        pb = ss.get("playbook")
        if not isinstance(pb, dict) or not pb.get("rows"):
            continue
        analytics.write_playbook(pb, client=client, model=model)
        ss["table"] = analytics.playbook_table(pb)
        if not str(pb.get("read_state") or "").startswith("published"):
            ss.setdefault("not_tracked", []).append(
                "the playbook's read sentences (" + str(pb.get("read_state")) + ")")
        (ah.setdefault("data", {}).setdefault("playbook", {}))["read_state"] = \
            pb.get("read_state")


def window(x: dict) -> str:
    """The real window of a weekly change: the two observation dates it spans
    (T2.1 item 14) -- a FRED series lags, so 'on the week' alone would hide
    which week."""
    a, b = x.get("prior_observed_at"), x.get("observed_at")
    if x.get("effective"):                  # W8-9: an announced, later-dated rate
        return asof_cell(x)
    return f"{a} to {b}" if a and a != b else f"as of {b}"


WEEK_PRICED = (("fred.breakeven_5y", "5-year breakeven"),
               ("fred.breakeven_10y", "10-year breakeven"),
               ("fred.breakeven_5y5y", "5-year, 5-year-forward breakeven"),
               ("umich.expect_5_10y", "Michigan 5-10 year expectations"),
               ("nyfed.sce_3y", "NY Fed 3-year expectations"))


def priced_week(st, now: str, then: str, cfg: dict, pmb, fed, fed_then,
                cadence: str = "weekly") -> dict:
    w = Period.of(cadence, cfg)
    b = stack_mod.priced_section(st, now, cfg, pmb, fed, fed_then)
    # THE WEEK'S CHANGE, not the day's (T2.1 item 14): the daily section's
    # series lines are replaced by each series' change over the week's window.
    b["items"] = [i for i in b["items"]
                  if not any(i["key"] == f"priced:{k}" for k, _ in WEEK_PRICED)]
    series = {}
    for k, name in WEEK_PRICED:
        x = change_over(st, k, now, then)
        if not x:
            continue
        series[name] = x
        b["items"].append(item(f"priced:{k}", f"{name} {_lvl(x)}, {_change(x)} "
                               f"{w.on} ({window(x)}).", 2,
                               (x["level"], x["change"])))
    b["data"]["series"] = series
    trig = (cfg.get("triggers") or {}).get("priced") or {}
    reason = None
    for k, th in (trig.get("moves_bp") or {}).items():
        x = change_over(st, k, now, then)
        if x and x.get("change") is not None and abs(x["change"]) >= th:
            reason = f"{k.split('.')[-1]} moved {_change(x)} {w.on} " \
                     f"(threshold {th} bp)"
            break
    rate_th = float(trig.get("fomc_implied_rate_next_four_meetings_bp") or 12.5)
    if not reason and fed and fed_then and fed.get("tracked"):
        was = {m["meeting"]: m["post_pct"] for m in fed_then.get("meetings") or []}
        for m in (fed.get("meetings") or [])[:4]:
            ch = derived.rate_bp_change(m["post_pct"], was.get(m["meeting"]))
            if ch is not None and abs(ch) >= rate_th:
                reason = (f"the implied rate after the {m['meeting']} meeting moved "
                          f"{_signed(ch, 'bp')} {w.on} (threshold {rate_th:g} bp)")
                break
    pm_th = float(trig.get("prediction_market_points") or 10)
    if not reason:
        for r in (pmb or {}).get("markets") or []:
            c = r.get("change_5s_points")
            if c is not None and abs(c) >= pm_th and not r.get("stale"):
                reason = (f"a watched market moved {c:+.1f} pts over five sessions "
                          f"(threshold {pm_th:g} pts)")
                break
    b["deep_reason"] = reason
    b["not_tracked"] = []
    b["print_items"] = False
    try:
        earn = wsec.earnings_block(st, now[:10], now, then, cadence=cadence)
    except Exception:                                           # noqa: BLE001
        earn = None
    b["_pmb"] = pmb
    b["subsections"] = priced_subsections(b, series, fed, earn)
    b.pop("_pmb", None)
    # SIGNAL-TRIAGE BATCH 6 (16 Oct 2026), section 4 ruling 2: items 40, 29 and
    # 35 under one "What's carrying the index" header. Item 35's margin-source
    # line belongs in the earnings block; outside the season it rides here.
    from . import index_carry_block as icb                      # noqa: PLC0415
    eb = next((ss for ss in b["subsections"]
               if str(ss.get("title", "")).startswith("Earnings")), None)
    if eb is not None:
        ml = icb.margin_line(st, now)
        if ml:
            eb["lines"] = list(eb.get("lines") or []) + [ml]
    carry = icb.priced_subsection(st, now, cadence, margin=eb is None)
    if carry:
        b["subsections"].append(carry)
    return b


def priced_subsections(b: dict, series: dict, fed: Optional[dict],
                       earnings: Optional[dict] = None) -> list[dict]:
    """T2.2 item 8: rates priced; prediction markets; surveyed expectations."""
    rows = []
    for m in ((fed or {}).get("meetings") or [])[:6]:
        rows.append([f"FOMC {m['meeting']}: implied rate after",
                     f"{m['post_pct']:.2f}%",
                     f"{round(100 * (m.get('move_probability_25bp') or 0)):.0f}% of a "
                     f"25 bp {m.get('direction') if m.get('direction') != 'hold' else 'move'}",
                     (fed or {}).get("as_of") or "—"])
    for name in ("5-year breakeven", "10-year breakeven",
                 "5-year, 5-year-forward breakeven"):
        x = series.get(name)
        if x:
            rows.append([name, _lvl(x), _change(x), window(x)])
    nt_rates = [] if (fed or {}).get("tracked") else [
        "the fed funds futures rate path: " + str((fed or {}).get("reason")
                                                   or "no contracts stored")]
    # PREDICTION MARKETS AS ONE TABLE (T2.5 item 9), the week's change beside
    # each venue's price; outages go to the footnote.
    from . import readability                                   # noqa: PLC0415
    pmb = b.get("_pmb")
    pmt = readability.pm_table(pmb, "5s")
    surveys = []
    for name in ("Michigan 5-10 year expectations", "NY Fed 3-year expectations"):
        x = series.get(name)
        if x:
            surveys.append([name, _lvl(x), _change(x), window(x)])
    return [{"title": "Rates priced: the fed-funds path and breakevens",
             "table": {"columns": ["Measure", "Level", "Priced or change", "As of"],
                       "rows": rows}, "not_tracked": nt_rates},
            {"title": "Prediction markets", "table": pmt,
             "not_tracked": (readability.pm_outages(pmb) if pmt["rows"]
                             else ["no prediction market stored"])},
            {"title": "Surveyed expectations and consensus",
             "table": {"columns": ["Survey", "Level", "Change", "Window"],
                       "rows": surveys},
             "not_tracked": ["the S&P 500 consensus EPS revision (the Weekly's 1% "
                             "trigger)", "one-year inflation expectations"]}] + (
        # IN SEASON ONLY (T2.3 item 9): nothing at all outside it.
        [{**earnings, "paragraph_wanted": False}] if earnings else [])


def story_statuses(stories: list[dict], st, now: str,
                   db_path: Optional[str] = None) -> dict:
    """W-1.3b item 3.1: each story's status and its reason, by the config's
    rules -- a drafted packet on a linked name, the story's variable at its
    implied level, a catalyst (declared, or a linked name's earnings) within
    the window, else a long-term theme."""
    from . import analytics, book_b                             # noqa: PLC0415
    from altdata import narratives as nmod                      # noqa: PLC0415
    acfg = analytics.load_config()
    try:
        ncfg = (nmod.load_config().get("narratives") or {})
    except Exception:                                           # noqa: BLE001
        ncfg = {}
    reg = book_b.register_rows(db_path)
    win = int(((acfg.get("narratives") or {}).get("catalyst_window_days")) or 30)
    earn: dict = {}
    if st is not None:
        try:
            from altdata import events as ev_mod                # noqa: PLC0415
            end = (dt.date.fromisoformat(now[:10]) + dt.timedelta(days=win)).isoformat()
            with ev_mod.EventStore(str(st.path)) as ev:
                for (payload, obs) in ev.conn.execute(
                        "SELECT payload, observed_at FROM events WHERE type = "
                        "'scheduled' AND observed_at >= ? AND observed_at <= ? "
                        "AND available_at <= ?", (now[:10], end, now)):
                    pl = json.loads(payload or "{}")
                    if pl.get("kind") == "earnings" and pl.get("symbol"):
                        earn.setdefault(str(pl["symbol"]).upper(), str(obs)[:10])
        except Exception:                                       # noqa: BLE001
            log.warning("earnings dates for the story status unavailable",
                        exc_info=True)

    def latest(key, inst=None):
        if st is None:
            return None
        r = st.latest_as_of(key, now, inst) if inst else st.latest_as_of(key, now)
        return None if not r else r.get("value_num")
    out = {}
    for s in stories:
        sid = str(s.get("id"))
        spec = {**(ncfg.get(sid) or {}), **s}
        out[sid] = analytics.story_status(sid, spec, acfg, now=now, latest=latest,
                                          earnings_dates=earn, register_rows=reg)
    return out


def narratives_week_section(nb: dict, wd: Optional[dict] = None,
                            voices: Optional[dict] = None, st=None,
                            now: Optional[str] = None,
                            db_path: Optional[str] = None) -> dict:
    """Section 8. Phase B (4 Oct 2026) makes it the synthesis: for each story,
    the week's sourced items for and against and who dissented; the voices table
    with weekly status; one consensus-against-contrarian line -- all from
    daily_cascade/voices_block.py over stored rows. The register's own lines
    (state, evaluations, proposals) follow."""
    stories = nb.get("narratives") or []
    items = list((voices or {}).get("items") or [])
    # PLAIN TITLES AND STATEMENTS, COUNTS IN WORDS (T2.2 item 9).
    for s in stories:
        items.append(item(f"narr:{s.get('id')}", wsec.story_line(
            str(s.get("id")), str(s.get("name")), str(s.get("state")),
            int(s.get("evidence_for") or 0), int(s.get("evidence_against") or 0)),
            2, (s.get("state"), s.get("evidence_for"), s.get("evidence_against"))))
    ev = nb.get("evaluations_this_week")
    if isinstance(ev, int) and ev:
        items.append(item("narr:evals", f"{ev} story evaluation(s) ran this week "
                          f"against the stored data.", 3, ev))
    props = nb.get("proposals") or []
    if props:
        items.append(item("narr:proposals", f"{len(props)} proposal(s) await the "
                          f"operator's confirmation.", 1, len(props)))
    wd = wd or {}
    if wd.get("state") in ("ok", "empty"):
        items.append(item("narr:filings", f"Filings since the last Weekly: "
                          f"{wd.get('filings_total', 0)}; headlines matched to a "
                          f"story: {wd.get('headlines_total', 0)}.", 3,
                          (wd.get("filings_total"), wd.get("headlines_total"))))
    if not items:
        items.append(item("narr:none", "No story is active in the register.", 1, "none"))
    from altdata import labels                                   # noqa: PLC0415
    # ONE FACT, ONCE (T2.5 item 1). Each story is one row of the stories table --
    # its state, the week's sourced items for and against, the register's
    # evidence and the week's dissent -- and each voice is one row of the voices
    # table; the lines that said either again are the section's data only. A
    # source the scan could not read is a footnote.
    week = {}
    for d in ((voices or {}).get("data") or {}).get("stories") or []:
        week[str(d.get("name"))] = d
    # W-1.3b item 3.1: counted by CLUSTER, never by item; the status from a
    # fixed vocabulary by rule; the steelman row from the scan's stored search.
    from . import analytics                                     # noqa: PLC0415
    status = story_statuses(stories, st, now or session.utc_iso(), db_path) \
        if stories else {}
    srows = []
    for s in stories:
        title = labels.story(s.get("id")).get("title") or s.get("name")
        w = week.get(str(s.get("name"))) or {}
        cl = w.get("clusters") or {"for": 0, "against": 0}
        stt = status.get(str(s.get("id"))) or ("long-term theme", "")
        srows.append([title, s.get("state"), f"{stt[0]} ({stt[1]})",
                      analytics.count_text(cl),
                      w.get("steelman") or "no counter-case queries declared",
                      ", ".join(w.get("dissent") or []) or "—"])
    nt = []
    for it in items:
        k = str(it["key"])
        if k.startswith(("voices:ev:", "voices:story:", "narr:evals")) or (
                k.startswith("narr:") and k[5:] in {str(s.get("id")) for s in stories}):
            it["show"] = False
        if k == "voices:unreachable":
            it["show"] = False
            nt.append(it["text"].rstrip("."))
    unreach = (voices or {}).get("unreachable") or []
    subs = ([{"title": "Stories",
              "table": {"columns": ["Story", "State", "Status",
                                    "This week, by event cluster",
                                    "Steelman (the counter-case)", "Dissent"],
                        "rows": srows}}] if srows else [])
    if unreach:
        subs.append({"title": "Sources the scan could not read",
                     "table": {"columns": ["Source", "Why", "Last scanned cleanly",
                                           "Active theses that depend on it"],
                               "rows": unreach}})
        nt = [x for x in nt if "unreachable" not in x.lower()]
    led = (voices or {}).get("ledger") or {}
    out = {"items": items,
           "subsections": subs,
           "reference": ([{"title": "The narrative ledger, this week: every item "
                                    "with its class, cluster and excerpt",
                           "table": led}] if led.get("rows") else []),
           "not_tracked": nt,
           "legend": wsec.states_legend([str(s.get("state")) for s in stories]),
           "data": {"stories": [{"title": labels.story(s.get("id")).get("title")
                                 or s.get("name"),
                                 "statement": labels.story(s.get("id")).get("statement"),
                                 "state": s.get("state"),
                                 "status": (status.get(str(s.get("id")))
                                            or ("long-term theme", ""))[0],
                                 "clusters": (week.get(str(s.get("name"))) or {})
                                 .get("clusters"),
                                 "evidence_for": s.get("evidence_for"),
                                 "evidence_against": s.get("evidence_against"),
                                 "last_changed": s.get("last_changed")}
                                for s in stories]}}
    if voices is not None:
        out["data"]["voices"] = voices.get("data")
        out["table"] = voices.get("table")
    else:
        out["not_tracked"] = ["the voices (the register could not be read)"]
    return out


def _voices_week(ending: str, now: str, st) -> Optional[dict]:
    try:
        from . import voices_block                              # noqa: PLC0415
        return voices_block.week_section(ending, now, str(st.path), item_fn=item)
    except Exception:                                           # noqa: BLE001
        log.warning("voices section unavailable", exc_info=True)
        return None


def graded_calls(cutoff: str, db_path: Optional[str] = None) -> dict:
    """The ledger's Brier by source over the last four weeks (brief 1.3 rule 3);
    the base-rate outlooks reported on their own line."""
    from altdata import probability_ledger as pl                # noqa: PLC0415
    since = (dt.datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
             - dt.timedelta(days=28)).isoformat()
    with pl.ProbabilityLedger(db_path) as led:
        rows = led.all_rows()
    done = [r for r in rows if r.get("resolved_at") and since <= str(r["resolved_at"])
            <= cutoff and r.get("brier") is not None]
    # THE BOOK B CANDIDATES (decision 6) are reported on their own line, never
    # pooled with any other source: a scanner's forecast is not a decision.
    cand_src = ("book_b_candidate", "dryrun.book_b_candidate")
    cands = [r for r in done if r["source"] in cand_src]
    done = [r for r in done if r["source"] not in cand_src]
    by: dict[str, list] = {}
    for r in done:
        by.setdefault(r["source"], []).append(r["brier"])
    cand_by: dict[str, list] = {}
    for r in cands:
        cand_by.setdefault(r["source"], []).append(int(r["outcome"]))
    candidates = [{"source": s, "n": len(o), "hits": sum(o),
                   "open": sum(1 for r in rows if r["source"] == s
                               and r.get("outcome") is None)}
                  for s, o in sorted(cand_by.items())]
    table = []
    for src, bs in sorted(by.items()):
        m = sum(bs) / len(bs)
        table.append({"source": src, "n": len(bs), "mean_brier": round(m, 4),
                      "vs_coin": round(m - pl.COIN_BRIER, 4),
                      "base_rate": src == "daily_close_outlook"})
    open_n = sum(1 for r in rows if r.get("outcome") is None
                 and r["source"] not in cand_src)
    return {"since": since[:10], "rows": table, "resolved": len(done),
            "unresolved": open_n, "coin_brier": pl.COIN_BRIER,
            "candidates": candidates,
            "candidates_open": sum(1 for r in rows if r["source"] in cand_src
                                   and r.get("outcome") is None)}


def candidates_line(calls: dict) -> str:
    """The Book B candidates' forecasts, on their own line (decision 6)."""
    rows = calls.get("candidates") or []
    live = [r for r in rows if not r["source"].startswith("dryrun.")]
    dry = [r for r in rows if r["source"].startswith("dryrun.")]

    def part(r):
        return (f"n={r['n']}, +1R first in {r['hits']} "
                f"({100.0 * r['hits'] / r['n']:.0f}%)" if r["n"] else "none resolved")
    txt = ("Book B candidates (the scanner's, taken or not; never pooled with the "
           "operator's decisions), last four weeks: "
           + ("; ".join(part(r) for r in live) if live else "none resolved"))
    if dry:
        txt += "; dry runs " + "; ".join(part(r) for r in dry)
    return txt + f"; {calls.get('candidates_open', 0)} open."


def read_attention_log(path: Optional[Path] = None) -> list[dict]:
    p = Path(path or ATTENTION_LOG)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(sitting|ruling)\s*\|\s*"
                     r"([\d.]+|—|-)\s*\|\s*(.*?)\s*\|\s*$", line)
        if m:
            mins = m.group(3)
            out.append({"date": m.group(1), "kind": m.group(2),
                        "minutes": float(mins) if re.match(r"[\d.]+$", mins) else None,
                        "note": m.group(4)})
    return out


def attention_counts(ending: str, cutoff: str, db_path: Optional[str] = None,
                     log_path: Optional[Path] = None) -> dict:
    """Item 4b's three counts for the week (Monday to the Sunday after it)."""
    from register.store import Register                         # noqa: PLC0415
    end = dt.date.fromisoformat(ending)
    mon = end - dt.timedelta(days=end.weekday())
    sun = mon + dt.timedelta(days=6)
    approved = deferred = 0
    with Register(db_path) as reg:
        rows = [dict(r) for r in reg.conn.execute("SELECT * FROM decisions")]
    prev_of = {r["superseded_by"]: r for r in rows if r.get("superseded_by")}
    for r in rows:
        day = str(r.get("created_at"))[:10]
        if not (mon.isoformat() <= day <= sun.isoformat()):
            continue
        before = prev_of.get(r["id"])
        if r.get("status") == "active" and (before is None
                                            or before.get("status") != "active"):
            approved += 1
        if r.get("status") == "declined" and r.get("abstention_reason") == \
                "attention_budget":
            deferred += 1
    log = [e for e in read_attention_log(log_path)
           if mon.isoformat() <= e["date"] <= sun.isoformat()]
    sit = [e for e in log if e["kind"] == "sitting"]
    minutes = sum(e["minutes"] or 0 for e in sit)
    return {"week": f"{mon.isoformat()} to {sun.isoformat()}",
            "packets_approved": approved, "packets_budget": PACKETS_PER_WEEK,
            "packets_deferred_attention_budget": deferred,
            "sittings": len(sit), "sitting_hours": round(minutes / 60.0, 2),
            "sitting_hours_budget": SITTING_HOURS_PER_WEEK,
            "sittings_untimed": sum(1 for e in sit if e["minutes"] is None),
            "rulings": sum(1 for e in log if e["kind"] == "ruling")}


def trigger_counts(sessions: list[str], st, cfg: dict) -> dict:
    """How many of the week's sessions each section-1.1 trigger fired on."""
    from altdata.prediction_markets import _close_cutoff        # noqa: PLC0415
    out = {"plumbing": [], "priced": []}
    for s in sessions:
        cut = _close_cutoff(dt.date.fromisoformat(s))
        try:
            pl = stack_mod.plumbing_section({"session": s}, st, cut, cfg)
            if pl.get("deep_reason"):
                out["plumbing"].append({"session": s, "reason": pl["deep_reason"]})
            pmb, fed, fed_prior = stack_mod.venues_and_path(s, cut, st)
            pr = stack_mod.priced_section(st, cut, cfg, pmb, fed, fed_prior)
            if pr.get("deep_reason"):
                out["priced"].append({"session": s, "reason": pr["deep_reason"]})
        except Exception as exc:                                # noqa: BLE001
            log.warning("trigger count for %s failed: %s", s, exc)
    return {"sessions": len(sessions), **out}


SOURCE_LABELS = {"daily_close_outlook": "base-rate outlooks (daily close)",
                 "narrative_register": "story forecasts (narrative register)",
                 "monthly_macro": "scenario weights (Monthly)"}


def source_label(src: str) -> str:
    return SOURCE_LABELS.get(src, str(src).replace("_", " "))


def ahead_week(p: dict, calls: dict, cal: Optional[dict] = None,
               watch: Optional[list] = None, pos: Optional[dict] = None,
               now: Optional[str] = None) -> dict:
    wa = p.get("week_ahead") or {}
    items = []
    # THE WEEK-AHEAD CALENDAR, IN FULL (T2.1 item 11, folded from the old Detail
    # tail): every tracked release in the window, one line a day. Tier-1
    # releases rank above the rest, so the budget's cut takes the routine ones.
    tier1 = ((stack_mod.config().get("triggers") or {}).get("plumbing") or {})         .get("tier1_events") or []
    by_day: dict = {}
    for r in (wa.get("releases") or {}).get("rows") or []:
        t = str(r.get("release_name") or "")
        if t and t not in by_day.setdefault(r["date"], []):
            by_day[r["date"]].append(t)
    for d in sorted(by_day):
        names = by_day[d]
        top = any(any(k.lower() in n.lower() for k in tier1) for n in names)
        items.append(item(f"ahead:{d}", f"{d}: " + "; ".join(names) + ".",
                          2 if top else 3, (d, names)))
    for d, evs in (wa.get("session_events") or {}).items():
        odd = [e for e in evs if e != "NORMAL"]
        if odd:
            items.append(item(f"ahead:sess:{d}", f"{d}: {', '.join(odd).lower().replace('_', ' ')}.",
                              3, odd))
    ear = wa.get("earnings") or {}
    for r in (ear.get("rows") or [])[:8]:
        items.append(item(f"ahead:earn:{r.get('date')}:{r.get('symbol')}",
                          f"{r.get('date')}: {r.get('symbol')} reports.", 3,
                          (r.get("date"), r.get("symbol"))))
    rows = calls.get("rows") or []
    scored = [r for r in rows if not r["base_rate"]]
    base = [r for r in rows if r["base_rate"]]
    items.append(item("ahead:calls", "Graded calls, last four weeks: " + (
        "; ".join(f"{source_label(r['source'])} n={r['n']}, Brier "
                  f"{r['mean_brier']:.3f}" for r in scored) if scored
        else "none resolved") + ".", 1,
        [(r["source"], r["n"], r["mean_brier"]) for r in scored]))
    items.append(item("ahead:base_rates", "Base-rate outlooks, last four weeks: " + (
        "; ".join(f"n={r['n']}, Brier {r['mean_brier']:.3f} against a coin's "
                  f"{calls['coin_brier']:.2f}" for r in base) if base
        else "none resolved") + ".", 1, [(r["n"], r["mean_brier"]) for r in base]))
    items.append(item("ahead:candidates", candidates_line(calls), 1,
                      [(r["source"], r["n"], r["hits"])
                       for r in calls.get("candidates") or []]))
    calls_table = {"columns": ["Source", "Resolved (4 wk)", "Mean Brier",
                               "Against a coin"],
                   "rows": [[source_label(r["source"]),
                             r["n"], f"{r['mean_brier']:.3f}",
                             f"{r['vs_coin']:+.3f}"] for r in rows]}
    # THE DAY-BY-DAY CALENDAR (T2.2 item 10) is the section's table; what the
    # system is watching and the graded calls follow as sub-sections.
    subs = [{"title": "Watching",
             "lines": watch or ["No contradiction is open and no count is running."]},
            # The lines only when the table is empty: one fact, once (T2.5).
            {"title": "Graded calls, last four weeks", "table": calls_table,
             "lines": ([] if calls_table["rows"] else
                       [i["text"] for i in items if i["key"] in ("ahead:calls",
                                                                 "ahead:base_rates")])
             # The candidates' line always, on its own (decision 6).
             + [i["text"] for i in items if i["key"] == "ahead:candidates"]}]
    nt = ["scenario weights with odds and signposts (scenario set #1, Audit #4 "
          "agenda item 2)"]
    # THE MARKET-MOVING CALENDAR (W-1.3a item 3.9): one ranked table, earnings,
    # the hand-seeded calendars and the register's dated events folded in; the
    # routine rows to the reference tables, counted; the top event's playbook
    # slot (item 3.5, filled in W-1.3b).
    from . import ahead                                         # noqa: PLC0415
    try:
        ah = ahead.build(cal, p, pos, now or p.get("as_of") or session.utc_iso(),
                         min_outcomes=int((stack_mod.config().get("storyline") or {})
                                          .get("family_min_outcomes") or 2))
    except Exception:                                           # noqa: BLE001
        log.warning("the ranked calendar is unavailable", exc_info=True)
        ah = None
    if ah is None:
        if cal and cal.get("routine_not_listed"):
            nt.append(f"{cal['routine_not_listed']} routine data releases and bill "
                      f"auctions not listed")
        return {"items": items, "print_items": False,
                "table": (cal or {}).get("table") or {"columns": [], "rows": []},
                "subsections": subs,
                "data": {"graded_calls": calls,
                         "calendar": [{k: r[k] for k in ("date", "time", "event",
                                                         "tier", "consensus")}
                                      for r in (cal or {}).get("rows") or []],
                         "watching": watch or []},
                "not_tracked": nt}
    if ah["playbook"]:
        # The slot: W-1.3b's code-built outcome table fills its lines.
        subs.append({"title": f"Playbook: {ah['playbook']['event']}",
                        "lines": [], "playbook": ah["playbook"]})
    return {"items": items, "print_items": False, "table": ah["table"],
            "subsections": subs,
            "summarised": list(ah["collapsed"]),
            "reference": ah["reference"],
            "notes": ah["notes"],
            "data": {"graded_calls": calls,
                     "calendar": [{k: r.get(k) for k in
                                   ("date", "time", "event", "tier", "consensus",
                                    "rank", "cls", "why", "amplify")}
                                  for r in ah["rows"]],
                     "playbook": ah["playbook"],
                     "routine_count": ah["routine_count"],
                     "watching": watch or []},
            "not_tracked": nt}


def scanner_calendar(p: dict) -> list[dict]:
    """The week ahead for the scanner's catalysts: earnings by symbol, and the
    tracked releases with the tier-1 ones marked."""
    wa = p.get("week_ahead") or {}
    tier1 = (((stack_mod.config().get("triggers") or {}).get("plumbing") or {})
             .get("tier1_events") or [])
    out = [{"date": r.get("date"), "event": f"{r.get('symbol')} earnings",
            "symbol": r.get("symbol")}
           for r in (wa.get("earnings") or {}).get("rows") or [] if r.get("symbol")]
    for r in (wa.get("releases") or {}).get("rows") or []:
        name = str(r.get("release_name") or "")
        if name and r.get("date"):
            out.append({"date": r["date"], "event": name, "symbol": None,
                        "tier1": any(k.lower() in name.lower() for k in tier1)})
    return out


def chain_walls(book: Optional[dict]) -> dict:
    """symbol -> [(label, level)]: the walls the chain store names, for the
    scanner's reclaim levels."""
    out: dict[str, list] = {}
    for i in (book or {}).get("instruments") or []:
        for lv in i.get("levels") or []:
            if lv.get("type") in ("call_wall", "put_wall") and lv.get("value"):
                out.setdefault(str(i.get("symbol")), []).append(
                    (f"the {lv['label']}", lv["value"]))
    return out


def book_week(p: dict, attn: dict, trig: dict, bz: Optional[str],
              ending: Optional[str] = None, db_path: Optional[str] = None,
              prior: Optional[dict] = None, walls: Optional[dict] = None,
              dry_run: bool = False) -> dict:
    rg = p.get("register") or {}
    rb = rg.get("rule_breaks") or {}
    items = [item("book:open", f"{rg.get('open_count', 0)} open decision(s), "
                  f"{rg.get('drafts_count', 0)} draft(s).", 1,
                  (rg.get("open_count"), rg.get("drafts_count")))]
    # THE WEEK'S BREAKS ARE THE LISTED ONES. The block also carries a running
    # total and a count of blocked decisions -- different quantities, never summed.
    listed = rb.get("rule_breaks_listed") or []
    kinds = sorted({str(b.get("kind")).replace("_", " ") for b in listed})
    items.append(item("book:breaks", f"{len(listed)} rule break(s) this week"
                      + (f" ({', '.join(kinds)})" if kinds else "")
                      + f"; {rb.get('rule_breaks_total', 0)} on the register to date.",
                      2, (len(listed), rb.get("rule_breaks_total"))))
    if rb.get("decision_blocked_this_week"):
        items.append(item("book:blocked", f"{rb['decision_blocked_this_week']} "
                          f"decision(s) blocked at entry this week.", 2,
                          rb["decision_blocked_this_week"]))
    if bz:
        items.append(item("book:z", f"Against Book Z, {bz}.", 2, bz))
    pk = rg.get("packet_fields") or {}
    if isinstance(pk, dict) and pk.get("entries_this_week") is not None:
        items.append(item("book:packets", f"New decisions entered this week: "
                          f"{pk['entries_this_week']} ({pk.get('setup_unclassified', 0)} "
                          f"with an unclassified setup; "
                          f"{pk.get('review_changed_not_none', 0)} changed at review).",
                          3, (pk["entries_this_week"], pk.get("review_changed_not_none"))))
    for b in listed:
        items.append(item(f"book:rb:{b.get('session')}:{b.get('instrument')}",
                          f"{b.get('session')}: {str(b.get('kind')).replace('_', ' ')} "
                          f"on {b.get('instrument')} -- {b.get('reason')}.", 3,
                          b.get("reason")))
    # DURATIONS IN MINUTES (T2.5 item 6): "22 of 120 minutes", never "0.37 of 2
    # hours". The table carries the counts; the item is its data and change mark.
    from .readability import minutes_of, plural                 # noqa: PLC0415
    sat, budget_min = minutes_of(attn["sitting_hours"]), \
        minutes_of(attn["sitting_hours_budget"])
    it = item("book:attention",
              f"Attention: {attn['packets_approved']} of "
              f"{plural(attn['packets_budget'], 'packet')} approved"
              + (f", {attn['packets_deferred_attention_budget']} deferred by "
                 f"the budget" if attn['packets_deferred_attention_budget']
                 else "")
              + f"; {sat} of {plural(budget_min, 'minute')} sitting"
              + f"; {plural(attn['rulings'], 'ruling')} taken in chat.", 1,
              (attn["packets_approved"], attn["sitting_hours"], attn["rulings"]))
    it["show"] = False
    items.append(it)
    items.append(item("book:triggers",
                      f"Triggers fired: Plumbing deep on {len(trig['plumbing'])} and "
                      f"What's priced deep on {len(trig['priced'])} of "
                      f"{trig['sessions']} session(s).", 2,
                      (len(trig["plumbing"]), len(trig["priced"]))))
    # W-1.3a items 3.8 and 3.6: Book B's candidates (the scanner's hook) and the
    # sitting's productivity line, beside the compliance line above.
    from . import book_b                                        # noqa: PLC0415
    ending = ending or p.get("week_ending")
    now = p.get("as_of") or session.utc_iso()
    run, ledger = None, {}
    try:
        # THE BOOK B SCANNER (brief of 12 Oct 2026), over Friday's close: the
        # week ahead's calendar for each candidate's catalyst, the chain's walls
        # for the reclaim levels.
        run = book_b.scanner_run(ending, db_path, cutoff=now,
                                 calendar=scanner_calendar(p), walls=walls,
                                 sessions=p.get("sessions_in_week") or None)
        scan = None if run is None else run["candidates"]
        pbook = next((s for s in (prior or {}).get("sections") or []
                      if s.get("id") == "book"), {})
        flow = book_b.sitting_flow(ending, db_path, scan,
                                   (pbook.get("data") or {}).get("candidates_printed"),
                                   approved=attn["packets_approved"])
        subs, kept = book_b.subsections(scan, flow, run)
        notes = list(subs[0].pop("notes", []))
    except Exception:                                           # noqa: BLE001
        # The section prints without the two blocks rather than not at all.
        log.warning("Book B's candidates and productivity are unavailable",
                    exc_info=True)
        scan, flow, kept = None, {}, {"printed": [], "reference": []}
        subs = [{"title": book_b.HEADING, "lines": [book_b.NO_SCANNER],
                 "candidates": []}]
        notes = ["The candidates and the productivity line could not be read."]
    # GRADING FROM DAY ONE (decision 6): every candidate, taken or not, a ledger
    # forecast under its setup and id -- a dry run under its own namespace --
    # and the open ones the stored closes now decide, resolved.
    if scan is not None:
        try:
            from altdata import book_b_scanner as bbs           # noqa: PLC0415
            ledger["graded"] = len(bbs.grade(db_path, ending, now, dry_run))
            # The standing candidates and the flip zone's refusals (ruled 13 Oct
            # 2026: refused at the gate, still graded).
            ledger["recorded"] = len(bbs.record_forecasts(bbs.graded(run), ending,
                                                          now, db_path, dry_run))
            ledger["source"] = bbs.source_name(dry_run)
        except Exception as exc:                                # noqa: BLE001
            log.warning("the candidates' forecasts were not written", exc_info=True)
            ledger["error"] = f"{type(exc).__name__}: {exc}"
    return {"items": items, "subsections": subs, "notes": notes,
            "reference": kept.get("reference") or [],
            "data": {"attention": attn, "triggers": trig, "book_z": bz,
                     "flow": {k: v for k, v in flow.items()},
                     "candidates": subs[0]["candidates"],
                     "candidates_printed": kept["printed"],
                     "scanner": "absent" if scan is None else "present",
                     "scanner_ledger": ledger,
                     "scanner_refused": len((run or {}).get("refused") or []),
                     "scanner_hooks": (run or {}).get("hooks")},
            "table": {"columns": ["Count", "This week", "Budget"],
                      "rows": [["Packets approved", attn["packets_approved"],
                                attn["packets_budget"]],
                               ["Sitting time", plural(sat, "minute"),
                                plural(budget_min, "minute")],
                               ["Rulings in chat", attn["rulings"], "measured"]]}}


def read_week(pmb: Optional[dict], wbd: Optional[dict] = None) -> dict:
    items = []
    th = 10.0
    # ONE LINE PER VENUE EVENT: a CPI event's strikes are one belief across legs,
    # so the event's largest five-session move stands for it (as the shock does).
    best: dict = {}
    for r in (pmb or {}).get("markets") or []:
        c = r.get("change_5s_points")
        if c is None or abs(c) < th or r.get("stale"):
            continue
        k = (r["venue"], r.get("event_id") or r["instrument"])
        if k not in best or abs(c) > abs(best[k]["change_5s_points"]):
            best[k] = r
    for r in sorted(best.values(), key=lambda x: -abs(x["change_5s_points"])):
        c = r["change_5s_points"]
        it = item(f"read:pm5:{r['instrument']}",
                  stack_mod.shock_sentence(r, "over five sessions", c), 1,
                  (r["probability"], c))
        # The move prints once, in What's priced's table (T2.5 items 1 and 9).
        it["show"] = False
        items.append(it)
    # THE WEEK BY DAY (T2.2 item 3): the table the opening paragraph reads, and
    # the press's own attributions, each with its URL -- never our cause.
    wbd = wbd or {}
    for n, line in enumerate(wbd.get("attributions") or []):
        items.append(item(f"read:attr:{n}", line, 2, line))
    return {"items": items[:4] + [i for i in items if i["key"].startswith("read:attr")],
            "table": wbd.get("table"),
            # COINCIDENCE, NOT CAUSATION (W-1.1 item 1.6): the daily table is
            # headed as what happened alongside each session, never why.
            "table_note": ("Events alongside the session: what coincided with each "
                           "day's move, not what caused it.") if wbd.get("table") else None,
            "data": {"five_session_moves": [i["text"] for i in items
                                            if i["key"].startswith("read:pm5")],
                     "week_by_day": wbd.get("data") or []}}


# ---------------------------------------------------------------------------
# The z of each row's move (W-1.1 item 1.0b)
# ---------------------------------------------------------------------------
# PLUMBING'S FIXED ROWS: the printed name -> (registry key, instrument).
PLUMB_ROW_KEYS = {
    "Net liquidity (Fed balance sheet less TGA and RRP)": ("calc.net_liquidity", None),
    "Bank reserves (H.4.1)": ("fred.bank_reserves", None),
    "Treasury General Account (H.4.1)": ("fred.tga", None),
    "Reverse repo (RRP)": ("fred.rrp", None),
    "SOFR": ("fred.sofr", None), "IORB": ("fred.iorb", None),
    "Investment-grade OAS": ("fred.ig_oas", None), "CCC OAS": ("fred.ccc_oas", None),
    "Copper, front future ($/lb; a growth gauge)": ("yfinance.mkt_copper_front", None),
    "USD/JPY (yen per dollar)": ("yfinance.mkt_usdjpy", None),
    "EUR/USD (dollars per euro)": ("yfinance.mkt_eurusd", None),
    "USD/CNY (yuan per dollar)": ("yfinance.mkt_usdcny", None),
    "Japan 10-year (JGB)": ("mof.jgb_10y", None),
    "Japan 30-year (JGB)": ("mof.jgb_30y", None),
    "VIX": ("yfinance.mkt_vix", None),
    "SPY 20-day realized against the VIX": ("calc.vol_spy_realized_20d", None),
    "MOVE (Treasury volatility)": ("yfinance.mkt_move", None),
    "SKEW (tail-risk pricing)": ("yfinance.mkt_skew", None),
}
Z_SECTIONS = ("tape", "plumbing", "positioning", "priced", "mechanics")


def row_keys(built: dict) -> dict:
    """{printed row name: (registry key, instrument)} for every row whose series
    the Weekly can name: Plumbing's, the tape set's, the CFTC contracts, the
    sectors, What's priced's series, the tier-1 releases' headlines."""
    from altdata import labels                                   # noqa: PLC0415
    from altdata.sources.yfinance_source import SECTOR_KEYS      # noqa: PLC0415
    out: dict = {n: (k, None) for k, n in PLUMB + WEEK_PRICED}
    out.update(PLUMB_ROW_KEYS)
    for t in bars_mod.tape():
        if t.get("daily"):
            out[t["label"]] = (t["daily"], None)
    for inst, name in CFTC_CONTRACTS:
        out[name[0].upper() + name[1:]] = ("cftc.noncomm_net", inst)
    for k in SECTOR_KEYS:
        out[labels.sector(k.replace("mkt_", "").upper())] = (f"yfinance.{k}", None)
    for r in ((built.get("plumbing") or {}).get("data") or {}).get("tier1_releases") or []:
        out[f"{r['release']}: {r['label']}"] = (r["series"], None)
    return out


def annotate_moves(built: dict, st, now: str, days: int = 7,
                   cfg: Optional[dict] = None) -> None:
    """Each budgeted section's `_move_z` -- {row name: {z, n, reason}} -- and
    Plumbing's `_row_block` (its bucket, config monthly_plumbing_buckets), in
    the section's data, where figure_budget reads them. The z is of the row's
    change over `days` against the series' own trailing-year changes of that
    length (derived.period_change_z), in the unit the row prints: a percent
    change for a price, a difference for a rate, a spread or a count."""
    from . import figure_budget as fb                           # noqa: PLC0415
    keys = row_keys(built)
    since = (dt.date.fromisoformat(now[:10]) - dt.timedelta(days=days + 400)).isoformat()
    cache: dict = {}
    bcfg = (cfg or stack_mod.config()).get("monthly_plumbing_buckets") or {}
    for sid in Z_SECTIONS:
        b = built.get(sid)
        if not b:
            continue
        zmap, blocks = {}, {}
        tables = [(sid, b.get("table"))] + [(ss.get("title"), ss.get("table"))
                                            for ss in b.get("subsections") or []]
        for where, t in tables:
            for m in fb.table_moves(t, str(where or ""), "Week"):
                name = m["name"]
                if sid == "plumbing":
                    from monthly_macro.stack import bucket_of    # noqa: PLC0415
                    blocks[name.strip().lower()] = bucket_of(
                        name, (keys.get(name) or (None,))[0], bcfg)
                if m.get("kind") != "move" or name not in keys:
                    continue
                key, inst = keys[name]
                unit = (fb.parse_figure(m["change"]) or (0, ""))[1]
                unit = unit if unit in ("%", "bp") else ""
                if (key, inst) not in cache:
                    cache[(key, inst)] = series(st, key, now, inst, since)
                lu = derived.level_units_of(key)
                zmap[name.strip().lower()] = derived.period_change_z(
                    cache[(key, inst)], now[:10], unit, lu, days)
        b.setdefault("data", {})["_move_z"] = zmap
        if blocks:
            b["data"]["_row_block"] = blocks


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def build(p: dict, book: dict, prior: Optional[dict] = None,
          db_path: Optional[str] = None, log_path: Optional[Path] = None,
          dry_run: bool = False) -> tuple:
    cfg = stack_mod.config()
    ending = p["week_ending"]
    now = p.get("as_of") or session.utc_iso()
    then = week_ago(now)
    sessions = p.get("sessions_in_week") or []
    wis = p.get("week_in_state") or {}
    extras: dict[str, Any] = {}
    with observations.ObservationStore(db_path) as st:
        pmb, fed, _ = stack_mod.venues_and_path(ending, now, st)
        try:
            from altdata import fed_funds                       # noqa: PLC0415
            fed_then = fed_funds.path_as_of(then, st)
        except Exception:                                       # noqa: BLE001
            fed_then = None
        pos = positioning_week(st, now, then)
        extras["cftc"] = pos.pop("_cftc_series")
        extras["leadership"] = pos.pop("_leadership")
        trig = trigger_counts(sessions, st, cfg)
        try:
            from altdata import benchmark                       # noqa: PLC0415
            bz = benchmark.book_line(now, st).get("text")
            # weekly-fixes-7 item 6: the week's window beside since-inception,
            # so "this week" in the book's opener has a figure to stand on.
            bzw = benchmark.week_line(then[:10], now, st).get("text")
            bz = "; ".join(x for x in (bzw, bz) if x) or None
        except Exception:                                       # noqa: BLE001
            bz = None
        from .stack_close import _contradiction_history          # noqa: PLC0415
        opened = [c for c in wis.get("contradictions") or []
                  if c.get("open_state") == "open"]
        hist = {c["id"]: _contradiction_history(st, c["id"], now) for c in opened}
        rel = tier1_releases(st, now, then)
        wbd = wsec.week_by_day(st, sessions, ending, now, then, rel, str(st.path))
        tape = stack_mod.tape_section(book, vp_windows=None)
        tt = wsec.tape_table(book, ending)
        oi = wsec.overnight_intraday(st, sessions, ending, now)
        # THE VOLUME PROFILE (VP-1 item 7): the week's value area against the
        # prior week's, beside the levels; the close's session table is not the
        # Weekly's. The storyline moves both into the detail tables, the value
        # area directly after the named levels (storyline.move_daily_tables).
        from altdata import volume_profile as vp                # noqa: PLC0415
        vpt = vp.table(book.get("instruments") or [], "week", "prior_week",
                       {t["id"]: t.get("unit") for t in bars_mod.tape()})
        tape.update({"table": tt["table"], "print_items": False,
                     "subsections": [
                         {"title": "Levels", "table": tt["levels_table"],
                          "paragraph_wanted": False},
                         *([{"title": "Value area: the week against the prior week",
                             "table": {k: vpt[k] for k in ("columns", "rows")},
                             "not_tracked": vpt["not_tracked"],
                             "paragraph_wanted": False}] if vpt["rows"] else []),
                         # OVERNIGHT AGAINST THE CASH SESSION (T2.3 item 1)
                         {"title": "SPY overnight against the cash session",
                          "table": oi["table"], "paragraph_wanted": False}]})
        tape["data"] = {**(tape.get("data") or {}),
                        "overnight_intraday": {"sessions": oi["rows"],
                                               "week": oi["totals"]},
                        "volume_profile": vpt["data"]}
        try:
            cal = wsec.calendar_week(st, ending, now, pmb)
        except Exception:                                       # noqa: BLE001
            log.warning("calendar unavailable", exc_info=True)
            cal = None
        # weekly-fixes-7 item 4: Watching reads section 4's counter (the same
        # state_dates over the stored objects), never persistence_days.
        watch = wsec.watching(st, now, opened, pmb, fed,
                              dates=wsec.state_dates(stored_objects(st, now)))
        from altdata import move_screen                         # noqa: PLC0415
        screen = move_screen.result_for(st, ending, now)
        mech = mechanics_week(st, sessions, now, wis, cfg,
                              computed_dir=p.get("computed_dir"), ending=ending)
        # W8-3: the Tape's flip words from Mechanics' close-vs-flip column.
        fw = wsec.apply_flip_words(tape, mech)
        if fw:
            tape["subsections"][0]["table_note"] = (
                f"SPY's gamma flip over the week: {fw['words']} (each session's "
                f"close against that morning's flip, as Mechanics prints it; the "
                f"named level is the last session's close capture, the next "
                f"session's level).")
        built = {
            "read": read_week(pmb, wbd),
            "tape": tape,
            "mechanics": mech,
            "misfit": misfit_week(wis, pmb, hist, screen=screen,
                                  dates=wsec.state_dates(stored_objects(st, now)),
                                  st=st, now=now),
            "plumbing": plumbing_week(st, now, then, book, auction_block=True),
            "positioning": pos,
            "priced": priced_week(st, now, then, cfg, pmb, fed, fed_then),
            "narratives": narratives_week_section(p.get("narratives") or {},
                                                  p.get("weekend_developments") or {},
                                                  _voices_week(ending, now, st),
                                                  st=st, now=now, db_path=db_path),
            "ahead": ahead_week(p, graded_calls(now, db_path), cal, watch,
                                pos=pos.get("data"), now=now),
            "book": book_week(p, attention_counts(ending, now, db_path, log_path),
                              trig, bz, ending=ending, db_path=db_path, prior=prior,
                              walls=chain_walls(book), dry_run=dry_run),
        }
        # SIGNAL-TRIAGE BATCH 6 item 43: the growth lead's line in Ahead.
        from . import t1_rest_block                             # noqa: PLC0415
        ah43 = t1_rest_block.ahead_subsection(st, now)
        if ah43:
            built["ahead"].setdefault("subsections", []).append(ah43)
        # THE CRYPTO BASKET (12 Oct 2026): a reference-tier table after the
        # sections, and ONE read-path line in What doesn't fit only when
        # something happened to a basket name -- silence otherwise.
        try:
            from altdata import crypto_basket                   # noqa: PLC0415
            cb = crypto_basket.weekly_block(st, ending[:10], now)
        except Exception:                                       # noqa: BLE001
            log.warning("crypto basket unavailable", exc_info=True)
            cb = None
        if cb:
            built["misfit"].setdefault("data", {})["crypto_basket_events"] = [
                {k: e.get(k) for k in ("kind", "name", "date", "text", "z")}
                for e in cb["events"]]
            if cb["line"]:
                built["misfit"]["items"].append(
                    item("misfit:crypto_basket", cb["line"], 2, cb["line"]))
        # THE CRYPTO FLOWS BLOCK (Batch 4 Tranche A, CD-9; 17 Oct 2026): at most
        # 12 lines, a table of its own in Positioning & flows, read from the
        # store with each line's data-as-of; no paragraph, no chart. The flags
        # never print (altdata/crypto_blocks.py).
        try:
            from altdata import crypto_blocks                   # noqa: PLC0415
            built["positioning"].setdefault("subsections", []).append(
                crypto_blocks.weekly_block(st, now))
        except Exception:                                       # noqa: BLE001
            log.warning("crypto flows block unavailable", exc_info=True)
        em_week(built, screen, ending)
        # W-1.3b items 3.4 and 3.5: What's priced's event x venue matrix over
        # Ahead's top events, and the top event's playbook.
        try:
            analytics_blocks(built, pmb, fed, cfg)
        except Exception:                                       # noqa: BLE001
            log.warning("the matrix and the playbook are unavailable", exc_info=True)
        try:
            annotate_moves(built, st, now, cfg=cfg)
        except Exception:                                       # noqa: BLE001
            # The ranking falls back to relative-to-level; the edition prints.
            log.warning("move z unavailable", exc_info=True)
        extras["rates"] = {name: series(st, k, now, since=(
            dt.date.fromisoformat(now[:10]) - dt.timedelta(days=365)).isoformat())
            for k, name in (("fred.yield_2y", "2-year"), ("fred.yield_10y", "10-year"),
                            ("fred.yield_30y", "30-year"), ("fred.hy_oas", "HY OAS"))}
        extras["contradictions"] = {}
        from .stack_close import _contradiction_history          # noqa: PLC0415
        for c in (built["misfit"]["data"].get("open_contradictions") or []):
            extras["contradictions"][c["name"]] = _contradiction_history(st, c["_id"], now)
    sections = stack_mod.assemble(built, cfg, prior, "weekly")
    # W-1.3a: the keys assemble does not carry -- a section's one-line summaries
    # (W-1.2 item 2.6), its reference rows and its notes.
    for s in sections:
        for k in ("summarised", "reference", "notes"):
            if (built.get(s["id"]) or {}).get(k):
                s[k] = list(built[s["id"]][k])
    tag_facts(sections, tt.get("row_ids") or [], oi.get("rows") or [],
              wbd.get("data") or [], book)
    # "UNVALIDATED" (W-1.1 item 1.7): a footnote in each section that prints a
    # descriptive classification; the glossary carries one entry each.
    classes = wsec.classifications(cfg, db_path)
    wsec.unvalidated_notes(sections, classes)
    changed = wsec.changed_since({}, wis, p, trig,
                                 (built["narratives"].get("data") or {})
                                 and {"data": (built["narratives"].get("data") or {})
                                      .get("voices") or {}})
    detail = stack_mod.move_screen_detail(screen, "weekly")
    ed = {"report": "weekly_stack", "session": ending, "week_ending": ending,
          "detail": detail,
          "changed_since": changed,
          "config_version": cfg.get("version"), "as_of": now,
          "prior_session": (prior or {}).get("week_ending"),
          "sections": sections, "budget": (cfg.get("budget") or {}).get("weekly"),
          "glossary_extra": wsec.unvalidated_glossary(classes)}
    if cb:
        ed["detail"] = list(ed.get("detail") or []) + [cb["detail"]]
    # weekly-fixes-7 item 14: a reference table whose every cell is a gap prints
    # as one line.
    from . import readability as _rd                            # noqa: PLC0415
    ed["detail"] = [_rd.collapse_gap_detail(d) for d in ed.get("detail") or []]
    return ed, extras


def em_week(built: dict, screen: Optional[dict], ending: str) -> None:
    """SR-46(c) and the EM calendar on the Weekly: the EM leg as a table under
    Plumbing & rates (its items do not print), and the quarter's hand-seeded EM
    events under Ahead."""
    from altdata import move_screen                              # noqa: PLC0415
    sp = [x for x in ((screen or {}).get("em") or {}).get("spreads") or []
          if x.get("available")]
    if sp and built.get("plumbing") is not None:
        rows = [[x["label"], f"{x['level']:.2f}%",
                 "—" if x.get("change5_bp") is None else _signed(round(x["change5_bp"]), "bp"),
                 (f"{move_screen._ord(x['pct_full'])} since {x['first']}"
                  + (f"; {move_screen._ord(x['pct_5y'])} of five years"
                     if x.get("five_year_complete") else ""))] for x in sp]
        built["plumbing"].setdefault("subsections", []).append(
            {"title": "EM leg", "paragraph_wanted": False,
             "table": {"columns": ["Series", "Level", "Week", "Percentile (window)"],
                       "rows": rows}})
    cal = move_screen.em_calendar(ending)
    if cal and built.get("ahead") is not None:
        built["ahead"].setdefault("subsections", []).append(
            {"title": "EM calendar", "lines": [move_screen.calendar_line(e) for e in cal]})
def tag_facts(sections: list[dict], tape_ids: list, oi_rows: list, wbd_rows: list,
              book: Optional[dict] = None) -> None:
    """THE FACTS PRINTED TWICE (W-1.1 item 1.1), tagged for the consistency gate
    (daily_cascade/consistency.py): each instrument's week and session move in
    the tape (canonical), SPY's week and sessions in the overnight split, SPY's
    and the 10-year's sessions in the week by day, and the 10-year's and
    30-year's week in Plumbing."""
    from . import consistency as cons                           # noqa: PLC0415
    by = {s["id"]: s for s in sections}
    tape = by.get("tape") or {}
    for r, (iid, as_of) in enumerate(tape_ids):
        cons.tag(tape.get("table"), r, 3, cons.fact_key(iid, as_of, "week"), True)
        cons.tag(tape.get("table"), r, 2, cons.fact_key(iid, as_of, "session"), True)
        # THE LEVEL TOO (W-1.1a item 6), for the alias check against the charts'
        # FRED series of the same instrument.
        if as_of:
            cons.tag(tape.get("table"), r, 1, cons.fact_key(iid, as_of, "level"), True)
    ov = next((ss.get("table") for ss in tape.get("subsections") or []
               if str(ss.get("title", "")).startswith("SPY overnight")), None)
    if ov is not None and oi_rows:
        for r, x in enumerate(oi_rows):
            cons.tag(ov, r, 3, cons.fact_key("spy", x["day"], "session"))
        cons.tag(ov, len(oi_rows), 3, cons.fact_key("spy", oi_rows[-1]["day"], "week"))
    read = by.get("read") or {}
    for r, x in enumerate(wbd_rows):
        cons.tag(read.get("table"), r, 1, cons.fact_key("spy", x.get("day"), "session"))
        cons.tag(read.get("table"), r, 2, cons.fact_key("y10", x.get("day"), "session"))
    pl = by.get("plumbing") or {}
    frames = {i["id"]: i.get("frame") or {} for i in (book or {}).get("instruments") or []}
    for r, row in enumerate(((pl.get("table") or {}).get("rows") or [])):
        iid = {"10-year": "y10", "30-year": "y30"}.get(str(row[0]))
        if iid and frames.get(iid, {}).get("wtd_change_bps") is not None:
            cons.tag(pl["table"], r, 2,
                     cons.fact_key(iid, frames[iid].get("as_of"), "week"))


def chart_plan(ed: dict) -> list[str]:
    """W1-W11 within the cap (10, ruled 4 Oct 2026); a fired trigger lifts it by
    one. W6 only with an open contradiction. W11, the standing decomposition
    (Batch 6 item 40, 16 Oct 2026), sits before W10: with W6 open and no
    trigger, W10 is the one set aside."""
    cap = int((ed.get("budget") or {}).get("charts") or 10)
    if any(s.get("depth_reason") for s in ed["sections"]):
        cap += 1
    misfit = next(s for s in ed["sections"] if s["id"] == "misfit")
    want = ["W1", "W2", "W8", "W7", "W3", "W5", "W4", "W9", "W11", "W10"]
    # W12, THE DEALER PANEL (6b part 2; brief v2 section 3: figures 2, 1 and 3),
    # in Mechanics after W7, when the edition reads the computed profiles. At the
    # cap of 10 it sets W10 aside; with W6 open and no trigger, W11 too.
    if ed.get("dealer_computed_dir"):
        want.insert(4, "W12")
    if (misfit.get("data") or {}).get("open_contradictions"):
        want.insert(4, "W6")
    return want[:cap]


# Where each chart prints: a section, or a section's sub-section by index.
PLACE = {"W1": ("tape", None), "W2": ("tape", None), "W8": ("tape", None),
         "W7": ("mechanics", None), "W3": ("plumbing", None),
         "W6": ("misfit", None), "W5": ("positioning", 0),
         "W4": ("positioning", 1), "W9": ("positioning", 3),
         "W10": ("priced", 1), "W11": ("priced", None),
         "W12": ("mechanics", None)}

# W8's six panels: (tape id, panel title).
W8_PANELS = (("btc", "Bitcoin"), ("gold", "Gold (front future)"), ("dxy", "DXY"),
             ("oil", "WTI (front future)"), ("y10", "10-year yield"),
             ("y30", "30-year yield"))
# W9's gauges: (panel title, store key, instrument). A key of None is not fed yet.
# NAAIM was dropped (PB-1, 5 Oct 2026): subscription-only since 1 Aug 2026.
W9_GAUGES = (("SPY put/call, volume (SPY chain, own capture)",
              "chain.spy_put_call_volume", "SPY"),
             ("VIX term structure (VIX3M over VIX)", "calc.vix3m_over_vix", None),
             ("Breadth (RSP over SPY)", "calc.breadth_rsp_over_spy", None),
             ("Retail sentiment, SPY (RTAT10)", "ndl.rtat10_sentiment", "SPY"),
             ("AAII bull-bear spread", "aaii.bull_bear_spread", None),
             ("MOVE (bond volatility)", "yfinance.mkt_move", None),
             ("VVIX (volatility of the VIX)", "yfinance.mkt_vvix", None),
             ("SKEW", "yfinance.mkt_skew", None))


# W3's yields: (store key, label).
W3_YIELDS = (("fred.yield_2y", "2-year"), ("fred.yield_10y", "10-year"),
             ("fred.yield_30y", "30-year"))


def chart_data(st, ed: dict, now: str, ending: str, sessions: list,
               pmb: Optional[dict] = None) -> dict:
    """Everything W3, W4, W7-W10 draw, read from the store at edition time."""
    out: dict[str, Any] = {}
    end = dt.date.fromisoformat(now[:10])
    since = lambda days: (end - dt.timedelta(days=days)).isoformat()  # noqa: E731
    out["yields10"] = {name: series(st, k, now, since=since(3653))
                       for k, name in W3_YIELDS}
    out["hy20"] = series(st, "fred.hy_oas", now, since=since(7305))
    out["cftc"] = {name: series(st, "cftc.noncomm_net", now, inst, since(730))
                   for inst, name in CFTC_CONTRACTS}
    out["gauges"] = {lab: (series(st, k, now, inst, since(730)) if k else [])
                     for lab, k, inst in W9_GAUGES}
    out["w8"] = {}
    for iid, lab in W8_PANELS:
        try:
            rows, _ = levels_mod.daily_bars(levels_mod.tape_spec(iid), ending, now, st)
        except Exception:                                       # noqa: BLE001
            rows = []
        out["w8"][lab] = rows
    lv = {}
    for x in st.as_of("dealer.scorecard_day", now, "SPY"):
        try:
            c = json.loads(x["value_text"])
        except (TypeError, ValueError):
            continue
        lv[str(x["observed_at"])[:10]] = {
            "flip": c.get("flip_morning"),
            "call_wall": c.get("call_wall_morning") or c.get("call_wall"),
            "put_wall": c.get("put_wall_morning") or c.get("put_wall"),
            "max_pain": c.get("max_pain")}
    out["w7_levels"] = lv
    odds: dict[str, list] = {}
    try:
        from altdata.prediction_markets import classify_fomc     # noqa: PLC0415
        cfgw = stack_mod._watch_cfg()
        for wid, rows in ((pmb or {}).get("watch") or {}).items():
            w = cfgw.get(wid) or {}
            if w.get("compare") is False or not rows:
                continue
            if wid == "fomc_decision":
                nxt = sorted({str(r.get("close_at") or "")[:10] for r in rows})[:1]
                picked = {r["venue"]: r for r in rows
                          if str(r.get("close_at") or "")[:10] in nxt
                          and classify_fomc(r.get("question") or "",
                                            r.get("outcome") or "") == "hold"}
                # W8-3: one template, "the 9 December meeting".
                from . import readability                       # noqa: PLC0415
                label = ("hold at the " + readability.meeting_name(
                    nxt[0], dt.date.fromisoformat(now[:10]).year) + " meeting"
                    if nxt else "hold at the next meeting")
            else:
                picked = stack_mod.side_rows(rows, w)
                label = str(w.get("subject") or w.get("label") or wid).replace(
                    "{year}", "").replace("{side}", "").strip()
            for v, r in picked.items():
                pts = series(st, "pm.probability", now, r["instrument"], since(90))
                if pts:
                    odds[f"{stack_mod._venue_name(v)}: {label}"[:60]] = pts
    except Exception:                                           # noqa: BLE001
        log.warning("W10 odds unavailable", exc_info=True)
    out["odds"] = odds
    try:
        from altdata import st_r5_index                          # noqa: PLC0415
        out["carry"] = st_r5_index.chart_series(st, now, "twelve_months")
    except Exception:                                           # noqa: BLE001
        log.warning("W11 series unavailable", exc_info=True)
        out["carry"] = {"absent": True, "reason": "the decomposition faulted"}
    try:
        from altdata import fed_funds                           # noqa: PLC0415
        out["paths"] = [fed_funds.path_as_of(t, st) for t in
                        (now, week_ago(now),
                         (dt.datetime.fromisoformat(now.replace("Z", "+00:00"))
                          - dt.timedelta(days=30)).isoformat())]
    except Exception:                                           # noqa: BLE001
        out["paths"] = [None, None, None]
    return out


@model_meter.metered("weekly")
def produce(p: dict, *, archive_dir: Optional[str], dry_run: bool = False,
             client=None, model: Optional[str] = None, narrative: bool = True,
             db_path: Optional[str] = None, log_path: Optional[Path] = None,
             prior_dir: Optional[str] = None) -> dict:
    ending = p["week_ending"]
    with bars_mod.BarStore(db_path) as bst:
        try:
            from daily_cascade import payload as close_payload  # noqa: PLC0415
            exposure = close_payload.exposure_rows(ending)[0]
        except Exception:                                       # noqa: BLE001
            exposure = []
        book = levels_mod.compute(ending, exposure, store=bst)
        with observations.ObservationStore(db_path) as _db:
            daily, _ = levels_mod.daily_bars(levels_mod.tape_spec("spy"), ending,
                                             None, _db)
    prior = load_prior(p.get("previous_week_ending") or "", prior_dir or archive_dir)
    ed, extras = build(p, book, prior, db_path, log_path, dry_run=dry_run)
    # THE CONSISTENCY GATE (W-1.1 item 1.1, ruling 1): within rounding, every
    # place prints the canonical figure and the difference is logged; beyond it,
    # EditionInconsistent fails the run. Before the prose, so every frame copies
    # the canonical figure.
    from . import consistency                                   # noqa: PLC0415
    consistency.reconcile(ed)
    if narrative:
        stack_prose.write(ed, client=client, model=model, outlooks=[],
                          cadence="weekly")
        storyline_pass(ed, prior, ending, client=client, model=model,
                       db_path=db_path, dry_run=dry_run)
        playbook_pass(ed, client=client, model=model)
    else:
        ed["precis"] = {"state": "skipped", "published": False}
    book_terms(ed, ending)
    from . import storyline                                     # noqa: PLC0415
    storyline.layout(ed, stack_mod.config())
    # W-1.3a item 3.7: the technical appendix closes the reference tier, and the
    # glossary carries the config's version.
    ta = wsec.technical_appendix(stack_mod.config())
    if ta:
        ed.setdefault("detail", []).append(ta)
    ed["definitions_version"] = wsec.definitions_version()
    # W12 (6b part 2) joins the plan only when the week's last settled dealer
    # profile exists under the payload's computed_dir.
    from . import dealer_block as _db                           # noqa: PLC0415
    ed["dealer_computed_dir"] = _db.chart_dir(p.get("computed_dir"), ending)
    plan = chart_plan(ed)
    base = f"weekly_tactical_{ending}"
    out_dir = archive_dir
    charts: dict[str, dict] = {}
    now = ed["as_of"]
    with observations.ObservationStore(db_path) as st:
        pmb, _, _ = stack_mod.venues_and_path(ending, now, st)
        cd = chart_data(st, ed, now, ending, p.get("sessions_in_week") or [], pmb)
    with bars_mod.BarStore(db_path) as bst:
        first = (dt.date.fromisoformat(ending) - dt.timedelta(days=21)).isoformat()
        spy5 = bst.read("spy", "5m", first, ending + "T23:59:59+00:00", now)
        es5 = bst.read("es", "5m", first, ending + "T23:59:59+00:00", now)
    then = week_ago(now)
    if "W1" in plan:
        charts["W1"] = charts_mod.w1(book, daily, f"{base}_w1", out_dir)
    if "W2" in plan:
        charts["W2"] = charts_mod.w2(book, daily, f"{base}_w2", out_dir)
    if "W8" in plan:
        charts["W8"] = charts_mod.w8(cd["w8"], f"{base}_w8", out_dir)
    if "W7" in plan:
        charts["W7"] = charts_mod.w7(spy5, cd["w7_levels"], f"{base}_w7", out_dir,
                                     es5=es5)
    if "W3" in plan:
        charts["W3"] = charts_mod.w3_panel(cd["yields10"], cd["hy20"], f"{base}_w3",
                                           out_dir, now)
        # W3's last points as levels, for the alias check (W-1.1a item 6).
        if not charts["W3"].get("unavailable"):
            charts["W3"]["levels"] = [
                {"series": key, "as_of": pts[-1][0], "value": round(pts[-1][1], 2),
                 "printed": f"{pts[-1][1]:.2f}%", "source": "FRED"}
                for key, pts in ((k, cd["yields10"].get(n) or []) for k, n in W3_YIELDS)
                if pts]
    if "W4" in plan:
        c4 = [v for v in cd["cftc"].values() if v]
        d0 = min((v[0][0] for v in c4), default=now[:10])
        charts["W4"] = charts_mod.z_panel(
            "W4", cd["cftc"], "Speculative positioning (CFTC), z-scores",
            f"{base}_w4", out_dir, min_points=20,
            subtitle=charts_mod.span_title(
                "net contracts", max((len(v) for v in c4), default=0),
                "weekly reports", d0, now, "two years"))
    if "W5" in plan:
        charts["W5"] = charts_mod.bars_chart(
            "W5", extras["leadership"], f"Leadership: the week's sector and "
            f"style-pair returns (%), {then[:10]} to {ending}", f"{base}_w5", out_dir)
    if "W9" in plan:
        g = [v for v in cd["gauges"].values() if v]
        d0 = min((v[0][0] for v in g), default=now[:10])
        charts["W9"] = charts_mod.z_panel(
            "W9", cd["gauges"], "Positioning and sentiment gauges, z-scores",
            f"{base}_w9", out_dir, ncols=3, min_points=20,
            subtitle=charts_mod.span_title(
                "each gauge", max((len(v) for v in g), default=0), "observations",
                d0, now, "two years"))
    if "W10" in plan:
        charts["W10"] = charts_mod.w10(cd["odds"], *cd["paths"], f"{base}_w10",
                                       out_dir)
    if "W11" in plan:
        charts["W11"] = charts_mod.index_carry("W11", cd.get("carry"), "twelve months",
                                               f"{base}_w11", out_dir)
    if "W12" in plan:
        from . import dealer_block                              # noqa: PLC0415
        mech = next((s for s in ed["sections"] if s["id"] == "mechanics"), {})
        charts["W12"] = charts_mod.dealer_chart(
            "W12", dealer_block.newest_settled(ending, "SPY", ed["dealer_computed_dir"]),
            f"{base}_w12", out_dir,
            rates=(mech.get("data") or {}).get("_dealer_rates"))
    if "W6" in plan:
        c6 = [v for v in extras["contradictions"].values() if v]
        n6 = max((len(v) for v in c6), default=0)
        d0 = min((v[0][0] for v in c6), default=now[:10])
        charts["W6"] = charts_mod.lines_chart(
            "W6", extras["contradictions"], charts_mod.span_title(
                "Open contradictions: gap z-score", n6, "sessions", d0, now,
                "since each opened"), f"{base}_w6", out_dir, min_points=5)
    # ONE INSTRUMENT, SEVERAL SERIES (W-1.1a item 6): the tape's levels against
    # the charts' FRED levels of the same instrument, before anything prints.
    from . import consistency as cons_mod                       # noqa: PLC0415
    cons_mod.reconcile_aliases(ed, charts)
    for cid, c in charts.items():
        sid, sub = PLACE[cid]
        s = next(x for x in ed["sections"] if x["id"] == sid)
        subs = s.get("subsections") or []
        if sub is not None and sub < len(subs):
            subs[sub].setdefault("charts_rendered", []).append(cid)
        else:
            s.setdefault("charts_rendered", []).append(cid)
    ed["charts"] = {k: {kk: v for kk, v in c.items() if kk != "png"}
                    for k, c in charts.items()}
    ed["levels"] = book
    ed["chart_count"] = sum(1 for c in charts.values() if not c.get("unavailable"))
    # THE FORMATTING PASS (T2.5 item 6), over every string the edition prints.
    from . import readability                                   # noqa: PLC0415
    readability.polish_edition(ed, charts)
    # THE GUARD LAST (A-4): finalize pops each sub-section's paragraph, and the
    # formatting pass, run after it, wrote the key back -- so nothing after
    # the budget may rewrite the edition's prose.
    stack_mod.enforce_budget(ed, "weekly")
    ed["run_id"] = p.get("run_id")
    from alpha.lab_line import weekly_line                      # noqa: PLC0415
    # X-1.11: the lab's one line -- alpha.db, beside the store, read-only.
    ed["alpha_lab"] = weekly_line(now, db_path and Path(db_path).with_name("alpha.db"))
    ed["archive_path"] = (str(Path(archive_dir) / f"{base}.html")
                          if archive_dir else None)
    html_email = render(p, ed, charts, mode="email")
    html_archive = render(p, ed, charts, mode="archive")
    images = [(stack_render.cid(k), c["png"]) for k, c in charts.items() if c.get("png")]
    # THE PDF (T2.5 item 11): the emailed HTML with print CSS, its charts the
    # same PNGs; archived beside the HTML and attached beside the body.
    pdf, pdf_detail = readability.pdf_bytes(html_email, images)
    return {"edition": ed, "charts": charts, "html_email": html_email,
            "html_archive": html_archive, "inline_images": images,
            "pdf": pdf, "pdf_detail": pdf_detail}


def storyline_pass(ed: dict, prior: Optional[dict], ending: str, *, client=None,
                   model: Optional[str] = None, db_path: Optional[str] = None,
                   dry_run: bool = False) -> None:
    """W-1.2 items 2.1-2.3: grade last week's stance, write the précis over the
    ten finished commentaries, and record this week's stance at publication --
    a dry run under its own namespace in the ledger, never the live source."""
    from . import precis                                        # noqa: PLC0415
    base_close = None
    try:
        with observations.ObservationStore(db_path) as st:
            ed["stances_graded"] = precis.grade_stances(db_path, ending, st, dry_run)
            base_close = precis.spy_close(st, ending, ed.get("as_of"))
    except Exception:                                           # noqa: BLE001
        log.warning("stance grading unavailable", exc_info=True)
    n = precis.graded_n(db_path, dry_run)
    res = precis.write(ed, prior, client=client, model=model, stance_n=n)
    precis.apply(ed, res, n)
    try:
        ed["precis"]["stance_id"] = precis.record_stance(
            res, ending, ed.get("as_of"), db_path, dry_run, base_close)
        ed["precis"]["stance_source"] = precis.source_name(dry_run)
    except Exception as exc:                                    # noqa: BLE001
        ed["precis"]["stance_error"] = f"{type(exc).__name__}: {exc}"


def book_terms(ed: dict, ending: str) -> None:
    """W-1.2 item 2.5: section 10 ends with the book's terms."""
    from . import precis                                        # noqa: PLC0415
    book = next((s for s in ed["sections"] if s["id"] == "book"), None)
    if book is None or book.get("empty"):
        return
    try:
        from daily_cascade import payload as close_payload      # noqa: PLC0415
        enf = close_payload.enforcement_block(ending, ed.get("as_of"))
    except Exception:                                           # noqa: BLE001
        enf = None
    line = precis.terms_line(ed, enf)
    if line:
        book["closing_lines"] = [line]


def render(p: dict, ed: dict, charts: dict, mode: str = "email") -> str:
    """The Weekly (T2.5 item 7): the title and week, the as-of in ET, the
    reading time and what changed since the last Weekly in the header; the ten
    sections; the glossary; the run's metadata in a small footer."""
    from . import readability as rd                             # noqa: PLC0415
    secs = "".join(stack_render.section_html(s, n, charts, mode, "weekly")
                   for n, s in enumerate(ed["sections"], start=1))
    try:
        week = rd.prose_date(ed.get("week_ending"))
    except ValueError:
        week = str(ed.get("week_ending"))
    head = stack_render.page_header(
        f"Weekly — week ending {week}", rd.stamp_et(ed.get("as_of")),
        rd.reading_minutes(ed, int(ed.get("chart_count") or 0)),
        ed.get("changed_since") or [], "Changed since last Weekly",
        extra_html=f' &middot; {stack_render.esc(ed["alpha_lab"])}' if ed.get("alpha_lab") else "")
    # THE ADDENDUM'S ONE LINE (Batch 8 item 51): where the Digital Assets page is;
    # nothing when the run carries no addendum.
    from . import digital_addendum                              # noqa: PLC0415
    link = digital_addendum.link_line(p.get("addendum"), mode)
    if link:
        head += f'<p style="{stack_render.SUB}">{stack_render.esc(link)}</p>'
    # W-1.2: the précis opens the edition (page 1), the terms box is page 2,
    # then the ten sections; the reference tables after the last section.
    from . import precis                                        # noqa: PLC0415
    return (f'<div style="{stack_render.WRAP}">{head}{precis.precis_html(ed)}'
            f'{precis.terms_box_html()}{secs}'
            f'{stack_render.details_html(ed.get("detail"), "weekly")}'
            f'{stack_render.glossary_html(_glossary() + list(ed.get("glossary_extra") or []), ed, stamp=ed.get("definitions_version"))}'
            + stack_render.page_footer(ed, ed.get("run_id") or p.get("run_id"),
                                       ed.get("archive_path"),
                                       stack_render._marks(ed, "Weekly"))
            + "</div>")


def changed_html(ed: dict) -> str:
    """'Changed since last Weekly' (T2.3 item 7) -- a table, never a list."""
    return stack_render.lines_table(ed.get("changed_since") or [],
                                    "Changed since last Weekly")


def _glossary() -> list[dict]:
    from altdata import labels                                  # noqa: PLC0415
    return labels.glossary()


def save_edition(ed: dict, ending: str, archive_dir: Optional[str]) -> Optional[str]:
    from altdata import withheld_log                            # noqa: PLC0415
    from . import deliver                                       # noqa: PLC0415
    withheld_log.record_edition("weekly_tactical", edition_name(ending), ed, archive_dir)
    return deliver.archive(json.dumps(ed, indent=2, default=str, sort_keys=True),
                           edition_name(ending), archive_dir)
