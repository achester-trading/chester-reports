"""
regime.py -- the market-state object, v1.

Audit #3 §K and O.5: ONE object, computed by the close pass, versioned, stored as
an observation with available_at, and read by every report. Nothing else in the
system computes a regime.

    python -m regime compute --as-of 2026-09-18
    python -m regime show   --as-of 2026-09-18
    python -m regime backfill --from 2022-04-21 --to 2026-09-18
    python -m regime print  --as-of 2026-09-18        # the WHAT CHANGED block

-----------------------------------------------------------------------------
WHAT THIS MODULE DOES NOT CONTAIN
-----------------------------------------------------------------------------

No dimension, no metric id, no threshold and no polarity. All of it is
config/market_state.yaml, because a threshold in code is a threshold that gets
tuned in a commit nobody reads as a change of belief. This file is the machinery:
read the config, score each member through altdata.derived, apply the declared
bands, apply persistence, store the result.

It also computes no dealer gamma. The exposure engine owns that and the order
says read it, so the gamma dial reads altdata.grader's own reader. A second
implementation would be a second answer.

-----------------------------------------------------------------------------
THREE RULES FROM §K, ENFORCED HERE
-----------------------------------------------------------------------------

1. A DIMENSION CHANGES STATE ONLY ON A DECLARED RULE, and not on the first
   reading that disagrees. `persistence_sessions` (default 2) means a new raw
   state must hold across that many consecutive session computations before the
   published state moves. Until it does the object carries the OLD state plus
   `pending_state` and `pending_since` -- which is the honest rendering of "it
   looks like it is turning and has not turned yet", and it is why a dimension
   does not flap across a single noisy print.

2. `contradicting` IS NEVER EMPTY BY OMISSION. A dimension with no disagreeing
   member records the string "none found" as a positive claim, so a reader can
   tell "we looked and everything agreed" from "nobody looked".

3. AN ABSENT DIMENSION SAYS WHY. No series, no fresh series, no registry entry --
   each is a different absence and each is named. Never a faked state, and never
   a stale state presented as a current one: past `max_staleness_sessions` the
   dimension is absent with the staleness in the reason.

-----------------------------------------------------------------------------
ONE OBJECT PER SESSION DAY
-----------------------------------------------------------------------------

The object is stored under registry_key `market_state` with observed_at = the
SESSION DATE and available_at = the compute instant. A recompute of the same day
is therefore a REVISION of that day's object, not a second object: the as-of join
returns the latest revision knowable at any cutoff, so readers always see one
object per day and a replay from a past cutoff sees the one that existed then.

That is the limit to know about. If two computes disagree, the second wins for
every future reader, and the first is still in the store as a vintage --
`observations.vintages("market_state", day)` is the audit trail.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any, Optional

from altdata import derived, observations, session

REPO = Path(__file__).resolve().parent
CONFIG_PATH = REPO / "config" / "market_state.yaml"

SCHEMA_VERSION = "market-state-v1"
STORE_KEY = "market_state"

# Fields that are PROVENANCE, not content. An exact replay compares everything
# else: the compute instant and the code revision necessarily differ between the
# stored object and a recomputation of it, and asserting on them would make the
# replay check impossible to pass rather than meaningful. Every number the object
# asserts about the market is compared.
REPLAY_EXCLUDE = ("computed_at", "available_at", "ingested_at", "git_sha",
                  "config_path")

NONE_FOUND = "none found"


# ---------------------------------------------------------------------------
# Config and provenance
# ---------------------------------------------------------------------------
_CONFIG: Optional[dict] = None


def load_config(path: Optional[Path] = None) -> dict:
    global _CONFIG
    if _CONFIG is not None and path is None:
        return _CONFIG
    import yaml
    with (path or CONFIG_PATH).open(encoding="utf-8") as fp:
        cfg = yaml.safe_load(fp) or {}
    if path is None:
        _CONFIG = cfg
    return cfg


def git_sha() -> str:
    """The revision that computed an object. Provenance, per §K's `version`."""
    try:
        out = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short",
                              "HEAD"], capture_output=True, text=True,
                             timeout=10)
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Scoring one member
# ---------------------------------------------------------------------------
def effective_percentile(pct: Optional[float], polarity: int) -> Optional[float]:
    """The member's percentile ON THE DIMENSION'S OWN SCALE.

    Polarity +1 passes it through; -1 flips it, because for half these series a
    HIGH reading means the opposite of the dimension's first-listed state -- a
    wide HY spread is stressed credit, a big RRP balance is tight liquidity.
    Getting one of these backwards inverts a whole dimension, which is why each
    polarity carries a `because` line in the config.
    """
    if pct is None:
        return None
    return round(pct if polarity >= 0 else 100.0 - pct, 4)


