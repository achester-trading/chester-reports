"""python -m alpha_proposer -- one daily proposer run (see propose.py)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from alpha import config as acfg
from alpha.ledger import Ledger
from alpha.store import ReadOnlyStore

from . import propose


def _main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m alpha_proposer",
                                 description="The Alpha Lab's daily proposer")
    ap.add_argument("--as-of")
    ap.add_argument("--store")
    ap.add_argument("--ledger")
    a = ap.parse_args(argv)
    lp = Path(a.ledger) if a.ledger else acfg.ledger_path()
    lg = Ledger(lp, read_only=True) if lp.is_file() else None
    st = ReadOnlyStore(a.store)
    try:
        rec = propose.run(st, lg, a.as_of)
        # A98 (D43): the critic, after the proposer -- "why this could fail" for
        # each hypothesis without one, within its budget (0 ships: no call).
        from . import critic                                    # noqa: PLC0415
        try:
            crec = critic.run(lg, a.as_of)
            print(json.dumps({"critic": crec.get("state"), "called": crec.get("called")}))
        except Exception as exc:                                # noqa: BLE001
            print(json.dumps({"critic": f"faulted: {type(exc).__name__}"}))
    finally:
        st.close()
        if lg is not None:
            lg.close()
    print(json.dumps({k: v for k, v in rec.items() if k != "reply"}, default=str))
    return 0 if rec.get("state") in ("written", "skipped", "nothing_written") else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
