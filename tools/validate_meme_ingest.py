"""
chester-meme's packets in, as Book D drafts (altdata/meme_ingest.py;
meme-ingest-ledgers-1, 17 Oct 2026). A fixture drop, a fixture register, no live
store, no network, no model.

  A  THE DROP: a valid packet, its duplicate (the same packet_id under another
     date), a schema-invalid packet (a forbidden `size` key), a restricted packet
     (`restricted: true`), a blocklisted name under an alias (BN.TO, by root) and
     another under a clean-looking ticker (by its name), and a *.tmp -- one run
     gives exactly ONE draft, the right refusals and the invalid one skipped; a
     second run writes nothing.
  B  THE REGISTER'S DECISION TABLES ARE UNTOUCHED: every table but the ingest's
     own two is the same, row for row, before and after.
  C  THE SQLITE NET: the drafts table refuses a restricted instrument by trigger
     (whatever wrote it), a packet column never changes, and a draft is never
     deleted.
  D  THE CONTRACT: a manifest naming another schema version, or the same version
     with another SHA-256, stops the run before any packet is read; the drop is
     never written; the status line reads "meme drafts awaiting review: n
     (refused: m)".
  E  THE OPERATOR'S TOOL: decide.py's confirm (`record --meme-packet`) refuses a
     draft's mismatched instrument or direction; `meme-reject` moves only the
     review columns; both reject writes are on the deny list.
  F  THE WIRING: the 06:45 pass calls the ingest after its pulls, the 21:15 unit
     after a pull of main and is not in DEPLOY_TIMERS; the close and the anchor
     carry the one line.

    python tools/validate_meme_ingest.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import copy
import hashlib
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gate_tmp                   # noqa: E402  -- removed at exit

TD = Path(gate_tmp.mkdtemp("validate_meme_ingest_"))
os.environ["CHESTER_DB"] = str(TD / "chester.db")

from altdata import meme_ingest as mi  # noqa: E402

PASS = FAIL = 0
LINE = "=" * 78


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


def head(t: str) -> None:
    print(f"\n{LINE}\n{t}\n{LINE}")


def packet(ticker: str, figi: str, seed: str, **extra) -> dict:
    """A packet in the contract's shape (docs/interface/decision_packet.schema.json)."""
    pid = "pk-" + hashlib.sha256(f"{figi}|{seed}".encode()).hexdigest()[:20]
    p = {"schema_version": "1.0", "packet_id": pid, "as_of": "2026-10-16",
         "session": "pm", "generated_at": "2026-10-16T23:44:00Z", "book": "D",
         "security_id": figi, "ticker": ticker, "name": f"{ticker} Holdings",
         "venue": "XNAS", "cik": None, "direction": "long", "phase": "ignition",
         "transition": "dormant->ignition", "rule_version": "1.0.0",
         "feature_version": "1.0.0",
         "thesis": ["Volume and attention crossed their arms together."],
         "evidence": [{"source": "polygon.grouped", "kind": "rule_arm",
                       "label": "volume", "event_date": "2026-10-16",
                       "available_at": "2026-10-16T21:00:00Z",
                       "url": "https://example.invalid/evidence/1"}],
         "fuel": {"quality": "missing"},
         "spark": {"feature_version": "1.0.0", "why": "fixture", "arms": [],
                   "conditions": [], "features": {}},
         "flags": [], "quality": "ok",
         "quality_detail": {"scan_status": "ok", "stale_inputs": [], "missing_inputs": []},
         "expires": "2099-10-23", "status": "draft"}
    p.update(extra)
    return p


def write_drop(root: Path, version: str, sha: str) -> dict:
    day = root / "packets" / "2026-10-16"
    day.mkdir(parents=True, exist_ok=True)
    (root / "packets" / "2026-10-15").mkdir(parents=True, exist_ok=True)
    good = packet("ABCD", "BBG000ABCD12", "good")
    dup_dir = root / "packets" / "2026-10-15"
    bad = packet("EFGH", "BBG000EFGH12", "bad", size=100)          # no_sizing
    restricted = packet("IJKL", "BBG000IJKL12", "restricted", restricted=True)
    alias = packet("BN.TO", "BBG000BNTO12", "alias")                # the root, BN
    by_name = packet("QXYZ", "BBG000QXYZ12", "name",
                     name="Brookfield Renewable Partners L.P.")      # the name net
    out = {"good": good, "bad": bad, "restricted": restricted, "alias": alias,
           "by_name": by_name}
    for p in out.values():
        (day / f"{p['packet_id']}.json").write_text(json.dumps(p, indent=2),
                                                    encoding="utf-8")
    (dup_dir / f"{good['packet_id']}.json").write_text(json.dumps(good, indent=2),
                                                       encoding="utf-8")
    (day / "pk-ffffffffffffffffffff.json.tmp").write_text("{", encoding="utf-8")
    (root / "MANIFEST.json").write_text(json.dumps({
        "manifest_version": "1.0", "producer": "fixture",
        "schemas": {"decision_packet": {"version": version, "sha256": sha}}}),
        encoding="utf-8")
    return out


