# Layer X — the Alpha Lab

**Status:**
- **Tranche 1**, the foundation (X-1.1 to X-1.13), was built 13 October 2026 on
  branch `alpha-lab-1`.
- **Tranche 2**, the first engines and the idea pipeline (X-2.1 to X-2.11, with
  the amendments of 14 October in the change order's section 10), was built
  14 October 2026 on branch `alpha-lab-2`, stacked on Tranche 1.

Ruled 12 October 2026: the brief `docs/briefs/alpha-lab-brief-2026-10-12.md`
(decisions 1–9) and the change order `docs/change-order-alpha-lab-2026-10-12.md`.
The amendments of 14 October were ruled in chat at 04:13 and 04:22 CT.

Four engines are registered, all candidates until their hypotheses pass:
`trend_ts`, `trend_xs`, `pm_futures` and `vrp_dealer`. The branch notes are
`docs/briefs/alpha-lab-1-notes.md` and `docs/briefs/alpha-lab-2-notes.md`.

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
| Loops | `alpha/loops/nightly.py`, `alpha/loops/weekly.py` | nightly: ingest, test, promote, learn from the ledger; weekly: walk-forward, bounded re-fit, rebalance, agenda, verdicts |
| Lines | `alpha/lab_line.py` | the Weekly's and the Daily close's one line each, read-only |
| Register | `alpha/hypotheses.py`, `alpha/intake.py` | every idea pre-registered before its test, on the batch schema alpha-lab-hypotheses v1; failures kept |
| Grammar | `alpha/rules.py`, `config/alpha_rules.yaml`, `docs/alpha-lab-rules.md` | a rule written as data, interpreted point-in-time; no code per idea |
| Workbench | `alpha/research/` | `python -m alpha.research new \| run \| report`; the committed translations of the first batch |
| Inbox and outbox | `alpha/inbox.py`, `alpha/outbox.py` | batches from Drive pre-registered at their creation time; the weekly verdicts back to Drive |
| Promotion | `alpha/promote.py`, `alpha/engines/grammar.py` | a passed idea to paper at min_size on the loop's authority; the model-idea rule; the operator's retirement by ruling |
| Engines | `alpha/engines/trend.py`, `pm_futures.py`, `vrp.py` | X-2.2, X-2.3, X-2.1 (the VRP is a coverage check until option quotes are stored) |
| Files | `alpha/files.py` | the lab's one file writer, confined to the roots `config/alpha.yaml` declares |
| Report | `alpha/report.py` | the monthly Lab report, attached to the Monthly |
| Proposer | `alpha_proposer/` (outside `alpha/`) | the daily proposer: one model call over a code-built packet, at most three ideas into the inbox |

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
- **No other writes.** It writes `alpha.db`, and files only through
  `alpha/files.py`, under the roots `config/alpha.yaml` declares (the research
  dir, the reports dir, the outbox). `tools/validate_alpha.py` group A checks
  that no other module writes a file. The observation store's hash is
  unchanged after a nightly run: group J checks that.

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
| Nightly | weekdays 17:40 ET (`chester-alpha-nightly.timer`), after the 16:45 close's capture | ingest the inbox; run the harness on what was registered; fill, mark, grade; the governor; posteriors; kill; cost calibration; weights proposed; attribution by regime key; drift; signals; promote |
| Proposer | weekdays 18:10 ET (`chester-alpha-proposer.timer`), after the nightly loop | one model call; at most three hypotheses into the inbox, for the next night |
| Weekly | Sunday 06:00 ET (`chester-alpha-weekly.timer`), after the Weekly | walk-forward extended; the bounded re-fit; the rebalance; the agenda; the verdicts to the outbox |
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
and are not in `DEPLOY_TIMERS`: see `deploy/systemd/README.md` section 14.

## 5. What prints

| Where | What |
|---|---|
| The Weekly's header | `Alpha Lab: +x.x% since <date> · n engines live · drawdown y% (z% since inception) · loop events this week k` |
| Before the first engine | the same header reads `Alpha Lab: not yet live` |
| The Daily close's header | `Alpha Lab today: n proposed · k screened out · j testing · m promoted · lab equity x% · drawdown y%` |
| Monthly | the Lab report, X-2.8, attached to the Monthly's mail |
| Drive, weekly | `lab-verdicts-YYYY-MM-DD.md` and `lab-agenda-YYYY-MM-DD.md` in `chester-vendor-checks/lab-outbox/`, for the Saturday brief and the sitting |
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

## 8. The idea pipeline (Tranche 2; change order section 10)

**Every idea is pre-registered before any test of it runs.** There are four ways
in, and all of them pass through `alpha/intake.py`:

| Channel | Source | Pre-registered at | Budget |
|---|---|---|---|
| The Saturday brief, a chat-side task, via Drive's `lab-inbox` | model | the file's Drive creation time (the sweep's `rclone lsjson --metadata` manifest, `Metadata.btime`) | 5 short + 5 medium a batch, 2 a family |
| The daily proposer (`alpha_proposer/`, 18:10 ET) | model | its manifest line's write time | 3 a session day, 2 a family a week |
| The workbench (`python -m alpha.research new`) | operator or chat | the instant `new` registers it | none |
| The research sitting, fortnightly, via Drive's `lab-inbox` | model | the file's Drive creation time | 5 a batch |

**Admission sorts each hypothesis into one of five outcomes:**
- **refused:** the batch is refused if it fails the schema, was edited more than
  five minutes after it was created, was written after it existed, or repeats a
  batch_id; a single hypothesis is refused if it names a blocked instrument;
- **screened out:** a duplicate of anything in the register, failures included,
  or over a budget;
- **data_gap:** it names a series or instrument the store does not hold;
- **needs_code:** its rule is in text only;
- **registered:** its rule is in the grammar, or it is a registered engine.

**Every admitted hypothesis counts in its family's variant count.**

**The harness runs registered ideas the night they arrive.** Each goes through
X-1.6 unchanged, capped by `research.max_runs_per_night`. A model's idea must
also pass the model-idea rule:
- non-negative expectancy after costs on data after 2026-07-01;
- 1.5 × min_signals at minimum size in paper before the allocator may raise it.

**Promotion is the loop's own.** A passed grammar rule trades through
`alpha/engines/grammar.py`, exactly as its backtest read it. A coded engine
trades through its own class. The operator retires either by ruling
(`python -m alpha.promote retire`, denied to sessions). A lab halted at -15%
stays halted until the operator runs `python -m alpha.governor resume --reason
"..."` (ruling 6), also denied to sessions; the resume re-bases the lab's
high-water mark.

**The weekly loop closes the circle.** It writes the agenda of misses and the
verdicts back to Drive for the next brief and the next sitting.

## 9. Tranche 3, part 1 (alpha-lab-3, 17 Oct 2026; change order section 5)

Pulled forward from November: X-3.6, X-3.1 and X-3.2. Nothing here changes the
constitution, and the lab still writes only alpha.db and its own files.

**Pre-registration by manifest.** `alpha/manifest.py` writes a batch's manifest,
holding the batch, its sha256 and its instant, under the research directory before
the register takes the batch. That instant is every hypothesis's
`pre_registered_at`, and the manifest's sha256 is on the batch row. Drive's
created time and the proposer's manifest line count as manifests too.

The harness (`workbench.run`) refuses a hypothesis:
- whose batch carries no manifest;
- whose manifest is dated after the run;
- whose manifest file no longer hashes to what was registered.

The workbench's `new`, the tells importer and the X-3 roster all register this
way. The box registers the roster with
`python -m alpha.manifest register alpha/research/roster-2026-10-17-x3.yaml`.

**X-3.6, tells as hypotheses** (`alpha/tells.py`, `config/alpha_tells.yaml`). The
importer reads four sources:
- the Weekly's tells (the Book B scanner's `tells:`);
- the Doctrine's section 5.3 trust matrix and Rule 9;
- the setups in `config/setups.yaml`;
- the probability ledger's graded sources, read by SQL over the read-only store.

Each tell becomes one hypothesis, "predicts at h sessions after costs?". It is
registered needs_code, as source `tell` on the channel `importer`. Its mechanism
is quoted word for word from the cited section, and the quote is checked. Its
horizon comes from the tell's own window.

The importer is idempotent:
- an unchanged tell writes nothing;
- a changed one is a new registration, and the old one is marked superseded (status
  refined, `superseded_by` set);
- a tell no paper states is not imported, and the import report says why. The move
  screen is one, and so is a forecast source with no declared paper.

The lab line and the Lab report print the count by source. Nothing is tested
here.

**X-3.1, engine 4, scheduled events.**

The base rates come first. `python -m alpha.event_rates compute` writes them to
`event_base_rates`, each row with its n, window and unit:
- for CPI, payrolls and FOMC: the first session's drift, the next session's drift
  and the VIX's change, by naive surprise, positioning and dealer regime;
- for earnings in the 29 names: the 1- and 20-session drift by the sign of the
  real surprise, and the realised reaction. The implied move is "awaiting", since
  none is stored.

The engine follows (`alpha/engines/events.py`):
- `events_macro`: CPI and payrolls, the next session by surprise bucket;
- `events_fomc`: by positioning;
- `events_pead`: the 20-session drift;
- `events_crush`: a data gap, since no tradable volatility instrument is stored.

**X-3.2, engine 5, crypto carry** (`alpha/engines/carry.py`,
`config/alpha_crypto_venues.yaml`). It is long spot and short the perp on the venue
paying the most. Its switch is S-3's funding regime (calc.funding_agg and
calc.leverage_z). Venue fees are dated constants, and funding accrues daily. The
basis is a listed gap, because no perp mark is stored.

The engine runs nothing until the store holds the manifest's 92-week window, and
until then prints "insufficient history". Once live (after the gate), the nightly
loop's carry step books the paper book's crypto rows in `carry_book` and
`carry_accruals`, and `book.cum_pnl` reads them.

The gate is `tools/validate_alpha_lab_3.py`. Part 2 takes X-3.5 (the grammar
search) and X-3.7 (the quarterly meta-loop). Engines 6 and 7 wait for their
preconditions.
