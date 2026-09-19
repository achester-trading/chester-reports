#!/usr/bin/env bash
#
# The make targets, for machines without make.
#
# WHY THIS EXISTS. `make` is absent on this repo's authoring laptop -- no make, no
# mingw32-make, no gmake -- so `make validate` and `make html` are unrunnable on
# the machine where most editing happens. That had a quiet second cost once the
# permission allowlist existed: .claude/settings.json allows `Bash(make validate)`,
# which matches a command that cannot run here, so the allowlist granted nothing
# and every gate run went back to a prompt. An allowlist that does not reach the
# real command is decoration.
#
# IT DOES NOT KEEP ITS OWN LIST OF VALIDATORS. It parses PY_VALIDATORS, EXTRA,
# SH_VALIDATORS and DATA_GATES out of the Makefile, because the entire reason the
# Makefile exists is that the list of gates once lived in two places and four of
# them had drifted out of CI while still passing locally. A shim with its own copy
# would be the third place. Adding a gate is still one line in the Makefile.
#
#   bash scripts/make.sh validate        every code gate, keep going, then report;
#                                        data gates run and report, no exit code
#   bash scripts/make.sh validate-fast   code gates, stop at the first failure
#   bash scripts/make.sh data-gates      the data gates ALONE, exiting on them
#   bash scripts/make.sh html            rebuild docs/html/ from the papers' .md
#   bash scripts/make.sh library-check   the library's gate on its own
#   bash scripts/make.sh list            what would run
#
# NOT COVERED, DELIBERATELY: `figures`. It has an ADOPT=1 mode that overwrites the
# committed Currencies figures, which CLAUDE.md says not to run yet, and a shim is
# not the place to make that easier to reach by accident. Use make on a box that
# has it, or run altdata.fx_charts directly.
#
# The deploy is NOT here either -- it is scripts/deploy.sh, which this script
# deliberately does not wrap. Two ways to spell the deploy is two shapes to
# allowlist, and the narrowness is the point.

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

# The same interpreter the Makefile picks, and for the same reason: a bare
# `python` on the authoring laptop has neither PyYAML nor pandas, and the failure
# reads as a broken validator rather than a missing interpreter.
if [ -x .venv/bin/python ]; then
    PY=.venv/bin/python
elif [ -x .venv/Scripts/python.exe ]; then
    PY=.venv/Scripts/python.exe
else
    PY=python
fi

# One variable out of the Makefile, continuations joined, CR stripped -- the
# working copy may be CRLF on Windows and a trailing \r turns every path into one
# that does not exist.
mk_list() {
    awk -v v="$1" '
        $0 ~ "^" v "[ \t]*:?=" { sub(/^[^=]*=/, ""); found = 1 }
        found {
            line = $0
            cont = (line ~ /\\[ \t]*$/)
            sub(/\\[ \t]*$/, "", line)
            print line
            if (!cont) exit
        }
    ' Makefile | tr -d '\r'
}

PY_VALIDATORS="$(mk_list PY_VALIDATORS)"
EXTRA="$(mk_list EXTRA)"
SH_VALIDATORS="$(mk_list SH_VALIDATORS)"
DATA_GATES="$(mk_list DATA_GATES)"

if [ -z "$(echo "$PY_VALIDATORS" | tr -d ' \n')" ]; then
    echo "could not read PY_VALIDATORS out of the Makefile -- refusing to run a" >&2
    echo "shorter list than the Makefile holds, which is the failure this whole" >&2
    echo "arrangement exists to prevent." >&2
    exit 2
fi

# How one gate runs. Shell gates go through bash, everything else through $PY.
run_gate() {
    case "$1" in
        *.sh) bash "$1" ;;
        *)    "$PY" "$1" ;;
    esac
}

target="${1:-validate}"

case "$target" in

list)
    echo "python:"; for v in $PY_VALIDATORS $EXTRA; do echo "  $v"; done
    echo "shell:";  for v in $SH_VALIDATORS; do echo "  $v"; done
    echo "data:";   for v in $DATA_GATES; do echo "  $v"; done
    echo "interpreter: $PY"
    ;;

html)
    exec "$PY" tools/build_paper_html.py
    ;;

library-check)
    exec "$PY" tools/check_library.py
    ;;

validate)
    # Runs every gate and THEN reports, like the make target: the question after
    # a change is "what did I break", not "what did I break first".
    out="$(mktemp)"
    fail=0
    for v in $PY_VALIDATORS $EXTRA $SH_VALIDATORS; do
        printf '%-44s' "$v"
        if run_gate "$v" >"$out" 2>&1; then
            echo "PASS"
        else
            echo "FAIL"; fail=1
            sed 's/^/    | /' "$out" | tail -12
        fi
    done
    echo
    # DATA GATES REPORT AND DO NOT SET THE EXIT CODE. Their verdict depends on the
    # data on this box, not on the commit under test, so a finding here is not a
    # regression -- see the Makefile's own note. The threshold is untouched.
    dfail=0
    for v in $DATA_GATES; do
        printf '%-44s' "$v"
        if run_gate "$v" >"$out" 2>&1; then
            echo "PASS"
        else
            echo "VERDICT  (data gate -- reported, not counted)"; dfail=1
            sed 's/^/    | /' "$out" | tail -14
        fi
    done
    rm -f "$out"
    echo
    if [ "$fail" -eq 0 ]; then echo "ALL CODE GATES PASSED"; else echo "CODE GATES FAILED"; fi
    if [ "$dfail" -ne 0 ]; then
        echo "A DATA GATE REPORTED A FINDING -- see above. This does NOT fail the"
        echo "suite: its verdict is about the data on this box, not about the code."
        echo "Run 'bash scripts/make.sh data-gates' to exit non-zero on it."
    fi
    exit "$fail"
    ;;

validate-fast)
    set -e
    for v in $PY_VALIDATORS $EXTRA $SH_VALIDATORS; do
        echo "== $v"
        run_gate "$v" >/dev/null
    done
    echo "ALL CODE GATES PASSED  (data gates: bash scripts/make.sh data-gates)"
    ;;

data-gates)
    fail=0
    for v in $DATA_GATES; do
        echo "== $v"
        run_gate "$v" || fail=1
    done
    exit "$fail"
    ;;

*)
    echo "unknown target: $target" >&2
    echo "one of: validate validate-fast data-gates html library-check list" >&2
    exit 2
    ;;
esac
