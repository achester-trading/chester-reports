# b60-reading-budgets: the reading budgets ruled 24 Oct (session B, 24 Oct 2026)

**What it is.** Rulings D19 and D20 of 24 Oct 2026: depth over brevity.
- **Budgets become targets, never caps.** Nothing is cut or withheld for length; an edition over its target prints a one-line note at the foot.
- **The close:** 5 minutes becomes 10.
- **The Weekly:** 20 minutes becomes 35.
- **The Digital Assets addendum:** the 52-line cap is replaced by about 1,500 words (about 7 minutes), and the cyber (item 77) and protocol (item 78) lines move from the incidents footnote into the body.
- **The Monthly:** unchanged at 55 minutes.

**Built now; merged after the 1 Nov Monthly** (no Weekly edit in the 29 Oct-1 Nov freeze); ratified at Doctrine #2 (7-8 Nov). Branch-only: pushed, not merged, nothing on the box, no unit, no secret.

## Base

- **Branch:** `b60-reading-budgets`, from `origin/b59-trigger-sources` at `e5ae3e5`, B59's tip when B60 began.
- **B59 moved once:** its CI fix `3dd56b5` (round 1: a hand-written ordinal and a store key in a Weekly line). It was merged in as `24e3bc7`, so this branch carries B59 whole.
- **Worktree:** `../chester-b60`.
- **Read:** the rulings log (D19/D20, `C:\Users\arich\Downloads\rulings-2026-10-24.md`), B56's notes for where items 77 and 78 went, and every renderer and writer that enforced a length.

## The commits

| Commit | What |
|---|---|
| `434a55f` | Parts 1-3: the targets, the guard, the writers, the addendum, the Weekly's crypto block |
| `c34e960` | Parts 4-5: the gates, CLAUDE.md, the Master Guide and its HTML |
| `24e3bc7` | The merge of B59's CI fix |
| (next) | The Monthly writers' ceilings as runaway guards; these notes |

## Every budget changed (file and line)

| Budget | Was | Now | Where |
|---|---|---|---|
| The close's reading target | 5 minutes | **10 minutes** | `config/reporting_stack.yaml:142` (`reading_targets_minutes.daily`) |
| The close's words | 1,000 | **2,250** (10 minutes less 3 charts at 20 s, at 250 words a minute) | `config/reporting_stack.yaml:116` |
| The Weekly's reading target | 20 minutes | **35 minutes** | `config/reporting_stack.yaml:142` |
| The Weekly's words | 3,500 | **7,900** (35 minutes less 10 charts at 20 s: 7,916, rounded down) | `config/reporting_stack.yaml:117` |
| The Monthly | 55 minutes, 10,000 words | **unchanged** (now a target; its cut is retired, below) | `config/reporting_stack.yaml:118`, `:142` |
| The Monthly's `trim_to_budget` | true | **false**, at every cadence; the function `stack.trim_to_budget` is deleted | `config/reporting_stack.yaml:386`; `daily_cascade/stack.py` |
| The addendum's reading target | 5 minutes | **7 minutes** | `config/digital_addendum.yaml:42` |
| The addendum's words | 1,100 | **1,500** | `config/digital_addendum.yaml:43` |
| The addendum's line cap | 52 (`max_lines`) | **retired** (the key is gone) | `config/digital_addendum.yaml` |
| The Weekly's crypto flows block | 12 rows (`weekly_max_lines`) | **retired**, every row prints | `altdata/crypto_blocks.py:269`, `config/crypto_sources.yaml` |

**The foot line:**
- **`stack.target_line`** (`daily_cascade/stack.py:1277`) is set by `enforce_budget` (`:1255`) at every cadence: "This edition runs about N minutes against a T-minute target." It prints first in the page's footer (`daily_cascade/stack_render.py:583`) and in the Markdown (`:898`).
- **The addendum** prints "This page runs about N minutes against a 7-minute target." (`daily_cascade/digital_addendum.py:932`).
- **The Quarterly** keeps its own read warning (`quarterly.read_warning`), as before. Its target is the read's and its reference is unbudgeted, so it gets no whole-edition line.

## Every truncation or withholding path removed or changed

