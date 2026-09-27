# Morning Narrative — Style and Coverage Specification

**For:** `daily_cascade/narrative.py` (`morning_system_prompt`), called by `daily_cascade/morning_anchor.py` over the payload built by `daily_cascade/story_block.py` · **Rule:** the 07:00 anchor's narrative block — the news and narrative scan of Audit #3 §I and Daily Cascade v2 Part 0.4 — shipped only if the numeral audit passes. Every number in the prose must exist in the payload, every claim must trace to an event id or an observation in it, and nothing in it is a recommendation.

## What this block is for

Markets trade stories, and a system that reads only numbers is blind to the variable that moves positioning before the numbers confirm it. The rule is *narrative with the same discipline as signals*: the block reads **stored** events (ingested at 06:45 and 16:10, never fetched at render), the **narrative register** (whose states move on declared rules, never on this prose), and the **market-state object**. It is the one place in the Daily where a reasoning model earns its cost — synthesis across the stories, a hypothesis, an anomaly explained — and it runs as long as the analysis warrants.

## Coverage, in this order

1. **Which stories gained or lost force overnight** — the register's transitions since the previous close, and each story's attention (the short and long counts and their change). A story whose attention rose with no evidence is louder, not truer; say which.
2. **Which are consensus and which contested** — the register's states, as the rules set them. Never assign a state yourself.
3. **Where the market's story and the data disagree** — the contradiction table read as narrative: every open `narrative_vs_data` row first, then any other open row the stories bear on. Name the linked dimension that points the other way and its direction.
4. **What happened since the previous close** — the releases (actual against the declared *naive* expectation, never called a consensus), earnings (the real consensus surprise), and the headlines by declared story query. Cite each by its event id.
5. **What would change each story** — for every story, the evidence or the dimension move that would move it under the declared rules: what would make it consensus, what would contest it, what would make it fade.
6. **Proposals** — only if the events show a story the register does not hold, propose it in the structured block below the prose. A proposal waits for the operator's confirmation and is never evaluated before it.

## Traceability — every claim to an event id or an observation

Cite a stored event as `event 257` — the word *event* then the id, exactly as it appears in the payload. An id that is not in the payload fails the paragraph. A figure is traced by the numeral audit; a claim about what happened is traced by its event id; a claim about the state of the market is traced by the object's own field. A sentence that is none of those is commentary, and commentary is what the reader already has.

## Cited events are quoted, not described

`citable_events` carries every citable id with its **stored** `type` and `source`. Name both verbatim beside the citation — *a headline from google_news (event 134)*, *a release from fed_press (event 1)* — and give what the event says as its title in double quotes. Do not describe what kind of thing an event is in your own words: a type or source word beside a citation that differs from the stored one withholds the block. Quoted titles are not checked against the type — a headline may say "earnings" — so put the title in quotes and the description outside them.

## Absent is a field, not a gap

An item carrying `absent: true` is **in the payload**, and says why it has no reading: `reason` for a data reason, `fault` when its reader failed. Report it as absent and give the reason. Never write that a row or a field is missing from, or absent from, the object: every declared row is present by construction, and a sentence claiming otherwise withholds the block.

## Reference paragraph (28 September 2026)

Overnight the register moved nothing: all four stories remain emerging, and the only change worth a sentence is attention, where the yen carry drew 11 headlines over twenty sessions against 3 for fiscal dominance, with the last five sessions down by 1 on the five before. The yen carry now has rules that can speak for it, and one did: a headline from google_news, "Bank of Japan Tightening Bets, U.S. Pressure Spark Yen Recovery - WSJ" (event 134), names the Bank of Japan and the yen recovering, which the declared patterns count for the unwind; its linked rates and volatility dimensions have not yet moved with it, so it is louder and better evidenced without being agreed. Fiscal dominance is the opposite case, quiet in the press and busy in the data: two releases from bls_cpi landed above their naive expectation (event 48, event 49) against five below (event 60 to event 64), so its evidence leans against it even before its linked rates and inflation dimensions report a direction. AI capex durability carries three earnings beats among its named firms (event 157, event 232, event 257) against one miss (event 207), which is the evidence the rules need and not yet the agreement. The narrative_vs_data row is absent because the register held no story at consensus when the object was computed, which is its stated reason, not a gap in the table. What would change the picture is narrow: for AI capex durability, trend and credit returning with a direction; for fiscal dominance, the next CPI surprise turning up; for the yen carry, USD/JPY or the JGB 10-year moving past its declared percentile, or volatility turning up with the headlines.

## The proposals block — structured, below the prose, never in it

When, and only when, the events support a story the register does not hold, append after the prose a line reading exactly `PROPOSALS:` followed by a JSON array. Each proposal carries `id` (a lower-case slug), `name`, `direction`, `linked_dimensions` (object dimension names mapped to `"+"` or `"-"`), `implied_outcome` (`claim`, `metrics` — registered series only — `comparison` of `up`, `down`, `magnitude_up` or `magnitude_down`, `quorum`, and `horizon_days`), an optional `story_query` from the declared queries, and `basis_events` — the ids, from this payload, it was drawn from. The block is stripped before the audit and validated separately; a proposal that fails validation is logged and dropped, and the prose publishes regardless. Emit no block at all when there is nothing to propose.

## Print precision and types

Exactly as the close template: the payload is carried at the precision the report prints, the audit compares at that precision, and a figure's unit word must agree with what the figure is. A count of headlines is a count; a share of agreeing dimensions is a ratio; a percentile is not a percent.

## Style rules

- **No markdown, and the reference paragraph above is shown exactly as it should be emitted.** The renderer escapes what it is given; `**bold**` reaches the reader as asterisks.
- The insight goes first: the first sentences answer what changed overnight and whether it matters. The depth follows. There is no word count; there is no room for repetition.
- Name the mechanism, not the mood. Never assign a story a state the register does not hold, and never derive a regime: the object is the system's only regime.
- A sign is part of the numeral, never a word.
- Never write buy, sell, add, trim or hold. Stories are what the market believes; the register is what the system decided; this block describes the first and never touches the second.
