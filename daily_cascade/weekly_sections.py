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
from altdata.numeral_audit import ordinal as na_ordinal

from .cadence import Period

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


# THE ATTRIBUTION TAKES A CLAUSE OR A QUOTATION (W-1.1 item 1.0). The 9 Oct
# edition printed "attributed the move in oil to Oil prices rose ...": the stored
# claim is often a whole sentence, and pasted after "to" it reads as nonsense. A
# claim that is a noun phrase or clause ("a supply cut", "the Fed's comments")
# follows "attributed the move in X to"; a claim that is a sentence -- it opens
# with a capital, or names a verb of movement -- is quoted as the outlet's words.
_SENTENCE_VERB = re.compile(r"\b(?:rose|fell|rallied|slid|dropped|climbed|jumped|"
                            r"gained|lost|surged|sank|edged|tumbled|soared|is|are|"
                            r"was|were|has|have|had|will|said|says)\b", re.I)


def attribution_text(a: dict) -> str:
    claim = str(a.get("claim") or "").strip().rstrip(".").strip()
    claim = claim.strip("\"“”'")
    outlet, market = a.get("outlet"), a.get("market")
    if claim and (claim[0].isupper() and not claim.startswith(("Fed", "OPEC", "U.S.",
                                                               "US ", "China", "ECB"))
                  or _SENTENCE_VERB.search(claim)):
        return f"{outlet}, on the move in {market}: “{claim}.”"
    return f"{outlet} attributed the move in {market} to {claim}"


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
                lines.append(f"{_day(d)}: {attribution_text(a)} ({a['source_url']}).")
    return {"table": {"columns": ["Day", "SPY", "10-year", "Tier-1 release "
                                  "(actual, prior)", "Fed speech or auction",
                                  "Most-cited story (source)"], "rows": rows},
            "data": data, "attributions": lines}


# ---------------------------------------------------------------------------
# The tape: one table (item 4)
# ---------------------------------------------------------------------------
# PER-ROW AS-OF (W-1.1 item 1.2, ruling 2). The edition's "as of" is the latest
# bar; a row whose own bar is older prints its date, and a PRICE whose last bar is
# older than the edition's prints "stale since <date>" beside it -- the 9 Oct
# Bitcoin row printed a bare price two days old. A series with a declared release
# lag (config `freshness.expected_lag`: TIC, monthly) prints "lag: <period>
# (<reference>, released <date>)" instead, because late is its normal state.
def stale_since(as_of: Optional[str], edition_day: Optional[str]) -> Optional[str]:
    if not as_of or not edition_day:
        return None
    return str(as_of)[:10] if str(as_of)[:10] < str(edition_day)[:10] else None


def with_stale(text: str, as_of: Optional[str], edition_day: Optional[str]) -> str:
    d = stale_since(as_of, edition_day)
    return f"{text} (stale since {d})" if d else text


def expected_lag(key: str, cfg: Optional[dict] = None) -> Optional[str]:
    if cfg is None:
        from altdata import bars as bars_mod                    # noqa: PLC0415
        cfg = bars_mod.load_config()
    return ((cfg.get("freshness") or {}).get("expected_lag") or {}).get(key)


def lag_label(key: str, observed_at: Optional[str], available_at: Optional[str],
              cfg: Optional[dict] = None) -> Optional[str]:
    """'lag: monthly (July, released 2026-09-18)' for a declared-lag series, or
    None. The reference period is the observation's own; the release date is
    when the store could first know it."""
    lag = expected_lag(key, cfg)
    if not lag or not observed_at:
        return None
    try:
        ref = dt.date.fromisoformat(str(observed_at)[:10])
    except ValueError:
        return None
    period = f"{ref:%B}" if lag == "monthly" else f"{ref:%d %b}"
    rel = f", released {str(available_at)[:10]}" if available_at else ""
    return f"lag: {lag} ({period}{rel})"


def edition_session(now: str) -> Optional[str]:
    """The last trading session on or before `now`'s date: the day a price's bar
    is held to. None where the session calendar cannot say -- then nothing is
    marked stale, rather than everything."""
    try:
        return session.last_trading_session(str(now)[:10]).isoformat()
    except Exception:                                           # noqa: BLE001
        return None


