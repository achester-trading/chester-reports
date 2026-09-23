#!/usr/bin/env python3
"""
Validation gate for tools/structure_compare.py. (Paste D piece 6)

    python tools/validate_structure_compare.py

The property under test is one sentence: A GUESSED VOLATILITY CANNOT REACH THE
TABLE. Everything below is that sentence made checkable.

  A. NO ASSUMED SIGMA SURVIVES. The module the paper's tables came from carried
     four hard-coded volatilities. A comparison priced on one of them looks
     identical to a measured one, arrives with the same decimals, and is the kind
     of number that gets acted on -- so the gate reads the source for them.

  B. THE SIGMA IS SOLVED, NOT READ OFF THE VENDOR. The vendor's call and put at
     one strike disagreed by nine vol points at SPY's 378-day expiry, because
     inverting an ITM price amplifies a wide quote. Every priced tenor must carry
     iv_source solved_bs_v1 AND the vendor's own legs beside it, so the reason
     this path exists stays visible.

  C. TWO NEAREST DISTINCT STRIKES. The solver propagates a strike's vol to its ITM
     twin, so "the two nearest contracts" is one strike twice and its gap is
     structurally zero -- a tolerance that cannot fire. The gate asserts two
     distinct strikes, which is the only form in which the tolerance means
     anything.

  D. AN UNPRICEABLE ASSET IS NOT PRICED. No chain, no number, and the record says
     which symbol would have to enter the capture universe first.

  E. CHAPTER 15's FINDING, RECOMPUTED. The 50/50 index-and-bills mix beats the
     buffered fund, the synthetic PPN and the bills-plus-butterfly on expected
     value. If that stops being true on live vol it is a finding, not a failure --
     so the gate prints the comparison and asserts only the direction the paper
     states, which is that these three lose.

  F. DETERMINISM AND THE WEEKLY GUARD. Two computations agree; a second write
     inside a week writes nothing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from altdata import derived, observations                      # noqa: E402
import structure_compare as sc                                 # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78
PASS = 0
FAIL = 0
SKIPPED: list[str] = []


def ok(msg: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {msg}")


def bad(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {msg}")


def check(cond: bool, msg: str) -> bool:
    (ok if cond else bad)(msg)
    return bool(cond)


def group_a() -> None:
    print(f"\n{LINE}\nA. NO ASSUMED SIGMA SURVIVES IN THE SOURCE\n{LINE}")
    src = (REPO / "tools" / "structure_compare.py").read_text(encoding="utf-8")
    check("sig=0.16" not in src and "sig=0.28" not in src
          and "sig=0.60" not in src,
          "the four hard-coded asset volatilities are gone")
    check("ASSETS={" not in src and "ASSETS = {" not in src,
          "and so is the ASSETS table that carried them")
    check("from svglib" not in src,
          "and the svglib import that made the old module unrunnable")
    # The paper's sigmas survive in ONE place on purpose: NOT_SOURCED records what
    # the paper assumed for the assets this system cannot price, which is a record
    # of the gap rather than an input to a calculation.
    check(all("paper_sigma" in spec for spec in sc.NOT_SOURCED.values()),
          "the paper's assumptions survive only inside NOT_SOURCED, as a record of "
          "what would be needed rather than as an input")
    for name, spec in sc.NOT_SOURCED.items():
        check(bool(spec.get("would_need")) and bool(spec.get("reason")),
              f"{name} names the symbol that would have to be captured "
              f"({spec.get('would_need')})")


def group_bcde(m: dict) -> None:
    print(f"\n{LINE}\nB. THE SIGMA IS SOLVED, WITH THE VENDOR'S LEGS BESIDE IT\n{LINE}")
    priced = {k: v for k, v in (m.get("tenors") or {}).items()
              if v.get("state") == "priced"}
    if not priced:
        SKIPPED.append("no tenor priced from the stored chains")
        print("  SKIP  no tenor priced -- the store holds no usable SPY chain")
        return
    for label, row in priced.items():
        v = row["atm_vol"]
        check(row.get("sigma_source") == "measured_atm_iv",
              f"{label}: sigma is labelled measured ({row['sigma']:.4f})")
        check(v.get("iv_source") == "solved_bs_v1",
              f"{label}: the vol is SOLVED ({v.get('iv_source')}), not the "
              f"vendor's own field")
        check(v.get("vendor_legs") is not None,
              f"{label}: the vendor's legs are reported beside it "
              f"({v.get('vendor_legs')}), gap {v.get('vendor_leg_gap')}")
        check(v.get("forward") is not None,
              f"{label}: a parity-implied forward was found ({v.get('forward')}) "
              f"-- no dividend was assumed to get the vol")
        check(row["years_priced"] != row["years_requested"]
              or v.get("dte_note"),
              f"{label}: the tenor actually priced is recorded "
              f"({row['years_priced']}y asked {row['years_requested']}y)")

    print(f"\n{LINE}\nC. TWO NEAREST DISTINCT STRIKES\n{LINE}")
    for label, row in priced.items():
        ks = row["atm_vol"].get("solved_strikes") or []
        check(len(set(ks)) == 2,
              f"{label}: two DISTINCT strikes anchor the vol ({ks}) -- one strike "
              f"twice would make the tolerance unfireable")
        check(row["atm_vol"].get("solved_gap") is not None
              and row["atm_vol"]["solved_gap"] <= sc.MAX_SOLVED_GAP,
              f"{label}: their gap {row['atm_vol'].get('solved_gap')} is inside "
              f"the declared {sc.MAX_SOLVED_GAP}")

    print(f"\n{LINE}\nD. AN UNPRICEABLE SYMBOL IS NOT PRICED\n{LINE}")
    none = sc.compare("ASTS")
    check(none.get("state") == "not_yet_sourced"
          or all(t.get("state") != "priced"
                 for t in (none.get("tenors") or {}).values()),
          f"a symbol with no declared dividend yield is not priced "
          f"({none.get('state')}: {str(none.get('reason'))[:60]}...)")
    check("sigma" not in json.dumps(none.get("tenors") or {}),
          "and no sigma appears anywhere in its record -- a guessed vol cannot "
          "reach the table by any path")

    print(f"\n{LINE}\nE. CHAPTER 15's FINDING, ON LIVE VOL\n{LINE}")
    for label, row in priced.items():
        mix = row["half_and_half_expected_pnl"]
        loses = set(row["loses_to_half_and_half"])
        print(f"  {label}: the 50/50 mix returns {mix:+.2f}; "
              f"beaten by {row['beats_half_and_half']}")
        for name in ("buffered_10", "synthetic_ppn",
                     "bills_plus_reverse_iron_butterfly"):
            ev = row["structures"][name]["expected_pnl"]
            check(name in loses,
                  f"{label}: {name} ({ev:+.2f}) loses to the mix ({mix:+.2f}), as "
                  f"15.5 states")
        check("hold_the_index" in row["beats_half_and_half"],
              f"{label}: and holding the index beats the mix, which is the other "
              f"half of the same finding")


def group_f(m: dict) -> None:
    print(f"\n{LINE}\nF. DETERMINISM AND THE WEEKLY GUARD\n{LINE}")
    again = sc.compare("SPY")
    a = json.dumps(m.get("tenors"), sort_keys=True)
    b = json.dumps(again.get("tenors"), sort_keys=True)
    check(a == b, f"two computations agree byte for byte ({len(a)} chars) -- the "
                  f"expectation is a deterministic midpoint grid, not a seeded "
                  f"Monte Carlo")
    db = observations.ObservationStore()
    try:
        stale = sc.stale_symbols(db, ["SPY"])
        rows = db.as_of("structure.compare.spy")
        if not rows:
            SKIPPED.append("no stored structure.compare.spy to test the guard")
            print("  SKIP  nothing stored yet; run `weekly` first")
        else:
            check(not stale,
                  "a symbol written inside the week is not rewritten -- the guard "
                  "counts days since the last row rather than testing a weekday, "
                  "so it fires once a week and self-heals after an outage")
        e = derived.registry_entry("structure.compare.spy")
        check(e.get("mechanism_group") == "structure_economics",
              f"the key is registered in its own mechanism group "
              f"({e.get('mechanism_group')}) -- a comparison of expressions can "
              f"never confirm a market signal")
        check(e.get("trigger_eligible") is False,
              "and it is not trigger_eligible: it says how to hold a view, never "
              "whether the view is right")
    finally:
        db.close()


def main() -> int:
    print(f"{LINE}\nstructure_compare.py -- live vol, or no table\n{LINE}")
    group_a()
    m = sc.compare("SPY")
    print(f"  SPY state={m.get('state')}  "
          f"tenors={[(k, v.get('state')) for k, v in (m.get('tenors') or {}).items()]}")
    group_bcde(m)
    group_f(m)
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed"
          + (f", {len(SKIPPED)} skipped" if SKIPPED else "") + f"\n{LINE}")
    for s in SKIPPED:
        print(f"  SKIPPED: {s}")
    print("VALIDATION PASSED" if FAIL == 0 else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