| Path | Was | Now |
|---|---|---|
| **The paragraph guard** (`daily_cascade/readability.py:611`, `_guard`; `:623`, `finalize`) | The close and the Weekly kept ONE paragraph, cut at a sentence to 120 words (the Weekly's to its opener band's top); the Monthly cut each to its depth allowance; "(trimmed)" printed | **Every paragraph prints in full.** A reply past the target sets `over_target` (recorded, not printed); `_cut` is deleted |
| **The Monthly's budget cut** (`stack.trim_to_budget`, T2.7) | Paragraphs went, appendix first, until the prose fit 10,000 words | **Deleted**; the foot line instead |
| **The one-sentence cut** (`daily_cascade/stack_prose.py:1191`) | A section asked for its claim alone (light, short and line depths) dropped the rest of an audited reply | **The rest prints**, `over_target` recorded |
| **The opener band's top** (`daily_cascade/opener.py:106`; the Weekly and the précis) | A commentary over the band's top was withheld ("runs 159 words; its band is 80 to 150") and sent back once | **Over the top prints in full.** Under the floor is still sent back once: a commentary too thin to carry its Takeaway is a shape fault, not a length cut |
| **The writers' character ceilings** (`stack_prose.MAX_CHARS` by depth, the read's `read_chars`, the Monthly's `MAX_CHARS x 2.5`, block `hi x 9 + 500` and summary 1,400) | Withheld a reply as `too_long` at about 2x the target | **Runaway guards** (`stack_prose.runaway`, `:1003`): each doubled (`RUNAWAY_SCALE = 2.0`, `:66`), never above `RUNAWAY_CEILING = 7000` (`:67`), so a reply that merely runs long prints and only one that lost the thread is withheld |
| **The addendum's row trim** (`TRIM_ORDER`) | The incidents, attention and ahead tables lost rows until the page fit 1,100 words | **Deleted**; the foot line |
| **The addendum's read word fault** | A read over 120 words was withheld | **Removed**; the read's ceiling is a runaway guard (`stack_prose.runaway(words x 9)`, `:881`) |
| **The addendum's cell truncations** (`_truncate`: questions 120 characters, roles 70, titles 80, claims 110) | Cut with an ellipsis | **`_whole`** (`:548`): whitespace collapsed, never shortened |
| **Items 77 and 78** | One cross-reference line each in the incidents section's footnote, to hold the 52 lines | **In the body** (`daily_cascade/batch15_b2_block.py:99`, `incidents_body`): the cyber table (KEV and NVD, week, count, percentile) with its three read lines, and the protocol table (active, listed, 30-day change, history) with its line and the hand-count gap |

## What still caps, and why (none is a reading budget)

| Cap | Where | Why it stays |
|---|---|---|
| **The model's output cap**, 2,000 tokens | `daily_cascade/narrative.py:87` (`MAX_TOKENS`) | A **provider and cost** limit: it bounds what one call can spend. The runaway ceilings are held under it (7,000 characters against about 8,000), so no reply is cut off by the provider mid-sentence |
| **The runaway guards** | `stack_prose.runaway`; `monthly_macro/prose.py` `SECTION_MAX_CHARS = 5200` (already a runaway guard); `narrative.MORNING_MAX_CHARS = 12000` (the anchor) | A **malfunction** guard: a model that lost the thread produces a refusal rather than forty pages. Doubled where they sat near the target |
| **The figure cap** (six a paragraph; the Monthly eight) | `daily_cascade/readability.py:46`, `stack_prose.figure_faults` | A **style rule** (T2.5 item 1, one fact once: the tables carry the rest), not length; a paragraph past it is still sent back once |
| **The duplicate withholding** | `readability.withhold_duplicates` | **Repetition**, not length (T2.5 item 4) |
| **The chart caps** (3, 10, 12, 40, 2) | `config/reporting_stack.yaml` `budget.*.charts` | Not reading length; D20 names none |
| **The anchor's signal lines**, at most 4 lines of 60 words | `config/st10_lines.yaml:16` | The 07:00 anchor is not named in D20; **listed for the operator** |
| **The crypto paragraph's daily part**, 6 lines | `config/crypto_sources.yaml:236` | Switched off (`enabled: false`); it serves the anchor and the close alike; **listed for the operator** |
| **The secondary notes** (below) | `config/reporting_stack.yaml:130-132`; `daily_cascade/note_common.py:241` | **Not changed** (paste item 4; not named in D20); listed for the operator to rule |

**The secondary notes' caps, unchanged and listed:**
- **The 09:50 open note:** 250 words of prose at most, reading target 2 minutes, one chart. A reply past its cap is **withheld, never trimmed** (`note_common.prose`: "the paragraph runs n words; the cap is 250"). The runaway ceiling is 8 characters a word (2,000).
- **The 21:30 evening note:** 150 words, target 1 minute, one chart. Withheld past the cap; ceiling 1,200 characters.
- **The Sunday evening note:** 400 words, target 3 minutes, one chart. Withheld past the cap; ceiling 3,200 characters.