def tape_table(book: dict, edition_day: Optional[str] = None) -> dict:
    cols = ["Market", "Last", "Session", "Week", "Month", "YTD", "Week high / low",
            "52-week high (distance)", "vs 20 / 50 / 200-day", "Gamma flip"]
    rows, gaps, ids = [], [], []
    # The edition's day: the latest bar among the session-traded instruments (a
    # continuous one, Bitcoin, trades on the weekend and would set it a day late).
    if edition_day is None:
        days = [str((i.get("frame") or {}).get("as_of") or "")
                for i in book.get("instruments") or [] if not i.get("continuous")]
        edition_day = max([d for d in days if d], default=None)
    # EVERY ROW CARRIES ITS UNIT (W-1.2 item 2.8): a price prints with the tape
    # config's `unit` -- "$668.40", "98.10 index"; a yield with its %.
    from altdata import bars as bars_mod                        # noqa: PLC0415
    units = {t["id"]: t.get("unit") for t in bars_mod.tape()}

    def price(v: float, iid: str) -> str:
        u = units.get(iid)
        if u == "$":
            return f"${v:,.2f}"
        return f"{v:,.2f} {u}" if u else f"{v:,.2f}"
    # THE MOBILE RULE (T2.3 item 8): no table wider than six columns -- the
    # returns table (6) and the levels table (5) are split below.
    for i in book.get("instruments") or []:
        f = i.get("frame") or {}
        y = i["kind"] == "yield"
        unit = "bp" if y else "%"
        k = "bps" if y else "pct"
        last = f.get("last")
        lv = {x["type"]: x["value"] for x in i.get("levels") or []}
        if last is None:
            # NO BAR FOR THE SESSION, BUT AN OLDER ONE (W-1.1 item 1.2): the row
            # prints that close, stale since its date, and no move -- never a
            # bare price, never a move measured from a stale close.
            pc = next((x for x in i.get("levels") or [] if x["type"] == "prior_close"),
                      None)
            if pc and pc.get("as_of"):
                fmt0 = (lambda v: f"{v:,.3f}%") if y else (lambda v, _i=i["id"]: price(v, _i))
                rows.append([i["label"], f"{fmt0(pc['value'])} (stale since "
                             f"{str(pc['as_of'])[:10]})", "—", "—", "—", "—",
                             "—", "—", "—", "—"])
                ids.append((i["id"], None))
                continue
            gaps.append(f"{i['label']}: no daily bar for the session")
            continue

        def dist(level: Optional[float]) -> str:
            if level is None:
                return "—"
            v = (last - level) * 100.0 if y else 100.0 * (last / level - 1.0)
            return _signed(round(v) if y else round(v, 2), unit)
        fmt = (lambda v: f"{v:,.3f}%") if y else (lambda v, _i=i["id"]: price(v, _i))
        hl = (f"{fmt(lv['week_high'])} / {fmt(lv['week_low'])}"
              if lv.get("week_high") is not None else "—")
        h52 = (f"{fmt(lv['high_52w'])} ({dist(lv['high_52w'])})"
               if lv.get("high_52w") is not None else "—")
        mas = " / ".join(dist(lv.get(m)) for m in ("ma_20d", "ma_50d", "ma_200d"))
        rows.append([i["label"], with_stale(fmt(last), f.get("as_of"), edition_day),
                     _signed(f.get(f"session_change_{k}"), unit),
                     _signed(f.get(f"wtd_change_{k}"), unit),
                     _signed(f.get(f"mtd_change_{k}"), unit),
                     _signed(f.get(f"ytd_change_{k}"), unit), hl, h52, mas,
                     fmt(lv["gamma_flip"]) if lv.get("gamma_flip") is not None else "—"])
        ids.append((i["id"], f.get("as_of")))
    ret = {"columns": cols[:6], "rows": [r[:6] for r in rows]}
    lev = {"columns": [cols[0]] + cols[6:], "rows": [[r[0]] + r[6:] for r in rows]}
    # Each row's instrument and bar date, for the consistency gate (W-1.1 1.1).
    return {"table": ret, "levels_table": lev, "not_tracked": gaps, "row_ids": ids}


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
    # THE WALLS ARE THE MORNING'S OTM WALLS (ruled 17 Oct 2026; audit F5): the
    # put wall moves from the all-strike put peak to the OTM put gamma wall, and
    # the call wall likewise. A card stored before 6b part 1 carries no OTM wall,
    # so its held flags are None, never scored against a peak.
    cw = card.get("call_wall_otm_morning")
    pw = card.get("put_wall_otm_morning")
    mp = card.get("max_pain")
    out = {"implied_range": round(implied, 2) if implied else None,
           "iv_source": ("SPY ATM 30-day IV" if own_iv else
                         "VIX as proxy" if vix else None),
           "actual_range": round(actual, 2) if actual is not None else None,
           "pinned": (None if close is None or mp is None
                      else _within(close, mp, pin_pct)),
           # ELIGIBILITY BEFORE OUTCOME (brief v2 section 5.2): a wall the
           # session never approached is None, never False.
           "call_wall_held": (None if None in (hi, close, cw)
                              or not _within(hi, cw, wall_pct) else close < cw),
           "put_wall_held": (None if None in (lo, close, pw)
                             or not _within(lo, pw, wall_pct) else close > pw),
           "amplified": (None if card.get("flip_crossed") is None or not implied
                         or actual is None else
                         bool(card["flip_crossed"]) and actual >= ratio * implied)}
    # DAMPENED (6b part 2; the pre-registration's H1 outcome): a regime session
    # (the morning's net-to-gross at the gate) in positive gamma whose range came
    # in at or under the declared share of the implied range. Ineligible: None.
    damp = float(fc.get("dampened_range_ratio", 0.8))
    elig = (card.get("regime_eligible") and (card.get("net_gex_morning") or 0) > 0)
    out["dampened"] = (None if not elig or not implied or actual is None
                       else actual <= damp * implied)
    flip = card.get("flip_morning")
    out["close_vs_flip"] = (None if None in (close, flip) else
                            ("above" if close > flip else "below"))
    # THE IV CHECK (PB-1): SPY's own ATM IV and the VIX more than the declared
    # gap apart -- both print and the row is marked "check"; neither is chosen.
    gap = float((cfg.get("dealer_flags") or {}).get("iv_vix_check_points", 5.0))
    out["iv_check"] = bool(own_iv and vix and abs(own_iv - vix) > gap)
    out["spy_iv"], out["vix"] = own_iv, vix
    return out


