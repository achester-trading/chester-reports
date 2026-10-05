"""
Monthly v2, Phase A: the storyline sections. (docs/briefs/monthly-v2-brief-2026-10-01.md)

    1  THE MONTH IN ONE PAGE      five numbered takeaways, then the paragraph
    2  LOOKING BACK, BY THEME     tagged, sourced items; then WHAT CHANGED
    3  VOICES                     "Voices register not yet built" until Phase B
    4  LOOKING AHEAD, 2-3 MONTHS  the calendar, and every scenario with its Brier
                                  and what would change our mind
    5  WHERE OUR READ LANDS       one paragraph, restating the weights and books
    +  a TIE-BACK SENTENCE opening every section after the first

EVERYTHING HERE IS READ, AND EVERY ITEM CARRIES ITS SOURCE. The brief's rule is
"no stored source, not printed": an item is a stored row -- the market-state
object, a narrative-register story or evaluation, an event, a ledger forecast, a
claim -- with its id and date. An item that cannot name one is REFUSED, kept in the
payload with the reason, and counted in the document, rather than printed.

TAGS ARE CHECKED, NOT CHOSEN. CONSENSUS needs two or more tier-1-2 sources; DISSENT
names its source; CORRECTION cites the prior statement it corrects; NEW is dated
inside the window. check_item() is the one place those rules live.

"WHAT CHANGED" IS COMPUTED. Every line is a difference between two stored records
-- the object at the previous Monthly against now, register evaluations inside the
window, ledger and register rows dated inside it -- and nothing in it is written by
hand. The window opens at the previous Monthly's report date.

NOTHING HERE COMPUTES A REGIME, and nothing here writes. The database is opened
read-only; a fixture without a table reads as empty, not as a fault.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

import yaml

from altdata import claims, observations, session, source_tiers

REPO = Path(__file__).resolve().parent.parent
THEMES_PATH = REPO / "config" / "monthly_themes.yaml"

V2_SECTIONS = ("month_in_markets", "month_in_one_page", "looking_back",
               "voices", "looking_ahead", "our_read")
TAGS = ("CONSENSUS", "NEW", "DISSENT", "CORRECTION")
TAKEAWAYS = 5

# The sections a tie-back sentence opens -- every one after the first.
TIE_BACK_SECTIONS = ("month_in_one_page", "looking_back", "voices", "looking_ahead", "our_read",
                     "regime", "scenarios", "top_bottom", "alternative_assets",
                     "register_month", "appendix")


def load_themes(path: Optional[Path] = None) -> dict:
    with open(path or THEMES_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Read-only access
# ---------------------------------------------------------------------------
def _connect() -> Optional[sqlite3.Connection]:
    """The shared database, READ-ONLY. None if it does not exist."""
    p = Path(observations.DEFAULT_DB)
    if not p.exists():
        return None
    conn = sqlite3.connect(f"{p.resolve().as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _q(conn: Optional[sqlite3.Connection], sql: str, args: Any = ()) -> list[dict]:
    """Rows as dicts. A missing table is an empty answer, not a fault: a fixture
    store, or a box before the table's first writer ran."""
    if conn is None:
        return []
    try:
        return [dict(r) for r in conn.execute(sql, args)]
    except sqlite3.OperationalError as exc:
        if "no such table" in str(exc):
            return []
        raise


def src(kind: str, ref: Any, date: Any, *, title: Optional[str] = None,
        tier: Optional[int] = None, url: Optional[str] = None) -> dict:
    """One citation: what kind of stored record, its id, its date."""
    out = {"kind": kind, "id": str(ref), "date": str(date)[:10] if date else None}
    if title:
        out["title"] = title
    if tier is not None:
        out["tier"] = tier
    if url:
        out["url"] = url
    return out


# ---------------------------------------------------------------------------
# The tag rules -- the one place they live
# ---------------------------------------------------------------------------
def check_item(item: dict, window: tuple[str, str]) -> Optional[str]:
    """None if the item may print; otherwise the reason it is refused."""
    sources = [s for s in (item.get("sources") or [])
               if s.get("kind") and s.get("id") and s.get("date")]
    if not sources:
        return "no stored source -- an item that cannot name one is not printed"
    tag = item.get("tag")
    if tag not in TAGS:
        return f"tag {tag!r} is not one of {', '.join(TAGS)}"
    start, end = window
    if tag == "CONSENSUS":
        backed = [s for s in sources if s.get("tier") in (1, 2)]
        if len(backed) < 2:
            return (f"CONSENSUS needs two or more tier-1-2 sources; this item has "
                    f"{len(backed)}")
    if tag == "DISSENT":
        if not any(s.get("title") or s.get("kind") in ("claim", "event")
                   for s in sources):
            return "DISSENT must name its source"
    if tag == "CORRECTION":
        c = item.get("corrects") or {}
        if not (c.get("id") and c.get("date") and c.get("statement")):
            return ("CORRECTION must cite the prior statement it corrects (id, "
                    "date and what was said)")
    if tag == "NEW":
        if not any(start <= (s.get("date") or "") <= end[:10] for s in sources):
            return (f"NEW needs a source dated inside the window {start} to "
                    f"{end[:10]}")
    return None


