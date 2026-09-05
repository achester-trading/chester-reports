# TODO

- Decide narrative thinking/effort config after first Opus 5 monthly render.

## Probe verdict, 4 Sep 2026

FlashAlpha key verified live on the `basic` plan (`/v1/account`), not from the
published tier table.

- **Basic serves**: `/v1/exposure/levels/{sym}` (aggregate levels only) and
  `/v1/options/{sym}` (expiry-keyed strike grid, no OI or exposure values).
  Plus `/v1/account` and `/health`.
- **Growth-gated**: per-strike exposure (`/v1/exposure/gex`), `/exposure/summary`,
  `/exposure/zero-dte`, `/flow/gex`, `/flow/dealer-risk`.
- **Alpha-gated**: `/flow/oi`, `/flow/signals`.
- **Not in the published API at all**: any Indic-module or liquidation endpoint.
- **Rate limit**: live `X-RateLimit-Limit: 250`/day, which settles the docs
  (100) vs SDK page (250) conflict in favour of 250.
- **OI staleness**: unmeasurable on Basic — no OI field is exposed on any
  reachable endpoint. A 60s intraday diff showed the strike grid frozen and
  `gamma_flip` moving only while spot also moved, which is consistent with
  recompute over a settled OI base rather than live OI.

Net: per-strike exposure, OI, and customer/dealer polarity all require Growth
or Alpha. **Upgrade decision pending price.** Until then FlashAlpha Basic is
the independent cross-check on our own computation, not a data source.

## Session −1 logger vs architecture v3 — reconciliation gaps (4 Sep)

Built tonight: chain fetch (13 symbols), self-computed per-strike GEX, pin log,
EOD runner, FlashAlpha cross-check. Gaps against Session −1, Part 22–26 and the
white-paper §2.8 disposition. **Not built tonight — listed only.**

Pin log / schema
- [x] **DONE 4 Sep.** `expiry_type` + `max_pain_expiry_type` added. The peak-GEX
      reference strike is classified by the expiry bucket contributing most |GEX|
      *at that strike*; max pain is classified by the bucket holding most OI
      there, since max pain is an OI construct, not a gamma one.
- [x] **DONE 4 Sep.** `shares_per_1pct` is now the stored primary and
      `dollar_gamma_per_1pct` is derived from it (shares x spot), so the two
      cannot drift. Raw notional kept as `net_gex`.
- [ ] Re-running a past date rewrites its row at the *current* tolerance. Doc:
      tolerance "declared in advance and never revised after the fact." Rows do
      carry their own `tolerance_bps`, so make a backfill refuse to change it.
- [ ] Label the pin read a **conditioner** until effective-n is meaningful.
      Nothing in the output says the sample is too small to act on yet.

Data-quality gates (none of these exist yet)
- [x] **DONE 5 Sep.** Liquidity floor: total OI/volume against thresholds
      declared in config. Median relative bid/ask spread is also reported (the
      doc's preferred tightness measure, SPY 0.016 vs ASTS 0.143 — clearly
      discriminating), so the gate can move onto spread once calibrated.
- [x] **DONE 5 Sep.** IV dispersion implemented as a gate. Threshold is
      PROVISIONAL — a normalised roughness figure has no natural scale.
      Observed 0.033–0.239 across 13 symbols against a 0.35 ceiling; calibrate
      once a real sample exists.
- [x] **DONE 5 Sep.** OI Herfindahl + effective strike count (SPY 109 effective
      strikes vs ASTS 30 — concentration varies ~4x across the universe).
- [x] **DONE 5 Sep.** OI-weighted DTE (SPY 103d shortest, TSLA 184d longest).

Cross-check
- [ ] No **declared divergence threshold or alert**. Doc: "Log the recompute
      spread; alert past a declared threshold." We log the spread only.
- [ ] Doc's intended check (recompute from FlashAlpha's own per-strike payload to
      catch a silent methodology change) is **impossible at Basic** — no
      per-strike data. Ours compares our yfinance-derived profile against their
      aggregate instead: same purpose, weaker evidence. Revisit if Growth lands.

