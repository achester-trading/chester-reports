"""
The intraday dealer captures, 09:45 and 12:30 ET (6b part 2; brief v2,
Captures; ratified 16 Oct 2026: from the sources the box already has).

    python -m altdata.dealer_capture run --slot 0945
    python -m altdata.dealer_capture run --slot 1230      # then the 12:30 gates

WHAT IT DOES. Snapshots the chains -- Yahoo for the options universe, Massive
for SPX and SPCX (ingestion only: their Greeks stay deferred behind the solver
gate, as at 16:10) -- and computes the engine's exposure JSON from EACH SNAPSHOT
IT JUST WROTE (not the snapshot closest to the settlement time, which is what
the 16:10 pass picks), written beside the 16:10 profiles. Open interest is the
prior close's vintage in every capture (`oi_vintage: prior_close`): OCC
publishes it once a day, so an intraday capture carries today's IV and spot on
yesterday's OI. The release ladder stays the 16:10 pass's: nothing here appends
to it.

THE 12:30 SLOT computes and evaluates the gates only (daily_cascade/
midday_gate.py) and calls no model unless a gate opens -- the cadence
document's rule (Audit #3 section I: "the 12:30 chain capture keeps running for
data and feeds an alert only").

Run by scripts/run_dealer_capture.sh from chester-dealer-0945 / -1230 (deploy/
systemd). Enabling those timers is the operator's.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from . import config, session

log = logging.getLogger("altdata.dealer_capture")
SLOTS = ("0945", "1230")


def _engine():
    tools = str(Path(__file__).resolve().parent.parent / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import exposure_compute                                     # noqa: PLC0415
    return exposure_compute


def compute_written(summary: dict, symbols: list[str], out_dir: Optional[str] = None,
                    run_id: Optional[str] = None) -> dict:
    """The engine over each symbol's just-written snapshot; {symbol: path or
    error}. One bad symbol never ends the run."""
    ec = _engine()
    out: dict[str, str] = {}
    for sym in symbols:
        entry = (summary.get("symbols") or {}).get(sym) or {}
        path = entry.get("csv")
        if not path:
            out[sym] = "no snapshot written"
            continue
        try:
            res = ec.compute_symbol(ec.load_chain(Path(path)), sym)
            if run_id:
                res["run_id"] = run_id
            res["source_chain"] = str(path)
            res["computed_path"] = str(ec.write_computed(res, out_dir))
            out[sym] = res["computed_path"]
        except Exception as exc:                                # noqa: BLE001
            log.exception("compute failed for %s", sym)
            out[sym] = f"{type(exc).__name__}: {exc}"
    return out


def run(slot: str, symbols: Optional[list[str]] = None, pull=None, vendor_pull=None,
        out_dir: Optional[str] = None) -> dict:
    """One capture. `pull` and `vendor_pull` default to the box's two sources
    (altdata.sources.options_chain and .massive_chain); the gate passes fakes."""
    if slot not in SLOTS:
        raise ValueError(f"slot must be one of {SLOTS}")
    universe = symbols or config.options_universe()
    vendor = [] if symbols else config.massive_universe()
    if pull is None:
        from .sources import options_chain                     # noqa: PLC0415
        pull = options_chain.pull
    run_id = session.new_run_id(f"dealer_capture_{slot}")
    summary = pull(symbols=universe)
    computed = compute_written(summary, universe, out_dir, run_id)
    vendor_summary = None
    if vendor:
        if vendor_pull is None:
            from .sources import massive_chain                 # noqa: PLC0415
            vendor_pull = massive_chain.pull
        try:
            vendor_summary = vendor_pull(symbols=vendor)
        except Exception as exc:                                # noqa: BLE001
            log.exception("vendor capture failed; the Yahoo chains are safe")
            vendor_summary = {"error": f"{type(exc).__name__}: {exc}"}
    out = {"slot": slot, "run_id": run_id, "captured": summary.get("success"),
           "total": summary.get("total"), "computed": computed,
           "vendor": (None if vendor_summary is None else
                      vendor_summary.get("error") or vendor_summary.get("success"))}
    if slot == "1230":
        from daily_cascade import midday_gate                   # noqa: PLC0415
        out["gates"] = midday_gate.run(session.session_date(), out_dir)
    return out


def _main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m altdata.dealer_capture")
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--slot", required=True, choices=SLOTS)
    ap.add_argument("--symbols", nargs="*")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    res = run(a.slot, a.symbols)
    print(json.dumps(res, indent=2, default=str))
    ok = res.get("captured") and any(not str(v).startswith(("no ", "Error"))
                                     and v.endswith(".json")
                                     for v in res["computed"].values())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
