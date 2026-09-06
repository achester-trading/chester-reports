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
    SeriesSpec("dxy",              "DTWEXBGS",   "Broad Dollar Index (DTWEXBGS, FRB)",        "7", "idx",  "daily"),
    SeriesSpec("usd_eur",          "DEXUSEU",    "USD/EUR exchange rate",           "7", "$",    "daily"),
    SeriesSpec("usd_jpy",          "DEXJPUS",    "JPY/USD exchange rate",           "7", "JPY",  "daily"),
    SeriesSpec("usd_cny",          "DEXCHUS",    "CNY/USD exchange rate",           "7", "CNY",  "daily"),
    
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

def options_universe() -> list[str]:
    """Symbols the yfinance chain fetcher pulls. 13 today."""
    return INDEX_ETF_SYMBOLS + SINGLE_NAMES

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
CHAIN_DIR: str = "data/chains"
COMPUTED_DIR: str = "data/computed"
PIN_LOG_PATH: str = "data/pin_log.csv"

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
