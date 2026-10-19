#!/usr/bin/env bash
# run_meme_ingest.sh -- chester-meme's packets in, as Book D drafts, at 21:45 ET
# (meme-ingest-ledgers-1, 17 Oct 2026), under chester-meme-ingest.service.
#
#   git pull --ff-only -> python -m altdata.meme_ingest
#
# After the meme's 19:30 evening scan (done by about 19:45; the contract reads
# after 20:15). The 06:45 overnight pass runs the same ingest for the morning
# scan. Reads $CHESTER_MEME_DROP (else ~/chester-meme/drop) and never writes into
# it; writes drafts only, never a register decision. A packet seen twice writes
# nothing, so the two passes cannot double-count.
set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/meme-ingest-$(date +%Y-%m).log"
LOCK="$STATE_DIR/meme-ingest.lock"
log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another meme ingest holds the lock"
    exit 0
fi
cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }
git pull --ff-only >>"$LOG" 2>&1 || log "WARN git pull --ff-only failed -- running on the checked-out code"
PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
    log "FATAL no interpreter at $PY"
    exit 1
fi

log "meme ingest at $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
"$PY" -m altdata.meme_ingest >>"$LOG" 2>&1
rc=$?
[[ $rc -ne 0 ]] && log "WARN the meme ingest exited $rc"
log "meme ingest: done"
exit $rc
