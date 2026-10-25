# Cloud sessions: files you own, queues, one stitcher — brief DRAFT

**Status: DRAFT for the operator's ruling.** Written 25 Oct 2026 (session B, B64) on branch `b64-cloud-sessions-brief` from `origin/b63-6i-brief` (`237a323`). Docs only: no code, config, Makefile or workflow is changed.

**Sources read.** CLAUDE.md; the chain-5, chain-6 and chain-7 stitch notes; `docs/briefs/rulings-2026-10-24.md` and the afternoon rulings, `rulings-2026-10-24-pm.md`, which are on `origin/a61b-feed-repair` (`e8bfc61`) and not on this branch's base; Workplan v7 section 1; the "files shared" sections of the October notes files (65 such sections, counted below). The tooling was read for each shared file: `Makefile`, `scripts/make.sh`, `.github/workflows/registry-check.yml`, `tools/validate_audit_3a.py` (its `PRINTED_COUNTS`, `NEW_KEY_BLOCKS` and `NEW_BLOCK_MEMBERS`), `config/security_master.yaml`, `config/catalogue_commands.yaml` and the readers of each registry.

---

## 1. The shape

**Three sessions.**
- **Two builders** (A and B, as now) each take one paste a night and work on one branch in their own clone.
- **One stitcher-and-librarian** (S) builds nothing new. It stitches the evening's branches into the chain, writes every count, index and generated file, refreshes the Master Guide, writes the box sheet and opens the evening pull request. It also takes the library's papers and the briefs that are docs only, where the work is reading across the repository.

**Pastes become files.**
- The operator writes each paste as `docs/pastes/<id>.md`, where the id is the paste's own, such as `B65`.
- The session's **first commit** on its branch is that file, verbatim. So every branch carries the order it was built to, and a stitcher, a reviewer or a later session reads the paste from the tree, not from a transcript.
- A session never edits its paste after the first commit. A correction from the operator is a new file, `<id>-amend-1.md`.

**The queue.** `docs/pastes/QUEUE.md` lists every paste in order, one row each: the id, the session, the base, the branch, the "run after" condition and the status. The operator adds rows and S updates the status at each stitch; builders never edit it (section 2). The queue replaces today's "run it AFTER B63 is pushed and reported" chains inside pasted text. A paste that arrives mid-run, as B63, B64 and B65 did tonight, waits in the queue instead of interleaving with the running work, which Workplan v7 already warns against ("A message typed into a running session can interleave with its work").

**One pull request an evening.** Only S opens a pull request, from the chain branch to main, after the stitch's CI is green. Builders push branches and report; they open nothing. The operator merges inside the windows (CLAUDE.md, Operating windows: a merge to main is a box write), on the merge evenings Workplan v7 sets: Monday and Thursday.

---

## 2. The files you own

### 2.1 The evidence

Of the 65 "files shared" sections in the October notes, these are the files they name most, by count of notes:

| File | Notes naming it |
|---|---|
| CLAUDE.md | 62 |
| `Makefile` | 54 |
| `metrics_registry.yaml` | 45 |
| `config/catalogue_commands.yaml` | 32 |
| `daily_cascade/weekly_stack.py` | 29 (written two ways in the notes) |
| `monthly_macro/stack.py` | 24 |
| `tools/validate_audit_3a.py` | 22 |
| `source_registry.yaml` | 18 |
| `daily_cascade/stack.py` | 14 |
| `altdata/config.py` | 12 |
| `docs/signal-triage-register.md` | 12 |
| `docs/master-guide.md` | 7 |
| `docs/dated-appendix-queue.md` | 6 |
| `config/security_master.yaml` | 5 |
| `docs/change-orders.md` | 3 |

The stitch notes say what actually conflicted:
- the gate-count line (each branch counted on main's base, chain-5's step 2 to 6);
- the Makefile's gate lines at one anchor;
- the registry's `expected_members` counts (chain-5's "splice");
- `monthly_macro/stack.py`'s hooks at the same insertion points (all three chains);
- the appendix queue's appends at the end (chain-5, chain-6, where Fix 1 was a gate that pinned the queue's last entry);
- the register header's "Batch orders" cell and the change-orders index (chain-5);
- `next_id` in the Security Master (chain-5, and the D28 rule after it).

Union merges of independent lines (most of the registry, `catalogue_commands.yaml`) resolved cleanly every time.

### 2.2 The rule and mechanism per file

