#!/usr/bin/env bash
#
# The 06:45 ET overnight fetch, as the VPS timer runs it.
#
#   git pull --ff-only -> calendar guard -> venv overnight -> log -> status
#     -> correction pull (early set) -> loggers -> weekly/annual checks -> events
#     -> surprise
#
# WHY IT IS A SEPARATE UNIT FROM THE 07:00 RENDER. Reports never fetch (30.4),
# and the reason is not tidiness. A render that fetched would fail for transport
# reasons -- Yahoo rate-limiting, a dropped network -- and then report them as
# market facts, or produce nothing at all and leave 07:00 silent. Split, a dead
# fetch becomes a block in the report that names why it is empty, which is the
# thing the reader needs before the open.
#
# Fifteen minutes of separation: enough for a slow Yahoo response, short enough
# that the numbers are still the morning's. The render flags anything older than
# 75 minutes rather than printing it as current.
#
# THE CALENDAR GUARD, same table as every other wrapper. No US session means no
# US open to anchor, and a fetch on Thanksgiving would write rows the 07:00 run
# would then have to decide about. Cheaper to not write them.
#
# NO HEARTBEAT HERE. The heartbeat belongs to the 07:00 render, which is the
# thing whose absence a human should hear about -- and it covers this unit
# transitively, because a fetch that did not run produces an absent overnight
# block, which makes the render degraded. Two heartbeats for one chain would
# both need clearing and neither would be the authority.
#
# Exit codes are overnight.py's, passed through:
#   0 at least one symbol fetched and written
#   1 nothing fetched -- every symbol failed, or yfinance is missing
#
# Overridable:
#   CHESTER_REPO / CHESTER_LOG_DIR / CHESTER_STATE_DIR / CHESTER_PYTHON
#   CHESTER_SESSION_DATE     evaluate the guard against this ET date
#   CHESTER_FORCE_RUN=1      run even on a non-session day
#   CHESTER_OVERNIGHT_DRY_RUN=1  fetch and write nothing

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"

mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/overnight-$(date +%Y-%m).log"
STATUS="$STATE_DIR/overnight_status"
LOCK="$STATE_DIR/overnight.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

# One fetch at a time. Two would double-write the same vintage -- harmless,
# because the store's idempotence index collapses them -- and would also double
# the requests to Yahoo, which is the part that gets rate-limited.
exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another overnight fetch holds the lock"
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
# Asked after the pull, so the box decides with the freshest holiday table it
# can have (Part 25). Fails OPEN: a redundant fetch costs ten HTTP requests, a
# suppressed one costs the morning's read.
SESSION_ARG="${CHESTER_SESSION_DATE:-}"
GUARD_LINE="$("$PY" -m altdata.session is-session ${SESSION_ARG:+"$SESSION_ARG"} 2>&1)"
GUARD_RC=$?

case $GUARD_RC in
    0) log "calendar ok -- $GUARD_LINE" ;;
    1)
        if [[ "${CHESTER_FORCE_RUN:-}" == "1" ]]; then
            log "non_session but CHESTER_FORCE_RUN=1 -- fetching anyway ($GUARD_LINE)"
        else
            log "SKIP non_session -- $GUARD_LINE (status untouched)"
            exit 0
        fi
        ;;
    *) log "WARN calendar guard unusable (rc=$GUARD_RC: $GUARD_LINE) -- fetching anyway" ;;
esac

DRY=""
[[ "${CHESTER_OVERNIGHT_DRY_RUN:-0}" == "1" ]] && DRY="--dry-run"

log "=== overnight fetch start sha=$SHA pull=$PULL_STATUS ${DRY:-live}"
"$PY" -m altdata.sources.overnight $DRY >>"$LOG" 2>&1

RC=$?

case $RC in
    0) STATE=ok;      MSG="overnight rows written" ;;
    1) STATE=nothing; MSG="NOTHING FETCHED -- every symbol failed, or yfinance is absent" ;;
    *) STATE=error;   MSG="overnight fetch failed rc=$RC" ;;
esac
log "$MSG"

printf 'state=%s rc=%s sha=%s at=%s\n' \
    "$STATE" "$RC" "$SHA" "$(date --iso-8601=seconds)" >"$STATUS"

# ---- the feeds, as the CORRECTION pass -------------------------------------
#
# AFTER THE FETCH, AND ONLY THE EARLY SET (30 Sep 2026). This pull used to run
# first and in full -- every price, 79 FRED series, 22 writers -- and once ST-1
# and ST-2 grew it past the unit's five minutes, systemd killed the pass on 28,
# 29 and 30 Sep before the overnight fetch ever started. The fetch is the capture
# (yfinance serves no history of an overnight session); the correction pass is
# not, so the capture goes first and the correction can never stand in front of
# it again.
#
# `--early` is the prices plus the official writers that publish between 16:10
# and now (altdata/feeds.py EARLY_WRITERS: MoF, CFETS). The prices are here for
# the two things the evening cannot fix: a close revised after 16:10 (a late
# print, an exchange correction), and a session missed because the box was
# down -- the pull re-reads two years, so a gap heals on the next run. FRED and
# the other writers publish in the US day; the 16:10 pull is the one that sees
# them. Re-pulling an unchanged close writes NOTHING (the vintage key), so the
# duplication costs a fetch and no rows.
log "feeds: correction pull start (early set)"
FEED_OUT="$("$PY" -m altdata.feeds pull --early 2>&1)"
FEED_RC=$?
printf '%s' "$FEED_OUT" | sed 's/^/  /' >>"$LOG"
[[ $FEED_RC -ne 0 ]] && log "WARN feeds pull exited $FEED_RC -- continuing"
log "feeds: correction pull done"

