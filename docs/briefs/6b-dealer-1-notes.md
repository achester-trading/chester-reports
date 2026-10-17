# 6b part 1: the dealer engine's additions, T1, T4, T2 and the decision summary (session A, 17 Oct 2026)

**Merge order: after the st-r5 line, in the second stitched chain.** Branch `6b-dealer-1` is cut from the tip of `st-r5-audit` (`acd3ff9`), so it carries `st-r5-rates`, `st-r5-index`, `st-r5-t1-rest`, `st-r5-fixes` and `st-r5-audit`, and merges after them. Branch-only: nothing merged, deployed or run on the box. Session B's 6e line (`6e-releases`, `6e-digital`), Batch 4 Tranche A, `post-friday-fixes` and Monday's chain were not touched.

**The spec** is `docs/briefs/dealer-positioning-brief-2026-10-09.md` (v2), ratified on 16 Oct 2026. This part is the brief's build steps 1 to 3:
- the engine additions and their tests;
- `horizon_windows`, T1 with its quality panel, and T4;
- T2 and the decision summary.

Charts, the three sentences, the scorecard ledger and the capture units are part 2. T3, the Weekly and Monthly wiring, the vendor line and the vendor writer are part 3.

## The rulings this applies (16 Oct)

- **The convention-free quantities print first:** the call-gamma mass, the put-gamma mass and the zero-gamma (balance) level. Net GEX and the regime word print second.
- **The regime word is gated** on net-to-gross at or above **0.10**. Below that it prints "indeterminate (net is x% of gross)".
- **"inferred, not observed"** heads every dealer table, and the sign convention prints once per edition, as the Mechanics section's note.
- **The brief's "never printed" list (section 1) and "not built, on purpose" list (section 7) hold.** The gate reads every printed string for them (group G).
- **The block proposes; the books decide.** `daily_cascade/dealer_block.py` imports no register, ledger, order path or network library and writes nothing (gate group J).

## 1. The engine additions (`tools/exposure_compute.py`)

**Already in the code before this branch** (dealer audit F1 and F21, 9 Oct):
- `overall.gross_gex_abs` and `overall.net_to_gross`;
- `net_gex_at_spot` calling `dealer_position()`;
- the three failure cases (empty chain, no IV, settled all DTE 0) in `tools/validate_exposure_edges.py`.

This branch tests them against hand figures (gate A) and runs the failure cases through the block as well (below).

**Added:**
- **The two masses:** `call_gamma_per_1pct` and `put_gamma_per_1pct`, unsigned, in dollars per 1% move. They sum to `gross_gamma_per_1pct` overall, in every bucket and in every horizon window and band.
- **`oi_delta_balance_shares`:** the raw-signed OI balance. Each contract's own delta × OI × 100, calls positive and puts negative, with no dealer sign. Printed with no directional word.
- **The walls, named as the brief names them** (audit F5):
  - `call_wall_otm` and `put_wall_otm` are *the* walls;
  - the all-strike extremes are stored as `peak_call_gex_strike` and `peak_put_gex_strike`, and the renderer prints them as peaks;
  - the legacy `call_wall` and `put_wall` keys stay in the JSON, because the pin log, the cross-check and every stored profile carry them. The renderer no longer reads them as walls.
