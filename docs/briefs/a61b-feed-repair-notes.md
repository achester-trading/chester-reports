# A61b: the feed repair before the Monthly (session A)

**Branch-only, cut from main so it can merge on Tue 27 Oct**, before the Monthly's last dry run (Wed 28) and the deploy freeze (Thu 29, 23:30). Repairs only: no new feature and no new source.

## Base and commits

- **Base:** `a61b-feed-repair` from `origin/main` at `4180398` ("Merge pull request #41 from achester-trading/chain-5").
- **Worktree:** its own, `../chester-a61b` (`../chester-a57` was still on `a61-rulings-1024`).

| Commit | What |
|---|---|
| `1f6c2ad` | Items 1–4: FRED's non-JSON path, `http_get_json`'s headers, StatCan, the two voices feeds. |
| `16cfe56` | Items 5–8 and the gate: the refusals, the declared statuses, the dead keys, inheritance, the ten families, `tools/validate_feed_repair.py`. |
| (this) | These notes. |

**The evidence.** `C:\Users\arich\Downloads\feed-errors-2026-10-24.txt` (150 lines, read first) and the store check's stale list, summarised in the paste. No stale-list file was in Downloads, so the summary is the evidence for item 6.

**Probes.** One keyless request per source from the laptop, robots.txt first, with the repo's standard User-Agent. None retried. They covered StatCan, Yahoo Finance, DefiLlama, Yahoo's PRL pair and one ZQ contract.

## The items

