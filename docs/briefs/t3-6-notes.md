# T3.6: the Monthly polish from dry run #5 (14 Oct 2026)

Branch `t3-6-monthly-polish`, from main at `cc91752`. Branch-only: nothing merged, nothing deployed, nothing on the box.

**When it merges.** It merges in the week of 19 Oct, before the 23 Oct Monthly dry run, after a later paste merges the new main into it.

**What prompted it.** Dry run #5 ran on 13 Oct at 08:51 ET, on main at `7754d0d`, before W-1.1b. It showed ten faults, M1 to M10.

**All ten are built**, each with its fixture before its code. The fixtures are in `tests/fixtures/monthly_run5_2026-10-13.json`, and the gate is `tools/validate_audit_fixes.py` group **I**. It is not H, because `w-1-3c-weekly-polish` already adds a group H to that file; see "Shared files".

## Main fixes none of the ten

**How I checked.** I read main at `cc91752`, which includes W-1.1b: the direction audit, the stance check and the sign rewrite inside each Monthly section. I checked each fault against that code by reading it; I did not re-run the dry run.

| | What main does | Fixed on main? |
|---|---|---|
| M1 | The numeral audit matches a figure to any payload value. The label audit checks a figure printed beside a *named* level ("the 40-week average of X"), not a figure a close-word binds to an average. | No |
| M2 | The direction audit holds each paragraph to its own section's signs. Nothing compares paragraphs with each other. | No |
| M3 | `readability.withhold_duplicates` withholds a later section's sentence that repeats The read *verbatim or by containment*. It does not compare the executive summary with section 1, does not compare section 1 with itself, catches no paraphrase, and the one page asked for "exactly 5" takeaways. | No |
| M4 | 2s10s is `change_over` on the stored `calc.yield_curve_2s10s`, whose prior can sit on a date its legs do not share. W-1.1a item 6 aligned SOFR–IORB, CCC–BB and gold/copper, but not 2s10s. | No |
| M5 | A gap's `direction` is read from its last two sessions. The misfit section prints points, not a table, so the direction audit read no moves for it. | No |
| M6 | `changed_since` printed one line per row. | No |
| M7 | The numeral audit already reads numerals only, so a count in words was always exempt. No frame asked for words, so the model wrote "2". | No (the frame) |
| M8 | `too_long` is in `NOT_RETRIED`, and the narratives' summary frame carried no source rule. | No |
| M9 | `DISPLAY_RULE` asks for the display string of a field that carries one. No check catches a raw "83553.85". | No |
| M10 | `config/reporting_stack.yaml` makes "the dollar" an alias of the DXY. Nothing handles a second dollar series. | No |

## What each fix does

**M1 (serious): the role audit.** `altdata/numeral_audit.py` `role_faults()`. Every figure the payload offers carries its role: close, average, percentile, change or level.
- **Where the role comes from:** the field's name (`close`, `end_level`, `ma_40w` …), or for a table cell, its column's head ("Month-end close", "40-week (≈200-day) average").
- **The rule:** a close-word ("closed", "closes", "the close", "month-end close", "ended", "finished", "settled") binds the figures after it in its sentence. A figure the payload holds only as an average is a fault, unless another role's word ("average", "percentile", "high", "from" …) stands between them.
- **Where it runs:** on every Monthly frame (section, block, summary, and the v2 sections). A failure is withheld and retried, and the retry hears which average it was ("4,554.56 is Gold's 40-week average, an average, not a close").
- **The frame side:** the long frame's data names each column's role (`long_frame_columns`), the tape's frame says so, and every frame carries `ROLE_RULE`.
- **On the fixture:** run 5's two quoted sentences fail on three figures each, and the corrected sentence passes.

