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
    # weekly-fixes-7 item 12: the sign is the ROUNDED figure's, so -0.4 bp
    # prints "0 bp", never "−0 bp" (the signed-zero rule).
    sign = "" if not float(mag.replace(",", "")) else ("+" if v > 0 else ("−" if v < 0 else ""))
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
    units = derived.level_units_of(key)
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
    if x.get("change_display"):
        return x["change_display"]
    # weekly-fixes-7 item 12: a raw change below one keeps two places (short
    # interest's days to cover moved −0.12, which printed "−0"); one that rounds
    # to zero there too is "unch", never a signed zero.
    # W8-8 (weekly-fixes-8): a series that declares its level's decimals (`dp`)
    # prints its change to them -- days to cover's −1.27 printed "−1".
    dp = x.get("dp")
    if dp is None:
        dp = 0 if abs(c) >= 1 else 2
    if round(c, dp) == 0:
        return "unch"
    return f"{'+' if c > 0 else '−'}{abs(c):,.{dp}f}"


# ---------------------------------------------------------------------------
# The sections
# ---------------------------------------------------------------------------
def tape_section(book: dict, vp_windows: Optional[tuple] = ("session",
                                                          "prior_session")) -> dict:
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
        # The profile's levels (VP-1) print in their own table below, so the
        # line's tested levels stay the ones it named before them.
        tested = [lv for lv in i["levels"] if lv.get("status") in ("held", "broke")
                  and not lv["type"].startswith("vp_")]
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
    # OVERNIGHT AGAINST THE CASH SESSION (T2.3 item 1), one line on the close.
    from .weekly_sections import overnight_line                 # noqa: PLC0415
    ol = overnight_line(book)
    if ol:
        items.insert(0, item("tape:overnight", ol, 1, ol))
        if not i["intraday"]["complete"]:
            gaps.append(f"{i['label']} intraday: {i['intraday']['reason']}")
    # THE VOLUME PROFILE (VP-1 item 6): the session's value area against the
    # prior session's, one row per configured instrument, by declared rule.
    from altdata import bars as bars_mod, volume_profile as vp  # noqa: PLC0415
    # The Weekly passes None and prints its own, the week against the prior week.
    units = {t["id"]: t.get("unit") for t in bars_mod.tape()}
    vpt = (vp.table(book.get("instruments") or [], *vp_windows, units) if vp_windows
           else {"rows": [], "not_tracked": [], "data": []})
    return {"items": items,
            "table": {"columns": ["Market", "Last", "Session", "Week", "Month"],
                      "rows": rows},
            "tables": [{k: vpt[k] for k in ("columns", "rows")}] if vpt["rows"] else [],
            "not_tracked": gaps + vpt["not_tracked"], "charts": ["C1", "C2"],
            "data": {"levels": [i["row"] for i in book.get("instruments") or []],
                     "level_status": {i["id"]: [{"label": lv["label"],
                                                 "value": lv["value"],
                                                 "status": lv.get("status")}
                                                for lv in i["levels"]]
                                      for i in book.get("instruments") or []},
                     "intraday": {i["id"]: i["intraday"]
                                  for i in book.get("instruments") or []},
                     "volume_profile": vpt["data"]}}


def state_vectors(p: dict, st) -> Optional[list]:
    """EL-5: the state vector of each SPY capture of the session under the
    payload's `computed_dir` (altdata/state_vector.py). None when the payload names
    no directory -- a gate's synthetic payload -- so nothing is read."""
    if not p.get("computed_dir"):
        return None
    from altdata import state_vector as sv                      # noqa: PLC0415
    from . import dealer_block                                  # noqa: PLC0415
    out = []
    try:
        caps = sorted((c for c in dealer_block.captures_on(p["session"], "SPY",
                                                           p["computed_dir"])
                       if not c.get("error") and c.get("fetched_at")),
                      key=lambda c: c["fetched_at"])
        if not caps:
            return []
        from altdata import events as events_mod                # noqa: PLC0415
        with bars_mod.BarStore() as bst:
            try:
                evs = events_mod.EventStore()
            except Exception:                                   # noqa: BLE001
                evs = None
            try:
                for c in caps:
                    out.append(sv.gather(st, bst, evs, c, p["session"]))
            finally:
                if evs is not None:
                    evs.close()
    except Exception as exc:                                    # noqa: BLE001
        return [{"absent": f"state vector: {type(exc).__name__}: {exc}"}]
    return out


