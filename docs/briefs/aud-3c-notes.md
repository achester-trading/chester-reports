# AUD-3c: the data-quality checks (session A, 15 Oct 2026)

**Builds on aud-3a-catalogue and merges after it.** Branch `aud-3c-quality` from the tip of `aud-3a-catalogue` at `3c85b21`. That is aud-3a's part 1 (`6d90f20`) plus its fix for CI #420; I rebased onto the fix before the first push. It uses three things AUD-3a built:

- the units split and per-member units, which give each key its delta rule;
- the move screen's pinned log basis for the volatility indexes and SKEW;
- the catalogue's commands table, which gains a line here.

Merge order: Friday's merges, then aud-1, then aud-3a through its refresh, then this branch through its own.

Branch-only. Nothing merged, deployed or run on the box. Session B's branches (aud-3b-security-master, alpha-lab-2, and the new FRED-history branch from aud-1) are untouched. So are `.env`, the box's units, the register and the ledgers.

**Why.** The audit of 14 Oct (recommendation 14) found no outlier or cross-source check on the prices or the FRED series: a bad print entered the store and the reports as if it were real. This branch adds a read-only check after each pull, with its flags in the close.

## What it builds

### `python -m altdata.quality check [--date D] [--db PATH]`

Opens the store read-only (SQLite `mode=ro`; a missing file is never created) and prints a table. Exit 0 clean, 1 flags, 2 the store cannot be opened. It writes nothing and never changes a value; the gate holds the store's bytes unchanged and finds no write statement in the module.

- **Which keys.** The closes block (`yfinance.mkt_<sym>`, 106 today; the audit's "81 prices" was an older count) and every FRED bulk block (macro, signal triage, FX scan, SLOOS, AQ-3, SR-43, Thailand). The list is read from the registry through config, not kept in the code.
- **New on the date.** An observation whose first vintage became available that day, Eastern time. A later vintage of an observation already stored is a revision, never a new print.

**a. Outliers.** A key's change on the date, against the standard deviation of its own last 60 changes, flags past 6 of them.
- Changes are measured by the key's own delta rule, through the move screen's `unit_rule`: log changes for prices (FX included), differences for yields, rates and spreads, and the move screen's pinned log basis for ^VIX, ^VIX3M, ^VVIX, ^MOVE and ^SKEW (`config/move_screen.yaml`).
- Each observation is read at its first vintage, so a series is judged on what it printed.
- A key with fewer than 61 observations, or with no variation in its last 60 changes, is skipped and named, never judged on a shorter window.

**b. Revisions.** A FRED value written on the date that differs from the value stored earlier for the same observation date. Listed with its old and new values and both availability dates; never an outlier, never a flag, no exit code.

**c. Cross-source pairs.** ^TNX against DGS10, ^TYX against DGS30, and ^VIX against VIXCLS, on the latest date both hold (on or before the date). A gap beyond the pair's tolerance flags. A pair with no measured tolerance prints "not measured" and never flags. A pair with no shared date prints "absent".

`python -m altdata.quality measure [--to D] [--db PATH]` computes each pair's tolerance read-only and prints it, for the operator to record in config. It writes nothing.

### The close

`stack_close.produce()` calls `quality.close_warnings(session, db_path)` after the edition is built and before it renders. The close runs at 16:45, after the 16:10 EOD capture. The day's flags are added to the Warnings table, one line each, at most five and then a count ("and N more data-check flags -- python -m altdata.quality check --date D"). Nothing prints on a clean day.

- The call is read-only and never raises: a store it cannot open, or a check that fails, prints nothing and costs the close nothing.
- A flag never blocks a report or withholds a number.
- The lines also land in the produce report as `data_check`.

The lines, as the gate prints them:

```
Data check: ^VIX 21.3 vs VIXCLS 22.1 on 14 Oct, beyond its 0.4-point tolerance
Data check: ^TNX 4.25 vs DGS10 4.31 on 14 Oct, beyond its 3 bp tolerance
Data check: SPY (yfinance.mkt_spy) 662.17 from 600.58 on 14 Oct, a log change 10.0 times the standard deviation of its last 60 changes
```

The pair line follows the brief's example word for word. An outlier line carries the store key beside its label, because two sources of one fact share a label: "the VIX" is both `yfinance.mkt_vix` and `fred.vix`.

### The config: `config/data_quality.yaml`, every number session-set, each with its reason

| Number | Value | Where from | Reason (short) |
|---|---|---|---|
| `outliers.sigma` | 6 | the brief | far past the move screen's 2.5: what is left is a print to look at before it is read as a move |
| `outliers.window` | 60 changes | the brief | three months of a daily series, five years of a monthly one; a shorter history is skipped, not judged |
| `pairs.percentile` | 99th | the brief | ordinary disagreements stay inside; a gap the pair shows on fewer than one day in a hundred flags |
| `pairs.*.floor` | 0.01 (one VIX cent; 1 bp for a yield) | **session-set, not in the brief** | a percentile below the quote's precision measures float rounding, not a gap (see the VIX below) |
| `close_lines` | 5 | the brief | readable on a bad-feed day; the rest are counted and one command away |

## The measured tolerances

Measured on 15 Oct 2026 with `python -m altdata.quality measure --to 2026-09-25 --db data/chester.db`, read-only on the laptop's copy of the store (to 25 Sep):

| Pair | Shared days | Window | p99 of the gap | Max gap | Tolerance recorded |
|---|---|---|---|---|---|
| ^VIX vs VIXCLS | 1,029 | 21 Apr 2022 to 28 May 2026 | 0.0000012 points | 2.61 points (6 Feb 2026: 20.37 vs 17.76) | **0.01 points (floored)** |
| ^TNX vs DGS10 | 0 | none | none | none | **not measured** |
| ^TYX vs DGS30 | 0 | none | none | none | **not measured** |

- **The VIX:** the two series agree to the float on 1,028 of 1,029 days, so the brief's rule gives a tolerance of about a millionth of a point, and any one-cent rounding difference would flag. I floored it at the quote's precision, 0.01. That floor is mine, not the brief's (needs you, 1). The one real gap in four years, 2.61 points on 6 Feb 2026, is exactly what this check exists to catch.
- **^TNX and ^TYX:** the laptop's copy holds no ^TNX or ^TYX close, because the tape's yields joined the closes on 4 Oct (T2.1) and the copy ends on 25 Sep. The laptop has no bars table either. So both pairs are recorded `tolerance: null` with their reason. They print "not measured" and never flag until a tolerance is measured on the box (the commands below) and written into the config.
- **A real-store check.** `check --date 2026-09-18` on the laptop's copy, the last day with closes: 31 keys with a new print, no outlier, no revision, the VIX pair clean. The check raised no false flag on a real day. (For 25 Sep it found no new print: the copy's closes stop on 18 Sep.)

