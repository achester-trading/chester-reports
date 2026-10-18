# Alpha Lab, Tranche 3 part 1: session notes, 17–18 Oct 2026

**Branch `alpha-lab-3`, cut from the tip of `audit-leftovers-2` (`d0b7432`). This is my own line, and it merges after `audit-leftovers-2` in the second stitched chain.** It therefore carries everything below it: `alpha-lab-2` (folded with Monday's chain last night), the crypto S-3 series, the meme ingest and the Batch 6 and Batch 5 ledgers.

Branch-only: pushed, not merged, not deployed, nothing run on the box. Every box step is printed below for Ari, and no unit was enabled, started or reconfigured.

This paste pulls forward from November three items: X-3.6 (tells as hypotheses), X-3.1 (engine 4, scheduled events) and X-3.2 (engine 5, crypto carry and basis). All three are built, and the rulings of 17 Oct are applied.

## Step 0: audit-leftovers-2's CI

| Run | Commit | Result |
|---|---|---|
| 39087884402 (Part 0) | `c0d5559` | passed, 104/104 |
| 39088326882 (Part 1) | `961106b` | passed, 104/104 |

Both are recorded in `docs/briefs/audit-leftovers-2-notes.md` (`d0b7432`). There was nothing to fix.

## The rulings of 17 Oct, as applied here

1. **The tier rule's reach is the same as-of only.** It was built that way. The architecture box now says so: "its reach is that one instant only, and since the store is append-only a lower tier never overwrites anything".
2. **Pass rules are pre-registered.**
   - `altdata/ledgers` prints a pre-registration line at the head of every edition.
   - `write_ledger` refuses a re-run whose pass rule differs from the first edition's. `registered_rule()` reads it from the earliest dated file.
   - All seven first editions register "none stated", that is, no gate.
   - The seven committed first editions are not edited, under their own "never edited" rule. The line appears from the next edition on (needs-you 9).
   - `validate_ledgers_b6` group K holds this: 41/0.
3. **ST-R4.20a is held until Thursday's 10-year attribution merge**, and is built the week after, not re-scoped. Nothing was built for it here.
4. **The four keys of 30b, 35b and 36b** arrive with Thursday's merge. Their refusal with a reason stands unchanged.
5. **On Ari's lists, nothing here:** the source-registry check before Thursday's merge, and the ^TNX/^TYX tolerance measurement in the week of the 19th.

The Alpha Lab order's rules hold throughout:
- The lab writes no candidate, packet, dial, band, tell or narrative. Group E of the new gate diffs those tables.
- It does not read the Monthly.
- It enters the sitting only as evidence.
- Every hypothesis is pre-registered by manifest before its first backtest.
- The base rates come first, and the engine second.
- Engine 5 waits for S-3. Engines 6 and 7 are not in this paste.

## What it builds on

From X-1 and X-2 as built:
- the ledger (`alpha.db`), the paper book and the point-in-time harness;
- the walk-forward with the embargo and the hold-out, and the cost model;
- the deflated-Sharpe gate, the allocator and the governor;
- the hypothesis register, with the v1 batch schema, its budgets and its duplicate screen;
- the workbench and the nightly harness (`max_runs_per_night`);
- the engine registry, as the only place an engine is named.

## Pre-registration by manifest (the thread through all three items)

- **The manifest is written first.** `alpha/manifest.py` writes it before the register takes the batch. The file is `<research_dir>/manifests/<batch_id>--<instant>.json`, holding the batch, its canonical sha256 and the instant. It goes through `alpha/files.py`, is gitignored, and is never overwritten.
- **The register uses the manifest's instant** as every hypothesis's `pre_registered_at`, and the batch row carries the manifest's sha256 and file name. Drive's created time and the proposer's manifest line already count as manifests.
- **The harness checks it.** `workbench.run` calls `manifest.check()` beside `refuse_if_unregistered()`, and refuses a hypothesis:
  - whose batch carries no manifest (the "fixture without one");
  - whose manifest is dated after the run;
  - whose manifest file no longer hashes to what was registered.
- **Three paths register this way:** the workbench's `new` (changed, so every path now has a manifest), the tells importer, and `python -m alpha.manifest register FILE` for the X-3 roster.

## X-3.6: tells as hypotheses

**Sources, all read and never written** (`alpha/tells.py`, `config/alpha_tells.yaml`):

| Source | What is read | Count (committed config) |
|---|---|---|
| Weekly | the Book B scanner's `tells:` (`config/book_b_scanner.yaml`): the style pairs IVW/IVE and IWF/IWD (SR-1), the ratios XLY/XLP and XLY/SPY (SR-5); the move screen's print | 4 (the move screen is not imported: no paper states its mechanism) |
| Doctrine | the trust matrix in section 5.3, parsed from the paper's table (ten rows), and Rule 9 ("Price reaction outranks the headline") | 11 |
| Setups | every setup in `config/setups.yaml` except `unclassified` | 15 |
| Forecasts | every probability-ledger source with at least one graded row (`brier` not null), read by SQL over the lab's read-only store connection; the module itself is never imported | as many as the box's ledger has graded *and* declared (below) |

**Each tell becomes one hypothesis:** "<tell> predicts at <h> sessions after costs?". It is source `tell`, channel `importer` (new, and the only channel that may carry `tell`), family `tell-<kind>`, status `needs_code`.
- **Mechanism:** a quote from the cited file and section. Each quote is checked word for word, ignoring whitespace and emphasis markers. All 31 quotes in the committed config verify.
- **Horizon:** the tell's own window:
  - SR-1's first test horizon, 126 sessions;
  - the scanner's 20-session ratio window;
  - the Doctrine's book horizons (A 126, B 30, C 5), with D 21 as a declared default (needs-you 2);
  - 5.3's half-lives (a month, 21; a session, 1);
  - for a forecast source, the median of horizon_date less emitted_at.
- **Instrument and exit rule:** from the source.
- **Recorded in `spec.tell`:** the tell's id, its definition's hash and the citation.
- **Nothing is tested.**

**Re-runs:**
- **Idempotent.** An unchanged tell writes nothing (no batch, no manifest, no row).
- **A changed tell** is a new registration with `supersedes`. The old one becomes status `refined`, with `superseded_by` set and the reason "superseded by HYP-x: the tell changed" (needs-you 7).
- **Refused, with the reason:** a quote not in its section, a tell no paper states, and a graded source with no declared paper.
- **Every hypothesis counts** one variant in its family (10.2 c).

**Where the counts print:**
- **The lab line:** "· tells n (Weekly a, Doctrine b, setups c, forecasts d)". It is appended to the live line and to "not yet live" alike, and adds nothing until the first import.
- **The Lab report:** section 7.

**Forecast sources declared:**
- `monthly_macro`: the Monthly Macro paper's preamble.
- `daily_close_outlook`, `weekly_stance`, `narrative_register`, `alt_asset:*` and `book_b*`: the Reporting System paper's 4.3, "Odds live in the ledger" (needs-you 3).

## X-3.1: engine 4, scheduled events

### The base rates come first

`python -m alpha.event_rates compute` writes them into `alpha.db`'s `event_base_rates` (`config/alpha_events.yaml`). Each row is one event, bucket kind, bucket and measure, with its n, its window (first and last event day) and its unit; a re-run on the same day replaces that day's rows. The monthly Lab report prints them as section 8.

**Events.**
- **CPI and payrolls** are taken from the events table's release and scheduled rows by entity (`fred.cpi`, `fred.nfp`). For the history before that table, they come from the first vintage of the series' ALFRED rows (`availability_kind observed`). A day within five days of an events-table day is deduplicated.
- **FOMC** is taken from the claims rows (kind `fomc`).

**Measures.** All three are on SPY's stored open and close, and the VIX:

| Measure | What it is |
|---|---|
| `first_session_drift_pct` | open to close of the first session after the print: the release day for 08:30, the next session for a 14:00 statement |
| `next_session_drift_pct` | the first session the nightly loop can enter after every input was knowable; what the engine trades |
| `vix_change_pts` | the VIX's close on the day less the close before; a crush is a fall |

**Buckets.**
- **Surprise:** sign and size, where large means at least 1 standard deviation of the previous 24 surprises. Under 8 prior surprises the size is "size unknown".
  - **CPI's surprise is the naive one** (`calc.surprise_vs_naive.cpi`, actual less the declared naive expectation). It is labelled naive everywhere and never called a consensus surprise.
  - **Payrolls and FOMC print "awaiting" with the reason.** `config/naive_expectations.yaml` declares nothing for `nfp`, and no FOMC surprise series is stored (needs-you 4 and 5).
- **Positioning:** the CFTC S&P 500 speculative net's two-year z, crowded at |z| ≥ 1.5.
- **Dealer regime:** read **by name** from 6b's keys: `exposure.net_gex[SPY]` gated on `exposure.net_to_gross ≥ 0.10`.
  - `exposure.net_to_gross` exists only on session A's 6b line, so on this line the bucket prints "awaiting".

**Earnings, 29 names.** The universe in `alpha_events.yaml` is held to `EARNINGS_SYMBOLS` by the gate.
- The 1- and 20-session drift, from the close of the session after the report day, by the sign of the **real** surprise (the yfinance analyst mean). Also the realised reaction.
- **Implied against realised: "awaiting".** No implied move is stored, because `daily_cascade/ahead.implied_move` reads the chain files at render.

**The hand figure** (gate group C), on four CPI releases (three from the events table, one from ALFRED):
- first-session drift: n 4, mean (+1.0 + 2.0 − 1.0 + 0.0)/4 = **+0.50%**, hit rate **50%**, window 2024-02-13 to 2024-05-15;
- VIX change: mean **−0.25 points**, a crush in 2 of 4;
- next-session drift: **+0.25%**;
- positive surprises: n 2 at +1.50%; negative: n 1 at −1.00%.

**Rows on the box's store** are its own. The base rates are computed there by the first command below, and print with their n. No real figure is in these notes.

### The engine second

`alpha/engines/events.py` implements four engines:

| Engine | Rule | State |
|---|---|---|
| `events_macro` | CPI and payrolls: SPY open to close in the next enterable session, long or short by the sign of the surprise bucket's mean in the fit window (at least 6 events a bucket, else no trade) | runs |
| `events_fomc` | the same after FOMC, bucketed by positioning | runs once the claims history is long enough; waits until then |
| `events_pead` | long a positive surprise, short a negative one, 20 sessions, nothing fitted | runs |
| `events_crush` | the crush | **data gap**: no tradable volatility instrument is stored (no option quotes per strike, no vol ETP) |

**Rows are point in time.**
- **Decision:** the first nightly loop (17:40 ET) after every input was knowable; the trade is in the next session.
- **Stale inputs are left out:** an event whose inputs were ingested more than five sessions after it, such as a backfill.
- **This shapes PEAD's sample.** yfinance's earnings history, ingested in September, is not knowable at the time, so its sample grows live.

**Costs:** an ETF or single-name round trip from the lab's cost model, at the engine's own capital.

**The harness runs each engine as X-1 built it:** the walk-forward with the embargo and the hold-out, then the deflated Sharpe. Promotion happens only through the nightly loop's promote step.

## X-3.2: engine 5, crypto carry and basis

`alpha/engines/carry.py` and `config/alpha_crypto_venues.yaml`.

**The switch** is S-3's funding regime, decided weekly at the last session of the ISO week as knowable then:
- **ON:** the trailing 7-day mean of `calc.funding_agg` is at least 10% annualised, and `calc.leverage_z` is below +2.
- **OFF:** the mean falls below 3%, or leverage_z reaches +2.
- **Between the two:** the state holds.

**The trade:**
- Long spot, short the perp on the venue paying the highest stored funding at entry.
- Equal notional, with a quarter of the sleeve held as the perp's margin.
- Funding is accrued daily from that venue's stored funding (annualised % / 365).

**The venues' fees are stored constants, listed and dated** (read 17 Oct 2026, entry-tier taker, the higher figure where two disagree):

| Leg | Taker | Source |
|---|---|---|
| Hyperliquid perps | 4.5 bp | the Hyperliquid docs' fee page |
| OKX perps | 5.0 bp | third-party summaries; **OKX's own page not reached** |
| Deribit perps | 5.0 bp | Deribit's support centre (its "upcoming" table says 3.5) |
| Spot leg (Coinbase Advanced, lowest tier) | 60 bp | 2026 reviews; **Coinbase's own table not reached** |

The perp class's spread and slippage are added on both legs at entry and exit. One motion costs about 87 bp at the fixture's size (needs-you 6).

**The basis is a listed gap.** No perp mark price is stored: `hl.*` and `fut.*` carry funding and open interest only. Both legs are therefore priced at the spot close, and the basis is assumed unchanged; every result and row says so.

**The history window.** The manifest states 92 weekly decisions with the switch computable: a year's fit (52) plus the weekly minimum sample (40). Below that, the coverage check prints "insufficient history: n of 92 …". In that case:
- nothing runs and nothing is counted;
- the hypothesis stays `registered`, so the nightly harness looks again;
- the z-scores mature in December, so this is what the box will print until well after that.

**The paper book's crypto rows.** These are `carry_book`, with the venue, the spot and perp leg sizes, the entry and exit costs and the net P&L, and `carry_accruals`, the funding per day.
- They are written only by the nightly loop's new carry step, for a live carry engine, which means after the gate.
- `book.cum_pnl` adds them to the engine's P&L, so the governor sees them.
- They are paper only.

## The engines' manifests (the roster)

`alpha/research/roster-2026-10-17-x3.yaml` holds batch `2026-10-17-roster-tranche-3`: source operator, channel workbench, five hypotheses. **It is not yet pre-registered:** registration happens on the box, by manifest.

| Local id | Engine | Horizon | Sample needed |
|---|---|---|---|
| E-4a | events_macro | 1 session | 100 |
| E-4b | events_fomc | 1 session | 100 |
| E-4c | events_pead | 20 sessions | 100 |
| E-4d | events_crush | 1 session (data gap) | 100 |
| E-5 | crypto_carry | weekly | 40 (after the 92-week window) |

On the fixture store (gate group D):
- E-4a ran and failed the standard gate;
- E-4c and E-5 ran and passed;
- E-4d is a data gap, and E-4b waited on its short FOMC history.

These are synthetic results, which only show the path works end to end. Nothing was promoted.

## Item 4: registry, catalogue and units

**The lab stores no observation-store key**, so it adds nothing to `metrics_registry.yaml` or the catalogue, whose command table covers `altdata/` only. Its new rows are in `alpha.db`:
- **`event_base_rates`**, which carries its own `unit` column (pct, vix_pts);
- **`carry_book` and `carry_accruals`**, in lab dollars and annualised % funding.

All three are documented in `alpha/ledger.py`'s docstring and `docs/alpha-lab.md` section 9.

**Budgets:** the lab line gains one clause, and the Lab report gains sections 7, 8 and 9.

**The CLAUDE.md count line is recounted** to ninety-six code gates (ninety-three Python, three shell) and seven data gates. `validate_audit_3a` holds it: 86/0.

## Gates

| Gate | Result (local, one at a time) |
|---|---|
| `tools/validate_alpha_lab_3.py` (new; Makefile after validate_alpha_proposer) | **48/0**: A the manifest (7), B the tells (14), C the hand figure (8), D the engines end to end (14), E nothing else written (5) |
| `tools/validate_ledgers_b6.py` (group K added) | **41/0** |
| `tools/validate_audit_3a.py` (count line, the architecture box) | **86/0** |

**Group E, nothing else written.** After the importer, the base rates, the roster and a full nightly run (no step failing):
- the store's sha256 is unchanged;
- the narratives, candidate, packet, band, tell, probability and events tables, and the dials (`market_state` rows), all diff empty;
- no SQL in `alpha/` writes any of them.

**Left to CI,** per the memory rule: `validate_alpha` (the workbench now writes a manifest, and the harness checks it), `validate_alpha_no_orders` (five new modules, none importing anything forbidden by my reading) and every other gate.

## Box commands for Ari

Run these inside a window, after this branch merges (Thursday's merge, in the second chain). Each is a box write to `alpha.db` and the research directory only, run by Ari:

```bash
cd ~/chester-reports
# 1. The first import of the tells (a dry run first prints what it would register)
.venv/bin/python -m alpha.tells import --dry-run
.venv/bin/python -m alpha.tells import
.venv/bin/python -m alpha.tells list
# 2. The first base-rate computation, and its rows
.venv/bin/python -m alpha.event_rates compute
.venv/bin/python -m alpha.event_rates show
# 3. The X-3 engines' roster, pre-registered by manifest (the nightly harness runs it)
.venv/bin/python -m alpha.manifest register alpha/research/roster-2026-10-17-x3.yaml
```

**No unit changes.** The nightly loop's carry step arrives with the code. No timer or unit file changed, so nothing needs enabling or restarting.

**What the lab line will print on Sunday 25 Oct.** This assumes the lab's Weekly hook is merged (alpha-lab-1 and alpha-lab-2) and command 1 has run. No engine will be live, because nothing has passed and been promoted, so:

> Alpha Lab: not yet live · tells *N* (Weekly 4, Doctrine 11, setups 15, forecasts *k*)

- *k* is the number of the box's graded forecast sources with a declared paper, and *N* = 30 + *k*.
- Without command 1, the line is unchanged: "Alpha Lab: not yet live".

## Files shared with the open branches

- **Session A's 6b keys, read by name only:**
  - `exposure.net_gex` (instrument SPY) is already registered.
  - `exposure.net_to_gross` is on `6b-dealer-1/2/3`. Until it merges, the dealer buckets print "awaiting". No file of session A's is touched.
- **This branch alone (`d0b7432..`)** shares only `CLAUDE.md` and `Makefile` with `gtm-core-2` and `6b-dealer-1/2/3`. These are one count line, one gate line and the alpha paragraphs, so a stitch resolves by taking both.
- **Inherited from `audit-leftovers-2`**, and already listed in its notes: `altdata/derived.py`, `altdata/feeds.py`, `altdata/sources/yfinance_source.py`, `scripts/run_eod_cron.sh` and `tools/validate_audit_3a.py`.

## What part 2 takes

- **X-3.5, the grammar search** (`alpha/search.py`): enumerated candidates counted in `variant_counts`, and survivors pre-registered by the search's own manifest. `alpha/manifest.py` is ready for that.
- **X-3.7, the quarterly meta-loop:** the counterfactual of each loop event, the loop's net contribution, and the Quarterly's lab page.
- **Engine 6, extremes reversion:** waits for the move screen's base rates to reach n ≥ 30 a bucket.
- **Engine 7, intraday dealer regimes:** waits for 6b's intraday captures and the state vector.

## Needs you

1. **What a "Doctrine tell" is.** I read it as the section 5.3 trust matrix's ten signal families plus Rule 9's price-reaction tell (11). keep / name others
2. **Book D's horizon.** The Doctrine says the catalyst sets it; the import declares 21 sessions. keep / rule
3. **The forecast sources' mechanism.** `weekly_stance`, `narrative_register`, `daily_close_outlook`, `alt_asset:*` and `book_b*` cite the Reporting System paper's "Odds live in the ledger", which states the rule rather than a mechanism. A graded source with no declared paper is refused. keep / name each source's paper
4. **The payroll surprise.** No naive expectation is declared for `nfp`, so payroll buckets by surprise print "awaiting". Add one to `config/naive_expectations.yaml`? (That makes a new store key.) yes / no
5. **The FOMC surprise and history.** No surprise series is stored, and FOMC dates exist only from the claims rows, so `events_fomc` waits. Build a futures-implied surprise from the fed funds rows, and/or declare past FOMC dates? choose
6. **The fees.** OKX's and Coinbase's figures are not verified at the primary source. The spot leg at Coinbase's lowest tier (60 bp) makes one motion cost about 87 bp. Verify, or name another spot venue? verify / choose
7. **"Superseded" is status `refined` with `superseded_by` set.** I did not add a new status: that needs a rebuild of the hypotheses table's CHECK constraint on the box's `alpha.db`. keep / add a status
8. **The macro engine trades the next session,** not the release day. An 08:30 print cannot be entered by a 17:40 loop before the open, so the release-day drift is a base rate only. accept / rule
9. **Ruling 2 and the seven first editions.** They are not edited, under their own "never edited" rule. The pre-registration line and the refusal apply from the next edition. ok / add an addendum file
10. **The PEAD sample.** yfinance's earnings history, ingested after the fact, is not knowable in time and is left out, so the sample grows live. noted

## CI

Read once each on 18 Oct 2026 (lenses-group-b's step 0):

- Run 39097051684 on `395483f` (the build): **failed**, 103 of 105 jobs passed. The two failures were `validate_alpha` (254 passed, 3 failed) and the `gates-passed` roll-up that follows from it.
- Run 39097161999 on `71ae80d` (these notes): **failed**, the same: 103/105, `validate_alpha` 254/3.
- **The cause was mine.** Three checks in `validate_alpha` pinned the engine registry to Tranche 2's four engines: the registry's list, `load_all()`'s length, and the nightly loop's candidate map. This branch adds five more to `config/alpha_engines.yaml`, so all three checks failed. The checks now hold Tranche 2's four first, then Tranche 3's five, all of them candidates that trade nothing (`ENGINE_IDS`). Locally that is 257 passed, 0 failed. The fix is the commit after these notes. Its run is read in lenses-group-b's notes, which carry the result forward.
