# AUD-1 — the first fixes from the data and architecture audit (notes)

Built as session B from Ari's paste, amended at 11:57 ET on 14 Oct 2026 (ruled
09:27 ET). Branch `aud-1-data-fixes` from main at `cc91752`. Branch-only: pushed,
not merged, not deployed, nothing run on the box. Every box step is below for Ari
to run. The branch merges in the week of 19 Oct, after a later paste merges the
new main into it.

| Commit | Item |
|---|---|
| `4d71126` | 2. Security: SMTP certificates verified, fetch errors redacted, the ignore list widened |
| `ecef186` | 4. FRED duplicates: no re-stamps, the compaction tool, narrower reads, incremental recomputes |
| `01b9422` | 1. The space leak: retention, Drive pruning, the disk line, the report archive swept |
| `1b8a32b` | 5. The EOD job: chains first, retries, the completeness gate, ZEC, Massive (and 1a) |
| `9966835` | 3. The meme loggers: ApeWisdom whole, Reg SHO above a floor, ten sessions kept |
| `40d7536` | 5b follow-up: the chain retries are bounded |

**CI.** #390 (`ecef186`) **failed** on three gates, all mine and all fixed in
`1b8a32b`:

- `validate_official_sources` group Q: in item 4c's change to
  `feeds.freshness`, I reused the name `last`, which already held the session date.
- `validate_monthly`: its fake SMTP did not accept 2a's `starttls(context=)`.
- `validate_weekly_edits` rule 9: `validate_audit_1` used a bare
  `tempfile.mkdtemp`. It now uses `gate_tmp`.

#394 (`1b8a32b`) is **green**. The run for the last push is given in the report
that comes with this file.

No gate reads the live store or fetches. Gates were run locally one at a time:

| Gate | Result |
|---|---|
| validate_audit_1 (new, groups A–D) | 38/0 |
| validate_prices | 101/0 |
| validate_backup | 68/0 |
| validate_secrets | 47/0 |
| validate_heartbeat_caller.sh | 97/0 |
| validate_session_calendar.sh | 52/0 |
| validate_official_sources | 223/0 |
| validate_feeds_scheduled | 19/0 |
| validate_monthly | 350/0 |
| validate_weekly_edits | 90/0 |
| validate_weekly_stack | 68/0 |
| validate_deploy | 118/0 |
| validate_systemd_units | 75/0 |
| validate_regime | 404/0 |
| validate_derived | 45/0 |
| validate_events | 91/0 |
| validate_monthly_frames | 32/0 |
| check_registry | OK |

## 1. The space leak

| Fix | Where | Fixture |
|---|---|---|
| **1a** The EOD zip no longer carries `chester.db`. It keeps the chains and the pin log, with the CRC and file-count checks. The database's off-box copy is the nightly sweep's `db/` snapshot. | `run_eod.py` `backup_chains` | validate_backup B (three entries, no db) and C (a corrupt db no longer touches the zip) |
| **1b** The sweep keeps the newest 14 session zips in `~/backups/chains`. An older zip is deleted only when the remote listing has the **same name and the same size**. | `backup_retention.py --mode local-chains`, `rclone_sync.sh` `prune_zips` | validate_backup group_aud1 |
| **1c** Drive's `backups/chains` is pruned to 30 days by exact name. The newest zip is never pruned, and nothing is deleted unless tonight's zip is listed. | `backup_retention.py --mode zips` | validate_backup group_aud1, offline |
| **1d** The heartbeat's verdict line carries `disk=` for the disk under `$REPO/data` and the swap in use. It warns at 70% (`disk=warn:<n>%`). It alerts at 85% or on any swap, as **exit 15, `disk_alert`**, ranked below the backup and above a stale feed. The sweep refuses to stage a DB snapshot with less than twice the DB's size free (**exit 5, `disk_low`**). The EOD job no longer stages one at all (1a). | `check_heartbeat_cron.sh`, `rclone_sync.sh` | validate_heartbeat_caller "The disk and the swap" (72% warns, 86% alerts, swap alerts, a stale pipeline still wins). Every other case pins the disk reading so no case depends on the runner's disk. validate_backup covers `disk_low`. |
| **1e** The report archive `CHESTER_REPORTS_DIR` (default `$REPO/reports`) is swept as its own copy tree, `reports/`. The README said it was already swept. It was not, and the README now says so. | `rclone_sync.sh`, `deploy/systemd/README.md` | validate_backup group_aud1 |

