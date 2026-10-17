"""
The crypto data layer's derived series (the order's section 3: S-1's share by
chain and S-3; CD-1 and CD-2, Batch 4 Tranche A part 1; crypto-tranche-a-1, 17 Oct
2026). A writer that READS THE STORE and fetches nothing, placed on
feeds.EXTERNAL_WRITERS after hl and fut so it reads what they just wrote (the
em_lenses pattern). Config: config/crypto_sources.yaml `s3`.

    python -m altdata.sources.crypto_derived     # compute and write

S-1 (with calc.stable_impulse_30d/_90d, which the crypto basket already writes):
    calc.stable_share      a chain's share of total stablecoin supply, %;
                           instrument = Ethereum, Tron, Solana or Base
                           (llama.stable_by_chain over llama.stable_total, the
                           same day); full history, from the stored series

S-3, per coin (instrument BTC or ETH):
    calc.funding_agg       open-interest-weighted funding across the venues,
                           annualised %: sum(f_v x OI_v) / sum(OI_v) over the
                           venues carrying both on the day, at least `min_venues`
                           (two: the order rejects a single-venue reading)
    calc.oi_usd            total open interest in USD across EVERY enabled venue
                           (a day missing one is not written, so the total never
                           shrinks because a venue was down); instrument NULL is
                           BTC + ETH
    calc.oi_mcap           calc.oi_usd over the coin's market cap
                           (llama.mcap_btc / _eth, the coin service, on the day or
                           within the three before), %
    calc.leverage_z        z-score of calc.funding_agg on the trailing 90 days
                           (the order's name; part 1 called it funding_agg_z)
    calc.oi_mcap_z         z-score of calc.oi_mcap on the trailing 90 days
                           (each needs 60 of the 90)

PART 2 (crypto-tranche-a-2, 17 Oct 2026):

S-2, per coin (instrument btc or eth), from farside.<coin>_total:
    calc.etf_streak        consecutive same-sign sessions to the day, signed
                           (+3: three inflow sessions; a zero session is 0)
    calc.etf_5d_pct        the five-session sum's percentile against every five-
                           session sum in the stored history to that day (from
                           Jan 2024), with at least 20 of them
S-4, per coin (instrument BTC or ETH), from deribit.dvol_<coin>:
    calc.dvol_pct_5y       the day's DVOL percentile over the five years before it
    calc.dvol_pct_full     ... over the full history (from Mar 2021); 60 days needed
    calc.dvol_minus_rv30   DVOL less 30-day realised volatility, points: realised
                           from the STORED daily closes (yfinance.mkt_btc_usd /
                           _eth_usd), 30 log returns annualised over 365 days --
                           never a second price series
S-5, per network and measure (instrument "<network>:new_pools" or
"<network>:trending_vol"), from GeckoTerminal's own rows only (a DexScreener
fallback row is sampled, never scored):
    calc.froth_z           z-score on a 20-day window, once 90 days of
                           GeckoTerminal store exist

ITEM 49 (digital-49-51b, 17 Oct 2026), from altdata/sources/treasury.py:
    calc.mnav                    MSTR's market cap over the value of its BTC:
                                 spot x shares / (BTC held x BTC close), the order's
                                 definition (basic, not enterprise value); daily,
                                 for each session with a captured MSTR spot, the
                                 share count and holdings as of that day, the BTC
                                 close on the day or within the three before.
                                 Item 49's one flag reads it at render (at or below
                                 1.0; the watch line 1.2); nothing else is derived
    calc.treasury_net_purchases  the month's net BTC bought by the tracked
                                 treasury companies: holdings at the month's end
                                 less holdings at the prior month's end, over the
                                 companies present at both (a snapshot within five
                                 days of each end); complete months only, so the
                                 first is November 2026

THE FLAGS, computed and stored, NEVER RENDERED (no block reads a calc.flag_* key;
tools/validate_crypto_sources.py holds that), gate status "not passed":
    calc.flag_etf_extreme       S-2: the 5-day sum's percentile <= 5 or >= 95
    calc.flag_leverage_crowded  S-3: leverage_z > +2 with OI/mcap at its 90-day high
    calc.flag_froth             S-5: both of a network's measures at z >= +2
    (1 the flag holds, 0 it does not; a day without its inputs is not written)

THE AGGREGATE STARTS WITH THE FIRST PULL. The venues' funding is backfilled, but
only OKX serves OI history (Hyperliquid and Deribit do not), and an OI weight
from another day would not be point in time; so calc.funding_agg and calc.oi_usd
begin when two (and, for the total, all) venues carry OI on the same day, and the
z-scores mature after 60 days. The per-venue funding history is stored meanwhile.

POINT IN TIME: every input is read as of the run (the latest vintage of each
day), and every row is written with the run's instant as available_at.
"""

