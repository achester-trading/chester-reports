# A97 notes: the Weekly's readability order (W10-1 to W10-3)

**Branch.** `a97-weekly-readability`, from origin/main at `422ea697`. The order
is `docs/pastes/A97-attachment-weekly-readability.md`; D46 accepted it on 31 Oct
2026, decisions 1-4 as recommended.

**Merge timing.** It merges Wed 4 Nov. The first edition is the 8 Nov Weekly.

**Commits:**

| Commit | What |
|---|---|
| `5e4f8ea0` | the paste and its attachment |
| `6723c3dc` | Part 1 |
| `a144f17b` | Part 2 |
| `09f7b061` | Part 3 |
| `b16a2fdb` | a Part 2 fix found by the Monthly's gate |
| `cd5cda66` | the notes |
| the reorder commit | the Weekly draws its charts before its prose, so the précis stays last |

## Part 1 · W10-1, the fallback

**What changed.**

- **`daily_cascade/audit_retry.py`** gains the fallback:
  - `partial()` gives the verdict over a twice-withheld draft;
  - `apply_fallback()` applies it to a result;
  - `figure_only()` and `failed_figures()` read the reason;
  - `MARKER`, `WHOLE_ONLY` and `status()`.
- **Which sentence goes.** Every sentence that carries a failed figure. The role
  audit's quoted span ("closed ... 4.48") places its sentence. Otherwise the
  sentence holding the figure's text is used, matched as a whole token ("5.2" is
  not in "15.29"). The figure list is the audit's whole list where the call
  kept it (`unmatched_figures`); the reason cuts it at six.
- **Removing every sentence that holds the figure** is deliberate. A figure
  correct in one sentence and failed in another loses both, so the published
  text never holds a figure the audit failed.

**The limits (D46 1).** A section stays withheld whole, as today, when:

- more than a third of its sentences fail;
- its first sentence fails;
- it is the Précis or "Our read". I added the stack's read ("The read", the
  Weekly's and the Monthly's synthesis) on the same ground: its five lines
  depend on each other.
- any fault is not a figure's. Filler, a misstated state, length, shape and
  vocabulary are not cured by removing a sentence. The figure faults are the
  numeral audit, the role audit and the bare large change.
- a failed figure cannot be placed in a sentence;
- the remainder then fails the section's own checks.

**The remainder is held to every rule.** Each caller re-runs its post-audit
checks on the remainder, without its markers:

- the Weekly: `daily_cascade/stack_prose.py`, whose checks were extracted into
  `checks()` unchanged;
- the Monthly: `monthly_macro/prose.py`, through `post_faults()`, the same calls
  `_attempt` makes.

Any fault keeps the section whole. No figure is edited. The audit's verdicts are
untouched; the fallback runs only after the second attempt and only removes.

**Where it is wired.**

- The Weekly: `stack_prose.FALLBACK_CADENCES = ("weekly", "monthly")`.
- The Monthly: `prose.write_all`, after its retry loop.
- The close keeps the whole-section rule.

**The status line.** It reads "Commentary published, k sentence(s) withheld by
the figure audit.":

- in the section's footnote (`stack_render.foot_parts`);
- in a Monthly sub-section's notes (`monthly_macro/stack.apply_prose`);
- in the archived edition: `partial`, `withheld_sentences` and `fallback` join
  the prose record.

