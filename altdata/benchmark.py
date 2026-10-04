"""
Book Z -- the benchmark ledgers (EL-3, §3.3 of the Enterprise Layer order).

    python -m altdata.benchmark mark              # mark every unmarked session
    python -m altdata.benchmark mark --dry-run
    python -m altdata.benchmark show              # the latest marks and the line

Three static reference portfolios, marked from the observation store and stored
as `paper.benchmark` rows keyed by (session, ledger) -- observed_at the session,
instrument the ledger:

    cash         daily accrual at the 3-month T-bill (FRED DTB3, fred.tbill_3m).
                 The NO TRADE book.
    spy          SPY bought at the start date's close and held.
    sixty_forty  60% SPY / 40% AGG, rebalanced at the close of the first session
                 of each month.

Each ledger starts at 100.0 at the START DATE's close: the register's first
packet date, or 1 Sep 2026 if that is earlier. They are the denominator for every
later claim that a book added value -- "vs cash / SPY / 60-40".

-----------------------------------------------------------------------------
POINT-IN-TIME, AND NEVER RECOMPUTED
-----------------------------------------------------------------------------

A mark is written ONCE per (session, ledger) and never rewritten: the marker
skips any session a ledger already holds, so a later vintage of a price can
never restate a benchmark. Each mark is carried forward from the ledger's
previous stored row -- its units and cash -- plus that session's closes. No later
close ever enters an earlier mark.

THE CATCH-UP IS LABELLED. The pass that first runs this marks every session from
the start date to its own. Those rows use the closes and the T-bill rate
observed ON OR BEFORE each session, read now, and they say so:
`availability_kind = reconstructed`, available_at = the instant they were
computed (never backdated). DTB3 reached this store on 26 Sep 2026, stamped with
its pull instant, so a strictly as-of mark could not exist for 1-25 Sep at all.
From then on the 16:45 close pass marks its own session, `ingest_instant`.

DIVIDENDS ARE CASH, NOT REINVESTED. The store's closes are dividend-unadjusted
(altdata/sources/yfinance_source.py), so a dividend on its ex-date is added to
the ledger's cash from the `_dividend` series. The spy ledger holds that cash;
the 60/40 sweeps it into the monthly rebalance. The cash ledger's T-bill yield
is a discount-basis rate applied as a simple accrual: rate x calendar days / 360.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Any, Optional

from . import observations, session

log = logging.getLogger(__name__)

KEY = "paper.benchmark"
LEDGERS = ("cash", "spy", "sixty_forty")
START_CAP = dt.date(2026, 9, 1)
BASE = 100.0
SPY, AGG, TBILL = "yfinance.mkt_spy", "yfinance.mkt_agg", "fred.tbill_3m"
WEIGHTS = {"spy": 0.60, "agg": 0.40}
METHOD = "book-z-v1"
LABEL = {"cash": "cash", "spy": "SPY", "sixty_forty": "60-40"}


def start_date(register_db: Optional[str] = None) -> dt.date:
    """The register's first packet date, or 1 Sep 2026 if that is earlier."""
    try:
        from register.store import Register  # noqa: PLC0415
        with Register(register_db) as reg:
            row = reg.conn.execute(
                "SELECT min(created_at) FROM decision_packets").fetchone()
        if row and row[0]:
            return min(START_CAP, dt.date.fromisoformat(str(row[0])[:10]))
    except Exception as exc:                                  # noqa: BLE001
        log.warning("register unreadable for Book Z's start (%s); using %s",
                    type(exc).__name__, START_CAP)
    return START_CAP


def _series(db: observations.ObservationStore, key: str) -> dict[str, float]:
    """day -> value, the newest vintage of each observed day."""
    out: dict[str, float] = {}
    for r in db.as_of(key):
        if r["value_num"] is not None:
            out[str(r["observed_at"])[:10]] = float(r["value_num"])
    return out


def _on_or_before(series: dict[str, float], day: str) -> Optional[tuple[str, float]]:
    days = [d for d in series if d <= day]
    if not days:
        return None
    d = max(days)
    return d, series[d]


