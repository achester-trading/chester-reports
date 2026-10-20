# Dealer scorecard — pre-registration (6b, October 2026)

*Written and committed on 17 Oct 2026, before the first scored month, by session A on branch `6b-dealer-2`. **Never edited.** A change is a new registration in a new dated file; this one stays as written. The spec is the dealer-positioning brief v2 (`docs/briefs/dealer-positioning-brief-2026-10-09.md`), section 5, ratified 16 Oct 2026, with the rulings of 17 Oct 2026 on the part 1 report.*

## What this registers

**The five hypotheses of the brief's section 5**, as six tests, because the wall hypothesis has a call side and a put side. Each states:
- its mechanism, its eligibility and its outcome;
- the window in which the outcome is read;
- its base rate and its price-action baseline;
- the formation and test split, and the promotion rule.

**The source.** Every input is the close's stored `dealer.scorecard_day` row for SPY (`daily_cascade/stack_close.py scorecard_row`), plus SPY's stored daily closes for H5. The code that scores them is `altdata/dealer_scorecard.py`. Its thresholds are mirrored in `config/reporting_stack.yaml` under `dealer_scorecard`, and `tools/validate_dealer_block.py` holds the two to each other and this file to its SHA-256.

**The common definitions:**
- **A regime session:** the morning profile's net-to-gross is at or above **0.10**. "Morning" is the prior session's settled 16:10 capture, the one in force during the session.
- **The implied one-day range:** prior close × implied volatility × √(1/252). The implied volatility is SPY's own at-the-money 30-day IV from our chain, or the VIX where that is not stored, labelled "VIX as proxy".
- **The walls** are the morning's OTM walls: the OTM call wall and the OTM put gamma wall (audit F5; ruled 17 Oct 2026). The all-strike extremes are peaks and are never scored as walls.
- **The peak-gamma strike** is the morning's largest |GEX| strike.
- **Eligibility comes before outcome.** An ineligible session is recorded as None, never as False. An outcome that needs sessions not yet stored is None (unresolved) until they are.

## The hypotheses

### H1 — dampened

- **Mechanism:** dealers long gamma hedge against the move, buying weakness and selling strength, so the realised range comes in under the implied.
- **Eligibility:** a regime session, with the morning's net GEX positive.
- **Outcome:** the session's high-to-low range is **at or under 0.8 ×** the implied one-day range.
- **Window:** the session itself.
- **Base rate:** the share of every scored session, eligible or not, whose range is at or under 0.8 × implied.
- **Baseline (price action, no dealer content):** persistence. The share of sessions meeting the threshold, among sessions that follow a session that also met it.

### H2 — amplified

- **Mechanism:** dealers short gamma hedge with the move, so the realised range runs over the implied.
- **Eligibility:** a regime session, with the morning's net GEX negative.
- **Outcome:** the range is **at or over 1.2 ×** the implied one-day range.
- **Window:** the session itself.
- **Base rate:** the share of every scored session whose range is at or over 1.2 × implied.
- **Baseline:** persistence, as in H1, on the 1.2 × threshold.

### H3a — call wall held

- **Mechanism:** dealer long-call hedging sells into a rally that reaches the call wall (Dealer's Hand 7.1).
- **Eligibility:** the session **approached** the morning OTM call wall: its high came within **0.25%** of it.
- **Outcome:** the close is below the wall.
- **Window:** the session itself.
- **Base rate:** the share of every scored session whose close sits at least 0.25% below its own high. This is what any touched level would read as "held".
- **Baseline:** the round-number test. The same approach and the same outcome, scored against the nearest $5 round number above the prior close.

### H3b — put wall held

- **Mechanism:** holders monetise protection and vanna unwinds near the put gamma wall (Dealer's Hand 7.2). The pure gamma story says the opposite, which is why this is a test and not a reading.
- **Eligibility:** the session's low came within **0.25%** of the morning OTM put gamma wall.
- **Outcome:** the close is above the wall.
- **Window:** the session itself.
- **Base rate:** the share of every scored session whose close sits at least 0.25% above its own low.
- **Baseline:** the round-number test, against the nearest $5 round number below the prior close.

### H4 — pinned

- **Mechanism:** hedging flow is densest at the peak-gamma strike, and on expiry it pulls the close toward it (Dealer's Hand 7.4).
- **Eligibility:** **the monthly third-Friday expiry only** (ruled 17 Oct 2026). SPY's weekly Fridays and daily expiries stay out, and this registration records that choice so it can be revisited with evidence, as a new registration.
- **Outcome:** the close is within **0.25%** of the morning peak-gamma strike.
- **Window:** the session itself.
- **Control:** the same test against max pain. Reported beside the outcome, never instead of it.
- **Base rate:** the share of every scored session, any day, closing within 0.25% of its morning peak-gamma strike.
- **Baseline:** the nearest-round-number test. The close within 0.25% of the nearest $5 round number, on the same eligible sessions.

### H5 — flip crossing

- **Mechanism:** crossing the zero-gamma level moves the market from hedging against moves to hedging with them, which shows in the sessions after the crossing, not in the crossing itself (Dealer's Hand 7.5).
- **Eligibility:** the session's range contained the morning zero-gamma level.
- **Outcome:** realised volatility over the **next three sessions** (close to close, annualised) is above realised volatility over the **prior ten**.
- **Window:** the three sessions after the eligible session. The outcome is unresolved until they are stored.
- **Base rate:** the share of every session with ten sessions before it and three after whose next-three realised volatility exceeds its prior-ten.
- **Baseline:** the same outcome on sessions whose range contained the 20-session moving average, a price level with no dealer content.

## How rates are printed

- **The form:** k/n, with a **Wilson 95% interval**, and the base rate and the baseline beside it, each with its own n.
- **Sessions and episodes are both counted.** An episode is a run of consecutive eligible sessions; a regime run or a wall approach that lasts several sessions is one episode.
- **The printing floor:** no count prints below **20** scored sessions. The line then says how many are scored and nothing else.
- **No rate is a decision below 120 eligible sessions**, and every line under that floor says so.

## Formation, test and promotion

**The split, per test:** the first **120** eligible sessions form, and the next **120** test. The formation estimate is never re-estimated on the test window.

**Promotion.** A test is promoted only when all three hold:
1. the test window's Wilson interval excludes **both** the base rate and the baseline;
2. it does so after a **Benjamini–Hochberg** control at **q = 0.10** across the registered family (the six tests here);
3. the formation estimate lies on the same side of the base rate as the test estimate.

**Before promotion:** a promoted test may then be printed as a reading in T3, the horizon matrix. Until one is, T3 prints only "registered hypotheses: n, none promoted". Nothing in this registration grants a reading before promotion.

**Demotion:** a promoted test is demoted when a rolling 120-session interval includes the base rate for two consecutive months.

**Tradable is a further step.** A promoted hypothesis's setups are graded in the setup ledger against stored bars with a modelled cost (a market order at the signal bar's close plus one tick) over N ≥ 40 setups, by the Doctrine's existing engine rule. The scorecard's base rates are what EL-12's engine registers as its prior. They are not an edge.

## What this registration does not do

- It writes no register row, no order and no alert.
- It changes no Weekly or Monthly descriptive flag except as recorded on branch `6b-dealer-2`:
  - the walls those flags score are the morning OTM walls;
  - a wall not approached is None;
  - "dampened" is added.
- The descriptive "pinned" (the close within 0.25% of max pain, any session) and "amplified" (the flip crossed and the range at or over 1.2 × implied) keep their existing definitions in the Weekly's table. The tests above are separate.
