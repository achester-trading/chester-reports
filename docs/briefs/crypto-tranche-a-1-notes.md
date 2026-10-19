# crypto-tranche-a-1: Batch 4 Tranche A, part 1 (17 Oct 2026)

**Branch and merge order.** `crypto-tranche-a-1`, session B, cut from the tip of
`6e-digital` (`aff064f`), with that branch's CI fix (`938b5e2`) merged in. It
carries the whole 6e line and **merges after `6e-metric-lenses`, `6e-rest`,
`6e-releases` and `6e-digital`, in the second stitched chain.**

**What it builds.** CD-1, CD-2 and CD-5 of the crypto data-sources order
(`docs/change-order-crypto-data-sources-2026-10-06.md`), pulled forward by Batch 8
section 6, with the S-1 and S-3 derived series. It also applies the 16 and 17 Oct
rulings (a) to (f). Config: `config/crypto_sources.yaml`.

**Rules kept.**
- Branch only: pushed, not merged, not deployed, nothing run on the box.
- Paper only, with no order path; the Brookfield blocklist is untouched.
- No secret, no key, no real position figure.
- Not touched: `.env`, the units on the box, the register, the ledgers,
  `chester-meme`, session A's branches.
- Every source was read keylessly with the project's User-Agent
  (`chester-reports/1.0`), within its robots.txt, to capture the fixtures.

## Step 0: the CI reads

| Run | Branch, commit | Result |
|---|---|---|
| 39031045828 | `docs-batch-8`, `1388967` | **green**: 84 of 84 jobs |
| 39032637251 | `6e-digital`, `aff064f` | **failed**: 85 of 87 jobs passed |

**The 6e-digital failure, and the fix.**
- `tools/validate_config_refs.py` refused three keys the addendum's config names
  before any writer exists: `calc.froth_z`, `calc.funding_agg` and `calc.oi_usd`.
  The second failed job, `gates-passed`, only rolls up that one failure.
- **The fix, `938b5e2` on `6e-digital`:** the three keys are registered as
  `status_extra: not_yet_sourced` (declared, never written), and
  `validate_audit_3a` counts them one by one.
- Locally after the fix: `validate_config_refs` 55/55, `check_registry` OK,
  `validate_lenses` 49/49, `validate_audit_3a` 83/83.
- **On this branch** the merge replaces two of the three with real entries, since
  `calc.funding_agg` and `calc.oi_usd` now have their writer. `calc.froth_z` stays
  not yet sourced until part 2 (CD-7).
- The fix's own CI run is recorded under "CI" below.

## The rulings applied

| Ruling | What changed |
|---|---|
| (a) D1c is met | The new writers run unheld. |
| (b) friction becomes a keyless alternative or a gap | Ethereum through Blockscout, keyless; ETH supply and burn listed as a gap; Bybit replaced by Deribit (below). |
| (c) no recurring by-hand data line | No by-hand line added. |
| (d) judgment drafts for accept-all | The session-set values below. |
| (e) the addendum's delivery and dates | The addendum is now **a second PDF on the Weekly's own email**, archived as `weekly_digital_<ending>.pdf` beside the HTML (if the PDF cannot be built, the HTML goes instead and the run says why). Stablecoin supply keeps printing from `llama.stable_total`, which CD-1 extends rather than duplicates. The VanEck JitoSOL date keeps its "15 Nov, to verify" marker. Deribit's month-end expiries stay computed from its rule. |
| (f) MSCI's schedule | The 30 Nov entry's marker is off; it reads "November 2026 Index Review implemented at the close of 30 Nov, effective 1 Dec". |

`tools/validate_digital_addendum.py` was extended for (e) and (f) and passes 77/77.
It drives the PDF through an injected renderer, so the gate never renders one; CI's
Weekly gates render the real one.

## The writers

Every writer is keyless and follows the publication contract: `KEYS` as a literal,
`pull(run_id)` returning OK, or STALE with nothing written. Each runs in two places:
- on `feeds.EXTERNAL_WRITERS`, in the weekday 16:10 pass, which is also the
  freshness roster;
- in `scripts/run_crypto_basket.sh`, every day at 17:25 ET, which is what covers the
  weekend, when crypto still trades.

