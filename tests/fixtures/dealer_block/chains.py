"""
Synthetic option chains for the dealer block's gates (6b part 1). Nothing here
is a market: every chain is built from declared numbers, so a gate's verdict is
about the commit. Two kinds:

  hand_chain   a few rows carrying VENDOR gamma, so the masses, the net and the
               net-to-gross are hand arithmetic (gamma x OI x 100 x spot, then
               x 0.01 x spot for dollars per 1%).
  bs_chain     a spread of strikes and five expiries (DTE 0, 3, 10, 35, 63) with
               implied vols, so the engine solves every Greek and the horizon
               windows and bands have rows in each.
"""

from __future__ import annotations

SESSION = "2026-10-16"
SETTLED = "2026-10-16T20:10:00+00:00"     # 16:10 ET: a settled capture
AM_0945 = "2026-10-16T13:45:00+00:00"     # 09:45 ET
AM_1100 = "2026-10-16T15:00:00+00:00"     # 11:00 ET: no declared slot
PRIOR_SETTLED = "2026-10-15T20:10:00+00:00"
PRIOR_0945 = "2026-10-15T13:45:00+00:00"

EXPIRIES = (("2026-10-16", 0), ("2026-10-19", 3), ("2026-10-26", 10),
            ("2026-11-20", 35), ("2026-12-18", 63))


def row(right: str, strike: float, oi: float, *, dte: int = 10,
        expiry: str = "2026-10-26", gamma=None, iv=0.20, spot: float = 100.0,
        fetched_at: str = SETTLED, symbol: str = "SPY") -> dict:
    return {"symbol": symbol, "right": right, "strike": float(strike),
            "open_interest": float(oi), "implied_vol": iv, "gamma": gamma,
            "dte": dte, "expiry": expiry, "spot": spot, "fetched_at": fetched_at,
            "volume": 5000.0, "bid": 1.00, "ask": 1.04}


def hand_chain(put_oi: float = 500.0, fetched_at: str = SETTLED) -> list[dict]:
    """Spot 100. Call 105: gamma 0.02, OI 1,000 -> 200,000 notional, $200,000
    per 1%. Put 95: gamma 0.03, OI `put_oi` -> 0.03 x put_oi x 100 x 100."""
    return [row("C", 105, 1000, gamma=0.02, fetched_at=fetched_at),
            row("P", 95, put_oi, gamma=0.03, fetched_at=fetched_at)]


def walls_chain(fetched_at: str = SETTLED) -> list[dict]:
    """Spot 100, vendor gamma. Signed GEX per strike (notional = gamma x OI x
    100 x 100): 90 -50,000 (put); 95 -150,000 (put); 98 +500,000 (an ITM call,
    the all-strike call peak); 102 -400,000 (an ITM put above spot, the
    all-strike put peak); 105 +200,000 (the OTM call wall); 110 +50,000 (the
    secondary call concentration). OTM put gamma wall 95, secondary 90."""
    f = fetched_at
    return [row("P", 90, 500, gamma=0.01, fetched_at=f),
            row("P", 95, 500, gamma=0.03, fetched_at=f),
            row("C", 98, 1000, gamma=0.05, fetched_at=f),
            row("P", 102, 1000, gamma=0.04, fetched_at=f),
            row("C", 105, 1000, gamma=0.02, fetched_at=f),
            row("C", 110, 500, gamma=0.01, fetched_at=f)]


# The same five expiries as seen from Thursday 15 Oct: Friday's is DTE 1.
EXPIRIES_THU = (("2026-10-16", 1), ("2026-10-19", 4), ("2026-10-26", 11),
                ("2026-11-20", 36), ("2026-12-18", 64))


def bs_chain(fetched_at: str = SETTLED, spot: float = 680.0,
             call_oi: float = 4000.0, put_oi: float = 3000.0,
             expiries=EXPIRIES) -> list[dict]:
    """Strikes 640 to 720 by 5 at each of the five expiries, calls heavier
    above spot and puts below, IV with a skew."""
    out = []
    for exp, dte in expiries:
        for k in range(640, 725, 5):
            m = (k - spot) / spot
            iv = max(0.12, 0.18 - 0.4 * m)
            c_oi = call_oi * (1.5 if k > spot else 0.6) * (1.0 + dte / 60.0)
            p_oi = put_oi * (1.5 if k < spot else 0.6) * (1.0 + dte / 60.0)
            out.append(row("C", k, c_oi, dte=dte, expiry=exp, iv=iv, spot=spot,
                           fetched_at=fetched_at))
            out.append(row("P", k, p_oi, dte=dte, expiry=exp, iv=iv, spot=spot,
                           fetched_at=fetched_at))
    return out
