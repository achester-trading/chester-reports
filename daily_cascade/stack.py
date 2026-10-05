"""
The ten-section stack on the daily close: the data, the depth, the marks.
(docs/briefs/reporting-stack-brief-2026-10-02.md 1, 1.1, 1.3, 1.4 -- Tranche T1)

    from daily_cascade import stack
    edition = stack.build(close_payload, level_book, outlooks, prior_edition)

WHAT CODE DECIDES, AND WHAT THE MODEL WRITES. Everything here is computed from
the store: each section's ITEMS (the lines with figures), its TABLE, its chart, its
DEPTH and the trigger that set it, the change mark on every item, the collapse of
an unchanged section, and the budget's cuts. The model writes only each
section's claim line and, for a deep section, its paragraphs (stack_prose.py), and
"The read" -- the five lines that matter -- over the sections' data.

THE THREE READING RULES (1.3), as code:
  1 a claim line opens every section (prose; audited like any paragraph);
  2 a ◆ marks an item whose fingerprint differs from the prior edition's -- the
    prior edition is the archived stack JSON of the previous session, and the
    model never places a mark;
  3 an outlook prints only with its ledger entry (outlooks.py).

COLLAPSE. A section whose items and table are identical to the prior edition's
prints its claim line and "(unchanged since <date>)", and nothing else.

THE BUDGET (1.4). Words are counted over the PROSE ONLY -- the claim lines and
paragraphs the model writes (T2.2, ruled 4 Oct 2026, every report). Tables and the
code-written lines are data: never counted, never cut. Over budget, the later
paragraphs of deep sections go first, and the section prints "(trimmed)". The
model never summarizes to fit.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from typing import Any, Optional

from altdata import bars as bars_mod, derived, observations, session

SECTION_ORDER = ("read", "tape", "mechanics", "misfit", "plumbing", "positioning",
                 "priced", "narratives", "ahead", "book")


def config() -> dict:
    return bars_mod.load_config()


def _fp(v: Any) -> str:
    return hashlib.sha1(json.dumps(v, sort_keys=True, default=str)
                        .encode()).hexdigest()[:12]


def item(key: str, text: str, priority: int = 2, value: Any = None) -> dict:
    """One line of a section. `value` is what the change mark compares; the
    text is what prints. Priority 1 is the last to be trimmed."""
    return {"key": key, "text": text, "priority": priority,
            "fingerprint": _fp(value if value is not None else text)}


def _signed(v: Optional[float], unit: str) -> str:
    if v is None:
        return "n/a"
    # Basis points whole (T2.1): a 0.4 bp move is noise printed as precision.
    mag = f"{abs(v):,.2f}" if unit == "%" else f"{abs(v):,.0f}"
    sign = "+" if v > 0 else ("−" if v < 0 else "")
    return f"{sign}{mag}{'%' if unit == '%' else ' bp'}"


# ---------------------------------------------------------------------------
# Store readers
# ---------------------------------------------------------------------------
def last_two(st, key: str, as_of: Optional[str], instrument: Optional[str] = None
             ) -> Optional[dict]:
    """{level, prior, change, unit, observed_at} for a series' last two prints."""
    rows = [r for r in st.as_of(key, as_of, instrument)
            if r.get("value_num") is not None]
    if not rows:
        return None
    rows.sort(key=lambda r: str(r["observed_at"]))
    lv = rows[-1]["value_num"]
    pv = rows[-2]["value_num"] if len(rows) > 1 else None
    units = str(derived.registry_entry(key).get("units") or "")
    du = derived.delta_unit_for(key)[0]
    if pv is None:
        ch = None
    elif du == "bps":
        ch = round((lv - pv) * (1.0 if units in ("bps", "bp") else 100.0))
    elif du == "percent" and pv:
        ch = round(100.0 * (lv / pv - 1.0), 2)
    else:
        ch = round(lv - pv, 4)
    return {"key": key, "level": lv, "prior": pv, "change": ch,
            "unit": "bp" if du == "bps" else ("%" if du == "percent" else ""),
            "level_units": units, "observed_at": str(rows[-1]["observed_at"])[:10]}


def _lvl(x: dict, dp: int = 2) -> str:
    u = x.get("level_units")
    v = x["level"]
    if u in ("%", "percent"):
        return f"{v:,.{dp}f}%"
    if u in ("bps", "bp"):
        return f"{v:,.0f} bp"
    return f"{v:,.{dp}f}"


def _change(x: dict) -> str:
    c = x.get("change")
    if c is None:
        return "no prior print"
    if x["unit"] == "bp":
        return _signed(c, "bp")
    if x["unit"] == "%":
        return _signed(c, "%")
    return f"{c:+,.0f}"


