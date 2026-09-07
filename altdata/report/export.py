"""
Export the week's report as a single JSON payload the dashboard reads.

The dashboard artifact can't read the store or hit APIs (browser sandbox /
CORS), so this is the handoff: one self-contained JSON blob with everything the
three tabs need — signals, the correlation matrix, rolling-correlation series
for the trend charts, per-asset summaries, recent price series for sparklines,
and the macro table. Commit it next to the store each week; the dashboard loads
it (paste-in now, fetch-from-URL later).

Schema is versioned (`schema_version`) so the dashboard can guard against drift.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import asdict
from typing import Optional

import numpy as np
import pandas as pd

from ..store import Store
from .. import analytics
from ..config import ASSETS, ASSETS_BY_ID, FRED_SERIES
from .signals import (
    build_signal_set, CORR_BREAK_DELTA, CORR_SHORT_WIN, CORR_BASELINE_WIN,
    HY_OAS_TRIGGER_BP, HY_OAS_APPROACH_BP,
)
from .assets import build_all_summaries
from .narratives import NARRATIVES
from .narratives_extended import NARRATIVES_EXTENDED
from .peers import PEERS
from .sources import SOURCES
from .cases_and_positioning import CASES_AND_POSITIONING

SCHEMA_VERSION = 5   # v5 adds LLM weekly_update field per asset

# how many trailing closes to ship per asset for the sparkline / detail chart
SPARK_POINTS = 180
# rolling-correlation window for the trend series shown in the Correlations tab
ROLL_TREND_WIN = 60

# Deep-dive timeframes — daily for 1y, weekly for 5y, monthly for 20y.
# Resampling keeps JSON size bounded while preserving the visual shape of the
# longer charts.
DEEP_DIVE_FRAMES = {
    "12m":   {"years": 1,  "resample": None},     # daily
    "5y":    {"years": 5,  "resample": "W-FRI"},  # weekly
    "20y":   {"years": 20, "resample": "ME"},     # monthly (or longest available)
}
# Correlation comparison windows for the textbook-vs-recent contrast.
RECENT_CORR_WIN = 60     # "recent" — what's happening now
HISTORIC_CORR_WIN = 1260  # "historic" — ~5 years of trading days


def _clean(x):
    """JSON-safe: NaN/inf -> None, numpy scalars -> python."""
    if x is None:
        return None
    if isinstance(x, (np.floating, float)):
        return None if (np.isnan(x) or np.isinf(x)) else float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    return x


def _macro_table(store: Store) -> list[dict]:
    labels = {
        "real_yield_10y": "10Y real yield (TIPS), %",
        "nominal_10y": "10Y nominal, %",
        "nominal_2y": "2Y nominal, %",
        "breakeven_10y": "10Y breakeven, %",
        "hy_oas": "HY OAS, %",
        "ig_oas": "IG OAS, %",
        "dollar_broad": "Broad USD index",
        "yield_curve_10_2": "10Y–2Y curve, %",
        "fed_funds": "Fed funds, %",
    }
    rows = []
    for metric, label in labels.items():
        df = store.read(metric, asset_id="macro").sort_values("date")
        if df.empty:
            continue
        rows.append({
            "metric": metric,
            "label": label,
            "value": _clean(float(df["value"].iloc[-1])),
            "asof": str(pd.Timestamp(df["date"].iloc[-1]).date()),
        })
    return rows


def _correlation_matrix(store: Store, window: int = ROLL_TREND_WIN) -> dict:
    ids = [a.id for a in ASSETS] + ["spy", "tlt"]
    cm = analytics.correlation_matrix(store, window_days=window, asset_ids=ids)
    if cm.empty:
        return {"window": window, "rows": []}
    rows = []
    for a in ASSETS:
        if a.id in cm.index:
            rows.append({
                "asset_id": a.id,
                "name": a.name,
                "category": a.category,
                "spy": _clean(cm.loc[a.id, "spy"]) if "spy" in cm.columns else None,
                "tlt": _clean(cm.loc[a.id, "tlt"]) if "tlt" in cm.columns else None,
            })
    return {"window": window, "rows": rows}


def _rolling_trends(store: Store) -> dict:
    """Per-asset rolling 60d correlation to SPY & TLT over time (trend charts)."""
    out = {}
    for a in ASSETS:
        roll = analytics.rolling_corr_to_benchmarks(store, a.id, window=ROLL_TREND_WIN)
        if roll.empty:
            continue
        roll = roll.tail(SPARK_POINTS)
        out[a.id] = [
            {
                "date": str(idx.date()),
                "spy": _clean(row.get("corr_spy")),
                "tlt": _clean(row.get("corr_tlt")),
            }
            for idx, row in roll.iterrows()
        ]
    return out


def _long_history(panel: pd.DataFrame, asset_id: str) -> dict:
    """Return resampled price history at 12M/5Y/20Y horizons.

    For each timeframe, returns the *longest available* series up to the
    target. For shorter-history assets (Solana, Zcash, spot-ETF flows), the
    20Y frame reports the full available span — the dashboard reads
    `coverage_years` and labels the chart accordingly ("since 2020", etc).
    """
    out = {}
    if panel.empty or asset_id not in panel.columns:
        for k in DEEP_DIVE_FRAMES:
            out[k] = {"series": [], "coverage_years": 0.0, "start_date": None}
        return out
    ser = panel[asset_id].dropna()
    if ser.empty:
        for k in DEEP_DIVE_FRAMES:
            out[k] = {"series": [], "coverage_years": 0.0, "start_date": None}
        return out
    full_start = ser.index.min()
    full_end = ser.index.max()
    for key, cfg in DEEP_DIVE_FRAMES.items():
        target_start = full_end - pd.DateOffset(years=cfg["years"])
        # use longest available — never pad past the data
        eff_start = max(full_start, target_start)
        window = ser.loc[eff_start:]
        if cfg["resample"]:
            window = window.resample(cfg["resample"]).last().dropna()
        coverage_days = (full_end - eff_start).days
        coverage_years = round(coverage_days / 365.25, 2)
        out[key] = {
            "series": [
                {"date": str(idx.date()), "price": _clean(float(v))}
                for idx, v in window.items()
            ],
            "coverage_years": coverage_years,
            "start_date": str(eff_start.date()) if pd.notna(eff_start) else None,
        }
    return out


def _correlation_contrast(panel: pd.DataFrame, asset_id: str) -> dict:
    """Compute recent (60d) vs historic (~5y) correlation of daily returns to
    SPY and TLT. The dashboard renders these next to the textbook-view sentence
    and flags any meaningful divergence."""
    out = {
        "recent_spy": None, "recent_tlt": None,
        "historic_spy": None, "historic_tlt": None,
        "diverges_spy": False, "diverges_tlt": False,
    }
    if panel.empty or asset_id not in panel.columns:
        return out
    cols = [c for c in [asset_id, "spy", "tlt"] if c in panel.columns]
    if len(cols) < 2:
        return out
    rets = panel[cols].pct_change().dropna(how="all")
    if rets.empty:
        return out

    def _corr(window_days, bench):
        if bench not in rets.columns:
            return None
        sub = rets[[asset_id, bench]].dropna().tail(window_days)
        if len(sub) < 30:  # need enough overlap to be meaningful
            return None
        c = sub[asset_id].corr(sub[bench])
        return _clean(c)

    out["recent_spy"]   = _corr(RECENT_CORR_WIN, "spy")
    out["recent_tlt"]   = _corr(RECENT_CORR_WIN, "tlt")
    out["historic_spy"] = _corr(HISTORIC_CORR_WIN, "spy")
    out["historic_tlt"] = _corr(HISTORIC_CORR_WIN, "tlt")
    # divergence: |recent - historic| > 0.25 — same threshold spirit as §3 breaks
    for bench in ("spy", "tlt"):
        r, h = out[f"recent_{bench}"], out[f"historic_{bench}"]
        if r is not None and h is not None:
            out[f"diverges_{bench}"] = abs(r - h) > 0.25
    return out


def _peer_correlations(panel: pd.DataFrame, asset_id: str) -> list:
    """Compute correlation of asset_id to each peer in PEERS[asset_id].
    Returns recent (60d) and historic (~5y) correlations plus the textbook
    rationale for each pairing."""
    if asset_id not in PEERS or panel.empty or asset_id not in panel.columns:
        return []
    rets = panel.pct_change().dropna(how="all")
    if rets.empty:
        return []

    out = []
    for peer_def in PEERS[asset_id]:
        peer_id = peer_def["asset_id"]
        if peer_id not in rets.columns:
            continue
        sub = rets[[asset_id, peer_id]].dropna()
        if len(sub) < 30:
            continue
        recent = sub.tail(RECENT_CORR_WIN)
        historic = sub.tail(HISTORIC_CORR_WIN)
        recent_corr = _clean(recent[asset_id].corr(recent[peer_id])) if len(recent) >= 30 else None
        historic_corr = _clean(historic[asset_id].corr(historic[peer_id])) if len(historic) >= 30 else None
        diverges = (
            recent_corr is not None and historic_corr is not None
            and abs(recent_corr - historic_corr) > 0.25
        )
        # peer display name from ASSETS_BY_ID
        peer_name = ASSETS_BY_ID[peer_id].name if peer_id in ASSETS_BY_ID else peer_id
        out.append({
            "asset_id": peer_id,
            "name": peer_name,
            "rationale": peer_def["rationale"],
            "recent_corr": recent_corr,
            "historic_corr": historic_corr,
            "diverges": diverges,
        })
    return out


def _merged_narrative(asset_id: str) -> dict:
    """Merge extended narrative (if available) over base narrative for an asset.
    Extended overrides only the fields it defines; base provides fallback for
    fields not in the extended entry. Returns a flat dict with the five
    narrative fields."""
    base = NARRATIVES.get(asset_id, {})
    ext = NARRATIVES_EXTENDED.get(asset_id, {})
    merged = dict(base)
    for k, v in ext.items():
        if v:
            merged[k] = v
    return {
        "performance":     merged.get("performance"),
        "supply":          merged.get("supply"),
        "demand":          merged.get("demand"),
        "outlook":         merged.get("outlook"),
        "correlation_txt": merged.get("correlation_txt"),
        "has_extended":    asset_id in NARRATIVES_EXTENDED,
    }


def _positioning_block(store: Store, asset_id: str) -> dict:
    """Extract positioning data from the store for this asset, structured for the
    dashboard's Market Positioning section.

    Returns a dict with whichever data is available:
      - cot:                COT non-commercial net positioning history + extremes
      - cot_change_recent:  4-week change in net positioning
      - etf_flows:           ETF net flow history (for BTC, ETH, gold proxy)
      - sentiment:           Fear & Greed weekly readings (for crypto)
      - exchange_inventory:  Storage / inventory levels (for oil, natgas)
    Plus a 'lens' field indicating which positioning data is *relevant* for this
    asset (per CASES_AND_POSITIONING[asset_id]['positioning_lens']), so the
    dashboard can render appropriate placeholders for not-yet-wired data.
    """
    out = {
        "lens": (CASES_AND_POSITIONING.get(asset_id, {}).get("positioning_lens", [])),
        "cot": None,
        "etf_flows": None,
        "sentiment": None,
        "exchange_inventory": None,
        "central_bank": None,
    }

    # ─── COT positioning ────────────────────────────────────
    cot_df = store.read(metric="cot_net_noncomm", asset_id=asset_id)
    if not cot_df.empty:
        # cot_df has columns: date, value, source, asof
        cot_df = cot_df.sort_values("date")
        recent = cot_df.tail(26)  # ~6 months weekly
        latest = recent.iloc[-1]
        # find recent extremes for context
        all_data = cot_df.tail(260)  # ~5 years weekly if available
        hist_max = all_data["value"].max() if not all_data.empty else None
        hist_min = all_data["value"].min() if not all_data.empty else None
        hist_mean = all_data["value"].mean() if not all_data.empty else None
        # percentile rank of current vs 5y range
        pct_rank = None
        if hist_max is not None and hist_min is not None and hist_max != hist_min:
            pct_rank = float((latest["value"] - hist_min) / (hist_max - hist_min))
        # 4-week change
        cot_4w_change = None
        if len(cot_df) >= 5:
            cot_4w_change = float(latest["value"] - cot_df.iloc[-5]["value"])
        out["cot"] = {
            "latest_net": _clean(float(latest["value"])),
            "latest_date": str(pd.Timestamp(latest["date"]).date()),
            "change_4w": _clean(cot_4w_change),
            "hist_max": _clean(float(hist_max)) if hist_max is not None else None,
            "hist_min": _clean(float(hist_min)) if hist_min is not None else None,
            "hist_mean": _clean(float(hist_mean)) if hist_mean is not None else None,
            "pct_rank": _clean(pct_rank),
            "history": [
                {"date": str(pd.Timestamp(r["date"]).date()), "value": _clean(float(r["value"]))}
                for _, r in recent.iterrows()
            ],
        }

    # ─── ETF flows (BTC, ETH primarily) ─────────────────────
    etf_df = store.read(metric="etf_net_flow", asset_id=asset_id)
    if not etf_df.empty:
        etf_df = etf_df.sort_values("date")
        recent = etf_df.tail(30)  # last ~30 days
        latest = recent.iloc[-1]
        sum_5d = float(recent.tail(5)["value"].sum()) if len(recent) >= 5 else None
        sum_30d = float(recent.tail(30)["value"].sum()) if len(recent) >= 30 else None
        out["etf_flows"] = {
            "latest": _clean(float(latest["value"])),
            "latest_date": str(pd.Timestamp(latest["date"]).date()),
            "sum_5d": _clean(sum_5d),
            "sum_30d": _clean(sum_30d),
            "unit": "USD millions",
            "history": [
                {"date": str(pd.Timestamp(r["date"]).date()), "value": _clean(float(r["value"]))}
                for _, r in recent.iterrows()
            ],
        }

    # ─── Crypto sentiment (Fear & Greed) ────────────────────
    if asset_id in ("btc", "eth", "sol", "zec"):
        fg_df = store.read(metric="fear_greed", asset_id="crypto")
        if not fg_df.empty:
            fg_df = fg_df.sort_values("date")
            latest = fg_df.iloc[-1]
            recent = fg_df.tail(30)
            regime = "fear" if latest["value"] < 25 else "greed" if latest["value"] > 75 else "neutral"
            out["sentiment"] = {
                "name": "Fear & Greed Index",
                "latest": _clean(float(latest["value"])),
                "latest_date": str(pd.Timestamp(latest["date"]).date()),
                "regime": regime,
                "history": [
                    {"date": str(pd.Timestamp(r["date"]).date()), "value": _clean(float(r["value"]))}
                    for _, r in recent.iterrows()
                ],
            }

    # ─── Exchange inventory (oil, natgas) ───────────────────
    inv_metric = {"oil": "crude_stocks", "natgas": "natgas_storage"}.get(asset_id)
    if inv_metric:
        inv_df = store.read(metric=inv_metric, asset_id=asset_id)
        if not inv_df.empty:
            latest = inv_df.sort_values("date").iloc[-1]
            out["exchange_inventory"] = {
                "name": "Crude Stocks" if asset_id == "oil" else "Natural Gas Storage",
                "latest": _clean(float(latest["value"])),
                "latest_date": str(pd.Timestamp(latest["date"]).date()),
                "unit": "thousand barrels" if asset_id == "oil" else "BCF",
            }

    return out


def _weekly_update(store: Store, asset_id: str) -> dict:
    """Pull the latest LLM weekly update for this asset from the store.

    The weekly_scan orchestrator writes Observations with metric='weekly_update',
    storing the LLM response text in the `note` field. Returns the most recent
    update with its date and source, or None if no update exists.
    """
    df = store.read(metric="weekly_update", asset_id=asset_id)
    if df.empty or "note" not in df.columns:
        return None
    df = df.sort_values("date")
    latest = df.iloc[-1]
    note = latest.get("note") or ""
    if not str(note).strip():
        return None
    return {
        "text": str(note),
        "date": str(pd.Timestamp(latest["date"]).date()),
        "source": str(latest.get("source", "llm_weekly_scan")),
        "is_stub": str(note).startswith("[WEEKLY_SCAN_STUB]")
                   or str(note).startswith("[anthropic SDK")
                   or str(note).startswith("[openai SDK")
                   or str(note).startswith("[ANTHROPIC_API_KEY")
                   or str(note).startswith("[OPENAI_API_KEY"),
    }


def _deep_dive_block(store: Store, panel: pd.DataFrame, asset_id: str) -> dict:
    """Per-asset deep-dive block. v5 schema: adds weekly_update."""
    cp = CASES_AND_POSITIONING.get(asset_id, {})
    return {
        "history":            _long_history(panel, asset_id),
        "narrative":          _merged_narrative(asset_id),
        "correlation":        _correlation_contrast(panel, asset_id),
        "peer_correlations":  _peer_correlations(panel, asset_id),
        "sources":            SOURCES.get(asset_id, []),
        "cases":              cp.get("cases"),
        "trading_environment": cp.get("trading_environment"),
        "positioning":        _positioning_block(store, asset_id),
        "weekly_update":      _weekly_update(store, asset_id),
    }


def _asset_blocks(store: Store) -> list[dict]:
    summaries = build_all_summaries(store)
    asset_ids = [a.id for a in ASSETS]
    # benchmarks needed for the deep-dive correlation contrast (recent vs historic)
    panel = store.price_panel(asset_ids + ["spy", "tlt"])
    blocks = []
    for s in summaries:
        spark = []
        if not panel.empty and s.asset_id in panel.columns:
            ser = panel[s.asset_id].dropna().tail(SPARK_POINTS)
            spark = [{"date": str(idx.date()), "price": _clean(float(v))} for idx, v in ser.items()]
        blocks.append({
            "asset_id": s.asset_id,
            "name": s.name,
            "category": s.category,
            "last_price": _clean(s.last_price),
            "last_date": str(s.last_date) if s.last_date else None,
            "momentum": {k: _clean(v) for k, v in (s.momentum or {}).items()},
            "rsi": _clean(s.rsi),
            "trend": s.trend,
            "cot_net": _clean(s.cot_net),
            "cot_net_change": _clean(s.cot_net_change),
            "supply_note": s.supply_note,
            "spark": spark,
            "deep_dive": _deep_dive_block(store, panel, s.asset_id),
        })
    return blocks


def build_payload(store: Store, monthly_fg_snapshot: Optional[float] = None) -> dict:
    sig = build_signal_set(store, monthly_fg_snapshot=monthly_fg_snapshot)

    # headline posture (mirrors the BLUF logic)
    escalated = [t for t in sig.triggers if t.escalated]
    triggered = [t for t in sig.triggers if t.state.startswith("TRIGGERED")]
    if escalated or triggered:
        posture = "ALERT"
    elif sig.active_breaks:
        posture = "WATCH"
    else:
        posture = "CLEAR"

    return {
        "schema_version": SCHEMA_VERSION,
        "generated": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "asof": str(sig.asof),
        "posture": posture,
        "thresholds": {
            "corr_break_delta": CORR_BREAK_DELTA,
            "corr_short_win": CORR_SHORT_WIN,
            "corr_baseline_win": CORR_BASELINE_WIN,
            "hy_oas_trigger_bp": HY_OAS_TRIGGER_BP,
            "hy_oas_approach_bp": HY_OAS_APPROACH_BP,
        },
        "signals": {
            "breaks": [
                {**asdict(b), "is_break": b.is_break,
                 "short_corr": _clean(b.short_corr), "baseline_corr": _clean(b.baseline_corr),
                 "delta": _clean(b.delta),
                 "name": ASSETS_BY_ID[b.asset_id].name}
                for b in sig.breaks
            ],
            "triggers": [asdict(t) for t in sig.triggers],
            "crypto_reconciliation": _recon_clean(sig.crypto_reconciliation),
        },
        "correlation_matrix": _correlation_matrix(store),
        "rolling_trends": _rolling_trends(store),
        "assets": _asset_blocks(store),
        "macro": _macro_table(store),
    }


def _recon_clean(r: Optional[dict]) -> Optional[dict]:
    if not r:
        return None
    out = dict(r)
    out["weekly_value"] = _clean(r.get("weekly_value"))
    out["monthly_value"] = _clean(r.get("monthly_value"))
    out["weekly_date"] = str(r.get("weekly_date")) if r.get("weekly_date") else None
    return out


def export_json(store: Store, path: str, monthly_fg_snapshot: Optional[float] = None) -> str:
    payload = build_payload(store, monthly_fg_snapshot=monthly_fg_snapshot)
    with open(path, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    return path