from __future__ import annotations

import datetime as dt
import logging
import math
from typing import Any, Optional

from . import _crypto as C
from . import _publication as pub

log = logging.getLogger(__name__)

SOURCE = "derived_state"
KEYS = ["calc.stable_share", "calc.funding_agg", "calc.oi_usd", "calc.oi_mcap",
        "calc.leverage_z", "calc.oi_mcap_z", "calc.etf_streak", "calc.etf_5d_pct",
        "calc.dvol_pct_5y", "calc.dvol_pct_full", "calc.dvol_minus_rv30",
        "calc.froth_z", "calc.flag_etf_extreme", "calc.flag_leverage_crowded",
        "calc.flag_froth", "calc.mnav", "calc.treasury_net_purchases"]
FLAG_KEYS = ["calc.flag_etf_extreme", "calc.flag_leverage_crowded", "calc.flag_froth"]
GATE_STATUS = "not passed"
STABLE_CHAINS = ("Ethereum", "Tron", "Solana", "Base")
# venue -> (funding key, OI key); the enabled set comes from config.
VENUE_KEYS = {"hyperliquid": ("hl.funding", "hl.oi"),
              "okx": ("fut.funding_okx", "fut.oi_okx"),
              "deribit": ("fut.funding_deribit", "fut.oi_deribit"),
              "bybit": ("fut.funding_bybit", "fut.oi_bybit")}
MCAP_KEYS = {"BTC": "llama.mcap_btc", "ETH": "llama.mcap_eth"}


def _series(st: Any, key: str, as_of: Optional[str], instrument: Optional[str] = None
            ) -> dict[str, float]:
    out = {}
    for r in st.as_of(key, as_of, instrument):
        if r.get("value_num") is not None:
            out[str(r["observed_at"])[:10]] = float(r["value_num"])
    return out


# ---------------------------------------------------------------------------
# Pure arithmetic -- what the gate checks by hand
# ---------------------------------------------------------------------------
def stable_share(total: dict[str, float], chain: dict[str, float]) -> dict[str, float]:
    return {d: 100.0 * v / total[d] for d, v in chain.items() if total.get(d)}


def funding_agg(by_venue: dict[str, tuple[Optional[float], Optional[float]]],
                min_venues: int = 2) -> Optional[float]:
    """{venue: (annualised funding %, OI USD)} -> the OI-weighted funding, or None
    with fewer than `min_venues` carrying both."""
    pairs = [(f, oi) for f, oi in by_venue.values()
             if f is not None and oi is not None and oi > 0]
    if len(pairs) < min_venues:
        return None
    return sum(f * oi for f, oi in pairs) / sum(oi for _, oi in pairs)


def zscores(series: dict[str, float], window: int = 90, min_obs: int = 60
            ) -> dict[str, float]:
    """Each day's z against the trailing `window` calendar days (the day
    included), with at least `min_obs` observations; population s.d. > 0."""
    days = sorted(series)
    out = {}
    for d in days:
        lo = (dt.date.fromisoformat(d) - dt.timedelta(days=window - 1)).isoformat()
        xs = [series[x] for x in days if lo <= x <= d]
        if len(xs) < min_obs:
            continue
        mu = sum(xs) / len(xs)
        sd = math.sqrt(sum((x - mu) ** 2 for x in xs) / len(xs))
        if sd > 0:
            out[d] = (series[d] - mu) / sd
    return out


def _near(m: dict[str, float], day: str, back: int = 3) -> Optional[float]:
    d = dt.date.fromisoformat(day)
    for k in range(back + 1):
        v = m.get((d - dt.timedelta(days=k)).isoformat())
        if v is not None:
            return v
    return None