**M2: one direction per instrument across the executive summary.** `prose.reconcile_summary()`, run in `stack.produce` after the summary pass.
- **The reading:** each published summary paragraph's direction for each instrument it names is read as up, down or flat. Up and down come from the direction lexicon; flat from "held", "holding", "steady", "unchanged" and similar words; phrases like "pulling back" and "gave back" count too.
- **When two paragraphs disagree,** the one against the month's sign is rewritten once, with the reason. Where the edition prints no sign for the instrument, the later paragraph is rewritten.
- **A paragraph still in conflict is withheld** (`inconsistent`).
- **On the fixture:** gold "pulling back" against "holding its level", and the dollar "firmed" against "held".

**M3: de-duplication.**
- **The similarity test** is new: `readability.similar_sentence()`. It is the old `same_sentence`, or a content-word overlap of ≥ 0.5 after light stemming, between sentences of at least five content words. The old test caught only verbatim and contained repeats.
- **Where it runs:** `stack.dedup_one_page()` runs after the summary. A one-page sentence similar to a summary sentence, or to an earlier one-page sentence, is withheld. A sentence withheld as a summary repeat still counts as said.
- **The cap:** the page is then cut to **four** paragraphs, and its notes say what went.
- **The frame** now asks for four takeaways, each said once.

**M4: the derived change equals its legs'.** `stack.derived_rows()` in the Monthly's plumbing.
- **How it is built:** 2s10s now takes both legs on the latest date both have, now and at the month's start (W-1.1a's `aligned_legs`, ported).
- **The check:** its change must equal the 10-year's change less the 2-year's, within 2 bp (`derived_check`).
- **If it does not,** the row prints "withheld: its change (…) is not its legs' (10-year +54 bp, 2-year +54 bp)", and the series leaves the data the prose reads.
- **On the fixture:** run 5's "+83 bp" against legs of +54 bp each fails; built from aligned legs, it reads 0 bp.

**M5: gaps.** `stack.month_direction()` reads each gap's direction over the **month**: its |z| at the latest point against its |z| at the month's start.
- **Where it is stored:** in the gap's data (with `z_month_start`) and in the gap table's Direction column.
- **The audit:** `prose.gap_faults()` holds a misfit or read frame's direction words about a gap to it. A clause naming a gap is read against that gap; one about "the gaps" in general is read against all of them, when they agree.

**M6: Changed since last Monthly.**
- **What prints:** forecasts and decisions are summarised, for example "11 forecasts emitted, 9 resolved: 6 right, 3 wrong." and "5 decisions closed." Every dial, dimension, exception, story and claim line is kept.
- **What "right" means:** a forecast is right when its probability was on the outcome's side, p ≥ 0.5 with the event and p < 0.5 without it. A resolved forecast missing either value counts as "not yet graded".
- **The data it needs:** `monthly_macro/v2.py`'s resolved rows now carry `probability` and `outcome`.

**M7: small counts in words.** `COUNT_RULE` is in every frame. The numeral audit already exempts a count written in words, by construction, and the gate shows "2 of the next four meetings" failing and "two" passing.

**M8: two fixes.**
- **Too long is now retried.** A `too_long` reply is retried **once**, told the cap it overran and a tighter one to write to (70%: 980 of 1,400 characters). If it is too long again, it is withheld.
- **The narratives' summary frame** requires the source and the noun beside every change (`SOURCE_RULE`).

**M9: the display form.** `numeral_audit.separator_faults()` withholds a figure of four or more integer digits printed without its thousands separators. The retry hears the form to copy ("write '83,553.85', as the tables print it"). A year (1900–2100, no decimals) and a name with digits are exempt.

**M10: the two dollar series.** `prose.dollar_label_faults()`: where the edition prints both the DXY and the Fed's broad index, "the dollar" beside a level of either is withheld. The rule is in every frame (`DOLLAR_RULE`). With one dollar series, "the dollar" stays its alias, as W-1.1a ruled.

## Fixtures

`tests/fixtures/monthly_run5_2026-10-13.json`.
- **Quoted from run 5, as the paste gives it:** M1's two sentences, M4's "+83 bp to 47 bp", and M9's "83553.85" and "7651.54".
- **Built to reproduce the fault where no text was given:** synthetic figures with the same shape (the long-frame averages, the gaps' z, the forecast counts, the dollar series' levels).

