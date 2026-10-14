# T3.5: the Monthly's frames take the Weekly's budget discipline — session notes

- **Branch:** `t3-5-monthly-frames`, from `origin/w-1-1-integrity` at 9f875e2.
  It carries W-1.1's item 1.0 machinery and should merge after W-1.1 without
  conflict.
- **Session:** A, 11 Oct 2026.

**The evidence I had.** The operator's log from Monthly dry run #4 (main
785fa19, 11 Oct 13:17 ET, on the box) has not reached this session. I worked
from the brief's classes (a) to (e), and reproduced each one on fixtures
against 9f875e2 before fixing it.

**Not run.** The full local suite (CI is the validate) and anything on the box.
I ran the gates this branch touches one at a time, and all are green:

| Gate | Result |
|---|---|
| `validate_monthly_frames` (new) | 32/0 |
| `validate_monthly_stack` | 261/0 |
| `validate_figure_budget` | 110/0 |
| `validate_no_filler` | 14/0 |
| `validate_weekly_integrity` | 36/0 |
| `validate_weekly_stack` | 68/0 |
| `validate_weekly_edits` | 89/0 |
| `validate_weekly_complete` | 57/0 |
| `validate_weekly` | 100/0 |
| `validate_monthly` | 350/0 |
| `validate_stack` | 66/0 |
| `validate_stack_cadence` | 99/0 |
| `validate_daily_close` | 102/0 |
| `validate_readability` | 63/0 |
| `validate_voices` | 70/0 |
| `validate_edition_consistency` | 14/0 |
| `validate_config_refs` | 25/0 |
| `validate_gates` | 31/0 |
| `check_library` | 0 failures |

## What was built

**(a) A count carries its noun, and the display and the gate agree**
(`altdata/numeral_audit.py`).

- **The display.** `change_display(value, units, key)` now prints the integer
  form with its noun: "+29,000 jobs", "+125,623 contracts", "−7,000 claims".
  - The noun comes from `DISPLAY_NOUNS`, matched by key or key prefix. Payrolls,
    claims, JOLTS, housing, `cftc.*`, `pm.volume`, `pm.open_interest`,
    `exposure.oi_*` and `eia.*` are covered.
  - A derived `calc.naive_expectation.*` or `calc.surprise_vs_naive.*` series
    takes its source's noun. A unit of "shares" or "contracts" gives its own.
- **The gate.** The bare-delta rule passes a figure followed by one of those
  nouns. So the form the writer is told to copy is the form the gate accepts,
  wherever the figure travels: under `change_display`, as a table cell, or in a
  parent's or summary's `figures_you_may_cite`.
  - That last case is the dry run's. The display reached the frame under a key
    `accepted_deltas` does not read, and the integer was withheld.
- **Unchanged.** A series with no noun keeps the plain integer, accepted as its
  own display as T3.4a ruled.
- **Callers.** All three now pass the key: `weekly_stack.change_over`,
  `weekly_stack.form_text` and `v2.metric_month`. So the Weekly prints
  "+150,000 jobs" too.
- **The prompt.** `prose.DISPLAY_RULE` now shows the noun form.
- **Fixed in passing: the rule missed a bare figure** at a sentence's end
  ("+29,000.") or before a comma ("+29,000, the most since May"). The
  lookahead `(?![\d.,])` refused the match outright. It now reads "not followed
  by more of a number".

**(b) The Monthly's block frame is a Weekly parent's**
(`daily_cascade/figure_budget.block_frame`, `monthly_macro/prose.py`).

- **The frame.** A block past the cap now gets:
  - `figures_you_may_cite`: the rows that fit the cap, ranked by z where the
    section carries one, else by absolute change;
  - the table, with every other row's figures masked as "[in the table]", and
    its column heads;
  - those rows' names under "In the tables (do not enumerate)";
  - a note that the masked rows are for the reader.
- **The prompt** carries `BLOCK_FRAME_NOTE`: copy the figures verbatim, and
  never convert one (a percent into basis points, a level into a change, two
  figures into a difference). It also carries the filler rule.
- **The filler ban** (`stack_prose.filler_faults`) now runs on every Monthly
  stack call: sections, blocks and summaries.
- **The retry** after the numeral audit names the refused figures and lists the
  allowed ones, in one fixed sentence (`FIGURE_RETRY`).
- **Counting.** `quantified_figures` no longer counts a table's name column as
  figures. Before, "CPI above 3% in October" counted as one.

**(c) The ordinal the table prints.**

- `numeral_audit.stored_ordinals` now also holds an ordinal a table cell prints
  ("89th (5 years, n=1,258)", "75th percentile"). That is the form
  `ORDINAL_RULE` tells the writer to copy, built by the same half-up rule. An
  ordinal in running text ("the 2nd session") is not read.
- The theme rows' data carries `percentile_ordinal` beside the scrubbed raw
  percentile.
