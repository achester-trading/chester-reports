"""
DATA GATE: the FlashAlpha vendor line against the engine, on this box's store
(6b part 3).

The vendor writer (altdata/sources/flashalpha.py, 16:25 ET) stores FlashAlpha's
GEX, raw-signed DEX, flip and walls beside the engine's settled 16:10 profile.
This gate reads the newest session both hold for SPY and flags each pair whose
gap passes its session-set threshold (config/flashalpha.yaml divergence), with
its reason. A flag is a question, never a correction (tools/cross_check.py's
rule); VEX is never compared (its definition is unreconciled). The code gate
proves the check on fixtures (tools/validate_dealer_vendor.py); this one runs it
on the real store. In a checkout with no store it reports NOT VALIDATED; under
CI it skips (box_only); like every data gate it does not set `make validate`'s
exit code.

    python tools/validate_vendor_divergence.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
from box_only import ci_skip                                    # noqa: E402

GATE_KIND = "data"
LINE = "=" * 78


def main() -> int:
    skipped = ci_skip(__file__)
    if skipped is not None:
        return skipped
    from altdata import config as acfg, observations, session   # noqa: PLC0415
    from altdata.sources import flashalpha as fa                # noqa: PLC0415
    from daily_cascade import dealer_block as db                # noqa: PLC0415
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"{LINE}\nThe vendor line: FlashAlpha against the engine (data gate)\n{LINE}")
    now = session.utc_iso()
    with observations.ObservationStore() as st:
        vend = fa.stored(st, now, "SPY")
    if not vend:
        print("  SKIPPED -- no dealer.vendor_* rows for SPY in this store (the 16:25 "
              "writer)\n\nNOT VALIDATED (no data). This gate runs on the box.")
        return 1
    prof = db.newest_settled(vend["day"], "SPY", str(acfg.COMPUTED_DIR), lookback_days=0)
    if not prof:
        print(f"  SKIPPED -- no settled SPY profile for {vend['day']}\n\nNOT VALIDATED.")
        return 1
    rows = fa.compare(vend, prof)
    flagged = [r for r in rows if r["flag"]]
    for line in fa.vendor_line(vend, prof):
        print(f"  {line}")
    if flagged:
        print(f"\n  FAIL  {len(flagged)} pair(s) past their threshold on {vend['day']}: "
              + "; ".join(f"{r['name']} (threshold {r['threshold']:g}; a 15-minute gap "
                          f"on one OI vintage -- a question to look at, not a "
                          f"correction)" for r in flagged))
        return 1
    print(f"\n  PASS  every compared pair inside its threshold on {vend['day']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
