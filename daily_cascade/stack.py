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

THE BUDGET (1.4). Words are counted over the claim lines, paragraphs and items;
over budget, the lowest-priority items go first, then the later paragraphs of
deep sections, and the section prints "(trimmed)". The model never summarizes to
fit.
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
    mag = f"{abs(v):,.2f}" if unit == "%" else f"{abs(v):,.1f}"
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
        ch = round((lv - pv) * (1.0 if units in ("bps", "bp") else 100.0), 1)
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


def misfit_section(p: dict) -> dict:
    ms = p.get("market_state") or {}
    items = []
    opened = [c for c in ms.get("contradictions") or [] if c.get("open")]
    for c in opened:
        items.append(item(f"misfit:{c['id']}",
                          f"{c['id']}: open {c.get('persistence_days')} session(s), "
                          f"z {c.get('magnitude')} against a threshold of "
                          f"{c.get('threshold_z')}.", 1,
                          (c.get("persistence_days"), c.get("magnitude"))))
    exc = ms.get("exceptions") or []
    if exc:
        items.append(item("misfit:exceptions",
                          f"{len(exc)} exception(s) open: "
                          + ", ".join(str(e.get("id")) for e in exc[:4])
                          + ("…" if len(exc) > 4 else "") + ".", 2,
                          sorted(str(e.get("id")) for e in exc)))
    if not items:
        items.append(item("misfit:none", "No contradiction is open and no "
                          "exception is flagged.", 1, "none"))
    return {"items": items, "charts": ["C3"] if opened else [],
            "not_tracked": ["venue-against-price disagreement (prediction "
                            "markets, 6d)"],
            "data": {"open_contradictions_count": len(opened),
                     "exceptions_count": len(exc),
                     "exceptions_by_kind": {k: sum(1 for e in exc
                                                   if e.get("kind") == k)
                                            for k in ("extreme", "contradiction")},
                     "open_contradictions": [{**{k: c.get(k) for k in
                                                 ("id", "legs", "magnitude",
                                                  "threshold_z", "persistence_days",
                                                  "since")},
                                              "excess_over_threshold_z": (
                                                  round(abs(c["magnitude"])
                                                        - abs(c["threshold_z"]), 2)
                                                  if isinstance(c.get("magnitude"),
                                                                (int, float))
                                                  and c.get("threshold_z")
                                                  else None)} for c in opened],
                     "exceptions": [{k: e.get(k) for k in ("id", "kind", "what",
                                                           "value")}
                                    for e in exc]}}


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


def priced_section(st, cutoff: str, cfg: dict) -> dict:
    items, data = [], {}
    for k, name in (("fred.breakeven_10y", "10-year breakeven"),
                    ("fred.breakeven_5y5y", "5-year, 5-year-forward breakeven"),
                    ("umich.expect_5_10y", "Michigan 5-10 year expectations"),
                    ("nyfed.sce_3y", "NY Fed 3-year expectations")):
        x = last_two(st, k, cutoff)
        if not x:
            continue
        data[name] = x
        items.append(item(f"priced:{k}", f"{name} {_lvl(x)} ({_change(x)}, as of "
                          f"{x['observed_at']}).", 2, (x["level"], x["change"])))
    reason = None
    for k, th in (((cfg.get("triggers") or {}).get("priced") or {})
                  .get("moves_bp") or {}).items():
        x = last_two(st, k, cutoff)
        if x and x.get("change") is not None and abs(x["change"]) >= th:
            reason = f"{k.split('.')[-1]} moved {_change(x)} (threshold {th} bp)"
            break
    return {"items": items, "deep_reason": reason,
            "not_tracked": ["the fed funds futures rate path (6d)",
                            "prediction-market odds (6d)",
                            "one-year inflation expectations"],
            "data": {"series": data}}


