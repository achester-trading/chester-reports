#!/usr/bin/env bash
#
# The 07:00 ET morning anchor, as the VPS timer runs it.
#
#   git pull --ff-only -> calendar guard -> venv morning_anchor -> heartbeat
#
# FETCHES NOTHING (30.4). scripts/fetch_overnight.sh ran at 06:45 and wrote the
# store; this reads it. A failure here is therefore a report-layer failure and
# nothing else -- the same property that made the 16:45 close run the first
# cascade slot built.
#
# THIS ONE HAS A HEARTBEAT, AND THE CLOSE REPORT DOES NOT.
#
# The close report writes none, on the reasoning that a missed report is not a
# missed capture: its inputs are already stored and it can be regenerated for any
# past session with --session. That reasoning is sound and it does not transfer
# here. The morning anchor reads the OVERNIGHT fetch, which is a live market read
# with no second chance -- by 09:30 the levels it would have captured are gone,
# and no --session will bring back what 06:45 did not store. A 07:00 that silently
# stops running loses a session's pre-open read every day until somebody notices,
# and "somebody notices a report stopped arriving" is exactly the monitoring this
# system does not want to depend on.
#
# So: heartbeat written ONLY on a clean run, and check_heartbeat.sh treats a
# missed 07:00 as non-healthy (exit 5). A degraded report -- one that published
# with an absent or stale overnight block -- still touches the heartbeat, because
# the RUN happened; what it published is the report's own business and the state
# row carries it. The heartbeat answers "did the 07:00 run", not "was the market
# data any good".
#
# Exit codes are morning_anchor.py's, passed through:
#   0 report built (and delivered, or dry-run)
#   1 every block empty -- nothing to say; heartbeat NOT touched
#   2 built and archived but DELIVERY FAILED -- the report exists on disk
#
# Overridable:
#   CHESTER_REPO / CHESTER_LOG_DIR / CHESTER_STATE_DIR / CHESTER_PYTHON
#   CHESTER_SESSION_DATE       evaluate the guard against this ET date
#   CHESTER_FORCE_RUN=1        run even on a non-session day
#   CHESTER_MORNING_DRY_RUN=1  build and archive, send nothing

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"

mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/morning_anchor-$(date +%Y-%m).log"
STATUS="$STATE_DIR/morning_anchor_status"
HEARTBEAT="$STATE_DIR/morning_heartbeat"
LOCK="$STATE_DIR/morning_anchor.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

# One report per morning. A second copy racing the first would email twice and
# the reader would have no way to tell which is which.
exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another morning anchor holds the lock"
    exit 0
fi

if [[ ! -d "$REPO/.git" ]]; then
    log "FATAL no git checkout at $REPO"
    printf 'state=no_repo at=%s\n' "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi
cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }

PULL_STATUS=ok
git pull --ff-only >>"$LOG" 2>&1 || PULL_STATUS=failed
SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
    log "FATAL no interpreter at $PY"
    printf 'state=no_venv sha=%s at=%s\n' "$SHA" "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi

# --- the calendar guard ---------------------------------------------------
# On a holiday there is no open to anchor, and a report that arrived anyway
# would show the previous session's numbers under today's date -- worse than no
# report, because it is a report that looks fine. Status untouched on a skip, so
# a quiet Monday cannot erase a Friday failure. Fails OPEN.
SESSION_ARG="${CHESTER_SESSION_DATE:-}"
GUARD_LINE="$("$PY" -m altdata.session is-session ${SESSION_ARG:+"$SESSION_ARG"} 2>&1)"
GUARD_RC=$?

case $GUARD_RC in
    0) log "calendar ok -- $GUARD_LINE" ;;
    1)
        if [[ "${CHESTER_FORCE_RUN:-}" == "1" ]]; then
            log "non_session but CHESTER_FORCE_RUN=1 -- running anyway ($GUARD_LINE)"
        else
            log "SKIP non_session -- $GUARD_LINE (status and heartbeat untouched)"
            exit 0
        fi
        ;;
    *) log "WARN calendar guard unusable (rc=$GUARD_RC: $GUARD_LINE) -- running anyway" ;;
esac

DRY=""
[[ "${CHESTER_MORNING_DRY_RUN:-0}" == "1" ]] && DRY="--dry-run"

log "=== morning anchor start sha=$SHA pull=$PULL_STATUS ${DRY:-live}"
"$PY" -m daily_cascade.morning_anchor $DRY >>"$LOG" 2>&1
RC=$?

case $RC in
    0) STATE=ok;            MSG="report built and delivered" ;;
    1) STATE=no_payload;    MSG="EVERY BLOCK EMPTY -- check the 06:45 fetch and the prior EOD pass" ;;
    2) STATE=not_delivered; MSG="built and ARCHIVED but delivery failed -- the report is on disk" ;;
    *) STATE=error;         MSG="morning anchor failed rc=$RC" ;;
esac
log "$MSG"

printf 'state=%s rc=%s sha=%s at=%s\n' \
    "$STATE" "$RC" "$SHA" "$(date --iso-8601=seconds)" >"$STATUS"

# THE HEARTBEAT, ON 0 AND 2 ONLY.
#
# 2 counts: the report was built and archived and only the mail failed, so the
# 07:00 slot did its job and the delivery channel is a separate alarm. 1 does
# NOT: every block was empty, which means the chain in front of this produced
# nothing and a warm heartbeat would assert a working morning read that does not
# exist. That is the case this heartbeat is for.
if [[ $RC -eq 0 ]] || [[ $RC -eq 2 ]]; then
    printf 'state=%s rc=%s sha=%s at=%s\n' \
        "$STATE" "$RC" "$SHA" "$(date --iso-8601=seconds)" >"$HEARTBEAT"
    log "heartbeat touched"
else
    log "heartbeat NOT touched (rc=$RC) -- the 07:00 read did not happen"
fi

exit $RC
