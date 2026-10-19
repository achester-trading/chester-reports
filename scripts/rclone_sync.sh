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
# ENCRYPTED, TO A SEPARATE ACCOUNT (audit-leftovers-1; the 14 Oct audit found the
# backups unencrypted in a Drive the box's token could wipe; ruled 15 Oct: rclone
# crypt under a separate Google account used only for backups). Every tree, the
# db/ snapshot and both prunes go through ONE crypt remote that
# scripts/rclone_crypt_env.sh builds from the environment
# (CHESTER_RCLONE_BACKUP_REMOTE, CHESTER_RCLONE_CRYPT_PASSWORD,
# CHESTER_RCLONE_CRYPT_SALT -- .env on the box); contents, file names and
# directory names are encrypted, and nothing secret is in rclone.conf. The old
# plaintext remote is NO LONGER WRITTEN: without the crypt settings the sweep
# exits 1 (no_crypt) rather than fall back to plaintext. The INBOUND pulls read
# the operator's main Drive through CHESTER_RCLONE_INBOX_REMOTE (a read-only
# token; deploy/systemd/README.md section 10), never through the backup remote.
#
# Six trees go off-box:
#   db/        tonight's snapshot of chester.db, integrity-checked and gzipped
#   data/      $REPO/data -- chains, computed profiles, the pin log -- WITHOUT
#              chester.db*: the live file is never uploaded (see below)
#   backups/   ~/backups, the EOD zips (already a second copy, now a third)
#   state/     $CHESTER_STATE_DIR -- heartbeat, status files, the brief's alert
#              -- WITHOUT backup_stage/, which db/ already carries
#   chester-data/  ~/chester-data -- the live CSV store (ALTDATA_STORE), moved
#              out of the tracked data_store/ on 30 Sep 2026; skipped if absent
#   reports/   the report archive (AUD-1 item 1e)
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
# The lab ledger's `alpha-YYYY-MM-DD.db.gz` snapshots in db/ keep by the same
# rule (ruling 8, 14 Oct 2026): by exact name, judged apart from chester's, the
# newest never pruned, and only on a night tonight's alpha snapshot uploaded.
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
# ONE BUDGET FOR THE SWEEP, NOT A SUM OF CAPS (14 Oct 2026). Until then the
# per-tree caps were sized so that their sum, plus the prunes, sat under the
# unit's TimeoutStartSec -- and every tree added broke the sum, so the caps were
# trimmed or the ceiling raised. The caps fit tonight's trees; the lab's copies
# (alpha-lab-2) and the next tree after them would break the sum again. So the
# sweep now has ONE budget, 105 minutes from its start
# (CHESTER_SWEEP_BUDGET_MIN), and whatever is added runs inside it:
#   - a tree's cap is the smaller of its own cap and the minutes left, less 2;
#   - with under 3 minutes left a tree is skipped, logged
#     "SKIP <tree> -- sweep budget spent", and named in FAILED as
#     <tree>(budget) -- rc 3, a sweep that did not copy everything;
#   - the housekeeping (the db/ prune, the chain-zip prune, the inbox pulls)
#     starts only with at least 10 minutes left, else it is logged "deferred to
#     the next night" and is not a failure; a prune stops deleting when fewer
#     than 2 minutes, one delete's own cap, are left.
# The trees run db, data, chester-data, state, reports, backups: the EOD zips
# go last because they repeat what data/ already holds. The budget, the
# kill-after and ten minutes of slack fit inside TimeoutStartSec
# (the validate_backup gate reads both files), so the sweep always writes its
# own status line before systemd's ceiling does.
#
# Exit codes:
#   0 everything copied (a failed db/ prune is logged and named, not fatal)
#   1 environment problem (no repo, no venv, no rclone, no remote configured)
#   2 the database snapshot, its integrity check or its compression failed --
#     nothing was uploaded for it
#   3 rclone reported a failure, or hit its time cap, on at least one tree, or a
#     tree was skipped with the sweep budget spent
#   4 terminated from outside (TimeoutStartSec, or a stop) mid-sweep
#   5 disk_low: under twice the database's size free where the snapshot is
#     staged -- nothing staged, nothing uploaded (AUD-1 item 1d)
#
# Overridable:
#   CHESTER_REPO        repo checkout        (~/chester-reports)
#   CHESTER_LOG_DIR     log directory        (~/logs)
#   CHESTER_STATE_DIR   state dir            (~/.chester)
#   CHESTER_BACKUP_DIR  EOD zips             (~/backups)
#   CHESTER_DATA_DIR    live CSV store root  (~/chester-data)
#   CHESTER_PYTHON      interpreter          ($REPO/.venv/bin/python)
#   CHESTER_RCLONE_BACKUP_REMOTE, CHESTER_RCLONE_CRYPT_PASSWORD,
#   CHESTER_RCLONE_CRYPT_SALT   the encrypted backup remote (rclone_crypt_env.sh);
#                           REQUIRED; without them the script exits 1 (no_crypt)
#                           rather than write plaintext anywhere
#   CHESTER_RCLONE_INBOX_REMOTE  the remote the inbound files are read from (the
#                           operator's main Drive, read-only); falls back to
#                           CHESTER_RCLONE_REMOTE's remote name; unset, the inbox
#                           pulls are skipped and logged
#   CHESTER_RCLONE_OUTBOX_REMOTE  the Alpha Lab outbox's own remote on the main
#                           Drive, scope drive.file; unset, the push is skipped
#   CHESTER_RCLONE_FLAGS    parallelism (default: --transfers 4 --checkers 8).
#                           The stall limits below are NOT overridable here, so
#                           tuning parallelism cannot quietly drop them.
#   CHESTER_SWEEP_BUDGET_MIN  the sweep's budget in minutes (105)
#   CHESTER_SWEEP_CLOCK     fixtures only: a file holding the epoch seconds the
#                           sweep reads as "now", so a gate can run a night on a
#                           fake clock without sleeping; unset, the clock is date

