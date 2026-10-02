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
import re
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Optional

import sys

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import session          # noqa: E402
from register import instruments     # noqa: E402

# ANCHORED TO THE REPO, NOT TO THE WORKING DIRECTORY.
#
# This was a bare relative path, which is correct exactly when the process was
# started from the checkout -- as every wrapper does, since each one runs
# `cd "$REPO"` first. It stops being correct the moment anything runs decide.py
# from somewhere else: SQLite would CREATE an empty database at
# ./data/chester.db rather than failing, and the register would silently fork
# into two files with no error to notice.
#
# That risk went up when the register moved to the box and gained a remote
# caller, so the default now resolves against the repository root. CHESTER_DB
# still overrides it, and a path passed explicitly still wins over both.
DEFAULT_DB = os.environ.get("CHESTER_DB") or str(REPO / "data" / "chester.db")

DIRECTIONS = ("long", "short", "flat", "hedge")
HORIZONS = ("intraday", "swing", "positional", "strategic", "structural")
STATUSES = ("draft", "active", "closed", "declined")
OPERATOR_ACTIONS = ("TAKE", "DECLINE", "MODIFY")
THESIS_STATES = ("INTACT", "STRAINED", "INVALIDATED")
# Part 31.3(c): a hedged and an unhedged instrument on the same market are two
# different instruments, never interchangeable. Mandatory for any non-USD
# denominated underlying; `n_a` is for a USD instrument, where the question does
# not arise.
CURRENCY_EXPOSURES = ("unhedged", "hedged", "n_a")
# The Doctrine's four books (Phase 5a). A decision that becomes ACTIVE names one:
# the cross-book heat view sums by it, and two of the Doctrine's rule breaks
# (Book B conversion, Book A's floor) are about a book.
BOOKS = ("A", "B", "C", "D")
# The gate at entry's outcome enumeration -- DTH §XIV, EL-2 §3.2.
GATE_OUTCOMES = ("approve", "resize", "restructure", "hedge", "delay", "reject")

# -----------------------------------------------------------------------------
# EL-1 -- THE PACKET FIELDS (docs/change-order-enterprise-layer-2026-09-27.md §3.1)
#
# Six fields, recorded at entry and immutable afterwards like every other column
# of a decision. The last three -- falsifiers, counter_thesis and the existing
# invalidation -- are Red Team v0: the register REFUSES DECISION_OK without them,
# at write time, the way it refuses a Brookfield-related security. All six are
# nullable because they arrive on a live register; a pre-P5-B row reads
# "not recorded", never a default it did not have.
# -----------------------------------------------------------------------------
# The producer of the draft. A registered paper engine id (§3.6) is added here
# when one is registered; none is yet.
ENGINE_IDS = ("daily_cascade", "weekly", "monthly", "operator")
# Computed at entry from the packet's direction against the sign of the
# market-state object's trend dimension; recorded, never recomputed.
HORIZON_ALIGNMENTS = ("aligned", "neutral", "counter")
REVIEW_CHANGED = ("none", "resized", "restructured", "hedged", "delayed",
                  "rejected")
# The gate at entry's verdict folds into review_changed: a review that changed the
# packet is a review, whether the operator or the gate made it.
GATE_TO_REVIEW = {"approve": "none", "resize": "resized",
                  "restructure": "restructured", "hedge": "hedged",
                  "delay": "delayed", "reject": "rejected"}
SETUPS_PATH = Path(__file__).resolve().parent.parent / "config" / "setups.yaml"


def setup_ids(path: Optional[Path] = None) -> tuple:
    """The setup families config/setups.yaml declares, `unclassified` included."""
    import yaml  # noqa: PLC0415
    with Path(path or SETUPS_PATH).open(encoding="utf-8") as fp:
        return tuple(((yaml.safe_load(fp) or {}).get("setups") or {}).keys())


def review_from_gate(gate_outcome: Optional[str],
                     explicit: Optional[str] = None) -> str:
    """review_changed for a new packet: the operator's word if given, else the
    gate's verdict folded in, else `none`."""
    if explicit:
        return explicit
    return GATE_TO_REVIEW.get(gate_outcome or "approve", "none")
# Rule breaks the register records. The first five are the order gate's
# reconciliation of fills against accepted decisions (Phase 5a item 1-2); the
# last three are the Doctrine's position rules (item 3).
RULE_BREAK_KINDS = (
    "unregistered_execution",        # a fill no decision on the register covers
    "execution_against_unaccepted",  # a fill against a draft/declined decision
    "side_mismatch",                 # a fill whose side the decision does not allow
    "size_exceeded",                 # fills past the decision's quantity
    "expression_mismatch",           # executed shape != expression_family/leverage_form
    "allocation_floor_breach",       # Book A's stance below its band's floor
    "book_b_conversion",             # a Book B position closed inside 2 sessions
    "time_stop_passed",              # an active position past its time stop
    "currency_mismatch",             # a fill in a currency the decision does not express (INC-6)
)

