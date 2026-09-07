#!/usr/bin/env bash
#
# Nightly off-box sweep -- D1a, and the answer to audit finding P0-1.
#
# THE STORE IS THE SYSTEM AND IT HAD ONE COPY. `data/chester.db` holds the
# point-in-time observation history, the decision register, and the immutable
# packets that make a past run replayable. It is gitignored, so git has never
# seen it; until the EOD zip learned to include it, the only copy in existence
# lived on one VPS. Losing that box would not have lost a night of chains -- it
# would have lost the record that the system had ever decided anything.
#
# Three trees go off-box:
#   $REPO/data      chains, computed profiles, the pin log, the database
#   ~/backups       the EOD zips (already a second copy, now a third off-box)
#   ~/.chester      heartbeat, status files, the alert the brief reads
#
# COPY, NEVER SYNC, AND THAT IS THE WHOLE SAFETY ARGUMENT. `rclone sync` makes
# the remote match the source, which means a local deletion -- a bad restore, a
# `rm -rf` on the wrong path, a disk that comes back empty -- is faithfully
# replicated to the backup, and the backup is gone at the exact moment it was
# needed. `rclone copy` only ever adds. The remote grows; nothing on it is
# removed by this script, ever. Pruning is a deliberate human act, not a side
# effect of the thing that is supposed to protect you.
#
# THE DATABASE IS SNAPSHOTTED, NOT COPIED. A live SQLite file read mid-write
# produces a file that opens cleanly and is missing rows -- a backup that looks
# valid and is not, which is worse than none because it is trusted. The
# snapshot goes through altdata.observations.snapshot_sqlite (the online backup
# API), the same call the EOD zip uses, so the two cannot drift apart. It is
# staged under a DATED name so the remote accumulates history rather than one
# ever-overwritten file: a corruption discovered on Thursday needs Tuesday's
# copy, and `copy` semantics only help if the names differ.
#
# Exit codes:
#   0 everything copied
#   1 environment problem (no repo, no venv, no rclone, no remote configured)
#   2 the database snapshot failed -- nothing was uploaded for it
#   3 rclone reported a failure on at least one tree
#
# Overridable:
#   CHESTER_REPO        repo checkout        (~/chester-reports)
#   CHESTER_LOG_DIR     log directory        (~/logs)
#   CHESTER_STATE_DIR   state dir            (~/.chester)
#   CHESTER_BACKUP_DIR  EOD zips             (~/backups)
#   CHESTER_PYTHON      interpreter          ($REPO/.venv/bin/python)
#   CHESTER_RCLONE_REMOTE   rclone remote and path, e.g. b2:chester-backup
#                           REQUIRED; without it the script exits 1 loudly
#                           rather than pretending to have run.
#   CHESTER_RCLONE_FLAGS    extra flags (default: --transfers 4 --checkers 8)

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
BACKUP_DIR="${CHESTER_BACKUP_DIR:-$HOME/backups}"
REMOTE="${CHESTER_RCLONE_REMOTE:-}"
RCLONE_FLAGS="${CHESTER_RCLONE_FLAGS:---transfers 4 --checkers 8}"

mkdir -p "$LOG_DIR" "$STATE_DIR"
LOG="$LOG_DIR/rclone_sync-$(date +%Y-%m).log"
STATUS="$STATE_DIR/rclone_sync_status"
LAST_OK="$STATE_DIR/rclone_sync_last_ok"
LOCK="$STATE_DIR/rclone_sync.lock"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" >>"$LOG"; }

finish() {   # finish <state> <rc> <detail>
    printf 'state=%s rc=%s at=%s detail=%s\n' \
        "$1" "$2" "$(date --iso-8601=seconds)" "$3" >"$STATUS"
    [[ "$1" == "ok" ]] && printf 'state=ok at=%s\n' "$(date --iso-8601=seconds)" >"$LAST_OK"
    log "$1 rc=$2 -- $3"
    exit "$2"
}

# One sweep at a time. A second copy would re-upload the same bytes and, more
# to the point, would race the first on the staged snapshot filename.
exec 9>"$LOCK"
if ! flock -n 9; then
    log "SKIP another sweep holds the lock"
    exit 0
fi

command -v rclone >/dev/null 2>&1 || finish no_rclone 1 "rclone is not installed"
[[ -n "$REMOTE" ]] || finish no_remote 1 \
    "CHESTER_RCLONE_REMOTE is unset -- nothing was copied anywhere"
[[ -d "$REPO/.git" ]] || finish no_repo 1 "no checkout at $REPO"

PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
[[ -x "$PY" ]] || finish no_venv 1 "no interpreter at $PY"

log "=== sweep start remote=$REMOTE"

# --- stage a consistent database snapshot -----------------------------------
STAGE="$STATE_DIR/backup_stage"
mkdir -p "$STAGE"
SNAP="$STAGE/chester-$(date +%Y-%m-%d).db"
rm -f "$STAGE"/chester-*.db          # only today's staged copy is kept locally
if ! "$PY" -m altdata.observations snapshot "$SNAP" >>"$LOG" 2>&1; then
    finish snapshot_failed 2 "database snapshot failed; see $LOG"
fi
log "staged $(basename "$SNAP")"

# --- copy, tree by tree -----------------------------------------------------
# Each tree is reported separately so a partial sweep names which part failed.
RC=0
FAILED=""
copy_tree() {    # copy_tree <local> <remote-subpath>
    local srcdir="$1" sub="$2"
    if [[ ! -d "$srcdir" ]]; then
        log "  skip $sub -- $srcdir does not exist"
        return 0
    fi
    # `copy`, not `sync`. See the header.
    if rclone copy "$srcdir" "$REMOTE/$sub" $RCLONE_FLAGS \
            --log-file "$LOG" --log-level INFO; then
        log "  ok $sub"
        return 0
    fi
    log "  FAILED $sub"
    FAILED="${FAILED:+$FAILED }$sub"
    return 1
}

copy_tree "$STAGE"      "db"      || RC=3
copy_tree "$REPO/data"  "data"    || RC=3
copy_tree "$BACKUP_DIR" "backups" || RC=3
copy_tree "$STATE_DIR"  "state"   || RC=3

if [[ $RC -eq 0 ]]; then
    finish ok 0 "all trees copied to $REMOTE"
fi
finish partial "$RC" "failed: $FAILED"
