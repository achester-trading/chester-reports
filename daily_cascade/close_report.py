"""
The 16:45 close debrief. D4c — the first Daily Cascade run to exist as code.

    python -m daily_cascade.close_report              # build, archive, send
    python -m daily_cascade.close_report --dry-run    # build and archive only
    python -m daily_cascade.close_report --session 2026-09-04

WHY THIS ONE FIRST (32.4). Its inputs are computed half an hour earlier by
the EOD pass, so it fetches nothing and cannot fail for a reason the report
layer owns. That makes it the cheapest possible end-to-end proof of the chain:
payload -> render -> deliver -> archive -> state record. The other eight runs
are payload configuration against a pipeline this one has already proven.

WHY IT CONTAINS NO SENTENCES (32.5). Narrative arrives at D4e, gated on D3's
numeral audit. Until something can FAIL a block for containing a number that is
not in its payload, the safe version of this report is the one with no prose to
audit. A Daily that can invent a number is worse than no Daily.

EXIT CODES. The report is the product; delivery is transport.
    0  report built (and delivered, or deliberately not sent)
    1  no payload worth sending -- nothing computed for the session
    2  built and archived, but delivery failed

2 is deliberately not 0 and deliberately not 1. The work survived and is on
disk; what failed is the part that puts it in front of a human. The unit maps
0 and 2 to success so the timer keeps its schedule, and the state record
carries the distinction for anything that wants to act on it.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import session                      # noqa: E402
from daily_cascade import deliver as delivery    # noqa: E402
from daily_cascade import payload as payload_mod  # noqa: E402
from daily_cascade import render as render_mod   # noqa: E402
from state.emit import emit                      # noqa: E402

log = logging.getLogger("daily_cascade.close")

REPORT_KEY = "daily_cascade"

# THE GRADES WATERMARK -- how "graded since the prior run" knows what the prior
# run was.
#
# Not "graded today". A grade written on a Saturday by a manual run must appear in
# Monday's report rather than vanishing because the calendar turned over, and a
# report that ran twice in one session must not show the same grades twice. So the
# high-water mark of graded_at is recorded after each successful render and read
# back on the next one.
#
# It lives beside the other box state, under CHESTER_STATE_DIR, because it is a
# fact about this box's reporting history and not about the repository. A missing
# file means "never reported", which correctly shows everything graded so far.
def _watermark_path() -> Path:
    base = os.environ.get("CHESTER_STATE_DIR") or str(Path.home() / ".chester")
    return Path(base) / "close_grades_watermark"


def _read_watermark():
    try:
        text = _watermark_path().read_text(encoding="utf-8").strip()
        return text or None
    except OSError:
        return None


def _write_watermark(grades: dict) -> None:
    """Record the newest graded_at this report actually showed.

    Taken from the grades block itself rather than from the clock: the watermark
    has to be the last thing REPORTED, not the moment of reporting, or a grade
    written between the read and the write would be skipped forever.
    """
    rows = (grades or {}).get("new_since") or []
    newest = max((r.get("graded_at") or "" for r in rows), default="")
    if not newest:
        return
    try:
        p = _watermark_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(newest, encoding="utf-8")
    except OSError as exc:
        log.warning("could not record the grades watermark: %s", exc)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--session", help="Session to report (default: newest scored)")
    ap.add_argument("--as-of", help="Point-in-time cutoff (default: now)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Build and archive; send nothing")
    ap.add_argument("--no-emit", action="store_true",
                    help="Skip the dashboard state record")
    ap.add_argument("--no-narrative", action="store_true",
                    help="Ship the data-only edition; attempt no paragraph")
    ap.add_argument("--narrative-model", default=None,
                    help="Override the pinned model (recorded on the artifact)")
    ap.add_argument("--archive-dir", help="Override the archive directory")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    run_id = session.new_run_id("daily_close")
    p = payload_mod.build(sess=args.session, as_of=args.as_of, run_id=run_id,
                          grades_since=_read_watermark())
    sess = p["session"]

    print(f"close debrief -- session {sess}")
    print(f"  run id     : {run_id}")
    print(f"  exposure   : {len(p['exposure'])} symbols "
          f"({len(p['exposure_missing'])} not in the table)")
    print(f"  pins       : {len(p['pins'])} rows, hits {p['pin_hits']}")
    print(f"  portfolio  : {p['portfolio']['state']}")
    gr = p.get("grades") or {}
    print(f"  grades     : {gr.get('state')}, {gr.get('total', 0)} graded, "
          f"{len(gr.get('new_since') or [])} new since "
          f"{gr.get('since') or 'the beginning'}")
    for w in p["warnings"]:
        print(f"  WARNING    : {w}")

    # An empty payload is not a report. Sending one would teach the reader that
    # the mail sometimes means nothing, which is how a daily report stops being
    # read at all.
    if not p["exposure"] and not p["pins"]:
        print("\nNothing computed for this session; no report sent.")
        if not args.no_emit:
            emit(REPORT_KEY, "error",
                 headline=f"no payload for {sess}",
                 detail={"run_id": run_id, "warnings": p["warnings"]},
                 as_of=_as_date(sess))
        return 1

    # THE PARAGRAPH, AND THE GATE IT PASSES THROUGH.
    #
    # Imported here rather than at module scope so the data path stays clean: the
    # no-prose gate asserts, in a fresh process, that importing payload or render
    # pulls in no narrative or LLM module. A top-level import in this file would
    # not break that assertion, but keeping the edge inside the one function that
    # publishes makes the boundary legible rather than a fact about import order.
    narr = None
    if not args.no_narrative:
        from daily_cascade import narrative as narrative_mod  # noqa: PLC0415

        # The prior session, for the deltas the template asks for. Built rather
        # than derived: the model must not compute a change, so the change has to
        # be a value, and a value it can be audited against has to come from the
        # same reader that produced today's.
        prior = None
        try:
            prior_sess = session.previous_trading_session(sess).isoformat()
            prior = payload_mod.build(sess=prior_sess, as_of=args.as_of)
        except Exception as exc:  # noqa: BLE001 -- a missing yesterday is not fatal
            log.info("prior session unavailable, deltas omitted: %s", exc)

        np_ = payload_mod.narrative_payload(p, prior)
        narr = narrative_mod.generate(
            np_, model=args.narrative_model,
            unit_constants=payload_mod.NARRATIVE_UNIT_CONSTANTS)

        # LOGGED EITHER WAY, and the failure is logged loudly. A withheld
        # paragraph is a fact about the model's output, and the only place it can
        # be investigated later is the log -- the report itself carries one line.
        if narr.published:
            print(f"  narrative  : published, {narr.figures_checked} figures "
                  f"audited (model {narr.model})")
            log.info("narrative published: %s figures audited, model=%s",
                     narr.figures_checked, narr.model)
        else:
            print(f"  narrative  : WITHHELD -- {narr.reason}")
            log.warning("narrative withheld (state=%s, model=%s): %s",
                        narr.state, narr.model, narr.reason)
            if narr.unmatched:
                log.warning("  unmatched figures: %s", ", ".join(narr.unmatched))

    name = f"daily_close_{sess}.html"
    subject = f"[chester] Close debrief {sess}"

    # THE ARCHIVE PATH IS KNOWN BEFORE THE SEND, so the copy that gets emailed
    # can name where the record is. This used to render once, deliver, then
    # re-render with the path and archive THAT -- which worked and quietly
    # produced two different documents: the email carried no path and the
    # archive carried one the email could not. Rendering once with the path
    # already in it makes the two copies byte-identical.
    html = render_mod.render(
        p, {"archive_path": delivery.archive_path(name, args.archive_dir)},
        narrative=narr)

    if args.dry_run:
        path = delivery.archive(html, name, args.archive_dir)
        out = {"archive_state": "archived" if path else "archive_failed",
               "archive_path": path, "delivery": "dry_run",
               "delivery_detail": "--dry-run", "delivered_at": session.utc_iso()}
    else:
        out = delivery.deliver(subject, html, name,
                               text_fallback=render_mod.text_fallback(p),
                               archive_dir=args.archive_dir)

    # AFTER the render, so a report that failed to build does not advance the
    # watermark and silently swallow the grades it never showed.
    _write_watermark(p.get("grades") or {})

    print(f"\n  archive    : {out['archive_path'] or 'FAILED'}")
    print(f"  delivery   : {out['delivery']} ({out['delivery_detail']})")

    if not args.no_emit:
        # REPORT_OK even when the mail failed: the report exists and is
        # correct. `degraded` is for a report that published with a hole in it,
        # which is what a missing block is.
        status = "ok"
        if p["warnings"] or p["portfolio"]["state"] != "ok":
            status = "degraded"
        if out["delivery"] in ("send_failed",) or out["archive_state"] == "archive_failed":
            status = "degraded"
        # A withheld paragraph does NOT degrade the report. The data-only
        # edition is a complete report and was the only edition for a reason; the
        # narrative state is carried so it can be graded, not so it can alarm.
        emit(REPORT_KEY, status,
             headline=(f"{len(p['exposure'])} symbols, "
                       f"{len(p['pins'])} pin rows, delivery {out['delivery']}"),
             detail={"run_id": run_id,
                     "narrative": (narr.state if narr else "disabled"),
                     "narrative_model": (narr.model if narr else None),
                     "narrative_figures": (narr.figures_checked if narr else 0),
                     "narrative_unmatched": (narr.unmatched if narr else []),
                     "exposure_symbols": len(p["exposure"]),
                     "pin_rows": len(p["pins"]),
                     "pin_hits": p["pin_hits"],
                     "portfolio": p["portfolio"]["state"],
                     "delivery": out["delivery"],
                     "archive": out["archive_path"],
                     "warnings": p["warnings"]},
             as_of=_as_date(sess))

    return 2 if out["delivery"] == "send_failed" else 0


def _as_date(s: str):
    import datetime as dt  # noqa: PLC0415
    try:
        return dt.date.fromisoformat(s)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    sys.exit(main())
