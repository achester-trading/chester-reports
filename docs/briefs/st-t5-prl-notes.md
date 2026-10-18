# st-t5-prl: ST-13, the PRL data layer (session notes, 18 Oct 2026)

**This branch, `st-t5-prl`, is cut from the tip of `lenses-group-b` (`3b0da9a`),
session B's own line in the second stitched chain.** It carries the lenses,
crypto Tranche A, the leftovers and the lab. **It merges after `lenses-group-b`,
in the second chain** (Thursday's merge).

ST-14 (the Monthly part renderer) and ST-15 (the emerging scan) are the next
paste.

Branch only: pushed, not merged, not deployed, nothing run on the box. No unit
was enabled, started or reconfigured. Session A's branches and chester-meme were
not touched.

| Part | Commit |
|---|---|
| ST-13, the build and its gate | `7c81ed1` |
| These notes | the commit after |

## Part 0: weekly-fixes-9's CI, the rulings, the worktree

**The CI reads**, once each:

| Run | Commit | Result |
|---|---|---|
| 39158278549 | `459cdb6` (the fixes) | **success, 96 of 96 jobs** |
| 39158393033 | `e88a94e` (its notes) | **success, 96 of 96 jobs** |
| 39175743738 | `4c5de89` (the rulings below) | **success, 96 of 96 jobs** |

Nothing of mine failed. All three runs are in `weekly-fixes-9-notes.md`.

**The rulings of 18 Oct, as applied on `weekly-fixes-9`:**
1. **The FX floor.** A pair the scanner still reads takes half an ATR alone.
   Equities and ETFs keep the larger of half an ATR and 0.5%. The "Pivots as
   set" line says both.
   - Fixture: one distance, past half an ATR and inside 0.5%, prints R for
     EURUSD and no R for a stock.
   - `validate_weekly_fixes_9` 39/0, `validate_book_b_scanner` 63/0.
2. **The two labelled flips stand.**
   - The session's level words and flags read the morning capture, as built.
   - The close capture's head prints its time, "Gamma flip (close capture, Fri
     16 Oct)", and the Tape's note says it is the next session's level.
3. **The Monthly v2 retry** stays listed for the Monthly's post-dry-run fixes.
4. **The `chester-chain` worktree** was fast-forwarded to `110fb31`; it was
   clean.

## Part 1: ST-13, item by item

What I read:
- the order's 2.7 (2.7.1-2.7.8), its row ST-13, G-24 to G-27 and Appendix E;
- the Security Master's model and resolver, and the crypto basket's PRL entry;
- Tranche A's writers (`fng.py`, `_crypto.py`, `_publication.run`) as the model
  for point-in-time rows;
- the registry's crypto families;
- CLAUDE.md.

### Two findings first

**1. PRL was already in the Security Master.** It is SM00118: class `crypto`,
from the crypto basket, keyed by Yahoo's coin id `PRL41876-USD`, the store key
`yfinance.crypto_prl`, `crypto_id coingecko:pearl-2`, and the alias `PRL`.
- A second entry would have two instruments carrying `coingecko:pearl-2`. The
  resolver refuses that (Ambiguous).
- It would also have taken SM00195, which session A's line allocates (`^VIX9D`
  and on, next_id 200 there).

**So SM00118 is reclassified in place: one coin, one id** (G-24, settled by
AUD-3b).

**2. CoinGecko's terms and the 13 Oct ruling.** On 13 Oct 2026 CoinGecko was
retired as a source for this store. `source_registry.yaml` `coingecko` is
`status: retired`; the basket and the ZEC logger moved to DefiLlama's coin
service. I read the terms again on 18 Oct (coingecko.com/en/api_terms):
- 6.1: "We do not encourage caching or storage of Data";
- 6.1.1: a refresh "at least every 24 hours";
- 6.2: "you are not allowed to duplicate, reproduce, copy, store, derive from or
  translate any Data".

The order (MW-4) and this paste ask for a CoinGecko fetcher storing
point-in-time series, and `calc.prl_*` derived from them. **I built the fetcher
as specified and left it behind the existing switch,
`ENABLED_SOURCES["coingecko"]`, which stays off.** While off it fetches and
parses, so `--dry-run` shows exactly what it would store, and it **writes
nothing**. Reconciling the two rulings is Ari's (needs-you 1).

The derived layer does not wait on that. It reads PRL's price and cap from the
basket's permitted series (Yahoo's close; DefiLlama's cap) and names the
fallback in each trace. Only D3 (circulating supply) and D5 (venues) need
CoinGecko alone, and they print absent with their reason until it is stored.

