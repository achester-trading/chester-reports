"""
AHEAD AS THE MARKET-MOVING CALENDAR (W-1.3a item 3.9; change order of 11 Oct
2026, section 4, amended 12 Oct -- "the Ahead should summarise all notable
upcoming events which may move markets"; upcoming earnings were missing from the
9 Oct edition).

    from daily_cascade import ahead
    a = ahead.build(cal, p, positioning_data, now)
    a["table"], a["rows"], a["top"], a["reference"], a["notes"]

ONE RANKED TABLE for the coming week, one line an event: what, when (ET), the
consensus or modal outcome where one exists, why it matters (the event class's
transmission channel) and the positioning that would amplify a surprise (the
class's amplifiers, read from the Positioning section's CFTC extremes). Every
input is stored or declared; nothing is fetched and the model ranks nothing.

  data releases, FOMC decisions and minutes, the Fed's speakers, coupon auctions,
  option expiries              daily_cascade/weekly_sections.calendar_week, each
                               row carrying its class
  EARNINGS                     the events table's scheduled earnings (the earnings
                               pass reads the tracked universe AND the
                               index-weight list), classed mega / bank / index /
                               tracked by config; consensus EPS where carried; the
                               option-implied move from the chain store where a
                               chain is captured, else "not captured"
  prediction-market resolutions  collapsed by family to the modal outcome; every
                               outcome in the reference tables
  index rebalances             the session calendar's declared classes
  political and geopolitical   the hand-seeded calendars (EM, China, Thailand)
                               and the claims register's dated events

RANKING is the class's importance tier (config/weekly_ahead.yaml), then the
time. The rank-1 event keeps the PLAYBOOK slot (item 3.5; W-1.3b fills it).
ROUTINE data releases and bill auctions go to the reference tables, counted.
"""

from __future__ import annotations

import datetime as dt
import logging
import math
import re
from pathlib import Path
from typing import Any, Optional

import yaml

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "weekly_ahead.yaml"
NOT_CAPTURED = "implied move not captured"
ODDS_NOT_STORED = "odds not stored"
# Six columns, the edition's widest (T2.5 item 10): the day and the time share one.
COLUMNS = ["When (ET)", "Event", "Importance", "Consensus / modal",
           "Why it matters", "Positioning that would amplify a surprise"]
REBALANCE_CLASSES = ("INDEX_REBALANCE", "ETF_REBALANCE")