A second run on the same weekday writes only a later vintage of the day's snapshots.

**Point in time** (`altdata/sources/_crypto.py`):
- `observed_at` is the UTC day;
- `available_at` is the pull instant, never backdated;
- history is written for complete UTC days only;
- a snapshot is filed under the pull's own UTC day.

**Funding** is the sum of the day's prints times 365, so a venue's interval never
has to be assumed. A day short of a print is not written.

### CD-1: DefiLlama (`altdata/sources/llama.py`, extended)

- **Watch names.** The order's watch names that are not crypto-basket names: BTC,
  ETH, SOL and ZEC as chains, HYPE and LINK as protocols. Each gets
  `llama.fees_<sym>` and `llama.revenue_<sym>` from `/summary/fees/{slug}`.
  - **The slug is resolved at run time, never written down.**
    - A chain is the `/overview/fees` row of `protocolType` "chain" with its name.
    - A protocol is the single parent shared by its `/protocols` rows:
      `parent#hyperliquid` and `parent#chainlink`.
    - Two candidates, or none, is a named failure for that run.
  - AAVE, TAO and PRL are basket names and are not pulled twice.
- **Watch coins.** `llama.mcap_btc` and `llama.mcap_eth`, with their supply, are
  S-3's denominator. They are forward-only, like the basket's caps.
- **Stablecoin supply:** the series already stored (`llama.stable_total`,
  `llama.stable_by_chain`) is extended, not restarted. S-1's share by chain is
  derived from it.
- **`/raises`:** re-probed 17 Oct 2026; it answers **402 "Upgrade to the paid API
  plan"**. A listed gap.
- **Fixtures** (`tests/fixtures/llama/`):
  - `protocols_watch.json` and `fees_overview_chains.json`, trimmed from the real
    responses;
  - `fees_watch_hyperliquid.json` and `fees_watch_ethereum.json`.

### CD-2: the perp venues

**Hyperliquid** (`altdata/sources/hl.py`), `POST api.hyperliquid.xyz/info`. The host
has no robots.txt (404: no rules).
- `hl.funding` (BTC and ETH): fundingHistory's hourly prints, history from 12 May
  2023.
- `hl.oi`: metaAndAssetCtxs' `openInterest` × `markPx`, a snapshot. **Forward-only:**
  Hyperliquid serves no OI history.
- **The weight limit, verified** in Hyperliquid's documentation ("Rate limits and
  user limits", read 17 Oct 2026):
  - 1,200 per minute per IP across REST requests;
  - `metaAndAssetCtxs` and `fundingHistory` weigh 20;
  - `fundingHistory` adds 1 per 20 items returned, at most 500 per call.
- **The guard** charges each request its worst case before sending it (45 for a
  funding page) and spends at most **600 a minute**, half the limit. A request that
  would overrun waits for the window, or with no wait allowed is **refused and never
  sent**.

**OKX and Deribit** (`altdata/sources/fut.py`).
- `fut.funding_okx`: about three months of history served, eight-hourly
  `realizedRate`.
- `fut.oi_okx`:
  - history from `rubik/stat/contracts/open-interest-history`, a year;
  - OKX's day is stamped 16:00 UTC and filed under that UTC date;
  - today's value from `public/open-interest` `oiUsd`.
- `fut.ls_account_okx`: the account long/short ratio, about 180 days served. It is
  stored and never read as a direction call.
- `fut.funding_deribit`: hourly `interest_1h`, history from 2019, 30 days per call.
- `fut.oi_deribit`: an inverse perpetual's `open_interest`, in USD; a snapshot,
  forward-only.
- Robots: OKX's robots.txt disallows nothing under `/api/v5/`; Deribit publishes
  none.

**Bybit: geo-blocked, switched off.** On 17 Oct 2026 `api.bybit.com` answered the
laptop with 403: "The Amazon CloudFront distribution is configured to block access
from your country".
- That is the condition D-2 dropped Binance for: a leg that runs only on the box and
  cannot be tested from the laptop.
- Under rule (b) the third venue is **Deribit's perpetuals**, keyless, reachable
  from both machines, and already an adopted source (DS-41).
