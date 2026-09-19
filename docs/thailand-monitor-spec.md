# Thailand Monitor — Report Specification

**Status:** deferred to the end of the roadmap (after Phase 5) · **Cadence:** quarterly, with alerts · **Isolation:** outside the trading system's regime dials, mechanism groups, and register. Reads the store; feeds nothing.

## Purpose — the decision it supports

One recurring decision and two occasional ones. **Recurring:** when, and in what tranches, to convert USD to THB for construction and land payments on the Pua, Nan property. **Occasional:** whether to hedge a known future THB liability (forward, staged conversion, or a THB deposit), and whether the project budget has drifted in real terms.

This is a personal-finance report about a THB liability held by a USD earner. It is not a market view and it must not become one — which is why it is isolated from the pillars and dials.

## Sections, in order (word budget: 800; deltas first)

1. **The rate, and what changed.** USD/THB level; change since last report, one quarter, one year; percentile against five years; the implied cost in USD of the *remaining* THB budget at today's rate versus at the rate assumed in the plan. *This line is the report.*
2. **What moves the baht** — read from the store, one line each with the delta: Bank of Thailand policy rate and stated path; Thai CPI; current-account balance and tourism arrivals (the baht's two structural drivers); the dollar's broad direction (from the Currencies paper's frame, referenced not restated); regional risk (CNY, JPY as the baht's neighbors).
3. **Construction and property cost.** Thai construction materials index and labor cost series (BoT / NESDC); regional property price index for the North where available, national otherwise; the project's own budget-to-date against the plan, in THB and in USD-at-plan-rate.
4. **The conversion decision.** A three-row table: convert the next tranche now / stage over the quarter / defer — each with the USD cost at the current rate, the rate at which each becomes the wrong choice, and the base rate of quarterly THB moves of that size (from the store's own history). No recommendation; the operator decides.
5. **Rules and residency** (only when changed). Remittance and foreign-ownership rules; any tax-residency or reporting item with a date.
6. **Alerts fired this quarter**, and the thresholds for the next.

## Alerts (the between-report mechanism)

- USD/THB moves more than 4% in either direction since the last report.
- Bank of Thailand changes the policy rate or its stated stance.
- A construction payment falls due within 30 days (from a dates table the operator maintains).
- The remaining budget's USD cost at the current rate exceeds plan by more than 10%.

## Data — all free

| Series | Source | Frequency |
|---|---|---|
| USD/THB | FRED `DEXTHUS`; BoT for intraday if ever needed | Daily |
| BoT policy rate, statements | Bank of Thailand API | Meeting |
| Thai CPI, construction materials index | Ministry of Commerce / BoT | Monthly |
| Current account, tourist arrivals | BoT, Ministry of Tourism | Monthly |
| Property price indices | BoT / Real Estate Information Center | Quarterly |
| Project budget and payment dates | operator-maintained CSV in the store | As entered |

Registry entries carry `namespace: thailand`, `trigger_eligible: false` permanently, and no mechanism group — so nothing here can ever vote in a trading decision.

## Build estimate

Four hours: fetchers (2), the report renderer on the existing delivery layer (1), alerts (1). Deferred until the trading system's Phases 0–5 are complete.
