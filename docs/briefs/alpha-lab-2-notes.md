# Alpha Lab, Tranche 2: the first engines and the idea pipeline, session notes, 14 Oct 2026

Branch `alpha-lab-2`, stacked on `alpha-lab-1` at `70dbfe8` (Tranche 1, not yet merged), so it merges after Tranche 1. It is branch-only: nothing merged, nothing deployed, nothing run on the box. Tranche 1's seven needs-you items are not yet ruled; this tranche builds on Tranche 1 as it stands.

**Sources:**
- the change order `docs/change-order-alpha-lab-2026-10-12.md`, sections 3–5, 8, 9, and section 10, the amendments of 14 Oct, appended in step 0;
- the brief, sections 5 and 8;
- `docs/alpha-lab.md`, now updated for Tranche 2.

**All of X-2.1 to X-2.11 are built**, in the order given. Every gate run is green; see "Gates and CI".

## Step 0, and the fixture

- **The fixture checks out.** The file is `C:\Users\arich\Downloads\hypotheses-2026-10-14.yaml`. It was copied byte for byte to `tests/fixtures/alpha/inbox/hypotheses-2026-10-14.yaml`: 8,047 bytes, SHA-256 `6fdc4dc7…14446626`, matching the paste. The committed blob carries the same hash.
- **Step 0 was committed as pasted:** `0e9084b` "Alpha Lab: change order section 10 (amendments of 14 Oct) and the first inbox batch as a fixture". It holds section 10 verbatim and the fixture, and nothing else.
- **The `.md` was not committed**, and no YAML was written from it.
- **The fixture's bytes are pinned.** `.gitattributes` marks `tests/fixtures/alpha/inbox/**` as `-text`, in the X-2.5 commit, so a Windows checkout cannot rewrite the line endings and change the hash.

## What each item built

| Item | Commit | Built |
|---|---|---|
| **X-2.5** The register | `ef42548` | `alpha/hypotheses.py`. The v1 batch schema check, with every field of the fixture's schema. The budgets. The normalised rule hash, and title similarity at 0.85, for duplicates; failures are included. The register lives in `alpha.db`: `hypotheses` (the fixture's fields, plus register id, `pre_registered_at`, status, result, `superseded_by`), `hypothesis_batches`, and `inbox_log`. Triggers keep the idea fixed and never deleted. `refuse_if_unregistered()` refuses a run before the pre-registration, an unregistered rule, and a closed idea. Registering counts one variant (10.2 c). An empty Tranche 1 `hypotheses` table is replaced. |
| **X-2.10a** The grammar v1 | `47b6dbd` | `alpha/rules.py`, an interpreter: it calls no eval, exec or compile. `docs/alpha-lab-rules.md`, written for the Saturday brief. `config/alpha_rules.yaml`. The first batch's translations are under `alpha/research/translations/2026-10-14-claude-weekly-01/`, each bound to the batch file's sha256. `tests/fixtures/alpha/fixture_store.py` is a synthetic store with the episodes planted. |
| **X-2.9** The workbench | `d0310d2` | `python -m alpha.research new \| run \| report \| list` (`alpha/research/`). `alpha/intake.py` is the one admission path. `alpha/promote.py` holds the model-idea screen. `alpha/files.py` is the lab's one file writer. `alpha/validate.py` gains `count_variant`, so a hypothesis's first run uses the count its registration made. |
| **X-2.11** Inbox and outbox | `5e5f319` | `alpha/inbox.py` and `alpha/outbox.py`. The sweep's inbox pull and outbox push are in `scripts/rclone_sync.sh`. The backup unit may write `inbox/lab`; the weekly unit may write `outbox/lab`. The nightly loop ingests; the weekly loop writes `lab-verdicts-YYYY-MM-DD.md`. |
| **X-2.10b** The daily proposer | `2568a55` | `alpha_proposer/`, outside `alpha/`. The prompt is `config/alpha_proposer_prompt.md`. The unit and timer are `chester-alpha-proposer.{service,timer}`, at 18:10 ET, printed and never enabled. The wrapper is `scripts/run_alpha_proposer.sh`. Its gate is `tools/validate_alpha_proposer.py`, in the Makefile; CLAUDE.md's count is now sixty code gates. |
| **X-2.6** Promotion | `0554511` | `promote_passed()` is the nightly loop's last step. It promotes a passed idea to live at min_size; a model's idea carries `paper_floor_signals` = 1.5 × min_signals, which the allocator honours. `alpha/engines/grammar.py` trades a promoted grammar rule. Paper gains close-only bars and fills at the close. `python -m alpha.promote retire --ruling` is the operator's, and is denied to sessions. |
| **X-2.4** The weekly loop | `6491f02` | Walk-forward extended; the bounded re-fit; the rebalance; `alpha/research/agenda.md` and `agenda.json`, with a copy to the outbox; the verdicts. `alpha/screen.py` is the lab's 2.5σ screen. |
| **X-2.2, X-2.3, X-2.1** The engines | `fb35698` | `alpha/engines/trend.py` (sleeves `trend_ts` and `trend_xs`), `alpha/engines/pm_futures.py` with `config/alpha_pm_map.yaml`, and `alpha/engines/vrp.py` (the coverage check). All four are registered as candidates. Their batch is `alpha/research/roster-2026-10-14.yaml`, for you to pre-register on the box. |
| **X-2.7, X-2.8**, the close's line | `7f95619` | `docs/briefs/alpha-research-sitting-template.md`. `alpha/report.py`: the monthly Lab report, attached by one hook in `monthly_macro/run.py`. `lab_line.daily_line`, through one hook in `stack_close`/`stack_render`, as small as the Weekly's. The nightly loop now runs the harness on each newly registered hypothesis. |

