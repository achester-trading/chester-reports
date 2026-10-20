"""
The 12:30 slot's crypto leverage line (CD-9's daily part, the crypto data-sources
order section 4; the a47 chain, 19 Oct 2026): ONE alert-only information line
when S-3's leverage flag ("crypto leverage -- crowded": funding z above +2 with
open interest over market cap at a 90-day high) trips, no setup rights,
mirroring MW-3's exception.

CLOSED UNTIL THE S-3 LEDGER PASSES. The gate is registered in
daily_cascade/midday_gate.GATES, but until config/crypto_sources.yaml
`blocks.midday_leverage` names a ledger whose verdict is PASS (admitted_by, with
admitted_verdict PASS -- the form config/style_regime.yaml uses), it returns
closed with that reason and reads nothing: no store, no flag. A closed slot
prints and writes nothing (midday_gate.run).

ONCE ADMITTED, it reads the newest stored flag (calc.flag_leverage_crowded,
written by altdata/sources/crypto_derived.py) knowable at 12:30 ET: the prior
session's at the latest, since the day's own is computed after the close. No
intraday funding or open-interest series exists, so "trips intraday" can only mean
the newest stored reading; the notes say so. A reading older than four days is
not read.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
GATE_ID = "crypto_leverage"
FLAG_KEY = "calc.flag_leverage_crowded"


def _admission(cfg: Optional[dict] = None) -> tuple[bool, str]:
    """(admitted, why): the passing S-3 ledger the config names, or the reason
    the gate stays closed."""
    if cfg is None:
        from altdata.sources import _crypto as C                # noqa: PLC0415
        cfg = C.config()
    m = (cfg.get("blocks") or {}).get("midday_leverage") or {}
    led = m.get("admitted_by")
    if not led:
        return False, ("closed: the S-3 ledger has not passed (no admitted_by in "
                       "config/crypto_sources.yaml blocks.midday_leverage)")
    p = REPO / str(led)
    if not p.is_file():
        return False, f"closed: the admitting ledger {led} does not exist"
    v = re.search(r"^\| Verdict \| \*\*(\w+)", p.read_text(encoding="utf-8"), re.M)
    word = v.group(1) if v else None
    if word != "PASS" or m.get("admitted_verdict") != "PASS":
        return False, f"closed: the admitting ledger {led} reads {word}, not PASS"
    return True, f"admitted by {led}"


def leverage_gate(ctx: dict, cfg: Optional[dict] = None,
                  db_path: Optional[str] = None) -> dict:
    """{"id", "open", "line", "why"} for midday_gate."""
    ok, why = _admission(cfg if cfg is not None else ctx.get("crypto_cfg"))
    if not ok:
        return {"id": GATE_ID, "open": False, "line": None, "why": why}
    from altdata import observations                            # noqa: PLC0415
    day = str(ctx.get("day") or "")[:10]
    cutoff = f"{day}T16:30:00+00:00"                            # 12:30 ET (EDT)
    import datetime as dt                                       # noqa: PLC0415
    oldest = (dt.date.fromisoformat(day) - dt.timedelta(days=4)).isoformat()
    with observations.ObservationStore(db_path or ctx.get("db_path")) as st:
        rows = sorted((r for r in st.as_of(FLAG_KEY, cutoff, "BTC")
                       if str(r.get("observed_at"))[:10] >= oldest),
                      key=lambda r: str(r.get("observed_at")))
    if not rows or not rows[-1].get("value_num"):
        return {"id": GATE_ID, "open": False, "line": None,
                "why": f"{why}; the newest leverage flag knowable at 12:30 is not set"}
    return {"id": GATE_ID, "open": True,
            "line": ("Crypto leverage -- crowded: BTC perp funding z above +2 with open "
                     "interest over market cap at a 90-day high (S-3). Information "
                     "only; no setup rights."),
            "why": why}
