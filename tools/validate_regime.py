"""
Validation gate for the market-state object and the contradiction table.

The object is the only regime in the system, so the things that could go wrong
with it are not cosmetic: a leak makes every backfilled state a hindsight state, a
non-deterministic compute makes a stored object unreplayable, an undeclared rule
puts a threshold back in code, and an empty `contradicting` turns "we looked and
everything agreed" into "nobody looked".

  A  EXACT REPLAY, SCOPED BY BOTH VERSIONS. A stored object, recomputed at its own
     cutoff and its own compute instant, must equal the stored version field for
     field -- but only objects computed under the current config_version AND
     method_version are compared, because a deliberate change to the rules or to the
     code is not a regression. The source hash is checked FIRST: it is what stops a
     method_version from quietly ceasing to be true. Provenance (computed_at,
     available_at, git_sha) is excluded because it necessarily differs, and
     excluding it is what makes the check meaningful rather than impossible.
  B  NO FUTURE LEAK. An observation knowable only after the cutoff must not change
     the object, and the same observation MUST change it once the cutoff passes --
     without the second half the first would pass on a store that lost the write.
  C  EVERY DIMENSION HAS A DECLARED RULE, in config and not in code: bands that
     cover the percentile range, members with a polarity and a reason, a horizon,
     a persistence count. Every dial declared. Every contradiction pair declared
     with its legs.
  D  `contradicting` IS NEVER EMPTY BY OMISSION -- checked on every stored object
     and on a seeded one, because §K makes "none found" a positive claim.
  E  PERSISTENCE. A flipped reading does not publish until it has held the declared
     number of sessions, and then it does. Seeded, because the production store
     cannot be made to flip.
  F  STALENESS. A dimension whose primary goes stale becomes ABSENT with the
     staleness in the reason, rather than carrying its last state forward.
  F2 AND IT IS PER CADENCE. A weekly series is not stale for printing weekly: the
     limit is each metric's OWN registry allowance times a declared multiple, so a
     weekly dimension and a daily one go absent at different ages.
  G  THE CONTRADICTION ARITHMETIC, on a seeded divergence whose z was computed by
     hand: it does not open on day one, opens on day two, and is an exception at
     five -- report-only, since this repo has no exceptions alert path.
  H  PERSISTENCE CHAINS. A backfill of N sessions produces exactly ONE first object
     per dimension, in ascending order, and every later object NAMES the
     predecessor its persistence rested on. This is the case that would have caught
     the two-clock bug, where all 77 sessions published a first object and the
     output looked entirely reasonable.
  J  AN ABSENCE CITES DATA (6c-3). No reason string in any object may name an
     exception class: a reader that raised records `fault`, and a fault printed as
     an absent_reason is a code problem the reader cannot tell from a gap in the
     market's record. Checked three ways -- statically over the method modules,
     over every stored object under the current method, and on a seeded ledger
     where the tail-weight read finds nothing, finds a set, and raises.
  K  THE RATES-DRIVER MEMBERS (ST-3). Known answers for the two cuts at every
     window, the move floor, the DKW / Kim-Wright shares, availability taken from
     the latest input, an absent model writing nothing, the stock-bond
     correlation, and inflation volatility refusing a window across a gap.
  L  THE RATES DRIVER (ST-3). The declaration (four cells, thresholds, every
     metric registered, none a rates member), the pure rule on each cell in both
     directions, not-determined below the floor, the models' sign disagreement
     arbitrated or not, the tie-breakers, persistence on the object, stale DKW
     falling back, the object identical with and without the driver, and the
     one-regime rule statically -- no other module names a cell and no
     calibration script opens the store.

    python tools/validate_regime.py
"""

from __future__ import annotations

import datetime as dt
import json
import statistics
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import contradictions as contra          # noqa: E402
import regime                            # noqa: E402
from altdata import derived, observations   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    ok(m) if c else bad(m)


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------
def weekdays_back(end: dt.date, n: int) -> list[dt.date]:
    out, day = [], end
    while len(out) < n:
        if day.weekday() < 5:
            out.append(day)
        day -= dt.timedelta(days=1)
    return list(reversed(out))


def seed(store, key: str, days: list[dt.date], values: list[float]) -> None:
    store.write_many([
        {"registry_key": key, "instrument": None, "observed_at": d.isoformat(),
         "available_at": dt.datetime(d.year, d.month, d.day, 21, 0,
                                     tzinfo=dt.timezone.utc).isoformat(),
         "value": float(v), "source": "synthetic"}
        for d, v in zip(days, values)])


END = dt.date(2026, 9, 18)


def tiny_config(persistence: int = 2) -> dict:
    """Two dimensions on REGISTERED daily metrics, so the real registry is used.

    fred.vix and fred.hy_oas carry a daily cadence and an `until_next_release`
    half-life, which is what gives group F a two-session staleness allowance to
    cross. A synthetic metric id would fall back to the monthly allowance and the
    staleness case would need 33 sessions of seeding to prove anything.
    """
    return {
        "version": "test-config",
        "defaults": {"persistence_sessions": persistence,
                     "staleness_multiple": 2, "window_days": 1826},
        "dimensions": {
            "volatility": {
                "horizon": "1-3m",
                "states": ["elevated", "normal", "subdued"],
                "bands": [{"state": "elevated", "min_percentile": 66},
                          {"state": "normal", "min_percentile": 33},
                          {"state": "subdued", "min_percentile": 0}],
                "members": [
                    {"metric": "fred.vix", "polarity": 1, "because": "implied"},
                    {"metric": "fred.bb_oas", "polarity": -1,
                     "because": "a second member, so supporting/contradicting "
                                "has something to say"}],
            },
            "credit": {
                "horizon": "1-3m",
                "states": ["easy", "neutral", "stressed"],
                "bands": [{"state": "easy", "min_percentile": 66},
                          {"state": "neutral", "min_percentile": 33},
                          {"state": "stressed", "min_percentile": 0}],
                "members": [{"metric": "fred.hy_oas", "polarity": -1,
                             "because": "a wide spread is stress"}],
            },
        },
        "dials": {
            "macro": {"from_dimensions": ["credit"],
                      "rules": [{"when": {"credit": "easy"}, "state": "calm"},
                                {"when": {}, "state": "mixed"}]},
            # THE SEEDED VOL DIAL MIRRORS THE REAL ONE'S SHAPE, including the
            # term-structure proxy. A fixture that keeps an older shape stops
            # testing the code that runs -- these four checks failed against a
            # tiny_config that still declared only the CFE keys.
            "vol": {"primary": "fred.vix",
                    "level_bands": [{"state": "elevated", "min_level": 20},
                                    {"state": "normal", "min_level": 0}],
                    "realized_implied": {"metric": "mkt_spy"},
                    "term_structure": {
                        "published": "challenger",
                        "dual_run_from": "2026-09-23",
                        "dual_run_until": "2026-12-23",
                        "basis_metric": "calc.vx1_vix_basis",
                        "champion": {
                            "metric": "calc.vx_front_ratio",
                            "requires_store_keys": ["cfe.vx1", "cfe.vx2"],
                            "ratio_bands": [
                                {"state": "contango", "min_ratio": 1.02},
                                {"state": "flat", "min_ratio": 0.99},
                                {"state": "backwardation", "min_ratio": 0.0}],
                            "persistence_sessions": 2},
                        "challenger": {
                            "metric": "calc.vix3m_over_vix",
                            "proxy_for": "vx_futures_curve",
                            "ratio_bands": [
                                {"state": "contango", "min_ratio": 1.05},
                                {"state": "flat", "min_ratio": 0.98},
                                {"state": "backwardation", "min_ratio": 0.0}],
                            "persistence_sessions": 2}}},
            "gamma": {"source": "exposure_engine", "symbol": "SPY"},
        },
        "contradictions": {
            "persistence_sessions": 2, "exception_sessions": 5,
            "window_days": 1826, "open_threshold_z": 2.0,
            "staleness_multiple": 2,
            "exception_alert_path": "report_only",
            "exception_alert_note": "report-only",
            "pairs": [{"id": "vix_vs_hy", "legs": ["fred.vix", "fred.hy_oas"],
                       "kind": "metric_pair", "polarities": [1, 1],
                       "expect": "same", "because": "seeded"}],
        },
    }


def compute_at(store, cfg, day: dt.date, stamp_n: int) -> dict:
    """One object for `day`, with a deterministic compute instant."""
    obj = regime.compute(as_of=regime.session_cutoff(day.isoformat()),
                         session_day=day.isoformat(), store=store, cfg=cfg,
                         computed_at=f"2026-09-19T{stamp_n:02d}:00:00+00:00")
    regime.store_object(obj, store)
    return obj


