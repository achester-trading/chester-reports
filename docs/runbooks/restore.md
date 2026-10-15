# Restore: rebuilding a dead box from GitHub and Drive

Written for AUD-2 item 5 on 14 Oct 2026. Until then no restore had ever been
tested. `python -m tools.restore_drill` now tests the most important step once a
month.

This is the procedure for when the VPS is gone: deleted, unbootable, or its disk
lost. **Every command here is the operator's.** `sudo` appears only in step 1, as
in `deploy/systemd/README.md`. Times are working estimates for one person who has
done it before, on the CX33 (8 GB) from 17 Oct 2026.

## What exists where

| Copy | Holds | Written |
|---|---|---|
| GitHub, `main` | the code, the units, the configs, the committed `data_store/` and `snapshots/` | on every push |
| Drive, `db/` | `chester-YYYY-MM-DD.db.gz`: `chester.db`, integrity-checked; 14 daily, 8 weekly, monthly | nightly at 02:30 ET |
| Drive, `data/` | `~/chester-reports/data` without `chester.db`: chains, computed profiles, the pin log | nightly at 02:30 ET |
| Drive, `backups/` | `~/backups`: the EOD zips | nightly at 02:30 ET (the zips themselves at 16:10) |
| Drive, `state/` | the state directory without `backup_stage/`: heartbeats, status files | nightly at 02:30 ET |
| Drive, `chester-data/` | `~/chester-data`: the live CSV store and the inboxes | nightly at 02:30 ET |
| The operator's own keeping | `.env`, IBC's `config.ini`, the rclone Drive token, the ssh key | never on Drive, never in git |

The Drive remote is the backup unit's `CHESTER_RCLONE_REMOTE`, for example
`gdrive:chester-backups`. It lives in the box-local drop-in
`chester-backup.service.d/remote.conf`.

## What the newest backups would lose

If the box dies at hour H on day D, a restore from the newest backups loses:

- **`chester.db` written since 02:30 ET on day D.** That is every observation,
  register row, grade, packet and `model_calls` row since the sweep's snapshot.
  - Dying at 16:30 loses that day's EOD pass, the morning anchor's object
    reads, the Portfolio Truth syncs (every 30 minutes from 09:00) and the
    auction ticks: about fourteen hours.
  - Dying at 02:00 loses nearly a full day.
  - The day's market observations can mostly be re-fetched by the next passes'
    backfills. Register writes and graded outcomes cannot; those were the
    operator's actions and would need re-entering from the reports' emails.
- **Chains and the pin log captured since 02:30 ET.** A chain is a market at an
  instant and cannot be re-fetched, so that day's 16:10 capture is lost unless
  the 16:10 EOD zip of the same day reached Drive. It did not: zips reach Drive
  at the next 02:30.
- **Everything since the last EOD zip (16:10 ET)** in `~/backups`. On the
  restored box the newest local zip is the one from the day before the sweep.
- **The CSV store and the state files** written since 02:30. The state files are
  rewritten by the next run of each writer anyway.

The worst case is the box dying just before 02:30: nearly 24 hours of
`chester.db`, and one EOD capture.

## The procedure

Total: about **2 h 30 min** of work, plus the Gateway's first supervised login.

### 1. A new box: 20 min

1. Create the server (CX33, Ubuntu LTS) and add the operator's ssh key.
2. Create the user and let its units outlive the session:

       sudo adduser ari && sudo usermod -aG sudo ari
       sudo loginctl enable-linger ari

3. Install the system packages:

       sudo apt install -y git python3-venv rclone xvfb sqlite3

   This is the only `sudo` in the procedure.
4. On the laptop, point `~/.ssh/config`'s `vps` entry at the new address.

### 2. The code: 10 min

    git clone git@github.com:achester-trading/chester-reports.git ~/chester-reports
    cd ~/chester-reports && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

### 3. The secrets, by hand: 15 min

1. **`.env`.** Write `~/chester-reports/.env` from the operator's own copy,
   mode 600. It is never on Drive and never in git, and `.env.example` names
   every key.
2. **Drive.** Run `rclone config` to re-authorise the Drive remote. Then prove
   it with `rclone lsd <remote>:`.
3. **IBC.** IBC and its `config.ini` (mode 600) go under `~/ibc`, per
   `deploy/systemd/README.md` section 4.

### 4. The data, from Drive: 30 to 60 min, mostly transfer

Restore the newest snapshot first. It is the one thing that cannot be rebuilt,
and the drill has already proved it opens.

    REMOTE=gdrive:chester-backups                    # the backup's remote
    mkdir -p ~/chester-reports/data && cd ~/chester-reports/data
    rclone lsf "$REMOTE/db" --files-only | sort | tail -1     # the newest
    rclone copy "$REMOTE/db/chester-YYYY-MM-DD.db.gz" .
    gunzip chester-YYYY-MM-DD.db.gz && mv chester-YYYY-MM-DD.db chester.db
    sqlite3 chester.db 'PRAGMA integrity_check'               # must print: ok

    rclone copy "$REMOTE/data"         ~/chester-reports/data
    rclone copy "$REMOTE/chester-data" ~/chester-data
    rclone copy "$REMOTE/backups"      ~/backups
    rclone copy "$REMOTE/state"        ~/state

These are copies from the remote, never `sync`, and never the other way. The
nightly sweep must not run until this step is done. Otherwise it would back up
a half-restored box under tonight's date. Step 5 enables it last.

### 5. The units: 20 min

1. **The box-local drop-ins.** Recreate each from `deploy/systemd/box-config.allow`:
   - the state directory's `Environment=` lines;
   - the backup's and the drill's `remote.conf`;
   - `ALTDATA_STORE` in `.env`, per README section 11.
2. **Copy the units and enable the timers** from the laptop:

       bash scripts/deploy.sh

   This copies every unit and enables the timers in `DEPLOY_TIMERS`.
3. **Prove the backup once by hand.** Then confirm its timer is enabled:

       cd ~/chester-reports && scripts/rclone_sync.sh; echo "exit=$?"

### 6. The Gateway: 30 min, supervised

Follow `deploy/systemd/README.md` section 4. That means one witnessed clean
start before `ibgateway.service` is enabled, then the watchdog and the restart
timer.

### 7. Prove it: 15 min

    systemctl --user list-timers
    ~/chester-reports/scripts/check_heartbeat_cron.sh; echo "exit=$?"
    cd ~/chester-reports && .venv/bin/python -m tools.restore_drill   # a drill on the new box

Then send a dry-run close (`deploy/systemd/README.md` section 8), and check the
dashboard shows every report reporting again.

## The drill

`python -m tools.restore_drill` does step 4's first block automatically, and
safely:
1. It copies the newest `db/` snapshot into a temporary directory.
2. It gunzips it there and runs `integrity_check`.
3. It prints each table's rows beside the live store's, which is opened
   read-only. The gap is what a restore today would lose.
4. It deletes the temporary directory.

It never writes to the remote. Its exit code is 0 for restorable, 1 for no remote
or no rclone, and 2 for no snapshot or a failed check.

`chester-restore-drill.timer` runs it on the 3rd of each month at 10:30 ET once
the operator enables it. It is deliberately not in `DEPLOY_TIMERS`. The output is
in `journalctl --user -u chester-restore-drill`.