- **The secondary concentrations:** `call_concentration_otm_2` and `put_concentration_otm_2`, the next OTM strike on each side (T2's rows).
- **The horizons:** `horizons`, the cumulative windows (0DTE, ≤ 7 days, ≤ 45 days, All), and `bands`, the exclusive bands (0DTE, 1–7, 8–45, > 45).
  - Both are cut by days to expiry from the same rows the listing buckets are built from, following `horizon_windows` in `config/reporting_stack.yaml`.
  - Each window carries the masses, net, gross, net-to-gross, DEX, its share of the hedge book and the OI balance. Each window, not each band, also carries its OTM walls, its peak-gamma strike and its own zero-gamma level.
  - Each records the listing buckets it draws on. The engine's buckets stay as stored.
  - At a settled capture, the 0DTE window and band are excluded ("settled, excluded"), with their OI structure and no greek, exactly like the 0DTE bucket.
- **Registered:** the seven new fields as metrics, with units, observation type and `added_date`, and their `FIELD_MECHANISM_GROUPS` entries. The window bookkeeping goes under `non_metrics`.
  - `tools/check_registry.py`'s drift check now reads inside `horizons` and `bands`: 116 exposure fields emitted, 0 unregistered.
  - The catalogue resolves the new keys from the registry (`python -m altdata.catalogue show exposure.call_gamma_per_1pct`).

**A note on "roll-ups of the listing buckets".** The windows can't be built from whole listing buckets. A monthly or quarterly listing can sit 5 days out or 60, so it would fall in different windows on different days. So the engine cuts the windows by each expiry's days to expiry, from the same rows, and records which buckets each window draws on. That is needs-you 1.

**The scorecard row** (`daily_cascade/stack_close.scorecard_row`):
- `gamma_regime` was already None when net GEX is None (F11).
- The eligibility fields now carry the brief's names:
  - `wall_approached_call` and `wall_approached_put` read the **morning's OTM walls** (stored alongside as `call_wall_otm_morning` and `put_wall_otm_morning`), not the all-strike peaks;
  - `flip_in_range` is new;
  - `is_expiry_session` is unchanged.
- **`regime_eligible`** is new: the morning's net-to-gross at or above 0.10.
- The old names `call_wall_approached` and `put_wall_approached`, which nothing read, are gone. Nothing reads the new fields yet either; part 2's ledger does.

**The IV-roughness threshold stays provisional** (0.35, `config.IV_ROUGHNESS_MAX`) until 60 captures are stored. The quality panel prints "provisional until 60 captures are stored" beside every reading.

## 2. Horizons, T1 and the quality panel, T4

`horizon_windows` and `dealer_block` are new blocks in `config/reporting_stack.yaml`. The block lives in `daily_cascade/dealer_block.py`, which prints views and recomputes nothing. Its only arithmetic is a distance from spot, a difference between two stored captures, and the bands' sum.

- **T1, the dashboard:**
  - **Rows, in the brief's order:** the call-gamma mass, the put-gamma mass, the zero-gamma (balance) level and its distance, net GEX with net-to-gross, the gated regime, the OTM call wall, the OTM put gamma wall, the hedge-book size (DEX), the share of the hedge book (the ≤ 7-day column is the brief's ≤ 7-day share), and the OI balance.
  - **Columns:** the four horizons.
  - **Spot** is in the table's head, and each level carries spot's distance to it.
  - At a settled capture, every 0DTE cell prints "settled, excluded". At an intraday capture the 0DTE column's head reads "0DTE (OI as of prior close)".
- **The quality panel**, under T1: the capture time and kind, the convention, the greeks source, rows (in, exposure rows, skipped and why), settled 0DTE rows excluded, data quality with the liquidity-floor reasons, IV roughness (raw figure and provisional verdict), OI concentration as effective strikes, MIN_T load-bearing, OI vintage "prior close", and the bands' reconciliation sentence.
- **T4, changes since the equivalent capture:**
  - The rows are the brief's nine: call mass, put mass, net GEX, net-to-gross, the zero-gamma level, the two OTM walls, the hedge-book size and the peak-gamma strike.
  - The columns are this capture, the equivalent and the change, and the head names the capture compared against.
  - A settled capture is the 16:10 slot. An intraday capture takes the nearest of 09:45 and 12:30 within 20 minutes, otherwise it has no slot.
  - It looks back 3 sessions for the prior capture in the same slot, and prints "no equivalent capture (…)" when there is none.
- **The three sentences of section 4** are part 2's. Their slot is `sentences` on the block, None here.
- **A profile computed before 6b** has no horizon windows. T1 says so and waits for the next capture, and the other tables still print.

## 3. T2 and the decision summary

- **T2, key levels** (the close: all expiries):
  - **Rows, one name per definition:** OTM call wall, secondary call concentration, zero-gamma level, spot, secondary put concentration, OTM put gamma wall, peak-gamma strike, peak put-gamma strike, put OI shelf, max pain, and the two all-strike extremes printed as "peak … (all strikes)", "a peak, not a wall (audit F5)".
  - **Columns:** strike, call / put gamma at the strike ($ per 1%), distance from spot, share of **gross**, and a conditional reading in the Dealer's Hand's words (Chapter 7), never "support" or "resistance". The mobile rule allows six columns, so call and put gamma share one.
  - **Max pain** prints only when the target session is an expiry session, otherwise "not an expiry".