def table_dump(db: Path, skip: tuple) -> dict:
    conn = sqlite3.connect(str(db))
    try:
        names = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {n: sorted(map(repr, conn.execute(f'SELECT * FROM "{n}"').fetchall()))
                for n in names if n not in skip}
    finally:
        conn.close()


def drop_digest(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        h.update(p.relative_to(root).as_posix().encode())
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


def main() -> int:
    from register.store import Register
    schema, version, sha = mi.held_schema()
    db = TD / "chester.db"
    # The register's schema in a fixture database: every one of its tables is
    # dumped before and after, so "untouched" covers all of them.
    with Register(str(db)) as reg:
        reg.conn.execute("SELECT 1")
    root = TD / "drop"
    pk = write_drop(root, version, sha)
    before = table_dump(db, ("meme_drafts", "meme_refusals"))
    drop_before = drop_digest(root)

    head("A. ONE DRAFT, THE REFUSALS, THE SKIP; A SECOND RUN WRITES NOTHING")
    r = mi.ingest(str(root), str(db), now="2026-10-17T01:45:00+00:00")
    conn = sqlite3.connect(str(db))
    drafts = conn.execute("SELECT packet_id, ticker, review, ingested_at, evidence_urls "
                          "FROM meme_drafts").fetchall()
    refusals = {row[0]: row[1] for row in conn.execute(
        "SELECT packet_id, kind FROM meme_refusals")}
    conn.close()
    check(len(drafts) == 1 and drafts[0][0] == pk["good"]["packet_id"]
          and drafts[0][2] == "awaiting" and drafts[0][3] == "2026-10-17T01:45:00+00:00"
          and json.loads(drafts[0][4]) == ["https://example.invalid/evidence/1"],
          f"the drafts table gains exactly ONE row, the valid packet, keyed by packet_id, "
          f"point in time, with its evidence URLs ({len(drafts)} row(s))")
    check(r["seen"] == 1 and r["drafts"] == 1,
          "its duplicate (the same packet_id under another date) is a no-op")
    check(refusals.get(pk["restricted"]["packet_id"]) == "restricted"
          and refusals.get(pk["alias"]["packet_id"]) == "blocklist"
          and refusals.get(pk["by_name"]["packet_id"]) == "blocklist" and r["refused"] == 3,
          "refused, never stored as drafts: the restricted packet, BN.TO (the "
          "blocklist's root) and a clean ticker whose name is Brookfield Renewable")
    check(refusals.get(pk["bad"]["packet_id"]) == "schema" and r["invalid"] == 1
          and any(d["kind"] == "schema" and "size" in d["reason"] for d in r["detail"]),
          "the schema-invalid packet (a forbidden `size` key) is logged and skipped, "
          "never repaired")
    check(not any("ffffffffffffffffffff" in d["packet_id"] for d in r["detail"]),
          "a *.tmp file is never read")
    r2 = mi.ingest(str(root), str(db), now="2026-10-17T10:45:00+00:00")
    conn = sqlite3.connect(str(db))
    n_after = conn.execute("SELECT COUNT(*) FROM meme_drafts").fetchone()[0]
    n_ref = conn.execute("SELECT COUNT(*) FROM meme_refusals").fetchone()[0]
    conn.close()
    check(r2["drafts"] == 0 and r2["refused"] == 0 and r2["seen"] == 6
          and n_after == 1 and n_ref == 4,
          "a second run (the 06:45 after the 21:15) writes nothing: every packet seen")

    head("B. THE REGISTER'S DECISION TABLES ARE UNTOUCHED")
    after = table_dump(db, ("meme_drafts", "meme_refusals"))
    changed = [t for t in set(before) | set(after) if before.get(t) != after.get(t)]
    check(not changed and "decisions" in after and "decision_packets" in after,
          f"every register table but the ingest's two is the same row for row "
          f"({len(after)} tables; changed: {changed})")
    check(drop_digest(root) == drop_before, "the drop is never written: its files and "
                                            "bytes are as they were")

    head("C. THE SQLITE NET")
    conn = sqlite3.connect(str(db))
    try:
        row = list(conn.execute("SELECT * FROM meme_drafts").fetchone())
        cols = [d[0] for d in conn.execute("SELECT * FROM meme_drafts").description]
        forced = dict(zip(cols, row), packet_id="pk-00000000000000000000",
                      ticker="BN", instrument_norm="BN")
        try:
            conn.execute(f"INSERT INTO meme_drafts ({','.join(forced)}) VALUES "
                         f"({','.join('?' * len(forced))})", list(forced.values()))
            refused = False
        except sqlite3.DatabaseError as exc:
            refused = "Brookfield" in str(exc)
        check(refused, "a draft for a restricted instrument written around the Python "
                       "check is refused by the trigger")
        for sql, what in (("UPDATE meme_drafts SET ticker = 'X'", "a packet column"),
                          ("DELETE FROM meme_drafts", "a delete")):
            try:
                conn.execute(sql)
                ok = False
            except sqlite3.DatabaseError:
                ok = True
            check(ok, f"{what} is refused")
    finally:
        conn.rollback()
        conn.close()

    head("D. THE CONTRACT")
    for v, s, what in (("2.0", sha, "another schema version"),
                       (version, "0" * 64, "the same version, another SHA-256")):
        other = TD / f"drop_{v}_{s[:4]}"
        write_drop(other, v, s)
        rr = mi.ingest(str(other), str(TD / "other.db"))
        check(rr.get("stopped") and rr["drafts"] == 0 and rr["refused"] == 0,
              f"a manifest naming {what} stops the run before any packet "
              f"({rr.get('stopped', '')[:60]})")
    line = mi.status_line(str(db), today="2026-10-17")
    check(line == "meme drafts awaiting review: 1 (refused: 3)",
          f"the one line ({line})")
    check(mi.status_line(str(TD / "never.db")) is None,
          "before the ingest has run there is no line")

    head("E. THE OPERATOR'S TOOL")
    import argparse
    import decide
    with Register(str(db)) as reg:
        good = pk["good"]
        ns = argparse.Namespace(meme_packet=good["packet_id"], instrument="ABCE",
                                direction="long", book=None)
        _, why1 = decide.meme_draft_for(reg, ns)
        ns2 = argparse.Namespace(meme_packet=good["packet_id"], instrument="ABCD",
                                 direction="short", book=None)
        _, why2 = decide.meme_draft_for(reg, ns2)
        ns3 = argparse.Namespace(meme_packet=good["packet_id"], instrument="ABCD",
                                 direction="long", book=None)
        row3, why3 = decide.meme_draft_for(reg, ns3)
    check(why1 and "not the draft's" in why1 and why2 and "direction" in why2
          and row3 is not None and why3 is None,
          "the confirm refuses another instrument or direction, and accepts the "
          "draft's own")
    rc = decide.cmd_meme_reject(argparse.Namespace(db=str(db),
                                                   packet_id=good["packet_id"],
                                                   reason="fixture"))
    conn = sqlite3.connect(str(db))
    rev = conn.execute("SELECT review, review_note, ticker FROM meme_drafts").fetchone()
    conn.close()
    check(rc == 0 and rev == ("rejected", "fixture", "ABCD")
          and table_dump(db, ("meme_drafts", "meme_refusals")) == before,
          "meme-reject moves only the review columns; the decision tables stay as "
          "they were")
    st = json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))
    deny = " ".join(st["permissions"]["deny"])
    check("decide.py meme-reject" in deny and "decide_remote.sh meme-reject" in deny
          and "decide.py record" in deny,
          "the confirm (record) and the reject are on the deny list: the operator's")

    head("F. THE WIRING")
    fo = (REPO / "scripts" / "fetch_overnight.sh").read_text(encoding="utf-8")
    pulls = [m.start() for m in re.finditer(r"altdata\.feeds pull", fo)]
    check(pulls and fo.index("-m altdata.meme_ingest") > max(pulls),
          "the 06:45 pass calls the ingest after its pulls")
    wr = (REPO / "scripts" / "run_meme_ingest.sh").read_text(encoding="utf-8")
    tm = (REPO / "deploy" / "systemd" / "chester-meme-ingest.timer").read_text(encoding="utf-8")
    sv = (REPO / "deploy" / "systemd" / "chester-meme-ingest.service").read_text(encoding="utf-8")
    dr = (REPO / "scripts" / "deploy_remote.sh").read_text(encoding="utf-8")
    check(wr.index("git pull --ff-only") < wr.index("-m altdata.meme_ingest")
          and "21:15 America/New_York" in tm and "run_meme_ingest.sh" in sv
          and "ReadOnlyPaths=-%h/chester-meme" in sv
          and "chester-meme-ingest.timer" not in re.search(
              r'DEPLOY_TIMERS="([^"]*)"', dr, re.S).group(1),
          "the 21:15 unit runs the ingest after a pull of main, holds the drop "
          "read-only, and is not in DEPLOY_TIMERS")
    sc = (REPO / "daily_cascade" / "stack_close.py").read_text(encoding="utf-8")
    sr = (REPO / "daily_cascade" / "stack_render.py").read_text(encoding="utf-8")
    mp = (REPO / "daily_cascade" / "morning_payload.py").read_text(encoding="utf-8")
    mr = (REPO / "daily_cascade" / "morning_render.py").read_text(encoding="utf-8")
    check('ed["meme_line"] = meme_ingest.status_line' in sc and 'ed["meme_line"]' in sr
          and '"meme_line": _meme_line(db_path)' in mp and "payload['meme_line']" in mr,
          "the close and the anchor carry the one line")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