# ---------------------------------------------------------------------------
# The sections
# ---------------------------------------------------------------------------
def tape_section(book: dict) -> dict:
    items, rows, gaps = [], [], []
    for i in book.get("instruments") or []:
        f = i.get("frame") or {}
        unit = "bp" if i["kind"] == "yield" else "%"
        s = f.get("session_change_bps" if unit == "bp" else "session_change_pct")
        w = f.get("wtd_change_bps" if unit == "bp" else "wtd_change_pct")
        m = f.get("mtd_change_bps" if unit == "bp" else "mtd_change_pct")
        if f.get("last") is None:
            gaps.append(f"{i['label']}: no daily bar for the session")
            continue
        last = f"{f['last']:,.3f}%" if unit == "bp" else f"{f['last']:,.2f}"
        tested = [lv for lv in i["levels"] if lv.get("status") in ("held", "broke")]
        tail = "; " + ", ".join(f"{lv['label']} {lv['value']:,.2f} {lv['status']}"
                                for lv in tested[:3]) if tested else ""
        pri = 1 if i["id"] in ("spy", "y10") else 2
        items.append(item(f"tape:{i['id']}",
                          f"{i['label']} {last}, {_signed(s, unit)} on the session, "
                          f"{_signed(w, unit)} on the week, {_signed(m, unit)} on the "
                          f"month{tail}.", pri,
                          (f.get("last"), s, [(lv["type"], lv["status"]) for lv in tested])))
        rows.append([i["label"], last, _signed(s, unit), _signed(w, unit),
                     _signed(m, unit)])
        if not i["intraday"]["complete"]:
            gaps.append(f"{i['label']} intraday: {i['intraday']['reason']}")
    return {"items": items,
            "table": {"columns": ["Market", "Last", "Session", "Week", "Month"],
                      "rows": rows},
            "not_tracked": gaps, "charts": ["C1", "C2"],
            "data": {"levels": [i["row"] for i in book.get("instruments") or []],
                     "level_status": {i["id"]: [{"label": lv["label"],
                                                 "value": lv["value"],
                                                 "status": lv.get("status")}
                                                for lv in i["levels"]]
                                      for i in book.get("instruments") or []},
                     "intraday": {i["id"]: i["intraday"]
                                  for i in book.get("instruments") or []}}}


def mechanics_section(p: dict) -> dict:
    items, rows = [], []
    for r in p.get("exposure") or []:
        if r.get("symbol") not in ("SPY", "QQQ", "IWM"):
            continue
        g = r.get("net_gex")
        regime = "positive" if (g or 0) > 0 else "negative"
        flip, spot = r.get("gamma_flip"), r.get("spot")
        side = ("above" if spot and flip and spot > flip else "below") if flip else None
        items.append(item(f"mech:{r['symbol']}",
                          f"{r['symbol']}: net GEX {regime}, spot {spot:,.2f} "
                          f"{side + ' the flip at ' + format(flip, ',.2f') if flip else '(no flip)'}"
                          f"; call wall {r.get('call_wall')}, put wall "
                          f"{r.get('put_wall')}, max pain {r.get('max_pain')}.",
                          1 if r["symbol"] == "SPY" else 2,
                          (regime, flip, r.get("call_wall"), r.get("put_wall"),
                           r.get("max_pain"))))
        rows.append([r["symbol"], f"net GEX {regime}", flip, r.get("call_wall"),
                     r.get("put_wall"), r.get("max_pain")])
    hits = p.get("pin_hits") or {}
    if p.get("pins"):
        items.append(item("mech:pins",
                          f"Pin verdicts: {hits.get('max_pain_hit', 0)} of "
                          f"{len(p['pins'])} symbols closed at max pain, "
                          f"{hits.get('peak_gex_hit', 0)} at the peak-gamma strike.",
                          2, hits))
    ms = p.get("market_state") or {}
    dials = ms.get("dials") or {}
    for d in ("gamma", "vol"):
        st = (dials.get(d) or {}).get("state")
        items.append(item(f"mech:dial:{d}", f"{'Dealer gamma' if d == 'gamma' else 'Volatility regime'} "
                          f"read: {st or 'absent'}.", 2, st))
    return {"items": items,
            "table": {"columns": ["Symbol", "Net GEX", "Flip", "Call wall",
                                  "Put wall", "Max pain"], "rows": rows},
            "not_tracked": ["the IV solver's latest verdict in the report",
                            "the FlashAlpha cross-check"],
            "data": {"exposure": [{k: r.get(k) for k in
                                   ("symbol", "spot", "net_gex", "gamma_flip",
                                    "call_wall", "put_wall", "max_pain",
                                    "dollar_gamma_per_1pct")}
                                  for r in p.get("exposure") or []
                                  if r.get("symbol") in ("SPY", "QQQ", "IWM")],
                     "pin_hits": hits, "pin_rows": len(p.get("pins") or []),
                     "dials": {k: (v or {}).get("state") for k, v in dials.items()}}}


