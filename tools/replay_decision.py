"""
Replay one decision's packet from its own record.

Architecture 26.2 #3: a packet is only worth keeping if the run REPLAYS EXACTLY
from it. `tools/validate_register.py` proves that property for an exposure
computation; this proves it for a DECISION, which is the record that actually
matters when a trade is graded a year later.

-----------------------------------------------------------------------------
TWO LEVELS, AND THE DIFFERENCE BETWEEN THEM IS THE POINT
-----------------------------------------------------------------------------
LEVEL 1 -- PACKET SELF-CONSISTENCY. Recompute the output hash from the decision
row, and the data-manifest hash from the stored file list. Both are functions of
stored data alone, so they are MACHINE-INDEPENDENT: a packet that replays on the
laptop must replay identically on the box, and if it does not, the record has
been altered. This is the level that has to be EXACT, and it is what makes moving
the register between machines verifiable rather than hopeful.

LEVEL 2 -- INPUT AVAILABILITY. Are the files the manifest names actually present,
with the content it recorded? This is machine-DEPENDENT by nature and a
difference here is not corruption. The box and the laptop hold different captures
of the same session -- the laptop's SPY chain for 2026-09-04 was taken at
20:10:03Z and the box's at 02:50:09Z -- so a decision made on the laptop's capture
cannot have its inputs re-derived on the box. That is a real limitation of the
move and it is reported rather than hidden, because the alternative is a green
replay that quietly means less than it appears to.

-----------------------------------------------------------------------------
WHAT A RECORD-SHAPE PACKET CANNOT PROVE
-----------------------------------------------------------------------------
Two packet shapes exist and they hash different things. A supersession hashes the
decision's own fields plus the id it supersedes -- all of which are on the row, so
it replays completely. A `record` additionally hashes the EXPRESSION WARNINGS,
which are a function of sec_type, expiry and structure: CLI arguments that are not
persisted on the decision row. Those are re-derived here from the documented
defaults, and when that reproduces the hash the result is reported as exact; when
it does not, the honest answer is that the packet depends on inputs the row does
not carry, and it is reported that way rather than as a failure.

    python tools/replay_decision.py fae90045
    python tools/replay_decision.py fae90045 --db data/chester.db --json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from register import manifest                       # noqa: E402
from register import store as reg_store             # noqa: E402
import expression_check                             # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINE = "=" * 78


def _rows(conn, sql, args=()):
    conn.row_factory = sqlite3.Row
    return [dict(r) for r in conn.execute(sql, args)]


def supersedes_of(conn, decision_id: str):
    """The id this decision superseded, from the pointer on the older row."""
    got = _rows(conn, "SELECT id FROM decisions WHERE superseded_by = ?",
                (decision_id,))
    return got[0]["id"] if got else None


def rebuild_outputs(conn, row: dict, run_id: str) -> list[tuple[dict, str]]:
    """Candidate objects whose hash the packet may have stored, newest shape first.

    MORE THAN ONE CANDIDATE, BECAUSE THE HASHED SHAPE HAS CHANGED ONCE AND WILL
    AGAIN. `expression_warnings` was added to the `record` object after the first
    decisions were written, so the oldest packet in this register hashes a
    strictly smaller object. Trying only today's shape would report that packet as
    DIFFERS, which is the same word this tool uses for an altered record -- and
    those two things could not be more different. One is a schema change with a
    date; the other is evidence the register has been tampered with.

    So every historical shape is a named candidate, the first that reproduces
    wins, and the NAME is reported. A packet that matches no candidate is the
    only one that means what DIFFERS should mean.
    """
    signals = sorted(json.loads(row.get("signals_used") or "[]"))

    if str(run_id).startswith("set-status-"):
        return [({"decision": {
            "supersedes": supersedes_of(conn, row["id"]),
            "instrument": row["instrument"],
            "direction": row["direction"],
            "horizon": row["horizon"],
            "edge_type": row["edge_type"],
            "thesis": row["thesis"],
            "invalidation": row["invalidation"],
            "status": row["status"],
            "operator_action": row["operator_action"],
            "signals_used": signals,
            "blocked_reason": row["blocked_reason"],
        }}, "supersession")]

    # A `record`. The expression warnings are a function of the declared shape,
    # and the shape's arguments are not on the row -- so they are re-derived from
    # the documented defaults (STK, no expiry, no structure). See the docstring.
    warns = expression_check.check(
        edge_type=row["edge_type"], horizon=row["horizon"],
        sec_type="STK", expiry=None, structure=None)
    base = {
        "instrument": row["instrument"],
        "direction": row["direction"],
        "horizon": row["horizon"],
        "edge_type": row["edge_type"],
        "thesis": row["thesis"],
        "invalidation": row["invalidation"],
        "signals_used": signals,
        "blocked_reason": row["blocked_reason"],
    }
    return [
        ({"decision": {**base,
                       "expression_warnings": [w["code"] for w in warns]}},
         "record"),
        # Packets written before the expression check was folded into the hash.
        # The oldest decision in this register (4f8be6ea, 5 September 2026, at
        # 55630fb with a clean tree) is one of these.
        ({"decision": dict(base)}, "record/pre-expression-warnings"),
    ]


def replay(decision_id: str, db: str | None = None) -> dict:
    """Level 1 and Level 2 for one decision. Never raises on a missing input."""
    conn = sqlite3.connect(db or reg_store.DEFAULT_DB)
    try:
        rows = _rows(conn, "SELECT * FROM decisions WHERE id LIKE ?",
                     (decision_id + "%",))
        if not rows:
            return {"ok": False, "error": f"no decision matching {decision_id!r}"}
        if len(rows) > 1:
            return {"ok": False,
                    "error": f"{decision_id!r} matches {len(rows)} decisions"}
        row = rows[0]
        pkts = _rows(conn, "SELECT * FROM decision_packets WHERE decision_id = ?",
                     (row["id"],))
        if not pkts:
            return {"ok": False, "error": f"decision {row['id']} has no packet"}
        pkt = pkts[0]

        volatile = (json.loads(pkt["volatile_fields"] or "[]")
                    or manifest.VOLATILE_FIELDS)
        candidates = rebuild_outputs(conn, row, pkt["run_id"])
        got_output, shape = None, None
        for obj, name in candidates:
            h = manifest.output_hash(obj, volatile)
            if got_output is None:
                got_output, shape = h, name          # the newest shape, for display
            if h == pkt["output_hash"]:
                got_output, shape = h, name          # the one that actually matches
                break

        # The manifest hash, recomputed from the STORED file list. Content
        # addressed, so this is a statement about the record and not about the
        # filesystem -- which is exactly what makes it machine-independent.
        dm = json.loads(pkt["data_manifest_json"] or "{}")
        files = dm.get("files") or []
        blob = json.dumps(files, sort_keys=True, separators=(",", ":"))
        import hashlib  # noqa: PLC0415
        got_manifest = hashlib.sha256(blob.encode()).hexdigest()

        # Level 2, reported separately.
        inputs = []
        for f in files:
            p = REPO / f["path"]
            present = p.is_file()
            actual = manifest.sha256_file(p) if present else None
            inputs.append({"path": f["path"], "present": present,
                           "recorded_sha": f["sha256"], "actual_sha": actual,
                           "matches": bool(present and actual == f["sha256"])})

        out_ok = got_output == pkt["output_hash"]
        man_ok = got_manifest == pkt["data_manifest_hash"]
        return {
            "ok": out_ok and man_ok,
            "decision_id": row["id"],
            "instrument": row["instrument"],
            "status": row["status"],
            "thesis_state": row["thesis_state"],
            "run_id": pkt["run_id"],
            "shape": shape,
            "git_sha": pkt["git_sha"],
            "code_dirty": pkt["code_dirty"],
            "output_hash": {"stored": pkt["output_hash"], "recomputed": got_output,
                            "exact": out_ok},
            "data_manifest_hash": {"stored": pkt["data_manifest_hash"],
                                   "recomputed": got_manifest, "exact": man_ok},
            "registry_versions": {
                "metrics": pkt["metrics_registry_version"],
                "sources": pkt["source_registry_version"]},
            "inputs": inputs,
            "inputs_available": all(i["matches"] for i in inputs) if inputs else None,
        }
    finally:
        conn.close()


def main() -> int:
    ap = argparse.ArgumentParser(description="Replay a decision packet")
    ap.add_argument("decision_id", help="full id or unambiguous prefix")
    ap.add_argument("--db", default=None)
    ap.add_argument("--json", action="store_true",
                    help="machine-readable, for comparing two machines")
    args = ap.parse_args()

    res = replay(args.decision_id, args.db)
    if args.json:
        print(json.dumps(res, indent=2, sort_keys=True))
        return 0 if res.get("ok") else 1

    if res.get("error"):
        print(f"REPLAY FAILED: {res['error']}")
        return 2

    print(f"{LINE}\nREPLAY -- decision packet, from its own record\n{LINE}")
    print(f"  decision    : {res['decision_id']}")
    print(f"  instrument  : {res['instrument']}  status {res['status']}"
          + (f"  state {res['thesis_state']}" if res["thesis_state"] else ""))
    print(f"  run_id      : {res['run_id']}   shape: {res['shape']}")
    print(f"  git_sha     : {res['git_sha'][:12]}"
          + ("   (recorded CODE_DIRTY -- not replayable from this SHA alone)"
             if res["code_dirty"] else ""))
    print(f"  registries  : metrics v{res['registry_versions']['metrics']}, "
          f"sources v{res['registry_versions']['sources']}")

    print(f"\n  LEVEL 1 -- packet self-consistency (machine-independent)")
    for name, key in (("output_hash", "output_hash"),
                      ("data_manifest", "data_manifest_hash")):
        h = res[key]
        mark = "EXACT  " if h["exact"] else "DIFFERS"
        print(f"    [{mark}] {name}")
        print(f"              stored     {h['stored']}")
        if not h["exact"]:
            print(f"              recomputed {h['recomputed']}")

    print(f"\n  LEVEL 2 -- input availability on THIS machine")
    if not res["inputs"]:
        print(f"    (the packet names no input files)")
    for i in res["inputs"]:
        if i["matches"]:
            mark = "PRESENT"
        elif i["present"]:
            mark = "CHANGED"
        else:
            mark = "ABSENT "
        print(f"    [{mark}] {i['path']}")
        if i["present"] and not i["matches"]:
            print(f"              recorded {i['recorded_sha'][:16]}  "
                  f"actual {(i['actual_sha'] or '')[:16]}")

    print(f"\n{LINE}")
    if res["ok"]:
        print("REPLAY EXACT -- the packet reproduces from its own record.")
        if res["inputs_available"] is False:
            print("NOTE: the named inputs are not all available here, so the "
                  "decision's\n      computation cannot be re-derived on this "
                  "machine. That is a fact\n      about this filesystem, not "
                  "about the record.")
    else:
        print("REPLAY FAILED -- the record does not reproduce its own packet.")
    print(LINE)
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
