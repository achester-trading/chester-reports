"""
The catalogue: one place to list, search and read what the system holds.
(AUD-3a item 5, 14 Oct 2026)

    python -m altdata.catalogue list [--domain D] [--kind K] [--source S] [--cadence C]
    python -m altdata.catalogue search TEXT
    python -m altdata.catalogue show ID [--db PATH]
    python -m altdata.catalogue commands [--domain D]

Until this module there were 101 per-domain commands and no list of them, and
finding what a key meant took metrics_registry.yaml, source_registry.yaml,
altdata/derived.py and the writer's source side by side. Everything here is read
from those files and config/catalogue_commands.yaml; nothing is computed that a
report computes differently.

  list      every resolved key (bulk blocks expanded), one line each: its units,
            its delta rule, its source, its cadence. Filters:
              --domain   the key's source's domains in source_registry.yaml
              --kind     metric (registered one by one) or bulk (from a block),
                         or its declared series_kind or family (yield, price ...)
              --source   a source id, matched against `source` and `sources`
              --cadence  its freq, else its native_horizon
  search    case-insensitive, over ids, descriptions (a bulk member's is its
            block's) and aliases (config/display_labels.yaml, the tape's aliases)
  show      every registry field, the resolved units and delta rule, the block it
            came from, the command that produces it; with --db, its row count and
            its first and newest observation, read-only (mode=ro)
  commands  the declared per-domain commands, one line each
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
_CACHE: dict = {}


def _yaml(rel: str) -> dict:
    if rel not in _CACHE:
        import yaml                                             # noqa: PLC0415
        p = REPO / rel
        _CACHE[rel] = (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) \
            if p.exists() else {}
    return _CACHE[rel]


def registry() -> dict:
    return _yaml("metrics_registry.yaml")


def sources() -> dict:
    return _yaml("source_registry.yaml").get("sources") or {}


def commands() -> dict:
    return _yaml("config/catalogue_commands.yaml").get("commands") or {}


def resolved() -> dict:
    if "_resolved" not in _CACHE:
        from . import derived                                   # noqa: PLC0415
        _CACHE["_resolved"] = derived.resolve_registry(registry())
    return _CACHE["_resolved"]


def aliases() -> dict[str, list[str]]:
    """{key: [the words a reader may use for it]}: display labels and the tape's."""
    out: dict[str, list[str]] = {}
    for k, v in (_yaml("config/display_labels.yaml") or {}).items():
        if isinstance(v, str):
            out.setdefault(str(k), []).append(v)
        elif isinstance(v, dict):
            for kk, vv in v.items():
                if isinstance(vv, str):
                    out.setdefault(str(kk), []).append(vv)
    for t in (_yaml("config/reporting_stack.yaml").get("tape") or []):
        if isinstance(t, dict) and t.get("daily"):
            out.setdefault(str(t["daily"]), []).extend(
                [str(t.get("label") or "")] + [str(a) for a in t.get("aliases") or []])
    return out


def description(key: str, e: dict) -> str:
    """The entry's own description, or its bulk block's."""
    d = e.get("description")
    if not d and e.get("bulk_block"):
        d = ((registry().get("bulk_imports") or {}).get(e["bulk_block"]) or {}).get(
            "description")
    return " ".join(str(d or "").split())


def key_sources(e: dict) -> list[str]:
    return list(e.get("sources") or ([e["source"]] if e.get("source") else []))


def domains(e: dict) -> list[str]:
    out: list[str] = []
    for s in key_sources(e):
        for d in (sources().get(s) or {}).get("domain") or []:
            if d not in out:
                out.append(d)
    return out


def kinds(key: str, e: dict) -> list[str]:
    reg = registry()
    return [k for k in ("bulk" if e.get("bulk_block") else "metric",
                        (reg.get("series_kinds") or {}).get(key),
                        (reg.get("families") or {}).get(key)) if k]


def cadence(e: dict) -> str:
    return str(e.get("freq") or e.get("native_horizon") or "")


def writer_modules(e: dict) -> list[str]:
    """The modules source_registry.yaml says implement the key's sources."""
    out: list[str] = []
    for s in key_sources(e):
        ib = (sources().get(s) or {}).get("implemented_by")
        for part in (ib if isinstance(ib, list) else str(ib or "").replace(",", " ").split()):
            if str(part).endswith(".py") and part not in out:
                out.append(str(part))
    return out


def producing_commands(e: dict) -> list[str]:
    """The `python -m` commands in config/catalogue_commands.yaml that run one of
    the key's sources (a writer module with no command of its own, like the price
    pull, is run by the command that declares its source -- altdata.feeds)."""
    want = set(key_sources(e))
    return sorted(f"python -m {mod}" for mod, c in commands().items()
                  if want & set(c.get("sources") or []))


def rows(domain: Optional[str] = None, kind: Optional[str] = None,
         source: Optional[str] = None, cad: Optional[str] = None) -> list[dict]:
    from . import derived                                       # noqa: PLC0415
    out = []
    for k, e in sorted(resolved().items()):
        if domain and domain not in domains(e):
            continue
        if kind and kind not in kinds(k, e):
            continue
        if source and source not in key_sources(e):
            continue
        if cad and cad != cadence(e):
            continue
        out.append({"key": k, "units": e.get("units"),
                    "delta": derived.delta_unit_for(k)[0],
                    "source": ",".join(key_sources(e)), "cadence": cadence(e)})
    return out


