"""
DATA GATE: China's official gold, SAFE against IMF IFS, on this box's store.

China keeps SAFE (safe.gold_reserves_oz) as its primary -- it publishes within
days -- and the IMF's International Liquidity series (imf.ifs.gold_reserves_oz.chn,
altdata/sources/imf_ifs.py) as the cross-check. The two are the same reported
number by two routes, so a gap is a parse error, a unit slip or a restatement on
one side: every month both hold in the last two years must agree within 1%
(config/imf_ifs.yaml china_divergence_max). The code gate proves the check on
seeded rows (tools/validate_imf_ifs.py, group F); this one runs it on the real
store. In a checkout with no store it reports NOT VALIDATED; under CI it skips
(box_only); like every data gate it does not set `make validate`'s exit code.

    python tools/validate_imf_china.py
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
    from altdata import observations                            # noqa: PLC0415
    from altdata.sources import imf_ifs                         # noqa: PLC0415
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"{LINE}\nChina's official gold: SAFE against IMF IFS (data gate)\n{LINE}")
    with observations.ObservationStore() as st:
        r = imf_ifs.crosscheck(st)
        path = st.path
    if not r["months"]:
        print(f"  SKIPPED -- the store at {path} holds no month in both "
              f"safe.gold_reserves_oz and {imf_ifs.LEVEL}chn (SAFE to "
              f"{r['safe_latest']}, IFS to {r['ifs_latest']})\n\nNOT VALIDATED "
              f"(no data). This gate runs on the box.")
        return 1
    for m in r["months"]:
        print(f"  {m['month']}  SAFE {m['safe']:>14,.0f}  IFS {m['ifs']:>14,.0f}  "
              f"gap {100 * (m['gap'] or 0):+.3f}%" + ("  FLAG" if m["flag"] else ""))
    tol = 100 * r["tolerance"]
    if r["flagged"]:
        print(f"\n  FAIL  {len(r['flagged'])} month(s) diverge by more than {tol:.0f}%: "
              + ", ".join(m["month"] for m in r["flagged"]))
        return 1
    print(f"\n  PASS  {len(r['months'])} common month(s) agree within {tol:.0f}% "
          f"(latest common {r['latest_common']}; SAFE to {r['safe_latest']}, "
          f"IFS to {r['ifs_latest']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