def _admit(items: list[dict], window: tuple[str, str]) -> tuple[list, list]:
    ok, refused = [], []
    for it in items:
        why = check_item(it, window)
        (refused if why else ok).append({**it, "refused_because": why} if why
                                        else it)
    return ok, refused


# ---------------------------------------------------------------------------
# The window
# ---------------------------------------------------------------------------
def window_of(p: dict) -> tuple[str, str]:
    """(start, cutoff): from the previous Monthly to this one's cutoff.

    No previous Monthly: from the first day of the previous calendar month, and
    the payload says so -- a window that silently began at the dawn of the store
    would make everything look new.
    """
    cutoff = str(p.get("as_of") or session.utc_iso())
    prev = (p.get("regime") or {}).get("previous_monthly")
    if prev:
        return str(prev)[:10], cutoff
    d = dt.date.fromisoformat(cutoff[:10])
    first = (d.replace(day=1) - dt.timedelta(days=1)).replace(day=1)
    return first.isoformat(), cutoff


# ---------------------------------------------------------------------------
# Narrative-register reads
# ---------------------------------------------------------------------------
def _stories(conn) -> dict[str, dict]:
    rows = _q(conn, "SELECT narrative_id, name, status, state, direction, opened,"
                    " last_changed, evidence_against, story_query"
                    " FROM narratives WHERE status = 'active'")
    return {r["narrative_id"]: r for r in rows}


def _state_at(conn, nid: str, day: str) -> Optional[dict]:
    """The story's state as last evaluated on or before `day`."""
    r = _q(conn, "SELECT id, session, state_after FROM narrative_evaluations"
                 " WHERE narrative_id = ? AND session <= ?"
                 " ORDER BY session DESC LIMIT 1", (nid, day))
    return r[0] if r else None


def _transitions(conn, start: str, cutoff: str) -> list[dict]:
    return _q(conn, "SELECT id, narrative_id, session, state_before, state_after,"
                    " transition FROM narrative_evaluations"
                    " WHERE transition IS NOT NULL AND session > ? AND session <= ?"
                    " AND evaluated_at <= ? ORDER BY session",
              (start, cutoff[:10], cutoff))


def _headlines(conn, query: Optional[str], start: str, cutoff: str) -> list[dict]:
    """The story query's headlines in the window, tiered, newest first."""
    if not query:
        return []
    rows = _q(conn, "SELECT id, observed_at, title, url, payload FROM events"
                    " WHERE type = 'headline' AND observed_at >= ?"
                    " AND observed_at <= ? AND available_at <= ?"
                    " ORDER BY observed_at DESC", (start, cutoff, cutoff))
    out = []
    for r in rows:
        try:
            q = (json.loads(r.get("payload") or "{}") or {}).get("query")
        except (TypeError, ValueError):
            q = None
        if q != query:
            continue
        out.append({**r, "tier": source_tiers.tier_of(r.get("title"))})
    return out


# ---------------------------------------------------------------------------
# 2. LOOKING BACK, BY THEME
# ---------------------------------------------------------------------------
_POLE_CACHE: dict[str, tuple] = {}


def _poles(dim: str) -> tuple:
    """A dimension's two extreme states, from config -- a move from one to the
    other is our own read reversed, which is what CORRECTION means."""
    if dim not in _POLE_CACHE:
        try:
            import regime
            states = ((regime.load_config() or {}).get("dimensions") or {}
                      ).get(dim, {}).get("states") or []
        except Exception:                                      # noqa: BLE001
            states = []
        _POLE_CACHE[dim] = (states[0], states[-1]) if len(states) >= 2 else ()
    return _POLE_CACHE[dim]


def _dimension_items(p: dict, dims: list[str]) -> tuple[list, list]:
    rg = p.get("regime") or {}
    items, held = [], []
    for row in rg.get("dimensions") or []:
        if row.get("dimension") not in dims:
            continue
        name, now, was = row["dimension"], row.get("state"), row.get("previous_state")
        source = src("object", f"market_state@{rg.get('session')}", rg.get("session"))
        if not row.get("changed"):
            held.append(f"{name} {now or 'absent'}")
            continue
        if now is None or was is None:
            # A MOVE INTO OR OUT OF ABSENCE IS A DATA FACT, NOT A MARKET ONE: the
            # dimension lost (or regained) its inputs. It stays in What changed,
            # which is a list of differences; it is not news under a theme.
            held.append(f"{name} {now or 'absent'} (was {was or 'absent'})")
            continue
        it = {"kind": "dimension", "dimension": name, "state": now,
              "previous_state": was, "sources": [source],
              "text": f"The {name} dimension moved from {was or 'absent'} to "
                      f"{now or 'absent'}"
                      + (f" (percentile {row.get('percentile')})"
                         if row.get("percentile") is not None else "")}
        poles = _poles(name)
        if poles and {was, now} == set(poles):
            it["tag"] = "CORRECTION"
            it["corrects"] = {"id": f"market_state@{rg.get('previous_monthly')}",
                              "date": rg.get("previous_monthly"),
                              "statement": f"the previous Monthly read {name} as "
                                           f"{was}"}
        else:
            it["tag"] = "NEW"
        items.append(it)
    return items, held


