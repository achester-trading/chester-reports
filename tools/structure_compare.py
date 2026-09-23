#!/usr/bin/env python3
"""
Chapter 15's scenario matrix, priced on LIVE implied volatility. (Paste D piece 6)

    python tools/structure_compare.py atm-vol                 # what the chains say
    python tools/structure_compare.py compare --symbol SPY
    python tools/structure_compare.py weekly                   # write the observation
    python tools/structure_compare.py weekly --dry-run

-----------------------------------------------------------------------------
WHAT THIS REPLACES, AND WHY THE ASSUMED SIGMA HAD TO GO
-----------------------------------------------------------------------------

The previous version of this file was the script that produced the paper's
Chapter 15 tables. It carried four ASSUMED volatilities -- 16% for US equity, 28%
for China, 20% for real estate, 60% for crypto -- and it imported an `svglib` that
does not exist in this repository, so it could not be run at all.

Those assumptions were right for a paper: Chapter 15 says its inputs are given so
that a reader can disagree with them rather than with the arithmetic, and a fixed
sigma makes the four asset classes comparable. They are wrong for a live
comparison, and wrongly in a direction that matters. The whole finding of Chapter
15 -- that most structures lose to a 50/50 index-and-bills mix on expected value
-- turns on the price of the options, and the price of the options is the
volatility. At 16% the collar is nearly free; at 40% the same collar's call strike
sits far enough out that it is a different trade. Deciding today with last year's
sigma is deciding about a structure nobody can buy.

So the sigma comes from the exposure engine's stored chain snapshots: the ATM
implied volatility at the tenor being priced, per symbol, as of the session the
snapshot describes.

-----------------------------------------------------------------------------
AND WHERE THERE IS NO CHAIN, THERE IS NO NUMBER
-----------------------------------------------------------------------------

The capture universe is thirteen symbols with Greeks -- SPY, QQQ, IWM and ten
single names -- plus two stored pending the solver gate. It contains no China ETF,
no REIT index and no crypto fund. The paper's other three asset classes therefore
report `not_yet_sourced` with the symbol that would have to enter the capture
universe first, and they do NOT report a comparison computed from the paper's
assumed sigma.

That refusal is the piece. A structure comparison for an asset whose volatility
was guessed looks exactly like one whose volatility was measured, arrives with the
same decimal places, and is the kind of number that gets acted on. The paper's
assumption is legitimate as a paper's assumption and illegitimate as this
system's input, and the difference between those two is a label nobody can see
once the table is rendered.

-----------------------------------------------------------------------------
WHAT THE OBSERVATION IS FOR
-----------------------------------------------------------------------------

One `structure.compare.<symbol>` observation per week, holding the whole matrix as
JSON: the structures, the scenario grid, the expected value, the probability of
finishing below capital, and the ATM vol each tenor was priced on. The Sunday
anchor reads it WHEN IT EXISTS -- 6b builds that anchor and this does not assume
it. Weekly rather than nightly because the comparison is a monthly-session
question and a nightly recompute would be 250 rows a year of a table nobody read.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from altdata import observations, session                      # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KEY_PREFIX = "structure.compare."
SOURCE = "derived_state"

# THE TENORS PRICED. Chapter 15 does twelve and six months; the chains rarely
# carry a clean two-year expiry, and a tenor interpolated from a six-month vol
# would be the assumed sigma wearing a different hat.
TENORS = ((1.0, "12m"), (0.5, "6m"))

# The risk-free rate and the scenario grid are the paper's, unchanged: they are
# stated inputs rather than measurements, and changing them would make the live
# table incomparable with the paper's.
RISK_FREE = 0.04
SCENARIOS = (-0.30, -0.20, -0.10, -0.05, 0.0, 0.05, 0.10, 0.15, 0.20, 0.30)
CAPITAL = 100.0

# HOW FAR THE TWO NEAREST-THE-MONEY SOLVED CONTRACTS MAY DISAGREE. Five vol
# points. Below it the disagreement is skew across two adjacent strikes, which is
# real and small; above it the quotes are not describing one volatility and no
# average of them is. Declared rather than tuned per run, because a tolerance
# chosen after seeing the answer is not a tolerance.
MAX_SOLVED_GAP = 0.05

# Dividend yields, per symbol, as declared inputs. NOT measured: the chains carry
# no dividend series and the store's dividend observations are per-event rather
# than a yield. Declared here so the number is visible and arguable, which is what
# Chapter 15 asks of its own inputs.
DIVIDEND_YIELD = {"SPY": 0.013, "QQQ": 0.006, "IWM": 0.013}

# THE KEYS, at module level so the registry can point a bulk block at them. A
# function would not do: the resolver iterates the attribute it is given, and a
# function object iterates to nothing -- which would register the keys silently as
# zero members.
REGISTRY_KEYS: tuple[str, ...] = ()          # filled below, after DIVIDEND_YIELD

# ONCE A WEEK, MEASURED IN DAYS SINCE THE LAST ROW rather than by weekday. A
# weekday test fires twice if the pass runs twice and never if the box is down on
# the chosen day; "older than seven days" is the property actually wanted, and it
# self-heals after an outage.
WEEKLY_DAYS = 7

# The drift used for the expected-value column, from the paper. An assumption by
# construction -- no expected return is measurable from a chain -- and the field
# `drift_assumed` carries it onto every row so it cannot be read as a measurement.
DRIFT = 0.08

REGISTRY_KEYS = tuple(f"{KEY_PREFIX}{s.lower()}" for s in sorted(DIVIDEND_YIELD))

# What the paper covers and this system cannot price, with the symbol that would
# have to enter the capture universe first. Declared rather than silently absent.
NOT_SOURCED = {
    "China": {"would_need": ["MCHI", "FXI"],
              "paper_sigma": 0.28,
              "reason": "no China ETF is in the chain-capture universe, so there "
                        "is no measured implied volatility to price with"},
    "Real estate": {"would_need": ["VNQ"],
                    "paper_sigma": 0.20,
                    "reason": "no REIT index fund is in the capture universe"},
    "Crypto": {"would_need": ["IBIT", "BITO"],
               "paper_sigma": 0.60,
               "reason": "no crypto fund is in the capture universe; MSTR and "
                         "COIN are captured and are single names with their own "
                         "idiosyncratic vol, not a proxy for the asset class"},
}


# ---------------------------------------------------------------------------
# Black-Scholes, with a continuous dividend yield
# ---------------------------------------------------------------------------
def _N(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs(S: float, K: float, T: float, r: float, q: float, sig: float,
       call: bool = True) -> float:
    if T <= 0 or sig <= 0:
        return max(S - K, 0.0) if call else max(K - S, 0.0)
    d1 = (math.log(S / K) + (r - q + 0.5 * sig * sig) * T) / (sig * math.sqrt(T))
    d2 = d1 - sig * math.sqrt(T)
    if call:
        return S * math.exp(-q * T) * _N(d1) - K * math.exp(-r * T) * _N(d2)
    return K * math.exp(-r * T) * _N(-d2) - S * math.exp(-q * T) * _N(-d1)


def solve_call_strike(S: float, T: float, r: float, q: float, sig: float,
                      target: float) -> float:
    """The strike whose call premium equals `target`. Bisection, 80 steps."""
    lo, hi = S, S * 3.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if bs(S, mid, T, r, q, sig, True) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ---------------------------------------------------------------------------
# The live input: ATM implied volatility per tenor, from the stored chains
# ---------------------------------------------------------------------------
def atm_vol(symbol: str, target_years: float, date: Optional[str] = None,
            snapshot: Optional[list[dict]] = None) -> dict:
    """The ATM implied volatility nearest a tenor, from a chain snapshot.

    THE VENDOR'S OWN IVs ARE NOT AVERAGED, AND THE FIRST RUN SHOWED WHY. At SPY's
    770 strike, 378 days out, the vendor served 22.59% on the call and 13.44% on
    the put -- a nine-point gap at ONE strike, where put-call parity says there
    should be none. The mean of those two is 18%, which is neither of them, and
    Chapter 15's whole finding turns on the price of the options: a collar is
    nearly free at 16% and a different trade at 40%. Averaging a disagreement that
    size would produce a table whose conclusions could flip.

    The gap is not information. It is what inverting an ITM price gives you: a deep
    in-the-money option is almost all intrinsic, its vega is tiny, and the
    inversion amplifies a wide quote into an enormous vol error. tools/iv_solver.py
    exists for exactly this and is already gated for SPY -- implied forward per
    expiry from parity, Black-76 on the forward, OTM SIDE ONLY -- so the ATM vol
    here is SOLVED from the two nearest-the-money OTM contracts rather than read
    off the vendor's ITM side.

    Both numbers are reported. `atm_iv` is the solved one and is what prices the
    structures; `vendor_legs` carries what the vendor said and `vendor_leg_gap` how
    far apart its legs were, because a widening gap is a chain-quality signal and
    hiding it would remove the evidence that this path was necessary.

    TWO NEAREST DISTINCT STRIKES, NOT TWO NEAREST CONTRACTS. The solver propagates
    each strike's OTM vol to its ITM twin, because vol belongs to (expiry, strike)
    rather than to call-versus-put and the twin needs a gamma -- so the call and the
    put at one strike are identical by construction. Reading "the two nearest
    contracts" therefore read one strike twice and produced a gap of exactly zero,
    which made the tolerance below unfireable. Adjacent strikes differ by the
    smile's slope, which is the disagreement worth measuring.

    AND IF THEY DISAGREE BY MORE THAN MAX_SOLVED_GAP THE TENOR IS NOT PRICED. The
    solver removes the ITM-inversion problem; it cannot repair a broken quote, and
    at that point the honest answer is no table rather than a table.

    THE EXPIRY IS THE NEAREST AVAILABLE, NOT THE ONE ASKED FOR, and the row says
    which. A twelve-month tenor priced from a nine-month expiry is a different
    number, and interpolating to the requested date would be inventing a
    volatility the chain does not carry.
    """
    import exposure_compute as ec                              # noqa: PLC0415
    out: dict[str, Any] = {"symbol": symbol, "target_years": target_years}
    rows = snapshot
    if rows is None:
        chains = ec.newest_chains(date, [symbol])
        if symbol not in chains:
            out["state"] = "not_yet_sourced"
            out["reason"] = (f"no stored chain snapshot for {symbol}"
                             + (f" on {date}" if date else ""))
            return out
        out["snapshot"] = str(chains[symbol].name)
        rows = ec.load_chain(chains[symbol])
    if not rows:
        out["state"] = "no_rows"
        out["reason"] = "the snapshot parsed to zero rows"
        return out
    spot = next((r["spot"] for r in rows if r.get("spot")), None)
    if not spot:
        out["state"] = "no_spot"
        out["reason"] = "the snapshot carries no spot, so ATM is undefined"
        return out
    out["spot"] = spot
    target_dte = target_years * 365.0
    usable = [r for r in rows
              if r.get("implied_vol") and r["implied_vol"] > 0
              and r.get("strike") and r.get("dte") is not None]
    if not usable:
        out["state"] = "no_iv"
        out["reason"] = ("the snapshot carries no positive implied volatility -- "
                         "an unsolved chain, or a vendor gate")
        return out
    dtes = sorted({int(r["dte"]) for r in usable})
    dte = min(dtes, key=lambda d: abs(d - target_dte))
    at_tenor = [r for r in rows if r.get("dte") is not None
                and int(r["dte"]) == dte]
    strikes = sorted({r["strike"] for r in at_tenor if r.get("strike")})
    k = min(strikes, key=lambda s: abs(s - spot))
    vendor_legs = {str(r.get("right") or "?").upper(): r.get("implied_vol")
                   for r in at_tenor if r.get("strike") == k}
    vendor_gap = None
    vals = [v for v in vendor_legs.values() if v]
    if len(vals) > 1:
        vendor_gap = round(max(vals) - min(vals), 6)

    # SOLVED, NOT AVERAGED -- see the docstring. The solver needs the whole
    # expiry, because the forward comes from parity across strikes.
    import iv_solver                                           # noqa: PLC0415
    solved = iv_solver.solve_chain(at_tenor, RISK_FREE,
                                   as_of=rows[0].get("fetched_at"))
    fwd = ((solved.get("expiries") or {}).get(at_tenor[0].get("expiry"))
           or {}).get("forward")
    ok_rows = [r for r in solved["rows"] if r.get("solved_iv")]
    if not ok_rows:
        out["state"] = "not_solvable"
        out["reason"] = (f"no contract at {dte}d solved: "
                         f"{(solved.get('quality') or {})}")
        out["vendor_legs"] = vendor_legs
        return out
    # THE TWO NEAREST DISTINCT STRIKES, and "distinct" is the load-bearing word.
    # The solver propagates each strike's OTM vol to its ITM twin -- vol is a
    # property of (expiry, strike) and not of call-versus-put, and the twin needs a
    # gamma. So the call and the put at ONE strike come back identical by
    # construction, and taking "the two nearest contracts" took the same strike
    # twice: a gap of exactly zero, and a MAX_SOLVED_GAP check that could never
    # fire. A check that cannot fail is worse than no check, because it reads as
    # one.
    #
    # Two adjacent STRIKES do differ, by the smile's slope across them, and that is
    # the disagreement worth measuring: at SPY's 378-day expiry, 795 solves to
    # 0.16898 and 800 to 0.16694, a fifth of a point.
    anchor = fwd or spot
    by_strike: dict[float, float] = {}
    for r in ok_rows:
        by_strike.setdefault(float(r["strike"]), float(r["solved_iv"]))
    near_k = sorted(by_strike, key=lambda x: abs(x - anchor))[:2]
    pair = {f"{k:g}": round(by_strike[k], 6) for k in near_k}
    vol = sum(by_strike[k] for k in near_k) / len(near_k)
    gap = (round(max(pair.values()) - min(pair.values()), 6)
           if len(pair) > 1 else 0.0)
    near = [r for r in ok_rows if float(r["strike"]) in set(near_k)]
    out.update({
        "atm_iv": round(vol, 6),
        "atm_strike": k,
        "solved_by_strike": pair,
        "solved_strikes": near_k,
        "solved_gap": gap,
        "forward": round(fwd, 4) if fwd else None,
        "moneyness": round(k / spot, 6),
        "dte": dte,
        "years": round(dte / 365.0, 4),
        "expiry": near[0].get("expiry"),
        "vendor_legs": {kk: (round(vv, 6) if vv else None)
                        for kk, vv in sorted(vendor_legs.items())},
        "vendor_leg_gap": vendor_gap,
        "iv_source": iv_solver.IV_SOURCE,
        "solved_of": f"{len(ok_rows)} of {len(at_tenor)} contracts at this expiry",
        "dte_requested": round(target_dte),
        "dte_note": ("the NEAREST available expiry, not the requested tenor -- "
                     "interpolating would invent a volatility the chain does not "
                     "carry"),
        "tenors_available": dtes[:12],
    })
    if gap > MAX_SOLVED_GAP:
        out["state"] = "solved_legs_disagree"
        out["reason"] = (
            f"the two nearest-the-money solved contracts disagree by "
            f"{gap:.4f} against a declared maximum of {MAX_SOLVED_GAP} -- the "
            f"solver removes the ITM-inversion problem but cannot repair a broken "
            f"quote, and a structure comparison priced on a volatility this "
            f"uncertain would carry conclusions that flip inside the uncertainty")
    else:
        out["state"] = "available"
    return out


# ---------------------------------------------------------------------------
# The structures, on whatever sigma it was handed
# ---------------------------------------------------------------------------
def structures(T: float, sig: float, q: float) -> tuple[dict, dict]:
    """Chapter 15's ten structures at $100 of capital. Payoff functions of spot."""
    S = CAPITAL
    r = RISK_FREE
    div = q * T * S
    rf = (1.0 + r) ** T - 1.0

    def P(K, s):
        return max(K - s, 0.0)

    def C(K, s):
        return max(s - K, 0.0)

    p95 = bs(S, 95, T, r, q, sig, False)
    p90 = bs(S, 90, T, r, q, sig, False)
    p85 = bs(S, 85, T, r, q, sig, False)
    p100 = bs(S, 100, T, r, q, sig, False)
    c100 = bs(S, 100, T, r, q, sig, True)
    c105 = bs(S, 105, T, r, q, sig, True)
    c110 = bs(S, 110, T, r, q, sig, True)
    k_collar = solve_call_strike(S, T, r, q, sig, p90)
    k_psc = solve_call_strike(S, T, r, q, sig, p95 - p85)
    k_buf = solve_call_strike(S, T, r, q, sig, p100 - p90)
    pv = S / (1.0 + r) ** T
    part_ppn = (S - pv) / c100 if c100 > 0 else 0.0
    rib_cost = (c100 + p100) - (c110 + p90)
    part_rib = (S - pv) / rib_cost if rib_cost > 0 else 0.0

    st = {
        "hold_the_index": lambda s: s + div,
        "bills": lambda s: S * (1.0 + rf),
        "half_index_half_bills": lambda s: 0.5 * (s + div) + 0.5 * S * (1.0 + rf),
        "protective_put_95": lambda s: s + div + P(95, s) - p95,
        "zero_cost_collar_90": lambda s: s + div + P(90, s) - C(k_collar, s),
        "put_spread_collar_95_85": lambda s: (s + div + P(95, s) - P(85, s)
                                             - C(k_psc, s)),
        "covered_call_105": lambda s: s + div - C(105, s) + c105,
        "buffered_10": lambda s: (S + min(C(100, s), k_buf - 100) if s >= 90
                                  else S - (90 - s)),
        "synthetic_ppn": lambda s: S + part_ppn * C(100, s),
        "bills_plus_reverse_iron_butterfly": lambda s: (
            S + part_rib * (min(C(100, s), 10) + min(P(100, s), 10))),
    }
    meta = {"p95": round(p95, 4), "p90": round(p90, 4), "p100": round(p100, 4),
            "c100": round(c100, 4), "c105": round(c105, 4),
            "collar_call_strike": round(k_collar, 2),
            "put_spread_collar_call_strike": round(k_psc, 2),
            "buffered_cap_strike": round(k_buf, 2),
            "ppn_participation": round(part_ppn, 4),
            "rib_cost": round(rib_cost, 4),
            "rib_participation": round(part_rib, 4),
            "dividend_cash": round(div, 4),
            "bill_return": round(rf, 4)}
    return st, meta


