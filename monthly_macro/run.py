"""
Monthly Macro Report — main entry point.

Usage:
    python -m monthly_macro.run                 # pull + write to ./reports/
    python -m monthly_macro.run --skip-fetch    # use existing store, only render
    python -m monthly_macro.run --out-dir custom-dir

Reads FRED_API_KEY from environment. The store is at $ALTDATA_STORE
(default ./data_store).
"""

from __future__ import annotations
import argparse
import datetime as dt
import logging
import os
import sys
from pathlib import Path

from altdata.store import Store
from altdata.sources import fred as fred_source
from .writer.render_md import render_report
from .writer.build_html import build_html


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    ap = argparse.ArgumentParser(description="Generate the Monthly Macro Report")
    ap.add_argument("--skip-fetch", action="store_true",
                    help="Skip FRED fetch (use existing store)")
    ap.add_argument("--out-dir", default="reports",
                    help="Where to write the report files (default: reports/)")
    ap.add_argument("--lookback-days", type=int, default=1500,
                    help="FRED history to pull, in days (default: 1500 ~= 4 years)")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    setup_logging(args.verbose)
    log = logging.getLogger("monthly_macro")

    store = Store()
    log.info("Store directory: %s", store.dir)

    # ---- Phase 1: pull FRED ----
    if args.skip_fetch:
        log.info("Skipping fetch; using existing store")
        # Stub a minimal summary so the writer's appendix has something
        keys = store.list_keys()
        fetch_summary = {
            "total": len(keys),
            "success": len(keys),
            "failed": [],
            "series": {},
        }
    else:
        try:
            fetch_summary = fred_source.pull(store, lookback_days=args.lookback_days)
            log.info("FRED fetch: %d/%d series succeeded", fetch_summary["success"], fetch_summary["total"])
            if fetch_summary["failed"]:
                log.warning("Failures: %s", [f[0] for f in fetch_summary["failed"]])
        except Exception as e:
            log.exception("FRED fetch failed")
            print(f"\nERROR: FRED fetch failed: {e}", file=sys.stderr)
            print("Check that FRED_API_KEY is set and valid.", file=sys.stderr)
            sys.exit(1)

    # ---- Phase 2: render markdown ----
    report_date = dt.date.today()
    log.info("Rendering markdown report for %s", report_date)
    md = render_report(store, fetch_summary, report_date)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / f"monthly_macro_{report_date.isoformat()}.md"
    md_path.write_text(md)
    log.info("Wrote markdown: %s (%d bytes)", md_path, len(md))

    # ---- Phase 3: build HTML ----
    log.info("Building styled HTML")
    html = build_html(md)
    html_path = out_dir / f"monthly_macro_{report_date.isoformat()}.html"
    html_path.write_text(html)
    log.info("Wrote HTML: %s (%d bytes)", html_path, len(html))

    print(f"\n✅ Report generated:")
    print(f"   {md_path}")
    print(f"   {html_path}")
    print(f"\n   FRED series populated: {fetch_summary['success']}/{fetch_summary['total']}")
    if fetch_summary.get("failed"):
        print(f"   Failed series: {len(fetch_summary['failed'])} (see appendix)")


if __name__ == "__main__":
    main()
