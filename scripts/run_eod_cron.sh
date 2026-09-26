#!/usr/bin/env bash
#
# EOD options pass, as the VPS runs it.
#
# Part 25 ruling: the VPS runs code, it never edits code. So this script pulls
# before every run and the box holds no local commits. Everything it needs is
# either in the repo or passed in through the environment.
#
#   git pull --ff-only  ->  calendar guard  ->  venv run_eod.py  ->  append log
#                                                              ->  touch heartbeat
#
# THE CALENDAR GUARD. The systemd timer says Mon-Fri, which handles weekends
# and knows nothing about Labor Day. On a market holiday the old behaviour was
# to run anyway: fetch a chain that has not moved since the previous close,
# file it under the holiday's date, and leave a record of a session that never
# happened. The guard asks altdata.session -- the same table check_heartbeat.sh
# reads, so the two can never disagree -- and on a non-session day it logs a
# "non_session skip" line and exits 0 having touched nothing. Exit 0 and an
# untouched heartbeat is the point: a skipped holiday must look to the checker
# exactly like a Saturday, not like a failure and not like a healthy run.
#
# Overridable environment (defaults suit a stock Ubuntu box):
#   CHESTER_REPO         repo checkout            (~/chester-reports)
#   CHESTER_LOG_DIR      log directory            (~/logs)
#   CHESTER_STATE_DIR    heartbeat/status dir     (~/.chester)
#   CHESTER_BACKUP_DIR   chain backup target      (~/backups/chains)
#   CHESTER_CLOSE_SOURCE pin-log close label      (eod_systemd_1610ET)
#   CHESTER_SESSION_DATE evaluate the guard against this ET date instead of
#                        today (YYYY-MM-DD). For testing the guard and for
#                        deliberate manual reruns; the timer never sets it.
#   CHESTER_FORCE_RUN=1  run even on a non-session day, logging that it did
#   CHESTER_PYTHON       interpreter to use    ($REPO/.venv/bin/python)
#
# Exit codes are run_eod.py's, passed through unchanged:
#   0 ok · 1 no chains captured · 2 compute failed · 3 pin scoring failed
#   4 ran fine but the off-box backup failed
#
# A non-session skip also exits 0 -- it is not an error, and nothing downstream
# should page about a closed market.
#
# The heartbeat is touched ONLY on exit 0 of an actual run. Exit 4 means the
# irreplaceable data was captured but has one copy, which is not a healthy run.

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
export CHESTER_BACKUP_DIR="${CHESTER_BACKUP_DIR:-$HOME/backups/chains}"
CLOSE_SOURCE="${CHESTER_CLOSE_SOURCE:-eod_systemd_1610ET}"

mkdir -p "$LOG_DIR" "$STATE_DIR" "$CHESTER_BACKUP_DIR"

# One log file per month: appending forever makes a file nobody will ever read,
# and rotating daily makes a directory nobody will ever grep.
LOG="$LOG_DIR/run_eod-$(date +%Y-%m).log"
HEARTBEAT="$STATE_DIR/eod_heartbeat"
STATUS="$STATE_DIR/eod_status"
LOCK="$STATE_DIR/eod.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

# Never let two runs overlap. A slow fetch that outlives its window would
# otherwise have a second run writing the same chain files underneath it.
exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another run holds the lock ($LOCK)"
    exit 0
fi

log "=== run start (close_source=$CLOSE_SOURCE backup=$CHESTER_BACKUP_DIR)"

if [[ ! -d "$REPO/.git" ]]; then
    log "FATAL no git checkout at $REPO"
    printf 'fatal=no_repo at=%s\n' "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi
cd "$REPO" || { log "FATAL cannot cd $REPO"; exit 1; }

# Pull before running, per Part 25. A failed pull is logged loudly but does NOT
# abort: a missed capture is permanent (yfinance serves no history) while a run
# on slightly stale code is not. The SHA actually used is recorded either way,
# so a surprising result can always be traced to the code that produced it.
PULL_STATUS=ok
if ! git pull --ff-only >>"$LOG" 2>&1; then
    PULL_STATUS=failed
    log "ERROR git pull --ff-only failed -- running on the checked-out code anyway"
fi
SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
log "code sha=$SHA pull=$PULL_STATUS"

VENV_PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
if [[ ! -x "$VENV_PY" ]]; then
    log "FATAL no venv interpreter at $VENV_PY"
    printf 'fatal=no_venv sha=%s at=%s\n' "$SHA" "$(date --iso-8601=seconds)" >"$STATUS"
    exit 1
fi

# Trading-calendar guard. Deliberately placed AFTER the pull, so the box always
# decides with the freshest holiday table rather than the one it happened to
# have checked out -- adding a missed holiday is then a commit, not an SSH
# session, which is the whole of Part 25.
#
# Three outcomes, and the third is the one worth stating: if the guard itself
# cannot answer -- interpreter gone, import error, anything -- the run PROCEEDS.
# A wasted holiday fetch costs one stale chain; a guard bug that silences the
# pipeline costs sessions that yfinance will never serve again. The failure
# direction is chosen, not accidental.
SESSION_ARG="${CHESTER_SESSION_DATE:-}"
GUARD_LINE="$("$VENV_PY" -m altdata.session is-session ${SESSION_ARG:+"$SESSION_ARG"} 2>&1)"
GUARD_RC=$?