def load_config(path: Optional[Path] = None) -> dict:
    try:
        with open(path or CONFIG_PATH, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except OSError:
        return {}


def _day(d: str) -> str:
    x = dt.date.fromisoformat(d[:10])
    return f"{x:%a} {x.day} {x:%b}"


# ---------------------------------------------------------------------------
# Earnings
# ---------------------------------------------------------------------------
def earnings_class(symbol: str, cfg: dict) -> str:
    e = cfg.get("earnings") or {}
    sym = str(symbol).upper()
    ranks = [str(s).upper() for s in e.get("index_weight_rank") or []]
    if sym in {str(s).upper() for s in e.get("hyperscalers") or []} or \
            (sym in ranks and ranks.index(sym) < int(e.get("mega_ranks") or 10)):
        return "earnings_mega"
    if sym in {str(s).upper() for s in e.get("banks") or []}:
        return "earnings_bank"
    if sym in ranks:
        return "earnings_index"
    return "earnings_tracked"


def ai_names(cfg: dict, repo: Optional[Path] = None) -> set[str]:
    """The names the AI-capex clause applies to (W8-6): every symbol listed under
    any bucket of config/ai_buckets.yaml, with the Weekly's own
    `earnings.ai_names`."""
    p = (repo or REPO) / "config" / "ai_buckets.yaml"
    out: set[str] = set()
    if p.exists():
        try:
            doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

            def walk(x):
                if isinstance(x, dict):
                    for v in x.values():
                        walk(v)
                elif isinstance(x, list):
                    for v in x:
                        walk(v)
                elif isinstance(x, str) and re.fullmatch(r"[A-Z][A-Z.\-]{0,5}", x):
                    out.add(x)
            walk(doc.get("buckets", doc))
        except (OSError, yaml.YAMLError):
            log.warning("config/ai_buckets.yaml unreadable; the Weekly's AI names stand")
    # GTM-4 names members for the hyperscalers only (its other buckets are GICS
    # industries the store cannot classify), so its members join the Weekly's
    # own list rather than replace it (the chain-2 stitch, 19 Oct 2026).
    return out | {str(s).upper() for s in (cfg.get("earnings") or {}).get("ai_names") or []}


def why_of(r: dict, c: dict, ai: set[str]) -> str:
    """A row's "why it matters": its class's channel, with the class's AI clause
    only for an AI name (W8-6: "its capital spending is the AI trade's" printed
    for TSLA)."""
    why = c.get("channel") or "—"
    sym = str(r.get("symbol") or str(r.get("event") or "").split(" ")[0]).upper()
    if c.get("ai_clause") and r.get("cls", "").startswith("earnings") and sym in ai:
        why += c["ai_clause"]
    # A register row's base rate prints beside its channel (Batch 16 item 90).
    if r.get("base_rate"):
        why += ". " + str(r["base_rate"])
    return why


def _mid(r: dict) -> Optional[float]:
    b, a = r.get("bid"), r.get("ask")
    if b is not None and a is not None and a >= b > 0:
        return (a + b) / 2
    return None


_BEFORE_OPEN = re.compile(r"before\s+(?:the\s+)?(?:open|bell)|pre-?market|\bbmo\b", re.I)


def before_open(time: Optional[str]) -> bool:
    """Is the release stated to land before the open (09:30 ET)? An unknown
    time is not."""
    t = str(time or "")
    if _BEFORE_OPEN.search(t):
        return True
    m = re.match(r"\s*(\d{1,2}):(\d{2})", t)
    return bool(m) and (int(m.group(1)), int(m.group(2))) < (9, 30)


def straddle_expiry(expiries, event_date: str,
                    time: Optional[str] = None) -> Optional[str]:
    """The expiry an event's straddle is read to (W8-5, weekly-fixes-8): the first
    expiry STRICTLY AFTER the event date whenever the release time is unknown or
    after the close -- an expiry on the event day itself settles before an
    after-close report (META, Wed 21 Oct, was read to the 21 Oct expiry) -- and
    the event date's own expiry only for a release before the open."""
    d = str(event_date)[:10]
    ok = sorted(str(e) for e in expiries
                if (str(e) >= d if before_open(time) else str(e) > d))
    return ok[0] if ok else None


STRADDLE_K = math.sqrt(2.0 / math.pi)   # straddle / spot = this x sigma x sqrt(T)


def atm_straddle(rows: list[dict], ex: str) -> Optional[tuple[float, float]]:
    """(the at-the-money straddle's mid, spot) on expiry `ex`, or None."""
    leg = [r for r in rows if str(r.get("expiry")) == ex]
    spot = next((r["spot"] for r in leg if r.get("spot")), None)
    if not spot:
        return None
    by: dict[float, dict] = {}
    for r in leg:
        if r.get("strike") is not None and _mid(r) is not None:
            by.setdefault(r["strike"], {})[r["right"]] = _mid(r)
    both = [k for k, v in by.items() if "C" in v and "P" in v]
    if not both:
        return None
    atm = min(both, key=lambda k: abs(k - spot))
    return by[atm]["C"] + by[atm]["P"], float(spot)


def event_move(pre_frac: float, pre_days: int, post_frac: float,
               post_days: int) -> Optional[float]:
    """The event-only move, percent, on the straddle convention: each straddle's
    fraction of spot is turned into total variance ((frac / sqrt(2/pi))^2), the
    pre-event expiry's variance RATE is applied over the post-event expiry's time,
    and the remainder, if positive, is turned back into a straddle fraction."""
    if pre_days <= 0 or post_days <= pre_days:
        return None
    v_post = (post_frac / STRADDLE_K) ** 2
    rate_pre = (pre_frac / STRADDLE_K) ** 2 / (pre_days / 365.0)
    ev = v_post - rate_pre * (post_days / 365.0)
    if ev <= 0:
        return None
    return 100.0 * STRADDLE_K * math.sqrt(ev)


def implied_move(symbol: str, report_date: str, now: str,
                 base: Optional[Path] = None, days_back: int = 5,
                 time: Optional[str] = None) -> Optional[str]:
    """The option-implied move into a report: the at-the-money straddle's mid to
    the event's expiry (`straddle_expiry`: strictly after the report date unless
    the release is before the open), over spot, from the newest captured chain
    of `symbol` at or before `now` (looking back `days_back` days). None when no
    chain is captured."""
    try:
        from altdata import chain_metrics                       # noqa: PLC0415
        root = Path(base) if base else chain_metrics.chain_dir()
        d0 = dt.date.fromisoformat(now[:10])
        for k in range(days_back + 1):
            day = (d0 - dt.timedelta(days=k)).isoformat()
            files = sorted(p for p in (root / day).glob(f"{symbol.upper()}_*.csv")
                           if "_quality" not in p.name) if (root / day).is_dir() else []
            if not files:
                continue
            rows = chain_metrics.load_rows(files[-1])
            ex = straddle_expiry({str(r["expiry"]) for r in rows if r.get("expiry")},
                                 report_date, time)
            if not ex:
                return None
            post = atm_straddle(rows, ex)
            if not post:
                return None
            strad, spot = post
            mv = 100.0 * strad / spot
            # BATCH 11 ITEM 57 (ruled 19 Oct 2026): THE EVENT-ONLY MOVE, where an
            # expiry before the report exists -- the expiry before the post-event
            # one, which settles before the report. On the straddle convention
            # (straddle / spot = sqrt(2/pi) x sigma x sqrt(T)): the post-event
            # expiry's total variance less the pre-event expiry's variance rate
            # over the same time; else the full straddle, labelled.
            pre_ex = max((str(r["expiry"]) for r in rows if r.get("expiry")
                          and str(r["expiry"]) < ex
                          and str(r["expiry"])[:10] > day), default=None)
            pre = atm_straddle(rows, pre_ex) if pre_ex else None
            if pre:
                ev = event_move(pre[0] / pre[1], (dt.date.fromisoformat(pre_ex[:10])
                                                   - dt.date.fromisoformat(day)).days,
                                strad / spot, (dt.date.fromisoformat(ex[:10])
                                               - dt.date.fromisoformat(day)).days)
                if ev is not None:
                    return (f"implied move ±{ev:.1f}% (event-only: the straddle to {ex} "
                            f"less the {pre_ex} expiry's variance rate over the same time)")
            return f"implied move ±{mv:.1f}% (straddle to {ex}; includes non-event days)"
    except Exception:                                           # noqa: BLE001
        log.warning("implied move unavailable for %s", symbol, exc_info=True)
    return None


def earnings_row(r: dict, cfg: dict, now: str, chain_base: Optional[Path]) -> dict:
    sym = r.get("symbol") or str(r["event"]).split()[0]
    eps = r.get("eps_estimate")
    cons = (f"EPS {eps:.2f} (analyst mean)" if isinstance(eps, (int, float))
            else "no consensus EPS carried")
    mv = implied_move(sym, r["date"], now, chain_base, time=r.get("time")) or NOT_CAPTURED
    return {**r, "cls": earnings_class(sym, cfg), "consensus": f"{cons}; {mv}",
            "implied_move": None if mv == NOT_CAPTURED else mv}


# ---------------------------------------------------------------------------
# The hand-seeded calendars and the register's dated events
# ---------------------------------------------------------------------------
def hand_rows(cfg: dict, mon: dt.date, sat: dt.date,
              repo: Optional[Path] = None) -> tuple[list[dict], list[str]]:
    rows, absent = [], []
    for hc in cfg.get("hand_calendars") or []:
        p = (repo or REPO) / hc["path"]
        if not p.exists():
            absent.append(Path(hc["path"]).name)
            continue
        try:
            entries = (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) \
                .get("entries") or []
        except (OSError, yaml.YAMLError):
            absent.append(Path(hc["path"]).name)
            continue
        for e in entries:
            try:
                d = dt.date.fromisoformat(str(e.get("date"))[:10])
            except ValueError:
                continue
            if mon <= d < sat:
                who = e.get(hc.get("who") or "body") or e.get("country") or e.get("body")
                ev = f"{who}: {e.get('event')}" if who else str(e.get("event"))
                # A DATE NOT YET CONFIRMED AT ITS SOURCE carries its marker
                # ("30 Nov, to verify on MSCI's calendar"; Batch 8 item 49c).
                if e.get("marker"):
                    ev += f" ({e['marker']})"
                rows.append({"date": d.isoformat(),
                             "time": str(e.get("time") or "time not stated"),
                             "event": ev,
                             "consensus": "—", "cls": hc["class"],
                             "source": e.get("source")})
    return rows, absent


def odds_line(watch_ids: list, db_path: Optional[str],
              now: Optional[str] = None) -> str:
    """The control-of-Congress odds as the row's consensus (Batch 16 items 80(b)
    and 90): each watched question's stored probability for its declared side,
    per venue, at the run's cutoff. Read from the store the Weekly opened; never
    fetched, and "odds not stored" when it holds none."""
    if not db_path or not watch_ids:
        return ODDS_NOT_STORED
    try:
        from altdata import observations                        # noqa: PLC0415
        from altdata import prediction_markets as pm            # noqa: PLC0415
        from altdata.sources import prediction_markets as src   # noqa: PLC0415
        watch = {w.get("id"): w for w in src.load_config().get("watch_list") or []}
        st = observations.ObservationStore(db_path)
        try:
            mks = pm.load(st, now)
        finally:
            st.close()
    except Exception:                                           # noqa: BLE001
        log.warning("the Ahead row's odds are unavailable", exc_info=True)
        return ODDS_NOT_STORED
    parts, newest, seen = [], None, False
    for wid in watch_ids:
        w = watch.get(wid) or {}
        # The declared side's stem ("Democratic Party" -> "democrat") names the
        # outcome on both venues, whose own labels differ.
        stem = str(w.get("side") or "").split(" ")[0].lower()[:8]
        venues = []
        for v, name in (("kalshi", "Kalshi"), ("polymarket", "Polymarket")):
            last = None
            for m in mks:
                label = f"{m.get('outcome') or ''} {m.get('question') or ''}".lower()
                if m.get("watch_id") != wid or m.get("venue") != v or \
                        not stem or stem not in label:
                    continue
                for r in m.get("history") or []:
                    if r.get("value_num") is not None and \
                            (last is None or str(r["available_at"]) > last[1]):
                        last = (float(r["value_num"]), str(r["available_at"]))
            if last is None:
                venues.append(f"{name} not stored")
                continue
            seen = True
            newest = max(newest or last[1], last[1])
            venues.append(f"{name} {100.0 * last[0]:.0f}%")
        parts.append(f"{w.get('subject') or wid}: " + ", ".join(venues))
    if not seen:
        return ODDS_NOT_STORED
    return "; ".join(parts) + f" (as of {newest[:10]})"


def register_rows(cfg: dict, mon: dt.date, sat: dt.date,
                  db_path: Optional[str] = None,
                  now: Optional[str] = None) -> list[dict]:
    out = []
    try:
        from altdata import claims                              # noqa: PLC0415
    except Exception:                                           # noqa: BLE001
        return out
    named = cfg.get("register_event_rows") or {}
    for cid in cfg.get("register_events") or []:
        try:
            c = claims.cite(cid)
            d = dt.date.fromisoformat(str(c.get("value"))[:10])
        except Exception:                                       # noqa: BLE001
            continue
        if mon <= d < sat:
            row = {"date": d.isoformat(), "time": "time not stated",
                   "event": str(c.get("unit") or cid).capitalize(),
                   "consensus": "—", "cls": "register_event", "claim": cid}
            n = named.get(cid)
            if n:
                row.update({"event": n.get("event") or row["event"],
                            "time": n.get("time") or row["time"],
                            "cls": n.get("cls") or row["cls"],
                            "base_rate": n.get("base_rate"),
                            "consensus": odds_line(n.get("odds") or [], db_path, now)
                            if n.get("odds") else "—"})
            out.append(row)
    return out


def rebalance_rows(p: dict, mon: dt.date, sat: dt.date) -> list[dict]:
    out = []
    for d, evs in ((p.get("week_ahead") or {}).get("session_events") or {}).items():
        hit = [e for e in evs or [] if e in REBALANCE_CLASSES]
        if hit and mon.isoformat() <= d[:10] < sat.isoformat():
            out.append({"date": d[:10], "time": "16:00",
                        "event": "Index rebalance" if "INDEX_REBALANCE" in hit
                        else "ETF rebalance", "consensus": "—",
                        "cls": "index_rebalance"})
    return out


# ---------------------------------------------------------------------------
# Families, channels, amplifiers
# ---------------------------------------------------------------------------
def collapse_families(rows: list[dict], min_outcomes: int = 2
                      ) -> tuple[list[dict], list[dict], list[str]]:
    """Prediction-market resolutions on one day of one family -> one row, its
    modal outcome (the likeliest, W-1.1's rule). Returns (rows, every outcome
    of a collapsed family, the collapsed lines)."""
    from .figure_budget import contract_family                  # noqa: PLC0415
    groups: dict = {}
    for r in rows:
        if r.get("cls") == "prediction_family":
            groups.setdefault((r["date"], contract_family(r["event"])), []).append(r)
    fams = {k: v for k, v in groups.items() if len(v) >= min_outcomes}
    out, full, lines, done = [], [], [], set()
    for r in rows:
        k = (r["date"], contract_family(r["event"])) \
            if r.get("cls") == "prediction_family" else None
        if k not in fams:
            out.append(r)
            continue
        if k in done:
            continue
        done.add(k)
        fam = fams[k]
        modal = max(fam, key=lambda x: x.get("probability") or -1.0)
        q = str(modal["event"]).split(":", 1)[1].strip()
        last = str(modal["consensus"]).replace("last ", "")
        out.append({**modal, "event": f"Prediction markets resolve: {len(fam)} "
                                      f"outcomes; modal: {q}",
                    "consensus": f"modal outcome, last {last}",
                    "family_size": len(fam)})
        full += fam
        lines.append(f"{_day(r['date'])}: {len(fam)} prediction-market outcomes "
                     f"resolve; the modal one, {q}, last at {last}.")
    return out, full, lines


def cftc_names() -> dict:
    from .weekly_stack import CFTC_CONTRACTS                    # noqa: PLC0415
    return dict(CFTC_CONTRACTS)


def amplifier(cls_cfg: dict, pos: Optional[dict], z_min: float) -> str:
    """The positioning that would amplify a surprise: the class's contracts
    whose two-year z is at least `z_min` from zero, from the Positioning
    section's own CFTC rows."""
    wanted = cls_cfg.get("amplifiers") or []
    if not wanted:
        return "—"
    names = cftc_names()
    seen, crowded = 0, []
    for inst in wanted:
        x = (pos or {}).get(f"cftc:{inst}") or {}
        z = x.get("z_2y")
        if z is None:
            continue
        seen += 1
        if abs(z) >= z_min:
            side = "net long" if (x.get("level") or 0) > 0 else "net short"
            crowded.append(f"speculators {side} {names.get(inst, inst)} "
                           f"(z {z:+.1f})")
    if crowded:
        return "; ".join(crowded)
    return (f"no crowded position (|z| under {z_min:g})" if seen
            else "positioning not stored")


# ---------------------------------------------------------------------------
# The table
# ---------------------------------------------------------------------------
def build(cal: Optional[dict], p: dict, pos: Optional[dict], now: str,
          cfg: Optional[dict] = None, chain_base: Optional[Path] = None,
          min_outcomes: int = 2, repo: Optional[Path] = None,
          db_path: Optional[str] = None) -> dict:
    """The ranked table. `db_path` is the store the earnings rows' reactions are
    read from, passed explicitly by the caller (the Weekly passes the store it
    opened); None reads none, never the default store."""
    cfg = cfg if cfg is not None else load_config()
    classes = cfg.get("classes") or {}
    cal = cal or {}
    win = cal.get("window")
    if win:
        mon = dt.date.fromisoformat(win[0])
    else:
        end = dt.date.fromisoformat(str(p.get("week_ending"))[:10])
        mon = end + dt.timedelta(days=(7 - end.weekday()) % 7 or 7)
    sat = mon + dt.timedelta(days=5)
    rows = []
    for r in cal.get("rows") or []:
        if r.get("cls") == "earnings":
            r = earnings_row(r, cfg, now, chain_base)
            # OS-11 (a44-opening-setup): the last three reactions and the pricing word.
            from . import opening_setup                         # noqa: PLC0415
            r = opening_setup.with_pricing(r, now, db_path)
        rows.append(dict(r))
    hrows, absent = hand_rows(cfg, mon, sat, repo)
    rows += hrows + register_rows(cfg, mon, sat, db_path, now) \
        + rebalance_rows(p, mon, sat)
    rows, full, lines = collapse_families(rows, min_outcomes)
    z_min = float(cfg.get("amplifier_z") or 1.5)
    ai = ai_names(cfg, repo)
    for r in rows:
        c = classes.get(r.get("cls") or "") or {}
        r["tier"] = int(c.get("tier") or r.get("tier") or 3)
        r["why"] = why_of(r, c, ai)
        r["amplify"] = amplifier(c, pos, z_min)
    rows.sort(key=lambda r: (r["tier"], r["date"], str(r.get("time")), r["event"]))
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    table = {"columns": list(COLUMNS),
             "rows": [[f"{_day(r['date'])}, {r.get('time')}", r["event"], r["tier"],
                       r.get("consensus") or "—", r["why"], r["amplify"]]
                      for r in rows]}
    # THE PLAYBOOK SLOT (item 3.5): the highest-ranked event whose class has an
    # outcome map (config `playbook: true`); the rank-1 event when none does.
    top = next((r for r in rows if (classes.get(r.get("cls") or "") or {})
                .get("playbook")), rows[0] if rows else None)
    playbook = ({"event": top["event"], "cls": top.get("cls"), "date": top["date"],
                 "time": top.get("time"), "tier": top["tier"],
                 "playbook_class": bool((classes.get(top.get("cls") or "") or {})
                                        .get("playbook")),
                 "outcomes": None} if top else None)
    routine = cal.get("routine") or []
    reference = []
    if routine:
        reference.append({"title": "Routine releases and bill auctions, the coming "
                                   "week",
                          "table": {"columns": ["Day", "Time (ET)", "Event"],
                                    "rows": [[_day(r["date"]), r["time"], r["event"]]
                                             for r in routine]}})
    if full:
        reference.append({"title": "Prediction-market resolutions, every outcome",
                          "table": {"columns": ["Day", "Time (ET)", "Event",
                                                "Consensus / prior"],
                                    "rows": [[_day(r["date"]), r.get("time"),
                                              r["event"], r.get("consensus")]
                                             for r in full]}})
    notes = []
    # weekly-fixes-7 item 12: "release time not captured" once, as a footnote.
    from .weekly_sections import RELEASE_NOT_CAPTURED            # noqa: PLC0415
    from .readability import fold_repeated_gaps                  # noqa: PLC0415
    notes += fold_repeated_gaps(table, {RELEASE_NOT_CAPTURED: (
        "A day with no time: the source stored the date, not the release time.")})
    if routine:
        notes.append(f"{len(routine)} routine data release(s) and bill auction(s) "
                     f"are in the reference tables.")
    notes.append("Ranked by importance tier (1 moves every market, 3 one), then "
                 "time; the tiers, channels and amplifiers are declared in config, "
                 "never chosen by the model.")
    if absent:
        notes.append("Hand-seeded calendars not present on this branch: "
                     + ", ".join(absent) + ".")
    return {"table": table, "rows": rows, "top": top, "playbook": playbook,
            "reference": reference, "collapsed": lines, "notes": notes,
            "routine_count": len(routine)}
