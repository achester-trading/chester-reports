"""
The Monthly's charts, M1-M9. (reporting-stack brief 3.1-3.4; Reader's Guide,
Appendix A; T3 second half)

THE WEEKLY'S MECHANICS, AT THE MONTHLY'S SPANS. Every chart is drawn by the
Weekly's own primitives (daily_cascade.charts): rendered from the store at
edition time and never from a live fetch; a PNG at 2x for the email, at most
150 KB and embedded by Content-ID; an SVG beside the HTML edition on disk; the
mobile rule (no text below 8 px at 400 px wide); a title that names the count,
the plain span and the date range; a caption written by code, which is also the
alt text; and "chart unavailable: <reason>" in place of a chart that cannot
render. No verdicts, no arrows.

ONE LEVEL LIST. M1 and M2 draw levels ONLY from the level list the tape's prose
is audited against (`book`, altdata/levels.py at the month-end session): the
40-week on M1, the 10- and 20-month on M2. What each chart drew is returned in
`drawn`, and the gate holds it to that list. M3 draws the stored per-session
scorecard (the flip and max pain each morning), which is what the Mechanics
prose is held to.

    M0  SPY, three months of daily candles, the 50- and 200-day     The tape
    M1  SPY, three years of weekly candles, the 40-week average,
        and the drawdown from the high                            The tape
    M2  SPY, ten years of monthly candles, the 10- and 20-month,
        and the drawdown from the high                            The tape
    M3  the dealer retrospective: the month's closes against the
        morning flip and max pain, shaded by gamma regime          Mechanics
    M4  the 10-year yield and the ACM 10-year term premium, five
        years                                                      Plumbing
    M5  the high-yield spread over twenty years, its percentiles
        marked and the latest's own                                Plumbing
    M6  every positioning series' current z over two years, ranked
        in one bar chart (T3.1 item 11; was ten small panels)     Positioning
    M7  breakevens at the month's start against its end          What's priced
    M10 the fed-funds futures' implied path, month start
        against month end (T3.1 item 12: each beside its block)   What's priced
    M8  the scenario weights by edition, and their Brier           Ahead
    M9  Book Z (cash, SPY, 60/40) against the paper account's NAV,
        indexed to 100 since the start date                        The book

The cap is the Monthly's chart budget (10); a fired depth trigger lifts it by
one, as on every cadence.

T3.1 (ruled 9 Oct 2026): M0 is new and prints first -- daily, then weekly, then
monthly (item 6); M1 carries the "% from high" underlay M2 has (item 5); M6 is
one ranked z chart (item 11); M7's two panels are two charts, M7 and M10, each
beside its block in What's priced (item 12).

THE CAP HOLDS ON WHAT PRINTS. Eleven charts are planned; the Monthly's cap is 12
from 9 Oct 2026 (T3.1 ruling; it was 10). M8 counts once scenario set #1 exists:
while the ledger holds no monthly_macro weight it prints "not yet: scenario set
#1" and is not drawn. Should more than the cap ever render, the ones first in
DROP_ORDER are set aside as the fallback, each printing "not printed: over the
Monthly's cap of N charts" in its place -- M8 first.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import re
from typing import Optional

from daily_cascade import charts as ch

log = logging.getLogger("monthly_macro.charts")

ORDER = ("M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M10", "M8", "M9")
DROP_ORDER = ("M8", "M9", "M3", "M2", "M5", "M4", "M6", "M10", "M7", "M1", "M0")
# Where each chart prints: (section id, sub-section title or None).
PLACE = {"M0": ("tape", None), "M1": ("tape", None), "M2": ("tape", None),
         "M3": ("mechanics", None),
         # Under the yields & spreads bucket's paragraph (T3.1 item 8): matched by
         # the sub-section's `bucket` (config monthly_plumbing_buckets.charts).
         "M4": ("plumbing", "yields"), "M5": ("plumbing", "yields"),
         "M6": ("positioning", None),
         # Beside their blocks in What's priced (T3.1 item 12), by `bucket`.
         "M7": ("priced", "breakevens"), "M10": ("priced", "fomc"),
         "M8": ("ahead", "Scenarios, and what would change our mind"),
         "M9": ("book", None)}
LONG_FRAME_TYPES = {"M1": ("ma_40w",), "M2": ("ma_10m", "ma_20m")}
DAILY_TYPES = ("ma_50d", "ma_200d")
BREAKEVENS = (("fred.breakeven_5y", "5-year"), ("fred.breakeven_10y", "10-year"),
              ("fred.breakeven_5y5y", "5y5y forward"))


def cap_of(ed: dict) -> int:
    """The Monthly's chart cap (the budget's); a fired trigger lifts it by one."""
    cap = int((ed.get("budget") or {}).get("charts") or 10)
    if any(s.get("depth_reason") for s in ed.get("sections") or []):
        cap += 1
    return cap


def plan(ed: dict) -> list[str]:
    """Every chart in ORDER; the cap is held on what renders (hold_cap)."""
    del ed
    return list(ORDER)


def hold_cap(charts: dict, cap: int) -> list[str]:
    """Set aside rendered charts, first in DROP_ORDER first, until at most
    `cap` render. Returns the ids set aside."""
    out = []
    for cid in DROP_ORDER:
        if sum(1 for c in charts.values() if not c.get("unavailable")) <= cap:
            break
        c = charts.get(cid)
        if c and not c.get("unavailable"):
            charts[cid] = {"id": cid, "title": c.get("title"),
                           "unavailable": f"not printed: over the Monthly's cap of "
                                          f"{cap} charts"}
            out.append(cid)
    return out


# ---------------------------------------------------------------------------
# Resampling
# ---------------------------------------------------------------------------
def monthly_bars(daily: list[dict]) -> list[dict]:
    """Daily OHLC to calendar months: first open, max high, min low, last close.
    The month's observed_at is its last session."""
    out: dict[str, dict] = {}
    for b in daily:
        k = str(b["observed_at"])[:7]
        m = out.get(k)
        if m is None:
            out[k] = {"observed_at": str(b["observed_at"])[:10], "open": b["open"],
                      "high": b["high"], "low": b["low"], "close": b["close"]}
        else:
            m.update(high=max(m["high"], b["high"]), low=min(m["low"], b["low"]),
                     close=b["close"], observed_at=str(b["observed_at"])[:10])
    return [out[k] for k in sorted(out)]


