# crypto-tranche-a-2: Batch 4 Tranche A, part 2 (17 Oct 2026)

**Branch and merge order.** `crypto-tranche-a-2`, session B, cut from the tip of
`crypto-tranche-a-1` (`5eb1456`, its CI read recorded). It carries part 1 and the 6e
line and **merges after `crypto-tranche-a-1`, in the second stitched chain**.

**What it builds.** CD-3, CD-4, CD-7, CD-8, the Weekly and Monthly parts of CD-9,
and CD-10 of `docs/change-order-crypto-data-sources-2026-10-06.md`. It also applies
Ari's rulings 1 to 5 of 17 Oct on the part 1 report. Config:
`config/crypto_sources.yaml`.

**Rules kept.**
- Branch only: pushed, not merged, not deployed, nothing on the box.
- Paper only, with no order path; the Brookfield blocklist is untouched.
- No key, no secret, no real position figure.
- Not touched: `.env`, the units on the box, the register, the trade ledgers,
  `chester-meme`, session A's branches.
- Every source was probed keylessly within robots.txt, with the project's
  User-Agent.

## Step 0: the CI reads

| Run | Branch, commit | Result |
|---|---|---|
| 39034892068 | `crypto-tranche-a-1`, `d2da8ad` | green: 88 of 88 jobs |
| 39034690356 | `6e-digital`, `938b5e2` (the fix) | green: 87 of 87 jobs |

Both are recorded in the part 1 notes (`5eb1456`). Nothing failed.

## The rulings applied

| Ruling | What changed |
|---|---|
| 1 Bybit stays out | Bybit is removed from `fut.VENUES`: its reader stays in the tree with **no call path**, and a config flipped to enabled still calls nothing. Deribit's perpetuals stay the third venue. |
| 2 `/global` | Not built on CoinGecko. **CoinPaprika's `/v1/global` reads keyless within robots** (`api.coinpaprika.com` has no robots.txt), so `paprika.total_mcap_usd` and `paprika.btc_dominance` are stored (forward-only), and the Weekly's dominance line prints them. Needs-you item 1 has the terms point. |
| 3 ETH supply and burn | Still a gap. Blockscout's Etherscan-compatible `ethsupply` answers keylessly but reports about 176M ETH against the roughly 120M outstanding, and its `ethsupplyexchange` figure is a price provider's. So no keyless source within robots serves a figure I would store. The Monthly prints the gap line, naming `ETHERSCAN_API_KEY`. |
| 4 the session-set values | Unchanged: the 600-a-minute Hyperliquid budget, the OI weighting, the backfill bounds. |
| 5 the z-score levels | Print from 15 Dec 2026. Until then the Weekly's funding lines print the level and "z-score from 15 Dec 2026". |

`calc.funding_agg_z` from part 1 is renamed **`calc.leverage_z`**, the order's name.
Nothing was ever stored under the old key, since part 1 isn't merged.

## The writers

Every writer is keyless, point in time (available_at is the pull instant; history
covers complete UTC days only) and STALE-not-empty. Each is on
`feeds.EXTERNAL_WRITERS` (the weekday 16:10 pass and the freshness roster) and in
`scripts/run_crypto_basket.sh` (17:25 ET, every day).

### CD-3: Deribit DVOL (`altdata/sources/deribit.py`)

- **Endpoint.** `public/get_volatility_index_data`, resolution 1D. No key;
  `www.deribit.com` has no robots.txt.
- **Series.** `deribit.dvol_btc` and `deribit.dvol_eth`: each day's candle close.
  History starts **24 Mar 2021**, the index's first print, probed 17 Oct.
- **Backfill.** Bounded: from that date, in windows of at most 900 days.
- **Strike-level OI** is not fetched; under D-4 it belongs to EL-12.
- **Fixtures:** `tests/fixtures/deribit/dvol_btc.json` and `dvol_eth.json`, the real
  responses (40 days).

### CD-4: Farside (`altdata/sources/farside.py`)

- **Pages.** `/btc/` and `/eth/`, read with `pandas.read_html`, with the browser
  user-agent the order asks for. It still names the project.
- **Robots.** `robots.txt` names only Twitterbot, so no rule covers this agent.
- **The refusal.** On 17 Oct the site answered the laptop **403 through Cloudflare**,
  to both user-agents. As the paste rules, the writer is built and the gap is listed;
  nothing is scraped around the refusal (no proxy, no archive copy, no headless
  browser). Whether the box gets through is the first box command's question.