## The five seed hypotheses and the grammar

**Three compile and run on the fixture store. Each translation states its substitutions:**
- **H-002** registers in the grammar with one substitution. The batch says "short at the Friday close", but the trigger reads that same close. The grammar fills a close-decided rule at the next session's **open**, which SPY stores. "The trigger week's high" is the highest stored daily high of the week. The conditioning variant drops `trigger[3]`.
- **H-004** registers in the grammar with two substitutions:
  - **"Duration-matched" becomes volatility-matched** over 60 sessions, because the store holds no duration series. "Beta-adjusted" LQD is matched the same way.
  - **HYG and IEF are close-only**, so the entry is the next close.

  The LQD hedge is a `replace` variant.
- **H-005** registers in the grammar as written. Its 20-day ATR is close-to-close, because TLT stores closes only. Its pre-2002 proxy is not expressed: it needs a duration.

**Two remain `needs_code`, with the reason.** Each is a committed translation with a `needs_code_reason`:
- **H-001 needs option prices.** The rule is an iron fly at the stored bid and ask; grammar v1 reads no option quote, and no event-straddle history is stored.
- **H-003 needs the Book B scanner's setups,** which are code over a ~60-symbol basket, plus the depth of SPY's gamma history.

**The real store may be too short for two of them.** I read the laptop's copy of the store, `../chester-reports/data/chester.db`, last written 30 Sep, opened `immutable=1` so nothing was written beside it. Prices there start 2021-09-20 (1,255 sessions), the OAS series start 2023-05-30 (786), and the 10-year yield starts 2022-04-21.
- H-002's and H-005's five-year percentile (1,260 observations) **barely fills, if at all**, so both will likely report insufficient history on the box.
- H-004 has about three years.

This is the store's depth, not the code's; see needs-you 5.

## The daily proposer

**Prompt version:** `alpha-proposer-v1`, on the first line of `config/alpha_proposer_prompt.md`. Every batch records it, with the model id, as `prompt_version`, `model_id` and `packet_sha256`. These are columns on `hypothesis_batches` too.

**Model:**
- **The model id** comes from `daily_cascade.narrative.DEFAULT_MODEL`, the close's pin.
- **The client** is `daily_cascade.narrative._client()`, which reads the key through `altdata.secrets`.
- **Thinking is off.**
- **There is one call a session day**; a second run that day writes nothing.

**The packet's fields** (`alpha_proposer/packet.py`, built by code):

