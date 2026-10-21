# a54-relative-volume: signal triage Batch 13, item 61 (session A, 20 Oct 2026)

**Base and boundaries.** This branch is cut from **main's tip, `f9ec9e3`** ("Merge pull request #40 from achester-trading/chain-3", merged 17:43 ET), which carries chain-3's merge.
- **It merges on its own, after chain-4.** When chain-4 is on main, main is merged into this branch with a merge commit, the gates are recounted, and the branch is pushed.
- **Branch only.** Pushed, nothing merged, nothing deployed, nothing run on the box, no unit enabled or started.
- **What was not touched:** session B's chain-4 and `a52-doctrine-2-pack` after A53's final tip, and chester-meme.
- **Two branches, two worktrees.** A53 (`a52-doctrine-2-pack`) and A54 each have their own worktree, and each had its work committed before the other was touched: no stash, no shared tree.
- **The specification** is `docs/change-order-signal-triage-batch-13-2026-10-20.md`, filed verbatim (`9375af8`, before any code) and indexed in `docs/change-orders.md` and the signal-triage register's header. On main, Batch 12 is not indexed yet; its line arrives with chain-4, so both index lines will meet there.
- **The operator's acceptance of 20 Oct** (the A54 plan, points a–e) is built as accepted.

## The commits

| Commit | What |
|---|---|
| `9375af8` | Part 0: the order filed verbatim and indexed |
| `f18eb87` | Part 1: OS-12a and OS-12b, the metric and the flag, with their four placements |
| `29651aa` | Part 2: OS-12c's pre-registration, committed alone before any scoring code |
| `761223c` | Part 2: the scoring script and its first edition; OS-12d, the flat-file volume |
| (this commit) | Part 3: `tools/validate_batch13.py`, the Makefile, CLAUDE.md, these notes |

## Part 1: OS-12a, the metric, and OS-12b, the flag

`daily_cascade/relative_volume.py` holds both.

**The 19 names.** `config.chain_universe()` gives 17: the 13 capture names and the paper bid's GLD, SLV, IBIT and USO. SPX and SPCX come from their Massive chains, as OS-10 reads them.

**The metric.**
- **The ratio:** the session's `chain.options_volume` (our own capture, calls and puts) over the mean of up to 20 stored sessions before the day.
- **Provisional:** under 20 sessions, the ratio prints "provisional (n sessions)".
- **The split:** calls against puts, from the stored put share of volume (`chain.put_share_volume`).
- **How rows are read:** through `opening_setup._series`, so a flat-file row joins only where `flatfile_history` admits it, and a captured reading wins on a shared session.

**The flag.**
- **The threshold:** at least 1.5 times the average, in `config/opening_setup.yaml` under `relative_volume`, labelled "session-set, provisional, frozen 30 days from 2026-10-20".
- **Beside each flagged name:**
  - the put/call split;
  - the day's change in front-month ATM IV by OS-10's method (the last two stored readings of `chain.atm_iv_front`; SPX and SPCX print "awaiting the solver gate");
  - any report within 10 sessions, from OS-11's events (an earnings print, or a scheduled earnings date).
- **The label:** "volume, no side". No side is ever inferred, and the gate holds every printed string to that.

**Placement.**

| Where | What, and how |
|---|---|
| **The 16:45 close** | The flagged names only, five rows at most, as a data table **among the close's detail tables** ("Relative options volume (OS-12)", after "Moves past 2.5σ"), outside the word budget. It is read in `stack_close.produce` immediately after `chain_metrics.record_session` stores the session's readings, because the sections are built before then. The cutoff is the flag day's 16:45 ET. |
| **The next 07:00 anchor** | OS-9's Context column gains "volume flag yesterday" for each name the prior session flagged. The flag is recomputed as of that session's 16:45 cutoff and is never stored, so the tag matches the table that close printed. |
| **The next close** | One Mechanics line (data, outside the word budget): "Yesterday's flagged names: k became OI builds, m did not", with each name's verdict from OS-9's builds on the flag day's settled capture and the next session's, the first whose open interest includes the flag day's trades. A name without both captures is said so. The flags are recomputed as above. |
| **The Weekly** | In Mechanics, beside OS-10 (`daily_cascade/dealer_weekly.py`): the count of flags per name over the week's sessions, each read as of its own close cutoff, and the ledger to date (the newest OS-12c edition's verdict, n and as-of). |