set -uo pipefail

REPO="${CHESTER_REPO:-$HOME/chester-reports}"
LOG_DIR="${CHESTER_LOG_DIR:-$HOME/logs}"
STATE_DIR="${CHESTER_STATE_DIR:-$HOME/.chester}"
BACKUP_DIR="${CHESTER_BACKUP_DIR:-$HOME/backups}"
DATA_DIR="${CHESTER_DATA_DIR:-$HOME/chester-data}"
# THE REPORT ARCHIVE (AUD-1 item 1e): every report's HTML, PDF and payload, as
# the reports' delivery step writes them -- CHESTER_REPORTS_DIR, else reports/ in
# the checkout. The README said the sweep carried it; it did not, until now.
REPORTS_DIR="${CHESTER_REPORTS_DIR:-$REPO/reports}"
# The backup target is the crypt remote (set below, once rclone is known to be
# there); the inbound files come from the main Drive, read-only.
REMOTE=""
INBOX_RNAME="${CHESTER_RCLONE_INBOX_REMOTE:-${CHESTER_RCLONE_REMOTE:-}}"
INBOX_RNAME="${INBOX_RNAME%%:*}"
# THE ALPHA LAB'S OUTBOX WRITES to the main Drive, which the read-only inbox remote
# cannot do: its own remote, scope drive.file -- it can create and write only the
# files it makes (ruling 1 of 17 Oct 2026). Unset, the outbox push is skipped and
# logged; it never falls back to the inbox remote or the crypt remote.
OUTBOX_RNAME="${CHESTER_RCLONE_OUTBOX_REMOTE:-}"
OUTBOX_RNAME="${OUTBOX_RNAME%%:*}"
SNAP_RECORD="$STATE_DIR/backup_snapshot"
RCLONE_FLAGS="${CHESTER_RCLONE_FLAGS:---transfers 4 --checkers 8}"
SWEEP_BUDGET_MIN="${CHESTER_SWEEP_BUDGET_MIN:-105}"
SWEEP_CLOCK="${CHESTER_SWEEP_CLOCK:-}"
HOUSEKEEP_MIN=10      # minutes left for a prune or an inbox pull to start

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

now_s() { if [[ -n "$SWEEP_CLOCK" ]]; then cat "$SWEEP_CLOCK"; else date +%s; fi; }
# Whole minutes left of the budget, rounded DOWN: 30 seconds gone is a minute gone.
mins_left() { echo $(( SWEEP_BUDGET_MIN - ( $(now_s) - SWEEP_START + 59 ) / 60 )); }
# can_housekeep <what>: a prune or a pull starts only with HOUSEKEEP_MIN left.
can_housekeep() {
    local left
    left=$(mins_left)
    if (( left < HOUSEKEEP_MIN )); then
        log "  $1: deferred to the next night (${left}m of the sweep budget left)"
        return 1
    fi
    return 0
}

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
# shellcheck source=scripts/rclone_crypt_env.sh
. "$(dirname "${BASH_SOURCE[0]}")/rclone_crypt_env.sh"
crypt_env || finish no_crypt 1 \
    "$CRYPT_ERR -- nothing was copied anywhere (the plaintext remote is no longer written)"