| Field | Contents |
|---|---|
| `session`, `as_of` | the session and the instant |
| `moves` | each stored symbol's one-day move, with a z-score against its own trailing moves (up to five years) |
| `screen` | the moves at or beyond 2.5σ. `altdata.move_screen` is not built yet, so this is `alpha/screen.py`'s own, and says so. |
| `dealer` | SPY's `exposure.net_gex`, gamma flip, call wall and put wall, with their changes |
| `state` | the stored dials, the open contradictions and the exceptions, read and never recomputed |
| `prediction` | probabilities that moved at or beyond the 10-point attention-shock threshold |
| `calendar` | scheduled releases in the next five sessions, as known now |
| `agenda` | `agenda.json`, the lab's agenda of misses |
| `register` | every hypothesis's id, title, family, status and rule hash. Failures are included; **results are not.** |
| `budgets` | per session day, per family per week, and this week's use |
| `dictionary` | every stored series: key, symbol, first and last day, rows |

**The code checks every proposal before anything is written:**
- the schema;
- the blocklist;
- the store's instruments;
- the rule compiled against the store (a rule that fails is kept as text, `needs_code`);
- duplicates against the whole register and against each other;
- three a session day, two a family a week.

**The gate's fake model** returns three proposals: one valid, one a duplicate of H-005, one on BN. It writes exactly one.

## The inbox manifest, as verified

**The fields were verified on rclone.org on 14 Oct**, in the Drive backend's Metadata table and on the `rclone lsjson` command page. `rclone lsjson --metadata --hash --files-only <remote>:chester-vendor-checks/lab-inbox` prints one object per file:

| Field | Meaning |
|---|---|
| `Path`, `Name`, `Size`, `MimeType`, `IsDir`, `ID` | the file |
| `ModTime` | RFC 3339; Drive gives millisecond precision |
| `Hashes.md5` | with `--hash`; Drive serves md5 |
| `Metadata.btime` | **the file's creation time**, RFC 3339 to the millisecond. This is the pre-registration instant. It is writable only on fresh uploads, never on updates. |
| `Metadata.mtime` | the last modification time, RFC 3339 to the millisecond |
| `Metadata.content-type` | and the others |

**What the ingestion uses:**
- `btime` is the created time;
- `mtime`, else `ModTime`, is the modified time;
- `md5` checks the bytes.

**What the ingestion does:**
- **A file listed without `btime` is refused.**
- **A file not yet listed waits a night.** The sweep lists before it copies, so a file can land in between.
- **Files are taken in order of creation,** so of two files carrying one batch_id, the earlier is the registration.
- **A file written on the box by the proposer** is checked against its own manifest line instead: `manifest-proposer.jsonl`, with name, sha256 and `written_at`.

**One thing could not be verified.** rclone's documentation does not say which version added `--metadata` to `lsjson`. The sweep's header records the box's rclone as v1.60. Needs-you 3 asks you to check on the box.

## The VRP coverage check (X-2.1)

**The check runs first, and the VRP is a data gap.** `alpha/engines/vrp.py` `coverage()` counts sessions that have BOTH stored option quotes (bid and ask per strike and expiry, for SPY and QQQ) AND the dealer series.
- **On the laptop's copy of the store** there are 0 option-quote sessions and 0 `exposure.*` sessions. The copy holds no dealer series at all; the box writes them.
- **On the fixture** there are 0 quote sessions and 60 dealer sessions.

Either way the VRP cannot reach its minimum sample of 100 until 6b's chain history or FlashAlpha's historical quotes are stored in the store. The chain files the EOD pass keeps on disk are not the store. Running the roster's E-1 on the box records the box's real count (needs-you 4).

## Box commands, printed for you and run by no session

**1. The directories**, once, before the sweep or the loops use them:

```bash
mkdir -p ~/chester-data/inbox/lab ~/chester-data/outbox/lab
```

**2. The unit changes** arrive with the merge, through the self-deploy: the `chester-backup` grant for `inbox/lab`, the `chester-alpha-weekly` grant for `outbox/lab`, and the new `chester-alpha-proposer`. All are oneshot units, not running between timers, so no restart is pending.

