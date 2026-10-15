"""
The store against the registry. (AUD-3a item 1, 14 Oct 2026)

    python -m tools.check_store_registry --db PATH [--as-of ISO] [--verbose]

Opens the store READ-ONLY (SQLite mode=ro) and prints what the registry and the
store disagree about. It writes nothing, anywhere.

  1. UNREGISTERED. Keys the store holds -- the observations table's registry_key,
     and the bars table's instruments as bars.<id> and bars.<id>.volume -- that
     resolve to no registry entry (altdata/derived.py's resolver, bulk blocks
     expanded) and to no non_metric.
  2. REGISTERED, NO ROWS. Registry keys with no row in the store. Printed and
     counted, but it does NOT set the exit code: the registry also declares what
     lives outside these two tables -- the exposure profiles, the pin log's
     columns, the register's grades -- so this list is never empty and is read,
     not gated. Keys declared not_yet_sourced or superseded are counted apart.
  3. STALE. Keys whose newest observed_at is older than their own staleness
     allowance, by derived.staleness_allowance() and derived.sessions_between():
     the same rule every report's confidence derives from.
  4. OFF-LIST SOURCES. Stored `source` strings that altdata/source_ids.py reads as
     no id in source_registry.yaml (AUD-3a item 4).

Exit 0 when lists 1, 3 and 4 are empty; 1 when any holds a finding; 2 when the
store cannot be opened. The gate runs it on a synthetic store; the box command is
in docs/briefs/aud-3a-notes.md.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPO = Path(__file__).resolve().parent.parent
QUIET_STATUSES = ("not_yet_sourced", "superseded")
# Blocks whose members are a table's or a file's COLUMNS, or a vocabulary's values
# -- registered so a new column cannot appear unregistered, never stored as keys.
# Left out of list 2, where they would read as 101 missing series.
FORMAT_BLOCKS = ("pin_log_columns", "event_columns", "event_types")


def open_ro(db: str) -> sqlite3.Connection:
    """The store, read-only. Raises when it does not exist or is no database."""
    p = Path(db)
    if not p.is_file():
        raise FileNotFoundError(f"no store at {db}")
    conn = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True)
    conn.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
    return conn


def _tables(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


def stored(conn: sqlite3.Connection) -> dict[str, dict]:
    """{key: {"newest": observed_at, "sources": set}} over both tables."""
    out: dict[str, dict] = {}
    t = _tables(conn)
    if "observations" in t:
        for key, newest in conn.execute(
                "SELECT registry_key, MAX(observed_at) FROM observations "
                "GROUP BY registry_key"):
            out[key] = {"newest": newest, "sources": set()}
        for key, src in conn.execute(
                "SELECT DISTINCT registry_key, source FROM observations"):
            out[key]["sources"].add(src)
    if "bars" in t:
        for inst, newest, vol in conn.execute(
                "SELECT instrument, MAX(observed_at), MAX(COALESCE(volume, 0)) "
                "FROM bars GROUP BY instrument"):
            out[f"bars.{inst}"] = {"newest": newest, "sources": set()}
            if vol and vol > 0:
                out[f"bars.{inst}.volume"] = {"newest": newest, "sources": set()}
        for inst, src in conn.execute("SELECT DISTINCT instrument, source FROM bars"):
            out[f"bars.{inst}"]["sources"].add(src)
    return out


def non_metric_names(reg: dict) -> set[str]:
    names: set[str] = set()
    for group in (reg.get("non_metrics") or {}).values():
        names |= set(group or [])
    names |= set((reg.get("reserved") or {}).get("members") or [])
    return names


def check(db: str, as_of: Optional[str] = None, reg: Optional[dict] = None) -> dict:
    """The four lists, as data. Raises when the store cannot be opened."""
    import yaml                                                 # noqa: PLC0415
    from altdata import derived, session, source_ids            # noqa: PLC0415
    reg = reg if reg is not None else yaml.safe_load(
        (REPO / "metrics_registry.yaml").read_text(encoding="utf-8"))
    resolved = derived.resolve_registry(reg)
    nonm = non_metric_names(reg)
    conn = open_ro(db)
    try:
        have = stored(conn)
    finally:
        conn.close()
    as_of = as_of or session.utc_iso()
    unregistered = sorted(k for k in have
                          if k not in resolved and k.rsplit(".", 1)[-1] not in nonm
                          and k not in nonm)
    quiet, no_rows = [], []
    for k in sorted(resolved):
        e = resolved[k] or {}
        if k in have or e.get("bulk_block") in FORMAT_BLOCKS:
            continue
        (quiet if (e.get("status_extra") or e.get("status")) in QUIET_STATUSES
         else no_rows).append(k)
    stale = []
    for k in sorted(have):
        if k not in resolved or not have[k]["newest"]:
            continue
        allow, why = derived.staleness_allowance_of(resolved[k], k)
        if allow is None:
            continue
        n, _basis = derived.sessions_between(str(have[k]["newest"])[:10], as_of[:10])
        if n > allow:
            stale.append({"key": k, "newest": str(have[k]["newest"])[:10],
                          "sessions": n, "allowance": allow, "why": why})
    srcs = sorted({s for v in have.values() for s in v["sources"]
                   if source_ids.canonical(s) is None}, key=str)
    return {"db": db, "as_of": as_of, "stored": len(have),
            "unregistered": unregistered, "no_rows": no_rows, "quiet": quiet,
            "stale": stale, "off_list_sources": srcs}


def report(r: dict, verbose: bool = False) -> str:
    line = "=" * 74
    out = [line, f"The store against the registry -- {r['db']} (read-only), "
           f"as of {r['as_of'][:16]}", line,
           f"  keys stored                  : {r['stored']}",
           f"  1. stored, unregistered      : {len(r['unregistered'])}"]
    out += [f"       {k}" for k in r["unregistered"]]
    by_ns: dict[str, int] = {}
    for k in r["no_rows"]:
        by_ns[k.split(".", 1)[0]] = by_ns.get(k.split(".", 1)[0], 0) + 1
    out.append(f"  2. registered, no rows       : {len(r['no_rows'])} (read, not "
               f"gated; {len(r['quiet'])} more declared not_yet_sourced or "
               f"superseded)")
    import textwrap                                             # noqa: PLC0415
    out += textwrap.wrap(" · ".join(f"{ns} {n}" for ns, n in sorted(by_ns.items())),
                         66, initial_indent="       ", subsequent_indent="       ")
    if verbose:
        out += [f"         {k}" for k in r["no_rows"]]
    out.append(f"  3. stale                     : {len(r['stale'])}")
    out += [f"       {s['key']}: newest {s['newest']}, {s['sessions']} sessions, "
            f"allowed {s['allowance']} ({s['why']})" for s in r["stale"]]
    out.append(f"  4. sources on no list        : {len(r['off_list_sources'])}")
    out += [f"       {s!r}" for s in r["off_list_sources"]]
    clean = not (r["unregistered"] or r["stale"] or r["off_list_sources"])
    out += ["", "  CLEAN" if clean else "  FINDINGS -- lists 1, 3 and 4 set the exit "
            "code", line]
    return "\n".join(out)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="The store against the registry "
                                 "(read-only)")
    ap.add_argument("--db", required=True)
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--verbose", "-v", action="store_true")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        r = check(a.db, a.as_of)
    except (sqlite3.Error, OSError) as exc:
        print(f"cannot open the store: {type(exc).__name__}: {exc}")
        return 2
    print(report(r, a.verbose))
    return 0 if not (r["unregistered"] or r["stale"] or r["off_list_sources"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