The backup unit gains `-%h/backups/chains` in ReadWritePaths, because the local
prune deletes there. Its `TimeoutStartSec` goes from the previous cap to
`2h45min` for the added tree and the prune. See the needs-you list on unit files.

## 2. Security

| Fix | Fixture |
|---|---|
| **2a** `starttls(context=ssl.create_default_context())` in both SMTP senders: `daily_cascade/deliver.py` and `scripts/send_smtp_alert.py`. | validate_secrets H: the call receives a verifying context |
| **2b** `FetchError` redacts its message when it is built (`_base.py`). In `fred.py`, `fred_releases.py` and `feeds.py`, a logged exception goes through `secrets.redact()`: `log.exception` became `log.error` with the redacted `traceback.format_exc()`. | validate_secrets G: a connection error with `api_key=...` in its URL is logged without the key |
| **2c** `.gitignore` adds `.env*` (keeping `.env.example`), `*.db`, `*.sqlite`, `*.zip`, and the box's report outputs: the close PDF, payload and stack JSON, `morning_anchor_*`, `weekly_tactical_*`, `monthly_macro_*`. | validate_secrets H |

Five committed files match the new patterns. As the paste said, none were deleted:

- `reports/monthly_macro_2026-05-30.html`
- `reports/monthly_macro_2026-05-30.md`
- `reports/monthly_macro_2026-09-23.html`
- `reports/monthly_macro_2026-09-23.md`
- `reports/monthly_macro_2026-09-23_payload.json`

## 3. The meme loggers

- **3a ApeWisdom.** The all-stocks filter is stored whole: every ticker on every
  page the payload declares (`pages`). There is a cap of 60 pages and a 1-second
  pause between pages. Wallstreetbets stays the tracked universe on two pages.
- **3b FINRA Reg SHO. The choice is the liquidity floor, not the top 500 by
  short-volume ratio.** Each night stores the tracked universe plus every symbol
  with **at least 1,000,000 shares of FINRA-reported total volume**.
  - **Why:** the ratio is the quantity being logged, and selecting on it puts a
    name in the set on its noisiest days. A thin name prints 100% short volume on
    one market maker's fill. The name then drops out the day its ratio settles,
    so each series has holes exactly where it would be read. A floor on total
    volume is independent of the ratio, so membership is stable and a liquid
    name's history is continuous.
  - **Rows a day:** I measured two public files from the laptop, never the box.
    13 Oct 2026 has 12,237 symbols and 1,205 above the floor. 9 Oct 2026 has
    12,279 and 1,154. With three keys per name (`short_volume`,
    `short_exempt_volume`, `total_volume`), that is **about 3,500–3,600 rows a
    session, roughly 0.9M a year**. For comparison, the other floors keep
    2,097 / 1,978 names (500k), 3,157 / 3,016 (250k) and 4,697 / 4,532 (100k).
  - **Ten sessions:** the nightly pull fetches **every session missing from the
    last ten** (`pull_regsho_missing`), oldest first, not only the newest.
- **3c.** The registry entries for `finra.short_volume`, `finra.total_volume`,
  `finra.short_exempt_volume`, `apewisdom.mentions`, `apewisdom.rank` and
  `apewisdom.upvotes` describe the new instrument sets, and so does the logger's
  own description. `finra.total_volume`'s entry said "total consolidated volume".
  It is FINRA-reported venues only, and the entry now says so.
- **Fixture:** validate_audit_1 group D.
  - All three declared pages are read and untracked tickers are stored.
  - Wallstreetbets stays the universe.
  - The floor keeps the universe whatever its volume, keeps a symbol exactly at
    the floor, and drops one share below.
  - Of the ten sessions to 13 Oct, exactly the seven not stored are fetched.
  - A second night fetches nothing.

