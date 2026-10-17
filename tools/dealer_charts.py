"""
Dealer-positioning charts from a stored exposure JSON and its chain. (9 Oct 2026)

    python tools/dealer_charts.py --exposure data/chains/2026-10-08/SPY_202527Z_exposure.json \
        --chain data/chains/2026-10-08/SPY_202138Z.csv --out build/dealer/

    python tools/dealer_charts.py --exposure SPY.json --exposure QQQ.json \
        --chain SPY.csv --chain QQQ.csv --out build/dealer/

READ-ONLY. Reads the files it is given, writes PNGs to --out, touches no store.
Four figures, the ones ruled on 9 Oct 2026 from the 8 Oct SPY/QQQ captures:

  1_<sym>_per_strike.png   GEX by strike within +/- band of spot: calls (+gamma
                           under the convention) and puts (-gamma) as bars, the net
                           as a line; spot, zero-gamma and the OTM walls marked
                           (audit F5: the OTM walls are THE walls).
  2_gamma_profile.png      Net GEX if spot were X, every contract's gamma
                           re-priced at X with OI and IV held: the zero crossing
                           and the asymmetry either side of spot. One panel per
                           symbol.
  3_buckets_release.png    Call- and put-gamma mass by exclusive band (0DTE, 1-7,
                           8-45, > 45; 6b part 2), and
                           the first symbol's expiration-release schedule: the
                           SIZE of delta hedge attached to each of the next ten
                           expiries. No direction is drawn: under dealers-hand-v1
                           every expiry's DEX is positive by construction, so
                           "dealer buys" would be a tautology, not a forecast
                           (audit of 9 Oct 2026, finding F3).
  4_dex_horizon.png        Cumulative DEX by days to expiry (log), the 1-week /
                           1-month / 1-quarter marks.

UNITS AND SIGNS are the engine's (tools/exposure_compute.py, convention
dealers-hand-v1): per-strike `gex` is sigma sign*Gamma*OI*100*S in dollars; the
"$ per 1%" figures are that times 0.01*S; DEX is dealer-hand and therefore a
SIZE, never a direction. A settled capture excludes DTE 0 (the engine's rule),
and the profile does the same. The profile holds IV fixed per contract (sticky
strike); a skew tilt moves the at-spot magnitude, not the slope's sign.

The figures are a diagnostic today and the 6b dealer block's charts tomorrow:
daily_cascade/charts.py imports the draw_* functions (6b part 2): each takes an
`ax` and then draws into it and returns what it drew, so the report's chart and
its tables reconcile. Nothing here reads config, prints prose or decides a flag;
no figure draws a direction for DEX or the roll-off (audit F3).
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

# The figures' style, applied by the CLI (main) and by daily_cascade/charts.py
# inside an rc_context -- never at import, so importing this module does not
# restyle the report's other charts.
RC = {
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": BASE, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "savefig.dpi": 160, "savefig.facecolor": SURFACE,
}


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
    """Every figure's stamp (brief v2 section 3): the capture time, settled or
    intraday, and the OI vintage."""
    cap = "settled, 0DTE excluded" if ex.get("capture") == "settled_eod" else "intraday"
    return (f"{ex.get('session_date', '')} capture {str(ex.get('fetched_at') or '')[11:16]}Z "
            f"({cap}; OI as of prior close)")


def _fig_or(ax, size):
    """(fig, ax, own): a new figure when no axis is given."""
    if ax is not None:
        return ax.figure, ax, False
    fig, ax = plt.subplots(figsize=size)
    return fig, ax, True


def _save(fig, out: Path, name: str) -> Path:
    fig.tight_layout()
    path = Path(out) / name
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------- figure 1 --
def draw_per_strike(ex: dict, out: Path = None, band: float = 0.06, ax=None):
    """GEX by strike within +/- band of spot, the OTM walls marked as THE walls
    (audit F5; the all-strike extremes are peaks and are not drawn as walls).
    With `ax`, draws there and returns what it drew; else writes the PNG."""
    sym, spot, ov = ex["symbol"], ex["spot"], ex["overall"]
    lo, hi = spot * (1 - band), spot * (1 + band)
    rows = [r for r in ex.get("per_strike") or [] if lo <= r["strike"] <= hi]
    xs = [r["strike"] for r in rows]
    fig, ax, own = _fig_or(ax, (11, 5.2))
    width = 0.8 * (min((b - a) for a, b in zip(xs, xs[1:])) if len(xs) > 1 else 1.0)
    ax.bar(xs, [_m(r["call_gex"]) for r in rows], width=width, color=BLUE,
           label="Calls (+gamma under the convention)", zorder=2)
    ax.bar(xs, [_m(r["put_gex"]) for r in rows], width=width, color=ORANGE,
           label="Puts (−gamma under the convention)", zorder=2)
    ax.plot(xs, [_m(r["gex"]) for r in rows], color=INK, lw=1.2, label="Net per strike",
            zorder=3)
    ax.axhline(0, color=BASE, lw=1)
    drawn = {"spot": spot}
    _level(ax, spot, f"spot {spot:.2f}", color=INK, ls="-")
    for key, lab, col, ha, y in (("gamma_flip", "zero-gamma", INK2, "left", 0.90),
                                 ("call_wall_otm", "OTM call wall", BLUE, "left", 0.97),
                                 ("put_wall_otm", "OTM put gamma wall", ORANGE, "right", 0.97)):
        v = ov.get(key)
        if v is not None:
            _level(ax, v, f"{lab} {v:,.2f}", color=col, ha=ha, y=y)
            drawn[key] = v
    ax.set_title(f"{sym} dealer gamma by strike — {_stamp(ex)}")
    ax.set_xlabel("Strike")
    ax.set_ylabel("GEX per strike, \\$M")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    _style(ax)
    ax.legend(loc="lower left", frameon=False, fontsize=9)
    drawn["strikes"] = xs
    if not own:
        return drawn
    return _save(fig, out, f"1_{sym.lower()}_per_strike.png")


# ---------------------------------------------------------------- figure 2 --
def gamma_profile(ex: dict, chain: Path = None, band: float = 0.08, steps: int = 161):
    """(spots, net GEX $M): the profile the engine stored (`gamma_profile`),
    else re-priced from the chain CSV (the CLI's older captures)."""
    gp = ex.get("gamma_profile") or {}
    if gp.get("spots"):
        return list(gp["spots"]), [_m(v) for v in gp["net_gex"]]
    rows = ec.load_chain(chain)
    if ex.get("capture") == "settled_eod":
        rows = [r for r in rows if (r.get("dte") or 0) > 0]
    spot, r = ex["spot"], ex["risk_free_rate"]
    xs = [spot * (1 - band + 2 * band * i / (steps - 1)) for i in range(steps)]
    return xs, [_m(ec.net_gex_at_spot(rows, x, r)) for x in xs]


PROFILE_NOTE = ("Below zero: negative gamma — dealer hedging leans with the move. "
                "Above: positive gamma — hedging leans against it.\n"
                "Each point re-prices every contract's gamma at that hypothetical "
                "spot; OI and IV held at the capture.")


def _profile_ax(ax, ex: dict, chain, col) -> dict:
    xs, ys = gamma_profile(ex, chain)
    spot, flip = ex["spot"], ex["overall"].get("gamma_flip")
    ax.plot(xs, ys, color=col, lw=2, zorder=3)
    ax.fill_between(xs, ys, 0, where=[y < 0 for y in ys], color=ORANGE, alpha=0.10, lw=0)
    ax.fill_between(xs, ys, 0, where=[y >= 0 for y in ys], color=BLUE, alpha=0.10, lw=0)
    ax.axhline(0, color=BASE, lw=1)
    _level(ax, spot, f"spot {spot:.2f}", color=INK, ls="-", ha="right")
    if flip:
        _level(ax, flip, f"zero-gamma {flip:.2f}", y=0.90)
    now = _m(ex["overall"]["net_gex"]) if ex["overall"].get("net_gex") is not None else None
    if now is not None:
        ax.plot([spot], [now], "o", ms=7, color=col, mec=SURFACE, mew=1.5, zorder=4)
        ax.annotate(f"today {now:,.0f} \\$M", (spot, now), xytext=(-8, -16),
                    textcoords="offset points", ha="right", fontsize=9, color=INK2)
    ax.set_title(f"{ex['symbol']}: net dealer gamma if spot were …")
    ax.set_xlabel("Hypothetical spot")
    ax.set_ylabel("Net GEX, \\$M")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    _style(ax)
    return {"spots": xs, "net_gex_m": ys, "flip": flip, "spot": spot, "at_spot_m": now}


def draw_profile(exs: list[dict], chains: list = None, out: Path = None, ax=None):
    """Figure 2. With `ax`, the first symbol's panel there, returning what it
    drew; else one panel per symbol, written to the PNG."""
    chains = list(chains or []) + [None] * len(exs)
    if ax is not None:
        return _profile_ax(ax, exs[0], chains[0], SERIES[0])
    n = len(exs)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 4.8), squeeze=False)
    for a, ex, chain, col in zip(axes[0], exs, chains, SERIES):
        _profile_ax(a, ex, chain, col)
    fig.suptitle(f"Gamma profile across spot — {_stamp(exs[0])}, ±8% band",
                 fontsize=12, fontweight="bold", color=INK)
    fig.text(0.5, 0.01, PROFILE_NOTE, ha="center", va="bottom", fontsize=8.5, color=INK2)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    path = Path(out) / "2_gamma_profile.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------- figure 3 --