# ---------------------------------------------------------------------------
# A. Exact replay -- against the REAL store and its backfilled objects
# ---------------------------------------------------------------------------
def group_a() -> None:
    print(f"{LINE}\nA. EXACT REPLAY\n{LINE}")
    store = observations.ObservationStore()
    try:
        current = (regime.load_config() or {}).get("version")
        current_method = regime.METHOD_VERSION

        # THE SOURCE HASH IS CHECKED FIRST, because it is the thing that makes the
        # version mean anything. A version constant nobody is forced to change is a
        # version constant that stops being true: someone edits the band logic, does
        # not bump, and every stored object silently claims a method it was not
        # computed under -- and the replay gate PASSES, because it is comparing the
        # new code against objects it just relabelled.
        matches, declared, actual = regime.method_pinned()
        check(matches,
              f"regime.py and contradictions.py hash to the pinned "
              f"METHOD_SOURCE_SHA ({declared}); actual {actual}. If the change "
              f"alters what the object SAYS: bump METHOD_VERSION, run "
              f"`python -m regime method --update`, re-backfill. If it does not: "
              f"run the update alone")

        all_rows = list(store.as_of(regime.STORE_KEY))
        # ONLY OBJECTS COMPUTED UNDER THE CURRENT RULES CAN BE REPLAYED.
        #
        # A stored object records its config_version. When the config changes on
        # purpose -- a dimension given new members, a contradiction pair pointed at
        # a different series -- every older object legitimately recomputes to
        # something else, and failing on that would mean the gate cannot tell "the
        # rules changed" from "the arithmetic broke". Those are the two things it
        # exists to distinguish, so superseded objects are REPORTED and skipped.
        # BOTH VERSIONS, and they answer different questions: config_version says
        # the RULES were edited, method_version says the CODE was. An object computed
        # under either an older rule set or an older method legitimately recomputes
        # to something else, and failing on that would mean the gate cannot tell a
        # deliberate change from a regression -- which are the two things it exists
        # to distinguish.
        rows = []
        for r in all_rows:
            o = json.loads(r["value_text"])
            if (o.get("config_version") == current
                    and o.get("method_version") == current_method):
                rows.append(r)
        superseded = len(all_rows) - len(rows)
        check(bool(all_rows), f"the store holds market_state objects "
                              f"({len(all_rows)})")
        if superseded:
            print(f"        {superseded} object(s) were computed under an earlier "
                  f"config or method version and are not replayed against "
                  f"{current}/{current_method}; re-run `regime backfill` to bring "
                  f"them forward")
        check(bool(rows),
              f"and {len(rows)} of them were computed under the current config "
              f"{current!r} AND method {current_method!r}, so there is something to "
              f"replay. A store where EVERY object is superseded is a store whose "
              f"history no longer matches its own rules")
        check(all(json.loads(r["value_text"]).get("method_version")
                  for r in all_rows),
              "and every stored object records a method_version at all -- an object "
              "that does not cannot be told from one computed under any other "
              "method")
        if not rows:
            return
        # The newest and the oldest: the oldest has no history, the newest has
        # eight predecessors, and persistence is the part most likely to replay
        # differently.
        for label, row in (("newest", rows[-1]), ("oldest", rows[0])):
            stored = json.loads(row["value_text"])
            again = regime.compute(as_of=stored["as_of"],
                                   session_day=stored["session"],
                                   computed_at=stored["computed_at"],
                                   store=store)
            a, b = regime.replay_fields(stored), regime.replay_fields(again)
            if a == b:
                ok(f"the {label} object ({stored['session']}) replays EXACTLY "
                   f"from the store")
            else:
                diffs = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
                bad(f"the {label} object ({stored['session']}) does not replay; "
                    f"fields differing: {diffs}")
        stored = json.loads(rows[-1]["value_text"])
        check(regime.replay_fields(stored) != stored,
              "and replay_fields() does strip the provenance it claims to -- a "
              "comparison that included computed_at could never pass")
        for f in ("computed_at", "git_sha"):
            check(f not in regime.replay_fields(stored),
                  f"{f} is excluded from the comparison")
        check("dimensions" in regime.replay_fields(stored)
              and "contradictions" in regime.replay_fields(stored),
              "while the dimensions and the contradiction table ARE compared")
    finally:
        store.close()


# ---------------------------------------------------------------------------
# B. No future leak
# ---------------------------------------------------------------------------
def group_b(store) -> None:
    print(f"\n{LINE}\nB. NO FUTURE LEAK\n{LINE}")
    cfg = tiny_config()
    days = weekdays_back(END, 300)
    seed(store, "fred.vix", days, [15.0 + (i % 5) * 0.1 for i in range(300)])
    seed(store, "fred.hy_oas", days, [3.0 + (i % 7) * 0.01 for i in range(300)])
    seed(store, "fred.bb_oas", days, [2.0 + (i % 3) * 0.01 for i in range(300)])

    before = regime.compute(as_of=regime.session_cutoff(END.isoformat()),
                            session_day=END.isoformat(), store=store, cfg=cfg,
                            computed_at="2026-09-19T01:00:00+00:00")
    # A VIX of 90 dated three days ago, published a week after the cutoff. If the
    # object filtered on observed_at this would move volatility to elevated and
    # every percentile with it.
    leak_day = END - dt.timedelta(days=3)
    store.write_many([{"registry_key": "fred.vix", "instrument": None,
                       "observed_at": leak_day.isoformat(),
                       "available_at": "2026-09-25T12:00:00+00:00",
                       "value": 90.0, "source": "synthetic"}])
    after = regime.compute(as_of=regime.session_cutoff(END.isoformat()),
                           session_day=END.isoformat(), store=store, cfg=cfg,
                           computed_at="2026-09-19T01:00:00+00:00")
    check(regime.replay_fields(before) == regime.replay_fields(after),
          "a VIX print knowable only next week changes nothing about this "
          "object -- not a state, not a percentile, not a rounding digit")

    later = regime.compute(as_of="2026-09-26T21:30:00+00:00",
                           session_day="2026-09-25", store=store, cfg=cfg,
                           computed_at="2026-09-19T01:00:00+00:00")
    # IT ARRIVES AS A REVISION, NOT A NEW PERIOD -- the leak row shares its
    # observed_at with an observation already in the series, which is the shape a
    # restatement has. So the newest LEVEL is unchanged (2026-09-18 is still the
    # last session) and what moves is the distribution the level sits in. Looking
    # for a changed level here was the wrong field, not a working store.
    z_before = before["dimensions"]["volatility"]["members"][0]["z_score"]
    z_later = later["dimensions"]["volatility"]["members"][0]["z_score"]
    check(z_before != z_later,
          f"and the same print IS seen once the cutoff passes it: a 90 in the "
          f"window moves the level's z from {z_before} to {z_later} -- so B "
          f"tests the as-of join and not a lost write")


# ---------------------------------------------------------------------------
# C. Every rule is declared, in config
# ---------------------------------------------------------------------------
def group_c() -> None:
    print(f"\n{LINE}\nC. EVERY DIMENSION HAS A DECLARED RULE\n{LINE}")
    cfg = regime.load_config()
    dims = cfg.get("dimensions") or {}
    check(len(dims) == 8, f"v1 declares eight dimensions (got {len(dims)})")
    for name in ("growth", "inflation", "rates", "liquidity", "credit", "trend",
                 "breadth", "volatility"):
        check(name in dims, f"{name} is declared")

    for name, spec in dims.items():
        bands = spec.get("bands") or []
        check(bool(bands), f"{name}: declares bands")
        mins = [float(b.get("min_percentile", -1)) for b in bands]
        check(mins == sorted(mins, reverse=True),
              f"{name}: bands are ordered high to low, so the first match wins "
              f"deterministically ({mins})")
        check(mins and min(mins) == 0.0,
              f"{name}: the lowest band starts at 0, so no percentile falls "
              f"through with no state")
        check(bool(spec.get("horizon")), f"{name}: declares a horizon")
        members = spec.get("members") or []
        check(bool(members), f"{name}: declares at least one member")
        for m in members:
            check(bool(m.get("metric")), f"{name}: every member names a metric")
            check(int(m.get("polarity", 0)) in (1, -1),
                  f"{name}/{m.get('metric')}: polarity is +1 or -1, not a "
                  f"weight -- a weight would be the composite this design "
                  f"refuses")
            check(bool(m.get("because")),
                  f"{name}/{m.get('metric')}: the polarity carries a reason, "
                  f"because getting one backwards inverts the whole dimension")
        states = set(spec.get("states") or [])
        band_states = {b.get("state") for b in bands}
        check(not states or states == band_states,
              f"{name}: the declared states and the bands' states agree "
              f"({sorted(states)} vs {sorted(band_states)})")

    dials = cfg.get("dials") or {}
    for d in ("macro", "vol", "gamma"):
        check(d in dials, f"dial {d} is declared")
    check(bool((dials.get("macro") or {}).get("rules")),
          "the macro dial is a declared lookup table, not a model")
    check(any(not (r.get("when") or {})
              for r in (dials.get("macro") or {}).get("rules") or []),
          "and it has a catch-all, so no combination of states falls through")
    check((dials.get("gamma") or {}).get("source") == "exposure_engine",
          "the gamma dial READS the exposure engine rather than recomputing "
          "dealer gamma")

    # The method version is declared, pinned, and named where a human will look.
    check(bool(regime.METHOD_VERSION) and regime.METHOD_SOURCE_SHA != "PENDING",
          f"a method_version is declared and its source hash pinned "
          f"({regime.METHOD_VERSION}, {regime.METHOD_SOURCE_SHA})")
    check("regime.py" in regime.METHOD_SOURCE_FILES
          and "contradictions.py" in regime.METHOD_SOURCE_FILES,
          f"and the hash covers both modules that decide the object's content "
          f"({list(regime.METHOD_SOURCE_FILES)})")
    ledger = (REPO / "docs" / "chester-reports-audit-3.md").read_text(
        encoding="utf-8")
    check(regime.METHOD_VERSION in ledger,
          f"and {regime.METHOD_VERSION} is named in the status ledger -- a bump "
          f"nobody recorded is a bump nobody can date")

    pairs = (cfg.get("contradictions") or {}).get("pairs") or []
    check(len(pairs) == 8,
          f"eight contradiction pairs are declared -- six computed, the reserved "
          f"prediction-markets pair, and 6c-2's narrative_vs_data (got "
          f"{len(pairs)})")
    narr = [p for p in pairs if p.get("kind") == contra.NARRATIVE_KIND]
    check(len(narr) == 1 and narr[0].get("id") == "narrative_vs_data"
          and pairs[-1].get("id") == "narrative_vs_data",
          "exactly one narrative pair, narrative_vs_data, appended after the "
          "others -- it expands to one row per story, so the declared table's "
          "shape stays fixed")
    for p in pairs:
        check(bool(p.get("id")) and bool(p.get("legs")),
              f"{p.get('id')}: declares an id and its legs")
        check(bool(p.get("because")), f"{p.get('id')}: declares why it is a pair")
    reserved = [p for p in pairs if p.get("kind") == contra.RESERVED_KIND]
    check(len(reserved) == 1,
          "exactly one row is reserved, and it names what it requires")
    c = cfg.get("contradictions") or {}
    for f in ("open_threshold_z", "persistence_sessions", "exception_sessions",
              "staleness_multiple"):
        check(f in c, f"contradictions declare {f} in config, not in code")
    check("max_staleness_sessions" not in c
          and "max_staleness_sessions" not in (cfg.get("defaults") or {}),
          "and the hand-set session count it replaced is GONE rather than left "
          "beside it -- two staleness rules in one config is one rule nobody can "
          "predict")

    # THE NEGATIVE CHECK: the thresholds are not ALSO in the code.
    import re
    src = (REPO / "regime.py").read_text(encoding="utf-8")
    # Docstrings and comments stripped first: this file EXPLAINS the states at
    # length, and a check that tripped on its own explanation is a check somebody
    # deletes.
    body = re.sub(r'(?s)""".*?"""', "", src)
    body = re.sub(r"#.*", "", body)
    check("expanding" not in body and "stressed" not in body,
          "and no dimension STATE NAME appears in regime.py's code -- the state "
          "vocabulary lives in the config, so adding a dimension is a config "
          "change")
    check("fred." not in body,
          "nor does any metric id -- regime.py carries no series of its own")


