# The box sheet for the feed repair (for Ari): Tuesday 27 October 2026, evening

**What this is.** Every box step `a61b-feed-repair` asks for, in order, for the evening it merges to main **alone** (D29.1; it merges before the Monthly's last dry run, and chain-7 then takes main, D31.5). Each step gives the exact command, what to expect, and when to stop. The sources:
- `docs/briefs/a61b-feed-repair-notes.md` ("The box sheet", and the A64 section);
- the rulings of 24 Oct (D29.1–D29.3, D29.5) and of 24 Oct evening (D31);
- `docs/briefs/b52-batch14-a2-notes.md` ("Box commands": the wealth ledger's box edition).

Every command below was checked against the code on this branch. Where the notes named a path or a flag the code does not have, this sheet follows the code, and the end of the sheet lists the corrections.

**Read this first.**
- **The window: Tuesday 27 Oct, 17:20–23:30 ET. Never 16:00–17:20**, while the EOD pass (16:10) and the close (16:45) run. If the merge slips past 23:30, the whole sheet waits for the next evening's window.
- **Typed at the box prompt** (`ssh vps`, user `ari`), in the checkout: `cd ~/chester-reports`, unless a step says "from the laptop". Units are user units. The logs are `~/logs/<name>-YYYY-MM.log`.
- **The store** is the checkout's `data/chester.db`. The live CSV store is under `~/chester-data`.
- **A dry run first** wherever one exists. Where a command has none, the step says what it writes.
- **"Paste back"** means: send the output to a session if it differs from what is expected here.
- **⚑ marks a step that may need a decision.**
- Nothing here was run by a session, and no unit was enabled, started or restarted by one.

**The order, in one line.** B1 and B2 before the merge (each can stop the evening); the merge; then M1 to M10 in order, the same evening.

---

## B. Before the merge

**B1. The clock, and last night's backup.** The heartbeat of 24 Oct read `backup=failed:partial disk=warn:70%`. Merge only on a clean backup.
```
TZ=America/New_York date
CHESTER_STATE_DIR="$HOME/state" bash scripts/check_heartbeat_cron.sh; echo "exit $?"
ls -lt ~/backups | head -3
```
- **Expect** an ET time between 17:20 and 23:30.
- **Expect** the heartbeat's `backup=` field to read `ok`, and the newest zip under `~/backups` to be dated last night (the 02:30 sweep).
- **Stop** if `backup=` reads `failed` or `stale`. Re-run the sweep (`systemctl --user start chester-backup.service`), wait for it to finish (`systemctl --user status chester-backup.service`), and re-run the heartbeat line. If it still fails, do not merge tonight: paste back the heartbeat line and the newest lines of `~/logs/rclone_sync-$(date +%F).log` (one log a day).

**B2. ⚑ Did the feeds pull hit its 12-minute cap?** (D29.2, the fed_funds order.)
```
grep -n "feeds pull hit its 12-minute cap" ~/logs/run_eod-2026-10.log | tail -10
grep -n "fed_funds" ~/logs/run_eod-2026-10.log | tail -10
```
- **Expect** either no cap line (then go on to the merge as it stands), or cap lines on the days `fedfunds.futures_price` went stale.
- **If the cap was hit:** D29.2 rules one line folded into tonight's merge: `fed_funds` moves ahead of `prediction_markets` in `FEEDS` (`altdata/feeds.py`, line 96: `FEEDS = ("prices", "fred", "official", "external", "loggers", "bars", "prediction_markets", "fed_funds")`). **Stop and paste back the cap lines.** A session commits that one line to `a61b-feed-repair` and pushes, and the merge waits for its CI. The session does not merge.

---

## The merge

**Merge `a61b-feed-repair` into main, alone,** by its pull request (yours to open and merge), inside the window. Nothing else merges tonight. Chain-7's pull request comes after the 1 Nov Monthly (D31.1), from `chain-7-main`.

---

## M. After the merge, the same evening

**M1. The merge is on the box, and the counts.**
```
git pull --ff-only && git log -1 --oneline
.venv/bin/python -c "from altdata import config; print(len(config.FRED_PULL_SERIES))"
.venv/bin/python -c "from altdata.sources import yfinance_source as y; print(len(y.SYMBOLS))"
```
- **Expect** the merge commit, then `277` and `124`. a61b changes neither list, so they are main's figures.
- **Stop** if `git pull` refuses (a dirty checkout): paste back `git status`.

**M2. The deploy, from the laptop.** a61b changes no unit, no timer and no script, so this is the drift check and the heartbeat only.
```
bash scripts/deploy.sh; echo "exit $?"
```
- **Expect** `exit 0`, and the timer roster unchanged.
- **Stop** on `exit 3` (a changed unit that needs a restart, which this branch should not cause) or `exit 4` (drift after the copy): paste back the output.

**M3. The refused writers ask nothing.** They make no request at all, so there is nothing to dry-run.
```
.venv/bin/python -m altdata.sources.mba 2>&1 | tail -3
.venv/bin/python -m altdata.sources.farside 2>&1 | tail -3
```
- **Expect** each summary to read `"status": "REFUSED"`, `"written": 0`, with the reason "refuses automated reads since 2026-10-24".

**M4. AERO's labelled break, dry run first** (D29.3).
```
.venv/bin/python -m altdata.sources.llama pull --only basket --dry-run 2>&1 | tail -20
.venv/bin/python -m altdata.sources.llama pull --only basket 2>&1 | tail -10
```
- **Expect** the dry run to ask DefiLlama for `aero` (never `aerodrome`), to print the AERO rows only from 2026-10-21, and to name the break in its summary's `breaks`.
- **Expect** the pull to write those rows; no row before 21 Oct is written or restated.
- **Stop before the pull** if `aero` answers 4xx: the four `llama.*_aero` keys then fail by name, and stay on the expected-stale list. Paste back the dry run.

**M5. One FRED series through the repaired fetch.** There is no dry run; this writes one series, as the 16:10 pass would.
```
.venv/bin/python -c "from altdata.sources import fred; from altdata.store import Store; from altdata import config; s=[x for x in config.FRED_PULL_SERIES if x.key=='gdp_deflator']; print(fred.pull(Store(), series=s))"
```
- **Expect** a summary with `success` 1 and no failure.
- **Stop** if FRED's error now names its HTTP status and body (the repair's new message): paste it back. The rest of the sheet can go on.

**M6. The writers the repair touched.** None has a dry run; each writes what its 16:10 run writes.
```
.venv/bin/python -m altdata.sources.statcan_cpi 2>&1 | tail -5
.venv/bin/python -m altdata.sources.rent_indices 2>&1 | tail -5
.venv/bin/python -m altdata.sources.voices_scan run --only troweprice_insights --no-model 2>&1 | tail -5
```
- **Expect** StatCan to read `OK`, or `STALE` with a reason naming the body the box was sent.
- **Expect** rents to write Zillow only (Apartment List declared refused).
- **Expect** the voices scan to read T. Rowe Price within its 60-second timeout, with no model call.
- EDGAR's frames (`altdata.sources.edgar_xbrl`) have no dry run and are left to Wednesday's 16:10 pass.

**M7. The feed re-run.** No dry run; it writes what the 16:10 pass writes, under the same 12-minute cap.
```
timeout 12m .venv/bin/python -m altdata.feeds pull --skip loggers 2>&1 | tail -30; echo "exit $?"
```
- **Expect** every feed to report and `exit 0`.
- **On `exit 124`** (the cap), note which feed was running last, and paste back. Tonight's B2 decision is what moves `fed_funds` ahead.

**M8. The store check, with the expected stale count.**
```
.venv/bin/python -m tools.check_store_registry --db data/chester.db 2>&1 | tail -40
```
- **Expect about 100 stale keys, in a range of 80 to 130**, down from about 280 (the notes' reductions table). Declared keys (refused, superseded, gap, while held) are listed apart, never as stale.
- **Expected to stay stale, and why:**
  - `french.*`, `shiller.sp_dividend`, `shiller.sp_earnings`: no publisher states a lag (D29.5);
  - `yfinance.crypto_prl`, `_volume`: Yahoo's hole;
  - `bars.*`: until the evening note runs (21:30, Sun–Thu);
  - `fedfunds.futures_price`: if the cap was the cause;
  - `ca.cpi_*`: if the box still gets a non-JSON body;
  - `calc.infl_vol`: D3;
  - `llama.*_aero`: until a pull after 21 Oct lands (M4).
- The EIA rigs and the Cleveland Fed rules should **no longer** be stale (A64's lag families).
- **Above 130:** stop. Paste back the stale list, and the `dead?` list beside it, before any further step. Do not purge or repair anything by hand.

**M9. The wealth ledger's box edition** (b52's box commands; public sources, written outside the checkout).
```
mkdir -p ~/chester-data/ledgers
.venv/bin/python tools/calibration/st_r6_66c_wealth_effect.py --box --out ~/chester-data/ledgers
ls -l ~/chester-data/ledgers/st-r6.66c-*
```
Then, from the laptop:
```
scp 'vps:~/chester-data/ledgers/st-r6.66c-*' docs/ledgers/
```
- **Expect** the box edition to print `FAIL`, n 65, as the laptop edition did. D9 accepted that verdict as drafted.
- After the copy, ask a session to commit the two files (the ledger and its episodes CSV). Nothing here invents their content.

**M10. The heartbeat: `feed_stale` should clear.**
```
CHESTER_STATE_DIR="$HOME/state" bash scripts/check_heartbeat_cron.sh; echo "exit $?"
```
- **Expect** `exit 0`, healthy, or a verdict other than `feed_stale` (exit 11). The feeds the repair fixed now deliver, and the declared keys no longer count.
- **On `exit 11`:** the verdict line names each stale series with its reason. Paste it back; if it names only the expected-to-stay keys of M8, the evening is done.

---

## What this sheet corrected from the notes

| The notes said | The code says, and this sheet uses |
|---|---|
| The store check at `--db ~/chester-data/chester.db` | The store is the checkout's `data/chester.db` (the chain-5 sheet's path; `altdata/observations.DEFAULT_DB`) |
| The EOD log as `~/chester-data/logs/eod*.log` | `~/logs/run_eod-YYYY-MM.log` (`scripts/run_eod_cron.sh`, `LOG_DIR`) |
| The cap line as "hit its 12-minute cap" | The full line is "WARN feeds pull hit its 12-minute cap" (`run_eod_cron.sh`, line 180); the grep matches it |
| `voices_scan --only … --no-model` | The flags belong to the `run` subcommand: `voices_scan run --only … --no-model` |
| `edgar_xbrl --dry-run` | It has no dry run; its pull writes, so it is left to Wednesday's 16:10 pass |
| The evening note's log as `evening_note*.log` under `~/chester-data/logs` | Logs are under `~/logs`; the step is dropped here, as the note's bars only matter to M8's `bars.*` line |

**Not verified against the code:** the exact stale count after M7, which only the box's store can give; and whether `aero` answers on DefiLlama (the laptop's request was refused by the session's permission check on 24 Oct).