| File | Who writes it | The rule | The mechanism | The one-time refactor |
|---|---|---|---|---|
| **CLAUDE.md's count line** (and every other printed count) | S only | No builder edits a count. A builder's paragraph is prose with no count. | `tools/stitch_counts.py --write` rewrites each sentence in `validate_audit_3a.PRINTED_COUNTS` and `ARCH_COUNTS` from the code; `--check` is what the gate already does | the tool, a short one over the existing `counts()` and `PRINTED_COUNTS` (section 3) |
| **CLAUDE.md, the rest** | builders add a paragraph; S places it | One paragraph per branch, at the end of the section its subject belongs to, never inside another's | union at distinct anchors; S orders them at the stitch | none |
| **The Makefile's gate lists** | builders, through a declaration; S never by hand | A gate declares itself in its own file; no builder edits `PY_VALIDATORS`, `SH_VALIDATORS` or `DATA_GATES` | `GATE_KIND = "code"` in each Python gate (the data gates already carry `"data"`); `tools/gate_list.py` lists by kind; the Makefile, `scripts/make.sh` and `registry-check.yml` all call it, so the list still lives in one place | add `GATE_KIND` to 136 Python gates (mechanical); the tool; three callers changed. `validate_deploy.py` and `validate_audit_3a` move with it |
| **`metrics_registry.yaml`** | builders | Add whole new keys or blocks only. Never edit a shared block's `expected_members` or a count; S recomputes them | union merge (it already merges cleanly); `stitch_counts.py` writes `expected_members` from the code | the tool's registry half. **No split into fragments:** 63 Python files open the file by name, so a fragment directory is a 63-reader change for a problem the union merge already solves |
| **`source_registry.yaml`** | builders | One new source block per new source; never edit another's | union merge | none (32 readers open it by name; same reason) |
| **`config/security_master.yaml`** | builders, from a block | Each paste carries its id block in its header (section 4); a builder takes ids only from it and never edits `next_id` | S sets `next_id` to one past the highest id used at the stitch; D28 (3)'s renumbering is then never needed | none in code; the paste header carries the block |
| **`monthly_macro/stack.py`** (and `daily_cascade/stack.py`, `daily_cascade/weekly_stack.py`) | builders, through a hook file | No builder edits the section lists inline; a sub-section joins through a declared hook | `config/stack_hooks/<id>.yaml`: cadence, section, `after:` (the hook it follows) and `module:function`; the stacks iterate the directory in `after:` order and refuse a cycle or a missing anchor | move the existing inline hooks of the three stacks into hook files, one commit, no output change, held by a gate that compares a rendered fixture before and after |
| **`docs/dated-appendix-queue.md`** | builders, one file per entry | Append by adding a file; never edit the queue | `docs/dated-appendix-queue/<paper-slug>/<date>-<id>.md`; S regenerates the index file at the stitch | split the current file; the four gates that read it (`validate_batch14_a1`, `_b2`, `validate_batch15_1`, `_2`) read the directory |
| **`docs/change-orders.md`** | S only | Builders never edit the index | `tools/change_orders_index.py --write`, from each order's filename and first heading | the tool; `validate_batch15_1` reads the index and moves with it |
| **The signal-triage register's header** | S only | The "Batch orders" cell is generated | the same index tool writes the cell | as above |
| **The Master Guide and its HTML** | builders add table rows; S writes the rest | A builder may add a row to a table (the union merges); the "As of" line, Landing next, Figures 2 and 5 and the HTML are S's | S runs `tools/figures/master_guide.py` and `tools/build_paper_html.py docs/master-guide.md` at the stitch | `check_master_guide`'s staleness checks (Figure 5, the HTML stamp) become warnings everywhere, and the stitch's CI fails if any remain (decision 6) |

**Three more files, not on the paste's list, belong in the table by the evidence:**
- `config/catalogue_commands.yaml` (32 notes): union merge, one key per module. No change.
- `tools/validate_audit_3a.py`'s `NEW_KEY_BLOCKS` and `NEW_BLOCK_MEMBERS` (22 notes): each branch adds its block names. They should move to a field on the registry block itself (`audited: true`), so the gate reads the registry, not a list.
- `altdata/config.py`'s `FRED_PULL_SERIES` and the validators that pin counts (`validate_prices`, `validate_st_r5_t1_rest`, `validate_narratives`): the pins should read their number from the code with the stated floor, so a count changes in one place.

---

## 3. Counts computed by a tool at stitch time

`tools/validate_audit_3a.py` already computes every count from the code (`counts()`) and fails a printed count that disagrees (`PRINTED_COUNTS`, `ARCH_COUNTS`). What it lacks is the write side.

