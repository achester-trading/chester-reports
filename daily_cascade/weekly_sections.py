"""
The Weekly's sections as edited after the first live edition. (T2.2, ruled 4 Oct
2026, seventeen items; the brief's 1.3, 2.2 and 3.1-3.3.)

    from daily_cascade import weekly_sections as wsec

DATA AND FIXED SENTENCES ONLY, like the rest of the stack: tables, the lines
beside them, the flags and the calendar are computed here from the store, the
register, the ledger and config; the model writes the claim and the paragraphs
over them (stack_prose.py), and may describe a flag, a state or a gap only in the
words this module and config/display_labels.yaml give it.

What each builder answers:
  week_by_day      The read: per session, SPY's and the 10-year's moves, the
                   tier-1 release with actual and prior, the Fed speech or
                   auction, the day's most-cited story with its source, and the
                   press's own attributions, each with its URL (item 3)
  tape_table       one table for the nine markets (item 4)
  dealer_week      the dealer scorecard table and its code-derived flags (item 18)
  gap_table        What doesn't fit's open gaps, with how to read them (item 5)
  calendar_week    Ahead's day-by-day calendar from the events table and
                   config/release_calendar.yaml (item 10)
  watching         "What the system is watching" (item 10)
"""

from __future__ import annotations

import datetime as dt
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Optional

import yaml

from altdata import derived, session

REPO = Path(__file__).resolve().parent.parent
CALENDAR_PATH = REPO / "config" / "release_calendar.yaml"

NUMBER_WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven",
                "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
                "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]


def in_words(n: Optional[int]) -> str:
    """Counts in words (item 9): 'nine', 'none' is the caller's; past twenty,
    digits."""
    if n is None:
        return "no"
    return NUMBER_WORDS[n] if 0 <= n < len(NUMBER_WORDS) else f"{n:,}"


def _signed(v: Optional[float], unit: str) -> str:
    from .stack import _signed as s                             # noqa: PLC0415
    return s(v, unit)


def _day(d: str) -> str:
    x = dt.date.fromisoformat(d[:10])
    return f"{x:%a} {x.day} {x:%b}"


# ---------------------------------------------------------------------------
# The read: the week by day (item 3)
# ---------------------------------------------------------------------------
def _closes(spec_id: str, ending: str, now: str, st) -> dict[str, float]:
    from altdata import levels                                  # noqa: PLC0415
    rows, _ = levels.daily_bars(levels.tape_spec(spec_id), ending, now, st)
    return {str(r["observed_at"])[:10]: r["close"] for r in rows}


def _fed_or_auction(st, day: str, now: str) -> list[str]:
    out = []
    try:
        from altdata import events                              # noqa: PLC0415
        with events.EventStore(str(st.path)) as ev:
            rows = ev.conn.execute(
                "SELECT title, source, payload FROM events WHERE "
                "substr(observed_at, 1, 10) = ? AND available_at <= ? AND ("
                "source = 'fed_calendar' OR (type = 'release' AND source IN "
                "('fed_press', 'fed_monetary'))) ORDER BY observed_at",
                (day, now)).fetchall()
        for title, src, payload in rows:
            t = str(title)
            if src == "fed_calendar":
                p = json.loads(payload or "{}")
                if p.get("kind") in ("Speeches", "Testimony"):
                    kind = "speech" if p.get("kind") == "Speeches" else "testimony"
                    out.append(f"{p.get('speaker') or t.split(' -- ')[0]} ({kind})")
            elif re.search(r"\b(speech|testimony|remarks)\b", t, re.I):
                out.append(t.split(" -- ")[0][:80])
    except Exception:                                           # noqa: BLE001
        pass
    for r in coupon_auctions(st, now):
        inst = str(r.get("instrument") or "")
        if str(r["observed_at"])[:10] == day and inst.split(":")[0] in ("Note", "Bond"):
            out.append(f"{inst.split(':')[1].lower()} {inst.split(':')[0].lower()} "
                       f"auction, high yield {r['value_num']:.3f}%")
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def week_by_day(st, sessions: list[str], ending: str, now: str, then: str,
                releases: list[dict], db_path: Optional[str] = None) -> dict:
    """Item 3. One row per session. Every cell is a stored figure or a sourced
    item; the press's explanations are ITS attributions, with URLs."""
    from altdata import labels, voices as vmod                  # noqa: PLC0415
    spy = _closes("spy", ending, now, st)
    tnx = _closes("y10", ending, now, st)
    days = sorted(set(sessions)) or sorted(d for d in spy if then[:10] < d <= ending)

    def move(series: dict, d: str, bp: bool) -> Optional[float]:
        prior = [k for k in series if k < d]
        if d not in series or not prior:
            return None
        a, b = series[d], series[max(prior)]
        return round((a - b) * 100.0) if bp else round(100.0 * (a / b - 1.0), 2)
    rel_by: dict[str, list[str]] = {}
    for r in releases:
        rel_by.setdefault(r["date"], []).append(
            f"{r['label']} {r['actual_text']} (prior {r['prior_text']})")
    with vmod.VoicesStore(db_path, readonly=True) as vs:
        ev = vs.evidence(as_of=now, since=then[:10])
        attrs = vs.attributions(as_of=now, since=then[:10])
    rows, data, lines = [], [], []
    for d in days:
        e = [x for x in ev if str(x["published_at"])[:10] == d]
        story = None
        if e:
            top, n = sorted(Counter(x["narrative_id"] for x in e).items(),
                            key=lambda kv: (-kv[1], kv[0]))[0]
            src = next(x for x in e if x["narrative_id"] == top)
            title = labels.story(top).get("title") or top.replace("_", " ")
            story = f"{title}, {in_words(n)} item{'s' if n != 1 else ''} " \
                    f"({src['outlet']}, {src['source_url']})"
        fed = _fed_or_auction(st, d, now)
        rs, ty = move(spy, d, False), move(tnx, d, True)
        row = [_day(d), _signed(rs, "%") if rs is not None else "—",
               _signed(ty, "bp") if ty is not None else "—",
               "; ".join(rel_by.get(d) or []) or "—",
               "; ".join(fed) or "—", story or "—"]
        rows.append(row)
        data.append({"day": d, "spy_pct": rs, "ten_year_bp": ty,
                     "releases": rel_by.get(d) or [], "fed_or_auction": fed,
                     "most_cited_story": story})
        for a in attrs:
            if str(a["published_at"])[:10] == d:
                lines.append(f"{_day(d)}: {a['outlet']} attributed the move in "
                             f"{a['market']} to {a['claim'].rstrip('.')} "
                             f"({a['source_url']}).")
    return {"table": {"columns": ["Day", "SPY", "10-year", "Tier-1 release "
                                  "(actual, prior)", "Fed speech or auction",
                                  "Most-cited story (source)"], "rows": rows},
            "data": data, "attributions": lines}


