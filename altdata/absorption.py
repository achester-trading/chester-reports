"""
Duration Absorption and the rates flags -- signal-triage ST-4 (docs/change-order-
signal-triage-2026-09-25.md, sections 2.1.2 to 2.1.4; st-t1-rest, 18 Oct 2026).

    python -m altdata.absorption compute [--as-of T] [--from DAY] [--dry-run]
    python -m altdata.absorption show [--as-of T]

Computed from the store, written as calc.* rows by the features pass (it rides
altdata/market_features.compute, after the correlation layer, never fatal), and
read by the Monthly's Duration Absorption block and Rate machine summary
(daily_cascade/absorption_block.py). Every flag is DISPLAY AND MODIFIER ONLY, as
the order grants; nothing here enters a composite, a trigger or the object.

SUPPLY (SR-23, G-14)
  calc.net_supply_1m       the month's net marketable issuance (MSPD, held by the
                           public, month on month) less the month's change in the
                           Fed's Treasury holdings (TREAST, month-end), dollars
  calc.net_supply_12m      the last twelve months of it, consecutive months only
  calc.net_supply_12m_gdp  over nominal GDP (the latest quarter, SAAR), percent
  calc.priv_residual_12m   the twelve months' net supply less foreign holders'
                           twelve-month change (TIC official + private), dollars:
                           what domestic price-sensitive hands absorbed
ABSORBERS (SR-26, SR-27)
  calc.tic_official_12m, calc.tic_private_12m   twelve-month changes, dollars
  calc.tic_official_share  official holdings over all foreign holdings, percent
  calc.tic_custodial_share the custodial centres' share (config: CUSTODIAL)
  calc.foreign_ust_share_lt  Treasuries' share of net foreign long-term purchases
                           over twelve months (TIC flows lines 5 + 10 over line 3)
  calc.abs_fragility       1 when, over twelve months, the Treasury share fell, the
                           custodial share rose and the official share fell (SR-27's
                           candidate rule); display only
PRICE (SR-22, G-32)
  calc.abs_stress          on each coupon auction day: 1 when bid-to-cover sat in
                           its tenor's bottom decile on this and the previous coupon
                           auction, or the dealers took more than 20% (G-32's rule
                           until a tail source exists)
THE FED-MARKET GAP (SR-21, G-4, G-31)
  calc.fed_mkt_gap_12m     the futures-implied rate twelve months ahead (100 less
                           that month's fed funds future) less the SEP median dot for
                           the year-end nearest twelve months out (FRED FEDTARMD), bp
  calc.cred_stress         1 when |the 12m gap| > 50 bp; the order's other leg
                           (60% of a move priced against the last signalled
                           direction) needs the signalled direction, NOT TRACKED
  calc.pm_disagree_fed     the venue's normalised probability less the futures-
                           implied probability on the next meeting, the larger side,
                           in points (altdata.prediction_markets' comparison)
DE-ANCHORING (SR-24)
  calc.deanchor            1 when the 5y5y breakeven sat above its 2022 high for 20
                           sessions AND the Fed Board's CIE is above its 2022 high or
                           UMich 5-10y expectations >= 3.5% for three months
  calc.be5y5y_range_pos    the 5y5y's percentile within 2010 to the day
  calc.producers_spot_ratio  GUNR over DBC (G-15: GUNR as the producers proxy; DBC
                           the stored broad commodity basket), a ratio; a note, no
                           rights
CREDIT AND THE AI CAPEX LOOP (SR-16, SR-25)
  calc.aa_bbb_oas_diff     BBB OAS less AA OAS, bp
  calc.self_fund_ratio     the five hyperscalers' operating cash flow over capex,
                           by calendar frame (EDGAR)
  calc.hs_netdebt_12m      their year-end long-term debt less cash, year on year,
                           dollars (EDGAR instant frames)
  calc.mu_inv_days         Micron's inventory over the quarter's cost of goods x 91
                           (EDGAR company concepts)
GOLD (SR-20, G-34)
  calc.cb_gold_12m         twelve months of central-bank net gold purchases (IMF IFS
                           aggregate), tonnes

NOT TRACKED (rule 30: the by-hand audit of 16 Oct removed every recurring manual key
but the global PMI; no keyless source within terms reads them):
  calc.net_supply_proj_12m (manual.cbo_deficit_path), calc.fed_mkt_gap_m1 and _m2
  (manual.fed_signalled_direction), calc.ai_long_share
  (manual.ig_issuance_10y_plus_share, manual.ai_ig_issuance_share).
"""

