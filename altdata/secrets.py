"""
The one place a secret is read, and the one place one is redacted. (P2-1)

-----------------------------------------------------------------------------
THE BUG THIS EXISTS TO FIX
-----------------------------------------------------------------------------

Phase 2b's FRED pull reported "FRED_API_KEY is not set" on a box where the key was
present and verified. Both facts were true. systemd units load `.env` through
`EnvironmentFile=`, so every scheduled run sees the key -- and a BY-HAND run of the
same module does not, because nothing in the process reads the file. The failure was
silent by design (log once, exit 0) and therefore indistinguishable from a missing
key, which is the worst possible shape for a configuration problem: the correct
diagnosis and the wrong one produce identical output.

So: an in-process loader, used by every entry point, that reads `.env` for variables
not already in the environment.

-----------------------------------------------------------------------------
THE ENVIRONMENT ALWAYS WINS
-----------------------------------------------------------------------------

A real environment variable is never overwritten by `.env`. That ordering is not a
detail -- it is what keeps this safe in the three places it runs:

  systemd     EnvironmentFile has already populated the environment; this finds
              nothing to do and changes nothing.
  CI          GitHub Actions secrets arrive as environment variables, and a stale
              `.env` committed by accident must never shadow them.
  by hand     the environment is empty and `.env` is the only source, which is the
              case that was broken.

`override=True` exists for one caller -- a test that needs a known value -- and is
not used by any pipeline.

-----------------------------------------------------------------------------
NEVER PRINTS A VALUE
-----------------------------------------------------------------------------

`get()` returns a value to a caller that asked for it. Nothing in this module logs
one, and `present()` exists precisely so that "is the key configured" can be
answered and logged WITHOUT the value entering a string. `describe()` reports
lengths and prefixes of names, never of values.

`redact()` is the third copy of a redactor in this repo made into the only one: it
replaces every registered secret with a marker, so a traceback or an error body that
happens to contain a key cannot reach a log. Register a secret with `remember()` as
soon as it is read.

    from altdata import secrets
    key = secrets.get("FRED_API_KEY")          # loads .env on first miss
    if not secrets.present("FRED_API_KEY"):    # never touches the value
        log.warning("fred: no key configured -- skipping")
    log.error(secrets.redact(str(exc)))        # safe to log
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
ENV_PATH = REPO / ".env"

# The marker a redacted secret leaves. Distinctive so a grep over the logs can
# prove the redactor fired rather than that nothing was there.
REDACTED = "[REDACTED]"

# A value this short is a placeholder, not a secret, and redacting it would turn
# every log line into markers. "PLACEHOLDER" is what the committed files carry.
MIN_SECRET_LEN = 8
PLACEHOLDERS = {"placeholder", "changeme", "todo", "none", "null", ""}

_loaded = False
_secrets: list[str] = []


def parse(text: str) -> dict[str, str]:
    """`.env` text as a dict. KEY=VALUE, `export` tolerated, quotes stripped.

    Deliberately not a dependency. python-dotenv is a fine library and this is
    eleven lines that four modules had each written slightly differently -- one of
    them stripping only double quotes, one not handling `export`, one not skipping
    comments after a value.
    """
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        # Quoted values keep everything inside the quotes, including a #. An
        # unquoted value stops at an inline comment.
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
            v = v[1:-1]
        else:
            v = v.split(" #", 1)[0].strip()
        if k:
            out[k] = v
    return out


def load(path: Optional[Path] = None, override: bool = False,
         force: bool = False) -> int:
    """Populate os.environ from `.env`. Returns how many names it set.

    Idempotent: the file is read once per process unless `force`. A missing file is
    not an error -- on CI there is no `.env` and there should not be.
    """
    global _loaded
    if _loaded and not force and path is None:
        return 0
    p = path or ENV_PATH
    _loaded = True
    if not p.is_file():
        return 0
    try:
        values = parse(p.read_text(encoding="utf-8"))
    except OSError:
        # A .env that cannot be read is a configuration problem, and raising here
        # would take down every entry point that imports this. The consequence
        # surfaces as the variable being absent, which is what present() reports.
        return 0
    n = 0
    for k, v in values.items():
        if override or k not in os.environ:
            os.environ[k] = v
            n += 1
        remember(v)
    return n


def get(name: str, default: Optional[str] = None) -> Optional[str]:
    """The value, loading `.env` on the first miss. Registers it for redaction."""
    v = os.environ.get(name)
    if v is None:
        load()
        v = os.environ.get(name)
    if v is None:
        return default
    remember(v)
    return v


def present(name: str) -> bool:
    """Whether the name is configured, WITHOUT the value entering a string.

    This is what a log line asks. `if secrets.get(name):` also works and is one
    slip away from `log.info(f"key={secrets.get(name)}")`; this cannot be misused
    that way because it returns a bool.
    """
    v = get(name)
    return bool(v) and v.strip().lower() not in PLACEHOLDERS


def require(name: str) -> str:
    """The value, or a clear error naming what to configure and where."""
    v = get(name)
    if not v or v.strip().lower() in PLACEHOLDERS:
        raise RuntimeError(
            f"{name} is not configured. Set it in {ENV_PATH.name} at the repo root "
            f"(gitignored) or in the environment. Committed files carry "
            f"placeholders only.")
    return v


def remember(value: Optional[str]) -> None:
    """Register a value so redact() will remove it from any text."""
    if not value or len(value) < MIN_SECRET_LEN:
        return
    if value.strip().lower() in PLACEHOLDERS:
        return
    if value not in _secrets:
        _secrets.append(value)


def redact(text: str) -> str:
    """Every registered secret replaced by a marker.

    Longest first, so a key that contains another registered value as a substring
    cannot leave a fragment behind.
    """
    if not text:
        return text
    out = str(text)
    for s in sorted(_secrets, key=len, reverse=True):
        out = out.replace(s, REDACTED)
    # A URL query parameter is the other way a key reaches a log -- FRED's own API
    # takes it as ?api_key=. Stripped by shape as well as by registration, because
    # the registration only covers keys this process has read.
    out = re.sub(r"(?i)([?&](?:api_?key|token|key|secret)=)[^&\s\"']+",
                 rf"\1{REDACTED}", out)
    return out


def describe(names: tuple[str, ...]) -> str:
    """Which of these names are configured. NAMES AND VERDICTS, NEVER VALUES."""
    load()
    bits = [f"{n}={'set' if present(n) else 'missing'}" for n in names]
    return " ".join(bits)


def _main(argv: list[str]) -> int:
    """`python -m altdata.secrets NAME...` -- reports set/missing, never values."""
    names = tuple(argv) or (
        "FRED_API_KEY", "ANTHROPIC_API_KEY", "CHESTER_STATE_TOKEN",
        "SMTP_USER", "SMTP_PASSWORD", "NASDAQ_DATA_LINK_API_KEY",
        "MASSIVE_API_KEY", "FLASHALPHA_API_KEY")
    n = load()
    print(f"{ENV_PATH.name}: {'present' if ENV_PATH.is_file() else 'absent'}; "
          f"{n} name(s) taken from it (the environment always wins)")
    for name in names:
        print(f"  {name:32} {'set' if present(name) else 'missing'}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
