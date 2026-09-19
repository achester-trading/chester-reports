"""
One-off repair: re-key Portfolio Truth position rows, and restore the leg the
store threw away.

WHY THIS EXISTS
---------------
Until 19 September 2026 a holding was stored under `localSymbol`. That key
separates two options on one underlying -- the case it was chosen for -- and
fails on a cross-listing, where one issue trades on two exchanges in two
currencies under a single localSymbol.

On 17 September 2026 at 13:31 UTC the account held SPY twice: conId 756733 on
ARCA in USD (long 100, the position decision fae90045 was recorded against) and
conId 38709152 on MEXI in MXN (short 100, opened when an exit order was
submitted against the wrong listing). Both keyed to `SPY`. Both therefore
produced the same idempotence tuple in `obs_vintage`, and `write_many`'s
`INSERT OR IGNORE` kept whichever IBKR served first -- the peso short -- and
discarded the dollar long. For 35 consecutive syncs the store asserted a
Mexican-peso short of 100 SPY and held no record at all of a live
hundred-share dollar long.

WHAT THIS DOES
--------------
Rebuilds the affected rows from the authoritative record of what the broker
actually returned: the `updatePortfolio:` lines in the Gateway sync log, which
carry conId, primaryExchange, currency and every value, per sync.

  1. Existing rows are RE-KEYED, not revised. A row's value was correct for the
     leg it described; only its `instrument` was wrong -- it said `SPY` when it
     meant `SPY@MEXI.MXN`. Re-keying is therefore a correction of the label, and
     the value, its vintage and its run_id are left exactly as written. Each
     re-key is verified against the log's value before it is applied and the
     script refuses on any mismatch rather than guessing.
  2. The DISCARDED leg's rows are INSERTED. They are not revisions of anything;
     they were never written. They carry the same observed_at, available_at,
     source and run_id the sync would have given them, so the reconstructed
     history is point-in-time identical to what a correct sync would have
     produced.
  3. `portfolio.position_currency` and `portfolio.position_con_id` are inserted
     for every holding, so no reader has to infer a currency from a key.

The script is idempotent: a second run finds nothing to do. It writes only with
--apply; the default is a dry run that prints the plan.

    python tools/backfill_position_keys.py --log ~/logs/ibkr_sync-2026-09.log
    python tools/backfill_position_keys.py --log ~/logs/ibkr_sync-2026-09.log --apply
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata.sources.ibkr_portfolio import instrument_key   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78

VALUE_FIELDS = (("portfolio.position_qty", "position"),
                ("portfolio.position_avg_cost", "avg_cost"),
                ("portfolio.position_market_value", "market_value"),
                ("portfolio.position_unrealized_pnl", "unrealized_pnl"))
TEXT_FIELDS = (("portfolio.position_currency", "currency"),)
NUM_EXTRA = (("portfolio.position_con_id", "con_id"),)

# `updatePortfolio: PortfolioItem(contract=Stock(conId=..., symbol='SPY', ...),
#  position=-100.0, marketPrice=..., marketValue=..., averageCost=...,
#  unrealizedPNL=..., realizedPNL=..., account='...')`
ITEM_RE = re.compile(r"updatePortfolio:\s*PortfolioItem\((?P<body>.*)\)\s*$")
SYNC_SPLIT_RE = re.compile(r"^\S+ === sync start ", re.M)
READ_AT_RE = re.compile(r"^\s*read at\s*:\s*(?P<ts>\S+)\s*$", re.M)


def _field(body: str, name: str, quoted: bool = False):
    """Pull one kwarg out of a repr'd PortfolioItem body."""
    pat = (rf"\b{name}='(?P<v>[^']*)'" if quoted
           else rf"\b{name}=(?P<v>-?[\d.]+|None)")
    m = re.search(pat, body)
    if not m:
        return None
    v = m.group("v")
    if quoted:
        return v or None
    if v == "None":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def parse_log(path: Path) -> list[dict]:
    """One entry per sync that returned at least one holding, in file order.

    The holdings are kept IN THE ORDER THE LOG REPORTS THEM, because that order
    is load-bearing: `ib.portfolio()` returned them in it, `to_observations`
    emitted them in it, and `INSERT OR IGNORE` therefore kept the first and
    dropped the rest. Reconstructing which row survived depends on it.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    syncs = []
    for chunk in SYNC_SPLIT_RE.split(text)[1:]:
        at = READ_AT_RE.search(chunk)
        if not at:
            continue                     # a sync that died before it read
        holdings = []
        for line in chunk.splitlines():
            m = ITEM_RE.search(line)
            if not m:
                continue
            body = m.group("body")
            holdings.append({
                "con_id": _field(body, "conId"),
                "symbol": _field(body, "symbol", quoted=True),
                "local_symbol": _field(body, "localSymbol", quoted=True),
                "primary_exchange": _field(body, "primaryExchange", quoted=True),
                "currency": _field(body, "currency", quoted=True),
                "position": _field(body, "position"),
                "avg_cost": _field(body, "averageCost"),
                "market_value": _field(body, "marketValue"),
                "unrealized_pnl": _field(body, "unrealizedPNL"),
            })
        if holdings:
            syncs.append({"read_at": at.group("ts"), "holdings": holdings})
    return syncs


def plan(conn: sqlite3.Connection, syncs: list[dict]) -> tuple[list, list, list]:
    """(rekeys, inserts, problems) -- computed, nothing written."""
    rekeys: list[tuple] = []
    inserts: list[tuple] = []
    problems: list[str] = []

    for s in syncs:
        read_at, holdings = s["read_at"], s["holdings"]
        keys = [instrument_key(h) for h in holdings]
        if len(set(keys)) != len(keys):
            problems.append(f"{read_at}: holdings still collide under the new "
                            f"key ({keys}) -- widen instrument_key()")
            continue

        rows = conn.execute(
            "SELECT id, registry_key, instrument, value_num, source, run_id, "
            "       available_at, ingested_at "
            "  FROM observations "
            " WHERE observed_at = ? AND registry_key LIKE 'portfolio.position%'",
            (read_at,)).fetchall()
        by_key = {}
        for r in rows:
            by_key.setdefault(r["registry_key"], []).append(r)

        survivor = holdings[0]
        for rk, field in VALUE_FIELDS:
            got = by_key.get(rk) or []
            if survivor.get(field) is None:
                continue
            unkeyed = [r for r in got if "@" not in (r["instrument"] or "")]
            if not unkeyed:
                continue                 # already re-keyed; idempotent
            if len(unkeyed) > 1:
                problems.append(f"{read_at} {rk}: {len(unkeyed)} unkeyed rows, "
                                f"expected 1")
                continue
            row = unkeyed[0]
            # The row that survived belongs to the FIRST holding. Prove it from
            # the value before relabelling anything -- a wrong label is the bug
            # being fixed, and guessing a second one would be worse.
            if abs((row["value_num"] or 0) - survivor[field]) > 1e-6:
                problems.append(
                    f"{read_at} {rk}: stored {row['value_num']} does not match "
                    f"the log's first holding {survivor[field]} "
                    f"(conId {survivor.get('con_id')}) -- refusing to re-key")
                continue
            rekeys.append((keys[0], row["id"]))

        # Every holding needs its currency and conId; every holding after the
        # first needs its four values, which were never written at all.
        for h, key in zip(holdings, keys):
            first = h is holdings[0]
            src, run_id, avail, ing = _vintage(rows, read_at)
            if src is None:
                problems.append(f"{read_at}: no existing row to take source and "
                                f"run_id from; cannot reconstruct the vintage")
                continue
            fields = list(TEXT_FIELDS) + list(NUM_EXTRA)
            if not first:
                fields = list(VALUE_FIELDS) + fields
            for rk, field in fields:
                if h.get(field) is None:
                    continue
                if any(r["registry_key"] == rk and r["instrument"] == key
                       for r in rows):
                    continue             # already present; idempotent
                is_text = (rk, field) in TEXT_FIELDS
                inserts.append((rk, key, read_at, avail, ing,
                                None if is_text else h[field],
                                h[field] if is_text else None, src, run_id))
    return rekeys, inserts, problems


def _vintage(rows, read_at):
    """source / run_id / available_at / ingested_at of this sync's own rows."""
    for r in rows:
        return r["source"], r["run_id"], r["available_at"], r["ingested_at"]
    return None, None, read_at, read_at


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=os.environ.get("CHESTER_DB", "data/chester.db"))
    ap.add_argument("--log", required=True,
                    help="Gateway sync log carrying the updatePortfolio lines")
    ap.add_argument("--apply", action="store_true",
                    help="write the repair; omit for a dry run")
    args = ap.parse_args()

    log = Path(os.path.expanduser(args.log))
    if not log.is_file():
        print(f"no such log: {log}")
        return 2

    syncs = parse_log(log)
    print(f"{LINE}\nPosition-key backfill\n{LINE}")
    print(f"  log           : {log}")
    print(f"  db            : {args.db}")
    print(f"  syncs w/ rows : {len(syncs)}")
    print(f"  holdings seen : {sum(len(s['holdings']) for s in syncs)}")
    legs = sorted({instrument_key(h) for s in syncs for h in s["holdings"]})
    print(f"  distinct legs : {len(legs)}")
    for k in legs:
        n = sum(1 for s in syncs for h in s["holdings"]
                if instrument_key(h) == k)
        print(f"                  {k}  ({n} syncs)")

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    rekeys, inserts, problems = plan(conn, syncs)

    print(f"\n  re-key        : {len(rekeys)} existing rows relabelled")
    print(f"  insert        : {len(inserts)} rows the store never held")
    if problems:
        print(f"\n  PROBLEMS ({len(problems)}) -- nothing will be written:")
        for p in problems[:20]:
            print(f"    {p}")
        if len(problems) > 20:
            print(f"    ... and {len(problems) - 20} more")
        print(LINE)
        return 1

    if not args.apply:
        print(f"\n  DRY RUN -- nothing written. Re-run with --apply.")
        print(LINE)
        return 0

    with conn:
        conn.executemany(
            "UPDATE observations SET instrument = ? WHERE id = ?", rekeys)
        conn.executemany(
            "INSERT OR IGNORE INTO observations "
            "(registry_key, instrument, observed_at, available_at, ingested_at,"
            " value_num, value_text, source, run_id) VALUES (?,?,?,?,?,?,?,?,?)",
            inserts)

    left = conn.execute(
        "SELECT COUNT(*) FROM observations "
        " WHERE registry_key LIKE 'portfolio.position%' "
        "   AND instrument NOT LIKE '%@%'").fetchone()[0]
    print(f"\n  APPLIED -- {len(rekeys)} re-keyed, {len(inserts)} inserted")
    print(f"  unkeyed position rows remaining: {left}")
    for k in legs:
        row = conn.execute(
            "SELECT value_num, observed_at FROM observations "
            " WHERE registry_key = 'portfolio.position_qty' AND instrument = ? "
            " ORDER BY observed_at DESC LIMIT 1", (k,)).fetchone()
        if row:
            print(f"    {k:<20} latest qty {row['value_num']:>8}  "
                  f"at {row['observed_at'][:19]}")
    print(LINE)
    return 0 if left == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