def drawdowns(bars: list[dict]) -> list[float]:
    """Each bar's close against the highest close up to it, in percent."""
    peak, out = None, []
    for b in bars:
        peak = b["close"] if peak is None else max(peak, b["close"])
        out.append(100.0 * (b["close"] / peak - 1.0) if peak else 0.0)
    return out


def spaced_ticks(ax, dates: list, k: int = 5) -> None:
    """The shared tick positions (daily_cascade.charts.dated_tick_index: about k
    spaced, the first and the last, none crowding the last), labelled by month
    rather than the Weekly's day: a ten-year span reads by year and month."""
    if not dates:
        return
    idx = ch.dated_tick_index(len(dates), k)
    ax.set_xticks(idx)
    ax.set_xticklabels([str(dates[i])[:7] for i in idx])


def _plain_span(n: int, want: int, unit: str, plain: str) -> str:
    return plain if n >= want else f"{plain} asked; the store holds {n} {unit}"


# ---------------------------------------------------------------------------
# M1, M2: the long frame
# ---------------------------------------------------------------------------
def _candles_log(cid: str, bars: list[dict], book: dict, title: str,
                 window: str, name: str, out_dir: Optional[str], ax=None,
                 fig=None, tick_every: int = 13) -> dict:
    own = ax is None
    if own:
        fig, ax = ch._base(title)
    ch._candles(ax, bars)
    lo, hi = min(b["low"] for b in bars), max(b["high"] for b in bars)
    # A logarithmic price axis beyond two years (brief 3.1), labelled in plain
    # prices rather than powers of ten.
    if lo > 0:
        from matplotlib.ticker import FuncFormatter             # noqa: PLC0415
        ax.set_yscale("log")
        plain = FuncFormatter(lambda v, _: f"{v:,.0f}")
        ax.yaxis.set_major_formatter(plain)
        ax.yaxis.set_minor_formatter(plain)
    drawn = ch._draw_levels(ax, ch._levels_of(book or {}, "spy",
                                              LONG_FRAME_TYPES[cid]), lo, hi)
    _unstack_level_labels(ax)
    ticks = list(range(0, len(bars), tick_every))
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(bars[t]["observed_at"])[:7] for t in ticks])
    return {"drawn": drawn, "fig": fig, "ax": ax}


def _unstack_level_labels(ax, min_gap_px: float = 11.0) -> None:
    """The level labels at the right edge, pushed apart where two levels sit so
    close that their labels would print over each other (the mobile rule is about
    legibility, and two labels in one place are neither legible)."""
    labels = [t for t in ax.texts if getattr(t, "xyann", None) == (3, 0)]
    if len(labels) < 2:
        return
    tf = ax.transData
    ys = sorted(((tf.transform((0, t.xy[1]))[1], t) for t in labels),
                key=lambda x: x[0])
    placed = []
    for y, t in ys:
        shift = 0.0
        if placed and y - placed[-1] < min_gap_px:
            shift = placed[-1] + min_gap_px - y
        placed.append(y + shift)
        # Offset points ~ pixels at the figure's dpi / 72; near enough to part them.
        t.xyann = (3, shift * 72.0 / ax.figure.dpi)