def _story_items(conn, nids: list[str], stories: dict, start: str,
                 cutoff: str) -> tuple[list, list]:
    items, held = [], []
    for nid in nids:
        s = stories.get(nid)
        if not s:
            held.append(f"{nid} (not an active story in the register)")
            continue
        heads = _headlines(conn, s.get("story_query"), start, cutoff)
        backed = [h for h in heads if h.get("tier") in (1, 2)]
        reg_src = src("narrative", nid, s.get("last_changed") or s.get("opened"))
        head_srcs = [src("event", h["id"], h["observed_at"], title=h["title"],
                         tier=h["tier"]) for h in backed[:3]]
        prior = _state_at(conn, nid, start)
        state = s.get("state")
        base = {"kind": "story", "story": nid, "state": state,
                "headlines_in_window": len(heads),
                "tier12_in_window": len(backed),
                "text": f"{s.get('name')}: {state} -- {s.get('direction')}"}
        opened = str(s.get("opened") or "")[:10]
        if prior and prior.get("state_after") and prior["state_after"] != state and (
                prior["state_after"] == "consensus"
                or (state == "consensus"
                    and prior["state_after"] in ("contested", "fading"))):
            items.append({**base, "tag": "CORRECTION",
                          "sources": [reg_src] + head_srcs,
                          "corrects": {"id": f"narrative_evaluation:{prior['id']}",
                                       "date": prior["session"],
                                       "statement": f"the register read "
                                                    f"{s.get('name')} as "
                                                    f"{prior['state_after']}"}})
        elif start <= opened <= cutoff[:10]:
            items.append({**base, "tag": "NEW",
                          "sources": [src("narrative", nid, opened)] + head_srcs})
        elif state == "consensus":
            items.append({**base, "tag": "CONSENSUS", "sources": head_srcs})
        elif state == "contested":
            against = []
            try:
                against = json.loads(s.get("evidence_against") or "[]")
            except (TypeError, ValueError):
                pass
            named = [src("event", a.get("event_id") or a.get("id"),
                         a.get("observed_at") or a.get("date"),
                         title=a.get("title")) if isinstance(a, dict)
                     else src("event", a, s.get("last_changed")) for a in against]
            items.append({**base, "tag": "DISSENT", "sources": named[-3:]})
        elif prior and prior.get("state_after") != state:
            items.append({**base, "tag": "NEW",
                          "sources": [src("narrative", nid, s.get("last_changed"))]
                          + head_srcs})
        else:
            held.append(f"{s.get('name')} {state}, {len(backed)} tier-1-2 "
                        f"headline(s) this window")
    return items, held


def _release_items(conn, sources: list[str], start: str,
                   cutoff: str) -> list[dict]:
    if not sources:
        return []
    marks = ",".join("?" for _ in sources)
    rows = _q(conn, f"SELECT id, observed_at, source, title, url FROM events"
                    f" WHERE type = 'release' AND source IN ({marks})"
                    f" AND observed_at >= ? AND observed_at <= ?"
                    f" AND available_at <= ? ORDER BY observed_at",
              (*sources, start, cutoff, cutoff))
    return [{"kind": "release", "tag": "NEW", "text": r["title"],
             "sources": [src("event", r["id"], r["observed_at"], title=r["title"],
                             url=r.get("url"))]}
            for r in rows]


def looking_back(p: dict, conn, window: tuple[str, str]) -> dict:
    cfg = load_themes()
    start, cutoff = window
    stories = _stories(conn)
    themes, refused_all = [], []
    for tid, t in (cfg.get("themes") or {}).items():
        d_items, d_held = _dimension_items(p, t.get("dimensions") or [])
        s_items, s_held = _story_items(conn, t.get("stories") or [], stories,
                                       start, cutoff)
        r_items = _release_items(conn, t.get("release_sources") or [], start,
                                 cutoff)
        ok, refused = _admit(d_items + s_items + r_items, window)
        refused_all += [{**r, "theme": tid} for r in refused]
        themes.append({
            "theme": tid, "name": t.get("name"),
            "dimensions": t.get("dimensions") or [],
            "no_dimension_why": t.get("no_dimension_why"),
            "stories": t.get("stories") or [],
            "items": ok, "refused": len(refused),
            "held": d_held + s_held,
            **theme_metrics(p, t),
            "fed_calendar": (fed_calendar(conn, cutoff) if t.get("fed_calendar")
                             else None)})
    return {"state": "ok", "window": [start, cutoff],
            "themes_version": cfg.get("version"), "themes": themes,
            "refused": refused_all,
            "what_changed": what_changed(p, conn, window)}


