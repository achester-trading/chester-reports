#!/usr/bin/env python3
"""
The one-strike reconciliation of the vendor's GEX against ours -- F-3, the first
entry of docs/ledgers/vendor-divergence-notes.md (ruled 18 Oct 2026; a43-render).

    python tools/vendor_reconcile.py                       # the fixture: vendor side
    python tools/vendor_reconcile.py --chain PATH          # the box: ours from the
                                                           # 16 Oct capture's CSV

THE GAP. On 16 Oct the vendor printed SPY net GEX -6.61bn and net DEX -52.2bn where
we printed -1.41bn per 1% and +209.94bn. The 9 Oct ledger established that the
two GEX definitions are the same sum (dealer position x gamma x OI x 100 x S^2 x
0.01, calls +, puts -), so a factor of four to five has to come from the inputs:
the OI set, gamma, the multiplier, the spot term, or the expiries covered.

THE STRIKE. SPY 770, the 23 Oct expiry, from the vendor's single-expiry GEX (its
per-strike call and put OI are in the response; tests/fixtures/dealer_block/
flashalpha_gex_SPY_exp2026-10-23_770.json). Backing gamma out of each leg under
their own convention shows what their IV did: a call and a put at one strike and
expiry have ONE Black-Scholes gamma at one IV, so two different implied gammas are
two different IVs. The box run sets our capture's gamma (from its IV) beside them.

Reads no store, calls no vendor, fetches nothing.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "tests" / "fixtures" / "dealer_block" / "flashalpha_gex_SPY_exp2026-10-23_770.json"
STRIKE, EXPIRY = 770.0, "2026-10-23"
# The vendor's response is as of 18 Oct (the 16 Oct settlement's OI): five calendar
# days to the 23 Oct expiry.
T_YEARS = 5 / 365.0


def unit(spot: float) -> float:
    """One contract's GEX per unit gamma: 100 x S^2 x 0.01."""
    return 100.0 * spot * spot * 0.01


def implied_gamma(gex: float, oi: float, spot: float) -> Optional[float]:
    return abs(gex) / (oi * unit(spot)) if oi and gex else None


def bs_gamma(spot: float, strike: float, iv: float, t: float = T_YEARS) -> float:
    s = iv * math.sqrt(t)
    d1 = (math.log(spot / strike) + 0.5 * s * s) / s
    return math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi) / (spot * s)


def iv_for_gamma(target: float, spot: float, strike: float, t: float = T_YEARS,
                 lo: float = 0.01, hi: float = 3.0) -> tuple[Optional[float], Optional[float]]:
    """(the low-IV root, the high-IV root) of bs_gamma = target. Gamma away from
    the money rises with IV to a peak and then falls, so a target under the peak
    has two IVs; one over it has none (returned as the peak's IV, flagged by the
    caller)."""
    grid = [lo + (hi - lo) * i / 3000 for i in range(3001)]
    g = [bs_gamma(spot, strike, v, t) for v in grid]
    k = max(range(len(g)), key=g.__getitem__)

    def root(a, b, rising):
        for _ in range(80):
            m = (a + b) / 2
            if (bs_gamma(spot, strike, m, t) < target) == rising:
                a = m
            else:
                b = m
        return (a + b) / 2
    if target > g[k]:
        return grid[k], None
    low = root(grid[0], grid[k], True) if g[0] < target else None
    high = root(grid[k], grid[-1], False) if g[-1] < target else None
    return low, high


def strike_reconciliation(row: dict, spot: float, our_iv: Optional[float] = None,
                          our_call_oi: Optional[float] = None,
                          our_put_oi: Optional[float] = None) -> dict:
    gc = implied_gamma(row["call_gex"], row["call_oi"], spot)
    gp = implied_gamma(row["put_gex"], row["put_oi"], spot)
    peak_iv, _ = iv_for_gamma(10.0, spot, row["strike"])           # gamma's peak
    out = {"strike": row["strike"], "spot": spot, "call_oi": row["call_oi"],
           "put_oi": row["put_oi"], "vendor_call_gex": row["call_gex"],
           "vendor_put_gex": row["put_gex"], "vendor_net_gex": row["net_gex"],
           "vendor_call_gamma": gc, "vendor_put_gamma": gp,
           "gamma_ratio_put_over_call": gp / gc if gc and gp else None,
           "gamma_peak": bs_gamma(spot, row["strike"], peak_iv), "gamma_peak_iv": peak_iv,
           "vendor_call_iv_roots": iv_for_gamma(gc, spot, row["strike"]),
           "vendor_put_iv_roots": iv_for_gamma(gp, spot, row["strike"])}
    if our_iv is not None:
        g = bs_gamma(spot, row["strike"], our_iv)
        co = row["call_oi"] if our_call_oi is None else our_call_oi
        po = row["put_oi"] if our_put_oi is None else our_put_oi
        out.update(our_iv=our_iv, our_gamma=g,
                   one_iv_call_gex=g * co * unit(spot), one_iv_put_gex=-g * po * unit(spot),
                   one_iv_net_gex=g * (co - po) * unit(spot))
    return out


def ours_from_chain(path: Path, expiry: str = EXPIRY, strike: float = STRIKE) -> dict:
    """Our capture's OI, IV and gamma for the strike, both legs (the box run)."""
    out = {}
    with path.open(encoding="utf-8") as fp:
        for r in csv.DictReader(fp):
            if str(r.get("expiry"))[:10] == expiry and abs(float(r.get("strike") or 0) - strike) < 1e-6:
                side = "call" if str(r.get("option_type") or r.get("type") or "").lower().startswith("c") else "put"
                out[side] = {k: r.get(k) for k in ("open_interest", "implied_vol", "gamma", "spot")}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="F-3's one-strike reconciliation")
    ap.add_argument("--chain", help="our 16 Oct SPY capture's CSV (data/chains/2026-10-16/)")
    a = ap.parse_args(argv)
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    row = next(r for r in fx["strikes"] if r["strike"] == STRIKE)
    ours = ours_from_chain(Path(a.chain)) if a.chain else {}
    iv = None
    if ours.get("call", {}).get("implied_vol"):
        iv = float(ours["call"]["implied_vol"])
    r = strike_reconciliation(row, fx["underlying_price"], iv)
    print(json.dumps({"vendor": r, "ours_from_capture": ours or "not read (laptop: the "
                      "box run passes --chain)"}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