def m0(book: dict, daily: list[dict], name: str, out_dir: Optional[str]) -> dict:
    """Three months of daily candles with the 50- and 200-day averages, from the
    level list (T3.1 item 6): the first of the tape's three frames."""
    bars = daily[-63:]
    title = (ch.span_title("SPY in daily bars", len(bars), "sessions",
                           str(bars[0]["observed_at"]), str(bars[-1]["observed_at"]),
                           _plain_span(len(bars), 63, "sessions", "three months"))
             if bars else "SPY in daily bars, three months")
    r = ch.candle_chart("M0", bars, book or {}, "spy", DAILY_TYPES, title,
                        f"{len(bars)} daily bars", name, out_dir, min_bars=20,
                        tick_every=15)
    if not r.get("unavailable"):
        r["title"] = title
    return r


def _with_drawdown(cid: str, bars: list[dict], book: dict, title: str, unit: str,
                   name: str, out_dir: Optional[str], tick_every: int) -> dict:
    """Candles on a log axis with the long-frame levels, over an underlay of
    each bar's close against the highest close before it -- M2's construction,
    which M1 shares (T3.1 item 5)."""
    plt = ch._plt()
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(ch.CHART_W, 4.4), sharex=True,
                                  gridspec_kw={"height_ratios": [3, 1]})
    ax.set_title(title, fontsize=9, loc="left", color="#0d2b45")
    for a in (ax, ax2):
        a.tick_params(labelsize=7)
        for side in ("top", "right"):
            a.spines[side].set_visible(False)
    r = _candles_log(cid, bars, book, title, f"{len(bars)} {unit}", name,
                     out_dir, ax=ax, fig=fig, tick_every=tick_every)
    dd = drawdowns(bars)
    ax2.fill_between(range(len(dd)), dd, 0, color=ch.DOWN, alpha=0.35,
                     linewidth=0)
    ax2.plot(range(len(dd)), dd, color=ch.DOWN, linewidth=0.8)
    ax2.set_ylabel("From the high, %", fontsize=7)
    fig.tight_layout()
    out = ch._finish(fig, name, out_dir)
    worst = min(range(len(dd)), key=lambda i: dd[i])
    cap = (ch.caption("SPY", f"{len(bars)} {unit}", r["drawn"])
           + f"; drawdown from the high {dd[-1]:+.1f}% at "
             f"{bars[-1]['observed_at']}, deepest {dd[worst]:+.1f}% at "
             f"{bars[worst]['observed_at']}")
    return {"id": cid, "title": title, "drawn": r["drawn"], "caption": cap,
            **out, "drawdown_pct": round(dd[-1], 2),
            "series": [{k: b[k] for k in ("observed_at", "open", "high", "low",
                                           "close")} for b in bars]}


def m1(book: dict, daily: list[dict], name: str, out_dir: Optional[str]) -> dict:
    wk = ch.weekly_bars(daily)[-156:]
    if len(wk) < 20:
        return {"id": "M1", "unavailable": f"{len(wk)} weekly bars stored, 20 needed"}
    try:
        title = ch.span_title("SPY in weekly bars", len(wk), "weeks",
                              wk[0]["observed_at"], wk[-1]["observed_at"],
                              _plain_span(len(wk), 156, "weeks", "three years"))
        return _with_drawdown("M1", wk, book, title, "weekly bars", name, out_dir,
                              tick_every=26)
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "M1", "unavailable": f"{type(exc).__name__}: {exc}"}