def _sessions(first: dt.date, last: dt.date) -> list[str]:
    out, d = [], first
    while d <= last:
        if session.is_trading_session(d.isoformat()):
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def _marked(db: observations.ObservationStore) -> dict[str, dict[str, dict]]:
    """ledger -> session -> the stored mark (payload)."""
    # PER LEDGER: as_of() matches `instrument IS ?` exactly, and a ledger is
    # the row's instrument. Reading with no instrument would find nothing, and
    # the marker would then re-mark every session on every run -- the one thing
    # a point-in-time ledger must never do.
    out: dict[str, dict[str, dict]] = {ld: {} for ld in LEDGERS}
    for ld in LEDGERS:
        for r in db.as_of(KEY, instrument=ld):
            if r["value_text"]:
                try:
                    out[ld][str(r["observed_at"])[:10]] = json.loads(r["value_text"])
                except ValueError:
                    continue
    return out


def _first_of_month(day: str, prev: Optional[str]) -> bool:
    return prev is None or prev[:7] != day[:7]


def compute_marks(db: observations.ObservationStore, through: str,
                  start: dt.date, live_session: Optional[str] = None) -> list[dict]:
    """The rows for every session a ledger does not yet hold, start..through."""
    done = _marked(db)
    spy, agg, tb = _series(db, SPY), _series(db, AGG), _series(db, TBILL)
    spy_dv = _series(db, SPY + "_dividend")
    agg_dv = _series(db, AGG + "_dividend")
    now = session.utc_iso(timespec="microseconds")
    days = _sessions(start, dt.date.fromisoformat(through))
    rows: list[dict] = []

    def emit(ledger: str, day: str, value: float, payload: dict) -> None:
        payload.update({"ledger": ledger, "session": day, "value": round(value, 6),
                        "start": start.isoformat(), "method": METHOD})
        kind = "ingest_instant" if day == live_session else "reconstructed"
        # THE ROW'S VALUE IS THE MARK'S JSON -- units, cash, the closes it was
        # marked at and the ledger value itself -- the way the market-state
        # object is stored. The store keeps one value per row, number or text,
        # and a mark without its units could not be carried forward.
        rows.append({"registry_key": KEY, "instrument": ledger, "observed_at": day,
                     "available_at": now,
                     "value": json.dumps(payload, sort_keys=True),
                     "value_text": json.dumps(payload, sort_keys=True),
                     "source": "book_z", "availability_kind": kind})

    for ledger in LEDGERS:
        prev_day, prev = None, None
        # Resume from the ledger's own last stored mark, if any.
        held = done[ledger]
        for day in days:
            if day in held:
                prev_day, prev = day, held[day]
                continue
            p_spy = spy.get(day)
            if ledger == "cash":
                if prev is None:
                    emit(ledger, day, BASE, {"cash": BASE, "accrued_at": None,
                                             "note": "start"})
                    prev_day, prev = day, rows[-1] and json.loads(rows[-1]["value_text"])
                    continue
                rate = _on_or_before(tb, prev_day)
                if rate is None:
                    log.warning("Book Z cash: no DTB3 on or before %s; %s unmarked",
                                prev_day, day)
                    continue
                days_n = (dt.date.fromisoformat(day)
                          - dt.date.fromisoformat(prev_day)).days
                value = float(prev["value"]) * (1.0 + rate[1] / 100.0 * days_n / 360.0)
                emit(ledger, day, value, {"cash": value, "rate_pct": rate[1],
                                          "rate_observed": rate[0],
                                          "days": days_n, "from": prev_day})
            elif ledger == "spy":
                if p_spy is None:
                    log.warning("Book Z spy: no SPY close for %s; unmarked", day)
                    continue
                if prev is None:
                    units, cash = BASE / p_spy, 0.0
                else:
                    units, cash = float(prev["units_spy"]), float(prev["cash"])
                    cash += units * spy_dv.get(day, 0.0)
                value = units * p_spy + cash
                emit(ledger, day, value, {"units_spy": units, "cash": cash,
                                          "close_spy": p_spy,
                                          "dividend": spy_dv.get(day)})
            else:
                p_agg = agg.get(day)
                if p_spy is None or p_agg is None:
                    log.warning("Book Z 60/40: no %s close for %s; unmarked",
                                "SPY" if p_spy is None else "AGG", day)
                    continue
                if prev is None:
                    total, u_s, u_a, cash = BASE, None, None, 0.0
                else:
                    u_s, u_a = float(prev["units_spy"]), float(prev["units_agg"])
                    cash = (float(prev["cash"]) + u_s * spy_dv.get(day, 0.0)
                            + u_a * agg_dv.get(day, 0.0))
                    total = u_s * p_spy + u_a * p_agg + cash
                rebalance = prev is None or _first_of_month(day, prev_day)
                if rebalance:
                    u_s = WEIGHTS["spy"] * total / p_spy
                    u_a = WEIGHTS["agg"] * total / p_agg
                    cash = 0.0
                value = u_s * p_spy + u_a * p_agg + cash
                emit(ledger, day, value, {"units_spy": u_s, "units_agg": u_a,
                                          "cash": cash, "close_spy": p_spy,
                                          "close_agg": p_agg,
                                          "rebalanced": rebalance})
            prev_day, prev = day, json.loads(rows[-1]["value_text"])
    return rows


