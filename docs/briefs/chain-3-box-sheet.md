# The box sheet for the third chain (for Ari)

**What this is.** Every box step the third chain's notes ask for, de-duplicated and ordered, for the evening `chain-3` merges to main. It is compiled from the box-command sections of six notes files:
- `docs/briefs/a47-chain3-notes.md` ("Box commands for Ari, after the third chain merges");
- `docs/briefs/a48-batch11-notes.md` ("Box commands for Ari, after the third chain merges (each dry run first)");
- `docs/briefs/a49-secondary-notes-notes.md` ("The merge sheet: box commands");
- `docs/briefs/b45-chain3-notes.md` ("Box commands");
- `docs/briefs/alpha-lab-4-notes.md` (the second paste's "Box commands", which supersedes the first paste's search and LTH lines);
- `docs/briefs/library-st-l-notes.md` ("Box commands": none required; its optional ledger editions are in D).

Each step names its source. It leaves out what chain-2's box sheet (`docs/briefs/chain-2-box-sheet.md`) already runs, except where a third-chain branch asks for a re-run, which is marked.

**Read this first.**
- **Times are Eastern.** Every step runs inside a window: weekdays 09:05–15:40 or 17:20–23:30, **never 16:00–17:20**; weekends are open, clear of Sunday 05:00. The merge evening's window is 17:20–23:30.
- **Every step is typed at the box prompt in the checkout** (`cd ~/chester-reports`) unless it says "from the laptop". Units are user units (`systemctl --user`). Logs are `~/logs/<name>-YYYY-MM.log`.
- **A dry run first** wherever one exists. It fetches and parses and writes nothing.
- **"Paste back"** means: send the output to a session if it differs from what is expected here.
- **⚑ marks a step that needs a decision from you.**
- Nothing here was run by a session, and no unit was enabled, started or restarted by one.
- **A wrapper typed at the ssh prompt does not get its unit's drop-in,** so its status and heartbeat land in `~/.chester`, not `~/state`. Prefix `CHESTER_STATE_DIR=~/state` where a step says so.

## Timers: what the self-deploy enables, and what is yours

The self-deploy (every 30 minutes inside the windows) copies the unit files and enables the timers in its declared list, `DEPLOY_TIMERS` in `scripts/deploy_remote.sh`. **The third chain does not change that list**, so the self-deploy enables no new timer. It copies:

| Unit | Change | Schedule | Who acts | Step |
|---|---|---|---|---|
| `chester-open-note.timer` / `.service` | new (a49) | Mon–Fri 09:50 ET | **you enable it by hand**, after its state drop-in | C |
| `chester-evening-note.timer` / `.service` | new (a49) | Sun–Thu 21:30 ET | **you enable it by hand**, after its state drop-in | C |
| `chester-meme-ingest.timer` | changed (a49): 21:45 → **21:15** (Mon–Fri and Sun, up to 2 minutes' jitter) | 21:15 ET | **you restart the timer**, once, for its new time | C4 |
| `chester-restore-drill.service` / `.timer` | **retired** (a47 item 5; ruling 6 of 19 Oct): removed from the repo, with `scripts/run_restore_drill.sh` and its `box-config.allow` line | — | **you remove the copies** chain-2's deploy left in `~/.config/systemd/user/` | A2 |
| `chester-ibkr-sync.timer` | comment only (R17: it fires through 17:30) | unchanged | nothing | — |

- The weekly restore test (`chester-restore-test.timer`, chain-2's C5) is the one restore check.
- Because the meme-ingest timer is active when the self-deploy copies its changed file, the heartbeat will likely report `restart_pending` (exit 14) naming it until C4 runs. That is expected.
- `chester-quarterly.timer` ships disabled and stays disabled. `ibgateway.service` and its restart timer stay held behind the witnessed clean start.

---

## A. The same evening as the merge: anything whose absence loses data

Nothing in the third chain captures a market at an instant that the scheduled units do not already take, so A is short. The notes' first runs are in C, because their `live_from` (26 Oct) makes every run before it a dry run.

**A1. Confirm the merge has reached the box.**
```
git pull --ff-only && git log -1 --oneline
systemctl --user list-unit-files 'chester-open-note*' 'chester-evening-note*' 'chester-meme-ingest*' 'chester-restore-drill*'
```
- **Expect** the merge commit's line. The note units listed once the self-deploy has copied them (within 30 minutes of the merge, or run `bash scripts/deploy.sh` from the laptop).
- **Expect** `chester-restore-drill*` still listed if chain-2's deploy copied it: A2 removes it.

**A2. Remove the retired restore drill's copies** (a47-chain3, "Box commands", 1).
```
ls ~/.config/systemd/user/chester-restore-drill* 2>/dev/null
systemctl --user is-enabled chester-restore-drill.timer
```
- **Expect** `disabled` (it was never enabled; chain-2's sheet held it back).
- If the files are there:
  ```
  rm ~/.config/systemd/user/chester-restore-drill.service ~/.config/systemd/user/chester-restore-drill.timer
  systemctl --user daemon-reload
  ```
- **Expect** `list-unit-files 'chester-restore-drill*'` to list nothing afterwards. `tools/restore_drill.py` stays in the repo; the weekly restore test calls it.

---

## B. First pulls, backfills and registrations, each dry run first

These fill history or register research. None loses data by waiting a day. Run them one at a time, after A, on the merge evening or the next one. **Before each one that reads a key, check `.env` through `altdata.secrets`**, which prints `set` or `missing` beside each name and never a value.

**B1. The dealer scorecard's backfill** (a48-batch11, "Box commands", 1). It rebuilds `dealer.scorecard_day` from the 16:10 settled captures, back to the first.
```
.venv/bin/python -m daily_cascade.scorecard_backfill run --dry-run
.venv/bin/python -m daily_cascade.scorecard_backfill run
```
- **Expect** per session: the capture read and the row it would write. Rows are labelled `"backfilled": true`, source `daily_close:backfill`. A session with any row is skipped, and a live row is never replaced. Pin flags and put/call are None on a backfilled row.
- A range is `run --from 2026-09-15 --to 2026-10-16`.
- It reads no key, so it has no `.env` check.

**B2. The names backfill, re-run** (a48-batch11, "Box commands", 2; **a re-run of chain-2's B5**). It now also writes `chain.iv30_atm`, `chain.rr_25d`, `chain.rv20` and `chain.rv60`. The store ignores duplicate rows, so the re-run is safe.
```
.venv/bin/python -m altdata.chain_metrics backfill-names --days 60 --dry-run
.venv/bin/python -m altdata.chain_metrics backfill-names --days 60
```
- **Expect** per day: the names read and the rows written, the four new keys among them.

**B3. E-6, engine 6 (extremes reversion): its dry run, then its registration** (b45-chain3, "Box commands"; alpha-lab-4).
```
.venv/bin/python -m alpha.engines.reversion lines 2>&1 | tee ~/logs/reversion_lines_dryrun.log
.venv/bin/python -m alpha.manifest register alpha/research/roster-2026-10-19-x3-3.yaml
```
- **Expect** `lines` to be read-only: each bucket's state, "awaiting (n=k of 30)" below 30 formation prints.
- **Expect** `register` to write the roster's manifest and its E-6 hypothesis at the manifest's instant. The spec's sha256 must match the roster's quote; a changed spec is refused.
- ⚑ Registration freezes the session-set choices (alpha-lab-4's needs-you).

**B4. E-7, engine 7 (intraday dealer regimes): its dry run, then its registration** (b45-chain3, "Box commands"). Its seven session-set choices were accepted as frozen in its spec (R8, 19 Oct). **Registering it is yours.**
```
.venv/bin/python -m alpha.engines.intraday_dealer lines 2>&1 | tee ~/logs/intraday_dealer_lines_dryrun.log
.venv/bin/python -m alpha.manifest register alpha/research/roster-2026-10-19-x3-4.yaml
```
- **Expect** `lines` to print each bucket's state with the legs not tracked. It is read-only.
- **Expect** the spec sha256 `2efa781c6d525bf5b13abb0d95193a4e867e2e04c6b0f56e05722b6a9798f1c7`; a changed spec is refused.

**B5. The mechanism scan's dry run** (b45-chain3, "Box commands"; chain-2's B7 ran the scan's dry run before posting existed, so this one is new for the posting step).
```
.venv/bin/python -m altdata.mechanism_scan run --dry-run --force
```
- **`--force` is needed on any day but Saturday** (the scan runs Saturdays ET unless forced).
- **Expect** the feeds and DefiLlama read, the dedupe and the pre-filter. No model call and no write. Saturday's real run posts each assessed entry as a PROPOSED story, with its base rate beside its grade (R7).
- ⚑ Confirm or reject each proposed story yourself: `python -m altdata.narratives confirm <id>` or `reject <id>`. Both are on the sessions' deny list.

**B6. The grammar search: coverage, and a scratch dry run** (alpha-lab-4, the second paste's "Box commands"). There is no real step by hand now: the CLI's `run` refuses outside a month's first week, and the first real step is the nightly loop's own last step in November's first week.
```
.venv/bin/python -m alpha.search coverage
ALPHA_RESEARCH_DIR=/tmp/search-dry .venv/bin/python -m alpha.search \
  --ledger /tmp/search-dry.db run --as-of 2026-11-02T22:00:00+00:00 \
  --max-candidates 8 --max-seconds 120 2>&1 | tee ~/logs/search_dryrun.log
```
- **Expect** `coverage` (read-only): the CFTC net passes; the macro and volatility dials fail (their vintages start in Sep 2026); funding fails (Oct 2026); the dealer regime is pending, "history from <date> (needs <date>); the dealer regime is not in search-v1". **So the first run tests 768 candidates, not 3,840.**
- R12 (19 Oct): no rethink of the dials' history before November; the box's coverage decides.
- **Expect** the scratch run to write only under `/tmp/search-dry*`, eight candidates, inside 120 s.

**B7. bitcoin-data.com's first pull** (alpha-lab-4, the second paste's "Box commands"; CD-12). **After you add `BITCOIN_DATA_API_KEY` to `.env`** (the free key, registered at bitcoin-data.com).
```
.venv/bin/python -m altdata.secrets BITCOIN_DATA_API_KEY
.venv/bin/python -m altdata.sources.btcdata budget
.venv/bin/python -m altdata.sources.btcdata 2>&1 | tee ~/logs/btcdata_first_pull.log
```
- **Expect** `set` from `secrets`, then `budget`'s requests spent and the key's presence, never its value.
- **Expect** the pull to spend 3 requests of the day's 15 (one per series, about 1,460 days from 2022-10-17). It writes `btcdata.lth_supply`, `.sth_supply`, `.supply_current` and `.lth_supply_share`. The guard refuses the 9th request in an hour and the 16th in a day; its state is `~/.chester/btcdata_requests.json`.
- Without the key it fetches nothing and the Monthly prints "not tracked (btcdata.lth_supply_share): no key in .env (BITCOIN_DATA_API_KEY)".
- Afterwards it rides the crypto basket's 17:25 run.
- **Paste back** the log if the parser refuses a row: the response's real field names are in it, and the fix is one line.

**B8. D4's flat-file backfill** (a48-batch11, "Box commands", 4). **After you add `MASSIVE_FLATFILES_ACCESS_KEY_ID` and `MASSIVE_FLATFILES_SECRET_ACCESS_KEY` to `.env`** (from Massive's dashboard). Its agreement tolerances were accepted on 19 Oct (R6).
```
.venv/bin/python -m altdata.secrets MASSIVE_FLATFILES_ACCESS_KEY_ID MASSIVE_FLATFILES_SECRET_ACCESS_KEY
.venv/bin/python tools/massive_flatfiles_backfill.py --dry-run
.venv/bin/python tools/massive_flatfiles_backfill.py --max-days 25
.venv/bin/python tools/massive_flatfiles_backfill.py --status
```
- **Expect** `set` beside both names.
- **Expect** the dry run to make one bucket listing (proving the credentials) and print the plan. It downloads nothing and writes nothing.
- **Expect** each real run to take at most 25 sessions (about 500 in all), resumable through `~/chester-data/flatfiles/backfill_state.json`. Rows go under source `chain_capture:flatfiles`, `reconstructed`, available 11:00 ET the next session.
- Repeat the `--max-days 25` line on later evenings until `--status` reports done. **Never 16:00–17:20.**

---

## C. The secondary notes (a49-secondary-notes, "The merge sheet: box commands")

`config/reporting_stack.yaml` sets `secondary_notes.live_from: "2026-10-26"`. Every run on a date before it is a dry run. **If the third chain merges after Thursday 22 October, a session moves `live_from` later first**: at least two weekday dry runs of each note and one Sunday dry run must come before it.

**C1. The state drop-ins, then daemon-reload.** Both notes write their status and heartbeat where the heartbeat reads them.
```
mkdir -p ~/.config/systemd/user/chester-open-note.service.d ~/.config/systemd/user/chester-evening-note.service.d
printf '[Service]\nEnvironment=CHESTER_STATE_DIR=%%h/state\n' > ~/.config/systemd/user/chester-open-note.service.d/override.conf
printf '[Service]\nEnvironment=CHESTER_STATE_DIR=%%h/state\n' > ~/.config/systemd/user/chester-evening-note.service.d/override.conf
systemctl --user daemon-reload
systemctl --user cat chester-open-note.service | tail -3
```
- **Expect** the `cat` to end with the override's `Environment=CHESTER_STATE_DIR=/home/<you>/state` line.

**C2. The evening note's first dry run, by hand, inside the evening window** (17:20–23:30; FORCE_RUN bypasses the `altdata.session evening-before` guard).
```
CHESTER_STATE_DIR=~/state CHESTER_FORCE_RUN=1 ~/chester-reports/scripts/run_evening_note.sh
tail -n 20 ~/logs/evening_note-$(date +%Y-%m).log
ls -t reports/dryrun/ | grep evening_note | head -2
```
- **Expect** the log line "evening note <session>: dry_run -> <path>; subject '...'; prose ...".
- **Expect** the archive under the checkout's `reports/dryrun/`: `evening_note_<session>.html` and `evening_note_<session>_payload.json`.
- **Expect** the mail under a "[DRY RUN] " subject, to `SMTP_RCPT` (else `CHESTER_ALERT_EMAIL`, else `SMTP_TO`). `deliver` loads `.env` itself.
- A soft failure still exits 0; read the log, not the exit code.

**C3. The open note's dry run by hand** (optional on the merge evening).
```
CHESTER_STATE_DIR=~/state CHESTER_FORCE_RUN=1 ~/chester-reports/scripts/run_open_note.sh
tail -n 20 ~/logs/open_note-$(date +%Y-%m).log
```
- Run in the evening, it waits the full 4-minute capture wait and prints "09:45 capture pending". That is the expected reading.
- It lands as `reports/dryrun/open_note_<session>.html` with its `_payload.json`, and mails under "[DRY RUN] ".

**C4. Enable both notes; restart the meme ingest for 21:15; read the timers.**
```
systemctl --user enable --now chester-open-note.timer chester-evening-note.timer
systemctl --user restart chester-meme-ingest.timer
systemctl --user list-timers 'chester-*note*' chester-meme-ingest.timer
```
- **Expect** next runs: the open note on the next weekday at 09:50; the evening note on the next Sunday to Thursday at 21:30; the meme ingest at 21:15 (plus up to 2 minutes' jitter), Monday to Friday and Sunday.
- **Expect** the heartbeat's `restart_pending` for the meme ingest to clear at its next run.
- **Expect** the dry runs: the weekday editions of 21–23 Oct and the Sunday edition of 25 Oct, under `reports/dryrun/`, each mailed "[DRY RUN]". The first live runs are Monday 26 Oct: the open note at 09:50 and the evening note at 21:30.
- Logs are `~/logs/open_note-YYYY-MM.log` and `~/logs/evening_note-YYYY-MM.log`; status files `<note>_status` and heartbeats `<note>_heartbeat` in `~/state` (100-hour allowance; the heartbeat only warns).
- ⚑ Read the dry runs before 26 Oct, and say if `live_from` should move. Read the first Sunday dry run's Yahoo news items: a Saturday news pull is proposed only if they stop short of Friday.

---

## D. The ledgers' box editions, written outside the checkout

Each writes into `~/chester-data/ledgers`, never into the checkout (a dirty checkout breaks every wrapper's `git pull --ff-only`). Copy them back from the laptop, then ask a session to commit them. A box edition supersedes the laptop's first edition; the pass rule is the one the first edition registered.

```
mkdir -p ~/chester-data/ledgers
```

**D1. S-2 and S-3** (a47-chain3, "Box commands", 2). ⚑ First decide S-3's "May 2026 rush" (a47's needs-you 2).
```
.venv/bin/python tools/calibration/s2_etf_flows.py --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/s3_leverage.py --box --out ~/chester-data/ledgers
```

**D2. OS-6 and OS-9** (a48-batch11, "Box commands", 3). The laptop's first editions are OS-6 FAIL and OS-9 INSUFFICIENT (the laptop holds no captures).
```
.venv/bin/python tools/calibration/os6_positioning.py --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/os9_build_outcomes.py --box --out ~/chester-data/ledgers
```

**D3. SN-1 and SN-2** (a49-secondary-notes; **optional**: its notes give no box command, but both scripts take `--box --out`).
```
.venv/bin/python tools/calibration/sn1_release_first_hour.py --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sn2_after_hours_earnings.py --box --out ~/chester-data/ledgers
```

**D4. library-st-l's three** (library-st-l, "Box commands": optional). The notes' lines omit `--out`, whose default is `docs/ledgers` inside the checkout, so `--out` is added here.
```
.venv/bin/python tools/calibration/fed_cycles.py --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr20_cofer.py --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr24_livingston.py --box --out ~/chester-data/ledgers
```

**Each prints** its as-of, window, n, statistic, the pass rule and its verdict. A ledger without its as-of, window or n is refused.

**Back to the laptop** (from the laptop, in the repo):
```
scp 'vps:~/chester-data/ledgers/s-[23]-*' docs/ledgers/
scp 'vps:~/chester-data/ledgers/os-[69]-*' docs/ledgers/
scp 'vps:~/chester-data/ledgers/sn-[12]-*' docs/ledgers/
scp 'vps:~/chester-data/ledgers/{fed-cycles,sr-20,sr-24}-*' docs/ledgers/
```

---

## E. Read-only checks

**E1. The heartbeat and the drift check.**
```
bash scripts/check_heartbeat_cron.sh; echo "exit $?"
```
- **Expect** exit 0 once C4 has run. Before it, `restart_pending` naming the meme ingest (exit 14) is the expected reading.

**E2. The timers.**
```
systemctl --user list-timers --all | grep chester
```
- **Expect** every `DEPLOY_TIMERS` timer with a next run, plus the two notes and the meme ingest at 21:15. No `chester-restore-drill`.

**E3. The register is untouched by the merge** (read-only).
```
.venv/bin/python -m altdata.mechanism_watch review | head -40
.venv/bin/python -m alpha.search plan
```
- **Expect** the mechanism-watch candidates as they were. `plan` prints the candidate count and the pending variables without running anything.

**E4. The pre-market line and the crypto paragraph** (a47-chain3, "Box commands", 3 and 4).
- The pre-market line: read it in the next 07:00 anchor's dry run, under the gauge (your dry run).
- The crypto paragraph: nothing to do. It ships **off** (`config/crypto_sources.yaml` `blocks.daily.enabled: false`) until you switch it on (a47's needs-you 1).

**E5. The cluster output** (a48-batch11, "Box commands", 5). Review the first two weeks of the level clusters' output (the anchor's lines and the close's outcome lines) with a session. This is the order's by-hand review, not a command.

---

## The one pull request

**Open it in the afternoon** (inside 09:05–15:40 ET), so its merge lands inside a window:
- **base** `main`, **compare** `chain-3`;
- title: "chain-3: the third chain (a47-chain3, a48-batch11, b45-chain3, library-st-l, a49-secondary-notes), with the rulings of 19 Oct 15:59 ET";
- body: the stitch notes' first line (`STITCH COMPLETE …`) and a link to `docs/briefs/chain-3-stitch-notes.md` and this sheet.

`chain-3` carries `master-guide` (which had not merged to main when the stitch began), so it merges cleanly whether or not `master-guide` lands first. `b48-scoreboard` and `a50-dealer-store` merge on their own afterwards.