def m2(book: dict, daily: list[dict], name: str, out_dir: Optional[str]) -> dict:
    mo = monthly_bars(daily)[-120:]
    if len(mo) < 12:
        return {"id": "M2", "unavailable": f"{len(mo)} monthly bars stored, 12 needed"}
    try:
        title = ch.span_title("SPY in monthly bars", len(mo), "months",
                              mo[0]["observed_at"], mo[-1]["observed_at"],
                              _plain_span(len(mo), 120, "months", "ten years"))
        return _with_drawdown("M2", mo, book, title, "monthly bars", name, out_dir,
                              tick_every=24)
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "M2", "unavailable": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# M3: the dealer retrospective
# ---------------------------------------------------------------------------
def m3(sessions: list[dict], name: str, out_dir: Optional[str]) -> dict:
    rows = [r for r in sessions if r.get("close") is not None]
    if len(rows) < 5:
        return {"id": "M3", "unavailable": f"{len(rows)} scored sessions with a close "
                                           f"stored, 5 needed"}
    try:
        title = ch.span_title("SPY closes against the morning flip and max pain",
                              len(rows), "sessions", rows[0]["session"],
                              rows[-1]["session"], "the month")
        fig, ax = ch._base(title)
        x = list(range(len(rows)))
        for i, r in enumerate(rows):
            neg = r.get("gamma_regime") == "negative"
            # Shading AND hatching, so the regime is never colour alone.
            ax.axvspan(i - 0.5, i + 0.5, color="#fde2e1" if neg else "#e3f2e8",
                       hatch="///" if neg else None, alpha=0.6, linewidth=0)
        ax.plot(x, [r["close"] for r in rows], color="#0d2b45", linewidth=1.2,
                marker="o", markersize=2.5, label="close")
        fx = [(i, r["flip_morning"]) for i, r in enumerate(rows)
              if r.get("flip_morning") is not None]
        mx = [(i, r["max_pain"]) for i, r in enumerate(rows)
              if r.get("max_pain") is not None]
        if fx:
            ax.plot([a for a, _ in fx], [b for _, b in fx], linestyle="none",
                    marker="_", markersize=7, color=ch.LEVEL_COLOURS["gamma_flip"],
                    label="morning flip")
        if mx:
            ax.plot([a for a, _ in mx], [b for _, b in mx], linestyle="none",
                    marker="x", markersize=3.5, color=ch.LEVEL_COLOURS["max_pain"],
                    label="max pain")
        ax.legend(fontsize=7, frameon=False, loc="upper left")
        ticks = list(range(0, len(rows), 5))
        ax.set_xticks(ticks)
        ax.set_xticklabels([rows[t]["session"][5:] for t in ticks])
        out = ch._finish(fig, name, out_dir)
        neg = sum(1 for r in rows if r.get("gamma_regime") == "negative")
        cap = (f"{title}; hatched sessions in negative gamma ({neg} of "
               f"{len(rows)}), plain in positive; month-end close "
               f"{rows[-1]['close']:,.2f}")
        return {"id": "M3", "title": title, "drawn": [], "caption": cap, **out,
                "series": [{k: r.get(k) for k in ("session", "close", "flip_morning",
                                                   "max_pain", "gamma_regime")}
                           for r in rows]}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "M3", "unavailable": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# M5: twenty years of the high-yield spread
# ---------------------------------------------------------------------------
def m5(hy: list[tuple[str, float]], name: str, out_dir: Optional[str]) -> dict:
    if len(hy) < 60:
        return {"id": "M5", "unavailable": f"{len(hy)} observations stored, 60 needed"}
    try:
        from altdata import derived                             # noqa: PLC0415
        vals = [v for _, v in hy]
        pct = derived.percentile_of(vals, vals[-1])
        yrs = (dt.date.fromisoformat(hy[-1][0]) - dt.date.fromisoformat(hy[0][0])).days
        title = ch.span_title("High-yield OAS (ICE BofA, FRED), percent", len(hy),
                              "observations", hy[0][0], hy[-1][0],
                              "twenty years" if yrs >= 365 * 20 - 31 else
                              f"twenty years asked; the store holds "
                              f"{yrs / 365.25:.1f}")
        fig, ax = ch._base(title)
        ax.plot(range(len(vals)), vals, color="#0d2b45", linewidth=0.9)
        marks = {q: derived.percentile_at(vals, q) for q in (10, 50, 90)}
        for q, v in marks.items():
            ax.axhline(v, color="#94a3b8" if q == 50 else "#d97706",
                       linestyle="--", linewidth=0.8)
            ax.annotate(f"{q}th {v:.2f}", xy=(1.0, v), xycoords=("axes fraction",
                        "data"), xytext=(3, 0), textcoords="offset points",
                        va="center", fontsize=6.5, color="#475569")
        ax.plot([len(vals) - 1], [vals[-1]], marker="o", color=ch.DOWN, markersize=4)
        ax.annotate(f"{vals[-1]:.2f} ({pct:.0f}th)", xy=(len(vals) - 1, vals[-1]),
                    xytext=(-4, 6), textcoords="offset points", ha="right",
                    fontsize=7, color=ch.DOWN)
        spaced_ticks(ax, [d for d, _ in hy], 5)
        out = ch._finish(fig, name, out_dir)
        cap = (f"{title}; latest {vals[-1]:.2f} on {hy[-1][0]}, at the "
               f"{pct:.0f}th percentile of the span; 10th {marks[10]:.2f}, median "
               f"{marks[50]:.2f}, 90th {marks[90]:.2f}")
        return {"id": "M5", "title": title, "drawn": [], "caption": cap, **out,
                "percentile": pct, "marks": marks,
                "series": [{"date": d, "value": v} for d, v in hy]}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "M5", "unavailable": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# M6: the positioning z-scores, ranked (T3.1 item 11)
