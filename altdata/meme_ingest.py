"""
chester-meme's packets in, as Book D drafts -- the packet ingest of the interface
contract (docs/interface/README-interface.md, "What the main repo needs to build",
item 2; the 11 Oct interface spec, schema s3). meme-ingest-ledgers-1, 17 Oct 2026.

    python -m altdata.meme_ingest              # ingest the drop, print a summary
    python -m altdata.meme_ingest --dry-run    # read and decide, write nothing
    python -m altdata.meme_ingest status       # the one line the reports print

WHEN. After chester-meme's scans have finished writing: the 21:45 ET pass
(chester-meme-ingest.timer, after the 19:30 evening scan, which is done by about
19:45, and the contract's "after 20:15") and the 06:45 overnight pass
(scripts/fetch_overnight.sh, after its pulls; the 06:30 morning scan is done by
06:45, and the contract's read is "before 07:00").

WHERE. The drop directory is $CHESTER_MEME_DROP, else ~/chester-meme/drop (the
meme's checkout on the box, user mode). This module READS it and never writes
into it: no file is moved, renamed, deleted or created there.

WHAT HAPPENS TO EACH PACKET, in order:
  1. drop/MANIFEST.json is read first. Its decision_packet schema must be the one
     this repo holds (docs/interface/decision_packet.schema.json): the same
     version AND the same SHA-256 over the file with LF endings. A different
     schema means this reader's copy is stale; nothing is ingested and the run
     says so, rather than validate against the wrong contract.
  2. drop/packets/YYYY-MM-DD/pk-*.json, skipping *.tmp (the writer's atomic
     rename) and the archive.
  3. SEEN BEFORE -- its packet_id already a draft or a logged refusal -- is a
     no-op. A packet is immutable and keyed by packet_id, so a second sighting
     writes nothing.
  4. RESTRICTED -- `restricted: true` (the field the meme's packets carry since 17
     Oct 2026) or a `restricted:*` flag -- is REFUSED: logged with its reason,
     never stored as a draft.
  5. THE BLOCKLIST -- the system's Brookfield rule (register/instruments.py, the
     register's own), applied to the ticker, the name and the security id
     whatever the packet says, so an alias (BN.TO, "Brookfield Renewable", a
     share-class tail) is caught by root or by name -- REFUSED likewise. The
     drafts table carries the same rule a second time in SQLite: a trigger over
     the register's restricted_instruments refuses the insert.
  6. THE SCHEMA -- jsonschema, Draft 2020-12, formats checked -- a packet that
     fails is logged and skipped, NEVER repaired. `restricted`, the one field
     announced since schema 1.0 was cut, is checked as a boolean and set aside
     before the 1.0 validation (see the notes' message to the meme session).
  7. Otherwise: ONE ROW in `meme_drafts`, keyed by packet_id, point in time
     (ingested_at, the write instant; the packet's own generated_at and as_of are
     kept), with security_id, direction, expires, quality and the evidence URLs,
     and the whole packet as written. NEVER a register decision: the decisions,
     their packets and their status are the operator's, through tools/decide.py
     (`record --meme-packet` to confirm, `meme-reject` to reject).

THE ONE LINE. The close and the 07:00 anchor print
"meme drafts awaiting review: n (refused: m)" -- n drafts not yet confirmed or
rejected and not expired, m packets refused (restricted or blocklisted) in the
last seven days. Nothing else about a draft prints until the operator confirms it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import logging
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO / "docs" / "interface" / "decision_packet.schema.json"
DEFAULT_DROP = "~/chester-meme/drop"
DROP_VAR = "CHESTER_MEME_DROP"
REFUSED_WINDOW_DAYS = 7
# The fields announced after schema 1.0 was cut, each with the type it must have.
# A field here is checked, then set aside for the 1.0 validation; anything else
# unknown fails the schema, as the contract says.
EXTENSIONS = {"restricted": bool}

TABLES = """
CREATE TABLE IF NOT EXISTS meme_drafts (
    packet_id        TEXT PRIMARY KEY,
    as_of            TEXT NOT NULL,
    session          TEXT NOT NULL,
    generated_at     TEXT NOT NULL,
    security_id      TEXT NOT NULL,
    ticker           TEXT NOT NULL,
    instrument_norm  TEXT NOT NULL,
    direction        TEXT NOT NULL CHECK (direction IN ('long', 'short')),
    phase            TEXT NOT NULL,
    transition       TEXT NOT NULL,
    rule_version     TEXT NOT NULL,
    expires          TEXT NOT NULL,
    quality          TEXT NOT NULL,
    evidence_urls    TEXT NOT NULL,
    packet_json      TEXT NOT NULL,
    packet_sha256    TEXT NOT NULL,
    source_file      TEXT NOT NULL,
    ingested_at      TEXT NOT NULL,
    review           TEXT NOT NULL DEFAULT 'awaiting'
                     CHECK (review IN ('awaiting', 'confirmed', 'rejected')),
    reviewed_at      TEXT,
    decision_id      TEXT,
    review_note      TEXT
);
CREATE TABLE IF NOT EXISTS meme_refusals (
    packet_id      TEXT NOT NULL,
    kind           TEXT NOT NULL CHECK (kind IN ('restricted', 'blocklist', 'schema', 'read')),
    reason         TEXT NOT NULL,
    source_file    TEXT NOT NULL,
    packet_sha256  TEXT NOT NULL,
    seen_at        TEXT NOT NULL,
    PRIMARY KEY (packet_id, packet_sha256)
);
-- THE BLOCKLIST'S SECOND NET (the register's own pattern): no draft for a
-- restricted instrument, whatever wrote it.
CREATE TRIGGER IF NOT EXISTS meme_drafts_block_restricted
BEFORE INSERT ON meme_drafts
WHEN EXISTS (SELECT 1 FROM restricted_instruments WHERE norm_ticker = NEW.instrument_norm)
BEGIN SELECT RAISE(ABORT, 'restricted instrument: no draft may be written for the Brookfield complex'); END;
-- A packet is evidence: what was ingested never changes. Only the review columns
-- move, and only the operator's tool moves them.
CREATE TRIGGER IF NOT EXISTS meme_drafts_packet_immutable
BEFORE UPDATE OF packet_id, as_of, session, generated_at, security_id, ticker,
    instrument_norm, direction, phase, transition, rule_version, expires, quality,
    evidence_urls, packet_json, packet_sha256, source_file, ingested_at ON meme_drafts
