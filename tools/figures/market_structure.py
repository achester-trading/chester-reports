#!/usr/bin/env python3
"""
Market Structure and Cascades' figures (B78, 26 Oct 2026), numbered by order of
appearance in the paper (B74 ruling 3), into docs/figures/market-structure-and-cascades/.

    python tools/figures/market_structure.py --db PATH

  fig-01  the cascade as a loop (Chapter 6.1): conceptual, no series
  fig-02  dealer gamma and the session's range (7.4): exposure.net_gex, yfinance.mkt_spy
  fig-03  the stock-bond correlation's sign (9.1): calc.corr_spy_tlt_60d, else the
          60-session correlation of the stored SPY and TLT closes by the correlation
          layer's own method (altdata/correlation.py returns and rolling_corr)
  fig-04  leveraged funds' net in ES (10.x): cftc.tff_lev_money_net_oi
  fig-05  the volatility index through the cases (Part III): fred.vix
  fig-06  forced flow against depth (19.1): levetf.aum, yfinance.mkt_spy
  fig-07  margin debt through the cases (19.1): finra.margin_debit

The store is opened read-only (mode=ro) and each observation day reads its latest
vintage. A figure whose keys hold no rows is not drawn; the script says so and the
paper keeps its placeholder, drawn at merge from the box's store. Every drawn
series figure says which store it came from in its foot line.
"""

from __future__ import annotations

import argparse
import datetime as dt
import math
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "figures" / "market-structure-and-cascades"
W, H = 680, 404
L, R, T, B = 62, 658, 34, 334
INK, MUTE, GRID = "#1a1a1a", "#5b5b5b", "#d8d4cc"
C1, C2, C3, RED = "#3a5f8a", "#2f6f4f", "#8a5fb0", "#9c3b3b"
FONT = "-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif"

