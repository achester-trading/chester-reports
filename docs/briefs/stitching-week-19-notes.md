# The stitching for the week of 19 Oct (session A, 15 Oct 2026)

Next week's nine branches are one merge chain on top of Friday's tip. Each branch merges the tip of the branch before it, so each holds everything above it, and next week's merges to main go in this order with no conflicts. Branch-only: nothing merged to main, deployed or run on the box. Session B's `6e-metric-lenses` is untouched.

**w-1-3c-weekly-polish has not moved past `fb67bf3`**, so aud-1 needed no merge and its tip is unchanged.

## The order, the stitched tips and their CI

| # | Branch | Stitched tip | Merged in | CI |
|---|---|---|---|---|
| 1 | aud-1-data-fixes | `63ec6a8` (unchanged) | none (already holds `fb67bf3`) | #414 green |
| 2 | aud-2-ops-security | `4a40842` | aud-1 `63ec6a8` | #429 green |
| 3 | aud-3a-catalogue | `2522987` | aud-2 `4a40842` | #430 green |
| 4 | aud-3c-quality | `dafb54d` | aud-3a `2522987` | #431 green |
| 5 | aud-3d-fred-history | `358122e` | aud-3c `dafb54d` | #432 green |
| 6 | alpha-lab-2 | `1df8b05` | aud-3d `358122e` | #433 green |
| 7 | t3-6-monthly-polish | `9ce3da2` | alpha-lab-2 `1df8b05` | #434 green |
| 8 | vp-1-volume-profile | `c601a2a` | t3-6 `9ce3da2` | #435 green |
| 9 | aud-3b-security-master | `928884e` | vp-1 `c601a2a` | #436, see the CI section |

Each merge kept both sides and was pushed before the next began.

**aud-3b's 15 Oct follow-ups were on origin before it was stitched:** `f253ca5` ("AUD-3b (15 Oct): the answers…") and `8900f8e` ("AUD-3b (15 Oct, later)…"), the tip. By then `6e-metric-lenses` was on origin, so session B had moved on.

**Before the stitching, on aud-3c (Part 1):** `bead491` holds the AUD-3c rulings (the VIX floor, ^TNX/^TYX after the backfills, `fred:backfill` labelled backfill, policy rates as steps): CI #428, green. The aud-3c notes' "15 Oct" section ends on "CI for this commit: see the line below", and this is that line. It is recorded here and not on aud-3c, because a commit there now would have to be stitched down the chain again.

**The gate count, recounted from the Makefile at every merge** (code gates = the Python list plus `smoke_test.py` plus the three shell gates; six data gates throughout):

| After | Code gates | Python |
|---|---|---|
| aud-1 + aud-2 | 76 | 73 |
| + aud-3a | 77 | 74 |
| + aud-3c | 78 | 75 |
| + aud-3d | 79 | 76 |
| + alpha-lab-2 (three gates) | 82 | 79 |
| + t3-6 (none) | 82 | 79 |
| + vp-1 | 83 | 80 |
| + aud-3b | **84** | **81** |

## Each conflict, and how it was resolved

**2. aud-2 ← aud-1**
- `CLAUDE.md`: the gate count, recounted.
- `Makefile`: `validate_audit_2.py` and `validate_audit_1.py`, both kept.
- `tools/validate_backup.py`: aud-1's budget check replaces aud-2's caps-sum statement (meeting a).
- `chester-backup.service` merged without a conflict. It holds everything meeting a asks for (below).

**3. aud-3a ← aud-2**
- `CLAUDE.md`: the count, plus AUD-3a's catalogue paragraph and AUD-2's model-meter paragraph, both kept.
- `Makefile`: three audit gates.
- **Where the branches meet** (no conflict, but a gate failed until fixed):
  - aud-1's `altdata/compact_fred.py` runs as `python -m`, and AUD-3a's catalogue gate requires a line for every such module. Added to `config/catalogue_commands.yaml`.
  - AUD-3a's words-count self-test planted its wrong count by replacing the literal "seventy-five code gates". It now plants one beside whatever count is printed, the same text as aud-3c's.

