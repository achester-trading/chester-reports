#!/usr/bin/env bash
# run_prices_saturday.sh -- the Saturday price pull (weekly-fixes-7 item 9, 17 Oct
# 2026), Saturdays at 06:00 ET under chester-prices-saturday.service.
#
#   git pull --ff-only -> python -m altdata.feeds pull --only prices
#
# Why: a continuous symbol's daily bar (BTC, the FX crosses) is stored only once
# its UTC day has ended, so no weekday pull stores Friday's; this one does, before
# the Sunday Weekly reads it. Reports never fetch: they read what this stored.
set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/prices-saturday-$(date +%Y-%m).log"
LOCK="$STATE_DIR/prices-saturday.lock"
log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another Saturday price run holds the lock"
    exit 0
fi
cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }
git pull --ff-only >>"$LOG" 2>&1 || log "WARN git pull --ff-only failed -- running on the checked-out code"
PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
    log "FATAL no interpreter at $PY"
    exit 1
fi

log "Saturday price pull at $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
"$PY" -m altdata.feeds pull --only prices >>"$LOG" 2>&1
rc=$?
[[ $rc -ne 0 ]] && log "WARN the price pull exited $rc"
log "Saturday price pull: done"
exit $rc
