"""
The lab's book arithmetic, shared by the loops: capital per engine, cumulative
net P&L, graded returns. Reads alpha.db only.
"""

from __future__ import annotations

from typing import Optional

from . import config as acfg


def applied_weight(ledger, engine_id: str, day: str) -> Optional[float]:
    r = ledger.one("SELECT weight FROM allocations WHERE engine_id=? AND kind='applied'"
                   " AND day<=? ORDER BY day DESC LIMIT 1", (engine_id, day))
    return float(r["weight"]) if r else None


def capital(ledger, engine: dict, day: str, cfg: Optional[dict] = None) -> float:
    """The engine's capital in lab dollars: its applied weight, else its
    min_size, of the lab's notional."""
    cfg = cfg or acfg.settings()
    w = applied_weight(ledger, engine["id"], day)
    return float(cfg.get("notional_capital") or 0) * (
        w if w is not None else float(engine["min_size"]))


def cum_pnl(ledger, engine_id: str, day: str) -> float:
    """Realised net P&L graded on or before `day`, plus each position open at the
    end of `day` at its latest mark on or before it (marks are net of entry
    costs, so the two add)."""
    real = ledger.one("SELECT COALESCE(SUM(net_pnl),0) AS s FROM grades "
                      "WHERE engine_id=? AND day<=?", (engine_id, day))["s"]
    unreal = 0.0
    for p in ledger.q("SELECT id FROM positions WHERE engine_id=? AND "
                      "substr(opened_at,1,10)<=? AND (closed_at IS NULL OR "
                      "substr(closed_at,1,10)>?)", (engine_id, day, day)):
        m = ledger.one("SELECT unrealised FROM marks WHERE position_id=? AND day<=? "
                       "ORDER BY day DESC LIMIT 1", (p["id"], day))
        if m:
            unreal += float(m["unrealised"])
    return float(real) + unreal + carry_pnl(ledger, engine_id, day)


def carry_pnl(ledger, engine_id: str, day: str) -> float:
    """X-3.2's crypto rows: a closed carry's net P&L once closed on or before
    `day`; an open one's funding accrued to `day` less its entry costs (both legs
    at one notional, the basis assumed unchanged: no perp mark is stored)."""
    if not ledger.one("SELECT 1 AS x FROM sqlite_master WHERE type='table' AND "
                      "name='carry_book'"):
        return 0.0                       # a read-only open of a pre-Tranche-3 alpha.db
    real = ledger.one("SELECT COALESCE(SUM(net_pnl),0) AS s FROM carry_book WHERE "
                      "engine_id=? AND status='closed' AND closed_day<=?",
                      (engine_id, day))["s"]
    unreal = 0.0
    for c in ledger.q("SELECT id, entry_costs FROM carry_book WHERE engine_id=? AND "
                      "opened_day<=? AND (closed_day IS NULL OR closed_day>?)",
                      (engine_id, day, day)):
        acc = ledger.one("SELECT COALESCE(SUM(accrued),0) AS s FROM carry_accruals "
                         "WHERE carry_id=? AND day<=?", (c["id"], day))["s"]
        unreal += float(acc) - float(c["entry_costs"])
    return float(real) + unreal


def previous_day(ledger, engine_id: str, day: str) -> Optional[str]:
    r = ledger.one("SELECT day FROM equity WHERE engine_id=? AND day<? "
                   "ORDER BY day DESC LIMIT 1", (engine_id, day))
    return r["day"] if r else None


def pnl_on(ledger, engine_id: str, day: str) -> float:
    """The day's net P&L: cumulative today less cumulative at the last day the
    governor recorded -- idempotent on a re-run of the same day."""
    prev = previous_day(ledger, engine_id, day)
    return cum_pnl(ledger, engine_id, day) - (cum_pnl(ledger, engine_id, prev)
                                              if prev else 0.0)


def graded_returns(ledger, engine_id: str, last: Optional[int] = None) -> list[float]:
    rows = ledger.q("SELECT net_return FROM grades WHERE engine_id=? "
                    "ORDER BY day, position_id", (engine_id,))
    x = [float(r["net_return"]) for r in rows]
    return x[-last:] if last else x


def daily_returns(ledger, engine_id: str) -> dict[str, float]:
    """Each recorded day's return of the engine's equity index."""
    rows = ledger.q("SELECT day, equity FROM equity WHERE engine_id=? ORDER BY day",
                    (engine_id,))
    out, prev = {}, None
    for r in rows:
        if prev is not None and prev > 0:
            out[r["day"]] = float(r["equity"]) / prev - 1.0
        prev = float(r["equity"])
    return out