BEGIN SELECT RAISE(ABORT, 'a meme draft''s packet is immutable'); END;
CREATE TRIGGER IF NOT EXISTS meme_drafts_no_delete
BEFORE DELETE ON meme_drafts
BEGIN SELECT RAISE(ABORT, 'meme drafts are never deleted'); END;
CREATE TRIGGER IF NOT EXISTS meme_refusals_immutable
BEFORE UPDATE ON meme_refusals
BEGIN SELECT RAISE(ABORT, 'meme_refusals is immutable'); END;
"""


def drop_dir(arg: Optional[str] = None) -> Path:
    return Path(os.path.expanduser(arg or os.environ.get(DROP_VAR) or DEFAULT_DROP))


def lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def held_schema() -> tuple[dict, str, str]:
    """(the schema, its version, its LF SHA-256) -- the copy this repo holds."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    version = schema["properties"]["schema_version"]["const"]
    return schema, version, lf_sha256(SCHEMA_PATH)


def manifest_fault(manifest: Optional[dict], version: str, sha: str) -> Optional[str]:
    """None when the manifest names the schema this repo holds, else why not."""
    if manifest is None:
        return "drop/MANIFEST.json is absent or unreadable"
    s = ((manifest.get("schemas") or {}).get("decision_packet") or {})
    if str(s.get("version")) != version:
        return (f"the manifest names decision_packet schema {s.get('version')!r}; this "
                f"repo holds {version!r} (docs/interface): update the copy first")
    if s.get("sha256") and s["sha256"] != sha:
        return ("the manifest's decision_packet schema differs from this repo's copy "
                "(same version, different SHA-256): update the copy first")
    return None


