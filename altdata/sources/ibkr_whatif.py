"""
Expression Intelligence -- What-If order previews. Read-only. (26.11, Gate 1.5)

The third of the four read-only IBKR services. Portfolio Truth answers "what do
I hold"; this answers "what would this cost me" -- commission, initial and
maintenance margin impact, and the buying-power delta -- for an order that is
contemplated and never sent.

26.16 #5 is the acceptance test this exists to make possible: a valid thesis
rejected on real IBKR spread, margin, commission and concentration. You cannot
reject a trade on economics you have not measured, and the economics are not
knowable from a price feed -- commission tiers, margin treatment and the
account's own leverage state live at the broker.

-----------------------------------------------------------------------------
THIS MODULE CONSTRUCTS AN ORDER OBJECT, AND THAT IS A REAL DIFFERENCE
-----------------------------------------------------------------------------

ibkr_portfolio.py holds the Gate 1 line absolutely -- no order type imported,
none constructed, `Order(` banned from its source by a validation gate. This
module CANNOT hold that line, because IBKR's What-If is not a separate request
type: it is a placeOrder message with the whatIf flag set, and ib_async's
`whatIfOrder()` calls `client.placeOrder` internally with `whatIf=True`.

So the guarantee here is different in kind, and stated rather than blurred:

    * The order object is built with whatIf=True at construction, and that is
      re-asserted immediately before the call. A preview that lost the flag
      would be an order.
    * transmit=False as well. Belt and braces; irrelevant to whatIfOrder, and
      the point is that it costs nothing to be wrong about which one saves you.
    * `ib.placeOrder` is never called by this module, and a validation gate
      greps this source for it exactly as it does for ibkr_portfolio.
    * The two modules keep SEPARATE client ids (17 and 18) so a What-If session
      is distinguishable from a Portfolio Truth session in the Gateway log.

Keeping this in its own module is the reason ibkr_portfolio's absolute claim
stays absolute. A single file doing both would have to weaken to the weaker of
the two guarantees, and the weakening would be invisible.

-----------------------------------------------------------------------------
WHAT `readonly=True` ACTUALLY DOES -- MEASURED, NOT ASSUMED
-----------------------------------------------------------------------------

In ib_async 2.1.0, the client-side `readonly=True` flag does ONE thing: it
skips fetching open and completed orders at startup (ib.py:2057, 2061). It
installs no check on placeOrder. It is not an order firewall.

The real read-only enforcement is SERVER-side: Gateway's
Configure > Settings > API > "Read-Only API" checkbox. That one does reject
order submission, and this module cannot weaken it.

The consequence, which is an operator decision and not ours to make: because
What-If travels as a placeOrder message, a Gateway with Read-Only API enabled
is expected to refuse What-If too. If it does, the choice is between Gate 1.5's
expression economics and Gate 1's strongest external guarantee. That refusal is
classified as `WhatIfNotPermitted` with the tradeoff spelled out, rather than
surfacing as a generic timeout -- because the fix is a decision, not a retry.

-----------------------------------------------------------------------------
THE DOUBLE.MAX_VALUE SENTINEL
-----------------------------------------------------------------------------

IBKR sends 1.7976931348623157E308 -- Java's Double.MAX_VALUE -- to mean "no
value", in commission and in the margin fields both. Parsed naively it is not
an error and not a NaN; it is a commission estimate of 1.8e308 dollars, which
propagates into a cost model and poisons it silently. `_num()` maps it to None.

Usage:
    python -m altdata.sources.ibkr_whatif --instrument SPY --direction long \\
        --quantity 100
    python -m altdata.sources.ibkr_whatif --instrument SPY --direction long \\
        --quantity 100 --json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any, Optional

from .. import session
from . import ibkr_portfolio as ibkr

log = logging.getLogger(__name__)

# Distinct from Portfolio Truth's 17, so the two sessions are separable in the
# Gateway's own log and a clash between them is a distinct, named error.
WHATIF_CLIENT_ID = 18

SEC_TYPES = ("STK", "OPT")
ORDER_TYPES = ("MKT", "LMT")
RIGHTS = ("C", "P")

# IBKR's "no value". See the module docstring.
IB_UNSET = 1.7976931348623157e308

# Account tags read BEFORE the preview, to give the deltas something real to be
# a delta from. OrderState carries no buying power at all, so the baseline is
# the only place a buying-power number can honestly come from.
BASELINE_TAGS = ("NetLiquidation", "BuyingPower", "AvailableFunds",
                 "ExcessLiquidity", "FullInitMarginReq", "FullMaintMarginReq")


class WhatIfError(ibkr.IbkrError):
    """Base for What-If specific failures."""


class WhatIfNotPermitted(WhatIfError):
    """The Gateway refused the What-If, almost always Read-Only API.

    Distinct from a generic API error because the remedy is a deliberate
    weakening of a safety setting, not a retry.
    """


class ContractNotResolved(WhatIfError):
    """IBKR could not resolve the contract, so no preview is possible."""


def action_for_direction(direction: str, action: Optional[str] = None) -> str:
    """BUY/SELL for the register's direction vocabulary.

    long and short map cleanly. `flat` and `hedge` DO NOT, and are refused
    rather than guessed: flat means close whatever is held, whose side and size
    depend on the current position; hedge names an intent, not a side. Guessing
    either would produce a confident preview of the wrong trade.
    """
    if action:
        if action not in ("BUY", "SELL"):
            raise ValueError(f"action must be BUY or SELL, got {action!r}")
        return action
    mapped = {"long": "BUY", "short": "SELL"}.get(direction)
    if mapped:
        return mapped
    raise ValueError(
        f"direction {direction!r} does not determine a side. `flat` closes a "
        f"position whose side and size depend on what is currently held, and "
        f"`hedge` names an intent rather than a side. Pass an explicit "
        f"action=BUY|SELL to preview one.")


def _num(v: Any) -> Optional[float]:
    """Float, with IBKR's Double.MAX_VALUE sentinel mapped to None."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f:                      # NaN
        return None
    # Compared with a wide relative tolerance rather than ==; the value makes a
    # round trip through a string field and need not come back bit-identical.
    if abs(f) >= IB_UNSET * 0.999:
        return None
    return f