# ---------------------------------------------------------------------------
# WHAT CHANGED -- computed, never written
# ---------------------------------------------------------------------------
def what_changed(p: dict, conn, window: tuple[str, str]) -> dict:
    start, cutoff = window
    rg = p.get("regime") or {}
    obj = src("object", f"market_state@{rg.get('session')}", rg.get("session"))
    rows: list[dict] = []
    if rg.get("state") == "ok" and rg.get("previous_monthly"):
        for d in rg.get("dials") or []:
            if d.get("changed"):
                rows.append({"what": f"dial {d['dial']}",
                             "from": d.get("previous_state"), "to": d.get("state"),
                             "source": obj})
        for d in rg.get("dimensions") or []:
            if d.get("changed"):
                rows.append({"what": f"dimension {d['dimension']}",
                             "from": d.get("previous_state"), "to": d.get("state"),
                             "source": obj})
        for x in rg.get("exceptions_opened") or []:
            rows.append({"what": f"exception {x}", "from": "closed", "to": "open",
                         "source": obj})
        for x in rg.get("exceptions_closed") or []:
            rows.append({"what": f"exception {x}", "from": "open", "to": "closed",
                         "source": obj})
    for t in _transitions(conn, start, cutoff):
        rows.append({"what": f"story {t['narrative_id']}",
                     "from": t.get("state_before"), "to": t.get("state_after"),
                     "source": src("narrative_evaluation", t["id"], t["session"])})
    for s in _stories(conn).values():
        if start <= str(s.get("opened") or "")[:10] <= cutoff[:10]:
            rows.append({"what": f"story {s['narrative_id']}", "from": None,
                         "to": f"opened ({s.get('state')})",
                         "source": src("narrative", s["narrative_id"], s["opened"])})
    for f in _q(conn, "SELECT probability_id, claim, probability, emitted_at"
                      " FROM probabilities WHERE emitted_at >= ? AND emitted_at <= ?",
                (start, cutoff)):
        rows.append({"what": "forecast emitted", "from": None,
                     "to": f"p {f['probability']}: {str(f['claim'])[:90]}",
                     "source": src("forecast", f["probability_id"], f["emitted_at"])})
    for f in _q(conn, "SELECT probability_id, claim, outcome, resolved_at"
                      " FROM probabilities WHERE resolved_at >= ? AND resolved_at <= ?",
                (start, cutoff)):
        rows.append({"what": "forecast resolved", "from": "open",
                     "to": f"outcome {f['outcome']}: {str(f['claim'])[:90]}",
                     "source": src("forecast", f["probability_id"],
                                   f["resolved_at"])})
    for d in _q(conn, "SELECT id, instrument, direction, status, created_at"
                      " FROM decisions WHERE created_at >= ? AND created_at <= ?"
                      " ORDER BY created_at", (start, cutoff)):
        rows.append({"what": f"decision {d['instrument']} {d['direction']}",
                     "from": None, "to": d["status"],
                     "source": src("decision", d["id"][:8], d["created_at"])})
    for cid, c in sorted((claims.all_claims() or {}).items()):
        cdate = str(c.get("date") or "")[:10]
        if start <= cdate <= cutoff[:10]:
            rows.append({"what": f"claim {cid}", "from": None,
                         "to": f"dated {cdate}", "source": src("claim", cid, cdate)})
    note = (None if rg.get("previous_monthly") else
            "no previous Monthly snapshot: the regime is not compared, and the "
            "window opens at the first day of the previous month")
    return {"window": [start, cutoff], "rows": rows, "count": len(rows),
            "regime_compared_against": rg.get("previous_monthly"), "note": note,
            "computed": True}


# ---------------------------------------------------------------------------
# 4. LOOKING AHEAD
# ---------------------------------------------------------------------------
def _signposts(row: dict) -> list[dict]:
    """What would change our mind: observable, dated, from stored records only."""
    out = []
    when = row.get("horizon_date") or row.get("resolve_by")
    if row.get("resolution_criterion") and when:
        out.append({"observable": str(row["resolution_criterion"]),
                    "date": str(when)[:10], "kind": "resolution"})
    sset = str(row.get("scenario_set") or "")
    if sset.startswith("hypothesis:"):
        nid = sset.split(":")[1]
        out.append({"observable": f"the register moves story `{nid}` to contested "
                                  f"or fading",
                    "date": "evaluated at every close", "kind": "story_state",
                    "story": nid})
    return out


