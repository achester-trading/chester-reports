"""
6b's state vector (EL-5; the Enterprise Layer change order section 3.5; the
Dealer's Hand section VI's list, as measurable variables only).

    from altdata import state_vector as sv
    vec = sv.compute(inputs)                     # pure: numbers and None
    vec = sv.gather(st, bst, evs, capture, day)  # reads the stores, as of the capture
    rows = sv.rows(vec, written_at)              # state.* observation rows

ONE VECTOR PER 6b CAPTURE: the settled 16:10 now, and the 09:45 and 12:30 once
part 2's units run. The close computes each capture's vector for its session and
stores it (instrument `SPY:<slot>`, observed on the session, available when
written). The content is as of the capture's own instant: the 5-minute bars up
to it, and every stored series read as of it.

NUMBERS AND NONE ONLY. No field holds a word: a regime, a "trend day", a "gap and
go" -- none of it. A leg whose input is not stored is None, never a guess and
never a proxy. `check()` fails a vector holding a string or a boolean.

THE FIELDS (FIELDS below holds each one's key, units and definition):
  gap_pct            the session open against the prior close, percent
  gap_fill           the share of the gap retraced by the capture, 0..1 (None
                     when there is no gap)
  or_high, or_low    the opening range: the first `opening_range_minutes` of
                     5-minute bars (None until it is complete)
  or_break           +1 the capture's last price above the range, -1 below, 0
                     inside
  vwap_rel_pct       the last price against the session VWAP to the capture
  breadth_50d        the sector-ETF proxy's share above its 50-day average
                     (calc.breadth_sector_above_50d, sample sector_etf_proxy)
  rv_pct, iv_pct, rv_iv_ratio
                     realised vol of the session's 5-minute returns to the
                     capture, annualised; SPY's own ATM 30-day IV as of the
                     capture (no VIX stand-in); their ratio
  vix3m_over_vix     the champion term-structure leg
  vix9d_over_vix     the challenger leg (Batch 9 item 52 added ^VIX9D)
  flip_dist_pct      spot against the capture's zero-gamma level, percent of spot
  net_gex_sign       +1, -1 or 0, the capture's net GEX
  net_to_gross       the capture's net-to-gross
  event_hours        hours from the capture to the next scheduled release in the
                     events table
  volume_ratio_20d   the session's volume to the capture against the mean of the
                     prior 20 sessions' volume to the same clock time
  trend_alignment    +1 the day's direction (the last price against the prior
                     close) agrees with the market-state trend dimension, -1 it
                     opposes, 0 either is flat

WHO READS IT. The close prints it as one line per capture in Mechanics; the
Weekly as one row per session in its mechanics table. NO ENGINE READS IT until
EL-12: tools/validate_dealer_block.py fails any import of this module from the
engines' packages (alpha/, alpha_proposer/).
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Any, Optional

KEY_PREFIX = "state."
SOURCE = "daily_close"
FIELDS: dict[str, tuple[str, str]] = {
    "gap_pct": ("percent_return", "the session open against the prior close, percent"),
    "gap_fill": ("fraction", "the share of the open's gap retraced by the capture"),
    "or_high": ("price", "the opening range's high (first 30 minutes of 5-minute bars)"),
    "or_low": ("price", "the opening range's low"),
    "or_break": ("ratio", "+1 the capture's last price above the opening range, -1 below, 0 inside"),
    "vwap_rel_pct": ("percent_return", "the last price against the session VWAP to the capture"),
    "breadth_50d": ("percent_share", "the sector-ETF proxy's share above its 50-day average, as of the capture"),
    "rv_pct": ("vol_pct", "realised vol of the session's 5-minute returns to the capture, annualised"),
    "iv_pct": ("vol_pct", "SPY's own ATM 30-day IV as of the capture (no VIX stand-in)"),
    "rv_iv_ratio": ("ratio", "rv_pct over iv_pct"),
    "vix3m_over_vix": ("ratio", "the champion term-structure leg, VIX3M over VIX, as of the capture"),
    "vix9d_over_vix": ("ratio", "the challenger leg, VIX9D over VIX, as of the capture"),
    "flip_dist_pct": ("percent_return", "spot against the capture's zero-gamma level, percent of spot"),
    "net_gex_sign": ("ratio", "+1, -1 or 0: the sign of the capture's net GEX"),
    "net_to_gross": ("fraction", "the capture's net-to-gross"),
    "event_hours": ("hours", "hours from the capture to the next scheduled release"),
    "volume_ratio_20d": ("ratio", "volume to the capture against the prior 20 sessions' mean to the same time"),
    "trend_alignment": ("ratio", "+1 the day's direction agrees with the trend dimension, -1 opposes, 0 flat"),
}
DEFAULTS = {"opening_range_minutes": 30, "volume_sessions": 20, "rv_min_returns": 10,
            "event_horizon_days": 14}


def key(field: str) -> str:
    return KEY_PREFIX + field


def config(cfg: Optional[dict] = None) -> dict:
    if cfg is None:
        from altdata import bars as bars_mod                    # noqa: PLC0415
        cfg = bars_mod.load_config()
    return {**DEFAULTS, **(cfg.get("state_vector") or {})}


def _sign(x: Optional[float]) -> Optional[int]:
    if x is None:
        return None
    return 1 if x > 0 else -1 if x < 0 else 0


def _r(x: Optional[float], n: int = 4) -> Optional[float]:
    return None if x is None or not math.isfinite(x) else round(float(x), n)


def _ratio(a: Optional[float], b: Optional[float]) -> Optional[float]:
    return a / b if a is not None and b not in (None, 0) else None


def _parse(ts: str) -> dt.datetime:
    t = dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def bars_to(bars: list[dict], at: str) -> list[dict]:
    """The bars that had closed by `at` (a bar's close is its start plus five
    minutes)."""
    cut = _parse(at)
    return [b for b in bars if _parse(b["observed_at"]) + dt.timedelta(minutes=5) <= cut]


def volume_to_clock(bars: list[dict], clock: dt.time) -> Optional[float]:
    """A session's volume over the bars that close by `clock` (ET)."""
    from altdata import session                                 # noqa: PLC0415
    tz = session._eastern_tz()
    vol, seen = 0.0, False
    for b in bars:
        end = (_parse(b["observed_at"]) + dt.timedelta(minutes=5)).astimezone(tz)
        if end.time() <= clock:
            vol += float(b.get("volume") or 0.0)
            seen = True
    return vol if seen else None


