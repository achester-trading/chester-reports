"""
Implied volatility solved from option prices.

WHY THIS EXISTS. Massive's Starter tier serves SPX open interest but no IV and
no greeks, and yfinance has no SPX at all. Our GEX engine needs gamma, and
gamma needs vol. So for SPX we recover vol from prices ourselves. Everything
downstream -- gamma, GEX, flip, walls -- is unchanged; only the source of sigma
differs, and rows carry iv_source so that difference stays visible forever.

METHOD, and why each choice is made this way.

1. IMPLIED FORWARD PER EXPIRY, not spot.
   Index options are forward-priced: using spot with a guessed dividend yield
   introduces an error that looks exactly like skew. Put-call parity gives the
   forward the market is actually using, with no dividend assumption at all:

       C - P = e^(-rT) (F - K)   =>   F = K + e^(rT) (C - P)

   Evaluated at the strike where |C - P| is smallest -- the strike nearest the
   forward, where both legs are liquid and the parity residual is least
   sensitive to a wide quote. This is the CBOE VIX construction.

2. BLACK-76 ON THE FORWARD, not Black-Scholes on spot.
   Consistent with step 1. Removes the dividend term entirely.

3. OTM SIDE ONLY -- puts below the forward, calls above.
   A deep ITM option is almost all intrinsic: its price barely moves with vol,
   so vega is tiny and inverting the price amplifies quote noise into enormous
   IV error. The OTM wing carries the information. This is why the same
   construction is used for VIX, and it is the single most important choice in
   this file.

4. BRENT'S METHOD for the root-find.
   Bisection is robust but slow; Newton is fast but can leave the bracket when
   vega is small. Brent takes the guaranteed convergence of bisection with
   superlinear speed when the function is well behaved. Implemented here rather
   than pulled from scipy: scipy is a large dependency for one root-find, and
   the pipeline's install must stay small enough to be trivially reproducible
   on the VPS.

QUALITY GATES. A solved IV is only as good as the price it came from, so each
solve carries why it should or should not be trusted:

    no_bracket      the price is outside what any vol in range can produce --
                    typically a crossed or stale quote, or a sub-intrinsic mark
    wide_spread     relative spread beyond the declared ceiling
    stale_quote     last trade older than the declared ceiling
    no_quote        no usable bid/ask

Gated rows are returned with iv=None rather than silently dropped, so the
caller can count what was rejected instead of inferring it from a thinner
chain. Counts feed the existing data_quality fields.
"""

from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict
from typing import Optional

IV_SOURCE = "solved_bs_v1"

# Root-find bounds. 1% to 500% covers every real listed option; a solve that
# wants to leave this range is a bad price, not a real vol.
IV_LO = 0.01
IV_HI = 5.0
BRENT_TOL = 1e-8
BRENT_MAX_ITER = 100

# Quality ceilings. Declared here, overridable by the caller, and recorded on
# every solve so a later reader knows what was enforced.
MAX_REL_SPREAD = 0.35        # (ask-bid)/mid above this and the mid is a guess
MAX_QUOTE_AGE_DAYS = 3.0     # last trade older than this is a stale mark
MIN_PRICE = 0.01             # below a cent there is no information


# ---------------------------------------------------------------------------
# Black-76
# ---------------------------------------------------------------------------

def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black76_price(forward: float, strike: float, t: float, r: float,
                  sigma: float, right: str) -> float:
    """Undiscounted-forward Black-76 price of a European option."""
    if t <= 0 or sigma <= 0 or forward <= 0 or strike <= 0:
        # Degenerate: worth intrinsic on the forward, discounted.
        intrinsic = (max(forward - strike, 0.0) if right == "C"
                     else max(strike - forward, 0.0))
        return math.exp(-r * t) * intrinsic
    v = sigma * math.sqrt(t)
    d1 = (math.log(forward / strike) + 0.5 * v * v) / v
    d2 = d1 - v
    disc = math.exp(-r * t)
    if right == "C":
        return disc * (forward * norm_cdf(d1) - strike * norm_cdf(d2))
    return disc * (strike * norm_cdf(-d2) - forward * norm_cdf(-d1))


# ---------------------------------------------------------------------------
# Brent's method
# ---------------------------------------------------------------------------