def _delta(after: Optional[float], before: Optional[float]) -> Optional[float]:
    if after is None or before is None:
        return None
    return after - before


def build_contract(instrument: str, sec_type: str = "STK",
                   exchange: str = "SMART", currency: str = "USD",
                   expiry: Optional[str] = None, strike: Optional[float] = None,
                   right: Optional[str] = None):
    """The contract to price. Options require all three of expiry/strike/right.

    A partially specified option is refused rather than sent: IBKR would
    resolve it to SOME contract, and a preview of a contract you did not
    specify is worse than no preview.
    """
    from ib_async import Contract  # noqa: PLC0415 -- lazy: tests need no lib

    sec_type = sec_type.upper()
    if sec_type not in SEC_TYPES:
        raise ValueError(f"sec_type must be one of {SEC_TYPES}, got {sec_type!r}")

    if sec_type == "OPT":
        missing = [n for n, v in (("expiry", expiry), ("strike", strike),
                                  ("right", right)) if v in (None, "")]
        if missing:
            raise ValueError(
                f"an OPT contract needs expiry, strike and right; missing "
                f"{', '.join(missing)}. A partial option specification resolves "
                f"to some contract, which is not the one you meant to price.")
        if str(right).upper() not in RIGHTS:
            raise ValueError(f"right must be C or P, got {right!r}")
        return Contract(secType="OPT", symbol=instrument.upper(),
                        lastTradeDateOrContractMonth=str(expiry).replace("-", ""),
                        strike=float(strike), right=str(right).upper(),
                        exchange=exchange, currency=currency,
                        multiplier="100")
    return Contract(secType="STK", symbol=instrument.upper(),
                    exchange=exchange, primaryExchange="ARCA",
                    currency=currency)


def build_order(action: str, quantity: float, order_type: str = "MKT",
                limit_price: Optional[float] = None):
    """A What-If order. whatIf=True is set here and checked again at the call."""
    from ib_async import Order  # noqa: PLC0415

    order_type = order_type.upper()
    if order_type not in ORDER_TYPES:
        raise ValueError(f"order_type must be one of {ORDER_TYPES}, got "
                         f"{order_type!r}")
    if order_type == "LMT" and limit_price is None:
        raise ValueError("a LMT preview needs --limit-price; without one IBKR "
                         "prices a limit order at zero")
    if quantity <= 0:
        raise ValueError(f"quantity must be positive, got {quantity!r}; the "
                         f"side is carried by action, not by the sign")

    o = Order()
    o.action = action
    o.orderType = order_type
    o.totalQuantity = float(quantity)
    # THE FLAG. Without it this is an order.
    o.whatIf = True
    # Irrelevant to whatIfOrder, and free.
    o.transmit = False
    if order_type == "LMT":
        o.lmtPrice = float(limit_price)
    return o


