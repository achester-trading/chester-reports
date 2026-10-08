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
import math
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


# THE MOBILE RULE (T2.3 item 8): every chart reads at 400 px wide. A figure is
# CHART_W inches; at 400 px a point of text is 400 / (72 * CHART_W) px, so no
# text is drawn below MIN_PX_AT_400 there -- the floor is applied to every text
# artist before saving, and the smallest is recorded for the gate.
CHART_W = 5.6
MIN_PX_AT_400 = 8.0


def legibility_floor(fig) -> float:
    """Raise any text below the floor; return the smallest text's px at 400 px."""
    from matplotlib.text import Text                            # noqa: PLC0415
    w = fig.get_size_inches()[0]
    floor_pt = MIN_PX_AT_400 * 72.0 * w / 400.0
    smallest = None
    for t in fig.findobj(Text):
        if not t.get_visible() or not str(t.get_text()).strip():
            continue
        if t.get_fontsize() < floor_pt:
            t.set_fontsize(floor_pt)
        px = t.get_fontsize() * 400.0 / (72.0 * w)
        smallest = px if smallest is None else min(smallest, px)
    return round(smallest or MIN_PX_AT_400, 2)


def _finish(fig, name: str, out_dir: Optional[str]) -> dict:
    """PNG bytes (shrunk to the cap) and the SVG written to disk."""
    plt = _plt()
    min_px = legibility_floor(fig)
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
    return {"png": png, "png_bytes": len(png), "svg_path": svg_path,
            "min_px_at_400": min_px}


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
    fig, ax = plt.subplots(figsize=(CHART_W, 3.3))
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


# ---------------------------------------------------------------------------
# THE WEEKLY'S CHARTS, W1-W6 (reporting-stack brief 3.2; T2). Same rules as the
# daily three: from the store at edition time, PNG <= 150 KB for the email and
# SVG on disk, only listed levels drawn, a caption written from the data, and a
# reason in place of a chart that cannot render. No verdicts.
# ---------------------------------------------------------------------------
def weekly_bars(daily: list[dict]) -> list[dict]:
    """Daily OHLC resampled to weeks (Monday-keyed): first open, max high, min
    low, last close. The week's observed_at is its last session."""
    out: dict[str, dict] = {}
    for b in daily:
        d = dt.date.fromisoformat(str(b["observed_at"])[:10])
        k = (d - dt.timedelta(days=d.weekday())).isoformat()
        w = out.get(k)
        if w is None:
            out[k] = {"observed_at": str(b["observed_at"])[:10], "open": b["open"],
                      "high": b["high"], "low": b["low"], "close": b["close"]}
        else:
            w.update(high=max(w["high"], b["high"]), low=min(w["low"], b["low"]),
                     close=b["close"], observed_at=str(b["observed_at"])[:10])
    return [out[k] for k in sorted(out)]


def candle_chart(cid: str, bars: list[dict], book: dict, iid: str, types: tuple,
                 title: str, window: str, name: str, out_dir: Optional[str],
                 min_bars: int = 20, tick_every: int = 20) -> dict:
    if len(bars) < min_bars:
        return {"id": cid, "unavailable": f"{len(bars)} bars stored, {min_bars} needed"}
    try:
        fig, ax = _base(title)
        _candles(ax, bars)
        lo, hi = min(b["low"] for b in bars), max(b["high"] for b in bars)
        drawn = _draw_levels(ax, _levels_of(book, iid, types), lo, hi)
        ticks = list(range(0, len(bars), tick_every))
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(bars[t]["observed_at"])[2:10] for t in ticks])
        out = _finish(fig, name, out_dir)
        lab = next((i["label"] for i in book.get("instruments") or []
                    if i["id"] == iid), iid.upper())
        return {"id": cid, "drawn": drawn, "caption": caption(lab, window, drawn),
                **out, "series": [{k: b[k] for k in ("observed_at", "open", "high",
                                                      "low", "close")} for b in bars]}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": cid, "unavailable": f"{type(exc).__name__}: {exc}"}


