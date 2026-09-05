#!/usr/bin/env bash
#
# EOD options pass, as the VPS runs it.
#
# Part 25 ruling: the VPS runs code, it never edits code. So this script pulls
# before every run and the box holds no local commits. Everything it needs is
# either in the repo or passed in through the environment.
#
#   git pull --ff-only  ->  venv run_eod.py  ->  append log  ->  touch heartbeat
#
# Overridable environment (defaults suit a stock Ubuntu box):
#   CHESTER_REPO         repo checkout            (~/chester-reports)
#   CHESTER_LOG_DIR      log directory            (~/logs)
#   CHESTER_STATE_DIR    heartbeat/status dir     (~/.chester)
#   CHESTER_BACKUP_DIR   chain backup target      (~/backups/chains)
#   CHESTER_CLOSE_SOURCE pin-log close label      (eod_systemd_1610ET)
#
# Exit codes are run_eod.py's, passed through unchanged:
#   0 ok · 1 no chains captured · 2 compute failed · 3 pin scoring failed
#   4 ran fine but the off-box backup failed
#
# The heartbeat is touched ONLY on exit 0. Exit 4 means the irreplaceable data
# was captured but has one copy, which is not a healthy run.

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

VENV_PY="$REPO/.venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
    log "FATAL no venv interpreter at $VENV_PY"
    printf 'fatal=no_venv sha=%s at=%s\n' "$SHA" "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi

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
