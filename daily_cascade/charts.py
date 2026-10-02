"""
The daily close's charts: C1, C2 and C3. (reporting-stack brief 3.1-3.3, T1)

RENDERED FROM THE STORE AT EDITION TIME, never from a live fetch. Each chart is
written twice: a PNG at 2x for the email (embedded by Content-ID, at most 150 KB)
and an SVG beside the HTML edition on disk. The series and the levels behind
every chart are returned so the edition can save them and regenerate the chart.

THE CHART DRAWS ONLY LISTED LEVELS. Every horizontal line comes from the level
list (altdata/levels.py) and is returned in `drawn`, which the gate checks against
the same object the prose is audited against. Candles: up hollow, down filled,
and coloured -- so colour is never the only encoding. No arrows, no verdicts. The
caption is written by code from the level list, and doubles as the alt text. A
chart that cannot render returns its reason, which the edition prints in its
place.
"""

from __future__ import annotations

import datetime as dt
import io
from pathlib import Path
from typing import Any, Optional

MAX_PNG_BYTES = 150_000
UP, DOWN = "#1b7f4b", "#b3261e"
LEVEL_COLOURS = {"prior_close": "#5a6b7a", "vwap": "#6a3d9a", "gamma_flip": "#d97706",
                 "call_wall": "#0d7a3f", "put_wall": "#b3261e", "max_pain": "#0d2b45",
                 "ma_20d": "#2563eb", "ma_50d": "#7c3aed", "ma_200d": "#0f766e",
                 "week_high": "#64748b", "week_low": "#64748b"}


def _plt():
    import matplotlib                                           # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt                             # noqa: PLC0415
    return plt


def _candles(ax, bars: list[dict]) -> None:
    for x, b in enumerate(bars):
        up = b["close"] >= b["open"]
        col = UP if up else DOWN
        ax.vlines(x, b["low"], b["high"], color=col, linewidth=0.8)
        lo, hi = sorted((b["open"], b["close"]))
        ax.add_patch(_rect(x - 0.32, lo, 0.64, max(hi - lo, 1e-9),
                           edge=col, face="white" if up else col))


def _rect(x, y, w, h, edge, face):
    from matplotlib.patches import Rectangle                    # noqa: PLC0415
    return Rectangle((x, y), w, h, edgecolor=edge, facecolor=face, linewidth=0.8)


def _finish(fig, name: str, out_dir: Optional[str]) -> dict:
    """PNG bytes (shrunk to the cap) and the SVG written to disk."""
    plt = _plt()
    png = b""
    for dpi in (200, 160, 130, 100):
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
        png = buf.getvalue()
        if len(png) <= MAX_PNG_BYTES:
            break
    svg_path = None
    if out_dir:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        svg_path = str(Path(out_dir) / f"{name}.svg")
        fig.savefig(svg_path, format="svg", bbox_inches="tight")
    plt.close(fig)
    return {"png": png, "png_bytes": len(png), "svg_path": svg_path}


def _levels_of(book: dict, iid: str, types: tuple) -> list[dict]:
    inst = next((i for i in book.get("instruments") or [] if i["id"] == iid), None)
    return [lv for lv in (inst or {}).get("levels") or [] if lv["type"] in types]


def _draw_levels(ax, lvls: list[dict], lo: float, hi: float) -> list[dict]:
    drawn = []
    span = hi - lo
    for lv in lvls:
        v = lv["value"]
        if not (lo - 0.15 * span <= v <= hi + 0.15 * span):
            continue                                   # off the chart's range
        ax.axhline(v, color=LEVEL_COLOURS.get(lv["type"], "#94a3b8"), linewidth=0.9,
                   linestyle="--", alpha=0.9)
        ax.annotate(f"{lv['label']} {v:,.2f}", xy=(1.0, v), xycoords=("axes fraction",
                    "data"), xytext=(3, 0), textcoords="offset points", va="center",
                    fontsize=6.5, color=LEVEL_COLOURS.get(lv["type"], "#475569"))
        drawn.append({"type": lv["type"], "label": lv["label"], "value": v})
    return drawn


def _base(title: str):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7.0, 3.3))
    ax.set_title(title, fontsize=9, loc="left", color="#0d2b45")
    ax.tick_params(labelsize=7)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", color="#e6ebef", linewidth=0.6)
    return fig, ax


def caption(label: str, window: str, drawn: list[dict]) -> str:
    return (f"{label}, {window}; " + "; ".join(f"{d['label']} {d['value']:,.2f}"
                                               for d in drawn)) if drawn else \
        f"{label}, {window}"