def misfit_section(p: dict, pmb: Optional[dict] = None) -> dict:
    ms = p.get("market_state") or {}
    items = []
    dis = (pmb or {}).get("disagreements") or {}
    for d in dis.get("fed_funds") or []:
        legs = d.get("legs_sum")
        norm_note = (f" (legs normalised from {round(legs * 100):.0f}%)"
                     if legs and abs(legs - 1.0) > 0.005 else "")
        items.append(item(f"misfit:pm_ff:{d['meeting']}:{d['venue']}:{d['side']}",
                          f"{d['venue'].title()} prices a {d['side']} at the "
                          f"{d['meeting']} meeting at {round(d['venue_probability'] * 100):.0f}%"
                          f"{norm_note}"
                          f" against {round(d['fed_funds_implied'] * 100):.0f}% from fed "
                          f"funds futures: {abs(d['gap_points']):.0f} points apart "
                          f"(threshold {d['threshold_points']:g}).", 1,
                          (d["venue_probability"], d["fed_funds_implied"])))
    for d in dis.get("scenario") or []:
        items.append(item(f"misfit:pm_sc:{d['instrument']}",
                          f"A prediction market prices {d['scenario']} at "
                          f"{round(d['venue_probability'] * 100):.0f}% against our weight "
                          f"of {round(d['scenario_weight'] * 100):.0f}% "
                          f"({abs(d['gap_points']):.0f} points).", 1,
                          (d["venue_probability"], d["scenario_weight"])))
    from altdata import labels                                   # noqa: PLC0415
    opened = [c for c in ms.get("contradictions") or [] if c.get("open")]
    for c in opened:
        items.append(item(f"misfit:{c['id']}", contradiction_line(c), 1,
                          (c.get("persistence_days"), c.get("magnitude"))))
    exc = ms.get("exceptions") or []
    if exc:
        items.append(item("misfit:exceptions",
                          f"{len(exc)} exception(s) open: "
                          + "; ".join(labels.exception(e.get("id")) for e in exc[:4])
                          + ("…" if len(exc) > 4 else "") + ".", 2,
                          sorted(str(e.get("id")) for e in exc)))
    if not items:
        items.append(item("misfit:none", "No contradiction is open and no "
                          "exception is flagged.", 1, "none"))
    return {"items": items, "charts": ["C3"] if opened else [],
            "not_tracked": list(dis.get("notes") or []) if pmb else
            ["prediction markets against fed funds: no prediction market stored"],
            "data": {"venue_disagreements": {k: dis.get(k) for k in
                                             ("fed_funds", "scenario")},
                     "open_contradictions_count": len(opened),
                     "exceptions_count": len(exc),
                     "exceptions_by_kind": {k: sum(1 for e in exc
                                                   if e.get("kind") == k)
                                            for k in ("extreme", "contradiction")},
                     "open_contradictions": [contradiction_data(c) for c in opened],
                     "exceptions": [{"name": labels.exception(e.get("id")),
                                     "kind": e.get("kind"), "_id": e.get("id")}
                                    for e in exc]}}


def _z(v) -> Optional[float]:
    return round(float(v), 1) if isinstance(v, (int, float)) else None


def contradiction_line(c: dict) -> str:
    """One contradiction in words: its label, sessions open, z to one decimal."""
    from altdata import labels                                   # noqa: PLC0415
    z, th = _z(c.get("magnitude")), c.get("threshold_z")
    return (f"{labels.contradiction(c.get('id')).capitalize()}: open "
            f"{c.get('persistence_days')} session(s), z {z:+.1f} against a threshold "
            f"of {float(th):.1f}." if z is not None and th is not None else
            f"{labels.contradiction(c.get('id')).capitalize()}: open "
            f"{c.get('persistence_days')} session(s).")


def contradiction_data(c: dict) -> dict:
    """What a prose slice may see of a contradiction: labels, never ids. The id
    rides under `_id` for the charts, and _slice drops `_` keys."""
    from altdata import labels                                   # noqa: PLC0415
    z, th = _z(c.get("magnitude")), c.get("threshold_z")
    return {"name": labels.contradiction(c.get("id")), "_id": c.get("id"),
            "legs": [labels.metric(x) for x in c.get("legs") or []],
            "z": z, "threshold_z": th, "persistence_days": c.get("persistence_days"),
            "since": c.get("since"),
            "excess_over_threshold_z": (round(abs(z) - abs(float(th)), 1)
                                        if z is not None and th else None)}


def _tier1(p: dict, st, cutoff: str, cfg: dict) -> Optional[str]:
    """The plumbing deep trigger's reason, or None (brief 1.1)."""
    trig = (cfg.get("triggers") or {}).get("plumbing") or {}
    day = p["session"]
    nxt = dt.date.fromisoformat(day) + dt.timedelta(days=1)
    while not (session.is_trading_session(nxt) if session.calendar_covers(nxt)
               else nxt.weekday() < 5):
        nxt += dt.timedelta(days=1)
    try:
        from altdata import events                               # noqa: PLC0415
        with events.EventStore(str(st.path)) as ev:
            rows = ev.calendar(day, nxt.isoformat(), as_of=cutoff)
        for r in rows:
            for t in trig.get("tier1_events") or []:
                if t.lower() in str(r.get("title") or "").lower():
                    when = "this session" if str(r["observed_at"])[:10] == day \
                        else "the next session"
                    return f"{t} {when}"
    except Exception:                                           # noqa: BLE001
        pass
    for inst in trig.get("auctions") or []:
        r = st.latest_as_of("auction.high_yield", cutoff, inst)
        if r and str(r.get("observed_at"))[:10] in (day, nxt.isoformat()):
            return f"{inst.split(':')[-1]} auction"
    return None