# ---------------------------------------------------------------------------
def m6(history: list[dict], now: str, name: str, out_dir: Optional[str]) -> dict:
    """One ranked horizontal bar per positioning series that has a z (its
    latest value against its own last two years, monthly_macro.stack
    .positioning_history) -- the z is the insight, and ten panes hid it. A
    series with too short a history is named in the caption, not drawn."""
    rows = sorted([(h["series"], h["z_two_years"]) for h in history or []
                   if h.get("z_two_years") is not None], key=lambda r: r[1])
    short = [h["series"] for h in history or [] if h.get("z_two_years") is None]
    if len(rows) < 2:
        return {"id": "M6", "unavailable": f"{len(rows)} positioning series with two "
                                           f"years of history stored, 2 needed"}
    try:
        plt = ch._plt()
        fig, ax = plt.subplots(figsize=(ch.CHART_W, 0.26 * len(rows) + 1.0))
        title = ch.span_title("Positioning, each series' z over its own two years",
                              len(rows), "series", _years_back(now, 2), now,
                              "ranked")
        ax.set_title(title, fontsize=9, loc="left", color="#0d2b45")
        ax.barh(range(len(rows)), [v for _, v in rows],
                color=[ch.UP if v >= 0 else ch.DOWN for _, v in rows],
                edgecolor="#0d2b45", linewidth=0.4)
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([k for k, _ in rows], fontsize=7)
        for x in (-2, -1, 1, 2):
            ax.axvline(x, color="#d97706" if abs(x) == 1 else "#b3261e",
                       linewidth=0.5, linestyle="--")
        ax.axvline(0, color="#94a3b8", linewidth=0.6)
        ax.tick_params(labelsize=7)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for i, (_, v) in enumerate(rows):
            ax.annotate(f"{v:+.1f}", xy=(v, i), xytext=(3 if v >= 0 else -3, 0),
                        textcoords="offset points", va="center",
                        ha="left" if v >= 0 else "right", fontsize=6.5)
        out = ch._finish(fig, name, out_dir)
        cap = (f"{title}; highest {rows[-1][0]} z {rows[-1][1]:+.1f}, lowest "
               f"{rows[0][0]} z {rows[0][1]:+.1f}"
               + (f"; history too short to rank: {', '.join(short)}" if short else ""))
        return {"id": "M6", "title": title, "drawn": [], "caption": cap, **out,
                "series": [{"series": k, "z": v} for k, v in rows],
                "not_drawn": short}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "M6", "unavailable": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# M7: what's priced, month start against month end
# ---------------------------------------------------------------------------
def m7(be: dict, then: str, now: str, name: str, out_dir: Optional[str]) -> dict:
    """Breakevens at the month's start against its end, beside the breakevens
    block (T3.1 item 12). `be`: label -> (value at the start, value at the end)."""
    have = {k: v for k, v in be.items() if None not in v}
    if not have:
        return {"id": "M7", "unavailable": "no breakeven stored at both ends of the "
                                           "month"}
    try:
        title = ch.span_title("Breakevens, percent", 2, "dates", then, now,
                              "month start against month end")
        fig, ax = ch._base(title)
        labs = list(have)
        xs = range(len(labs))
        ax.bar([x - 0.18 for x in xs], [have[k][0] for k in labs], width=0.36,
               color="white", edgecolor="#0d2b45", hatch="//", label="month start")
        ax.bar([x + 0.18 for x in xs], [have[k][1] for k in labs], width=0.36,
               color="#0d2b45", label="month end")
        # The values on the bars: a breakeven moves by basis points, which a bar
        # from zero cannot show.
        for x, k in zip(xs, labs):
            for dx, v in ((-0.18, have[k][0]), (0.18, have[k][1])):
                ax.annotate(f"{v:.2f}", xy=(x + dx, v), xytext=(0, 2),
                            textcoords="offset points", ha="center", fontsize=6.5)
        ax.set_ylim(0, max(max(v) for v in have.values()) * 1.18)
        ax.set_xticks(list(xs))
        ax.set_xticklabels(labs, fontsize=7)
        ax.legend(fontsize=7, frameon=False, loc="upper center", ncol=2,
                  bbox_to_anchor=(0.5, -0.12))
        out = ch._finish(fig, name, out_dir)
        bits = [f"{k} breakeven {a:.2f} to {b:.2f}" for k, (a, b) in have.items()]
        return {"id": "M7", "title": title, "drawn": [],
                "caption": f"Breakevens, {then[:10]} against {now[:10]}: "
                           + "; ".join(bits), **out,
                "breakevens": {k: list(v) for k, v in have.items()}}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "M7", "unavailable": f"{type(exc).__name__}: {exc}"}


