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

from . import charts as charts_mod
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


def change_over(st, key: str, now_cut: str, then_cut: str,
                instrument: Optional[str] = None) -> Optional[dict]:
    """{level, prior, change, unit, observed_at} between two cutoffs."""
    a = st.latest_as_of(key, now_cut, instrument)
    b = st.latest_as_of(key, then_cut, instrument)
    if not a or a.get("value_num") is None:
        return None
    lv = a["value_num"]
    pv = b.get("value_num") if b else None
    units = str(derived.registry_entry(key).get("units") or "")
    du = derived.delta_unit_for(key)[0]
    if pv is None or str(b.get("observed_at")) == str(a.get("observed_at")):
        ch = None
    elif du == "bps":
        ch = round((lv - pv) * (1.0 if units in ("bps", "bp") else 100.0), 1)
    elif du == "percent" and pv:
        ch = round(100.0 * (lv / pv - 1.0), 2)
    else:
        ch = round(lv - pv, 4)
    return {"key": key, "level": lv, "prior": pv, "change": ch,
            "unit": "bp" if du == "bps" else ("%" if du == "percent" else ""),
            "level_units": units, "observed_at": str(a["observed_at"])[:10],
            "prior_observed_at": str(b["observed_at"])[:10] if b else None}


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
                   cfg: Optional[dict] = None) -> dict:
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
        items.append(item(f"mech:dial:{ch.get('dial')}",
                          f"{name.get(ch.get('dial'), str(ch.get('dial')))} moved "
                          f"from {ch.get('from') or 'absent'} to {ch.get('to')}.", 1,
                          (ch.get("from"), ch.get("to"))))
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
    vol = wsec.volatility(st, cutoff, wis)
    subs.append({**vol, "paragraph_wanted": True})
    return {"items": items, "not_tracked": nt,
            "subsections": subs, "lead_paragraphs": "1",
            "table": dw["table"],
            "table_note": dw["table_note"] if dw["table"]["rows"] else None,
            "data": {"dealer_week": dw["data"]["sessions"], "dials_now": dials,
                     "volatility": vol.get("data"),
                     "dial_changes": wis.get("dial_changes") or []}}


def misfit_week(wis: dict, pmb: Optional[dict],
                history: Optional[dict] = None) -> dict:
    base = stack_mod.misfit_section({"market_state": {}}, pmb)
    items = [i for i in base["items"] if i["key"] != "misfit:none"]
    from altdata import labels                                   # noqa: PLC0415
    opened = [c for c in wis.get("contradictions") or []
              if c.get("open_state") == "open"]
    for c in opened:
        items.append(item(f"misfit:{c['id']}", stack_mod.contradiction_line(c), 1,
                          (c.get("persistence_days"), c.get("magnitude"))))
    for e in wis.get("exceptions_opened") or []:
        items.append(item(f"misfit:exc:{e}", f"Opened this week: "
                          f"{labels.exception(e)}.", 2, e))
    for e in wis.get("exceptions_intraweek_only") or []:
        items.append(item(f"misfit:intra:{e}", f"Opened and closed inside the "
                          f"week: {labels.exception(e)}.", 3, e))
    if not items:
        items.append(item("misfit:none", "No contradiction open, no exception "
                          "opened this week.", 1, "none"))
    data = dict(base["data"])
    now_open = wis.get("exceptions_open_now") or []
    data.update({"open_contradictions": [stack_mod.contradiction_data(c)
                                         for c in opened],
                 "exceptions_opened": [labels.exception(e) for e in
                                       wis.get("exceptions_opened") or []],
                 "exceptions_open_now": [labels.exception(e) for e in now_open]})
    # THE GAP TABLE (T2.2 item 5): each open gap with what each side is saying,
    # its z, direction and count, under a two-line note on how to read it. The
    # contradiction lines move into the table; the items keep the prediction-
    # market disagreements and the week's openings.
    gaps = wsec.gap_table(opened, history or {})
    data["gaps"] = gaps["data"]
    items = [i for i in items if not any(i["key"] == f"misfit:{c['id']}"
                                         for c in opened)]
    if not items:
        items.append(item("misfit:none", "No prediction-market disagreement and "
                          "no exception opened this week.", 1, "none"))
    exc_table = {"columns": ["Open at the week's end", "What it is", "Opened this week"],
                 "rows": [[labels.exception(e),
                           labels.exception_kind(e.split(":", 1)[0]),
                           "yes" if e in (wis.get("exceptions_opened") or []) else ""]
                          for e in now_open]}
    return {"items": items, "not_tracked": base.get("not_tracked") or [],
            "data": data, "table": gaps["table"] if opened else None,
            "table_note": gaps["table_note"] if opened else None,
            "subsections": ([{"title": "Exceptions open at the week's end",
                              "table": exc_table}] if now_open else [])}


