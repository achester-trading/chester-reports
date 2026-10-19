#!/usr/bin/env bash
#
# The encrypted backup remote, built from the environment (audit-leftovers-1; the
# 14 Oct audit's security finding, the fix ruled 15 Oct: rclone crypt under a
# separate Google account used only for backups). SOURCED, never run: the nightly
# sweep (scripts/rclone_sync.sh), the weekly restore test
# (scripts/run_restore_test.sh) and the monthly drill (scripts/run_restore_drill.sh)
# each source it, so the remote is defined in exactly one place.
#
#   crypt_env    sets RCLONE_CONFIG_CHESTERCRYPT_* in this shell's environment and
#                CRYPT_REMOTE to the crypt remote's root; returns 1, with
#                CRYPT_ERR naming what is missing, when a setting is absent
#
# THE SETTINGS, ALL FROM THE ENVIRONMENT (.env on the box, Ari's write; never in
# this repo and never in rclone.conf):
#   CHESTER_RCLONE_BACKUP_REMOTE   the Drive remote on the SEPARATE backup account,
#                                  and its folder, e.g. chesterbak:chester-backups.
#                                  Its OAuth token is in rclone.conf, as every
#                                  Drive remote's is; it is a token for an account
#                                  that holds nothing but ciphertext.
#   CHESTER_RCLONE_CRYPT_PASSWORD  the crypt password, in clear in .env (and in
#   CHESTER_RCLONE_CRYPT_SALT      Ari's password manager off the box); the salt is
#                                  rclone's "password2"
#
# rclone reads a remote from RCLONE_CONFIG_<NAME>_<KEY> variables, so the crypt
# remote exists for the processes this shell starts and nowhere on disk. Its
# password and salt must be given to rclone OBSCURED; `rclone obscure -` reads the
# clear value from stdin, so it never appears in a process's argument list.
# Filenames and directory names are encrypted as well as contents (standard
# filename encryption), so the backup account shows neither what nor when.

CRYPT_NAME="CHESTERCRYPT"
CRYPT_ROOT="chester"          # the folder inside the crypt remote the trees go under

crypt_env() {
    CRYPT_ERR=""
    CRYPT_REMOTE=""
    local base="${CHESTER_RCLONE_BACKUP_REMOTE:-}"
    local pw="${CHESTER_RCLONE_CRYPT_PASSWORD:-}"
    local salt="${CHESTER_RCLONE_CRYPT_SALT:-}"
    if [[ -z "$base" ]]; then
        CRYPT_ERR="CHESTER_RCLONE_BACKUP_REMOTE is unset"
        return 1
    fi
    if [[ -z "$pw" || -z "$salt" ]]; then
        CRYPT_ERR="CHESTER_RCLONE_CRYPT_PASSWORD or CHESTER_RCLONE_CRYPT_SALT is unset"
        return 1
    fi
    local opw osalt
    if ! opw="$(printf '%s' "$pw" | rclone obscure - 2>/dev/null)" || [[ -z "$opw" ]] \
            || ! osalt="$(printf '%s' "$salt" | rclone obscure - 2>/dev/null)" \
            || [[ -z "$osalt" ]]; then
        CRYPT_ERR="rclone obscure failed (is rclone installed?)"
        return 1
    fi
    export "RCLONE_CONFIG_${CRYPT_NAME}_TYPE=crypt"
    export "RCLONE_CONFIG_${CRYPT_NAME}_REMOTE=$base"
    export "RCLONE_CONFIG_${CRYPT_NAME}_FILENAME_ENCRYPTION=standard"
    export "RCLONE_CONFIG_${CRYPT_NAME}_DIRECTORY_NAME_ENCRYPTION=true"
    export "RCLONE_CONFIG_${CRYPT_NAME}_PASSWORD=$opw"
    export "RCLONE_CONFIG_${CRYPT_NAME}_PASSWORD2=$osalt"
    CRYPT_REMOTE="$(printf '%s' "$CRYPT_NAME" | tr '[:upper:]' '[:lower:]'):$CRYPT_ROOT"
    return 0
}
