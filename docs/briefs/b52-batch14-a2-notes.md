# b52-batch14-a2: signal triage Batch 14, Part A2 -- items 63 and 66 (session B, 21 Oct 2026)

**What it is.** Two of Part A's 1 Nov Monthly candidates, from the Batch 14 order (ruled 20 Oct 2026 with filing amendments F1 to F8):
- **Item 63,** the AI capex chain (written as 56);
- **Item 66,** the transmission mechanisms (written as 59), with its ledger.

Section 0 governs. Its F1 table translates every number; the order's items 52 and below keep theirs, so "items 34, 36, 41" are Batch 6's and "item 26" is ST-R4.26.

**Branch.** `b52-batch14-a2`, from main's tip `f9ec9e3` ("Merge pull request #40 from achester-trading/chain-3"), in its own checkout (`../chester-reports-b52`). It merges on its own. When chain-4 is on main, main merges into it with a merge commit, the gates are recounted, and it is pushed.
- **Branch only:** pushed, not merged, not deployed, nothing run on the box, no unit touched.
- **Read only:** chain-4, a54-relative-volume, a55-box-fixes and b51-registry-html. a56-batch14-a1 was not on origin when checked.
- **Not touched:** the order's filing and its indexes (session A's), and chester-meme.
- **Timing:** green and ready to merge by Saturday 24 Oct, before the Monthly's last dry run on 28 Oct.

**The specification** is `C:\Users\arich\Downloads\change-order-signal-triage-batch-14-2026-10-20.md`, read in full first. Where it and the code differ, the code wins; every difference is listed below.

## Part 1: the source checks (run 21 Oct 2026, from the laptop, before building)

Section 5 lists no check for items 63 or 66, so in F7's spirit:

| # | Check | Result |
|---|---|---|
| 1 | A free, keyless price source for each of item 63's proxies | **Passes**, Yahoo through the basket's own reader. Daily history: SMH from 2000-06-05; SOXX from 2001-07-13; MU from 1984; AMD from 1980; GRID from 2009-11-17; ANET from 2014-06-06; VRT from 2018-08-02; PAVE from 2017-03-08; ASML from 1995. All have five years. NVDA, AVGO and XLU are already in the basket |
| 2 | Z.1's household equity share | **Passes, already stored** for item 30: `fred.hh_equity_share` (FRED `BOGZ1FL153064486Q`). The public graph CSV serves it quarterly from 1945-10-01; the newest on 21 Oct is Q2 2026 (dated 2026-04-01) |
| 3 | ICI's allocation proxy between Z.1 releases | **Fails the standing rule.** www.ici.org answers HTTP 403 to the project's generic User-Agent on robots.txt and on its statistics pages (`/research/stats/combined`, `/research/stats/flows`), as a53 found on 20 Oct. A writer never passes for a browser, so it is a **listed gap**. Its keyless stand-in is below |
| 4 | Real consumption from FRED | **Passes:** keyless graph CSV. `DPCERA3M086SBEA` (real PCE, quantity index, monthly from 1959), `PCEC96` (chained dollars, from 2007) and `PCECC96` (quarterly, from 1947). The ledger reads `DPCERA3M086SBEA` for its depth. The store holds none of them, and nothing else needs one |
| 5 | F4: a public page for JDI Research | **Passes.** www.jdiresearch.com's robots.txt allows / for every agent bar PetalBot. Its blog serves an RSS feed (`/blog-feed.xml`) with dated items (newest 19 Oct 2026) without a login. The HTML blog renders its links client-side, so the feed is the source |

## Item 63: the AI capex chain

