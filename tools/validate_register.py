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

import sqlite3
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from altdata import config, observations, session  # noqa: E402
from register import instruments, manifest  # noqa: E402
from register.store import Register, RestrictedInstrumentError  # noqa: E402
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
    ):
        raises(lambda s=bad_sym: reg.record(instrument=s, **base),
               RestrictedInstrumentError, f"refused {bad_sym!r} -- {why}")

    n_blocked = len(reg.blocked_attempts())
    check(n_blocked == 9, f"every refusal is logged ({n_blocked} attempts recorded)")

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
def group_e(db_path: str) -> None:
    print(f"\n{LINE}\nE. THE DECISION CLI\n{LINE}")
    import subprocess
    def run_cli(*a):
        return subprocess.run([sys.executable, str(REPO / "tools" / "decide.py"),
                               "--db", db_path, *a],
                              capture_output=True, text=True, cwd=str(REPO))

    ok_args = ["record", "--instrument", "SPY", "--direction", "long",
               "--thesis", "t", "--edge-type", "positioning",
               "--horizon", "swing", "--invalidation", "below 760",
               # Signals that ARE fresh, so this exercises the clean path
               # rather than accidentally testing the block.
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
def main() -> int:
    print(f"{LINE}\nRegister and point-in-time validation   {session.describe()}\n{LINE}")
    # ignore_cleanup_errors: on Windows a SQLite file cannot be unlinked while
    # any connection to it is open, and a failing assertion can leave one.
    # The test result matters; the temp directory does not.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        db = str(Path(td) / "test.db")
        group_a(db)
        group_b(db)
        group_c(db)
        group_e(db)
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
