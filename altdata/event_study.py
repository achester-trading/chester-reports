"""
The event-study utility (signal-triage Batch 16 item 91(a), round 7: "own small
module modelled on gs-quant's design, no dependency on the package: +/-N windows,
pre / post / day-0 views, cross-event averages, two-asset comparison"). Built by
A128 (6 Nov 2026) as the one utility, under item 116's close-flow ledger and item
118's divergence ledger. Batch 16 names it the engine under items 49, 52,
80(b)/90, 87 and the FOMC reaction ledger as those move onto it. Build no second
one.

EVERYTHING HERE IS ARITHMETIC ON A SERIES the caller hands in: [(ISO date,
value)], ascending, one value per session (a close). Nothing reads the store,
the network or the clock, so every figure is reproducible by hand and a gate can
seed it.

THE OFFSETS ARE SESSIONS, NOT DAYS. Offset 0 is the event's own session, which
must be in the series. Offset k is the k-th session after it in the series, and
-k the k-th before it. A holiday is simply not in the series.

  window(series, day, pre, post)  {offset: value} for -pre..+post; complete or not
  views(series, day, pre, post)   pre (-pre close to -1 close), day0 (-1 to 0),
                                  post {k: 0 close to +k close}
  forward(series, day, k)         the return from the event close to the k-th
                                  session's close, or None when it has not come
  study(series, events, horizons) per event, the forward returns at each horizon,
                                  and the cross-event average of each
  average(xs)                     n, mean, median, share negative and share
                                  positive (None-free values only)
  base_rate(series, horizons)     the same average over EVERY session in a window:
                                  what an event's figures are read against
  compare(a, b, events, horizons) two assets over the same events, side by side,
                                  with a minus b

A window that runs past the series' end is "pending": its value is None and it
is never counted in an average. No average is ever taken over a partial window.
"""

from __future__ import annotations

import math
from typing import Iterable, Optional, Sequence

Series = list[tuple[str, float]]


def _index(series: Series) -> dict[str, int]:
    return {d: i for i, (d, _) in enumerate(series)}


def position(series: Series, day: str) -> Optional[int]:
    """The event session's place in the series, or None when it is not a session
    of the series."""
    return _index(series).get(day)


def window(series: Series, day: str, pre: int, post: int) -> dict:
    """{offset: value} for offsets -pre..+post around the event session. `complete`
    is False when either end runs past the series."""
    i = position(series, day)
    if i is None:
        return {"event": day, "values": {}, "complete": False,
                "reason": f"{day} is not a session of the series"}
    vals = {k: series[i + k][1] for k in range(-pre, post + 1)
            if 0 <= i + k < len(series)}
    return {"event": day, "values": vals,
            "complete": len(vals) == pre + post + 1, "reason": None}


def _ret(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or not a:
        return None
    return b / a - 1.0


def forward(series: Series, day: str, k: int) -> Optional[float]:
    """The return from the event session's close to the k-th session's close
    after it; None when the k-th session is not in the series yet (pending)."""
    i = position(series, day)
    if i is None or i + k >= len(series) or i + k < 0:
        return None
    return _ret(series[i][1], series[i + k][1])


def views(series: Series, day: str, pre: int, post: int) -> dict:
    """gs-quant's three views of one event: `pre`, the -pre close to the -1
    close; `day0`, the -1 close to the event close; `post`, {k: the event close
    to the +k close} for k = 1..post (None where pending)."""
    w = window(series, day, pre, post)
    v = w["values"]
    return {"event": day,
            "pre": _ret(v.get(-pre), v.get(-1)) if pre >= 1 else None,
            "day0": _ret(v.get(-1), v.get(0)),
            "post": {k: _ret(v.get(0), v.get(k)) for k in range(1, post + 1)},
            "complete": w["complete"], "reason": w["reason"]}


def average(xs: Iterable[Optional[float]]) -> dict:
    """n, mean, median, share negative and share positive, over the values that
    are not None. An empty set gives n 0 and None for the rest, never a zero."""
    v = [x for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]
    if not v:
        return {"n": 0, "mean": None, "median": None, "share_negative": None,
                "share_positive": None}
    s = sorted(v)
    m = len(s) // 2
    med = s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2.0
    return {"n": len(v), "mean": sum(v) / len(v), "median": med,
            "share_negative": sum(1 for x in v if x < 0) / len(v),
            "share_positive": sum(1 for x in v if x > 0) / len(v)}


def study(series: Series, events: Sequence[str], horizons: Sequence[int],
          pre: int = 0) -> dict:
    """Per event: its forward returns at each horizon (and its `pre` view when
    asked); then the cross-event average at each horizon, pending windows left
    out and counted."""
    rows = []
    for d in events:
        r = {"event": d, "in_series": position(series, d) is not None}
        for h in horizons:
            r[h] = forward(series, d, h)
        if pre:
            r["pre"] = views(series, d, pre, 0)["pre"]
            r["day0"] = views(series, d, pre, 0)["day0"]
        rows.append(r)
    avg = {h: average(r[h] for r in rows) for h in horizons}
    pending = {h: sum(1 for r in rows if r["in_series"] and r[h] is None) for h in horizons}
    return {"rows": rows, "average": avg, "pending": pending,
            "missing": [r["event"] for r in rows if not r["in_series"]]}


def base_rate(series: Series, horizons: Sequence[int], first: str = "",
              last: str = "9999") -> dict:
    """The average at each horizon over every session in [first, last] whose
    window has closed: the unconditional figure an event study is read against."""
    days = [d for d, _ in series if first <= d <= last]
    return {h: average(forward(series, d, h) for d in days) for h in horizons}


def compare(a: Series, b: Series, events: Sequence[str],
            horizons: Sequence[int]) -> dict:
    """Two assets over the same events: each one's forward return, and a minus b,
    per event and on average (an event pending or missing in either is left out
    of that horizon's spread)."""
    rows = []
    for d in events:
        r = {"event": d}
        for h in horizons:
            fa, fb = forward(a, d, h), forward(b, d, h)
            r[h] = {"a": fa, "b": fb,
                    "spread": None if fa is None or fb is None else fa - fb}
        rows.append(r)
    avg = {h: {"a": average(r[h]["a"] for r in rows),
               "b": average(r[h]["b"] for r in rows),
               "spread": average(r[h]["spread"] for r in rows)} for h in horizons}
    return {"rows": rows, "average": avg}


def daily_change(series: Series) -> Series:
    """The close-to-close change of each session against the previous one."""
    return [(series[i][0], series[i][1] / series[i - 1][1] - 1.0)
            for i in range(1, len(series)) if series[i - 1][1]]


def ratio(a: Series, b: Series) -> Series:
    """a over b on the sessions both carry."""
    mb = dict(b)
    return [(d, v / mb[d]) for d, v in a if d in mb and mb[d]]
