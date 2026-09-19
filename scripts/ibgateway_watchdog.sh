#!/usr/bin/env bash
#
# IB Gateway health watchdog -- the health authority for ibgateway.service.
#
# WHY THIS EXISTS RATHER THAN Restart=on-failure.
#
# Observed on the VPS with bad credentials in IBC's config.ini: IBC sits at
# 294MB RSS, `systemctl --user status ibgateway` reports active (running), and
# NO PORT EVER OPENS. Forever. The process never exits, so Restart=on-failure
# never fires. systemd cannot tell a Gateway waiting on an unanswered login
# dialog from one serving an API, because from the outside they are the same
# process in the same state. Only something that tries to USE the API can.
#
# HEALTHY HAS ONE DEFINITION IN THIS SYSTEM, AND THIS IS NOT A SECOND ONE.
# The probe is the portfolio sync's own connection path, run with --dry-run,
# and the verdict is its exit code. A watchdog with its own idea of healthy
# would eventually disagree with the sync, and then two things would be right
# about different facts:
#
#   0  OK              connected, authenticated, account readable
#   3  NOT_LISTENING   nothing on the port -- Gateway down, OR the hang above
#   4  NOT_RESPONDING  listening, handshake stalled -- API off, clientId clash
#   5  SIGNED_OUT      connected and logged out; looks healthy from outside
#   6  API_ERROR       anything else
#
# TWO COUNTERS, BECAUSE A RESTART IS NOT ALWAYS THE ANSWER.
#
#   consecutive failures -> restart, after FAILURES_BEFORE_RESTART. Hysteresis
#     so a single probe landing during startup or a daily restart does not
#     trigger another one.
#
#   restarts today -> STOP RESTARTING after MAX_RESTARTS_PER_DAY. This is the
#     important one. The hang this watchdog exists for is caused by BAD
#     CREDENTIALS, and restarting cannot fix bad credentials. Without a cap the
#     watchdog would restart forever, each cycle looking like action while the
#     real fault -- a wrong password in config.ini -- stays untouched and
#     unreported. Past the cap it stops trying and says so loudly.
#
# Exit codes (the unit maps 0/1/2 all to success, so the timer keeps firing):
#   0 healthy
#   1 unhealthy, restart attempted
#   2 unhealthy, restart SUPPRESSED -- needs a human
#
# STOPPING THE GATEWAY ON PURPOSE -- and the only supported way to place an order.
#
# The API this system uses is read-only by construction: every IBKR service in
# altdata/ connects with readonly=True and tools/validate_ibkr_portfolio.py
# proves no order-placing call exists in the source. Placing an order therefore
# means doing it by hand in the Gateway GUI, which means stopping the headless
# unit first -- and a stopped Gateway is exactly what this watchdog restarts.
#
# Intent is declared by a file. The procedure, in order:
#
#   1. touch  ~/state/gateway.stopped_by_operator      declare the intent FIRST
#   2. systemctl --user stop ibgateway                 then stop the unit
#   3. place the order in the GUI
#   4. rm  ~/state/gateway.stopped_by_operator         hand it back
#
# The marker goes down BEFORE the stop, not after: between the stop and the
# touch the watchdog would see an unexplained dead unit and restart it out from
# under the order being placed. Step 4 is how the Gateway comes back -- the
# watchdog sees a dead unit with no marker and starts it. `systemctl --user
# start ibgateway` also works, and the unit removes the marker itself on start
# so a forgotten step 4 cannot leave the Gateway permanently unguarded.
#
# Overridable:
#   CHESTER_REPO / CHESTER_LOG_DIR / CHESTER_STATE_DIR / CHESTER_PYTHON
#   IBKR_HOST (127.0.0.1)  IBKR_PORT (4002)
#   WATCHDOG_CLIENT_ID (18)          -- NOT the sync's 17; see below
#   FAILURES_BEFORE_RESTART (3)
#   MAX_RESTARTS_PER_DAY (3)
#   GATEWAY_INTENT_FILE ($HOME/state/gateway.stopped_by_operator)

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
HOST="${IBKR_HOST:-127.0.0.1}"
PORT="${IBKR_PORT:-4002}"

# A DIFFERENT clientId from scripts/sync_ibkr.sh (17). IBKR rejects a second
# connection reusing a live clientId, which surfaces as exit 4 -- so sharing
# the id would make the watchdog report NOT_RESPONDING every time it happened
# to probe during a sync, and it would be blaming itself.
CLIENT_ID="${WATCHDOG_CLIENT_ID:-18}"

FAILURES_BEFORE_RESTART="${FAILURES_BEFORE_RESTART:-3}"
MAX_RESTARTS_PER_DAY="${MAX_RESTARTS_PER_DAY:-3}"
UNIT="ibgateway.service"