def band_state(pct: Optional[float], bands: list[dict]) -> Optional[str]:
    """First declared band whose min_percentile the reading reaches."""
    if pct is None:
        return None
    for b in bands:
        if pct >= float(b.get("min_percentile", 0)):
            return str(b.get("state"))
    return None


def score_member(spec: dict, as_of: str, window: int,
                 store: observations.ObservationStore) -> dict:
    metric = str(spec.get("metric"))
    polarity = int(spec.get("polarity", 1))
    d = derived.derived_forms(metric, as_of, window=window, store=store)
    return {
        "metric": metric,
        "polarity": polarity,
        "because": spec.get("because"),
        "level": d["level"],
        "percentile_raw": d["percentile"],
        "percentile": effective_percentile(d["percentile"], polarity),
        "delta_unit": d["delta_unit"],
        "delta_5d": d["delta_5d"],
        "delta_20d": d["delta_20d"],
        "rate_of_change": d["rate_of_change"],
        "z_score": d["z_score"],
        "extreme": d["extreme"],
        "confidence": d["confidence"],
        "confidence_reason": d["confidence_reason"],
        "n": d["n"],
        "observed_at": d["observed_at"],
        "staleness_sessions": d["staleness_sessions"],
        "staleness_allowance_sessions": d["staleness_allowance_sessions"],
        "registered": d["registered"],
        "absent_reason": d.get("absent_reason"),
    }