**3. Enable the timers**, inside a window, after Tranche 1's are enabled:

```bash
systemctl --user enable --now chester-alpha-proposer.timer
systemctl --user list-timers 'chester-alpha-*'
```

**4. Check rclone once.** This is read-only:

```bash
rclone version | head -1
rclone lsjson --metadata --hash --files-only gdrive:chester-vendor-checks/lab-inbox | head -c 800
```

It should print `"btime"` inside each `"Metadata"` object.

**5. Pre-register the engine roster**, as a box write inside a window. The nightly harness then runs it:

```bash
cd ~/chester-reports && .venv/bin/python -m alpha.research new alpha/research/roster-2026-10-14.yaml --source operator
```

## Not named by the change order, so chosen here

1. **The register lives in `alpha.db`, not in `alpha/hypotheses/<id>.yaml`.** The box can write `alpha.db`, but writing the checkout would dirty `git pull --ff-only`. `python -m alpha.research list` prints it.
2. **The first batch is translated in committed files,** `alpha/research/translations/<batch>/<id>.yaml`, bound to the batch's sha256 and applied at ingestion. A translation never changes the pre-registration instant, and it states every substitution.
3. **The grammar has four additions beyond the paste's list,** each documented:
   - the series combinators `ratio` and `spread`;
   - the window transforms `max` and `min`, used for a stop at a series level;
   - `cooldown`;
   - a `replace` variant kind (instrument, entry, exits or direction swapped), and `drop`;
   - `this_close` decides at 15:50 ET on what is knowable then.
4. **The nightly loop runs the harness** on each newly registered hypothesis, capped at `research.max_runs_per_night: 10`. It also re-runs a model idea whose post-cutoff screen waits for data. Without this, nothing would test what the inbox or the proposer delivers.
5. **The model-idea screen with no trade after 2026-07-01 is *pending*.** The hypothesis stays `testing` and is not failed; the next run looks again.
6. **How variants are counted:**
   - registering counts 1;
   - a first run counts each conditioning value and each drop or replace variant *before* the base is scored;
   - a coded engine's fitting grid counts on its first run (the trend's 3×3 is 8 more);
   - a re-run of an unchanged rule counts nothing.
7. **Promoted grammar rules are named by their register id** in `alpha.db`. This is a second naming place beside `config/alpha_engines.yaml`, because promotion is the loop's and the loop cannot commit config. CLAUDE.md says so.
8. **The paper book gained three things:**
   - close-only bars, so the basket's close-only instruments can be traded;
   - fills at the close;
   - a session-dated time stop.

   A grammar rule's pct, R or ATR stop is set from the **decision day's close**, because the entry price is not known when the signal is written.
9. **`alpha/files.py` is the lab's one file writer.** Group A of `validate_alpha` now allows it and no other module.
10. **The trend engine has a volatility floor (2% a year) and a per-name cap (25%).** Without them, a near-constant series takes the whole book.
11. **Engine 3 maps contracts by hand,** in `config/alpha_pm_map.yaml`. It is empty until someone reads a contract's resolution rule.
12. **`validate_backup`'s cap check was widened.** It now accepts a capped `rclone copy` on its own line, skips comments, and requires the stall limits on every copy, not just the first.
13. **The Daily close's line uses " · "**, as the Weekly's does. The paste spelled it with " - ".
14. **The deny list gains `alpha.promote retire`**, beside the register writes. `validate_deploy` and CLAUDE.md were updated to match.
15. **A sitting's batch is budgeted at five.**
16. **The agenda's copy goes to the outbox** as `lab-agenda-YYYY-MM-DD.md`, so the sitting can read it from Drive.
17. **Title similarity can flag different rules that share wording.** The roster's two trend sleeves did, until E-2b was retitled. Screened-out ideas are kept and counted, so a false positive costs a variant, not an idea.

## Gates and CI

**Run locally** (the affected gates, not the full suite):

