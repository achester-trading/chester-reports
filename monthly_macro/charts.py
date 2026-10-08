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

    M1  SPY, three years of weekly candles, the 40-week average     The tape
    M2  SPY, ten years of monthly candles, the 10- and 20-month,
        and the drawdown from the high                            The tape
    M3  the dealer retrospective: the month's closes against the
        morning flip and max pain, shaded by gamma regime          Mechanics
    M4  the 10-year yield and the ACM 10-year term premium, five
        years                                                      Plumbing
    M5  the high-yield spread over twenty years, its percentiles
        marked and the latest's own                                Plumbing
    M6  speculative positioning (CFTC) as z-scores, five years     Positioning
    M7  what's priced at the month's start against its end:
        breakevens and the fed-funds implied path                  What's priced
    M8  the scenario weights by edition, and their Brier           Ahead
    M9  Book Z (cash, SPY, 60/40) against the paper account's NAV,
        indexed to 100 since the start date                        The book

The cap is the Monthly's chart budget (10); a fired depth trigger lifts it by
one, as on every cadence.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import re
from typing import Optional

from daily_cascade import charts as ch

log = logging.getLogger("monthly_macro.charts")

ORDER = ("M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9")
# Where each chart prints: (section id, sub-section title or None).
PLACE = {"M1": ("tape", None), "M2": ("tape", None), "M3": ("mechanics", None),
         "M4": ("plumbing", None), "M5": ("plumbing", None),
         "M6": ("positioning", None), "M7": ("priced", None),
         "M8": ("ahead", "Scenarios, and what would change our mind"),
         "M9": ("book", None)}
LONG_FRAME_TYPES = {"M1": ("ma_40w",), "M2": ("ma_10m", "ma_20m")}
BREAKEVENS = (("fred.breakeven_5y", "5-year"), ("fred.breakeven_10y", "10-year"),
              ("fred.breakeven_5y5y", "5y5y forward"))


def plan(ed: dict) -> list[str]:
    """M1-M9 within the cap; a fired trigger lifts the cap by one."""
    cap = int((ed.get("budget") or {}).get("charts") or 10)
    if any(s.get("depth_reason") for s in ed.get("sections") or []):
        cap += 1
    return list(ORDER)[:cap]


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
    """k evenly spaced dated ticks and the last date, dropping a spaced tick that
    falls within half a step of the last (two labels printed over each other)."""
    if not dates:
        return
    n = len(dates)
    step = max(1, n // k)
    idx = [i for i in range(0, n, step) if n - 1 - i >= step / 2] + [n - 1]
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


def m1(book: dict, daily: list[dict], name: str, out_dir: Optional[str]) -> dict:
    wk = ch.weekly_bars(daily)[-156:]
    if len(wk) < 20:
        return {"id": "M1", "unavailable": f"{len(wk)} weekly bars stored, 20 needed"}
    try:
        title = ch.span_title("SPY in weekly bars", len(wk), "weeks",
                              wk[0]["observed_at"], wk[-1]["observed_at"],
                              _plain_span(len(wk), 156, "weeks", "three years"))
        r = _candles_log("M1", wk, book, title, f"{len(wk)} weekly bars", name, out_dir,
                         tick_every=26)
        out = ch._finish(r["fig"], name, out_dir)
        return {"id": "M1", "title": title, "drawn": r["drawn"],
                "caption": ch.caption("SPY", f"{len(wk)} weekly bars", r["drawn"]),
                **out, "series": [{k: b[k] for k in ("observed_at", "open", "high",
                                                      "low", "close")} for b in wk]}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "M1", "unavailable": f"{type(exc).__name__}: {exc}"}


