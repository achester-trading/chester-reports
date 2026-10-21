# The box sheet for the fourth chain (for Ari)

**What this is.** Every box step the fourth chain's notes ask for, de-duplicated and ordered, for the evening `chain-4` merges to main. It is compiled from the box-command sections of four notes files:
- `docs/briefs/a50-dealer-store-notes.md` (A50, "The backfill: Ari's box command, dry run first"; A51, "A51 needs you" 3 and 4);
- `docs/briefs/b48-scoreboard-notes.md` (B48: none; B49, "Box command (Ari's; inside a window)");
- `docs/briefs/a52-doctrine-2-pack-notes.md` (A52: none, it is docs only);
- `docs/briefs/a53-batch12-notes.md` (A53, section 7, "The box commands, dry runs first").

Each step names its source. It leaves out everything chain-3's sheet (`docs/briefs/chain-3-box-sheet.md`) runs: none of the fourth chain's notes asks for a re-run of one of its steps. **If chain-3's sheet has not been run yet, run it first**, through its section C (the secondary notes), because this sheet's E2 reads the volatile-day flag in the open note's dry run.

**Read this first.**
- **Times are Eastern.** Every step runs inside a window: weekdays 09:05–15:40 or 17:20–23:30, **never 16:00–17:20**; weekends are open, clear of Sunday 05:00. The merge evening's window is 17:20–23:30.
- **Every step is typed at the box prompt in the checkout** (`cd ~/chester-reports`) unless it says "from the laptop". Units are user units (`systemctl --user`). Logs are `~/logs/<name>-YYYY-MM.log`.
- **A dry run first** wherever one exists. It fetches and parses and writes nothing. Where a command has no dry run, the sheet says so.
- **"Paste back"** means: send the output to a session if it differs from what is expected here.
- **⚑ marks a step that needs a decision from you.**
- Nothing here was run by a session, and no unit was enabled, started or restarted by one.

## Timers: what the self-deploy enables, and what is yours

