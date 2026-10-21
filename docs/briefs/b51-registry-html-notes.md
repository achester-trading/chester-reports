# b51-registry-html: the store-registry check and the HTML editions (session B, 21 Oct 2026)

**What it is.** Two things the box evening of 20 Oct 2026 turned up:
- **The store-registry check.** `python -m tools.check_store_registry --db data/chester.db` exited 1 at 20:47 ET with 62 unregistered keys, 978 stale and one off-list source.
- **The HTML editions.** Three rendering faults in `tools/build_paper_html.py`.

**Branch.** `b51-registry-html`, from main's tip `f9ec9e3` ("Merge pull request #40 from achester-trading/chain-3"). It merges on its own, after chain-4. When chain-4 is on main, main merges into it with a merge commit, the editions are rebuilt and the gates recounted (below).
- **Branch only:** pushed, not merged, not deployed, nothing run on the box, no unit touched.
- **Read only:** a54-relative-volume and a55-box-fixes, for the shared files. chain-4 was not pushed to from this branch, and chester-meme was not opened.
- **The specification** is the paste. Where it and the code differ, the code wins; every difference is under "Where the paste and the code differ".

## Part 1: the store-registry check

### (a) The clock

**Finding.** `check()` counted sessions from a key's newest date to `as_of[:10]`, the as-of's **UTC** date. At 20:47 ET on Tuesday 20 Oct the UTC date is Wednesday 21 Oct, so a key last written on Monday counted Tuesday and Wednesday: "2 sessions, allowed 1". The session had not happened. That accounts for the 389 corr.* keys and the `session` half-life keys.

**Fix** (`e725389`). The count runs to `session.last_completed_session(as_of)`: the ET calendar, today only once its close and grace have passed. That is the same function the heartbeat adopted for the same false alarm, and its docstring says why. The report's header prints the session it counted to.

**Fixture.** `validate_b51_registry_html` group A:
- an as-of of 00:47 UTC on Wednesday 21 Oct counts Tuesday 20 Oct as the last session;
- a `session` key last written on Monday is not stale on Tuesday evening;
- the same key is stale (2 against 1) on Wednesday evening.

A mutation test, with the old line restored in a copy, fails both checks with the box's own line ("2 sessions, allowed 1").

### (b) The allowances

**Finding.** A key's age is counted from its observation date. A source that publishes late, or in batches, is therefore older than its cadence's allowance even while it works.

**Fix** (`e725389`). `config/publication_lags.yaml` states each family's source, its real publication lag in sessions and a bound (`max_lag`), each session-set with its reason. `altdata/derived.staleness_allowance_of` is the one staleness rule: the store check, the reports' confidence and the freshness roster all read it. It now adds the first matching family's lag to the cadence's allowance and says so in its reason ("…, plus 6 sessions' publication lag (fred_h10)").

A family matches by FRED id, read through `config.FRED_PULL_SERIES`, and/or by store-key glob, optionally by `freq`. The registry's own declarations (`freq` and `information_half_life`) are unchanged.

**The allowances, as set** (keys matched on main):