def read_baseline(ib) -> dict:
    """Account state before the preview, so a delta has a real starting point.

    Split out for the same reason read_state is in Portfolio Truth: the
    validation gate exercises it against canned data with no connection.
    """
    try:
        rows = list(ib.accountSummary() or [])
    except Exception as e:  # noqa: BLE001
        raise ibkr.IbkrApiError(f"reading the account baseline failed: "
                                f"{type(e).__name__}: {e}") from e
    out: dict = {}
    for av in rows:
        tag = getattr(av, "tag", None)
        if tag in BASELINE_TAGS:
            out[tag] = _num(getattr(av, "value", None))
    return out


def _buying_power_projection(baseline: dict, init_after: Optional[float],
                             equity_after: Optional[float]) -> dict:
    """Buying-power delta, derived from IBKR's own identities and OBSERVED.

    OrderState carries no buying power, so this is derived rather than
    reported, and every step says so.

        AvailableFunds  = EquityWithLoanValue - FullInitMarginReq
        ExcessLiquidity = EquityWithLoanValue - FullMaintMarginReq

    Those are IBKR's definitions, so applying them to the What-If's `after`
    figures is arithmetic rather than assumption.

    Buying power is the one that needs care. It is AvailableFunds times a
    multiplier that depends on account type -- 1 for cash, 4 for Reg T
    intraday, something else for portfolio margin -- and hardcoding 4 would be
    inventing the account's own leverage. So the multiplier is MEASURED from
    the live account (BuyingPower / AvailableFunds), recorded in the output,
    and if it cannot be measured the projection is None rather than a guess.
    """
    bp_before = baseline.get("BuyingPower")
    af_before = baseline.get("AvailableFunds")
    af_after = _delta(equity_after, init_after)      # the identity, applied

    mult = None
    if bp_before is not None and af_before not in (None, 0):
        mult = bp_before / af_before

    bp_after = af_after * mult if (af_after is not None and mult is not None) else None
    return {
        "buying_power_before": bp_before,
        "buying_power_after_est": bp_after,
        "buying_power_delta_est": _delta(bp_after, bp_before),
        "available_funds_before": af_before,
        "available_funds_after": af_after,
        "available_funds_delta": _delta(af_after, af_before),
        "leverage_multiplier_observed": mult,
        "derivation": (
            "AvailableFunds = EquityWithLoanValue - FullInitMarginReq (IBKR "
            "identity, applied to the What-If's after-figures). BuyingPower is "
            "AvailableFunds x a multiplier measured from this account as "
            "BuyingPower/AvailableFunds, never assumed."),
    }


def parse_state(state, contract_desc: str, baseline: dict) -> dict:
    """OrderState -> a structured preview. No connection needed."""
    init_before = _num(getattr(state, "initMarginBefore", None))
    init_after = _num(getattr(state, "initMarginAfter", None))
    maint_before = _num(getattr(state, "maintMarginBefore", None))
    maint_after = _num(getattr(state, "maintMarginAfter", None))
    eq_before = _num(getattr(state, "equityWithLoanBefore", None))
    eq_after = _num(getattr(state, "equityWithLoanAfter", None))

    # IBKR reports both the change and the endpoints. Prefer its own change
    # field and fall back to the difference, because the two can disagree at
    # the cent level and its number is the one its risk engine used.
    init_change = _num(getattr(state, "initMarginChange", None))
    maint_change = _num(getattr(state, "maintMarginChange", None))
    eq_change = _num(getattr(state, "equityWithLoanChange", None))

    commission = _num(getattr(state, "commission", None))
    warning = (getattr(state, "warningText", "") or "").strip()

    out = {
        "contract": contract_desc,
        "status": getattr(state, "status", None),
        "commission": {
            "estimate": commission,
            "min": _num(getattr(state, "minCommission", None)),
            "max": _num(getattr(state, "maxCommission", None)),
            "currency": getattr(state, "commissionCurrency", None) or None,
        },
        "margin": {
            "init_before": init_before,
            "init_after": init_after,
            "init_change": init_change if init_change is not None
                           else _delta(init_after, init_before),
            "maint_before": maint_before,
            "maint_after": maint_after,
            "maint_change": maint_change if maint_change is not None
                            else _delta(maint_after, maint_before),
        },
        "equity_with_loan": {
            "before": eq_before,
            "after": eq_after,
            "change": eq_change if eq_change is not None
                      else _delta(eq_after, eq_before),
        },
        "buying_power": _buying_power_projection(baseline, init_after, eq_after),
        "baseline": baseline,
        "warning_text": warning or None,
    }

    # A preview with no commission and no margin figure is a shape, not an
    # estimate. Saying so here stops it being read as "this trade is free".
    out["complete"] = commission is not None and out["margin"]["init_change"] is not None
    return out