# ---------------------------------------------------------------------------
# The tape: one table (item 4)
# ---------------------------------------------------------------------------
def tape_table(book: dict) -> dict:
    cols = ["Market", "Last", "Session", "Week", "Month", "YTD", "Week high / low",
            "52-week high (distance)", "vs 20 / 50 / 200-day", "Gamma flip"]
    rows, gaps = [], []
    # THE MOBILE RULE (T2.3 item 8): no table wider than six columns -- the
    # returns table (6) and the levels table (5) are split below.
    for i in book.get("instruments") or []:
        f = i.get("frame") or {}
        y = i["kind"] == "yield"
        unit = "bp" if y else "%"
        k = "bps" if y else "pct"
        last = f.get("last")
        if last is None:
            gaps.append(f"{i['label']}: no daily bar for the session")
            continue
        lv = {x["type"]: x["value"] for x in i.get("levels") or []}

        def dist(level: Optional[float]) -> str:
            if level is None:
                return "—"
            v = (last - level) * 100.0 if y else 100.0 * (last / level - 1.0)
            return _signed(round(v) if y else round(v, 2), unit)
        fmt = (lambda v: f"{v:,.3f}%") if y else (lambda v: f"{v:,.2f}")
        hl = (f"{fmt(lv['week_high'])} / {fmt(lv['week_low'])}"
              if lv.get("week_high") is not None else "—")
        h52 = (f"{fmt(lv['high_52w'])} ({dist(lv['high_52w'])})"
               if lv.get("high_52w") is not None else "—")
        mas = " / ".join(dist(lv.get(m)) for m in ("ma_20d", "ma_50d", "ma_200d"))
        rows.append([i["label"], fmt(last), _signed(f.get(f"session_change_{k}"), unit),
                     _signed(f.get(f"wtd_change_{k}"), unit),
                     _signed(f.get(f"mtd_change_{k}"), unit),
                     _signed(f.get(f"ytd_change_{k}"), unit), hl, h52, mas,
                     fmt(lv["gamma_flip"]) if lv.get("gamma_flip") is not None else "—"])
    ret = {"columns": cols[:6], "rows": [r[:6] for r in rows]}
    lev = {"columns": [cols[0]] + cols[6:], "rows": [[r[0]] + r[6:] for r in rows]}
    return {"table": ret, "levels_table": lev, "not_tracked": gaps}


# ---------------------------------------------------------------------------
# Mechanics: the dealer scorecard and its flags (item 18)
# ---------------------------------------------------------------------------
def _within(a: Optional[float], b: Optional[float], pct: float) -> bool:
    return a is not None and b not in (None, 0) and abs(a / b - 1.0) * 100.0 <= pct


def flags_for(card: dict, vix: Optional[float], cfg: dict) -> dict:
    """The code-derived flags (item 18). Each is True, False, or None when a
    field it needs is not stored -- never guessed. The implied range uses SPY's
    own ATM 30-day IV when the card carries it, else the VIX, labelled "VIX as
    proxy" (rulings of 5 Oct)."""
    fc = cfg.get("dealer_flags") or {}
    pin_pct = float(fc.get("pinned_pct", 0.25))
    wall_pct = float(fc.get("wall_pct", 0.25))
    ratio = float(fc.get("amplified_range_ratio", 1.2))
    close, hi, lo = card.get("close"), card.get("session_high"), card.get("session_low")
    spot = card.get("prior_close") or close
    own_iv = card.get("atm_iv_30d")
    iv = own_iv if own_iv else vix
    implied = (spot * (iv / 100.0) * math.sqrt(1.0 / 252.0)
               if spot and iv else None)
    actual = (hi - lo) if None not in (hi, lo) else None
    cw = card.get("call_wall_morning") or card.get("call_wall")
    pw = card.get("put_wall_morning") or card.get("put_wall")
    mp = card.get("max_pain")
    out = {"implied_range": round(implied, 2) if implied else None,
           "iv_source": ("SPY ATM 30-day IV" if own_iv else
                         "VIX as proxy" if vix else None),
           "actual_range": round(actual, 2) if actual is not None else None,
           "pinned": (None if close is None or mp is None
                      else _within(close, mp, pin_pct)),
           "call_wall_held": (None if None in (hi, close, cw) else
                              _within(hi, cw, wall_pct) and close < cw),
           "put_wall_held": (None if None in (lo, close, pw) else
                             _within(lo, pw, wall_pct) and close > pw),
           "amplified": (None if card.get("flip_crossed") is None or not implied
                         or actual is None else
                         bool(card["flip_crossed"]) and actual >= ratio * implied)}
    flip = card.get("flip_morning")
    out["close_vs_flip"] = (None if None in (close, flip) else
                            ("above" if close > flip else "below"))
    # THE IV CHECK (PB-1): SPY's own ATM IV and the VIX more than the declared
    # gap apart -- both print and the row is marked "check"; neither is chosen.
    gap = float((cfg.get("dealer_flags") or {}).get("iv_vix_check_points", 5.0))
    out["iv_check"] = bool(own_iv and vix and abs(own_iv - vix) > gap)
    out["spy_iv"], out["vix"] = own_iv, vix
    return out