# ---------------------------------------------------------------------------
# One dimension
# ---------------------------------------------------------------------------
def compute_dimension(name: str, spec: dict, as_of: str, defaults: dict,
                      store: observations.ObservationStore) -> dict:
    window = int(spec.get("window_days") or defaults.get("window_days")
                 or derived.DEFAULT_WINDOW_DAYS)
    max_stale = int(spec.get("max_staleness_sessions")
                    or defaults.get("max_staleness_sessions") or 10)
    persistence = int(spec.get("persistence_sessions")
                      or defaults.get("persistence_sessions") or 2)
    bands = spec.get("bands") or []
    members = spec.get("members") or []

    out: dict[str, Any] = {
        "dimension": name,
        "horizon": spec.get("horizon"),
        "states_declared": spec.get("states") or [b.get("state") for b in bands],
        "persistence_sessions": persistence,
        "max_staleness_sessions": max_stale,
        "window_days": window,
        "note": spec.get("note"),
        "state": None, "direction": None, "rate_of_change": None,
        "percentile": None, "confidence": "low",
        "supporting": [], "contradicting": NONE_FOUND,
        "members": [],
    }
    if not members or not bands:
        out["absent_reason"] = (
            f"{name} declares no {'members' if not members else 'bands'} in "
            f"config/market_state.yaml")
        return out

    scored = [score_member(m, as_of, window, store) for m in members]
    out["members"] = scored
    primary = scored[0]

    # RULE 3. Three different absences, three different reasons.
    if primary["percentile"] is None:
        out["absent_reason"] = (
            f"no observation for the primary member {primary['metric']} "
            f"knowable at {as_of}"
            + ("" if primary["registered"] else
               f" (and {primary['metric']} has no registry entry)"))
        return out
    stale = primary["staleness_sessions"]
    if stale is not None and stale > max_stale:
        out["absent_reason"] = (
            f"the primary member {primary['metric']} was last observed "
            f"{primary['observed_at']}, {stale} sessions before this cutoff, "
            f"against a declared allowance of {max_stale}. A state computed "
            f"from it would be a stale state presented as a current one")
        out["stalest_observation"] = primary["observed_at"]
        return out

    raw_state = band_state(primary["percentile"], bands)
    out["raw_state"] = raw_state
    out["percentile"] = primary["percentile"]
    out["rate_of_change"] = primary["rate_of_change"]
    roc = primary["rate_of_change"]
    if roc is None:
        out["direction"] = "0"
        out["direction_reason"] = (
            f"{primary['metric']} has no measured rate of change at this "
            f"cutoff -- no lookback resolved to a different observation")
    else:
        signed = roc * primary["polarity"]
        out["direction"] = "+" if signed > 0 else ("-" if signed < 0 else "0")
        out["direction_reason"] = (
            f"{primary['metric']} rate_of_change {roc} "
            f"({primary['delta_unit']}/session) x polarity "
            f"{primary['polarity']:+d}")

    # RULE 2. Supporting and contradicting are metric ids, and contradicting is
    # never empty by omission.
    supporting, contradicting = [], []
    for m in scored[1:]:
        if m["percentile"] is None:
            continue
        their = band_state(m["percentile"], bands)
        (supporting if their == raw_state else contradicting).append(m["metric"])
    out["supporting"] = supporting
    out["contradicting"] = contradicting if contradicting else NONE_FOUND
    out["members_unavailable"] = [m["metric"] for m in scored[1:]
                                  if m["percentile"] is None]

    # Confidence: the primary's, downgraded one step when the evidence is
    # against it. Derived, never authored -- there is no argument that sets it.
    conf = primary["confidence"]
    if contradicting and len(contradicting) > len(supporting):
        conf = {"high": "med", "med": "low", "low": "low"}[conf]
        out["confidence_reason"] = (
            f"{primary['confidence']} on the primary ({primary['confidence_reason']}), "
            f"downgraded because {len(contradicting)} members disagree and "
            f"{len(supporting)} agree")
    else:
        out["confidence_reason"] = primary["confidence_reason"]
    out["confidence"] = conf
    return out


# ---------------------------------------------------------------------------
# Persistence -- rule 1
# ---------------------------------------------------------------------------
def prior_objects(as_of: str, before_session: str, limit: int,
                  store: observations.ObservationStore) -> list[dict]:
    """The most recent stored objects for sessions before `before_session`.

    As-of correct in BOTH directions: only objects knowable at `as_of`, and only
    sessions strictly before the one being computed. A backfill that read the
    object it was about to overwrite would manufacture its own persistence.
    """
    rows = store.as_of(STORE_KEY, as_of=as_of)
    out = []
    for r in rows:
        if str(r["observed_at"])[:10] >= before_session:
            continue
        try:
            out.append(json.loads(r["value_text"]))
        except Exception:
            continue
    return out[-limit:] if limit else out


