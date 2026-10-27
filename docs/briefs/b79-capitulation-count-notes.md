# B79: the Capitulation Count (Batch 17 item 97(a)–(c)), notes

*Session B, 26 Oct 2026.*

- **Branch:** `b79-capitulation-count`, from `origin/chain-7-main` at `dfa14a54`.
- **Order:** `docs/change-order-signal-triage-batch-17-2026-10-26.md`, committed with the paste (`docs/pastes/B79.md`).
- **Merge:** after the 8 Nov Weekly; it is the first slot in Tranche B.
- **A81's J3–J5:** A81 had not pushed when this was built, so J4 and J5 were taken as the paste states them.
  - **J4:** ICI is a listed gap. Family 5 is unscorable while its flows leg is a gap, and the count prints "k of n scorable".
  - **J5:** SOXX is not added; the sector legs read SMH.
  - **J3:** not in the paste and not read. If it changes anything here, the change is a later paste's.

## Commits

| SHA | What |
|---|---|
| `eb30ff7d` | The paste, verbatim, and the attached order |
| `4c42f4a6` | Part 1, 97(b), the feeds |
| `6d073791` | The ledger's pre-registration, committed alone before its first run |
| `f67453a5` | Parts 2 and 3, 97(a) and 97(c) |

Parts 2 and 3 are one commit because 97(c) shares the count's module and block. This departs from "one commit per part" and is stated here.

## Sources: robots and terms (all read 26 Oct 2026)

| Source | Robots | Terms | Verdict |
|---|---|---|---|
| Cboe daily market statistics, `cdn.cboe.com/data/us/options/market_statistics/daily/<date>_daily_options` | www.cboe.com disallows `/book/` and `/*market_statistics/volume_reports/` only. cdn.cboe.com answers 403, which RFC 9309 reads as no rules | www.cboe.com/terms (Last Updated 16 Nov 2022): "view, print and download one copy of the Materials for your personal non-commercial use … You may not otherwise copy, reproduce, alter, store either in hard copy or in an electronic retrieval system …" | **Built, switched OFF** (`ENABLED = False`), pending your ruling (needs-you 1) |
| FRED VXNCLS, VXVCLS | FRED, as every FRED series | FRED, as every FRED series | **Built**: added to the pull |
| SPY, ssga.com | No rule against product pages | "The whole or any part of this work may not be reproduced, copied or transmitted … without SSGA's express written consent" | **Gap** |
| QQQ, invesco.com | Disallows only query parameters (`asOfDate`, `startDate` and others) | Not located; the legal page answered 404 | **Gap**: permission not established |
| IWM, ishares.com | Disallows search, sign-on and `.dl` only | Not located; the terms page answered 404. `ishares_trusts.py`'s registry entry records no terms reading | **Gap** |
| SMH, vaneck.com | Crawl-delay 25; no rule against SMH's pages | Not located; the terms page answered 404 | **Gap** |
| ICI weekly flows | not read | J4: a listed gap (ICI refuses an identified client; `ici_mmf.py` parked) | **Gap** |

The Cboe file for 23 Oct 2026 was read once to make the parser's fixture (`tests/fixtures/capitulation/`). It reads total 0.93, index 1.10 and equity 0.67, which matches V1. Files answer from 23 Oct 2019; earlier dates answer 403.

## Keys

- **New, stored:**
  - `cboe.pc_equity`, `cboe.pc_index`, `cboe.pc_total` (source `cboe_putcall`, writer switched off);
  - `fred.vxn` (VXNCLS, from 2 Feb 2001) and `fred.vix3m` (VXVCLS, from 4 Dec 2007), in the new block `fred_batch17`.
- **Derived, computed at read time and not stored:** `calc.pc_equity_20d` and `calc.pc_{equity,index,total}_pct_1y`. They are not registered as stored keys.
- **VIX/VIX3M (97(b)(ii)):** no new stored series. The count reads FRED's pair, `fred.vix / fred.vix3m`, when both are stored for the day. Otherwise it reads the existing `calc.vix3m_over_vix` inverted, which the features pass stores every session.
- **Registered:** `metrics_registry.yaml` (the three Cboe metrics, the block, two long-window rows, a `market_state_barred` entry); `source_registry.yaml` `cboe_putcall` (status built); `config/publication_lags.yaml` family `cboe_putcall`; `config/catalogue_commands.yaml` (two modules).

