#!/usr/bin/env python3
"""
The printed counts, checked and written by a tool (S1 part 1; the cloud-sessions
brief, section 3). No builder edits a count: the stitcher runs this once, after
the last merge.

    python tools/stitch_counts.py --check     # validate_audit_3a's count verdict
    python tools/stitch_counts.py --write     # rewrite each count in place

The counts come from validate_audit_3a (code_counts(), PRINTED_COUNTS,
ARCH_COUNTS, number(), printed_count_faults()), called, never copied, and from
check_registry's resolve_members() for each bulk block's expected_members. A
count is rewritten in the form its sentence already uses: words stay words
("one hundred and thirty-four"), numerals stay numerals. --write prints a table
of before and after; a sentence whose pattern is gone is a fault --write cannot
repair, and it says so.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import validate_audit_3a as A3                                  # noqa: E402

ARCH = Path("docs") / "chester-reports-architecture-v3.md"
REGISTRY = Path("metrics_registry.yaml")
ONES = ("zero one two three four five six seven eight nine ten eleven twelve "
        "thirteen fourteen fifteen sixteen seventeen eighteen nineteen").split()
TENS = {v: k for k, v in A3.TENS.items()}


def words(n: int) -> str:
    """134 -> 'one hundred and thirty-four', the form the printed counts use
    (A3.number reads it back)."""
    if n < 20:
        return ONES[n]
    if n < 100:
        t, o = divmod(n, 10)
        return TENS[t * 10] + (f"-{ONES[o]}" if o else "")
    h, r = divmod(n, 100)
    return f"{ONES[h]} hundred" + (f" and {words(r)}" if r else "")


def in_form(old: str, n: int) -> str:
    return str(n) if old.strip().isdigit() else words(n)


def _flatten(text: str) -> tuple[str, list[int]]:
    """The architecture document's box is a blockquote: read it with each "\\n> "
    as a space (as validate_audit_3a does), keeping a map back to the original."""
    flat, pos, i = [], [], 0
    while i < len(text):
        m = re.match(r"\n> ?", text[i:])
        if m:
            flat.append(" ")
            pos.append(i)
            i += m.end()
            continue
        flat.append(text[i])
        pos.append(i)
        i += 1
    pos.append(len(text))
    return "".join(flat), pos


def rewrite(text: str, table: list, counts: dict, where: str,
            flatten: bool = False) -> tuple[str, list[dict]]:
    """Each printed count in `table` set to the code's, in place."""
    flat, pos = _flatten(text) if flatten else (text, None)
    rows, edits = [], []
    for what, rx, key in table:
        m = re.search(rx, flat)
        if not m:
            rows.append({"where": where, "what": what, "printed": "(gone)",
                         "code": counts[key], "action": "FAULT: the sentence is gone"})
            continue
        old = m.group(1)
        try:
            n = A3.number(old)
        except (KeyError, ValueError):
            rows.append({"where": where, "what": what, "printed": old,
                         "code": counts[key], "action": "FAULT: not a number"})
            continue
        new = in_form(old, counts[key])
        same = n == counts[key]
        rows.append({"where": where, "what": what, "printed": old, "code": counts[key],
                     "action": "unchanged" if same else f"-> {new}"})
        if not same:
            a, b = m.span(1)
            if pos is not None:
                a, b = pos[a], pos[b]
            edits.append((a, b, new))
    for a, b, new in sorted(edits, reverse=True):
        text = text[:a] + new + text[b:]
    return text, rows


def bulk_counts(registry_text: str) -> dict:
    import yaml
    from check_registry import resolve_members                  # noqa: PLC0415
    reg = yaml.safe_load(registry_text) or {}
    out = {}
    for bid, block in (reg.get("bulk_imports") or {}).items():
        block = block or {}
        if block.get("expected_members") is None or not block.get("members_from"):
            continue
        try:
            out[bid] = (int(block["expected_members"]),
                        len(resolve_members(block["members_from"],
                                            block.get("member_key"))))
        except Exception as e:                                  # noqa: BLE001
            out[bid] = (int(block["expected_members"]), f"unresolved: {e}")
    return out