# -----------------------------------------------------------------------------
# THE EXPRESSION VOCABULARIES -- Options as Expression, Chapter 8's map and
# Part IV's engineered payoffs, plus `outright` for the ordinary case.
#
# WHY A CLOSED VOCABULARY RATHER THAN FREE TEXT. 26.7 forbids downweighting a
# signal for an EXPRESSION loss, and that rule only pays if expression is recorded
# as its own dimension at decision time. Free text records it in a form no query
# can group: "risk reversal", "risk-reversal" and "RR" are three answers to the
# question "do our timing edges lose because the timing was wrong or because we
# keep expressing them in stock". The whole value of the field is that it can be
# grouped six months later.
#
# The `structure` argument on decide.py stays free text and keeps its job -- it
# describes a shape to the expression check. This field names the FAMILY, and the
# families are the paper's own: Chapter 8.9's map, in its order, then Part IV.
# -----------------------------------------------------------------------------
EXPRESSION_FAMILIES = (
    # The ordinary case. Not a structure, and named so that "no structure" is a
    # recorded answer rather than a blank.
    "outright",
    # Chapter 8.1-8.6: the volatility shapes, in the paper's own map order.
    "long_straddle",
    "long_strangle",
    "long_butterfly",
    "iron_condor",
    "iron_butterfly",
    "reverse_iron_butterfly",
    "collar",
    "put_spread_collar",
    "put_backspread",
    "call_backspread",
    "risk_reversal",
    "broken_wing_butterfly",
    "reverse_iron_condor",
    "double_diagonal",
    "diagonal",
    # The two-leg workhorses the map treats as given rather than listing.
    "vertical_spread",
    "calendar_spread",
    "covered_call",
    "cash_secured_put",
    "protective_put",
    # Part IV -- the engineered payoffs. Chapters 12-14.
    "buffered_fund",
    "synthetic_ppn",
    "dual_directional",
)

# -----------------------------------------------------------------------------
# HOW THE LEVERAGE IS DELIVERED -- Chapter 16.2's table, plus the PPN re-strike.
#
# 16.1: "Leverage is measured in risk, never in notional." The register already
# records risk, so this field does not size anything -- it records WHICH
# INSTRUMENT delivered a given dollar of risk, because the forms differ in
# financing cost, in whether the risk is defined, and in whether a margin call
# can arrive. A deep-in-the-money call controlling $200k with $20k at risk and a
# margin loan buying $200k with no stop are the same size in the register and are
# not remotely the same decision.
# -----------------------------------------------------------------------------
LEVERAGE_FORMS = (
    # The unlevered case, named so that "none" is recorded rather than blank.
    "none",
    "margin",                 # the broker's rate; the only form with a call risk
    "futures",                # ~8-10x on initial margin, financing in the basis
    "leaps",                  # deep-in-the-money long-dated call: stock with a floor
    "call_spread",            # highest delta per dollar at a known target
    "risk_reversal",          # skew-funded direction; NOT defined risk
    "short_box",              # SPX box sold: financing near the risk-free rate
    "ppn_restrike",           # re-striking a synthetic PPN's participation leg
    "leveraged_etf",          # days only; the variance tax is the cost
    "cash_secured_put",       # 1x on the cash reserved -- paid to wait at a level
)



class RestrictedInstrumentError(Exception):
    """Raised when a decision names an instrument the register refuses.

    Deliberately not a warning and not a filtered-out row. The architecture:
    "a recommendation tagged to a restricted entity is rejected, not warned."
    """


class PacketIncompleteError(ValueError):
    """DECISION_OK without falsifiers, invalidation or counter_thesis (EL-1).

    A ValueError, so every caller that already refuses an incomplete decision
    refuses this one; its own class, so the refusal can be named in a report.
    """


class CurrencyMismatchError(Exception):
    """The instrument's listing currency is not the packet's expression currency.

    INC-6 (1 Oct 2026): a SPY view was carried for two weeks by SPY@MEXI.MXN,
    the peso listing, and lost -8,951.36 USD mostly to the peso and the
    listing's basis. A packet now declares the currency its view is expressed in
    (USD by default); an instrument listed in another one is refused at record
    and at activation, naming both. The operator's override (--override-gate)
    is the only way past it, and it is a record.
    """


class CurrencyExposureUnstatedError(Exception):
    """A non-USD listing was named without saying what to do about the currency.

    Separate from RestrictedInstrumentError because it is not a compliance
    refusal and carries none of that weight: the instrument is permitted, the
    decision is simply incomplete. Part 31.3(c).
    """


