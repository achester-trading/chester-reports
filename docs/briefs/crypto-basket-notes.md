# The crypto basket tier: build notes (13 Oct 2026)

**Branch and inputs**
- **Branch:** `crypto-basket`, from `main` at `7754d0d`. Not merged and not deployed; nothing was run on the box.
- **Built against:** the ruled brief, `docs/briefs/crypto-basket-brief-2026-10-12.md` (decisions 1–7, decision 3 as the alternative).
- **Thesis source:** the operator's document, `docs/scans/crypto-basket-summary-2026-10-12.md`.
- **First commit:** those two files, docs only.

**Rules kept**
- Paper only, and no secrets: every source used is keyless.
- No register write. The restatement writes to the dry-run namespace.
- No other branch was touched. The unmerged ones (`aq-6-thesis-register`, `c1-move-screen`, the AQ and W-1 branches) were read by name with `git show`.

## What was built

**1. `config/crypto_basket.yaml`: twelve names, `tier: basket`.** A script lifted every quoted field from the document, with only its Markdown escapes removed:
- the thesis (the document's italic line);
- `case_for` and `case_against`, verbatim;
- what pays the token, US access and the odds, from the table.

`tools/validate_crypto_basket.py` checks:
- that each quote is in the document;
- that the odds equal the document's table, so a revised odds field fails the gate. The model never writes one.

Per name the config also carries:
- the resolved Yahoo symbol;
- the DefiLlama slug and coin id, and which DefiLlama series that slug actually serves;
- the measurable's key, with a note on what it does and doesn't measure;
- the falsifier: kind, series, threshold and date, or the reason it isn't measured;
- `operator_restatement: null`, the operator's own third column, hand-seeded when he wants one.

PRL carries `demoted: {from: deep, to: basket, coin_page: false}`.

**2. The series.**
- **`altdata/sources/llama.py`** is CD-1 pulled forward whole, under the `llama.*` family:
  - fees, revenue and holders revenue daily, plus protocol TVL, for every basket name DefiLlama lists;
  - market cap and supply for all twelve;
  - S-1 stablecoin supply, total and by chain (Ethereum, Tron, Solana, Base), with full history from 2017;
  - chain TVL (all chains and the same four), DEX volume and perps OI;
  - the S-1 derived series `calc.stable_impulse_30d` and `_90d`.
- **`yfinance_source.CRYPTO_BASKET`:** the twelve Yahoo closes and daily volume (`yfinance.crypto_<sym>`, `_volume`), as their own continuous basket. They are kept out of `SYMBOLS`, so the tape, breadth, betas and the routine pull are unchanged.
- **`calc.crypto_dilution_<sym>`:** a year's issuance over the value returned to holders, written only when both legs are stored.
- **Point-in-time:**
  - `observed_at` is the UTC day;
  - `available_at` is the pull instant, `ingest_instant`, never backdated;
  - a day is written only once it has ended;
  - a re-read of an unchanged value writes nothing.
- **Registry:** every key is in `metrics_registry.yaml` with `family` and `long_window`. Five bulk blocks hold the per-name series, and the market-wide ones have their own entries. Four new mechanism groups were added.
  - The store's third clock is `ingested_at`; there is no `retrieved_at` column, and ST-13's `retrieved_at` is that field.
  - `defillama` and `saturday_scan` are new in `source_registry.yaml`.
- **Fixtures:** samples captured on 13 Oct 2026 are in `tests/fixtures/llama/`, trimmed to 400 days. No gate fetches; the gate refuses any HTTP call.

**3. The falsifier grader, `altdata/crypto_basket.grade()`.** It returns holds / strained / failed / not measured, with the rule printed beside the status.
- **Failed** when the threshold is crossed, or when the date passes without the condition.
- **Strained** within the band (session-set at 10%), or past half the time to the date with no progress. The half-time rule applies to falsifiers that need something to happen (AERO); for a bad-when-reached threshold (ONDO's doubling) only the band applies.
- **Not measured, with the reason,** where there is no series, no threshold, or nothing stored at the cutoff. A measured falsifier with an empty store is never "holds".

**4. The odds restatement (decision 3).** `restate_quarter(st, quarter, quarterly_run, …)` writes `alt_asset` entries in aq-6's shape (`alt_asset:crypto_basket.<sym>`, scenario set `crypto_basket.<sym>-<quarter>-odds`), labelled "model estimate" and `emitted_by: model`. Each is graded next quarter on the direction of its move against the named measurable. The rules, each enforced by `validate_restatement` and shown in the gate:
- An undated row is refused.
- A move without a reason is refused.
- A reason must be one clause.
- A move must name one of the quarter's changes. Those are found mechanically: a falsifier's state changed, a measurable moved ≥ 25% (session-set), or a scan item.
- With no change, the model isn't asked and the row reads "unchanged — no measurable moved".
- The reference column is the config's text, byte-identical across quarters.
- It refuses to run without the Quarterly's run id. There is no CLI path to restate by hand.

Until `aq-6-thesis-register` merges, entries go to the dry-run namespace: `$CHESTER_DRYRUN_DIR` (default `~/state/dryrun`) `/alt_asset/crypto_basket_restatements.jsonl`.

**5. Printing.**
- **Weekly:** the basket as a detail table after the sections: the twelve names' price, week, 30 days and drawdown from high, then market cap and the measurable's latest and change, with an as-of date on every row.
  - Two tables of at most six columns each, because the readability rule caps a table at six.
  - One line in *What doesn't fit*, only when something happened: a 2.5σ move (`c1-move-screen`'s rule, recomputed locally), a falsifier crossed, a dated event due (AERO's 21 Oct launch), or a scan item. Otherwise it prints nothing.
- **Monthly:** *Themes: digital — the crypto basket*, right after the classics' rows, which are unchanged: price, month, market cap, drawdown and dilution; what pays the token over 30 days; one status line per name from the grader.
- **Quarterly:** `quarterly_pages()` builds the half-page per name:
  - the thesis and odds, with the reference, model and operator columns;
  - the measurables' quarter, the falsifier's state, dilution and US access;
  - the scan's stories on the name;
  - MW-7 on turnover (volume over market cap), with executable depth printed as not measured.

  PRL's page carries SR-10's S1–S8 as its falsifier set and says it has no coin page.
- **The amendment:** the AQ change order's §4.6 has its one line, "PRL: deep → basket, 12 Oct, by the crypto basket brief."
- **Consistency:** each new table tags its moves, and `daily_cascade/consistency.py` now also reads detail tables and a block's extra `tables`, which it didn't before. It compares only tagged cells, so existing editions are unaffected. The figure budget reads the Monthly block's twelve moves inside its cap.

**6. The gate:** `tools/validate_crypto_basket.py`, 76 checks, in the Makefile's list. It covers:
- the config, the series, the grader and the Weekly line;
- the restatement rules, the blocks and the wiring.

**7. The box, printed, not run.** `chester-crypto-basket.service` and `.timer` run `scripts/run_crypto_basket.sh` daily at 17:25 ET: after the 16:45 close capture and inside the evening window. The timer is in `DEPLOY_TIMERS`, so the self-deploy enables it after the merge.

## Sources, per name

**Price** is Yahoo for all twelve; it lists every one once the right symbol is used. **Market cap and supply** come from DefiLlama's coin service for all twelve. **Fees, revenue and TVL** come from DefiLlama's open API.

| Name | Yahoo (resolved) | DefiLlama slug | Coin id | DefiLlama serves | The measurable |
|---|---|---|---|---|---|
| SKY | SKY33038-USD | `sky` (parent of Sky Lending, Money, RWA) | `coingecko:sky` | fees, revenue, holders rev., TVL | `llama.revenue_sky` |
| LDO | LDO-USD | `lido` | `coingecko:lido-dao` | the four | `llama.tvl_ldo` (staked ETH) |
| SYRUP | SYRUP-USD | `maple-finance` | `coingecko:syrup` | the four | `llama.tvl_syrup` (TVL, not AUM) |
| AAVE | AAVE-USD | `aave` | `coingecko:aave` | the four | `llama.revenue_aave` |
| AERO | AERO29270-USD | `aerodrome` | `coingecko:aerodrome-finance` | the four | `llama.fees_aero` |
| TAO | TAO22974-USD | none: listed as `bittensor` with no fee, revenue or TVL series | `coingecko:bittensor` | none | not measured |
| MORPHO | MORPHO34104-USD | `morpho` | `coingecko:morpho` | the four | `llama.tvl_morpho` |
| UNI | UNI7083-USD | `uniswap` | `coingecko:uniswap` | the four | `llama.holders_revenue_uni` (the burn) |
| ONDO | ONDO-USD | `ondo-finance` | `coingecko:ondo-finance` | fees, revenue, holders rev. (TVL chart empty) | `llama.fees_ondo` |
| KAS | KAS-USD | none: not listed | `coingecko:kaspa` | none | not measured |
| VVV | VVV35509-USD | `venice` | `coingecko:venice-token` | the four | `llama.fees_vvv` (on-chain staking, not the run-rate) |
| PRL | PRL41876-USD | `pearl` (a chain; gecko `pearl-2`, pearlresearch.ai) | `coingecko:pearl-2` | fees only | `llama.fees_prl` |

**What Yahoo lacked, and the fallback:**
- **Prices: no fallback was needed.** But the bare `-USD` pair is **another coin** for three names: SKY-USD is Skycoin, AERO-USD is Aerovek, PRL-USD is The Parallel. It is **absent** for four (TAO, MORPHO, UNI, VVV), which Yahoo lists under a suffixed id. Each symbol was checked against Yahoo's own name on 13 Oct.
- **Pearl's Yahoo history starts 20 Aug 2026** (54 days), so its move screen stays silent until 500 observations.
- **Market cap and supply: Yahoo reports a snapshot only,** and 0 for Pearl. So they come from the fallback.

**CoinGecko's terms: the verdict is no.** The terms (coingecko.com/en/api_terms, latest version 5 Sep 2025):
- don't provide for keyless access at all; the licence follows "the usage plan that you select";
- say "We do not encourage caching or storage of Data";
- require a refresh at least every 24 hours, and deletion of everything on termination;
- require "Powered by CoinGecko" attribution.

A point-in-time store that keeps every vintage contradicts the storage clauses.

**The fallback: DefiLlama's coin service** (`coins.llama.fi/mcaps` and `/prices/current`). DefiLlama's terms (defillama.com/terms, effective 24 Jun 2025):
- allow the official public API for personal, non-commercial use;
- forbid republishing the data without permission.

Neither API host has a robots.txt rule. The service has no cap history, so **market cap and supply are forward-only**: they start the day the writer first runs. Supply is the cap over the service's own price at the same instant.

**Not served free:** `/raises` ("Upgrade to the paid API plan") and `/emissions` (Pro). DS-21's unlock schedules stay by hand, and no emissions series exists.

## Falsifiers: measured, and not

| Name | Measured? | How, or why not |
|---|---|---|
| ONDO | yes | `llama.supply_ondo`: failed at 2× the first stored supply by 31 Jan 2029; strained within 10% |
| AERO | yes | `llama.fees_aero`: the 30-day fee sum on 21 Jan 2027 against the 30 days to 20 Oct 2026. The threshold is the session's; the document dates the launch but gives no level |
| MORPHO | yes | `llama.holders_revenue_morpho`: the switch is on when the 30-day value reaching holders is above zero. Undated, so it cannot fail until a date is set |
| KAS | no | Kaspa's fees have no free series (not on DefiLlama) |
| PRL | no | SR-10's S1–S8 are its set. S1, S2, S7 and S8 are narrative; S3–S6 need SR-10's ST-13/ST-14 store, which isn't built |
| SKY, LDO, SYRUP, AAVE, TAO, UNI, VVV | no | The document gives no threshold or date for the "if it fizzles" paragraph (decision 4: the rest print "not measured"). TAO's outside revenue also has no series |

**ONDO's baseline** is the first stored supply. Because the cap is forward-only, that is the day the writer first runs, not 12 Oct.

## Box commands, for Ari (printed, not run)

**1. Backfill, once, after the merge and before the first timer run** (on the box, in `~/chester-reports`):
```
# Yahoo: the twelve closes and volume, full history (Pearl's starts 20 Aug 2026)
.venv/bin/python -c "from altdata.sources import yfinance_source as y; print(y.pull_crypto_basket(period='max'))"
# DefiLlama: every call returns full history, so the routine pull is the backfill
.venv/bin/python -m altdata.sources.llama pull
# the derived series (S-1 impulse now; dilution once 30 days of supply are stored)
.venv/bin/python -m altdata.crypto_basket derive
```
Market cap and supply have no backfill (forward-only).

**2. Enable.** The timer is in `DEPLOY_TIMERS`, so the self-deploy enables it at its next tick after the merge, or `bash scripts/deploy.sh` from the laptop. By hand:
```
systemctl --user daemon-reload
systemctl --user enable --now chester-crypto-basket.timer
systemctl --user list-timers chester-crypto-basket.timer
```

**3. The restatement** runs inside the Quarterly. When `aq-1`…`aq-10` merge, its run calls:
```
from altdata import crypto_basket, observations
with observations.ObservationStore() as st:
    rows = crypto_basket.restate_quarter(st, "<quarter>", "<the quarterly run id>")
pages = crypto_basket.quarterly_pages(st, "<quarter>", {r["name"]: r for r in rows})
```

**4. The Saturday scan's items:** `python -m altdata.crypto_basket scan-items <file.yaml>`. It takes a YAML list of `{name, kind, title, url, date}` and refuses anything outside the basket, the kinds, a URL or a date.

## Anything unexpected

- **Wrong coins.** Yahoo's bare pairs are the wrong coin for SKY, AERO and PRL. Read naively, the basket would have tracked Skycoin, Aerovek and The Parallel.
- **VVV and PRL are on DefiLlama;** the brief expected null for both, after verification.
  - VVV is `venice`, with fees from 8 Dec 2025. They are on-chain staking only, about $21k a day, not the founder's ~$100M run-rate.
  - PRL is the chain `pearl`, the right Pearl (gecko `pearl-2`), with fees from 31 May 2026.
  - TAO is listed with no series. KAS is not listed.
- **What DefiLlama measures isn't always the document's figure.** Maple's TVL (~$2.8bn) isn't its $4.55bn AUM. Ondo's TVL chart is empty. Each name's config note says what the series measures.
- **The live digital block reads two keys that don't exist.** The Monthly's *Themes: digital* reads `zec.price` and `crypto.cap_share`. The registered keys are `zec.price_usd` and `zec.crypto_cap_share`, so those rows always print absent. Left alone: the brief rules the classics unchanged.
- **ETH and SOL have no price series anywhere** (main or any branch). The "classics" today are BTC and ZEC.
- **The existing ZEC logger reads CoinGecko keylessly** (`zec.market_cap_usd`, `crypto.total_market_cap_usd`). By my reading of the terms above, that is the same problem.
- **Nothing ingests the Saturday scan.** `scan-items` is the path, and nothing writes to it yet.
- **Three dependencies live on unmerged branches:**
  - **The Weekly's "reference tier"** exists only on W-1.2 to W-1.3b. On main the basket prints as a detail table after the sections, which is where `storyline.move_reference` would put it.
  - **The Quarterly** exists only on the AQ branches. The basket tier is built as `quarterly_pages()` and `restate_quarter()`, to be called from its run.
  - **The move screen** is on `c1-move-screen`. Its rule is recomputed locally under the same constants until it merges.
- **The consistency walker's blind spot.** It skipped detail tables and a block's second table. It reads both now.
- **The prices gate's continuous-symbol check** now allows exactly BTC-USD, the three FX pairs and the twelve basket symbols the config declares.

## Needs you

1. **CoinGecko:** accept DefiLlama's coin service for market cap and supply, forward-only, given that CoinGecko's terms don't provide for keyless reads and discourage storing data? And should the existing ZEC logger's keyless CoinGecko reads be reviewed on the same reading? yes / no
2. **AERO's threshold** is the session's: fees one quarter after the 21 Oct launch below the 30 days before it. Ratify, or give a level? ratify / level
3. **MORPHO's fee switch** has no date in the document, so it cannot fail. Set a date? date / leave undated
4. **The grader's band** (10%) and the restatement's "a measurable moved" bar (25% on the quarter) are session-set. Ratify? yes / no
5. **ONDO's baseline** is the first stored supply, which is the writer's first run, because the cap is forward-only. Accept, or hand-seed the 12 Oct figure? accept / hand-seed
6. **MW-7 for the basket:** §4.6 refreshes the roster on executable depth and turnover, with no numeric bar. Turnover prints; depth is not measured (no free order-book source). Set bars, or leave the call to you each quarter? bars / by hand
7. **The Monthly's two dead digital keys** (`zec.price`, `crypto.cap_share`): fix them (a classics change), or leave them as ruled? fix / leave
8. **Merge order, inside windows:** this branch on its own. Its Quarterly and restatement wiring follow the AQ merges, and its Weekly table moves to the reference tier when W-1.3 merges. yes / no
