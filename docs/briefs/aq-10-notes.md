# AQ-10 — the Quarterly's validators: build notes (12 Oct 2026)

Branch `aq-10-validators`, from `origin/aq-2-chapters-2` at `833bf99`, not merged.
Built against the Alternative Assets Quarterly change order
(`docs/change-order-alternative-assets-quarterly-2026-10-10.md`): the AQ-10 row of
§11, with §3, §4.1 items 6, 8 and 10, §4.10, §4.11, §5, §6 and §9. The change
order itself is not edited.

## What was built

**The gate.** `tools/validate_quarterly_gates.py`, in the Makefile's list after
`validate_quarterly_stack.py`. It is fixtures only and never reads the live store.

Each rule is written once, as a function over an edition (or over a ledger's
rows) that returns the faults it finds. Every rule is shown both ways on a
synthetic fixture: one that passes, and one that fails for that rule. The gate
then runs all five over the Quarterly's own dry run, on the synthetic store that
`validate_quarterly_stack.py` seeds.

| Gate | Rules | Checks on this branch |
|---|---|---|
| 1. The quarterly stack | render · cap · read · reference | 19 |
| 2. The thesis register | family · horizon · measurable · grade date · Brier slot · trigger · not yet · seed | 21 (+2 on AQ-6's merge) |
| 3. The correlation block | keys · break · shift | 13 (+3 on AQ-5's merge) |
| 4. The kill conditions | config · render · state | 16 (+1 on AQ-8a's merge) |
| 5. Draft per horizon | one draft · cost · role · no draft · Thailand · agriculture | 18 (+1 on AQ-6's merge) |

On this branch the result is **87 passed, 0 failed, 7 skipped**. The skipped
seven are the checks marked "activates when <branch> merges".

Those seven were also run in a scratch worktree with `aq-5-correlation-layer`,
`aq-6-thesis-register` and `aq-8a-gold-residual` merged onto this branch. There
all 95 checks pass and none is skipped. The scratch merge was thrown away; it
had three trivial conflicts, listed under *What waits*.

- **1. The quarterly stack.**
  - Every front-matter section and every chapter item has content or a not-yet
    reason.
  - At most 40 charts are drawn.
  - Every chart a section names exists in the edition, so none is dropped
    silently.
  - A chart held over the cap is listed in `charts_over_cap`, and its name is in
    the line the page prints in its place.
  - The read's time is recomputed by the rule (250 words a minute, 20 seconds a
    drawn lead chart) and must match the edition. It must be printed in both
    headers.
  - Over 90 minutes the read must carry its warning, and no lead item may be cut.
  - The reference has no budget in config and nothing in it is trimmed. Inflating
    a reference item must leave the read's time unchanged.
  - **The dry run:** 21 sections, 18 charts, the read 7 minutes of 8.
- **2. The thesis register.** It reads AQ-6's documented row shape: `theses()`,
  which is the ledger's row joined to `alt_asset_theses`.
  - Every entry has a family from AQ-6's eleven and a horizon of 3m or 12m.
  - Every entry has a measurable `{series, comparator, level, date}`, a grade
    date (`horizon_date`) and a Brier slot (null, or in [0, 1]).
  - Neither the entry nor its measurable's series is trigger-eligible. No
    registry key is trigger-eligible at all, which the gate also asserts.
  - Before Doctrine #2, items 1 and 2 print "not yet" cleanly: no rows, no fault,
    no `None`. So does AQ-6's `seed_table` on an empty ledger.
- **3. The correlation block.**
  - Every row of item 8 names its keys, and each key is registered.
  - Where a chapter carries break assets, item 8 prints one 30-day against
    120-day break line. Every break on it has |Δ| ≥ 0.30 and the direction its
    sign gives, and appears on the page.
  - Item 6's break-logic rows print one of three forms: "no break fired", "not
    yet: <branch>", or the breaks.
  - Every shift record carries a numeric 60-day and 252-day value, and every
    printed shift line shows both.
  - **On AQ-5's merge:** `shift_eval` flags no day the 252-day window lacks, and
    `is_break` and `direction` are the gate's threshold and sign.
- **4. The kill conditions.**
  - All 29 analyses in `config/quarterly_chapters.yaml` carry `kill`: the §5
    text, or "none ruled" where the ruling gave none.
  - Item 6 prints every listed analysis with a reading and a kill state in the
    four words: holds / strained / killed / not measured — <reason>.
  - **The dry run:** all 29 print "not measured", each with its reason.
  - **On AQ-8a's merge:** its own kill readers map into the four words.
- **5. Draft per horizon.**
  - At most one draft per family per horizon.
  - Every draft carries its cost row and a portfolio role in XVII's words.
  - A no-draft line carries its reason.
  - A deep chapter prints a line for each horizon.
  - Thailand prints no draft, even when the books table holds one.
  - Agriculture prints its rule line, and a draft on an instrument not named as
    understood prints as a no draft.

**What the gates needed changed in the builders.** Four of the five rules were
not yet true of the AQ-2 build, so the builders changed with them.

- **Over-cap charts are named** (`quarterly.hold_cap`). The AQ-1 form replaced
  the chart with "over the edition's chart cap (40)", with no caption: the page
  said a chart was missing but not which one. The line now ends with the chart's
  caption.
- **Item 6 has a kill-state column** (`quarterly_items.kill_state`,
  `ANALYSIS_COLUMNS`). The state is computed, never declared, by the first rule
  that applies:
  - `kill_measurable`, a measurable in the falsification tests' grammar (met is
    killed);
  - `kill_reader`, a function of the analysis's own module, with `kill_args`.
    Metals' two-bid now reads AQ-8a's `paper_bid.oi_kill_state` for GLD, and
    degrades to "not yet: aq-8a-gold-residual";
  - otherwise "not measured", with the reason: none ruled, the analysis waits,
    or no measurable yet.

  AQ-8a's own wordings map in through `kill_vocab`:
  - "no stable sign (kill condition met; …)" becomes killed;
  - "stable" becomes holds;
  - "kill test waits: n of 12" becomes not measured.
- **Item 8 carries its keys, the break state and the shifts**
  (`quarterly.correlation_rows`).
  - Each row's registry key goes in `data.rows`. A matrix cell is read under
    AQ-5's alias.
  - There is one 30-day against 120-day line for the chapter's break assets, with
    "none fired for …" in a quiet quarter.
  - The quarter's shifts on the chapter's pairs: the records in `data.shifts`,
    at most five printed, each with both windows. A missing window prints as a
    dash, so the gate sees it; it no longer faults the item.
- **Item 10 carries the cost row and holds the rules**
  (`quarterly_items.book_rows`, `cost_text`).
  - The table's columns are Horizon, Line, Portfolio role, Cost row, and
    Decision or reason.
  - **The cost row** comes from the `cost_json` AQ-6 stores: the commission from
    the rate card, or its reason, with spread, roll, borrow and FX hedge named as
    not priced.
  - **A draft's decision cell** names its instrument.
  - **A missing horizon** in a deep chapter prints a no-draft line, so the gap
    shows.
  - **Agriculture:** a draft on an instrument not in
    `book_rule.understood_instruments` prints as a no draft, "thin or poorly
    understood contract … (section 4.11)".
  - Rows sort 3m, then 12m.

`tools/validate_quarterly_stack.py` group G's item 6 check now expects four
columns. Gates re-run here: `validate_quarterly_gates` 87/0/7,
`validate_quarterly_stack` 94/0, `validate_config_refs` 29/0,
`validate_stack_cadence` 99/0.

## What waits, and for what

- **AQ-6 (`aq-6-thesis-register`):** two checks in gate 2, one in gate 5.
  - Its real `seed_table` on an empty ledger.
  - Its `FAMILIES` and `HORIZON_KINDS` against the gate's.
  - Its `PORTFOLIO_ROLES` and `draft_rule_faults`.
  - Until then, item 10's book is not read at all: it prints the AQ-2 not-yet
    line.
- **AQ-5 (`aq-5-correlation-layer`):** three checks in gate 3.
  - `shift_eval` with the 252-day window absent or partial.
  - `is_break` and `direction`.
  - Every named row it offers the Quarterly is registered.
  - Item 8 prints "not yet — the correlation layer (AQ-5)" until then.
- **AQ-8a (`aq-8a-gold-residual`):** one check in gate 4. Its
  `gold_kill_state`, `yudd_kill_state`, `oi_kill_state` and `rr_kill_state`
  outputs must map into the four words.
- **c1-move-screen:** no AQ-10 gate needs its code. Its hook (EM's episode list)
  is already held by `validate_quarterly_stack.py` group G, part 2.
- **The scratch merge's conflicts**, for whoever merges these branches.
  - `monthly_macro/stack.py`: AQ-5's `correlations` and AQ-6's `theses_seed`
    both extend the Monthly slow layer's `data` dict, so keep both keys. AQ-6's
    `seed_sub` line and AQ-8a's metals block meet at one spot, so keep both.
  - `Makefile` and `CLAUDE.md`: list unions.
- **The two-bid's twelve-month kill test.** AQ-8a's `oi_kill_state` says "the
  forward 20-day test is AQ-10's kill-condition gate, not yet built". This
  branch does **not** build that statistical test. The gate holds that its state
  prints, and prints in the four words. The test itself is an analysis
  computation, due about October 2027, when twelve months of call-put OI exist.
  It needs a ruling on what "a relationship" means (Needs you 2).
- **Twenty-nine analyses, all "not measured".** Each ruled kill condition that
  has text but no measurable reads "the analysis waits" while its analysis waits.
  Once an analysis is built, its kill condition needs `kill_measurable` or
  `kill_reader` to compute a state. Otherwise it prints "the kill condition has
  no measurable in config yet", which passes the gate but says nothing.

## Choices made for the operator to overrule

1. **"none ruled" counts as a kill condition in config.** §5 gives several
   analyses "—". The config says `kill: "none ruled (section 5)"`, and the state
   reads "not measured — no kill condition was ruled (section 5: —)", AQ-8a's
   wording. A blank or missing `kill` is what fails.
2. **Killed is printed, and nothing acts on it.** This follows AQ-8a's "kill
   condition met; not acted on". A killed state is a line for the quarterly
   review, never an automatic removal.
3. **Agriculture's understood list ships empty.** Until the operator names
   instruments, every agriculture draft prints as a no draft. That is the
   conservative reading of "thin or poorly understood contracts are a no draft
   by rule".
4. **A missing horizon prints "no draft — no book line was written for this
   horizon".** It does not leave the row out. AQ-6's loader already refuses such
   a file for a deep family, so this only shows on a hand-edited ledger.
5. **Item 8's shifts are capped at five lines per chapter, then "and N more".**
   The Weekly's caps are the model. The records are all in `data.shifts`.
6. **The read's budget is warned on, never enforced.** This is AQ-1's ruling
   (the read is warned over 90 minutes and nothing is cut). The gate fails only
   a missing warning or a cut lead item.

## Needs you

1. Name the agriculture contracts and funds that are liquid and understood (`understood_instruments` in config/quarterly_chapters.yaml; empty means every agriculture draft prints as a no draft)? names / keep empty
2. Rule the two-bid kill test's "no relationship to forward 20-day returns": a rank correlation of call−put OI percentile against the forward 20-day GLD return over the twelve months, |ρ| < 0.10 and p > 0.10 = killed? yes / other
3. Accept choices 1–6 as they stand? yes / no
4. Merge order, inside windows: AQ-2 part 2, then this branch, then AQ-5 / AQ-6 / AQ-8a in any order, each re-running this gate? yes / no
