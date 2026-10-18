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
import os
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
    # NUMBER, not thousands (T3.3, 10 Oct 2026): IC4WSA is published in plain units
    # -- 200,500 claims -- and "K" printed it as "200.5 million" in the second box
    # dry run. EXHOSLUSM495S below is plain Number too (4,020,000 homes).
    SeriesSpec("claims_4wk",       "IC4WSA",     "Initial claims, 4-week avg",      "1", "N",    "weekly"),
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
    SeriesSpec("existing_homes",   "EXHOSLUSM495S","Existing home sales",           "2", "N",    "monthly"),
    SeriesSpec("new_homes",        "HSN1F",      "New home sales, single-family",   "2", "K",    "monthly"),
    SeriesSpec("mortgage_30y",     "MORTGAGE30US","30-year mortgage rate",          "2", "%",    "weekly"),
    SeriesSpec("ahe_yoy",          "CES0500000003","Avg hourly earnings, private",  "2", "$",    "monthly"),

    # Pillar 2F — Consumer Stress
    SeriesSpec("mortgage_delinq",  "DRSFRMACBS", "Mortgage delinquency rate (1-4 family)","2","%","quarterly"),
    SeriesSpec("cc_delinq_30",     "DRCCLACBS",  "Credit card delinquency, 30+ days",     "2","%","quarterly"),
    SeriesSpec("cc_chargeoff",     "CORCCACBS",  "Credit card charge-off rate",     "2", "%",    "quarterly"),
    SeriesSpec("auto_delinq",      "DRALACBN",   "Auto loan delinquency, 30+ days", "2", "%",    "quarterly"),
    # MILLIONS of dollars, not billions (T3.3): CMDEBT 20,934,549 is $20.9tn.
    SeriesSpec("total_hh_debt",    "CMDEBT",     "Household debt, total",           "2", "M",    "quarterly"),

    # Pillar 3 — Systemic Liquidity
    SeriesSpec("fed_balance",      "WALCL",      "Fed balance sheet, total assets", "3", "M",    "weekly"),
    SeriesSpec("rrp",              "RRPONTSYD",  "Overnight reverse repo",          "3", "B",    "daily"),
    # MILLIONS, not billions. WTREGEN is published in millions of dollars like
    # WALCL beside it -- 830,296 is $830bn -- and this line said "B" until the
    # net-liquidity port caught it. RRP is the odd one out: RRPONTSYD really is
    # billions (11.677 = $11.7bn), which is how a units field with two neighbours
    # in millions came to be copied wrong.
    SeriesSpec("tga",              "WTREGEN",    "Treasury General Account balance","3", "M",    "weekly"),
    SeriesSpec("m2",               "M2SL",       "M2 money stock",                  "3", "B",    "monthly"),
    SeriesSpec("nfci",             "NFCI",       "Chicago Fed NFCI",                "3", "idx",  "weekly"),
    SeriesSpec("nfci_lev",         "NFCILEVERAGE","NFCI leverage subindex",         "3", "idx",  "weekly"),
    SeriesSpec("bank_reserves",    "WRESBAL",    "Bank reserves at Fed",            "3", "M",    "weekly"),

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
    SeriesSpec("dxy",              "DTWEXBGS",   "Broad Dollar Index (DTWEXBGS, FRB)",        "7", "idx",  "daily"),
    SeriesSpec("usd_eur",          "DEXUSEU",    "USD/EUR exchange rate",           "7", "$",    "daily"),
    SeriesSpec("usd_jpy",          "DEXJPUS",    "JPY/USD exchange rate",           "7", "JPY",  "daily"),
    SeriesSpec("usd_cny",          "DEXCHUS",    "CNY/USD exchange rate",           "7", "CNY",  "daily"),
    
    # Pillar 8 — Sovereign
    SeriesSpec("fed_debt_pct_gdp", "GFDEGDQ188S","Federal debt held by public / GDP","8","%",    "quarterly"),
    SeriesSpec("fed_outlays",      "FGEXPND",    "Federal outlays",                 "8", "B",    "quarterly"),
    SeriesSpec("current_account",  "BOPGSTB",    "Goods & services balance",        "8", "M",    "monthly"),
]


# ---------------------------------------------------------------------------
# FRED series added by the signal-triage order (ST-1, 26 Sep 2026).
#
# A SEPARATE LIST, NOT AN APPEND TO FRED_SERIES, and the separation is the point.
# FRED_SERIES is the Monthly's set: its snapshot, its appendix and surprise v1's
# calc.naive_expectation / calc.surprise_vs_naive families all iterate it, so one
# line added there is a Monthly render change and two new calc.* series apiece --
# which ST-1 may not make (features are ST-3/ST-4). These are pulled by the same
# FRED path (sources/fred.py, via FRED_PULL_SERIES below), land under the same
# `fred.` prefix, and reach the freshness roster; nothing else reads them yet.
#
# Pillar codes follow FRED_SERIES where a pillar fits. Two are new and resolve
# through metrics_registry.yaml's fred_signal_triage block: "2R" (a term-premium
# model's reading, mechanism group rates_decomposition) and "HH" (Z.1 household
# holdings, household_allocation).
#
# UNITS WERE READ OFF EACH SERIES' FRED PAGE on 26 Sep 2026, not copied from a
# neighbour -- see CLAUDE.md on WTREGEN. Three are traps: the G.19 consumer-credit
# series are MILLIONS (TOTALSL 5,186,204 = $5.19tn), not the billions most
# write-ups quote; TREAST is millions like WALCL; GDP is billions SAAR. The Z.1
# rows are millions, quarterly, end of period.
# ---------------------------------------------------------------------------

