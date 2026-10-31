"""
python -m paper_exec status                      # never connects
python -m paper_exec run [--ledger PATH]         # by hand, on the box; dry unless
                                                 # the operator set both flags
python -m paper_exec clear-kill --reason "..."   # the operator's, after a kill

`run` and `clear-kill` are on the deny list: a session never runs them.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from . import config as pcfg
from .state import State


def status_lines(cfg: dict) -> list[str]:
    mode = pcfg.mode(cfg)
    if mode == "off":
        return ["paper executor off"]
    st = State(pcfg.state_dir(cfg))
    out = [f"paper executor {mode}" + (" (built and logged, nothing sent)" if mode == "dry"
                                       else " (sending to the paper account)"),
           f"port {cfg.get('port')}, paper accounts only ({cfg.get('paper_account_prefix')}...)"]
    k = st.killed()
    out.append(f"KILLED since {k.get('at')} ({k.get('by')}); the operator clears it"
               if k else "kill switch: clear")
    rb = st.reconcile_block()
    out.append("reconciliation: STOPPED -- " + "; ".join(rb.get("mismatches") or [])
               if rb else "reconciliation: no block")
    for eng, p in st.pauses().items():
        out.append(f"PAUSED {eng} since {p.get('at')}: last {p.get('n')} paper trades "
                   f"mean {p.get('paper_mean'):+.4f} against backtest "
                   f"{p.get('backtest_mean'):+.4f}, shortfall {p.get('shortfall'):+.4f} "
                   f"= {p.get('z'):+.2f} standard errors; the operator resumes it")
    return out


def _main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m paper_exec")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    r = sub.add_parser("run")
    r.add_argument("--ledger")
    c = sub.add_parser("clear-kill")
    c.add_argument("--reason", required=True)
    a = ap.parse_args(argv)
    cfg = pcfg.load()
    if a.cmd == "status":
        print("\n".join(status_lines(cfg)))
        return 0
    if a.cmd == "clear-kill":
        was = State(pcfg.state_dir(cfg)).clear_kill(a.reason)
        print("kill cleared" if was else "no kill state; the clear is recorded")
        return 0
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if pcfg.mode(cfg) == "off":
        print("paper executor off")
        return 0
    from alpha import config as acfg                            # noqa: PLC0415
    from alpha.ledger import Ledger                             # noqa: PLC0415
    from . import executor                                      # noqa: PLC0415
    with Ledger(Path(a.ledger) if a.ledger else acfg.ledger_path()) as lg:
        rep = executor.run(executor.intents_from_ledger(lg, cfg), cfg, lg)
    print(json.dumps(rep, indent=1, default=str))
    return 0 if rep.get("state") in ("done", "paper executor off") else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