def narratives_section(st) -> dict:
    try:
        from altdata import narratives                         # noqa: PLC0415
        with narratives.NarrativeRegister(str(st.path)) as reg:
            rows = reg.all("active")
    except Exception:                                           # noqa: BLE001
        rows = []
    if not rows:
        return {"items": [item("narr:none", "No story is active in the register.",
                               1, "none")], "data": {}}
    states = {}
    for r in rows:
        states.setdefault(r["state"], []).append(r["name"])
    text = "; ".join(f"{s}: {', '.join(n)}" for s, n in sorted(states.items()))
    return {"items": [item("narr:states", f"Stories — {text}.", 1, states)],
            "data": {"stories": [{"story": r["name"], "state": r["state"]}
                                 for r in rows]}}


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
                             f"{round(o['probability'] * 100):.0f}% that {o['claim']}; "
                             f"resolved {o['horizon_date']} (base rate, n={o['n']}; "
                             + (f"ledger {str(o['ledger_id'])[:12]})."
                                if not str(o["ledger_id"]).startswith("dry-run")
                                else "not recorded: dry run)."), 1,
                             (o["probability"], o["claim"])))
    return {"items": items[:9],
            "data": {"events": [i["text"] for i in items if "outlook" not in i["key"]],
                     "outlooks": [{k: o.get(k) for k in
                                   ("id", "claim", "probability", "n",
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
def build(p: dict, book: dict, outlook_rows: list[dict],
          prior: Optional[dict] = None, store_path: Optional[str] = None) -> dict:
    cfg = config()
    cutoff = p.get("as_of") or session.utc_iso()
    with observations.ObservationStore(store_path) as st:
        built = {
            "read": {"items": [], "data": {}},
            "tape": tape_section(book),
            "mechanics": mechanics_section(p),
            "misfit": misfit_section(p),
            "plumbing": plumbing_section(p, st, cutoff, cfg),
            "positioning": positioning_section(st, cutoff),
            "priced": priced_section(st, cutoff, cfg),
            "narratives": narratives_section(st),
            "ahead": ahead_section(p, st, cutoff, outlook_rows),
            "book": book_section(p),
        }
    specs = {s["id"]: s for s in cfg.get("sections") or []}
    prior_secs = {s["id"]: s for s in (prior or {}).get("sections") or []}
    out = []
    for sid in SECTION_ORDER:
        sp, b = specs[sid], built[sid]
        depth = sp.get("daily") or "light"
        reason = b.get("deep_reason")
        if sp.get("deep_on") and reason:
            depth = "deep"
        pr = prior_secs.get(sid) or {}
        pmarks = {i["key"]: i["fingerprint"] for i in pr.get("items") or []}
        for it in b["items"]:
            it["changed"] = bool(prior) and pmarks.get(it["key"]) != it["fingerprint"]
        fp = _fp([(i["key"], i["fingerprint"]) for i in b["items"]]
                 + [b.get("table")])
        unchanged = bool(prior) and pr.get("fingerprint") == fp and sid != "read"
        out.append({"id": sid, "title": sp["title"], "depth": depth,
                    "depth_reason": (reason if depth == "deep" and sp.get("deep_on")
                                     else None),
                    "items": b["items"], "table": b.get("table"),
                    "charts": b.get("charts") or [], "data": b.get("data") or {},
                    "not_tracked": b.get("not_tracked") or [],
                    "fingerprint": fp, "collapsed": unchanged,
                    "unchanged_since": ((pr.get("unchanged_since") or
                                         (prior or {}).get("session"))
                                        if unchanged else None),
                    "prior_claim": pr.get("claim") if unchanged else None,
                    "claim": None, "paragraphs": [], "trimmed": False})
    return {"report": "daily_close_stack", "session": p["session"],
            "config_version": cfg.get("version"), "as_of": cutoff,
            "prior_session": (prior or {}).get("session"),
            "sections": out, "budget": (cfg.get("budget") or {}).get("daily")}


def words(text: Optional[str]) -> int:
    return len(re.findall(r"[\w'.%$−+-]+", text or ""))


def section_words(s: dict) -> int:
    if s.get("collapsed"):
        return words(s.get("claim"))
    return (words(s.get("claim")) + sum(words(x) for x in s.get("paragraphs") or [])
            + sum(words(i["text"]) for i in s.get("items") or []))


def enforce_budget(ed: dict) -> dict:
    """Trim to the word budget, lowest priority first; mark what was cut."""
    limit = int((ed.get("budget") or {}).get("words") or 1000)
    total = lambda: sum(section_words(s) for s in ed["sections"])  # noqa: E731
    cands = sorted(((i["priority"], n, i["key"])
                    for n, s in enumerate(ed["sections"]) if not s["collapsed"]
                    for i in s["items"] if i["priority"] >= 2), reverse=True)
    for _, n, key in cands:
        if total() <= limit:
            break
        s = ed["sections"][n]
        s["items"] = [i for i in s["items"] if i["key"] != key]
        s["trimmed"] = True
    for s in reversed(ed["sections"]):
        while total() > limit and len(s.get("paragraphs") or []) > 1:
            s["paragraphs"] = s["paragraphs"][:-1]
            s["trimmed"] = True
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
