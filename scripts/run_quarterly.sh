#!/usr/bin/env bash
#
# The Alternative Assets Quarterly, as its timer runs it (AQ-1).
#
#   git pull --ff-only -> venv monthly_macro.run --cadence quarterly -> log
#   -> status -> heartbeat
#
# ONE RUNNER. The Quarterly is the Monthly's runner at the fourth cadence
# (monthly_macro.run --cadence quarterly), not a parallel pipeline; this wrapper
# is run_monthly.sh's shape with the Quarterly's files, so the two never share a
# lock, a status file or a heartbeat.
#
# THE SECOND SATURDAY AFTER QUARTER-END, 06:00 ET (chester-quarterly.timer). The
# report reads stored data, so the weekend is as good as a weekday, and it never
# fetches: the box's passes own the store.
#
# SHIPPED DISABLED. The timer is not in DEPLOY_TIMERS; the operator enables it
# after the December dry run. Until it is enabled the heartbeat does not watch it.
#
# Exit codes are monthly_macro.run's, passed through:
#   0 built, archived and delivered
#   1 the run failed
#   2 built and ARCHIVED but NOT delivered -- the report is on disk
#
# Overridable:
#   CHESTER_REPO           repo checkout    (~/chester-reports)
#   CHESTER_LOG_DIR        log directory    (~/logs)
#   CHESTER_STATE_DIR      status dir       -- MANDATORY (the unit sets it)
#   CHESTER_PYTHON         interpreter      ($REPO/.venv/bin/python)
#   CHESTER_QUARTERLY_AS_OF          point-in-time cutoff, for replaying a quarter
#   CHESTER_QUARTERLY_NO_NARRATIVE=1 ship the data-only edition
#   CHESTER_QUARTERLY_DELIVER_ONLY=YYYY-MM-DD  re-send that archived edition and
#                                    build nothing

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"

if [[ -z "${CHESTER_STATE_DIR:-}" ]]; then
    printf '%s\n' \
        "FATAL run_quarterly.sh: CHESTER_STATE_DIR is unset, and there is no safe" \
        "default -- the status and heartbeat files must land where the monitor" \
        "reads them." \
        "  by hand:  CHESTER_STATE_DIR=\"\$HOME/state\" ./scripts/run_quarterly.sh" >&2
    exit 1
fi
STATE_DIR="$CHESTER_STATE_DIR"
export CHESTER_STATE_DIR

mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/quarterly-$(date +%Y).log"
STATUS="$STATE_DIR/quarterly_status"
HEARTBEAT="$STATE_DIR/quarterly_heartbeat"
LOCK="$STATE_DIR/quarterly.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another quarterly run holds the lock"
    exit 0
fi

if [[ ! -d "$REPO/.git" ]]; then
    log "FATAL no git checkout at $REPO"
    printf 'state=no_repo at=%s\n' "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi
cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }

PULL_STATUS=ok
git pull --ff-only >>"$LOG" 2>&1 || PULL_STATUS=failed
SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
    log "FATAL no interpreter at $PY"
    printf 'state=no_venv sha=%s at=%s\n' "$SHA" "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi

ARGS=(--cadence quarterly --skip-fetch)
[[ -n "${CHESTER_QUARTERLY_AS_OF:-}" ]] && ARGS+=(--as-of "$CHESTER_QUARTERLY_AS_OF")
[[ -n "${CHESTER_QUARTERLY_NO_NARRATIVE:-}" ]] && ARGS+=(--skip-narrative)
if [[ -n "${CHESTER_QUARTERLY_DELIVER_ONLY:-}" ]]; then
    ARGS=(--cadence quarterly --deliver-only "$CHESTER_QUARTERLY_DELIVER_ONLY")
fi

log "=== quarterly start sha=$SHA pull=$PULL_STATUS ${ARGS[*]}"
START=$(date +%s)
"$PY" -m monthly_macro.run "${ARGS[@]}" >>"$LOG" 2>&1
RC=$?
ELAPSED=$(( $(date +%s) - START ))

case $RC in
    0) STATE=ok;            DELIVERY="smtp ok";     MSG="quarterly built, archived and delivered" ;;
    1) STATE=failed;        DELIVERY="none";        MSG="RUN FAILED -- see the log" ;;
    2) STATE=not_delivered; DELIVERY="smtp failed"; MSG="built and ARCHIVED but delivery failed -- the report is on disk" ;;
    *) STATE=error;         DELIVERY="none";        MSG="quarterly report failed rc=$RC" ;;
esac
if [[ -n "${CHESTER_QUARTERLY_DELIVER_ONLY:-}" ]]; then
    case $RC in
        0) MSG="re-delivered (no build) the archived edition of $CHESTER_QUARTERLY_DELIVER_ONLY" ;;
        2) MSG="re-delivery FAILED (no build) for $CHESTER_QUARTERLY_DELIVER_ONLY -- the archive is unchanged" ;;
    esac
fi
log "$MSG (rc=$RC, ${ELAPSED}s)"
log "delivery=$DELIVERY"

printf 'state=%s rc=%s delivery=%s sha=%s pull=%s elapsed=%s at=%s\n' \
    "$STATE" "$RC" "${DELIVERY// /_}" "$SHA" "$PULL_STATUS" "$ELAPSED" \
    "$(date --iso-8601=seconds)" >"$STATUS"

# THE HEARTBEAT ONLY ON A RUN THAT PRODUCED A REPORT, with its state first.
if [[ "$RC" -eq 0 || "$RC" -eq 2 ]]; then
    printf '%s sha=%s rc=%s at=%s\n' "$STATE" "$SHA" "$RC" \
        "$(date --iso-8601=seconds)" >"$HEARTBEAT"
fi

exit $RC