def dealer_week(st, sessions: list[str], cutoff: str, cfg: dict) -> dict:
    cards = []
    for s in sessions:
        rows = [x for x in st.as_of("dealer.scorecard_day", cutoff, "SPY")
                if str(x["observed_at"])[:10] == s]
        if rows:
            try:
                cards.append(json.loads(rows[-1]["value_text"]))
            except (TypeError, ValueError):
                pass
    vix_key = (cfg.get("dealer_flags") or {}).get("implied_vol_key") or "yfinance.mkt_vix"
    vix = {str(r["observed_at"])[:10]: r["value_num"] for r in st.as_of(vix_key, cutoff)
           if r.get("value_num") is not None}

    def g(v, fmt="{:,.2f}"):
        return "—" if v is None else fmt.format(v)

    def bn(v):
        return "—" if v is None else f"{v / 1e9:+,.2f}bn"

    def yn(v):
        return "—" if v is None else ("yes" if v else "no")
    rows, scored = [], []
    for c in cards:
        f = flags_for(c, vix.get(str(c.get("session"))[:10]), cfg)
        set_flags = [n for n, k in (("pinned", "pinned"), ("call wall held",
                                     "call_wall_held"), ("put wall held",
                                                         "put_wall_held"),
                                    ("amplified", "amplified")) if f.get(k)]
        rows.append([_day(c["session"]), c.get("gamma_regime") or "—",
                     bn(c.get("net_gex_close")),
                     bn(c.get("dex_close")),
                     g(c.get("flip_morning")),
                     f"{g(c.get('call_wall_morning') or c.get('call_wall'))} / "
                     f"{g(c.get('put_wall_morning') or c.get('put_wall'))}",
                     # -- the second table from here
                     _day(c["session"]), g(c.get("max_pain")),
                     (g(f["implied_range"])
                      + (f" (SPY IV {f['spy_iv']:.1f}, VIX {f['vix']:.1f}: check)"
                         if f.get("iv_check") else
                         " (VIX as proxy)" if f.get("iv_source") == "VIX as proxy"
                         else "")),
                     g(f["actual_range"]),
                     f["close_vs_flip"] or "—",
                     ", ".join(set_flags + (["check"] if f.get("iv_check") else []))
                     or "none"])
        scored.append({"session": c["session"], "flags": {k: f[k] for k in
                       ("pinned", "call_wall_held", "put_wall_held", "amplified")},
                       "implied_range": f["implied_range"],
                       "actual_range": f["actual_range"],
                       "close_vs_flip": f["close_vs_flip"],
                       "gamma_regime": c.get("gamma_regime")})
    # TWO TABLES OF SIX (T2.3 mobile rule): the profile, then the ranges.
    return {"table": {"columns": ["Session", "Gamma regime", "Net GEX", "DEX",
                                  "Flip", "Call / put wall"],
                      "rows": [r[:6] for r in rows]},
            "ranges_table": {"columns": ["Session", "Max pain", "Implied range",
                                         "Actual range", "Close vs flip", "Flags"],
                             "rows": [r[6:] for r in rows]},
            "table_note": ("SPY. Walls and flip as of each morning; implied one-day "
                           "range = prior close × SPY's at-the-money 30-day IV "
                           "(from our own chain) × √(1/252), or the VIX where that "
                           "is not stored, marked 'VIX as proxy'; flags are "
                           "computed: pinned = close within "
                           f"{(cfg.get('dealer_flags') or {}).get('pinned_pct', 0.25)}% "
                           "of max pain; a wall held = the session's high (low) "
                           "within "
                           f"{(cfg.get('dealer_flags') or {}).get('wall_pct', 0.25)}% "
                           "of it and the close inside; amplified = the flip "
                           "crossed and the actual range at least "
                           f"{(cfg.get('dealer_flags') or {}).get('amplified_range_ratio', 1.2)}"
                           "× the implied."),
            "data": {"sessions": scored}, "cards": cards}


# ---------------------------------------------------------------------------
# What doesn't fit: the gap table (item 5)
# ---------------------------------------------------------------------------
GAP_NOTE = ("How to read: z is how unusual today's distance between the two "
            "markets is against the pair's own history; 2.0 means further apart "
            "than 95% of the time. Rising means the gap is widening, falling that "
            "it is closing; the count is the sessions it has been open.")


def gap_table(opened: list[dict], history: dict[str, list]) -> dict:
    from altdata import labels                                  # noqa: PLC0415
    rows, data = [], []
    for c in opened:
        cid = c.get("id")
        plain = labels.contradiction_plain(cid)
        h = history.get(cid) or []
        trend = "—"
        if len(h) >= 2 and None not in (h[-1][1], h[-2][1]):
            trend = "rising" if abs(h[-1][1]) > abs(h[-2][1]) else "falling"
        z = c.get("magnitude")
        rows.append([labels.contradiction(cid).capitalize(), plain.get("legs") or "—",
                     (f"{float(z):+.1f} (line {float(c.get('threshold_z') or 2.0):.1f})"
                      if isinstance(z, (int, float)) else "—"), trend,
                     c.get("persistence_days"), plain.get("closes") or "—"])
        data.append({"gap": labels.contradiction(cid), "sides": plain.get("legs"),
                     "z": round(float(z), 1) if isinstance(z, (int, float)) else None,
                     "direction": trend, "sessions_open": c.get("persistence_days"),
                     "closes_when": plain.get("closes")})
    return {"table": {"columns": ["Gap", "What each side is saying", "z (line)",
                                  "Direction", "Sessions open", "What would close it"],
                      "rows": rows},
            "table_note": GAP_NOTE, "data": data}


