"""
Realised P&L from structured exits. (INC-6 follow-up, 1 Oct 2026)

    exit_from_executions(decision, executions, store)   the close, from its fills
    realised(decision, store)                            P&L in the listing ccy and USD

NEVER TYPED BY HAND. The two SPY closes of 24 Sep and 1 Oct carried their fills
and their P&L in --note free text, and the INC-6 figure (-8,951.36 USD) was
worked out in a chat. A close now carries its exit as fields -- price, UTC time,
currency, USD per unit of that currency -- and the P&L is computed from them and
from Portfolio Truth's average cost and quantity at the last sync BEFORE the exit:

    pnl_local = (exit_price - avg_cost) * quantity      (quantity signed: a short
                                                          is negative, so a rise
                                                          is a loss)
    pnl_usd   = pnl_local * exit_fx_to_usd              (the whole P&L at the exit
                                                          rate, INC-6's convention)

An input that is missing is named, and the P&L is absent rather than guessed.
"""

from __future__ import annotations

from typing import Any, Optional

# A short is closed by a BUY and a long by a SELL.
CLOSING_SIDE = {"long": "SLD", "short": "BOT"}


def _fx_to_usd(ccy: str, store: Any, as_of: Optional[str]) -> Optional[float]:
    """USD per one unit of `ccy`, from the stored FX series; None if unstored."""
    if str(ccy).upper() == "USD":
        return 1.0
    from register import heat  # noqa: PLC0415
    got = heat.to_usd(1.0, ccy, store, as_of)
    return got.get("usd")


def exit_from_executions(decision: dict, executions: list[dict],
                         store: Any = None) -> Optional[dict]:
    """The close's exit fields from the executions table, or None.

    The closing fills are those on the decision's own instrument, on the closing
    side, after the decision was taken. Several fills of one order (85 + 15 on
    24 Sep) are one exit: the price is their size-weighted mean, the time the
    last fill's.
    """
    side = CLOSING_SIDE.get(str(decision.get("direction")))
    inst = decision.get("instrument")
    # From when the decision was TAKEN (decision_time), not when its row was
    # written: a row recorded after the fact must still find its fill.
    since = str(decision.get("decision_time") or decision.get("created_at") or "")
    if not side or not inst:
        return None
    fills = sorted((e for e in executions
                    if e.get("instrument") == inst
                    and str(e.get("side")).upper() == side
                    and str(e.get("exec_time") or "") >= since),
                   key=lambda e: str(e.get("exec_time")))
    if not fills:
        return None
    # The LAST order's fills: one close, however many prints it took.
    last_order = fills[-1].get("order_id") or fills[-1].get("perm_id")
    if last_order is not None:
        fills = [e for e in fills
                 if (e.get("order_id") or e.get("perm_id")) == last_order]
    qty = sum(float(e.get("qty") or 0) for e in fills)
    if qty <= 0:
        return None
    price = sum(float(e["price"]) * float(e.get("qty") or 0) for e in fills) / qty
    when = str(fills[-1]["exec_time"]).replace("Z", "+00:00")
    ccy = str(fills[-1].get("currency") or "").upper() or None
    fx = _fx_to_usd(ccy, store, when) if ccy else None
    return {"exit_price": round(price, 6), "exit_time": when,
            "exit_currency": ccy, "exit_fx_to_usd": fx, "quantity": qty,
            "exec_ids": [e.get("exec_id") for e in fills],
            "fx_source": ("USD" if ccy == "USD" else
                          "stored FX series" if fx else
                          "no stored rate -- pass --exit-fx")}


def closes_in(rows: list[dict], first: str, last: str, store: Any) -> list[dict]:
    """Every live close whose exit (or, unrecorded, its write) falls in
    [first, last], with its realised P&L. For the close report and the Weekly."""
    out = []
    for r in rows:
        d = dict(r)
        if d.get("superseded_by") or d.get("status") != "closed":
            continue
        when = str(d.get("exit_time") or d.get("decision_time") or "")[:10]
        if not (first <= when <= last):
            continue
        p = realised(d, store)
        out.append({"id": d.get("id"), "instrument": d.get("instrument"),
                    "direction": d.get("direction"),
                    "close_reason": d.get("close_reason"),
                    "exit_time": d.get("exit_time"), "exit_price": d.get("exit_price"),
                    "currency": p.get("currency"), "pnl_local": p.get("pnl_local"),
                    "pnl_usd": p.get("pnl_usd"), "missing": p.get("missing") or []})
    return out


def realised(decision: dict, store: Any) -> dict:
    """{pnl_local, pnl_usd, currency, quantity, avg_cost, ...} or the reasons."""
    out: dict[str, Any] = {"decision_id": decision.get("id"),
                           "instrument": decision.get("instrument"),
                           "currency": decision.get("exit_currency"),
                           "pnl_local": None, "pnl_usd": None, "missing": []}
    px, when = decision.get("exit_price"), decision.get("exit_time")
    if px is None or not when:
        out["missing"].append("exit not recorded")
        return out
    qty = avg = None
    if store is not None:
        q = store.latest_as_of("portfolio.position_qty", as_of=when,
                               instrument=decision.get("instrument"))
        a = store.latest_as_of("portfolio.position_avg_cost", as_of=when,
                               instrument=decision.get("instrument"))
        qty = (q or {}).get("value_num")
        avg = (a or {}).get("value_num")
    if not qty:
        out["missing"].append("no nonzero Portfolio Truth quantity before the exit")
    if avg is None:
        out["missing"].append("no Portfolio Truth average cost before the exit")
    if out["missing"]:
        return out
    pnl_local = round((float(px) - float(avg)) * float(qty), 2)
    fx = decision.get("exit_fx_to_usd")
    out.update(quantity=qty, avg_cost=avg, exit_price=px, exit_time=when,
               pnl_local=pnl_local, exit_fx_to_usd=fx,
               pnl_usd=(round(pnl_local * float(fx), 2) if fx else None))
    if not fx:
        out["missing"].append(f"no exit_fx_to_usd: the P&L is in "
                              f"{out['currency']} only")
    return out
