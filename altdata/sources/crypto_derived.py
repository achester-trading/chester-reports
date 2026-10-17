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
    calc.funding_agg_z     z-score of calc.funding_agg on the trailing 90 days
    calc.oi_mcap_z         z-score of calc.oi_mcap on the trailing 90 days
                           (each needs 60 of the 90; the S-3 flag -- funding z > +2
                           with OI/mcap at a 90-day high -- waits for its gate)

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
        "calc.funding_agg_z", "calc.oi_mcap_z"]
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
        rows += [C.row("calc.funding_agg_z", d, round(v, 4), now, SOURCE, coin)
                 for d, v in zscores(agg, win, min_obs).items()]
        rows += [C.row("calc.oi_mcap_z", d, round(v, 4), now, SOURCE, coin)
                 for d, v in zscores(ratio, win, min_obs).items()]
    if len(oi_by_coin) >= 2:
        both = set.intersection(*[set(v) for v in oi_by_coin.values()])
        rows += [C.row("calc.oi_usd", d, round(sum(v[d] for v in oi_by_coin.values()), 2),
                       now, SOURCE) for d in sorted(both)]
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
