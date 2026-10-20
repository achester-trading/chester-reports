#!/usr/bin/env bash
# run_flashalpha.sh -- the FlashAlpha vendor writer, 16:25 ET on weekdays (6b part 3,
# 17 Oct 2026), under chester-flashalpha.service.
#
# One pull of the vendor's dealer readings for config/flashalpha.yaml's symbols,
# stored point in time as dealer.vendor_*. Quota-guarded by the writer itself; the
# key is read through altdata.secrets and never printed. A failure is logged, never
# fatal to anything else: the Weekly's vendor line says what is absent.
set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/flashalpha-$(date +%Y-%m).log"
LOCK="$STATE_DIR/flashalpha.lock"
log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another vendor pull holds the lock"
    exit 0
fi
cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }
PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
    log "FATAL no interpreter at $PY"
    exit 1
fi

log "flashalpha: pull at $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
OUT="$("$PY" -m altdata.sources.flashalpha pull 2>&1)"
RC=$?
printf '%s\n' "$OUT" | sed 's/^/  /' >>"$LOG"
[[ $RC -ne 0 ]] && log "WARN vendor pull exited $RC"
exit 0
