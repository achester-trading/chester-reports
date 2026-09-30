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
# Five trees go off-box:
#   db/        tonight's snapshot of chester.db, integrity-checked and gzipped
#   data/      $REPO/data -- chains, computed profiles, the pin log -- WITHOUT
#              chester.db*: the live file is never uploaded (see below)
#   backups/   ~/backups, the EOD zips (already a second copy, now a third)
#   state/     $CHESTER_STATE_DIR -- heartbeat, status files, the brief's alert
#              -- WITHOUT backup_stage/, which db/ already carries
#   chester-data/  ~/chester-data -- the live CSV store (ALTDATA_STORE), moved
#              out of the tracked data_store/ on 30 Sep 2026; skipped if absent
#
# COPY, NEVER SYNC, AND THAT IS THE WHOLE SAFETY ARGUMENT. `rclone sync` makes
# the remote match the source, which means a local deletion -- a bad restore, a
# `rm -rf` on the wrong path, a disk that comes back empty -- is faithfully
# replicated to the backup, and the backup is gone at the exact moment it was
# needed. `rclone copy` only ever adds. data/, backups/ and state/ only ever
# grow; nothing in them is removed by this script, ever.
#
# THE ONE REMOVAL IS db/ RETENTION, AND IT IS NARROW ON PURPOSE (29 Sep 2026).
# A dated full snapshot every night grows without bound, so db/ keeps 14 daily,
# 8 weekly and one per month forever (scripts/backup_retention.py holds the
# rule). It deletes with `rclone deletefile` on ONE NAMED FILE at a time, each
# name matching `chester-YYYY-MM-DD.db[.gz]`, only inside db/, and only after
# tonight's snapshot is confirmed on the remote. Never `delete`, `purge` or
# `sync`, which act on whatever a filter or a listing happens to match.
#
# THE DATABASE IS SNAPSHOTTED, NOT COPIED. A live SQLite file read mid-write
# produces a file that opens cleanly and is missing rows -- a backup that looks
# valid and is not, which is worse than none because it is trusted. The
# snapshot goes through altdata.observations.snapshot_sqlite (the online backup
# API), the same call the EOD zip uses, so the two cannot drift apart. Until 29
# Sep the data/ tree ALSO uploaded the live chester.db as a raw file every
# night, the torn copy this paragraph warns against; it is now excluded. The
# snapshot is then PRAGMA integrity_check'ed, gzipped, and the gzip is
# decompressed and compared byte for byte against the snapshot before anything
# is uploaded: a compressed copy nobody has ever decompressed is not a backup.
# It is staged under a DATED name so the remote accumulates history: a
# corruption discovered on Thursday needs Tuesday's copy.
#
# A STALL FAILS, IT DOES NOT HANG (29 Sep 2026). On 29 Sep the sweep sat in
# Google Drive's 403 "Quota exceeded ... Requests per minute" -- the shared
# rclone client ID's quota -- until systemd killed it at TimeoutStartSec, which
# left no status line and named no tree. So: rclone gets an idle timeout, a
# bounded retry budget and a request-rate ceiling; every tree runs under its
# own coreutils `timeout`, so a stuck tree fails as that tree (rc 3) and the
# rest still run; and a SIGTERM from systemd writes state=killed before exit.
# The durable fix for the quota is the operator's own OAuth client ID
# (deploy/systemd/README.md section 10), which no file in this repo carries.
#
# Exit codes:
#   0 everything copied (a failed db/ prune is logged and named, not fatal)
#   1 environment problem (no repo, no venv, no rclone, no remote configured)
#   2 the database snapshot, its integrity check or its compression failed --
#     nothing was uploaded for it
#   3 rclone reported a failure, or hit its time cap, on at least one tree
#   4 terminated from outside (TimeoutStartSec, or a stop) mid-sweep
#
# Overridable:
#   CHESTER_REPO        repo checkout        (~/chester-reports)
#   CHESTER_LOG_DIR     log directory        (~/logs)
#   CHESTER_STATE_DIR   state dir            (~/.chester)
#   CHESTER_BACKUP_DIR  EOD zips             (~/backups)
#   CHESTER_DATA_DIR    live CSV store root  (~/chester-data)
#   CHESTER_PYTHON      interpreter          ($REPO/.venv/bin/python)
#   CHESTER_RCLONE_REMOTE   rclone remote and path, e.g. gdrive:chester-backups
#                           REQUIRED; without it the script exits 1 loudly
#                           rather than pretending to have run.
#   CHESTER_RCLONE_FLAGS    parallelism (default: --transfers 4 --checkers 8).
#                           The stall limits below are NOT overridable here, so
#                           tuning parallelism cannot quietly drop them.

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
BACKUP_DIR="${CHESTER_BACKUP_DIR:-$HOME/backups}"
DATA_DIR="${CHESTER_DATA_DIR:-$HOME/chester-data}"
REMOTE="${CHESTER_RCLONE_REMOTE:-}"
RCLONE_FLAGS="${CHESTER_RCLONE_FLAGS:---transfers 4 --checkers 8}"

