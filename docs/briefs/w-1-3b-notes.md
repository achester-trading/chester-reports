# W-1.3b — the Weekly's descriptive analytics: session notes

Branch `w-1-3b-analytics` from the tip of `w-1-3a-opener` (d17bf8b). It stacks on
W-1.1, T3.5, W-1.2 and W-1.3a. Spec: §4 of
`docs/change-order-weekly-storyline-2026-10-11.md`, items 3.1–3.5, and the W-1.3b
paste of 12 Oct.

Everything built here is DESCRIPTIVE. Each piece labels what stored data shows by
a declared rule, in `config/weekly_analytics.yaml`. Forward-outcome statistics
are the scorecard track's and are not built.

Session A, 12 Oct 2026.

## Gates run

**Not run:** the full local suite (CI is the validate), and anything on the box.
No register write was made: the gate's register rows are in-memory dicts, and
its narrative row lives in a temporary database. I ran the gates this branch
touches one at a time; all are green:

| Gate | Result |
|---|---|
| `validate_weekly_analytics` (new) | 30/0 |
| `validate_weekly_calendar` | 38/0 |
| `validate_weekly_opener` | 28/0 |
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
| `validate_voices` | 70/0 |
| `validate_monthly_frames` | 32/0 |
| `validate_monthly_stack` | 261/0 |
| `validate_monthly` | 350/0 (1 skipped) |
| `validate_stack` | 66/0 |
| `validate_daily_close` | 102/0 |
| `validate_morning_anchor` | 71/0 |
| `validate_config_refs` | 26/0 |
| `validate_gates` | 31/0 |
| `check_library` | 0 failures |

**Not re-run.** Two small edits came after the Weekly gates' last local runs:
the 10A blocks became Weekly-only, and the no-matrix line moved to a note. Neither
changes what the Weekly prints on the fixture. CI holds them.

Gates updated:

- `validate_weekly_edits`: Positioning now has seven sub-sections, adding TFF and
  ETF shares.
- `validate_weekly_integrity`: the tiered exceptions table keeps "Exception
  since", with "opened this week" beside the date.
- `validate_weekly_calendar`: the playbook slot is filled now.

The Makefile carries the new gate. CLAUDE.md reads fifty-five code gates.

## What was built

**3.1 Narratives** (`daily_cascade/analytics.py`, `daily_cascade/voices_block.py`,
`altdata/voices.py`).

- **Each ledger item** carries:
  - a source class (official, data, sell-side or press), from its voice's kind;
    an outlet the config names as a data agency is "data";
  - an event-cluster id: the source URL's root, the published date and the
    story.
- **Counts are by cluster**, never by item: "2 clusters for, 0 against". The
  Stories table's columns are:
  - Story;
  - State;
  - Status;
  - This week, by event cluster;
  - Steelman (the counter-case);
  - Dissent.

  The register's to-date item counts left the table; they were item counts.
- **The steelman.** The voices scan now ends with a counter-case search. Each
  story's queries (config `narratives.stories.<id>.steelman_queries`) are run
  against the voices stored over the past seven days. Each search is recorded in
  a new table, `steelman_searches`, found or not. The Weekly prints what was
  found, or "none found after search: <queries>", or "not searched this week"
  where the scan wrote no row.
- **The status** comes from a fixed vocabulary. The rules are tried in order:
  - **tradeable:** a linked instrument has a draft or active register decision;
  - **priced:** the story's declared variable is at its implied level;
  - **catalysed:** a declared catalyst, or a linked name's scheduled earnings,
    falls within 30 days;
  - **long-term theme:** otherwise.
- **Unreachable sources** get a sub-section: source, why, last scanned cleanly,
  and the active theses whose evidence came from it.
- **The ledger.** The reference tables carry every item with its class, cluster,
  label and stored excerpt. The excerpt goes through the voices block's view
  audit, as the steelman's view does.

**3.2 Exceptions.**

- **Three tables, in tier order:** potential leading indicator, contemporaneous
  contradiction, extreme without a trade.
- **The tier** comes from config by kind. An extreme in credit spreads, the 2s10s
  curve or claims is "potential leading indicator".
- **Labels.** Each row carries its labels:
  - **level:** in its five-year top or bottom decile;
  - **change:** its seven-day change at |z| ≥ 2;
  - **extreme:** at its five-year bound.
- **Descriptive fields.** Each row also carries a resolution path, a catalyst
  and an invalidation, from a template per tier.
- **"Opened this week"** now sits beside the exception-since date.
- **The Monthly** shares this builder, so its What doesn't fit tiers the same
  way.

**3.3 Positioning (Weekly only).**

- **Two new blocks.** TFF categories (leveraged funds, asset managers, dealers)
  as % of open interest, and the ETF share counts (GLD, IAU, SLV, IBIT).
- **The positioning-change score.** Every TFF, ETF and CFTC row now carries the
  four-week change as a z against two years, beside the level z.
- **Not stored yet.** The TFF and ETF keys (`cftc.tff_*_net_oi`,
  `etf.*_shares`) are written by the unmerged AQ-3 branches. Until they merge,
  both blocks say the series are not stored.
