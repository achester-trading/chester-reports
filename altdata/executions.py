"""
The executions table -- what actually filled, at what price, for what commission.

-----------------------------------------------------------------------------
WHY THIS DID NOT EXIST, AND WHAT ITS ABSENCE COST
-----------------------------------------------------------------------------
Three read-only IBKR services were built: Portfolio Truth (what is held),
What-If (what a trade would cost before it is placed) and Costs (estimates).
Nothing read what actually HAPPENED. `reqExecutions` and `ExecutionFilter`
appeared nowhere in the repository, so there was no fill price, no commission and
no fill time for any position, on any box.

That gap had a concrete cost on 19 September. The close report's portfolio block
was asked to print "fill price and commission from the execution record" and had to
print two dashed columns with a reason instead. Worse, the 17 September exit --
submitted against SPY on MEXI in pesos rather than SPY on ARCA in dollars -- had to
be reconstructed by diffing two half-hourly position snapshots against the raw
Gateway log, because nothing recorded the fill itself. A system that knows what it
holds but not how it got there cannot grade its own execution, which is the whole
of Part 7's error decomposition: a right thesis filled badly and a wrong thesis are
different failures and look identical without this table.

READ-ONLY PERMITS IT. Reading executions is not placing orders. Every service
still connects with readonly=True and
tools/validate_ibkr_portfolio.py still proves no order-placing call exists in the
source; this adds a second read to a read-only client.

-----------------------------------------------------------------------------
execId IS THE IDEMPOTENCE KEY, AND IT IS THE BROKER'S
-----------------------------------------------------------------------------
IBKR assigns every fill a globally unique execId. So the primary key is that
string and re-running the sync is a no-op -- no expression index, no vintage
tuple, none of the machinery the observation store needs, because the source
already solved the problem. A partial fill is several executions with several
execIds and is stored as several rows, which is correct: they happened at
different prices and the average is a derived number, not a fact.

COMMISSION ARRIVES SEPARATELY, AND LATE IS NOT NEVER. IBKR delivers a
CommissionReport on its own schedule, sometimes after the execution it belongs to.
So a row may be written with commission NULL and completed later, and the writer
therefore UPDATES a NULL commission but never overwrites one that is already
recorded. A fill is a fact; the first complete version of it is the one kept.

-----------------------------------------------------------------------------
WHAT IS NOT RECOVERABLE, STATED PLAINLY
-----------------------------------------------------------------------------
`reqExecutions` returns the CURRENT DAY's executions only -- IBKR does not serve
history through it, and the Gateway is restarted nightly. Every fill before this
table existed is therefore gone from the API's point of view, including the 17
September one that matters most. It is reconstructable from the raw Gateway log and
from the position snapshots either side of it, and that reconstruction is in the
commit history, not in this table. Monday's fills are the first rows, and the table
does not pretend otherwise.
"""

from __future__ import annotations

import datetime as dt
import logging
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional

from . import observations, session

log = logging.getLogger("altdata.executions")

