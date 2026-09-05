"""
The decision register, and the immutable packets behind it.

Architecture 26.2 #4: every serious recommendation, abstention, operator
TAKE/DECLINE/MODIFY and market snapshot is logged immediately. 26.2 #3: a
material recommendation carries a packet from which the run REPLAYS EXACTLY.

-----------------------------------------------------------------------------
WHAT IS ENFORCED HERE RATHER THAN ASKED FOR NICELY
-----------------------------------------------------------------------------

THE BROOKFIELD RESTRICTION, at write time, in two places.

    1. Register.record() consults config/tracked_entities.yaml and raises
       RestrictedInstrumentError. The attempt is logged to blocked_attempts
       before the raise, so a refusal leaves a record rather than a silence.
    2. A BEFORE INSERT trigger on `decisions` raises regardless of who is
       inserting -- including a raw sqlite3 connection that never imports this
       module.

The second is not redundancy for its own sake. Enforcement that lives only in
one function is enforcement anyone can walk around by opening the database, and
the architecture's line is that a narrative instruction is a suggestion while a
schema constraint is a rule. So it is literally a schema constraint.

IMMUTABILITY of decision_packets, by trigger on UPDATE and DELETE. A packet
that can be edited is not evidence of anything.

REVISION CREATES A NEW RECORD. Part 7: overwriting destroys the grading trail.
A superseded decision is frozen by trigger; supersede() writes a new row and
points the old one at it, which is the only mutation the old row ever accepts.

CLOSED VOCABULARIES as CHECK constraints -- direction, horizon, status,
operator_action, thesis_state. A typo becomes a new category otherwise, and a
new category silently becomes a new bucket in every downstream count.

-----------------------------------------------------------------------------
HORIZONS ARE PART 7's, NOT INVENTED HERE
-----------------------------------------------------------------------------

intraday / swing / positional / strategic / structural. The taxonomy is the
absorption mechanism for the whole report system -- thirteen documents stay
thirteen documents because every report writes into one register with an
explicit horizon. Free text here would dissolve that.

`status` (draft/active/closed/declined) and `thesis_state`
(INTACT/STRAINED/INVALIDATED) are DIFFERENT AXES and both are kept. A decision
can be active and STRAINED. Collapsing them loses exactly the distinction Part 7
grades on: a thesis exited early that would have worked is a different failure
from a thesis that was wrong.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Optional

import sys

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import session          # noqa: E402
from register import instruments     # noqa: E402

DEFAULT_DB = os.environ.get("CHESTER_DB", "data/chester.db")

DIRECTIONS = ("long", "short", "flat", "hedge")
HORIZONS = ("intraday", "swing", "positional", "strategic", "structural")
STATUSES = ("draft", "active", "closed", "declined")
OPERATOR_ACTIONS = ("TAKE", "DECLINE", "MODIFY")
THESIS_STATES = ("INTACT", "STRAINED", "INVALIDATED")


class RestrictedInstrumentError(Exception):
    """Raised when a decision names an instrument the register refuses.

    Deliberately not a warning and not a filtered-out row. The architecture:
    "a recommendation tagged to a restricted entity is rejected, not warned."
    """


SCHEMA = f"""
CREATE TABLE IF NOT EXISTS decisions (
    id               TEXT PRIMARY KEY,
    created_at       TEXT NOT NULL,
    decision_time    TEXT NOT NULL,
    instrument       TEXT NOT NULL,
    instrument_norm  TEXT NOT NULL,
    direction        TEXT NOT NULL CHECK (direction IN {DIRECTIONS!r}),
    thesis           TEXT NOT NULL,
    edge_type        TEXT NOT NULL,
    horizon          TEXT NOT NULL CHECK (horizon IN {HORIZONS!r}),
    size             TEXT,
    invalidation     TEXT NOT NULL,
    status           TEXT NOT NULL CHECK (status IN {STATUSES!r}),
    operator_action  TEXT CHECK (operator_action IS NULL
                                 OR operator_action IN {OPERATOR_ACTIONS!r}),
    thesis_state     TEXT CHECK (thesis_state IS NULL
                                 OR thesis_state IN {THESIS_STATES!r}),
    superseded_by    TEXT REFERENCES decisions(id),
    run_id           TEXT
);

