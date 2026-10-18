"""
SR-1's style regime -- the one definition of the rule's arithmetic, shared by the
calibration study (tools/calibration/sr01_sr13_style.py) and the Monthly's
style-regime panel (daily_cascade/style_block.py). Signal-triage ST-8;
st-t3-calib, 18 Oct 2026.

THE RULE (docs/signal-triage-register.md, SR-1): the log growth/value total-return
ratio's z against its 10-year trend above +2, followed by a break -- the ratio
below its 40-week mean, or more than 8% off its 52-week high. Its thresholds live
in config/style_regime.yaml with the ledger that admitted them; a threshold
without its ledger is refused (tools/validate_st_t3_calib.py).

DISPLAY ONLY. The narrow flag the register grants on a passed gate is the
register's to grant: until the operator accepts the gate status (rule 31), the
panel prints the readings and no flag word, and nothing here enters a composite,
a trigger or the market-state object.
"""

from __future__ import annotations

import datetime as dt
import math
from pathlib import Path
from typing import Callable, Optional, Sequence

import yaml

CONFIG = Path(__file__).resolve().parent.parent / "config" / "style_regime.yaml"


def config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def trend_z(xs: Sequence[float]) -> Optional[float]:
    """The last point's residual from a least-squares line through xs, over the
    residuals' sample sd (n - 2): "z vs. its trend"."""
    n = len(xs)
    if n < 3:
        return None
    mt, mx = (n - 1) / 2.0, sum(xs) / n
    stt = sum((a - mt) ** 2 for a in range(n))
    b = sum((a - mt) * (x - mx) for a, x in enumerate(xs)) / stt
    a0 = mx - b * mt
    res = [x - (a0 + b * a) for a, x in enumerate(xs)]
    sd = math.sqrt(sum(r * r for r in res) / (n - 2))
    return res[-1] / sd if sd else None


def weekly_last(s: Sequence[tuple[str, float]]) -> list[tuple[str, float]]:
    """The last observation of each ISO week, dated that observation's day."""
    out: dict[tuple, tuple] = {}
    for d, v in s:
        y, w, _ = dt.date.fromisoformat(d).isocalendar()
        out[(y, w)] = (d, v)
    return [out[k] for k in sorted(out)]


def total_return(price: Sequence[tuple[str, float]],
                 dividend: dict[str, float]) -> list[tuple[str, float]]:
    """A total-return index from traded closes and the cash distributions stored
    beside them (the price writer never folds them in)."""
    out, g = [], 1.0
    for i, (d, p) in enumerate(price):
        if i:
            g *= (p + dividend.get(d, 0.0)) / price[i - 1][1]
        out.append((d, g))
    return out


def breaks(xs: Sequence[tuple[str, float]], i: int, ma: int, high: int,
           off_high: float) -> Optional[str]:
    """The break at step i, or None: below the `ma` mean, or more than
    `off_high` (a log) under the `high`-step high."""
    v = xs[i][1]
    if v < sum(x for _, x in xs[i - ma + 1:i + 1]) / ma:
        return "below the moving average"
    if v < max(x for _, x in xs[i - high + 1:i + 1]) + off_high:
        return "more than 8% off the high"
    return None


def triggers(xs: Sequence[tuple[str, float]], z_of: Callable[[int], Optional[float]],
             ma: int, high: int, arm: int, z_arm: float, off_high: float) -> list[dict]:
    """[{i, day, z_setup, break}] on a ratio series [(day, log ratio)]: armed by a
    z above z_arm for `arm` steps, fired by the first break while armed, which
    disarms it; a new z above z_arm after the trigger re-arms it."""
    out, armed_until, setup_z, last = [], -1, None, -1
    for i, (d, _) in enumerate(xs):
        z = z_of(i)
        if z is not None and z > z_arm and i > last:
            armed_until, setup_z = i + arm, z
        if i < max(ma, high) - 1 or i > armed_until:
            continue
        b = breaks(xs, i, ma, high, off_high)
        if b:
            out.append({"i": i, "day": d, "z_setup": setup_z, "break": b})
            armed_until, last = -1, i
    return out


def weekly_state(growth: Sequence[tuple[str, float]], value: Sequence[tuple[str, float]],
                 cfg: Optional[dict] = None) -> Optional[dict]:
    """The rule's reading now on two weekly total-return series: z, the distance
    from the 52-week high, the 40-week mean, whether a setup is live, whether the
    last week is a break while armed. None below the trend's minimum history."""
    r = (cfg or config())["rule"]
    g, v = dict(weekly_last(growth)), dict(weekly_last(value))
    days = sorted(set(g) & set(v))
    xs = [(d, math.log(g[d] / v[d])) for d in days]
    lo, hi = int(r["trend_weeks_min"]), int(r["trend_weeks"])
    ma, high = int(r["ma_weeks"]), int(r["high_weeks"])
    if len(xs) < max(lo, ma, high):
        return None
    off = math.log(1 - float(r["off_high_pct"]) / 100.0)

    def z_of(i):
        return trend_z([x for _, x in xs[max(0, i - hi + 1):i + 1]]) if i >= lo - 1 else None
    i = len(xs) - 1
    arm = int(r["arm_weeks"])
    zs = [z_of(k) for k in range(max(0, i - arm), i + 1)]
    trig = triggers(xs, z_of, ma, high, arm, float(r["z_arm"]), off)
    return {"day": xs[i][0], "z": zs[-1],
            "off_high_pct": 100.0 * (1 - math.exp(xs[i][1] - max(x for _, x in xs[i - high + 1:i + 1]))),
            "vs_ma_pct": 100.0 * (math.exp(xs[i][1] - sum(x for _, x in xs[i - ma + 1:i + 1]) / ma) - 1),
            "setup_live": any(z is not None and z > float(r["z_arm"]) for z in zs),
            "break_now": bool(trig and trig[-1]["i"] == i),
            "last_trigger": trig[-1]["day"] if trig else None}