FRED_SIGNAL_SERIES: list[SeriesSpec] = [
    # Rates -- Thread R (SR-6, 15, 17, 22, 23)
    SeriesSpec("tips_10y",         "DFII10",     "10-year TIPS real yield",         "2", "%",    "daily"),
    # DFII30 added 28 Sep 2026 (SR-17); unit read off its FRED page that day:
    # percent, not seasonally adjusted, daily (H.15).
    SeriesSpec("tips_30y",         "DFII30",     "30-year TIPS real yield",         "2", "%",    "daily"),
    SeriesSpec("yield_5y",         "DGS5",       "5-year Treasury yield",           "2", "%",    "daily"),
    SeriesSpec("tbill_3m",         "DTB3",       "3-month T-bill, secondary market (discount basis)","2","%","daily"),
    SeriesSpec("term_premium_kw",  "THREEFYTP10","10y term premium, Kim-Wright model","2R","%",   "daily"),
    SeriesSpec("fed_funds",        "FEDFUNDS",   "Effective federal funds rate, monthly avg","3","%", "monthly"),
    SeriesSpec("usrec",            "USREC",      "NBER recession indicator (1 = recession month)","2","0/1","monthly"),
    SeriesSpec("soma_treasuries",  "TREAST",     "Fed SOMA Treasury holdings, Wednesday level","3","M","weekly"),
    SeriesSpec("gdp_nominal",      "GDP",        "Nominal GDP, SAAR",               "2", "B",    "quarterly"),

    # Credit -- SR-16 (AI credit absorption; the AA-BBB differential)
    SeriesSpec("aa_oas",           "BAMLC0A2CAA","ICE BofA AA corporate OAS",       "6", "%",    "daily"),
    SeriesSpec("bbb_oas",          "BAMLC0A4CBBB","ICE BofA BBB corporate OAS",     "6", "%",    "daily"),

    # Consumer credit, G.19 -- SR-5. First prints come from ALFRED (O.16), not here.
    SeriesSpec("consumer_credit_total",       "TOTALSL",  "Consumer credit outstanding, total (G.19)",  "2F","M","monthly"),
    SeriesSpec("consumer_credit_revolving",   "REVOLSL",  "Consumer credit, revolving (G.19)",          "2F","M","monthly"),
    SeriesSpec("consumer_credit_nonrevolving","NONREVSL", "Consumer credit, nonrevolving (G.19)",       "2F","M","monthly"),

    # Dollar -- SR-14 / G-12. The nominal broad index is FRED_SERIES' `dxy`.
    SeriesSpec("real_dollar_broad","RTWEXBGS",   "Real Broad Dollar Index (Jan 2006=100)","7","idx","monthly"),

    # Z.1 household holdings (B.101, households and nonprofits) -- SR-12
    SeriesSpec("hh_equities",      "HNOCEAQ027S","Households & nonprofits: corporate equities, level (Z.1)","HH","M","quarterly"),
    SeriesSpec("hh_debt_securities","HNODSAQ027S","Households & nonprofits: debt securities, level (Z.1)","HH","M","quarterly"),
    SeriesSpec("hh_deposits",      "DABSHNO",    "Households & nonprofits: currency, deposits and MMF shares, level (Z.1)","HH","M","quarterly"),

    # Japan, OECD MEI monthly averages via FRED -- ST-2, SR-2 (the yen leg of the
    # funding-currency stack; the daily JGB curve is altdata/sources/mof.py).
    # Both PERCENT, read off their FRED pages 26 Sep 2026. China's 10-year was
    # also named (IRLTLT01CNM156N) but FRED returns 404 for it and carries no
    # China long rate at all; it comes from CFETS instead (sources/cfets.py).
    SeriesSpec("jp_10y",           "IRLTLT01JPM156N","Japan 10-year government bond yield, monthly avg (OECD)","7","%","monthly"),
    SeriesSpec("jp_3m",            "IR3TIB01JPM156N","Japan 3-month interbank rate, monthly avg (OECD)","7","%","monthly"),

    # INC-6 follow-up (1 Oct 2026): the rate the heat view converts a peso
    # exposure at. FRED's DEXMXUS is MEXICAN PESOS PER ONE U.S. DOLLAR, daily,
    # H.10 -- confirmed against FRED's own series record before the commit, per
    # the unit rule in CLAUDE.md. The price basket's instruments are all
    # USD-listed; MXN is the one non-USD listing the account has held.
    SeriesSpec("usd_mxn",          "DEXMXUS",    "MXN/USD exchange rate (pesos per dollar)","7","MXN","daily"),
    # 6d (2 Oct 2026, item 10): the 5-year breakeven for the What's-priced trigger,
    # beside T10YIE and T5YIFR. Percent, daily -- read off FRED's series page.
    SeriesSpec("breakeven_5y",     "T5YIE",      "5-year breakeven inflation rate",  "4", "%",    "daily"),
    # T2.3 (ruled 4 Oct 2026, item 3): the funding rate against the Fed's floor,
    # for Plumbing's SOFR-IORB spread. Both percent, daily -- read off FRED's
    # series pages (SOFR; IORB, from 29 Jul 2021).
    SeriesSpec("sofr",             "SOFR",       "Secured overnight financing rate", "3", "%",    "daily"),
    SeriesSpec("iorb",             "IORB",       "Interest on reserve balances",     "3", "%",    "daily"),
    # Signal-triage batch 3, ST-B3-02 (SR-6 by tenor, 13 Oct 2026): the 5-year
    # real yield, for the 5-year's split (and the 2-year's, as the nearest TIPS
    # tenor). Percent, daily -- read off FRED's series page that day ("Market
    # Yield on U.S. Treasury Securities at 5-Year Constant Maturity, Quoted on
    # an Investment Basis, Inflation-Indexed").
    SeriesSpec("tips_5y",          "DFII5",      "5-year TIPS real yield",          "2",  "%",    "daily"),
    # SR-46 (ruled 6 Oct 2026; Audit #4 Category 1 item 5): the EM screen's FRED
    # currencies are AQ-3's H.10 keys (FRED_FX_SCAN_SERIES, FRED_THAILAND_SERIES:
    # usd_brl, usd_zar, usd_inr, usd_krw, usd_twd, usd_thb), one copy each
    # (Friday stitching, 13 Oct).
    # SR-46(c): the EM spread family. Both PERCENT, daily, read off their FRED
    # pages 11 Oct 2026. FRED notes that from April 2026 each serves only THREE
    # YEARS of observations, so a five-year percentile is not computable from it.
    SeriesSpec("em_corp_oas",      "BAMLEMCBPIOAS","ICE BofA EM Corporate Plus OAS",  "6", "%",    "daily"),
    SeriesSpec("em_hy_oas",        "BAMLEMHBHYCRPIOAS","ICE BofA High Yield EM Corporate Plus OAS","6","%","daily"),
]

# ---------------------------------------------------------------------------
# THE FX SCAN TIER (AQ-3 part 1, 11 Oct 2026; the Quarterly's currency chapter,
# change order section 4.4): every daily pair of the Fed's H.10 release on FRED
# that the store did not already hold (it held DEXUSEU, DEXJPUS, DEXCHUS,
# DEXMXUS). Each was read off FRED on 11 Oct 2026 -- live, last print 2 Oct --
# and its QUOTE CONVENTION with it: H.10 quotes most pairs as foreign currency
# PER US DOLLAR, and four as US DOLLARS PER UNIT (AUD, NZD, GBP and the euro
# already held). The units field is the quoted currency, so a USD-per pair is
# "$" and USD/KRW is "KRW"; every one moves in percent (derived.DELTA_UNITS).
# A separate list for the reason FRED_SIGNAL_SERIES is one: FRED_SERIES is the
# Monthly's set, and nothing reads these yet but the currency chapter.
#
# THE BAHT IS NOT HERE. DEXTHUS is in FRED_THAILAND_SERIES below, registered
# under namespace: thailand and trigger_eligible: false (the Thailand chapter's
# isolation, section 4.10), so no trigger can reach it through this list.
# ---------------------------------------------------------------------------
FRED_FX_SCAN_SERIES: list[SeriesSpec] = [
    SeriesSpec("usd_aud", "DEXUSAL", "USD per AUD (H.10)",                 "7", "$",   "daily"),
    SeriesSpec("usd_nzd", "DEXUSNZ", "USD per NZD (H.10)",                 "7", "$",   "daily"),
    SeriesSpec("usd_gbp", "DEXUSUK", "USD per GBP (H.10)",                 "7", "$",   "daily"),
    SeriesSpec("usd_cad", "DEXCAUS", "CAD per USD (H.10)",                 "7", "CAD", "daily"),
    SeriesSpec("usd_chf", "DEXSZUS", "CHF per USD (H.10)",                 "7", "CHF", "daily"),
    SeriesSpec("usd_sek", "DEXSDUS", "SEK per USD (H.10)",                 "7", "SEK", "daily"),
    SeriesSpec("usd_nok", "DEXNOUS", "NOK per USD (H.10)",                 "7", "NOK", "daily"),
    SeriesSpec("usd_dkk", "DEXDNUS", "DKK per USD (H.10)",                 "7", "DKK", "daily"),
    SeriesSpec("usd_brl", "DEXBZUS", "BRL per USD (H.10)",                 "7", "BRL", "daily"),
    SeriesSpec("usd_zar", "DEXSFUS", "ZAR per USD (H.10)",                 "7", "ZAR", "daily"),
    SeriesSpec("usd_krw", "DEXKOUS", "KRW per USD (H.10)",                 "7", "KRW", "daily"),
    SeriesSpec("usd_twd", "DEXTAUS", "TWD per USD (H.10)",                 "7", "TWD", "daily"),
    SeriesSpec("usd_inr", "DEXINUS", "INR per USD (H.10)",                 "7", "INR", "daily"),
    SeriesSpec("usd_sgd", "DEXSIUS", "SGD per USD (H.10)",                 "7", "SGD", "daily"),
    SeriesSpec("usd_hkd", "DEXHKUS", "HKD per USD (H.10)",                 "7", "HKD", "daily"),
    SeriesSpec("usd_myr", "DEXMAUS", "MYR per USD (H.10)",                 "7", "MYR", "daily"),
    SeriesSpec("usd_lkr", "DEXSLUS", "LKR per USD (H.10)",                 "7", "LKR", "daily"),
    SeriesSpec("usd_ves", "DEXVZUS", "VES per USD (H.10; Venezuela, administered rate)", "7", "VES", "daily"),
]

# THE BAHT, ISOLATED (section 4.10; the Thailand spec). Pulled by the same FRED
# path, registered in its own block under namespace: thailand.
FRED_THAILAND_SERIES: list[SeriesSpec] = [
    SeriesSpec("usd_thb", "DEXTHUS", "THB per USD (H.10)",                 "7", "THB", "daily"),
]

