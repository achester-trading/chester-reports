#!/usr/bin/env bash
#
# The Alpha Lab's weekly loop (X-1.7, X-1.10), as chester-alpha-weekly.timer runs
# it: Sunday 06:00 ET, after the Weekly's 05:00 run (its TimeoutStartSec is 15
# minutes). In Tranche 1 it applies the nightly loop's proposed allocator weights
# -- the rebalance, never by hand. It reads and writes alpha.db only.
#
#   git pull --ff-only -> venv alpha.loops.weekly -> log -> status
#
# No calendar guard: Sunday is never a session, and the rebalance is the week's,
# not a session's.
#
# Overridable: CHESTER_REPO, CHESTER_LOG_DIR, CHESTER_STATE_DIR, CHESTER_PYTHON.

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"

mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/alpha_weekly-$(date +%Y-%m).log"
STATUS="$STATE_DIR/alpha_weekly_status"
LOCK="$STATE_DIR/alpha_weekly.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another weekly loop holds the lock"
    exit 0
fi

if [[ ! -d "$REPO/.git" ]]; then
    log "FATAL no git checkout at $REPO"
    printf 'state=no_repo at=%s\n' "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi
cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }

git pull --ff-only >>"$LOG" 2>&1 || log "WARN git pull --ff-only failed; running the checkout as it is"
SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
    log "FATAL no interpreter at $PY"
    printf 'state=no_venv sha=%s at=%s\n' "$SHA" "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi

log "=== alpha weekly start sha=$SHA"
"$PY" -m alpha.loops.weekly >>"$LOG" 2>&1
RC=$?
STATE=ok
[[ $RC -ne 0 ]] && STATE=failed
printf 'state=%s rc=%s sha=%s at=%s\n' "$STATE" "$RC" "$SHA" \
    "$(date --iso-8601=seconds)" >"$STATUS"
log "=== alpha weekly end rc=$RC"
exit "$RC"