# Portfolio Truth keys a holding `<localSymbol>@<venue>.<currency>`, and the
# register reads the same form so an instrument can be written once and mean the
# same thing in both places. A bare ticker has no currency in it and yields
# None -- unknown, not USD, because assuming USD is what let a peso listing pass
# for a dollar one.
_LISTING = re.compile(r"@[A-Za-z0-9_.-]+\.([A-Z]{3})$")


def listing_currency(instrument: Optional[str]) -> Optional[str]:
    """The ISO currency in a qualified instrument key, or None if unqualified."""
    m = _LISTING.search(str(instrument or "").strip())
    return m.group(1) if m else None


def currency_mismatch(instrument: Optional[str],
                      expression_currency: Optional[str]) -> Optional[str]:
    """The refusal text when a listing's currency is not the expression's, or None.

    INC-8 (2 Oct 2026): one rule, used by the register's write AND by
    tools/decide.py before a dry run returns, so a dry run says what the write
    would refuse. An unknown on either side -- a bare ticker, an empty
    expression currency -- is not judged: unknown is not USD."""
    ccy = listing_currency(instrument)
    expr = str(expression_currency).upper() if expression_currency else None
    if not ccy or not expr or ccy == expr:
        return None
    return (f"{instrument!r} is listed in {ccy}, but the decision expresses its "
            f"view in {expr}. A {ccy} listing carries the {ccy}/{expr} rate and "
            f"the listing's own basis as well as the market (INC-6: the "
            f"SPY@MEXI.MXN short lost mostly to the peso). Name the {expr} "
            f"listing, declare --expression-currency {ccy} if the {ccy} exposure "
            f"is the point, or record an operator override (--override-gate).")


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
    run_id           TEXT,
    -- 26.2 #7: decision eligibility is not report eligibility. A recommendation
    -- whose inputs are missing or stale is DECISION_BLOCKED -- it is still
    -- recorded, because an abstention is a decision and the register logs
    -- abstentions too, but it lands as draft and never as active.
    -- blocked_reason is why; NULL means nothing blocked it.
    signals_used     TEXT,
    blocked_reason   TEXT,
    -- Part 31.3(c). NULL is permitted because the column was added to a live
    -- register and every pre-existing row predates the field; on a NEW decision
    -- record() refuses NULL for any non-USD listing rather than defaulting it.
    currency_exposure TEXT CHECK (currency_exposure IS NULL
                                  OR currency_exposure IN {CURRENCY_EXPOSURES!r}),
    -- Options as Expression, Chapter 8 and Part IV. WHICH SHAPE the decision was
    -- expressed in, from a closed vocabulary so that six months of outcomes can be
    -- grouped by it. NULL is permitted: the column was added to a live register and
    -- every pre-existing row predates it. The expression check WARNS when an
    -- options decision leaves it unset and does not refuse -- Phase 5 is where that
    -- becomes binding.
    expression_family TEXT CHECK (expression_family IS NULL
                                  OR expression_family IN {EXPRESSION_FAMILIES!r}),
    -- Chapter 16.2. HOW the leverage was delivered, which the risk number cannot
    -- say: a deep-in-the-money call with $20k at risk and a margin loan with $20k
    -- at risk are one size and two different decisions -- one has a defined worst
    -- case and no call risk, the other has neither.
    leverage_form    TEXT CHECK (leverage_form IS NULL
                                 OR leverage_form IN {LEVERAGE_FORMS!r}),
    -- 31.1. The base rate this thesis departs from, cited BY ID and never by
    -- retyping the figure: a variant perception is a claim about a distribution,
    -- and a packet that retypes "-10% happens about once a year" cannot be
    -- replayed against the table that said so. NULL is permitted -- most
    -- decisions cite none -- and a value must name a stored observation
    -- (baserate.*) or a claims-registry id (claim:*), because free text here is
    -- the retyped figure the field exists to prevent.
    base_rate_cited  TEXT,
    -- What a supersession was FOR. The thesis is carried forward verbatim by
    -- design, so without this the trail records that a decision changed and
    -- not one word about why.
    note             TEXT,
    -- PHASE 5a. The book, a structured size, the time stop, the reason a
    -- position was closed, and the gate at entry's verdict. All nullable: the
    -- columns arrive on a live register whose rows predate them. vega_usd is
    -- dollars per one volatility point for an options expression.
    book             TEXT CHECK (book IS NULL OR book IN {BOOKS!r}),
    quantity         REAL,
    notional_usd     REAL,
    vega_usd         REAL,
    time_stop        TEXT,
    close_reason     TEXT,
    gate_outcome     TEXT CHECK (gate_outcome IS NULL
                                 OR gate_outcome IN {GATE_OUTCOMES!r}),
    gate_detail      TEXT,
    gate_override    TEXT,
    -- EL-1 (§3.1). Recorded at entry, immutable. falsifiers is a JSON list.
    -- NULL on every pre-P5-B row, which reads "not recorded".
    setup_id         TEXT,
    engine_id        TEXT,
    horizon_alignment TEXT,
    review_changed   TEXT,
    falsifiers       TEXT,
    counter_thesis   TEXT
);

