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

WHY IT CONTAINED NO SENTENCES, AND WHAT CHANGED (32.5; 6c-2). Narrative was
gated on D3's numeral audit: until something could FAIL a block for containing a
number not in its payload, the safe version of this report was the one with no
prose. The audit exists, so 6c-2 gives the anchor its first model call -- the
news and narrative scan (Audit #3 §I, Daily Cascade v2 Part 0.4) -- over the story
block's payload only, pinned (narrative.MORNING_MODEL), thinking off, at print
precision, behind the numeral audit, the type audit and a traceability check on
every cited event id. A withheld draft is logged and the anchor ships its
data-only edition. The data path still cannot reach a model: the narrative module
is imported inside _narrative_scan() and nowhere else, and
tools/validate_daily_close.py checks that in the source and in a clean process.
`--no-narrative` is the data-only edition on demand.

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
    ap.add_argument("--no-narrative", action="store_true",
                    help="skip the narrative scan: the data-only edition")
    ap.add_argument("--narrative-model", default=None,
                    help="override the pinned morning model")
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

    narr, proposals = _narrative_scan(p, args, run_id)

    name = f"morning_anchor_{sess}.html"
    subject = f"[chester] Morning anchor {sess}"
    html = render_mod.render(p, {"archive_path":
                                 delivery.archive_path(name, args.archive_dir)},
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
                     "narrative_state": getattr(narr, "state", "not_attempted"),
                     "narrative_model": getattr(narr, "model", None),
                     "narrative_verdicts": (narr.verdicts() if narr is not None
                                            else None),
                     "narrative_proposals": proposals,
                     "delivery": out["delivery"],
                     "archive": out["archive_path"],
                     "warnings": p["warnings"]},
             as_of=_as_date(sess))

    return 2 if out["delivery"] == "send_failed" else 0


def _narrative_scan(p: dict, args, run_id: str):
    """THE ANCHOR'S FIRST MODEL CALL (6c-2). (result, proposals written).

    Over the story block's payload only, behind the numeral and type audit and a
    traceability check on every cited event id. Imported HERE and not at the top,
    exactly as the close report does, so importing the data path pulls in no model:
    tools/validate_daily_close.py asserts that in a clean process.

    A PROPOSAL the model appends is validated by the register and written as
    `proposed`; one that fails is logged and dropped, and the prose publishes
    regardless. Never raises: a missing paragraph is a data-only edition, which is
    a complete report.
    """
    if args.no_narrative:
        return None, []
    try:
        from daily_cascade import narrative as narrative_mod  # noqa: PLC0415
        from daily_cascade import story_block                 # noqa: PLC0415
        block = p.get("stories") or {}
        np_ = story_block.narrative_payload(block, p.get("what_changed"))
        narr = narrative_mod.generate(
            np_, model=args.narrative_model or narrative_mod.MORNING_MODEL,
            system_prompt=narrative_mod.morning_system_prompt(),
            guide_path=narrative_mod.MORNING_TEMPLATE_PATH,
            max_chars=narrative_mod.MORNING_MAX_CHARS, one_paragraph=False,
            split=narrative_mod.split_proposals,
            citable_ids=block.get("citable_event_ids") or [],
            cite_word=story_block.CITE_WORD)
    except Exception as exc:                                   # noqa: BLE001
        log.warning("narrative scan failed to run: %s: %s",
                    type(exc).__name__, exc)
        return None, []
    v = narr.verdicts()
    print(f"  narrative  : {narr.state} (model {narr.model}) -- numeral "
          f"{v['numeral']}; type {v['type']}; traceability {v['traceability']}")
    if not narr.published:
        log.warning("narrative withheld (state=%s): %s", narr.state, narr.reason)
        if narr.rejected_text:
            # LOGGED, NEVER RENDERED: the draft the audit rejected, so a human
            # can see whether the audit was right.
            log.info("  withheld draft (NOT published): %s", narr.rejected_text)
    written = []
    extra = narr.extra or {}
    if extra.get("parse_error"):
        log.warning("proposals block unreadable: %s", extra["parse_error"])
    for prop in extra.get("proposals") or []:
        nid = str(prop.get("id") or "")
        try:
            from altdata import narratives as nr                # noqa: PLC0415
            allowed = set((p.get("stories") or {}).get("citable_event_ids") or [])
            basis = [int(x) for x in prop.get("basis_events") or []]
            if not set(basis) <= allowed:
                raise nr.NarrativeError(
                    f"basis events {sorted(set(basis) - allowed)} are not in this "
                    f"morning's payload")
            with nr.NarrativeRegister(args.db) as reg:
                reg.propose(nid, prop, basis,
                            proposed_by=f"morning_anchor:{narr.model}:{run_id}")
            written.append(nid)
            print(f"  proposal   : {nid} written as proposed -- awaits "
                  f"`{nr.CONFIRM_COMMAND.format(id=nid)}`")
        except Exception as exc:                               # noqa: BLE001
            log.warning("proposal %r refused: %s", nid, exc)
    return narr, written


def _as_date(s: str):
    import datetime as dt  # noqa: PLC0415
    try:
        return dt.date.fromisoformat(s)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    sys.exit(main())
