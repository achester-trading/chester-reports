"""
Per-strike dealer exposure -- gamma, delta, vanna and charm -- from a raw chain.

Reads the newest chain CSV per symbol written by altdata.sources.options_chain
and produces the exposure profile the logger records nightly. Formerly
gex_compute; tools/gex_compute.py is now a shim that re-exports this module, so
existing callers keep working unchanged.

FOUR GREEKS, ONE PIECE OF EVIDENCE. Every row this module emits carries
`mechanism_group = dealer_chain_derived`, and that tag is load-bearing. GEX,
DEX, VEX and CHEX are four derivatives of ONE object: the same settled open
interest, the same implied-vol surface, the same signing assumption. They move
together by construction. Per architecture 26.9 -- "four Greeks are not four
votes" -- anything downstream must treat the set as a single confluence
cluster. Counting a gamma reading and a charm reading as two independent
confirmations would be double-counting the same chain.

-----------------------------------------------------------------------------
DEALERS-HAND-V1 SIGN CONVENTIONS, PER GREEK
-----------------------------------------------------------------------------

One assumption drives all four:

    dealer_position(right) = +1 for calls, -1 for puts

Dealers are assumed long calls and short puts. This is the standard street
convention and it is an *assumption*, not an observation: real dealer inventory
is unobservable from public chains, because a call a dealer sold looks
identical to one they bought. Every output carries convention_version and a
caveat field so a later reader cannot mistake a convention for a measurement.
Under the opposite (customer-hand) reading, every sign below inverts.

GEX -- gamma exposure.  Unchanged from the previous version of this file.

    GEX_strike = dealer_position x gamma x OI x 100 x spot

    Stored primary is `shares_per_1pct`: the change in dealer delta, in shares,
    for a 1% move in spot. `dollar_gamma_per_1pct` is derived from it (shares x
    spot) rather than computed independently, so the two cannot drift; raw
    notional (`net_gex`) is kept as the underlying quantity.

    POSITIVE net GEX = dealers are long gamma. They sell into rallies and buy
    dips to stay hedged, which dampens realised vol. Negative = they chase,
    which amplifies it.

DEX -- delta exposure.  The dealer OPTION BOOK's delta, in shares.

    DEX_strike = dealer_position x delta x OI x 100

    POSITIVE DEX = the option book is long delta, so the dealer is SHORT that
    many shares of stock as a hedge. The sign of the hedge is the opposite of
    the sign of DEX, and confusing the two inverts every conclusion, so:

        dex_shares      what the option book is long   (+ = long delta)
        hedge held      -dex_shares of stock
        unwind at expiry  +dex_shares traded           (+ = dealer BUYS back)

    That last line is the expiration-release output. When a contract expires
    its delta goes to zero, the hedge against it is no longer needed, and the
    dealer trades out of it. A large positive DEX rolling off is mechanical
    dealer buying; a large negative DEX rolling off is mechanical selling.
    `unwind_direction` states which, per expiry, so the reader never has to
    re-derive the sign.

    DEX IS ONE-SIGNED UNDER THIS CONVENTION, AND THAT IS NOT A BUG. A long call
    has positive delta; a SHORT put also has positive delta. Both legs of
    dealers-hand-v1 therefore contribute positively and net DEX is positive for
    every symbol, every bucket and every expiry -- 269 of 269 rows on the first
    backfill, with no negatives possible even in principle. So the DIRECTION of
    DEX carries no information at all, and `unwind_direction` will read
    dealer_buys forever. What does carry information is the MAGNITUDE, its
    distribution across expiry dates, and its change from one session to the
    next. Read the release ladder as "how much hedge rolls off, and when",
    never as "which way".

    The direction only becomes a real variable if flow polarity ever arrives to
    replace the assumed +1/-1 with observed dealer sides. That is Alpha-tier
    data this system does not have; the column exists so the ladder does not
    have to change shape on the day it does.

VEX -- vanna exposure.  d(delta)/d(vol), in shares per ONE VOL POINT.

    vanna      = -phi(d1) x d2 / sigma          (identical for calls and puts)
    VEX_strike = dealer_position x vanna x 0.01 x OI x 100

    The 0.01 is the unit choice: raw vanna is per 1.00 of vol (100 vol points),
    which is not a move anything survives. Quoted per vol point, the number is
    the shares of delta the book gains if IV rises one point.

    POSITIVE VEX = a vol rise makes the option book longer delta, so the dealer
    SELLS stock into rising vol. This is the classic vanna feed: vol down ->
    dealers buy, vol up -> dealers sell.

CHEX -- charm exposure.  d(delta)/d(time), in shares per CALENDAR DAY.

    charm      = -phi(d1) x (2rT - d2 sigma sqrt(T)) / (2 T sigma sqrt(T))
    CHEX_strike = dealer_position x (charm / 365) x OI x 100

    With no dividend yield, put delta = call delta - 1, so charm is identical
    for calls and puts -- the constant differentiates away. Same as vanna.

    POSITIVE CHEX = the book gets longer delta simply from time passing, so the
    dealer SELLS stock as the clock runs. This is the drift that shows up on
    quiet Thursday and Friday afternoons with nothing else happening.

TRIGGERS, AND WHY VANNA AND CHARM ARE NOT THE SAME KIND OF NUMBER AS GEX.
GEX is triggered by SPOT: it acts the moment price moves. Vanna needs a change
in IV and charm needs the passage of time. Neither fires on a still tape, so
they are best read as a standing pressure that resolves over hours to days, not
as a level price reacts to.

    Vanna DOES go to zero in 0DTE. vanna = -phi(d1) d2 / sigma, and as T -> 0
    every strike goes to phi(d1) -> 0 (wings) or d2 -> 0 (at the money), so the
    whole 0DTE bucket collapses toward nothing. Expect a near-zero number there
    and treat a large one as a data fault.

    Charm DOES NOT. Charm scales as 1/sqrt(T) and DIVERGES as T -> 0; the 0DTE
    bucket carries the largest per-day charm in the book, not the smallest.
    What is bounded is not the rate but the total: delta has only hours left in
    which to resolve to 0 or 1, so a per-DAY rate on a contract with two hours
    to live is an extrapolation of something that cannot run a full day.

    That divergence is why a SETTLED capture no longer reports 0DTE greeks at
    all -- see the settlement section below. On an INTRADAY capture, where
    those contracts still have hours of life, charm is reported and
    `chex_floored_rows` is the counter to check before believing a large one.

-----------------------------------------------------------------------------
SETTLEMENT SEMANTICS -- WHY A SETTLED PROFILE HAS NO 0DTE GREEKS
-----------------------------------------------------------------------------

At the 16:10 ET capture the day's contracts are expired or minutes from it.
Their gamma is not a forward-looking dealer exposure; it is an artifact of
quoting corpses. A settled profile therefore excludes DTE=0 from every exposure
aggregate -- GEX, DEX, VEX, CHEX, the walls, the flip, the peak strike -- by
declared semantic rule (config.SETTLED_0DTE_RULE), not as a numerical dodge.

The 0DTE bucket is still reported. It carries its OI STRUCTURE, and its four
greeks are replaced by config.SETTLED_0DTE_GREEKS_LABEL. Open interest at
settlement is a fact; gamma at settlement is not. OI constructs -- max pain,
the quality gates -- read every row including 0DTE, because the distortion was
never in the OI, only in gamma via the MIN_T floor.

The rule is conditioned on the CAPTURE, not the calendar. `is_settled_capture`
asks whether the snapshot was taken at or after 16:00 ET. At the 09:45 capture
the same contracts have hours of life and real two-sided markets, and their
gamma is the most meaningful in the book -- so 0DTE greeks are the intraday
cadence's property, and that is where the pin log's 0DTE segmentation will get
real data. Nothing here discards them; it declines to compute them from a
corpse.

What this repaired, measured on 2026-09-04: the peak-GEX pin rate read 7/13
with floored rows in and 0/13 without, and the peak strike moved on 9 of 13
symbols. Every "hit" sat within 16bps of spot and most within 1bp, because
0DTE gamma scales as 1/sqrt(T) and peaks at the money -- so a floored row
planted the peak strike AT the money and the pin test then asked whether the
strike nearest spot is near spot. Floored rows carried 87.0% of AAPL's |GEX|
and 54.1% of NVDA's.

MIN_T IS A GUARD AND MUST NEVER BE LOAD-BEARING. It stops a division by zero;
it does not license a number where none is meaningful. Every bucket reports
`floored_share_of_abs_gex`, and any bucket over
config.MIN_T_LOAD_BEARING_SHARE sets `min_t_load_bearing` -- at that point the
floor is no longer preventing an error, it is manufacturing the answer. The
flag fires on the profile, not in a comment, so a future capture that drifts
back into this cannot do it quietly.

GREEKS SOURCE. yfinance ships no greeks, so all four are computed Black-Scholes
from the chain's own implied vol with r = config.RISK_FREE_RATE:

    d1    = (ln(S/K) + (r + sigma^2/2) T) / (sigma sqrt(T))
    d2    = d1 - sigma sqrt(T)
    gamma = phi(d1) / (S sigma sqrt(T))
    delta = N(d1) for calls, N(d1) - 1 for puts

If a future vendor supplies gamma directly, a `gamma` column in the chain is
used as-is for gamma while the other three are still solved from IV;
`gamma_source` records which path gamma took. No dividend yield is modelled
(q = 0), which is the same simplification the gamma path has always made.

Usage:
    python tools/exposure_compute.py                    # newest snapshot
    python tools/exposure_compute.py --symbols SPY QQQ
    python tools/exposure_compute.py --date 2026-09-04
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from altdata import config   # noqa: E402
from altdata import session  # noqa: E402
import quality_gates    # noqa: E402

log = logging.getLogger(__name__)

# session_date now lives in altdata.session so every module keys sessions the
# same way. Re-exported because callers already import it from here.
session_date = session.session_date


SQRT_2PI = math.sqrt(2.0 * math.pi)
MIN_T = 1.0 / (365.0 * 24.0)     # 1 hour, so 0DTE gamma and charm stay finite
MAX_SANE_IV = 5.0                # 500% vol; above this the quote is garbage

# WHICH IMPLIED VOL PRODUCED A GREEK. The label travels on the profile and on
# every pin-log row, because a greek solved from option prices and one taken
# from the vendor's own IV column are not the same measurement and must never
# be indistinguishable in the store. tools/iv_solver.py tags every row it
# touches with iv_source; anything untagged came from the chain's IV column.
IV_SOURCE_LABELS = {
    "solved_bs_v1": "solved_bs_v1",          # tools/iv_solver.py
    None: "computed_bs_from_yf_iv",          # the chain's own IV column
}
DEFAULT_IV_LABEL = "computed_bs_from_yf_iv"

DAYS_PER_YEAR = 365.0            # charm is per year; the book reads per day
VOL_POINT = 0.01                 # vanna is per 1.00 of vol; the book reads per point
CONTRACT_MULTIPLIER = 100.0      # shares per option contract

# Every row emitted here belongs to one confluence cluster, not four. See the
# module docstring and architecture 26.9.
MECHANISM_GROUP = "dealer_chain_derived"

# PER-FIELD mechanism groups. The profile-level MECHANISM_GROUP above is the
# dominant one and was, until now, the ONLY one stamped -- which quietly told a
# reader that max pain and gamma flip are the same cluster. They are not.
#
# 26.9 requires settled OI, effective OI and flow polarity kept distinct, and
# max pain is an OI construct rather than a gamma one: it is a payout minimum
# over open interest and would be unchanged if every implied vol in the chain
# were wrong. Treating an OI level as confirmation of a gamma level is
# double-counting one chain through two lenses -- the exact failure the tag
# exists to prevent.
#
# tools/check_registry.py asserts this map agrees with metrics_registry.yaml
# field by field, so the two cannot drift apart again.
FIELD_MECHANISM_GROUPS: dict[str, str] = {
    # --- gamma and the levels derived from it ---------------------------
    "net_gex": "dealer_chain_derived",
    "shares_per_1pct": "dealer_chain_derived",
    "dollar_gamma_per_1pct": "dealer_chain_derived",
    "gamma_flip": "dealer_chain_derived",
    "gamma_flip_cum_strikes": "dealer_chain_derived",
    "call_wall": "dealer_chain_derived",
    "put_wall": "dealer_chain_derived",
    "put_wall_otm": "dealer_chain_derived",
    "call_wall_otm": "dealer_chain_derived",
    "put_wall_gamma": "dealer_chain_derived",
    "peak_abs_gex_strike": "dealer_chain_derived",
    "gex": "dealer_chain_derived",
    "call_gex": "dealer_chain_derived",
    "put_gex": "dealer_chain_derived",
    "share_of_total_abs_gex": "dealer_chain_derived",
    # --- delta, vanna, charm: same chain, same cluster -------------------
    "dex_shares": "dealer_chain_derived",
    "dex_notional": "dealer_chain_derived",
    "abs_dex_shares": "dealer_chain_derived",
    "dex": "dealer_chain_derived",
    "share_of_total_abs_dex": "dealer_chain_derived",
    "share_of_abs_dex": "dealer_chain_derived",
    "vex_shares_per_volpt": "dealer_chain_derived",
    "vex_notional_per_volpt": "dealer_chain_derived",
    "vex": "dealer_chain_derived",
    "chex_shares_per_day": "dealer_chain_derived",
    "chex_notional_per_day": "dealer_chain_derived",
    "chex": "dealer_chain_derived",
    # --- OI constructs: a DIFFERENT mechanism ---------------------------
    # Unchanged by any implied vol in the chain. That is the test for which
    # side of this line a field belongs on.
    "max_pain": "dealer_chain_oi",
    "put_wall_oi": "dealer_chain_oi",
    "oi_total": "dealer_chain_oi",
    "oi_calls": "dealer_chain_oi",
    "oi_puts": "dealer_chain_oi",
    "oi_put_call_ratio": "dealer_chain_oi",
    "oi_strikes": "dealer_chain_oi",
    "spot": "dealer_chain_oi",
    # --- quality, which is evidence ABOUT the chain, not from it --------
    "floored_share_of_abs_gex": "chain_quality",
    "data_quality": "chain_quality",
    "liquidity_floor": "chain_quality",
    "iv_dispersion": "chain_quality",
    "oi_concentration": "chain_quality",
    "oi_weighted_dte": "chain_quality",
}


def iv_label(row: dict) -> str:
    """The greeks_source label for one row, from its IV provenance."""
    return IV_SOURCE_LABELS.get(row.get("iv_source"), DEFAULT_IV_LABEL)


def _iv_counter(row: dict) -> str:
    return ("greeks_from_solver" if iv_label(row) == "solved_bs_v1"
            else "greeks_from_yf_iv")


def greeks_source_for(quality: dict) -> str:
    """One label for the profile, or an explicit mix.

    A mixed profile is reported AS a mix rather than as whichever source
    happened to dominate. Two IV paths inside one number is a fact a reader
    needs, and "mostly the vendor's" is not a provenance.
    """
    yf = quality.get("greeks_from_yf_iv", 0)
    solved = quality.get("greeks_from_solver", 0)
    if solved and yf:
        return (f"mixed:computed_bs_from_yf_iv+solved_bs_v1"
                f"({solved}/{yf + solved} solved)")
    if solved:
        return "solved_bs_v1"
    return DEFAULT_IV_LABEL


def is_settled_capture(fetched_at=None) -> bool:
    """Was this snapshot taken at or after the close, in ET?

    The 0DTE exclusion is a property of the CAPTURE, not of the calendar date:
    the same contracts that are corpses at 16:10 are the liveliest thing in the
    book at 09:45. Anything with no timestamp is treated as settled, because
    every capture this pipeline has taken so far is an EOD one and the
    conservative reading is the one that refuses to compute.
    """
    if fetched_at is None:
        return True
    et = session.to_eastern(fetched_at)
    return (et.hour, et.minute) >= (config.SETTLEMENT_ET_HOUR,
                                    config.SETTLEMENT_ET_MINUTE)


def dealer_position(right: str) -> float:
    """dealers-hand-v1: long calls, short puts. The one assumption behind all
    four Greeks -- kept as a function so no call site can quietly disagree."""
    return 1.0 if right == "C" else -1.0


# ---------------------------------------------------------------------------
# Black-Scholes gamma
# ---------------------------------------------------------------------------

def norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _d1_d2(spot: float, strike: float, iv: float, t: float,
           r: float) -> Optional[tuple[float, float, float]]:
    """(d1, d2, sigma*sqrt(t)) or None when the inputs cannot produce one.

    Shared by every Greek so they cannot disagree about their own inputs --
    four functions each re-deriving d1 is four chances to typo one of them.
    """
    denom = iv * math.sqrt(t)
    if denom <= 0:
        return None
    try:
        d1 = (math.log(spot / strike) + (r + 0.5 * iv * iv) * t) / denom
    except ValueError:
        return None
    if not math.isfinite(d1):
        return None
    return d1, d1 - denom, denom


def bs_gamma(spot: float, strike: float, iv: float, t_years: float,
             r: float) -> Optional[float]:
    """Black-Scholes gamma. Identical for calls and puts.

    Returns None when inputs cannot produce a meaningful number rather than
    letting a divide-by-zero or a log of a negative propagate into the profile.
    """
    if not (spot and strike and iv) or spot <= 0 or strike <= 0 or iv <= 0:
        return None
    t = max(t_years, MIN_T)
    dd = _d1_d2(spot, strike, iv, t, r)
    if dd is None:
        return None
    d1, _, denom = dd
    g = norm_pdf(d1) / (spot * denom)
    return g if math.isfinite(g) else None


def bs_greeks(spot: float, strike: float, iv: float, t_years: float, r: float,
              right: str) -> Optional[dict]:
    """gamma, delta, vanna and charm for one contract, per share of underlying.

    All four come out of one d1/d2 evaluation so they are guaranteed mutually
    consistent -- that consistency is exactly why they are one mechanism group
    and not four independent signals.

    Units, which differ per Greek and are the easiest thing to get wrong:
        gamma  delta per $1 move in spot
        delta  dimensionless, -1..1
        vanna  delta per 1.00 of vol (NOT per vol point; scaled at the call
               site, so this stays the textbook quantity)
        charm  delta per YEAR (scaled to per-day at the call site, same reason)

    `t_floored` reports whether MIN_T bound the time input, because charm
    diverges as T -> 0 and a floored 0DTE charm is an extrapolation, not a
    measurement. Returns None rather than partial output: a contract that
    cannot produce one Greek cannot produce a trustworthy set.
    """
    if not (spot and strike and iv) or spot <= 0 or strike <= 0 or iv <= 0:
        return None
    t_raw = t_years
    t = max(t_years, MIN_T)
    dd = _d1_d2(spot, strike, iv, t, r)
    if dd is None:
        return None
    d1, d2, denom = dd            # denom = sigma sqrt(t)

    gamma = norm_pdf(d1) / (spot * denom)
    delta = norm_cdf(d1) if right == "C" else norm_cdf(d1) - 1.0
    # Vanna and charm are identical for calls and puts at q = 0: put delta is
    # call delta minus a constant, and a constant differentiates away.
    vanna = -norm_pdf(d1) * d2 / iv
    charm = -norm_pdf(d1) * (2.0 * r * t - d2 * denom) / (2.0 * t * denom)

    out = {"gamma": gamma, "delta": delta, "vanna": vanna, "charm": charm,
           "t_floored": t_raw < MIN_T}
    return out if all(math.isfinite(v) for k, v in out.items()
                      if isinstance(v, float)) else None


# ---------------------------------------------------------------------------
# Expiry bucketing
# ---------------------------------------------------------------------------

def _third_friday(d: dt.date) -> dt.date:
    first = d.replace(day=1)
    # weekday(): Mon=0 .. Fri=4
    offset = (4 - first.weekday()) % 7
    return first + dt.timedelta(days=offset + 14)


def bucket_for(expiry: str, dte: int) -> str:
    """Exactly one bucket per expiry. Order matters and is deliberate:
    0DTE wins over everything, then quarterly, monthly, weekly, then the rest."""
    try:
        d = dt.date.fromisoformat(expiry)
    except ValueError:
        return "other"
    if dte <= 0:
        return "0dte"
    is_third_friday = d == _third_friday(d)
    if is_third_friday and d.month in (3, 6, 9, 12):
        return "quarterly"
    if is_third_friday:
        return "monthly"
    if dte <= 7:
        return "weekly"
    return "other"


BUCKETS = ["0dte", "weekly", "monthly", "quarterly", "other"]


# ---------------------------------------------------------------------------
# Profile construction
# ---------------------------------------------------------------------------

def gamma_flip_all(strike_gex: list[tuple[float, float]]) -> list[float]:
    """Every zero crossing of cumulative GEX, walking strikes upward.

    Linearly interpolated between the bracketing strikes. A real book crosses
    zero more than once: far-OTM strikes carry tiny GEX that oscillates around
    zero, so the *first* crossing is usually noise a long way from spot.
    """
    crossings: list[float] = []
    cum = 0.0
    prev_strike = prev_cum = None
    for strike, gex in sorted(strike_gex):
        cum += gex
        if prev_cum is not None and (prev_cum < 0 <= cum or prev_cum > 0 >= cum):
            span = cum - prev_cum
            crossings.append(strike if span == 0
                             else prev_strike + (-prev_cum / span) * (strike - prev_strike))
        prev_strike, prev_cum = strike, cum
    return crossings


def gamma_flip(strike_gex: list[tuple[float, float]],
               spot: Optional[float] = None) -> Optional[float]:
    """The flip level: the zero crossing nearest spot.

    Returns None when the cumulative curve never changes sign -- a book that
    is positive or negative all the way up has no flip, and inventing one
    would be worse than reporting none.
    """
    crossings = gamma_flip_all(strike_gex)
    if not crossings:
        return None
    if spot is None:
        return crossings[0]
    return min(crossings, key=lambda c: abs(c - spot))


def net_gex_at_spot(rows: list[dict], candidate: float, r: float) -> float:
    """Total signed GEX if spot were `candidate`, gamma re-evaluated there.

    Gamma is a function of spot, so moving spot changes every strike's
    contribution -- which is the whole point of a flip level.
    """
    total = 0.0
    for row in rows:
        iv, k = row.get("implied_vol"), row.get("strike")
        oi = row.get("open_interest") or 0.0
        if not (iv and k) or oi <= 0 or iv <= 0 or iv >= MAX_SANE_IV:
            continue
        g = bs_gamma(candidate, k, iv, max(row.get("dte") or 0, 0) / 365.0, r)
        if g is None:
            continue
        notional = g * oi * 100.0 * candidate
        total += notional if row.get("right") == "C" else -notional
    return total


def zero_gamma_level_with_reason(rows: list[dict], spot: float, r: float,
                                 band: float = 0.15, steps: int = 60
                                 ) -> tuple[Optional[float], str]:
    """zero_gamma_level, plus a code saying why a None is None.

    A blank flip is not self-explanatory: it could mean the book is genuinely
    one-signed across the window, that the scan found nothing, or that there
    was no usable data at all. Those demand different responses -- the first is
    a real market state, the last is a broken snapshot -- so the reason travels
    with the row rather than leaving a reader to guess.
    """
    if not spot or spot <= 0:
        return None, "no_spot"
    usable = [x for x in rows
              if (x.get("implied_vol") or 0) > 0
              and (x.get("open_interest") or 0) > 0
              and x.get("strike")]
    if not usable:
        return None, "no_usable_rows"

    lo, hi = spot * (1.0 - band), spot * (1.0 + band)
    level = zero_gamma_level(rows, spot, r, band=band, steps=steps)
    if level is not None:
        return level, "crossing_found"

    # One-signed across the whole window: report which sign, because a book
    # that is short gamma everywhere in range reads very differently from one
    # that is long gamma everywhere.
    lo_val = net_gex_at_spot(rows, lo, r)
    hi_val = net_gex_at_spot(rows, hi, r)
    if lo_val >= 0 and hi_val >= 0:
        return None, "one_signed_positive_in_band"
    if lo_val <= 0 and hi_val <= 0:
        return None, "one_signed_negative_in_band"
    return None, "no_crossing_found_in_band"


def zero_gamma_level(rows: list[dict], spot: float, r: float,
                     band: float = 0.15, steps: int = 60) -> Optional[float]:
    """The zero-gamma level: the spot at which net dealer gamma changes sign.

    This is the standard 'gamma flip'. It is NOT the same thing as the zero
    crossing of GEX accumulated across strikes at a fixed spot -- that curve
    answers a different question and can fail to cross at all for a book that
    is one-signed at today's spot, which is exactly what it did for SPY, QQQ
    and IWM on 4 Sep while the vendor reported a flip just above spot.

    Scans a +/-band window around spot, takes the sign change nearest spot,
    then bisects for precision. Returns None if net gamma holds one sign across
    the whole window -- a genuinely one-signed book has no flip in range, and
    inventing one would be worse than reporting none.
    """
    if not spot or spot <= 0:
        return None
    lo, hi = spot * (1.0 - band), spot * (1.0 + band)
    xs = [lo + (hi - lo) * i / steps for i in range(steps + 1)]
    vals = [(x, net_gex_at_spot(rows, x, r)) for x in xs]

    brackets = []
    for (x0, v0), (x1, v1) in zip(vals, vals[1:]):
        if v0 == 0:
            brackets.append((x0, x0))
        elif (v0 < 0 < v1) or (v0 > 0 > v1):
            brackets.append((x0, x1))
    if not brackets:
        return None

    x0, x1 = min(brackets, key=lambda b: abs((b[0] + b[1]) / 2 - spot))
    if x0 == x1:
        return round(x0, 4)
    v0 = net_gex_at_spot(rows, x0, r)
    for _ in range(40):                     # ~1e-12 relative precision
        mid = (x0 + x1) / 2
        vm = net_gex_at_spot(rows, mid, r)
        if vm == 0:
            return round(mid, 4)
        if (v0 < 0) != (vm < 0):
            x1 = mid
        else:
            x0, v0 = mid, vm
    return round((x0 + x1) / 2, 4)


def max_pain(rows: list[dict]) -> Optional[float]:
    """Strike at which total in-the-money payout to option holders is smallest.

    Evaluated at every listed strike: for candidate settle S,
        payout(S) = sum_calls OI x max(0, S - K) + sum_puts OI x max(0, K - S)
    """
    strikes = sorted({r["strike"] for r in rows if r["strike"]})
    if not strikes:
        return None
    best_s, best_pay = None, None
    for s in strikes:
        pay = 0.0
        for r in rows:
            oi, k = r["open_interest"] or 0.0, r["strike"]
            if not oi or not k:
                continue
            if r["right"] == "C" and s > k:
                pay += oi * (s - k)
            elif r["right"] == "P" and k > s:
                pay += oi * (k - s)
        if best_pay is None or pay < best_pay:
            best_s, best_pay = s, pay
    return best_s


def dominant_bucket_at_strike(rows: list[dict], spot: float,
                              strike: Optional[float]) -> Optional[str]:
    """Which expiry bucket contributes most |GEX| at one strike.

    The architecture wants the pin rate segmented by expiry type. A symbol-level
    bucket share does not answer that: what matters is which expiry is actually
    driving the level being scored. So the reference strike is classified by the
    expiry that dominates it, not by the book as a whole.
    """
    if strike is None:
        return None
    totals: dict[str, float] = defaultdict(float)
    for r in rows:
        if r.get("strike") != strike:
            continue
        g, oi = r.get("gamma"), r.get("open_interest") or 0.0
        if g is None or oi <= 0:
            continue
        totals[bucket_for(r["expiry"], r.get("dte") or 0)] += abs(g * oi * 100.0 * spot)
    return max(totals, key=totals.__getitem__) if totals else None


def dominant_bucket_by_oi(rows: list[dict], strike: Optional[float]) -> Optional[str]:
    """Which expiry bucket holds most OI at one strike.

    Max pain is an OI-weighted payout minimum, not a gamma construct, so its
    reference strike is classified by open interest rather than by |GEX|.
    """
    if strike is None:
        return None
    totals: dict[str, float] = defaultdict(float)
    for r in rows:
        if r.get("strike") != strike:
            continue
        oi = r.get("open_interest") or 0.0
        if oi <= 0:
            continue
        totals[bucket_for(r["expiry"], r.get("dte") or 0)] += oi
    return max(totals, key=totals.__getitem__) if totals else None


def _empty_greek_aggregates() -> dict:
    """The four-Greek keys, all None. Kept in one place so an empty profile and
    a populated one always carry the SAME key set -- a downstream reader must
    never have to test for a missing key to tell 'no data' from 'zero'."""
    return {
        "dex_shares": None, "dex_notional": None,
        "vex_shares_per_volpt": None, "vex_notional_per_volpt": None,
        "chex_shares_per_day": None, "chex_notional_per_day": None,
        "abs_dex_shares": None,
    }


def _profile(rows: list[dict], spot: float) -> dict:
    """Aggregate per-strike GEX, DEX, VEX and CHEX, and the levels from them.

    All four are accumulated in one pass over the same rows with the same
    dealer_position multiplier, which is what makes them one mechanism group:
    they cannot disagree about the book, only about which sensitivity of it
    they describe.
    """
    by_strike: dict[float, float] = defaultdict(float)
    call_gex: dict[float, float] = defaultdict(float)
    put_gex: dict[float, float] = defaultdict(float)
    dex_strike: dict[float, float] = defaultdict(float)
    vex_strike: dict[float, float] = defaultdict(float)
    chex_strike: dict[float, float] = defaultdict(float)

    for r in rows:
        g, oi, k = r.get("gamma"), r.get("open_interest") or 0.0, r.get("strike")
        if g is None or not k or oi <= 0:
            continue
        pos = dealer_position(r["right"])
        contracts = oi * CONTRACT_MULTIPLIER

        notional = g * contracts * spot
        by_strike[k] += pos * notional        # long calls -> +gamma, puts -> -
        if r["right"] == "C":
            call_gex[k] += notional
        else:
            put_gex[k] += notional

        # The other three ride the same position sign. A row whose extra Greeks
        # failed to solve still contributes its gamma above rather than being
        # dropped -- losing a strike from the GEX profile to protect a charm
        # number would be the wrong trade.
        d, v, c = r.get("delta"), r.get("vanna"), r.get("charm")
        if d is not None:
            dex_strike[k] += pos * d * contracts
        if v is not None:
            vex_strike[k] += pos * v * VOL_POINT * contracts
        if c is not None:
            chex_strike[k] += pos * (c / DAYS_PER_YEAR) * contracts

    if not by_strike:
        return {"net_gex": None, "shares_per_1pct": None,
                "dollar_gamma_per_1pct": None,
                "gamma_flip": None, "call_wall": None, "put_wall": None,
                "put_wall_gamma": None, "put_wall_oi": None,
                "put_wall_otm": None, "call_wall_otm": None,
                "strikes": 0, **_empty_greek_aggregates()}

    # Two competing put-wall definitions, reported side by side rather than
    # collapsed. They answer different questions and last night they disagreed
    # by 19 points on QQQ:
    #   gamma -- the strike carrying the most put gamma, which sits near the
    #            money because gamma peaks at the money
    #   oi    -- the largest OTM put OI shelf, which is the level traders mean
    #            by "put wall": where size actually sits below spot
    put_wall_gamma = (max(put_gex.items(), key=lambda kv: kv[1])[0]
                      if put_gex else None)
    otm_put_oi: dict[float, float] = defaultdict(float)
    for r in rows:
        if r.get("right") != "P":
            continue
        k, oi = r.get("strike"), r.get("open_interest") or 0.0
        if k and oi > 0 and k < spot:
            otm_put_oi[k] += oi
    put_wall_oi = (max(otm_put_oi.items(), key=lambda kv: kv[1])[0]
                   if otm_put_oi else None)

    # Third definition, and the one FlashAlpha turns out to use: the extreme
    # GEX strike restricted to OTM. Verified 5 Sep -- it reproduces their
    # put_wall on both SPY (760) and QQQ (700), where the all-strikes version
    # disagreed by 19 points on QQQ because the ATM strike carries the largest
    # negative GEX without being a wall in any tradeable sense.
    _pairs_all = sorted(by_strike.items())
    otm_below = [(k, v) for k, v in _pairs_all if k < spot and v < 0]
    otm_above = [(k, v) for k, v in _pairs_all if k > spot and v > 0]
    put_wall_otm = min(otm_below, key=lambda kv: kv[1])[0] if otm_below else None
    call_wall_otm = max(otm_above, key=lambda kv: kv[1])[0] if otm_above else None

    pairs = sorted(by_strike.items())
    net = sum(v for _, v in pairs)
    # Architecture: store shares and dollars per 1% move, and treat raw notional
    # as derived. shares_per_1pct is the primary quantity; the dollar figure is
    # computed from it rather than independently, so the two cannot drift.
    shares_1pct = net * 0.01
    positives = [(k, v) for k, v in pairs if v > 0]
    negatives = [(k, v) for k, v in pairs if v < 0]

    # Shares is the primary for all three new Greeks, exactly as it is for
    # gamma; the notional is derived (shares x spot) so the pair cannot drift.
    dex_sh = sum(dex_strike.values())
    vex_sh = sum(vex_strike.values())
    chex_sh = sum(chex_strike.values())
    return {
        "net_gex": net,
        "shares_per_1pct": shares_1pct,
        "dollar_gamma_per_1pct": shares_1pct * spot,
        # DEX: what the dealer OPTION BOOK is long, in shares. The hedge is the
        # opposite sign; the unwind at expiry is this sign. See the docstring.
        "dex_shares": dex_sh,
        "dex_notional": dex_sh * spot,
        # VEX: shares of delta gained per ONE vol point.
        "vex_shares_per_volpt": vex_sh,
        "vex_notional_per_volpt": vex_sh * spot,
        # CHEX: shares of delta gained per calendar day of time passing.
        "chex_shares_per_day": chex_sh,
        "chex_notional_per_day": chex_sh * spot,
        # Gross delta, for a share-of-book denominator that does not net to
        # nothing when longs and shorts cancel.
        "abs_dex_shares": sum(abs(v) for v in dex_strike.values()),
        "gamma_flip_cum_strikes": gamma_flip(pairs, spot),
        "gamma_flip_cum_all": gamma_flip_all(pairs),
        "call_wall": max(positives, key=lambda kv: kv[1])[0] if positives else None,
        "put_wall": min(negatives, key=lambda kv: kv[1])[0] if negatives else None,
        "peak_abs_gex_strike": max(pairs, key=lambda kv: abs(kv[1]))[0],
        "put_wall_gamma": put_wall_gamma,
        "put_wall_oi": put_wall_oi,
        "put_wall_otm": put_wall_otm,
        "call_wall_otm": call_wall_otm,
        "strikes": len(pairs),
        "per_strike": [{"strike": k, "gex": v,
                        "call_gex": call_gex.get(k, 0.0),
                        "put_gex": -put_gex.get(k, 0.0),
                        "dex": dex_strike.get(k, 0.0),
                        "vex": vex_strike.get(k, 0.0),
                        "chex": chex_strike.get(k, 0.0)} for k, v in pairs],
    }


def _strike_gex(rows: list[dict], spot: float) -> dict[float, float]:
    """Signed GEX per strike for an arbitrary subset of rows.

    Used to weigh one subset against another -- floored rows against their own
    bucket, say -- where counting rows would be the wrong measure, because one
    at-the-money contract can outweigh two hundred wings.
    """
    out: dict[float, float] = defaultdict(float)
    for r in rows:
        g, oi, k = r.get("gamma"), r.get("open_interest") or 0.0, r.get("strike")
        if g is None or not k or oi <= 0:
            continue
        out[k] += dealer_position(r["right"]) * g * oi * CONTRACT_MULTIPLIER * spot
    return out


def _oi_structure(rows: list[dict]) -> dict:
    """Open-interest shape of a set of rows, with no reference to any greek.

    This is what a settled 0DTE bucket is allowed to report. OI at settlement
    is an observed fact about what was outstanding; gamma at settlement is an
    extrapolation from a quote nobody would trade against.
    """
    call_oi = sum(r.get("open_interest") or 0.0 for r in rows if r.get("right") == "C")
    put_oi = sum(r.get("open_interest") or 0.0 for r in rows if r.get("right") == "P")
    total = call_oi + put_oi
    strikes = {r.get("strike") for r in rows if r.get("strike")}
    return {
        "contracts": len(rows),
        "oi_total": total,
        "oi_calls": call_oi,
        "oi_puts": put_oi,
        "oi_put_call_ratio": round(put_oi / call_oi, 4) if call_oi else None,
        "oi_strikes": len(strikes),
    }


def expiration_release(rows: list[dict], spot: float) -> list[dict]:
    """Dated dealer-delta unwind: how much hedge rolls off at each expiry.

    One row per upcoming expiry, earliest first. `dex_shares` is what the
    option book expiring that day is long; when it expires that delta becomes
    zero and the hedge against it is no longer needed, so the dealer trades
    +dex_shares shares -- BUYING when DEX is positive. `unwind_direction`
    spells that out rather than leaving a reader to re-derive a sign that
    inverts the conclusion if they get it backwards.

    This is a mechanical consequence of contracts expiring, not a forecast. It
    says what hedge is scheduled to be released and when; it does not say the
    market will move, because the other side of every hedge is somebody else's
    position that also rolls.

    `unwind_direction` is constant under dealers-hand-v1 -- see the module
    docstring. It is the magnitude and the dating that mean anything here.
    """
    agg: dict[str, dict] = {}
    for r in rows:
        d, oi, exp = r.get("delta"), r.get("open_interest") or 0.0, r.get("expiry")
        if d is None or oi <= 0 or not exp:
            continue
        a = agg.setdefault(exp, {"expiry": exp, "dte": r.get("dte"),
                                 "dex_shares": 0.0, "contracts": 0.0})
        a["dex_shares"] += dealer_position(r["right"]) * d * oi * CONTRACT_MULTIPLIER
        a["contracts"] += oi
        # An expiry's DTE is a property of the date, but rows can disagree if a
        # snapshot straddles midnight; take the smallest, which is the one the
        # scheduler cares about.
        if a["dte"] is None or (r.get("dte") is not None and r["dte"] < a["dte"]):
            a["dte"] = r.get("dte")

    out = sorted(agg.values(), key=lambda a: a["expiry"])
    total_abs = sum(abs(a["dex_shares"]) for a in out)
    cum = 0.0
    for a in out:
        share = abs(a["dex_shares"]) / total_abs if total_abs else None
        cum += share or 0.0
        a["bucket"] = bucket_for(a["expiry"], a["dte"] or 0)
        a["dex_notional"] = a["dex_shares"] * spot
        a["share_of_abs_dex"] = round(share, 4) if share is not None else None
        a["cumulative_share_of_abs_dex"] = round(cum, 4) if total_abs else None
        a["unwind_direction"] = ("dealer_buys" if a["dex_shares"] > 0 else
                                 "dealer_sells" if a["dex_shares"] < 0 else "flat")
    return out


def compute_symbol(rows: list[dict], symbol: str) -> dict:
    """Full computed output for one symbol's chain snapshot."""
    spot = next((r["spot"] for r in rows if r.get("spot")), None)
    fetched_at = next((r["fetched_at"] for r in rows if r.get("fetched_at")), None)

    # The deferral fence, enforced from the DATA rather than from a symbol
    # list. A chain whose rows say their Greeks are gated does not get Greeks,
    # whoever asked and whatever universe they passed. Massive writes this on
    # SPX and SPCX because that tier serves no IV for index underlyings and the
    # solved-IV path is red in tools/validate_iv_solver.py; computing anyway
    # would produce numbers that look exactly like the trustworthy ones.
    gated = {r.get("greeks_status") for r in rows} - {None, ""}
    if gated:
        return {"symbol": symbol,
                "error": f"greeks deferred: {'/'.join(sorted(gated))}",
                "greeks_status": sorted(gated)[0],
                "mechanism_group": MECHANISM_GROUP,
                "session_date": session.session_date(
                    next((r.get("fetched_at") for r in rows if r.get("fetched_at")), None)),
                "quality": {"rows_in": len(rows), "deferred": True}}

    quality = {"rows_in": len(rows), "gamma_computed": 0, "gamma_supplied": 0,
               "skipped_no_iv": 0, "skipped_insane_iv": 0, "skipped_no_oi": 0,
               # Four-Greek extension. greeks_solved counts rows carrying the
               # full delta/vanna/charm set; chex_floored_rows counts rows whose
               # time input hit MIN_T, which is where a 0DTE charm number stops
               # being a measurement and becomes an extrapolation.
               "greeks_solved": 0, "greeks_unsolved": 0, "chex_floored_rows": 0,
               # Per-row IV provenance, counted rather than assumed, so a mixed
               # profile is visible as a mix instead of collapsing to whichever
               # label happened to be written first.
               "greeks_from_yf_iv": 0, "greeks_from_solver": 0}
    if not spot:
        return {"symbol": symbol, "error": "no spot in snapshot", "quality": quality}

    usable: list[dict] = []
    for r in rows:
        oi = r.get("open_interest") or 0.0
        if oi <= 0:
            quality["skipped_no_oi"] += 1
            continue

        iv = r.get("implied_vol")
        t_years = max(r.get("dte") or 0, 0) / DAYS_PER_YEAR
        vendor_gamma = r.get("gamma")

        # The full set is solved from IV whenever IV allows it, even when the
        # vendor supplies gamma -- a vendor gamma column says nothing about
        # delta, vanna or charm, and dropping three Greeks because one arrived
        # pre-computed would be a strange trade.
        greeks = None
        if iv is not None and 0 < iv < MAX_SANE_IV:
            greeks = bs_greeks(spot, r["strike"], iv, t_years,
                               config.RISK_FREE_RATE, r.get("right"))

        if vendor_gamma is not None:
            quality["gamma_supplied"] += 1
            extra = {"gamma": vendor_gamma}
            if greeks:
                extra.update({k: greeks[k] for k in ("delta", "vanna", "charm")})
                quality["greeks_solved"] += 1
                quality["chex_floored_rows"] += int(greeks["t_floored"])
                quality[_iv_counter(r)] += 1
            else:
                quality["greeks_unsolved"] += 1
            usable.append({**r, **extra})
            continue

        # No vendor gamma: IV is the only path, so the usual rejections apply.
        if iv is None or iv <= 0:
            quality["skipped_no_iv"] += 1
            continue
        if iv >= MAX_SANE_IV:
            quality["skipped_insane_iv"] += 1
            continue
        if greeks is None:
            quality["skipped_no_iv"] += 1
            continue
        quality["gamma_computed"] += 1
        quality["greeks_solved"] += 1
        quality["chex_floored_rows"] += int(greeks["t_floored"])
        quality[_iv_counter(r)] += 1
        usable.append({**r, "gamma": greeks["gamma"], "delta": greeks["delta"],
                       "vanna": greeks["vanna"], "charm": greeks["charm"]})

    # ---- settlement semantics ------------------------------------------
    # At a settled capture the day's contracts are corpses; their gamma is an
    # artifact, not an exposure. Exposure aggregates are built WITHOUT them.
    # OI constructs below still read `usable` in full -- the distortion was
    # never in the open interest. See config.SETTLED_0DTE_RULE.
    settled = is_settled_capture(fetched_at)
    if settled:
        exposure_rows = [r for r in usable if (r.get("dte") or 0) > 0]
        excluded = [r for r in usable if (r.get("dte") or 0) <= 0]
    else:
        exposure_rows, excluded = usable, []
    quality["exposure_rows"] = len(exposure_rows)
    quality["settled_0dte_excluded_rows"] = len(excluded)

    overall = _profile(exposure_rows, spot)
    # Primary flip = standard zero-gamma level (spot at which net dealer gamma
    # changes sign). The cumulative-across-strikes crossing is retained beside
    # it under gamma_flip_cum_strikes; the two answer different questions and
    # disagreeing is expected, not a bug.
    _flip, _flip_reason = zero_gamma_level_with_reason(
        exposure_rows, spot, config.RISK_FREE_RATE)
    overall["gamma_flip"] = _flip
    overall["flip_reason"] = _flip_reason
    overall["flip_band_pct"] = 15.0
    overall["gamma_flip_method"] = "zero_gamma_level_spot_scan"

    buckets: dict[str, dict] = {}
    total_abs = sum(abs(s["gex"]) for s in overall.get("per_strike", [])) or 0.0
    total_abs_dex = overall.get("abs_dex_shares") or 0.0
    for b in BUCKETS:
        brows = [r for r in usable if bucket_for(r["expiry"], r.get("dte") or 0) == b]
        if not brows:
            continue

        # The settled 0DTE bucket reports OI structure and refuses to report
        # greeks. Reported, not dropped: open interest at settlement is a fact.
        if settled and b == "0dte":
            buckets[b] = {
                **_empty_greek_aggregates(),
                "net_gex": None, "shares_per_1pct": None,
                "dollar_gamma_per_1pct": None,
                "greeks": config.SETTLED_0DTE_GREEKS_LABEL,
                "excluded_from_exposure_aggregates": True,
                "rule": config.SETTLED_0DTE_RULE,
                "share_of_total_abs_gex": None,
                "share_of_total_abs_dex": None,
                "expiries": sorted({r["expiry"] for r in brows}),
                **_oi_structure(brows),
            }
            continue

        p = _profile(brows, spot)
        b_abs = sum(abs(s["gex"]) for s in p.get("per_strike", []))
        p.pop("per_strike", None)
        p["share_of_total_abs_gex"] = round(b_abs / total_abs, 4) if total_abs else None
        # Gamma share and delta share are different questions and answer
        # differently: 0DTE dominates gamma while carrying little delta.
        p["share_of_total_abs_dex"] = (
            round((p.get("abs_dex_shares") or 0.0) / total_abs_dex, 4)
            if total_abs_dex else None)
        p["expiries"] = sorted({r["expiry"] for r in brows})
        p.update(_oi_structure(brows))
        # MIN_T is a guard, never load-bearing. A bucket whose floored rows
        # carry more than config.MIN_T_LOAD_BEARING_SHARE of its own |GEX| says
        # so on the profile: past that point the floor is not preventing an
        # error, it is manufacturing the answer.
        floored = [r for r in brows
                   if max(r.get("dte") or 0, 0) / DAYS_PER_YEAR < MIN_T]
        f_abs = sum(abs(v) for v in _strike_gex(floored, spot).values())
        share = (f_abs / b_abs) if b_abs else 0.0
        p["chex_floored_rows"] = len(floored)
        p["floored_share_of_abs_gex"] = round(share, 4)
        p["min_t_load_bearing"] = share > config.MIN_T_LOAD_BEARING_SHARE
        buckets[b] = p

    mp = max_pain(usable)
    per_strike = overall.pop("per_strike", [])
    return {
        "symbol": symbol,
        "computed_at": session.utc_iso(),
        "fetched_at": fetched_at,
        "session_date": session_date(fetched_at),
        "spot": spot,
        "convention_version": config.CONVENTION_VERSION,
        "convention_caveat": config.CONVENTION_CAVEAT,
        # GEX, DEX, VEX and CHEX are four views of one chain, not four signals.
        # Architecture 26.9: they form a single confluence cluster.
        "mechanism_group": MECHANISM_GROUP,
        # ...but not every field in this profile is in that cluster. The OI
        # constructs are their own mechanism and the quality gates are evidence
        # about the chain rather than from it, so the group is stamped PER
        # FIELD as well. A consumer counting confluence reads this map, not the
        # scalar above.
        "field_mechanism_groups": FIELD_MECHANISM_GROUPS,
        "gamma_source": ("vendor" if quality["gamma_supplied"]
                         else greeks_source_for(quality)),
        # Varies with the IV that produced it -- see IV_SOURCE_LABELS. Hardcoded
        # until now, which made a solver-IV profile and a vendor-IV profile
        # indistinguishable in the store. That was the prerequisite blocking
        # SPX Greeks from going live.
        "greeks_source": greeks_source_for(quality),
        "risk_free_rate": config.RISK_FREE_RATE,
        # What this capture is, and therefore what it is allowed to claim.
        "capture": "settled_eod" if settled else "intraday",
        "settled_0dte_rule": config.SETTLED_0DTE_RULE if settled else None,
        "overall": overall,
        # Dated dealer-delta unwind, earliest expiry first. Built from the
        # exposure rows, so a settled capture's own expiry is absent -- its
        # unwind is not upcoming, it is happening as the snapshot is taken.
        "expiration_release": expiration_release(exposure_rows, spot),
        # OI constructs read every row, 0DTE included. Max pain is a payout
        # minimum over open interest and was never touched by the MIN_T floor.
        "max_pain": mp,
        # Expiry that dominates each reference level, so the pin rate can be
        # segmented by expiry type as the architecture requires.
        "expiry_type": dominant_bucket_at_strike(
            exposure_rows, spot, overall.get("peak_abs_gex_strike")),
        "max_pain_expiry_type": dominant_bucket_by_oi(usable, mp),
        "buckets": buckets,
        "quality": quality,
        # Data-quality gates over the same chain. Carried on the profile so the
        # pin log can refuse to let a bad day into the base rate silently.
        "gates": quality_gates.evaluate(rows),
        "per_strike": per_strike,
    }


