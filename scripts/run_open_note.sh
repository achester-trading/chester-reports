#!/usr/bin/env bash
#
# The open note, 09:50 ET every trading day (docs/change-order-secondary-notes-
# 2026-10-19.md, ruled 19 Oct 2026). One wrapper, two steps:
#
#   git pull --ff-only -> calendar guard (today a session) ->
#     python -m altdata.note_fetch open      (the fetch: writes the store only)
#     python -m daily_cascade.open_note      (the note: reads the store only;
#                                             waits a bounded time for the 09:45
#                                             capture, then "09:45 capture pending")
#   -> status and heartbeat
#
# run_dealer_capture.sh's shape. Its own lock. Before `live_from` (config
# secondary_notes) the note itself makes every run a dry run: archived under
# dryrun/ and mailed with "[DRY RUN]" in the subject.
#
# THE NOTE IS SECONDARY: a fault here is a WARNING on the heartbeat (a stale
# open_note_heartbeat), never a failed unit -- so the wrapper exits 0 after a
# soft failure and the status file carries the step's rc.
#
# Overridable environment: CHESTER_REPO, CHESTER_LOG_DIR, CHESTER_STATE_DIR,
# CHESTER_PYTHON, CHESTER_SESSION_DATE, CHESTER_FORCE_RUN=1 (as run_eod_cron.sh).
set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/open_note-$(date +%Y-%m).log"
HEARTBEAT="$STATE_DIR/open_note_heartbeat"
STATUS="$STATE_DIR/open_note_status"
LOCK="$STATE_DIR/open_note.lock"

log() { printf '%s [open_note] %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another open note holds the lock ($LOCK)"
    exit 0
fi
log "=== run start"
cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }
PULL_STATUS=ok
if ! git pull --ff-only >>"$LOG" 2>&1; then
    PULL_STATUS=failed
    log "ERROR git pull --ff-only failed -- running on the checked-out code anyway"
fi
SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
VENV_PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$VENV_PY" ]]; then
    log "FATAL no venv interpreter at $VENV_PY"
    printf 'fatal=no_venv sha=%s at=%s\n' "$SHA" "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi

SESSION_ARG="${CHESTER_SESSION_DATE:-}"
GUARD_LINE="$("$VENV_PY" -m altdata.session is-session ${SESSION_ARG:+"$SESSION_ARG"} 2>&1)"
GUARD_RC=$?
if [[ $GUARD_RC -eq 1 && "${CHESTER_FORCE_RUN:-}" != "1" ]]; then
    log "SKIP non_session -- $GUARD_LINE (heartbeat and status untouched)"
    exit 0
fi
log "calendar rc=$GUARD_RC -- $GUARD_LINE"

START_EPOCH=$(date +%s)
"$VENV_PY" -m altdata.note_fetch open ${SESSION_ARG:+--date "$SESSION_ARG"} >>"$LOG" 2>&1
FETCH_RC=$?
[[ $FETCH_RC -eq 0 ]] || log "WARN the fetch returned rc=$FETCH_RC (no bars written); the note names each absence"
"$VENV_PY" -m daily_cascade.open_note ${SESSION_ARG:+--date "$SESSION_ARG"} >>"$LOG" 2>&1
RC=$?
ELAPSED=$(( $(date +%s) - START_EPOCH ))
log "run end rc=$RC fetch_rc=$FETCH_RC elapsed=${ELAPSED}s sha=$SHA pull=$PULL_STATUS"
printf 'rc=%s fetch_rc=%s sha=%s pull=%s elapsed=%s at=%s\n' \
    "$RC" "$FETCH_RC" "$SHA" "$PULL_STATUS" "$ELAPSED" "$(date --iso-8601=seconds)" >"$STATUS"
if [[ $RC -eq 0 ]]; then
    printf 'ok sha=%s elapsed=%s at=%s\n' "$SHA" "$ELAPSED" "$(date --iso-8601=seconds)" >"$HEARTBEAT"
else
    log "WARN the note returned rc=$RC: secondary, so the unit exits 0 and the heartbeat warns"
fi
exit 0