def plumbing_section(p: dict, st, cutoff: str, cfg: dict) -> dict:
    items, data = [], {}
    keys = (("fred.yield_2y", "2-year"), ("fred.yield_10y", "10-year"),
            ("fred.yield_30y", "30-year"), ("calc.yield_curve_2s10s", "2s10s"),
            ("fred.hy_oas", "High-yield OAS"), ("acm.term_premium_10y",
                                                "10-year term premium (ACM)"))
    for k, name in keys:
        x = last_two(st, k, cutoff)
        if not x:
            continue
        data[name] = x
        items.append(item(f"plumb:{k}", f"{name} {_lvl(x)} ({_change(x)}, as of "
                          f"{x['observed_at']}).",
                          1 if k in ("fred.yield_10y", "fred.hy_oas") else 3,
                          (x["level"], x["change"])))
    reason = _tier1(p, st, cutoff, cfg)
    if not reason:
        for k, th in (((cfg.get("triggers") or {}).get("plumbing") or {})
                      .get("moves_bp") or {}).items():
            x = last_two(st, k, cutoff)
            if x and x.get("change") is not None and abs(x["change"]) >= th:
                reason = f"{k.split('.')[-1]} moved {_change(x)} (threshold {th} bp)"
                break
    return {"items": items, "deep_reason": reason,
            "charts": ["C3"] if reason else [],
            "not_tracked": ["repo-market stress (SOFR, general collateral)"],
            "data": {"series": data}}


def positioning_section(st, cutoff: str) -> dict:
    items, data = [], {}
    for k, inst, name in (("cftc.noncomm_net", "USD_INDEX",
                           "Speculators' net dollar-index futures"),
                          ("cftc.noncomm_net", "JPY", "Speculators' net yen futures"),
                          ("finra.short_interest_days_to_cover", "SPY",
                           "SPY short interest, days to cover"),
                          ("ndl.rtat10_sentiment", "SPY", "Retail sentiment in SPY"),
                          ("apewisdom.mentions", "SPY@wallstreetbets",
                           "SPY mentions on WallStreetBets")):
        x = last_two(st, k, cutoff, inst)
        if not x:
            continue
        data[name] = x
        items.append(item(f"pos:{k}:{inst}", f"{name}: {x['level']:,.2f} "
                          f"({_change(x)}, as of {x['observed_at']}).", 3,
                          (x["level"], x["observed_at"])))
    sectors = []
    for s in ("xlk", "xlf", "xle", "xlv", "xli", "xlp", "xly", "xlu", "xlb",
              "xlre", "xlc"):
        x = last_two(st, f"yfinance.mkt_{s}", cutoff)
        if x and x.get("change") is not None:
            sectors.append((x["change"], s.upper()))
    if len(sectors) >= 4:
        sectors.sort(reverse=True)
        lead = ", ".join(f"{n} {_signed(c, '%')}" for c, n in sectors[:2])
        lag = ", ".join(f"{n} {_signed(c, '%')}" for c, n in sectors[-2:])
        items.insert(0, item("pos:leadership", f"Leadership: {lead}; lagging {lag}.",
                             1, sectors))
        data["sectors"] = [{"sector": n, "change_pct": c} for c, n in sectors]
    return {"items": items[:4] if len(items) > 4 else items,
            "not_tracked": ["S&P 500 futures positioning (CFTC holds yen and "
                            "dollar-index futures only)"],
            "data": data}


def _pct(p: Optional[float]) -> str:
    return "n/a" if p is None else f"{round(p * 100):.0f}%"


def _pts(v: Optional[float]) -> str:
    if v is None:
        return "no prior"
    sign = "+" if v > 0 else ("\u2212" if v < 0 else "")
    return f"{sign}{abs(v):.1f} pts"


def _venue_name(v: str) -> str:
    return {"kalshi": "Kalshi", "polymarket": "Polymarket"}.get(v, v)


