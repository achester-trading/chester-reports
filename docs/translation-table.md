# Risk Level Translation Table — v2.3

**Purpose:** Translates between the five reports' risk language. Pin this at the top of your workflow. When the same market state is described differently across reports, the discrepancy itself is the signal — resolve it before sizing positions.

**Operational tool:** The **System State Dashboard** (Tier 0, `system-state-dashboard.jsx`) is the morning instrument panel that applies the conflict-resolution rule below mechanically against the live state of all five reports. Pin the dashboard above this table — read the dashboard's sizing synthesis first, consult this table when something looks off.

**What changed in v2.3:** Added (1) the **Monthly Matrix → Top & Bottom Verdict Mapping** table — answers whether a Monthly Matrix scenario weighting is consistent with the live Top & Bottom verdict, (2) the **Options Output Reconciliation Rule** — distinguishes Monthly Appendix C (illustrative thesis expression) from Top & Bottom Appendix D (live engineered portfolios), and (3) a note that pillar weights and overlay thresholds are subject to quarterly calibration based on `quarterly_backtest.py` output. The crypto two-source reconciliation has been simplified — Alt Asset now writes crypto values to Monthly's SQLite, so there's one source of truth refreshed weekly.

---

## The Five-Tier Frame

| Tier | Report | Horizon | Role in the stack |
|---|---|---|---|
| 1 | **Disruptive Themes Report** | Generational | Sets the era — defines what "normal" means and the tail risks |
| 2 | **Monthly Macro Report** | Strategic | Sets the posture — composite score → position size |
| 3 | **Top & Bottom Report** | Structural | Flags the turn — composite + 10 triggers + 3 parallel-signal overlays |
| 4 | **Alternative Asset Report** | Cross-asset | Lateral confirmation — correlation breaks, outside-equity signals |
| 5 | **Daily Cascade** | Tactical | Executes — timed, sized setups |

Tiers 1–3 are the **vertical spine** (each constrains the one below). Tier 4 runs **laterally** alongside the spine as a confirm/contradict check. Tier 5 executes within all of them.

The relationship between Tiers 2 and 3 is the most important one to internalize: the **Monthly Macro Report** is the calendar-driven baseline (refreshes on a fixed cadence, sets the standing position size); the **Top & Bottom Report** is the event-driven escalation layer (fires only when triggers or overlays approach or breach, can shift the sizing read mid-month).

---

## The Core Mapping Table

| Disruptive Themes Regime | Monthly Macro Composite | Top & Bottom Status | Daily Macro Risk | Daily GEX Regime (typical) | Position Sizing |
|---|---|---|---|---|---|
| **Soft-landing holds** | +0.5 to −0.5 / NEUTRAL | CLEAR | LOW | POSITIVE | 100% normal |
| **Late-cycle, contained** | −0.5 to −1.2 / OVEREXTENDED | WATCH | ELEVATED | POSITIVE / NEUTRAL | 50–70% normal |
| **Late-cycle, fragile** | Below −1.2 / TOP SIGNAL | ALERT | HIGH | NEUTRAL / NEGATIVE | 25–40% normal, no new longs |
| **Crisis / regime break** | Below −1.2, falling | ALERT (most triggers fired) | HIGH | NEGATIVE | Defensive only, hedged |
| **Trough / reset** | Rising from lows / BOTTOM WATCH | BOTTOM SIGNAL armed | LOW | NEGATIVE → POSITIVE | Begin scaling longs back in |

The Disruptive Themes column is the slowest to move — it may sit on one row for quarters. The Daily columns can traverse several rows in a single week. **The Disruptive Themes column caps the others:** if it reads "late-cycle, fragile," the maximum sizing is the fragile row's ceiling even when the Daily looks benign.

---

## How to Read the Five Tiers

**Disruptive Themes Report** — the slow-moving strategic *frame*. Updates every two months. Highest authority on direction; it caps how aggressive any lower tier may be. Built on the Five-Force Framework (five factors including Factor V, Monetary Architecture in Transition) with a scenario distribution, drawdown ranges, and — as of the Q3 2026 refresh — its own composite on the same −2…+2 band convention as the Top & Bottom Report (currently −1.2, OVEREXTENDED, edge of TOP SIGNAL). The "regime" column above is the modal scenario; the composite gives the row a number. Deep context lives in the *Foundations and Field Guide* companion paper.

