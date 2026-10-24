# The box sheet for the fifth chain (for Ari)

**What this is.** Every box step the fifth chain asks for, in order, for the evening `chain-5` merges to main and the weekend after it. `chain-5` carries chain-4 whole, so this sheet carries **chain-4's sheet in full** first (Part I, T1 the evening note's timer first), and then what each of the five later branches' notes asks for (Part II). Each step names its source:
- `docs/briefs/chain-4-box-sheet.md` (chain-4's sheet: T1, A, B, D, E), unchanged except where a later branch moves an expected count, each such change marked **chain-5**;
- `docs/briefs/a55-box-fixes-notes.md` ("The box commands, dry runs first", rounds 1 and 2);
- `docs/briefs/b51-registry-html-notes.md` ("Box commands");
- `docs/briefs/a56-batch14-a1-notes.md` ("The box commands, dry runs first");
- `docs/briefs/b52-batch14-a2-notes.md` ("Box commands");
- `docs/briefs/a54-relative-volume-notes.md` (OS-12c's box edition; OS-12d's backfill; "Needs you" 1 and 2).

**Dropped because an earlier sheet already ran it on 20 Oct.** The `.env` check of Massive's two flat-file keys (chain-3's sheet B, run 20 Oct) is not repeated before C9; if it printed `missing` that evening, set the keys first. Nothing else in these notes repeats a step chain-3's sheet ran; the FRED history (C1) and the store check (C5) are re-runs the notes ask for **again**, because the 20 Oct runs failed or miscounted.

**Read this first.**
- **Times are Eastern.** Every step runs inside a window: weekdays 09:05–15:40 or 17:20–23:30, **never 16:00–17:20**; weekends are open, clear of Sunday 05:00 (the Weekly). Tonight's window, Friday 23 Oct, closes at 23:30; Saturday and Sunday are open but for Sunday 04:30–06:00.
- **Every step is typed at the box prompt in the checkout** (`cd ~/chester-reports`) unless it says "from the laptop". Units are user units (`systemctl --user`). Logs are `~/logs/<name>-YYYY-MM.log`.
- **A dry run first** wherever one exists. It fetches and parses and writes nothing. Where a command has none, the sheet says so and names what it writes.
- **"Paste back"** means: send the output to a session if it differs from what is expected here.
- **⚑ marks a step that needs a decision from you.**
- Nothing here was run by a session, and no unit was enabled, started or restarted by one.

**The order, in one line.** Merge the PR (the end of this sheet), then T1 tonight; then A1, C0 and C1 tonight if the window allows; the rest Saturday (B, then C2 onward), with C9's backfill re-run until done. Sunday's 05:00 Weekly reads whatever has landed.

---

# Part I. Chain-4's sheet, in full

## Timers: what the self-deploy enables, and what is yours

**The fourth chain adds no unit and no timer, and does not change `DEPLOY_TIMERS`.** It fixes one timer's schedule (fix 5) and changes two unit files by comment only (a50-dealer-store, A51's "kept as a starting value" lines). **chain-5:** the four later branches add no unit, no timer and no `DEPLOY_TIMERS` entry either; a55 adds two warning-only blocks to `scripts/check_heartbeat_cron.sh` (the requirements check, and the FOMC audit on the 1st), which the next heartbeat runs from the pulled checkout.

| Unit | Change | Schedule | Who acts | Step |
|---|---|---|---|---|
| `chester-open-note.service` | comment only: `TimeoutStartSec` and the memory caps "kept 19 Oct 2026 as a starting value; reviewed after the first two live weeks" | unchanged (Mon–Fri 09:50) | nothing; the self-deploy copies it | — |
| `chester-evening-note.service` | the same comment | unchanged (Sun–Thu 21:30) | nothing; the self-deploy copies it | — |
| `chester-evening-note.timer` | **fix 5:** `OnCalendar=Sun..Thu 21:30` → `OnCalendar=Mon..Thu,Sun 21:30 America/New_York`. The same five evenings; systemd 255 refused the old range ("bad unit file setting") because its week runs Monday to Sunday | Sun–Thu 21:30 ET | **you enable it by hand**, after the self-deploy has copied it | T1 |

