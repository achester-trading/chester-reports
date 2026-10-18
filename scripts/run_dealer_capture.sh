#!/usr/bin/env bash
#
# The intraday dealer captures, 09:45 and 12:30 ET, as the VPS runs them (6b
# part 2; brief v2, Captures). One wrapper, the slot as its argument:
#
#   scripts/run_dealer_capture.sh 0945
#   scripts/run_dealer_capture.sh 1230     # the capture, then the 12:30 gates
#   scripts/run_dealer_capture.sh chains   # 16:31: the vendor chains only (M-3)
#
#   git pull --ff-only -> calendar guard -> python -m altdata.dealer_capture
#     run --slot <slot> -> status and heartbeat
#
# The same shape as run_eod_cron.sh: the box runs code it pulls and never edits
# it; on a non-session day it logs a skip and exits 0 having touched nothing.
# Its own lock, so it never waits on the EOD pass and the EOD pass never waits
# on it (the two never overlap in time: 09:45 and 12:30 against 16:10).
#
# Overridable environment: CHESTER_REPO, CHESTER_LOG_DIR, CHESTER_STATE_DIR,
# CHESTER_PYTHON, CHESTER_SESSION_DATE, CHESTER_FORCE_RUN=1 (as run_eod_cron.sh).
#
# Exit codes: altdata.dealer_capture's -- 0 a capture computed, 1 nothing
# computed; 2 a bad slot argument.
set -uo pipefail

SLOT="${1:-}"
case "$SLOT" in
    0945|1230|chains) ;;
    *) echo "usage: $0 0945|1230|chains" >&2; exit 2 ;;
esac

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/dealer_capture-$(date +%Y-%m).log"
HEARTBEAT="$STATE_DIR/dealer_capture_${SLOT}_heartbeat"
STATUS="$STATE_DIR/dealer_capture_${SLOT}_status"
LOCK="$STATE_DIR/dealer_capture.lock"

log() { printf '%s [%s] %s\n' "$(date --iso-8601=seconds)" "$SLOT" "$*" >>"$LOG"; }

exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another capture holds the lock ($LOCK)"
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
if [[ "$SLOT" == "chains" ]]; then
    # M-3 (18 Oct 2026): SPX and SPCX at 16:31 ET, the 16:16 data.
    "$VENV_PY" -m altdata.vendor_chains run >>"$LOG" 2>&1
else
    "$VENV_PY" -m altdata.dealer_capture run --slot "$SLOT" >>"$LOG" 2>&1
fi
RC=$?
if [[ "$SLOT" == "0945" || "$SLOT" == "1230" ]]; then
    # F-1 (18 Oct 2026): the vendor's summary and levels for SPY, QQQ and SPX at
    # this slot, inside its 60-a-day budget. Never fatal: its exit code is logged
    # and the capture's stands.
    "$VENV_PY" -m altdata.sources.flashalpha pull --slot "$SLOT" >>"$LOG" 2>&1 \
        || log "vendor pull at $SLOT returned rc=$? (never fatal)"
fi
ELAPSED=$(( $(date +%s) - START_EPOCH ))
log "run end rc=$RC elapsed=${ELAPSED}s sha=$SHA pull=$PULL_STATUS"
printf 'rc=%s sha=%s pull=%s elapsed=%s at=%s\n' \
    "$RC" "$SHA" "$PULL_STATUS" "$ELAPSED" "$(date --iso-8601=seconds)" >"$STATUS"
if [[ $RC -eq 0 ]]; then
    printf 'ok sha=%s elapsed=%s at=%s\n' "$SHA" "$ELAPSED" "$(date --iso-8601=seconds)" >"$HEARTBEAT"
fi
exit $RC