# Deliberately NOT under STATE_DIR. This one file is typed by a human under
# pressure, mid-procedure, with an order waiting -- so it gets a fixed, short,
# documented path rather than one that moves with an environment variable the
# operator would have to resolve first. ibgateway.service names the same literal
# path to remove it on start, and two places agreeing on a constant is safer
# here than two places computing the same expression.
INTENT_FILE="${GATEWAY_INTENT_FILE:-$HOME/state/gateway.stopped_by_operator}"

mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/ibgateway_watchdog-$(date +%Y-%m).log"
STATE="$STATE_DIR/ibgateway_watchdog.state"
STATUS="$STATE_DIR/ibgateway_health"
LOCK="$STATE_DIR/ibgateway_watchdog.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

# A probe can outlive its five-minute slot if the Gateway is wedged. Overlapping
# watchdogs would each count the same failure and restart in lockstep.
exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another watchdog holds the lock"
    exit 0
fi

# --- state: consecutive failures, restarts today ---------------------------
FAILS=0
RESTARTS=0
RESTART_DAY="$(date +%F)"
if [[ -f "$STATE" ]]; then
    # shellcheck disable=SC1090
    source "$STATE" 2>/dev/null || true
fi
# The restart budget is per calendar day; a new day starts fresh.
if [[ "$RESTART_DAY" != "$(date +%F)" ]]; then
    RESTARTS=0
    RESTART_DAY="$(date +%F)"
fi

save_state() {
    printf 'FAILS=%s\nRESTARTS=%s\nRESTART_DAY=%s\n' \
        "$FAILS" "$RESTARTS" "$RESTART_DAY" >"$STATE"
}

report() {   # report <state> <detail> <exitcode>
    printf 'state=%s detail=%s fails=%s restarts_today=%s at=%s\n' \
        "$1" "$2" "$FAILS" "$RESTARTS" "$(date --iso-8601=seconds)" >"$STATUS"
    save_state
    exit "$3"
}

# --- is the unit even supposed to be up? -----------------------------------
# INTENT IS A FILE, NOT AN INFERENCE.
#
# This branch used to treat ANY not-active unit as a human decision -- the log
# line literally read "stopped deliberately?", question mark and all, because
# the code could not tell. That guess is wrong far more often than it is right.
# IBKR closes the Gateway down on its own schedule every night; a crash, an OOM
# kill and a failed start all land in the same state. In every one of those the
# watchdog did nothing and said it was fine, which is the same outcome as not
# having a watchdog, on the one unit it exists to keep alive.
#
# So a deliberate stop now declares itself by touching a file, and everything
# else is a fault to be fixed. The operator's procedure is in the header.
ACTIVE_STATE="$(systemctl --user is-active "$UNIT" 2>/dev/null || true)"
case "$ACTIVE_STATE" in
    active|reloading)
        ;;                       # up: fall through to the probe

    activating|deactivating)
        # MID-TRANSITION IS NOT DOWN, and this distinction is load-bearing.
        # `is-active` returns non-zero for "activating", so a probe landing
        # during startup used to read as not-active. The Gateway needs tens of
        # seconds and IBC drives a GUI to get there (TimeoutStartSec=5min), so
        # restarting on that reading would interrupt every start before it
        # finished and loop forever -- restarting a Gateway precisely because it
        # was busy starting.
        log "unit $UNIT is $ACTIVE_STATE -- in transition, leaving it alone"
        report "unit_$ACTIVE_STATE" "$UNIT is $ACTIVE_STATE; waiting" 0
        ;;

    *)
        # inactive, failed, or unknown.
        if [[ -f "$INTENT_FILE" ]]; then
            log "unit $UNIT is $ACTIVE_STATE and $INTENT_FILE exists -- stopped"
            log "  by the operator on purpose. Not restarting. Remove the marker"
            log "  to hand the Gateway back to the watchdog."
            FAILS=0
            report "stopped_by_operator" \
                   "$UNIT stopped deliberately; marker present" 0
        fi

        # No marker: nobody claimed this. Bring it back, under the same daily
        # budget as any other restart -- a Gateway that cannot start must not be
        # relaunched all night.
        log "unit $UNIT is $ACTIVE_STATE with no operator marker -- not"
        log "  deliberate. Scheduled closedown, a crash or a failed start all"
        log "  look like this, and all of them want the Gateway back up."
        if [[ $RESTARTS -ge $MAX_RESTARTS_PER_DAY ]]; then
            log "  CRITICAL restart budget exhausted ($RESTARTS/$MAX_RESTARTS_PER_DAY today)."
            log "  NOT restarting. A unit that will not stay up is not a"
            log "  restarting problem -- check the journal and IBC's config.ini."
            report "down_budget_exhausted" \
                   "restart suppressed: budget exhausted, human required" 2
        fi
        RESTARTS=$((RESTARTS + 1))
        FAILS=0
        save_state                   # before spending it; see the note below
        log "  starting $UNIT (restart $RESTARTS of $MAX_RESTARTS_PER_DAY today)"
        if systemctl --user start "$UNIT"; then
            log "  start issued"
            report "down_restarted" \
                   "was $ACTIVE_STATE; started ($RESTARTS/$MAX_RESTARTS_PER_DAY today)" 1
        fi
        log "  ERROR start command failed"
        report "down_start_failed" "start command FAILED" 2
        ;;
