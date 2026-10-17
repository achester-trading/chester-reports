"""
The 12:30 alert-only slot's gates (6b part 2; Audit #3 section I: "the 12:30
chain capture keeps running for data and feeds an alert only; the LLM is called
only when an exception gate opens").

    from daily_cascade import midday_gate
    res = midday_gate.run("2026-10-16", base_dir)     # after the 12:30 capture

EACH GATE is a pure function of what is stored -- the session's 12:30 capture,
the morning profile (the prior session's settled 16:10) and whatever else it
declares -- returning {"id", "open": bool, "line": str, "why": str}. A gate that
cannot be evaluated is closed, with its reason. When every gate stays closed the
slot writes nothing and calls nothing. When one opens, the slot writes the
alert: the open gates' trigger lines, code-written, and nothing else; no model
is called here (a narrated alert would go through the existing narrative step,
behind its audits, and is not built). The alert is a file in the outbox; how it
reaches the operator is the operator's to decide.

THE GATES (registered in GATES; a later order adds its own):
  dealer_flip_cross  by 12:30 spot is at least `confirm_pct` (0.10%, the
                     continuation setup's confirmation) through the morning
                     zero-gamma level, and both captures' regimes pass the
                     net-to-gross gate -- a regime transition, which the
                     cadence document's Alerts row names
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Callable, Optional

from . import dealer_block


def _cfg() -> dict:
    return dealer_block.config()


def dealer_flip_cross(ctx: dict) -> dict:
    """Spot at 12:30 through the morning zero-gamma level by the confirmation
    margin, both regimes gated."""
    cfg = ctx.get("cfg") or _cfg()
    mid, morning = ctx.get("midday"), ctx.get("morning")
    gid = "dealer_flip_cross"
    if not mid or not morning:
        return {"id": gid, "open": False, "line": None,
                "why": "no 12:30 capture" if not mid else "no morning profile"}
    flip = (morning.get("overall") or {}).get("gamma_flip")
    m_spot, s0 = mid.get("spot"), morning.get("spot")
    if flip is None or not m_spot or not s0:
        return {"id": gid, "open": False, "line": None,
                "why": "no morning zero-gamma level or no spot"}
    conf = float(((cfg.get("setups") or {}).get("c_negative_gamma_continuation") or {})
                 .get("confirm_pct", 0.10)) / 100.0
    mo, mm = mid.get("overall") or {}, morning.get("overall") or {}
    gated = all(dealer_block.regime_sign(o.get("net_gex"), o.get("net_to_gross"), cfg)
                for o in (mo, mm))
    down = s0 >= flip and m_spot <= flip * (1 - conf)
    up = s0 <= flip and m_spot >= flip * (1 + conf)
    if not (down or up):
        return {"id": gid, "open": False, "line": None,
                "why": f"spot {m_spot:,.2f} not {conf * 100:.2f}% through {flip:,.2f}"}
    if not gated:
        return {"id": gid, "open": False, "line": None,
                "why": "a regime is indeterminate (net-to-gross under the gate)"}
    reg = dealer_block.regime(mo.get("net_gex"), mo.get("net_to_gross"), cfg)
    line = (f"{mid.get('symbol')} at 12:30: spot {m_spot:,.2f}, "
            f"{'down' if down else 'up'} through the morning zero-gamma level "
            f"{flip:,.2f} ({dealer_block.dist(flip, m_spot)} from spot); the 12:30 "
            f"capture reads {reg}. Inferred, not observed; OI as of prior close.")
    return {"id": gid, "open": True, "line": line, "why": "threshold crossing"}


# The registry. A later order adds its gate here (Batch 9 item 52: the VIX gate).
GATES: list[Callable[[dict], dict]] = [dealer_flip_cross]


def context(day: str, base_dir: Optional[str] = None, symbol: str = "SPY") -> dict:
    """The stored inputs every gate reads: the session's newest intraday
    capture near 12:30 and the morning profile (the prior settled capture)."""
    cfg = _cfg()
    caps = [c for c in dealer_block.captures_on(day, symbol, base_dir)
            if not c.get("error") and dealer_block.slot_of(c, cfg) == "12:30"]
    mid = max(caps, key=lambda c: c.get("fetched_at") or "") if caps else None
    prev = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
    morning = dealer_block.newest_settled(prev, symbol, base_dir)
    return {"day": day, "cfg": cfg, "midday": mid, "morning": morning}


def evaluate(ctx: dict, gates: Optional[list] = None) -> list[dict]:
    out = []
    for g in gates if gates is not None else GATES:
        try:
            out.append(g(ctx))
        except Exception as exc:                                # noqa: BLE001
            out.append({"id": getattr(g, "__name__", "gate"), "open": False,
                        "line": None, "why": f"{type(exc).__name__}: {exc}"})
    return out


def alert_dir() -> Path:
    return Path(os.environ.get("CHESTER_ALERT_DIR")
                or Path.home() / "chester-data" / "outbox" / "midday")


def run(day: str, base_dir: Optional[str] = None, gates: Optional[list] = None,
        out_dir: Optional[Path] = None, ctx: Optional[dict] = None) -> dict:
    """Evaluate; write the alert only when a gate opens. Never calls a model."""
    ctx = ctx if ctx is not None else context(day, base_dir)
    res = evaluate(ctx, gates)
    opened = [r for r in res if r["open"]]
    out = {"day": day, "gates": res, "opened": [r["id"] for r in opened],
           "alert": None, "model_called": False}
    if opened:
        d = Path(out_dir) if out_dir else alert_dir()
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"midday_{day}_1230.json"
        path.write_text(json.dumps({"day": day, "slot": "12:30",
                                    "lines": [r["line"] for r in opened],
                                    "gates": res}, indent=2, default=str),
                        encoding="utf-8")
        out["alert"] = str(path)
    return out
