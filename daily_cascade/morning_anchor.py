"""
The 07:00 ET morning anchor, data-only edition. Phase 1, on the D4c pattern.

    python -m daily_cascade.morning_anchor              # build, archive, send
    python -m daily_cascade.morning_anchor --dry-run    # build and archive only
    python -m daily_cascade.morning_anchor --session 2026-09-18

WHY IT LOOKS EXACTLY LIKE close_report.py. The close run was built first because
its inputs are computed half an hour earlier, so it could not fail for a reason
the report layer owned -- which made it the cheapest end-to-end proof of
payload -> render -> deliver -> archive -> state. That chain is now proven, so
this run is payload configuration against a pipeline rather than new pipeline. The
one structural difference is that this report has a fetch in front of it, and the
fetch is a SEPARATE UNIT at 06:45 precisely so that this process still cannot
fail for a transport reason: a dead fetch is a block that says why, not a crash.

WHY IT CONTAINS NO SENTENCES (32.5). Narrative arrives at D4e, gated on D3's
numeral audit. Until something can FAIL a block for containing a number that is
not in its payload, the safe version of this report is the one with no prose to
audit. tools/validate_daily_close.py reads every module in this package and
fails on any import of an LLM client or the narrative layer.

EXIT CODES. The report is the product; delivery is transport.
    0  report built (and delivered, or deliberately not sent)
    1  no payload worth sending -- the overnight block is absent AND there is
       nothing from the prior close either, so the message would be empty
    2  built and archived, but delivery failed

An absent overnight block ALONE is not exit 1. The prior close's exposure, the
pin verdicts and the portfolio are still worth a 07:00 message, and the absent
block names why it is absent -- which is information the reader needs before the
open, not a reason to stay silent. Silence is the one outcome that teaches a
reader nothing.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import session                             # noqa: E402
from daily_cascade import deliver as delivery           # noqa: E402
from daily_cascade import morning_payload as payload_mod  # noqa: E402
from daily_cascade import morning_render as render_mod  # noqa: E402
from state.emit import emit                             # noqa: E402

log = logging.getLogger("daily_cascade.morning")

REPORT_KEY = "daily_cascade"
SLOT = "morning_anchor"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--session", help="Session being opened (default: today ET)")
    ap.add_argument("--as-of", help="Point-in-time cutoff (default: now)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Build and archive; send nothing")
    ap.add_argument("--no-emit", action="store_true",
                    help="Skip the dashboard state record")
    ap.add_argument("--archive-dir", help="Override the archive directory")
    ap.add_argument("--db", help="Override the observation store")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    run_id = session.new_run_id("morning_anchor")
    p = payload_mod.build(sess=args.session, as_of=args.as_of, run_id=run_id,
                          db_path=args.db)
    sess = p["session"]
    on = p["overnight"]

    print(f"morning anchor -- session {sess} (prior {p['prior_session']})")
    print(f"  run id     : {run_id}")
    print(f"  overnight  : {on['state']}, {len(on['rows'])} instruments, "
          f"{len(on['attribution'])} attributed")
    if on.get("fetched_at"):
        print(f"  fetched at : {on['fetched_at']}")
    print(f"  exposure   : {len(p['exposure'])} symbols from {p['exposure_session']}")
    print(f"  pins       : {len(p['pins'])} rows")
    print(f"  portfolio  : {p['portfolio']['state']}")
    for w in p["warnings"]:
        print(f"  WARNING    : {w}")

    # Empty means EVERY block is empty. An absent overnight block on its own
    # still leaves a report worth sending, and the absent block naming its own
    # reason is what tells the reader the 06:45 timer is down.
    if not on["rows"] and not p["exposure"] and not p["pins"]:
        print("\nEvery block is empty; no report sent.")
        if not args.no_emit:
            emit(REPORT_KEY, "error",
                 headline=f"morning anchor: no payload for {sess}",
                 detail={"run_id": run_id, "slot": SLOT,
                         "warnings": p["warnings"]},
                 as_of=_as_date(sess))
        return 1

    html = render_mod.render(p)
    name = f"morning_anchor_{sess}.html"
    subject = f"[chester] Morning anchor {sess}"

    if args.dry_run:
        path = delivery.archive(html, name, args.archive_dir)
        out = {"archive_state": "archived" if path else "archive_failed",
               "archive_path": path, "delivery": "dry_run",
               "delivery_detail": "--dry-run", "delivered_at": session.utc_iso()}
    else:
        out = delivery.deliver(subject, html, name,
                               text_fallback=render_mod.text_fallback(p),
                               archive_dir=args.archive_dir)

    # THE FOOTER NAMES THE ARCHIVE PATH, AND IT IS KNOWN BEFORE THE SEND.
    # deliver() archives first (rule 1), so the path exists by the time the
    # socket opens -- which means the EMAILED copy can state where the record
    # is, not only the archived one. The close report re-renders after delivery
    # to add this and the mailed copy therefore cannot carry it; this run
    # renders once, with the path already in hand.
    if out.get("archive_path"):
        delivery.archive(render_mod.render(p, out), name, args.archive_dir)

    print(f"\n  archive    : {out['archive_path'] or 'FAILED'}")
    print(f"  delivery   : {out['delivery']} ({out['delivery_detail']})")

    if not args.no_emit:
        # REPORT_OK even when the mail failed: the report exists and is correct.
        # `degraded` is for a report that published with a hole in it, which is
        # what an absent or stale block is.
        status = "ok"
        if p["warnings"] or on["state"] != "ok":
            status = "degraded"
        if (out["delivery"] == "send_failed"
                or out["archive_state"] == "archive_failed"):
            status = "degraded"
        emit(REPORT_KEY, status,
             headline=(f"morning anchor: {len(on['rows'])} instruments "
                       f"({on['state']}), delivery {out['delivery']}"),
             detail={"run_id": run_id,
                     "slot": SLOT,
                     "overnight_state": on["state"],
                     "overnight_rows": len(on["rows"]),
                     "overnight_stale": on["stale"],
                     "fetched_at": on.get("fetched_at"),
                     "attributed": len(on["attribution"]),
                     "prior_session": p["prior_session"],
                     "exposure_symbols": len(p["exposure"]),
                     "pin_rows": len(p["pins"]),
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