REMOTE="$CRYPT_REMOTE"
[[ -d "$REPO/.git" ]] || finish no_repo 1 "no checkout at $REPO"

PY="${CHESTER_PYTHON:-$REPO/.venv/bin/python}"
[[ -x "$PY" ]] || finish no_venv 1 "no interpreter at $PY"

SWEEP_START=$(now_s)
log "=== sweep start remote=$REMOTE budget=${SWEEP_BUDGET_MIN}m"

# --- stage a consistent, verified, compressed database snapshot -------------
STAGE="$STATE_DIR/backup_stage"
mkdir -p "$STAGE"

# NOT ON A NEARLY FULL DISK (AUD-1 item 1d). The snapshot and its gzip need up to
# twice the database's size beside it; a stage that fills the disk takes the
# live store's WAL with it. Under twice the database's size free: no snapshot,
# a named exit, and the heartbeat's disk line says why.
DB_FILE="$REPO/data/chester.db"
if [[ -f "$DB_FILE" ]]; then
    DB_BYTES=$(stat -c %s "$DB_FILE")
    FREE_BYTES=$(df --output=avail -B1 "$STAGE" | tail -1 | tr -d ' ')
    if [[ -n "$FREE_BYTES" ]] && (( FREE_BYTES < 2 * DB_BYTES )); then
        finish disk_low 5 "only $FREE_BYTES bytes free beside $STAGE, under twice the database's $DB_BYTES; no snapshot staged"
    fi
fi
SNAP="$STAGE/chester-$(date +%Y-%m-%d).db"
UPLOAD="$SNAP.gz"
rm -f "$STAGE"/chester-*             # only tonight's staged copy is kept locally
if ! SNAP_OUT="$(cd "$REPO" && "$PY" -m altdata.observations snapshot "$SNAP" 2>&1)"; then
    printf '%s\n' "$SNAP_OUT" >>"$LOG"
    finish snapshot_failed 2 "database snapshot failed; see $LOG"
fi
printf '%s\n' "$SNAP_OUT" >>"$LOG"
# THE ROW COUNT AT SNAPSHOT TIME (audit-leftovers-1): the weekly restore test
# compares the restored copy's observations against this, not against the live
# store, which has moved on since.
SNAP_ROWS="$(printf '%s\n' "$SNAP_OUT" | sed -n 's/.*, \([0-9,]*\) observations).*/\1/p' | tr -d ',' | tail -1)"
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
printf 'name=%s observations=%s at=%s\n' "$(basename "$UPLOAD")" "${SNAP_ROWS:-unknown}" \
    "$(date --iso-8601=seconds)" >"$SNAP_RECORD"
rm -f "$SNAP"                        # the verified .gz is what goes off-box

# --- the Alpha Lab's ledger, the same way (X-1.1, 13 Oct 2026) ---------------
# alpha.db sits beside chester.db under data/ and is a live SQLite file too, so
# it is snapshotted through its own module's online backup (python -m
# alpha.ledger snapshot), integrity-checked, gzipped and round-tripped, staged
# dated into db/ beside chester's, and excluded from the data/ tree below. The
# db/ prune keeps them by the same rule, as their own family (ruling 8).
# IT NEVER BLOCKS chester.db: before the lab's timers are enabled there is no
# alpha.db (a logged skip), and a failed alpha snapshot uploads nothing for it
# and fails the sweep as rc 3 named `alpha-db(snapshot)`, after every tree ran.
ALPHA_DB="$REPO/data/alpha.db"
ALPHA_SNAP="$STAGE/alpha-$TODAY.db"
ALPHA="skipped (no $ALPHA_DB)"
rm -f "$STAGE"/alpha-*
if [[ -f "$ALPHA_DB" ]]; then
    if (cd "$REPO" && "$PY" -m alpha.ledger snapshot "$ALPHA_SNAP" "$ALPHA_DB") >>"$LOG" 2>&1 \
            && (cd "$REPO" && "$PY" -m altdata.observations integrity "$ALPHA_SNAP") >>"$LOG" 2>&1 \
            && gzip -c "$ALPHA_SNAP" >"$ALPHA_SNAP.gz.part" \
            && mv "$ALPHA_SNAP.gz.part" "$ALPHA_SNAP.gz" \
            && gzip -dc "$ALPHA_SNAP.gz" | cmp -s - "$ALPHA_SNAP"; then
        ALPHA="ok"
        log "staged $(basename "$ALPHA_SNAP").gz"
    else
        ALPHA="FAILED"
        rm -f "$ALPHA_SNAP.gz" "$ALPHA_SNAP.gz.part"
        log "  alpha ledger: snapshot FAILED (chester.db's backup unaffected); see $LOG"
    fi
    rm -f "$ALPHA_SNAP"