# ---------------------------------------------------------------------------
# From the store
# ---------------------------------------------------------------------------
def compute(st: Any, as_of: Optional[str] = None, cfg: Optional[dict] = None,
            now: Optional[str] = None) -> list[dict]:
    cfg = cfg or C.config()
    now = now or C.now_iso()
    s3 = cfg.get("s3") or {}
    min_v = int(s3.get("min_venues") or 2)
    win, min_obs = int(s3.get("z_window") or 90), int(s3.get("z_min_obs") or 60)
    venues = [v for v, spec in (cfg.get("venues") or {}).items()
              if spec.get("enabled") and v in VENUE_KEYS]
    rows: list[dict] = []
    # S-1: the share by chain.
    total = _series(st, "llama.stable_total", as_of)
    for ch in STABLE_CHAINS:
        for d, v in sorted(stable_share(total, _series(st, "llama.stable_by_chain",
                                                       as_of, ch)).items()):
            rows.append(C.row("calc.stable_share", d, round(v, 4), now, SOURCE, ch))
    # S-3, per coin.
    oi_by_coin: dict[str, dict[str, float]] = {}
    for coin in cfg.get("coins") or ["BTC", "ETH"]:
        fund = {v: _series(st, VENUE_KEYS[v][0], as_of, coin) for v in venues}
        oi = {v: _series(st, VENUE_KEYS[v][1], as_of, coin) for v in venues}
        days = sorted(set().union(*[set(x) for x in fund.values()],
                                  *[set(x) for x in oi.values()]))
        agg, tot = {}, {}
        for d in days:
            a = funding_agg({v: (fund[v].get(d), oi[v].get(d)) for v in venues}, min_v)
            if a is not None:
                agg[d] = a
            if venues and all(oi[v].get(d) is not None for v in venues):
                tot[d] = sum(oi[v][d] for v in venues)
        mcap = _series(st, MCAP_KEYS.get(coin, ""), as_of) if coin in MCAP_KEYS else {}
        ratio = {d: 100.0 * v / m for d, v in tot.items()
                 if (m := _near(mcap, d)) not in (None, 0)}
        oi_by_coin[coin] = tot
        rows += [C.row("calc.funding_agg", d, round(v, 6), now, SOURCE, coin)
                 for d, v in agg.items()]
        rows += [C.row("calc.oi_usd", d, round(v, 2), now, SOURCE, coin)
                 for d, v in tot.items()]
        rows += [C.row("calc.oi_mcap", d, round(v, 6), now, SOURCE, coin)
                 for d, v in ratio.items()]
        lz = zscores(agg, win, min_obs)
        rows += [C.row("calc.leverage_z", d, round(v, 4), now, SOURCE, coin)
                 for d, v in lz.items()]
        rows += [C.row("calc.oi_mcap_z", d, round(v, 4), now, SOURCE, coin)
                 for d, v in zscores(ratio, win, min_obs).items()]
        # S-3's flag: stored, never rendered.
        for d, z in lz.items():
            if d in ratio:
                hi = at_window_high(ratio, d, win)
                rows.append(C.row("calc.flag_leverage_crowded", d,
                                  1.0 if (z > 2.0 and hi) else 0.0, now, SOURCE, coin))
    if len(oi_by_coin) >= 2:
        both = set.intersection(*[set(v) for v in oi_by_coin.values()])
        rows += [C.row("calc.oi_usd", d, round(sum(v[d] for v in oi_by_coin.values()), 2),
                       now, SOURCE) for d in sorted(both)]
    rows += s2_rows(st, as_of, cfg, now)
    rows += s4_rows(st, as_of, cfg, now)
    rows += s5_rows(st, as_of, cfg, now)
    rows += mnav_rows(st, as_of, now)
    rows += net_purchase_rows(st, as_of, now)
    return rows


# ---------------------------------------------------------------------------
# Part 2: S-2, S-4, S-5 and their flags
# ---------------------------------------------------------------------------
def at_window_high(series: dict[str, float], day: str, window: int = 90) -> bool:
    lo = (dt.date.fromisoformat(day) - dt.timedelta(days=window - 1)).isoformat()
    xs = [v for d, v in series.items() if lo <= d <= day]
    return bool(xs) and series[day] >= max(xs)


def streaks(series: dict[str, float]) -> dict[str, int]:
    """Signed consecutive same-sign sessions to each day; a zero day is 0."""
    out, run, sign = {}, 0, 0
    for d in sorted(series):
        v = series[d]
        s = (v > 0) - (v < 0)
        run = run + 1 if (s == sign and s != 0) else (1 if s != 0 else 0)
        sign = s
        out[d] = run * s
    return out


def rank_pct(history: list[float], x: float) -> float:
    """The share of `history` (x included) at or below x, in percent."""
    return 100.0 * sum(1 for h in history if h <= x) / len(history)


def sums(series: dict[str, float], n: int = 5) -> dict[str, float]:
    days = sorted(series)
    return {days[i]: sum(series[d] for d in days[i - n + 1:i + 1])
            for i in range(n - 1, len(days))}


