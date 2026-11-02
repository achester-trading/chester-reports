"""validate_names -- no listed person's name in a committed file (D38).

THE RULE. No person's name appears in a committed file. Write outlets, institutions
and roles instead, and "the operator" for the operator. Until B109 (2 Nov 2026) the
rule was applied by hand in every paste, and it slipped twice in one week. This gate
makes it hold.

THE LIST IS NEVER COMMITTED. The names to refuse are read from:
  CHESTER_NAMES_DENYLIST   comma-separated, from the environment; else
  CHESTER_NAMES_FILE       a file of names, one per line or comma-separated
                           (the default file name, .chester-names, is gitignored).
With neither set, the gate runs its self-test, prints "names gate: no denylist;
skipped" and exits 0. CI and a fresh laptop never fail for want of the list.

WHAT IT SCANS. Every tracked file (`git ls-files`), docs/pastes/ included, skipping
binaries. It reads the working tree, never git history. A hit is a whole word,
matched case-insensitively. It is printed as file:line with the name masked "***".

WHAT IT NEVER COUNTS.
- The repository's and the organisation's names in paths and URLs. The system is
  named after a surname, so "chester" alone is never a hit, and a denylist entry
  of it is ignored with a message.
- The measure names in ALLOWLIST (Sahm, Brier, CAPE, Taylor, Wu-Xia, ACM). They are
  removed from a line before the denylist is matched.
- Git history: the gate never reads it.

  python tools/validate_names.py            the self-test, then the scan if a list is set
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

GATE_KIND = "code"

REPO = Path(__file__).resolve().parent.parent
ENV_LIST = "CHESTER_NAMES_DENYLIST"
ENV_FILE = "CHESTER_NAMES_FILE"
DEFAULT_FILE = ".chester-names"

# Matched first and removed from the line: measures named after people.
ALLOWLIST = ("Sahm", "Brier", "CAPE", "Taylor", "Wu-Xia", "ACM")
# The repository and the organisation: never a hit, in a path, a URL or alone.
NEVER = ("chester",)
_URL = re.compile(r"https?://\S+")
_REPO_TOKEN = re.compile(r"[\w.-]*chester[\w.-]*", re.I)
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".xlsx", ".xls", ".zip",
              ".gz", ".db", ".sqlite", ".parquet", ".ico", ".woff", ".woff2", ".ttf"}

PASS = FAIL = 0


def check(cond: bool, msg: str) -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {msg}")
    else:
        FAIL += 1
        print(f"  FAIL  {msg}")


def denylist(environ=None) -> list[str]:
    """The names to refuse, from the environment or the named file; [] if neither."""
    env = os.environ if environ is None else environ
    raw = (env.get(ENV_LIST) or "").strip()
    if not raw and (env.get(ENV_FILE) or "").strip():
        p = Path(env[ENV_FILE]).expanduser()
        raw = p.read_text(encoding="utf-8") if p.is_file() else ""
    names = [n.strip() for n in re.split(r"[,\n]", raw) if n.strip()]
    out = []
    for n in names:
        if n.lower() in NEVER:
            print(f"  note: {n.lower()!r} is the repository's name and is never a hit; ignored")
            continue
        out.append(n)
    return out


def _clean(line: str) -> str:
    """The line with URLs, repository tokens and allowlisted measures removed."""
    line = _URL.sub(" ", line)
    line = _REPO_TOKEN.sub(" ", line)
    for a in ALLOWLIST:
        line = re.sub(rf"(?<![\w-]){re.escape(a)}(?![\w-])", " ", line, flags=re.I)
    return line


def _pattern(names: list[str]) -> re.Pattern:
    alt = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return re.compile(rf"(?<![\w])(?:{alt})(?![\w])", re.I)


def hits_in(text: str, pat: re.Pattern) -> list[tuple[int, str]]:
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        if pat.search(_clean(line)):
            masked = pat.sub("***", line)
            out.append((i, masked.strip()[:160]))
    return out


def tracked_files() -> list[Path]:
    r = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True, check=True)
    return [REPO / p for p in r.stdout.decode("utf-8").split("\0") if p]


def read_text(p: Path):
    if p.suffix.lower() in BINARY_EXT or not p.is_file():
        return None
    b = p.read_bytes()
    if b"\0" in b[:8192]:
        return None
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("latin-1")


def selftest() -> None:
    print("A. THE RULES, ON FIXTURE LINES (no real name)")
    pat = _pattern(["Zed", "Quill"])
    check(hits_in("Zed accepts the draft.", pat) == [(1, "*** accepts the draft.")],
          "a listed name is a hit, whole word, masked as ***")
    check(hits_in("zed and QUILL", pat) and hits_in("zed and QUILL", pat)[0][1] == "*** and ***",
          "case-insensitive")
    check(not hits_in("Zedonia and Quillfeather", pat), "whole words only")
    check(not hits_in("https://example.org/Zed/page", pat), "a name inside a URL is not a hit")
    check(not hits_in("see chester-reports and achester-trading", _pattern(["chester"])),
          "the repository's and the organisation's names are never hits")
    check(denylist({ENV_LIST: "chester, Zed"}) == ["Zed"],
          "a denylist entry 'chester' is ignored")
    check(not hits_in("the Sahm rule, the Brier score and a Taylor rule", _pattern(["Taylor", "Sahm"])),
          "allowlisted measures are matched before the denylist")
    check(denylist({}) == [], "no list set: an empty denylist")
    check(denylist({ENV_LIST: "Zed,Quill"}) == ["Zed", "Quill"], "the variable is comma-separated")
    gi = (REPO / ".gitignore").read_text(encoding="utf-8")
    check(any(ln.strip() == DEFAULT_FILE for ln in gi.splitlines()),
          f".gitignore lists {DEFAULT_FILE}, so the list cannot be committed by accident")
    check(not (REPO / DEFAULT_FILE).exists() or DEFAULT_FILE not in
          [p.name for p in tracked_files()], "no names file is tracked")


def main() -> int:
    print("=" * 78 + "\nvalidate_names -- no listed person's name in a committed file (D38)\n" + "=" * 78)
    selftest()
    names = denylist()
    if not names:
        print(f"\n{PASS} passed, {FAIL} failed")
        print("names gate: no denylist; skipped")
        return 1 if FAIL else 0
    print(f"\nB. THE SCAN ({len(names)} name(s) from the list; never printed)")
    pat = _pattern(names)
    by_file: dict[str, list] = {}
    for p in tracked_files():
        t = read_text(p)
        if t is None:
            continue
        h = hits_in(t, pat)
        if h:
            by_file[str(p.relative_to(REPO)).replace("\\", "/")] = h
    total = sum(len(v) for v in by_file.values())
    for f, hs in sorted(by_file.items()):
        for ln, masked in hs:
            print(f"    {f}:{ln}: {masked}")
    check(total == 0, f"no listed name in a tracked file ({total} hit(s) in {len(by_file)} file(s))")
    print(f"\n{PASS} passed, {FAIL} failed")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