def brentq(f, a: float, b: float, tol: float = BRENT_TOL,
           max_iter: int = BRENT_MAX_ITER) -> Optional[float]:
    """Root of f on [a, b]. Returns None if the interval does not bracket one.

    Standard Brent: inverse quadratic interpolation where it helps, secant
    where it does not, bisection whenever either would step outside the
    bracket or fail to halve the interval. The bracket is never abandoned, so
    this cannot wander off the way a bare Newton can when vega is small.
    """
    fa, fb = f(a), f(b)
    if fa == 0.0:
        return a
    if fb == 0.0:
        return b
    if fa * fb > 0:
        return None                      # no sign change: not bracketed

    if abs(fa) < abs(fb):
        a, b, fa, fb = b, a, fb, fa
    c, fc = a, fa
    d = e = b - a

    for _ in range(max_iter):
        if fb * fc > 0:
            c, fc = a, fa
            d = e = b - a
        if abs(fc) < abs(fb):
            a, b, c = b, c, b
            fa, fb, fc = fb, fc, fb
        tol1 = 2.0 * 1e-15 * abs(b) + 0.5 * tol
        xm = 0.5 * (c - b)
        if abs(xm) <= tol1 or fb == 0.0:
            return b
        if abs(e) >= tol1 and abs(fa) > abs(fb):
            s = fb / fa
            if a == c:
                p, q = 2.0 * xm * s, 1.0 - s          # secant
            else:
                q, rr = fa / fc, fb / fc              # inverse quadratic
                p = s * (2.0 * xm * q * (q - rr) - (b - a) * (rr - 1.0))
                q = (q - 1.0) * (rr - 1.0) * (s - 1.0)
            if p > 0:
                q = -q
            p = abs(p)
            if 2.0 * p < min(3.0 * xm * q - abs(tol1 * q), abs(e * q)):
                e, d = d, p / q
            else:
                d = e = xm                            # fall back to bisection
        else:
            d = e = xm
        a, fa = b, fb
        b += d if abs(d) > tol1 else (tol1 if xm > 0 else -tol1)
        fb = f(b)
    return b


# ---------------------------------------------------------------------------
# Implied forward
# ---------------------------------------------------------------------------

def mid_price(bid: Optional[float], ask: Optional[float],
              last: Optional[float] = None) -> Optional[float]:
    """Mid of a two-sided quote; last trade only if there is no quote."""
    if bid is not None and ask is not None and ask >= bid > 0:
        return (bid + ask) / 2.0
    if last and last > 0:
        return last
    return None


def rel_spread(bid: Optional[float], ask: Optional[float]) -> Optional[float]:
    if bid is None or ask is None or ask < bid or ask <= 0:
        return None
    mid = (bid + ask) / 2.0
    return (ask - bid) / mid if mid > 0 else None


def implied_forward(rows: list[dict], t: float, r: float) -> Optional[dict]:
    """Forward implied by put-call parity, from the strike with the tightest
    call/put price difference.

    Returns None when no strike has usable quotes on both legs -- inventing a
    forward from spot would silently reintroduce the dividend error this whole
    approach exists to avoid.
    """
    by_strike: dict[float, dict[str, dict]] = defaultdict(dict)
    for row in rows:
        k, right = row.get("strike"), row.get("right")
        if k and right in ("C", "P"):
            by_strike[k][right] = row

    best = None
    for k, legs in by_strike.items():
        c, p = legs.get("C"), legs.get("P")
        if not c or not p:
            continue
        cm = mid_price(c.get("bid"), c.get("ask"), c.get("last_price"))
        pm = mid_price(p.get("bid"), p.get("ask"), p.get("last_price"))
        if cm is None or pm is None:
            continue
        diff = abs(cm - pm)
        if best is None or diff < best["abs_diff"]:
            best = {"strike": k, "call_mid": cm, "put_mid": pm, "abs_diff": diff}

    if best is None:
        return None
    fwd = best["strike"] + math.exp(r * t) * (best["call_mid"] - best["put_mid"])
    if not math.isfinite(fwd) or fwd <= 0:
        return None
    return {"forward": fwd, "atm_strike": best["strike"],
            "parity_abs_diff": round(best["abs_diff"], 6)}


# ---------------------------------------------------------------------------
# Per-contract solve
# ---------------------------------------------------------------------------

def solve_one(price: float, forward: float, strike: float, t: float,
              r: float, right: str) -> tuple[Optional[float], Optional[str]]:
    """Invert Black-76 for sigma. Returns (iv, reject_reason)."""
    if price is None or price < MIN_PRICE:
        return None, "no_quote"
    lo = black76_price(forward, strike, t, r, IV_LO, right)
    hi = black76_price(forward, strike, t, r, IV_HI, right)
    if not (lo <= price <= hi):
        # Below the floor is a sub-intrinsic or crossed mark; above the ceiling
        # needs a vol no listed option carries. Either way the price is bad.
        return None, "no_bracket"
    iv = brentq(lambda s: black76_price(forward, strike, t, r, s, right) - price,
                IV_LO, IV_HI)
    if iv is None or not math.isfinite(iv):
        return None, "no_bracket"
    return iv, None


def _quote_age_days(row: dict, as_of: Optional[str]) -> Optional[float]:
    lt = row.get("last_trade_date")
    if not lt or not as_of:
        return None
    try:
        a = dt.datetime.fromisoformat(str(lt))
        b = dt.datetime.fromisoformat(str(as_of))
        if a.tzinfo is None:
            a = a.replace(tzinfo=dt.timezone.utc)
        if b.tzinfo is None:
            b = b.replace(tzinfo=dt.timezone.utc)
        return (b - a).total_seconds() / 86400.0
    except Exception:  # noqa: BLE001
        return None


