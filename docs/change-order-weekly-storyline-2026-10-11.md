# Change order — the Weekly: integrity, storyline, descriptive analytics (W-1, provisional)

| | |
|---|---|
| Status | **Ruled, 11 Oct 2026.** Recommendations accepted in chat 11 Oct ("Yes, I accept your recommendations"); the five rulings in §8 taken one at a time the same morning, all as proposed. Tranche 1 is specified to paste level and goes to session A tonight; tranche 2's three open points (§3) wait for dry run #4 and Monday's rulings; tranche 3 follows tranche 2. The id W-1 is provisional — Audit #4 numbers it. |
| Owner | Ari Chester |
| Inputs | The Weekly of 9 Oct 2026 (19 pp); the reader's storyline rewrite of it (`weekly-2026-10-09-storyline.md`); the operator's critique and GPT's review of the same edition (11 Oct); T3.4 (figure budget at the frame), merged 11 Oct. |
| Why | The edition had the week's story in its tables and did not tell it. Six of ten commentaries were withheld by the figure cap (T3.4 fixes the mechanism); but a fully-commented edition would still lack a through-line, because each section's prose is written from its own frame and no frame sees the others. Beneath that, the edition carries reconcilable inconsistencies it does not catch itself. Order of work: catch the inconsistencies first, then tell the story, then sharpen the analytics that need no evidence sample. The validated and probabilistic layers wait for the scorecard — evidence does not compress. |

## 1. The disposition of GPT's review

Adopted and in this order: evidence weighting over evidence counts; a pre-publication consistency gate; age-vs-status vocabulary for exceptions; auction fields; level/change/extreme labels; a productivity line in the book; "unvalidated" tags on descriptive classifications; coincidence not causation in the read. Confirmed as already built or scheduled (no change): scenario set #1 and the prediction-market mapping; the scorecard's pre-registration ledger and base rates; `available_at` point-in-time discipline; the thesis register; the §10A positioning standard (extended here to the Weekly); the 6b dealer block; AQ-3's global rates; the Book B scanner; DTH-1. Deferred to the evidence tracks (§6). Declined with reasons (§7).

## 2. Tranche 1 — integrity (W-1.1; this week; overnight, branch-only)

The principle: the report identifies and explains its own inconsistencies; a reader never has to.

**1.0 The figure budget's second pass (T3.4c — added 11 Oct from the Weekly dry run on T3.4).** The dry run on the 9 Oct data commented 6 of 10 sections (was 4 of 10) and showed three faults in the budget itself. (a) *Filler:* the "also moved" names given to the model come back as sentences — "the 10-year, 30-year and 2-year all moved alongside…", "futures across the S&P 500, Nasdaq-100, Russell 2000 … moved through the week" — which say nothing. The frame now carries the also-moved names as "in the tables; do not enumerate", bans the sentence form "X, Y and Z (also|all) moved", and a gate (`validate_no_filler`, pattern `(also|all) mov(ed|ing)` in prose) withholds a paragraph that uses it. (b) *The wrong six:* ranking moves relative to level favours low-level series — IG OAS −4 bp outranked CCC +37 bp — so plumbing's prose concluded "credit showing no stress" while the week's credit fact was the CCC blow-out. Ranking becomes the z of the week's change against the series' trailing-year changes (fallback: relative to level when fewer than 60 observations exist). (c) *Allocation:* positioning spent all six figures on six sector returns and had none left for the COT extremes. Sections with three or more sub-blocks (plumbing, positioning, priced) get a cap of 8 on the Weekly with at least one figure per sub-block that moved, the remainder to the largest z. Also: the budget extends to the four frames it did not cover — read (15 figures cited), mechanics (12), misfit (7), ahead (7); the comparison vocabulary the book gate requires ("excess", "relative to") is carried into the read and book frames as the banned list is (T3.4a's pattern); the events-line builder's "attributed the move in oil to Oil prices rose…" is fixed to take a clause or a quotation. **≈ 4 h, inside W-1.1.**

