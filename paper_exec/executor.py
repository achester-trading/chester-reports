"""
One pass of the executor, by hand, on the box: the rules in order.

    report = executor.run(intents, cfg, ledger)       # never sends unless both flags

  1. OFF          enabled false -> nothing connects; "paper executor off".
  2. KILLED       the sticky kill state -> nothing connects.
  3. PAPER ONLY   client.connect: a paper port, then paper accounts, or it raises
                  before any order object is built.
  4. FILLS        the gateway's fills of orders sent earlier into the ledger,
                  first, so the ledger holds them before the comparison.
  5. RECONCILE    the gateway against the ledger; a mismatch stops sending.
  6. EACH INTENT  the kill state again (a kill file stops the very next send),
                  the engine's decay pause, the contract (MES only; ES refused),
                  the bracket, the size (ceiling, governor, heat cap); then DRY
                  (built and logged, nothing sent) or SEND (both flags set).

THE ONE SEND PATH is _send(): it takes a contract and a bracket and refuses
anything but three orders -- the parent and its two children, each child tied to
the parent's id -- so an entry cannot leave here without its stop and target.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from . import client, contracts, fills, orders, reconcile
from . import config as pcfg
from .state import State

log = logging.getLogger(__name__)


class NotABracket(RuntimeError):
    pass


def governor_view(ledger, engine_id: str) -> dict:
    from alpha import governor                                  # noqa: PLC0415
    return {"lab": governor.lab_status(ledger), "engine": ledger.engine(engine_id) or {}}


def open_risk(ledger, cfg: dict) -> float:
    """The open paper positions' risk to their stops, in dollars."""
    total = 0.0
    for r in ledger.q(
            "SELECT p.instrument, p.qty, p.entry_price, p.stop_price FROM positions p "
            "JOIN fills f ON f.id = p.entry_fill_id WHERE p.status='open' AND "
            "f.source='paper_exec'"):
        mult = float(((cfg.get("instruments") or {}).get(r["instrument"]) or {})
                     .get("multiplier") or 1)
        if r["stop_price"] is not None:
            total += abs(r["entry_price"] - r["stop_price"]) * mult * r["qty"]
    return total


def describe(i: orders.Intent, c: dict, qty: int) -> dict:
    """What a dry run logs: contract, side, size, entry, stop, target."""
    return {"symbol": c["symbol"], "conid": c["conid"], "side": "BUY" if i.side == 1 else "SELL",
            "qty": qty, "entry_limit": i.entry, "stop": i.stop, "target": i.target}


def _send(ib: Any, contract: Any, bracket: Any, ref: str) -> list[int]:
    """Send a whole bracket or nothing: three orders, the children tied to the
    parent. The order ids, parent first."""
    legs = list(bracket or [])
    if len(legs) != 3:
        raise NotABracket(f"{len(legs)} order(s): an entry leaves only as a bracket")
    parent, *children = legs
    pid = int(getattr(parent, "orderId", 0) or 0)
    if not pid or any(int(getattr(ch, "parentId", -1)) != pid for ch in children):
        raise NotABracket("a child is not tied to the parent: not sent")
    for o in legs:
        o.orderRef = ref
    for o in legs:
        ib.placeOrder(contract, o)
    return [int(o.orderId) for o in legs]


def run(intents: list[orders.Intent], cfg: dict, ledger, *,
        ib_factory: Optional[Callable[[], Any]] = None, master=None,
        limits: Optional[dict] = None) -> dict:
    mode = pcfg.mode(cfg)
    st = State(pcfg.state_dir(cfg))
    rep: dict = {"mode": mode, "results": [], "reconcile": [], "fills": []}
    if mode == "off":
        rep["state"] = "paper executor off"
        return rep
    if st.killed():
        rep["state"] = "killed: nothing connects until the operator clears it"
        return rep
    ib = client.connect(cfg, ib_factory)          # raises on a live port or account
    try:
        # The fills of this executor's own orders come in FIRST: a fill since the
        # last pass moves the gateway's position, and the ledger must hold it
        # before the two are compared.
        rep["fills"] = fills.capture(ledger, st, ib.fills())
        bad = reconcile.run(ib, ledger, st)
        rep["reconcile"] = bad
        if bad:
            rep["state"] = "reconciliation mismatch: sending stopped"
            log.error("paper_exec: reconciliation mismatch: %s", "; ".join(bad))
            return rep
        limits = limits if limits is not None else pcfg.risk_limits()
        risk = open_risk(ledger, cfg)
        for i in intents:
            res = {"intent": i.as_dict()}
            rep["results"].append(res)
            if st.killed():
                res["state"] = "killed"
                continue
            if st.pause(i.engine_id):
                res["state"] = f"paused: engine {i.engine_id}'s edge-decay pause"
                continue
            try:
                c, why = contracts.resolve(i.symbol, cfg, master)
            except contracts.Refused as exc:
                res["state"] = f"refused: {exc}"
                continue
            if c is None:
                res["state"] = f"skipped: {why}"
                continue
            why = orders.check(i)
            if why:
                res["state"] = f"refused: {why}"
                continue
            qty, why = orders.size(i, c, cfg, limits, risk, governor_view(ledger, i.engine_id))
            if qty < 1:
                res["state"] = f"refused: size 0 ({why})"
                continue
            d = describe(i, c, qty)
            res["order"] = d
            ref = f"{reconcile.REF_PREFIX}{i.engine_id}:{i.signal_id}"
            if mode != "send":
                st.log_order({"state": "dry", "intent": i.as_dict(), "order": d,
                              "multiplier": c["multiplier"], "sized_by": why})
                log.warning("paper_exec DRY: would send %s", d)
                res["state"] = "dry: built and logged, nothing sent"
                continue
            con = contracts.contract(c)
            bracket = ib.bracketOrder(d["side"], qty, i.entry, i.target, i.stop)
            ids = _send(ib, con, bracket, ref)
            st.log_order({"state": "sent", "intent": i.as_dict(), "order": d,
                          "order_ids": ids, "multiplier": c["multiplier"],
                          "sized_by": why})
            risk += orders.risk_per_contract(i, c["multiplier"]) * qty
            res["state"], res["order_ids"] = "sent", ids
        rep["state"] = "done"
        return rep
    finally:
        ib.disconnect()


def intents_from_ledger(ledger, cfg: dict) -> list[orders.Intent]:
    """The lab's pending signals on this tranche's instruments, as intents: the
    entry from the signal's params (`entry`), its stop and target."""
    names = set(cfg.get("instruments") or {}) | set(cfg.get("refused") or {})
    out = []
    for s in ledger.pending_signals():
        if str(s["instrument"]).upper() not in names:
            continue
        out.append(orders.Intent(
            engine_id=s["engine_id"], signal_id=s["id"], symbol=str(s["instrument"]).upper(),
            side=int(s["direction"]), entry=(s.get("params") or {}).get("entry"),
            stop=s.get("stop_price"), target=s.get("target_price")))
    return out