- Both are oneshot services, so neither is running when the self-deploy copies it, and no `restart_pending` should follow. If the heartbeat names either one anyway, `systemctl --user daemon-reload` is enough (the unit's behaviour is unchanged).
- `scripts/check_heartbeat_cron.sh` changes by one comment (the same line).
- The dealer store (A50) runs inside the existing capture and EOD units: **no unit of its own**, and the units already allow writes under `%h/chester-reports`.
- Batch 12's two new writers (`ofr_fsi`, `fdic_qbp`) are on `OFFICIAL_WRITERS`, so they ride the 16:10 EOD pass from the first session after the merge. No timer.

**T1. Enable the evening note's timer, after the merge** (chain-4 fix 5; it replaces chain-3's sheet C4 for this one timer, which the box refused on 20 Oct). The state drop-in from chain-3's C1 stays as it is.
```
git pull --ff-only && grep OnCalendar deploy/systemd/chester-evening-note.timer
grep OnCalendar ~/.config/systemd/user/chester-evening-note.timer
systemctl --user daemon-reload
systemctl --user enable --now chester-evening-note.timer
systemctl --user list-timers chester-evening-note.timer
```
- **Expect** both `grep` lines to read `OnCalendar=Mon..Thu,Sun 21:30 America/New_York`. If the second still reads `Sun..Thu`, the self-deploy has not run yet: wait for its next tick (every 30 minutes inside the windows), or run `bash scripts/deploy.sh` from the laptop.
- **Expect** `enable --now` to print the `Created symlink` line and no "bad unit file setting".
- **Expect** `list-timers` to show the next run at 21:30 ET on the next Sunday-to-Thursday evening. The box's clock is UTC, so while EDT lasts (to 1 Nov) it shows **01:30 UTC the next day**. **chain-5:** an enable on Friday 23 Oct shows Sunday 25 Oct 21:30 ET as **Mon 01:30 UTC**. From 1 Nov (EST) it shows 02:30 UTC.
- Before `live_from` (26 Oct) each run is a dry run under `reports/dryrun/`, mailed "[DRY RUN]". **chain-5:** Sunday's is the last dry run; its paragraph now aims at about 320 words under the 400 cap (a55 Part 2), so a withheld-for-length paragraph should not recur.

---

## A. The same evening as the merge: anything whose absence loses data

**Nothing in the fourth chain loses data by waiting a day.** The dealer store's backfill reads profiles already on disk under `data/computed/`, which stay there; the FRED legs, KRE and the two writers have their history at the source; the superseding batch is a registration. So A is one check. **chain-5:** nothing in the later branches loses data by waiting either; the eight new symbols' history is at the source (C7).