fi
log "  alpha ledger: $ALPHA"

# --- copy, tree by tree -----------------------------------------------------
# Each tree is reported separately and runs under its own time cap, so a
# partial sweep names which part failed and a stalled tree cannot starve the
# others. The cap is cut to the budget's minutes left, less 2, and a tree with
# under 3 minutes left is skipped and named (see the header).
RC=0
FAILED=""
copy_tree() {    # copy_tree <local> <remote-subpath> <minutes> [rclone filter args...]
    local srcdir="$1" sub="$2" mins="$3"
    shift 3
    if [[ ! -d "$srcdir" ]]; then
        log "  skip $sub -- $srcdir does not exist"
        return 0
    fi
    local left
    left=$(mins_left)
    if (( left < 3 )); then
        log "  SKIP $sub -- sweep budget spent"
        FAILED="${FAILED:+$FAILED }$sub(budget)"
        return 1
    fi
    (( left - 2 < mins )) && mins=$(( left - 2 ))
    log "  start $sub (cap ${mins}m, ${left}m of the budget left)"
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
ALPHA_PRUNE="not run"
# prune_db <prefix> <tonight's file>: sets PRUNE_OUT. chester and alpha are
# judged apart; each name is re-matched against its own family's pattern.
prune_db() {
    local prefix="$1" require="$2" listing doomed name re n=0
    case "$prefix" in
        chester) re='^chester-[0-9]{4}-[0-9]{2}-[0-9]{2}\.db(\.gz)?$' ;;
        alpha)   re='^alpha-[0-9]{4}-[0-9]{2}-[0-9]{2}\.db(\.gz)?$' ;;
        *) PRUNE_OUT="refused (no rule for $prefix)"; return 1 ;;
    esac
    if ! listing="$(timeout 5m rclone lsf "$REMOTE/db" --files-only $RCLONE_LIMITS 2>>"$LOG")"; then
        PRUNE_OUT="failed (listing db/)"
        return 1
    fi
    if ! doomed="$(printf '%s\n' "$listing" \
            | "$PY" "$REPO/scripts/backup_retention.py" --prefix "$prefix" \
                --today "$TODAY" --require "$require" 2>>"$LOG")"; then
        PRUNE_OUT="refused (tonight's snapshot not listed on the remote)"
        return 1
    fi
    for name in $doomed; do
        if (( $(mins_left) < 2 )); then
            PRUNE_OUT="stopped (sweep budget spent; $n deleted)"
            log "  prune ($prefix): $PRUNE_OUT"
            return 0
        fi
        # The same pattern backup_retention.py matches, checked again here: the
        # shell deletes nothing it has not itself recognised as a dated snapshot.
        if [[ ! "$name" =~ $re ]]; then
            log "  prune: refusing unexpected name '$name'"
            continue
        fi
        if timeout 2m rclone deletefile "$REMOTE/db/$name" $RCLONE_LIMITS \
                --log-file "$LOG" --log-level INFO; then
            log "  prune: deleted db/$name"
            n=$((n + 1))
        else
            PRUNE_OUT="failed (deleting db/$name)"
            return 1
        fi
    done
    PRUNE_OUT="ok ($n deleted)"
    return 0
}

if copy_tree "$STAGE" "db" 20; then
    # Both families' prunes start only with HOUSEKEEP_MIN of the budget left,
    # like every other prune (stitching, week of 19 Oct): short of it, each is
    # deferred to the next night and says so.
    if can_housekeep "prune"; then
        prune_db chester "$(basename "$UPLOAD")"; PRUNE="$PRUNE_OUT"
        [[ "$PRUNE" == ok* ]] || log "  prune: $PRUNE"
    else
        PRUNE="deferred to the next night"
    fi
    if [[ "$ALPHA" != "ok" ]]; then
        ALPHA_PRUNE="not run (no alpha snapshot tonight)"
    elif can_housekeep "alpha prune"; then
        prune_db alpha "$(basename "$ALPHA_SNAP").gz"; ALPHA_PRUNE="$PRUNE_OUT"
    else
        ALPHA_PRUNE="deferred to the next night"
    fi
    log "  alpha prune: $ALPHA_PRUNE"
    PRUNE="$PRUNE; alpha: $ALPHA_PRUNE"
else
    RC=3
