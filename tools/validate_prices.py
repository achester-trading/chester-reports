"""
Validation gate for the price feed: the parser, and the availability rule.

NO NETWORK. The parser is proven against a SAVED FIXTURE --
tests/fixtures/yfinance_spy_history.csv, a real seven-row slice of yfinance's own
output that contains a real dividend. A feed test that fetches is a test that fails
when Yahoo is slow, and a test that fails for reasons outside the commit is a test
people stop reading.

  A  THE PARSER READS THE RIGHT COLUMN. `Close`, not `Adj Close` -- and the
     fixture is chosen so the two DIFFER, which is the only way to prove it. A
     dividend-adjusted close restates its own history every quarter and would
     disagree with the pin log, the exposure engine's spot and every decision's
     reference price.
  B  A ZERO DIVIDEND IS NOT AN EVENT. yfinance emits 0.0 on every ordinary day.
  C  A MISSING VALUE IS NOT A ZERO. A NaN close is dropped, not stored as 0.
  D  THE BASKET IS DECLARED AND REGISTERED. 28 symbols, the eleven sectors and
     RSP among them, every one resolving to a registry entry through the bulk
     block -- because a metric with no entry has no delta semantics and no
     revision policy.
  E  THE RECONSTRUCTION RULE BITES. A price series may have its availability
     reconstructed; a REVISABLE series may not, and the backfill refuses it. This
     is asserted rather than trusted: the rule is the one thing standing between a
     backfill and a leak no as-of join can catch.
  F  THE RECONSTRUCTED CLOCK IS THE SESSION CLOSE, IN THE RIGHT ZONE. 16:00 ET
     plus the declared latency, which is a different UTC hour in summer and
     winter -- a fixed offset would put half the year's availabilities an hour
     before the close they describe.
  G  A RE-READ OF AN IDENTICAL VALUE IS NOT A REVISION. A second pull of unchanged
     data writes ZERO rows; a changed value still writes its vintage; and a reader
     at an earlier cutoff still sees the original. This is the rule whose absence
     made two dimensions read 514 sessions stale on a store that was complete.
  H  NO BAR ON A NON-SESSION DATE. yfinance served VIX closes on Memorial Day and
     Labor Day; the index does not exist when the options market is shut. Continuous
     instruments are exempt by DECLARATION -- Bitcoin, and nothing else.

    python tools/validate_prices.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import backfill_prices as bp                                  # noqa: E402
from altdata import derived, observations                     # noqa: E402
from altdata.sources import yfinance_source as yf_src         # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FIXTURE = REPO / "tests" / "fixtures" / "yfinance_spy_history.csv"

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


def fixture_rows() -> list[dict]:
    with FIXTURE.open(encoding="utf-8", newline="") as fp:
        return list(csv.DictReader(fp))


def group_a() -> None:
    print(f"{LINE}\nA. THE PARSER READS `Close`, NOT `Adj Close`\n{LINE}")
    check(FIXTURE.is_file(), f"{FIXTURE.relative_to(REPO)} exists")
    rows = fixture_rows()
    check(len(rows) == 7, f"the fixture holds 7 rows (got {len(rows)})")
    for col in ("Close", "Adj Close", "Dividends", "Stock Splits"):
        check(col in rows[0], f"and carries the {col!r} column")

    parsed = yf_src.parse_rows(rows)
    closes = dict(parsed["closes"])
    check(len(closes) == 7, f"7 closes parsed (got {len(closes)})")

    # The dividend day is the one where Close and Adj Close diverge in the
    # fixture, which is what makes this check able to fail.
    differ = [r for r in rows
              if abs(float(r["Close"]) - float(r["Adj Close"])) > 1e-9]
    check(bool(differ),
          f"the fixture contains rows where Close and Adj Close DIFFER "
          f"({len(differ)} of {len(rows)}) -- without that this check could not "
          f"tell the two columns apart")
    for r in differ:
        day = r["Date"][:10]
        got = closes.get(day)
        want, adj = float(r["Close"]), float(r["Adj Close"])
        check(got is not None and abs(got - want) < 1e-9,
              f"{day}: parsed {got} = Close {want}, not Adj Close {adj}")

    src = (REPO / "altdata" / "sources" / "yfinance_source.py").read_text(
        encoding="utf-8")
    check("auto_adjust=False" in src,
          "and the fetch asks for auto_adjust=False, so the frame the parser "
          "sees has an unadjusted Close to read")
    check("Adj Close" not in src,
          "the module never names Adj Close -- there is no path by which the "
          "adjusted series reaches the store")


def group_b() -> None:
    print(f"\n{LINE}\nB. A ZERO DIVIDEND IS NOT AN EVENT\n{LINE}")
    rows = fixture_rows()
    parsed = yf_src.parse_rows(rows)
    zeros = [r for r in rows if float(r["Dividends"] or 0) == 0]
    nonzero = [r for r in rows if float(r["Dividends"] or 0) != 0]
    check(len(zeros) == 6 and len(nonzero) == 1,
          f"the fixture holds {len(zeros)} zero-dividend days and "
          f"{len(nonzero)} real one")
    check(len(parsed["dividends"]) == 1,
          f"exactly one dividend row is produced (got "
          f"{len(parsed['dividends'])}) -- storing the zeros would be 250 rows a "
          f"year per symbol asserting that nothing happened")
    d_day, d_val = parsed["dividends"][0]
    check(d_day == nonzero[0]["Date"][:10]
          and abs(d_val - float(nonzero[0]["Dividends"])) < 1e-9,
          f"and it is the real one: {d_day} = {d_val}")
    check(parsed["splits"] == [],
          f"no split rows, the fixture containing none (got {parsed['splits']})")


def group_c() -> None:
    print(f"\n{LINE}\nC. A MISSING VALUE IS NOT A ZERO\n{LINE}")
    rows = [
        {"Date": "2026-09-01", "Close": "100.0", "Dividends": "0", "Stock Splits": "0"},
        {"Date": "2026-09-02", "Close": "nan", "Dividends": "0", "Stock Splits": "0"},
        {"Date": "2026-09-03", "Close": "", "Dividends": "0", "Stock Splits": "0"},
        {"Date": "2026-09-04", "Close": "102.0", "Dividends": "nan", "Stock Splits": "2.0"},
        {"Date": "", "Close": "999.0", "Dividends": "0", "Stock Splits": "0"},
    ]
    p = yf_src.parse_rows(rows)
    days = [d for d, _ in p["closes"]]
    check(days == ["2026-09-01", "2026-09-04"],
          f"a NaN close and an empty close are DROPPED, not stored as zero "
          f"(kept {days})")
    check(p["dividends"] == [],
          "a NaN dividend is not an event either")
    check(p["splits"] == [("2026-09-04", 2.0)],
          f"a real split is kept (got {p['splits']})")
    check(all(d for d, _ in p["closes"]),
          "and a row with no date is skipped rather than keyed on an empty "
          "string")


def group_d_backfill() -> None:
    """The backfill's two refusals: a revisable series, and a running session."""
    print(f"\n{LINE}\nD2. THE BACKFILL REFUSES WHAT IT CANNOT DATE\n{LINE}")
    import importlib
    bf = importlib.import_module("tools.backfill_prices")

    cutoff = "2026-09-22"
    rows = [("2026-09-21", 1.0), ("2026-09-22", 2.0), ("2026-09-23", 3.0)]
    kept, dropped = bf.drop_incomplete_sessions(rows, cutoff)
    check([d for d, _ in kept] == ["2026-09-21", "2026-09-22"],
          "a bar dated after the last completed session is dropped -- it carries "
          "the last trade, not the close, and a reconstructed availability would "
          "stamp it as knowable this evening")
    check(dropped == ["2026-09-23"],
          "and the dropped date is returned so the count can be printed rather "
          "than absorbed")
    kept2, dropped2 = bf.drop_incomplete_sessions(rows, "2026-09-23")
    check(len(kept2) == 3 and not dropped2,
          "and nothing is dropped once the session has closed")

    ok, why = bf.reconstructable("fred.payems")
    check(not ok, f"a revisable series is still refused ({why[:60]}...)")
    ok, why = bf.reconstructable("yfinance.mkt_gspc")
    check(ok, f"and the new index series is reconstructable ({why})")