# SLOOS (AQ-3 part 2, 11 Oct 2026; the credit chapter's lending-standards
# measurable, the operator's ruling on AQ-2 part 2's choice 6). The Fed's Senior
# Loan Officer Opinion Survey: the NET PERCENTAGE of domestic banks tightening
# standards, quarterly (observed_at = the survey quarter's first day). A net
# share of banks, not a rate: its own block (fred_sloos) moves it in percentage
# points, where "%" alone would print a ten-point swing as 1,000 bp. Read off
# FRED 11 Oct 2026, last print 2026-07-01. The CRE split exists from 2013Q4 only.
FRED_SLOOS_SERIES: list[SeriesSpec] = [
    SeriesSpec("sloos_ci_large", "DRTSCILM", "SLOOS: net % of banks tightening C&I standards, large and middle-market firms", "6", "%", "quarterly"),
    SeriesSpec("sloos_ci_small", "DRTSCIS", "SLOOS: net % of banks tightening C&I standards, small firms", "6", "%", "quarterly"),
    SeriesSpec("sloos_cre_construction", "SUBLPDRCSC", "SLOOS: net % tightening CRE, construction and land development", "6", "%", "quarterly"),
    SeriesSpec("sloos_cre_nonres", "SUBLPDRCSN", "SLOOS: net % tightening CRE, nonfarm nonresidential", "6", "%", "quarterly"),
    SeriesSpec("sloos_cre_multifamily", "SUBLPDRCSM", "SLOOS: net % tightening CRE, multifamily", "6", "%", "quarterly"),
]

# THE REAL-ESTATE AND GLOBAL-RATES LEGS (AQ-3 part 2). Each read off FRED on 11
# Oct 2026 with its unit checked against the series page (Gotcha 2):
#   DRCRELEXFACBS  CRE loan delinquency (ex farmland), all banks, %, quarterly,
#                  last 2026-04-01 -- the real-estate chapter's headline row
#   CSUSHPINSA     Case-Shiller US national, index Jan 2000 = 100, NSA, monthly
#   DFF            effective fed funds, daily -- the US leg of the hedging cost
#   ECBDFR         ECB deposit facility rate, daily -- the euro leg
#   IRSTCI01JPM156N  Japan's call rate, monthly (OECD) -- the yen leg; FRED
#                  carries no daily BoJ rate, so the JGB hedge is monthly-stepped
#   IRLTLT01GBM156N  UK 10-year gilt, monthly average (OECD). The Bank of
#                  England's own database is disallowed to robots
#                  (/boeapps/database/_iadb-FromShowColumns.asp), so the gilt
#                  is this monthly series and not a daily one
#   DTWEXEMEGS     the Fed's nominal EMERGING-MARKET dollar index, index Jan
#                  2006 = 100, daily, NSA (read off FRED 12 Oct 2026, last print
#                  129.7052) -- the EM paper's request (AQ-14 Needs you 4, ruled
#                  yes); the EM chapter's structure row reads fred.dxy_em
FRED_AQ3_SERIES: list[SeriesSpec] = [
    SeriesSpec("cre_delinq", "DRCRELEXFACBS", "CRE loan delinquency rate (ex farmland), all banks", "6", "%", "quarterly"),
    SeriesSpec("case_shiller_national", "CSUSHPINSA", "S&P CoreLogic Case-Shiller US national home price index, NSA", "2", "idx", "monthly"),
    SeriesSpec("effr_daily", "DFF", "Effective federal funds rate, daily", "3", "%", "daily"),
    SeriesSpec("ecb_dfr", "ECBDFR", "ECB deposit facility rate", "7", "%", "daily"),
    SeriesSpec("jp_call_rate", "IRSTCI01JPM156N", "Japan call money rate, monthly (OECD)", "7", "%", "monthly"),
    SeriesSpec("gilt_10y", "IRLTLT01GBM156N", "UK 10-year government bond yield, monthly average (OECD)", "7", "%", "monthly"),
    SeriesSpec("dxy_em", "DTWEXEMEGS", "Nominal Emerging Market Economies US Dollar Index (DTWEXEMEGS, FRB; Jan 2006=100)", "7", "idx", "daily"),
]

# SR-43 / SR-49 (signal-triage batch 4, ST4-09 and ST4-15): the OECD long-term
# government bond yields the twin-deficit fit and the selloff-shape axis share --
# the "OECD-yields fetcher" is these series on the existing FRED pull. Each id
# and unit was read off its FRED series page on 12 Oct 2026 (Gotcha 2): all
# "Percent, Not Seasonally Adjusted", monthly averages. The UK (gilt_10y) and
# Japan (jp_10y) are already above; China's id 404s and is not used.
FRED_SR43_SERIES: list[SeriesSpec] = [
    SeriesSpec(f"oecd_10y_{c.lower()}", f"IRLTLT01{c}M156N",
               f"{name} 10-year government bond yield, monthly average (OECD)",
               "7", "%", "monthly")
    for c, name in (("US", "United States"), ("CA", "Canada"), ("DE", "Germany"),
                    ("FR", "France"), ("IT", "Italy"), ("ES", "Spain"),
                    ("NL", "Netherlands"), ("BE", "Belgium"), ("AU", "Australia"),
                    ("NZ", "New Zealand"), ("CH", "Switzerland"), ("SE", "Sweden"))
]
# 6e, THE REST (macro completeness; 16 Oct 2026, session B, branch 6e-rest): the
# FRED legs of the architecture's Session 3b (rates and policy), 3c (fiscal and
# demand) and the CPI lead composite's free components (Part 17). Every id was
# read off fredgraph on 16 Oct 2026 with its latest print (Gotcha 2: units from
# the series page, not a neighbouring line):
#   DFEDTARU / DFEDTARL   the target range, percent, daily (4.00 / 3.75)
#   EFFR                  effective fed funds, percent, daily (3.88); DFF above
#                         is the 7-day-a-week series, EFFR the business-day one
#   ECBESTRVOLWGTTRMDMNRT euro short-term rate (EURSTR), percent, daily (2.440)
#   IUDSOIA               SONIA, percent, daily (3.7324) -- the UK's overnight
#                         leg; Bank Rate on FRED (BOERUKM) stopped in 2017
#   MTSDS133FMS / MTSR133FMS / MTSO133FMS  the Monthly Treasury Statement's
#                         deficit, receipts and outlays, MILLIONS of dollars,
#                         monthly, not annualised (Sep 2026: -26,900 / 557,875 /
#                         584,775)
#   A091RC1Q027SBEA       federal government interest payments, BILLIONS, SAAR,
#                         quarterly (1,279.7)
#   FGRECPT               federal government current receipts, BILLIONS, SAAR,
#                         quarterly (6,056.0)
#   GFDEBTN               federal debt, total public debt, MILLIONS, quarterly
#                         (39,462,398)
#   BCNSDODNS             nonfinancial corporate business, debt securities and
#                         loans, MILLIONS, quarterly (Z.1; 15,698,562)
#   XTEXVA01KRM667S       Korea's exports of goods, US DOLLARS, monthly, SA
#                         (OECD; $100.4bn Aug 2026) -- the monthly series, not
#                         the 20-day print, which FRED does not carry
#   CUSR0000SAH1 / SEHA / SEHC  CPI shelter, rent of primary residence, owners'
#                         equivalent rent, index, monthly, SA
#   CUSR0000SAS / SACL1E / SETA02  CPI services, core goods (commodities less
#                         food and energy), used cars and trucks, index, SA
#   PPIFIS / WPSID61 / WPSID62  PPI final demand; processed goods for
#                         intermediate demand; unprocessed goods, index
#   IR / IREXFUELS        import prices, all and ex fuels, index
#   FRBATLWGT3MMAUMHWGO   the Atlanta Fed wage growth tracker, 3-month moving
#                         average of median wage growth, PERCENT (3.9), monthly
FRED_6E_SERIES: list[SeriesSpec] = [
    # Session 3b: rates and policy
    SeriesSpec("fed_target_upper", "DFEDTARU", "Federal funds target range, upper limit", "3", "%", "daily"),
    SeriesSpec("fed_target_lower", "DFEDTARL", "Federal funds target range, lower limit", "3", "%", "daily"),
    SeriesSpec("effr", "EFFR", "Effective federal funds rate, business days", "3", "%", "daily"),
    SeriesSpec("estr", "ECBESTRVOLWGTTRMDMNRT", "Euro short-term rate (EURSTR), volume-weighted trimmed mean", "7", "%", "daily"),
    SeriesSpec("sonia", "IUDSOIA", "Sterling overnight index average (SONIA)", "7", "%", "daily"),
    # Session 3c: fiscal and demand
    SeriesSpec("mts_deficit", "MTSDS133FMS", "Monthly Treasury Statement: federal surplus or deficit (-), millions, monthly", "8", "M", "monthly"),
    SeriesSpec("mts_receipts", "MTSR133FMS", "Monthly Treasury Statement: total receipts, millions, monthly", "8", "M", "monthly"),
    SeriesSpec("mts_outlays", "MTSO133FMS", "Monthly Treasury Statement: total outlays, millions, monthly", "8", "M", "monthly"),
    SeriesSpec("fed_interest_payments", "A091RC1Q027SBEA", "Federal government interest payments, billions SAAR", "8", "B", "quarterly"),
    SeriesSpec("fed_current_receipts", "FGRECPT", "Federal government current receipts, billions SAAR", "8", "B", "quarterly"),
    SeriesSpec("fed_debt_total", "GFDEBTN", "Federal debt: total public debt, millions", "8", "M", "quarterly"),
    SeriesSpec("nonfin_corp_debt", "BCNSDODNS", "Nonfinancial corporate business: debt securities and loans, millions (Z.1)", "6", "M", "quarterly"),
    SeriesSpec("korea_exports", "XTEXVA01KRM667S", "Korea exports of goods, US dollars, monthly, SA (OECD)", "7", "$", "monthly"),
    # The CPI lead composite's free components (architecture Part 17)
    SeriesSpec("cpi_shelter", "CUSR0000SAH1", "CPI: shelter, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_rent", "CUSR0000SEHA", "CPI: rent of primary residence, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_oer", "CUSR0000SEHC", "CPI: owners' equivalent rent of residences, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_services", "CUSR0000SAS", "CPI: services, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_core_goods", "CUSR0000SACL1E", "CPI: commodities less food and energy commodities, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_used_cars", "CUSR0000SETA02", "CPI: used cars and trucks, SA", "4", "idx", "monthly"),
    SeriesSpec("ppi_final_demand", "PPIFIS", "PPI: final demand, SA", "4", "idx", "monthly"),
    SeriesSpec("ppi_intermediate", "WPSID61", "PPI: processed goods for intermediate demand, SA", "4", "idx", "monthly"),
    SeriesSpec("ppi_unprocessed", "WPSID62", "PPI: unprocessed goods for intermediate demand, SA", "4", "idx", "monthly"),
    SeriesSpec("import_prices", "IR", "Import price index, all commodities", "4", "idx", "monthly"),
    SeriesSpec("import_prices_ex_fuel", "IREXFUELS", "Import price index, all imports excluding fuels", "4", "idx", "monthly"),
    SeriesSpec("atl_wage_tracker", "FRBATLWGT3MMAUMHWGO", "Atlanta Fed wage growth tracker, 3-month moving average of median wage growth, percent", "1", "%", "monthly"),
]

