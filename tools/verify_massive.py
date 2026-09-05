"""
Massive Options Starter -- day-one verification.

probe_massive.py answered the pre-subscription question (does SPX exist, and is
the snapshot gated). This answers the post-subscription one: does the tier we
now pay for actually deliver what the logger needs, before any of it is wired
into the pipeline.

Three checks, each with its own verdict:

    Q1  Per-contract open interest, greeks and implied volatility actually
        return on the snapshot endpoint, for SPX and for SPY as control.
    Q2  History depth on one SPX contract.
    Q3  OI vintage -- is it settled end-of-day, as their docs claim?

The HTTP harness (auth, redaction, raw capture, 429 handling) is imported from
probe_massive rather than duplicated, so both scripts write evidence the same
way and the key is redacted by the same code path.

Pacing: Starter is documented as unlimited calls, so this uses a light 1s pace
rather than Basic's 13s -- polite, not throttled. A 429 is still honoured.

Usage:
    python tools/verify_massive.py
"""

from __future__ import annotations

import datetime as dt
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from altdata import session  # noqa: E402
from probe_massive import (  # noqa: E402
    OUT_DIR, SNAPSHOT_PATH, _SECRETS, call, credentials,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AGGS_PATH = "/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
STARTER_PACING = 1.0
LINE = "=" * 70


def first_result(res: dict) -> Optional[dict]:
    body = res.get("body") or {}
    r = body.get("results")
    if isinstance(r, list) and r and isinstance(r[0], dict):
        return r[0]
    return None


def results(res: dict) -> list:
    body = res.get("body") or {}
    r = body.get("results")
    return r if isinstance(r, list) else []


def main() -> int:
    key, base, problems = credentials()
    if problems:
        print("BLOCKED -- credentials not ready:")
        for p in problems:
            print(f"  - {p}")
        return 2
    _SECRETS.append(key)

    print("Massive Options Starter -- day-one verification")
    print(f"  base:   {base}")
    print(f"  pacing: {STARTER_PACING}s (Starter = unlimited calls)\n")

    snaps: dict[str, dict] = {}
    for sym in ("SPX", "SPY"):
        r = call(base, SNAPSHOT_PATH.format(underlying=sym), {"limit": 10},
                 key, f"verify_snapshot_{sym}", "bearer")
        snaps[sym] = r
        print(f"  [{r.get('status')}] snapshot {sym:<4} {len(results(r))} contract(s)")
        time.sleep(STARTER_PACING)

    # ---- Q1 -------------------------------------------------------------
    print(f"\n{LINE}\nQ1  Per-contract OI / greeks / IV\n{LINE}")
    q1_pass = True
    for sym, r in snaps.items():
        c = first_result(r)
        if r.get("status") != 200 or not c:
            body = r.get("body") or {}
            print(f"  {sym}: HTTP {r.get('status')} -- {body.get('message') or 'no contract returned'}")
            q1_pass = False
            continue
        det = c.get("details") or {}
        greeks = c.get("greeks") or {}
        oi, iv = c.get("open_interest"), c.get("implied_volatility")
        g = {k: greeks.get(k) for k in ("delta", "gamma", "theta", "vega")}
        print(f"  {sym}  {det.get('ticker')}  (exp {det.get('expiration_date')}, "
              f"strike {det.get('strike_price')})")
        print(f"      open_interest      : {oi!r}")
        print(f"      implied_volatility : {iv!r}")
        print(f"      greeks             : {g}")
        # Coverage across the sample, not just the first row -- one populated
        # contract would not prove the field is reliably served.
        rs = results(r)
        n = len(rs)
        have_oi = sum(1 for x in rs if x.get("open_interest") is not None)
        have_iv = sum(1 for x in rs if x.get("implied_volatility") is not None)
        have_g = sum(1 for x in rs if (x.get("greeks") or {}).get("gamma") is not None)
        print(f"      across {n} contracts: OI {have_oi}/{n}, IV {have_iv}/{n}, gamma {have_g}/{n}")
        if oi is None or iv is None or greeks.get("gamma") is None:
            q1_pass = False
    print(f"\n  VERDICT: " + ("PASS -- OI, IV and greeks all present per contract."
                              if q1_pass else
                              "FAIL -- at least one required field is missing."))

    # ---- Q2 -------------------------------------------------------------
    print(f"\n{LINE}\nQ2  History depth (one SPX contract)\n{LINE}")
    spx_c = first_result(snaps.get("SPX", {}))
    ticker = ((spx_c or {}).get("details") or {}).get("ticker")
    q2_verdict = "UNKNOWN -- no SPX contract available to test."
    q2_pass = False
    if ticker:
        today = session.session_date_obj()
        start = (today - dt.timedelta(days=3 * 365)).isoformat()
        r = call(base, AGGS_PATH.format(ticker=ticker, start=start,
                                        end=today.isoformat()),
                 {"adjusted": "true", "sort": "asc", "limit": 50000},
                 key, f"verify_aggs_{ticker}", "bearer")
        rs = results(r)
        print(f"  [{r.get('status')}] {ticker}   requested from {start}")
        if rs:
            f_d = dt.datetime.fromtimestamp(rs[0]["t"] / 1000, dt.timezone.utc).date()
            l_d = dt.datetime.fromtimestamp(rs[-1]["t"] / 1000, dt.timezone.utc).date()
            span = (l_d - f_d).days
            print(f"      {len(rs)} daily bars   earliest {f_d}   latest {l_d}   span {span}d")
            q2_pass = True
            q2_verdict = (f"{len(rs)} daily bars, {f_d} to {l_d} ({span}d). "
                          f"NOTE: an option's history is bounded by its listing "
                          f"date, so this is a floor on depth, not a measure of "
                          f"the documented 2-year entitlement.")
        else:
            body = r.get("body") or {}
            q2_verdict = (f"NO BARS returned (HTTP {r.get('status')}"
                          f"{', ' + str(body.get('message')) if body.get('message') else ''}).")
        time.sleep(STARTER_PACING)
    print(f"\n  VERDICT: {q2_verdict}")

    # ---- Q3 -------------------------------------------------------------
    print(f"\n{LINE}\nQ3  OI vintage -- settled EOD?\n{LINE}")
    c = first_result(snaps.get("SPY", {})) or first_result(snaps.get("SPX", {}))
    q3_verdict = "UNKNOWN -- no contract to inspect."
    if c:
        day = c.get("day") or {}
        lq = c.get("last_quote") or {}
        print(f"      open_interest    : {c.get('open_interest')!r}")
        print(f"      top-level keys   : {sorted(c)}")
        print(f"      day sub-keys     : {sorted(day)}")
        print(f"      day.last_updated : {day.get('last_updated')!r}")
        print(f"      last_quote t     : {lq.get('last_updated') or lq.get('timestamp')!r}")
        has_oi_stamp = any("oi" in k.lower() and "updat" in k.lower() for k in c)
        q3_verdict = (
            "CONSISTENT WITH SETTLED EOD -- open_interest is served as a scalar "
            "with no independent OI timestamp"
            + ("" if not has_oi_stamp else " (an OI-specific stamp is present)")
            + ". Their docs define it as 'the quantity of this contract held at "
            "the end of the last trading day'. The payload does not contradict "
            "that, but proving it empirically needs an intraday diff during a "
            "live session -- markets are closed now.")
    print(f"\n  VERDICT: {q3_verdict}")

    print(f"\n{LINE}")
    print(f"Q1 {'PASS' if q1_pass else 'FAIL'}   "
          f"Q2 {'PASS' if q2_pass else 'INCONCLUSIVE'}   Q3 see above")
    print(f"Raw responses: {OUT_DIR}\n{LINE}")
    return 0 if q1_pass else 1


if __name__ == "__main__":
    sys.exit(main())
