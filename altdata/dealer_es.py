"""
ST-R6.45c: the dealer levels in ES (6b part 3; Batch 6 item 45, ruled 15 Oct
2026: "the conversion of dealer levels to ES waits for the 6b engine").

    from altdata import dealer_es
    conv = dealer_es.convert(profile, es_price, ratio_history, contract="ESZ6")
    conv["row"]        # the ES block's dealer row, in place of
                       # "dealer levels in ES: after the 6b engine"

THE METHOD. The engine's levels are SPY's (its SPX Greeks stay deferred behind
the solver gate), so each level is carried to ES through ONE same-minute ratio:
ES (the front month, the 5-minute bar closing at 16:00 ET) over SPY's spot in
the settled 16:10 profile. That ratio is SPX/SPY scale times the front month's
basis -- carry and dividends to expiry -- in one number, so no basis is modelled
separately. Front month only, the contract the ES block records each morning
(item 45's roll record) printed beside it.

THE ERROR BAND. The ratio is not constant: SPY's dividend timing and the basis
decay move it. The band is two standard deviations of the ratio's own daily
relative change over the prior 20 sessions, applied to each converted level and
printed in points. The method and the band print ONCE per edition (`note`).

Read-only against the ES block's config: nothing here writes, and the block's
own windows, levels and ledger are untouched.
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Optional

LEVELS = (("gamma_flip", "zero-gamma"), ("call_wall_otm", "OTM call wall"),
          ("put_wall_otm", "OTM put gamma wall"), ("peak_abs_gex_strike", "peak-gamma strike"),
          ("max_pain", "max pain"))
BAND_SESSIONS = 20
BAND_SIGMAS = 2.0


def ratio_band(history: list[float], n: int = BAND_SESSIONS) -> Optional[float]:
    """Two standard deviations of the ratio's daily relative change over the
    prior n sessions, as a fraction; None under five changes."""
    h = [x for x in history if x][-(n + 1):]
    ch = [b / a - 1.0 for a, b in zip(h, h[1:])]
    if len(ch) < 5:
        return None
    m = sum(ch) / len(ch)
    return BAND_SIGMAS * math.sqrt(sum((c - m) ** 2 for c in ch) / (len(ch) - 1))


def convert(profile: dict, es_price: Optional[float], history: list[float],
            contract: Optional[str] = None) -> dict:
    """Each SPY level carried to ES through the same-minute ratio, with its band."""
    spot = (profile or {}).get("spot")
    if not es_price or not spot:
        return {"row": "dealer levels in ES: no same-minute ES price or SPY profile "
                       "for the session", "levels": {}}
    r = es_price / spot
    band = ratio_band(history)
    o = profile.get("overall") or {}
    levels = {}
    for key, lab in LEVELS:
        v = profile.get("max_pain") if key == "max_pain" else o.get(key)
        if v is None:
            continue
        es = v * r
        levels[key] = {"label": lab, "spy": v, "es": es,
                       "band_pts": es * band if band is not None else None}
    parts = [f"{x['label']} {x['es']:,.2f}"
             + (f" (±{x['band_pts']:.1f})" if x["band_pts"] is not None else "")
             for x in levels.values()]
    head = f"Dealer levels in ES ({contract or 'front month'}): "
    row = head + ("; ".join(parts) if parts else "none in range") + \
        ". Inferred, not observed."
    note = (f"ES conversion: each SPY level times one same-minute ratio, the ES front "
            f"month's 16:00 bar over SPY's settled spot ({r:.4f}; scale and basis in "
            f"one number). Band: two standard deviations of the ratio's daily change "
            f"over {BAND_SESSIONS} sessions"
            + (f" (±{band * 100:.2f}%)." if band is not None else
               ", not yet computable (fewer than five changes stored)."))
    return {"ratio": r, "band": band, "levels": levels, "row": row, "note": note,
            "contract": contract}


def es_at(bars: list[dict], day: str, et_minute: str = "16:00") -> Optional[float]:
    """The close of the 5-minute ES bar ending at `et_minute` ET on `day`."""
    from . import session                                       # noqa: PLC0415
    for b in bars:
        t = session.to_eastern(b["observed_at"])
        end = (t + dt.timedelta(minutes=5)).strftime("%H:%M")
        if t.date().isoformat() == day and end == et_minute:
            return float(b["close"])
    return None


def ratio_history(es_bars: list[dict], spy_closes: dict[str, float],
                  sessions: list[str]) -> list[float]:
    """The same-minute ratio on each prior session where both are stored."""
    out = []
    for d in sessions:
        es = es_at(es_bars, d)
        if es and spy_closes.get(d):
            out.append(es / spy_closes[d])
    return out
