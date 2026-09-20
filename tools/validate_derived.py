"""
Validation gate for the standard derived forms.

SEEDED, not sampled. Every series here is written into a throwaway store with
values whose percentile, z-score and deltas were computed by hand, so this gate
tests the arithmetic rather than agreeing with it. A validator that reads the
production store can only assert that the code is self-consistent, which is the
one thing a bug is too.

  A  KNOWN PERCENTILE AND Z. A 1..100 ramp: every figure is hand-checked.
  B  THE WINDOW IS APPLIED. The same series read over 5y and over 30d must give
     DIFFERENT answers, and both must match the hand computation. This is the
     check that fails if `window` is ever accepted and ignored -- which is the
     likeliest way this function breaks, because ignoring it still returns a
     plausible number.
  C  NO FUTURE LEAK. An observation whose available_at is after the cutoff must
     not change the result by so much as a rounding digit. Asserted by comparing
     the whole dict before and after writing a wildly out-of-range future row.
  D  DELTA SEMANTICS COME FROM `units`. A yield moves in bps, a price in
     percent, a count raw -- resolved through the REAL registry, including the
     bulk import that owns the 59 FRED series.
  E  A DELTA WITH NO MEASUREMENT IS None, NOT ZERO. A monthly series has no
     1-session change; zero would claim it was measured and did not move.
  F  CONFIDENCE IS DERIVED. Fresh and ample reads high, very stale reads low,
     and there is no argument that sets it.

    python tools/validate_derived.py
"""

from __future__ import annotations

import datetime as dt
import statistics
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import derived, observations  # noqa: E402

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


def near(a, b, tol=1e-6) -> bool:
    if a is None or b is None:
        return a is b
    return abs(float(a) - float(b)) <= tol


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------
def weekdays_back(end: dt.date, n: int) -> list[dt.date]:
    """n weekdays ending at `end`, oldest first."""
    out: list[dt.date] = []
    day = end
    while len(out) < n:
        if day.weekday() < 5:
            out.append(day)
        day -= dt.timedelta(days=1)
    return list(reversed(out))


def seed(store, key: str, days: list[dt.date], values: list[float],
         available_offset_days: int = 0) -> None:
    rows = []
    for d, v in zip(days, values):
        avail = dt.datetime(d.year, d.month, d.day, 21, 0,
                            tzinfo=dt.timezone.utc) + dt.timedelta(
                                days=available_offset_days)
        rows.append({"registry_key": key, "instrument": None,
                     "observed_at": d.isoformat(),
                     "available_at": avail.isoformat(),
                     "value": float(v), "source": "synthetic"})
    store.write_many(rows)


# 2026-09-18 is a Friday and a real trading session; every case is cut off the
# evening of it so the calendar is the one the system actually runs on.
AS_OF = "2026-09-18T21:30:00+00:00"
END = dt.date(2026, 9, 18)


def group_a(store) -> None:
    print(f"{LINE}\nA. KNOWN PERCENTILE AND Z, HAND-CHECKED\n{LINE}")
    days = weekdays_back(END, 100)
    seed(store, "fred.hy_oas", days, [float(i) for i in range(1, 101)])
    d = derived.derived_forms("fred.hy_oas", AS_OF, store=store)

    check(d["n"] == 100, f"n is the 100 seeded observations (got {d['n']})")
    check(near(d["level"], 100.0), f"level is the newest value (got {d['level']})")
    # Every value <= 100, so 100/100.
    check(near(d["percentile"], 100.0),
          f"percentile of the series maximum is 100 (got {d['percentile']})")
    sd = statistics.stdev([float(i) for i in range(1, 101)])
    want_z = round((100.0 - 50.5) / sd, 4)
    check(near(d["z_score"], want_z, 1e-4),
          f"z of the maximum is (100-50.5)/{sd:.4f} = {want_z} "
          f"(got {d['z_score']})")
    check(d["extreme"] is True,
          "and the series maximum is flagged extreme (percentile >= 95)")

    # The midpoint, asked as of its own day: 50 values at or below 50.
    mid_as_of = dt.datetime(days[49].year, days[49].month, days[49].day, 22,
                            tzinfo=dt.timezone.utc).isoformat()
    m = derived.derived_forms("fred.hy_oas", mid_as_of, store=store)
    check(m["n"] == 50 and near(m["percentile"], 100.0),
          f"asked mid-series the answer uses only what existed then "
          f"(n={m['n']}, percentile={m['percentile']})")


