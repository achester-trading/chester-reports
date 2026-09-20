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

import contradictions as contradictions_mod
from altdata import derived, observations, session

REPO = Path(__file__).resolve().parent
CONFIG_PATH = REPO / "config" / "market_state.yaml"

SCHEMA_VERSION = "market-state-v1"
STORE_KEY = "market_state"

# ---------------------------------------------------------------------------
# METHOD VERSION -- what the CODE does, as distinct from what the config says
# ---------------------------------------------------------------------------
#
# config_version already separates "a threshold changed on purpose" from "the
# arithmetic broke". This separates the third case, which was costing a full
# re-backfill on every commit that touched the object's content: THE CODE CHANGED ON
# PURPOSE. Six re-backfills in one day, each four minutes, because the replay gate
# could not tell a deliberate change of method from a regression.
#
# So a stored object records the method that produced it, and the replay gate compares
# only objects computed under the current one. Bumping is DELIBERATE: it is named in
# the commit message and in the status ledger, and it is the signal that the history
# needs bringing forward.
#
# THE HASH IS WHAT MAKES THE BUMP HONEST. A version constant nobody is forced to
# change is a version constant that stops being true -- someone edits the band logic,
# does not bump, and every stored object silently claims a method it was not computed
# under. So the modules that decide the object's content are hashed, the hash is
# pinned here, and validate_regime.py FAILS when the two disagree. The message it
# prints is the whole mechanism: bump the version, update the hash, re-backfill.
METHOD_VERSION = "market-state-method-2"

# The modules whose content decides what the object says. regime.py builds it and
# contradictions.py fills its table; altdata/derived.py is deliberately NOT here --
# it has its own gate with 36 seeded checks, and folding it in would make every
# delta-semantics fix look like a method change to the object.
METHOD_SOURCE_FILES = ("regime.py", "contradictions.py")

# Updated in the same commit as the version above. Recompute with:
#   python -m regime method --update
METHOD_SOURCE_SHA = "4471b53571a05d33"

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


def method_source_sha(files: Optional[tuple[str, ...]] = None) -> str:
    """A content hash of the modules that decide the object's content.

    THE PIN LINE IS EXCLUDED FROM THE HASH, which it has to be: hashing a file that
    contains its own hash cannot converge. Everything else counts, comments and
    docstrings included -- a comment that changes the reason for a rule is a change
    worth a reader noticing, and excluding comments would let a rewritten
    justification pass as no change at all.
    """
    import hashlib
    import re as _re
    h = hashlib.sha256()
    for name in sorted(files or METHOD_SOURCE_FILES):
        text = (REPO / name).read_text(encoding="utf-8")
        text = _re.sub(r'(?m)^METHOD_SOURCE_SHA = ".*"$',
                       'METHOD_SOURCE_SHA = "<excluded>"', text)
        h.update(name.encode())
        h.update(text.replace("\r\n", "\n").encode())
    return h.hexdigest()[:16]