**4. aud-3c ← aud-3a**
- `CLAUDE.md`: the count, plus AUD-2's and AUD-3c's paragraphs.
- `Makefile`.
- `daily_cascade/stack_close.py`: AUD-2's model-meter line, then AUD-3c's data check, both before the render.
- `tools/validate_stack.py`: AUD-2's `group_m`, then AUD-3c's group I.

**5. aud-3d ← aud-3c**
- `CLAUDE.md` count; `Makefile`.
- **Where they meet:** a commands-table line for `altdata.fred_history`. Its writer stores source `fred:backfill`: the string AUD-3c's ruling labels backfill, and the one AUD-3a reads as `fred`. They agree.

**6. alpha-lab-2 ← aud-3d**: eight files, the most of any merge. Meeting b is below.
- `CLAUDE.md`:
  - the count;
  - the deny table's two rows: each side only added to one row, so the rm row is aud-1/2's (the wider list, `git clean -fdx` included) and the register row is the lab's (`alpha.promote retire`, `alpha.governor resume`).
- `Makefile`: the chain's gates, then the lab's three.
- `.gitignore`: the lab's agenda files and aud-1's secrets, databases and outputs, both kept.
- `daily_cascade/stack_close.py`: the model meter, the data check, the lab line.
- `deploy/systemd/README.md`:
  - **both branches added a section 13.** AUD-2's (memory caps and the OOM order) stays 13, because about fifteen unit files cite "README.md section 13" for it.
  - The lab's loops become **section 14**, and the lab's own three references move with it: the README's own line, `chester-alpha-proposer.timer` and `docs/alpha-lab.md`.
- `chester-backup.service`: the union of ReadWritePaths, both comments.
- `scripts/backup_retention.py`: the lab's `--prefix` and aud-1's `--mode`/`--remote`. In db mode the family pattern check stays.
- `scripts/rclone_sync.sh`: meeting b.
- **Found in the auto-merge and fixed:** git merged `prune_db` cleanly, but its budget-stop line set aud-1's `PRUNE` directly, where the lab's version of the function returns through `PRUNE_OUT`. A budget-stopped prune would have reported the wrong status. It now sets `PRUNE_OUT`.
- **Gate texts the merge moved:**
  - `tools/validate_alpha.py` counted `daily_line(` in `stack_close.py` and expected one. aud-2's `model_meter.daily_line(` shares the name, so it now counts the lab's bare call.
  - `tools/validate_backup.py`'s ruling-8 and copy-cap checks are text checks; they accept the budgeted forms (below).

**7. t3-6 ← alpha-lab-2**
- `CLAUDE.md` count only. T3.6 adds no gate.
- `monthly_macro/v2.py` merged clean: T3.6's edits sit beside AUD-3a's `level_units_of`.

**8. vp-1 ← t3-6**
- `CLAUDE.md`: the count, and VP-1's volume-profile paragraph after the chain's.
- `Makefile`.
- `monthly_macro/stack.py`: the Monthly payload carries both T3.6's `long_frame_columns` and VP-1's `volume_profile`.
- `tools/validate_stack.py`: groups M and I, then VP-1's group V.
- **Where they meet:**
  - a commands-table line for `altdata.volume_profile`;
  - AUD-3a's "newly resolved keys" check assumed every key new since `fb67bf3` came from its block fixes. VP-1 registers 18 metrics one by one (`calc.vp_*`). The check now holds the block keys to the resolver fix, still 164, and counts the one-by-one metrics apart.