from __future__ import annotations

import calendar
import datetime as dt
import logging
from typing import Optional

from . import observations

log = logging.getLogger(__name__)

TONNE_OZ = 32150.7466
CUSTODIAL = ("United Kingdom", "Belgium", "Ireland", "Luxembourg", "Cayman Islands")
COUPON_PREFIXES = ("Note:", "Bond:", "TIPS:")
DEALER_MAX = 0.20
BTC_DECILE = 0.10
GAP_BP = 50.0
DEANCHOR_YEAR = "2022"
DEANCHOR_SESSIONS = 20
UMICH_BAR = 3.5
RANGE_FROM = "2010-01-01"
PRODUCERS, SPOT = "yfinance.mkt_gunr", "yfinance.mkt_dbc"

FEATURES: dict[str, str] = {
    "calc.net_supply_1m": "net marketable issuance less the Fed's Treasury change, month",
    "calc.net_supply_12m": "the same over twelve consecutive months",
    "calc.net_supply_12m_gdp": "twelve months' net supply over nominal GDP, percent",
    "calc.priv_residual_12m": "twelve months' net supply less foreign holders' change",
    "calc.tic_official_12m": "foreign official holdings' twelve-month change",
    "calc.tic_private_12m": "foreign private holdings' twelve-month change",
    "calc.tic_official_share": "official over all foreign holdings, percent",
    "calc.tic_custodial_share": "the custodial centres' share of foreign holdings, percent",
    "calc.foreign_ust_share_lt": "Treasuries' share of net foreign long-term purchases, 12m",
    "calc.abs_fragility": "SR-27's candidate rule, 1 or 0; display only",
    "calc.abs_stress": "G-32's absorption-stress rule per coupon auction, 1 or 0",
    "calc.fed_mkt_gap_12m": "the futures-implied rate 12m ahead less the SEP median dot, bp",
    "calc.cred_stress": "|12m gap| > 50 bp, 1 or 0 (the signalled-direction leg not tracked)",
    "calc.pm_disagree_fed": "venue less futures-implied probability, next meeting, points",
    "calc.deanchor": "SR-24's de-anchoring rule, 1 or 0",
    "calc.be5y5y_range_pos": "the 5y5y breakeven's percentile within 2010 to the day",
    "calc.producers_spot_ratio": "GUNR over DBC",
    "calc.aa_bbb_oas_diff": "BBB less AA OAS, bp",
    "calc.self_fund_ratio": "hyperscalers' operating cash flow over capex, by frame",
    "calc.hs_netdebt_12m": "hyperscalers' long-term debt less cash, year on year",
    "calc.mu_inv_days": "Micron's inventory over the quarter's cost of goods x 91",
    "calc.cb_gold_12m": "twelve months of central-bank net gold purchases, tonnes",
}
NOT_TRACKED: dict[str, str] = {
    "calc.net_supply_proj_12m": "manual.cbo_deficit_path",
    "calc.fed_mkt_gap_m1": "manual.fed_signalled_direction",
    "calc.fed_mkt_gap_m2": "manual.fed_signalled_direction",
    "calc.ai_long_share": "manual.ig_issuance_10y_plus_share, manual.ai_ig_issuance_share",
}
HYPERSCALERS = ("AMZN", "GOOGL", "META", "MSFT", "ORCL")