| # | Item | Verdict | Cause found | Fix, or why it is a gap | Evidence |
|---|---|---|---|---|---|
| 1 | FRED non-JSON (about 15 series on one run) | **fixed** | FRED answered with a body that was not JSON on the day the 1.9m-row ALFRED history ran beside the 16:10 pull. Together the pull (0.4 s pauses, up to 150 a minute with no latency) and the history (0.6 s, 100 a minute) could reach about 250 a minute against FRED's 120: most likely a rate-limit page. | See the details below the table. | The log lines; `altdata/sources/fred.py` `PACING_SECONDS` 0.4 before |
| 2 | edgar_xbrl `TypeError: ... unexpected keyword argument 'headers'` | **fixed** | No merge removed anything. `http_get_json` has never taken `headers` (unchanged since `08386f7`, 30 May). Callers written later assumed it: `edgar_xbrl` (GTM part 2 `ae09e15`, 17 Oct; ST-4 `18ec03d`, 18 Oct), `altdata/sources/gt.py` and `treasury.py`. `edgar.py` worked around it with `_accepts_headers()`. | The helper now takes `headers`, as every other helper in `_base.py` does, and sends the project User-Agent by default (it sent none before). All four callers work unchanged, and the gate checks that every caller passes only keywords the helper takes. The SEC contact still comes from CHESTER_SEC_CONTACT at run time, through `edgar.user_agent()`, unchanged. | `git log -S"def http_get_json"` |
| 3 | statcan_cpi `JSONDecodeError` | **fixed in part; the cause on the box is unverified** | The laptop's one probe of the writer's own URL that day was HTTP 200 `application/json` with both vectors, September 2026 released 19 Oct. robots.txt has no rule over `/t1/wds/`. The 16:10 pass is outside the service's overnight window. So the box receives something the laptop does not, and the laptop cannot see what. | The writer refuses a non-JSON body by name (its Content-Type and its first 120 characters) and asks for `Accept: application/json`. The next box run's STALE reason will say what the box was sent. The box sheet has a one-line check. | The probe; `altdata/sources/statcan_cpi.py` `load()` |
| 4a | yahoo_finance voices feed, HTTP 404 every run | **gap** | `finance.yahoo.com/news/rssindex` answers 404. The one candidate probed, `/news/rss`, is 404 too, and no other public RSS path was found. | `enabled: false` with its `unreachable_reason`; `validate_voices` updated. | The log extract (13 runs) and the probe |
| 4b | troweprice_insights `TimeoutError` | **fixed, once** | The listing page did not answer within the scan's 25 s. | `timeout_seconds: 60` for that host only (a per-source field the scan now reads). If it still times out, the next step is `enabled: false` with that reason. | The log extract |
| 5a | mba, HTTP 403 on its own robots.txt | **refused** | The site refuses automated reads. | See "The refusals" below. | The log extract |
| 5b | rent_indices, HTTP 403 from apartmentlist.com | **refused (Apartment List); Zillow repaired** | The 403 came from the Apartment List leg, but the writer went STALE whole, so **Zillow's ZORI stopped too**. | Apartment List is no longer requested and `aptlist.rent_us` is declared refused. Zillow is read alone and should resume on the next run. | The log extract |
| 5c | farside, HTTP 403 (Cloudflare "Just a moment") | **refused** | A Cloudflare challenge on `/btc/` and `/eth/`. | Declared refused in `source_registry.yaml`, with its date and the status seen. The ETF-flow lines (`crypto_blocks.etf_line` and `_etf_daily`, the addendum's decomposition, the evening note) print the gap. | The log extract |
| 6a | lbma.gold_pm_usd (newest 29 Sep) | **superseded** by `yfinance.mkt_gold_front` | Off the roster since 9 Oct (A-4: the JSON answers 403, robots.txt 401). The key still said `not_yet_sourced`, which the store check did not skip. | `member_overrides`. | `altdata/feeds.py` comment; `lbma.py` docstring |
| 6b | overnight.tnx_chg, _chg_pct, _prior_settle (22 Sep) | **superseded** by `yfinance.mkt_tnx` | `^TNX` prints in US cash hours only. At the 06:45 read its newest bar is the prior settle bar, so since 23 Sep (the "a market that did not trade did not move zero" rule) the change fields are omitted by design. `overnight.tnx_last` is still written. | `member_overrides`. | `altdata/sources/overnight.py`; the log's `^TNX -> mkt_tnx` lines |
| 6c | bars.cnh, eth, hsi, kospi, n225, nq, rty, sse, usdjpy (21 Oct) | **not a gateway fault; needs a box look** | These are the secondary notes' `note_bars`, fetched only by `python -m altdata.note_fetch evening` in `chester-evening-note.timer` (21:30 ET, Sunday to Thursday, enabled by hand). They come from Yahoo, not IB Gateway. Newest bars on 21 Oct mean Thursday 22 Oct's run wrote nothing; with no runs on Friday or Saturday, that is **one missed run** as of 24 Oct, not a dead feed. The cause is not in the log extract. | Nothing guessed. The box sheet's evening-note lines say what to look at. | `altdata/bars.py` `note_instruments`; `deploy/systemd/README.md` "The secondary notes" |
| 6d | llama.fees, revenue, holders_revenue, tvl `_aero` (17–19 Oct) | **gap (held)** | DefiLlama merged Aerodrome and Velodrome into the parent `aero` ("Aero"; previous names Aerodrome, Velodrome, Aero Protocol) at the 21 Oct launch. The slug `aerodrome` now serves the merged protocol's history back to 2022, through 22 Oct. Storing it would restate AERO's whole history with Velodrome in it. | `llama_hold` in `config/crypto_basket.yaml`, so the writer asks nothing for AERO; the four keys are declared `gap`. Needs-you 3 rules it. | The probe (`/summary/fees/aerodrome`: name Aero, 1,607 points, last 2026-10-22) |
| 6e | mempool.difficulty (16 Oct) | **fixed (registry)** | Not dead. The difficulty is set every 2,016 blocks (about 14 days), one row per adjustment, but it was registered with a session half-life (2 sessions). | Weekly cadence, `until_next_release`, plus the `btc_difficulty` lag (4, bound 5): 12 sessions. | `altdata/sources/mempool.py` docstring; the log's 19 rows a day are hashrate and fees |
| 6f | crypto.total_market_cap_usd, zec.crypto_cap_share (16 Oct) | **gap** | Retired **13 Oct** (not 6 Oct) by the ruling on CoinGecko's terms. No keyless source with vintages serves the total. | Declared `gap` with the reason. | `altdata/loggers/shielded.py` |
| 6g | yfinance.crypto_prl, _volume (18 Oct) | **gap, still requested** | Yahoo serves no `PRL41876-USD` bar after 18 Oct (the probe of 24 Oct, 15 days asked). That is a vendor hole, not a refusal or a delisting notice. | Left requested so it heals if Yahoo resumes; **expected to stay stale**. | The probe |
| 6h | fedfunds.futures_price (20 Oct) | **cause probable, not verified; needs a box look** | Yahoo serves `ZQX26.CBT` daily through 23 Oct (the probe), so the source works. `fed_funds` is the **last** feed in `altdata/feeds.py` `FEEDS`, and `run_eod_cron.sh` caps the feeds pull at 12 minutes (`timeout 12m`). If the pull ran past 12 minutes after the 20 Oct merges grew the FRED list and the writers, `fed_funds` is the one cut. The log extract does not show the cap line. | Nothing reordered. The box sheet greps for the cap; needs-you 2. | `scripts/run_eod_cron.sh` line 176; the probe |
| 7a | fred.ioer (newest 2021-07-28) | **superseded** by `fred.iorb` | Discontinued 28 Jul 2021. | `member_overrides`. It is still in the bank-stress pull list: removing it would move the FRED count pins chain-6 also moves. | `altdata/config.py` |
| 7b | fred.mmf_retail (31 Aug; registered weekly) | **fixed (lag)** | WRMFNS is weekly data published in H.6, once a month, about four weeks after the month: on 24 Oct the newest week was 31 Aug. | Family `fred_h6_weekly`, lag 34 (bound 37): 42 sessions. | The store check's date |
| 7c | portfolio.position_* (1–2 Oct) | **declared `while_held`** | Written only while a position is held; a flat paper book writes none. | Six keys declared; the store check and the heartbeat roster read the declaration. | — |
| 7d | calc.infl_vol | **unchanged** (ruled D3) | — | — | — |
| 8a | Inheritance | **fixed** | Derived keys did not inherit their inputs' lag: `calc.naive_expectation.core_pce` was allowed 54 sessions, `calc.surprise_vs_naive.core_pce` 32. | See the details below the table. | `validate_feed_repair` group F |
| 8b | Monthly sources outside FRED | **ten families added; four sources listed** | No lag family. | See the list below. | `validate_feed_repair` group G |

**Item 1, the FRED repair.** In `altdata/sources/fred.py`, `get_json`:
- records the HTTP status and the first 120 characters of the body;
- retries up to three attempts in all, with a doubling backoff, honouring Retry-After capped at 60 s;
- does not retry a 4xx other than 429;
- then fails with the status in the reason.

The pull marks the series failed. `feeds.pull_fred` records it STALE with the reason, which before was only logged, so each series read "attempted, nothing written". The run logs **one** summary line, with tracebacks at DEBUG only.

Pacing is now start to start: a request starts at least 0.55 s after the last, so at most about 109 a minute, and it sleeps only the part of the interval the request did not take. A slow night is not made slower, which matters because of the 12-minute cap (6h). The ALFRED history reads through the same fetch, with its own 0.6 s.

**Item 5, the refusals.** `source_registry.yaml` now carries `status: refused`, `refused_since` and `refused_seen` for MBA and Farside. Apartment List is the rent writer's leg, declared on its key. Each pull returns REFUSED **with no request**, and `feeds.writer_failures` counts REFUSED as no failure of the run. The readers print "not tracked: <source> refuses automated reads since 2026-10-24 (<status>)": the MBA line (`st_r5_rates.mba`) and every ETF-flow line. The helpers are `altdata/refusals.py`, which is not a writer, so a report may import it (the import rule in `validate_official_sources`).

**Item 8a, how inheritance works.** A derived key's allowance takes the largest publication lag among its own family and its declared inputs (`derived.inherited_lag`). Inputs are declared three ways:
- `inputs:` on twelve features: the eight `calc.yoy_*`, `calc.real_wages_yoy`, the two `calc.r_real_10y_*` and `calc.real_policy_rate`;
- `member_inputs: ["fred.{member}"]` on the `naive_expectations` and `surprise_vs_naive` blocks (59 surprise keys);
- `member_inputs_from: altdata.correlation.member_inputs` on the three correlation blocks.

`calc.surprise_vs_naive.core_pce` is now 54 sessions; the daily FX surprises take H.10's lag (8), and Brent, WTI and natural gas EIA's. All 62 `corr.*` keys with natural gas take EIA's 6 (7 sessions).

**Item 8b, the families and the gaps.** Ten families are added, each with its source, its documented lag and a bound, under b51's rule:

| Family | Lag (bound) |
|---|---|
| Canada CPI | 24 (26) |
| Japan CPI | 24 (27) |
| UK CPI | 23 (25) |
| Thailand CPI | 18 (20) |
| ECB IRS | 23 (25) |
| Redfin | 19 (22) |
| NY Fed SCE | 18 (21) |
| Census VIP | 33 (35) |
| H.6 retail money funds | 34 (37) |
| Bitcoin difficulty | 4 (5) |

Four sources are **listed, not given a lag**, because neither the writer nor its source check states a quantified delay, and b51's rule forbids choosing one:
- the Tuck data library (`french.*`);
- EIA's rig counts (`eia.rigs_*`);
- the Cleveland Fed rules (`clevfed.rules_*`);
- the Shiller workbook's dividends and earnings (`shiller.sp_dividend`, `shiller.sp_earnings`; "lag the price by months").

A key still stale after this is a fault and is listed (the box sheet).

## Where the paste and the code differ

1. **The CoinGecko date.** CoinGecko's total and ZEC's share retired on **13 Oct** (`altdata/loggers/shielded.py`), not on 6 Oct as the paste expected.
2. **The bars source.** `bars.*` are Yahoo bars written by the evening note's fetch, not an IB Gateway feed. The gateway's state does not bear on them.
3. **fred.ioer.** It is declared superseded, not removed from the pull. Removing it would move the FRED counts that chain-6 moves too, a stitch conflict for no gain.
4. **The voices timeout.** It is a new per-source field, `timeout_seconds`, read by the scan per host. The paste asked for "raise its timeout once", and the scan had one global timeout.

## The gate

`tools/validate_feed_repair.py`, a new gate rather than an extension of `validate_b51_registry_html`: the repair spans seven writers and the store check, so it is cleaner on its own. **36 checks**, groups A–G as its docstring lists:
- A: the non-JSON path to STALE on a fixture;
- B: the edgar call on a fixture, and every caller's keywords;
- C: StatCan's non-JSON body and a JSON parse;
- D: a refused source never requested, and the gap text;
- E: a declared key never stale, and the repair's declarations in force;
- F: inheritance taking the largest input lag;
- G: every new family with its source, reason and lag within bound.

It is registered in the Makefile after `validate_b51_registry_html`, and CLAUDE.md's line is recounted on this base: **134 code gates (131 Python, three shell)**, from main's 133 (130, 3). `validate_audit_3a` passes on the recount.

**Gates touched by the repair and updated:**
- `validate_voices`: Yahoo disabled, T. Rowe Price's 60 s.
- `validate_official_sources` and `validate_digital_addendum`: they set an empty refusal registry so their fixture tests still exercise the MBA and Farside parsers; the refusal is held by the new gate.
- `validate_st_r5_rates`: MBA's status is now `refused`; it sets the same override for its parser tests.

**Local runs:**

| Gate | Result |
|---|---|
| validate_feed_repair | 36 / 0 |
| validate_b51_registry_html | 25 / 0 |
| validate_voices | 73 / 0 |
| validate_official_sources | 340 / 0 |
| validate_st_r5_rates | 72 / 0 |
| validate_digital_addendum | 94 / 0 |
| validate_secondary_notes | 88 / 0 |
| validate_feeds_scheduled | 19 / 0 |
| validate_fred_history | 25 / 0 |
| validate_backups | 29 / 0 |
| validate_audit_3a | 88 / 0 |
| check_registry | OK |
| check_library | 27 papers, 0 failures, 0 warnings |

## The CI run

| Run | On | Result |
|---|---|---|
| read once after the push | the branch tip | see the report |

## Files shared with chain-6

`CLAUDE.md` (the gate line), the `Makefile` (one line), `altdata/feeds.py`, `altdata/sources/voices_scan.py`, `altdata/st_r5_rates.py`, `config/voices_sources.yaml`, `daily_cascade/digital_addendum.py`, `metrics_registry.yaml` and `source_registry.yaml`.

**The stitch will meet:**
- the gate count: chain-6's line plus one;
- `voices_sources.yaml`: chain-6 adds FXEmpire and edits the Apollo `not_used` line; this branch edits Yahoo and T. Rowe Price, different blocks;
- the registry: this branch adds `member_overrides` before `forward_dated:` and `inputs:` lines on twelve metrics;
- `source_registry.yaml`: the MBA and Farside blocks.

## The box sheet (Tue 27 Oct evening, after the merge, inside the windows)

These are the operator's commands. Dry runs first.

```
cd ~/chester-reports && git log --oneline -1          # the merge is on the box
# 1. FRED: one series through the new fetch (read-only print of the summary)
.venv/bin/python -c "from altdata.sources import fred; from altdata.store import Store; from altdata import config; s=[x for x in config.FRED_PULL_SERIES if x.key=='gdp_deflator']; print(fred.pull(Store(), series=s))"
# 2. EDGAR's frames (needs CHESTER_SEC_CONTACT, unchanged)
.venv/bin/python -m altdata.sources.edgar_xbrl --dry-run 2>&1 | tail -5     # or its pull, if it has no dry run
# 3. StatCan: what the box is sent (the STALE reason now names it)
.venv/bin/python -m altdata.sources.statcan_cpi 2>&1 | tail -5
# 4. Rents: Zillow alone
.venv/bin/python -m altdata.sources.rent_indices 2>&1 | tail -5
# 5. The refused writers ask nothing (REFUSED, no request)
.venv/bin/python -m altdata.sources.mba 2>&1 | tail -3
.venv/bin/python -m altdata.sources.farside 2>&1 | tail -3
# 6. The voices scan, two sources only, no model
.venv/bin/python -m altdata.sources.voices_scan --only troweprice_insights --no-model 2>&1 | tail -5
# 7. Why fed_funds stopped (the 12-minute cap?) and the evening note on 22 Oct
grep -n "hit its 12-minute cap\|fed_funds: served" ~/chester-data/logs/eod*.log | tail -10
grep -n "evening_note\]" ~/chester-data/logs/evening_note*.log | tail -10
systemctl --user list-timers chester-evening-note.timer
# 8. Then the store check
.venv/bin/python -m tools.check_store_registry --db ~/chester-data/chester.db
```

Paths to the logs are the box's own (`deploy/systemd/README.md` names them). Where a command takes no `--dry-run`, it writes only what its writer writes on the 16:10 pass.

**The stale count expected after the merge and one 16:10 pass: about 100, from 280, a range of 80 to 130.** It cannot be exact from the laptop without the store's list. The reductions:

| Change | Keys |
|---|---|
| Declared by this branch | 24 |
| Inheritance: corr.\* with natural gas | 62 |
| Inheritance: surprise_vs_naive and the yoy, real and r_real keys, the stale share of them | about 30 |
| The ten new families | 26 |
| FRED's 15 series, if FRED answers | 15 |
| EDGAR's features | about 6 |
| StatCan, if the box gets JSON | 2 |
| Zillow | 1 |

**Expected to remain stale, and why:**
- `french.*`, `eia.rigs_*`, `clevfed.rules_*`, `shiller.sp_dividend` and `shiller.sp_earnings`: no documented lag (8b).
- `yfinance.crypto_prl` and `_volume`: Yahoo's hole (6g).
- `bars.*`: until the evening note runs again (6c).
- `fedfunds.futures_price`: if the cap is the cause (6h).
- `ca.cpi_*`: if the box still receives a non-JSON body (3).
- `calc.infl_vol`: D3.
- The bookkeeping keys this branch did not touch: the rest of the 280 the paste called "most are bookkeeping".

## Also seen in the log, outside this paste

The 24 Oct 10:35 heartbeat reads `verdict=unit_failed rc=13 ... backup=failed:partial disk=warn:70% units=failed:chester-ba...`. The backup unit failed partially, and the disk is at 70%. **Not touched here** (no units); listed for the operator.

## Needs you (at most five; yes or no each)

1. **Merge on Tue 27 Oct inside the windows, then the box sheet above?** Yes / no.
2. **If the eod log shows the feeds pull hitting its 12-minute cap, move `fed_funds` ahead of `prediction_markets` in `FEEDS` (or raise the cap) as a one-line follow-up?** Yes / no.
3. **AERO after DefiLlama's merge:** follow the merged parent `aero` from 21 Oct as a labelled break, or keep the four keys a listed gap? Follow / gap.
4. **Yahoo Finance's voices feed stays disabled** (no public feed found)? Yes / no.
5. **Lags for the Tuck library, EIA's rig counts, the Cleveland Fed rules and the Shiller workbook's earnings:** have a session look up each publisher's stated delay before a family is written? Yes / no.