def m10(path_then: Optional[dict], path_now: Optional[dict], then: str, now: str,
        name: str, out_dir: Optional[str]) -> dict:
    """The fed-funds futures' implied rate after each of the next meetings, at
    the month's start against its end, beside the FOMC block (T3.1 item 12)."""
    paths = [(lab, p) for lab, p in (("month start", path_then), ("month end", path_now))
             if p and p.get("tracked") and p.get("meetings")]
    if not paths:
        return {"id": "M10", "unavailable": "the fed funds implied path is not "
                                            "tracked: fewer than four meetings "
                                            "retrievable"}
    try:
        title = ch.span_title("Fed funds futures: implied rate after each meeting, "
                              "percent", len(paths), "dates", then, now,
                              "month start against month end")
        fig, ax = ch._base(title)
        for (lab, p), c in zip(paths, ("#94a3b8", "#0d2b45")):
            ms = p["meetings"][:6]
            ax.plot(range(len(ms)), [m["post_pct"] for m in ms], color=c,
                    marker="o", markersize=3, linewidth=1.0, label=lab)
        ms = paths[-1][1]["meetings"][:6]
        ax.set_xticks(range(len(ms)))
        ax.set_xticklabels([m["meeting"][2:10] for m in ms], fontsize=6.5)
        ax.legend(fontsize=7, frameon=False)
        out = ch._finish(fig, name, out_dir)
        last = paths[-1][1]["meetings"][:6]
        cap = (f"Fed funds futures, {then[:10]} against {now[:10]}: "
               + "; ".join(f"after {m['meeting'][:10]} {m['post_pct']:.2f}%"
                           for m in last[:3])
               + ("" if len(paths) == 2 else "; the month's start is not tracked"))
        return {"id": "M10", "title": title, "drawn": [], "caption": cap, **out,
                "paths": [lab for lab, _ in paths]}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "M10", "unavailable": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# M8: the scenario weights and their Brier, edition by edition
# ---------------------------------------------------------------------------
def scenario_history(rows: list[dict], now: str) -> list[dict]:
    """Per Monthly edition (scenario set monthly_macro:YYYY-MM): the weights as
    emitted, and the mean Brier of those resolved by the cutoff."""
    out: dict[str, dict] = {}
    for r in rows:
        ss = str(r.get("scenario_set") or "")
        if r.get("source") != "monthly_macro" or not ss.startswith("monthly_macro:") \
                or str(r.get("emitted_at")) > now:
            continue
        e = out.setdefault(ss.split(":", 1)[1], {"weights": [], "briers": []})
        e["weights"].append((r["claim"], float(r["probability"])))
        if r.get("brier") is not None and r.get("resolved_at") \
                and str(r["resolved_at"]) <= now:
            e["briers"].append(float(r["brier"]))
    return [{"edition": k, "weights": v["weights"], "n_resolved": len(v["briers"]),
             "brier": (sum(v["briers"]) / len(v["briers"]) if v["briers"] else None)}
            for k, v in sorted(out.items())]


def m8(hist: list[dict], name: str, out_dir: Optional[str]) -> dict:
    if not hist:
        return {"id": "M8", "unavailable": "not yet: scenario set #1"}
    try:
        plt = ch._plt()
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(ch.CHART_W, 4.0), sharex=True,
                                     gridspec_kw={"height_ratios": [3, 2]})
        title = ch.span_title("Scenario weights by Monthly edition, and their Brier",
                              len(hist), "edition" if len(hist) == 1 else "editions",
                              hist[0]["edition"],
                              hist[-1]["edition"], "since the first")
        a1.set_title(title, fontsize=9, loc="left", color="#0d2b45")
        hatches = ("", "//", "..", "xx", "\\\\", "--")
        for i, e in enumerate(hist):
            base = 0.0
            for j, (_, w) in enumerate(e["weights"]):
                a1.bar(i, w, bottom=base, color="#cbd5e1", edgecolor="#0d2b45",
                       hatch=hatches[j % len(hatches)], linewidth=0.5)
                if w >= 0.08:
                    a1.annotate(f"{w:.0%}", xy=(i, base + w / 2), ha="center",
                                va="center", fontsize=6.5)
                base += w
        a1.set_ylabel("weight", fontsize=7)
        xs = [i for i, e in enumerate(hist) if e["brier"] is not None]
        if xs:
            a2.bar(xs, [hist[i]["brier"] for i in xs], color="#0d2b45", width=0.5)
            for i in xs:
                a2.annotate(f"{hist[i]['brier']:.3f} (n={hist[i]['n_resolved']})",
                            xy=(i, hist[i]["brier"]), xytext=(0, 2),
                            textcoords="offset points", ha="center", fontsize=6.5)
        a2.axhline(0.25, color=ch.DOWN, linestyle="--", linewidth=0.8)
        a2.annotate("a coin, 0.25", xy=(1.0, 0.25), xycoords=("axes fraction", "data"),
                    xytext=(3, 0), textcoords="offset points", va="center",
                    fontsize=6.5, color=ch.DOWN)
        a2.set_ylabel("mean Brier", fontsize=7)
        a2.set_xticks(range(len(hist)))
        a2.set_xticklabels([e["edition"] for e in hist], fontsize=7)
        for a in (a1, a2):
            a.tick_params(labelsize=7)
            for side in ("top", "right"):
                a.spines[side].set_visible(False)
        fig.tight_layout()
        out = ch._finish(fig, name, out_dir)
        last = hist[-1]
        cap = (f"{title}; {last['edition']}: "
               + "; ".join(f"{c} {w:.0%}" for c, w in last["weights"])
               + "; " + ("; ".join(f"{e['edition']} Brier {e['brier']:.3f} "
                                   f"(n={e['n_resolved']})" for e in hist
                                   if e["brier"] is not None)
                         or "no edition's weights resolved yet"))
        return {"id": "M8", "title": title, "drawn": [], "caption": cap, **out,
                "series": hist}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "M8", "unavailable": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# M9: Book Z against the books