**9. aud-3b ← vp-1**
- `CLAUDE.md`: the count, then AUD-3b's Security Master paragraph, then the Alpha Lab's Layer X section.
- `Makefile`.
- `.gitattributes`: AUD-3b's `docs/interface/* text eol=lf` and the lab's inbox fixtures `-text`, both kept.
- **Where they meet:** commands-table lines for `altdata.figi`, `altdata.listings` and `altdata.security_master`. Meeting c is below.

## The three meetings

**a. aud-2 meeting aud-1** (stitch 2)
- **The backup unit:** aud-2's `TimeoutStartSec=2h`, `MemoryHigh=1.2G`, `MemoryMax=1.5G`, `OOMScoreAdjust=500` and its 2h comment (the sweep's own 105-minute budget ends it; 2h is the backstop).
- **ReadWritePaths, the union:** aud-1's `-%h/backups/chains` is included. After stitch 6 the lab's `-%h/chester-data/inbox/lab` is too.
- **`validate_backup`:** aud-1's budget check replaces aud-2's caps-sum statement: budget 105m + kill-after 1m + 10m fits inside 120m.
- **Locally**, in a clean worktree: validate_backup, validate_systemd_units, validate_audit_1, validate_audit_2 (25/0) and validate_gates (31/0) all passed.

**b. alpha-lab-2 meeting aud-1** (stitch 6). `scripts/rclone_sync.sh`:
- **Prunes:** the chester and the alpha-* prunes each start only through `can_housekeep`, with 10 minutes of the budget left, the same as the zip prune and the inbound pulls. Short of that, each is deferred to the next night and says so (`db/ prune: deferred …; alpha: deferred …`).
- **Copies:** the lab's inbox and outbox copies each start only with 3 minutes of the budget left, as a tree does. Each one's 5-minute cap is cut to the minutes left less 2.
  - Short of that, it is skipped, logged `SKIP lab-inbox -- sweep budget spent`, and named in the status line as `lab skipped: lab-inbox(budget) lab-outbox(budget)`.
  - As before, the lab never touches RC.
- **The fixture**, a new LAB BUDGET group in `tools/validate_backup.py`, runs three nights on the fake clock:
  - a normal night: the alpha snapshot goes to `db/` and never to `data/`, its prune runs, and both copies run under 5m caps with nothing named;
  - a short night (`db=97`): the inbox starts with "cap 1m, 3m of the budget left", and the outbox at 2 is skipped and named, exit 0;
  - a spent night (`db=100`): both copies are skipped and named, and both prunes are deferred and never listed.
- validate_backup **87/0** locally, in a clean worktree.

**c. aud-3b meeting aud-1** (stitch 9)
- **`altdata/listings.py age [--today D]`:** the newest snapshot's age in sessions, counted by the session calendar from the snapshot's day (exclusive) to today (inclusive). So a weekend or a holiday is no miss.
  - Fresh up to `MAX_AGE_SESSIONS = 2`, stale past it, none without a snapshot.
  - Exit 3 on a fault, so a crash never reads as stale.
- **`scripts/check_heartbeat_cron.sh`:** a warning-only check, like the events ingest's. It never changes the verdict or the exit code. It logs the age line and `WARNING listings: the snapshot is <state> …`, and puts `listings=<state>` in the log line and the status file.
- **The fixture**, in `tools/validate_heartbeat_caller.sh`:
  - Friday read on Monday: fresh;
  - Wednesday read the Friday after Thanksgiving: fresh;
  - two sessions: fresh;
  - four sessions: stale, with the warning and the count logged, verdict ok, exit 0;
  - no snapshot: none, exit 0;
  - the skip switch.
