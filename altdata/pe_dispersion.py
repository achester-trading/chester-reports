"""
Signal-triage Batch 12, item 60.4 (ST-R6.60c; F4): the hyperscaler forward-P/E
dispersion line, printed with item 40's Monthly decomposition (the M11 chart's
sub-section).

    from altdata import pe_dispersion as pe
    rows = pe.rows(st, cutoff)
    pe.lines(rows)

F4. The forward-P/E log (the consensus logger, yf.forward_pe by symbol) starts in
2026, and no keyless source serves earlier forward P/E. So each name prints:
  forward   its latest forward P/E against its peak SINCE LOGGING BEGAN, labelled
            with that date ("forward, peak since <first logged day>")
  trailing  where stored prices and reported EPS allow: the latest close over the
            last four reported quarters' EPS, against that ratio's 2025 peak,
            labelled "trailing" (the closes yfinance.mkt_<sym>; the EPS the
            earnings writer's events, payload reported_eps)
A name whose leg cannot be computed says why. Report-only: no flag, no score.
"""

from __future__ import annotations

import json
from typing import Optional

from . import st_r5_rates as rt

FORWARD_PE = "yf.forward_pe"
PEAK_YEAR = "2025"


def names() -> list[str]:
    """The hyperscalers (config/weekly_ahead.yaml), GOOG folded into GOOGL."""
    from daily_cascade import ahead                             # noqa: PLC0415
    hs = (ahead.load_config().get("earnings") or {}).get("hyperscalers") or []
    return [s for s in dict.fromkeys(str(x).upper() for x in hs) if s != "GOOG"]


def forward(pts: list[tuple[str, float]]) -> Optional[dict]:
    pts = [(d, v) for d, v in pts if v and v > 0]
    if not pts:
        return None
    pk = max(pts, key=lambda x: x[1])
    return {"now": pts[-1][1], "now_day": pts[-1][0], "peak": pk[1], "peak_day": pk[0],
            "since": pts[0][0], "vs_peak_pct": round((pts[-1][1] / pk[1] - 1) * 100.0, 1)}


def trailing_series(closes: list[tuple[str, float]], eps: list[tuple[str, float]]
                    ) -> list[tuple[str, float]]:
    """Close over the sum of the last four reported quarters' EPS known on the
    day (a report counts from its own day); days with fewer than four, or a sum
    at or below zero, are skipped."""
    eps = sorted(eps)
    out, j, known = [], 0, []
    for d, c in closes:
        while j < len(eps) and eps[j][0] <= d:
            known.append(eps[j][1])
            j += 1
        if len(known) >= 4:
            s = sum(known[-4:])
            if s > 0:
                out.append((d, c / s))
    return out


def trailing(closes, eps) -> dict:
    ser = trailing_series(closes, eps)
    peak = [x for x in ser if x[0].startswith(PEAK_YEAR)]
    if not ser:
        return {"state": "absent", "why": "fewer than four reported quarters stored"}
    if not peak:
        return {"state": "absent", "why": f"no {PEAK_YEAR} close with four reported quarters before it"}
    pk = max(peak, key=lambda x: x[1])
    return {"state": "ok", "now": ser[-1][1], "now_day": ser[-1][0], "peak": pk[1],
            "peak_day": pk[0], "vs_peak_pct": round((ser[-1][1] / pk[1] - 1) * 100.0, 1)}


def _eps(st, sym: str, cutoff: str) -> list[tuple[str, float]]:
    try:
        cur = st.conn.execute("SELECT observed_at, payload FROM events WHERE "
                              "type='earnings' AND available_at<=?", (cutoff,))
    except Exception:                                           # noqa: BLE001
        return []
    out = {}
    for obs, payload in cur.fetchall():
        try:
            p = json.loads(payload or "{}") or {}
        except ValueError:
            continue
        if str(p.get("symbol") or "").upper() == sym and p.get("reported_eps") is not None:
            out[str(obs)[:10]] = float(p["reported_eps"])
    return sorted(out.items())


def rows(st, cutoff: str, syms: Optional[list[str]] = None) -> list[dict]:
    out = []
    for sym in syms or names():
        fwd = forward(rt._pts(st, FORWARD_PE, cutoff, sym))    # noqa: SLF001
        closes = rt._pts(st, f"yfinance.mkt_{sym.lower().replace('-', '_')}", cutoff)  # noqa: SLF001
        out.append({"symbol": sym, "forward": fwd,
                    "trailing": trailing(closes, _eps(st, sym, cutoff))})
    return out


def lines(rs: list[dict]) -> list[str]:
    out = []
    for r in rs:
        f, t = r["forward"], r["trailing"]
        fwd = (f"forward {f['now']:.1f}x, {f['vs_peak_pct']:+.1f}% against its peak "
               f"{f['peak']:.1f}x ({f['peak_day']}) since logging began ({f['since']})"
               if f else "forward: not yet logged")
        trl = (f"trailing {t['now']:.1f}x, {t['vs_peak_pct']:+.1f}% against its 2025 peak "
               f"{t['peak']:.1f}x ({t['peak_day']})" if t["state"] == "ok"
               else f"trailing: {t['why']}")
        out.append(f"{r['symbol']}: {fwd}; {trl}.")
    if out:
        out.insert(0, "Hyperscaler P/E dispersion (item 60, F4; report-only): each "
                      "name's forward P/E against its peak since the log began, and its "
                      "trailing P/E against its 2025 peak where stored prices and "
                      "reported EPS allow.")
    return out
