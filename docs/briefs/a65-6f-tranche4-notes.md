# A65: 6f tranche 4, alignment_weekly (24 Oct 2026, overnight)

The last 6f tranche, under ruling 9a of D27 (`docs/briefs/rulings-2026-10-24.md`: "9a alignment_weekly only"). It adds one per-horizon field on the decision packet, as the Enterprise Layer order names it (`docs/change-order-enterprise-layer-2026-09-27.md`: the `horizon_alignment` row, "A second field, `alignment_weekly`, is added at 6f when the state object carries per-horizon reads", and the gated-items row "`alignment_weekly` | 6f (state object v2)").

Branch-only and paper only. Nothing merged, the box not touched, no units, no secrets. No `decide.py` run against any register, and no register writes: every register here is a scratch file in a temporary directory. Nothing here merges before the 1 Nov Monthly.

## Base

`origin/chain-7` existed at the first fetch (18:28 ET), so there was no wait. **`a65-6f-tranche4` branches from chain-7's tip, `a6c53f57`** ("chain-7 CI round 1: VVV's thesis restored verbatim ..."). That tip carries a62-6f-build and a63-6f-calibration, both merged into chain-7 (`8e7e6af4`, `53adb247`).

## The field

**`alignment_weekly`**: `aligned` / `neutral` / `counter`, or absent (NULL) with its reason. It sits on the register's decision row, beside `horizon_alignment`. It is stamped at entry by `tools/decide.py record` and never recomputed. A supersession carries it forward from the old row, as it does `horizon_alignment`.