**1.1 Cross-table consistency gate.** A new pre-publication gate (`tools/validate_edition_consistency.py`, run inside the Weekly's render, reading the rendered payload only) checks that any figure keyed by (series, as-of) that appears in more than one table or frame is identical at printed precision. On a mismatch within rounding tolerance the edition prints one canonical value in every place and logs the source of the difference; beyond tolerance the gate fails the run. First case: SPY's weekly return printed +1.16% in the tape and +1.17% in the overnight/cash split. The session finds the convention difference (close-to-close vs compounded overnight + cash sessions, or a different close), fixes to one convention, and documents it in the glossary.

**1.2 Per-row as-of and freshness.** Every table row carries its effective date, taken from the store's bar date or `available_at`. The edition header's "as of" is the latest; rows older than the edition cutoff print their own date. A price series whose last bar is older than the edition date prints "stale since <date>" in place of a bare price (the Bitcoin case). Slow series with an expected lag (TIC monthly, WASDE, IMF) carry "lag: monthly (July, released Sep)" from a per-series config value, not "stale". Blank-rather-than-guessed stays the rule for missing inputs.

**1.3 Age versus status.** Contradictions and exceptions print three dates — "gap since · pending since · exception since" — so a gap measured for eight sessions and promoted to exception this week is not printed as one number. The read's prose uses "open n sessions" only for the gap age. The glossary states the z-score window and what the gap z measures (cumulative divergence over the window, not the week's move), and the contradictions table prints the window.

**1.4 Auction fields.** The auction writer stores tail/stop-through versus when-issued, bid-to-cover, indirect %, direct %, dealer %, and each one's percentile against the trailing two years; the table prints them. The word "tail" appears in prose only when the stored tail is positive. (The 9 Oct 30-year: a 7% dealer take and — per GPT's reading — a tail; both are facts, and the sentence should carry both: demand was there, at a concession.)

**1.5 Prediction-market contract record.** The `pm_rest` writer stores bid, ask, mid, last, volume or liquidity, `retrieved_at`, and the resolution-rule text or URL. The report prints the mid; for a meeting's legs it prints the raw sum ("legs sum 108%") and the normalised probabilities side by side; cross-venue disagreement uses mids; a leg whose spread exceeds a config threshold is marked illiquid. A rule renamed: the "outside 10–90% is mispriced" check becomes the "favourite–longshot check" and reads as a flag, not a verdict.

**1.6 Coincidence, not causation.** The daily table is headed "events alongside the session". The read frame's instruction: state coincidence, never cause — allowed connectors are "alongside", "coincided with", "the same session as". The bare-delta/motive gate's banned list adds "because", "on the back of", "in response to", "reacting to" for the model's own voice. Quoted text is exempt from the motive-word check (the Lane case: a quoted official's "driven by" is attribution, not inference).

**1.7 "Unvalidated" tags.** Dealer flags (pinned/held/amplified), the gamma regime, exception tiers and every other descriptive classification carry "(descriptive; unvalidated, n=0)" in the glossary and one footnote per section; n is the count of scorecard-graded instances once the scorecard grades them.

