"""
The pillar-to-dial mapping, read. (Audit #3 section G; N item 8)

    from monthly_macro import pillars
    pillars.for_dial("macro")       # the pillars feeding it, heaviest first
    pillars.dimension_for("1")      # 'growth' -- what the Monthly READS
    pillars.unsourced()             # what a pillar wants and cannot get

config/pillars.yaml carries the declaration and its reasoning; this module is the
reader. It computes nothing about the market: a pillar has no state, and where its
metrics are already a dimension the caller reads the object rather than deriving a
second reading of the same series under another name.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
PILLARS_PATH = REPO / "config" / "pillars.yaml"

# The three dials. Named here so a typo in the config is a failure rather than a
# fourth dial nobody declared.
DIALS = ("macro", "vol", "gamma")

_CACHE: Optional[dict] = None


def load(path: Optional[Path] = None, reload: bool = False) -> dict:
    global _CACHE
    if _CACHE is not None and not reload and path is None:
        return _CACHE
    import yaml                                                # noqa: PLC0415
    with (path or PILLARS_PATH).open(encoding="utf-8") as fp:
        data = yaml.safe_load(fp) or {}
    out = {"version": data.get("version"),
           "dials": data.get("dials") or {},
           "pillars": {}}
    for num, body in (data.get("pillars") or {}).items():
        entry = dict(body or {})
        entry["number"] = str(num)
        entry.setdefault("status", "active")
        out["pillars"][str(num)] = entry
    if path is None:
        _CACHE = out
    return out


def all_pillars(path: Optional[Path] = None) -> dict:
    return load(path)["pillars"]


def get(number: str, path: Optional[Path] = None) -> dict:
    p = all_pillars(path)
    if str(number) not in p:
        raise KeyError(f"no pillar {number!r} in {PILLARS_PATH.name}; "
                       f"declared: {sorted(p)}")
    return p[str(number)]


def for_dial(dial: str, path: Optional[Path] = None) -> list[dict]:
    """The pillars feeding a dial, heaviest first. Empty for gamma, by design."""
    return sorted((p for p in all_pillars(path).values()
                   if p.get("dial") == dial),
                  key=lambda p: (-float(p.get("weight") or 0), p["number"]))


def dimension_for(number: str, path: Optional[Path] = None) -> Optional[str]:
    """The object dimension this pillar READS, or None with a recorded reason."""
    return get(number, path).get("from_object")


def weight_total(dial: str, path: Optional[Path] = None) -> float:
    return round(sum(float(p.get("weight") or 0) for p in for_dial(dial, path)), 6)


def unsourced(path: Optional[Path] = None) -> list[dict]:
    """Every gap a pillar declares, with what it needs and why it matters."""
    out = []
    for p in sorted(all_pillars(path).values(), key=lambda x: x["number"]):
        for gap in p.get("not_yet_sourced") or []:
            out.append({"pillar": p["number"], "name": p.get("name"), **gap})
    return out


def summary(path: Optional[Path] = None) -> dict:
    reg = load(path)
    return {
        "version": reg["version"],
        "pillars": len(reg["pillars"]),
        "by_dial": {d: [p["number"] for p in for_dial(d, path)] for d in DIALS},
        "weights": {d: weight_total(d, path) for d in DIALS},
        "reading_a_dimension": {p["number"]: p.get("from_object")
                                for p in reg["pillars"].values()
                                if p.get("from_object")},
        "no_dimension": {p["number"]: p.get("from_object_absent_reason")
                         for p in reg["pillars"].values()
                         if not p.get("from_object")},
        "relocated": [p["number"] for p in reg["pillars"].values()
                      if p.get("status") == "relocated"],
        "unsourced": len(unsourced(path)),
    }


def _main(argv: list[str]) -> int:
    import argparse
    import json
    p = argparse.ArgumentParser(description="The pillar-to-dial mapping.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary")
    sub.add_parser("gaps")
    d = sub.add_parser("dial")
    d.add_argument("name", choices=DIALS)
    a = p.parse_args(argv)
    if a.cmd == "summary":
        print(json.dumps(summary(), indent=2, sort_keys=True))
    elif a.cmd == "gaps":
        for g in unsourced():
            print(f"  pillar {g['pillar']} ({g['name']}): {g['what']}")
            print(f"    needs {', '.join(g.get('needs') or [])}")
    else:
        for pl in for_dial(a.name):
            print(f"  {pl['number']:>2}  w={pl.get('weight'):<5} "
                  f"{pl.get('name'):<34} reads "
                  f"{pl.get('from_object') or '(no dimension)'}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
