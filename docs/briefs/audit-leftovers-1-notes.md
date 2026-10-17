# audit-leftovers-1: the 14 Oct audit's leftovers, part 1 (17 Oct 2026)

**What it builds on, and the merge order.** Branch `audit-leftovers-1` from the tip
of `digital-49-51b` (my own line), so it carries the 6e and crypto branches. It
**merges after `digital-49-51b`, in the second stitched chain.** `weekly-fixes-7`
and `writer-fixes-1` merge on Monday on their own.

**One departure from the paste, and why.** The paste says aud-1's code and aud-2's
unit files are "in your line through the chain". They are not.
`digital-49-51b`'s line holds part of aud-3a but no aud-1 or aud-2 commit:

- `merge-base(aud-2, digital-49-51b)` is `fb67bf3`, from before both;
- the compaction tool, the restore drill and the memory caps were absent here.

They are in **Monday's** chain (aud-1 → aud-2 → aud-3a → aud-3c → aud-3b/3d).
Everything in Part 2 is built on that code, so **this branch merges
`origin/aud-2-ops-security` (which carries aud-1) into `digital-49-51b`'s tip
first** (`990b018`). Those commits reach main on Monday before this branch merges
on Thursday, so the merge changes nothing at Thursday's merge except that three
conflicts are already resolved:

- the Makefile's gate list: both;
- `chester-backup.service`'s ReadWritePaths: the union of both;
- CLAUDE.md: both paragraphs, with the gate count recounted.

**Nothing here changes what any report prints.**

## Step 0 (recorded on the branches themselves)

- `crypto-tranche-a-2`, run 39038665381 on `7e55cda`: **passed, 86/86** (80 code,
  6 data).
- `digital-49-51b`, run 39038761347 on `c5ab776`: **passed, 86/86**.

Both notes files carry the rows.

**The first derive's "stable impulse: computed 6368, written 0" is expected.**
The llama pull (macro group) calls `crypto_basket.write_stable_impulse` itself,
straight after its own write. The basket's `derive` then recomputes the same
6,368 rows (30- and 90-day, every stored day of `llama.stable_total`), and
`drop_unchanged` drops them all as already stored. Nothing was skipped.

**The rulings of 17 Oct on Tranche A part 2 and Phase 2** are applied on
`digital-49-51b` (`1856de2`; its notes have the detail), and this branch carries
them:

- mNAV is labelled "equity basis". The enterprise-value line is not printed,
  because EDGAR waits on `CHESTER_SEC_CONTACT`.
- CoinPaprika's and GeckoTerminal's terms URL, the date read and a quarterly
  re-read are in the catalogue.
- GeckoTerminal is read under its own terms. **One departure for you to
  confirm:** its swagger now publishes about 10 calls a minute, not 30, so the
  guard sits at 6.

## 1. Incremental pulls and one grouped freshness query

### FRED

Each series now asks only for what it lacks:
`observation_start` = its newest stored day less a **revision window by release
frequency**. The windows are SESSION-SET; the reasons are in
`altdata/sources/fred.py`'s docstring.

| Frequency | Window | Why |
|---|---|---|
| daily | 30 days | restated within days, if at all |
| weekly | 120 days | H.4.1 and claims revise the prior weeks |
| monthly, quarterly | 400 days | the release month plus the annual revisions (payrolls' benchmark, GDP's annual update) |

- **A series with nothing stored gets its full history** (no
  `observation_start`).
- A caller that passes `lookback_days` keeps the old fixed window; that is the
  Monthly's `--lookback-days`.
- A 400-day window misses a five-year seasonal-factor restatement (CPI each
  February). That is the FRED history run's job: `pull(..., full=True)`, still a
  leftover below.

**The CSV copy is merged, not rewritten** (`Store.write_observations(merge=True)`).
The old write overwrote the file with the batch, so a narrow fetch would have
truncated it. The newest stored day is read from that CSV (the dual write keeps
it level with the observation store), so the pull opens no database to decide
its window and its gates stay off the live store.

### The other writers