def group_d() -> None:
    print(f"\n{LINE}\nD. THE BASKET IS DECLARED AND REGISTERED\n{LINE}")
    syms = yf_src.SYMBOLS
    check(len(syms) == 40, f"40 symbols declared (got {len(syms)}) -- 31, plus "
          f"ST-2's nine")
    check("^VIX" in syms and "^VIX3M" in syms,
          "the volatility indices are in the basket -- FRED's VIXCLS arrives the "
          "next morning, so a 16:45 object computed from it reads yesterday's "
          "volatility")
    # THE LONG HISTORY IS THE INDEX, NOT THE FUND, and the gate says so because
    # substituting SPY is the tempting mistake: a base-rate distribution built on
    # SPY cannot contain 1929, 1937, 1973 or 1987, which are four of the episodes
    # it exists to carry.
    check("^GSPC" in syms,
          "^GSPC is in the basket -- the base rates need a century, and SPY began "
          "trading in 1993")
    check(yf_src.SYMBOLS.get("^GSPC") == "mkt_gspc",
          "and it keys to yfinance.mkt_gspc")
    check("RSP" in syms,
          "RSP is in the basket -- its absence was one of the two reasons "
          "breadth could not be computed at all")
    check(len(yf_src.SECTOR_KEYS) == 11,
          f"the eleven SPDR sectors are named as a group "
          f"({len(yf_src.SECTOR_KEYS)})")
    missing = [k for k in yf_src.SECTOR_KEYS if k not in syms.values()]
    check(not missing, f"and every one is in the basket ({missing or 'all present'})")

    unregistered = []
    for key in syms.values():
        for suffix in ("", yf_src.DIVIDEND_SUFFIX, yf_src.SPLIT_SUFFIX):
            mid = f"yfinance.{key}{suffix}"
            if not derived.registry_entry(mid):
                unregistered.append(mid)
    check(not unregistered,
          f"every close, dividend and split series resolves to a registry entry "
          f"through the bulk block ({len(syms) * 3} series"
          + (f"; unregistered: {unregistered[:4]}" if unregistered else "") + ")")

    e = derived.registry_entry("yfinance.mkt_spy")
    check(e.get("units") == "price" and
          derived.delta_unit_for("yfinance.mkt_spy")[0] == "percent",
          f"a close is units 'price', so its delta is in PERCENT "
          f"({derived.delta_unit_for('yfinance.mkt_spy')})")
    check(e.get("revision_policy") == "split_only",
          f"and its revision_policy is split_only, not never -- a split does "
          f"restate the history, legitimately and rarely "
          f"({e.get('revision_policy')})")