def venue_items(pmb: Optional[dict], fed: Optional[dict]) -> list[dict]:
    """What's priced: the rate path, the FOMC odds per meeting, the watch list."""
    items: list[dict] = []
    if fed and fed.get("tracked"):
        items.append(item("priced:rate_path", f"Fed funds futures: {fed['sentence']}.",
                          1, [(m["meeting"], m["post_pct"]) for m in fed["meetings"]]))
    meetings = (fed or {}).get("meetings") or []
    odds = (pmb or {}).get("fomc_odds") or {}
    days = sorted(set(list(odds) + [m["meeting"] for m in meetings]))[:4]
    for d in days:
        parts = []
        lo, hi = ((pmb or {}).get("legs_sum_band") or [0.95, 1.05])
        for v, o in sorted((odds.get(d) or {}).items()):
            tot = o["hold"] + o["hike"] + o["cut"]
            flag = (f" (legs sum to {round(tot * 100):.0f}%)"
                    if not lo <= tot <= hi else "")
            parts.append(f"{_venue_name(v)} hold {_pct(o['hold'])}, hike "
                         f"{_pct(o['hike'])}, cut {_pct(o['cut'])}{flag}")
        m = next((x for x in meetings if abs((dt.date.fromisoformat(x["meeting"])
                                             - dt.date.fromisoformat(d)).days) <= 2),
                 None)
        if m:
            parts.append(f"futures imply {_pct(m['move_probability_25bp'])} of a "
                         f"25 bp {m['direction'] if m['direction'] != 'hold' else 'move'}"
                         f" ({m['pre_pct']:.2f}% to {m['post_pct']:.2f}%)")
        if parts:
            items.append(item(f"priced:fomc:{d}", f"FOMC {d}: " + "; ".join(parts) + ".",
                              1 if d == days[0] else 2,
                              [(d, sorted((odds.get(d) or {}).items()))]))
    wcfg = _watch_cfg()
    for wid, rows in ((pmb or {}).get("watch") or {}).items():
        if wid == "fomc_decision" or not rows:
            continue
        w = wcfg.get(wid) or {}
        label = str(w.get("label") or wid)
        picked = side_rows(rows, w)
        if w.get("compare") is False:
            # EACH VENUE'S MARKET BY ITS OWN TITLE, never paired: a Kalshi CPI
            # strike and a Polymarket CPI range are different questions.
            for v, r in sorted(picked.items()):
                items.append(item(f"priced:pm:{wid}:{v}",
                                  f"{label[0].upper() + label[1:]} -- "
                                  f"{_venue_name(v)}: \"{r.get('question')}\" "
                                  f"{_pct(r['probability'])} "
                                  f"({_pts(r.get('change_1s_points'))} on the session"
                                  + (", outside 10-90%" if r.get("bias_zone") else "")
                                  + ").", 3, (v, r["probability"])))
            continue
        txt = "; ".join(
            f"{_venue_name(v)} {_pct(r['probability'])}"
            f" ({_pts(r.get('change_1s_points'))} on the session"
            + (", outside 10-90%" if r.get("bias_zone") else "") + ")"
            for v, r in sorted(picked.items()))
        side = w.get("side") or "Yes"
        items.append(item(f"priced:pm:{wid}", f"{label[0].upper() + label[1:]} "
                          f"({side}): {txt}.", 3,
                          [(v, r["probability"]) for v, r in sorted(picked.items())]))
    for v, info in ((pmb or {}).get("venues") or {}).items():
        if info.get("outage"):
            items.append(item(f"priced:outage:{v}",
                              f"{_venue_name(v)}: as of {info.get('as_of') or 'never'} "
                              f"(nothing stored for this session).", 1,
                              info.get("as_of")))
    return items


def side_rows(rows: list[dict], w: dict) -> dict:
    """Per venue, the one market an item prints: its declared side's market (the
    soonest-closing where several match), or -- with no side, or compare false --
    the venue's highest-volume market."""
    side = str(w.get("side") or "")
    out: dict = {}
    for r in sorted(rows, key=lambda x: (str(x.get("close_at") or ""),
                                         -(x.get("volume") or 0))):
        v = r["venue"]
        if side and w.get("compare") is not False:
            events = [x for x in rows if x["venue"] == v
                      and x.get("event_id") == r.get("event_id")]
            ok = (side.lower() in str(r.get("outcome") or "").lower()
                  or len(events) == 1)
            if ok and v not in out:
                out[v] = r
        elif v not in out or (r.get("volume") or 0) > (out[v].get("volume") or 0):
            out[v] = r
    return out


BIAS_LEGEND = ("Outside 10-90%: at odds this far from even, prediction markets are "
               "known to misprice the level, so read the change, not the level.")


def priced_section(st, cutoff: str, cfg: dict, pmb: Optional[dict] = None,
                   fed: Optional[dict] = None, fed_prior: Optional[dict] = None
                   ) -> dict:
    items, data = [], {}
    for k, name in (("fred.breakeven_5y", "5-year breakeven"),
                    ("fred.breakeven_10y", "10-year breakeven"),
                    ("fred.breakeven_5y5y", "5-year, 5-year-forward breakeven"),
                    ("umich.expect_5_10y", "Michigan 5-10 year expectations"),
                    ("nyfed.sce_3y", "NY Fed 3-year expectations")):
        x = last_two(st, k, cutoff)
        if not x:
            continue
        data[name] = x
        items.append(item(f"priced:{k}", f"{name} {_lvl(x)} ({_change(x)}, as of "
                          f"{x['observed_at']}).", 2, (x["level"], x["change"])))
    items = venue_items(pmb, fed) + items
    trig = (cfg.get("triggers") or {}).get("priced") or {}
    reason = None
    for k, th in (trig.get("moves_bp") or {}).items():
        x = last_two(st, k, cutoff)
        if x and x.get("change") is not None and abs(x["change"]) >= th:
            reason = f"{k.split('.')[-1]} moved {_change(x)} (threshold {th} bp)"
            break
    rate_th = float(trig.get("fomc_implied_rate_next_four_meetings_bp") or 12.5)
    if not reason and fed and fed_prior and fed.get("tracked"):
        was = {m["meeting"]: m["post_pct"] for m in fed_prior.get("meetings") or []}
        for m in (fed.get("meetings") or [])[:4]:
            ch = derived.rate_bp_change(m["post_pct"], was.get(m["meeting"]))
            if ch is not None and abs(ch) >= rate_th:
                reason = (f"the implied rate after the {m['meeting']} meeting moved "
                          f"{_signed(ch, 'bp')} (threshold {rate_th:g} bp)")
                break
    pm_th = float(trig.get("prediction_market_points") or 10)
    if not reason:
        for sh in (pmb or {}).get("shocks") or []:
            if abs(sh["change_1s_points"]) >= pm_th:
                reason = (f"{_venue_name(sh['venue'])} {sh.get('question')!s:.60} moved "
                          f"{_pts(sh['change_1s_points'])} (threshold {pm_th:g} pts)")
                break
    not_tracked = ["one-year inflation expectations"]
    if not fed or not fed.get("tracked"):
        not_tracked.insert(0, "the fed funds futures rate path: "
                              + ((fed or {}).get("reason") or "no contracts stored"))
    if not pmb or not pmb.get("markets"):
        not_tracked.insert(0, "prediction-market odds: no venue market stored")
    legend = BIAS_LEGEND if any("outside 10-90%" in i["text"] for i in items) else None
    return {"items": items, "deep_reason": reason, "not_tracked": not_tracked,
            "legend": legend,
            "data": {"series": data,
                     "rate_path": {k: (fed or {}).get(k) for k in
                                   ("meetings", "tracked", "reason", "sentence",
                                    "as_of", "contracts")},
                     "venues": {k: (pmb or {}).get(k) for k in
                                ("venues", "fomc_odds", "shocks")},
                     "watch": {wid: [{k: r.get(k) for k in
                                      ("venue", "question", "outcome", "probability",
                                       "probability_ordinal", "change_1s_points",
                                       "change_5s_points", "change_20s_points",
                                       "bias_zone", "as_of")}
                                     for r in rows[:6]]
                               for wid, rows in ((pmb or {}).get("watch") or {}).items()}}}