- Bybit's reader is built and tested on fixtures in **its documented response
  shape**, labelled as such in `tests/fixtures/fut/README.md`, not captured.
- It is off in config, and its three keys are not registered while it is off.

**The other fixtures** (`tests/fixtures/hl/`, `tests/fixtures/fut/`) are the real
responses, captured 17 Oct 2026.

### CD-5: network state and sentiment

**mempool.space** (`altdata/sources/mempool.py`). `/robots.txt` returns the site's app
page, so no rules apply.
- `mempool.hashrate`: by day, from `/v1/mining/hashrate/3m`; the backfill uses `/all`,
  from 3 Jan 2009, in one call.
- `mempool.difficulty`: at each adjustment.
- `mempool.difficulty_change_est`: the next adjustment's estimate.
- `mempool.fee_rate`: five tiers.
- `mempool.mempool_vsize`.
- `mempool.tip_height`.
- `mempool.pool_share`: the top ten pools, last week.

**alternative.me** (`altdata/sources/fng.py`). `fng.value`, the full history from
1 Feb 2018 in one call, so every pull is its own backfill.

**The Ethereum decision under rule (b)** (`altdata/sources/blockscout.py`).
- Etherscan needs `ETHERSCAN_API_KEY`, a registration Ari has not made.
- The keyless path within robots is **Blockscout's Ethereum explorer**,
  `eth.blockscout.com/api/v2`, whose robots.txt says Allow /. It serves:
  - `blockscout.gas_gwei`: slow, average, fast;
  - `blockscout.utilization`: % of block gas used;
  - `blockscout.tx_count`: daily, 30 days served.