## The gates

**Updated, every gate that pinned a budget, the 52-line cap or a cut:**

| Gate | Checks changed | Result |
|---|---|---|
| `validate_stack_cadence` | Group A's targets (10, 35, 55, 90 minutes; 2,250, 7,900, 10,000 words), group D's guard (full paragraphs, `over_target`) and runaway scale. **Group M rewritten:** no cadence trims, `trim_to_budget` gone from the code, and **an over-target fixture at the close, the Weekly and the Monthly renders every paragraph, claim and item in full and prints the foot line in the page and the Markdown**. Inside its target, no line; the Quarterly carries none and cuts nothing | 104/0 |
| `validate_stack` | Group F: the fixture is inside its 10-minute target; over a 1-minute target nothing is cut and the footer carries the line | 84/0 |
| `validate_weekly_stack` | Group H: the 35-minute, 7,900-word target; over it the Weekly prints every paragraph and item and the line | 83/0 |
| `validate_monthly_stack` | Group E: over 10,000 words and 55 minutes nothing is cut, no "(trimmed)", the page prints the line; the budget step never trims a stored summary | left to CI (memory) |
| `validate_readability` | The guard cuts nothing past the 120-word, one-paragraph target | 67/0 |
| `validate_digital_addendum` | The 1,500 / 7 / 2 targets with no `max_lines`. **Over a 100-word, 1-minute target the page keeps every row and line of the full week and prints its foot line.** Items 77 and 78 are in the incidents body with their tables, not the footnote. A read past 120 words prints in full; a runaway reply is still withheld | 98/0 |
| `validate_batch15_2` | The addendum's incidents body carries items 77 and 78 | 57/0 |
| `validate_crypto_sources` | The Weekly block prints all its measures, with no cap key | 117/0 |

Also run locally: `validate_quarterly_gates` 95/0, `validate_a47_chain3` 42/0, `validate_a55_box_fixes` 31/0, `validate_audit_fixes` 103/0 (the gates that test a too-long reply), `check_master_guide` 0/0 (the guide's close and Weekly rows rewritten and its HTML rebuilt), `check_library` 0/0, and `validate_audit_3a` 88/0.

**No gate is added**, so CLAUDE.md's count line is unchanged (138 code gates, B59's count).

**CI:** recorded below once read.

## Differences from the paste

- **The Monthly's `trim_to_budget` is removed, not only its number kept.** D20's "nothing cut or withheld for length" covers the Monthly; its 55 minutes and 10,000 words stand, as targets.
- **The writers' character ceilings are kept as runaway guards (doubled), not removed.** Removing them entirely would leave only the provider's output cap, which cuts a reply mid-sentence.
- **The opener band's floor is kept.** A commentary under the floor is still sent back once; that is a shape fault, not length.
- **The anchor's caps** (signal lines, crypto daily part, the morning ceiling) are not changed: the 07:00 anchor is not named in D20. They are listed.
- **Nothing in the Weekly's renderer is changed for the freeze** (29 Oct-1 Nov), because nothing here merges before 1 Nov.

## Files shared with other branches

- `config/reporting_stack.yaml`, `config/digital_addendum.yaml`, `config/crypto_sources.yaml`.
- `daily_cascade/stack.py`, `readability.py`, `stack_render.py`, `stack_prose.py`, `opener.py`, `digital_addendum.py`, `batch15_b2_block.py`.
- `altdata/crypto_blocks.py`, `monthly_macro/stack.py`, `monthly_macro/prose.py`.
- CLAUDE.md, the Master Guide and its HTML.
- The gates above.

These touch the same files as any branch that edits the stack's prose path (the 6f build of the week of 2 Nov, a62).

## Needs you (at most five)

1. **The secondary notes' caps:** keep the open note's 250, the evening note's 150 and Sunday's 400 words as caps (a reply past them is withheld), or make them targets like D20's?
2. **The 07:00 anchor's caps:** the signal lines (4 lines, 60 words each) and the crypto daily part (6 lines, switched off). Keep, or bring them under D20?
3. **The word equivalents:** accept 2,250 words for the close and 7,900 for the Weekly (each target at 250 words a minute less its charts' time)?
4. **The runaway guards:** accept the writers' ceilings doubled and held under 7,000 characters, as malfunction guards rather than reading budgets?
5. **The opener band's floor:** keep sending back a Weekly commentary that is under its band's floor (too thin), now that the top is a target?
