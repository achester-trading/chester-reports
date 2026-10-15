"""
The research workbench's command line (X-2.9).

    python -m alpha.research new FILE.yaml [--source operator|chat]
    python -m alpha.research run HYP-0007 [--as-of ISO]
    python -m alpha.research report HYP-0007 [--out DIR]
    python -m alpha.research list [--status S]

Every command takes --store (the observation store, opened read-only) and
--ledger (alpha.db). `new` pre-registers now; `run` puts a registered rule
through the harness; `report` writes alpha/research/reports/<id>.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from ..ledger import Ledger
from ..store import ReadOnlyStore
from . import workbench


def _main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m alpha.research",
                                 description="The Alpha Lab's research workbench")
    ap.add_argument("--store")
    ap.add_argument("--ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new", help="pre-register ideas from a YAML file, now")
    n.add_argument("file")
    n.add_argument("--source", default="operator", choices=("operator", "chat"))
    r = sub.add_parser("run", help="put a registered rule through the harness")
    r.add_argument("id")
    r.add_argument("--as-of")
    p = sub.add_parser("report", help="write the one-page verdict")
    p.add_argument("id")
    p.add_argument("--out")
    ls = sub.add_parser("list", help="the register")
    ls.add_argument("--status")
    a = ap.parse_args(argv)
    with Ledger(a.ledger) as lg:
        if a.cmd == "list":
            from ..hypotheses import Register                   # noqa: PLC0415
            for h in Register(lg).all([a.status] if a.status else None):
                print(f"{h['id']}  {h['status']:<12} {h['family']:<16} {h['title']}")
            return 0
        if a.cmd == "report":
            print(workbench.report(lg, a.id, a.out))
            return 0
        st = ReadOnlyStore(a.store)
        try:
            if a.cmd == "new":
                doc = yaml.safe_load(Path(a.file).read_text(encoding="utf-8"))
                out = workbench.new(lg, st, doc, a.source, file_name=Path(a.file).name)
                print(json.dumps(out, indent=2))
                return 0
            try:
                out = workbench.run(lg, st, a.id, a.as_of)
            except workbench.QueuedForSitting as exc:
                print(str(exc))
                return 2
            print(f"{out['id']}: {out['status']} -- {out['reason']}")
            return 0
        finally:
            st.close()


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
