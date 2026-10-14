# Alpha Lab, Tranche 1: the foundation (X-1.1 to X-1.13), session notes, 13 Oct 2026

Branch `alpha-lab-1`, from main at `cc91752`. It is branch-only: nothing merged, nothing deployed, nothing run on the box.

The sources are the change order `docs/change-order-alpha-lab-2026-10-12.md` (sections 2, 3, 6, 8 and 9) and the brief `docs/briefs/alpha-lab-brief-2026-10-12.md` (sections 3, 4 and 8). The architecture, the constitution verbatim with its hash, and the loops are in `docs/alpha-lab.md`.

**All thirteen items are built.** Both new gates are green, and so are the existing gates on everything touched (see "Gates").

## What each item built

| Item | Built |
|---|---|
| **X-1.1** Package and ledger | `alpha/` beside the existing packages. `alpha/ledger.py` owns `alpha.db` (see "The `alpha.db` path" below). `alpha.db` holds the change order's thirteen tables plus two it did not name; every row carries `as_of` and `written_at`. Also: the blocklist triggers, an append-only `loop_events`, the variant count, the hold-out table, and `python -m alpha.ledger snapshot` (SQLite's online backup). The nightly sweep backs it up (see "Not named by the change order", item 6). |
| **X-1.2** Read-only store | `alpha/store.py`'s `ReadOnlyStore` subclasses `altdata.observations.ObservationStore` over `file:…?mode=ro`. It never runs the parent's `__init__`, which would create the schema, switch the journal mode and migrate. It refuses `write()` and `write_many()`, and reads the bars table on the same connection. Its readers: daily OHLC from `yfinance.<key>` and `_open`/`_high`/`_low`/`_volume`, a stored bid/ask pair, and the market-state object. **The test:** the store file's sha256 is unchanged after 38 nightly runs, a weekly run and a failed run on the fixture, and its WAL holds nothing. |
| **X-1.3** The engine interface | `alpha/engine.py`. `Engine` is abstract over `universe`, `signal(as_of, store)`, `size(signal, risk_budget)` and `exits(position, bar)`. It declares `engine_id`, `family`, `horizon`, `cost_class`, `validated_ranges`, `kill_rule` and `min_size`. `config/alpha_engines.yaml` is empty (`engines: []`), and an engine module outside `alpha/engines/` will not load. |
| **X-1.4** The cost model | `alpha/costs.py` with `config/alpha_costs.yaml`, covering eight classes: ETF, single name, index option, equity option, future, perp, prediction-market contract, FX pair. A fill crosses half the stored quote's spread (a buy at the ask, a sell at the bid), or half a fixed estimate where no quote is stored. On top of that it pays slippage of `impact × √(notional / dollar ADV)` with a floor, and commission. Over the holding period it also pays borrow (shorts only), roll, funding and FX, charged on the exit fill. Every component is stored on the fill. **It never fills at the mid.** |
| **X-1.5** Simulated execution | `alpha/paper.py`. A signal fills at the next stored bar's open plus costs, or at a stored quote that is newer than the signal. Exits are walked bar by bar, bracket-style. Positions are marked daily at the latest stored close, net of entry costs. Each closed position is graded once: gross, every cost, net, net return, and its exit day's regime key. `tools/validate_alpha_no_orders.py` checks the source by AST, then imports every alpha module in a fresh interpreter and searches `sys.modules`. It drives 23 synthetic defects through its own scanner as a self-test. 45/0. It is in the Makefile, so CI runs it on every push. |
| **X-1.6** The validation harness | `alpha/validate.py`. It reads point-in-time only: `pit_series()` takes the vintage knowable at each decision, and a row knowable after its decision voids the run. It runs walk-forward with the embargo of one horizon in rows. Hold-out rows are removed before any fit or test and used once, as the final check. The deflated Sharpe uses N, the family's variant count including the run, which `bump_variant` adds to on every run, pass or fail. It applies the minimum-sample check, and writes the pass record (metrics, the ranges the fits chose, the kill rule at birth) to `engines`. **Fixtures:** the known-edge series passes with deflated Sharpe 2.77 (n=653); the null series fails at −0.11; the deflated Sharpe falls 4.73 → 3.94 → 3.46 → 3.09 at N = 1, 10, 100, 1000. |
| **X-1.7** The allocator | `alpha/allocate.py`. Weights are `w = 0.25 × Σ⁻¹ μ`, with μ shrunk the same way as the posteriors. Engines whose returns correlate above the threshold form one cluster: it is sized once on the cluster's average return and the weight is split equally. An engine below `min_signals` graded signals is held at `min_size`. A halved engine carries half its weight, and a negative weight is set to zero. The heat cap scales every weight above minimum. |
| **X-1.8** The governor | `alpha/governor.py`. It keeps an equity index per engine and the lab's equity in dollars, each with its high-water mark and drawdown, in `equity`. At −10% an engine is halved and frozen. At −20% it is stopped: status `validation`, frozen, positions exited at the next stored bar's open. At −15% the lab is halted: every position is exited and no new signals are taken until an operator `lab_resume`. Every transition is a `loop_events` row. `validate.refit_allowed()` refuses a frozen engine. |
| **X-1.9** The nightly loop | `alpha/loops/nightly.py` runs eleven steps, each wrapped in its own `try`, so a failure costs only that step and is written as a `failure` event. The steps: hold-out and registry, paper, marks, governor, posteriors, kill rule, cost calibration, proposed weights, attribution by regime key, drift, tonight's signals. The posteriors are Beta-binomial on the win rate and normal–normal on expectancy, both shrunk toward zero, with the prior recorded on every row. Every change is a `loop_events` row. `alpha/loops/weekly.py` applies the proposed weights (the rebalance). |
| **X-1.10** Units and timers | `deploy/systemd/chester-alpha-nightly.{service,timer}` and `chester-alpha-weekly.{service,timer}`, with the wrappers `scripts/run_alpha_nightly.sh` (lock, `git pull --ff-only`, the session-calendar guard, status file) and `scripts/run_alpha_weekly.sh`. The timers are not in `DEPLOY_TIMERS`: the deploy copies the units and **enabling them is the operator's**. The enable command is printed in `deploy/systemd/README.md` section 13 and in "Needs you" below. |
| **X-1.11** The Weekly's lab line | `alpha/lab_line.py` prints "Alpha Lab: +x.x% since <date> · n engines live · drawdown y% · loop events this week k", or "Alpha Lab: not yet live" until an engine is live or halved. It opens `alpha.db` with `mode=ro`, never creates it, and never raises. **The hook is a three-line diff** in `daily_cascade/weekly_stack.py`: one import and one assignment in `produce()`, and one `extra_html=` argument on `render()`'s `page_header` call, so the line prints in the header block. It reads the `alpha.db` beside the store the Weekly was given. |
| **X-1.12** Gates and fixtures | `tools/validate_alpha.py`, 110/0, groups A–M, on a synthetic store and the committed fixtures `tests/fixtures/alpha/ledger_fixture.json` and `fixture_engine.py`. It covers the constitution hash check, including the cases that must fail, and the no-orders scan. In the Makefile, so CI runs it. No gate reads the live store. |
| **X-1.13** Documents | `docs/alpha-lab.md`. A CLAUDE.md section, "Layer X — the Alpha Lab (`alpha/`)", and the gate count raised to fifty-nine (fifty-six Python). The Doctrine paragraph is Appendix D.3 of `docs/whitepapers/operating-doctrine-whitepaper.md`, as a **docs-only commit of its own, last**. |