def group_b(store) -> None:
    print(f"\n{LINE}\nB. THE WINDOW IS APPLIED\n{LINE}")
    # A ramp from 1..100 again, but read over two windows. Over 5y the level is
    # the maximum of all 100; over 30 CALENDAR days only the last ~21 weekdays
    # are in scope, and the level is still the maximum of those -- so the
    # percentile agrees but n MUST NOT.
    wide = derived.derived_forms("fred.hy_oas", AS_OF, store=store)
    narrow = derived.derived_forms("fred.hy_oas", AS_OF, window=30, store=store)
    check(wide["n"] > narrow["n"],
          f"a 30-day window sees fewer observations than 5y "
          f"({narrow['n']} < {wide['n']})")
    check(narrow["window_requested_days"] == 30,
          "the requested window is reported back")
    check(narrow["window_actual_days"] <= 30,
          f"and window_actual_days respects it ({narrow['window_actual_days']})")

    # Now the case that actually catches an ignored window: a series whose
    # RECENT history is calm and whose distant history is extreme. Over 5y the
    # level sits mid-distribution; over 30 days it is the maximum.
    days = weekdays_back(END, 300)
    vals = [100.0] * 279 + [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0,
                            11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0,
                            19.0, 20.0, 21.0]
    seed(store, "fred.ig_oas", days, vals)
    w = derived.derived_forms("fred.ig_oas", AS_OF, store=store)
    n30 = derived.derived_forms("fred.ig_oas", AS_OF, window=30, store=store)
    check(w["percentile"] is not None and n30["percentile"] is not None
          and abs(w["percentile"] - n30["percentile"]) > 20,
          f"the two windows disagree by design -- 5y reads "
          f"{w['percentile']}, 30d reads {n30['percentile']}. A function that "
          f"accepted `window` and ignored it would return the same number "
          f"twice and pass every other check in this file")
    # HAND-CHECKED, and the first attempt at this number was wrong in a way
    # worth keeping: 30 calendar days back from Friday 18 Sep reaches 19 Aug,
    # which holds 23 weekdays -- the 21 ramp values AND the last two 100s. So
    # the level 21 has 21 of 23 values at or below it, not 21 of 21.
    check(n30["n"] == 23,
          f"the 30-day window holds 23 weekdays (got {n30['n']})")
    check(near(n30["percentile"], round(100.0 * 21 / 23, 4)),
          f"and its percentile is the hand-computed 21/23 = "
          f"{round(100.0 * 21 / 23, 4)} (got {n30['percentile']})")
    check(near(w["percentile"], 7.0),
          f"while the 5y figure is the hand-computed 7.0 -- 21 of 300 values "
          f"at or below 21 (got {w['percentile']})")


def group_c(store) -> None:
    print(f"\n{LINE}\nC. NO FUTURE LEAK\n{LINE}")
    before = derived.derived_forms("fred.hy_oas", AS_OF, store=store)

    # An observation dated INSIDE the window but knowable only afterwards. This
    # is the shape that leaks: a FRED revision to an old period, published next
    # week. Filtering on observed_at would let it through.
    leak_day = END - dt.timedelta(days=3)
    store.write_many([{
        "registry_key": "fred.hy_oas", "instrument": None,
        "observed_at": leak_day.isoformat(),
        "available_at": "2026-09-25T12:00:00+00:00",   # a week after the cutoff
        "value": 999999.0, "source": "synthetic"}])
    after = derived.derived_forms("fred.hy_oas", AS_OF, store=store)
    check(before == after,
          "an observation whose available_at is after the cutoff changes "
          "nothing -- not the level, not n, not the percentile, not a rounding "
          "digit")

    # And it IS visible once the cutoff moves past it, or the check above would
    # pass just as well on a store that dropped the row entirely.
    #
    # IT ARRIVES AS A REVISION, NOT AS A NEW PERIOD. The leak row shares its
    # observed_at with an observation already in the series, which is the shape a
    # FRED restatement actually has -- so n does NOT grow; the value for that one
    # period changes and the distribution moves with it. Asserting n+1 here was
    # wrong about the store, not about the store being wrong.
    later = derived.derived_forms("fred.hy_oas", "2026-09-26T12:00:00+00:00",
                                  store=store)
    check(later["n"] == before["n"],
          f"the revision replaces its period rather than adding one "
          f"({before['n']} -> {later['n']})")
    check(later["percentile"] != before["percentile"]
          or later["z_score"] != before["z_score"],
          f"but it IS seen once the cutoff passes its available_at -- the "
          f"distribution moves (z {before['z_score']} -> {later['z_score']}), "
          f"so C tests the as-of join and not a lost write")