| Gate | Result |
|---|---|
| validate_alpha | 232/0 (groups A–U; N–U are new) |
| validate_alpha_no_orders | 61/0, unchanged in strictness |
| validate_alpha_proposer (new) | 42/0 |
| validate_backup | 63/0 |
| validate_deploy | 118/0 |
| validate_systemd_units | 88/0 |
| validate_secrets | 37/0 |
| validate_config_refs | 40/0 |
| validate_gates | 31/0 |
| validate_daily_close | 102/0 |
| validate_stack | 66/0 |
| validate_stack_cadence | 99/0 |
| validate_readability | 63/0 |
| validate_voices | 70/0 |
| validate_weekly_stack | 68/0 |
| validate_weekly_calendar | 40/0 |
| validate_weekly_complete | 57/0 |
| validate_weekly_edits | 90/0 |
| validate_monthly | 350/0 (1 skipped) |
| validate_monthly_stack | 261/0 |
| check_library | 0 failures, 0 warnings |

**CI, by push:**

| Run | Covers | Result |
|---|---|---|
| **#375** | step 0, X-2.5, X-2.10a | green |
| **#378** | X-2.9, X-2.11 | green |
| **#380** | X-2.10b | green |
| **#381** | X-2.6 | green |
| **#382** | X-2.4 | green |
| **#383** | the engines | green |
| **#384** | X-2.7, X-2.8 and the line | running when these notes were written |

These docs are a further push.

## Needs you

1. **Merge** `alpha-lab-2` after `alpha-lab-1`, inside a window. yes / no
2. **The box commands above:** the two `mkdir`s, enabling the proposer's timer, and pre-registering the roster.
3. **rclone on the box.** Check that its `lsjson --metadata` prints Drive's `btime` (v1.60 per the sweep's header). Without it, every Drive batch is refused, which is safe but stalls the inbox. ok / upgrade rclone
4. **The VRP's real coverage.** Running the roster's E-1 records it. Until option quotes are stored, the VRP is a data gap. noted
5. **History depth.** The laptop's copy of the store has prices from 2021-09 and OAS from 2023-05. Five-year windows (H-002, H-005) barely fill, and 40 independent signals for a weekly rule need more years than the store holds. Backfill longer price and FRED history, or accept that these fail on sample? backfill / accept
6. **The translations' substitutions:**
   - H-002 enters at the next open;
   - H-004 hedges by volatility, not duration, and enters at the next close;
   - H-005 uses a close-to-close ATR.

   accept / rule otherwise
7. **The roster's source.** The four engines are registered as source `operator`, because the roster is the brief's, ruled 12 Oct. That keeps them out of the model-idea rule. keep / rule `model`
8. **The trend engine's costs at its size.** At min_size 0.05 ($5,000 lab dollars) across up to 20 names, the $1 commission minimum alone is about 0.4% a side on a $250 position, which may sink it. Raise trend's min_size, cut its breadth, or revisit `commission_min` for ETFs? choose
9. **The model-idea screen with no trade after the cutoff is pending, not failed** (Not named, item 5). keep / rule
10. **The variant counting** (Not named, item 6). keep / rule
11. **The register as a second naming place** for promoted grammar rules (Not named, item 7). keep / rule
12. **The Saturday brief task.** Once this is on main, the task should:
    - read `docs/alpha-lab-rules.md`;
    - write v1 YAML, with its `.md`, to `lab-inbox`;
    - read `lab-verdicts-*` and `lab-agenda-*` from `lab-outbox`.

    Update the task's instructions? yes / no
13. **Engine 3's contract map** (`config/alpha_pm_map.yaml`) is empty. Who maps contracts: a session from the stored resolution rules, or you?
14. **Tranche 1's seven items** are still open, including item 5, the missing `lab_resume` command.


## 14 Oct evening

The follow-ups ruled at 08:40 ET (rulings 6, 8, 10, 13, 18), with Ari's answers
of the evening folded in. Branch only: nothing merged to main, nothing deployed,
nothing run on the box.

### The merge

`origin/w-1-3c-weekly-polish` at **fb67bf3** (it had not moved) is merged as
**`26e86d3`**, pushed on its own before the changes.