def schema_faults(packet: dict, schema: dict) -> list[str]:
    import jsonschema                                           # noqa: PLC0415
    body = dict(packet)
    out = []
    for k, typ in EXTENSIONS.items():
        if k in body:
            if not isinstance(body[k], typ):
                out.append(f"{k}: must be {typ.__name__}")
            body.pop(k)
    v = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    out += [f"{'/'.join(str(p) for p in e.absolute_path) or '(top)'}: {e.message[:160]}"
            for e in sorted(v.iter_errors(body), key=lambda e: list(e.absolute_path))]
    return out


def restriction(packet: dict, rules: Any) -> Optional[tuple[str, str]]:
    """(kind, reason) when the packet may not become a draft, else None."""
    if packet.get("restricted") is True:
        return "restricted", "the packet carries restricted: true"
    flags = [f for f in packet.get("flags") or [] if str(f).startswith("restricted:")]
    if flags:
        return "restricted", f"the packet carries {flags[0]}"
    for probe in (packet.get("ticker"), packet.get("name"), packet.get("security_id")):
        hit = rules.check(probe) if probe else None
        if hit:
            return "blocklist", (f"{probe!r} is on the Brookfield blocklist "
                                 f"({hit.get('entity')}, matched on {hit.get('matched_on')})")
    return None


def _open(db_path: Optional[str]):
    """The register's database, through the register itself: its open mirrors the
    blocklist into restricted_instruments, which the drafts trigger reads. The
    decision tables are not written here."""
    from register.store import Register                         # noqa: PLC0415
    reg = Register(db_path)
    reg.conn.executescript(TABLES)
    reg.conn.commit()
    return reg


def ingest(drop: Optional[str] = None, db_path: Optional[str] = None,
           dry_run: bool = False, now: Optional[str] = None) -> dict:
    root = drop_dir(drop)
    now = now or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    out: dict = {"drop": str(root), "drafts": 0, "seen": 0, "refused": 0,
                 "invalid": 0, "unreadable": 0, "dry_run": dry_run, "detail": []}
    schema, version, sha = held_schema()
    manifest = None
    try:
        manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    fault = manifest_fault(manifest, version, sha)
    if fault:
        out["stopped"] = fault
        log.warning("meme ingest: nothing ingested -- %s (%s)", fault, root)
        return out
    files = sorted(p for p in (root / "packets").glob("*/pk-*.json")
                   if not p.name.endswith(".tmp"))
    reg = _open(db_path)
    try:
        conn = reg.conn
        seen = {r[0] for r in conn.execute("SELECT packet_id FROM meme_drafts")}
        seen |= {r[0] for r in conn.execute("SELECT packet_id FROM meme_refusals")}
        for f in files:
            raw = f.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            pid = f.stem
            if pid in seen:
                out["seen"] += 1
                continue
            try:
                packet = json.loads(raw.decode("utf-8"))
                if not isinstance(packet, dict):
                    raise ValueError("not a JSON object")
            except (UnicodeDecodeError, ValueError) as exc:
                kind, reason = "read", f"unreadable: {exc}"[:300]
            else:
                if packet.get("packet_id") != pid:
                    kind, reason = "schema", (f"packet_id {packet.get('packet_id')!r} "
                                              f"is not the file's name {pid!r}")
                else:
                    r = restriction(packet, reg.restrictions)
                    if r:
                        kind, reason = r
                    else:
                        faults = schema_faults(packet, schema)
                        kind, reason = ("schema", "; ".join(faults[:3])) if faults else (None, None)
            rel = f.relative_to(root).as_posix()
            if kind is not None:
                out["refused" if kind in ("restricted", "blocklist") else
                    "invalid" if kind == "schema" else "unreadable"] += 1
                out["detail"].append({"packet_id": pid, "kind": kind, "reason": reason})
                log.warning("meme ingest: %s %s -- %s (%s)", kind.upper(), pid, reason, rel)
                if not dry_run:
                    conn.execute("INSERT OR IGNORE INTO meme_refusals (packet_id, kind, "
                                 "reason, source_file, packet_sha256, seen_at) VALUES "
                                 "(?,?,?,?,?,?)", (pid, kind, reason, rel, digest, now))
                seen.add(pid)
                continue
            from register.instruments import normalise          # noqa: PLC0415
            row = (pid, packet["as_of"], packet["session"], packet["generated_at"],
                   packet["security_id"], packet["ticker"], normalise(packet["ticker"]),
                   packet["direction"], packet["phase"], packet["transition"],
                   packet["rule_version"], packet["expires"], packet["quality"],
                   json.dumps([e["url"] for e in packet["evidence"]]),
                   raw.decode("utf-8"), digest, rel, now)
            if not dry_run:
                try:
                    conn.execute(
                        "INSERT INTO meme_drafts (packet_id, as_of, session, generated_at, "
                        "security_id, ticker, instrument_norm, direction, phase, transition, "
                        "rule_version, expires, quality, evidence_urls, packet_json, "
                        "packet_sha256, source_file, ingested_at) VALUES "
                        "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", row)
                except sqlite3.DatabaseError as exc:
                    # The trigger's net: a restricted instrument the Python check
                    # did not name still never becomes a draft.
                    out["refused"] += 1
                    reason = f"refused by the register's trigger: {exc}"
                    out["detail"].append({"packet_id": pid, "kind": "blocklist",
                                          "reason": reason})
                    log.warning("meme ingest: BLOCKLIST %s -- %s", pid, reason)
                    conn.execute("INSERT OR IGNORE INTO meme_refusals (packet_id, kind, "
                                 "reason, source_file, packet_sha256, seen_at) VALUES "
                                 "(?,?,?,?,?,?)", (pid, "blocklist", reason, rel, digest, now))
                    seen.add(pid)
                    continue
            out["drafts"] += 1
            out["detail"].append({"packet_id": pid, "kind": "draft",
                                  "ticker": packet["ticker"],
                                  "direction": packet["direction"]})
            seen.add(pid)
        if not dry_run:
            conn.commit()
    finally:
        reg.close()
    log.info("meme ingest: %d draft(s), %d seen, %d refused, %d invalid, %d unreadable",
             out["drafts"], out["seen"], out["refused"], out["invalid"], out["unreadable"])
    return out


