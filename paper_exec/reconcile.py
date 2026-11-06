"""
Reconciliation at start: the gateway against the ledger, before any send.

  POSITIONS. For each instrument, the gateway's net position against the
  ledger's open paper positions (positions opened by a source='paper_exec' fill),
  signed. Any difference is a mismatch.
  OPEN ORDERS. Every open order at the gateway must be one this executor sent
  (its orderRef carries REF_PREFIX and its order id is in the order log). An
  order the executor did not send -- a hand-placed one, another tool's -- is a
  mismatch.

Any mismatch stops sending (State.set_reconcile) and names itself; a clean
reconciliation clears the block.
"""

from __future__ import annotations

from typing import Any

REF_PREFIX = "paper_exec:"


def ledger_net(ledger) -> dict[str, float]:
    out: dict[str, float] = {}
    rows = ledger.q(
        "SELECT p.instrument, p.direction, p.qty FROM positions p JOIN fills f "
        "ON f.id = p.entry_fill_id WHERE p.status='open' AND f.source='paper_exec'")
    for r in rows:
        out[r["instrument"]] = out.get(r["instrument"], 0.0) + r["direction"] * r["qty"]
    return out


def gateway_net(ib: Any) -> dict[str, float]:
    out: dict[str, float] = {}
    for p in ib.positions() or []:
        sym = str(getattr(p.contract, "symbol", "") or getattr(p.contract, "localSymbol", ""))
        out[sym] = out.get(sym, 0.0) + float(p.position)
    return out


def run(ib: Any, ledger, state) -> list[str]:
    """The mismatches, each named; [] when the gateway and the ledger agree."""
    bad: list[str] = []
    g, lg = gateway_net(ib), ledger_net(ledger)
    for sym in sorted(set(g) | set(lg)):
        if abs(g.get(sym, 0.0) - lg.get(sym, 0.0)) > 1e-9:
            bad.append(f"{sym}: the gateway holds {g.get(sym, 0.0):+g}, the ledger "
                       f"{lg.get(sym, 0.0):+g}")
    sent = {int(i) for o in state.orders() if o.get("state") == "sent"
            for i in o.get("order_ids") or []}
    for t in ib.openTrades() or []:
        o = t.order
        ref = str(getattr(o, "orderRef", "") or "")
        if not ref.startswith(REF_PREFIX) or int(getattr(o, "orderId", -1)) not in sent:
            bad.append(f"an open order this executor did not send: id "
                       f"{getattr(o, 'orderId', '?')}, ref {ref or 'none'}")
    state.set_reconcile(bad)
    return bad