### 1. `crypto.watch` in the Security Master, and the PRL entry

**The model** (`altdata/security_master.py`):
- `ASSET_CLASSES` gains `crypto.watch`.
- A watch entry is keyed by `identifiers.crypto_id = "coingecko:<id>"` (the
  scheme ZEC already uses), and `Master.by_coingecko("pearl-2")` resolves it.
- It carries MW-1's fields under `watch`: `coingecko_id`, `name`, `issuer`,
  `chain`, `explorer`, `mechanism_class`, verbatim from the order.
- No schema change reaches chester-meme. The export is keyed by composite FIGI
  from the listings, and a watch coin has none.

**The loader test (G-24).** `structural()` runs `watch_faults` on every
`crypto.watch` entry and refuses:
- a `ticker` identifier, a ticker history, or a bare-ticker alias (the
  collision MW-1 names);
- a missing MW-1 field;
- a `crypto_id` that is not its CoinGecko id, or a name that disagrees with its
  watch name.

**Kept on purpose:** Yahoo's coin-specific id and the basket's store key stay,
because the basket resolves through them. Yahoo's plain `PRL-USD` is another
coin, so `PRL41876-USD` is not the ticker.

**SM00118 now:** `crypto.watch`, `watch` as MW-1, alias `PRL` removed (nothing
resolved by it), `active_from 2026-04-27` (genesis), each field with its
source.

**Gates:**
- `validate_security_master` **97/0**. Its continuous-symbol check now reads
  "crypto (a watch coin included) or fx".
- `validate_st_t5_prl` B: the resolver, the MW-1 fields, three refused
  ticker-keyed fixtures, a missing field and a wrong crypto_id, and no FIGI.

### 2. The CoinGecko fetcher for pearl-2

`altdata/sources/coingecko.py`. G-25: no fetcher existed on this line, only the
switch, so there was nothing to extend. This is the fetcher the order names,
and the switch stays its gate.

**Sources:** `GET /api/v3/coins/pearl-2` (market_data) and
`/api/v3/coins/pearl-2/tickers`.

**Series:**
- `coingecko.prl_price`, `_market_cap`, `_volume_24h`, `_circulating`, on the UTC
  day of `last_updated`;
- `coingecko.prl_venue_volume` (one row per venue, instrument = the venue);
- `coingecko.prl_venues` (the count).

available_at is the pull instant. A response for another coin is refused.

**Keyless first.** The Demo key is optional and read only if the environment
carries it.
- **Its name is `COINGECKO_DEMO_API_KEY`**, sent as `x-cg-demo-api-key`. It is
  named in the catalogue line and `config/prl.yaml`.
- No session creates it; `.env` is Ari's.
- The User-Agent names no one.

**The budget:** two calls a pull, 6 s apart. A weekly pull plus one daily close
is 16 calls a week, far inside the public limit (of the order of 5-15 calls a
minute) and the Demo plan's (30 a minute, 10,000 a month).

**The terms line:** in the docstring and as a caveat on `source_registry.yaml`
`coingecko`, which stays **retired**.

**Fixtures** (C):
- `/coins/pearl-2` and `/tickers` responses parse to their rows;
- another coin's response is refused;
- keyless, and the key only from the environment;
- two calls six seconds apart;
- **switch off: fetched, parsed, nothing written**;
- switch on (in the gate only): written point in time.

### 3. `pearl_explorer.py`: the chain height and supply

`altdata/sources/pearl_explorer.py`. Three legs, in MW-4's order:
1. a JSON endpoint declared in `config/prl.yaml` (its URL and the JSON path of
   each field);
2. the block page (its URL and regexes);
3. neither: nothing is stored, and the derived layer prints ESTIMATED.

Legs 1 and 2 are read only where robots.txt allows the path, under the REP's
reading with wildcards (`aaii.robots_verdict`). An unreadable robots.txt is not
permission.

**G-26: the endpoint is not yet discovered.** On 18 Oct neither
explorer.pearlresearch.ai nor pearlresearch.ai answered from this machine. The
TLS connection closed on /robots.txt, and later connections were refused. So no
robots or terms line could be read, and nothing is declared. The docstring
records:
- "robots: (not read: unreachable 18 Oct 2026)";
- "terms: (not read: unreachable 18 Oct 2026)";
- "endpoint: (none declared)".

`source_registry.yaml` `pearl_explorer` is `status: built`.

**Series:** `pearl.chain_height`, `pearl.chain_difficulty`, `pearl.chain_supply`,
observed values only.

