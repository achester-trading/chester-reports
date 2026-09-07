"""
Alternative Asset Report generator.

Reads the Store, computes signals + per-asset summaries, and renders a
numbered-section Markdown report in the house style:

  0. Status / provenance gate
  1. BLUF — executive summary referencing every numbered section
  2. Cross-Asset Correlation Matrix (vs SPY / TLT)   ← the report's key output
  3. Correlation Regime Breaks
  4. Top-Report Trigger Confirmation (with escalation logic)
  5. Crypto Sentiment Reconciliation
  6. Macro & Rates Backdrop
  7. Per-Asset Surveillance (momentum / technicals / positioning / supply)

Ordering follows the framework's macro→micro logic: the lateral cross-asset
signals (the report's reason for existing) come first, then the per-asset
detail. The BLUF is generated last but placed second, so it can summarize the
real computed state of each section rather than boilerplate.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

import numpy as np
import pandas as pd

from ..store import Store
from .. import analytics
from ..config import ASSETS, ASSETS_BY_ID
from .signals import build_signal_set, SignalSet, CORR_BREAK_DELTA
from .assets import build_all_summaries, AssetSummary


# --------------------------------------------------------------------------
# small formatting helpers
# --------------------------------------------------------------------------
def _pct(v: Optional[float], digits: int = 1) -> str:
    return "—" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:+.{digits}f}%"


def _num(v: Optional[float], digits: int = 2) -> str:
    return "—" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:,.{digits}f}"


def _corr(v: Optional[float]) -> str:
    return "—" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:+.2f}"


def _state_badge(state: str) -> str:
    return {
        "CLEAR": "🟢 CLEAR",
        "APPROACHING": "🟡 APPROACHING",
        "TRIGGERED": "🔴 TRIGGERED",
        "TRIGGERED*": "🔴 TRIGGERED\\*",
    }.get(state, state)


# --------------------------------------------------------------------------
# section renderers
# --------------------------------------------------------------------------
def _section_status(store: Store, sig: SignalSet, run_meta: dict) -> str:
    metrics = store.metrics()
    lines = [
        "## 0 · Status & Provenance",
        "",
        f"- **As-of (latest close in store):** {sig.asof.isoformat()}",
        f"- **Report generated:** {run_meta.get('generated', dt.datetime.utcnow().isoformat())} UTC",
        f"- **Metrics available in store:** {len(metrics)} ({', '.join(metrics[:12])}{'…' if len(metrics) > 12 else ''})",
        f"- **Correlation break threshold:** |Δ| ≥ {CORR_BREAK_DELTA:.2f} (30d vs 120d)",
    ]
    missing = [m for m in ("close", "hy_oas", "cot_net_noncomm", "fear_greed") if m not in metrics]
    if missing:
        lines.append(f"- **⚠️ Missing expected metrics:** {', '.join(missing)} — sections degrade gracefully")
    return "\n".join(lines)


def _correlation_matrix_section(store: Store, window: int = 60) -> tuple[str, pd.DataFrame]:
    ids = [a.id for a in ASSETS] + ["spy", "tlt"]
    cm = analytics.correlation_matrix(store, window_days=window, asset_ids=ids)
    if cm.empty:
        return "## 2 · Cross-Asset Correlation Matrix\n\n_No price data in store; matrix unavailable._", cm

    # Show each asset's correlation to the two benchmarks (the report's core view).
    rows = ["## 2 · Cross-Asset Correlation Matrix",
            f"_Rolling {window}-day return correlations to US equities (SPY) and bonds (TLT). "
            "The report's primary output — a correlation break is often the earliest liquidity signal._",
            "",
            "| Asset | → SPY | → TLT |",
            "|---|---:|---:|"]
    for a in ASSETS:
        if a.id in cm.index:
            spy_c = cm.loc[a.id, "spy"] if "spy" in cm.columns else np.nan
            tlt_c = cm.loc[a.id, "tlt"] if "tlt" in cm.columns else np.nan
            rows.append(f"| {a.name} | {_corr(spy_c)} | {_corr(tlt_c)} |")
    return "\n".join(rows), cm


def _breaks_section(sig: SignalSet) -> str:
    active = sig.active_breaks
    rows = ["## 3 · Correlation Regime Breaks",
            f"_Assets whose 30-day correlation to a benchmark has shifted ≥ {CORR_BREAK_DELTA:.2f} from the 120-day baseline._",
            ""]
    if not active:
        rows.append("🟢 **No correlation regime breaks this week.** Cross-asset relationships within normal range.")
        return "\n".join(rows)
    rows += ["| Asset | Bench | 30d | 120d | Δ | Move |",
             "|---|---|---:|---:|---:|---|"]
    for b in sorted(active, key=lambda x: -abs(x.delta)):
        name = ASSETS_BY_ID[b.asset_id].name
        rows.append(
            f"| {name} | {b.benchmark.upper()} | {_corr(b.short_corr)} | {_corr(b.baseline_corr)} "
            f"| {b.delta:+.2f} | decoupling {b.direction} |"
        )
    rows += ["", f"**{len(active)} active break(s).** A credit-sensitive asset decoupling from SPY, or gold "
                 "decoupling, feeds the trigger confirmation in §4."]
    return "\n".join(rows)


def _triggers_section(sig: SignalSet) -> str:
    rows = ["## 4 · Top-Report Trigger Confirmation",
            "_Lateral check: does the cross-asset picture confirm a Top Report turn-trigger? "
            "Per the governing rule, an Alt break confirming a trigger escalates it from "
            "APPROACHING to TRIGGERED-equivalent (\\*) for sizing — even if the raw threshold isn't hit._",
            ""]
    if not sig.triggers:
        rows.append("_No trigger-relevant signals computable (missing inputs)._")
        return "\n".join(rows)
    rows += ["| Signal | State | Detail |", "|---|---|---|"]
    for t in sig.triggers:
        rows.append(f"| {t.name} | {_state_badge(t.state)} | {t.detail} |")
    escalated = [t for t in sig.triggers if t.escalated]
    if escalated:
        rows += ["", "> **⚠️ Escalation active.** "
                 + " ".join(f"_{t.name}_ escalated by lateral confirmation." for t in escalated)
                 + " Treat as TRIGGERED-equivalent for position sizing."]
    return "\n".join(rows)


def _crypto_section(sig: SignalSet) -> str:
    rows = ["## 5 · Crypto Sentiment Reconciliation",
            "_Fresh weekly Fear & Greed vs the standing Monthly Pillar-5 snapshot. "
            "Alt wins on timing; a regime divergence is itself an early-turn signal._",
            ""]
    r = sig.crypto_reconciliation
    if not r:
        rows.append("_Fear & Greed data unavailable in store._")
        return "\n".join(rows)
    rows.append(f"- **Weekly (Alt) read:** {r['weekly_value']:.0f} → **{r['weekly_regime'].upper()}** "
                f"(as-of {r['weekly_date']})")
    if r.get("monthly_value") is not None:
        rows.append(f"- **Monthly (Pillar 5) snapshot:** {r['monthly_value']:.0f} → "
                    f"**{r.get('monthly_regime', '—').upper()}**")
    if r["diverges"]:
        rows.append(f"\n> **⚠️ Divergence:** {r['note']}")
    elif r["note"]:
        rows.append(f"\n_{r['note']}_")
    return "\n".join(rows)


def _macro_section(store: Store) -> str:
    rows = ["## 6 · Macro & Rates Backdrop",
            "_Context for the cross-asset moves above._", "",
            "| Series | Latest | As-of |", "|---|---:|---|"]
    labels = {
        "real_yield_10y": "10Y real yield (TIPS), %",
        "nominal_10y": "10Y nominal, %",
        "breakeven_10y": "10Y breakeven, %",
        "hy_oas": "HY OAS, %",
        "dollar_broad": "Broad USD index",
        "yield_curve_10_2": "10Y–2Y curve, %",
    }
    any_row = False
    for metric, label in labels.items():
        df = store.read(metric, asset_id="macro").sort_values("date")
        if df.empty:
            continue
        any_row = True
        rows.append(f"| {label} | {_num(float(df['value'].iloc[-1]), 2)} | {pd.Timestamp(df['date'].iloc[-1]).date()} |")
    if not any_row:
        return "## 6 · Macro & Rates Backdrop\n\n_No FRED data in store yet._"
    return "\n".join(rows)


def _vol_regime_section(store: Store) -> str:
    """White paper XIII's regime read: which of the five states, and how many
    of the computable tells are firing. Gates the sizing guidance downstream —
    the construction sections of VII/XI/XII condition adds on this state."""
    from ..analytics import vol_regime
    vr = vol_regime(store)
    rows = ["## 7 · Volatility Regime",
            "_Regime identification over level (paper XIII). Position-construction "
            "rules across the library condition adds and sizing on this state._", ""]
    if vr["vix"] is None:
        rows.append("_No VIX in store yet — run ingestion with FRED enabled "
                    "(series VIXCLS, VXVCLS)._")
        return "\n".join(rows)
    badge = {"deep calm": "🟢", "normal low-vol": "🟢",
             "elevated / pre-transition": "🟡", "high-vol": "🔴",
             "crisis": "🔴"}.get(vr["regime"], "⚪")
    rows.append(f"**Regime: {badge} {vr['regime'].upper()}** — "
                f"{vr['tells_firing']} of {vr['tells_computable']} computable "
                f"tells firing (threshold that has preceded transitions: 3+ of "
                f"the full eight; four require options-surface data not "
                f"tracked here — see XIII §33).")
    rows += ["", "| Input | Latest | Percentile* |", "|---|---:|---:|"]
    def _p(x): return "—" if x is None else f"{x:.0f}"
    def _n(x, d=2): return "—" if x is None else f"{x:.{d}f}"
    rows.append(f"| VIX | {_n(vr['vix'],2)} | {_p(vr['vix_pct'])} |")
    rows.append(f"| VIX/VIX3M ratio | {_n(vr['ratio'],3)} | contango < 1 |")
    rows.append(f"| MOVE | {_n(vr['move'],1)} | {_p(vr['move_pct'])} |")
    rows.append(f"| VVIX | {_n(vr['vvix'],1)} | {_p(vr['vvix_pct'])} |")
    rows.append(f"| SPY 1M realized | {_n(vr['spy_realized_1m'],1)} | "
                f"implied − realized: {_n(vr['implied_minus_realized'],1)} |")
    rows.append(f"\n_*Percentile within the store's own history "
                f"({vr['history_days']} obs); ranks need ≥250 obs — backfill "
                f"with `--lookback 1200` for stable ranks._")
    rows.append("")
    for name, firing in vr["tells"]:
        mark = "—" if firing is None else ("🔴 FIRING" if firing else "🟢 quiet")
        rows.append(f"- {mark} · {name}")
    return "\n".join(rows)


def _asset_body_section(summaries: list[AssetSummary]) -> str:
    rows = ["## 8 · Per-Asset Surveillance",
            "_Price, momentum across horizons, technicals, positioning, and supply per asset._", ""]
    # group by category for readability
    cats: dict[str, list[AssetSummary]] = {}
    for s in summaries:
        cats.setdefault(s.category, []).append(s)
    cat_labels = {"metals": "Precious & Industrial Metals", "energy": "Energy",
                  "commodities": "Commodities", "crypto": "Digital Assets",
                  "realestate": "Real Estate", "equity": "Regional Equity", "fx": "Currencies"}
    for cat, items in cats.items():
        rows.append(f"### {cat_labels.get(cat, cat.title())}")
        rows += ["| Asset | Last | 1M | 3M | 1Y | RSI | Trend | COT net (Δwk) | Supply/Flow |",
                 "|---|---:|---:|---:|---:|---:|:---:|---:|---|"]
        for s in items:
            cot = "—"
            if s.cot_net is not None:
                chg = f" ({s.cot_net_change:+,.0f})" if s.cot_net_change is not None else ""
                cot = f"{s.cot_net:,.0f}{chg}"
            trend = {"up": "▲", "down": "▼"}.get(s.trend or "", "·")
            rows.append(
                f"| {s.name} | {_num(s.last_price)} | {_pct(s.momentum.get('1M'))} "
                f"| {_pct(s.momentum.get('3M'))} | {_pct(s.momentum.get('1Y'))} "
                f"| {_num(s.rsi, 0)} | {trend} | {cot} | {s.supply_note or '—'} |"
            )
        rows.append("")
    return "\n".join(rows)


def _bluf_section(sig: SignalSet, summaries: list[AssetSummary], cm: pd.DataFrame) -> str:
    """Executive summary referencing each numbered section's actual computed state."""
    active = sig.active_breaks
    escalated = [t for t in sig.triggers if t.escalated]
    triggered = [t for t in sig.triggers if t.state.startswith("TRIGGERED")]

    # headline posture
    if escalated or triggered:
        headline = "🔴 **ALERT** — cross-asset signals confirm elevated turn-risk."
    elif active:
        headline = "🟡 **WATCH** — correlation regime shifts present; no trigger confirmation yet."
    else:
        headline = "🟢 **CLEAR** — cross-asset relationships within normal range."

    # movers
    ranked = [s for s in summaries if s.momentum.get("1M") is not None]
    ranked.sort(key=lambda s: s.momentum["1M"], reverse=True)
    top = ranked[0] if ranked else None
    bottom = ranked[-1] if ranked else None

    lines = [
        "## 1 · BLUF — Bottom Line Up Front",
        "",
        headline,
        "",
        "**Section-by-section:**",
        f"- **§2 Correlation Matrix:** {'computed for ' + str(cm.shape[0]) + ' assets vs SPY/TLT' if not cm.empty else 'unavailable (no price data)'}.",
        f"- **§3 Regime Breaks:** {len(active)} active break(s)"
        + (f" — largest: {ASSETS_BY_ID[max(active, key=lambda b: abs(b.delta)).asset_id].name}." if active else "; relationships stable."),
        f"- **§4 Trigger Confirmation:** {len(triggered)} signal(s) at TRIGGERED/-equivalent"
        + (f", {len(escalated)} escalated by lateral confirmation — **treat as TRIGGERED for sizing**." if escalated else "."),
        f"- **§5 Crypto Sentiment:** "
        + (_crypto_bluf(sig) ),
        f"- **§6 Macro Backdrop:** see rates/credit table.",
        f"- **§7 Per-Asset:** "
        + (f"top 1M mover **{top.name}** ({_pct(top.momentum.get('1M'))}), weakest **{bottom.name}** ({_pct(bottom.momentum.get('1M'))})."
           if top and bottom else "per-asset detail below."),
    ]
    return "\n".join(lines)


