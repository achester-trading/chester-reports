# 6f: the market-state object v2 — specification DRAFT

**Status: DRAFT for the operator's rulings, taken in chat one decision at a time (section 9). Nothing here is built, configured or gated.** Written 23–24 Oct 2026 (session A, A60) on branch `a60-6f-spec` from `origin/chain-5` (`6fa2024`). Docs only. 6f is placed in the week of 2 Nov by Workplan v7 (`docs/workplan-v7-2026-10-16.md`, "Week of 2 Nov ... 6f"); Audit #3 sizes it at about 8 hours (`docs/chester-reports-audit-3.md`, the 6f row: "16 dimensions with transition probabilities · dial calibration · tail families (~6) with Brier · debt-cycle branch | 8 | Phase 3").

**Sources read.**
- **Code and config:** `regime.py`, `contradictions.py`, `config/market_state.yaml`, `metrics_registry.yaml`, `source_registry.yaml`, `altdata/probability_ledger.py`, `altdata/fred_history.py`, `config/prediction_markets.yaml`, `tools/decide.py`, `register/heat.py` and the object's readers. All of it as it stands on chain-5.
- **Docs and orders:** `docs/market-state.md`; `docs/chester-reports-audit-3.md` (§K and the method rows); the Enterprise Layer order of 27 Sep; the signal-triage order of 25 Sep and Batches 5 to 15.
- **Branches:** the four post-Monthly branches (a57, a58, b55, b56), read from origin.
- **Library, read only:** the Twenty-Five (Paper II, `docs/whitepapers/tail-scenarios-whitepaper.md` and `docs/tail-scenarios-25-reference.md`) and the Operating Doctrine (XVIII). No white paper was edited.

**Where the code and a document differ, the code wins** and the difference is listed in section 1.4.

---

## 1. What v1 is today, from the code

### 1.1 The object

`regime.py` computes one object per session day. It stores it under `registry_key` `market_state`, with `observed_at` set to the session and `available_at` to the compute instant, and source `derived_state`. A recompute of the same day is a new vintage of that day, not a second object.

**Identity:**

| Field | Value |
|---|---|
| `schema_version` | `market-state-v1` |
| `method_version` | `market-state-method-8` (`regime.py` `METHOD_VERSION`; the source pin is `METHOD_SOURCE_SHA = 9a9404d42ced31c6` over `regime.py` and `contradictions.py`) |
| `config_version` | `market-state-v1.10` |

v1.11, v1.12, method-9 and method-10 are retired, and `tools/validate_regime.py` group L refuses them. The next numbers are v1.13 and method-11.

**Defaults:**
- `persistence_sessions: 2`.
- `staleness_multiple: 3`: a dimension goes absent when its primary is older than three times the registry's staleness allowance for its cadence (daily 2 sessions, weekly 8, monthly 32, quarterly 95).
- `window_days: 1826`, the five-year percentile window.

**Eight dimensions, each banded on its first member (the primary):**
- The bands are the same everywhere: the first state at the 66th percentile and above, the second at the 33rd, the third below.
- The other members are evidence. Each is `supporting` if it lands in the published band and `contradicting` if not, and a dimension where no member disagrees records the literal `none found`.
- Confidence is the primary's own, lowered one step when more members contradict than support.
- Direction is the sign of the primary's rate of change times its polarity.
- A dimension can be absent for one of three reasons: no members, no observation, or a stale primary.

| Dimension | States | Primary (polarity) |
|---|---|---|
| growth | expanding / slowing / contracting | `fred.claims_4wk` (−1) |
| inflation | rising / stable / falling | `fred.breakeven_10y` |
| rates | high / mid / low | `fred.yield_10y` |
| liquidity | ample / neutral / tight | `calc.net_liquidity` |
| credit | easy / neutral / stressed | `fred.hy_oas` (−1) |
| trend | up / flat / down | `calc.trend_spy_vs_200d` |
| breadth | broad / mixed / narrow | `calc.breadth_sector_above_50d` |
| volatility | elevated / normal / subdued | `yfinance.mkt_vix` |

**Three dials:**
- **macro:** a declared lookup over growth × inflation, with nine states from `goldilocks` to `deflationary_bust`. `rates` is declared as an input but unused. The dial is absent, not `mixed`, when an input is absent.
- **vol:** VIX level bands (crisis 30, elevated 20, normal 14, subdued), plus two legs:
  - realized/implied, `calc.vol_spy_realized_20d` over VIX;
  - term structure: a champion/challenger dual run until 23 Dec 2026, with champion `calc.vx_front_ratio` on `cfe.vx1`/`cfe.vx2` and challenger `calc.vix3m_over_vix`, which is the published one.
- **gamma:** the sign of dealer gamma, read from the pin log through `altdata/grader.py`.

**Eight contradiction rows:**
- `price_vs_breadth`, `equities_vs_credit`, `long_bond_vs_hy` and `implied_vs_realized_vol` are metric pairs. Their magnitude is the z of the standardised gap against the gap's own history, with at least 30 aligned dates.
- `growth_vs_cyclicals` is a mixed pair.
- `gamma_vs_trend` is a dial pair, a state mismatch whose magnitude is `None`.
- `prediction_markets_vs_assets` is reserved (`requires: part_27_v1`).
- `narrative_vs_data` expands to one row per active story.
- A row opens after two sessions and closes on the first session that fails. A symmetric close is ruled for v1.13.
- An open row at five sessions is an exception, `report_only`.
- `implied_vs_realized_vol` also declares `also_reads: probability_ledger.tail_weight` (scenario-set prefix `tail:`). Nothing emits one, so that leg is absent.

**Persistence.** A new raw state publishes only after it holds for `persistence_sessions` consecutive computes. Until then the object carries the old state plus `pending_state` and `pending_sessions`. Its memory of itself (up to eight prior objects) is read at `computed_at`; market data is read at the session's cutoff.

