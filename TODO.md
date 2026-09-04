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
- [ ] `pin_log` lacks `expiry_type` per row. Doc requires the pin rate segmented
      by expiry type; bucket *shares* are stored but the row itself is not typed,
      so the segmentation cannot be run.
- [ ] Store **share gamma per 1% move** alongside dollar gamma. Doc: "shares and
      dollars per 1% move — store that, and treat raw notional as derived." We
      store dollars + raw notional only.
- [ ] Re-running a past date rewrites its row at the *current* tolerance. Doc:
      tolerance "declared in advance and never revised after the fact." Rows do
      carry their own `tolerance_bps`, so make a backfill refuse to change it.
- [ ] Label the pin read a **conditioner** until effective-n is meaningful.
      Nothing in the output says the sample is too small to act on yet.

Data-quality gates (none of these exist yet)
- [ ] **Liquidity floor** — hard rule: exclude thin books from skew/OI-percentile
      work. Doc prefers bid/ask tightness over an OI threshold; we already store
      `bid`/`ask` per contract, so this is computable from stored chains.
- [ ] **IV dispersion / surface roughness** as a data-quality gate, not an
      analytic — high roughness downgrades confidence in everything derived that
      day. Doc: "Nothing else in the system catches a bad options day."
- [ ] **OI concentration (Herfindahl)** — strike-level twin of expiry-bucket
      concentration; signals discontinuous rather than decaying regime change.
- [ ] **OI-weighted DTE** — single number for short- vs long-dated positioning.

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
- [ ] Raw chains live only on this Windows box, gitignored. Part 25 rules the VPS
      the primary runtime with outputs on the box, so gitignoring is right — but
      the data is the one asset that cannot be recovered, and it currently has no
      backup and no VPS home. Migrate + back up before the sample has real value.
- [ ] SPX absent (yfinance has no index options). Blocks the doc's Session −1
      universe of SPX/SPY/QQQ/IWM. Pending the Part B vendor decision.