# BATCH 7, GROUP A (items 46 and 48; 6e-releases, 16 Oct 2026, session B): the
# release lenses' FRED legs. Every id, its first and latest observation and its
# unit were read off FRED (fredgraph.csv and the series page) on 16 Oct 2026;
# all monthly series run to Sep 2026 unless noted.
#   CPIENGSL / CPIUFDSL   CPI energy, CPI food, index, SA (the decomposition)
#   CUSR0000SASLE         CPI services less energy services (core services), SA
#   CUSR0000SAC           CPI commodities (goods), SA -- goods against services
#   MEDCPIM158SFRBCLE / TRMMEANCPIM158SFRBCLE  the Cleveland Fed median and 16%
#                         trimmed-mean CPI, PERCENT CHANGE AT ANNUAL RATE, from
#                         1983 (filing note 1: not pulled before)
#   CUSR0000SETG01 / SAS4  airline fares; transportation services (the
#                         pass-through basket), SA
#   PCU484484             PPI, truck transportation (the basket's freight leg),
#                         index Dec 2003 = 100, NSA
#   USPRIV / USEHS        private payrolls; private education and health
#                         services, THOUSANDS (cyclical core = the difference)
#   UNEMPLOY              unemployed, THOUSANDS (openings per unemployed)
#   ICSA / CCSA           initial and continuing claims, NUMBER, weekly (Sat)
#   LNS13026638           unemployed, permanent job losers, THOUSANDS, from 1994
#   LNS11300060           participation rate, 25-54, PERCENT
#   TEMPHELPS             temporary help services, THOUSANDS, from 1990
#   AWHI                  aggregate weekly hours index, production and
#                         nonsupervisory, total private, 2002 = 100
#   ECIALLCIV / ECIWAG    ECI total compensation (civilian); wages and salaries
#                         (private), index, QUARTERLY (to Q2 2026)
#   FRBATLWGT3MMAUMHWGJMJSW / ...JMJST  the Atlanta Fed tracker for job
#                         switchers and stayers, PERCENT, 3-month moving average
#   SMS00000000000000021 / ...22  diffusion indexes, 1- and 3-month span, TOTAL
#                         NONFARM ACROSS STATES (State and Metro), to Aug 2026 --
#                         the keyless stand-in for the CES industry indexes,
#                         whose hosts (api.bls.gov, data.bls.gov) disallow every
#                         agent in robots.txt (see docs/briefs/6e-releases-notes.md)
#   ECBASSETSW            Eurosystem total assets, EURO millions, weekly (the
#                         6e-rest gap; unit EUR_M, ruling (a)5 of 16 Oct)
#   CUSR0000S... (20)     the CPI diffusion's categories, index, SA (below)
FRED_RELEASES_SERIES: list[SeriesSpec] = [
    # Item 46: the decomposition, the pass-through basket
    SeriesSpec("cpi_energy", "CPIENGSL", "CPI: energy, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_food", "CPIUFDSL", "CPI: food, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_core_services", "CUSR0000SASLE", "CPI: services less energy services, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_commodities", "CUSR0000SAC", "CPI: commodities (all goods), SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_median", "MEDCPIM158SFRBCLE", "Cleveland Fed median CPI, percent change at annual rate, monthly", "4", "%", "monthly"),
    SeriesSpec("cpi_trimmed_mean", "TRMMEANCPIM158SFRBCLE", "Cleveland Fed 16% trimmed-mean CPI, percent change at annual rate, monthly", "4", "%", "monthly"),
    SeriesSpec("cpi_airline_fares", "CUSR0000SETG01", "CPI: airline fares, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_transport_services", "CUSR0000SAS4", "CPI: transportation services, SA", "4", "idx", "monthly"),
    SeriesSpec("ppi_truck_freight", "PCU484484", "PPI by industry: truck transportation, index Dec 2003 = 100, NSA", "4", "idx", "monthly"),
    # Item 48, lenses 1-6: employment
    SeriesSpec("payrolls_private", "USPRIV", "All employees, total private, thousands, SA", "1", "K", "monthly"),
    SeriesSpec("payrolls_edu_health", "USEHS", "All employees, private education and health services, thousands, SA", "1", "K", "monthly"),
    SeriesSpec("unemployed_level", "UNEMPLOY", "Unemployment level, thousands, SA", "1", "K", "monthly"),
    SeriesSpec("claims_initial", "ICSA", "Initial claims, number, weekly, SA", "1", "N", "weekly"),
    SeriesSpec("claims_continuing", "CCSA", "Continued claims (insured unemployment), number, weekly, SA", "1", "N", "weekly"),
    SeriesSpec("permanent_job_losers", "LNS13026638", "Unemployed: permanent job losers, thousands, SA", "1", "K", "monthly"),
    SeriesSpec("lfpr_prime_age", "LNS11300060", "Labor force participation rate, 25-54, percent, SA", "1", "%", "monthly"),
    SeriesSpec("temp_help", "TEMPHELPS", "All employees, temporary help services, thousands, SA", "1", "K", "monthly"),
    SeriesSpec("agg_weekly_hours", "AWHI", "Index of aggregate weekly hours, production and nonsupervisory, total private, 2002 = 100", "1", "idx", "monthly"),
    SeriesSpec("eci_total", "ECIALLCIV", "Employment cost index: total compensation, civilian, index, quarterly", "1", "idx", "quarterly"),
    SeriesSpec("eci_wages", "ECIWAG", "Employment cost index: wages and salaries, private industry, index, quarterly", "1", "idx", "quarterly"),
    SeriesSpec("atl_wage_switchers", "FRBATLWGT3MMAUMHWGJMJSW", "Atlanta Fed wage growth tracker, job switchers, 3-month moving average, percent", "1", "%", "monthly"),
    SeriesSpec("atl_wage_stayers", "FRBATLWGT3MMAUMHWGJMJST", "Atlanta Fed wage growth tracker, job stayers, 3-month moving average, percent", "1", "%", "monthly"),
    SeriesSpec("diffusion_states_1m", "SMS00000000000000021", "Diffusion index, 1-month span, total nonfarm across states, SA", "1", "%", "monthly"),
    SeriesSpec("diffusion_states_3m", "SMS00000000000000022", "Diffusion index, 3-month span, total nonfarm across states, SA", "1", "%", "monthly"),
    # Ruling (a)5: the 6e-rest gap with a keyless path
    SeriesSpec("ecb_assets", "ECBASSETSW", "Eurosystem central bank total assets, euro millions, weekly", "7", "EUR_M", "weekly"),
    # Item 46a: the CPI diffusion's categories (with cpi_rent, cpi_oer,
    # cpi_used_cars and cpi_airline_fares, 24 in all; config/releases.yaml)
    SeriesSpec("cpi_c_food_home", "CUSR0000SAF11", "CPI: food at home, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_food_away", "CUSR0000SEFV", "CPI: food away from home, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_alcohol", "CUSR0000SAF116", "CPI: alcoholic beverages, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_gasoline", "CUSR0000SETB01", "CPI: gasoline (all types), SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_electricity", "CUSR0000SEHF01", "CPI: electricity, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_utility_gas", "CUSR0000SEHF02", "CPI: utility (piped) gas service, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_apparel", "CPIAPPSL", "CPI: apparel, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_new_vehicles", "CUSR0000SETA01", "CPI: new vehicles, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_vehicle_parts", "CUSR0000SETC", "CPI: motor vehicle parts and equipment, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_medical_goods", "CUSR0000SAM1", "CPI: medical care commodities, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_tobacco", "CUSR0000SEGA", "CPI: tobacco and smoking products, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_household", "CUSR0000SAH3", "CPI: household furnishings and operations, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_personal_care", "CUSR0000SAG1", "CPI: personal care, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_lodging", "CUSR0000SEHB", "CPI: lodging away from home, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_water_trash", "CUSR0000SEHG", "CPI: water and sewer and trash collection services, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_professional_med", "CUSR0000SEMC", "CPI: professional (medical) services, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_hospital", "CUSR0000SEMD", "CPI: hospital and related services, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_vehicle_repair", "CUSR0000SETD", "CPI: motor vehicle maintenance and repair, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_tuition", "CUSR0000SEEB", "CPI: tuition, other school fees, and childcare, SA", "4", "idx", "monthly"),
    SeriesSpec("cpi_c_video_audio", "CUSR0000SERA", "CPI: video and audio, SA", "4", "idx", "monthly"),
]