def _gated_regime(card: dict, cfg: dict) -> str:
    """The close's regime word, gated on net-to-gross (6b; ruled 16 Oct 2026).
    A card stored before the gate carries no net-to-gross: its sign prints
    marked ungated, never as a regime."""
    from . import dealer_block                                  # noqa: PLC0415
    ntg = card.get("net_to_gross_close")
    if ntg is None:
        g = card.get("gamma_regime")
        return f"{g} (ungated)" if g else "—"
    return dealer_block.regime(card.get("net_gex_close"), ntg,
                               cfg.get("dealer_block") or {})


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
                                    ("amplified", "amplified"),
                                    ("dampened", "dampened")) if f.get(k)]
        rows.append([_day(c["session"]), _gated_regime(c, cfg),
                     bn(c.get("net_gex_close")),
                     bn(c.get("dex_close")),
                     g(c.get("flip_morning")),
                     f"{g(c.get('call_wall_otm_morning'))} / "
                     f"{g(c.get('put_wall_otm_morning'))}",
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
                       ("pinned", "call_wall_held", "put_wall_held", "amplified",
                        "dampened")},
                       "implied_range": f["implied_range"],
                       "actual_range": f["actual_range"],
                       "close_vs_flip": f["close_vs_flip"],
                       "gamma_regime": c.get("gamma_regime")})
    # TWO TABLES OF SIX (T2.3 mobile rule): the profile, then the ranges.
    return {"table": {"columns": ["Session", "Gamma regime", "Net GEX", "DEX",
                                  "Flip", "OTM call / put wall"],
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
            "it is closing. The dates: when the gap crossed its line (its age, in "
            "sessions), when it opened, and when it became an exception.")


# AGE VERSUS STATUS (W-1.1 item 1.3, ruled 11 Oct 2026). The 9 Oct edition printed
# a gap measured for eight sessions and promoted to an exception that week as one
# number. A gap now prints three dates, read from the stored objects:
#   gap since        the first session of the current run above its line -- the
#                    session it went pending; "open n sessions" is this age
#   open since       the first session the persistence rule opened it
#   exception since  the first session it counted as an exception
# An extreme prints the first session of its current run as an exception.
def state_dates(objs: list[tuple[str, dict]]) -> dict[str, dict]:
    """{contradiction id or exception id: {gap_since, open_since,
    exception_since, sessions}} from the stored objects, oldest first. Each date
    is the start of the CURRENT unbroken run of that state."""
    import regime                                               # noqa: PLC0415
    runs: dict[str, dict] = {}
    for day, obj in objs:
        seen_c, seen_e = set(), set()
        for c in obj.get("contradictions") or []:
            cid = c.get("id")
            if not cid:
                continue
            r = runs.setdefault(cid, {})
            for flag, k in ((bool(c.get("condition_met")), "gap_since"),
                            (c.get("open_state") == "open", "open_since"),
                            (bool(c.get("exception")), "exception_since")):
                if flag:
                    r[k] = r.get(k) or day
                else:
                    r[k] = None
            r["sessions"] = (r.get("sessions") or 0) + 1 if c.get("condition_met") else 0
            seen_c.add(cid)
        for e in regime.exception_ids(obj):
            r = runs.setdefault(e, {})
            r["exception_since"] = r.get("exception_since") or day
            seen_e.add(e)
        for k, r in runs.items():
            if ":" in k and k not in seen_e:
                r["exception_since"] = None
            elif ":" not in k and k not in seen_c:
                r.update(gap_since=None, open_since=None, exception_since=None,
                         sessions=0)
    return runs


def three_dates(d: Optional[dict]) -> str:
    """'gap since 2026-09-29 (8 sessions) · open since 2026-09-30 · exception
    since 2026-10-05', each part only where the state holds."""
    d = d or {}
    parts = []
    if d.get("gap_since"):
        n = d.get("sessions")
        parts.append(f"gap since {d['gap_since']}"
                     + (f" ({n} session{'s' if n != 1 else ''})" if n else ""))
    if d.get("open_since"):
        parts.append(f"open since {d['open_since']}")
    if d.get("exception_since"):
        parts.append(f"exception since {d['exception_since']}")
    return " · ".join(parts) or "—"


# The window the gap's z is measured over (config/market_state.yaml
# contradictions.window_days), in words for the column head and the glossary.
def gap_window_words() -> str:
    try:
        cfg = yaml.safe_load((REPO / "config" / "market_state.yaml")
                             .read_text(encoding="utf-8")) or {}
        days = int(((cfg.get("contradictions") or {}).get("window_days")) or 1826)
    except Exception:                                           # noqa: BLE001
        days = 1826
    years = round(days / 365.25)
    return f"{in_words(years)}-year window" if years >= 1 else f"{days}-day window"


def gap_table(opened: list[dict], history: dict[str, list],
              dates: Optional[dict] = None) -> dict:
    from altdata import labels                                  # noqa: PLC0415
    rows, data = [], []
    dates = dates or {}
    for c in opened:
        cid = c.get("id")
        plain = labels.contradiction_plain(cid)
        h = history.get(cid) or []
        trend = "—"
        if len(h) >= 2 and None not in (h[-1][1], h[-2][1]):
            trend = "rising" if abs(h[-1][1]) > abs(h[-2][1]) else "falling"
        z = c.get("magnitude")
        dd = dates.get(cid) or {"gap_since": c.get("since"),
                                "sessions": c.get("persistence_days")}
        rows.append([labels.contradiction(cid).capitalize(), plain.get("legs") or "—",
                     (f"{float(z):+.1f} (line {float(c.get('threshold_z') or 2.0):.1f})"
                      if isinstance(z, (int, float)) else "—"), trend,
                     three_dates(dd), plain.get("closes") or "—"])
        data.append({"gap": labels.contradiction(cid), "sides": plain.get("legs"),
                     "z": round(float(z), 1) if isinstance(z, (int, float)) else None,
                     "direction": trend,
                     # The GAP's age, in sessions -- "open n sessions" in prose
                     # means this and nothing else (item 1.3).
                     "sessions_open": dd.get("sessions") or c.get("persistence_days"),
                     "gap_since": dd.get("gap_since"), "open_since": dd.get("open_since"),
                     "exception_since": dd.get("exception_since"),
                     "closes_when": plain.get("closes")})
    return {"table": {"columns": ["Gap", "What each side is saying",
                                  f"z, {gap_window_words()} (line)", "Direction",
                                  "Gap since · open since · exception since",
                                  "What would close it"],
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
                  cal: Optional[dict] = None, classes: Optional[dict] = None) -> dict:
    """The coming week, Monday to Friday after `ending`, one row per event:
    day, time ET, event, importance, consensus or prior -- and (W-1.3a item 3.9)
    each row's event class from config/weekly_ahead.yaml's `release_classes`.
    A release no class names and every bill auction is ROUTINE: kept apart, for
    the reference tables, and counted. Scheduled earnings rows are kept with
    their symbol, session and consensus EPS."""
    from altdata import events                                  # noqa: PLC0415
    cal = cal or load_calendar()
    if classes is None:
        from . import ahead                                     # noqa: PLC0415
        classes = ahead.load_config().get("release_classes") or {}
    end = dt.date.fromisoformat(ending[:10])
    mon = end + dt.timedelta(days=(7 - end.weekday()) % 7 or 7)
    sat = mon + dt.timedelta(days=5)
    rows: list[dict] = []
    routine: list[dict] = []
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
                         "consensus": "—",
                         "cls": ("fomc_decision" if kind == "FOMC Meetings" else
                                 "fed_chair" if chair else "fed_speaker")})
            continue
        if src == "treasury_upcoming":
            inst = canonical_auction(str(p.get("instrument") or ""))
            if inst.split(":")[0] not in ("Note", "Bond", "TIPS"):
                routine.append({"date": d, "time": "11:30",
                                "event": f"{inst.split(':')[-1]} "
                                         f"{inst.split(':')[0].lower()} auction"})
                continue
            m = match_release(inst, cal)
            hy = st.latest_as_of("auction.high_yield", now, inst)
            bc = st.latest_as_of("auction.bid_to_cover", now, inst)
            prior = (f"prior {inst.split(':')[1].lower()}: high yield "
                     f"{hy['value_num']:.3f}%"
                     + (f", bid-to-cover {bc['value_num']:.2f}" if bc else "")
                     + f" ({str(hy['observed_at'])[:10]}); tail not stored"
                     if hy else "no prior auction stored")
            label = (m or {}).get("label") or \
                f"{inst.split(':')[1]} {inst.split(':')[0].lower()} auction"
            rows.append({"date": d, "time": (m or {}).get("time") or "13:00",
                         "event": label, "tier": (m or {}).get("tier") or 3,
                         "consensus": prior,
                         "cls": classes.get(label) or "coupon_auction"})
            continue
        if typ == "session_event":
            if not re.search(r"OPEX|expir", t, re.I):
                continue
            q = dt.date.fromisoformat(d).month in (3, 6, 9, 12)
            ex = cal.get("expiries") or {}
            rows.append({"date": d, "time": "16:00",
                         "event": ("Quarterly" if q else "Monthly") + " option expiry",
                         "tier": ex.get("quarterly_tier" if q else "monthly_tier", 2),
                         "consensus": "—",
                         "cls": "opex_quarterly" if q else "opex_monthly"})
            continue
        if typ == "earnings" or p.get("kind") == "earnings":
            sym = p.get("symbol") or t.split()[0]
            rows.append({"date": d, "time": earnings_session(p.get("release_at") or obs),
                         "event": f"{sym} earnings", "tier": 3,
                         "consensus": "no consensus stored", "symbol": sym,
                         "eps_estimate": p.get("eps_estimate"), "cls": "earnings"})
            continue
        name = p.get("release_name") or t.split(" -- ")[0]
        m = match_release(name, cal) or match_release(t, cal)
        cls = classes.get((m or {}).get("label") or "")
        if not m or not m.get("label") or not cls:
            routine.append({"date": d, "time": (m or {}).get("time") or
                            "time not stated",
                            "event": (m or {}).get("label") or name})
            continue
        rows.append({"date": d, "time": m.get("time") or "time not stated",
                     "event": m["label"], "tier": m.get("tier") or 3,
                     "consensus": "no consensus stored", "cls": cls})
    for r in (pmb or {}).get("markets") or []:
        ca = str(r.get("close_at") or "")
        if mon.isoformat() <= ca[:10] < sat.isoformat():
            rows.append({"date": ca[:10], "time": _et(ca) or "time not stated",
                         "event": f"Prediction market resolves: {r.get('question')}",
                         "tier": 3, "consensus": f"last {round(100 * (r.get('probability') or 0))}%",
                         "cls": "prediction_family",
                         "probability": r.get("probability")})
    # THE CALENDAR'S OWN EVENTS (batch 3, §5): dated and recurring rows the
    # events table does not carry -- buybacks, the BoJ, JGB auctions, H.4.1.
    from . import calendar_config                               # noqa: PLC0415
    rows += calendar_config.rows(cal, mon, sat)
    seen, out = set(), []
    for r in sorted(rows, key=lambda r: (r["date"], r["time"], r["tier"], r["event"])):
        k = (r["date"], r["event"])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    rseen, rout = set(), []
    for r in sorted(routine, key=lambda r: (r["date"], r["time"], r["event"])):
        if (r["date"], r["event"]) not in rseen:
            rseen.add((r["date"], r["event"]))
            rout.append(r)
    return {"table": {"columns": ["Day", "Time (ET)", "Event", "Importance",
                                  "Consensus / prior"],
                      "rows": [[_day(r["date"]), r["time"], r["event"],
                                r["tier"], r["consensus"]] for r in out]},
            "rows": out, "window": [mon.isoformat(), (sat - dt.timedelta(days=1)).isoformat()],
            "routine": rout, "routine_not_listed": len(rout)}