def _erfinv(y: float) -> float:
    a = 0.147
    ln = math.log(max(1e-15, 1 - y * y))
    t = 2 / (math.pi * a) + ln / 2
    return math.copysign(math.sqrt(max(0.0, math.sqrt(t * t - ln / a) - t)), y)


def expected(fn, T: float, sig: float, q: float, n: int = 4000) -> tuple:
    """Expected payoff and P(below capital) under a lognormal, by quadrature.

    A DETERMINISTIC MIDPOINT GRID rather than a random draw, for the same reason
    base_rates.pctile() is written out: the gate requires a recompute to be
    identical, and a Monte Carlo with a seed is a recompute that is identical until
    somebody changes the seed.
    """
    mu = DRIFT - q
    m = (mu - 0.5 * sig * sig) * T
    sd = sig * math.sqrt(T)
    tot = 0.0
    below = 0
    for i in range(n):
        z = (i + 0.5) / n
        x = math.sqrt(2.0) * _erfinv(2.0 * z - 1.0)
        s = CAPITAL * math.exp(m + sd * x)
        v = fn(s)
        tot += v
        below += 1 if v < CAPITAL else 0
    return tot / n, below / n


def compare(symbol: str = "SPY", date: Optional[str] = None) -> dict:
    """The matrix for one symbol, priced on its own measured ATM vol per tenor."""
    out: dict[str, Any] = {
        "symbol": symbol,
        "capital": CAPITAL,
        "risk_free": RISK_FREE,
        "drift_assumed": DRIFT,
        "dividend_yield_assumed": DIVIDEND_YIELD.get(symbol),
        "scenarios": list(SCENARIOS),
        "inputs_note": ("sigma is MEASURED from the chain; the drift, the "
                        "risk-free rate and the dividend yield are DECLARED "
                        "assumptions and are named on every row so neither can be "
                        "read as the other"),
        "tenors": {},
    }
    q = DIVIDEND_YIELD.get(symbol)
    if q is None:
        out["state"] = "not_yet_sourced"
        out["reason"] = (f"no declared dividend yield for {symbol}; a structure "
                         f"comparison without it flatters every protected "
                         f"structure, because the dividend forgone is the largest "
                         f"hidden cost in most of them")
        return out
    any_priced = False
    for T, label in TENORS:
        vol = atm_vol(symbol, T, date=date)
        row: dict[str, Any] = {"atm_vol": vol}
        if vol.get("state") != "available":
            row["state"] = vol.get("state")
            row["reason"] = vol.get("reason")
            out["tenors"][label] = row
            continue
        sig = float(vol["atm_iv"])
        # THE TENOR PRICED IS THE EXPIRY FOUND, not the label. Using T=1.0 with a
        # nine-month vol would price a year of decay at nine months' volatility.
        t_actual = float(vol["years"])
        st, meta = structures(t_actual, sig, q)
        table = {}
        for name, fn in st.items():
            ev, ploss = expected(fn, t_actual, sig, q)
            table[name] = {
                "scenarios": {f"{int(x * 100):+d}%": round(fn(CAPITAL * (1 + x))
                                                           - CAPITAL, 4)
                              for x in SCENARIOS},
                "expected_pnl": round(ev - CAPITAL, 4),
                "p_below_capital": round(ploss, 4),
            }
        mix = table["half_index_half_bills"]["expected_pnl"]
        beats_mix = sorted(k for k, v in table.items()
                           if v["expected_pnl"] > mix)
        row.update({
            "state": "priced",
            "sigma": round(sig, 6),
            "sigma_source": "measured_atm_iv",
            "years_priced": t_actual,
            "years_requested": T,
            "premiums": meta,
            "structures": table,
            # CHAPTER 15's OWN FINDING, recomputed rather than quoted: the 50/50
            # mix is what every option structure must beat, and most do not.
            "half_and_half_expected_pnl": mix,
            "beats_half_and_half": beats_mix,
            "loses_to_half_and_half": sorted(
                k for k in table if k not in beats_mix
                and k != "half_index_half_bills"),
        })
        any_priced = True
        out["tenors"][label] = row
    out["state"] = "priced" if any_priced else "not_priced"
    out["not_yet_sourced"] = {
        name: dict(spec, state="not_yet_sourced") for name, spec in NOT_SOURCED.items()
    }
    return out