# BATCH 7, GROUP B (item 48 lenses 12-20; lenses-group-b, 18 Oct 2026, session B):
# the PPI and GDP lenses' FRED legs. Every id, its first and latest observation
# and its title were read off FRED (fredgraph.csv and the series page) on 18 Oct
# 2026; monthly series run to Sep 2026, quarterly to Q2 2026, unless noted.
#   WPSFD49116            PPI final demand less foods, energy and trade services,
#                         SA, from Aug 2013 (lens 14's core)
#   PPITSS                PPI final demand: trade services, SA, from Nov 2009 --
#                         the margin proxy (lens 14)
#   WPSID51..WPSID54      PPI intermediate demand by production flow, stages 1-4,
#                         SA, from Nov 2009 (lens 12's pipeline; stage 4 is the
#                         nearest final demand)
#   PCU523940523940       PPI portfolio management and investment advice, NSA,
#                         from Dec 2022 (PCU523920523920, the older industry code,
#                         stops in Dec 2022; lens 13)
#   PCU481111481111       PPI scheduled passenger air transportation, NSA (13)
#   PCU622622 / PCU621111621111  PPI hospitals; offices of physicians, NSA (13)
#   A191RL1Q225SBEA       real GDP, percent change at an annual rate (15)
#   LB0000031Q020SBEA     real final sales to private domestic purchasers,
#                         BILLIONS of chained dollars, SAAR (15's core)
#   DPCERY2Q224SBEA, A008RY2Q224SBEA, A011RY2Q224SBEA, A014RY2Q224SBEA,
#   A019RY2Q224SBEA, A822RY2Q224SBEA  contributions to real GDP's percent change,
#                         PERCENTAGE POINTS at an annual rate: consumption,
#                         nonresidential and residential fixed investment,
#                         inventories, net exports, government (15)
#   GDPDEF                the GDP implicit price deflator, index 2017 = 100
#   GDI                   gross domestic income, BILLIONS, SAAR (17; the gap is
#                         computed against GDP, stored as gdp_nominal)
#   Y034RC1Q027SBEA / B985RC1Q027SBEA  information processing equipment;
#                         software, BILLIONS, SAAR (16's AI-related split)
#   B009RC1Q027SBEA       nonresidential structures, BILLIONS, SAAR (16)
#   PRFIC1                real private residential fixed investment, BILLIONS of
#                         chained dollars, SAAR, from 2007 (16)
#   CP                    corporate profits after tax (without IVA and CCAdj),
#                         BILLIONS, SAAR (18)
#   DSPIC96 / W875RX1     real disposable personal income; real personal income
#                         excluding current transfer receipts, BILLIONS of chained
#                         dollars, SAAR, monthly to Aug 2026 (19)
#   PSAVERT               the personal saving rate, PERCENT, monthly (19)
#   GDPNOW                the Atlanta Fed's GDPNow, percent change at an annual
#                         rate, quarterly; each update is a vintage, so its path
#                         through the quarter is ALFRED's and the live pull's (20)
FRED_GROUP_B_SERIES: list[SeriesSpec] = [
    # Lenses 12-14: PPI
    SeriesSpec("ppi_fd_core_ex_trade", "WPSFD49116", "PPI: final demand less foods, energy and trade services, SA", "4", "idx", "monthly"),
    SeriesSpec("ppi_trade_services", "PPITSS", "PPI: final demand trade services, SA", "4", "idx", "monthly"),
    SeriesSpec("ppi_stage1", "WPSID51", "PPI: intermediate demand by production flow, stage 1, SA", "4", "idx", "monthly"),
    SeriesSpec("ppi_stage2", "WPSID52", "PPI: intermediate demand by production flow, stage 2, SA", "4", "idx", "monthly"),
    SeriesSpec("ppi_stage3", "WPSID53", "PPI: intermediate demand by production flow, stage 3, SA", "4", "idx", "monthly"),
    SeriesSpec("ppi_stage4", "WPSID54", "PPI: intermediate demand by production flow, stage 4, SA", "4", "idx", "monthly"),
    SeriesSpec("ppi_portfolio_mgmt", "PCU523940523940", "PPI by industry: portfolio management and investment advice, NSA", "4", "idx", "monthly"),
    SeriesSpec("ppi_airline_passenger", "PCU481111481111", "PPI by industry: scheduled passenger air transportation, NSA", "4", "idx", "monthly"),
    SeriesSpec("ppi_hospitals", "PCU622622", "PPI by industry: hospitals, NSA", "4", "idx", "monthly"),
    SeriesSpec("ppi_physicians", "PCU621111621111", "PPI by industry: offices of physicians, NSA", "4", "idx", "monthly"),
    # Lenses 15-20: GDP
    SeriesSpec("gdp_real_growth", "A191RL1Q225SBEA", "Real GDP, percent change at an annual rate, SA", "2", "%", "quarterly"),
    SeriesSpec("final_sales_pdp", "LB0000031Q020SBEA", "Real final sales to private domestic purchasers, billions of chained dollars, SAAR", "2", "B", "quarterly"),
    SeriesSpec("gdp_contrib_pce", "DPCERY2Q224SBEA", "Contribution to real GDP growth: personal consumption, pp at an annual rate", "2", "%", "quarterly"),
    SeriesSpec("gdp_contrib_nonres", "A008RY2Q224SBEA", "Contribution to real GDP growth: nonresidential fixed investment, pp", "2", "%", "quarterly"),
    SeriesSpec("gdp_contrib_residential", "A011RY2Q224SBEA", "Contribution to real GDP growth: residential fixed investment, pp", "2", "%", "quarterly"),
    SeriesSpec("gdp_contrib_inventories", "A014RY2Q224SBEA", "Contribution to real GDP growth: change in private inventories, pp", "2", "%", "quarterly"),
    SeriesSpec("gdp_contrib_net_exports", "A019RY2Q224SBEA", "Contribution to real GDP growth: net exports, pp", "2", "%", "quarterly"),
    SeriesSpec("gdp_contrib_government", "A822RY2Q224SBEA", "Contribution to real GDP growth: government consumption and investment, pp", "2", "%", "quarterly"),
    SeriesSpec("gdp_deflator", "GDPDEF", "GDP implicit price deflator, index 2017 = 100, SA", "4", "idx", "quarterly"),
    SeriesSpec("gdi_nominal", "GDI", "Gross domestic income, billions, SAAR", "2", "B", "quarterly"),
    SeriesSpec("inv_info_equipment", "Y034RC1Q027SBEA", "Private fixed investment: information processing equipment, billions, SAAR", "2", "B", "quarterly"),
    SeriesSpec("inv_software", "B985RC1Q027SBEA", "Private fixed investment: software, billions, SAAR", "2", "B", "quarterly"),
    SeriesSpec("inv_nonres_structures", "B009RC1Q027SBEA", "Private fixed investment: nonresidential structures, billions, SAAR", "2", "B", "quarterly"),
    SeriesSpec("inv_residential_real", "PRFIC1", "Real private residential fixed investment, billions of chained dollars, SAAR", "2", "B", "quarterly"),
    SeriesSpec("corp_profits_after_tax", "CP", "Corporate profits after tax (without IVA and CCAdj), billions, SAAR", "2", "B", "quarterly"),
    SeriesSpec("real_disp_income", "DSPIC96", "Real disposable personal income, billions of chained dollars, SAAR", "2", "B", "monthly"),
    SeriesSpec("real_income_ex_transfers", "W875RX1", "Real personal income excluding current transfer receipts, billions of chained dollars, SAAR", "2", "B", "monthly"),
    SeriesSpec("saving_rate", "PSAVERT", "Personal saving rate, percent", "2", "%", "monthly"),
    SeriesSpec("gdpnow", "GDPNOW", "Atlanta Fed GDPNow, percent change at an annual rate (each update a vintage)", "2", "%", "quarterly"),
]