PLUMB = (("fred.yield_2y", "2-year"), ("fred.yield_10y", "10-year"),
         ("fred.yield_30y", "30-year"), ("calc.yield_curve_2s10s", "2s10s"),
         ("fred.hy_oas", "High-yield OAS"),
         ("acm.term_premium_10y", "10-year term premium (ACM)"))


# THE BARS' YIELD FOR THE WEEK'S MOVE (T2 ruling 3, 3 Oct 2026): one 10-year
# change per edition, the tape's -- Friday close to Friday close from the 5-minute
# feed's daily bars. FRED stays the level, the percentile and the history, and
# says its own as-of when it lags the bars.
BAR_YIELDS = {"fred.yield_10y": "y10", "fred.yield_30y": "y30"}


def plumbing_week(st, now: str, then: str, book: Optional[dict] = None) -> dict:
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
                              f"{_signed(fr['wtd_change_bps'], 'bp')} on the week "
                              f"(Friday to Friday, as of {fr.get('as_of')}{fred_lvl}).",
                              1 if k == "fred.yield_10y" else 2,
                              (fr["last"], fr["wtd_change_bps"])))
            rows.append([name, f"{fr['last']:.3f}%",
                         _signed(fr["wtd_change_bps"], "bp"), fr.get("as_of")])
            continue
        if not x:
            continue
        data[name] = x
        items.append(item(f"plumb:{k}", f"{name} {_lvl(x)}, {_change(x)} on the week "
                          f"({window(x)}).",
                          1 if k in ("fred.yield_10y", "fred.hy_oas") else 2,
                          (x["level"], x["change"])))
        rows.append([name, _lvl(x), _change(x), x["observed_at"]])
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
    pr = wsec.plumbing_rows(st, now, then)
    rows += pr["rows"]
    fx = wsec.global_fx(st, now, then)
    # NO BULLETS (T2.2 item 6): the table carries every figure and the prose
    # reads from it; the items stay as the section's data and its change marks.
    return {"items": items, "print_items": False,
            "data": {"series": data, "tier1_releases": rel, "plumbing": pr["data"]},
            "table": {"columns": ["Series", "Level or actual", "Week or prior",
                                  "As of"], "rows": rows},
            "subsections": [{**fx, "paragraph_wanted": False}],
            "not_tracked": pr["not_tracked"]}


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
        return f"{v:+,.0f}"
    if form in ("mom",):
        return f"{v:+.1f}%"
    if form in ("yoy", "annualised"):
        return f"{v:.1f}%"
    units = str(derived.registry_entry(key).get("units") or "")
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