**The reference table** (`config/capex_chain.yaml`, `reference`): BNP Paribas's illustrative $100 of AI capex, dated August 2026. It has its source line ("as published by a16z") and BNP's own caveat (high-level estimates).
- **The buckets:** semis $50 (accelerators 25, memory 15, CPUs and server production 10); power $20 (grid and independent generation 10, distribution 6.5, on-site routing 3.5); networking $15; cooling $7.5; facilities and construction $7.5.
- **The memo line:** wafer-fab equipment about $8 inside semis, roughly half of it lithography.
- **Where it prints:** in the Monthly's slow layers as Factor I's exhibit, "Factor I, the AI capex chain: who gets paid", with the caveat beside it.
- **The Equities paper** cites it only through `docs/dated-appendix-queue.md` (a new entry for XV's AI-rings section). No paper's body is edited.

**The proxies** (`proxies`, each with its reason). None is Brookfield; the gate checks every key against the blocklist.

| Bucket | Proxies | New to the basket |
|---|---|---|
| Semis | SMH | SMH |
| — accelerators | NVDA, AVGO | — |
| — memory | MU | MU |
| — CPUs and server production | AMD | AMD |
| Power | GRID, XLU | GRID |
| Networking | ANET | ANET |
| Cooling | VRT | VRT |
| Facilities and construction | PAVE | PAVE |
| Memo: lithography | ASML | ASML |

**What the eight new symbols change:**
- **The basket:** 115 → 123 (`yfinance_source.SYMBOLS`); volume units 95 → 103; the volume-shares block 85 → 93. The registry's `market_closes` and `market_actions` blocks, `validate_prices` (101/0), `validate_audit_3a`'s `NEW_BLOCK_MEMBERS`, CLAUDE.md and the architecture document carry the new counts.
- **The Security Master:** `SM00205`–`SM00212`, `next_id` 213. `SM00204` is left to chain-4's KRE so the two cannot collide. Name, currency, exchange and multiplier are null and listed unverified until a listings file confirms them.
- **The single names** (MU, AMD, ANET, VRT, ASML) are equities but not earnings names. They are a declared set, `CAPEX_CHAIN_SYMBOLS`, and `validate_security_master` now holds the basket's equities to `EARNINGS_SYMBOLS | CAPEX_CHAIN_SYMBOLS`, the two sets apart (102/0).
- **The Book B scanner's universe** is every basket instrument with bars, so the eight join it once backfilled, as KRE did (a53). Listed for Ari (needs-you 4).

**The relative line** (`altdata/capex_chain.py` `relative`; the Monthly's what's priced):
- each bucket's equal-weight basket over three months, against SPY, in pp;
- ranked lead to lag, with each bucket's own return;
- a bucket without history is listed with its reason, never ranked;
- beside it, the hyperscalers' **filed** capex growth (AMZN, GOOGL, META, MSFT, ORCL; EDGAR's XBRL frames, annual) and a line that guidance is not tracked.

Report only: the weights are printed as BNP's and never used to score a bucket.

## Item 66: the wealth-effect impulse, the net-transmission line, the ledger

**The impulse** (`altdata/transmission.py` `impulse`), monthly:
- **The measure:** Z.1's household equity share (`fred.hh_equity_share`) times SPX's year-on-year price return (`yfinance.mkt_gspc`, month-end closes), over 100, in pp of household financial assets.
- **Percentiles:** dual (five years and the full history), each with its n, in the rates-transmission cluster's own form.
- **The quarter:** a quarter's share is its own at the month that closes the quarter.
- **Between releases** the share is the latest quarter's **marked to SPX** from the quarter's end, s(1+r)/(1+s·r), the rest of the household balance sheet held flat. It is labelled "marked" wherever it stands in. That is the keyless stand-in for ICI's refused proxy (check 3).

