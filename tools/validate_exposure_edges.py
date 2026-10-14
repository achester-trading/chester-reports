"""
Validation gate for the exposure engine's edges (dealer audit, 9 Oct 2026).

SYNTHETIC CHAINS, no store and no network. Every chain here is built in the
gate, so the verdict is about the commit, not about whatever the box captured.

The failure cases share one rule: a chain that cannot support a net GEX must
say so -- an error dict, or a None net_gex with a flip_reason -- and never hand
back a number. A zero, or a figure computed from nothing, reads exactly like a
measured flat book, and the regime word would be printed off it.

  A  EMPTY CHAIN. No rows at all: an error dict, no numeric net GEX.
  B  NO IV. Rows with open interest but no implied vol and no vendor gamma:
     nothing is usable, so net_gex is None and the flip carries a reason.
  C  SETTLED, ALL DTE 0. An after-the-close capture whose every row expires
     today: the settlement rule excludes all of them from exposure, so net_gex
     is None, the flip carries a reason, and the 0DTE bucket reports OI only.
  D  RECONCILIATION (F1, F21). On a populated chain: the per-strike GEX sums to
     net_gex; gross_gex_abs >= |net_gex|, overall and in every bucket;
     net_to_gross is |net| / gross; gross_gamma_per_1pct is gross x 0.01 x
     spot; and net_gex_at_spot, re-pricing gamma at spot through the same
     dealer_position(), lands on the profile's net -- one sign rule, two
     call sites that agree.

    python tools/validate_exposure_edges.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import exposure_compute as ec  # noqa: E402

LINE = "=" * 74
PASS = 0
FAIL = 0

SETTLED = "2026-09-04T20:10:00+00:00"     # 16:10 ET: a settled EOD capture
INTRADAY = "2026-09-04T14:30:00+00:00"    # 10:30 ET


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    (ok if c else bad)(m)


def is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def chain(expiries, *, fetched=SETTLED, iv=0.25, put_oi=1300.0) -> list[dict]:
    rows = []
    for expiry, dte in expiries:
        for strike in (90.0, 95.0, 100.0, 105.0, 110.0):
            for right in ("C", "P"):
                rows.append({
                    "symbol": "SYN", "fetched_at": fetched, "spot": 100.0,
                    "expiry": expiry, "dte": dte, "right": right,
                    "strike": strike,
                    "open_interest": 1000.0 if right == "C" else put_oi,
                    "implied_vol": iv, "volume": 100.0, "bid": 1.0, "ask": 1.1,
                    "gamma": None, "greeks_status": None, "vendor": None,
                    "spot_source": None,
                })
    return rows


def no_net(prof: dict) -> bool:
    """Neither the top level nor `overall` carries a numeric net GEX."""
    return not is_num(prof.get("net_gex")) and \
        not is_num((prof.get("overall") or {}).get("net_gex"))


def group_a() -> None:
    print(f"\n{LINE}\nA. EMPTY CHAIN\n{LINE}")
    prof = ec.compute_symbol([], "SYN")
    check(bool(prof.get("error")), f"an empty chain returns an error dict "
          f"({prof.get('error')!r})")
    check(no_net(prof), "and no numeric net GEX")


def group_b() -> None:
    print(f"\n{LINE}\nB. NO IV\n{LINE}")
    prof = ec.compute_symbol(
        chain((("2026-09-11", 7), ("2026-10-16", 42)), fetched=INTRADAY, iv=None),
        "SYN")
    o = prof.get("overall") or {}
    q = prof.get("quality") or {}
    check(q.get("skipped_no_iv") == q.get("rows_in") and q.get("rows_in"),
          f"every row is skipped for want of IV ({q.get('skipped_no_iv')} of "
          f"{q.get('rows_in')})")
    check(bool(prof.get("error")) or no_net(prof),
          f"no numeric net GEX (net_gex={o.get('net_gex')!r})")
    check(bool(prof.get("error")) or bool(o.get("flip_reason")),
          f"the blank flip carries a reason ({o.get('flip_reason')!r})")
    check(o.get("gross_gex_abs") is None and o.get("net_to_gross") is None,
          "gross and net-to-gross are None, not zero")


def group_c() -> None:
    print(f"\n{LINE}\nC. SETTLED CAPTURE, EVERY ROW DTE 0\n{LINE}")
    prof = ec.compute_symbol(chain((("2026-09-04", 0),)), "SYN")
    o = prof.get("overall") or {}
    q = prof.get("quality") or {}
    check(prof.get("capture") == "settled_eod" or bool(prof.get("error")),
          f"the capture reads as settled ({prof.get('capture')!r})")
    check(q.get("exposure_rows") == 0 or bool(prof.get("error")),
          f"no row survives into exposure ({q.get('exposure_rows')!r} rows, "
          f"{q.get('settled_0dte_excluded_rows')!r} excluded)")
    check(bool(prof.get("error")) or no_net(prof),
          f"no numeric net GEX (net_gex={o.get('net_gex')!r})")
    check(bool(prof.get("error")) or bool(o.get("flip_reason")),
          f"the blank flip carries a reason ({o.get('flip_reason')!r})")
    z = (prof.get("buckets") or {}).get("0dte") or {}
    check(z.get("net_gex") is None and z.get("gross_gex_abs") is None
          and is_num(z.get("oi_total")),
          "the 0DTE bucket reports OI and no gamma, gross included")


def group_d() -> None:
    print(f"\n{LINE}\nD. RECONCILIATION\n{LINE}")
    prof = ec.compute_symbol(
        chain((("2026-09-04", 0), ("2026-09-11", 7), ("2026-10-16", 42))), "SYN")
    o = prof.get("overall") or {}
    net, gross = o.get("net_gex"), o.get("gross_gex_abs")
    check(is_num(net) and is_num(gross), f"a populated chain computes "
          f"(net {net!r}, gross {gross!r})")
    if not (is_num(net) and is_num(gross)):
        return
    strike_sum = sum(s["gex"] for s in prof.get("per_strike") or [])
    check(math.isclose(strike_sum, net, rel_tol=1e-9, abs_tol=1e-6),
          f"the per-strike GEX sums to net_gex ({strike_sum:,.2f} vs {net:,.2f})")
    check(gross >= abs(net), f"gross_gex_abs >= |net_gex| overall "
          f"({gross:,.0f} >= {abs(net):,.0f})")
    check(math.isclose(o.get("net_to_gross"), abs(net) / gross, rel_tol=1e-12),
          f"net_to_gross is |net| / gross ({o.get('net_to_gross'):.4f})")
    check(math.isclose(o.get("gross_gamma_per_1pct"),
                       gross * 0.01 * prof["spot"], rel_tol=1e-12),
          "gross_gamma_per_1pct is gross x 0.01 x spot")
    # The chain's puts outweigh its calls 1.3 : 1, so the net is negative and a
    # strict fraction of the gross -- the case the audit worried about.
    check(net < 0 and 0 < o["net_to_gross"] < 1,
          "a put-heavy book nets negative, at a fraction of its gross")

    live = [(b, p) for b, p in (prof.get("buckets") or {}).items()
            if is_num(p.get("net_gex"))]
    check(bool(live) and all(p["gross_gex_abs"] >= abs(p["net_gex"])
                             for _, p in live),
          f"gross >= |net| in every computed bucket ({[b for b, _ in live]})")
    check(all("gross_gex_abs" in p and "net_to_gross" in p
              for p in (prof.get("buckets") or {}).values()),
          "every bucket carries the gross keys, settled 0DTE included")

    exposure = [r for r in chain((("2026-09-11", 7), ("2026-10-16", 42)))]
    at_spot = ec.net_gex_at_spot(exposure, prof["spot"], ec.config.RISK_FREE_RATE)
    check(math.isclose(at_spot, net, rel_tol=1e-6),
          f"net_gex_at_spot at spot reproduces net_gex ({at_spot:,.2f}) -- "
          f"one sign rule (F21)")
    flipped = [{**r, "right": "P" if r["right"] == "C" else "C"} for r in exposure]
    check(math.isclose(ec.net_gex_at_spot(flipped, prof["spot"],
                                          ec.config.RISK_FREE_RATE),
                       -net, rel_tol=1e-6),
          "swapping every call for a put flips its sign")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    group_a()
    group_b()
    group_c()
    group_d()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