def positioning_week(st, now: str, then: str) -> dict:
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
        data[f"cftc:{inst}"] = {**x, "z_2y": None if z is None else round(z, 1),
                                "percentile_2y": pct}
        items.append(item(f"pos:cftc:{inst}", f"Speculators' net {name}: "
                          f"{x['level']:,.0f} contracts ({_change(x)} since the prior "
                          f"report, as of {x['observed_at']})"
                          + (f", z {z:+.1f} over two years" if z is not None else "")
                          + ".", 2, (x["level"], x["observed_at"])))
        rows.append(["CFTC " + name, f"{x['level']:,.0f}", _change(x), x["observed_at"]])
    if missing:
        nt.append("CFTC net speculative positioning in " + ", ".join(missing)
                  + " (not yet stored)")
    for sym in ("SPY", "QQQ", "IWM"):
        x = change_over(st, "finra.short_interest_days_to_cover", now, then, sym)
        if x:
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
                              + (f" against {pm:+.2f} the week before" if pm is not None
                                 else "") + ".", 3, round(m, 2)))
    for sym in ("SPY", "QQQ", "NVDA", "TSLA"):
        x = change_over(st, "apewisdom.mentions", now, then, f"{sym}@wallstreetbets")
        if x:
            data[f"ape:{sym}"] = x
            items.append(item(f"pos:ape:{sym}", f"{sym} mentions on WallStreetBets: "
                              f"{x['level']:,.0f} ({_change(x)} on the week).", 4,
                              (x["level"], x["observed_at"])))
    for k, name in (("tic.flow_net_foreign", "Net foreign purchases of US long-term "
                     "securities"), ("tic.flow_total", "Total net TIC flows")):
        x = change_over(st, k, now, then)
        if x:
            from altdata.numeral_audit import scaled_display    # noqa: PLC0415
            disp = scaled_display(x["level"], x.get("level_units") or "usd") \
                or f"{x['level']:,.0f}"
            data[k] = {**x, "level_display": disp}
            items.append(item(f"pos:{k}", f"{name}: {disp} for "
                              f"{x['observed_at'][:7]} (TIC, monthly).", 4,
                              (x["level"], x["observed_at"])))
    lead = leadership(st, now, then)
    if lead:
        srt = sorted([r for r in lead if len(r[0]) <= 4], key=lambda r: -r[1])
        if len(srt) >= 4:
            items.insert(0, item("pos:leadership", "Leadership on the week: "
                                 + ", ".join(f"{n} {_signed(v, '%')}" for n, v in srt[:3])
                                 + "; lagging " + ", ".join(f"{n} {_signed(v, '%')}"
                                                           for n, v in srt[-3:]) + ".",
                                 1, srt))
        for lab, v in lead:
            if len(lab) > 4:
                items.append(item(f"pos:style:{lab}", f"{lab}: {_signed(v, '%')} "
                                  f"on the week.", 2, v))
        data["leadership"] = [{"name": n, "week_return_pct": v} for n, v in lead]
    else:
        nt.append("the week's sector and style-pair returns (no closes stored)")
    subs = positioning_subsections(st, now, then, data, lead, rows)
    return {"items": items, "not_tracked": nt, "data": data, "print_items": False,
            "subsections": subs, "_cftc_series": cftc, "_leadership": lead}


def positioning_subsections(st, now: str, then: str, data: dict, lead: list,
                            rows: list) -> list[dict]:
    """T2.2 item 7: five sub-sections, each with its table and one paragraph."""
    from altdata import labels                                   # noqa: PLC0415
    out = []
    # THE WEEK, ONE MONTH AND THREE MONTHS, and the 50/200-day count (T2.3
    # item 6), sector names from the display labels.
    sec = wsec.sector_table(st, now, then, lead)
    data["sectors_above_50d"] = sec["above_50d"]
    data["sectors_above_200d"] = sec["above_200d"]
    out.append({"title": "Sector rotation and leadership", "table": sec["table"],
                "lines": [sec["line"]] if sec["line"] else [],
                "not_tracked": [] if sec["table"]["rows"] else
                ["the week's sector returns"]})
    cf = []
    for inst, name in CFTC_CONTRACTS:
        x = data.get(f"cftc:{inst}")
        if x:
            cf.append([name[0].upper() + name[1:], f"{x['level']:,.0f}", _change(x),
                       "—" if x.get("z_2y") is None else f"{x['z_2y']:+.1f}",
                       x["observed_at"]])
    out.append({"title": "Speculative positioning (CFTC)",
                "table": {"columns": ["Contract", "Net speculative contracts",
                                      "Change", "z, two years", "As of"], "rows": cf},
                "not_tracked": [n for i, n in CFTC_CONTRACTS
                                if f"cftc:{i}" not in data]})
    si = [[f"{sym} days to cover", f"{data[f'finra:{sym}']['level']:,.2f}",
           _change(data[f"finra:{sym}"]), data[f"finra:{sym}"]["observed_at"]]
          for sym in ("SPY", "QQQ", "IWM") if data.get(f"finra:{sym}")]
    out.append({"title": "Short interest",
                "table": {"columns": ["Series", "Level", "Change", "Settlement"],
                          "rows": si}})
    rs = []
    for sym in ("SPY", "QQQ", "IWM", "NVDA", "TSLA"):
        r = data.get(f"rtat:{sym}")
        if r:
            rs.append([f"{sym} retail sentiment (RTAT10, week mean)",
                       f"{r['week_mean']:+.2f}",
                       "—" if r.get("prior_week_mean") is None
                       else f"{r['prior_week_mean']:+.2f}", f"n={r['n']}"])
    for sym in ("SPY", "QQQ", "NVDA", "TSLA"):
        x = data.get(f"ape:{sym}")
        if x:
            rs.append([f"{sym} WallStreetBets mentions", f"{x['level']:,.0f}",
                       _change(x), x["observed_at"]])
    aaii = change_over(st, "aaii.bull_bear_spread", now, then)
    if aaii:
        data["aaii"] = aaii
        # SOURCE AND AS-OF ON THE ROW (rulings of 5 Oct, item 4).
        rs.append(["AAII bull-bear spread, points (source: AAII Sentiment Survey, "
                   f"weekly; as of {aaii['observed_at']})", f"{aaii['level']:+.1f}",
                   "—" if aaii.get("prior") is None
                   else f"{aaii['level'] - aaii['prior']:+.1f}", aaii["observed_at"]])
    out.append({"title": "Retail sentiment",
                "table": {"columns": ["Series", "This week", "Prior or change",
                                      "As of"], "rows": rs},
                "not_tracked": [] if aaii else ["the AAII bull-bear spread"]})
    tic = [[("Net foreign purchases of US long-term securities"
             if k == "tic.flow_net_foreign" else "Total net TIC flows"),
            data[k]["level_display"], data[k]["observed_at"][:7]]
           for k in ("tic.flow_net_foreign", "tic.flow_total") if data.get(k)]
    out.append({"title": "Foreign flows (TIC)",
                "table": {"columns": ["Series", "Level", "Month"], "rows": tic}})
    return out


