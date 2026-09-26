"""
manual_input -- the one door for an operator-typed figure into the observation store.

    python tools/manual_input.py KEY VALUE OBSERVED_AT "NOTE"
    python tools/manual_input.py manual.sep_median_12m 3.625 2026-09-17 \
        "SEP Sep 2026, 2027 year-end median dot, midpoint"
    python tools/manual_input.py --list

Signal-triage order §1.10: "every operator-entered figure is a manual_input writer
(a small CLI that stamps available_at and run_id). No block reads a file." Some
numbers have no free machine source -- the SEP median dot, a FedWatch probability
until G-4 settles one, the CBO deficit path, IG new-issue concessions -- and the
alternative to this CLI is a figure pasted into a renderer or a YAML file, where
it has no available_at, no registry entry and no history.

WHAT IT WRITES. ONE observation per call:

  registry_key  KEY, which must be REGISTERED in metrics_registry.yaml with
                `source: manual_input` -- an unregistered key is refused, so a
                typo cannot start a new series
  observed_at   OBSERVED_AT, the date the figure describes or was published
                (YYYY-MM-DD); never after today's session
  available_at  NOW, microsecond UTC. §1.4: "Manual inputs carry the date the
                operator entered them" -- the instant WE knew it, not the instant
                the source published it, which is what keeps an as-of join honest
                about a figure typed in a week late
  value_num     VALUE
  value_text    NOTE -- where the figure came from, in the operator's words. Kept
                on the same row, so the number and its provenance cannot be
                separated
  run_id        session.new_run_id("manual_input")
  source        manual_input

A CORRECTION IS A NEW ENTRY, not an edit: re-enter the same KEY and OBSERVED_AT,
and the later available_at supersedes the earlier one in the as-of join while the
mistake stays on record. Nothing here updates or deletes.

UNITS ARE CHECKED where the registry declares a bounded one: a `fraction` must lie
in [0, 1], so "72" for a 72% probability is refused rather than stored as 7,200%.
"""

from __future__ import annotations

import argparse
import datetime as dt
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOURCE = "manual_input"


def registry() -> dict:
    import yaml  # noqa: PLC0415
    with (REPO / "metrics_registry.yaml").open(encoding="utf-8") as fp:
        return (yaml.safe_load(fp) or {}).get("metrics") or {}


def manual_keys(reg: dict | None = None) -> dict[str, dict]:
    reg = registry() if reg is None else reg
    return {k: v for k, v in reg.items()
            if isinstance(v, dict) and v.get("source") == SOURCE}


class Refused(ValueError):
    """An entry that must not be written. The message says why."""


def validate(key: str, value: str, observed_at: str, note: str,
             keys: dict[str, dict]) -> tuple[float, str]:
    from altdata import session  # noqa: PLC0415
    if key not in keys:
        raise Refused(f"{key!r} is not a registered manual_input key. Register "
                      f"it in metrics_registry.yaml with `source: {SOURCE}` "
                      f"first; known keys: {', '.join(sorted(keys)) or 'none'}")
    try:
        num = float(value)
    except ValueError:
        raise Refused(f"value {value!r} is not a number") from None
    if not math.isfinite(num):
        raise Refused(f"value {value!r} is not finite")
    units = keys[key].get("units")
    if units == "fraction" and not 0.0 <= num <= 1.0:
        raise Refused(f"{key} is a fraction (0..1); {num} is out of range -- "
                      f"enter 72% as 0.72")
    try:
        day = dt.date.fromisoformat(observed_at)
    except ValueError:
        raise Refused(f"observed_at {observed_at!r} is not YYYY-MM-DD") from None
    today = session.session_date_obj()
    if day > today:
        raise Refused(f"observed_at {day} is after today's session ({today}); a "
                      f"figure cannot describe a day that has not happened")
    if not note or not note.strip():
        raise Refused("a note is required: where the figure came from")
    return num, day.isoformat()


def write(key: str, value: str, observed_at: str, note: str,
          db_path: str | None = None) -> dict:
    """Validate and write one observation. Raises Refused; returns the row."""
    from altdata import observations, session  # noqa: PLC0415
    num, day = validate(key, value, observed_at, note, manual_keys())
    run_id = session.new_run_id(SOURCE)
    available = observations.canonical_instant(
        session.utc_iso(timespec="microseconds"))
    with observations.ObservationStore(db_path) as db:
        # value_num AND value_text on one row: the schema allows both, and
        # write_many() only ever sets one, so this is the one direct insert. The
        # instants are canonicalised exactly as write_many() would.
        cur = db.conn.execute(
            "INSERT OR IGNORE INTO observations (registry_key, instrument, "
            "observed_at, available_at, ingested_at, value_num, value_text, "
            "source, run_id, availability_kind) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (key, None, day, available, available, num, note.strip(), SOURCE,
             run_id, "ingest_instant"))
        db.conn.commit()
        written = cur.rowcount
    return {"registry_key": key, "observed_at": day, "available_at": available,
            "value": num, "note": note.strip(), "run_id": run_id,
            "written": written}


def list_keys(db_path: str | None = None) -> int:
    from altdata import observations  # noqa: PLC0415
    keys = manual_keys()
    with observations.ObservationStore(db_path) as db:
        for k in sorted(keys):
            last = db.latest_as_of(k)
            held = (f"{last['observed_at']} = {last['value_num']} "
                    f"({last['value_text']})" if last else "no entry yet")
            print(f"{k:34} {keys[k].get('units', ''):9} {held}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Write one operator-entered figure to the observation store.")
    p.add_argument("key", nargs="?")
    p.add_argument("value", nargs="?")
    p.add_argument("observed_at", nargs="?", help="YYYY-MM-DD")
    p.add_argument("note", nargs="?", help="where the figure came from")
    p.add_argument("--list", action="store_true",
                   help="registered manual keys and their latest entry")
    p.add_argument("--db", default=None, help="observation store path")
    a = p.parse_args(argv)
    if a.list:
        return list_keys(a.db)
    if not all((a.key, a.value, a.observed_at, a.note)):
        p.error("KEY VALUE OBSERVED_AT NOTE are all required (or --list)")
    try:
        row = write(a.key, a.value, a.observed_at, a.note, a.db)
    except Refused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {row['registry_key']} {row['observed_at']} = {row['value']} "
          f"available_at {row['available_at']} run {row['run_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