# ---------------------------------------------------------------------------
# Reading the store
# ---------------------------------------------------------------------------
def series(db, key: str, as_of: Optional[str], instrument: Optional[str] = None
           ) -> list[tuple[str, float, str]]:
    """[(day, value, available_at)] knowable at as_of, oldest first."""
    if db is None:
        return []
    try:
        rows = db.as_of(key, as_of, instrument)
    except Exception:                                           # noqa: BLE001
        return []
    out = [(str(r["observed_at"])[:10], float(r["value_num"]), str(r["available_at"]))
           for r in rows if r.get("value_num") is not None]
    return sorted(out)


def instruments(db, key: str) -> list[str]:
    try:
        return list(db.instruments(key))
    except Exception:                                           # noqa: BLE001
        return []


def month(d: str) -> str:
    return d[:7]


def month_add(m: str, k: int) -> str:
    i = int(m[:4]) * 12 + int(m[5:7]) - 1 + k
    return f"{i // 12:04d}-{i % 12 + 1:02d}"


def month_end(m: str) -> str:
    y, mo = int(m[:4]), int(m[5:7])
    return f"{m}-{calendar.monthrange(y, mo)[1]:02d}"


def last_by_month(s: list[tuple]) -> dict[str, tuple]:
    out: dict[str, tuple] = {}
    for x in s:
        out[month(x[0])] = x
    return out


def latest_avail(*avails: str) -> str:
    """A row is knowable only once every input is (the features pass's rule)."""
    return max(a for a in avails if a)


# ---------------------------------------------------------------------------
# Supply and absorbers (monthly)
# ---------------------------------------------------------------------------
def net_supply(issuance: list[tuple], soma: list[tuple]) -> dict[str, tuple]:
    """{month: (dollars, available_at)}: issuance less the month-end change in
    the Fed's Treasuries (TREAST in MILLIONS, issuance in dollars)."""
    som = last_by_month(soma)
    out = {}
    for d, v, a in issuance:
        m = month(d)
        p = month_add(m, -1)
        if m in som and p in som:
            ch = (som[m][1] - som[p][1]) * 1e6
            out[m] = (v - ch, latest_avail(a, som[m][2]))
    return out


def rolling_12(by_month: dict[str, tuple]) -> dict[str, tuple]:
    """Twelve consecutive months' sum, keyed by the last month."""
    out = {}
    for m in sorted(by_month):
        ms = [month_add(m, -k) for k in range(12)]
        if all(x in by_month for x in ms):
            out[m] = (sum(by_month[x][0] for x in ms),
                      latest_avail(*(by_month[x][1] for x in ms)))
    return out


def change_12(by_month: dict[str, tuple]) -> dict[str, tuple]:
    out = {}
    for m, (v, a) in by_month.items():
        p = month_add(m, -12)
        if p in by_month:
            out[m] = (v - by_month[p][0], latest_avail(a, by_month[p][1]))
    return out


# ---------------------------------------------------------------------------
# The auction flag (per coupon auction)
# ---------------------------------------------------------------------------
def abs_stress(btc: dict[str, list[tuple]], dealer: dict[str, list[tuple]]
               ) -> list[tuple[str, str, int, str, str]]:
    """[(day, instrument, flag, trace, available_at)] on each coupon auction.
    Bottom decile: the tenor's own bid-to-cover history up to and including
    that auction."""
    events = []
    for inst, s in btc.items():
        if not inst.startswith(COUPON_PREFIXES):
            continue
        hist: list[float] = []
        for d, v, a in s:
            hist.append(v)
            srt = sorted(hist)
            cut = srt[int(BTC_DECILE * (len(srt) - 1))] if len(srt) >= 10 else None
            events.append((d, inst, v, cut is not None and v <= cut, a))
    events.sort()
    dl = {(inst, d): v for inst, s in dealer.items() for d, v, _ in s}
    out = []
    prev_low = False
    for d, inst, v, low, a in events:
        ds = dl.get((inst, d))
        two = low and prev_low
        big = ds is not None and ds > DEALER_MAX
        trace = (f"bid-to-cover {v:.2f}" + (" (bottom decile)" if low else "")
                 + ("; the previous coupon auction too" if two else "")
                 + (f"; dealers {100 * ds:.1f}% > 20%" if big else
                    f"; dealers {100 * ds:.1f}%" if ds is not None else "; dealers n/a"))
        out.append((d, inst, int(two or big), trace, a))
        prev_low = low
    return out