# Fail fast, retry sanely, stay under Drive's request quota. All in rclone
# v1.60 (the Debian package on the box). --timeout is the IO idle timeout: a
# connection that moves no bytes for 2 minutes is dead, not slow.
RCLONE_LIMITS="--timeout 2m --contimeout 60s --low-level-retries 10 --retries 2 --retries-sleep 30s --tpslimit 8 --stats 1m --stats-one-line"

TODAY="$(date +%Y-%m-%d)"
mkdir -p "$LOG_DIR" "$STATE_DIR"
# One log per run, so a failed night can be read on its own.
LOG="$LOG_DIR/rclone_sync-$TODAY.log"
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

# Killed from outside -- systemd's TimeoutStartSec, or a stop -- still leaves a
# status line the heartbeat reads as failed:killed, instead of the previous
# night's `ok` standing until it goes stale.
trap 'finish killed 4 "terminated mid-sweep (TimeoutStartSec or a stop); see $LOG"' TERM INT

command -v rclone >/dev/null 2>&1 || finish no_rclone 1 "rclone is not installed"
[[ -n "$REMOTE" ]] || finish no_remote 1 \
    "CHESTER_RCLONE_REMOTE is unset -- nothing was copied anywhere"
[[ -d "$REPO/.git" ]] || finish no_repo 1 "no checkout at $REPO"

PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
[[ -x "$PY" ]] || finish no_venv 1 "no interpreter at $PY"

log "=== sweep start remote=$REMOTE"

# --- stage a consistent, verified, compressed database snapshot -------------
STAGE="$STATE_DIR/backup_stage"
mkdir -p "$STAGE"
SNAP="$STAGE/chester-$(date +%Y-%m-%d).db"
UPLOAD="$SNAP.gz"
rm -f "$STAGE"/chester-*             # only tonight's staged copy is kept locally
if ! (cd "$REPO" && "$PY" -m altdata.observations snapshot "$SNAP") >>"$LOG" 2>&1; then
    finish snapshot_failed 2 "database snapshot failed; see $LOG"
fi
if ! (cd "$REPO" && "$PY" -m altdata.observations integrity "$SNAP") >>"$LOG" 2>&1; then
    finish snapshot_failed 2 "staged snapshot failed PRAGMA integrity_check; see $LOG"
fi
if ! gzip -c "$SNAP" >"$UPLOAD.part" || ! mv "$UPLOAD.part" "$UPLOAD"; then
    finish snapshot_failed 2 "compressing the snapshot failed; see $LOG"
fi
# The round trip, not just the CRC: decompress and compare every byte.
if ! gzip -dc "$UPLOAD" | cmp -s - "$SNAP"; then
    finish snapshot_failed 2 "gzip round trip does not reproduce the snapshot"
