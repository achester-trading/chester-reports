"""
Nightly consensus and revision log. (Part 29.2)

Forward EPS, forward P/E and the trailing pair for the tracked universe and the
sector ETFs, read nightly from yfinance. Logging only: the decomposition that reads
it is the point, and it stays behind `insufficient_history` until a quarter exists.

    python -m altdata.loggers.consensus probe
    python -m altdata.loggers.consensus pull
    python -m altdata.loggers.consensus derived

-----------------------------------------------------------------------------
WHAT THE SOURCE ACTUALLY SERVES, WHICH IS NOT WHAT WAS ASKED FOR
-----------------------------------------------------------------------------

The order asks for forward EPS and forward P/E "per name for the tracked universe +
SPY/QQQ/IWM + the sector ETFs". The probe says yfinance serves those fields for
INDIVIDUAL STOCKS and not for ETFs:

    NVDA   forwardEps 15.68   forwardPE 14.17   trailingPE 28.10
    SPY    forwardEps None    forwardPE None    trailingPE 24.61
    XLK    forwardEps None    forwardPE None    trailingPE 33.56

An ETF has no consensus estimate because no analyst covers a wrapper; a bottom-up
forward earnings yield for SPY has to be built from its holdings, which is a
different job with a different source. So the ETFs are logged for what they DO carry
-- the trailing multiple -- and the absent fields are simply not written rather than
stored as nulls that would later read as zeroes.

That is worth stating rather than quietly shipping: the index-level forward multiple
this log was partly wanted for is NOT in it, and getting it needs a holdings-weighted
build or a vendor that sells the aggregate.

-----------------------------------------------------------------------------
THE DECOMPOSITION, AND WHY IT WAITS
-----------------------------------------------------------------------------

Price = earnings x multiple, so a price move decomposes into an earnings-revision
component and a re-rating component. That identity is exact in logs:

    ln(P1/P0) = ln(E1/E0) + ln(M1/M0)

The decomposition is the reason to log this at all -- it separates "the market paid
more" from "the estimate went up", which no price series can do alone. It reads
`insufficient_history` until 60 sessions exist, because a decomposition over a
fortnight is dominated by the noise in a single revision.
"""

from __future__ import annotations

import json
import logging
import math
import time
from typing import Any, Optional

from .. import observations, session
from . import LoggerSpec, guarded_days, register

log = logging.getLogger(__name__)

FORWARD_EPS = "yf.forward_eps"
FORWARD_PE = "yf.forward_pe"
TRAILING_EPS = "yf.trailing_eps"
TRAILING_PE = "yf.trailing_pe"
ANALYSTS = "yf.analyst_count"
TARGET_MEAN = "yf.target_mean_price"

FIELDS = {
    FORWARD_EPS: "forwardEps",
    FORWARD_PE: "forwardPE",
    TRAILING_EPS: "trailingEps",
    TRAILING_PE: "trailingPE",
    ANALYSTS: "numberOfAnalystOpinions",
    TARGET_MEAN: "targetMeanPrice",
}

PACING_SECONDS = 0.6
MIN_HISTORY = 60          # a quarter, as the order asks
TIMEOUT_NOTE = "yfinance has no timeout knob on .info; a hung name is skipped"


def universe() -> list[str]:
    """The tracked options universe plus the eleven sector ETFs.

    SPY, QQQ and IWM are already in the options universe, so the order's "+
    SPY/QQQ/IWM" is satisfied by it rather than by adding them twice.
    """
    from .. import config
    from ..sources import yfinance_source as yf_src
    sectors = [k.replace("mkt_", "").upper() for k in yf_src.SECTOR_KEYS]
    seen, out = set(), []
    for sym in list(config.options_universe()) + sectors:
        if sym not in seen:
            seen.add(sym)
            out.append(sym)
    return out


def read_one(symbol: str) -> dict:
    """The declared fields for one name. Absent fields are ABSENT, not zero."""
    import yfinance as yf
    info = yf.Ticker(symbol).info or {}
    out: dict[str, float] = {}
    for key, field in FIELDS.items():
        v = info.get(field)
        if v is None:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if f != f or not math.isfinite(f):        # NaN or inf is missing
            continue
        out[key] = f
    return out


def probe() -> dict:
    """Which fields this source actually serves, for a stock and for an ETF."""
    out: dict[str, Any] = {"checked_at": session.utc_iso(), "samples": {}}
    for sym in ("NVDA", "SPY", "XLK"):
        try:
            out["samples"][sym] = {k.split(".")[-1]: v
                                   for k, v in read_one(sym).items()}
        except Exception as exc:                              # noqa: BLE001
            out["samples"][sym] = {"error": f"{type(exc).__name__}: {exc}"}
    stock = out["samples"].get("NVDA") or {}
    etf = out["samples"].get("SPY") or {}
    out["ok"] = bool(stock)
    out["forward_for_etfs"] = "forward_eps" in etf
    out["note"] = ("forward estimates are served for stocks and not for ETFs; the "
                   "ETFs are logged for their trailing multiple only")
    return out