def m2(book: dict, daily: list[dict], name: str, out_dir: Optional[str]) -> dict:
    mo = monthly_bars(daily)[-120:]
    if len(mo) < 12:
        return {"id": "M2", "unavailable": f"{len(mo)} monthly bars stored, 12 needed"}
    try:
        plt = ch._plt()
        fig, (ax, ax2) = plt.subplots(2, 1, figsize=(ch.CHART_W, 4.4), sharex=True,
                                      gridspec_kw={"height_ratios": [3, 1]})
        title = ch.span_title("SPY in monthly bars", len(mo), "months",
                              mo[0]["observed_at"], mo[-1]["observed_at"],
                              _plain_span(len(mo), 120, "months", "ten years"))
        ax.set_title(title, fontsize=9, loc="left", color="#0d2b45")
        for a in (ax, ax2):
            a.tick_params(labelsize=7)
            for side in ("top", "right"):
                a.spines[side].set_visible(False)
        r = _candles_log("M2", mo, book, title, f"{len(mo)} monthly bars", name,
                         out_dir, ax=ax, fig=fig, tick_every=24)
        dd = drawdowns(mo)
        ax2.fill_between(range(len(dd)), dd, 0, color=ch.DOWN, alpha=0.35,
                         linewidth=0)
        ax2.plot(range(len(dd)), dd, color=ch.DOWN, linewidth=0.8)
        ax2.set_ylabel("From the high, %", fontsize=7)
        fig.tight_layout()
        out = ch._finish(fig, name, out_dir)
        worst = min(range(len(dd)), key=lambda i: dd[i])
        cap = (ch.caption("SPY", f"{len(mo)} monthly bars", r["drawn"])
               + f"; drawdown from the high {dd[-1]:+.1f}% at "
                 f"{mo[-1]['observed_at']}, deepest {dd[worst]:+.1f}% at "
                 f"{mo[worst]['observed_at']}")
        return {"id": "M2", "title": title, "drawn": r["drawn"], "caption": cap,
                **out, "drawdown_pct": round(dd[-1], 2),
                "series": [{k: b[k] for k in ("observed_at", "open", "high", "low",
                                               "close")} for b in mo]}
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
# M7: what's priced, month start against month end
# ---------------------------------------------------------------------------
def m7(be: dict, path_then: Optional[dict], path_now: Optional[dict],
       then: str, now: str, name: str, out_dir: Optional[str]) -> dict:
    """`be`: label -> (value at the month's start, value at its end)."""
    have = {k: v for k, v in be.items() if None not in v}
    paths = [(lab, p) for lab, p in (("month start", path_then), ("month end", path_now))
             if p and p.get("tracked") and p.get("meetings")]
    if not have and not paths:
        return {"id": "M7", "unavailable": "no breakeven and no implied path stored "
                                           "at both ends of the month"}
    try:
        plt = ch._plt()
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(ch.CHART_W, 3.2))
        for ax in (a1, a2):
            ax.tick_params(labelsize=7)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
        if have:
            labs = list(have)
            xs = range(len(labs))
            a1.bar([x - 0.18 for x in xs], [have[k][0] for k in labs], width=0.36,
                   color="white", edgecolor="#0d2b45", hatch="//", label="month start")
            a1.bar([x + 0.18 for x in xs], [have[k][1] for k in labs], width=0.36,
                   color="#0d2b45", label="month end")
            # The values on the bars: a breakeven moves by basis points, which a
            # bar from zero cannot show.
            for x, k in zip(xs, labs):
                for dx, v in ((-0.18, have[k][0]), (0.18, have[k][1])):
                    a1.annotate(f"{v:.2f}", xy=(x + dx, v), xytext=(0, 2),
                                textcoords="offset points", ha="center", fontsize=6.5)
            a1.set_ylim(0, max(max(v) for v in have.values()) * 1.18)
            a1.set_xticks(list(xs))
            a1.set_xticklabels(labs, fontsize=7)
            a1.set_title("Breakevens (%)", fontsize=8, loc="left")
            a1.legend(fontsize=7, frameon=False, loc="upper center", ncol=2,
                      bbox_to_anchor=(0.5, -0.12))
        else:
            ch._untracked(a1, "Breakevens")
        if paths:
            for (lab, p), c in zip(paths, ("#94a3b8", "#0d2b45")):
                ms = p["meetings"][:6]
                a2.plot(range(len(ms)), [m["post_pct"] for m in ms], color=c,
                        marker="o", markersize=3, linewidth=1.0, label=lab)
            ms = paths[-1][1]["meetings"][:6]
            a2.set_xticks(range(len(ms)))
            a2.set_xticklabels([m["meeting"][2:10] for m in ms], fontsize=6.5)
            a2.set_title("Fed funds futures: implied rate after each meeting (%)",
                         fontsize=8, loc="left")
            a2.legend(fontsize=7, frameon=False)
        else:
            # Wrapped to the panel: the shared one-line form runs into its
            # neighbour at half width.
            a2.set_xticks([])
            a2.set_yticks([])
            a2.set_title("Fed funds implied path", fontsize=8, loc="left")
            a2.text(0.5, 0.5, "not yet tracked:\nfewer than four meetings\n"
                    "retrievable", ha="center", va="center", fontsize=7.5,
                    color="#94a3b8", transform=a2.transAxes)
        title = ch.span_title("What's priced", 2, "dates",
                              then, now, "month start against month end")
        fig.suptitle(title, fontsize=9, x=0.02, ha="left", color="#0d2b45")
        fig.tight_layout()
        out = ch._finish(fig, name, out_dir)
        bits = [f"{k} breakeven {a:.2f} to {b:.2f}" for k, (a, b) in have.items()]
        cap = (f"What's priced, {then[:10]} against {now[:10]}: "
               + ("; ".join(bits) if bits else "breakevens not stored at both ends")
               + ("" if len(paths) == 2 else "; the implied path is not tracked at "
                                             "both ends"))
        return {"id": "M7", "title": title,
                "drawn": [], "caption": cap, **out,
                "breakevens": {k: list(v) for k, v in have.items()},
                "paths": [lab for lab, _ in paths]}
    except Exception as exc:                                    # noqa: BLE001
        return {"id": "M7", "unavailable": f"{type(exc).__name__}: {exc}"}


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
        return {"id": "M8", "unavailable": "no Monthly scenario weight in the ledger"}
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
            from daily_cascade.weekly_stack import CFTC_CONTRACTS  # noqa: PLC0415
            cftc = {lab: series(st, "cftc.noncomm_net", now, inst, five)
                    for inst, lab in CFTC_CONTRACTS}
            got = [v for v in cftc.values() if len(v) >= 20]
            if not got:
                return {"id": "M6", "unavailable": "no CFTC contract with 20 weekly "
                                                   "reports stored"}
            d0 = min(v[0][0] for v in got)
            title = ch.span_title(
                "Speculative positioning, CFTC net contracts as z-scores",
                max(len(v) for v in got), "weekly reports", d0, now, "five years")
            return {**ch.z_panel("M6", cftc, title, f"{base}_m6", out_dir,
                                 min_points=20), "title": title}
        run("M6", _m6)

        def _m7():
            from altdata import fed_funds                         # noqa: PLC0415
            be = {}
            for k, lab in BREAKEVENS:
                a, b = st.latest_as_of(k, then), st.latest_as_of(k, now)
                be[lab] = ((a or {}).get("value_num"), (b or {}).get("value_num"))
            return m7(be, fed_funds.path_as_of(then, st), fed_funds.path_as_of(now, st),
                      then, now, f"{base}_m7", out_dir)
        run("M7", _m7)

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
                    if sub and ss.get("title") == sub), s)
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