BAND_COL = {"b0": ORANGE, "b1_7": BLUE, "b8_45": AQUA, "b46": YELLOW}


def _bands_ax(ax, ex: dict) -> dict:
    """The exclusive bands (0DTE, 1-7, 8-45, > 45; brief v2 section 2) as call-
    and put-gamma mass, $bn per 1%: sizes, no sign. A settled 0DTE band says so."""
    bands = list((ex.get("bands") or {}).values())
    labels, calls, puts = [], [], []
    for b in bands:
        labels.append(b["label"] + ("\nsettled,\nexcluded" if b.get("excluded") else ""))
        calls.append(_bn(b.get("call_gamma_per_1pct") or 0.0))
        puts.append(_bn(b.get("put_gamma_per_1pct") or 0.0))
    xs = list(range(len(bands)))
    ax.bar([x - 0.2 for x in xs], calls, width=0.4, color=BLUE, label="Call-gamma mass", zorder=2)
    ax.bar([x + 0.2 for x in xs], puts, width=0.4, color=ORANGE, label="Put-gamma mass", zorder=2)
    ax.set_xticks(xs, labels, fontsize=9)
    ax.set_ylabel("\\$bn per 1% move")
    ax.set_title("Gamma by days to expiry (exclusive bands)")
    ax.legend(frameon=False, loc="upper right")
    _style(ax)
    return {"bands": [b["id"] for b in bands], "call_bn": calls, "put_bn": puts}


