"""
Validation gate for the Gate 1.5 schedule fallback (altdata/sources/ibkr_costs).

No Gateway, no network. Checks the arithmetic of the rate card, the measured
(never assumed) leverage, and above all that cost_source cannot be confused
with a broker preview.

  A  cost_source discipline -- three grades, never collapsed.
  B  Stock commission: per-share, floor, 1% cap.
  C  Option commission: premium bands, order floor, assumed-band flag.
  D  Margin from the MEASURED multiplier, None when unmeasurable.
  E  Buying-power delta is exactly -notional, at any leverage.
  F  Provenance: the unverified schedule flag rides along with the number.
  G  Degradation: no price and no account still produce an honest record.

    python tools/validate_ibkr_costs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import config                              # noqa: E402
from altdata.sources import ibkr_costs as ic            # noqa: E402
from altdata.sources import ibkr_whatif as wi           # noqa: E402

LINE = "=" * 78
PASSED = FAILED = 0

# A representative margin account: 4.44x leverage, maint/init 0.8.
BASELINE = {"NetLiquidation": 100000.0, "BuyingPower": 400000.0,
            "AvailableFunds": 90000.0, "ExcessLiquidity": 92000.0,
            "FullInitMarginReq": 10000.0, "FullMaintMarginReq": 8000.0}


def check(cond: bool, label: str) -> None:
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  FAIL  {label}")


def group_a() -> None:
    print(f"\n{LINE}\nA. cost_source -- THREE GRADES, NEVER COLLAPSED\n{LINE}")
    e = ic.estimate("SPY", "long", 100, 770.67, baseline=BASELINE)
    check(e["cost_source"] == "estimated_from_schedule",
          "an estimate is tagged estimated_from_schedule")
    check(e["cost_source"] != "whatif",
          "and is never tagged whatif -- a packet cannot claim a preview it "
          "did not get")

    # The What-If path must tag itself too, or the distinction is one-sided.
    src = (REPO / "altdata" / "sources" / "ibkr_whatif.py").read_text(encoding="utf-8")
    check('"cost_source": "whatif"' in src,
          "ibkr_whatif tags its own output cost_source=whatif")
    check(ic.COST_SOURCE == "estimated_from_schedule",
          "the constant is the one name, not a literal repeated per call site")
    check(e.get("method_version") == "schedule_v1",
          "the method is versioned, so a later rate card is distinguishable")


def group_b() -> None:
    print(f"\n{LINE}\nB. STOCK COMMISSION\n{LINE}")
    # 100 shares x 0.0035 = 0.35, exactly at the floor.
    c = ic.commission_stk(100, 770.67)
    check(abs(c["raw_per_share_total"] - 0.35) < 1e-9,
          "100 shares x $0.0035 = $0.35 per-share total")
    check(abs(c["estimate"] - 0.35) < 1e-9, "estimate is $0.35")
    check(c["cap_applied"] is False,
          "the 1% cap ($770.67) does not bind a $0.35 commission")

    # 10 shares: raw 0.035, floor lifts it to 0.35 -- a 10x effect.
    c2 = ic.commission_stk(10, 770.67)
    check(abs(c2["estimate"] - 0.35) < 1e-9 and c2["floor_applied"] is True,
          "10 shares is floored to $0.35 and says floor_applied")

    # A penny stock where 1% of trade value binds: 1000 shares at $0.02 =
    # $20 notional, 1% = $0.20, below both the raw $3.50 and the $0.35 floor.
    c3 = ic.commission_stk(1000, 0.02)
    check(c3["cap_applied"] is True and abs(c3["estimate"] - 0.20) < 1e-9,
          "the 1% cap binds on a low-value trade and is applied last")
    check(c3["estimate"] < config.IBKR_STK_TIERED_MIN_PER_ORDER,
          "the cap can take the commission BELOW the floor -- cap wins, as "
          "IBKR's schedule has it")

    c4 = ic.commission_stk(100, None)
    check(c4["cap"] is None and abs(c4["estimate"] - 0.35) < 1e-9,
          "with no price there is no cap, and the floor still applies")


def group_c() -> None:
    print(f"\n{LINE}\nC. OPTION COMMISSION\n{LINE}")
    c = ic.commission_opt(10, 5.00)
    check(abs(c["estimate"] - 6.50) < 1e-9,
          "10 contracts at premium 5.00 -> 10 x $0.65 = $6.50")
    check(c["premium_band_assumed"] is False, "a supplied premium is not assumed")

    c2 = ic.commission_opt(1, 5.00)
    check(abs(c2["estimate"] - 1.00) < 1e-9 and c2["floor_applied"],
          "1 contract is lifted to the $1.00 order floor")

    check(abs(ic.commission_opt(10, 0.07)["estimate"] - 5.00) < 1e-9,
          "premium 0.07 falls in the $0.50 band")
    check(abs(ic.commission_opt(10, 0.01)["estimate"] - 2.50) < 1e-9,
          "premium 0.01 falls in the $0.25 band")

    c3 = ic.commission_opt(10, None)
    check(c3["premium_band_assumed"] is True and abs(c3["estimate"] - 6.50) < 1e-9,
          "an unknown premium assumes the TOP band and flags that it did")


def group_d() -> None:
    print(f"\n{LINE}\nD. MARGIN FROM MEASURED LEVERAGE\n{LINE}")
    notional = 100 * 770.67                     # 77,067
    m = ic.margin_impact(notional, BASELINE, "BUY", "STK")
    mult = 400000 / 90000                       # 4.444...
    check(abs(m["leverage_multiplier_observed"] - mult) < 1e-9,
          "the multiplier is measured (BuyingPower/AvailableFunds), not 4")
    check(abs(m["init_change"] - notional / mult) < 0.01,
          "initial margin is notional / measured multiplier")
    check(abs(m["maint_to_init_ratio_observed"] - 0.8) < 1e-9,
          "the maint/init ratio is measured from the account (8000/10000)")
    check(abs(m["maint_change"] - (notional / mult) * 0.8) < 0.01,
          "maintenance margin uses that measured ratio, not an assumed 25%")

    empty = {"BuyingPower": 400000.0, "AvailableFunds": 90000.0,
             "FullInitMarginReq": 0.0, "FullMaintMarginReq": 0.0}
    m2 = ic.margin_impact(notional, empty, "BUY", "STK")
    check(m2["maint_change"] is None,
          "an empty account gives NO maintenance figure rather than a guess")
    check(any("unmeasurable" in c for c in m2["caveats"]),
          "and says why, in a caveat carried with the record")

    m3 = ic.margin_impact(notional, BASELINE, "SELL", "STK")
    check(any("SHORT STOCK IS NOT MODELLED" in c for c in m3["caveats"]),
          "a short is flagged rather than silently under-margined")

    m4 = ic.margin_impact(notional, {}, "BUY", "STK")
    check(m4["init_change"] is None,
          "no account read means no margin estimate at all")


def group_e() -> None:
    print(f"\n{LINE}\nE. BUYING-POWER DELTA IS EXACTLY -NOTIONAL\n{LINE}")
    notional = 77067.0
    b = ic.buying_power_impact(notional, BASELINE)
    check(b["buying_power_delta_est"] == -notional,
          "delta is -notional exactly, not an approximation")
    check(abs(b["buying_power_after_est"] - (400000 - notional)) < 1e-6,
          "after = before - notional")

    # The m cancels: assert it at a different leverage.
    lev2 = dict(BASELINE, BuyingPower=180000.0, AvailableFunds=90000.0)  # 2x
    b2 = ic.buying_power_impact(notional, lev2)
    check(b2["buying_power_delta_est"] == -notional,
          "and it holds at 2x leverage too -- the multiplier really cancels")
    check(abs(b2["available_funds_delta"] - (-notional / 2.0)) < 1e-6,
          "while AvailableFunds delta DOES depend on the measured multiplier")


def group_f() -> None:
    print(f"\n{LINE}\nF. PROVENANCE TRAVELS WITH THE NUMBER\n{LINE}")
    e = ic.estimate("SPY", "long", 100, 770.67, baseline=BASELINE)
    s = e["schedule"]
    check(s["verified"] is False,
          "the schedule is marked UNVERIFIED (IBKR 403s automated fetches)")
    check(s["source"].startswith("https://") and s["as_of"] == "2026-09-05",
          "source URL and as-of date ride along in the record")
    check(s["structure"] == "tiered", "the assumed account structure is named")
    check("Fixed" in s["verify_note"] or "Tiered" in s["verify_note"],
          "the note says the account's structure is itself an assumption")
    check(e["is_floor_not_all_in"] is True and len(e["excludes"]) >= 3,
          "the estimate declares itself a FLOOR and names what it excludes")
    check(any("regulatory" in x for x in e["excludes"]),
          "regulatory pass-throughs are named among the exclusions")


def group_g() -> None:
    print(f"\n{LINE}\nG. HONEST DEGRADATION\n{LINE}")
    e = ic.estimate("SPY", "long", 100, None, baseline={})
    check(e["notional"] is None, "no price means no notional")
    check(e["commission"]["estimate"] == 0.35,
          "commission still estimates -- the rate card needs no account")
    check(e["margin"]["init_change"] is None
          and e["buying_power"]["buying_power_delta_est"] is None,
          "margin and buying power are None, not zero")
    check(e["available"] is True,
          "the record is still `available` -- it IS an estimate, just a partial "
          "one, and available=False is reserved for no estimate at all")

    opt = ic.estimate("SPY", "long", 10, 5.00, sec_type="OPT",
                      baseline=BASELINE)
    check(opt["contract_multiplier"] == 100.0 and opt["notional"] == 5000.0,
          "an option's notional applies the 100x contract multiplier")

    try:
        ic.estimate("SPY", "flat", 100, 770.67, baseline=BASELINE)
        check(False, "flat should not be priceable without an explicit action")
    except ValueError as ex:
        check("does not determine a side" in str(ex),
              "flat is refused here too -- the same rule as What-If's")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"{LINE}\nGATE 1.5 SCHEDULE FALLBACK VALIDATION (no Gateway, no "
          f"network)\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f, group_g):
        g()
    print(f"\n{LINE}\n{PASSED} passed, {FAILED} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAILED else "VALIDATION FAILED")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