# ---------------------------------------------------------------------------
def indexed(pts: list[tuple[str, float]], start: str) -> list[tuple[str, float]]:
    """A series rebased to 100 at its last value on or before `start`."""
    base = [v for d, v in pts if d <= start]
    b0 = base[-1] if base else (pts[0][1] if pts else None)
    if not b0:
        return []
    return [(d, 100.0 * v / b0) for d, v in pts if d >= start]


def m9(ledgers: dict, nav: list[tuple[str, float]], start: str, now: str,
       name: str, out_dir: Optional[str]) -> dict:
    series = {lab: pts for lab, pts in ledgers.items() if pts}
    navi = indexed(nav, start)
    if navi:
        series["Paper account NAV, all books"] = navi
    if not series:
        return {"id": "M9", "unavailable": "no Book Z mark and no account NAV stored"}
    n = max(len(v) for v in series.values())
    title = ch.span_title("Book Z against the books, indexed to 100", n, "sessions",
                          start, now, f"since {start}")
    r = ch.lines_chart("M9", series, title, name, out_dir, min_points=2)
    r["title"] = title
    if not r.get("unavailable"):
        r["caption"] += ("; Books A to D are not marked separately yet, so the "
                         "account's NAV stands for all of them" if navi else
                         "; the account's NAV is not stored yet")
    return r


# ---------------------------------------------------------------------------
# The edition's charts
# ---------------------------------------------------------------------------
def series(st, key: str, now: str, instrument: Optional[str] = None,
           since: Optional[str] = None) -> list[tuple[str, float]]:
    rows = sorted((str(r["observed_at"])[:10], float(r["value_num"]))
                  for r in st.as_of(key, now, instrument)
                  if r.get("value_num") is not None)
    return [r for r in rows if not since or r[0] >= since]


def _years_back(now: str, years: int) -> str:
    d = dt.date.fromisoformat(now[:10])
    return (d - dt.timedelta(days=int(365.25 * years))).isoformat()


def build(ed: dict, book: Optional[dict], retro: Optional[dict], db_path: Optional[str],
          out_dir: Optional[str], base: str) -> dict:
    """Every planned chart, each placed in its section; ed["charts"] (without the
    PNG bytes) and ed["chart_count"] set. Returns {id: chart} with the PNGs."""
    from altdata import benchmark, levels as levels_mod, observations  # noqa: PLC0415
    from altdata import probability_ledger                         # noqa: PLC0415
    w = ed.get("window") or {}
    last, now, then = w.get("last"), w.get("now"), w.get("then")
    want = plan(ed)
    charts: dict[str, dict] = {}

    def run(cid: str, fn) -> None:
        if cid not in want:
            return
        try:
            charts[cid] = fn()
        except Exception as exc:                                 # noqa: BLE001
            log.warning("%s unavailable", cid, exc_info=True)
            charts[cid] = {"id": cid, "unavailable": f"{type(exc).__name__}: {exc}"}

    with observations.ObservationStore(db_path) as st:
        try:
            daily, _ = levels_mod.daily_bars(levels_mod.tape_spec("spy"), last, now, st)
        except Exception:                                       # noqa: BLE001
            daily = []
        run("M0", lambda: m0(book or {}, daily, f"{base}_m0", out_dir))
        run("M1", lambda: m1(book or {}, daily, f"{base}_m1", out_dir))
        run("M2", lambda: m2(book or {}, daily, f"{base}_m2", out_dir))
        run("M3", lambda: m3((retro or {}).get("sessions") or [], f"{base}_m3",
                             out_dir))
        five = _years_back(now, 5)
        def _m4():
            title = _m4_title(st, now, five)
            return {**ch.lines_chart(
                "M4", {"10-year yield": series(st, "fred.yield_10y", now, since=five),
                       "ACM term premium, 10-year": series(
                           st, "acm.term_premium_10y", now, since=five)},
                title, f"{base}_m4", out_dir), "title": title}
        run("M4", _m4)
        run("M5", lambda: m5(series(st, "fred.hy_oas", now, since=_years_back(now, 20)),
                             f"{base}_m5", out_dir))

        def _m6():
            pos = next((s for s in ed.get("sections") or []
                        if s["id"] == "positioning"), {})
            return m6((pos.get("data") or {}).get("history") or [], now,
                      f"{base}_m6", out_dir)
        run("M6", _m6)

        def _m7():
            be = {}
            for k, lab in BREAKEVENS:
                a, b = st.latest_as_of(k, then), st.latest_as_of(k, now)
                be[lab] = ((a or {}).get("value_num"), (b or {}).get("value_num"))
            return m7(be, then, now, f"{base}_m7", out_dir)
        run("M7", _m7)

        def _m10():
            from altdata import fed_funds                         # noqa: PLC0415
            return m10(fed_funds.path_as_of(then, st), fed_funds.path_as_of(now, st),
                       then, now, f"{base}_m10", out_dir)
        run("M10", _m10)

        def _m9():
            start = benchmark.start_date().isoformat()
            led = {}
            for lg in benchmark.LEDGERS:
                pts = series(st, benchmark.KEY, now, lg, start)
                led[f"Book Z: {benchmark.LABEL.get(lg, lg)}"] = pts
            return m9(led, series(st, "portfolio.nav", now), start, now,
                      f"{base}_m9", out_dir)
        run("M9", _m9)

    def _m8():
        with probability_ledger.ProbabilityLedger(db_path) as led:
            return m8(scenario_history(led.all_rows(), now), f"{base}_m8", out_dir)
    run("M8", _m8)
    for c in charts.values():
        if c.get("min_px_at_400") is not None:
            c["min_px_at_400"] = float(c["min_px_at_400"])
    ed["charts_over_cap"] = hold_cap(charts, cap_of(ed))
    place(ed, charts)
    ed["charts"] = {k: {kk: v for kk, v in c.items() if kk != "png"}
                    for k, c in charts.items()}
    ed["chart_count"] = sum(1 for c in charts.values() if not c.get("unavailable"))
    ed["chart_plan"] = want
    return charts


