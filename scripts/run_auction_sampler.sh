#!/usr/bin/env bash
#
# The closing-auction sampler's wrapper. 15:49 ET, trading days only.
#
# Shaped like the other wrappers: git pull, calendar guard, venv, log, status. The
# differences are the two this unit cannot share:
#
#   NO CATCH-UP AND NO RETRY. An auction happens once. A run that starts late has
#   nothing to sample and a retry has less, so the wrapper reports and exits rather
#   than trying again.
#
#   IT REFUSES TO RUN UNTIL A PROBE SAYS ENTITLED. The auction feed is a paid
#   subscription and the failure mode without that check is the bad one: the request
#   succeeds, no tick ever arrives, and an empty row is written every thirty seconds
#   forever while the unit looks healthy. altdata/loggers/auction.py holds the
#   stored probe result and makes that call; this wrapper just reports it.

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
mkdir -p "$LOG_DIR" "$STATE_DIR"

LOG="$LOG_DIR/auction_sampler-$(date +%Y-%m).log"
STATUS="$STATE_DIR/auction_status"
LOCK="$STATE_DIR/auction.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another sampler holds the lock"
    exit 0
fi

cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }

# A pull, like every other wrapper: the calendar table and the event classes are
# code, and a stale checkout would sample with last month's holiday list.
if git pull --ff-only >>"$LOG" 2>&1; then PULL_STATUS=ok; else PULL_STATUS=failed; fi
SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
[[ -x "$PY" ]] || { log "FATAL no interpreter at $PY"; exit 1; }

# The same calendar guard every wrapper uses, reading the same table.
GUARD_LINE="$("$PY" -m altdata.session is-session 2>&1)"
case $? in
    0) log "calendar ok -- $GUARD_LINE" ;;
    1) log "SKIP non_session -- $GUARD_LINE"; exit 0 ;;
    *) log "WARN calendar guard unusable ($GUARD_LINE) -- sampling anyway" ;;
esac

CLASSES="$("$PY" -c 'from altdata import session; print(",".join(session.auction_event_classes()) or "NONE")' 2>/dev/null || echo unknown)"
log "=== auction sampler start sha=$SHA pull=$PULL_STATUS classes=$CLASSES"

START=$(date +%s)
OUT="$("$PY" -m altdata.loggers.auction sample 2>&1)"
RC=$?
ELAPSED=$(( $(date +%s) - START ))
printf '%s\n' "$OUT" | sed 's/^/  /' >>"$LOG"
log "run end rc=$RC elapsed=${ELAPSED}s"

printf 'rc=%s sha=%s classes=%s elapsed=%s at=%s\n' \
    "$RC" "$SHA" "$CLASSES" "$ELAPSED" "$(date --iso-8601=seconds)" >"$STATUS"

printf '%s\n' "$OUT"
exit $RC
