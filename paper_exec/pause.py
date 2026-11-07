"""
THE EDGE-DECAY PAUSE (D43, ruled 31 Oct 2026; the assessment's section 4).

Per engine, over its last `n` (20) CLOSED paper trades -- positions opened by a
source='paper_exec' fill and graded by fills.capture, so their net_return is the
lab's own unit (net over notional):

  paper mean        the mean net_return of those trades, with its sd
  backtest mean     engines.validated_metrics.expectancy -- the harness's
                    expectancy per trade after costs, the figure the engine's
                    validation was granted on (alpha/validate.py), never refitted
  backtest SE       validated_metrics.sd / sqrt(validated_metrics.n_signals)
  shortfall         paper mean - backtest mean
  SE                sqrt(sd_paper^2 / n + backtest SE^2): the standard error of
                    the difference, so neither the paper sample's noise nor the
                    backtest's is ignored
  z                 shortfall / SE

It TRIPS at n >= 20 and z <= -2.0 (config/paper_exec.yaml `decay`): the pause
is written to the state directory with its figures, the executor sends nothing
for that engine, and the status command prints it. Below 20 it reads
"accruing (n=k)" and never trips. It NEVER CLEARS ITSELF: a later good run
changes nothing; only the operator's resume (python -m paper_exec resume
--engine X --reason "...", denied to sessions) lifts it, and the resume is
recorded with its reason. Open positions keep their resting brackets: a pause
stops new entries, never forces a flat.
"""

from __future__ import annotations

import math
from typing import Optional

from .state import State, now


def paper_returns(ledger, engine_id: str, n: int) -> list[float]:
    rows = ledger.q(
        "SELECT g.net_return FROM grades g JOIN positions p ON p.id = g.position_id "
        "JOIN fills f ON f.id = p.entry_fill_id WHERE g.engine_id=? AND "
        "f.source='paper_exec' AND p.status='closed' ORDER BY p.closed_at DESC, p.id DESC "
        "LIMIT ?", (engine_id, int(n)))
    return [float(r["net_return"]) for r in rows]


def figures(ledger, engine_id: str, cfg: dict) -> dict:
    """The comparison, whatever it decides."""
    d = cfg.get("decay") or {}
    need, zline = int(d.get("n") or 20), float(d.get("z") or 2.0)
    rs = paper_returns(ledger, engine_id, need)
    eng = ledger.engine(engine_id) or {}
    vm = eng.get("validated_metrics") or {}
    out = {"engine": engine_id, "n": len(rs), "need": need, "z_line": -zline,
           "fields": "engines.validated_metrics.expectancy, .sd, .n_signals"}
    if len(rs) < need:
        return {**out, "state": f"accruing (n={len(rs)})"}
    try:
        bt, bsd, bn = float(vm["expectancy"]), float(vm["sd"]), int(vm["n_signals"])
    except (KeyError, TypeError, ValueError):
        return {**out, "state": "no backtest record (validated_metrics) to compare"}
    mean = sum(rs) / len(rs)
    sd = math.sqrt(sum((r - mean) ** 2 for r in rs) / (len(rs) - 1)) if len(rs) > 1 else 0.0
    bse = bsd / math.sqrt(bn) if bn > 0 else 0.0
    se = math.sqrt(sd ** 2 / len(rs) + bse ** 2)
    short = mean - bt
    z = short / se if se > 0 else (0.0 if short == 0 else math.copysign(math.inf, short))
    return {**out, "paper_mean": mean, "paper_sd": sd, "backtest_mean": bt,
            "backtest_se": bse, "se": se, "shortfall": short, "z": z,
            "state": "trip" if z <= -zline else "within"}


def evaluate(ledger, state: State, engine_id: str, cfg: dict) -> dict:
    """Trip the pause when the figures say so; an existing pause is kept as it
    is, whatever today's figures read."""
    have = state.pause(engine_id)
    f = figures(ledger, engine_id, cfg)
    if have:
        return {**f, "paused": True, "since": have.get("at")}
    if f["state"] == "trip":
        state.set_pause(engine_id, f)
        return {**f, "paused": True, "since": now()}
    return {**f, "paused": False}


def resume(state: State, engine_id: str, reason: str) -> Optional[dict]:
    """The operator's resume: the pause file goes, the resume is recorded."""
    if not reason or not reason.strip():
        raise ValueError("a resume carries the operator's reason")
    have = state.pause(engine_id)
    if not have:
        return None
    (state.root / f"pause-{engine_id}.json").unlink()
    state._append("resumed.jsonl", {"at": now(), "engine": engine_id,          # noqa: SLF001
                                    "reason": reason.strip(), "pause": have})
    return have