# The cases the paper tells (Part III), with the date each is marked at. A case
# before the series' first observation is listed in the foot, not marked.
CASES = [("1987", "1987-10-19"), ("1998", "1998-08-31"), ("2010", "2010-05-06"),
         ("Feb 2018", "2018-02-05"), ("Mar 2020", "2020-03-16"), ("Jan 2021", "2021-01-28"),
         ("2022 gilts", "2022-09-28"), ("Aug 2024", "2024-08-05"), ("Apr 2025", "2025-04-08")]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Plot:
    """The house plot, as tools/figures/evidence_inference.py draws it, on a date axis."""

    def __init__(self, title, xr, yr):
        self.xr, self.yr = xr, yr
        self.out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" '
                    f'font-family="{FONT}" font-size="11">',
                    f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff"/>',
                    f'<text x="{L}" y="20" font-size="12.5" font-weight="600" fill="{INK}">{esc(title)}</text>',
                    f'<defs><clipPath id="plotbox"><rect x="{L}" y="{T}" width="{R - L}" '
                    f'height="{B - T}"/></clipPath></defs>']

    def x(self, v):
        a, b = self.xr
        return L + (v - a) / (b - a) * (R - L)

    def y(self, v):
        a, b = self.yr
        return B - (v - a) / (b - a) * (B - T)

    def grid(self, xs, ys, xfmt=str, yfmt=str, ylabel=""):
        for v in xs:
            px = self.x(v)
            self.out.append(f'<line x1="{px:.1f}" y1="{B}" x2="{px:.1f}" y2="{T}" stroke="{GRID}" stroke-width="0.6"/>'
                            f'<text x="{px:.1f}" y="{B + 15}" text-anchor="middle" fill="{MUTE}">{xfmt(v)}</text>')
        for v in ys:
            py = self.y(v)
            self.out.append(f'<line x1="{L}" y1="{py:.1f}" x2="{R}" y2="{py:.1f}" stroke="{GRID}" stroke-width="0.6"/>'
                            f'<text x="{L - 7}" y="{py + 3.5:.1f}" text-anchor="end" fill="{MUTE}">{yfmt(v)}</text>')
        if ylabel:
            self.out.append(f'<text x="16" y="{(T + B) / 2}" text-anchor="middle" fill="{MUTE}" '
                            f'transform="rotate(-90 16 {(T + B) / 2})">{ylabel}</text>')

    def line(self, pts, color, width=1.4):
        d = " ".join(f"{'M' if i == 0 else 'L'}{self.x(a):.1f},{self.y(b):.1f}" for i, (a, b) in enumerate(pts))
        self.out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" '
                        f'clip-path="url(#plotbox)"/>')

    def fill_to(self, pts, base, color, opacity):
        """Shade between the series and a level, one run per sign, as SVG paths."""
        if not pts:
            return
        d = (f"M{self.x(pts[0][0]):.1f},{self.y(base):.1f} "
             + " ".join(f"L{self.x(a):.1f},{self.y(b):.1f}" for a, b in pts)
             + f" L{self.x(pts[-1][0]):.1f},{self.y(base):.1f} Z")
        self.out.append(f'<path d="{d}" fill="{color}" opacity="{opacity}" stroke="none" '
                        f'clip-path="url(#plotbox)"/>')

    def hline(self, v, color, dash="4 3"):
        self.out.append(f'<line x1="{L}" y1="{self.y(v):.1f}" x2="{R}" y2="{self.y(v):.1f}" '
                        f'stroke="{color}" stroke-width="1.0" stroke-dasharray="{dash}"/>')

    def mark(self, a, label, row=0):
        px = self.x(a)
        self.out.append(f'<line x1="{px:.1f}" y1="{B}" x2="{px:.1f}" y2="{T + 4}" stroke="{RED}" '
                        f'stroke-width="1.0" stroke-dasharray="3 3"/>'
                        f'<text x="{px + 4:.1f}" y="{T + 13 + 13 * row}" fill="{RED}">{esc(label)}</text>')

    def text(self, a, b, s, color=MUTE, anchor="start", size=11):
        self.out.append(f'<text x="{self.x(a):.1f}" y="{self.y(b):.1f}" fill="{color}" '
                        f'text-anchor="{anchor}" font-size="{size}">{esc(s)}</text>')

    def svg(self, foot, width=110):
        lines, cur = [], ""
        for w in foot.split():
            if cur and len(cur) + 1 + len(w) > width:
                lines.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}" if cur else w
        lines.append(cur)
        y0 = H - 8 - 13 * (len(lines) - 1)
        spans = "".join(f'<tspan x="{L}" y="{y0 + 13 * i}">{esc(s)}</tspan>' for i, s in enumerate(lines))
        self.out.append(f'<text fill="{MUTE}" font-size="10">{spans}</text></svg>')
        return "".join(self.out)


# ---------------------------------------------------------------- the store

def series(conn, key):
    """{YYYY-MM-DD: value}, each observation day at its latest vintage."""
    rows = conn.execute(
        "SELECT substr(observed_at, 1, 10), value_num FROM observations o "
        "WHERE registry_key = ? AND value_num IS NOT NULL AND available_at = ("
        "  SELECT max(available_at) FROM observations i WHERE i.registry_key = o.registry_key "
        "  AND substr(i.observed_at, 1, 10) = substr(o.observed_at, 1, 10) AND i.value_num IS NOT NULL) "
        "ORDER BY 1", (key,)).fetchall()
    return {d: float(v) for d, v in rows if v is not None and math.isfinite(float(v))}


def yr(d):
    """A date string as a fractional year, the x axis of every series figure."""
    t = dt.date.fromisoformat(d)
    start = dt.date(t.year, 1, 1)
    return t.year + (t - start).days / 365.25


def year_ticks(a, b):
    return [y for y in range(math.ceil(a), math.floor(b) + 1)]


def mark_cases(p, first, last):
    """Mark the cases inside the series' span; return the names before it."""
    before, row = [], 0
    for name, d in CASES:
        if d < first:
            before.append(name)
        elif d <= last:
            p.mark(yr(d), name, row % 2)
            row += 1
    return before


# ---------------------------------------------------------------- the figures

