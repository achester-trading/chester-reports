# W-1.3a — the Weekly's storyline opener, candidates, Ahead calendar, productivity line and glossary stamp: session notes

Branch `w-1-3a-opener` from `origin/w-1-2-storyline` at 26894d9. It stacks on
W-1.1, T3.5 and W-1.2 and merges after them. Spec: §4 of
`docs/change-order-weekly-storyline-2026-10-11.md`, items 3.0, 3.8, 3.9, 3.6 and
3.7, as amended 12 Oct. The amended change order is the branch's first commit.

Session A, 12 Oct 2026.

## Gates run

**Not run:** the full local suite (CI is the validate), and anything on the box.
I ran the gates this branch touches one at a time. All of them are green, after
the two fixes noted below the table:

| Gate | Result |
|---|---|
| `validate_weekly_opener` (new) | 28/0 |
| `validate_weekly_calendar` (new) | 38/0 |
| `validate_weekly_storyline` | 30/0 |
| `validate_weekly_stack` | 68/0 |
| `validate_weekly_integrity` | 36/0 |
| `validate_weekly_edits` | 90/0 |
| `validate_weekly_complete` | 57/0 |
| `validate_weekly` | 100/0 (1 skipped) |
| `validate_figure_budget` | 110/0 |
| `validate_no_filler` | 14/0 |
| `validate_edition_consistency` | 14/0 |
| `validate_readability` | 63/0 (the PDF is not validated here: no WeasyPrint) |
| `validate_stack_cadence` | 99/0 |
| `validate_config_refs` | 25/0 |
| `validate_gates` | 31/0 |
| `check_library` | 0 failures |

**Two fixes.** The batch run found two faults, both fixed and both gates re-run
green:

- `book_week` called with no week ending crashed `validate_weekly_stack`. The
  Book B blocks now degrade to a note instead of taking section 10 down.
- The technical appendix printed module paths (`cftc.py`), which trip the id
  rule. The paths are removed.

**Not reached locally.** The machine ran low on memory and the session's tooling
stopped the batch run partway through. These gates were not re-run locally
after the final changes, and CI holds them:

- `validate_stack`, `validate_daily_close`, `validate_morning_anchor`;
- `validate_monthly_frames`, `validate_monthly_stack`, `validate_monthly`;
- `validate_voices`.

An earlier run on this branch, before the Ahead and Book B work, had
`validate_stack`, `validate_daily_close`, `validate_monthly_frames` and
`validate_voices` green.

Gates updated to the new layout:

- `validate_weekly_stack`: its scripted writer replies in the opener's shape
  (`OPENER_TEXT`, `opener_text(tag)`).
- `validate_weekly_storyline`: the précis fixture carries its WEEK paragraph, and
  the summary key is renamed (see the defect below).
- `validate_weekly_edits`: routine releases are checked in the reference tables
  and the notes.
- `validate_readability`: the Weekly's order is opener → tables → charts →
  footnote; its paragraph cap is the band's top.
- `validate_stack_cadence`: the Weekly's paragraph cap is 220 deep and 150
  medium; the frame asks for "120 to 220 words".

The Makefile carries the two new gates. CLAUDE.md now reads fifty-four code
gates.

## What was built

**3.0 The section opener** (`daily_cascade/opener.py`).