Intraday
- [ ] No intraday sampling (09:30 / 11:00 / 14:00 / 15:30). Note when building:
      the doc's settled-OI caveat applies to **our** yfinance chains too — OI is
      settled, so intraday snapshots measure *spot traversing a static profile*,
      not positioning evolution. Must be labelled as such in the output.
- [ ] **The intraday cadence now OWNS 0DTE greeks** (ruling, 5 Sep). A settled
      capture computes none; the 09:45 fetch is where those contracts have
      hours of life, real two-sided markets and a solver coverage rate that can
      clear the gate, so that is where 0DTE GEX is computed and where the pin
      log's 0DTE segmentation gets real data. `exposure_compute.is_settled_capture`
      already switches on capture time, so an intraday chain gets full 0DTE
      greeks with no further change. Two things to build alongside it:
      the gate's `0DTE GEX profile` check currently reports N/A at a settled
      capture and is waiting for an intraday one to run against for real; and
      an intraday 15:30 sample must consult `is_early_close()`, since on those
      days the market is already shut by then.
- [ ] **PREREQUISITE, found by the MIN_T flag on its first run: intraday 0DTE
      greeks need a FRACTIONAL time to expiry, and the code does not have one
      yet.** `dte` is an integer day count, so a same-day contract is `dte=0`
      whatever the clock says, `t_years = 0/365 = 0`, and MIN_T floors it to one
      hour. At 09:45 roughly 6.25 hours remain — about 6x MIN_T — so the floor
      would understate T sixfold and overstate gamma by ~sqrt(6) ~ 2.4x.
      Relabelling Friday's chain as a 09:45 capture reproduces this exactly:
      the 0DTE bucket comes back with `floored_share_of_abs_gex = 1.0` and
      `min_t_load_bearing = True`, every row on the floor.
      So moving 0DTE greeks to the intraday cadence does NOT by itself make
      them meaningful — the cadence must compute time to expiry from the
      capture instant to the session close (respecting early closes, where the
      close is 13:00 ET) rather than from a day count. The flag is doing its
      job: MIN_T is load-bearing here, and it says so instead of quietly
      returning a number.