def group_d(store) -> None:
    print(f"\n{LINE}\nD. DELTA SEMANTICS COME FROM `units`\n{LINE}")
    days = weekdays_back(END, 60)

    # fred.hy_oas: units '%' -> bps. 2.70 -> 2.72 is +2bp.
    seed(store, "fred.bb_oas", days, [2.70] * 59 + [2.72])
    d = derived.derived_forms("fred.bb_oas", AS_OF, store=store)
    check(d["delta_unit"] == "bps" and "units '%'" in d["delta_unit_reason"],
          f"a spread quoted in percent moves in bps ({d['delta_unit']}, "
          f"{d['delta_unit_reason']})")
    check(near(d["delta_5d"], 2.0),
          f"and 2.70 -> 2.72 is +2.0 bp, not +0.02 (got {d['delta_5d']})")

    # fred.wti: units '$' -> percent. 100 -> 101 is +1%.
    seed(store, "fred.wti", days, [100.0] * 59 + [101.0])
    w = derived.derived_forms("fred.wti", AS_OF, store=store)
    check(w["delta_unit"] == "percent",
          f"a price moves in percent ({w['delta_unit']})")
    check(near(w["delta_5d"], 1.0),
          f"and 100 -> 101 is +1.0 percent, not +1.0 raw (got {w['delta_5d']})")

    # fred.claims_4wk: units 'K' -> raw. 221000 -> 229000 is +8000.
    seed(store, "fred.claims_4wk", days, [221000.0] * 59 + [229000.0])
    c = derived.derived_forms("fred.claims_4wk", AS_OF, store=store)
    check(c["delta_unit"] == "raw", f"a count moves raw ({c['delta_unit']})")
    check(near(c["delta_5d"], 8000.0),
          f"and 221000 -> 229000 is +8000 (got {c['delta_5d']})")

    check(all(x["rate_of_change_basis"] for x in (d, w, c)),
          "each rate_of_change names the delta and span it came from")
    check(near(d["rate_of_change"], d["delta_20d"] / 20.0),
          "and is that delta divided by its sessions")

    u = derived.derived_forms("nosuch.metric", AS_OF, store=store)
    check(u["delta_unit"] == "raw" and "no registry entry" in
          u["delta_unit_reason"],
          "an unregistered metric is raw AND SAYS SO -- a silent default here "
          "is the delta rule failing without a trace")


def group_e(store) -> None:
    print(f"\n{LINE}\nE. A DELTA WITH NO MEASUREMENT IS None\n{LINE}")
    # Month-ends only, the shape of a monthly macro series.
    monthly = [dt.date(2026, m, 1) for m in range(1, 10)]
    seed(store, "fred.core_pce", monthly, [120.0 + m for m in range(9)])
    d = derived.derived_forms("fred.core_pce", AS_OF, store=store)
    check(d["delta_1d"] is None,
          "a monthly series has no 1-session change, and reports None")
    check(d["delta_1d"] != 0 and d["delta_1d"] is not 0,  # noqa: F632
          "and NOT zero, which would claim it was measured and did not move")
    check(d["delta_20d"] is not None,
          f"while its 20-session change IS measured ({d['delta_20d']})")
    check(d["staleness_allowance_sessions"] == derived.FREQ_SESSIONS["monthly"],
          f"and its staleness allowance is the monthly cadence, not the daily "
          f"one ({d['staleness_allowance_sessions']} sessions)")


def group_f(store) -> None:
    print(f"\n{LINE}\nF. CONFIDENCE IS DERIVED, NEVER AUTHORED\n{LINE}")
    import inspect
    sig = inspect.signature(derived.derived_forms)
    check("confidence" not in sig.parameters,
          "derived_forms() has no confidence argument -- a confidence an "
          "author can set reports what the author hoped")

    days = weekdays_back(END, 400)
    seed(store, "fred.yield_10y", days, [4.0 + (i % 7) * 0.01
                                        for i in range(400)])
    fresh = derived.derived_forms("fred.yield_10y", AS_OF, store=store)
    check(fresh["confidence"] == "high",
          f"fresh and ample reads high ({fresh['confidence']}: "
          f"{fresh['confidence_reason']})")

    # The same series, asked four months later: nothing has been written since.
    old = derived.derived_forms("fred.yield_10y", "2027-01-18T21:00:00+00:00",
                                store=store)
    check(old["confidence"] == "low" and "very stale" in old["confidence_reason"],
          f"the same series four months on reads low ({old['confidence']}: "
          f"{old['confidence_reason']})")

    thin_days = weekdays_back(END, 5)
    seed(store, "fred.natgas", thin_days, [3.0, 3.1, 3.2, 3.3, 3.4])
    thin = derived.derived_forms("fred.natgas", AS_OF, store=store)
    check(thin["confidence"] == "low" and str(derived.N_THIN) in
          thin["confidence_reason"],
          f"fresh but n=5 reads low ({thin['confidence_reason']})")

    check(fresh["session_basis"] == "same_session",
          f"a level observed on the cutoff day reports zero distance as its own "
          f"basis ({fresh['session_basis']}), not as a counting method")
    check(old["session_basis"] in ("calendar", "weekdays", "mixed"),
          f"and a row with real distance stamps HOW its sessions were counted "
          f"({old['session_basis']}) -- the holiday calendar covers 2026-2027 "
          f"only, so a backfill into 2023 must say which basis it used")

    # The basis matters because the fallback is reachable from the real store,
    # whose history starts in 2022.
    n, basis = derived.sessions_between("2023-03-01", "2023-03-31")
    check(basis == "weekdays" and n == 22,
          f"a span entirely outside the calendar counts weekdays and says so "
          f"({n} sessions, basis {basis})")


def main() -> int:
    print(f"{LINE}\nStandard derived forms -- seeded cases\n{LINE}")
    with tempfile.TemporaryDirectory() as td:
        path = str(Path(td) / "derived_test.db")
        store = observations.ObservationStore(path)
        try:
            for g in (group_a, group_b, group_c, group_d, group_e, group_f):
                try:
                    g(store)
                except Exception as exc:          # a raising gate is a failure
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