# W-1.3c item 9: what a row with no release time says. "session not stated" read
# as if the company had not said; the truth is that the source stored a date.
RELEASE_NOT_CAPTURED = "release time not captured"


def earnings_session(observed_at: Any) -> str:
    """Pre- or post-market from a stored earnings timestamp: the event's
    `release_at` where the source carried a release time, else its observed_at.
    The calendar route stores a bare date at 13:30Z (altdata/sources/earnings._iso),
    which says nothing about the session: "release time not captured"."""
    s = str(observed_at or "")
    if len(s) <= 10 or "T13:30:00" in s:
        return RELEASE_NOT_CAPTURED
    try:
        et = session.to_eastern(dt.datetime.fromisoformat(s.replace("Z", "+00:00")))
    except (ValueError, TypeError):
        return RELEASE_NOT_CAPTURED
    hm = et.hour * 60 + et.minute
    return ("pre-market" if hm < 9 * 60 + 30 else "post-market" if hm >= 16 * 60
            else "during the session")


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
# W-1.1 item 1.7 -- "UNVALIDATED" TAGS (ruled 11 Oct 2026)
# ===========================================================================
def validated_min_n() -> int:
    """W-1.3a item 3.7: graded at least this often, a classification or signal
    is validated (config `validated_min_n`, 30)."""
    try:
        from . import stack as stack_mod                        # noqa: PLC0415
        return int(stack_mod.config().get("validated_min_n") or 30)
    except Exception:                                           # noqa: BLE001
        return 30


def unvalidated_tag(n: int) -> str:
    """The tag a descriptive classification carries; at n >= the validated
    minimum it is a validated signal and says so instead (W-1.3a item 3.7)."""
    if n >= validated_min_n():
        return f"(validated, n={n})"
    return f"(descriptive; unvalidated, n={n})"


def definitions_version(repo: Optional[Path] = None) -> str:
    """W-1.3a item 3.7: the glossary's stamp -- the short hash of the last commit
    that touched config/, at render. A run outside a git checkout says so."""
    import subprocess                                           # noqa: PLC0415
    root = str(repo or REPO)
    for args in (["git", "log", "-1", "--format=%h", "--", "config"],
                 ["git", "rev-parse", "--short", "HEAD"]):
        try:
            out = subprocess.run(args, cwd=root, capture_output=True, text=True,
                                 timeout=10).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            out = ""
        if re.fullmatch(r"[0-9a-f]{6,40}", out or ""):
            return out
    return "unavailable (no git checkout)"