fi
copy_tree "$REPO/data"  "data"    40 --exclude "/chester.db*" --exclude "/alpha.db*" || RC=3
[[ "$ALPHA" == "FAILED" ]] && { RC=3; FAILED="${FAILED:+$FAILED }alpha-db(snapshot)"; }
copy_tree "$DATA_DIR"   "chester-data" 15                         || RC=3
copy_tree "$STATE_DIR"  "state"   10 --exclude "/backup_stage/**" || RC=3
copy_tree "$REPORTS_DIR" "reports" 15                             || RC=3
# The zips last: they repeat what data/ holds. The compaction's safety copy
# (the FRED compaction's --backup, ~/backups/chester-pre-compact-*.db) is a
# raw, unencrypted database and stays on the box.
copy_tree "$BACKUP_DIR" "backups" 30 --exclude "/chester-pre-compact-*.db" || RC=3
log "  prune: $PRUNE"

# --- the chain zips: the newest 14 on each side (AUD-1 1b, 1c; one rule since
# audit-leftovers-1) ---------------------------------------------------------
# Neither was ever pruned. Both by exact name, one file at a time, after the
# copy above has run; neither touches RC -- a failed prune is a log line.
#   DRIVE: backups/chains/chains_YYYY-MM-DD.zip dated more than 30 days back,
#     only once the newest local zip is listed there (backup_retention.py
#     --mode zips), with `rclone deletefile` -- never delete, purge or sync.
#   THE BOX: ~/backups/chains keeps its newest 14 session zips; an older one is
#     deleted only when the remote listing holds THAT EXACT FILE -- the same name
#     and the same size (--mode local-chains).
CHAINS_DIR="$BACKUP_DIR/chains"
ZIPS="not run"
prune_zips() {
    [[ -d "$CHAINS_DIR" ]] || { ZIPS="skipped (no $CHAINS_DIR)"; return 0; }
    can_housekeep "zips" || { ZIPS="deferred to the next night"; return 0; }
    local newest listing remote_file name n=0 m=0
    newest="$(ls -1 "$CHAINS_DIR" 2>/dev/null | grep -E '^chains_[0-9]{4}-[0-9]{2}-[0-9]{2}\.zip$' | sort | tail -1)"
    [[ -n "$newest" ]] || { ZIPS="skipped (no local zip)"; return 0; }
    remote_file="$STATE_DIR/remote_chains.lsf"
    if ! timeout 5m rclone lsf "$REMOTE/backups/chains" --files-only --format sp \
            --separator ";" $RCLONE_LIMITS >"$remote_file" 2>>"$LOG"; then
        ZIPS="failed (listing backups/chains)"
        return 1
    fi
    listing="$(cut -d';' -f2 "$remote_file")"
    # THE SAME RULE ON BOTH SIDES (audit-leftovers-1): the newest 14 zips are kept
    # on the box AND on Drive, so the mirror stops growing without bound. The box
    # goes first -- an older zip is deleted there only when Drive holds the exact
    # file -- then Drive deletes the same names by the same rule.
    for name in $(find "$CHAINS_DIR" -maxdepth 1 -name 'chains_*.zip' -printf '%s;%f\n' \
            | "$PY" "$REPO/scripts/backup_retention.py" --mode local-chains \
                --remote "$remote_file" 2>>"$LOG"); do
        [[ "$name" =~ ^chains_[0-9]{4}-[0-9]{2}-[0-9]{2}\.zip$ ]] || continue
        if (( $(mins_left) < 2 )); then
            ZIPS="stopped (sweep budget spent; $m deleted locally)"
            return 0
        fi
        rm -f -- "$CHAINS_DIR/$name" && m=$((m + 1))
    done
    for name in $(printf '%s\n' "$listing" \
            | "$PY" "$REPO/scripts/backup_retention.py" --mode zips \
                --today "$TODAY" --require "$newest" 2>>"$LOG"); do
        [[ "$name" =~ ^chains_[0-9]{4}-[0-9]{2}-[0-9]{2}\.zip$ ]] || continue
        if (( $(mins_left) < 2 )); then
            ZIPS="stopped (sweep budget spent; $m deleted locally, $n on Drive)"
            return 0
        fi
        if timeout 2m rclone deletefile "$REMOTE/backups/chains/$name" $RCLONE_LIMITS \
                --log-file "$LOG" --log-level INFO; then
            n=$((n + 1))
        fi
    done
    ZIPS="ok ($m deleted locally, $n on Drive)"
    return 0
}
prune_zips || true
log "  zips: $ZIPS"