# THE GLD TRUST'S EXPENSE RATIO (AQ-3 part 1 follow-up, 12 Oct 2026). The forward
# ounces between two archives are shares x the last archive's ounces per share,
# decayed by this ratio day by day: the Sponsor's fee is paid in gold, so each
# share's gold falls by the fee and nothing else (altdata/sources/spdr_gld.py).
# Re-read the ratio off the fund page when the trust changes its fee.
GLD_EXPENSE_RATIO = {
    "ratio": 0.0040,
    "source": ("State Street Global Advisors, the SPDR Gold Shares (GLD) fund page, "
               "ssga.com/us/en/intermediary/etfs/spdr-gold-shares-gld: Expense "
               "Ratio 0.40%"),
    "read": "2026-10-12",
}

# Everything the FRED pull fetches and the freshness roster watches.
FRED_PULL_SERIES: list[SeriesSpec] = (FRED_SERIES + FRED_SIGNAL_SERIES
                                      + FRED_FX_SCAN_SERIES + FRED_THAILAND_SERIES
                                      + FRED_SLOOS_SERIES + FRED_AQ3_SERIES
                                      + FRED_SR43_SERIES + FRED_6E_SERIES
                                      + FRED_RELEASES_SERIES + FRED_GROUP_B_SERIES)


# Quick lookup by key
SERIES_BY_KEY = {s.key: s for s in FRED_PULL_SERIES}


# Source enable/disable switches (v1 = FRED only)
ENABLED_SOURCES = {
    "fred":      True,
    # ON in ST-2: altdata/sources/eia.py reads it and reports STALE when off.
    "eia":       True,
    # ON in ST-2: altdata/sources/cftc.py reads it and reports STALE when off.
    "cftc":      True,
    # CoinGecko is not a source (ruled 13 Oct and 18 Oct 2026: its terms forbid a
    # point-in-time store); no switch is kept that one flag could turn into a
    # terms breach. See source_registry.yaml `coingecko` (retired).
}


def all_fred_ids() -> list[str]:
    """Convenience: just the FRED IDs as a flat list."""
    return [s.fred_id for s in FRED_PULL_SERIES]


def series_for_pillar(pillar: str) -> list[SeriesSpec]:
    return [s for s in FRED_SERIES if s.pillar == pillar]


# ---------------------------------------------------------------------------
# Options / GEX pipeline (Session -1 logger)
# ---------------------------------------------------------------------------

# Index/ETF core. The single-name universe comes from docs/architecture-v3.md,
# which is not committed yet -- SINGLE_NAMES stays empty until it lands rather
# than being guessed, since a wrong universe silently corrupts every pin stat.
INDEX_ETF_SYMBOLS: list[str] = ["SPY", "QQQ", "IWM"]
SINGLE_NAMES: list[str] = [
    "NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOGL",
    "TSLA", "MSTR", "COIN", "ASTS",
]
# SPX and SPCX join this universe when the paid vendor lands -- yfinance has no
# SPX index-option coverage, which is the gap Part B's vendor review exists to
# close. Adding them here before then would produce empty chains, not errors.
#
# As of 5 Sep these two are served by altdata.sources.massive_chain, INGESTION
# ONLY -- see MASSIVE_SYMBOLS below. They stay listed here because they remain
# pending for Greeks, which is the sense that matters downstream.
PENDING_VENDOR_SYMBOLS: list[str] = ["SPX", "SPCX"]

# Symbols only Massive can serve. Chains are captured and stored; no Greeks are
# computed for them, because this tier serves no IV for index underlyings and
# the solved-IV path is gated on tools/validate_iv_solver.py, which is red.
# Every row they produce carries greeks_status=pending_solver_gate and
# exposure_compute refuses it, so the deferral is enforced by the data rather
# than by remembering.
MASSIVE_SYMBOLS: list[str] = ["SPX", "SPCX"]

# True where spot must be inferred from put-call parity because the tier will
# not sell the underlying's level (I:SPX returns 403). False where the vendor
# serves an ordinary equity close.
MASSIVE_SPOT_FROM_PARITY: dict[str, bool] = {"SPX": True, "SPCX": False}

# TICKER REUSE FENCE. A symbol here has been used by more than one issuer, so
# reference data returns contracts belonging to a company that no longer owns
# the ticker. Contracts expiring before the date are dropped at ingestion.
#
# SPCX: the current underlying is Space Exploration Technologies Corp Class A,
# listed 2026-06-12, whose options first traded 2026-06-16 -- confirmed by the
# three most liquid contracts all opening that day. The same symbol previously
# belonged to a SPAC/new-issue ETF, and its contracts (expiring 2021-01-15 and
# 2026-01-16, strikes 16-35 against the current 70-145+) are still returned by
# an expired=true query. Blending them would join two unrelated companies into
# one series. This is the Part 26.2 #6 Security Master gap, fenced by hand
# until an identity layer exists.
UNDERLYING_VERIFIED_FROM: dict[str, str] = {"SPCX": "2026-06-16"}

# THE PAPER BID'S FOUR (AQ-8a; change order 10 Oct 2026, section 5 "Two-bid
# decomposition", the Part 9 ruling's GLD, SLV, IBIT and USO). Captured every
# night with the universe so the paper-bid leg -- net call-put OI and the
# 25-delta risk reversal (altdata/paper_bid.py) -- accrues from the merge; a
# night not captured is gone. CAPTURE ONLY: they are not in options_universe(),
# so they enter no exposure profile, no pin log and no dealer table -- those
# carry the 13 and their statistics are the 13's.
PAPER_BID_SYMBOLS: list[str] = ["GLD", "SLV", "IBIT", "USO"]