def technical_appendix(cfg: dict) -> Optional[dict]:
    """W-1.3a item 3.7: the reference tier's formulas, units and sign
    conventions, the GEX/DEX universe and the expiry coverage."""
    ta = cfg.get("technical_appendix") or {}
    rows = [[r.get("quantity"), r.get("formula"), r.get("units"), r.get("sign")]
            for r in ta.get("rows") or []]
    dealers = [t.get("dealer") for t in cfg.get("tape") or [] if t.get("dealer")]
    if dealers:
        rows.append(["GEX/DEX universe", ", ".join(dealers) + " (the tape's dealer "
                     "symbols), from their captured chains", "—", "—"])
    if ta.get("expiry_coverage"):
        rows.append(["Expiry coverage", ta["expiry_coverage"], "—", "—"])
    if not rows:
        return None
    return {"title": "Technical appendix",
            "table": {"columns": ["Quantity", "Formula", "Units", "Sign convention"],
                      "rows": rows}}


def graded_count(source: Optional[str], db_path: Optional[str] = None) -> int:
    """Scorecard-graded instances of a classification: resolved ledger rows
    under its `graded_source`. None -> 0, never guessed."""
    if not source:
        return 0
    try:
        from altdata import probability_ledger as pl            # noqa: PLC0415
        with pl.ProbabilityLedger(db_path) as led:
            return sum(1 for r in led.all_rows()
                       if r.get("source") == source and r.get("resolved_at"))
    except Exception:                                           # noqa: BLE001
        return 0


def classifications(cfg: dict, db_path: Optional[str] = None) -> list[dict]:
    """Each declared descriptive classification with its n."""
    return [{**c, "n": graded_count(c.get("graded_source"), db_path)}
            for c in cfg.get("descriptive_classifications") or []]


def unvalidated_notes(sections: list[dict], classes: list[dict]) -> None:
    """One footnote per section that prints a descriptive classification."""
    for s in sections:
        mine = [c for c in classes if s.get("id") in (c.get("sections") or [])]
        if not mine:
            continue
        ns = {c["n"] for c in mine}
        if len(ns) == 1:
            text = (_join([c["label"] for c in mine]).capitalize()
                    + f": {unvalidated_tag(ns.pop())}.")
        else:
            text = "; ".join(f"{c['label']} {unvalidated_tag(c['n'])}"
                             for c in mine).capitalize() + "."
        s.setdefault("notes", []).append(text)


def unvalidated_glossary(classes: list[dict]) -> list[dict]:
    return [{"term": c["label"].removeprefix("the "),
             "text": ((f"a validated signal: computed by a declared rule and graded "
                       f"against what followed {unvalidated_tag(c['n'])}; n counts "
                       f"the scorecard's graded instances.")
                      if c["n"] >= validated_min_n() else
                      (f"a descriptive classification, computed by a declared rule "
                       f"and not yet graded against what followed "
                       f"{unvalidated_tag(c['n'])}; n counts the scorecard's graded "
                       f"instances."))}
            for c in classes]


