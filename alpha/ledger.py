"""
alpha.db -- the lab's ledger (X-1.1). The ONLY database alpha/ writes.

    python -m alpha.ledger init                 # create the tables, print the path
    python -m alpha.ledger snapshot DEST        # online-backup copy, for the sweep
    python -m alpha.ledger path                 # where it is

WHERE IT LIVES. Under the data root beside the observation store, the path in
config/alpha.yaml (`ledger.path`, "{data_root}/alpha.db"), $ALPHA_DB overriding
it: alpha/config.py ledger_path(). On the box that is
~/chester-reports/data/alpha.db, and the nightly sweep snapshots it beside
chester.db (scripts/rclone_sync.sh) -- never as a raw file.

THE TABLES are the change order's, each row carrying `as_of` (the instant the
row is about, a point-in-time cutoff) and `written_at` (when the lab wrote it):

  engines         the roster: family, horizon, status, the validation record
  hypotheses      X-2.5's register: every idea, its rule and its pre-registration
                  instant, with its status and result -- failures kept
  hypothesis_batches  each batch file ingested (X-2.11): its Drive created and
                  modified times, its sha256, its source and channel
  inbox_log       every inbox file seen, ingested, refused or ignored, and why
  signals         an engine's signal at an as-of instant
  fills           a modelled fill: price, every cost component, the stored quote
  positions       a paper position, opened by a fill and closed by one
  marks           the daily mark of an open position
  grades          a closed position's result, net of modelled costs
  edge_posterior  per engine per day: n, the win-rate and expectancy posteriors,
                  and the shrinkage prior they were computed under
  cost_calibration modelled against stored costs, per engine per cost class
  attribution     per engine per day per regime key
  loop_events     every change any loop makes: before, after, counterfactual,
                  version, reversed_by
  variant_counts  per engine family: every validation run adds one
  holdout         the months no loop may fit on

and two the change order did not name, both of them records the named tables
needed somewhere to live:

  allocations     the allocator's weights per engine per day, proposed (nightly)
                  or applied (weekly) -- the "weights" the loops recompute
  equity          per engine and for the lab ('__lab__') per day: equity, the
                  high-water mark and the drawdown the governor reads

and three of Tranche 3's (X-3.1, X-3.2):

  event_base_rates  the system's own event base rates, per event, bucket and
                  measure, with n and the window (alpha/event_rates.py)
  carry_book      the paper book's crypto rows: a delta-neutral carry's venue,
                  leg sizes and funding accrued (alpha/engines/carry.py)
  carry_accruals  each day's funding received or paid on an open carry

THE BLOCKLIST, A SECOND TIME, IN SQLITE. alpha/blocklist.py refuses a restricted
instrument before any write; the triggers below refuse it again for any insert
that bypasses that module, against `restricted_instruments`, which every open of
the ledger re-mirrors from the system's list (the register's own pattern).

loop_events IS APPEND-ONLY. A change is reversed by a NEW event; the only update
the table accepts is setting `reversed_by` on the event it reverses, once.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable, Optional

from . import blocklist
from . import config as acfg

VERSION = "x2.0"
LAB = "__lab__"
ENGINE_STATUSES = ("candidate", "live", "halved", "validation", "retired")

SCHEMA = """
CREATE TABLE IF NOT EXISTS restricted_instruments (
    norm_ticker TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS engines (
    id                TEXT PRIMARY KEY,
    family            TEXT NOT NULL,
    horizon           TEXT NOT NULL CHECK (horizon IN ('intraday','daily','weekly')),
    status            TEXT NOT NULL CHECK (status IN
                        ('candidate','live','halved','validation','retired')),
    validated_at      TEXT,
    validated_metrics TEXT,
    validated_ranges  TEXT,
    kill_rule         TEXT,
    min_size          REAL NOT NULL,
    frozen            INTEGER NOT NULL DEFAULT 0,
    as_of             TEXT NOT NULL,
    written_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hypotheses (
    id                TEXT PRIMARY KEY,
    batch_id          TEXT NOT NULL,
    local_id          TEXT NOT NULL,
    title             TEXT NOT NULL,
    family            TEXT NOT NULL,
    horizon_class     TEXT,
    horizon_sessions  INTEGER,
    horizon           TEXT,
    mechanism         TEXT NOT NULL,
    universe          TEXT,
    instruments       TEXT,
    rule_text         TEXT NOT NULL,
    rule_dsl          TEXT,
    rule_origin       TEXT,
    rule_hash         TEXT NOT NULL,
    conditioning      TEXT,
    expected          TEXT,
    expected_sign     INTEGER,
    expected_size     REAL,
    sample            TEXT,
    sample_needed     INTEGER,
    data              TEXT,
    needs_code        INTEGER NOT NULL,
    kill_rule         TEXT,
    state_at_registration TEXT,
    spec              TEXT NOT NULL,
    source            TEXT NOT NULL CHECK (source IN
                        ('model','operator','chat','sitting','systematic','tell')),
    channel           TEXT NOT NULL,
    proposer          TEXT,
    model_idea_rule   INTEGER NOT NULL CHECK (model_idea_rule IN (0, 1)),
    pre_registered_at TEXT NOT NULL,
    status            TEXT NOT NULL CHECK (status IN
                        ('registered','needs_code','data_gap','screened_out',
                         'testing','passed','failed','refined','promoted','retired')),
    status_reason     TEXT,
    result            TEXT,
    supersedes        TEXT,
    superseded_by     TEXT REFERENCES hypotheses(id),
    engine_id         TEXT,
    as_of             TEXT NOT NULL,
    written_at        TEXT NOT NULL,
    UNIQUE (batch_id, local_id)
);

CREATE TABLE IF NOT EXISTS hypothesis_batches (
    batch_id          TEXT PRIMARY KEY,
    schema            TEXT NOT NULL,
    file_name         TEXT,
    file_sha256       TEXT,
    source            TEXT NOT NULL,
    channel           TEXT NOT NULL,
    proposer          TEXT,
    batch_written_at  TEXT,
    created_time      TEXT,
    modified_time     TEXT,
    pre_registered_at TEXT NOT NULL,
    model_idea_rule   INTEGER NOT NULL,
    inputs            TEXT,
    prompt_version    TEXT,
    model_id          TEXT,
    packet_sha256     TEXT,
    n_hypotheses      INTEGER NOT NULL,
    as_of             TEXT NOT NULL,
    written_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inbox_log (
    id                INTEGER PRIMARY KEY,
    file_name         TEXT NOT NULL,
    file_sha256       TEXT,
    batch_id          TEXT,
    local_id          TEXT,
    verdict           TEXT NOT NULL CHECK (verdict IN ('ingested','refused','ignored')),
    reason            TEXT,
    created_time      TEXT,
    modified_time     TEXT,
    as_of             TEXT NOT NULL,
    written_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signals (
    id              INTEGER PRIMARY KEY,
    engine_id       TEXT NOT NULL,
    instrument      TEXT NOT NULL,
    instrument_norm TEXT NOT NULL,
    direction       INTEGER NOT NULL CHECK (direction IN (-1, 1)),
    strength        REAL,
    size_fraction   REAL NOT NULL,
    stop_price      REAL,
    target_price    REAL,
    time_stop       TEXT,
    params          TEXT,
    state           TEXT NOT NULL DEFAULT 'pending' CHECK (state IN
                      ('pending','filled','expired','cancelled')),
    as_of           TEXT NOT NULL,
    written_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fills (
    id               INTEGER PRIMARY KEY,
    signal_id        INTEGER REFERENCES signals(id),
    position_id      INTEGER,
    engine_id        TEXT NOT NULL,
    instrument       TEXT NOT NULL,
    instrument_norm  TEXT NOT NULL,
    purpose          TEXT NOT NULL CHECK (purpose IN ('entry','exit')),
    side             INTEGER NOT NULL CHECK (side IN (-1, 1)),
    qty              REAL NOT NULL,
    fill_kind        TEXT NOT NULL CHECK (fill_kind IN ('bar_open','quote','bar_level')),
    reference_price  REAL NOT NULL,
    modelled_price   REAL NOT NULL,
    stored_quote     TEXT,
    cost_class       TEXT NOT NULL,
    cost_spread      REAL NOT NULL,
    cost_slippage    REAL NOT NULL,
    cost_commission  REAL NOT NULL,
    cost_borrow      REAL NOT NULL,
    cost_roll        REAL NOT NULL,
    cost_funding     REAL NOT NULL,
    cost_fx          REAL NOT NULL,
    cost_total       REAL NOT NULL,
    filled_at        TEXT NOT NULL,
    as_of            TEXT NOT NULL,
    written_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS positions (
    id              INTEGER PRIMARY KEY,
    engine_id       TEXT NOT NULL,
    signal_id       INTEGER REFERENCES signals(id),
    instrument      TEXT NOT NULL,
    instrument_norm TEXT NOT NULL,
    cost_class      TEXT NOT NULL,
    direction       INTEGER NOT NULL CHECK (direction IN (-1, 1)),
    qty             REAL NOT NULL,
    entry_fill_id   INTEGER REFERENCES fills(id),
    entry_price     REAL NOT NULL,
    stop_price      REAL,
    target_price    REAL,
    time_stop       TEXT,
    opened_at       TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('open','closed')),
    exit_fill_id    INTEGER REFERENCES fills(id),
    exit_price      REAL,
    exit_reason     TEXT,
    closed_at       TEXT,
    as_of           TEXT NOT NULL,
    written_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS marks (
    position_id INTEGER NOT NULL REFERENCES positions(id),
    engine_id   TEXT NOT NULL,
    day         TEXT NOT NULL,
    price       REAL NOT NULL,
    unrealised  REAL NOT NULL,
    as_of       TEXT NOT NULL,
    written_at  TEXT NOT NULL,
    PRIMARY KEY (position_id, day)
);

CREATE TABLE IF NOT EXISTS grades (
    position_id  INTEGER PRIMARY KEY REFERENCES positions(id),
    engine_id    TEXT NOT NULL,
    day          TEXT NOT NULL,
    gross_pnl    REAL NOT NULL,
    costs        REAL NOT NULL,
    net_pnl      REAL NOT NULL,
    net_return   REAL NOT NULL,
    win          INTEGER NOT NULL CHECK (win IN (0, 1)),
    regime_key   TEXT,
    as_of        TEXT NOT NULL,
    written_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS edge_posterior (
    engine_id       TEXT NOT NULL,
    day             TEXT NOT NULL,
    n               INTEGER NOT NULL,
    wins            INTEGER NOT NULL,
    win_alpha       REAL NOT NULL,
    win_beta        REAL NOT NULL,
    win_mean        REAL NOT NULL,
    exp_mean        REAL NOT NULL,
    exp_sd          REAL NOT NULL,
    raw_expectancy  REAL,
    prior_strength  REAL NOT NULL,
    prior_win_rate  REAL NOT NULL,
    prior_exp_mean  REAL NOT NULL,
    as_of           TEXT NOT NULL,
    written_at      TEXT NOT NULL,
    PRIMARY KEY (engine_id, day)
);

CREATE TABLE IF NOT EXISTS cost_calibration (
    engine_id     TEXT NOT NULL,
    cost_class    TEXT NOT NULL,
    day           TEXT NOT NULL,
    n             INTEGER NOT NULL,
    modelled_bps  REAL,
    stored_bps    REAL,
    ratio         REAL,
    as_of         TEXT NOT NULL,
    written_at    TEXT NOT NULL,
    PRIMARY KEY (engine_id, cost_class, day)
);

CREATE TABLE IF NOT EXISTS attribution (
    engine_id   TEXT NOT NULL,
    day         TEXT NOT NULL,
    regime_key  TEXT NOT NULL,
    pnl         REAL NOT NULL,
    n           INTEGER NOT NULL,
    as_of       TEXT NOT NULL,
    written_at  TEXT NOT NULL,
    PRIMARY KEY (engine_id, day, regime_key)
);

CREATE TABLE IF NOT EXISTS loop_events (
    id              INTEGER PRIMARY KEY,
    loop            TEXT NOT NULL,
    kind            TEXT NOT NULL,
    engine          TEXT,
    before          TEXT,
    after           TEXT,
    counterfactual  TEXT,
    version         TEXT NOT NULL,
    reversed_by     INTEGER REFERENCES loop_events(id),
    source          TEXT NOT NULL DEFAULT 'loop',
    as_of           TEXT NOT NULL,
    written_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS variant_counts (
    family      TEXT PRIMARY KEY,
    count       INTEGER NOT NULL,
    as_of       TEXT NOT NULL,
    written_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS holdout (
    month       TEXT PRIMARY KEY,
    rule        TEXT NOT NULL,
    as_of       TEXT NOT NULL,
    written_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS allocations (
    engine_id   TEXT NOT NULL,
    day         TEXT NOT NULL,
    kind        TEXT NOT NULL CHECK (kind IN ('proposed','applied')),
    weight      REAL NOT NULL,
    cluster     TEXT,
    detail      TEXT,
    as_of       TEXT NOT NULL,
    written_at  TEXT NOT NULL,
    PRIMARY KEY (engine_id, day, kind)
);

CREATE TABLE IF NOT EXISTS equity (
    engine_id   TEXT NOT NULL,
    day         TEXT NOT NULL,
    equity      REAL NOT NULL,
    hwm         REAL NOT NULL,
    drawdown    REAL NOT NULL,
    as_of       TEXT NOT NULL,
    written_at  TEXT NOT NULL,
    PRIMARY KEY (engine_id, day)
);

-- X-3.1: THE SYSTEM'S OWN EVENT BASE RATES (alpha/event_rates.py), one row per
-- event, bucket and measure, with its n and its window; a re-run on the same day
-- replaces that day's rows, an earlier day's are kept.
CREATE TABLE IF NOT EXISTS event_base_rates (
    computed_on TEXT NOT NULL,
    event       TEXT NOT NULL,
    bucket_kind TEXT NOT NULL,
    bucket      TEXT NOT NULL,
    measure     TEXT NOT NULL,
    n           INTEGER NOT NULL,
    first_day   TEXT,
    last_day    TEXT,
    mean        REAL,
    hit_rate    REAL,
    hit_means   TEXT,
    unit        TEXT NOT NULL,
    note        TEXT,
    as_of       TEXT NOT NULL,
    written_at  TEXT NOT NULL,
    PRIMARY KEY (computed_on, event, bucket_kind, bucket, measure)
);

-- X-3.2: THE PAPER BOOK'S CRYPTO ROWS (alpha/engines/carry.py). A delta-neutral
-- carry is two legs at one notional -- spot long, the perp short on one venue --
-- so it is booked here with the venue, the leg sizes and the funding accrued, not
-- in `positions`, whose one-instrument fill needs a stored perp price the store
-- does not hold. Paper only; book.cum_pnl() adds it to the engine's P&L.
CREATE TABLE IF NOT EXISTS carry_book (
    id              INTEGER PRIMARY KEY,
    engine_id       TEXT NOT NULL,
    coin            TEXT NOT NULL,
    venue           TEXT NOT NULL,
    opened_day      TEXT NOT NULL,
    spot_qty        REAL NOT NULL,
    perp_qty        REAL NOT NULL,
    notional        REAL NOT NULL,
    entry_price     REAL NOT NULL,
    entry_costs     REAL NOT NULL,
    funding_accrued REAL NOT NULL DEFAULT 0,
    status          TEXT NOT NULL CHECK (status IN ('open','closed')),
    closed_day      TEXT,
    exit_price      REAL,
    exit_costs      REAL,
    net_pnl         REAL,
    basis_note      TEXT,
    as_of           TEXT NOT NULL,
    written_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS carry_accruals (
    carry_id     INTEGER NOT NULL REFERENCES carry_book(id),
    engine_id    TEXT NOT NULL,
    day          TEXT NOT NULL,
    venue        TEXT NOT NULL,
    funding_pct  REAL NOT NULL,
    accrued      REAL NOT NULL,
    as_of        TEXT NOT NULL,
    written_at   TEXT NOT NULL,
    PRIMARY KEY (carry_id, day)
);

CREATE INDEX IF NOT EXISTS positions_open ON positions (status, engine_id);
CREATE INDEX IF NOT EXISTS events_by_time ON loop_events (written_at);

CREATE TRIGGER IF NOT EXISTS signals_block_restricted
BEFORE INSERT ON signals
WHEN EXISTS (SELECT 1 FROM restricted_instruments WHERE norm_ticker = NEW.instrument_norm)
BEGIN SELECT RAISE(ABORT, 'restricted instrument: the Brookfield complex never reaches the lab'); END;

CREATE TRIGGER IF NOT EXISTS fills_block_restricted
BEFORE INSERT ON fills
WHEN EXISTS (SELECT 1 FROM restricted_instruments WHERE norm_ticker = NEW.instrument_norm)
BEGIN SELECT RAISE(ABORT, 'restricted instrument: the Brookfield complex never reaches the lab'); END;

CREATE TRIGGER IF NOT EXISTS positions_block_restricted
BEFORE INSERT ON positions
WHEN EXISTS (SELECT 1 FROM restricted_instruments WHERE norm_ticker = NEW.instrument_norm)
BEGIN SELECT RAISE(ABORT, 'restricted instrument: the Brookfield complex never reaches the lab'); END;

CREATE TRIGGER IF NOT EXISTS loop_events_append_only
BEFORE UPDATE OF loop, kind, engine, before, after, counterfactual, version,
                 source, as_of, written_at ON loop_events
BEGIN SELECT RAISE(ABORT, 'loop_events is append-only: reverse a change with a new event'); END;

CREATE TRIGGER IF NOT EXISTS loop_events_reversed_once
BEFORE UPDATE OF reversed_by ON loop_events
WHEN OLD.reversed_by IS NOT NULL
BEGIN SELECT RAISE(ABORT, 'loop_events: an event is reversed once'); END;

CREATE TRIGGER IF NOT EXISTS loop_events_no_delete
BEFORE DELETE ON loop_events
BEGIN SELECT RAISE(ABORT, 'loop_events is append-only'); END;

-- THE REGISTER KEEPS ITS FAILURES (X-2.5): a hypothesis is never deleted, and
-- the idea it records -- its rule, its mechanism, its pre-registration instant --
-- is never rewritten. Status, result and the links move; the idea does not.
CREATE TRIGGER IF NOT EXISTS hypotheses_no_delete
BEFORE DELETE ON hypotheses
BEGIN SELECT RAISE(ABORT, 'the hypothesis register keeps its failures: no delete'); END;

CREATE TRIGGER IF NOT EXISTS hypotheses_idea_fixed
BEFORE UPDATE OF id, batch_id, local_id, title, family, mechanism, rule_text,
                 rule_hash, spec, source, channel, pre_registered_at ON hypotheses
BEGIN SELECT RAISE(ABORT, 'a registered hypothesis is fixed: a change is a new, counted variant'); END;

CREATE TRIGGER IF NOT EXISTS hypothesis_batches_no_delete
BEFORE DELETE ON hypothesis_batches
BEGIN SELECT RAISE(ABORT, 'a batch, once ingested, is kept'); END;
"""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")


def _j(v: Any) -> Optional[str]:
    return None if v is None else json.dumps(v, sort_keys=True, default=str)


def version() -> str:
    """The lab's version as a loop event records it: the code's and the
    constitution's, so an event is traceable to the rules in force."""
    return f"{VERSION}+c{acfg.constitution_sha256()[:12]}"


class Ledger:
    """alpha.db. Opened read-write by the loops; `read_only=True` for a reader
    (the Weekly's line), which never creates the file."""

    def __init__(self, path: Optional[str | Path] = None,
                 read_only: bool = False) -> None:
        self.path = Path(path or acfg.ledger_path())
        self.read_only = read_only
        if read_only:
            self.conn = sqlite3.connect(f"file:{self.path.as_posix()}?mode=ro",
                                        uri=True)
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout = 5000")
        if not read_only:
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.execute("PRAGMA foreign_keys = ON")
            self._migrate()
            self.conn.executescript(SCHEMA)
            self.sync_restrictions()
            self.conn.commit()

    def _migrate(self) -> None:
        """Tranche 1 created `hypotheses` on the change order's first sketch and
        wrote nothing to it ("written from Tranche 2"). Tranche 2's register is
        the fixture batch's schema (X-2.5), so an EMPTY old-shaped table is
        replaced; a non-empty one is refused rather than rewritten -- the register
        keeps what it holds."""
        cols = {r[1] for r in self.conn.execute("PRAGMA table_info(hypotheses)")}
        if not cols or "batch_id" in cols:
            return
        n = self.conn.execute("SELECT COUNT(*) FROM hypotheses").fetchone()[0]
        if n:
            raise RuntimeError(f"alpha.db holds {n} hypotheses in the Tranche 1 shape; "
                               "the register is not rewritten in place")
        self.conn.execute("DROP TABLE hypotheses")

    # -- plumbing -----------------------------------------------------------
    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Ledger":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def q(self, sql: str, args: Iterable[Any] = ()) -> list[dict]:
        return [dict(r) for r in self.conn.execute(sql, tuple(args)).fetchall()]

    def one(self, sql: str, args: Iterable[Any] = ()) -> Optional[dict]:
        r = self.conn.execute(sql, tuple(args)).fetchone()
        return dict(r) if r else None

    def _insert(self, table: str, row: dict) -> int:
        row = {**row, "written_at": row.get("written_at") or utc_now()}
        cols = ", ".join(row)
        marks = ", ".join(f":{k}" for k in row)
        cur = self.conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", row)
        self.conn.commit()
        return int(cur.lastrowid)

    def _upsert(self, table: str, row: dict) -> None:
        row = {**row, "written_at": row.get("written_at") or utc_now()}
        cols = ", ".join(row)
        marks = ", ".join(f":{k}" for k in row)
        self.conn.execute(f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({marks})",
                          row)
        self.conn.commit()

    def sync_restrictions(self) -> int:
        """Mirror the system's blocklist into the table the triggers read."""
        roots = blocklist.roots()
        self.conn.execute("DELETE FROM restricted_instruments")
        self.conn.executemany("INSERT INTO restricted_instruments VALUES (?)",
                              [(r,) for r in roots])
        return len(roots)

    # -- engines ------------------------------------------------------------
    def engine(self, engine_id: str) -> Optional[dict]:
        r = self.one("SELECT * FROM engines WHERE id = ?", (engine_id,))
        if r:
            for k in ("validated_metrics", "validated_ranges", "kill_rule"):
                r[k] = json.loads(r[k]) if r.get(k) else None
        return r

    def engines(self, statuses: Optional[Iterable[str]] = None) -> list[dict]:
        rows = self.q("SELECT id FROM engines ORDER BY id")
        out = [self.engine(r["id"]) for r in rows]
        if statuses is not None:
            want = set(statuses)
            out = [e for e in out if e and e["status"] in want]
        return [e for e in out if e]

    def upsert_engine(self, engine_id: str, family: str, horizon: str,
                      status: str, min_size: float, as_of: str,
                      kill_rule: Optional[dict] = None, frozen: bool = False,
                      validated_at: Optional[str] = None,
                      validated_metrics: Optional[dict] = None,
                      validated_ranges: Optional[dict] = None) -> None:
        self._upsert("engines", {
            "id": engine_id, "family": family, "horizon": horizon,
            "status": status, "validated_at": validated_at,
            "validated_metrics": _j(validated_metrics),
            "validated_ranges": _j(validated_ranges), "kill_rule": _j(kill_rule),
            "min_size": float(min_size), "frozen": int(bool(frozen)),
            "as_of": as_of})

    def set_engine(self, engine_id: str, as_of: str, **fields: Any) -> None:
        """Set status/frozen/validation fields on an engine. Callers write the
        loop_events row for the change; the governor and the harness do."""
        if not fields:
            return
        enc = {k: (_j(v) if k in ("validated_metrics", "validated_ranges",
                                  "kill_rule") else
                   int(bool(v)) if k == "frozen" else v)
               for k, v in fields.items()}
        sets = ", ".join(f"{k} = :{k}" for k in enc)
        self.conn.execute(f"UPDATE engines SET {sets}, as_of = :as_of, "
                          f"written_at = :written_at WHERE id = :id",
                          {**enc, "as_of": as_of, "written_at": utc_now(),
                           "id": engine_id})
        self.conn.commit()

    # -- signals, fills, positions -----------------------------------------
    def add_signal(self, engine_id: str, instrument: str, direction: int,
                   size_fraction: float, as_of: str, strength: Optional[float] = None,
                   stop_price: Optional[float] = None,
                   target_price: Optional[float] = None,
                   time_stop: Optional[str] = None,
                   params: Optional[dict] = None) -> int:
        norm = blocklist.refuse(instrument)
        return self._insert("signals", {
            "engine_id": engine_id, "instrument": instrument,
            "instrument_norm": norm, "direction": int(direction),
            "strength": strength, "size_fraction": float(size_fraction),
            "stop_price": stop_price, "target_price": target_price,
            "time_stop": time_stop, "params": _j(params), "as_of": as_of})

    def pending_signals(self, engine_id: Optional[str] = None) -> list[dict]:
        sql = "SELECT * FROM signals WHERE state='pending'"
        args: tuple = ()
        if engine_id:
            sql, args = sql + " AND engine_id=?", (engine_id,)
        rows = self.q(sql + " ORDER BY id", args)
        for r in rows:
            r["params"] = json.loads(r["params"]) if r.get("params") else {}
        return rows

    def set_signal_state(self, signal_id: int, state: str) -> None:
        self.conn.execute("UPDATE signals SET state=?, written_at=? WHERE id=?",
                          (state, utc_now(), signal_id))
        self.conn.commit()

    def add_fill(self, row: dict) -> int:
        row = dict(row)
        row["instrument_norm"] = blocklist.refuse(row["instrument"])
        row["stored_quote"] = _j(row.get("stored_quote"))
        return self._insert("fills", row)

    def open_position(self, row: dict) -> int:
        row = dict(row)
        row["instrument_norm"] = blocklist.refuse(row["instrument"])
        row.setdefault("status", "open")
        return self._insert("positions", row)

    def close_position(self, position_id: int, exit_fill_id: int,
                       exit_price: float, reason: str, closed_at: str) -> None:
        self.conn.execute(
            "UPDATE positions SET status='closed', exit_fill_id=?, exit_price=?,"
            " exit_reason=?, closed_at=?, as_of=?, written_at=? WHERE id=?"
            " AND status='open'",
            (exit_fill_id, exit_price, reason, closed_at, closed_at, utc_now(),
             position_id))
        self.conn.commit()

    def link_fill(self, fill_id: int, position_id: int) -> None:
        self.conn.execute("UPDATE fills SET position_id=? WHERE id=?",
                          (position_id, fill_id))
        self.conn.commit()

    def open_positions(self, engine_id: Optional[str] = None) -> list[dict]:
        if engine_id:
            return self.q("SELECT * FROM positions WHERE status='open' AND "
                          "engine_id=? ORDER BY id", (engine_id,))
        return self.q("SELECT * FROM positions WHERE status='open' ORDER BY id")

    def add_mark(self, position_id: int, engine_id: str, day: str, price: float,
                 unrealised: float, as_of: str) -> None:
        self._upsert("marks", {"position_id": position_id, "engine_id": engine_id,
                               "day": day, "price": price,
                               "unrealised": unrealised, "as_of": as_of})

    def add_grade(self, row: dict) -> None:
        self._upsert("grades", row)

    # -- the learning records ----------------------------------------------
    def put(self, table: str, row: dict) -> None:
        """An upsert into one of the per-day record tables."""
        if table not in ("edge_posterior", "cost_calibration", "attribution",
                         "allocations", "equity"):
            raise ValueError(f"put() does not write {table}")
        self._upsert(table, row)

    def event(self, loop: str, kind: str, as_of: str, engine: Optional[str] = None,
              before: Any = None, after: Any = None, counterfactual: Any = None,
              source: str = "loop") -> int:
        """One loop_events row. Every change any loop makes is one of these."""
        return self._insert("loop_events", {
            "loop": loop, "kind": kind, "engine": engine, "before": _j(before),
            "after": _j(after), "counterfactual": _j(counterfactual),
            "version": version(), "source": source, "as_of": as_of})

    def reverse(self, event_id: int, by_event_id: int) -> None:
        self.conn.execute("UPDATE loop_events SET reversed_by=? WHERE id=?",
                          (by_event_id, event_id))
        self.conn.commit()

    def events(self, since: Optional[str] = None) -> list[dict]:
        if since:
            return self.q("SELECT * FROM loop_events WHERE written_at >= ? "
                          "ORDER BY id", (since,))
        return self.q("SELECT * FROM loop_events ORDER BY id")

    # -- the variant count and the hold-out --------------------------------
    def variant_count(self, family: str) -> int:
        r = self.one("SELECT count FROM variant_counts WHERE family=?", (family,))
        return int(r["count"]) if r else 0

    def bump_variant(self, family: str, as_of: str) -> int:
        """Every validation run is one more variant of its family. Returns the
        count INCLUDING this run, which is the N the run is deflated by."""
        n = self.variant_count(family) + 1
        self._upsert("variant_counts", {"family": family, "count": n, "as_of": as_of})
        return n

    def record_holdout(self, months: Iterable[str], rule: str, as_of: str) -> int:
        n = 0
        for m in months:
            cur = self.conn.execute(
                "INSERT OR IGNORE INTO holdout (month, rule, as_of, written_at)"
                " VALUES (?,?,?,?)", (m, rule, as_of, utc_now()))
            n += cur.rowcount
        self.conn.commit()
        return n

    def holdout_months(self) -> list[str]:
        return [r["month"] for r in self.q("SELECT month FROM holdout ORDER BY month")]


def snapshot(src: Path, dest: Path) -> dict:
    """A consistent copy of the live ledger through SQLite's online backup API,
    as altdata.observations.snapshot_sqlite does for chester.db -- never a file
    copy, which read mid-write opens cleanly and is missing rows."""
    src, dest = Path(src), Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.unlink(missing_ok=True)
    conn = sqlite3.connect(f"file:{src.as_posix()}?mode=ro", uri=True)
    try:
        out = sqlite3.connect(str(dest))
        try:
            conn.backup(out)
            n = out.execute("SELECT COUNT(*) FROM loop_events").fetchone()[0]
        finally:
            out.close()
    finally:
        conn.close()
    return {"src": str(src), "dest": str(dest), "bytes": dest.stat().st_size,
            "loop_events": n}


def _main(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    if cmd == "path":
        print(acfg.ledger_path())
        return 0
    if cmd == "init":
        with Ledger() as lg:
            print(f"alpha.db ready at {lg.path}")
        return 0
    if cmd == "snapshot" and len(argv) >= 2:
        src = Path(argv[2]) if len(argv) > 2 else acfg.ledger_path()
        if not src.exists():
            print(f"no ledger at {src}")
            return 1
        try:
            info = snapshot(src, Path(argv[1]))
        except Exception as exc:                              # noqa: BLE001
            print(f"snapshot failed: {type(exc).__name__}: {exc}")
            return 2
        print(f"snapshot ok {info['dest']} ({info['bytes']:,} bytes, "
              f"{info['loop_events']:,} loop events)")
        return 0
    print("usage: python -m alpha.ledger path | init | snapshot <dest> [src]")
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