# ---------------------------------------------------------------------------
# The fed-market gap
# ---------------------------------------------------------------------------
def implied_12m(prices: dict[str, float], day: str) -> Optional[tuple[str, float]]:
    """(the contract month, 100 less its price) twelve months after the day's."""
    m = month_add(day[:7], 12)
    if m in prices:
        return m, 100.0 - prices[m]
    return None


def sep_dot(dots: list[tuple], day: str) -> Optional[tuple[str, float]]:
    """The SEP median for the year-end nearest twelve months out (FEDTARMD dates a
    year's dot on 1 Jan of that year)."""
    target = (dt.date.fromisoformat(day) + dt.timedelta(days=365))
    ye = str(target.year if target.month >= 7 else target.year - 1)
    hit = [x for x in dots if x[0][:4] == ye]
    return (ye, hit[-1][1]) if hit else None


# ---------------------------------------------------------------------------
# De-anchoring
# ---------------------------------------------------------------------------
def deanchor_on(be: list[tuple], cie: list[tuple], umich: list[tuple], day: str
                ) -> tuple[Optional[int], str]:
    """(1/0, trace), or (None, why) when the rule cannot be read."""
    y = DEANCHOR_YEAR
    hi = [v for d, v, _ in be if d[:4] == y]
    if not hi:
        return None, f"no {y} 5y5y in the store"
    upto = [x for x in be if x[0] <= day]
    last = upto[-DEANCHOR_SESSIONS:]
    leg1 = len(last) == DEANCHOR_SESSIONS and all(v > max(hi) for _, v, _ in last)
    cie_hi = [v for d, v, _ in cie if d[:4] == y]
    cie_now = [v for d, v, _ in cie if d <= day]
    leg_c = bool(cie_hi and cie_now and cie_now[-1] > max(cie_hi))
    um = [v for d, v, _ in umich if d <= day][-3:]
    leg_u = len(um) == 3 and all(v >= UMICH_BAR for v in um)
    on = int(leg1 and (leg_c or leg_u))
    trace = (f"5y5y above its {y} high of {max(hi):.2f}% for {DEANCHOR_SESSIONS} "
             f"sessions: {'yes' if leg1 else 'no'}; CIE above its {y} high: "
             f"{'yes' if leg_c else 'no' if cie_hi else 'not stored'}; UMich 5-10y "
             f">= {UMICH_BAR}% three months: {'yes' if leg_u else 'no' if um else 'not stored'}")
    return on, trace


def range_pos(be: list[tuple], day: str) -> Optional[float]:
    win = [v for d, v, _ in be if RANGE_FROM <= d <= day]
    if len(win) < 2:
        return None
    x = win[-1]
    return round(100.0 * sum(1 for v in win if v <= x) / len(win), 4)