CREATE TABLE IF NOT EXISTS decision_packets (
    packet_id                TEXT PRIMARY KEY,
    decision_id              TEXT NOT NULL REFERENCES decisions(id),
    created_at               TEXT NOT NULL,
    run_id                   TEXT NOT NULL,
    decision_time            TEXT NOT NULL,
    available_at_cutoff      TEXT NOT NULL,
    git_sha                  TEXT NOT NULL,
    code_dirty               INTEGER NOT NULL,
    data_manifest_hash       TEXT NOT NULL,
    data_manifest_json       TEXT NOT NULL,
    metrics_registry_version TEXT NOT NULL,
    source_registry_version  TEXT NOT NULL,
    output_hash              TEXT NOT NULL,
    volatile_fields          TEXT NOT NULL
);

-- Restricted roots are mirrored into the DB so the trigger can see them. The
-- YAML stays the source of truth; sync_restrictions() rewrites this table.
CREATE TABLE IF NOT EXISTS restricted_instruments (
    norm_ticker TEXT PRIMARY KEY,
    entity      TEXT NOT NULL,
    tier        TEXT,
    note        TEXT
);

-- A refusal must leave a record. Silence is indistinguishable from "nobody
-- tried", and the whole point is to be able to show the rule working.
CREATE TABLE IF NOT EXISTS blocked_attempts (
    id           INTEGER PRIMARY KEY,
    attempted_at TEXT NOT NULL,
    instrument   TEXT NOT NULL,
    instrument_norm TEXT NOT NULL,
    matched_on   TEXT NOT NULL,
    entity       TEXT,
    payload      TEXT NOT NULL
);

-- THE BACKSTOP. Fires for any inserter, including one that never imports the
-- Python register.
CREATE TRIGGER IF NOT EXISTS decisions_block_restricted_insert
BEFORE INSERT ON decisions
WHEN EXISTS (SELECT 1 FROM restricted_instruments
              WHERE norm_ticker = NEW.instrument_norm)
BEGIN
    SELECT RAISE(ABORT, 'restricted instrument: no recommendation may be written for the Brookfield complex');
END;

CREATE TRIGGER IF NOT EXISTS decisions_block_restricted_update
BEFORE UPDATE OF instrument, instrument_norm ON decisions
WHEN EXISTS (SELECT 1 FROM restricted_instruments
              WHERE norm_ticker = NEW.instrument_norm)
BEGIN
    SELECT RAISE(ABORT, 'restricted instrument: no recommendation may be written for the Brookfield complex');
END;

-- Packets are evidence. Evidence that can be edited is not evidence.
CREATE TRIGGER IF NOT EXISTS packets_immutable_update
BEFORE UPDATE ON decision_packets
BEGIN SELECT RAISE(ABORT, 'decision_packets is immutable'); END;

CREATE TRIGGER IF NOT EXISTS packets_immutable_delete
BEFORE DELETE ON decision_packets
BEGIN SELECT RAISE(ABORT, 'decision_packets is immutable'); END;

