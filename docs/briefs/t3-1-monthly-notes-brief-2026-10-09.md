# T3.1 — the Monthly after its first dry run: Ari's notes, two rounds (9 Oct 2026)

| | |
|---|---|
| Status | Ruled 9 Oct 2026 in chat (the operator's notes on the 8 Oct `[DRY RUN]` Monthly, rounds one and two). Binds session B's T3.1 build. |
| Owner | Ari Chester |
| Scope | The stacked Monthly only (`monthly_macro/stack.py`, the shared stack code at cadence "monthly", `config/reporting_stack.yaml`). The Weekly and the close change only where a shared builder changes and the change is cadence-gated. |
| Amends | Doctrine monthly item 7a (no content change to Monthly v2 Phase A before the 23 Oct dry run) — the operator's own ruling, amended by these notes: the executive summary (item 20) and the themes paragraphs (item 19) are content. Everything else is shape. |
| Lands | Branch `t3-1-monthly-notes` during the freeze (13–15 Oct); merge to main Fri 16 Oct inside a window; first seen in the 23 Oct dry run. |
| Hours | ≈ 27 h of session work in two sittings (round one ≈ 17 h, round two ≈ 10 h). |

**The principle behind every item:** the operator reads the Monthly for takeaways, not for numbers. Wherever a table carried the message, a written read now carries it and the table supports it. Nothing is trimmed: the word budget rises to carry the prose (item 23).

## The rulings, section by section

Numbers 1–17 are round one, 18–22 round two, 22 the budget. "Prose" means a model-written paragraph through the Monthly's section writer, behind the same audits as every other paragraph (numeral audit, flag-word audit, "no stored source, not printed"); the writer prints nothing it cannot cite from the section's own data.

### Delivery

1. **Text wraps on the phone.** The page already flows below 720 px; the cause is the tables — every cell is `white-space:nowrap` and Gmail on iPhone ignores horizontal scrolling, so one wide table zooms the whole email out. Fix: text cells wrap (`nowrap` only on numeric cells), `table-layout:fixed` on tables wider than six columns, images already fluid; and attach the edition's `.html` to the email so Safari renders it responsively. Verify with a 390 px-wide render. (`stack_render.py` TBL/SCROLL; `deliver.py`.) ~1.5 h.

### The tape

2. **First table: close and move only, plus YTD.** Drop the prior-month-close column; add YTD (from the prior year-end close in the store). ~0.5 h.
3. **Long frames keep their ruled values, labelled with the daily equivalent**: "40-week (≈200-day)", "10-month (≈210-day)", "20-month (≈400-day)". Levels, never signals, as ruled 2 Oct. ~0.25 h.
4. **Cross-asset table (GTM-14): month, YTD, twelve months.** Prior-month and twelve-month returns from the store's daily closes. ~0.5 h.
5. **156-week SPY chart carries the "% from high" underlay**, the same construction as the 120-month chart. (`charts.py`.) ~0.5 h.
6. **A 3-month daily SPY bar chart, placed first**, with the 50- and 200-day averages; then the weekly, then the monthly — daily → weekly → monthly. Chart count net +1 here, −9 under item 11; the cap of ten holds. ~1 h.

### What doesn't fit

7. **Paragraphs with headers and bullets instead of the table.** Each item that fits is a short header (what doesn't fit), one sentence on the mechanism, bullets for the figures. The table's data stays the source; the renderer changes at monthly cadence only. ~1.5 h.

### Plumbing & rates

8. **Six buckets, each a table and a written takeaway, the two charts under their paragraphs.** Buckets: yields & spreads; macro (employment, income, GDP); liquidity; auction results; metals; global rates. Assignment by the registry's `family` where it exists and by a bucket map in `config/reporting_stack.yaml` where it does not; a series the map does not name prints under "other" and the validator counts those. One prose paragraph per bucket (≈ 60–100 words). ~4 h.

### Positioning & flows

9. **Horizons at monthly cadence: The month · Three months · Twelve months.** "One month" (the trailing 22 sessions) is dropped at the monthly cadence — it duplicates "the month" at month-end. (`weekly_sections.sector_table`, cadence-gated.) ~0.5 h.
10. **A written read on every sub-section** — sectors, speculative positioning (CFTC), short interest, retail sentiment, foreign flows (TIC): level, change against the prior month, and where the level sits in the series' own history (the z or the dual percentile where 6e has built it; "history too short" printed where it is), one paragraph each. ~2.5 h with item 11.
11. **The ten small panels go; one ranked bar chart of current z-scores across every positioning series replaces them.** The z-score is the insight; ten panes hid it. ~1 h.

### What's priced

12. **FOMC pricing and the breakevens split into two blocks, each with a few sentences of read**; the fed-funds-futures chart and the breakeven chart move inline beside their blocks. ~1.5 h.
13. **Prediction markets split into FOMC markets and the rest, a paragraph each**; political markets are read for their market channel (what a change in the odds would move, and through what). ~1.5 h.

### Ahead

14. **Every row carries the weekday and a 1–5 significance rank** from the release calendar's tiers (tier 1 → 5; tier 2 → 3 or 4 by the plumbing trigger's list; everything else 1 or 2), with a one-clause reason on ranks 4–5. (`events_block.py`, `config/release_calendar.yaml`.) ~1 h.

### Mechanics (no change in this build)

15. The dealer retrospective stays as built; the FlashAlpha vendor line comes with 6b's rewire (ledger of 9 Oct).

### Narratives

16. **Every Narratives table gains a longer-horizon column**: for the stories, evidence counts over three months and since the register began; for the voices, status over three months. Where the Phase B register (started 4 Oct) is younger than the window, the cell prints "since 4 Oct" with the count it has, never a blank. ~1.5 h.
17. **The voices as paragraphs and bullets, not a table**: one short paragraph per story — who said what, status, dissent — with the source line under each bullet. `voices_block.py` stays the only renderer; the monthly view is a prose view behind the same audit. ~1.5 h.

### Scenarios

18. **Paragraph summaries in narrative form; "what would change our mind" in two or three sentences**, not a list of variables. The renderer changes now; the content arrives when scenario set #1 is ruled (Audit #4, item II.2) — until then the block prints its placeholder in the new shape. ~1.5 h.

### Slow layers — themes

19. **A paragraph for each alternative-asset family** (the families in `config/monthly_themes.yaml`), written from the family's rows: what moved, what the long frame says, what the operator should take away. ~2 h.

### The edition as a whole

20. **An executive summary opens the edition, before section 1**: one paragraph of three to five sentences per section, in stack order (the read, the tape, mechanics, what doesn't fit, plumbing & rates, positioning & flows, what's priced, narratives, reading, ahead, the book, slow layers), each carrying that section's takeaways and its two or three load-bearing figures. Built last, from the finished sections (never from the raw payload), by one model call per section through the same writer and audits; a summary paragraph that fails its audit prints "(summary withheld — audit)" rather than an unaudited sentence. It is prose and counts in the budget. ~3 h.
21. **Organisation of the body: unchanged in this build.** The operator reads the 23 Oct dry run with the summary in place and decides the order of the body at the 28 Oct dry run; nothing is trimmed meanwhile.

### Budget

22. **The Monthly's word budget rises to 10,000 and its reading target to 55 minutes** (`config/reporting_stack.yaml`: `budgets.monthly.words`, `reading_targets_minutes.monthly`), so that nothing is trimmed to make room for the prose these notes add (≈ 3,000 words). The executive summary with section 1 is the short path and prints its own reading time. The operator confirms or changes the two numbers at the 23 Oct dry run with the count in front of him; the chart cap of ten is unchanged.

## What the session reports back

The branch, CI run id, the word count and chart count of a `--dry-run` edition against the current store, the reading time printed, a 390 px render of two sections (the tape and plumbing & rates) as PNG attachments, and a "needs you" list. No merge, no deploy, no email: the merge is the operator's word on Fri 16 Oct.