**Replay.** There is no `replay` command. `tools/validate_regime.py` and `tools/validate_regime_store.py` group A recompute each stored object at its own `as_of` and `computed_at` and compare every field except `REPLAY_EXCLUDE`, which holds `computed_at`, `available_at`, `ingested_at`, `git_sha` and `config_path`. Only objects at the current config and method versions are replayed; the rest are reported as superseded. `regime backfill` skips sessions already at the current method. `regime range` reports the supportable window.

### 1.2 What reads it

| Reader | What it reads |
|---|---|
| The 16:45 close (`daily_cascade/close_report.py`) | The only writer (`compute` and `store_object`). |
| Close payload, morning anchor, `state_block.py`, `stack.py`, `stack_close.py`, `story_block.py`, `volatile_day.py` | Dimensions, dials, contradictions, exceptions, session events; the detail tables at the end of the stacked close. |
| The Weekly (`weekly_payload.py`, `weekly_sections.py`, `weekly_stack.py`) | Dimensions, dials including `vol.term_structure`, contradiction history, the macro dial's history, `method_change_at`. |
| The Monthly (`monthly_macro/payload.py`, `prose.py`, `v2.py`) | Dials, dimensions and their members, contradictions, exceptions, config and method versions. |
| The books: `register/heat.py` `regime_band` and `tools/decide.py` | The last 11 objects' `dials.macro.state`, mapped through `config/risk_limits.yaml` (`dial-to-doctrine-v1.1`, `transition_sessions: 10`); the vol and gamma dial states. |
| Packets: `tools/decide.py` `horizon_alignment` | `dimensions.trend.state` only (`aligned` / `neutral` / `counter`). |
| The Book B scanner (`altdata/book_b_scanner.py`) | `dials.vol` and `dials.gamma`, plus heat's macro band. |
| The Alpha Lab (`alpha/store.py`, `alpha/rules.py`, `config/alpha_search.yaml`) | `dials.macro.state` and `dials.vol.state` as conditioning keys, read-only. |
| `altdata/state_vector.py`, `altdata/narratives.py` | `dimensions.trend.percentile`; dimension states for the narrative rows. |

### 1.3 What v1 does not have

v1 has no calibration of any dial or dimension, no transition probability, no tail probability (the probability ledger holds none, by design of the tail list), no debt-cycle field, and no per-horizon read. `tools/calibration/` is forbidden to import `regime`.

### 1.4 Where the code and the documents differ (the code wins)

1. **Staleness.** `docs/market-state.md` §3 says `max_staleness_sessions`, and so does `regime.py`'s own docstring; the code uses `staleness_multiple × the registry allowance`.
2. **VIX term structure.** `docs/market-state.md` §4 and §9 describe the term structure as the proxy only and as "gated on the CFE Enhanced subscription". The config runs the champion/challenger dual. `source_registry.yaml`'s `cboe` entry (`altdata/loggers/vxcurve.py`) reads public settlement files on cdn.cboe.com "without authentication. No key". On the code, VIX term structure is no longer gated on a subscription; what waits is the dual run's end (23 Dec 2026) and its verdict.
3. **§5's heading.** `docs/market-state.md` §5 is headed "Three dimensions are absent"; all eight compute.
4. **The method-8 pin.** Audit #3 names it `ee0bb0593afccf35`; the code pins `9a9404d42ced31c6`. Not verified here whether a later `regime method --update` explains it.
5. **Stale docstrings.** `contradictions.py`'s docstring says v1 computes one row. `regime.py`'s lists a `print` command that does not exist.
6. **Config changelog.** It skips v1.8, which method-6's note cites.
7. **ALFRED depth.** `docs/market-state.md` §5 says no as-of history reaches behind 30 May 2026, while §9 says ALFRED "lets the backfill reach back to 2022". `altdata/fred_history.py` is built and writes first-publication `available_at` (`fred:backfill`). The box's `--all` run of 20 Oct had failures (`docs/briefs/a55-box-fixes-notes.md`), and whether the re-run completed, and what `regime range` prints now, is not verified from the laptop. Section 8 treats it as a dependency to check, not as done.
8. **Where §K lives.** The schema is in Audit #3 (`docs/chester-reports-audit-3.md` §K), not in the architecture document.

---

## 2. The eight new dimensions

**Ground rules for every proposal below:**
- **Same mechanics as v1:** bands on one primary, members as evidence, polarity with a `because` line, persistence 2, absence with reasons.
- **No composite.** A dimension is never an average.
- **Keyless, stored inputs only.**
- **Orders that bar a key keep it out.** A key whose order bars the market-state object stays out, and no member is proposed from such an order (section 7.2 lists those rules).
- **Vendor keys are out.** `vendor.*` and any FlashAlpha, Nasdaq Data Link or Massive key is out under Batch 11's "no vendor value in any flag, tell, dial, decision or engine".
- **Bands are proposals, not fitted values.** They are the session's proposals, to be ruled on (decision 3).

"Post-Monthly branches" means a57 (`a57-batch14-b1`), a58 (`a58-batch15-1`), b55 (`b55-batch14-b2`) and b56 (`b56-batch15-2`). **Every key those branches add is barred from the object by its own order:** Batch 14 F5 ("Nothing enters a composite or the market-state object"), Batch 15 §1 and the config headers that repeat it. They are listed below for completeness and are not proposed as members.

### 2.1 positioning: crowded / neutral / light

**What exists on chain-5 (keyless):**
- `finra.margin_debit` (monthly).
- `cftc.tff_lev_money_net` and `cftc.tff_asset_mgr_net` (weekly, Traders in Financial Futures: Treasuries and FX).
- `cftc.noncomm_net` (weekly, legacy).
- `levetf.aum` (daily, ProShares).
- `finra.short_interest` (twice monthly).
- `etf.*_share_flow` (daily).
- The dealer `exposure.*` keys, which are already the gamma dial's ground and so are not proposed again.

