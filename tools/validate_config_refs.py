#!/usr/bin/env python3
"""
Validation gate: every metric id referenced from a config file resolves. (6c-3)

    python tools/validate_config_refs.py

`config/story_queries.yaml` tagged every yen-carry headline with `fred.usdjpy`
for a week. The registered key is `fred.usd_jpy`, so the tag named nothing, no
join could ever match it, and every gate passed -- because no gate asked. The
same sweep found thirteen more in `config/pillars.yaml`: FRED series ids written
as keys (`fred.payems` for `fred.nfp`), a transform filed under the wrong
namespace (`fred.r_vs_g` for `calc.r_minus_g`), and five series the store has
never held. A config file is where a key is typed by hand, and a key that
resolves to nothing fails silently everywhere downstream.

WHAT COUNTS AS A METRIC ID. Any string -- a value OR a mapping key, anywhere in
the file -- shaped `<namespace>.<name>` where the namespace is one the registry
already uses (fred, calc, yfinance, mof, ...). The namespaces come from the
registry itself, so a new source family is covered the day it registers. A
filename (`regime.py`) and a bulk-import key prefix (`calc.surprise_vs_naive.`)
are not ids and are excluded by shape. Series the system does not hold are
named by their SOURCE id in a `not_yet_sourced` block, never as a key.

  A  every tracked YAML config file: each metric-shaped string is registered
  B  the check is shown to fire: the typo it exists for, planted, fails it
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml  # noqa: E402

from altdata import derived  # noqa: E402

PASS = 0
FAIL = 0
LINE = "=" * 78

# Workflow files are YAML and not config; the registries ARE config.
EXCLUDE = re.compile(r"^\.github/|^data/")
NOT_AN_ID = re.compile(r"\.(py|ya?ml|md|sh|json|csv|html|txt|sqlite|db)$")


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


def config_files() -> list[str]:
    out = subprocess.run(["git", "-C", str(REPO), "ls-files", "*.yaml", "*.yml"],
                         capture_output=True, text=True, check=True).stdout
    return sorted(f for f in out.split() if not EXCLUDE.search(f))


def id_pattern(reg: dict) -> re.Pattern:
    spaces = sorted({k.split(".", 1)[0] for k in reg if "." in k})
    return re.compile(r"^(?:%s)\.[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*$"
                      % "|".join(map(re.escape, spaces)))


def strings(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from strings(k)
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)
    elif isinstance(o, str):
        yield o.strip()


def unresolved(doc, reg: dict, pat: re.Pattern) -> tuple[int, list[str]]:
    refs = [s for s in strings(doc) if pat.match(s) and not NOT_AN_ID.search(s)]
    return len(refs), sorted({s for s in refs if s not in reg})


def main() -> int:
    print(f"{LINE}\nEvery metric id in config resolves to a registered key\n{LINE}")
    reg = derived._load_registry()
    check(len(reg) > 100, f"the registry loads ({len(reg)} keys)")
    pat = id_pattern(reg)
    total = 0
    for f in config_files():
        doc = yaml.safe_load((REPO / f).read_text(encoding="utf-8"))
        n, missing = unresolved(doc, reg, pat)
        total += n
        check(not missing, f"{f}: {n} metric id(s), all registered"
              + (f" -- UNRESOLVED: {missing}" if missing else ""))
    check(total > 400, f"and the sweep found ids to check ({total}) -- a pattern "
                       f"that matched nothing would pass everything")

    print(f"\n{LINE}\nB. THE CHECK FIRES\n{LINE}")
    planted = {"yen_carry": {"entities": ["fred.usdjpy", "yfinance.mkt_vix"]}}
    n, missing = unresolved(planted, reg, pat)
    check(missing == ["fred.usdjpy"],
          f"the typo this gate exists for fails it ({missing})")
    _, keyed = unresolved({"release_surprises": {"fred.cpii": "+"}}, reg, pat)
    check(keyed == ["fred.cpii"], "and a misspelled id used as a mapping KEY does")
    _, fine = unresolved({"a": "regime.py", "b": "calc.surprise_vs_naive.",
                          "c": "Base Rates, Chapter 3.1", "d": "NVDA"}, reg, pat)
    check(not fine, "while a filename, a key prefix, prose and a ticker do not")

    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