# ---------------------------------------------------------------------------
# Snapshot IO
# ---------------------------------------------------------------------------

def _to_float(v):
    try:
        f = float(v)
        return None if f != f else f
    except (TypeError, ValueError):
        return None


def load_chain(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fp:
        for rec in csv.DictReader(fp):
            rows.append({
                "symbol": rec.get("symbol"),
                "fetched_at": rec.get("fetched_at"),
                "spot": _to_float(rec.get("spot")),
                "expiry": rec.get("expiry"),
                "dte": int(_to_float(rec.get("dte")) or 0),
                "right": rec.get("right"),
                "strike": _to_float(rec.get("strike")),
                "open_interest": _to_float(rec.get("open_interest")),
                "implied_vol": _to_float(rec.get("implied_vol")),
                # Needed by the data-quality gates, not by the GEX maths.
                "volume": _to_float(rec.get("volume")),
                "bid": _to_float(rec.get("bid")),
                "ask": _to_float(rec.get("ask")),
                "gamma": _to_float(rec.get("gamma")),   # absent today, vendor later
                # Written by altdata.sources.massive_chain on symbols whose
                # Greeks are gated. Absent on yfinance chains, which is the
                # ungated case -- see the fence in compute_symbol.
                # Set by tools/iv_solver.py on any row it solved. Absent on
                # a raw vendor chain, which is itself the provenance.
                "iv_source": (rec.get("iv_source") or None),
                "greeks_status": (rec.get("greeks_status") or None),
                "vendor": (rec.get("vendor") or None),
                "spot_source": (rec.get("spot_source") or None),
            })
    return rows


def snapshot_fetched_at(path: Path) -> Optional[dt.datetime]:
    """The observation time a chain CSV carries, from its first data row.

    Only the first row is read: every row in a snapshot shares one fetched_at,
    and parsing 9,000 of them to learn one timestamp would be silly.
    """
    try:
        with path.open(encoding="utf-8", newline="") as fp:
            row = next(csv.DictReader(fp), None)
    except OSError:
        return None
    if not row or not row.get("fetched_at"):
        return None
    try:
        return session.to_eastern(row["fetched_at"])
    except Exception:  # noqa: BLE001 -- an unparseable stamp is just unusable
        return None


def _closeness_to_target(ts: Optional[dt.datetime]) -> tuple[int, float]:
    """Sort key: how far this observation is from the EOD target, in minutes.

    Snapshots with no readable timestamp sort last rather than being dropped --
    a chain that cannot say when it was taken is still better than no chain.
    """
    if ts is None:
        return (1, 0.0)
    hh, mm = (int(x) for x in config.EOD_SNAPSHOT_TARGET_ET.split(":"))
    return (0, abs((ts.hour * 60 + ts.minute) - (hh * 60 + mm)))


def newest_chains(date: Optional[str] = None,
                  symbols: Optional[list[str]] = None,
                  base_dir: Optional[str] = None) -> dict[str, Path]:
    """The chain CSV per symbol that best represents a session's close.

    NOT the newest file, despite the name -- kept only because callers import
    it. Two things were wrong with "newest":

      * mtime is a filesystem fact, not an observation time. Copying, restoring
        or backing up a directory rewrites it, and then the "newest" snapshot is
        whichever file the copy happened to touch last.
      * A snapshot taken late in the evening has ALREADY LOST the day's 0DTE
        contracts -- they expired and dropped out of the chain. On 2026-09-04
        the 22:44 ET capture of SPY held 9,003 rows and no expiring contracts at
        all, against 9,428 rows including 425 0DTE in the 16:10 capture. Picking
        the later file silently deleted the bucket that carries most of the
        gamma, and nothing downstream could tell, because an absent bucket and
        a genuinely empty one look identical.

    So: rank by the fetched_at the rows themselves carry, and take the capture
    nearest config.EOD_SNAPSHOT_TARGET_ET. Ties break to the later observation.
    """
    root = Path(base_dir or config.CHAIN_DIR)
    if not root.exists():
        return {}
    days = sorted((p for p in root.iterdir() if p.is_dir()), reverse=True)
    if not days:
        return {}

    def _pick(day: Path) -> dict[str, Path]:
        best: dict[str, tuple[tuple, Path]] = {}
        for p in sorted(day.glob("*.csv")):
            sym = p.name.split("_")[0]
            if symbols and sym not in symbols:
                continue
            ts = snapshot_fetched_at(p)
            # Negated epoch so that, at equal distance from the target, the
            # later observation sorts first.
            rank = (*_closeness_to_target(ts), -(ts.timestamp() if ts else 0.0))
            if sym not in best or rank < best[sym][0]:
                best[sym] = (rank, p)
        return {sym: p for sym, (_, p) in sorted(best.items())}

    if date:
        day = root / date
        return _pick(day) if day.exists() else {}

    # No date given: the newest day that actually holds chains for the symbols
    # asked for, not merely the newest directory. Two vendors write here now
    # and they do not always write on the same days -- a Massive-only capture
    # would otherwise make "latest" a day the yfinance symbols never appear in,
    # and the run would report no chains while a perfectly good set sat one
    # directory back.
    for day in days:
        found = _pick(day)
        if found:
            return found
    return {}


def write_computed(result: dict, base_dir: Optional[str] = None) -> Path:
    day = result.get("session_date") or session.session_date(
        result.get("fetched_at") or result.get("computed_at"))
    out_dir = Path(base_dir or config.COMPUTED_DIR) / day
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = session.utc_stamp("%H%M%SZ")
    # New name for the four-Greek payload. Readers glob both this and the old
    # *_gex.json, so profiles written before the extension stay loadable and
    # nothing has to be migrated or deleted.
    path = out_dir / f"{result['symbol']}_{stamp}_exposure.json"
    path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return path


# Column order is the file format. Append-only, exactly as the pin log.
EXPIRATION_RELEASE_COLUMNS = [
    "date", "symbol", "expiry", "dte", "bucket",
    "dex_shares", "dex_notional", "unwind_direction",
    "share_of_abs_dex", "cumulative_share_of_abs_dex",
    "contracts", "spot", "convention_version", "mechanism_group",
]


def release_rows(result: dict) -> list[dict]:
    """Flatten one computed profile's expiration release into CSV rows."""
    day = result.get("session_date")
    sym, spot = result.get("symbol"), result.get("spot")
    out = []
    for a in result.get("expiration_release") or []:
        out.append({
            "date": day, "symbol": sym, "expiry": a.get("expiry"),
            "dte": a.get("dte"), "bucket": a.get("bucket"),
            "dex_shares": a.get("dex_shares"),
            "dex_notional": a.get("dex_notional"),
            "unwind_direction": a.get("unwind_direction"),
            "share_of_abs_dex": a.get("share_of_abs_dex"),
            "cumulative_share_of_abs_dex": a.get("cumulative_share_of_abs_dex"),
            "contracts": a.get("contracts"), "spot": spot,
            "convention_version": result.get("convention_version"),
            "mechanism_group": result.get("mechanism_group"),
        })
    return out


def append_release(rows: list[dict], path: Optional[str] = None) -> Optional[Path]:
    """Append release rows, replacing any existing (date, symbol).

    Replacement is by (date, symbol) rather than (date, symbol, expiry): a
    re-run can legitimately produce a DIFFERENT set of expiries, and keying on
    the expiry too would leave yesterday's stale rows behind forever.
    """
    if not rows:
        return None
    p = Path(path or config.EXPIRATION_RELEASE_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)

    existing: list[dict] = []
    if p.exists():
        with p.open(encoding="utf-8", newline="") as fp:
            existing = list(csv.DictReader(fp))

    replacing = {(r["date"], r["symbol"]) for r in rows}
    kept = [r for r in existing
            if (r.get("date"), r.get("symbol")) not in replacing]
    merged = kept + [{k: ("" if v is None else v) for k, v in r.items()}
                     for r in rows]
    merged.sort(key=lambda r: (str(r.get("date")), str(r.get("symbol")),
                               str(r.get("expiry"))))
    with p.open("w", encoding="utf-8", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=EXPIRATION_RELEASE_COLUMNS,
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(merged)
    return p


def run(symbols: Optional[list[str]] = None, date: Optional[str] = None,
        base_dir: Optional[str] = None, out_dir: Optional[str] = None,
        release_path: Optional[str] = None,
        run_id: Optional[str] = None) -> dict:
    chains = newest_chains(date, symbols, base_dir)
    if not chains:
        log.warning("No chain snapshots found under %s", base_dir or config.CHAIN_DIR)
        return {}
    results: dict[str, dict] = {}
    release: list[dict] = []
    for sym, path in chains.items():
        try:
            res = compute_symbol(load_chain(path), sym)
            # Stamped here rather than inside compute_symbol: compute_symbol is
            # a pure function of a chain and must stay replayable without a
            # run identity, which is exactly what the packet's output_hash
            # depends on. The run_id is a property of the WRITE, not the maths.
            if run_id:
                res["run_id"] = run_id
            res["source_chain"] = str(path)
            res["computed_path"] = str(write_computed(res, out_dir))
            release.extend(release_rows(res))
            results[sym] = res
        except Exception:  # noqa: BLE001 -- one bad symbol must not end the run
            log.exception("compute failed for %s", sym)
    # Written once for the whole run rather than per symbol: the file is
    # rewritten in full each time, and doing that 13 times a night would be
    # 13 chances to be interrupted halfway.
    try:
        p = append_release(release, release_path)
        if p:
            log.info("  expiration release: %d rows -> %s", len(release), p)
    except Exception:  # noqa: BLE001 -- a side table must not fail the run
        log.exception("expiration-release write failed; profiles are stored")
    return results


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compute per-strike GEX/DEX/VEX/CHEX from stored chains")
    ap.add_argument("--symbols", nargs="*")
    ap.add_argument("--date", default=None, help="Chain date (YYYY-MM-DD)")
    ap.add_argument("--base-dir", default=None)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--release-path", default=None,
                    help="Override config.EXPIRATION_RELEASE_PATH")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    res = run(args.symbols, args.date, args.base_dir, args.out_dir,
              args.release_path)
    if not res:
        print("No chains to compute. Run altdata.sources.options_chain first.")
        return 1

    print(f"\nconvention: {config.CONVENTION_VERSION}   "
          f"mechanism_group: {MECHANISM_GROUP} (one cluster, not four votes)")
    print(f"{'sym':<6} {'spot':>9} {'$gamma/1%':>16} {'flip':>9} "
          f"{'call wall':>9} {'put wall':>9} {'max pain':>9}")
    for sym, r in res.items():
        if r.get("error"):
            print(f"{sym:<6} ERROR: {r['error']}")
            continue
        o = r["overall"]
        fmt = lambda v, w=9, p=2: (f"{v:>{w},.{p}f}" if isinstance(v, (int, float)) else f"{'-':>{w}}")
        print(f"{sym:<6} {fmt(r['spot'])} {fmt(o['dollar_gamma_per_1pct'], 16, 0)} "
              f"{fmt(o['gamma_flip'])} {fmt(o['call_wall'])} {fmt(o['put_wall'])} "
              f"{fmt(r['max_pain'])}")

    print(f"\n{'sym':<6} {'DEX shares':>15} {'VEX sh/volpt':>15} "
          f"{'CHEX sh/day':>15}   next expiry unwind")
    for sym, r in res.items():
        if r.get("error"):
            continue
        o = r["overall"]
        rel = (r.get("expiration_release") or [{}])[0]
        fmt = lambda v, w=15: (f"{v:>{w},.0f}" if isinstance(v, (int, float)) else f"{'-':>{w}}")
        nxt = (f"{rel.get('expiry')} ({rel.get('dte')}d) "
               f"{rel.get('dex_shares') or 0:,.0f} sh {rel.get('unwind_direction')}"
               if rel.get("expiry") else "-")
        print(f"{sym:<6} {fmt(o.get('dex_shares'))} "
              f"{fmt(o.get('vex_shares_per_volpt'))} "
              f"{fmt(o.get('chex_shares_per_day'))}   {nxt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