**Fixtures** (D):
- a fixture JSON response through a declared spec, robots allowing it;
- robots refusing it reads nothing;
- the block-page leg, its rows marked `pearl_explorer:page`;
- nothing declared (this branch): reads nothing, writes nothing, says ESTIMATED.

### 4. The emission calculator, D1-D6 and the thesis status

`altdata/prl.py`, config `config/prl.yaml`.

**The emission (Appendix E):**
- `reward(h) = 2.1e9 * K / ((h + K)(h - 1 + K))` and `supply_code(H) = 2.1e9 * H
  / (H + K)`, with K = 650,226.
- **The three unit tests:** block 1 = **3,229.6**, block 113,770 = **2,339.4**,
  supply = **312.72M**.
- The rewards sum to the supply (the formula telescopes), half the supply sits
  at block K, and the pace is about 1.04M PRL a day.

**The height, and the ESTIMATED marker:**
- The explorer's height on the cutoff's day is used as read.
- Otherwise the height is **ESTIMATED**: the newest observed height, else
  Appendix E's anchor (block 113,770 at 2026-09-15 23:53 UTC), stepped at the
  194 s target. It is stored as `calc.prl_height_estimated`, never as the
  explorer's key.
- Every figure from an estimated height says ESTIMATED in its trace, and an
  empty store still prints a height and a supply.
- Why the anchor and not genesis: estimating from genesis would sit about
  50,000 blocks low, because the first 40,000 blocks came in 5.9 days.

**D1-D6, each as `calc.prl_*`** (2.7.4; units by AUD-3a):

| Item | Key | Definition | Units |
|---|---|---|---|
| D1 | `supply_code` | the code supply | count, PRL |
| D2 | `overhang` | 121.70M over D1 | percent_share |
| D3 | `supply_gap` | D1 less CoinGecko's circulating | count |
| D4 | `emission_to_volume` | reward x 86400/194 x price over 24h volume | ratio |
| D5 | `venue_conc` | the top venue's share | percent_share |
| D6 | `idle_gpu_flag` | difficulty up > 25% while price is down > 20% over 30 days | boolean |

Also stored: `calc.prl_reward` (count) and `calc.prl_height_estimated`. Each
row's available_at is the latest of its inputs'.

**The thesis status** (2.7.5): `calc.prl_thesis_status`, stored as JSON
`{status, trace}`.
- **IMPROVED:** S1 a named partner; S2 a PRL path; S3 a tier-1 listing; D5
  below 60% with volume up.
- **DETERIORATED:** S7 an exploit, halt or reorg; the Together endpoint
  withdrawn; D4 above 1.0 for four weekly reads; a top venue delisted.
  DETERIORATED outranks IMPROVED.
- **UNCHANGED** otherwise.
- The trace prints the word, then what fired, what was read (each input beside
  its value) and what was not read.
- The narrative signposts are `manual_input` until ST-15 and are passed in.

**Rights (MW-2):** D6 is the one narrow flag (`rights_ceiling narrow_flag`), and
the status's is `none`. Nothing is trigger-eligible, and no composite, dial,
overlay or band reads any key.

**Fixtures** (E):
- D1-D5 by hand from a fixture store (D5: CoinEx 91.0%);
- D6 on (difficulty +45.8%, price -25.0%) and off;
- the ESTIMATED fallback on an empty store, never blank;
- an absent input absent with its reason;
- a week-old observed height as the estimate's anchor;
- the three thesis words, each with its trace;
- every stored row point in time.

### 5. Registry, catalogue, units, counts

- **Registry:** 18 new metrics (6 `coingecko.prl_*`, 3 `pearl.chain_*`, 9
  `calc.prl_*`), each with units, family and long window. The flag and the label
  go in `lens_excluded` with their reasons. There is no by-hand key; every
  source is a writer or calc.
- **Source registry:** `pearl_explorer` (tier B, `primary_fact`, `built`), and the
  ST-13 caveat on `coingecko` (still retired).
- **Catalogue:** `altdata.sources.coingecko` (naming the optional key),
  `altdata.sources.pearl_explorer` and `altdata.prl`.
- **Counts:** CLAUDE.md now reads ninety-eight code gates (ninety-five Python),
  recounted from the Makefile, and a paragraph on the layer.
- **Nothing renders:** ST-14 renders.
- **The Daily grep:** no `daily_cascade` module names PRL or Pearl or imports the
  layer (F). The ST-10 gate itself is not on this line, so this gate carries its
  check.

### The gates, locally, one at a time