- **ETH supply, staked and burnt (Etherscan's `ethsupply2`) has no keyless source
  here: a listed gap, under the key's name `ETHERSCAN_API_KEY`.** The design does not
  route around the key.
- Blockscout's price and market cap are CoinGecko's, and are not stored.

**CoinGecko `/global` is not built.** The paste places it on "the ST-13 fetcher",
but:
- **no ST-13 CoinGecko fetcher exists on any branch**;
- on 13 Oct 2026 CoinGecko's terms were ruled out for this store: they discourage
  storage and provide no keyless plan (`altdata/loggers/shielded.py`,
  `docs/briefs/crypto-basket-notes.md`).

So total market cap and BTC dominance stay "not sourced", as `shielded.py` already
records. This is on the needs-you list.

### The derived series (`altdata/sources/crypto_derived.py`)

A writer that reads the store and fetches nothing. On the roster it sits after the
venues, and the llama pull also runs it.

| Key | What |
|---|---|
| `calc.stable_share` | S-1: a chain's share of stablecoin supply (Ethereum, Tron, Solana, Base), full history from the stored series. S-1's impulses (`calc.stable_impulse_30d/_90d`) stay the crypto basket's. |
| `calc.funding_agg` | S-3: OI-weighted funding, annualised, **at least two venues** carrying both funding and OI that day. |
| `calc.oi_usd` | S-3: total OI across **every** enabled venue; a day missing one is not written. Instrument NULL is BTC + ETH. |
| `calc.oi_mcap` | S-3: OI over the coin's market cap, %. |
| `calc.funding_agg_z`, `calc.oi_mcap_z` | 90-day z-scores, 60 observations needed. |

**The aggregate starts with the first pull.**
- Funding history is backfilled at every venue.
- But only OKX serves OI history, and an OI weight taken from another day would not
  be point in time.
- So `calc.funding_agg` and `calc.oi_usd` begin on the first day two venues (or, for
  the total, all three) carry OI, and the z-scores mature about 60 days later.

The S-3 flag (funding z > +2 with OI over market cap at a 90-day high) waits for its
gate, as the order rules.

## Registry, roster, catalogue, families

- **24 new keys** registered individually, each with family, long window and a unit
  from the vocabulary:
  - funding: `percent_rate`, family rate;
  - OI: `usd`, family quantity;
  - long/short: `ratio`;
  - shares: `percent_share`;
  - fear and greed: `index_points`, family conditions.
- **A new bulk block,** `llama_watch_daily`, with 12 members.
- **The caps' and supply blocks** grow from 12 to 14 members (BTC and ETH).
- **Two new mechanism groups:** `crypto_leverage` and `crypto_network`.
- **Five new sources:** `hyperliquid`, `perp_venues`, `mempool_space`,
  `alternative_me`, `blockscout`.
- **Six catalogue lines.**
- **The family report**, `docs/briefs/6e-family-assignments.md`, is regenerated:
  2,757 keys and 289 ambiguous. The two new ambiguous ones are BTC's and ETH's caps,
  flagged "quantity, alternative: price" the way the basket's are.

## Session-set values (for Ari's accept-all)

| Value | Set at | Reason |
|---|---|---|
| Hyperliquid budget | 600 a minute (the limit is 1,200) | room for a by-hand backfill beside the daily pull |
| Two venues for the aggregate | `min_venues: 2` | the order rejects a single-venue reading |
| Total OI | all enabled venues on the day | a total must not shrink because a venue was down |
| z window | 90 days, 60 observations | the order's 90 days; two thirds before a z prints |
| OI over market cap | the cap on the day or within the three before | the coin service is forward-only and daily |
| Backfill bounds | Hyperliquid funding from 12 May 2023; OKX OI 365 days, funding 92; Deribit funding from 2019-01-01; at most 200 pages a series | what each venue serves, capped |
| The daily window | 14 days | catches a missed weekend; an empty key's first pull writes all of it |
| Bybit | off | geo-blocked (above) |

## Box commands, for Ari (printed, not run; inside a window)

Run them after the second chain merges, on weekdays 09:05-15:40 or 17:20-23:30 ET, or
on a weekend clear of Sunday 05:00. Nothing here needs a key. The first timer run
writes each series' daily window on its own; these backfill the depth.

```
cd ~/chester-reports
# 1. Dry runs first (fetch and parse, write nothing), about a minute each.
.venv/bin/python -m altdata.sources.hl backfill --dry-run       # ~9-10 min: ~120 funding pages at 45 weight, paced at 600/min
.venv/bin/python -m altdata.sources.fut backfill --dry-run      # ~3-5 min: Deribit from 2019 in 30-day calls, OKX a year
.venv/bin/python -m altdata.sources.mempool backfill --dry-run  # seconds: /hashrate/all once
# 2. The backfills (point in time: today's instant as available_at).
.venv/bin/python -m altdata.sources.hl backfill                 # ~10 min
.venv/bin/python -m altdata.sources.fut backfill                # ~5 min
.venv/bin/python -m altdata.sources.mempool backfill            # seconds
# 3. The first daily pulls (the 17:25 timer does this from then on).
.venv/bin/python -m altdata.sources.llama pull --only watch     # ~1 min: 2 resolution calls, 12 series
.venv/bin/python -m altdata.sources.llama pull --only coins     # seconds: adds BTC's and ETH's caps
.venv/bin/python -m altdata.sources.fng                         # seconds: the whole history
.venv/bin/python -m altdata.sources.blockscout                  # seconds
.venv/bin/python -m altdata.sources.crypto_derived              # seconds: S-1 share and S-3 from the store
# 4. Read-only checks.
.venv/bin/python -m altdata.sources.llama resolve
.venv/bin/python -m altdata.catalogue show calc.funding_agg
```

## Gates

| Gate | Result |
|---|---|
| `tools/validate_crypto_sources.py` (new; groups A-H) | **60/60** locally |
| `tools/validate_digital_addendum.py` (rulings (e), (f); per-coin funding cells) | 77/77 locally |
| `tools/validate_official_sources.py` (every writer STALE-not-empty offline; the no-unit-per-writer check matches whole names, since `hl` sat inside "monthly") | 287/287 locally |
| `tools/validate_audit_3a.py` (the new keys one by one; the llama blocks) | 83/83 locally |
| `tools/validate_crypto_basket.py` (llama extended) | 93/93 locally |
| `tools/validate_config_refs.py`, `tools/validate_lenses.py`, `tools/check_registry.py` | 56/56, 49/49, OK |
| everything else, and anything that renders a PDF | CI |

**What `validate_crypto_sources` holds:**
- **A:** a parser per endpoint, each on the stored real response, against figures
  computed by hand from the fixture.
- **B:** S-1 and S-3 against hand computations, including the two-venue rule and the
  all-venues total.
- **C:** the weight guard refuses a burst, and the refused request is never sent.
- **D:** OKX failing leaves Deribit's rows standing; every venue failing is STALE and
  writes nothing.
- **E:** the backfills are bounded by start date and page cap, and point in time.
- **F:** no series is stored twice with the crypto basket.
- **G:** registry, roster, catalogue, the gaps named, and no writer reads a key.
- **H:** the watch slugs are resolved at run time, and an ambiguous name is refused.

No gate opens a connection.

## Files shared with open branches

**Session A** (`6b-dealer-1`, its own commits above `st-r5-audit`):
- `CLAUDE.md`: the gate-count sentence, which becomes eighty here.
- `Makefile`: the gate list's tail.
- `metrics_registry.yaml`: additions on both sides; expect adjacency conflicts only.

Through the chains `6b-dealer-1` and `alpha-lab-2` stand on, these also overlap:
- `altdata/feeds.py`: the `EXTERNAL_WRITERS` tuple's tail;
- `config/catalogue_commands.yaml`;
- `source_registry.yaml`;
- `tools/validate_audit_3a.py`;
- `tools/validate_official_sources.py`.

All of them are additions; at a conflict, keep both sides.

**`post-friday-fixes`:** `metrics_registry.yaml` only.

**The 6e line:** `daily_cascade/digital_addendum.py`, `config/digital_addendum.yaml`
and `config/digital_asset_calendar.yaml` are 6e-digital's own files, changed here for
rulings (e) and (f).

## What part 2 takes next

From the order and Batch 8 section 6:
- **CD-3** `deribit.py`: DVOL and S-4.
- **CD-4** `farside.py`: ETF flows and S-2.
- **CD-7** `gt.py`: the froth gauge, S-5 and `calc.froth_z`.
- **CD-8**: the remaining `calc.*` and the Factor V rows.
- **CD-9**: the Weekly and Monthly parts.
- **CD-10**: the validators.
- **Item 51's Phase 2 panels**, which wire this part's series into the addendum (fear
  and greed, the network state, per-venue funding).
- **Item 49's mNAV (49a) and treasury-company purchases (49b).**

Part 2 should also wire `fng.value`, `mempool.*` and `blockscout.*` into the
addendum's sections 2 and 5. This part stores them and does not print them, beyond
the funding and OI cells already wired.

## Needs you

1. **CoinGecko `/global`.** No ST-13 fetcher exists, and the 13 Oct ruling bars
   storing CoinGecko's data. Should total market cap and BTC dominance stay "not
   sourced", or do you revisit the terms ruling for a Demo-key fetcher?
2. **Bybit.** It is geo-blocked from the US, and Deribit's perpetuals are the third
   venue in its place. Accept Deribit, or run Bybit on the box only? Box-only is what
   D-2 rejected for Binance; if you choose it, the switch is one config line plus
   registering its three keys.
3. **ETH supply and burn.** This is a gap until `ETHERSCAN_API_KEY` exists in `.env`.
   It is your registration to make, or to leave as a gap.
4. **`/raises`** is paid (402). It stays a gap; the VC-raises cycle gauge has no free
   source.
5. **The session-set values above,** above all the 600-a-minute budget and the
   two-venue rule.
6. **S-3 matures slowly.** The aggregate starts at the first common OI day, and its
   z-scores need about 60 days, so the leverage flag's gate cannot run before
   mid-December.

## CI

This branch's push and the `6e-digital` fix (`938b5e2`) are each read once and
recorded here.

| Run | Branch, commit | Result |
|---|---|---|
| 39034690356 (Gates, push) | `6e-digital`, `938b5e2` (the fix) | green: 87 of 87 jobs |
| 39034892068 (Gates, push) | `crypto-tranche-a-1`, `d2da8ad` | green: 88 of 88 jobs |

Read 17 Oct 2026. Ari's rulings of 17 Oct on this report are applied on
`crypto-tranche-a-2`:
- Bybit stays out, with its reader switched off by config and no call path.
- `/global` stays unbuilt; total market cap and dominance come from a keyless source or are a listed gap.
- ETH supply and burn stay a gap.
- The session-set values stand.
- The z-score levels print from mid-December.