REPO = Path(__file__).resolve().parent.parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS executions (
    -- IBKR's own globally unique id. The natural key, so a re-sync is a no-op
    -- and no vintage tuple has to be invented to make one.
    exec_id       TEXT PRIMARY KEY,
    account       TEXT,
    order_id      INTEGER,
    perm_id       INTEGER,
    con_id        INTEGER,
    symbol        TEXT,
    local_symbol  TEXT,
    sec_type      TEXT,
    exchange      TEXT,
    currency      TEXT,
    -- The SAME instrument key Portfolio Truth writes,
    -- `<localSymbol>@<venue>.<currency>`, so a fill joins to the position it
    -- moved without a translation step. The 17 September exit is the argument
    -- for this: `SPY` would have matched both listings and told nobody anything.
    instrument    TEXT,
    side          TEXT,          -- BOT / SLD, as IBKR reports it
    qty           REAL,
    price         REAL,
    avg_price     REAL,
    cum_qty       REAL,
    -- The broker's fill time, normalised to UTC. NOT the ingest time: a fill
    -- that happened at the open and was read at 16:30 is a fact about the open.
    exec_time     TEXT,
    -- NULL until the CommissionReport arrives, which IBKR may deliver later.
    commission    REAL,
    commission_currency TEXT,
    realized_pnl  REAL,
    order_ref     TEXT,
    last_liquidity INTEGER,
    ingested_at   TEXT NOT NULL,
    run_id        TEXT,
    source        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS exec_by_instrument ON executions (instrument, exec_time);
CREATE INDEX IF NOT EXISTS exec_by_time       ON executions (exec_time);
CREATE INDEX IF NOT EXISTS exec_by_con_id     ON executions (con_id, exec_time);
"""


def _utc(value: Any) -> Optional[str]:
    """A broker timestamp as UTC ISO, or None. Never raises."""
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        d = value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc).isoformat()
    text = str(value).strip()
    if not text:
        return None
    try:
        d = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text                      # keep it rather than drop it
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc).isoformat()


def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
        return None if f != f else f     # NaN is not a number
    except (TypeError, ValueError):
        return None


def _int(v: Any) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


class ExecutionStore:
    """The executions table, in the same database as the observation store."""

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = Path(path or observations.DEFAULT_DB)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        # Same reasoning as the register and the observation store: several
        # timer-driven writers share this file, and the default busy_timeout of
        # zero turns a concurrent read into "database is locked" rather than a
        # short wait.
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "ExecutionStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def write_many(self, rows: Iterable[dict], run_id: Optional[str] = None) -> dict:
        """Insert fills; complete a NULL commission on one already stored.

        Returns counts rather than a bare number, because "nothing was written"
        has two very different causes -- every fill already known, or no fill
        served -- and a single 0 cannot tell them apart.
        """
        ingested = session.utc_iso()
        inserted = updated = skipped = 0
        for r in rows:
            if not r.get("exec_id"):
                continue                 # without the broker's key there is no row
            cols = {
                "exec_id": r.get("exec_id"), "account": r.get("account"),
                "order_id": _int(r.get("order_id")),
                "perm_id": _int(r.get("perm_id")),
                "con_id": _int(r.get("con_id")), "symbol": r.get("symbol"),
                "local_symbol": r.get("local_symbol"),
                "sec_type": r.get("sec_type"), "exchange": r.get("exchange"),
                "currency": r.get("currency"), "instrument": r.get("instrument"),
                "side": r.get("side"), "qty": _num(r.get("qty")),
                "price": _num(r.get("price")),
                "avg_price": _num(r.get("avg_price")),
                "cum_qty": _num(r.get("cum_qty")),
                "exec_time": _utc(r.get("exec_time")),
                "commission": _num(r.get("commission")),
                "commission_currency": r.get("commission_currency"),
                "realized_pnl": _num(r.get("realized_pnl")),
                "order_ref": r.get("order_ref"),
                "last_liquidity": _int(r.get("last_liquidity")),
                "ingested_at": ingested,
                "run_id": run_id or r.get("run_id"),
                "source": r.get("source") or "ibkr",
            }
            names = list(cols)
            cur = self.conn.execute(
                f"INSERT OR IGNORE INTO executions ({','.join(names)}) "
                f"VALUES ({','.join('?' * len(names))})",
                [cols[n] for n in names])
            if cur.rowcount:
                inserted += 1
                continue
            # Already known. The ONE field allowed to arrive late is the
            # commission, and only from NULL -- a recorded commission is never
            # overwritten, because a fill is a fact and the first complete
            # version of it is the one kept.
            if cols["commission"] is not None:
                cur = self.conn.execute(
                    "UPDATE executions SET commission = ?, "
                    "       commission_currency = COALESCE(?, commission_currency), "
                    "       realized_pnl = COALESCE(realized_pnl, ?) "
                    " WHERE exec_id = ? AND commission IS NULL",
                    (cols["commission"], cols["commission_currency"],
                     cols["realized_pnl"], cols["exec_id"]))
                if cur.rowcount:
                    updated += 1
                    continue
            skipped += 1
        self.conn.commit()
        return {"inserted": inserted, "commission_completed": updated,
                "already_known": skipped}

    # -- reads -------------------------------------------------------------
    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM executions").fetchone()[0]

    def for_instrument(self, instrument: str, limit: int = 50) -> list[dict]:
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM executions WHERE instrument = ? "
            "ORDER BY exec_time DESC LIMIT ?", (instrument, limit))]

    def latest(self, limit: int = 20) -> list[dict]:
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM executions ORDER BY exec_time DESC LIMIT ?", (limit,))]

    def missing_commission(self) -> list[dict]:
        """Fills whose commission has not arrived. Worth surfacing, not hiding."""
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM executions WHERE commission IS NULL "
            "ORDER BY exec_time DESC")]
