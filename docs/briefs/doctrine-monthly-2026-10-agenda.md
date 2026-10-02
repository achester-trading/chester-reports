# Doctrine monthly — 3–4 October 2026 — agenda

One sitting, decisions taken in chat one at a time; each ruling is applied to the files by a session afterwards. Items are ordered so that early answers feed later ones. *Proposed* values are the session defaults now running unratified.

## 1. The regime mapping — first live test

On 1 Oct the macro dial moved **expansion → overheating**, which the proposed mapping reads as **Transition (leaving Expansion)**: Book A band 60–70%, net-beta cap 85%.

- Ratify the dial-to-Doctrine mapping (expansion/goldilocks → Expansion; late-cycle/overheating → Overheat; stagflation → Tightening; slowdown/contraction/bust → Contraction; mixed → Transition) and the **10-session crossing rule**.
- Decide whether a dial change on one session should move bands at once, or only after it holds (as dimensions do, two sessions).

## 2. Risk limits (config/risk_limits.yaml)

- Net beta across books ≤ top of Book A's band + 15 pp *(from the Doctrine — confirm)*.
- Sector ≤ 25% of capital, beta-adjusted *(proposed)*.
- Vega ≤ 0.5% of capital per vol point *(proposed)*.
- Duration ≤ 5% of capital per 100 bp *(proposed)*.
- Instrument reference: index sector weights and bond durations *(approximate, proposed)*.

## 3. The change ladder (Enterprise Layer §3.4a)

Five tiers — tactical learning → regime adaptation → relationship change → structural change → durable principle — with the evidence and authority each requires, and the rule that an anomaly climbs at most one tier per review cadence. Ratify or adjust.

## 4. The attention budget (§3.4b)

*Proposed:* at most five packet approvals a week; one review sitting a week of at most two hours; both counts printed by the Weekly; anything beyond queues. Set the numbers.

## 5. The intraday rung (§3.4c)

Record the 27 Sep ruling: Books A–D stand; intraday is a tactics layer for Books B and C plus at most two paper engines (dealer-positioning/0DTE, one scheduled-event engine), each with a mechanism, a base rate, N ≥ 40 and a kill criterion before its first trade. Confirm, and pick which engine goes first after 6b.

## 6. Metric lenses (docs/briefs/metric-lenses-brief-2026-10-01.md)

- Correction / bear flags at −10% / −20%.
- Credit-widening flag at +100 bp in three months.
- Each family's long window (20y for spreads, VIX, labour, ratios; full history for rates, inflation, returns; none for quantities).
- The 30-point disagreement flag between the five-year and long percentiles.
- Any series whose family is ambiguous.

## 7. The Monthly

- Phase A is live for 1 Nov. Anything you want changed before then, from the dry runs you read.
- Phase B (voices register, ~10 h): go now or after 6b?

## 8. Lessons from the first fortnight (for the Doctrine's dated appendix)

- INC-6: a foreign listing is a currency position (MEXI short, −$8,951; the guard is built).
- INC-7: an exit the system didn't see — Portfolio Truth carried a closed position for a week.
- The first graded decisions: anything to write down about how they were taken.

## 9. Order of work after the session

*Amended 2 Oct 14:21 ET* — Ari pulled 6d forward to follow the daily commentary build. Proposed: T1 daily close (reporting stack, ~14 h) → 6d prediction markets + rate path (~6 h) → T2 Weekly (~10 h) → T3 Monthly (~12 h, for 1 Nov) → cloud migration → 6b intraday slots → 6e with the metric lenses → 6f → Quarterly Structural; Audit #4 holds 14–15 Oct. Confirm or reorder.

## 10. The reporting stack (docs/briefs/reporting-stack-brief-2026-10-02.md)

Adopted 2 Oct; these values are proposed and run unratified until this sitting:

- Plumbing & rates "deep" trigger on the daily: tier-1 event this session or next, or 10y/30y ≥ ±10 bp, 2s10s ≥ ±8 bp, HY OAS ≥ ±15 bp.
- What's priced "deep" trigger: breakevens ≥ 10 bp; implied rate for any of the next four meetings ≥ 12.5 bp; a watched prediction market ≥ 10 pts; S&P consensus EPS revision ≥ 1% (Weekly); UMich/SCE expectations ≥ 0.3 pt.
- Reading budgets: daily ≤ 1,000 words / 3 charts; Weekly ≤ 3,500 / 6; Monthly ≤ 7,000 / 10.
- Long-frame averages in the Monthly: 40-week, 10-month, 20-month — levels, never signals.
- Prediction-market watch list and the disagreement thresholds (venue vs fed funds ≥ 15 pts; venue vs our scenario weight ≥ 20 pts).