def search(text: str) -> list[dict]:
    t = text.lower()
    al = aliases()
    out = []
    for k, e in sorted(resolved().items()):
        hay = " ".join([k, description(k, e), *al.get(k, [])]).lower()
        if t in hay:
            out.append({"key": k, "description": description(k, e)[:110]})
    return out


def show(key: str, db: Optional[str] = None) -> Optional[dict]:
    from . import derived                                       # noqa: PLC0415
    e = resolved().get(key)
    if e is None:
        return None
    du, why = derived.delta_unit_for(key)
    allow, awhy = derived.staleness_allowance_of(e, key)
    out: dict[str, Any] = {
        "key": key, "fields": {k: v for k, v in sorted(e.items())},
        "description": description(key, e),
        "units": e.get("units"), "level_prints_as": derived.level_units_of(e),
        "delta_unit": du, "delta_rule": why,
        "staleness_allowance": allow, "staleness_rule": awhy,
        "bulk_block": e.get("bulk_block"), "domains": domains(e),
        "writers": writer_modules(e), "commands": producing_commands(e),
        "aliases": aliases().get(key, []),
        # The source's terms as read (ruling 3 of 17 Oct 2026): the URL, the date
        # read and the re-read cadence, where the source registry records them.
        "terms": {s: {f: (sources().get(s) or {}).get(f)
                      for f in ("terms_url", "terms_read", "terms_reread")}
                  for s in key_sources(e) if (sources().get(s) or {}).get("terms_url")}}
    if db:
        out["store"] = store_facts(db, key)
    return out


def store_facts(db: str, key: str) -> dict:
    """Row count, first and newest observation, read-only. A bars.* key reads the
    bars table."""
    sys.path.insert(0, str(REPO / "tools"))
    import check_store_registry as csr                          # noqa: PLC0415
    conn = csr.open_ro(db)
    try:
        if key.startswith("bars."):
            inst = key.split(".")[1]
            n, first, newest = conn.execute(
                "SELECT COUNT(*), MIN(observed_at), MAX(observed_at) FROM bars "
                "WHERE instrument = ?", (inst,)).fetchone()
        else:
            n, first, newest = conn.execute(
                "SELECT COUNT(*), MIN(observed_at), MAX(observed_at) FROM "
                "observations WHERE registry_key = ?", (key,)).fetchone()
    finally:
        conn.close()
    return {"rows": n, "first_observed": first, "newest_observed": newest}


def _print_rows(rs: list[dict]) -> None:
    for r in rs:
        print(f"{r['key']:<52} {str(r['units']):<15} {r['delta']:<8} "
              f"{r['source']:<22} {r['cadence']}")
    print(f"({len(rs)} keys)")


def main(argv: Optional[list[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m altdata.catalogue",
                                 description="List, search and read the registry.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("list")
    pl.add_argument("--domain")
    pl.add_argument("--kind")
    pl.add_argument("--source")
    pl.add_argument("--cadence")
    ps = sub.add_parser("search")
    ps.add_argument("text")
    pw = sub.add_parser("show")
    pw.add_argument("id")
    pw.add_argument("--db")
    pc = sub.add_parser("commands")
    pc.add_argument("--domain")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        _print_rows(rows(a.domain, a.kind, a.source, a.cadence))
    elif a.cmd == "search":
        rs = search(a.text)
        for r in rs:
            print(f"{r['key']:<52} {r['description']}")
        print(f"({len(rs)} matches)")
    elif a.cmd == "show":
        try:
            s = show(a.id, a.db)
        except Exception as exc:                                # noqa: BLE001
            print(f"cannot read the store: {type(exc).__name__}: {exc}")
            return 2
        if s is None:
            print(f"{a.id}: no registry entry (try `search`)")
            return 1
        print(f"{s['key']}\n  {s['description']}")
        for k in ("units", "level_prints_as", "delta_unit", "delta_rule",
                  "staleness_allowance", "staleness_rule", "bulk_block", "domains",
                  "writers", "commands", "aliases"):
            print(f"  {k:<20}: {s[k]}")
        for src, t in s["terms"].items():
            print(f"  terms ({src}){'':<{max(0, 11 - len(src))}}: {t['terms_url']}, read "
                  f"{t['terms_read']}, re-read {t['terms_reread']}")
        print("  registry fields:")
        for k, v in s["fields"].items():
            if k != "description":
                print(f"    {k:<24}: {v}")
        if "store" in s:
            print(f"  store               : {s['store']['rows']} rows, first "
                  f"{s['store']['first_observed']}, newest "
                  f"{s['store']['newest_observed']}")
    else:
        for mod, c in sorted(commands().items()):
            if a.domain and c.get("domain") != a.domain:
                continue
            print(f"python -m {mod:<40} [{c.get('domain')}] {c.get('line')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
