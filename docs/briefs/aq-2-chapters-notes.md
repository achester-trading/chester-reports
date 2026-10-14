# AQ-2 part 1 — the chapter machinery and the first three deep chapters: build notes (11 Oct 2026)

Branch `aq-2-chapters-1`, built on `aq-1-quarterly-cadence`. Not merged. It
follows the change order
`docs/change-order-alternative-assets-quarterly-2026-10-10.md`: §4.1 item by
item, §4.2–§4.4, §5, §6, §8 and §10A.

## What was built

- **`config/quarterly_chapters.yaml`.** For each filled family it declares:
  - the five lines;
  - the Tier 1/2 structure series. Each is either an existing registry key, or
    `absent: <reason>`, which prints by name as not tracked;
  - two structure charts;
  - the funds whose option chains give the implied range;
  - the curve's wait;
  - the analyses, with their hooks and their kill conditions as §5 rules them;
  - **the falsification tests:** `{id, paper, section, statement, measurable |
    null}`, with the statement in the paper's own words, verbatim;
  - **the ten questions:** Appendix D, verbatim;
  - the permitted and banned words;
  - a figure budget per written item.

  It also carries oil's second half (gas, power and uranium, a sub-chapter) and
  currency's named pair universe (the deep basket and the scan tier).
- **`monthly_macro/quarterly_items.py`.** The item builders the shell calls.
  Each degrades to the not-yet footnote with its reason; nothing is blank and
  nothing is invented. A filled chapter's sub-sections:

  | Tier | Item | What it reads |
  |---|---|---|
  | lead | Confidence and what changed | Weakest link: the stalest tracked series and the count of untracked structure series. Brier to date: AQ-6's `grades()`. Standing dissent: the minority side among the quarter's stored voices on the family's subject. What changed: each falsification test's state against the prior Quarterly's |
  | lead | 1 · Last quarter's theses, graded | AQ-6 `graded_table()` (the AQ-1 hook) |
  | lead | 2 · Theses | AQ-6 `seed_table()`, the chapter's family (AQ-1 hook) |
  | lead | 3 · The quarter | Five lines over the payload's quarter window, from the store as of. Three charts: the family's long frame (AQ-4 hook) and the two structure charts, drawn in the house style |
  | reference | 3 · The quarter: why | The QTD/YTD table (AQ-4 hook, `tools.horizon_charts.compute`); the driver-attribution row (AQ-8a hook `attribution.driver_table`: explained share, largest loading, the residual's sign, sign stability) |
  | reference | 3a · What's priced | The curve (6b; oil prints its one stored point, the WTI prompt spread). The options-implied range from the chain store: ATM IV at the expiry nearest 91 days, a one-sigma range. Consensus against spot: AQ-7 |
  | reference | 4 · Structure | Latest, change on the quarter, percentile over the full history (n), and the five-year column "until the lenses" |
  | reference | 4b · The second half (oil) | Gas, power and uranium: their structure and the paper's five tests on them |
  | reference | 4c · The pair universe (currency) | The deep basket (stored pairs with latest, quarter change, percentile, envelope; the rest named), and the scan tier (fifteen, by name) |
  | reference | 5 · Supply and demand | The agency tables (AQ-7). One written read answering the four questions, asked only where the quarter holds stored voices on the family. It reads the five lines' largest moves (within the budget) and the voices' views with their numbers masked. With no stored voice it prints "no stored source, not printed" |
  | reference | 6 · The analyses | Each analysis's state from its hook (AQ-8a `gold_block`, `two_bid_state`, `triple`; AQ-5 `triple`) or its stored series, beside its kill condition as ruled |
  | reference | 7 · Falsification tests | Holds / strained / failed, computed by code where a measurable exists; "not measured — <reason>" otherwise. One row each, in the paper's wording, with the evidence read |
  | reference | 8 · Correlations | AQ-5 (the AQ-1 hook) |
  | reference | 9 · Emerging stories | The quarter's stored voices on the family, with their sources. The structural-change line ("none confirmed", with its reason) |
  | reference | 10 · The book | AQ-6's `alt_asset_books` for the coming quarter: drafts, or the no-draft line |
  | reference | 11 · The ten questions | One audited line per question. A question whose series nothing stores is answered "Not answered: no stored source" by code, without a call |

- **The transmission map.** The front matter's opening figure (Q0, in The read):
  the six arrows of §3 in the house style, counted in the chart cap.
- **Charts and delivery.**
  - Chart ids are Q0, Q1, …; drawn charts count toward the cap of 40.
  - Over the cap, a chart is marked unavailable and named, never dropped
    silently.
  - Archived PNGs are `alt_asset_<date>_q<n>.png`; the Monthly's chart module
    takes a prefix, and `cids_in` reads the Q series.
- **The prose.** Through the stack's writer:
  - item 5 through `block_plan`, which now honours a block's own figure budget
    and never goes above the cadence's cap;
  - item 11 through `write_all`, one call per answerable question, with its own
    frame.
- **Gate.** `tools/validate_quarterly_stack.py` group G (65 checks in the file).
  It extends the AQ-1 gate's synthetic store with two and a half years of the
  three chapters' series and three voices on gold. It checks:
  - the filled and shell chapters;
  - every series is registered or named absent;
  - the measurables reference registered keys;
  - each test's statement and each question is the paper's verbatim;
  - the figure budgets;
  - every item renders or says why not;
  - the lead page;
  - the confidence line with a named dissent;
  - the five lines and the three charts;
  - the dual percentiles;
  - the tests computed: Metals holds; the Fed-fighting test fails on the seeded
    easing with CPI above 3%;
  - oil's second half and currency's pair universe;
  - the item 5 frame within budget;
  - the questions;
  - the transmission map in the cap;
  - the executive summary over all eleven chapters.

## What waits, and for what

| Waits for | What |
|---|---|
| **AQ-4** (horizon charts) | The family's long frame (lead chart 1 of 3) and the QTD/YTD table. The hook calls `tools.horizon_charts.compute` and `draw_frame` once the branch is merged |
| **AQ-5** (correlation layer) | Item 8, and the copper/gold-against-the-10-year analysis |
| **AQ-6** (thesis register) | Items 1, 2 and 10; the Brier on the confidence line |
| **AQ-8a** (attribution) | The driver-attribution row; the gold residual and the two-bid in item 6; yields-up/dollar-down, as an analysis and as the measurable the "disorderly tail" test needs (null until then, naming the key) |
| **AQ-7** (quarterly scan) | The agency balances (item 5); consensus against spot (3a); the scan's stories (item 9); the Silver Institute test |
| **AQ-3** (series) | Every structure row marked absent: ETF tonnage, disaggregated COT, exchange inventories, TC/RCs, TTF/JKM/EU storage, PJM, uranium, rigs, OVX, the H.10 pairs, the basis, stablecoin supply. Their tests stay "not measured" until then |
| **6b** (futures curves) | The curve against spot and the roll (3a) |
| **The lenses (6e)** | The five-year percentile column |
| **The chain capture** | The implied range. GLD, SLV and USO are captured from AQ-8a; FXE and FXY are not captured at all |
| **The tail watch's log and the intake register** | The structural-change line's status. It prints "none confirmed" with that reason until they are stored |

## Choices made in the build, for the operator to overrule

1. **The papers govern the tests and the questions.** Where the change order's
   summary of a paper's tests differs from the paper, the paper's own
   "Falsification Tests" section is encoded: Metals 7, Energy 7, Currencies 6.
   - Metals: the change order lists "target-driven buying", "TC/RC as the early
     warning" and "scrap response"; the paper's seven are the ones encoded.
   - Currencies: the change order's "intervention resets positioning" is not
     among the paper's six.
2. **Item 7 is reference.** The brief puts items 1, 2 and 3 and the two lead
   lines on the lead page; §3 had also listed the tests' one-line verdicts there.
   This is one key in `config/reporting_stack.yaml`'s template.
3. **Thresholds the papers do not state numerically** (marked `session_set`):
   - "Tight inverse correlation to TIPS" is read as a 63-session correlation of
     gold's log returns against DFII10's daily changes at or below −0.5,
     strained at or below −0.3.
   - "Its 2024 levels" is read as gold's 2024 mean; "net sellers" as official
     holdings down over the last quarter.
   - "The Fed easing" is read as the funds rate lower over the quarter. "Without
     a clear growth deterioration" is not measured, and the line says so.
4. **The implied range:** ATM IV at the expiry nearest 91 days (at least 7),
   spot × exp(±IV·√(days/365)).
5. **The confidence line's weakest link** is the tracked series whose last
   observation is oldest at the quarter's end, plus the count of untracked
   structure series.
6. **The standing dissent** is the minority side among each voice's latest
   direction on the family's subject this quarter. An even split names no one.
7. **The chapters' permitted and banned words** are session-set starting lists
   (e.g. metals bans "safe haven", "inflation hedge", "store of value"), fed to
   the chapter's frames. They are for the operator to rule.
8. **The figure budgets:**
   - five for the quarter's lines, four for item 5, two per question, three for
     the summary (the cadence's three);
   - T3.4 (`t3-4-figure-budget`) is not merged under this branch, and it carries
     no notes file, so its rule is applied here at each item's frame: the
     largest moves up to the budget with their display forms, the rest by name;
   - when T3.4 merges, the Quarterly's parent frames can take its
     `parent_frame`.
9. **The second half's tests are printed twice:** in item 7 with all seven, and
   in the second-half sub-chapter.

## Needs you

- **Rule** the permitted and banned words per chapter, and the session-set
  thresholds in choice 3.
- **Confirm** item 7's tier (reference, per this brief) against §3's lead page.
- **Merge order** (when you say, inside windows): AQ-1, then this. AQ-4, AQ-5,
  AQ-6 and AQ-8a then light their hooks in any order; nothing here needs
  changing when they land.
- **Part 2:** the other eight chapters (EM, China, crypto, real estate, credit,
  international equities, Thailand, agriculture).
- **The December dry run on the box** (yours): the three chapters on real data
  for the first time.