def apply_persistence(dim: dict, name: str, history: list[dict]) -> dict:
    """Publish a new state only after it has held `persistence_sessions` times."""
    raw = dim.get("raw_state")
    need = int(dim.get("persistence_sessions") or 2)
    prev_published = None
    prev_last_changed = None
    for obj in reversed(history):
        d = (obj.get("dimensions") or {}).get(name) or {}
        if d.get("state"):
            prev_published = d["state"]
            prev_last_changed = d.get("last_changed")
            break

    if raw is None:                       # absent; nothing to publish
        dim["state"] = None
        return dim
    if prev_published is None:            # first object ever for this dimension
        dim["state"] = raw
        dim["last_changed"] = dim.get("as_of_session")
        dim["persistence"] = f"first object; published {raw} immediately"
        return dim
    if raw == prev_published:
        dim["state"] = raw
        dim["last_changed"] = prev_last_changed
        dim["persistence"] = f"unchanged, held since {prev_last_changed}"
        return dim

    # The raw reading disagrees with what is published. Count how many of the
    # most recent objects ALSO read raw -- including this one.
    run = 1
    for obj in reversed(history):
        d = (obj.get("dimensions") or {}).get(name) or {}
        if d.get("raw_state") == raw:
            run += 1
        else:
            break
    if run >= need:
        dim["state"] = raw
        dim["last_changed"] = dim.get("as_of_session")
        dim["persistence"] = (
            f"changed from {prev_published}: {raw} held {run} consecutive "
            f"sessions, meeting the declared {need}")
    else:
        dim["state"] = prev_published
        dim["pending_state"] = raw
        dim["pending_sessions"] = run
        dim["last_changed"] = prev_last_changed
        dim["persistence"] = (
            f"{raw} has held {run} of the {need} sessions required; publishing "
            f"{prev_published} until it does")
    return dim


# ---------------------------------------------------------------------------
# The dials
# ---------------------------------------------------------------------------
def dial_macro(cfg: dict, dims: dict) -> dict:
    spec = (cfg.get("dials") or {}).get("macro") or {}
    inputs = {k: (dims.get(k) or {}).get("state")
              for k in (spec.get("from_dimensions") or [])}
    absent = [k for k, v in inputs.items() if v is None]

    # THE CATCH-ALL IS FOR DIMENSIONS THAT DISAGREE, NOT FOR DIMENSIONS THAT ARE
    # MISSING. A rule with an empty `when` matches anything, including an object
    # where every input is absent -- which would have published macro=mixed off
    # no data at all. "Mixed" is a claim about readings that exist.
    used = [k for k in inputs if k in
            {kk for r in (spec.get("rules") or []) for kk in (r.get("when") or {})}]
    missing_used = [k for k in used if inputs.get(k) is None]
    if missing_used:
        return {"dial": "macro", "state": None, "inputs": inputs,
                "inputs_absent": absent,
                "absent_reason": (
                    f"the declared rules read {sorted(used)} and "
                    f"{sorted(missing_used)} "
                    f"{'is' if len(missing_used) == 1 else 'are'} absent; "
                    f"the catch-all rule is for readings that disagree, not for "
                    f"readings that do not exist"),
                "note": spec.get("note")}

    for rule in spec.get("rules") or []:
        when = rule.get("when") or {}
        if all(inputs.get(k) == v for k, v in when.items()):
            return {"dial": "macro", "state": str(rule.get("state")),
                    "inputs": inputs, "matched_rule": when or "catch-all",
                    "inputs_absent": absent, "note": spec.get("note")}
    return {"dial": "macro", "state": None, "inputs": inputs,
            "inputs_absent": absent,
            "absent_reason": "no declared macro rule matched, and the config "
                             "carries no catch-all",
            "note": spec.get("note")}