**Monthly Macro Report** — the strategic *posture*. Composite score across ten pillars → regime label → position size for the month. This is the handoff value the Daily Cascade actually consumes, and the standing baseline that everything below executes within.

**Top & Bottom Report** — the structural reversal *warning system*. Composite verdict (TOP SIGNAL / OVEREXTENDED / NEUTRAL / CONSTRUCTIVE / BOTTOM SIGNAL) is the primary read, supplemented by ten event-driven triggers and three parallel-signal overlays that catch composite blind spots.

**Alternative Asset Report** — the lateral *cross-check*. Does not set posture; it confirms or contradicts the equity-stack read from outside equities. Its correlation matrix is an early-warning layer that often leads the Top & Bottom Report's credit and dollar triggers.

**Daily Cascade** — the tactical *execution layer*. GEX, trend, macro risk, vol — toggling session by session. Most volatile, least authoritative on direction; most authoritative on timing.

---

## Conflict Resolution Rule (Five-Tier, with Overlays)

**Governing principle:** *When tiers disagree, the slower tier wins on DIRECTION and the faster tier wins on TIMING.* The more cautious reading wins on sizing until reconciled.

Practically, resolve in this order:

1. **Disruptive Themes caps sizing.** No lower tier may size above the Disruptive Themes row's ceiling. A bullish Daily under a "fragile" regime still trades — but small and hedged.
2. **Monthly Macro sets the standing baseline.** Position size for the month defaults to the Monthly composite's regime row. This is the starting point everything below executes from.
3. **Top & Bottom composite is the primary structural read.** The verdict (TOP SIGNAL → OVEREXTENDED → NEUTRAL → CONSTRUCTIVE → BOTTOM SIGNAL) drives any escalation or relaxation of the Monthly baseline within the month.
4. **Active overlays escalate by one tier.** Any parallel signal in ACTIVE state — Concentration & Complacency, HY Spread Acceleration, or Liquidity & Funding Stress — shifts the sizing read one row more cautious, even if the composite hasn't moved. The overlays exist specifically to catch what composite scoring misses; ignoring them when active defeats the design.
5. **Triggers fire within composite verdict.** The 10 triggers refine the composite — APPROACHING flags add caution; TRIGGERED flags confirm the composite reading; new fires between Monthly refreshes shift the read one row more cautious.
6. **Alternative Asset escalates, never relaxes.** A correlation break can *raise* caution one tier; it cannot lower it. (See alignment rules below.)
7. **Daily Cascade sets timing within the cap.** Once tiers 1–6 set the ceiling, the Daily decides entry, exit, and stop — but cannot expand the size ceiling.

### Worked examples

- **Disruptive Themes "late-cycle fragile" + Daily Cascade "positive gamma, buy dip"** → Buy the dip (Daily timing) at reduced size with tight stops (Disruptive Themes direction). Not a conflict — this is the system working as designed.

- **Monthly Macro NEUTRAL + Top & Bottom ALERT (multiple triggers fired) + Daily Macro LOW** → Treat as HIGH. Top & Bottom is the leading indicator on structural tops and fires before the Monthly composite updates. Size 25–40%, no new longs.

- **NEW · Monthly Macro OVEREXTENDED + Top & Bottom composite OVEREXTENDED + Concentration overlay ACTIVE (5/5 firing)** → Escalate one tier further to **TOP SIGNAL-equivalent sizing**. The composite already flags caution; the active Concentration overlay says "this looks like 2000/2022 — valuation extremes the composite is mathematically prone to under-weighting." Operate as if the composite were already at TOP SIGNAL. Size 25–40%, no new longs, particularly in concentrated names (Mag 7, semis).

- **Monthly Macro OVEREXTENDED + Alternative Asset shows HY-credit correlation break + gold/Treasury reserve shift** → Escalate to the fragile row. Two Alt-asset signals are confirming the Top & Bottom Report's credit and dollar triggers from outside equities — this is exactly the early-warning the lateral tier exists to provide.

- **Disruptive Themes "soft-landing" + Monthly Macro TOP SIGNAL + HY Spread Acceleration overlay armed** → Rare and important. A fast deterioration the Disruptive Themes hasn't caught up to, confirmed by an overlay specifically designed to catch credit-cycle tops the composite misses. Trust the faster tier on sizing (go cautious now), AND flag the Disruptive Themes for an early refresh — the quarterly cadence may be stale.

