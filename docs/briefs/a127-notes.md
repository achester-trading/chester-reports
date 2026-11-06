# A127 notes: item 116 part 1, the levered-ETF close flow (6 Nov 2026)

Session A, branch `a127-item-116-close-flow`, from `origin/main` at `ee04ba21` (b114-names-sweep's merge, confirmed). Branch only: it merges Monday 9 Nov in chain-13. No PR, no merge, no box.

The order is `docs/change-order-signal-triage-batch-22-2026-11-05.md` on `origin/b129-five-filings`: item 116 (the order's 98), its section 0 (P1-P6), O-1 and O-6. This paste builds 98.1 and 98.3. 98.2, the calibration ledger and its two seed rows, is not in it.

**Rights.** A report line and the 15:00 flag only. Nothing enters a composite, the market-state object, the T&B intake queue or a regime. The flag is alert-only.

## What was built

| Piece | Where |
|---|---|
| The roster: 32 funds, 6 buckets, the underlyings, the floor, the flag and the switch | `config/levered_etf.yaml` |
| The AUM writer for the issuers other than ProShares (into the existing `levetf.aum` key) | `altdata/sources/levered_etf.py` |
| The ProShares writer extended with USD and ROM (the same file, the same key) | `altdata/sources/proshares.py` |
| The estimate, the flag and its dated switch, the 15:00 pass | `altdata/close_flow.py` |
| The prints: the close's table and line; the Weekly's and Monthly's period table | `daily_cascade/close_flow_block.py` |
| The close builds the 16:45 estimate and stores its rows after the report | `daily_cascade/stack.py`, `daily_cascade/stack_close.py` |
| The Weekly and the Monthly print the period table, last in Positioning before the allocation block | `daily_cascade/weekly_stack.py` |
| The 15:00 unit, timer and wrapper (one call, non-fatal) | `deploy/systemd/chester-close-flow.{service,timer}`, `scripts/run_close_flow.sh` |
| The DTH-1 draft setup (98.3) | `config/setups.yaml` `c_dth1_close_flow_reversal` |
| The gate | `tools/validate_item_116.py` (63 checks) |

## The roster

There are 32 funds: 30 read and 2 gaps. Each fund names its issuer, L, underlying, bucket and issuer page.

- **ProShares, 14 funds, on the existing writer:** TQQQ, SQQQ, QLD, QID, UPRO, SPXU, SSO, SDS, UDOW, SDOW, URTY and SRTY, plus USD and ROM.
- **Direxion, 11 funds:** SPXL, SPXS, SOXL, SOXS, TNA, TZA, TECL, FAS, TSLL, TSLS and GGLL.
- **GraniteShares, 3 funds:** NVDL, AMDL and CONL.
- **REX, 2 funds:** MSTU and MSTZ.
- **Tradr, 2 funds, both gaps:** SNXX and TSLQ.

**The buckets.** Semiconductors, Nasdaq 100, S&P 500, Russell 2000, and named single stocks. A sixth, "other index and sector funds", holds the Dow 30, technology and financials funds (UDOW, SDOW, TECL, ROM and FAS). It is named rather than folded into a neighbour.

**The floor.** It is $500m, applied to the funds the paste did not name. Each fund is measured by its issuer's own figure, read on 6 Nov 2026. A named fund stays on the roster whatever its size: SPXS, TZA, CONL and MSTZ are below the floor.

**Not on the roster**, each with its reason in the config:
- UVXY, a volatility product;
- TMF, which holds Treasuries;
- YINN, China large caps, not a US close;
- LABU, whose index ETF (XBI) is not stored;
- MSTX, at $0.255bn, below the floor.

The other funds read and found below the floor:

| Fund | AUM read on 6 Nov |
|---|---|
| NVDU | $0.321bn |
| AAPU | $0.125bn |
| PLTU | $0.223bn |
| MSFU | $0.353bn |
| METU | $0.311bn |
| AMZU | $0.284bn |
| WEBL | $0.061bn |
| FNGG | $0.089bn |
| TSLR | $0.054bn |
| AAPB | $0.017bn |
| FBL | $0.138bn |
| MSFL | $0.054bn |
| NVD | $0.059bn |
| PTIR | $0.197bn |
| NVDX | $0.317bn |
| TSLT | $0.147bn |

These figures are build-time evidence only; none is committed in config.

**The blocklist.** No Brookfield-complex name is on the roster. The writer and the 15:00 pass assert every ticker against `register/instruments.py` before any request, and the check fails closed: a blocklist that will not load refuses every ticker. The gate plants BN and proves both.

## The Security Master: the ids allocated (D28)

`next_id` was 221 and is now 241. The twenty new entries are each asset class `etf`, with `yahoo`, `store_key` and `ticker` identifiers. Each name and exchange comes from Nasdaq Trader's symbol directories (File Creation Time 1106202612:11, 2026-11-06), mapped through `config/listing_exchanges.yaml`.

| Id | Ticker | Id | Ticker |
|---|---|---|---|
| SM00221 | USD | SM00231 | TSLL |
| SM00222 | ROM | SM00232 | TSLS |
| SM00223 | SPXL | SM00233 | GGLL |
| SM00224 | SPXS | SM00234 | NVDL |
| SM00225 | SOXL | SM00235 | AMDL |
| SM00226 | SOXS | SM00236 | CONL |
| SM00227 | TNA | SM00237 | MSTU |
| SM00228 | TZA | SM00238 | MSTZ |
| SM00229 | TECL | SM00239 | SNXX |
| SM00230 | FAS | SM00240 | TSLQ |

The twelve existing ProShares entries (SM00132 to SM00138 and SM00216 to SM00220) gain `yahoo` and `store_key` identifiers. Their ids are unchanged.

`store_key` is `levetf.aum:<TICKER>`: the store key and the instrument. These funds have no price key of their own, so the store key names the one series kept for each.

If chain-13's stitch meets another branch that took ids from 221, D28.3's renumbering applies.

## V-98b: the issuers' pages (checked 6 Nov 2026)

| Issuer | Reading | robots.txt | Result |
|---|---|---|---|
| ProShares | `accounts.profunds.com/etfdata/ByFund/<T>-historical_nav.csv` (the existing writer) | 404 (no rules) | read; full history |
| Direxion | `www.direxion.com/holdings/<T>.csv`: net assets = MarketValue x 100 / HoldingsPercent | `Allow: /` | read, all 11 |
| GraniteShares | the fund page, then its dated holdings workbook: shares outstanding x NAV/Share | `/umbraco` disallowed only | read, all 3 (two requests a fund) |
| REX (T-Rex) | the fund page's "As of" date and "Fund Assets" | no disallow; `Crawl-delay: 10` (honoured) | read, both |
| Defiance | the page's "Net Assets" | no disallow | readable, but its one candidate (MSTX) is below the floor |
| Tradr | pages fill AUM in the browser; no figure or file | — | **gap**: SNXX and TSLQ |

**Direxion's data.** The holdings file dated D carries D's previous session's closing prices. I checked AMD's and NVDA's lines against their 5 Nov closes. So the AUM is stored at the previous session's close, which is the one the formula wants. The writer refuses a file whose lines' implied net assets disagree by more than 0.1%.

**GraniteShares' own AUM figure.** The page fills it from a signed Azure endpoint, a key in effect, which is never called. The workbook's shares outstanding x NAV/Share is used instead.

**Tradr: the aggregator step (V-98b).** I checked one public aggregator, stockanalysis.com. Its robots.txt allows the ETF pages, but its terms say "You may not use bots, scripts, scrapers ... or any other automated" means. So SNXX and TSLQ are gaps (the 16 Oct rule), named in every estimate's left-out line. Tradr's own home page lists both among its largest funds, and one manual look at the aggregator put SNXX near the floor.

**Dry run.** `python -m altdata.sources.levered_etf --dry-run` on 6 Nov read all 16 non-ProShares funds and wrote nothing.

## V-98c: dollars per 1% move, recomputed

These figures come from the roster's AUM as each issuer stated it at the 5 Nov close (REX's at 4 Nov). They were read on 6 Nov by the writers' own parsers, and nothing was stored. The command is `python -m altdata.close_flow per-move`, which reads the stored AUM once it exists.

**Totals:**
- Roster AUM read: **$98.1bn** across 30 funds.
- Every underlying moving 1% at once: **$5.30bn**.
- The index funds alone: **$5.14bn**.

**By bucket**, for every underlying moving 1%:

| Bucket | $ per 1% |
|---|---|
| Semiconductors | $1.51bn |
| Nasdaq 100 | $2.18bn |
| S&P 500 | $0.90bn |
| Russell 2000 | $0.12bn |
| Other index and sector | $0.43bn |
| Single stocks | $0.15bn |

**Largest funds:**

| Fund | AUM |
|---|---|
| TQQQ | $27.97bn |
| SOXL | $13.56bn |
| QLD | $11.16bn |
| SSO | $6.92bn |
| SPXL | $5.87bn |
| SOXS | $5.52bn |
| UPRO | $4.84bn |
| TECL | $3.61bn |
| TSLL | $2.65bn |
| NVDL | $2.25bn |
| SQQQ | $2.19bn |

**The old rule is retired.** The ~$7bn-per-1% rule of thumb dates from $117bn of levered AUM. It is retired: the figure is now the roster's own, and it moves with the AUM every day.

**Not comparable with 5 Nov's figures as it stands.** These AUMs are after the 5 Nov fall, which took SOXL and TQQQ down hard. On 5 Nov's moves this roster gives roughly $15bn (semis), $12bn (Nasdaq 100) and $4bn (S&P 500), which is below MS's $52bn 1pm estimate. Two reasons: MS's universe is wider than this roster, and its estimate predates the fall in AUM. V-98a's check against MS stays with the Sunday Weekly.

## The 15:00 pass and the 16:45 estimate

**There was no 15:00 pass on main.** No timer runs between the 12:30 capture and the 15:49 auction sampler. The paste names "the 15:00 pass's wrapper (one call)". So this branch ships one:
- `chester-close-flow.timer`, Mon-Fri 15:00 ET;
- its service, with the EOD unit's sandbox and no memory cap (a light unit);
- `scripts/run_close_flow.sh`, which makes one call, `python -m altdata.close_flow estimate --slot 1500`, and exits 0 whatever happens.

The timer is **held out of `DEPLOY_TIMERS`**: the operator enables it on the box (needs-you 1). It is in the Master Guide's Table 1 as "by hand"; figure 2 and the Guide's HTML edition were regenerated.

**The 15:00 estimate.** The pass re-reads both AUM writers first, non-fatally. ProShares posts the prior close's NAV in the evening, and the others' files carry it by morning, so the EOD pull alone would leave the 15:00 read a day stale. It then reads each underlying's last completed 5-minute bar at or before 15:00 ET, through `note_fetch.yf_fetcher`, against its stored prior close. On an early close it reads the 13:00 close. It stores `calc.close_flow.*` with instrument `1500`.

**D33.** "No new yfinance symbols from 24 Oct 2026" is in the registry. So the intraday read covers only the eleven underlyings already in the price basket: QQQ, SPY, IWM, SMH, DIA, XLK, XLF, NVDA, TSLA, GOOGL and AMD. MSTR, COIN and SNDK are not read. MSTU, MSTZ and CONL have their AUM stored but are left out of both estimates as "underlying not read (D33)" (needs-you 2).

**The 16:45 estimate.** The close computes it in memory from the stored closes (the EOD pass at 16:10 has written them) and the prior-close AUM. It stores the rows (instrument `1645`) after the report, as it does the gold rows. The mechanical close-flow line is a Positioning item, fingerprinted by the day's total, so a session whose flow moved is never collapsed as unchanged.

**% of ADV.** Each bucket is measured against the 20-session average dollar volume of the instruments driving it, through the session before. For an index bucket that is the ETF's dollar volume (SMH, QQQ, SPY, IWM, DIA/XLK/XLF), not its constituents' (needs-you 3). The 60-session switch reads the box's own history in the same units, so the flag is unaffected.

**The flag (O-1).** At 15:00, |the total| at or above $20bn fires. After 60 stored 15:00 sessions, `flag_rule()` switches by itself to the 90th percentile of |the history| in % of ADV. It dates the switch as the session after the 60th stored one and prints that date in the line. No one edits the config on day 61.

**The prints.** The close shows a table (16:45 and 15:00 by bucket, $bn and % of ADV), the flag's line only when it fired, and the funds left out, named. The "mechanical close flow" line says "dealer hedging: not yet combined", because 6b's dealer-hedging estimate is not wired. The Weekly shows the week's sessions, largest first. The Monthly shows the same table, its five largest. Nothing goes in the 07:00 anchor.

**History** builds from the first live run; nothing is backfilled by hand.

**The fragility panel is unchanged.** Item 71's panel still reads its own twelve ProShares funds from the same key. It now finds more instruments under `levetf.aum`, but it reads only the tickers in its `covered` list (validate_batch14_b1 68/0).

## 98.3: the DTH-1 draft setup

`c_dth1_close_flow_reversal`, Book C, has `status: draft`, a status word added to the catalogue's header for an entry a ruled order places as a draft. Its mechanism carries the order's sentence. Two places had to accept it:
- `tools/validate_packets.py` accepts `draft` beside `stub` and `complete`;
- `config/alpha_tells.yaml` lists it under `setups_skipped`, so the lab does not pre-register a draft as a hypothesis. The lab's setup count stays 15.

The register's rights are unchanged: like a stub, the id resolves and grants nothing.

## Registries, roster and counts

- **`levetf.aum`** now declares `sources: [proshares, levered_etf]`. The new instruments are barred from the market-state object, and so is `calc.close_flow.*`.
- **Fourteen `calc.close_flow.*` keys** (six buckets and the total, $ and % of ADV) are registered: trigger-ineligible and lens-excluded (an estimate per session and slot).
- **Two source ids** are added to `source_registry.yaml`: `levered_etf` (variants by issuer) and `close_flow`.
- **`levered_etf`** joins `feeds.EXTERNAL_WRITERS` after `proshares`, so it runs in the EOD pass after the prices and is on the freshness roster. The catalogue lists both new modules.
- **Counts** (`tools/stitch_counts.py --write`): 168 code gates (165 Python, 3 shell), 8 data gates, 42 external writers.

## Gates

Run one at a time in the foreground; the tallies are in the report.

**The paste's eight:**
- `validate_item_116`
- `validate_security_master`
- `validate_batch14_b1`
- `validate_stack` (the daily stack has no positioning group, so it ran whole)
- `validate_weekly_stack --group E`
- `check_registry`
- `validate_gates`
- `check_library`

**Also run, because this branch touches what they read:**
- `validate_packets`
- `validate_alpha_lab_3`
- `validate_deploy`
- `validate_systemd_units`
- `check_master_guide`
- `validate_official_sources`
- `validate_config_refs`
- `validate_audit_3a`
- `validate_secrets`
- `validate_backups`
- `validate_weekly_stack` (whole)
- `validate_weekly_edits` (Positioning's sub-sections are now thirteen)
- `validate_monthly_stack` (the Monthly reads the close-flow table with no written read)
- `validate_monthly`
- `validate_weekly_complete`

The full suite was also run once as a sweep.

## Not in this paste

- **98.2:** the calibration ledger through the round-7 event-study utility, and its two seed rows (5 Jun and 5 Nov 2026, by hand).
- **The CLAUDE.md paragraph** for item 116: CLAUDE.md is not in this paste's shared files beyond the counts, so it is left for the chain-13 stitch.
- **6b's dealer-hedging estimate:** not wired, so the combined line waits for it.

## Needs you

1. **Enable the 15:00 timer** on the box after chain-13's merge, inside a window: `systemctl --user enable --now chester-close-flow.timer`. A session never runs unit commands. Until it is enabled the close prints "the 15:00 close-flow estimate" as not stored, and the flag cannot fire.
2. **MSTR, COIN and SNDK are not in the price basket**, and D33 admits no new Yahoo symbol. MSTU, MSTZ and CONL (about $1.07bn of AUM) are stored and named, but not estimated, until the price-source migration (A93's IBKR writer) carries those names. Should they wait for it, or should a D33 exception be ruled?
3. **% of ADV for the index buckets** is the ETF's dollar volume, not the constituents'. The semiconductors bucket therefore reads large percentages against SMH. The flag's switch is unaffected, since it uses the box's own history in the same units. Keep this, or rule a constituent-based ADV?
4. **Tradr is a gap** (SNXX, TSLQ): no keyless figure, and the aggregator's terms forbid automated reads. Leave it as a gap, or rule a by-hand line (rule 3 needs your explicit yes)?
5. **The roster misses MS's wider universe.** The recomputed $5.3bn per 1% is the roster's own figure; MS's universe is wider. The floor ($500m) is session-set and can be lowered in the config if you want more of the long tail.
