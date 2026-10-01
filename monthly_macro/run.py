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


SUBJECT = "Monthly Regime & Allocation — {date}"


def deliver_edition(stamp: str, out_dir: str = "reports") -> dict:
    """Email one ARCHIVED edition: the HTML in the body, the Markdown attached.

    Reads the files the build archived rather than taking them from memory, so
    what is mailed is byte-identical to the record and a past edition can be
    re-sent (--deliver-only) without rebuilding it -- a rebuild would call the
    model again and rewrite the snapshot next month compares against.

    The same transport as the Weekly and the 16:45 close: daily_cascade/deliver,
    which reads the SMTP credentials the heartbeat's alert path uses. Never
    raises. Prints ONE greppable line for run_monthly.sh's log:
        delivery=smtp ok       sent
        delivery=smtp failed   anything else, with the named state and detail
    """
    d = Path(out_dir)
    md_name, html_name = f"monthly_macro_{stamp}.md", f"monthly_macro_{stamp}.html"
    try:
        md = (d / md_name).read_text(encoding="utf-8")
        html = (d / html_name).read_text(encoding="utf-8")
    except OSError as exc:
        state, detail = "archive_missing", f"{type(exc).__name__}: {exc}"
    else:
        state, detail = delivery.send_html(
            SUBJECT.format(date=stamp), html,
            text_fallback=md, attachments=[(md_name, md, "markdown")])
    ok = state == "sent"
    print(f"delivery=smtp {'ok' if ok else 'failed'} state={state} -- {detail}",
          flush=True)
    return {"delivery": state, "delivery_detail": detail,
            "delivered_at": session.utc_iso()}


def write_prose(p: dict, args, log) -> dict:
    """One audited call per v2 section; the results are kept ON the payload, so
    the archive records what was written, what was withheld and why."""
    from . import prose as prose_mod
    out = prose_mod.write_all(p, model=args.narrative_model)
    total = sum(r.get("words") or 0 for r in out.values())
    held = [k for k, r in out.items() if not r.get("published")]
    log.info("prose: %d section(s), %d published, %d words%s", len(out),
             len(out) - len(held), total,
             f"; withheld: {', '.join(held)}" if held else "")
    for k in held:
        log.warning("  section %s withheld: %s", k, out[k].get("reason"))
    p["prose"] = {k: {kk: r.get(kk) for kk in ("title", "state", "published",
                                               "words", "reason", "model", "text",
                                               "rejected_text")}
                  for k, r in out.items()}
    return out