def s2_rows(st: Any, as_of: Optional[str], cfg: dict, now: str) -> list[dict]:
    c = cfg.get("s2") or {}
    n, lo, hi = int(c.get("window") or 5), float(c.get("flag_low") or 5), \
        float(c.get("flag_high") or 95)
    rows = []
    for coin in ("btc", "eth"):
        tot = _series(st, f"farside.{coin}_total", as_of)
        if not tot:
            continue
        for d, v in streaks(tot).items():
            rows.append(C.row("calc.etf_streak", d, float(v), now, SOURCE, coin))
        s5 = sums(tot, n)
        days = sorted(s5)
        for i, d in enumerate(days):
            hist = [s5[x] for x in days[:i + 1]]
            if len(hist) < 20:
                continue
            p = rank_pct(hist, s5[d])
            rows.append(C.row("calc.etf_5d_pct", d, round(p, 4), now, SOURCE, coin))
            rows.append(C.row("calc.flag_etf_extreme", d,
                              1.0 if (p <= lo or p >= hi) else 0.0, now, SOURCE, coin))
    return rows


def realised_vol(closes: dict[str, float], day: str, n: int = 30) -> Optional[float]:
    days = [d for d in sorted(closes) if d <= day][-(n + 1):]
    if len(days) < n + 1:
        return None
    r = [math.log(closes[b] / closes[a]) for a, b in zip(days, days[1:])
         if closes[a] > 0 and closes[b] > 0]
    if len(r) < n:
        return None
    mu = sum(r) / len(r)
    return 100.0 * math.sqrt(365.0) * math.sqrt(sum((x - mu) ** 2 for x in r) / (len(r) - 1))


def s4_rows(st: Any, as_of: Optional[str], cfg: dict, now: str) -> list[dict]:
    c = cfg.get("s4") or {}
    days5 = int(c.get("pct_5y_days") or 1826)
    rv_n = int(c.get("rv_days") or 30)
    rows = []
    for coin, pkey in (c.get("price_keys") or {"BTC": "yfinance.mkt_btc_usd",
                                               "ETH": "yfinance.mkt_eth_usd"}).items():
        dv = _series(st, f"deribit.dvol_{coin.lower()}", as_of)
        if not dv:
            continue
        closes = _series(st, pkey, as_of)
        days = sorted(dv)
        for i, d in enumerate(days):
            hist = [dv[x] for x in days[:i + 1]]
            if len(hist) >= 60:
                rows.append(C.row("calc.dvol_pct_full", d, round(rank_pct(hist, dv[d]), 4),
                                  now, SOURCE, coin))
                lo = (dt.date.fromisoformat(d) - dt.timedelta(days=days5)).isoformat()
                h5 = [dv[x] for x in days[:i + 1] if x > lo]
                rows.append(C.row("calc.dvol_pct_5y", d, round(rank_pct(h5, dv[d]), 4),
                                  now, SOURCE, coin))
            rv = realised_vol(closes, d, rv_n)
            if rv is not None:
                rows.append(C.row("calc.dvol_minus_rv30", d, round(dv[d] - rv, 4), now,
                                  SOURCE, coin))
    return rows


def mnav(spot: float, shares: float, holdings: float, btc: float) -> Optional[float]:
    """The order's mNAV: market cap over the value of the BTC held."""
    if not (spot and shares and holdings and btc):
        return None
    return spot * shares / (holdings * btc)


def _asof_value(series: dict[str, float], day: str, back: Optional[int] = None
                ) -> Optional[float]:
    ks = [d for d in series if d <= day and (back is None or d >= (
        dt.date.fromisoformat(day) - dt.timedelta(days=back)).isoformat())]
    return series[max(ks)] if ks else None


def mnav_rows(st: Any, as_of: Optional[str], now: str) -> list[dict]:
    spot = _series(st, "treasury.mstr_spot", as_of, "MSTR")
    shares = _series(st, "treasury.mstr_shares", as_of)
    hold = _series(st, "treasury.btc_holdings", as_of, "MSTR")
    btc = _series(st, "yfinance.mkt_btc_usd", as_of)
    rows = []
    for d, sp in sorted(spot.items()):
        v = mnav(sp, _asof_value(shares, d), _asof_value(hold, d), _asof_value(btc, d, 3))
        if v is not None:
            rows.append(C.row("calc.mnav", d, round(v, 6), now, SOURCE, "MSTR"))
    return rows


def month_end(day: str) -> str:
    d = dt.date.fromisoformat(day)
    nxt = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    return (nxt - dt.timedelta(days=1)).isoformat()