# ---------------------------------------------------------------------------
# The vector, from inputs already read
# ---------------------------------------------------------------------------
def compute(inp: dict, cfg: Optional[dict] = None) -> dict:
    """`inp`: bars (the session's 5-minute bars to the capture), prior_close,
    profile (the capture: spot and overall), iv_pct, breadth_50d, vix, vix3m,
    vix9d, event_hours, volume_avg (the prior sessions' mean volume to the same
    clock, or None), trend_pct (the trend dimension's percentile). Any of them
    may be missing; each field then is None."""
    c = config(cfg if cfg is not None else {})
    bars = inp.get("bars") or []
    pc = inp.get("prior_close")
    prof = inp.get("profile") or {}
    ov = prof.get("overall") or {}
    v: dict[str, Any] = {f: None for f in FIELDS}
    last = bars[-1]["close"] if bars else None
    if bars and pc:
        op = bars[0]["open"]
        gap = op - pc
        v["gap_pct"] = _r(100.0 * gap / pc)
        if gap:
            lo, hi = min(b["low"] for b in bars), max(b["high"] for b in bars)
            fill = (op - lo) / gap if gap > 0 else (hi - op) / -gap
            v["gap_fill"] = _r(min(1.0, max(0.0, fill)))
    n_or = int(c["opening_range_minutes"]) // 5
    if len(bars) >= n_or > 0:
        orb = bars[:n_or]
        oh, ol = max(b["high"] for b in orb), min(b["low"] for b in orb)
        v["or_high"], v["or_low"] = _r(oh, 2), _r(ol, 2)
        v["or_break"] = 1 if last > oh else -1 if last < ol else 0
    vol = sum(float(b.get("volume") or 0) for b in bars)
    if bars and vol > 0:
        vwap = sum((b["high"] + b["low"] + b["close"]) / 3 * float(b.get("volume") or 0)
                   for b in bars) / vol
        v["vwap_rel_pct"] = _r(100.0 * (last - vwap) / vwap)
    v["breadth_50d"] = _r(inp.get("breadth_50d"))
    rets = [math.log(bars[i]["close"] / bars[i - 1]["close"]) for i in range(1, len(bars))
            if bars[i - 1]["close"]]
    if len(rets) >= int(c["rv_min_returns"]):
        v["rv_pct"] = _r(math.sqrt(sum(r * r for r in rets) / len(rets))
                         * math.sqrt(78 * 252) * 100.0, 3)
    v["iv_pct"] = _r(inp.get("iv_pct"), 3)
    v["rv_iv_ratio"] = _r(_ratio(v["rv_pct"], v["iv_pct"]))
    v["vix3m_over_vix"] = _r(_ratio(inp.get("vix3m"), inp.get("vix")))
    v["vix9d_over_vix"] = _r(_ratio(inp.get("vix9d"), inp.get("vix")))
    spot, flip = prof.get("spot"), ov.get("gamma_flip")
    if spot and flip:
        v["flip_dist_pct"] = _r(100.0 * (spot - flip) / spot)
    v["net_gex_sign"] = _sign(ov.get("net_gex"))
    v["net_to_gross"] = _r(ov.get("net_to_gross"))
    v["event_hours"] = _r(inp.get("event_hours"), 2)
    v["volume_ratio_20d"] = _r(_ratio(vol if bars else None, inp.get("volume_avg")))
    tp = inp.get("trend_pct")
    day_dir = _sign(None if last is None or not pc else last - pc)
    trend_dir = None if tp is None else _sign(tp - 50.0)
    v["trend_alignment"] = (None if day_dir is None or trend_dir is None
                            else day_dir * trend_dir)
    return v