- **The order.** On the Weekly, every section's commentary prints first, before
  any table or chart, as one paragraph:
  - the relevance sentence (the précis's, W-1.2 item 2.3);
  - the claim line, in bold;
  - the body;
  - one sentence beginning "**Takeaway:**", the word in bold.

  The tables, sub-sections, summaries, charts and closing lines follow. The
  reference tier follows the last section. The close and the Monthly are
  untouched: the opener is a cadence key, `cadences.weekly.opener`.
- **The bands.** Deep sections run 120–220 words, medium 80–150, and the précis
  150–250. The paragraph guard's cap on the Weekly is the band's top, so it never
  cuts a Takeaway off.
- **The frame.** It carries the shape both as instruction and as a worked
  example: explain, describe, Takeaway. The example's figures are placeholders,
  so none can be copied. The frame tells the writer the tables print below its
  paragraph. The read takes the same shape at the deep band.
- **The audit.** It joins the section writer's other checks. It requires:
  - the text sits in its band;
  - there is exactly one Takeaway, and it is the last sentence;
  - the Takeaway carries no figure, the code-checkable half of "never a
    restatement";
  - the commentary is one paragraph.

  A failure gets the usual one retry with the reason, then the commentary is
  withheld.
- **A withheld commentary** prints "Commentary withheld by the audit: <reason>"
  where the paragraph would have been, before the first table. The section's
  data stays in place, and the footnote no longer repeats the line.
- **The précis** gains a WEEK line: the week in one paragraph, with the same
  band, Takeaway and audit. It opens the edition. TENSION, FOR and AGAINST stay
  in the reply for the record and for next week's outlook, but no longer print.

**3.8 Candidates for the sitting (paper)** (`daily_cascade/book_b.py`).

- **The hook.** It reads `altdata.book_b_scanner.candidates(ending, db_path)`.
  Until that module exists, the block prints "no scanner yet — the first
  candidates arrive with Book B", and a note says the block activates when the
  scanner merges.
- **The list** is ranked by the scanner's own score. Each candidate gets one
  line: instrument, direction, thesis, catalyst and date, invalidation, horizon,
  size band, and the scanner's score.
- **A candidate never prints** if it carries no register draft (`decision_id`),
  or if its instrument is on the restriction list. Each kind is counted in a
  note. The register is where the Brookfield rule is enforced, so a candidate
  prints only after the register has accepted it; the restriction check is the
  second net.
- **A candidate the prior sitting passed over** prints once with its reason,
  "Passed over at the sitting: SPY long — operator judgment." The prior
  edition's printed list is archived in the edition JSON. A passed-over
  candidate is not carried into the next printed list, so it drops after one
  edition.

**3.9 Ahead as the market-moving calendar** (`daily_cascade/ahead.py`,
`config/weekly_ahead.yaml`).

- **The table.** One ranked table with six columns:
  - when (ET);
  - the event;
  - its importance tier;
  - the consensus or modal outcome;
  - why it matters (the event class's transmission channel);
  - the positioning that would amplify a surprise.

  Rows rank by the config tier, then by time. The model ranks nothing.
- **The sources:**
  - `calendar_week` now tags each row with its event class. It keeps scheduled
    earnings, which it used to drop as unmatched releases; that is why the
    9 Oct edition had none.
  - Earnings are classed mega, bank, index or tracked from the config's index
    weight list. Each carries its session (pre-market, post-market, or "session
    not stated" for a bare date), the consensus EPS where carried, and the
    implied move: the ATM straddle mid on the first expiry on or after the
    report, from the chain store, or "implied move not captured".
  - Prediction-market families collapse to their modal outcome; every outcome
    goes to the reference tables.
  - Index rebalances come from the session calendar.
  - The three hand-seeded calendars are read when present. A file missing from
    this branch is named in the footnote.
  - The claims register's dated events (the midterm) are included.
- **Amplifiers** are the class's CFTC contracts at a two-year |z| of at least
  1.5, read from the Positioning section's own rows.
- **Routine releases** (tier-3 data releases and every bill auction) go to the
  reference tables, counted in a note.
- **The playbook slot.** The rank-1 event gets an empty "Playbook: <event>"
  sub-section and `data.playbook`, for W-1.3b to fill.
- **The earnings pass** (`altdata/sources/earnings.universe`) now pulls the
  index-weight names, the hyperscalers and the banks from the config. It is
  still the one network read for earnings; the Weekly reads the events table
  only.

**3.6 The book's productivity line.** Section 10 gets a "Productivity" sub-section
beside the compliance line. Its line reads:

> Triggers fired N → reviewed N → packets drafted N → approved N; register
> decisions (chat rulings on briefs are not book decisions): N open.

- **Passed-over rows.** Below the line is a table with a row for every reviewed
  signal that was not approved. The reason is the register's declined row
  (abstention reason or note), or "no reason recorded".
- **Fired** prints "—" until the scanner exists.

**3.7 The glossary and the appendix.**

- **The stamp.** The glossary opens with "Definitions version <hash>": the short
  hash of the last commit that touched `config/`, at render. Outside a git
  checkout it reads "unavailable (no git checkout)".
- **The technical appendix** is the last reference table (config
  `technical_appendix`). It gives formulas, units and sign conventions for:
  - z, percentile, bp, OAS;
  - net GEX, DEX, the flip;
  - net liquidity, the CFTC net, the implied move, Brier.

  It also lists the GEX/DEX universe, read from the tape's `dealer` symbols, and
  the expiry coverage.
- **The validated tag.** A classification graded at least `validated_min_n` (30)
  times prints "(validated, n=K)", and its glossary entry calls it a validated
  signal. None qualifies today.

**A W-1.2 defect fixed on the way.** W-1.2's one-line summaries were stored
under the section key `collapsed`. `stack.assemble` already sets that key to a
boolean, "unchanged since the prior edition". This had two effects:

- `setdefault("collapsed", [])` returned `False`, so every collapse step failed
  into the log (voices, families, extremes);
- an unchanged section would have made the renderer call `list(True)`.

The summaries now live under `summarised`. The Weekly's build also carries
`summarised`, `reference` and `notes` from the built sections, which `assemble`
dropped.

## Choices made for the operator to overrule

- **The band is measured over the writer's text** (claim, body and Takeaway),
  not the relevance sentence. The précis writes that sentence after the
  sections, so the writer cannot count it.
- **"Never a restatement" is audited as "the Takeaway carries no figure".**
  Whether it states a real implication is left to the reader.
- **The claim stays bold inside the opener paragraph**, and it is still the
  email subject. The précis's tension, for and against no longer print; the
  WEEK paragraph carries them.
- **The worked example** is written fresh in the 9 Oct storyline paragraphs'
  shape, with placeholder figures. `weekly-2026-10-09-storyline.md` is not in
  the repository, so I could not quote its shape.
- **The scanner's documented shape.** The brief points to the Enterprise Layer
  spec's Book B section, and `docs/briefs/enterprise-layer-spec-2026-09-27.md`
  has none. I built against Audit #4 agenda item 3's description: drafts in the
  register with level, invalidation, time stop, falsifiers and pre-check. The
  fields are listed in `book_b.py`. `decision_id` is required.
- **The productivity counts:**
  - fired: the scanner's candidates;
  - reviewed: decisions with an operator action or a decline created this week,
    plus last week's printed candidates now ruled on;
  - drafted: decisions entered this week that are not supersessions;
  - approved: the attention count's approvals.

  The register's in-place status changes carry no timestamp, so "reviewed this
  week" is dated by row creation.
- **The decisions count** is the register's open (draft or active) decisions,
  with the caption.
- **The tiers, channels and amplifiers** in `config/weekly_ahead.yaml` are all
  session-set:
  - CPI, PCE, payrolls, GDP, the FOMC decision, the refunding, a quarterly
    expiry and a top-ten index-weight name are tier 1;
  - minutes, the Chair, tier-2 data, the benchmark auctions, a monthly expiry, a
    rebalance, a bank and the EM and China calendars are tier 2;
  - other speakers and coupons, tracked names, prediction families and Thailand
    are tier 3.
- **Routine** means a release no class names, plus every bill auction. UMich,
  H.4.1, industrial production, housing starts, durable goods and consumer
  credit now go to the reference tables.
- **The index-weight list** (the top 25 by S&P 500 weight, as of 30 Sep) is
  hand-seeded, with ranks 1–10 as mega. It widens the earnings pass from 12
  names to 29.
- **The playbook sub-section is placed last in Ahead**, after Watching and the
  graded calls. It prints nothing until W-1.3b fills it.
- **The implied move uses the newest capture within five days.** Only SPY is
  captured today, so every single name reads "not captured".
- **The definitions version is the last commit that touched `config/`**, not
  HEAD. The stamp changes only when a definition could have.

## Needs you

1. **Keep the opener's band measured over the writer's text, excluding the
   précis's relevance sentence?** Yes / no.
2. **Keep the tier map in `config/weekly_ahead.yaml` as proposed?** In
   particular: a top-ten index-weight earnings report is tier 1, beside CPI. Yes /
   no, or name the changes.
3. **The Book B scanner's output shape.** The Enterprise Layer spec has no Book B
   section. Confirm the fields in `daily_cascade/book_b.py`, especially the
   required register `decision_id`, or point me to the document that defines
   them.
4. **Widen the earnings pass to the 25 index-weight names, the hyperscalers and
   the banks?** It is the box's existing yfinance calendar read, 17 more
   symbols on the same pass (12 to 29). It reaches the box at the next pull after merge.
   Yes / no.
5. **The three hand-seeded calendars** (`em_calendar.yaml`,
   `china_political_calendar.yaml`, `thailand_political_calendar.yaml`) live on
   the unmerged `c1-move-screen` and `aq-2-chapters-2` branches. Ahead reads
   them once they merge and names them as absent until then. Keep that order
   rather than copying the templates here? Yes / no.
