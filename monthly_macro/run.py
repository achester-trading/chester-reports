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
import json
import logging
import os
import sys
from pathlib import Path

from altdata.store import Store
from altdata.sources import fred as fred_source
from altdata.sources import yfinance_source
from .writer.build_html import build_html
from .writer import render_v2
from . import payload as payload_mod
from .narrative import MAX_CHARS, TEMPLATE_PATH, monthly_system_prompt
from .snapshot import build_current, load_prior_snapshot, write_snapshot
from altdata import config as altconfig
from altdata import session
from state.emit import emit
from daily_cascade import deliver as delivery
from daily_cascade import narrative as narrative_mod

# Windows consoles default to cp1252, which cannot encode the check marks
# the report prints or the em-dashes the log lines use. Force UTF-8 on
# both streams (logging writes to stderr).
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


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
    ap.add_argument("--as-of", default=None,
                    help="Point-in-time cutoff; the payload reads only what was "
                         "knowable then, which is what makes a past month "
                         "replayable")
    ap.add_argument("--narrative-model", default=None,
                    help="Override the pinned model (recorded on the artifact)")
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
    report_date = session.session_date_obj()
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

    # ---- Phase 3: the payload, then the document ------------------------------
    #
    # SIX SECTIONS OF CHANGE, READING THE OBJECT. The old path rendered ten pillar
    # pages of levels from the store and asked a model to characterise the regime
    # from them; the regime now comes from regime.latest() and the pillars are
    # inputs printed beneath the dial each one feeds. render_md.py is kept for its
    # masthead and appendix helpers and is no longer the report.
    run_id = session.new_run_id("monthly")
    log.info("Building the payload as-of %s", args.as_of or "now")
    p = payload_mod.build(args.as_of, run_id=run_id)
    for w in p.get("warnings") or []:
        log.warning("payload absence -- %s", w)

    # ---- Phase 5: the paragraph, audited ---------------------------------------
    narr = None
    if args.skip_narrative:
        log.info("Narrative step skipped (--skip-narrative)")
    else:
        np_ = payload_mod.narrative_payload(p)
        narr = narrative_mod.generate(
            np_, model=args.narrative_model,
            system_prompt=monthly_system_prompt(),
            guide_path=TEMPLATE_PATH,
            # Long form, like the weekly: a month that had several things in it
            # needs several paragraphs, and the ceiling is a runaway guard.
            max_chars=MAX_CHARS, one_paragraph=False)
        if narr.published:
            log.info("narrative published: %d figures audited, model=%s",
                     narr.figures_checked, narr.model)
        else:
            log.warning("narrative withheld (state=%s, model=%s): %s",
                        narr.state, narr.model, narr.reason)
            if narr.unmatched:
                log.warning("  unmatched figures: %s", ", ".join(narr.unmatched))
            if narr.rejected_text:
                log.info("  rejected paragraph (NOT published): %s",
                         narr.rejected_text)

    md = render_v2.render(p, narrative=narr)
    html = build_html(md)

    # ---- ARCHIVE THROUGH deliver(), like every other report -------------------
    # run.py used to write both files with Path.write_text, which is the Windows
    # encoding bug CLAUDE.md records: the default codec on a local run cannot encode
    # the report's own check marks. delivery.archive() writes explicit UTF-8 and is
    # the one archive path in the system.
    stamp = p.get("report_date")
    md_path = delivery.archive(md, f"monthly_macro_{stamp}.md", args.out_dir)
    pay_path = delivery.archive(
        json.dumps(p, indent=2, default=str, sort_keys=True),
        f"monthly_macro_{stamp}_payload.json", args.out_dir)
    html_path = delivery.archive(html, f"monthly_macro_{stamp}.html", args.out_dir)
    log.info("archived %s, %s and the payload %s", md_path, html_path, pay_path)

    # ---- Persist this run's snapshot for next month's comparison ----
    try:
        write_snapshot(store, report_date, altconfig.FRED_SERIES)
    except Exception:
        log.exception("Could not write snapshot; next run will lack a comparison point")

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
