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
- AN ACCOUNT, NOT PROSE (B111, ruling (f) of 2 Nov 2026). A word that is a login
  is removed from the line before the denylist is matched:
    a home-path segment:  /home/<login>/..., /Users/<login>/..., C:\\Users\\<login>\\...
    an account address:   <login>@host (ssh <login>@host among them)
    an account command:   chown, chgrp, su, sudo -u, adduser, useradd, usermod,
                          userdel, passwd and loginctl enable-/disable-linger, each
                          with its arguments up to the next shell separator; and
                          the box sheet's "user `<login>`"
  The same word in prose is still a hit.

THE PASTE HEADER (B114; ruled 2 Nov 2026). Every paste opens on the standing header
"From <name> - run this", and it stays as written. On line 1 of a file under
docs/pastes/ ending .md, that exact header's name token is removed before the
denylist is matched; the rest of line 1, every other line of a paste, and the same
header anywhere else are still scanned.

THE PATH ALLOWLIST (B111, ruling (f)). Files that are never edited (the dated
ledgers in docs/ledgers/) are skipped by path, read from the same place as the
list: an entry "allow:<path>" in CHESTER_NAMES_DENYLIST or the names file, or
CHESTER_NAMES_ALLOW_PATHS (comma-separated). The scan prints "allowlisted: n
files" and each path, so the allowlist cannot grow silently; an allowed path that
is not tracked is said so.

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
ENV_ALLOW = "CHESTER_NAMES_ALLOW_PATHS"
ALLOW_PREFIX = "allow:"
DEFAULT_FILE = ".chester-names"

# Matched first and removed from the line: measures named after people.
ALLOWLIST = ("Sahm", "Brier", "CAPE", "Taylor", "Wu-Xia", "ACM")
# The repository and the organisation: never a hit, in a path, a URL or alone.
NEVER = ("chester",)
_URL = re.compile(r"https?://\S+")
_REPO_TOKEN = re.compile(r"[\w.-]*chester[\w.-]*", re.I)
# An account, not prose (B111): removed before the denylist is matched.
_ACCOUNT = (
    re.compile(r"(?:/home/|/Users/|\\Users\\)[\w.-]+", re.I),          # a home-path segment
    re.compile(r"[\w.-]+@[\w-]+(?:\.[\w-]+)*"),                          # login@host
    re.compile(r"\b(?:chown|chgrp|su|adduser|useradd|usermod|userdel|passwd"
               r"|sudo\s+-u|loginctl\s+(?:enable|disable)-linger)\b[^&;|\n`]*"),  # a command
    re.compile(r"\buser\s+`[\w.-]+`"),                                   # the sheet's user `<login>`
)
# The standing paste header (B114): its name token, on line 1 of docs/pastes/*.md only.
_PASTE_HEADER = re.compile(r"^(\s*From )[\w.'-]+( - run this\b)")
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


def _entries(env) -> list[str]:
    """Every entry of the list's one place: the variable, else the named file."""
    raw = (env.get(ENV_LIST) or "").strip()
    if not raw and (env.get(ENV_FILE) or "").strip():
        p = Path(env[ENV_FILE]).expanduser()
        raw = p.read_text(encoding="utf-8") if p.is_file() else ""
    return [n.strip() for n in re.split(r"[,\n]", raw) if n.strip()]


def allow_paths(environ=None) -> list[str]:
    """The path allowlist: "allow:<path>" entries of the list, plus ENV_ALLOW."""
    env = os.environ if environ is None else environ
    out = [e[len(ALLOW_PREFIX):].strip() for e in _entries(env)
           if e.lower().startswith(ALLOW_PREFIX)]
    out += [p.strip() for p in (env.get(ENV_ALLOW) or "").split(",") if p.strip()]
    norm = (p.replace("\\", "/") for p in out)
    return sorted({p[2:] if p.startswith("./") else p for p in norm if p})


def denylist(environ=None) -> list[str]:
    """The names to refuse, from the environment or the named file; [] if neither."""
    env = os.environ if environ is None else environ
    names = [e for e in _entries(env) if not e.lower().startswith(ALLOW_PREFIX)]
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
    for rx in _ACCOUNT:
        line = rx.sub(" ", line)
    line = _REPO_TOKEN.sub(" ", line)
    for a in ALLOWLIST:
        line = re.sub(rf"(?<![\w-]){re.escape(a)}(?![\w-])", " ", line, flags=re.I)
    return line