# ---------------------------------------------------------------------------
# The rows
# ---------------------------------------------------------------------------
def compute_rows(db, as_of: Optional[str] = None, first_day: Optional[str] = None,
                 cutoff_day: Optional[str] = None) -> list[dict]:
    rows: list[dict] = []

    def emit(key: str, day: str, value, available: str, inst: Optional[str] = None):
        if value is None or (first_day and day < first_day):
            return
        rows.append({"registry_key": key, "instrument": inst, "observed_at": day,
                     "available_at": available, "value": value, "source": "calc",
                     "availability_kind": "observed"})

    # Supply
    ns = net_supply(series(db, "fiscaldata.mspd_net_marketable_issuance", as_of),
                    series(db, "fred.soma_treasuries", as_of))
    for m, (v, a) in ns.items():
        emit("calc.net_supply_1m", month_end(m), round(v, 2), a)
    ns12 = rolling_12(ns)
    gdp = series(db, "fred.gdp_nominal", as_of)
    for m, (v, a) in ns12.items():
        emit("calc.net_supply_12m", month_end(m), round(v, 2), a)
        g = [x for x in gdp if x[0] <= month_end(m)]
        if g:
            emit("calc.net_supply_12m_gdp", month_end(m),
                 round(100.0 * v / (g[-1][1] * 1e9), 4), latest_avail(a, g[-1][2]))
    # Absorbers
    off = {month(d): (v, a) for d, v, a in series(db, "tic.official_holdings", as_of)}
    prv = {month(d): (v, a) for d, v, a in series(db, "tic.private_holdings", as_of)}
    off12, prv12 = change_12(off), change_12(prv)
    for m, (v, a) in off12.items():
        emit("calc.tic_official_12m", month_end(m), round(v, 2), a)
    for m, (v, a) in prv12.items():
        emit("calc.tic_private_12m", month_end(m), round(v, 2), a)
    for m, (v, a) in ns12.items():
        if m in off12 and m in prv12:
            emit("calc.priv_residual_12m", month_end(m),
                 round(v - off12[m][0] - prv12[m][0], 2),
                 latest_avail(a, off12[m][1], prv12[m][1]))
    share_o, share_c, share_t = {}, {}, {}
    for m, (o, a) in off.items():
        if m in prv and (o + prv[m][0]) > 0:
            share_o[m] = (100.0 * o / (o + prv[m][0]), latest_avail(a, prv[m][1]))
            emit("calc.tic_official_share", month_end(m), round(share_o[m][0], 4),
                 share_o[m][1])
    by_c = {c: {month(d): (v, a) for d, v, a in
                series(db, "tic.holdings_by_country", as_of, c)}
            for c in instruments(db, "tic.holdings_by_country")}
    tot = {month(d): (v, a) for d, v, a in series(db, "tic.holdings_total", as_of)}
    for m, (t, a) in tot.items():
        cs = [by_c[c][m] for c in CUSTODIAL if c in by_c and m in by_c[c]]
        if t > 0 and len(cs) == len(CUSTODIAL):
            share_c[m] = (100.0 * sum(x[0] for x in cs) / t,
                          latest_avail(a, *(x[1] for x in cs)))
            emit("calc.tic_custodial_share", month_end(m), round(share_c[m][0], 4),
                 share_c[m][1])
    fl = {k: {month(d): (v, a) for d, v, a in series(db, k, as_of)}
          for k in ("tic.flow_private_treasuries", "tic.flow_official_treasuries",
                    "tic.flow_net_domestic")}
    tr12 = rolling_12({m: (fl["tic.flow_private_treasuries"][m][0]
                           + fl["tic.flow_official_treasuries"][m][0],
                           latest_avail(fl["tic.flow_private_treasuries"][m][1],
                                        fl["tic.flow_official_treasuries"][m][1]))
                       for m in fl["tic.flow_private_treasuries"]
                       if m in fl["tic.flow_official_treasuries"]})
    lt12 = rolling_12(fl["tic.flow_net_domestic"])
    for m, (v, a) in tr12.items():
        if m in lt12 and lt12[m][0]:
            share_t[m] = (100.0 * v / lt12[m][0], latest_avail(a, lt12[m][1]))
            emit("calc.foreign_ust_share_lt", month_end(m), round(share_t[m][0], 4),
                 share_t[m][1])
    for m in sorted(share_t):
        p = month_add(m, -12)
        if all(p in d and m in d for d in (share_t, share_c, share_o)):
            on = int(share_t[m][0] < share_t[p][0] and share_c[m][0] > share_c[p][0]
                     and share_o[m][0] < share_o[p][0])
            emit("calc.abs_fragility", month_end(m), on,
                 latest_avail(share_t[m][1], share_c[m][1], share_o[m][1]))
    # Auctions
    btc = {i: series(db, "auction.bid_to_cover", as_of, i)
           for i in instruments(db, "auction.bid_to_cover")}
    dlr = {i: series(db, "auction.dealer_share", as_of, i)
           for i in instruments(db, "auction.dealer_share")}
    for d, inst, flag, _trace, a in abs_stress(btc, dlr):
        emit("calc.abs_stress", d, flag, a, inst)
    # Credit, breakevens, producers
    aa = {d: (v, a) for d, v, a in series(db, "fred.aa_oas", as_of)}
    for d, v, a in series(db, "fred.bbb_oas", as_of):
        if d in aa:
            emit("calc.aa_bbb_oas_diff", d, round(100.0 * (v - aa[d][0]), 4),
                 latest_avail(a, aa[d][1]))
    be = series(db, "fred.breakeven_5y5y", as_of)
    cie = series(db, "fedboard.cie", as_of)
    umich = series(db, "umich.expect_5_10y", as_of)
    start = first_day or (be[0][0] if be else None)
    for d, v, a in be:
        if start and d >= start:
            emit("calc.be5y5y_range_pos", d, range_pos(be, d), a)
            on, _ = deanchor_on(be, cie, umich, d)
            emit("calc.deanchor", d, on, a)
    sp = {d: (v, a) for d, v, a in series(db, SPOT, as_of)}
    for d, v, a in series(db, PRODUCERS, as_of):
        if d in sp and sp[d][0] > 0:
            emit("calc.producers_spot_ratio", d, round(v / sp[d][0], 6),
                 latest_avail(a, sp[d][1]))
    # The fed-market gap, on each stored futures day.
    prices_by_day: dict[str, dict[str, tuple]] = {}
    for inst in instruments(db, "fedfunds.futures_price"):
        for d, v, a in series(db, "fedfunds.futures_price", as_of, inst):
            prices_by_day.setdefault(d, {})[inst] = (v, a)
    dots = series(db, "fred.sep_median_ff", as_of)
    for d in sorted(prices_by_day):
        imp = implied_12m({k: v for k, (v, _) in prices_by_day[d].items()}, d)
        dot = sep_dot([x for x in dots if x[2] <= f"{d}T23:59:59"], d)
        if imp and dot:
            gap = round(100.0 * (imp[1] - dot[1]), 2)
            a = latest_avail(prices_by_day[d][imp[0]][1],
                             next(x[2] for x in dots if x[0][:4] == dot[0]))
            emit("calc.fed_mkt_gap_12m", d, gap, a)
            emit("calc.cred_stress", d, int(abs(gap) > GAP_BP), a)
    # The AI capex loop (EDGAR)
    from .gtm_equities import frame_year                        # noqa: PLC0415
    by: dict[str, dict[int, dict]] = {"ocf": {}, "capex": {}, "debt": {}, "cash": {}}
    for f, key in (("ocf", "edgar.xbrl_operating_cash_flow"), ("capex", "edgar.xbrl_capex"),
                   ("debt", "edgar.xbrl_long_term_debt"), ("cash", "edgar.xbrl_cash")):
        for tk in HYPERSCALERS:
            for d, v, a in series(db, key, as_of, tk):
                y = frame_year(d) if f in ("ocf", "capex") else int(d[:4])
                by[f].setdefault(y, {})[tk] = (v, a)
    for y in sorted(by["ocf"]):
        o, c = by["ocf"][y], by["capex"].get(y, {})
        if len(o) == len(c) == len(HYPERSCALERS):
            cap = sum(abs(v) for v, _ in c.values())
            if cap:
                emit("calc.self_fund_ratio", f"{y}-12-31",
                     round(sum(v for v, _ in o.values()) / cap, 4),
                     latest_avail(*(a for _, a in [*o.values(), *c.values()])))
    nd = {}
    for y in by["debt"]:
        dd, cc = by["debt"][y], by["cash"].get(y, {})
        if len(dd) == len(cc) == len(HYPERSCALERS):
            nd[y] = (sum(v for v, _ in dd.values()) - sum(v for v, _ in cc.values()),
                     latest_avail(*(a for _, a in [*dd.values(), *cc.values()])))
    for y, (v, a) in nd.items():
        if y - 1 in nd:
            emit("calc.hs_netdebt_12m", f"{y}-12-31", round(v - nd[y - 1][0], 2),
                 latest_avail(a, nd[y - 1][1]))
    inv = {d: (v, a) for d, v, a in series(db, "edgar.xbrl_mu_inventory", as_of, "MU")}
    for d, v, a in series(db, "edgar.xbrl_mu_cogs_q", as_of, "MU"):
        if d in inv and v > 0:
            emit("calc.mu_inv_days", d, round(inv[d][0] / v * 91.0, 2),
                 latest_avail(a, inv[d][1]))
    # Gold
    g = {month(d): (v, a) for d, v, a in
         series(db, "imf.ifs.gold_net_purchases_oz.total", as_of)}
    for m, (v, a) in rolling_12(g).items():
        emit("calc.cb_gold_12m", month_end(m), round(v / TONNE_OZ, 2), a)
    # The prediction-market disagreement: the cutoff day only (the venues' history
    # is the store's few weeks; nothing is back-filled).
    if cutoff_day:
        v = pm_disagree(db, as_of, cutoff_day)
        if v is not None:
            emit("calc.pm_disagree_fed", cutoff_day, v[0], v[1])
    return rows