def rewrite_registry(text: str, counts: Optional[dict] = None
                     ) -> tuple[str, list[dict]]:
    """Each bulk block's expected_members set to its resolved count, its line's
    comment kept."""
    counts = bulk_counts(text) if counts is None else counts
    lines = text.split("\n")
    rows, inside, block = [], False, None
    for i, ln in enumerate(lines):
        if re.match(r"^bulk_imports:\s*$", ln):
            inside = True
            continue
        if inside and re.match(r"^\S", ln):
            inside = False
        if not inside:
            continue
        m = re.match(r"^  ([A-Za-z0-9_.\-]+):\s*$", ln)
        if m:
            block = m.group(1)
            continue
        m = re.match(r"^(    expected_members: )(\d+)(.*)$", ln)
        if m and block in counts:
            printed, code = counts[block]
            if not isinstance(code, int):
                rows.append({"where": "metrics_registry.yaml", "what": block,
                             "printed": printed, "code": code,
                             "action": "FAULT: members do not resolve"})
                continue
            rows.append({"where": "metrics_registry.yaml", "what": block,
                         "printed": printed, "code": code,
                         "action": "unchanged" if printed == code else f"-> {code}"})
            if printed != code:
                lines[i] = f"{m.group(1)}{code}{m.group(3)}"
    return "\n".join(lines), rows


def run(root: Path, write: bool, counts: Optional[dict] = None,
        bulk: Optional[dict] = None) -> tuple[list[dict], list[str]]:
    """(the rows, the files written). `counts` and `bulk` default to the code's;
    a fixture passes its own."""
    counts = A3.code_counts() if counts is None else counts
    rows, written = [], []
    for rel, table, flat in ((Path("CLAUDE.md"), A3.PRINTED_COUNTS, False),
                             (ARCH, A3.ARCH_COUNTS, True)):
        p = root / rel
        raw = p.read_bytes()
        crlf = b"\r\n" in raw
        text = raw.decode("utf-8").replace("\r\n", "\n")
        new, r = rewrite(text, table, counts, rel.as_posix(), flatten=flat)
        rows += r
        if write and new != text:
            p.write_bytes((new.replace("\n", "\r\n") if crlf else new).encode("utf-8"))
            written.append(rel.as_posix())
    p = root / REGISTRY
    raw = p.read_bytes()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8").replace("\r\n", "\n")
    new, r = rewrite_registry(text, bulk)
    rows += r
    if write and new != text:
        p.write_bytes((new.replace("\n", "\r\n") if crlf else new).encode("utf-8"))
        written.append(REGISTRY.as_posix())
    return rows, written


def table(rows: list[dict]) -> str:
    out = ["| Where | Count | Printed | Code | Action |", "|---|---|---|---|---|"]
    out += [f"| {r['where']} | {r['what']} | {r['printed']} | {r['code']} | "
            f"{r['action']} |" for r in rows]
    return "\n".join(out)


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="the printed counts (S1 part 1)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="fail on any count that "
                   "disagrees with the code (validate_audit_3a's verdict)")
    g.add_argument("--write", action="store_true", help="rewrite each count in place")
    ap.add_argument("--root", default=str(REPO), help="the tree (default this repo)")
    a = ap.parse_args(argv)
    rows, written = run(Path(a.root), a.write)
    print(table(rows))
    faults = [r for r in rows if r["action"].startswith("FAULT")]
    drift = [r for r in rows if r["action"].startswith("->")]
    if a.write:
        print(f"\nwrote {', '.join(written) if written else 'nothing'}"
              f" ({len(drift)} count(s) changed)")
        return 1 if faults else 0
    print(f"\n{len(rows)} counts: {len(drift)} disagree, {len(faults)} fault(s)")
    return 1 if (faults or drift) else 0


if __name__ == "__main__":
    raise SystemExit(main())
