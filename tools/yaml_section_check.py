#!/usr/bin/env python3
"""
After a merge at a stitch: every YAML file both parents changed since their
merge base, each second-level key's top-level section in the merge against its
section in each parent (D42.12, 29 Oct 2026; B86b).

    python tools/yaml_section_check.py [MERGE_COMMIT]     # default HEAD

A key (a mapping's child, or a list item's `id`/`key`/`label`) that sits under one
top-level section in a parent and another in the merge has MOVED SECTION: the
check prints it and exits 1, and the stitch stops. The case that made this a
step: the b70 merge at the chain-8 assembly put 88 `families` lines inside
`member_overrides` with no conflict marker.
"""

from __future__ import annotations

import subprocess
import sys

import yaml


def _git(*a: str) -> str:
    return subprocess.run(["git", *a], capture_output=True, check=True).stdout.decode("utf-8")


def _show(ref: str, path: str):
    try:
        return yaml.safe_load(_git("show", f"{ref}:{path}"))
    except subprocess.CalledProcessError:
        return None


def placements(doc) -> dict:
    """{child key: top-level section} for every top-level mapping's children."""
    out: dict = {}
    if not isinstance(doc, dict):
        return out
    for top, v in doc.items():
        kids = []
        if isinstance(v, dict):
            kids = list(v)
        elif isinstance(v, list):
            kids = [next((x[k] for k in ("id", "key", "label") if isinstance(x, dict)
                          and isinstance(x.get(k), str)), None) for x in v]
        for k in kids:
            if k is not None:
                out.setdefault(str(k), set()).add(str(top))
    return out


def main(argv=None) -> int:
    merge = (argv or sys.argv[1:] or ["HEAD"])[0]
    parents = _git("rev-list", "--parents", "-n", "1", merge).split()[1:]
    if len(parents) != 2:
        print(f"{merge} is not a two-parent merge")
        return 2
    p1, p2 = parents
    base = _git("merge-base", p1, p2).strip()
    touched = [set(_git("diff", "--name-only", base, p).split()) for p in parents]
    both = sorted(f for f in touched[0] & touched[1] if f.endswith((".yaml", ".yml")))
    bad = []
    for f in both:
        m = placements(_show(merge, f))
        for p in parents:
            for k, tops in placements(_show(p, f)).items():
                # moved: it left a section the parent had it in, and sits in one
                # the parent did not (a key may live in two sections, metrics and
                # families, so overlap alone proves nothing).
                if k in m and (tops - m[k]) and (m[k] - tops):
                    bad.append(f"{f}: '{k}' is under {sorted(tops)} in {p[:8]} "
                               f"but under {sorted(m[k])} in the merge")
    print(f"{merge[:12]}: {len(both)} YAML file(s) both sides touched: {both}")
    for b in bad[:40]:
        print("  MOVED", b)
    print(f"{len(bad)} key(s) moved section" if bad else "no key moved section")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