-- Part 7: a superseded decision stays exactly as written.
CREATE TRIGGER IF NOT EXISTS decisions_superseded_frozen
BEFORE UPDATE ON decisions
WHEN OLD.superseded_by IS NOT NULL
BEGIN SELECT RAISE(ABORT, 'a superseded decision is frozen; write a new one'); END;
"""


class Register:
    """The decision register. Refuses restricted instruments at write time."""

    def __init__(self, path: Optional[str] = None,
                 entities_path: Optional[Path] = None) -> None:
        self.path = Path(path or DEFAULT_DB)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.restrictions = (instruments.Restrictions(entities_path)
                             if entities_path else instruments.restrictions())
        self.sync_restrictions()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Register":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def sync_restrictions(self) -> int:
        """Mirror the YAML blocklist into the table the trigger reads."""
        rows = [(root, str(r.get("entity") or ""), str(r.get("tier") or ""),
                 str(r.get("note") or ""))
                for root, r in self.restrictions.roots.items()]
        self.conn.execute("DELETE FROM restricted_instruments")
        self.conn.executemany(
            "INSERT INTO restricted_instruments (norm_ticker, entity, tier, note) "
            "VALUES (?,?,?,?)", rows)
        self.conn.commit()
        return len(rows)

    # -- the insert path ---------------------------------------------------
    def record(self, instrument: str, direction: str, thesis: str,
               edge_type: str, horizon: str, invalidation: str,
               size: Optional[str] = None, status: str = "draft",
               operator_action: Optional[str] = None,
               thesis_state: Optional[str] = None,
               decision_time: Optional[str] = None,
               run_id: Optional[str] = None,
               decision_id: Optional[str] = None) -> str:
        """Write one decision. Raises RestrictedInstrumentError if blocked.

        The restriction check happens FIRST -- before validation, before any
        write -- so that a blocked instrument cannot reach the table even if
        some other field is also wrong and would have failed later.
        """
        norm = instruments.normalise(instrument)
        hit = self.restrictions.check(instrument)
        if hit:
            self._log_blocked(instrument, norm, hit, locals())
            raise RestrictedInstrumentError(
                f"{instrument!r} is in the {hit.get('entity_id', 'restricted')} "
                f"complex (matched on {hit['matched_on']}"
                + (f": {hit['root']}" if hit["matched_on"] == "root"
                   else f": {hit.get('pattern')!r}")
                + "). No recommendation may be written for it. "
                  "Diagnostic and strategic coverage is unaffected.")

        did = decision_id or str(uuid.uuid4())
        now = session.utc_iso()
        self.conn.execute(
            "INSERT INTO decisions (id, created_at, decision_time, instrument,"
            " instrument_norm, direction, thesis, edge_type, horizon, size,"
            " invalidation, status, operator_action, thesis_state, run_id)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (did, now, decision_time or now, instrument, norm, direction,
             thesis, edge_type, horizon, size, invalidation, status,
             operator_action, thesis_state, run_id))
        self.conn.commit()
        return did

    def _log_blocked(self, instrument: str, norm: str, hit: dict,
                     payload: dict) -> None:
        safe = {k: v for k, v in payload.items()
                if k not in ("self",) and isinstance(v, (str, int, float, type(None)))}
        self.conn.execute(
            "INSERT INTO blocked_attempts (attempted_at, instrument,"
            " instrument_norm, matched_on, entity, payload) VALUES (?,?,?,?,?,?)",
            (session.utc_iso(), instrument, norm, hit["matched_on"],
             str(hit.get("entity")), json.dumps(safe, default=str)))
        self.conn.commit()

    # -- packets -----------------------------------------------------------
    def attach_packet(self, decision_id: str, packet: dict) -> str:
        """Attach an immutable packet. Written once, never updated."""
        pid = packet.get("packet_id") or str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO decision_packets (packet_id, decision_id, created_at,"
            " run_id, decision_time, available_at_cutoff, git_sha, code_dirty,"
            " data_manifest_hash, data_manifest_json, metrics_registry_version,"
            " source_registry_version, output_hash, volatile_fields)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (pid, decision_id, session.utc_iso(), packet["run_id"],
             packet["decision_time"], packet["available_at_cutoff"],
             packet["git_sha"], int(packet.get("code_dirty", 0)),
             packet["data_manifest_hash"],
             json.dumps(packet.get("data_manifest", {}), sort_keys=True),
             str(packet["metrics_registry_version"]),
             str(packet["source_registry_version"]),
             packet["output_hash"],
             json.dumps(sorted(packet.get("volatile_fields", [])))))
        self.conn.commit()
        return pid

    def packet(self, decision_id: str) -> Optional[dict]:
        cur = self.conn.execute(
            "SELECT * FROM decision_packets WHERE decision_id = ? "
            "ORDER BY created_at LIMIT 1", (decision_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    # -- lifecycle ---------------------------------------------------------
    def supersede(self, old_id: str, **new_decision) -> str:
        """Replace a decision with a new record, per Part 7.

        The old row is not edited beyond the pointer -- that single UPDATE is
        allowed because superseded_by is still NULL when it runs, and the
        freeze trigger closes the row immediately afterwards.
        """
        new_id = self.record(**new_decision)
        self.conn.execute("UPDATE decisions SET superseded_by = ? WHERE id = ?",
                          (new_id, old_id))
        self.conn.commit()
        return new_id

    def set_status(self, decision_id: str, status: str,
                   operator_action: Optional[str] = None) -> None:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        if operator_action is not None and operator_action not in OPERATOR_ACTIONS:
            raise ValueError(f"operator_action must be one of {OPERATOR_ACTIONS}")
        self.conn.execute(
            "UPDATE decisions SET status = ?, operator_action = COALESCE(?, operator_action)"
            " WHERE id = ?", (status, operator_action, decision_id))
        self.conn.commit()

    # -- read --------------------------------------------------------------
    def get(self, decision_id: str) -> Optional[dict]:
        cur = self.conn.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def all(self) -> list[dict]:
        cur = self.conn.execute("SELECT * FROM decisions ORDER BY created_at")
        return [dict(r) for r in cur.fetchall()]

    def blocked_attempts(self) -> list[dict]:
        cur = self.conn.execute(
            "SELECT * FROM blocked_attempts ORDER BY attempted_at")
        return [dict(r) for r in cur.fetchall()]