def pull(run_id: Optional[str] = None,
         store: Optional[observations.ObservationStore] = None,
         symbols: Optional[list[str]] = None) -> dict:
    own = store is None
    db = store or observations.ObservationStore()
    try:
        # THE OBSERVED DATE IS THE SESSION, not the wall clock: this runs at 06:45
        # and reports on the close it follows, so dating it "today" would put a
        # Monday-morning read on Monday when it describes Friday.
        day = session.last_trading_session().isoformat()
        now = session.utc_iso(timespec="microseconds")
        rows, got, failed = [], 0, []
        for sym in (symbols or universe()):
            try:
                vals = read_one(sym)
            except Exception as exc:                          # noqa: BLE001
                failed.append((sym, f"{type(exc).__name__}: {exc}"))
                continue
            if not vals:
                failed.append((sym, "no declared field served"))
                continue
            got += 1
            for key, value in vals.items():
                rows.append({"registry_key": key, "instrument": sym,
                             "observed_at": day, "available_at": now,
                             "value": value, "source": "yfinance",
                             "run_id": run_id,
                             "availability_kind": "ingest_instant"})
            time.sleep(PACING_SECONDS)
        written = db.write_many(observations.drop_unchanged(db, rows))
        for sym, why in failed:
            log.warning("consensus: %s -- %s", sym, why)
        log.info("consensus: %d names, %d rows written for session %s",
                 got, written, day)
        return {"session": day, "names": got, "rows": len(rows),
                "written": written, "failed": failed}
    except Exception as exc:                                  # noqa: BLE001
        log.exception("consensus pull raised")
        return {"error": f"{type(exc).__name__}: {exc}", "written": 0}
    finally:
        if own:
            db.close()


def derived(as_of: Optional[str] = None,
            store: Optional[observations.ObservationStore] = None) -> dict:
    """The revision decomposition: how much of a price move was estimates.

    ln(P1/P0) = ln(E1/E0) + ln(M1/M0), exactly. Reported per name over the longest
    span both legs support.
    """
    own = store is None
    db = store or observations.ObservationStore()
    try:
        def compute() -> dict:
            from ..sources import yfinance_source as yf_src
            out: dict[str, Any] = {"state": "ok", "names": {}}
            for sym in universe():
                eps = [(str(r["observed_at"])[:10], r["value_num"])
                       for r in db.as_of(FORWARD_EPS, as_of=as_of, instrument=sym)
                       if r["value_num"]]
                key = f"yfinance.mkt_{sym.lower()}"
                px = [(str(r["observed_at"])[:10], r["value_num"])
                      for r in db.as_of(key, as_of=as_of) if r["value_num"]]
                if len(eps) < 2 or len(px) < 2:
                    out["names"][sym] = {
                        "state": "absent",
                        "reason": (f"forward EPS points {len(eps)}, price points "
                                   f"{len(px)} -- a decomposition needs two of "
                                   f"each, and ETFs carry no forward EPS at all")}
                    continue
                d0, e0 = eps[0]
                d1, e1 = eps[-1]
                pxd = dict(px)
                p0 = pxd.get(d0)
                p1 = pxd.get(d1)
                if not p0 or not p1 or e0 <= 0 or e1 <= 0:
                    out["names"][sym] = {"state": "absent",
                                         "reason": "no price on both EPS dates"}
                    continue
                total = math.log(p1 / p0)
                earnings = math.log(e1 / e0)
                out["names"][sym] = {
                    "state": "ok", "from": d0, "to": d1,
                    "price_log_return": round(total, 6),
                    "earnings_component": round(earnings, 6),
                    "rerating_component": round(total - earnings, 6),
                    "share_from_earnings": (round(earnings / total, 4)
                                            if abs(total) > 1e-9 else None)}
            return out

        return guarded_days(FORWARD_EPS, MIN_HISTORY, compute, store=db)
    finally:
        if own:
            db.close()


def keys() -> list[str]:
    return list(FIELDS)


SPEC = register(LoggerSpec(
    name="consensus",
    description="Forward and trailing EPS/PE per name, nightly, for the tracked "
                "universe and the sector ETFs. ETFs carry no forward estimate.",
    keys=keys,
    run=pull,
    requires_key=None,
    min_history=MIN_HISTORY,
    notes="Part 29.2. The decomposition reads insufficient_history until 60 "
          "sessions exist.",
))


def _main(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Consensus/revision logger.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe")
    sub.add_parser("pull")
    sub.add_parser("derived")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    fn = {"probe": probe, "pull": pull, "derived": derived}[a.cmd]
    print(json.dumps(fn(), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
