# ST-R5 Tranche 1, the rest: items 31, 32, 38, 39, 42, 43 and 44 — session notes

**Builds on `st-r5-index`, and merges after it.** Branch `st-r5-t1-rest` from
`st-r5-index` at `204a051` (that branch's CI fix), which stacks on `st-r5-rates`
and the stitched chain (`aud-3b-security-master`, `2fb1048`). The merge order is:

1. the stitched chain;
2. `st-r5-rates`;
3. `st-r5-index`;
4. this branch.

It must not merge ahead of any of them. The two notes commits that land on
`st-r5-rates` and `st-r5-index` after their branch points (their CI records) are
not on this branch. They touch only their own notes files.

Spec:

- **The Batch 6 order** (`docs/change-order-signal-triage-batch-6-2026-10-15.md`,
  on `docs-batch-6`):
  - items 31, 32, 38, 39, 42, 43 and 44;
  - section 4, cross-item rulings 3, 4 and 5;
  - section 8, verify items 1, 6 and 8;
  - section 11, filing notes 4, 6 and 8.
- **The Batch 4 order:** SR-45 (items 9 and 14) and SR-46 (item 10).
- **The 25 Sep order's integration rules:** R28, D1c and the calibration-ledger
  rule.
- **AUD-3a's units rules.**

Session A, 16 Oct 2026. Branch only: pushed, not merged, not deployed, nothing on
the box. Tranche 1 only. The ledgers (31b, 32b, 43b, 44b) and the queue entry
(44c) come later.

## Step 0 — `st-r5-index`'s CI

| Run | Commit | Result |
|---|---|---|
| 38904790271 | `0a55984` (the build) | failure, 92 of 94 jobs |
| 38905177161 | `e5677f4` (the notes) | failure, 92 of 94 jobs |
| 38939100628 | `204a051` (the fix) | **success, 94 of 94 jobs** |

**The verdict: green.** Both failures were on `st-r5-index`'s own change, so I
fixed them there first, as the paste required:

- The failing gate was `validate_stack_cadence`, plus the `gates-passed` roll-up.
  Its check "positioning at 'monthly' prints no week phrase" caught the
  allocation block's note, "with about a ten-week lag".
- The note now reads "published about seventy days after the quarter ends".
- `204a051` carries the fix and the first CI record. This branch starts from it.
- I read the fix's run once afterwards and record it here. Its line in
  `st-r5-index`'s own notes is a separate notes commit on that branch.

## Needs you

1. **D1c, and the writers held for it.** The repo-wide write lock has still not
   landed: WAL and the busy timeout did, in `f98fec4` on 6 Sep (TODO.md, D1c).
   This branch adds two new writers, both built held on the same
   `HELD_FOR_D1C` pattern as `st-r5-rates`' two:
   - `altdata/sources/sp500_members.py` (items 44 and 31): SPY's daily holdings
     and the members' daily closes.
   - `altdata/sources/wgc_stock.py` (item 38): the WGC above-ground stock.

   One ruling lifts all four held writers: `redfin`, `mba`, `sp500_members`,
   `wgc_stock`. Each then needs two edits:
   - `HELD_FOR_D1C = False` in the module;
   - the module's name added to `altdata/feeds.py` `EXTERNAL_WRITERS`.

   Until then:
   - the drawdown histogram and the gap print "awaiting constituent prices";
   - the peak-band flag prints "awaiting constituent holdings";
   - the gold/equity line names the held writer.

   Nothing else on this branch is a new writer. Two existing writers are
   extended:
   - **FRED:** nineteen series join `FRED_SIGNAL_SERIES`.
   - **BIS:** a second request stores every area under `bis.policy_rate`.
2. **The box held no top-10 concentration series.** The paste lists one, and I
   searched the repo and every remote branch: the only top-10 series is the
   retail-trading logger's (`ndl.rtat10_concentration`). So the measure is
   built from the same SPY holdings file as item 44 (issue 1).
   - It is the ten largest issuers' weight in SPY: the S&P 500's float-adjusted
     capitalisation, a second share class counted with its first (GOOGL with
     GOOG).
   - On SSGA's 15 Oct 2026 file, the ten largest issuers held **40.1%**, inside
     the 40–44% band, and the ten largest lines 38.6%.

   Verify item 8 below maps it against BofA's basket.
3. **Item 32 is not an `inflation.driver` sub-state yet.** The market-state
   object (v1.10) has no driver on inflation. Adding one changes the rules: it
   needs config v1.13, method-11 if `regime.py` changes, and a pre-registered
   calibration first, the rule `rates.driver` failed twice under. So the
   classifier is computed report-only in Mechanics, beside where item 24's
   correlation flag prints on session B's `st-r4-tranche-1b`. This is the route
   item 34 took on `st-r5-rates`. The pre-registration it would need is below.
   Your ruling: whether to open that pre-registration now or after the 32b
   ledger.
4. **Item 31's overlay is designed, not built.** The Concentration &
   Complacency overlay exists only in the docs: `master-narrative.md` lists
   "Top-10 ≥25%" among its five inputs.
   - The peak-band flag therefore calibrates an unbuilt overlay. It prints that
     fact and takes no weight.
   - Note: the overlay's designed input (25%) and the order's peak band (40–44%)
     are far apart. On the 15 Oct file the 25% trigger has been on for years.
     Whether 31b recalibrates the input is your call.
5. **Item 39 has gaps, and US–JP is one of them.** FRED's OECD CPI series
   stopped updating in 2025, and Japan's in 2021. Without a current CPI, the
   UK's, Japan's and Canada's real yields are listed gaps, and so is the US–JP
   differential the order wants in the Currencies read.
   - Eurostat's HICP on FRED is current (Sep 2026) for Germany, France, Italy,
     the Netherlands, Belgium, Sweden and Switzerland, core and headline. The
     panel reads it.
   - Two ways to close the US–JP gap; neither is built:
     - a by-hand monthly key for Japan's core CPI (`tools/manual_input.py`,
       one line a month);
     - a reader for Japan's e-Stat. That would be a new writer, held for D1c.