`tools/stitch_counts.py`:
- `--check` is the gate's verdict, unchanged.
- `--write` rewrites each printed count in place, in the form the sentence already uses: "one hundred and thirty-nine" stays in words, "283" stays a numeral. It covers CLAUDE.md, the architecture document's store box and the registry's `expected_members`.
- It prints a table of before and after for the stitch notes. It never writes on a builder's branch; S runs it once, after the last merge.

The counts it owns today: the FRED lists (eight named in CLAUDE.md), `FRED_PULL_SERIES`, the writer roster's three counts, the yfinance symbols, the committed CSVs, the four gate counts, the market-state object's dimensions, dials and contradiction rows, and the basket blocks' members. The stitch notes' "The final counts" table becomes this tool's output.

---

## 4. The paste contract

Every paste file opens with a header the session can check before it starts:

| Field | Example | Who checks it |
|---|---|---|
| `id` | `B65` | the file name |
| `session` | `builder-B`, `builder-A` or `stitcher` | the session |
| `base` | the current chain's tip, or main once that chain has merged (Workplan v7's rule) | the session states the SHA in its notes |
| `branch` | `b65-learning-loop-v2` | the session |
| `run_after` | `B64 reported` | QUEUE.md |
| `shared_files` | the files of section 2 it expects to touch | S, at the stitch |
| `sm_ids` | `SM00221-SM00230`, or none | the session takes ids only from it |
| `gates_added` | names, or none | `gate_list.py` |
| `estimate` | hours | the work order |

Then the body, as now: what this is, the rules, the parts, and REPORT BACK.

The session:
- commits the paste verbatim first;
- commits in Parts;
- pushes and reads CI once (`gh run list --branch <branch> --limit 3`);
- writes its notes with a "files shared" section naming every section-2 file it touched;
- reports.

On a kill it pushes what is committed and reports what is not.

The standing rules carry over unchanged:
- no secrets, no `.env`, no units, no sudo, no register writes;
- the Brookfield blocklist at write time;
- names of people stripped from code and registry text, while filed orders stay verbatim (D28);
- nothing written into chester-meme.

---

## 5. The box side

