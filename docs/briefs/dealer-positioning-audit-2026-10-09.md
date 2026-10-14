# Dealer positioning block — adversarial audit before implementation (9 Oct 2026)

| | |
|---|---|
| Status | Audit of `docs/briefs/dealer-positioning-brief-2026-10-09.md` (v1) and `tools/dealer_charts.py` against the engine as it stands on main (804e81c → 237005a), run 9 Oct 2026 in the decision chat. Deliverables A–G in order. The v1 brief is withdrawn; the v2 brief issued with this audit replaces it. |
| Evidence | Code read: `tools/exposure_compute.py`, `tools/quality_gates.py`, `tools/pin_log.py`, `daily_cascade/stack_close.py` (`scorecard_row`), `daily_cascade/weekly_sections.py` (`flags_for`, `dealer_week`), `monthly_macro/dealer.py`, `config/reporting_stack.yaml` (`dealer_flags`), `altdata/config.py`, `tools/cross_check.py`, the Dealer's Hand paper (Chapters 6–10, 17, A.1–A.3). Tests run on the box's 8 Oct 2026 SPY settled chain (`data/chains/2026-10-08/SPY_202138Z.csv`) and the 9 Oct FlashAlpha ledger. Tests not run are marked. |
| Verdict in one line | **The arithmetic is sound and already honest about what it infers; the v1 brief over-reached in three places (DEX direction, unwind direction, the scorecard's thresholds) and under-reached in two (the net-to-gross confidence measure, the OI vintage). The scorecard as designed could not have established an edge at any sample size the calendar allows; it is redesigned as a pre-registered experiment.** |

---

## A. Findings register

Severity: **S1** would mislead a decision · **S2** would mislead a reader · **S3** housekeeping. Class: **VD** verified defect · **UA** unverified assumption · **ML** methodological limitation · **OE** optional enhancement. Cost in session hours.

| # | Finding | Sev | Class | Decision impact | Cost | Disposition |
|---|---|---|---|---|---|---|
| F1 | **Net GEX is a small difference of two large masses, and its sign is therefore fragile.** 8 Oct SPY: call-gamma mass $22.2bn/1%, put-gamma mass $25.6bn/1%, net −$3.5bn/1% — **net is 7% of gross**. A 15% misattribution of put open interest flips the sign. The paper's reliability hierarchy ("the sign is the most robust output") holds only when net is large against gross; nothing in the engine or the brief prints that ratio. | S1 | ML (quantified) | High: the regime word drives the setups | 1 | **Must fix:** print `net/gross` beside every net GEX and gate the regime word on it (v2 brief §2) |
| F2 | **DEX is positive by construction under `dealers-hand-v1`** (both legs carry positive delta: 0 of 9,227 rows negative on 8 Oct; `tools/cross_check.py` already records "269 of 269"). The v1 brief's "net DEX", "delta bias (bullish/bearish)" and the outside note's "directional hedge exposure" rows would print a sign that cannot vary. | S1 | VD in the brief (the code is right; the brief misused it) | High: a reader would read direction into a constant | 0 | **Must fix:** DEX printed as hedge-book size and tenor only; "delta bias" removed; the raw-signed Σ Δ·OI (calls − puts) printed as an OI-balance figure with no directional word |
| F3 | **`unwind_direction` is constant ("dealer_buys") under the convention** (`expiration_release`, lines 874–875, and `TODO.md:298–305` say so). Figure 3's right panel and the v1 brief's "what releases and in which direction" present a tautology as a forecast. | S1 | VD in the brief/figure | Medium | 0.5 | **Must fix:** the release panel shows magnitude only ("DEX released at expiry, $bn"), the direction word and the sign are dropped; the caption says the hedge rolls off, not which way the market goes |
| F4 | **The 0DTE column is structurally stale.** Open interest is published once a day by OCC; yfinance's OI during session T is the T−1 close vintage (verified: 795 calls 24,348 in our 8 Oct 16:21 chain against 38,398 in FlashAlpha's 8 Oct-close OI feed read on 9 Oct). Same-day-listed 0DTE contracts carry near-zero OI until the next morning, so an intraday "0DTE gamma" from OI measures yesterday's positioning in today's expiry. 6b's purchased feed gives volume, not intraday OI; a volume-based "effective OI" is an estimate. | S1 | ML | High for any intraday 0DTE claim | 2 (6b) | **Must fix:** the 0DTE column is labelled "OI as of prior close"; an effective-OI estimate, if built in 6b, is printed as a separate, labelled column and never silently substituted |
| F5 | **Three things are called "put wall"**: the paper's (largest put OI, A.1 and 7.2), the engine's `put_wall` (most negative signed GEX over all strikes), `put_wall_otm` (same, OTM only — the FlashAlpha-matching one), `put_wall_gamma` (largest put-gamma strike) and `put_wall_oi` (largest OTM put-OI shelf, 500 on 8 Oct). The Weekly's `held` flag uses `put_wall`; the paper's definition would score a different level. | S2 | VD (vocabulary) | Medium: a held/failed verdict depends on which | 1 | **Must fix:** one name per definition in the renderer and the paper's glossary: *put gamma wall* (OTM, the level), *put OI shelf*, *peak put-gamma strike*; the flags name which they score |
| F6 | **The scorecard's denominators are wrong for the hypotheses.** `pinned` is scored on every session (max pain is an expiry construct; on a non-expiry session "close within 0.25% of max pain" tests nothing). `held` is `False` on a session where the wall was never approached, so "held" hit rates conflate untested with failed. `amplified` is `False` (not `None`) when the flip was not crossed, so its rate is diluted by ineligible sessions. | S1 | VD (experiment design, not code) | High: the retrospective's hit rates would be uninterpretable | 2 | **Must fix:** eligibility before outcome for every flag (v2 brief §5); `None` for ineligible, never `False` |
| F7 | **The 20-session floor and the 40-session retirement cannot establish or retire anything.** A hit rate of 0.60 on 20 sessions has a 95% interval of 0.39–0.78; on 60, 0.47–0.71; on 120, 0.51–0.68. Detecting a 15-point improvement over a 0.50 base rate at 80% power needs ≈ 170 eligible sessions per arm; with a regime split and eligibility (walls are approached on perhaps a third of sessions) that is two to three years. | S1 | ML (quantified) | High: a rule would be promoted or retired on noise | 0 | **Must fix:** rates print with a Wilson interval and n; promotion and retirement criteria are set by evidence, not session counts (v2 brief §5) |
| F8 | **Multiple testing.** Five flags × two regimes × two windows plus the synthesis rules is ≥ 20 simultaneous tests; at α = 0.05 one is expected to "work" by chance. | S1 | ML | High | 0.5 | **Must fix:** pre-registration ledger before the first scored month (the repo already has the form: `docs/ledgers/rates-driver-2026-09-30-r2-preregistration.md`); a false-discovery control across the family |
| F9 | **Overlapping observations.** Sessions are not independent (regime persists; the same OI underlies consecutive days). Hit rates computed per session overstate precision. | S2 | ML | Medium | 0.5 | Count episodes (a regime run, a wall approach) as the unit for the interval; print both session-n and episode-n |
| F10 | **Fixed-IV profile.** A ±2-point parallel IV shift moves the flip by 0.2 points and the ±1% figures by ~10%: immaterial. A sticky-delta-style skew tilt (IV rising as spot falls, 0.5–1.0 vol per 1%) moves the flip 1.2–2.0 points (0.15–0.25% of spot) and the at-spot figure from −3.5 to −6.6/−8.6bn: **material near the flip, immaterial for the slope's direction.** | S2 | ML (quantified) | Medium near the flip | 1 | Print the profile with a shaded band from the two tilt cases; the slope and the crossing direction are what the read uses, not the at-spot point |
| F11 | **`gamma_regime` prints "negative" when `net_gex` is `None`** (`stack_close.py:100–101`: `(exp.get("net_gex") or 0) > 0`). | S2 | VD (code) | Low today (SPY always computes), high if it ever doesn't | 0.25 | Fix: `None` when `net_gex` is `None` |
| F12 | **The convention caveat is not carried into the pin log columns**; the profile JSON carries it, the pin-log row does not (`convention_version` is there; the caveat text is not). | S3 | VD | Low | 0 | Accept: `convention_version` is the machine-readable form; the renderer prints the caveat once per edition |
| F13 | **Max pain is scored daily but is meaningful only at expiry** (the paper's own 7.4: "no mechanism … empirical support is weak"; A.1: "meaningful only when coincident with peak GEX"). | S2 | ML | Medium | 0 | Eligibility: expiry sessions only; and `pinned` scored against **peak-gamma strike** as the primary and max pain as the control |
| F14 | **Dividend yield q = 0 and r = 4.3% fixed.** SPY yields ≈ 1.2%; gamma barely moves, long-dated deltas move a little, the flip (near-dated gamma) does not. | S3 | ML | Low | 1 | Accept; log as a known approximation; revisit when a vendor Greek column arrives |
| F15 | **Walls are defined over all strikes** (`call_wall` = largest positive signed GEX anywhere, including below spot). Harmless on 8 Oct (790, above spot) but an in-the-money call strike can win after a sharp fall. | S2 | VD (definition) | Medium after large moves | 0.25 | Print `call_wall_otm` / `put_wall_otm` as *the* walls (they are the FlashAlpha-matching ones) and keep the all-strike extremes as "peak" figures |
| F16 | **Horizons overlap in the v1 brief** (≤ 7 d, ≤ 45 d, all are cumulative; the engine's listing buckets are exclusive). Nothing double-counts in the engine; the brief's prose could be read either way. | S2 | UA | Low | 0.5 | Define both: cumulative windows for the tables, exclusive bands (0DTE · 1–7 · 8–45 · > 45) for the bucket chart, and a reconciliation line (the bands sum to "all") |
| F17 | **Changes over time mix four causes** (spot, IV, OI, expiry roll-off). T4 prints the change; it does not say why. | S2 | OE | Medium | 4 | Later: a three-step decomposition from the two stored chains (spot at yesterday's book; IV at yesterday's book; OI and roll-off), keyed by `contract_symbol`; prints only when both chains are complete |
| F18 | **The synthesis rules in T3** ("0DTE negative, aggregate positive → intraday amplification") are hypotheses written as readings. | S1 | UA | High | 0 | Must fix: printed only as pre-registered hypotheses with their running evidence, never as a reading, until promoted (§C) |
| F19 | **Exposure-quality panel is missing from the page** though the engine computes it (`gates`: data quality, liquidity floor with reasons, IV roughness — threshold still marked provisional — OI concentration, `min_t_load_bearing`, rows skipped and why, exposure rows, `settled_0dte_excluded_rows`, `greeks_source`, `convention_version`). | S2 | OE (cheap) | Medium: the reader cannot tell a thin chain from a thick one | 1 | Adopt: one small panel per capture, printed under T1 |
| F20 | **IV-roughness threshold is provisional** (`IV_ROUGHNESS_MAX = 0.35`, "needs calibration against a real sample") and gates `data_quality: degraded`. | S3 | UA | Low | 2 | Calibrate at the first 60 stored captures; until then the panel prints the raw roughness, not only the verdict |
| F21 | **One canonical source holds**: every figure in the v1 tables and charts traces to the exposure JSON or the pin log; `net_gex_at_spot` re-prices gamma for the profile with an inline sign rather than `dealer_position()` (line 528) — same rule, second place. | S3 | VD (duplication of the sign rule) | Low | 0.25 | Fix: call `dealer_position()` so the one assumption has one call site |
| F22 | **The decision summary names setups.** The books decide (Doctrine); the block proposes; nothing writes the register. Verified in the v1 brief; kept. | — | — | — | — | Retain |

---

## B. Calculation audit

**Lineage.** yfinance chain (`altdata/sources/options_chain.py`, 16 columns, no Greeks, OI of the prior close vintage, IV per contract) → `tools/exposure_compute.load_chain` → `compute_symbol` → exposure JSON (`data/computed/<date>/SYM_*_exposure.json`) → `tools/pin_log.py` row and `dealer.scorecard_day` row (the close) → the Weekly's `flags_for` → the Monthly's retrospective. Every number the block prints is a view of the JSON or the pin-log row; the charts read the JSON and the chain (the profile).

**Formulas (lines in `exposure_compute.py`).** d1 = [ln(S/K) + (r + σ²/2)T]/(σ√T) (371); Γ = φ(d1)/(Sσ√T) (393, 426); Δ = N(d1) or N(d1) − 1 (427); vanna = −φ(d1)·d2/σ (430); charm = −φ(d1)·(2rT − d2σ√T)/(2Tσ√T) (431); q = 0; r = 0.043; T = DTE/365 floored at one hour, and the floored share of |GEX| is reported per bucket (MIN_T "must never be load-bearing"). Sign: `dealer_position` = +1 calls, −1 puts (342–345). Per strike: GEX = sign·Γ·OI·100·S (715–716), in dollars; `shares_per_1pct` = net·0.01; `dollar_gamma_per_1pct` = that ·S (773–789) — i.e. sign·Γ·OI·S²·0.01, the paper's A.2 formula and, since the 9 Oct ledger, FlashAlpha's. DEX = sign·Δ·OI·100 shares, ·S dollars (728, 792–793). Zero-gamma: the spot at which Σ sign·Γ(S*)·OI·100·S* = 0, scanned ±15% on 61 points, nearest bracket to spot, bisected 40 times (569–612); the cumulative-across-strikes crossing is kept separately as `gamma_flip_cum_strikes`. Max pain: payout-minimising strike over all open interest including DTE 0 (615–637, 1067). Settled capture (≥ 16:00 ET): DTE 0 rows excluded from every exposure aggregate, kept in OI constructs (997–1004). Buckets: 0DTE wins, then third-Friday quarterly, third-Friday monthly, ≤ 7 days weekly, else other (450–466).

**Verified by execution (8 Oct SPY chain, 9,474 rows in, 8,507 exposure rows):**
- Per-strike GEX sums to `overall.net_gex` (−447.6M) — reconciled to the dollar.
- The profile at today's spot equals `net_gex` (the dot sits on the line) — reconciled.
- Zero-gamma: one crossing in ±15% (775.46); a 601-point scan finds the same single crossing; the engine's bisection is correct and the 61-point bracket scan is adequate for a book whose profile is smooth (gamma kernels), with the caveat that a crossing narrower than 0.5% of spot could be missed — not observed.
- Definition against FlashAlpha's per-strike GEX for one expiry: ratio 1.01 median (9 Oct ledger).
- DEX dealer-hand: 0 of 9,227 rows negative — positive by construction (F2).
- Gross against net: call mass $22.2bn/1%, put mass $25.6bn/1%, net −$3.46bn/1% (F1).

**Sign-assumption sensitivity (executed).**

| Assumption | Net at spot, $/1% | Zero crossing in ±15% |
|---|---|---|
| dealers long calls, short puts (`dealers-hand-v1`) | −3.46bn | 775.46 |
| global inversion (customer-hand) | +3.46bn | 775.46 — **the level is invariant; only the regime word flips** |
| dealers short both | −47.8bn | none |
| dealers long both | +47.8bn | none |
| OTM naive, ITM inverted (a crude moneyness rule) | −1.31bn | 774.29 |

**What can and cannot be inferred from the inputs.** Observable: open interest per contract (prior-close vintage), implied volatility per contract, spot. Computable without any inventory assumption: the **call-gamma mass**, the **put-gamma mass**, their per-strike concentrations (the walls as strikes with the most call or put gamma), and the **balance level** — the spot at which the two masses are equal, which is what the "zero-gamma level" is under any symmetric convention. Assumed: which side the dealer is on, per leg. Dependent on the assumption: the sign of net GEX (the regime word), every DEX direction, VEX and CHEX directions, `unwind_direction`. The practical approach (D) prints the convention-free quantities first and the convention-dependent ones with the net-to-gross ratio as their confidence, and never prints a direction word for a quantity whose sign the convention fixes.

**Fixed-IV profile (executed).** Parallel ±2 points: flip ±0.2 points, ±1% values ±10% — immaterial. Skew tilt 0.5 / 1.0 vol per 1% (IV rising into a fall): flip +1.2 / +2.0 points; at-spot −6.6 / −8.6bn against −3.46bn; the ±1% values −19/+16 and −21/+14 against −16/+19 — the slope's sign and the asymmetry survive; the at-spot magnitude does not (F10).

**Expiration release.** Per expiry Σ sign·Δ·OI·100 (884); direction constant under the convention (F3). What is defensible: the **size** of delta hedge attached to each expiry and the **tenor** of the hedge book (figure 4). What is not: a direction for the unwind, which also assumes positions are held to expiry rather than rolled (the docstring says so at 869–872).

---

## C. Scorecard audit — the experiment as it should be run

**Unit, eligibility, outcome, base rates — per hypothesis.** Flags are scored only on eligible sessions; an ineligible session is `None`, never `False` (F6). Every rate prints as k/n with a Wilson 95% interval and the base rate beside it (F7). Regime is the **settled** profile in force during the session (the prior close's), gated by the net-to-gross ratio (F1): a session with |net|/gross below 0.10 is "indeterminate" and is its own arm.

| Hypothesis | Mechanism (falsifiable prediction) | Eligible sessions | Outcome | Base rate (same window, all eligible sessions regardless of regime) |
|---|---|---|---|---|
| **dampened** | In positive gamma dealers hedge against the move, so the realised range is below the implied one-day range more often than otherwise | positive-gamma sessions, ratio ≥ 0.10 | actual range < 0.8 × implied | share of all sessions with range < 0.8 × implied |
| **amplified / expanded** | In negative gamma the realised range exceeds the implied range more often; steeper profiles (slope at spot above its 60-session median) more so | negative-gamma sessions; the steep subset separately | actual range ≥ 1.2 × implied | share of all sessions with range ≥ 1.2 × implied |
| **call wall held** | A rally into the call gamma wall is sold by hedgers | sessions whose high came within 0.25% of the morning OTM call wall (**approached**) | close below the wall | share of all sessions that approached *any* round-number strike 1–3% above the open and closed below it (the price-action baseline) |
| **put wall held** | As 7.2 says the pure-gamma mechanism is *against* support; monetisation and vanna are for it — the prediction is weaker and the paper says so | sessions whose low came within 0.25% of the morning OTM put gamma wall | close above the wall | the mirror baseline below the open |
| **pinned** | Hedging into expiry pulls the close toward the peak-gamma strike | **expiry sessions only** (0DTE existed), both regimes | close within 0.25% of the morning peak-gamma strike; max pain as a control level | share of expiry sessions closing within 0.25% of the nearest round-number strike (the baseline a pin must beat) |
| **flip crossing** | Crossing the zero-gamma level changes the realised-vol regime | sessions where the morning flip was inside the day's range | next three sessions' realised vol above / below the prior ten sessions' | the unconditional share of three-day vol rises |

**Baselines a signal must beat** (the outside note's point, adopted): price action alone (the round-number test above), implied vol alone (the implied-range test is already relative to IV), realised vol alone (the prior-ten-session range). A flag that does not beat the simple baseline is not an edge however high its hit rate.

**Independence and multiplicity (F8, F9).** Episodes, not sessions, are the unit for the interval: a regime run counts once for the regime hypotheses; a wall approach counts once. The family of tests is pre-registered in `docs/ledgers/dealer-scorecard-preregistration-2026-10.md` before the first scored month: hypotheses, eligibility, thresholds, windows, baselines, the promotion rule — written down, dated, unchanged thereafter; a change is a new registration with a new date. The promotion rule controls the family: Benjamini–Hochberg at 0.10 across the registered tests, reported with each rate.

**Out of sample.** The stored captures begin 4 Sep 2026 (the pin log) with the scorecard rows from the stacked close's start in October; there is no history to walk forward yet. Design: the first 120 eligible sessions per hypothesis are the **formation** sample and may not promote anything; the following 120 are the **test** sample; promotion needs the test-sample interval to exclude the base rate *and* the baseline, with the formation-sample estimate in the same direction. At ~250 sessions a year and eligibility of a third for the wall tests, the first promotion decision is **late 2027** for the wall hypotheses and **late 2026 / early 2027** for the regime hypotheses (every session is eligible). The 2 Oct Doctrine ruling (first engine after 20 sessions of stored verdicts) is unaffected: that is a base rate to *register*, not an edge to trade — the engine's registration prints it as its prior, and its own N ≥ 40 paper trades remain the engine's kill criterion.

**What "useful" means.** A hypothesis is **evidence** when its test-sample interval excludes the base rate and the baseline after the family control; it is **tradable** only when the setup ledger (G.7 of the outside note, adopted as §5 of the v2 brief) shows a positive expectancy after modelled costs over N ≥ 40 setups graded against stored bars — the Doctrine's existing engine rule. Costs: SPY spreads are negligible; the modelled cost is the slippage of a market order at the signal bar's close plus one tick, recorded per setup.

**Monitoring and retirement.** Every registered hypothesis prints monthly with its running k/n, interval, base rate and baseline; a promoted hypothesis is demoted when a rolling 120-session interval includes the base rate for two consecutive months; nothing is retired on fewer than 120 eligible sessions — silence is the honest state before that.

---

## D. Revised specification — the smallest set of changes

**Must fix before the block prints a number (in 6b):**
1. Net-to-gross ratio computed and stored in the exposure JSON (`overall.gross_gex_abs`, `overall.net_to_gross`); the regime word prints only when the ratio ≥ 0.10, else "indeterminate" (F1).
2. DEX as size and tenor; no direction word; the raw-signed OI balance printed without a directional reading (F2).
3. Release panel: magnitude only (F3).
4. 0DTE column labelled "OI as of prior close"; effective-OI estimate, if built, as its own labelled column (F4).
5. One name per wall definition; the OTM walls are *the* walls; the flags say which level they score (F5, F15).
6. Scorecard eligibility before outcome, `None` for ineligible; `pinned` on expiry sessions against the peak-gamma strike; `gamma_regime` `None` when `net_gex` is `None` (F6, F11, F13).
7. Rates print as k/n with Wilson intervals and base rates; the pre-registration ledger is written before the first scored month; the synthesis rules print as registered hypotheses with running evidence, never as readings (F7, F8, F18).
8. Exposure-quality panel under T1 (F19).
9. `net_gex_at_spot` uses `dealer_position()` (F21).

**Later enhancements (Doctrine #2 or Audit #5 decide):** the change decomposition (F17, 4 h); the profile's skew band (F10, 1 h); episode-counting for intervals (F9, 0.5 h) — in the registration from the start, computed when there are episodes; IV-roughness calibration (F20); the dividend yield (F14).

**Accepted limitations, stated on the page:** the sign convention (already printed); OI vintage (new); fixed IV in the profile (new, one clause); q = 0 (in the method note).

**Removed from v1:** "net DEX" and "delta bias" rows; the release direction; the horizon-agreement *rules* as readings; the 20-session and 40-session thresholds as decision criteria.

---

## E. Test plan

| Test | Expected | Fails when | Evidence | Status |
|---|---|---|---|---|
| Per-strike sum = `overall.net_gex` | equal to the dollar | any difference | 8 Oct SPY and QQQ | **Run, passed** (9 Oct) |
| Profile at spot = `net_gex` | equal | difference > 1e-6 relative | 8 Oct SPY/QQQ | **Run, passed** |
| Single-expiry definition vs FlashAlpha per-strike | ratio 0.9–1.1 near the money | outside | 16 Oct expiry, 20 strikes | **Run, passed** (median 1.01) |
| Full-chain raw-signed DEX vs FlashAlpha | within 5% | outside | 9 Oct | **Run, passed** (1%) |
| Dealer-hand DEX sign by construction | 0 negative rows | any negative row | 8 Oct, 9,227 rows | **Run, confirmed** (F2) |
| Zero-gamma scan: 61 vs 601 points | same crossing set | a crossing found at 601 and missed at 61 | 8 Oct | **Run, passed** (one crossing both) |
| Sign-assumption sensitivity | level invariant under global inversion; regime word flips | level moves under global inversion (would indicate a bug) | 8 Oct | **Run, passed**; the "short both / long both" cases documented (F1) |
| Fixed-IV sensitivity | slope direction stable; at-spot magnitude moves | slope flips under a 1-vol tilt | 8 Oct | **Run**; slope stable, magnitude moves (F10) |
| Net-to-gross ratio | computed and stored; regime word gated | ratio missing or gate ignored | unit test on a synthetic chain with net = 0 | **Not run** — code not written |
| Scorecard eligibility | ineligible = `None`; rates exclude `None` | a `False` where `None` is due | unit test with a session whose wall was not approached | **Not run** |
| `gamma_regime` with `net_gex` `None` | `None` | "negative" | unit test | **Not run** (defect confirmed by reading) |
| Walk-forward | formation/test split as registered | promotion from the formation sample | the ledger | **Cannot run** — no history; design only |
| OI vintage | yfinance OI = prior-close vintage | — | 795C 24,348 vs 38,398 | **Run, confirmed** (9 Oct ledger) |
| Failure modes: empty chain, chain without IV, chain with all DTE 0 at a settled capture | error dicts / "no usable rows" / `flip_reason` set; no silent zeros | a number printed | `compute_symbol` on three synthetic chains | **Not run** — to be added to `validate_weekly_complete.py` |

---

## F. Implementation decision

| Part of the v1 design | Decision | Reason |
|---|---|---|
| Four tables as views of the exposure JSON | **Retain** | one canonical source; already true |
| T1 dashboard | **Modify**: add net-to-gross and the regime gate; replace "net DEX" with hedge-book size; add the quality panel | F1, F2, F19 |
| T2 key levels | **Modify**: the OTM walls as the walls; one name per definition; rank by share of gross | F5, F15 |
| T3 horizon agreement with synthesis rules | **Modify**: the matrix stays (signs, magnitudes, levels); the rules become registered hypotheses with running evidence | F18 |
| T4 changes | **Retain**; decomposition later | F17 |
| Decision summary naming setups | **Retain** | F22 |
| Figure 1 per-strike | **Retain** (OTM walls labelled) | |
| Figure 2 profile | **Retain**; skew band later | F10 |
| Figure 3 buckets + release | **Modify**: exclusive bands; release as magnitude only | F3, F16 |
| Figure 4 DEX horizon | **Retain**; caption says size and tenor, not direction | F2 |
| Figure 5 scorecard chart | **Modify**: k/n with intervals and base rates; episodes | F7, F9 |
| Scorecard: base rates, regime split, two new flags | **Modify** into the pre-registered experiment of §C | F6–F9, F13 |
| 20-session floor / 40-session retirement | **Remove** as decision criteria; the floor stays as the printing floor for counts | F7 |
| 0DTE intraday reads | **Defer** to a labelled effective-OI estimate in 6b; never from OI alone | F4 |
| Horizon-agreement rules as a daily "reading" | **Remove** until promoted | F18 |
| FlashAlpha vendor line | **Retain** (weekly) | |
| Outside note's "market direction" and "buy dip / sell rip" cells | **Not adopted** (v1 already declined) | direction is the framework's, not the block's |

---

## G. Revised implementation prompt

Issued separately as the v2 brief (`docs/briefs/dealer-positioning-brief-2026-10-09.md`, replacing v1) and the 6b paste; the paste is given only when 6b starts (week of 20 Oct), so that it reflects the Audit #4 placement. The tool `tools/dealer_charts.py` is committed now with F3 applied (release panel magnitude-only) and F21 noted for the engine.
