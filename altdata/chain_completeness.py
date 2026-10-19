"""The EOD capture's completeness record (AUD-1 item 5c, the audit of 14 Oct 2026).

Written by run_eod.py beside the day's chains, read by the 16:45 close, which
prints the gap. It lives here rather than in run_eod.py so the close can read it
without importing the capture.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from . import config

# THE COMPLETENESS GATE (AUD-1 item 5c, the audit of 14 Oct 2026). A capture
# that came back with most of the universe was a green run: nothing said which
# symbols or expiries were missing until a reader found a hole. So the capture
# counts what it got against what it expected -- symbols, and the expiries each
# symbol listed -- and a capture below either floor fails with a NAMED exit (5,
# incomplete) and no heartbeat touch. The record is written beside the chains as
# _completeness.json, where the close reads it and prints the gap. Massive's
# vendor symbols count SEPARATELY: they are additive, so a missing SPX chain is
# named in the close but does not fail the yfinance capture.
EXIT_INCOMPLETE = 5
MIN_EXPIRY_SHARE = 0.90
COMPLETENESS_FILE = "_completeness.json"
# M-3: the 16:31 vendor capture's own record, merged at read.
VENDOR_FILE = "_vendor_completeness.json"
VENDOR_PENDING = ("not yet captured at the read (chester-vendor-chains runs at "
                  "16:31 ET)")


def completeness(yf_summary: dict, universe: list[str],
                 vendor_summary: Optional[dict] = None,
                 vendor_universe: Optional[list[str]] = None) -> dict:
    """The capture against what it should have been. ok is False below
    len(universe) - 1 symbols (12 of 13) or MIN_EXPIRY_SHARE of the expiries the
    captured symbols listed."""
    syms = (yf_summary or {}).get("symbols") or {}
    got = [s for s in universe if (syms.get(s) or {}).get("rows")]
    missing = [s for s in universe if s not in got]
    listed = sum(int((syms.get(s) or {}).get("expiries_fetched")
                     or (syms.get(s) or {}).get("expiries_listed") or 0) for s in got)
    with_rows = sum(int((syms.get(s) or {}).get("expiries_with_rows") or 0) for s in got)
    share = (with_rows / listed) if listed else 0.0
    need = max(1, len(universe) - 1)
    short = {s: f"{(syms.get(s) or {}).get('expiries_with_rows', 0)} of "
                f"{(syms.get(s) or {}).get('expiries_fetched') or (syms.get(s) or {}).get('expiries_listed', 0)}"
             for s in got
             if int((syms.get(s) or {}).get("expiries_with_rows") or 0)
             < int((syms.get(s) or {}).get("expiries_fetched")
                   or (syms.get(s) or {}).get("expiries_listed") or 0)}
    out = {"symbols_expected": len(universe), "symbols_captured": len(got),
           "symbols_missing": missing, "symbols_floor": need,
           "expiries_expected": listed, "expiries_captured": with_rows,
           "expiry_share": round(share, 4), "expiry_floor": MIN_EXPIRY_SHARE,
           "expiries_short": short,
           "ok": len(got) >= need and share >= MIN_EXPIRY_SHARE}
    vu = list(vendor_universe or [])
    if vu:
        vs = (vendor_summary or {}).get("symbols") or {}
        out["vendor"] = {
            "expected": vu,
            "captured": [s for s in vu if (vs.get(s) or {}).get("rows")],
            "missing": [s for s in vu if not (vs.get(s) or {}).get("rows")],
            "key_missing": bool((vendor_summary or {}).get("key_missing"))}
    return out


def vendor_record(vendor_summary: dict, universe: list[str], data_as_of: str) -> dict:
    vs = (vendor_summary or {}).get("symbols") or {}
    return {"expected": list(universe),
            "captured": [s for s in universe if (vs.get(s) or {}).get("rows")],
            "missing": [s for s in universe if not (vs.get(s) or {}).get("rows")],
            "key_missing": bool((vendor_summary or {}).get("key_missing")),
            "data_as_of": data_as_of}


def write_vendor(rec: dict, day: str, base_dir: Optional[str] = None) -> Optional[Path]:
    d = Path(base_dir or config.CHAIN_DIR) / day
    try:
        d.mkdir(parents=True, exist_ok=True)
        p = d / VENDOR_FILE
        p.write_text(json.dumps(rec, indent=1, sort_keys=True), encoding="utf-8")
        return p
    except OSError:
        return None


def gap_lines(rec: dict) -> list[str]:
    """The record as the close prints it: one line per gap, none when complete."""
    out = []
    if rec.get("symbols_missing"):
        out.append(f"chains missing for {', '.join(rec['symbols_missing'])} "
                   f"({rec['symbols_captured']} of {rec['symbols_expected']} captured)")
    if rec.get("expiries_expected") and rec.get("expiry_share", 1) < rec.get("expiry_floor", 0.9):
        out.append(f"only {rec['expiries_captured']} of {rec['expiries_expected']} "
                   f"listed expiries captured ({rec['expiry_share']:.0%}, floor "
                   f"{rec['expiry_floor']:.0%})")
    v = rec.get("vendor") or {}
    if v.get("pending"):
        out.append(f"vendor chains {', '.join(v.get('expected') or [])}: {VENDOR_PENDING}")
    elif v.get("missing"):
        why = " (the Massive key is not set)" if v.get("key_missing") else ""
        out.append(f"vendor chains missing: {', '.join(v['missing'])}{why}")
    return out


def write_completeness(rec: dict, day: str,
                       base_dir: Optional[str] = None) -> Optional[Path]:
    d = Path(base_dir or config.CHAIN_DIR) / day
    try:
        d.mkdir(parents=True, exist_ok=True)
        p = d / COMPLETENESS_FILE
        p.write_text(json.dumps(rec, indent=1, sort_keys=True), encoding="utf-8")
        return p
    except OSError:
        return None




def read_completeness(day: str, base_dir: Optional[str] = None) -> Optional[dict]:
    """The day's record, or None when the capture wrote none (a day before AUD-1,
    or a capture that never started)."""
    p = Path(base_dir or config.CHAIN_DIR) / day / COMPLETENESS_FILE
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    # M-3: the vendor record arrives at 16:31 from its own unit. Merged when it is
    # there; when it is not, the read says it is pending, never missing. A record
    # from before M-3 (its vendor section written by the EOD pass) is kept.
    try:
        rec["vendor"] = json.loads((p.parent / VENDOR_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        if not rec.get("vendor") and config.massive_universe():
            rec["vendor"] = {"expected": config.massive_universe(), "pending": True}
    return rec
