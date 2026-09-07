"""
FX long-history charts for the Currencies white paper (VIII).

Fetches 30 years of daily FX history, caches it, renders the eight
house-style figures (per-currency two-panel + the comparative
envelope-vs-gold figure), and injects them into the white paper HTML —
replacing whatever fx figures are already there, so the command is
idempotent and re-runnable whenever you want the charts refreshed.

Usage
-----
    # with network (home machine):
    python -m altdata.report.fx_charts --html currency-white-paper.html

    # no network / no FRED reachable — falls back to the reconstructed
    # anchor dataset and says so in the captions:
    python -m altdata.report.fx_charts --html currency-white-paper.html --offline

    # just refresh the cache / just write SVGs without touching the HTML:
    python -m altdata.report.fx_charts --fetch-only
    python -m altdata.report.fx_charts --svg-dir figs/

Data paths, in order of preference per series:
  1. fredgraph.csv  — https://fred.stlouisfed.org/graph/fredgraph.csv?id=X
     Full history, no API key. Primary path.
  2. FRED API       — if FRED_API_KEY is set (same key the sources/fred.py
     fetcher uses), observation_start=1995-01-01.
  3. yfinance       — only for DXY ("DX-Y.NYB") and gold ("GC=F"), which FRED
     lacks. Optional import; skipped if not installed.
  4. packaged anchors (fx_anchors.py) — the reconstructed dataset shipped with
     the repo. Always available; used per-series when 1–3 all fail, or for
     everything under --offline.

Design notes:
  * Cache is one CSV per series under <cache-dir>/fx_history/ (default:
    ./data/fx_history/). A cached file younger than --max-age-days (default 7)
    is used without a network call, so this can run in the weekly cron next to
    weekly_scan without hammering FRED.
  * 30-year panels are drawn at month-end resolution, 5-year panels at
    week-end resolution, with the TRUE daily extremes computed from the raw
    daily series and marked as dots — light SVGs, honest ranges.
  * Every fetcher degrades to a no-op + fallback rather than raising; the one
    thing this module refuses to do is silently present anchors as daily data:
    the caption always states which source drew the figure.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import os
import re
import sys

import pandas as pd

# matplotlib configured for SVG, no display
import matplotlib

matplotlib.use("SVG")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import MultipleLocator  # noqa: E402

from . import fx_anchors  # packaged reconstructed dataset

# ---------------------------------------------------------------------------
# Series catalogue
# ---------------------------------------------------------------------------

FREDGRAPH = "https://fred.stlouisfed.org/graph/fredgraph.csv"
FRED_API = "https://api.stlouisfed.org/fred/series/observations"

# key -> (display name, FRED id or None, yfinance ticker or None,
#         direction note, anchor key, quoted-as)
# quoted-as: "usd_per_unit" (EUR, GBP) or "unit_per_usd" (JPY, CHF, CNY, THB)
CATALOG = {
    "DXY":  ("US Dollar Index (DXY)", None, "DX-Y.NYB", "up = dollar stronger", "DXY",  "index"),
    "DXYB": ("US Dollar Index (Fed broad)", "DTWEXBGS", None, "up = dollar stronger", "DXY", "index"),
    "EUR":  ("EUR/USD", "DEXUSEU", None, "up = euro stronger",     "EUR", "usd_per_unit"),
    "JPY":  ("USD/JPY", "DEXJPUS", None, "up = yen weaker",        "JPY", "unit_per_usd"),
    "GBP":  ("GBP/USD", "DEXUSUK", None, "up = sterling stronger", "GBP", "usd_per_unit"),
    "CHF":  ("USD/CHF", "DEXSZUS", None, "up = franc weaker",      "CHF", "unit_per_usd"),
    "CNY":  ("USD/CNY", "DEXCHUS", None, "up = yuan weaker",       "CNY", "unit_per_usd"),
    "THB":  ("USD/THB", "DEXTHUS", None, "up = baht weaker",       "THB", "unit_per_usd"),
    "GOLD": ("Gold (USD/oz)", None, "GC=F", "", "GOLD", "usd_per_unit"),
}

FIGURE_KEYS = ["DXY", "EUR", "JPY", "GBP", "CHF", "CNY", "THB"]  # per-currency figs
START = dt.date(1995, 9, 1)  # thirty-one years of runway

# House palette
NAVY, BURG, GREEN, AMBER = "#0f2747", "#9E2B25", "#2F5E3A", "#8A5A12"
PAPER, SURF, GRID, INK = "#FAFAF9", "#F4F2EC", "#d8d4ca", "#22303f"

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["DejaVu Serif"],
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK, "ytick.color": INK, "font.size": 11,
    "figure.facecolor": PAPER, "axes.facecolor": PAPER,
    "svg.fonttype": "none", "axes.unicode_minus": False,
})


# ---------------------------------------------------------------------------
# Fetch + cache
# ---------------------------------------------------------------------------

def _cache_path(cache_dir: str, name: str) -> str:
    return os.path.join(cache_dir, f"{name}.csv")


def _fresh(path: str, max_age_days: int) -> bool:
    if not os.path.exists(path):
        return False
    age = dt.date.today() - dt.date.fromtimestamp(os.path.getmtime(path))
    return age.days <= max_age_days


def _parse_fred_csv(text: str) -> pd.Series | None:
    """fredgraph.csv: DATE,<ID> with '.' for missing."""
    try:
        df = pd.read_csv(io.StringIO(text), na_values=["."])
    except Exception:
        return None
    if df.shape[1] < 2 or df.empty:
        return None
    df.columns = ["date", "value"] + list(df.columns[2:])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    s = (df.dropna(subset=["date", "value"])
           .set_index("date")["value"].astype(float).sort_index())
    return s if len(s) else None


def _fetch_fredgraph(series_id: str) -> pd.Series | None:
    try:
        import requests
        r = requests.get(FREDGRAPH, params={"id": series_id}, timeout=30)
        r.raise_for_status()
        return _parse_fred_csv(r.text)
    except Exception as e:  # pragma: no cover - network dependent
        print(f"    fredgraph {series_id}: {e.__class__.__name__} — skipping")
        return None


def _fetch_fred_api(series_id: str) -> pd.Series | None:
    key = os.environ.get("FRED_API_KEY")
    if not key:
        return None
    try:
        import requests
        r = requests.get(FRED_API, params={
            "series_id": series_id, "api_key": key, "file_type": "json",
            "observation_start": START.isoformat()}, timeout=30)
        r.raise_for_status()
        obs = r.json().get("observations", [])
        rows = [(o["date"], o["value"]) for o in obs
                if o.get("value") not in (None, ".", "")]
        if not rows:
            return None
        df = pd.DataFrame(rows, columns=["date", "value"])
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index("date")["value"].astype(float).sort_index()
    except Exception as e:  # pragma: no cover
        print(f"    fred api {series_id}: {e.__class__.__name__} — skipping")
        return None


def _fetch_yf(ticker: str) -> pd.Series | None:
    try:
        import yfinance as yf
        df = yf.download(ticker, start=START.isoformat(), progress=False,
                         auto_adjust=False)
        if df is None or df.empty:
            return None
        col = "Close" if "Close" in df else df.columns[0]
        s = df[col]
        if isinstance(s, pd.DataFrame):  # multi-index safety
            s = s.iloc[:, 0]
        return s.dropna().astype(float).sort_index()
    except Exception as e:  # pragma: no cover
        print(f"    yfinance {ticker}: {e.__class__.__name__} — skipping")
        return None


def load_series(key: str, cache_dir: str, max_age_days: int = 7,
                offline: bool = False) -> tuple[pd.Series, pd.Series, str]:
    """Return (long_series, five_year_series, source_tag). source_tag in
    {'fred:<ID>', 'yf:<ticker>', 'anchors', 'cache'}. For fetched daily data
    the five-year series is simply the last ~5.6y slice of the long one; for
    the packaged anchors it is the separate quarterly-resolution set."""
    name, fred_id, yf_ticker, *_ = CATALOG[key]
    os.makedirs(cache_dir, exist_ok=True)
    path = _cache_path(cache_dir, key)

    if not offline and _fresh(path, max_age_days):
        s = _parse_fred_csv(open(path).read())
        if s is not None:
            src = open(path + ".src").read().strip() if os.path.exists(path + ".src") else "cache"
            s = s[s.index.date >= START]
            return s, _five_slice(s), src

    if not offline:
        s, src = None, None
        if fred_id:
            s = _fetch_fredgraph(fred_id) or _fetch_fred_api(fred_id)
            src = f"fred:{fred_id}" if s is not None else None
        if s is None and yf_ticker:
            s = _fetch_yf(yf_ticker)
            src = f"yf:{yf_ticker}" if s is not None else None
        # DXY special case: fall back to the Fed broad index (2006+)
        if s is None and key == "DXY":
            s = _fetch_fredgraph("DTWEXBGS") or _fetch_fred_api("DTWEXBGS")
            src = "fred:DTWEXBGS" if s is not None else None
        if s is not None:
            s = s[s.index.date >= START]
            s.rename("value").rename_axis("date").reset_index().to_csv(path, index=False)
            open(path + ".src", "w").write(src)
            return s, _five_slice(s), src

    # last resort / offline: packaged anchors
    dts, vals = fx_anchors.anchor_series(key, "long")
    s = pd.Series(vals, index=pd.to_datetime(dts)).sort_index()
    dts5, vals5 = fx_anchors.anchor_series(key, "five")
    s5 = pd.Series(vals5, index=pd.to_datetime(dts5)).sort_index()
    return s, s5, "anchors"


def _five_slice(s: pd.Series) -> pd.Series:
    start = pd.Timestamp(dt.date.today() - dt.timedelta(days=int(5.6 * 365)))
    return s[s.index >= start]


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def _style_ax(ax, title):
    ax.set_title(title, fontsize=12.5, color=NAVY, loc="left", pad=8,
                 fontweight="bold")
    ax.grid(True, color=GRID, lw=0.6, alpha=0.7)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.margins(x=0.02)


def _mark(ax, when, val, label, up: bool):
    ax.scatter([when], [val], s=26, color=BURG, zorder=5)
    ax.annotate(label, (when, val), textcoords="offset points",
                xytext=(2, 10 if up else -24), fontsize=8.6, color=BURG,
                ha="left", linespacing=1.1)


def _extreme_label(s: pd.Series, idx) -> str:
    v = s.loc[idx]
    return f"{v:,.4g}\n{idx.strftime('%b %Y')}"


def fig_currency(key: str, s: pd.Series, five_raw: pd.Series, src: str,
                 out_dir: str) -> str:
    name, _, _, direction, *_ = CATALOG[key]
    is_daily = src != "anchors"
    five_start = five_raw.index.min()

    long_s = s.resample("ME").last().dropna() if is_daily else s
    five_s = five_raw.resample("W").last().dropna() if is_daily else five_raw

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.0, 6.6),
                                 gridspec_kw=dict(hspace=0.42))
    a1.plot(long_s.index, long_s.values, color=NAVY, lw=1.6)
    a1.axvspan(five_start, s.index.max() + pd.Timedelta(days=40),
               color=AMBER, alpha=0.12, lw=0)
    lo_i, hi_i = s.idxmin(), s.idxmax()
    lo, hi = float(s.min()), float(s.max())
    a1.axhline(lo, color=GREEN, lw=0.8, ls=(0, (4, 3)), alpha=0.8)
    a1.axhline(hi, color=BURG, lw=0.8, ls=(0, (4, 3)), alpha=0.8)
    _style_ax(a1, f"{name} — thirty years   ({direction})" if direction
                  else f"{name} — thirty years")
    mid = (hi + lo) / 2
    a1.text(0.995, -0.30,
            f"thirty-year range {lo:,.4g} to {hi:,.4g}  "
            f"(~{(hi - lo) / mid * 100:.0f}% of the midpoint)",
            transform=a1.transAxes, ha="right", fontsize=9, color=INK)
    ymid = mid
    _mark(a1, hi_i, hi, _extreme_label(s, hi_i), up=hi < ymid)
    _mark(a1, lo_i, lo, _extreme_label(s, lo_i), up=lo < ymid)

    a2.plot(five_s.index, five_s.values, color=NAVY, lw=1.9)
    base = five_s.min() - (five_s.max() - five_s.min()) * 0.06
    a2.fill_between(five_s.index, five_s.values, base, color=NAVY,
                    alpha=0.05, lw=0)
    _style_ax(a2, f"{name} — the last five years")
    f_lo_i, f_hi_i = five_raw.idxmin(), five_raw.idxmax()
    fmid = (five_raw.max() + five_raw.min()) / 2
    _mark(a2, f_hi_i, float(five_raw.max()),
          f"{five_raw.max():,.4g}", up=five_raw.max() < fmid)
    _mark(a2, f_lo_i, float(five_raw.min()),
          f"{five_raw.min():,.4g}", up=five_raw.min() < fmid)

    fig.text(0.01, 0.005,
             "Shaded band on the thirty-year panel = the five-year window below.",
             fontsize=8.4, color="#6b6a63")
    out = os.path.join(out_dir, f"fx_{key.lower()}.svg")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return _responsive(out)


def fig_comparative(series: dict[str, tuple[pd.Series, str]], out_dir: str) -> str:
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.0, 7.2),
                                 gridspec_kw=dict(hspace=0.45,
                                                  height_ratios=[1.15, 1]))
    colors = {"EUR": NAVY, "JPY": BURG, "GBP": GREEN, "CHF": AMBER,
              "CNY": "#5a5a8a", "THB": "#7a5d43"}
    for k, col in colors.items():
        s, src = series[k]
        m = (s.resample("ME").last().dropna() if src != "anchors" else s)
        quoted = CATALOG[k][5]
        base = m.iloc[0]
        vals = (m / base - 1) * 100 if quoted == "usd_per_unit" \
            else (base / m - 1) * 100
        a1.plot(m.index, vals.values, color=col, lw=1.5, label=k)
    a1.axhline(0, color=INK, lw=0.8)
    _style_ax(a1, "Value of each currency against the dollar — "
                  "cumulative % change since 1996 (EUR: 1999)")
    a1.set_ylabel("%")
    a1.legend(ncol=3, frameon=False, fontsize=9, loc="upper left",
              bbox_to_anchor=(0, 1.02), handlelength=1.2, columnspacing=1.0)
    a1.text(0.995, 0.03,
            "Devaluation-1: currencies oscillate against each other in a broad envelope",
            transform=a1.transAxes, ha="right", fontsize=8.6, color=INK,
            bbox=dict(fc=SURF, ec=GRID, pad=3))

    g, gsrc = series["GOLD"]
    gm = g.resample("ME").last().dropna() if gsrc != "anchors" else g
    a2.plot(gm.index, gm.values, color=AMBER, lw=2.0)
    a2.set_yscale("log")
    a2.set_yticks([250, 500, 1000, 2000, 4000])
    a2.set_yticklabels(["250", "500", "1,000", "2,000", "4,000"])
    _style_ax(a2, "The anti-currency: gold in dollars, log scale")
    hi_i = g.idxmax()
    a2.scatter([hi_i], [g.max()], s=26, color=BURG, zorder=5)
    a2.annotate(f"{g.max():,.0f}\n{hi_i.strftime('%b %Y')}", (hi_i, g.max()),
                textcoords="offset points", xytext=(-46, -6), fontsize=8.6,
                color=BURG)
    a2.text(0.995, 0.05,
            "Devaluation-2: every currency above has fallen against this line",
            transform=a2.transAxes, ha="right", fontsize=8.6, color=INK,
            bbox=dict(fc=SURF, ec=GRID, pad=3))
    out = os.path.join(out_dir, "fx_comparative.svg")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return _responsive(out)


def _responsive(path: str) -> str:
    s = open(path).read()
    s = re.sub(r'<svg ([^>]*?)width="[^"]*" height="[^"]*"',
               r'<svg \1width="100%"', s, count=1)
    open(path, "w").write(s)
    return path


# ---------------------------------------------------------------------------
# HTML injection (idempotent)
# ---------------------------------------------------------------------------

FIG_CSS = """
.fxfig{margin:1.5rem 0;padding:.85rem .6rem .7rem;background:#fff;border:1px solid #e3e0d6;border-radius:6px}
.fxfig svg{display:block;max-width:100%;height:auto}
.fxfig figcaption{font-size:.72rem;color:#6b6a63;margin-top:.55rem;line-height:1.4;letter-spacing:.01em;font-family:-apple-system,'Segoe UI',sans-serif}
@media print{.fxfig{break-inside:avoid}}
"""

ANCHOR_H2 = {  # figure key -> h2 id in the white paper
    "DXY": "20-the-us-dollar", "EUR": "21-the-euro", "JPY": "22-the-yen",
    "GBP": "23-sterling", "CHF": "24-the-swiss-franc", "CNY": "25-the-yuan",
}


def _caption(key: str, src: str) -> str:
    name, fred_id, yf_ticker, *_ = CATALOG[key]
    today = dt.date.today().isoformat()
    if src.startswith("fred:"):
        return (f"Daily history via FRED {src.split(':',1)[1]} (monthly "
                f"resolution shown; extremes from daily data), fetched {today}.")
    if src.startswith("yf:"):
        return (f"Daily history via Yahoo Finance {src.split(':',1)[1]} "
                f"(monthly resolution shown; extremes from daily data), "
                f"fetched {today}.")
    ref = fred_id or ("DTWEXBGS (broad; DXY via ICE)" if key == "DXY" else "n/a")
    return ("Approximate reconstruction: annual anchors with major daily "
            "extremes marked (dots); five-year panel quarterly. Indicative "
            f"of range, not tick data. Exact series: FRED {ref}.")


def inject(html_path: str, svg_dir: str, sources: dict[str, str]) -> None:
    h = open(html_path).read()
    # remove existing figures (idempotent)
    h, n = re.subn(r'<figure class="fxfig">.*?</figure>', "", h, flags=re.S)
    if n:
        print(f"  removed {n} existing figures")
    if ".fxfig{" not in h:
        h = h.replace("</style>", FIG_CSS + "</style>", 1)

    def fig_html(key: str, svgfile: str) -> str:
        svg = open(os.path.join(svg_dir, svgfile)).read()
        svg = svg[svg.find("<svg"):]
        return (f'<figure class="fxfig">{svg}'
                f'<figcaption>{_caption(key, sources[key])}</figcaption></figure>')

    for key, hid in ANCHOR_H2.items():
        m = re.search(rf'(<h2 id="{hid}">[^<]*</h2>)', h)
        if not m:
            print(f"  WARNING: anchor {hid} not found; skipping {key}")
            continue
        h = h.replace(m.group(1), m.group(1) + fig_html(key, f"fx_{key.lower()}.svg"), 1)

    m = re.search(r'(<p><strong>Thai baht\.</strong>)', h)
    if m:
        h = h.replace(m.group(1), fig_html("THB", "fx_thb.svg") + m.group(1), 1)
    m = re.search(r'(<h3 id="[^"]*long-view[^"]*">[^<]*</h3>)', h)
    if m:
        comp_cap = ("Top: each currency's value against the dollar, cumulative % "
                    "change. Bottom: gold in dollars, log scale. The envelopes "
                    "oscillate; the escalator accumulates. "
                    + ("Monthly resolution from daily data."
                       if any(s != "anchors" for s in sources.values())
                       else "Annual anchors (offline mode)."))
        comp = open(os.path.join(svg_dir, "fx_comparative.svg")).read()
        comp = comp[comp.find("<svg"):]
        h = h.replace(m.group(1), m.group(1) +
                      f'<figure class="fxfig">{comp}<figcaption>{comp_cap}'
                      f'</figcaption></figure>', 1)
    open(html_path, "w").write(h)
    print(f"  wrote {html_path} ({os.path.getsize(html_path)//1024} KB)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--html", help="currency white paper HTML to inject into")
    ap.add_argument("--svg-dir", default="figs_fx", help="where SVGs are written")
    ap.add_argument("--cache-dir", default="data/fx_history")
    ap.add_argument("--max-age-days", type=int, default=7)
    ap.add_argument("--offline", action="store_true",
                    help="skip all network; use packaged anchor dataset")
    ap.add_argument("--fetch-only", action="store_true")
    args = ap.parse_args(argv)

    os.makedirs(args.svg_dir, exist_ok=True)
    series: dict[str, tuple[pd.Series, pd.Series, str]] = {}
    print("loading series:")
    for key in list(dict.fromkeys(FIGURE_KEYS + ["GOLD"])):
        s, s5, src = load_series(key, args.cache_dir, args.max_age_days,
                                 args.offline)
        series[key] = (s, s5, src)
        print(f"  {key:<5} {src:<16} {len(s):>6} pts  "
              f"{s.index.min().date()} .. {s.index.max().date()}")
    if args.fetch_only:
        return 0

    print("rendering figures:")
    for key in FIGURE_KEYS:
        p = fig_currency(key, *series[key], out_dir=args.svg_dir)
        print(f"  {p} ({os.path.getsize(p)//1024} KB)")
    p = fig_comparative({k: (v[0], v[2]) for k, v in series.items()},
                        args.svg_dir)
    print(f"  {p} ({os.path.getsize(p)//1024} KB)")

    if args.html:
        print("injecting:")
        inject(args.html, args.svg_dir, {k: v[2] for k, v in series.items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