def mechanics_section(p: dict, dealer: Optional[list] = None,
                      vol_ev: Optional[dict] = None,
                      state_vecs: Optional[list] = None) -> dict:
    """The close's Mechanics. 6b part 1 (brief v2, ratified 16 Oct 2026): the
    regime word is GATED on net-to-gross (dealer_block.regime), the walls are the
    OTM walls (audit F5), and `dealer` -- the dealer block per configured symbol
    (daily_cascade/dealer_block.py) -- adds T1 with its quality panel, T4, T2 and
    the decision summary as sub-sections, the summary's lead as one item, and
    the sign convention once, as the section's note."""
    from . import dealer_block                                  # noqa: PLC0415
    dcfg = dealer_block.config()
    items, rows = [], []
    for r in p.get("exposure") or []:
        if r.get("symbol") not in ("SPY", "QQQ", "IWM"):
            continue
        g = r.get("net_gex")
        regime = dealer_block.regime(g, r.get("net_to_gross"), dcfg)
        flip, spot = r.get("gamma_flip"), r.get("spot")
        side = ("above" if spot and flip and spot > flip else "below") if flip else None
        cw = r.get("call_wall_otm", r.get("call_wall"))
        pw = r.get("put_wall_otm", r.get("put_wall"))
        items.append(item(f"mech:{r['symbol']}",
                          f"{r['symbol']}: {regime}, spot {spot:,.2f} "
                          f"{side + ' the zero-gamma level at ' + format(flip, ',.2f') if flip else '(no zero-gamma level)'}"
                          f"; OTM call wall {cw}, OTM put gamma wall {pw}, max pain "
                          f"{r.get('max_pain')}.",
                          1 if r["symbol"] == "SPY" else 2,
                          # The legacy all-strike peaks stay in the change mark,
                          # so a moved peak still marks the line.
                          (regime, flip, cw, pw, r.get("max_pain"),
                           r.get("call_wall"), r.get("put_wall"))))
        rows.append([r["symbol"], regime, flip, cw, pw, r.get("max_pain")])
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
    subs, notes, nt, extra = [], [], [], {}
    for b in dealer or []:
        if b.get("absent"):
            nt.append(b["absent"])
            continue
        subs += b["subsections"]
        lead = b["summary"]["lines"][0]
        su = b["summary"]["setups"]
        items.append(item(f"mech:dealer:{b['data']['symbol']}",
                          f"{b['data']['symbol']} dealer summary: {lead} "
                          + (f"Setups whose conditions hold: "
                             f"{', '.join(dict.fromkeys(x['id'] for x in su))}."
                             if su else "No setup."),
                          1, b["fingerprint"]))
        if b.get("notes") and not notes:
            notes = [x for x in b["notes"] if x]
        if b.get("sentences") and "dealer_sentences" not in extra:
            extra["dealer_sentences"] = b["sentences"]
        if b.get("_window_rows"):
            extra.setdefault("_dealer_profiles", []).append(b["_window_rows"])
    # THE VOLATILITY EVENT (Batch 9 item 52; altdata/vol_event.py): silent unless
    # the trigger fires; then its sub-section, its trigger line as an item, and
    # the paragraph's facts.
    if vol_ev and vol_ev.get("fired"):
        from altdata import vol_event as ve                     # noqa: PLC0415
        subs = [ve.block(vol_ev)] + subs
        items.append(item("mech:vol_event", vol_ev["trigger_line"], 1,
                          vol_ev["trigger_line"]))
        extra["vol_event"] = ve.facts(vol_ev)
    if vol_ev is not None:
        extra["_vol_event"] = vol_ev
    # EL-5: THE STATE VECTOR, one compact line per capture; numbers only.
    if state_vecs:
        from altdata import state_vector as sv                  # noqa: PLC0415
        good = [g for g in state_vecs if g.get("vector")]
        lines = [sv.line(g) for g in good] + [g["absent"] for g in state_vecs
                                              if g.get("absent")]
        if lines:
            subs.append({"title": "State vector, SPY", "table": None, "lines": lines})
        if good:
            extra["_state_vectors"] = good
    return {"items": items,
            "table": {"columns": ["Symbol", "Regime (gated)", "Zero-gamma",
                                  "OTM call wall", "OTM put wall", "Max pain"],
                      "rows": rows},
            "subsections": subs, "notes": notes,
            "not_tracked": ["the IV solver's latest verdict in the report",
                            "the FlashAlpha cross-check"] + nt,
            "data": {"exposure": [{k: r.get(k) for k in
                                   ("symbol", "spot", "net_gex", "gamma_flip",
                                    "call_wall", "put_wall", "max_pain",
                                    "dollar_gamma_per_1pct")}
                                  for r in p.get("exposure") or []
                                  if r.get("symbol") in ("SPY", "QQQ", "IWM")],
                     "pin_hits": hits, "pin_rows": len(p.get("pins") or []),
                     "dials": {k: (v or {}).get("state") for k, v in dials.items()},
                     **extra}}