def _release_ax(ax, ex: dict, n_expiries: int = 10) -> dict:
    """The hedge rolling off by expiry, as a SIZE (audit F3): the DEX attached
    to each of the next expiries, $bn, with no direction."""
    rel = (ex.get("expiration_release") or [])[:n_expiries]
    xs = list(range(len(rel)))
    vals = [abs(_bn(e["dex_notional"])) for e in rel]
    ax.bar(xs, vals, color=[BUCKET_COL.get(e["bucket"], MUTED) for e in rel], width=0.7,
           zorder=2)
    for x, v, e in zip(xs, vals, rel):
        ax.text(x, v, f"{v:.1f}", ha="center", va="bottom", fontsize=8, color=INK2)
    ax.set_xticks(xs, [f"{e['expiry'][5:]}\n{e['dte']}d" for e in rel], fontsize=8.5)
    ax.set_ylabel("Hedge attached, \\$bn (size)")
    ax.set_title(f"{ex['symbol']} hedge rolling off by expiry, next {len(rel)}")
    _style(ax)
    return {"expiries": [e["expiry"] for e in rel], "size_bn": vals}


def draw_buckets_release(exs: list[dict], out: Path = None, n_expiries: int = 10,
                         ax=None, ax2=None):
    """Figure 3: the exclusive bands and the hedge rolling off by expiry,
    magnitude only (F3). With `ax` and `ax2`, draws the first symbol's two
    panels there and returns what it drew; else writes the PNG."""
    ex = exs[0]
    if ax is not None:
        return {**_bands_ax(ax, ex), **_release_ax(ax2, ex, n_expiries)}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.8),
                                 gridspec_kw={"width_ratios": [1, 1.35]})
    _bands_ax(a1, ex)
    _release_ax(a2, ex, n_expiries)
    fig.suptitle(_stamp(ex), fontsize=10, color=INK2)
    return _save(fig, out, "3_buckets_release.png")


