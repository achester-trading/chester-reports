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
CFTC_CONTRACTS = (("SP500", "S&P 500 futures"), ("UST10Y", "10-year note futures"),
                  ("VIX", "VIX futures"), ("USD_INDEX", "Dollar index futures"),
                  ("JPY", "Yen futures"))


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


def mechanics_week(st, sessions: list[str], cutoff: str, wis: dict) -> dict:
    cards = []
    for s in sessions:
        r = st.latest_as_of("dealer.scorecard_day", cutoff, "SPY")
        rows = [x for x in st.as_of("dealer.scorecard_day", cutoff, "SPY")
                if str(x["observed_at"])[:10] == s]
        if rows:
            try:
                cards.append(json.loads(rows[-1]["value_text"]))
            except (TypeError, ValueError):
                pass
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
    return {"items": items, "not_tracked": nt,
            "table": {"columns": ["Session", "Net GEX", "Flip crossed", "Range %",
                                  "Return %", "Max pain hit"],
                      "rows": [[c.get("session"), c.get("gamma_regime"),
                                c.get("flip_crossed"), c.get("session_range_pct"),
                                c.get("session_return_pct"), c.get("pin_max_pain_hit")]
                               for c in cards]},
            "data": {"scorecards": cards, "dials_now": dials,
                     "dial_changes": wis.get("dial_changes") or []}}


def misfit_week(wis: dict, pmb: Optional[dict]) -> dict:
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
    # THE EXCEPTIONS TABLE, folded in from the old Detail tail (T2.1 item 11).
    table = {"columns": ["Open at the week's end", "Kind", "Opened this week"],
             "rows": [[labels.exception(e), e.split(":", 1)[0],
                       "yes" if e in (wis.get("exceptions_opened") or []) else ""]
                      for e in now_open]}
    return {"items": items, "not_tracked": base.get("not_tracked") or [],
            "data": data, "table": table}


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
    return {"items": items, "data": {"series": data, "tier1_releases": rel},
            "table": {"columns": ["Series", "Level", "Week", "As of"], "rows": rows},
            "not_tracked": ["repo-market stress (SOFR, general collateral)"]}


