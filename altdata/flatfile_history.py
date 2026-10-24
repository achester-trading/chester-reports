"""
When a rank may read the flat-file history (signal-triage Batch 11, decision D4,
ruled 19 Oct 2026).

tools/massive_flatfiles_backfill.py writes two years of per-name readings from
Massive's options day bars under the same keys as our captures, with the source
`chain_capture:flatfiles`, labelled "from last-trade closes, not mids". A rank reads
that history ONLY where its overlap with the captured history agrees within a
tolerance pre-registered in docs/briefs/a48-batch11-notes.md (and here, unchanged):

  overlap   at least 10 sessions on which both a captured and a flat-file reading
            exist for the same name and key;
  agreement the median absolute difference over the overlap is at most:
              chain.iv30_atm          1.5 vol points
              chain.skew_25d_put      1.5 vol points
              chain.rr_25d            2.0 vol points
              chain.put_share_volume  5.0 percentage points

Otherwise the flat-file rows are stored and unused. Where both exist on a session,
the captured reading wins.

A DATED ADDITION (signal-triage Batch 13, item 61, D5; a54, 20 Oct 2026; session-set).
The four tolerances above and the 10-session overlap are A48's pre-registration and
stay exactly as they are. Beside them, the backfill's daily volume per name joins
under its own rule, a RELATIVE one:

  chain.options_volume, chain.call_volume, chain.put_volume
            the median over the overlap of |captured - flat-file| / captured is at
            most 0.10 (10%), with the same 10-session overlap

Relative, because volume is in contracts and its scale differs by name by orders of
magnitude (an index fund trades millions a day, a single name thousands), so no one
absolute tolerance could serve every name. 10%, because the two readings are not
the same instant: our capture is the session's last snapshot (16:10 ET, the vendor
names 16:16) and the day aggregate is the whole day's trades, so late prints make
the flat file a little larger; a median gap within a tenth says the two count the
same trading, and one past it says they do not. Where both exist on a session, the
captured reading still wins.
"""

from __future__ import annotations

import statistics
from typing import Optional

SOURCE = "chain_capture:flatfiles"
LABEL = "from last-trade closes, not mids"
MIN_OVERLAP = 10
TOLERANCE = {"chain.iv30_atm": 1.5, "chain.skew_25d_put": 1.5, "chain.rr_25d": 2.0,
             "chain.put_share_volume": 5.0}
# Batch 13 D5 (a54, 20 Oct 2026; session-set): the volume keys' RELATIVE tolerance,
# the median of |captured - flat-file| / captured over the overlap.
VOLUME_TOLERANCE_REL = {"chain.options_volume": 0.10, "chain.call_volume": 0.10,
                        "chain.put_volume": 0.10}


def is_flatfile(row: dict) -> bool:
    return str(row.get("source") or "").startswith(SOURCE)


def admitted(captured: dict[str, float], flat: dict[str, float], key: str) -> bool:
    """Does the flat-file history agree with ours on their overlap?"""
    both = sorted(set(captured) & set(flat))
    rel = VOLUME_TOLERANCE_REL.get(key)
    if rel is not None:
        both = [d for d in both if captured[d]]
        if len(both) < MIN_OVERLAP:
            return False
        return statistics.median(abs(captured[d] - flat[d]) / abs(captured[d])
                                 for d in both) <= rel
    tol = TOLERANCE.get(key)
    if tol is None or len(both) < MIN_OVERLAP:
        return False
    return statistics.median(abs(captured[d] - flat[d]) for d in both) <= tol


RAW_SQL = ("SELECT observed_at, value_num, source, available_at FROM observations "
           "WHERE registry_key = :key AND instrument IS :inst AND available_at <= :now "
           "AND value_num IS NOT NULL ORDER BY observed_at, available_at")


def rows_both(st, key: str, now: str, inst=None) -> list[dict]:
    """Each date's latest knowable row OF EACH KIND (captured, flat-file). The as-of
    join keeps only a date's newest instant, and a flat-file row (published the
    next morning) is always newer than the capture it would then hide; so the two
    kinds are read apart. A store without a connection (a gate's stand-in) falls
    back to the join."""
    conn = getattr(st, "conn", None)
    if conn is None or (key not in TOLERANCE and key not in VOLUME_TOLERANCE_REL):
        return list(st.as_of(key, now, inst) or [])
    from altdata.observations import canonical_instant           # noqa: PLC0415
    cur = conn.execute(RAW_SQL, {"key": key, "inst": inst, "now": canonical_instant(now)})
    last: dict[tuple[str, bool], dict] = {}
    for r in cur.fetchall():
        d = dict(zip(("observed_at", "value_num", "source", "available_at"), tuple(r)))
        last[(str(d["observed_at"])[:10], is_flatfile(d))] = d
    return list(last.values())


def merged(rows: list[dict], key: str) -> tuple[dict[str, float], Optional[str]]:
    """({day: value}, the note): the captured readings, joined by the flat-file
    ones only when admitted; the note says which."""
    cap, flat = {}, {}
    for r in rows:
        if r.get("value_num") is None:
            continue
        (flat if is_flatfile(r) else cap)[str(r["observed_at"])[:10]] = float(r["value_num"])
    if not flat:
        return cap, None
    if admitted(cap, flat, key):
        return {**flat, **cap}, f"earlier history {LABEL}"
    return cap, None