- **The decision summary** (the close; the 09:45 slot when part 2's capture lands):
  - **Its lines:** the gated regime and the zero-gamma level's distance; the two walls; the setups whose conditions hold, each with its level, invalidation and time stop, or "No setup"; and "Every level here is inferred, not observed. The block proposes; the books decide; nothing here writes the register."
  - **The setups** (`config/setups.yaml`, conditions in `dealer_block.setups`):
    - `c_pin_fade`: an expiry session, positive gamma (gated), spot within 0.5% of the peak-gamma strike. Invalidation through the zero-gamma level; time stop the expiry session's close.
    - `c_negative_gamma_continuation`: negative gamma (gated), and spot through the zero-gamma level or an OTM wall since the equivalent capture, by at least 0.10%. Invalidation back through the level; time stop two sessions.
    - `d_forced_flow`: on an expiry session, the peak-gamma strike with max pain as the control, time stop the closing auction; on a tier-1 release day, the two OTM walls, time stop the release session's close.
- **Which session the summary is for.** The settled 16:10 capture is taken after its session ends, and that session's expiry has already settled. So the close's summary is **for the next trading session**: its expiry, its releases. A 09:45 or 12:30 capture reads its own session. The summary opens "For <date>."
- **What counts as an expiry session** (session-set, `dealer_block.expiry_sessions: friday`): the target session is a Friday with a listed expiry. SPY lists an expiry every weekday, so under "any" every session would be one, and `d_forced_flow` would fire at every close. This is needs-you 2.

## 4. The display

- **Inside the close's existing Mechanics section** (`daily_cascade/stack.py mechanics_section`), within its budgets: five sub-sections (T1, the quality panel, T4, T2, the decision summary), and no new chart.
- **The decision summary's lead is one priority-1 item**, so the section's change mark sees the block. The section fingerprint counts items and tables, not sub-sections.
- **The per-symbol lines for SPY, QQQ and IWM** now print the gated regime and the OTM walls. The change fingerprint still includes the legacy peaks, so a moved peak still marks the line, and `validate_stack`'s "a moved call wall un-collapses the section" holds unchanged.
- **The close reads the captures** from the payload's new `computed_dir` (`daily_cascade/payload.py`). A gate's synthetic payload names none, so nothing is read and nothing is added: gates stay deterministic.
- **The tier-1 releases** come from the stored events calendar, for the next session (`stack.releases_on`).
- **Every table is at most six columns**, the mobile rule.

## Session-set thresholds, with their reasons

All are in `config/reporting_stack.yaml` under `dealer_block`; the ratified ones are marked RULED there.

| Setting | Value | Reason |
|---|---|---|
| `symbols` | [SPY] | the scorecard's symbol; QQQ and IWM keep their one Mechanics line, inside the close's budget |
| `slot_tolerance_min` | 20 | a capture late by a pacing retry still matches its slot; 09:45 and 12:30 can never be confused |
| `equivalent_lookback_sessions` | 3 | one missed capture still compares against the one before, and T4 names the date |
| `expiry_sessions` | friday | SPY lists an expiry every weekday; "any" would make every session an expiry session (a holiday-shifted Thursday monthly is missed under "friday") |
| `c_pin_fade.near_peak_pct` | 0.5 | about two SPY strikes at $5 spacing near 680: close enough that the fade is toward the pin |
| `c_negative_gamma_continuation.confirm_pct` | 0.10 | about 0.7 SPY points: past the strike's own noise without waiting for the move to be over |
| `c_negative_gamma_continuation.levels` | zero-gamma, the two OTM walls | the levels the brief names as tradeable |
| time stops | the expiry session's close; two sessions; the closing auction; the release session's close | Doctrine 4.3 (Book C is tactical, intraday to a few days) and 4.4 (forced flow ends with its event) |
| T2 readings | Dealer's Hand Chapter 7, conditional | never "support" or "resistance" as facts (brief section 1) |

Ratified, not session-set: `net_to_gross_min` 0.10, the stamp, the convention line, and the 16:10 and 09:45 equivalents.

## Gates

Each was run locally, one at a time, only those this branch writes or changes:

| Gate | Result | What it holds |
|---|---|---|
| `tools/validate_dealer_block.py` (new; Makefile) | **71/0** | A the masses, gross and net-to-gross by hand, the gate at 0.10 both ways; B the OTM walls are the walls, the extremes peaks, one name per definition, rank as share of gross by hand; C the windows and bands from config, the reconciliation, nesting, "settled, excluded", "OI as of prior close"; D T1's rows and columns, the quality panel; E T4 finds 16:10 and 09:45 and misses 11:00 and a 16:10 with only a 09:45 before it, the change by hand, the stored-captures path; F each setup fires on its fixture with level, invalidation and time stop, "No setup", the settled capture's next-session target, the Friday rule; G nothing from the "never printed" list; H Mechanics carries the block, the stamp on every table that holds a figure, the convention once, ≤ 6 columns, `computed_dir` read or not, a pre-6b profile; I the scorecard's eligibility fields; J no register, ledger, order path or network import, no write |
| `tools/validate_exposure_edges.py` (group E added) | **28/0** | the masses sum to gross overall, in every bucket, window and band; peaks equal the legacy keys; one figure set per window; the settled 0DTE window and band excluded |
| `tools/validate_weekly_complete.py` (group M added) | **63/0** | the three failure cases through the engine and the block: an empty chain (absent, its reason); no IV (no net GEX, no regime word, the zero-gamma reason, rows skipped for no IV, no setup); settled all DTE 0 (every 0DTE cell "settled, excluded", no figure from nothing) |
| `tools/check_registry.py` (drift check reads the horizons) | **OK** | 116 exposure fields, 0 unregistered |

**The fixtures** are `tests/fixtures/dealer_block/chains.py`:
- a hand chain with vendor gamma, so every mass is arithmetic;
- the walls chain, where the ITM extremes are not the OTM walls;
- a Black-Scholes chain with five expiries, seen from Friday and from Thursday.

**The gate count** is now **eighty-nine code gates (eighty-six Python, three shell)**, six data gates. CLAUDE.md and the Makefile agree (89/86). Every other gate, and anything that renders a PDF (`validate_stack`, `validate_monthly_stack`), is left to CI.

**A slip, fixed before the commit:** the gate's stand-in event store first opened a SQLite file named `unused` in the worktree root. It was caught at staging and deleted; the stand-in now points into the gate's temporary directory.

## A sample, on the fixture chain

Synthetic: the Black-Scholes fixture chain, spot 680, settled Friday 16 Oct at 16:10, compared against the Thursday 16:10 capture. These are not market figures.

**Dealer dashboard, SPY** (settled Friday 16 Oct, 16:10)

| SPY at 680.00 (inferred, not observed) | 0DTE | ≤ 7 days | ≤ 45 days | All |
|---|---|---|---|---|
| Call-gamma mass ($/1%) | settled, excluded | $0.38bn | $1.26bn | $1.74bn |
| Put-gamma mass ($/1%) | settled, excluded | $0.28bn | $0.91bn | $1.24bn |
| Zero-gamma (balance) level | settled, excluded | 675.41 (−0.68%) | 670.08 (−1.46%) | 665.90 (−2.07%) |
| Net GEX ($/1%), net-to-gross | settled, excluded | +$0.10bn (15%) | +$0.35bn (16%) | +$0.50bn (17%) |
| Regime (gated) | settled, excluded | positive gamma | positive gamma | positive gamma |
| OTM call wall | settled, excluded | 685.00 (+0.74%) | 685.00 (+0.74%) | 685.00 (+0.74%) |
| OTM put gamma wall | settled, excluded | 675.00 (−0.74%) | 675.00 (−0.74%) | 675.00 (−0.74%) |
| Hedge-book size (DEX) | settled, excluded | $2.84bn | $11.78bn | $19.20bn |
| Share of the hedge book | settled, excluded | 15% | 61% | 100% |
| OI balance (Σ Δ·OI, calls − puts) | settled, excluded | +0.6m shares | +2.9m shares | +5.4m shares |

**Chain quality, SPY** (settled Friday 16 Oct, 16:10)

| Chain quality (inferred, not observed) | Reading |
|---|---|
| Capture | 2026-10-16 16:10 ET, settled |
| Convention | dealers-hand-v1 |
| Greeks source | computed_bs_from_yf_iv |
| Rows | 170 in; 136 exposure rows; 0 skipped |
| Settled 0DTE rows excluded | 34 |
| Data quality | ok; liquidity floor passed |
| IV roughness | 0.000, within the provisional 0.35 (provisional until 60 captures are stored) |
| OI concentration | 16.8 effective strikes |
| MIN_T load-bearing | no |
| OI vintage | prior close |
| Bands | The bands (1–7, 8–45, > 45; 0DTE settled, excluded) sum to All: call mass $1.74bn of $1.74bn; put mass $1.24bn of $1.24bn; hedge book $19.20bn of $19.20bn. |

**Changes since the equivalent capture, SPY** (settled Friday 16 Oct, 16:10)

| Since 2026-10-15 16:10 (inferred, not observed) | This capture | Equivalent | Change |
|---|---|---|---|
| Call-gamma mass ($/1%) | $1.74bn | $1.68bn | +$0.07bn |
| Put-gamma mass ($/1%) | $1.24bn | $1.20bn | +$0.04bn |
| Net GEX ($/1%) | +$0.50bn | +$0.48bn | +$0.03bn |
| Net-to-gross | 17% | 17% | +0 pp |
| Zero-gamma level | 665.90 | 661.34 | +4.57 |
| OTM call wall | 685.00 | 680.00 | +5.00 |
| OTM put gamma wall | 675.00 | 670.00 | +5.00 |
| Hedge-book size (DEX) | $19.20bn | $18.33bn | +$0.87bn |
| Peak-gamma strike | 685.00 | 680.00 | +5.00 |

**Key levels, SPY** (settled Friday 16 Oct, 16:10)

| Key levels, SPY (inferred, not observed) | Strike | Call / put gamma ($/1%) | From spot | Share of gross | Reading |
|---|---|---|---|---|---|
| OTM call wall | 685.00 | $0.25bn / $0.08bn | +0.74% | 11.0% | if approached while gamma is positive, dealer long-call hedging sells into the rally; a decisive break can squeeze (DH 7.1) |
| Secondary call concentration | 690.00 | $0.23bn / $0.07bn | +1.47% | 9.8% | the next call concentration above; the same reading, smaller (DH 7.1) |
| Zero-gamma level | 665.90 | — | −2.07% | — | the regime boundary: above it dealer hedging leans against moves, below it leans with them; crossing it changes the playbook, not the price (DH 7.5) |
| Spot | 680.00 | — | — | — | the capture's spot |
| Secondary put concentration | 670.00 | $0.08bn / $0.15bn | −1.47% | 7.8% | the next put concentration below; the same reading, smaller (DH 7.2) |
| OTM put gamma wall | 675.00 | $0.10bn / $0.18bn | −0.74% | 9.2% | holds only if holders monetize and vol falls; a break is regime information (DH 7.2) |
| Peak-gamma strike | 685.00 | $0.25bn / $0.08bn | +0.74% | 11.0% | where hedging flow is densest; the pin candidate on an expiry session (DH 7.4) |
| Peak put-gamma strike | 675.00 | $0.10bn / $0.18bn | −0.74% | 9.2% | where put gamma peaks, near the money by construction; a peak, not a wall (audit F5) |
| Put OI shelf | 640.00 | $0.02bn / $0.05bn | −5.88% | 2.4% | the largest out-of-the-money put open interest; an OI level, not a gamma one (DH 7.2) |
| Max pain | not an expiry | — | — | — | an OI construct; meaningful only where it coincides with the peak-gamma strike (DH 7.4) |
| Peak call-GEX strike (all strikes) | 685.00 | $0.25bn / $0.08bn | +0.74% | 11.0% | an all-strike extreme: a peak, not a wall (audit F5) |
| Peak put-GEX strike (all strikes) | 675.00 | $0.10bn / $0.18bn | −0.74% | 9.2% | an all-strike extreme: a peak, not a wall (audit F5) |

**Decision summary, SPY** (settled Friday 16 Oct, 16:10)

- For 2026-10-19. Regime: positive gamma; the zero-gamma level 665.90 is −2.07% from spot.
- Walls: OTM call wall 685.00 (+0.74%), OTM put gamma wall 675.00 (−0.74%).
- No setup: none of c_pin_fade, c_negative_gamma_continuation or d_forced_flow holds.
- Every level here is inferred, not observed. The block proposes; the books decide; nothing here writes the register.

**Decision summary, SPY** (settled Thursday 15 Oct, 16:10: the summary is for Friday)

- For 2026-10-16. Regime: positive gamma; the zero-gamma level 670.18 is −1.44% from spot.
- Walls: OTM call wall 685.00 (+0.74%), OTM put gamma wall 675.00 (−0.74%).
- Setup d_forced_flow (Forced flow, Book D): 2026-10-16 is an expiry session; level 685.00 (the peak-gamma strike; max pain 675.00 the control); invalidation: the session trading more than 0.5% from 685.00 into the final hour; time stop: the closing auction.
- Every level here is inferred, not observed. The block proposes; the books decide; nothing here writes the register.

**Decision summary** (the 09:45 pin fixture: Friday, positive gamma, spot 0.3% from the peak)

- For 2026-10-16. Regime: positive gamma; the zero-gamma level 98.00 is −2.29% from spot.
- Walls: OTM call wall 102.00 (+1.69%), OTM put gamma wall 97.00 (−3.29%).
- Setup c_pin_fade (Fade toward a gamma-implied pin, Book C): 2026-10-16 is an expiry session, gamma is positive, and the peak-gamma strike is −0.30% from spot; level 100.00 (the peak-gamma strike); invalidation: spot through the zero-gamma level at 98.00; time stop: the expiry session's close.
- Setup d_forced_flow (Forced flow, Book D): 2026-10-16 is an expiry session; level 100.00 (the peak-gamma strike; max pain 100.00 the control); invalidation: the session trading more than 0.5% from 100.00 into the final hour; time stop: the closing auction.
- Every level here is inferred, not observed. The block proposes; the books decide; nothing here writes the register.

**Section note (once per edition)**

> Sign convention (dealers-hand-v1): dealers are assumed long calls and short puts, so call gamma counts positive and put gamma negative. An assumption about who holds the options, not an observation; under the opposite reading every net sign inverts. The call- and put-gamma masses and the zero-gamma level hold under either.

## Box commands, for the operator

Nothing here runs from a session. Each step is inside a window (weekdays 09:05–15:40 or 17:20–23:30 ET), after this branch reaches main with the second chain.

1. **The first captures need nothing new.** The 16:10 EOD pass already writes the settled capture. From the first EOD run after the merge, its profile carries the horizon windows and the new fields, and the 16:45 close prints the block.
   - On the first close after the merge, T4's prior 16:10 predates the new fields, so the masses' rows read "n/a" against it for one day.
   - A profile computed before the merge prints T1 as "computed before the horizon windows existed; the next capture carries them".
2. **To read the block from the stored captures without a report** (read-only):
   ```
   cd ~/chester-reports
   .venv/bin/python -m daily_cascade.dealer_block show --date <YYYY-MM-DD>
   ```
3. **Part 2's units, named here and not created:**
   - `chester-dealer-0945.service` / `.timer` and `chester-dealer-1230.service` / `.timer`, the intraday captures from the sources the box already has (Massive for SPX and SPCX, Yahoo for the rest);
   - the 5–15-minute SPY recompute.
   Part 2 writes them; enabling them is yours.

Nothing restarts, and no unit file changes on this branch.

## Files shared with the open branches

Trial merges (`git merge-tree`, nothing committed) of this branch's commit against each open branch, compared with the same merges from `st-r5-audit`'s tip:

- **This branch adds no conflict of its own with any of them:** `6e-releases`, `6e-digital`, `6e-rest`, `st-r4-tranche-1b`, `st-r6-es-block`, `aud-3b-security-master` (Monday's chain) and `post-friday-fixes`. Every conflict the trials show comes from the st-r5 line underneath and is the second chain's to resolve. Mostly that is CLAUDE.md's count line, plus the st-r5 files that session B also touches.
- **The files this branch touches that open branches also touch:**
  - `CLAUDE.md` (the count line: 89/86 here; recount at stitching);
  - `Makefile` (one line);
  - `metrics_registry.yaml` (seven entries, the non_metrics lists);
  - `config/reporting_stack.yaml` (two new blocks, also touched by `6e-releases` and `6e-digital`);
  - `daily_cascade/stack.py` (`mechanics_section`, `releases_on`, `dealer_blocks`; also touched by the 6e branches, `st-r4-tranche-1b` and `st-r6-es-block`);
  - `daily_cascade/stack_close.py` (`scorecard_row`; also touched by `st-r4-tranche-1b` and `st-r6-es-block`).

  All merge cleanly in the trials.
- **New files:** `daily_cascade/dealer_block.py`, `tools/validate_dealer_block.py`, `tests/fixtures/dealer_block/chains.py`.

## What parts 2 and 3 take next

- **Part 2:**
  - the charts wired from `tools/dealer_charts.py` (figure 2 on the close as its one dealer chart);
  - the three fixed sentences in `sentences`, behind the numeral and flag-word audits, with "dampened" added to the flag words;
  - the pre-registration ledger `docs/ledgers/dealer-scorecard-preregistration-2026-10.md` and the Weekly's flags on the new eligibility fields (`weekly_sections.flags_for` still reads the old semantics);
  - the rate printer with Wilson intervals;
  - the 09:45 and 12:30 capture units, and the decision summary in the 09:45 slot.
- **Part 3:**
  - T3, the horizon matrix, with "registered hypotheses: n, none promoted";
  - the Weekly's T2 per horizon (the windows carry their walls and peak; T2 per window wants per-strike gamma by window, a small engine addition);
  - the Monthly wiring, the FlashAlpha vendor line in the Weekly's Mechanics, and the vendor writer.

## Needs you

1. **"Roll-ups of the listing buckets."** The windows are cut by each expiry's days to expiry, from the rows the buckets are built from. They are not sums of whole buckets, because a monthly or quarterly listing moves between windows as it ages. Each window records the buckets it draws on, and the buckets stay as stored. Say if you meant something else.
2. **What counts as an expiry session for the setups and T2's max pain:** Friday (session-set) or any listed expiry. SPY's daily expiries make "any" fire `d_forced_flow` at every close. Under "friday" a holiday-shifted Thursday monthly is missed. The scorecard's `is_expiry_session` (any DTE 0) is left for part 2's pre-registration to rule on.
3. **The close's summary is for the next session.** The settled capture's own expiry has passed, so the expiry setups and the release day read the next trading session. Confirm.
4. **The session-set setup thresholds** in the table above: 0.5% from the peak for the pin fade, 0.10% through a level for confirmation, the 20-minute slot tolerance, the 3-session lookback and the time stops.
5. **Legacy `call_wall` and `put_wall`** stay in the JSON, the pin log and the Weekly's held flags, as the all-strike peaks. The brief's flags should score the OTM walls, and part 2's pre-registration is where that changes. Until then, the Weekly's "held" still scores the all-strike put peak (audit F5).
6. **The block covers SPY only on the close.** QQQ and IWM keep one gated line each. Say if either should carry the full block.

## CI

**`st-r5-audit` underneath is red** (run 38992737390, one failure). `validate_secrets` refused `tools/validate_by_hand_audit.py`, because its Korea-gap check named the dotfile in a quoted string, which only `altdata/secrets.py` may do. The fault is mine, from the st-r5-audit paste. This paste names only `6b-dealer-1`, so the fix (the check stated positively: the gap "needs a registered key (ruled out") is committed here, where the file is inherited and would fail the same way. `validate_by_hand_audit` 17/0. `st-r5-audit` itself stays red until Tuesday's stitch takes this commit, or a paste names that branch: needs-you 7.

| Commit | Run | Result |
|---|---|---|
| `e9b7fc9` (notes) | 39033119597 | **failed**: one check, `validate_secrets` on the inherited `validate_by_hand_audit.py` |
| `d7c1593` (the fix) | 39033223933 | **green**: every gate passes |

## Needs you, added

7. **`st-r5-audit` is red** on one gate text of mine (above). The fix is on this branch. Either let Tuesday's stitch carry it, or name `st-r5-audit` in a paste and I'll put the same commit there.
   - **Ruled 17 Oct:** repaired on `st-r5-audit` itself (the 6b part 2 paste, Part 0).