def _m4_title(st, now: str, since: str) -> str:
    pts = series(st, "fred.yield_10y", now, since=since)
    first = pts[0][0] if pts else since
    return ch.span_title("The 10-year yield and the ACM 10-year term premium, percent",
                         len(pts), "observations", first, now, "five years")


def place(ed: dict, charts: dict) -> None:
    for cid in ORDER:
        if cid not in charts:
            continue
        sid, sub = PLACE[cid]
        s = next((x for x in ed["sections"] if x["id"] == sid), None)
        if s is None:
            continue
        tgt = next((ss for ss in s.get("subsections") or []
                    if sub and sub in (ss.get("title"), ss.get("bucket"))), s)
        tgt.setdefault("charts_rendered", []).append(cid)


def drawn_levels_ok(chart: dict, book: Optional[dict]) -> bool:
    """Every level a chart drew is in the level list, label and value."""
    listed = {(lv["label"], lv["value"]) for i in (book or {}).get("instruments") or []
              for lv in i.get("levels") or []}
    return all((d["label"], d["value"]) in listed for d in chart.get("drawn") or [])


def png_name(stamp: str, cid: str) -> str:
    return f"monthly_macro_{stamp}_{cid.lower()}.png"


def cids_in(html: str) -> list[str]:
    """The chart ids an archived HTML references by Content-ID."""
    return sorted(set(m.upper() for m in re.findall(r'cid:(m\d+)@chester', html)))


def archive_pngs(charts: dict, stamp: str, out_dir: str) -> list[str]:
    """Each chart's PNG beside the archived HTML, so a re-send (--deliver-only)
    mails the same images the record references. Returns the paths written."""
    from pathlib import Path                                    # noqa: PLC0415
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    out = []
    for k, c in charts.items():
        if c.get("png"):
            p = d / png_name(stamp, k)
            p.write_bytes(c["png"])
            out.append(str(p))
    return out


def inline_images(html: str, stamp: str, out_dir: str) -> tuple[list, list[str]]:
    """(the (Content-ID, PNG bytes) pairs an archived HTML references, the ids
    whose PNG is missing)."""
    from pathlib import Path                                    # noqa: PLC0415
    from daily_cascade import stack_render                      # noqa: PLC0415
    got, missing = [], []
    for cid in cids_in(html):
        p = Path(out_dir) / png_name(stamp, cid)
        if p.exists():
            got.append((stack_render.cid(cid), p.read_bytes()))
        else:
            missing.append(cid)
    return got, missing


def self_contained(html: str, images: Optional[list]) -> str:
    """The archived email HTML with each `cid:` chart replaced by its PNG as a
    data URI: the page attached to the email (T3.1 item 1), which a phone's
    browser opens on its own and lays out to the screen."""
    import base64                                               # noqa: PLC0415
    for c, png in images or []:
        html = html.replace(f"cid:{c}", "data:image/png;base64,"
                            + base64.b64encode(png).decode("ascii"))
    return html