def check(v: dict) -> list[str]:
    """Faults: a field outside FIELDS, or a value that is not a number or None
    (a string is a label; a boolean is a verdict)."""
    out = []
    for k, x in v.items():
        if k not in FIELDS:
            out.append(f"{k}: not a state-vector field")
        elif x is not None and (isinstance(x, bool) or not isinstance(x, (int, float))):
            out.append(f"{k}: {x!r} is not a number -- the vector holds no labels")
    return out


# ---------------------------------------------------------------------------
# Reading the stores, as of the capture
# ---------------------------------------------------------------------------
def slot_of(capture: dict) -> str:
    """'1610' for the settled capture; the intraday capture's HHMM (ET) otherwise."""
    if capture.get("capture") == "settled_eod":
        return "1610"
    from altdata import session                                 # noqa: PLC0415
    t = _parse(capture["fetched_at"]).astimezone(session._eastern_tz())
    return t.strftime("%H%M")


def _latest(st, k: str, at: str, instrument: Optional[str] = None) -> Optional[float]:
    """The newest stored value of `k` knowable at `at`; None when there is none."""
    try:
        if instrument is None:
            r = st.latest_as_of(k, as_of=at)
        else:
            rs = st.as_of(k, at, instrument)
            r = rs[-1] if rs else None
    except Exception:                                           # noqa: BLE001
        return None
    return None if not r else r.get("value_num")


def gather(st, bst, evs, capture: dict, day: str, cfg: Optional[dict] = None) -> dict:
    """The vector for one capture of `day`. `bst` the bar store, `evs` the
    events store (None: event_hours is None). Every store is read as of the
    capture's own instant."""
    from altdata import bars as bars_mod, session               # noqa: PLC0415
    c = config(cfg)
    at = capture.get("fetched_at")
    out: dict[str, Any] = {"day": day, "slot": slot_of(capture), "at": at}
    inp: dict[str, Any] = {"profile": capture}
    day_bars = bars_mod.intraday(bst, "spy", day)["bars"] if bst is not None else []
    inp["bars"] = bars_to(day_bars, at)
    prev = session.previous_trading_session(dt.date.fromisoformat(day))
    prev_bars = bars_mod.intraday(bst, "spy", prev.isoformat())["bars"] if bst else []
    inp["prior_close"] = (prev_bars[-1]["close"] if prev_bars
                          else _latest(st, "yfinance.mkt_spy", at))
    inp["iv_pct"] = _latest(st, "chain.spy_atm_iv_30d", at, "SPY")
    inp["breadth_50d"] = _latest(st, "calc.breadth_sector_above_50d", at)
    for k, s in (("vix", "yfinance.mkt_vix"), ("vix3m", "yfinance.mkt_vix3m"),
                 ("vix9d", "yfinance.mkt_vix9d")):
        inp[k] = _latest(st, s, at)
    # The prior sessions' volume to the same clock.
    clock = _parse(at).astimezone(session._eastern_tz()).time()
    vols, d = [], prev
    for _ in range(int(c["volume_sessions"]) * 2):
        if len(vols) >= int(c["volume_sessions"]):
            break
        x = volume_to_clock(bars_mod.intraday(bst, "spy", d.isoformat())["bars"]
                            if bst else [], clock)
        if x:
            vols.append(x)
        d = session.previous_trading_session(d)
    inp["volume_avg"] = (sum(vols) / len(vols)
                         if len(vols) >= int(c["volume_sessions"]) else None)
    # The next scheduled release, from the events table as known at the capture.
    if evs is not None:
        try:
            last = (_parse(at) + dt.timedelta(days=int(c["event_horizon_days"]))).date()
            rel = [r for r in evs.calendar(day, last.isoformat(), as_of=at)
                   if r.get("type") == "release" and _parse(r["observed_at"]) > _parse(at)]
            if rel:
                nxt = min(_parse(r["observed_at"]) for r in rel)
                inp["event_hours"] = (nxt - _parse(at)).total_seconds() / 3600.0
        except Exception:                                       # noqa: BLE001
            pass
    try:
        import regime                                           # noqa: PLC0415
        obj = regime.latest(as_of=at, store=st) or {}
        inp["trend_pct"] = ((obj.get("dimensions") or {}).get("trend") or {}).get("percentile")
    except Exception:                                           # noqa: BLE001
        inp["trend_pct"] = None
    out["vector"] = compute(inp, c)
    return out