- **Thin samples.** An RTAT row with fewer than 4 observations prints "thin sample
  (n=K)" and is kept out of `sentiment_composite_members`.
- **TIC** already printed its reference month and release date (W-1.1); the gate
  re-checks it.

**3.4 What's priced.**

- **The matrix.** An event × market matrix for Ahead's tier-1 events of the
  FOMC, CPI, payrolls and GDP classes. Its columns are fed funds futures,
  Kalshi, Polymarket, economist consensus and the disagreement.
- **Like with like.** Each cell is that market's probability of one outcome. For
  the FOMC, that is the fed funds path's modal move, against the prediction
  markets' normalised odds for the meeting.
- **The disagreement column** prints the spread in points. It is flagged at the
  15-point cross-venue threshold (`prediction_markets.disagreement_points`).
- **Not compared.** Prediction markets that list different contracts are not
  compared.
- **The consensus column** prints "—": no consensus feed exists.
- **Where it prints.** The matrix is a second table inside the Prediction markets
  block, so the section keeps its three sub-chapters.

**3.5 Ahead's playbook.**

- **The event.** The playbook goes to the highest-ranked event whose class has an
  outcome map; on the fixture, that is CPI.
- **The table.** Hot, in-line and cool, each with three cells:
  - its transmission across yields, dollar, equities and vol, from config;
  - the crowded CFTC positions that outcome would move against;
  - one frame sentence.

  A position amplifies when its sign × its contract's exposure × the channel's
  move is negative: a crowded long in 10-year notes amplifies a hot print.
- **The frame sentences** come from one audited model call after the prose. The
  audit refuses figures, refused words and anything past 30 words; one retry,
  then a dash.

## Choices made for the operator to overrule

- **The cluster key** is the URL root, the date and the story. Two officials on
  the same agency site the same day about the same story are one cluster, even
  when they gave separate speeches.
- **The steelman "search"** is a keyword search of the voices the scan has
  already stored over seven days, not a new network search. The scan reads only
  its declared sources and makes no web search. The queries are session-seeded,
  in config.
- **The status precedence** is tradeable, then priced, then catalysed, then
  long-term theme. Only fiscal dominance has a "priced" rule (the 10-year term
  premium at 1.0%), and only the midterm story has a hand-seeded catalyst.
- **The exception tiers:**
  - contradiction → contemporaneous contradiction;
  - extreme → extreme without a trade, except credit spreads, 2s10s and claims,
    which are potential leading indicators.

  The templates are generic per tier.
- **The 10A blocks are Weekly only.** The Monthly's Positioning keeps its five
  read blocks.
- **The thin-sample threshold is 4.** The Weekly has no sentiment composite yet,
  so the exclusion is a recorded membership list ready for one.
- **The matrix covers only tier-1 events** of the four priced classes. The
  economist-consensus column waits for a feed.
- **The playbook's channel signs.** For example, a cool payrolls print is
  equities down and vol up: the bad-news-is-bad reading. They are a proposal.

## Needs you

1. **Keep the steelman as a search of the stored voices**, rather than a new
   network query per story in the scan? Yes / no.
2. **Keep the story-status precedence** (tradeable > priced > catalysed >
   long-term theme) and the seeded rules in `config/weekly_analytics.yaml`? Yes /
   no, or name the changes.
3. **Keep the exception tiers as mapped:** credit spreads, 2s10s and claims
   extremes as potential leading indicators, other extremes as extremes without
   a trade? Yes / no.
4. **Keep the playbook's outcome map,** especially a cool payrolls print as
   equities down and vol up? Yes / no.
5. **The Monthly's What doesn't fit now tiers its exceptions too,** through the
   shared builder. Keep that, or hold the tiers to the Weekly? Keep / Weekly
   only.

## Follow-up, 12 Oct: two rulings applied

**1. The Book B candidate's shape** (W-1.3a Needs you 3). A candidate carries
the register's draft fields, as the Alternative Assets change order §4.1 item 10
lists them:

- instrument, direction, thesis, edge;
- horizon, size, invalidation, counter-thesis.

It also carries:

- `setup_id`, a family `config/setups.yaml` declares (EL-1);
- the scanner's `score`;
- the catalyst and its date;
- `candidate_id`.

`decision_id` is null on every candidate. It is assigned only when the sitting
approves a packet.

`daily_cascade/book_b.py` changes accordingly:

- **What prints.** A candidate with an id and a declared setup, on an
  instrument the restriction list does not name. It is ranked by the scanner's
  score.
- **A passed-over candidate.** Last week's printed candidate is matched to the
  week's register rows by instrument, direction and setup:
  - an approved lineage is not a pass;
  - a declined row gives the reason;
  - no row at all is a pass with "no reason recorded".

`validate_weekly_calendar`'s fixture and checks follow the ruled shape (39/0).

**2. The playbook's regime switch** (W-1.3b Needs you 4). When the stored fed
funds path prices hikes, a cool growth print's equity and volatility cells read
"two-sided — rates relief against growth fear". Pricing hikes means the implied
rate rising from the next meeting over the following four. Otherwise the map
stands. Both branches are fixtured in `validate_weekly_analytics`.
