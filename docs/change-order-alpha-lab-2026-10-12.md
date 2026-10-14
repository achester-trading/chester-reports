# Change order — Layer X, the Alpha Lab (X-1 … X-3)

| | |
|---|---|
| Status | **Ruled, 12 Oct 2026.** Nine decisions in the brief (`docs/briefs/alpha-lab-brief-2026-10-12.md`): 1–8 accepted as a list at 20:28 ET, 9 (the learning loop) at 20:40 ET. Tabled at Audit #4 as a new layer. Build: Tranche 1 the week of 19 Oct, after Friday's merges. |
| Owner | Ari Chester |
| Inputs | The brief of 12 Oct; the Operating Doctrine; the Enterprise Layer change order (`docs/change-order-enterprise-layer-2026-09-27.md`, Part VIII and the order gate); the 2 Oct ruling "never orders stands for the engines"; the gate ladder (Gate 1 mark-to-market, Gate 1.5 paper orders through the order gate, Gate 3 live, not before 2027). |
| Why | The operator asked for "a new layer … independent … unrestrained, with singular focus on profitability", then "a self-learning loop … continuously learning, as well as innovating". The reports are the operator's intelligence and the Doctrine's books his capital; neither is a machine's book. This order builds one beside them, in ledger-paper, that reads the whole store and writes nothing back. |

## 1. The layer in one paragraph (the Doctrine amendment — item X-1.13)

> **Layer X — the Alpha Lab.** Beside the four books and the five reports there is one independent layer: a machine's book in ledger-paper that reads the observation store and writes nothing back to it, to the register, to the narrative ledger or to any report. It has four restraints and no others — the Brookfield blocklist; ledger entries against stored prices, with no order path of any kind before the Gate 3 ruling; a risk governor; an evidence gate — and inside them it searches, trades, learns and innovates on its own authority, without the sitting and outside the attention budget. Part VIII's limits on engines do not apply inside it and are unchanged outside it. Its results are tabled at sittings as evidence; each rung of the gate ladder is the operator's ruling. Its constitution — the four restraints, the governor's numbers, the validation standard, the kill criterion, the hold-out and the variant count — changes only by ruling.

## 2. The constitution (`config/alpha_constitution.yaml` — read by every loop, written by none)