# ---------------------------------------------------------------------------
# The weekly observation
# ---------------------------------------------------------------------------
def stale_symbols(store: observations.ObservationStore,
                  symbols: list[str], days: int = WEEKLY_DAYS) -> list[str]:
    """Which symbols have no observation inside `days`. The weekly guard."""
    import datetime as _dt
    cutoff = (session.last_completed_session()
              - _dt.timedelta(days=days)).isoformat()
    out = []
    for sym in symbols:
        rows = store.as_of(f"{KEY_PREFIX}{sym.lower()}")
        newest = str(rows[-1]["observed_at"])[:10] if rows else None
        if newest is None or newest <= cutoff:
            out.append(sym)
    return out


def weekly(symbols: Optional[list[str]] = None, date: Optional[str] = None,
           dry_run: bool = False, if_stale: bool = False,
           store: Optional[observations.ObservationStore] = None) -> dict:
    """One structure.compare.<symbol> observation per symbol with a chain.

    WRITTEN FOR THE SUNDAY ANCHOR TO READ WHEN IT EXISTS. 6b builds that anchor;
    this does not wait for it and does not assume it. An observation nobody reads
    yet is a week of history; a table computed at read time is a table that cannot
    be replayed.
    """
    own = store is None
    db = store or observations.ObservationStore()
    try:
        syms = symbols or sorted(DIVIDEND_YIELD)
        skipped: list[str] = []
        if if_stale:
            want = stale_symbols(db, syms)
            skipped = [s for s in syms if s not in want]
            syms = want
        day = date or session.last_completed_session().isoformat()
        stamp = session.utc_iso(timespec="microseconds")
        written = 0
        results = {}
        for sym in syms:
            m = compare(sym, date=date)
            m["session"] = day
            m["computed_at"] = stamp
            results[sym] = {"state": m.get("state"),
                            "tenors": {k: v.get("state")
                                       for k, v in (m.get("tenors") or {}).items()},
                            "sigma": {k: v.get("sigma")
                                      for k, v in (m.get("tenors") or {}).items()}}
            if dry_run or m.get("state") != "priced":
                continue
            written += db.write(
                f"{KEY_PREFIX}{sym.lower()}", None, day, stamp,
                json.dumps(m, sort_keys=True), source=SOURCE,
                availability_kind="ingest_instant")
        return {"session": day, "symbols": len(syms), "written": written,
                "dry_run": dry_run, "results": results,
                "skipped_fresh": skipped,
                "weekly_days": WEEKLY_DAYS,
                "not_yet_sourced": sorted(NOT_SOURCED)}
    finally:
        if own:
            db.close()