def method_pinned() -> tuple[bool, str, str]:
    """(matches, declared, actual). What validate_regime.py asserts."""
    actual = method_source_sha()
    return METHOD_SOURCE_SHA == actual, METHOD_SOURCE_SHA, actual


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
    multiple = float(spec.get("staleness_multiple")
                     or defaults.get("staleness_multiple") or 3)
    persistence = int(spec.get("persistence_sessions")
                      or defaults.get("persistence_sessions") or 2)
    bands = spec.get("bands") or []
    members = spec.get("members") or []

    out: dict[str, Any] = {
        "dimension": name,
        "horizon": spec.get("horizon"),
        "states_declared": spec.get("states") or [b.get("state") for b in bands],
        "persistence_sessions": persistence,
        "staleness_multiple": multiple,
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
    # THE ALLOWANCE IS THE PRIMARY'S OWN, from its registry half_life and cadence,
    # times the declared multiple. A weekly series is not stale for being weekly.
    stale = primary["staleness_sessions"]
    own = primary["staleness_allowance_sessions"]
    limit = None if own is None else int(round(own * multiple))
    out["staleness_limit_sessions"] = limit
    if own is None:
        out["staleness_basis"] = (
            f"{primary['metric']} has no staleness allowance -- its half_life is "
            f"permanent, so it cannot go stale")
    else:
        out["staleness_basis"] = (
            f"{primary['metric']} allows {own} sessions, from its registry "
            f"half_life at its own cadence ({primary.get('staleness_basis')}), "
            f"x{multiple} = {limit}")
    if stale is not None and limit is not None and stale > limit:
        out["absent_reason"] = (
            f"the primary member {primary['metric']} was last observed "
            f"{primary['observed_at']}, {stale} sessions before this cutoff. Its "
            f"own allowance is {own} sessions -- from its registry half_life at "
            f"its own cadence, not a daily calendar -- and {multiple}x that is "
            f"{limit}. A state computed from it would be a stale state presented "
            f"as a current one")
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
def prior_objects(objects_as_of: str, before_session: str, limit: int,
                  store: observations.ObservationStore) -> list[dict]:
    """The most recent stored objects for sessions before `before_session`.

    TWO CLOCKS, AND CONFLATING THEM BROKE THE FIRST BACKFILL. Market data is read
    at the SESSION's cutoff, so the object contains only what was knowable that
    evening -- that is the leak rule and it is absolute. But the object's memory of
    ITSELF is not market data: it is the state machine's own history, and it is
    read at `objects_as_of`, the instant this object was computed.

    The first backfill got this wrong and the symptom was silent. Each day read its
    own history at that day's evening cutoff; the predecessor objects had been
    written minutes earlier in September, so none of them was "knowable" in June
    and every one of 77 sessions reported "first object; published immediately".
    Persistence -- the whole reason states do not flap -- never engaged, and the
    output looked entirely reasonable.

    The rule is therefore: only sessions strictly before this one, and only objects
    that existed when this object was computed. That is deterministic, which is
    what makes the exact-replay check in tools/validate_regime.py possible: a
    replay passes the stored object's own computed_at and sees the same
    predecessors it saw. A later RECOMPUTE of an earlier session can change what a
    replay of a later one sees, and that is a real change rather than a flaw -- it
    means the history was edited.
    """
    rows = [r for r in store.as_of(STORE_KEY, as_of=objects_as_of)
            if str(r["observed_at"])[:10] < before_session]
    # SLICE BEFORE PARSING. Each object is tens of kilobytes of JSON and the
    # backfill calls this once per session, so parsing the whole history to keep
    # the last eight made the run quadratic in its own output -- 77 sessions was
    # imperceptible and a five-year backfill was not.
    if limit:
        rows = rows[-limit:]
    out = []
    for r in rows:
        try:
            out.append(json.loads(r["value_text"]))
        except Exception:
            continue
    return out


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


# The session classes on which a pre-expiry gamma reading describes a book that is
# about to stop existing. Named here rather than inline because the dial's confidence
# turns on it and a reader should be able to find the list.
PROVISIONAL_ON = ("OPEX", "TRIPLE_WITCHING")


def dial_gamma(cfg: dict, session_date: str,
               events: Optional[list[str]] = None) -> dict:
    """READ from the exposure engine, never recomputed.

    ON AN EXPIRY SESSION THE READING IS PROVISIONAL, and this is the one place the
    object's confidence is set by the CALENDAR rather than by staleness or sample
    size. A dealer gamma profile measured from a chain on expiry day is computed over
    open interest much of which settles that morning: the number is a correct
    description of a book that is about to stop existing. It says little about the
    gamma dealers will be carrying on Monday, which is what a 1-3m dial is for.

    So the state is still published -- it is a true reading and suppressing it would
    lose information -- but confidence is LOW and `provisional` is set until the next
    settled capture. Friday 18 September 2026 was triple witching, and every gamma
    reading in the Phase 2 work was taken on it with nothing saying so.
    """
    spec = (cfg.get("dials") or {}).get("gamma") or {}
    sym = str(spec.get("symbol") or "SPY")
    evs = list(events or [])
    provisional = [e for e in evs if e in PROVISIONAL_ON]
    out: dict[str, Any] = {"dial": "gamma", "symbol": sym,
                           "source": spec.get("source"), "state": None,
                           "session_events": evs,
                           "confidence": "med",
                           "provisional": bool(provisional),
                           "note": spec.get("note")}
    if provisional:
        out["confidence"] = "low"
        out["provisional_reason"] = (
            f"this session is {', '.join(provisional)}: the profile is computed over "
            f"open interest much of which settles at this expiry, so it describes a "
            f"book that is about to stop existing. PROVISIONAL until the next "
            f"settled capture.")
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
            cfg: Optional[dict] = None,
            computed_at: Optional[str] = None) -> dict:
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
        # Fixed BEFORE the history is read, because it is the clock the history is
        # read at. A replay passes the stored object's own value here.
        stamp = computed_at or session.utc_iso()
        defaults = cfg.get("defaults") or {}

        dims: dict[str, dict] = {}
        for name, spec in (cfg.get("dimensions") or {}).items():
            d = compute_dimension(name, spec or {}, cutoff, defaults, st)
            d["as_of_session"] = day
            dims[name] = d

        # THE SESSION'S OWN EVENT CLASSES, from the table beside the holiday list.
        # A property of the DATE that no market data carries and that changes what
        # the data means: an index-rebalance close and an ordinary Tuesday's differ
        # by an order of magnitude in size, and an expiry close describes a book
        # that is about to settle.
        events = session.auction_event_classes(day)

        history = prior_objects(stamp, day, limit=8, store=st)
        for name, d in dims.items():
            apply_persistence(d, name, history)

        obj = {
            "object": "market_state",
            "schema_version": SCHEMA_VERSION,
            "method_version": METHOD_VERSION,
            "config_version": cfg.get("version"),
            "session": day,
            "as_of": cutoff,
            "computed_at": stamp,
            "git_sha": git_sha(),
            "config_path": str(CONFIG_PATH.relative_to(REPO)).replace("\\", "/"),
            "derived_convention": derived.CONVENTION_VERSION,
            "session_events": events,
            "dimensions": dims,
            "dials": {
                "macro": dial_macro(cfg, dims),
                "vol": dial_vol(cfg, cutoff, st),
                "gamma": dial_gamma(cfg, day, events=events),
            },
            "prior_objects_read": len(history),
            # WHICH PREDECESSOR THIS OBJECT'S PERSISTENCE RESTED ON, named rather
            # than implied. Every published state is a function of the previous
            # object's state -- that is what persistence means -- so an object that
            # does not say which one it read cannot be audited: a chain with a gap,
            # a duplicate or a predecessor computed under different rules all
            # produce plausible states and no trace of why.
            #
            # (session, computed_at) is the identity: observed_at is the session and
            # available_at is the compute instant, and the store's vintage key makes
            # the pair unique. config_version travels too, because persistence
            # across a rules change is a different claim from persistence within
            # one.
            "previous_object": (
                {"session": history[-1].get("session"),
                 "computed_at": history[-1].get("computed_at"),
                 "config_version": history[-1].get("config_version"),
                 "schema_version": history[-1].get("schema_version")}
                if history else None),
        }
        # The table reads the object's OWN dimensions and dials rather than the
        # store a second time, so a contradiction can never disagree with the
        # state it is drawn from.
        obj["contradictions"] = contradictions_mod.evaluate(
            cfg, dims, obj["dials"], cutoff, day, history, st)
        obj["exceptions"] = exceptions_of(obj)
        obj["absent_dimensions"] = sorted(
            n for n, d in dims.items() if d.get("state") is None)
        obj["open_contradictions"] = sorted(
            r["id"] for r in obj["contradictions"] if r.get("open"))
        obj["absent_contradictions"] = sorted(
            r["id"] for r in obj["contradictions"]
            if r.get("open_state") == "absent")
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

    The 07:00 anchor calls this and does not recompute: an anchor that computed its
    own object could disagree with the close report's, and then the system holds
    two regimes and no way to say which one a decision was made under.

    WHEN `session_day` IS GIVEN, `as_of` IS NOT APPLIED, and the reason is the same
    two-clock distinction the persistence history turns on. An object ABOUT session
    S already contains only what was knowable on S -- that is enforced when it is
    computed. Its available_at records when the system got round to computing it,
    which for a backfilled or re-rendered session is later. Filtering on it would
    mean a report re-rendered for a past session could not read the object about
    that session, which is exactly the case Phase 2 piece 7 asks for.

    Without `session_day`, `as_of` applies normally: "the newest object the system
    could have had at this instant" is the right question for a live pass.
    """
    own = store is None
    st = store or observations.ObservationStore()
    try:
        if session_day:
            rows = [r for r in st.as_of(STORE_KEY)
                    if str(r["observed_at"])[:10] == session_day]
        else:
            rows = st.as_of(STORE_KEY, as_of=as_of)
        if not rows:
            return None
        return json.loads(rows[-1]["value_text"])
    finally:
        if own:
            st.close()


def replay_fields(obj: dict) -> dict:
    """The object minus provenance, normalised, for an exact-replay comparison.

    THE JSON ROUND TRIP IS PART OF THE COMPARISON, not a formality. One side of a
    replay comes out of the store, so it has been through json.dumps and back; the
    other is fresh in memory. Any type JSON does not preserve differs between them
    for no reason at all -- a tuple becomes a list, and the gate reports a failure
    that means nothing. That happened on the first real run, on
    `gamma_vs_trend.states`: stored ['negative', 'flat'] against replayed
    ('negative', 'flat').

    Normalising both sides through JSON makes the comparison what it should be: the
    stored form IS JSON, so equality in JSON terms is the only equality that
    matters. A real difference -- a changed number, a changed state -- survives the
    round trip untouched.
    """
    def strip(o):
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items() if k not in REPLAY_EXCLUDE}
        if isinstance(o, (list, tuple)):
            return [strip(v) for v in o]
        return o
    return json.loads(json.dumps(strip(obj), sort_keys=True, default=str))


# ---------------------------------------------------------------------------
# exceptions[] -- §K's own field, and the only part of the object that pushes
# ---------------------------------------------------------------------------
def exceptions_of(obj: dict) -> list[dict]:
    """The object's threshold crossings, as §K's {what, threshold, value, since}.

    TWO KINDS, and they are different claims:

      A CONTRADICTION THAT HAS BEEN OPEN LONG ENOUGH. The table already decides
      this -- `exception: true` at the declared exception_sessions -- and the row
      carries its own since and magnitude. A divergence that lasted a week is a
      statement about the market; one that lasted a day is noise, which is why the
      persistence rule comes first and this reads its output rather than the raw z.

      A MEMBER AT A FIVE-YEAR EXTREME. `extreme` is a percentile crossing, and it
      is worth surfacing even when its dimension's band did not move: a single
      series at its 2nd percentile of five years is a fact about that series, and
      the band it sits in is a fact about three others.

    ORDERED, and stable: contradictions before extremes, each alphabetically. The
    heartbeat compares this set against the previous run's, so an unstable order
    would read as a change every time.
    """
    out: list[dict] = []
    for r in obj.get("contradictions") or []:
        if not r.get("exception"):
            continue
        out.append({
            "id": f"contradiction:{r.get('id')}",
            "kind": "contradiction",
            "what": f"{r.get('id')} open {r.get('persistence_days')} sessions",
            "threshold": r.get("threshold_z"),
            "value": r.get("magnitude"),
            "since": r.get("since"),
            "legs": r.get("legs"),
            "alert_path": r.get("alert_path")})
    for name, d in (obj.get("dimensions") or {}).items():
        multiple = float(d.get("staleness_multiple") or 3)
        for m in d.get("members") or []:
            if not m.get("extreme"):
                continue
            # A STALE EXTREME IS NOT AN EXCEPTION. The first run of this reported
            # three of them -- bb_oas, ig_oas and yield_30y at five-year extremes --
            # computed from prints four months old, inside dimensions that had
            # REFUSED to state a state for exactly that reason. Surfacing them
            # anyway would be the "stale state presented as a current one" the
            # dimension rule exists to prevent, arriving through a side door that
            # also emails.
            own = m.get("staleness_allowance_sessions")
            stale = m.get("staleness_sessions")
            if own is not None and stale is not None and stale > own * multiple:
                continue
            out.append({
                "id": f"extreme:{m.get('metric')}",
                "kind": "extreme",
                "what": f"{m.get('metric')} at a five-year extreme ({name})",
                "threshold": d.get("extreme_rule") or "percentile <= 5 or >= 95",
                "value": m.get("percentile_raw"),
                "since": None,
                "level": m.get("level")})
    out.sort(key=lambda e: (0 if e["kind"] == "contradiction" else 1, e["id"]))
    return out


def exception_ids(obj: Optional[dict]) -> list[str]:
    return [e["id"] for e in exceptions_of(obj or {})]


# ---------------------------------------------------------------------------
# WHAT CHANGED -- the diff two objects make, and the anchors' first data block
# ---------------------------------------------------------------------------
def previous_object(obj: dict,
                    store: Optional[observations.ObservationStore] = None
                    ) -> Optional[dict]:
    """The object for the session before this one, as-of correct at its cutoff."""
    own = store is None
    st = store or observations.ObservationStore()
    try:
        prior = prior_objects(obj.get("computed_at") or session.utc_iso(),
                              obj.get("session") or "9999-99-99", limit=1,
                              store=st)
        return prior[-1] if prior else None
    finally:
        if own:
            st.close()


def what_changed(current: dict, previous: Optional[dict]) -> dict:
    """The diff. DATA ONLY -- no model, no prose, no judgement of importance.

    O.6: deltas and percentiles first, levels behind them. The reason is that a
    close report read fast is read from the top, and a level is the least
    informative thing on the page -- it says where a series is, not that it moved,
    not whether the move is unusual, and not whether anything else disagrees.

    EVERY MAGNITUDE CARRIES ITS PERCENTILE. A state change with no percentile is a
    label; with one it is a measurement a reader can argue with.
    """
    out: dict[str, Any] = {
        "session": current.get("session"),
        "compared_with": (previous or {}).get("session"),
        "dimension_changes": [], "dial_changes": [],
        "extremes_set": [], "extremes_cleared": [],
        "absences_opened": [], "absences_cleared": [],
        "contradictions_opened": [], "contradictions_closed": [],
        "contradictions_persisting": [], "pending_states": [],
    }
    cur_dims = current.get("dimensions") or {}
    prev_dims = (previous or {}).get("dimensions") or {}
    if previous is None:
        out["note"] = ("no previous object -- this is the first for this "
                       "cutoff, so nothing is reported as changed rather than "
                       "everything being reported as new")

    for name, d in cur_dims.items():
        p = prev_dims.get(name) or {}
        now_state, was_state = d.get("state"), p.get("state")
        if previous is not None and now_state != was_state:
            if now_state is None:
                out["absences_opened"].append({
                    "dimension": name, "was": was_state,
                    "reason": d.get("absent_reason")})
            elif was_state is None and p:
                out["absences_cleared"].append({
                    "dimension": name, "now": now_state,
                    "percentile": d.get("percentile")})
            else:
                out["dimension_changes"].append({
                    "dimension": name, "from": was_state, "to": now_state,
                    "percentile": d.get("percentile"),
                    "direction": d.get("direction"),
                    "confidence": d.get("confidence"),
                    "since": d.get("last_changed"),
                    "rule": d.get("persistence")})
        if d.get("pending_state"):
            out["pending_states"].append({
                "dimension": name, "published": now_state,
                "pending": d.get("pending_state"),
                "sessions": d.get("pending_sessions"),
                "required": d.get("persistence_sessions"),
                "percentile": d.get("percentile")})

        # EXTREME FLAGS, member by member. The flag lives on the member rather
        # than the dimension, so this is where a single series going to a 5-year
        # extreme becomes visible even when its dimension's band did not move.
        was_ex = {m.get("metric"): m.get("extreme")
                  for m in (p.get("members") or [])}
        for m in d.get("members") or []:
            mid, now_ex = m.get("metric"), m.get("extreme")
            if now_ex and not was_ex.get(mid):
                out["extremes_set"].append({
                    "dimension": name, "metric": mid,
                    "percentile": m.get("percentile_raw"),
                    "percentile_on_dimension_scale": m.get("percentile"),
                    "level": m.get("level"), "z_score": m.get("z_score")})
            elif was_ex.get(mid) and not now_ex and now_ex is not None:
                out["extremes_cleared"].append({
                    "dimension": name, "metric": mid,
                    "percentile": m.get("percentile_raw")})

    cur_dials = current.get("dials") or {}
    prev_dials = (previous or {}).get("dials") or {}
    for name, d in cur_dials.items():
        was = (prev_dials.get(name) or {}).get("state")
        now = d.get("state")
        if previous is not None and now != was:
            out["dial_changes"].append({
                "dial": name, "from": was, "to": now,
                "percentile": d.get("percentile"),
                "level": d.get("level"),
                "reason": d.get("absent_reason")})

    prev_rows = {r.get("id"): r for r in (previous or {}).get("contradictions")
                 or []}
    for r in current.get("contradictions") or []:
        pid = r.get("id")
        was_open = bool((prev_rows.get(pid) or {}).get("open"))
        entry = {"id": pid, "magnitude": r.get("magnitude"),
                 "threshold_z": r.get("threshold_z"),
                 "since": r.get("since"),
                 "persistence_days": r.get("persistence_days"),
                 "legs": r.get("legs"),
                 "exception": r.get("exception"),
                 "alert_path": r.get("alert_path")}
        if r.get("open") and not was_open:
            out["contradictions_opened"].append(entry)
        elif was_open and not r.get("open"):
            out["contradictions_closed"].append(
                {**entry, "closed_note": r.get("closed_note")})
        elif r.get("open"):
            out["contradictions_persisting"].append(entry)

    out["nothing_changed"] = not any(
        out[k] for k in ("dimension_changes", "dial_changes", "extremes_set",
                         "extremes_cleared", "absences_opened",
                         "absences_cleared", "contradictions_opened",
                         "contradictions_closed", "contradictions_persisting"))
    return out


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
        earliest_metric: Optional[str] = None
        earliest_kind: Optional[str] = None
        detail = {}
        for name, metric in primaries:
            rows = st.as_of(metric)
            first_avail = min((str(r["available_at"]) for r in rows), default=None)
            kinds = sorted({(r["availability_kind"]
                             if "availability_kind" in r.keys() else None)
                            or "unstated" for r in rows})
            detail[name] = {"primary": metric,
                            "earliest_available_at": first_avail,
                            "availability_kinds": kinds,
                            "observations": len(rows)}
            if first_avail and (earliest is None or first_avail < earliest):
                earliest = first_avail
                earliest_metric = metric
                earliest_kind = ", ".join(kinds)
        last = session.last_trading_session().isoformat()
        if earliest is None:
            return {"first": None, "last": last, "per_dimension": detail,
                    "reason": "no primary member has any observation at all"}
        day = dt.date.fromisoformat(earliest[:10]) + dt.timedelta(days=1)
        for _ in range(14):
            if session_days(day.isoformat(), day.isoformat()):
                break
            day += dt.timedelta(days=1)
        # WHICH PRIMARY SET THE BOUND, AND HOW ITS AVAILABILITY WAS ARRIVED AT.
        # This message used to tell one story -- the FRED migration instant -- and
        # it went wrong the moment prices arrived with a RECONSTRUCTED availability
        # reaching back five years: the bound moved to 2021 and the text still
        # blamed a 2026 migration. A range that explains itself has to read the
        # store rather than recite a known cause.
        # WHICH PRIMARIES ARE REVISABLE, asked of the registry rather than of the
        # spelling of their ids. A prefix test would also have put a metric id in
        # this file, which validate_regime.py forbids for a good reason: a series
        # named in code is a series that stops being a config decision.
        revisable = [d for d in detail.values()
                     if derived.registry_entry(d["primary"]).get(
                         "revision_policy") == "revised"
                     and d["earliest_available_at"]]
        fred_bound = min((str(d["earliest_available_at"])[:10]
                          for d in revisable), default=None)
        return {"first": day.isoformat(), "last": last, "per_dimension": detail,
                "earliest_available_at": earliest,
                "earliest_primary": earliest_metric,
                "earliest_availability_kind": earliest_kind,
                "fred_bound": fred_bound,
                "reason": (
                    f"the earliest availability across the dimensions' primary "
                    f"members is {earliest[:10]}, from {earliest_metric} "
                    f"(availability: {earliest_kind}). Objects before that date "
                    f"would find nothing knowable at all."
                    + (f" NOTE: the {len(revisable)} revisable primaries only "
                       f"become knowable at {fred_bound} -- their migrated history "
                       f"shares one available_at, the CSV-to-SQLite migration "
                       f"instant, rather than a real first-publication date -- so "
                       f"every session before {fred_bound} has those dimensions "
                       f"absent and only the reconstructable ones present. ALFRED "
                       f"ingestion (O.16) is what widens it."
                       if fred_bound and fred_bound > day.isoformat() else ""))}
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
        # IN SESSION ORDER, ASSERTED AND NOT ASSUMED. Each object's persistence
        # reads the objects already written, so a run that went backwards would
        # give every session an empty history and publish every raw reading as a
        # first object -- which is the exact failure the two-clock bug produced,
        # and it looked entirely reasonable in the output. session_days() builds an
        # ascending list; this is here so that a future change to it cannot quietly
        # break persistence instead of failing.
        if days != sorted(days):
            raise ValueError(
                f"backfill received sessions out of order ({days[:3]}...); "
                f"persistence depends on ascending order and would silently "
                f"publish every reading as a first object")
        for day in days:
            obj = compute(as_of=session_cutoff(day), session_day=day,
                          store=st, cfg=cfg)
            computed += 1
            written += store_object(obj, st)
            if verbose and computed % 100 == 0:
                print(f"   {computed}/{len(days)} sessions ({day})")
        return {"sessions": len(days), "computed": computed, "written": written,
                "ordered": days == sorted(days),
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
    evs = obj.get("session_events") or []
    L.append(f"MARKET STATE  session {obj['session']}   as-of {obj['as_of']}")
    L.append(f"  session events: {', '.join(evs) if evs else '(none)'}")
    L.append(f"  schema {obj['schema_version']}  config {obj['config_version']}"
             f"  sha {obj.get('git_sha')}")
    L.append("")
    L.append("  DIALS")
    for name, d in (obj.get("dials") or {}).items():
        state = d.get("state") or f"ABSENT -- {d.get('absent_reason')}"
        flag = ""
        if d.get("provisional"):
            flag = f"  PROVISIONAL (conf {d.get('confidence')})"
        L.append(f"    {name:8} {state}{flag}")
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
    exc = obj.get("exceptions") or []
    if exc:
        L.append("")
        L.append(f"  EXCEPTIONS ({len(exc)})")
        for e in exc:
            L.append(f"    {e['what']}  value={e.get('value')}  "
                     f"threshold={e.get('threshold')}"
                     + (f"  since {e['since']}" if e.get("since") else ""))
    rows = obj.get("contradictions") or []
    L.append("")
    L.append(f"  CONTRADICTIONS ({len(rows)} declared, "
             f"{len(obj.get('absent_contradictions') or [])} absent, "
             f"{len(obj.get('open_contradictions') or [])} open)")
    for r in rows:
        if r.get("open_state") == "absent":
            L.append(f"    {r['id']:28} ABSENT -- {r.get('absent_reason')}")
            continue
        mag = ("state mismatch" if r.get("magnitude") is None
               else f"z {r.get('magnitude'):+.2f}")
        exc = "  EXCEPTION" if r.get("exception") else ""
        L.append(f"    {r['id']:28} {str(r.get('open_state')):8} {mag:>16}  "
                 f"since {r.get('since') or '-'}  "
                 f"{r.get('persistence_days')}d{exc}")
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

    m = sub.add_parser("method", help="the method version and its source hash")
    m.add_argument("--update", action="store_true",
                   help="rewrite METHOD_SOURCE_SHA to match the current source")

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

    ex = sub.add_parser("exceptions",
                        help="the latest object's exceptions, one id per line")
    ex.add_argument("--session", default=None)
    ex.add_argument("--json", action="store_true")

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

    if a.cmd == "method":
        matches, declared, actual = method_pinned()
        print(f"method_version   {METHOD_VERSION}")
        print(f"source files     {list(METHOD_SOURCE_FILES)}")
        print(f"declared hash    {declared}")
        print(f"actual hash      {actual}")
        print(f"match            {matches}")
        if a.update:
            path = REPO / "regime.py"
            text = path.read_text(encoding="utf-8")
            import re as _re
            new = _re.sub(r'(?m)^METHOD_SOURCE_SHA = ".*"$',
                          f'METHOD_SOURCE_SHA = "{actual}"', text, count=1)
            path.write_text(new, encoding="utf-8", newline="")
            print(f"\nupdated METHOD_SOURCE_SHA to {actual}. BUMP "
                  f"METHOD_VERSION in the same commit if the change alters what "
                  f"the object says, and re-backfill.")
        elif not matches:
            print("\nThe source has changed since the hash was pinned. If that "
                  "change alters what the object SAYS: bump METHOD_VERSION, run "
                  "`regime method --update`, re-backfill. If it does not (a "
                  "comment, a rename): run `regime method --update` alone.")
        return 0 if matches or a.update else 1

    if a.cmd == "exceptions":
        # ONE ID PER LINE, and nothing else on stdout: the heartbeat diffs this
        # against the previous run's list with comm(1), so a header or a count
        # would read as an exception that opened.
        obj = latest(session_day=a.session)
        if obj is None:
            return 1
        if a.json:
            print(json.dumps(exceptions_of(obj), indent=2, sort_keys=True))
        else:
            for e in exceptions_of(obj):
                print(e["id"])
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
