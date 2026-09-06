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
- [~] **SUPERSEDED by 30.1 #1 (D1a).** Was: replace the OneDrive backup with
      VPS-side storage. The VPS half happened and made things WORSE, which is
      the audit's point: the zip now lands in `~/backups/chains`, on the same
      disk as the data it protects. A backup on the same disk is not a backup.
      The ruling is Hetzner server backups plus an `rclone` off-box sync of
      `data/` + `~/backups/` + `~/state/`.
- [~] **SUPERSEDED by 30.1 #1 (D1a).** The VPS-home half is done. The backup
      half is not, and the stakes rose: 30.1 rules the point-in-time store "the
      system's memory; it must survive the box." Chains are no longer the only
      irreplaceable asset — the store, the register and the packets are too.
- [~] **RESOLVED then SUPERSEDED by 30.1 #2 (D1b).** SPX/SPCX ingestion landed
      via Massive Starter. The audit goes further: yfinance is a single point of
      failure carrying 13 of 15 symbols' chains and every price, so **Massive
      becomes primary for all 15** and yfinance is demoted to fallback and
      cross-check.

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

## VPS deployment fixes (5 Sep 2026)

Two defects the deployment found, both invisible from this machine.

**run_id lineage.** `ibkr_portfolio` never passed `run_id`, so every Portfolio
Truth row landed unattributable — two syncs a minute apart were
indistinguishable in the store and no packet could claim lineage over rows it
could not identify as its own. There was also **no convention to follow**:
`run_eod` had no run_id either, only an implicit identity in `started` and its
output filenames. So `session.new_run_id(producer)` is now the single
convention, `<producer>-<utc stamp>`, and BOTH producers use it.

- [ ] run_id is stamped on exposure profiles and on Portfolio Truth rows. The
      pin log does not carry one yet — it is derived from profiles that do, so
      the lineage is reachable, but a direct column would save a join.
- [ ] `new_run_id` uses MICROSECOND resolution. Seconds was not an identity:
      two syncs in the same second shared one id, which is exactly the failure
      a run_id exists to prevent. Caught by the test, not by review.

**Three unit defects, all silent.** The box was carrying an `override.conf` to
work around them; it can now be deleted (README has the command, and per Part 25
an override is the box editing code, which the rule forbids).

| Defect | Why it was invisible |
|---|---|
| `Environment=DISPLAY=:0` | names a physical display that does not exist headless; IBC's Java GUI dies or hangs before the login, looking like the credential hang |
| missing `-inline` | `gatewaystart.sh` backgrounds and returns, so `Type=simple` sees the service exit and flaps while real IBC runs unsupervised outside the cgroup |
| `StartLimit*` in `[Service]` | systemd moved these to `[Unit]` in v230 and **ignores them silently** under `[Service]` — the restart-storm guard was never in force |

- [ ] `xvfb` is now a prerequisite (`sudo apt install -y xvfb`), added to the
      README. The unit deliberately sets no `DISPLAY`: `xvfb-run
      --auto-servernum` exports its own, and setting it by hand reintroduces
      the bug.
- [ ] Still unverified from here: `%h/ibc/gatewaystart.sh`. Confirm IBC's
      install path on the box before the first start.

## Registry semantic pass (5 Sep 2026) — 26.4 fields on all 57 metrics

`native_horizon` reviewed and `information_half_life`, `invalidated_by`,
`observation_type`, `revision_policy` added to every metric and both bulk
blocks, vocabulary-checked by `tools/check_registry.py`. Note the count: **57,
not 44** — 44 was right until Portfolio Truth added 13.

Two additions beyond 26.4's letter, approved 5 Sep, recorded here because they
are ours and not the architecture's:

- **`invalidated_by`.** Half-life gates decision use, so it must be the TIGHTER
  constraint; an expiry rewrite is a hard invalidation, not decay. Encoding the
  rewrite as a half-life would have licensed acting on a ten-day-old gamma flip
  merely because no expiry had intervened, when a fresh one is computed nightly.
- **`recomputed`** as a third `revision_policy`. Neither `never` nor `revised`
  describes what happened twice this week: the mtime fix and the settlement
  rule REWROTE Friday's numbers. A methodology change is not the source
  restating.

**Every dealers-hand-v1 metric is `inferred`, not `calculated`** (28 of them).
The signing convention is an assumption about inventory that public chains
cannot observe — under the customer-hand reading every sign inverts. Calling it
`calculated` lends the arithmetic's certainty to the assumption beneath it. OI
constructs stay `calculated`: `max_pain` would be unchanged if every implied vol
in the chain were wrong, which is the test for which side of that line a field
sits on.

- [ ] **PREREQUISITE FOR SPX GOING LIVE: `greeks_source` is hardcoded to
      `computed_bs_from_iv`.** Solver-IV-derived greeks are `inferred` like all
      dealer-signed metrics — the solver is a second inference layer, not a
      different observation type — so the distinction cannot live on the metric
      entry. It has to be per row, and that field is the place. Today it does
      not vary, so a yfinance-IV profile and a solved-IV profile are
      indistinguishable in the store. Make it emit `solved_bs_v1` before SPX
      Greeks are computed.
- [ ] **The pin backfill now VIOLATES a declared policy, not a preference.**
      `pin.*` is `revision_policy: never` because the architecture says the
      tolerance is "declared in advance and never revised after the fact". The
      code still regrades an old row at today's tolerance on a re-run. Rows
      carry their own `tolerance_bps`, so the fix is for a backfill to refuse
      to change it.
- [ ] ALFRED remains uningested; `fred_macro` declares
      `revision_source: ALFRED -- not yet ingested` so the gap is visible in
      the registry rather than only in this file.

### Per-field mechanism_group — the code/registry gap is closed

`exposure_compute.FIELD_MECHANISM_GROUPS` stamps 41 fields (27 derived / 8 OI /
6 quality) and the profile emits it as `field_mechanism_groups`.
`check_registry` asserts the code map and the registry agree field by field, so
the two cannot drift apart again. A consumer counting confluence reads that map,
not the profile-level scalar.

### systemd: silent-ignore is now a five-time pattern