# ---------------------------------------------------------------------------
# D. contradicting is never empty by omission
# ---------------------------------------------------------------------------
def group_d(store) -> None:
    print(f"\n{LINE}\nD. `contradicting` IS NEVER EMPTY BY OMISSION\n{LINE}")
    real = observations.ObservationStore()
    try:
        rows = real.as_of(regime.STORE_KEY)
        bad_rows = []
        stated, with_list = 0, 0
        for r in rows:
            obj = json.loads(r["value_text"])
            for name, d in (obj.get("dimensions") or {}).items():
                if d.get("state") is None:
                    continue
                c = d.get("contradicting")
                if c == [] or c is None:
                    bad_rows.append((obj["session"], name))
                elif c == regime.NONE_FOUND:
                    stated += 1
                else:
                    with_list += 1
        check(not bad_rows,
              f"across {len(rows)} stored objects, no dimension with a state has "
              f"an empty or missing `contradicting` "
              f"({stated} say 'none found', {with_list} name metrics)"
              + (f" -- offenders: {bad_rows[:5]}" if bad_rows else ""))
        check(stated + with_list > 0,
              "and there were dimensions with states to check, so this is not "
              "vacuously true")
    finally:
        real.close()

    cfg = tiny_config()
    obj = regime.compute(as_of=regime.session_cutoff(END.isoformat()),
                         session_day=END.isoformat(), store=store, cfg=cfg,
                         computed_at="2026-09-19T02:00:00+00:00")
    cd = obj["dimensions"]["credit"]
    check(cd.get("contradicting") == regime.NONE_FOUND,
          f"a single-member dimension records 'none found' as a POSITIVE CLAIM "
          f"rather than an empty list (got {cd.get('contradicting')!r}) -- so a "
          f"reader can tell 'we looked and everything agreed' from 'nobody "
          f"looked'")


# ---------------------------------------------------------------------------
# E. Persistence
# ---------------------------------------------------------------------------
def group_e(store) -> None:
    print(f"\n{LINE}\nE. PERSISTENCE -- A STATE DOES NOT FLAP\n{LINE}")
    cfg = tiny_config(persistence=3)
    # A credit series that sits MID-DISTRIBUTION for 201 sessions and then blows
    # out. The middle matters: the first attempt used a rising sawtooth, whose last
    # calm value is the maximum of its own window -- and on hy_oas's -1 polarity a
    # maximum spread reads as `stressed`, so the "before" state was already the
    # state being tested for and the transition could not be seen. The tail is 3.0
    # against a window of 2.9s and 3.1s, which is the 50th percentile and
    # therefore `neutral`.
    days = weekdays_back(END, 204)
    calm = [2.9, 3.1] * 100 + [3.0]
    blown = [9.0, 9.1, 9.2]
    seed(store, "fred.hy_oas", days, calm + blown)
    seed(store, "fred.vix", days, [15.0] * 204)
    seed(store, "fred.bb_oas", days, [2.0 + (i % 3) * 0.01 for i in range(204)])

    seen = []
    for i, day in enumerate(days[-4:]):
        obj = compute_at(store, cfg, day, 10 + i)
        d = obj["dimensions"]["credit"]
        seen.append((day.isoformat(), d.get("state"), d.get("raw_state"),
                     d.get("pending_state"), d.get("pending_sessions")))
    for s in seen:
        print(f"        {s[0]}  published={s[1]}  raw={s[2]}  "
              f"pending={s[3]} ({s[4]})")

    check(seen[0][1] == "neutral",
          f"before the blowout credit sits mid-distribution, published neutral "
          f"(got {seen[0][1]})")
    check(seen[1][2] == "stressed" and seen[1][1] == "neutral",
          f"the first stressed reading does NOT publish: raw {seen[1][2]}, "
          f"published {seen[1][1]}")
    check(seen[1][3] == "stressed" and seen[1][4] == 1,
          f"it is recorded as pending, 1 of 3 sessions (got {seen[1][3]}, "
          f"{seen[1][4]})")
    check(seen[2][1] == "neutral" and seen[2][4] == 2,
          f"nor does the second (published {seen[2][1]}, pending {seen[2][4]} "
          f"of 3)")
    check(seen[3][1] == "stressed",
          f"the third publishes it, the declared count being met "
          f"(got {seen[3][1]})")
    last = regime.latest(session_day=days[-1].isoformat(), store=store)
    check(last["dimensions"]["credit"].get("last_changed") == days[-1].isoformat(),
          f"and last_changed is the session it changed on, not the session the "
          f"reading first appeared "
          f"({last['dimensions']['credit'].get('last_changed')})")


# ---------------------------------------------------------------------------
# F. Staleness
# ---------------------------------------------------------------------------
def group_f(store) -> None:
    print(f"\n{LINE}\nF. A STALE DIMENSION GOES ABSENT, NOT FORWARD\n{LINE}")
    cfg = tiny_config()
    days = weekdays_back(END, 100)
    seed(store, "fred.vix", days, [15.0 + (i % 5) * 0.1 for i in range(100)])
    seed(store, "fred.bb_oas", days, [2.0] * 100)
    seed(store, "fred.hy_oas", days, [3.0 + (i % 5) * 0.01 for i in range(100)])

    fresh = regime.compute(as_of=regime.session_cutoff(END.isoformat()),
                           session_day=END.isoformat(), store=store, cfg=cfg,
                           computed_at="2026-09-19T20:00:00+00:00")
    check(fresh["dimensions"]["volatility"].get("state") is not None,
          "on the last seeded session volatility has a state")

    # Ten sessions later, nothing new written. The declared allowance is 4.
    far = (END + dt.timedelta(days=21)).isoformat()
    stale = regime.compute(as_of=regime.session_cutoff(far), session_day=far,
                           store=store, cfg=cfg,
                           computed_at="2026-09-19T21:00:00+00:00")
    v = stale["dimensions"]["volatility"]
    check(v.get("state") is None,
          f"three weeks on, with nothing new written, it is ABSENT rather than "
          f"carrying its last state forward (got {v.get('state')})")
    r = v.get("absent_reason") or ""
    check("sessions before this cutoff" in r and "own allowance" in r
          and "not a daily calendar" in r,
          f"and the reason names the staleness, the metric's OWN allowance and the "
          f"multiple: {r[:140]}")
    check(stale["dials"]["vol"].get("state") is None,
          "the vol dial goes absent on the same argument -- a vol dial is a "
          "statement about today")
    # THE TERM-STRUCTURE LEG NOW COMPUTES, FROM A DECLARED PROXY. The check this
    # replaces asserted the opposite -- that the leg stayed absent naming the CFE keys
    # and was "not approximated from something else" -- which was right for the design
    # it was written against and was deliberately overruled: VIX3M/VIX runs today,
    # labelled, while the curve waits on a subscription. What must hold now is
    # stronger than absence, and it is that the label cannot be lost.
    # THE LEG RUNS TWO NOW, and what must hold is that neither can be mistaken for
    # the other. Cboe's public settlement files made the curve reachable, so the
    # champion computes -- and the proxy is NOT retired on the day its champion
    # arrives, because reports have been read against the proxy's published state
    # and switching silently would change what a printed word means.
    ts = stale["dials"]["vol"].get("term_structure") or {}
    champ = ts.get("champion") or {}
    chal = ts.get("challenger") or {}
    check(champ.get("metric") == "calc.vx_front_ratio",
          f"the champion leg computes from the VX curve itself "
          f"({champ.get('metric')})")
    check(chal.get("metric") == "calc.vix3m_over_vix",
          f"the challenger leg computes from the proxy ({chal.get('metric')})")
    check(chal.get("proxy_for") == "vx_futures_curve",
          f"and the challenger still names what it STANDS IN FOR, so no rendering "
          f"can present it as the futures curve ({chal.get('proxy_for')})")
    check(champ.get("proxy_for") is None,
          "while the champion names no proxy_for -- it IS the curve, and a "
          "proxy_for on it would be a caveat about nothing")
    check(ts.get("published_by") in ("champion", "challenger"),
          f"the leg says which of the two its published state came from "
          f"({ts.get('published_by')})")
    check(ts.get("published_by") == "challenger",
          "and it is still the challenger -- the champion does not take over on "
          "the day it arrives; both print for the declared quarter")
    check(bool(ts.get("dual_run_until")),
          f"the dual run has a declared end date ({ts.get('dual_run_until')}), "
          f"so 'for a quarter' is a date and not an intention")
    check("cfe.vx1" in str(champ.get("requires_store_keys")),
          f"the champion names the CFE keys it needs "
          f"({champ.get('requires_store_keys')})")
    check(ts.get("legs_agree") in (True, False, None),
          f"and every object records whether the two legs agreed "
          f"({ts.get('legs_agree')}) -- the quarter's question is a count of "
          f"disagreeing sessions, not an opinion")
    for name, leg in (("champion", champ), ("challenger", chal)):
        check(int(leg.get("persistence_sessions") or 0) >= 2,
              f"the {name} has a persistence rule of its own "
              f"({leg.get('persistence_sessions')} sessions)")
    # AND THEIR BANDS ARE NOT THE SAME BANDS. A one-month futures spread sits
    # nearer 1.00 than a three-month/one-month implied ratio: reusing the
    # challenger's 1.05 contango threshold would read every ordinary curve as flat.
    cb = [b.get("min_ratio") for b in (champ.get("ratio_bands") or [])]
    hb = [b.get("min_ratio") for b in (chal.get("ratio_bands") or [])]
    check(cb and hb and cb != hb,
          f"the two legs carry DIFFERENT band thresholds ({cb} against {hb}) -- "
          f"the same thresholds on two different scales would make the "
          f"comparison meaningless")

    src = (REPO / "config" / "market_state.yaml").read_text(encoding="utf-8")
    check("NOT the VX futures curve" in src or "not the VX futures curve" in src,
          "and the config says in words that the challenger is not the futures "
          "curve")