-- THE ORDER GATE'S RECORD OF WHAT BROKE (Phase 5a). Written by the
-- reconciliation of fills against accepted decisions and by the Doctrine's
-- position rules; read by the close, the Weekly and the grader. Immutable, like a
-- packet: a rule break that can be edited away is not a record. dedupe_key makes
-- every writer idempotent -- the hourly sync and the close pass both run it.
CREATE TABLE IF NOT EXISTS rule_breaks (
    id           INTEGER PRIMARY KEY,
    detected_at  TEXT NOT NULL,
    session      TEXT NOT NULL,
    kind         TEXT NOT NULL CHECK (kind IN {RULE_BREAK_KINDS!r}),
    decision_id  TEXT,
    instrument   TEXT,
    exec_ids     TEXT,
    reason       TEXT NOT NULL,
    detail       TEXT,
    source       TEXT NOT NULL,
    dedupe_key   TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS rule_breaks_by_session ON rule_breaks (session);
CREATE INDEX IF NOT EXISTS rule_breaks_by_decision ON rule_breaks (decision_id);
CREATE TRIGGER IF NOT EXISTS rule_breaks_immutable_update
BEFORE UPDATE ON rule_breaks
BEGIN SELECT RAISE(ABORT, 'rule_breaks is immutable'); END;
CREATE TRIGGER IF NOT EXISTS rule_breaks_immutable_delete
BEFORE DELETE ON rule_breaks
BEGIN SELECT RAISE(ABORT, 'rule_breaks is immutable'); END;

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
    volatile_fields          TEXT NOT NULL,
    -- Gate 1.5 (26.11): the live economics of the contemplated expression --
    -- commission, margin impact, buying-power delta -- as measured by IBKR's
    -- What-If at decision time, plus any 26.7 expression warnings. NULL means
    -- no preview was run, which is DIFFERENT from a preview that found no
    -- cost, and the two must stay distinguishable: 26.16 #5 grades whether a
    -- thesis was rejected on real economics, and "we never looked" cannot be
    -- allowed to read as "it was free".
    expected_cost_json       TEXT
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
        # WAL AND A BUSY TIMEOUT, BEFORE ANY OTHER STATEMENT.
        #
        # SQLite's default rollback journal takes an EXCLUSIVE lock on the
        # whole file for a write, and the default busy_timeout is ZERO -- a
        # concurrent reader or writer does not wait, it fails immediately with
        # "database is locked". This database has several timer-driven users
        # (Portfolio Truth every 30 minutes, the close report at 16:45, the
        # nightly sweep, the decision CLI by hand) and the four flock calls in
        # scripts/ each guard their own script against a second copy of itself
        # -- none of them guards the database.
        #
        # WAL lets readers proceed while a writer works, which is the case that
        # actually collides here: a report reading the store while the sync
        # writes it. busy_timeout turns the remaining true write-write
        # collisions into a short wait instead of an error.
        #
        # The failure this prevents is named in the audit: "database is locked"
        # errors THAT LOOK LIKE DATA GAPS. altdata/store.py swallows exactly
        # this exception, so a lock collision there costs observations with no
        # trace anywhere.
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        # Databases created before 26.2 #7 landed lack these two columns.
        # ALTER is the whole migration: both are nullable and NULL means
        # "nothing blocked it", which is the right reading of a pre-existing row.
        # currency_exposure is Part 31.3(c); note carries what a supersession
        # was FOR, which the carried-forward thesis cannot say. Both nullable:
        # NULL means the field predates the column, not that it is n_a.
        for col in ("signals_used TEXT", "blocked_reason TEXT",
                    "currency_exposure TEXT", "note TEXT",
                    "base_rate_cited TEXT", "expression_family TEXT",
                    "leverage_form TEXT",
                    # Phase 5a. ALTER cannot carry a CHECK that references the
                    # vocabulary on an existing table, so record() enforces
                    # book and gate_outcome for rows written from now on.
                    "book TEXT", "quantity REAL", "notional_usd REAL",
                    "vega_usd REAL", "time_stop TEXT", "close_reason TEXT",
                    "gate_outcome TEXT", "gate_detail TEXT",
                    "gate_override TEXT",
                    # EL-1. Vocabulary enforced in record(), as for Phase 5a.
                    "setup_id TEXT", "engine_id TEXT",
                    "horizon_alignment TEXT", "review_changed TEXT",
                    "falsifiers TEXT", "counter_thesis TEXT",
                    # INC-6 follow-up. NULL on a pre-existing row reads as USD.
                    "expression_currency TEXT",
                    # INC-6 follow-up: a close's fill, structured (exit_fx_to_usd
                    # is USD per one unit of exit_currency). NULL = not recorded.
                    "exit_price REAL", "exit_time TEXT", "exit_currency TEXT",
                    "exit_fx_to_usd REAL"):
            try:
                self.conn.execute(f"ALTER TABLE decisions ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass                       # already present
        # Same migration for the packet's Gate 1.5 economics. NULL on a
        # pre-existing packet is the honest reading: no preview was run.
        try:
            self.conn.execute("ALTER TABLE decision_packets "
                              "ADD COLUMN expected_cost_json TEXT")
        except sqlite3.OperationalError:
            pass
        self.conn.commit()
        self._migrate_rule_break_kinds()
        self.restrictions = (instruments.Restrictions(entities_path)
                             if entities_path else instruments.restrictions())
        self.sync_restrictions()

    def _migrate_rule_break_kinds(self) -> None:
        """Widen rule_breaks' CHECK to the current RULE_BREAK_KINDS, keeping
        every row. (1 Oct 2026: currency_mismatch, the first kind added after
        the table existed on the box.)

        SQLite cannot ALTER a CHECK, so the table is rebuilt: copied whole into
        a table with the new constraint, the old one dropped (DROP fires no
        delete trigger, and the rows are already in the copy), the copy renamed,
        and the indexes and immutability triggers recreated from SCHEMA. One
        transaction; a no-op once the stored constraint names every kind.
        """
        row = self.conn.execute("SELECT sql FROM sqlite_master WHERE type='table'"
                                " AND name='rule_breaks'").fetchone()
        if not row or all(f"'{k}'" in (row[0] or "") for k in RULE_BREAK_KINDS):
            return
        ddl = SCHEMA[SCHEMA.index("CREATE TABLE IF NOT EXISTS rule_breaks"):]
        ddl = ddl[:ddl.index(");") + 2].replace(
            "CREATE TABLE IF NOT EXISTS rule_breaks", "CREATE TABLE rule_breaks__new")
        before = self.conn.execute("SELECT COUNT(*) FROM rule_breaks").fetchone()[0]
        cols = ("id, detected_at, session, kind, decision_id, instrument, exec_ids,"
                " reason, detail, source, dedupe_key")
        try:
            self.conn.execute("BEGIN")
            self.conn.execute(ddl)
            self.conn.execute(f"INSERT INTO rule_breaks__new ({cols}) "
                              f"SELECT {cols} FROM rule_breaks")
            after = self.conn.execute(
                "SELECT COUNT(*) FROM rule_breaks__new").fetchone()[0]
            if after != before:
                raise sqlite3.DatabaseError(
                    f"rule_breaks rebuild copied {after} of {before} rows")
            self.conn.execute("DROP TABLE rule_breaks")
            self.conn.execute("ALTER TABLE rule_breaks__new RENAME TO rule_breaks")
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
        self.conn.executescript(SCHEMA)     # indexes and triggers, IF NOT EXISTS
        self.conn.commit()

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
               decision_id: Optional[str] = None,
               signals_used: Optional[list] = None,
               blocked_reason: Optional[str] = None,
               currency_exposure: Optional[str] = None,
               base_rate_cited: Optional[str] = None,
               expression_family: Optional[str] = None,
               leverage_form: Optional[str] = None,
               note: Optional[str] = None,
               book: Optional[str] = None,
               quantity: Optional[float] = None,
               notional_usd: Optional[float] = None,
               vega_usd: Optional[float] = None,
               time_stop: Optional[str] = None,
               close_reason: Optional[str] = None,
               gate_outcome: Optional[str] = None,
               gate_detail: Optional[dict] = None,
               gate_override: Optional[str] = None,
               setup_id: Optional[str] = None,
               engine_id: Optional[str] = None,
               horizon_alignment: Optional[str] = None,
               review_changed: Optional[str] = None,
               falsifiers: Optional[list] = None,
               counter_thesis: Optional[str] = None,
               expression_currency: Optional[str] = "USD",
               exit_price: Optional[float] = None,
               exit_time: Optional[str] = None,
               exit_currency: Optional[str] = None,
               exit_fx_to_usd: Optional[float] = None,
               becoming_active: bool = True) -> str:
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

        # PART 31.3(c). A non-USD listing carries a currency leg the ticker
        # hides, and the register will not accept one unless the operator has
        # named the leg on purpose. This is the rule that would have refused the
        # 17 September 2026 exit: the order was submitted against SPY on MEXI in
        # pesos rather than SPY on ARCA in dollars, and nothing asked why a
        # dollar book was suddenly taking peso exposure.
        ccy = listing_currency(instrument)
        # 31.1: A CITATION, NOT A FIGURE. The prefixes are the whole check and they
        # are enough: `baserate.` names an observation whose table can be read back
        # as of the decision's own cutoff, and `claim:` names a claims-registry
        # entry with a source and a review date. Free text would be the retyped
        # number, which is exactly what citing by id exists to stop -- a packet
        # saying "-10% about once a year" cannot be replayed, and the same sentence
        # is true of two different tables.
        if base_rate_cited is not None and not str(base_rate_cited).startswith(
                ("baserate.", "claim:")):
            raise ValueError(
                f"base_rate_cited must name a stored base-rate observation "
                f"('baserate.<table>' or 'baserate.<table>|<field.path>') or a "
                f"claims-registry id ('claim:<id>'); got "
                f"{base_rate_cited!r}. A retyped figure cannot be replayed")
        # THE VOCABULARY IS ENFORCED, THE RULES ARE NOT -- yet. A value outside the
        # list is refused here, because a typo would silently create a
        # twenty-fourth family that no query groups with the one it meant. Whether
        # the field is REQUIRED for a given decision is the expression check's
        # question, and it warns rather than blocking until Phase 5.
        if (expression_family is not None
                and expression_family not in EXPRESSION_FAMILIES):
            raise ValueError(
                f"expression_family must be one of {EXPRESSION_FAMILIES}; got "
                f"{expression_family!r}. Free text here would create a family no "
                f"query can group with the one it meant")
        if leverage_form is not None and leverage_form not in LEVERAGE_FORMS:
            raise ValueError(
                f"leverage_form must be one of {LEVERAGE_FORMS}; got "
                f"{leverage_form!r}")
        if currency_exposure is not None and currency_exposure not in CURRENCY_EXPOSURES:
            raise ValueError(f"currency_exposure must be one of "
                             f"{CURRENCY_EXPOSURES}")
        if ccy and ccy != "USD" and currency_exposure is None:
            raise CurrencyExposureUnstatedError(
                f"{instrument!r} is denominated in {ccy}, not USD. Part 31.3(c) "
                f"requires currency_exposure on any non-USD underlying -- a "
                f"hedged and an unhedged instrument on the same market are two "
                f"different instruments. Pass hedged or unhedged deliberately; "
                f"if this listing is not the one you meant, that is the point "
                f"of this refusal.")

        # INC-6 / INC-8: THE LISTING CURRENCY MUST BE THE EXPRESSION CURRENCY,
        # on EVERY write -- a new decision and any supersede, closing included
        # (INC-8: the 1 Oct guard checked draft and activation only, and a close
        # written with an invented "USD" on a peso listing passed). Closing a
        # wrong-listing position is not trapped by this: tools/decide.py carries an
        # empty currency forward from the listing's own suffix, so the close of a
        # peso listing is a peso expression. A bare ticker or an EMPTY expression
        # currency is not judged -- empty is stored as NULL, never as "USD".
        expr = str(expression_currency).upper() if expression_currency else None
        if expr is not None and not re.fullmatch(r"[A-Z]{3}", expr):
            raise ValueError(f"expression_currency must be a 3-letter ISO code; "
                             f"got {expression_currency!r}")
        refusal = currency_mismatch(instrument, expr)
        if refusal and not gate_override:
            raise CurrencyMismatchError(refusal)

        # THE EXIT, STRUCTURED (INC-6 follow-up). A close used to carry its fill
        # in --note free text and its decision_time was the instant the command
        # ran; the realised P&L could not be computed from either.
        if exit_price is not None and not float(exit_price) > 0:
            raise ValueError(f"exit_price must be positive; got {exit_price!r}")
        if exit_time is not None and not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)",
                str(exit_time)):
            raise ValueError(f"exit_time must be an ISO instant in UTC "
                             f"(…+00:00 or Z); got {exit_time!r}")
        if exit_currency is not None and not re.fullmatch(r"[A-Z]{3}",
                                                          str(exit_currency)):
            raise ValueError(f"exit_currency must be a 3-letter ISO code; got "
                             f"{exit_currency!r}")
        if exit_fx_to_usd is not None and not float(exit_fx_to_usd) > 0:
            raise ValueError(f"exit_fx_to_usd must be positive (USD per unit of "
                             f"exit_currency); got {exit_fx_to_usd!r}")
        if exit_currency == "USD" and exit_fx_to_usd not in (None, 1, 1.0):
            raise ValueError("exit_fx_to_usd for a USD exit is 1")

        if book is not None and book not in BOOKS:
            raise ValueError(f"book must be one of {BOOKS}; got {book!r}")
        if gate_outcome is not None and gate_outcome not in GATE_OUTCOMES:
            raise ValueError(f"gate_outcome must be one of {GATE_OUTCOMES}")
        if time_stop is not None and not re.fullmatch(r"\d{4}-\d{2}-\d{2}",
                                                      str(time_stop)):
            raise ValueError(f"time_stop must be YYYY-MM-DD; got {time_stop!r}")

        # EL-1: the vocabularies, enforced on every write.
        if setup_id is not None and setup_id not in setup_ids():
            raise ValueError(
                f"setup_id must be a family in config/setups.yaml (or "
                f"`unclassified`); got {setup_id!r}")
        if engine_id is not None and engine_id not in ENGINE_IDS:
            raise ValueError(f"engine_id must be one of {ENGINE_IDS}; got "
                             f"{engine_id!r}")
        if (horizon_alignment is not None
                and horizon_alignment not in HORIZON_ALIGNMENTS):
            raise ValueError(f"horizon_alignment must be one of "
                             f"{HORIZON_ALIGNMENTS}")
        if review_changed is not None and review_changed not in REVIEW_CHANGED:
            raise ValueError(f"review_changed must be one of {REVIEW_CHANGED}")
        if falsifiers is not None:
            falsifiers = [str(f).strip() for f in falsifiers if str(f).strip()]
        if counter_thesis is not None:
            counter_thesis = " ".join(str(counter_thesis).split())

        did = decision_id or str(uuid.uuid4())
        now = session.utc_iso()

        # THE 26.2 #7 SEMANTIC, ENFORCED HERE RATHER THAN IN THE CALLER. A
        # blocked decision cannot be active, whoever asks. Downgrading in the
        # CLI alone would leave the invariant one careless caller away from
        # being false, and this is the invariant the whole check exists for.
        if blocked_reason and status == "active":
            status = "draft"
        # PHASE 5a -- THE GATE AT ENTRY, ENFORCED HERE TOO. A decision reaches
        # DECISION_OK (active) only if the register accepts it: it names a book,
        # and the gate did not answer delay or reject -- unless the operator
        # recorded an override, which is the only way past a refusal and is
        # itself a record.
        # ON THE TRANSITION, NOT ON A TOUCH. A row that was already active and is
        # re-recorded to annotate it (a thesis_state, a note) predates Phase 5a
        # if it has no book, and refusing that write would leave the register
        # unable to describe its own open position. decide.py set-status passes
        # becoming_active=False when the predecessor was already active.
        if status == "active" and book is None and becoming_active:
            raise ValueError(
                "an active decision must name its book (A/B/C/D): the cross-book "
                "heat view and the Doctrine's book rules cannot see it otherwise")
        # ANY VERDICT BUT approve HOLDS THE DECISION IN DRAFT. A resize the
        # register activated at the full size would be a limit that limits
        # nothing; the operator re-records at the size the gate named, or records
        # an override, and either is on the record.
        if (status == "active" and gate_outcome not in (None, "approve")
                and not gate_override):
            status = "draft"
            blocked_reason = (blocked_reason or "") + (
                ("; " if blocked_reason else "")
                + f"gate at entry: {gate_outcome}")

        # RED TEAM v0, AT WRITE TIME -- after the downgrades above, because a
        # blocked or gate-held request lands as draft and is not DECISION_OK.
        # DECISION_OK (active) is refused without a
        # falsifier, an invalidation and a counter-thesis -- whoever asks, like
        # the Brookfield refusal, so no caller can forget it. On the transition,
        # as for the book: a pre-P5-B row re-recorded while already active is
        # describing a position that exists, not entering one.
        if status == "active" and becoming_active:
            missing = [n for n, v in (("falsifiers", falsifiers),
                                      ("invalidation", (invalidation or "").strip()),
                                      ("counter_thesis", counter_thesis))
                       if not v]
            if missing:
                raise PacketIncompleteError(
                    f"DECISION_OK refused: the packet has no "
                    f"{', '.join(missing)}. EL-1 (Red Team v0): an active decision "
                    f"states at entry what would show it wrong (>= 1 falsifier), "
                    f"where it ends (invalidation), and the other side's case in "
                    f"one sentence (counter_thesis)")

        self.conn.execute(
            "INSERT INTO decisions (id, created_at, decision_time, instrument,"
            " instrument_norm, direction, thesis, edge_type, horizon, size,"
            " invalidation, status, operator_action, thesis_state, run_id,"
            " signals_used, blocked_reason, currency_exposure,"
            " base_rate_cited, expression_family, leverage_form, note,"
            " book, quantity, notional_usd, vega_usd, time_stop, close_reason,"
            " gate_outcome, gate_detail, gate_override,"
            " setup_id, engine_id, horizon_alignment, review_changed,"
            " falsifiers, counter_thesis, expression_currency,"
            " exit_price, exit_time, exit_currency, exit_fx_to_usd)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,"
            "         ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (did, now, decision_time or now, instrument, norm, direction,
             thesis, edge_type, horizon, size, invalidation, status,
             operator_action, thesis_state, run_id,
             json.dumps(signals_used or []), blocked_reason,
             currency_exposure, base_rate_cited, expression_family,
             leverage_form, note, book, quantity, notional_usd, vega_usd,
             time_stop, close_reason, gate_outcome,
             (json.dumps(gate_detail, sort_keys=True, default=str)
              if gate_detail is not None else None), gate_override,
             setup_id, engine_id, horizon_alignment, review_changed,
             (json.dumps(falsifiers) if falsifiers is not None else None),
             counter_thesis, expr, exit_price, exit_time, exit_currency,
             exit_fx_to_usd))
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
            " source_registry_version, output_hash, volatile_fields,"
            " expected_cost_json)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (pid, decision_id, session.utc_iso(), packet["run_id"],
             packet["decision_time"], packet["available_at_cutoff"],
             packet["git_sha"], int(packet.get("code_dirty", 0)),
             packet["data_manifest_hash"],
             json.dumps(packet.get("data_manifest", {}), sort_keys=True),
             str(packet["metrics_registry_version"]),
             str(packet["source_registry_version"]),
             packet["output_hash"],
             json.dumps(sorted(packet.get("volatile_fields", []))),
             (json.dumps(packet["expected_cost"], sort_keys=True, default=str)
              if packet.get("expected_cost") is not None else None)))
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
        if status == "active":
            row = self.get(decision_id)
            if row and row.get("blocked_reason"):
                raise ValueError(
                    f"decision {decision_id} is DECISION_BLOCKED "
                    f"({row['blocked_reason']}) and cannot be made active. "
                    f"Clear the block by refreshing its inputs and recording a "
                    f"new decision; a blocked row is not promoted in place.")
            # EL-1 holds for the in-place writer too: a draft promoted here
            # without the three fields would be DECISION_OK by the back door.
            if row and row.get("status") != "active":
                fals = json.loads(row.get("falsifiers") or "null")
                missing = [n for n, v in (
                    ("falsifiers", fals),
                    ("invalidation", (row.get("invalidation") or "").strip()),
                    ("counter_thesis", row.get("counter_thesis"))) if not v]
                if missing:
                    raise PacketIncompleteError(
                        f"decision {decision_id} cannot be made active: no "
                        f"{', '.join(missing)} (EL-1). Record a new decision "
                        f"with them.")
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

    # -- rule breaks (Phase 5a) ---------------------------------------------
    def write_rule_break(self, *, kind: str, session_day: str, reason: str,
                         dedupe_key: str, source: str,
                         decision_id: Optional[str] = None,
                         instrument: Optional[str] = None,
                         exec_ids: Optional[list] = None,
                         detail: Optional[dict] = None) -> bool:
        """Write one rule break; False when that dedupe_key is already recorded."""
        if kind not in RULE_BREAK_KINDS:
            raise ValueError(f"kind must be one of {RULE_BREAK_KINDS}")
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO rule_breaks (detected_at, session, kind,"
            " decision_id, instrument, exec_ids, reason, detail, source,"
            " dedupe_key) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (session.utc_iso(), session_day, kind, decision_id, instrument,
             json.dumps(exec_ids or []), reason,
             json.dumps(detail or {}, sort_keys=True, default=str), source,
             dedupe_key))
        self.conn.commit()
        return cur.rowcount > 0

    def rule_breaks(self, since: Optional[str] = None,
                    decision_id: Optional[str] = None) -> list[dict]:
        q, args = "SELECT * FROM rule_breaks WHERE 1=1", []
        if since:
            q += " AND session >= ?"
            args.append(since)
        if decision_id:
            q += " AND decision_id = ?"
            args.append(decision_id)
        return [dict(r) for r in self.conn.execute(q + " ORDER BY id", args)]

    def open_decisions(self) -> list[dict]:
        """Active, unsuperseded decisions: what the heat view sums."""
        cur = self.conn.execute(
            "SELECT * FROM decisions WHERE status = 'active' "
            "AND superseded_by IS NULL ORDER BY created_at")
        return [dict(r) for r in cur.fetchall()]

    def blocked_attempts(self) -> list[dict]:
        cur = self.conn.execute(
            "SELECT * FROM blocked_attempts ORDER BY attempted_at")
        return [dict(r) for r in cur.fetchall()]