**The fourth chain adds no unit and no timer, and does not change `DEPLOY_TIMERS`.** It changes two unit files by comment only (a50-dealer-store, A51's "kept as a starting value" lines):

| Unit | Change | Schedule | Who acts | Step |
|---|---|---|---|---|
| `chester-open-note.service` | comment only: `TimeoutStartSec` and the memory caps "kept 19 Oct 2026 as a starting value; reviewed after the first two live weeks" | unchanged (Mon–Fri 09:50) | nothing; the self-deploy copies it | — |
| `chester-evening-note.service` | the same comment | unchanged (Sun–Thu 21:30) | nothing; the self-deploy copies it | — |

- Both are oneshot services, so neither is running when the self-deploy copies it, and no `restart_pending` should follow. If the heartbeat names either one anyway, `systemctl --user daemon-reload` is enough (the unit's behaviour is unchanged).
- `scripts/check_heartbeat_cron.sh` changes by one comment (the same line).
- The dealer store (A50) runs inside the existing capture and EOD units: **no unit of its own**, and the units already allow writes under `%h/chester-reports`.
- Batch 12's two new writers (`ofr_fsi`, `fdic_qbp`) are on `OFFICIAL_WRITERS`, so they ride the 16:10 EOD pass from the first session after the merge. No timer.

---

## A. The same evening as the merge: anything whose absence loses data

**Nothing in the fourth chain loses data by waiting a day.** The dealer store's backfill reads profiles already on disk under `data/computed/`, which stay there; the FRED legs, KRE and the two writers have their history at the source; the superseding batch is a registration. So A is one check.

**A1. Confirm the merge has reached the box.**
```
git pull --ff-only && git log -1 --oneline
.venv/bin/python -c "from altdata import config; print(len(config.FRED_PULL_SERIES))"
```
- **Expect** the merge commit's line, then `277` (266, plus RSAFS from A51, plus Batch 12's ten).

---

## B. First pulls, backfills and registrations, each dry run first

Run them one at a time, after A1, on the merge evening or the next one. **Before each one that reads a key, check `.env` through `altdata.secrets`**, which prints `set` or `missing` beside each name and never a value.

**B1. A50's dealer-capture backfill** (a50-dealer-store, A50, "The backfill: Ari's box command, dry run first"; its needs-you 1). It stores the computed profiles already on disk.
```
.venv/bin/python -m altdata.dealer_store backfill --dry-run
.venv/bin/python -m altdata.dealer_store backfill
```
- **Expect** the dry run to print the files read, the rows it would write, the first and last session, and the skipped files counted by reason. A profile the vendor supplied (`gamma_source "vendor"`) is refused and counted among the skipped.
- **Expect** the second command to write them. A re-run writes nothing: the store's vintage key makes a re-store a no-op.
- `--from D --to D` bound the sessions; `--dir` and `--db` override the defaults. It reads no key.

**B2. The retail-sales (RSAFS) history** (a50-dealer-store, A51 needs-you 4, "optional"). Its first rows come from the FRED pull after the merge; the deep history, from ALFRED at each value's first publication, is wanted if the open note's prior form is wanted before the next release.
```
.venv/bin/python -m altdata.secrets FRED_API_KEY
.venv/bin/python -m altdata.fred_history backfill --series retail_sales --dry-run
.venv/bin/python -m altdata.fred_history backfill --series retail_sales
```
- **Expect** `set`, then "FRED history -- 1 series, DRY RUN, nothing written" and the vintages it would write; then the same, writing, under source `fred:backfill`.
- `--series` takes the registered key (`retail_sales`), not the FRED id.

**B3. Batch 12's first pulls** (a53-batch12, section 7). Four parts, in this order.

*B3a. The ten FRED legs' first-print history (ALFRED).* They also arrive with the next 16:10 pull; this gives them their history.
```
.venv/bin/python -m altdata.fred_history backfill --series fin_cp_3m,sofr_p99,ioer,dw_primary_credit,fed_other_credit,fhlb_advances,h8_dep_small,h8_dep_large,mmf_retail,stlfsi --dry-run
.venv/bin/python -m altdata.fred_history backfill --series fin_cp_3m,sofr_p99,ioer,dw_primary_credit,fed_other_credit,fhlb_advances,h8_dep_small,h8_dep_large,mmf_retail,stlfsi
```
- **Expect** "FRED history -- 10 series, DRY RUN, nothing written", then the same writing.

*B3b. KRE's price history.*
```
.venv/bin/python tools/backfill_prices.py --symbols KRE --period max --dry-run
.venv/bin/python tools/backfill_prices.py --symbols KRE --period max
```
- **Expect** KRE's daily bars from 2006 (`yfinance.mkt_kre`), close and volume.

*B3c. The two new writers.* **Neither has a dry run** (a53's notes list them after the dry runs for that reason). Each is append-only, and a re-run writes nothing new. Both also ride the 16:10 EOD pass, so this step only brings their history forward by a day.
```
.venv/bin/python -m altdata.sources.ofr_fsi --backfill
.venv/bin/python -m altdata.sources.fdic_qbp --since 2007-03-31
```
- **`--backfill` is added here** to a53's line: on a first pull, with nothing yet held, the writer writes its whole history anyway, but if the 16:10 pass has already run once, only the last 400 days would be written without it. With it, the order does not matter.
- **Expect** each to print its JSON summary, `"status": "OK"`, with `written` in the thousands for the OFR FSI (daily from 2000) and about 78 quarters' rows for the FDIC (from Q1 2007).

*B3d. The read, once they are in* (read-only).
```
.venv/bin/python -m altdata.bank_stress show
```
- **Expect** the panel's rows with their dual percentiles, both flags (funding stress, deposit flight) and the classifier, which prints only when KRE is down more than 10% over 20 sessions. "not tracked" for the CDS/AT1 arm.

**B4. The superseding hypotheses batch's registration** (b48-scoreboard, B49 "Box command (Ari's; inside a window)"; B49 Part 1(d)). **No dry run exists**: the manifest is the record, written first.
```
.venv/bin/python -m alpha.manifest register alpha/research/hypotheses-2026-10-20-supersedes-2026-10-14.yaml
```
- **Expect** five registrations, none screened out, each taking its original's status.
- **Expect** each original (2026-10-14-claude-weekly-01, H-001 to H-005) to move to `refined`, with its successor named.
- The manifest is written first, under the research directory, at the run's instant. The 14 Oct file is not edited, and its eight hash pins stand.

**B5. The narrative pair** (a53-batch12, section 3 and needs-you 5). Nothing to run: `ai_excess_orderly_flush` and `estimates_overshoot_reckoning` enter as PROPOSED at the register's next seed. ⚑ Confirm or reject each yourself: `python -m altdata.narratives confirm <id>` or `reject <id>`. Both are on the sessions' deny list.

---

## D. The ledgers' box editions, written outside the checkout

**None of the fourth chain's notes asks for a box edition.** The one new ledger, ST-R6.59c (the bank-stress base rate, a53), is scored by `tools/calibration/st_r6_59c_bank_stress.py` from public sources only and opens no store, so its laptop first edition (`docs/ledgers/st-r6.59c-ledger-2026-10-20.md`, FAIL, n 18) is the edition; a box run would read nothing the laptop did not. If you want one anyway, it writes outside the checkout:
```
mkdir -p ~/chester-data/ledgers
.venv/bin/python tools/calibration/st_r6_59c_bank_stress.py --out ~/chester-data/ledgers
```
- A dirty checkout breaks every wrapper's `git pull --ff-only`, so never let it write into `docs/ledgers/` on the box.
- Back to the laptop (from the laptop, in the repo): `scp 'vps:~/chester-data/ledgers/st-r6.59c-*' docs/ledgers/`, then ask a session to commit it.

---

## E. Read-only checks

**E1. The heartbeat and the drift check.**
```
bash scripts/check_heartbeat_cron.sh; echo "exit $?"
```
- **Expect** the same verdict as before the merge. The fourth chain adds no timer, so nothing new is due; the two new writers read PENDING until their first 16:10 run (or B3c), never STALE.

**E2. The volatile-day flag, all four arms** (a50-dealer-store, A51 Part 2).
- In the next 07:00 anchor (its email, or its archive `reports/morning_anchor_<session>.html`): the flag under the gauge, each arm with its reading and as-of, "Printed, not applied" at the end.
- In the next open note's dry run (`reports/dryrun/open_note_<session>.html`, until `live_from`): the "Volatile-day flag" block, with the gap settled from SPY's 09:30 open.
- **New on chain-4:** each live anchor also archives `reports/morning_anchor_<session>_volatile_day.json`, the flag exactly as printed, which the order gate reads at entry (below, E3). Check it exists after the first live anchor:
  ```
  ls -t reports/morning_anchor_*_volatile_day.json | head -2
  ```
- ⚑ A51's two session-set values (the index-mover rule; `min_atr_sessions` 15) wait for your confirm.

**E3. The entry stamp** (b48-scoreboard, B49 Part 3; chain-4 fix 4). Nothing to run, and **no migration**: the stamp lives in the decision's existing `gate_detail` JSON field. Your next `decide.py record` writes the Volatility and Gamma dials and the volatile-day flag as printed (`volatile_day`, `volatile_day_settled`, `volatile_day_source`) beside the Doctrine regime. A decision entered before 07:00 ET, or on a day no live edition printed the flag, stamps it absent with its reason.

**E4. The scoreboard** (b48-scoreboard). Read it at the top of Sunday's Weekly, above the précis:
```
.venv/bin/python -m register.scoreboard show
```
- **Expect** "accruing (n=k)" in every cell until it holds ten graded decisions, and "not built" for the benchmarks while a book holds an open decision.

**E5. 25 Oct: the Sunday news-block check** (a50-dealer-store, A51 needs-you 3). In the first Sunday evening note's dry run, read whether the Yahoo news items stop short of Friday. A Saturday news pull is proposed only if they do.

---

## The one pull request

**Open it in the afternoon** (inside 09:05–15:40 ET), so its merge lands inside a window:
- **base** `main`, **compare** `chain-4`;
- title: "chain-4: the fourth chain (a50-dealer-store, b48-scoreboard, a52-doctrine-2-pack), with three fixes and the Master Guide as built";
- body: the stitch notes' first line (`STITCH COMPLETE …`) and a link to `docs/briefs/chain-4-stitch-notes.md` and this sheet.

`chain-4` carries all three branches, so none of them merges on its own afterwards. a53 asks that the branch be on main **before the Monthly's last dry run on 28 October**.