def window(x: dict) -> str:
    """The real window of a weekly change: the two observation dates it spans
    (T2.1 item 14) -- a FRED series lags, so 'on the week' alone would hide
    which week."""
    a, b = x.get("prior_observed_at"), x.get("observed_at")
    return f"{a} to {b}" if a and a != b else f"as of {b}"


WEEK_PRICED = (("fred.breakeven_5y", "5-year breakeven"),
               ("fred.breakeven_10y", "10-year breakeven"),
               ("fred.breakeven_5y5y", "5-year, 5-year-forward breakeven"),
               ("umich.expect_5_10y", "Michigan 5-10 year expectations"),
               ("nyfed.sce_3y", "NY Fed 3-year expectations"))


def priced_week(st, now: str, then: str, cfg: dict, pmb, fed, fed_then) -> dict:
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
        b["items"].append(item(f"priced:{k}", f"{name} {_lvl(x)}, {_change(x)} on "
                               f"the week ({window(x)}).", 2,
                               (x["level"], x["change"])))
    b["data"]["series"] = series
    trig = (cfg.get("triggers") or {}).get("priced") or {}
    reason = None
    for k, th in (trig.get("moves_bp") or {}).items():
        x = change_over(st, k, now, then)
        if x and x.get("change") is not None and abs(x["change"]) >= th:
            reason = f"{k.split('.')[-1]} moved {_change(x)} on the week " \
                     f"(threshold {th} bp)"
            break
    rate_th = float(trig.get("fomc_implied_rate_next_four_meetings_bp") or 12.5)
    if not reason and fed and fed_then and fed.get("tracked"):
        was = {m["meeting"]: m["post_pct"] for m in fed_then.get("meetings") or []}
        for m in (fed.get("meetings") or [])[:4]:
            ch = derived.rate_bp_change(m["post_pct"], was.get(m["meeting"]))
            if ch is not None and abs(ch) >= rate_th:
                reason = (f"the implied rate after the {m['meeting']} meeting moved "
                          f"{_signed(ch, 'bp')} on the week (threshold {rate_th:g} bp)")
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
        earn = wsec.earnings_block(st, now[:10], now, then)
    except Exception:                                           # noqa: BLE001
        earn = None
    b["subsections"] = priced_subsections(b, series, fed, earn)
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
    pm_lines = [i["text"] for i in b["items"]
                if i["key"].startswith("priced:fomc") or i["key"].startswith("priced:pm")
                or i["key"].startswith("priced:outage")]
    surveys = []
    for name in ("Michigan 5-10 year expectations", "NY Fed 3-year expectations"):
        x = series.get(name)
        if x:
            surveys.append([name, _lvl(x), _change(x), window(x)])
    return [{"title": "Rates priced: the fed-funds path and breakevens",
             "table": {"columns": ["Measure", "Level", "Priced or change", "As of"],
                       "rows": rows}, "not_tracked": nt_rates},
            {"title": "Prediction markets", "lines": pm_lines,
             "not_tracked": [] if pm_lines else ["no prediction market stored"]},
            {"title": "Surveyed expectations and consensus",
             "table": {"columns": ["Survey", "Level", "Change", "Window"],
                       "rows": surveys},
             "not_tracked": ["the S&P 500 consensus EPS revision (the Weekly's 1% "
                             "trigger)", "one-year inflation expectations"]}] + (
        # IN SEASON ONLY (T2.3 item 9): nothing at all outside it.
        [{**earnings, "paragraph_wanted": False}] if earnings else [])


