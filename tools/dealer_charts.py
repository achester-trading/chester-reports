"""
Dealer-positioning charts from a stored exposure JSON and its chain. (9 Oct 2026)

    python tools/dealer_charts.py --exposure data/chains/2026-10-08/SPY_202527Z_exposure.json \
        --chain data/chains/2026-10-08/SPY_202138Z.csv --out build/dealer/

    python tools/dealer_charts.py --exposure SPY.json --exposure QQQ.json \
        --chain SPY.csv --chain QQQ.csv --out build/dealer/

READ-ONLY. Reads the files it is given, writes PNGs to --out, touches no store.
Four figures, the ones ruled on 9 Oct 2026 from the 8 Oct SPY/QQQ captures:

  1_<sym>_per_strike.png   GEX by strike within +/- band of spot: calls (dealers
                           long, +gamma) and puts (dealers short, -gamma) as bars,
                           the net as a line; spot, zero-gamma, call wall, put wall
                           and max pain marked.
  2_gamma_profile.png      Net GEX if spot were X, every contract's gamma
                           re-priced at X with OI and IV held: the zero crossing
                           and the asymmetry either side of spot. One panel per
                           symbol.
  3_buckets_release.png    Net GEX ($ per 1%) by expiry bucket per symbol, and
                           the first symbol's expiration-release schedule (DEX
                           released at each of the next ten expiries, signed by
                           unwind direction).
  4_dex_horizon.png        Cumulative DEX by days to expiry (log), the 1-week /
                           1-month / 1-quarter marks.

UNITS AND SIGNS are the engine's (tools/exposure_compute.py, convention
dealers-hand-v1): per-strike `gex` is sigma sign*Gamma*OI*100*S in dollars; the
"$ per 1%" figures are that times 0.01*S; DEX is dealer-hand. A settled capture
excludes DTE 0 (the engine's rule), and the profile does the same.

The figures are a diagnostic today and the 6b dealer block's charts tomorrow:
daily_cascade/charts.py imports the draw_* functions when that build lands, so
nothing here reads config, prints prose or decides a flag.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.patches import Patch                  # noqa: E402
from matplotlib.ticker import FuncFormatter           # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exposure_compute as ec                         # noqa: E402

# --- palette: the report's light surface and categorical order ---------------
SURFACE = "#fcfcfb"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SERIES = (BLUE, ORANGE)                 # first symbol, second symbol
BUCKET_COL = {"weekly": BLUE, "monthly": AQUA, "quarterly": YELLOW, "other": MUTED,
              "0dte": ORANGE}
BUCKET_ORDER = ("weekly", "monthly", "quarterly", "other")

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": BASE, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "savefig.dpi": 160, "savefig.facecolor": SURFACE,
})


def _m(x: float) -> float:
    return x / 1e6


def _bn(x: float) -> float:
    return x / 1e9


def _style(ax) -> None:
    ax.grid(axis="x", visible=False)
    ax.tick_params(length=0)


def _level(ax, x, label, color=INK2, ls=(0, (4, 3)), y=0.97, ha="left", dx=1.0):
    ax.axvline(x, color=color, lw=1.0, ls=ls, zorder=3)
    ax.text(x + (dx if ha == "left" else -dx), y, label, color=color, fontsize=8.5,
            ha=ha, va="top", transform=ax.get_xaxis_transform(), zorder=4)


def _stamp(ex: dict) -> str:
    cap = "settled, 0DTE excluded" if ex.get("capture") == "settled_eod" else "intraday"
    return f"{ex.get('session_date', '')} capture {ex.get('fetched_at', '')[11:16]}Z ({cap})"


# ---------------------------------------------------------------- figure 1 --
def draw_per_strike(ex: dict, out: Path, band: float = 0.06) -> Path:
    sym, spot, ov = ex["symbol"], ex["spot"], ex["overall"]
    lo, hi = spot * (1 - band), spot * (1 + band)
    rows = [r for r in ex["per_strike"] if lo <= r["strike"] <= hi]
    xs = [r["strike"] for r in rows]
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.bar(xs, [_m(r["call_gex"]) for r in rows], width=0.8, color=BLUE,
           label="Calls (dealers long, +gamma)", zorder=2)
    ax.bar(xs, [_m(r["put_gex"]) for r in rows], width=0.8, color=ORANGE,
           label="Puts (dealers short, −gamma)", zorder=2)
    ax.plot(xs, [_m(r["gex"]) for r in rows], color=INK, lw=1.2, label="Net per strike", zorder=3)
    ax.axhline(0, color=BASE, lw=1)
    _level(ax, spot, f"spot {spot:.2f}", color=INK, ls="-")
    if ov.get("gamma_flip"):
        _level(ax, ov["gamma_flip"], f"flip {ov['gamma_flip']:.2f}", y=0.90)
    if ov.get("call_wall"):
        _level(ax, ov["call_wall"], f"call wall {ov['call_wall']:.0f}", color=BLUE)
    if ov.get("put_wall"):
        _level(ax, ov["put_wall"], f"put wall {ov['put_wall']:.0f}", color=ORANGE, ha="right")
    if ex.get("max_pain"):
        _level(ax, ex["max_pain"], f"max pain {ex['max_pain']:.0f}", color=MUTED, y=0.90, ha="right")
    ax.set_title(f"{sym} dealer gamma by strike — {_stamp(ex)}")
    ax.set_xlabel("Strike")
    ax.set_ylabel("GEX per strike, \\$M  (Γ·OI·100·S, dealer-hand sign)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    _style(ax)
    ax.legend(loc="lower left", frameon=False, fontsize=9)
    g1 = ov["dollar_gamma_per_1pct"]
    ax.text(0.99, 0.03, f"Net GEX all strikes {_m(ov['net_gex']):,.0f} \\$M  ·  "
            f"{'−' if g1 < 0 else '+'}\\${abs(_bn(g1)):.2f}bn per 1% move",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=9, color=INK2)
    fig.tight_layout()
    path = out / f"1_{sym.lower()}_per_strike.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------- figure 2 --
def gamma_profile(ex: dict, chain: Path, band: float = 0.08, steps: int = 161):
    rows = ec.load_chain(chain)
    if ex.get("capture") == "settled_eod":
        rows = [r for r in rows if (r.get("dte") or 0) > 0]
    spot, r = ex["spot"], ex["risk_free_rate"]
    xs = [spot * (1 - band + 2 * band * i / (steps - 1)) for i in range(steps)]
    return xs, [_m(ec.net_gex_at_spot(rows, x, r)) for x in xs]


def draw_profile(exs: list[dict], chains: list[Path], out: Path) -> Path:
    n = len(exs)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 4.8), squeeze=False)
    for ax, ex, chain, col in zip(axes[0], exs, chains, SERIES):
        xs, ys = gamma_profile(ex, chain)
        spot, flip = ex["spot"], ex["overall"].get("gamma_flip")
        ax.plot(xs, ys, color=col, lw=2, zorder=3)
        ax.fill_between(xs, ys, 0, where=[y < 0 for y in ys], color=ORANGE, alpha=0.10, lw=0)
        ax.fill_between(xs, ys, 0, where=[y >= 0 for y in ys], color=BLUE, alpha=0.10, lw=0)
        ax.axhline(0, color=BASE, lw=1)
        _level(ax, spot, f"spot {spot:.2f}", color=INK, ls="-", ha="right")
        if flip:
            _level(ax, flip, f"zero-gamma {flip:.2f}", y=0.90)
        now = _m(ex["overall"]["net_gex"])
        ax.plot([spot], [now], "o", ms=7, color=col, mec=SURFACE, mew=1.5, zorder=4)
        ax.annotate(f"today {now:,.0f} \\$M", (spot, now), xytext=(-8, -16),
                    textcoords="offset points", ha="right", fontsize=9, color=INK2)
        ax.set_title(f"{ex['symbol']}: net dealer gamma if spot were …")
        ax.set_xlabel("Hypothetical spot")
        ax.set_ylabel("Net GEX, \\$M")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
        _style(ax)
    fig.suptitle(f"Gamma profile across spot — {_stamp(exs[0])}, ±8% band",
                 fontsize=12, fontweight="bold", color=INK)
    fig.text(0.5, 0.01, "Below zero: negative gamma — dealers hedge with the move (amplify). "
             "Above: positive gamma — dealers hedge against it (dampen).\n"
             "Each point re-prices every contract's gamma at that hypothetical spot; OI and IV held at the capture.",
             ha="center", va="bottom", fontsize=8.5, color=INK2)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    path = out / "2_gamma_profile.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------- figure 3 --
def draw_buckets_release(exs: list[dict], out: Path, n_expiries: int = 10) -> Path:
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.8), gridspec_kw={"width_ratios": [1, 1.35]})
    xs = range(len(BUCKET_ORDER))
    w = 0.38 if len(exs) > 1 else 0.6
    for i, (ex, col) in enumerate(zip(exs, SERIES)):
        vals, shares = [], []
        for b in BUCKET_ORDER:
            bk = ex["buckets"].get(b) or {}
            vals.append(_bn(bk.get("dollar_gamma_per_1pct") or 0.0))
            shares.append(bk.get("share_of_total_abs_gex") or 0.0)
        pos = [x + (i - (len(exs) - 1) / 2) * (w + 0.02) for x in xs]
        ax.bar(pos, vals, width=w, color=col, label=ex["symbol"], zorder=2)
        for p, v, s in zip(pos, vals, shares):
            ax.text(p, v + (0.03 if v >= 0 else -0.03), f"{v:+.2f}\n{s:.0%}", ha="center",
                    va="bottom" if v >= 0 else "top", fontsize=8, color=INK2)
    ax.axhline(0, color=BASE, lw=1)
    labels = {"weekly": "Weekly\n≤7d", "monthly": "Monthly\n3rd Fridays",
              "quarterly": "Quarterly\nDec/Mar/Jun/Sep", "other": "Other\nlater Fridays,\nmonth-ends"}
    ax.set_xticks(list(xs), [labels[b] for b in BUCKET_ORDER], fontsize=9)
    ax.set_ylabel("Net dealer gamma, \\$bn per 1% move")
    ax.set_title("Net GEX by expiry bucket (share of |GEX| below)")
    ax.legend(frameon=False, loc="upper left")
    ax.margins(y=0.25)
    _style(ax)

    ex = exs[0]
    rel = ex["expiration_release"][:n_expiries]
    xs2 = range(len(rel))
    vals = [_bn(e["dex_notional"]) * (1 if e["unwind_direction"] == "dealer_buys" else -1) for e in rel]
    ax2.bar(list(xs2), vals, color=[BUCKET_COL.get(e["bucket"], MUTED) for e in rel], width=0.7, zorder=2)
    for x, v, e in zip(xs2, vals, rel):
        ax2.text(x, v + (0.3 if v >= 0 else -0.3), f"{v:.1f}\n{e['share_of_abs_dex']:.1%}", ha="center",
                 va="bottom" if v >= 0 else "top", fontsize=8, color=INK2)
    ax2.set_xticks(list(xs2), [f"{e['expiry'][5:]}\n{e['dte']}d" for e in rel], fontsize=8.5)
    ax2.axhline(0, color=BASE, lw=1)
    ax2.set_ylabel("Delta hedge released, \\$bn (+ = dealers buy back)")
    ax2.set_title(f"{ex['symbol']} expiration-release schedule, next {len(rel)} expiries (share of |DEX|)")
    ax2.legend(handles=[Patch(color=BUCKET_COL[b], label=b) for b in BUCKET_ORDER
                        if any(e["bucket"] == b for e in rel)], frameon=False, loc="upper right")
    ax2.margins(y=0.25)
    _style(ax2)
    fig.tight_layout()
    path = out / "3_buckets_release.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------- figure 4 --
def draw_dex_horizon(exs: list[dict], out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 4.6))
    for ex, col, up in zip(exs, SERIES, (1, -1)):
        rel = sorted(ex["expiration_release"], key=lambda e: e["dte"])
        dte, cum, run = [0], [0.0], 0.0
        for e in rel:
            run += _bn(e["dex_notional"])
            dte.append(e["dte"])
            cum.append(run)
        ax.step(dte, cum, where="post", color=col, lw=2, label=ex["symbol"], zorder=3)
        ax.annotate(f"{ex['symbol']} {_bn(ex['overall']['dex_notional']):.0f}bn", (dte[-1], cum[-1]),
                    xytext=(6, 10 * up), textcoords="offset points", color=col, va="center",
                    fontsize=9, fontweight="bold")
        for k in (7, 30, 90):
            v = sum(_bn(e["dex_notional"]) for e in rel if e["dte"] <= k)
            ax.plot([k], [v], "o", ms=6, color=col, mec=SURFACE, mew=1.2, zorder=4)
            ax.annotate(f"{v:.0f}", (k, v), xytext=(0, 8 if up > 0 else -14),
                        textcoords="offset points", ha="center", fontsize=8.5, color=INK2)
    for k, lab in ((7, "1 wk"), (30, "1 mo"), (90, "1 qtr")):
        ax.axvline(k, color=GRID, lw=1, ls=(0, (3, 3)))
        ax.text(k, 0.97, lab, transform=ax.get_xaxis_transform(), ha="center", va="top",
                fontsize=8.5, color=MUTED)
    ax.set_xscale("log")
    ticks = [1, 2, 4, 7, 14, 30, 60, 90, 180, 365, 730]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(t) for t in ticks])
    ax.set_xlabel("Days to expiry (log)")
    ax.set_ylabel("Cumulative dealer delta exposure, \\$bn")
    ax.set_title(f"DEX by horizon — how much delta hedge rolls off, and when ({_stamp(exs[0])})")
    ax.legend(frameon=False, loc="upper left")
    ax.set_xlim(0.9, 1300)
    _style(ax)
    fig.tight_layout()
    path = out / "4_dex_horizon.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exposure", action="append", required=True, help="exposure JSON (compute_symbol output); repeatable, first is primary")
    ap.add_argument("--chain", action="append", default=[], help="chain CSV matching each --exposure, in order (needed for the profile)")
    ap.add_argument("--out", required=True, help="output directory for the PNGs")
    ap.add_argument("--band", type=float, default=0.06, help="per-strike chart band around spot (default 0.06)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    exs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in a.exposure][:2]
    chains = [Path(c) for c in a.chain][:2]
    made = [draw_per_strike(ex, out, a.band) for ex in exs]
    if len(chains) == len(exs):
        made.append(draw_profile(exs, chains, out))
    else:
        print("profile skipped: give one --chain per --exposure", file=sys.stderr)
    made.append(draw_buckets_release(exs, out))
    made.append(draw_dex_horizon(exs, out))
    for p in made:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
