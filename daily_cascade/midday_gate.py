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
behind its audits, and is not built). The alert is a file in the outbox, and
it is MAILED (ruling 2 of 17 Oct 2026) by the path the heartbeat and the Weekly
already use (daily_cascade/deliver.py, the same SMTP credentials): subject
"12:30 alert: <the trigger line>", at most one message a session (a marker
beside the outbox copy), the outbox copy kept whatever the send does. No other
channel. A send failure is recorded in the alert file, never raised.

THE GATES (registered in GATES; a later order adds its own):
  yen_unwind, deval_trip  ST-10: SR-2's unwind tell on the 12:30 USDJPY quote,
                     and SR-4's tell's two tracked legs on today's fix and the
                     12:30 CNH and CNY quotes (no verdict word while a leg is
                     not tracked); daily_cascade/funding_hooks.py
  crypto_leverage    CD-9: S-3's "crypto leverage -- crowded" line, information
                     only; CLOSED, reading nothing, until config names a passing
                     S-3 ledger; daily_cascade/crypto_gate.py
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


def _vol_gate(ctx: dict) -> dict:
    from altdata import vol_event                               # noqa: PLC0415
    return vol_event.vol_gate(ctx)


def _yen_unwind(ctx: dict) -> dict:
    from . import funding_hooks                                 # noqa: PLC0415
    return funding_hooks.yen_unwind(ctx)


def _deval_trip(ctx: dict) -> dict:
    from . import funding_hooks                                 # noqa: PLC0415
    return funding_hooks.deval_trip(ctx)


def _bank_stress(ctx: dict) -> dict:
    from altdata import bank_stress                             # noqa: PLC0415
    return bank_stress.gate(ctx)


def _crypto_leverage(ctx: dict) -> dict:
    from . import crypto_gate                                   # noqa: PLC0415
    return crypto_gate.leverage_gate(ctx)


# The registry. Batch 9 item 52 adds the VIX gate (upward only); ST-10 (a43-render,
# 18 Oct 2026) adds ST-5's two tells, alert-only (daily_cascade/funding_hooks.py).
# CD-9's daily part (the a47 chain, 19 Oct 2026) adds S-3's leverage line, closed
# until the S-3 ledger passes (daily_cascade/crypto_gate.py). Batch 12 item 59 (a53,
# 20 Oct 2026, F5) adds the bank-stress gate: open only on the session a flag turns
# on (altdata/bank_stress.py); the slot still sends at most one message.
GATES: list[Callable[[dict], dict]] = [dealer_flip_cross, _vol_gate, _yen_unwind,
                                       _deval_trip, _bank_stress, _crypto_leverage]


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


def _send(subject: str, body: str) -> tuple[str, str]:
    from . import deliver                                       # noqa: PLC0415
    html = "<pre>" + body.replace("&", "&amp;").replace("<", "&lt;") + "</pre>"
    return deliver.send_html(subject, html, body)


def mail_alert(day: str, lines: list[str], d: Path,
               send: Optional[Callable[[str, str], tuple[str, str]]] = None) -> dict:
    """Mail the session's alert once. The marker is written before the send, so
    a crash mid-send cannot produce a second message; the state is returned."""
    marker = d / f"midday_{day}_1230.mailed"
    if marker.exists():
        return {"state": "already_sent", "detail": marker.read_text(encoding="utf-8")}
    subject = f"12:30 alert: {lines[0]}"
    body = "\n".join([f"{day}, 12:30 ET -- code-written; no model was called.", ""]
                     + lines)
    marker.write_text(f"{day} {subject}", encoding="utf-8")
    try:
        state, detail = (send or _send)(subject, body)
    except Exception as exc:                                    # noqa: BLE001
        state, detail = "send_failed", f"{type(exc).__name__}"
    return {"state": state, "detail": detail, "subject": subject}


def run(day: str, base_dir: Optional[str] = None, gates: Optional[list] = None,
        out_dir: Optional[Path] = None, ctx: Optional[dict] = None,
        extra: Optional[dict] = None,
        send: Optional[Callable[[str, str], tuple[str, str]]] = None,
        archive_dir: Optional[str] = None) -> dict:
    """Evaluate; write the alert only when a gate opens, then mail it once.
    Never calls a model. `extra` joins the stored context (the 12:30 quotes, the
    vol history); `send` replaces the SMTP send (the gate's fake)."""
    ctx = ctx if ctx is not None else context(day, base_dir)
    ctx = {**ctx, **(extra or {})}
    res = evaluate(ctx, gates)
    opened = [r for r in res if r["open"]]
    out = {"day": day, "gates": res, "opened": [r["id"] for r in opened],
           "alert": None, "model_called": False}
    if opened:
        d = Path(out_dir) if out_dir else alert_dir()
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"midday_{day}_1230.json"
        lines = [r["line"] for r in opened]
        rec = {"day": day, "slot": "12:30", "lines": lines, "gates": res}
        path.write_text(json.dumps(rec, indent=2, default=str), encoding="utf-8")
        out["alert"] = str(path)
        out["mail"] = mail_alert(day, lines, d, send)
        rec["mail"] = {k: v for k, v in out["mail"].items() if k != "detail"}
        path.write_text(json.dumps(rec, indent=2, default=str), encoding="utf-8")
        # RULING 4 OF 17 OCT 2026: the slot writes the withheld-drafts log when it
        # opens. The alert is unnarrated today, so `withheld` is empty and nothing
        # is written; a narrated alert's audit fills it.
        from altdata import withheld_log  # noqa: PLC0415
        withheld_log.record("midday_alert", path.name, rec.get("withheld") or [],
                            archive_dir)
    return out
