# Phase 4 paper engine: nautilus_trader against an in-house engine (D35)

Paste B90 (`docs/pastes/B90.md`), 30 Oct 2026. Branch `b90-nautilus-assessment`
from `origin/main` at `422ea697`. **Docs only: nothing was installed on the laptop
or the box.** Public sources only; each is cited where used and was read on
30 Oct 2026.

**What D35 ruled (24 Oct).**
- nautilus_trader goes into the Phase 4 paper-engine brief as a candidate against
  an in-house engine, assessed after the 1 Nov Monthly.
- Two additions go into the brief whichever engine wins: an automatic signal
  pause when live edge decays (paper fills against backtest), and a standing
  "Why this could fail" section on every signal.
- Not adopted from the same source: crypto exchange websockets,
  terminal reverse-engineering and HFT-latency signals.

## The recommendation, in three lines

1. **Build the Phase 4 paper engine in-house.** Extend `alpha/paper.py`'s ledger
   and give Gate 2 a thin, separately audited IBKR paper executor on `ib_async`,
   the library Gate 1 already uses. Do not adopt nautilus_trader now.
2. **Do not run nautilus for backtests only.** A second backtester over a second
   data model gives a second answer to "what did this engine earn". That is the
   two-regimes problem the system already forbids.
3. **Re-assess nautilus as the Gate 2 execution node only.** Do it once 2.0 is
   final, the box runs Python 3.13, and the IB adapter's open order-path bugs are
   closed. Until then, it is a watched candidate with dated triggers (decision 3).

## 1. What the in-house paper path does today, from the code

### What it does

**Fills (`alpha/paper.py`, X-1.5).**
- A signal is a row in `alpha.db` and becomes a fill only against a price the
  store already holds, knowable at the run's as-of instant:
  - at a stored bid or ask where a quote exists after the signal (a buy at the
    ask, a sell at the bid);
  - otherwise at the next stored bar's open plus the cost model;
  - or at its close, for a close-only instrument or a `next_close` grammar
    entry.
- "A signal is never filled at a price from before it, and never at the mid." An
  unfillable signal expires after `MAX_WAIT_BARS` (5) sessions, with the event
  logged.

**Exits** are evaluated bar by bar, bracket-style, in a fixed order:
1. a gap through the stop or target, at the open;
2. a bar's range reaching the stop or the target. Where one bar reaches both,
   **the stop wins**, "because a daily bar does not say which came first and the
   conservative order is the one that costs";
3. the engine's own exits;
4. the time stop;
5. a governor stop or lab halt, at the next open.

**Costs (`alpha/costs.py`, X-1.4).**
- Spread, slippage, commission, borrow, roll, funding and FX, each non-negative,
  each recorded per fill. The numbers are `config/alpha_costs.yaml`'s.
- A nightly calibration compares the modelled spread with stored quotes
  (`cost_calibration`) and never rewrites the model by itself.

**The ledger (`alpha/ledger.py`, X-1.1).**
- `alpha.db`, the only database the lab writes: signals, fills, positions,
  marks, grades, `edge_posterior`, attribution, `loop_events`, `variant_counts`,
  holdout, allocations, equity, and later the event base rates and the carry
  book.
- Every row carries `as_of` and `written_at`.

**The point-in-time rule.**
- Engines read only through the `ReadOnlyStore` they are handed (`mode=ro`), at
  the as-of instant they are handed; `alpha/pit.py` gives vintage-aware series.
- A backtest never trades on a figure before the 17:40 ET nightly loop that
  could have read it (`nightly_after()`).
- `tools/validate_alpha.py` proves the store's hash is unchanged after a run.

**Books and guards.**
- `alpha/book.py`'s per-engine capital, P&L and drawdown.
- The governor's −15% halt, which only the operator lifts.
- Per-engine kill rules, the allocator, the blocklist (`register/instruments.py`)
  and the Brookfield rule.

**No order path.** `tools/validate_alpha_no_orders.py` holds `alpha/` to no
order, gate, broker or network import. CLAUDE.md denies `placeOrder`,
`place_order`, `bracketOrder`, `submit_order`, `order_router`, `ibkr_orders`,
`execution_framework`, `reqGlobalCancel` and `--allow-live` pre-emptively.

**The register's books** (A–D, Book Z's benchmarks) live in `chester.db`. The lab
never writes them. Decisions are the operator's (`decide.py record`, denied to
sessions).