def _classify(e: Exception) -> Exception:
    """Map a raw failure onto the error whose FIX is different."""
    msg = str(e)
    low = msg.lower()
    if "read-only" in low or "read only" in low or "10199" in msg:
        return WhatIfNotPermitted(
            f"the Gateway refused the What-If: {msg}\n"
            f"This is almost certainly Read-Only API "
            f"(Configure > Settings > API > Read-Only API). What-If travels as "
            f"a placeOrder message with whatIf=True, so a Gateway that blocks "
            f"order submission blocks previews with it.\n"
            f"The tradeoff is an operator decision: Gate 1.5's expression "
            f"economics require the setting off, and turning it off removes "
            f"the strongest external guarantee behind Gate 1. Nothing in this "
            f"repo changes it for you.")
    if "no security definition" in low or "ambiguous" in low or "200" == msg[:3]:
        return ContractNotResolved(
            f"IBKR could not resolve the contract: {msg}. Check the symbol, "
            f"and for an option the expiry/strike/right triple.")
    return ibkr.IbkrApiError(f"What-If failed: {type(e).__name__}: {msg}")


def preview(ib, instrument: str, direction: str, quantity: float,
            order_type: str = "MKT", limit_price: Optional[float] = None,
            sec_type: str = "STK", expiry: Optional[str] = None,
            strike: Optional[float] = None, right: Optional[str] = None,
            action: Optional[str] = None, port: int = ibkr.DEFAULT_PORT,
            run_id: Optional[str] = None) -> dict:
    """One What-If, from an already-connected client. Never places an order."""
    side = action_for_direction(direction, action)
    contract = build_contract(instrument, sec_type=sec_type, expiry=expiry,
                              strike=strike, right=right)
    order = build_order(side, quantity, order_type=order_type,
                        limit_price=limit_price)

    # Re-asserted at the boundary. The flag is the entire difference between a
    # preview and a trade, and it is one attribute assignment away from being
    # lost to a refactor that looks harmless.
    if getattr(order, "whatIf", False) is not True:
        raise WhatIfError("refusing to send: whatIf is not True on the order")

    previewed_at = session.utc_iso(timespec="microseconds")
    baseline = read_baseline(ib)

    # Resolve the contract first, so an unresolvable symbol is ITS OWN error
    # rather than a confusing margin failure.
    try:
        details = ib.reqContractDetails(contract)
    except Exception as e:  # noqa: BLE001
        raise _classify(e) from e
    if not details:
        raise ContractNotResolved(
            f"IBKR returned no contract details for {instrument!r} "
            f"({sec_type}). Nothing was previewed.")
    resolved = getattr(details[0], "contract", contract)

    try:
        state = ib.whatIfOrder(resolved, order)
    except Exception as e:  # noqa: BLE001
        raise _classify(e) from e
    if state is None:
        raise WhatIfNotPermitted(
            "the Gateway returned no order state for the What-If. The usual "
            "cause is Read-Only API being enabled -- see the module docstring.")

    desc = (f"{getattr(resolved, 'localSymbol', None) or instrument.upper()} "
            f"{sec_type}")
    out = parse_state(state, desc, baseline)
    out.update({
        "instrument": instrument.upper(),
        "direction": direction,
        "action": side,
        "quantity": float(quantity),
        "order_type": order_type.upper(),
        "limit_price": limit_price,
        "sec_type": sec_type.upper(),
        "expiry": expiry,
        "strike": strike,
        "right": right,
        "previewed_at": previewed_at,
        "mode": ibkr.mode_for_port(port),
        "source": ibkr.source_for_port(port),
        "run_id": run_id,
        # Never inferred from a constant, exactly as Portfolio Truth derives
        # its source tag: a preview cannot claim paper while pricing live.
        "port": port,
    })
    return out