- **What it reads.** The weekly per-horizon trend read, `horizons.weekly` (the spec's section 6; `calc.trend_spy_vs_50d`, banded 66/33, persistence 2, as A62 built it), on the stored object of **the decision's session**.
- **The decision's session.** `session.last_completed_session(now)`: the last session whose close plus the 60-minute grace has passed at entry. Its close object is the one the system could have had.
  - At 10:00 ET on a Tuesday, that is Monday's object.
  - At 17:00 ET on Tuesday, it is Tuesday's object, if the 16:45 close has stored it.
- **The rule:**
  - same sign as the read: `aligned`; opposite sign: `counter`;
  - a `flat` read, or an unsigned direction (`flat`, `hedge`): `neutral`.
- **Absent, with the reason stored in `alignment_weekly_basis`:**
  1. **No object for the session yet:** "entered before the 2026-10-23 object existed (newest stored: 2026-10-22)".
  2. **No per-horizon block on the object** (a v1 object): "the ... object carries no per-horizon reads".
  3. **The weekly read absent:** "weekly read absent on the ... object: <the object's own absent_reason>".
  4. **The weekly read uncalibrated:** "weekly read up on the ... object, uncalibrated (n = k of 30)". This is A63's rule applied to the read itself. `altdata/state_calibration.horizon_row` counts the weekly read's own transitions over the stored objects knowable at entry, at the horizon's own length (20 sessions, `config/market_state.yaml` `horizons.weekly.sessions`). Fewer than 30 independent starts is uncalibrated.
  5. **No object readable at all:** "no market-state object readable (<exception>)".
- **Existing rows** have neither column value. They read **"entered before 6f"** (`register.store.PRE_6F`) in `decide.py show` and in the Quarterly's cut.
- **Report only.** Nothing refuses, resizes or gates a counter-aligned packet. DTH's strategic view is a prior, never a command (order §7).

What prints at entry (`decide.py record`), beside the existing line:

```
  alignment       : aligned  (direction long against trend up on the 2026-10-23 object)
  alignment_weekly: absent  (weekly read up on the 2026-10-23 object, uncalibrated (n = 2 of 30))
```

On a register the migration has not reached, it adds: "not recorded: this register predates the 6f migration (tools/migrate_alignment_weekly.py)".

## The migration and its dry run

`tools/migrate_alignment_weekly.py` follows `altdata/purge_synthetic.py`'s safety pattern.
- **`--dry-run` is the default.** It prints the columns it would add and the rows that would read "entered before 6f", and changes nothing.
- **`--apply` refuses** without `--backup PATH`, and when that path already exists.
- **The backup.** With a new path, the run makes an online-backup copy (sqlite's backup API), runs `PRAGMA integrity_check` on it, and checks it holds as many decisions as the register. It refuses on a failure. It refuses with exit 3 when the disk has less free space than the database's size.
- **One transaction.** Both `ALTER TABLE decisions ADD COLUMN`s run in one `BEGIN IMMEDIATE` … `COMMIT`, with a rollback on error: both columns or neither.
- **Nothing is backfilled.** A stamp computed now for an old row would be today's object restating a past decision.
- **Logged.** One line goes to `migrations.log` beside the database.
- **Run twice,** it finds both columns and does nothing.
- **Deny list.** `Bash(*migrate_alignment_weekly.py*--apply*)` is on the deny list in `.claude/settings.json`. `tools/validate_deploy.py` gains a register-writes sample for it, and CLAUDE.md's deny table names it.

**The register no longer adds these columns when it opens.** Every earlier nullable column was added that way, by the ALTER list in `Register.__init__`. These two are left out of it on purpose, so the live schema changes only when the operator runs the migration. They are in `SCHEMA`, so a new register, and every gate's fixture register, has them. `Register.has_alignment_weekly` tells `record()` whether to write them.

**The dry run on a scratch register.** The scratch register is today's schema without the two columns, with four draft rows: the live register's shape before the migration.

```
dry run: C:\Users\arich\AppData\Local\Temp\claude\...\a65_scratch\scratch-register.db
  decisions: 4 rows, 56 columns
  would add: alignment_weekly TEXT (nullable)
  would add: alignment_weekly_basis TEXT (nullable)
  backfill: none; 4 existing rows read 'entered before 6f'
dry run: nothing changed

exit 0 | file unchanged: True
```

**The box sheet line (chain-8).** After the merge to main, inside the windows, and before the first `decide.py record` after the merge. The operator's:

```
cd ~/chester-reports && .venv/bin/python tools/migrate_alignment_weekly.py --dry-run
cd ~/chester-reports && .venv/bin/python tools/migrate_alignment_weekly.py --apply --backup ~/backups/chester-pre-alignment-weekly-$(date +%Y%m%d).db
```

The dry run should print the box's decision count and two "would add" lines. The apply should end with "added 2 columns in one transaction; logged to ...". Both use the register's default path, the one `decide.py` uses.

## The Quarterly's register split

**There was no existing split by `horizon_alignment` to extend.** The aq-* notes name only the AQ-6 thesis register (`altdata/thesis_register.py`), which holds theses and has no alignment field. `tools/cuts.py` and `register/scoreboard.py` cut by status, book, mechanism, gamma sign and the dials at entry, never by alignment. The order's DTH §XXIII test ("the Quarterly's table of graded packets by `horizon_alignment`") was not built.

So this builds the table with both cuts, `horizon_alignment` first and the weekly field second:
- **Function.** `register/scoreboard.alignment_split()`. It reads the grades and the decisions read-only.
- **Window.** The previous calendar quarter, the Quarterly's own.
- **Which grades.** One latest grade per decision, every status alike.
- **Cells.** Each cut prints `aligned`, `neutral` and `counter`. The weekly cut also prints "absent at entry" and "entered before 6f"; the trend cut prints "not recorded" where it applies.
- **Each cell** gives the count and the hit rate, "n=12, 8 hits (67%)". A cell under 10 prints **"n < 10"** and no figure (`config/scoreboard.yaml` `alignment_split.min_n`).
- **Where it prints.** `monthly_macro/payload.build(period="quarter")` attaches it to the register block. `stack.detail_tables` prints its two lines in "The register's month" table. Only the Quarterly's payload carries it, so the Monthly's table is unchanged.

## Session-set values

| Value | As set | Reason |
|---|---|---|
| The decision's session | `last_completed_session(now)`, the 60-minute close grace | The object the system could have had at entry; `regime.latest()` alone would read a newer vintage of nothing. The brief's "entered before the day's object exists" read as "before the last completed session's object is stored". |
| Calibration of the weekly read | its own transitions at 20 sessions, 30 independent starts, `row_for`'s rule | A63's rule applied to the read itself, since A63's matrices calibrate the dials and dimensions, not `horizons{}`. |
| Neutral cases | a flat read, or a flat or hedge direction | As `horizon_alignment`. |
| Hit | `return_pct` > 0, the grade's return in the decision's own direction | Every grade has it. `r_multiple_ruled` needs a parseable invalidation level. |
| Which grades count | all graded decisions, taken, declined and draft alike; latest grade per decision; the current grader method | The grader's shadow-outcome rule: alignment is a property of the packet, not the operator's action. |
| The cut's window | the previous calendar quarter, by `graded_at` | The Quarterly's window. |
| The floor | `min_n: 10`, printed "n < 10" | The brief's. |

## Differences from the brief and the spec

1. **Two columns, not one.** `alignment_weekly` and `alignment_weekly_basis`. The brief's "absent with its reason" needs the reason stored, and the enum has no "absent". `horizon_alignment`'s basis is printed and never stored. This one is stored, because absence is its common case for months.
2. **Absent, not neutral, when there is nothing to read.** The spec (section 6) gives `alignment_weekly` the four neutral cases of `horizon_alignment`, among them no object and the read absent. The brief rules absent for an absent or uncalibrated read and for no object. The brief is later, so it wins. Flat and unsigned stay neutral.
3. **The Quarterly split was new, not extended.** See above.
4. **The calibration of `horizons{}`.** The spec gives each horizon a `transition_prob`, but A62/A63 did not put one on the object. The stamp computes the weekly row at entry from stored objects, by `horizon_row`. It adds nothing to the object, so regime's method hash is unchanged.
5. **The gate is `tools/validate_6f_calibration.py`** (groups E, F, G; 42/0), not `validate_regime`. The stamp is a calibration read, and A63's fixtures are there. No new gate, so CLAUDE.md's gate count is unchanged.

## Commits

- the build: `register/store.py`, `tools/decide.py`, `altdata/state_calibration.py`, `tools/migrate_alignment_weekly.py`, `register/scoreboard.py`, `config/scoreboard.yaml`, `monthly_macro/payload.py`, `monthly_macro/stack.py`, `tools/validate_6f_calibration.py`, `.claude/settings.json`, `tools/validate_deploy.py`, CLAUDE.md;
- these notes.

## Gates run locally

- `validate_6f_calibration` 42/0 (E 14, F 7, G 6 new);
- `validate_regime` 516/0;
- `validate_register` 180/0 (2 skipped);
- `validate_deploy` 154/0;
- `validate_b48_scoreboard` 69/0;
- `check_registry` OK;
- `check_library`: 27 papers, 0 failures, 0 warnings.

The rest are left to CI.

## Files shared

These files are shared with other branches, so expect stitch conflicts in them:
- `register/store.py`, `tools/decide.py` (the register);
- `monthly_macro/payload.py`, `monthly_macro/stack.py` (the Monthly; one line each);
- `.claude/settings.json`, `tools/validate_deploy.py`, CLAUDE.md (the deny list).

## CI

| Run | On | Result |
|---|---|---|
| 40139747558 | `c3a846e2` | **success** (9m52s; read once, 24 Oct evening) |

## Needs you (at most five)

1. **The migration is yours,** from the box sheet line above, after the merge. Until it runs, `decide.py record` stamps nothing and says so. Nothing else changes.
2. **Expect "absent" on every packet for a long time.** A calibrated weekly read needs 30 independent starts 20 sessions apart, about 600 stored sessions under the current method. The box has days of method-11 objects, so every stamp will read "uncalibrated (n = k of 30)" until the history is backfilled under method-11 or the ruling is relaxed for the stamp. Decision: keep A63's floor for the stamp (as built), or stamp from the read alone and print its calibration beside it.
3. **The split's hit definition.** A positive return in the decision's direction, over all graded statuses. The other choice is ruled R > 0 over taken decisions, as the scoreboard does. Doctrine #2 can amend it.
4. **The DTH §XXIII table did not exist.** It is built here for both fields. If a different home for it was meant (`tools/cuts.py`, or a Quarterly chapter of its own), say which.
