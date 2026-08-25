"""
yfinance market-data fetcher (Phase 2).

Pulls daily closes for a fixed basket of 27 market symbols and writes them
into the store using the same conventions as the FRED source. No API key
required — yfinance scrapes Yahoo Finance's public endpoints.

Failure philosophy: one bad symbol never kills the run. Each symbol is
fetched independently; failures are collected into the summary dict and
surfaced in the report appendix, same as FRED.

Store keys are prefixed `mkt_` so market data is visually separate from
FRED macro series in the data_store directory.
"""

from __future__ import annotations
import logging
import time
from typing import Optional

from ..store import Store

log = logging.getLogger(__name__)

PACING_SECONDS = 0.5      # be polite to Yahoo; 27 symbols ≈ 15s total
LOOKBACK_PERIOD = "2y"    # enough history for YoY and 200dma derivations

# symbol -> store key. 27 symbols: broad indices, 11 SPDR sectors,
# rates/credit, commodities, dollar, international, crypto.
SYMBOLS: dict[str, str] = {
    # Broad equity
    "SPY": "mkt_spy",
    "QQQ": "mkt_qqq",
    "IWM": "mkt_iwm",
    "DIA": "mkt_dia",
    # Sector SPDRs
    "XLK": "mkt_xlk",
    "XLF": "mkt_xlf",
    "XLE": "mkt_xle",
    "XLV": "mkt_xlv",
    "XLI": "mkt_xli",
    "XLP": "mkt_xlp",
    "XLY": "mkt_xly",
    "XLU": "mkt_xlu",
    "XLB": "mkt_xlb",
    "XLRE": "mkt_xlre",
    "XLC": "mkt_xlc",
    # Rates & credit
    "TLT": "mkt_tlt",
    "IEF": "mkt_ief",
    "SHY": "mkt_shy",
    "HYG": "mkt_hyg",
    "LQD": "mkt_lqd",
    # Commodities & dollar
    "GLD": "mkt_gld",
    "SLV": "mkt_slv",
    "USO": "mkt_uso",
    "UUP": "mkt_uup",
    # International
    "EFA": "mkt_efa",
    "EEM": "mkt_eem",
    # Crypto
    "BTC-USD": "mkt_btc_usd",
}


def _fetch_symbol(symbol: str) -> list[tuple[str, Optional[float]]]:
    """Fetch daily closes for one symbol. Returns [(iso_date, close), ...].

    Imports yfinance lazily so the rest of the pipeline works even if the
    dependency is missing (the failure is then per-symbol, not import-time).
    """
    import yfinance as yf  # lazy import by design

    t = yf.Ticker(symbol)
    df = t.history(period=LOOKBACK_PERIOD, interval="1d", auto_adjust=True)
    if df is None or df.empty:
        raise RuntimeError(f"yfinance returned no rows for {symbol}")

    out: list[tuple[str, Optional[float]]] = []
    for idx, row in df.iterrows():
        close = row.get("Close")
        value = None if close is None or close != close else float(close)  # NaN check
        out.append((idx.date().isoformat(), value))
    return out


def pull(store: Store, symbols: Optional[dict[str, str]] = None) -> dict:
    """Pull all symbols into the store.

    Returns a summary dict shaped like the FRED source's:
        {"total": int, "success": int, "failed": [(key, err), ...],
         "series": {key: {"rows": n, "last_date": iso, "last_value": v}}}
    """
    basket = symbols or SYMBOLS
    summary: dict = {"total": len(basket), "success": 0, "failed": [], "series": {}}

    for symbol, key in basket.items():
        try:
            obs = _fetch_symbol(symbol)
            n = store.write_observations(key, obs, source="yfinance")
            last_date, last_value = obs[-1] if obs else (None, None)
            summary["series"][key] = {
                "rows": n,
                "last_date": last_date,
                "last_value": last_value,
            }
            summary["success"] += 1
            log.info("yfinance %-8s -> %s (%d rows, last %s)", symbol, key, n, last_date)
        except Exception as e:  # noqa: BLE001 — per-symbol isolation is the point
            summary["failed"].append((key, str(e)))
            log.warning("yfinance %-8s FAILED: %s", symbol, e)
        time.sleep(PACING_SECONDS)

    return summary
