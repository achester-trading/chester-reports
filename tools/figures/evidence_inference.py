#!/usr/bin/env python3
"""
Evidence and Inference's five computed figures (A74, 24 Oct 2026), drawn from the
paper's own formulas and worked numbers into docs/figures/evidence-inference/.

    python tools/figures/evidence_inference.py

  fig-01  the interval on a 0.2R edge against the number of decisions: 0.2 +/- 2/sqrt(n)
          (Chapter 1: per-decision spread near 1R; the interval about twice the
          standard error), the table's six sample sizes marked
  fig-02  a Sharpe of 1.0's error bar against years: SE = sqrt((1 + S^2/2) / T)
          (Chapter 2), one and two standard errors, T = 1, 5 and 10 marked
  fig-03  three priors updating on a process whose true hit rate is 60% (Chapter
          9): a weak prior (Beta(3,3)), the sceptic's (80 decisions at 50%,
          Beta(40,40)) and the mechanism's (40 decisions at 60%, Beta(24,16)); each
          posterior mean along the expected path, wins = 0.6n
  fig-04  Kelly under an uncertain edge (Chapter 14): the fraction of full Kelly
          against the edge's standard error as a share of the edge, by two rules --
          Bayesian shrinkage, m^2/(m^2+s^2), and sizing to the edge's lower
          two-standard-error bound, 1 - 2s/m -- with the paper's sample sizes marked
          for a 0.2R edge (s/m = 1/(0.2*sqrt(n)); a year's 200 decisions raw and at
          the effective 60 of Chapter 3)
  fig-05  edge decay (Chapter 15): a 0.2R edge decaying linearly from week 40 to zero
          by week 66, at 200 decisions a year; the trailing 13-week expectancy with
          a one-standard-error band, which first excludes the old edge at week 65

Deterministic and standard-library only: every number is computed, nothing is
sampled. A conceptual figure: no figure in it is data.
"""

from __future__ import annotations

import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "docs" / "figures" / "evidence-inference"
W, H = 680, 380
L, R, T, B = 62, 658, 34, 334          # plot box
INK, MUTE, GRID = "#1a1a1a", "#5b5b5b", "#d8d4cc"
C1, C2, C3, RED = "#3a5f8a", "#2f6f4f", "#8a5fb0", "#9c3b3b"
FONT = "-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif"


class Plot:
    def __init__(self, title, xr, yr, xlog=False):
        self.xr, self.yr, self.xlog = xr, yr, xlog
        self.out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" '
                    f'font-family="{FONT}" font-size="11">',
                    f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff"/>',
                    f'<text x="{L}" y="20" font-size="12.5" font-weight="600" fill="{INK}">{title}</text>']

    def x(self, v):
        a, b = self.xr
        if self.xlog:
            a, b, v = math.log10(a), math.log10(b), math.log10(v)
        return L + (v - a) / (b - a) * (R - L)

    def y(self, v):
        a, b = self.yr
        return B - (v - a) / (b - a) * (B - T)

    def grid(self, xs, ys, xfmt=str, yfmt=str, xlabel="", ylabel=""):
        for v in xs:
            px = self.x(v)
            self.out.append(f'<line x1="{px:.1f}" y1="{B}" x2="{px:.1f}" y2="{T}" stroke="{GRID}" stroke-width="0.6"/>'
                            f'<text x="{px:.1f}" y="{B + 15}" text-anchor="middle" fill="{MUTE}">{xfmt(v)}</text>')
        for v in ys:
            py = self.y(v)
            self.out.append(f'<line x1="{L}" y1="{py:.1f}" x2="{R}" y2="{py:.1f}" stroke="{GRID}" stroke-width="0.6"/>'
                            f'<text x="{L - 7}" y="{py + 3.5:.1f}" text-anchor="end" fill="{MUTE}">{yfmt(v)}</text>')
        if xlabel:
            self.out.append(f'<text x="{(L + R) / 2}" y="{B + 32}" text-anchor="middle" fill="{MUTE}">{xlabel}</text>')
        if ylabel:
            self.out.append(f'<text x="16" y="{(T + B) / 2}" text-anchor="middle" fill="{MUTE}" '
                            f'transform="rotate(-90 16 {(T + B) / 2})">{ylabel}</text>')

    def line(self, pts, color, width=1.8, dash=None):
        d = " ".join(f"{'M' if i == 0 else 'L'}{self.x(a):.1f},{self.y(b):.1f}" for i, (a, b) in enumerate(pts))
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da}/>')

    def band(self, lo, hi, color, opacity):
        top = " ".join(f"L{self.x(a):.1f},{self.y(b):.1f}" for a, b in hi)
        bot = " ".join(f"L{self.x(a):.1f},{self.y(b):.1f}" for a, b in reversed(lo))
        d = "M" + top[1:] + " " + bot + " Z"
        self.out.append(f'<path d="{d}" fill="{color}" opacity="{opacity}" stroke="none"/>')

    def dot(self, a, b, color, label=None, dx=6, dy=-6, anchor="start"):
        self.out.append(f'<circle cx="{self.x(a):.1f}" cy="{self.y(b):.1f}" r="3.2" fill="{color}"/>')
        if label:
            self.out.append(f'<text x="{self.x(a) + dx:.1f}" y="{self.y(b) + dy:.1f}" fill="{color}" '
                            f'text-anchor="{anchor}">{label}</text>')

    def text(self, a, b, s, color=MUTE, anchor="start", size=11):
        self.out.append(f'<text x="{self.x(a):.1f}" y="{self.y(b):.1f}" fill="{color}" '
                        f'text-anchor="{anchor}" font-size="{size}">{s}</text>')

    def vline(self, a, color, label=None):
        px = self.x(a)
        self.out.append(f'<line x1="{px:.1f}" y1="{B}" x2="{px:.1f}" y2="{T}" stroke="{color}" '
                        f'stroke-width="1.1" stroke-dasharray="4 3"/>')
        if label:
            self.out.append(f'<text x="{px + 4:.1f}" y="{T + 12}" fill="{color}">{label}</text>')

    def svg(self, foot):
        self.out.append(f'<text x="{L}" y="{H - 6}" fill="{MUTE}" font-size="10">{foot}</text></svg>')
        return "".join(self.out)