## Part 2: OS-12c, the ledger, and OS-12d, the flat-file volume

### OS-12c, the ledger

1. **The pre-registration,** `docs/ledgers/relative-volume-preregistration-2026-10.md`, was committed alone (`29651aa`, SHA-256 `a1bd6de7…fe4b`, LF bytes, held by the gate) and is never edited.
   - **The comparison:** each flagged name-day (ratio at least 1.5, with 20 sessions before it) against the same name's unflagged days. The measures are the next 5 sessions' absolute move and the change in front-month IV.
   - **The statistic:** the mean excess with a one-sample t.
   - **The samples:** the captures, and the flat files read apart, never pooled.
   - **The pass rule:** INSUFFICIENT under 30 flagged or 30 unflagged name-days or 5 names; PASS when the mean excess absolute move is above zero with t at least 2.0; FAIL otherwise. The IV change decides nothing.
   - **Rights:** none until it passes.
2. **The scoring script,** `tools/calibration/os12c_relative_volume.py`, reads our captures on disk and public closes. It never opens the store, under the calibration rule.
3. **The first edition,** `docs/ledgers/os-12c-ledger-2026-10-20.md`: **INSUFFICIENT, n 0**. The laptop holds no captures, and under the registration that is a result.

**The box edition** (the operator's), writing outside the checkout:
```
cd ~/chester-reports
.venv/bin/python tools/calibration/os12c_relative_volume.py --box --out ~/chester-data/ledgers-dryrun   # the dry run: a scratch directory
.venv/bin/python tools/calibration/os12c_relative_volume.py --box --out ~/chester-data/ledgers            # the edition, outside the checkout
```
A session copies a box edition into `docs/ledgers/` by commit, the way the laptop editions arrive. Once there, the Weekly's "ledger to date" reads it.

### OS-12d, the flat-file volume

- **The backfill.** `tools/massive_flatfiles_backfill.py` now also stores each name's daily total, call and put volume, in contracts (`chain.options_volume`, `chain.call_volume` and `chain.put_volume`, the last two newly registered), from the day aggregates under the flat-file source.
  - A session already marked done without volume is done again. Its writes are idempotent, so only the volume rows are new.
  - The state file records `"volume": true`.
- **Read apart** from the captured rows under A48's rule, `altdata/flatfile_history.py`.
  - **Unchanged:** the four pre-registered tolerances and the 10-session overlap, exactly as they were.
  - **Beside them, a dated addition (Batch 13, D5, session-set):** `VOLUME_TOLERANCE_REL`, a **relative** tolerance of **10%**. It is the median, over the overlap, of |captured − flat-file| / captured.
  - **Why relative:** volume is in contracts, and its scale differs by name by orders of magnitude (an index fund trades millions a day, a single name thousands), so no one absolute tolerance could serve every name.
  - **Why 10%:** the two readings are not the same instant. Our capture is the session's last snapshot (16:10 ET; the vendor names 16:16), while the day aggregate counts every trade, so late prints make the flat file a little larger. A median gap within a tenth says the two count the same trading; one past it says they do not.
  - **The captured reading still wins** on a shared session.
  - The same reason is in the module's docstring.

**The backfill's box command** (the operator's). It needs the two flat-file keys in `.env` first: `MASSIVE_FLATFILES_ACCESS_KEY_ID` and `MASSIVE_FLATFILES_SECRET_ACCESS_KEY`, names only.
```
cd ~/chester-reports
.venv/bin/python -m altdata.secrets MASSIVE_FLATFILES_ACCESS_KEY_ID MASSIVE_FLATFILES_SECRET_ACCESS_KEY
.venv/bin/python tools/massive_flatfiles_backfill.py --dry-run
.venv/bin/python tools/massive_flatfiles_backfill.py --max-days 25
.venv/bin/python tools/massive_flatfiles_backfill.py --status
```
Run it inside the windows, never 16:00–17:20. Re-run `--max-days 25` until `--status` shows nothing to do: the sessions done before this branch are redone once for their volume.

