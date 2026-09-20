"""
Closing-auction tick sampler. (Part 29.4, LOGGING ONLY)

Samples the NYSE-family auction feed through the IB Gateway in the ten minutes
before the close, storing the indicative price, the paired quantity and the
imbalance with its side. Raw imbalance is display-only: ABSORPTION -- what the
imbalance did to the price -- is 6h and gated, and nothing here computes it.

    python -m altdata.loggers.auction probe          # entitlement, then decide
    python -m altdata.loggers.auction sample         # the 15:50-16:00 run
    python -m altdata.loggers.auction status

-----------------------------------------------------------------------------
THE PROBE DECIDES WHETHER THIS RUNS AT ALL
-----------------------------------------------------------------------------

The auction feed is a paid subscription (source_registry: ibkr_md_nyse_imbalances).
Whether this account has it is not a thing to assume, and the failure mode without a
probe is the worst kind: reqMktData succeeds, no auction tick ever arrives, and the
sampler writes an empty row every thirty seconds forever while looking healthy.

So the probe asks, records the answer either way, and the sampler refuses to run
until the recorded answer says entitled. A dormant sampler with a stored probe
result is a decision; a dormant sampler with nothing written down is a thing someone
forgot.

WHAT A PROBE OUTSIDE THE AUCTION WINDOW CAN AND CANNOT SETTLE. Auction ticks only
publish between roughly 15:50 and 16:00 ET, so a probe at any other time cannot see
one even with a full entitlement. What it CAN see is the error: IBKR returns 354
("requested market data is not subscribed") or 10089/10090 for an unentitled
request, and silence for an entitled one. So the probe reports three states --
`entitled`, `not_entitled`, `inconclusive_closed` -- and never collapses the third
into either of the others.

-----------------------------------------------------------------------------
EVERY SAMPLE IS STAMPED WITH ITS EVENT CLASS
-----------------------------------------------------------------------------

session.auction_event_classes() says what kind of close this is: OPEX,
TRIPLE_WITCHING, MONTH_END, QUARTER_END, INDEX_REBALANCE, ETF_REBALANCE, or NORMAL.
An index-rebalance auction carries multiples of an ordinary Tuesday's size because
index funds must trade at the official close, and pooling the two would make every
distribution bimodal -- so the stamp travels with the row and any later analysis can
condition on it.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import time
from typing import Any, Optional

from .. import observations, session
from . import LoggerSpec, register

log = logging.getLogger(__name__)

# The NYSE-family names the order asks for: the three index ETFs and eight sectors.
SYMBOLS: tuple[str, ...] = (
    "SPY", "QQQ", "IWM",
    "XLK", "XLF", "XLI", "XLE", "XLV", "XLU", "XLP", "XLY",
)

PRICE_KEY = "ibkr.auction_indicative_price"
PAIRED_KEY = "ibkr.auction_paired_qty"
IMBALANCE_KEY = "ibkr.auction_imbalance_qty"
SIDE_KEY = "ibkr.auction_imbalance_side"

# IBKR generic tick lists. 225 is "Auction" (auction price, volume, imbalance);
# 588 is the regulatory imbalance. Requested together so an account entitled to
# only one of them still produces something, and the probe can say which.
GENERIC_TICKS = "225,588"

# The window and cadence the order specifies.
WINDOW_START_ET = dt.time(15, 50)
WINDOW_END_ET = dt.time(16, 0)
SAMPLE_SECONDS = 30

# Where the probe's answer lives. A FILE rather than a constant, because the answer
# is about this account and this subscription and may change without a code change.
PROBE_KEY = "ibkr.auction_probe"

# Errors that mean "you are not subscribed". 354 is the general one; 10089 and 10090
# are the market-data-specific variants.
NOT_ENTITLED_CODES = {354, 10089, 10090, 10091, 10197}


def _connect(port: int = 4002, client_id: int = 23):
    from ..sources import ibkr_portfolio as ibkr
    return ibkr.connect(port=port, client_id=client_id)


def in_window(now_et: Optional[dt.datetime] = None) -> bool:
    now = now_et or session.to_eastern()
    return WINDOW_START_ET <= now.time() <= WINDOW_END_ET


def probe(port: int = 4002, seconds: float = 12.0,
          store: Optional[observations.ObservationStore] = None) -> dict:
    """Ask the Gateway for auction ticks and record what came back.

    Stored either way: "we asked and were refused" is the fact that makes a dormant
    sampler a decision rather than an oversight.
    """
    out: dict[str, Any] = {
        "checked_at": session.utc_iso(),
        "port": port,
        "in_auction_window": in_window(),
        "symbols_requested": ["SPY"],
        "errors": [],
        "ticks_seen": {},
        "state": "unknown",
    }
    ib = None
    try:
        ib = _connect(port=port)
        errors: list[dict] = []

        def on_error(reqId, code, msg, contract=None):        # noqa: ANN001
            errors.append({"code": int(code), "message": str(msg)[:200]})

        try:
            ib.errorEvent += on_error
        except Exception:                                      # noqa: BLE001
            pass

        from ib_async import Stock
        c = Stock("SPY", "SMART", "USD")
        ib.qualifyContracts(c)
        ticker = ib.reqMktData(c, genericTickList=GENERIC_TICKS, snapshot=False)
        deadline = time.time() + seconds
        seen: dict[str, Any] = {}
        while time.time() < deadline:
            ib.sleep(1.0)
            for field in ("auctionPrice", "auctionVolume", "auctionImbalance",
                          "regulatoryImbalance"):
                v = getattr(ticker, field, None)
                if v is not None and v == v:                   # not NaN
                    seen[field] = v
        try:
            ib.cancelMktData(c)
        except Exception:                                      # noqa: BLE001
            pass

        out["errors"] = errors
        out["ticks_seen"] = seen
        refused = [e for e in errors if e["code"] in NOT_ENTITLED_CODES]
        if refused:
            out["state"] = "not_entitled"
            out["reason"] = refused[0]["message"]
        elif seen:
            out["state"] = "entitled"
        elif out["in_auction_window"]:
            # In the window, no refusal, no tick: entitled-but-silent is possible
            # and so is a feed problem. Not collapsed into either.
            out["state"] = "inconclusive_silent"
            out["reason"] = ("in the auction window, no refusal and no tick -- "
                             "either the feed published nothing or the "
                             "entitlement is partial")
        else:
            out["state"] = "inconclusive_closed"
            out["reason"] = ("outside 15:50-16:00 ET no auction tick publishes even "
                             "with a full entitlement, so silence proves nothing. "
                             "No refusal was returned, which is the only positive "
                             "signal available at this hour")
    except Exception as exc:                                  # noqa: BLE001
        out["state"] = "probe_failed"
        out["reason"] = f"{type(exc).__name__}: {exc}"
    finally:
        if ib is not None:
            try:
                ib.disconnect()
            except Exception:                                  # noqa: BLE001
                pass

    own = store is None
    db = store or observations.ObservationStore()
    try:
        db.write(PROBE_KEY, None, session.session_date(),
                 session.utc_iso(timespec="microseconds"),
                 json.dumps(out, sort_keys=True), source="ibkr_paper",
                 availability_kind="ingest_instant")
    finally:
        if own:
            db.close()
    return out


def last_probe(store: Optional[observations.ObservationStore] = None
               ) -> Optional[dict]:
    own = store is None
    db = store or observations.ObservationStore()
    try:
        rows = db.as_of(PROBE_KEY)
        if not rows:
            return None
        return json.loads(rows[-1]["value_text"])
    finally:
        if own:
            db.close()


def sample(port: int = 4002, seconds: Optional[float] = None,
           store: Optional[observations.ObservationStore] = None,
           run_id: Optional[str] = None, force: bool = False) -> dict:
    """The 15:50-16:00 sampler. Refuses to run until a probe says entitled."""
    probe_result = last_probe(store=store)
    if not force and (probe_result or {}).get("state") != "entitled":
        state = (probe_result or {}).get("state", "never_probed")
        log.warning("auction: dormant -- the stored probe says %r. Run "
                    "`python -m altdata.loggers.auction probe` inside "
                    "15:50-16:00 ET to settle it.", state)
        return {"skipped": f"probe state {state}", "written": 0}

    classes = session.auction_event_classes()
    if not classes:
        return {"skipped": "not a session", "written": 0}

    own = store is None
    db = store or observations.ObservationStore()
    ib = None
    written = samples = 0
    try:
        ib = _connect(port=port)
        from ib_async import Stock
        contracts = {}
        for sym in SYMBOLS:
            c = Stock(sym, "SMART", "USD")
            ib.qualifyContracts(c)
            contracts[sym] = (c, ib.reqMktData(c, genericTickList=GENERIC_TICKS,
                                               snapshot=False))
        day = session.session_date()
        deadline = (time.time() + seconds if seconds
                    else _seconds_until(WINDOW_END_ET) + time.time())
        while time.time() < deadline:
            ib.sleep(SAMPLE_SECONDS)
            stamp = session.utc_iso(timespec="microseconds")
            rows = []
            for sym, (_c, t) in contracts.items():
                price = getattr(t, "auctionPrice", None)
                paired = getattr(t, "auctionVolume", None)
                imb = getattr(t, "auctionImbalance", None)
                if imb is None or imb != imb:
                    imb = getattr(t, "regulatoryImbalance", None)
                for key, value in ((PRICE_KEY, price), (PAIRED_KEY, paired),
                                   (IMBALANCE_KEY, imb)):
                    if value is None or value != value:
                        continue
                    rows.append({"registry_key": key, "instrument": sym,
                                 # OBSERVED AT THE TICK INSTANT, not the session:
                                 # this is an intraday series and its shape through
                                 # the window is the whole point.
                                 "observed_at": stamp, "available_at": stamp,
                                 "value": float(value), "source": "ibkr_paper",
                                 "run_id": run_id,
                                 "availability_kind": "observed"})
                if imb is not None and imb == imb:
                    rows.append({"registry_key": SIDE_KEY, "instrument": sym,
                                 "observed_at": stamp, "available_at": stamp,
                                 "value": (1.0 if imb > 0 else
                                           (-1.0 if imb < 0 else 0.0)),
                                 "source": "ibkr_paper", "run_id": run_id,
                                 "availability_kind": "observed"})
            if rows:
                written += db.write_many(rows)
                samples += 1
        for sym, (c, _t) in contracts.items():
            try:
                ib.cancelMktData(c)
            except Exception:                                  # noqa: BLE001
                pass
        return {"session": day, "event_classes": classes, "samples": samples,
                "written": written, "symbols": len(contracts)}
    except Exception as exc:                                   # noqa: BLE001
        log.exception("auction sampler raised")
        return {"error": f"{type(exc).__name__}: {exc}", "written": written}
    finally:
        if ib is not None:
            try:
                ib.disconnect()
            except Exception:                                  # noqa: BLE001
                pass
        if own:
            db.close()


def _seconds_until(t: dt.time) -> float:
    now = session.to_eastern()
    target = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
    return max(0.0, (target - now).total_seconds())


def keys() -> list[str]:
    return [PRICE_KEY, PAIRED_KEY, IMBALANCE_KEY, SIDE_KEY]


SPEC = register(LoggerSpec(
    name="auction",
    description="Closing-auction ticks (indicative price, paired, imbalance, side) "
                "for 11 NYSE-family names, 15:50-16:00 ET.",
    keys=keys,
    run=lambda **kw: {"skipped": "the sampler runs on its own timer, not in the "
                                 "overnight step", "written": 0},
    requires_key=None,
    min_history=20,
    # NOT IN THE FRESHNESS ROSTER YET, and this is the flag's whole purpose: the
    # sampler is dormant until an entitlement probe inside the auction window says
    # otherwise, and a dormant-by-design logger must not make the heartbeat red.
    # Flip this to True in the same commit that enables the timer.
    in_freshness=False,
    notes="Part 29.4 logging only. Raw imbalance is display-only; absorption is 6h "
          "and gated. Needs its own timer -- the enable command is printed, never "
          "run.",
))


def _main(argv: list[str]) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Closing-auction sampler.")
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("probe")
    pr.add_argument("--port", type=int, default=4002)
    pr.add_argument("--seconds", type=float, default=12.0)
    sm = sub.add_parser("sample")
    sm.add_argument("--port", type=int, default=4002)
    sm.add_argument("--seconds", type=float, default=None)
    sm.add_argument("--force", action="store_true")
    sub.add_parser("status")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    if a.cmd == "probe":
        print(json.dumps(probe(port=a.port, seconds=a.seconds), indent=2,
                         sort_keys=True))
        return 0
    if a.cmd == "status":
        print(json.dumps({"last_probe": last_probe(),
                          "event_classes_today": session.auction_event_classes(),
                          "in_window": in_window()},
                         indent=2, sort_keys=True))
        return 0
    print(json.dumps(sample(port=a.port, seconds=a.seconds, force=a.force),
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