`tools/validate_systemd_units.py`, closed allowlist over all 9 shipped units,
in CI. Verified it catches every historical instance: a directive in the wrong
section, an invalid enumerated value, and an unknown directive. An unrecognised
directive FAILS rather than being skipped — a typo and something nobody vetted
look identical from here, and the vetting is the value.

- [x] **DONE 5 Sep. `ProtectHome=read-write` on `chester-eod.service` was
      invalid** (`yes|no|read-only|tmpfs`) and silently ignored. **It was hiding
      a second defect:** `ProtectSystem=strict` mounts the whole tree read-only,
      so the unit had no writable path for logs, state, backups or the data lake
      and would have failed on its first real write. Added `ReadWritePaths`.
- [ ] `systemd-analyze verify` on the box would catch a superset of this and
      needs systemd, which the authoring machine has not got. Run it once on
      the VPS as a cross-check of the allowlist.

### Portfolio sync gaps are now visible without reading a log

`SuccessExitStatus=0 3 4 5 6` is deliberate — none of those is a systemd
failure — but it means `systemctl status` shows GREEN on a failed sync. The
sync now writes `~/.chester/ibkr_sync_status` and, only on a clean run,
`~/.chester/ibkr_sync_last_success`, whose AGE is how long the portfolio series
has had a hole in it. Same state vocabulary as the watchdog's health file, so
the two agree on what a failure is called and not merely that one happened.

## Provenance, tolerance policy and the decision CLI (5 Sep 2026)

- [x] **DONE. `greeks_source` varies with the IV path.** `computed_bs_from_yf_iv`
      for the chain's own IV, `solved_bs_v1` when tools/iv_solver.py fed it, and
      a mixed profile reports AS mixed with the solved fraction rather than
      collapsing to whichever dominated. iv_solver already tagged every row with
      `iv_source`; the label now rides that through to the profile and onto every
      pin-log row. **This was the prerequisite blocking SPX Greeks.**
- [x] **DONE. The pin log honours row-level `tolerance_bps`.** A rerun preserves
      each row's declared tolerance and logs that it did; only `--allow-regrade`
      moves it, and says loudly that it is a methodology change. Demonstrated:
      widening config 25 -> 500bps leaves a rerun at 25bps with the SAME miss,
      while --allow-regrade turns that miss into a hit. That is precisely the
      marking-your-own-homework failure the policy exists to stop.

`tools/decide.py` is the register's first writer. It exists NOW, before anything
produces a recommendation automatically, so the first thing that does cannot
route around it.

- [ ] **The CLI's shape was inferred.** No spec for it existed in the repo. It
      follows the register schema and Part 7 (invalidation is a REQUIRED
      argument, not an optional one -- an argument you can omit gets filled in
      later, which is exactly when it stops being an invalidation) and 26.7's
      edge taxonomy as a closed set. Review it against what you actually meant.
- [ ] Every recorded decision gets a packet at write time. `code_dirty` reads 1
      whenever the tree is dirty, which it was during development; a real
      decision should be recorded from a clean tree.
- [ ] No `supersede` or `set-status` subcommand yet. The register supports both
      (Part 7 revision creates a new record); the CLI does not expose them.
