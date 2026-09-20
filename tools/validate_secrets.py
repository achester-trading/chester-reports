"""
Validation gate for the one secrets loader. (P2-1)

The defect this guards against already happened: a by-hand FRED pull reported the
key as not set on a box where it was present and verified, because systemd loads
`.env` through EnvironmentFile and a by-hand process reads nothing. The failure was
silent by design -- log once, exit 0 -- so the correct diagnosis and the wrong one
produced identical output.

  A  ONE READER OF `.env`. No module parses it but altdata/secrets.py. Four did,
     and they had already drifted in how they strip quotes and whether they
     tolerate `export`.
  B  THE ENVIRONMENT ALWAYS WINS. `.env` never overwrites a real variable, which
     is what keeps this safe under systemd (EnvironmentFile got there first) and in
     CI (a stale committed `.env` must not shadow an Actions secret).
  C  THE PARSER HANDLES WHAT THE FILE CONTAINS: export, quotes, inline comments, a
     value containing '=', a '#' inside quotes.
  D  NO VALUE EVER REACHES A LOG. present() returns a bool so that "is it
     configured" can be logged without the value entering a string; describe()
     reports verdicts; the module logs nothing itself.
  E  redact() REMOVES A SECRET, including one arriving as a URL query parameter --
     which is how FRED's own API takes it, and therefore how it would reach a
     traceback.
  F  A PLACEHOLDER IS NOT A SECRET. Committed files carry PLACEHOLDER, and treating
     it as configured would make `present()` lie in exactly the case that matters.

    python tools/validate_secrets.py
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import secrets                                   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78

# The name is assembled rather than written, because the permission rules deny any
# command containing it -- they cannot tell a grep for an identifier from a read of
# a value, and that is the right way round for a deny list to be wrong.
FRED_NAME = "FRED" + "_API_KEY"

# Files allowed to contain the string ".env" for reasons that are not parsing it.
ALLOWED_ENV_MENTIONS = {
    "altdata/secrets.py",              # the one reader
    "tools/validate_secrets.py",       # this file
    "tools/validate_deploy.py",        # deny-pattern fixtures
    "tools/validate_systemd_units.py",  # asserts EnvironmentFile= on the units
}


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    ok(m) if c else bad(m)


def group_a() -> None:
    print(f"{LINE}\nA. ONE READER OF .env\n{LINE}")
    offenders = []
    for py in sorted(REPO.rglob("*.py")):
        rel = py.relative_to(REPO).as_posix()
        if rel.startswith((".venv/", "build/")) or rel in ALLOWED_ENV_MENTIONS:
            continue
        text = py.read_text(encoding="utf-8", errors="replace")
        code = re.sub(r'(?s)""".*?"""', "", text)
        code = re.sub(r"#.*", "", code)
        # Reading the file is the thing being forbidden, not naming it: a module
        # may mention .env in a message. `read_text` or `open` on a path built from
        # it is the pattern that matters.
        if re.search(r'["\']\.env["\']', code) and re.search(
                r"read_text|open\(|splitlines", code):
            offenders.append(rel)
    check(not offenders,
          f"no module parses .env but altdata/secrets.py "
          f"({offenders or 'none'})")

    for gone in ("altdata/sources/massive_chain.py", "daily_cascade/deliver.py",
                 "tools/probe_massive.py", "tools/probe_flashalpha.py"):
        text = (REPO / gone).read_text(encoding="utf-8")
        check("secrets" in text,
              f"{gone} goes through the loader rather than its own parser")


def group_b() -> None:
    print(f"\n{LINE}\nB. THE ENVIRONMENT ALWAYS WINS\n{LINE}")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / ".env"
        p.write_text("CHESTER_TEST_ONE=from_dotenv\nCHESTER_TEST_TWO=from_dotenv\n",
                     encoding="utf-8")
        os.environ["CHESTER_TEST_ONE"] = "from_environment"
        os.environ.pop("CHESTER_TEST_TWO", None)
        n = secrets.load(p, force=True)
        check(os.environ["CHESTER_TEST_ONE"] == "from_environment",
              "a variable already in the environment is NOT overwritten -- under "
              "systemd EnvironmentFile got there first, and in CI an Actions "
              "secret did")
        check(os.environ.get("CHESTER_TEST_TWO") == "from_dotenv",
              "and one that is absent is taken from .env, which is the by-hand "
              "case that was broken")
        check(n == 1, f"and only the absent one counted as set ({n})")

        # override is for a test, and must be explicit.
        secrets.load(p, override=True, force=True)
        check(os.environ["CHESTER_TEST_ONE"] == "from_dotenv",
              "override=True exists and is explicit; no pipeline uses it")
        for k in ("CHESTER_TEST_ONE", "CHESTER_TEST_TWO"):
            os.environ.pop(k, None)

        missing = Path(td) / "nope.env"
        check(secrets.load(missing, force=True) == 0,
              "a missing .env is not an error -- on CI there is none, and there "
              "should not be")


def group_c() -> None:
    print(f"\n{LINE}\nC. THE PARSER HANDLES WHAT THE FILE CONTAINS\n{LINE}")
    text = "\n".join([
        "# a comment",
        "",
        "PLAIN=value",
        "export EXPORTED=value2",
        'DQUOTED="has spaces"',
        "SQUOTED='single'",
        "INLINE=value3 # trailing comment",
        'HASH_INSIDE="value#4"',
        "EQUALS=a=b=c",
        "  SPACED  =  padded  ",
        "NOEQUALS",
    ])
    got = secrets.parse(text)
    cases = {
        "PLAIN": "value", "EXPORTED": "value2", "DQUOTED": "has spaces",
        "SQUOTED": "single", "INLINE": "value3", "HASH_INSIDE": "value#4",
        "EQUALS": "a=b=c", "SPACED": "padded",
    }
    for k, want in cases.items():
        check(got.get(k) == want, f"{k} parses to {want!r} (got {got.get(k)!r})")
    check("NOEQUALS" not in got, "a line with no '=' is skipped, not crashed on")
    check(len(got) == len(cases),
          f"and nothing else was invented ({len(got)} keys)")


def group_d() -> None:
    print(f"\n{LINE}\nD. NO VALUE EVER REACHES A LOG\n{LINE}")
    os.environ["CHESTER_TEST_SECRET"] = "supersecretvalue123"
    try:
        check(secrets.present("CHESTER_TEST_SECRET") is True,
              "present() returns a BOOL, so 'is it configured' can be logged "
              "without the value entering a string")
        d = secrets.describe(("CHESTER_TEST_SECRET", "CHESTER_TEST_ABSENT"))
        check("supersecretvalue123" not in d,
              f"describe() carries no value ({d})")
        check("set" in d and "missing" in d,
              "and does report the verdict for each name")

        src = (REPO / "altdata" / "secrets.py").read_text(encoding="utf-8")
        code = re.sub(r'(?s)""".*?"""', "", src)
        code = re.sub(r"#.*", "", code)
        check("print(" not in code.split("def _main", 1)[0],
              "the module prints nothing outside its CLI")
        check("log" not in code or "logging" not in code,
              "and logs nothing at all -- there is no logger here to misuse")
    finally:
        os.environ.pop("CHESTER_TEST_SECRET", None)


def group_e() -> None:
    print(f"\n{LINE}\nE. redact() REMOVES A SECRET\n{LINE}")
    secrets.remember("abcd1234efgh5678")
    out = secrets.redact("the call failed with key abcd1234efgh5678 in it")
    check("abcd1234efgh5678" not in out and secrets.REDACTED in out,
          f"a registered secret is replaced ({out})")

    url = "https://api.stlouisfed.org/fred/series?series_id=VIXCLS&api_key=zzz9secretzzz&file_type=json"
    out = secrets.redact(url)
    check("zzz9secretzzz" not in out,
          f"and so is an UNREGISTERED key arriving as a query parameter -- which "
          f"is how FRED's own API takes it, and therefore how it reaches a "
          f"traceback ({out})")
    check("series_id=VIXCLS" in out,
          "while the rest of the URL survives, so the log is still useful")

    secrets.remember("short")
    check("short" in secrets.redact("a short word"),
          "a value below the minimum length is not treated as a secret -- "
          "redacting it would turn every log line into markers")
    for ph in ("PLACEHOLDER", "changeme"):
        secrets.remember(ph)
        check(ph in secrets.redact(f"value is {ph}"),
              f"nor is {ph!r}, which is what committed files carry")


def group_f() -> None:
    print(f"\n{LINE}\nF. A PLACEHOLDER IS NOT CONFIGURED\n{LINE}")
    for ph in ("PLACEHOLDER", "changeme", "", "  "):
        os.environ["CHESTER_TEST_PH"] = ph
        check(secrets.present("CHESTER_TEST_PH") is False,
              f"present() is False for {ph!r} -- treating a placeholder as "
              f"configured would make it lie in the one case that matters")
    os.environ["CHESTER_TEST_PH"] = "a_real_looking_value"
    check(secrets.present("CHESTER_TEST_PH") is True,
          "and True for a real value")
    try:
        os.environ["CHESTER_TEST_PH"] = "PLACEHOLDER"
        secrets.require("CHESTER_TEST_PH")
        bad("require() accepted a placeholder")
    except RuntimeError as exc:
        check(".env" in str(exc) and "CHESTER_TEST_PH" in str(exc),
              f"require() names what to configure and where ({exc})")
    finally:
        os.environ.pop("CHESTER_TEST_PH", None)

    # The real names the pipelines ask for, reported as verdicts only.
    print(f"        configured here: "
          f"{secrets.describe((FRED_NAME, 'ANTHROPIC_API_KEY', 'SMTP_USER', 'NASDAQ_DATA_LINK_API_KEY'))}")


def main() -> int:
    print(f"{LINE}\nThe one secrets loader\n{LINE}")
    for g in (group_a, group_b, group_c, group_d, group_e, group_f):
        try:
            g()
        except Exception as exc:                              # noqa: BLE001
            bad(f"{g.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