- The column heads travel in the frame, so "20-day change" no longer leaves an
  unmatched 20 (the energy block's second figure).

**(d) The three withheld summaries.**

- **What I found on the fixture payload:** the theme tables printed the store
  key as the row name ("yfinance.mkt_gld"). That withheld the metals block and
  the Slow layers summary for an internal id.
- **The fix:** the rows now carry labels from `config/display_labels.yaml` ("the
  gold fund (GLD)" and four more). An unlabelled series prints its key in words,
  never with its dot.
- **Not reproduced:** The read, Narratives and Ahead pass on the fixture, both
  when citing exactly their `figures_you_may_cite` and with realistic drafts.
  Their reasons are in the operator's log, which I do not have. See Needs you.

**(e) A voice's view is attributed** (`stack_prose.style_faults(...,
attributed=True)`, `voices_block.view_faults`).

- A view prints under its voice, outlet and URL. So its motive words are the
  voice's claim, whether quoted or paraphrased, and the motive check is skipped
  for a view. Every other style and policy-word rule still holds.
- `unquoted` also strikes single curly quotes, guillemets, and straight single
  quotes that open and close at word boundaries. An apostrophe ("Lane's") does
  not count as a quote.
- The same words in our own prose remain a motive fault.

**The gate.** `tools/validate_monthly_frames.py` (32 checks) covers all five
classes on fixtures shaped like the dry run's blocks: Yields & spreads, Macro,
FOMC pricing, Prediction markets: the rest, and the three theme blocks.
`validate_monthly_stack`, `validate_figure_budget`, `validate_weekly_stack` and
`validate_weekly_edits` were updated to the new forms. The Makefile carries the
gate, and CLAUDE.md now reads fifty-one code gates.

## Withheld blocks on the fixture payload, before and after

The fixture is `tools/validate_monthly_stack.build_payload()`, with a writer
that copies its frame faithfully: each block writes its first citable row as
printed, and each summary its `figures_you_may_cite`.

| | 9f875e2 (before) | this branch (after) |
|---|---|---|
| Blocks withheld | 1 of 9 (`block:slow:metals`, internal id) | 0 of 9 |
| Summaries withheld | 1 of 12 (`summary:slow`, internal id) | 0 of 12 |

The fixture payload is sparse: it has no FOMC, prediction-market, payroll or
CFTC block. The other classes were reproduced one at a time on 9f875e2 and pass
here:

| Class | On 9f875e2 | Here |
|---|---|---|
| (a) | "+29,000" cited with no display beside it is withheld | "+29,000 jobs" passes |
| (c) | "89th" copied from the table is withheld | passes |
| (d) | the theme row prints "yfinance.mkt_gld" | "The gold fund (GLD)" |
| (e) | Lane's view prints "view withheld: motive: 'driven by'" | the view prints |

## Choices made for the operator to overrule

- **The noun list is mine.**
  - Payrolls are "jobs", claims "claims", JOLTS "openings", "hires" and
    "layoffs", housing "starts", "permits" and "homes", CFTC and
    prediction-market counts "contracts", EIA stocks "barrels".
  - The noun also prints in the tables' change cells: "+42,984 contracts".
  - A nounless count keeps the bare integer.
- **A voice's view is exempt from the motive check entirely**, not only inside
  its quotation marks. Its source is printed beside it. If you want the
  exemption limited to quoted text, as on our own prose, it is the
  `attributed=True` in `voices_block.view_faults`.
- **Blocks inside the cap keep their full slice.** That means the table, lines,
  points and data, as before. Only a block past the cap gets the masked frame.
  The dry run's four refused blocks are all past the cap on real data: eight
  yield rows, six or more FOMC meetings, the watched markets.
- **The block ranking uses z where the section carries one**, the Weekly
  parents' rule. Monthly sections carry none today, so blocks still rank by
  absolute change.
- **The retry lists every allowed row with all its cells**, the as-of date
  included. That is longer than the Weekly's, but nothing is left to guess.
- **The theme labels are new display labels:** GLD, SLV, USO, BTC-USD and ZEC's
  shielded share. `zec.price` and `crypto.cap_share` are not in the registry,
  so they print their key in words.

## Needs you

1. **Send the dry run #4 log for The read, Narratives and Ahead?** Their three
   summaries did not reproduce on the fixture, so their class is unfixed beyond
   the filler ban and the retry. Yes / no.
2. **Keep the voice's view fully exempt from the motive check?** The
   alternative is quoted text only. Yes / no.
3. **Keep the noun in the tables' change cells** ("+42,984 contracts")? The
   alternative is the bare integer in tables, with the noun in the frame only.
   Yes / no.
4. **Give blocks inside the cap the masked frame too?** That would drop their
   raw data and keep only the table and display fields. It is not done here.
   Yes / no.
