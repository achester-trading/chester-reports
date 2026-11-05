# Doctrine #2 — 7–8 November 2026 — minutes (template)

**Template, written 2 Nov 2026 by session B (B120). It holds no ruling.** The session that writes the minutes fills the blank columns from the sitting, one row per decision, in the agenda's order (`docs/briefs/doctrine-2-sitting-2026-11-agenda.md`). "Recommendation" quotes the pack (`docs/briefs/doctrine-2-pack-2026-11.md`), whose rows in Parts 9 and 12 are options only. "Releases" quotes the pack's Part 11 or Part 12 where it names a build; "—" where it names none.

Sitting held in chat from ____ (Sat 7 Nov) and ____ (Sun 8 Nov, not before 06:00 ET). Each ruling is the operator's; the record here is what a session applies.

## Block 1. The decisions that release builds

Block accept-all: ____ (time, and the operator's words)

| # | Title | The pack's recommendation | Ruling | The operator's words | Releases | Date |
|---|---|---|---|---|---|---|
| D2-73 | The price-source migration: the plan and the deadline | options only (Part 9): (a) confirm D38's acceptance of b68's ten decisions as the plan: IBKR daily bars primary, Massive for the S&P members and corporate actions; a $60 a month ceiling; DTWEXBGS with its lag labelled; the uncovered keys (^MOVE, the foreign cash indices, ^SET.BK, consensus, the earnings calendar's forward dates) listed gaps; retirement **Fri 8 Jan 2027**; (b) a 22 Dec 2026 deadline; (c) no deadline, family by family | | | Part 11: "Releases the gateway and Massive writers and 98(c). The deadline is 8 Jan" | |
| D2-74 | The Cboe readers: `cboe_indices` (COR1M, COR3M, DSPX) and the VX-curve logger | options only (Part 9): (a) freeze, retire or licence; (b) freeze, retire before 23 Dec with the dual run ended in a v1.13 note, or licence; (c) purge after a backup, or keep frozen; (d) Yahoo's ^VIX and ^VIX3M (the vol dial and the published VIX3M/VIX leg) follow D33's ruling; FRED's VIXCLS, VXVCLS and VXNCLS as the substitute of record (nothing reads VXVCLS today); the VX1-VIX basis a listed gap (D45); the dispersion panel's Yahoo fallback (^DSPX from May 2024; ^COR1M and ^COR3M quotes without history), unused while held; (e) re-point to `yfinance.mkt_dspx`, or void; (f) ask, or not; (g) end at 23 Dec as planned, or end now | | | Part 11: "Lifts or keeps the hold" (`b95-cboe-held`) | |
| D2-75 | The 23-hour equity session's three adjustments (item 98) | options only (Part 9): (i) released by this sitting, in the order's work order: 98(c) inside the price migration (D2-73), then (a), then (b); (ii) held for Audit #5's placement of SR-68 | | | Part 11: "Releases 98(a)–(c) or leaves them to Audit #5" | |
| D2-79 | Whether D41 closes D2-45 (W-1, the DTH-1 scope) | options only (Part 9): (a) record D2-45 as closed by D41; (b) rule D2-45 as drafted where D41's brief did not settle it. The pack cannot quote the brief | | | Part 11: "The Book B scanner's daily candidates wait on it" | |
| D2-80 | The SR numbering collision (amends D2-22) | options only (Part 9): (a) items 45–78 take SR-77 onward; (b) the batches' provisional rows renumber after items 45–78; (c) both wait for Audit #5, which places every provisional row | | | Part 11: "Audit #5 numbers by them" | |
| D2-81 | `alignment_weekly`'s split: the hit definition | options only (Part 9): (a) as built: a positive return in the decision's direction, over all graded statuses; (b) ruled R > 0 over taken decisions, as the scoreboard reads | | | Part 11: "The stamp's build" | |
| D2-76 | Paper XXXI's roll-up tiers | options only (Part 9): (a) record D48 (the memo's decision 7: count fired mechanism families; CLEAR 0–1, WATCH 2, ALERT 3+) as confirmed; (b) reopen | | | — | |
| D2-82 | A66's capex-guidance extraction rules | options only (Part 9): (a) ratify with D2-4's block; (b) amend | | | — | |
| D2-83 | The Reporting System paper, Drafts 3 and 4 | options only (Part 9): (a) accept Draft 4 as drafted, Draft 3 superseded; (b) review first | | | — | |
| D2-85 | The X layer's cadence under the operator's Grok plan | options only (Part 12): (a) a plan change for a third slot: the evening run first, the midday run only if a fourth is cheap; (b) swap: the 06:15 equity-vol run becomes the evening run (the eqmacro attention ledger and the ES card's X read lose their morning input); (c) hold at two until item 50's decision point, and judge the pilot on the morning runs alone; note: The morning window (about 10:00 UTC the day before, up to the run) already covers the previous evening's after-hours posts. The evening run's value is same-day timing, not coverage (the B104 paste) | | | Part 11: "D2-85 before any X-layer build" | |
| D2-91 | Item 50, the X pilot, at its decision point | options only (Part 12): (a) **continue** to Audit #5 as a pilot, the evening run added only if a third Grok slot exists (D2-85), the rumour ledger kept as the base-rate record. Cost: one morning run a day (about 10 minutes), the two Grok slots as now, a third only for the evening run. (b) **promote**: the rumour ledger becomes a registered base-rate source (a read-only row in the register; rights unchanged, attention and rumour tracking only), the evening-note block (item 115) built after the sitting, and the morning triage shortened to the principals, the rumours and the checkable claims, the attention statistics dropped until the ledgers are whole. Cost: the morning run, shorter; the two slots; the evening block's input needs a third slot or D2-85's swap; one build after the sitting. (c) **stop** the pilot and keep the ledgers as a dated record. Cost: none going forward; the two slots and the morning run freed; note: Options only; no recommendation beyond the rule-31 form. Taken with D2-85, whose option (c) waits on this decision point | | | — | |
| D2-86 | The readers' findings as a standing loop | options only (Part 12): (a) standing, with the findings file as the Audit's input and the comparisons folded into the existing frame checks; (b) standing, with a new consistency gate; (c) one-off, closed when A95 and A103 merge; note: A95's paste already sends a comparison with no gate to "the Monthly's own consistency check … rather than a new gate" | | | Part 11: "D2-86 before Audit #5's agenda" | |

## Block 2. Values and structure (Parts 1 and 2)

Block accept-all: ____ (time, and the operator's words)

| # | Title | The pack's recommendation | Ruling | The operator's words | Releases | Date |
|---|---|---|---|---|---|---|
| D2-1 | The five sets confirmed in chat on 24 Oct (Table 1.1) | **Ratify as a block.** | | | — | |
| D2-2 | B51's publication-lag table (12 families; D4) and the lag families added since (Table 1.2) | **Ratify as a block**, including chain-5's two added families, which D4's "as set" may not have covered. | | | — | |
| D2-3 | The sets confirmed earlier in October (Table 1.3) | **Ratify as a block.** | | | — | |
| D2-4 | The session-set values no ruling covers (Table 1.4, by file) | **Ratify as starting values, as a block.** Each is reviewed at Audit #5 against its first month; a value a ledger needs changed comes back as one line. | | | — | |
| D2-5 | The reading budgets (D19/D20; old W-6) | **Ratify as set.** | | | — | |
| D2-6 | The secondary notes' word caps (B60) | **Make them targets.** Keep the runaway character ceilings (2,000 / 1,200 / 3,200) as the one guard that withholds, since that guard is about a runaway reply, not length. | | | — | |
| D2-7 | The 07:00 anchor's caps (B60) | **Make the signal lines a target.** The crypto daily part stays off. | | | — | |
| D2-8 | B60's word equivalents and guards | **Ratify as set.** | | | — | |
| D2-9 | The Weekly's structure since 2 Oct (Table 2.1) | **Ratify as built.** | | | — | |
| D2-10 | The Weekly's chart set and the Monthly's chart cap (old W-4) | **Ratify as set.** | | | — | |

## Block 3. The standing rules (Part 3)

Block accept-all: ____ (time, and the operator's words)

| # | Title | The pack's recommendation | Ruling | The operator's words | Releases | Date |
|---|---|---|---|---|---|---|
| D2-11 | The outlet rule for voices (D5) | **Standing**, into the Doctrine's sources section. | | | — | |
| D2-12 | X-only accounts batched monthly (D6) | **Standing.** | | | — | |
| D2-13 | The 16 Oct sources rule and the refusals declared since (Table 3.1) | **Standing, with the refusals ratified as listed gaps.** A refused source is re-checked only by a session told to, never by a retry. | | | — | |
| D2-14 | A lag is documented, never guessed (b51; D29.5) | **Standing**, in those words. | | | — | |
| D2-15 | The lab ledger reads filings only (D21) | **Standing**, extended to every company-financials line. A66's capex guidance is built to it already. | | | — | |
| D2-16 | Budgets are targets (D20) | **Standing for reading budgets.** The attention budget stays a rule (Part 6). | | | — | |
| D2-17 | Decision sets come as one list (STANDING, 24 Oct) | **Standing**, into the Doctrine's governance section. | | | — | |

## Block 4. Regime and calibration (Part 4)

Block accept-all: ____ (time, and the operator's words)

| # | Title | The pack's recommendation | Ruling | The operator's words | Releases | Date |
|---|---|---|---|---|---|---|
| D2-18 | The `calc.infl_vol` bridge question (D3), beside SR-9's 5.25% note (D2-37) | **No bridge.** It stays unwritten and prints its reason until the window clears. A bridged print would be a guess entering a volatility series. | | | — | |
| D2-19 | 6f's twelve rulings (D27), for the record (Table 4.1) | **Record them in the Doctrine's regime section**, with the three dimensions that wait and what each waits for. | | | — | |
| D2-20 | What the first calibration read will show | **Note that nothing prints a transition probability yet**, and the Doctrine reads none until a row calibrates. | | | — | |
| D2-21 | `alignment_weekly`'s floor (A65) | **Keep the floor as built.** An uncalibrated read is a stamp nobody can grade. | | | Part 11, with D2-81: "The stamp's build" | |

## Block 5. The register (Part 5)

Block accept-all: ____ (time, and the operator's words)

| # | Title | The pack's recommendation | Ruling | The operator's words | Releases | Date |
|---|---|---|---|---|---|---|
| D2-22 | SR numbers for items 45 to 78 (Table 5.1) | **Assign as drafted.** | | | Part 11, with D2-80: "Audit #5 numbers by them" | |
| D2-23 | The unnumbered items before 45 (Batch 4's S-2 to S-5 and its working SR-37…49 bar 43, 45, 46; Batch 5's items 16–29; Batch 6's 30–44) | **They take SR-94 onward at Audit #5, after their own reconciliation.** Their working numbers are in code, and numerals are accession IDs, not reading order. Batch 4's working "SR-48" (diesel) is retired as a number because the register's SR-48 is GTM-1. | | | Part 11, with D2-80: "Audit #5 numbers by them" | |
| D2-24 | Do amendments take their own number? (items 53–58, 60, 67, 68, 76, 78) | **Each takes its own number**, naming the entry it amends ("one record per proposal"). | | | Part 11, with D2-80: "Audit #5 numbers by them" | |
| D2-25 | The pending rule-31 ledger lines (Table 5.2) | **Accept as a block.** D9's four first verdicts are already accepted and are listed for the record. | | | Part 11, with D2-80: "Audit #5 numbers by them" | |

## Block 6. The attention budget (Part 6)

Block accept-all: ____ (time, and the operator's words)

| # | Title | The pack's recommendation | Ruling | The operator's words | Releases | Date |
|---|---|---|---|---|---|---|
| D2-26 | The attention budget for the November build phase (R-6; minutes item 4) | **Re-ratify both as rules, not targets.** Add that a notes file carries at most five needs-you (practice since A58) and that decisions reach the operator as one list a day at most. | | | — | |
| D2-27 | The third count's cap (old W-3: rulings taken in chat) | **Five decision lists a week.** Past five, the next list queues to the following week, and a breach prints as a rule break. | | | — | |
| D2-28 | The attention log's gap | **A session backfills 9–23 Oct from the notes files**, and every chat ruling round is logged from now on. | | | — | |

## Block 7. The calendar (Part 7)

Block accept-all: ____ (time, and the operator's words)

| # | Title | The pack's recommendation | Ruling | The operator's words | Releases | Date |
|---|---|---|---|---|---|---|
| D2-29 | The dated items (Table 7.1) | **Confirm**, with the two undated items (the cloud-session move; the wider options universe revisit) taken at Audit #5. | | | — | |
| D2-30 | The Monthly of 1 Dec and its first Digital Assets chapter (ST-R6.51c) | **Order a build slot for the week of 9 Nov**, after the 6f tranches. | | | — | |
| D2-31 | The December vendor month's start (FlashAlpha beside SpotGamma) | **Start Tue 1 Dec**, judged in the January Monthly. | | | — | |

## Block 8. Part 12's decisions and D2-90

Block accept-all: ____ (time, and the operator's words)

| # | Title | The pack's recommendation | Ruling | The operator's words | Releases | Date |
|---|---|---|---|---|---|---|
| D2-84 | The readable editions' contract | options only (Part 12): (a) ratify as written; (b) ratify, with the Letters' word budget made a configured target like the editions'; (c) hold until three Monthly Letters exist; note: The Reporting System paper's Appendix F (B103, on b102) records the reading order as superseding §10.3; the body keeps its text | | | — | |
| D2-87 | The MSTR/MSCI post-effective read | options only (Part 12): (a) a one-shot task for 1 Dec 07:10, with the December clause lifted for that date; (b) fold the read into the 2 Dec morning triage; (c) drop it, so the watch ends 30 Nov; note: The order's F5 drafted (a) for late November | | | — | |
| D2-88 | The ES cards and the Sunday map in the register | options only (Part 12): (a) keep the rows and the archive (as ruled); (b) keep the rows, no archive; (c) move the rows to a private note outside the repo; note: D50 and D54 are the rulings that option (a) restates | | | — | |
| D2-89 | The Monthly's first-edition withholds as an incident | options only (Part 12): (a) an incident, with the lesson "the writer's data block must carry every scaled figure's display string and series name before the audit binds"; (b) not an incident: the audit worked as designed; (c) an incident only if the 1 Dec edition withholds more than three; note: Appendix F.1 records the run and A95's disposition, and says the audit held. It does not rule the question | | | — | |
| D2-90 | The EM shock screen's amendment (filed 105(a), Batch 19) | options only (Part 12): (a)(i) a member's \|z1\| at or past a bar (drafted: 4) opens its country's shock that session; (a)(ii) every flagged country on a mixed session opens one; (a)(iii) the dating as built; separately, past sessions classified as of their own close; (b) the central bank's daily PTAX rate as a candidate FX source for the 16 Oct check (A96's switch), FRED's H.10 the reference until then; (c) the policy rate and a DI-pre tenor from the same service as a listed gap with a named candidate; (d) report-only confirmed; note: B105's notes recommend (a)(i) at 4 with the as-of-close fix, (b) and (c) as candidates for the check, and (d). Those are drafts; the sitting rules | | | Part 12: "nothing is built or fetched before the sitting rules" (B105's amendment) | |

## Block 9. The items carried from the 20 Oct pack (Part 8), and Part 9's records

Block accept-all: ____ (time, and the operator's words)

| # | Title | The pack's recommendation | Ruling | The operator's words | Releases | Date |
|---|---|---|---|---|---|---|
| D2-32 | V-1 the volatile-day flag's actions | Apply in full from the day Gate C passes, enforced at the order gate where it can be; until then printed, never applied. | | | Part 11: "Gate C's build list depends on them" | |
| D2-33 | V-2 the flag's stamp | The full stamp (three dials and the flag) is on packets at entry since B49 and chain-4; **record as done.** | | | — | |
| D2-34 | V-3 the flag's three session-set values (`min_atr_sessions` 15; `index_movers` = `earnings_mega`; the earnings window) | Confirm as starting values. **Corrected:** the 20 Oct text says "two" and lists three. *Block D2-4.* | | | — | |
| D2-35 | R-1 SR-1's rights | (b): the flag word, and Book B's pair as `b_style_regime_pair` at the Card's minimum; hold the Book A tilt and SR-13's modifier. | | | Part 11: "Each changes what a book may do" | |
| D2-36 | H-1 SR-3's tail-register edits | Make the three edits as worded. *Block: reading rules.* | | | — | |
| D2-37 | H-2 SR-9's 5.25% note | Adopt as an unvalidated heuristic, never a threshold (the bridge question is D2-18). *Block: reading rules.* | | | — | |
| D2-38 | H-3 the projection rule (SR-18) | Add the sentence to the reading rules. *Block: reading rules.* | | | — | |
| D2-39 | H-4 the false-bottom rule (SR-8, Book A A-2) | Adopt sentences one and three; hold sentence two and A-2's re-entry until a second element discriminates. | | | Part 11: "Each changes what a book may do" | |
| D2-40 | H-5 the ETF record-low note (SR-22) | Adopt as a reading rule. *Block: reading rules.* | | | — | |
| D2-41 | B-1 marking open positions | Realised only, the figure withheld while a book holds an open decision; order the entry-fill write path before Gate C. | | | Part 11: "Gate C's build list depends on them" | |
| D2-42 | B-2 risk-adjusted and after-tax | Add P&L in R once B-1's entry fill exists; after-tax at the annual review. *Block: measurement.* | | | — | |
| D2-43 | B-3 long against short | Cut it in the Monthly's by-book table, short first. *Block: measurement.* | | | — | |
| D2-44 | B-4 the printing floor | `min_n` 10. *Block: measurement.* | | | — | |
| D2-45 | W-1 the DTH-1 scope | The dealer-positioning / 0DTE engine as the default first engine, held until the scorecard has 20 scored sessions; release the Book B scanner's daily candidates now. | | | Part 11, with D2-79: "The Book B scanner's daily candidates wait on it" | |
| D2-46 | W-2 the Category 2 triggers | Confirm as listed; review at Audit #5. *Block: deferrals.* | | | — | |
| D2-47 | W-5 the triggers that fired too often or never | Recalibrate from the October counts at the sitting, one line each. | | | — | |
| D2-48 | T8-1 the Daily Cascade's eight reports | Rename to the five as-built touches. *Block: renames.* | | | — | |
| D2-49 | T8-2 the 0700 setup list | The close's dealer-block proposals, re-read at 07:00, are the list. | | | Part 11: "Gate C's build list depends on them" | |
| D2-50 | T8-3 the 1000 report | It becomes "the 09:50 open note"; confirm or cancel, never add. | | | Part 11: "Gate C's build list depends on them" | |
| D2-51 | T8-4 the weekly reflection report | Rename to "the Weekly (Sunday 05:00)". *Block: renames.* | | | — | |
| D2-52 | T8-5 the Weekly's top | Accept b48's top; print heat and net exposure from `heat.view()`; move the rule-break count up. *Block: measurement.* | | | — | |
| D2-53 | T8-6 Top & Bottom | Keep the text, mark dormant. *Block: dormant.* | | | — | |
| D2-54 | T8-7 Alternative Asset | Rename to the Quarterly and the Monthly's slow layers. *Block: renames.* | | | — | |
| D2-55 | T8-8 Monthly Macro and "Part 16" | Rename; the tail scan in the slow layers. *Block: renames.* | | | — | |
| D2-56 | T8-9 Disruptive Themes | Mark dormant. *Block: dormant.* | | | — | |
| D2-57 | T8-10 Book D's alert layer | Rename to the as-built sources; the overhang tracker dormant. *Blocks: renames, dormant.* | | | — | |
| D2-58 | T8-11 the exceptional tier and Phase 2 | The phase is the operator's ruling; Phase 1 current; the tier closed. | | | Part 11: "Gate C's build list depends on them" | |
| D2-59 | T8-12 the benchmarks | Accept as built: Book A alone and the 60/40. *Block: measurement.* | | | — | |
| D2-60 | T8-13 the 13-week expectancy | Accept with `min_n` 10; 30 and 50 stay the change thresholds. *Block: measurement.* | | | — | |
| D2-61 | T8-14 the Weekly's three counts | Record as matching; the third's cap is D2-27. *Block: measurement.* | | | — | |
| D2-62 | T8-15 the intraday rung's first engine | Keep engine 7 and the rung apart. | | | Part 11: "Gate C's build list depends on them" | |
| D2-63 | T8-16 the mandatory 1000 touch | Stands as 6.5 words it, for the open note, once Book C is active. | | | Part 11: "Gate C's build list depends on them" | |
| D2-64 | T8-17 the 1000 report as a Book D touch | Drop it for now; revisit at Gate C. | | | Part 11: "Gate C's build list depends on them" | |
| D2-65 | O-1 the first alternative-asset theses (1Q27) | Seed at the sitting, measurables only, under AQ-6's procedure. | | | Part 11: "Measurables only, under AQ-6's procedure" (the 1Q27 theses) | |
| D2-66 | O-2 the EM resolution criteria | Yes. | | | — | |
| D2-67 | O-3 the crypto basket in Book A | A measured series with no band until a quarter of the Quarterly has read it. | | | — | |
| D2-68 | O-4 the "and climbing" leg | Order the v1.13 bump: the climb over the vol dimension's own window. | | | Part 11, with D2-74: "One bump can carry the dual run's end and the \"and climbing\" leg" | |
| D2-69 | O-5 the packet template | Confirm, adding the regime stamp and Book C's 1000-report confirmation status. | | | Part 11: "Gate C's build list depends on them" | |
| D2-70 | O-6 the Alpha Lab's place | A research book beside the four, reporting monthly, with no right over a book. | | | — | |
| D2-71 | O-7 the dealer engine's later enhancements | Defer to Audit #5. *Block: deferrals.* | | | — | |
| D2-72 | S-1 the fifteen setup stubs and the kill criterion | Accept Annex B's drafts; the kill rule for B, C and D as written; `d_tail_hedge` judged on its budget; Book A's two at the four-quarter review. | | | — | |
| D2-77 | The Weekly readability order (W10-1 to W10-3) | options only (Part 9): For the record. Built by A97 for the 8 Nov Weekly | | | — | |
| D2-78 | The Phase 4 paper engine | options only (Part 9): For the record: D43 (a)–(f), no live orders before 2027; D44, Pillar 5H from EDGAR 13F, Tranche B | | | — | |

## New rulings taken at the sitting

**The numbering.**
- `docs/briefs/rulings-2026-10-28-31.md` (on `b95-batch-21-filing`) ends at **D48**.
- The 1 Nov order (`docs/change-order-readable-editions-2026-11-01.md`, on `b102-readable-editions-register`) rules **D50 to D56** and names **D57** as proposed.
- **D49** is on no branch: a gap to be recorded or explained.
- New rulings here continue from D57: **the first is D58**.

| D | Ruling | The operator's words | Applied by | Date |
|---|---|---|---|---|
| D58 | | | | |
| | | | | |

## Incidents to log

| INC | What happened | Lesson (for the Doctrine's dated appendix; no figures in a lesson entry) | Date |
|---|---|---|---|
| | | | |

## The next sitting

Date: ____ (the pack's calendar, Part 7, and D2-29 decide it).
