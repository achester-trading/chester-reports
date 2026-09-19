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
# WHAT IT DOES, in order and nothing else:
#   1. git pull --ff-only on the box   (--ff-only: never a merge commit on a
#                                       machine whose rule is that it runs code
#                                       and never edits it)
#   2. copy deploy/systemd/*.service and *.timer into ~/.config/systemd/user/
#   3. systemctl --user daemon-reload
#   4. enable --now any timer in DEPLOY_TIMERS not already enabled
#   5. the drift check and the heartbeat checker
#   6. print the timer roster
#
# WHAT IT WILL NEVER DO. It contains no stop, no disable, no restart and no kill,
# and tools/validate_deploy.py reads this file to assert that line by line. A
# deploy that can restart a unit is a deploy that can take the Gateway down
# mid-session while nobody is watching, and the cost is asymmetric: the worst case
# of refusing is a printed command, the worst case of acting is a dead pipeline
# with a position open.
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
#   1  the pull or the copy itself failed
#
# Overridable:
#   DEPLOY_HOST        ssh destination           (vps)
#   DEPLOY_REPO        checkout on the box       (~/chester-reports)
#   DEPLOY_UNIT_DIR    installed units           (~/.config/systemd/user)
#   DEPLOY_STATE_DIR   the box's state dir       (~/state)

set -uo pipefail

HOST="${DEPLOY_HOST:-vps}"
REPO_REMOTE="${DEPLOY_REPO:-\$HOME/chester-reports}"
UNIT_DIR="${DEPLOY_UNIT_DIR:-\$HOME/.config/systemd/user}"
STATE_DIR="${DEPLOY_STATE_DIR:-\$HOME/state}"

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
"

BAR="=============================================================================="
sh_() { ssh -o BatchMode=yes "$HOST" "$@"; }

echo "$BAR"
echo "DEPLOY -> $HOST   (never stops, disables, restarts or kills a unit)"
echo "$BAR"

echo "-- 1. pull --ff-only"
sh_ "cd $REPO_REMOTE && git pull --ff-only" || exit 1
SHA="$(sh_ "cd $REPO_REMOTE && git rev-parse --short HEAD")" || exit 1
echo "   box at $SHA"
echo

echo "-- 2. copy units, and note which CHANGED while running"
# The whole loop runs on the box in one shell: it has to compare, read
# is-active BEFORE overwriting, and copy, and splitting that across ssh calls
# would race its own copy.
NEEDS="$(sh_ "cd $REPO_REMOTE && mkdir -p $UNIT_DIR && need=''
for f in deploy/systemd/*.service deploy/systemd/*.timer; do
  u=\$(basename \"\$f\"); d=$UNIT_DIR/\$u
  cmp -s \"\$f\" \"\$d\" 2>/dev/null && continue
  was_active=no
  if [ -e \"\$d\" ] && systemctl --user is-active --quiet \"\$u\" 2>/dev/null; then was_active=yes; fi
  cp \"\$f\" \"\$d\"
  echo \"   copied \$u\" >&2
  [ \"\$was_active\" = yes ] && need=\"\$need \$u\"
done
printf '%s' \"\$need\"")" || exit 1
echo "   (nothing copied = every unit already matched the repo)"
echo

echo "-- 3. daemon-reload"
sh_ "systemctl --user daemon-reload" && echo "   ok"
echo

echo "-- 4. enable --now any declared timer not yet enabled"
for t in $DEPLOY_TIMERS; do
    if sh_ "systemctl --user is-enabled --quiet $t 2>/dev/null"; then
        echo "   already enabled  $t"
    else
        echo "   enabling         $t"
        sh_ "systemctl --user enable --now $t" 2>&1 | sed 's/^/     /'
    fi
done
echo

echo "-- 5. drift check and heartbeat"
sh_ "cd $REPO_REMOTE && CHESTER_STATE_DIR=$STATE_DIR ./scripts/check_heartbeat_cron.sh" \
    >/dev/null 2>&1
HB=$?
sh_ "grep -hE 'verdict=' \$HOME/logs/heartbeat_check-*.log | tail -1" | sed 's/^/   /'
DRIFT="$(sh_ "sed -n 's/.*drift=\([a-z_]*\).*/\1/p' $STATE_DIR/heartbeat_check_status 2>/dev/null")"
echo "   heartbeat exit=$HB   drift=${DRIFT:-unknown}"
echo

echo "-- 6. timer roster"
sh_ "systemctl --user list-timers --all --no-pager" | sed 's/^/   /'
echo

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