def read_items(pmb: Optional[dict]) -> list[dict]:
    """The read: an attention shock earns a line (brief 4)."""
    out = []
    for sh in (pmb or {}).get("shocks") or []:
        out.append(item(f"read:shock:{sh['instrument']}",
                        shock_sentence(sh, "in a session",
                                       sh["change_1s_points"]), 1,
                        (sh["probability"], sh["change_1s_points"])))
    return out


def _watch_cfg() -> dict:
    try:
        from altdata.sources import prediction_markets as pm_src  # noqa: PLC0415
        return {w["id"]: w for w in pm_src.load_config().get("watch_list") or []}
    except Exception:                                           # noqa: BLE001
        return {}


def market_subject(m: dict) -> str:
    """A venue market in words, from its watch item's declared SUBJECT template
    (config/prediction_markets.yaml) -- never the raw market title, except where
    an item prints each venue's market by its own title."""
    from altdata.prediction_markets import classify_fomc        # noqa: PLC0415
    w = _watch_cfg().get(m.get("watch_id")) or {}
    day = str(m.get("decision_date") or m.get("close_at") or "")[:10]
    try:
        d = dt.date.fromisoformat(day)
        meeting, year = d.strftime("%B"), str(d.year)
    except ValueError:
        meeting = year = ""
    side = classify_fomc(m.get("question") or "", m.get("outcome") or "") or "move"
    tpl = w.get("subject")
    if not tpl:
        story = str(m.get("watch_id") or "").split(":", 1)[-1].replace("_", " ")
        return f"a market on the {story} story"
    return tpl.format(side=side, meeting=meeting, year=year,
                      title=m.get("question") or m.get("event_title") or "")


def shock_sentence(sh: dict, window: str, change: float) -> str:
    """The template sentence for a venue move (T2.1 item 4)."""
    return (f"{_venue_name(sh['venue'])}'s odds of {market_subject(sh)} moved "
            f"{_pts(change)} {window}, to {_pct(sh['probability'])}"
            + (" (confirmed by the other venue or by volume)"
               if sh.get("state") == "CONFIRMED" else
               " (one venue, thin volume: unconfirmed)" if sh.get("state") else "")
            + ".")


def narratives_section(st, session_day: Optional[str] = None,
                       cutoff: Optional[str] = None) -> dict:
    try:
        from altdata import narratives                         # noqa: PLC0415
        with narratives.NarrativeRegister(str(st.path)) as reg:
            rows = reg.all("active")
    except Exception:                                           # noqa: BLE001
        rows = []
    # PHASE B (4 Oct 2026): the day's most-cited story and a dissent if one was
    # published, each sourced, from the voices the 06:45 scan stored. Fixed
    # sentences over stored rows; every view printed is audited.
    voices = None
    if session_day and cutoff:
        try:
            from . import voices_block                          # noqa: PLC0415
            voices = voices_block.daily_line(session_day, cutoff, str(st.path))
        except Exception as exc:                                # noqa: BLE001
            voices = {"lines": [f"Voices unavailable: {type(exc).__name__}."]}
    vitems = [item(f"narr:voices:{n}", t, 1, t)
              for n, t in enumerate((voices or {}).get("lines") or [])]
    if not rows:
        return {"items": [item("narr:none", "No story is active in the register.",
                               1, "none")] + vitems, "data": {"voices": voices}}
    states = {}
    for r in rows:
        states.setdefault(r["state"], []).append(r["name"])
    text = "; ".join(f"{s}: {', '.join(n)}" for s, n in sorted(states.items()))
    return {"items": vitems + [item("narr:states", f"Stories — {text}.", 2, states)],
            "data": {"stories": [{"story": r["name"], "state": r["state"]}
                                 for r in rows],
                     "voices": {k: (voices or {}).get(k) for k in
                                ("lines", "story", "sides")}}}