def dial_vol(cfg: dict, as_of: str,
             store: observations.ObservationStore) -> dict:
    spec = (cfg.get("dials") or {}).get("vol") or {}
    primary = str(spec.get("primary") or "")
    d = derived.derived_forms(primary, as_of, store=store) if primary else {}
    out: dict[str, Any] = {"dial": "vol", "primary": primary,
                           "level": d.get("level"),
                           "percentile": d.get("percentile"),
                           "confidence": d.get("confidence"),
                           "state": None}
    level = d.get("level")
    if level is None:
        out["absent_reason"] = (f"no observation for {primary} knowable at "
                                f"{as_of}")
    else:
        for b in spec.get("level_bands") or []:
            if level >= float(b.get("min_level", 0)):
                out["state"] = str(b.get("state"))
                out["matched_band"] = b
                break
        stale = d.get("staleness_sessions")
        allow = d.get("staleness_allowance_sessions")
        if stale is not None and allow is not None and stale > 3 * allow:
            out["state"] = None
            out["absent_reason"] = (
                f"{primary} was last observed {d.get('observed_at')}, {stale} "
                f"sessions before this cutoff -- a vol dial is a statement "
                f"about today")

    # The two legs that are gated on data the store does not have. Both report
    # absent with the reason; neither is approximated from something else.
    ri = spec.get("realized_implied") or {}
    ri_metric = str(ri.get("metric") or "")
    ri_rows = store.as_of(ri_metric, as_of=as_of) if ri_metric else []
    out["realized_implied"] = {
        "state": None,
        "absent_reason": (None if ri_rows else
                          f"{ri_metric} is not in the store, so realized "
                          f"volatility cannot be computed -- the dial is "
                          f"implied-only"),
        "note": ri.get("note")}
    ts = spec.get("term_structure") or {}
    need = list(ts.get("requires_store_keys") or [])
    have = [k for k in need if store.as_of(k, as_of=as_of)]
    out["term_structure"] = {
        "state": None,
        "requires": need,
        "present": have,
        "absent_reason": (None if need and len(have) == len(need) else
                          f"requires {need}; the store has {have or 'none of them'}"),
        "note": ts.get("note")}
    return out


def dial_gamma(cfg: dict, session_date: str) -> dict:
    """READ from the exposure engine, never recomputed."""
    spec = (cfg.get("dials") or {}).get("gamma") or {}
    sym = str(spec.get("symbol") or "SPY")
    out: dict[str, Any] = {"dial": "gamma", "symbol": sym,
                           "source": spec.get("source"), "state": None,
                           "note": spec.get("note")}
    try:
        from altdata import grader
        # PriceSeries reads the PIN LOG -- the system's own record of what it saw
        # at the close, net_gex included. That is the right source for "read, do
        # not recompute": it is not a number this module derived, it is the number
        # the EOD pass wrote down at the time.
        book = grader.PriceSeries()
        sign = book.gamma_sign(sym, session_date)
    except Exception as exc:
        out["absent_reason"] = (f"the exposure engine's reader raised "
                                f"{type(exc).__name__}: {exc}")
        return out
    if sign is None:
        out["absent_reason"] = (
            f"no exposure profile for {sym} at or before {session_date} -- the "
            f"EOD pass produced none, and this dial does not recompute gamma")
        return out
    out["state"] = sign
    out["read_from"] = "altdata.grader.PriceBook.gamma_sign"
    return out


# ---------------------------------------------------------------------------
# The object
# ---------------------------------------------------------------------------
def compute(as_of: Optional[str] = None, session_day: Optional[str] = None,
            store: Optional[observations.ObservationStore] = None,
            cfg: Optional[dict] = None) -> dict:
    """The market-state object for one session, as-of correct at `as_of`.

    `session_day` is the session the object is ABOUT; `as_of` is the cutoff it
    may know. For a live close pass they are the same evening. For a backfill,
    `as_of` is set to the session's own evening so the object contains only what
    was knowable then -- which is what makes the history usable for grading.
    """
    cfg = cfg or load_config()
    own = store is None
    st = store or observations.ObservationStore()
    try:
        day = session_day or session.last_trading_session().isoformat()
        cutoff = as_of or session.utc_iso(timespec="microseconds")
        defaults = cfg.get("defaults") or {}

        dims: dict[str, dict] = {}
        for name, spec in (cfg.get("dimensions") or {}).items():
            d = compute_dimension(name, spec or {}, cutoff, defaults, st)
            d["as_of_session"] = day
            dims[name] = d

        history = prior_objects(cutoff, day, limit=8, store=st)
        for name, d in dims.items():
            apply_persistence(d, name, history)

        obj = {
            "object": "market_state",
            "schema_version": SCHEMA_VERSION,
            "config_version": cfg.get("version"),
            "session": day,
            "as_of": cutoff,
            "computed_at": session.utc_iso(),
            "git_sha": git_sha(),
            "config_path": str(CONFIG_PATH.relative_to(REPO)).replace("\\", "/"),
            "derived_convention": derived.CONVENTION_VERSION,
            "dimensions": dims,
            "dials": {
                "macro": dial_macro(cfg, dims),
                "vol": dial_vol(cfg, cutoff, st),
                "gamma": dial_gamma(cfg, day),
            },
            # Piece 3 fills this. Named rather than omitted, for the reason the
            # regime block itself was named before it was built: an absent
            # section reads as "nothing to say" and a named one reads as "owed".
            "contradictions": [],
            "contradictions_note": "contradiction table v1 -- Phase 2 piece 3",
            "prior_objects_read": len(history),
        }
        obj["absent_dimensions"] = sorted(
            n for n, d in dims.items() if d.get("state") is None)
        return obj
    finally:
        if own:
            st.close()


