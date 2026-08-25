"""
Markdown writer for the Monthly Macro Report.

This is the *data* layer of the report — it generates a markdown document
with every metric the store has, organized by pillar, with:

- Latest values, prior values, YoY changes, and date stamps
- Derived metric computations (Sahm Rule, R-G, M2 YoY, etc.)
- Significance flags on high-impact metrics
- Trigger thresholds for each metric

What it does NOT do (yet):
- Generate the narrative synthesis paragraphs (those are hand-written or
  LLM-generated in a separate step, kept out of the deterministic pipeline)
- Pull 13F / commentary / news data (separate fetchers, future work)

The output is a markdown file structured the same way as the v16 template,
with [NARRATIVE PLACEHOLDER] markers where prose needs to be added.
This way the writer is deterministic, reproducible, and easy to debug; the
narrative layer can be added as a separate LLM step that reads this data file.
"""

from __future__ import annotations
import datetime as dt
from typing import Optional

from altdata.store import Store
from altdata import config
from .. import compute


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_value(value, units: str = "") -> str:
    """Format a numeric value with units; em-dash for None."""
    if value is None:
        return "—"
    if units == "%":
        return f"{value:.2f}%"
    if units == "$":
        return f"${value:,.2f}"
    if units == "K":
        return f"{value:,.0f}K"
    if units == "M":
        return f"{value:,.0f}M"
    if units == "B":
        return f"{value:,.1f}B"
    if units == "T":
        return f"{value:,.2f}T"
    if units == "bp":
        return f"{value:+.0f} bp"
    return f"{value:,.2f}"


def fmt_date(date_str: Optional[str]) -> str:
    if not date_str:
        return ""
    try:
        d = dt.datetime.fromisoformat(date_str).date()
        return d.strftime("%b %Y")
    except ValueError:
        return date_str


def _row(store: Store, key: str, units: str = "") -> tuple[str, str]:
    """Get (latest_str, latest_date_str) for a series."""
    latest = store.latest(key)
    if not latest:
        return ("**B**", "")
    return (fmt_value(latest["value"], units), fmt_date(latest["date"]))


# ---------------------------------------------------------------------------
# Section generators
# ---------------------------------------------------------------------------

def render_masthead(report_date: dt.date) -> str:
    return f"""# Monthly Macro Report

**Date:** {report_date.strftime('%A, %B %d, %Y')}
**Generated:** {dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
**Pipeline version:** v1 (FRED-only)

---

## Pipeline Status

This report is **data-populated** from the FRED API and yfinance market data,
with narrative synthesis generated automatically by the Phase 5 Claude step.
Any section still showing `[NARRATIVE PLACEHOLDER]` indicates that generation
was skipped or failed for that section; see the note at the end of the report.

"""


def render_executive_summary(store: Store, derived: dict) -> str:
    """Skeleton headwinds/tailwinds with auto-populated data points."""
    parts = [
        "## I. Executive Summary\n",
        "*[NARRATIVE PLACEHOLDER — regime characterization paragraph]*\n",
        "### Headwinds (auto-detected)\n",
    ]

    headwinds = []
    tailwinds = []

    cpi_yoy = derived.get("cpi_yoy", {}).get("value")
    if cpi_yoy is not None:
        if cpi_yoy > 4.0:
            headwinds.append(f"- **CPI YoY at {cpi_yoy:.1f}%** — above 4% trigger")
        elif cpi_yoy < 2.5:
            tailwinds.append(f"- **CPI YoY at {cpi_yoy:.1f}%** — disinflation supportive")

    hy_oas = store.latest("hy_oas")
    if hy_oas and hy_oas["value"] is not None:
        v = hy_oas["value"]
        if v < 3.5:
            tailwinds.append(f"- **HY OAS at {v:.2f}%** — credit at cycle tights")
        elif v > 4.5:
            headwinds.append(f"- **HY OAS at {v:.2f}%** — credit stress emerging")

    sahm = derived.get("sahm_rule", {}).get("value")
    if sahm is not None:
        if sahm >= 0.5:
            headwinds.append(f"- **Sahm Rule at {sahm:.2f}** — recession trigger FIRED")
        elif sahm >= 0.3:
            headwinds.append(f"- **Sahm Rule at {sahm:.2f}** — approaching 0.50 trigger")

    real_wages = derived.get("real_wages_yoy", {}).get("value")
    if real_wages is not None:
        if real_wages < 0:
            headwinds.append(f"- **Real wages -{abs(real_wages):.2f}% YoY** — household stress")
        else:
            tailwinds.append(f"- **Real wages +{real_wages:.2f}% YoY** — supportive of consumption")

    parts.append("\n".join(headwinds) if headwinds else "- *(none auto-detected)*")
    parts.append("\n\n### Tailwinds (auto-detected)\n")
    parts.append("\n".join(tailwinds) if tailwinds else "- *(none auto-detected)*")

    parts.append("\n\n### Market-Impact Synthesis\n")
    parts.append("*[NARRATIVE PLACEHOLDER — 4-paragraph synthesis]*\n")
    return "\n".join(parts) + "\n"