def ahead_section(p: dict, st, cutoff: str, outlook_rows: list[dict]) -> dict:
    items = []
    day = dt.date.fromisoformat(p["session"])
    last = (day + dt.timedelta(days=7)).isoformat()
    try:
        from altdata import events                               # noqa: PLC0415
        with events.EventStore(str(st.path)) as ev:
            cal = [r for r in ev.calendar((day + dt.timedelta(days=1)).isoformat(),
                                          last, as_of=cutoff)
                   if r.get("type") in ("scheduled", "session_event")]
    except Exception:                                           # noqa: BLE001
        cal = []
    keep = ("FOMC", "Consumer Price Index", "Employment Situation", "Producer Price",
            "Retail", "Personal Income", "Gross Domestic", "ISM", "earnings",
            "OPEX", "minutes", "refunding", "midterm", "Surveys of Consumers",
            "Job Openings")
    seen = set()
    for r in cal:
        t = str(r.get("title") or "")
        if not any(k.lower() in t.lower() for k in keep):
            continue
        key = (str(r["observed_at"])[:10], t.split(" -- ")[0])
        if key in seen:
            continue
        seen.add(key)
        items.append(item(f"ahead:{key[0]}:{key[1]}", f"{key[0]}: {key[1]}.", 2, key))
    for o in outlook_rows:
        if o["state"] != "computed":
            continue
        items.insert(0, item(f"ahead:outlook:{o['id']}",
                             f"The base rate for {o['claim']} is "
                             f"{round(o['probability'] * 100):.0f}% (n={o['n']}); "
                             f"resolves {o['horizon_date']} ("
                             + (f"ledger {str(o['ledger_id'])[:12]})."
                                if not str(o["ledger_id"]).startswith("dry-run")
                                else "not recorded: dry run)."), 1,
                             (o["probability"], o["claim"])))
    return {"items": items[:9],
            "data": {"events": [i["text"] for i in items if "outlook" not in i["key"]],
                     "outlooks": [{k: o.get(k) for k in
                                   ("id", "kind", "claim", "probability", "n",
                                    "horizon_date", "ledger_id", "state", "reason")}
                                  for o in outlook_rows]}}


def book_section(p: dict) -> dict:
    pf = p.get("portfolio") or {}
    pos = pf.get("positions") or []
    items = [item("book:positions", f"{len(pos)} open position(s) in Portfolio Truth"
                  + (": " + ", ".join(f"{x['instrument']} {x.get('qty'):+g}"
                                      for x in pos[:4]) if pos else "") + ".", 1,
                  [(x["instrument"], x.get("qty")) for x in pos])]
    e = p.get("enforcement") or {}
    rb = e.get("rule_breaks") or []
    items.append(item("book:breaks", f"{len(rb)} rule break(s) this session; "
                      f"{e.get('rule_breaks_total', 0)} on the register.", 2,
                      len(rb)))
    for c in pf.get("closed_today") or []:
        pnl = (f"{c['pnl_local']:+,.2f} {c.get('currency') or ''}"
               if c.get("pnl_local") is not None else "exit not recorded")
        items.append(item(f"book:closed:{c['id']}", f"Closed {c['instrument']}: "
                          f"realised {pnl}.", 1, c.get("pnl_local")))
    return {"items": items, "data": {"positions": len(pos), "rule_breaks": len(rb)}}


# ---------------------------------------------------------------------------
# Assembly: depth, marks, collapse, budget
# ---------------------------------------------------------------------------
def venues_and_path(session_day: str, cutoff: str, st) -> tuple:
    """6d: the venue block, today's rate path and the prior session's. Each one
    that cannot be read is None, and the sections say what is not tracked."""
    fed = fed_prior = pmb = None
    try:
        from altdata import fed_funds                            # noqa: PLC0415
        fed = fed_funds.path_as_of(cutoff, st)
        prev = session.previous_trading_session(session_day)
        from altdata.prediction_markets import _close_cutoff     # noqa: PLC0415
        fed_prior = fed_funds.path_as_of(_close_cutoff(prev), st)
    except Exception:                                           # noqa: BLE001
        pass
    try:
        from altdata import prediction_markets as pm             # noqa: PLC0415
        pmb = pm.block(session_day, cutoff, fed_path=fed, store=st)
    except Exception:                                           # noqa: BLE001
        pass
    return pmb, fed, fed_prior


def build(p: dict, book: dict, outlook_rows: list[dict],
          prior: Optional[dict] = None, store_path: Optional[str] = None) -> dict:
    cfg = config()
    cutoff = p.get("as_of") or session.utc_iso()
    with observations.ObservationStore(store_path) as st:
        pmb, fed, fed_prior = venues_and_path(p["session"], cutoff, st)
        built = {
            "read": {"items": read_items(pmb), "data": {
                "attention_shocks": (pmb or {}).get("shocks") or []}},
            "tape": tape_section(book),
            "mechanics": mechanics_section(p),
            "misfit": misfit_section(p, pmb),
            "plumbing": plumbing_section(p, st, cutoff, cfg),
            "positioning": positioning_section(st, cutoff),
            "priced": priced_section(st, cutoff, cfg, pmb, fed, fed_prior),
            "narratives": narratives_section(st, p["session"], cutoff),
            "ahead": ahead_section(p, st, cutoff, outlook_rows),
            "book": book_section(p),
        }
    out = assemble(built, cfg, prior, "daily")
    return {"report": "daily_close_stack", "session": p["session"],
            "config_version": cfg.get("version"), "as_of": cutoff,
            "prior_session": (prior or {}).get("session"),
            "sections": out, "budget": (cfg.get("budget") or {}).get("daily")}