def fig1():
    p = Plot("Figure 1 · The 95% interval on a true 0.2R edge narrows with the square root of n",
             (20, 1200), (-0.4, 0.8), xlog=True)
    p.grid([30, 50, 100, 150, 200, 400, 1000], [-0.4, -0.2, 0, 0.2, 0.4, 0.6, 0.8],
           yfmt=lambda v: f"{v:+.1f}R" if v else "0", xlabel="decisions (log scale)",
           ylabel="measured expectancy")
    ns = [20 * (1200 / 20) ** (i / 200) for i in range(201)]
    p.band([(n, 0.2 - 2 / math.sqrt(n)) for n in ns], [(n, 0.2 + 2 / math.sqrt(n)) for n in ns], C1, 0.18)
    p.line([(20, 0.2), (1200, 0.2)], C1)
    p.line([(20, 0), (1200, 0)], RED, 1.1, "4 3")
    for n in (30, 50, 150, 200, 400, 1000):
        se = 1 / math.sqrt(n)
        p.dot(n, 0.2 - 2 * se, C1)
        p.dot(n, 0.2 + 2 * se, C1, f"n {n}: {0.2 - 2 * se:+.2f} to {0.2 + 2 * se:+.2f}",
              dy=-8, anchor="middle")
    p.text(21, 0.03, "zero", RED)
    return p.svg("Interval = 0.2 ± 2/√n, the per-decision spread taken as 1R (Chapter 1). "
                 "A year (≈200) cannot exclude much below +0.06R; 30 or 50 cannot exclude zero.")


def fig2():
    p = Plot("Figure 2 · A Sharpe of 1.0 and its error bar: one year cannot tell it from zero",
             (0.5, 20), (-2, 4))
    p.grid([1, 2, 5, 10, 15, 20], [-2, -1, 0, 1, 2, 3, 4], xlabel="years of data",
           ylabel="annualized Sharpe")
    ts = [0.5 + i * 0.1 for i in range(196)]
    se = lambda t: math.sqrt((1 + 0.5) / t)
    p.band([(t, 1 - 2 * se(t)) for t in ts], [(t, 1 + 2 * se(t)) for t in ts], C1, 0.12)
    p.band([(t, 1 - se(t)) for t in ts], [(t, 1 + se(t)) for t in ts], C1, 0.22)
    p.line([(0.5, 1), (20, 1)], C1)
    p.line([(0.5, 0), (20, 0)], RED, 1.1, "4 3")
    for t in (1, 5, 10):
        p.dot(t, 1 + se(t), C1, f"T {t}: SE {se(t):.2f}", dy=-8,
              anchor="start" if t < 10 else "middle")
    p.text(15, -1.55, "dark: ±1 SE   light: ±2 SE", MUTE)
    return p.svg("SE = √((1 + S²/2)/T) with S = 1 (Chapter 2): 1.22 at one year, 0.55 at five, "
                 "0.39 at ten, where one standard error spans about 0.6 to 1.4.")