esac

PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
    log "FATAL no interpreter at $PY -- cannot probe"
    report "watchdog_broken" "no interpreter at $PY" 2
fi

# --- the probe -------------------------------------------------------------
cd "$REPO" || { log "FATAL cannot cd $REPO"; report "watchdog_broken" "no repo" 2; }
PROBE_OUT="$("$PY" -m altdata.sources.ibkr_portfolio --dry-run \
    --host "$HOST" --port "$PORT" --client-id "$CLIENT_ID" --timeout 20 2>&1)"
RC=$?

case $RC in
    0) STATE_NAME=ok ;;
    3) STATE_NAME=not_listening ;;
    4) STATE_NAME=not_responding ;;
    5) STATE_NAME=signed_out ;;
    *) STATE_NAME=api_error ;;
esac

if [[ $RC -eq 0 ]]; then
    if [[ $FAILS -gt 0 ]]; then
        log "RECOVERED after $FAILS consecutive failure(s)"
    fi
    FAILS=0
    report "ok" "authenticated, ${HOST}:${PORT} serving" 0
fi

# --- unhealthy -------------------------------------------------------------
FAILS=$((FAILS + 1))
log "UNHEALTHY rc=$RC state=$STATE_NAME fails=$FAILS/$FAILURES_BEFORE_RESTART restarts_today=$RESTARTS"
printf '%s\n' "$PROBE_OUT" | tail -3 >>"$LOG"

# The signature of the hang: systemd says active, the port says nothing.
if [[ "$STATE_NAME" == "not_listening" ]]; then
    RSS="$(systemctl --user show "$UNIT" -p MemoryCurrent --value 2>/dev/null)"
    log "  unit is ACTIVE but no port is listening -- the empty-dialog hang " \
        "signature (MemoryCurrent=${RSS:-unknown}). systemd cannot see this."
fi

if [[ $FAILS -lt $FAILURES_BEFORE_RESTART ]]; then
    log "  below the restart threshold; watching"
    report "$STATE_NAME" "failure $FAILS of $FAILURES_BEFORE_RESTART" 1
fi

if [[ $RESTARTS -ge $MAX_RESTARTS_PER_DAY ]]; then
    # The case this cap exists for. Restarting cannot fix a wrong password, and
    # a watchdog looping on one hides the fault behind apparent activity.
    log "  CRITICAL restart budget exhausted ($RESTARTS/$MAX_RESTARTS_PER_DAY today)."
    log "  NOT restarting again. If state=not_listening or signed_out has "
    log "  persisted across restarts, the cause is almost certainly IBC's "
    log "  config.ini credentials -- a restart has never fixed those and "
    log "  never will. Check the credentials, then clear $STATE."
    report "$STATE_NAME" "restart suppressed: budget exhausted, human required" 2
fi

RESTARTS=$((RESTARTS + 1))
FAILS=0

# PERSIST THE BUDGET BEFORE SPENDING IT, NOT AFTER.
#
# The increment used to reach disk only via report(), which runs AFTER
# `systemctl restart` returns -- and the watchdog frequently did not survive
# that call.
#
# What actually happened on the box, 6 Sep 2026: the unit declared
# BindsTo=ibgateway.service, and `systemctl restart` stops a unit before
# starting it, so the stop propagated back and systemd SIGTERMed the watchdog
# mid-call. The increment never landed. The log read "restart 1 of 3 today"
# repeatedly while the state file stayed frozen at RESTARTS=0 -- four restarts
# in two seconds, 84 launch attempts in one day, against a Gateway needing ~90s
# to authenticate. The cap could not fire because the process that increments
# it was being killed by the restart it was counting. BindsTo= is gone now, but
# the ordering defect it exposed is fixed here rather than left to depend on
# that.
#
# The same loss happens without BindsTo=: `systemctl restart` blocks until the
# unit starts or times out, ibgateway.service allows TimeoutStartSec=5min and
# this unit allows 3min, so a Gateway hung on its login dialog outlasts the
# watchdog and systemd kills it mid-call anyway.
#
# A crash, a reboot, or an OOM kill between here and report() has the same
# effect. Writing first makes the counter conservative under every one of them:
# the worst case is a restart charged to the budget that never happened, which
# costs one restart of headroom and fails safe. The alternative fails open, and
# it fails open precisely when the Gateway is at its most wedged.
save_state

log "  restarting $UNIT (restart $RESTARTS of $MAX_RESTARTS_PER_DAY today)"
if systemctl --user restart "$UNIT"; then
    log "  restart issued"
    report "$STATE_NAME" "restarted ($RESTARTS/$MAX_RESTARTS_PER_DAY today)" 1
fi
log "  ERROR restart command failed"
report "$STATE_NAME" "restart command FAILED" 2
