"""
Report generation entry point.

    python -m altdata.report                       # write to ./reports/
    python -m altdata.report --out report.md
    python -m altdata.report --monthly-fg 72       # pass Monthly Pillar-5 F&G snapshot

Reads the same Store the ingestion job writes. Intended to run after the weekly
ingest (e.g. a second step in the GitHub Action, or the report repo's own job).
"""

from __future__ import annotations

import argparse
import datetime as dt
import os

from ..store import Store
from .generate import generate_report
from .export import export_json


def main():
    ap = argparse.ArgumentParser(description="Generate the Alternative Asset Report")
    ap.add_argument("--store-dir", default=None, help="store dir (default env ALTDATA_STORE or ./data_store)")
    ap.add_argument("--out", default=None, help="markdown output path (default reports/alt-asset-report-<date>.md)")
    ap.add_argument("--json", default=None, help="also export dashboard JSON payload to this path "
                                                 "(default reports/alt-asset-data-<date>.json)")
    ap.add_argument("--no-json", action="store_true", help="skip JSON export")
    ap.add_argument("--monthly-fg", type=float, default=None,
                    help="standing Monthly Pillar-5 Fear&Greed snapshot for reconciliation")
    args = ap.parse_args()

    store = Store(args.store_dir)
    md = generate_report(store, monthly_fg_snapshot=args.monthly_fg)

    out = args.out
    if not out:
        os.makedirs("reports", exist_ok=True)
        out = os.path.join("reports", f"alt-asset-report-{dt.date.today().isoformat()}.md")
    with open(out, "w") as f:
        f.write(md)
    print(f"Wrote {out} ({len(md):,} chars)")

    if not args.no_json:
        jpath = args.json
        if not jpath:
            os.makedirs("reports", exist_ok=True)
            jpath = os.path.join("reports", f"alt-asset-data-{dt.date.today().isoformat()}.json")
        export_json(store, jpath, monthly_fg_snapshot=args.monthly_fg)
        sz = os.path.getsize(jpath)
        print(f"Wrote {jpath} ({sz:,} bytes) — load this into the dashboard")


if __name__ == "__main__":
    main()