- [ ] The CLI has no DECISION_BLOCKED check (26.2 #7). A recommendation whose
      inputs are missing or stale should be blocked while the report still
      publishes; today the CLI records regardless and only the empty manifest
      hints at it.

### A bug the first dry run showed

`_inputs_for` took the newest directory holding ANY chains, so on a day the
vendor capture ran alone it pinned SPX and SPCX into a **SPY** decision's
manifest. A packet that pins the WRONG inputs is worse than one that pins none:
it claims a lineage it does not have, and the claim is indistinguishable from a
true one. It now walks back until it finds the instrument's own chain, and
reports an empty manifest with a reason when there is none.

## DECISION_BLOCKED (26.2 #7) — 5 Sep 2026

`tools/freshness.py` + wired into `tools/decide.py`. Every signal in
`--signals-used` (now REQUIRED -- a decision citing no evidence cannot be
checked, and an unchecked decision is what 26.2 #7 forbids) is assessed at entry
time against ITS OWN registry `information_half_life`, not one global timeout.

Stale or missing -> the decision is still RECORDED, lands as `draft` with a
`blocked_reason`, and can never be `active`. Recorded rather than refused
because an abstention is a decision and the register logs abstentions: the
blocked rows are the record of what the system could not answer, and dropping
them would leave only the days it happened to be ready.

The invariant is enforced in `Register.record()`, not in the CLI -- downgrading
only in the CLI would leave it one careless caller away from false. `set_status`
also refuses to promote a blocked row in place.

Exit codes: 0 clean, 2 restricted instrument, 3 DECISION_BLOCKED. A blocked DRY
RUN exits 3 as well; a dry run's job is to say what would happen, and a 0 would
say "fine" about a decision that is not.

### A judgment worth revisiting

**Friday's close on a Saturday is NOT stale**, and the block does not fire on
it. A `session` half-life is assessed against the most recent COMPLETED trading
session (via the NYSE calendar), so on a Saturday that is Friday and Friday's
data is the current vintage. Blocking it would forbid the process Part 7 is
built on -- the Friday session is what SETS the swing thesis. What does block on
a Saturday is anything with an `intraday` half-life, because nothing is trading
and no intraday reading can describe a closed market.

- [ ] Two bugs the first transcripts exposed, both fixed: the lookup passed the
      decision's ticker to every store, so FRED rows (instrument=NULL) and
      portfolio rows (keyed on the ACCOUNT, not the symbol) all reported as
      missing -- a false block, which is the failure that teaches people to
      ignore the check. And `fred.anything` passed the registry check via the
      bulk block, then failed as missing data, blaming the pipeline for a typo.
- [ ] `INTRADAY_MAX_AGE_H = 4.0` and `FREQ_MAX_AGE_DAYS` are declared constants
      with no calibration behind them. They are a first cut; tighten once there
      is a real sync cadence to measure against.
- [x] Supersede / set-status subcommands. `decide.py set-status` now supersedes
      per Part 7 rule 3 rather than mutating -- `Register.set_status()` keeps
      its in-place UPDATE but has no production caller, existing only so the
      validation suite can prove the freeze constraint against a direct writer.

## Gate 1.5 (26.11) -- open

- [x] **SETTLED 5 Sep 2026: Read-Only API refuses What-If.** Measured on the
      VPS. Evidence line, the Gateway's own words:

          "The API interface is currently in Read-Only mode"

      RULING: Read-Only stays ON through the hand-placed-orders phase and comes
      off at Gate 2 by design, when code-side guards replace it -- not as a
      concession bought to unblock a feature. `ibkr_whatif.py` is kept intact
      and unused until then; `--preview-mode whatif` is the flag that turns it
      back on, so Gate 2 needs no code change here.
- [x] **SETTLED 2026-09-05: the stock schedule is VERIFIED, and this account is
      FIXED, not Tiered.** Hand-read from Client Portal by the operator: USD
      0.005 per share, $1.00 minimum per order, 1% of trade value maximum,
      all-in. `IBKR_COMMISSION_SCHEDULE_VERIFIED = True`, with `..._VERIFIED_ON`
      and `..._VERIFIED_BY` riding in every stock `expected_cost` packet. Both
      readings 26.17 asked for are closed at once -- the figures, and the
      structure, which only Client Portal exposes.

      The declared Tiered card was wrong twice over: wrong rate ($0.0035 /
      $0.35 against $0.005 / $1.00) and wrong claim about what it covered. A
      100-share SPY order was estimated at $0.35 and is actually $1.00 -- and
      note WHY that hid: under Tiered the per-share total landed exactly on the
      floor, so `floor_applied` was False and the estimate looked like
      arithmetic rather than a minimum. Under Fixed the minimum plainly binds.
      The FlashAlpha check earned its keep.
- [x] **SETTLED for stocks: the estimate is ALL-IN, not a floor.** Fixed bundles
      the exchange, clearing and regulatory pass-throughs that Tiered bills
      separately, so a stock `expected_cost` is the whole number:
      `is_floor_not_all_in` is False and `excludes` is empty. This INVERTS what
      this file said while it assumed Tiered. Still worth doing, with a changed
      purpose: compare the first real fill against the estimate and record the
      gap -- now a check ON a verified card, not the thing that would verify it.
- [ ] **The OPTION card is unverified AND structurally stale: Tiered bands on a
      Fixed account.** Only stocks were hand-read. The per-contract bands
      (0.65 / 0.50 / 0.25 by premium) describe a schedule this account is not
      on, so an option `expected_cost` is not this account's cost. Left in place
      rather than guessed at -- inventing a Fixed per-contract rate to fill the
      hole is exactly the FlashAlpha move. `IBKR_OPT_COMMISSION_VERIFIED = False`
      and `schedule.structure_mismatch = True` ride in the packet and
      `format_estimate` prints both, so it cannot be read as trustworthy by
      accident. No option has been traded, so this blocks nothing today. Hand-read
      the option schedule off Client Portal before the first option decision.
- [ ] **Short stock margin is not modelled.** The measured leverage multiplier
      describes the account's long-side treatment; Reg T requires 150% for a
      short. A SELL of stock carries an explicit caveat in the record rather
      than a silent under-margin. Model it before any short is recorded.
- [ ] **No live What-If has ever run, and now none will until Gate 2.** Every
      number in `tools/validate_ibkr_whatif.py` is a fixture. When Read-Only
      comes off, the first live run must confirm: commission populated for a
      100-share SPY order, margin fields not all Double.MAX_VALUE, and
      `BuyingPower/AvailableFunds` yielding a sane multiplier.
- [ ] The expression rules are mechanism arguments, not calibrated thresholds.
      `carry_edge_no_accrual` fires at <=7 DTE and `HORIZON_DAYS` maps swing to
      21 days; both are declared, neither is measured. Revisit once outcomes
      exist to grade expression failures against.
- [ ] `expected_cost` is deliberately NOT in `output_hash` -- commission tiers
      and margin state move, and an identical decision should not fail replay
      for that. If 26.16 #5 later needs the economics to be part of what
      replays, that is a schema decision, not a hash tweak.
- [ ] The decision CLI is `tools/decide.py`, not `new_decision.py`. Renaming is
      cheap if the other name is preferred -- say so rather than both existing.

---

# Part 29 + Part 30 reconciliation (5 Sep 2026)

*Read against Change Order #3 (Part 29, eight tactical additions) and Audit #2
(Part 30, Track D). **Nothing built in this pass** — this is the reconciliation
only. Items above marked `[~]` are superseded by a ruling below.*

## Track D — the ruled order of work (30.7)

Track D supersedes every informal "next" in this file. ~15–18h to a running
Daily with Friday/Sunday and a closed learning loop.

- [ ] **D0 — Daily run-state inventory (0.5h). Out-of-band item 4, still open;
      retire cron-job.org.** Gate: *nothing is built on an unconfirmed
      pipeline.* Repo-side findings are recorded under "D0 — what the repo
      already answers" below; the rest needs the principal.
- [ ] **D1 — Durability trio (2h).** Three separate tasks, broken out below.
- [ ] **D2 — `regime.py` (2h).** Macro regime state from series ALREADY in the
      store (net liquidity, HY OAS, curve, realized/implied vol, breadth,
      dealer gamma regime), written as an observation with its own
      `available_at`. Declared thresholds, state machine — not a 0–100
      composite (29's rule 1). Feeds the Daily's Backdrop immediately and seeds
      T&B (Sessions 10–14), which refines rather than replaces it. Per 30.8,
      VIX term structure (VX1/VX2/VX3 slope, contango → backwardation) joins as
      a declared state machine once CFE Enhanced is subscribed. **+31.2: D2 also
      emits `regime.debt_cycle_state` (+1.5h)** — see the Part 31 section below;
      it is a regime output, not a pillar row.
- [ ] **D3 — Session 4-lite (3h). BLOCKS ANY DAILY NARRATIVE.** 30.3: numbers
      in the store are gated, prose is not. Payload-constrained generation on
      the Monthly's pattern, a numeral audit that FAILS THE BLOCK when a number
      appears that is not in its payload, and a directional check. Ruling
      verbatim: *"A Daily that can invent a number is worse than no Daily."*
- [ ] **D4 — Daily Cascade pipeline (3–4h).** Block payload builders (Part 20)
      reading the store, render, `daily_cascade_state.json`, drafted setups
      becoming `decide.py` drafts. **Two VPS timers first (07:00, 16:30)**; the
      remaining seven of Part 28's nine are added as each block earns trust.
      `auto_publish: false`. **+31.3: D4 also lands overnight gap attribution
      (1h) and the country-fund NAV-premium series (0.5h)** — see the Part 31
      section below; both are Backdrop-context rights only.
- [ ] **D5 — 15b-lite (3h): the loop closes.** Shadow outcome at its horizon
      for EVERY decision from stored prices — **taken, declined and draft
      alike**, which is what makes the loop learn when no trade is placed.
      Taken decisions additionally reconcile to Portfolio Truth fills. Plus a
      `hypotheses` table (Part 29 registers seven) on the same grading path,
      and the Friday Weekly Reflection as a query over it with narrative on
      top. Execution-quality analytics land here too — see 30.8 adopted #1.
      **31.5(a) affirms this step and its scope verbatim** — taken, declined and
      draft alike — so D5 is unchanged, not expanded, by Part 31.
- [ ] **D6 — 15a-lite (2–3h): Sunday Forward Plan.** Register state + regime +
      calendar + Part 27 v1 movers + lessons-retrieved-before-decision.

**Then, in this order (30.7):** Part 29 items 1–4 · intraday cadence (gated on
Tuesday's debut + capture-instant T) · T&B full · remaining v17 core (S1/S2
leftovers, S3b, ALFRED, alert delivery) · Part 29 items 5–9 · Part 28 A1/A3 ·
Sessions 8–9 with Part 27 v1.

## D1 — the durability trio, as three tasks

- [ ] **D1a — Off-box backup (30.1 #1).** Hetzner server backups (console
      click, ~20% of box price) AND `rclone` nightly sync of `data/` +
      `~/backups/` + `~/state/` to cloud storage. Touches: a new
      `scripts/rclone_sync.sh`; new `deploy/systemd/chester-backup.{service,timer}`
      asserted by `tools/validate_systemd_units.py` per 30.2(b);
      `run_eod.py:backup_chains()` and `config.BACKUP_DIR` for the target.
      Needs from the principal: the Hetzner console click, and an rclone remote
      + credentials.
- [ ] **D1b — Massive primary for all 15 symbols (30.1 #2, ~1h).** yfinance is
      an unofficial API that breaks periodically and currently carries 13 of 15
      symbols' chains AND every price. Touches: `altdata/sources/massive_chain.py`
      (vendor-only today → primary); `altdata/sources/options_chain.py`
      (yfinance → fallback + cross-check); `run_eod.py` stages 1 and 1b merge;
      `config.options_universe()` / `massive_universe()` /
      `PENDING_VENDOR_SYMBOLS` collapse into one universe;
      `tools/exposure_compute.py` — **the `greeks_source` split collapses**,
      since solver IV then feeds every symbol identically, which also retires
      the SPX-specific `greeks_status=pending_solver_gate` path. Watch: Massive
      rows must carry the staleness fields the data-quality gates read
      (`last_trade_date`), and the yfinance cross-check inherits FlashAlpha's
      old role as the independent witness.
- [ ] **D1c — SQLite WAL + busy_timeout + repo-wide write lock (30.1 #3,
      ~30 min). BEFORE ANY NEW WRITER SHIPS.** Confirmed in the repo: neither
      `register/store.py` nor `altdata/observations.py` sets WAL or
      `busy_timeout` — both open with `PRAGMA foreign_keys = ON` and nothing
      else. And the three existing `flock` calls
      (`scripts/run_eod_cron.sh:59`, `sync_ibkr.sh:43`,
      `ibgateway_watchdog.sh:73`) each lock **their own script against a second
      copy of itself** — `eod.lock`, `ibkr_sync.lock`,
      `ibgateway_watchdog.lock`. None of them guards the database, so two
      different writers collide today with nothing in the way. Touches: both
      store classes' `__init__`; a shared lock helper; every writer
      (`run_eod.py`, `pin_log.py`, `decide.py`, the IBKR sync, the heartbeat).
      Roster this must survive: EOD, heartbeat, Portfolio Truth every 30 min,
      Gateway watchdog, plus incoming intraday, MOC sampler and seven Daily
      runs. Failure mode named in the ruling: `database is locked` errors *that
      look like data gaps*.

## Part 30 standing rules — bind every future change

- [ ] **30.2(a) — identity and time, enforced by the registry gate.** Every new
      writer and every new source passes through `session_date()`, canonical
      microsecond UTC, and `run_id`-on-write. No exceptions. The weekend's
      whole failure population (UTC-vs-session ×3, mtime-vs-observation ×2,
      silently-ignored systemd directives ×5, timestamp-precision ×2,
      run_id-precision ×2) was identity and time bugs, every one caught by a
      test or a deployment and never by reading.
- [ ] **30.2(b) — every shipped systemd directive is asserted by the
      validator.** The unknown-directive trap stays.
- [ ] **30.4 — REPORTS NEVER FETCH.** Fetchers are timers that write the store;
      every report block queries the store as-of. One pull per source per
      cadence, shared by all nine Daily runs, the Weekend, the Monthly and T&B.
      This is the data-efficiency rule and the leakage rule at once. **Any
      block found fetching is a defect** — applies to the Daily's builders when
      D4 lands, and is worth auditing `monthly_macro` against.
- [ ] **30.8 ops — the IBKR market-data line budget is a registry-level fact.**
      100 concurrent lines by default; more cost money. CAP-SPX at full
      constituent breadth is infeasible on that budget. Record it in the source
      registry so the MOC sampler does not discover it at 15:50.

## Part 30.8 — market-data feeds, approved ~$12.55/mo

- [ ] Subscribe, each tied to an existing consumer: **NYSE/Arca/MKT order
      imbalances ($3.00)** — 29.4's auction probe fails without the
      entitlement; **CFE Enhanced ($4.50) + CBOE Streaming Indexes ($3.50)** —
      fill four of the Volatility paper's eight `not_yet_sourced` regime tells
      and feed D2; **CME L1 ($1.55)** — ES/NQ/RTY overnight for the Daily's
      Market Base; **OPRA L1 ($1.50)** — intraday cadence only, where Massive's
      15-minute delay bites. **FX ($0)**.
- [ ] **Nasdaq Closing Cross (NOII) stays a marked GAP.** NYSE-family auction
      data is never presented as market-wide.
- [ ] Deferred until a consumer names them: CBOT, NYMEX, COMEX.
- [ ] **30.8 adopted #1 — executions, fills and commissions into Portfolio
      Truth (read-only).** This is what makes 26.7's *execution error*
      measurable rather than estimated, and it lands in D5 as execution-quality
      analytics: slippage vs decision-time price, implementation shortfall,
      fill-vs-limit. Also the first real check on the Gate 1.5 cost estimate —
      see the schedule-verification item above.
- [ ] **30.8 adopted #2 — portfolio-impact line.** Every regime change and
      alert annotated with the held book's sensitivity (beta, net delta/gamma
      from Portfolio Truth × the exposure engine).
- [ ] **30.8 adopted #3 — standard derived forms as a registry convention.**
      One generic function computing level, own-history percentile, z,
      momentum, acceleration, divergence, regime, anomaly, confidence for any
      registered metric. A convention over the store, not a new layer.
- [ ] **30.8 adopted #4 — ETF-vs-underlying closing-flow divergence** (Arca) as
      a 29.4 metric.

## Part 29 — after Track D, in 29.9's order

Ordering rule: **forward-only loggers first** (every day unlogged is lost);
probes before wiring; nothing displaces Tuesday's debut check.

- [ ] 1. RTAT10 fetcher + 2016 backfill + derived metrics (29.3) — 2h. Free
      key. **Do first: it is the rare historied source**, so percentiles seed
      on day one and it is backtestable against 2021/2022. Registry flag
      `sample: top10_censored` on every derived metric — head of the
      distribution, never market-wide breadth.
- [ ] 2. Cohort registry + nightly consensus logging + return attribution
      (29.2) — 2h. **Starts the estimate-history clock**; decomposition reads
      `insufficient_history` until Q4. Seed: DELL, NVDA, SMCI, AVGO, HPE.
- [ ] 3. Probes: IBKR imbalance ticks (29.4) and IBKR borrow fields (29.7) —
      1h, read-only. Gated on the 30.8 imbalance subscription.
- [ ] 4. `response_ratio(stimulus, response, window)` primitive (29.0) — 1h.
      Four items reduce to it: MOC absorption, Dell revision-velocity,
      meme attention divergence, PM–asset divergence. `observation_type:
      calculated`.
- [ ] 5. Yen monitor v0 (29.1) — 2–3h. Five mechanism groups, FXY chains
      through the exposure engine, JGB CSV. ORANGE needs three groups, RED
      five.
- [ ] 6. Meme v0 (29.7) — 4–5h. ApeWisdom, FINRA, borrow series, funnel,
      lifecycle state machine, board, register rules.
- [ ] 7. ZEC theme block + DAT entity template + CYPH instance (29.5–29.6) —
      4–5h. Every figure enters the claims registry (26.5) and is **verified
      via EDGAR before any report cites it**.
- [ ] 8. MOC sampler + event table + pin-log column (29.4) — 2.5h. New cadence:
      **15:50–16:00 sampler at ~30s** on the VPS.
- [ ] 9. PM phase 2 (29.8) — 5–7h. Gated on Part 27 v1 through one live event.

## Part 29 requirements that land on code already built

- [ ] **29.7 → `tools/expression_check.py`: a bare meme short must be flagged
      with the unbounded-loss note.** Meme shorts default to defined-risk. The
      module has no short-side rule at all today — its six rules are about edge
      shape, none about unbounded loss.
- [ ] **29.7 → the register: `book: opportunistic`.** New column or tag, with
      `edge_type: behavioral`, horizon intraday/swing, and a **declared sizing
      cap in config (per-name and aggregate % of NAV) — numbers set by the
      principal, not at 09:31.**
- [ ] **29.7 → invalidation semantics: short invalidation includes borrow
      conditions** (CTB above X or availability below Y invalidates even if
      price has not moved). `decide.py --invalidation` is free text today.
- [ ] **29.7 → attention metrics get `half_life: intraday`** so
      DECISION_BLOCKED refuses entries on stale mentions. The freshness check
      already enforces this once the metrics are registered.
- [ ] **29.4 → event classification table in `altdata/session.py`, beside the
      holiday table:** NORMAL / MONTH_END / QUARTER_END / INDEX_REBALANCE /
      OPEX / TRIPLE_WITCHING / ETF_REBALANCE. *A reconstitution-day imbalance
      is never discretionary flow.*
- [ ] **29.1 → FXY options through the exposure engine** as the FX-vol
      mechanism group (IV and skew as the risk-reversal analog). The engine
      takes a new symbol; the universe question is D1b's.
- [ ] **29.6 → CYPH joins the chain universe**, subject to the existing
      liquidity floor.
- [ ] **29.2 → `kill_condition` on registry entries** (Dell's: backlog
      conversion stalls). Already an open Session 2 item; 29.2 gives it its
      first concrete instance.

## D0 — what the repo already answers

*Determined by reading the repo, so the inventory does not have to re-ask.*

- **The Daily Cascade has no code. None.** What exists is the reservation only:
  `daily_cascade` in `state/emit.py:VALID_KEYS`, three `allowed_reports` rows
  in `source_registry.yaml`, and a "Not yet built" row in `CLAUDE.md` and
  `AGENTS.md`. There is no `daily_cascade/` package, no runner, no block
  builders.
- **`monthly_macro/run.py` is the only caller of `emit()`.** So the dashboard
  has never received a `daily_cascade` state record from this repo.
- **`.github/workflows/monthly-report.yml` has `on: workflow_dispatch:` and no
  `schedule:` block.** GitHub therefore never fires it by itself — an external
  caller must POST to the dispatch API. That external caller is the thing D0
  retires, and **nothing in the repo replaces it yet.**
- **The workflow consumes four secrets:** `FRED_API_KEY`, `ANTHROPIC_API_KEY`,
  `CHESTER_STATE_URL`, `CHESTER_STATE_TOKEN`.
- **`registry-check.yml` runs on push and pull_request** — unaffected by
  retiring the external scheduler.
- **The VPS timer roster is four units** (five with `chester-heartbeat.timer`,
  added 6 Sep — see "D0 finding closed" at the end of this file), none of them
  the Monthly and none of them a Daily: `chester-eod.timer` (Mon–Fri 16:10 ET),
  `chester-ibkr-sync.timer` (Mon–Fri 09..17:00/30 ET),
  `ibgateway-restart.timer` (01:00 ET daily), `ibgateway-watchdog.timer`
  (every 5 min). **Retiring cron-job.org therefore requires building the
  replacement trigger — it is not a deletion.**

---

# Part 31 reconciliation (6 Sep 2026)

*Read against Part 31 — the only new architecture part carrying system
obligations. Five papers landed in `docs/whitepapers/`; Part 31's own framing is
that **most of a paper changes nothing** and it records only where one obliges
the system to change. **Nothing built in this pass.** Total ~8.5–9.5h, and 31.7
is explicit that it **folds into Track D and T&B rather than opening a track**,
so the D-order in "Track D — the ruled order of work" above is unchanged.
Nothing in Part 31 supersedes an item already in this file; three D-steps gained
an annotation in place (D2, D4, D5) and the rest is new work below.*

## Folded into existing D-steps — annotated above, listed here for the total

- [ ] **31.2 — `regime.debt_cycle_state`, inside D2 (+1.5h).** The long-cycle
      debt resolution as ONE mechanism state with two mutually exclusive
      branches sharing antecedents: **deflationary liquidation** (falling
      inflation with rising real yields, currency strengthening; destroys
      equities/credit/real estate, protects long governments, cash, gold after
      revaluation) and **inflationary repression** (nominal yields capped below
      inflation, persistent negative real yields, gold rising against real
      yields; destroys **bonds and cash in real terms**, protects gold,
      commodities, real assets, equities partially). Observables — debt/GDP and
      its full-employment trajectory, the structural deficit, **net interest as
      a share of revenue**, foreign-official absorption share, term-premium
      behavior when growth expectations fall, real yields vs inflation, gold vs
      real yields — are in the store or cheap to add. **Ruling: read together as
      one state, never as separate pillar rows** (26.9 applied to a new
      cluster). `observation_type: inferred`, with the honest counter-case in
      the registry note: no demonstrated debt/GDP threshold, Japan at twice the
      ratio, the reserve-currency exception.
- [ ] **31.2 sizing consequence — the operative half, and it is a RULE, not a
      metric.** The Doctrine's duration sleeve is a **deflation** hedge
      specifically. Book A's Contraction band raises duration, which is the
      right instrument for branch one and the **wrong** one for branch two. The
      tail-hedge budget's expression therefore depends on which branch the state
      reads, and the dependency is recorded in advance **so the choice is not
      made under stress.** Lands with the branch logic; touches the Doctrine's
      Book A bands, not only code.
- [ ] **31.3(a) — overnight gap attribution, with D4 (1h). The cheapest win in
      the International Equities paper.** The 07:00 report reports the gap
      today; it will attribute it: Tokyo close-to-close, the European session's
      move at time of writing, the futures move outside both, and the release or
      headline in whichever window dominated. Data is already available —
      index-futures continuous series plus regional index closes. New metrics
      `overnight.gap_attribution_*`, `observation_type: calculated`,
      `half_life: session`. **Rights: Backdrop context only — may NOT generate a
      Book C setup.**
- [ ] **31.3(b) — country-fund premium to stale NAV, with D4 (0.5h).** Premium
      to last-published NAV computed at the U.S. close for the tracked country
      and regional funds. The registry entry must say **explicitly that this is
      a timing artifact, not a mispricing** — `observation_type: observed`,
      `half_life: intraday`, with the note that a stop placed on a country fund
      is triggered by exactly this artifact. Rights: Backdrop context, plus a
      **Book B expression warning when an international candidate's stop sits
      inside the typical artifact range.**

## New work Part 31 adds outside the D-steps

- [ ] **31.1 — `tools/base_rates.py` (2–3h, gated on D2 for the store's
      series). A base rate is a computed observation, not a table in a paper.**
      The reason is the replay guarantee: *a base rate cited in a decision
      packet must be replayable as of the date it was cited, or the packet's
      guarantee is void the first time a table is updated.* Computes the paper's
      Part I and II tables from series already in the store — return
      distributions at four frequencies with p25/median/p75, intra-year drawdown
      distribution, drawdown frequency and duration by depth band, streak and
      gap statistics, correlation by regime, VIX distribution — each written as
      an observation with `available_at`, `registry_key: baserate.*`,
      `observation_type: calculated`, `native_horizon: strategic`,
      `half_life: permanent`, `revision_policy: recomputed`,
      `trigger_eligible: false`. Recomputed annually by a scheduled job and on
      any methodology change.
- [ ] **31.1 drift flag — a base rate that moves more than a declared tolerance
      on recomputation is FLAGGED FOR REVIEW.** A changing base rate is itself
      information. The tolerance is declared in advance, the same discipline as
      the pin log's `tolerance_bps`, and a recompute never silently regrades.
- [ ] **31.1 — figures the system cannot compute go to the claims registry
      (26.5), not the observation store**: the pre-1970 episodes, the
      international drawdowns, the literature citations, each with its source.
      Gated on the claims registry existing (S14 dependency).
- [ ] **31.1 → `decide.py` gains an optional `base_rate_cited` field**, so a
      variant-perception thesis records the consensus it departs from. Small,
      and `decide.py` already exists.
- [ ] **31.1 → report convention: any report stating a magnitude may state its
      percentile against the base rate** ("a 2.1% decline, 88th percentile of
      daily moves"). The Daily's Backdrop block **adopts it as a standing
      convention** when D4 lands.
- [ ] **31.1 → Top & Bottom carries the bear-rally base rate** in its top-side
      language: three to five 5%+ counter-trend rallies inside a −20% decline,
      p75 of the largest at +16%. This governs how a top call is **held**, not
      how it is made. Lands with T&B (Sessions 10–14), beside the extended
      episode set already listed above.
- [ ] **31.3(c) — `currency_exposure` on `decide.py` (0.5h, immediate; no
      gate).** A hedged and an unhedged instrument on the same market are **two
      different instruments, never interchangeable.** Field values
      `unhedged` / `hedged` / `n_a`, **mandatory for any non-USD-denominated
      underlying**, and `tools/expression_check.py` flags an unhedged
      international position whose thesis makes no mention of the currency —
      the Rule 11 test applied to the leg the ticker hides. Note the ordering:
      this is the one Part 31 item that needs nothing built first.
- [ ] **31.3 universe consequence — the chain-capture universe gains no symbols
      by default.** The international candidates are Book A and Book B
      instruments read from price series, not options. An international ETF
      entering Book C passes the existing liquidity floor like anything else.
      Recorded so D1b's universe collapse does not quietly widen.
- [ ] **31.4 — Positioning & Flows Tables A–C enter the claims registry
      (1h, S14 dependency), NOT the observation store**, because they are cited
      estimates rather than computed series. The registry note carries the
      paper's **three-denominator warning verbatim**: direct ownership of U.S.
      equity, global AUM by institution type, and equity-relevant AUM are three
      different measurements — and **forced-flow footprint = equity exposure ×
      turnover × rule-boundness** is the fourth and the one the system sizes by.
- [ ] **31.4 — the discretionary holders' failure-mode signatures each become a
      `mechanism_group`** so the confluence guard counts them once: platform
      degrossing, redemption waves, liability-driven collateral calls,
      currency-hedge rebalancing, market-maker withdrawal. **Market-maker
      withdrawal is NOT a separate metric** — it is what the absorption
      measurement already detects, and the registry says so rather than creating
      a second reading of one fact. (Same defect class as "four Greeks ≠ four
      votes"; the registry entry is the enforcement.)
- [ ] **31.5(b) — the Systematic Book's failure classes become validator
      obligations**, promoting Part 30.2's catalogue from narrative to standing
      rules, **with one addition that is new law: a safety property is verified
      by READING THE ENFORCING CODE, not the comment that describes it.** This
      came from the client library's read-only flag doing nothing of the kind.
      **Any future docstring asserting an enforcement guarantee cites the line
      that enforces it** — applies to `ibkr_portfolio.py`, `register/store.py`'s
      restriction path, and every validator shipped from here on.

## 31.6 — what Part 31 explicitly does NOT change (binding; recorded so it stays that way)

- [ ] **No new signal family. The Part 26 freeze holds.** None of the papers
      introduces one.
- [ ] **No metric in any of the four papers is `trigger_eligible`.** The
      international sleeve, the debt-cycle branches and the base rates are
      **conditioners and references** — they inform a thesis, size an
      expectation, and set the bar for a variant view. **None of them generates
      a packet.**
- [ ] **Seasonality is `trigger_eligible: false` PERMANENTLY AND BY
      CONSTRUCTION**, not pending evidence — a calendar effect has no
      counterparty story that survives Rule 6. Enforce it in the registry entry
      so no later pass can promote it once there is data.
- [ ] **The presidential/midterm-cycle conditional enters as a DATED REGISTER
      HYPOTHESIS**, not a metric — it joins the `hypotheses` table D5 builds.

## Library bookkeeping from the same drop (not architecture, but owed)

- [ ] **The HTML editions of the library guide and the Dealer's Hand are not in
      the repo.** Only the Markdown arrived in `af57d1c`/`88b1490`; the sole
      committed `.html` is `reports/monthly_macro_2026-05-30.html`. The
      md-canonical-for-editing / html-canonical-for-reading rule is now recorded
      in the guide and in `CLAUDE.md`/`AGENTS.md`, but the artifact it points at
      is missing — commit the two HTML files, or the rule names files that do
      not exist.
- [ ] **Two papers in the guide's roster have no file in `docs/whitepapers/`:**
      **X** (Tops and Bottoms) and **XII** (The Daily Cascade Paper). Both have
      full entries in the guide, and both are cited as dependencies by papers
      that ARE committed.
- [ ] **`paper-building-and-validating-a-systematic-book-draft1.md` (31 Aug,
      ~4,900 words) is superseded by `systematic-book-whitepaper.md`** (6 Sep,
      ~9,100 words, as-built) — same title, same numeral XIX, two files. The
      older one was written *before* Gate 1 as a specification; the newer one
      states plainly that the integration was built first and the paper written
      the other way round. Retire or archive the draft; two files answering to
      one numeral is the numbering hazard the guide exists to prevent.
- [ ] **The guide has no per-paper entry for XX (Base Rates) or XXI
      (International Equities)** — both appear in the at-a-glance table and the
      contents list, neither has a `## XX.` / `## XXI.` section. XVII's entry
      sits in "In draft and planned" rather than in sequence, which reads as
      deliberate; XX and XXI read as an omission.
- [ ] **Guide, XIII entry: "Where Paper V gives reading rules for gamma"** is a
      pre-reorder numeral inside the document that is canonical for numerals. It
      means the Daily Cascade paper, now XII.

---

# D0 finding closed: the heartbeat had no caller (6 Sep 2026) — BUILT

*The D0 inventory turned up one live defect rather than a gap in the plan.
`scripts/check_heartbeat.sh` had existed since the calendar work with **nothing
on the box running it** — no timer, no unit, no caller except
`validate_session_calendar.sh` driving it in a sandbox. The inverted-heartbeat
design was half-built: `run_eod_cron.sh` writes the heartbeat on every clean
exit and no process ever read it. The EOD pass could have failed every night
for the six weeks the system narrative describes and the first symptom would
have been a report with a hole in it. Built before D1 because it is the thing
that tells you D1 is needed.*

**Landed:** `scripts/check_heartbeat_cron.sh` ·
`deploy/systemd/chester-heartbeat.{service,timer}` (08:30 ET daily) ·
`tools/validate_heartbeat_caller.sh` (24 assertions, in CI) · README section 7.

- [x] Daily 08:30 ET timer, **every day including weekends and holidays** —
      the checker is calendar-aware, so a Saturday check reports OK against
      Friday's heartbeat, and running on a closed day proves the monitor is
      alive on the days nothing else is.
- [x] **Four delivery channels**, weakest to strongest: the verdict-keyed log
      line (`grep -c 'verdict=ok'` over a month is an uptime figure);
      `~/.chester/heartbeat_check_last_ok`, touched only when healthy so **its
      age is the outage length**; `systemctl --user list-units --failed`,
      because the unit declares **no `SuccessExitStatus`** and only exit 0
      counts; and email when the box can send it.
- [x] `~/.chester/alerts/eod_heartbeat.json`, **written on every check
      including healthy ones**, at a path fixed now for D4's Morning Brief. A
      brief that only sees a file when something is wrong cannot distinguish
      "all clear" from "the monitor stopped", which is the whole point of an
      inverted heartbeat. The reader ages `checked_at` on it like any source.
- [x] **Delivery outcome recorded, never assumed** — `delivery=mail` /
      `mail_failed` / `no_mta` / `no_address` in both the log and the alert.
      A box with no mail transport says so the day it is installed rather than
      during the outage it was meant to report. Sixth instance of the
      configured-looks-wired-does-nothing pattern; this one is instrumented.
- [x] Exit `9` for "the check itself could not run", deliberately outside the
      checker's 0–3 range: the monitor being broken must not read as the
      pipeline having failed, or somebody debugs the wrong machine.
- [x] The validator was **proved to fail on its target defect** (mutate
      `last_ok` to be touched unconditionally → 2 FAILs), not merely to pass.
      A first attempt at that mutation silently did not match and the suite
      stayed green — caught by disbelieving the green line, which is the
      31.5(b) rule applied to a test rather than to a docstring.

## Two design departures worth remembering

- **This wrapper does NOT `git pull`,** unlike `run_eod_cron.sh` and
  `sync_ibkr.sh`. Part 25 has the box pull before running; a monitor is the
  exception, because a pull that hangs or fails would become a heartbeat
  failure — the monitor reporting on itself. The checker reads a local file and
  a local holiday table and needs no fresher code than the box has.
- **`Persistent=true`,** unlike `chester-ibkr-sync.timer`. A missed sync would
  append a snapshot stamped now but describing whenever the box came back — a
  misdated observation, worse than a gap. This writes no dated record; it
  measures the heartbeat's age at the moment it runs, so a catch-up check is a
  late check, and a late check finding a four-day-old heartbeat is the alarm.

## CI gate structure (6 Sep 2026) — one failure must not hide the others

- [ ] **Make `registry-check.yml`'s gates run independently.** The job runs
      seven checks as seven sequential steps, so the first failure ends the job
      and every later step reports `skipped`. When
      `validate_register.py` (step 6) went red at `55630fb`, it took the
      Portfolio Truth gate, the IB Gateway watchdog policy, the heartbeat
      caller policy and the systemd directive allowlist down with it —
      **sixteen consecutive runs in which four gates did not execute and
      nothing said so.** `skipped` reads as "not applicable" at a glance; it
      meant "unknown" for a day.
      - The cost of the coupling is not the delay, it is the false reading. A
        red X on the workflow says one thing is broken. It in fact said one
        thing is broken and four things are unmeasured, and the difference only
        surfaced because the failure was investigated rather than triaged.
      - Two ways to fix it, and they are not equivalent. `continue-on-error`
        per step keeps one job and lets every gate run, but the job's own
        conclusion then needs assembling or a real failure goes green — trading
        a masking bug for a swallowing bug, which is worse. A matrix job (one
        gate per job, `fail-fast: false`) gives each gate its own pass/fail line
        and its own log, and the workflow fails if any job does. Prefer the
        matrix; the seven checks share only the checkout and a `pip install
        PyYAML`, so there is nothing to serialise for.
      - Blocks nothing today — all seven are green as of `2e58f87`. It is a
        wanted change to the reporting, not to the checks.
- [ ] **Decide whether the two IBKR cost validators belong in the gate.**
      `validate_ibkr_costs.py` and `validate_ibkr_whatif.py` are not in
      `registry-check.yml`, so the commission rate-card change in `7faaf64` was
      verified only by hand on the box. They need no data and no network — the
      same profile as the checks already in the workflow. Fold them in with the
      matrix above rather than as two more sequential steps.

## Still owed on the box (Part 25 — the VPS runs code, this repo cannot install it)

- [x] **NOTED 2026-09-06: the box holds a write-capable deploy key.** Added
      after a commit authored on the box stranded itself — the work was
      committed locally and had no way out, because the box could pull over
      HTTPS but not push. The key closes that. **It is a recovery path, not a
      license.** Part 25's rule is unchanged and unweakened: *the VPS runs
      code; it never edits code.* Authoring still belongs in the repo
      workflow; what changed is only that rescuing a commit that should not
      have been made here no longer needs a human at a second machine. A
      standing escape hatch invites use, so the test stays the same one as
      before it existed — if a change could have been made on the laptop, it
      should have been. Each time it is used, record the exception in the
      commit message the way `7faaf64` does.

- [ ] **Pull, copy the two units, enable the timer.** README section 7. No gate
      held over this one, unlike the Gateway units: it is read-only, writes
      only its own log and state, and cannot affect what it watches.
- [ ] **Prove the email channel once, then trust its silence.** `apt install
      bsd-mailx msmtp-mta` (or whatever the box has), set
      `CHESTER_ALERT_EMAIL` via `systemctl --user edit`, and run once with
      `CHESTER_ALERT_EMAIL_ALWAYS=1`. Until that is done the log will read
      `delivery=no_address`, which is honest but is not an alarm anyone
      receives.
- [ ] **Confirm the first real verdict.** The box's own `eod_heartbeat` decides
      whether the first 08:30 reads `ok` or `no_heartbeat`; the latter would be
      a real finding about the EOD timer, not about this check.
- [ ] **`systemd-analyze verify chester-heartbeat.{service,timer}`** on the box,
      folding into the existing cross-check item for the directive allowlist.