def group_f2(store) -> None:
    print(f"\n{LINE}\nF2. STALENESS IS PER CADENCE, NOT A DAILY CALENDAR\n{LINE}")
    # THE CASE GROWTH MADE. fred.claims_4wk is WEEKLY (allowance 8 sessions) and
    # fred.vix is DAILY (allowance 2). One hand-set session count for both either
    # forgives the daily series a fortnight's silence or condemns the weekly one for
    # printing on schedule. Seeded so the two verdicts have to differ.
    cfg = tiny_config()
    cfg["dimensions"]["growth"] = {
        "horizon": "1-3m", "states": ["expanding", "slowing", "contracting"],
        "bands": [{"state": "expanding", "min_percentile": 66},
                  {"state": "slowing", "min_percentile": 33},
                  {"state": "contracting", "min_percentile": 0}],
        "members": [{"metric": "fred.claims_4wk", "polarity": -1,
                     "because": "weekly, and the point of this case"}]}

    weekly = [d for d in weekdays_back(END, 300) if d.weekday() == 3][-40:]
    seed(store, "fred.claims_4wk", weekly,
         [220000.0 + (i % 7) * 500 for i in range(len(weekly))])
    daily = weekdays_back(END, 300)
    seed(store, "fred.vix", daily, [15.0 + (i % 9) * 0.2 for i in range(300)])
    seed(store, "fred.bb_oas", daily, [2.0] * 300)
    seed(store, "fred.hy_oas", daily, [3.0 + (i % 5) * 0.01 for i in range(300)])

    claims_alw, claims_why = derived.staleness_allowance("fred.claims_4wk")
    vix_alw, vix_why = derived.staleness_allowance("fred.vix")
    mult = cfg["defaults"]["staleness_multiple"]
    check(claims_alw == 8 and vix_alw == 2,
          f"a weekly series allows {claims_alw} sessions and a daily one "
          f"{vix_alw} -- read from the registry, not set in this file "
          f"({claims_why}; {vix_why})")

    obj = regime.compute(as_of=regime.session_cutoff(END.isoformat()),
                         session_day=END.isoformat(), store=store, cfg=cfg,
                         computed_at="2026-09-19T05:00:00+00:00")
    g = obj["dimensions"]["growth"]
    v = obj["dimensions"]["volatility"]
    check(g.get("state") is not None,
          f"the weekly dimension HAS a state, its newest print being "
          f"{g['members'][0]['staleness_sessions']} sessions old against a limit of "
          f"{claims_alw} x {mult} (got {g.get('state')}; "
          f"{str(g.get('absent_reason'))[:70]})")
    check(v.get("state") is not None,
          f"and the daily one has a state too, its print being current "
          f"({v.get('state')})")
    check(g.get("staleness_limit_sessions") == claims_alw * mult
          and v.get("staleness_limit_sessions") == vix_alw * mult,
          f"and THE TWO LIMITS DIFFER, which is the whole point: growth "
          f"{g.get('staleness_limit_sessions')} sessions vs volatility "
          f"{v.get('staleness_limit_sessions')}")

    # Move the cutoff far enough to kill the daily series and not the weekly one.
    later = (END + dt.timedelta(days=9)).isoformat()
    obj2 = regime.compute(as_of=regime.session_cutoff(later), session_day=later,
                          store=store, cfg=cfg,
                          computed_at="2026-09-19T06:00:00+00:00")
    g2 = obj2["dimensions"]["growth"]
    v2 = obj2["dimensions"]["volatility"]
    check(v2.get("state") is None,
          f"nine calendar days on the DAILY dimension is absent, past its "
          f"{vix_alw * mult}-session limit")
    check(g2.get("state") is not None,
          f"while the WEEKLY one still has a state, its limit being "
          f"{claims_alw * mult} (got {g2.get('state')}) -- one hand-set count "
          f"could not have produced both verdicts")


# ---------------------------------------------------------------------------
# G. The contradiction arithmetic
# ---------------------------------------------------------------------------
def group_g(store) -> None:
    print(f"\n{LINE}\nG. THE CONTRADICTION ARITHMETIC\n{LINE}")
    cfg = tiny_config()
    days = weekdays_back(END, 210)

    # Two legs that track each other for 200 sessions, then split hard for six.
    # Hand-computed below from the same definition the module documents.
    vix = [15.0 + (i % 10) * 0.5 for i in range(200)]
    hy = [3.0 + (i % 10) * 0.1 for i in range(200)]
    vix += [15.0, 15.0, 15.0, 15.0, 15.0, 15.0]
    hy += [9.0, 9.2, 9.4, 9.6, 9.8, 10.0]
    seed(store, "fred.vix", days[:206], vix)
    seed(store, "fred.hy_oas", days[:206], hy)
    seed(store, "fred.bb_oas", days[:206], [2.0] * 206)

    states = []
    for i, day in enumerate(days[199:206]):
        obj = compute_at(store, cfg, day, 30 + i)
        row = [r for r in obj["contradictions"] if r["id"] == "vix_vs_hy"][0]
        states.append((day.isoformat(), row.get("open_state"),
                       row.get("magnitude"), row.get("persistence_days"),
                       row.get("exception"), row.get("since")))
    for s in states:
        print(f"        {s[0]}  {str(s[1]):8} z={s[2]}  days={s[3]}  exc={s[4]}")

    hand = _hand_gap_z(vix[:201], hy[:201])
    check(states[1][2] is not None and abs(states[1][2] - hand) < 1e-6,
          f"the magnitude matches the hand computation to six places "
          f"(module {states[1][2]}, by hand {hand})")
    fired = [s for s in states if s[1] in ("pending", "open")]
    check(bool(fired), "the seeded split does cross the threshold")
    check(states[1][1] == "pending",
          f"the first crossing does NOT open the row (got {states[1][1]}) -- a "
          f"single day's disagreement is noise")
    opened = [s for s in states if s[1] == "open"]
    check(bool(opened) and opened[0][3] >= 2,
          f"it opens once the condition has held the declared 2 sessions "
          f"(first open at {opened[0][0] if opened else 'never'}, "
          f"{opened[0][3] if opened else 0} days)")
    first_crossing = states[1][0]
    check(opened and all(o[5] == first_crossing for o in opened),
          f"and `since` is the session the DIVERGENCE began ({first_crossing}), "
          f"not the later session the row was published on, and it does not "
          f"reset while the row stays open ({sorted({o[5] for o in opened})})")
    exc = [s for s in states if s[4]]
    check(bool(exc) and exc[0][3] >= 5,
          f"at five sessions it becomes an EXCEPTION "
          f"({exc[0][0] if exc else 'never'}, {exc[0][3] if exc else 0} days)")
    if exc:
        obj = regime.latest(session_day=exc[0][0], store=store)
        row = [r for r in obj["contradictions"] if r["id"] == "vix_vs_hy"][0]
        check(row.get("alert_path") == "report_only",
              f"and the exception says REPORT-ONLY on the row, because this repo "
              f"has no exceptions alert path (got {row.get('alert_path')!r})")


def group_h(store) -> None:
    print(f"\n{LINE}\nH. PERSISTENCE CHAINS: EXACTLY ONE FIRST OBJECT\n{LINE}")
    # THE BUG THIS CASE EXISTS FOR. The first backfill gave every one of 77 sessions
    # an empty history -- each read its predecessors at that session's own market
    # cutoff, and they had been written minutes earlier in real time -- so all 77
    # published their raw reading as a "first object" and persistence never engaged.
    # The output was entirely plausible. A run of N sessions must produce exactly
    # ONE first object per dimension, and this asserts it over a real backfill.
    cfg = tiny_config()
    days = weekdays_back(END, 300)
    seed(store, "fred.vix", days, [15.0 + (i % 11) * 0.3 for i in range(300)])
    seed(store, "fred.bb_oas", days, [2.0 + (i % 4) * 0.02 for i in range(300)])
    seed(store, "fred.hy_oas", days, [3.0 + (i % 9) * 0.02 for i in range(300)])

    first_day, last_day = days[-12].isoformat(), days[-1].isoformat()
    import regime as rg
    saved = rg._CONFIG                       # noqa: SLF001
    rg._CONFIG = cfg                         # noqa: SLF001
    try:
        r = rg.backfill(first_day, last_day, store=store, verbose=False)
    finally:
        rg._CONFIG = saved                   # noqa: SLF001

    check(r["computed"] >= 10,
          f"the backfill ran over {r['computed']} sessions (N > 1, which is the "
          f"precondition for this case meaning anything)")
    check(r.get("ordered") is True,
          "and it reports that it ran in ascending session order")

    objs = [json.loads(x["value_text"]) for x in store.as_of(rg.STORE_KEY)]
    objs = [o for o in objs if first_day <= o["session"] <= last_day]
    objs.sort(key=lambda o: o["session"])
    check(len(objs) == r["computed"],
          f"and stored one object per session ({len(objs)} of {r['computed']})")

    firsts: dict[str, list[str]] = {}
    for o in objs:
        for name, d in (o.get("dimensions") or {}).items():
            if str(d.get("persistence") or "").startswith("first object"):
                firsts.setdefault(name, []).append(o["session"])

    offenders = {k: v for k, v in firsts.items() if len(v) > 1}
    check(not offenders,
          f"NO DIMENSION reports a first object twice "
          f"({ {k: len(v) for k, v in firsts.items()} })"
          + (f" -- offenders: {offenders}" if offenders else ""))
    check(bool(firsts),
          f"and at least one dimension DID report one, so this is not vacuously "
          f"true ({sorted(firsts)})")
    for name, sessions in firsts.items():
        check(sessions[0] == objs[0]["session"],
              f"{name}'s first object is the first session of the run "
              f"({sessions[0]} == {objs[0]['session']})")

    # The chain itself: every object after the first names its predecessor, and the
    # predecessor it names is the session before it.
    check(objs[0].get("previous_object") is None,
          "the run's first object names no predecessor")
    broken = []
    for prev, cur in zip(objs, objs[1:]):
        po = cur.get("previous_object") or {}
        if po.get("session") != prev["session"]:
            broken.append((cur["session"], po.get("session"), prev["session"]))
    check(not broken,
          f"and every later object names the session immediately before it as the "
          f"predecessor its persistence rested on"
          + (f" -- broken: {broken[:3]}" if broken else f" ({len(objs) - 1} links)"))
    check(all((o.get("previous_object") or {}).get("config_version")
              == cfg["version"] for o in objs[1:]),
          "each link records the predecessor's config_version, so persistence "
          "across a rules change is distinguishable from persistence within one")


def _hand_gap_z(a: list[float], b: list[float]) -> float:
    """The documented definition, written out independently."""
    ma, sa = statistics.fmean(a), statistics.stdev(a)
    mb, sb = statistics.fmean(b), statistics.stdev(b)
    za = [(x - ma) / sa for x in a]
    zb = [(x - mb) / sb for x in b]
    gaps = [x - y for x, y in zip(za, zb)]
    return round((gaps[-1] - statistics.fmean(gaps)) / statistics.stdev(gaps), 4)