def group_e() -> None:
    print(f"\n{LINE}\nE. THE RECONSTRUCTION RULE BITES\n{LINE}")
    allowed, why = bp.reconstructable("yfinance.mkt_spy")
    check(allowed, f"a price series may be reconstructed ({why})")

    for revisable in ("fred.hy_oas", "fred.vix", "fred.claims_4wk"):
        allowed, why = bp.reconstructable(revisable)
        check(not allowed,
              f"{revisable} is REFUSED -- it is revisable, and stamping 'known "
              f"at the release' on what may be a third revision is a leak no "
              f"as-of join can catch")
    check("ALFRED" in bp.reconstructable("fred.hy_oas")[1],
          "and the refusal says what a revisable series needs instead")

    allowed, why = bp.reconstructable("yfinance.nosuch_series")
    check(not allowed and "no registry entry" in why,
          "an unregistered metric is refused too: an unknown policy is not a "
          "reconstructable one")

    # The refusal must happen in the BACKFILL, not merely in a helper nobody
    # calls. Run it against a revisable metric and assert nothing is written.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        db = observations.ObservationStore(str(Path(td) / "p.db"))
        try:
            r = bp.backfill({"HYOAS": "hy_oas_not_a_price"}, years=1,
                            dry_run=False, store=db)
            check(r["written"] == 0 and len(r["refused"]) == 1,
                  f"backfill() refuses an unreconstructable metric and writes "
                  f"nothing ({r['written']} rows, {len(r['refused'])} refused)")
            check(db.count() == 0,
                  f"and the store is untouched ({db.count()} rows)")
        finally:
            db.close()

    check(observations.RECONSTRUCTABLE_POLICIES == ("never", "split_only"),
          f"the permitted policies are declared in one place "
          f"({observations.RECONSTRUCTABLE_POLICIES})")
    check("reconstructed" in observations.AVAILABILITY_KINDS,
          "and `reconstructed` is a declared availability kind, so a reader can "
          "tell a reconstructed availability from an observed one")
    try:
        observations.ObservationStore(":memory:").write_many([
            {"registry_key": "x", "instrument": None, "observed_at": "2026-01-01",
             "available_at": "2026-01-01T00:00:00+00:00", "value": 1.0,
             "source": "t", "availability_kind": "invented"}])
        bad("an unrecognised availability_kind is accepted -- the column would "
            "be unqueryable")
    except ValueError:
        ok("an unrecognised availability_kind is rejected at the write, not "
           "stored and forgotten")


