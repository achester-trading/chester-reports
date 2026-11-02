"""
Fill capture: each IBKR paper fill of an order this executor sent becomes one row
of the lab's `fills`, in the expectancy schema, with source='paper_exec', the
venue's order id and the fill's own time. A parent's fill opens a position; a
child's (the stop or the target) closes it and grades it by the lab's own rule
(alpha/paper.py: net over notional), so a paper trade's net_return is the unit
the engine's backtest expectancy is in.

fill_kind is 'quote' -- an executed price at the venue, never a modelled bar --
and reference_price = modelled_price = the fill's price: the lab's modelled fill
for the same signal is compared with it in the next tranche (the implementation
shortfall line). Costs: the venue's commission; the other components are zero.
A fill already captured (its order id and time) is never written twice.
"""

from __future__ import annotations

from typing import Any

COST_CLASS = "future"


def _order_map(state) -> dict[int, dict]:
    """order id -> {purpose, intent, bracket}, from the sent brackets."""
    out: dict[int, dict] = {}
    for o in state.orders():
        if o.get("state") != "sent":
            continue
        ids = [int(i) for i in o.get("order_ids") or []]
        for n, oid in enumerate(ids):
            out[oid] = {"purpose": "entry" if n == 0 else "exit",
                        "leg": ("parent", "target", "stop")[n] if n < 3 else "?", **o}
    return out


def _seen(ledger, oid: str, at: str) -> bool:
    return bool(ledger.one("SELECT 1 FROM fills WHERE source='paper_exec' AND "
                           "venue_order_id=? AND venue_fill_time=?", (oid, at)))


def capture(ledger, state, fills: list[Any]) -> list[int]:
    """The ledger fill ids written for `fills` (ib.fills()). Fills of orders the
    executor did not send are left alone (reconciliation names them)."""
    om = _order_map(state)
    written = []
    for f in fills or []:
        ex = f.execution
        oid = int(ex.orderId)
        info = om.get(oid)
        if info is None:
            continue
        at = (ex.time.isoformat() if hasattr(ex.time, "isoformat") else str(ex.time))
        if _seen(ledger, str(oid), at):
            continue
        intent = info["intent"]
        side = 1 if str(ex.side).upper() in ("BOT", "BUY") else -1
        qty, price = float(ex.shares), float(ex.price)
        commission = abs(float(getattr(getattr(f, "commissionReport", None),
                                       "commission", 0.0) or 0.0))
        fid = ledger.add_fill({
            "signal_id": intent.get("signal_id"), "engine_id": intent["engine_id"],
            "instrument": intent["symbol"], "purpose": info["purpose"], "side": side,
            "qty": qty, "fill_kind": "quote", "reference_price": price,
            "modelled_price": price, "stored_quote": None, "cost_class": COST_CLASS,
            "cost_spread": 0.0, "cost_slippage": 0.0, "cost_commission": commission,
            "cost_borrow": 0.0, "cost_roll": 0.0, "cost_funding": 0.0, "cost_fx": 0.0,
            "cost_total": commission, "filled_at": at, "as_of": at,
            "source": "paper_exec", "venue_order_id": str(oid), "venue_fill_time": at})
        written.append(fid)
        mult = float(info.get("multiplier") or 1)
        if info["purpose"] == "entry":
            pid = ledger.open_position({
                "engine_id": intent["engine_id"], "signal_id": intent.get("signal_id"),
                "instrument": intent["symbol"], "cost_class": COST_CLASS,
                "direction": side, "qty": qty, "entry_fill_id": fid,
                "entry_price": price, "stop_price": intent.get("stop"),
                "target_price": intent.get("target"), "opened_at": at, "as_of": at})
            ledger.link_fill(fid, pid)
            continue
        pos = ledger.one(
            "SELECT p.* FROM positions p JOIN fills f ON f.id = p.entry_fill_id "
            "WHERE p.status='open' AND f.source='paper_exec' AND p.engine_id=? AND "
            "p.instrument=? ORDER BY p.id LIMIT 1", (intent["engine_id"], intent["symbol"]))
        if pos is None:
            continue
        ledger.link_fill(fid, pos["id"])
        ledger.close_position(pos["id"], fid, price, f"paper {info['leg']}", at)
        entry = ledger.one("SELECT cost_total FROM fills WHERE id=?", (pos["entry_fill_id"],))
        notional = pos["qty"] * pos["entry_price"] * mult
        gross = pos["direction"] * pos["qty"] * mult * (price - pos["entry_price"])
        cost = float(entry["cost_total"]) + commission
        net = gross - cost
        ledger.add_grade({"position_id": pos["id"], "engine_id": pos["engine_id"],
                          "day": at[:10], "gross_pnl": gross, "costs": cost,
                          "net_pnl": net,
                          "net_return": net / notional if notional else 0.0,
                          "win": int(net > 0), "regime_key": None, "as_of": at})
    return written
