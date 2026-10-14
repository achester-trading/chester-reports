# Dealer positioning — the tables, the charts, the commentary and the scorecard (brief v2, 9 Oct 2026)

| | |
|---|---|
| Status | **v2, after the adversarial audit of the same day** (`docs/briefs/dealer-positioning-audit-2026-10-09.md`); replaces v1, which is withdrawn. Placed by Audit #4 under Part V; builds inside **6b** as the dealer block, with the scorecard beside EL-12's engine registration. |
| Owner | Ari Chester |
| Source of every figure | The engine's exposure JSON per capture per symbol (`tools/exposure_compute.py`, `dealers-hand-v1`). Every table and chart is a view of it; nothing recomputes. |
| Captures | 16:10 settled today (DTE 0 excluded by rule); 09:45 and 12:30 with 6b, plus the 5–15-minute SPY recompute. Open interest is the **prior close's vintage in every capture** (OCC publishes once a day): an intraday capture carries today's IV and spot on yesterday's OI. |
| Charts | `tools/dealer_charts.py` (committed with this brief; release panel is magnitude-only per audit F3). `daily_cascade/charts.py` imports its `draw_*` functions when the block lands. |
| Hours | ≈ 19 h in 6b: engine additions 2, tables and quality panel 6, charts wired 2, scorecard and pre-registration 6, Weekly/Monthly wiring 3. |

## 1. What the page may and may not say

Printed first, as convention-free quantities: the **call-gamma mass** and the **put-gamma mass** ($ per 1%), their per-strike concentrations, and the **balance level** — the spot at which the two masses are equal, which is the zero-gamma level under any symmetric convention. Printed second, as convention-dependent quantities with their confidence: net GEX and the regime word, gated by the **net-to-gross ratio** (`overall.net_to_gross`, new): below 0.10 the regime prints "indeterminate (net is x% of gross)". The sign convention prints once per edition; "inferred, not observed" stays on every dealer table.

Never printed: a direction for DEX (positive by construction under the convention — it is the **size and tenor of the hedge book**); a direction for the expiry roll-off (the same); "support" or "resistance" as facts; the horizon rules of §3 as readings before they are promoted (§5); a 0DTE gamma figure without the words "OI as of prior close".

## 2. The tables (views; horizons by days to expiry)

Cumulative windows for the tables — **0DTE · ≤ 7 days · ≤ 45 days · all** — as roll-ups of the engine's listing buckets by DTE (`horizon_windows` in `config/reporting_stack.yaml`; the engine's buckets stay as stored). Exclusive bands for the bucket chart — 0DTE · 1–7 · 8–45 · > 45 — which sum to "all"; the renderer prints the reconciliation. At a settled capture the 0DTE column prints "settled — excluded".

**T1 — Dashboard** (every capture). Rows: call-gamma mass, put-gamma mass, net GEX ($/1%) with net-to-gross, regime (gated), zero-gamma level and its distance from spot, OTM call wall, OTM put gamma wall, hedge-book size (dealer-hand DEX, $bn) with the ≤ 7-day share, the raw-signed OI balance (Σ Δ·OI, calls − puts, no directional word), spot's distance to each level. Columns: the four horizons. Under it, **the quality panel**: capture time and kind, `convention_version`, `greeks_source`, rows in / exposure rows / rows skipped and why, `settled_0dte_excluded_rows`, data quality and the liquidity-floor reasons, IV roughness (raw figure and the provisional verdict), OI concentration (effective strikes), `min_t_load_bearing`, OI vintage ("prior close"). Then the three sentences of §4.

**T2 — Key levels** (the close: all expiries; the Weekly: one per horizon). Rows: OTM call wall, secondary call concentration, zero-gamma, spot, secondary put concentration, OTM put gamma wall, peak-gamma strike, max pain (expiry sessions only; otherwise "not an expiry"). Columns: strike, call-gamma and put-gamma at the strike, distance from spot, rank as share of **gross**, and a conditional reading in the Dealer's Hand's words. **One name per definition** (audit F5): *OTM call wall* and *OTM put gamma wall* (the levels; FlashAlpha-matching), *peak put-gamma strike*, *put OI shelf*; the flags in §5 say which level they score. The all-strike extremes print as "peak" figures, not walls.

**T3 — Horizon matrix** (the close as lines; the Weekly as a table). Per horizon: gamma sign with net-to-gross, magnitude against the series' own five-year percentile, nearest major level and distance, implied one-day range. No synthesis sentence until a registered hypothesis is promoted (§5); until then the matrix is followed by one line: "registered hypotheses: n, none promoted".

