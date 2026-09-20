"""
The contradiction table, v1. Audit O.12 -- six computed pairs and one reserved.

A contradiction is TWO THINGS THAT NORMALLY MOVE TOGETHER, MOVING APART. The
table exists because the system's other outputs are each about one market, and
the most useful information in a dataset of several markets is usually the
disagreement between them: an index making new highs while participation narrows,
equities calm while credit widens, a long bond selling off while high yield does
not notice.

-----------------------------------------------------------------------------
THE MAGNITUDE IS THE z OF THE GAP, NOT THE GAP
-----------------------------------------------------------------------------

Two legs that normally sit far apart would fire every day on a raw gap. So each
leg is standardised over the SAME window (its own mean and standard deviation),
the gap between the standardised legs is computed FOR EVERY DAY in the window,
and the magnitude is today's gap expressed as a z of that gap's own history.

    z_a(t) = (a(t) - mean(a)) / sd(a)          over the window
    gap(t) = polarity_a * z_a(t) - polarity_b * z_b(t)
    magnitude = (gap(last) - mean(gap)) / sd(gap)

So 2.0 means "these two are further apart than they have been 95% of the time",
which is a claim about the relationship rather than about either level.

The two legs are aligned on COMMON DATES first. A weekly series against a daily
one would otherwise produce a gap series that mostly measures which day it is.

-----------------------------------------------------------------------------
OPEN, CLOSED, AND WHY A ROW DOES NOT OPEN ON ITS FIRST DAY
-----------------------------------------------------------------------------

The condition is |magnitude| >= open_threshold_z. A row OPENS once the condition
has held persistence_sessions consecutive sessions, and CLOSES the same way --
the identical rule the dimensions use, for the identical reason: a single day's
disagreement is noise, and a table that opened a row on it would cry wolf until
nobody read it.

`since` is the first session of the current run, and persistence_days counts it.
At or past exception_sessions the row is an EXCEPTION.

THE EXCEPTION IS REPORT-ONLY, AND SAYS SO ON THE ROW. The order asks for it to be
wired into the Phase 1 exceptions alert path "if one exists; otherwise
report-only and say so". It does not exist: scripts/check_heartbeat_cron.sh sends
the heartbeat and drift alerts through scripts/send_smtp_alert.py, and nothing in
this repo sends an exceptions alert. So every exception row carries
alert_path=report_only and the note naming where the branch belongs.

-----------------------------------------------------------------------------
WHAT IS ABSENT TODAY, AND WHY THAT IS THE FINDING
-----------------------------------------------------------------------------

Five of the six computable pairs have a leg the store does not carry -- trend,
breadth, realized volatility and the sector ratio all need equity prices. So v1
computes ONE row, long bond versus high yield, which happens to be the pair the
order calls "the standing watch line". Each absent row names its missing leg
rather than being dropped, because a table that silently shrinks to its available
rows reads as a table with nothing to report.
"""

from __future__ import annotations

import statistics
from typing import Any, Optional

from altdata import derived, observations

RESERVED_KIND = "reserved"


# ---------------------------------------------------------------------------
# Leg resolution -- a leg is a metric, a dimension, or a dial
# ---------------------------------------------------------------------------
def resolve_leg(leg: str, dims: dict, dials: dict) -> dict:
    """What series (or state) a declared leg refers to.

    A DIMENSION LEG RESOLVES TO ITS PRIMARY MEMBER, with the dimension's own
    polarity already folded in -- so `trend vs credit` compares the two things the
    dimensions are actually built on rather than their band labels, which are too
    coarse to take a z of.
    """
    if leg.startswith("dial."):
        name = leg.split(".", 1)[1]
        d = dials.get(name) or {}
        return {"kind": "dial", "name": leg, "state": d.get("state"),
                "absent_reason": d.get("absent_reason")}
    if leg in dims:
        d = dims[leg]
        members = d.get("members") or []
        if not members:
            return {"kind": "dimension", "name": leg, "metric": None,
                    "absent_reason": f"dimension {leg} declares no members"}
        primary = members[0]
        return {"kind": "dimension", "name": leg,
                "metric": primary.get("metric"),
                "polarity": int(primary.get("polarity", 1)),
                "state": d.get("state"),
                "absent_reason": d.get("absent_reason")}
    return {"kind": "metric", "name": leg, "metric": leg, "polarity": 1}


# ---------------------------------------------------------------------------
# The statistic
# ---------------------------------------------------------------------------
def standardise(values: list[float]) -> Optional[list[float]]:
    if len(values) < 3:
        return None
    try:
        sd = statistics.stdev(values)
    except statistics.StatisticsError:
        return None
    if sd == 0:
        return None
    mean = statistics.fmean(values)
    return [(v - mean) / sd for v in values]