# ---------------------------------------------------------------------------
# Storing and printing
# ---------------------------------------------------------------------------
def rows(g: dict, written_at: str, symbol: str = "SPY") -> list[dict]:
    """One observation row per field that is not None (instrument
    '<symbol>:<slot>', observed on the session, available when written)."""
    return [{"registry_key": key(f), "instrument": f"{symbol}:{g['slot']}",
             "observed_at": g["day"], "available_at": written_at, "value": x,
             "source": SOURCE}
            for f, x in g["vector"].items() if x is not None]


def _f(x: Optional[float], fmt: str) -> str:
    if x is None:
        return "—"
    return format(int(round(x)) if fmt.endswith("d") else x, fmt)


def line(g: dict) -> str:
    """The close's one compact line for one capture: numbers, '—' for None."""
    v = g["vector"]
    s = g["slot"]
    return (f"{s[:2]}:{s[2:]}: gap {_f(v['gap_pct'], '+.2f')}% (fill "
            f"{_f(v['gap_fill'], '.2f')}); opening range {_f(v['or_low'], ',.2f')}–"
            f"{_f(v['or_high'], ',.2f')}, break {_f(v['or_break'], '+d')}; VWAP "
            f"{_f(v['vwap_rel_pct'], '+.2f')}%; breadth {_f(v['breadth_50d'], '.0f')}%; "
            f"RV/IV {_f(v['rv_iv_ratio'], '.2f')} ({_f(v['rv_pct'], '.1f')}/"
            f"{_f(v['iv_pct'], '.1f')}); VIX3M/VIX {_f(v['vix3m_over_vix'], '.3f')}, "
            f"VIX9D/VIX {_f(v['vix9d_over_vix'], '.3f')}; flip {_f(v['flip_dist_pct'], '+.2f')}%, "
            f"GEX sign {_f(v['net_gex_sign'], '+d')}, net-to-gross "
            f"{_f(v['net_to_gross'], '.2f')}; next release {_f(v['event_hours'], '.1f')} h; "
            f"volume {_f(v['volume_ratio_20d'], '.2f')}× 20d; trend alignment "
            f"{_f(v['trend_alignment'], '+d')}.")


def stored(st, day: str, cutoff: str, slot: str = "1610", symbol: str = "SPY") -> dict:
    """The vector stored for one session and slot: {field: value or None}."""
    out: dict[str, Any] = {f: None for f in FIELDS}
    for f in FIELDS:
        try:
            rs = [r for r in st.as_of(key(f), cutoff, f"{symbol}:{slot}")
                  if str(r["observed_at"])[:10] == day]
        except Exception:                                       # noqa: BLE001
            rs = []
        if rs:
            out[f] = rs[-1].get("value_num")
    return out


WEEKLY_COLUMNS = ["Session", "Gap % / fill", "OR break / VWAP %", "RV/IV · VIX3M/VIX · VIX9D/VIX",
                  "Flip % · GEX sign · NTG", "Event h · vol × 20d · trend"]


def weekly_row(day_label: str, v: dict) -> list[str]:
    """The Weekly's row for one session (six columns, the mobile rule)."""
    return [day_label,
            f"{_f(v['gap_pct'], '+.2f')} / {_f(v['gap_fill'], '.2f')}",
            f"{_f(v['or_break'], '+d')} / {_f(v['vwap_rel_pct'], '+.2f')}",
            f"{_f(v['rv_iv_ratio'], '.2f')} · {_f(v['vix3m_over_vix'], '.3f')} · "
            f"{_f(v['vix9d_over_vix'], '.3f')}",
            f"{_f(v['flip_dist_pct'], '+.2f')} · {_f(v['net_gex_sign'], '+d')} · "
            f"{_f(v['net_to_gross'], '.2f')}",
            f"{_f(v['event_hours'], '.1f')} · {_f(v['volume_ratio_20d'], '.2f')} · "
            f"{_f(v['trend_alignment'], '+d')}"]
