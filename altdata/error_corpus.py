"""
The error corpus -- every graded miss, with what was said, what happened and what
was missing when it was said (Learning Loop v2, LL-3; B73).

    python -m altdata.error_corpus backfill --dry-run [--db PATH] [--as-of ISO]
    python -m altdata.error_corpus backfill           [--db PATH] [--as-of ISO]
    python -m altdata.error_corpus count              [--db PATH]

The brief's section 2.4a (docs/briefs/learning-loop-v2-brief-2026-10-25.md): the
code half of the critic. Code assembles it from stored evidence only; no model is
called here or anywhere it is read from (R-4: a model never attributes a miss).
It prints nowhere yet; the critic (LL-5) reads it.

WHAT IS A MISS, declared, not fitted:
  * a PROBABILITY ROW (the ledger's `probabilities`, resolved, live sources only)
    whose Brier is above the coin's 0.25, i.e. the forecast stood on the wrong
    side of one half. The margin is the Brier less 0.25, in Brier units.
  * a GRADE (altdata/grader.py, the current method) whose ruled R is below zero,
    or, where no R could be computed, whose return in the decision's own
    direction is below zero. The margin is that R, or that return in percent. A
    flat or hedge decision has neither and is never a miss.
A hit, an unresolved row and an ungraded decision write nothing.

WHAT WAS MISSING AT EMISSION. Three columns, each NULL where nothing recorded it
(NULL is "not recorded", never "nothing missing"):
  * absent_dimensions and awaiting_legs: from the market-state object the system
    held at the emission instant (regime.latest(as_of=emitted_at)): its
    `absent_dimensions` and its `absent_contradictions` (a contradiction row with
    a leg absent). Point in time: an object stored after the instant is not read.
  * missing_inputs: the ledger row's own field, written by its source at
    emission (probability_ledger.record's `missing_inputs`; NULL on rows written
    before it). A grade has none: the register records no such field.

APPEND-ONLY. One row per miss, keyed by what it is a miss of, so a second build
writes nothing; two triggers refuse UPDATE and DELETE.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Any, Optional

from . import observations, session

log = logging.getLogger("altdata.error_corpus")

COIN_BRIER = 0.25
DRY = "dryrun."
METHOD = "error-corpus-v1"

SCHEMA = """
CREATE TABLE IF NOT EXISTS error_corpus (
    corpus_id      TEXT PRIMARY KEY,    -- sha256(kind, ref_id)[:32]
    kind           TEXT NOT NULL CHECK (kind IN ('probability', 'decision')),
    source         TEXT NOT NULL,       -- the ledger source, or register:<book>
    ref_id         TEXT NOT NULL,       -- probability_id; or decision|horizon|graded_at
    emitted_at     TEXT NOT NULL,       -- the emission's as-of
    said_json      TEXT NOT NULL,       -- the stored row, as stored
    happened_json  TEXT NOT NULL,       -- the resolution or the grade
    margin         REAL NOT NULL,
    margin_unit    TEXT NOT NULL,       -- brier_over_coin | r_ruled | return_pct
    absent_dimensions TEXT,             -- JSON list from the object; NULL not recorded
    awaiting_legs  TEXT,                -- JSON list from the object; NULL not recorded
    missing_inputs TEXT,                -- JSON list from the source; NULL not recorded
    object_session TEXT,                -- the object read, or NULL when none was held
    recorded_at    TEXT NOT NULL,
    method_version TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS error_corpus_by_source ON error_corpus (source, emitted_at);

CREATE TRIGGER IF NOT EXISTS error_corpus_no_update
BEFORE UPDATE ON error_corpus
BEGIN SELECT RAISE(ABORT, 'the error corpus is append-only'); END;

CREATE TRIGGER IF NOT EXISTS error_corpus_no_delete
BEFORE DELETE ON error_corpus
BEGIN SELECT RAISE(ABORT, 'the error corpus is append-only'); END;
"""


def corpus_id(kind: str, ref: str) -> str:
    return hashlib.sha256(f"{kind}\x1f{ref}".encode()).hexdigest()[:32]


def _ro(db: Optional[str]) -> Optional[sqlite3.Connection]:
    p = Path(db or observations.DEFAULT_DB)
    if not p.exists():
        return None
    conn = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _has(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (table,)).fetchone() is not None


# ---------------------------------------------------------------------------
# The misses
# ---------------------------------------------------------------------------
def probability_miss(r: dict) -> Optional[dict]:
    if r.get("outcome") is None or str(r.get("source", "")).startswith(DRY):
        return None
    b = r.get("brier")
    if b is None:
        b = (float(r["probability"]) - int(r["outcome"])) ** 2
    if b <= COIN_BRIER:
        return None
    return {"kind": "probability", "source": r["source"],
            "ref_id": r["probability_id"], "emitted_at": r["emitted_at"],
            "said": {k: r.get(k) for k in (
                "probability_id", "source", "scenario_set", "claim", "probability",
                "emitted_at", "horizon_date", "resolution_criterion", "emitted_by",
                "method_version")},
            "happened": {k: r.get(k) for k in (
                "outcome", "resolved_at", "resolution_note", "brier")},
            "margin": float(b) - COIN_BRIER, "margin_unit": "brier_over_coin",
            "missing_inputs": r.get("missing_inputs")}


def decision_miss(g: dict) -> Optional[dict]:
    r, p = g.get("r_multiple_ruled"), g.get("return_pct")
    if isinstance(r, (int, float)):
        if r >= 0:
            return None
        margin, unit = float(r), "r_ruled"
    elif isinstance(p, (int, float)):
        if p >= 0:
            return None
        margin, unit = float(p), "return_pct"
    else:
        return None
    ref = f"{g['decision_id']}|{g['horizon']}|{g['graded_at']}"
    return {"kind": "decision",
            "source": f"register:{g.get('book') or '(no book recorded)'}",
            "ref_id": ref, "emitted_at": g.get("decision_time") or g["graded_at"],
            "said": {k: g.get(k) for k in (
                "decision_id", "instrument", "direction", "status", "operator_action",
                "thesis_state", "decision_time", "horizon", "horizon_date",
                "invalidation_text", "signals_used", "mechanism_group")},
            "happened": {k: g.get(k) for k in (
                "graded_at", "reference_price", "reference_date", "horizon_price",
                "horizon_price_date", "return_pct", "mae_close_pct",
                "invalidation_hit", "r_multiple", "r_multiple_ruled", "r_basis",
                "method_version")},
            "margin": margin, "margin_unit": unit, "missing_inputs": None}


def stored(as_of: str, db: Optional[str] = None) -> tuple[list[dict], list[dict]]:
    """(resolved ledger rows, current-method grades with their book), by as_of."""
    conn = _ro(db)
    if conn is None:
        return [], []
    try:
        rows: list[dict] = []
        if _has(conn, "probabilities"):
            rows = [dict(r) for r in conn.execute(
                "SELECT * FROM probabilities WHERE outcome IS NOT NULL "
                "AND resolved_at <= ? ORDER BY resolved_at", (as_of,))]
        grades: list[dict] = []
        if _has(conn, "grades"):
            from . import grader                                # noqa: PLC0415
            grades = [dict(r) for r in conn.execute(
                "SELECT * FROM grades WHERE method_version = ? AND graded_at <= ? "
                "ORDER BY graded_at", (grader.METHOD_VERSION, as_of))]
            if _has(conn, "decisions"):
                books = {str(r["id"]): r["book"] for r in conn.execute(
                    "SELECT id, book FROM decisions")}
                for g in grades:
                    g["book"] = books.get(str(g["decision_id"]))
    finally:
        conn.close()
    return rows, grades


def misses(as_of: str, db: Optional[str] = None) -> list[dict]:
    rows, grades = stored(as_of, db)
    out = [m for m in map(probability_miss, rows) if m]
    out += [m for m in map(decision_miss, grades) if m]
    return out


# ---------------------------------------------------------------------------
# What the system held at emission
# ---------------------------------------------------------------------------
def object_at(emitted_at: str, store: Any) -> Optional[dict]:
    import regime                                               # noqa: PLC0415
    try:
        return regime.latest(as_of=str(emitted_at), store=store)
    except Exception:                                         # noqa: BLE001
        return None


def at_emission(m: dict, objects) -> dict:
    """The object columns for one miss. `objects(emitted_at)` returns the
    market-state object held at that instant, or None."""
    obj = objects(m["emitted_at"]) if objects else None
    if not obj:
        return {"absent_dimensions": None, "awaiting_legs": None,
                "object_session": None}
    return {"absent_dimensions": json.dumps(sorted(obj.get("absent_dimensions") or [])),
            "awaiting_legs": json.dumps(sorted(obj.get("absent_contradictions") or [])),
            "object_session": obj.get("session")}


# ---------------------------------------------------------------------------
# The table
# ---------------------------------------------------------------------------
def ensure(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def write(conn: sqlite3.Connection, m: dict, extra: dict,
          recorded_at: Optional[str] = None) -> bool:
    cur = conn.execute(
        "INSERT OR IGNORE INTO error_corpus (corpus_id, kind, source, ref_id, "
        "emitted_at, said_json, happened_json, margin, margin_unit, "
        "absent_dimensions, awaiting_legs, missing_inputs, object_session, "
        "recorded_at, method_version) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (corpus_id(m["kind"], m["ref_id"]), m["kind"], m["source"], m["ref_id"],
         str(m["emitted_at"]), json.dumps(m["said"], sort_keys=True, default=str),
         json.dumps(m["happened"], sort_keys=True, default=str), m["margin"],
         m["margin_unit"], extra.get("absent_dimensions"), extra.get("awaiting_legs"),
         m.get("missing_inputs"), extra.get("object_session"),
         recorded_at or session.utc_iso(), METHOD))
    return cur.rowcount == 1


def backfill(db: Optional[str] = None, as_of: Optional[str] = None,
             dry_run: bool = True, objects=None) -> dict:
    """Every stored miss by `as_of` into the corpus. Idempotent: a miss already
    held writes nothing. A dry run writes nothing at all."""
    as_of = as_of or session.utc_iso()
    found = misses(as_of, db)
    out = {"as_of": as_of, "dry_run": dry_run, "misses": len(found),
           "by_kind": {k: sum(1 for m in found if m["kind"] == k)
                       for k in ("probability", "decision")},
           "written": 0, "already": 0}
    if dry_run or not found:
        return out
    st = None
    if objects is None:
        st = observations.ObservationStore(db)
        cache: dict[str, Optional[dict]] = {}

        def objects(at: str) -> Optional[dict]:
            if at not in cache:
                cache[at] = object_at(at, st)
            return cache[at]
    conn = sqlite3.connect(str(Path(db or observations.DEFAULT_DB)))
    try:
        conn.execute("PRAGMA busy_timeout = 5000")
        ensure(conn)
        for m in found:
            if write(conn, m, at_emission(m, objects)):
                out["written"] += 1
            else:
                out["already"] += 1
        conn.commit()
    finally:
        conn.close()
        if st is not None:
            st.close()
    return out


def count(db: Optional[str] = None) -> int:
    conn = _ro(db)
    if conn is None:
        return 0
    try:
        if not _has(conn, "error_corpus"):
            return 0
        return int(conn.execute("SELECT COUNT(*) FROM error_corpus").fetchone()[0])
    finally:
        conn.close()


def rows(db: Optional[str] = None) -> list[dict]:
    """The corpus, read-only, for the critic (LL-5)."""
    conn = _ro(db)
    if conn is None:
        return []
    try:
        if not _has(conn, "error_corpus"):
            return []
        return [dict(r) for r in conn.execute(
            "SELECT * FROM error_corpus ORDER BY emitted_at")]
    finally:
        conn.close()


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m altdata.error_corpus")
    ap.add_argument("what", choices=("backfill", "count"))
    ap.add_argument("--db")
    ap.add_argument("--as-of")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "count":
        print(f"error_corpus rows: {count(a.db)}")
        return 0
    print(json.dumps(backfill(a.db, a.as_of, dry_run=a.dry_run), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