case $GUARD_RC in
    0)
        log "calendar ok -- $GUARD_LINE"
        ;;
    1)
        if [[ "${CHESTER_FORCE_RUN:-}" == "1" ]]; then
            log "non_session but CHESTER_FORCE_RUN=1 -- running anyway ($GUARD_LINE)"
        else
            # Touch neither the heartbeat nor the status file. The heartbeat
            # keeps the age of the last real session, which is what the checker
            # measures against its holiday-aware allowance; the status file
            # keeps the last real run's verdict, so a Friday failure is still
            # visible on Tuesday instead of being erased by a quiet Monday.
            log "SKIP non_session -- $GUARD_LINE (heartbeat and status untouched)"
            exit 0
        fi
        ;;
    *)
        log "WARN calendar guard unusable (rc=$GUARD_RC: $GUARD_LINE) -- running anyway"
        ;;
esac

# ---- the feeds, BEFORE the chains and before the 16:45 object ---------------
#
# The market-state object computes at 16:45 from whatever is in the store, so the
# order here is the whole point: a feed that ran after it would produce an object
# describing yesterday. Prices and FRED both, through one entry point
# (altdata/feeds.py) so the list of what runs does not exist twice.
#
# ITS FAILURE IS NOT THIS RUN'S FAILURE. The chains are the irreplaceable stage --
# yfinance serves no history, so a missed night is missed forever -- and a feed
# problem must not stop them. A stale feed is visible in the heartbeat's freshness
# check and in the object's own absent-with-a-reason dimensions, which is a better
# channel than a red pipeline that hides the chain fetch behind it.
log "feeds: pull start"
# LOGGERS ARE SKIPPED HERE AND RUN IN THE OVERNIGHT PASS. They are nightly by
# design (29.3's RTAT publishes for the prior session; the consensus log is an
# end-of-day read) and this step exists to put prices and FRED in front of the
# 16:45 object. Running them twice would be harmless -- drop_unchanged sees to that
# -- and would still spend a vendor's rate limit twice for nothing.
FEED_OUT="$("$VENV_PY" -m altdata.feeds pull --skip loggers 2>&1)"
FEED_RC=$?
printf '%s' "$FEED_OUT" | sed 's/^/  /' >>"$LOG"
if [[ $FEED_RC -ne 0 ]]; then
    log "WARN feeds pull exited $FEED_RC -- continuing; the freshness check reports it"
else
    log "feeds: pull done"
fi

# THE DERIVED FEATURES, RECOMPUTED FROM THE PULL THAT JUST LANDED.
#
# breadth, trend, realized vol and the VIX3M/VIX term-structure ratio are calc.*
# series DERIVED from the prices above, and nothing else in the system computes
# them: regime.compute() reads calc.* and never writes it. So a pass that pulled
# prices and did not recompute them leaves the 16:45 object reading whenever the
# features were last run by hand, and within a few sessions the dimensions' own
# staleness rule turns them absent -- for want of a step, not for want of data.
# That is exactly what happened: the features existed on one machine and not on
# the box, and the vol dial's term-structure leg read absent there while reading
# contango here, from the same store.
#
# Its failure is not this run's failure, for the same reason the pull's is not.
log "features: derived recompute"
FEAT_OUT="$("$VENV_PY" -m altdata.market_features compute 2>&1)"
FEAT_RC=$?
printf '%s' "$FEAT_OUT" | sed 's/^/  /' >>"$LOG"
if [[ $FEAT_RC -ne 0 ]]; then
    log "WARN market_features exited $FEAT_RC -- continuing; the object's dimensions report their own staleness"
else
    log "features: derived recompute done"
fi

# ---- the events ingest, then the surprises ---------------------------------
#
# ORDER MATTERS AND IT IS NOT ALPHABETICAL. The ingest writes the earnings rows
# that the earnings surprise is read out of, and the FRED pull above writes the
# actuals the macro surprise is measured against -- so both run after those two and
# before nothing.
#
# NEITHER CAN FAIL THE PASS, on the same argument as the feature recompute: this
# runs unattended and a traceback here would cost the capture that follows it. Each
# source reports its own state and two of the six are dormant by configuration.
log "events: ingest"
EV_OUT="$("$VENV_PY" -m altdata.events_ingest pull 2>&1 | tail -20)"
EV_EXIT=$?
printf '%s' "$EV_OUT" | sed 's/^/  /' >>"$LOG"
[[ $EV_EXIT -ne 0 ]] && log "WARN events_ingest exited $EV_EXIT -- continuing; tomorrow's anchor prints its EVENTS block with a reason"

log "surprise: compute"
SUR_OUT="$("$VENV_PY" -m altdata.surprise compute 2>&1 | tail -8)"
SUR_EXIT=$?
printf '%s' "$SUR_OUT" | sed 's/^/  /' >>"$LOG"
[[ $SUR_EXIT -ne 0 ]] && log "WARN surprise exited $SUR_EXIT -- continuing"

START_EPOCH=$(date +%s)
"$VENV_PY" run_eod.py --close-source "$CLOSE_SOURCE" >>"$LOG" 2>&1
RC=$?
ELAPSED=$(( $(date +%s) - START_EPOCH ))

log "run end rc=$RC elapsed=${ELAPSED}s"
printf 'rc=%s sha=%s pull=%s elapsed=%s at=%s\n' \
    "$RC" "$SHA" "$PULL_STATUS" "$ELAPSED" "$(date --iso-8601=seconds)" >"$STATUS"

if [[ $RC -eq 0 ]]; then
    # Heartbeat content is the evidence; its mtime is what the checker reads.
    printf 'ok sha=%s pull=%s elapsed=%s at=%s\n' \
        "$SHA" "$PULL_STATUS" "$ELAPSED" "$(date --iso-8601=seconds)" >"$HEARTBEAT"
    log "heartbeat touched"
else
    log "heartbeat NOT touched (rc=$RC)"
fi

exit $RC
