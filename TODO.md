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

- [ ] **DECIDE: denominate the gate's gamma check by gross |GEX|.** The
      diagnosis above is complete; this is the remaining action. Note what it
      does and does not claim. It does NOT say the solver reproduces net dealer
      gamma to 10% -- on SPY the net differs by 402M on a -1.45bn base and that
      is real. It says the two IV sources agree to ~2% of the gamma actually
      in the book, and that the net is too small a residual to divide by. If
      the net is what a downstream consumer acts on, its uncertainty must be
      reported in absolute terms alongside, not hidden by a friendlier ratio.
      Keep the twinning finding regardless: 43-49% of every comparison is
      propagated vol carrying a 5-8x wider tail, which is worth a separate
      quality flag even once the denominator is fixed.

- [ ] **RESOLVED 5 Sep: Tuesday's pin verdicts are NOT readable as they
      stand. The 7/13 peak-GEX hit rate is an artifact of the MIN_T floor.**

          peak-GEX pins within 25bps, all rows        : 7/13
          peak-GEX pins within 25bps, ex-floored rows : 0/13
          peak strike MOVED when floored rows removed : 9/13

      Every hit sits within 16bps of spot and most within 1bp -- AAPL 320.00
      vs 319.97, IWM 296.00 vs 295.97, QQQ 719.00 vs 718.96, MSFT 500.00 vs
      499.70. That is not a pin, it is the nearest listed strike to spot.
      0DTE gamma scales as 1/sqrt(T) and peaks at the money, so a floored 0DTE
      row plants the peak-GEX strike AT the money by construction, and the pin
      test then asks whether the strike nearest spot is near spot. It is
      tautological, and it will read as a 54% hit rate forever.

      Floored share of |GEX| is large enough to dominate on most names:
      AAPL 87.0%, NVDA 54.1%, META 28.7%, MSTR 28.6%, MSFT 19.4%, ASTS 19.6%,
      QQQ 17.9%, IWM 13.2%. SPY is the exception at 1.0%, and SPY is one of
      the four whose peak strike did NOT move.

      Do not read Tuesday's pin column until the 0DTE-in-EOD question below is
      settled. Both candidate answers fix this: excluding settled contracts
      removes the floored rows outright, and a defensible MIN_T stops the
      1/sqrt(T) blowup from dominating.

- [ ] **0DTE IV is unsolvable at the close, on every symbol.** Coverage across
      all 13 on 2026-09-04: 0.0%-2.4%, with 60-70% rejected `wide_spread`. At
      16:09 ET the day's contracts are at or past expiry and a penny-wide
      market on a two-cent option is a 100% relative spread. So neither IV
      source is verifiable for 0DTE, and the 6 rows that DO solve dominate the
      bucket -- they carry -5.2bn of the -5.235bn solved 0DTE gamma, against
      +196M for the other 376 on yfinance IV. **The deeper question this
      raises: at a post-close snapshot the 0DTE contracts have already settled,
      so their true remaining gamma is zero and the MIN_T floor is inventing
      it. Decide whether 0DTE belongs in an EOD profile at all.**
- [ ] **The two snapshot qualities pull in opposite directions.** The 16:10
      capture is right for OI and 0DTE completeness; the 22:44 capture had
      cleaner quotes (gate read -4.55% there, ex-0DTE 23.1% here). Worth
      measuring whether a late-evening capture should feed the IV solver while
      the close capture feeds OI.
- [ ] **Charm in 0DTE is an extrapolation, not a measurement.** Charm scales as
      1/sqrt(T) and diverges as T -> 0, so 0DTE carries the largest per-day
      charm in the book. NVDA 2026-09-04: 0DTE charm +20.4M sh/day against a
      whole-symbol total of +19.3M — the bucket flips the symbol's sign, on 108
      rows resting on the MIN_T floor. `chex_floored_rows` is carried per
      symbol and per bucket so this is checkable. Decide whether the headline
      CHEX should exclude 0DTE. (Vanna needs no such treatment: it genuinely
      collapses to ~0 in 0DTE, SPY 0.7% of book vanna.)
- [ ] **DEX direction is uninformative under `dealers-hand-v1`** and will stay
      that way. Long calls carry positive delta and SHORT puts also carry
      positive delta, so net DEX is positive for every symbol, bucket and
      expiry — 269 of 269 rows on the first backfill, with no negative possible
      in principle. Magnitude, dating and day-over-day change are the signal;
      `unwind_direction` only becomes a real variable if Alpha-tier flow
      polarity ever replaces the assumed +1/-1.

### Fixed in passing, but it revises committed history

`newest_chains` selected the day's chain by file **mtime**. For 2026-09-04 that
picked the 22:44 ET capture, taken hours after the close, by which time all 425
0DTE contracts had expired off the chain — so the whole 0DTE bucket was silently
absent and nothing downstream could tell, because a missing bucket and an empty
one look identical. Selection now ranks by the `fetched_at` the rows carry,
nearest `config.EOD_SNAPSHOT_TARGET_ET` (16:10, matching the timer). This moves
every 2026-09-04 number: SPY $gamma/1% -988M -> -1,172M, NVDA 1.67bn -> 4.15bn,
QQQ -339M -> -3.26bn. Earlier rows in the pin log were computed the old way.

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