There is no live store, no model and no network. M4's store test seeds a temporary store, and every model call is replaced by scripted drafts.

## Gates

Run locally, one at a time:

| Gate | Result |
|---|---|
| validate_audit_fixes | 89/0 (30 new, in group I) |
| validate_monthly_stack | 261/0 |
| validate_monthly | 350/0, 1 skipped |
| validate_monthly_frames | 32/0 |
| validate_numeral_audit | 159/0 |
| validate_readability | 63/0 |
| validate_stack | 66/0 |
| validate_stack_cadence | 99/0 |

**Where the new checks live.** I put the new checks in `validate_audit_fixes` only, the gate that already carries W-1.1a's and W-1.1b's fixtures. The others named in the paste pass unchanged, and no new gate was needed.

CI: see the reply, which gives the run number.

## Files this branch shares with other branches

This branch changes seven files:
- `altdata/numeral_audit.py`
- `daily_cascade/readability.py`
- `monthly_macro/prose.py`
- `monthly_macro/stack.py`
- `monthly_macro/v2.py`
- `tests/fixtures/monthly_run5_2026-10-13.json` (new)
- `tools/validate_audit_fixes.py`

**How I got the list.** For each branch not yet merged into main, I took `git diff --name-only` from its merge base with main and intersected it with the seven files above. Nothing in the repo names "Friday's 23 stitched branches". The unmerged branches other than the two alpha-lab ones number **24**, so the list below covers all 24. One of them is presumably not in Friday's set.

| Branch | Shared files |
|---|---|
| **w-1-3c-weekly-polish** (merges last on Friday) | **all six code files** — numeral_audit, readability, prose, stack, v2, validate_audit_fixes. It adds its own group H to `validate_audit_fixes`, which is why this branch's group is I. |
| aq-1-quarterly-cadence, aq-3-series-1, aq-10-validators, aq-2-chapters-1, aq-2-chapters-2, aq-3-series-2, aq-7-quarterly-scan, b3-tranche-a, c1-move-screen, crypto-basket, el-1-packets, el-2-3-rollup, lib-aq14-em-paper, sr-36-basis-proxy, sr-37-38-ai-fcf, sr-38-inbox, sr-43-49-rates-anchor | `monthly_macro/prose.py`, `stack.py`, `v2.py` |
| aq-4-horizon-charts, aq-6-thesis-register, aq-9a-em-scorecard, imf-ifs-gold | `monthly_macro/stack.py`, `v2.py` |
| aq-5-correlation-layer, aq-8a-gold-residual | `monthly_macro/stack.py` |
| **alpha-lab-1, alpha-lab-2** | none of these files |

**Several of these branches are stacked on each other,** so a shared file may be an upstream change rather than the branch's own.

**Where to expect conflicts.** In practice they will be where the new main has changed `monthly_macro/stack.py` (`w-1-3c` alone changes 406 lines there), `prose.py`, `numeral_audit.py`, `readability.py` and the end of `validate_audit_fixes.py`. They will surface when the new main is merged into this branch.

## Not named in the paste, so chosen here

1. **Where the M1 role audit runs.** It runs on every Monthly frame, the v2 sections included, not only the executive summary and section 2.
2. **What the role audit binds.** A close-word binds every later figure in its sentence until another role's word intervenes. Changes (%, bp, points) are never read as closes.
3. **The M2 direction lexicon.** Its flat words and phrases are mine (`FLAT_WORDS`, `_DOWN_PHRASE`, `_UP_PHRASE`).
4. **The M3 similarity bar** is 0.5 content-word overlap and at least five content words. The one page went from "exactly 5" takeaways to "at most 4".
5. **M4's tolerance is 2 bp.** Only 2s10s is in `DERIVED`; others can be added there.
6. **M6's "right" and "wrong"** is the probability-side rule above.
7. **M8's tighter cap is 70%.** It is one extra attempt beyond the three the audits get.
8. **M9's exemptions:** years and digit-bearing names.
9. **M10 fires only where two dollar series print.**
10. **The gate group is I, not H** (`w-1-3c-weekly-polish`).