# ---- the loggers (L-1, 6 Oct 2026) -----------------------------------------
#
# THIS IS THEIR ONE SCHEDULED RUN. The 16:10 eod pull skips them ("they run in
# the overnight pass") and --early's fixed set skips them too, so from 30 Sep to
# 6 Oct borrow, consensus, vxcurve, shielded and rtat ran nowhere and nothing
# said so (INC-9, docs/incidents.md). tools/validate_feeds_scheduled.py now
# fails any commit in which a feed has no scheduled runner.
#
# After the correction pull, and after the status line, for the same reason the
# correction pull is: the overnight fetch is the capture and nothing goes in front
# of it. Its failure is not this run's failure -- one logger never takes another
# down (feeds.pull_loggers), and a dead one surfaces as the freshness roster
# reporting its keys stale.
log "feeds: loggers start"
LOG_OUT="$("$PY" -m altdata.feeds pull --only loggers 2>&1)"
LOG_RC=$?
printf '%s' "$LOG_OUT" | sed 's/^/  /' >>"$LOG"
[[ $LOG_RC -ne 0 ]] && log "WARN feeds pull --only loggers exited $LOG_RC -- continuing"
log "feeds: loggers done"

# THE BASE-RATE TABLES, AND WHY THERE IS NO SECOND UNIT FOR THEM.
#
# They recompute on the first session of a calendar year, on a method change, and
# whenever a table is missing -- and on every other night this step prints one line
# saying it did nothing. A distribution over ninety-nine years does not move because
# a Tuesday happened, so a timer of its own would be a unit to maintain, monitor and
# deploy for a job that fires once a year. The date check lives in base_rates.py
# rather than in this shell: "the first session of the year" is a calendar question,
# and the holiday table is the only thing that knows 1 January is not it.
#
# Its failure is not this run's failure. The overnight pass exists to fetch data
# that cannot be fetched later; a reference table that can be recomputed on demand
# must not stand in front of that.
# THE WEEKLY STRUCTURE COMPARISON. Same shape as the base-rate check below it and
# the same reasoning: the guard lives in the tool, not in this shell. `--if-stale`
# writes only the symbols whose newest table is over a week old, which fires once a
# week without a weekday test -- a weekday test fires twice if the pass runs twice
# and never if the box was down on the chosen day.
log "structure compare: weekly check"
SC_OUT="$("$PY" tools/structure_compare.py weekly --if-stale 2>&1 | tail -20)"
SC_RC=$?
printf '%s' "$SC_OUT" | sed 's/^/  /' >>"$LOG"
[[ $SC_RC -ne 0 ]] && log "WARN structure_compare exited $SC_RC -- continuing"

log "base rates: annual check"
BR_OUT="$("$PY" tools/base_rates.py maybe-recompute 2>&1)"
BR_RC=$?
printf '%s' "$BR_OUT" | sed 's/^/  /' >>"$LOG"
[[ $BR_RC -ne 0 ]] && log "WARN base_rates maybe-recompute exited $BR_RC -- continuing"

# AFTER THE VERDICT IS TAKEN, and this position is load-bearing. `RC=$?` above
# reads the exit status of the command immediately before it, so a step inserted
# between the fetch and that line would have made the wrapper report the exit code
# of a `[[ ]]` test instead of the fetch's -- the pass would have said `ok` whatever
# happened upstream. Everything below runs after the status file is written -- the
# correction pull, the weekly and annual checks, the ingest -- and each one's
# failure is a warning rather than the pass's verdict, because the fetch is the
# capture and these are records that can be pulled again.
# ---- the events ingest, then the surprises ---------------------------------
#
# THE MORNING HALF. The 07:00 anchor's EVENTS block reads "since the previous
# close", so the pass that fills it has to run before the anchor and after the
# overnight fetch -- which is here. The EOD pass runs the same two steps at 16:10;
# both are idempotent because every row is content-hashed, so the second pull of a
# day inserts only what arrived between them.
log "events: ingest"
EV_OUT="$("$PY" -m altdata.events_ingest pull 2>&1 | tail -20)"
EV_EXIT=$?
printf '%s' "$EV_OUT" | sed 's/^/  /' >>"$LOG"
[[ $EV_EXIT -ne 0 ]] && log "WARN events_ingest exited $EV_EXIT -- continuing; the anchor prints its EVENTS block with a reason"

# ---- the voices scan moved to its own timer (PB-1, 5 Oct 2026) -------------
# chester-voices.timer, 06:15 ET, scripts/run_voices_scan.sh: it no longer shares
# this pass's ten-minute limit. NAAIM was dropped (subscription-only since
# 1 Aug 2026).

log "surprise: compute"
SUR_OUT="$("$PY" -m altdata.surprise compute 2>&1 | tail -8)"
SUR_EXIT=$?
printf '%s' "$SUR_OUT" | sed 's/^/  /' >>"$LOG"
[[ $SUR_EXIT -ne 0 ]] && log "WARN surprise exited $SUR_EXIT -- continuing"


exit $RC