**A1. Confirm the merge has reached the box.**
```
git pull --ff-only && git log -1 --oneline
.venv/bin/python -c "from altdata import config; print(len(config.FRED_PULL_SERIES))"
.venv/bin/python -c "from altdata.sources import yfinance_source as y; print(len(y.SYMBOLS))"
```
- **Expect** the merge commit's line, then `277` (266, plus RSAFS from A51, plus Batch 12's ten), then **`124`** (**chain-5:** the second check is new: 115, plus KRE from Batch 12, plus b52's eight).

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

**B2. The retail-sales (RSAFS) history** (a50-dealer-store, A51 needs-you 4, "optional"). Its first rows come from the FRED pull after the merge; the deep history, from ALFRED at each value's first publication, is wanted if the open note's prior form is wanted before the next release. **chain-5:** C1's `--all` covers this series; run B2 or C1, not both.
```
.venv/bin/python -m altdata.secrets FRED_API_KEY
.venv/bin/python -m altdata.fred_history backfill --series retail_sales --dry-run
.venv/bin/python -m altdata.fred_history backfill --series retail_sales
```
- **Expect** `set`, then "FRED history -- 1 series, DRY RUN, nothing written" and the vintages it would write; then the same, writing, under source `fred:backfill`.
- `--series` takes the registered key (`retail_sales`), not the FRED id.

**B3. Batch 12's first pulls** (a53-batch12, section 7). Four parts, in this order.

*B3a. The ten FRED legs' first-print history (ALFRED).* They also arrive with the next 16:10 pull; this gives them their history. **chain-5:** C1's `--all` covers these ten too; run B3a or C1, not both.
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
- **Expect** each to print its JSON summary with `"status": "OK"` and a non-zero `written`: the OFR FSI daily from 2000 (`ofr.fsi`, `ofr.fsi_funding`, `ofr.fsi_credit`), and the FDIC's aggregate by quarter from Q1 2007 (`fdic.unrealised_total`, `_afs`, `_htm`).
- **Paste back** a STALE status: its reason names the refusal.

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

**B5. The narrative pair** (a53-batch12, section 3 and needs-you 5). Nothing to run: `ai_excess_orderly_flush` and `estimates_overshoot_reckoning` enter as PROPOSED at the register's next seed. ⚑ Confirm or reject each yourself: `python -m altdata.narratives confirm <id>` or `reject <id>`. Both are on the sessions' deny list. **chain-5:** C6's seed brings them in with a56's third proposal.

---

## D. The ledgers' box editions, written outside the checkout

**None of the fourth chain's notes asks for a box edition.** The one new ledger, ST-R6.59c (the bank-stress base rate, a53), is scored by `tools/calibration/st_r6_59c_bank_stress.py` from public sources only and opens no store, so its laptop first edition (`docs/ledgers/st-r6.59c-ledger-2026-10-20.md`, FAIL, n 18) is the edition; a box run would read nothing the laptop did not. If you want one anyway, it writes outside the checkout:
```
mkdir -p ~/chester-data/ledgers
.venv/bin/python tools/calibration/st_r6_59c_bank_stress.py --out ~/chester-data/ledgers
```
- A dirty checkout breaks every wrapper's `git pull --ff-only`, so never let it write into `docs/ledgers/` on the box.
- Back to the laptop (from the laptop, in the repo): `scp 'vps:~/chester-data/ledgers/st-r6.59c-*' docs/ledgers/`, then ask a session to commit it.

**chain-5:** two later ledgers do ask for box editions, C8 (ST-R6.66c) and C10 (OS-12c), under the same rule.

---

## E. Read-only checks

**E1. The heartbeat and the drift check.**
```
bash scripts/check_heartbeat_cron.sh; echo "exit $?"
```
- **Expect** the same verdict as before the merge. The fourth chain adds no timer, so nothing new is due; the two new writers read PENDING until their first 16:10 run (or B3c), never STALE.
- **chain-5:** a new **requirements** line follows the listings check, `requirements: all N satisfied`, or a WARNING naming what is missing and the fix (C0). It never changes the verdict or the exit code. The FOMC audit's lines print only on the 1st (the first is Sunday 1 Nov), also as WARNINGs.

**E2. The volatile-day flag, all four arms** (a50-dealer-store, A51 Part 2).
- In the next 07:00 anchor (its email, or its archive `reports/morning_anchor_<session>.html`): the flag under the gauge, each arm with its reading and as-of, "Printed, not applied" at the end.
- In the next open note's dry run (`reports/dryrun/open_note_<session>.html`, until `live_from`): the "Volatile-day flag" block, with the gap settled from SPY's 09:30 open.
- **New on chain-4:** each live anchor also archives `reports/morning_anchor_<session>_volatile_day.json` (under `$CHESTER_REPORTS_DIR` if it is set), the flag exactly as printed, which the order gate reads at entry (below, E3). Check it exists after the first live anchor:
  ```
  ls -t reports/morning_anchor_*_volatile_day.json | head -2
  ```
- ⚑ A51's two session-set values (the index-mover rule; `min_atr_sessions` 15) wait for your confirm.
- **chain-5:** the first live anchor after the merge is Monday 26 Oct's. Its OS-9 table may also carry "volume flag yesterday" for a name Friday's close did not flag, since Friday's close ran before the merge; from Monday's close on, the relative-volume table prints among the close's detail tables (a54).

**E3. The entry stamp** (b48-scoreboard, B49 Part 3; chain-4 fix 4). Nothing to run, and **no migration**: the stamp lives in the decision's existing `gate_detail` JSON field. Your next `decide.py record` writes the Volatility and Gamma dials and the volatile-day flag as printed (`volatile_day`, `volatile_day_settled`, `volatile_day_source`) beside the Doctrine regime. A decision entered before 07:00 ET, or on a day no live edition printed the flag, stamps it absent with its reason. The reader looks in the same archive the reports write (`$CHESTER_REPORTS_DIR`, else `reports/` from the checkout), so run `decide.py` from the checkout, as every step here is.

**E4. The scoreboard** (b48-scoreboard). Read it at the top of Sunday's Weekly, above the précis:
```
.venv/bin/python -m register.scoreboard show
```
- **Expect** "accruing (n=k)" in every cell until it holds ten graded decisions, and "not built" for the benchmarks while a book holds an open decision.

**E5. 25 Oct: the Sunday news-block check** (a50-dealer-store, A51 needs-you 3). In the first Sunday evening note's dry run, read whether the Yahoo news items stop short of Friday. A Saturday news pull is proposed only if they do.

---

# Part II. What the later branches add

Run after A1, one at a time. C0 and C1 tonight if the window allows; the rest from Saturday morning. **chain-5 changed none of these commands**; each is the branch's own, read against the merged code.

**C0. The requirements check** (a55 Part 5; its box commands). Read-only; **no dry run needed**, it installs nothing.
```
.venv/bin/python -m altdata.requirements_check; echo "exit $?"
```
- **Expect** `requirements: all N satisfied` and `exit 0`. The fifth chain adds nothing to `requirements.txt`, so this confirms 20 Oct's hand install (jsonschema) holds.
- If it prints `requirements: missing … -- fix on the box: .venv/bin/pip install -r requirements.txt`, run that fix, then the check again. **Paste back** anything out of range.

**C1. The FRED history, again** (a55 Part 1; its box commands). What failed on 20 Oct first, then the backfill over every series; rows already stored are skipped. Its windows are now 1,900 vintages, so the "2001 vintage dates" refusal should not recur.
```
grep FAILED ~/logs/fred_history.log
.venv/bin/python -m altdata.secrets FRED_API_KEY
.venv/bin/python -m altdata.fred_history backfill --all --dry-run
.venv/bin/python -m altdata.fred_history backfill --all
```
- **Expect** the `grep` to list 20 Oct's failed series (`yield_30y` among them, "There are 2001 vintage dates…"). **Paste back** the list.
- **Expect** `set`, then "FRED history -- 277 series, DRY RUN, nothing written", the per-series lines and a closing "N rows would be written (0 written); k refused, 0 failed".
- **Expect** the real run's last line to read "… 0 failed" and exit 0. It is long: start it early in the window. It covers B2's and B3a's series too.
- **Paste back** any `failed` line.

**C2. One news pull, the probe first** (a55 Part 3; its box commands). The BLS feeds send the one contact, `CHESTER_SEC_CONTACT`, read from `.env` at run time.
```
.venv/bin/python -m altdata.secrets CHESTER_SEC_CONTACT
.venv/bin/python -m altdata.events_ingest probe --only news
.venv/bin/python -m altdata.events_ingest pull --only news
```
- **Expect** `set`. `probe` is the pull's dry run: it fetches and parses and writes nothing.
- **Expect** `bls_empsit` and `bls_cpi` to read OK with items, not 403. With the key `missing`, both read **pending** with "the host asks for a contact in the User-Agent, and CHESTER_SEC_CONTACT is not set", and no request is made. ⚑ That is a55's needs-you 1, the alias address (below).
- **Expect** the pull to write the items the probe listed.

**C3. The claims writer: the FOMC history, the probe first** (a55 round 2; its box commands). **This must run before C4.**
```
.venv/bin/python -m altdata.events_ingest probe --only claims
.venv/bin/python -m altdata.events_ingest pull --only claims
```
- **Expect** the probe to list `cal.fomc_history`'s statements: one `scheduled` event per statement, 239 of them (4 Feb 1994 to 10 Dec 2025), keys `fomc-<date>`, source `claims_registry`, beside 2026's and 2027's.
- **Expect** the pull to write them. A re-run writes nothing new.

**C4. The event base rates, after C3** (a55 Part 4 and round 2; its box commands). **`compute` has no dry run**; `show` reads first.
```
.venv/bin/python -m alpha.event_rates show
.venv/bin/python -m alpha.event_rates compute
.venv/bin/python -m alpha.event_rates show
```
- **Expect** the first `show` to print the stored base rates, the FOMC buckets with n = 0 (the reader missed the writer's `claims_registry` rows until a55).
- **`compute` writes `alpha.db`'s `event_base_rates` only** (the lab's own database; the store is read-only to it).
- **Expect** the second `show` to count FOMC events in the hundreds: a55 counted **243** on the laptop (the history's 239 less two Sunday statements, plus this year's six past decisions). The box's count follows its own price window. **Paste back** a count far from 243.

**C5. The FOMC audit's first run** (a55 round 2; its box commands). Read-only: it reads one page and writes nothing, so **no dry run is needed**.
```
.venv/bin/python -m altdata.fomc_audit check; echo "exit $?"
```
- **Expect** a clean read (exit 0): the file's 2021–2027 dates match the Board's calendar, the last 8 Dec 2027. Exit 1 names a MISSING or CHANGED meeting, exit 2 an UNREADABLE page. **Paste back** either.

**C6. The store check, read-only, and the synthetic rows' purge as a DRY RUN only** (b51; its box commands).
```
.venv/bin/python -m tools.check_store_registry --db data/chester.db
.venv/bin/python -m altdata.purge_synthetic --dry-run --db data/chester.db
```
- **Expect** the check's header to print "last completed session <date> (ET)", Friday's date on Friday evening or the weekend:
  - list 1 down to the 59 `synthetic.*` keys alone (the 62 of 20 Oct less `market_state`, `fred.series_release_map` and `yfinance.mkt_usdcnh`, now declared);
  - list 3 much shorter than 20 Oct's 978, each key past three times its allowance marked "dead?"; **chain-5:** H.8's two deposit series and Shiller's real home price now carry their publication lags (`fred_h8_weekly`, `shiller_housing`), so a merely late print of them does not list;
  - list 4 still `'synthetic'`.
- **Paste back the stale list, the "dead?" lines first.** Each key on it is either a family to add with its real lag or a stopped writer to fix, never an allowance to widen.
- **Expect** the purge's dry run to print 28,980 rows in 59 keys and "dry run: nothing deleted".
- ⚑ **The apply waits for your ruling** (b51 needs-you 2): quarantine (a registry line, nothing deleted) or removal. Do not run `--apply` from this sheet.

**C7. a56's first pulls: Shiller's housing sheet, then the narrative seed** (a56; its box commands). The page check is read-only; the pull and the seed write.
```
.venv/bin/python -c "from altdata.sources import _publication as p, shiller as s; print(p.find_link(s.PAGE, s.HOUSING_LINK))"
.venv/bin/python -m altdata.sources.shiller
.venv/bin/python -m altdata.narratives seed
.venv/bin/python -m altdata.narratives list
```
- **The page check is the dry run** (the pull has none): **expect** the URL of `Fig3-1.xls` on shillerdata.com. **Paste back** an error: the pull would then write CAPE without the housing sheet (it says so in a warning).
- **Expect** the pull's JSON with `"status": "OK"`, `shiller.real_home_price` among its keys (annual 1890–1952, monthly from 1953, July 2026 last as of 6 Oct).
- **Expect** the seed to enter `gse_mbs_purchase_floor` as PROPOSED (origin `config_proposal`), with chain-4's pair (B5) if no seed has run since. `list` shows all three.
- ⚑ Confirm or reject each yourself (`python -m altdata.narratives confirm <id>` / `reject <id>`); both are on the sessions' deny list.

**C8. b52's eight symbols, their five-year history, the reads, and the wealth-effect ledger's box edition** (b52; its box commands). The eight read nothing until their history lands.
```
.venv/bin/python tools/backfill_prices.py --symbols SMH,MU,AMD,GRID,ANET,VRT,PAVE,ASML --years 5 --dry-run
.venv/bin/python tools/backfill_prices.py --symbols SMH,MU,AMD,GRID,ANET,VRT,PAVE,ASML --years 5
.venv/bin/python -m altdata.capex_chain show
.venv/bin/python -m altdata.transmission show
```
- **Expect** the backfill's dry run to print "price backfill -- 8 symbols, 5y" and the rows it would write; then the same, writing (close and volume, `yfinance.mkt_smh` and the rest).
- **Expect** `capex_chain show` to print BNP Paribas's table (August 2026) with its caveat, then the relative line, each bucket against SPY over three months (or "not enough history" until the backfill lands).
- **Expect** `transmission show` to print the four legs side by side (items 34, 36, 41 and the wealth-effect impulse), each read on its own scale, a leg without data "not read".

*The ledger's box edition, written outside the checkout* (public sources only; no store opened). **It has no dry run**, so the first run writes to a scratch directory, as a54's ledger does:
```
mkdir -p ~/chester-data/ledgers-dryrun ~/chester-data/ledgers
.venv/bin/python tools/calibration/st_r6_66c_wealth_effect.py --box --out ~/chester-data/ledgers-dryrun
.venv/bin/python tools/calibration/st_r6_66c_wealth_effect.py --box --out ~/chester-data/ledgers
```
- **Expect** both to print **FAIL, n 65** on the same public sources as the laptop's first edition. **Paste back** a different verdict or n.
- Back to the laptop (from the laptop, in the repo): `scp 'vps:~/chester-data/ledgers/st-r6.66c-*' docs/ledgers/`, then ask a session to commit it.
- The voices scan reads JDI Research's feed at its next 06:15 run; nothing to run by hand. ⚑ b52's needs-you 6: confirm it, or set it `enabled: false`.

**C9. a54's flat-file volume backfill** (a54, OS-12d; needs-you 1). The two keys were checked on 20 Oct (chain-3's sheet B), so that line is not repeated. Re-run `--max-days 25` until `--status` shows nothing to do: the sessions done before a54 are redone once for their volume.
```
.venv/bin/python tools/massive_flatfiles_backfill.py --dry-run
.venv/bin/python tools/massive_flatfiles_backfill.py --max-days 25
.venv/bin/python tools/massive_flatfiles_backfill.py --status
```
- **Expect** the dry run to list the sessions it would read, those done before a54 among them (their state lacks `"volume": true`).
- **Expect** each real run to take at most 25 sessions and write `chain.options_volume`, `chain.call_volume` and `chain.put_volume` under the flat-file source, beside the closes; idempotent, so only the volume rows are new.
- **Expect** `--status` to show the state file's `"volume": true` and, at the end, nothing left to do.
- Never 16:00–17:20 on a weekday. It is long; the weekend is the natural time.