| Conflict | Resolution |
|---|---|
| `CLAUDE.md`, the gate count | w-1-3c's text, recounted from the Makefile's list: **seventy-seven code gates (seventy-four Python, three shell) and six data gates**. w-1-3c said 74 and five. This branch adds three gates (validate_alpha, validate_alpha_no_orders, validate_alpha_proposer), and the sixth data gate is validate_imf_china. |
| `Makefile` | both gate lists: w-1-3c's six gates, then this branch's three. |
| `deploy/systemd/chester-backup.service` | ReadWritePaths is the union: `-%h/chester-data/inbox/aaii`, `inbox/spdji`, `inbox/etf` (w-1-3c) and `inbox/lab` (this branch). Both sides' comments are kept. |

CI on the merge, **#409, failed** on three gates. Two failures came from the merge
and one predates it. Each is fixed in the changes commit:

- **validate_backup**: w-1-3c's check allows exactly its three inboxes under
  `~/chester-data`, and the union adds the lab's. The check now names all four,
  the same union.
- **validate_alpha**: the weekly hook check counted `weekly_line(` once, and w-1-3c
  added `correlation.weekly_line(`, which is a different function. The check now
  counts only the bare call. The lab's hook itself is unchanged.
- **check_library**: CLAUDE.md marked `alpha/research/reports/` and
  `~/chester-data/outbox/lab/` as repo paths, which they are not. This had
  failed since #385, Tranche 2's own push. Both are runtime paths, one written
  at run time and one on the box, so CLAUDE.md now gives them as plain text and
  names `alpha/files.py`.

### The changes

**a. lab_resume (ruling 6).**
- `python -m alpha.governor resume --reason "..."` writes the `lab_resume` event,
  with source `operator` and the reason quoted.
  - It refuses an empty reason, and refuses a lab that is not halted.
  - `status` prints `halted` or `running`.
- `governor.lab_status` now counts only an **operator** lab_resume. A lab_resume
  row a loop writes lifts nothing, and neither does a recovery of the equity.
- **Not named, chosen here:** on the resume, the lab's high-water mark is re-based
  to its equity at that moment. Otherwise the next night would re-halt on the
  same drawdown Ari had just reviewed. A fresh -15% from the re-based mark halts
  the lab again.
- The command is denied to sessions as the register writes are:
  `Bash(*alpha.governor resume*)` in `.claude/settings.json`, the CLAUDE.md
  denied-table row, and two shapes in validate_deploy's "register writes"
  list. `docs/alpha-lab.md` says so.
- In validate_alpha group I:
  - the deny matches the command, and the same check fails once the line is
    removed from a copy of the list;
  - CLAUDE.md names it;
  - the halt holds through a new high-water mark and through a loop's lab_resume;
  - the CLI's event lifts it;
  - there is no re-halt the next night, and a fresh -15% halts it again.

**b. The alpha-\* snapshot prune (ruling 8).**
- `scripts/backup_retention.py --prefix alpha` applies the db/ rule to
  `alpha-YYYY-MM-DD.db[.gz]`: 14 daily, 8 weekly, monthly forever, and the
  newest always.
  - It matches by exact name and judges each family apart, so a run for one
    prefix never plans a name of the other.
  - `--require` must name a file of that family.
- `rclone_sync.sh` runs the alpha pass after chester's, only on a night tonight's
  alpha snapshot was staged.
  - The shell re-matches each name against its own family's pattern before the
    one `rclone deletefile "$REMOTE/db/$name"`.
  - The status line reads `db/ prune: ok (n deleted); alpha: ok (m deleted)`.
- **Under the budget next week.** This branch's `rclone_sync.sh` has no sweep
  budget. When it meets aud-1-data-fixes, the lab's copies (the alpha snapshot,
  the inbox and the outbox) and this prune go under aud-1's 105-minute budget,
  the prune behind its 10-minutes-left rule like the db/ prune.