def render_pillar_snapshot(store: Store, derived: dict) -> str:
    """Top-line readings per pillar — pulled live from data."""
    cpi = derived.get("cpi_yoy", {}).get("value")
    core_cpi = derived.get("core_cpi_yoy", {}).get("value")
    hy = store.latest("hy_oas")
    ccc = store.latest("ccc_oas")
    nfci = store.latest("nfci")
    m2yoy = derived.get("m2_yoy", {}).get("value")
    fed_bs = store.latest("fed_balance")
    sahm = derived.get("sahm_rule", {}).get("value")
    curve = derived.get("yield_curve_2s10s", {}).get("value")
    wti = store.latest("wti")
    dxy = store.latest("dxy")
    yr10 = store.latest("yield_10y")
    vix = store.latest("vix")

    def _v(x, fmt="{:.2f}"):
        return fmt.format(x) if x is not None else "—"

    rows = [
        ("1<br>Labor",       "cooling not breaking",
         f"• Sahm {_v(sahm)}<br>• Claims (see table)<br>• U3 (see table)"),
        ("2<br>Momentum",    "data-dependent",
         f"• 2s10s {_v(curve, '{:+.0f}bp')}<br>• Housing (see table)"),
        ("3<br>Liquidity",   "see table",
         f"• NFCI {_v(nfci['value'] if nfci else None) if nfci else '—'}<br>• M2 YoY {_v(m2yoy, '{:+.1f}%')}<br>• Fed BS {_v((fed_bs['value']/1e6) if fed_bs else None, '${:.2f}T')}"),
        ("4<br>Inflation",   "see table",
         f"• CPI {_v(cpi, '{:.1f}%')}<br>• Core CPI {_v(core_cpi, '{:.1f}%')}<br>• WTI {_v(wti['value'] if wti else None, '${:.2f}')}"),
        ("5<br>Sentiment",   "live-feed pending",
         f"• VIX {_v(vix['value'] if vix else None)}<br>*(BofA B&B, NAAIM, 13F = manual / future fetchers)*"),
        ("6<br>Val & Credit","credit-driven",
         f"• HY OAS {_v(hy['value'] if hy else None, '{:.2f}%')}<br>• CCC OAS {_v(ccc['value'] if ccc else None, '{:.2f}%')}<br>*(CAPE, FwdPE = manual)*"),
        ("7<br>Global",      "see table",
         f"• DXY {_v(dxy['value'] if dxy else None)}<br>• 10Y {_v(yr10['value'] if yr10 else None, '{:.2f}%')}"),
        ("8<br>Sovereign",   "structural watch",
         f"• Debt/GDP (see table)<br>• R vs G (see Pillar 8)"),
        ("9<br>Banking",     "private credit watch",
         "*(SLOOS, private credit = manual / future fetchers)*"),
        ("10<br>Commentary", "manual / desk roster",
         "*(Pillar 10 commentary is manual or fetcher-driven)*"),
    ]
    out = ["## II. Pillar Snapshot\n",
           "*Auto-populated from the data store. See each pillar for full detail.*\n",
           "| Pillar | Status | Headline Readings |",
           "|---|---|---|"]
    for r in rows:
        out.append(f"| {r[0]} | {r[1]} | {r[2]} |")
    return "\n".join(out) + "\n\n---\n"