def _pattern(names: list[str]) -> re.Pattern:
    alt = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return re.compile(rf"(?<![\w])(?:{alt})(?![\w])", re.I)


def is_paste(rel: str) -> bool:
    """A paste file: docs/pastes/<name>.md (B114's header rule applies to its line 1)."""
    rel = rel.replace("\\", "/")
    return rel.startswith("docs/pastes/") and rel.endswith(".md") and rel.count("/") == 2


def hits_in(text: str, pat: re.Pattern, rel: str = "") -> list[tuple[int, str]]:
    out = []
    paste = is_paste(rel)
    for i, line in enumerate(text.splitlines(), 1):
        scan = _PASTE_HEADER.sub(r"\1\2", line) if (paste and i == 1) else line
        if pat.search(_clean(scan)):
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

    print("B. AN ACCOUNT, NOT PROSE; THE PATH ALLOWLIST (B111, ruling (f))")
    zed = _pattern(["Zed"])
    acct = ["ExecStart=/home/zed/chester-reports/run.sh",
            r"C:\Users\Zed\projects\x and /Users/zed/x",
            "ssh zed@vps 'ls' and mail zed@example.org",
            "sudo adduser zed && sudo usermod -aG sudo zed",
            "sudo loginctl enable-linger zed; chown zed:zed f; su - zed; sudo -u zed id",
            "typed at the box prompt (`ssh vps`, user `zed`)"]
    check(not any(hits_in(a, zed) for a in acct),
          "a login in a home path, an address or an account command is not a hit")
    check(len(hits_in("Zed restarts the unit; the Gateway needs Zed's login", zed)) == 1
          and hits_in("cd /home/zed && Zed signs off", zed),
          "the same word in prose is still a hit, beside an excluded path too")
    env = {ENV_LIST: "Zed, allow:docs/ledgers/a.md", ENV_ALLOW: "docs/ledgers/b.md,./c.md"}
    check(denylist(env) == ["Zed"] and allow_paths(env) == ["c.md", "docs/ledgers/a.md", "docs/ledgers/b.md"],
          "allow:<path> entries and CHESTER_NAMES_ALLOW_PATHS are paths, never names")
    check(allow_paths({}) == [], "no allowlist set: nothing is skipped")

    print("C. THE PASTE HEADER (B114; ruled 2 Nov 2026)")
    head = "From Zed - run this (session B): B1, a paste.\nThe body."
    check(not hits_in(head, zed, "docs/pastes/B1.md"),
          "line 1's standing header 'From <name> - run this' in docs/pastes/*.md is not a hit")
    check(hits_in("From Zed - run this (session B): Zed asks for B1.", zed, "docs/pastes/B1.md")
          == [(1, "From *** - run this (session B): *** asks for B1.")],
          "the rest of line 1 is still scanned")
    check(hits_in("The title.\nFrom Zed - run this (session B): B1", zed, "docs/pastes/B1.md")
          == [(2, "From *** - run this (session B): B1")],
          "the header on any line but the first is a hit")
    check(len(hits_in(head, zed, "docs/briefs/b1-notes.md")) == 1
          and len(hits_in(head, zed, "docs/pastes/old/B1.md")) == 1
          and len(hits_in(head, zed, "docs/pastes/B1.txt")) == 1,
          "the same header outside docs/pastes/*.md is a hit")
    check(len(hits_in("From Zed, run this: B1", zed, "docs/pastes/B1.md")) == 1,
          "only the exact pattern is excluded")


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
    allowed = allow_paths()
    files = tracked_files()
    rels = {str(p.relative_to(REPO)).replace("\\", "/") for p in files}
    print(f"  allowlisted: {len(allowed)} files")
    for a in allowed:
        print(f"    {a}" + ("" if a in rels else "  (not a tracked file)"))
    by_file: dict[str, list] = {}
    for p in files:
        if str(p.relative_to(REPO)).replace("\\", "/") in allowed:
            continue
        t = read_text(p)
        if t is None:
            continue
        h = hits_in(t, pat, str(p.relative_to(REPO)))
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