def options_universe() -> list[str]:
    """Symbols the yfinance chain fetcher pulls with Greeks. 13 today."""
    return INDEX_ETF_SYMBOLS + SINGLE_NAMES


def chain_universe() -> list[str]:
    """Every symbol the yfinance chain fetcher captures nightly: the 13 and the
    paper bid's four. 17 today."""
    return options_universe() + [s for s in PAPER_BID_SYMBOLS
                                 if s not in options_universe()]

def massive_universe() -> list[str]:
    """Symbols the Massive chain fetcher pulls. Ingestion only."""
    return list(MASSIVE_SYMBOLS)

def full_universe() -> list[str]:
    """Everything captured nightly, from either vendor. 15 symbols: 13 with
    full Greeks, 2 stored pending the solver gate."""
    return options_universe() + massive_universe()

# Pin-log tolerance. 25 basis points of spot, declared here so the logger and
# any later backfill agree on what counts as a hit.
PIN_TOLERANCE_BPS: float = 25.0

# Black-Scholes inputs. yfinance ships no greeks, so gamma is always computed
# from the chain's own IV.
RISK_FREE_RATE: float = 0.043

# ---------------------------------------------------------------------------
# Settlement semantics -- what a post-close capture is allowed to claim
# ---------------------------------------------------------------------------
#
# RULING, 5 Sep 2026. At the settled 16:10 ET capture, same-day contracts are
# expired or minutes from it. Their gamma is not a forward-looking dealer
# exposure; it is an artifact of quoting corpses. So the settled EOD profile
# EXCLUDES DTE=0 from every exposure aggregate, by declared semantic rule
# rather than as a numerical workaround.
#
# What the rule does NOT do:
#   * It does not discard the rows. The 0DTE bucket is still reported, carrying
#     its OI STRUCTURE, with its greeks marked not_meaningful_at_settlement.
#     Open interest at settlement is a fact; gamma at settlement is not.
#   * It does not touch OI constructs. Max pain and the OI quality gates read
#     every row, 0DTE included -- they were never distorted by this, because
#     the distortion came from the MIN_T floor on gamma, not from the OI.
#   * It does not apply intraday. At the 09:45 capture the same contracts have
#     hours of life and real two-sided quotes, and that is where 0DTE GEX is
#     genuinely computable. 0DTE greeks are the intraday cadence's property.
#
# A capture is "settled" if it was taken at or after this ET time.
SETTLEMENT_ET_HOUR: int = 16
SETTLEMENT_ET_MINUTE: int = 0
SETTLED_0DTE_RULE: str = "exclude_dte0_from_exposure_aggregates_v1"
SETTLED_0DTE_GREEKS_LABEL: str = "not_meaningful_at_settlement"

# MIN_T IS A NUMERICAL GUARD AND MUST NEVER BE LOAD-BEARING. It exists so a
# near-zero time to expiry cannot divide by zero -- not so that a number can be
# produced where none is meaningful. Any bucket whose floored rows carry more
# than this share of its |GEX| is flagged, because at that point the floor is
# no longer preventing an error, it is manufacturing the answer.
MIN_T_LOAD_BEARING_SHARE: float = 0.05

# Sign convention marker written onto every computed output. Bump this string
# if the dealer-positioning assumption below ever changes.
CONVENTION_VERSION: str = "dealers-hand-v1"
CONVENTION_CAVEAT: str = (
    "Standard signing assumption: dealers are long calls (+gamma) and short "
    "puts (-gamma). This is a convention, not observed positioning -- actual "
    "dealer books are unobservable from public chains. Flip-side readings "
    "(customer-hand) invert every sign."
)

# Local data lake (gitignored).
#
# The computed-profile directory and the pin log are env-overridable for the
# same reason BACKUP_DIR is -- a caller that is not this working tree needs to
# retarget them without a code edit. The concrete caller is the CI gate:
# `data/` is gitignored, so on a fresh checkout these two paths point at
# nothing, and every signal that resolves through them reads as MISSING. That
# is correct for real data and wrong for a test that needs to exercise the
# not-missing path. See tools/validate_register.py group E.
CHAIN_DIR: str = "data/chains"
COMPUTED_DIR: str = os.environ.get("CHESTER_COMPUTED_DIR", "data/computed")
PIN_LOG_PATH: str = os.environ.get("CHESTER_PIN_LOG_PATH", "data/pin_log.csv")

# Which snapshot represents a session, when a day holds several. Matches the
# systemd timer's 16:10 ET firing: the EOD profile is meant to describe the book
# at the close, so the capture nearest the bell wins.
#
# This is declared rather than inferred because the alternative -- "the newest
# file" -- is wrong in a way that hides. A snapshot taken late in the evening
# has already lost the day's 0DTE contracts to expiry, so it silently drops the
# bucket that carries most of the gamma, and file mtime is not an observation
# time at all: a copy, a restore or a backup rewrites it.
EOD_SNAPSHOT_TARGET_ET: str = "16:10"

# Dated dealer-delta unwind, one row per (session, symbol, expiry). Kept out of
# the pin log because it is many rows per symbol per day, where the pin log is
# deliberately exactly one -- mixing the two cardinalities in one file would
# make every pin-rate query start with a de-duplication step.
EXPIRATION_RELEASE_PATH: str = "data/expiration_release.csv"

# Off-box backup for the raw chains. They are the one asset in this system
# that cannot be re-fetched -- yfinance serves no history -- so every run
# copies the day's chains somewhere that is not this laptop.
# Env-overridable so the VPS can retarget it without a code edit.
BACKUP_DIR: str = os.environ.get(
    "CHESTER_BACKUP_DIR",
    "C:/Users/arich/OneDrive/chester-reports/chains",
)

# ---------------------------------------------------------------------------
# Data-quality gates (tools/quality_gates.py)
# ---------------------------------------------------------------------------

# Liquidity floor -- a HARD RULE, declared in advance. Below these a symbol is
# excluded from skew and OI-percentile work entirely, not merely downgraded:
# confident-looking percentiles on thin books are worse than no metric.
LIQUIDITY_MIN_TOTAL_OI: float = 25_000.0
LIQUIDITY_MIN_TOTAL_VOLUME: float = 2_000.0

# IV surface roughness ceiling: normalised mean |second difference| of IV across
# adjacent strikes, median over expiry/right series. PROVISIONAL -- a normalised
# roughness figure has no natural scale, and calibrating it against the same
# symbols it judges would be circular. Revisit once a real sample exists.
IV_ROUGHNESS_MAX: float = 0.35

# ---------------------------------------------------------------------------
# IV solver validation gate (tools/validate_iv_solver.py)
# ---------------------------------------------------------------------------

# SPX goes live on solved IV only when SPY-via-solver reproduces
# SPY-via-yfinance inside these bounds. Declared BEFORE the first comparison is
# run, so the gate cannot be quietly widened to fit whatever came out.
#
# Reasoning for each number:
#  - 2 vol points is the width of a typical listed bid/ask in vol terms, so
#    agreeing inside it means the two methods differ by less than the market's
#    own quote uncertainty.
#  - The flip is a level traders act on; 0.25% of spot is ~1.9 points on SPY,
#    below the 1-point strike grid, so tighter would be measuring rounding.
#  - Walls are strikes, so they either match or they do not. Exact.
#  - Dollar gamma is a magnitude, not a level; 10% keeps a scale error visible
#    while tolerating the different IV each method assigns to the same strike.
#    THE 10% IS UNCHANGED; WHAT IT DIVIDES BY CHANGED, 5 Sep. See
#    IV_SOLVER_GAMMA_DENOMINATOR below.
#  - Below an 80% solve rate on the eligible OTM wing the profile is being
#    built from too little of the book to compare fairly.
IV_SOLVER_MAX_MEDIAN_IV_DIFF: float = 0.02      # vol points, absolute
IV_SOLVER_MAX_FLIP_DIFF_PCT: float = 0.25       # percent of spot
IV_SOLVER_WALLS_MUST_MATCH_EXACTLY: bool = True
IV_SOLVER_MAX_GAMMA_DIFF_PCT: float = 10.0      # percent of dollar gamma/1%
IV_SOLVER_MIN_SOLVE_RATE: float = 0.80          # of the eligible OTM wing