**c. Trend at its minimum size (ruling 13).**
- The $1 commission minimum stays.
- `trend.weights()` takes the sleeve's capital and holds no position under
  `MIN_POSITION` ($1,000):
  - The breadth is at most capital / $1,000 names, never above `max_names` (20).
    trend_xs takes at most half that a side.
  - A name whose vol-targeted weight would still sit under $1,000 is dropped, the
    next candidate takes its place, and the book is re-weighted.
  - `signal()` and the harness's `_returns()` both pass `capital()`, which is
    notional × min_size.
- The fixture's results:

  | Capital | trend_ts | trend_xs |
  |---|---|---|
  | 5,000 (min_size 0.05) | 5 names, the smallest $1,000 | 4 names, balanced, each ≥ $1,000 |
  | 20,000 | 13 names (up to twenty), each ≥ $1,000 | |
  | 100,000 | 20 names, never more | |

  Vol targeting is why 20,000 holds 13 rather than 20: twenty names at 20,000
  average exactly $1,000, so the quieter names push the busier ones under the
  floor. It reaches 20 as the capital grows.
- **This answers needs-you 8 of Tranche 2.**

**d. The history backfill (ruling 10, as answered).** The price command is below
under "Box commands". **The FRED backfill is held.** The FRED pull stamps every
row available at the moment it is pulled. A deep backfill would therefore be
invisible to every as-of query before the backfill date, and the lab's long
windows would stay empty. A later paste builds a FRED history writer that
stamps each value with its ALFRED first-publication vintage (the next business
day after the observation where a series has no vintage record), each row marked
as a backfill under its own run.

**e. The prediction-market contract map (ruling 18, as answered).**
- `python -m alpha.pm_map draft [--store PATH]` opens the store through
  `ReadOnlyStore` and prints draft `contracts:` entries to the screen. It writes
  nothing: it builds the YAML as text, and the lab's no-file-write gate holds
  that. It drafts a contract only if:
  - it is on the FOMC-decision watch;
  - its pm.market row stores a resolution rule (`criteria`);
  - it resolves on a stored FOMC decision day;
  - its outcome label reads as a 25 bp cut, a 25 bp hike or a hold.
- Every entry is `confirmed: false` and carries `resolution` and `drafted_from`:
  the stored rule quoted in full, the outcome label, the question, the rules
  page and the row's observed_at.
- Each contract it does not draft is listed after the entries with the reason
  (no rule stored, a date off the calendar, a move beyond 25 bp).
- Engine 3's `contracts()` now reads only `confirmed: true` entries.
  `config/alpha_pm_map.yaml` stays `contracts: []`, so engine 3 holds no
  contracts until Ari confirms lines and a later paste commits them.
- validate_alpha **group V** drafts from a synthetic six-contract store:
  - two entries, a cut and a hold, each quoting its rule;
  - nothing for the contract with no stored rule;
  - the >25 bp contract and the off-calendar date skipped with their reasons;
  - another watch ignored;
  - the CLI's output parses and the store is byte-identical;
  - a pasted draft maps nothing in the engine, and a confirmed line maps one;
  - the committed map confirms nothing.

### Gates (only the touched ones, locally, one at a time)

| Gate | Result |
|---|---|
| validate_alpha | 255/0 |
| validate_backup | 70/0 |
| validate_deploy | 118/0 |
| validate_alpha_no_orders | 63/0 |
| validate_systemd_units | 98/0 |
| check_library | 0 failures |

No gate read the live store, fetched or called a model. CI is the validate.

### CI

- **#409** (`26e86d3`, the merge): failed, as above; fixed in the changes commit.
- `cc4cf79` (the changes and the three fixes): **CI #413 green.**

### Box commands, printed for Ari and run by no session

**The deep price backfill.** Run it after aud-1-data-fixes is on main and after
the FRED compaction, on a weekday evening inside the window (17:20-23:30 ET),
clear of the 02:30 sweep. Not Friday night.

```bash
cd ~/chester-reports && git log -1 --oneline       # the merged tree
df -h ~/chester-reports/data                       # want at least 3 GB free
ls -lh ~/chester-reports/data/chester.db
free -m
.venv/bin/python tools/backfill_prices.py --period max --dry-run 2>&1 | tee ~/logs/backfill_prices_max_dryrun.log
.venv/bin/python tools/backfill_prices.py --period max 2>&1 | tee ~/logs/backfill_prices_max.log
ls -lh ~/chester-reports/data/chester.db
```