def assemble(built: dict, cfg: dict, prior: Optional[dict],
             cadence: str = "daily") -> list[dict]:
    """The ten sections in order, at the cadence's depth, marked and collapsed.

    One function for every cadence (T2): the daily close and the Weekly differ in
    each section's depth and in which conditional rule may deepen it -- both read
    from config/reporting_stack.yaml under the cadence's key -- and in nothing
    else. The change marks and the collapse compare against the PRIOR EDITION OF
    THE SAME CADENCE, never across cadences."""
    specs = {s["id"]: s for s in cfg.get("sections") or []}
    prior_secs = {s["id"]: s for s in (prior or {}).get("sections") or []}
    deep_key = "deep_on" if cadence == "daily" else f"{cadence}_deep_on"
    out = []
    for sid in SECTION_ORDER:
        sp, b = specs[sid], built[sid]
        depth = sp.get(cadence) or "light"
        reason = b.get("deep_reason")
        if sp.get(deep_key) and reason:
            depth = "deep"
        pr = prior_secs.get(sid) or {}
        pmarks = {i["key"]: i["fingerprint"] for i in pr.get("items") or []}
        for it in b["items"]:
            it["changed"] = bool(prior) and pmarks.get(it["key"]) != it["fingerprint"]
        fp = _fp([(i["key"], i["fingerprint"]) for i in b["items"]]
                 + [b.get("table")])
        unchanged = bool(prior) and pr.get("fingerprint") == fp and sid != "read"
        out.append({"id": sid, "title": sp["title"],
                    "subtitle": sp.get("subtitle"), "depth": depth,
                    "depth_reason": (reason if depth == "deep" and sp.get(deep_key)
                                     else None),
                    "items": b["items"], "table": b.get("table"),
                    "charts": b.get("charts") or [], "data": b.get("data") or {},
                    "not_tracked": b.get("not_tracked") or [],
                    "legend": b.get("legend"),
                    # T2.2: a section may print its lines as data beside a table
                    # (print_items False), carry a note above its table, and hold
                    # sub-sections, each with its own table and one paragraph.
                    "print_items": b.get("print_items", True),
                    "prose_paragraphs": b.get("prose_paragraphs"),
                    "table_note": b.get("table_note"),
                    "subsections": b.get("subsections") or [],
                    "fingerprint": fp, "collapsed": unchanged,
                    "unchanged_since": ((pr.get("unchanged_since") or
                                         (prior or {}).get("session"))
                                        if unchanged else None),
                    "prior_claim": pr.get("claim") if unchanged else None,
                    "claim": None, "paragraphs": [], "trimmed": False})
    return out


def words(text: Optional[str]) -> int:
    return len(re.findall(r"[\w'.%$−+-]+", text or ""))


def section_words(s: dict) -> int:
    """PROSE ONLY (T2.2, 4 Oct 2026): the claim line, the paragraphs and each
    sub-section's paragraph. Items and tables are data and never count."""
    if s.get("collapsed"):
        return words(s.get("claim"))
    return (words(s.get("claim")) + sum(words(x) for x in s.get("paragraphs") or [])
            + sum(words(ss.get("paragraph")) for ss in s.get("subsections") or []))


def enforce_budget(ed: dict) -> dict:
    """Trim to the word budget, lowest priority first; mark what was cut."""
    limit = int((ed.get("budget") or {}).get("words") or 1000)
    total = lambda: sum(section_words(s) for s in ed["sections"])  # noqa: E731

    def cut_paragraphs(keep: int) -> None:
        for s in reversed(ed["sections"]):
            while total() > limit and len(s.get("paragraphs") or []) > keep:
                s["paragraphs"] = s["paragraphs"][:-1]
                s["trimmed"] = True

    # PROSE ONLY IS CUT (T2.2): a deep section's third paragraph, then second
    # paragraphs. A claim line, an item and a table are never cut -- they are
    # data, and the budget counts prose.
    cut_paragraphs(2)
    cut_paragraphs(1)
    ed["words"] = total()
    return ed


def chart_plan(ed: dict, available: dict[str, Optional[str]]) -> list[str]:
    """Which charts this edition carries, by the brief's rule (3.2), within the
    cap (1.4); a fired trigger lifts the cap by one (1.1)."""
    cap = int((ed.get("budget") or {}).get("charts") or 3)
    fired = any(s.get("depth_reason") for s in ed["sections"])
    cap += 1 if fired else 0
    want = ["C1", "C2"]
    misfit = next(s for s in ed["sections"] if s["id"] == "misfit")
    plumb = next(s for s in ed["sections"] if s["id"] == "plumbing")
    if (misfit.get("data") or {}).get("open_contradictions"):
        want.append("C3")
    elif plumb.get("depth") == "deep":
        want.append("C3")
    return [c for c in want][:cap]