# DTE=0 IS EXCLUDED FROM THE SOLVER-VS-YFINANCE IV COMPARISON. Declared here
# rather than buried in the gate, because a silent exclusion is
# indistinguishable from a bug, and this one changes what the gate certifies.
#
# The reason is not that 0DTE is inconvenient. It is that at the 16:10 ET close
# snapshot the day's expiring contracts have no usable two-sided market left:
# measured across all 13 symbols on 2026-09-04, the solver could price between
# 0.0% and 2.4% of 0DTE contracts carrying open interest, rejecting 60-70% of
# them as `wide_spread` -- a penny-wide market on a two-cent option is a 100%
# relative spread. Comparing two IV series where one of them barely exists is
# not a measurement of agreement.
#
# THE SOLVER STILL SOLVES 0DTE IN PRODUCTION. This flag governs the validation
# comparison only; nothing is carved out of iv_solver itself.
IV_SOLVER_EXCLUDE_DTE0: bool = True

# ...and because excluding it silently would leave 0DTE unchecked, the bucket
# gets its own substitute check: its GEX PROFILE under solved IV must match the
# profile under yfinance IV within IV_SOLVER_MAX_GAMMA_DIFF_PCT. A profile is an
# integral over strikes, so it tolerates per-strike IV noise that a strike-by-
# strike comparison would flag.
#
# That argument holds only while enough of the bucket actually solves. Below
# this coverage the two "profiles" are integrals over different domains, and
# the check reports INCONCLUSIVE rather than a pass it has not earned.
IV_SOLVER_DTE0_MIN_COVERAGE: float = 0.50       # of 0DTE contracts with OI

# GAMMA COMPARISON DENOMINATOR. "gross" divides the solver-vs-yfinance gamma
# error by the book's GROSS |GEX|; "net" divides it by net dollar gamma, which
# is what the gate did until 5 Sep.
#
# Net is ill-conditioned and the diagnostic is unambiguous. Net dollar gamma is
# a signed residual of two large offsetting halves, so the same absolute error
# reads wildly differently depending on how much of the book happens to cancel.
# Splitting SPY ex-0DTE into directly-solved and ITM-twinned strata gave 5.1%
# and 5.2% -- while their COMBINATION gave 27.6%, because the strata net
# -4.67bn and +3.21bn and the errors add while the magnitudes cancel. QQQ read
# 82.7% on net and 4.34% on gross, and it was the worst symbol only because its
# net is 5% of its gross book, the smallest ratio in the universe.
#
# On a gross denominator all 13 symbols clear the SAME 10% bar, worst 9.53%.
# This is a change of what the ratio measures, not a relaxation of how much
# error it tolerates -- the threshold is untouched.
#
# WHAT IT DOES NOT CLAIM, and why the absolute figure is reported beside it:
# this does NOT say the solver reproduces net dealer gamma to 10%. SPY's net
# differs by $402M on a -$1.45bn base and that is real. It says the two IV
# sources agree to ~2% of the gamma actually in the book. Anything acting on
# the net needs the absolute uncertainty, which the gate now prints and which
# no ratio can substitute for.
IV_SOLVER_GAMMA_DENOMINATOR: str = "gross"      # "gross" | "net"


# ---------------------------------------------------------------------------
# GATE 1.5 -- IBKR COMMISSION SCHEDULE
# ---------------------------------------------------------------------------
# THE RULING, 5 Sep 2026. IB Gateway refuses What-If under Read-Only API --
# measured on the VPS, error text "The API interface is currently in Read-Only
# mode". What-If travels as a placeOrder message with whatIf=True, so a Gateway
# that blocks order submission blocks previews with it. Read-Only STAYS ON
# through the hand-placed-orders phase and comes off at Gate 2 by design, when
# code-side guards replace it. So expected_cost comes from this schedule until
# then, and altdata/sources/ibkr_whatif.py is kept intact for Gate 2 rather
# than deleted.
#
# US STOCKS -- VERIFIED 2026-09-05.
# source: Client Portal, hand-read by operator.
# This account is on FIXED pricing, not Tiered: USD 0.005 per share, $1.00
# minimum per order, 1% of trade value maximum, ALL-IN. Both readings that
# 26.17 required are now closed -- the figures themselves, and the account's
# structure. Client Portal is the only place the structure is visible; the API
# does not expose it, which is why it was an assumption until a human looked.
#
# This REPLACES the Tiered figures ($0.0035/share, $0.35 floor) declared here
# on 5 Sep 2026 when interactivebrokers.com returned HTTP 403 to automated
# fetches of commissions-stocks.php. Those numbers were wrong in both
# directions at once: the wrong structure, and -- because Fixed bundles the
# pass-throughs Tiered bills separately -- the wrong claim about what the
# estimate covers. The FlashAlpha check earned its keep here.
IBKR_COMMISSION_SCHEDULE_SOURCE: str = (
    "https://www.interactivebrokers.com/en/pricing/commissions-stocks.php")
IBKR_COMMISSION_SCHEDULE_AS_OF: str = "2026-09-05"
IBKR_COMMISSION_SCHEDULE_VERIFIED: bool = True
IBKR_COMMISSION_SCHEDULE_VERIFIED_ON: str = "2026-09-05"
IBKR_COMMISSION_SCHEDULE_VERIFIED_BY: str = (
    "Client Portal, hand-read by operator")
IBKR_COMMISSION_SCHEDULE_VERIFY_NOTE: str = (
    "US STOCKS verified 2026-09-05, hand-read from IBKR Client Portal: this "
    "account is on FIXED pricing -- $0.005/share, $1.00 order minimum, 1% of "
    "trade value cap, all-in. Client Portal is the only place the "
    "Fixed-vs-Tiered structure is visible; the API does not expose it. US "
    "OPTIONS are NOT verified and still carry Tiered per-contract bands, which "
    "do not describe a Fixed account -- see IBKR_OPT_COMMISSION_VERIFIED.")

# Which structure THIS account is on. No longer an assumption: read off Client
# Portal on 2026-09-05. Fixed bundles exchange and regulatory fees into the
# headline rate; Tiered bills them separately.
IBKR_ACCOUNT_COMMISSION_STRUCTURE: str = "fixed"

# US STOCKS, IBKR Pro FIXED. Verified -- see above.
IBKR_STK_FIXED_PER_SHARE: float = 0.005
IBKR_STK_FIXED_MIN_PER_ORDER: float = 1.00
IBKR_STK_FIXED_MAX_PCT_OF_TRADE: float = 0.01
IBKR_STK_COMMISSION_VERIFIED: bool = True

# Fixed is ALL-IN for stocks: exchange, clearing and regulatory pass-throughs
# are inside the per-share rate, not billed on top. So the stock estimate is
# the whole number, not a floor -- the opposite of what this file said while it
# assumed Tiered. Nothing is excluded, so nothing is named.
IBKR_STK_IS_ALL_IN: bool = True
IBKR_STK_EXCLUSIONS: tuple = ()

# US OPTIONS, IBKR Pro TIERED, per contract by premium band:
# (premium_at_or_above, per_contract). Ordered high to low.
#
# UNVERIFIED, AND STRUCTURALLY STALE. These are Tiered bands on an account now
# known to be Fixed, so they do not describe this account's option costs at
# all. They are left in place rather than guessed at: inventing a Fixed
# per-contract rate to fill the hole is precisely the FlashAlpha move. The
# mismatch is declared here and rides in every option estimate's packet, so an
# option cost cannot be read as trustworthy by accident. No option has been
# traded; this blocks nothing today.
IBKR_OPT_SCHEDULE_STRUCTURE: str = "tiered"
IBKR_OPT_COMMISSION_VERIFIED: bool = False
IBKR_OPT_TIERED_PER_CONTRACT: tuple = ((0.10, 0.65), (0.05, 0.50), (0.0, 0.25))
IBKR_OPT_TIERED_MIN_PER_ORDER: float = 1.00

# Tiered quotes the broker's own commission only; the pass-throughs below are
# billed on top and vary by venue, order type and whether the order added or
# removed liquidity -- none knowable before the fill. Recorded as named
# exclusions rather than folded into a fudge factor.
IBKR_OPT_IS_ALL_IN: bool = False
IBKR_OPT_EXCLUSIONS: tuple = ("exchange fees", "clearing fees",
                              "regulatory fees (SEC/FINRA)",
                              "liquidity add/remove adjustments")