- **Not run to the end locally.** Claude Code stopped the gate because the laptop ran low on memory (15 Oct, afternoon). It had passed about 49 checks with no failure, before reaching the listings group. As the paste rules, I did not retry it; CI is the verdict (#436 for the merge, and this notes commit's run).

## Gates run locally

One at a time, only those whose files a conflict or a meeting touched. Run in a clean worktree where the laptop's own `data/` would interfere.

- validate_backup **87/0**;
- validate_systemd_units 112/0;
- validate_audit_1, validate_audit_2 25/0, validate_audit_3a 83/0 (after each of stitches 3, 5, 8 and 9);
- validate_gates 32/0; check_library 27 papers 0/0;
- validate_quality 48/0; validate_fred_history 25/0;
- validate_alpha 257/0; validate_alpha_no_orders 63/0;
- check_registry OK;
- validate_heartbeat_caller: stopped by the low-memory guard at about 49 checks, all passing, before the listings group. Left to CI.

Left to CI because they render a PDF: validate_stack, validate_monthly_stack. Every other gate is left to CI too.

**Two local results to explain:**
- **validate_backup's "chain zip read the database"** fails in the laptop's main checkout because `data/pin_log.csv` exists there. It passes on aud-1's own tip and on every stitched tip in a clean worktree, so it is the laptop, not the merge.
- **validate_security_master fails one check locally:** `jsonschema` is not installed in the laptop's venv. It is in `requirements.txt`, CI installs it, and CI is green on every tip.

## The EL pair: a trial merge, not committed

`el-2-3-rollup` (`03d0ece`, based on `84852af`, 9 commits) trial-merged into the final tip `928884e` in a scratch worktree, then aborted.

- **One conflict: CLAUDE.md's gate count.** EL's line says seventy-six (seventy-three Python) and **five** data gates. With EL's two new gates (validate_packets, validate_rollup) the merged Makefile counts **eighty-six code gates (eighty-three Python, three shell) and six data gates**, which is the line to write on Friday.
- **Everything else, 19 files, merged clean.** That includes `monthly_macro/payload.py`, `monthly_macro/stack.py`, `register/*`, `tools/decide.py`, `config/risk_limits.yaml` and `config/setups.yaml`.
- `tools/decide.py` keeps AUD-3a's `CLIENT_IDS["whatif"]` preview default.
- The three Python files both sides touched compile.

## Left for a later paste, as the paste said

AUD-3a's items that wait on aud-1:
- **The as-of join's source tier** read through `altdata/source_ids.py`. `altdata/observations.py` is aud-1's file.
- **Each writer onto its registered source id:** `daily_close`, `book_z`, `narrative_register`, `paper_bid_chain` and `alt_asset:<family>` are registered and still written as they were.
- **`altdata/loggers/borrow.py`'s client-id literal** onto `altdata/ibkr_clients.py`'s table. The gate already checks the literal against the table.

## Needs you

1. **README section numbers.** AUD-2's memory caps keep section 13, and the lab's loops are now section 14. The unit files cite 13 for the caps, so I renumbered the lab's. OK?
2. **The lab copies' threshold.** They take a tree's rule: start with 3 minutes left, cap cut to fit, skipped and named past that. The prunes take the housekeeping rule (10 minutes, deferred). The paste said "skipped and named" for the copies and "deferred like the other prunes" for the prune, and I read that as these two rules. Say if the copies should wait for 10 minutes instead.
3. **The listings age counts today's session.** The 06:45 pull is due before the 08:30 heartbeat, and the warning comes past two sessions. So one failed pull is silent; two in a row, plus that morning's, warns. Tighten to one?
4. **Gate texts I changed on other sessions' branches**, each to keep both sides' behaviour, worth a look:
   - `validate_alpha`'s hook count;
   - `validate_backup`'s ruling-8 and copy-cap patterns;
   - `validate_audit_3a`'s new-key check (mine, widened for VP-1's metrics).
5. **The EL pair on Friday:** the one conflict is the count line above (86/83, six data gates).

## CI

The table above records each branch's CI, read once each. This notes commit is the last on aud-3b; its run is below.

## Monday's fold (session A, 17 Oct 2026)