def rerender(args, log) -> int:
    """Re-render an archived payload. Builds nothing it already has.

    A payload archived before a section existed (the 1 Oct edition predates
    Monthly v2) gets that section built AT THE PAYLOAD'S OWN CUTOFF, so the
    re-render reads what was knowable then, not what is knowable now. The
    paragraph is written again through the same audited step, over the same
    narrative payload; --skip-narrative leaves it out.

    --dry-run writes <name>_dryrun.md/.html and NEVER delivers. Without it the
    re-render is archived under the edition's own names -- which replaces the
    record -- so a re-render that is not a dry run is refused here.
    """
    if not args.dry_run:
        print("refused: --from-payload re-renders only as --dry-run; it never "
              "replaces an archived edition or sends one", file=sys.stderr)
        return 1
    p = json.loads(Path(args.from_payload).read_text(encoding="utf-8"))
    from . import v2
    added = []
    if p.get("month_in_markets") is None:
        # Any edition from before the current v2 shape -- a 4b payload, or a
        # Phase A one without the scorecard -- gets the v2 sections rebuilt at
        # its own cutoff, all together, so they agree with each other.
        p.update(payload_mod.v2_sections(p))
        added = list(v2.V2_SECTIONS)
        p["sections"] = list(payload_mod.SECTIONS)
    from daily_cascade import precision
    p = precision.apply(p)
    log.info("re-rendering %s (cutoff %s); built at its cutoff: %s",
             args.from_payload, p.get("as_of"), ", ".join(added) or "nothing")
    prose = None
    if not args.skip_narrative:
        prose = write_prose(p, args, log)
    md = render_v2.render(p, prose=prose)
    stamp = p.get("report_date")
    md_path = delivery.archive(md, f"monthly_macro_{stamp}_dryrun.md", args.out_dir)
    # The dry run's payload, prose and rejected sections included, for reading.
    delivery.archive(json.dumps(p, indent=2, default=str, sort_keys=True),
                     f"monthly_macro_{stamp}_dryrun_payload.json", args.out_dir)
    html_path = delivery.archive(build_html(md), f"monthly_macro_{stamp}_dryrun.html",
                                 args.out_dir)
    if prose:
        print("prose by section (words; withheld sections say why):")
        for k, r in prose.items():
            print(f"   {k:<34} {'published' if r.get('published') else 'WITHHELD'}"
                  f"  {r.get('words') or 0:>5}"
                  + ("" if r.get("published") else f"  -- {r.get('reason')}"))
        print(f"   {'TOTAL':<34} {'':9}  "
              f"{sum(r.get('words') or 0 for r in prose.values()):>5}")
    cov = (p.get("looking_ahead") or {}).get("coverage") or []
    if cov:
        print("calendar coverage (present / missing, by window):")
        for c in cov:
            cells = []
            for wname, w in c["windows"].items():
                if "have" in w:
                    cells.append(f"{wname}: {', '.join(w['have']) or 'none'}"
                                 + (f" (missing {', '.join(w['missing'])})"
                                    if w.get("missing") else ""))
                else:
                    cells.append(f"{wname}: {'present' if w['present'] else 'MISSING'}")
            print(f"   {c['item']:<30} {' | '.join(cells)}"
                  + (f"  -- free source: {c['free_source']}" if c.get("free_source")
                     and not any(w['present'] for w in c['windows'].values())
                     else ""))
    print(f"dry run -- NOT delivered:\n   {md_path}\n   {html_path}")
    print("delivery=skipped (--dry-run)")
    return 0


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
    ap.add_argument("--no-deliver", action="store_true",
                    help="Build and archive only; send nothing (the GitHub "
                         "workflow fallback, which has no SMTP and uploads "
                         "the files as an artifact instead)")
    ap.add_argument("--deliver-only", default=None, metavar="YYYY-MM-DD",
                    help="Send an already-archived edition and build nothing")
    ap.add_argument("--from-payload", default=None, metavar="PATH",
                    help="Re-render an ARCHIVED payload instead of building one; "
                         "sections it predates are built at ITS cutoff")
    ap.add_argument("--dry-run", action="store_true",
                    help="Write <name>_dryrun.md/.html and send nothing")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    setup_logging(args.verbose)
    log = logging.getLogger("monthly_macro")

    # EXIT CODES, the Weekly's: 0 built and delivered (or --no-deliver), 1 the
    # run failed, 2 built and ARCHIVED but not delivered. A delivery failure
    # never fails the build -- the report exists on disk -- but rc=2 reaches
    # run_monthly.sh, which records not_delivered where the heartbeat reads it.
    if args.deliver_only:
        out = deliver_edition(args.deliver_only, args.out_dir)
        return 0 if out["delivery"] == "sent" else 2
    if args.from_payload:
        return rerender(args, log)

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
    # inputs printed beneath the dial each one feeds. render_md.py, which carried
    # the ten placeholders, is deleted rather than kept for parts: a renderer
    # nothing calls is a second answer waiting for somebody to call it.
    run_id = session.new_run_id("monthly")
    log.info("Building the payload as-of %s", args.as_of or "now")
    p = payload_mod.build(args.as_of, run_id=run_id)
    for w in p.get("warnings") or []:
        log.warning("payload absence -- %s", w)

    # ---- Phase 5: the prose, audited ------------------------------------------
    # v2: one audited call per section (monthly_macro.prose). The single
    # paragraph below remains only for a payload without the v2 sections.
    narr = None
    prose = None
    if args.skip_narrative:
        log.info("Narrative step skipped (--skip-narrative)")
    elif p.get("month_in_markets") is not None:
        prose = write_prose(p, args, log)
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

    md = render_v2.render(p, narrative=narr, prose=prose)
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

    # ---- DELIVER, LAST: everything above is on disk before a socket opens ----
    if args.no_deliver:
        print("delivery=skipped (--no-deliver)")
        return 0
    out = deliver_edition(stamp, args.out_dir)
    return 0 if out["delivery"] == "sent" else 2


if __name__ == "__main__":
    sys.exit(main())