def store_object(obj: dict,
                 store: Optional[observations.ObservationStore] = None) -> int:
    """One row, observed_at = the session, available_at = the compute instant."""
    own = store is None
    st = store or observations.ObservationStore()
    try:
        return st.write(STORE_KEY, None, obj["session"],
                        obj.get("computed_at") or session.utc_iso(),
                        json.dumps(obj, sort_keys=True), source="derived_state")
    finally:
        if own:
            st.close()


def latest(as_of: Optional[str] = None,
           store: Optional[observations.ObservationStore] = None,
           session_day: Optional[str] = None) -> Optional[dict]:
    """THE READER EVERY REPORT USES. Reads; never computes.

    The 07:00 anchor calls this and does not recompute: an anchor that computed
    its own object could disagree with the close report's, and then the system
    holds two regimes and no way to say which one a decision was made under.
    """
    own = store is None
    st = store or observations.ObservationStore()
    try:
        rows = st.as_of(STORE_KEY, as_of=as_of)
        if session_day:
            rows = [r for r in rows if str(r["observed_at"])[:10] == session_day]
        if not rows:
            return None
        return json.loads(rows[-1]["value_text"])
    finally:
        if own:
            st.close()


def replay_fields(obj: dict) -> dict:
    """The object minus provenance, for an exact-replay comparison."""
    def strip(o):
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items() if k not in REPLAY_EXCLUDE}
        if isinstance(o, list):
            return [strip(v) for v in o]
        return o
    return strip(obj)


# ---------------------------------------------------------------------------
# Backfill
# ---------------------------------------------------------------------------
def session_days(first: str, last: str) -> list[str]:
    """Trading sessions from first to last inclusive, calendar where it covers."""
    a, b = dt.date.fromisoformat(first), dt.date.fromisoformat(last)
    out, day = [], a
    while day <= b:
        covered = session.calendar_covers(day)
        if (session.is_trading_session(day) if covered else day.weekday() < 5):
            out.append(day.isoformat())
        day += dt.timedelta(days=1)
    return out


def session_cutoff(day: str) -> str:
    """The evening of a session, as the as-of a backfilled object may know.

    21:00 UTC is after the 16:00 ET close year-round (17:00 UTC in summer,
    21:00 in winter is 16:00 ET) -- so an object backfilled for a day sees that
    day's close and nothing after it.
    """
    return f"{day}T21:30:00.000000+00:00"