def _crypto_bluf(sig: SignalSet) -> str:
    r = sig.crypto_reconciliation
    if not r:
        return "Fear & Greed unavailable."
    base = f"weekly read {r['weekly_value']:.0f} ({r['weekly_regime']})"
    if r.get("diverges"):
        return base + " — **diverges from Monthly snapshot (early-turn signal)**."
    return base + "."


# --------------------------------------------------------------------------
# top-level
# --------------------------------------------------------------------------
def generate_report(store: Store, monthly_fg_snapshot: Optional[float] = None) -> str:
    """Produce the full Alternative Asset Report as Markdown."""
    sig = build_signal_set(store, monthly_fg_snapshot=monthly_fg_snapshot)
    summaries = build_all_summaries(store)
    run_meta = {"generated": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}

    corr_md, cm = _correlation_matrix_section(store)

    parts = [
        f"# The Alternative Asset Report",
        f"### *The View From Outside Equities* — week of {sig.asof.isoformat()}",
        "",
        "> Lateral confirmation layer for the equity stack. When gold, oil, crypto, the dollar, "
        "or credit-sensitive assets diverge from the equity story, the correlation matrix flags it — "
        "often before the Daily cascade sees it in the tape.",
        "",
        "---",
        _section_status(store, sig, run_meta),
        "",
        "---",
        _bluf_section(sig, summaries, cm),
        "",
        "---",
        corr_md,
        "",
        "---",
        _breaks_section(sig),
        "",
        "---",
        _triggers_section(sig),
        "",
        "---",
        _crypto_section(sig),
        "",
        "---",
        _macro_section(store),
        "",
        "---",
        _vol_regime_section(store),
        "",
        "---",
        _asset_body_section(summaries),
        "",
        "---",
        "_Generated by the altdata pipeline. Values carry source + as-of provenance; "
        "see §0. This report is a lateral check — size conviction to agreement across the five-report stack._",
    ]
    return "\n".join(parts)
