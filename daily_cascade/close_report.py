"""
The 16:30 close debrief. D4c — the first Daily Cascade run to exist as code.

    python -m daily_cascade.close_report              # build, archive, send
    python -m daily_cascade.close_report --dry-run    # build and archive only
    python -m daily_cascade.close_report --session 2026-09-04

WHY THIS ONE FIRST (32.4). Its inputs are computed twenty minutes earlier by
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--session", help="Session to report (default: newest scored)")
    ap.add_argument("--as-of", help="Point-in-time cutoff (default: now)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Build and archive; send nothing")
    ap.add_argument("--no-emit", action="store_true",
                    help="Skip the dashboard state record")
    ap.add_argument("--archive-dir", help="Override the archive directory")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    run_id = session.new_run_id("daily_close")
    p = payload_mod.build(sess=args.session, as_of=args.as_of, run_id=run_id)
    sess = p["session"]

    print(f"close debrief -- session {sess}")
    print(f"  run id     : {run_id}")
    print(f"  exposure   : {len(p['exposure'])} symbols "
          f"({len(p['exposure_missing'])} not in the table)")
    print(f"  pins       : {len(p['pins'])} rows, hits {p['pin_hits']}")
    print(f"  portfolio  : {p['portfolio']['state']}")
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

    html = render_mod.render(p)
    name = f"daily_close_{sess}.html"
    subject = f"[chester] Close debrief {sess}"

    if args.dry_run:
        path = delivery.archive(html, name, args.archive_dir)
        out = {"archive_state": "archived" if path else "archive_failed",
               "archive_path": path, "delivery": "dry_run",
               "delivery_detail": "--dry-run", "delivered_at": session.utc_iso()}
    else:
        out = delivery.deliver(subject, html, name,
                               text_fallback=render_mod.text_fallback(p),
                               archive_dir=args.archive_dir)

    # Re-render once the delivery outcome is known, so the archived copy states
    # what happened to it. The emailed copy cannot say this -- it was built
    # before it was sent -- and the archive is the one that gets read later.
    if out.get("archive_path"):
        delivery.archive(render_mod.render(p, out), name, args.archive_dir)

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
        emit(REPORT_KEY, status,
             headline=(f"{len(p['exposure'])} symbols, "
                       f"{len(p['pins'])} pin rows, delivery {out['delivery']}"),
             detail={"run_id": run_id,
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