def gap_z(a: list[tuple[str, float]], b: list[tuple[str, float]],
          pol_a: int, pol_b: int) -> dict:
    """Today's standardised gap, as a z of the gap's own history."""
    da, db = dict(a), dict(b)
    common = sorted(set(da) & set(db))
    if len(common) < 30:
        return {"magnitude": None, "n": len(common),
                "absent_reason": (
                    f"only {len(common)} dates are common to both legs; a gap's "
                    f"own distribution needs at least 30 to mean anything")}
    za = standardise([da[d] for d in common])
    zb = standardise([db[d] for d in common])
    if za is None or zb is None:
        return {"magnitude": None, "n": len(common),
                "absent_reason": "a leg has no variation over the window, so a "
                                 "standardised gap is undefined"}
    gaps = [pol_a * x - pol_b * y for x, y in zip(za, zb)]
    sd = statistics.stdev(gaps)
    if sd == 0:
        return {"magnitude": None, "n": len(common),
                "absent_reason": "the gap never varies over the window"}
    mean = statistics.fmean(gaps)
    return {"magnitude": round((gaps[-1] - mean) / sd, 4),
            "gap_today": round(gaps[-1], 4),
            "gap_mean": round(mean, 4),
            "gap_sd": round(sd, 4),
            "n": len(common),
            "aligned_first": common[0], "aligned_last": common[-1]}


# ---------------------------------------------------------------------------
# Persistence over the stored history
# ---------------------------------------------------------------------------
def prior_rows(history: list[dict], pair_id: str) -> list[dict]:
    out = []
    for obj in history:
        for r in obj.get("contradictions") or []:
            if r.get("id") == pair_id:
                out.append({"session": obj.get("session"), **r})
    return out


def apply_persistence(row: dict, prior: list[dict], session_day: str,
                      persistence: int, exception_at: int) -> dict:
    """Open after `persistence` consecutive sessions meeting the condition."""
    cond = bool(row.get("condition_met"))
    run = 1 if cond else 0
    for p in reversed(prior):
        if bool(p.get("condition_met")) == cond:
            run += 1
        else:
            break
    row["run_sessions"] = run

    was_open = bool(prior[-1].get("open")) if prior else False
    if cond and (run >= persistence or was_open):
        row["open"] = True
        row["open_state"] = "open"
        since = session_day
        for p in reversed(prior):
            if bool(p.get("condition_met")):
                since = p.get("since") or p.get("session") or since
            else:
                break
        row["since"] = since
        row["persistence_days"] = run
    elif cond:
        row["open"] = False
        row["open_state"] = "pending"
        row["since"] = None
        row["persistence_days"] = run
        row["pending_note"] = (f"the condition has held {run} of the "
                               f"{persistence} sessions required to open")
    else:
        row["open"] = False
        row["open_state"] = "closed"
        row["since"] = None
        row["persistence_days"] = 0
        if was_open:
            row["closed_note"] = (
                f"closed: the condition failed after {run} session(s) below "
                f"the threshold")

    row["exception"] = bool(row.get("open") and
                            row.get("persistence_days", 0) >= exception_at)
    return row


