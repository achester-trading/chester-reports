"""
The VX futures curve from Cboe's public settlement files. (Paste D piece 3)

    python -m altdata.loggers.vxcurve probe
    python -m altdata.loggers.vxcurve pull
    python -m altdata.loggers.vxcurve backfill --months 24
    python -m altdata.loggers.vxcurve curve --session 2026-09-22

-----------------------------------------------------------------------------
WHAT ANSWERS, AND WHAT DOES NOT
-----------------------------------------------------------------------------

Four Cboe endpoints were probed. One answers without a key:

    cdn.cboe.com/data/us/futures/market_statistics/historical_data/VX/VX_<expiry>.csv
        HTTP 200. The WHOLE daily history of one contract: trade date, open,
        high, low, close, SETTLE, change, volume, EFP, open interest.

    .../market_statistics/settlement/<date>.csv        HTTP 403
    .../market_statistics/historical_data/  (listing)  HTTP 403
    api/global/delayed_quotes/quotes/VX.json           HTTP 403

So there is no directory listing and no all-products daily file: the contract's
expiry has to be COMPUTED and the URL constructed. That is the one piece of real
knowledge this module carries, and it is checkable -- `VX_2026-10-21.csv` exists
because 21 October 2026 is the Wednesday thirty days before the third Friday of
November 2026, and the fetch that proved the endpoint also proved the arithmetic.

-----------------------------------------------------------------------------
MONTHLY CONTRACTS ONLY, DECLARED
-----------------------------------------------------------------------------

Cboe lists weekly VX futures as well as monthly ones. VX1/VX2/VX3 in the term
structure literature and in 30.8's state machine mean the first three MONTHLY
contracts, and mixing a weekly into the front slot would make the slope jump
every Wednesday for a reason that has nothing to do with the curve. Only monthly
expiries are fetched, and the curve rows record which expiry filled each slot so
the choice is visible rather than implied.

-----------------------------------------------------------------------------
WHAT IS COMPUTED, AND WHY A RATIO AS WELL AS A SLOPE
-----------------------------------------------------------------------------

    cfe.vx_settle          per contract, instrument = the expiry date
    cfe.vx1 / vx2 / vx3    the front three monthly settles for a session
    calc.vx_front_slope    VX2 - VX1, in volatility points
    calc.vx1_vix_basis     VX1 - VIX, in volatility points
    calc.vx_front_ratio    VX2 / VX1

The ratio exists because the vol dial's term-structure leg is banded on a RATIO,
and the challenger it is replacing -- calc.vix3m_over_vix -- is one. A champion
measured in points and a challenger measured as a ratio cannot be printed side by
side and compared; the whole point of the dual run is that they can.

The basis is the number the proxy could never see. VIX3M/VIX is two implied
volatilities of the same index: it moves with the curve but it cannot show a
futures-to-index dislocation, because both its legs ARE the index. VX1 - VIX is
exactly that dislocation, and it is the reason the proxy was always labelled
`proxy_for: vx_futures_curve` rather than treated as the thing itself.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import logging
from typing import Any, Optional

from .. import observations, session
from ..sources._base import http_get_json                      # noqa: F401
from . import LoggerSpec, register

log = logging.getLogger(__name__)

BASE = ("https://cdn.cboe.com/data/us/futures/market_statistics/"
        "historical_data/VX/VX_{expiry}.csv")

SETTLE_KEY = "cfe.vx_settle"
SLOT_KEYS = ("cfe.vx1", "cfe.vx2", "cfe.vx3")
SLOPE_KEY = "calc.vx_front_slope"
BASIS_KEY = "calc.vx1_vix_basis"
RATIO_KEY = "calc.vx_front_ratio"
PROBE_KEY = "cfe.vx_probe"
VIX_KEY = "yfinance.mkt_vix"

SOURCE = "cboe"
TIMEOUT = 25
# How many monthly contracts the routine pull refreshes. Three slots need three
# unexpired contracts; four is the margin for an expiry week, when the front
# contract settles and the file stops updating.
PULL_CONTRACTS = 5
BACKFILL_MONTHS = 24

# THE PROBED ENDPOINTS, kept so the three refusals are a stored fact rather than
# something to rediscover. Each is (label, url template, what it returned).
PROBED = (
    ("contract_history", BASE, "HTTP 200 -- the one that answers"),
    ("daily_settlement",
     "https://cdn.cboe.com/data/us/futures/market_statistics/settlement/"
     "{date}.csv", "HTTP 403"),
    ("directory_listing",
     "https://cdn.cboe.com/data/us/futures/market_statistics/historical_data/VX/",
     "HTTP 403"),
    ("delayed_quotes",
     "https://cdn.cboe.com/api/global/delayed_quotes/quotes/VX.json",
     "HTTP 403"),
)


# ---------------------------------------------------------------------------
# Expiry arithmetic -- the only real knowledge here
# ---------------------------------------------------------------------------
def third_friday(year: int, month: int) -> dt.date:
    d = dt.date(year, month, 1)
    fridays = [d.replace(day=day) for day in range(1, 32)
               if day <= (dt.date(year + (month == 12), (month % 12) + 1, 1)
                          - dt.timedelta(days=1)).day
               and d.replace(day=day).weekday() == 4]
    return fridays[2]


def monthly_expiry(year: int, month: int) -> dt.date:
    """The VX monthly settlement date for the contract named <month year>.

    Thirty days before the third Friday of the FOLLOWING month, which lands on a
    Wednesday whenever that Friday is a Friday.

    THE HOLIDAY ADJUSTMENT IS REAL AND IT FIRED TWICE IN TWO YEARS. When the third
    Friday is an exchange holiday the SPX options it settles against expire on the
    Thursday, and the VIX settlement moves thirty days before THAT -- one day
    earlier. Two of twenty-four contracts 403'd on the first backfill for exactly
    this: April 2025's third Friday was Good Friday and June 2026's is Juneteenth.

    Where the holiday table covers the anchor month the adjustment is computed. It
    only covers 2026-2027, so outside that range the anchor is taken as given and
    fetch_contract() retries one day earlier -- see ADJUSTED_LOOKBACK_DAYS. Two
    mechanisms for one fact is not duplication here: one is knowledge (the table)
    and the other is a bounded search for when we have none.
    """
    nxt_y, nxt_m = (year + 1, 1) if month == 12 else (year, month + 1)
    anchor = third_friday(nxt_y, nxt_m)
    if session.calendar_covers(anchor) and not session.is_trading_session(anchor):
        anchor = session.previous_trading_session(anchor)
    return anchor - dt.timedelta(days=30)


def expiries_around(day: Optional[dt.date] = None, ahead: int = PULL_CONTRACTS,
                    behind: int = 0) -> list[dt.date]:
    """The monthly expiries from `behind` months back to `ahead` months forward."""
    d = day or session.last_completed_session()
    out: list[dt.date] = []
    for k in range(-behind, ahead + 1):
        y, m = d.year, d.month + k
        while m > 12:
            y, m = y + 1, m - 12
        while m < 1:
            y, m = y - 1, m + 12
        e = monthly_expiry(y, m)
        if e not in out:
            out.append(e)
    return sorted(out)


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------
def _get(url: str) -> bytes:
    import urllib.request
    req = urllib.request.Request(
        url, headers={"User-Agent": "chester-reports/1.0 (+market-state)"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


# HOW FAR BACK TO LOOK WHEN THE COMPUTED EXPIRY HAS NO FILE. One day, because the
# only documented shift is the third Friday becoming a Thursday, and a wider search
# would eventually find SOME file and silently label it with the wrong expiry --
# which would put a contract in the wrong curve slot. A bounded search that fails
# is better than an unbounded one that succeeds by accident.
ADJUSTED_LOOKBACK_DAYS = 1


def fetch_contract(expiry: dt.date) -> dict:
    """One contract's whole daily history. Never raises.

    On a miss it retries ADJUSTED_LOOKBACK_DAYS earlier and records that it did:
    `expiry_adjusted` is the date the file was actually found under, so a holiday
    shift shows up in the data rather than in a comment.
    """
    url = BASE.format(expiry=expiry.isoformat())
    out: dict[str, Any] = {"expiry": expiry.isoformat(), "url": url, "rows": []}
    try:
        raw = _get(url).decode("utf-8", "replace")
    except Exception as exc:                                   # noqa: BLE001
        first_error = f"{type(exc).__name__}: {str(exc)[:120]}"
        for back in range(1, ADJUSTED_LOOKBACK_DAYS + 1):
            alt = expiry - dt.timedelta(days=back)
            try:
                raw = _get(BASE.format(expiry=alt.isoformat())).decode(
                    "utf-8", "replace")
            except Exception:                                  # noqa: BLE001
                continue
            out["expiry"] = alt.isoformat()
            out["url"] = BASE.format(expiry=alt.isoformat())
            out["expiry_computed"] = expiry.isoformat()
            out["expiry_adjusted"] = alt.isoformat()
            out["adjust_reason"] = (
                "the computed expiry had no file; found one day earlier, which is "
                "the documented shift when the anchor Friday is a holiday")
            break
        else:
            out["error"] = first_error
            return out
    rdr = csv.DictReader(io.StringIO(raw))
    for row in rdr:
        day = (row.get("Trade Date") or "").strip()[:10]
        settle = (row.get("Settle") or "").strip()
        if not day or not settle:
            continue
        try:
            value = float(settle)
        except ValueError:
            continue
        # A SETTLE OF ZERO IS NOT A PRICE. The listing day of a contract that has
        # not traded carries zeros in several columns; storing one would put a
        # volatility of nothing into the front slot.
        if value <= 0:
            continue
        try:
            oi = int(float((row.get("Open Interest") or "0").strip() or 0))
            vol = int(float((row.get("Total Volume") or "0").strip() or 0))
        except ValueError:
            oi = vol = 0
        out["rows"].append({"date": day, "settle": value,
                            "open_interest": oi, "volume": vol})
    out["rows"].sort(key=lambda r: r["date"])
    out["first"] = out["rows"][0]["date"] if out["rows"] else None
    out["last"] = out["rows"][-1]["date"] if out["rows"] else None
    return out


def probe() -> dict:
    """Is the endpoint reachable, and does the expiry arithmetic hit a real file?"""
    e = expiries_around(ahead=2)[0]
    got = fetch_contract(e)
    out = {
        "checked_at": session.utc_iso(),
        "endpoints": [{"label": lab, "url": tmpl, "result": res}
                      for lab, tmpl, res in PROBED],
        "sample_expiry": e.isoformat(),
        "sample_rows": len(got.get("rows") or []),
        "sample_first": got.get("first"),
        "sample_last": got.get("last"),
        "state": "available" if got.get("rows") else "unreachable",
    }
    if got.get("error"):
        out["error"] = got["error"]
    if not got.get("rows"):
        out["fallback"] = ("CFE Enhanced over the Gateway, per the order -- a paid "
                           "entitlement on the IBKR account rather than a public "
                           "file")
    return out


# ---------------------------------------------------------------------------
# Writing: settles, then the curve those settles imply
# ---------------------------------------------------------------------------
def _write_settles(db: observations.ObservationStore, contracts: list[dict],
                   run_id: Optional[str]) -> int:
    stamp = session.utc_iso(timespec="microseconds")
    rows = []
    for c in contracts:
        for r in c["rows"]:
            rows.append({
                "registry_key": SETTLE_KEY, "instrument": c["expiry"],
                "observed_at": r["date"],
                # RECONSTRUCTED, not the write instant: a settlement is published
                # the evening of its trade date, and stamping today's clock onto a
                # 2024 settle would make every as-of-correct read before today
                # find nothing. Permitted here because a settlement price is never
                # restated -- the same rule tools/backfill_prices.py enforces.
                "available_at": _settle_available_at(r["date"]),
                "value": r["settle"], "source": SOURCE, "run_id": run_id,
                "availability_kind": "reconstructed"})
    return db.write_many(observations.drop_unchanged(db, rows))


# The settlement is published after the 16:15 ET close of the futures session.
# Declared once, so every reconstructed settle means the same thing.
SETTLE_AVAILABLE_AT_ET = dt.time(16, 45)


def _settle_available_at(day: str) -> str:
    d = dt.date.fromisoformat(day[:10])
    naive = dt.datetime.combine(d, SETTLE_AVAILABLE_AT_ET)
    tz = session._eastern_tz()                                 # noqa: SLF001
    aware = naive.replace(tzinfo=tz)
    return observations.canonical_instant(
        aware.astimezone(dt.timezone.utc).isoformat())


def curve_rows(contracts: list[dict], vix: dict[str, float],
               run_id: Optional[str] = None) -> list[dict]:
    """Per session date: the front three monthly settles and the three derived.

    THE SLOTS ARE ASSIGNED BY EXPIRY ORDER ON THAT DATE, not by which file the row
    came from. On the session a contract settles it is no longer the front month,
    and a slot filled by file order would keep an expiring contract in VX1 for one
    session too long -- the one session on which the front slot matters most.
    """
    by_day: dict[str, list[tuple[str, float]]] = {}
    for c in contracts:
        exp = c["expiry"]
        for r in c["rows"]:
            if r["date"] < exp:
                by_day.setdefault(r["date"], []).append((exp, r["settle"]))
    stamp = session.utc_iso(timespec="microseconds")
    out: list[dict] = []
    for day, legs in sorted(by_day.items()):
        legs.sort()
        avail = _settle_available_at(day)
        for i, key in enumerate(SLOT_KEYS):
            if i < len(legs):
                out.append({"registry_key": key, "instrument": None,
                            "observed_at": day, "available_at": avail,
                            "value": legs[i][1], "source": SOURCE,
                            "run_id": run_id,
                            "availability_kind": "reconstructed"})
        if len(legs) >= 2 and legs[0][1] > 0:
            out.append({"registry_key": SLOPE_KEY, "instrument": None,
                        "observed_at": day, "available_at": avail,
                        "value": round(legs[1][1] - legs[0][1], 6),
                        "source": "calc", "run_id": run_id,
                        "availability_kind": "reconstructed"})
            out.append({"registry_key": RATIO_KEY, "instrument": None,
                        "observed_at": day, "available_at": avail,
                        "value": round(legs[1][1] / legs[0][1], 6),
                        "source": "calc", "run_id": run_id,
                        "availability_kind": "reconstructed"})
        if legs and day in vix:
            out.append({"registry_key": BASIS_KEY, "instrument": None,
                        "observed_at": day, "available_at": avail,
                        "value": round(legs[0][1] - vix[day], 6),
                        "source": "calc", "run_id": run_id,
                        "availability_kind": "reconstructed"})
    return out


def _vix_map(db: observations.ObservationStore) -> dict[str, float]:
    out: dict[str, float] = {}
    for r in db.as_of(VIX_KEY):
        if r.get("value_num") is not None:
            out[str(r["observed_at"])[:10]] = float(r["value_num"])
    return out


def pull(run_id: Optional[str] = None,
         store: Optional[observations.ObservationStore] = None,
         months: int = PULL_CONTRACTS, behind: int = 1) -> dict:
    own = store is None
    db = store or observations.ObservationStore()
    try:
        exps = expiries_around(ahead=months, behind=behind)
        contracts, failed = [], []
        for e in exps:
            c = fetch_contract(e)
            if c.get("error") or not c["rows"]:
                failed.append((e.isoformat(), c.get("error") or "no rows"))
                continue
            contracts.append(c)
        if not contracts:
            # THE PROBE IS STORED ON FAILURE TOO. A route that stops answering is
            # the same kind of fact as one that never did, and the next person
            # should read it rather than re-probe.
            p = probe()
            db.write(PROBE_KEY, None,
                     session.last_completed_session().isoformat(),
                     session.utc_iso(timespec="microseconds"),
                     json.dumps(p, sort_keys=True), source=SOURCE,
                     availability_kind="ingest_instant")
            log.warning("vxcurve: no contract answered; probe stored")
            return {"contracts": 0, "written": 0, "failed": failed,
                    "probe_state": p.get("state")}
        written = _write_settles(db, contracts, run_id)
        rows = curve_rows(contracts, _vix_map(db), run_id)
        written += db.write_many(observations.drop_unchanged(db, rows))
        days = sorted({r["observed_at"] for r in rows})
        log.info("vxcurve: %d contracts, %d rows, %s..%s",
                 len(contracts), written, days[0] if days else "-",
                 days[-1] if days else "-")
        return {"contracts": len(contracts), "written": written,
                "failed": failed, "sessions": len(days),
                "first": days[0] if days else None,
                "last": days[-1] if days else None,
                "expiries": [c["expiry"] for c in contracts]}
    except Exception as exc:                                   # noqa: BLE001
        log.exception("vxcurve pull raised")
        return {"error": f"{type(exc).__name__}: {exc}", "written": 0}
    finally:
        if own:
            db.close()


def backfill(months: int = BACKFILL_MONTHS,
             store: Optional[observations.ObservationStore] = None) -> dict:
    """The modest backfill: `months` monthly contracts back from today.

    Each contract file carries its own whole history, so twenty-four contracts is
    roughly two years of a three-slot curve for twenty-four requests.
    """
    return pull(run_id=session.new_run_id("vxcurve-backfill"), store=store,
                months=PULL_CONTRACTS, behind=months)


def keys() -> list[str]:
    return [SETTLE_KEY, *SLOT_KEYS, SLOPE_KEY, BASIS_KEY, RATIO_KEY, PROBE_KEY]


SPEC = register(LoggerSpec(
    name="vx_curve",
    description="VX1/VX2/VX3 monthly settlements from Cboe's public per-contract "
                "files, with the front slope, the front ratio and the VX1-VIX "
                "basis the VIX3M proxy cannot see.",
    keys=keys,
    run=pull,
    requires_key=None,
    min_history=0,
    notes="Paste D piece 3. The champion for the vol dial's term-structure leg; "
          "calc.vix3m_over_vix runs beside it as challenger for a quarter.",
))


def _main(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="VX curve from Cboe settlements.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    pl = sub.add_parser("pull")
    pl.add_argument("--months", type=int, default=PULL_CONTRACTS)
    bf = sub.add_parser("backfill")
    bf.add_argument("--months", type=int, default=BACKFILL_MONTHS)
    cv = sub.add_parser("curve")
    cv.add_argument("--session", default=None)
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if a.cmd == "probe":
        print(json.dumps(probe(), indent=2, sort_keys=True))
        return 0
    if a.cmd == "pull":
        print(json.dumps(pull(months=a.months), indent=2, sort_keys=True))
        return 0
    if a.cmd == "backfill":
        print(json.dumps(backfill(months=a.months), indent=2, sort_keys=True))
        return 0
    db = observations.ObservationStore()
    try:
        day = a.session or session.last_completed_session().isoformat()
        out = {}
        for k in (*SLOT_KEYS, SLOPE_KEY, RATIO_KEY, BASIS_KEY):
            rows = [r for r in db.as_of(k) if str(r["observed_at"])[:10] == day]
            out[k] = rows[-1]["value_num"] if rows else None
        print(json.dumps({"session": day, **out}, indent=2, sort_keys=True))
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