def narratives_week_section(nb: dict, wd: Optional[dict] = None,
                            voices: Optional[dict] = None) -> dict:
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
    out = {"items": items,
           "legend": wsec.states_legend([str(s.get("state")) for s in stories]),
           "data": {"stories": [{"title": labels.story(s.get("id")).get("title")
                                 or s.get("name"),
                                 "statement": labels.story(s.get("id")).get("statement"),
                                 "state": s.get("state"),
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
    by: dict[str, list] = {}
    for r in done:
        by.setdefault(r["source"], []).append(r["brier"])
    table = []
    for src, bs in sorted(by.items()):
        m = sum(bs) / len(bs)
        table.append({"source": src, "n": len(bs), "mean_brier": round(m, 4),
                      "vs_coin": round(m - pl.COIN_BRIER, 4),
                      "base_rate": src == "daily_close_outlook"})
    open_n = sum(1 for r in rows if r.get("outcome") is None)
    return {"since": since[:10], "rows": table, "resolved": len(done),
            "unresolved": open_n, "coin_brier": pl.COIN_BRIER}


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
               watch: Optional[list] = None) -> dict:
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
    calls_table = {"columns": ["Source", "Resolved (4 wk)", "Mean Brier",
                               "Against a coin"],
                   "rows": [[source_label(r["source"]),
                             r["n"], f"{r['mean_brier']:.3f}",
                             f"{r['vs_coin']:+.3f}"] for r in rows]}
    # THE DAY-BY-DAY CALENDAR (T2.2 item 10) is the section's table; what the
    # system is watching and the graded calls follow as sub-sections.
    subs = [{"title": "What the system is watching",
             "lines": watch or ["No contradiction is open and no count is running."]},
            {"title": "Graded calls, last four weeks", "table": calls_table,
             "lines": [i["text"] for i in items if i["key"] in ("ahead:calls",
                                                                "ahead:base_rates")]}]
    nt = ["scenario weights with odds and signposts (scenario set #1, Audit #4 "
          "agenda item 2)"]
    if cal and cal.get("routine_not_listed"):
        nt.append(f"{cal['routine_not_listed']} routine data releases and bill "
                  f"auctions not listed")
    return {"items": items, "print_items": False,
            "table": (cal or {}).get("table") or {"columns": [], "rows": []},
            "subsections": subs,
            "data": {"graded_calls": calls,
                     "calendar": [{k: r[k] for k in ("date", "time", "event", "tier",
                                                     "consensus")}
                                  for r in (cal or {}).get("rows") or []],
                     "watching": watch or []},
            "not_tracked": nt}


def book_week(p: dict, attn: dict, trig: dict, bz: Optional[str]) -> dict:
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
    items.append(item("book:attention",
                      f"Attention: {attn['packets_approved']} of "
                      f"{attn['packets_budget']} packets approved"
                      + (f", {attn['packets_deferred_attention_budget']} deferred by "
                         f"the budget" if attn['packets_deferred_attention_budget']
                         else "")
                      + f"; {attn['sitting_hours']:g} of "
                        f"{attn['sitting_hours_budget']} sitting hours"
                      + f"; {attn['rulings']} ruling(s) taken in chat.", 1,
                      (attn["packets_approved"], attn["sitting_hours"], attn["rulings"])))
    items.append(item("book:triggers",
                      f"Triggers fired: Plumbing deep on {len(trig['plumbing'])} and "
                      f"What's priced deep on {len(trig['priced'])} of "
                      f"{trig['sessions']} session(s).", 2,
                      (len(trig["plumbing"]), len(trig["priced"]))))
    return {"items": items, "data": {"attention": attn, "triggers": trig,
                                     "book_z": bz},
            "table": {"columns": ["Count", "This week", "Budget"],
                      "rows": [["Packets approved", attn["packets_approved"],
                                attn["packets_budget"]],
                               ["Sitting hours", attn["sitting_hours"],
                                attn["sitting_hours_budget"]],
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
        items.append(item(f"read:pm5:{r['instrument']}",
                          stack_mod.shock_sentence(r, "over five sessions", c), 1,
                          (r["probability"], c)))
    # THE WEEK BY DAY (T2.2 item 3): the table the opening paragraph reads, and
    # the press's own attributions, each with its URL -- never our cause.
    wbd = wbd or {}
    for n, line in enumerate(wbd.get("attributions") or []):
        items.append(item(f"read:attr:{n}", line, 2, line))
    return {"items": items[:4] + [i for i in items if i["key"].startswith("read:attr")],
            "table": wbd.get("table"),
            "data": {"five_session_moves": [i["text"] for i in items
                                            if i["key"].startswith("read:pm5")],
                     "week_by_day": wbd.get("data") or []}}


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def build(p: dict, book: dict, prior: Optional[dict] = None,
          db_path: Optional[str] = None, log_path: Optional[Path] = None) -> tuple:
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
        except Exception:                                       # noqa: BLE001
            bz = None
        from .stack_close import _contradiction_history          # noqa: PLC0415
        opened = [c for c in wis.get("contradictions") or []
                  if c.get("open_state") == "open"]
        hist = {c["id"]: _contradiction_history(st, c["id"], now) for c in opened}
        rel = tier1_releases(st, now, then)
        wbd = wsec.week_by_day(st, sessions, ending, now, then, rel, str(st.path))
        tape = stack_mod.tape_section(book)
        tt = wsec.tape_table(book)
        oi = wsec.overnight_intraday(st, sessions, ending, now)
        tape.update({"table": tt["table"], "print_items": False,
                     "prose_paragraphs": "exactly four",
                     "subsections": [
                         {"title": "Levels", "table": tt["levels_table"],
                          "paragraph_wanted": False},
                         # OVERNIGHT AGAINST THE CASH SESSION (T2.3 item 1)
                         {"title": "SPY overnight against the cash session",
                          "table": oi["table"], "paragraph_wanted": False}]})
        tape["data"] = {**(tape.get("data") or {}),
                        "overnight_intraday": {"sessions": oi["rows"],
                                               "week": oi["totals"]}}
        try:
            cal = wsec.calendar_week(st, ending, now, pmb)
        except Exception:                                       # noqa: BLE001
            log.warning("calendar unavailable", exc_info=True)
            cal = None
        watch = wsec.watching(st, now, opened, pmb, fed)
        built = {
            "read": read_week(pmb, wbd),
            "tape": tape,
            "mechanics": mechanics_week(st, sessions, now, wis, cfg),
            "misfit": misfit_week(wis, pmb, hist),
            "plumbing": plumbing_week(st, now, then, book),
            "positioning": pos,
            "priced": priced_week(st, now, then, cfg, pmb, fed, fed_then),
            "narratives": narratives_week_section(p.get("narratives") or {},
                                                  p.get("weekend_developments") or {},
                                                  _voices_week(ending, now, st)),
            "ahead": ahead_week(p, graded_calls(now, db_path), cal, watch),
            "book": book_week(p, attention_counts(ending, now, db_path, log_path),
                              trig, bz),
        }
        extras["rates"] = {name: series(st, k, now, since=(
            dt.date.fromisoformat(now[:10]) - dt.timedelta(days=365)).isoformat())
            for k, name in (("fred.yield_2y", "2-year"), ("fred.yield_10y", "10-year"),
                            ("fred.yield_30y", "30-year"), ("fred.hy_oas", "HY OAS"))}
        extras["contradictions"] = {}
        from .stack_close import _contradiction_history          # noqa: PLC0415
        for c in (built["misfit"]["data"].get("open_contradictions") or []):
            extras["contradictions"][c["name"]] = _contradiction_history(st, c["_id"], now)
    sections = stack_mod.assemble(built, cfg, prior, "weekly")
    changed = wsec.changed_since({}, wis, p, trig,
                                 (built["narratives"].get("data") or {})
                                 and {"data": (built["narratives"].get("data") or {})
                                      .get("voices") or {}})
    ed = {"report": "weekly_stack", "session": ending, "week_ending": ending,
          "changed_since": changed,
          "config_version": cfg.get("version"), "as_of": now,
          "prior_session": (prior or {}).get("week_ending"),
          "sections": sections, "budget": (cfg.get("budget") or {}).get("weekly")}
    return ed, extras


def chart_plan(ed: dict) -> list[str]:
    """W1-W10 within the cap (10, ruled 4 Oct 2026); a fired trigger lifts it by
    one. W6 only with an open contradiction."""
    cap = int((ed.get("budget") or {}).get("charts") or 10)
    if any(s.get("depth_reason") for s in ed["sections"]):
        cap += 1
    misfit = next(s for s in ed["sections"] if s["id"] == "misfit")
    want = ["W1", "W2", "W8", "W7", "W3", "W5", "W4", "W9", "W10"]
    if (misfit.get("data") or {}).get("open_contradictions"):
        want.insert(4, "W6")
    return want[:cap]


# Where each chart prints: a section, or a section's sub-section by index.
PLACE = {"W1": ("tape", None), "W2": ("tape", None), "W8": ("tape", None),
         "W7": ("mechanics", None), "W3": ("plumbing", None),
         "W6": ("misfit", None), "W5": ("positioning", 0),
         "W4": ("positioning", 1), "W9": ("positioning", 3),
         "W10": ("priced", 1)}

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


def chart_data(st, ed: dict, now: str, ending: str, sessions: list,
               pmb: Optional[dict] = None) -> dict:
    """Everything W3, W4, W7-W10 draw, read from the store at edition time."""
    out: dict[str, Any] = {}
    end = dt.date.fromisoformat(now[:10])
    since = lambda days: (end - dt.timedelta(days=days)).isoformat()  # noqa: E731
    out["yields10"] = {name: series(st, k, now, since=since(3653))
                       for k, name in (("fred.yield_2y", "2-year"),
                                       ("fred.yield_10y", "10-year"),
                                       ("fred.yield_30y", "30-year"))}
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
                label = f"hold at the {nxt[0] if nxt else ''} meeting"
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
        from altdata import fed_funds                           # noqa: PLC0415
        out["paths"] = [fed_funds.path_as_of(t, st) for t in
                        (now, week_ago(now),
                         (dt.datetime.fromisoformat(now.replace("Z", "+00:00"))
                          - dt.timedelta(days=30)).isoformat())]
    except Exception:                                           # noqa: BLE001
        out["paths"] = [None, None, None]
    return out


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
    ed, extras = build(p, book, prior, db_path, log_path)
    if narrative:
        stack_prose.write(ed, client=client, model=model, outlooks=[],
                          cadence="weekly")
    stack_mod.enforce_budget(ed)
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
    if "W4" in plan:
        c4 = [v for v in cd["cftc"].values() if v]
        d0 = min((v[0][0] for v in c4), default=now[:10])
        charts["W4"] = charts_mod.z_panel(
            "W4", cd["cftc"], charts_mod.span_title(
                "Speculative positioning, CFTC net contracts as z-scores",
                max((len(v) for v in c4), default=0), "weekly reports", d0, now,
                "two years"), f"{base}_w4", out_dir, min_points=20)
    if "W5" in plan:
        charts["W5"] = charts_mod.bars_chart(
            "W5", extras["leadership"], f"Leadership: the week's sector and "
            f"style-pair returns (%), {then[:10]} to {ending}", f"{base}_w5", out_dir)
    if "W9" in plan:
        g = [v for v in cd["gauges"].values() if v]
        d0 = min((v[0][0] for v in g), default=now[:10])
        charts["W9"] = charts_mod.z_panel(
            "W9", cd["gauges"], charts_mod.span_title(
                "Positioning and sentiment gauges as z-scores",
                max((len(v) for v in g), default=0), "observations", d0, now,
                "two years"), f"{base}_w9", out_dir, ncols=3, min_points=20)
    if "W10" in plan:
        charts["W10"] = charts_mod.w10(cd["odds"], *cd["paths"], f"{base}_w10",
                                       out_dir)
    if "W6" in plan:
        c6 = [v for v in extras["contradictions"].values() if v]
        n6 = max((len(v) for v in c6), default=0)
        d0 = min((v[0][0] for v in c6), default=now[:10])
        charts["W6"] = charts_mod.lines_chart(
            "W6", extras["contradictions"], charts_mod.span_title(
                "Open contradictions: gap z-score", n6, "sessions", d0, now,
                "since each opened"), f"{base}_w6", out_dir, min_points=5)
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
    html_email = render(p, ed, charts, mode="email")
    html_archive = render(p, ed, charts, mode="archive")
    images = [(stack_render.cid(k), c["png"]) for k, c in charts.items() if c.get("png")]
    return {"edition": ed, "charts": charts, "html_email": html_email,
            "html_archive": html_archive, "inline_images": images}


def render(p: dict, ed: dict, charts: dict, mode: str = "email") -> str:
    from . import weekly_render as wr                           # noqa: PLC0415
    base = stack_render.base
    esc = base.esc
    secs = "".join(stack_render.section_html(s, n, charts, mode)
                   for n, s in enumerate(ed["sections"], start=1))
    marks = (f"{stack_render.DIAMOND} marks a line that changed since the Weekly of "
             f"{esc(ed['prior_session'])}." if ed.get("prior_session") else
             "No prior stacked Weekly to compare against: nothing is marked as "
             "changed and nothing collapses.")

    def detail(fn):
        try:
            return fn(p)
        except Exception as exc:                                # noqa: BLE001
            return (f'<p style="{base.NOTE}">detail block unavailable: '
                    f'{esc(type(exc).__name__)}: {esc(exc)}</p>')
    return f"""<div style="{base.WRAP}">
<h1 style="{base.H1}">Weekly &mdash; week ending {esc(ed.get('week_ending'))}</h1>
<p style="{base.SUB}">As-of cutoff {esc(ed.get('as_of'))} &middot; stack
<code>{esc(ed.get('config_version'))}</code> &middot; {esc(ed.get('words'))} words
&middot; {esc(ed.get('chart_count'))} chart(s) &middot; about
{esc(wsec.reading_minutes(ed, int(ed.get('chart_count') or 0)))} minutes to read
&middot; {marks}</p>
{changed_html(ed)}
{secs}
{stack_render.glossary_html(_glossary())}
<p style="{base.NOTE}">Every figure above was read from the store, the register or
the ledger. No figure here is a recommendation; prediction-market odds are the
markets' prices, and every probability the system states is a ledger entry.</p>
</div>"""


def changed_html(ed: dict) -> str:
    """'Changed since last Weekly' (T2.3 item 7), under the header."""
    esc = stack_render.base.esc
    lines = ed.get("changed_since") or []
    if not lines:
        return ""
    return (f'<div style="border:1px solid #cbd5e1;border-radius:4px;padding:8px 10px;'
            f'margin:8px 0 12px 0;font-size:12.5px"><strong>Changed since last '
            f'Weekly</strong><ul style="margin:4px 0 0 0;padding-left:18px">'
            + "".join(f"<li>{esc(x)}</li>" for x in lines) + "</ul></div>")


def _glossary() -> list[dict]:
    from altdata import labels                                  # noqa: PLC0415
    return labels.glossary()


def save_edition(ed: dict, ending: str, archive_dir: Optional[str]) -> Optional[str]:
    from . import deliver                                       # noqa: PLC0415
    return deliver.archive(json.dumps(ed, indent=2, default=str, sort_keys=True),
                           edition_name(ending), archive_dir)