# --- the inbound files: AAII's weekly row (10 Oct 2026), S&P DJI's EPS workbook
# (13 Oct 2026) --------------------------------------------------------------
# Each is ONE NAMED FILE in the operator's Drive, under chester-vendor-checks/
# <folder>/, copied into ~/chester-data/inbox/<folder>/ for its reader:
#   aaii   aaii-weekly.csv       the chat-side task "AAII weekly read -- Thursday"
#                                appends a row a week (altdata/sources/aaii.py)
# Read from the main Drive (CHESTER_RCLONE_INBOX_REMOTE), never the backup remote. `copyto` of one file, never a sync: the inbox
# only gains or overwrites that file, and copyto carries Drive's modification
# time over, which the S&P DJI reader takes as the drop time. They run after the
# trees and the prune and NEVER touch RC -- a missing or failed pull is a log
# line, not a failed backup.
pull_inbox_file() {
    local folder="$1" name="$2" rname="$INBOX_RNAME"
    [[ -n "$rname" ]] || { log "  $folder inbox: skip -- no inbox remote configured"; return 0; }
    local src="$rname:chester-vendor-checks/$folder/$name"
    local dest="$DATA_DIR/inbox/$folder/$name"
    can_housekeep "$folder inbox" || return 0
    if ! timeout 2m rclone lsf "$rname:chester-vendor-checks/$folder" --files-only \
            --include "/$name" $RCLONE_LIMITS 2>>"$LOG" \
            | grep -qxF "$name"; then
        log "  $folder inbox: skip -- $src is absent (or unlistable)"
        return 0
    fi
    if timeout 3m rclone copyto "$src" "$dest" $RCLONE_LIMITS \
            --log-file "$LOG" --log-level INFO; then
        log "  $folder inbox: ok -> $dest"
    else
        log "  $folder inbox: FAILED copyto (not counted against the sweep)"
    fi
    return 0
}
pull_inbox_file aaii aaii-weekly.csv || true
# spdji's sp-500-eps-est.xlsx is no longer pulled: S&P DJI withdrew the workbook
# (item 40's forward leg, ruled 17 Oct 2026; weekly-fixes-7 took it off the roster).

# --- the GLD archive: a one-time history load (12 Oct 2026) -----------------
# The operator downloads the GLD historical archive once in a browser (its API
# host disallows robots) and drops it in Drive under chester-vendor-checks/etf/;
# this copies each file there into the inbox the GLD writer reads, which tells
# the archive by its content, never its name. The AAII pull is the model:
# `copyto` of each named file, never a sync -- the inbox only gains or
# overwrites; nothing is deleted on either side. A file already in the inbox at
# the same size is skipped by rclone itself. Runs after the trees and NEVER
# touches RC.
pull_etf_archive() {
    local rname="$INBOX_RNAME" dir="$DATA_DIR/inbox/etf"
    [[ -n "$rname" ]] || { log "  etf inbox: skip -- no inbox remote configured"; return 0; }
    local srcdir="$rname:chester-vendor-checks/etf" f n=0
    local files
    can_housekeep "etf archive" || return 0
    if ! files=$(timeout 2m rclone lsf "$srcdir" --files-only --max-depth 1 \
            $RCLONE_LIMITS 2>>"$LOG") || [[ -z "$files" ]]; then
        log "  etf archive: skip -- $srcdir is empty, absent (or unlistable)"
        return 0
    fi
    while IFS= read -r f; do
        [[ -z "$f" ]] && continue
        if (( $(mins_left) < 7 )); then   # one copy's own 5m cap, plus the 2
            log "  etf archive: sweep budget spent; the rest deferred to the next night"
            break
        fi
        local src="$srcdir/$f" dest="$dir/$f"
        if timeout 5m rclone copyto "$src" "$dest" $RCLONE_LIMITS \
                --log-file "$LOG" --log-level INFO; then
            n=$((n + 1))
        else
            log "  etf archive: FAILED copyto $f (not counted against the sweep)"
        fi
    done <<< "$files"
    log "  etf archive: $n file(s) -> $dir"
    return 0
}
pull_etf_archive || true