Every case, as found (the explorer's survey):

| Writer | Since parameter | After this branch |
|---|---|---|
| bundesbank | `startPeriod` | already incremental (60 days once held) |
| cfets | `startDate`/`endDate` | already incremental (30 days) |
| treasury_auctions | `startDate`/`endDate` | already incremental (45 days); the field name is fixed on `writer-fixes-1` |
| fiscaldata | `record_date:gte` | already incremental |
| deribit, hl, fut | start timestamps | already incremental (14 days) |
| fred_releases | `realtime_start/end` | already a window |
| **fng** (alternative.me) | `limit` (days) | **now incremental**: limit = days since its newest + 7 (`limit=0`, the whole history, when nothing is stored) |
| **ecb_irs** | `startPeriod` | **now incremental**: from a year before its newest month (checked live: 37 lines against 1,358) |
| fedboard H.4.1 | `lastobs` | fixed on `writer-fixes-1` (`lastobs=520`); making it `lastobs=8` once held is a one-line follow-up after the stitch, not done here because it would conflict with that branch |
| imf_ifs, bis_cbpol, imf_weo, imf_em (SDMX) | `startPeriod` exists | **unchanged**: not tested against their endpoints today; listed for the next part |
| wb_qeds | paging only | unchanged |
| eia, eia_rigs, acm, sffed, dkw, tic, french, shiller, damodaran, … | none: whole published files | unchanged (the source has no since) |
| mempool | its backfill reads `/all` | unchanged (the daily read is the current value) |

The shared helper is `_publication.since(keys, revision_days, db)`. It takes the
**earliest** of a writer's per-key newest days less the window, and gives None
(the full history) when any key has nothing stored.

**The price pull keeps its two-year re-read**, as ruled. It is deliberate
(corrections heal) and cheap (an unchanged close writes nothing).

### The grouped query

`feeds.freshness` (which `feeds check` and the heartbeat read) now calls
`ObservationStore.newest_observed_map(keys, as_of)` **once** for the whole
roster. That is one grouped `MAX(observed_at)` per key, for instrument NULL and
for any instrument, in statements of at most 900 keys. It replaces one indexed
query per key (two for an instrument-keyed one). The verdicts are unchanged.

**Gates** (`validate_audit_1.py` group E, 48/0 locally):

- a held monthly series asks for the 400-day window, a held daily one for 30,
  and a new one for the full history, through `fred.pull` with a stubbed fetch;
- the narrow fetch merges into the CSV copy;
- `lookback_days` keeps the fixed window;
- fng and the ECB with and without history;
- the grouped query returns exactly the per-key answers on a fixture store (a
  NULL-instrument key, an instrument-keyed one, an unknowable vintage, an absent
  key);
- `feeds.freshness` makes no per-key `latest_as_of` call.

## 2. Encrypted backups, the restore test, retention on both sides, reports/

### The crypt remote

`scripts/rclone_crypt_env.sh` (sourced by the sweep, the weekly test and the
monthly drill) builds `chestercrypt:` from three `.env` settings:

- `CHESTER_RCLONE_BACKUP_REMOTE`, the Drive remote on the **separate backup
  account**, and its folder;
- `CHESTER_RCLONE_CRYPT_PASSWORD`;
- `CHESTER_RCLONE_CRYPT_SALT`.

It does this through rclone's `RCLONE_CONFIG_CHESTERCRYPT_*` variables, with:

- `filename_encryption = standard` and directory names encrypted;
- the password and salt obscured from stdin (`rclone obscure -`), never argv.

**Nothing secret is in `rclone.conf`.** It holds only the backup account's Drive
token, as any Drive remote does, for an account that holds only ciphertext.

### The sweep (`scripts/rclone_sync.sh`)

- Every tree goes to `chestercrypt:chester/`: `db/`, `data/`, `chester-data/`,
  `state/`, **`reports/`** (it was already swept since aud-1's 1e; the README
  now says so) and `backups/`.
- **The old plaintext remote is no longer written.** Without the crypt settings
  the sweep exits 1, `no_crypt`, and copies nothing. There is no fallback.
- **The inbound files read the main Drive** through `CHESTER_RCLONE_INBOX_REMOTE`,
  a read-only token, never through the backup remote: AAII's row, GLD's archive,
  the X pilot's ledgers and digests.
- The spdji pull is gone (item 40's forward leg is withdrawn; `weekly-fixes-7`
  took the writer off the roster).
- `chester-backup.service` now reads `.env` (`EnvironmentFile=-…`) for the crypt
  settings.

### Retention, the same rule on both sides

The chain zips keep **the newest 14 on the box and on Drive** (`backup_retention.py
--mode zips` now counts instead of keeping 30 days). The box prunes first, and an
older zip is deleted locally only when Drive holds the exact file; Drive then
deletes the same names. `db/` keeps its 14 daily, 8 weekly and monthly-forever
rule.

### The record for the restore test

At snapshot time the sweep writes `~/.chester/backup_snapshot`: `name=
observations= at=`, the count parsed from the snapshot's own line.

### The weekly restore test

`chester-restore-test.timer` runs Sundays at 10:15 ET, after the 02:30 sweep
(whose ceiling is two hours) and clear of the 05:00 Weekly. It is **not in
`DEPLOY_TIMERS`**: enabled before the first encrypted snapshot exists, it could
only fail. It runs `scripts/run_restore_test.sh`, which calls `tools.restore_drill
--remote chestercrypt:chester --expect ~/.chester/backup_snapshot --status
~/.chester/restore_test_status`:

- it pulls the newest `db/` snapshot through the crypt remote into a temporary
  directory, gunzips it and runs `PRAGMA integrity_check`;
- the restored `observations` count must **equal the count recorded at snapshot
  time**, and the snapshot must be the one recorded;
- it writes `state=restore_ok` or `state=restore_failed` with the reason.

The monthly drill (aud-2) reads through the same crypt remote. Caps are
percentages (the 4 GB ruling), and `OOMScoreAdjust=500`.

### The heartbeat's backup field

It now also reads `restore_test_status`:

- a failed test reads `backup=failed:restore_test`;
- one not passed within 8 days (`CHESTER_RESTORE_MAX_DAYS`) reads
  `backup=stale_restore:<d>d`;
- both exit 12, and the alert JSON gains `restore_test`;
- no file (the test not yet enabled) changes nothing.

### Gates

| Gate | What it holds | Local |
|---|---|---|
| `tools/validate_backups.py` (**new**, a code gate) | **G** the crypt env from the environment only (bash with a fake rclone: the remote and obscured secrets when set, refused by name when not); **H** the restore test on a fixture snapshot (restore_ok; restore_failed on a corrupted copy, a wrong count, an unrecorded snapshot); **I** one listing pruned identically on both sides; **J** the trees with reports/, the crypt target, no plaintext target, the recorded count parsed, the inbox remote; **K** and **L** below | 28 / 0 |
| `tools/validate_backup_crypt.py` (**new, a DATA gate**) | real rclone, the local backend, configured by the same script with an empty rclone.conf: ciphertext only (no plaintext byte, file or directory name); the restore test restores it (restore_ok); a corrupted copy and a wrong password fail it (restore_failed) | 4 / 0 here |
| `tools/validate_secrets.py` group I | no tracked file gives an rclone secret variable (or the crypt settings) a value; no `rclone.conf` tracked; no `rclone obscure <literal>`; probes for the scan | 51 / 0 |
| `tools/validate_heartbeat_caller.sh` | restore failed, stale and ok cases | 104 / 0 |
| `tools/validate_backup.py` | updated for the crypt target, the inbox remote, one inbound file, the newest-14 zip rule; its fake sweep runs through the crypt remote | 80 / 0 |
| `validate_systemd_units.py`, `validate_audit_2.py`, `check_library.py` | unchanged checks over the new units and docs | 105 / 0, 25 / 0, clean |

**rclone is not in CI** (`.github/workflows` installs none), so the round trip is
a data gate, as the paste asked, like the IV solver's. It is "skipped: box-only"
in CI and runs on the box and on this laptop, which has rclone v1.75.1. It ran
here: 4/0.

## 3. The lock helper and the append-only triggers

**`observations.open_writer(writer, path=None)`** gives:

- WAL;
- a busy timeout of `BUSY_TIMEOUT_MS` (5,000);
- the writer's name on the store and in the log;
- an error logged if a maintenance row is ever left committed.

It is D1c's rule (satisfied by WAL and the busy timeout for append-only writers)
made one function. **Every scheduled writer now opens the store through it.**
That is 57 opens in 31 modules: every official and external writer on the
rosters, the price, FRED and prediction-market writers, the CSV store's dual
write, the publication runner, fed funds, the loggers, and the derived passes the
pulls run. **Gate K** fails any of those modules that constructs
`ObservationStore(` or calls `sqlite3.connect(` itself.

**The triggers.** `observations_no_update` and `observations_no_delete` (BEFORE
UPDATE / BEFORE DELETE) raise `observations is append-only: … refused` unless
the `observations_maintenance` table holds a row.

**The one documented exception path is `observations.maintenance(conn, tool)`.**
It inserts a row, yields for the DELETEs and removes the row, **in one
transaction**. So no other connection ever sees the row (gate L proves a second
connection reads 0 mid-transaction), and a crash rolls the row back with the
deletes. Every use is logged at WARNING with the tool's name. Its users:

- aud-1's compaction (`compact_fred.py`);
- the prediction-market backfill's replacement of its own earlier backfill rows
  (`prediction_markets.py`). It is a by-hand command, and without the path a
  re-run would be refused.

The one-off repair tools `tools/backfill_position_keys.py` (UPDATE) and
`tools/remove_partial_bars.py` (DELETE) are **refused by design** once the
triggers are in; if either is ever needed again, it goes through
`maintenance()`.

**The migration is a box write, the operator's:** `python -m altdata.observations
install-triggers` (idempotent). `python -m altdata.observations triggers` reads
whether they are in (exit 3 if not). They are **not** in `SCHEMA`, so opening a
store never installs them by surprise.

**Throughput, measured on the fixture** (gate L, best of three a side, 20,000
inserts): 0.189 s without the triggers and 0.192 s with, a ratio of 1.02. An
INSERT fires neither trigger. Earlier single runs read 0.93 and 1.19, which is
noise.

**Gate L** also holds:

- a fixture UPDATE and DELETE are refused;
- the maintenance path deletes, unseen by a second connection, and is gone after
  its commit;
- `compact_fred --apply` still works on a store with the triggers installed (5
  vintages of one value become 1, the triggers still in).

## 4. The README and CLAUDE.md

- **`deploy/systemd/README.md` section 10** is rewritten to what is true: where
  the backup goes and how it is encrypted (the four `.env` names, never their
  values), what is swept, retention on both sides, the record, the restore test,
  and the heartbeat field. The history sections (29 Sep, the client ID, running
  by hand) are kept.
- **`docs/runbooks/restore.md`** now restores a dead box through the crypt
  remote. It says plainly that the crypt password and salt must survive the box:
  in Ari's password manager.
- **CLAUDE.md** gains the paragraph on backups, `open_writer`, the triggers and
  incremental pulls. **The count line is recounted: eighty-five code gates
  (eighty-two Python, three shell) and seven data gates.** That is the merge's
  84 plus `validate_backups.py`, and the data gates gain `validate_backup_crypt.py`
  (`validate_audit_3a` holds the count, 83/0).

## Box steps, for Ari, in order

**Inside a window after Thursday's merge. Printed, never run here.** Values never
appear here or anywhere but `.env` and your password manager.

**Until steps 1-4 are done the nightly sweep exits 1 (`no_crypt`) and the
heartbeat reads `backup=failed:no_crypt`.** So do them in the same window as the
merge, before 02:30.

1. **The OAuth consent for the backup account** (a browser step, yours). The
   remote uses your own client ID (README section 10, "Your own Google Drive
   client ID"), signed in as the **separate backup account**. On the box:
   `rclone config` → new remote, type `drive`, your client ID and secret, scope
   `drive`, then `rclone authorize "drive" …` on the laptop, signed in as the
   backup account. Prove it with `rclone lsd <name>:`.
2. **The read-only inbox remote** on your **main** account, the same way with
   scope `drive.readonly`. It reads AAII's row, GLD's archive and the X pilot's
   files from `chester-vendor-checks/`. Prove it with `rclone lsd <name>:`.
3. **`.env`, by name** (the values are yours; generate the password and salt,
   e.g. 32 random characters each, and put both in your password manager
   **first**):
   - `CHESTER_RCLONE_BACKUP_REMOTE` (e.g. `<backup remote name>:chester-backups`)
   - `CHESTER_RCLONE_CRYPT_PASSWORD`
   - `CHESTER_RCLONE_CRYPT_SALT`
   - `CHESTER_RCLONE_INBOX_REMOTE` (e.g. `<read-only remote name>:`)
4. **The first encrypted backup, by hand:**
   ```
   ssh vps 'cd ~/chester-reports && scripts/rclone_sync.sh; echo "exit=$?"; cat ~/.chester/rclone_sync_status ~/.chester/backup_snapshot'
   ```
   Expect `exit=0`, `state=ok`, and a record with the observations count. In the
   backup account's Drive, the folder should hold only encrypted names.
5. **The first restore test, by hand:**
   ```
   ssh vps 'cd ~/chester-reports && scripts/run_restore_test.sh; cat ~/.chester/restore_test_status'
   ```
   Expect `state=restore_ok`. Then enable the weekly test (a unit command,
   yours):
   ```
   ssh vps 'systemctl --user daemon-reload && systemctl --user enable --now chester-restore-test.timer'
   ```
6. **The append-only migration** (a box write):
   ```
   ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.observations install-triggers && .venv/bin/python -m altdata.observations triggers'
   ```
   It is safe at any time; every writer already inserts only. If aud-1's FRED
   compaction is still to run, it works with the triggers in (gate L).
7. **Revoke the old full-scope token** once step 5 has passed. That is the main
   account's Security page → third-party access → the rclone client.
   - **Do this only after step 2 is in place:** the inbox no longer needs the old
     token, but a revoke before the read-only remote exists stops the inbound
     files.
   - Then delete the old plaintext folder (`gdrive:chester-backups`) after a
     retention period you choose. The encrypted `db/` keeps 14 daily and 8
     weekly snapshots, so 8 weeks is the natural point at which nothing in the
     old folder is newer than what the new one holds.
   - Remove the `chester-backup.service.d/remote.conf` drop-in (its
     `CHESTER_RCLONE_REMOTE` is no longer read by the sweep). The monthly drill
     no longer needs it either.

## Still open after this paste

- **The chester-meme draft ingest** (the next paste; it waits for Monday's aud-3b
  packet schema).
- **The as-of join's source tier.**
- **Writers onto their registered source ids.**
- **Call sites onto the Security Master.**
- **The FRED history run** (`fred.pull(..., full=True)`, which also catches the
  five-year seasonal restatements the 400-day window misses) **and the deep
  price backfill.**
- **The outlier and cross-source gate.**
- From this paste:
  - H.4.1 incremental (`lastobs=8` once held), after the stitch;
  - the SDMX writers' `startPeriod` (imf_ifs, bis_cbpol, imf_weo, imf_em), once
    tested against each endpoint.

## Files shared with the open branches

Trial merges (`git merge-tree`, nothing written) of this tip against each branch.
The conflicts **beyond those `digital-49-51b` already has** with the same
branches:

| Branch | New conflicts from this branch | Resolution |
|---|---|---|
| `aud-3a`, `aud-3c`, `aud-3d` (Monday) | `Makefile` | both gate lists |
| `aud-3b` (Monday) | `Makefile`; `deploy/systemd/README.md` section 10 | both gate lists. **README:** keep this branch's section 10 opening, then re-add aud-3b's "Alpha Lab's inbox and outbox" paragraph, with `<remote>` read as the inbox remote (see below) |
| `6b-dealer-3`, `st-r5-audit` (session A's line) | `Makefile`; `deploy/systemd/README.md` | as for aud-3b |
| `docs-batch-9`, `weekly-fixes-7`, `writer-fixes-1` | none | — |

**Session A's files.** This branch touches **none of session A's dealer files**:
not `dealer_block`, `dealer_weekly`, `weekly_sections`, `charts`, `stack_close`
or `exposure_compute`. It does share:

- `altdata/feeds.py`: the freshness read; their hunks are elsewhere, and the
  merge shows no new conflict there;
- `altdata/observations.py`: helpers added before the class, and the busy-timeout
  pragma's literal;
- `altdata/sources/prediction_markets.py`: the backfill's delete;
- `scripts/check_heartbeat_cron.sh`: the restore block after the backup block,
  and one JSON line;
- `chester-backup.service`: one `EnvironmentFile` line.

**A stitch hazard, aud-3b's Alpha Lab copies.** aud-3b (Monday) adds a lab
**inbox** pull and a lab **outbox** push to the sweep against the main Drive
(`chester-vendor-checks/lab-inbox`, `lab-outbox`). On this branch's sweep:

- the **inbox** pull must use `$INBOX_RNAME`, never `$REMOTE`, which is now the
  crypt remote. Lab batches written there would be unreadable to the Saturday
  brief.
- the **outbox** push **writes** to the main Drive, which the read-only inbox
  token cannot do.

I have not changed aud-3b's code (Monday's chain). The stitch must make that
call; see Needs you 1.

## Needs you

1. **The lab outbox's write path (a decision).** After the stitch the lab outbox
   needs a remote that can write to the main Drive.
   - **My recommendation:** a third remote on the main account with scope
     `drive.file`, which can create and update only the files rclone itself
     made, so it cannot wipe the rest of the Drive. Then
     `CHESTER_RCLONE_OUTBOX_REMOTE` in `.env`.
   - The alternative is to keep the old full-scope token for the outbox alone,
     which leaves the risk the audit named.
   - Until decided, **do not revoke the old token (step 7) if the lab outbox
     runs.**
2. **GeckoTerminal's guard at 6 a minute against its published ~10** (the ruling
   said 30). Confirm, or tell me to set it otherwise.
3. **The box steps above, in order**, in the merge's window.
4. **The crypt password and salt in your password manager before step 4.** A
   backup no one can decrypt is not a backup.

## CI

Read once after the push; recorded below.