fi
log "staged $(basename "$UPLOAD") ($(stat -c %s "$SNAP") bytes -> $(stat -c %s "$UPLOAD"))"
rm -f "$SNAP"                        # the verified .gz is what goes off-box

# --- copy, tree by tree -----------------------------------------------------
# Each tree is reported separately and runs under its own time cap, so a
# partial sweep names which part failed and a stalled tree cannot starve the
# others. The caps sum to 115 minutes, plus up to ~10 for the db/ prune;
# TimeoutStartSec is 2h30min, so a cap always fires before systemd does.
RC=0
FAILED=""
copy_tree() {    # copy_tree <local> <remote-subpath> <minutes> [rclone filter args...]
    local srcdir="$1" sub="$2" mins="$3"
    shift 3
    if [[ ! -d "$srcdir" ]]; then
        log "  skip $sub -- $srcdir does not exist"
        return 0
    fi
    log "  start $sub (cap ${mins}m)"
    # `copy`, not `sync`. See the header.
    timeout --kill-after=60s "${mins}m" \
        rclone copy "$srcdir" "$REMOTE/$sub" $RCLONE_FLAGS $RCLONE_LIMITS "$@" \
            --log-file "$LOG" --log-level INFO
    local rc=$?
    if [[ $rc -eq 0 ]]; then
        log "  ok $sub"
        return 0
    fi
    if [[ $rc -eq 124 || $rc -eq 137 ]]; then
        log "  TIMEOUT $sub -- no completion within ${mins}m"
        FAILED="${FAILED:+$FAILED }$sub(timeout)"
    else
        log "  FAILED $sub rc=$rc"
        FAILED="${FAILED:+$FAILED }$sub"
    fi
    return 1
}

# --- db/ retention: 14 daily + 8 weekly + monthly, by name, inside db/ only --
PRUNE="not run"
prune_db() {
    local listing doomed name n=0
    if ! listing="$(timeout 5m rclone lsf "$REMOTE/db" --files-only $RCLONE_LIMITS 2>>"$LOG")"; then
        PRUNE="failed (listing db/)"
        return 1
    fi
    if ! doomed="$(printf '%s\n' "$listing" \
            | "$PY" "$REPO/scripts/backup_retention.py" \
                --today "$TODAY" --require "$(basename "$UPLOAD")" 2>>"$LOG")"; then
        PRUNE="refused (tonight's snapshot not listed on the remote)"
        return 1
    fi
    for name in $doomed; do
        # The same pattern backup_retention.py matches, checked again here: the
        # shell deletes nothing it has not itself recognised as a dated snapshot.
        if [[ ! "$name" =~ ^chester-[0-9]{4}-[0-9]{2}-[0-9]{2}\.db(\.gz)?$ ]]; then
            log "  prune: refusing unexpected name '$name'"
            continue
        fi
        if timeout 2m rclone deletefile "$REMOTE/db/$name" $RCLONE_LIMITS \
                --log-file "$LOG" --log-level INFO; then
            log "  prune: deleted db/$name"
            n=$((n + 1))
        else
            PRUNE="failed (deleting db/$name)"
            return 1
        fi
    done
    PRUNE="ok ($n deleted)"
    return 0
}

if copy_tree "$STAGE" "db" 20; then
    prune_db || log "  prune: $PRUNE"
else
    RC=3
fi
copy_tree "$REPO/data"  "data"    40 --exclude "/chester.db*"     || RC=3
copy_tree "$BACKUP_DIR" "backups" 30                              || RC=3
copy_tree "$STATE_DIR"  "state"   10 --exclude "/backup_stage/**" || RC=3
copy_tree "$DATA_DIR"   "chester-data" 15                         || RC=3
log "  prune: $PRUNE"

if [[ $RC -eq 0 ]]; then
    finish ok 0 "all trees copied to $REMOTE; db/ prune: $PRUNE"
fi
finish partial "$RC" "failed: $FAILED; db/ prune: $PRUNE"