| Gate | Result |
|---|---|
| `tools/validate_st_t5_prl.py` (new, in the Makefile) | **57 passed, 0 failed** |
| `tools/validate_security_master.py` | **97 passed, 0 failed** |
| `tools/validate_crypto_basket.py`, `validate_crypto_sources.py`, `validate_outliers.py` | **93/0, 105/0, 37/0** |
| `tools/validate_audit_3a.py`, `validate_lenses.py` | **86/0, 49/0** |
| `tools/check_registry.py`, `tools/check_library.py` | OK; 0 failures, 0 warnings |

Everything else is left to CI. No gate reads the live store, fetches or calls a
model, and nothing rendered.

**Network reads while building** (never by a gate):
- one read of CoinGecko's terms page;
- one read of DefiLlama's coin service and prices, in the last paste, for W8-11;
- attempted reads of the explorer and pearlresearch.ai's robots.txt, which
  failed.

## CI

Each run read once, with `gh run list --branch st-t5-prl --limit 3`.

| Run | Commit | Result when read |
|---|---|---|
| 39177151583 | `7c81ed1` (the build) | **in progress**: 105 of 107 jobs green, 1 failed (`validate_config_refs`) |
| 39177294541 | `dd10f77` (these notes) | **in progress**: the same failure |
| (the rulings) | the commit after | in the session's closing report |

**The cause was mine.** `validate_config_refs` reads any `<namespace>.<name>`
string in a config file as a metric id. `crypto` is a registered namespace
(`crypto.total_market_cap_usd`), so the class `crypto.watch` in
`config/security_master.yaml` read as an unregistered key.
- The gate now treats an `asset_class` field's value as vocabulary, not an id
  (`VOCAB_FIELDS`).
- A new check shows the entry's metric keys beside it are still caught.
- Locally: 79 passed, 0 failed.

## The rulings of 18 Oct on this report, as applied (the second paste's Part 0)

1. **CoinGecko stays retired.**
   - `altdata/sources/coingecko.py` is removed, and so is its
     `ENABLED_SOURCES` entry, so no flag can turn it on. The six
     `coingecko.prl_*` registry entries and its catalogue line are gone.
   - `source_registry.yaml` `coingecko` stays retired and keeps the terms line
     (6.1, 6.1.1, 6.2), with the ruling.
   - The order's register gains a "Rulings addendum — 18 Oct 2026": MW-4's
     CoinGecko clause is superseded.
   - **PRL's inputs** (`config/prl.yaml` `derived`) are now the basket's own keys:
     price `yfinance.crypto_prl` and 24h volume `yfinance.crypto_prl_volume`
     (Yahoo, PRL41876-USD; D4 reads that volume); cap `llama.mcap_prl` and
     circulating supply `llama.supply_prl` (DefiLlama's coin service).
   - **D5** prints "not tracked (source retired): calc.prl_venue_conc's only
     input was CoinGecko's tickers". The registry entry carries `tracked: false`,
     and the thesis rule lists D5's leg as not read.
   - **D3** is the formula at the explorer's height less the explorer's supply.
     It is ESTIMATED, with no row written, until the explorer reads.
   - **Fixtures** (`validate_st_t5_prl` C and E):
     - the removal, the terms line, the register line, the inputs;
     - D4 from Yahoo's volume;
     - D5 not tracked;
     - D3's ESTIMATED path and its explorer path.
2. **The explorer:** no robots or terms line had been pasted when this ran, so
   the endpoint stays undeclared and the height ESTIMATED.
3. **Scheduling: no new timer.**
   - `python -m altdata.prl weekly [--dry-run] [--force]` is the explorer read.
     It runs on Saturdays and skips itself otherwise. With no endpoint declared
     it returns PENDING, so the heartbeat lists its keys pending with no
     allowance running.
   - `python -m altdata.prl daily [--dry-run]` is the D-series compute.
   - Both are one line each in `scripts/run_crypto_basket.sh`, the basket's
     daily 17:25 run, after the basket's own writes. There is no separate
     Saturday run on the box: the "Saturday crypto scan" is the chat-side
     interim task, so its weekly step lives in the Saturday run of the basket's
     timer.
   - Both are on the freshness roster (`feeds.freshness`, roster `prl`). Each
     records its attempt.
   - **Fixtures** (H): the daily dry run writes nothing, then the real run
     writes; the weekly skips off-Saturday and is PENDING on Saturday; the two
     lines sit after `derive`; no PRL unit; the roster.
4. **SM00118 reclassified in place stands.** Gate H proves the basket still
   resolves `PRL41876-USD` to `yfinance.crypto_prl` through it.

**Locally after the rulings:**
- `validate_st_t5_prl` **61/0**, `validate_config_refs` **79/0**;
- `validate_crypto_basket` **93/0**, `validate_crypto_sources` **105/0**;
- `validate_backups` **28/0**, `validate_audit_3a` **86/0**, `validate_lenses`
  **49/0**;
- `check_registry` and `check_library` OK.

**This supersedes, above:** the CoinGecko fetcher (item 2), the "switch stays
off" finding, needs-you items 1 and 3 (both ruled), and the box command for
CoinGecko. The box commands that stand are the explorer's dry run (now
`python -m altdata.prl weekly --dry-run --force`) and the compute's
(`python -m altdata.prl daily --dry-run`).