def screen_items(screen: Optional[dict], cadence: str = "daily") -> tuple[list, dict]:
    """THE STORE-WIDE MOVE SCREEN IN WHAT DOESN'T FIT (Audit #4 Category 1 items 1
    and 5; altdata/move_screen.py): the top flags by |z|, each "<series> +x.xσ
    1-day / +x.xσ 5-day · false flag k/N", SR-35's 10-year companion beside its
    row, the rest counted ("n more past 2.5σ -- in the tables"); the EM line
    (idiosyncratic or systemic); the contagion lines -- every shock on the close,
    only one that passed on the Weekly and the Monthly. (items, data)."""
    if not screen:
        return [], {}
    from altdata import move_screen                              # noqa: PLC0415
    rl = move_screen.report_lines(screen, cadence)
    items = [item(f"misfit:move:{n}", ln, 1 if n < 2 else 2, ln)
             for n, ln in enumerate(rl["lines"])]
    if rl["more"]:
        items.append(item("misfit:move:more", rl["more"], 3, rl["more"]))
    em = screen.get("em") or {}
    line = em.get("line") or move_screen.em_line(em)
    if line:
        items.append(item("misfit:em", line, 1, em.get("state")))
    weekly = cadence != "daily"
    for c in screen.get("contagion") or []:
        cl = move_screen.contagion_line(c, weekly=weekly)
        if cl:
            items.append(item(f"misfit:contagion:{c['country']}:{c['shock_date']}",
                              cl, 1, c.get("status")))
    data = {"move_screen": {"screened": screen.get("screened"),
                            "flags": [{"series": f.get("label"), "z_1d": f.get("z1"),
                                       "z_5d": f.get("z5")}
                                      for f in (screen.get("flags") or [])[:10]],
                            "em_state": em.get("state")},
            "_move_screen_reference": rl["reference"]}
    return items, data


def move_screen_detail(screen: Optional[dict], cadence: str = "daily") -> list[dict]:
    """The reference tier: every flag, in a detail table after section 10."""
    if not screen or not screen.get("flags"):
        return []
    from altdata import move_screen                              # noqa: PLC0415
    ref = move_screen.report_lines(screen, cadence)["reference"]
    return [{"title": "Moves past 2.5σ", "table": ref,
             "notes": [f"{screen.get('screened')} daily series screened against their "
                       f"own five-year history; {len(screen.get('skipped') or [])} "
                       f"skipped for want of 500 observations."]}]


def misfit_section(p: dict, pmb: Optional[dict] = None,
                   screen: Optional[dict] = None) -> dict:
    ms = p.get("market_state") or {}
    items = []
    dis = (pmb or {}).get("disagreements") or {}
    for d in dis.get("fed_funds") or []:
        legs = d.get("legs_sum")
        norm_note = (f" (normalised; legs sum {round(legs * 100):.0f}%)"
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
    sitems, sdata = screen_items(screen, "daily")
    items += sitems
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
                                    for e in exc], **sdata}}


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


def releases_on(day: str, st, cutoff: str, cfg: dict) -> list[str]:
    """The tier-1 releases (triggers.plumbing.tier1_events) on `day`, by the
    stored events calendar -- the dealer block's d_forced_flow release day. []
    when none, or when the calendar cannot be read."""
    trig = (cfg.get("triggers") or {}).get("plumbing") or {}
    out: list[str] = []
    try:
        from altdata import events                               # noqa: PLC0415
        with events.EventStore(str(st.path)) as ev:
            rows = ev.calendar(day, day, as_of=cutoff)
        for r in rows:
            for t in trig.get("tier1_events") or []:
                if (t.lower() in str(r.get("title") or "").lower()
                        and str(r["observed_at"])[:10] == day and t not in out):
                    out.append(t)
    except Exception:                                           # noqa: BLE001
        pass
    return out


