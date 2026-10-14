# Layer X — the Alpha Lab

**Status:** Tranche 1, the foundation (X-1.1 to X-1.13), built 13 October 2026 on
branch `alpha-lab-1`. Ruled 12 October 2026: the brief
`docs/briefs/alpha-lab-brief-2026-10-12.md` (decisions 1–9) and the change order
`docs/change-order-alpha-lab-2026-10-12.md`. No engine is registered; the first
engines are Tranche 2's.

## 1. What it is

Beside the four books and the five reports there is one independent layer: a
machine's book in **ledger-paper** that reads the observation store and writes
nothing back to it, to the register, to the narrative ledger or to any report.
It has four restraints and no others:

1. **The Brookfield blocklist**, the system's own, applied at signal time.
2. **Ledger entries against stored prices.** There is no order path of any kind
   before the Gate 3 ruling.
3. **A risk governor.**
4. **An evidence gate.**

Inside those it searches, trades, learns and innovates on its own authority.
Its results are tabled at sittings as evidence, and each rung of the gate ladder
is the operator's ruling.

## 2. Architecture

| Piece | File | What it does |
|---|---|---|
| Ledger | `alpha/ledger.py` | `alpha.db`, the only database the lab writes |
| Store | `alpha/store.py` | the observation store, opened `mode=ro` through the point-in-time reader |
| Engines | `alpha/engine.py`, `config/alpha_engines.yaml` | the interface; the registry is the only place an engine is named |
| Costs | `alpha/costs.py`, `config/alpha_costs.yaml` | eight cost classes, never the mid |
| Paper | `alpha/paper.py` | fills at the next stored bar's open or a stored quote; bracket exits bar by bar; daily marks; grades |
| Harness | `alpha/validate.py` | point-in-time, walk-forward with the embargo, the hold-out, the deflated Sharpe, the minimum sample, the pass record |
| Allocator | `alpha/allocate.py` | quarter-Kelly, the heat cap, correlated engines counted once |
| Governor | `alpha/governor.py` | high-water marks; halve, stop, halt |
| Loops | `alpha/loops/nightly.py`, `alpha/loops/weekly.py` | learn from the ledger nightly; rebalance weekly |
| Line | `alpha/lab_line.py` | the Weekly's one line, read-only |

**The ledger lives at `{data_root}/alpha.db`.** That is beside the observation
store: `config/alpha.yaml` sets `ledger.path`, and `$ALPHA_DB` overrides it. On
the box this is `~/chester-reports/data/alpha.db`.

- The nightly sweep (`scripts/rclone_sync.sh`) snapshots it the way it snapshots
  `chester.db`: online backup, integrity check, gzip round trip, staged dated
  into `db/`.
- The live file is never uploaded raw.

**Its tables** are the change order's, plus two it did not name:

- `allocations` holds the allocator's proposed and applied weights per engine
  per day.
- `equity` holds each engine's equity index and the lab's dollars, with the
  high-water mark and the drawdown.

Every row carries `as_of` and `written_at`. `loop_events` is append-only: a
change is reversed by a new event, and the old row gains `reversed_by` once.

**What `alpha/` may never do.** `tools/validate_alpha_no_orders.py` holds every
item below, in CI on every push.

- **No forbidden imports.** It may not import:
  - the order gate, or the register (any of `register/`);
  - the broker modules;
  - the probability ledger or the narrative ledger;
  - the report writers;
  - any network library or the repo's fetchers;
  - `subprocess`.
- **No network or order code.** It may not use `requests`, `urllib`, `socket`,
  or any order-routing name.
- **The blocklist without the register.** The system's blocklist is reached by
  loading `register/instruments.py` from its file. The `register` package is
  never imported, because its `__init__` imports the decision writer.
- **No other writes.** It writes no file: `tools/validate_alpha.py` group A
  checks this. The observation store's hash is unchanged after a nightly run:
  group J checks that.

## 3. The constitution

The file is `config/alpha_constitution.yaml`. It is read by every loop and
written by none. It carries exactly the change order's section 2 values.

A session changes a value only on a paste that quotes the ruling, and then:

- adds a row to the hash ledger below, with the new sha256 and the ruling it
  quotes;
- leaves every earlier row as it stands.

`tools/validate_alpha.py` fails when the file's sha256, taken over its bytes with
line endings normalised to LF, is not in a row of that table carrying "Ruled".

### The constitution, verbatim

```yaml
objective: "maximise expected log growth of the lab's notional capital net of modelled costs, subject to the governor"

# raised only by ruling, on the ledger's evidence
kelly_fraction: 0.25

governor:
  engine:
    # from the engine's own high-water mark; stop -> status `validation`, frozen
    halve_at: -0.10
    stop_at: -0.20
  portfolio:
    # from the lab's high-water mark -> status `halted`, operator review
    stop_at: -0.15

validation:
  embargo: "one engine horizon between fit and test windows"
  embargo_horizons: 1
  # independent signals, before any size above minimum
  min_signals:
    daily: 100
    weekly: 40
    intraday: 400
  # at the engine's sample, deflated by the ledger's variant count for that
  # engine family
  deflated_sharpe_min: 1.0
  min_size_period: "the first min_signals paper signals at minimum size regardless of backtest"

kill:
  rule: "after min_signals: expectancy after modelled costs <= 0, or realised Sharpe < 0.5 x the deflated Sharpe it was validated with"
  expectancy_at_or_below: 0.0
  realised_sharpe_below_deflated_multiple: 0.5

holdout_months:
  rule: "every fourth calendar month of history, never fitted by any loop; used only for the final check before a promotion"
  every: 4

refit:
  # a halved or stopped engine is never re-fitted
  frozen_in_drawdown: true

orders:
  value: none
  rule: "alpha/ may not import any order, gate, broker or network module (static gate)"

blocklist:
  rule: "the system's, applied at signal time; a blocked instrument never reaches the ledger"
```

