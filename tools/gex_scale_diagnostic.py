"""
GEX / DEX scale diagnostic -- READ ONLY. Recomputes a stored chain's dealer gamma
and delta exposure step by step, by expiry window and under the definitions other
vendors use, so a gap against an outside number can be classified as a coverage
difference, a definition difference or a units fault.

    python tools/gex_scale_diagnostic.py data/chains/2026-09-30/SPY_201420Z.csv
    python tools/gex_scale_diagnostic.py CHAIN.csv --vendor-gex -1.0e9 --vendor-dex 33.7e9

Writes nothing. It calls exposure_compute's own loader and Black-Scholes and
first REPRODUCES what compute_symbol printed, so every other row of its table is
the same arithmetic over a different subset or definition.

THE FORMULAS, as implemented in tools/exposure_compute.py (_profile):
    per row        notional  = gamma x OI x 100 x S          (net_gex sums sign x this)
    shares / 1%    = net_gex x 0.01      = sum(sign x gamma x OI x 100 x S x 0.01)
    $ / 1%         = shares / 1% x S     = sum(sign x gamma x OI x 100 x S^2 x 0.01)
    DEX shares     = sum(sign x delta x OI x 100);  DEX $ = DEX shares x S
    sign           = +1 call, -1 put (dealers long calls, short puts)
The 100 is CONTRACT_MULTIPLIER, applied once; S appears twice in $/1% by
definition (once in the delta change per 1%, once to turn shares into dollars).

FlashAlpha documents its GEX as sum(sign x gamma x OI x 100 x S) and labels it
"per 1% move" (flashalpha.com/concepts/gex). That is this repo's `net_gex` --
the per-1% dollar figure divided by S x 0.01. The two are the same book in
different units; compare like with like.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import exposure_compute as ec   # noqa: E402
from altdata import config      # noqa: E402

CUTS = (0, 1, 2, 7, 14, 21, 30, 45, 60, 90, 9999)


def greeks_rows(rows: list[dict], spot: float) -> list[dict]:
    """The rows compute_symbol would use, with BS gamma and delta, before the
    settled-0DTE exclusion (applied per subset below)."""
    out = []
    for r in rows:
        oi, iv = r.get("open_interest") or 0.0, r.get("implied_vol")
        if oi <= 0 or iv is None or not (0 < iv < ec.MAX_SANE_IV):
            continue
        t = max(r.get("dte") or 0, 0) / ec.DAYS_PER_YEAR
        g = ec.bs_greeks(spot, r["strike"], iv, t, config.RISK_FREE_RATE, r["right"])
        out.append({**r, "gamma": g["gamma"], "delta": g["delta"]})
    return out


def gamma_units(u: list[dict], spot: float) -> dict:
    sh_pt = sum(ec.dealer_position(r["right"]) * r["gamma"] * r["open_interest"]
                * ec.CONTRACT_MULTIPLIER for r in u)
    return {"shares_per_pt": sh_pt, "usd_per_pt_flashalpha": sh_pt * spot,
            "shares_per_1pct": sh_pt * spot * 0.01,
            "usd_per_1pct": sh_pt * spot * spot * 0.01}


def dex_usd(u: list[dict], spot: float, convention: str = "dealer") -> float:
    def d(r):
        if convention == "dealer":
            return ec.dealer_position(r["right"]) * r["delta"]
        if convention == "raw":
            return r["delta"]
        return r["delta"] if r["right"] == "C" else 0.0
    return sum(d(r) * r["open_interest"] * ec.CONTRACT_MULTIPLIER for r in u) * spot


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("chain", type=Path)
    ap.add_argument("--vendor-gex", type=float, default=None,
                    help="the outside $/1%% figure, for the ratio line")
    ap.add_argument("--vendor-dex", type=float, default=None)
    a = ap.parse_args(argv)

    rows = ec.load_chain(a.chain)
    spot = next(r["spot"] for r in rows if r.get("spot"))
    full = ec.compute_symbol(rows, rows[0]["symbol"])
    ov = full["overall"]
    settled = ec.is_settled_capture(rows[0]["fetched_at"])
    keys = [(r["expiry"], r["right"], r["strike"]) for r in rows]
    print(f"{a.chain.name}: {len(rows)} rows, spot {spot:.2f}, fetched "
          f"{rows[0]['fetched_at']}, settled capture {settled}")
    print(f"duplicate (expiry, right, strike) rows: {len(keys) - len(set(keys))}; "
          f"total OI {sum(r['open_interest'] or 0 for r in rows):,.0f}; "
          f"CONTRACT_MULTIPLIER {ec.CONTRACT_MULTIPLIER:g}")
    print(f"\nREPRODUCED by compute_symbol: $/1% {ov['dollar_gamma_per_1pct']:,.0f}  "
          f"shares/1% {ov['shares_per_1pct']:,.0f}  net_gex {ov['net_gex']:,.0f}  "
          f"DEX $ {ov['dex_notional']:,.0f}")

    u = greeks_rows(rows, spot)
    print(f"\n{'subset':<28}{'$/1% (ours)':>16}{'shares/1%':>14}"
          f"{'S.G.OI.100 (FA)':>18}{'DEX $':>18}")
    for lab, p in (("all expiries", lambda r: True),
                   ("all, 0DTE excluded", lambda r: r["dte"] > 0),
                   ("<= 45 DTE", lambda r: r["dte"] <= 45),
                   ("<= 7 DTE", lambda r: r["dte"] <= 7),
                   ("0DTE only (t floored)", lambda r: r["dte"] == 0)):
        s = [r for r in u if p(r)]
        g = gamma_units(s, spot)
        print(f"{lab:<28}{g['usd_per_1pct']:>16,.0f}{g['shares_per_1pct']:>14,.0f}"
              f"{g['usd_per_pt_flashalpha']:>18,.0f}{dex_usd(s, spot):>18,.0f}")
    print(f"\nDEX $bn, cumulative by DTE cutoff:")
    print(f"  {'convention':<14}" + "".join(
        f"{('<=' + str(c)) if c < 9999 else 'all':>8}" for c in CUTS))
    for conv in ("dealer", "raw", "calls"):
        print(f"  {conv:<14}" + "".join(
            f"{dex_usd([r for r in u if r['dte'] <= c], spot, conv) / 1e9:>8.1f}"
            for c in CUTS))
    if a.vendor_gex:
        print(f"\nvendor $/1% {a.vendor_gex:,.0f}: ours / vendor = "
              f"{ov['dollar_gamma_per_1pct'] / a.vendor_gex:.2f}x; "
              f"S x 0.01 = {spot * 0.01:.2f}x; net_gex / vendor = "
              f"{ov['net_gex'] / a.vendor_gex:.2f}x")
    if a.vendor_dex:
        print(f"vendor DEX {a.vendor_dex:,.0f}: ours / vendor = "
              f"{ov['dex_notional'] / a.vendor_dex:.2f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