## Needs you

1. **Merge order.** The new main goes into this branch first, then this branch merges before the 23 Oct dry run, inside a window. Expect conflicts with `w-1-3c-weekly-polish`'s changes to the six shared code files. yes / no
2. **The one page: four takeaways rather than five.** The paste capped it at four paragraphs, so the frame now asks for four. Does that supersede an earlier ruling of five? keep four / rule
3. **The M6 rule for right and wrong** (p ≥ 0.5 on the outcome's side). keep / rule
4. **The thresholds:** M3's 0.5 similarity, M4's 2 bp, M8's 70% cap. keep / change
5. **The acceptance is the 23 Oct Monthly dry run** (yours, on the box): whether any of M1 to M10 recurs on live text.

## 14 Oct evening: Friday's tip and five takeaways (session A)

Session B built T3.6, and session A took it over this evening.

### The tip merged

`origin/w-1-3c-weekly-polish` at **`fb67bf3`** (it had not moved), merged as
`76941f9` and pushed on its own. One conflict, as the trial merge predicted:

- **`tools/validate_audit_fixes.py`**, in three places: the docstring, the end
  of the groups, and `main()`'s loop.
  - The tip's group H prints two parts, **H** (W-1.3c item 1) and **I** (item
    6). T3.6's group was also lettered **I**, chosen to avoid the tip's H.
  - **Both sides are kept** by relettering T3.6's group **J**: its docstring
    entry, its heading, and `group_i` renamed to `group_j`. It now runs after
    the tip's groups.
  - No check changed. The gate passes 103/0: the tip's 73 plus T3.6's 30.
- **CLAUDE.md** did not conflict, but the gate total was recounted from the
  merged Makefile: **74 code gates** (71 Python, counting `smoke_test.py` as the
  Makefile's `EXTRA` does, and 3 shell) and **six data gates**. The tip's prose
  said five data gates; its Makefile lists six (`validate_imf_china.py`).

Where the notes above say "group I", read **J** from this merge on.

All of T3.6's other files auto-merged: `numeral_audit.py`, `readability.py`,
`prose.py`, `stack.py` and `v2.py`. On the merge, the gates T3.6 ran all passed:

| Gate | Result |
|---|---|
| validate_audit_fixes | 103/0 |
| validate_monthly_stack | 262/0 |
| validate_monthly | 350/0, 1 skipped |
| validate_monthly_frames | 32/0 |
| validate_numeral_audit | 167/0 |
| validate_readability | 67/0 |
| validate_stack | 66/0 |
| validate_stack_cadence | 99/0 |
| validate_gates | passed |

### The change: five takeaways (ruled 09:27 ET, decision 8)

This answers needs-you 2 above: five, not four. Three places now say five:

- **The cap:** `monthly_macro/stack.py` `ONE_PAGE_MAX = 5`.
- **The frame:** `monthly_macro/prose.py`'s one-page frame asks for "Five
  takeaways …", with `"paragraphs": "exactly 5"`, as before T3.6. It keeps
  T3.6's "Say each thing once: no takeaway restates another."
- **The gate:** `validate_audit_fixes` group J.
  - The six-paragraph fixture page is cut to five, and its note reads "Cut to 5
    paragraphs".
  - The frame asks for five takeaways, each said once.

The M3 de-duplication is unchanged: `readability.similar_sentence`, and
`dedup_one_page` against the summary and against itself. A page that loses a
repeat still prints fewer than five, with its notes saying what went.

### Gates (local, one at a time)

| Gate | Result |
|---|---|
| validate_audit_fixes | 103/0 |
| validate_monthly_frames | 32/0 |
| validate_monthly_stack | 262/0 |
| validate_monthly | 350/0, 1 skipped |

### CI

- **#403** (`76941f9`, the merge): green.
- **#404** (`e6d42e0`, five takeaways): green.
