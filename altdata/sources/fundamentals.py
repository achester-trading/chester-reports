"""
Quarterly fundamentals for six AI-capex names -- yfinance, stamped by SEC filing.

    python -m altdata.sources.fundamentals   # one pull, summary to stdout

Signal-triage order ST-2 (SR-16 capex funding, SR-25 the memory-cycle tell): the
inputs to calc.self_fund_ratio, calc.hs_netdebt_12m and calc.mu_inv_days (ST-4).

SOURCE. yfinance's quarterly_cashflow, quarterly_balance_sheet and
quarterly_income_stmt for AMZN, GOOGL, MSFT, META, ORCL, MU -- five to seven
quarters deep, no key. A tier-C mirror of the companies' 10-Q/10-K filings.

STORED, key yfinance.fund_<ticker>_<field>, observed_at = the fiscal quarter's end
(MU and ORCL keep their own fiscal calendars), DOLLARS:
  _operating_cash_flow   "Operating Cash Flow"
  _capex                 "Capital Expenditure" -- AS PUBLISHED, NEGATIVE for an
                         outflow; a ratio against cash flow takes the magnitude
  _net_debt              "Total Debt" minus "Cash And Cash Equivalents" from the
                         SAME balance sheet. yfinance's own "Net Debt" row is
                         mostly empty (AMZN: one quarter of five on 26 Sep 2026)
                         and mixing it in would change the definition from
                         quarter to quarter. Total Debt includes lease
                         liabilities where the filer reports them there.
  _inventory             "Inventory" -- AMZN, MU, MSFT and GOOGL only; META and
                         ORCL carry none and have no key
  _cogs                  "Cost Of Revenue"
A missing or NaN cell writes nothing.

-----------------------------------------------------------------------------
AVAILABLE_AT = THE FILING, WHEN THAT IS TRUE -- AND ONLY THEN
-----------------------------------------------------------------------------

The order asks for available_at = the filing date. yfinance serves each quarter's
LATEST figures, which may be restated, so stamping every stored quarter with its
original filing date would hand a backtest a restated number "known" at the
original filing -- the leak metrics_registry.yaml's reconstruction rule exists to
stop. So:

  a quarter first captured within FRESH_DAYS of its 10-Q/10-K ACCEPTANCE is
  stamped with that acceptance instant (EDGAR acceptanceDateTime, `observed`):
  the value seen then is the value filed;
  every other row -- the backfill, and anything when EDGAR is not configured --
  is stamped with the write instant (`ingest_instant`), an upper bound.

EDGAR needs CHESTER_SEC_CONTACT (see sources/edgar.py, whose ticker map and
submissions URL this reuses); without it the writer still runs and every row
takes the write instant. A later restatement is a new vintage at its own write
instant. revision_policy: revised.
"""

from __future__ import annotations

import datetime as dt
import logging
import math
from typing import Any, Optional

from .. import observations, session
from . import _publication as pub

log = logging.getLogger(__name__)

SOURCE = "yfinance_fundamentals"
TICKERS = ("AMZN", "GOOGL", "MSFT", "META", "ORCL", "MU")
INVENTORY_TICKERS = ("AMZN", "GOOGL", "MSFT", "MU")
FRESH_DAYS = 14
FORMS = ("10-Q", "10-K")

# field -> (statement, row label)
FIELDS = {"operating_cash_flow": ("cashflow", "Operating Cash Flow"),
          "capex": ("cashflow", "Capital Expenditure"),
          "inventory": ("balance", "Inventory"),
          "cogs": ("income", "Cost Of Revenue")}
DEBT_ROWS = ("Total Debt", "Cash And Cash Equivalents")


def key(ticker: str, field: str) -> str:
    return f"yfinance.fund_{ticker.lower()}_{field}"


def keys_for(ticker: str) -> list[str]:
    fields = ["operating_cash_flow", "capex", "net_debt", "cogs"]
    if ticker in INVENTORY_TICKERS:
        fields.insert(3, "inventory")
    return [key(ticker, f) for f in fields]


KEYS = [k for t in TICKERS for k in keys_for(t)]


def _num(v: Any) -> Optional[float]:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else x


def values_from_frames(ticker: str, frames: dict[str, dict[str, dict[str, Any]]]
                       ) -> dict[tuple[str, str], float]:
    """{(key, period_end): value} from {statement: {row label: {period: value}}}."""
    out: dict[tuple[str, str], float] = {}
    wanted = set(keys_for(ticker))
    for field, (stmt, label) in FIELDS.items():
        k = key(ticker, field)
        if k not in wanted:
            continue
        for period, v in ((frames.get(stmt) or {}).get(label) or {}).items():
            x = _num(v)
            if x is not None:
                out[(k, str(period)[:10])] = x
    bal = frames.get("balance") or {}
    debt, cash = bal.get(DEBT_ROWS[0]) or {}, bal.get(DEBT_ROWS[1]) or {}
    for period in set(debt) & set(cash):
        d, c = _num(debt[period]), _num(cash[period])
        if d is not None and c is not None:
            out[(key(ticker, "net_debt"), str(period)[:10])] = d - c
    return out


