"""
The contract: the config's instruments only (MES in this tranche), each through
the Security Master's ibkr_conid. A refused symbol (ES) is refused by contract;
an instrument the Master does not hold, or holds without a conid, is skipped and
named -- a conid is never guessed (A93's rule).
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Optional


class Refused(ValueError):
    pass


def resolve(symbol: str, cfg: dict, master=None) -> tuple[Optional[dict], str]:
    """({symbol, conid, multiplier, exchange, currency, sm_id}, why) or (None, why)."""
    sym = str(symbol or "").upper()
    refused = {str(k).upper(): v for k, v in (cfg.get("refused") or {}).items()}
    if sym in refused:
        raise Refused(str(refused[sym]))
    spec = (cfg.get("instruments") or {}).get(sym)
    if spec is None:
        raise Refused(f"{sym} is not an instrument of this tranche "
                      f"({', '.join(cfg.get('instruments') or {})} only)")
    if master is None:
        from altdata.security_master import Master             # noqa: PLC0415
        master = Master()
    try:
        e = master.resolve(sym, str(spec.get("lookup_scheme") or "ticker"))
    except Exception as exc:                                    # noqa: BLE001
        return None, f"{sym}: no Security Master entry ({type(exc).__name__}: {exc})"
    if e.get("restricted"):
        raise Refused(f"{sym} ({e.get('id')}) is restricted")
    conid = (e.get("identifiers") or {}).get("ibkr_conid")
    if conid in (None, ""):
        return None, f"{sym} ({e.get('id')}) has no ibkr_conid in the Security Master"
    try:
        conid = int(conid)
    except (TypeError, ValueError):
        return None, f"{sym} ({e.get('id')}) has an unreadable ibkr_conid"
    return {"symbol": sym, "conid": conid, "sm_id": e.get("id"),
            "multiplier": float(spec.get("multiplier") or 1),
            "exchange": spec.get("exchange"), "currency": spec.get("currency")}, \
        str(e.get("id"))


def contract(c: dict):
    """The request's contract by conid (IBKR fills the rest)."""
    try:
        from ib_async import Contract                          # noqa: PLC0415
        return Contract(conId=int(c["conid"]), exchange=c.get("exchange") or "SMART")
    except ImportError:
        return SimpleNamespace(conId=int(c["conid"]), exchange=c.get("exchange") or "SMART")
