#!/usr/bin/env python3
"""
The Weekly Tactical. Sunday 05:00 ET. (Phase 4a)

    python -m daily_cascade.weekly_report                    # build, archive, send
    python -m daily_cascade.weekly_report --dry-run          # build and archive only
    python -m daily_cascade.weekly_report --week-ending 2026-09-18 --dry-run
    python -m daily_cascade.weekly_report --no-narrative

payload -> narrative -> render -> archive (with its payload) -> deliver.

ONE ANCHOR REPLACING TWO. The Friday Reflection and the Sunday Forward Plan were
separate documents that shared most of their content and disagreed whenever one was
skipped; this is the single slot that reads the week and sets up the next one.

EXIT CODES, deliberately the close report's shape so a wrapper can treat them alike:

    0  built, archived and delivered
    1  no payload -- nothing could be read, which means a store or register fault
    2  built and ARCHIVED but delivery failed; the report is on disk
    3  built and archived in --dry-run

THE PAYLOAD IS ARCHIVED BESIDE THE HTML, for the reason the close report learned
it: diagnosing a withheld paragraph from a rebuilt payload answers "what would the
payload be now" and not "what did the model see".
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import session                          # noqa: E402
from daily_cascade import deliver as delivery        # noqa: E402
from daily_cascade import narrative as narrative_mod  # noqa: E402
from daily_cascade import weekly_payload as payload_mod  # noqa: E402
from daily_cascade import weekly_render as render_mod    # noqa: E402

log = logging.getLogger("daily_cascade.weekly")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TEMPLATE_PATH = REPO / "docs" / "narrative-template-weekly.md"


def main() -> int:
    ap = argparse.ArgumentParser(description="The Weekly Tactical.")
    ap.add_argument("--week-ending", default=None,
                    help="Friday the reported week ended on (default: the one "
                         "just past)")
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="Build and archive; send nothing")
    ap.add_argument("--no-narrative", action="store_true",
                    help="Ship the data-only edition; attempt no paragraph")
    ap.add_argument("--no-fetch", action="store_true",
                    help="Skip the two network reads in THE WEEK AHEAD (FRED "
                         "release dates, earnings) and report them skipped")
    ap.add_argument("--narrative-model", default=None)
    ap.add_argument("--archive-dir", default=None)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    run_id = session.new_run_id("weekly")

    p = payload_mod.build(args.week_ending, as_of=args.as_of, run_id=run_id,
                          fetch=not args.no_fetch)
    ending = p.get("week_ending")
    if not ending:
        print("no payload -- the week could not be resolved")
        return 1

    # --- the paragraph -------------------------------------------------------
    narr = None
    if not args.no_narrative:
        np_ = payload_mod.narrative_payload(p)
        narr = narrative_mod.generate(
            np_, model=args.narrative_model,
            system_prompt=weekly_system_prompt(),
            guide_path=TEMPLATE_PATH)
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

    name = f"weekly_tactical_{ending}.html"
    subject = f"[chester] Weekly Tactical — {ending}"

    # The payload first, so a delivery failure cannot cost the record.
    try:
        pay = delivery.archive(json.dumps(p, indent=2, default=str,
                                          sort_keys=True),
                               f"weekly_tactical_{ending}_payload.json",
                               args.archive_dir)
        log.info("archived payload %s", pay)
    except Exception as exc:                                   # noqa: BLE001
        log.warning("payload archive failed (%s: %s) -- the report continues",
                    type(exc).__name__, exc)

    html = render_mod.render(
        p, {"archive_path": delivery.archive_path(name, args.archive_dir)},
        narrative=narr)

    if args.dry_run:
        path = delivery.archive(html, name, args.archive_dir)
        out = {"archive_path": path, "delivery": "dry_run",
               "delivery_detail": "--dry-run"}
        rc = 3
    else:
        out = delivery.deliver(subject, html, name,
                               text_fallback=render_mod.text_fallback(p),
                               archive_dir=args.archive_dir)
        rc = 0 if out.get("delivery") == "sent" else 2

    st = p.get("week_in_state") or {}
    gr = p.get("grades") or {}
    rg = p.get("register") or {}
    wa = p.get("week_ahead") or {}
    print(f"\nweekly tactical -- week ending {ending}")
    print(f"  run id     : {run_id}")
    print(f"  state      : {st.get('state')} -- "
          f"{len(st.get('dimension_changes') or [])} dimension change(s), "
          f"{len(st.get('dial_changes') or [])} dial move(s), "
          f"{len(st.get('exceptions_opened') or [])} exception(s) opened, "
          f"{len(st.get('exceptions_intraweek_only') or [])} opened and closed "
          f"inside the week")
    ag = (st.get("vol_term_structure") or {}).get("week_agreement") or {}
    print(f"  vol legs   : {ag.get('agreed')} agreed, {ag.get('disagreed')} "
          f"disagreed, {ag.get('not_comparable')} not comparable")
    print(f"  grades     : {gr.get('state')} -- {gr.get('total_graded')} to date, "
          f"{len(gr.get('graded_this_week') or [])} this week")
    print(f"  register   : {rg.get('open_count')} open, "
          f"{rg.get('drafts_count')} draft, "
          f"{(rg.get('rule_breaks') or {}).get('restricted_instrument_attempts_this_week')}"
          f" restricted attempt(s) this week")
    print(f"  week ahead : releases {(wa.get('releases') or {}).get('state')}, "
          f"earnings {(wa.get('earnings') or {}).get('state')}, "
          f"{len(wa.get('session_events') or {})} sessions classified")
    print(f"  weekend    : "
          f"{(p.get('weekend_developments') or {}).get('state')}")
    if narr is not None:
        print(f"  narrative  : "
              + (f"published, {narr.figures_checked} figures audited "
                 f"(model {narr.model})" if narr.published
                 else f"WITHHELD -- {narr.reason}"))
    print(f"  archive    : {out.get('archive_path') or 'FAILED'}")
    print(f"  delivery   : {out.get('delivery')} ({out.get('delivery_detail')})")
    for w in p.get("warnings") or []:
        print(f"  WARNING    : {w}")
    return rc


def weekly_system_prompt() -> str:
    """The weekly brief. The close report's rules, with two differences.

    LONG-FORM IS PERMITTED AND NO WORD COUNT IS STATED -- the operator's ruling. A
    weekly reflection that had to fit a daily's length would drop either the grades
    or the theses, and both are the reason the slot exists.

    The audit and the print-precision rule are UNCHANGED, and that is the point:
    length is a matter of judgement, and whether a figure exists is not.
    """
    base = narrative_mod.SYSTEM_PROMPT
    return base + (
        "\n\nTHIS IS THE WEEKLY TACTICAL, not the close report. Four differences:\n"
        "\n1. LENGTH IS WHATEVER THE WEEK NEEDS. No word count, no paragraph "
        "count. Several paragraphs are correct when the week had several things in "
        "it; on a week where nothing changed, say so in three sentences and stop.\n"
        "\n2. THE HORIZON IS THE WEEK. Do not write about one session's move. What "
        "changed over five sessions, what held, and what opened and closed inside "
        "the week without showing at either end -- that last one is in the payload "
        "as exceptions_intraweek_only and it is the fact a weekly usually misses.\n"
        "\n3. COVER, in this order: the week's state changes; the grades and what "
        "their INTERVAL permits you to say (an interval that spans zero permits "
        "nothing about the sign); each open thesis and WHAT WOULD CHANGE IT; where "
        "the vol dial's two legs disagree and why that matters this week; the week "
        "ahead. Say what is not sourced where the payload says so.\n"
        "\n4. NO RECOMMENDATION, exactly as in the close report. The register's "
        "rule decides each position and the paragraph states the rule and the "
        "distance.\n")


if __name__ == "__main__":
    sys.exit(main())