## 4. The FRED duplicates

- **4a.** The Store's dual write goes through `observations.drop_unchanged`.
  - Fixture (validate_prices `fred_dual`): two identical pulls write once, and a
    changed value writes one row.
  - `drop_unchanged` reads from the batch's earliest day, not the whole history.
- **4b.** `python -m altdata.compact_fred`, with `--dry-run`, `--apply --backup
  PATH` or `--list-scope`.
  - **Scope:** `fred.*`, `calc.surprise_vs_naive.*`, `calc.naive_expectation.*`,
    and the 34 FRED-derived `calc.*` keys from market_features' `MACRO_FEATURES ∪
    RATES_FEATURES`, as printed by `--list-scope`:
    - `calc.attr_acm_tp_share_20d`, `_60d`
    - `calc.attr_curve_share_5d`, `_20d`, `_60d`
    - `calc.attr_d10y_5d`, `_20d`, `_60d`
    - `calc.attr_dkw_path_share_20d`, `_60d`
    - `calc.attr_dkw_tp_share_20d`, `_60d`
    - `calc.attr_kw_tp_share_20d`, `_60d`
    - `calc.attr_real_share_5d`, `_20d`, `_60d`
    - `calc.corr_spy_tlt_60d`, `calc.infl_vol`, `calc.net_liquidity`,
      `calc.r_minus_g`, `calc.r_real_10y_core_pce`, `calc.r_real_10y_cpi`,
      `calc.real_wages_yoy`, `calc.sahm_rule`, `calc.yield_curve_2s10s`
    - `calc.yoy_ahe`, `calc.yoy_core_cpi`, `calc.yoy_core_pce`, `calc.yoy_cpi`,
      `calc.yoy_housing_starts`, `calc.yoy_m2`, `calc.yoy_pce`,
      `calc.yoy_real_gdp`
  - **What it keeps:** the first vintage of each run of identical values per
    (key, instrument, observed_at). It never deletes a differing vintage, and a
    value that returns after a revision is kept.
  - **Safeguards:** `--apply` refuses unless the same run made and
    integrity-checked the backup, and it refuses a backup path that already
    exists. It runs VACUUM only if free disk is more than twice the DB's size.
    The dry run prints rows per key.
  - **Exits:** 0 ok, 2 refused, 3 failed.
  - **Fixture:** validate_audit_1 group A, a synthetic store with re-stamps and
    one real revision.
- **4c.**
  - `as_of()` takes an optional `observed_from` lower bound.
  - `latest_as_of()` reads one indexed row instead of the whole history.
  - `drop_unchanged`, the feeds freshness check and the regime's presence check
    and stored-object read all use the narrow paths.
  - **Fixture:** validate_prices `asof_paths`. The answers match the full join at
    four cutoffs, a revision included. The query plan uses the index.
    `newest_observed_any` (below) matches the per-instrument loop at five cutoffs.
  - The regime's `METHOD_SOURCE_SHA` was refreshed through `regime method
    --update`. It is a non-semantic change, and `METHOD_VERSION` is unchanged.
- **4d.** `altdata.market_features compute` and `altdata.surprise compute` start
  from the newest stored day minus 120 days (`RECOMPUTE_WINDOW_DAYS`), unless
  `--from` or the new `--full` is given. Fixture: validate_audit_1 group B.

## 5. The EOD job

- **5a.** `run_eod_cron.sh` now runs in this order:
  1. `run_eod.py --capture-only`: Stage 1 and 1b and the completeness gate.
  2. The feeds, under `timeout 12m`. Exit 124 is logged and the run continues.
  3. Features, events and surprise, as before.
  4. `run_eod.py --skip-fetch`: compute, pins, backup and the state record.

  With no chains at all (exit 1), the feeds still run and the compute is skipped.
  Fixture: validate_session_calendar.sh.
  - The stub records that the capture's line precedes `feeds: pull start`.
  - The compute pass is `--skip-fetch`, and the feeds step carries the 12-minute cap.
  - Capture exit 5 ends the run at 5 with the compute still run and the heartbeat untouched.
  - Capture exit 1 ends at 1 with the feeds run and the compute skipped.
- **5b.** The Yahoo chain, expiry-list, spot-history and price-history calls retry
  three times with doubling backoff (2s, 4s), on an error or an empty frame. The
  helper is `_base.retry_call`.
  - **Bounded:** after three expiries in a row come back empty even with retries,
    the rest of that symbol gets one try each. Without that, a night Yahoo serves
    nothing would run about forty minutes, past `chester-eod.service`'s
    30-minute `TimeoutStartSec`. The unit would kill the run before the wrapper
    wrote its status.
  - **Fixtures:** validate_prices L (error, then empty, then a frame: three tries
    with the wait doubling; three failures re-raise). validate_audit_1 C (an empty
    expiry is retried and captured; 20 dead expiries cost 26 calls, not 60).
- **5c.** `altdata/chain_completeness.py` holds the gate.
  - **Floors:** below 12 of 13 symbols, or below 90% of the expiries the captured
    symbols listed, the run exits **5 (incomplete)** and the heartbeat is not
    touched.
  - **Record:** `<CHAIN_DIR>/<day>/_completeness.json`. The 16:45 close reads it
    into its warnings, as "EOD capture: …" lines in the stacked close's Warnings
    table.
  - **Full runs:** a manual full `run_eod.py` also ends at 5 when its own capture
    was short.
  - **Fixture:** validate_audit_1 C. 12 of 13 passes and 11 fails; 89% fails and
    90% passes; the record round-trips.
- **5d.** The ZEC logger's closes go through `drop_incomplete_bars`. ZEC-USD joins
  `CONTINUOUS_SYMBOLS`, so its bar is finished once its UTC day has ended.
  validate_prices' declared-set check was updated to include it. Fixture:
  validate_prices L, where the 14 Oct bar is held back at 20:00 UTC on 14 Oct.
- **5e.** Massive stays on, and no pause flag was added.
  - **Order:** Stage 1b runs inside the capture pass, after the yfinance chains
    and before the feeds.
  - **Retries:** the same three tries, except on a day `empty_is_expected()`
    says is empty.
  - **No key:** without the key it prints "Massive key not set -- SPX and SPCX
    not captured", sets `key_missing`, and nothing raises.
  - **Counting:** its completeness is counted apart (`vendor`), so a missing SPX
    does not fail the capture but is named in the close.
  - **Fixture:** validate_audit_1 C.

## Box commands, for Ari. Not run.

None of these can run before the merge in the week of 19 Oct: the tools exist
only on this branch. Run them inside a window.

**Compaction window: weekday 18:00–23:00 ET.** The 16:45 close has finished,
`chester-ibkr-sync` (09:00–17:00 every 30 minutes) has stopped writing, and the
02:30 sweep has not started. Saturday daytime also works.

**Check the disk first.** The backup and VACUUM need room. Read the time in ET
through Python's `zoneinfo`, not Git Bash.

```
ssh vps 'df -h ~ ; ls -l ~/chester-reports/data/chester.db ; du -sh ~/backups/chains ; ls ~/backups/chains | wc -l'
```

**1. Compaction dry run.** It reads only, and prints rows to delete per key.

```
ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.compact_fred --dry-run'
```

**2. Compaction apply.** Run it only after reading the dry run, and only if
`df` shows at least twice the DB's size free. The backup path must not already
exist.

```
ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.compact_fred --apply --backup ~/backups/chester-pre-compact-$(date +%F).db'
```

- Exit 0 means done. Exit 2 means it refused, with the reason printed, and
  nothing was deleted. Exit 3 means it failed after the backup, and the backup
  holds every row.
- Keep the backup until a Weekly and a close have rendered cleanly, then delete
  it yourself.

**3. A first manual prune of old zips, only if the disk needs it.** It is needed
if `df` shows more than 70% used. Each old zip carries a full `chester.db`, which
is the leak 1a stops. The sweep prunes them itself from its first night after the
merge, so this is only for not waiting.

List what the plan would delete. This prints names and deletes nothing.
`<remote>` is the value of `CHESTER_RCLONE_REMOTE` on the box.

```
ssh vps 'cd ~/chester-reports && rclone lsf <remote>/backups/chains --files-only --format sp --separator ";" > ~/.chester/remote_chains.lsf && find ~/backups/chains -maxdepth 1 -name "chains_*.zip" -printf "%s;%f\n" | .venv/bin/python scripts/backup_retention.py --mode local-chains --remote ~/.chester/remote_chains.lsf'
```

Then remove each printed name yourself, after reading the list, as
`rm ~/backups/chains/<name>`.

**4. After the first night on the new code**, check the order, the timings and
the new lines:

```
ssh vps 'grep -E "chains: capture|completeness|gap:|feeds: pull|run end" ~/logs/run_eod-$(date +%Y-%m).log | tail -20'
ssh vps 'grep -E "disk:|verdict=" ~/logs/heartbeat_check-*.log | tail -4'
ssh vps 'tail -5 ~/logs/rclone_sync-*.log'
```

## Files shared with other branches

These are `git diff --name-only` from each branch's merge-base with
`origin/main`, intersected with this branch's 37 files. **t3-6-monthly-polish
shares none.**

| Branch | Shared files |
|---|---|
| w-1-3c-weekly-polish | CLAUDE.md, Makefile, altdata/feeds.py, altdata/loggers/shielded.py, altdata/market_features.py, altdata/sources/_base.py, altdata/sources/yfinance_source.py, deploy/systemd/README.md, deploy/systemd/chester-backup.service, metrics_registry.yaml, run_eod.py, scripts/rclone_sync.sh, scripts/run_eod_cron.sh, tools/validate_backup.py, tools/validate_prices.py |
| alpha-lab-2 | .gitignore, CLAUDE.md, Makefile, deploy/systemd/README.md, deploy/systemd/chester-backup.service, scripts/rclone_sync.sh, tools/validate_backup.py |
| t3-6-monthly-polish | none |
| vp-1-volume-profile | CLAUDE.md, Makefile, metrics_registry.yaml, scripts/run_eod_cron.sh |

**Friday's 23 stitched branches.** I took these to be the 30 unmerged branches
less the four the paste names, alpha-lab-1, this branch and
aud-2-ops-security: aq-1, aq-2-chapters-1/-2, aq-3-series-1/-2, aq-4, aq-5,
aq-6, aq-7, aq-8a, aq-9a, aq-10, b3-tranche-a, c1-move-screen, crypto-basket,
el-1-packets, el-2-3-rollup, imf-ifs-gold, lib-aq14-em-paper, sr-36, sr-37-38,
sr-38-inbox and sr-43-49. They stack on one another, so the sets are cumulative.

- **Every one of the 23 shares:** CLAUDE.md, Makefile, altdata/market_features.py,
  altdata/sources/yfinance_source.py, metrics_registry.yaml and
  tools/validate_prices.py.
- **All but aq-5 also share:** run_eod.py and scripts/run_eod_cron.sh.
- **All but aq-5, aq-6 and aq-8a also share:** altdata/feeds.py.
- **Fourteen also share:** altdata/sources/_base.py, chester-backup.service,
  rclone_sync.sh and validate_backup.py. These are aq-2-chapters-1/-2,
  aq-3-series-2, aq-7, aq-10, b3-tranche-a, c1-move-screen, crypto-basket,
  el-1-packets, el-2-3-rollup, lib-aq14-em-paper, sr-36, sr-37-38, sr-38-inbox
  and sr-43-49.
- **altdata/loggers/shielded.py:** aq-10, crypto-basket, el-1, el-2-3 and
  lib-aq14.
- **deploy/systemd/README.md:** aq-2-chapters-1/-2, aq-7, aq-10, b3, c1,
  crypto-basket, el-1, el-2-3, lib-aq14 and sr-38-inbox.

**Not named in the paste:**

- **aud-2-ops-security** shares CLAUDE.md, Makefile, deploy/systemd/README.md,
  chester-backup.service and validate_backup.py.
- **alpha-lab-1** shares CLAUDE.md, Makefile, deploy/systemd/README.md and
  rclone_sync.sh.

**Where the merge will need care:**

- `scripts/run_eod_cron.sh`: the reorder rewrites the middle of the file, and
  vp-1 and the aq chain also edit it.
- `run_eod.py`.
- `scripts/rclone_sync.sh` and `chester-backup.service`'s `TimeoutStartSec` and
  ReadWritePaths: alpha-lab-2 and aud-2 change them too.
- The gate count in CLAUDE.md and the Makefile line: this branch adds one gate,
  `validate_audit_1`, and says "fifty-eight code gates (fifty-five Python".

## Choices the paste did not name

- **Exit codes.** Heartbeat exit **15** is `disk_alert`, since 0–5 and 8–14 were
  taken. `run_eod.py` exit **5** is `incomplete`. The sweep's exit **5** is
  `disk_low`.
- **The disk line measures `$REPO/data`,** where `chester.db` lives, falling back
  to `$HOME`. It can be overridden with `CHESTER_DISK_PATH`.
- **5a splits `run_eod.py` into two passes** with the new `--capture-only` flag,
  rather than moving the feeds inside `run_eod.py`.
- **The 5b retry bound** (three dead expiries, then one try each), added to stay
  inside the EOD unit's 30 minutes.
- **ZEC-USD in `CONTINUOUS_SYMBOLS`.** It is the declared set the unfinished-bar
  rule reads, and validate_prices' exact-set check was updated with a comment.
- **Two new store reads.**
  - `ObservationStore.days_present(key, since)` answers which of the last ten
    Reg SHO sessions are stored.
  - `ObservationStore.newest_observed_any(key, as_of)` serves the freshness
    check. Its per-instrument loop would have asked thousands of queries a key
    now that the loggers store the whole all-stocks feed and about 1,200 Reg SHO
    names.
- **ApeWisdom's page cap is 60, with a 1-second pause between pages,** for a free
  keyless API.
- **The `finra.total_volume` description was corrected:** the file reports FINRA
  venues, not the consolidated tape.

## Needs you

1. **The `chester-backup.service` edit.**
   - **What changed:** ReadWritePaths gains `-%h/backups/chains`, and
     `TimeoutStartSec` becomes `2h45min`.
   - **Why:** 1b cannot delete a local zip without the first, and the sweep now
     copies one more tree and prunes.
   - **Your ruling:** the paste's rules say "Do not touch … units". I read that as
     the installed units on the box, which nothing here touches; the change is a
     repo file that reaches the box only through the self-deploy after the merge.
     If you meant the repo's unit files too, revert that hunk and 1b's local
     prune will fail read-only on the box.
   - **After the merge:** the self-deploy installs it. The unit is a oneshot run
     by its timer, so a restart should not be pending. If the heartbeat says
     `restart_pending`, the restart is yours.
2. **The compaction**, dry run then apply, from the commands above, after the
   merge and inside a window.
3. **A first prune of old zips**, only if `df` shows more than 70% used.
4. **Timing of the reordered EOD night.** The capture now runs before the feeds.
   I could not find a recorded capture duration in the repo, so check the first
   night's `chains: capture end` and `feeds: pull done` times against the 16:45
   close (command 4). If the capture runs long, the 16:45 object reads the
   previous session's prices for the legs that pull had not reached.
5. **Storage growth.** Reg SHO grows by about 3,500–3,600 rows a session.
   ApeWisdom all-stocks grows by three keys per ticker on every page, its size
   set by the payload. Both pass `drop_unchanged`, but a new day is new rows.
   The 1d disk line is the watch on both.

## 14 Oct evening — the follow-ups, ruled

Ari ruled on the needs-you list above on the evening of 14 Oct. This section
records what was built from those rulings. Where it and the sections above
disagree, this section is current.

**Step 0.** CI #395 (`4daf4c4`) finished **green**.

### The merge of w-1-3c-weekly-polish

Merged `origin/w-1-3c-weekly-polish` at **`fb67bf3`** (it had not moved), as
merge commit **`608c4e0`**, pushed on its own before the changes below. Six
conflicts, each resolved by keeping both sides:

| File | Resolution |
|---|---|
| `CLAUDE.md` | w-1-3c's sentence, with the gate count recounted from the Makefile's list: **seventy-five code gates (seventy-two Python, three shell) and six data gates**. w-1-3c's text said 74 and five; the list holds 75 and six (it added `validate_imf_china` as a data gate). |
| `Makefile` | w-1-3c's six gates, then `validate_audit_1`. |
| `altdata/sources/yfinance_source.py` | w-1-3c's continuous set, which already holds ZEC-USD (AQ-5) and the crypto basket; the AUD-1 5d reason kept as a comment. |
| `deploy/systemd/chester-backup.service` | ReadWritePaths is the union: `inbox/aaii`, `inbox/spdji`, `inbox/etf` and `backups/chains`, with both sides' comments. |
| `scripts/rclone_sync.sh` | AUD-1's zip prune, then w-1-3c's `pull_inbox_file` (AAII and S&P DJI, which replaced the AAII-only pull) and the GLD archive pull. |
| `tools/validate_prices.py` | w-1-3c's declared set (a superset of AUD-1's), the AUD-1 note kept. |

The merge was checked locally before the push: validate_backup 70/0,
validate_prices 101/0, validate_audit_1 38/0, validate_systemd_units 85/0,
check_library 0 failures.

### The changes

1. **The unit file, ruled.** Repo unit files are code. `-%h/backups/chains`
   stays in ReadWritePaths. `TimeoutStartSec` is back to main's `2h30min`: that
   line is aud-2's, which sets `2h` when it merges. The unit's diff against main
   is now only the ReadWritePaths union and its comments.
2. **One budget for the sweep** (`scripts/rclone_sync.sh`), in place of trimmed
   caps.
   - The budget is **105 minutes from the sweep's start**
     (`CHESTER_SWEEP_BUDGET_MIN` overrides it). Each tree's cap is the smaller of
     its own cap and the minutes left, less 2.
   - With under 3 minutes left a tree is skipped, logged `SKIP <tree> -- sweep
     budget spent`, and named in FAILED as `<tree>(budget)`, rc 3.
   - The db/ prune, the chain-zip prune and the inbox pulls start only with at
     least 10 minutes left; otherwise they log `deferred to the next night` and
     are not a failure. A prune stops deleting when fewer than 2 minutes (one
     delete's own cap) are left.
   - **Beyond the ruling's words:** the ruling named "the AAII copy". Since the
     merge, that copy is `pull_inbox_file`, which also pulls S&P DJI's workbook,
     and w-1-3c added the GLD archive pull. All three are under the 10-minute
     rule, and the GLD loop stops between files with under 7 minutes left (its
     5-minute copy cap plus the 2).
   - Tree order: db, data, chester-data, state, reports, backups. The zips go last.
   - The backups tree excludes `/chester-pre-compact-*.db`, so the compaction's
     safety copy never leaves the box unencrypted.
   - The header comment says why a budget: trimmed caps fit tonight's trees, but
     the lab's copies on alpha-lab-2 and the next tree would break the sum again.
     A budget holds whatever is added, and the sweep always writes its own status
     line before systemd's ceiling.
   - Fixtures need a fake clock, so `CHESTER_SWEEP_CLOCK` (a file of epoch
     seconds) stands in for `date +%s` when set. Unset on the box.
   - `deploy/systemd/README.md`'s stall paragraph no longer says 2h45min and
     describes the budget.
3. **The swap rule, corrected** (`scripts/check_heartbeat_cron.sh`).
   - Swap: **warn above 512 MiB, alert above 1 GiB**.
   - Memory: **alert when MemAvailable is under 10% of MemTotal**.
   - The disk thresholds stay (warn 70%, alert 85%). An alert is still exit 15,
     `disk_alert`.
   - The verdict reads, e.g., `disk=warn:62%+swap:614400kB` or
     `disk=alert:62%+memavail:8%`. The swap is named only above 512 MiB.
   - `CHESTER_SWAP_USED_KB` has twins for fixtures: `CHESTER_MEM_AVAILABLE_KB` and
     `CHESTER_MEM_TOTAL_KB` (MemTotal is needed for the 10%). The gate pins all
     three in every invocation.
4. **Rulings recorded, as built:**
   - **Reg SHO keeps the universe plus every symbol with at least 1,000,000
     shares of total volume.** Ruled; built in item 3 (`REGSHO_MIN_TOTAL_VOLUME`).
   - **The 5b retry bound stands:** three dead expiries in a row, then one try
     each (`RETRY_GIVE_UP_AFTER = 3`).
   - **No manual zip prune.** The disk is at 62%. Box command 3 above is
     withdrawn; the sweep prunes from its first night after the merge.
   - **The five committed `reports/monthly_macro_*` files stay**, and go private
     with the repo.
   - **The compaction runs after the merge, on a weekday evening, after the CX33
     move.** Box commands 1–2 above, in that order.
   - **The first-night timing check (box command 4) is Ari's,** the morning after
     the merge.

### Gates (run locally, one at a time)

| Gate | Result |
|---|---|
| validate_backup | 79/0 (again after the comment fix) |
| validate_heartbeat_caller.sh | 101/0 (the run finished after all; CI #399 and #400 passed it too) |
| validate_systemd_units | 85/0 (on the merge; again after the comment fix below) |
| validate_deploy | not rerun locally (memory); CI |
| validate_audit_1 | 38/0 (on the merge) |

validate_backup's new BUDGET group runs the real `rclone_sync.sh` end to end
against a fake rclone that copies local trees, honours `--exclude`, and moves the
fake clock a set number of minutes per tree. Nothing sleeps. Its fixtures:

- **A normal night** runs every tree in order, and every prune and pull.
- **The exclude** keeps `chester-pre-compact-*.db` on the box, and the zips go up.
- **A cut cap:** db takes 80 minutes, so data's cap becomes 23m.
- **A tree past the budget** is skipped and named, rc 3.
- **A prune with 9 minutes left** is deferred and never listed, and the sweep
  still exits 0.
- **The override:** a 5-minute budget stops after three trees.

The static check now holds that the budget (105) plus the kill-after (1) plus 10
fits inside TimeoutStartSec, read from the unit file. That is 116 against 150
here, and against 120 after aud-2.

The heartbeat gate's fixtures:

- 131 MiB of swap with 2.7 GiB available is clean.
- 600 MiB warns.
- 1.1 GiB alerts.
- 8% available alerts.
- A stale pipeline still outranks a full disk, and outranks swap with low memory.

### CI

- Merge commit `608c4e0`: **CI #396 failed** on one check in validate_attribution
  (79/1). w-1-3c's AQ-8a check looks for `run_eod.py --close-source` before
  `altdata.attribution compute` in `run_eod_cron.sh`, and AUD-1 5a split that
  call into `--capture-only` and `--skip-fetch` passes. The order was still
  right (the attribution follows the compute pass). The check now reads "after
  the last run_eod.py pass"; locally 82/0.
- `e660f80` (the changes): **CI #399 failed** on the attribution check above
  and on one check in validate_systemd_units; `2420fba` (the attribution fix):
  **CI #400 failed** on the units check alone (84/1):
  "chester-backup.service reaches a secret but has no EnvironmentFile=". The
  sweep reaches no secret. The gate follows any `tools/<name>.py` path a wrapper
  names, and the new header comment named `tools/validate_backup.py`, whose
  fixtures carry a key name. The comment now says "the validate_backup gate",
  and the other new comment names the FRED compaction without its module path.
  No behaviour changed. Every other gate passed in #399 and #400, the
  heartbeat gate and validate_attribution among them.
- `ead3a53` (the comment fix): **CI #408 green.**

### Needs you

- **Nothing new to rule.** The box steps are unchanged: commands 1, 2 and 4
  above, now on the ruled schedule (compaction after the merge and the CX33 move;
  the timing check the morning after the merge). Command 3 is withdrawn.
- **When aud-2 merges onto this:** its `TimeoutStartSec=2h` meets this branch's
  budget check (116 ≤ 120 holds). The check reads the unit file, so it needs no
  edit.
- **When alpha-lab-2 meets this branch next week,** the lab's copies and its
  alpha-* snapshot prune go under the budget.
