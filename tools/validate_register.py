"""
Validation gate for the point-in-time store, the decision register, and replay.

Four groups, each proving something that would otherwise be a claim:

  A  LEAKAGE. A row whose available_at is after the query cutoff must be
     invisible. Plus the revision case, which is the reason the whole store
     exists -- FRED restates, and a backtest that sees the restatement is
     trading on information that did not exist.
  B  THE BROOKFIELD RESTRICTION. Rejected at write time, by the Python register
     AND by a SQLite trigger that fires for an inserter which never imports it.
     A rule enforced in only one place is enforced only for people who use that
     place.
  C  IMMUTABILITY. Packets refuse UPDATE and DELETE; a superseded decision is
     frozen. Evidence that can be edited is not evidence.
  D  REPLAY. Friday's run, rebuilt from its own packet: same SHA, same data
     manifest, same output. This is architecture 26.2 #3's acceptance test.

Runs against a temporary database, so it never touches data/chester.db.

    python tools/validate_register.py
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from altdata import config, observations, session  # noqa: E402
from register import instruments, manifest  # noqa: E402
from register.store import (Register, RestrictedInstrumentError,   # noqa: E402
                            CurrencyExposureUnstatedError, listing_currency)
import exposure_compute as ec               # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
SKIPPED: list[str] = []
LINE = "=" * 78


def ok(msg: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {msg}")


def bad(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {msg}")


def check(cond: bool, msg: str) -> None:
    ok(msg) if cond else bad(msg)


def raises(fn, exc, msg: str) -> None:
    try:
        fn()
    except exc:
        ok(msg)
        return
    except Exception as e:  # noqa: BLE001
        bad(f"{msg} -- raised {type(e).__name__} instead: {e}")
        return
    bad(f"{msg} -- did not raise")


# ---------------------------------------------------------------------------
def group_a(db_path: str) -> None:
    print(f"\n{LINE}\nA. POINT-IN-TIME: leakage and revisions\n{LINE}")
    store = observations.ObservationStore(db_path)

    # The leakage case. Same series, one row knowable before the cutoff and one
    # only after it.
    store.write("test.series", None, "2026-08-01",
                "2026-09-01T12:00:00+00:00", 100.0, source="fred")
    store.write("test.series", None, "2026-09-01",
                "2026-10-01T12:00:00+00:00", 200.0, source="fred")

    at_sep = store.as_of("test.series", as_of="2026-09-15T00:00:00+00:00")
    check(len(at_sep) == 1 and at_sep[0]["value_num"] == 100.0,
          "a row whose available_at is AFTER the cutoff is invisible")
    check(all(r["available_at"] <= "2026-09-15T00:00:00+00:00" for r in at_sep),
          "every returned row was knowable at the cutoff")

    at_oct = store.as_of("test.series", as_of="2026-10-15T00:00:00+00:00")
    check(len(at_oct) == 2, "the same query later sees both periods")

    # The revision case -- the reason available_at exists at all.
    store.write("test.revised", None, "2026-08-01",
                "2026-09-05T12:30:00+00:00", 150.0, source="fred")
    store.write("test.revised", None, "2026-08-01",
                "2026-10-03T12:30:00+00:00", 175.0, source="fred")

    first = store.as_of("test.revised", as_of="2026-09-20T00:00:00+00:00")
    later = store.as_of("test.revised", as_of="2026-10-20T00:00:00+00:00")
    check(len(first) == 1 and first[0]["value_num"] == 150.0,
          "before the restatement, the ORIGINAL print is returned")
    check(len(later) == 1 and later[0]["value_num"] == 175.0,
          "after it, the revision supersedes -- one row per period, not two")
    check(len(store.vintages("test.revised", "2026-08-01")) == 2,
          "both vintages survive; the original is not overwritten")

    # Forward-dated observed_at must NOT be filtered: the expiration-release
    # ladder is dated at future expiries and was known when computed.
    store.write("test.forward", None, "2026-12-18",
                "2026-09-04T20:10:00+00:00", 42.0, source="yfinance")
    fwd = store.as_of("test.forward", as_of="2026-09-05T00:00:00+00:00")
    check(len(fwd) == 1,
          "a forward-DATED record stays visible (leakage is about knowing, "
          "not about the period)")

    # REGRESSION: mixed-precision instants. The join compares available_at
    # lexicographically so SQLite can use an index, and that only matches
    # chronological order when every value is the same width. A microsecond
    # stamp sorts AFTER a second-resolution one for the same instant, because
    # '.' > '+'. FRED writes seconds and broker snapshots write microseconds,
    # so without canonicalisation the broker rows were invisible to any
    # second-resolution cutoff -- they looked like they had not happened yet.
    store.write("test.precision", None, "2026-09-04",
                "2026-09-04T20:10:00+00:00", 1.0, source="fred")
    store.write("test.precision", None, "2026-09-05",
                "2026-09-05T11:22:33.456789+00:00", 2.0, source="ibkr_paper")
    mixed = store.as_of("test.precision", as_of="2026-09-05T12:00:00+00:00")
    check(len(mixed) == 2,
          "a MICROSECOND row and a SECOND row are both visible to one cutoff")
    tight = store.as_of("test.precision", as_of="2026-09-05T11:22:33+00:00")
    check(len(tight) == 1 and tight[0]["value_num"] == 1.0,
          "a cutoff mid-second correctly excludes the later microsecond row")

    # Idempotence: re-ingesting the same vintage is a no-op, not a duplicate.
    before = store.count()
    store.write("test.series", None, "2026-08-01",
                "2026-09-01T12:00:00+00:00", 100.0, source="fred")
    check(store.count() == before, "re-ingesting the same vintage is idempotent")
    store.close()


# ---------------------------------------------------------------------------
def group_b(db_path: str) -> None:
    print(f"\n{LINE}\nB. THE BROOKFIELD RESTRICTION, at write time\n{LINE}")
    reg = Register(db_path)

    base = dict(direction="long", thesis="t", edge_type="e",
                horizon="swing", invalidation="below 40")

    # A clear instrument must still work -- a rule that blocks everything is
    # not evidence that it blocks the right thing.
    did = reg.record(instrument="SPY", **base)
    check(reg.get(did) is not None, "an unrestricted instrument records normally")

    for bad_sym, why in (
            ("BN", "the parent, plain ticker"),
            ("bn.to", "lower case, exchange suffix"),
            ("BN.PR.A", "a preferred series"),
            ("BEP.UN", "a unit class"),
            ("O:BN260918C00050000", "a Polygon option symbol"),
            ("BN260918C00050000", "an OCC contract symbol"),
            ("BNT", "Brookfield Wealth Solutions -- the operator's own chain"),
            ("OCSL", "Oaktree, tier 4"),
            ("Brookfield Real Assets Income Fund", "matched on entity NAME"),
            # THE LISTING-QUALIFIER BYPASS. Portfolio Truth keys a holding
            # `<sym>@<venue>.<currency>` and the register accepts that form, so
            # the normaliser has to strip it BEFORE the blocklist is consulted.
            # It did not, briefly: the dotted-suffix rule ate `.CAD` as a
            # three-letter tail, left `@TSE` attached, and `BN@TSE.CAD`
            # normalised to `BN@TSE` -- no root matched and a restricted
            # instrument written the qualified way walked through the compliance
            # check. This is the one failure mode a compliance restriction may
            # not have, so it is pinned here rather than left to the unit case.
            ("BN@TSE.CAD", "the qualified listing form must not bypass the rule"),
            ("bn@tse.cad", "the qualified form, lower case"),
            ("BEP.UN@TSE.CAD", "a unit class in the qualified form"),
            ("BN    260918C00050000@SMART.USD", "an OCC option, qualified"),
    ):
        raises(lambda s=bad_sym: reg.record(instrument=s, **base),
               RestrictedInstrumentError, f"refused {bad_sym!r} -- {why}")

    # Compliance OUTRANKS the currency rule. A restricted instrument in a
    # non-USD listing must report the restriction, not a missing field: the
    # operator who supplies currency_exposure and retries must still be refused.
    raises(lambda: reg.record(instrument="BN@TSE.CAD",
                              currency_exposure="hedged", **base),
           RestrictedInstrumentError,
           "a restricted non-USD listing is refused as RESTRICTED even with "
           "currency_exposure supplied -- compliance is checked first")

    check(instruments.normalise("BEPC@NYSE.USD") == "BEPC",
          "BEPC does not collapse to BEP once the qualifier is stripped")

    n_blocked = len(reg.blocked_attempts())
    check(n_blocked == 14, f"every refusal is logged ({n_blocked} attempts recorded)")

    # THE BACKSTOP. A raw connection that never imports the register.
    raw = sqlite3.connect(db_path)
    def raw_insert():
        raw.execute(
            "INSERT INTO decisions (id, created_at, decision_time, instrument,"
            " instrument_norm, direction, thesis, edge_type, horizon,"
            " invalidation, status) VALUES"
            " ('x','t','t','BN','BN','long','t','e','swing','i','draft')")
        raw.commit()
    raises(raw_insert, sqlite3.IntegrityError,
           "a RAW sqlite insert bypassing the Python register is refused by the trigger")
    # The aborted insert leaves the raw connection holding a lock; release it
    # before the register writes again or the next check fails on the lock
    # rather than on what it is actually testing.
    raw.rollback()
    raw.close()

    # Closed vocabularies are schema constraints, not conventions.
    raises(lambda: reg.record(instrument="QQQ", **{**base, "horizon": "monthly"}),
           sqlite3.IntegrityError,
           "'monthly' is not a Part 7 horizon and the CHECK constraint says so")
    raises(lambda: reg.record(instrument="QQQ", **{**base, "direction": "buy"}),
           sqlite3.IntegrityError,
           "'buy' is not a direction; the vocabulary is closed")
    reg.close()


# ---------------------------------------------------------------------------
def group_g(db_path: str) -> None:
    """Part 31.3(c): the currency leg the ticker hides."""
    print(f"\n{LINE}\nG. PART 31.3(c) -- CURRENCY EXPOSURE ON A NON-USD LISTING\n{LINE}")
    reg = Register(db_path)
    base = dict(direction="short", thesis="t", edge_type="positioning",
                horizon="swing", invalidation="none")

    for inst, ccy in (("SPY", None), ("SPY@ARCA.USD", "USD"),
                      ("SPY@MEXI.MXN", "MXN"), ("7203@TSEJ.JPY", "JPY"),
                      ("SPY   260918C00780000@SMART.USD", "USD")):
        check(listing_currency(inst) == ccy,
              f"listing_currency({inst!r}) == {ccy!r}")

    # THE 17 SEPTEMBER 2026 CASE. The exit was submitted against SPY on MEXI in
    # pesos instead of SPY on ARCA in dollars, and nothing asked why a dollar
    # book was taking peso exposure. This refusal is that question.
    raises(lambda: reg.record(instrument="SPY@MEXI.MXN", **base),
           CurrencyExposureUnstatedError,
           "a non-USD listing without currency_exposure is refused")
    # Since INC-6 the expression currency must match the listing too (group K):
    # a deliberate peso position is expressed in MXN.
    did = reg.record(instrument="SPY@MEXI.MXN", currency_exposure="unhedged",
                     expression_currency="MXN", **base)
    check(reg.get(did)["currency_exposure"] == "unhedged",
          "stated deliberately, it records -- and the field is on the row")

    # A USD listing and a bare ticker are unaffected: the rule is about a
    # currency leg, not about qualifying every instrument.
    check(reg.get(reg.record(instrument="SPY@ARCA.USD", **base)) is not None,
          "a USD listing needs no currency_exposure")
    check(reg.get(reg.record(instrument="QQQ", **base)) is not None,
          "an unqualified ticker needs none either -- currency unknown, not USD")

    raises(lambda: reg.record(instrument="SPY@MEXI.MXN",
                              currency_exposure="maybe", **base),
           ValueError, "the vocabulary is closed (unhedged/hedged/n_a)")

    # ANNOTATING A LIVE ROW IS NOT ACTIVATING IT. The CLI re-checks signal
    # freshness when a row BECOMES active, which is right, and used to re-check
    # it on any set-status naming `active` -- including on a row that already
    # was. That made the register unable to describe its own open positions: a
    # held position's entry signals are stale a week later by definition, so the
    # one write that matters after a missed exit (status still active,
    # thesis_state INVALIDATED) was refused as a stale activation.
    live = reg.record(instrument="QQQ", status="active",
                      operator_action="TAKE", book="B",
                    falsifiers=["fixture falsifier"], counter_thesis="fixture counter-thesis",
                      **{**base, "thesis": "held position"})
    reg.close()

    r = subprocess.run([sys.executable, str(REPO / "tools" / "decide.py"),
                        "--db", db_path, "set-status", "--id", live,
                        "--status", "active", "--thesis-state", "INVALIDATED",
                        "--note", "thesis dead, position still on", "--dry-run"],
                       capture_output=True, text=True, cwd=str(REPO))
    check(r.returncode == 0 and "INVALIDATED" in r.stdout
          and "RE-CHECKED NOW" not in r.stdout,
          "an already-active row can be annotated INVALIDATED without a "
          "freshness re-check -- the gate is on the transition, not on a touch")

    reg = Register(db_path)
    d2 = reg.record(instrument="QQQ", status="draft",
                    **{**base, "thesis": "a draft to promote"})
    reg.close()
    r = subprocess.run([sys.executable, str(REPO / "tools" / "decide.py"),
                        "--db", db_path, "set-status", "--id", d2,
                        "--status", "active", "--dry-run"],
                       capture_output=True, text=True, cwd=str(REPO))
    check("RE-CHECKED NOW" in r.stdout,
          "a DRAFT becoming active still gets the freshness re-check -- "
          "narrowing the gate did not remove it")

    # RE-DESIGNATION, NOT SUBSTITUTION. A decision written as `SPY` cannot be
    # joined to a holding keyed `SPY@ARCA.USD` once the book carries two SPY
    # listings, so a supersession may make the designation more precise. Left
    # open, the same flag would be a way to move a recorded decision onto a
    # different security and inherit its thesis, timestamps and grading -- so the
    # issuer root must not change, and that is the whole rule.
    reg = Register(db_path)
    d3 = reg.record(instrument="SPY", status="active", operator_action="TAKE",
                    book="B",
                    falsifiers=["fixture falsifier"], counter_thesis="fixture counter-thesis",
                    **{**base, "direction": "long", "thesis": "to re-designate"})
    reg.close()

    def set_status_cli(*extra):
        return subprocess.run(
            [sys.executable, str(REPO / "tools" / "decide.py"), "--db", db_path,
             "set-status", "--id", d3, "--status", "active", "--dry-run", *extra],
            capture_output=True, text=True, cwd=str(REPO))

    r = set_status_cli("--instrument", "SPY@ARCA.USD", "--note", "precision")
    check("SPY -> SPY@ARCA.USD" in r.stdout and "same root SPY" in r.stdout,
          "SPY -> SPY@ARCA.USD is permitted: the same issuer, stated precisely")

    r = set_status_cli("--instrument", "QQQ", "--note", "substitution")
    check("REFUSED" in r.stdout and "changes the issuer" in r.stdout,
          "SPY -> QQQ is REFUSED -- a supersession may not substitute a "
          "different security and inherit the thesis and grading of this one")

    r = set_status_cli("--instrument", "BN@TSE.CAD", "--note", "restricted")
    check("REFUSED" in r.stdout,
          "and it cannot be used to walk a decision into the Brookfield complex")


# ---------------------------------------------------------------------------
def group_c(db_path: str) -> None:
    print(f"\n{LINE}\nC. IMMUTABILITY of packets and superseded decisions\n{LINE}")
    reg = Register(db_path)
    did = reg.record(instrument="IWM", direction="short", thesis="t",
                     edge_type="e", horizon="positional", invalidation="above 300")
    pid = reg.attach_packet(did, {
        "run_id": "r1", "decision_time": session.utc_iso(),
        "available_at_cutoff": session.utc_iso(), "git_sha": "abc",
        "code_dirty": 0, "data_manifest_hash": "h", "data_manifest": {},
        "metrics_registry_version": "1", "source_registry_version": "1",
        "output_hash": "o", "volatile_fields": ["computed_at"]})
    check(reg.packet(did) is not None, "a packet attaches to its decision")

    raises(lambda: reg.conn.execute(
        "UPDATE decision_packets SET git_sha='tampered' WHERE packet_id=?", (pid,)),
        sqlite3.IntegrityError, "UPDATE on decision_packets is refused")
    raises(lambda: reg.conn.execute(
        "DELETE FROM decision_packets WHERE packet_id=?", (pid,)),
        sqlite3.IntegrityError, "DELETE on decision_packets is refused")

    new_id = reg.supersede(did, instrument="IWM", direction="short", thesis="t2",
                           edge_type="e", horizon="positional",
                           invalidation="above 305")
    check(reg.get(did)["superseded_by"] == new_id,
          "supersede writes a NEW record and points the old one at it")
    raises(lambda: reg.set_status(did, "closed"), sqlite3.IntegrityError,
           "a superseded decision is frozen -- Part 7's grading trail survives")
    reg.close()


# ---------------------------------------------------------------------------
def seed_fresh_signals(td: str) -> dict:
    """Synthesise the two inputs group E's clean path needs, and return the env
    that points `decide.py` at them.

    Why this exists. `exposure.gamma_flip` resolves through the newest computed
    profile and `pin.hit` through the pin log -- both under `data/`, which is
    gitignored. On a fresh CI checkout neither exists, so both read as "no
    observation found", the clean-path assertions below get a DECISION_BLOCKED,
    and the gate fails for a reason that is about the checkout rather than
    about the code. That is what happened from 55630fb onward.

    Deleting the assertion was the other option and it is the wrong one: it is
    the half of 26.2 #7 that proves the freshness check DISCRIMINATES. A check
    that only ever blocks is indistinguishable from an outage, and a gate that
    cannot tell those apart is not a gate. So seed the inputs instead.

    These are the thinnest records the two locators will accept -- a session
    date and a symbol. They are not plausible market data and are not meant to
    be: nothing here computes on them, the locators only read their freshness.
    The blocked-path assertions above stay honest because `portfolio.nav` is
    deliberately NOT seeded, so the block still has exactly one cause and the
    test still names it.
    """
    root = Path(td) / "signals"
    computed = root / "computed"
    last = session.last_trading_session().isoformat()
    (computed / last).mkdir(parents=True, exist_ok=True)
    (computed / last / f"SPY_{last}_exposure.json").write_text(
        json.dumps({"symbol": "SPY", "session_date": last,
                    "synthetic": "validate_register group E fixture"}),
        encoding="utf-8")

    pin = root / "pin_log.csv"
    import pin_log as pl  # noqa: PLC0415
    with pin.open("w", encoding="utf-8", newline="") as fp:
        import csv  # noqa: PLC0415
        w = csv.DictWriter(fp, fieldnames=pl.PIN_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerow({"date": last, "symbol": "SPY"})

    # AND AN EMPTY OBSERVATION STORE OF ITS OWN. A code gate never reads the live
    # store: on the box the IBKR sync writes a fresh portfolio.nav into it, and
    # once freshness resolved keys through the registry (3a1785f) that live row
    # un-blocked the blocked path below -- the gate failed on the box and passed
    # on a laptop for a reason that was about the machine, not the code.
    obs = Path(td) / "group_e_obs.db"
    with observations.ObservationStore(str(obs)):
        pass
    return {"CHESTER_COMPUTED_DIR": str(computed),
            "CHESTER_PIN_LOG_PATH": str(pin),
            "CHESTER_DB": str(obs)}


def group_e(db_path: str, td: str) -> None:
    print(f"\n{LINE}\nE. THE DECISION CLI\n{LINE}")
    import subprocess
    env = {**os.environ, **seed_fresh_signals(td)}
    def run_cli(*a):
        return subprocess.run([sys.executable, str(REPO / "tools" / "decide.py"),
                               "--db", db_path, *a],
                              capture_output=True, text=True, cwd=str(REPO),
                              env=env)

    # The seeding is itself worth asserting. If it silently stopped working --
    # a renamed env var, a changed locator -- every clean-path check below
    # would fail with a blocked decision and point at the CLI instead of at
    # the fixture.
    #
    # `config` was imported before the env was set, so the in-process check has
    # to be pointed at the fixture by hand and pointed back afterwards. Leaving
    # it repointed would redirect group F's pin-log reads at an empty file and
    # turn a real check into a false skip.
    import freshness                             # noqa: PLC0415
    saved = (config.COMPUTED_DIR, config.PIN_LOG_PATH, observations.DEFAULT_DB)
    config.COMPUTED_DIR = env["CHESTER_COMPUTED_DIR"]
    config.PIN_LOG_PATH = env["CHESTER_PIN_LOG_PATH"]
    observations.DEFAULT_DB = env["CHESTER_DB"]
    try:
        check(not freshness.check_signals(
                  ["exposure.gamma_flip", "pin.hit"], "SPY")["blocked"],
              "fixture: both seeded signals locate and read fresh")
        check(freshness.check_signals(["portfolio.nav"], "SPY")["blocked"],
              "fixture: portfolio.nav is deliberately NOT seeded, so the "
              "blocked path below has exactly one cause")
    finally:
        config.COMPUTED_DIR, config.PIN_LOG_PATH, observations.DEFAULT_DB = saved

    ok_args = ["record", "--instrument", "SPY", "--direction", "long",
               "--thesis", "t", "--edge-type", "positioning",
               "--horizon", "swing", "--invalidation", "below 760",
               # Signals that ARE fresh -- seeded above -- so this exercises
               # the clean path rather than accidentally testing the block.
               "--signals-used", "exposure.gamma_flip", "pin.hit"]
    r = run_cli(*ok_args, "--dry-run")
    check(r.returncode == 0 and "DRY RUN" in r.stdout,
          "a clean instrument dry-runs to exit 0")
    check("no decision written" in r.stdout, "the dry run says it wrote nothing")

    reg = Register(db_path)
    before = len(reg.all())
    reg.close()
    run_cli(*ok_args, "--dry-run")
    reg = Register(db_path)
    check(len(reg.all()) == before,
          "a dry run really writes nothing -- the register is unchanged")
    reg.close()

    # THE CASE THAT MATTERS: the restriction must fire in dry-run too, or the
    # dry run reports "this is what would happen" while omitting the one thing
    # that would not.
    r = run_cli("record", "--instrument", "BN.TO", "--direction", "long",
                "--thesis", "t", "--edge-type", "structural",
                "--horizon", "positional", "--invalidation", "x", "--dry-run",
                "--signals-used", "exposure.gamma_flip")
    check(r.returncode == 2, "a restricted instrument dry-runs to exit 2")
    check("REFUSED" in r.stdout and "brookfield" in r.stdout,
          "the dry run REFUSES it rather than reporting what would happen")

    # Invalidation is required by the CLI, not merely NOT NULL in the schema:
    # an argument you can omit gets filled in later, which is when it stops
    # being an invalidation.
    r = run_cli("record", "--instrument", "SPY", "--direction", "long",
                "--thesis", "t", "--edge-type", "positioning",
                "--horizon", "swing", "--dry-run",
                "--signals-used", "exposure.gamma_flip")
    check(r.returncode != 0 and "invalidation" in (r.stderr + r.stdout),
          "a decision with no invalidation is refused by the CLI")

    # ---- DECISION_BLOCKED (26.2 #7) --------------------------------------
    blocked = ["record", "--instrument", "SPY", "--direction", "long",
               "--thesis", "t", "--edge-type", "positioning",
               "--horizon", "swing", "--invalidation", "x",
               "--status", "active",
               "--signals-used", "exposure.gamma_flip", "portfolio.nav"]
    r = run_cli(*blocked, "--dry-run")
    check(r.returncode == 3, "a blocked dry run exits 3, not 0")
    check("DECISION_BLOCKED" in r.stdout, "the dry run says DECISION_BLOCKED")
    check("what would unblock it" in r.stdout,
          "it prints what would unblock it, not merely that it is blocked")
    check("downgraded to `draft`" in r.stdout,
          "a requested `active` is visibly downgraded")

    r = run_cli(*blocked)
    check(r.returncode == 3, "the real write also exits 3 when blocked")
    reg = Register(db_path)
    rows = [d for d in reg.all() if d.get("blocked_reason")]
    check(bool(rows), "a blocked decision is RECORDED, not refused -- an "
                      "abstention is a decision")
    if rows:
        d = rows[-1]
        check(d["status"] == "draft",
              "it lands as draft even though `active` was requested")
        check("portfolio.nav" in (d["blocked_reason"] or ""),
              "blocked_reason names the signal that blocked it")
        check("exposure.gamma_flip" in (d["signals_used"] or ""),
              "signals_used is stored on the row")
        raises(lambda: reg.set_status(d["id"], "active"), ValueError,
               "a blocked row cannot later be promoted to active")
    reg.close()

    # And the other side of 26.2 #7: fresh inputs must NOT block, or the check
    # is just an outage.
    r = run_cli("record", "--instrument", "SPY", "--direction", "long",
                "--thesis", "t", "--edge-type", "positioning",
                "--horizon", "swing", "--invalidation", "x", "--dry-run",
                "--signals-used", "exposure.gamma_flip", "pin.hit")
    check(r.returncode == 0 and "DECISION_OK" in r.stdout,
          "signals inside their half-life are DECISION_OK -- Friday's close on "
          "a Saturday is current, not stale")


def group_h(db_path: str) -> None:
    """The expression fields and the four options-paper rules. (Paste D piece 5)"""
    print(f"\n{LINE}\nH. EXPRESSION FAMILY, LEVERAGE FORM, AND THE FOUR RULES\n{LINE}")
    import expression_check as ex
    from register import store as rs

    # --- the vocabularies are closed, and the closure is the point -----------
    check(len(rs.EXPRESSION_FAMILIES) >= 20 and "outright" in rs.EXPRESSION_FAMILIES,
          f"{len(rs.EXPRESSION_FAMILIES)} expression families are declared, "
          f"including `outright` so 'no structure' is a recorded answer rather "
          f"than a blank")
    check("ppn_restrike" in rs.LEVERAGE_FORMS and "short_box" in rs.LEVERAGE_FORMS
          and "none" in rs.LEVERAGE_FORMS,
          f"{len(rs.LEVERAGE_FORMS)} leverage forms are declared, including the "
          f"PPN re-strike and the short box")

    reg = rs.Register(db_path)
    kw = dict(instrument="SPY", direction="long", thesis="t",
              edge_type="mispricing", horizon="positional", invalidation="x",
              signals_used=["yfinance.mkt_spy"])
    did = reg.record(expression_family="risk_reversal", leverage_form="leaps", **kw)
    row = reg.conn.execute(
        "SELECT expression_family, leverage_form FROM decisions WHERE id=?",
        (did,)).fetchone()
    check(tuple(row) == ("risk_reversal", "leaps"),
          f"both fields round-trip through the register {tuple(row)}")
    for field, value in (("expression_family", "condor-ish"),
                         ("leverage_form", "lots")):
        try:
            reg.record(**{field: value}, **kw)
            bad(f"{field} accepted {value!r} -- free text would create a value no "
                f"query groups with the one it meant")
        except ValueError as exc:
            ok(f"{field} refuses {value!r} ({str(exc)[:48]}...)")
    check(reg.record(**kw) is not None,
          "and both are OPTIONAL -- the column was added to a live register and "
          "every pre-existing row predates it")
    reg.conn.close()

    # --- the four rules WARN and never block --------------------------------
    def codes(**kw2):
        return [w["code"] for w in ex.check(**kw2)]

    base = dict(edge_type="convexity", horizon="swing", sec_type="OPT",
                expiry="20271217")
    check("expression_family_unrecorded" in codes(**base),
          "an options decision with no expression_family warns -- 26.7's error "
          "decomposition cannot be applied to an expression nobody recorded")
    check("leverage_form_unrecorded" in codes(
              edge_type="mispricing", horizon="positional", sec_type="STK",
              notional=250000, allocation=100000),
          "notional above the allocation with no leverage_form warns")
    check("leverage_form_unrecorded" not in codes(
              edge_type="mispricing", horizon="positional", sec_type="STK",
              notional=50000, allocation=100000),
          "and an unlevered position does not")
    check("index_comparison_unstated" in codes(
              expression_family="iron_condor", **base),
          "an option structure with no index-outright comparison warns -- Chapter "
          "15 prices every structure against the index and a 50/50 mix, and most "
          "lose to the mix")
    check("index_comparison_unstated" not in codes(
              expression_family="iron_condor",
              index_comparison="beats outright inside 4,900-5,400", **base),
          "and a stated comparison clears it")
    check("index_comparison_unstated" not in codes(
              expression_family="outright", **base),
          "while `outright` is not asked to defend itself against the index")
    check("long_vol_at_high_iv" in codes(
              expression_family="long_straddle", iv_percentile=92.0, **base),
          f"buying a straddle at the 92nd IV percentile warns "
          f"(threshold {ex.IV_PERCENTILE_WARN})")
    check("long_vol_at_high_iv" not in codes(
              expression_family="long_straddle", iv_percentile=40.0, **base),
          "and the same structure at the 40th does not")
    # THE EXCEPTION THAT MAKES THE RULE RIGHT. 16.3 recommends the
    # deep-in-the-money LEAP as the way to add AT a trough: its price is intrinsic
    # value and its extrinsic is a fraction, so a high IV percentile barely touches
    # it. A rule that flagged it would be telling the operator not to do the thing
    # the chapter tells him to do.
    check("long_vol_at_high_iv" not in codes(
              expression_family="diagonal", leverage_form="leaps",
              iv_percentile=95.0, index_comparison="beats outright above 5,100",
              **base),
          "a deep-in-the-money LEAP at the 95th percentile is NOT flagged -- its "
          "price is intrinsic and 16.3 names it as the way to add at a trough")
    for w in ex.check(expression_family="long_straddle", iv_percentile=92.0,
                      **base):
        check(w.get("severity") == "warning" and w.get("mechanism"),
              f"{w['code']} is a warning and names its mechanism -- binding is "
              f"Phase 5's job, and a mechanism can be argued with where a score "
              f"cannot")


def group_f() -> None:
    print(f"\n{LINE}\nF. PROVENANCE AND THE TOLERANCE POLICY\n{LINE}")
    import pin_log as pl
    chains = ec.newest_chains("2026-09-04", ["SPY"])
    if not chains:
        SKIPPED.append("provenance/tolerance: no stored SPY chain")
        print("  SKIP  no stored SPY chain")
        return
    rows = ec.load_chain(chains["SPY"])
    prof = ec.compute_symbol([dict(r) for r in rows], "SPY")
    check(prof["greeks_source"] == "computed_bs_from_yf_iv",
          f"vendor-IV profile is labelled {prof['greeks_source']!r}")
    solved = [{**r, "iv_source": "solved_bs_v1"} for r in rows]
    check(ec.compute_symbol(solved, "SPY")["greeks_source"] == "solved_bs_v1",
          "solver-IV profile is labelled solved_bs_v1, distinctly")
    mixed = ec.compute_symbol(
        [dict(r) for r in rows[:400]] +
        [{**r, "iv_source": "solved_bs_v1"} for r in rows[400:]], "SPY")
    check(mixed["greeks_source"].startswith("mixed:"),
          f"a mixed profile reports AS mixed ({mixed['greeks_source'][:44]}...)")

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        logp = str(Path(td) / "pin.csv")
        pl.run(date="2026-09-04", log_path=logp)
        first = pl.declared_tolerances(logp)
        original = config.PIN_TOLERANCE_BPS
        try:
            config.PIN_TOLERANCE_BPS = 500.0
            pl.run(date="2026-09-04", log_path=logp)
            after = pl.declared_tolerances(logp)
            check(after == first,
                  "a rerun PRESERVES each row's declared tolerance when config moved")
            pl.run(date="2026-09-04", log_path=logp, allow_regrade=True)
            regraded = pl.declared_tolerances(logp)
            check(all(v == 500.0 for v in regraded.values()),
                  "--allow-regrade is the ONLY way the declared tolerance moves")
        finally:
            config.PIN_TOLERANCE_BPS = original


def group_d() -> None:
    print(f"\n{LINE}\nD. REPLAY: Friday's run, from its own packet\n{LINE}")
    day = "2026-09-04"
    chains = ec.newest_chains(day)
    if not chains:
        # data/ is gitignored, so CI has none. A skip is the honest answer: the
        # test is an acceptance check against REAL stored data and there is
        # none to accept. Failing would be wrong, and passing would be a lie.
        SKIPPED.append(f"replay acceptance ({day}): no stored chains")
        print(f"  SKIP  no stored chains for {day} -- acceptance test needs "
              f"real data and CI has none")
        return

    inputs = sorted(chains.values())
    cutoff = "2026-09-05T00:00:00+00:00"

    def run_once() -> dict:
        return {sym: ec.compute_symbol(ec.load_chain(p), sym)
                for sym, p in sorted(chains.items())}

    first = run_once()
    packet = manifest.build_packet("run-friday", cutoff, cutoff, inputs, first)
    print(f"  packet: sha={packet['git_sha'][:12]} dirty={packet['code_dirty']} "
          f"manifest={packet['data_manifest_hash'][:12]} "
          f"files={packet['data_manifest']['file_count']} "
          f"output={packet['output_hash'][:12]}")

    second = run_once()
    replay = manifest.build_packet("run-friday-replay", cutoff, cutoff, inputs, second)

    check(replay["git_sha"] == packet["git_sha"], "same git SHA")
    check(replay["data_manifest_hash"] == packet["data_manifest_hash"],
          "same data manifest hash (inputs addressed by content, not path)")
    check(replay["metrics_registry_version"] == packet["metrics_registry_version"]
          and replay["source_registry_version"] == packet["source_registry_version"],
          "same registry versions")
    check(replay["output_hash"] == packet["output_hash"],
          "same output hash -- the run replays exactly")

    # And prove the canonicalisation is doing real work rather than hiding a
    # difference: the RAW outputs must differ, because both carry clocks.
    raw_same = manifest.output_hash(first, volatile=()) == \
        manifest.output_hash(second, volatile=())
    check(not raw_same,
          "raw outputs DIFFER (they carry computed_at/evaluated_at) -- so the "
          "match above is canonicalisation, not a no-op comparison")

    # A changed input must break the manifest, or it is not pinning anything.
    with tempfile.TemporaryDirectory() as td:
        clone = Path(td) / inputs[0].name
        clone.write_bytes(inputs[0].read_bytes() + b"\n")
        tampered = manifest.data_manifest([clone] + list(inputs[1:]))
        check(tampered["hash"] != packet["data_manifest_hash"],
              "a single changed input byte changes the manifest hash")

    if packet["code_dirty"]:
        print("  NOTE  the working tree is dirty, so this packet records "
              "code_dirty=1 and is honestly NOT replayable from the SHA alone")


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# I. BULK-REGISTERED SIGNALS RESOLVE (Phase 5a finding 5, fixed in P5-B)
# ---------------------------------------------------------------------------
def group_i(td: str) -> None:
    print(f"\n{LINE}\nI. SIGNAL FRESHNESS RESOLVES BULK-REGISTERED KEYS\n{LINE}")
    import datetime as dt
    import freshness                             # noqa: PLC0415
    obs_db = str(Path(td) / "fresh_obs.db")
    last = session.last_trading_session()
    old = last - dt.timedelta(days=14)
    # Knowable NOW, whatever the clock says. Stamped 21:00 UTC, today's bar is in
    # the future before the close, latest_as_of cannot see it, and the gate fails
    # every trading-day morning -- which is when CI ran 03bf3de. This group is
    # about bulk-key RESOLUTION; the session-timing rule is not what it tests.
    seen = min(dt.datetime.fromisoformat(f"{last.isoformat()}T21:00:00+00:00"),
               session.utc_now() - dt.timedelta(minutes=5)).isoformat()
    with observations.ObservationStore(obs_db) as st:
        st.write_many([
            {"registry_key": "yfinance.mkt_spy", "instrument": None,
             "observed_at": last.isoformat(),
             "available_at": seen,
             "value": 700.0, "source": "synthetic"},
            {"registry_key": "yfinance.mkt_qqq", "instrument": None,
             "observed_at": old.isoformat(),
             "available_at": f"{old.isoformat()}T21:00:00+00:00",
             "value": 500.0, "source": "synthetic"}])
    saved = observations.DEFAULT_DB
    observations.DEFAULT_DB = obs_db
    try:
        r = freshness.check_signals(["yfinance.mkt_spy"], "SPY")
        v = r["verdicts"][0]
        check(not r["blocked"] and not r["unknown"] and v["half_life"] == "session",
              f"yfinance.mkt_spy, a BULK-registered price key with a bar from the "
              f"latest completed session ({last}), resolves and passes "
              f"({v['reason']})")
        r = freshness.check_signals(["yfinance.mkt_qqq"], "QQQ")
        v = r["verdicts"][0]
        check(r["blocked"] and not r["unknown"] and "latest completed session"
              in v["reason"],
              f"yfinance.mkt_qqq with its newest bar outside its allowance "
              f"({old}) is BLOCKED as stale, not as unregistered ({v['reason']})")
        r = freshness.check_signals(["fred.anything"], "SPY")
        check(r["blocked"] and r["unknown"] == ["fred.anything"],
              "a key no bulk block has a member for is still unregistered -- a "
              "typo is not blamed on the pipeline")
        r = freshness.check_signals(["yfinance.mkt_nosuch"], "SPY")
        check(r["unknown"] == ["yfinance.mkt_nosuch"],
              "nor does the price prefix alone register a key")
    finally:
        observations.DEFAULT_DB = saved

    # THE SESSION RULE READS THE LATEST *COMPLETED* SESSION (1 Oct 2026). It
    # read last_trading_session(), which before the close on a trading day is
    # today, so yesterday's close -- the current vintage -- was blocked as stale
    # every morning. Pinned clocks and past-dated bars: true whenever this runs.
    def at(observed: str, seen: str, now: str) -> dict:
        db = str(Path(td) / f"clock_{observed}_{now[:13]}.db")
        with observations.ObservationStore(db) as st:
            st.write_many([{"registry_key": "yfinance.mkt_spy", "instrument": None,
                            "observed_at": observed, "available_at": seen,
                            "value": 700.0, "source": "synthetic"}])
        prev = observations.DEFAULT_DB
        observations.DEFAULT_DB = db
        try:
            return freshness.assess("yfinance.mkt_spy", "session", "SPY", now=now)
        finally:
            observations.DEFAULT_DB = prev
    v = at("2026-09-30", "2026-09-30T20:20:00+00:00", "2026-10-01T13:30:00+00:00")
    check(not v["stale"],
          f"09:30 ET Thu 1 Oct: Wednesday's close is fresh, not blocked for want "
          f"of a Thursday bar that cannot exist yet ({v['reason']})")
    v = at("2026-09-29", "2026-09-29T20:20:00+00:00", "2026-10-01T13:30:00+00:00")
    check(v["stale"] and "2026-09-30" in v["reason"],
          f"and Tuesday's close at that hour IS stale, naming Wednesday "
          f"({v['reason']})")
    v = at("2026-09-30", "2026-09-30T20:20:00+00:00", "2026-09-30T20:30:00+00:00")
    check(not v["stale"],
          f"16:30 ET Wed 30 Sep, after the EOD write but inside the close grace: "
          f"Wednesday's own bar is fresh, not stale for being newer than the "
          f"latest completed session ({v['reason']})")

    # AND THROUGH THE CLI, which is where finding 5 bit.
    reg_db = str(Path(td) / "fresh_reg.db")
    env = {**os.environ, "CHESTER_DB": obs_db}
    base = [sys.executable, str(REPO / "tools" / "decide.py"), "--db", reg_db,
            "record", "--instrument", "SPY", "--direction", "long",
            "--thesis", "t", "--edge-type", "positioning", "--horizon", "swing",
            "--invalidation", "below 760", "--dry-run", "--signals-used"]
    ok_run = subprocess.run(base + ["yfinance.mkt_spy"], capture_output=True,
                            text=True, cwd=str(REPO), env=env)
    check(ok_run.returncode == 0 and "DECISION_BLOCKED" not in ok_run.stdout,
          f"decide.py record citing yfinance.mkt_spy with a current bar is not "
          f"blocked (rc {ok_run.returncode})")
    bad_run = subprocess.run(base + ["yfinance.mkt_qqq"], capture_output=True,
                             text=True, cwd=str(REPO), env=env)
    check("DECISION_BLOCKED" in bad_run.stdout,
          "and citing yfinance.mkt_qqq, whose bar is past its allowance, is "
          "DECISION_BLOCKED")


# ---------------------------------------------------------------------------
# J. EL-1: THE PACKET FIELDS AND RED TEAM v0 (P5-B)
# ---------------------------------------------------------------------------
def group_j(td: str) -> None:
    print(f"\n{LINE}\nJ. EL-1: PACKET FIELDS, AND DECISION_OK REFUSED WITHOUT THEM\n{LINE}")
    import yaml
    from register import store as rs
    from register.store import PacketIncompleteError

    sp = yaml.safe_load((REPO / "config" / "setups.yaml").read_text(
        encoding="utf-8"))["setups"]
    check("unclassified" in sp and all(
              (v or {}).get("book") in ("A", "B", "C", "D")
              for k, v in sp.items() if k != "unclassified"),
          f"config/setups.yaml: {len(sp) - 1} setup families, each on a book, "
          f"plus `unclassified`")
    check({v["book"] for k, v in sp.items() if k != "unclassified"}
          == {"A", "B", "C", "D"},
          "every book the Doctrine names has at least one setup family")

    db = str(Path(td) / "el1.db")
    base = dict(instrument="SPY", direction="long", thesis="t",
                edge_type="positioning", horizon="swing", invalidation="below 760",
                book="B", expression_family="outright", leverage_form="none")
    fields = dict(falsifiers=["SPY settles below 760"],
                  counter_thesis="Dealers are short gamma and the tape can gap.")
    with Register(db) as reg:
        for drop in ("falsifiers", "counter_thesis"):
            f = {k: v for k, v in fields.items() if k != drop}
            raises(lambda f=f: reg.record(status="active", **base, **f),
                   PacketIncompleteError,
                   f"DECISION_OK without {drop} is refused at write time")
        raises(lambda: reg.record(status="active", **{**base, "invalidation": " "},
                                  **fields),
               PacketIncompleteError,
               "DECISION_OK with a blank invalidation is refused")
        raises(lambda: reg.record(status="active", **base,
                                  falsifiers=["  "], counter_thesis="x"),
               PacketIncompleteError,
               "a falsifier list of blanks is no falsifier")
        d = reg.record(status="active", setup_id="b_breakout", engine_id="operator",
                       horizon_alignment="aligned", review_changed="none",
                       **base, **fields)
        row = reg.get(d)
        check(row["status"] == "active" and json.loads(row["falsifiers"])
              == fields["falsifiers"] and row["setup_id"] == "b_breakout",
              "with falsifiers, invalidation and counter_thesis it is active, "
              "every field on the row")
        g = reg.record(status="active", gate_outcome="resize", **base)
        check(reg.get(g)["status"] == "draft",
              "a gate-held request without the fields lands as draft, not "
              "refused -- a draft is not DECISION_OK")
        bl = reg.record(status="active", blocked_reason="x: stale", **base)
        check(reg.get(bl)["status"] == "draft",
              "and so does a blocked request -- an abstention is still recorded")
        for kw, val in (("setup_id", "no_such_setup"), ("engine_id", "robot"),
                        ("review_changed", "tweaked"),
                        ("horizon_alignment", "sideways")):
            raises(lambda kw=kw, val=val: reg.record(
                       status="draft", **base, **{kw: val}), ValueError,
                   f"{kw}={val!r} is outside its vocabulary and refused")
        dr = reg.record(status="draft", **base)
        raises(lambda: reg.set_status(dr, "active"), PacketIncompleteError,
               "the in-place writer cannot promote a draft without the fields")
        dr2 = reg.record(status="draft", **base, **fields)
        reg.set_status(dr2, "active")
        check(reg.get(dr2)["status"] == "active",
              "and promotes one that has them")
        # A pre-P5-B row: active, no fields. Re-recording it while it stays
        # active describes an open position; it is not an entry.
        legacy = reg.record(status="active", becoming_active=False, **base)
        check(reg.get(legacy)["falsifiers"] is None
              and reg.get(legacy)["setup_id"] is None,
              "a pre-P5-B row keeps NULL fields -- no default is invented for it")
    check([rs.review_from_gate(o) for o in rs.GATE_OUTCOMES]
          == ["none", "resized", "restructured", "hedged", "delayed", "rejected"]
          and rs.review_from_gate("resize", "none") == "none",
          "the gate's verdict folds into review_changed; an explicit operator "
          "value wins")

    # horizon_alignment, from the trend dimension of the object, at entry.
    import importlib
    import regime
    decide = importlib.import_module("decide")
    saved = regime.latest
    try:
        for trend, direction, want in (("up", "long", "aligned"),
                                       ("up", "short", "counter"),
                                       ("down", "short", "aligned"),
                                       ("flat", "long", "neutral"),
                                       (None, "long", "neutral"),
                                       ("up", "hedge", "neutral")):
            regime.latest = (lambda t=trend: {"session": "2026-09-30",
                                              "dimensions": {"trend": {"state": t}}})
            got, why = decide.horizon_alignment(direction)
            check(got == want, f"trend {trend}, {direction} -> {want} ({why})")
        regime.latest = lambda: None
        check(decide.horizon_alignment("long")[0] == "neutral",
              "no stored object -> neutral, with the reason")
    finally:
        regime.latest = saved

    # THE CLI.
    obs_db = str(Path(td) / "fresh_obs.db")        # group I's fresh mkt_spy bar
    env = {**os.environ, "CHESTER_DB": obs_db}
    cli_db = str(Path(td) / "el1_cli.db")
    rec = [sys.executable, str(REPO / "tools" / "decide.py"), "--db", cli_db,
           "record", "--instrument", "SPY", "--direction", "long", "--thesis", "t",
           "--edge-type", "positioning", "--horizon", "swing",
           "--invalidation", "below 760", "--signals-used", "yfinance.mkt_spy",
           "--status", "active", "--book", "B", "--expression-family", "outright",
           "--leverage-form", "none", "--dry-run"]
    r = subprocess.run(rec, capture_output=True, text=True, cwd=str(REPO), env=env)
    check(r.returncode == 2 and "DECISION_OK needs --falsifier and --counter-thesis"
          in r.stdout,
          "decide.py record --status active with neither field is refused, both "
          "named")
    r = subprocess.run(rec + ["--falsifier", "SPY settles below 760",
                              "--counter-thesis", "The tape can gap lower.",
                              "--setup", "b_breakout"],
                       capture_output=True, text=True, cwd=str(REPO), env=env)
    check("REFUSED -- DECISION_OK" not in r.stdout
          and "setup_id        : b_breakout" in r.stdout
          and "alignment       :" in r.stdout,
          "with both it passes the EL-1 check and prints setup, alignment and "
          "the fields")
    with Register(cli_db) as reg:
        old = reg.record(status="draft", **base)
    sh = subprocess.run([sys.executable, str(REPO / "tools" / "decide.py"),
                         "--db", cli_db, "show", old],
                        capture_output=True, text=True, cwd=str(REPO), env=env)
    check(sh.stdout.count("not recorded") >= 6,
          "`show` on a row without the fields reads 'not recorded' for each "
          "of the six")

    # THE WEEKLY'S COUNTS. One decision and its successor are one entry; a
    # pre-P5-B row is not recorded, never `none`.
    from daily_cascade import weekly_payload as wp
    rows = [
        {"id": "a", "created_at": "2026-09-29T14:00", "superseded_by": "a2",
         "setup_id": "unclassified", "review_changed": "resized"},
        {"id": "a2", "created_at": "2026-09-30T14:00", "superseded_by": None,
         "setup_id": "unclassified", "review_changed": "resized"},
        {"id": "b", "created_at": "2026-09-30T15:00", "superseded_by": None,
         "setup_id": "b_breakout", "review_changed": "none"},
        {"id": "c", "created_at": "2026-09-30T16:00", "superseded_by": None,
         "setup_id": None, "review_changed": None},
        {"id": "d", "created_at": "2026-09-20T16:00", "superseded_by": None,
         "setup_id": "unclassified", "review_changed": "rejected"}]
    pf = wp.packet_fields_week(rows, "2026-09-28", "2026-10-02")
    check(pf["entries_this_week"] == 3 and pf["setup_unclassified"] == 1
          and pf["setup_not_recorded"] == 1 and pf["review_changed_not_none"] == 1
          and pf["review_changed_by_kind"] == {"resized": 1},
          f"the Weekly counts entries once (a successor is not a new entry), "
          f"`unclassified` 1, review_changed != none 1, pre-P5-B 1 not recorded, "
          f"last week's row excluded ({pf})")


def group_k(td: str) -> None:
    """INC-6 follow-up: the listing currency against the expression currency."""
    print(f"\n{LINE}\nK. THE CURRENCY GUARD -- a foreign listing is a currency "
          f"position (INC-6)\n{LINE}")
    import sqlite3
    from register import heat, store as rs
    from register.reconcile import reconcile_executions
    from register.store import CurrencyMismatchError

    db = str(Path(td) / "ccy.db")
    base = dict(direction="short", thesis="flatten the wrong-listing leg",
                edge_type="positioning", horizon="swing",
                invalidation="none -- flatten at the next open")
    with Register(db) as reg:
        # THE 30 SEP CASE: SPY on MEXI in pesos, against a dollar view.
        try:
            reg.record(instrument="SPY@MEXI.MXN", currency_exposure="unhedged", **base)
            bad("SPY@MEXI.MXN against a USD expression was recorded")
        except CurrencyMismatchError as exc:
            msg = str(exc)
            check("MXN" in msg and "USD" in msg,
                  f"the 30 Sep MEXI case is REFUSED at record, naming both "
                  f"currencies ({msg[:90]}...)")
        ok_id = reg.record(instrument="SPY@ARCA.USD", **base)
        check(bool(ok_id), "a USD listing against the USD expression is recorded")
        ov = reg.record(instrument="SPY@MEXI.MXN", currency_exposure="unhedged",
                        gate_override="operator: the peso exposure is intended",
                        **base)
        check(bool(ov), "the operator's override (--override-gate) is the way past "
                        "it, and it is recorded")
        mx = reg.record(instrument="SPY@MEXI.MXN", currency_exposure="unhedged",
                        expression_currency="MXN", **base)
        check((reg.get(mx) or {}).get("expression_currency") == "MXN",
              "declaring the expression in MXN, the MXN listing passes -- and the "
              "packet records it")
        check((reg.get(ok_id) or {}).get("expression_currency") == "USD",
              "a decision that declares nothing is recorded as USD")
        # A LEGACY peso draft (written before the guard) can be CLOSED, not
        # activated.
        reg.conn.execute("UPDATE decisions SET expression_currency = NULL "
                         "WHERE id = ?", (ov,))
        reg.conn.commit()
        legacy = reg.get(ov)
        keep = {k: legacy[k] for k in ("instrument", "direction", "thesis",
                                       "edge_type", "horizon", "invalidation",
                                       "currency_exposure")}
        try:
            reg.supersede(ov, status="active", book="B", falsifiers=["x"],
                          counter_thesis="y", expression_currency="USD", **keep)
            bad("a legacy peso draft was ACTIVATED against a USD expression")
        except CurrencyMismatchError:
            ok("activation is judged too: a legacy peso draft is refused when it "
               "would become active")
        # INC-8: the guard judges EVERY supersede, closing included -- a close
        # carrying an invented "USD" onto a peso listing is refused ...
        try:
            reg.supersede(ov, status="closed", close_reason="flatten",
                          expression_currency="USD", **keep)
            bad("INC-8: a close wrote USD onto a peso listing")
        except CurrencyMismatchError:
            ok("INC-8: a CLOSE is judged too -- a USD expression on a peso listing "
               "is refused at close as at entry")
        # ... and closing is still never trapped: the legacy row's EMPTY currency
        # carries forward as empty (or as the listing's own MXN), and both close.
        closed = reg.supersede(ov, status="closed", close_reason="flatten",
                               expression_currency=None, **keep)
        check(bool(closed) and (reg.get(closed) or {}).get("expression_currency")
              is None,
              "but an empty currency closes, and stays EMPTY -- never stored as "
              "USD, so a wrong-listing position is never trapped")

    # THE CLI, as a dry run: refused before anything else, exit 2.
    r = subprocess.run(
        [sys.executable, str(REPO / "tools" / "decide.py"), "--db", db, "record",
         "--instrument", "SPY@MEXI.MXN", "--direction", "short", "--thesis", "t",
         "--edge-type", "positioning", "--horizon", "swing",
         "--invalidation", "flatten", "--currency-exposure", "unhedged",
         "--signals-used", "yfinance.mkt_spy", "--dry-run"],
        capture_output=True, text=True, cwd=str(REPO),
        env={**os.environ, "CHESTER_DB": db})
    check(r.returncode == 2 and "CURRENCY MISMATCH" in r.stdout
          and "MXN" in r.stdout and "USD" in r.stdout,
          f"decide.py record --dry-run says REFUSED -- CURRENCY MISMATCH and "
          f"exits 2 (rc {r.returncode})")

    # RECONCILIATION: a peso fill against a dollar decision is a rule break.
    with Register(str(Path(td) / "ccy_rec.db")) as reg:
        reg.record(instrument="SPY@ARCA.USD", direction="long", thesis="t",
                   edge_type="positioning", horizon="swing", invalidation="below 760",
                   status="active", book="B", falsifiers=["below 760"],
                   counter_thesis="the tape can gap",
                   decision_time="2026-09-19T15:00:00+00:00")
        fill = {"exec_id": "fixture.mexi.1", "instrument": "SPY@MEXI.MXN",
                "symbol": "SPY", "side": "BOT", "qty": 100.0, "sec_type": "STK",
                "currency": "MXN", "exec_time": "2026-10-01T14:50:07+00:00"}
        usd_fill = {**fill, "exec_id": "fixture.arca.1",
                    "instrument": "SPY@ARCA.USD", "currency": "USD"}
        out = reconcile_executions(reg, [fill, usd_fill], "2026-10-01")
        kinds = {b["exec_id"]: b["kind"] for b in out["breaks"]}
        check(kinds.get("fixture.mexi.1") == "currency_mismatch",
              f"a fill in MXN against a decision expressed in USD becomes a rule "
              f"break of kind currency_mismatch ({kinds})")
        check("fixture.arca.1" not in kinds or
              kinds["fixture.arca.1"] != "currency_mismatch",
              "and the USD fill on the same decision is not one")
        rb = [b for b in reg.rule_breaks() if b["kind"] == "currency_mismatch"]
        check(len(rb) == 1, "the break is written to the register's rule_breaks")

    # THE MIGRATION: a register created before currency_mismatch existed.
    old = str(Path(td) / "ccy_old.db")
    kinds_old = tuple(k for k in rs.RULE_BREAK_KINDS if k != "currency_mismatch")
    con = sqlite3.connect(old)
    con.executescript(rs.SCHEMA.replace(repr(rs.RULE_BREAK_KINDS), repr(kinds_old)))
    con.execute("INSERT INTO rule_breaks (detected_at, session, kind, reason, source,"
                " dedupe_key) VALUES ('2026-09-30T00:00:00+00:00', '2026-09-30',"
                " 'side_mismatch', 'pre-existing', 'fixture', 'old-1')")
    con.commit()
    con.close()
    with Register(old) as reg:
        sql = reg.conn.execute("SELECT sql FROM sqlite_master WHERE name="
                               "'rule_breaks'").fetchone()[0]
        kept = [b["dedupe_key"] for b in reg.rule_breaks()]
        new = reg.write_rule_break(kind="currency_mismatch", session_day="2026-10-01",
                                   reason="fixture", dedupe_key="new-1",
                                   source="fixture")
        trig = {r[0] for r in reg.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND "
            "tbl_name='rule_breaks'")}
    check("currency_mismatch" in sql and kept == ["old-1"] and new,
          "a register created before the new kind is rebuilt in place: the "
          "constraint widened, the existing break kept, the new kind written")
    check({"rule_breaks_immutable_update", "rule_breaks_immutable_delete"} <= trig,
          "and its immutability triggers are back")

    # THE HEAT VIEW: converted at a stored rate it names, or not at all.
    with observations.ObservationStore(str(Path(td) / "fx.db")) as st:
        none = heat.to_usd(1395131.0, "MXN", st)
        st.write_many([{"registry_key": "fred.usd_mxn", "instrument": None,
                        "observed_at": "2026-09-30",
                        "available_at": "2026-09-30T21:00:00+00:00",
                        "value": 18.256, "source": "synthetic"}])
        got = heat.to_usd(1395131.0, "MXN", st)
        dec = {"id": "x", "instrument": "SPY@MEXI.MXN", "direction": "short",
               "notional_usd": 1395131.0, "expression_currency": "MXN",
               "book": "B"}
        ex = heat.exposure(dec, st, {})
    check(none["usd"] is None and "parity is not assumed" in none["reason"],
          "with no stored USD/MXN rate the heat view converts nothing and says so "
          "-- never parity")
    check(got["usd"] is not None and abs(got["usd"] - 1395131.0 / 18.256) < 0.01
          and got["series"] == "fred.usd_mxn" and got["observed_at"] == "2026-09-30",
          f"with one stored, 1,395,131 MXN is {got['usd']:,.2f} USD at "
          f"fred.usd_mxn 18.256 (2026-09-30), and the view names the rate")
    check(abs(ex["notional_usd"] - 1395131.0 / 18.256) < 0.01
          and ex["fx"]["currency"] == "MXN",
          "and a peso decision's exposure enters the heat view in dollars, "
          "converted")
    from altdata import config as acfg
    check(any(s.key == "usd_mxn" and s.fred_id == "DEXMXUS"
              for s in acfg.FRED_SIGNAL_SERIES),
          "USD/MXN (FRED DEXMXUS, pesos per dollar) is among the FX series pulled")


def group_l(td: str) -> None:
    """INC-6 follow-up: structured exits, and realised P&L computed from them."""
    print(f"\n{LINE}\nL. STRUCTURED EXITS -- the close carries its fill, the P&L is "
          f"computed\n{LINE}")
    from altdata import executions
    from register import pnl
    from daily_cascade import render as close_render

    db = str(Path(td) / "exits.db")
    env = {**os.environ, "CHESTER_DB": db}
    # SYNTHETIC FIGURES. A long of 100 at 100.00 (USD) and a short of -50 at
    # 2,000.00 (MXN), with Portfolio Truth before each exit and the closing fills.
    with observations.ObservationStore(db) as st:
        rows = []
        for inst, qty, avg, at in (("TEST@ARCA.USD", 100.0, 100.0,
                                    "2026-09-20T15:00:00+00:00"),
                                   ("TEST@MEXI.MXN", -50.0, 2000.0,
                                    "2026-09-20T15:00:00+00:00")):
            rows += [{"registry_key": "portfolio.position_qty", "instrument": inst,
                      "observed_at": at, "available_at": at, "value": qty,
                      "source": "ibkr_paper"},
                     {"registry_key": "portfolio.position_avg_cost",
                      "instrument": inst, "observed_at": at, "available_at": at,
                      "value": avg, "source": "ibkr_paper"}]
        rows.append({"registry_key": "fred.usd_mxn", "instrument": None,
                     "observed_at": "2026-09-21",
                     "available_at": "2026-09-21T21:00:00+00:00", "value": 20.0,
                     "source": "synthetic"})
        st.write_many(rows)
    with executions.ExecutionStore(db) as xs:
        xs.write_many([
            {"exec_id": "t.arca.1", "order_id": 7, "instrument": "TEST@ARCA.USD",
             "symbol": "TEST", "side": "SLD", "qty": 60, "price": 110.0,
             "currency": "USD", "sec_type": "STK",
             "exec_time": "2026-09-22T16:00:00+00:00"},
            {"exec_id": "t.arca.2", "order_id": 7, "instrument": "TEST@ARCA.USD",
             "symbol": "TEST", "side": "SLD", "qty": 40, "price": 112.5,
             "currency": "USD", "sec_type": "STK",
             "exec_time": "2026-09-22T16:00:05+00:00"},
            {"exec_id": "t.mexi.1", "order_id": 8, "instrument": "TEST@MEXI.MXN",
             "symbol": "TEST", "side": "BOT", "qty": 50, "price": 2100.0,
             "currency": "MXN", "sec_type": "STK",
             "exec_time": "2026-09-22T17:00:00+00:00"}])
    with Register(db) as reg:
        base = dict(thesis="t", edge_type="positioning", horizon="swing",
                    invalidation="i", book="B", falsifiers=["f"], counter_thesis="c",
                    decision_time="2026-09-19T15:00:00+00:00")
        long_id = reg.record(instrument="TEST@ARCA.USD", direction="long",
                             status="active", **base)
        short_id = reg.record(instrument="TEST@MEXI.MXN", direction="short",
                              status="active", currency_exposure="unhedged",
                              expression_currency="MXN", **base)
        for bad_kw, what in (({"exit_time": "2026-09-22 16:00"}, "a non-UTC time"),
                             ({"exit_price": -1.0}, "a negative price"),
                             ({"exit_currency": "pesos"}, "a free-text currency"),
                             ({"exit_currency": "USD", "exit_fx_to_usd": 0.9},
                              "a USD exit at an FX other than 1")):
            raises(lambda kw=bad_kw: reg.record(
                instrument="TEST@ARCA.USD", direction="long", status="closed",
                **{**base, **kw}), ValueError, f"an exit with {what} is refused")
        xrows = executions.ExecutionStore(db).all()
        with observations.ObservationStore(db) as st:
            e1 = pnl.exit_from_executions(reg.get(long_id), xrows, st)
            e2 = pnl.exit_from_executions(reg.get(short_id), xrows, st)
    check(e1 and e1["exit_price"] == 111.0 and e1["exit_time"].startswith(
              "2026-09-22T16:00:05") and e1["exit_currency"] == "USD"
          and e1["exit_fx_to_usd"] == 1.0,
          f"the closing fills of one order are one exit: 60 @ 110 and 40 @ 112.5 "
          f"-> {e1 and e1['exit_price']} USD at the last fill's time")
    check(e2 and e2["exit_price"] == 2100.0 and e2["exit_currency"] == "MXN"
          and abs((e2["exit_fx_to_usd"] or 0) - 0.05) < 1e-12,
          f"a peso close takes its FX from the stored USD/MXN (20.0 -> "
          f"{e2 and e2['exit_fx_to_usd']} USD per peso)")
    with observations.ObservationStore(db) as st:
        p1 = pnl.realised({"id": "a", "instrument": "TEST@ARCA.USD", **e1}, st)
        p2 = pnl.realised({"id": "b", "instrument": "TEST@MEXI.MXN", **e2}, st)
        p0 = pnl.realised({"id": "c", "instrument": "TEST@ARCA.USD"}, st)
    check(p1["pnl_local"] == 1100.0 and p1["pnl_usd"] == 1100.0,
          f"realised P&L is computed: (111 - 100) x 100 = {p1['pnl_local']:+,.2f} USD")
    check(p2["pnl_local"] == -5000.0 and p2["pnl_usd"] == -250.0,
          f"a short that rose is a loss, in its currency and in USD: (2,100 - "
          f"2,000) x -50 = {p2['pnl_local']:+,.2f} MXN = {p2['pnl_usd']:+,.2f} USD")
    check(p0["pnl_local"] is None and "exit not recorded" in p0["missing"],
          "with no exit there is no P&L, and it says so")

    # THE CLI: the dry run shows the exit and the P&L for confirmation.
    def cli(*a):
        return subprocess.run([sys.executable, str(REPO / "tools" / "decide.py"),
                               "--db", db, "set-status", *a],
                              capture_output=True, text=True, cwd=str(REPO), env=env)
    r = cli("--id", long_id, "--status", "closed", "--close-reason", "target",
            "--dry-run")
    check(r.returncode == 0 and "exit (from executions table" in r.stdout
          and "111" in r.stdout and "+1,100.00 USD" in r.stdout,
          "set-status --status closed --dry-run fills the exit from the "
          "executions table and shows the realised P&L for confirmation")
    r = cli("--id", long_id, "--status", "closed", "--close-reason", "target")
    with Register(db) as reg:
        succ = [d for d in reg.all() if d.get("status") == "closed"
                and d.get("instrument") == "TEST@ARCA.USD"]
    check(r.returncode == 0 and succ and succ[-1]["exit_price"] == 111.0
          and succ[-1]["exit_currency"] == "USD",
          "and the close is written with the four exit fields on the row")
    r = cli("--id", succ[-1]["id"], "--status", "closed", "--exit-price", "111",
            "--exit-time", "2026-09-22T16:00:05+00:00", "--dry-run")
    check("NO CHANGE" in r.stdout,
          "re-closing with the same exit is no change -- but a NEW exit is one")
    # --exit-fx ALONE keeps the fill's price and time: the peso back-fill case.
    with Register(db) as reg:
        s_rows = [d for d in reg.all() if d["id"] == short_id]
    r = cli("--id", short_id, "--status", "closed", "--close-reason", "flatten",
            "--exit-fx", "0.04", "--dry-run")
    check("2,100" in r.stdout and "2026-09-22T17:00:00" in r.stdout
          and "0.04" in r.stdout and "-200.00 USD" in r.stdout and s_rows,
          "--exit-fx alone keeps the fill's price and time and overrides only the "
          "rate: -5,000 MXN x 0.04 = -200.00 USD")
    with Register(db) as reg:
        lone = reg.record(instrument="NOFILL@ARCA.USD", direction="long",
                          status="active", **base)
    r = cli("--id", lone, "--status", "closed", "--dry-run")
    check("exit not recorded" in r.stdout,
          "a close with no fill and no flags is allowed, and prints 'exit not "
          "recorded'")

    # THE CLOSE AND THE WEEKLY print it.
    with Register(db) as reg, observations.ObservationStore(db) as st:
        closed = pnl.closes_in(reg.all(), "2026-09-22", "2026-09-22", st)
    html = close_render.closes_html(closed, "this week")
    check(any(c["pnl_local"] == 1100.0 for c in closed) and "+1,100.00 USD" in html,
          "the close report's and the Weekly's 'Closed' table shows the realised "
          "P&L, computed")
    src = (REPO / "daily_cascade" / "weekly_payload.py").read_text(encoding="utf-8")
    check("reg_pnl.closes_in(" in src, "and the Weekly's register block carries it")


def group_m(td: str) -> None:
    """INC-8: an empty currency carries forward empty; the guard judges every
    supersede; the corrective supersede leaves the chain's P&L unchanged."""
    print(f"\n{LINE}\nM. INC-8 -- NO INVENTED CURRENCY; THE GUARD ON EVERY SUPERSEDE\n{LINE}")
    from register import pnl
    db = str(Path(td) / "inc8.db")
    env = {**os.environ, "CHESTER_DB": db}
    # SYNTHETIC FIGURES ONLY: a short of -50 at 2,000.00 MXN, closed at 2,100.00
    # with USD/MXN at 20.0. The shape of the 1 Oct chain, none of its numbers.
    with observations.ObservationStore(db) as st:
        at = "2026-09-20T15:00:00+00:00"
        st.write_many([
            {"registry_key": "portfolio.position_qty", "instrument": "TEST@MEXI.MXN",
             "observed_at": at, "available_at": at, "value": -50.0,
             "source": "ibkr_paper"},
            {"registry_key": "portfolio.position_avg_cost",
             "instrument": "TEST@MEXI.MXN", "observed_at": at, "available_at": at,
             "value": 2000.0, "source": "ibkr_paper"}])
    base = dict(instrument="TEST@MEXI.MXN", direction="short", thesis="t",
                edge_type="positioning", horizon="swing", invalidation="i",
                book="B", falsifiers=["f"], counter_thesis="c",
                currency_exposure="unhedged",
                decision_time="2026-09-19T15:00:00+00:00")
    exit_kw = dict(exit_price=2100.0, exit_time="2026-09-22T17:00:00+00:00",
                   exit_currency="MXN", exit_fx_to_usd=0.05)
    with Register(db) as reg:
        act = reg.record(status="active", expression_currency="MXN", **base)
        # The 1 Oct bug, reproduced: a close written with "USD" on a peso listing.
        # Today's guard refuses that, so the fixture needs an override to make it.
        bad_head = reg.supersede(act, status="closed", close_reason="flatten",
                                 expression_currency="USD",
                                 gate_override="fixture: reproduces the 1 Oct row",
                                 **base, **exit_kw)
        head = reg.get(bad_head)
    with observations.ObservationStore(db) as st:
        before = pnl.realised(head, st)
    n0 = _count(db)

    def cli(*extra):
        return subprocess.run(
            [sys.executable, str(REPO / "tools" / "decide.py"), "--db", db,
             "set-status", "--id", bad_head, "--status", "closed",
             "--close-reason", "flatten", *extra],
            capture_output=True, text=True, cwd=str(REPO), env=env)
    r = cli("--expression-currency", "USD", "--dry-run")
    check(r.returncode == 2 and "CURRENCY MISMATCH" in r.stdout,
          f"set-status --dry-run is refused with the write: a USD expression on a "
          f"peso listing, at close (rc {r.returncode})")
    r = cli("--expression-currency", "MXN", "--dry-run")
    check(r.returncode == 0 and "USD -> MXN" in r.stdout and _count(db) == n0,
          f"the corrective supersede, as a dry run, shows USD -> MXN and writes "
          f"nothing (rc {r.returncode})")
    r = cli("--expression-currency", "MXN")
    with Register(db) as reg:
        new = reg.get(reg.get(bad_head)["superseded_by"] or "") or {}
        old_row = reg.get(bad_head)
    check(r.returncode == 0 and new.get("expression_currency") == "MXN"
          and old_row.get("expression_currency") == "USD",
          "for real: a NEW head in MXN, and the old head still says USD -- it is "
          "superseded, never edited")
    check(all(new.get(k) == head.get(k) for k in exit_kw)
          and new.get("status") == "closed",
          "the exit carries across unchanged: price, time, currency and fx")
    with observations.ObservationStore(db) as st:
        after = pnl.realised(new, st)
    check(before.get("pnl_local") == after.get("pnl_local") == -5000.0
          and before.get("pnl_usd") == after.get("pnl_usd") == -250.0,
          f"and the chain's realised P&L is identical before and after: "
          f"{before.get('pnl_local')} MXN / {before.get('pnl_usd')} USD, then "
          f"{after.get('pnl_local')} MXN / {after.get('pnl_usd')} USD")
    # An EMPTY currency carries forward from the listing's suffix, never as USD.
    with Register(db) as reg:
        legacy = reg.record(status="active", expression_currency=None, **base)
        check((reg.get(legacy) or {}).get("expression_currency") is None,
              "the register stores an empty expression currency as EMPTY, not USD")
    r = subprocess.run(
        [sys.executable, str(REPO / "tools" / "decide.py"), "--db", db,
         "set-status", "--id", legacy, "--status", "closed", "--close-reason",
         "flatten", "--exit-price", "2100", "--exit-time",
         "2026-09-22T17:00:00+00:00", "--exit-fx", "0.05"],
        capture_output=True, text=True, cwd=str(REPO), env=env)
    with Register(db) as reg:
        nxt = reg.get(reg.get(legacy)["superseded_by"] or "") or {}
    check(r.returncode == 0 and nxt.get("expression_currency") == "MXN"
          and "(from the listing's suffix)" in r.stdout,
          f"an empty one is taken from the listing's suffix on supersede -- MXN, "
          f"stated as such (rc {r.returncode}, got "
          f"{nxt.get('expression_currency')!r})")
    # RULED 2 OCT: nothing to compare is itself a refusal at activation.
    from register.store import CurrencyMismatchError
    bare = dict(base, instrument="TEST")
    with Register(db) as reg:
        draft = reg.record(status="draft", expression_currency=None, **bare)
        try:
            reg.supersede(draft, status="active", expression_currency=None, **bare)
            bad("a bare ticker with no expression currency was ACTIVATED")
        except CurrencyMismatchError as exc:
            ok(f"a bare ticker with no expression currency is refused at activation "
               f"-- the guard has nothing to compare ({str(exc)[:60]}...)")
        closed_bare = reg.supersede(draft, status="closed", close_reason="flatten",
                                    expression_currency=None, **bare)
        check(bool(closed_bare), "but it can still be closed: nothing is trapped")
        dollar = reg.record(status="draft", expression_currency="USD", **bare)
        act = reg.supersede(dollar, status="active", expression_currency="USD",
                            **bare)
        check(bool(act), "and a bare ticker that DECLARES its currency activates")
        draft2 = reg.record(status="draft", expression_currency=None, **bare)
    r = subprocess.run(
        [sys.executable, str(REPO / "tools" / "decide.py"), "--db", db,
         "set-status", "--id", draft2, "--status", "active", "--book", "B",
         "--dry-run"], capture_output=True, text=True, cwd=str(REPO), env=env)
    check(r.returncode == 2 and "nothing to compare" in r.stdout,
          f"decide.py set-status says so before its dry run returns (rc {r.returncode})")
    src_txt = (REPO / "tools" / "decide.py").read_text(encoding="utf-8")
    check('expression_currency") or "USD"' not in src_txt,
          "and decide.py no longer falls back to an invented USD on supersede")


def _count(db: str) -> int:
    import sqlite3
    with sqlite3.connect(db) as c:
        return c.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]


def main() -> int:
    print(f"{LINE}\nRegister and point-in-time validation   {session.describe()}\n{LINE}")
    # ignore_cleanup_errors: on Windows a SQLite file cannot be unlinked while
    # any connection to it is open, and a failing assertion can leave one.
    # The test result matters; the temp directory does not.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        db = str(Path(td) / "test.db")
        group_a(db)
        group_b(db)
        group_g(db)
        group_c(db)
        group_e(db, td)
        group_h(db)
        group_i(td)
        group_j(td)
        group_k(td)
        group_l(td)
        group_m(td)
    group_f()
    group_d()

    tail = f", {len(SKIPPED)} skipped" if SKIPPED else ""
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed{tail}")
    for s in SKIPPED:
        print(f"  SKIPPED: {s}")
    print(LINE)
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
