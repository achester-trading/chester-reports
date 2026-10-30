"""
Red Team v1 in shadow -- a blinded model pass on every material packet, written
to a file and nowhere else (Learning Loop v2, LL-4; A80).

    python -m altdata.redteam_shadow run [--date YYYY-MM-DD] [--db PATH]
                                         [--out-root DIR] [--dry-run]

The brief's section 2.7 and decision 10, ruled 25 Oct 2026. EL-9 (docs/change-
order-enterprise-layer-2026-09-27.md, section 6) is "a blinded model pass on
material packets (evidence shown, thesis withheld), output recorded in
review_changed", gated on Gate 1.5 complete and at least 30 graded packets. The
gate stands as ruled. This runs the same pass in SHADOW from now, so that when
the gate opens its record against the outcomes already exists:

  * A MATERIAL PACKET is a decision with a replay packet in the register
    (decision_packets; architecture 26.2 #3: "a material recommendation carries
    a packet"), its packet created on the day.
  * BLINDED: the prompt carries the evidence (EVIDENCE: the instrument, the
    direction, the book, the horizon, the setup, the entry condition, the
    invalidation, the time stop, the risk budget, the expected return and
    downside, the benchmark, the horizon alignment, the packet's cutoff and
    its data manifest's inputs) and withholds the thesis (WITHHELD: the thesis,
    the counter-thesis, the falsifiers, the mechanism, the operator's action,
    the status, review_changed, red_team, the outcome).
  * ONE CALL per packet, through altdata/model_meter.py (report redteam_shadow),
    with the narrative step's model. A packet whose file exists is not called
    again.
  * THE ONE WRITE: `<out-root>/docs/redteam/shadow/<date>-<packet>.md`.
    shadow_path() refuses any other target. The register is opened `mode=ro`,
    so neither review_changed nor red_team nor any other register field can be
    written from here; tools/validate_postmortems.py proves the register's file
    is byte for byte unchanged after a run.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Callable, Optional

REPO = Path(__file__).resolve().parent.parent
SUBDIR = Path("docs") / "redteam" / "shadow"
METHOD = "redteam-shadow-v1"

EVIDENCE = ("instrument", "direction", "book", "horizon", "setup_id", "engine_id",
            "edge_type", "decision_time", "entry_condition", "invalidation",
            "time_stop", "risk_budget", "expected_return", "expected_downside",
            "benchmark", "horizon_alignment", "size")
WITHHELD = ("thesis", "counter_thesis", "falsifiers", "mechanism", "operator_action",
            "status", "thesis_state", "review_changed", "red_team",
            "red_team_review_minutes", "outcome", "outcome_at", "falsifier_date")

SHADOW_PROMPT = (
    "You are a red team reviewing a proposed position before entry. You are shown "
    "the evidence the position was entered on. Its thesis is withheld from you on "
    "purpose.\n\n"
    "From the evidence alone:\n"
    "1. State the strongest case AGAINST taking this position, in at most five "
    "sentences.\n"
    "2. Name up to three observable conditions that, if they occurred before the "
    "horizon, would show the position wrong.\n"
    "3. Say whether the stated invalidation and time stop are consistent with the "
    "horizon, in one sentence.\n\n"
    "Rules, every one binding: use no number that is not in the evidence; do not "
    "guess the thesis; do not recommend a size, an order or a trade; write no "
    "preamble.\n\n"
    "THE EVIDENCE (JSON):\n")


class ShadowPathError(PermissionError):
    """The shadow pass tried to write outside its directory."""


def shadow_path(root: Path, day: str, packet_id: str) -> Path:
    """The one file the pass may write; anything else is refused."""
    base = (Path(root) / SUBDIR).resolve()
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(packet_id))
    p = (base / f"{day}-{safe}.md").resolve()
    if p.parent != base or not dt.date.fromisoformat(day):
        raise ShadowPathError(f"the shadow pass writes only under {base}")
    return p


def material_packets(day: str, db: Optional[str]) -> list[dict]:
    """The decisions whose replay packet was created on `day` (UTC date), with
    every decision column, over a read-only connection."""
    p = Path(db) if db else None
    if p is None or not p.exists():
        return []
    conn = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        have = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"decisions", "decision_packets"} <= have:
            return []
        return [dict(r) for r in conn.execute(
            "SELECT d.*, p.packet_id AS packet_id, p.created_at AS packet_created_at,"
            " p.available_at_cutoff AS packet_cutoff, p.data_manifest_json AS"
            " packet_manifest FROM decision_packets p JOIN decisions d"
            " ON d.id = p.decision_id WHERE substr(p.created_at, 1, 10) = ?"
            " ORDER BY p.created_at", (day,))]
    finally:
        conn.close()


def evidence(row: dict) -> dict:
    """The blinded evidence: the EVIDENCE fields and the packet's inputs, never a
    WITHHELD field."""
    ev = {k: row.get(k) for k in EVIDENCE if row.get(k) not in (None, "")}
    ev["packet_cutoff"] = row.get("packet_cutoff")
    try:
        man = json.loads(row.get("packet_manifest") or "{}")
    except ValueError:
        man = {}
    files = man.get("files") if isinstance(man, dict) else None
    if isinstance(files, (list, dict)):
        ev["inputs"] = sorted(files) if isinstance(files, dict) else sorted(
            str(f.get("path") if isinstance(f, dict) else f) for f in files)
    return ev


def prompt_of(row: dict) -> str:
    return SHADOW_PROMPT + json.dumps(evidence(row), indent=2, sort_keys=True, default=str)


def _call(prompt: str, db: Optional[str], packet_id: str) -> tuple[Optional[str], str]:
    from . import model_meter                                   # noqa: PLC0415
    from daily_cascade.narrative import DEFAULT_MODEL           # noqa: PLC0415
    cl, why = model_meter.client()
    if cl is None:
        return None, why
    try:
        with model_meter.scope(report="redteam_shadow", section=packet_id, db_path=db):
            resp = model_meter.create(cl, model=DEFAULT_MODEL, max_tokens=700,
                                      messages=[{"role": "user", "content": prompt}])
    except Exception as exc:                                    # noqa: BLE001
        return None, f"the call failed ({type(exc).__name__})"
    return "".join(getattr(b, "text", "") for b in resp.content).strip(), ""


def file_md(row: dict, day: str, prompt: str, text: str) -> str:
    return "\n".join([
        f"# Red Team v1, shadow: packet {row['packet_id']}", "",
        f"{METHOD}, {day}. Decision `{row['id']}`. Shadow only: EL-9's gate stands "
        f"(Gate 1.5 and 30 graded packets); this is recorded to a file and never to "
        f"review_changed or the register. Blinded: the thesis, the counter-thesis, "
        f"the falsifiers and the mechanism were withheld.", "",
        "## The red team's read", "", text, "",
        "## The prompt as sent", "", "```", prompt, "```", ""])


def run(day: Optional[str] = None, db: Optional[str] = None,
        root: Optional[Path] = None, dry_run: bool = False,
        call: Optional[Callable[[str], str]] = None) -> dict:
    """One blinded call per material packet of the day; one file each."""
    if day is None:
        from . import session                                   # noqa: PLC0415
        day = session.utc_iso()[:10]
    if db is None:
        from . import observations                              # noqa: PLC0415
        db = str(observations.DEFAULT_DB)
    root = Path(root or REPO)
    out = {"day": day, "packets": 0, "written": [], "kept": [], "failed": {},
           "dry_run": dry_run}
    for row in material_packets(day, db):
        out["packets"] += 1
        p = shadow_path(root, day, row["packet_id"])
        if p.exists():
            out["kept"].append(p.name)
            continue
        pr = prompt_of(row)
        if dry_run:
            out["written"].append(p.name)
            continue
        if call is not None:
            text, why = call(pr), ""
        else:
            text, why = _call(pr, db, row["packet_id"])
        if not text:
            out["failed"][p.name] = why or "an empty reply"
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(file_md(row, day, pr, text), encoding="utf-8", newline="\n")
        out["written"].append(p.name)
    return out


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m altdata.redteam_shadow")
    ap.add_argument("what", choices=("run",))
    ap.add_argument("--date", help="the packets' UTC creation date (default today)")
    ap.add_argument("--db")
    ap.add_argument("--out-root", help="the directory docs/redteam/shadow/ sits "
                                       "under (default: the checkout)")
    ap.add_argument("--dry-run", action="store_true",
                    help="list the packets and their files; no call, no write")
    a = ap.parse_args(argv)
    print(json.dumps(run(a.date, a.db, Path(a.out_root) if a.out_root else None,
                         a.dry_run), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