- **Series.** `farside.btc_total`, `farside.eth_total`, and per issuer
  `farside.btc_issuer` and `farside.eth_issuer`, with the instrument as the ticker.
  All are stored in dollars (the page's US$ millions × 1e6).
- **Parsing.** "(x)" is negative. "-" is no figure, never a zero. The fee row and
  the summary rows are dropped.
- **The column-change detector.** The issuer columns must equal config's list
  exactly. A changed table is refused whole, with the change named.
- **STALE.** The run says STALE with the last good date and writes nothing.
- **When it runs.** The 17:25 daily crypto run, after the US close. It also has a
  step in the 06:45 `scripts/fetch_overnight.sh`, outside the early pass, which two
  gates pin, for the **T-1 figure**.
- **Backfill.** The all-data pages from **11 Jan 2024**. The slugs come from config
  and could not be verified against the live links, since the site refused.
- **Fixtures** (`tests/fixtures/farside/`) are **NOT captured**. They follow the
  page's published shape, and `README.md` says so. The issuer column lists are from
  the published shape and **must be checked on the box's dry run**: the detector
  names any difference.

### CD-7: the froth gauge (`altdata/sources/gt.py`)

- **GeckoTerminal is refused by robots.** `api.geckoterminal.com/robots.txt` reads
  `User-Agent: * / Allow: /docs/ / Disallow: /`, read 17 Oct.
  - The writer reads robots first and **makes no API call while it refuses**. The
    day GeckoTerminal opens the path, the writer starts.
  - Its parsers are tested on the response shape GeckoTerminal documents in its own
    swagger spec, read from `/docs/`, which robots allows.
- **The guard.** GeckoTerminal's published limit is 30 a minute; the guard spends at
  most 20 and refuses a burst.
- **The fallback** (the order's DexScreener, only when GeckoTerminal fails):
  - `api.dexscreener.com/latest/dex/search?q=<network>`, which has no robots.txt;
  - it writes trending volume only, with the row's source `dexscreener:fallback`;
  - a search is not a census, so it **never enters the z-score**.
- **Series.** `gt.new_pools_24h` and `gt.trending_vol_24h`, instrument `solana` or
  `base`. They are sampled from the first deploy, and no backfill exists.
- **S-5's z-scores** need 90 days of GeckoTerminal store. That is mid-January 2027
  at the earliest, and **only once robots admits the API**. Until then the Weekly's
  froth line prints unscored, and says it has no sample.
- **Fixtures** (`tests/fixtures/gt/`): `swagger.json` (real); `new_pools_p*.json`
  and `trending_pools.json`, built from the spec's example pool; and
  `dexscreener_search_solana.json`, the real response.

### Ruling 2: CoinPaprika (`altdata/sources/paprika.py`)

`paprika.total_mcap_usd` and `paprika.btc_dominance`, from `/v1/global`: snapshots,
forward-only. Fixture: `tests/fixtures/paprika/global.json` (real).

## CD-8: the derived series (`altdata/sources/crypto_derived.py`)

| Series | Definition |
|---|---|
| S-1 | `calc.stable_impulse_30d/_90d` (the crypto basket's, unchanged) and `calc.stable_share` (part 1) |
| S-2 | `calc.etf_streak`: signed consecutive same-sign sessions. `calc.etf_5d_pct`: the five-session sum's percentile against every stored sum, from 20 sums. |
| S-3 | `calc.funding_agg`, `calc.oi_usd`, `calc.oi_mcap`, `calc.leverage_z`, `calc.oi_mcap_z` (part 1's, renamed) |
| S-4 | `calc.dvol_pct_5y` and `calc.dvol_pct_full` (60 days needed); `calc.dvol_minus_rv30`, with realised volatility from the **stored** `yfinance.mkt_btc_usd/eth_usd` closes, never a second price series. The band (compressed ≤ 20th, stressed ≥ 80th on the full-history percentile) is a lens, printed. |
| S-5 | `calc.froth_z` per network and measure, on a 20-day window after 90 days of GeckoTerminal store |

**The flags** are computed and stored, **gate status "not passed", never rendered**:
- `calc.flag_etf_extreme`: the five-session sum at or below the 5th or at or above
  the 95th percentile;
- `calc.flag_leverage_crowded`: leverage z above +2 with OI over market cap at its
  90-day high;
- `calc.flag_froth`: both of a network's froth measures at z ≥ +2.

**SR-20's amendment** (the S-1 stablecoin rows) is drafted in
`docs/signal-triage-register.md` under SR-20, for your accept-all. SR-29 is
untouched.

## CD-9: the blocks (`altdata/crypto_blocks.py`)

**The Weekly** (`daily_cascade/weekly_stack.py`). A "Crypto flows" table in
Positioning & flows, **12 lines**, each with its data-as-of:
1. stablecoin supply, 7 and 30 days;
2. BTC ETF flows, the week and the streak;
3. ETH ETF flows, the week and the streak;
4. BTC aggregate funding, the week's change;
5. ETH aggregate funding, the week's change;
6. total OI, the week's change;
7. BTC DVOL and its band;
8. ETH DVOL and its band;
9. hashrate and the last difficulty adjustment;
10. the fee tier;
11. the froth line, unscored;
12. total cap and dominance.

The order places it beside the Mechanism Watch block, but that block (MW-10) isn't
built, so it stands alone in the section. A stale Farside table prints "STALE: last
good <date>".

**The Monthly** (`monthly_macro/stack.py`, at the monthly cadence only; the
Quarterly is unchanged):
- **Mechanics** gains "Crypto network health": hashrate, difficulty, fee, gas,
  transactions and utilisation, plus the ETH supply-and-burn gap line and the SR-29
  row as it prints today.
- **The slow layers** gain four tables after the digital family:
  - "Factor V: stablecoins" (SR-20, S-1);
  - "Watch names: what pays the token": 30-day fee and revenue sums, the change and
    the percentiles;
  - "VC raises": "Not available: the endpoint is paywalled";
  - "Token unlocks, next 90 days": it reads the Security Master's `unlock_schedule`
    field when the Security Master lands, and prints "No schedules entered" until
    then. This is reference data, not a recurring by-hand line.
- Every row is in the triple form with dual percentiles (five years, full history)
  and their n.

**What they displace: nothing.** Both blocks are tables with no paragraph and no
chart. The Weekly's 3,500-word budget and the Monthly's 10,000 count claims and
paragraphs only; the chart caps (10 and 12) are untouched. The daily paragraph and
the 12:30 line are Tranche B, not wired.

## CD-10: the validators (`tools/validate_crypto_sources.py`, extended to 98 checks)

- **Parsers:** one per new endpoint, each on its fixture, against a hand
  computation.
- **The Farside detector** refuses a changed header.
- **The STALE render** prints STALE with its last good date.
- **The GeckoTerminal guard** refuses a burst; robots stops the writer before any
  call; **the DexScreener fallback marks its row**.
- **S-2, S-4 and S-5** against hand figures.
- **No flag prints:** a fixture store with every flag true renders no flag word.
- **Isolation and bounds:** a failing coin or table doesn't stop the others; the
  DVOL backfill is bounded.
- **Point in time:** available_at on every row; backfills carry the pull instant.
- **Ruling 1:** Bybit has no call path.
- **The grep gate:** no report or renderer imports a crypto writer, and the blocks
  fetch nothing and read no flag key. No intraday grep gate existed, so this is it.

**Locally:**

| Gate | Result |
|---|---|
| `validate_crypto_sources` | 98/98 |
| `validate_digital_addendum` | 77/77 |
| `validate_official_sources` | 295/295 |
| `validate_audit_3a` | 83/83 |
| `validate_crypto_basket` | 93/93 |
| `validate_feeds_scheduled` | 19/19 |
| `validate_config_refs` | 56/56 |
| `validate_lenses` | 49/49 |
| `check_registry` | OK |
| `check_library` | 0 failures |

The Weekly and Monthly stack gates render PDFs, so they're left to CI.

## Registry and roster

- **20 new individual keys**, all with family, long_window and a vocabulary unit.
- **`calc.froth_z`** goes from not yet sourced to written, and part 1's z-score is
  renamed `calc.leverage_z`.
- **Five new sources:** `deribit`, `farside`, `geckoterminal` (status `built`: robots
  refuses it), `dexscreener`, `coinpaprika`.
- **Four catalogue lines.**
- **The family report** is regenerated: 2,770 keys, still 289 ambiguous.
- **The `CLAUDE.md` gate count** is unchanged at eighty, since no new gate file was
  added.

## Box commands, for Ari (after Thursday's merge, inside a window; printed, not run)

```
cd ~/chester-reports
# Dry runs first: they fetch and parse, and write nothing.
.venv/bin/python -m altdata.sources.deribit backfill --dry-run    # ~10 s: 2 windows per coin
.venv/bin/python -m altdata.sources.farside backfill --dry-run    # ~10 s, IF the box gets past Cloudflare;
                                                                  # a 403 or a changed header prints here
.venv/bin/python -m altdata.sources.gt                            # seconds: robots refuses GeckoTerminal ->
                                                                  # writes DexScreener fallback rows only
# The backfills (point in time):
.venv/bin/python -m altdata.sources.deribit backfill              # ~10 s
.venv/bin/python -m altdata.sources.farside backfill              # ~10 s if reachable
# Part 1's, beside them:
.venv/bin/python -m altdata.sources.hl backfill                   # ~10 min (600 weight a minute)
.venv/bin/python -m altdata.sources.fut backfill                  # ~5 min
.venv/bin/python -m altdata.sources.mempool backfill              # seconds
# The first samples and the derived pass:
.venv/bin/python -m altdata.sources.paprika                       # seconds
.venv/bin/python -m altdata.sources.crypto_derived                # ~30 s: S-1 to S-5 from the store
```

## Files shared with open branches

**Session A** (`6b-dealer-2`, `vol-event-52`, `6b-dealer-3`, and the chain they stand
on). Every overlap is an addition; at a conflict, keep both sides.
- **The gate count line in `CLAUDE.md`:** not changed here. One new paragraph sits
  after part 1's.
- **The `Makefile` gate list:** not changed here.
- **`metrics_registry.yaml`:** additions before `bulk_imports`.
- **The Weekly's builder,** `daily_cascade/weekly_stack.py`: one insertion before
  `em_week`.
- **The Monthly's builder,** `monthly_macro/stack.py`: one insertion after
  `slow_layers`.
- **`altdata/feeds.py`:** the `EXTERNAL_WRITERS` tail.
- **`scripts/fetch_overnight.sh`:** a step after the loggers.
- **`scripts/run_crypto_basket.sh`.**
- **`source_registry.yaml`, `config/catalogue_commands.yaml`,
  `tools/validate_audit_3a.py`.**
- **`docs/signal-triage-register.md`:** one block under SR-20.

**The 6e line:** `config/digital_addendum.yaml` (Farside's unit is now `usd`) and
`tools/validate_digital_addendum.py`.

## What the next paste takes

- **Item 51's Phase 2 panels (ST-R6.51b).** They wire these series into the
  addendum by key name.
- **Item 49a,** the mNAV series.
- **Item 49b,** treasury net purchases.

## Needs you

1. **CoinPaprika's terms.** The free plan is keyless, personal and non-commercial,
   and requires "Powered by Coinpaprika" attribution (the Weekly block's note carries
   it). It allows no redistribution and has no storage clause. But
   `altdata/loggers/shielded.py`'s note of 13 Oct lists CoinPaprika among sources
   "whose terms do not permit stored vintages". I read the API terms on 17 Oct and
   found no such clause. Confirm the series may be stored, or I take it out.
2. **Farside refuses the laptop (403, Cloudflare).** The box's dry run will show
   whether the box gets through. If it doesn't, S-2 stays empty and the ETF lines
   print "not stored".
3. **GeckoTerminal's robots.txt disallows its API.** S-5 cannot accrue history
   within robots. Either you rule the documented public API usable despite robots
   (a reversal of the standing rule), or the froth gauge stays a listed gap, with
   DexScreener fallback rows stored unscored.
4. **Farside's issuer column lists** come from the published shape and are
   unverified. Check them on the box's dry run; the detector names any difference.
5. **SR-20's amendment,** for your accept-all.
6. **The session-set values:**
   - the DVOL band (20th and 80th);
   - the froth flag (both measures at z ≥ +2);
   - the GeckoTerminal budget (20 a minute);
   - the 20-sum minimum for S-2's percentile;
   - the 60-day minimum for S-4's.

## CI

This branch's push is read once and recorded here.

| Run | Commit | Result |
|---|---|---|
| 39037767039 (Gates, push) | `a4d8390` | **failed: 86 of 88 jobs passed** |

**The failure.** `tools/validate_weekly_edits.py` failed two checks; the second
failed job, `gates-passed`, only rolls them up.
1. It pinned Positioning at seven sub-sections, and the crypto flows block is the
   eighth.
2. The word "venue", banned in a rendered Weekly, appeared in two of the block's
   placeholder lines.

**The fix,** on this branch: the lines say "two exchanges report" and "every exchange
reports it", and the gate's list carries "Crypto flows" as the eighth sub-section.
Its CI run is recorded on `digital-49-51b`'s notes.

| Run | Commit | Result |
|---|---|---|
| 39038665381 (Gates, push) | `7e55cda` | **passed: 86 of 86 gate jobs** (80 code, 6 data; `gates-passed` green) |

Read once on 17 Oct. Nothing failed, so nothing to fix.

**The first derive on the box (17 Oct).** The crypto basket's `derive` printed
"stable impulse: computed 6368, written 0" after the llama pull had written
85,887 rows. That is expected, not a skip: `llama.pull` (macro group) calls
`crypto_basket.write_stable_impulse` itself, straight after its own write
(`altdata/sources/llama.py`, "S-1's derived series, from what is now stored"), so
the 30- and 90-day impulse was already stored by the pull. The basket's `derive`
recomputes the same 6,368 rows (both windows over every stored day of
`llama.stable_total`) and `drop_unchanged` removes all of them because each is
already there with the same value. A non-zero "written" on a later derive means
a new day or a revised input, which is the only case in which it should write.