**Acceptance.** The Weekly dry run on the 9 Oct data passes the new gate; the notes file lists every discrepancy found in that edition with its explanation — at minimum the six GPT tabled (SPY return, exception age/status, the z-score window versus the week's move, mixed 7/8/9 Oct dates, the Bitcoin bar, the 108% legs). CI green. **Estimate ≈ 12 h** (8 h + item 1.0). Merge: see §8 ruling 3.

## 3. Tranche 2 — storyline (W-1.2; spec after dry run #4; build next week)

**2.1 The précis, written last.** A second pass: after the ten section commentaries exist, a précis frame reads all ten and writes (a) the one tension of the week and the evidence on each side; (b) a verdict by asset — equities, rates, credit, dollar, commodities — each one of up / down / chop / transition; (c) a confidence line naming the evidence that drives it; (d) "what would change our mind": three or four observables due within the week; (e) what changed in the *outlook* since last week, distinct from what changed in the data. The précis is the only prose that may cite figures from more than one section.

**2.2 The stance line, pre-registered.** The equity verdict becomes a graded call: direction of SPY's close at the next Weekly versus this one, with a probability, written to the scorecard's pre-registration ledger at publication, graded by Brier like the base-rate calls, and printed with "n=k, unvalidated" until k is meaningful. The day layer (DTH-1) reads this line and never produces its own regime.

**2.3 The relevance sentence.** Every section commentary opens with one sentence tying it to the précis ("Positioning: the crowd is on the same side as the index, which is why the breadth story matters").

**2.4 Contradiction status lines.** Each open contradiction in §4 carries one of: *resolved by* (and which section holds the evidence), *carried* (and what resolves it), *stale*. (The 9 Oct HY tension was resolved by §5's CCC/BB decomposition — the equity market reads the index spread, the long bond reads the bottom tier — and the edition should have said so.)

**2.5 The book's stance with terms.** §10 ends with: what the regime band permits, what the book is positioned for, and the three observables that would make its caution wrong.

**2.6 Collapse by default, expand in reference.** Silent and unreachable voices → one line in the read path, rows in reference. Resolved prediction-market legs (the 18 Core CPI rows) → one line: "Core CPI m/m modal 0.2% (p), y/y modal 2.5% (p)". Exceptions that restate a five-year extreme already in the tape → one line each. The terms box from the storyline rewrite becomes the edition's page-2 box.

**2.7 Tape and mechanics de-duplicated.** The tape is *where we are* (levels, trend, distance from levels, breadth); mechanics is *how we got there* (dealer hedging, realised vs implied, the daily path). The daily table lives in one of them, not both.

**2.8 Presentation.** Six-panel small multiples: one-line titles, the subtitle to the caption. Each table row carries its unit. The close/Weekly tape frame keeps ≤ 3 named levels (T3.4b's rule) within the cap.

**Open until dry run #4:** whether 2.1 is a second model pass over the ten commentaries (recommended) or a single frame over the ten payloads; the verdict asset list (the five above, or add volatility); 2.2's horizon (one week, recommended). **Estimate ≈ 12 h.**

## 4. Tranche 3 — descriptive analytics (W-1.3; after tranche 2)

**3.1 Narratives.** Each ledger item carries a source class (official / data / sell-side / press) and an event-cluster id; the count shown is by cluster ("4 clusters for, 0 against"), never by item. A steelman row per narrative that the scan must fill from an active search for the counter-case or mark "none found after search" with the queries used. A status column: long-term theme / catalysed / priced / tradeable. Unreachable sources show the date last scanned and whether any active thesis depends on them. The item's excerpt is stored with the label.

**3.2 Exceptions.** Three tiers — potential leading indicator / contemporaneous contradiction / extreme without a trade — printed as the table's grouping and order. Every series carries a level / change / extreme label. Each exception carries resolution path, catalyst and invalidation (descriptive fields; forward-outcome statistics are §6).

**3.3 Positioning.** The §10A standard extended to the Weekly: disaggregated TFF categories (leveraged funds, asset managers, dealers), % of open interest, ETF share counts. A positioning-change score: the four-week change in each position as a z against two years, beside the level z. Sentiment rows below a config sample threshold print "thin sample (n=3)" and are excluded from any composite. TIC and other lagged flows print their reference month and release date.

**3.4 What's priced.** An event × venue matrix for the top events (fed-funds futures / Kalshi / Polymarket / economist consensus where a feed exists) with a disagreement column; the cross-venue threshold applies per row.

**3.5 Ahead.** The one top-importance event of the week gets a playbook: hot / in-line / cool outcomes × transmission channels (yields, dollar, equities, vol) × the positioning that would amplify each, drawn from scenario set #1's transmission columns. The unlisted routine releases stay unlisted.

**3.6 The book.** A productivity line beside the compliance line: triggers fired → reviewed → packets drafted → approved. A passed-over row for every reviewed signal with no packet, with the reason. The decisions count is captioned as register decisions; chat rulings on briefs are not book decisions and are not counted.

**3.7 Glossary and appendix.** A definitions-version stamp (the config's git short hash) on the glossary; a technical appendix in the reference tier for formulas, units, sign conventions and the GEX/DEX universe and expiry coverage; descriptive classifications and validated signals kept visibly distinct.

**Estimate ≈ 14 h.** Rough total for W-1 ≈ 38 h.

## 5. Calendar (Workplan v6 §4, amended)

| Night | Session A | Note |
|---|---|---|
| Sun 11 → Mon 12 | **W-1.1 first** (incl. 1.0, ≈ 12 h); then the store-wide move screen + the EM screen queued | both branch-only; W-1.1 goes first so CI and the operator's read fit before Monday's merge; its notes file lists the 9 Oct discrepancies |
| Mon 12 → Tue 13 | SR-36; **then W-1.2 queued** (spec from Monday's rulings) | before the Tue 23:30 freeze — branches continue through it |
| Tue 13 → Wed 14 | SR-43/49; **then W-1.3 queued** | |
| Wed 14 → Thu 15 | SR-37/38 | slides to the week of 19 Oct if A's nights overrun |

Session B's nights are unchanged (AQ-2 part 2; AQ-3 parts 1 and 2 — AQ-3 part 2 adds the 10-year Bund, the OAT–Bund spread, 10-year gilts and the US–JGB spread; the EM paper). Merges: W-1.1 per §8 ruling 3; W-1.2 and W-1.3 on Fri 16 after the sitting confirms, in that order, after the AQ branches. The Weekly of Sun 18 Oct is the first with W-1.1; Sun 25 Oct the first with the storyline, the correlation line and Book B candidates.

## 6. Deferred — for the Audit #4 agenda and the evidence tracks

- Probabilities and confidence on the trend regime per index and horizon — after the scorecard's base rates (mid-November); the call itself starts now (2.2).
- Forward-outcome tables per single-series exception (returns, vol, drawdown at 1/5/20/60 sessions after comparable readings) — computable from the store's five-year history; Category 2 after Audit #4. Not for gap z-scores (history too short).
- Brier against market-implied and base-rate baselines; calibration by probability bucket; log loss — into the scorecard design.
- A surprise calculator (actual vs consensus / historical forecast error) — needs an economist-consensus feed we do not have; logged as a data gap.
- Performance decomposition (by strategy, exposure vs selection, by regime; benchmark matched to risk) — after Book B has a track record.
- Per-underlying GEX/DEX (SPY, QQQ, IWM, index options separately) and morning-setup vs end-of-day classification — the 6b brief, week of 19 Oct.
- The packet template carries thesis, catalyst, consensus, edge, entry, invalidation, payoff, sizing, horizon, evaluation — Doctrine #2 confirms or amends.
- Validation of every descriptive signal (frequency, hit rate, forward return, time to resolution, by regime, after costs, false positives) — the scorecard track, point-in-time, as the sample accrues.

## 7. Declined

- *The Weekly determines whether an observation is an opportunity.* The architecture separates observations (reports) from recommendations (packets, the sitting, Book B). The Weekly carries a stance with terms (2.2, 2.5), not setups; setups are Book B's candidate list.
- *Prioritise in the summary instead of capping figures.* The cap is on the frame's input and forces selection; the précis prioritises. Both stay. What GPT saw — withheld commentary and audit messages in the report — is the bug T3.4 fixed.
- *Remove the 10–90% rule.* Renamed (1.5), not removed: prediction markets do overprice longshots and underprice favourites; the rule is a flag.
- *A unified regime model that scores daily, weekly and monthly direction now.* The macro regime exists (the Doctrine's quadrant and band); the trend verdict starts as a descriptive, pre-registered call; probabilities wait for grading. Built early, a regime model manufactures the confidence GPT warns against.

## 8. Needs you (five rulings; one at a time in chat)

1. **Gate severity (1.1).** Within rounding tolerance: print the canonical value and log. Beyond tolerance: fail the run. — **Yes — 11 Oct 2026.**
2. **Stale versus lagged (1.2).** Price series older than the edition date print "stale since"; series with a config `expected_lag` print "lag: <period> (<reference>, released <date>)". — **Yes — 11 Oct 2026.**
3. **W-1.1 merge timing.** Monday 12 Oct evening, inside the window, after CI green and my read of the notes file — before the Tuesday freeze, so the Weekly of 18 Oct carries it. (It is a defect fix, like T3.x, not a sitting-placed item.) — **Yes — 11 Oct 2026.**
4. **Calendar (§5).** W-1.2 and W-1.3 as session A's second queued pastes on Mon→Tue and Tue→Wed; SR-37/38 slides a week if needed. — **Yes — 11 Oct 2026.**
5. **The stance call (2.2).** Horizon one week (to the next Weekly); the probability is on SPY's direction; graded by Brier in the scorecard ledger. — **Yes — 11 Oct 2026.**