**The net-transmission line** (`net`): the tightening legs (items 34, 36, 41: the rates-transmission cluster's own reads) beside the loosening leg. **How each is scaled, and why:**

| Leg | Scaled as | Why |
|---|---|---|
| Item 34, the market's tightening flag | a flag: on, off, or not read | it is a binary rule (the 10-year up, 12-month policy pricing down); a flag has no percentile |
| Item 36, housing: pending sales on the year | its own-history percentile | a level series; Redfin, single-source |
| Item 41, the quality tail: CCC less BB | its own-history percentile | a level series; ICE BofA OAS via FRED |
| Item 66, the wealth-effect impulse | its own-history percentile | a level series |

**No weights are invented.** No rule puts a flag, a sales growth rate, a spread and a wealth gain on one scale, so the legs print side by side. None is weighted or summed, and no net figure prints.
- **The read** is a count: the tightening legs reading tight (a level leg past its 20th or 80th percentile, by direction) out of those read.
- **The loosening leg** reads loose past its 80th.
- **A leg without its data** reads "not read", never zero.

**Placement.** The Monthly's Plumbing & rates, right after the rates-transmission sub-section: "Rates transmission: the loosening leg", lines only.

**The ledger, ST-R6.66c:**
1. **The pre-registration**, `docs/ledgers/wealth-effect-preregistration-2026-10.md`, was committed alone first (`0764ca8`), before any scoring code. Its SHA-256 over the LF bytes is `2358f4ceec95c81144e7a8255bffa1a152914bf309f5022884dd37b73a3cecc5`, held by the gate. It is never edited.
2. **The scoring script**, `tools/calibration/st_r6_66c_wealth_effect.py`, reads public sources only and opens no store. It defines the impulse:
   - the Z.1 share is lagged three months for publication and not marked;
   - times SPX's year-on-year return each December from 1960;
   - against real PCE growth over the next twelve months.
3. **The pass rule:** Spearman ρ ≥ 0.20 with n ≥ 40, positive in each half, and the top tercile's median outcome above the bottom's.
4. **The laptop first edition**, `docs/ledgers/st-r6.66c-ledger-2026-10-21.md`, with its episodes CSV: **FAIL, n 65.** ρ is +0.06 against the rule's 0.20. Both halves are positive (+0.13 and +0.12), and the top tercile's median real-consumption growth (3.74%) beats the bottom's (3.29%). The rule fails on the whole-sample ρ.
5. **Rights:** report only, as ruled. The verdict grants nothing, and any later right is Ari's ruling. It reaches the register only as a rule-31 draft.

**The voices entry (F4).** JDI Research's own blog, through its RSS feed (`config/voices_sources.yaml` `jdi_research`), tier 2 in `config/source_tiers.yaml`.
- **Its kind:** the vocabulary has no "research seller with positions", so the kind is `independent`, and the ruled tag rides in its note.
- **Not read:** its LinkedIn posts.
- **No person's name** is in a committed file: the firm is the default voice, and the scan names the author from the post at run time.

## Every listed gap

- **ICI's allocation data** (item 66's proxy): refused to an identified client. The Z.1 share is marked to SPX in its place, labelled.
- **Hyperscaler capex guidance** (item 63's "capex-guidance series"): not stored. Item 26 reads through to ST-R4.26, the fiscal-bark flag. The line reads filed capex, annual.
- **The K-shape panel** (consumption by income): Group B's listed gap. The net-transmission line prints without it and names it.
- **Real consumption** is not stored. The ledger reads it from FRED's public CSV; nothing else needs it.

## Where the order and the code differ

1. **"Item 26's capex-guidance series"**: item 26 is the fiscal-bark flag and no guidance series exists, so the line reads filed capex (EDGAR) and says guidance is not tracked.
2. **"The K-shape panel (GTM-12)"**: GTM-12 is the federal-finances rows (`daily_cascade/gtm_block.py`). The K-shape panel is a listed gap, so the line prints in Plumbing & rates without it.
3. **"With the ICI proxy between Z.1 releases"**: ICI refuses, so the share is marked to SPX instead, labelled (F2: a keyless alternative).
4. **"Printed with the K-shape panel"** and "slow layers": the order also names the slow layers for item 66. The line prints once, in Plumbing & rates, beside the cluster it completes.
5. **The voices tag:** the kind vocabulary is fixed, so the tag is a note (above).
6. **Monthly only:** both items are the 1 Nov Monthly's candidates, so neither prints in the close or the Weekly.

## Every session-set value, with its reason

| Value | Setting | Reason |
|---|---|---|
| Each bucket's proxies | the table above | the liquid, keyless, US-listed instruments closest to each bucket; SMH over SOXX for its longer history |
| The relative window | 3 months | the quarter a capex print covers |
| The benchmark | SPY | the index the chain's spending sits inside |
| The basket | equal weight, price return | no weight is BNP's to give inside a bucket; the stored close |
| `min_sessions` | 55 of a 3-month window | a proxy missing more than about a week is not ranked |
| The between-release share | marked to SPX, s(1+r)/(1+s·r) | the share revalued with equities, the rest held flat: the simplest keyless rule, labelled |
| The read's bands | the 20th and 80th percentiles | the tails the stack's lenses already call extreme |
| The ledger's publication lag | three full months after the quarter's end | Z.1 is published about ten weeks after the quarter |
| The ledger's sample | Decembers from 1960 | non-overlapping years; real PCE's monthly index starts in 1959 |
| The ledger's rule | ρ ≥ 0.20, n ≥ 40, both halves positive, top tercile above bottom | a modest, stable, monotone lead: not a fit to one era |

## Each new key, its source and its real publication lag (for b51's `config/publication_lags.yaml`)

| Key | Source | Cadence | Publication | Lag to add |
|---|---|---|---|---|
| `yfinance.mkt_smh`, `_mu`, `_amd`, `_grid`, `_anet`, `_vrt`, `_pave`, `_asml` (and their `_volume`, `_dividend`, `_split`) | Yahoo, through the basket | daily | the close, pulled at 16:10 and re-pulled by the close | **none**: the daily allowance holds |

Item 66 stores no new key: the impulse and the line are computed on read. Its input `fred.hh_equity_share` (Z.1) is already covered by b51's `z1_quarterly` family (its id `BOGZ1*`). The capex line's `edgar.xbrl_capex` is annual, within the annual allowance.

## Box commands (the operator's; inside the windows; dry runs first)

After this branch merges:
```
cd ~/chester-reports
# the eight new proxies' five-year history (they read nothing until it lands):
.venv/bin/python tools/backfill_prices.py --symbols SMH,MU,AMD,GRID,ANET,VRT,PAVE,ASML --years 5 --dry-run
.venv/bin/python tools/backfill_prices.py --symbols SMH,MU,AMD,GRID,ANET,VRT,PAVE,ASML --years 5
# the reads, once they are in (read-only):
.venv/bin/python -m altdata.capex_chain show
.venv/bin/python -m altdata.transmission show
# the ledger's box edition, written OUTSIDE the checkout (public sources, the same rule):
mkdir -p ~/chester-data/ledgers
.venv/bin/python tools/calibration/st_r6_66c_wealth_effect.py --box --out ~/chester-data/ledgers
```
- **Expect** the backfill's dry run to print "price backfill -- 8 symbols, 5y" and the rows it would write; then the same, writing.
- **Expect** `capex_chain show` to print the table, then the relative line (or "not enough history" until the backfill lands).
- **Expect** `transmission show` to print the four legs.
- **Expect** the box edition to print FAIL, n 65, on the same public sources. Copy it back from the laptop with `scp 'vps:~/chester-data/ledgers/st-r6.66c-*' docs/ledgers/` and ask a session to commit it.
- The voices scan reads JDI Research's feed at its next 06:15 run; nothing to run by hand.

## Files shared with chain-4, a54-relative-volume, a55-box-fixes, b51-registry-html and a56-batch14-a1

| File | chain-4 (`4b096bb`) | a54 (`751902a`) | a55 (`b377748`) | b51 (`fc00a8b`) | At the merge |
|---|---|---|---|---|---|
| CLAUDE.md | ✓ | ✓ | ✓ | ✓ | keep both; recount once |
| Makefile | ✓ | ✓ | ✓ | ✓ | keep every gate line |
| `metrics_registry.yaml` | ✓ (the basket blocks' counts: KRE) | ✓ | — | ✓ | splice; the basket counts are the union: 115 + KRE + these eight = **124**; volume units 104; shares 94 |
| `config/catalogue_commands.yaml` | ✓ | — | ✓ | ✓ | keep both |
| `altdata/sources/yfinance_source.py` | ✓ (KRE) | — | — | — | keep both symbols |
| `config/security_master.yaml` | ✓ (SM00204, `next_id` 205) | — | — | — | keep both; `next_id` 213 |
| `tools/validate_prices.py`, `tools/validate_audit_3a.py` | ✓ (116, 96; KRE's members) | — | — | — | the union: 124, 104; both members' lines |
| `monthly_macro/stack.py` | ✓ (a53's bank-stress sub-section) | — | — | — | keep both hooks |
| `docs/master-guide.md` and its HTML | ✓ | ✓ | — | ✓ (the editions' builder) | Table 7a's rows both; rebuild the HTML with the merged builder, never hunk-resolve |
| `docs/chester-reports-architecture-v3.md` | ✓ (116 symbols, 277 FRED) | — | — | — | 124 symbols |
| `docs/dated-appendix-queue.md` | — | — | — | — | a56 also writes the queue (F2's one-off lines): keep every entry |

a56-batch14-a1 was not on origin when checked (21 Oct, about 01:30 ET). Its files are expected to meet this branch's at the order's indexes (not touched here) and the queue.

## The CI rounds

| Round | Run | On | Result |
|---|---|---|---|
| 1 | — | — | — |

## Needs you

1. **The box commands** above, after the merge: the eight symbols' backfill (dry run first), the two reads and the ledger's box edition outside the checkout.
2. **ST-R6.66c's FAIL** (n 65): a rule-31 draft for your accept-all. Nothing prints or gains a right from it.
3. **The session-set values** in the table: confirm or replace. Above all, the proxies and the between-release mark that stands in for ICI.
4. **The Book B scanner's universe** now takes in the eight proxies once they are backfilled, as it took KRE. Keep them, or exclude them in `config/book_b_scanner.yaml`.
5. **The Master Guide's Part 5 counts:** ST-R6.66c's FAIL makes chain-4's "twenty-two gated, thirteen failed" twenty-three and fourteen. That is the next chain refresh's; this branch adds the two Table 7a rows only.
6. **The JDI Research entry** (F4): the voices scan reads its feed from the next run. Confirm, or set it `enabled: false`.