| Family | Matches | Source | Its real publication lag | Cadence allowance | Lag added | Allowance | Bound |
|---|---|---|---|---|---|---|---|
| `fred_h10` | `DEX*`, `DTWEXBGS`; `calc.naive_expectation.dxy`, `.usd_*`; `calc.*hedged*` (33 keys) | Fed H.10, through FRED | Weekly, Monday afternoon, the previous week's daily rates: the newest is up to a week and a half old, a day more after a Monday holiday | 2 (daily) | 6 | 8 | 7 |
| `eia_spot` | `DCOILWTICO`, `DCOILBRENTEU`, `DHHNGSP`; their naive expectations (6) | EIA spot prices, through FRED | Posted weekly (Wednesday) through the previous few sessions | 2 | 6 | 8 | 7 |
| `term_premium_models` | `calc.attr_kw_tp_share_*`, `_acm_tp_share_*`, `_dkw_path_share_*`; `THREEFYTP10` (7) | Kim-Wright (Fed Board, FRED), ACM (NY Fed), DKW (SF Fed) | Republished weekly or irregularly, a week at a time (the registry's own note on those blocks) | 2 | 5 | 7 | 6 |
| `z1_quarterly` | `BOGZ1*` (1 on main; chain-4's FHLB advances join) | Fed Z.1 | About ten weeks after the quarter ends (a53's check: Q2 2026 newest on 20 Oct) | 95 (quarterly) | 85 | 180 | 90 |
| `tic` | `tic.*` (42) | US Treasury TIC | Around the 18th of the second month after the reference month | 32 (monthly) | 45 | 77 | 50 |
| `imf` | `imf.*` (57) | IMF IFS and COFER | Two to three months after the month, by country; COFER a quarter | 32 | 65 | 97 | 70 |
| `em_monthly` | `em.*` monthly (78) | Central banks, statistics offices, IMF | Four to eight weeks after the month | 32 | 45 | 77 | 50 |
| `em_quarterly` | `em.*` quarterly (44) | National accounts, balance of payments | About a quarter after it ends | 95 | 65 | 160 | 70 |
| `worldbank_pink_sheet` | `worldbank.*` (5) | World Bank Pink Sheet | The first days of the following month | 32 | 15 | 47 | 18 |
| `nbs` | `nbs.*` (11) | NBS China | From the month's last day (PMI) to the 15th–20th of the next | 32 | 25 | 57 | 28 |
| `fred_quarterly_release` | every other FRED quarterly; quarterly naive expectations (58) | BEA and others, through FRED | Advance estimate about 30 days after the quarter, third about 90 | 95 | 60 | 155 | 65 |
| `fred_monthly_release` | every other FRED monthly; monthly naive expectations (165) | BLS, BEA, Census, the Fed | One to six weeks after the month ends | 32 | 22 | 54 | 25 |

**The bound that keeps this honest.** A lag is the source's documented delay, with a holiday's slack. It is never a number chosen to clear a key off the list. The gate refuses:
- a lag above its stated bound;
- a family that matches no registered key;
- a family missing its source or reason.

The store check marks a key **past three times its allowance** as "dead?", whatever its lag (c).

**Not in the table, and why.**
- **The `session` half-life keys (corr.* and the rest)** need no lag: the clock was their whole fault.
- **The day's closes** were already fresh.
- **`calc.attr_d10y_*`, `_real_share_*` and `_curve_share_*`** read the 10-year, TIPS and 2-year yields, which FRED posts the next morning, so they keep the daily allowance. If they are still stale on the re-run, their writer has a fault to find; their allowance is not the thing to widen.

**Effect on the reports.** The same rule feeds the reports' confidence (`derived.confidence_of`). A monthly print is "fresh" for 54 sessions, not 32, and an H.10 rate for 8, not 2. `validate_derived`'s monthly pin now reads the cadence plus the family's lag, still never the daily allowance (52/0).

### (c) Dead keys

From the code and the laptop's committed store. The box's full list prints on the re-run, each stopped key marked "dead?".

| Key | Newest | Writer | Why it stopped | Resolution |
|---|---|---|---|---|
| `calc.infl_vol` | 2025-09-01 (289 sessions) | `altdata/market_features.py`, the rates features: the 24-month deviation of annualised month-on-month core CPI | **BLS never published October 2025's CPI** (the 2025 shutdown). `fred.core_cpi` holds no 2025-10-01 value (the committed `data_store/core_cpi.csv` row 44 is blank). The writer refuses every 24-month window that spans a missing month, so none can be written until the window clears the gap, with the change ending November 2027. That refusal is deliberate and pinned (`validate_regime`, "with month 10 missing, no window that spans the gap is written") | **Writer left as ruled; listed.** No registry status fits: it is neither superseded nor not yet sourced. Nothing reads it: no module outside `market_features` names it, and it is not in the market-state object. The choice is yours (needs-you 3) |
| `yfinance.mkt_usdcnh` | about 2026-10-03 | the price basket, until PB-1 (5 Oct 2026) replaced CNH=X with CNY=X | Yahoo serves one daily bar for CNH=X | **Registered as superseded** by `cnh.usdcnh` (the hourly-bar writer), and so never stale (e) |
| `fred.series_release_map` | 2026-09 | the Weekly, until 6c-1.6 (`3f5994e`, 25 Sep 2026) removed its fetch | The map moved to `data/fred_release_map.json` (`altdata/sources/fred_releases.py`) | **Declared a stored object** (e). Its writer is already gone; the two constants left in `daily_cascade/weekly_payload.py` are unused |
| `synthetic.*` (59) | various | none since 5.2 | (d) | (d) |

**What the 20 Oct counts suggest beyond these.** The box's own numbers show 47 keys at 2026-08-01 and 34 at 2026-07-31. Their monthly prints are 56 sessions old on 20 Oct against the new monthly allowance of 54: still stale, but not dead. Each of them is either a release later than the table's (a family to add, with its real lag) or a writer that has stopped. The re-run says which; it is listed for the next session (needs-you 1).

### (d) The synthetic rows

**Origin.** The smoke test, before 5.2 (`26d020e`, 23 Sep 2026).
- `git show 26d020e^:smoke_test.py`: it set `ALTDATA_STORE` to a temporary directory and wrote every `config.FRED_SERIES` entry through `altdata.store.Store.write_observations(spec.key, obs, source="synthetic")`.
- `Store`'s **dual write** (`git show 26d020e^:altdata/store.py`, line 105) mirrored each row into the observation store under `f"{source}.{key}"`. It opened `observations.ObservationStore()`, the **default** database, not a temporary one.
- So each run of the smoke test on the box wrote `synthetic.<key>` rows into the live `chester.db`.
- `config.FRED_SERIES` holds 59 series, the 59 keys the box counted. 28,980 rows is about 491 a key, from the generator's 60 monthly or 400 daily points over more than one run.
- 5.2 moved the smoke test onto a temporary `ObservationStore`, so no row has been written since.

**Nothing reads them.**
- The registry declares no `synthetic.*` key.
- Every report reads registered keys.
- `validate_b51_registry_html` group D scans every module in the repository for a `synthetic.<name>` literal and finds none, outside the purge tool and the gate.

**Your two choices** (needs-you 2):
1. **Quarantine.** Declare `synthetic` on a quarantine list in `source_registry.yaml`: never read, kept as evidence. Nothing is deleted, and the store check stops listing the source. Not built: it is a one-line registry change once you choose it, and the check would need to read the list.
2. **Remove** through the store's audited maintenance path. **Built: `altdata/purge_synthetic.py`**, on `altdata/compact_fred.py`'s pattern:
   - it removes only rows whose key starts `synthetic.` **and** whose source is `synthetic`;
   - `--dry-run` is the default;
   - `--apply` refuses without `--backup` naming a NEW path, which the run fills with an online snapshot and integrity-checks before a single row goes;
   - it refuses when the disk's free space is under the database's size;
   - the delete is one transaction through `observations.maintenance()`, the one exception to the append-only triggers, logged;
   - afterwards it counts the scope again;
   - group D holds all of it on a synthetic store.

### (e) The three other unregistered keys

| Key | What it is | Resolution |
|---|---|---|
| `market_state` | The market-state object, one per session, written by the 16:45 close only (`regime.STORE_KEY`, `regime.store_object`) and read through `regime.latest()` | Declared under a new `non_metrics` group, `stored_objects`: it is an object, not a series. Its freshness is the heartbeat's |
| `fred.series_release_map` | FRED's series-to-release map, written by the Weekly until 25 Sep (above) | The same group, with its history. Nothing writes or reads it now |
| `yfinance.mkt_usdcnh` | USD/CNH's daily close from the basket, ST-2 to PB-1 | A registry entry, `status_extra: superseded`, `superseded_by: cnh.usdcnh`, family price. The store check skips a superseded key's staleness |

## Part 2: the HTML editions

Commit `4f22c0e`, in `tools/build_paper_html.py`:
- **(a) Nested lists.** `commonmark_lists()` re-indents a list nested at CommonMark's content column (two or three spaces) to the four spaces Python-Markdown needs, before rendering. Fenced code is left as written.
- **(b) Checkboxes.** `task_marks()` prints `- [ ]` and `- [x]` items as ☐ and ☑ (`li.task`, no bullet).
- **(c) Figure ids.** `figure_tag()` namespaces each figure's ids by its own number ("Figure 3" → `f03`, "Figure 12b" → `f12b`), unique across the edition. The counter had restarted in every section, so the Guide's five figures all carried `f01`.

**Every edition rebuilt.** Each edition's visible text was compared word for word against main's: all 28 are identical. The Guide gains five nested lists and 24 checkboxes; the other editions differ only in the CSS and their figure ids. `check_library` passes (27 papers, 0/0), as does `check_master_guide` (0/0).

## Part 3: the gate

**A new gate, `tools/validate_b51_registry_html.py`** (25 checks, groups A–E, synthetic fixtures). I chose a new gate over extending `validate_audit_3a`, which holds AUD-3a's counts, and because `build_paper_html` had no gate of its own. Commit `4190371`, with one Makefile line.
- **Code gates:** **one hundred and twenty-six (one hundred and twenty-three Python, three shell)**, on main's 125. `validate_audit_3a` 88/0.
- **Also changed and run locally:**
  - `validate_derived` 52/0;
  - `validate_audit_3a` 88/0 (the purge tool's catalogue line);
  - `check_registry`;
  - `validate_config_refs` 103/0;
  - `validate_gates` 32/0;
  - `check_library` 0/0;
  - `check_master_guide` 0/0.
- **Left to CI:** every other gate. The publication lags change the reports' confidence wherever a monthly, quarterly or H.10 key is read, so CI is the test of that.

## The CI rounds

| Round | Run | On | Result |
|---|---|---|---|
| 1 | 39543993552 | `1265645` (Parts 1 to 3 and these notes) | **green**, 136/136 jobs: every code gate (the new `validate_b51_registry_html` among them, and every gate the publication lags reach through the reports' confidence), the data gates (each reports, never sets the exit code), the shell gates and the smoke test |

One round.

## Where the paste and the code differ

1. **"Apply them where the registry declares allowances."** The registry declares cadences (`freq`, `information_half_life`), not allowances. The lags therefore live in one config file, read by the one rule that turns a cadence into an allowance, rather than spread over hundreds of registry entries.
2. **`calc.infl_vol` is not fixed.** Its gap refusal is a pinned rule, so the writer is left as ruled and the choice is yours.
3. **The dead-key list** holds what the code and the laptop's store can show. The box's full list prints on the re-run, marked "dead?".
4. **"Two sessions, allowed 1" for 389 corr.* keys:** those keys carry the `session` half-life (allowance 1), and the clock fix alone clears them.
5. **The quarantine choice is not built,** since it is yours to choose; the removal tool is.

## Box commands (the operator's; inside the windows; dry runs first)

After this branch merges:
```
cd ~/chester-reports
.venv/bin/python -m tools.check_store_registry --db data/chester.db
.venv/bin/python -m altdata.purge_synthetic --dry-run --db data/chester.db
```
- **Expect** the check to print "last completed session <date> (ET)" in its header:
  - list 1 down to the 59 `synthetic.*` keys alone;
  - list 3 much shorter, each stopped key marked "dead?";
  - list 4 still `'synthetic'`, until (d) is decided.
- **Paste back** the stale list, the "dead?" lines first.
- **Expect** the purge's dry run to print 28,980 rows in 59 keys and "dry run: nothing deleted".

Only if you choose removal:
```
.venv/bin/python -m altdata.purge_synthetic --apply --db data/chester.db --backup ~/backups/chester-pre-purge-synthetic-$(date +%Y%m%d).db
.venv/bin/python -m tools.check_store_registry --db data/chester.db
```
- **Expect** "backup ok: … integrity_check ok", then "deleted 28,980 rows (… remain; 0 in scope)".
- **Expect** the re-run's lists 1 and 4 to no longer name `synthetic`.
- Never 16:00–17:20.

## Files shared with chain-4, a54-relative-volume and a55-box-fixes

| File | chain-4 (`4b096bb`) | a54 (`751902a`) | a55 (`e3002bc`) | At the merge |
|---|---|---|---|---|
| CLAUDE.md | the count line; paragraphs | the count line; a paragraph | the count line | keep both; recount once |
| Makefile | three gate lines after `validate_secondary_notes` | a gate line | a gate line | keep every line |
| `metrics_registry.yaml` | `fred_notes`, `fred_bank_stress` blocks | its keys | — | splice whole blocks |
| `config/catalogue_commands.yaml` | its lines | — | its lines | keep both |
| `docs/html/*.html` | the Guide, the volatility and systematic-book editions | the Guide | — | rebuild from the merged `.md`, never hunk-resolve |

**At the merge of main (with chain-4) into this branch:**
- `config/publication_lags.yaml` gains H.8's weekly deposits (`DPSSCBW027SBOG`, `DPSLCBW027SBOG`: dated Wednesday, released the Friday of the following week, so about 7 sessions over the weekly allowance) and H.4.1's two weekly credit lines.
  - Those keys exist only on chain-4, and the gate refuses a family that matches nothing.
  - chain-4's `fred.fhlb_advances` joins `z1_quarterly` by its id.
- Every edition is rebuilt with this builder.

## Needs you

1. **The registry check's re-run** on the box after the merge (the command above). Paste back the stale list. Each key still stale is either a family to add with its real lag, or a stopped writer to fix; neither is an allowance to widen.
2. **The synthetic rows:** quarantine them (a registry line, nothing deleted) or remove them (`altdata.purge_synthetic`, dry run then apply with a new backup, yours on the box).
3. **`calc.infl_vol`:** leave it unwritten until a 24-month window clears October 2025 (November 2027), or rule a bridge for a missing print. For example, a two-month change annualised over its own span, counted as one observation. That is a change to SR-9's regime variable and its pinned gap rule.
4. **The publication lags:** confirm or replace each session-set value in the table.