def mark(through: Optional[str] = None, dry_run: bool = False,
         store: Optional[observations.ObservationStore] = None,
         register_db: Optional[str] = None) -> dict:
    """Mark every unmarked session up to `through` (default: the last session)."""
    day = through or session.last_trading_session().isoformat()
    start = start_date(register_db)
    own = store is None
    db = store or observations.ObservationStore()
    try:
        rows = compute_marks(db, day, start, live_session=day)
        n = 0 if dry_run else db.write_many(rows)
        by = {ld: sum(1 for r in rows if r["instrument"] == ld) for ld in LEDGERS}
        return {"through": day, "start": start.isoformat(), "computed": len(rows),
                "written": n, "by_ledger": by, "dry_run": dry_run}
    finally:
        if own:
            db.close()


def latest(as_of: Optional[str] = None,
           store: Optional[observations.ObservationStore] = None) -> dict:
    """ledger -> its newest stored mark knowable at `as_of`."""
    own = store is None
    db = store or observations.ObservationStore()
    try:
        out: dict[str, dict] = {}
        for ld in LEDGERS:
            rows = [r for r in db.as_of(KEY, as_of=as_of, instrument=ld)
                    if r["value_text"]]
            if rows:
                out[ld] = json.loads(rows[-1]["value_text"])
        return out
    finally:
        if own:
            db.close()


def line(as_of: Optional[str] = None,
         store: Optional[observations.ObservationStore] = None) -> dict:
    """The "vs cash / SPY / 60-40" line: each ledger's return since the start."""
    marks = latest(as_of, store)
    if not marks:
        return {"text": None, "absent_reason": "no Book Z mark is stored -- "
                "`python -m altdata.benchmark mark` has not run"}
    parts, sessions = [], set()
    for ld in LEDGERS:
        m = marks.get(ld)
        if not m:
            parts.append(f"{LABEL[ld]} not marked")
            continue
        parts.append(f"{LABEL[ld]} {100.0 * (m['value'] / BASE - 1.0):+.2f}%")
        sessions.add(m["session"])
    start = next(iter(marks.values()))["start"]
    through = max(sessions) if sessions else None
    return {"text": (f"vs {' / '.join(parts)} since {start}"
                     + (f" (marked to {through})" if through else "")),
            "start": start, "through": through,
            "returns_pct": {ld: (round(100.0 * (marks[ld]["value"] / BASE - 1.0), 4)
                                 if ld in marks else None) for ld in LEDGERS}}


def _mark_on_or_before(db, ledger: str, day: str, as_of: Optional[str]) -> Optional[dict]:
    rows = [json.loads(r["value_text"]) for r in db.as_of(KEY, as_of=as_of,
                                                          instrument=ledger)
            if r["value_text"] and str(r["observed_at"])[:10] <= day]
    return rows[-1] if rows else None