def w1(book: dict, daily: list[dict], name: str, out_dir: Optional[str]) -> dict:
    """Six months of daily candles with the 50- and 200-day."""
    bars = daily[-126:]
    title = (span_title("SPY", len(bars), "sessions", str(bars[0]["observed_at"]),
                        str(bars[-1]["observed_at"]), "six months")
             if bars else "SPY, six months")
    return candle_chart("W1", bars, book, "spy", ("ma_50d", "ma_200d"),
                        title, f"{len(bars)} sessions", name, out_dir, min_bars=40)


def w2(book: dict, daily: list[dict], name: str, out_dir: Optional[str]) -> dict:
    """Two years of weekly candles with the 40-week average."""
    wk = weekly_bars(daily)[-104:]
    title = (span_title("SPY in weekly bars", len(wk), "weeks",
                        str(wk[0]["observed_at"]), str(wk[-1]["observed_at"]),
                        "two years") if wk else "SPY, two years")
    return candle_chart("W2", wk, book, "spy", ("ma_40w",),
                        title, f"{len(wk)} weekly bars",
                        name, out_dir, min_bars=20, tick_every=13)


def lines_chart(cid: str, series: dict, title: str, name: str,
                out_dir: Optional[str], right: Optional[str] = None,
                min_points: int = 20) -> dict:
    """One or more dated series; `right` names one plotted on a second axis."""
    short = [k for k, v in series.items() if len(v) < min_points]
    if not series or len(short) == len(series):
        return {"id": cid, "unavailable": f"fewer than {min_points} stored points"}
    try:
        fig, ax = _base(title)
        cols = ("#2563eb", "#0d2b45", "#7c3aed", "#b3261e", "#0f766e")
        ax2 = ax.twinx() if right and right in series else None
        allx = sorted({d for v in series.values() for d, _ in v})
        pos = {d: i for i, d in enumerate(allx)}
        for (lab, pts), col in zip(series.items(), cols):
            if lab in short:
                continue
            tgt = ax2 if (ax2 is not None and lab == right) else ax
            tgt.plot([pos[d] for d, _ in pts], [v for _, v in pts], color=col,
                     linewidth=1.1, label=lab)
        ax.legend(fontsize=7, frameon=False, loc="upper left")
        if ax2 is not None:
            ax2.tick_params(labelsize=7)
            ax2.legend(fontsize=7, frameon=False, loc="upper right")
        ticks = list(range(0, len(allx), max(1, len(allx) // 6)))
        ax.set_xticks(ticks)
        ax.set_xticklabels([allx[t][2:10] for t in ticks])
        out = _finish(fig, name, out_dir)
        last = "; ".join(f"{k} {v[-1][1]:,.2f} ({v[-1][0]})"
                         for k, v in series.items() if v and k not in short)
        return {"id": cid, "drawn": [], "caption": f"{title}; {last}", **out,
                "series": {k: [{"date": d, "value": x} for d, x in v]
                           for k, v in series.items()},
                "not_drawn": short}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": cid, "unavailable": f"{type(exc).__name__}: {exc}"}


def banded_chart(cid: str, series: dict, title: str, name: str,
                 out_dir: Optional[str], min_points: int = 20) -> dict:
    """Each series in its own panel with its mean and +-1 sigma band (W4)."""
    keep = {k: v for k, v in series.items() if len(v) >= min_points}
    if not keep:
        return {"id": cid, "unavailable": f"fewer than {min_points} stored points"}
    try:
        plt = _plt()
        fig, axes = plt.subplots(len(keep), 1, figsize=(CHART_W, 1.9 * len(keep) + 0.6),
                                 squeeze=False)
        fig.suptitle(title, fontsize=9, x=0.02, ha="left", color="#0d2b45")
        stats = {}
        for ax, (lab, pts) in zip(axes[:, 0], keep.items()):
            vals = [v for _, v in pts]
            m = sum(vals) / len(vals)
            sd = (sum((v - m) ** 2 for v in vals) / max(1, len(vals) - 1)) ** 0.5
            ax.plot(range(len(vals)), vals, color="#0d2b45", linewidth=1.1)
            ax.axhline(m, color="#94a3b8", linestyle="--", linewidth=0.8)
            for y in (m + sd, m - sd):
                ax.axhline(y, color="#d97706", linestyle="--", linewidth=0.8)
            ax.set_title(lab, fontsize=8, loc="left")
            ax.tick_params(labelsize=7)
            ax.set_xticks([0, len(vals) - 1])
            ax.set_xticklabels([pts[0][0], pts[-1][0]])
            stats[lab] = {"last": vals[-1], "mean": m, "sd": sd, "n": len(vals),
                          "as_of": pts[-1][0]}
        fig.tight_layout()
        out = _finish(fig, name, out_dir)
        cap = "; ".join(f"{k}: {s['last']:,.0f} against a {s['n']}-print mean of "
                        f"{s['mean']:,.0f} (one sigma {s['sd']:,.0f}), as of "
                        f"{s['as_of']}" for k, s in stats.items())
        return {"id": cid, "drawn": [], "caption": f"{title}. {cap}", **out,
                "stats": stats, "not_drawn": sorted(set(series) - set(keep))}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": cid, "unavailable": f"{type(exc).__name__}: {exc}"}


def bars_chart(cid: str, rows: list, title: str, name: str,
               out_dir: Optional[str]) -> dict:
    """Sorted horizontal bars: the week's sector and style-pair returns (W5)."""
    if len(rows) < 3:
        return {"id": cid, "unavailable": f"{len(rows)} returns stored, 3 needed"}
    try:
        rows = sorted(rows, key=lambda r: r[1])
        plt = _plt()
        fig, ax = plt.subplots(figsize=(CHART_W, 0.24 * len(rows) + 0.9))
        ax.set_title(title, fontsize=9, loc="left", color="#0d2b45")
        ax.barh(range(len(rows)), [v for _, v in rows],
                color=[UP if v >= 0 else DOWN for _, v in rows],
                edgecolor="#0d2b45", linewidth=0.4)
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([k for k, _ in rows], fontsize=7)
        ax.axvline(0, color="#94a3b8", linewidth=0.6)
        ax.tick_params(labelsize=7)
        for i, (_, v) in enumerate(rows):
            ax.annotate(f"{v:+.2f}%", xy=(v, i), xytext=(3 if v >= 0 else -3, 0),
                        textcoords="offset points", va="center",
                        ha="left" if v >= 0 else "right", fontsize=6.5)
        out = _finish(fig, name, out_dir)
        top, bot = rows[-1], rows[0]
        return {"id": cid, "drawn": [], "caption": f"{title}; highest {top[0]} "
                f"{top[1]:+.2f}%, lowest {bot[0]} {bot[1]:+.2f}%", **out,
                "series": [{"name": k, "return_pct": v} for k, v in rows]}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": cid, "unavailable": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# THE WEEKLY'S EDITED AND NEW CHARTS (T2.2, ruled 4 Oct 2026, items 12-17).
# Every title names the count, the plain span and the date range; every panel
# with nothing stored says "not yet tracked" in place of a line.
# ---------------------------------------------------------------------------
def span_title(label: str, n: int, unit: str, first: str, last: str,
               plain: str) -> str:
    """'SPY, 126 sessions (six months), 2026-04-06 to 2026-10-02'."""
    return f"{label}, {n} {unit} ({plain}), {first[:10]} to {last[:10]}"


def _panel_grid(nrows: int, ncols: int, h: float = 2.0):
    plt = _plt()
    fig, axes = plt.subplots(nrows, ncols, figsize=(CHART_W, h * nrows + 0.7),
                             squeeze=False)
    for ax in axes.flat:
        ax.tick_params(labelsize=6.5)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.grid(axis="y", color="#e6ebef", linewidth=0.5)
    return fig, axes


def _untracked(ax, title: str, why: str = "not yet tracked") -> None:
    ax.set_title(title, fontsize=7.5, loc="left")
    ax.text(0.5, 0.5, why, ha="center", va="center", fontsize=8, color="#94a3b8",
            transform=ax.transAxes)
    ax.set_xticks([])
    ax.set_yticks([])


def dated_tick_index(n: int, k: int = 4) -> list[int]:
    """Tick positions for `n` dated points: about `k` evenly spaced, the first
    and the last. A spaced tick within half a step of the last is dropped, so
    two labels are never printed on top of each other (T2.7: B's finding)."""
    if n <= 0:
        return []
    step = max(1, n // k)
    idx = {i for i in range(0, n, step) if i == 0 or n - 1 - i >= step / 2}
    return sorted(idx | {n - 1})


def _dated_ticks(ax, dates: list, k: int = 4) -> None:
    if not dates:
        return
    idx = dated_tick_index(len(dates), k)
    ax.set_xticks(idx)
    ax.set_xticklabels([str(dates[i])[2:10] for i in idx])


def zscores(pts: list) -> list:
    """Each point's z against the whole window's mean and standard deviation."""
    vals = [v for _, v in pts]
    if len(vals) < 3:
        return []
    m = sum(vals) / len(vals)
    sd = (sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5
    return [(d, (v - m) / sd) for d, v in pts] if sd else []


def pct_band(vals: list, lo: float = 10, hi: float = 90) -> Optional[tuple]:
    if len(vals) < 20:
        return None
    s = sorted(vals)

    def q(p):
        return s[min(len(s) - 1, max(0, int(round(p / 100 * (len(s) - 1)))))]
    return q(lo), q(hi)


def w3_panel(yields: dict, hy: list, name: str, out_dir: Optional[str],
             asof: str) -> dict:
    """Item 12: 2x2 -- yields (2, 10, 30) over one year and over ten; HY OAS over
    one year and over ten with the 5- and 20-year 10th-90th percentile bands."""
    try:
        end = dt.date.fromisoformat(asof[:10])
        y1 = (end - dt.timedelta(days=365)).isoformat()
        y10 = (end - dt.timedelta(days=3653)).isoformat()
        fig, axes = _panel_grid(2, 2, 2.2)
        cols = ("#2563eb", "#0d2b45", "#7c3aed")
        drawn = {}
        for ax, since, span in ((axes[0, 0], y1, "one year"), (axes[0, 1], y10, "ten years")):
            pts_all = []
            for (lab, pts), c in zip(yields.items(), cols):
                pp = [(d, v) for d, v in pts if d >= since]
                if pp:
                    ax.plot(range(len(pp)), [v for _, v in pp], color=c, linewidth=1.0,
                            label=lab)
                    pts_all = pp if len(pp) > len(pts_all) else pts_all
            if pts_all:
                ax.set_title(span_title("Treasury yields (%)", len(pts_all), "days",
                                        pts_all[0][0], pts_all[-1][0], span),
                             fontsize=7.5, loc="left")
                _dated_ticks(ax, [d for d, _ in pts_all])
                ax.legend(fontsize=6, frameon=False)
                drawn[f"yields_{span}"] = len(pts_all)
            else:
                _untracked(ax, f"Treasury yields, {span}")
        for ax, since, span in ((axes[1, 0], y1, "one year"), (axes[1, 1], y10, "ten years")):
            pp = [(d, v) for d, v in hy if d >= since]
            if len(pp) < 5:
                _untracked(ax, f"High-yield OAS, {span}")
                continue
            ax.plot(range(len(pp)), [v for _, v in pp], color="#b3261e", linewidth=1.0)
            for yrs, alpha in ((5, 0.18), (20, 0.08)):
                start = (end - dt.timedelta(days=int(365.25 * yrs))).isoformat()
                band = pct_band([v for d, v in hy if d >= start])
                if band:
                    ax.axhspan(band[0], band[1], color="#d97706", alpha=alpha,
                               label=f"{yrs}-year 10th-90th percentile")
            ax.set_title(span_title("High-yield OAS (%)", len(pp), "days", pp[0][0],
                                    pp[-1][0], span), fontsize=7.5, loc="left")
            _dated_ticks(ax, [d for d, _ in pp])
            ax.legend(fontsize=6, frameon=False)
            drawn[f"hy_{span}"] = len(pp)
        fig.tight_layout()
        out = _finish(fig, name, out_dir)
        last = "; ".join(f"{k} {v[-1][1]:.2f}% ({v[-1][0]})" for k, v in yields.items() if v)
        cap = ("Treasury yields and high-yield OAS, one year and ten years; " + last
               + (f"; HY OAS {hy[-1][1]:.2f}% ({hy[-1][0]})" if hy else ""))
        return {"id": "W3", "drawn": [], "caption": cap, **out, "panels": drawn}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "W3", "unavailable": f"{type(exc).__name__}: {exc}"}


def z_panel(cid: str, series: dict, title: str, name: str,
            out_dir: Optional[str], ncols: int = 2, min_points: int = 20) -> dict:
    """Items 13 and 16: one small panel per series, its z-score over the window,
    the +-1 and +-2 lines; an empty series prints 'not yet tracked'."""
    try:
        keys = list(series)
        nrows = math.ceil(len(keys) / ncols)
        fig, axes = _panel_grid(nrows, ncols, 1.35)
        fig.suptitle(title, fontsize=8.5, x=0.02, ha="left", color="#0d2b45")
        stats, untracked = {}, []
        for ax, k in zip(axes.flat, keys):
            pts = series.get(k) or []
            if len(pts) < min_points:
                _untracked(ax, k)
                untracked.append(k)
                continue
            z = zscores(pts)
            if not z:
                _untracked(ax, k, "no variation stored")
                untracked.append(k)
                continue
            ax.plot(range(len(z)), [v for _, v in z], color="#0d2b45", linewidth=0.9)
            for y, c in ((0, "#94a3b8"), (1, "#d97706"), (-1, "#d97706"),
                         (2, "#b3261e"), (-2, "#b3261e")):
                ax.axhline(y, color=c, linewidth=0.5, linestyle="--" if y else "-")
            ax.set_title(f"{k}: z {z[-1][1]:+.1f} ({z[-1][0]})", fontsize=7, loc="left")
            _dated_ticks(ax, [d for d, _ in z], 2)
            stats[k] = {"z": round(z[-1][1], 2), "as_of": z[-1][0], "n": len(z)}
        for ax in list(axes.flat)[len(keys):]:
            ax.axis("off")
        fig.tight_layout(rect=(0, 0, 1, 0.96))
        out = _finish(fig, name, out_dir)
        cap = (f"{title}. " + "; ".join(f"{k} z {v['z']:+.1f} ({v['as_of']})"
                                        for k, v in stats.items())
               + (f"; not yet tracked: {', '.join(untracked)}" if untracked else ""))
        return {"id": cid, "drawn": [], "caption": cap, **out, "stats": stats,
                "not_drawn": untracked}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": cid, "unavailable": f"{type(exc).__name__}: {exc}"}


def bars_65(bars5: list) -> list:
    """5-minute bars to 65-minute bars, six per regular session, anchored at
    09:30 ET (item 14)."""
    from altdata import session                                 # noqa: PLC0415
    out: dict = {}
    for b in bars5:
        t = session.to_eastern(dt.datetime.fromisoformat(b["observed_at"]))
        mins = (t.hour * 60 + t.minute) - (9 * 60 + 30)
        if mins < 0 or mins >= 390:
            continue
        k = (t.date().isoformat(), mins // 65)
        x = out.get(k)
        vol = b.get("volume") or 0
        tp = (b["high"] + b["low"] + b["close"]) / 3
        if x is None:
            out[k] = {"session": k[0], "slot": k[1], "open": b["open"], "high": b["high"],
                      "low": b["low"], "close": b["close"], "pv": tp * vol, "v": vol}
        else:
            x.update(high=max(x["high"], b["high"]), low=min(x["low"], b["low"]),
                     close=b["close"], pv=x["pv"] + tp * vol, v=x["v"] + vol)
    return [out[k] for k in sorted(out)]


def es_overnight(es5: list, day: str) -> list[dict]:
    """ES's overnight for session `day`: 18:00 ET the evening before to the 09:30
    open, as 65-minute closes (T2.3 item 2)."""
    from altdata import session                                 # noqa: PLC0415
    d = dt.date.fromisoformat(day)
    start = dt.datetime.combine(d - dt.timedelta(days=1), dt.time(18, 0),
                                tzinfo=session._eastern_tz())
    end = dt.datetime.combine(d, dt.time(9, 30), tzinfo=session._eastern_tz())
    out: dict[int, dict] = {}
    for b in es5:
        t = session.to_eastern(dt.datetime.fromisoformat(b["observed_at"]))
        if not (start <= t < end):
            continue
        k = int((t - start).total_seconds() // (65 * 60))
        out.setdefault(k, {"slot": k, "close": b["close"], "first_open": b["open"]})
        out[k]["close"] = b["close"]
    return [out[k] for k in sorted(out)]


def es_at_open(es5: list, day: str) -> Optional[float]:
    """ES's price at the 09:30 cash open (the bar starting 09:30 ET)."""
    from altdata import session                                 # noqa: PLC0415
    for b in es5:
        t = session.to_eastern(dt.datetime.fromisoformat(b["observed_at"]))
        if t.date().isoformat() == day and (t.hour, t.minute) == (9, 30):
            return b["open"]
    return None


def w7(bars5: list, levels_by_day: dict, name: str,
       out_dir: Optional[str], sessions: int = 10, es5: Optional[list] = None) -> dict:
    """Items 14 (T2.2) and 2 (T2.3): SPY over the last ten sessions -- the cash
    hours as 65-minute candles on a shaded band, the overnight hours as a lighter
    line from ES=F scaled to SPY by the session's basis (SPY's open over ES's at
    09:30), each session's VWAP, and the flip, walls and max pain as of each
    morning across the whole 23-hour session. Without ES bars the chart is the
    cash session alone and says so."""
    b65 = bars_65(bars5)
    days = sorted({b["session"] for b in b65})[-sessions:]
    b65 = [b for b in b65 if b["session"] in days]
    if len(days) < 2:
        return {"id": "W7", "unavailable": f"{len(days)} session(s) of 5-minute bars "
                                           f"stored, 2 needed (run the 60-day backfill)"}
    try:
        fig, ax = _base(span_title("SPY, 23-hour sessions", len(days), "sessions",
                                   days[0], days[-1], "two weeks"))
        x0 = 0
        drawn, with_es = [], 0
        cols = {"flip": LEVEL_COLOURS["gamma_flip"], "call_wall": LEVEL_COLOURS["call_wall"],
                "put_wall": LEVEL_COLOURS["put_wall"], "max_pain": LEVEL_COLOURS["max_pain"]}
        ticks = []
        for d in days:
            seg = [b for b in b65 if b["session"] == d]
            on = es_overnight(es5 or [], d)
            es_open = es_at_open(es5 or [], d)
            basis = (seg[0]["open"] / es_open) if (seg and es_open) else None
            start = x0
            if on and basis:
                with_es += 1
                ax.plot(range(x0, x0 + len(on)), [o["close"] * basis for o in on],
                        color="#94a3b8", linewidth=0.9)
                x0 += len(on)
            ax.axvspan(x0 - 0.5, x0 + len(seg) - 0.5, color="#eef2ff", zorder=0)
            for i, b in enumerate(seg):
                _candles_at(ax, x0 + i, b)
            cum_pv = cum_v = 0.0
            vw = []
            for b in seg:
                cum_pv += b["pv"]
                cum_v += b["v"]
                vw.append(cum_pv / cum_v if cum_v else None)
            if vw and all(v is not None for v in vw):
                ax.plot(range(x0, x0 + len(seg)), vw, color=LEVEL_COLOURS["vwap"],
                        linewidth=0.9)
            end = x0 + len(seg)
            for k, v in (levels_by_day.get(d) or {}).items():
                if isinstance(v, (int, float)):
                    ax.hlines(v, start - 0.4, end - 0.6, color=cols.get(k, "#94a3b8"),
                              linewidth=0.9, linestyle="--")
                    drawn.append({"session": d, "type": k, "value": v})
            ax.axvline(start - 0.5, color="#cbd5e1", linewidth=0.6)
            ticks.append((x0, d[5:10]))
            x0 = end
        ax.set_xticks([t for t, _ in ticks])
        ax.set_xticklabels([lab for _, lab in ticks])
        out = _finish(fig, name, out_dir)
        cap = (f"SPY over {len(days)} sessions ({days[0]} to {days[-1]}): the cash "
               f"session in 65-minute candles (shaded), "
               + (f"the overnight from ES=F scaled to SPY by each session's basis "
                  f"({with_es} of {len(days)} sessions)" if with_es else
                  "the overnight not drawn (no ES=F bars stored)")
               + f"; VWAP per session; flip, walls and max pain as of each morning "
                 f"where stored ({len({x['session'] for x in drawn})} of {len(days)})")
        return {"id": "W7", "drawn": drawn, "caption": cap, **out,
                "overnight_sessions": with_es,
                "series": [{k: b[k] for k in ("session", "slot", "open", "high", "low",
                                               "close")} for b in b65]}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "W7", "unavailable": f"{type(exc).__name__}: {exc}"}


def _candles_at(ax, x: int, b: dict) -> None:
    up = b["close"] >= b["open"]
    col = UP if up else DOWN
    ax.vlines(x, b["low"], b["high"], color=col, linewidth=0.8)
    lo, hi = sorted((b["open"], b["close"]))
    ax.add_patch(_rect(x - 0.32, lo, 0.64, max(hi - lo, 1e-9),
                       edge=col, face="white" if up else col))


def w8(panels: dict, name: str, out_dir: Optional[str],
       yields: tuple = ("10-year yield", "30-year yield"), n: int = 126) -> dict:
    """Item 15: 2x3, 126 sessions each with the 20-, 50- and 200-day averages;
    the two yields share one percent axis."""
    try:
        fig, axes = _panel_grid(2, 3, 2.0)
        ylo = yhi = None
        for lab in yields:
            closes = [r["close"] for r in (panels.get(lab) or [])][-n:]
            if closes:
                ylo = min(closes + ([ylo] if ylo is not None else []))
                yhi = max(closes + ([yhi] if yhi is not None else []))
        stats = {}
        for ax, (lab, rows) in zip(axes.flat, panels.items()):
            closes_all = [r["close"] for r in rows]
            if len(closes_all) < 20:
                _untracked(ax, lab, f"{len(closes_all)} closes stored")
                continue
            show = rows[-n:]
            off = len(rows) - len(show)
            ax.plot(range(len(show)), [r["close"] for r in show], color="#0d2b45",
                    linewidth=0.9)
            for w, c in ((20, LEVEL_COLOURS["ma_20d"]), (50, LEVEL_COLOURS["ma_50d"]),
                         (200, LEVEL_COLOURS["ma_200d"])):
                ma = [(i - off, sum(closes_all[i - w + 1:i + 1]) / w)
                      for i in range(off, len(rows)) if i >= w - 1]
                if ma:
                    ax.plot([x for x, _ in ma], [v for _, v in ma], color=c,
                            linewidth=0.7, label=f"{w}-day")
            if lab in yields and ylo is not None:
                ax.set_ylim(ylo - 0.05, yhi + 0.05)
            d0, d1 = str(show[0]["observed_at"])[:10], str(show[-1]["observed_at"])[:10]
            ax.set_title(f"{lab}, {len(show)} sessions, {d0} to {d1}", fontsize=7,
                         loc="left")
            _dated_ticks(ax, [str(r["observed_at"])[:10] for r in show], 2)
            stats[lab] = {"last": show[-1]["close"], "as_of": d1, "n": len(show)}
        handles = axes[0, 0].get_legend_handles_labels()[0]
        if handles:
            axes[0, 0].legend(fontsize=5.5, frameon=False)
        fig.suptitle("Bitcoin, gold, the dollar, oil and the long yields: 126 sessions "
                     "(six months) with the 20-, 50- and 200-day averages",
                     fontsize=8.5, x=0.02, ha="left", color="#0d2b45")
        fig.tight_layout(rect=(0, 0, 1, 0.95))
        out = _finish(fig, name, out_dir)
        cap = ("Six markets over 126 sessions with their 20-, 50- and 200-day "
               "averages; " + "; ".join(f"{k} {v['last']:,.2f} ({v['as_of']})"
                                        for k, v in stats.items()))
        return {"id": "W8", "drawn": [], "caption": cap, **out, "stats": stats}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "W8", "unavailable": f"{type(exc).__name__}: {exc}"}


def w10(odds: dict, path_now: Optional[dict], path_week: Optional[dict],
        path_month: Optional[dict], name: str, out_dir: Optional[str]) -> dict:
    """Item 17: the watched prediction-market odds over ninety days, beside the
    fed-funds implied path today, a week ago and a month ago."""
    try:
        plt = _plt()
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(CHART_W, 3.2))
        for ax in (a1, a2):
            ax.tick_params(labelsize=6.5)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
        cols = ("#2563eb", "#0d2b45", "#7c3aed", "#b3261e", "#0f766e", "#d97706")
        alld = sorted({d for v in odds.values() for d, _ in v})
        pos = {d: i for i, d in enumerate(alld)}
        drawn = 0
        for (lab, pts), c in zip(odds.items(), cols):
            if len(pts) >= 3:
                a1.plot([pos[d] for d, _ in pts], [100 * v for _, v in pts], color=c,
                        linewidth=0.9, label=lab)
                drawn += 1
        if drawn:
            a1.set_title(span_title("Prediction-market odds (%)", len(alld), "days",
                                    alld[0], alld[-1], "ninety days"),
                         fontsize=7.5, loc="left")
            a1.legend(fontsize=5.5, frameon=False)
            _dated_ticks(a1, alld, 3)
        else:
            _untracked(a1, "Prediction-market odds, ninety days")
        paths = [(lab, pth, c) for lab, pth, c in (("today", path_now, "#0d2b45"),
                                                   ("a week ago", path_week, "#2563eb"),
                                                   ("a month ago", path_month, "#94a3b8"))
                 if pth and pth.get("tracked") and pth.get("meetings")]
        if paths:
            for lab, pth, c in paths:
                ms = pth["meetings"][:6]
                a2.plot(range(len(ms)), [m["post_pct"] for m in ms], color=c,
                        marker="o", markersize=2.5, linewidth=0.9, label=lab)
            ms = paths[0][1]["meetings"][:6]
            a2.set_xticks(range(len(ms)))
            a2.set_xticklabels([m["meeting"][2:10] for m in ms], fontsize=6)
            a2.set_title("Fed funds futures: implied rate after each meeting (%)",
                         fontsize=7.5, loc="left")
            a2.legend(fontsize=5.5, frameon=False)
        else:
            _untracked(a2, "Fed funds implied path",
                       "not yet tracked: fewer than four meetings retrievable")
        fig.tight_layout()
        out = _finish(fig, name, out_dir)
        cap = ("Prediction-market odds over ninety days, and the fed-funds implied "
               "path today, a week ago and a month ago"
               + ("" if paths else "; the futures path is not yet tracked"))
        return {"id": "W10", "drawn": [], "caption": cap, **out,
                "markets": list(odds), "paths": [pp[0] for pp in paths]}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "W10", "unavailable": f"{type(exc).__name__}: {exc}"}
