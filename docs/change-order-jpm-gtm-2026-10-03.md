# Change Order — JPM Guide to the Markets 4Q 2026: borrow list rulings

| | |
|---|---|
| Status | **Ruled 2026-10-03 16:32 ET** in chat — Ari: "accept all recommendations, across all groups." Register numbers (SR-36 onward) are assigned at Audit #4 (14–15 Oct), where this batch's slot in the order of work is confirmed. |
| Source | `docs/scans/jpm-gtm-2026q4.md` — the quarterly read of J.P. Morgan Asset Management's *Guide to the Markets*, U.S. 4Q 2026 (data as of 30 Sep 2026), produced 3 Oct 2026 by the scheduled task "JPM Guide to the Markets — quarterly read". Candidate IDs GTM-1…GTM-23 are the scan's. |
| Owner | Ari Chester |
| Binding on | Claude Code sessions building T3 (Monthly), 6e (metric lenses), Phase B (voices) and the GTM batch |
| Precedence | Below Part 26, the change orders, Amendments #3–#5, the reporting-stack brief and the metric-lenses brief. Rights are narrow: base-rate row, modifier, sourced figure or voices entry; nothing here becomes a panel or trigger before an offline calibration study. Figures from the Guide print in the Monthly only as sourced figures (URL and slide number stored); the Guide's recommendations never print. |

## Rulings

