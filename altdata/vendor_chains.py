"""
The vendor chains' own capture, 16:31 ET -- M-3, the Massive capture clock (ruled
18 Oct 2026; a43-render).

    python -m altdata.vendor_chains run        # SPX and SPCX, the 16:16 ET data

WHY ITS OWN UNIT. Massive Options Starter is 15-minute delayed and SPX options
trade to 16:15 ET, so the vendor leg of the 16:10 EOD pass read 15:55 data. That
leg moved here: chester-vendor-chains.service and .timer at 16:31 ET on weekdays
(scripts/run_dealer_capture.sh chains), which reads the 16:16 data -- after the
SPX close and before the 16:45 close report. It writes the same chain files to
the same directory as before (altdata.sources.massive_chain.write_snapshot), and
run_eod.py skips the vendor universe and says so in its log.

Every row and manifest carries its data's as-of, "16:16 ET (15-minute delay)";
the 09:45 and 12:30 captures stamp theirs "09:30 ET" and "12:15 ET" the same way.
Open interest is the prior settlement's whatever the clock, so nothing is
backfilled.

THE CLOSE'S READ. This writes its own record, _vendor_completeness.json, beside
the EOD pass's _completeness.json rather than into it (two writers, one file);
altdata.chain_completeness.read_completeness merges it, and a 16:45 read that
finds no vendor record yet says so rather than calling SPX missing.

Exit codes: 0 a vendor chain captured, 1 none.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Optional

from . import chain_completeness, config, session

log = logging.getLogger(__name__)


def run(pull=None, base_dir: Optional[str] = None, day: Optional[str] = None) -> dict:
    """The vendor universe at the 16:31 clock. `pull` defaults to
    altdata.sources.massive_chain.pull; the gate passes a fake."""
    universe = config.massive_universe()
    as_of = config.vendor_as_of(config.VENDOR_CHAINS_SLOT)
    if pull is None:
        from .sources import massive_chain                     # noqa: PLC0415
        pull = massive_chain.pull
    s = pull(symbols=universe, base_dir=base_dir, data_as_of=as_of)
    rec = chain_completeness.vendor_record(s, universe, as_of)
    where = chain_completeness.write_vendor(rec, day or session.session_date(), base_dir)
    log.info("vendor chains (%s): %d/%d, data as of %s -> %s", ", ".join(universe),
             len(rec["captured"]), len(universe), as_of, where)
    return {"captured": rec["captured"], "missing": rec["missing"], "data_as_of": as_of,
            "record": str(where) if where else None}


def _main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m altdata.vendor_chains")
    ap.add_argument("cmd", choices=["run"])
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    res = run()
    print(json.dumps(res, indent=2, default=str))
    return 0 if res["captured"] else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