def run(instrument: str, direction: str, quantity: float,
        host: str = ibkr.DEFAULT_HOST, port: int = ibkr.DEFAULT_PORT,
        client_id: int = WHATIF_CLIENT_ID, allow_live: bool = False,
        ib_factory=None, **kw) -> dict:
    """Connect, preview once, disconnect. The convenience entry point."""
    ib = ibkr.connect(host=host, port=port, client_id=client_id,
                      allow_live=allow_live, ib_factory=ib_factory)
    try:
        return preview(ib, instrument, direction, quantity, port=port, **kw)
    finally:
        try:
            ib.disconnect()
        except Exception:  # noqa: BLE001 -- a failed disconnect ends nothing
            pass


def format_preview(p: dict, indent: str = "  ") -> str:
    """Human-readable economics. Used by the CLI and by decide.py --preview."""
    def money(v, w=14):
        return f"{v:>{w},.2f}" if isinstance(v, (int, float)) else f"{'n/a':>{w}}"

    L = []
    q = p.get("quantity")
    L.append(f"{indent}{p.get('action')} {q:,.0f} {p.get('instrument')} "
             f"{p.get('sec_type')} @ {p.get('order_type')}"
             + (f" {p.get('limit_price')}" if p.get("limit_price") else "")
             + f"   [{p.get('mode')}]")
    c, m, e, b = (p.get("commission") or {}, p.get("margin") or {},
                  p.get("equity_with_loan") or {}, p.get("buying_power") or {})
    L.append(f"{indent}commission        {money(c.get('estimate'))} "
             f"{c.get('currency') or ''}"
             + (f"   (min {c.get('min')}, max {c.get('max')})"
                if c.get("min") is not None else ""))
    L.append(f"{indent}init margin       {money(m.get('init_before'))} -> "
             f"{money(m.get('init_after'))}   change {money(m.get('init_change'))}")
    L.append(f"{indent}maint margin      {money(m.get('maint_before'))} -> "
             f"{money(m.get('maint_after'))}   change {money(m.get('maint_change'))}")
    L.append(f"{indent}equity with loan  {money(e.get('before'))} -> "
             f"{money(e.get('after'))}   change {money(e.get('change'))}")
    L.append(f"{indent}buying power      {money(b.get('buying_power_before'))} -> "
             f"{money(b.get('buying_power_after_est'))}   delta "
             f"{money(b.get('buying_power_delta_est'))}   DERIVED")
    mult = b.get("leverage_multiplier_observed")
    L.append(f"{indent}  leverage multiplier measured from this account: "
             + (f"{mult:.2f}x" if isinstance(mult, (int, float)) else "unmeasurable"))
    if p.get("warning_text"):
        L.append(f"{indent}IBKR warning      {p['warning_text']}")
    if not p.get("complete"):
        L.append(f"{indent}INCOMPLETE -- IBKR returned no commission or no "
                 f"margin figure. Do not read this as a free trade.")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="What-If preview for a contemplated order (read-only)")
    ap.add_argument("--instrument", required=True)
    ap.add_argument("--direction", default="long",
                    choices=("long", "short", "flat", "hedge"))
    ap.add_argument("--action", default=None, choices=("BUY", "SELL"),
                    help="Required for flat/hedge, which do not imply a side")
    ap.add_argument("--quantity", type=float, required=True)
    ap.add_argument("--order-type", default="MKT", choices=ORDER_TYPES)
    ap.add_argument("--limit-price", type=float, default=None)
    ap.add_argument("--sec-type", default="STK", choices=SEC_TYPES)
    ap.add_argument("--expiry", default=None, help="OPT only, YYYYMMDD")
    ap.add_argument("--strike", type=float, default=None, help="OPT only")
    ap.add_argument("--right", default=None, choices=RIGHTS, help="OPT only")
    ap.add_argument("--host", default=ibkr.DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=ibkr.DEFAULT_PORT)
    ap.add_argument("--client-id", type=int, default=WHATIF_CLIENT_ID)
    ap.add_argument("--allow-live", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    try:
        p = run(args.instrument, args.direction, args.quantity,
                host=args.host, port=args.port, client_id=args.client_id,
                allow_live=args.allow_live, order_type=args.order_type,
                limit_price=args.limit_price, sec_type=args.sec_type,
                expiry=args.expiry, strike=args.strike, right=args.right,
                action=args.action)
    except ibkr.IbkrError as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        return {"GatewayNotRunning": 2, "GatewayNotResponding": 3,
                "IbkrAuthError": 4, "WhatIfNotPermitted": 5,
                "ContractNotResolved": 6}.get(type(e).__name__, 1)

    if args.json:
        print(json.dumps(p, indent=2, default=str))
    else:
        print(format_preview(p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