def vol_event_for(p: dict, st, cutoff: str) -> Optional[dict]:
    """Batch 9 item 52: the session's volatility read, from the store, when the
    payload asks for it (`vol_event`, set by the close's payload builder); None
    for a gate's synthetic payload, so nothing is read."""
    if not p.get("vol_event"):
        return None
    from altdata import vol_event as ve                         # noqa: PLC0415
    try:
        prof = None
        if p.get("computed_dir"):
            from . import dealer_block                          # noqa: PLC0415
            prof = dealer_block.newest_settled(p["session"], "SPY", p["computed_dir"],
                                               lookback_days=0)
        ev = ve.evaluate(ve.read_series(st, cutoff), p["session"], profile=prof,
                         attributions=ve.attributions_for(p["session"], cutoff))
        # Batch 14 item 71 (F5): the "liquidity" lens, a report-only row.
        if ev.get("fired"):
            from . import batch14_b1_block                      # noqa: PLC0415
            ve.with_liquidity(ev, batch14_b1_block.liquidity_lens(st, p["session"],
                                                                  cutoff))
        return ev
    except Exception as exc:                                    # noqa: BLE001
        return {"day": p["session"], "fired": False, "trigger": {},
                "trigger_line": f"Volatility: the read faulted ({type(exc).__name__})"}


def _dealer_chart_dir(p: dict) -> Optional[str]:
    from . import dealer_block                                  # noqa: PLC0415
    return dealer_block.chart_dir(p.get("computed_dir"), p.get("session"), 0)