def stamp(values: dict[tuple[str, str], float], filings: dict[str, str],
          held: set[tuple[str, str]], now_iso: str) -> list[dict]:
    """Rows with available_at chosen by the rule in the module docstring.

    `filings` maps period end -> the original 10-Q/10-K acceptance instant (UTC);
    `held` is the (key, period) pairs already in the store.
    """
    now = dt.datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    rows = []
    for (k, period), v in sorted(values.items()):
        acc = filings.get(period)
        fresh = False
        if acc and (k, period) not in held:
            accepted = dt.datetime.fromisoformat(acc.replace("Z", "+00:00"))
            fresh = timedelta_ok(accepted, now)
        rows.append({"registry_key": k, "instrument": None, "observed_at": period,
                     "available_at": acc if fresh else now_iso, "value": v,
                     "availability_kind": "observed" if fresh else "ingest_instant"})
    return rows


def timedelta_ok(accepted: dt.datetime, now: dt.datetime) -> bool:
    return dt.timedelta(0) <= now - accepted <= dt.timedelta(days=FRESH_DAYS)


# --- fetch ---------------------------------------------------------------------
def fetch_frames(ticker: str) -> dict[str, dict[str, dict[str, Any]]]:
    import yfinance as yf  # noqa: PLC0415 -- lazily, as the price pass does
    tk = yf.Ticker(ticker)
    out = {}
    for stmt, df in (("cashflow", tk.quarterly_cashflow),
                     ("balance", tk.quarterly_balance_sheet),
                     ("income", tk.quarterly_income_stmt)):
        if df is None or df.empty:
            raise ValueError(f"{ticker}: yfinance returned no quarterly {stmt}")
        out[stmt] = {str(row): {str(col)[:10]: df.loc[row, col] for col in df.columns}
                     for row in df.index}
    return out


def filing_instants(ticker: str, ciks: dict, headers: dict) -> dict[str, str]:
    """{report period: acceptance instant UTC} for the ORIGINAL 10-Q/10-K."""
    import requests  # noqa: PLC0415
    from .edgar import SUBMISSIONS_URL  # noqa: PLC0415
    cik = ciks.get(ticker)
    if not cik:
        return {}
    r = requests.get(SUBMISSIONS_URL.format(cik=cik), headers=headers, timeout=30)
    r.raise_for_status()
    rec = (r.json().get("filings") or {}).get("recent") or {}
    out: dict[str, str] = {}
    for form, period, acc in zip(rec.get("form", []), rec.get("reportDate", []),
                                 rec.get("acceptanceDateTime", [])):
        if form in FORMS and period and acc:
            inst = observations.canonical_instant(acc)
            if period not in out or inst < out[period]:
                out[period] = inst
    return out


def _edgar_context() -> tuple[Optional[dict], dict]:
    """(ticker -> CIK, headers), or (None, {}) when EDGAR is not configured."""
    try:
        from . import edgar  # noqa: PLC0415
        ua = edgar.user_agent()
        if not ua:
            return None, {}
        headers = {"User-Agent": ua}
        return edgar.cik_map(headers), headers
    except Exception as exc:                                  # noqa: BLE001
        log.warning("fundamentals: EDGAR unavailable (%s); rows take the write "
                    "instant", exc)
        return None, {}


def pull(run_id: Optional[str] = None, db=None) -> dict:
    def produce() -> list[dict]:
        now_iso = session.utc_iso(timespec="microseconds")
        ciks, headers = _edgar_context()
        own = db is None
        store = db or observations.ObservationStore()
        try:
            held = {(r[0], r[1]) for r in store.conn.execute(
                "SELECT DISTINCT registry_key, observed_at FROM observations "
                "WHERE registry_key LIKE 'yfinance.fund_%'")}
        finally:
            if own:
                store.close()
        rows: list[dict] = []
        for ticker in TICKERS:
            values = values_from_frames(ticker, fetch_frames(ticker))
            filings = {}
            if ciks:
                try:
                    filings = filing_instants(ticker, ciks, headers)
                except Exception as exc:                      # noqa: BLE001
                    log.warning("fundamentals: %s filings unavailable (%s)",
                                ticker, exc)
            rows.extend(stamp(values, filings, held, now_iso))
        return rows
    return pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