## The gates

**`tools/validate_quality.py` (new), 36/0 locally.** It runs on its own synthetic store: about a year of business days, no network, no model.
- **A, the config:** the four numbers and their reasons, the three pairs, each measured or saying why not.
- **B, outliers:**
  - 10-sigma jumps on SPY (log), the 10-year (difference) and the VIX (pinned log) are flagged;
  - QQQ's 3-sigma move is not;
  - a 30-observation key is skipped and named;
  - U-3's revised month is not an outlier.
- **C, revisions:** U-3's restated month is listed with old and new values, printed under revisions, and never a flag.
- **D, pairs:**
  - ^VIX and VIXCLS 0.8 apart flag;
  - ^TNX with no tolerance is "not measured";
  - each of the three pairs is tested inside and outside a tolerance;
  - the brief's line holds word for word, and a yield pair prints in bp;
  - the 99th percentile and the floor are checked.
- **E, read-only:** the bytes are unchanged after three checks, with nothing new beside the store but SQLite's own side files. Flags exit 1, a missing store exits 2 and is not created, a clean store exits 0. The module opens `mode=ro` and holds no write statement.
- **F, the close:** a flagged day gives "Data check:" lines; past five, five lines and a count; a clean day and an unopenable store give nothing. The Warnings table prints the line, and `produce()` adds it before rendering.