def dealer_blocks(p: dict, st, cutoff: str, cfg: dict) -> Optional[list]:
    """The dealer block (6b part 1) for the close, read from the computed
    profiles under the payload's `computed_dir`. None when the payload names no
    directory -- a gate's synthetic payload -- so nothing is read."""
    if not p.get("computed_dir"):
        return None
    from . import dealer_block                                  # noqa: PLC0415
    # The close's capture is the settled 16:10, so its summary is for the next
    # session (dealer_block.target_session): that session's releases.
    nxt = dt.date.fromisoformat(p["session"]) + dt.timedelta(days=1)
    while not (session.is_trading_session(nxt) if session.calendar_covers(nxt)
               else nxt.weekday() < 5):
        nxt += dt.timedelta(days=1)
    try:
        return dealer_block.for_session(p["session"], base_dir=p["computed_dir"],
                                        releases=releases_on(nxt.isoformat(), st,
                                                             cutoff, cfg),
                                        st=st, cutoff=cutoff)
    except Exception as exc:                                    # noqa: BLE001
        return [{"absent": f"dealer block: {type(exc).__name__}: {exc}"}]


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
    # 6E, THE REST (16 Oct 2026): the close adopts the lens columns as one table
    # of the same six series -- data, so no prose word and no chart. What it
    # gains: each series' own forms (percentiles with their windows, the
    # spread's three-month change, the 10-year's anchors) beside the items'
    # one-session change. It displaces nothing.
    from . import lens_cells                                     # noqa: PLC0415
    lt = lens_cells.lens_table(st, cutoff, list(keys))
    # BATCH 7 LENS 24 AND ITEM 46 (6e-releases, 16 Oct 2026): on a release's
    # day, one "what moved the print" line, code-written from the release's own
    # lens figures (altdata/releases.py), as a first-priority item -- the path
    # the close's existing narrative step already reads, under its existing
    # audits; no new model call. Any other day: nothing.
    rel = []
    try:
        from altdata import releases                             # noqa: PLC0415
        rel = releases.release_day_lines(st, cutoff)
    except Exception:                                           # noqa: BLE001
        rel = []              # report-only: a fault costs the line, never the section
    for x in rel:
        items.append(item(f"plumb:release:{x['release']}", x["line"], 1,
                          (x["release"], x["month"], x["line"])))
    return {"items": items, "deep_reason": reason,
            "charts": ["C3"] if reason else [],
            "not_tracked": ["repo-market stress (SOFR, general collateral)"],
            "subsections": [lt] if lt else [],
            "data": {"series": data, "release_lines": rel}}


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
        if k == "finra.short_interest_days_to_cover":
            x["dp"] = 2          # W8-8: the change to the level's two decimals
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
                                  + (f", {FLC}" if r.get("bias_zone") else "")
                                  + ").", 3, (v, r["probability"])))
            continue
        txt = "; ".join(
            f"{_venue_name(v)} {_pct(r['probability'])}"
            f" ({_pts(r.get('change_1s_points'))} on the session"
            + (f", {FLC}" if r.get("bias_zone") else "") + ")"
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


# THE FAVOURITE-LONGSHOT CHECK (W-1.1 item 1.5, ruled 11 Oct 2026): the rule once
# printed as "outside 10-90%" -- read as "mispriced" -- is a flag, not a verdict.
# Prediction markets tend to overprice longshots and underprice favourites, so a
# price this far from even is read for its change more than its level.
FLC = "favourite–longshot check: outside 10-90%"
BIAS_LEGEND = ("Favourite–longshot check (outside 10-90%): a flag, not a verdict -- "
               "prediction markets tend to overprice longshots and underprice "
               "favourites, so at odds this far from even read the change more than "
               "the level.")


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
    # PREDICTION MARKETS AS ONE TABLE (T2.5 item 9): the odds lines stay as the
    # section's data and change marks; the table is what prints. The bias note
    # is the table's own column, and the glossary explains it.
    from . import readability                                   # noqa: PLC0415
    pmt = readability.pm_table(pmb, "1s")
    for i in items:
        if i["key"].startswith(("priced:fomc", "priced:pm", "priced:outage")):
            i["show"] = False
    not_tracked += readability.pm_outages(pmb)
    subs = ([{"title": "Prediction markets", "table": pmt}] if pmt["rows"] else [])
    return {"items": items, "deep_reason": reason, "not_tracked": not_tracked,
            "legend": None, "subsections": subs,
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
        it = item(f"read:shock:{sh['instrument']}",
                  shock_sentence(sh, "in a session", sh["change_1s_points"]), 1,
                  (sh["probability"], sh["change_1s_points"]))
        # The move prints once, in What's priced's table (T2.5 item 1); here it
        # is The read's data.
        it["show"] = False
        out.append(it)
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
        # W8-3: one template, "the 9 December meeting" (the year when not this one).
        from . import readability                               # noqa: PLC0415
        from altdata import session as _session                 # noqa: PLC0415
        meeting = readability.meeting_name(day, _session.session_date_obj().year)
        year = str(d.year)
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
    # published, each sourced, from the voices the 06:15 scan stored. Fixed
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
        # THE MOVE SCREEN (Audit #4 Category 1 items 1 and 5): the stored result,
        # else computed in memory; the close never writes it.
        from altdata import move_screen                          # noqa: PLC0415
        screen = move_screen.result_for(st, p["session"], cutoff)
        built = {
            "read": {"items": read_items(pmb), "data": {
                "attention_shocks": (pmb or {}).get("shocks") or []}},
            "tape": tape_section(book),
            "mechanics": mechanics_section(p, dealer_blocks(p, st, cutoff, cfg),
                                           vol_event_for(p, st, cutoff),
                                           state_vectors(p, st)),
            "misfit": misfit_section(p, pmb, screen),
            "plumbing": plumbing_section(p, st, cutoff, cfg),
            "positioning": positioning_section(st, cutoff),
            "priced": priced_section(st, cutoff, cfg, pmb, fed, fed_prior),
            "narratives": narratives_section(st, p["session"], cutoff),
            "ahead": ahead_section(p, st, cutoff, outlook_rows),
            "book": book_section(p),
        }
        em_extras(built, screen, p["session"])
        # SIGNAL-TRIAGE BATCH 14, PART B1 (a57, 23 Oct 2026): item 65's speed-flag
        # attribution on a flag day and item 71's fragility panel, in Mechanics
        # (daily_cascade/batch14_b1_block.py; tables and lines only).
        from . import batch14_b1_block                          # noqa: PLC0415
        batch14_b1_block.close_extras(built, st, p["session"], cutoff, screen)
        # SIGNAL-TRIAGE BATCH 15 ITEM 73 (a58, 23 Oct 2026): the gold event's and
        # the developed-market drawdown's flag lines in the event area, on a
        # fired day only (daily_cascade/batch15_a_block.py; lines only).
        from . import batch15_a_block                           # noqa: PLC0415
        batch15_a_block.close_extras(built, st, p["session"], cutoff)
        # 6f TRANCHE 2 (a63): the dials' transition reads, one line.
        from . import state_v2_block                            # noqa: PLC0415
        state_v2_block.close_extras(built, st, cutoff)
        # D15 (b59, rulings of 24 Oct 2026): the one-day 10-year trigger's flag line
        # in the event area, on a trigger day only (daily_cascade/b59_block.py).
        from . import b59_block                                 # noqa: PLC0415
        b59_block.close_extras(built, st, p["session"], cutoff)
        # SIGNAL-TRIAGE BATCH 3, ST-B3-16: SR-32's early line on the tape --
        # nothing below 4.40%, one line approaching, the mechanism at 4.5%.
        from . import batch3_block                              # noqa: PLC0415
        built["tape"]["items"] += batch3_block.tape_items(st, cutoff)
        # SIGNAL-TRIAGE BATCH 6 item 40: the close carries the decomposition's
        # one-line read only, in What's priced.
        from . import index_carry_block                         # noqa: PLC0415
        if built.get("priced") is not None:
            built["priced"]["items"] += index_carry_block.close_items(st, cutoff)
        # SIGNAL-TRIAGE BATCH 6: the rates-transmission flag and quality tail in
        # Plumbing & rates, and the MBA line on the release Wednesday.
        from . import rates_transmission_block                  # noqa: PLC0415
        if built.get("plumbing") is not None:
            built["plumbing"]["items"] += rates_transmission_block.close_items(
                st, cutoff, p["session"])
        # SIGNAL-TRIAGE BATCH 12 item 59 (a53, 20 Oct 2026): the bank-stress flags
        # beside item 34's cluster, and the correction-vs-crisis classifier in The
        # read when it prints (KRE down more than 10% over 20 sessions).
        from . import bank_stress_block                         # noqa: PLC0415
        if built.get("plumbing") is not None:
            built["plumbing"]["items"] += bank_stress_block.close_items(st, cutoff)
        built["read"]["items"] += bank_stress_block.read_items(st, cutoff)
        # CD-9's daily part (the a47 chain, 19 Oct 2026): the crypto paragraph as
        # a Positioning & flows sub-section of data lines, which the word budget
        # does not count -- only while its switch is on.
        # BATCH 11 ITEM 55 (H6, registered 19 Oct 2026): one outcome line over the
        # session's level clusters in force, a Mechanics item (data, outside the
        # word budget; it displaces nothing).
        from altdata import level_clusters as _lc               # noqa: PLC0415
        if built.get("mechanics") is not None:
            try:
                with bars_mod.BarStore(store_path) as _bst:
                    _cl = _lc.close_item_text(st, _bst, p["session"], cutoff)
                if _cl:
                    built["mechanics"]["items"].append(item("mech:clusters", _cl, 3))
            except Exception:                                   # noqa: BLE001
                import logging                                  # noqa: PLC0415
                logging.getLogger(__name__).warning(
                    "the cluster outcome line faulted", exc_info=True)
        # BATCH 13 ITEM 61 (OS-12, D4; a54): what became of yesterday's flagged
        # volume -- the prior session's flags recomputed as of its close cutoff,
        # against OS-9's builds on the two sessions' captures. A Mechanics item
        # (data, outside the word budget); nothing when yesterday flagged nothing.
        if built.get("mechanics") is not None:
            try:
                from . import relative_volume as _rv            # noqa: PLC0415
                _prev = session.previous_trading_session(
                    dt.date.fromisoformat(str(p["session"])[:10])).isoformat()
                _ln = _rv.next_close_line(st, _prev, str(p["session"])[:10])
                if _ln:
                    built["mechanics"]["items"].append(item("mech:os12_outcome", _ln, 3))
            except Exception:                                   # noqa: BLE001
                import logging                                  # noqa: PLC0415
                logging.getLogger(__name__).warning(
                    "the OS-12 outcome line faulted", exc_info=True)
        from altdata import crypto_blocks                       # noqa: PLC0415
        if built.get("positioning") is not None and crypto_blocks.daily_enabled():
            built["positioning"].setdefault("subsections", []).append(
                crypto_blocks.daily_paragraph(st, cutoff))
    out = assemble(built, cfg, prior, "daily")
    return {"report": "daily_close_stack", "session": p["session"],
            "dealer_computed_dir": _dealer_chart_dir(p),
            "config_version": cfg.get("version"), "as_of": cutoff,
            "prior_session": (prior or {}).get("session"),
            "sections": out, "budget": (cfg.get("budget") or {}).get("daily")}


def em_extras(built: dict, screen: Optional[dict], day: str) -> None:
    """SR-46(c) and the EM calendar on the close: the report-only "EM leg" line
    in Plumbing & rates, and the quarter's hand-seeded EM events in Ahead."""
    from altdata import move_screen                              # noqa: PLC0415
    leg = ((screen or {}).get("em") or {}).get("em_leg_line")
    if leg and built.get("plumbing") is not None:
        built["plumbing"]["items"].append(item("plumb:em_leg", leg, 2, leg))
    for e in move_screen.em_calendar(day):
        if built.get("ahead") is not None:
            ln = move_screen.calendar_line(e)
            built["ahead"]["items"].append(item(f"ahead:em:{e.get('date')}:"
                                                f"{e.get('country')}", ln, 2, ln))


def section_ids(cfg: dict, cadence: str, built: Optional[dict] = None) -> list[str]:
    """The sections assemble() lays out at `cadence`, in config order (T2.7).

    The ten (SECTION_ORDER) always, each at its declared depth or "light". A
    section that exists at ONE CADENCE ONLY -- the Monthly's Reading chapter
    declares a `monthly` depth and no other -- is skipped at every cadence that
    declares no depth for it, and at its own cadence too unless the caller built
    it (the Monthly builds Reading after assembly, from the register, and places
    it itself). A section missing from config is a code fault: KeyError."""
    specs = [s for s in cfg.get("sections") or []]
    have = {s["id"] for s in specs}
    missing = [sid for sid in SECTION_ORDER if sid not in have]
    if missing:
        raise KeyError(f"config sections lack {missing}")
    out = []
    for sp in specs:
        sid = sp["id"]
        if sid in SECTION_ORDER:
            out.append(sid)
        elif sp.get(cadence) and built is not None and sid in built:
            out.append(sid)
    return out


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
    for sid in section_ids(cfg, cadence, built):
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
                 + [b.get("table")] + list(b.get("tables") or []))
        unchanged = bool(prior) and pr.get("fingerprint") == fp and sid != "read"
        out.append({"id": sid, "title": sp["title"],
                    "subtitle": sp.get("subtitle"), "depth": depth,
                    "depth_reason": (reason if depth == "deep" and sp.get(deep_key)
                                     else None),
                    "items": b["items"], "table": b.get("table"),
                    # A section's further tables (VP-1: the close's value-area
                    # table beside the returns), printed after its table.
                    "tables": b.get("tables") or [],
                    "charts": b.get("charts") or [], "data": b.get("data") or {},
                    "not_tracked": b.get("not_tracked") or [],
                    "legend": b.get("legend"),
                    # T2.2: a section may print its lines as data beside a table
                    # (print_items False), carry a note above its table, and hold
                    # sub-sections, each with its own table and one paragraph.
                    "print_items": b.get("print_items", True),
                    "prose_paragraphs": b.get("prose_paragraphs"),
                    "lead_paragraphs": b.get("lead_paragraphs"),
                    "table_note": b.get("table_note"),
                    "subsections": b.get("subsections") or [],
                    "fingerprint": fp, "collapsed": unchanged,
                    "unchanged_since": ((pr.get("unchanged_since") or
                                         (prior or {}).get("session"))
                                        if unchanged else None),
                    "prior_claim": pr.get("claim") if unchanged else None,
                    "claim": None, "paragraphs": [], "trimmed": False})
    # EMPTY MEANS ONE LINE (T2.5 item 5): marked here, so the prose skips the
    # section and the renderer prints its footnote alone. The period noun is the
    # cadence's (config `cadences:`), so "Nothing new this month" is written as
    # such rather than rewritten from the Weekly's.
    from . import readability                                   # noqa: PLC0415
    from . import cadence as cadence_mod                        # noqa: PLC0415
    period = cadence_mod.get(cadence, cfg)["period"]
    for s in out:
        s["period"] = period
    readability.mark_empty(out, period)
    return out


def words(text: Optional[str]) -> int:
    return len(re.findall(r"[\w'.%$−+-]+", text or ""))


def section_words(s: dict) -> int:
    """PROSE ONLY (T2.2, 4 Oct 2026, every report): the claim line, the
    paragraphs and each sub-section's paragraphs -- the Monthly's sub-sections
    keep theirs (`paragraphs`), the close's and the Weekly's keep none. Items,
    lines and tables are data and never count. One function for every cadence
    (T2.6); a detail block (the Monthly's) is counted the same way."""
    if s.get("collapsed"):
        return words(s.get("claim"))
    n = words(s.get("claim")) + sum(words(x) for x in s.get("paragraphs") or [])
    for ss in s.get("subsections") or []:
        n += words(ss.get("paragraph")) + sum(words(x) for x in ss.get("paragraphs") or [])
        # A sub-section's LEAD (ST-R6.45d: the ES block's read) counts when it
        # is model prose; a withheld or absent note in its place is not.
        if ss.get("lead_prose"):
            n += words(ss.get("lead"))
    return n


def edition_words(ed: dict) -> int:
    """The edition's prose: every section, and every detail block after them,
    and an executive summary where the edition carries one (the Monthly's,
    T3.1 item 20 -- it is prose and counts in the budget)."""
    return (sum(section_words(s) for s in ed.get("sections") or [])
            + sum(section_words(d) for d in ed.get("detail") or [])
            + sum(words(x.get("text")) for x in ed.get("summary") or []))


def enforce_budget(ed: dict, cadence: str = "daily") -> dict:
    """THE GUARD (T2.5 item 2; per cadence, T2.6), as D19/D20 left it (24 Oct
    2026: budgets are targets, never caps). The paragraph guard drops empty
    paragraphs and cuts nothing for length; a sentence that repeats The read is
    withheld where it repeats it (item 4: repetition, not length). Then the
    edition's reading time is read against its cadence's target, and over it the
    edition carries one foot line (`target_line`). Nothing is cut or withheld to
    fit; a claim line, an item and a table are data and never touched."""
    from . import readability                                   # noqa: PLC0415
    from . import cadence as cadence_mod                        # noqa: PLC0415
    readability.finalize(ed, cadence)
    readability.withhold_duplicates(ed)
    cad = cadence_mod.get(cadence)
    ed["words"] = edition_words(ed)
    if ed.get("reading_target_minutes") is None:
        ed["reading_target_minutes"] = cad.get("reading_target_minutes")
    # The Quarterly's target is its READ's, warned on by quarterly.read_warning;
    # its reference is unbudgeted, so the whole edition is not read against it.
    ed["target_line"] = None if cad.get("read_budget") else target_line(ed)
    return ed


def target_line(ed: dict) -> Optional[str]:
    """D20's one foot line when the edition runs over its reading target, else
    None: "This edition runs about N minutes against a T-minute target." The
    minutes are the shared estimate (readability.reading_minutes)."""
    from . import readability                                   # noqa: PLC0415
    t = ed.get("reading_target_minutes")
    if not t:
        return None
    n = readability.reading_minutes(ed)
    if n <= int(t):
        return None
    return f"This edition runs about {n} minutes against a {int(t)}-minute target."


def chart_plan(ed: dict, available: dict[str, Optional[str]]) -> list[str]:
    """Which charts this edition carries, by the brief's rule (3.2), within the
    cap (1.4); a fired trigger lifts the cap by one (1.1)."""
    cap = int((ed.get("budget") or {}).get("charts") or 3)
    fired = any(s.get("depth_reason") for s in ed["sections"])
    cap += 1 if fired else 0
    want = ["C1", "C2"]
    misfit = next(s for s in ed["sections"] if s["id"] == "misfit")
    plumb = next(s for s in ed["sections"] if s["id"] == "plumbing")
    c3 = bool((misfit.get("data") or {}).get("open_contradictions")
              or plumb.get("depth") == "deep")
    if c3:
        want.append("C3")
    # D2, THE CLOSE'S ONE DEALER CHART (6b part 2; brief v2 section 3), when the
    # edition reads the computed profiles: after C1 and any C3, before C2. On a
    # day with C3 and no fired trigger, C2 is the one set aside.
    if ed.get("dealer_computed_dir"):
        want = ["C1"] + (["C3"] if c3 else []) + ["D2", "C2"]
    return [c for c in want][:cap]