| Key | Value (ruled 12 Oct) |
|---|---|
| `objective` | maximise expected log growth of the lab's notional capital net of modelled costs, subject to the governor |
| `kelly_fraction` | 0.25 (raised only by ruling, on the ledger's evidence) |
| `governor.engine.halve_at` / `stop_at` | −10% / −20% from the engine's own high-water mark (stop → status `validation`, frozen) |
| `governor.portfolio.stop_at` | −15% from the lab's high-water mark (→ status `halted`, operator review) |
| `validation.embargo` | one engine horizon between fit and test windows |
| `validation.min_signals` | daily 100 · weekly 40 · intraday 400 — independent signals, before any size above minimum |
| `validation.deflated_sharpe_min` | 1.0 at the engine's sample, deflated by the ledger's variant count for that engine family |
| `validation.min_size_period` | the first `min_signals` paper signals at minimum size regardless of backtest |
| `kill` | after `min_signals`: expectancy after modelled costs ≤ 0, or realised Sharpe < 0.5 × the deflated Sharpe it was validated with |
| `holdout_months` | every fourth calendar month of history, never fitted by any loop; used only for the final check before a promotion |
| `refit.frozen_in_drawdown` | true — a halved or stopped engine is never re-fitted |
| `orders` | none; `alpha/` may not import any order, gate, broker or network module (static gate) |
| `blocklist` | the system's, applied at signal time; a blocked instrument never reaches the ledger |

A session changes a value here only on a paste that quotes the ruling; `tools/validate_alpha.py` fails if the file's hash differs from the one recorded in `docs/alpha-lab.md` without a matching ruling line.

## 3. Tranche 1 — the foundation (X-1; ≈ 38 h; week of 19 Oct; branch `alpha-lab-1`)

**X-1.1 Package and ledger.** `alpha/` beside the existing packages. `alpha/ledger.py` owns `alpha.db` (SQLite, under the data root beside the observation store, path in config; added to the backup set in `scripts/deploy.sh`). Tables: `engines` (id, family, horizon, status, validated_at, validated_metrics, validated_ranges, kill_rule, min_size), `hypotheses` (see X-2.5), `signals`, `fills` (modelled price, cost components, stored reference quote), `positions`, `marks`, `grades`, `edge_posterior` (per engine per day: n, win-rate posterior, expectancy posterior, shrinkage prior), `cost_calibration`, `attribution` (per engine per day per regime key), `loop_events` (loop, kind, engine, before, after, counterfactual, version, reversed_by), `variant_counts` (per family), `holdout` (the months). Every row carries `as_of` and `written_at`.

**X-1.2 Read-only store access.** `alpha/store.py` wraps the existing point-in-time reader; the connection to the observation store is opened read-only (`mode=ro`); a test proves no write path exists from `alpha/` (the store's file hash is unchanged after a full nightly run on the fixture).

**X-1.3 The engine interface.** `alpha/engine.py`: an abstract base with `engine_id`, `family`, `horizon`, `universe()`, `signal(as_of)`, `size(signal, risk_budget)`, `exits(position, bar)`, `cost_class`, `validated_ranges`, `kill_rule`. Engines are registered in `config/alpha_engines.yaml`; the registry is the only place an engine is named.

**X-1.4 The cost model.** `alpha/costs.py` with `config/alpha_costs.yaml`: per cost class (ETF, single name, index option, equity option, future, perp, prediction-market contract, FX pair) — half the quoted spread crossed where a quote is stored, a fixed spread estimate where not; slippage as a function of size against dollar ADV; commissions; borrow for shorts; roll for futures; funding for perps; FX for foreign names. Conservative by construction (never the mid). `cost_calibration` holds the modelled-versus-stored comparison the nightly loop writes.

**X-1.5 Simulated execution.** `alpha/paper.py`: a signal becomes a ledger fill at the next stored bar's open plus the cost model, or at the stored bid/ask where a quote exists (6b's chain history for options; the W-1.1 contract record for prediction markets; venue prices for crypto); exits are evaluated bar by bar, bracket-style; marks daily from the store. `tools/validate_alpha_no_orders.py`: a static gate that fails on any import in `alpha/` of the order gate, the broker modules, or any network library, and on any `requests`/`urllib`/socket use. CI runs it on every push.

**X-1.6 The validation harness.** `alpha/validate.py`: point-in-time reads only (`available_at`); walk-forward with the embargo; the hold-out months excluded from every fit; the deflated Sharpe (Bailey–López de Prado) with the variant count read from `variant_counts` and incremented by every run; the minimum-sample check; the pass record written to `engines` with the metrics and the ranges the parameters were validated over. A fixture with a synthetic series of known edge must pass and a null series must fail; the deflated Sharpe must fall as the variant count rises.

**X-1.7 The allocator.** `alpha/allocate.py`: fractional Kelly at `kelly_fraction` from the posteriors and the engines' realised covariance; a portfolio heat cap; engines whose returns correlate above a session-set threshold are counted as one; rebalanced by the weekly loop, never by hand. New engines enter at `min_size`.

**X-1.8 The governor.** `alpha/governor.py`: high-water marks per engine and for the lab; the three thresholds from the constitution; transitions written to `loop_events`; a halved engine carries `frozen=true` and no loop re-fits it.

**X-1.9 The nightly loop.** `alpha/loops/nightly.py`: mark and grade; posterior update (Beta-binomial on the win rate, normal–normal on expectancy, both with a shrinkage prior toward zero whose strength is session-set and recorded); cost calibration; allocator weights; attribution by regime key (the dials' stored states, the volatility regime, the dealer regime, event days); drift check against the validated metrics; every change a `loop_events` row.

**X-1.10 Units and timers.** `chester-alpha-nightly.timer` (weekdays, after the daily close capture — the session verifies the cascade's capture time and schedules after it), `chester-alpha-weekly.timer` (Sunday, after the Weekly's run). Unit files through `scripts/deploy.sh`; enabling is the operator's. A loop that fails writes its failure to `loop_events` and never touches a report.

**X-1.11 The Weekly's lab line.** One line, read from `alpha.db` read-only, in the Weekly's header block: "Alpha Lab: +x.x% since <date> · n engines live · drawdown y% · loop events this week k" — "Alpha Lab: not yet live" until the first engine passes. Fixture-gated like every other line.

**X-1.12 Gates and fixtures.** `tools/validate_alpha.py` (fixture ledger; X-1.6's synthetic tests; hold-out exclusion; governor transitions; the constitution hash; the no-orders check), a CI job, no live-store reads in any gate.

**X-1.13 Documents.** `docs/alpha-lab.md` (architecture, the constitution verbatim with its hash, the loops, the gate ladder); the Doctrine amended with §1's paragraph (docs-only commit on the operator's word); a CLAUDE.md section for `alpha/`: the store read-only, no order/gate/broker/network imports, the constitution unchanged without a quoted ruling, the two-session rule unchanged.

## 4. Tranche 2 — the first engines and the learning loop (X-2; ≈ 40 h; week of 26 Oct; branch `alpha-lab-2`, stacked on 1)

**X-2.1 Engine 1 — dealer-conditioned defined-risk VRP.** SPY and QQQ; iron condors, put spreads and call spreads at daily and weekly expiries; entry conditioned on the stored dealer regime (gamma sign and level, vanna and charm into expiry) and on the implied-against-realised gap; exits at a fraction of credit, a multiple of credit, or expiry; fills at stored bid/ask. Before 6b's chain history the backtest uses the stored FlashAlpha historical quotes where coverage exists — the session runs the coverage check first and records the sample it actually has.

**X-2.2 Engine 2 — cross-asset trend.** Time-series momentum (blended 12-1, 6-1, 3-1 look-backs) and cross-sectional momentum over the ~90 stored instruments and the crypto set; long and short; volatility-targeted per sleeve; weekly rebalance; ETF and future cost classes.

**X-2.3 Engine 3 — prediction-market against futures.** Reads the Kalshi/Polymarket contract record (W-1.1 — bid, ask, liquidity) and the fed-funds-implied meeting probabilities from the store; enters when they differ by more than a threshold set from the stored history, on the venue with the better executable price, above a liquidity floor; holds to resolution or to convergence within a band; graded on resolution. Depends on `w-1-1-integrity` merged.

**X-2.4 The weekly loop.** `alpha/loops/weekly.py`: extend each live engine's walk-forward by the week; re-estimate parameters within `validated_ranges` only, a move accepted only if the deflated out-of-sample metric improves on the embargoed window, every re-fit one more variant; a parameter that wants to leave its range is logged as a hypothesis, not moved; allocator rebalance; then write `alpha/research/agenda.md` and `agenda.json` from the residuals — losses by regime, instrument and day; the move screen's prints without a position; the engines' pairwise correlation (crowding); the backtest-to-paper gap per engine.

**X-2.5 The hypothesis register.** `alpha/hypotheses/<id>.yaml`: mechanism paragraph, expected sign and size, instruments and horizon, sample needed, kill rule, `pre_registered_at`, source (`sitting` / `systematic` / `tell`), status (`proposed` / `testing` / `passed` / `failed` / `retired`), result. `alpha/validate.py` refuses to run on a hypothesis whose `pre_registered_at` is later than the run — a hypothesis written after its backtest is a variant, not an idea. Failures are kept with their result; the register of failures is part of the lab's knowledge.

**X-2.6 Promotion on the loop's authority.** A hypothesis that passes X-1.6 is written to `engines` at `min_size` and begins trading at the next loop; the Weekly's lab line and the monthly Lab report name it; the operator may retire any engine by ruling (a `loop_events` row with `source=operator`).

**X-2.7 The research sitting.** A paste template, `docs/briefs/alpha-research-sitting-template.md`: the session reads `agenda.md`, the failures register and the system's own papers, proposes at most five hypotheses, pre-registers them, runs the harness, and reports — never edits the constitution, never promotes by hand. The first sitting is the first paste after Tranche 2 merges; thereafter fortnightly, as a queued paste.

**X-2.8 The monthly Lab report.** `alpha/report.py`, mailed with the Monthly: engines and their posteriors; the loop's events; promotions and retirements; the failures register's additions; the cost calibration; the lab's P&L and drawdown against the governor.

## 5. Tranche 3 — the rest of the roster, the search, the meta-loop (X-3; ≈ 46 h; November, as 6b and S-3 land; branch `alpha-lab-3`)

**X-3.1 Engine 4 — scheduled events.** CPI, payrolls, FOMC: the surprise against consensus conditioned on stored positioning and the dealer regime, traded in the first session's drift or the volatility crush after; earnings in the 29-name universe: post-announcement drift and implied-against-realised move. The system's own event base rates first; the engine second.

**X-3.2 Engine 5 — crypto carry and basis.** After the S-3 funding and open-interest series are stored: perp funding harvest and spot–perp basis on BTC and ETH, delta-neutral, with the funding regime as the switch.

**X-3.3 Engine 6 — extremes reversion.** After the move screen's base rates reach n ≥ 30 per bucket: fade the 2.5σ prints whose own history reverses, at the horizon the history says.

**X-3.4 Engine 7 — intraday dealer regimes.** After 6b's intraday captures and the state vector exist: opening-range and VWAP behaviour conditioned on the gamma regime and 0DTE flow. The Enterprise Layer's own dealer engine stays the Doctrine's, under Part VIII's rules; this is the lab's.

**X-3.5 The grammar search.** `alpha/search.py`: engine components — signal families × conditioning variables (the dials, the dealer regime, positioning, the funding regime) × horizons × instruments × exits — enumerated and tested with every candidate counted in `variant_counts`; survivors written to the register as `systematic` hypotheses, pre-registered by the search's own manifest before its first backtest.

**X-3.6 Tells as hypotheses.** Every Weekly tell, Doctrine tell, scanner setup (`config/setups.yaml`) and graded forecast source in the probability ledger is imported as a pre-registered hypothesis — "predicts at horizon *h* after costs?" — with its mechanism text quoted from the paper that states it. This is how the reports' intelligence reaches the lab; the reports never drive it.

**X-3.7 The quarterly meta-loop.** `alpha/loops/quarterly.py`: for every `loop_events` row of the quarter, the counterfactual from the same stored prices (what the lab would have earned without the change); the loop's net contribution; if negative, `refit` bounds narrowed and the re-fit cadence slowed for the next quarter, recorded as a loop event of its own. A page in the Quarterly: the lab's quarter, the engines, the loop's contribution, the failures register, the gate-ladder standing.

## 6. What prints, and where the lab is not

Weekly: the lab line (X-1.11). Monthly: the Lab report (X-2.8). Quarterly: the lab page (X-3.7). Nowhere else: the lab does not write a candidate, a packet, a dial, a band, a tell or a narrative; it does not read the Monthly to decide; it does not enter the sitting except as evidence tabled by the operator.

## 7. Calendar

| When | What |
|---|---|
| Wed 14 – Thu 15 Oct | Audit #4 tables the lab as a new layer (Part VII, a row of its own; not Category 1). |
| Fri 16 Oct | Merge day as ruled; the lab waits for it. |
| Week of 19 Oct | Tranche 1 on `alpha-lab-1` — three session-nights (A or B as the queue allows; never a third session); CI green; merged on the operator's word inside a window. Units deployed; timers enabled by the operator. The Weekly of Sun 25 Oct prints "Alpha Lab: not yet live". |
| Week of 26 Oct | Tranche 2 on `alpha-lab-2`; engines 1–3 validated; the first research sitting. The Weekly of Sun 1 Nov prints the first live engines. |
| Sat 7 – Sun 8 Nov | Doctrine #2 receives the first monthly Lab report as evidence; the lab's place in the Doctrine confirmed. |
| November | Tranche 3 as 6b's chain history and intraday captures, and the S-3 series, land. |
| Spring 2027 | The first engines reach their minimum samples; the gate ladder's Gate 1.5 question is the operator's to put. |

## 8. Rules for the sessions building it

The standing rules unchanged (paper only; sessions never place orders; the blocklist; one task, one machine; no secrets; CI is the validate; a push to main is a deploy; units printed, never run). Added for `alpha/`: the observation store is opened read-only; no import of the order gate, the broker modules or any network library; `config/alpha_constitution.yaml` is not edited without a paste that quotes the ruling; no loop runs inside a report's run; no gate reads the live store; the lab never fetches.

## 9. Deferred and declined

Deferred: broker-paper through the order gate (Gate 1.5 — the gate ladder's, when the operator puts the question); a second VPS for the intraday engines (if the nightly or weekly loop ever delays a report's run); machine-learned engines beyond the grammar (permitted in principle, through the same gate, with every hyperparameter search counted — not before the grammar has run). Declined: any order path; any write to the store, register, ledgers or reports; discretionary overrides inside the lab (the operator retires engines by ruling and changes the constitution by ruling; he does not trade the lab's book); single-name fundamental picking; any Brookfield-complex instrument.