6. **Item 38's denominator is by hand, and WFE is a gap.**
   - WFE's statistics portal needs a login, so its world capitalisation is a
     listed gap.
   - MSCI's ACWI factsheet carries the capitalisation, but only in a PDF, and
     the repo has no PDF reader. A writer would add a dependency.
   - So the monthly proxy is a by-hand key, `manual.msci_acwi_mcap_usd_bn`
     (USD billions: the factsheet's "Mkt Cap (USD Millions)" ÷ 1,000).
   - ACWI's capitalisation is float-adjusted and covers about 85% of each
     market, so the ratio reads higher than Costa's (over WFE's full
     capitalisation). The block's note says so.
   - The ratio's history starts with your first entry, so its percentiles print
     a small n for some time.
7. **Two "new" inputs already exist.** Filing note 8 says Michigan's 5–10-year
   needs a new reader. `altdata/sources/umich.py` has been on the external
   roster since ST-2, so no new reader is needed.
   - The NY Fed SCE writer already stores the 3-year median (`nyfed.sce_3y`),
     so it needed no extension.
   - The only new input is the Cleveland Fed's 10-year, a FRED series
     (`EXPINF10YR`).
8. **DEANCHOR (the batch-2 flag item 42 extends) is a definition, not code.**
   SR-24 defines it, and nothing computes it. The composite sits beside it:
   - The composite prints the definition's first leg: the 5y5y breakeven
     against its own 2022 high.
   - It builds no confirmation logic for the flag.
9. **The OECD leading indicator is the G7's.** FRED's OECD-total CLI stopped at
   Nov 2022 and the US one at Jan 2024. The G7 aggregate (`G7LOLITOAASTSAM`)
   is current to Sep 2026. Item 43 prints it at the lead.
10. **By-hand keys, monthly:**
    - `manual.global_pmi`: the J.P.Morgan Global Manufacturing PMI headline;
    - `manual.msci_acwi_mcap_usd_bn`: ACWI's capitalisation.

    The commands are under Box commands.
11. **Session B's dispersion fallback.** `st-r4-tranche-1b` leaves
    `realized.key` unset in `config/batch5_tranche_1b.yaml`. The constituent
    closes are **`sp500.member_close`**: one key, one instrument per member, in
    Yahoo's ticker form (BRK-B). I sent session B the name. It is set at merge
    on its side.
12. **No report gains words or charts.** Every new sub-section is code-written
    with no model paragraph (`paragraph_wanted: False`). It adds no chart to the
    Weekly's ten or the Monthly's twelve.

## Gates run

**Locally, one at a time, only the gates this branch writes or changes:**

| Gate | Result |
|---|---|
| `validate_st_r5_t1_rest` (new) | 77/0 |
| `validate_audit_3a` (the FRED counts and nineteen declared block members) | 83/0 |
| `validate_em_scorecard` (the BIS writer: 175 keys across the five writers) | 63/0 |
| `check_registry` | OK |

Every other gate is left to CI, including the market-state object's own and
anything that renders a PDF.

**CI on this branch:**

| Run | Commit | Result |
|---|---|---|
| 38943816188 | aef5fdb | failure, 90/95. Two faults, both this branch's own. (1) The diffusion sub-section and three others carried no `not_tracked` list, and the Monthly's slow layers append the sourced-figures absence to the last sub-section's list: `KeyError: 'not_tracked'` in `validate_monthly_stack`, `validate_crypto_basket` and `validate_correlation_layer`. (2) The oil-shock line wrote "20th"/"80th" by hand, which `validate_numeral_audit` refuses; it now goes through `ordinal()`. The fifth failure is `gates-passed`, the roll-up. |
| (next push) | — | recorded at the next read |

