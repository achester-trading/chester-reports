#!/usr/bin/env bash
#
# Portfolio Truth sync, as a VPS timer will run it.
#
# Read-only IBKR account state into the observation store. Architecture 26.11
# Gate 1: no order capability anywhere in the path.
#
# Modelled on run_eod_cron.sh -- same lock, same log-per-month, same pull-then-
# run shape -- but WITHOUT a heartbeat. A missed portfolio sync is not like a
# missed chain capture: broker state can be re-read at any time, so nothing is
# lost by skipping one and there is no irreplaceable asset to alarm about.
#
# EXIT CODES ARE THE POINT. Each maps to a different fix, so alerting can say
# what to do without anyone reading a log:
#   0 ok
#   3 Gateway not running        -> start IB Gateway
#   4 Gateway not responding     -> API not enabled, clientId clash, or a dialog
#   5 not authenticated          -> Gateway is up and SIGNED OUT
#   6 other IBKR API error       -> read the log
#   1 environment problem        -> no repo, no venv
#
# Overridable:
#   CHESTER_REPO      repo checkout        (~/chester-reports)
#   CHESTER_LOG_DIR   log directory        (~/logs)
#   CHESTER_STATE_DIR lock directory       (~/.chester)
#   CHESTER_PYTHON    interpreter          ($REPO/.venv/bin/python)
#   IBKR_HOST/IBKR_PORT/IBKR_CLIENT_ID     (127.0.0.1 / 4002 / 17)
#
# 4002 is Gateway PAPER. The port is the mode; the sync refuses a live port
# unless --allow-live is passed, which this wrapper deliberately never does.

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
HOST="${IBKR_HOST:-127.0.0.1}"
PORT="${IBKR_PORT:-4002}"
CLIENT_ID="${IBKR_CLIENT_ID:-17}"

mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/ibkr_sync-$(date +%Y-%m).log"
LOCK="$STATE_DIR/ibkr_sync.lock"
# A verdict a monitor can read without grepping a log. The unit declares
# SuccessExitStatus=0 3 4 5 6 -- deliberately, since none of those is a systemd
# failure -- which means `systemctl status` shows GREEN on a failed sync. The
# log line alone is therefore not enough to keep a gap visible: something has
# to hold the last outcome where a check can find it.
STATUS="$STATE_DIR/ibkr_sync_status"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

# One client id, one connection. Two overlapping syncs would collide on the
# clientId and the second would fail as "not responding", which is a confusing
# way to learn that the first is still running.
exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another sync holds the lock ($LOCK)"
    exit 0
fi

if [[ ! -d "$REPO/.git" ]]; then
    log "FATAL no git checkout at $REPO"
    exit 1
fi
cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }

PULL_STATUS=ok
git pull --ff-only >>"$LOG" 2>&1 || PULL_STATUS=failed
SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
    log "FATAL no interpreter at $PY"
    exit 1
fi

log "=== sync start sha=$SHA pull=$PULL_STATUS target=$HOST:$PORT client=$CLIENT_ID"
"$PY" -m altdata.sources.ibkr_portfolio \
    --host "$HOST" --port "$PORT" --client-id "$CLIENT_ID" >>"$LOG" 2>&1
RC=$?

case $RC in
    0) STATE=ok;              MSG="sync ok" ;;
    3) STATE=not_listening;   MSG="GATEWAY NOT RUNNING -- start IB Gateway on $HOST:$PORT" ;;
    4) STATE=not_responding;  MSG="GATEWAY NOT RESPONDING -- API disabled, clientId $CLIENT_ID in use, or a dialog is blocking" ;;
    5) STATE=signed_out;      MSG="NOT AUTHENTICATED -- Gateway is running and signed out" ;;
    *) STATE=api_error;       MSG="IBKR error rc=$RC" ;;
esac
log "$MSG"

# Same state vocabulary the watchdog writes to ~/.chester/ibgateway_health, so
# the two agree on what a failure is called as well as on what one is.
printf 'state=%s rc=%s sha=%s at=%s
'     "$STATE" "$RC" "$SHA" "$(date --iso-8601=seconds)" >"$STATUS"

# last_success is only ever touched on a clean sync, so the AGE of this file is
# how long the portfolio series has had a hole in it -- visible without reading
# a month of log.
if [[ $RC -eq 0 ]]; then
    printf 'state=ok rc=0 sha=%s at=%s
' "$SHA" "$(date --iso-8601=seconds)"         >"$STATE_DIR/ibkr_sync_last_success"
fi
exit $RC
