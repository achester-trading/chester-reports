#!/usr/bin/env bash
#
# Write the decision register from the laptop, into the ONE register on the box.
#
#   scripts/decide_remote.sh list
#   scripts/decide_remote.sh show fae90045
#   scripts/decide_remote.sh record --instrument SPY@ARCA.USD --direction long \
#       --thesis "a thesis with spaces, commas and 'quotes'" ...
#
# WHY THIS EXISTS RATHER THAN A SECOND REGISTER.
#
# The register used to live on the laptop while Portfolio Truth lived on the VPS,
# and a register that cannot see the positions it describes cannot check itself.
# Two failures came out of that on 19 September: the close report's decision and
# invalidation columns were structurally empty on the box, and a decision about a
# position that demonstrably existed landed DECISION_BLOCKED because the machine
# holding the register could not see the observation proving it.
#
# The fix is one store, on the box. This script is the laptop's way to write to
# it, so the answer to "where is the register" stays a single place rather than
# becoming "it depends which machine you were on".
#
# QUOTING IS THE WHOLE IMPLEMENTATION. A thesis is a sentence: it has spaces,
# commas, apostrophes and em dashes, and every one of them is a chance for an
# argument to arrive at the box split in two or mangled. `printf %q` quotes each
# argument for the REMOTE shell, one at a time, so what decide.py parses on the
# box is byte-for-byte what was typed here. Passing "$@" through unquoted, or
# joining with spaces, silently corrupts exactly the field that carries the
# reasoning.
#
# Overridable:
#   CHESTER_SSH_HOST   ssh destination        (vps)
#   CHESTER_REMOTE_REPO  checkout on the box  (~/chester-reports)

set -uo pipefail

HOST="${CHESTER_SSH_HOST:-vps}"
REMOTE_REPO="${CHESTER_REMOTE_REPO:-\$HOME/chester-reports}"

if [[ $# -eq 0 ]]; then
    sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
fi

# Each argument quoted for the remote shell, separately.
REMOTE_ARGS=""
for a in "$@"; do
    REMOTE_ARGS+=" $(printf '%q' "$a")"
done

# THE BOX'S CODE IS WHAT WRITES THE PACKET, so a stale checkout there records a
# decision made by older code under an older git_sha. Warned rather than
# refused: the packet records the SHA it ran at, so the fact is preserved either
# way, and a hard block would land precisely when a decision most needs writing.
LOCAL_SHA="$(git -C "$(dirname "$0")/.." rev-parse --short HEAD 2>/dev/null || echo unknown)"
REMOTE_SHA="$(ssh -o BatchMode=yes "$HOST" "cd $REMOTE_REPO && git rev-parse --short HEAD" 2>/dev/null || echo unknown)"
if [[ "$LOCAL_SHA" != "$REMOTE_SHA" ]]; then
    printf 'WARNING: the box is at %s and this checkout is at %s.\n' \
        "$REMOTE_SHA" "$LOCAL_SHA" >&2
    printf '         The decision will be written by the BOX'"'"'s code and its packet will\n' >&2
    printf '         record %s. Push and pull first if that is not what you want.\n\n' "$REMOTE_SHA" >&2
fi

printf '-> %s:%s  decide.py%s\n\n' "$HOST" "$REMOTE_REPO" "$REMOTE_ARGS" >&2

# The box's venv, from the box's checkout, against the box's store. No --db: the
# default is anchored to the repository root now, so it resolves to the one
# register whatever the working directory happens to be.
ssh -o BatchMode=yes "$HOST" \
    "cd $REMOTE_REPO && .venv/bin/python tools/decide.py$REMOTE_ARGS"
RC=$?

if [[ $RC -ne 0 ]]; then
    printf '\ndecide.py exited %s on %s -- nothing was written unless it says so above.\n' \
        "$RC" "$HOST" >&2
fi
exit $RC