# ---------------------------------------------------------------------------
# I. THE MACRO TRANSFORMS, AND THE UNITS GUARD
# ---------------------------------------------------------------------------
# WHY A PLAUSIBLE BAND AND NOT A UNIT TEST ON THE ARITHMETIC. The arithmetic was
# never wrong: `bs - rrp - tga` is the right expression. The UNIT of one leg was
# wrong, and no test of the expression can catch that -- monthly_macro/compute.py
# had TGA in billions when WTREGEN is millions, returned -823.6 trillion for its
# whole life, and every reading of the code agreed with itself because CLAUDE.md
# and config.py carried the same wrong unit.
#
# What catches a units error is a statement about the WORLD: the Fed's balance
# sheet net of two drains is a few trillion dollars, and anything outside
# 2.5tn-10tn is arithmetic, not a regime. This group asserts the computed series
# is inside that band AND that the un-normalised subtraction is outside it, so the
# guard is shown to fire rather than assumed to.
def group_i(store) -> None:
    print(f"\n{LINE}\nI. THE MACRO TRANSFORMS: UNITS, CADENCE, POLARITY\n{LINE}")
    from altdata import market_features as mf

    lo, hi = mf.NET_LIQUIDITY_BAND
    print(f"  net-liquidity band: ${lo/1e12:.1f}tn to ${hi/1e12:.1f}tn")

    # --- the units guard, on a seeded week with REAL magnitudes --------------
    # WALCL 6,704,383 (millions), RRPONTSYD 11.677 (billions), WTREGEN 830,296
    # (millions) -- the actual observations of 27 May 2026.
    days = weekdays_back(END, 40)
    seed(store, "fred.fed_balance", days, [6_704_383.0] * len(days))
    seed(store, "fred.rrp", days, [11.677] * len(days))
    seed(store, "fred.tga", days, [830_296.0] * len(days))
    rows = [r for r in mf.macro_rows(store)
            if r["registry_key"] == "calc.net_liquidity"]
    check(bool(rows), f"calc.net_liquidity computes ({len(rows)} rows)")
    if rows:
        v = rows[-1]["value"]
        check(lo <= v <= hi,
              f"and lands INSIDE the plausible band (${v/1e12:.3f}tn) -- every leg "
              f"normalised to dollars before the subtraction")

    # THE WRONG UNIT, COMPUTED DELIBERATELY. This is what compute.py did.
    wrong = (6_704_383.0 / 1e6) - (11.677 / 1e3) - (830_296.0 / 1e3)
    check(not (lo <= wrong * 1e12 <= hi),
          f"and the OLD normalisation (TGA as billions) is outside it "
          f"({wrong:.1f} in its own units, {wrong * 1e12:.3g} in dollars) -- the "
          f"band is what makes a three-order-of-magnitude leg impossible to ship")
    check(wrong < 0,
          f"which the published Monthly printed as a liquidity level: {wrong:.1f}. "
          f"A negative net liquidity is not a tight regime, it is a unit")

    # --- SAME-DAY ONLY: no leg is carried forward ---------------------------
    # A row on a day one leg does not have would be a number dated to no session.
    extra = [d for d in weekdays_back(END, 60) if d not in days]
    seed(store, "fred.rrp", extra, [11.0] * len(extra))
    rows2 = [r for r in mf.macro_rows(store)
             if r["registry_key"] == "calc.net_liquidity"]
    check(len(rows2) == len(rows),
          f"adding RRP-only days adds NO net-liquidity rows ({len(rows2)} == "
          f"{len(rows)}) -- the series is the intersection of its three legs, "
          f"because carrying one forward would date the result to no session")

    # --- AVAILABILITY NEVER PRECEDES THE INPUTS ----------------------------
    late = [r for r in rows2
            if r["available_at"][:10] < str(r["observed_at"])[:10]]
    check(not late,
          f"no row claims to be knowable before its own session ({len(late)})")

    # --- THE REGISTRY AGREES WITH THE COMPUTATION --------------------------
    from altdata import derived
    for key in sorted(mf.MACRO_FEATURES):
        e = derived.registry_entry(key)
        check(bool(e), f"{key} is registered")
        if not e:
            continue
        check(e.get("observation_type") == "calculated",
              f"  {key}: observation_type calculated")
        check(e.get("trigger_eligible") is False,
              f"  {key}: NOT trigger_eligible")
        allow, why = derived.staleness_allowance(key)
        check(allow is not None and allow > 0,
              f"  {key}: staleness allowance {allow} sessions ({why})")
    du, _ = derived.delta_unit_for("calc.yoy_core_pce")
    check(du == "pp",
          f"a year-over-year rate moves in PERCENTAGE POINTS, not basis points "
          f"(got {du!r}) -- core PCE 3.29 to 3.41 is +0.12pp in the sentence a "
          f"macro reader is reading")
    du2, _ = derived.delta_unit_for("calc.yield_curve_2s10s")
    check(du2 == "bps",
          f"and a curve spread moves in basis points (got {du2!r})")

    # --- THE WIRING, off the declared config -------------------------------
    #
    # Read from config/market_state.yaml rather than from a computed object,
    # because this is a question about the RULES: a store with no macro data would
    # make every object here absent and the wiring unassertable, and the wiring is
    # exactly what must not drift.
    import regime as rg
    cfg = rg.load_config()
    dims = cfg.get("dimensions") or {}

    def members(name: str) -> list[str]:
        return [m.get("metric") for m in (dims.get(name) or {}).get("members") or []]

    liq = members("liquidity")
    check(liq[:1] == ["calc.net_liquidity"],
          f"liquidity's PRIMARY is calc.net_liquidity (members {liq}) -- the "
          f"primary was fred.rrp, one drain standing in for the whole quantity "
          f"because it was the only daily leg")
    check("fred.rrp" in liq and "fred.fed_balance" in liq,
          "and its legs stay as members, so a disagreement between the net figure "
          "and one of its parts is still visible")

    rates = members("rates")
    check("calc.yield_curve_2s10s" in rates,
          f"rates reads calc.yield_curve_2s10s ({rates})")
    check(rates and rates[0] != "calc.yield_curve_2s10s",
          f"and NOT as its primary (primary is {rates[0] if rates else None}) -- "
          f"the level is what everything is discounted at, and an inversion at 1% "
          f"and an inversion at 5% are different worlds")

    growth = members("growth")
    check("calc.sahm_rule" in growth, f"growth reads calc.sahm_rule ({growth})")
    check(growth and growth[0] != "calc.sahm_rule",
          f"and NOT as its primary (primary is {growth[0] if growth else None}): a "
          f"number that names a recession is exactly the kind that should not move "
          f"a state by itself")
    sahm_pol = next((m.get("polarity") for m in dims["growth"]["members"]
                     if m.get("metric") == "calc.sahm_rule"), None)
    check(sahm_pol == -1,
          f"with polarity -1 (got {sahm_pol}) -- the Sahm value RISES as "
          f"unemployment rises off its trailing low, so a high percentile is "
          f"weakening growth. A +1 here would read every recession as an expansion")
    curve_pol = next((m.get("polarity") for m in dims["rates"]["members"]
                      if m.get("metric") == "calc.yield_curve_2s10s"), None)
    check(curve_pol == -1,
          f"and 2s10s polarity -1 (got {curve_pol}): a flat curve is the policy "
          f"rate held above the long end, which is what `high` means")

    # NUMERIC, not lexical: "market-state-v1.10" sorts below "v1.8" as a string,
    # and this check failed on the first two-digit minor.
    vparts = tuple(int(x) for x in
                   str(cfg.get("version")).rsplit("-v", 1)[-1].split("."))
    check(vparts >= (1, 8),
          f"the config version records the rules change ({cfg.get('version')})")
    # AT LEAST method-6, not exactly: the check is that the liquidity change was
    # recorded as a method bump, and a later bump (method-7, 6c-2's narrative row)
    # must not read as that record being undone.
    method_n = int(str(rg.METHOD_VERSION).rsplit("-", 1)[-1])
    check(method_n >= 6,
          f"and the method version records that the object's meaning moved with "
          f"it ({rg.METHOD_VERSION}): an object whose liquidity state came from one "
          f"drain is not comparable with one whose state came from the quantity")


# ---------------------------------------------------------------------------
# J. An absence cites data
# ---------------------------------------------------------------------------
import ast        # noqa: E402
import builtins   # noqa: E402
import re         # noqa: E402

# Every builtin exception class except the Warning family (a reason may begin
# "Warning" as an English word, and no reader raises one), plus any CamelCase
# name ending Error or Exception -- sqlite3.OperationalError, FetchError and the
# rest are not builtins.
_BUILTIN_EXC = sorted(
    n for n, v in vars(builtins).items()
    if isinstance(v, type) and issubclass(v, BaseException)
    and not issubclass(v, Warning))
EXC_NAME = re.compile(r"\b(?:" + "|".join(_BUILTIN_EXC)
                      + r"|[A-Z][A-Za-z0-9]+(?:Error|Exception))\b")