# --- the X pilot's files (Batch 8 items 50 and 51; 17 Oct 2026) -------------
# The Grok digest (Drive chester-x-digest/, one x-digest-YYYY-MM-DD.md a day) and
# the reader task's two ledgers (Drive chester-vendor-checks/x-triage/) are read
# by the Digital Assets addendum (daily_cascade/digital_addendum.py) from the
# inbox, never from Drive:
#   chester-x-digest/x-digest-YYYY-MM-DD.md   -> ~/chester-data/inbox/x-digest/
#   chester-vendor-checks/x-triage/x-attention-ledger.csv, x-voices-ledger.csv
#                                             -> ~/chester-data/inbox/x-triage/
# `copyto` of each named file, never a sync. Each copied file gets a stamp
# beside it, <file>.copied_at, holding the instant its bytes arrived: that is
# the addendum's available_at (copyto carries Drive's modification time over,
# which is not when the box could read the file). A file whose bytes did not
# change keeps its stamp. Runs after the trees and NEVER touches RC.
pull_x_pilot() {
    local rname="$INBOX_RNAME" f n=0 files
    [[ -n "$rname" ]] || { log "  x inbox: skip -- no inbox remote configured"; return 0; }
    x_copy() {    # x_copy <remote src> <local dest>
        local src="$1" dest="$2" before="" after=""
        [[ -f "$dest" ]] && before="$(sha256sum "$dest" | cut -d' ' -f1)"
        if timeout 3m rclone copyto "$src" "$dest" $RCLONE_LIMITS \
                --log-file "$LOG" --log-level INFO; then
            after="$(sha256sum "$dest" | cut -d' ' -f1)"
            if [[ "$before" != "$after" || ! -f "$dest.copied_at" ]]; then
                date -u --iso-8601=seconds >"$dest.copied_at"
            fi
            return 0
        fi
        log "  x pilot: FAILED copyto $(basename "$dest") (not counted against the sweep)"
        return 1
    }
    if files=$(timeout 2m rclone lsf "$rname:chester-vendor-checks/x-triage" \
            --files-only --max-depth 1 $RCLONE_LIMITS 2>>"$LOG"); then
        while IFS= read -r f; do
            [[ "$f" == "x-attention-ledger.csv" || "$f" == "x-voices-ledger.csv" ]] \
                || continue
            x_copy "$rname:chester-vendor-checks/x-triage/$f" \
                "$DATA_DIR/inbox/x-triage/$f" && n=$((n + 1))
        done <<< "$files"
    else
        log "  x pilot: skip -- chester-vendor-checks/x-triage is absent (or unlistable)"
    fi
    if files=$(timeout 2m rclone lsf "$rname:chester-x-digest" --files-only \
            --max-depth 1 $RCLONE_LIMITS 2>>"$LOG"); then
        while IFS= read -r f; do
            [[ "$f" =~ ^x-digest-[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$ ]] || continue
            x_copy "$rname:chester-x-digest/$f" "$DATA_DIR/inbox/x-digest/$f" \
                && n=$((n + 1))
        done <<< "$files"
    else
        log "  x pilot: skip -- chester-x-digest is absent (or unlistable)"
    fi
    log "  x pilot: $n file(s) -> $DATA_DIR/inbox/x-triage, x-digest"
    return 0
}
pull_x_pilot || true

# --- the Alpha Lab's inbox and outbox (X-2.11, 14 Oct 2026) -----------------
# The same pattern as the AAII file, for a folder each way, and like it NEVER
# touching RC: a missing folder or a failed copy is a log line, not a failed
# backup.
#
# IN: <remote>:chester-vendor-checks/lab-inbox -> ~/chester-data/inbox/lab/.
# The Saturday brief writes hypothesis batches there (hypotheses-*.yaml, each
# with a human .md copy). THE MANIFEST FIRST: `rclone lsjson --metadata --hash`
# of the Drive folder, written beside the files as manifest-drive.json. Each
# entry's Metadata.btime is the file's Drive creation time -- the hypothesis
# batch's pre-registration instant -- and Metadata.mtime its last modification
# (rclone's Drive metadata, both RFC 3339 to the millisecond); Hashes.md5 lets
# the ingestion prove the bytes it read are the bytes listed. Listing before
# copying means a file can only ever be copied WITH an entry, or wait a night
# for one. Then `rclone copy` of the .yaml and .md files only -- never sync,
# never delete: the inbox only gains, and the daily proposer's own files and
# manifest, which are not on Drive, are never touched.
#
# OUT: ~/chester-data/outbox/lab/ -> <outbox remote>:chester-lab-outbox/, a
# top-level folder of its own (ruling 8, 19 Oct 2026), NEVER under
# chester-vendor-checks. A drive.file remote sees only what its own app made, so
# it cannot see the operator's chester-vendor-checks and would create a second
# folder of that name; rclone then resolves the duplicated name to either one,
# which could send the read-only inbox pulls (GLD's archive, AAII's row, the X
# pilot's files, the lab inbox) to the wrong folder. The inbox pulls stay where
# they are. The weekly loop writes lab-verdicts-YYYY-MM-DD.md there for the
# Saturday brief. `rclone copy`, never sync: the remote folder only gains.
LAB_OUTBOX_FOLDER="chester-lab-outbox"
LAB_INBOX="$DATA_DIR/inbox/lab"
LAB_OUTBOX="$DATA_DIR/outbox/lab"
# UNDER THE SWEEP'S BUDGET (stitching, week of 19 Oct): each copy runs only with
# 3 minutes of the budget left, as a tree does, its 5-minute cap cut to the
# minutes left less 2. Short of that it is skipped and NAMED -- lab-inbox(budget)
# or lab-outbox(budget) in LAB_SKIPPED, printed in the status line -- and, like
# every inbound file, never touches RC.
LAB_SKIPPED=""
LAB_CAP=5
lab_budget() {   # lab_budget <name>: sets LAB_CAP, or names the skip and fails
    local left
    left=$(mins_left)
    if (( left < 3 )); then
        log "  SKIP $1 -- sweep budget spent"
        LAB_SKIPPED="${LAB_SKIPPED:+$LAB_SKIPPED }$1(budget)"
        return 1
    fi
    LAB_CAP=5
    (( left - 2 < LAB_CAP )) && LAB_CAP=$(( left - 2 ))
    log "  start $1 (cap ${LAB_CAP}m, ${left}m of the budget left)"
    return 0
}
pull_lab_inbox() {
    # The main Drive, read-only (meme-ingest-ledgers-1's fold: never $REMOTE,
    # which is the crypt remote since audit-leftovers-1).
    local rname="$INBOX_RNAME"
    [[ -n "$rname" ]] || { log "  lab inbox: skip -- no inbox remote configured"; return 0; }
    local src="$rname:chester-vendor-checks/lab-inbox"
    if [[ ! -d "$LAB_INBOX" ]]; then
        log "  lab inbox: skip -- $LAB_INBOX does not exist (mkdir -p it once)"
        return 0
    fi
    lab_budget "lab-inbox" || return 0
    if timeout 2m rclone lsjson "$src" --files-only --metadata --hash $RCLONE_LIMITS \
            >"$LAB_INBOX/manifest-drive.json.part" 2>>"$LOG" \
            && mv "$LAB_INBOX/manifest-drive.json.part" "$LAB_INBOX/manifest-drive.json"; then
        log "  lab inbox: manifest ok -> $LAB_INBOX/manifest-drive.json"
    else
        rm -f "$LAB_INBOX/manifest-drive.json.part"
        log "  lab inbox: skip -- $src is absent or unlistable (not counted against the sweep)"
        return 0
    fi
    if timeout --kill-after=60s "${LAB_CAP}m" rclone copy "$src" "$LAB_INBOX" $RCLONE_LIMITS \
            --include "*.yaml" --include "*.md" --log-file "$LOG" --log-level INFO; then
        log "  lab inbox: ok -> $LAB_INBOX"
    else
        log "  lab inbox: FAILED copy (not counted against the sweep)"
    fi
    return 0
}
push_lab_outbox() {
    # Its own drive.file remote (ruling 1 of 17 Oct 2026), never $REMOTE.
    local rname="$OUTBOX_RNAME"
    [[ -n "$rname" ]] || { log "  lab outbox: skip -- no outbox remote configured"; return 0; }
    if [[ ! -d "$LAB_OUTBOX" ]]; then
        log "  lab outbox: skip -- $LAB_OUTBOX does not exist (mkdir -p it once)"
        return 0
    fi
    lab_budget "lab-outbox" || return 0
    if timeout --kill-after=60s "${LAB_CAP}m" rclone copy "$LAB_OUTBOX" "$rname:$LAB_OUTBOX_FOLDER" $RCLONE_LIMITS \
            --log-file "$LOG" --log-level INFO; then
        log "  lab outbox: ok -> $rname:$LAB_OUTBOX_FOLDER"
    else
        log "  lab outbox: FAILED copy (not counted against the sweep)"
    fi
    return 0
}
pull_lab_inbox || true
push_lab_outbox || true

LAB_NOTE="${LAB_SKIPPED:+; lab skipped: $LAB_SKIPPED}"
if [[ $RC -eq 0 ]]; then
    finish ok 0 "all trees copied to $REMOTE; db/ prune: $PRUNE$LAB_NOTE"
fi
finish partial "$RC" "failed: $FAILED; db/ prune: $PRUNE$LAB_NOTE"