def c1(book: dict, intraday_bars: list[dict], complete: bool, reason: Optional[str],
       name: str, out_dir: Optional[str]) -> dict:
    """The session's 5-minute candles with VWAP, prior close, flip, walls, max pain."""
    if not complete:
        return {"id": "C1", "unavailable": reason or "bars incomplete"}
    if not intraday_bars:
        return {"id": "C1", "unavailable": "no 5-minute bars stored"}
    try:
        fig, ax = _base("SPY, the session in 5-minute bars")
        _candles(ax, intraday_bars)
        lo = min(b["low"] for b in intraday_bars)
        hi = max(b["high"] for b in intraday_bars)
        drawn = _draw_levels(ax, _levels_of(book, "spy", (
            "vwap", "prior_close", "gamma_flip", "call_wall", "put_wall",
            "max_pain")), lo, hi)
        ticks = list(range(0, len(intraday_bars), 12))
        ax.set_xticks(ticks)
        ax.set_xticklabels([_et(intraday_bars[t]["observed_at"]) for t in ticks])
        out = _finish(fig, name, out_dir)
        cap = caption("SPY", f"{len(intraday_bars)} five-minute bars", drawn)
        return {"id": "C1", "drawn": drawn, "caption": cap, **out,
                "series": [{k: b[k] for k in ("observed_at", "open", "high", "low",
                                               "close")} for b in intraday_bars]}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "C1", "unavailable": f"{type(exc).__name__}: {exc}"}


def _et(iso: str) -> str:
    from altdata import session                                 # noqa: PLC0415
    return session.to_eastern(dt.datetime.fromisoformat(iso)).strftime("%H:%M")


def c2(book: dict, daily_bars: list[dict], name: str, out_dir: Optional[str]) -> dict:
    """60 daily candles with the 20- and 50-day, the week's range, the 200-day."""
    bars = daily_bars[-60:]
    if len(bars) < 20:
        return {"id": "C2", "unavailable": f"{len(bars)} daily bars stored, 20 needed"}
    try:
        fig, ax = _base("SPY, 60 sessions")
        _candles(ax, bars)
        lo, hi = min(b["low"] for b in bars), max(b["high"] for b in bars)
        drawn = _draw_levels(ax, _levels_of(book, "spy", (
            "ma_20d", "ma_50d", "ma_200d", "week_high", "week_low")), lo, hi)
        ticks = list(range(0, len(bars), 10))
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(bars[t]["observed_at"])[5:10] for t in ticks])
        out = _finish(fig, name, out_dir)
        return {"id": "C2", "drawn": drawn,
                "caption": caption("SPY", f"{len(bars)} sessions", drawn), **out,
                "series": [{k: b[k] for k in ("observed_at", "open", "high", "low",
                                               "close")} for b in bars]}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "C2", "unavailable": f"{type(exc).__name__}: {exc}"}


def c3_contradiction(cid: str, history: list[tuple[str, float]], threshold: float,
                     name: str, out_dir: Optional[str]) -> dict:
    """An open contradiction's z-score over 60 sessions, with the +-threshold band."""
    pts = history[-60:]
    if len(pts) < 5:
        return {"id": "C3", "unavailable": f"{len(pts)} stored sessions of {cid}"}
    try:
        fig, ax = _base(f"Contradiction {cid}: gap z-score, {len(pts)} sessions")
        ax.plot(range(len(pts)), [v for _, v in pts], color="#0d2b45", linewidth=1.2)
        for y in (threshold, -threshold):
            ax.axhline(y, color="#d97706", linestyle="--", linewidth=0.9)
        ax.axhline(0, color="#94a3b8", linewidth=0.6)
        ticks = list(range(0, len(pts), 10))
        ax.set_xticks(ticks)
        ax.set_xticklabels([pts[t][0][5:10] for t in ticks])
        out = _finish(fig, name, out_dir)
        return {"id": "C3", "drawn": [], "kind": "contradiction",
                "caption": f"{cid}: z {pts[-1][1]:+.2f} on {pts[-1][0]}, "
                           f"threshold ±{threshold:g}, {len(pts)} sessions",
                **out, "series": [{"session": d, "z": v} for d, v in pts]}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "C3", "unavailable": f"{type(exc).__name__}: {exc}"}


def c3_rates(series: dict[str, list[tuple[str, float]]], name: str,
             out_dir: Optional[str]) -> dict:
    """The 2-, 10- and 30-year over 60 sessions (Plumbing deep)."""
    if not series or any(len(v) < 5 for v in series.values()):
        return {"id": "C3", "unavailable": "fewer than 5 stored yields in a tenor"}
    try:
        fig, ax = _base("Treasury yields, 60 sessions (%)")
        for (label, pts), col in zip(series.items(), ("#2563eb", "#0d2b45", "#7c3aed")):
            pts = pts[-60:]
            ax.plot(range(len(pts)), [v for _, v in pts], color=col, linewidth=1.2,
                    label=label)
        ax.legend(fontsize=7, frameon=False)
        out = _finish(fig, name, out_dir)
        last = ", ".join(f"{k} {v[-1][1]:.2f}% ({v[-1][0]})" for k, v in series.items())
        return {"id": "C3", "drawn": [], "kind": "rates",
                "caption": f"Treasury yields, 60 sessions; {last}", **out,
                "series": {k: [{"date": d, "value": x} for d, x in v[-60:]]
                           for k, v in series.items()}}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "C3", "unavailable": f"{type(exc).__name__}: {exc}"}


def unavailable_line(chart: dict) -> str:
    return f"chart unavailable: {chart.get('unavailable')}"
