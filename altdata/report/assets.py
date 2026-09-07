"""
Per-asset summary records for the report body.

Assembles, for each asset, the numbers the Alt report tracks: price + momentum
across horizons, technicals (RSI, trend vs SMA), institutional positioning (COT
net + week-over-week change), and any supply/flow metric available (EIA stocks,
ETF flows). Pure reads from the Store; returns plain dataclasses the renderer
formats.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from ..store import Store
from .. import analytics
from ..config import ASSETS, ASSETS_BY_ID


@dataclass
class AssetSummary:
    asset_id: str
    name: str
    category: str
    last_price: Optional[float] = None
    last_date: Optional[dt.date] = None
    momentum: dict = field(default_factory=dict)        # horizon -> pct
    rsi: Optional[float] = None
    trend: Optional[str] = None                          # 'up' / 'down' / None
    cot_net: Optional[float] = None
    cot_net_change: Optional[float] = None               # vs prior week
    supply_note: Optional[str] = None                    # EIA / flows one-liner


def _sma(series: pd.Series, n: int) -> Optional[float]:
    s = series.dropna()
    if len(s) < n:
        return None
    return float(s.tail(n).mean())


def _cot(store: Store, asset_id: str) -> tuple[Optional[float], Optional[float]]:
    df = store.read("cot_net_noncomm", asset_id=asset_id).sort_values("date")
    if df.empty:
        return None, None
    net = float(df["value"].iloc[-1])
    change = None
    if len(df) >= 2:
        change = net - float(df["value"].iloc[-2])
    return net, change


def _supply_note(store: Store, asset_id: str) -> Optional[str]:
    # Energy: latest EIA stock/storage reading.
    if asset_id == "oil":
        df = store.read("crude_stocks", asset_id="oil").sort_values("date")
        if not df.empty:
            return f"Crude stocks {df['value'].iloc[-1]:,.0f} (EIA, {pd.Timestamp(df['date'].iloc[-1]).date()})"
    if asset_id == "natgas":
        df = store.read("natgas_storage", asset_id="natgas").sort_values("date")
        if not df.empty:
            return f"Working gas in storage {df['value'].iloc[-1]:,.0f} Bcf (EIA, {pd.Timestamp(df['date'].iloc[-1]).date()})"
    # Crypto: latest ETF net flow.
    if asset_id in ("btc", "eth"):
        df = store.read("etf_net_flow", asset_id=asset_id).sort_values("date")
        if not df.empty:
            v = df["value"].iloc[-1]
            return f"Spot-ETF net flow {v:+,.0f} (latest, {pd.Timestamp(df['date'].iloc[-1]).date()})"
    return None


def build_asset_summary(store: Store, asset_id: str) -> AssetSummary:
    a = ASSETS_BY_ID[asset_id]
    summ = AssetSummary(asset_id=asset_id, name=a.name, category=a.category)

    panel = store.price_panel([asset_id])
    if not panel.empty and asset_id in panel.columns:
        s = panel[asset_id].dropna()
        if not s.empty:
            summ.last_price = float(s.iloc[-1])
            summ.last_date = s.index[-1].date()
            sma50 = _sma(s, 50)
            sma200 = _sma(s, 200)
            if sma50 is not None and sma200 is not None:
                summ.trend = "up" if (summ.last_price > sma50 > sma200) else (
                    "down" if (summ.last_price < sma50 < sma200) else None
                )

    summ.momentum = analytics.momentum_table(store, asset_id)
    summ.rsi = analytics.rsi(store, asset_id)
    summ.cot_net, summ.cot_net_change = _cot(store, asset_id)
    summ.supply_note = _supply_note(store, asset_id)
    return summ


def build_all_summaries(store: Store) -> list[AssetSummary]:
    return [build_asset_summary(store, a.id) for a in ASSETS]
