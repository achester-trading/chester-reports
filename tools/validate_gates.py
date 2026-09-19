"""
Validation gate for the gate harness itself.

A validator that FAILS TO EXECUTE is a failed validator. Not a skipped one, not
a warning, not a gate that quietly reports nothing: a non-zero exit for any
reason at all -- a syntax error, a bad import, a missing dependency, a crash
before the first check -- must come out the other end as a failure.

This is true today by construction, in both places: `make validate` branches on
the exit status of each validator, and the CI matrix runs each one as its own job
so its exit status is the job's result. Nothing pinned it, which is the gap this
file closes. The property is one refactor away from being lost -- a harness
rewritten to grep its children's output for "PASSED" would still look correct on
a green suite and would pass a validator that never ran -- and the repo has
already paid for this once: tools/validate_backup.py carried a syntax error for
two commits while its siblings kept passing, because a single sequential job
died on the import and took the rest of the suite with it.

What it proves:

  A  THE LIST IS COMPLETE. Every validator in tools/ is in the Makefile's list.
     A gate that exists but was never wired in is a gate nobody runs, which is
     indistinguishable from not having written it.
  B  A BROKEN VALIDATOR EXITS NON-ZERO. Seeded three ways -- a syntax error, a
     failed import, a crash before the first assertion -- because "fails to
     execute" has more than one shape and the harness must not care which.
  C  THE HARNESS BRANCHES ON EXIT STATUS. The Makefile recipe is read and
     checked to test the child's status rather than its output, and to
     accumulate a failure into its own exit code.
  D  MAKE AND CI CANNOT DISAGREE. The workflow generates its matrix from
     `make list`; that pipeline is applied here to the same output and must
     reproduce the Makefile's list exactly.

    python tools/validate_gates.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MAKEFILE = REPO / "Makefile"
WORKFLOW = REPO / ".github" / "workflows" / "registry-check.yml"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78


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


def makefile_vars() -> dict[str, list[str]]:
    """The three gate lists, parsed out of the Makefile's own text.

    Parsed rather than shelled out to `make`, because make is absent on a stock
    Windows box and this property has to be checkable wherever the validators
    themselves are checkable.
    """
    text = MAKEFILE.read_text(encoding="utf-8")
    out: dict[str, list[str]] = {}
    for name in ("PY_VALIDATORS", "SH_VALIDATORS", "EXTRA", "DATA_GATES"):
        m = re.search(rf"^{name}\s*:?=\s*((?:.*?\\\n)*.*)$", text, re.M)
        if not m:
            out[name] = []
            continue
        body = m.group(1).replace("\\\n", " ")
        out[name] = [t for t in body.split() if t and not t.startswith("#")]
    return out


def declared_kind(rel: str) -> str:
    """GATE_KIND as the gate's own source declares it, or "code" if it does not.

    Read as TEXT rather than imported. Importing a gate would run its module-level
    code -- which for several of these means reading a store or a chain -- and a
    check about lists has no business doing that.
    """
    p = REPO / rel
    if not p.is_file():
        return "missing"
    m = re.search(r"^GATE_KIND\s*=\s*[\"'](\w+)[\"']",
                  p.read_text(encoding="utf-8", errors="replace"), re.M)
    return m.group(1) if m else "code"


def validate_recipe() -> str:
    """The body of the `validate:` target."""
    text = MAKEFILE.read_text(encoding="utf-8")
    m = re.search(r"^validate:\n((?:\t.*\n|\n)*)", text, re.M)
    return m.group(1) if m else ""


# ---------------------------------------------------------------------------
def group_a() -> None:
    print(f"\n{LINE}\nA. THE LIST IS COMPLETE\n{LINE}")
    v = makefile_vars()
    listed = (set(v["PY_VALIDATORS"]) | set(v["SH_VALIDATORS"])
              | set(v["EXTRA"]) | set(v["DATA_GATES"]))
    check(bool(listed), f"the Makefile names {len(listed)} gates")

    on_disk = {
        f"tools/{p.name}" for p in (REPO / "tools").iterdir()
        if p.is_file() and re.match(r"^(validate_|check_).*\.(py|sh)$", p.name)
    }
    missing = sorted(on_disk - listed)
    check(not missing,
          f"every validator in tools/ is in the Makefile's list "
          f"({missing or 'none missing'})")

    ghosts = sorted(p for p in listed if not (REPO / p).exists())
    check(not ghosts, f"every listed gate exists on disk ({ghosts or 'none missing'})")

    # This file must be in the list, or it is a gate that proves the list is
    # complete and is itself not in it.
    check("tools/validate_gates.py" in listed,
          "this validator is itself in the list")

    # ---- THE CODE/DATA SPLIT, WHICH IS THE PART THAT COULD BE ABUSED --------
    #
    # Data gates report instead of failing the suite, which is right for a check
    # whose verdict is about the box's chains rather than the commit. It is also
    # exactly the mechanism somebody would reach for to silence an inconvenient
    # CODE validator -- move it to DATA_GATES and the suite goes green while the
    # check keeps failing in a paragraph nobody reads.
    #
    # So membership is not the Makefile's word alone. Each data gate must DECLARE
    # itself with GATE_KIND = "data" in its own source, and these two statements
    # must agree in both directions.
    code = set(v["PY_VALIDATORS"]) | set(v["EXTRA"]) | set(v["SH_VALIDATORS"])
    data = set(v["DATA_GATES"])

    check(not (code & data),
          f"no gate is in both lists ({sorted(code & data) or 'none'})")

    undeclared = sorted(g for g in data if declared_kind(g) != "data")
    check(not undeclared,
          f"every DATA_GATE declares GATE_KIND = \"data\" in its own source "
          f"({undeclared or 'all declare it'})")

    mislabelled = sorted(g for g in code if declared_kind(g) == "data")
    check(not mislabelled,
          f"no gate declaring itself a data gate is being run as a code gate "
          f"({mislabelled or 'none'})")

    check(bool(data), "there is at least one data gate, so the split is real "
                      "rather than a dormant abstraction")


def group_b() -> None:
    print(f"\n{LINE}\nB. A BROKEN VALIDATOR EXITS NON-ZERO\n{LINE}")

    # Three shapes of "fails to execute". The harness must not distinguish
    # them, so all three are seeded rather than trusting one to stand for all.
    seeds = {
        "a syntax error (parse fails, nothing runs)":
            "def broken(:\n    pass\n",
        "a failed import (parses, dies at module load)":
            "import a_module_that_does_not_exist_anywhere\n",
        "a crash before the first check (parses, imports, then raises)":
            "raise RuntimeError('died before asserting anything')\n",
        "an explicit non-zero exit with no output at all":
            "import sys\nsys.exit(3)\n",
    }
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        for label, body in seeds.items():
            p = Path(td) / "validate_seeded.py"
            p.write_text(body, encoding="utf-8")
            r = subprocess.run([sys.executable, str(p)],
                              capture_output=True, text=True, cwd=str(REPO))
            check(r.returncode != 0,
                  f"{label} -> exit {r.returncode}")

        # THE CONVERSE, which is what makes the above mean anything: a
        # validator that really does pass must exit zero, or "non-zero" is
        # just describing every validator.
        p = Path(td) / "validate_fine.py"
        p.write_text("print('VALIDATION PASSED')\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(p)],
                          capture_output=True, text=True, cwd=str(REPO))
        check(r.returncode == 0, "a working validator exits 0")

        # And the trap the harness must not fall into: a validator that PRINTS
        # the word PASSED and then dies. Anything keying on output rather than
        # status reads this as a pass.
        p = Path(td) / "validate_liar.py"
        p.write_text("print('ALL GATES PASSED')\n"
                     "raise SystemExit(1)\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(p)],
                          capture_output=True, text=True, cwd=str(REPO))
        check(r.returncode != 0 and "PASSED" in r.stdout,
              "a validator that prints PASSED and then fails still exits "
              "non-zero -- status is the truth, output is not")


def group_c() -> None:
    print(f"\n{LINE}\nC. THE HARNESS BRANCHES ON EXIT STATUS\n{LINE}")
    recipe = validate_recipe()
    check(bool(recipe), "the validate: target was found in the Makefile")

    # `if $(PYTHON) $$v >...; then PASS; else FAIL; fail=1; fi` -- the shell
    # `if` tests the command's status. What must NOT appear is a decision made
    # by reading the child's output.
    check(re.search(r"if\s+\$\(PYTHON\)\s+\$\$v", recipe) is not None,
          "python gates are branched on by running them in an `if`, so the "
          "exit status is what decides")
    check(re.search(r"if\s+bash\s+\$\$v", recipe) is not None,
          "shell gates likewise")
    check("fail=1" in recipe and re.search(r"exit\s+\$\$fail", recipe),
          "a failure is accumulated into fail and becomes the target's own "
          "exit code -- the suite cannot report GATES FAILED and exit 0")
    check(not re.search(r"grep\s+-q?\s*['\"]?(PASS|PASSED)", recipe),
          "nothing in the recipe decides a gate's result by grepping its "
          "output for PASSED")

    # The data pass must exist, must run every data gate, and must NOT feed the
    # suite's exit code. `dfail` is its own counter for exactly that reason.
    check("DATA_GATES" in recipe,
          "the validate recipe runs the data gates too -- separated, not dropped")
    check("dfail" in recipe,
          "with their own counter, so a data finding cannot set the exit code")
    check(re.search(r"exit\s+\$\$fail", recipe) is not None
          and "exit $$dfail" not in recipe,
          "and the target exits on the CODE counter alone")
    check("VERDICT" in recipe,
          "a data finding prints as a VERDICT rather than as a FAIL, so the two "
          "kinds are distinguishable at a glance")

    fast = MAKEFILE.read_text(encoding="utf-8")
    m = re.search(r"^validate-fast:\n((?:\t.*\n|\n)*)", fast, re.M)
    check(m is not None and "set -e" in m.group(1),
          "validate-fast runs under `set -e`, so it stops on the first "
          "non-zero exit rather than running on and reporting success")


def group_d() -> None:
    print(f"\n{LINE}\nD. MAKE AND CI CANNOT DISAGREE\n{LINE}")
    if not WORKFLOW.exists():
        bad(f"{WORKFLOW.relative_to(REPO)} is missing")
        return
    wf = WORKFLOW.read_text(encoding="utf-8")

    check("make list-code" in wf and "make list-data" in wf,
          "the workflow generates BOTH matrices from make rather than keeping a "
          "second copy of either list")

    # THE INVARIANT MOST LIKELY TO BE HELPFULLY BROKEN. gates-passed is the
    # required check; if somebody adds data-gate to its `needs`, every build goes
    # red for the absence of chains a CI runner was never going to have, and the
    # first fix anybody reaches for after that is widening the solver's tolerance.
    m = re.search(r"gates-passed:\s*needs:\s*(\[[^\]]*\]|\S+)", wf, re.S)
    needs = (m.group(1) if m else "")
    check("data-gate" not in needs,
          f"the required check does NOT depend on the data gates ({needs!r}) -- "
          f"a CI runner has no captured chains, so their verdict says nothing "
          f"about the commit")
    check("continue-on-error: true" in wf,
          "and the data-gate job is continue-on-error, so it reports without "
          "deciding the build")
    check("fail-fast: false" in wf,
          "fail-fast is off, so one broken gate does not hide the others")

    # Reproduce the workflow's own pipeline against the Makefile's lists: it
    # takes the indented lines of `make list` and keeps those ending .py/.sh.
    v = makefile_vars()
    from_make = v["PY_VALIDATORS"] + v["EXTRA"] + v["SH_VALIDATORS"]
    kept = [g for g in from_make if g.endswith((".py", ".sh"))]
    check(sorted(kept) == sorted(from_make),
          f"every listed gate survives the workflow's `.py|.sh` filter -- a "
          f"gate with another suffix would be silently dropped from CI "
          f"({sorted(set(from_make) - set(kept)) or 'none dropped'})")

    # Each matrix leg runs the gate directly, so its exit status IS the job's.
    check(re.search(r"\*\.sh\)\s*bash", wf) is not None
          and re.search(r"\*\)\s*python", wf) is not None,
          "each leg invokes the gate directly, so a non-zero exit fails the "
          "job -- there is no wrapper to swallow it")
    check(re.search(r'needs\.gate\.result.*!=.*success', wf) is not None,
          "the single required check fails unless EVERY matrix leg succeeded, "
          "so a skipped or cancelled leg cannot pass for a green one")


def main() -> int:
    print(f"{LINE}\nGate-harness validation -- a validator that cannot run is a "
          f"failed validator\n{LINE}")
    group_a()
    group_b()
    group_c()
    group_d()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    if FAIL:
        print("VALIDATION FAILED")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
