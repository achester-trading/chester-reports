# Change order — Signal-triage round 6, Part 2 (items 46–48)

**File:** `docs/change-order-signal-triage-batch-7-2026-10-16.md`
**Status:** RULED 2026-10-16 in chat; **FILED 2026-10-16** by the filing chat (13:45 ET). Commits on `docs-batch-7` from main, after Batch 6.
**Encoding:** Batch 7 of Post-Freeze Amendment #4. Round 6 Part 1 (item 45, delivered 15 Oct) was folded into Batch 6 at filing (`docs/change-order-signal-triage-batch-6-2026-10-15.md`, items 30–45), so there was no separate Batch 7 to fold into; this file is round 6 Part 2 and takes the next batch number. Decided by the filing chat, 16 Oct 2026.
**Precedence:** below Part 26 and the 25 Sep integrated signal-triage order; follows its integration rules (R28 sub-states, Track D preconditions, validation gates as offline calibration studies with dated ledgers). Item 48 is also an amendment to the 1 Oct metric-lenses brief (`docs/briefs/metric-lenses-brief-2026-10-01.md`) and is built in or after 6e.

---

## 1. Purpose and scope

Two third-party posts and one operator design question, triaged 16 Oct 2026 and ruled in chat. Items 46 and 47 follow the standard entry form. Item 48 is a brief-style entry: a set of decomposition lenses for the four main macro releases, arising from the operator's question after item 46.

Nothing here changes the frozen architecture. Rights: flags, narrative-register entries, by-hand lines, report panels. No composite weights change.

## 2. Entries

### 46 · September CPI: energy shock or broad acceleration? (Charles-Henry Monchau, Syz; Schwab/BLS chart)

**Source.** Monchau (credible voice, in register); Schwab chart of BLS data as of 30 Sep 2026.
**Read.** Headline CPI +0.6% m/m; gasoline +9.1% is roughly half of it; fuel oil +15.3%, airline fares +1.2%; rent +0.2%, OER +0.3%; dairy, meat and medical goods fell. Monchau: an energy shock, not broad acceleration; the question is pass-through into airfares, shipping and business prices; the Fed faces a hard October call with hiring slowing.
**Thought process.** The live test of item 32's supply-shock sub-state: a shock that stays in energy is contained, one that spreads is the 1970s pattern GS shaded. It also sets Monchau against Budaghyan (item 35), who reads inflation as broader than core because corporate prices run near 5%. Both are measurable. Median and trimmed-mean CPI (Cleveland Fed) show whether the middle of the distribution is moving; a diffusion measure shows how many categories run hot; a pass-through basket (airline fares, transportation services, truck-freight PPI) shows whether energy is leaking with its usual one-to-three-month lag.
**Stack today.** Headline and core prints; item 35's corporate-price gap; no component decomposition or pass-through read.
**Ruling.** Monthly CPI decomposition panel: contributions from energy, food, core goods, shelter and core services ex-shelter; Cleveland Fed median and 16% trimmed-mean CPI; diffusion (share of categories above 4% annualised m/m). Pass-through flag: the energy-sensitive basket accelerating within three months of an energy spike switches item 32's sub-state from "supply shock, contained" to "supply shock, propagating." Narrative-register disagreement pair — Monchau (energy, contained) vs Budaghyan (broad) — adjudicated monthly by median CPI and diffusion. Scenario line for the Warsh matrix: energy shock with a softening labour market.
**Rights.** Flag only.
**Placement.** Plumbing & rates, inflation block; full panel in the Monthly; one-line read in the daily close on CPI day.
**Work.** ST-R6.46a decomposition panel (BLS API, Cleveland Fed) — 3h. ST-R6.46b pass-through basket and flag — 2h. Disagreement pair and matrix line — by hand 0.25h.

### 47 · The collapse in AI cost (Linus Ekenstam chart, via Monchau)