def pm_disagree(db, as_of: Optional[str], day: str) -> Optional[tuple[float, str]]:
    """The venue's normalised probability less the futures-implied one on the next
    meeting, the side with the larger gap, in points; None when either leg is
    not stored."""
    try:
        from . import fed_funds, prediction_markets as pm               # noqa: PLC0415
        path = fed_funds.path_as_of(as_of, store=db)
        blk = pm.block(day, as_of, fed_path=path, store=db)
    except Exception:                                           # noqa: BLE001
        log.info("pm_disagree: a leg is unreadable", exc_info=True)
        return None
    meetings = (path or {}).get("meetings") or []
    if not meetings:
        return None
    nxt = meetings[0]
    implied = {"hike": 0.0, "cut": 0.0}
    if nxt["direction"] in implied:
        implied[nxt["direction"]] = nxt["move_probability_25bp"]
    best = None
    for dday, by_venue in (blk.get("fomc_odds") or {}).items():
        if not pm._near(dday, nxt["meeting"]):                   # noqa: SLF001
            continue
        for v in by_venue.values():
            tot = v["hike"] + v["hold"] + v["cut"]
            is_book = v["hold"] > 0 and (v["hike"] > 0 or v["cut"] > 0)
            for side in ("hike", "cut"):
                p = v[side] / tot if is_book and tot > 0 else v[side]
                gap = round(100.0 * (p - implied[side]), 2)
                if best is None or abs(gap) > abs(best):
                    best = gap
    if best is None:
        return None
    from . import session                                        # noqa: PLC0415
    return best, observations.canonical_instant(as_of or session.utc_iso(
        timespec="microseconds"))


