"""
ST-R6.66c -- the wealth-effect impulse against real consumption growth (signal-triage
Batch 14, item 66, written as 59; ruling 3; b52-batch14-a2). A dated ledger, report only.

    python tools/calibration/st_r6_66c_wealth_effect.py [--box] [--out DIR] [--date D]

THE PRE-REGISTRATION is docs/ledgers/wealth-effect-preregistration-2026-10.md,
committed alone before this script and never edited (tools/validate_batch14_a2.py
holds its SHA-256). This script applies it and changes nothing in it:

  the impulse, month m   Z.1's household equity share (FRED BOGZ1FL153064486Q) of
                         the latest quarter ending at least three full months
                         before m's end, times SPX's year-on-year price return at m
                         (Yahoo ^GSPC, month-end closes), over 100: pp
  the outcome, month m   real PCE's growth over the next twelve months (FRED
                         DPCERA3M086SBEA), m+12 over m, percent
  the sample             every December from 1960 with its twelve forward months
  PASS                   Spearman rho >= 0.20 with n >= 40, rho > 0 in each half
                         (split at the median year), and the impulse's top tercile's
                         median outcome above the bottom tercile's; INSUFFICIENT
                         under n 40; FAIL otherwise

Public sources only: it opens no store and reads no vendor value and no by-hand key.
study(data, mode) is arithmetic over plain series, so a gate can hand it a fixture.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                           # noqa: E402

ITEM = "ST-R6.66c"
PREREG = "docs/ledgers/wealth-effect-preregistration-2026-10.md"
SHARE_ID, PCE_ID, SPX = "BOGZ1FL153064486Q", "DPCERA3M086SBEA", "^GSPC"
FIRST_YEAR, MIN_N, RHO_MIN = 1960, 40, 0.20
PASS_RULE = ("the pre-registration's (docs/ledgers/wealth-effect-preregistration-2026-10.md): "
             "Spearman rho between each December's impulse and real PCE growth over the "
             "next twelve months >= 0.20 with n >= 40, rho > 0 in each half split at the "
             "median year, and the impulse's top tercile's median outcome above the "
             "bottom tercile's; INSUFFICIENT under n 40")


def load_public() -> dict:
    from altdata.ledgers import sources as S                    # noqa: PLC0415
    import datetime as dt                                       # noqa: PLC0415
    return {"share": S.fred(SHARE_ID), "pce": S.fred(PCE_ID), "spx": S.yahoo(SPX),
            "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def _ym(d: str) -> tuple[int, int]:
    return int(d[:4]), int(d[5:7])


def _shift(y: int, m: int, k: int) -> tuple[int, int]:
    n = y * 12 + (m - 1) + k
    return n // 12, n % 12 + 1


def share_for(share: list, y: int, m: int) -> Optional[float]:
    """The latest quarter whose end is at least three full months before m's end:
    a quarter dated (qy, qm) ends at (qy, qm+2); it qualifies when that month is
    on or before m-3."""
    ly, lm = _shift(y, m, -3)
    best = None
    for d, v in share:
        qy, qm = _ym(d)
        ey, em = _shift(qy, qm, 2)
        if (ey, em) <= (ly, lm):
            best = v
    return best


def month_end_closes(spx: list) -> dict[tuple[int, int], float]:
    out: dict[tuple[int, int], float] = {}
    for d, v in spx:
        out[_ym(d)] = v
    return out


def ranks(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return r


def spearman(a: list[float], b: list[float]) -> Optional[float]:
    if len(a) < 3:
        return None
    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return None if den == 0 else num / den


def episodes(data: dict) -> list[dict]:
    closes = month_end_closes(data["spx"])
    pce = {_ym(d): v for d, v in data["pce"]}
    share = sorted(data["share"])
    out = []
    years = sorted({y for (y, m) in closes if m == 12 and y >= FIRST_YEAR})
    for y in years:
        c, back = closes.get((y, 12)), closes.get((y - 1, 12))
        p0, p1 = pce.get((y, 12)), pce.get((y + 1, 12))
        s = share_for(share, y, 12)
        if None in (c, back, p0, p1, s) or back <= 0 or p0 <= 0:
            continue
        ret = (c / back - 1.0) * 100.0
        out.append({"december": y, "share_pct": round(s, 3), "spx_yoy_pct": round(ret, 2),
                    "impulse_pp": round(s * ret / 100.0, 3),
                    "real_pce_next12_pct": round((p1 / p0 - 1.0) * 100.0, 3)})
    return out


def study(data: dict, mode: str) -> dict:
    eps = episodes(data)
    n = len(eps)
    x = [e["impulse_pp"] for e in eps]
    y = [e["real_pce_next12_pct"] for e in eps]
    rho = spearman(x, y)
    half = (n + 1) // 2
    rho1 = spearman(x[:half], y[:half])
    rho2 = spearman(x[half:], y[half:])
    k = n // 3
    by = sorted(eps, key=lambda e: e["impulse_pp"])
    lo = C.median([e["real_pce_next12_pct"] for e in by[:k]]) if k else None
    hi = C.median([e["real_pce_next12_pct"] for e in by[-k:]]) if k else None
    if n < MIN_N:
        verdict = (f"{C.INSUFFICIENT} -- n {n} under the registered {MIN_N}")
    else:
        ok = (rho is not None and rho >= RHO_MIN and (rho1 or 0) > 0 and (rho2 or 0) > 0
              and lo is not None and hi is not None and hi > lo)
        verdict = (f"{C.PASS if ok else C.FAIL} -- rho {C.f2(rho)} (rule >= {RHO_MIN}), "
                   f"halves {C.f2(rho1)} and {C.f2(rho2)} (rule > 0), top tercile "
                   f"{C.f2(hi)}% against bottom {C.f2(lo)}% (rule: top above bottom)")
    first = eps[0]["december"] if eps else "n/a"
    last = eps[-1]["december"] if eps else "n/a"
    return {
        "item": ITEM,
        "title": "the wealth-effect impulse against real consumption growth",
        "source_mode": mode,
        "as_of": (f"real PCE to {data['pce'][-1][0] if data['pce'] else 'n/a'}; Z.1 to "
                  f"{data['share'][-1][0] if data['share'] else 'n/a'}; SPX to "
                  f"{data['spx'][-1][0] if data['spx'] else 'n/a'}"),
        "window": f"Decembers {first} to {last}, each with its twelve forward months",
        "n": n,
        "statistic": ("Spearman's rho between each December's impulse (Z.1's household "
                      "equity share, lagged three months for publication, times SPX's "
                      "year-on-year return) and real PCE growth over the next twelve "
                      "months; its halves; the terciles' median outcomes"),
        "pass_rule": PASS_RULE,
        "verdict": verdict,
        "rights": ("None. The impulse stays report-only whatever the verdict, as ruled "
                   "(item 66: 'report only until the ledger is built'); a verdict grants "
                   "nothing by itself, and any later right is the operator's ruling. "
                   + C.RIGHTS_NOTE),
        "sources": [f"FRED graph CSV (no key): {SHARE_ID}, {PCE_ID}, current vintages",
                    f"Yahoo daily closes: {SPX} (month-end closes)",
                    f"retrieved {data.get('retrieved', 'n/a')}",
                    f"pre-registration: {PREREG}"],
        "body": [f"- rho over the whole sample: {C.f2(rho)} (n {n})",
                 f"- rho by half: {C.f2(rho1)} (Decembers {first} to "
                 f"{eps[half - 1]['december'] if half and eps else 'n/a'}), {C.f2(rho2)} "
                 f"(the rest)",
                 f"- real PCE growth over the next twelve months, median: top tercile of "
                 f"the impulse {C.f2(hi)}%, bottom tercile {C.f2(lo)}% (k {k} each)"],
        "caveats": ["Equity returns and consumption both follow the business cycle: a "
                    "positive rho is consistent with a common cause as well as a wealth "
                    "effect. The ledger claims no cause.",
                    "Current vintages: BEA's and Z.1's revisions are not undone; no "
                    "public source serves all three series' first prints."],
        "episodes": eps,
    }


if __name__ == "__main__":
    sys.exit(C.cli(ITEM, load_public, study))
