#!/usr/bin/env bash
#
# THE BOX-SIDE HALF OF THE DEPLOY. Not run by hand. It has two callers:
# scripts/deploy.sh ships this file over ONE ssh connection --
#
#     ssh -o BatchMode=yes vps 'bash -s -- <repo> <unit_dir> <state_dir>' < scripts/deploy_remote.sh
#
# -- and it runs steps 1-6 on the box in that one session; and the box's own
# self-deploy (scripts/run_self_deploy.sh, chester-deploy.timer, A-4) runs the
# same file from the checkout when main's deploy/systemd/ has changed.
#
# WHY ONE CONNECTION. Until 28 Sep 2026 the deploy opened a new ssh session per
# step and two per timer in step 4 -- about fifteen connections in under a minute
# -- and that deploy died after step 3 with every later call timing out on port 22
# while the box was up. One session is under any per-source threshold, whatever
# the box's limiter turns out to be, and ssh ControlMaster (the usual answer) is
# not available from the Windows laptop this runs from.
#
# THE SAME INVARIANTS AS BEFORE, and tools/validate_deploy.py reads this file as
# part of the fixed deploy body: no stop, no disable, no restart, no kill, no mask
# is executed; the pull is --ff-only; timers are only ever ENABLED, from the
# declared list below and never from a glob.
#
# OUTPUT CONTRACT with scripts/deploy.sh: the numbered sections are printed as they
# run, and the last lines are three markers the caller parses and does not print --
#     @@NEEDS <units that changed while running>
#     @@DRIFT <drift state from the heartbeat's status file>
#     @@HB    <the heartbeat checker's exit code>
# Exit 1 means the pull or the copy failed and nothing after it ran.
#
# STDIN IS THE SCRIPT ITSELF. `bash -s` reads it from the ssh pipe, so the body is
# one function, parsed whole before anything runs, and called with </dev/null so
# no command inside it can read the rest of the script as its own input.

set -uo pipefail

REPO_REMOTE="${1:-$HOME/chester-reports}"
UNIT_DIR="${2:-$HOME/.config/systemd/user}"
STATE_DIR="${3:-$HOME/state}"

# THE TIMERS THIS MAY ENABLE. A declared list, not a glob over the unit
# directory, and the difference matters: ibgateway.service and
# ibgateway-restart.timer are deliberately held back behind a witnessed clean
# start (deploy/systemd/README.md section 4), and a glob would enable them the
# first time anybody ran a deploy. Adding a timer here is a deliberate edit.
DEPLOY_TIMERS="
chester-eod.timer
chester-daily-close.timer
chester-heartbeat.timer
chester-ibkr-sync.timer
chester-backup.timer
chester-overnight.timer
chester-morning-anchor.timer
chester-weekly.timer
chester-voices.timer
chester-auction.timer
chester-deploy.timer
"

deploy_main() {
    echo "-- 1. pull --ff-only"
    cd "$REPO_REMOTE" || { echo "   cannot cd $REPO_REMOTE"; return 1; }
    git pull --ff-only || return 1
    echo "   box at $(git rev-parse --short HEAD)"
    echo

    echo "-- 2. copy units, and note which CHANGED while running"
    # Compare, read is-active BEFORE overwriting, then copy -- in that order, per
    # unit, so a copy never races its own check.
    mkdir -p "$UNIT_DIR" || return 1
    local need="" f u d was_active
    for f in deploy/systemd/*.service deploy/systemd/*.timer; do
        u="$(basename "$f")"
        d="$UNIT_DIR/$u"
        cmp -s "$f" "$d" 2>/dev/null && continue
        was_active=no
        if [ -e "$d" ] && systemctl --user is-active --quiet "$u" 2>/dev/null; then
            was_active=yes
        fi
        cp "$f" "$d" || return 1
        echo "   copied $u"
        [ "$was_active" = yes ] && need="$need $u"
    done
    echo "   (nothing copied = every unit already matched the repo)"
    # THE LEDGER (A-4): a changed unit left RUNNING is written to
    # $STATE_DIR/alerts/restart_pending, and the heartbeat names it until the
    # operator restarts it. Resolved lines are pruned first. Recorded, never acted
    # on: the restart stays the operator's.
    if [ -f ./scripts/restart_pending.sh ]; then
        bash ./scripts/restart_pending.sh "$STATE_DIR" prune
        if [ -n "$need" ]; then
            # shellcheck disable=SC2086  # $need is a space-separated unit list
            bash ./scripts/restart_pending.sh "$STATE_DIR" record $need \
                && echo "   restart pending, recorded in $STATE_DIR/alerts/restart_pending:$need"
        fi
    fi
    echo

    echo "-- 3. daemon-reload"
    systemctl --user daemon-reload && echo "   ok"
    echo

    echo "-- 4. enable --now any declared timer not yet enabled"
    local t
    for t in $DEPLOY_TIMERS; do
        if systemctl --user is-enabled --quiet "$t" 2>/dev/null; then
            echo "   already enabled  $t"
        else
            echo "   enabling         $t"
            systemctl --user enable --now "$t" 2>&1 | sed 's/^/     /'
        fi
    done
    echo

    echo "-- 5. drift check and heartbeat"
    CHESTER_STATE_DIR="$STATE_DIR" ./scripts/check_heartbeat_cron.sh >/dev/null 2>&1
    local hb=$?
    grep -hE 'verdict=' "$HOME"/logs/heartbeat_check-*.log 2>/dev/null | tail -1 \
        | sed 's/^/   /'
    local drift
    drift="$(sed -n 's/.*drift=\([a-z_]*\).*/\1/p' "$STATE_DIR/heartbeat_check_status" \
             2>/dev/null)"
    echo "   heartbeat exit=$hb   drift=${drift:-unknown}"
    echo

    echo "-- 6. timer roster"
    systemctl --user list-timers --all --no-pager | sed 's/^/   /'
    echo

    echo "@@NEEDS $need"
    echo "@@DRIFT ${drift:-}"
    echo "@@HB $hb"
    return 0
}

deploy_main </dev/null
exit $?
