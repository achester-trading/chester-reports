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
from altdata.sources import yfinance_source
from .writer.render_md import render_report
from .writer.build_html import build_html
from .narrative import add_narratives
from .snapshot import build_current, load_prior_snapshot, write_snapshot
from altdata import config as altconfig
from state.emit import emit

# Windows consoles default to cp1252, which cannot encode the check marks
# the report and the summary print use. Force UTF-8 on stdout.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


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
    ap.add_argument("--skip-narrative", action="store_true",
                    help="Skip the Claude narrative step even if ANTHROPIC_API_KEY is set")
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

    # Tag FRED-only counts so the appendix can report sources separately.
    fetch_summary["fred_total"] = fetch_summary["total"]
    fetch_summary["fred_success"] = fetch_summary["success"]
    fetch_summary.setdefault("mkt_total", 0)
    fetch_summary.setdefault("mkt_success", 0)

    # ---- Phase 2: pull market data (yfinance) ----
    if not args.skip_fetch:
        try:
            mkt_summary = yfinance_source.pull(store)
            log.info("yfinance fetch: %d/%d symbols succeeded",
                     mkt_summary["success"], mkt_summary["total"])
            # Merge into the FRED summary so the appendix reflects both.
            fetch_summary["total"] += mkt_summary["total"]
            fetch_summary["success"] += mkt_summary["success"]
            fetch_summary["failed"].extend(mkt_summary["failed"])
            fetch_summary["series"].update(mkt_summary["series"])
            fetch_summary["mkt_total"] = mkt_summary["total"]
            fetch_summary["mkt_success"] = mkt_summary["success"]
        except Exception:
            log.exception("yfinance fetch failed entirely; continuing with FRED data only")

    # ---- Snapshot memory: compare against the last run before rendering ----
    report_date = dt.date.today()
    try:
        current_snap = build_current(store, altconfig.FRED_SERIES)
        prior_snap = load_prior_snapshot(report_date)
        change_ctx = {"current": current_snap, "prior": prior_snap}
        if prior_snap:
            log.info("Change detection active vs %s", prior_snap.get("report_date"))
        else:
            log.info("No prior snapshot — baseline run, change lines will say so")
    except Exception:
        log.exception("Snapshot comparison failed; rendering without change lines")
        change_ctx = None

    # ---- Phase 3: render markdown ----
    log.info("Rendering markdown report for %s", report_date)
    md = render_report(store, fetch_summary, report_date, change_ctx=change_ctx)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / f"monthly_macro_{report_date.isoformat()}.md"
    md_path.write_text(md, encoding="utf-8")
    log.info("Wrote markdown: %s (%d bytes)", md_path, len(md))

    # ---- Persist this run's snapshot for next month's comparison ----
    try:
        write_snapshot(store, report_date, altconfig.FRED_SERIES)
    except Exception:
        log.exception("Could not write snapshot; next run will lack a comparison point")

    # ---- Phase 5: Claude narrative ----
    if args.skip_narrative:
        log.info("Narrative step skipped (--skip-narrative)")
    else:
        md_before = md
        try:
            md = add_narratives(md)
        except Exception:
            log.exception("Narrative step raised unexpectedly; using data-only report")
            md = md_before
        if md != md_before:
            md_path.write_text(md, encoding="utf-8")
            log.info("Rewrote markdown with narratives: %s (%d bytes)", md_path, len(md))

    # ---- Phase 3: build HTML ----
    log.info("Building styled HTML")
    html = build_html(md)
    html_path = out_dir / f"monthly_macro_{report_date.isoformat()}.html"
    html_path.write_text(html, encoding="utf-8")
    log.info("Wrote HTML: %s (%d bytes)", html_path, len(html))

    # ---- Emit state to the dashboard Worker (telemetry; never fatal) ----
    try:
        snap_series = change_ctx["current"]["series"] if change_ctx else {}
        def _v(k):
            e = snap_series.get(k) or {}
            return e.get("value")
        emit(
            report_key="monthly_macro",
            status="published",
            headline=f"Monthly Macro {report_date.isoformat()} — "
                     f"{fetch_summary['success']}/{fetch_summary['total']} series",
            detail={
                "series_ok": fetch_summary["success"],
                "series_total": fetch_summary["total"],
                "failures": [k for k, _ in fetch_summary.get("failed", [])],
                "hy_oas": _v("hy_oas"),
                "ccc_oas": _v("ccc_oas"),
                "vix": _v("vix"),
                "nfci": _v("nfci"),
                "yield_10y": _v("yield_10y"),
                "narrative": not args.skip_narrative,
            },
            as_of=report_date,
        )
    except Exception:
        log.exception("State emission raised unexpectedly; report is unaffected")

    print(f"\n✅ Report generated:")
    print(f"   {md_path}")
    print(f"   {html_path}")
    print(f"\n   FRED series populated: {fetch_summary['success']}/{fetch_summary['total']}")
    if fetch_summary.get("failed"):
        print(f"   Failed series: {len(fetch_summary['failed'])} (see appendix)")


if __name__ == "__main__":
    main()