def _every_instrument(st: Any, key: str, as_of: Optional[str]) -> list[dict]:
    """Every instrument's rows as of the cutoff. The store's as_of() reads one
    instrument (None is the NULL one), so the holdings -- one row per ticker --
    are read instrument by instrument."""
    insts = [r[0] for r in st.conn.execute(
        "SELECT DISTINCT instrument FROM observations WHERE registry_key = ?", (key,))]
    out: list[dict] = []
    for inst in insts:
        out += [dict(r, instrument=inst) for r in st.as_of(key, as_of, inst)]
    return out


def holdings_at(st: Any, as_of: Optional[str], end: str, window: int = 5
                ) -> dict[str, float]:
    """Each ticker's newest snapshot within `window` days before `end`."""
    lo = (dt.date.fromisoformat(end) - dt.timedelta(days=window)).isoformat()
    out: dict[str, tuple[str, float]] = {}
    for r in _every_instrument(st, "treasury.btc_holdings", as_of):
        d = str(r["observed_at"])[:10]
        if r.get("value_num") is None or not (lo <= d <= end):
            continue
        t = r.get("instrument")
        if t not in out or d > out[t][0]:
            out[t] = (d, float(r["value_num"]))
    return {t: v for t, (_, v) in out.items()}


def net_purchase_rows(st: Any, as_of: Optional[str], now: str) -> list[dict]:
    days = sorted({str(r["observed_at"])[:10]
                   for r in _every_instrument(st, "treasury.btc_holdings", as_of)})
    if not days:
        return []
    today = (as_of or now)[:10]
    ends = sorted({month_end(d) for d in days})
    rows = []
    for e in ends:
        if e >= today:
            continue
        prev = month_end((dt.date.fromisoformat(e).replace(day=1)
                          - dt.timedelta(days=1)).isoformat())
        a, b = holdings_at(st, as_of, prev), holdings_at(st, as_of, e)
        both = set(a) & set(b)
        if both:
            rows.append(C.row("calc.treasury_net_purchases", e,
                              round(sum(b[t] - a[t] for t in both), 4), now, SOURCE))
    return rows


def _gt_series(st: Any, key: str, as_of: Optional[str], inst: str) -> dict[str, float]:
    """GeckoTerminal's own rows only: a fallback row (source dexscreener:...) is
    sampled, never scored."""
    out = {}
    for r in st.as_of(key, as_of, inst):
        if r.get("value_num") is not None and str(r.get("source") or "") == "geckoterminal":
            out[str(r["observed_at"])[:10]] = float(r["value_num"])
    return out


def s5_rows(st: Any, as_of: Optional[str], cfg: dict, now: str) -> list[dict]:
    c = cfg.get("s5") or {}
    win, need, fz = int(c.get("z_window") or 20), int(c.get("min_store_days") or 90), \
        float(c.get("flag_z") or 2.0)
    rows = []
    for net in (cfg.get("gt") or {}).get("networks") or ["solana", "base"]:
        zs = {}
        for meas, key in (("new_pools", "gt.new_pools_24h"),
                          ("trending_vol", "gt.trending_vol_24h")):
            s = _gt_series(st, key, as_of, net)
            if not s:
                continue
            first = min(s)
            ok = {d: v for d, v in s.items()
                  if (dt.date.fromisoformat(d) - dt.date.fromisoformat(first)).days >= need - 1}
            z = {d: v for d, v in zscores(s, win, max(10, win // 2)).items() if d in ok}
            zs[meas] = z
            rows += [C.row("calc.froth_z", d, round(v, 4), now, SOURCE, f"{net}:{meas}")
                     for d, v in z.items()]
        if len(zs) == 2:
            for d in sorted(set(zs["new_pools"]) & set(zs["trending_vol"])):
                rows.append(C.row("calc.flag_froth", d,
                                  1.0 if (zs["new_pools"][d] >= fz and
                                          zs["trending_vol"][d] >= fz) else 0.0,
                                  now, SOURCE, net))
    return rows


def pull(run_id: Optional[str] = None, db=None, as_of: Optional[str] = None) -> dict:
    from .. import observations as obs  # noqa: PLC0415

    def produce() -> list[dict]:
        own = db is None
        st = db or obs.ObservationStore()
        try:
            return compute(st, as_of)
        finally:
            if own:
                st.close()
    # Nothing stored to derive from is STALE (the contract's "zero rows"): the
    # freshness roster then says the derived series are not current, which is
    # true until the venues' first pull lands.
    return pub.run(SOURCE, KEYS, produce, run_id=run_id, db=db)


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(pull(), indent=2, sort_keys=True, default=str))