**IBKR today is Gate 1 only.**
- Read-only sync: `altdata/sources/ibkr_portfolio.py` on `ib_async`, with
  `ib_insync` as the fallback.
- Costs (`ibkr_costs.py`) and what-if previews (`ibkr_whatif.py`).
- The client ids are in `altdata/ibkr_clients.py` (17–20).
- `ibgateway.service` is held back behind one witnessed clean start.

### What it lacks for paper trading futures through IBKR (Gate 2)

The architecture's Gate 2 (`docs/chester-reports-architecture-v3.md`, "Gate 2 —
Paper"): "Orders to the IBKR paper account off Daily Cascade signals, full OCO
brackets … Minimum three months of dwell. The test is … whether realized paper
expectancy matches what the register predicted."

What is missing:
1. **An order path of any kind.** That is deliberate, and it is Gate 2's whole
   build: a separate executor, its own deny-list review and a client id.
2. **A futures contract model.**
   - Today a future is an instrument with a cost class and a multiplier in its
     meta, plus a modelled roll cost.
   - There is no contract chain, expiry calendar or roll rule. `altdata/es_block.py`
     knows CME's roll rule for the ES read, but the lab does not.
   - There are no ES/MES contract specifications or exchange margin.
3. **Intraday matching finer than stored 5-minute bars,** and no quote-level
   queue model. Adequate for the lab's horizons; thin for the intraday engines
   (E-7, DTH-1's two).
4. **Broker reconciliation:** broker positions against the ledger's, halting on
   a mismatch (Gate 4's list, needed in paper too).
5. **Broker-side brackets and OCO.** Exits today are simulated. In paper they
   must be resting orders, and the ledger must read their fills back.
6. **Paper fills against modelled fills.** Nothing yet compares an IBKR paper
   fill with the ledger's modelled fill for the same signal. This is the
   measurement D35's edge-decay pause needs (section 4).

## 2. nautilus_trader, from its public documentation

### Licence

**LGPL-3.0-or-later.** Sources:
- the GitHub README, "available on GitHub under the GNU Lesser General Public
  License v3.0";
- PyPI's JSON (`https://pypi.org/pypi/nautilus_trader/json`), `license`
  "LGPL-3.0-or-later";
- the GitHub API, `spdx_id` "LGPL-3.0".

For this use, a private system that imports the library unmodified and
distributes nothing, the LGPL places no obligation on our code. The obligations
(offering the library's source, allowing relinking) attach on distribution, and
nothing here is distributed. Modifying the library and running it privately is
also unencumbered. This is a reading of the licence's terms, not legal advice; no
clause bars the use.

### Python version and install footprint

- **Python.**
  - PyPI's latest stable, **1.231.0**, `requires_python` ">=3.12,<3.15".
  - The 2.0 line drops 3.12. Its rc7 notes (15 Oct 2026) say "Python 3.13 and
    3.14 are supported"; the README's platform table lists Python 3.13–3.14
    (GitHub releases page).
  - This repo's CI runs Python 3.12 (`.github/workflows/registry-check.yml`), as
    the box's Ubuntu 24.04 ships it. **Adopting 2.x means a second interpreter
    on the box**, 3.13 in its own venv, beside the 3.12 the reports run on.
- **Platform.**
  - Linux x86_64 wheels; the README asks for glibc 2.35 or newer. Ubuntu 24.04
    ships 2.39, so it qualifies.
  - "No Rust toolchain is required to install prebuilt wheels."
- **Memory.** **Not stated** in the README or the docs read. The box has 4 GB,
  with unit memory caps as percentages of the machine (ruled 17 Oct 2026).
  Measuring it would take an install, which this paste forbids, so the footprint
  is an open measurement (decision 3's first trigger).
- **The IB extra.** `nautilus_trader[ib]` pins `nautilus-ibapi==10.45.1` and
  `protobuf==5.29.6` (PyPI's `requires_dist`). That is a second IB client
  library beside the `ib_async` Gate 1 already uses.

### The IB adapter for futures (ES/MES)

Source: https://nautilustrader.io/docs/latest/integrations/interactive_brokers/,
listed **"stable"** on the integrations index.

- **Connection** is through TWS or IB Gateway: paper port 4002 (Gateway) or 7497
  (TWS), live 4001/7496, with "the adapter defaults to `127.0.0.1:4002`". It
  requires "server protocol version 213 or newer". A `DockerizedIBGateway`
  option manages a container.
- **Futures.**
  - Contracts load by symbol and exchange with `build_futures_chain=True`, and
    ids use IB's local symbol (e.g. `YMM6.XCBT`). ES appears in the docs'
    examples; MES is not mentioned but is the same contract family.
  - "IB limits continuous futures to historical data": `CONTFUT` has no live
    subscriptions or orders.
- **Orders.** Market, limit, stop, stop-limit, the if-touched types and trailing
  stops. "Submit order list … includes bracket and linked orders."
- **Paper mode** is IB's own paper account on the paper port. It is not a
  nautilus simulation.

**Its open issues on the order path,** from GitHub issues, open, "Interactive
Brokers" in the title, read 30 Oct 2026. There are **12 open, 10 labelled bug**,
and 36 closed since 1 Aug. Those that touch Gate 2 directly:
- #5464 "Factory brackets are denied because exits are reduce-only" (27 Oct);
- #5463 "Refuses every modify after an order's first" (26 Oct);
- #5277 "Execution client seeds its order ID below IDs it already used, so every
  order is refused" (9 Oct);
- #5350 "An execution without a commission report aborts startup reconciliation"
  (17 Oct);
- #5428, startup reconciliation refuses on IB's avgCost (23 Oct);
- #5353, commission reports after fills (17 Oct).

On data:
- #5394 "Historical ticks get ts_init = receive time" (20 Oct);
- #5384, historical bars "miss bars between duration segments" (20 Oct).

The adapter is maintained actively, with fixes landing weekly, and **unsettled on
exactly brackets, modifies, order ids and reconciliation**, which are Gate 2's
centre.

### The backtest–live parity claim

- **The claim**, from the README: "The same strategy and execution-algorithm
  code can run across backtest and live systems, reducing deployment
  divergence."
- **Its own caveat:** live execution can involve behaviour "that a simulation may
  not reproduce". The backtesting index (`/docs/latest/concepts/backtesting/`)
  lists subpages for fill models, bar-based execution and live differences. The
  bar-based execution subpage answered 404 at its expected URL, so its OHLC
  sequencing is not quoted here.

**What the parity is, and is not.** It is parity between nautilus's simulator
and nautilus's live node: the same strategy object in both. It is **not** parity
between our lab's ledger and IBKR. For us it buys something only if the lab's
engines are rewritten as nautilus strategies.

### The data catalogue

From `/docs/latest/concepts/data/`:
- `ParquetDataCatalog`: models are "serialized as Arrow record batches and
  stored in Parquet files", with prices as `Decimal128(38, 16)`.
- Two timestamps: `ts_event` (when it happened) and `ts_init` ("initialization
  time, not always receipt time"). Replay is "stably sorted by `ts_init`".
- Custom data types are allowed: `@customdataclass` with `ts_event` and
  `ts_init`.
- An older catalogue needs `nautilus catalog migrate-parquet` after schema
  changes.

**There is no vintage, no `available_at` and no revision.** The page does not
address look-ahead. Our store's guarantee, that a row is knowable only from its
`available_at` and a revised value is a new row from its own vintage, has no
counterpart. An adapter that set `ts_init = available_at` per vintage could
imitate it for the newest vintage only. #5394 shows `ts_init`'s meaning still
shifting.

### Maintenance signals

- **Cadence:** "We aim to follow a bi-weekly release schedule" (README). The 2.0
  candidates ran rc3 20 Aug, rc4 2 Sep, rc5 15 Sep, rc6 4 Oct, rc7 15 Oct and
  rc8 28 Oct 2026 (GitHub releases).
- **Breaking changes:** heavy across the 2.0 line. Cython was removed, config
  and adapter classes were renamed (rc4), Python 3.12 was dropped (rc7), and the
  notes say downstream code must be updated.
- **Stable line:** 1.231.0 is current, with releases about every 2–4 weeks
  through 2025 (PyPI upload times, 1.211.0 on 9 Feb 2025 to 1.218.0 on
  31 May 2025).
- **Activity:** 31.1k stars, the last push 30 Oct 2026, 138 open issues
  (GitHub API).

## 3. Side by side

| | In-house (extend `alpha/` plus a thin Gate 2 executor) | nautilus_trader adopted | Middle: nautilus for backtests only, in-house paper |
|---|---|---|---|
| **Point-in-time rule** | Native: the store's `available_at`, `mode=ro`, the hash gate | Lost. `ts_init` has no vintage, so it needs a store-to-catalogue export per run, newest vintage only | Lost for the backtests, kept for paper. The two disagree by construction |
| **Data model** | One: the observation store | Two: the store plus a Parquet catalogue, kept in step | Two |
| **Register and packets** | The register is unchanged; Gate 2 reads the decision and writes nothing to it | Strategies must be wrapped to read decisions; the register stays outside | Unchanged |
| **The gates** | Existing: validate_alpha, no_orders, the deny list. Gate 2's executor gets its own | New gates for an order-capable framework inside the repo; the deny list must name its order entry points | The lab's no-network gate must exempt nautilus's imports, or keep it outside `alpha/` |
| **IBKR futures paper** | To build: contract chain and roll, brackets as resting orders, fills read back, reconciliation (≈ the Gate 2 estimate, ~3 sessions plus the futures model) | Supplied, but with the open bugs on brackets, modify, order ids and reconciliation (section 2) | To build, as in-house |
| **Backtest–paper parity** | Ours to measure: modelled against IBKR paper fills, per signal (section 4) | Theirs: simulator against live node, only for engines rewritten as strategies | None: the backtester and the paper path are different code |
| **Box** | 3.12, already installed; `ib_async` already in use | A second interpreter (3.13), a second IB client (`nautilus-ibapi`), an unknown footprint on 4 GB | As adopted, for the research runs |
| **Upgrade risk** | Ours | A 2.0 line with breaking changes every rc | As adopted |
| **What it buys** | Keeps every invariant | Matching engine, order-book sim, an IB adapter, a large community | Faster event-driven backtests of intraday ideas |

**The middle option's real cost** is the two answers. The lab's grades, the
deflated gate, the RAS gate (91(b)) and the cost cliff (91(c)) are computed on
the in-house ledger. A nautilus backtest of the same engine would give a second
P&L with different fill rules (no "stop wins" convention, a different cost
model) and different timestamps. The operator would then hold two records of one
engine with no rule for which governs. That is what the system refuses for regime
("Do not add a second regime anywhere").

## 4. The edge-decay pause (D35), specified for the in-house engine

This applies whichever engine wins, and needs nothing from nautilus.

- **What is measured, per engine:** for each closed paper position, the
  realised net return R_paper (IBKR paper fills at Gate 2; the ledger's modelled
  fills before it). It is set against R_bt, the engine's frozen backtest
  expectancy per trade: the formation figure the promotion was granted on, read
  from `engines.validation` and never refitted.
- **The statistic:** the rolling mean of R_paper − R_bt over the engine's last
  **N = 20 closed positions**, with its standard error s/√N. This is the
  scoreboard's session-set `min_n` (`config/scoreboard.yaml`). It is mirrored by
  an implementation-shortfall line: the paper fill against the modelled fill, per
  fill, which separates cost drift from edge drift.
- **The threshold, pre-registered:** **pause when the mean shortfall is below
  zero by more than 2 standard errors** (z ≤ −2.0) at N ≥ 20. Below 20, the
  engine prints "accruing (n=k)" and never pauses on decay.
  - The governor's −15% halt and the kill rule run regardless.
  - 2 SE is the line Evidence and Inference's Figure 5 draws. There, a 0.2R edge
    decaying from week 40 is first excluded at week 65 at 200 decisions a year.
    That is the detection lag the operator accepts by this choice, stated beside
    the rule.
  - The cost line pauses separately when the median fill shortfall exceeds the
    modelled spread-plus-slippage by 50% over 20 fills. That is a cost review,
    not an edge verdict.
- **What pauses:** the engine's **new signals.** They are queued in state
  `paused` with the reason, and logged as a `loop_events` row. Open positions
  keep their exits, so a pause never forces a flat at a bad price. Resuming is
  the operator's (a ruled event, like `alpha.governor resume`), or automatic
  after N further *formation-scored* shadow signals clear the threshold. Which
  of the two is decision 4.
- **Pre-registration:** a `spec` block in a new `config/alpha_decay.yaml`, its
  sha256 quoted by each engine's roster entry, as E-6 and E-7 quote theirs. The
  engine refuses a spec that no longer hashes. It is the Enterprise Layer's
  drift trigger, 91(d), made concrete. Its home is 91(d)'s, so one rule serves
  both.

## 5. "Why this could fail" (D35's critic loop)

- **Where it lives:** a required field, `why_this_could_fail`, on every
  hypothesis in `alpha.db`'s register (`alpha/hypotheses.py`; the batch schema
  gains it at v2). It is fixed at pre-registration, before the run, and never
  edited after. It is a list of two to five failure modes, each in a closed
  vocabulary:
  - `mechanism` (the story is wrong);
  - `crowding`;
  - `cost` (the edge is below the cost cliff);
  - `regime` (it lives in one environment);
  - `data` (an artefact of the series or its vintage);
  - `capacity`;
  - `execution`.

  Each mode carries a sentence and, where it can, the stored series that would
  show it.
- **Who writes it:**
  - The proposer writes its own, and a separate critic call writes a second
    list. That call is made in `alpha_proposer/`, outside `alpha/`, through
    `model_meter`. It sees the rule and the mechanism, never the backtest
    result. This is R-1's information partition: "a reviewer that sees the
    evidence and not the thesis".
  - For an operator's or a session's idea, the author writes the list and the
    critic call adds one.
  - The lab promotes nothing whose field is empty.
- **How it is graded:** at kill, retirement or a decay pause, the loop records
  which failure mode the evidence matches. That is an attribution from stored
  series, by rule where the mode named a series, else "unattributed". The score
  is **the share of failures whose mode was listed in advance**, per author
  (proposer, critic, operator, session), over a rolling year, with n. It prints
  in the quarterly meta-loop's page (`alpha/report.py` `quarter_page`). A critic
  that never anticipates the actual failure is visible as such. No LLM writes
  the attribution (R-4: "an LLM never writes counterfactual attribution").
- **For the register's books:** the same field goes on Book C's setup catalogue
  drafts (`config/setups.yaml`), when Book C activates. That is a register change,
  the operator's.

## 6. Decisions for the operator

1. **The Phase 4 paper engine.**
   - (a) in-house: extend `alpha/` and build a thin Gate 2 IBKR paper executor
     on `ib_async`;
   - (b) adopt nautilus_trader for backtest, paper and later live;
   - (c) nautilus for backtests only, with the in-house paper path.

   **Recommend (a).** (b) gives up the point-in-time store and takes on an
   unsettled IB order path. (c) creates two records of one engine.
2. **Where the Gate 2 executor lives.**
   - (a) a new package outside `alpha/` and `register/` (e.g. `execution/`), its
     own deny-list review, client id 21, paper port only, and a gate proving it
     cannot reach the live port;
   - (b) inside `altdata/`.

   **Recommend (a).** The lab's no-orders gate stays absolute.
3. **nautilus as a watched candidate.** Re-assess it as the Gate 2 execution
   node only when all three hold:
   - 2.0 final has been released;
   - the box runs Python 3.13 for another reason;
   - the IB issues on brackets, modify, order ids and reconciliation (#5464,
     #5463, #5277, #5350, #5428) are closed.

   At that point a laptop-only footprint measurement is the first step.
   **Recommend yes**, with the triggers written into the Phase 4 brief, or
   (b) drop it.
4. **The edge-decay pause's resume.**
   - (a) the operator's ruled event only;
   - (b) automatic after 20 shadow signals clear the threshold.

   **Recommend (a)** for the first year, as the governor's halt is. The numbers
   (N = 20, z ≤ −2, the cost line at +50%) are proposed for pre-registration in
   `config/alpha_decay.yaml` at 91(d)'s build.
5. **"Why this could fail".**
   - (a) required on every hypothesis from batch schema v2, with the critic call
     partitioned from results;
   - (b) required only on promotion to paper.

   **Recommend (a).** The field is cheapest and most honest before the run.
6. **ES against MES for Gate 2's futures dwell.**
   - (a) MES, a tenth of the notional: the same signals and the same bracket
     logic, and dwell costs are a rounding error;
   - (b) ES.

   **Recommend (a).** Gate 2's test is expectancy matching, not size.

## Why this could fail (this assessment's own)

- **The in-house executor is underestimated.** Brackets, modifies, order ids and
  reconciliation are exactly where nautilus's IB adapter still has open bugs.
  Ours will meet the same IB behaviours, and the ~3-session Gate 2 estimate may
  be light. Mitigation: build reconciliation first and dwell three months as
  ruled.
- **nautilus's 2.0 settles quickly and the case for it strengthens.** Decision 3
  exists so that a better candidate is noticed rather than ignored.
- **The pause fires on noise.** At N = 20 a 2-SE rule still errs. That is why
  resume is the operator's and why the rule is pre-registered with its stated
  lag.
- **The memory footprint was not measured.** No install was allowed. If it fits
  easily, one argument against (b) and (c) weakens, but the point-in-time
  argument does not.