Nothing changes on the box, and nothing in a cloud session reaches it.
- **No access.** A cloud session has no ssh key, no `.env` and no secret of any kind. The deny list's guarantees ("A session never runs unit commands, `sudo` or register writes") hold there by absence as well as by rule. Every code gate seeds its own store, so none needs a key.
- **The box reads main only.** Each wrapper pulls main before it runs (`git pull --ff-only`), and the self-deploy follows main's unit files. A cloud branch is invisible to the box until the operator merges S's pull request inside the windows.
- **The box sheet.** S writes it per chain, as now (`docs/briefs/chain-<n>-box-sheet.md`). It holds the restart and enable commands, the dry runs (the operator's, per the box-dry-runs rule), the backfills and the one-time drops. The operator runs it after the merge.
- **The laptop's role** shrinks to the operator's terminal for the box sheet and the chat-side tasks. Neither moves.

---

## 6. Cost and limits

- **The cloud credit expires on 5 Nov 2026** (the paste). Every step of the migration that depends on it falls before then, or the work falls back to the laptop sessions on the 5th (decision 7).
- **Opus**, the operator's standing choice, for all three sessions.
- **No cost figure is stated here.** No stored figure for the credit's balance or the per-session rate is in the repository. The first week's sessions should record their own usage in their notes, so the second week's plan rests on a measured number.
- **On a kill** (the session's limit, a timeout, or a lost connection), the session pushes what is committed and reports, as on the laptop. Committing in Parts keeps the loss to one Part.
- **What the cloud removes:** the laptop's memory ceiling, which killed background CI waits and gates during these nights. **What it keeps:** CI as the validate ("Push; CI is the validate"). A cloud session may run the gates it touches locally, but its verdict is CI's.

---

## 7. The migration order

1. **This brief ruled.**
2. **The refactor branch** (S's first paste, on the laptop, one night, about 6 hours), docs and tools only, no output change:
   - `stitch_counts.py`;
   - `gate_list.py` with `GATE_KIND` on every gate and the three callers;
   - `change_orders_index.py`;
   - the appendix-queue split;
   - the stack-hook files;
   - `check_master_guide`'s staleness warnings.

   It merges on a merge evening inside the windows. It is a box write like any other, so not 29 Oct to 1 Nov, the Weekly's freeze before the 1 Nov Monthly.
3. **`docs/pastes/` and QUEUE.md created**, with tonight's queue (B65 onward) as its first rows.
4. **One builder in the cloud** on a docs-only paste, to prove the clone, the push, CI and the report.
5. **The second builder**, on a code paste.
6. **S in the cloud**, stitching and opening the evening pull request.
7. **Review on 5 Nov**, when the credit ends: continue paid, or return to the laptop with the refactors kept. The refactors earn their keep either way, because the conflicts they remove are the laptop's too.

Steps 2 to 6 fall between 26 Oct and 4 Nov. The 1 Nov Monthly and its freeze sit in the middle, and the cloud steps (4 to 6) take only docs and post-Monthly branches across them.

---

## 8. DECISIONS FOR ARI

**1. Pastes in a public repository.** `achester-trading/chester-reports` is public (`gh repo view`: PUBLIC). Options: (a) commit pastes verbatim to `docs/pastes/`, as the paste says; (b) commit them to a private companion repository the sessions also clone; (c) commit them verbatim with only the operator's sign-off line removed. **Recommend (a).** The repository already carries every filed order verbatim (D28: "filed orders stay verbatim"), and the pastes contain no secret: the standing rules forbid one. Every builder must be able to read the paste from the tree, which (b) complicates with a second clone. If a paste ever must carry something private, it stays in chat and the file says so.

**2. How a gate joins the list.** Options: (a) `GATE_KIND` in each gate and `tools/gate_list.py` as the one list; (b) one file per gate under a `gates/` directory; (c) keep the Makefile lines and let S resolve them. **Recommend (a).** It keeps CLAUDE.md's rule, that the list lives in one place, while ending the anchor conflict that every chain hit. The data gates already declare their kind this way. (c) is today's practice and cost each stitch a recount.

**3. The registries: one file or fragments.** Options: (a) keep `metrics_registry.yaml` and `source_registry.yaml` single, with builders adding whole blocks and S computing the counts; (b) a fragment directory per branch. **Recommend (a).** The union merges resolved cleanly in all three chains. Only the counts conflicted, and the tool writes those. Fragments would touch 63 and 32 readers that open the files by name.

**4. Security Master ids.** Options: (a) a block of ids in each paste's header; (b) every branch allocates from `next_id` and the stitch renumbers a collision (D28 (3), today's rule); (c) a range per session. **Recommend (a).** A renumbered id is a rewrite of a committed fact on a branch, which the master's own rule ("a stable id that is never reused") was written to avoid. Blocks cost the operator one header line per paste. (c) leaves holes that look like retired ids.

**5. The stack hooks.** Options: (a) hook files under `config/stack_hooks/`; (b) keep inline hooks and let S order them. **Recommend (a).** `monthly_macro/stack.py` conflicted in all three chains, at the same insertion points. A hook file with `after:` makes the order a declared fact, and a gate can hold it. The refactor is one commit with no output change, held by a rendered fixture.

**6. Generated files on a builder's branch.** Options: (a) staleness of Figure 5, the HTML stamps and the indexes is a warning on every branch, and the stitch's CI fails on any that remain; (b) builders regenerate them. **Recommend (a).** Generated files conflict as wholes and are rebuilt anyway; B62 lost a CI round to exactly this. The check stays the same in CI and locally, because the warning is the same everywhere. What changes is that the stitch, not the builder, clears it.

**7. When to migrate.** Options: (a) the refactor branch now, the cloud trial from 27 Oct, all three in the cloud by 2 Nov, a review on 5 Nov; (b) refactors only, no cloud before the credit ends; (c) everything after Doctrine #2 (7–8 Nov). **Recommend (a).** The credit expires on 5 Nov, so (c) forgoes it. The refactors are worth doing either way. A trial on docs-only pastes before the Monthly risks nothing the box reads.

**8. How often S opens a pull request.** Options: (a) on the merge evenings only (Monday and Thursday, Workplan v7); (b) every night; (c) whenever a chain is green. **Recommend (a).** The operator's merge is the box write and belongs inside the windows on a planned evening. Two builders a night fill a chain in two or three nights, which is the cadence the chains have kept since 13 Oct.

---

## Notes

- **Read from another branch:** the afternoon rulings of 24 Oct (D28, D29) are on `origin/a61b-feed-repair` only. D28 (3) is the Security Master rule that decision 4 would replace.
- **The count of 65 notes sections** is a reading of headings that contain "files shared" or "shared files". Files named only in prose outside such a section are not counted.
- **No cost figure** is given (section 6): none is stored.

- **CI:** CI queued, run 40146071056 (at `f270731`). The next paste that touches this branch reads the result once.