Point-in-time and provenance (Part 26.2)
- [ ] No `available_at` on any record (26.2 #2, point-in-time correctness).
- [ ] No run_id / code git hash / data-manifest hash — a run is not replayable
      from its own record (26.2 #3, immutable Decision Packet).
- [ ] No Security Master identity layer (26.2 #6); bare tickers only.

Durability and coverage
- [ ] **Replace the OneDrive backup with VPS-side storage when cron moves there.**
      `run_eod.py` stage 4 zips `data/chains/<date>/` and copies it to
      `config.BACKUP_DIR` (OneDrive today, env-overridable via
      `CHESTER_BACKUP_DIR`). That is a stopgap for a laptop, not a runtime
      answer: Part 25 rules the VPS primary, so the backup target should become
      box-side storage plus an off-box copy.
- [ ] Raw chains live only on this Windows box, gitignored. Part 25 rules the VPS
      the primary runtime with outputs on the box, so gitignoring is right — but
      the data is the one asset that cannot be recovered, and it currently has no
      backup and no VPS home. Migrate + back up before the sample has real value.
- [ ] SPX absent (yfinance has no index options). Blocks the doc's Session −1
      universe of SPX/SPY/QQQ/IWM. Pending the Part B vendor decision.

## Put-wall definition resolved (5 Sep)

FlashAlpha's `put_wall` is the extreme-GEX strike **restricted to OTM**, not the
extreme across all strikes. Verified against both symbols: SPY 760 = 760, QQQ
700 = 700, zero divergence, where the all-strikes version was 19 points off on
QQQ because the ATM 719 strike carries the largest negative GEX (-0.37bn)
without being a wall in any tradeable sense.

Four definitions now computed side by side rather than collapsed:
`put_wall` (net GEX, all strikes), `put_wall_gamma` (put-only gamma, sits ATM),
`put_wall_oi` (largest OTM put OI shelf), and `put_wall_otm` (matches the
vendor). `call_wall_otm` added for symmetry — it already agreed, but only
because no ATM strike happened to dominate the call side.

- [ ] Decide which put-wall definition the pin log should score against. It
      currently uses `put_wall` (net GEX, all strikes); `put_wall_otm` is the
      tradeable one and the one the vendor agrees with.

## Trading calendar (added 5 Sep 2026)

- [ ] **Extend `altdata/session.py:NYSE_HOLIDAYS` past 2027 during Q4 2027.**
      The table covers 2026-2027 only. Past its last year `is_trading_session`
      fails open -- unknown weekdays run -- so the failure is a wasted holiday
      fetch, not a lost session, but it is still a failure. Source:
      https://www.nyse.com/markets/hours-calendars.
- [ ] Early closes are tabulated and treated as sessions. If intraday sampling
      ever lands, its 15:30 ET sample must consult `is_early_close()` -- the
      market is already shut by then on those days.

## Four-Greek extension — open items (5 Sep 2026)

Landed: `gex_compute.py` -> `exposure_compute.py` (import shim kept), per-strike
GEX/DEX/VEX/CHEX Black-Scholes from stored chains and IV, all four bucketed
0DTE/weekly/monthly/quarterly, dated expiration-release ladder in
`data/expiration_release.csv`, `mechanism_group=dealer_chain_derived` on every
row, pin log 44 -> 66 columns append-only. Backfilled from 2026-09-04.

- [x] **DONE 5 Sep.** DTE=0 excluded from the solver-vs-yfinance IV comparison
      and from the whole-book profile checks, declared in
      `config.IV_SOLVER_EXCLUDE_DTE0` with the evidence; the solver still
      solves 0DTE in production. A substitute 0DTE check compares the bucket's
      GEX *profile* under both IV sources. Gate is now three-valued
      (PASS/FAIL/INCONCLUSIVE) so a check that cannot see the book reports
      neither green nor red.
- [x] **DIAGNOSED 5 Sep: the gamma check fails on an ill-conditioned
      DENOMINATOR, not on solver error.** No threshold has been changed. The
      recommended fix is a change of denominator, which is a statement about
      what the metric measures, not a relaxation of how much error it tolerates.

      *The hypothesis was half right.* The IV tail IS concentrated in twinned
      rows -- p90 |dIV| is 0.024-0.071 on directly-measured rows against
      0.159-0.355 on twinned ones, 5-8x higher on every symbol. But the gamma
      divergence does NOT live there. Split ex-0DTE into strata:

          SPY   measured  5.1%   twinned  5.2%   COMBINED  27.6%
          QQQ   measured 11.8%   twinned  9.5%   COMBINED  82.7%
          TSLA  measured 26.4%   twinned 19.4%   COMBINED 137.6%

      Each stratum is tighter than their combination, which is impossible for
      an ordinary error budget and is the tell.

      *Cause.* Net dollar gamma is a signed residual of two large offsetting
      halves, and the strata split the book along exactly the axis that
      cancels: measured rows are the OTM wing (dealers short puts, so it nets
      NEGATIVE) and twinned rows are their ITM twins (nets POSITIVE). For SPY,
      -4.67bn + 3.21bn = -1.45bn. The errors ADD (236M + 166M = 402M) while the
      nets CANCEL, so the same absolute error becomes a far larger percentage.
      A percent-of-net tolerance on a quantity that nearly cancels is unstable
      by construction.

      *Evidence, same error measured against gross |GEX| instead of net, all 13
      symbols, ex-0DTE, co-solved rows only:*

          worst on a NET denominator   : 137.6%  (TSLA)
          worst on a GROSS denominator :   9.53% (AAPL)

      **Every symbol passes the existing 10% bar on a gross denominator.**
      Full set, err/NET vs err/GROSS: AAPL 12.6/9.53, AMZN 11.9/7.13,
      ASTS 18.4/7.21, COIN 0.9/0.54, GOOGL 29.8/7.10, IWM 2.6/1.23,
      META 3.5/2.66, MSFT 5.9/5.22, MSTR 0.9/0.72, NVDA 4.5/3.52,
      QQQ 82.7/4.34, SPY 27.6/2.04, TSLA 137.6/8.92.

      *This also explains the QQQ clue, and it was not liquidity.* QQQ's net
      gamma is -661M against 12.6bn gross -- the net is 5% of the book, the
      smallest ratio in the universe -- so QQQ has the smallest denominator
      relative to its own size. On a gross denominator QQQ is 4.34%, better
      than average.

- [x] **DONE 5 Sep. Gamma check now divides by gross |GEX| at the unchanged
      10% bar** (`config.IV_SOLVER_GAMMA_DENOMINATOR = "gross"`). SPY reads
      1.592% of gross where it read 23.086% of net. The gate PASSES.
      Per the caveat, the absolute net uncertainty is printed beside it and is
      not hidden by the friendlier ratio -- SPY's line reads
      `[net residual 23.086%, absolute $315,983,913]`, and the profile section
      spells out "net dealer gamma could be out by $315,983,913".
- [ ] Keep the twinning finding on the books regardless of the denominator:
      43-49% of every comparison is propagated ITM vol carrying a 5-8x wider
      tail (p90 0.159-0.355 vs 0.024-0.071). That deserves a per-row quality
      flag so a consumer can weight by how well each strike's vol is known.
      Not urgent now that the gate is sound; still true.

- [x] **RULED AND APPLIED 5 Sep. The pin artifact is gone.** The 7/13 rate was
      the MIN_T floor planting peak-GEX at the money; under the settlement rule
      the settled peak is the ex-0DTE peak and Friday rewrites to **0/13** on
      peak, call_wall_otm and put_wall_otm alike. A one-day sample where
      nothing pinned is a real result; the 54% was not.
      Pin scoring now keys on the ex-0DTE peak PLUS the two OTM walls, which
      never had this problem -- a wall is the extreme GEX strike restricted to
      out-of-the-money, so an at-the-money artifact could not become one however
      large it grew. That makes them the control on the peak, not just two more
      levels.

- [x] **RESOLVED BY RULING 5 Sep.** 0DTE IV is unsolvable at the close on every
      symbol (coverage 0.0-2.4%, 60-70% rejected `wide_spread`) and the ruling
      accepts that rather than working around it: at a settled capture those
      contracts are expired or minutes from it, so their gamma is an artifact
      of quoting corpses, not a forward-looking exposure. The settled profile
      excludes DTE=0 from every exposure aggregate by declared semantic rule
      (`config.SETTLED_0DTE_RULE`); the bucket still reports OI structure with
      greeks marked `not_meaningful_at_settlement`. OI constructs -- max pain,
      the quality gates -- are untouched, because the distortion was never in
      the OI.

- [ ] **The two snapshot qualities pull in opposite directions.** The 16:10
      capture is right for OI and 0DTE completeness; the 22:44 capture had
      cleaner quotes (gate read -4.55% there, ex-0DTE 23.1% here). Worth
      measuring whether a late-evening capture should feed the IV solver while
      the close capture feeds OI.
- [x] **SUPERSEDED 5 Sep for settled captures.** NVDA's +20.4M sh/day 0DTE
      charm no longer appears: a settled profile computes no 0DTE greeks at
      all. The finding stands for the INTRADAY cadence, where charm is real and
      `chex_floored_rows` remains the counter to check.

- [ ] **DEX direction is uninformative under `dealers-hand-v1`** and will stay
      that way. Long calls carry positive delta and SHORT puts also carry
      positive delta, so net DEX is positive for every symbol, bucket and
      expiry — 269 of 269 rows on the first backfill, with no negative possible
      in principle. Magnitude, dating and day-over-day change are the signal;
      `unwind_direction` only becomes a real variable if Alpha-tier flow
      polarity ever replaces the assumed +1/-1.

### Selection and semantic boundaries in the committed history

Two changes now revise numbers that were already committed. Rows written either
side of each are not comparable, and nothing on an old row says so, which is
why both are recorded here rather than only in a commit message.

**Boundary 1 -- snapshot selection (earlier on 5 Sep).** `newest_chains`
selected the day's chain by file **mtime**. For 2026-09-04 that picked the
22:44 ET capture, taken hours after the close, by which time all 425 0DTE
contracts had expired off the chain — so the whole 0DTE bucket was silently
absent and nothing downstream could tell, because a missing bucket and an empty
one look identical. Selection now ranks by the `fetched_at` the rows carry,
nearest `config.EOD_SNAPSHOT_TARGET_ET` (16:10, matching the timer). Moved
every 2026-09-04 number: SPY $gamma/1% -988M -> -1,172M, NVDA 1.67bn -> 4.15bn,
QQQ -339M -> -3.26bn.

**Boundary 2 -- settlement semantics (this ruling).** The settled profile now
excludes DTE=0 from every exposure aggregate. Moved them again, in the other
direction: SPY -1,172M -> **-1,369M**, NVDA 4.15bn -> **1.68bn**, QQQ -3.26bn ->
**-542M**. NVDA and QQQ move most because floored rows carried 54.1% and 17.9%
of their |GEX|; SPY moves least because it carried 1.0%.

Rows written under the new rule carry `capture`, `settled_0dte_rule`,
`exposure_rows` and `settled_0dte_excluded_rows` so the boundary is legible
from the data. **Rows predating it carry none of those columns, and an empty
`capture` is the marker for "computed under the old rule".**

*Rewritten under the ruling:* 2026-09-04 (Friday), all 13 symbols. There are no
Thursday rows to rewrite — the only sessions on disk are 2026-09-04 (48 chain
files) and the 2026-09-05 Saturday Massive-only capture, so Friday is the
entire affected history.

## SPX + SPCX ingestion (5 Sep 2026) — landed, Greeks deferred

`altdata/sources/massive_chain.py` captures both into the shared chain schema.
Verified live: SPX 28,024 rows / 20,909 with OI / 55 expiries / 113 pages;
SPCX 3,182 rows / 2,503 with OI / 18 expiries. Tuesday captures **15 symbols:
13 with full Greeks, 2 ingestion-pending-solver.**

Every row carries `greeks_status=pending_solver_gate`, and `exposure_compute`
refuses any chain carrying it — the deferral is enforced from the data, so it
cannot be lost by someone passing a wider `--symbols`.

- [ ] **Compute SPX/SPCX Greeks once the solver gate goes green.** Nothing else
      blocks them: chains are being stored from today, and the spot problem is
      solved — put-call parity recovers the forward from the option prices, so
      the `I:SPX` 403 does not bite. Sanity check on the first capture: parity
      spot **7710.94** against SPY's 770.24 close x10 = 7702, 0.12% apart.
- [ ] Backfill is impossible for these two and that is now permanent, not
      pending: Massive serves OI from the live snapshot only. Whatever OI
      history SPX ends up with starts 2026-09-05.
- [ ] `MASSIVE_MAX_PAGES` is 400 (100k contracts). SPX used 113. Revisit if a
      capture ever reports `truncated`.

### Two directory hazards found and fixed while wiring this

Both were latent before today and both silently produced wrong output rather
than an error.

1. `pin_log.load_computed` scored profiles by the directory it read but keyed
   the ROW on the profile's own `session_date`. Pre-fix profiles sitting in a
   UTC-named directory therefore wrote rows for a different day, replacing good
   ones — this clobbered the four-Greek backfill mid-session before it was
   caught. Now a profile whose session disagrees with its directory is skipped,
   including one whose `session_date` is null and would otherwise fall back to
   deriving the date from `fetched_at`.
2. Both `newest_chains` and `load_computed` took "the latest directory" as
   "the latest data". With two vendors writing on different days, a
   Massive-only Saturday capture made the latest directory one the yfinance
   symbols never appear in, and the run reported no chains while a complete set
   sat one directory back. Both now walk back to the newest directory that
   actually holds something for the symbols asked for.

## Registries (5 Sep 2026) — minimal-but-real first cut

`metrics_registry.yaml` (44 metrics + 138 bulk members across 2 blocks),
`source_registry.yaml` (5 sources), and one CI gate, `tools/check_registry.py`,
wired to `.github/workflows/registry-check.yml` on every push and PR.

**Every metric is `trigger_eligible: false`.** That is the honest state, not a
placeholder: no recommendation path exists and the pin-log sample is one
session. The gate refuses to let anything become trigger-eligible without a
source, mechanism group, native horizon, units and a written rationale.

- [ ] **Refine FRED mechanism groups below pillar level.** Nine pillars is the
      right first cut — liquidity and labour can confirm each other, two labour
      series cannot — but within a pillar some series still move together
      (initial claims and continuing claims are not two votes). Split when a
      confluence rule actually reads them.
- [ ] **`exposure_compute` stamps one `mechanism_group` per profile
      (`dealer_chain_derived`), but the registry distinguishes
      `dealer_chain_derived` from `dealer_chain_oi`.** Max pain and the OI
      shelves are OI constructs, not gamma ones, and architecture 26.9 wants
      settled OI kept separate. The registry is ahead of the code here on
      purpose; align the code's stamp when something consumes the distinction.
- [ ] Source `precedence` records one rule (massive A1 beats yfinance C on a
      shared chain) that is **not yet exercised** — the two universes are
      disjoint today. It becomes live the first time both serve one symbol.
- [ ] The registry has no notion of a metric's *quality* weight. The solver's
      twinned-vol finding (43-49% of rows, 5-8x wider tail) is the first case
      that would want one.

## Session 5 core (5 Sep 2026) — point-in-time store, register, restriction

`altdata/observations.py` (SQLite, three clocks, one as-of join),
`register/` (decisions, immutable packets, the Brookfield rule),
`config/tracked_entities.yaml` (29 restricted roots + name matching),
`tools/validate_register.py` (33 checks, wired into CI alongside the registry
gate). CSV writers keep running — `altdata/store.py` now dual-writes.
Migrated 20,372 observations across 59 keys; re-running writes 0.

- [ ] **Migrated `available_at` is an ESTIMATE and is tagged as one.** The CSVs
      carry `as_of` (pull time), an upper bound on availability, not the release
      time — for a series revised between release and pull it OVERSTATES how
      early we knew, the direction that leaks. Migrated rows carry
      `source='fred:csv_migrated'` so they stay distinguishable. Visible in real
      data: every migrated row has `available_at = 2026-05-30`, so an as-of
      query before that date returns nothing. **Backfill true release times
      from FRED's ALFRED vintage API to fix this properly.**
- [ ] Only `altdata/store.py` dual-writes so far. The options pipeline
      (exposure profiles, pin log) still writes CSV only and is not in the
      point-in-time store. Decide whether exposure metrics belong there or stay
      file-based — they are per-session snapshots, not revised series, so the
      case is weaker than for FRED.
- [ ] The register has no writer yet. Nothing produces decisions, which is why
      every metric is still `trigger_eligible: false`. The register exists so
      that the first thing that does produce one cannot bypass it.
- [ ] `code_dirty` was 1 on the first real packet, because the tree had
      uncommitted work. That is honest and correct, but a packet built during
      an actual decision should be built from a clean tree; consider refusing
      to attach a packet with `code_dirty=1` once decisions are real.

### Brookfield restriction — rulings, 5 Sep 2026

Tier 4 (Oaktree + Brookfield-branded funds) IN — Oaktree shares Brookfield as
controlling parent, so it is information adjacency, not brand similarity.
`RA`/`INF` by entity NAME only, never bare ticker — both are generic enough
that a symbol block would eventually fire on an unrelated issuer, and a rule
that misfires invisibly is worse than one that asks. `EAF`/`TSU` reviewed and
deliberately excluded, recorded with the reason so it is not re-argued.

- [ ] **The list is from the corporate structure, not a live filing.** Verify
      against current SEC/SEDAR filings before treating it as complete.
- [ ] Ticker-keyed blocking is the Part 26.2 #6 Security Master gap, and
      Brookfield is close to the worst case: `BAM` meant the entity now called
      `BN` before the 2022 spin-off. `valid_from` is recorded on every row for a
      future identity layer. The FORWARD restriction is unaffected — only new
      decisions are blocked, and every root is Brookfield's today.

## IBKR Gate 1 — Portfolio Truth (5 Sep 2026)

`ib_insync` -> `ib_async` swapped before any Gate 1 code existed, which was the
point: it appeared **only in documentation** (architecture Part 26.11 and the
systematic-book whitepaper), never in requirements.txt and never imported, so
nothing was ever written against the archived library. `ib_async>=1.0` is now a
declared dependency.

`altdata/sources/ibkr_portfolio.py` + `scripts/sync_ibkr.sh` +
`tools/validate_ibkr_portfolio.py` (34 checks, in CI). Reads NAV, cash, buying
power, margin, cushion and per-position qty/cost/value/PnL into the observation
store as `source=ibkr_paper`, 13 registered metrics, all
`mechanism_group=portfolio_truth`, all `trigger_eligible: false`.

- [ ] **LIVE TEST PENDING ON THE VPS.** Everything so far is against fakes. Once
      Gateway is up: `python -m altdata.sources.ibkr_portfolio --dry-run`, then
      without `--dry-run`, then wire `scripts/sync_ibkr.sh` to a systemd timer
      following the `deploy/systemd/` pattern. The connection-refused path is
      the one thing already proven against reality (exit 3 on a closed port).
- [ ] Gate 1's pass condition is a RECONCILIATION -- does the register's
      mark-to-market agree with the broker's? That needs the register to hold
      decisions, which it does not yet. Portfolio Truth is the input side only.
- [ ] The other three read-only services of 26.11 are unbuilt: Portfolio Risk
      (actual Greeks, factor/currency exposure), Expression Intelligence
      (bid/ask, IV, What-If commission and margin), Execution Evaluation
      (fills, arrival price, slippage).
- [ ] `ACCOUNT_TAGS` covers nine summary tags. IBKR serves many more; add on
      demand rather than pulling everything, since most of it is noise.

### A real bug the IBKR work exposed in the point-in-time store

The as-of join compares `available_at` LEXICOGRAPHICALLY so SQLite can use an
index, and that only matches chronological order when every value has the same
width. It does not: `'...T12:34:56.789012+00:00'` sorts AFTER
`'...T12:34:56+00:00'` because `.` (0x2E) > `+` (0x2B). FRED writes seconds and
broker snapshots write microseconds, so **every broker row was invisible to any
second-resolution cutoff** -- it looked like it had not happened yet.

Fixed by canonicalising every instant to fixed-width microsecond UTC on write
and on query, with a regression test in `tools/validate_register.py`. The store
was wiped and re-migrated (20,372 rows, regenerable from the CSVs). Worth
remembering the shape of this: it only surfaced because a second source with a
different timestamp precision arrived.

## IB Gateway runtime units (5 Sep 2026) — written, NOT enabled

`deploy/systemd/ibgateway.service`, `ibgateway-watchdog.{service,timer}`,
`ibgateway-restart.{service,timer}`, `scripts/ibgateway_watchdog.sh`,
`tools/validate_ibgateway_watchdog.sh` (25 checks, in CI). The VPS drafts were
awaiting repo adoption; these supersede them and are the authoritative version.

**The design constraint is a VPS finding: on bad credentials IBC sits at 294MB,
`active (running)`, with no port, forever.** The process never exits, so
`Restart=on-failure` never fires and `systemctl status` is a green light over a
dead service. systemd cannot distinguish a Gateway waiting on an unanswered
login dialog from one serving an API. Hence the watchdog is the health
authority and `~/.chester/ibgateway_health` is the thing to read.

Health has exactly one definition: the watchdog's probe IS the portfolio sync's
connection path (`--dry-run`), and its verdict is that command's exit code, so
sync and watchdog cannot drift apart on what "healthy" means.

- [ ] **NOTHING IS ENABLED AND NOTHING AUTO-STARTS.** Every `[Install]` is
      commented out, so `systemctl --user enable` fails until a human
      uncomments it. The gate: one witnessed clean supervised start — a
      listening 4002 **and** `state=ok` in the health file. A listening port
      alone does not clear it, because `signed_out` also listens.
      README.md section 4 has the procedure.
- [ ] Daily restart is 01:00 ET, deliberately AFTER IBKR's 23:45–00:45 reset
      window rather than before it: restarting at 22:00 would leave the Gateway
      up through the reset, which is how a stale session is acquired. Pinned to
      `America/New_York` so it cannot drift into the window at a DST boundary.
- [ ] The restart budget stops at 3/day on purpose. The hang is caused by bad
      credentials and no restart fixes those; an uncapped watchdog would loop
      forever, looking like action while the real fault stayed unreported. Past
      the cap it exits 2 and names `config.ini` in the log.
- [ ] Watchdog probes on clientId 18, sync on 17. Sharing one would make the
      watchdog report `not_responding` whenever it probed during a sync and
      blame itself for the collision.
- [ ] `ExecStart=%h/ibc/gatewaystart.sh` assumes IBC is installed at `~/ibc`.
      Verify that path on the box before the first start; it is the one thing
      here that was not verifiable from this machine.