def group_f() -> None:
    print(f"\n{LINE}\nF. THE RECONSTRUCTED CLOCK IS THE CLOSE, IN THE RIGHT ZONE\n{LINE}")
    summer = bp.reconstructed_available_at("2026-09-18")
    winter = bp.reconstructed_available_at("2026-01-15")
    check(summer.startswith("2026-09-18T20:20"),
          f"a September session close (16:00 EDT = 20:00 UTC) plus the declared "
          f"{yf_src.RECONSTRUCTED_LATENCY_MINUTES} minutes is 20:20 UTC "
          f"(got {summer})")
    check(winter.startswith("2026-01-15T21:20"),
          f"a January one (16:00 EST = 21:00 UTC) is 21:20 UTC (got {winter}) -- "
          f"a fixed offset would put half the year an hour before its own close")
    check(summer > "2026-09-18T20:00",
          "and it is AFTER the close it describes, never before")
    check(yf_src.RECONSTRUCTED_LATENCY_MINUTES > 0,
          f"the latency is declared and positive "
          f"({yf_src.RECONSTRUCTED_LATENCY_MINUTES} minutes), so every "
          f"reconstructed row in the store means the same thing")


def group_g() -> None:
    print(f"\n{LINE}\nG. A RE-READ OF AN IDENTICAL VALUE IS NOT A REVISION\n{LINE}")
    import tempfile
    from altdata import session as sess
    with tempfile.TemporaryDirectory() as td:
        db = observations.ObservationStore(str(Path(td) / "v.db"))
        try:
            rows = [{"registry_key": "yfinance.mkt_spy", "instrument": None,
                     "observed_at": "2026-09-18",
                     "available_at": "2026-09-18T20:20:00+00:00",
                     "value": 761.69, "source": "yfinance",
                     "availability_kind": "reconstructed"}]
            first = db.write_many(observations.drop_unchanged(db, rows))
            check(first == 1, f"the first write lands ({first} row)")

            # THE SAME VALUE, A LATER INSTANT: what a second pull of the day does.
            again = [{**rows[0], "available_at": "2026-09-20T15:00:00+00:00",
                      "availability_kind": "ingest_instant"}]
            second = db.write_many(observations.drop_unchanged(db, again))
            check(second == 0,
                  f"a SECOND PULL OF AN UNCHANGED VALUE WRITES ZERO ROWS "
                  f"(got {second}) -- without this it would create a vintage that "
                  f"supersedes the better-dated one and hide the close from every "
                  f"earlier as-of cutoff")
            check(len(db.vintages("yfinance.mkt_spy", "2026-09-18")) == 1,
                  "so the period still has exactly one vintage")

            # A CHANGED value is a revision and must still land.
            revised = [{**again[0], "value": 762.15}]
            third = db.write_many(observations.drop_unchanged(db, revised))
            check(third == 1,
                  f"but a CHANGED value does land ({third}) -- a corrected close is "
                  f"exactly what a vintage is for")
            vs = db.vintages("yfinance.mkt_spy", "2026-09-18")
            check(len(vs) == 2 and vs[-1]["value_num"] == 762.15,
                  f"and the newer vintage wins for a later reader "
                  f"({[v['value_num'] for v in vs]})")

            # THE PROOF THAT MATTERS: the earlier cutoff still sees the original.
            early = db.as_of("yfinance.mkt_spy", as_of="2026-09-19T00:00:00+00:00")
            check(early and early[-1]["value_num"] == 761.69,
                  f"while a reader as of the 19th still sees 761.69, not the "
                  f"revision published on the 20th ({early[-1]['value_num']})")
        finally:
            db.close()

    src = (REPO / "metrics_registry.yaml").read_text(encoding="utf-8")
    check("A RE-READ OF AN IDENTICAL VALUE IS NOT A REVISION" in src,
          "and the rule is written into the registry doc, not only into the code")