## The values chosen

**The `alpha.db` path.** It is `{data_root}/alpha.db`, where `{data_root}` is the observation store's directory (`altdata.observations.DEFAULT_DB`'s parent). That puts it beside the store, as the change order asks. On the box this is `~/chester-reports/data/alpha.db`, next to `chester.db`. `config/alpha.yaml` holds the template (`ledger.path`), and `$ALPHA_DB` overrides it.

**The nightly timer runs at 17:40 ET, Monday to Friday.** I checked the cascade's capture time:
- `chester-daily-close` fires at 16:45 with up to 60 s of jitter.
- It settles the prices (VIX is struck at 16:15) and writes the session's market-state object.
- It is capped by `TimeoutStartSec=10min`, so it is done by 16:56 at the latest.
- `chester-ibkr-sync`'s last slot is 17:30, and the self-deploy's next tick is 17:50.

17:40 is after all of these. Holidays are skipped by the wrapper's calendar guard.

**The weekly timer runs Sunday at 06:00 ET**, after the Weekly's 05:00 run and its 15-minute cap.

The gate checks both orderings from the unit files themselves (group L).

**The other session-set values** are in `config/alpha.yaml`:

| Setting | Value | Where it is recorded |
|---|---|---|
| Shrinkage prior strength | `prior_signals: 20` toward zero edge (win-rate prior 0.5, expectancy prior mean 0). Twelve signals keep 12/32 of their raw edge; a hundred keep 100/120. | Every `edge_posterior` row (`prior_strength`, `prior_win_rate`, `prior_exp_mean`) |
| Correlation threshold | 0.7 on daily returns over the trailing 120 days, with at least 20 days in common | Every `weights_proposed` event, with the heat cap and the clusters |
| Heat cap | 1.0 (no leverage) | Every `weights_proposed` event |
| Notional capital | 100,000 lab dollars | |
| Drift band | 2 standard errors of the realised Sharpe over the last 60 graded signals | |
| Cost-calibration window | 60 days | |