# ---------------------------------------------------------------------------
# Ahead: the day-by-day calendar (item 10)
# ---------------------------------------------------------------------------
def load_calendar(path: Optional[Path] = None) -> dict:
    with open(path or CALENDAR_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def canonical_auction(inst: str) -> str:
    """'Note:9-Year 10-Month' -> 'Note:10-Year': a reopening is named by the
    security it reopens, as the auction results are stored."""
    typ, _, term = inst.partition(":")
    m = re.match(r"(\d+)-Year(?:\s+(\d+)-Month)?", term)
    if m and m.group(2):
        return f"{typ}:{int(m.group(1)) + 1}-Year"
    return inst


def match_release(title: str, cal: dict) -> Optional[dict]:
    for r in cal.get("releases") or []:
        if str(r["match"]).lower() in str(title).lower():
            return r
    return None


def _et(iso: str) -> Optional[str]:
    try:
        t = session.to_eastern(dt.datetime.fromisoformat(iso.replace("Z", "+00:00")))
        return t.strftime("%H:%M")
    except (ValueError, TypeError):
        return None


def calendar_week(st, ending: str, now: str, pmb: Optional[dict] = None,
                  cal: Optional[dict] = None) -> dict:
    """The coming week, Monday to Friday after `ending`, one row per event:
    day, time ET, event, importance, consensus or prior."""
    from altdata import events                                  # noqa: PLC0415
    cal = cal or load_calendar()
    end = dt.date.fromisoformat(ending[:10])
    mon = end + dt.timedelta(days=(7 - end.weekday()) % 7 or 7)
    sat = mon + dt.timedelta(days=5)
    rows: list[dict] = []
    skipped = 0
    with events.EventStore(str(st.path)) as ev:
        recs = ev.conn.execute(
            "SELECT type, source, observed_at, title, payload FROM events WHERE "
            "type IN ('scheduled', 'session_event', 'earnings') AND observed_at >= ? "
            "AND observed_at < ? AND available_at <= ? ORDER BY observed_at",
            (mon.isoformat(), sat.isoformat(), now)).fetchall()
    for typ, src, obs, title, payload in recs:
        p = json.loads(payload or "{}")
        d = str(obs)[:10]
        t = str(title)
        if src == "fed_calendar":
            kind = p.get("kind")
            chair = "Chair" in t and "Vice" not in t
            rows.append({"date": d, "time": p.get("time_et") or "time not stated",
                         "event": (f"{p.get('speaker')}: {t.split(' -- ')[-1]}"
                                   if kind != "FOMC Meetings" else "FOMC meeting"),
                         "tier": 1 if kind == "FOMC Meetings" else (2 if chair else 3),
                         "consensus": "—"})
            continue
        if src == "treasury_upcoming":
            inst = canonical_auction(str(p.get("instrument") or ""))
            if inst.split(":")[0] not in ("Note", "Bond", "TIPS"):
                skipped += 1
                continue
            m = match_release(inst, cal)
            hy = st.latest_as_of("auction.high_yield", now, inst)
            bc = st.latest_as_of("auction.bid_to_cover", now, inst)
            prior = (f"prior {inst.split(':')[1].lower()}: high yield "
                     f"{hy['value_num']:.3f}%"
                     + (f", bid-to-cover {bc['value_num']:.2f}" if bc else "")
                     + f" ({str(hy['observed_at'])[:10]}); tail not stored"
                     if hy else "no prior auction stored")
            rows.append({"date": d, "time": (m or {}).get("time") or "13:00",
                         "event": (m or {}).get("label") or
                         f"{inst.split(':')[1]} {inst.split(':')[0].lower()} auction",
                         "tier": (m or {}).get("tier") or 3, "consensus": prior})
            continue
        if typ == "session_event":
            if not re.search(r"OPEX|expir", t, re.I):
                continue
            q = dt.date.fromisoformat(d).month in (3, 6, 9, 12)
            ex = cal.get("expiries") or {}
            rows.append({"date": d, "time": "16:00",
                         "event": ("Quarterly" if q else "Monthly") + " option expiry",
                         "tier": ex.get("quarterly_tier" if q else "monthly_tier", 2),
                         "consensus": "—"})
            continue
        if typ == "earnings":
            rows.append({"date": d, "time": "time not stated",
                         "event": f"{p.get('symbol') or t.split()[0]} earnings",
                         "tier": 3, "consensus": "no consensus stored"})
            continue
        name = p.get("release_name") or t.split(" -- ")[0]
        m = match_release(name, cal) or match_release(t, cal)
        if not m or not m.get("label"):
            skipped += 1
            continue
        rows.append({"date": d, "time": m.get("time") or "time not stated",
                     "event": m["label"], "tier": m.get("tier") or 3,
                     "consensus": "no consensus stored"})
    for r in (pmb or {}).get("markets") or []:
        ca = str(r.get("close_at") or "")
        if mon.isoformat() <= ca[:10] < sat.isoformat():
            rows.append({"date": ca[:10], "time": _et(ca) or "time not stated",
                         "event": f"Prediction market resolves: {r.get('question')}",
                         "tier": 3, "consensus": f"last {round(100 * (r.get('probability') or 0))}%"})
    seen, out = set(), []
    for r in sorted(rows, key=lambda r: (r["date"], r["time"], r["tier"], r["event"])):
        k = (r["date"], r["event"])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return {"table": {"columns": ["Day", "Time (ET)", "Event", "Importance",
                                  "Consensus / prior"],
                      "rows": [[_day(r["date"]), r["time"], r["event"],
                                r["tier"], r["consensus"]] for r in out]},
            "rows": out, "window": [mon.isoformat(), (sat - dt.timedelta(days=1)).isoformat()],
            "routine_not_listed": skipped}


def transition_expiry(st, now: str, limits: Optional[dict] = None) -> Optional[dict]:
    """When the Doctrine's Transition count expires: the session `n` sessions
    after the latest Macro dial change, or None when no count is running."""
    import regime                                               # noqa: PLC0415
    try:
        from register import heat                               # noqa: PLC0415
        lim = limits or heat.load_limits()
    except Exception:                                           # noqa: BLE001
        lim = limits or {}
    n = int(((lim.get("regime_mapping") or {}).get("transition_sessions")) or 10)
    rows = st.rows_before(regime.STORE_KEY, "9999-12-31", as_of=now, limit=n + 2)
    states = []
    for r in rows:
        try:
            o = json.loads(r["value_text"])
        except Exception:                                       # noqa: BLE001
            continue
        states.append((o.get("session"), ((o.get("dials") or {}).get("macro") or {})
                       .get("state")))
    change = None
    for i in range(1, len(states)):
        if states[i][1] != states[i - 1][1] and states[i][1] is not None:
            change = states[i]
    if not change or not change[0]:
        return None
    d = dt.date.fromisoformat(str(change[0])[:10])
    k = 0
    while k < n:
        d += dt.timedelta(days=1)
        if session.is_trading_session(d) if session.calendar_covers(d) else d.weekday() < 5:
            k += 1
    return {"changed_on": str(change[0])[:10], "to": change[1], "sessions": n,
            "expires_after": d.isoformat()}


def watching(st, now: str, opened: list[dict], pmb: Optional[dict],
             fed: Optional[dict]) -> list[str]:
    """Item 10: what the system is watching, in the config's words."""
    from altdata import labels                                  # noqa: PLC0415
    out = []
    for c in opened:
        plain = labels.contradiction_plain(c.get("id"))
        z = c.get("magnitude")
        out.append(f"{labels.contradiction(c.get('id')).capitalize()}: open "
                   f"{c.get('persistence_days')} session(s)"
                   + (f" at z {float(z):+.1f}" if isinstance(z, (int, float)) else "")
                   + (f"; it closes when {plain['closes']}." if plain.get("closes")
                      else "."))
    try:
        te = transition_expiry(st, now)
    except Exception:                                           # noqa: BLE001
        te = None
    if te:
        out.append(f"The macro regime changed to {te['to']} on {te['changed_on']}; "
                   f"the Doctrine's {te['sessions']}-session Transition count runs "
                   f"through {te['expires_after']}.")
    from .stack import _venue_name, _pct                        # noqa: PLC0415
    meetings = (fed or {}).get("meetings") or []
    odds = (pmb or {}).get("fomc_odds") or {}
    nxt = sorted(set(list(odds) + [m["meeting"] for m in meetings]))[:1]
    for d in nxt:
        parts = [f"{_venue_name(v)} hold {_pct(o.get('hold'))}, hike "
                 f"{_pct(o.get('hike'))}, cut {_pct(o.get('cut'))}"
                 for v, o in sorted((odds.get(d) or {}).items())]
        m = next((x for x in meetings if abs((dt.date.fromisoformat(x["meeting"])
                                             - dt.date.fromisoformat(d)).days) <= 2),
                 None)
        if m:
            parts.append(f"fed funds futures imply {m['post_pct']:.2f}% after it")
        if parts:
            out.append(f"The next FOMC meeting, {d}: prediction markets and futures "
                       f"-- " + "; ".join(parts) + ".")
    return out


# ---------------------------------------------------------------------------
# Narratives: plain titles, the states' legend, counts in words (item 9)
# ---------------------------------------------------------------------------
def story_line(nid: str, name: str, state: str, ev_for: int, ev_against: int) -> str:
    from altdata import labels                                  # noqa: PLC0415
    st = labels.story(nid)
    title = st.get("title") or name
    stmt = st.get("statement")
    f = (f"{in_words(ev_for).capitalize()} piece{'s' if ev_for != 1 else ''} of "
         f"evidence supported it" if ev_for else "No evidence supported it")
    a = (f"{in_words(ev_against)} contradicted it" if ev_against
         else "none contradicted it")
    return f"{title} ({state}). {stmt + ' ' if stmt else ''}{f}, {a}."


def states_legend(states: list[str]) -> Optional[str]:
    from altdata import labels                                  # noqa: PLC0415
    parts = [f"{s}: {labels.state(s)}" for s in sorted(set(states)) if labels.state(s)]
    return ("States: " + "; ".join(parts) + ".") if parts else None


# ===========================================================================
# T2.3 -- WEEKLY COMPLETENESS (ruled 4 Oct 2026)
# ===========================================================================
def coupon_auctions(st, now: str) -> list[dict]:
    """Every stored auction high yield, across instruments. `as_of` with no
    instrument reads only instrument-less rows, and every auction row carries
    its security as the instrument -- so the instruments are listed first."""
    try:
        insts = [r[0] for r in st.conn.execute(
            "SELECT DISTINCT instrument FROM observations WHERE registry_key = "
            "'auction.high_yield' AND instrument IS NOT NULL")]
    except Exception:                                           # noqa: BLE001
        return []
    out = []
    for inst in insts:
        for r in st.as_of("auction.high_yield", now, inst) or []:
            out.append({**r, "instrument": inst})
    return out


def _closes_of(st, key: str, now: str) -> list[tuple[str, float]]:
    rows = sorted((str(r["observed_at"])[:10], r["value_num"])
                  for r in st.as_of(key, now) if r.get("value_num") is not None)
    out: dict[str, float] = {}
    for d, v in rows:
        out[d] = v
    return sorted(out.items())


def _ret(a: Optional[float], b: Optional[float]) -> Optional[float]:
    return None if a is None or not b else round(100.0 * (a / b - 1.0), 2)


def overnight_intraday(st, sessions: list[str], ending: str, now: str) -> dict:
    """Item 1: per session, SPY's overnight return (prior cash close -> open) and
    intraday return (open -> close), from the stored daily OHLC; and the week's
    totals of each, compounded."""
    from altdata import levels                                  # noqa: PLC0415
    rows, _ = levels.daily_bars(levels.tape_spec("spy"), ending, now, st)
    by = {str(r["observed_at"])[:10]: r for r in rows if r.get("ohlc")}
    days = sorted(d for d in (sessions or []) if d in by)
    allc = [str(r["observed_at"])[:10] for r in rows]
    out, on_tot, id_tot = [], 1.0, 1.0
    for d in days:
        i = allc.index(d)
        if i == 0:
            continue
        prior = rows[i - 1]["close"]
        o, c = by[d]["open"], by[d]["close"]
        on, intr, cc = _ret(o, prior), _ret(c, o), _ret(c, prior)
        if None in (on, intr):
            continue
        on_tot *= 1 + on / 100.0
        id_tot *= 1 + intr / 100.0
        out.append({"day": d, "overnight_pct": on, "intraday_pct": intr,
                    "close_to_close_pct": cc})
    totals = ({"overnight_pct": round(100 * (on_tot - 1), 2),
               "intraday_pct": round(100 * (id_tot - 1), 2)} if out else None)
    table = {"columns": ["Session", "Overnight", "Intraday", "Close to close"],
             "rows": [[_day(r["day"]), _signed(r["overnight_pct"], "%"),
                       _signed(r["intraday_pct"], "%"),
                       _signed(r["close_to_close_pct"], "%")] for r in out]
             + ([["The week", _signed(totals["overnight_pct"], "%"),
                  _signed(totals["intraday_pct"], "%"), "—"]] if totals else [])}
    return {"rows": out, "totals": totals, "table": table}


def overnight_line(book: dict) -> Optional[str]:
    """The daily close's one line (item 1): 'the overnight carried +0.6% of the
    day's +0.4%' -- SPY's open against the prior close, inside the day's move."""
    spy = next((i for i in book.get("instruments") or [] if i["id"] == "spy"), {})
    o = (spy.get("ohlc") or {}).get("open")
    c = (spy.get("frame") or {}).get("last")
    prior = next((lv["value"] for lv in spy.get("levels") or []
                  if lv["type"] == "prior_close"), None)
    if None in (o, c, prior) or not prior:
        return None
    on, day = _ret(o, prior), _ret(c, prior)
    return (f"SPY: the overnight carried {_signed(on, '%')} of the day's "
            f"{_signed(day, '%')} (prior close {prior:,.2f} to the open {o:,.2f}; "
            f"the cash session {_signed(_ret(c, o), '%')}).")


def _bn(v: Optional[float], scale: float = 1.0) -> str:
    if v is None:
        return "—"
    x = v * scale
    return (f"${x / 1e12:,.2f}tn" if abs(x) >= 1e12 else f"${x / 1e9:,.0f}bn")


def plumbing_rows(st, now: str, then: str) -> dict:
    """Item 3: net liquidity and its legs, SOFR against IORB, the credit
    spreads beside HY, the week's auctions, copper and gold/copper. Rows for
    Plumbing's table; each figure from the store with its as-of."""
    from altdata import derived                                 # noqa: PLC0415
    rows, data, nt = [], {}, []

    def two(key, inst=None):
        a = st.latest_as_of(key, now, inst)
        b = st.latest_as_of(key, then, inst)
        return (a.get("value_num") if a else None, b.get("value_num") if b else None,
                str(a["observed_at"])[:10] if a else None)
    nl, nlp, nla = two("calc.net_liquidity")
    if nl is not None:
        rows.append(["Net liquidity (Fed balance sheet less TGA and RRP)", _bn(nl),
                     (_bn(nl - nlp) if nlp is not None else "no prior"), nla])
        data["net_liquidity"] = {"level": nl, "week_change": None if nlp is None
                                 else nl - nlp, "as_of": nla}
    else:
        nt.append("net liquidity")
    # H.4.1 legs: reserves and RRP in billions, TGA in millions (CLAUDE.md gotcha).
    for key, name, scale in (("fred.bank_reserves", "Bank reserves (H.4.1)", 1e9),
                             ("fred.tga", "Treasury General Account (H.4.1)", 1e6),
                             ("fred.rrp", "Reverse repo (RRP)", 1e9)):
        v, pv, asof = two(key)
        if v is None:
            nt.append(name)
            continue
        rows.append([name, _bn(v, scale), _bn((v - pv) if pv is not None else None, scale)
                     if pv is not None else "no prior", asof])
    so, sop, soa = two("fred.sofr")
    io, iop, ioa = two("fred.iorb")
    if so is not None and io is not None:
        sp = round((so - io) * 100)
        spp = round((sop - iop) * 100) if None not in (sop, iop) else None
        rows.append(["SOFR", f"{so:.2f}%", _signed(None if sop is None else
                                                   round((so - sop) * 100), "bp"), soa])
        rows.append(["IORB", f"{io:.2f}%", _signed(None if iop is None else
                                                   round((io - iop) * 100), "bp"), ioa])
        rows.append(["SOFR less IORB (funding pressure when above zero)",
                     f"{sp:+d} bp", _signed(None if spp is None else sp - spp, "bp"),
                     soa])
        data["sofr_iorb_bp"] = sp
    else:
        nt.append("SOFR and IORB (the FRED pull adds them from the next run)")
    for key, name in (("fred.ig_oas", "Investment-grade OAS"),
                      ("fred.ccc_oas", "CCC OAS")):
        v, pv, asof = two(key)
        if v is not None:
            rows.append([name, f"{v:.2f}%", _signed(None if pv is None else
                                                    round((v - pv) * 100), "bp"), asof])
    ccc, cccp, ccca = two("fred.ccc_oas")
    bb, bbp, _ = two("fred.bb_oas")
    if None not in (ccc, bb):
        gap = round((ccc - bb) * 100)
        gp = round((cccp - bbp) * 100) if None not in (cccp, bbp) else None
        rows.append(["CCC less BB (stress inside high yield)", f"{gap:,d} bp",
                     _signed(None if gp is None else gap - gp, "bp"), ccca])
    cu, cup, cua = two("yfinance.mkt_copper_front")
    au, aup, _ = two("yfinance.mkt_gold_front")
    if cu is not None:
        rows.append(["Copper, front future ($/lb; a growth gauge)", f"{cu:,.3f}",
                     _signed(_ret(cu, cup), "%"), cua])
        if au is not None:
            r = au / cu
            rp = (aup / cup) if None not in (aup, cup) else None
            rows.append(["Gold over copper (rises when growth fears rise)",
                         f"{r:,.0f}", _signed(_ret(r, rp), "%"), cua])
            data["gold_copper"] = round(r, 1)
    else:
        nt.append("copper (the price feed adds HG=F from the next run)")
    # THE WEEK'S AUCTIONS: coupons only, with their own figures; the tail is not
    # stored (no when-issued yield).
    auctions = []
    for r in coupon_auctions(st, now):
        d = str(r["observed_at"])[:10]
        inst = str(r.get("instrument") or "")
        if not (then[:10] < d <= now[:10]) or inst.split(":")[0] not in ("Note", "Bond", "TIPS"):
            continue
        btc = st.latest_as_of("auction.bid_to_cover", now, inst)
        dl = st.latest_as_of("auction.dealer_share", now, inst)
        auctions.append({"date": d, "instrument": inst, "high_yield": r["value_num"],
                         "bid_to_cover": btc.get("value_num") if btc else None,
                         "dealer_share": dl.get("value_num") if dl else None})
        typ, term = inst.split(":", 1)
        rows.append([f"{term} {typ.lower()} auction ({d}): high yield "
                     f"{r['value_num']:.3f}%",
                     f"bid-to-cover {btc['value_num']:.2f}" if btc else "—",
                     f"dealers took {100 * dl['value_num']:.0f}%" if dl else "—",
                     "tail not stored"])
    data["auctions"] = auctions
    return {"rows": rows, "data": data, "not_tracked": nt}


def global_fx(st, now: str, then: str) -> dict:
    """Item 4: the sub-section 'Global rates and FX'."""
    rows, nt = [], []
    for key, name, dp in (("yfinance.mkt_usdjpy", "USD/JPY (yen per dollar)", 2),
                          ("yfinance.mkt_eurusd", "EUR/USD (dollars per euro)", 4),
                          ("yfinance.mkt_usdcny", "USD/CNY (yuan per dollar)", 4)):
        a = st.latest_as_of(key, now)
        b = st.latest_as_of(key, then)
        if not a:
            nt.append(name.split(" (")[0] + " (the price feed adds it from the next run)")
            continue
        rows.append([name, f"{a['value_num']:,.{dp}f}",
                     _signed(_ret(a["value_num"], b["value_num"] if b else None), "%"),
                     str(a["observed_at"])[:10]])
    for key, name in (("mof.jgb_10y", "Japan 10-year (JGB)"),
                      ("mof.jgb_30y", "Japan 30-year (JGB)")):
        a = st.latest_as_of(key, now)
        b = st.latest_as_of(key, then)
        if not a:
            nt.append(name)
            continue
        rows.append([name, f"{a['value_num']:.3f}%",
                     _signed(None if not b else round((a["value_num"] - b["value_num"]) * 100),
                             "bp"), str(a["observed_at"])[:10]])
    nt.append("the 10-year Bund and the OAT-Bund spread (the ECB's data portal is "
              "the source to add)")
    return {"title": "Global rates and FX",
            "table": {"columns": ["Series", "Level", "Week", "As of"], "rows": rows},
            "not_tracked": nt}


def volatility(st, now: str, wis: Optional[dict] = None) -> dict:
    """Item 5: the 'Volatility' sub-section of Mechanics -- six rows."""
    from altdata import derived                                 # noqa: PLC0415
    five = (dt.date.fromisoformat(now[:10]) - dt.timedelta(days=1826)).isoformat()
    vix_hist = [v for d, v in _closes_of(st, "yfinance.mkt_vix", now) if d >= five]
    vix = vix_hist[-1] if vix_hist else None
    rows, data = [], {}
    if vix is not None:
        pct = derived.percentile_of(vix_hist, vix) if len(vix_hist) > 20 else None
        rows.append(["VIX", f"{vix:.2f}",
                     f"{round(pct):d}th percentile, five years" if pct is not None else "—"])
        data["vix"] = vix
        data["vix_percentile_5y"] = None if pct is None else round(pct)
    vts = (wis or {}).get("vol_term_structure") or {}
    pub = vts.get(vts.get("published_by") or "") or {}
    if pub.get("ratio") is not None:
        rows.append(["VIX3M over VIX (term structure, published)",
                     f"{float(pub['ratio']):.2f}", str(pub.get("state") or "—")])
    rv = st.latest_as_of("calc.vol_spy_realized_20d", now)
    rvv = rv.get("value_num") if rv else None
    if rvv is not None and rvv < 3:
        rvv = rvv * 100.0                     # stored as a fraction
    if rvv is not None and vix is not None:
        rows.append(["SPY 20-day realized against the VIX", f"{rvv:.1f} vs {vix:.1f}",
                     f"implied {'above' if vix > rvv else 'below'} realized by "
                     f"{abs(vix - rvv):.1f} points"])
        data["implied_daily_move_pct"] = round(vix / 252 ** 0.5, 2)
        data["realized_daily_move_pct"] = round(rvv / 252 ** 0.5, 2)
        rows.append(["Daily move priced, and realized",
                     f"{data['implied_daily_move_pct']:.2f}% priced",
                     f"{data['realized_daily_move_pct']:.2f}% realized"])
    for key, name in (("yfinance.mkt_move", "MOVE (Treasury volatility)"),
                      ("yfinance.mkt_skew", "SKEW (tail-risk pricing)")):
        a = st.latest_as_of(key, now)
        rows.append([name, f"{a['value_num']:.1f}" if a else "—",
                     str(a["observed_at"])[:10] if a else "not yet stored"])
    return {"title": "Volatility",
            "table": {"columns": ["Measure", "Level", "Context"], "rows": rows[:6]},
            "data": data}


def sector_table(st, now: str, then: str, lead: list) -> dict:
    """Item 6: the week, one month and three months beside each other, and how
    many sectors sit above their 50- and 200-day averages."""
    from altdata import labels                                  # noqa: PLC0415
    from altdata.sources.yfinance_source import SECTOR_KEYS     # noqa: PLC0415
    rows, above50, above200, n = [], 0, 0, 0
    for k in SECTOR_KEYS:
        cl = _closes_of(st, f"yfinance.{k}", now)
        if len(cl) < 2:
            continue
        vals = [v for _, v in cl]
        last = vals[-1]
        wk = next((v for d, v in reversed(cl) if d <= then[:10]), None)
        m1 = vals[-22] if len(vals) > 22 else None
        m3 = vals[-64] if len(vals) > 64 else None
        rows.append((labels.sector(k.replace("mkt_", "").upper()), _ret(last, wk),
                     _ret(last, m1), _ret(last, m3)))
        if len(vals) >= 200:
            n += 1
            above50 += last > sum(vals[-50:]) / 50
            above200 += last > sum(vals[-200:]) / 200
    rows.sort(key=lambda r: -(r[1] or -999))
    styles = [(lab, v) for lab, v in lead if len(lab) > 4]
    line = (f"Sectors above their 50-day average: {above50} of {n}; above their "
            f"200-day: {above200} of {n}." if n else None)
    return {"table": {"columns": ["Sector or pair", "Week", "One month", "Three months"],
                      "rows": [[r[0], _signed(r[1], "%"), _signed(r[2], "%"),
                                _signed(r[3], "%")] for r in rows]
                      + [[lab, _signed(v, "%"), "—", "—"] for lab, v in styles]},
            "line": line, "above_50d": above50, "above_200d": above200, "of": n}


def changed_since(ed: dict, wis: dict, p: dict, trig: dict,
                  voices: Optional[dict] = None) -> list[str]:
    """Item 7: what changed since the last Weekly, computed, in display labels."""
    from altdata import labels                                  # noqa: PLC0415
    name = {"gamma": "Dealer gamma", "vol": "The volatility regime",
            "macro": "The macro regime"}
    out = []
    for ch in wis.get("dial_changes") or []:
        out.append(f"{name.get(ch.get('dial'), ch.get('dial'))} moved from "
                   f"{ch.get('from') or 'absent'} to {ch.get('to')}.")
    opened = wis.get("exceptions_opened") or []
    if opened:
        out.append("Exceptions opened: " + "; ".join(labels.exception(e) for e in opened) + ".")
    closed = wis.get("exceptions_closed") or []
    if closed:
        out.append("Exceptions closed: " + "; ".join(labels.exception(e) for e in closed) + ".")
    rb = (((p.get("register") or {}).get("rule_breaks") or {}).get("rule_breaks_listed") or [])
    if rb:
        out.append(f"Rule breaks: {len(rb)} ("
                   + ", ".join(sorted({str(b.get('kind')).replace('_', ' ') for b in rb}))
                   + ").")
    fired = [f"Plumbing deep on {len(trig.get('plumbing') or [])}"
             if trig.get("plumbing") else None,
             f"What's priced deep on {len(trig.get('priced') or [])}"
             if trig.get("priced") else None]
    fired = [x for x in fired if x]
    if fired:
        out.append(f"Triggers fired: {'; '.join(fired)} of "
                   f"{trig.get('sessions', 0)} session(s).")
    inf = [v for v in ((voices or {}).get("data") or {}).get("voices") or []
           if v.get("status") == "INFLECTED"]
    if inf:
        out.append("Voices that inflected: " + "; ".join(
            f"{v['voice']} ({v['outlet']})" for v in inf[:5]) + ".")
    return out or ["Nothing in the dials, exceptions, rule breaks, triggers or voices "
                   "changed since the last Weekly."]


def reading_minutes(ed: dict, charts: int) -> float:
    """Item 7: prose words / 250 plus 20 seconds a chart, in minutes."""
    from .stack import section_words                          # noqa: PLC0415
    words = sum(section_words(s) for s in ed.get("sections") or [])
    return round(words / 250.0 + charts * 20 / 60.0, 1)


EARNINGS_SEASONS = ((1, 10, 2, 28), (4, 10, 5, 31), (7, 10, 8, 31), (10, 10, 11, 30))


def seasons_from_config() -> tuple:
    try:
        return tuple((x["from"][0], x["from"][1], x["to"][0], x["to"][1])
                     for x in load_calendar().get("earnings_seasons") or [])             or EARNINGS_SEASONS
    except Exception:                                           # noqa: BLE001
        return EARNINGS_SEASONS


def in_season(day: str, seasons: Optional[tuple] = None) -> bool:
    seasons = seasons or seasons_from_config()
    d = dt.date.fromisoformat(day[:10])
    for m1, d1, m2, d2 in seasons:
        if dt.date(d.year, m1, d1) <= d <= dt.date(d.year, m2, d2):
            return True
    return False


def earnings_block(st, ending: str, now: str, then: str,
                   seasons: Optional[tuple] = None) -> Optional[dict]:
    """Item 9: universe names that reported this week -- EPS and revenue against
    stored consensus, beat or miss, the next day's reaction from stored prices.
    None outside the season (prints nothing); inside it, 'no universe name
    reported' when none did."""
    if not in_season(ending, seasons):
        return None
    from altdata import events                                  # noqa: PLC0415
    rows, data = [], []
    with events.EventStore(str(st.path)) as ev:
        recs = ev.conn.execute(
            "SELECT observed_at, payload FROM events WHERE type = 'earnings' AND "
            "observed_at > ? AND observed_at <= ? AND available_at <= ?",
            (then, now, now)).fetchall()
    for obs, payload in recs:
        pl = json.loads(payload or "{}")
        if pl.get("reported_eps") is None:
            continue
        sym = str(pl.get("symbol") or "")
        est = pl.get("eps_estimate")
        eps = pl.get("reported_eps")
        verdict = ("beat" if est is not None and eps > est else
                   "miss" if est is not None and eps < est else
                   "in line" if est is not None else "no consensus stored")
        d = str(obs)[:10]
        cl = _closes_of(st, f"yfinance.mkt_{sym.lower()}", now)
        before = next((v for dd, v in reversed(cl) if dd < d), None)
        after = next((v for dd, v in cl if dd > d), None)
        react = _ret(after, before)
        rev_a, rev_e = pl.get("reported_revenue"), pl.get("revenue_estimate")
        rows.append([sym, f"{eps:.2f} vs {est:.2f}" if est is not None else f"{eps:.2f}",
                     verdict,
                     (f"{rev_a / 1e9:,.1f}bn vs {rev_e / 1e9:,.1f}bn"
                      if None not in (rev_a, rev_e) else "revenue not stored"),
                     _signed(react, "%") if react is not None else "not yet",
                     d])
        data.append({"symbol": sym, "eps": eps, "eps_estimate": est, "verdict": verdict,
                     "reaction_pct": react, "date": d})
    return {"title": "Earnings this week",
            "table": {"columns": ["Name", "EPS against consensus", "Verdict", "Revenue",
                                  "Next day", "Reported"], "rows": rows},
            "lines": [] if rows else ["No universe name reported this week."],
            "data": data}
