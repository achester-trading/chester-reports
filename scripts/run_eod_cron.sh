#!/usr/bin/env bash
#
# EOD options pass, as the VPS runs it.
#
# Part 25 ruling: the VPS runs code, it never edits code. So this script pulls
# before every run and the box holds no local commits. Everything it needs is
# either in the repo or passed in through the environment.
#
#   git pull --ff-only  ->  calendar guard  ->  venv run_eod.py  ->  append log
#                                                              ->  touch heartbeat
#
# THE CALENDAR GUARD. The systemd timer says Mon-Fri, which handles weekends
# and knows nothing about Labor Day. On a market holiday the old behaviour was
# to run anyway: fetch a chain that has not moved since the previous close,
# file it under the holiday's date, and leave a record of a session that never
# happened. The guard asks altdata.session -- the same table check_heartbeat.sh
# reads, so the two can never disagree -- and on a non-session day it logs a
# "non_session skip" line and exits 0 having touched nothing. Exit 0 and an
# untouched heartbeat is the point: a skipped holiday must look to the checker
# exactly like a Saturday, not like a failure and not like a healthy run.
#
# Overridable environment (defaults suit a stock Ubuntu box):
#   CHESTER_REPO         repo checkout            (~/chester-reports)
#   CHESTER_LOG_DIR      log directory            (~/logs)
#   CHESTER_STATE_DIR    heartbeat/status dir     (~/.chester)
#   CHESTER_BACKUP_DIR   chain backup target      (~/backups/chains)
#   CHESTER_CLOSE_SOURCE pin-log close label      (eod_systemd_1610ET)
#   CHESTER_SESSION_DATE evaluate the guard against this ET date instead of
#                        today (YYYY-MM-DD). For testing the guard and for
#                        deliberate manual reruns; the timer never sets it.
#   CHESTER_FORCE_RUN=1  run even on a non-session day, logging that it did
#   CHESTER_PYTHON       interpreter to use    ($REPO/.venv/bin/python)
#
# Exit codes are run_eod.py's, passed through unchanged:
#   0 ok · 1 no chains captured · 2 compute failed · 3 pin scoring failed
#   4 ran fine but the off-box backup failed
#
# A non-session skip also exits 0 -- it is not an error, and nothing downstream
# should page about a closed market.
#
# The heartbeat is touched ONLY on exit 0 of an actual run. Exit 4 means the
# irreplaceable data was captured but has one copy, which is not a healthy run.

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
export CHESTER_BACKUP_DIR="${CHESTER_BACKUP_DIR:-$HOME/backups/chains}"
CLOSE_SOURCE="${CHESTER_CLOSE_SOURCE:-eod_systemd_1610ET}"

mkdir -p "$LOG_DIR" "$STATE_DIR" "$CHESTER_BACKUP_DIR"

# One log file per month: appending forever makes a file nobody will ever read,
# and rotating daily makes a directory nobody will ever grep.
LOG="$LOG_DIR/run_eod-$(date +%Y-%m).log"
HEARTBEAT="$STATE_DIR/eod_heartbeat"
STATUS="$STATE_DIR/eod_status"
LOCK="$STATE_DIR/eod.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

# Never let two runs overlap. A slow fetch that outlives its window would
# otherwise have a second run writing the same chain files underneath it.
exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another run holds the lock ($LOCK)"
    exit 0
fi

log "=== run start (close_source=$CLOSE_SOURCE backup=$CHESTER_BACKUP_DIR)"

if [[ ! -d "$REPO/.git" ]]; then
    log "FATAL no git checkout at $REPO"
    printf 'fatal=no_repo at=%s\n' "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi
cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }

# Pull before running, per Part 25. A failed pull is logged loudly but does NOT
# abort: a missed capture is permanent (yfinance serves no history) while a run
# on slightly stale code is not. The SHA actually used is recorded either way,
# so a surprising result can always be traced to the code that produced it.
PULL_STATUS=ok
if ! git pull --ff-only >>"$LOG" 2>&1; then
    PULL_STATUS=failed
    log "ERROR git pull --ff-only failed -- running on the checked-out code anyway"
fi
SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
log "code sha=$SHA pull=$PULL_STATUS"

VENV_PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$VENV_PY" ]]; then
    log "FATAL no venv interpreter at $VENV_PY"
    printf 'fatal=no_venv sha=%s at=%s\n' "$SHA" "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi

# Trading-calendar guard. Deliberately placed AFTER the pull, so the box always
# decides with the freshest holiday table rather than the one it happened to
# have checked out -- adding a missed holiday is then a commit, not an SSH
# session, which is the whole of Part 25.
#
# Three outcomes, and the third is the one worth stating: if the guard itself
# cannot answer -- interpreter gone, import error, anything -- the run PROCEEDS.
# A wasted holiday fetch costs one stale chain; a guard bug that silences the
# pipeline costs sessions that yfinance will never serve again. The failure
# direction is chosen, not accidental.
SESSION_ARG="${CHESTER_SESSION_DATE:-}"
GUARD_LINE="$("$VENV_PY" -m altdata.session is-session ${SESSION_ARG:+"$SESSION_ARG"} 2>&1)"
GUARD_RC=$?

case $GUARD_RC in
    0)
        log "calendar ok -- $GUARD_LINE"
        ;;
    1)
        if [[ "${CHESTER_FORCE_RUN:-}" == "1" ]]; then
            log "non_session but CHESTER_FORCE_RUN=1 -- running anyway ($GUARD_LINE)"
        else
            # Touch neither the heartbeat nor the status file. The heartbeat
            # keeps the age of the last real session, which is what the checker
            # measures against its holiday-aware allowance; the status file
            # keeps the last real run's verdict, so a Friday failure is still
            # visible on Tuesday instead of being erased by a quiet Monday.
            log "SKIP non_session -- $GUARD_LINE (heartbeat and status untouched)"
            exit 0
        fi
        ;;
    *)
        log "WARN calendar guard unusable (rc=$GUARD_RC: $GUARD_LINE) -- running anyway"
        ;;
esac

START_EPOCH=$(date +%s)
"$VENV_PY" run_eod.py --close-source "$CLOSE_SOURCE" >>"$LOG" 2>&1
RC=$?
ELAPSED=$(( $(date +%s) - START_EPOCH ))

log "run end rc=$RC elapsed=${ELAPSED}s"
printf 'rc=%s sha=%s pull=%s elapsed=%s at=%s\n' \
    "$RC" "$SHA" "$PULL_STATUS" "$ELAPSED" "$(date --iso-8601=seconds)" >"$STATUS"

if [[ $RC -eq 0 ]]; then
    # Heartbeat content is the evidence; its mtime is what the checker reads.
    printf 'ok sha=%s pull=%s elapsed=%s at=%s\n' \
        "$SHA" "$PULL_STATUS" "$ELAPSED" "$(date --iso-8601=seconds)" >"$HEARTBEAT"
    log "heartbeat touched"
else
    log "heartbeat NOT touched (rc=$RC)"
fi

exit $RC