def tier1_releases(st, now: str, then: str) -> list[dict]:
    """The week's tier-1 releases that occurred, with each tracked series'
    actual, prior and as-of from the store (T2.1 item 13). The tier-1 list is
    the Plumbing trigger's (config/reporting_stack.yaml)."""
    from altdata import events, labels                          # noqa: PLC0415
    tier1 = ((stack_mod.config().get("triggers") or {}).get("plumbing") or {}) \
        .get("tier1_events") or []
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
        name = str(title).split(" -- ")[0]
        if not any(t.lower() in name.lower() for t in tier1):
            continue
        try:
            series = (json.loads(payload or "{}").get("series") or [])
        except ValueError:
            series = []
        for s in series:
            key = f"fred.{s}"
            if (name, key) in seen:
                continue
            seen.add((name, key))
            pts = [r for r in st.as_of(key, now) if r.get("value_num") is not None]
            pts.sort(key=lambda r: str(r["observed_at"]))
            if not pts:
                continue
            a, p = pts[-1], (pts[-2] if len(pts) > 1 else None)
            units = str(derived.registry_entry(key).get("units") or "")

            def fmt(v):
                if v is None:
                    return "n/a"
                return f"{v:,.2f}%" if units in ("%", "percent") else f"{v:,.1f}"
            out.append({"release": name, "date": str(obs_at)[:10], "series": key,
                        "label": labels.metric(key), "actual": a["value_num"],
                        "prior": p["value_num"] if p else None,
                        "actual_text": fmt(a["value_num"]),
                        "prior_text": fmt(p["value_num"] if p else None),
                        "as_of": str(a["observed_at"])[:10]})
    return out


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
        items.append(item(f"pos:cftc:{inst}", f"Speculators' net {name.lower()}: "
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
    return {"items": items, "not_tracked": nt, "data": data,
            "table": {"columns": ["Series", "Level", "Change", "As of"], "rows": rows},
            "_cftc_series": cftc, "_leadership": lead}


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
    b["not_tracked"] = list(b.get("not_tracked") or []) + [
        "the S&P 500 consensus EPS revision (the Weekly's 1% trigger)"]
    return b


def narratives_week_section(nb: dict, wd: Optional[dict] = None) -> dict:
    stories = nb.get("narratives") or []
    items = []
    for s in stories:
        items.append(item(f"narr:{s.get('id')}", f"{s.get('name')}: {s.get('state')}"
                          + (f", last changed {s.get('last_changed')}"
                             if s.get("last_changed") else "")
                          + f"; evidence {s.get('evidence_for', 0)} for, "
                            f"{s.get('evidence_against', 0)} against.", 2,
                          (s.get("state"), s.get("evidence_for"),
                           s.get("evidence_against"))))
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
    return {"items": items, "data": {"stories": [{k: s.get(k) for k in
                                                  ("name", "state", "direction",
                                                   "last_changed")} for s in stories]},
            "not_tracked": ["the voices register (Phase B, week of 19 Oct)"]}


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


def ahead_week(p: dict, calls: dict) -> dict:
    wa = p.get("week_ahead") or {}
    items = []
    keep = ("FOMC", "Consumer Price", "Employment Situation", "Producer Price",
            "Retail", "Personal Income", "Gross Domestic", "ISM", "minutes",
            "refunding", "Surveys of Consumers", "Job Openings", "H.15")
    seen = set()
    for r in (wa.get("releases") or {}).get("rows") or []:
        t = str(r.get("release_name") or "")
        if any(k.lower() in t.lower() for k in keep) and (r["date"], t) not in seen:
            seen.add((r["date"], t))
            items.append(item(f"ahead:{r['date']}:{t}", f"{r['date']}: {t}.", 2,
                              (r["date"], t)))
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
    return {"items": items,
            "table": {"columns": ["Source", "Resolved (4 wk)", "Mean Brier",
                                  "Against a coin"],
                      "rows": [[source_label(r["source"]),
                                r["n"], f"{r['mean_brier']:.3f}",
                                f"{r['vs_coin']:+.3f}"] for r in rows]},
            "data": {"graded_calls": calls,
                     "releases": [i["text"] for i in items if i["key"].startswith("ahead:2")]},
            "not_tracked": ["scenario weights with odds and signposts (scenario set #1, "
                            "Audit #4 agenda item 2)"]}


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


def read_week(pmb: Optional[dict]) -> dict:
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
    return {"items": items[:4], "data": {"five_session_moves": [i["text"] for i in items]}}


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
        built = {
            "read": read_week(pmb),
            "tape": stack_mod.tape_section(book),
            "mechanics": mechanics_week(st, sessions, now, wis),
            "misfit": misfit_week(wis, pmb),
            "plumbing": plumbing_week(st, now, then, book),
            "positioning": pos,
            "priced": priced_week(st, now, then, cfg, pmb, fed, fed_then),
            "narratives": narratives_week_section(p.get("narratives") or {},
                                                  p.get("weekend_developments") or {}),
            "ahead": ahead_week(p, graded_calls(now, db_path)),
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
    ed = {"report": "weekly_stack", "session": ending, "week_ending": ending,
          "config_version": cfg.get("version"), "as_of": now,
          "prior_session": (prior or {}).get("week_ending"),
          "sections": sections, "budget": (cfg.get("budget") or {}).get("weekly")}
    return ed, extras


def chart_plan(ed: dict) -> list[str]:
    cap = int((ed.get("budget") or {}).get("charts") or 6)
    if any(s.get("depth_reason") for s in ed["sections"]):
        cap += 1
    want = ["W1", "W2", "W3", "W4", "W5"]
    misfit = next(s for s in ed["sections"] if s["id"] == "misfit")
    if (misfit.get("data") or {}).get("open_contradictions"):
        want.append("W6")
    return want[:cap]


PLACE = {"W1": "tape", "W2": "tape", "W3": "plumbing", "W4": "positioning",
         "W5": "positioning", "W6": "misfit"}


def produce(p: dict, *, archive_dir: Optional[str], dry_run: bool = False,
            client=None, model: Optional[str] = None, narrative: bool = True,
            db_path: Optional[str] = None, log_path: Optional[Path] = None) -> dict:
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
    prior = load_prior(p.get("previous_week_ending") or "", archive_dir)
    ed, extras = build(p, book, prior, db_path, log_path)
    if narrative:
        stack_prose.write(ed, client=client, model=model, outlooks=[],
                          cadence="weekly")
    stack_mod.enforce_budget(ed)
    plan = chart_plan(ed)
    base = f"weekly_tactical_{ending}"
    out_dir = archive_dir
    charts: dict[str, dict] = {}
    if "W1" in plan:
        charts["W1"] = charts_mod.w1(book, daily, f"{base}_w1", out_dir)
    if "W2" in plan:
        charts["W2"] = charts_mod.w2(book, daily, f"{base}_w2", out_dir)
    if "W3" in plan:
        charts["W3"] = charts_mod.lines_chart(
            "W3", extras["rates"], "Treasury yields and HY OAS, one year (%)",
            f"{base}_w3", out_dir, right="HY OAS")
    if "W4" in plan:
        charts["W4"] = charts_mod.banded_chart(
            "W4", dict(extras["cftc"]),
            "Positioning: CFTC net speculative contracts, two years, +-1 sigma",
            f"{base}_w4", out_dir)
    if "W5" in plan:
        charts["W5"] = charts_mod.bars_chart(
            "W5", extras["leadership"], "Leadership: the week's sector and "
            "style-pair returns (%)", f"{base}_w5", out_dir)
    if "W6" in plan:
        charts["W6"] = charts_mod.lines_chart(
            "W6", extras["contradictions"], "Open contradictions: gap z-score",
            f"{base}_w6", out_dir, min_points=5)
    for cid, c in charts.items():
        s = next(x for x in ed["sections"] if x["id"] == PLACE[cid])
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
&middot; {esc(ed.get('chart_count'))} chart(s) &middot; {marks}</p>
{secs}
<p style="{base.NOTE}">Every figure above was read from the store, the register or
the ledger. No figure here is a recommendation; venue odds are the markets' prices,
and every probability the system states is a ledger entry.</p>
</div>"""


def save_edition(ed: dict, ending: str, archive_dir: Optional[str]) -> Optional[str]:
    from . import deliver                                       # noqa: PLC0415
    return deliver.archive(json.dumps(ed, indent=2, default=str, sort_keys=True),
                           edition_name(ending), archive_dir)
