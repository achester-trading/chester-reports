"""
Signal layer for the Alternative Asset Report.

Turns the stored data + computed analytics into the framework's lateral-check
signals. Three things live here, mapped directly to the framework spec:

1. CORRELATION REGIME BREAKS — for each asset, compare its short-window
   correlation to SPY/TLT against a longer baseline. A large shift is a
   "break" — the earliest liquidity signal the Alt report exists to catch.

2. TOP-REPORT ESCALATION — the governing rule: an Alt correlation break that
   confirms a Top Report trigger escalates that trigger from APPROACHING to
   TRIGGERED-equivalent for sizing, even if the raw threshold isn't hit. We
   evaluate the two triggers the Alt report can speak to:
     #3 HY OAS > 350bp        (we read hy_oas from FRED directly)
     credit-sensitive decoupling from SPY (correlation break confirmation)
   plus the Saeclum-grade gold/Treasury signal.

3. CRYPTO SENTIMENT RECONCILIATION — the Alt report's fresh weekly Fear & Greed
   read vs a standing monthly snapshot. Alt wins on timing; divergence is
   itself an early-turn signal and is flagged.

Everything reads from the Store; nothing hits a network. Pure functions so the
report module just formats their output.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from ..store import Store
from .. import analytics
from ..config import ASSETS, BENCHMARKS

# --- thresholds (tunable in one place) --------------------------------------
CORR_BREAK_DELTA = 0.30      # |short - baseline| above this = regime break
CORR_SHORT_WIN = 30          # short rolling window (days)
CORR_BASELINE_WIN = 120      # baseline window (days)
HY_OAS_TRIGGER_BP = 350.0    # Top Report trigger #3 threshold (basis points)
HY_OAS_APPROACH_BP = 300.0   # "approaching" band
FEARGREED_EXTREME_HIGH = 75  # greed
FEARGREED_EXTREME_LOW = 25   # fear


@dataclass
class CorrelationBreak:
    asset_id: str
    benchmark: str           # 'spy' or 'tlt'
    short_corr: float
    baseline_corr: float
    delta: float
    direction: str           # 'toward' / 'away' (sign of change in correlation)

    @property
    def is_break(self) -> bool:
        return abs(self.delta) >= CORR_BREAK_DELTA


@dataclass
class TriggerStatus:
    name: str
    state: str               # CLEAR | APPROACHING | TRIGGERED | TRIGGERED*
    detail: str
    escalated: bool = False   # True if lateral confirmation bumped it


@dataclass
class SignalSet:
    asof: dt.date
    breaks: list[CorrelationBreak] = field(default_factory=list)
    triggers: list[TriggerStatus] = field(default_factory=list)
    crypto_reconciliation: Optional[dict] = None

    @property
    def active_breaks(self) -> list[CorrelationBreak]:
        return [b for b in self.breaks if b.is_break]


def _latest_value(store: Store, metric: str, asset_id: str = "macro") -> Optional[tuple[dt.date, float]]:
    df = store.read(metric, asset_id=asset_id)
    if df.empty:
        return None
    row = df.sort_values("date").iloc[-1]
    return (pd.Timestamp(row["date"]).date(), float(row["value"]))


def correlation_breaks(store: Store) -> list[CorrelationBreak]:
    """Per-asset short-vs-baseline correlation shift to SPY and TLT."""
    out: list[CorrelationBreak] = []
    asset_ids = [a.id for a in ASSETS]
    for aid in asset_ids:
        for bench in ("spy", "tlt"):
            roll_short = analytics.rolling_corr_to_benchmarks(store, aid, window=CORR_SHORT_WIN, benchmarks=(bench,))
            roll_base = analytics.rolling_corr_to_benchmarks(store, aid, window=CORR_BASELINE_WIN, benchmarks=(bench,))
            col = f"corr_{bench}"
            if roll_short.empty or roll_base.empty or col not in roll_short or col not in roll_base:
                continue
            s = roll_short[col].dropna()
            b = roll_base[col].dropna()
            if s.empty or b.empty:
                continue
            short_c = float(s.iloc[-1])
            base_c = float(b.iloc[-1])
            delta = short_c - base_c
            out.append(CorrelationBreak(
                asset_id=aid, benchmark=bench,
                short_corr=short_c, baseline_corr=base_c, delta=delta,
                direction="toward" if delta > 0 else "away",
            ))
    return out


# Credit-sensitive assets whose decoupling from SPY confirms credit stress.
CREDIT_SENSITIVE = {"us_re", "intl_re", "em", "china"}


def evaluate_triggers(store: Store, breaks: list[CorrelationBreak]) -> list[TriggerStatus]:
    """Evaluate the triggers the Alt report can speak to, with escalation logic."""
    out: list[TriggerStatus] = []

    # --- Trigger #3: HY OAS > 350bp (read directly from FRED) ---
    hy = _latest_value(store, "hy_oas")
    # FRED BAMLH0A0HYM2 is in PERCENT; convert to bp.
    if hy is not None:
        _, hy_pct = hy
        hy_bp = hy_pct * 100.0
        if hy_bp >= HY_OAS_TRIGGER_BP:
            state, detail = "TRIGGERED", f"HY OAS {hy_bp:.0f}bp ≥ {HY_OAS_TRIGGER_BP:.0f}bp"
        elif hy_bp >= HY_OAS_APPROACH_BP:
            state, detail = "APPROACHING", f"HY OAS {hy_bp:.0f}bp (approaching {HY_OAS_TRIGGER_BP:.0f}bp)"
        else:
            state, detail = "CLEAR", f"HY OAS {hy_bp:.0f}bp"
        trig = TriggerStatus("#3 HY OAS > 350bp (credit spreads)", state, detail)

        # ESCALATION: credit-sensitive asset decoupling from SPY confirms stress.
        credit_decoupling = [
            b for b in breaks
            if b.is_break and b.asset_id in CREDIT_SENSITIVE
            and b.benchmark == "spy" and b.direction == "away"
        ]
        if trig.state == "APPROACHING" and credit_decoupling:
            names = ", ".join(sorted({b.asset_id for b in credit_decoupling}))
            trig.state = "TRIGGERED*"
            trig.escalated = True
            trig.detail += f" — ESCALATED: {names} decoupling from SPY confirms credit stress laterally"
        out.append(trig)

    # --- Saeclum-grade: gold breaking away from SPY (gold-SPY decoupling) ---
    gold_break = next(
        (b for b in breaks if b.asset_id == "gold" and b.benchmark == "spy" and b.is_break),
        None,
    )
    if gold_break:
        out.append(TriggerStatus(
            "Gold–SPY regime break (Saeclum Factor IV — dollar/liquidity)",
            "TRIGGERED*" if gold_break.direction == "away" else "APPROACHING",
            f"Gold 30d corr to SPY {gold_break.short_corr:+.2f} vs {gold_break.baseline_corr:+.2f} baseline "
            f"(Δ{gold_break.delta:+.2f}) — flag for Saeclum refresh",
            escalated=gold_break.direction == "away",
        ))

    # --- Crypto risk-on/off correlation flip vs SPY (indirect sentiment) ---
    btc_break = next(
        (b for b in breaks if b.asset_id == "btc" and b.benchmark == "spy" and b.is_break),
        None,
    )
    if btc_break:
        out.append(TriggerStatus(
            "#1 Sentiment (indirect — BTC/SPY correlation flip)",
            "APPROACHING",
            f"BTC 30d corr to SPY {btc_break.short_corr:+.2f} vs {btc_break.baseline_corr:+.2f} baseline "
            f"(Δ{btc_break.delta:+.2f}) — risk appetite regime shift",
        ))

    return out


def crypto_sentiment_reconciliation(store: Store, monthly_snapshot: Optional[float] = None) -> Optional[dict]:
    """Fresh weekly Fear & Greed vs standing monthly snapshot.

    `monthly_snapshot` is the value carried in Monthly Pillar 5 (passed in by the
    caller / report config). If omitted, we report only the fresh weekly read.
    Alt wins on timing; a divergence in regime (greed↔fear) is flagged as an
    early-turn signal per the reconciliation rule.
    """
    fg = _latest_value(store, "fear_greed", asset_id="crypto")
    if fg is None:
        return None
    fg_date, fg_val = fg

    def regime(v: float) -> str:
        if v >= FEARGREED_EXTREME_HIGH:
            return "greed"
        if v <= FEARGREED_EXTREME_LOW:
            return "fear"
        return "neutral"

    weekly_regime = regime(fg_val)
    result = {
        "weekly_value": fg_val,
        "weekly_date": fg_date,
        "weekly_regime": weekly_regime,
        "monthly_value": monthly_snapshot,
        "diverges": False,
        "note": "",
    }
    if monthly_snapshot is not None:
        monthly_regime = regime(monthly_snapshot)
        result["monthly_regime"] = monthly_regime
        if monthly_regime != weekly_regime:
            result["diverges"] = True
            result["note"] = (
                f"Weekly Alt read ({fg_val:.0f}, {weekly_regime}) diverges from standing "
                f"Monthly snapshot ({monthly_snapshot:.0f}, {monthly_regime}). "
                f"Alt wins on timing; Monthly stays in composite until refresh. "
                f"Divergence itself is an early-turn signal."
            )
        else:
            result["note"] = f"Weekly and Monthly agree ({weekly_regime})."
    return result


def build_signal_set(store: Store, monthly_fg_snapshot: Optional[float] = None) -> SignalSet:
    breaks = correlation_breaks(store)
    triggers = evaluate_triggers(store, breaks)
    recon = crypto_sentiment_reconciliation(store, monthly_fg_snapshot)
    # asof = latest close date in the store
    panel = store.price_panel()
    asof = panel.index[-1].date() if not panel.empty else dt.date.today()
    return SignalSet(asof=asof, breaks=breaks, triggers=triggers, crypto_reconciliation=recon)