def supportable_range(store: Optional[observations.ObservationStore] = None,
                      cfg: Optional[dict] = None) -> dict:
    """The session range the store can support AS-OF CORRECTLY, and why.

    THIS IS NOT THE RANGE THE STORE HAS DATA FOR, and the difference is the whole
    point. Every one of the 20,372 migrated FRED observations carries the SAME
    available_at -- 2026-05-30, the instant the CSV store was migrated into
    SQLite. The CSVs only ever had `date` and `as_of`, so the migration had no
    true first-publication date to give them; observations.py's own docstring
    names this as the reason the three clocks exist.

    So an object backfilled for a 2023 session would correctly find that NOTHING
    was knowable then, and produce eight absent dimensions. Thousands of rows
    saying "the store did not exist yet" are not history, they are noise that
    makes the real history harder to find.

    The supportable range therefore starts at the first session after the
    earliest available_at among the declared PRIMARY members, and ends at the last
    trading session. Backfilling outside it is possible with explicit --from /
    --to and it is not the default.
    """
    cfg = cfg or load_config()
    own = store is None
    st = store or observations.ObservationStore()
    try:
        primaries = []
        for name, spec in (cfg.get("dimensions") or {}).items():
            members = (spec or {}).get("members") or []
            if members:
                primaries.append((name, str(members[0].get("metric"))))
        earliest: Optional[str] = None
        detail = {}
        for name, metric in primaries:
            rows = st.as_of(metric)
            first_avail = min((str(r["available_at"]) for r in rows), default=None)
            detail[name] = {"primary": metric,
                            "earliest_available_at": first_avail,
                            "observations": len(rows)}
            if first_avail and (earliest is None or first_avail < earliest):
                earliest = first_avail
        last = session.last_trading_session().isoformat()
        if earliest is None:
            return {"first": None, "last": last, "per_dimension": detail,
                    "reason": "no primary member has any observation at all"}
        day = dt.date.fromisoformat(earliest[:10]) + dt.timedelta(days=1)
        for _ in range(14):
            if session_days(day.isoformat(), day.isoformat()):
                break
            day += dt.timedelta(days=1)
        return {"first": day.isoformat(), "last": last, "per_dimension": detail,
                "earliest_available_at": earliest,
                "reason": (
                    f"every migrated FRED observation shares available_at "
                    f"{earliest[:10]} -- the CSV-to-SQLite migration instant, not "
                    f"a real first-publication date -- so nothing was knowable "
                    f"before it and an object for an earlier session would be "
                    f"eight absent dimensions")}
    finally:
        if own:
            st.close()


def backfill(first: str, last: str, store: Optional[
        observations.ObservationStore] = None, verbose: bool = True) -> dict:
    """Compute and store one object per session, each as-of its own evening.

    WHY IT IS WORTH THE RUN. "What changed" needs a previous object to compare
    against, and persistence needs a run of them -- a state machine with no
    history publishes its first reading as gospel. The audit also wants dial
    calls graded later (6f), and a dial call can only be graded if it was
    recorded at the time it was made. This is that record, as-of correct.
    """
    own = store is None
    st = store or observations.ObservationStore()
    cfg = load_config()
    written, computed = 0, 0
    try:
        days = session_days(first, last)
        for day in days:
            obj = compute(as_of=session_cutoff(day), session_day=day,
                          store=st, cfg=cfg)
            computed += 1
            written += store_object(obj, st)
            if verbose and computed % 100 == 0:
                print(f"   {computed}/{len(days)} sessions ({day})")
        return {"sessions": len(days), "computed": computed, "written": written,
                "first": days[0] if days else None,
                "last": days[-1] if days else None}
    finally:
        if own:
            st.close()


