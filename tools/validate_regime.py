"""
Validation gate for the market-state object and the contradiction table.

The object is the only regime in the system, so the things that could go wrong
with it are not cosmetic: a leak makes every backfilled state a hindsight state, a
non-deterministic compute makes a stored object unreplayable, an undeclared rule
puts a threshold back in code, and an empty `contradicting` turns "we looked and
everything agreed" into "nobody looked".

  A  EXACT REPLAY. A stored object, recomputed from the store at its own cutoff and
     its own compute instant, must equal the stored version field for field --
     every number it asserts about the market. Provenance (computed_at,
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
            "vol": {"primary": "fred.vix",
                    "level_bands": [{"state": "elevated", "min_level": 20},
                                    {"state": "normal", "min_level": 0}],
                    "realized_implied": {"metric": "mkt_spy"},
                    "term_structure": {"requires_store_keys": ["cfe.vx1"]}},
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
        all_rows = list(store.as_of(regime.STORE_KEY))
        # ONLY OBJECTS COMPUTED UNDER THE CURRENT RULES CAN BE REPLAYED.
        #
        # A stored object records its config_version. When the config changes on
        # purpose -- a dimension given new members, a contradiction pair pointed at
        # a different series -- every older object legitimately recomputes to
        # something else, and failing on that would mean the gate cannot tell "the
        # rules changed" from "the arithmetic broke". Those are the two things it
        # exists to distinguish, so superseded objects are REPORTED and skipped.
        rows = [r for r in all_rows
                if (json.loads(r["value_text"]).get("config_version") == current)]
        superseded = len(all_rows) - len(rows)
        check(bool(all_rows), f"the store holds market_state objects "
                              f"({len(all_rows)})")
        if superseded:
            print(f"        {superseded} object(s) were computed under an earlier "
                  f"config version and are not replayed against {current}; "
                  f"re-run `regime backfill` to bring them forward")
        check(bool(rows),
              f"and {len(rows)} of them were computed under the current config "
              f"{current!r}, so there is something to replay. A store where EVERY "
              f"object is superseded is a store whose history no longer matches "
              f"its own rules")
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

    pairs = (cfg.get("contradictions") or {}).get("pairs") or []
    check(len(pairs) == 7,
          f"seven contradiction rows are declared -- six computed and the "
          f"reserved prediction-markets pair (got {len(pairs)})")
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
    ts = stale["dials"]["vol"].get("term_structure") or {}
    check(ts.get("state") is None and "cfe.vx1" in str(ts.get("absent_reason")),
          "the term-structure leg reports the store keys it needs rather than "
          "being approximated from something else")


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


def main() -> int:
    print(f"{LINE}\nThe market-state object and the contradiction table\n{LINE}")
    group_a()
    group_c()
    for g in (group_b, group_d, group_e, group_f, group_f2, group_g,
              group_h):
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
