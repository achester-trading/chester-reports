"""
Treasury auction results -- TreasuryDirect securities API.

    python -m altdata.sources.treasury_auctions      # one pull, summary to stdout

Signal-triage order ST-1, feed row "Treasury auction results (auction.*)"; used by
SR-22 (the auction as the price-side symptom of SR-23's supply gap) and, at ST-4,
by the ABS_STRESS candidate flag. NOT the `ibkr.auction_*` family: those are the
EQUITY closing auction's imbalance feed. This family is `auction.*` -- Treasury.

SOURCE. https://www.treasurydirect.gov/TA_WS/securities/search
?startDate=..&endDate=..&dateFieldName=auctionDate&format=json -- no key. One
record per auction, back to 2009 at least. A record with no bidToCoverRatio has
not been held and is skipped.

WHAT IS STORED, per auction, keyed instrument = "<type>:<original term>" (e.g.
"Note:10-Year"; a 9-year-10-month reopening is still "Note:10-Year") and
observed_at = the auction date:

  auction.bid_to_cover        bidToCoverRatio                         ratio
  auction.dealer_share        primaryDealerAccepted / competitiveAccepted
  auction.direct_share        directBidderAccepted  / competitiveAccepted
  auction.indirect_share      indirectBidderAccepted / competitiveAccepted
  auction.high_yield          highYield, coupons only (Note, Bond, TIPS -- a
                              TIPS high yield is REAL); bills and FRNs price on
                              discount rate and margin and carry none
  auction.offering_amount     offeringAmount                          usd
  auction.cusip               the CUSIP, as text, so a reopening is identifiable

The three shares are of COMPETITIVE ACCEPTED, the Treasury's own denominator:
dealer + direct + indirect = competitiveAccepted exactly (checked on the 7-year of
24 Sep 2026: 5.448 + 13.164 + 24.870 = 43.481bn). SOMA add-ons and
non-competitive awards are outside it.

NOT STORED: THE TAIL. `auction.tail_bp` -- high yield minus the when-issued yield
at the 13:00 bid deadline -- needs the when-issued yield, which TreasuryDirect does
not publish and no free source serves. It is registered as not_yet_sourced and
prints NOT AVAILABLE until one is found. auction.high_yield is stored so a tail can
be computed the day a when-issued source exists; nothing here approximates one.

AVAILABILITY. available_at = 13:00 ET on the auction day, per the signal-triage
order, marked `reconstructed` (a declared latency on the observation date).
Permitted because auction results are never revised (revision_policy: never).
CAVEAT, measured: TreasuryDirect stamped the 24 Sep 2026 7-year's result
updatedTimestamp 13:03:20 -- coupon results post a few minutes AFTER the 13:00
competitive close, so 13:00 is minutes early for coupons; bills close at 11:30 and
13:00 is late for them. The constant is the order's and is named here so moving it
is a one-line, reviewable change.

FETCH WINDOW. A key with no stored rows triggers the backfill from
BACKFILL_START, a year per request; after that the last REFRESH_DAYS only.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Optional

from .. import observations, session
from . import _publication as pub
from ._base import http_get_json

log = logging.getLogger(__name__)

SOURCE = "treasurydirect"
URL = "https://www.treasurydirect.gov/TA_WS/securities/search"
BACKFILL_START = dt.date(2009, 1, 1)
REFRESH_DAYS = 45
AVAILABLE_ET = dt.time(13, 0)

KEYS = ["auction.bid_to_cover", "auction.dealer_share", "auction.direct_share",
        "auction.indirect_share", "auction.high_yield",
        "auction.offering_amount", "auction.cusip"]
# Registered, never written: see NOT STORED above.
NOT_SOURCED = ["auction.tail_bp"]
COUPON_TYPES = ("Note", "Bond", "TIPS")


def _num(v: Any) -> Optional[float]:
    try:
        x = float(str(v).strip())
    except (TypeError, ValueError):
        return None
    return x


def _term(rec: dict, typ: str) -> str:
    """The tenor an auction belongs to, for the instrument key.

    COUPONS BY ORIGINAL TERM, BILLS BY THE TERM SOLD. A 10-year reopening is sold
    as a "9-Year 10-Month" and belongs with the 10-year series, so coupons key on
    originalSecurityTerm. Bills are the opposite: a 13-week bill that reopens an
    old 26-week bill carries originalSecurityTerm "26-Week", and keying on it put
    1,080 bill auctions on top of the real 26- and 52-week ones on the first
    backfill. A bill is what it is sold as.
    """
    if typ in ("Bill", "CMB"):
        term = rec.get("securityTerm") or rec.get("originalSecurityTerm")
    else:
        term = rec.get("originalSecurityTerm") or rec.get("securityTerm")
    return str(term or "").strip()


def available_at(auction_day: str) -> str:
    """13:00 America/New_York on the auction day, as canonical UTC."""
    et = session._eastern_tz()
    local = dt.datetime.combine(dt.date.fromisoformat(auction_day), AVAILABLE_ET,
                                tzinfo=et)
    return observations.canonical_instant(
        local.astimezone(dt.timezone.utc).isoformat())


def rows_from_records(records: list[dict]) -> list[dict]:
    """Observation rows from TreasuryDirect records. Unheld auctions skipped."""
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for rec in records:
        btc = _num(rec.get("bidToCoverRatio"))
        day = str(rec.get("auctionDate") or "")[:10]
        if btc is None or len(day) != 10:
            continue
        typ = str(rec.get("type") or rec.get("securityType") or "").strip()
        term = _term(rec, typ)
        if not typ or not term:
            continue
        inst = f"{typ}:{term}"
        if (inst, day) in seen:
            # Two auctions of one instrument on one day (a CMB pair, say) would
            # collide on the store's key. The first is kept and the collision is
            # said out loud rather than resolved by whichever row wins the insert.
            log.warning("auctions: second %s auction on %s (cusip %s) skipped",
                        inst, day, rec.get("cusip"))
            continue
        seen.add((inst, day))
        avail = available_at(day)
        base = {"instrument": inst, "observed_at": day, "available_at": avail,
                "availability_kind": "reconstructed"}
        vals: dict[str, Any] = {"auction.bid_to_cover": btc}
        comp = _num(rec.get("competitiveAccepted"))
        if comp and comp > 0:
            for key, field in (("auction.dealer_share", "primaryDealerAccepted"),
                               ("auction.direct_share", "directBidderAccepted"),
                               ("auction.indirect_share",
                                "indirectBidderAccepted")):
                x = _num(rec.get(field))
                if x is not None:
                    vals[key] = round(x / comp, 8)
        if typ in COUPON_TYPES:
            hy = _num(rec.get("highYield"))
            if hy is not None:
                vals["auction.high_yield"] = hy
        off = _num(rec.get("offeringAmount"))
        if off is not None:
            vals["auction.offering_amount"] = off
        if rec.get("cusip"):
            vals["auction.cusip"] = str(rec["cusip"]).strip()
        for key, v in vals.items():
            out.append(dict(base, registry_key=key, value=v))
    return out


def _ranges(db: Optional[observations.ObservationStore]) -> list[tuple[str, str]]:
    today = session.session_date_obj()
    own = db is None
    store = db or observations.ObservationStore()
    try:
        held = pub.newest_observed(store, ["auction.bid_to_cover"])
    finally:
        if own:
            store.close()
    if held.get("auction.bid_to_cover"):
        return [((today - dt.timedelta(days=REFRESH_DAYS)).isoformat(),
                 today.isoformat())]
    out, start = [], BACKFILL_START
    while start <= today:
        end = min(dt.date(start.year, 12, 31), today)
        out.append((start.isoformat(), end.isoformat()))
        start = dt.date(start.year + 1, 1, 1)
    return out


def fetch_records(start: str, end: str) -> list[dict]:
    data = http_get_json(URL, params={"startDate": start, "endDate": end,
                                      "dateFieldName": "auctionDate",
                                      "format": "json"}, timeout=60)
    if not isinstance(data, list):
        raise ValueError(f"TreasuryDirect returned {type(data).__name__}, "
                         f"not a list of auctions")
    return data


def pull(run_id: Optional[str] = None, db=None) -> dict:
    def produce() -> list[dict]:
        records: list[dict] = []
        for start, end in _ranges(db):
            records.extend(fetch_records(start, end))
        return rows_from_records(records)
    return pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