- **Monthly Macro BOTTOM WATCH + Top & Bottom Report shows BOTTOM SIGNAL armed + Alt Assets show oversold extremes** → Begin scaling longs back in. Three-tier agreement on the upside turn — the inverse of a TOP SIGNAL confluence and equally actionable.

---

## Monthly Matrix → Top & Bottom Verdict Mapping

The Monthly Macro Report's Section III ships **five probability-weighted scenarios** (e.g. "Hartnett pullback 40-50%, Stagflation muddle 25-35%"). The Top & Bottom Report's composite produces a **single verdict** (TOP SIGNAL / OVEREXTENDED / NEUTRAL / CONSTRUCTIVE / BOTTOM SIGNAL). These describe the same world from different angles, and they should be consistent. The mapping table below answers: *"Given the Monthly's modal scenario, what verdict should the Top & Bottom be showing? And what does a mismatch mean?"*

| Monthly Matrix Modal Scenario | Probability Range | Expected Top & Bottom Verdict | Action if Mismatched |
|---|---|---|---|
| **Yardeni melt-up continues** | 5–10% | NEUTRAL or CONSTRUCTIVE | If TB shows OVEREXTENDED, the Monthly may be stale — schedule early refresh OR Top & Bottom's overlays are catching what the Monthly composite has not yet absorbed |
| **Iran resolution → energy collapse → disinflation** | 15–25% | NEUTRAL trending → CONSTRUCTIVE | If TB stays OVEREXTENDED post-resolution, disinflation has not yet transmitted to credit / breadth metrics; ignore the Monthly scenario for sizing until TB confirms |
| **Stagflation muddle — high-vol sideways** | 25–35% | NEUTRAL or OVEREXTENDED | Wide acceptable range; no mismatch unless TB hits TOP SIGNAL or CONSTRUCTIVE |
| **Hartnett signal — moderate pullback** | 40–50% | **OVEREXTENDED** | If TB shows NEUTRAL, the Monthly may be over-weighting Hartnett — wait for TB's weekly Sunday refresh before sizing down further |
| **Severe private→public credit migration** | 5–10% | **TOP SIGNAL** | If TB does not confirm, watch HY OAS and the HY Spread Acceleration overlay specifically — the migration trigger is the one most prone to delayed public-market reaction |

**Reading rule:** Modal scenario × verdict should be **consistent**. When they aren't, the mismatch itself is information — usually a refresh-timing artifact (one report is fresher than the other) or evidence that the slower report's framing is stale. The dashboard surfaces these mismatches as cross-tier conflicts.

---

## The Ten Top & Bottom Report Triggers

Expanded from six in v3 Live. Tracked live in the daily 7AM Cross-Report Coordination block:

| # | Trigger | What it catches |
|---|---|---|
| 1 | **SpaceX IPO** — S-1 filed | Hartnett melt-up completion signal |
| 2 | **OpenAI IPO** — S-1 filed | Second Hartnett completion signal |
| 3 | **CPI breaches 4%** | Forces Fed back to tightening bias |
| 4 | **HY OAS > 350bp** | Credit-market confirmation of equity top — the missing ingredient until it fires |
| 5 | **% SPX > 200-DMA < 50%** | Breadth deterioration at price highs |
| 6 | **B&B Indicator > 8.0** | Hartnett sell signal armed; loss window opens 2–3 months out |
| 7 | **2s10s Un-Inversion** | Recession typically follows un-inversion within 6–12 months |
| 8 | **Curve Re-Inversion** | Second-chance recession signal when 3m10y or 2s10s flips back |
| 9 | **Credit Spread Acceleration** | Rate-of-change in HY/IG widening — leads absolute levels by 1–3 months at turns |
| 10 | **Private Credit Bifurcation** | Stress in less-transparent market while public HY tight — new channel post-2020 |

Each reads CLEAR / APPROACHING / TRIGGERED. Roll-up status is **CLEAR / WATCH / ALERT** — exact trigger-count thresholds for each tier are **TBD pending verification against the live `compute_scorecard.py`**. Prior versions used CLEAR (0–1), WATCH (2), ALERT (3+) for the six-trigger set; the thresholds for the expanded ten-trigger set have not been confirmed in this document.

---

## The Three Parallel-Signal Overlays

The structural innovation of Top & Bottom v3 Live. Each overlay fires **independent of the composite** and addresses a specific failure mode documented in calibration testing. Treat each as a CONDITION ("the market is stretched in this way") rather than a timing signal.