## Box commands, for Ari

Run these inside a window, **after Thursday's merge**, dry run first. Nothing
here was run.

1. **The first CoinGecko pull.** The dry run reads two endpoints, parses, and
   writes nothing:
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.sources.coingecko --dry-run | head -60'`

   A real pull writes nothing either until `ENABLED_SOURCES["coingecko"]` is
   turned on in `altdata/config.py`, which waits on needs-you 1.
2. **The first explorer read:**
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.sources.pearl_explorer --dry-run'`

   With no endpoint declared it reports "estimated", with the reason. The box
   may reach the explorer where the laptop could not. If so, read its robots.txt
   and terms (`ssh vps 'curl -sS https://explorer.pearlresearch.ai/robots.txt |
   head -40'`) before any endpoint is declared.
3. **The first `calc.prl_*` compute.** The dry run prints every figure, its
   trace and the rows it would write:
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.prl compute --dry-run | head -80'`

   Then the same without `--dry-run` writes the day's rows. Today D1, D2 and the
   reward print ESTIMATED from the anchor; D4 needs a 24h volume (CoinGecko's);
   D3 and D5 print absent.

**No timer is added and no unit changes.** Scheduling the three steps (for
example, a line in `scripts/run_crypto_basket.sh`) is needs-you 3.

## Files shared with the open branches

**Session A's line** (`a44-opening-setup`, `a43-render`, `st-t3-calib`,
`gtm-core-2`) also edits:
- `CLAUDE.md`, `Makefile`;
- `config/catalogue_commands.yaml`, `config/security_master.yaml`;
- `metrics_registry.yaml`, `source_registry.yaml`.

A trial merge (`git merge-tree`, which writes nothing) shows **no conflict this
branch adds**: every conflict against session A's line is one `lenses-group-b`
already has.

- **`config/security_master.yaml`** is the one to read at the stitch. Session A
  appends SM00195 to SM00199 and moves next_id to 200. This branch edits SM00118
  in place and leaves next_id at 195, so the two merge clean and session A's
  next_id stands.
- **The rest:** each of my edits is an insertion beside a named anchor:
  - the metrics before `blockscout.gas_gwei`;
  - two `lens_excluded` lines at the map's head;
  - `pearl_explorer` before `alternative_me`;
  - three catalogue lines before `altdata.sources.fng`;
  - one Makefile line after `validate_releases_b`;
  - the count line, and one CLAUDE.md paragraph before the Digital Assets
    addendum's.

  The counts are the stitch's to recompute.

`alpha-lab-3` shares no file with this branch. Untouched: chester-meme, `.env`,
the units, the registers and the trade ledgers.

## Needs you

1. **CoinGecko: store or not.** The 13 Oct ruling and the terms as read on 18 Oct
   (6.1, 6.1.1, 6.2) stand against a store of CoinGecko vintages and figures
   derived from them. The order and this paste ask for exactly that. The fetcher
   is built and writes nothing while `ENABLED_SOURCES["coingecko"]` is off.
   Three ways forward:
   - turn it on (the order's MW-4);
   - keep it off: D3 and D5 stay absent, and D4 needs another 24h-volume source;
   - store with a 24-hour refresh only, which a point-in-time store cannot do.
2. **The explorer (G-26):** unreachable from this machine on 18 Oct. Once robots
   and terms are read from the box (or a browser), the endpoint goes in
   `config/prl.yaml`, and its robots and terms line in the fetcher's docstring.
3. **Scheduling:** none of the three steps is on a timer or on
   `feeds.EXTERNAL_WRITERS`, so no heartbeat lists them yet. A weekly pull plus
   a daily close (MW-4) is one line each in the basket's daily run, after the
   CoinGecko ruling.
4. **SM00118 reclassified, not a new entry:** one coin, one id. Its `PRL` alias
   is gone (nothing resolved by it). Say if you want the basket's crypto class
   kept beside the watch class instead.