def keys() -> list[str]:
    return list(REGISTRY_KEYS)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = p.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("atm-vol")
    a1.add_argument("--symbol", default="SPY")
    a1.add_argument("--date", default=None)
    a2 = sub.add_parser("compare")
    a2.add_argument("--symbol", default="SPY")
    a2.add_argument("--date", default=None)
    a2.add_argument("--json", action="store_true")
    a3 = sub.add_parser("weekly")
    a3.add_argument("--date", default=None)
    a3.add_argument("--dry-run", action="store_true")
    a3.add_argument("--if-stale", action="store_true",
                    help="write only the symbols whose newest observation is "
                         "older than a week -- what the overnight pass calls")
    sub.add_parser("keys")
    a = p.parse_args(argv)

    if a.cmd == "keys":
        for k in keys():
            print(k)
        return 0
    if a.cmd == "atm-vol":
        for T, label in TENORS:
            print(f"{label}: "
                  + json.dumps(atm_vol(a.symbol, T, date=a.date), sort_keys=True))
        return 0
    if a.cmd == "weekly":
        print(json.dumps(weekly(date=a.date, dry_run=a.dry_run,
                                if_stale=a.if_stale), indent=2, sort_keys=True))
        return 0

    m = compare(a.symbol, date=a.date)
    if a.json:
        print(json.dumps(m, indent=2, sort_keys=True))
        return 0
    print(f"{m['symbol']}  state={m.get('state')}  "
          f"q={m.get('dividend_yield_assumed')}  drift={m['drift_assumed']} "
          f"(assumed)")
    for label, row in (m.get("tenors") or {}).items():
        if row.get("state") != "priced":
            print(f"\n  {label}: {row.get('state')} -- {row.get('reason')}")
            continue
        print(f"\n  {label}: sigma {row['sigma']:.4f} MEASURED at "
              f"{row['years_priced']:.2f}y (asked {row['years_requested']}y), "
              f"ATM {row['atm_vol']['atm_strike']} of "
              f"{row['atm_vol']['spot']:.2f}")
        print(f"    {'structure':<36}{'EV':>8}{'P(loss)':>9}   -20%    0%   +20%")
        for name, v in row["structures"].items():
            sc = v["scenarios"]
            print(f"    {name:<36}{v['expected_pnl']:>+8.2f}"
                  f"{v['p_below_capital'] * 100:>8.0f}%"
                  f"{sc['-20%']:>+8.1f}{sc['+0%']:>+7.1f}{sc['+20%']:>+7.1f}")
        print(f"    beats the 50/50 mix ({row['half_and_half_expected_pnl']:+.2f}): "
              f"{row['beats_half_and_half']}")
    for name, spec in (m.get("not_yet_sourced") or {}).items():
        print(f"\n  {name}: not_yet_sourced -- {spec['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