def looking_ahead(p: dict, conn, window: tuple[str, str]) -> dict:
    cfg = (load_themes().get("calendar") or {})
    cutoff = window[1]
    first = cutoff[:10]
    last = (dt.date.fromisoformat(first)
            + dt.timedelta(days=int(cfg.get("horizon_days") or 92))).isoformat()
    names = set(cfg.get("fred_release_names") or [])
    keep = set(cfg.get("include_sources") or [])
    cal = []
    seen = set()
    for r in _q(conn, "SELECT id, observed_at, source, title, payload FROM events"
                      " WHERE type IN ('scheduled', 'session_event')"
                      " AND observed_at > ? AND observed_at <= ?"
                      " AND available_at <= ? ORDER BY observed_at",
                (cutoff, f"{last}T23:59:59Z", cutoff)):
        try:
            pay = json.loads(r.get("payload") or "{}") or {}
        except (TypeError, ValueError):
            pay = {}
        if r["source"] == "fred_releases":
            if pay.get("release_name") not in names:
                continue
        elif r["source"] not in keep:
            continue
        key = (str(r["observed_at"])[:10], r["title"])
        if key in seen:
            continue
        seen.add(key)
        cal.append({"date": str(r["observed_at"])[:10], "title": r["title"],
                    "source": src("event", r["id"], r["observed_at"],
                                  title=r["title"])})
    # HOW FAR EACH CALENDAR SOURCE REACHES. FRED's release calendar is stored a
    # few weeks out; a quiet November is the table's horizon, not the market's.
    reach = {r["source"]: str(r["newest"])[:10] for r in _q(
        conn, "SELECT source, MAX(observed_at) newest FROM events"
              " WHERE type = 'scheduled' AND available_at <= ? GROUP BY source",
        (cutoff,))}
    scen, refused = [], []
    for r in _q(conn, "SELECT * FROM probabilities WHERE emitted_at <= ?"
                      " AND (resolved_at IS NULL OR resolved_at > ?)"
                      " ORDER BY probability DESC", (cutoff, cutoff)):
        sp = _signposts(r)
        row = {"claim": r.get("claim"), "probability": r.get("probability"),
               "brier": r.get("brier"), "source": r.get("source"),
               "scenario_set": r.get("scenario_set"),
               "resolve_by": str(r.get("horizon_date") or r.get("resolve_by")
                                 or "")[:10] or None,
               "signposts": sp,
               "cite": src("forecast", r.get("probability_id"), r.get("emitted_at"))}
        if sp:
            scen.append(row)
        else:
            refused.append({**row, "refused_because":
                            "no stored, dated signpost -- a weight with nothing "
                            "that would change it is not printed"})
    # SPLIT BY WINDOW (Ari's second round): the rest of this month, then the two
    # after it -- "October" and "November–December" on 1 Oct.
    wins = calendar_windows(cutoff)
    windows = [{"name": n, "first": f, "last": l,
                "calendar": [c for c in cal if f <= c["date"] <= l]}
               for n, f, l in wins]
    cov = coverage(conn, cutoff)
    gaps = []
    for c in cov:
        # Windows the item is not expected in (its months fall elsewhere) are
        # neither present nor missing; they are left out of the judgement.
        ws = {n: w for n, w in c["windows"].items() if w.get("expected", True)}
        if not ws:
            continue
        if any("have" in w for w in ws.values()):
            have = {s for w in ws.values() for s in w.get("have") or []}
            want = [s for w in ws.values() for s in (w.get("have") or [])
                    + (w.get("missing") or [])]
            absent = [s for s in dict.fromkeys(want) if s not in have]
            if absent:
                gaps.append(f"{c['item']}: {', '.join(absent)}")
        elif not any(w["present"] for w in ws.values()):
            gaps.append(f"{c['item']} dates")
        elif c.get("once"):
            continue          # a one-off event is covered by being in any window
        else:
            gaps += [f"{c['item']} for {n}" for n, w in ws.items()
                     if not w["present"]]
    return {"state": "ok" if (cal or scen) else "empty",
            "reason": (None if (cal or scen) else
                       "nothing scheduled in the events table and no live "
                       "forecast in the ledger inside the horizon"),
            "horizon": [first, last], "calendar": cal, "calendar_reach": reach,
            "windows": windows, "coverage": cov, "not_yet_tracked": gaps,
            "scenarios": scen, "scenarios_refused": refused}


# ---------------------------------------------------------------------------
# THE MONTH IN MARKETS -- the opening scorecard (Ari's revision, 1 Oct)
# ---------------------------------------------------------------------------
def month_bounds(p: dict) -> tuple[dt.date, dt.date]:
    """(start, end): the previous calendar month's two month-ends.

    The 1 Oct edition covers September: the close on or before 31 Aug against
    the close on or before 30 Sep.
    """
    day = dt.date.fromisoformat(str(p.get("report_date") or p.get("as_of"))[:10])
    end = day.replace(day=1) - dt.timedelta(days=1)
    start = end.replace(day=1) - dt.timedelta(days=1)
    return start, end


def _level_on(rows: list[dict], day: dt.date) -> Optional[dict]:
    """The last observation on or before `day`."""
    best = None
    for r in rows:
        if str(r.get("observed_at"))[:10] <= day.isoformat() \
                and r.get("value_num") is not None:
            best = r
    return best


def month_in_markets(p: dict) -> dict:
    from altdata import derived
    cfg = load_themes()
    start, end = month_bounds(p)
    cutoff = str(p.get("as_of") or session.utc_iso())
    rows, missing = [], []
    with observations.ObservationStore() as st:
        for spec in cfg.get("scorecard") or []:
            key = spec["metric"]
            obs = sorted(st.as_of(key, as_of=cutoff),
                         key=lambda r: str(r.get("observed_at")))
            a, b = _level_on(obs, start), _level_on(obs, end)
            if not (a and b):
                missing.append(f"{spec['label']} ({key}): no observation on or "
                               f"before {start if not a else end} knowable at the "
                               f"cutoff")
                continue
            # A LEVEL OLDER THAN A WEEK IS NOT THAT MONTH-END'S LEVEL. A series
            # that stopped printing would otherwise read as a flat month -- the
            # same old value at both ends, "+0.0 bp" -- which is a fact about the
            # feed presented as one about the market.
            stale = [(r, day) for r, day in ((a, start), (b, end))
                     if (day - dt.date.fromisoformat(str(r["observed_at"])[:10])).days > 7]
            if stale:
                r, day = stale[0]
                missing.append(f"{spec['label']} ({key}): its last observation on or "
                               f"before {day} is dated {str(r['observed_at'])[:10]}, "
                               f"more than a week earlier")
                continue
            s0, s1 = float(a["value_num"]), float(b["value_num"])
            unit, _why = derived.delta_unit_for(key)
            if unit == "bps":
                change = round((s1 - s0) * 100.0, 1)
            elif unit == "percent" and s0:
                change = round((s1 / s0 - 1.0) * 100.0, 2)
            else:
                unit, change = "raw", round(s1 - s0, 4)
            d = derived.derived_forms(key, cutoff, store=st)
            rows.append({"id": spec["id"], "label": spec["label"], "metric": key,
                         "start_date": str(a["observed_at"])[:10],
                         "start_level": s0,
                         "end_date": str(b["observed_at"])[:10], "end_level": s1,
                         "change": change, "change_unit": unit,
                         "percentile": d.get("percentile"),
                         "source": src("store", key, b["observed_at"])})
    return {"state": "ok" if rows else "empty",
            "reason": (None if rows else
                       "no scorecard series has observations at both month-ends"),
            "month": end.strftime("%B %Y"), "start": start.isoformat(),
            "end": end.isoformat(), "rows": rows, "missing": missing,
            "prose": "written per section by monthly_macro.prose"}


