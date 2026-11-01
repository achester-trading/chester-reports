# B99 notes: the premium sleeve, a paper engine in the Alpha Lab

Paste B99 (`docs/pastes/B99.md`), 31 Oct 2026. Branch `b99-premium-sleeve`, base
origin/b98-ks-family-registry at `f0343d55`. Batch 19 item 100, accepted 27 Oct.
Merges after B98. Paper only: no live orders before 2027, and nothing in `alpha/`
can reach a broker.

## The order of the commits (pre-registration integrity)

1. `2015c409`: **the registration**, before any engine code.
   - `alpha/research/roster-2026-10-31-premium-sleeve.yaml`, batch
     `2026-10-31-roster-premium-sleeve`, hypothesis **P-1**. It sits in the
     rosters' workbench path, `alpha/research/`, not the Drive inbox: an
     operator-ruled item enters as the X-3 engines did.
   - `config/alpha_premium_sleeve.yaml`, the pre-registered spec, sha256
     `e5986830db0027e4057ffebc06ac8093838089528878f5fd48980a81fde84a01`, quoted
     by P-1.
   - Pushed.
2. `2eab85bc`: **the engine**, `alpha/engines/premium_sleeve.py`, together with
   its registry entry (disabled), the spread's cost line, `engine.active()` and
   validate_alpha's follow-ups. Pushed.
3. `a3af77f1`: **the gate**, `tools/validate_premium_sleeve.py`, and CLAUDE.md's
   gate counts. Pushed.
4. These notes.

No backtest was run. The engine's `simulate` ran only on the gate's synthetic
store and chain.

## The registration: P-1 and its variants

- **The hypothesis.** `family_ref: KS options` (house, B98), `family:
  premium-sleeve`, source operator, `model_idea_rule: false`,
  `engine: premium_sleeve`, horizon medium, 20 sessions.
- **`rule_dsl` is absent.** The grammar reaches the VRP gate, but not the
  min-max IV rank, the put spread as an instrument, delta selection, or exits
  priced off the credit. So the rule is the engine's, as for E-1 to E-7, and
  `rule_text` states all of it.
- **Counted variants: six.** The base and five changes, each a counted variant;
  the engine's `grid_size` is 6:

| Variant | Change |
|---|---|
| base | short \|delta\| 0.16–0.20, 30–45 DTE, take profit 50% of credit, close at 21 DTE |
| `delta_band_low_end` | band 0.14–0.20 |
| `delta_band_high_end` | band 0.16–0.22 |
| `dte_low_bound` | 25–45 DTE |
| `dte_high_bound` | 30–50 DTE |
| `take_profit_level` | 60% of credit |

- **Expected:** positive expectancy after costs, about +2% to +5% of the
  spread's maximum loss per trade, with a left tail. This is an operator-ruled
  prior, not a measured one.
- **Sample:** at most about 12 entries a year (one open at a time, held 10–24
  sessions), likely 4 to 8. The constitution's daily minimum is 100, and SPX
  chains are stored only from October 2026, so coverage is a data gap for years.

**Session-set where the ruling is silent** (each marked in the spec):
- SPX, not XSP: the vendor chain the system holds is SPX's, and XSP is a tenth of
  it under the same rule.
- The expiry nearest the window's middle.
- The short strike nearest |delta| 0.18.
- The long strike 50 points below the short.
- Delta at rate and dividend zero.
- An unread overlay stands down.
- Sizing in whole spreads at the sleeve capital, 5% of the lab's notional
  (`min_size: 0.05`).

## The engine's inputs, by key (each read as knowable at 17:40 ET)