## Every session-set value, with its reason

| Value | Setting | Reason |
|---|---|---|
| The threshold | 1.5x (RULED, D2), "session-set, provisional, frozen 30 days from 2026-10-20" | the order's; reviewed after 30 days |
| The close cutoff for the recompute | 16:45 ET on the flag day | the close has written the day's volume rows by then (each available at its capture's instant, 16:10 or 16:31), so the tag and the line match the printed table, and a later restatement does not move them |
| "Became an OI build" | at least one OS-9 build at or over the name's floor (2,000 contracts for SPY, QQQ, IWM and SPX; 500 for a single name), on the flag day's and the next session's captures | OS-9's own definition and floor, so the line and the anchor's table agree on what a build is |
| The flat-file volume tolerance | 10% relative, 10-session overlap (D5) | above |
| The Weekly's flag count | each session as its own close printed it | so the Weekly's count is the sum of the closes' tables |

## Where the order and the code differ

1. **"The 17 chain names"** and "SPX and SPCX from their Massive chains": 19 symbols, as accepted (a).
2. **"Any report within 10 sessions (OS-11)":** OS-11 holds no within-N-sessions helper. OS-12 counts 10 trading sessions ahead (`altdata/session`) over the events table, keeping an earnings print or a scheduled earnings date. OS-9's tag reads 14 calendar days and only the `earnings` type, and is unchanged.
3. **The front-month IV change:** "the day's change" is OS-10's, the last two stored readings, which are adjacent sessions when both were captured.
4. **The ledger:** it scores the 17. SPX and SPCX are flagged in the reports but have no public closes in the sample.
5. **The flat-file sample** is its own later edition, read from the flat files themselves. The calibration rule keeps every script out of the store, so the stored flat-file rows are not read by it.

## The gate and the checks

- **The gate:** `tools/validate_batch13.py`, a new gate, 33 checks, groups A–G, synthetic fixtures only.
- **What it covers:**
  - the ratio at, below and above 1.5;
  - the provisional label under 20 sessions;
  - the next-morning recompute (a restatement knowable only the next morning does not count) and the next close's line on synthetic captures;
  - no side inferred;
  - the pre-registration's SHA-256;
  - the ledger's rule on fixtures (INSUFFICIENT, PASS, FAIL);
  - the flat-file volume (9% admitted, 11% refused, A48's four unchanged, the captured reading winning);
  - configuration and placement.
- **Changed and run locally:** `validate_batch13` 33/0; `validate_opening_setup` 61/0; `validate_audit_3a` 88/0; `check_registry` OK; `check_master_guide` 0/0 (Table 7a gains the ledger and its registration); `check_library` 0/0.
- **The count:** 126 code gates (123 Python, three shell), counted on main's base; CLAUDE.md updated. Batch 12's gate arrives with chain-4, so the count will need its recount at the merge from main.

## Files shared with chain-4

Chain-4 is main plus `a52-doctrine-2-pack` at A53's tip. Both change:
- `CLAUDE.md`: the gate count and a paragraph each;
- `Makefile`: one gate line each;
- `daily_cascade/stack.py`: here, one Mechanics item after H6's line; there, the bank-stress items;
- `docs/change-orders.md` and `docs/signal-triage-register.md`: Batch 12's and Batch 13's index lines;
- `docs/master-guide.md` and `docs/html/master-guide.html`: Table 7a rows each;
- `metrics_registry.yaml`.

The merge from main resolves them and recounts the gates.

## Needs you

1. **The two flat-file keys in `.env`,** then the backfill above, dry run first.
2. **The ledger's box edition** above, dry run first, once 20 or more capture sessions per name are stored.
3. **The session-set values** above: confirm or replace. The threshold is reviewed after 30 days, from 2026-11-19.
4. **The merge:** after chain-4, then main into this branch with a merge commit and a recount.