def fig1():
    """The cascade as a loop: four steps in a cycle, two exits. No series."""
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" '
           f'font-family="{FONT}" font-size="11">',
           f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff"/>',
           '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
           f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker></defs>',
           f'<text x="{L}" y="20" font-size="12.5" font-weight="600" fill="{INK}">'
           'Figure 1 · The cascade as a loop: a move that changes constraints produces the next move</text>']

    def box(cx, cy, w, h, head, sub, color):
        out.append(f'<rect x="{cx - w / 2:.0f}" y="{cy - h / 2:.0f}" width="{w}" height="{h}" rx="8" '
                   f'fill="#fff" stroke="{color}" stroke-width="1.6"/>')
        out.append(f'<text x="{cx}" y="{cy - 4 if sub else cy + 4}" text-anchor="middle" font-weight="600" '
                   f'fill="{color}" font-size="12">{esc(head)}</text>')
        for i, s in enumerate(sub):
            out.append(f'<text x="{cx}" y="{cy + 12 + 12 * i}" text-anchor="middle" fill="{MUTE}" '
                       f'font-size="10">{esc(s)}</text>')

    def arrow(x1, y1, x2, y2, label=None, lx=0, ly=0, color=INK):
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.4" '
                   f'marker-end="url(#ah)"/>')
        if label:
            out.append(f'<text x="{(x1 + x2) / 2 + lx}" y="{(y1 + y2) / 2 + ly}" fill="{MUTE}" '
                       f'font-size="10" text-anchor="middle">{esc(label)}</text>')

    # the loop: top, right, bottom, left
    box(340, 74, 200, 44, "1. A price move", [], C1)
    box(540, 178, 210, 66, "2. Constraints tighten",
        ["margin, value-at-risk, volatility targets,", "redemptions, the dealer's hedge"], C1)
    box(340, 278, 210, 54, "3. Forced flow meets depth", ["trades in the move's direction"], C1)
    box(140, 178, 200, 54, "4. The move extends", ["by flow divided by depth"], C1)
    arrow(440, 84, 520, 144)
    arrow(520, 212, 430, 262)
    arrow(250, 268, 170, 206)
    arrow(160, 150, 238, 90)
    out.append(f'<text x="340" y="182" text-anchor="middle" fill="{INK}" font-size="11.5" '
               'font-weight="600">the loop</text>')
    out.append(f'<text x="340" y="198" text-anchor="middle" fill="{MUTE}" font-size="10">'
               'each turn tightens the next</text>')
    # the two exits, from step 3
    out.append(f'<path d="M235,290 C180,320 130,330 96,334" fill="none" stroke="{C2}" stroke-width="1.3" '
               'stroke-dasharray="4 3" marker-end="url(#ah)"/>')
    out.append(f'<text x="{L}" y="350" fill="{C2}" font-size="10.5" font-weight="600">Damps</text>'
               f'<text fill="{MUTE}" font-size="10"><tspan x="{L + 44}" y="350">depth absorbs the flow, or a buyer</tspan>'
               f'<tspan x="{L + 44}" y="362">outside the constraints steps in</tspan></text>')
    out.append(f'<path d="M445,290 C500,320 560,330 600,334" fill="none" stroke="{RED}" stroke-width="1.3" '
               'stroke-dasharray="4 3" marker-end="url(#ah)"/>')
    out.append(f'<text x="{R}" y="350" fill="{RED}" font-size="10.5" font-weight="600" text-anchor="end">Runs</text>'
               f'<text fill="{MUTE}" font-size="10" text-anchor="end"><tspan x="{R - 40}" y="350">shared constraint shapes, thin depth:</tspan>'
               f'<tspan x="{R - 40}" y="362">the loop goes round again</tspan></text>')
    foot = ("Conceptual: no series. Whether the loop dies or runs depends on how much capital sits under "
            "constraints of the same shape, and on how deep the market is (Chapter 6).")
    out.append(f'<text fill="{MUTE}" font-size="10"><tspan x="{L}" y="{H - 21}">{esc(foot[:104])}</tspan>'
               f'<tspan x="{L}" y="{H - 8}">{esc(foot[104:].strip())}</tspan></text></svg>')
    return "".join(out)