def _join(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


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
    # ONE CONVENTION FOR THE WEEK'S RETURN (W-1.1 item 1.1). The 9 Oct edition
    # printed SPY +1.16% in the tape and +1.17% here: this table compounded each
    # session's overnight and intraday returns AFTER rounding them to two
    # decimals, and the rounding drifted a hundredth. The week is now the tape's
    # convention -- the last close over the prior week's last close, from the same
    # daily bars -- and the overnight and intraday legs compound unrounded.
    out, on_tot, id_tot = [], 1.0, 1.0
    first_prior = last_close = None
    for d in days:
        i = allc.index(d)
        if i == 0:
            continue
        prior = rows[i - 1]["close"]
        o, c = by[d]["open"], by[d]["close"]
        if None in (o, c, prior) or not o or not prior:
            continue
        on, intr, cc = _ret(o, prior), _ret(c, o), _ret(c, prior)
        on_tot *= o / prior
        id_tot *= c / o
        first_prior = prior if first_prior is None else first_prior
        last_close = c
        out.append({"day": d, "overnight_pct": on, "intraday_pct": intr,
                    "close_to_close_pct": cc})
    totals = ({"overnight_pct": round(100 * (on_tot - 1), 2),
               "intraday_pct": round(100 * (id_tot - 1), 2),
               "close_to_close_pct": _ret(last_close, first_prior)}
              if out else None)
    table = {"columns": ["Session", "Overnight", "Intraday", "Close to close"],
             "rows": [[_day(r["day"]), _signed(r["overnight_pct"], "%"),
                       _signed(r["intraday_pct"], "%"),
                       _signed(r["close_to_close_pct"], "%")] for r in out]
             + ([["The week", _signed(totals["overnight_pct"], "%"),
                  _signed(totals["intraday_pct"], "%"),
                  _signed(totals.get("close_to_close_pct"), "%")]] if totals else [])}
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


def _bn_change(v: Optional[float], scale: float = 1.0) -> str:
    """A signed dollar change: +$13bn, −$28bn."""
    if v is None:
        return "—"
    x = v * scale
    sign = "+" if x >= 0 else "−"
    return sign + _bn(abs(x))


# THE AUCTION'S FIELDS (W-1.1 item 1.4, ruled 11 Oct 2026). Each of the week's
# coupon auctions with its bid-to-cover and its indirect, direct and dealer shares
# of competitive accepted -- the writer's fields, altdata/sources/treasury_auctions
# -- each beside its percentile among the same security's auctions over the
# trailing two years. THE TAIL: high yield less the when-issued yield at the
# bid deadline. TreasuryDirect does not publish the when-issued yield and no free
# source serves it, so `auction.tail_bp` is registered and not sourced; the table
# prints "not stored", and the prose may say "tail" only where a stored tail is
# positive (stack_prose.tail_faults). Nothing here approximates one.
AUCTION_FIELDS = (("auction.bid_to_cover", "bid_to_cover"),
                  ("auction.indirect_share", "indirect"),
                  ("auction.direct_share", "direct"),
                  ("auction.dealer_share", "dealer"),
                  ("auction.tail_bp", "tail_bp"))
AUCTION_PCT_DAYS = 730


def auction_records(st, now: str, then: str) -> list[dict]:
    """The period's coupon auctions, each field with its two-year percentile."""
    from altdata import derived                                 # noqa: PLC0415
    out = []
    for r in coupon_auctions(st, now):
        d = str(r["observed_at"])[:10]
        inst = str(r.get("instrument") or "")
        if not (then[:10] < d <= now[:10]) or inst.split(":")[0] not in ("Note", "Bond", "TIPS"):
            continue
        rec = {"date": d, "instrument": inst, "high_yield": r["value_num"]}
        lo = (dt.date.fromisoformat(d) - dt.timedelta(days=AUCTION_PCT_DAYS)).isoformat()
        for key, f in AUCTION_FIELDS:
            hist = [(str(x["observed_at"])[:10], x["value_num"])
                    for x in st.as_of(key, now, inst) or []
                    if x.get("value_num") is not None]
            today = [v for day, v in hist if day == d]
            rec[f] = today[-1] if today else None
            past = [v for day, v in hist if lo <= day <= d]
            rec[f"{f}_percentile_2y"] = (round(derived.percentile_of(past, rec[f]))
                                         if rec[f] is not None and len(past) >= 5
                                         else None)
            rec[f"{f}_n_2y"] = len(past)
        out.append(rec)
    return out


def _with_pct(v: Optional[str], p: Optional[float]) -> str:
    if v is None:
        return "—"
    if p is None:
        return v
    # W-1.3c item 7: the shared helper, half up (int() truncated 88.7 to 88th).
    from altdata.numeral_audit import ordinal                     # noqa: PLC0415
    return f"{v} ({ordinal(p)})"


def auction_table(recs: list[dict]) -> dict:
    """One row per auction: the security, high yield and date; bid-to-cover; the
    three shares; the tail -- each figure with its two-year percentile."""
    rows = []
    for a in recs:
        typ, term = a["instrument"].split(":", 1)
        rows.append([f"{term} {typ.lower()} ({a['date']}), high yield "
                     f"{a['high_yield']:.3f}%",
                     _with_pct(None if a["bid_to_cover"] is None
                               else f"{a['bid_to_cover']:.2f}",
                               a["bid_to_cover_percentile_2y"]),
                     _with_pct(None if a["indirect"] is None
                               else f"{100 * a['indirect']:.1f}%",
                               a["indirect_percentile_2y"]),
                     _with_pct(None if a["direct"] is None
                               else f"{100 * a['direct']:.1f}%",
                               a["direct_percentile_2y"]),
                     _with_pct(None if a["dealer"] is None
                               else f"{100 * a['dealer']:.1f}%",
                               a["dealer_percentile_2y"]),
                     ("not stored" if a["tail_bp"] is None else
                      _with_pct(f"{a['tail_bp']:+.1f} bp", a["tail_bp_percentile_2y"]))])
    return {"columns": ["Auction", "Bid-to-cover", "Indirect", "Direct", "Dealers",
                        "Tail vs when-issued"], "rows": rows}


AUCTION_NOTE = ("Each figure's percentile is among the same security's auctions over "
                "the trailing two years. Shares are of competitive accepted. The tail "
                "needs the when-issued yield, which no free source publishes.")


def aligned_legs(st, k1: str, k2: str, now: str, then: str
                 ) -> tuple[tuple, tuple, Optional[str]]:
    """((leg1, leg2) now, (leg1, leg2) at `then`, the date both share now): each
    pair read on the latest date both legs have on or before the cutoff --
    never one leg's Friday against the other's Wednesday."""
    def at(cut):
        a = {str(r["observed_at"])[:10]: r["value_num"] for r in st.as_of(k1, cut)
             if r.get("value_num") is not None}
        b = {str(r["observed_at"])[:10]: r["value_num"] for r in st.as_of(k2, cut)
             if r.get("value_num") is not None}
        common = sorted(set(a) & set(b))
        if not common:
            return (None, None), None
        d = common[-1]
        return (a[d], b[d]), d
    cur, day = at(now)
    prior, _ = at(then)
    return cur, prior, day


def plumbing_rows(st, now: str, then: str, cadence: str = "weekly",
                  liquidity_deltas: bool = False,
                  auctions_in_table: bool = True) -> dict:
    """Item 3: net liquidity and its legs, SOFR against IORB, the credit
    spreads beside HY, the week's auctions, copper and gold/copper. Rows for
    Plumbing's table; each figure from the store with its as-of.

    `liquidity_deltas` (the Monthly's, T3.2 item 4): the change column of net
    liquidity and each H.4.1 leg is a level difference the reader needs, so it
    rides in `data["liquidity"]` as a figure in dollars with its signed form --
    the one the table prints -- for the writer to copy."""
    from altdata import derived                                 # noqa: PLC0415
    rows, data, nt = [], {}, []
    liq: list[dict] = []

    def delta(name, level, change, scale, asof):
        if liquidity_deltas and change is not None:
            liq.append({"series": name, "level_display": _bn(level, scale),
                        "change_dollars": change * scale,
                        "change_dollars_signed": _bn_change(change, scale),
                        "as_of": asof})

    def two(key, inst=None):
        a = st.latest_as_of(key, now, inst)
        b = st.latest_as_of(key, then, inst)
        return (a.get("value_num") if a else None, b.get("value_num") if b else None,
                str(a["observed_at"])[:10] if a else None)

    def pair(k1, k2):
        """BOTH LEGS AT ONE AS-OF (W-1.1a item 6): a derived series -- SOFR less
        IORB, CCC less BB, gold over copper -- takes each leg on the latest date
        both legs have, now and at the period's start, and prints that date. The
        12 Oct dry run's CCC and BB, SOFR and IORB could each sit on their own
        latest day."""
        return aligned_legs(st, k1, k2, now, then)
    nl, nlp, nla = two("calc.net_liquidity")
    if nl is not None:
        rows.append(["Net liquidity (Fed balance sheet less TGA and RRP)", _bn(nl),
                     (_bn_change(nl - nlp) if nlp is not None else "no prior"), nla])
        data["net_liquidity"] = {"level": nl, "week_change": None if nlp is None
                                 else nl - nlp, "as_of": nla}
        delta("Net liquidity (Fed balance sheet less TGA and RRP)", nl,
              None if nlp is None else nl - nlp, 1.0, nla)
    else:
        nt.append("net liquidity")
    # H.4.1 legs: reserves and TGA in millions, RRP in billions (CLAUDE.md gotcha;
    # WRESBAL was declared "B" until the first live render read $2,948tn).
    for key, name, scale in (("fred.bank_reserves", "Bank reserves (H.4.1)", 1e6),
                             ("fred.tga", "Treasury General Account (H.4.1)", 1e6),
                             ("fred.rrp", "Reverse repo (RRP)", 1e9)):
        v, pv, asof = two(key)
        if v is None:
            nt.append(name)
            continue
        rows.append([name, _bn(v, scale), _bn_change(v - pv, scale)
                     if pv is not None else "no prior", asof])
        delta(name, v, None if pv is None else v - pv, scale, asof)
    so, sop, soa = two("fred.sofr")
    io, iop, ioa = two("fred.iorb")
    (so2, io2), (sop2, iop2), sio_asof = pair("fred.sofr", "fred.iorb")
    if so is not None and io is not None:
        sp = round((so - io) * 100)
        spp = round((sop - iop) * 100) if None not in (sop, iop) else None
        rows.append(["SOFR", f"{so:.2f}%", _signed(None if sop is None else
                                                   round((so - sop) * 100), "bp"), soa])
        rows.append(["IORB", f"{io:.2f}%", _signed(None if iop is None else
                                                   round((io - iop) * 100), "bp"), ioa])
        if so2 is not None and io2 is not None:
            sp = round((so2 - io2) * 100)
            spp = (round((sop2 - iop2) * 100) if None not in (sop2, iop2) else None)
        rows.append(["SOFR less IORB (funding pressure when above zero)",
                     f"{sp:+d} bp", _signed(None if spp is None else sp - spp, "bp"),
                     sio_asof or soa])
        data["sofr_iorb_bp"] = sp
    else:
        nt.append("SOFR and IORB (the FRED pull adds them from the next run)")
    for key, name in (("fred.ig_oas", "Investment-grade OAS"),
                      ("fred.ccc_oas", "CCC OAS")):
        v, pv, asof = two(key)
        if v is not None:
            rows.append([name, f"{v:.2f}%", _signed(None if pv is None else
                                                    round((v - pv) * 100), "bp"), asof])
    (ccc, bb), (cccp, bbp), ccca = pair("fred.ccc_oas", "fred.bb_oas")
    if None not in (ccc, bb):
        gap = round((ccc - bb) * 100)
        gp = round((cccp - bbp) * 100) if None not in (cccp, bbp) else None
        rows.append(["CCC less BB (stress inside high yield)", f"{gap:,d} bp",
                     _signed(None if gp is None else gap - gp, "bp"), ccca])
    cu, cup, cua = two("yfinance.mkt_copper_front")
    au, aup, _ = two("yfinance.mkt_gold_front")
    if cu is not None:
        # IN DOLLARS, AS THE LABEL SAYS (T3.3 item 6): the bare "6.710" typed
        # as a count in the audit, while the prose wrote "$6.710 per pound".
        rows.append(["Copper, front future ($/lb; a growth gauge)", f"${cu:,.3f}",
                     _signed(_ret(cu, cup), "%") if cup else "no prior", cua])
        (au2, cu2), (aup2, cup2), gc_asof = pair("yfinance.mkt_gold_front",
                                                 "yfinance.mkt_copper_front")
        if au2 is not None and cu2:
            r = au2 / cu2
            rp = (aup2 / cup2) if None not in (aup2, cup2) and cup2 else None
            rows.append(["Gold over copper (rises when growth fears rise)",
                         f"{r:,.0f}", _signed(_ret(r, rp), "%") if rp else "no prior",
                         gc_asof])
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
    if not auctions_in_table:
        # The Weekly prints the auctions in their own table (W-1.1 item 1.4).
        rows = [r for r in rows if " auction (" not in str(r[0])]
    if not auctions:
        rows.append([f"Treasury coupon auctions {Period.of(cadence).this}", "none held",
                     "—", "—"])
    data["auctions"] = auctions
    if liquidity_deltas:
        data["liquidity"] = liq
    return {"rows": rows, "data": data, "not_tracked": nt}


def global_fx(st, now: str, then: str, cadence: str = "weekly") -> dict:
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
        rows.append([name, with_stale(f"{a['value_num']:,.{dp}f}",
                                      str(a["observed_at"])[:10], edition_session(now)),
                     _signed(_ret(a["value_num"], b["value_num"]), "%") if b
                     else "no prior", str(a["observed_at"])[:10]])
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
            "table": {"columns": ["Series", "Level", Period.of(cadence).col, "As of"],
                      "rows": rows},
            "not_tracked": nt}