def status_line(db_path: Optional[str] = None, today: Optional[str] = None) -> Optional[str]:
    """"meme drafts awaiting review: n (refused: m)" -- None before the ingest has
    ever run (no table), or when the store cannot be read. Read-only."""
    from register.store import DEFAULT_DB                       # noqa: PLC0415
    path = Path(db_path or DEFAULT_DB)
    if not path.exists():
        return None
    today = today or dt.date.today().isoformat()
    since = (dt.date.fromisoformat(today[:10])
             - dt.timedelta(days=REFUSED_WINDOW_DAYS)).isoformat()
    try:
        conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        try:
            n = conn.execute("SELECT COUNT(*) FROM meme_drafts WHERE review = 'awaiting' "
                             "AND expires >= ?", (today[:10],)).fetchone()[0]
            m = conn.execute("SELECT COUNT(DISTINCT packet_id) FROM meme_refusals WHERE "
                             "kind IN ('restricted', 'blocklist') AND seen_at >= ?",
                             (since,)).fetchone()[0]
        finally:
            conn.close()
    except sqlite3.Error:
        return None
    return f"meme drafts awaiting review: {n} (refused: {m})"


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description="Ingest chester-meme's packets as Book D drafts")
    ap.add_argument("cmd", nargs="?", default="ingest", choices=("ingest", "status"))
    ap.add_argument("--drop", default=None, help=f"the drop directory (${DROP_VAR})")
    ap.add_argument("--db", default=None, help="the register's database")
    ap.add_argument("--dry-run", action="store_true", help="decide, write nothing")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if a.cmd == "status":
        print(status_line(a.db) or "meme ingest has not run here")
        return 0
    r = ingest(a.drop, a.db, dry_run=a.dry_run)
    if r.get("stopped"):
        print(f"meme ingest: nothing ingested -- {r['stopped']}")
        return 0
    print(f"meme ingest{' (dry run)' if a.dry_run else ''}: {r['drafts']} draft(s), "
          f"{r['seen']} already seen, {r['refused']} refused, {r['invalid']} schema-invalid, "
          f"{r['unreadable']} unreadable -- {r['drop']}")
    for d in r["detail"]:
        print(f"  {d['kind']:<10} {d['packet_id']}  {d.get('reason') or d.get('ticker', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