## What was built, item by item

| File | Role |
|---|---|
| `config/st_r5_t1_rest.yaml` | every source key and every threshold, each with its reason |
| `altdata/st_r5_t1_rest.py` | the seven reads (reads only: no fetch, no write, no model) |
| `daily_cascade/t1_rest_block.py` | where each read prints |
| `altdata/sources/sp500_members.py` | new writer, held |
| `altdata/sources/wgc_stock.py` | new writer, held |
| `altdata/sources/bis_cbpol.py` | extended writer |
| `altdata/config.py` | extended FRED pull |
| `tools/validate_st_r5_t1_rest.py` | the gate |

### ST-R5.31a — the peak-band flag (`concentration`)

- **Source:** `sp500.member_weight` (SPY's holdings, held writer). The share is
  the ten largest issuers' weight.
- **Flag:** fires at **40.0%** and above. It reads "inside the band" up to 44%
  and "above the band" past it.
- **BofA's basket:** printed beside it from the same file.
- **Report-only:** no weight, and the line names the unbuilt overlay.
- **Fixtures (gate group C):** these figures are hand-computed:

  | Case | Result |
  |---|---|
  | GOOGL and GOOG merged | the top ten sum to exactly 40.0% and fire; ten *lines* would be 38.5% |
  | 39.99% | does not fire |
  | 44.01% | reads above the band |
  | no holdings | "awaiting constituent holdings" |
  | holdings 9 days old | absent with their age |

### ST-R5.44a — the drawdown histogram and the gap (`breadth`)

- **Source:** `sp500.member_close` and the index close (`yfinance.mkt_gspc`).
- **Distance:** a member's distance is its close against its highest close in
  the trailing 365 days.
- **Buckets:** the chart's four:

  | Bucket | Rule |
  |---|---|
  | At a 52-week closing high | distance 0 |
  | Within 10% | above −10% |
  | 10–20% below | from −10% to above −20% |
  | 20% or more below | −20% or deeper |

  An edge falls in the deeper bucket.
- **The gap:** the equal-weighted average member's distance less the index's,
  in percentage points.
- **Weekly:** prints in Mechanics, and in the Monthly too.
- **Survivorship:** today's members only. The note says survivorship reads the
  past lower (SR-45's caveat).
- **Fixtures (group D):** twenty members with set drawdowns:

  | Check | Result |
  |---|---|
  | buckets (by hand) | 2, 6, 5 and 7 |
  | average member | −16.45% |
  | index | −2.5% |
  | gap | −13.95 pp |
  | 95% coverage | prints |
  | 90% coverage | "awaiting constituent prices (18 of 20 members hold a year of closes)" |
  | no closes | "awaiting constituent prices" |

### ST-R5.32a — the oil-shock signature (`oil_shock`)

- **Sources:** `fred.brent` (DCOILBRENTEU), `yfinance.mkt_gspc` and
  `fred.yield_10y`, all stored.
- **Correlations:** 126-session correlations of daily changes, Brent log
  returns against S&P 500 log returns and against the 10-year's change.
- **Percentiles:** each current correlation's percentile over the 20-year
  history of its own rolling values. The history is printed with its real
  length and n when shorter.
- **ON:** Brent–SPX at or below its 20th percentile *and* Brent–10y at or above
  its 80th: "the supply-shock signature is ON: oil trades as the hedge".
- **Otherwise:** "no supply-shock signature (demand-driven or mixed)".
- **Fixtures (group E):**
  - A hand case for the correlation (+1 and −1).
  - A seeded three-year path whose last six months carry the shock, which
    reads ON.
  - Each leg fires with its threshold set equal to the observed percentile, and
    turns off 0.0001 beyond it.
  - With no Brent: "Brent not stored".

### ST-R5.42a — the composite inflation-expectations z (`expectations`)

- **Inputs:**

  | Input | Key | Note |
  |---|---|---|
  | 5y5y breakeven | `fred.breakeven_5y5y` | month-end |
  | Cleveland Fed 10-year | `fred.expinf_10y` | new FRED series EXPINF10YR |
  | NY Fed SCE 3-year | `nyfed.sce_3y` | stored |
  | Michigan 5–10-year | `umich.expect_5_10y` | stored |

- **Each input's z:** its latest month against its own trailing 120 months, at
  least 36.
- **Present:** an input counts when its latest month is within three months of
  the edition's.
- **The composite:** the mean of the present z's. It is **refused below
  three**: "not printed — 2 of 4 inputs present, fewer than 3".
- **Flag:** at a composite of +1.0 and above.
- **DEANCHOR:** its first leg prints as a comparison with the 2022 high.
- **Fixtures (group F):**
  - The z's agree with `statistics.stdev` over each input's 120 months.
  - Four inputs, then three (Michigan five months stale), then two (refused).
  - The flag fires at its threshold and not 0.01 below it.

### ST-R5.39a — the real-yield panel (`real_yields`)

- **Countries:** the G10 (the eleven of the Group of Ten) and SR-46's ten EM
  countries.
- **Nominal:** the OECD 10-year on FRED, a monthly average. Existing keys come
  first: `oecd_10y_*`, `gilt_10y`, `jp_10y`. Three are new: Mexico, South
  Africa and Korea. China's is `cfets.cgb_10y`.
- **Real:** nominal less CPI inflation on the year, core first and headline
  beside it:

  | Countries | CPI |
  |---|---|
  | US | `fred.core_cpi`, `fred.cpi` |
  | Euro countries, Sweden, Switzerland | Eurostat HICP on FRED (fourteen new series) |
  | EM | IMF headline, `em.cpi.yoy.*` and `thai.cpi_yoy`; no core stored |

- **Linker:** the US's TIPS monthly mean. The other five named linkers have no
  FRED series, so they are one listed gap.
- **Stale CPI:** a CPI more than three months behind its yield is a gap, never a
  number.
- **Differentials:** US–DE and US–JP print in the Currencies read: the Weekly's
  "Global rates and FX" and the Monthly's global-rates bucket.
- **Gaps on 16 Oct:**
  - **No 10-year on FRED:** Brazil, India, Indonesia, Turkey, Taiwan and
    Thailand.
  - **No current CPI:** the UK, Japan and Canada.
- **Fixtures (group G):**

  | Country | Real, core | Real, headline | Linker |
  |---|---|---|---|
  | US | 1.90% | 2.40% | 1.85% |
  | DE | 1.20% | 1.40% | — |

  - US–DE is +70 bp. US–JP is a gap naming Japan.
  - France's HICP five months behind is a gap.
  - Mexico's real yield is on headline, with the core gap named.

### ST-R5.38a — gold against world equities (`gold_equity`)

- **The ratio:** `wgc.above_ground_t` × 32,150.7466 oz/t × `yfinance.mkt_gold_front`
  ÷ `manual.msci_acwi_mcap_usd_bn` × 10⁹.
- **Points:** one per by-hand capitalisation entry, with a gold close no more
  than five days earlier.
- **Percentiles:** dual percentiles with their real window and n.
- **Where it prints:**
  - in the Monthly's Slow layers as "Factor V: gold against world equities";
  - as a line beside item 30's allocation block, Weekly and Monthly.
- **Fixtures (group H):**
  - The ratio by hand: 26.0% at $4,000/oz over $110,000bn.
  - A July entry with no gold close within five days is dropped, which leaves
    n = 2.
  - With no stock, the reason names the held writer.
  - WFE is listed.

### ST-R5.43a — global policy diffusion (`diffusion`)

- **Source:** `bis.policy_rate`, every BIS area (the extended writer).
- **An area's last move:** its latest month-end change of at least a basis
  point.
- **Counted:** an area counts in a month when its last observation is at most
  three months older. That drops a legacy series (the euro members before
  1999) by itself.
- **The index:** cuts less hikes, over the areas counted. It needs 20.
- **Printed with:**
  - its value six and twelve months earlier;
  - its percentile and n;
  - the value at the 8-month lead;
  - the G7 CLI;
  - the global PMI, by hand.
- **Where it prints:** Slow layers, plus one line in Ahead: "on Topdown's
  8-month lead it bears on growth into <month>". The lead is labelled
  unvalidated.
- **Report-only** until 43b.
- **Fixtures (group I):**
  - 24 areas: ten hiked in 2024 and cut in Jun 2026, six hiked in Mar 2026,
    seven never moved, and one stale.
  - Sep 2026: net +17.4% of 23. Jan 2026: −41.7% of 24.
  - Five areas is absent. Nothing stored means no ahead line.

### The display (group J) and the registry (group K)

| Where | Weekly | Monthly |
|---|---|---|
| Mechanics | "Concentration and breadth"; "The oil-shock signature" | the same |
| Plumbing & rates | "Inflation expectations: the composite"; "Real 10-year yields across countries"; the differentials in "Global rates and FX" | the same; the differentials in the global-rates bucket |
| Positioning & flows | item 38's line in the allocation block | the same |
| Slow layers | — (the Weekly has none) | "Factor V: gold against world equities"; "Global policy diffusion" |
| Ahead | "The growth lead: policy diffusion" | the same |

**Group J also checks:**
- No paragraph is asked.
- No week phrase at "monthly", "52-week" aside.
- Every number in a section's `data` has a typed field name.
  - This guards against the fault `st-r5-rates` met in CI: the numeral audit
    reads an untyped field as any unit.
- No filler line and no causal claim.
- `regime.py` reads none of it, and the inflation dimension declares no driver
  (the object stays v1.10).

**Group K:**
- Every key the reads use is registered with its units.
- The new keys carry a family and a long window.
- The two sources are held.
- The catalogue names the three new commands.
- The reads import no fetcher or model, and write no store.

## The held writers, and the two edits that lift each

| Writer | Writes | Lift (after your D1c ruling) |
|---|---|---|
| `altdata/sources/sp500_members.py` | `sp500.member_weight`, `sp500.member_close` | `HELD_FOR_D1C = False`; add `"sp500_members"` to `feeds.EXTERNAL_WRITERS` |
| `altdata/sources/wgc_stock.py` | `wgc.above_ground_t` | `HELD_FOR_D1C = False`; add `"wgc_stock"` to `feeds.EXTERNAL_WRITERS` |

`st-r5-rates`' `redfin` and `mba` lift the same way.

**`sp500_members`:**
- Reads SSGA's workbook after www.ssga.com's robots.txt allows it. The `*` group
  disallows nothing on that path on 16 Oct.
- Reads the closes through `altdata.import_yfinance()`, under the
  operator-sanctioned yfinance exception, never passing for a browser.
- First pull: two years; then ten days.

**`wgc_stock`:**
- Reads one sentence of www.gold.org's "how much gold" page, which robots
  allows.
- A changed sentence is refused.

## Session-set thresholds (`config/st_r5_t1_rest.yaml`)

| Item | Value | Reason |
|---|---|---|
| 31 | holdings older than 7 days are stale | the file is daily; a week covers a holiday and a missed pull |
| 44 | a member counts with ≥240 closes in the window, last close within 4 days of the index | a year is ~250 sessions; ten missing are tolerated |
| 44 | the histogram prints at ≥95% coverage | a half-loaded store must never read as breadth |
| 32 | "6-month rolling" read as 126 sessions; a window needs 120 of them with all three series | half of ~252 sessions a year; FRED and Yahoo holidays differ |
| 42 | z over 120 months, at least 36; present if ≤3 months old | SCE and Michigan publish about a month behind |
| 42 | the flag at a composite z of +1.0 | one standard deviation above the inputs' own ten-year means |
| 39 | a CPI more than 3 months behind its yield is a gap | a stale real yield is worse than none |
| 38 | the gold close within 5 days of the capitalisation's date | a factsheet's date can fall on a weekend or a holiday |
| 43 | an area counts if its data is ≤3 months old; a move is ≥1 bp; ≥20 areas | India and Korea run behind; a fraction of a bp is no move |

The order gives these: 31's band (40–44%); 32's six months, 20 years and
20th/80th percentiles; 42's four inputs and its minimum of three; 43's lead (8
months, Topdown's fit, for the ledger to test).

## Verify items

**1. Item 9's breadth definition against item 44's.** They do not contradict.
- **Item 9 (SR-45a)** is "the share of current constituents ≥20% below their own
  high, monthly, conditioned on the index within 1% of a record".
  - Its "record highs" are the *index's* records. The 30 Sep reading was 49%
    of members ≥20% off with the index at a record.
  - So item 9 is weak breadth under a record index, not breadth at records.
- **Item 44** is the same picture, read weekly and without the record
  condition: its 20%-or-more bucket is item 9's numerator.
- **Two differences remain:**
  - Item 9's history is Inovestor's point-in-time list. Ours and Raymond
    James's use today's members, so survivorship reads lower.
  - Which "high" Inovestor uses (52-week or all-time) is not stated in the
    order. Ours is the 52-week closing high, as Raymond James's chart.

  44b should state both.

**6. The BIS dataset's coverage and update lag.**

*The writer's records:*
- The docstring and AQ-9a's notes, 11 Oct: eleven of the scorecard's thirteen,
  no row for Taiwan or the UAE.
- Latest months on 11 Oct: Sep 2026 for most, India Jun, Korea Jul.

*Re-read on 16 Oct for the extension:*
- The table serves **49 areas**:
  - 36 current to Sep 2026;
  - Korea to Aug 2026, India to Jun 2026;
  - Argentina to Jun 2025;
  - Croatia to Jul 2022 (euro entry);
  - ten euro members' legacy rates ending 1998–2000. The euro area's own is
    XM.
- So **38 areas are live**, the order's "~38 economies".

*Lag:*
- Monthly, end of period. September's month-end was served by 16 Oct, about
  two weeks after the month.
- India and Korea run one to three months further behind. The three-month
  allowance keeps them in.
- The BIS sent no Last-Modified on 16 Oct, so the rows carry the ingest
  instant.

**8. The box's top-10 series against BofA's AI Big 10, mapped once.**
- The box held no top-10 series (Needs you, 2). The measure is the ten largest
  issuers' weight in SPY's holdings.
- On SSGA's 15 Oct 2026 file:

  | Measure | Share |
  |---|---|
  | ten largest issuers | 40.1% |
  | ten largest lines | 38.6% |
  | BofA's basket (Mag 7, Broadcom, AMD, Micron) | 40.0% |

- **The baskets nearly coincide.** The top ten by weight on 15 Oct were NVDA,
  AAPL, MSFT, GOOGL, AMZN, AVGO, META, MU, TSLA, LLY: BofA's basket less AMD,
  plus Eli Lilly.
- **The denominators differ.** BofA's 42% is of US market capitalisation per
  the secondary report. Ours is of the S&P 500's float-adjusted capitalisation,
  which, being the larger names' index, reads a top-ten share higher than a
  whole-market denominator would. Japan's 44% is a country's share of MSCI
  ACWI, a third measure.
- The band is a base rate across measures, and the block prints which measure
  ours is.

## Item 32: the pre-registration a sub-state would need

The same shape as `docs/ledgers/rates-driver-2026-09-30-r2-preregistration.md`.
It is written before any code that puts the read in the object, and never
edited after.

| Field | Content |
|---|---|
| Hypothesis | while the signature is ON, the S&P 500's and a 60/40's forward returns at 1, 3 and 6 months differ from their unconditional distribution, and Brent's correlation to the S&P 500 stays negative over the next 3 months |
| Frozen | 126 sessions of daily changes; percentiles over 20 years; Brent–SPX ≤ 20th and Brent–10y ≥ 80th; on and off read at the session close |
| Data | DCOILBRENTEU from 1987, ^GSPC, DGS10; 60/40 as SPY/IEF or the closest stored proxy |
| Grid | thresholds of 15/85 and 25/75 and windows of 63/252 reported as robustness only, never chosen from |
| Pass | your rule, set before the run; the rates-driver precedent was a declared minimum hit rate against a coin |
| On pass | config v1.13 (`inflation.driver`: supply_shock / demand), method-11 if `regime.py` changes, and a replay gate, as group L holds for rates |

## Drafts (yours, by hand)

**31 — the peak-concentration table** (XX Base Rates; the Equities paper's dated
appendix). Shares are BofA's, via secondary reporting (item 20's caveat). The
dates and paths are to be confirmed against BofA's chart, and the post-peak
columns are 31b's.

| Episode | Basket | Denominator | Peak share | Peak (to confirm) | Leaders' relative drawdown | Time to trough | Breadth after |
|---|---|---|---|---|---|---|---|
| Railroads | the railroads | US market capitalisation | 63% | 19th century | 31b | 31b | 31b |
| 1920s | utilities, telecoms, industrials | US market capitalisation | 36% | 1929 | 31b | 31b | 31b |
| Nifty Fifty | the fifty | US market capitalisation | 40% | 1972–73 | 31b | 31b | 31b |
| Japan | Japanese equities | MSCI ACWI | 44% | 1989 | 31b | 31b | 31b |
| TMT | technology, media, telecoms | US market capitalisation | 41% | 2000 | 31b | 31b | 31b |
| AI Big 10 | Mag 7, Broadcom, AMD, Micron | US market capitalisation | 42% | 2026 (live) | — | — | — |

Caveats to print with it:
- The baskets are defined after the fact.
- The measures differ: Japan is a country's share of a world index.
- Ours is the S&P 500's float-adjusted share (Verify item 8).

**32 — the Book A rule-table line:**

> While the oil-shock signature is ON (Brent–S&P 500 six-month correlation at or
> below its 20-year 20th percentile and Brent–10-year at or above its 80th), oil
> and broad commodities sit in the hedge sleeve, not the risk sleeve. They return
> at the first weekly close with either leg outside its band. Pending the 32b
> ledger; descriptive until then.

**38 — the base-rate note** (Metals paper; XXVII's dated appendix):

> Gold's above-ground stock against world equity capitalisation has peaked three
> times since 1901, at roughly 80–90%: the First World War, the Second, and the
> end of the 1970s inflation decade. Each peak came in a regime of war finance or
> monetary disorder. It troughed near 5% around 2000, and stood near 20% in
> 2025 (Costa, Azuria Capital, a gold-fund manager). Three peaks in 125 years
> make it a secular frame, not a timing tool. The stack's monthly proxy divides
> by MSCI ACWI's float-adjusted capitalisation, so it reads higher than this
> series.

**39 — the sovereign-scorecard column:** "Real 10-year (core CPI), month", from
the panel's table. It rides item 21's quarterly update, and the UK, Japan and
Canada stay blank until a current CPI is stored.

**42 — the disagreement pair** (narrative register):

> **"More hikes"** (Callum Thomas, Topdown Charts): composite inflation
> expectations are turning up and the Fed follows with a lag.
> **"The market does the tightening"** (Ruth Carson, Bloomberg; Orchard, T. Rowe
> Price): the long end's rise does the Fed's work.
>
> Adjudicated monthly. The composite z's direction over three months sits
> against item 34's flag (`st-r5-rates`):
> - composite rising with the flag off scores for "more hikes";
> - composite flat or falling with the flag on scores for "the market does the
>   tightening";
> - both rising, or both off, is a draw and is said to be one.

**42 — the Warsh-matrix line:**

> Inflation-expectations composite at or above +1.0 z and rising: weight the
> hikes-resume cell up. Composite below 0 and falling while the 10-year rises:
> weight the hold-and-let-the-curve-work cell up. Descriptive, unvalidated; the
> matrix's weights stay yours.

**43 — the global PMI**, monthly, by hand (the command is below).

## A sample on the gate's fixtures

These are the gate's own fixtures, not market data.

```
Concentration and breadth (Mechanics)
  The ten largest issuers' share of the S&P 500's float-adjusted capitalisation,
  40.0% on 2026-10-09 (SPY's holdings): inside the band of past bubble peaks
  (40–44%, BofA); the peak-band flag is on. BofA's basket (the Magnificent 7,
  Broadcom, AMD, Micron) holds 38.5% of the same file. A calibration of the
  Concentration & Complacency overlay's top-10 input (designed at 25%; the
  overlay is not built), with no weight.
  | At a 52-week closing high | 2 | 10% |
  | Within 10% of it          | 6 | 30% |
  | 10–20% below              | 5 | 25% |
  | 20% or more below         | 7 | 35% |
  The average S&P 500 member closed 16.4% below its 52-week closing high on
  2026-10-09, the index 2.5% below its own: a gap of -13.9 pp (20 of 20 members
  counted).

The oil-shock signature (Mechanics)
  Brent against the S&P 500, six-month correlation of daily changes -0.87 (0th
  percentile); Brent against the 10-year +0.84 (100th); over its stored history
  since 2024-02-16, shorter than 20 years (n=691 windows), on 2026-10-09: the
  supply-shock signature is ON: oil trades as the hedge. ...

Inflation expectations: the composite (Plumbing & rates)
  | 5y5y breakeven        | 2.90% | Sep 2026 | +6.14 | since Oct 2016 (n=120) |
  | Cleveland Fed 10-year | 2.75% | Sep 2026 | +4.51 | since Oct 2016 (n=120) |
  | NY Fed SCE 3-year     | 2.95% | Sep 2026 | +5.22 | since Oct 2016 (n=120) |
  The composite inflation-expectations z: +5.29, the mean of 3 of 4 inputs' own
  ten-year z (-1.23 in Jul 2026); the flag (z at or above +1.0) is on.
  not tracked: Michigan 5-10 year: its latest month is May 2026, 5 months old

Real 10-year yields across countries (Plumbing & rates)
  | United States | 4.90% | Sep 2026 | 1.90% | 2.40% | 1.85% |
  | Germany       | 3.40% | Sep 2026 | 1.20% | 1.40% | —     |
  Real 10-year differential, US less DE, on core CPI: +70 bp (Sep 2026).
  Real 10-year differential, US less JP: a gap (Japan's real yield on core CPI
  is a gap).

Factor V: gold against world equities (Slow layers)
  Gold's above-ground stock at $4,000/oz is 26.0% of ACWI's capitalisation on
  2026-09-30 (stock as of 2026-06-30); 100th percentile of its stored history
  since 2026-08-31 (n=2; shorter than 10 years).

Global policy diffusion (Slow layers) and Ahead
  Global policy diffusion, Sep 2026: net +17% of 23 central banks last moved by
  cutting (10 cut, 6 hiked); -67% six months earlier, -42% a year earlier; ...
  At the lead: diffusion 8 months back (Jan 2026) was -42%; the OECD G7 leading
  indicator is 100.94 (Sep 2026); the global manufacturing PMI 50.2 (by hand,
  2026-09-01). Report-only until its lead is ledgered.
  Policy diffusion at +17% (Sep 2026); on Topdown's 8-month lead it bears on
  growth into May 2027. The lead is unvalidated until its own ledger is written.
```

## Box commands (yours, inside a window: weekdays 09:05–15:40 or 17:20–23:30 ET, never 16:00–17:20)

Everything below runs only after this branch reaches main, behind the chain,
`st-r5-rates` and `st-r5-index`. The wrappers pull main. No deploy and no unit
change is needed until D1c lifts the held writers.

```bash
# 1. The nineteen new FRED series arrive with the 16:10 pull, each with its whole
#    history (EXPINF10YR, G7LOLITOAASTSAM, CP0000/00XEFD for DE FR IT NL BE SE CH,
#    IRLTLT01 for MX ZA KR). To have them before a Monthly, one pull by hand:
~/chester-reports/.venv/bin/python -m altdata.sources.fred

# 2. The BIS writer's extension (every area) runs in the official writers at
#    16:10. By hand, once (one request, about 25,000 rows on its first run):
~/chester-reports/.venv/bin/python -m altdata.sources.bis_cbpol

# 3. Monthly, by hand (values are yours):
~/chester-reports/.venv/bin/python tools/manual_input.py manual.global_pmi <LEVEL> <YYYY-MM-01> "J.P.Morgan Global Manufacturing PMI, <month>"
~/chester-reports/.venv/bin/python tools/manual_input.py manual.msci_acwi_mcap_usd_bn <USD_BN> <YYYY-MM-DD> "MSCI ACWI factsheet, Mkt Cap (USD Millions) / 1,000, <date>"

# 4. After your D1c ruling and the two edits per writer (a commit, then main):
#    the first pulls, inside a window. sp500_members reads two years of ~500
#    members' closes on its first run.
~/chester-reports/.venv/bin/python -m altdata.sources.sp500_members
~/chester-reports/.venv/bin/python -m altdata.sources.wgc_stock

# 5. The reads as the box sees them, and the registry check.
~/chester-reports/.venv/bin/python -m altdata.st_r5_t1_rest show
~/chester-reports/.venv/bin/python -m tools.check_store_registry --db ~/chester-reports/data/chester.db
```

## Files shared with the open branches

This branch's files over `st-r5-index`, against each open branch's own commits
since the chain:

| Branch | Shared files | Nature |
|---|---|---|
| `st-r5-rates`, `st-r5-index` (mine) | every file they changed: this branch is built on them | sequential, no conflict; merge them first |
| `st-r4-tranche-1` (session B) | `CLAUDE.md`, `Makefile`, `altdata/config.py`, `config/catalogue_commands.yaml`, `daily_cascade/weekly_stack.py`, `metrics_registry.yaml`, `monthly_macro/stack.py`, `source_registry.yaml`, `tools/validate_audit_3a.py` | see the counts below. My hooks are short, appended at the end of `mechanics_week`, `plumbing_week`, the allocation block in `positioning_week`, the Weekly's `built` dict (Ahead), and the Monthly's `mechanics_section`, `plumbing_section`, `slow_layers` and `ahead` step. Its item-24 sub-section sits in Mechanics too; both append, so the order after merge is its then mine. |
| `st-r4-tranche-1b` (session B) | the same nine files | as above. Its dispersion fallback's `realized.key` is set to `sp500.member_close` at merge. |
| `6e-metric-lenses` (session B) | `CLAUDE.md`, `Makefile`, `metrics_registry.yaml` | gate count and list; registry entries in different blocks. When 6e merges, `st_r5_rates.lens` (which this branch reuses) should move onto 6e's `derived.lens_forms`. |
| `st-r6-es-block` (session B) | `CLAUDE.md`, `Makefile`, `config/catalogue_commands.yaml`, `daily_cascade/weekly_stack.py` | gate count and list; catalogue lines; different functions in `weekly_stack.py` |

**The counts after every branch merges.** This branch's 52 in
`FRED_SIGNAL_SERIES` are the chain's 27, `st-r5-rates`' 2, `st-r5-index`'s 4 and
this branch's 19. `st-r4-tranche-1b` adds 3 (PPIDCS and two GDP contributions,
which include `st-r4-tranche-1`'s one). That makes **55** in
`FRED_SIGNAL_SERIES`, **157** in `FRED_PULL_SERIES`, and `expected_members` 55.

The code-gate count is the chain's 84, plus my three (`st_r5_rates`,
`st_r5_index`, `st_r5_t1_rest`), plus session B's. `validate_em_scorecard`'s 175
keys stand unless session B changes a writer of the five.

## Not named in the orders

- **`bis.policy_rate` is a new key on an existing writer.** `bis_cbpol`'s
  `allowed_reports` gains `weekly_tactical`, for the Weekly's Ahead line.
- **Robots.** Both new writers read robots.txt each run with the repo's
  wildcard-aware reader (`aaii.robots_verdict`), as the GLD and MBA readers do,
  and stop on a disallow.