def group_h() -> None:
    print(f"\n{LINE}\nH. NO BAR ON A NON-SESSION DATE\n{LINE}")
    # 2026-09-07 is Labor Day and 2026-09-12/13 are a weekend. yfinance served a VIX
    # close on the holiday; the index does not exist on a day the options market is
    # shut, and stored it would have counted as a session in every percentile and
    # every staleness count that reads the series.
    rows = [("2026-09-04", 10.0), ("2026-09-07", 11.0), ("2026-09-08", 12.0),
            ("2026-09-12", 13.0), ("2026-09-13", 14.0)]
    kept, dropped = yf_src.drop_non_session_bars("^VIX", rows)
    check([d for d, _ in kept] == ["2026-09-04", "2026-09-08"],
          f"a holiday and a weekend are dropped from an exchange-traded series "
          f"(kept {[d for d, _ in kept]})")
    check(dropped == ["2026-09-07", "2026-09-12", "2026-09-13"],
          f"and the dropped dates are reported rather than silently discarded "
          f"({dropped})")

    kept_c, dropped_c = yf_src.drop_non_session_bars("BTC-USD", rows)
    check(len(kept_c) == len(rows) and not dropped_c,
          "a DECLARED continuous instrument keeps every bar -- Bitcoin trades all "
          "week, and 528 of its 1,827 bars are on non-session dates and real")
    # EXACTLY THE DECLARED SET, NOT A PATTERN. Bitcoin, and since ST-2 the
    # offshore yuan, whose US-holiday quotes are real. Anything else arriving here
    # is an exemption nobody reviewed.
    check(set(yf_src.CONTINUOUS_SYMBOLS) == {"BTC-USD", "CNH=X"},
          f"the exemption is a declared set (BTC-USD, CNH=X), not a guess about "
          f"tickers ({sorted(yf_src.CONTINUOUS_SYMBOLS)})")

    # And the live store obeys it, which is the assertion the order asked for.
    db = observations.ObservationStore()
    try:
        offenders = {}
        for sym, key in yf_src.SYMBOLS.items():
            if sym in yf_src.CONTINUOUS_SYMBOLS:
                continue
            bad_days = [str(r["observed_at"])[:10]
                        for r in db.as_of(f"yfinance.{key}")
                        if not yf_src.is_session_date(str(r["observed_at"])[:10])]
            if bad_days:
                offenders[key] = bad_days[-3:]
        check(not offenders,
              f"NO PRICE SERIES IN THE STORE carries a non-session observed date "
              f"({offenders or 'clean'})")
    finally:
        db.close()

    check(yf_src.is_session_date("2026-09-07") is False,
          "Labor Day 2026 is not a session")
    check(yf_src.is_session_date("2026-09-18") is True,
          "and Friday 18 September is")


def main() -> int:
    print(f"{LINE}\nThe price feed -- parser on a fixture, and the availability rule\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_d_backfill,
              group_e, group_f,
              group_g, group_h):
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            bad(f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