def reason_strings(obj, path: str = "") -> list[tuple[str, str]]:
    """Every (path, text) under a key naming a reason, anywhere in the object."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}" if path else str(k)
            if "reason" in str(k) and isinstance(v, str):
                out.append((here, v))
            else:
                out.extend(reason_strings(v, here))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(reason_strings(v, f"{path}[{i}]"))
    return out


def exception_names_in_reasons(obj) -> list[str]:
    return [f"{p}: {EXC_NAME.search(t).group(0)}"
            for p, t in reason_strings(obj) if EXC_NAME.search(t)]


def static_reason_faults(src: str) -> list[str]:
    """Places a reason is built from a caught exception, found in the AST.

    A reason-named key -- a subscript target, a dict key, a keyword -- whose value
    mentions `__name__` or a name bound by an `except ... as` clause.
    """
    tree = ast.parse(src)
    exc_names = {h.name for h in ast.walk(tree)
                 if isinstance(h, ast.ExceptHandler) and h.name}

    def tainted(node) -> bool:
        return any((isinstance(n, ast.Attribute) and n.attr == "__name__")
                   or (isinstance(n, ast.Name) and n.id in exc_names)
                   for n in ast.walk(node))

    def is_reason(k) -> bool:
        return (isinstance(k, ast.Constant) and isinstance(k.value, str)
                and "reason" in k.value)

    hits = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if (isinstance(t, ast.Subscript) and is_reason(t.slice)
                        and tainted(n.value)):
                    hits.append(f"line {n.lineno}: [{t.slice.value!r}] = ...")
        elif isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if k is not None and is_reason(k) and tainted(v):
                    hits.append(f"line {n.lineno}: {{{k.value!r}: ...}}")
        elif isinstance(n, ast.keyword):
            if n.arg and "reason" in n.arg and tainted(n.value):
                hits.append(f"line {n.value.lineno}: {n.arg}=...")
    return hits


def group_j(store) -> None:
    print(f"\n{LINE}\nJ. AN ABSENCE CITES DATA; A FAULT IS A FAULT\n{LINE}")

    # --- the detector, shown to fire before it is trusted -------------------
    old = ("probability_ledger.tail_weight: the probability ledger could not be "
           "read (AttributeError) -- reported absent rather than assumed")
    check(bool(exception_names_in_reasons({"also_reads": {"absent_reason": old}})),
          "the detector fires on the string every object carried from Phase 2 "
          "to method-7 (AttributeError)")
    for s_ in ("sqlite3.OperationalError: no such table",
               "KeyError: 'x'", "reader raised FetchError"):
        check(bool(exception_names_in_reasons({"r": {"absent_reason": s_}})),
              f"and on {s_!r}")
    check(not exception_names_in_reasons(
              {"absent_reason": "no observations for ['fred.vix'] knowable at "
                                "2026-09-25; Warning: stale"}),
          "and not on a data reason")
    check(not exception_names_in_reasons(
              {"because": "an Exception row is report-only (KeyError aside)"}),
          "and only reason-named keys are read -- a `because` is prose about "
          "the rule, not a reason for an absence")

    # --- static: no method module builds a reason from a caught exception ---
    for name in regime.METHOD_SOURCE_FILES:
        hits = static_reason_faults((REPO / name).read_text(encoding="utf-8"))
        check(not hits, f"{name} builds no reason string from a caught "
                        f"exception{': ' + '; '.join(hits) if hits else ''}")
    probe = ("try:\n    x()\nexcept Exception as exc:\n"
             "    out['absent_reason'] = f'{type(exc).__name__}'\n")
    check(bool(static_reason_faults(probe)),
          "and the static check fires on the shape it forbids")

    # --- every stored object under the current method ------------------------
    live = observations.ObservationStore()
    try:
        cur = regime.METHOD_VERSION
        objs = [json.loads(r["value_text"]) for r in live.as_of(regime.STORE_KEY)]
        objs = [o for o in objs if o.get("method_version") == cur]
    finally:
        live.close()
    hits = [(o.get("session"), h) for o in objs
            for h in exception_names_in_reasons(o)]
    check(not hits,
          f"no stored {cur} object ({len(objs)}) names an exception class in a "
          f"reason" + (f": {hits[:3]}" if hits else ""))

    # --- seeded: the tail-weight read, three ways ----------------------------
    from altdata import probability_ledger as pl
    spec = {"scenario_set_prefix": "tail:"}
    what = "probability_ledger.tail_weight"
    at = "2026-09-25T20:05:00+00:00"
    empty = contra.tail_weight(what, spec, at, store)
    check(empty.get("value") is None
          and "0 forecast(s) live" in str(empty.get("absent_reason"))
          and not empty.get("fault"),
          f"an empty ledger is ABSENT with a data reason: "
          f"{str(empty.get('absent_reason'))[:90]}")
    with pl.ProbabilityLedger(str(store.path)) as led:
        led.record(source="monthly_macro", scenario_set="monthly_macro:2026-09-01",
                   claim="Soft landing", probability=0.6,
                   emitted_at="2026-09-01T00:00:00+00:00",
                   horizon_date="2026-12-01", resolution_criterion="seeded")
        for claim, p, when in (("Credit event", 0.10, "2026-09-01"),
                               ("Equity crash", 0.05, "2026-09-01"),
                               ("Credit event", 0.12, "2026-09-10"),
                               ("Equity crash", 0.08, "2026-09-10"),
                               ("Credit event", 0.50, "2026-09-30")):
            led.record(source="tail_watch", scenario_set=f"tail:{when}",
                       claim=claim, probability=p,
                       emitted_at=f"{when}T00:00:00+00:00",
                       horizon_date="2026-12-31", resolution_criterion="seeded")
    got = contra.tail_weight(what, spec, at, store)
    check(got.get("value") == 0.2 and got.get("scenario_set") == "tail:2026-09-10",
          f"with tail sets live, the weight is the NEWEST set's sum knowable at "
          f"the cutoff -- 0.12 + 0.08, not the older set added in and not the "
          f"set emitted after it (got {got.get('value')} from "
          f"{got.get('scenario_set')})")
    early = contra.tail_weight(what, spec, "2026-09-05T20:05:00+00:00", store)
    check(early.get("value") == 0.15,
          f"and replayed at 5 September it reads the set live then (got "
          f"{early.get('value')})")

    orig = pl.ProbabilityLedger.live_as_of
    try:
        def boom(self, as_of):
            raise RuntimeError("seeded fault")
        pl.ProbabilityLedger.live_as_of = boom
        f = contra.tail_weight(what, spec, at, store)
    finally:
        pl.ProbabilityLedger.live_as_of = orig
    check(bool(f.get("fault")) and "RuntimeError" in f["fault"]
          and not f.get("absent_reason"),
          "a reader that raises records `fault` and NO absent_reason")
    check(not exception_names_in_reasons({"also_reads": f}),
          "so the gate passes on it: the fault is visible and named as one")
    check(regime.why_absent(f).startswith("FAULT (code, not data)"),
          "and it prints as FAULT, never as an absence")


# ---------------------------------------------------------------------------
# K. THE RATES-DRIVER MEMBERS (signal-triage ST-3)
#
# Known answers on seeded straight lines: a 10-year rising 2bp a session with the
# real yield rising 1.6bp and the 2-year 1bp is a real share of exactly 0.8 and a
# curve share of exactly 0.5 at every window. A flat stretch first, so the move
# floor has something to refuse.
# ---------------------------------------------------------------------------
def group_k(store) -> None:
    print(f"\n{LINE}\nK. THE RATES-DRIVER MEMBERS: THE CUTS, THE SHARES, THE "
          f"CORRELATION\n{LINE}")
    import math
    from altdata import market_features as mf

    flat, n = 30, 91
    days = weekdays_back(END, n)
    up = [0.0] * flat + [0.02 * (i + 1) for i in range(n - flat)]
    seed(store, "fred.yield_10y", days, [4.00 + u for u in up])
    seed(store, "fred.tips_10y", days, [1.80 + 0.8 * u for u in up])
    seed(store, "fred.yield_2y", days, [3.50 + 0.5 * u for u in up])
    seed(store, "fred.term_premium_kw", days, [0.50 + 0.5 * u for u in up])
    # DKW: path 0.75 and premium 0.25 of PATH + PREMIUM. The liquidity leg MOVES,
    # as much as the other two together: a share taken over the whole real move
    # (the v1.11 definition) would read 0.375 / 0.125 and fail these checks.
    seed(store, "dkw.exp_real_short_rate_10y", days, [1.0 + 0.3 * u for u in up])
    seed(store, "dkw.real_term_premium_10y", days, [0.4 + 0.1 * u for u in up])
    seed(store, "dkw.tips_liquidity_premium_10y", days, [0.2 + 0.4 * u for u in up])
    # THE LAST 10-YEAR TIPS PRINT ARRIVES LATE: the share built on it must say so.
    last = days[-1]
    late_at = dt.datetime(last.year, last.month, last.day, 23, 30,
                          tzinfo=dt.timezone.utc).isoformat()
    store.write_many([{"registry_key": "fred.tips_10y", "instrument": None,
                       "observed_at": last.isoformat(), "available_at": late_at,
                       "value": 1.80 + 0.8 * up[-1], "source": "synthetic"}])
    rows = mf.rates_rows(store)
    by = {}
    for r in rows:
        by.setdefault(r["registry_key"], {})[r["observed_at"]] = r
    L = last.isoformat()

    for w in mf.ATTR_WINDOWS:
        d = by.get(f"calc.attr_d10y_{w}d", {}).get(L)
        check(d is not None and abs(d["value"] - 2.0 * w) < 1e-6,
              f"calc.attr_d10y_{w}d is the 10-year's {w}-observation move in bp "
              f"(+{2 * w}; got {d and d['value']})")
        rs = by.get(f"calc.attr_real_share_{w}d", {}).get(L)
        check(rs is not None and abs(rs["value"] - 0.8) < 1e-6,
              f"calc.attr_real_share_{w}d = Δreal/Δ10y = 0.8 "
              f"(got {rs and rs['value']})")
        cs = by.get(f"calc.attr_curve_share_{w}d", {}).get(L)
        check(cs is not None and abs(cs["value"] - 0.5) < 1e-6,
              f"calc.attr_curve_share_{w}d = Δ2y/Δ10y = 0.5 "
              f"(got {cs and cs['value']})")

    # THE FLOOR: on the flat stretch the move is written (it is 0) and no share is.
    quiet = {k for k, r in by.get("calc.attr_d10y_5d", {}).items()
             if abs(r["value"]) < mf.ATTR_MIN_MOVE_BP}
    check(bool(quiet), f"the flat stretch writes a 5-observation move below the "
                       f"{mf.ATTR_MIN_MOVE_BP:g}bp floor ({len(quiet)} days)")
    leaked = [k for k in quiet
              if k in by.get("calc.attr_real_share_5d", {})
              or k in by.get("calc.attr_curve_share_5d", {})]
    check(not leaked,
          f"and on none of those days is a share written -- a ratio over a "
          f"near-zero move is noise with a large number on it ({len(leaked)})")

    def instant(s):
        return dt.datetime.fromisoformat(s) if s else None
    rs = by.get("calc.attr_real_share_60d", {}).get(L) or {}
    check(instant(rs.get("available_at")) == instant(late_at),
          f"the share's available_at is its LATEST input's -- the late TIPS print, "
          f"{late_at} (got {rs.get('available_at')})")
    cs = by.get("calc.attr_curve_share_60d", {}).get(L) or {}
    check(bool(cs) and instant(cs["available_at"]) < instant(late_at),
          "while the curve share, which never read it, is not delayed by it")

    kw = by.get("calc.attr_kw_tp_share_60d", {}).get(L)
    check(kw is not None and abs(kw["value"] - 0.5) < 1e-6,
          f"calc.attr_kw_tp_share_60d = ΔTP_kw/Δ10y = 0.5 "
          f"(got {kw and kw['value']})")
    p = by.get("calc.attr_dkw_path_share_60d", {}).get(L)
    t = by.get("calc.attr_dkw_tp_share_60d", {}).get(L)
    check(p is not None and abs(p["value"] - 0.75) < 1e-6
          and t is not None and abs(t["value"] - 0.25) < 1e-6,
          f"DKW's path and premium shares of PATH + PREMIUM are 0.75 and 0.25, "
          f"with the liquidity leg moving as much as both -- it is out of the "
          f"denominator (got {p and p['value']}, {t and t['value']})")
    check(not by.get("calc.attr_acm_tp_share_60d"),
          "ACM, with no rows in the store, writes nothing -- an absent model is "
          "absent, not zero")

    # --- the stock-bond correlation, on returns built to be exactly opposite ----
    spy = [100.0]
    for i in range(1, n):
        spy.append(spy[-1] * math.exp(0.01 * math.sin(i * 1.7)))
    tlt = [100.0 * (100.0 / s) for s in spy]
    seed(store, "yfinance.mkt_spy", days, spy)
    seed(store, "yfinance.mkt_tlt", days, tlt)
    rows = mf.rates_rows(store)
    corr = [r for r in rows if r["registry_key"] == "calc.corr_spy_tlt_60d"]
    check(len(corr) == n - mf.CORR_WINDOW,
          f"the correlation starts once {mf.CORR_WINDOW} returns exist "
          f"({len(corr)} rows from {n} closes)")
    check(bool(corr) and all(abs(r["value"] + 1.0) < 1e-9 for r in corr),
          f"and reads -1 on returns that are exactly opposite "
          f"(last {corr and corr[-1]['value']})")
    tlt_rows = [r for r in rows if r["registry_key"] == "calc.corr_spy_tlt_60d"
                and r["observed_at"] == L]
    check(bool(tlt_rows) and tlt_rows[0]["available_at"][:10] == L,
          "and is dated and knowable on its window's last session")

    # --- inflation volatility: consecutive months only --------------------------
    months = []
    y, m = 2021, 1
    for _ in range(60):
        months.append(dt.date(y, m, 1))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    lv = [300.0]
    for i in range(1, len(months)):
        lv.append(lv[-1] * (1.002 if i % 2 else 1.004))
    seed(store, "fred.core_cpi", months, lv)
    iv = [r for r in mf.rates_rows(store) if r["registry_key"] == "calc.infl_vol"]
    moms = [((lv[i] / lv[i - 1]) ** 12 - 1) * 100 for i in range(1, len(lv))]
    want = statistics.stdev(moms[-mf.INFL_VOL_MONTHS:])
    check(len(iv) == len(moms) - mf.INFL_VOL_MONTHS + 1
          and abs(iv[-1]["value"] - want) < 1e-6,
          f"calc.infl_vol is the {mf.INFL_VOL_MONTHS}-month deviation of "
          f"annualised month-on-month core CPI ({iv and iv[-1]['value']:.4f} vs "
          f"{want:.4f}, {len(iv)} rows)")
    # A MISSING MONTH: every window spanning it is refused. With month 10 gone, the
    # first window clear of the gap is the 24 changes ending at month 35.
    gone = months[10]
    with tempfile.TemporaryDirectory() as td:
        s2 = observations.ObservationStore(str(Path(td) / "gap.db"))
        try:
            keep = [(d, v) for d, v in zip(months, lv) if d != gone]
            seed(s2, "fred.core_cpi", [d for d, _ in keep], [v for _, v in keep])
            iv2 = [r for r in mf.rates_rows(s2)
                   if r["registry_key"] == "calc.infl_vol"]
        finally:
            s2.close()
    first_clear = months[11 + mf.INFL_VOL_MONTHS].isoformat()
    check(len(iv2) == len(months) - (11 + mf.INFL_VOL_MONTHS)
          and all(r["observed_at"] >= first_clear for r in iv2),
          f"and with {gone} missing, no window that spans the gap is written: "
          f"{len(iv2)} rows, the first on {iv2 and iv2[0]['observed_at']} "
          f"(first clear window ends {first_clear})")

    # --- the registry agrees with the computation ------------------------------
    for key in sorted(mf.RATES_FEATURES):
        e = derived.registry_entry(key)
        check(bool(e) and e.get("units") and e.get("mechanism_group")
              and e.get("revision_policy") and e.get("information_half_life")
              and e.get("trigger_eligible") is False
              and e.get("observation_type") in ("calculated", "inferred"),
              f"{key}: registered with units, mechanism_group, revision_policy, "
              f"half-life; not trigger_eligible")


# ---------------------------------------------------------------------------
# L. THE RATES DRIVER (signal-triage ST-3)
# ---------------------------------------------------------------------------
def _drv_inputs(move=40.0, real=1.3, curve=1.2, path=0.8, prem=0.15,
                kw=10.0, acm=None, sffed=8.0, dkw=6.0, corr=0.3,
                ties=(None, None)) -> dict:
    def lv(x, metric="seeded"):
        return ({"metric": metric, "level": x, "observed_at": "2026-09-18"}
                if x is not None else
                {"metric": metric, "level": None,
                 "absent_reason": f"no observation for {metric} (seeded)"})
    primary = ({"model": "dkw", "path_share": path, "premium_share": prem,
                "observed_at": "2026-08-31"} if path is not None else
               {"model": "dkw", "path_share": None, "premium_share": None,
                "absent_reason": "DKW last observed 2026-04-30 (seeded)"})
    return {
        "move": lv(move, "calc.attr_d10y_60d"),
        "real_share": lv(real, "calc.attr_real_share_60d"),
        "curve_share": lv(curve, "calc.attr_curve_share_60d"),
        "primary": primary,
        "tie_breakers": [
            {"model": m, "premium_share": q,
             **({} if q is not None else {"absent_reason": f"{m} absent (seeded)"})}
            for m, q in zip(("kw", "acm"), ties)],
        "models": [{"name": n, "change_bp": c, "arbiter": n == "dkw",
                    **({} if c is not None else {"absent_reason": f"{n} absent"})}
                   for n, c in (("kw", kw), ("acm", acm), ("sffed", sffed),
                                ("dkw", dkw))],
        "evidence": [lv(corr, "calc.corr_spy_tlt_60d")],
    }


def group_l(store) -> None:
    print(f"\n{LINE}\nL. THE RATES DRIVER: FOUR CELLS, SYMMETRIC, DECLARED\n{LINE}")
    import inspect
    import re
    cfg_real = regime.load_config()
    spec = cfg_real["dimensions"]["rates"]["driver"]
    th = spec["thresholds"]
    und = spec["undecided_state"]
    cell = regime.driver_cell

    # --- the declaration -------------------------------------------------------
    rule_states = {r["state"] for side in spec["rules"].values() for r in side}
    check(set(spec["states"]) == rule_states | {und},
          f"the four declared cells are the rules' states plus the undecided one "
          f"({sorted(spec['states'])})")
    for k in ("share_min", "move_floor_bp", "be_flat_bp", "front_leading",
              "front_anchored", "sign_deadband_bp"):
        check(k in th, f"threshold {k} is declared in config ({th.get(k)})")
    metrics = (list(spec["inputs"].values())
               + [spec["decomposition"]["primary"]["path_share"],
                  spec["decomposition"]["primary"]["premium_share"]]
               + [t["premium_share"] for t in spec["decomposition"]["tie_breakers"]]
               + [m["metric"] for m in spec["models"]]
               + [e["metric"] for e in spec["evidence"]])
    unreg = [m for m in metrics if not derived.registry_entry(m)]
    check(not unreg, f"every metric the driver names is registered "
                     f"({len(metrics)} named; unregistered {unreg})")
    check(sum(bool(m.get("arbiter")) for m in spec["models"]) == 1
          and len(spec["models"]) == 4,
          "four term-premium models, exactly one of them the arbiter")
    rates_members = {m["metric"] for m in cfg_real["dimensions"]["rates"]["members"]}
    check(not (rates_members & set(metrics)),
          "and none of them is a member of the rates dimension, so the "
          "dimension's state, lists and confidence cannot move with the driver")
    body = re.sub(r'(?s)""".*?"""', "", (REPO / "regime.py").read_text(
        encoding="utf-8"))
    body = re.sub(r"#.*", "", body)
    named = [s for s in spec["states"] if re.search(rf"\b{s}\b", body)]
    check(not named, f"no driver cell name appears in regime.py's code -- the "
                     f"vocabulary is config ({named})")
    src = inspect.getsource(regime.driver_cell)
    check(not re.search(r"\b(store|derived|observations|session)\.", src),
          "driver_cell() is pure: it touches no store, no derived form, no clock")

    # --- the four cells, a selloff each ----------------------------------------
    r = cell(_drv_inputs(), spec)
    check(r["raw_state"] == "fed_path" and r["direction"] == "selloff",
          f"path share 0.80, breakevens down 12bp, front end leading (1.20): "
          f"fed_path in a selloff (got {r['raw_state']}, {r['direction']})")
    check(r["supporting"] == ["calc.corr_spy_tlt_60d"],
          "and a positive stock-bond correlation supports it")
    r = cell(_drv_inputs(real=0.9, corr=-0.2), spec)
    check(r["raw_state"] == "growth" and r["supporting"],
          f"breakevens +4bp (flat or with the move): growth, supported by a "
          f"negative correlation (got {r['raw_state']}, {r['supporting']})")
    r = cell(_drv_inputs(real=0.9, corr=0.3), spec)
    check(r["raw_state"] == "growth"
          and r["contradicting"] == ["calc.corr_spy_tlt_60d"],
          "and the same cell with a positive correlation lists it as "
          "contradicting -- evidence never decides the cell")
    r = cell(_drv_inputs(path=0.2, prem=0.7, curve=0.3), spec)
    check(r["raw_state"] == "term_premium",
          f"premium share 0.70 with the front end anchored (0.30): term_premium "
          f"(got {r['raw_state']})")
    r = cell(_drv_inputs(path=0.2, prem=0.7, curve=0.9), spec)
    check(r["raw_state"] == und and "anchored: no" in (r.get("undecided_reason") or ""),
          f"and with the front end NOT anchored it is {und}, the failed "
          f"condition named ({r.get('undecided_reason')})")
    r = cell(_drv_inputs(path=0.5, prem=0.4), spec)
    check(r["raw_state"] == und and r.get("undecided_reason"),
          f"neither share at 0.60: {und}, with the reason "
          f"({r.get('undecided_reason')})")
    r = cell(_drv_inputs(curve=0.8), spec)
    check(r["raw_state"] == und and "fed_path" in r["undecided_reason"]
          and "growth" in r["undecided_reason"],
          "path-driven with breakevens down but the front end not leading: "
          "undecided, and the reason names both rules that were tried")

    # --- symmetric -------------------------------------------------------------
    r = cell(_drv_inputs(move=-40.0, kw=-10, sffed=-8, dkw=-6), spec)
    check(r["raw_state"] == "fed_path" and r["direction"] == "rally",
          f"the mirror -- 10y -40bp, breakevens +12bp against it, 2y leading it "
          f"down: fed_path in a RALLY, the dovish reading (got {r['raw_state']}, "
          f"{r['direction']})")
    r = cell(_drv_inputs(move=-40.0, real=0.9, corr=-0.2, kw=-10, sffed=-8,
                         dkw=-6), spec)
    check(r["raw_state"] == "growth" and r["direction"] == "rally",
          f"and a growth rally: breakevens falling with the yield (got "
          f"{r['raw_state']}, {r['direction']})")

    # --- not determined ----------------------------------------------------------
    r = cell(_drv_inputs(move=10.0), spec)
    check(r["raw_state"] is None and r["direction"] is None
          and "move floor" in (r.get("not_determined_reason") or ""),
          f"|Δ10y| 10bp under the {th['move_floor_bp']}bp floor: NOT DETERMINED, "
          f"no cell and no direction ({r.get('not_determined_reason')})")
    r = cell(_drv_inputs(path=None), spec)
    check(r["raw_state"] is None
          and "no decomposition" in (r.get("not_determined_reason") or ""),
          f"no DKW split and no tie-breaker: not determined, each absence cited "
          f"({r.get('not_determined_reason')})")
    r = cell(_drv_inputs(real=None), spec)
    check(r["raw_state"] is None
          and "cannot be tested" in (r.get("not_determined_reason") or ""),
          "path-driven with the breakeven leg absent: not determined -- the "
          "shape is untested, which is not the same claim as mixed")

    # --- the models' signs -------------------------------------------------------
    r = cell(_drv_inputs(kw=-10.0), spec)
    check(r["raw_state"] == "fed_path" and "dkw (+1) arbitrates"
          in (r.get("arbitration") or "") and r["model_signs"]["kw"] == "-1",
          f"KW falls while SF Fed and DKW rise: the disagreement is SURFACED and "
          f"DKW arbitrates ({r.get('arbitration')})")
    check(r["model_signs"]["acm"] == "absent",
          "ACM with no reading is `absent` in the signs, not a vote either way")
    r = cell(_drv_inputs(kw=-10.0, dkw=None), spec)
    check(r["raw_state"] == und and "arbiter" in (r.get("undecided_reason") or ""),
          f"and with DKW unable to arbitrate the cell is {und} "
          f"({r.get('undecided_reason')})")
    r = cell(_drv_inputs(kw=-10.0, dkw=2.0), spec)
    check(r["raw_state"] == und,
          f"a DKW change inside the {th['sign_deadband_bp']}bp dead-band has no "
          f"sign, so it cannot arbitrate either")

    # --- tie-breakers -----------------------------------------------------------
    r = cell(_drv_inputs(path=None, ties=(0.7, None), curve=0.3), spec)
    check(r["raw_state"] == "term_premium" and r.get("decided_by") == "kw",
          f"DKW absent: Kim-Wright alone (premium share 0.70) decides, ACM's "
          f"absence noted (got {r['raw_state']}, by {r.get('decided_by')})")
    r = cell(_drv_inputs(path=None, ties=(0.7, 0.2)), spec)
    check(r["raw_state"] == und,
          f"and when KW and ACM disagree on the side, {und}")
    check(all(cell(_drv_inputs(**kw_), spec).get("trace")
              for kw_ in ({}, {"move": 1.0}, {"path": None})),
          "every outcome carries a trace, determined or not")

    # --- integration: the object, on a seeded store ------------------------------
    cfg = tiny_config(persistence=2)
    cfg["dimensions"]["rates"] = {
        "horizon": "1-3m", "states": ["high", "low"],
        "bands": [{"state": "high", "min_percentile": 50},
                  {"state": "low", "min_percentile": 0}],
        "members": [{"metric": "fred.yield_10y", "polarity": 1,
                     "because": "seeded"}],
        "driver": spec,
    }
    days = weekdays_back(END, 80)
    seed(store, "fred.vix", days, [15 + (i % 7) for i in range(80)])
    seed(store, "fred.bb_oas", days, [2.0] * 80)
    seed(store, "fred.hy_oas", days, [3.0 + 0.01 * i for i in range(80)])
    seed(store, "fred.yield_10y", days, [4.0 + 0.01 * i for i in range(80)])
    for k, v in (("calc.attr_d10y_60d", 40.0), ("calc.attr_real_share_60d", 1.3),
                 ("calc.attr_curve_share_60d", 1.2),
                 ("calc.attr_dkw_path_share_60d", 0.8),
                 ("calc.attr_dkw_tp_share_60d", 0.15),
                 ("calc.corr_spy_tlt_60d", 0.3)):
        seed(store, k, days, [v] * 80)
    for k, step in (("fred.term_premium_kw", 0.002), ("sffed.term_premium_10y", 0.002),
                    ("dkw.real_term_premium_10y", 0.002)):
        seed(store, k, days, [0.5 + step * i for i in range(80)])

    objs = [compute_at(store, cfg, d, 1 + i) for i, d in enumerate(days[-6:-3])]
    drv = objs[-1]["dimensions"]["rates"].get("driver") or {}
    check(drv.get("state") == "fed_path" and drv.get("trace"),
          f"on the object: dimensions.rates.driver publishes fed_path with its "
          f"trace (got {drv.get('state')}: {drv.get('trace')})")
    acm = next((m for m in drv.get("models") or [] if m["name"] == "acm"), {})
    check(acm.get("change_bp") is None and "no observation for "
          "acm.term_premium_10y knowable" in (acm.get("absent_reason") or ""),
          f"ACM, never written (G-33 on the box), is absent with a reason that "
          f"cites data ({acm.get('absent_reason')})")
    check(all(o["dimensions"]["rates"]["driver"].get("trace") for o in objs),
          "and every object carries the trace")

    # A ONE-SESSION FLIP DOES NOT MOVE THE PUBLISHED CELL; TWO DO. The flipped
    # share is a LATER VINTAGE of the session's row (21:05, inside the 21:30
    # cutoff): the store keeps both, and the as-of read takes the newer.
    def revise(day: dt.date, value: float) -> None:
        store.write_many([{
            "registry_key": "calc.attr_real_share_60d", "instrument": None,
            "observed_at": day.isoformat(),
            "available_at": dt.datetime(day.year, day.month, day.day, 21, 5,
                                        tzinfo=dt.timezone.utc).isoformat(),
            "value": value, "source": "synthetic"}])
    flip_day = days[-3]
    revise(flip_day, 0.9)
    o1 = compute_at(store, cfg, flip_day, 10)
    d1 = o1["dimensions"]["rates"]["driver"]
    check(d1.get("raw_state") == "growth" and d1.get("state") == "fed_path"
          and d1.get("pending_state") == "growth",
          f"one session reading growth: published stays fed_path, growth pending "
          f"({d1.get('persistence')})")
    revise(days[-2], 0.9)
    o2 = compute_at(store, cfg, days[-2], 11)
    d2 = o2["dimensions"]["rates"]["driver"]
    check(d2.get("state") == "growth"
          and d2.get("since") == days[-2].isoformat(),
          f"the second consecutive session publishes growth, dated "
          f"({d2.get('persistence')})")

    # THE IDENTITY: the object without the driver is the object with it, less it.
    import copy
    bare = copy.deepcopy(cfg)
    bare["dimensions"]["rates"].pop("driver")
    stamp = "2026-09-19T12:00:00+00:00"
    cut = regime.session_cutoff(days[-1].isoformat())
    with_d = regime.compute(as_of=cut, session_day=days[-1].isoformat(),
                            store=store, cfg=cfg, computed_at=stamp)
    without = regime.compute(as_of=cut, session_day=days[-1].isoformat(),
                             store=store, cfg=bare, computed_at=stamp)
    a = copy.deepcopy(regime.replay_fields(with_d))
    b = copy.deepcopy(regime.replay_fields(without))
    a["dimensions"]["rates"].pop("driver", None)
    diffs = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
    check(not diffs,
          f"with and without the driver the object is identical in every other "
          f"field -- dimensions, dials, contradictions, exceptions (differing: "
          f"{diffs})")
    check(regime.exception_ids(with_d) == regime.exception_ids(without),
          "and the exception list the heartbeat reads is the same list")
    check("driver:" in regime.format_object(with_d),
          "`regime show` prints the driver line")

    # STALE DKW FALLS BACK TO THE TIE-BREAKERS, and says why.
    with tempfile.TemporaryDirectory() as td:
        s2 = observations.ObservationStore(str(Path(td) / "stale.db"))
        try:
            long = weekdays_back(END, 140)
            for k, v in (("calc.attr_d10y_60d", 40.0),
                         ("calc.attr_real_share_60d", 0.9),
                         ("calc.attr_curve_share_60d", 0.3),
                         ("calc.attr_kw_tp_share_60d", 0.2)):
                seed(s2, k, long, [v] * 140)
            seed(s2, "calc.attr_dkw_path_share_60d", long[:40], [0.1] * 40)
            seed(s2, "calc.attr_dkw_tp_share_60d", long[:40], [0.8] * 40)
            seed(s2, "fred.yield_10y", long, [4.0 + 0.01 * i for i in range(140)])
            d3 = regime.rates_driver(spec, regime.session_cutoff(END.isoformat()),
                                     {"staleness_multiple": 2}, s2)
        finally:
            s2.close()
    prim = (d3.get("decomposition") or {}).get("primary") or {}
    check("last observed" in (prim.get("absent_reason") or "")
          and d3.get("raw_state") == "growth" and d3.get("decided_by") == "kw",
          f"DKW last written ~100 sessions back is STALE, with its age in the "
          f"reason; Kim-Wright's path share (0.80) decides growth "
          f"(got {d3.get('raw_state')} by {d3.get('decided_by')}; "
          f"{prim.get('absent_reason')})")

    # --- the one-regime rule, statically -----------------------------------------
    import subprocess
    tracked = subprocess.run(["git", "ls-files", "*.py"], cwd=REPO,
                             capture_output=True, text=True).stdout.split()
    tracked += [p.relative_to(REPO).as_posix()
                for p in (REPO / "tools" / "calibration").glob("*.py")]
    offenders = []
    for rel in sorted(set(tracked)):
        # altdata/report/ is vendored CONTENT, not a pipeline: nothing imports it
        # (CLAUDE.md), and its "fed_path" is a positioning-lens label.
        if (rel in ("regime.py", "tools/validate_regime.py")
                or rel.startswith("altdata/report/")):
            continue
        p = REPO / rel
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        # fed_path, not term_premium: the second is also an ordinary series name
        # (acm.term_premium_10y) and the vendored report content uses it as one.
        if re.search(r"""['"]fed_path['"]""", t):
            if rel.startswith("tools/calibration/") and "driver_cell" in t:
                continue
            offenders.append(rel)
    check(not offenders,
          f"no module outside regime.py names a driver cell -- the one place a "
          f"cell is computed is driver_cell(); calibration may only import it "
          f"({offenders})")
    cal = sorted((REPO / "tools" / "calibration").glob("*.py"))
    opens = [p.name for p in cal
             if re.search(r"ObservationStore|from altdata import .*observations|"
                          r"derived_forms|regime\.(compute|latest|rates_driver)",
                          p.read_text(encoding="utf-8"))]
    check(not opens,
          f"no calibration script opens the store or computes an object "
          f"({len(cal)} script(s) checked; offenders {opens})")


def main() -> int:
    print(f"{LINE}\nThe market-state object and the contradiction table\n{LINE}")
    group_a()
    group_c()
    for g in (group_b, group_d, group_e, group_f, group_f2, group_g,
              group_h, group_i, group_j, group_k, group_l):
        with tempfile.TemporaryDirectory() as td:
            store = observations.ObservationStore(str(Path(td) / "regime.db"))
            try:
                g(store)
            except Exception as exc:                       # noqa: BLE001
                bad(f"{g.__name__} raised {type(exc).__name__}: {exc}")
            finally:
                store.close()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