def render_pillar(pillar_num: str, title: str, store: Store, derived: dict) -> str:
    """Generic pillar renderer: synthesis placeholder, then full data table for
    every series mapped to this pillar."""
    parts = [
        f"## Pillar {pillar_num} — {title}\n",
        "### Synthesis\n",
        "*[NARRATIVE PLACEHOLDER — 4-paragraph synthesis: regime, data story, cross-pillar, matrix implication]*\n",
        "### Data\n",
        "| Metric | Latest | As of |",
        "|---|---|---|",
    ]

    specs = config.series_for_pillar(pillar_num)
    for s in specs:
        latest_str, date_str = _row(store, s.key, s.units)
        parts.append(f"| {s.description} | {latest_str} | {date_str} |")

    derived_for_pillar = {
        "1": [("Sahm Rule", derived.get("sahm_rule"), "")],
        "2": [
            ("Real GDP YoY", derived.get("gdp_yoy"), "%"),
            ("Yield Curve 2s10s", derived.get("yield_curve_2s10s"), "bp"),
            ("Housing Starts YoY", derived.get("housing_starts_yoy"), "%"),
        ],
        "3": [
            ("M2 YoY Growth", derived.get("m2_yoy"), "%"),
            ("Fed Net Liquidity (rough)", derived.get("fed_net_liquidity"), "T"),
        ],
        "4": [
            ("Headline CPI YoY", derived.get("cpi_yoy"), "%"),
            ("Core CPI YoY", derived.get("core_cpi_yoy"), "%"),
            ("PCE YoY", derived.get("pce_yoy"), "%"),
            ("Core PCE YoY", derived.get("core_pce_yoy"), "%"),
            ("Real Wages YoY", derived.get("real_wages_yoy"), "%"),
        ],
        "8": [],
    }
    for name, comp, units in derived_for_pillar.get(pillar_num, []):
        if not comp:
            continue
        v = comp.get("value")
        v_str = fmt_value(v, units) if v is not None else "—"
        d_str = fmt_date(comp.get("as_of"))
        parts.append(f"| **{name}** *(computed)* | {v_str} | {d_str} |")

    if pillar_num == "8":
        rg = derived.get("r_vs_g", {}).get("value")
        if rg and isinstance(rg, dict):
            parts.append(f"| **R (Core PCE basis)** *(computed)* | {fmt_value(rg.get('r_core_pce_basis'), '%')} | |")
            parts.append(f"| **R (CPI basis)** *(computed)* | {fmt_value(rg.get('r_cpi_basis'), '%')} | |")
            parts.append(f"| **G (Real GDP YoY)** *(computed)* | {fmt_value(rg.get('g_real_gdp_yoy'), '%')} | |")
            flag = rg.get('r_greater_than_g')
            flag_str = "YES" if flag is True else ("NO" if flag is False else "—")
            parts.append(f"| **R > G regime** | {flag_str} | |")

    parts.append("\n**What Changed Since Last Report:**\n")
    parts.append("- *[manual or LLM-generated — compare to prior month's data]*\n")
    parts.append("\n**Watch in Next 30 Days:**\n")
    parts.append("- *[manual or LLM-generated]*\n")
    return "\n".join(parts) + "\n---\n"


def render_appendix(fetch_summary: dict) -> str:
    """Coverage diagnostics from the fetch run."""
    parts = [
        "## IV. Appendix\n",
        "### Appendix A — Coverage Summary\n",
        f"- Data series pulled: **{fetch_summary['success']} / {fetch_summary['total']}**",
        f"  - FRED macro series: {fetch_summary.get('fred_success', '—')} / {fetch_summary.get('fred_total', '—')}",
        f"  - Market series (yfinance): {fetch_summary.get('mkt_success', '—')} / {fetch_summary.get('mkt_total', '—')}",
    ]
    if fetch_summary.get("failed"):
        parts.append("- Failures:")
        for key, reason in fetch_summary["failed"]:
            parts.append(f"  - `{key}`: {reason[:120]}")
    else:
        parts.append("- No failures.")

    parts.append("\n### Appendix B — Production Pipeline Roadmap\n")
    parts.append("- Phase 1: FRED ingestion — **shipped** ✓")
    parts.append("- Phase 2: market data via yfinance — **shipped** ✓ (IBKR / FlashAlpha future)")
    parts.append("- Phase 3: scrapers (BofA Flow Show, AAII, NAAIM, OpenInsider) — planned")
    parts.append("- Phase 4: 13F fetcher (SEC EDGAR) — planned")
    parts.append("- Phase 5: narrative LLM step — **shipped** ✓ (commentary engine future)")
    parts.append("- Phase 6: monthly orchestration — **shipped** ✓ via GitHub Actions (email delivery future)")

    parts.append("\n### Appendix C — Illustrative Options-Trade Expressions\n")
    parts.append("*[Manual section — preserved from prior reports; refresh when narrative is added]*\n")
    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------

def render_report(store: Store, fetch_summary: dict, report_date: Optional[dt.date] = None) -> str:
    """Assemble the full Markdown report."""
    if report_date is None:
        report_date = dt.date.today()

    derived = compute.compute_all(store)

    parts = [
        render_masthead(report_date),
        render_executive_summary(store, derived),
        render_pillar_snapshot(store, derived),
        render_pillar("1", "Labor Market Vitality", store, derived),
        render_pillar("2", "Macroeconomic Momentum", store, derived),
        render_pillar("3", "Systemic Liquidity", store, derived),
        render_pillar("4", "Inflation Dynamics", store, derived),
        render_pillar("5", "Investor Sentiment & Positioning", store, derived),
        render_pillar("6", "Valuation & Credit Spreads", store, derived),
        render_pillar("7", "Global Interconnectivity", store, derived),
        render_pillar("8", "Sovereign Health & Debt Cycle", store, derived),
        "## Pillar 9 — Banking System Health\n\n*[Manual — SLOOS / private credit metrics, future fetcher]*\n\n---\n",
        "## Pillar 10 — Commentary & Narrative Flow\n\n*[Manual — desk roster + commentary, future fetcher]*\n\n---\n",
        "## III. Macroeconomic Matrix — Outlook & Probabilities\n\n*[Manual — scenarios and probabilities]*\n\n---\n",
        render_appendix(fetch_summary),
        f"\n*End of Monthly Macro Report — pipeline v1 (FRED-only).*\n",
    ]
    return "\n".join(parts)