| Input | Key(s) | Rule |
|---|---|---|
| VRP | `yfinance.mkt_vix` less `calc.vol_spy_realized_20d` | > 0 (the house's VRP, `altdata/vol_event.py`) |
| IV rank | `yfinance.mkt_vix`, last 252 sessions | (x − min)/(max − min) × 100 ≥ 66.67 |
| Dealer | `exposure.net_gex`, `exposure.spot`, `exposure.gamma_flip` (instrument SPX) | net GEX > 0, or spot > flip |
| Overlays | `altdata/tb_harness.py` `overlays_at` (`hy_accel`, `liquidity`; inputs in `config/tb_episodes.yaml`) | stand down on FIRES, and on anything not CLEAR |
| The count | `capitulation.count_band`, `top_bottom.verdict` | stand down on surrender without BOTTOM SIGNAL; not stored, stand down ("count not stored") |
| The chain | the vendor snapshots `data/chains/<session>/SPX_<HHMMSSZ>.csv`, each row knowable at its `fetched_at` | no snapshot, expiry or strike: no trade, "chain not stored" |
| Settlement | `yfinance.mkt_gspc` | at expiry, the cash value against the close |

- **The fills.** `config/alpha_costs.yaml` gains `index_option_spread`. Each leg
  is filled against its own stored quote: the short sold at its bid, the long
  bought at its ask, plus slippage and a commission per leg. Never the mid. A
  leg with no quote is not traded.
- **The exits.** The entry fills at the session after the decision. The
  take-profit closes when the executable debit is at most half the credit. The
  21-DTE close comes at the first session 21 days or fewer from expiry, and
  unclosed positions cash-settle at expiry. One spread at a time.
- **The record.** `position_record()` writes a trade in the `positions` table's
  own columns, with `family_ref` beside it (the table has no family column).
- **Disabled.** `config/alpha_engines.yaml` lists the engine with
  `enabled: false`. `alpha/engine.py` gains `active()`, which the nightly and
  weekly loops now load. `registered()` still lists every entry, so P-1 can name
  its engine at registration.

## The gaps

1. **The benchmark, the Cboe PUT index:** not stored, pending Doctrine #2
   (D2-74). Under D45's hold no new Cboe series is pulled, so the sleeve ledgers
   its returns against cash, as a fraction of the sleeve's capital. This is in
   P-1's `data.gaps` and the spec's `benchmark`.
2. **The Capitulation Count.** B79's module computes the count and stores none,
   and no writer stores `top_bottom.verdict`. As ruled, the stand-down reads
   "count not stored" and the engine stands down. **So it will never enter**
   until a writer stores `capitulation.count_band`, a later paste's work.
3. **The overlays have no stored state.** The harness computes them as of the
   session from their stored inputs. Wherever an input is unread, the overlay is
   UNREAD and the sleeve stands down.
4. **The chain is files, not the store.** It is the system's own vendor
   snapshots, read-only and point in time, as engine 7 reads its computed
   profiles. It carries no Greeks (`greeks_status: pending_solver_gate`), so the
   delta is the engine's own, Black-Scholes from each row's implied volatility.
5. **History.** No SPX chain is stored before October 2026.

## The gates

| Gate | Tally |
|---|---|
| validate_premium_sleeve (new) | 36 passed, 0 failed |
| validate_alpha | 271 passed, 0 failed |
| validate_alpha_no_orders | 75 passed, 0 failed |
| validate_alpha_lab_3 | 65 passed, 0 failed |
| validate_alpha_lab_4 | 65 passed, 0 failed |
| validate_b45_chain3 | 29 passed, 0 failed |
| validate_alpha_proposer | 42 passed, 0 failed |
| validate_audit_3a | 88 passed, 0 failed |
| validate_gates | 32 passed, 0 failed |
| check_library, check_master_guide | 0 failures |
| check_registry | OK |

- **validate_alpha follows the registry.** Its engine list gains
  premium_sleeve; its cost classes are nine; the nightly loop's candidates
  exclude the disabled engine; and B98's group W counts only the hypotheses
  without their own `family_ref`, since P-1 carries its own.
- **Makefile.** No line to add: since S1 a gate declares itself
  (`GATE_KIND = "code"`), and the Makefile's list is `tools/gate_list.py`'s.
  CLAUDE.md's counts move to 160 code gates, 157 of them Python.

## The lab's own steps after the merge (the operator's, on the box, inside a window)

1. **Register P-1 by manifest before any backtest:**
   `python -m alpha.manifest register alpha/research/roster-2026-10-31-premium-sleeve.yaml`.
   It counts 1 under `KS options` at registration and 5 more at its first
   harness run, 6 in all.
2. **The harness run.** `python -m alpha.research run <its HYP id>` prints its
   coverage: "insufficient history: n completed spreads over k stored SPX snapshot
   sessions; the harness needs 100". Nothing is promoted before that sample.
3. **The paper period.** P-1 is operator-ruled (`model_idea_rule: false`), so the
   model-idea rule's 1.5× paper period does not apply. If the lab ever classed it
   as model-proposed, which it should not, the period would be 1.5 × 100 = 150
   paper signals.
4. **Enabling** (`enabled: true`) is the operator's, and changes nothing until
   the count is stored (gap 2).
5. **Promotion** only through RAS (item 91(b)) and the cost cliff (item 91(c)),
   under the constitution, at its own sleeve cap under the Doctrine. OTM and LEAP
   buying stays a separate Book D sleeve, never funded by premium.