def solve_chain(rows: list[dict], r: float,
                max_rel_spread: float = MAX_REL_SPREAD,
                max_quote_age_days: float = MAX_QUOTE_AGE_DAYS,
                as_of: Optional[str] = None) -> dict:
    """Solve IV for a whole chain, OTM side only, expiry by expiry.

    Returns {"rows": [...], "expiries": {...}, "quality": {...}}. Every input
    row comes back; rejected ones carry solved_iv=None and a reject reason, so
    the caller can count rejections rather than infer them from a shorter list.
    """
    by_expiry: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_expiry[row.get("expiry")].append(row)

    out_rows: list[dict] = []
    expiries: dict[str, dict] = {}
    counts: dict[str, int] = defaultdict(int)

    for expiry, erows in by_expiry.items():
        dte = max(erows[0].get("dte") or 0, 0)
        t = max(dte / 365.0, 1.0 / (365.0 * 24.0))
        fwd_info = implied_forward(erows, t, r)

        if fwd_info is None:
            for row in erows:
                counts["no_forward"] += 1
                out_rows.append({**row, "solved_iv": None, "iv_source": IV_SOURCE,
                                 "iv_reject": "no_forward", "forward": None})
            expiries[expiry] = {"dte": dte, "forward": None,
                                "reason": "no two-sided strike for parity"}
            continue

        fwd = fwd_info["forward"]
        solved = 0
        for row in erows:
            k, right = row.get("strike"), row.get("right")
            rec = {**row, "solved_iv": None, "iv_source": IV_SOURCE,
                   "iv_reject": None, "forward": fwd}

            # OTM side only: puts below the forward, calls above.
            if not k or right not in ("C", "P"):
                rec["iv_reject"] = "no_quote"
            elif (right == "P" and k >= fwd) or (right == "C" and k <= fwd):
                rec["iv_reject"] = "itm_skipped"
            else:
                spread = rel_spread(row.get("bid"), row.get("ask"))
                age = _quote_age_days(row, as_of or row.get("fetched_at"))
                if spread is not None and spread > max_rel_spread:
                    rec["iv_reject"] = "wide_spread"
                elif age is not None and age > max_quote_age_days:
                    rec["iv_reject"] = "stale_quote"
                else:
                    px = mid_price(row.get("bid"), row.get("ask"),
                                   row.get("last_price"))
                    iv, why = solve_one(px, fwd, k, t, r, right)
                    rec["solved_iv"], rec["iv_reject"] = iv, why
                    if iv is not None:
                        solved += 1
                rec["rel_spread"] = spread
                rec["quote_age_days"] = age

            counts[rec["iv_reject"] or "solved"] += 1
            out_rows.append(rec)

        expiries[expiry] = {"dte": dte, "forward": round(fwd, 4),
                            "atm_strike": fwd_info["atm_strike"],
                            "parity_abs_diff": fwd_info["parity_abs_diff"],
                            "solved": solved, "rows": len(erows)}

    # --- propagate each strike's vol to its ITM twin ----------------------
    # Vol is a property of (expiry, strike), not of call-vs-put: by put-call
    # parity both legs at a strike carry the same implied vol. Solving only the
    # OTM wing is right for *reading* vol, but GEX needs gamma for every
    # contract that has open interest, ITM included. Leaving the ITM legs unset
    # deletes them from the profile, which removes the offsetting side below
    # and above the forward and inflates dollar gamma several-fold -- exactly
    # what the validation gate caught on its first run.
    otm_iv: dict[tuple, float] = {}
    for rec in out_rows:
        if rec.get("solved_iv") is not None:
            otm_iv[(rec.get("expiry"), rec.get("strike"))] = rec["solved_iv"]
    twinned = 0
    for rec in out_rows:
        if rec.get("solved_iv") is None and rec.get("iv_reject") == "itm_skipped":
            iv = otm_iv.get((rec.get("expiry"), rec.get("strike")))
            if iv is not None:
                rec["solved_iv"] = iv
                rec["iv_from_twin"] = True
                rec["iv_reject"] = None
                twinned += 1
    counts["itm_skipped"] -= twinned
    counts["solved_from_twin"] = twinned

    total = len(out_rows)
    solved_n = counts.get("solved", 0) + counts.get("solved_from_twin", 0)
    # ITM rows are skipped by design, so a solve rate over the eligible OTM
    # wing is the honest denominator; the raw rate is kept beside it.
    eligible = total - counts.get("itm_skipped", 0)
    return {
        "rows": out_rows,
        "expiries": expiries,
        "quality": {
            "iv_source": IV_SOURCE,
            "rows_in": total,
            "solved": solved_n,
            "solved_direct": counts.get("solved", 0),
            "solved_from_twin": counts.get("solved_from_twin", 0),
            "solve_rate_of_eligible": round(solved_n / eligible, 4) if eligible else None,
            "solve_rate_of_all": round(solved_n / total, 4) if total else None,
            "rejects": {k: v for k, v in sorted(counts.items()) if k != "solved"},
            "max_rel_spread": max_rel_spread,
            "max_quote_age_days": max_quote_age_days,
            "iv_bounds": [IV_LO, IV_HI],
        },
    }