def fig3(conn):
    s = series(conn, "calc.corr_spy_tlt_60d")
    how = "calc.corr_spy_tlt_60d"
    if not s:
        from altdata import correlation  # noqa: PLC0415
        spy, tlt = series(conn, "yfinance.mkt_spy"), series(conn, "yfinance.mkt_tlt")
        if not spy or not tlt:
            return None
        sa = {d: (v, d, None) for d, v in spy.items()}
        sb = {d: (v, d, None) for d, v in tlt.items()}
        ret = correlation.returns(sa, sb)
        c = correlation.rolling_corr(ret.x, ret.y, 60)
        s = {ret.days[i + 59]: float(v) for i, v in enumerate(c) if math.isfinite(v)}
        how = "the stored SPY and TLT closes (yfinance.mkt_spy, yfinance.mkt_tlt), the correlation layer's method"
    days = sorted(s)
    first, last = days[0], days[-1]
    a, b = yr(first), yr(last)
    p = Plot("Figure 3 · The stock–bond correlation's sign: 60-session SPY–TLT return correlation", (a, b), (-1, 1))
    p.grid(year_ticks(a, b), [-1, -0.5, 0, 0.5, 1], xfmt=str, yfmt=lambda v: f"{v:+.1f}" if v else "0",
           ylabel="correlation")
    pts = [(yr(d), s[d]) for d in days]
    p.fill_to([(x, max(v, 0)) for x, v in pts], 0, RED, 0.22)
    p.fill_to([(x, min(v, 0)) for x, v in pts], 0, C1, 0.22)
    p.line(pts, INK, 1.2)
    p.hline(0, MUTE, "2 3")
    before = mark_cases(p, first, last)
    p.text(a + 0.02 * (b - a), -0.78, "positive (red): stocks and bonds fall together", RED, size=10)
    p.text(a + 0.02 * (b - a), -0.9, "negative (blue): bonds hedge stocks", C1, size=10)
    return p.svg(f"From {how}; {first} to {last}. Laptop store; the box regenerates. "
                 f"Cases before the series: {', '.join(before)}." if before else
                 f"From {how}; {first} to {last}. Laptop store; the box regenerates.")


def fig5(conn):
    s = series(conn, "fred.vix")
    if not s:
        return None
    days = sorted(s)
    first, last = days[0], days[-1]
    a, b = yr(first), yr(last)
    top = max(10, math.ceil(max(s.values()) / 10) * 10)
    p = Plot("Figure 5 · The volatility index through the cases, from its first stored observation",
             (a, b), (0, top))
    p.grid(year_ticks(a, b), list(range(0, top + 1, 10)), ylabel="VIX, daily close")
    p.line([(yr(d), s[d]) for d in days], C1, 1.1)
    before = mark_cases(p, first, last)
    return p.svg(f"fred.vix, {first} to {last}: laptop store; the box regenerates from its full history. "
                 f"Cases before the store's first observation, not marked: {', '.join(before)}.")


NEEDS_BOX = {2: ("exposure.net_gex", "yfinance.mkt_spy"), 4: ("cftc.tff_lev_money_net_oi",),
             6: ("levetf.aum", "yfinance.mkt_spy"), 7: ("finra.margin_debit",)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--db", required=True, help="the observation store, opened read-only")
    args = ap.parse_args()
    conn = sqlite3.connect(f"file:{Path(args.db).as_posix()}?mode=ro", uri=True)
    OUT.mkdir(parents=True, exist_ok=True)
    drawn = {1: fig1(), 3: fig3(conn), 5: fig5(conn)}
    for n, keys in NEEDS_BOX.items():
        held = [k for k in keys if series(conn, k)]
        if set(held) == set(keys):
            print(f"fig-{n:02d}: every key is held here, but no drawing is written for it yet")
        else:
            print(f"fig-{n:02d}: not drawn -- no rows for {', '.join(k for k in keys if k not in held)}; "
                  f"drawn at merge from the box's store")
    for n, svg in sorted(drawn.items()):
        if svg is None:
            print(f"fig-{n:02d}: not drawn -- its keys hold no rows in this store")
            continue
        path = OUT / f"fig-{n:02d}.svg"
        path.write_bytes((svg + "\n").encode("utf-8"))
        print(f"wrote {path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
