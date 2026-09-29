#!/usr/bin/env bash
#
# The deploy. Six steps, a fixed body, and no verb that can take a running unit
# down.
#
# WHY A SCRIPT AND NOT A MAKE RECIPE. It began as one and could not run from
# either machine: `make` is absent on the laptop (a stock Windows box, as
# CLAUDE.md warns) while the box is the only place make exists -- and the box
# cannot resolve `vps`, because `vps` is the laptop's ssh alias FOR the box. So the
# recipe was unrunnable in both directions. The logic lives here, `make deploy`
# delegates to it, and the laptop can run it directly under Git Bash today.
#
# It is also better placed here on its own merits: make escaping is what produced
# the `$$` thicket and hid a `set -o pipefail` under dash until the first real run
# died on it.
#
# ONE ssh CONNECTION. The box-side work -- steps 1-6 -- is scripts/deploy_remote.sh,
# shipped to the box over a single `ssh vps 'bash -s' < deploy_remote.sh`. Until
# 28 Sep 2026 this script opened a new ssh session per step and two per timer in
# step 4, about fifteen connections in under a minute; that deploy completed steps
# 1-3 and then every call timed out on port 22 while the box was up. One session
# is under any per-source threshold, and ssh ControlMaster -- the usual cure --
# is not available from the Windows laptop. The two files are ONE fixed deploy
# body and tools/validate_deploy.py audits both.
#
# WHAT IT DOES, in order and nothing else (all on the box, in that one session):
#   1. git pull --ff-only on the box   (--ff-only: never a merge commit on a
#                                       machine whose rule is that it runs code
#                                       and never edits it)
#   2. copy deploy/systemd/*.service and *.timer into ~/.config/systemd/user/
#   3. systemctl --user daemon-reload
#   4. enable --now any timer in DEPLOY_TIMERS not already enabled
#   5. the drift check and the heartbeat checker
#   6. print the timer roster
# and then, here on the laptop, the verdict below.
#
# WHAT IT WILL NEVER DO. Neither file contains a stop, disable, restart or kill,
# and tools/validate_deploy.py reads both to assert that line by line. A deploy
# that can restart a unit is a deploy that can take the Gateway down mid-session
# while nobody is watching, and the cost is asymmetric: the worst case of refusing
# is a printed command, the worst case of acting is a dead pipeline with a
# position open.
#
# SO A CHANGED UNIT THAT IS RUNNING EXITS 3. daemon-reload re-reads unit files but
# an ACTIVE unit keeps running the old one -- a live timer keeps its computed
# next-elapse, a long-running service keeps its old ExecStart -- so the deploy is
# genuinely incomplete and says so with the exact command to finish it. An INACTIVE
# unit needs nothing: a oneshot picks up the new file on its next activation, which
# is why most deploys here exit 0.
#
# EXIT CODES
#   0  clean: copied, enabled, nothing needs a restart, drift clean
#   3  a changed unit is RUNNING and needs a restart you must run yourself
#   4  drift still reported AFTER the copy -- the deploy did not take
#   1  the pull or the copy itself failed, or the connection did
#
# Overridable:
#   DEPLOY_HOST        ssh destination           (vps)
#   DEPLOY_REPO        checkout on the box       (~/chester-reports)
#   DEPLOY_UNIT_DIR    installed units           (~/.config/systemd/user)
#   DEPLOY_STATE_DIR   the box's state dir       (~/state)

set -uo pipefail

HOST="${DEPLOY_HOST:-vps}"
# Passed to the remote script as arguments. Left unexpanded here ('$HOME...') so
# they resolve on the BOX, where $HOME is the box's home, not the laptop's.
REPO_REMOTE="${DEPLOY_REPO:-\$HOME/chester-reports}"
UNIT_DIR="${DEPLOY_UNIT_DIR:-\$HOME/.config/systemd/user}"
STATE_DIR="${DEPLOY_STATE_DIR:-\$HOME/state}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE="$HERE/deploy_remote.sh"
BAR="=============================================================================="

if [ ! -r "$REMOTE" ]; then
    echo "deploy_remote.sh is missing beside this script -- nothing was run" >&2
    exit 1
fi

echo "$BAR"
echo "DEPLOY -> $HOST   (never stops, disables, restarts or kills a unit)"
echo "$BAR"

# ONE ssh CONNECTION FOR STEPS 1-6. The remote script prints each section as it
# runs; its three @@ marker lines are captured for the verdict below and not
# printed. BatchMode: a deploy must never sit at a password prompt.
OUT="$(mktemp)"
trap 'rm -f "$OUT"' EXIT
ssh -o BatchMode=yes "$HOST" "bash -s -- \"$REPO_REMOTE\" \"$UNIT_DIR\" \"$STATE_DIR\"" \
    < "$REMOTE" | tee "$OUT" | grep -v '^@@'
REMOTE_RC=${PIPESTATUS[0]}

# The pull or the copy failed on the box (exit 1), or ssh itself did not connect
# (255). Either way steps 2-6 are not known to have run.
if [ "$REMOTE_RC" -ne 0 ]; then
    echo "$BAR"
    echo "DEPLOY FAILED on the box or on the connection (exit $REMOTE_RC) --"
    echo "the pull or the unit copy did not complete. Nothing was restarted."
    echo "$BAR"
    exit 1
fi

NEEDS="$(sed -n 's/^@@NEEDS //p' "$OUT" | tail -1)"
DRIFT="$(sed -n 's/^@@DRIFT //p' "$OUT" | tail -1)"

echo "$BAR"
rc=0
if [ -n "${NEEDS// /}" ]; then
    echo "A CHANGED UNIT IS RUNNING. daemon-reload re-read the file; the running"
    echo "unit is still on the old one. This deploy will not restart it -- run:"
    echo
    for u in $NEEDS; do
        # Printed, never executed. This line is the entire reason the deploy
        # exits 3 instead of acting.
        echo "    ssh $HOST 'systemctl --user restart $u'"
    done
    echo
    echo "Then re-run the deploy to confirm."
    rc=3
fi
if [ -n "$DRIFT" ] && [ "$DRIFT" != clean ] && [ "$DRIFT" != none_installed ]; then
    echo "DRIFT IS STILL $DRIFT AFTER THE COPY -- the deploy did not take."
    echo "An undeclared drop-in, or a unit the copy loop did not cover. See"
    echo "deploy/systemd/box-config.allow and the heartbeat log."
    [ "$rc" -eq 0 ] && rc=4
fi
[ "$rc" -eq 0 ] && echo "DEPLOY CLEAN."
echo "$BAR"
exit "$rc"