## The families, as coded (`config/capitulation_count.yaml`)

Each family is yes, no or gap. A gap scores nothing and lowers the scorable count. An input older than 10 days at the cutoff is a gap, never carried forward.

1. **VIX.** `fred.vix` is above 30, or VIX/VIX3M is above 1 (FRED's pair, else `calc.vix3m_over_vix` inverted).
2. **Equity put/call.** The mean of `cboe.pc_equity` over the last 20 stored sessions is 0.8 or more. Below 20 sessions it is a gap, "accruing".
3. **Dealer gamma.** SPY's newest capture (`exposure.net_gex`) is positive, and a capture in the 5 sessions before it was negative. A sign counts only at net-to-gross of 0.10 or more, the 6b gate's rule. Spot must also be above `exposure.gamma_flip`.
4. **Short interest.** All three must hold:
   - SPY's `finra.short_interest` is at the 80th percentile or above of its own stored history (at least 24 prints);
   - the S&P 500 (`yfinance.mkt_gspc`) is above its drawdown low (the low since the 52-week high), and that low is at least 3 sessions old;
   - `calc.breadth_rsp_over_spy` is above its value on the low's day.
5. **Flows and AAII.** Two consecutive weeks of inflow, and AAII bearish peaked above 50% and falling. **Unscorable today:** no flows feed exists (J4), and the AAII writer stores only `aaii.bull_bear_spread`, not the bearish share.

**Labels:** the order's bands on the count itself: 0–1 none, 2–3 oversold, 4–5 surrender. Below 4 scorable families, the line adds "surrender unreachable". There are no decimals and no weights. The direction mark (▲ ▼ =) compares with the previous trading session's count.

**Where it prints:**
- **The close:** in Positioning & flows, on exception only: when the count changed from the prior session, or it is 2 or more.
- **The Weekly:** in Positioning & flows, when the S&P 500 is more than 5% below its 52-week high.
- **Table 3's caption:** the T&B verdict is not built (no writer stores it), so the caption says "T&B verdict: not built … the pair is the read, not the count alone". `tb_verdict()` is where a stored verdict will be read.

**97(c), the sector divergence line:**
- VXN less VIX, with its percentile over its own trailing 252 sessions (accruing until then);
- SMH's drawdown from its 52-week high against the S&P 500's;
- "SMH flows not tracked".

It is an exception when the spread's percentile is above 90, or SMH's drawdown is more than twice the index's. It prints in the close on exception, and in the Weekly's sub-section.

## The laptop's count for 23 Oct 2026, against the post's "one of five" (V1)

The laptop's store (`chester-reports/data/chester.db`) was last written on 15 Oct. Its newest VIX row is 28 May 2026 and its newest price rows are 18–21 Sep. So for 23 Oct, as for 18 Sep, it reads **0 of 0 scorable**: every family is a gap here.

The partial-store caveat: on public figures for 23 Oct, family 1 would read **no**. FRED gives VIX 19.45 and VIX3M 20.48, a ratio of 0.95, with VIX not above 30. Family 2 is a gap (the switch is off). Its one-day equity ratio of 0.67 would not reach 0.8 either way, but the test is a 20-session mean. Families 3 and 4 need the box's captures and FINRA rows, and family 5 is unscorable. So the laptop cannot reproduce the post's "one of five". The post's point was concentrated in semis and on its own reading of the gauges, and it matches nothing the count's tests score on the inputs in reach. The box's first `show` for 23 Oct is the real comparison (box sheet below).

## The ledger

- **Pre-registered:** `docs/ledgers/capitulation-count-2026-10-26.md`, SHA-256 `9cc5a283c4c6d1716f44b46e1561797b35536d43e0e9210698519cf45ce74d4e` (LF-normalised). Committed alone at `6d073791`, before any run; the gate holds the hash.
- **The rule (session-set; the order states none):**
  - **Usable:** an episode with 4 or more scorable families.
  - **INSUFFICIENT:** fewer than 5 usable episodes.
  - **PASS:** 3 or more firings of "4 or more", of which at least 60% held for 60 sessions and at least 67% gave a positive +60-session S&P 500 return.
  - **FAIL:** otherwise.
- **The episodes:** fourteen, from A77's `config/tb_episodes.yaml` (read on its branch, not merged).
- **Resolution:** S&P 500 and QQQ (the labelled Nasdaq-100 proxy) at +20 and +60 sessions, and whether the low held for 60 sessions.
- **Laptop first edition** (`docs/ledgers/capitulation-count-2026-10-26.csv`): **INSUFFICIENT (n 0)**, as the pre-registration expected. Point in time, even the VIX is a gap before the laptop's rows were written.

## Gates

| Gate | Result |
|---|---|
| `validate_capitulation_feeds.py` (new) | 25 passed |
| `validate_capitulation_count.py` (new) | 58 passed |
| `validate_daily_close.py` | 102 passed |
| `validate_weekly_complete.py` | 96 passed |
| `validate_weekly_edits.py` | 91 passed |
| `validate_prices.py` | 101 passed |
| `validate_official_sources.py` | 340 passed |
| `check_registry.py` | OK |
| `check_library.py` | 27 papers, 0 failures, 0 warnings |

**The counts.** `stitch_counts.py` is not on this base, so CLAUDE.md's counts are left to the stitch. `validate_audit_3a.py` therefore reports the drift and will fail in CI until the stitch writes them:
- FRED_PULL_SERIES 283 → **285**;
- code gates 140 → **142**;
- Python gates 137 → **139**;
- the architecture document's store box, FRED pull 283 → **285**.

Its other 86 checks pass, including the catalogue line for both new command modules.

## Box commands (for the post-8-Nov box sheet; the operator's, not run here)

```
# 1. FRED: VXN and VIX3M arrive with the next 06:45 FRED pull (no new unit). To check first:
python -m altdata.sources.fred --dry-run            # if the pull offers it; else let the timer run
# 2. Cboe put/call -- ONLY after the ruling on Cboe's terms (needs-you 1), with ENABLED set True:
python -m altdata.sources.cboe_putcall --dry-run --date 2026-10-23
python -m altdata.sources.cboe_putcall --backfill-from 2019-10-23 --dry-run
python -m altdata.sources.cboe_putcall --backfill-from 2019-10-23
#    then add "cboe_putcall" to feeds.EXTERNAL_WRITERS (a later paste)
# 3. The count, read-only:
python -m altdata.capitulation_count show --db ~/chester-data/chester.db --date 2026-10-23
# 4. The ledger (dry run first; the CSV is the box's edition):
python -m altdata.capitulation_count ledger --db <the store> --dry-run
python -m altdata.capitulation_count ledger --db <the store>
```

## Needs you

1. **Cboe's terms.** The terms allow "one copy … for your personal non-commercial use" and forbid otherwise storing it "in an electronic retrieval system". That is the clause the CoinGecko retirement turned on. The writer is built and switched off. Rule it on (one line, `ENABLED = True`), or keep it off and leave family 2 a gap. The live `cboe_indices` reader (COR1M, COR3M, DSPX) sits under the same terms, and its registry entry records only robots.
2. **Flows.** None of the four issuers' terms could be established as permitting a reader: SSGA's forbid reproduction without consent, and three terms pages were not found. Family 5 therefore stays unscorable, and SMH flows print "not tracked". Do you want a by-hand or vendor route? Under the rule, that needs your explicit yes in a filed order.
3. **AAII's bearish share.** Family 5's second leg needs `aaii.bearish`, but the AAII writer stores only the bull-bear spread. The weekly CSV in the inbox carries the bearish column, so adding the key is a small change to the existing writer, in a later paste. Is that wanted?
4. **The ledger's session-set rule.** The thresholds (5 usable episodes, 3 firings, 60% held, 67% positive) and the families' `exists_from` dates (gamma and short interest null) are this session's. Accept them, or name your own before the box's edition. A change is a new dated registration.
5. **CI and the counts.** `validate_audit_3a` will fail in CI on the counts above (285 / 142 / 139) until the stitch writes them, since `stitch_counts.py` is not on `chain-7-main`. Should the counts be written by hand on this branch instead?
