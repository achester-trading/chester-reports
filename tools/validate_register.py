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

from altdata import observations, session   # noqa: E402
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
