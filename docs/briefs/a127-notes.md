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


## A127b: the five rulings on the needs-you (D66, 6 Nov 2026, 16:46 ET)

Base `37c80ce9` (the branch's tip, as expected); paste `docs/pastes/A127b.md`.

**Ruling 1, the 15:00 timer.** Nothing built. See the box steps below.

**Ruling 2, no Yahoo exception (D33 stands).**
- MSTR's and COIN's spot now come from the captured option chains, through item 49's read, `altdata/sources/treasury.py` `chain_spot`.
  - That function gained one optional argument, `at_or_before`, so a reader as of a cutoff never sees a later capture. Item 49's own call passes none and behaves as before.
- The return is the session's newest chain at or before the estimate's instant against the previous session's newest chain. That is the chain's spot, not the official close, and the price record says so.
- MSTU, MSTZ, CONL and the new MSTX rejoin both estimates on that spot.
- At 15:00 the newest chain is normally the 12:30 capture. A chain older than 180 minutes at 15:00 (session-set, `chain_spot.max_age_minutes_1500`) leaves the fund out, named.
- MSTR and COIN have no stored volume, so they are in no `adv` list. The single-stock bucket's ADV is its stored names'.
- **SNDK has no chain.** Its underlying carries `gap: no keyless price`, which prints on its one fund, SNXX. SNXX is also a Tradr AUM gap. It waits for the price migration.

**Ruling 3, % of ADV against the ETF's own dollar volume.** Kept. The reason is written beside the `buckets` field in `config/levered_etf.yaml`.

**Ruling 4, Tradr stays a gap.** No by-hand line. The config's Tradr comment says why: no figure or file on the page, the aggregator's terms, and rule 3.

**Ruling 5, the floor drops from $500m to $250m.** It is session-set and dated in the config (`aum_floor_set`). Six funds clear it. All six were read live on 6 Nov through the same writer, each at the 5 Nov close:

| Fund | Issuer | L | Underlying | Bucket | AUM, 5 Nov | Id |
|---|---|---|---|---|---|---|
| NVDU | Direxion | 2 | NVDA | single stocks | $0.321bn | SM00241 |
| MSFU | Direxion | 2 | MSFT | single stocks | $0.353bn | SM00242 |
| METU | Direxion | 2 | META | single stocks | $0.311bn | SM00243 |
| AMZU | Direxion | 2 | AMZN | single stocks | $0.284bn | SM00244 |
| NVDX | REX | 2 | NVDA | single stocks | $0.268bn | SM00245 |
| MSTX | Defiance | 2 | MSTR (chain spot) | single stocks | $0.255bn | SM00246 |

- `next_id` is now 247.
- MSFT, META and AMZN were already in the price basket (`yfinance.mkt_*`), so no new Yahoo symbol was added.
- MSTX is the first Defiance fund. The writer gained a `defiance_page` method, which reads the page's "Data as of" date and its "Net Assets". Defiance's robots.txt disallows only its fund-document uploads.
- NVDX's page reads $0.268bn as of 5 Nov. A127's note gave $0.317bn, presumably an earlier day's figure.
- PLTU ($0.223bn) and the rest stay below the floor, each listed in the config's `excluded`.
- The roster is now 38 funds: 36 read and 2 Tradr gaps.

**V-98c, recomputed** from the issuers' 5 Nov figures:

| | A127 ($500m floor) | A127b ($250m floor) |
|---|---|---|
| Funds read | 30 | 36 |
| Roster AUM | $98.1bn | $99.75bn |
| Dollars per 1%, every underlying | **$5.30bn** | **$5.33bn** |
| Dollars per 1%, index funds only | $5.14bn | $5.14bn |
| Single-stock bucket | $0.15bn | $0.19bn |

The long tail adds about $0.03bn per 1%. The gap to MS's universe is not the floor.

**Gates**, one at a time:

| Gate | Result |
|---|---|
| validate_item_116 | 68/0 (gains the chain-spot path, the floor and the Defiance parser) |
| validate_security_master | 102/0 |
| validate_batch14_b1 | 68/0 |
| check_registry | OK |
| validate_gates | 32/0 |

Also run, since `chain_spot` is item 49's:
- validate_digital_addendum: passed;
- validate_crypto_sources: passed.

### Box steps (the operator's)

1. **The 15:00 timer.** D66 ruling 1 sets it for Monday 9 Nov, after chain-13's merge and deploy, inside a window:
   `systemctl --user enable --now chester-close-flow.timer`

### For the price migration

- SNDK (SNXX's underlying): "gap: no keyless price".
- MSTR and COIN read the chain spot until the migration carries them. Their funds then move to stored closes and enter the bucket's ADV.

**CI.** A127's run 42280039981 failed on one check: `validate_numeral_audit`, 180/1. `close_flow.py`'s flag line wrote an ordinal suffix by hand ("60th"), and its private `_ord` duplicated the one helper. Both now go through `numeral_audit.ordinal()`, and the gate reads 181/0. The fix is committed after A127b's push, so A127b's own run fails the same way. The fix rides A128's push.


## A128: item 116's ledger (98.2) and item 118 (the order's 100)

Base: the branch at `11e946b9` (A127b's pushed tip). Two local commits sat on it: A127b's ordinal fix `86a5af08` and the paste `679aa1eb`. The pre-registrations are `14a343a6`, committed before any code.

### The two missing tools, and the ruling

A128 says to use round 7's event-study utility (Batch 16 item 91(a)) and to add SPHB/SPLV as a member of the crowding-unwind gauge (89(a)), building no second utility. **Neither existed** on main or on any remote branch. Both sit in Batch 16's Tranche B ("after 8 Nov; Audit #5 places").

Asked mid-run, the operator chose to build 91(a) first, then A128, with 89(a) left unbuilt:
- **91(a), built as the one utility.** `altdata/event_study.py` does what Batch 16 lists: ±N windows in sessions, the pre / day-0 / post views, forward returns that print "pending" past the series' end, cross-event averages, the base rate and the two-asset comparison. It is pure arithmetic: no store, network or clock import. Gate group H holds every function by hand, and fails on a second window/views/forward implementation under `altdata/`.
- **89(a), not built.** `config/crowding.yaml` declares the family with `gauge.built: false` and one member, `hb_lv`. 89(a)'s gauge adopts the members when it lands. Until then the member prints only its flag line.

### The pre-registrations (SHA-256 of the LF bytes, held by the gate and the configs)

| File | SHA-256 | Held in |
|---|---|---|
| `docs/ledgers/close-flow-preregistration-2026-11.md` | `2e55de27a48183fc7ba752be94d11b035a735f1402928eb439233580124cd68f` | `config/levered_etf.yaml` `ledger`, gate group I |
| `docs/ledgers/hb-lv-divergence-preregistration-2026-11.md` | `cdadf38f9f3a45732a38a068453d4a912fc0a18116c1222199a3a569cb05de84` | `config/crowding.yaml` `members.hb_lv.ledger`, gate group J |

### Part 1: the close-flow ledger (98.2)

`altdata/ledgers/close_flow_116.py` runs on `python -m altdata.ledgers run close-flow`, through the utility.

**The event.** A stored 16:45 session whose |total % of ADV| is in the top decile. Below 20 stored sessions the ledger prints "accruing (n=k of 20)". Each event is measured on its largest index bucket's ETF (SMH, QQQ, SPY or IWM) and on SPY: the last 30 minutes (5-minute bars), the gap at the next open, +1 and +5.

**The first edition** is `docs/ledgers/close-flow-ledger-2026-11-06.md`, a laptop run on public sources. The close-flow history lives only in the box's store, so the edition reads "accruing (n=0 of 20)" with no event and no pass rule ("none stated").

**The seed rows, as written** (judgment drafts for the operator's accept-all, rule 31; returns from Yahoo):

| Row | Session | Flow | Marked | Index | Last 30 min | Next open | +1 | +5 | SPY last 30 | SPY next open | SPY +1 | SPY +5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-06-05 | -$55.0bn | seed, order's figure | SPY | not available | +0.79% | +0.23% | +0.57% | not available | +0.79% | +0.23% | +0.57% |
| 2 | 2026-11-05 | -$52.0bn | seed, order's figure; estimate, unconfirmed (V-98a open) | SMH | -1.22% | +5.74% | +3.62% | pending | -0.28% | +0.25% | +0.31% | pending |

- 5 Jun's last 30 minutes are "not available": Yahoo serves 5-minute bars for 60 days only.
- 5 Nov's index is SMH, the order's largest named bucket ($21bn). On 6 Nov SMH opened +5.7% after −11.2% on 5 Nov. Both rows' next open ran against the flow.
- V-98a stays open.

### Part 2: item 118

**SPHB and SPLV join the basket.** SM00247 SPHB and SM00248 SPLV (Nasdaq Trader's listing, ARCX) are in the Security Master with `yahoo`, `store_key` and `ticker`. `next_id` is 249. Both are in `yfinance_source.SYMBOLS` and resolve through `resolve_basket`. The basket is now 129 symbols, and the registry's member counts are 129 and 99. Both need a price backfill on the box (box steps).

**D33 and this paste.** D33 admits no new Yahoo symbol, and D66 ruling 2 kept it an hour earlier. A128 names these two symbols explicitly, and the order itself says "through the existing yfinance fetcher". I took A128 as the operator's explicit exception, for these two symbols only.

**The member.** `altdata/hb_lv.py` writes `calc.hb_lv_ratio` (SPHB over SPLV) and `calc.hb_lv_ratio_chg_1d` (percent), source `hb_lv`.
- It runs in the market-features pass over recent sessions; `compute --full` writes the history.
- Each row is available at the later of its two closes.
- Both keys are registered (mechanism group `crowding`, new to the vocabulary) and barred from the market-state object.

**The flag.** The S&P 500 up 0.5% or more while SPHB/SPLV is down 2% or more, defined once (`hb_lv.flag`) and used by both the close and the ledger. `daily_cascade/hb_lv_block.py` prints one line in the close's What doesn't fit, on a fired day only, with both figures and "No rights until the backtest". It is read from the stored closes, so it does not wait on the features pass.

**V-100a holds** on the public series: on 4 Nov the S&P 500 closed **+1.58%** (7,568.92 → 7,688.62) and SPHB/SPLV **−2.73%**. The order's first row is written, marked "the order's day (V-100a checked)". It is the backtest's own event for that session, not a second copy.

**The backtest** (first edition, `docs/ledgers/hb-lv-divergence-ledger-2026-11-06.md`; no pass rule set): **n = 9 events** from 6 May 2011 to 6 Nov 2026, over 3,900 sessions screened. All nine fall in 2020 or later. Three overlap the event before them.

| Horizon | Events: n | Mean | Median | Share negative | All sessions: mean | Share negative |
|---|---|---|---|---|---|---|
| +1 | 9 | −1.40% | −1.00% | 67% | +0.05% | 46% |
| +5 | 8 | −0.29% | +0.97% | 38% | +0.25% | 40% |
| +20 | 8 | +2.81% | +4.56% | 12% | +0.99% | 33% |

The next session is weaker than the base rate (6 of 9 down), and the 20-session window is stronger. With n 9, three of them overlapping, this is recorded, not read.

### Gates (one at a time, foreground)

| Gate | Result |
|---|---|
| validate_item_116 | 105/0 (groups H, I and J added) |
| validate_ledgers_b6 | 41/0 |
| validate_security_master | 102/0 |
| validate_stack (whole: its groups are letters, with no what-doesn't-fit or positioning group) | 84/0 |
| check_registry | OK |
| validate_gates | 32/0 |
| check_library | 27 papers, 0 failures, 0 warnings |

Also run:
- validate_audit_3a 88/0 (after `altdata.hb_lv`'s catalogue line);
- validate_numeral_audit 181/0;
- validate_config_refs 149/0;
- validate_official_sources 383/0;
- validate_weekly_complete 96/0.

**Counts** (`stitch_counts.py --write`): 168 code gates (165 Python, 3 shell), 8 data gates, 42 external writers, 129 yfinance symbols (was 127).

### Box steps (the operator's)

1. After chain-13's merge, backfill the two new symbols, dry run first:
   `python tools/backfill_prices.py --symbols SPHB,SPLV --dry-run`, then without `--dry-run`.
2. Write the ratio's history: `python -m altdata.hb_lv compute --full --dry-run`, then without.
3. Each ledger's box re-run reads the store: `python -m altdata.ledgers run close-flow --source store` and `python -m altdata.ledgers run hb-lv-divergence --source store`. They apply the first editions' "none stated" and may not change it.
4. From A127b: `systemctl --user enable --now chester-close-flow.timer` on Monday 9 Nov, inside a window.