The Friday merges are done, and main (`1148c66`) now carries the 25 Friday branches, the EL pair among them. This pass makes Monday's chain clean against that main and applies the three fixes the Friday stitching deferred. Branch-only: nothing merged to main, deployed or run on the box. Session B's `6e-rest` and `st-r4-tranche-1b`, and my own `st-r5-*` branches (which fold on Tuesday), were not touched.

### Monday's merge order

1. `post-friday-fixes`
2. `aud-1-data-fixes`
3. `aud-2-ops-security`
4. `aud-3a-catalogue`
5. `aud-3c-quality`
6. `aud-3d-fred-history`
7. `alpha-lab-2`
8. `t3-6-monthly-polish`
9. `vp-1-volume-profile`
10. `aud-3b-security-master`
11. `docs-batch-7`

**Branch *k* carries 1 to *k*−1.** Merged in this order, each is a fast merge of what is already reviewed. Merging out of order would bring the earlier branches in with it.

**`docs-batch-7` (`7b4f821`) was not folded**, because the paste does not name it for the fold. It adds one file, the Batch 7 change order. A trial merge onto aud-3b's new tip (`git merge-tree`, nothing committed) is clean.

### post-friday-fixes

- **Tip `129caae`**, cut from `origin/main` at `1148c66`. Notes: `docs/briefs/post-friday-fixes-notes.md`.
- **Fix 1. The filler rule exempts code-written tagged lines.**
  - `stack_prose.filler_faults(..., code_written=True)` passes a line that ends on "(descriptive; unvalidated, n=N)".
  - A model's paragraph is never exempt.
  - The rule's gate, `validate_no_filler`, gains group F, built on SR-43/49's anchors line itself: 26/0.
- **Fix 2. AQ-8a's official gold leg reads the IMF IFS writer's series.**
  - The leg is now `imf.ifs.gold_net_purchases_oz.total`, a flow summed over three months, read with its country count. It replaces SAFE's China holdings.
  - `imf.ifs_official_gold_oz` is superseded by it.
  - The fixture follows in `validate_attribution`: 85/0.
- **Fix 3. The Ahead classes are unchanged**, as ruled: `boj_decision` tier 2; `treasury_buyback`, `jgb_auction` and `weekly_release` tier 3.
- **CI:** see the CI section below.

### The new tips

The count column is code gates / Python, three shell gates throughout, recounted from each merged Makefile; the data gates stay six.

| # | Branch | Was | New tip | Merged in | Count |
|---|---|---|---|---|---|
| 1 | aud-1-data-fixes | `63ec6a8` | `ff6af51` | post-friday-fixes `129caae` | 77 / 74 |
| 2 | aud-2-ops-security | `4a40842` | `1072a85` | aud-1 `ff6af51` | 78 / 75 |
| 3 | aud-3a-catalogue | `2522987` | `9f027ee` | aud-2 `1072a85` | 79 / 76 |
| 4 | aud-3c-quality | `dafb54d` | `531d158` | aud-3a `9f027ee` (merge `c9b43a2`), then the count self-test fix | 80 / 77 |
| 5 | aud-3d-fred-history | `358122e` | `8c71795` | aud-3c `531d158` | 81 / 78 |
| 6 | alpha-lab-2 | `1df8b05` | `b0d391f` | aud-3d `8c71795` | 84 / 81 |
| 7 | t3-6-monthly-polish | `9ce3da2` | `a3cba85` | alpha-lab-2 `b0d391f` | 84 / 81 |
| 8 | vp-1-volume-profile | `c601a2a` | `427a93b` | t3-6 `a3cba85` | 85 / 82 |
| 9 | aud-3b-security-master | `2fb1048` | this notes commit | vp-1 `427a93b` (merge `c31ff64`), then the listing fix `c5175a1` | 86 / 83 |

Each branch was pushed before the next merge began.

### CLAUDE.md's count line, as resolved

On aud-3b, the tip of the chain:

> **`make validate` runs every gate** — eighty-six code gates (eighty-three Python, three shell) and six data gates, no network, no box.

