"""
Does the venv satisfy requirements.txt? (a55, 20 Oct 2026: chain-3 added
jsonschema to requirements.txt, nothing installs requirements on the box -- `make
deploy` does not pip install -- and the Security Master export refused to write
until the package was installed by hand.)

    python -m altdata.requirements_check [--requirements PATH]

REPORT-ONLY. Each requirement's name and specifier against the installed
distribution's version through importlib.metadata: no network, no install, no
import of the package itself. Exit 0 when every requirement is satisfied, 1 when
one is missing or out of range, and one line either way. The heartbeat prints the
line as a WARNING and never changes its verdict or exit code. The fix is the
operator's, on the box:

    .venv/bin/pip install -r requirements.txt

A line with an environment marker that does not apply here (`; sys_platform ==
...`) is skipped; a URL or editable requirement is not checked and is counted.
"""

from __future__ import annotations

import argparse
import re
import sys
from importlib import metadata
from pathlib import Path
from typing import Callable, Optional

REPO = Path(__file__).resolve().parent.parent
FIX = ".venv/bin/pip install -r requirements.txt"
NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(\[[^\]]*\])?\s*(.*)$")


def parse(text: str) -> list[dict]:
    """[{name, spec, marker, line}] from requirements.txt, comments dropped."""
    out = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "git+", "http")):
            if line:
                out.append({"name": None, "spec": "", "marker": None, "line": line})
            continue
        req, _, marker = line.partition(";")
        m = NAME_RE.match(req)
        if not m:
            continue
        out.append({"name": m.group(1), "spec": m.group(3).strip(),
                    "marker": marker.strip() or None, "line": line})
    return out


def _satisfies(version: str, spec: str) -> Optional[bool]:
    """True/False by the specifier; None when it cannot be evaluated here."""
    if not spec:
        return True
    try:
        from packaging.specifiers import SpecifierSet           # noqa: PLC0415
        from packaging.version import Version                   # noqa: PLC0415
        return Version(version) in SpecifierSet(spec)
    except Exception:                                           # noqa: BLE001
        return None


def _marker_applies(marker: Optional[str]) -> bool:
    if not marker:
        return True
    try:
        from packaging.markers import Marker                    # noqa: PLC0415
        return Marker(marker).evaluate()
    except Exception:                                           # noqa: BLE001
        return True


def check(text: str, version_of: Callable[[str], str] = metadata.version) -> dict:
    """{"missing": [name], "out_of_range": [(name, version, spec)], "unchecked": n,
    "checked": n}."""
    missing, bad, unchecked, checked = [], [], 0, 0
    for r in parse(text):
        if r["name"] is None:
            unchecked += 1
            continue
        if not _marker_applies(r["marker"]):
            continue
        checked += 1
        try:
            v = version_of(r["name"])
        except metadata.PackageNotFoundError:
            missing.append(r["name"])
            continue
        ok = _satisfies(v, r["spec"])
        if ok is False:
            bad.append((r["name"], v, r["spec"]))
        elif ok is None:
            unchecked += 1
    return {"missing": missing, "out_of_range": bad, "unchecked": unchecked,
            "checked": checked}


def line(r: dict) -> str:
    if not r["missing"] and not r["out_of_range"]:
        return f"requirements: all {r['checked']} satisfied"
    parts = []
    if r["missing"]:
        parts.append("missing " + ", ".join(r["missing"]))
    if r["out_of_range"]:
        parts.append("out of range " + ", ".join(f"{n} {v} (wants {s})"
                                                for n, v, s in r["out_of_range"]))
    return f"requirements: {'; '.join(parts)} -- fix on the box: {FIX}"


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m altdata.requirements_check")
    ap.add_argument("--requirements", default=str(REPO / "requirements.txt"))
    a = ap.parse_args(argv)
    r = check(Path(a.requirements).read_text(encoding="utf-8"))
    print(line(r))
    return 0 if not r["missing"] and not r["out_of_range"] else 1


if __name__ == "__main__":
    sys.exit(main())