**T4 — Changes since the equivalent capture** (every capture; 16:10 vs the prior 16:10, 09:45 vs the prior 09:45; "no equivalent capture" otherwise). Rows: call mass, put mass, net GEX and net-to-gross, zero-gamma, the two OTM walls, hedge-book size, peak-gamma strike. Later (Doctrine #2 or Audit #5): the three-step decomposition — spot at yesterday's book, IV at yesterday's book, OI and roll-off — from the two stored chains keyed by `contract_symbol`.

**The decision summary** (the close and the 09:45 slot): regime (gated) and distance to the flip; the two walls; **the setups whose conditions hold** from `config/setups.yaml` (`c_pin_fade` on an expiry session in positive gamma near the peak-gamma strike; `c_negative_gamma_continuation` after confirmation through a level in negative gamma; `d_forced_flow` on expiry and release days), each with the level, the invalidation and the time stop the setup requires; "no setup" when none holds. The books decide; the block proposes; nothing writes the register.

## 3. The charts

| Figure | Where | Note |
|---|---|---|
| 2 — gamma profile across spot | the close (its one dealer chart), the Weekly, the Monthly | the regime, the distance to the flip and the asymmetry; later, a shaded band from a ±0.5-vol skew tilt (audit F10) |
| 1 — gamma by strike with the OTM walls | the Weekly, the Monthly; the 09:45 slot after 6b | where the gamma sits and in which hand |
| 3 — exclusive bands and the hedge rolling off by expiry | the Weekly, the Monthly | size per expiry; no direction |
| 4 — hedge book by horizon | the Monthly | tenor |
| 5 — the scorecard | the Weekly, the Monthly | k/n with intervals, base rate and baseline per registered hypothesis |

Each figure is stamped with the capture time, "settled" or "intraday", and "OI as of prior close".

## 4. The commentary

Three fixed sentences per capture, model-written behind the numeral and flag-word audits: (1) regime with net-to-gross and the distance to the flip, and the ±1% asymmetry from the profile; (2) where the gamma concentrates — the two OTM walls, the peak-gamma strike, which expiry carries them, and the size rolling off at the next expiry; (3) the setups whose conditions hold, or none, and the level that invalidates the read. At the Weekly a fourth: the week against the Monday read, from the scorecard rows, with the registered hypotheses' running evidence. The words "pinned", "held", "amplified", "dampened" appear only where the scorecard's flag for that session is True (the existing flag-word audit, extended to the two new words).

## 5. The scorecard — a pre-registered experiment

The close stores one `dealer.scorecard_day` row per session; the Weekly computes the flags; the Monthly's retrospective prints them. This brief changes **what is eligible, what is a base rate, and what counts as evidence** (audit C), not where the rows live.

1. **Pre-registration first.** Before the first scored month, `docs/ledgers/dealer-scorecard-preregistration-2026-10.md` records every hypothesis: mechanism, eligibility, outcome, window, base rate, price-action baseline, the formation/test split and the promotion rule. Dated, unchanged thereafter; a change is a new registration.
2. **Eligibility before outcome.** *dampened* and *amplified / expanded*: regime sessions (net-to-gross ≥ 0.10), outcome against 0.8× / 1.2× the implied one-day range; *call wall held* and *put wall held*: sessions that **approached** the morning OTM wall within 0.25%, outcome the close inside it, baseline the round-number test; *pinned*: **expiry sessions only**, against the peak-gamma strike with max pain as the control, baseline the nearest-round-number test; *flip crossing*: sessions whose range contained the morning flip, outcome the next three sessions' realised vol against the prior ten. An ineligible session is `None`, never `False`; `gamma_regime` is `None` when `net_gex` is `None`.
3. **How rates print.** k/n, a Wilson 95% interval, the base rate and the baseline beside it; sessions and episodes both counted (a regime run or a wall approach is one episode). The printing floor stays at 20 scored sessions for counts; **no rate is a decision** below 120 eligible sessions.
4. **Promotion.** The first 120 eligible sessions per hypothesis form; the next 120 test; promotion needs the test interval to exclude both the base rate and the baseline after a Benjamini–Hochberg control at 0.10 across the registered family, with the formation estimate in the same direction. A promoted hypothesis may then be printed as a reading in T3 and is demoted when a rolling 120-session interval includes the base rate for two consecutive months.
5. **Tradable is a further step**: the setup ledger (a hypothesis's setups graded against stored bars with a modelled cost — a market order at the signal bar's close plus one tick) over N ≥ 40 setups, the Doctrine's existing engine rule. The scorecard's base rates are what EL-12's engine registers as its prior; they are not an edge.
6. **The vendor line** (FlashAlpha, weekly) prints in the Weekly's Mechanics.

## 6. Engine additions (small, in 6b)

`overall.gross_gex_abs` and `overall.net_to_gross`; `net_gex_at_spot` calls `dealer_position()` (audit F21); walls named per §2 in the JSON keys the renderer reads (`call_wall_otm`, `put_wall_otm` are *the* walls); `scorecard_row` fixes (`gamma_regime` `None`; eligibility fields: `wall_approached_call`, `wall_approached_put`, `is_expiry_session`, `flip_in_range`); failure tests for an empty chain, a chain without IV and a settled capture whose rows are all DTE 0, in `validate_weekly_complete.py`; the IV-roughness threshold calibrated at the first 60 stored captures.

## 7. Not built, on purpose

Strike charts per expiry; a "market direction" cell; any directional reading from DEX, VEX, CHEX or the roll-off; synthesis rules as readings before promotion; an intraday 0DTE gamma from OI alone; any order, alert or register write; cross-symbol comparisons in raw dollars.

## 8. Build order inside 6b

1. engine additions and tests (2 h) → 2. `horizon_windows`, T1 with the quality panel, T4 (3 h) → 3. T2 and the decision summary (2 h) → 4. charts wired (2 h) → 5. the pre-registration ledger, scorecard eligibility fields and the rate printer with intervals (6 h) → 6. T3 matrix, Weekly and Monthly wiring, figure 5, the vendor line (4 h).