## Not named by the change order, so chosen here

1. **Two tables beyond the change order's list.**
   - `allocations` holds weights per engine per day, `proposed` by the nightly loop and `applied` by the weekly loop. The change order says the nightly loop computes the weights and the weekly loop rebalances, so both needed somewhere to live.
   - `equity` holds the governor's equity, high-water marks and drawdowns.
2. **Columns beyond the change order's list.**
   - `engines.frozen`, which X-1.8 implies.
   - `signals.state` (`pending`, `filled`, `expired` after five sessions without a stored price, or `cancelled`).
   - `loop_events.source` (`loop` or `operator`).
   - `restricted_instruments`, the mirror the triggers read.
3. **How the constitution's sentences are read.**
   - The constitution file carries the section 2 values only. Where a value is a sentence, the number the code needs sits beside it under the same key: `embargo_horizons: 1`, `holdout_months.every: 4`, and the kill rule's two numbers.
   - **The hold-out** is every month whose number divides by four (April, August, December). Its final check requires the hold-out's expectancy after costs to be positive.
   - **"Deflated Sharpe ≥ 1.0"** is read as the annualised (SR − SR0), per Bailey and López de Prado. The probabilistic form is recorded beside it.
   - **The minimum sample** is a condition of passing validation, as well as of sizing.

   `docs/alpha-lab.md` section 3 states all of these.
4. **Governor details the constitution leaves open.**
   - A halved engine returns to `live`, unfrozen, when its equity makes a new high-water mark.
   - A stopped or killed engine's open positions are exited at the next stored bar's open.
   - The lab's halt stays until an operator `lab_resume` event. **Tranche 1 ships no command to write one** (see "Needs you").
5. **The kill rule runs in the nightly loop.** Once an engine has `min_signals` graded signals, if the rule fires it is set to `retired`, frozen, and its positions are exited. The brief's section 8 lets the loop "retire an engine under the kill rule" alone.
6. **The backup set.** The brief puts it in `scripts/deploy.sh`, but `deploy.sh` holds no backup set. The nightly sweep, `scripts/rclone_sync.sh`, does, so alpha.db went there.
   - **What it does:** snapshots `alpha.db` through `python -m alpha.ledger snapshot`, runs the integrity check and the gzip round trip, stages the file dated as `db/alpha-YYYY-MM-DD.db.gz`, and excludes `/alpha.db*` from the `data/` tree.
   - **No alpha.db yet** is a logged skip.
   - **A failed alpha snapshot** fails the sweep as rc 3, named, after every tree has run. chester.db is untouched.
   - **Retention:** the db/ prune only touches `chester-YYYY-MM-DD` names, so alpha's snapshots accumulate (see "Needs you").