# ---------------------------------------------------------------- figure 4 --
def _horizon_ax(ax, ex: dict, col=BLUE, up: int = 1) -> dict:
    rel = sorted(ex.get("expiration_release") or [], key=lambda e: e["dte"])
    dte, cum, run = [0], [0.0], 0.0
    for e in rel:
        run += abs(_bn(e["dex_notional"]))
        dte.append(max(e["dte"], 1))
        cum.append(run)
    ax.step(dte, cum, where="post", color=col, lw=2, label=ex["symbol"], zorder=3)
    marks = {}
    for k in (7, 30, 90):
        v = sum(abs(_bn(e["dex_notional"])) for e in rel if e["dte"] <= k)
        marks[k] = v
        ax.plot([k], [v], "o", ms=6, color=col, mec=SURFACE, mew=1.2, zorder=4)
        ax.annotate(f"{v:.0f}", (k, v), xytext=(0, 8 if up > 0 else -14),
                    textcoords="offset points", ha="center", fontsize=8.5, color=INK2)
    for k, lab in ((7, "1 wk"), (30, "1 mo"), (90, "1 qtr")):
        ax.axvline(k, color=GRID, lw=1, ls=(0, (3, 3)))
        ax.text(k, 0.97, lab, transform=ax.get_xaxis_transform(), ha="center", va="top",
                fontsize=8.5, color=MUTED)
    ax.set_xscale("log")
    ticks = [1, 7, 30, 90, 365]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(t) for t in ticks])
    ax.set_xlabel("Days to expiry (log)")
    ax.set_ylabel("Cumulative hedge book, \\$bn")
    ax.set_title("The hedge book by horizon (size, and when it rolls off)")
    ax.set_xlim(0.9, 1300)
    _style(ax)
    return {"cumulative_bn": cum[-1] if cum else 0.0, "marks_bn": marks}


def draw_dex_horizon(exs: list[dict], out: Path = None, ax=None):
    """Figure 4: the hedge book by horizon -- a size and a tenor, never a
    direction. With `ax`, the first symbol there, returning what it drew."""
    if ax is not None:
        return _horizon_ax(ax, exs[0])
    fig, ax = plt.subplots(figsize=(10, 4.6))
    for ex, col, up in zip(exs, SERIES, (1, -1)):
        _horizon_ax(ax, ex, col, up)
    ax.legend(frameon=False, loc="upper left")
    fig.suptitle(_stamp(exs[0]), fontsize=10, color=INK2)
    return _save(fig, out, "4_dex_horizon.png")


# ---------------------------------------------------------------- figure 5 --
def draw_scorecard(rates: list[dict], out: Path = None, ax=None):
    """Figure 5 (6b part 3; brief v2 section 3): each registered hypothesis's
    k/n with its Wilson 95% interval, the base rate and the baseline beside it.
    A hypothesis under the printing floor (20 scored sessions) draws no bar and
    says so; nothing here is a reading before promotion."""
    fig, ax, own = _fig_or(ax, (10, 4.6))
    labels, drawn = [], []
    for i, r in enumerate(rates):
        labels.append(f"{r['label']}\n{r['k']}/{r['n']}")
        if r.get("printable") and r.get("interval"):
            p = r["k"] / r["n"]
            lo, hi = r["interval"]
            ax.bar(i, p * 100, width=0.55, color=BLUE, zorder=2)
            ax.plot([i, i], [lo * 100, hi * 100], color=INK, lw=1.4, zorder=3)
            for key, mk, col in (("base_rate", "_", ORANGE), ("baseline", "x", AQUA)):
                if r.get(key) is not None:
                    ax.plot([i], [r[key] * 100], marker=mk, ms=14 if mk == "_" else 7,
                            mew=2, color=col, zorder=4, ls="none")
            drawn.append({"hypothesis": r["hypothesis"], "rate": p, "interval": (lo, hi),
                          "base_rate": r.get("base_rate"), "baseline": r.get("baseline")})
        else:
            ax.text(i, 3, "under 20\nscored", ha="center", va="bottom", fontsize=8,
                    color=MUTED)
            drawn.append({"hypothesis": r["hypothesis"], "rate": None})
    ax.set_xticks(range(len(rates)), labels, fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Hit rate, % (Wilson 95%)")
    ax.set_title("The scorecard: k/n, base rate (–) and baseline (×); none promoted")
    _style(ax)
    if not own:
        return {"rates": drawn}
    return _save(fig, out, "5_scorecard.png")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exposure", action="append", required=True, help="exposure JSON (compute_symbol output); repeatable, first is primary")
    ap.add_argument("--chain", action="append", default=[], help="chain CSV matching each --exposure, in order (needed for the profile)")
    ap.add_argument("--out", required=True, help="output directory for the PNGs")
    ap.add_argument("--band", type=float, default=0.06, help="per-strike chart band around spot (default 0.06)")
    a = ap.parse_args(argv)
    plt.rcParams.update(RC)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    exs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in a.exposure][:2]
    chains = [Path(c) for c in a.chain][:2]
    made = [draw_per_strike(ex, out, a.band) for ex in exs]
    if len(chains) == len(exs) or all(ex.get("gamma_profile") for ex in exs):
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