# ---------------------------------------------------------------------------
# EVERYTHING THE STORE HOLDS FOR A THEME (Ari's second round, 1 Oct)
# ---------------------------------------------------------------------------
# A print older than this before the month-end is not "this month's" -- it goes
# to the footnote with its date instead of into the prose as if it were current.
STALE_DAYS = 75


def metric_month(st, spec: dict, cutoff: str, month_end: dt.date) -> dict:
    """One series over the month: its latest print on or before the month-end,
    the change since the print about a month before it, and its level percentile.

    WORKS FOR ANY CADENCE. A daily series compares 30 Sep with 31 Aug; a monthly
    one its August print with July's; a weekly one with the week four before.
    `since` names the earlier print's date so the change is never mistaken for a
    calendar-month move it is not.
    """
    from altdata import derived
    key, inst = spec["metric"], spec.get("instrument")
    obs = sorted(st.as_of(key, as_of=cutoff, instrument=inst),
                 key=lambda r: str(r.get("observed_at")))
    b = _level_on(obs, month_end)
    out = {"label": spec.get("label") or key, "metric": key, "instrument": inst}
    if not b:
        return {**out, "state": "missing",
                "why": "no print knowable at the cutoff"}
    b_day = dt.date.fromisoformat(str(b["observed_at"])[:10])
    if (month_end - b_day).days > STALE_DAYS:
        return {**out, "state": "stale", "last_print": b_day.isoformat()}
    prev_target = min(month_end.replace(day=1) - dt.timedelta(days=1),
                      b_day - dt.timedelta(days=25))
    a = _level_on(obs, prev_target)
    unit, _ = derived.delta_unit_for(key)
    s1 = float(b["value_num"])
    row = {**out, "state": "ok", "latest_date": b_day.isoformat()}
    if unit == "bps":
        row["latest_pct"] = s1
    else:
        row["latest_level"] = s1
    if a:
        s0 = float(a["value_num"])
        row["since"] = str(a["observed_at"])[:10]
        if unit == "bps":
            row["change_bps"] = round((s1 - s0) * 100.0, 1)
        elif unit == "percent" and s0:
            row["change_pct"] = round((s1 / s0 - 1.0) * 100.0, 2)
        else:
            row["change"] = round(s1 - s0, 4)
    # THE DISPLAY FORM of a large figure, in the series' own unit ("$7.51tn",
    # "159.33 million") -- the writer copies it rather than rescaling.
    from altdata import numeral_audit as na
    units = (derived.registry_entry(key) or {}).get("units")
    disp = na.scaled_display(s1, units) if "latest_level" in row else None
    if disp:
        row["latest_level_display"] = disp
    if "change" in row:
        cdisp = na.scaled_display(row["change"], units)
        if cdisp:
            row["change_display"] = cdisp
    try:
        d = derived.derived_forms(key, cutoff, store=st, instrument=inst)
        row["level_percentile_5y"] = d.get("percentile")
    except Exception:                                          # noqa: BLE001
        pass
    return row


def theme_metrics(p: dict, theme_cfg: dict) -> dict:
    """{rows, not_yet_tracked}: every configured series, and every gap in words."""
    cutoff = str(p.get("as_of") or session.utc_iso())
    _, month_end = month_bounds(p)
    rows, gaps = [], []
    with observations.ObservationStore() as st:
        for spec in theme_cfg.get("metrics") or []:
            r = metric_month(st, spec, cutoff, month_end)
            if r["state"] == "ok":
                rows.append(r)
            elif r["state"] == "stale":
                gaps.append(f"{r['label']} (latest print {r['last_print']})")
            else:
                gaps.append(r["label"])
    return {"rows": rows,
            "not_yet_tracked": gaps + list(theme_cfg.get("untracked") or [])}


def fed_calendar(conn, cutoff: str) -> dict:
    """The latest FOMC decision and the next meeting, from stored events."""
    last = _q(conn, "SELECT id, observed_at, title FROM events WHERE source ="
                    " 'fed_monetary' AND observed_at <= ? AND available_at <= ?"
                    " ORDER BY observed_at DESC LIMIT 1", (cutoff, cutoff))
    nxt = _q(conn, "SELECT id, observed_at, title FROM events WHERE type ="
                   " 'scheduled' AND title LIKE 'FOMC%' AND observed_at > ?"
                   " AND available_at <= ? ORDER BY observed_at LIMIT 2",
             (cutoff, cutoff))
    return {"latest_decision": ({"date": str(last[0]["observed_at"])[:10],
                                 "statement": last[0]["title"]} if last else None),
            "next_meetings": [str(n["observed_at"])[:10] for n in nxt]}


