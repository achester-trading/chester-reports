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

- [ ] **0DTE gamma is numerically unstable, and the IV-solver gate now FAILS
      because of it.** `tools/validate_iv_solver.py` reports SPY dollar
      gamma/1% diverging -436% between yfinance IV and solved IV. All of it is
      the 0DTE bucket: +196M on yfinance IV vs -5,235M on solved IV, while
      every other bucket agrees within 15%. Two compounding causes:
      only 6 of 382 0DTE rows solve at all, and with T floored at MIN_T (1
      hour) a single near-ATM contract carries ~$377M of gamma, so the bucket
      is dominated by sigma rather than by positioning.
      The gate was passing before only because the chain it was reading had no
      0DTE contracts in it (see the snapshot bug below) — it was being
      evaluated on the easy subset. **Decide: raise MIN_T to something
      defensible, or exclude 0DTE from the solver comparison explicitly and
      say so in the gate.** Do not loosen the thresholds; that buries it.
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