This is the line the Friday EL trial predicted (86/83, six data gates).

- **The count gate confirms it.** `validate_audit_3a` group F: **84/0** on aud-3c's tip and again on aud-3b's.
- **Main's CLAUDE.md said "five data gates"** (EL's line) while its Makefile holds six: `validate_imf_china` came with imf-ifs-gold. Every resolution says six, the Makefile's number.
- **The EL pair added two Python gates, `validate_packets` and `validate_rollup`**, not one Python and one other as the paste put it. Main counts 76/73 against aud-1's 75/72 because aud-1 carries `validate_audit_1`, which main lacks. Each line above is the merged Makefile's own count.

### Other conflicts

- **None textual.** At every merge the one conflict was the count line, except t3-6, which had none (T3.6 adds no gate).
- **One meeting** (no textual conflict, but a gate failed until fixed), on **aud-3c**:
  - AUD-3a's count self-test planted a wrong count by matching a hyphenated number word.
  - At eighty code gates, the first one-word count, it planted nothing, so `validate_audit_3a` failed one check: "a count in words is read and caught too".
  - The plant now matches either form, anchored on the count line, and checks the plant took (`531d158`). It is on aud-3c, the first tip where the count is one word, and flows down the chain from there.
  - This is a mechanical change to a gate text on AUD-3a's own gate, the same kind as the week-19 stitching's.

### aud-3b's fix: a missed morning's listing start

Ruled 15 Oct (`docs/briefs/aud-3b-notes.md`, needs-you 9) and built in `c5175a1`:

- **When a session falls between two snapshots** (the 06:45 job missed a morning), a listing first seen on the later one starts on **the day after the previous snapshot**, with **`from_known: false`**.
- **Sessions are counted by the session calendar** (`derived.sessions_between`), so a weekend or a holiday is no miss.
- **The master's known date still wins** where it falls in the gap.
- **Ticker changes and reuse keep the snapshot date**, because the ruling names new listings. See needs-you 2.
- **Code:** `altdata/ticker_history.py`, `_missed_morning` and the new-listing branch of `build`.
- **Fixture:** `tools/validate_security_master.py` group L, **90/0**:
  - consecutive sessions keep the snapshot date;
  - a **one-day gap** (Mon 19, Tuesday missed, Wed 21) starts Tue 20, from_known false;
  - a **three-day gap** (Mon 19, Tue to Thu missed, Fri 23) starts Tue 20, from_known false;
  - a weekend keeps the snapshot date;
  - the bound counts from the snapshot just before the listing appeared;
  - the master's date inside the gap wins;
  - a ticker change across a gap keeps the snapshot date.
- The aud-3b notes' needs-you 9 now records the ruling and the build.

### Gates run locally

One at a time, only those this pass wrote or changed:
- validate_no_filler **26/0**;
- validate_attribution **85/0**;
- validate_audit_3a **84/0**: the count gate, as the paste asks, run on aud-3c and on aud-3b;
- validate_security_master **90/0**. The week-19 local failure on `jsonschema` did not recur.

Every other gate is left to CI.

### Needs you

1. **The EL pair's gate kind.** The paste said one of EL's two gates is Python. Both are Python in the Makefile, and the count is written from the Makefile. If one was meant to be a data gate, it would need `GATE_KIND = "data"` and a move to `DATA_GATES`. That is EL's branch, already on main.
2. **A ticker change after a missed morning** still takes the snapshot date, which states the new ticker's start too late by the missed days. The ruling named new listings only. Say if ticker changes and reuse should take the same lower bound.
3. **docs-batch-7 is last on Monday** and merges clean onto this tip. Nothing to do unless it moves.

### CI

| Branch | Commit | Run | Result |
|---|---|---|---|
| post-friday-fixes | `129caae` | 39029276141 | queued at the first read; see below |
| aud-3b-security-master | this notes commit | recorded at the next read | |