- **What it writes.** It covers every symbol in `yfinance_source.SYMBOLS`, 106 on
  the merged tree, from yfinance's first bar. Availability is reconstructed as
  the close plus the declared latency, flagged `reconstructed`. A series that is
  not `never` or `split_only` is refused. Rows already stored (the last five
  years) are ignored as duplicate vintages.
- **The estimate.** It is a reckoning from listing dates, not a fetch; the dry
  run prints the exact first date and count per symbol.
  - Closes: about 700k in total, about 570k of them new. These are 29 single
    names averaging about 35 years, 55 ETFs about 18, 9 indices about 45
    (^GSPC from 1927), 7 futures and 7 FX pairs about 23, and 4 coins about 9.
  - Rows in all: about **1.2 to 1.6 million new rows**, adding the volume
    companions, the tape set's open/high/low, dividends and splits.
  - Disk: about **0.3 to 0.6 GB** more in chester.db.
  - Run time: about **15 to 30 minutes**, mostly one yfinance call per symbol.
    The dry run fetches as well, so allow the same again for it.
- **Why the df check wants 3 GB.** The nightly sweep refuses to stage a snapshot
  with less than twice the database's size free (`disk_low`, exit 5). A larger
  chester.db raises that bar the same night.
- **Then:** the next close pass recomputes the features over the deeper history,
  and `compute --backfill` for the correlation layer is a separate step if wanted.

**The FRED backfill: held**, for the reason under item d. No command until the
history writer exists.

**The contract-map draft**, once alpha-lab-2 is on the box (the module is on this
branch only). It is read-only, prints to the screen, and writes nothing:

```bash
cd ~/chester-reports && .venv/bin/python -m alpha.pm_map draft
```

Paste its output into chat. A later paste commits the lines Ari confirms.

**lab_resume**, for when the lab ever halts. It is Ari's, and denied to sessions:

```bash
cd ~/chester-reports && .venv/bin/python -m alpha.governor status
cd ~/chester-reports && .venv/bin/python -m alpha.governor resume --reason "<why>"
```

### Needs you

1. **The contract map:** run the draft command after the merge and paste the
   output; confirm or strike each line. Until then engine 3 trades nothing.
2. **The re-based high-water mark on a resume** (item a, chosen here). keep / rule
   otherwise
3. **trend at 20,000 holds 13, not 20** (item c). This is the floor working
   against vol targeting, and it reaches 20 as capital grows. keep / rule
4. **The price backfill:** the commands above, on the ruled schedule.
5. **The FRED history writer:** the later paste, as ruled.
6. **Next week's meeting with aud-1:** the lab's copies and the alpha prune go
   under the sweep budget, as item b says.
7. Tranche 2's needs-you 8 (trend's costs) and 13 (the contract map) are now
   answered by these rulings. 14 (lab_resume) is built.

## 15 Oct

Ari's answers to the 14 Oct evening needs-you list.

- **The resume re-bases the high-water mark: kept** (needs-you 2). A resume now
  never hides a loss:
  - The `lab_resume` event records the high-water mark and the drawdown it
    replaced: `before.hwm`, `after.hwm_replaced`, `after.drawdown_replaced`, beside
    `hwm_rebased_to`.
  - The Weekly's lab line prints the drawdown since inception beside the current
    one: `drawdown y% (z% since inception)`. Since inception is measured from the
    all-time high, the notional or the highest equity ever recorded, which no
    resume moves.
  - `docs/alpha-lab.md`'s header table and the fixture ledger's expected line
    are updated.
  - Fixture, validate_alpha group I: a lab halted at -16% and resumed records
    100,000 and -16% as replaced. The next night's Weekly line reads
    `drawdown 0.0% (16.0% since inception)`.
- **Trend at 20,000 holding 13 names: accepted, no change** (needs-you 3).

Gates, locally: validate_alpha **257/0**. CI: in the report.