7. **The blocklist without importing `register`.** `register/__init__.py` imports the decision writer. So `alpha/blocklist.py` loads `register/instruments.py`, the system's own rule, from its file. The no-orders gate checks that the `register` package never loads.
8. **The no-orders gate forbids more than the change order lists:**
   - the probability ledger, the narrative ledger and the grader;
   - `state.emit` (a POST), delivery, and `monthly_macro`;
   - `subprocess`, `os.system` and `os.popen`, the way around all of the above;
   - CLAUDE.md's deny-list order names and `--allow-live`.
9. **Engines must live in `alpha/engines/`**, so the static gate reads them. The fixture engine lives in `tests/fixtures/alpha/`, and the gate lets that package in only while its test runs.
10. **The weekly loop in Tranche 1 does the rebalance only.** Re-fitting and the research agenda are X-2.4's.
11. **The lab line prints "Alpha Lab: unavailable (<error>)"** if `alpha.db` cannot be read, rather than failing the Weekly.
12. **"The two-session rule unchanged" (X-1.13)** is read as the build rule in the change order's calendar: sessions A or B, never a third. Correct me if it means something else.

## Gates

| Gate | Result |
|---|---|
| validate_alpha (new) | 110/0 |
| validate_alpha_no_orders (new) | 46/0 (after the CI fix below) |
| validate_weekly_stack | 68/0 |
| validate_config_refs | 29/0 |
| validate_deploy | 118/0 |
| validate_secrets | 37/0 |
| validate_gates | 31/0 |
| validate_systemd_units | 83/0 |
| validate_weekly_storyline | 30/0 |
| validate_weekly_opener | 28/0 |
| validate_backup | 63/0 |
| check_library | 0 failures, 0 warnings (after the Doctrine edit, with its HTML rebuilt) |

**CI.** The first push's run, **#347**, failed one gate: validate_alpha_no_orders. On the runner's Python, the standard library's own `pathlib` imports `urllib.parse`, a string quoter, so the import-time check saw `urllib` loaded. The laptop runs 3.14, so this only showed in CI.

The fix: `urllib` and `urllib.parse` are allowed at import time only. A new check fails if `urllib.request`, `http.client`, `socket`, `ssl` or `requests` is loaded. The static scan still forbids `alpha/` importing any of them.

The fix commit follows the Doctrine commit, rather than rewriting the pushed branch. The Doctrine change is still a docs-only commit of its own.

## Needs you

1. **Merge** `alpha-lab-1` on your word, inside a window, after Friday's merges. yes / no
2. **Enable the timers** on the box once merged, inside the windows (printed, not run):
   ```bash
   systemctl --user enable --now chester-alpha-nightly.timer chester-alpha-weekly.timer
   systemctl --user list-timers 'chester-alpha-*'
   ```
3. **The constitution's readings** (Not named, item 3). Hold-out = April, August and December; deflated Sharpe = annualised SR − SR0; the hold-out check = positive expectancy; minimum sample also required to pass. keep / rule otherwise
4. **The governor's open points** (Not named, item 4). Halved → live at a new high; stop and kill exit positions at the next open. keep / rule otherwise
5. **How the lab's halt is lifted.** At −15% the lab halts until an operator `lab_resume` event. There is no command for it. Add one as an operator-only CLI, denied to sessions like the register writes? add / leave
6. **The session-set numbers:** notional 100,000; shrinkage 20; correlation 0.7; heat cap 1.0; the cost defaults in `config/alpha_costs.yaml`. ok / change
7. **Backup retention for `alpha-*` snapshots.** Keep them all (small files), or extend the db/ prune rule to them? keep / prune
