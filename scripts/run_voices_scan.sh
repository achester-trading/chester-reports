#!/usr/bin/env bash
# run_voices_scan.sh -- the daily voices scan, on its own timer (PB-1, 5 Oct 2026).
#
# Until PB-1 the scan ran inside the 06:45 overnight pass and shared its
# ten-minute unit limit with the price fetch, the events ingest and the
# surprises; on 5 Oct its 240-second budget ran out before the last five
# sources. It now runs at 06:15 ET under chester-voices.service with a
# fifteen-minute budget of its own (config/voices_sources.yaml), and finishes
# before the 06:45 pass starts. Reports never fetch: they read what this stored.
#
# Order: the idempotent seed, then the scan (which also resolves the 13F filers).
# A failure is logged, never fatal to anything else: the reports print each
# unreachable source by name.
set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/voices-$(date +%Y-%m).log"
LOCK="$STATE_DIR/voices.lock"
log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another voices scan holds the lock"
    exit 0
fi
cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }
PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
    log "FATAL no interpreter at $PY"
    exit 1
fi

log "voices: seed and scan at $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
OUT="$( { "$PY" -m altdata.voices seed && "$PY" -m altdata.sources.voices_scan run; } 2>&1 )"
RC=$?
printf '%s\n' "$OUT" | grep -v '^INFO ' | sed 's/^/  /' >>"$LOG"
[[ $RC -ne 0 ]] && log "WARN voices scan exited $RC"
log "voices: done"
exit 0
