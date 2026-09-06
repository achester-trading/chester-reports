"""
Schedule-derived expression economics -- the Gate 1.5 fallback.

THE RULING, 5 Sep 2026. IB Gateway refuses What-If under Read-Only API,
measured on the VPS: "The API interface is currently in Read-Only mode".
What-If travels as a placeOrder message with whatIf=True, so a Gateway that
blocks order submission blocks previews with it. Read-Only STAYS ON through the
hand-placed-orders phase and comes off at Gate 2 by design, when code-side
guards replace it.

So until Gate 2 the economics come from here: IBKR's published commission
schedule plus a margin impact derived from the account's own measured leverage.
ibkr_whatif.py is untouched and remains the Gate 2 path.

-----------------------------------------------------------------------------
cost_source IS THE POINT OF THIS MODULE
-----------------------------------------------------------------------------

Every estimate carries `cost_source="estimated_from_schedule"`; every What-If
carries `cost_source="whatif"`. A packet must never claim a broker preview it
did not get, because 26.16 #5 grades whether a thesis was rejected on REAL
economics -- and an estimate that reads like a quote would make that test pass
on arithmetic the broker never saw.

Three grades, kept distinct wherever this data goes:

    whatif                    the broker priced it
    estimated_from_schedule   we priced it from a published rate card
    NULL                      nobody priced it

-----------------------------------------------------------------------------
WHAT IS MEASURED AND WHAT IS DECLARED
-----------------------------------------------------------------------------

MEASURED, from the live account (account reads are unaffected by Read-Only API
-- accountSummary is a read, not an order):

    leverage multiplier   BuyingPower / AvailableFunds
    maint/init ratio      FullMaintMarginReq / FullInitMarginReq

Initial margin for a new position is then notional / multiplier, which is the
account's own initial-margin rate inverted rather than Reg T's 50% assumed. If
the account holds nothing, the maint/init ratio is unmeasurable and maintenance
margin is reported None rather than guessed.

DECLARED, in config, with source and date: the commission rate card. Stocks
were hand-read from Client Portal on 2026-09-05 and are VERIFIED -- Fixed
pricing, all-in. Options are NOT: they still carry Tiered bands on a Fixed
account, so their card matches nothing. The two are flagged separately, and
whichever applies rides along in every estimate this module produces, along
with a structure_mismatch flag when the card and the account disagree.

DERIVED, exactly: buying-power delta is -notional. Not an approximation --
BuyingPower = AvailableFunds x m and AvailableFunds falls by notional/m, so the
m cancels. It holds whatever the account's leverage is.

-----------------------------------------------------------------------------
WHERE THIS IS WEAKER THAN A WHAT-IF, STATED RATHER THAN SMOOTHED
-----------------------------------------------------------------------------

  * Commission excludes exchange, clearing and regulatory pass-throughs. The
    estimate is a FLOOR on the true cost, not a central estimate.
  * Short stock is not modelled. Reg T requires 150% for a short and the
    long-side multiplier does not describe it, so a SELL of stock is flagged
    rather than silently under-margined.
  * Options assume the top premium band unless a premium is supplied.
  * It knows nothing about the spread, which for a real order is usually larger
    than the commission. A What-If does not price the spread either, but it at
    least prices the account's real margin treatment.

Usage:
    python -m altdata.sources.ibkr_costs --instrument SPY --quantity 100 \\
        --price 770.67
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Optional

from .. import config
from .. import session
from . import ibkr_portfolio as ibkr

log = logging.getLogger(__name__)

COST_SOURCE = "estimated_from_schedule"
METHOD_VERSION = "schedule_v1"


def commission_stk(shares: float, price: Optional[float]) -> dict:
    """IBKR Pro FIXED, US stocks. Floor and cap both applied and both named."""
    per_share = config.IBKR_STK_FIXED_PER_SHARE
    floor = config.IBKR_STK_FIXED_MIN_PER_ORDER
    raw = abs(shares) * per_share
    est = max(raw, floor)
    floor_applied = est > raw

    cap = None
    cap_applied = False
    if price is not None:
        cap = abs(shares) * price * config.IBKR_STK_FIXED_MAX_PCT_OF_TRADE
        if est > cap:
            est, cap_applied = cap, True

    return {
        "estimate": round(est, 4),
        "raw_per_share_total": round(raw, 4),
        "floor_applied": floor_applied,
        "cap": None if cap is None else round(cap, 4),
        "cap_applied": cap_applied,
        "currency": "USD",
        "rate_card": (f"{per_share} per share, {floor} order floor, "
                      f"{config.IBKR_STK_FIXED_MAX_PCT_OF_TRADE:.1%} cap"),
    }


def commission_opt(contracts: float, premium: Optional[float]) -> dict:
    """IBKR Pro Tiered, US options. Premium band assumed when unknown."""
    bands = config.IBKR_OPT_TIERED_PER_CONTRACT
    if premium is None:
        # The top band. Overstates a cheap contract rather than understating an
        # expensive one, and says which it did.
        per_contract = bands[0][1]
        assumed = True
    else:
        per_contract = bands[-1][1]
        assumed = False
        for threshold, rate in bands:
            if premium >= threshold:
                per_contract = rate
                break

    floor = config.IBKR_OPT_TIERED_MIN_PER_ORDER
    raw = abs(contracts) * per_contract
    est = max(raw, floor)
    return {
        "estimate": round(est, 4),
        "raw_per_contract_total": round(raw, 4),
        "per_contract": per_contract,
        "premium_band_assumed": assumed,
        "floor_applied": est > raw,
        "cap": None,
        "cap_applied": False,
        "currency": "USD",
        "rate_card": f"{per_contract} per contract, {floor} order floor",
    }


def margin_impact(notional: float, baseline: dict, action: str,
                  sec_type: str) -> dict:
    """Margin and buying-power impact from the account's MEASURED leverage.

    The multiplier is the account's own, not Reg T's assumed 4. If it cannot be
    measured, everything downstream of it is None -- an unmeasurable account
    yields no margin estimate rather than a plausible one.
    """
    bp = baseline.get("BuyingPower")
    af = baseline.get("AvailableFunds")
    init_req = baseline.get("FullInitMarginReq")
    maint_req = baseline.get("FullMaintMarginReq")
    ewl = baseline.get("NetLiquidation")

    mult = (bp / af) if (bp is not None and af not in (None, 0)) else None
    init_change = (notional / mult) if mult else None

    # Maintenance from the account's OWN maint/init ratio, where it holds
    # enough to have one. An empty account has 0/0 and gets None.
    ratio = ((maint_req / init_req)
             if (maint_req is not None and init_req not in (None, 0)) else None)
    maint_change = (init_change * ratio) if (init_change is not None and ratio) else None

    caveats = []
    if action == "SELL" and sec_type == "STK":
        caveats.append(
            "SHORT STOCK IS NOT MODELLED. Reg T requires 150% of the short's "
            "value (100% proceeds plus 50%), and the long-side leverage "
            "multiplier does not describe that. Treat this initial-margin "
            "figure as a lower bound, possibly by a factor of three.")
    if ratio is None:
        caveats.append(
            "maintenance margin is unmeasurable -- the account reports no "
            "existing init/maint requirement to take a ratio from, so it is "
            "reported None rather than assumed.")

    return {
        "init_before": init_req,
        "init_after": (init_req + init_change)
                      if (init_req is not None and init_change is not None) else None,
        "init_change": None if init_change is None else round(init_change, 2),
        "maint_before": maint_req,
        "maint_after": (maint_req + maint_change)
                       if (maint_req is not None and maint_change is not None) else None,
        "maint_change": None if maint_change is None else round(maint_change, 2),
        "leverage_multiplier_observed": mult,
        "maint_to_init_ratio_observed": ratio,
        "equity_with_loan_reference": ewl,
        "caveats": caveats,
    }


def buying_power_impact(notional: float, baseline: dict) -> dict:
    """Buying-power delta, which is exactly -notional. See the module docstring."""
    bp = baseline.get("BuyingPower")
    af = baseline.get("AvailableFunds")
    mult = (bp / af) if (bp is not None and af not in (None, 0)) else None
    return {
        "buying_power_before": bp,
        "buying_power_after_est": (bp - notional) if bp is not None else None,
        "buying_power_delta_est": -notional,
        "available_funds_before": af,
        "available_funds_after": (af - notional / mult)
                                 if (af is not None and mult) else None,
        "available_funds_delta": (-notional / mult) if mult else None,
        "leverage_multiplier_observed": mult,
        "derivation": (
            "buying-power delta is exactly -notional: BuyingPower = "
            "AvailableFunds x m and AvailableFunds falls by notional/m, so m "
            "cancels and the result holds at any leverage. AvailableFunds "
            "delta does depend on m, which is measured from this account."),
    }


def estimate(instrument: str, direction: str, quantity: float,
             price: Optional[float], sec_type: str = "STK",
             baseline: Optional[dict] = None, action: Optional[str] = None,
             premium: Optional[float] = None, multiplier: Optional[float] = None,
             price_source: str = "unknown", port: int = ibkr.DEFAULT_PORT,
             run_id: Optional[str] = None) -> dict:
    """A full expected_cost record from the rate card. Never contacts a broker.

    `baseline` is the account read; without one the commission still estimates
    and the margin fields are all None, which is the honest shape for "we know
    the rate card but not the account".
    """
    from .ibkr_whatif import action_for_direction   # noqa: PLC0415

    sec = (sec_type or "STK").upper()
    side = action_for_direction(direction, action)
    baseline = baseline or {}
    contract_mult = multiplier if multiplier is not None else (100.0 if sec == "OPT" else 1.0)

    notional = (abs(quantity) * price * contract_mult) if price is not None else None

    if sec == "OPT":
        comm = commission_opt(quantity, premium if premium is not None else price)
    else:
        comm = commission_stk(quantity, price)

    marg = (margin_impact(notional, baseline, side, sec) if notional is not None
            else {"init_change": None, "maint_change": None,
                  "caveats": ["no price available, so no notional and no "
                              "margin estimate"]})
    bpow = (buying_power_impact(notional, baseline) if notional is not None
            else {"buying_power_delta_est": None,
                  "derivation": "no price available, so no notional"})

    # Which rate card actually priced this, and whether it matches the account.
    if sec == "OPT":
        card_structure = config.IBKR_OPT_SCHEDULE_STRUCTURE
        card_verified = config.IBKR_OPT_COMMISSION_VERIFIED
    else:
        card_structure = config.IBKR_ACCOUNT_COMMISSION_STRUCTURE
        card_verified = config.IBKR_STK_COMMISSION_VERIFIED
    structure_mismatch = card_structure != config.IBKR_ACCOUNT_COMMISSION_STRUCTURE

    return {
        "cost_source": COST_SOURCE,
        "method_version": METHOD_VERSION,
        "available": True,
        "instrument": instrument.upper(),
        "direction": direction,
        "action": side,
        "quantity": float(quantity),
        "sec_type": sec,
        "price": price,
        "price_source": price_source,
        "contract_multiplier": contract_mult,
        "notional": notional,
        "commission": comm,
        "margin": marg,
        "buying_power": bpow,
        "baseline": baseline,
        "estimated_at": session.utc_iso(timespec="microseconds"),
        "mode": ibkr.mode_for_port(port),
        "source": ibkr.source_for_port(port),
        "run_id": run_id,
        # The rate card's provenance travels WITH the number, so a packet read
        # in six months does not have to guess which schedule produced it.
        # Stock and option cards are verified INDEPENDENTLY: the account is
        # Fixed and the stock card was hand-read on 2026-09-05, while the
        # option card is still Tiered bands and describes no account we have.
        # One shared flag would let the verified stock card vouch for it.
        "schedule": {
            "structure": card_structure,
            "account_structure": config.IBKR_ACCOUNT_COMMISSION_STRUCTURE,
            "structure_mismatch": structure_mismatch,
            "source": config.IBKR_COMMISSION_SCHEDULE_SOURCE,
            "as_of": config.IBKR_COMMISSION_SCHEDULE_AS_OF,
            "verified": card_verified,
            # Stamped only when the card really was read; an unverified card
            # carries no borrowed provenance.
            "verified_on": (config.IBKR_COMMISSION_SCHEDULE_VERIFIED_ON
                            if card_verified else None),
            "verified_by": (config.IBKR_COMMISSION_SCHEDULE_VERIFIED_BY
                            if card_verified else None),
            "verify_note": config.IBKR_COMMISSION_SCHEDULE_VERIFY_NOTE,
        },
        "excludes": list(config.IBKR_OPT_EXCLUSIONS if sec == "OPT"
                         else config.IBKR_STK_EXCLUSIONS),
        "is_floor_not_all_in": (not config.IBKR_OPT_IS_ALL_IN) if sec == "OPT"
                               else (not config.IBKR_STK_IS_ALL_IN),
    }


def read_baseline(host: str = ibkr.DEFAULT_HOST, port: int = ibkr.DEFAULT_PORT,
                  client_id: int = 19, allow_live: bool = False,
                  ib_factory=None) -> dict:
    """Account values for the margin side. A READ -- Read-Only API permits it.

    Client id 19: distinct from Portfolio Truth's 17 and What-If's 18, so three
    concurrent sessions never collide and the Gateway log says which is which.
    """
    from .ibkr_whatif import read_baseline as _read   # noqa: PLC0415
    ib = ibkr.connect(host=host, port=port, client_id=client_id,
                      allow_live=allow_live, ib_factory=ib_factory)
    try:
        return _read(ib)
    finally:
        try:
            ib.disconnect()
        except Exception:  # noqa: BLE001
            pass


def format_estimate(e: dict, indent: str = "  ") -> str:
    """Human-readable, and unmistakably an estimate rather than a quote."""
    def money(v, w=14):
        return f"{v:>{w},.2f}" if isinstance(v, (int, float)) else f"{'n/a':>{w}}"

    c, m, b = e.get("commission") or {}, e.get("margin") or {}, e.get("buying_power") or {}
    L = [f"{indent}{e.get('action')} {e.get('quantity'):,.0f} {e.get('instrument')} "
         f"{e.get('sec_type')}   [{e.get('mode')}]   "
         f"cost_source={e.get('cost_source')}"]
    L.append(f"{indent}price             {money(e.get('price'))}   "
             f"({e.get('price_source')})")
    L.append(f"{indent}notional          {money(e.get('notional'))}")
    L.append(f"{indent}commission        {money(c.get('estimate'))} "
             f"{c.get('currency') or ''}   [{c.get('rate_card')}]"
             + ("  FLOOR APPLIED" if c.get("floor_applied") else "")
             + ("  1% CAP APPLIED" if c.get("cap_applied") else ""))
    L.append(f"{indent}init margin       {money(m.get('init_before'))} -> "
             f"{money(m.get('init_after'))}   change {money(m.get('init_change'))}")
    L.append(f"{indent}maint margin      {money(m.get('maint_before'))} -> "
             f"{money(m.get('maint_after'))}   change {money(m.get('maint_change'))}")
    L.append(f"{indent}buying power      {money(b.get('buying_power_before'))} -> "
             f"{money(b.get('buying_power_after_est'))}   delta "
             f"{money(b.get('buying_power_delta_est'))}")
    mult = m.get("leverage_multiplier_observed")
    ratio = m.get("maint_to_init_ratio_observed")
    L.append(f"{indent}  leverage multiplier measured from this account: "
             + (f"{mult:.2f}x" if isinstance(mult, (int, float)) else "unmeasurable")
             + ("  maint/init " + (f"{ratio:.3f}" if isinstance(ratio, (int, float))
                                   else "unmeasurable")))
    sch = e.get("schedule") or {}
    if not sch.get("verified"):
        L.append(f"{indent}  SCHEDULE UNVERIFIED ({sch.get('as_of')}) -- "
                 f"{sch.get('source')}")
    if sch.get("structure_mismatch"):
        L.append(f"{indent}  SCHEDULE STRUCTURE MISMATCH: rate card is "
                 f"{sch.get('structure')} but this account is "
                 f"{sch.get('account_structure')} -- this is not this "
                 f"account's cost")
    if e.get("is_floor_not_all_in"):
        L.append(f"{indent}  FLOOR, NOT ALL-IN. Excludes: "
                 f"{', '.join(e.get('excludes') or [])}")
    for cav in (m.get("caveats") or []):
        L.append(f"{indent}  CAVEAT: {cav}")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Schedule-derived cost estimate (no broker preview)")
    ap.add_argument("--instrument", required=True)
    ap.add_argument("--direction", default="long",
                    choices=("long", "short", "flat", "hedge"))
    ap.add_argument("--action", default=None, choices=("BUY", "SELL"))
    ap.add_argument("--quantity", type=float, required=True)
    ap.add_argument("--price", type=float, default=None)
    ap.add_argument("--premium", type=float, default=None, help="OPT only")
    ap.add_argument("--sec-type", default="STK", choices=("STK", "OPT"))
    ap.add_argument("--no-account", action="store_true",
                    help="Skip the account read; commission only")
    ap.add_argument("--host", default=ibkr.DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=ibkr.DEFAULT_PORT)
    ap.add_argument("--allow-live", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    baseline = {}
    if not args.no_account:
        try:
            baseline = read_baseline(host=args.host, port=args.port,
                                     allow_live=args.allow_live)
        except ibkr.IbkrError as e:
            print(f"account read unavailable ({type(e).__name__}); commission "
                  f"only\n  {str(e).splitlines()[0]}", file=sys.stderr)

    e = estimate(args.instrument, args.direction, args.quantity, args.price,
                 sec_type=args.sec_type, baseline=baseline, action=args.action,
                 premium=args.premium, port=args.port,
                 price_source="--price" if args.price is not None else "none")
    print(json.dumps(e, indent=2, default=str) if args.json
          else format_estimate(e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