**The run log** names each withheld sentence and its reason ("audit fallback:
weekly/tape sentence withheld (figure audit: 0.30%): ...") and the status.

**The withheld-drafts log.** `altdata/withheld_log.py` writes a `kind` on every
line, "whole" or "partial", and `partial_in()` collects the partial
publications. `altdata/system_metrics.py` counts whole withholds as before and
partials apart (`partials()`). `validate_system_metrics` pins `withheld()`'s
return, and it is unchanged.

**The dry-run replay.** The script is
`$TEMP/.../scratchpad/a97_replay.py`, over the two run logs outside the repo. It
reads each section the log withheld twice: its second draft, read whole across
the log's lines, and its second reason. That is everything the logs keep, so the
replay applies the fallback's own limits but not the live re-check of the
remainder, which needs the edition.

**28 Oct: 10 of the 20 withheld sections would have published, with 10
markers** (one each):

| Section | Sentences withheld |
|---|---|
| `month_in_markets` | 1 of 9 |
| `theme:liquidity_plumbing` | 1 of 9 |
| `theme:geopolitics_reserve` | 1 of 10 |
| `looking_ahead` | 1 of 8 |
| `pillar:4` | 1 of 7 |
| `pillar:7` | 1 of 3 |
| `block:plumbing:yields` | 1 of 4 |
| `block:positioning:cftc` | 1 of 4 |
| `summary:narratives` | 1 of 4 |
| `summary:slow` | 1 of 5 |

Ten stay whole:

| Reason | Sections |
|---|---|
| the first sentence fails | `pillar:1`, `stack:slow`, `block:plumbing:liquidity`, `summary:plumbing` |
| more than a third fail | `pillar:2` (2 of 5), `block:positioning:sectors` (1 of 2) |
| a fault that is not a figure's | `theme:sentiment` (a misstated state), `stack:tape` (filler) |
| the whole-section rule | `our_read` |
| a figure list cut at six | `theme:fiscal_dollar` (8 failed, 6 listed); live, the audit's whole list would decide it |

**29 Oct: 4 of the 13 would have published, with 8 markers:**

| Section | Sentences withheld |
|---|---|
| `theme:fed_path` | 2 of 8 |
| `theme:equity_positioning` | 1 of 11 |
| `theme:sentiment` | 3 of 11 |
| `pillar:2` | 2 of 7 |

Of the nine that stay whole, the first sentence fails in five and a non-figure
fault stands in four.

The replay reads reason strings, so A90's binding change does not move it.

**Fixtures** (synthetic; gate group A):

- nine sentences with one bad publishes with one marker, the other eight
  byte-equal;
- four of nine withholds whole; three of nine publishes;
- a bad first sentence withholds whole;
- the Précis, `our_read` and the read withhold whole on one bad sentence;
- filler withholds whole;
- a first failure is never the fallback's;
- the remainder's re-check;
- the cut list, the role span and the bare delta;
- the whole-token match;
- the footnote, the withheld log's kinds and system metrics;
- the Monthly's marks;
- the wiring, held by source.

## Part 2 · W10-2, the "What to see" line

**A finding that changed the design.** Both editions write their sections' prose
*before* they draw their charts:

- the Weekly: `weekly_stack.produce`, prose at the consistency gate and charts
  after;
- the Monthly: `monthly_macro/stack.produce`, "after the prose, as the
  Weekly's".

So the section's prose call cannot see a chart's data block. The lines come from
**one call per section, fed only that section's charts' blocks**, metered as
`see:<section>`. The section's own prose, its prompt and its audits are
untouched. **This differs from the order's "the section's model call"; it is for
the operator to accept or redirect.**

**The Weekly's chart drawing now comes before its prose** (the reorder commit,
after the notes' first commit). CI's
first runs failed `validate_weekly_storyline`, which holds the précis as the last
commentary written; only the playbook pass may follow it. Lines written after
the drawing came after the précis. So:

- only the drawing moved: the plan, the data reads and the draw calls, W3's
  levels with them;
- the alias check, the placement into sections and the edition's chart record
  stay where they were, after the layout;
- the order is now: draw, the sections' prose, the lines (grouped by the
  Weekly's fixed `PLACE` map), the précis, the playbook;
- the drawing reads only what `build()` made. Nothing between the prose and the
  old drawing point changes what it reads: the précis, the playbook, the book's
  terms, the coverage table and the layout (which rewrites the gap table's
  status column).

The Monthly draws after its sections' prose as before. Its lines follow the
drawing and come before the executive summary, which stays its last prose.

**What changed.**

- **`daily_cascade/chart_lines.py`:**
  - `data_block()` derives each chart's block from what it returned: `series`
    (dated lines, bars or returns), `stats`, or W3's `levels`. The block holds
    the series, its window (from, to), first, last, change, high and low.
  - A chart that returned none of these (the dealer panel, W10, W7's levels)
    has no block and no line, and no call is made for it.
  - `check_line()` runs at most 30 words (refused before the audit), then no
    action word (buy, sell, long, short, add, trim, and their forms), then the
    numeral audit against that chart's block alone.
  - One revision is made for the failing lines. A second failure leaves
    `see_withheld` on the chart, which prints without the line.
- **Rendering:** `stack_render._chart_html` prints "What to see: ..." beneath
  the caption, and `md_charts` does the same in the Markdown.
- **Wiring:** both editions' `produce()`, when narrative. The Weekly calls
  `write_groups(groups_from(PLACE, charts))`; the Monthly calls `write(ed,
  charts)`, grouped by `charts_rendered`.
- **Cost:** about one call per section that carries charts (the Weekly's 11
  charts sit in five or six sections), plus a revision where a line fails.

**The fix found by the Monthly's gate** (`b16a2fdb`). A Monthly Mechanics chart's
bars carry no high, so its block faulted and the section's other charts lost
their lines. The range now falls back to the closes, and each chart's block is
built on its own.

**Fixtures** (gate group B):

- the block is the chart's own;
- the line renders from a synthetic block in one call fed that block alone;
- it prints beneath the caption, in HTML and Markdown;
- a figure not in the block fails, is revised once and is withheld, and the
  chart prints without it; a passing revision prints;
- a 31-word line is refused before the audit, and 30 words reach it;
- six action words are refused;
- a chart with no block has no line and no call;
- a close-only series, and an odd chart beside a good one;
- one call per section;
- the Weekly's grouping by `PLACE`;
- the order (draw, prose, lines, précis), held by source.

## Part 3 · W10-3, the Coverage table

**What changed.**

- **`daily_cascade/coverage.py`.** Rows are grouped by the registry's
  **`family` field**: price, rate, spread, release, quantity, conditions,
  ratio. A lens-excluded key has none and counts under "other"; a stored key the
  registry does not know is "unregistered".
  - **Why not `source`:** it has 108 values. On the laptop's store the family
    grouping gives 28 rows over 3,095 keys; source would give well over a
    hundred.
- **The states, from the store check's lists:**

  | State | Comes from |
  |---|---|
  | stored | `current` |
  | stale | `stale`; "dead?" counted in the reason |
  | awaiting | `no_rows`, and `quiet`'s not_yet_sourced |
  | declared gap, refused, held, superseded | `declared` and `quiet`, by status |
  | stored, unregistered | `unregistered` |

  Stale and superseded are not in the order's list. Each is the check's own
  state, and folding it into "stored" would misstate it.
- **"Unvalidated" prints no row.** It is a signal's tag ("descriptive;
  unvalidated, n=0"), not a key's, and no list in the store check holds it. The
  module says so.
- **The other columns:**
  - **Count.**
  - **Reason:** where declared. A key in a reason prints as the edition names it
    everywhere else (`labels.metric`), never as its id; `validate_weekly_edits`
    refuses any id in the rendered edition.
  - **Since:** for a stored or stale row, the newest observation; for a declared
    or awaiting row, the registry's newest `added_date`; "—" where it records
    none. The registry keeps no date a status changed, and the note beneath the
    table says so.
- **`tools/check_store_registry.check()`** also returns `current`, the
  registered keys stored and in allowance. `report()` never reads it, so **the
  CLI's output is unchanged**; the gate holds it. Coverage calls `check()` as a
  function over the store opened read-only and never runs the CLI.
- **Where it prints.** `ed["sections"]["book"]["coverage"]` is the Weekly's
  section 10. It prints last before the footnote, after the paragraphs, so it
  is at the end of section 10 and before the Detail Tables. The Monthly's
  appendix detail block carries the same table. Rendering is through
  `stack_render.coverage_html` (section, opener and detail layouts) and
  `md_coverage`.

**Fixtures** (gate group C):

- a synthetic store and registry with one key per state renders one row each;
- the counts match: nine registered plus one unregistered, each once;
- no key twice;
- reasons, "dead?" and dates;
- no registry id in a cell;
- the store is unchanged;
- no store, no table;
- `report()`'s output unchanged and the check called as a function;
- placement in the Weekly, the Markdown and the appendix.

## Part 4 · Gates

`tools/validate_weekly_readability.py`, 56/0. One Makefile line. The count goes
from 135/132 to 136/133, by hand: main has no stitch tools.

**Merge-order recount.** A92, A93, A96 and A97 each make the same +1 on their
own branches, so the last of the four to merge sets 139/136.

Each gate ran one at a time in the foreground, on the final branch unless noted:

| Gate | Result |
|---|---|
| `validate_weekly_readability` | 56/0 |
| `validate_weekly_stack` | 83/0 |
| `validate_weekly_edits` | 91/0 |
| `validate_weekly_storyline` | 31/0 (it failed in CI before the reorder) |
| `validate_weekly_complete` | 96/0 |
| `validate_weekly_analytics` | 35/0 |
| `validate_weekly_calendar` | 44/0 |
| `validate_weekly_opener` | 46/0 |
| `validate_digital_addendum` | 94/0 |
| `validate_readability` | 67/0 |
| `validate_monthly` | 360/0, 1 skipped |
| `validate_audit_fixes` | 135/1. The one failure, B84's ordinal expectation, fails identically on main `422ea697`. A91 updated it on `a90-monthly-dryrun-2`, and on the dry-merged tree the gate is 158/0. |
| `validate_numeral_audit` | 172/0 |
| `check_registry` | OK |
| `validate_monthly_stack` | 267/0, run whole, no traceback |
| `validate_system_metrics` | 21/0 |
| `validate_audit_3a` | 88/0 |
| `validate_b51_registry_html` | 25/0 |
| `validate_feed_repair` | 50/0 |
| `validate_gates` | 32/0 |

`validate_weekly_edits` group 9 required the new gate's temporary directory to
go through `tools/gate_tmp.py`, and it does.

## The dry merge against A90

**Result:** `git merge --no-commit --no-ff origin/a90-monthly-dryrun-2`
(`f8819b62`) merged automatically, with no conflicts. A90 touches
`altdata/numeral_audit.py`, its fixture, `validate_audit_fixes` and its notes;
A97 touches none of them.

**Gates on the merged tree:**

| Gate | Result |
|---|---|
| `validate_weekly_readability` | 54/0 (53/0 at the time; the close-only case came after) |
| `validate_numeral_audit` | 172/0 |
| `validate_audit_fixes` | 158/0 |

The merge was aborted, not committed. The two do not collide: A97 reads the
audit's verdicts and reasons and changes none of its binding.

## Box steps after the merge

None beyond the deploy. No unit, timer, store write, migration or key. The first
Weekly to carry all three is 8 Nov.

**One thing to watch.** The Coverage table runs the store check's two grouped
queries over the box's store, read-only, once per edition. On the laptop's
1.7 GB store it finished well inside the gate's five-minute limit; the Weekly's
run log will show its time.
