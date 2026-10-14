#!/usr/bin/env bash
#
# THE BOX'S SELF-DEPLOY (A-4, 9 Oct 2026), under chester-deploy.timer.
#
# A push to main already reaches the box's CODE at the next timer run: every
# wrapper pulls main before it starts. Unit files did not follow: they reached
# ~/.config/systemd/user/ only when somebody ran scripts/deploy.sh from the laptop,
# so a merged unit change sat in the checkout as drift until then. This closes that
# gap, and nothing else:
#
#   1. inside the operating windows only (CLAUDE.md, "Operating windows"), checked
#      here in ET as well as in the timer's calendar, so a manual start or a late
#      timer cannot deploy at 16:30
#   2. git pull --ff-only, as every wrapper does
#   3. prune the restart-pending ledger (a restart since the last run resolves it)
#   4. if main's deploy/systemd/ tree differs from the one the last successful run
#      deployed, run the box half of the deploy -- scripts/deploy_remote.sh, the
#      same file the laptop ships: unit copy, daemon-reload, enable of
#      DEPLOY_TIMERS, the drift check and the heartbeat. Otherwise stop.
#
# IT NEVER RESTARTS, STOPS OR DISABLES A UNIT. When the copy finds a changed unit
# RUNNING, deploy_remote.sh writes "restart pending: <unit>" to
# ~/state/alerts/restart_pending, and the 08:30 heartbeat's verdict names it until
# the operator restarts it. tools/validate_deploy.py group I holds this file, the
# ledger and the unit to that, line by line and end to end.
#
# EXIT CODES. 0: nothing to do, outside the window, deployed, deployed with a
# restart pending (reported through the ledger, not as a failed unit -- the deploy
# WORKED and found something), or deployed with drift still reported (the
# heartbeat's drift verdict is that channel already, and a re-copy cannot clear an
# undeclared drop-in, so retrying every tick would only repeat the alarm). 1: the
# pull or the box half failed, which leaves chester-deploy.service failed and the
# heartbeat's unit check names it; the tree is not recorded, so the next tick
# retries.
#
# Overridable (the validator's scratch box):
#   CHESTER_REPO              checkout                 (~/chester-reports)
#   CHESTER_LOG_DIR           logs                     (~/logs)
#   CHESTER_STATE_DIR         state and alerts         (~/state)
#   CHESTER_SYSTEMD_USER_DIR  installed units          (~/.config/systemd/user)
#   CHESTER_DEPLOY_CLOCK      "<iso weekday> <HHMM>" in ET, instead of the clock

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/state}"
UNIT_DIR="${CHESTER_SYSTEMD_USER_DIR:-$HOME/.config/systemd/user}"
LAST_TREE="$STATE_DIR/self_deploy_last_tree"
STATUS="$STATE_DIR/self_deploy_status"

# THE OPERATING WINDOWS, in ET (CLAUDE.md). Weekdays 09:05-15:40 and 17:20-23:30,
# never 16:00-17:20 while the EOD pass and the 16:45 close run. Weekends open,
# clear of the Sunday 05:00 Weekly (04:00-06:59 here). The timer's calendar is
# written inside these; this is the second guard, not the first.
in_window() {                    # in_window <iso weekday 1-7> <HHMM>
    local d="$1" t=$((10#$2))
    if (( d <= 5 )); then
        (( t >= 905 && t <= 1540 )) || (( t >= 1720 && t <= 2330 ))
        return
    fi
    if (( d == 7 )) && (( t >= 400 && t < 700 )); then
        return 1
    fi
    return 0
}

self_deploy_main() {
    mkdir -p "$LOG_DIR" "$STATE_DIR" || return 1
    local log_file="$LOG_DIR/self_deploy-$(date +%Y-%m).log"
    log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$log_file"; }

    local clock
    clock="${CHESTER_DEPLOY_CLOCK:-$(TZ=America/New_York date +'%u %H%M')}"
    # shellcheck disable=SC2086  # "<weekday> <HHMM>", two words on purpose
    if ! in_window $clock; then
        log "SKIP outside the operating windows (ET $clock)"
        return 0
    fi

    # flock is util-linux: on the box always; absent from Git Bash, where only the
    # validator's scratch box runs this and nothing can contend.
    exec 9>"$STATE_DIR/self_deploy.lock"
    if command -v flock >/dev/null 2>&1 && ! flock -n 9; then
        log "SKIP another self-deploy holds the lock"
        return 0
    fi

    cd "$REPO" || { log "FATAL cannot cd $REPO"; return 1; }
    if ! git pull --ff-only -q >/dev/null 2>&1; then
        log "FAIL git pull --ff-only"
        printf 'state=pull_failed at=%s\n' "$(date --iso-8601=seconds)" >"$STATUS"
        return 1
    fi
    local sha tree last
    sha="$(git rev-parse --short HEAD)"
    tree="$(git rev-parse HEAD:deploy/systemd 2>/dev/null)"
    [[ -f ./scripts/restart_pending.sh ]] \
        && bash ./scripts/restart_pending.sh "$STATE_DIR" prune
    last="$(cat "$LAST_TREE" 2>/dev/null)"
    if [[ -n "$tree" ]] && [[ "$tree" == "$last" ]]; then
        log "unchanged deploy/systemd/ at $sha -- nothing to deploy"
        return 0
    fi

    log "deploy/systemd/ changed (${last:-never deployed} -> $tree) at $sha -- running the box half"
    local out rc needs drift
    out="$(bash ./scripts/deploy_remote.sh "$REPO" "$UNIT_DIR" "$STATE_DIR" </dev/null 2>&1)"
    rc=$?
    printf '%s\n' "$out" | grep -v '^@@' | sed 's/^/  /' >>"$log_file"
    if [[ $rc -ne 0 ]]; then
        log "FAIL the box half exited $rc -- the pull or the unit copy did not complete"
        printf 'state=deploy_failed rc=%s sha=%s at=%s\n' "$rc" "$sha" \
            "$(date --iso-8601=seconds)" >"$STATUS"
        return 1
    fi
    needs="$(printf '%s\n' "$out" | sed -n 's/^@@NEEDS //p' | tail -1)"
    drift="$(printf '%s\n' "$out" | sed -n 's/^@@DRIFT //p' | tail -1)"
    needs="${needs# }"
    printf '%s\n' "$tree" >"$LAST_TREE"
    if [[ -n "$drift" ]] && [[ "$drift" != clean ]] && [[ "$drift" != none_installed ]]; then
        log "deployed $sha; DRIFT still $drift after the copy -- the heartbeat's drift verdict names it${needs:+; restart pending: $needs}"
        printf 'state=drift drift=%s units=%s sha=%s at=%s\n' "$drift" "${needs// /,}" \
            "$sha" "$(date --iso-8601=seconds)" >"$STATUS"
    elif [[ -n "${needs// /}" ]]; then
        log "deployed $sha; RESTART PENDING (recorded, not run):$needs"
        printf 'state=restart_pending units=%s sha=%s at=%s\n' "${needs// /,}" "$sha" \
            "$(date --iso-8601=seconds)" >"$STATUS"
    else
        log "deployed $sha clean"
        printf 'state=ok sha=%s at=%s\n' "$sha" "$(date --iso-8601=seconds)" >"$STATUS"
    fi
    return 0
}

# One function, parsed whole before it runs: the pull above may rewrite this
# file, and bash reads a script as it goes.
self_deploy_main </dev/null
exit $?