def compute(as_of: Optional[str] = None, first_day: Optional[str] = None,
            store: Optional[observations.ObservationStore] = None,
            dry_run: bool = False) -> dict:
    own = store is None
    db = store or observations.ObservationStore()
    try:
        from . import session                                    # noqa: PLC0415
        day = (as_of or session.utc_iso())[:10]
        rows = compute_rows(db, as_of, first_day, cutoff_day=day)
        written = 0 if dry_run else db.write_many(observations.drop_unchanged(db, rows))
        by_key: dict[str, int] = {}
        for r in rows:
            by_key[r["registry_key"]] = by_key.get(r["registry_key"], 0) + 1
        return {"computed": len(rows), "written": written, "by_key": by_key}
    finally:
        if own:
            db.close()


def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.absorption")
    ap.add_argument("cmd", choices=["compute", "show"])
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--from", dest="first", default=None)
    ap.add_argument("--db", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    with observations.ObservationStore(a.db) as st:
        if a.cmd == "compute":
            r = compute(a.as_of, a.first, st, a.dry_run)
            print(f"{r['computed']} rows computed, {r['written']} written")
            for k in sorted(r["by_key"]):
                print(f"  {k:32} {r['by_key'][k]:>6}")
        else:
            from daily_cascade import absorption_block            # noqa: PLC0415
            for ln in absorption_block.lines(st, a.as_of):
                print(ln)
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