| ID | Item | Ruling | Rights | Placement | Hours |
|---|---|---|---|---|---|
| GTM-1 | Inflection-points table (level, fwd P/E, dividend yield, 10y at prior tops/bottoms and today) | **ADOPT** — eight historical rows stored from the scan as sourced figures; "today" row computed | base-rate row | GTM batch; T&B standing exhibit | 2 |
| GTM-2 | Valuation quad: fwd P/E, CAPE, dividend yield, EY − Baa | **ADOPT** — the long-run average ± 1 SD added as a form on valuation ratios, beside the dual percentiles already ruled | modifier | **6e** (pulled forward) | in 6e |
| GTM-3 | Concentration twin (top-10 cap share vs earnings share; P/E top 10 vs other 490 vs own averages) | **ADOPT via the T&B overlay intake queue** (one at a time) | modifier | GTM batch | 4 |
| GTM-4 | AI five-bucket decomposition + hyperscaler cash-flow bridge (OCF − capex, 2019–2028F, consensus capex path) | **ADOPT** — highest value on the list; bucket definitions by hand quarterly | modifier | GTM batch (Factor I exhibit; Monthly mechanics) | 6 |
| GTM-5 | EPS growth decomposition (margin / revenue / share count vs 2001–25 average) | **LOG** — this quarter's figures stored from the scan; pipeline later with GTM-1 | base-rate row | scans ingest | 0 |
| GTM-6 | Credit twin percentile (OAS and yield-to-worst percentiles, IG and HY) + HY rating mix | **ADOPT** — percentiles computed in the spread family; rating mix by hand quarterly | modifier | **6e** (pulled forward) | in 6e |
| GTM-7 | Stock–bond correlation regime table (three eras with average inflation) | **AMEND SR-9**; computed from monthly total returns | modifier | GTM batch; Book A rule table | 2 |
| GTM-8 | Sentiment turning-point base rate (peaks → +4.8%, troughs → +24.1% over 12 months) | **ADOPT**, with the applicability caveat printed in the row (every sampled trough coincided with a price low; this one is at a high) | base-rate row + disagreement entry | GTM batch; narratives; Base Rates paper | 2 |
| GTM-9 | All-time-high base rates (count YTD, share of days, share that became floors, followed within a week) | **ADOPT**, from our own price history | base-rate row | GTM batch; Bull Rebuttal gate | 2 |
| GTM-10 | Sector rows: correlation to 10y yield changes; fwd P/E vs 20y avg; NTM EPS vs median; foreign share of sales | **ADOPT the correlation row** (computed); the rest as sourced figures quarterly | modifier | GTM batch; tape leadership | 1 |
| GTM-11 | K-shape panel (labor vs profits share; net worth by cohort; income vs spending by quintile) | **ADOPT, placed with Amendment #3 workstream B** (the Internal Order panel), built once | modifier | Amendment #3 WS-B | 4 |
| GTM-12 | Federal finances (net interest vs defense vs customs; deficit share; CBO debt path) | **ADOPT what the Factor IV panel lacks**; CBO by hand at each update | modifier | GTM batch; Factor IV | 2 |
| GTM-13 | Fixed-income scenario table (yield, YTD, duration, correlations, ±100 bp returns by sector) | **ADOPT**; durations from `config/instrument_reference.yaml` | modifier | GTM batch; plumbing & rates; Book A | 3 |
| GTM-14 | Cross-asset YTD ranking (the quilt's current column) | **ADOPT** from the proxies the store already holds | tape | **T3** (pulled forward) | 1 |
| GTM-15 | Effective tariff rate (customs duties ÷ goods imports, monthly) | **ADOPT** | modifier | GTM batch; inflation lens | 1.5 |
| GTM-16 | Hyperscaler credit anchors (net debt/EBITDA vs IG median; share of IG index; issuance) | **ADOPT as sourced figures** quarterly; **AMEND SR-16** (Duration Absorption) with the anchor row | modifier | scans ingest | 0 |
| GTM-17 | AI buildout funding mix 2026–30 ($5.5tn) | **LOG** | sourced figure | scans ingest | 0 |
| GTM-18 | Global composite PMI heatmap | **LOG** as sourced figures quarterly (no free feed) | sourced figure | scans ingest | 0 |
| GTM-19 | International return decomposition | **LOG** (annual appendix) | sourced figure | scans ingest; library | 0 |
| GTM-20 | AI adoption and capability markers (Census BTOS; METR) | **LOG**, semi-annual | sourced figure | scans ingest; Factor I-b | 0 |
| GTM-21 | Household delinquency flows + debt-service ratio | **ADOPT the DSR** (FRED) as the **SR-5** modifier; delinquency flows stored quarterly from the scan | modifier | GTM batch | 0.5 |
| GTM-22 | Dollar cycles table | **LOG**, one-off | dated appendix | library track (Currencies) | 0 |
| GTM-23 | Recovery-time and 60/40 drift tables | **LOG**, one-off | dated appendix | library track (Portfolio Construction) | 0 |

Also ruled from the scan:

- **The triple on every slow-layer row** — latest / long-run average / percentile, with "data as of" — adopted as the Monthly's table form. **T3.**
- **The core CPI – core PCE gap** as a derived series with a lens (the sign flip is a What-doesn't-fit item). **6e.**
- **A scans ingest** — the reference table of each `docs/scans/*.md` stored as sourced figures (URL, slide number, as-of), so the Monthly can print them under "No stored source, not printed". **T3.** Without it no LOG item and no by-hand figure can appear.
- **Voices entry** — J.P. Morgan Asset Management, Global Market Insights (GTM U.S. 4Q 2026, 30 Sep 2026), stance as inferred in the scan, status NEW — the first sell-side row of the Phase B register. **Phase B.**
- **The disagreement entry** — sentiment at 48.1 with the index at an all-time high has no precedent in the base rate's sample; logged against the base rate's applicability, not as a signal.

## Build

The GTM batch (GTM-1, 3, 4, 7, 8, 9, 10, 12, 13, 15, 21) is about **24 hours**; GTM-11 travels with Amendment #3 workstream B (~4 h); the pulled-forward items add about 3 hours to T3 and 6e combined. Proposed slot: **after 6e and before 6f**; Audit #4 confirms or moves it. Every adopted series carries its `family` and `long_window` under the metric-lenses brief; every figure stored from the scan carries its slide number and as-of date.

## Register

SR-9, SR-16 and SR-5 are amended as above. New register numbers for the adopted items are assigned at Audit #4, continuing from the last number in `docs/signal-triage-register.md` (SR-36 if nothing newer is visible).

## Quarterly mechanism

The scheduled task "JPM Guide to the Markets — quarterly read" exists (created 3 Oct 2026; fires 06:56 ET on the 6th of January, April, July and October; web sources only; delivers `docs/scans/jpm-gtm-YYYYqN.md` and a short summary; no decision rights). After each run, the task's baseline reference table is replaced with the run's §7 table (one line to a chat session). Its prompt was amended 3 Oct to carry these rulings so later runs propose AMEND GTM-nn against adopted items rather than re-proposing them.