| Overlay | Failure Mode It Catches | Trigger Logic | Action When ACTIVE |
|---|---|---|---|
| **Concentration & Complacency** | Valuation tops the composite under-weights (2000, 2022) | 3+ of 5: Fwd P/E ≥ 20x · CAPE ≥ 30 · ERP ≤ 1.5% · Top-10 ≥ 25% · VIX ≤ 18 | Escalate sizing one tier · Particularly tighten concentrated-name exposure |
| **HY Spread Acceleration** | Credit-cycle tops where absolute HY level still looks tight (2007 calibration miss) | HY +50% off 12m low · 30d HY widening ≥ 40bp · IG widening ≥ 15bp · IG OAS ≥ 110bp | Escalate sizing one tier · Add credit-cycle confirmation to the bear case |
| **Liquidity & Funding Stress** | Plumbing stress before it becomes credit stress (2019 repo, 2025 funding strains) | Fed net liquidity YoY ≤ −10% · Bank reserves within 5% of LCLOR · SOFR–IORB ≥ +5bp · ON-RRP ≤ $200B · TGA volatility ≥ $200B/wk | Escalate sizing one tier · Watch SOFR–IORB as the leading sub-signal |

**Rule:** An ACTIVE overlay (3+ of its triggers firing) escalates the composite's sizing implication by one tier. Multiple active overlays do **not** stack beyond one tier of escalation — the rationale is that overlays often share underlying drivers (concentration and complacency tend to co-fire, for example), so additive escalation would double-count.

The 2024 yen-carry episode is the canonical false-positive case: Concentration & Complacency fired but no crash followed. The signal was *correct* that the market was expensive — it just didn't time the turn. The overlays are not timing signals. They are condition flags. Use them to size more cautiously, not to predict the date.

---

## Alternative Asset ↔ Top & Bottom Signal Alignment

The Alternative Asset Report's correlation matrix overlaps with two Top & Bottom triggers and one parallel-signal overlay. Use these as cross-confirmation — when the Alt Asset Report and the Top & Bottom Report agree, conviction in the turn-risk rises sharply:

| Alt Asset Signal | Confirms Top & Bottom Element | Action |
|---|---|---|
| HY/credit-sensitive assets decoupling from SPY | Trigger #4 (HY OAS > 350bp) + HY Acceleration overlay | If both fire, treat credit risk as confirmed, not emerging |
| Gold crossing Treasuries as reserve share / gold-SPY break | Disruptive Themes Factor IV (Dollar/Liquidity) + Liquidity overlay | Disruptive-Themes-grade signal; flag for early refresh |
| Crypto risk-on/off correlation flip vs SPY | Sentiment & Positioning (indirect) | Confirms or contradicts equity sentiment extreme |

**Rule:** An Alt Asset Report correlation break that confirms a Top & Bottom trigger or activates an overlay escalates that signal from APPROACHING to TRIGGERED-equivalent for sizing purposes, even if the raw threshold hasn't been hit yet. Lateral confirmation counts.

---

## Crypto Sentiment — Single Source of Truth

*Simplified in v2.3.* Crypto sentiment (BTC/Gold ratio, Crypto Fear & Greed, stablecoin flows) historically lived in **both** Monthly Pillar 5 and the Alternative Asset Report with separate refresh cadences, requiring a reconciliation rule. As of architecture v2.0, the Alternative Asset Report writes its weekly crypto values back to Monthly's `timeseries.db`, and Pillar 5 reads from there at composite-build time. **One source, weekly refresh, no reconciliation needed.**

The Alt Asset Report remains the deep-dive (full technicals, on-chain positioning, multi-horizon momentum); the Monthly Pillar 5 reading is a summary cross-check that automatically reflects the latest Alt Asset values. If the two ever appear to disagree, that's a bug in the writeback, not a reconciliation question.

---

## Options Output Reconciliation Rule

Both the Monthly Macro Report (Appendix C) and the Top & Bottom Report (Appendix D) ship structured options trade recommendations. They are **not redundant** — they exist for different purposes — but they can appear to conflict. The reconciliation rule:

| Report Output | Purpose | Design Philosophy |
|---|---|---|
| **Monthly Appendix C** — three illustrative trades (3M / 6M / 12M) | *Pedagogical thesis expression* | Single-trade structures showing how each macro thesis would be sized in options space. Demonstrates the macro framing, not a portfolio recommendation. |
| **Top & Bottom Appendix D** — three scenario-weighted portfolios (3M / 6M / 12M) | *Live engineered structures* | Multi-position portfolios with defined max loss across all probability-weighted scenarios. These are the trades a portfolio would actually express. |

**Conflict rule:** When the two appendices recommend different structures at the same horizon, **Top & Bottom wins on structure** (it accounts for the probability distribution across scenarios; Monthly Appendix C assumes a single thesis plays out). **Monthly wins on macro framing** (it explains *why* the trade exists — which pillar movement drives it, which catalyst would invalidate it).

In practice, the two should rarely disagree on direction because both are built from the same composite output. They will routinely disagree on strikes and structure — that's a feature: Top & Bottom optimizes for the probability-weighted payoff distribution, Monthly optimizes for thesis clarity.

---

## Sync Points Across All Five

| Trigger | Action |
|---|---|
| **First trading day of month** | Update Daily Cascade sector baseline to match new Monthly Macro sector pillar |
| **Every Sunday 9:30 PM** | Weekly Forward Plan refreshes coordination block; Monday 7AM pulls same values forward |
| **Every Friday 6 PM** | Weekly Reflection updates the Weekly Delta (which Monthly Macro pillars moved) |
| **Weekly (or on correlation break)** | Alternative Asset Report refreshes; any break confirming a Top & Bottom trigger or overlay escalates per rules above |
| **Every two months (or on regime input change)** | Disruptive Themes Report refreshes; recheck that its regime row still caps the Monthly Macro correctly |
| **Persistent Disruptive Themes ↔ Monthly Macro divergence (>1 month)** | Disruptive Themes cadence may be stale — schedule early refresh |
| **Persistent Daily ↔ Monthly Macro divergence (>5 sessions)** | Monthly Macro may be stale — schedule early refresh |
| **Any overlay flips from CLEAR to ACTIVE between Monthly refreshes** | Apply one-tier escalation immediately; do not wait for next Monthly run |

---

## When Discrepancies Persist

In practice the Disruptive Themes Report is almost always right at the multi-quarter horizon, the Monthly Macro at the multi-week horizon, and the Daily Cascade at the multi-hour horizon. The interesting questions live in between:

- **Multi-day horizon** → that's where the **Top & Bottom Report** (composite + triggers + overlays) earns its keep.
- **Cross-asset confirmation at any horizon** → that's where the **Alternative Asset Report** earns its keep.

A discrepancy that survives its tier's natural refresh window is the signal that the slower tier needs an early update — escalate up the stack, never down.

---

## Quarterly Calibration Caveat

*Added in v2.3.* The conflict-resolution rule above is **stable** — it describes how the tiers compose, not which numerical thresholds drive each tier's verdict. But the underlying thresholds are not stable: they were calibrated against a specific market regime and will drift as volatility regimes change. Examples of thresholds subject to recalibration:

- Pillar weights in the Top & Bottom composite (currently Valuation 17%, Macro & Liquidity 24%, etc.)
- Overlay firing thresholds (e.g. "5 of 5 indicators firing = ACTIVE")
- Trigger thresholds (HY OAS > 350bp, % SPX > 200-DMA < 50%, etc.)
- Verdict band edges (composite ≤ -1.2 = TOP SIGNAL)

These are reviewed every 90 days via `quarterly_backtest.py`, which replays the live scoring engine against the prior 8 quarters of `timeseries.db` data. If a pillar weight or threshold systematically misses a known turning point, the operator proposes an adjustment for the next monthly cycle. **The translation logic remains the same; the numbers within it evolve.**

The System State Dashboard surfaces the *current* threshold values and the date of their last calibration, so the operator always knows which generation of thresholds is in force.

---

*v2.4 — Synced with the "Foundations and Field Guide to the Five-Force Framework" companion paper: Disruptive Themes tier now described with five factors (incl. Factor V, Monetary Architecture in Transition) and its own −2…+2 composite (Q3 2026: −1.2, OVEREXTENDED, edge of TOP SIGNAL). Stray "Saeclum" naming removed. Pins to Master Narrative v1.5. Supersedes v2.3 — commit this version to docs/ in place of the v2.3 named in the Session 0 checklist. Where this document and chester-reports-architecture-v3.md disagree, architecture v3 is canonical.*