# ---------------------------------------------------------------------------
# One pair
# ---------------------------------------------------------------------------
def evaluate_pair(spec: dict, dims: dict, dials: dict, as_of: str,
                  session_day: str, window: int, threshold: float,
                  max_stale: int,
                  store: observations.ObservationStore) -> dict:
    pid = str(spec.get("id"))
    legs = list(spec.get("legs") or [])
    row: dict[str, Any] = {
        "id": pid, "legs": legs, "kind": spec.get("kind"),
        "expect": spec.get("expect"), "because": spec.get("because"),
        "magnitude": None, "since": None, "persistence_days": 0,
        "open": False, "open_state": "absent", "condition_met": False,
        "threshold_z": threshold,
    }

    if spec.get("kind") == RESERVED_KIND:
        row["absent_reason"] = (
            f"RESERVED. Requires {spec.get('requires')}, which does not exist. "
            f"The row is declared now so the table's shape is fixed and the pair "
            f"cannot be forgotten when it does.")
        return row

    if len(legs) != 2:
        row["absent_reason"] = f"{pid} declares {len(legs)} legs, not two"
        return row

    pols = list(spec.get("polarities") or [])
    a = resolve_leg(str(legs[0]), dims, dials)
    b = resolve_leg(str(legs[1]), dims, dials)
    row["leg_detail"] = [a, b]

    # A DIAL PAIR HAS NO SERIES. gamma is a sign the exposure engine wrote down,
    # not a number with a distribution, so this pair is a STATE MISMATCH and its
    # magnitude is honestly None rather than a z of something invented.
    if a["kind"] == "dial" or b["kind"] == "dial":
        for leg in (a, b):
            if leg.get("state") is None:
                row["absent_reason"] = (
                    f"{leg['name']} has no state: "
                    f"{leg.get('absent_reason') or 'absent'}")
                return row
        pair = (str(a.get("state")), str(b.get("state")))
        mismatch = {("negative", "up"), ("positive", "down")}
        row["states"] = pair
        row["condition_met"] = pair in mismatch
        row["magnitude"] = None
        row["magnitude_note"] = (
            "a dial pair is a STATE MISMATCH, not a z: dealer gamma is a sign "
            "the exposure engine wrote down, and a z of a sign would be a number "
            "with no meaning")
        row["mismatch_rule"] = sorted(f"{x}/{y}" for x, y in mismatch)
        return row

    for leg in (a, b):
        if not leg.get("metric"):
            row["absent_reason"] = (f"{leg['name']} resolves to no metric: "
                                    f"{leg.get('absent_reason') or 'absent'}")
            return row

    sa = derived.series_as_of(a["metric"], as_of, window=window, store=store)
    sb = derived.series_as_of(b["metric"], as_of, window=window, store=store)
    if not sa or not sb:
        missing = [leg["metric"] for leg, s in ((a, sa), (b, sb)) if not s]
        row["absent_reason"] = (
            f"no observations for {missing} knowable at {as_of}"
            + (" -- the store carries no equity price series; nothing schedules "
               "yfinance_source.py" if any(str(m).startswith("mkt_")
                                           for m in missing) else ""))
        return row

    # STALENESS, LEG BY LEG. A gap between two prints from May is not a
    # divergence today. The first run of this table reported an unchanging
    # z = +0.17 for 77 consecutive sessions off data that stopped moving on
    # 28 May, which looks exactly like a working row and is not one.
    stale_legs = []
    for leg, ser in ((a, sa), (b, sb)):
        n_stale, _ = derived.sessions_between(ser[-1][0], str(as_of)[:10])
        if n_stale > max_stale:
            stale_legs.append(f"{leg['metric']} last observed {ser[-1][0]}, "
                              f"{n_stale} sessions back")
    if stale_legs:
        row["absent_reason"] = (
            "; ".join(stale_legs) + f" -- against a declared allowance of "
            f"{max_stale} sessions. A gap measured between stale prints is not a "
            f"divergence today")
        return row

    pol_a = int(pols[0]) if len(pols) == 2 else int(a.get("polarity", 1))
    pol_b = int(pols[1]) if len(pols) == 2 else int(b.get("polarity", 1))
    if spec.get("expect") == "opposite":
        pol_b = -pol_b
    elif spec.get("expect") not in (None, "same"):
        row["absent_reason"] = (f"expect {spec.get('expect')!r} is not "
                                f"implemented in v1 (same | opposite)")
        return row

    stat = gap_z(sa, sb, pol_a, pol_b)
    row.update(stat)
    row["polarities_used"] = [pol_a, pol_b]
    row["metrics"] = [a["metric"], b["metric"]]
    if stat.get("magnitude") is None:
        return row

    row["open_state"] = "closed"
    row["condition_met"] = abs(stat["magnitude"]) >= threshold

    # The extra leg pair 4 declares. Read, or reported absent -- never assumed.
    extra = spec.get("also_reads")
    if extra:
        row["also_reads"] = {"what": extra, "value": None,
                             "absent_reason": _tail_weight_absent(extra)}
    return row


def _tail_weight_absent(what: str) -> Optional[str]:
    """Whether the probability ledger has a live tail weight to read."""
    try:
        from altdata import probability_ledger
        store = probability_ledger.LedgerStore()
        try:
            rows = store.unresolved() if hasattr(store, "unresolved") else []
        finally:
            if hasattr(store, "close"):
                store.close()
        if rows:
            return None
        return (f"{what}: the probability ledger holds no live tail-family "
                f"probability, so there is nothing to read. It is seeded from "
                f"the Monthly's scenario weights only.")
    except Exception as exc:
        return (f"{what}: the probability ledger could not be read "
                f"({type(exc).__name__}) -- reported absent rather than assumed")


# ---------------------------------------------------------------------------
# The table
# ---------------------------------------------------------------------------
def evaluate(cfg: dict, dims: dict, dials: dict, as_of: str, session_day: str,
             history: list[dict],
             store: observations.ObservationStore) -> list[dict]:
    spec = cfg.get("contradictions") or {}
    window = int(spec.get("window_days")
                 or (cfg.get("defaults") or {}).get("window_days")
                 or derived.DEFAULT_WINDOW_DAYS)
    threshold = float(spec.get("open_threshold_z") or 2.0)
    persistence = int(spec.get("persistence_sessions") or 2)
    exception_at = int(spec.get("exception_sessions") or 5)
    max_stale = int(spec.get("max_staleness_sessions")
                    or (cfg.get("defaults") or {}).get("max_staleness_sessions")
                    or 10)
    alert_path = str(spec.get("exception_alert_path") or "report_only")
    alert_note = spec.get("exception_alert_note")

    rows = []
    for pair in spec.get("pairs") or []:
        row = evaluate_pair(pair or {}, dims, dials, as_of, session_day,
                            window, threshold, max_stale, store)
        if row.get("open_state") != "absent" or row.get("magnitude") is not None \
                or row.get("states"):
            apply_persistence(row, prior_rows(history, row["id"]), session_day,
                              persistence, exception_at)
        if row.get("exception"):
            row["alert_path"] = alert_path
            row["alert_note"] = alert_note
        rows.append(row)
    return rows
