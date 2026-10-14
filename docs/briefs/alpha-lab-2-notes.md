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