def book_line(as_of: Optional[str] = None,
              store: Optional[observations.ObservationStore] = None) -> dict:
    """THE BOOK AGAINST BOOK Z, as labelled absolutes and then the excess.
    (T2 ruling 1, 3 Oct 2026.)

    The book's own return is Portfolio Truth's NAV, from its first stored value
    on or after Book Z's start to the newest knowable at `as_of`. Each benchmark's
    return is measured over THAT SAME WINDOW -- its mark on the book's first NAV
    date to its newest mark -- so an excess never compares two windows. The
    excess is book minus benchmark, in percentage points. Where the book cannot be
    measured it says so and no excess is printed: an excess against nothing is a
    benchmark's return in disguise.
    """
    own = store is None
    db = store or observations.ObservationStore()
    try:
        marks = latest(as_of, db)
        if not marks:
            return {"text": None, "absent_reason": "no Book Z mark is stored"}
        start = next(iter(marks.values()))["start"]
        navs = [r for r in db.as_of("portfolio.nav", as_of=as_of)
                if r.get("value_num") and str(r["observed_at"])[:10] >= start]
        out: dict = {"start": start, "benchmarks_pct": {}, "excess_pts": {}}
        if not navs:
            out["book_pct"] = None
            out["book_absent_reason"] = "no Portfolio Truth NAV stored since " + start
            first_day = start
        else:
            first_day = str(navs[0]["observed_at"])[:10]
            out["book_pct"] = round(100.0 * (navs[-1]["value_num"]
                                             / navs[0]["value_num"] - 1.0), 2)
            out["book_through"] = str(navs[-1]["observed_at"])[:10]
        out["window_start"] = first_day
        through = None
        for ld in LEDGERS:
            m0 = _mark_on_or_before(db, ld, first_day, as_of)
            m1 = marks.get(ld)
            if not m0 or not m1:
                out["benchmarks_pct"][ld] = None
                continue
            r = round(100.0 * (m1["value"] / m0["value"] - 1.0), 2)
            out["benchmarks_pct"][ld] = r
            through = max(through or m1["session"], m1["session"])
            if out["book_pct"] is not None:
                out["excess_pts"][ld] = round(out["book_pct"] - r, 2)
        out["through"] = through

        def pct(v):
            return "not marked" if v is None else f"{v:+.2f}%"
        bench = ", ".join(f"{LABEL[ld]} {pct(out['benchmarks_pct'][ld])}"
                          for ld in LEDGERS)
        if out["book_pct"] is None:
            out["text"] = (f"the book: not tracked ({out['book_absent_reason']}); "
                           f"since {first_day}: {bench}")
        else:
            exc = " / ".join(f"{out['excess_pts'][ld]:+.2f}" if ld in out["excess_pts"]
                             else "n/a" for ld in LEDGERS)
            out["text"] = (f"since {first_day}: the book {pct(out['book_pct'])} "
                           f"(Portfolio Truth NAV); {bench}; excess vs cash / SPY / "
                           f"60-40: {exc} pts"
                           + (f" (marked to {through})" if through else ""))
        return out
    finally:
        if own:
            db.close()


def _main(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Book Z: the benchmark ledgers.")
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mark")
    m.add_argument("--through", default=None, metavar="YYYY-MM-DD")
    m.add_argument("--dry-run", action="store_true")
    sub.add_parser("show")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if a.cmd == "mark":
        r = mark(through=a.through, dry_run=a.dry_run)
        print(f"Book Z through {r['through']} (start {r['start']}): "
              f"{r['computed']} mark(s) computed, {r['written']} written"
              + ("  (dry run)" if r["dry_run"] else ""))
        for ld, n in r["by_ledger"].items():
            print(f"  {ld:12} {n}")
    marks = latest()
    for ld in LEDGERS:
        mk = marks.get(ld)
        print(f"  {ld:12} " + (f"{mk['value']:.4f} at {mk['session']}" if mk
                               else "not marked"))
    ln = line()
    print("  " + (ln["text"] or f"line absent: {ln['absent_reason']}"))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