# ---------------------------------------------------------------------------
# Rendering -- the WHAT CHANGED block lives in daily_cascade; this is the
# human-readable dump the CLI prints.
# ---------------------------------------------------------------------------
def format_object(obj: dict) -> str:
    L = []
    L.append(f"MARKET STATE  session {obj['session']}   as-of {obj['as_of']}")
    L.append(f"  schema {obj['schema_version']}  config {obj['config_version']}"
             f"  sha {obj.get('git_sha')}")
    L.append("")
    L.append("  DIALS")
    for name, d in (obj.get("dials") or {}).items():
        state = d.get("state") or f"ABSENT -- {d.get('absent_reason')}"
        L.append(f"    {name:8} {state}")
    L.append("")
    L.append("  DIMENSIONS")
    for name, d in (obj.get("dimensions") or {}).items():
        if d.get("state") is None:
            L.append(f"    {name:11} ABSENT -- {d.get('absent_reason')}")
            continue
        pend = (f"  (pending {d['pending_state']}, "
                f"{d.get('pending_sessions')}/{d['persistence_sessions']})"
                if d.get("pending_state") else "")
        L.append(f"    {name:11} {d['state']:14} dir {d['direction']}  "
                 f"pct {d['percentile']}  conf {d['confidence']}{pend}")
        L.append(f"                supporting: {d['supporting'] or '[]'}")
        L.append(f"                contradicting: {d['contradicting']}")
    rows = obj.get("contradictions") or []
    L.append("")
    L.append(f"  CONTRADICTIONS ({len(rows)})"
             + (f" -- {obj.get('contradictions_note')}" if not rows else ""))
    for r in rows:
        if r.get("state") == "absent":
            L.append(f"    {r['id']:26} ABSENT -- {r.get('absent_reason')}")
        else:
            L.append(f"    {r['id']:26} {r.get('open_state')}  "
                     f"z {r.get('magnitude')}  since {r.get('since')}  "
                     f"{r.get('persistence_days')}d")
    return "\n".join(L)


def _main(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="The market-state object.")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compute", help="compute and store one session's object")
    c.add_argument("--as-of", default=None,
                   help="the cutoff the object may know (default: now)")
    c.add_argument("--session", default=None,
                   help="the session it is about (default: last trading session)")
    c.add_argument("--no-store", action="store_true")
    c.add_argument("--json", action="store_true")

    s = sub.add_parser("show", help="print the stored object for a session")
    s.add_argument("--as-of", default=None)
    s.add_argument("--session", default=None)
    s.add_argument("--json", action="store_true")

    b = sub.add_parser("backfill", help="one object per session over a range")
    b.add_argument("--from", dest="first", default=None,
                   help="default: the first session the store can support "
                        "as-of correctly")
    b.add_argument("--to", dest="last", default=None,
                   help="default: the last trading session")

    sub.add_parser("range", help="what the store can support as-of correctly")

    a = p.parse_args(argv)

    if a.cmd == "compute":
        # A COMPUTE FOR A PAST SESSION DEFAULTS ITS CUTOFF TO THAT SESSION'S
        # EVENING. Passing --session 2026-05-01 and letting as_of default to now
        # would produce an object that knew four months of the future, which is
        # the one thing this whole design is against.
        as_of = a.as_of
        if as_of is None and a.session:
            as_of = session_cutoff(a.session)
        obj = compute(as_of=as_of, session_day=a.session)
        if not a.no_store:
            n = store_object(obj)
            print(f"stored {n} row(s) for session {obj['session']}")
        print(json.dumps(obj, indent=2, sort_keys=True) if a.json
              else format_object(obj))
        return 0

    if a.cmd == "show":
        as_of = a.as_of or (session_cutoff(a.session) if a.session else None)
        obj = latest(as_of=as_of, session_day=a.session)
        if obj is None:
            print("no stored market_state object for that cutoff")
            return 1
        print(json.dumps(obj, indent=2, sort_keys=True) if a.json
              else format_object(obj))
        return 0

    if a.cmd == "range":
        r = supportable_range()
        print(f"as-of supportable: {r['first']} .. {r['last']}")
        print(f"  {r['reason']}")
        for name, d in (r.get("per_dimension") or {}).items():
            print(f"    {name:11} {d['primary']:24} "
                  f"{d['observations']:6} obs  earliest available_at "
                  f"{str(d['earliest_available_at'])[:19]}")
        return 0

    if a.cmd == "backfill":
        rng = supportable_range()
        first = a.first or rng["first"]
        last = a.last or rng["last"]
        if first is None:
            print("nothing to backfill: " + rng["reason"])
            return 1
        if a.first is None:
            print(f"range {first} .. {last} (as-of supportable)")
            print(f"  {rng['reason']}")
        r = backfill(first, last)
        print(f"backfill: {r['computed']} sessions computed, {r['written']} "
              f"rows written, {r['first']} .. {r['last']}")
        return 0
    return 2


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
