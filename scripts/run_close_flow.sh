#!/usr/bin/env bash
#
# The 15:00 pass: the levered-ETF close-flow estimate (signal-triage Batch 22 item
# 116, the order's 98.1; A127, 6 Nov 2026). Trading days only.
#
# ONE CALL: `python -m altdata.close_flow estimate --slot 1500`, which re-reads
# the AUM writers (ProShares' NAV files, the other issuers' pages), reads each
# underlying's 15:00 bar, stores calc.close_flow.* (instrument 1500) and prints
# the flag line. NON-FATAL: a failed estimate is logged and the wrapper exits 0,
# so nothing downstream waits on it; the 16:45 close computes its own estimate.
# Report and alert only: nothing here enters a composite, the market-state object
# or a regime, and nothing is sent.
#
# Shaped like the other wrappers: lock, git pull, calendar guard, venv, log, status.

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
mkdir -p "$LOG_DIR" "$STATE_DIR"

LOG="$LOG_DIR/close_flow-$(date +%Y-%m).log"
STATUS="$STATE_DIR/close_flow_status"
LOCK="$STATE_DIR/close_flow.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another close-flow run holds the lock"
    exit 0
fi

cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }

if git pull --ff-only >>"$LOG" 2>&1; then PULL_STATUS=ok; else PULL_STATUS=failed; fi
SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
[[ -x "$PY" ]] || { log "FATAL no interpreter at $PY"; exit 1; }

GUARD_LINE="$("$PY" -m altdata.session is-session 2>&1)"
case $? in
    0) log "calendar ok -- $GUARD_LINE" ;;
    1) log "SKIP non_session -- $GUARD_LINE"; exit 0 ;;
    *) log "WARN calendar guard unusable ($GUARD_LINE) -- estimating anyway" ;;
esac

log "=== close-flow 15:00 start sha=$SHA pull=$PULL_STATUS"
START=$(date +%s)
OUT="$("$PY" -m altdata.close_flow estimate --slot 1500 2>&1)"
RC=$?
ELAPSED=$(( $(date +%s) - START ))
printf '%s\n' "$OUT" | sed 's/^/  /' >>"$LOG"
log "run end rc=$RC elapsed=${ELAPSED}s"

printf 'rc=%s sha=%s elapsed=%s at=%s\n' \
    "$RC" "$SHA" "$ELAPSED" "$(date --iso-8601=seconds)" >"$STATUS"

# Non-fatal by design: the estimate's absence is in the log and the status file,
# and the close prints "the 15:00 close-flow estimate" as not stored.
exit 0