**C10. a54's OS-12c ledger, box edition** (a54, Part 2; needs-you 2). **Only once 20 or more capture sessions per name are stored**; before that it reads INSUFFICIENT, as the laptop's did (n 0). Dry run to a scratch directory first, as a54 wrote it:
```
.venv/bin/python tools/calibration/os12c_relative_volume.py --box --out ~/chester-data/ledgers-dryrun
.venv/bin/python tools/calibration/os12c_relative_volume.py --box --out ~/chester-data/ledgers
```
- **Expect** INSUFFICIENT under 30 flagged or 30 unflagged name-days or 5 names, with its n; PASS or FAIL beyond. Copy back by `scp` as in C8 and ask a session to commit it.

**C11. The read-only re-checks after Part II.**
```
bash scripts/check_heartbeat_cron.sh; echo "exit $?"
```
- **Expect** E1's verdict and the requirements line. The eight new symbols read fresh after C8 (the daily allowance holds them); `shiller.real_home_price` after C7.

---

## The needs-you items this sheet meets (⚑)

1. **a55's alias address** (a55 needs-you 1, as a55 wrote it): "put it in `.env` as `CHESTER_SEC_CONTACT` (the one key; the senders are listed above). Name only, never in a file." C2 reads pending until it is set.
2. **b51's synthetic rows** (C6): quarantine or removal. The apply is not on this sheet.
3. **The narrative proposals** (B5, C7): three to confirm or reject.
4. **The JDI Research feed** (C8): confirm, or `enabled: false`.

The full needs-you list is in `docs/briefs/chain-5-stitch-notes.md`.

---

## The one pull request

**Open it once chain-5's CI is green, and merge it before 23:30 ET the same evening** (tonight's window is 17:20–23:30; if it slips, Saturday is open, clear of Sunday 05:00):
- **base** `main`, **compare** `chain-5`;
- title: "chain-5: the fifth chain (chain-4, a54-relative-volume, a55-box-fixes, b51-registry-html, a56-batch14-a1, b52-batch14-a2), with two fixes and the Master Guide as built";
- body: the stitch notes' first line (`STITCH COMPLETE …`) and a link to `docs/briefs/chain-5-stitch-notes.md` and this sheet.

`chain-5` carries all six branches, chain-4 among them, so none of them merges on its own afterwards, and chain-4's own pull request (if one is open) is closed unmerged. The secondary notes go live on Monday 26 Oct and the Monthly's last dry run is Wednesday 28 Oct: both read main, so the merge goes in before either.

After the merge (from the laptop, read-only): `ssh vps systemctl --user list-timers` shows the roster unchanged but for T1's evening-note timer.