**On the branches:** b56 adds ES and NQ as instruments of the existing `cftc.tff_lev_money_*` keys (barred: `config/hf_positioning.yaml`, "no composite and no market-state object reads it"); a58 adds `sec13f.gold_etf_*` (report only).

**Missing:** S&P 500 short interest as a share of float; prime-book leverage (one dated record only); a hedge-fund performance proxy (subscription).

**Proposed:**
- Primary `finra.margin_debit`, read as its 12-month change (+1: rising margin debt is crowding).
- Members `cftc.tff_lev_money_net` on the 10-year note (+1, the basis-trade crowding read), `levetf.aum` (+1) and `finra.short_interest` on SPY (−1).
- Monthly cadence, with a staleness allowance of 32 × 3.
- Percentile bands at 66 and 33.

**Buildable** from stored keyless inputs. Its weakness is cadence: the primary prints about three weeks after month-end, so the dimension is a monthly read inside a daily object, and the Weekly will see it unchanged for four weeks.

### 2.2 sentiment: euphoric / neutral / fearful

**What exists on chain-5 (keyless):**
- `aaii.bull_bear_spread` (weekly, from the inbox).
- `chain.spy_put_call_volume` (daily, the system's own capture).
- `exposure.oi_put_call_ratio` (daily).
- `fred.uoM_sent` (monthly, UMCSENT).
- `fng.value` (crypto, daily).

`vendor.fear_greed` and `ndl.rtat10_*` need keys and are out. Voices are not a stored numeric key.

**On the branches:** none.

**Missing:** an equity fear-and-greed read that is not a vendor's.

**Proposed:**
- Primary `aaii.bull_bear_spread` (+1).
- Members `chain.spy_put_call_volume` (−1: a high put share is fear) and `fred.uoM_sent` (+1).
- Weekly cadence, percentile bands at 66 and 33.
- Contrarian use is not the object's business. The object says what sentiment is, and nothing reads "fearful" as "buy".

**Buildable.** `chain.spy_put_call_volume`'s own history begins with the capture, so its percentile window is short and it prints absent until a minimum history (proposed 252 sessions) exists.

### 2.3 valuation: rich / fair / cheap

**What exists on chain-5 (keyless):**
- `shiller.cape` (monthly).
- `index.forward_pe` (registered, `status_extra: not_yet_sourced`, so no rows).
- `yf.forward_pe` per name (daily snapshots).
- `fred.hh_equity_share` (quarterly Z.1).
- `fred.corp_profits_after_tax` (quarterly).

**On the branches:** a57 adds `fred.z1_equities_mv` (barred, Batch 14 F5). b55's CMA table stores scans only (barred, `config/cma_table.yaml`).

**Missing:** a stored equity risk premium. The excess CAPE yield of Batch 14 item 64 is computed in memory, not stored. A forward earnings yield at index level is a listed gap.

**Proposed:**
- Primary `shiller.cape` (+1: high is rich).
- Member `fred.hh_equity_share` (+1).
- An ERP member is to be added when one is stored (decision 4).
- Monthly cadence. The percentile window is the long one: CAPE's own history, not five years, because five years of CAPE is one regime.

**Buildable.** Whether the window is five years or full history changes the state materially. CAPE has sat above its long-history 66th percentile for most of the last 30 years.

### 2.4 earnings: upgrading / flat / downgrading. Not buildable yet

**What exists on chain-5 (keyless):**
- `yf.forward_eps`, `yf.trailing_eps` and `yf.analyst_count` (per-name daily snapshots).
- `calc.earnings_surprise_pct` and `calc.consensus_surprise_z.earnings` (per print).
- `events.earnings`.
- `spdji.fwd12m_op_eps` is retired (17 Oct).

**On the branches:** none.

**Missing:** an index-level forward EPS series with history. S&P DJI is withdrawn, and `index.forward_pe` is unsourced.

A breadth-of-revisions read across the stored names, the share of names whose `yf.forward_eps` rose over 20 sessions, is computable from keyless snapshots. Its history, though, starts with the snapshot capture, and the basket is the price basket, not the index.

**Proposed when buildable:**
- Primary: the 20-session revision breadth across the S&P names stored (+1).
- Member `calc.consensus_surprise_z.earnings`, the quarter's mean (+1).
- Daily cadence, bands at 60 and 40 on the share itself (absolute, not percentile).

**Waits for:** an index forward-EPS source that is public and keyless (a listed gap since Batch 12 F3), or a ruling that the basket breadth is the dimension (decision 5), plus 252 sessions of snapshots.

### 2.5 funding_stress: calm / watch / stressed

**What exists on chain-5 (keyless):**
- `calc.sofr_iorb_bp` and `calc.sofr_effr_bp` (daily).
- `fred.sofr_p99`, `fred.fin_cp_3m` and `fred.tbill_3m` (daily).
- `fred.stlfsi` (weekly).
- `ofr.fsi`, `ofr.fsi_funding` and `ofr.fsi_credit` (daily, chain-5 only). Their registry note reads "a composite of the bank-stress panel ... flags only".
- `tic.fima_repo` (weekly).
- `fred.dw_primary_credit` and `fred.fhlb_advances`.

The ST-5 funding-currency keys (`calc.jp_*`, `calc.cny_*`, `calc.deval_tell`) are barred by name in `tools/validate_st_t2_rates.py` group L, which fails on any of them in any config but `funding_currency.yaml`.

**On the branches:** none. a58's item 76 protection-demand line is a listed gap (DTCC).

**Missing:** FRA-OIS and cross-currency basis (no key found); bank CDS and AT1 (listed gaps, Batch 12 F2).

**Proposed:**
- Primary `calc.sofr_iorb_bp` (+1 is stress: SOFR printing above IORB means reserves are scarce at the margin).
- Members `fred.fin_cp_3m` less `fred.tbill_3m` (+1). This needs one new `calc.` spread, a new key, so it is a v1.13-class config change and not a reuse; see decision 6. Also `fred.stlfsi` (+1) and `tic.fima_repo` (+1).
- Daily cadence.
- Absolute bands in basis points, not percentile: stressed at 10 bp and above, watch at 0 bp and above, calm below. A spread that sat below zero for most of five years would make a percentile band call "stressed" at −3 bp.
- `ofr.fsi_funding` is not proposed while its note says "flags only".

**Buildable.** It overlaps the liquidity dimension (whose members include `fred.nfci`) and the credit dimension. The overlap is acceptable because the primaries differ, and a disagreement between them is information.

### 2.6 geopolitical: elevated / normal / quiet. Not buildable yet

**What exists on chain-5:**
- `pm.probability` and its siblings (prediction-market prices; keyless at both venues on the source registry).
- `events.headline` (news queries).

The prediction-market rights (`config/prediction_markets.yaml`) are "discovery, attention shock ... and disagreement, and nothing else. No automatic change to any scenario weight, narrative, theme or book ... Never a trigger". A dimension's state reaches the books through the macro dial's neighbours and the Weekly's tables, which is more than those rights allow.

**On the branches:** b56 adds `cyber.kev_added_week` and `cyber.nvd_critical_week` (report only; "flag for the tail register"; barred).

**Missing:** any geopolitical risk index or economic policy uncertainty index (`config/monthly_themes.yaml` lists "a geopolitical risk index", shipping and strait disruption data, and sanctions announcements as untracked). Headlines are not a level with a history.

**Waits for:** a public, keyless, daily or monthly geopolitical risk index with a long history, source-checked under the 16 Oct rule. Until then the state is `absent: not_buildable` with that reason.

### 2.7 tail: not a dimension (proposed). Not buildable yet as a dimension

**What exists on chain-5 (keyless):**
- `yfinance.mkt_skew`, `yfinance.mkt_vvix`, `yfinance.mkt_move`, `yfinance.mkt_vix9d` and `yfinance.mkt_vix3m` (daily).
- `cboe.cor1m` and `cboe.dspx`.
- `chain.skew_25d_put` and `chain.rr_25d`.
- `screen.move` and `screen.em` (the move screen).
- `vol.event_ledger`.

**On the branches:** `gold.event_ledger` and `equity.dm_drawdown_ledger` (a58), `rates.speed_event_ledger` (a57) and the `cyber.*` pair (b56). All are barred ("FLAGS ONLY: nothing here enters ... the market-state object").

The Twenty-Five's §0.2 forbids "aggregation into a score ... do not compose into a single 'tail index'". A `tail` dimension with one state is that index by another name.

**Proposed:**
- There is no `tail` dimension.
- The tail content of v2 is `tail_families[]` (section 4), one row per family, never summed.
- The protection-price read (SKEW, 25-delta put skew) is already the volatility dimension's neighbour. It is proposed as a new member of `volatility`, `yfinance.mkt_skew` (+1), not as a dimension.

The sixteen therefore becomes fifteen, and decision 2 asks whether to accept that or to build a narrow `tail_pricing` dimension on SKEW alone.

### 2.8 policy: easing priced / on hold / tightening priced

**What exists on chain-5 (keyless):**
- `calc.policy_2y_minus_effr_bp` (daily).
- `fedfunds.futures_price` (daily) and `calc.fed_mkt_gap_12m` (daily: futures-implied less the median dot).
- `calc.real_policy_rate` (monthly).
- `fred.fed_target_upper` and `fred.fed_funds`.
- `calc.market_implied_surprise_z.fomc` (per event).

The rates-attribution keys (`calc.attr_*`) are excluded by ST-3's re-scoping ("not read by `regime.py`"; group L of `tools/validate_regime.py` asserts the object is unchanged when they are written).

**On the branches:** a57's `rates.speed_event_ledger` (barred).

**Missing:** `calc.fed_mkt_gap_m1` and `_m2` (registered, never written, "NOT TRACKED (rule 30)"); `pm.implied` (reserved, written by nothing).

**Proposed:**
- Primary `calc.policy_2y_minus_effr_bp`, polarity +1 on a tightening scale.
- Absolute bands: tightening priced at +25 bp and above, easing priced at −25 bp and below, on hold between.
- Members `calc.fed_mkt_gap_12m` (+1) and `calc.real_policy_rate` (+1, the stance the market is pricing against).
- Daily cadence.

**Buildable.** It must not become the withdrawn `rates.driver` by another route. It reads only the expected policy path, not the split of yield moves into path and premium. The 25 Sep order's R28 ("one regime, sub-states not new tags") is why it is a dimension of the one object, and the 30 Sep withdrawal is why it carries no term-premium leg.

### 2.9 The eight in one table

| Dimension | Primary (proposed) | Cadence | Bands | Verdict |
|---|---|---|---|---|
| positioning | `finra.margin_debit` (12-month change) | monthly | percentile 66/33 | buildable |
| sentiment | `aaii.bull_bear_spread` | weekly | percentile 66/33 | buildable |
| valuation | `shiller.cape` | monthly | percentile 66/33, long window | buildable |
| earnings | revision breadth over the stored S&P names | daily | absolute 60/40 | **not buildable yet** (index forward EPS; 252 sessions of snapshots) |
| funding_stress | `calc.sofr_iorb_bp` | daily | absolute 10/0 bp | buildable (one new `calc.` spread for a member) |
| geopolitical | none | n/a | n/a | **not buildable yet** (no public keyless risk index) |
| tail | none: `tail_families[]` instead | n/a | n/a | **not buildable as a dimension** (the Twenty-Five forbids a tail index) |
| policy | `calc.policy_2y_minus_effr_bp` | daily | absolute ±25 bp | buildable |

Five are buildable on stored keyless inputs, and three are not.

---

## 3. Transition probabilities and dial calibration

### 3.1 The method

**Calibration is measured, never assumed.** For each dial (macro, vol, gamma) and each dimension, take the published state at session t and the published state at t + h, both read from stored objects, never recomputed with today's code. The pair is one observation.

Two things are built from the pairs:
- **The transition matrix:** for each state s, the share of sessions in s whose state at t + h was s′. The empirical P(s′ | s, h) is counted, not modelled.
- **The scored forecast:** each published object carries, for each dial, `transition_prob` (§K's field), the matrix row for its current state. When t + h arrives, the row is scored against the realised state with the multi-class Brier score, Σ over states of (p_s − 1[s realised])². A coin is the uniform row. The ledger compares the matrix against two baselines: persistence (p = 1 − ε on the current state) and the uniform row.

**Horizons:**
- 5 sessions (Book C).
- 20 sessions (Book B).
- 63 sessions (Book A's one-to-three-month horizon, the Doctrine's Allocation book).

These are the Doctrine's book horizons (Part IV) and the per-horizon reads of section 6 take them from the same place.

### 3.2 The sample before anything prints

**A row of the matrix prints only when its state has at least 30 independent starts at that horizon.** "Independent" means start dates at least h sessions apart, so a 63-session row needs about 30 non-overlapping quarters of a state. That is seven or more years of that state, which for the macro dial's rarer states (stagflation, deflationary_bust) the as-of-correct history cannot give.

Below the minimum the field prints the literal `uncalibrated (n = k of 30)`, never a number. The alternative of printing nothing hides that the read was attempted, which `docs/market-state.md` §3 ("contradicting is never empty by omission") already rules against. See decision 7.

### 3.3 What the backfilled history may and may not do

**It may supply the states.** Only objects computed as of their session, with every input read at `available_at` ≤ the session's cutoff, may count. That means objects from `regime backfill` under the current method, reading FRED rows that came from ALFRED with first-publication `available_at` (`fred:backfill`), and price rows at their own close.

**It may not do any of these:**
- Use a value revised later.
- Use an object recomputed with a later method version to stand in for an earlier one. A calibration sample is tied to one method version, and a method bump restarts the count unless the replay of the old sessions under the new method is itself as-of-correct, which is true by construction for a backfill.
- Fit the bands. Bands are ruled, then scored, and a band moved after reading the scores is a new pre-registration.
- Score a transition across a session whose object is a fault or an absence (the pair is skipped and counted as skipped).

The reach of the as-of history is the binding constraint. If ALFRED's backfill reaches 2022, the 20-session rows of the common states may reach 30 starts within the build, and the 63-session rows will not for years.

### 3.4 The ledger rows it adds

The scored forecasts go into the existing probability ledger (`altdata/probability_ledger.py`), not a new table. The ledger already has immutable forecasts, resolve-once and `brier = (p − outcome)²` per binary row. A multi-class row is written as one binary row per state of a scenario set, which the ledger's `coherence()` check already holds to a sum of 1.

**Each row:**

| Field | Value |
|---|---|
| `source` | `market_state` |
| `scenario_set` | `state:<dial or dimension>:<h>s:<session>` |
| `claim` | `<dial> is <state> at <session + h>` |
| `probability` | The matrix row entry, clipped to (0.01, 0.99) because the ledger refuses certainty (rule 6c-3) |
| `horizon_date` | The session h sessions on |
| `resolution_criterion` | `the published state of <dial> on the market_state object for <horizon_date>, latest vintage` |
| `method_version` | `brier-v1` |
| `emitted_by` | `regime:method-11` |

**Volume.** 3 dials × 3 horizons × up to 9 states is about 81 rows a session for the dials alone. Adding dimensions would multiply it by six. Decision 8 proposes dials only, at first, with dimensions' matrices computed and printed but not ledgered.

**Uncalibrated rows are never ledgered.** A row is ledgered only when it prints.

---

## 4. Tail families

The Twenty-Five (Paper II) groups its scenarios into seven mechanism families. §K asks for "~6" `tail_families[]`, each `{family, state, probability, brier_to_date}`. The proposal keeps the paper's seven, because merging two would be the system inventing an equivalence the paper did not draw.

**Probabilities:**
- **No family has a probability source today.** The probability ledger carries none for the tail list "by design".
- **Prediction markets cannot supply one.** Their rights are discovery, attention shock and disagreement only, and `scenario_map: {}` is empty on purpose ("a mapping no one wrote would be the system inventing an equivalence").
- **So every family's `probability` is `none`, with that reason,** until either a calibration-archive gate is met (`config/prediction_markets.yaml`: 90 live snapshot days, 20 qualifying shocks, venue leads assets net of costs, two consecutive monthly calibration parts) and a ruling grants confidence modification, or a ruled per-family source exists.

**State.** What a family can carry today is a `state`: `watch` when any of its scenarios' first-mover series named in `docs/tail-scenarios-25-reference.md` is past its declared tripwire, otherwise `quiet`.

**Rights.** Rows are never summed across families (§0.2). Rights are **report-only**: no book, packet, dial or engine reads `tail_families[]`. The Doctrine's §5.3 trust matrix ("Watchlist for D hedges") is the ceiling of what a later ruling could grant.

| Family (the Twenty-Five) | Scenarios | Tripwire inputs stored today (examples, by key) | Probability source | Brier |
|---|---|---|---|---|
| A: Funding, duration and plumbing | 1, 2, 9, 11, 19 | `calc.sofr_iorb_bp`, `fred.yield_30y`, `tic.fima_repo` | none | none until a probability exists |
| B: Credit and the mandate machine | 5, 6, 14 | `fred.hy_oas`, `fred.ccc_oas` | none | none |
| C: Concentration and the buildout | 3, 20 | `calc.breadth_rsp_over_spy` | none | none |
| D: Physical shocks and geopolitics | 7, 8, 12, 17 | `fred.brent`, `pm.probability` (attention shock only) | none | none |
| E: Policy legitimacy and the inflation path | 10, 15, 16 | `fred.breakeven_5y5y`, `calc.fed_mkt_gap_12m` | none | none |
| F: Settlement and money architecture | 4, 18, 13 | gold against real yields (`yfinance.mkt_gold_front`, `fred.tips_10y`) | none | none |
| G: The price-insensitive buyer class | 21–25 | `levetf.aum`, `etf.*_share_flow` | none | none |

The tripwire per scenario is the paper's own and is read, not reinvented. Where the paper names a first mover the store does not hold, the family's row says which. `brier_to_date` prints `none: no probability emitted`. Once a probability exists, Brier is scored on the family's binary "a scenario in this family reaches its Current-state 'active' line within 63 sessions", resolved against the paper's own active line, and that criterion is ruled before the first emission (decision 10).

---

## 5. debt_cycle_branch

**The two branches.** Architecture v3 §31.2 defines two mutually exclusive branches with shared antecedents and opposite instrumentation:
- **Deflationary liquidation.** Tell: "Falling inflation with rising real yields; currency strengthening".
- **Inflationary repression.** Tell: "Nominal yields capped below inflation; persistent negative real yields; gold rising against real yields".

§K's field is `{state: none|deflationary|inflationary, confidence, observables}`.

**The inputs it names.** debt/GDP, structural deficit, net interest/revenue, foreign-official absorption share, term premium when growth falls, real yields against inflation, and gold against real yields. It specifies them "read together as one mechanism state ... `regime.debt_cycle_state`, `observation_type: inferred`".

**What is stored (keyless):**
- `calc.deficit_ttm_pct_gdp` and `calc.r_minus_g_*`;
- `fiscaldata.mspd_*`;
- the `tic.flow_*` official lines;
- `fred.tips_10y` and `fred.breakeven_10y`;
- `yfinance.mkt_gold_front`;
- `fred.term_premium_kw`.

The term premium is barred from the object by ST-3, as the rates-attribution split.

**What decides between them: nothing ruled.** Paper XXVII ("Debt Cycles, Regimes, and Environments") is unwritten; its numeral is reserved and its brief is `docs/briefs/phase-2-briefs-xxv-xxvii.md`. The twelve diagnostic questions (its chapter 5) that would locate the economy on the cycle do not exist yet. The brief says the lenses are read as a union, "one lens among several", and a session that wrote the decision rule tonight would be writing XXVII's conclusion before XXVII.

**Verdict: not buildable yet.** The field prints `state: none`, `confidence: none` and the reason `awaits Paper XXVII's diagnostic (the rule that decides the branch)`. Its observables block prints the stored inputs above as levels with percentiles, read only.

Read-only display is safe: §31.2 says the sizing consequence (duration is the wrong hedge for the inflationary branch) is "recorded as a rule so the choice is not made under stress". That rule is the Doctrine's to write, not 6f's. See decision 11.

---

## 6. Per-horizon reads for the Enterprise Layer

**What the order names.** The Enterprise Layer order (27 Sep) names two fields:
- `horizon_alignment`, which exists today and is computed at entry in `tools/decide.py` from `dimensions.trend.state` for the packet's session;
- `alignment_weekly`, "added at 6f when the state object carries per-horizon reads; not before" (§3.1 EL-1, and the gated-items table: "`alignment_weekly` | 6f (state object v2)").

Its principle R-7: "The state object holds the market view per horizon and never collapses them." DTH §II's strategic view "is the trend dimension now and the per-horizon reads at 6f; it is a prior ... never a command" (§7).

**No code for `alignment_weekly` exists**, and nothing prints it as pending.

**Proposed per-horizon reads: a new `horizons` block on the object, one entry per book horizon, each a read of the trend dimension at that horizon's own length.**

| Field | Definition | Stored source |
|---|---|---|
| `horizons.daily.trend` | up / flat / down from `calc.trend_spy_ma20_slope`'s sign and percentile bands (66/33) | existing key |
| `horizons.weekly.trend` | up / flat / down from `calc.trend_spy_vs_50d` (66/33) | existing key |
| `horizons.monthly.trend` | up / flat / down from `calc.trend_spy_vs_200d` (66/33): today's trend dimension primary | existing key |
| `horizons.<h>.since`, `.pending_state`, `.percentile` | as for a dimension, with persistence 2 at every horizon | object |
| `horizons.<h>.transition_prob` | section 3's row at that horizon's h (5, 20, 63), or `uncalibrated (n = k of 30)` | object |

All three are existing members of the trend dimension, so no new key is needed.

**Packet fields.** Fields written to the packet at entry, recorded and never recomputed:
- `horizon_alignment`, unchanged: the trend dimension, which stays the monthly read.
- `alignment_weekly`: the packet's direction against `horizons.weekly.trend`, `aligned` / `neutral` / `counter`, with the same four `neutral` cases `decide.py` already handles (no object readable, no object stored, the read absent, flat or unsigned direction).
- `alignment_daily`: proposed, but **not named by the order**. Decision 9 asks whether to add it or keep to the order's one field.

**Other effects:**
- **The register.** It gains the `alignment_weekly` column, beside `HORIZON_ALIGNMENTS` in `register/store.py`. That is a register schema change, which is the operator's to deploy.
- **The Quarterly.** Its table of graded packets by `horizon_alignment` (DTH §XXIII's test) gains a second split by `alignment_weekly`.
- **Prior, never a command.** Nothing refuses a counter-aligned packet.

---

## 7. Rights and boundaries

### 7.1 What may read v2

**The existing readers keep reading exactly what they read** (section 1.2). v2 is additive: no field v1 publishes changes meaning, name or band. This makes the build safe while v1 runs.

**Allowed, report-only:**
- **New dimensions:** the close's detail tables, the Weekly and the Monthly may print them.
- **`tail_families[]`, `debt_cycle_branch` and `transition_prob`:** report-only for every reader.

**Not allowed without a filed ruling:**
- **New dimensions:** `register/heat.py`, `decide.py`'s band and the Book B scanner may not read them.
- **The macro dial:** keeps its growth × inflation table. A new dimension entering the dial is a dial change and a Doctrine question (the Operating Doctrine's §5.2: the dials act multiplicatively on size).
- **The Alpha Lab:** may add a new dimension to its conditioning keys only through `config/alpha_search.yaml`, under its own pre-registration. The object never reads the lab.

### 7.2 The rules that keep items out of the object

Each stands, and v2 is written so that none needs lifting:

1. **The 25 Sep order:**
   - R28: rejected is "any second regime, cell or tag computed outside the market-state object".
   - §1.10, "One regime": no item computes or renders a regime of its own; regime-like reads become declared members, sub-states or contradiction rows of the object.
   - §1.7: no item enters the Monthly or the Top & Bottom composite.
   - The order-wide line: "No change in any composite score, dial or dimension state ... except the new `rates.driver` sub-state", which was withdrawn on 30 Sep.
2. **The `rates.driver` withdrawal (30 Sep):** "The object has **no** rates sub-state". `altdata/rates_attribution.py` is not read by `regime.py`, and `tools/validate_regime.py` group L asserts the object is unchanged when the attribution is written. The redesign needs a fresh pre-registration.
3. **The 25 Sep §2.2.2 rows:** `carry_vs_vol` and `fix_vs_offshore`, "declared, computed, no rights".
4. **The 25 Sep §2.3.6 and MW-2 / R9:** `calc.neg_beta_share_*` is a conditioner only, and no `calc.prl_*` path reaches a dial or dimension.
5. **ST-5, held by `tools/validate_st_t2_rates.py` group L:**
   - the nine funding-currency keys and the two candidate rows appear in no config but their own;
   - `regime.py` and `contradictions.py` import nothing of ST-5;
   - every ST-5 key is `trigger_eligible: false`.
6. **Batch 11 §1:** "Nothing outside the market-state object computes a regime" and "No vendor value in any flag, tell, dial, decision or engine". Item 53 dropped the VIX regime sub-index as "a second volatility regime". The `vendor.*` keys are "never lensed".
7. **Batches 5 to 13:** "No composite weight(s)". Batch 12 items 59 and 60 are flags only. Batch 13: "Report only. No score, no composite".
8. **Batch 14 F5:** "Nothing enters a composite or the market-state object" (items 62–71: `rates.speed_event_ledger`, the `fred.ppi_*` lines, `fred.z1_equities_mv`, `fred.households`, the fragility and air-pocket flags).
9. **Batch 15 §1:** "No composite weights change. Rights are flags and report lines only". Items 72 (report), 73 (flags: `gold.event_ledger`, `equity.dm_drawdown_ledger`, `fred.nikkei225`), 74 and 76 (flags), 77 and 78 (report).
10. **Config headers that repeat the rule:** `config/capex_chain.yaml`, `config/attribution.yaml` and `config/releases.yaml` on chain-5; `config/fragility.yaml` (a57); `config/gold_event.yaml` and `config/dm_drawdown.yaml` (a58); `config/cma_table.yaml` (b55); `config/hf_positioning.yaml` and `config/cyber_pressure.yaml` (b56).
11. **The prediction-market rights:** discovery, attention shock and disagreement, never a trigger. The `prediction_markets_vs_assets` row stays reserved.
12. **The Twenty-Five §0.2:** no tail index, no sizing off a tripwire.

**The gate that holds it.** v2's build adds a check, in `tools/validate_regime.py`, that the market-state config names no key whose registry entry or config header carries a market-state bar. Today the bar is prose in orders and headers. The gate would need a machine-readable field (proposed: `market_state: barred` in the registry, set on every key the orders above cover) and a one-off seeding pass (decision 12).

### 7.3 Method version, replay, and v1 during the build

**Version bumps:**
- v2 is **config v1.13 → v2.0 and method-11**, one bump each, both new numbers. Retired numbers stay retired.
- `schema_version` becomes `market-state-v2`. Readers that check the schema string, if any, are listed by the build's first step.

**Replay:**
- After the bump, `regime method --update` pins the new source hash, and `regime backfill` recomputes every session in the supportable range under method-11.
- The replay gate then replays method-11 objects only, and reports method-8 objects as superseded, as it does today.
- The method-8 objects stay in the store as earlier vintages. A calibration sample (section 3) is drawn from one method only.

**v1 during the build.** The build happens on a branch, with v1 at method-8 on main computing every evening. v2 lands on main as a single merge, inside the windows, after a dry backfill on the box writes method-11 objects for the range into a scratch store (the operator's) and the replay gate passes there.

The `symmetric close` ruling for v1.13 rides the same bump, because two config bumps in a week would split the calibration sample twice.

---

## 8. The work order

| Tranche | What | Hours | Depends on | Week of 2 Nov? |
|---|---|---|---|---|
| **0. Checks** | **On the box (the operator's):**<br>• what `regime range` prints;<br>• whether ALFRED's `--all` backfill completed after the a55 fix;<br>• how many as-of-correct sessions exist per dial state.<br>**On a branch:**<br>• the readers that check `schema_version`. | 1 | the box | yes |
| **1. Schema and the five buildable dimensions** | • The five buildable dimensions (positioning, sentiment, valuation, funding_stress, policy) and the SKEW member of volatility.<br>• Absent rows for earnings and geopolitical with their reasons.<br>• `horizons{}` (section 6).<br>• config v2.0, method-11, the symmetric close.<br>• `validate_regime` groups for each new dimension, on fixtures. | 3 | rulings 1–6; chain-6 on main (so the registry and the FRED pull it reads are the merged ones) | yes |
| **2. Calibration** | • The transition counts over stored objects.<br>• The `uncalibrated (n = k of 30)` rendering.<br>• The ledger writer for dial rows.<br>• A gate that proves a calibration read uses no object computed after its own session. | 2 | Tranche 1; tranche 0's answer on history depth; rulings 7–8 | yes, if Tranche 1 lands by Wednesday |
| **3. tail_families and debt_cycle_branch** | • Seven rows of state and tripwire.<br>• `probability: none` with reasons.<br>• The debt-cycle observables block with `state: none`. | 1.5 | Tranche 1; rulings 10–11 | yes |
| **4. alignment_weekly** | The register column, `decide.py`'s second field, the Quarterly split. | 1.5 | Tranche 1; ruling 9; a register schema change the operator deploys | likely the week of 9 Nov |
| **5. The bar gate** | The `market_state: barred` field, its seeding, the check in `validate_regime`. | 1 | ruling 12 | yes |
| **Later** | • earnings when an index forward-EPS source exists;<br>• geopolitical when a risk index is source-checked;<br>• tail probabilities when the PM calibration gate and a ruling allow;<br>• debt_cycle_branch's rule when Paper XXVII is written;<br>• the VIX term-structure verdict when the dual run ends (23 Dec 2026). | n/a | as named | no |

**Total:** about 10 hours against Audit #3's 8. The difference is the bar gate (1 hour) and `alignment_weekly` (1.5 hours), which the audit row does not name.

**Dependencies, stated plainly:**
- **ALFRED vintages** gate the calibration's depth, not its build.
- **The CFE subscription no longer gates VIX term structure.** The code reads Cboe's public files, and section 1.4 item 2 records the difference.
- **chain-6** gates the merge, not the branch work.

---

## 9. Decisions for the operator

Each is a choice between named options, with a recommendation. They are written to be taken one at a time.

**1. How many dimensions v2 adds now. (a) the five buildable ones now, the other three absent with reasons; (b) wait until all eight are buildable; (c) the five now and drop the other three from the plan.** Recommend (a). The five rest on stored keyless series and the object already knows how to say "absent, and why". Waiting for a geopolitical index or an index forward-EPS source could take months and holds back calibration, which needs time more than anything. Dropping the three would lose the record that they were wanted.

**2. The tail dimension. (a) no tail dimension: tail content is `tail_families[]` only and SKEW joins volatility as a member; (b) a narrow `tail_pricing` dimension on `yfinance.mkt_skew`.** Recommend (a). The Twenty-Five's §0.2 forbids a single tail index, and a dimension with one state is that index whatever its primary. SKEW as a member of volatility keeps the information, as a contradiction when protection is bid while VIX is low, without making a tail verdict.

**3. Band form for the new dimensions. (a) percentile bands (66/33) where the series has no natural zero, absolute bands where it does (funding_stress in bp, policy in ±25 bp, earnings breadth 60/40); (b) percentile bands everywhere, as v1.** Recommend (a). A spread that sat below zero for most of five years would call "stressed" at −3 bp under percentile bands. The vol dial already uses absolute VIX bands for the same reason: some levels mean something on their own.

**4. Valuation's window. (a) the series' full history; (b) five years, as every v1 dimension.** Recommend (a). Five years of CAPE is one regime, so a five-year percentile says only where valuation sits inside the current regime and would flip "cheap" after any correction from a high. The long window says what a valuation read is for. The difference should be printed alongside, which the dual-window lens already does elsewhere.

**5. Earnings at index level. (a) not buildable yet: wait for a public keyless index forward-EPS source; (b) build it now as revision breadth over the stored S&P names, labelled as a basket proxy.** Recommend (a). The basket is the price basket, not the index, and its snapshot history is short. A proxy dimension would print states with a percentile window too short to mean anything and would teach readers to trust it. (b) is defensible if the label is printed on every state, but it should be ruled, not drifted into.

**6. funding_stress's CP member. (a) add one new `calc.` series, financial CP less the 3-month bill, as a stored member; (b) members only from existing keys (`fred.stlfsi`, `tic.fima_repo`).** Recommend (a). The CP-bill spread is the classic funding read and both legs are already pulled keyless from FRED. One derived series with its registry entry is a small, visible change, and it keeps the member list from leaning on a weekly composite index (`fred.stlfsi`) for the daily read.

**7. What prints before calibration. (a) `uncalibrated (n = k of 30)`; (b) nothing.** Recommend (a). The object's own rule is that an empty field must not be mistaken for an empty result ("contradicting is never empty by omission"). Printing the count tells the reader how far the read is from having an error bar, and it costs one line.

**8. What the ledger takes. (a) dial transition rows only, at three horizons, once a row is calibrated; (b) dials and every dimension; (c) nothing ledgered until Audit #4.** Recommend (a). The dials are what the books read, so they are what needs grading. Dimensions would multiply the rows about six-fold for reads nothing acts on, and their matrices can still be printed in the Monthly without being ledgered.

**9. Per-horizon fields on the packet. (a) `alignment_weekly` only, as the order names; (b) `alignment_weekly` and `alignment_daily`.** Recommend (a). The order names one field and DTH §XXIII's test needs one split to start. A daily alignment is close to the packet's own entry signal for Book C and would mostly measure itself.

**10. Tail-family probabilities. (a) `probability: none` for every family until the prediction-market calibration gate is met and a ruling grants confidence modification; (b) a ruled per-family source now, from the tail register's hand scores.** Recommend (a). The hand scores are judgment, not a forecast with a criterion, and the ledger refuses a row without a resolution criterion for a reason. Brier on a hand score would grade the operator's guesses, not the system's.

**11. debt_cycle_branch. (a) `state: none` with the observables printed read-only, the rule left to Paper XXVII; (b) a provisional rule now from §31.2's tells (falling inflation with rising real yields reads deflationary; negative real yields with gold rising against them reads inflationary).** Recommend (a). §31.2's tells are descriptions of each branch, not a test that separates them early: both branches share antecedents, which is the hard part. A provisional rule would get written into the Doctrine's hedge choice before the paper that is meant to justify it.

**12. The bar gate. (a) add a `market_state: barred` registry field, seeded from every order that bars the object, and a `validate_regime` check; (b) keep the bars as prose in orders and config headers, as today.** Recommend (a). Today one gate (ST-5's group L) holds the rule mechanically for nine keys, and A58's own build tripped it by naming them in a new config. Every other bar is a sentence a future session has to find. A field and a check make v2's member list provably clean.

---

*Draft only. Nothing in sections 2–8 is built until the decisions above are taken.*
