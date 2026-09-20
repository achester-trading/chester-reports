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


def group_d() -> None:
    print(f"\n{LINE}\nD. THE BASKET IS DECLARED AND REGISTERED\n{LINE}")
    syms = yf_src.SYMBOLS
    check(len(syms) == 28, f"28 symbols declared (got {len(syms)})")
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


def main() -> int:
    print(f"{LINE}\nThe price feed -- parser on a fixture, and the availability rule\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f):
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
