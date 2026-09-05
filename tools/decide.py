"""
The decision CLI -- the only supported way a recommendation enters the register.

The register has existed since the point-in-time work landed and has had no
writer, which is why every metric is still `trigger_eligible: false`. This is
that writer. It exists NOW, before anything produces a recommendation
automatically, so the first thing that does cannot route around it.

WHAT IT REFUSES, AND WHY THAT IS THE POINT

  * A restricted instrument. The Brookfield complex is checked BEFORE anything
    else and before any write, and --dry-run checks it too. A dry run that
    skipped the restriction would be worse than no dry run: it would report
    "this is what would happen" while omitting the one thing that would not.

  * A vocabulary violation. direction, horizon, status and operator_action are
    CHECK constraints in the schema, so a typo is refused by the database and
    not merely by this file.

  * A DECISION WHOSE INPUTS ARE STALE OR MISSING. 26.2 #7: a report may
    publish degraded, a recommendation may not. Every signal in --signals-used
    is checked at entry time against ITS OWN registry half-life, and a stale or
    missing one leaves the decision recorded but `draft` with a blocked_reason,
    never `active`. It is recorded rather than refused because an abstention is
    a decision and the register logs abstentions too -- the blocked ones are
    the record of what the system could not answer, and deleting them would
    leave only the days it happened to be ready.

  * A decision with no invalidation. Part 7: invalidation is defined before the
    position exists, never mid-week. The register makes it NOT NULL; this makes
    it a required argument, so it cannot be filled in later "when we see how it
    goes", which is exactly when it stops being an invalidation.

EVERY RECORDED DECISION GETS A PACKET. 26.2 #3: a material recommendation must
replay exactly from its own record. The packet is built at write time from the
run id, the git SHA, a content-addressed manifest of the chains that informed
it, the registry versions and the available_at cutoff -- not reconstructed
later from memory, which is the only version of this that works.

    python tools/decide.py record --instrument SPY --direction long \\
        --thesis "..." --edge-type positioning --horizon swing \\
        --invalidation "close below 760" --dry-run
    python tools/decide.py set-status --id <id> --status active \\
        --operator-action TAKE
    python tools/decide.py list
    python tools/decide.py show <id>

A STATUS CHANGE IS A NEW RECORD, NOT AN EDIT. Part 7: overwriting destroys the
grading trail. `set-status` supersedes -- see cmd_set_status.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from altdata import session                       # noqa: E402
from register import instruments, manifest        # noqa: E402
from register.store import (                      # noqa: E402
    DIRECTIONS, HORIZONS, OPERATOR_ACTIONS, STATUSES, THESIS_STATES,
    Register, RestrictedInstrumentError,
)
import exposure_compute as ec                     # noqa: E402
import freshness                                  # noqa: E402

LINE = "=" * 78

# 26.7's edge taxonomy. Closed, because "which edges does this system actually
# have" is a question you can only answer if the answer is not free text.
EDGE_TYPES = ("information", "expectation", "structural", "positioning",
              "liquidity", "behavioral", "carry", "convexity", "timing",
              "execution")


def _inputs_for(instrument: str) -> tuple[list[Path], str]:
    """The stored chains that informed THIS instrument's decision.

    Returns (paths, note). Keeps walking back until it finds a chain for the
    instrument itself rather than settling for whatever the newest directory
    happens to hold: the first version of this took the newest day with ANY
    chains and, on a day the vendor capture ran alone, pinned SPX and SPCX into
    a SPY decision's manifest. A packet that pins the WRONG inputs is worse than
    one that pins none -- it claims a lineage it does not have, and the claim
    looks exactly like a true one.

    An instrument with no stored chain gets an EMPTY manifest and says so. That
    is the honest answer for a decision on something this system does not
    capture, and it is visible rather than silently substituted.
    """
    root_sym = instruments.normalise(instrument)
    root = Path(ec.config.CHAIN_DIR)
    if not root.exists():
        return [], "no chain directory"
    days = sorted((p for p in root.iterdir() if p.is_dir()), reverse=True)
    for day in days:
        hit = ec.newest_chains(day.name, [root_sym]).get(root_sym)
        if hit:
            return [hit], f"{root_sym} chain from session {day.name}"
    return [], (f"no stored chain for {root_sym} -- manifest is empty and this "
                f"decision pins no market inputs")


def cmd_record(args) -> int:
    reg = Register(args.db)
    try:
        norm = instruments.normalise(args.instrument)
        hit = reg.restrictions.check(args.instrument)
        run_id = args.run_id or session.new_run_id("decide")
        cutoff = args.available_at_cutoff or session.utc_iso(timespec="microseconds")

        print(f"{LINE}\nDECISION {'(DRY RUN -- nothing will be written)' if args.dry_run else 'RECORD'}\n{LINE}")
        print(f"  instrument      : {args.instrument}   -> normalised {norm!r}")
        print(f"  direction       : {args.direction}")
        print(f"  horizon         : {args.horizon}")
        print(f"  edge_type       : {args.edge_type}")
        print(f"  size            : {args.size or '(unsized)'}")
        print(f"  status          : {args.status}")
        print(f"  operator_action : {args.operator_action or '(none yet)'}")
        print(f"  thesis          : {args.thesis}")
        print(f"  invalidation    : {args.invalidation}")
        print(f"  signals_used    : {', '.join(sorted(args.signals_used))}")

        # THE RESTRICTION, CHECKED IN DRY RUN TOO.
        print(f"\n  restriction check")
        if hit:
            print(f"    REFUSED -- {args.instrument!r} is in the "
                  f"{hit.get('entity_id')} complex")
            print(f"    matched on {hit['matched_on']}"
                  + (f": {hit['root']}" if hit["matched_on"] == "root"
                     else f": {hit.get('pattern')!r}"))
            print(f"    {hit.get('entity')}")
            print(f"\n  No recommendation may be written for this instrument. "
                  f"Diagnostic and\n  strategic coverage is unaffected -- it may "
                  f"be analysed, just not recommended.")
            if not args.dry_run:
                # Route through the register anyway so the attempt is LOGGED.
                # A refusal that leaves no record is indistinguishable from
                # nobody having tried.
                try:
                    reg.record(instrument=args.instrument, direction=args.direction,
                               thesis=args.thesis, edge_type=args.edge_type,
                               horizon=args.horizon, invalidation=args.invalidation,
                               size=args.size, status=args.status,
                               operator_action=args.operator_action, run_id=run_id)
                except RestrictedInstrumentError:
                    print(f"  attempt logged to blocked_attempts")
            print(f"{LINE}")
            return 2
        print(f"    clear -- {norm!r} is not restricted")

        # ---- DECISION_BLOCKED (26.2 #7) --------------------------------
        fresh = freshness.check_signals(args.signals_used, norm)
        print(f"\n  signal freshness ({len(args.signals_used)} declared)")
        for v in fresh["verdicts"]:
            mark = "STALE" if v["stale"] else " ok  "
            where = v["where"] or "not found"
            print(f"    [{mark}] {v['key']:<30} {str(v['half_life'] or '?'):<18} "
                  f"{where}")
            print(f"             {v['reason']}")
        status = args.status
        blocked_reason = fresh["blocked_reason"]
        if fresh["blocked"]:
            print(f"\n  DECISION_BLOCKED -- {len(fresh['stale'])} of "
                  f"{len(args.signals_used)} signals unusable")
            print(f"    The report may still publish; the RECOMMENDATION may not.")
            print(f"    Recorded as `draft` with a blocked_reason, never active.")
            print(f"\n    what would unblock it:")
            for v in fresh["stale"]:
                print(f"      {v['key']}")
                print(f"        -> {v['unblock'] or 'refresh the source'}")
            if status == "active":
                print(f"\n    requested status `active` downgraded to `draft`")
                status = "draft"
        else:
            print(f"\n  DECISION_OK -- every declared signal is inside its "
                  f"half-life")

        # The packet, built now rather than reconstructed later.
        inputs, inputs_note = _inputs_for(args.instrument)
        pkt = manifest.build_packet(run_id, session.utc_iso(), cutoff, inputs,
                                    {"decision": {
                                        "instrument": args.instrument,
                                        "direction": args.direction,
                                        "horizon": args.horizon,
                                        "edge_type": args.edge_type,
                                        "thesis": args.thesis,
                                        "invalidation": args.invalidation,
                                        "signals_used": sorted(args.signals_used),
                                        "blocked_reason": blocked_reason}})
        print(f"\n  decision packet (26.2 #3 -- must replay exactly)")
        print(f"    run_id              : {pkt['run_id']}")
        print(f"    git_sha             : {pkt['git_sha'][:12]}"
              + ("   CODE_DIRTY -- not replayable from this SHA alone"
                 if pkt["code_dirty"] else ""))
        print(f"    available_at_cutoff : {pkt['available_at_cutoff']}")
        print(f"    data_manifest       : {pkt['data_manifest_hash'][:12]}  "
              f"({pkt['data_manifest']['file_count']} input file(s))")
        print(f"        source          : {inputs_note}")
        for f in pkt["data_manifest"]["files"][:3]:
            print(f"        {f['sha256'][:10]}  {f['path']}")
        print(f"    registry versions   : metrics v{pkt['metrics_registry_version']}, "
              f"sources v{pkt['source_registry_version']}")
        print(f"    output_hash         : {pkt['output_hash'][:12]}")
        print(f"    volatile_fields     : {', '.join(pkt['volatile_fields'])}")

        if args.dry_run:
            print(f"\n  DRY RUN -- no decision written, no packet attached.")
            print(f"  Re-run without --dry-run to record it"
                  + (" -- it will land as draft, blocked."
                     if blocked_reason else "."))
            print(LINE)
            # Exit 3 on a blocked dry run too. A dry run's job is to say what
            # WOULD happen, and exiting 0 would say "fine" about a decision
            # that is not -- which is the one thing a dry run must not do.
            return 3 if blocked_reason else 0

        did = reg.record(instrument=args.instrument, direction=args.direction,
                         thesis=args.thesis, edge_type=args.edge_type,
                         horizon=args.horizon, invalidation=args.invalidation,
                         size=args.size, status=status,
                         operator_action=args.operator_action, run_id=run_id,
                         signals_used=sorted(args.signals_used),
                         blocked_reason=blocked_reason)
        pid = reg.attach_packet(did, pkt)
        print(f"\n  RECORDED{'  (DECISION_BLOCKED)' if blocked_reason else ''}")
        print(f"    decision id : {did}")
        print(f"    packet id   : {pid}  (immutable)")
        print(f"    status      : {status}")
        if blocked_reason:
            print(f"    blocked     : {blocked_reason[:120]}")
        print(LINE)
        return 3 if blocked_reason else 0
    finally:
        reg.close()


def cmd_list(args) -> int:
    reg = Register(args.db)
    try:
        rows = reg.all()
        if not rows:
            print("no decisions recorded")
            return 0
        print(f"{'id':<38}{'instrument':<12}{'dir':<7}{'horizon':<12}"
              f"{'status':<10}{'action':<9}state")
        for r in rows:
            print(f"{r['id']:<38}{r['instrument']:<12}{r['direction']:<7}"
                  f"{r['horizon']:<12}{r['status']:<10}"
                  f"{str(r['operator_action'] or '-'):<9}"
                  f"{r['thesis_state'] or '-'}"
                  + ("  SUPERSEDED" if r["superseded_by"] else ""))
        blocked = reg.blocked_attempts()
        if blocked:
            print(f"\n{len(blocked)} blocked attempt(s) on restricted instruments:")
            for b in blocked[-5:]:
                print(f"  {b['attempted_at']}  {b['instrument']} "
                      f"(matched on {b['matched_on']})")
        return 0
    finally:
        reg.close()


def cmd_show(args) -> int:
    reg = Register(args.db)
    try:
        d = reg.get(args.id)
        if not d:
            print(f"no decision {args.id!r}")
            return 1
        for k, v in d.items():
            print(f"  {k:<22} {v}")
        p = reg.packet(args.id)
        print("\n  packet:" if p else "\n  no packet attached")
        if p:
            for k, v in p.items():
                if k == "data_manifest_json":
                    v = f"{len(json.loads(v).get('files', []))} file(s)"
                print(f"    {k:<24} {v}")
        return 0
    finally:
        reg.close()


def cmd_set_status(args) -> int:
    """Change a decision's status by SUPERSEDING it, never by editing it.

    Part 7 rule 3: revision creates a new record. The original keeps its status,
    its operator_action and its packet exactly as written, gains `superseded_by`
    pointing at the successor, and is frozen by trigger from that moment. An
    in-place UPDATE would leave the register saying the decision had always been
    active and always TAKEn -- erasing that it was a draft first, and erasing the
    interval in which the operator decided. That interval is the grading trail.

    Register.set_status() still exists and still mutates in place. Nothing in
    production calls it: it is exercised only by the validation suite, which uses
    it to prove the freeze and DECISION_BLOCKED constraints hold against a direct
    writer. This command is the reason it has no other caller.
    """
    reg = Register(args.db)
    try:
        old = reg.get(args.id)
        if not old:
            print(f"no decision {args.id!r}")
            return 1

        action = args.operator_action or old["operator_action"]
        print(f"{LINE}\nSET STATUS -- by supersession, per Part 7\n{LINE}")
        print(f"  decision        : {old['id']}")
        print(f"  instrument      : {old['instrument']}  {old['direction']} "
              f"{old['horizon']}")
        print(f"  thesis          : {old['thesis']}")
        print(f"  from            : status {old['status']:<8} action "
              f"{old['operator_action'] or '(none)'}")
        print(f"  to              : status {args.status:<8} action "
              f"{action or '(none)'}")

        # A frozen row cannot take the pointer, and the trigger would abort the
        # UPDATE anyway. Refusing here names WHICH row to act on instead.
        if old["superseded_by"]:
            print(f"\n  REFUSED -- already superseded by {old['superseded_by']}")
            print(f"    That row is frozen and stays exactly as written. Set the "
                  f"status on\n    the successor; a chain with two live heads is "
                  f"not a chain.")
            print(LINE)
            return 1

        if args.status == old["status"] and action == old["operator_action"]:
            print(f"\n  NO CHANGE -- nothing written.")
            print(f"    Part 7 rule 4: revision has a bar. A superseding record "
                  f"that changes\n    nothing is noise in the trail that grades "
                  f"revisions per cycle.")
            print(LINE)
            return 0

        signals = json.loads(old["signals_used"] or "[]")
        blocked_reason = old["blocked_reason"]

        # 26.2 #7 AT THE MOMENT OF ACTIVATION, not only at the moment of
        # recording. A draft written this morning on signals that have since gone
        # stale must not become active tonight. Without this re-check,
        # `set-status --status active` is precisely the route around
        # DECISION_BLOCKED that the record path closes.
        if args.status == "active":
            fresh = freshness.check_signals(signals, old["instrument_norm"])
            print(f"\n  signal freshness, RE-CHECKED NOW ({len(signals)} carried "
                  f"forward)")
            for v in fresh["verdicts"]:
                mark = "STALE" if v["stale"] else " ok  "
                print(f"    [{mark}] {v['key']:<30} "
                      f"{str(v['half_life'] or '?'):<18} "
                      f"{v['where'] or 'not found'}")
                print(f"             {v['reason']}")
            if fresh["blocked"] or blocked_reason:
                print(f"\n  REFUSED -- DECISION_BLOCKED")
                print(f"    {fresh['blocked_reason'] or blocked_reason}")
                for v in fresh["stale"]:
                    print(f"      {v['key']}")
                    print(f"        -> {v['unblock'] or 'refresh the source'}")
                print(f"\n    Nothing written, and the draft is not copied into a "
                      f"second blocked\n    row -- it already stands as the record "
                      f"of what could not be activated.\n    Refresh the inputs "
                      f"and record a new decision.")
                print(LINE)
                return 3
            print(f"\n  DECISION_OK -- every declared signal is inside its "
                  f"half-life")

        if args.dry_run:
            print(f"\n  DRY RUN -- nothing written, nothing superseded.")
            print(LINE)
            return 0

        run_id = args.run_id or session.new_run_id("set-status")
        now = session.utc_iso()
        new_id = reg.supersede(
            args.id,
            instrument=old["instrument"], direction=old["direction"],
            thesis=old["thesis"], edge_type=old["edge_type"],
            horizon=old["horizon"], invalidation=old["invalidation"],
            size=old["size"], status=args.status, operator_action=action,
            thesis_state=old["thesis_state"], run_id=run_id,
            decision_time=now, signals_used=signals,
            blocked_reason=blocked_reason)

        # The successor gets its own packet, because a decision without one
        # cannot be replayed and `show` would report none. Its INPUTS are the
        # original's, carried forward by content hash: a status change consults
        # no market data, so re-hashing tonight's chains would pin inputs this
        # decision never saw. What is taken fresh is the code and the clock --
        # the operator acted now, against this SHA.
        old_pkt = reg.packet(args.id)
        dm = (json.loads(old_pkt["data_manifest_json"]) if old_pkt
              else {"files": [], "hash": "", "file_count": 0})
        pkt = {
            "run_id": run_id,
            "decision_time": now,
            "available_at_cutoff": (old_pkt["available_at_cutoff"] if old_pkt
                                    else now),
            "git_sha": manifest.git_sha(),
            "code_dirty": manifest.code_dirty(),
            "data_manifest": dm,
            "data_manifest_hash": (old_pkt["data_manifest_hash"] if old_pkt
                                   else dm.get("hash", "")),
            "output_hash": manifest.output_hash(
                {"decision": {"supersedes": args.id,
                              "instrument": old["instrument"],
                              "direction": old["direction"],
                              "horizon": old["horizon"],
                              "edge_type": old["edge_type"],
                              "thesis": old["thesis"],
                              "invalidation": old["invalidation"],
                              "status": args.status,
                              "operator_action": action,
                              "signals_used": sorted(signals),
                              "blocked_reason": blocked_reason}}),
            "volatile_fields": list(manifest.VOLATILE_FIELDS),
            **manifest.registry_versions(),
        }
        pid = reg.attach_packet(new_id, pkt)

        frozen = reg.get(args.id)
        print(f"\n  SUPERSEDED -- two rows, not one edited row")
        print(f"    old : {args.id}")
        print(f"          status {frozen['status']}, action "
              f"{frozen['operator_action'] or '(none)'}, superseded_by "
              f"{frozen['superseded_by']}")
        print(f"          frozen -- further UPDATEs abort at the trigger")
        print(f"    new : {new_id}")
        print(f"          status {args.status}, action {action or '(none)'}")
        print(f"          packet {pid}  (inputs inherited, "
              f"{dm.get('file_count', 0)} file(s))")
        print(LINE)
        return 0
    finally:
        reg.close()


def main() -> int:
    ap = argparse.ArgumentParser(description="Record a decision in the register")
    ap.add_argument("--db", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record", help="record a decision (or --dry-run it)")
    r.add_argument("--instrument", required=True)
    r.add_argument("--direction", required=True, choices=DIRECTIONS)
    r.add_argument("--thesis", required=True, help="one line; what and why")
    r.add_argument("--edge-type", required=True, choices=EDGE_TYPES)
    r.add_argument("--horizon", required=True, choices=HORIZONS)
    # Required, not optional. Part 7: defined before the position exists.
    r.add_argument("--invalidation", required=True,
                   help="the pre-set condition that ends this, written NOW")
    r.add_argument("--signals-used", required=True, nargs="+", metavar="KEY",
                   help="Registry keys this decision rests on. Required: a "
                        "decision citing no evidence cannot be checked, and an "
                        "unchecked decision is the thing 26.2 #7 forbids.")
    r.add_argument("--size", default=None)
    r.add_argument("--status", default="draft", choices=STATUSES)
    r.add_argument("--operator-action", default=None, choices=OPERATOR_ACTIONS)
    r.add_argument("--run-id", default=None)
    r.add_argument("--available-at-cutoff", default=None)
    r.add_argument("--dry-run", action="store_true",
                   help="Show exactly what would be written, including the "
                        "restriction check, and write nothing.")
    r.set_defaults(func=cmd_record)

    ss = sub.add_parser("set-status",
                        help="change a decision's status by superseding it")
    ss.add_argument("--id", required=True)
    ss.add_argument("--status", required=True, choices=STATUSES)
    ss.add_argument("--operator-action", default=None, choices=OPERATOR_ACTIONS,
                    help="Carried forward from the superseded row if omitted.")
    ss.add_argument("--run-id", default=None)
    ss.add_argument("--dry-run", action="store_true",
                    help="Show what would be superseded, and write nothing.")
    ss.set_defaults(func=cmd_set_status)

    l = sub.add_parser("list", help="list recorded decisions")
    l.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="show one decision and its packet")
    sh.add_argument("id")
    sh.set_defaults(func=cmd_show)

    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