def calendar_windows(cutoff: str) -> list[tuple[str, str, str]]:
    """(name, first, last): the rest of this month, then the next two months.
    On 1 Oct: "October", then "November–December"."""
    d = dt.date.fromisoformat(cutoff[:10])
    first_next = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    after = (first_next.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    end = ((after.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
           - dt.timedelta(days=1))
    return [(d.strftime("%B"), d.isoformat(),
             (first_next - dt.timedelta(days=1)).isoformat()),
            (f"{first_next.strftime('%B')}–{end.strftime('%B')}",
             first_next.isoformat(), end.isoformat())]


def coverage(conn, cutoff: str) -> list[dict]:
    """Every release on the coverage list, present or missing in each window."""
    import re
    cfg = load_themes().get("coverage") or []
    wins = calendar_windows(cutoff)
    rows = _q(conn, "SELECT e.source, e.title, e.observed_at, e.payload FROM events e"
                    " WHERE e.type IN ('scheduled', 'session_event')"
                    " AND e.observed_at > ? AND e.observed_at <= ?"
                    " AND e.available_at <= ?",
              (cutoff, f"{wins[-1][2]}T23:59:59Z", cutoff))
    out = []
    for c in cfg:
        rx = re.compile(c["match"])
        per = {}
        for name, first, last in wins:
            # ONLY IN ITS OWN MONTHS: a quarterly or one-off item is expected in a
            # window only if one of its declared months falls inside it.
            if c.get("months"):
                f0, l0 = dt.date.fromisoformat(first), dt.date.fromisoformat(last)
                in_win = {(f0.year, f0.month)}
                d = f0
                while (d.year, d.month) < (l0.year, l0.month):
                    d = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
                    in_win.add((d.year, d.month))
                if not any(m in c["months"] for _, m in in_win):
                    per[name] = {"present": None, "expected": False}
                    continue
            hits = []
            for r in rows:
                if c.get("sources") and r["source"] not in c["sources"]:
                    continue
                if not (first <= str(r["observed_at"])[:10] <= last):
                    continue
                try:
                    rel = (json.loads(r.get("payload") or "{}") or {}).get(
                        "release_name") or ""
                except (TypeError, ValueError):
                    rel = ""
                if rx.search(r["title"] or "") or rx.search(rel):
                    hits.append(r["title"])
            if c.get("expect"):
                have = sorted({s for s in c["expect"] for h in hits
                               if h.startswith(f"{s} ")})
                per[name] = {"present": bool(have), "have": have,
                             "missing": [s for s in c["expect"] if s not in have]}
            else:
                per[name] = {"present": bool(hits), "count": len(hits)}
        out.append({"item": c["item"], "windows": per, "once": bool(c.get("once")),
                    "free_source": c.get("free_source")})
    return out


# ---------------------------------------------------------------------------
# 5. WHERE OUR READ LANDS -- bounded to the weights and the books
# ---------------------------------------------------------------------------
def our_read(p: dict, conn, ahead: dict) -> dict:
    # SELECT *: `book` arrived with Phase 5a, and a register older than that
    # migration is a register with no books rather than a fault.
    open_ = _q(conn, "SELECT * FROM decisions WHERE status = 'active'"
                     " AND superseded_by IS NULL ORDER BY created_at")
    scen = ahead.get("scenarios") or []
    bz = ((p.get("register_month") or {}).get("books_vs_benchmark") or {})
    parts = ["Our read is what the scenario weights and the books already hold, "
             "and nothing beyond them."]
    if scen:
        top = scen[0]
        parts.append(f"The ledger carries {len(scen)} live weight(s); the "
                     f"highest is {top['probability']} that "
                     f"{str(top['claim'])[:160].rstrip('.')}, resolving "
                     f"{top.get('resolve_by') or 'at its horizon'}.")
    else:
        parts.append("The ledger carries no live weight, so no scenario view is "
                     "stated.")
    if open_:
        parts.append("The register holds " + ", ".join(
            f"{d['instrument']} {d['direction']}"
            + (f" (Book {d['book']})" if d.get("book") else "") for d in open_)
            + " as active.")
    else:
        parts.append("The register holds no active position, so the books state "
                     "no view either.")
    if bz.get("line"):
        parts.append(f"Against Book Z: {bz['line']}.")
    return {"state": "ok", "paragraph": " ".join(parts),
            "bounded_to": ["probabilities", "decisions", "benchmark"],
            "live_weights": len(scen), "active_decisions": len(open_)}


# ---------------------------------------------------------------------------
# 1. THE MONTH IN ONE PAGE -- five takeaways, each from a stored record
# ---------------------------------------------------------------------------
def takeaways(p: dict, back: dict, ahead: dict) -> list[dict]:
    cands: list[dict] = []
    wc = back.get("what_changed") or {}
    for r in wc.get("rows") or []:
        # State to state only: a dial gone absent is a data gap, and a takeaway
        # is about the market.
        if (r["what"].startswith(("dial ", "dimension "))
                and r.get("from") and r.get("to")):
            cands.append({"text": f"The {r['what']} moved from "
                                  f"{r.get('from') or 'absent'} to "
                                  f"{r.get('to') or 'absent'}.",
                          "sources": [r["source"]], "origin": "regime"})
    opened = [r for r in wc.get("rows") or [] if r["what"].startswith("exception ")
              and r.get("to") == "open"]
    if opened:
        cands.append({"text": f"{len(opened)} exception(s) opened in the object: "
                              + ", ".join(r["what"][10:] for r in opened[:3]) + ".",
                      "sources": [opened[0]["source"]], "origin": "regime"})
    for t in back.get("themes") or []:
        for it in t.get("items") or []:
            if it["kind"] == "story":
                cands.append({"text": f"[{it['tag']}] {it['text']} "
                                      f"({it['tier12_in_window']} tier-1-2 "
                                      f"headline(s) in the window).",
                              "sources": it["sources"][:2],
                              "origin": "looking_back"})
    for t in back.get("themes") or []:
        for it in t.get("items") or []:
            if it["kind"] == "release":
                cands.append({"text": f"[NEW] {t['name']}: {it['text']}.",
                              "sources": it["sources"], "origin": "looking_back"})
    for s in (ahead.get("scenarios") or [])[:1]:
        cands.append({"text": f"The highest live weight is {s['probability']}: "
                              f"{str(s['claim'])[:140].rstrip('.')}.",
                      "sources": [s["cite"]], "origin": "looking_ahead"})
    rg = p.get("regime") or {}
    if rg.get("state") == "ok":
        dials = ", ".join(f"{d['dial']} {d.get('state') or 'absent'}"
                          for d in rg.get("dials") or [])
        cands.append({"text": f"The dials read {dials}.",
                      "sources": [src("object", f"market_state@{rg.get('session')}",
                                      rg.get("session"))],
                      "origin": "regime"})
    out = []
    for c in cands:
        if len(out) == TAKEAWAYS:
            break
        if c["sources"] and all(s.get("id") and s.get("date") for s in c["sources"]):
            out.append({**c, "n": len(out) + 1})
    return out


# ---------------------------------------------------------------------------
# TIE-BACK SENTENCES -- deterministic, from where each takeaway came
# ---------------------------------------------------------------------------
_DEFAULT_TIE = {
    "month_in_one_page": "The five takeaways below are the month above, each "
                         "pinned to the stored record it came from.",
    "looking_back": "No takeaway is drawn from the themes this month; they are "
                    "the record behind the paragraph above.",
    "voices": "These are the voices that would test the paragraph above, each "
              "with its source and a status computed against last month.",
    "looking_ahead": "The calendar below is where the paragraph above gets "
                     "tested next.",
    "our_read": "This restates the weights and books the paragraph above "
                "rests on.",
    "regime": "The regime the paragraph above describes is this object's, read "
              "and never recomputed.",
    "scenarios": "These are the weights behind the paragraph's forward view, "
                 "each with its score.",
    "top_bottom": "No takeaway rests on Top & Bottom this month.",
    "alternative_assets": "No takeaway rests on the alternative assets this "
                          "month.",
    "register_month": "The register is where the paragraph's views would have "
                      "become decisions.",
    "appendix": "The series behind every figure above, one delta row each.",
}


def tie_backs(takes: list[dict]) -> dict[str, str]:
    out = {}
    for sec in TIE_BACK_SECTIONS:
        nums = [t["n"] for t in takes if t.get("origin") == sec]
        if nums:
            which = (f"Takeaway {nums[0]}" if len(nums) == 1 else
                     "Takeaways " + ", ".join(str(n) for n in nums[:-1])
                     + f" and {nums[-1]}")
            out[sec] = (f"{which} above {'is' if len(nums) == 1 else 'are'} read "
                        f"from this section.")
        else:
            out[sec] = _DEFAULT_TIE[sec]
    return out


def voices_block_for(win: tuple[str, str]) -> dict:
    """Section 4 (Phase B, 4 Oct 2026): the voices table with MONTHLY status,
    the four weeks' story evidence rolled up, the consensus line, and 13F where
    a voice's firm files one -- read from the stored rows, never fetched."""
    try:
        from daily_cascade import voices_block                  # noqa: PLC0415
        cutoff = win[1]
        month_end = (dt.date.fromisoformat(cutoff[:10])
                     - dt.timedelta(days=1)).isoformat()
        b = voices_block.month_block(month_end, cutoff, observations.DEFAULT_DB)
        return b
    except Exception as exc:                                    # noqa: BLE001
        return {"state": "fault",
                "reason": f"the voices register could not be read "
                          f"({type(exc).__name__})"}


# ---------------------------------------------------------------------------
# The Phase A sections, built onto an existing payload
# ---------------------------------------------------------------------------
def build(p: dict) -> dict:
    """The five v2 sections and the tie-backs, for payload `p` at its cutoff."""
    conn = _connect()
    try:
        win = window_of(p)
        back = looking_back(p, conn, win)
        ahead = looking_ahead(p, conn, win)
        read = our_read(p, conn, ahead)
        takes = takeaways(p, back, ahead)
        return {
            "month_in_markets": month_in_markets(p),
            "month_in_one_page": {
                "state": "ok" if takes else "empty",
                "reason": (None if takes else
                           "no stored record supports a takeaway this month"),
                "takeaways": takes,
                "takeaways_supported": len(takes),
                "paragraph": None},
            "looking_back": back,
            "voices": voices_block_for(win),
            "looking_ahead": ahead,
            "our_read": read,
            "tie_backs": tie_backs(takes),
        }
    finally:
        if conn is not None:
            conn.close()