**`tools/validate_stack.py` (the close's gate), group I added, left to CI** because it renders the PDF.
- A clean fixture day: the report's `data_check` is empty and no "Data check:" line prints.
- A seeded day with ^VIX 21.3 and VIXCLS 22.1: the pair's line, in the email's Warnings table.

Before handing it to CI I ran the check alone on that gate's seed store, with no rendering: no flags on the clean seed (9 keys checked, 5 too short), and exactly the expected line on the flagged one. So the gate's existing checks see no new warning.

**Also changed:**
- `tools/validate_audit_3a.py` 83/0. Its words-count self-test planted a wrong count by replacing the literal "seventy-five code gates". It now plants one beside whatever count CLAUDE.md prints, because the count moves with every gate.
- validate_gates 32/0; validate_config_refs 50/0 (the new config's keys are registered); check_library 27 papers, 0/0.
- CLAUDE.md now says seventy-six code gates (seventy-three Python) and has a paragraph on the check.
- The Makefile lists `tools/validate_quality.py`.
- `config/catalogue_commands.yaml` gains `altdata.quality`.

No gate reads the live store, fetches or calls a model. The measure and the real-day check above were session runs on the laptop's copy, read-only, not gates. Windows raised no low-memory warning; I ran no background watcher.

## Box commands, for Ari (none run here)

After the merge, inside a window (weekdays 09:05–15:40 or 17:20–23:30 ET, never 16:00–17:20):

```
cd ~/chester-reports && .venv/bin/python -m altdata.quality check --db data/chester.db
cd ~/chester-reports && .venv/bin/python -m altdata.quality measure --db data/chester.db
```

Both open the store read-only.

**Reading `check`:**
- The header names the date (the session by default; `--date D` for another).
- Outliers each give the prior and new value, the basis (log or difference) and how many standard deviations.
- Revisions give the old value, when it was stored, and the new value. They are for reading, not alarms.
- Each pair prints CLEAN, FLAG, "not measured" or "absent".
- Skipped keys are too short or flat to judge.
- Exit 1 means at least one flag. Look at the key's source before believing the move. Exit 2 means the store did not open.

**Reading `measure`:** one line per pair: shared days, first and last date, p99, max gap, and the tolerance with the floor applied. ^TNX's and ^TYX's lines are the numbers to record in `config/data_quality.yaml` (`tolerance`, `measured_on`, `measured_window`), as a one-line ruling each. With about two weeks of shared history on the box, their p99 rests on few days; see needs you, 2.

## Files this branch shares with the open branches

Compared against each branch's own changes since its base:

- **aud-1-data-fixes** (`63ec6a8`): `CLAUDE.md`, `Makefile`. Both are the gate-count line and the gate list, which conflict at every refresh. None of aud-1's code files is touched: the close's Warnings lines are added in `stack_close.py`, not in `daily_cascade/payload.py` (aud-1's), where the warnings list is built.
- **aud-2-ops-security** (`02ee5a3`): `CLAUDE.md`, `Makefile`, `daily_cascade/stack_close.py`, `tools/validate_stack.py`.
  - aud-2 inserts its model-meter line in `produce()` right after `ed["run_id"]`, the same spot as the data check (line ~278), and its group at the end of `validate_stack.main()` (~674), the same spot as group I.
  - **Both will conflict textually at the refresh.** Each side's block stays whole; the order doesn't matter.
- **alpha-lab-2** (`9f20f7c`, session B's): `CLAUDE.md`, `Makefile`, `daily_cascade/stack_close.py`. Its lab line goes in at the same spot in `produce()`, so the same kind of conflict.
- **vp-1-volume-profile** (`f8e25d8`): `CLAUDE.md`, `Makefile`, `tools/validate_stack.py`. Its group also goes at the end of `main()`, so the same kind of conflict.
- **t3-6-monthly-polish** (`7071a70`): `CLAUDE.md`.
- **aud-3b-security-master** (`1330dfa`, session B's): `CLAUDE.md`, `Makefile`.
- **aud-3a-catalogue:** this branch's base. It also edits `tools/validate_audit_3a.py` (the words-count self-test) and `config/catalogue_commands.yaml`.
- **The new FRED-history branch from aud-1:** not on origin when I compared; not checked. Its incremental pulls will write the vintages the revision check reads. See needs you, 3.

## Not named in the paste, so chosen here

- **The floor on each pair's tolerance** (0.01). Without it the VIX pair flags on rounding.
- **What "new on the date" means:** the first vintage's availability date in ET; a later vintage is a revision.
- **An outlier is judged on first-vintage values**, so a revision never moves the history the next print is measured against.
- **Too short or flat to judge.** A key with fewer than 61 observations, or zero variation in its window, is skipped and named. A policy rate held flat for 60 prints has no spread to measure against, so its next move would otherwise flag as infinite.
- **A `measure` subcommand**, so the box can measure ^TNX and ^TYX with the same code.
- **The store key in the outlier line**, to tell the two VIX series apart.
- **`fred.vix`** (VIXCLS, units `idx`) is a FRED key, so it is checked for outliers like the others. Its basis is log through its own delta rule, the same as the pinned ^VIX.
- **The close reads the default store** (`observations.DEFAULT_DB`) when the payload gives none, as every other reader does.

## Needs you

1. **The pair floor.** Keep the 0.01 floor, or take the brief's rule as written? As written, the VIX tolerance is about 0.0000012 points, and any one-cent difference between Yahoo and FRED would flag.
2. **^TNX and ^TYX.** Measure on the box after the merge (the command above) and record the two tolerances? Or wait for more shared history, since there are about two weeks of ^TNX closes today? Until then both print "not measured".
3. **Revisions and the FRED-history branch.** Session B's FRED-history branch from aud-1 will backfill vintages. On the day it runs, every restated value it writes will list as a revision written that day; none flags. Want the check to say "backfill" for rows written by that pull, by source string or run id, once that branch's writer is known?
4. **Policy rates.** IORB, the ECB deposit rate and Japan's call rate step rather than drift. One cut inside 60 flat prints gives a small spread, and the next cut could flag. Exclude step series from the outlier check, or keep them as prompts?

## CI

- aud-3a-catalogue: #420 (`6d90f20`, part 1) failed `validate_events` on a literal unit; fixed in `3c85b21` (see `docs/briefs/aud-3a-notes.md`).
- This branch: see the line below.