**Source.** Ekenstam (aggregator; chart unsourced, benchmark undefined — Monchau's own caveat); Monchau's commentary.
**Read.** AI cost shown falling roughly a million-fold over 2021–26, "54 times faster than electricity," against compute (1940–2001), DNA sequencing and lithium batteries. Monchau: cheaper intelligence expands demand; it helps users and squeezes providers whose products become interchangeable; exploding usage does not mean expanding profits.
**Thought process.** The chart's numbers are unusable, but the mechanism is central to Factor I. Provider revenue is price per unit times volume. If price falls faster than volume grows, revenue stalls while the capex Factor I tracks keeps rising — the AI-bubble mechanism in one line. If volume grows faster (the Jevons case), the capex is justified. Both sides are measurable from public sources: constant-capability inference cost (Epoch AI, Artificial Analysis), token-volume disclosures and OpenRouter's public statistics, AI revenue lines in hyperscaler earnings.
**Stack today.** Factor I has capex vs revenue and, from this round, the real-economy and dependency lines (22, 23, 26); no unit-economics line.
**Ruling.** "AI unit economics" line in Factor I, quarterly by hand: constant-capability inference cost (Epoch AI primary), token-volume proxy, implied provider revenue (price × volume) set against the capex series, with a Jevons test (volume growth vs price decline) as the one-line read. Carried into the next Disruptive Themes refresh brief beside items 22, 23 and 26; linked to Amendment #3's AI-capability workstream. Ekenstam chart not used; Epoch AI added as a source.
**Rights.** None until the DT refresh rules.
**Placement.** Factor I (DT refresh brief); slow layers.
**Work.** By hand — 1.5h first build, 0.5h/quarter.

### 48 · Macro release decomposition lenses — employment, CPI, PPI, GDP (operator design question) — AMENDMENT to the metric-lenses brief of 1 Oct 2026

**Origin.** After item 46 the operator asked whether the other main releases warrant similar decomposition. Ruled as one brief rather than one item per release.
**Thought process.** The 1 Oct metric-lenses ruling treats each metric family on its own horizons; item 46 is the CPI lens. The macro releases each have a small set of decompositions that separate signal from noise — persistent from transitory, breadth from headline, first print from revision — and a few lenses apply to every release. The list below is the set that earns a place; everything else stays out.

**Lenses by release.**

*Employment (monthly report, JOLTS, claims)*
1. Cyclical core payrolls: private ex-healthcare, education and government.
2. Diffusion: BLS share of industries adding jobs, 1- and 3-month; flag below 50 for three months.
3. Revisions as a signal: two-month net revision and birth-death contribution; flag on persistent negative revisions.
4. Unemployment by flow: permanent job losers (flag on YoY rise), prime-age participation, Sahm rule; continuing vs initial claims (rising continuing with flat initial = hiring freeze).
5. Leading pieces: temp help, aggregate weekly hours index, JOLTS quits rate, openings-to-unemployed ratio.
6. Wages: ECI and Atlanta Fed wage tracker beside average hourly earnings, with the job-switcher premium.

*CPI (extends item 46)*
7. Shelter lead: BLS new-tenant rent index, Zillow and Apartment List rents, ~12-month lead on CPI shelter.
8. Supercore: core services ex-shelter, 3- and 6-month annualised.
9. Sticky vs flexible CPI (Atlanta Fed); goods vs services.
10. Base-effect ladder: the mechanical path of YoY over the next three months from the months dropping out.
11. CPI–PCE wedge, with the weight differences named.

*PPI*
12. Intermediate demand stages 1–4 as pipeline pressure leading final demand.
13. PCE-relevant components: portfolio-management fees, airfares, healthcare services.
14. Trade services separately (the margin proxy item 35 strips out).

*GDP (quarterly)*
15. Final sales to private domestic purchasers as the core; inventories, net exports and government shown separately, government as the fiscal impulse.
16. Investment split: AI-related (item 22), structures ex-data-center (item 23), residential (item 36).
17. GDI–GDP gap (statistical discrepancy) as a downturn tell.
18. NIPA corporate profits vs S&P EPS — macro-vs-micro earnings divergence, paired with item 35.
19. Real disposable income ex transfers, saving rate; consumption-by-income panel (GTM K-shape, already adopted).
20. Nowcast path: GDPNow and NY Fed nowcast evolution through the quarter, print read against it.

*Cross-cutting, applied to every release*
21. 3- and 6-month annualised beside YoY.
22. First-print vs revised: flags evaluate on the vintage available at the time (point-in-time store, `available_at`).
23. Surprise vs consensus, feeding item 25's quadrant monthly rather than quarterly; consensus source to be settled (Bloomberg paywalled; public calendars as fallback; SPF stays the quarterly anchor).
24. One "what moved the print" line per release in the daily close, in the item-46 voice.

**Ruling.** Adopt all 24 lenses as an amendment to the metric-lenses brief, built in or after 6e in two priority groups: Group A — employment (1–6) and CPI (7–11); Group B — PPI (12–14) and GDP (15–20); cross-cutting lenses (21–24) built with Group A. Flags as named in lenses 2, 3 and 4; all other lenses report-only. Panels print in the Monthly; the release-day daily close carries the one-line read and any flag change. Data: BLS, BEA, Atlanta, Cleveland, Dallas, Kansas City and New York Fed, Zillow and Apartment List — all free; consensus source open.
**Rights.** Flags in 2, 3, 4 only; otherwise report.
**Placement.** Plumbing & rates (inflation block), a new labour block, and the slow layers (GDP); daily close on release days.
**Work.** ST-R6.48a Group A — employment lenses — 6h. ST-R6.48b Group A — CPI lenses (beyond item 46) — 4h. ST-R6.48c cross-cutting (annualised rates, vintage handling, release-day read line) — 4h. ST-R6.48d Group B — PPI lenses — 3h. ST-R6.48e Group B — GDP lenses — 5h. ST-R6.48f surprise index once a consensus source is settled — 3h. **Total ≈ 25h.**

## 3. Cross-item notes

- 46 and 48 are one build: item 46's panel is CPI lenses 1–6 of the brief in effect; ST-R6.46a and ST-R6.48b share code.
- 47 joins 22, 23 and 26 as Factor I inputs for the next Disruptive Themes refresh; none scored before it.
- 46's pass-through flag is the switch on item 32's sub-state; 48's surprise lens (23) is the monthly feed to item 25's quadrant — both from round 5.
- Three narrative disagreement pairs now run on inflation: fiscal vs capital competition (26), more hikes vs market-does-the-tightening (42 vs 34), energy-contained vs broad (46 vs 35). The Monthly adjudicates each from its own measure.

## 4. Work order (provisional; the audit places it)

- **Now (rides 6e):** ST-R6.46a (3), ST-R6.46b (2), ST-R6.48a (6), ST-R6.48b (4), ST-R6.48c (4) — ~19h.
- **After Group A:** ST-R6.48d (3), ST-R6.48e (5) — 8h.
- **When a consensus source is settled:** ST-R6.48f (3).
- **By hand:** 47 unit-economics line (1.5h, then 0.5h/quarter); 46 disagreement pair and Warsh line (0.25h).
- **Total:** ≈30h of sessions plus ≈2h by hand.
- **1 Nov Monthly candidates:** 46 panel and the CPI lenses, if 6e's timing allows; employment lenses at the December Monthly.

## 5. Verify items

1. Free consensus source for the surprise lens (48.23).
2. BLS API coverage of the new-tenant rent index history (48.7).
3. Epoch AI's constant-capability cost series definition and update cadence (47).
4. Whether the Cleveland Fed median/trimmed-mean series are already among the 59 FRED pulls (46).

## 6. Register, voices and sources

**Register:** items 46–48 with round numbers; SR numbers at the next Doctrine sitting, after Batches 5 and 6. 48 also recorded as an amendment to the metric-lenses brief.
**Voices:** Monchau / Syz (credible, already in register); Ekenstam (aggregator).
**New sources:** Cleveland Fed median and trimmed-mean CPI; Atlanta Fed sticky/flexible CPI and wage tracker; BLS new-tenant rent index, diffusion indices and JOLTS; Zillow and Apartment List rent indices; KC Fed LMCI; BEA GDI and NIPA profits; Atlanta Fed GDPNow and NY Fed nowcast; Epoch AI.

## 7. Decisions and sign-off

- 46, 47 — ruled 2026-10-16 ("Yes, accept").
- 48 — ruled 2026-10-16 ("Yes, roll it this way"), as one brief with Group A/B priority.

Signed: A. Chester, 2026-10-16 (chat rulings as recorded above).
Filing: filed as Batch 7 (see Encoding); commits on `docs-batch-7` after Batch 6; register entries at the next Doctrine sitting.

## 8. Filing notes (16 Oct 2026, the integration review)

These notes record what the filing review found in the repo at the stitched chain's tip and on the open branches (`st-r5-index` at `e5677f4`, `6e-metric-lenses` at `273dd8a`). They are not rulings. Each one is for the build session to confirm.

1. **Verify item 4, answered in part.** The Cleveland Fed median and 16% trimmed-mean CPI are not among the FRED series the repo pulls (134 at the chain's tip); the Atlanta Fed sticky CPI already is (`sticky_cpi`, STICKCPIM157SFRBATL), as are JOLTS quits, payrolls, U-3, CPI and core PCE. Both Cleveland series are on FRED (MEDCPIM158SFRBCLE, TRMMEANCPIM158SFRBCLE), so they are additions to the FRED pull, not a new writer.
2. **Most of item 48 is FRED.** Of the 24 lenses, the series for the employment, CPI, PPI and GDP groups are on FRED with few exceptions: the Sahm rule, permanent job losers, prime-age participation, initial and continuing claims, temp help, aggregate weekly hours, the ECI, the Atlanta Fed wage tracker, the KC Fed LMCI, the PPI intermediate-demand stages, final sales to private domestic purchasers, GDI, NIPA profits and the saving rate all have FRED ids. Those are extensions of the FRED writer. The sources that are not FRED, and so are new writers: the BLS API (the CES diffusion indexes and the new-tenant rent index), the Zillow and Apartment List rent files, the GDPNow and NY Fed nowcast workbooks, and Epoch AI. New writers were held for Track D's D1c until 16 Oct, when the operator ruled that WAL and the busy timeout satisfy D1c for append-only scheduled writers; they build unheld, and the write-lock helper is queued separately.
3. **Lens 22 is largely built.** AUD-3d (branch `aud-3d-fred-history`, in the stitched chain) stamps every FRED series with its first-publication availability from ALFRED vintages, so first-print-versus-revised evaluation on the point-in-time store already holds for FRED-sourced series. Series pulled directly from the BLS or BEA need their own first-publication stamps, as the Bank of Thailand and other official writers do.
4. **Item 47's quarterly by-hand line** was ruled explicitly in this order, which is what the operator's rule of 16 Oct requires for any new recurring by-hand data line. Epoch AI publishes its data as downloadable files, so the by-hand audit (queued 16 Oct) should test whether the constant-capability cost series reads automatically within robots; the token-volume proxy and the hyperscaler revenue lines are likelier to stay by hand.
5. **Item 46's "by hand" entries** (the disagreement pair and the Warsh-matrix line) are judgment drafts, not data. Under the operator's ruling of 16 Oct, the build session commits them as drafted and lists them for the operator's accept-all; the register's confirm/reject stays the operator's.
6. **The new labour block** changes the stack's section list. The build session updates the report template edit map (the 25 Sep order, §7), the section word budgets in `config/reporting_stack.yaml`, and the Monthly's table and chart budgets, and records what the block displaces, if anything.
7. **Builds with 6e.** `6e-metric-lenses` is session B's branch; its own notes list what remains of 6e (S3a, S3b, S3c, the CPI lead composite, the three bound lenses, the Weekly and close adopting the lens columns, and a consensus source). Items 46 and 48 Group A, with the cross-cutting lenses, ride B's next 6e paste as the order's work order says (~19h). Item 46's panel and the CPI lenses reach the 1 Nov Monthly only if 6e merges in the second stitched chain on Thu 22 Oct, ahead of the Fri 23 dry run.
8. **The consensus source (lens 23, verify item 1) is still open**, and 6e's own needs-you list asks the same question (its item 6). No free, machine-readable consensus for the macro releases was found at filing; the Survey of Professional Forecasters stays the quarterly anchor and ST-R6.48f waits.
9. **Item 46's pass-through flag switches item 32's sub-state.** Item 32 (Batch 6) is being built on `st-r5-t1-rest` on 16 Oct; whether it lands as an `inflation.driver` sub-state or report-only pending a pre-registration is that session's finding. The flag here is built against whichever form lands, and says so.