The file's header comment, which explains this rule, is omitted above. The
comment is part of the hashed bytes.

### The hash ledger

| Date | sha256 | Ruling |
|---|---|---|
| 13 Oct 2026 | `09ade9116752f9fdedc2ba8515bc4013b71b30772321a4d7ec9909ebcd82a86a` | Ruled 12 Oct 2026 — the change order's section 2, decisions 1–9 of the brief (accepted 20:28 and 20:40 ET) |

### How the constitution's sentences are read

These readings are the session's, and each is recorded in the branch notes for
the operator to overrule.

- **The hold-out** is the months whose number divides by four: April, August
  and December, in every year.
  - Those rows are removed before any walk-forward.
  - No fit and no walk-forward test sees them.
  - They are used once, at the end of a validation run, as its final check: the
    hold-out's expectancy after costs must be positive.
- **The embargo** is one engine horizon in rows: one session for a daily or
  intraday engine, five for a weekly one.
- **The deflated Sharpe** follows Bailey and López de Prado.
  - The out-of-sample Sharpe per signal, less SR0, is annualised at the
    sample's own signal rate. SR0 is the expected maximum Sharpe of N variants
    under the null, at the sample's skew and kurtosis.
  - N is the family's variant count in `alpha.db`, including the run itself.
  - "Deflated Sharpe ≥ 1.0" applies to that annualised difference. The
    probabilistic form is recorded beside it.
- **The minimum sample** is also a condition of the validation pass: at least
  `min_signals` out-of-sample signals.
- **A halved engine** returns to `live`, unfrozen, when its equity makes a new
  high-water mark.
  - A stopped engine (`validation`) returns only through validation.
  - A stopped or killed engine's open positions are exited at the next stored
    bar's open.
- **The lab's halt** stays until an operator event, `lab_resume`, with source
  `operator`. Tranche 1 provides no command for it.

## 4. The loops

| Loop | When | Tranche 1 |
|---|---|---|
| Nightly | weekdays 17:40 ET (`chester-alpha-nightly.timer`), after the 16:45 close's capture | fill, mark, grade; the governor; posteriors; kill; cost calibration; weights proposed; attribution by regime key; drift |
| Weekly | Sunday 06:00 ET (`chester-alpha-weekly.timer`), after the Weekly | the allocator's rebalance; the re-fit and the research agenda are X-2.4's |
| Fortnightly | the research sitting | X-2.7 |
| Quarterly | the meta-loop | X-3.7 |

**Session-set values** live in `config/alpha.yaml` and are recorded where they
are used:

| Value | Setting | Recorded on |
|---|---|---|
| Shrinkage prior strength | 20 pseudo-signals toward zero edge, at a win rate of 0.5 | every `edge_posterior` row |
| Correlation threshold | 0.7 over 120 days, at least 20 in common | every `weights_proposed` event |
| Heat cap | 1.0, i.e. no leverage | every `weights_proposed` event |
| Drift band | 2 standard errors over the last 60 graded signals | — |
| Notional | 100,000 lab dollars | — |

**The regime key** is read from the stored market-state object and never
recomputed. It takes the form `macro=<state>|vol=<state>|gamma=<state>|event=<0|1>`.

**Enabling the loops is the operator's.** The units are copied by the deploy
and are not in `DEPLOY_TIMERS`: see `deploy/systemd/README.md` section 13.

## 5. What prints

| Where | What |
|---|---|
| The Weekly's header | `Alpha Lab: +x.x% since <date> · n engines live · drawdown y% · loop events this week k` |
| Before the first engine | the same header reads `Alpha Lab: not yet live` |
| Monthly | the Lab report, X-2.8 |
| Quarterly | the lab page, X-3.7 |
| Anywhere else | nothing |

The Weekly's line is read from `alpha.db` read-only, by one hook in
`daily_cascade/weekly_stack.py`.

## 6. The gate ladder

- **Ledger-paper** is where the lab lives now.
- **Broker-paper** through the order gate comes after Gate 1.5.
- **Live** comes after Gate 3, not before 2027.

Each rung is the operator's ruling, never the lab's.

## 7. Gates

| Gate | What it checks |
|---|---|
| `tools/validate_alpha.py` | the constitution and its hash; the ledger; the read-only store; the interface; the costs; paper; the harness's synthetic tests; the allocator; the governor; the nightly loop end to end; the Weekly's line; the units |
| `tools/validate_alpha_no_orders.py` | the static and import-time no-orders gate |

Both are code gates in the Makefile, so CI runs them on every push. Neither
reads the live store.