def fig3():
    p = Plot("Figure 3 · The same evidence, three priors: a true 60% hit rate",
             (0, 500), (0.40, 0.70))
    p.grid([0, 30, 100, 200, 300, 400, 500], [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70],
           yfmt=lambda v: f"{v * 100:.0f}%", xlabel="decisions observed (wins at 60%)",
           ylabel="believed hit rate")
    ns = list(range(0, 501, 5))
    pri = (("weak prior", 3, 3, C3), ("sceptic: 80 at 50%", 40, 40, RED),
           ("mechanism: 40 at 60%", 24, 16, C2))
    p.line([(0, 0.6), (500, 0.6)], MUTE, 1.0, "4 3")
    for name, a, b, col in pri:
        p.line([(n, (a + 0.6 * n) / (a + b + n)) for n in ns], col)
        v30 = (a + 18) / (a + b + 30)
        p.dot(30, v30, col, f"{name}: {v30 * 100:.0f}% after 30", dx=8,
              dy=(-7 if name.startswith("mech") else (14 if name.startswith("scep") else -7)))
    p.text(420, 0.605, "truth 60%", MUTE)
    return p.svg("Posterior mean (a + wins)/(a + b + n) along the expected path: the weak prior "
                 "is at 58% after 30, the sceptic at 53%; the mechanism's prior starts at 60% (Chapter 9).")


def fig4():
    p = Plot("Figure 4 · Kelly under an uncertain edge: the growth-optimal fraction falls as the error bar grows",
             (0, 1.2), (0, 1.0))
    p.grid([0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2], [0, 0.25, 0.5, 0.75, 1.0],
           xfmt=lambda v: f"{v:.1f}", yfmt=lambda v: f"{v:.2f}",
           xlabel="the edge's standard error, as a share of the edge (s/m)",
           ylabel="fraction of full Kelly")
    xs = [i * 0.012 for i in range(101)]
    p.line([(x, 1 / (1 + x * x)) for x in xs], C1)
    p.line([(x, max(0.0, 1 - 2 * x)) for x in xs], C2)
    p.line([(0, 0.25), (1.2, 0.25)], RED, 1.1, "4 3")
    p.line([(0, 0.075), (1.2, 0.075)], MUTE, 1.0, "2 3")
    p.text(1.19, 0.27, "quarter-Kelly", RED, "end")
    p.text(1.19, 0.095, "the Doctrine's 0.75% against Kelly's 10%", MUTE, "end")
    p.text(0.62, 0.78, "shrinkage m²/(m²+s²)", C1)
    p.text(0.05, 0.32, "lower 2-SE bound, 1 − 2s/m", C2)
    for n, lab in ((1000, "1,000"), (200, "200"), (60, "60 effective"), (30, "30")):
        r = 1 / (0.2 * math.sqrt(n))
        p.vline(r, MUTE)
        p.text(r + 0.01, 0.93 if n != 60 else 0.86, f"n {lab}", MUTE)
    return p.svg("For a 0.2R edge, s/m = 1/(0.2√n). At a year's 200 decisions the bound rule sits near "
                 "a third of Kelly, and at the effective 60 of Chapter 3 near none (Chapter 14).")


def fig5():
    p = Plot("Figure 5 · Edge decay from week 40 is not distinguishable from noise until about week 65",
             (0, 100), (-0.3, 0.6))
    p.grid([0, 13, 26, 40, 52, 65, 78, 100], [-0.2, 0, 0.2, 0.4, 0.6],
           yfmt=lambda v: f"{v:+.1f}R" if v else "0", xlabel="week",
           ylabel="expectancy per decision")
    k = 0.2 / 26                                   # to zero at week 66
    edge = lambda w: 0.2 if w < 40 else max(0.0, 0.2 - k * (w - 40))
    se = 1 / math.sqrt(13 * 200 / 52)              # a 13-week window at 200 a year
    trail = lambda w: sum(edge(w - i) for i in range(13)) / 13
    ws = [w for w in range(13, 101)]
    p.band([(w, trail(w) - se) for w in ws], [(w, trail(w) + se) for w in ws], C1, 0.18)
    p.line([(w, trail(w)) for w in ws], C1)
    p.line([(w, edge(w)) for w in range(0, 101)], INK, 1.3, "5 3")
    p.line([(0, 0.2), (100, 0.2)], MUTE, 0.9, "2 3")
    p.vline(40, RED, "decay begins")
    first = next(w for w in ws if w > 40 and trail(w) + se < 0.2)
    p.vline(first, C2, f"week {first}: band excludes 0.2R")
    p.text(72, 0.47, "dashed: the true edge", INK)
    p.text(72, 0.40, "blue: trailing 13-week expectancy, ±1 SE", C1)
    return p.svg(f"Illustrative: 200 decisions a year (SE {se:.2f}R on 13 weeks); a 0.2R edge decaying "
                 f"linearly to zero by week 66. The band first excludes the old edge at week {first} (Chapter 15).")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for i, f in enumerate((fig1, fig2, fig3, fig4, fig5), 1):
        path = OUT / f"fig-{i:02d}.svg"
        path.write_text(f() + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(OUT.parents[2])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
