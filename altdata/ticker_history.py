"""
The ticker history chester-meme's guard reads (AUD-3b Part 2; its spec section 3,
R-T1a-3), rebuilt the same way every morning and never hand-edited.

INPUTS: the daily listings snapshots (altdata/listings.py), the FIGI assignment
log (altdata/figi.py, append-only: which composite FIGI a symbol was mapped to,
from which day), and the master's known windows (config/security_master.yaml).

THE RULES, one composite FIGI at a time, walking the snapshots in date order:

  rename         same FIGI, same ticker, new name             -> nothing changes
  ticker change  same FIGI, new ticker                        -> the old row closes
                 and a new one opens, on the snapshot date
  reuse          a different FIGI on a known ticker           -> the old holder's row
                 closes with an EXACT, EXCLUSIVE effective_to on the snapshot date,
                 and the new holder's row opens from it
  delisting      the ticker gone                              -> its row closes
  new listing    a FIGI first seen after the first snapshot   -> a row from the day
                 after the PREVIOUS snapshot (ruled 16 Oct 2026, aud-3b Needs-you 9),
                 so a missed morning makes the start early, never late. Exact on
                 consecutive trading days but for the weekend's calendar days, on
                 which nothing trades. A reused ticker's new holder still opens on
                 the snapshot date, where the old holder's row closes, so the two
                 never overlap
                 (from_known false only after a missed morning, ruled 15 Oct;
                 the start date is the 16 Oct ruling's)

Where a boundary falls between two snapshots and the master knows its real date
(BAM in 2022, SPCX in 2026, the ETF's SPCX -> SPCK in April 2026), the master's
date is used, never the later snapshot's.

UNKNOWN STARTS. On the first snapshot every holding is already running. Where the
master knows when it began, the row carries that date. Otherwise effective_from
is 1900-01-01 and the row carries from_known: false, so chester-meme's guard
keeps its present assumption ("no ticker changed hands") for every unknown
start: it repairs only what is known and never wipes history for want of a date.

A MISSED MORNING (ruled 15 Oct 2026, built 17 Oct). The snapshot date is a new
listing's exact start only when the two snapshots are consecutive sessions. When
a session falls between them (the 06:45 job missed a morning), the listing began
on some day in the gap, so the row starts on the day after the previous snapshot
and carries from_known: false. Starting it on the later snapshot would state a
start too late, and chester-meme's guard nulls a listing's rows before a stated
start; the earlier bound never wipes history. Sessions are counted by the session
calendar (derived.sessions_between), so a weekend or a holiday is no miss. The
master's known date still wins where it falls in the gap. Ticker changes and
reuse keep the snapshot date: the ruling names new listings.

Dates: effective_from inclusive, effective_to EXCLUSIVE (the contract's). The
master's active_to is inclusive, so a master window ending on D exports as
effective_to D + 1.
"""

from __future__ import annotations

import bisect
import datetime as dt
from typing import Optional

SENTINEL = "1900-01-01"


def _next(day: str) -> str:
    return (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()


class Assignments:
    """figi_of(symbol, day): the FIGI a symbol was mapped to as of `day`; before
    its first mapping, its first (the holder when first seen)."""

    def __init__(self, rows: list[dict]) -> None:
        self.by: dict[str, list[tuple[str, str]]] = {}
        for r in sorted(rows, key=lambda r: (r["symbol"], r["date"])):
            self.by.setdefault(r["symbol"], []).append((r["date"], r["figi"]))

    def figi_of(self, symbol: str, day: str) -> Optional[str]:
        xs = self.by.get(symbol)
        if not xs:
            return None
        i = bisect.bisect_right([d for d, _ in xs], day) - 1
        return xs[max(i, 0)][1]


def master_windows(master) -> list[dict]:
    """Every known (ticker, from, to-exclusive, security id) row in the master,
    from each entry's ticker_history or else its ticker and active window."""
    out = []
    for e in master.instruments if master is not None else []:
        if e.get("merged_into"):
            continue
        rows = e.get("ticker_history") or (
            [{"ticker": e["identifiers"]["ticker"], "from": e.get("active_from"),
              "to": e.get("active_to")}] if e["identifiers"].get("ticker") else [])
        for r in rows:
            out.append({"ticker": str(r["ticker"]), "from": r.get("from"),
                        "to_x": _next(r["to"]) if r.get("to") else None, "sid": e["id"]})
    return out


def _master_at(windows: list[dict], ticker: str, day: str) -> Optional[dict]:
    hits = [w for w in windows if w["ticker"] == ticker
            and (w["from"] is None or w["from"] <= day)
            and (w["to_x"] is None or day < w["to_x"])]
    return hits[0] if len(hits) == 1 else None


def build(snapshots, assignments: Assignments, master=None) -> dict[str, list[dict]]:
    """{composite FIGI: [ticker rows]} over the snapshots, oldest first. Streams:
    `snapshots` is any iterable of (day, rows), and only one day is held."""
    windows = master_windows(master)
    hist: dict[str, list[dict]] = {}
    it = iter(snapshots)
    first = next(it, None)
    if first is None:
        return hist
    d0, rows0 = first
    for r in rows0:
        f = assignments.figi_of(r["symbol"], d0)
        if not f or f in hist:
            continue
        w = _master_at(windows, r["symbol"], d0)
        if w:
            known = sorted((x for x in windows if x["sid"] == w["sid"]),
                           key=lambda x: x["from"] or SENTINEL)
            hist[f] = [{"ticker": x["ticker"], "effective_from": x["from"] or SENTINEL,
                        "effective_to": x["to_x"], "from_known": x["from"] is not None}
                       for x in known if x["from"] is None or x["from"] <= d0]
        else:
            hist[f] = [{"ticker": r["symbol"], "effective_from": SENTINEL,
                        "effective_to": None, "from_known": False}]
    prev = d0
    for day, rows in it:
        missed = _missed_morning(prev, day)
        holder = {}
        for r in rows:
            f = assignments.figi_of(r["symbol"], day)
            if f:
                holder[r["symbol"]] = f
        # close every open row whose ticker no longer belongs to its FIGI
        closed = set()
        for f, rs in hist.items():
            for row in rs:
                if row["effective_to"] is None and holder.get(row["ticker"]) != f:
                    w = _master_at(windows, row["ticker"], prev)
                    row["effective_to"] = (w["to_x"] if w and w["to_x"]
                                           and prev < w["to_x"] <= day else day)
                    closed.add(row["ticker"])
        # open a row for every holding not already open
        for s, f in holder.items():
            new_listing = f not in hist and s not in closed
            rs = hist.setdefault(f, [])
            if any(x["ticker"] == s and x["effective_to"] is None for x in rs):
                continue
            w = _master_at(windows, s, day)
            # The start is the 16 Oct ruling's (aud-3b Needs-you 9): a new listing
            # opens the day after the previous snapshot; a reused ticker's new
            # holder on the snapshot day. from_known is false only after a
            # missed morning (ruled 15 Oct), where the start is a bound.
            if w and w["from"] and prev < w["from"] <= day:
                start, known = w["from"], True
            elif new_listing:
                start, known = _next(prev), not missed
            else:
                start, known = day, True
            rs.append({"ticker": s, "effective_from": start, "effective_to": None,
                       "from_known": known})
        prev = day
    return hist


def _missed_morning(prev: str, day: str) -> bool:
    """True when a trading session falls strictly between two snapshot days:
    more than one session from `prev` (exclusive) to `day` (inclusive)."""
    from . import derived                                       # noqa: PLC0415
    return derived.sessions_between(prev, day)[0] > 1