def volatility(st, now: str, wis: Optional[dict] = None,
               then: Optional[str] = None) -> dict:
    """Item 5: the 'Volatility' sub-section of Mechanics -- six rows. With `then`
    (W-1.1 item 1.0a) a fourth column carries each level's change over the
    period, so Mechanics' frame can rank the VIX, realized, SKEW and MOVE moves."""
    from altdata import derived                                 # noqa: PLC0415
    five = (dt.date.fromisoformat(now[:10]) - dt.timedelta(days=1826)).isoformat()

    def wk(key: str, pct_scale: bool = False) -> str:
        if not then:
            return "—"
        a, b = st.latest_as_of(key, now), st.latest_as_of(key, then)
        if not a or not b or a.get("value_num") is None or b.get("value_num") is None \
                or str(a["observed_at"]) == str(b["observed_at"]):
            return "—"
        d = a["value_num"] - b["value_num"]
        if pct_scale and abs(a["value_num"]) < 3:
            d *= 100.0                        # realized stored as a fraction
        d = round(d, 1)
        return f"{'+' if d > 0 else ('−' if d < 0 else '')}{abs(d):.1f} pts"
    vix_hist = [v for d, v in _closes_of(st, "yfinance.mkt_vix", now) if d >= five]
    vix = vix_hist[-1] if vix_hist else None
    rows, data = [], {}
    if vix is not None:
        pct = derived.percentile_of(vix_hist, vix) if len(vix_hist) > 20 else None
        rows.append(["VIX", f"{vix:.2f}",
                     f"{na_ordinal(pct)} percentile, five years" if pct is not None else "—",
                     wk("yfinance.mkt_vix")])
        data["vix"] = vix
        data["vix_percentile_5y"] = None if pct is None else round(pct)
    vts = (wis or {}).get("vol_term_structure") or {}
    pub = vts.get(vts.get("published_by") or "") or {}
    if pub.get("ratio") is not None:
        rows.append(["VIX3M over VIX (term structure, published)",
                     f"{float(pub['ratio']):.2f}", str(pub.get("state") or "—"), "—"])
    rv = st.latest_as_of("calc.vol_spy_realized_20d", now)
    rvv = rv.get("value_num") if rv else None
    if rvv is not None and rvv < 3:
        rvv = rvv * 100.0                     # stored as a fraction
    if rvv is not None and vix is not None:
        rows.append(["SPY 20-day realized against the VIX", f"{rvv:.1f} vs {vix:.1f}",
                     f"implied {'above' if vix > rvv else 'below'} realized by "
                     f"{abs(vix - rvv):.1f} points", wk("calc.vol_spy_realized_20d", True)])
        data["implied_daily_move_pct"] = round(vix / 252 ** 0.5, 2)
        data["realized_daily_move_pct"] = round(rvv / 252 ** 0.5, 2)
        rows.append(["Daily move priced, and realized",
                     f"{data['implied_daily_move_pct']:.2f}% priced",
                     f"{data['realized_daily_move_pct']:.2f}% realized", "—"])
    for key, name in (("yfinance.mkt_move", "MOVE (Treasury volatility)"),
                      ("yfinance.mkt_skew", "SKEW (tail-risk pricing)")):
        a = st.latest_as_of(key, now)
        rows.append([name, f"{a['value_num']:.1f}" if a else "—",
                     str(a["observed_at"])[:10] if a else "not yet stored", wk(key)])
    cols = ["Measure", "Level", "Context"] + ([Period.of("weekly").col] if then else [])
    return {"title": "Volatility",
            "table": {"columns": cols, "rows": [r[:len(cols)] for r in rows[:6]]},
            "data": data}


