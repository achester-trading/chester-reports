#!/usr/bin/env bash
#
# The Weekly Tactical, as the Sunday timer runs it.
#
#   git pull --ff-only -> venv weekly_report -> log -> status -> heartbeat
#
# NO CALENDAR GUARD, and that is the difference from every other wrapper here.
# The weekday wrappers ask `altdata.session is-session` because a report dated a
# holiday would show the previous session's numbers under today's date. This runs
# ON PURPOSE on a day the market is shut: the week it reports on ended Friday, and
# `week_ending()` resolves that Friday from the calendar itself -- so a Good Friday
# becomes the Thursday without this script knowing anything about holidays.
#
# IT WRITES A HEARTBEAT, unlike the close report. The close's own wrapper explains
# why it does not: its data is already stored and the report regenerates for any
# past session, so there is nothing irreplaceable to alarm about. That is true here
# too -- but a weekly that silently stops is invisible for a week at a time, which
# is long enough for the loop to be broken without anybody noticing. The heartbeat
# is what makes a missed Sunday visible by Monday.
#
# Exit codes are weekly_report.py's, passed through:
#   0 built and delivered
#   1 no payload -- the week could not be resolved (a store or register fault)
#   2 built and archived but DELIVERY FAILED -- the report exists on disk
#   3 built and archived in --dry-run
#
# Overridable:
#   CHESTER_REPO           repo checkout    (~/chester-reports)
#   CHESTER_LOG_DIR        log directory    (~/logs)
#   CHESTER_STATE_DIR      status dir       -- MANDATORY, see below
#   CHESTER_PYTHON         interpreter      ($REPO/.venv/bin/python)
#   CHESTER_WEEK_ENDING    report on this week instead of the one just past
#   CHESTER_WEEKLY_DRY_RUN=1   build and archive, send nothing
#   CHESTER_WEEKLY_NO_FETCH=1  skip the two forward reads

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"

# MANDATORY, for the reason the heartbeat scripts give at length: a status file
# written where nobody reads it is a report that looks missing. Unlike those two
# this script WRITES rather than reads, so the wrong directory loses the record
# instead of inventing an outage -- still worth refusing rather than guessing.
if [[ -z "${CHESTER_STATE_DIR:-}" ]]; then
    printf '%s\n' \
        "FATAL run_weekly.sh: CHESTER_STATE_DIR is unset, and there is no safe" \
        "default -- the status and heartbeat files must land where the monitor" \
        "reads them." \
        "  systemd:  Environment=CHESTER_STATE_DIR=%h/state (a drop-in)" \
        "  by hand:  CHESTER_STATE_DIR=\"\$HOME/state\" ./scripts/run_weekly.sh" >&2
    exit 1
fi
STATE_DIR="$CHESTER_STATE_DIR"
export CHESTER_STATE_DIR

mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/weekly-$(date +%Y-%m).log"
STATUS="$STATE_DIR/weekly_status"
HEARTBEAT="$STATE_DIR/weekly_heartbeat"
LOCK="$STATE_DIR/weekly.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

# One anchor per Sunday. A second copy racing the first would email twice and
# write the archive twice, and the reader could not tell which they had.
exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another weekly run holds the lock"
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

ARGS=()
[[ -n "${CHESTER_WEEK_ENDING:-}" ]] && ARGS+=(--week-ending "$CHESTER_WEEK_ENDING")
[[ -n "${CHESTER_WEEKLY_DRY_RUN:-}" ]] && ARGS+=(--dry-run)
[[ -n "${CHESTER_WEEKLY_NO_FETCH:-}" ]] && ARGS+=(--no-fetch)

log "=== weekly tactical start sha=$SHA pull=$PULL_STATUS ${ARGS[*]:-live}"
START=$(date +%s)
"$PY" -m daily_cascade.weekly_report "${ARGS[@]}" >>"$LOG" 2>&1
RC=$?
ELAPSED=$(( $(date +%s) - START ))

case $RC in
    0) STATE=ok;            MSG="anchor built and delivered" ;;
    1) STATE=no_payload;    MSG="NO PAYLOAD -- the week could not be resolved" ;;
    2) STATE=not_delivered; MSG="built and ARCHIVED but delivery failed -- the report is on disk" ;;
    3) STATE=dry_run;       MSG="built and archived (dry run)" ;;
    *) STATE=error;         MSG="weekly report failed rc=$RC" ;;
esac
log "$MSG (rc=$RC, ${ELAPSED}s)"

printf 'state=%s rc=%s sha=%s pull=%s elapsed=%s at=%s\n' \
    "$STATE" "$RC" "$SHA" "$PULL_STATUS" "$ELAPSED" "$(date --iso-8601=seconds)" \
    >"$STATUS"

# THE HEARTBEAT IS WRITTEN ONLY ON A RUN THAT PRODUCED A REPORT. A delivery
# failure still produced one (the archive is on disk), so rc=2 counts; rc=1 did
# not, and stamping the heartbeat for it would let a broken week look current.
if [[ "$RC" -eq 0 || "$RC" -eq 2 || "$RC" -eq 3 ]]; then
    printf '%s sha=%s rc=%s at=%s\n' "$STATE" "$SHA" "$RC" \
        "$(date --iso-8601=seconds)" >"$HEARTBEAT"
fi

exit $RC
