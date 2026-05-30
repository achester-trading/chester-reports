"""
Central configuration: registry of every data series the pipeline pulls.

Each FRED series is declared with:
- key:          stable identifier used everywhere downstream
- fred_id:      FRED's series ID (looked up at https://fred.stlouisfed.org/)
- description:  human-readable label
- pillar:       which Monthly Macro Report pillar uses it (for traceability)
- units:        '%', 'index', 'M' (millions), 'B' (billions), 'T' (trillions), etc.
- freq:         expected release frequency — 'daily', 'weekly', 'monthly', 'quarterly'

Adding a metric? Add an entry here. Everything else picks it up automatically.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class SeriesSpec:
    key: str
    fred_id: str
    description: str
    pillar: str
    units: str
    freq: str


# ---------------------------------------------------------------------------
# FRED series — the v1 production set.
# ---------------------------------------------------------------------------

FRED_SERIES: list[SeriesSpec] = [
    # Pillar 1 — Labor Market Vitality
    SeriesSpec("nfp",              "PAYEMS",     "Nonfarm payrolls, total",         "1", "K",    "monthly"),
    SeriesSpec("u3_rate",          "UNRATE",     "Unemployment rate (U-3)",         "1", "%",    "monthly"),
    SeriesSpec("claims_4wk",       "IC4WSA",     "Initial claims, 4-week avg",      "1", "K",    "weekly"),
    SeriesSpec("lfp_rate",         "CIVPART",    "Labor force participation rate",  "1", "%",    "monthly"),
    SeriesSpec("emp_pop_ratio",    "EMRATIO",    "Employment-population ratio",     "1", "%",    "monthly"),
    SeriesSpec("avg_wkly_hours",   "AWHAETP",    "Avg weekly hours, private",       "1", "hrs",  "monthly"),
    SeriesSpec("lt_unemp",         "UEMP27OV",   "Unemployed 27+ weeks",            "1", "K",    "monthly"),
    SeriesSpec("job_openings",     "JTSJOL",     "Job openings, total (JOLTS)",     "1", "K",    "monthly"),
    SeriesSpec("hires_total",      "JTSHIL",     "Hires level, total (JOLTS)",      "1", "K",    "monthly"),
    SeriesSpec("quits_rate",       "JTSQUR",     "Quits rate (JOLTS)",              "1", "%",    "monthly"),
    SeriesSpec("layoffs",          "JTSLDL",     "Layoffs & discharges (JOLTS)",    "1", "K",    "monthly"),

    # Pillar 2 — Macroeconomic Momentum
    SeriesSpec("real_gdp",         "GDPC1",      "Real GDP",                        "2", "B",    "quarterly"),
    SeriesSpec("yield_2y",         "DGS2",       "2-year Treasury yield",           "2", "%",    "daily"),
    SeriesSpec("yield_10y",        "DGS10",      "10-year Treasury yield",          "2", "%",    "daily"),
    SeriesSpec("yield_30y",        "DGS30",      "30-year Treasury yield",          "2", "%",    "daily"),
    SeriesSpec("housing_starts",   "HOUST",      "Housing starts, total",           "2", "K",    "monthly"),
    SeriesSpec("housing_starts_sf","HOUST1F",    "Housing starts, single-family",   "2", "K",    "monthly"),
    SeriesSpec("housing_permits",  "PERMIT",     "Building permits, total",         "2", "K",    "monthly"),
    SeriesSpec("existing_homes",   "EXHOSLUSM495S","Existing home sales",           "2", "K",    "monthly"),
    SeriesSpec("new_homes",        "HSN1F",      "New home sales, single-family",   "2", "K",    "monthly"),
    SeriesSpec("mortgage_30y",     "MORTGAGE30US","30-year mortgage rate",          "2", "%",    "weekly"),
    SeriesSpec("ahe_yoy",          "CES0500000003","Avg hourly earnings, private",  "2", "$",    "monthly"),

    # Pillar 2F — Consumer Stress
    SeriesSpec("mortgage_delinq",  "DRSFRMACBS", "Mortgage delinquency rate (1-4 family)","2","%","quarterly"),
    SeriesSpec("cc_delinq_30",     "DRCCLACBS",  "Credit card delinquency, 30+ days",     "2","%","quarterly"),
    SeriesSpec("cc_chargeoff",     "CORCCACBS",  "Credit card charge-off rate",     "2", "%",    "quarterly"),
    SeriesSpec("auto_delinq",      "DRALACBN",   "Auto loan delinquency, 30+ days", "2", "%",    "quarterly"),
    SeriesSpec("total_hh_debt",    "CMDEBT",     "Household debt, total",           "2", "B",    "quarterly"),

    # Pillar 3 — Systemic Liquidity
    SeriesSpec("fed_balance",      "WALCL",      "Fed balance sheet, total assets", "3", "M",    "weekly"),
    SeriesSpec("rrp",              "RRPONTSYD",  "Overnight reverse repo",          "3", "B",    "daily"),
    SeriesSpec("tga",              "WTREGEN",    "Treasury General Account balance","3", "B",    "weekly"),
    SeriesSpec("m2",               "M2SL",       "M2 money stock",                  "3", "B",    "monthly"),
    SeriesSpec("nfci",             "NFCI",       "Chicago Fed NFCI",                "3", "idx",  "weekly"),
    SeriesSpec("nfci_lev",         "NFCILEVERAGE","NFCI leverage subindex",         "3", "idx",  "weekly"),
    SeriesSpec("bank_reserves",    "WRESBAL",    "Bank reserves at Fed",            "3", "B",    "weekly"),

    # Pillar 4 — Inflation
    SeriesSpec("cpi",              "CPIAUCSL",   "CPI, all items",                  "4", "idx",  "monthly"),
    SeriesSpec("core_cpi",         "CPILFESL",   "Core CPI (ex food/energy)",       "4", "idx",  "monthly"),
    SeriesSpec("pce",              "PCEPI",      "PCE price index",                 "4", "idx",  "monthly"),
    SeriesSpec("core_pce",         "PCEPILFE",   "Core PCE",                        "4", "idx",  "monthly"),
    SeriesSpec("sticky_cpi",       "STICKCPIM157SFRBATL","Sticky CPI, 1-mo annualized","4","%","monthly"),
    SeriesSpec("sticky_core",      "CORESTICKM157SFRBATL","Sticky Core CPI, 1-mo ann","4","%","monthly"),
    SeriesSpec("flex_cpi",         "FLEXCPIM157SFRBATL","Flexible CPI, 1-mo ann",   "4", "%",    "monthly"),
    SeriesSpec("breakeven_10y",    "T10YIE",     "10-year breakeven inflation",     "4", "%",    "daily"),
    SeriesSpec("breakeven_5y5y",   "T5YIFR",     "5y5y forward inflation expectation","4","%",  "daily"),
    SeriesSpec("wti",              "DCOILWTICO", "WTI crude oil",                   "4", "$",    "daily"),
    SeriesSpec("brent",            "DCOILBRENTEU","Brent crude oil",                "4", "$",    "daily"),
    SeriesSpec("natgas",           "DHHNGSP",    "Natural gas, Henry Hub",          "4", "$",    "daily"),

    # Pillar 5 — sentiment (most live elsewhere; what FRED has)
    SeriesSpec("vix",              "VIXCLS",     "VIX",                             "5", "idx",  "daily"),
    SeriesSpec("uoM_sent",         "UMCSENT",    "U Michigan consumer sentiment",   "5", "idx",  "monthly"),

    # Pillar 6 — Valuation & Credit
    SeriesSpec("ig_oas",           "BAMLC0A0CM", "IG corporate OAS",                "6", "%",    "daily"),
    SeriesSpec("hy_oas",           "BAMLH0A0HYM2","HY corporate OAS",               "6", "%",    "daily"),
    SeriesSpec("ccc_oas",          "BAMLH0A3HYC","CCC & lower OAS",                 "6", "%",    "daily"),
    SeriesSpec("bb_oas",           "BAMLH0A1HYBB","BB OAS",                         "6", "%",    "daily"),

    # Pillar 7 — Global / FX
    SeriesSpec("dxy",              "DTWEXBGS",   "Dollar broad index (FRB)",        "7", "idx",  "daily"),
    SeriesSpec("usd_eur",          "DEXUSEU",    "USD/EUR exchange rate",           "7", "$",    "daily"),
    SeriesSpec("usd_jpy",          "DEXJPUS",    "JPY/USD exchange rate",           "7", "JPY",  "daily"),
    SeriesSpec("usd_cny",          "DEXCHUS",    "CNY/USD exchange rate",           "7", "CNY",  "daily"),
    SeriesSpec("gold",             "GOLDAMGBD228NLBM","Gold spot, London PM fix",   "7", "$",    "daily"),

    # Pillar 8 — Sovereign
    SeriesSpec("fed_debt_pct_gdp", "GFDEGDQ188S","Federal debt held by public / GDP","8","%",    "quarterly"),
    SeriesSpec("fed_outlays",      "FGEXPND",    "Federal outlays",                 "8", "B",    "quarterly"),
    SeriesSpec("current_account",  "BOPGSTB",    "Goods & services balance",        "8", "M",    "monthly"),
]


# Quick lookup by key
SERIES_BY_KEY = {s.key: s for s in FRED_SERIES}


# Source enable/disable switches (v1 = FRED only)
ENABLED_SOURCES = {
    "fred":      True,
    "eia":       False,
    "cftc":      False,
    "coingecko": False,
}


def all_fred_ids() -> list[str]:
    """Convenience: just the FRED IDs as a flat list."""
    return [s.fred_id for s in FRED_SERIES]


def series_for_pillar(pillar: str) -> list[SeriesSpec]:
    return [s for s in FRED_SERIES if s.pillar == pillar]