def sector_table(st, now: str, then: str, lead: list,
                 cadence: str = "weekly") -> dict:
    """Item 6: the week, one month and three months beside each other, and how
    many sectors sit above their 50- and 200-day averages.

    AT THE MONTHLY'S CADENCE (T3.1 item 9, ruled 9 Oct 2026): the month, three
    months and twelve months. "One month" -- the trailing 22 sessions -- is
    dropped there, because at month-end it is the month a second time."""
    from altdata import labels                                  # noqa: PLC0415
    from altdata.sources.yfinance_source import SECTOR_KEYS     # noqa: PLC0415
    monthly = cadence == "monthly"
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
        if monthly:
            m1, m3 = m3, (vals[-253] if len(vals) > 253 else None)
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
    later = ["Three months", "Twelve months"] if monthly else ["One month",
                                                                 "Three months"]
    return {"table": {"columns": ["Sector or pair", Period.of(cadence).col, *later],
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


def reading_minutes(ed: dict, charts: int) -> int:
    """Item 7: prose words / 250 plus 20 seconds a chart, in whole minutes
    rounded up (T2.5 item 6) -- readability.reading_minutes is the one rule."""
    from .readability import reading_minutes as rm             # noqa: PLC0415
    return rm(ed, charts)


EARNINGS_SEASONS = ((1, 10, 2, 28), (4, 10, 5, 31), (7, 10, 8, 31), (10, 10, 11, 30))


def seasons_from_config() -> tuple:
    try:
        return tuple((x["from"][0], x["from"][1], x["to"][0], x["to"][1])
                     for x in load_calendar().get("earnings_seasons") or []) \
            or EARNINGS_SEASONS
    except Exception:                                           # noqa: BLE001
        return EARNINGS_SEASONS


def in_season(day: str, seasons: Optional[tuple] = None) -> bool:
    seasons = seasons or seasons_from_config()
    d = dt.date.fromisoformat(day[:10])
    for m1, d1, m2, d2 in seasons:
        if dt.date(d.year, m1, d1) <= d <= dt.date(d.year, m2, d2):
            return True
    return False


SEASON_DAYS = 7


def earnings_season(st, ending: str, now: str) -> dict:
    """In season or not, from the stored dates (T2.3 rulings of 5 Oct, item 1):
    in season when any universe name has a confirmed earnings date within seven
    days of the week's end -- either side, so the week a season's last names
    report still prints them -- or a reported result inside that span, which is
    a date that happened. The fixed windows in release_calendar.yaml decide only
    when no earnings date is stored at all."""
    from altdata import events                                  # noqa: PLC0415
    d = dt.date.fromisoformat(ending[:10])
    lo = (d - dt.timedelta(days=SEASON_DAYS)).isoformat()
    hi = (d + dt.timedelta(days=SEASON_DAYS)).isoformat() + "T23:59:59"
    try:
        with events.EventStore(str(st.path)) as ev:
            stored = ev.conn.execute(
                "SELECT COUNT(*) FROM events WHERE available_at <= ? AND "
                "(type = 'earnings' OR (type = 'scheduled' AND "
                "json_extract(payload, '$.kind') = 'earnings'))", (now,)).fetchone()[0]
            near = ev.conn.execute(
                "SELECT DISTINCT json_extract(payload, '$.symbol') FROM events "
                "WHERE available_at <= ? AND observed_at >= ? AND observed_at <= ? "
                "AND (type = 'earnings' OR (type = 'scheduled' AND "
                "json_extract(payload, '$.kind') = 'earnings' AND "
                "json_extract(payload, '$.date_confirmed') = 1))",
                (now, lo, hi)).fetchall()
    except Exception:                                           # noqa: BLE001
        stored, near = 0, []
    if not stored:
        return {"in_season": in_season(ending), "basis": "fixed windows (no "
                "earnings date stored)", "names": []}
    names = sorted(str(r[0]) for r in near if r[0])
    return {"in_season": bool(names), "basis": f"confirmed dates within "
            f"{SEASON_DAYS} days of {ending[:10]}", "names": names}


def earnings_block(st, ending: str, now: str, then: str,
                   seasons: Optional[tuple] = None,
                   cadence: str = "weekly") -> Optional[dict]:
    """Item 9: universe names that reported this week -- EPS and revenue against
    stored consensus, beat or miss, the next day's reaction from stored prices.
    None outside the season (prints nothing); inside it, 'no universe name
    reported' when none did. `seasons` forces the fixed windows (a test's
    switch); otherwise the season comes from the stored dates."""
    if seasons is not None:
        if not in_season(ending, seasons):
            return None
    elif not earnings_season(st, ending, now)["in_season"]:
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
    w = Period.of(cadence)
    return {"title": f"Earnings {w.this}",
            "table": {"columns": ["Name", "EPS against consensus", "Verdict", "Revenue",
                                  "Next day", "Reported"], "rows": rows},
            "lines": [] if rows else [f"No universe name reported {w.this}."],
            "data": data}
