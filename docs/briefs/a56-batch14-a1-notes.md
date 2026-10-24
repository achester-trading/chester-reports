# a56-batch14-a1: signal triage Batch 14, Part A1, items 64, 69 and 70 (session A, 21 Oct 2026)

**Base and boundaries.** This branch is cut from **main's tip, `f9ec9e3`** ("Merge pull request #40 from achester-trading/chain-3"), which carries chain-3.
- **Merging.** Chain-4 merges on Wednesday evening. When it is on main, main is merged into this branch with a merge commit, the gates are recounted, and the branch is pushed.
- **Branch only.** Pushed, nothing merged, nothing deployed, nothing run on the box, no unit enabled or started.
- **Only read:** session B's `b52-batch14-a2` (items 63 and 66) and `b51-registry-html`. chester-meme was not opened.
- **The specification** is `docs/change-order-signal-triage-batch-14-2026-10-20.md`, filed byte for byte (`28edfe1`, before any code). Its section 0 (F1 to F8) governs, and items are cited by their filed numbers.
- **Where the order and the code differ, the code wins.** Each difference is listed below.
- **Timing:** these are 1 Nov Monthly candidates, so the branch is to be green and ready to merge by Saturday 24 Oct.

## The commits

| Commit | What |
|---|---|
| `28edfe1` | Part 0: the order filed verbatim and indexed in `docs/change-orders.md` and the signal-triage register's header, after Batch 11 (main's last; Batches 12 and 13 arrive with chain-4 and a54) |
| (this commit) | Parts 1–4: items 64, 69 and 70, the gate, these notes |

## Part 0: the source checks (section 5 and F6, F7)

| Check | Result |
|---|---|
| **Item 64's levels** (10y 5.31%, real 10y 2.95%, "as of 9 Oct 2026", "highest since 2002 and 2008") against FRED DGS10 and DFII10 (fredgraph.csv, keyless) | **The levels are right, the date is not.** DGS10 closed 5.31% and DFII10 2.95% on **5 Oct 2026**, both their 2026 highs. DGS10 was last at or above it on 14 May 2002 (5.32%), DFII10 on 24 Nov 2008 (3.11%), so "highest since 2002 and 2008" holds. On 9 Oct they closed 5.24% and 2.91%. The dated record carries 5 Oct (D7: series and as-of date). |
| **5**, the 5.33% to 5.08% day (Part B's item 65), against DGS10 | **Does not match.** No DGS10 close reached 5.33% in 2026, and no session from September fell 25 bp; the largest mid-October fall was 9 bp (5.19% to 5.10% on 15 Oct). It may be an intraday range. Recorded for Part B. |
| **6**, the purchase claim (F6), against a primary FHFA or GSE release | **The date and terms hold; no primary FHFA release exists.** <br>• **The announcement**, 8 Jan 2026: the President's instruction to buy $200bn of mortgage bonds, as reported that day (CNN, `cnn.com/2026/01/08/business/mortgage-bonds-trump-purchase-rates`). <br>• **The confirmation:** the FHFA director's, that Fannie Mae and Freddie Mac would make the purchases. <br>• **FHFA's own record:** its news releases (page 1 of the list, 24 Feb 2026 back to 24 Nov 2025) and its statements carry no release on it. The portfolio cap was reported raised to $225bn each by an FHFA email of 12 Jan. <br>• **The GSEs' own records:** Freddie Mac's monthly volume summary for January 2026 (`freddiemac.com/investors/financials/pdf/0126mvs.pdf`) and its Q1 10-Q are primary for the purchases. They were not machine-readable here (font-encoded PDFs), and Fannie Mae's site refused the read, so **no GSE figure is quoted**. <br>• **Verdict:** confirmed against the day's reporting and the director's confirmation, not against an FHFA release; listed in needs-you. |
| **7**, a keyless current-coupon MBS yield, or a proxy | **None; a listed gap.** FRED carries no current-coupon MBS yield. An MBS ETF's published yield is the issuer's figure, a vendor value under the rules, so it is not used. The order's own fallback stands: the PMMS spread alone. The current-coupon spread prints "not tracked". |
| **GSE retained portfolios** ("only if keyless and simple") | **Not simple; a listed gap.** <br>• Freddie Mac's monthly summaries are PDFs whose text needs a PDF parser the project does not carry. <br>• Fannie Mae's site answers automated reads with 403. <br>• The line prints "not tracked". |
| **Shiller's housing data** (the 16 Oct standing rule) | **Passes.** shillerdata.com's robots.txt disallows only `/404`, and its page links `Fig3-1.xls` beside the `ie_data.xls` the project already reads (ST-2). The file is the real home price index, 1890 = 100: annual to 1952, monthly from January 1953 (July 2026 last, Last-Modified 6 Oct 2026). |

## Part 1: item 64, the excess CAPE yield (F3)

- **What it is:** the cyclically adjusted earnings yield (100 / Shiller's CAPE) less the real 10-year (FRED DFII10, `fred.tips_10y`) as the month's mean of daily closes. It is monthly from 2003, when DFII10 begins, with dual percentiles: five years and the full stored history, each with its n.
- **The label:** "Excess CAPE yield (100 / CAPE less the real 10-year, DFII10; not Shiller's own real rate)". Shiller's own measure takes its real rate from the nominal 10-year less trailing inflation.
- **The forward version** is a listed gap and prints as one.
- **Where it prints:** the Monthly's slow layers (`daily_cascade/batch14_a1_block.py`). GTM-2's valuation quad is not built (see the differences).
- **The dated record** of the levels is in `docs/dated-appendix-queue.md`, under 5 Oct 2026.

## Part 2: item 69, the housing footprint

| Line | How |
|---|---|
| **PMMS less the 10-year** | Freddie Mac's 30-year rate (`fred.mortgage_30y`, already pulled) less DGS10 (`fred.yield_10y`) on the PMMS day, bp, with dual percentiles. It prints in item 36's housing block (`rates_transmission_block`), in the Weekly's and the Monthly's Plumbing & rates. |
| **Current-coupon MBS less the 10-year** | "not tracked", with its reason (Part 0, check 7) |
| **GSE retained portfolios** | "not tracked", with its reason (Part 0) |
| **Real home prices since 1890** | Shiller's index, stored by the existing Shiller pull as **`shiller.real_home_price`** (the one new key, registered). It prints in the Monthly's slow layers as the latest month's percentile against one point a year. |
| **The narrative entry** | `gse_mbs_purchase_floor`, under `proposals:` in `config/narratives.yaml`, the existing config proposal path. It enters at the next seed as PROPOSED (origin `config_proposal`) with F6's tag: "verified (announcement of 8 Jan 2026); the post's source is a promoter". Its evidence and outcome read PMMS falling. Confirming or rejecting is the operator's. |
| **Item 20's ledger line** | A housing intervention dated 8 Jan 2026, with its citations, queued in `docs/dated-appendix-queue.md`. Item 20's ledger is not built (see the differences). |
| **The X account** (F4) | The X pilot's seed list is the chat-side digest's prompt, not a file in this repo. So the account is listed for the operator to add, tagged promoter (needs-you). |

**The one point a year** for the real home price is session-set: each year's mean of its months from 1953, so the monthly era does not outweigh 1890–1952 twelve to one.

## Part 3: item 70, the nominal-growth anchor

- **What it is:** the 10-year (the quarter's mean of daily DGS10 closes) less the 10-year and the 5-year CAGR of nominal GDP (BEA via FRED, `fred.gdp_nominal`, already pulled), quarterly, bp, with dual percentiles. This is the US macro r-g.
- **Where it prints:** the 10-year attribution block (`batch5_block`, Plumbing & rates, Weekly and Monthly).
- **Beside it, a fair-value range:** from the lowest to the highest of the 10- and 5-year CAGRs and SR-43's twin-deficit fit (`rates_anchors.fiscal_anchor`), against the latest 10-year. When the fit is absent the line says so.
- **The sovereign scorecard column:** item 21's scorecard is not built, so the column is named "not built" in the slow layers.
- **The 8% forecast** is queued in `docs/dated-appendix-queue.md`, appendix only.
- **The voices register:** the newsletter writer is **not** entered (see the differences and needs-you).

## Part 4: the gate

- **The gate:** `tools/validate_batch14_a1.py`, a new gate, 30 checks, groups A–G, synthetic fixtures only, no network.
- **What it covers:**
  - **(A)** the excess CAPE yield by hand, its dual percentiles and label, absent with its reason, and the forward gap;
  - **(B)** the mortgage spread by hand with its percentiles; "not tracked" for the MBS spread and the GSE holdings; the housing block's hook;
  - **(C)** Shiller's housing sheet parsed and the percentile since 1890 by hand;
  - **(D)** the nominal-growth anchor by hand, with its percentiles, the fair-value range with and without the twin-deficit fit, and its line in the attribution block;
  - **(E)** the proposal validating, seeded into a scratch register as PROPOSED, with F6's tag;
  - **(F)** the slow sub-section and the scorecard's "not built"; no store write, by-hand key, vendor value, composite or market-state import; FRED and Shiller keys only; the new key registered; no person's name or handle in the new code, proposal or appendix lines;
  - **(G)** the three queued appendix entries.
- **Changed and run locally:**
  - `validate_batch14_a1` 30/0;
  - `validate_st_r5_rates` 72/0;
  - `validate_narratives` 103/0 (its pin of committed proposals is now four);
  - `validate_audit_3a` 88/0;
  - `check_registry` OK;
  - `validate_st_r4_t1` 49/0;
  - `validate_official_sources` 336/0;
  - `check_library` 0/0.
- **Left to CI:** the stack gates, which render the Weekly and Monthly.
- **The count:** 126 code gates (123 Python, three shell), counted on main's base. Chain-4, a54 and a55 add gates, so the recount at the merge from main sets it.

## Every listed gap

1. The real 10-year against the S&P **forward** earnings yield: no keyless forward earnings yield (F3).
2. The **current-coupon MBS** spread over the 10-year: no keyless series; an ETF yield is a vendor value.
3. **GSE retained portfolios:** not keyless and simple.
4. The US macro r-g as a column in **item 21's scorecard:** the scorecard is not built.
5. **GTM-2's valuation quad**, **item 20's ledger** and the **Reinhart-Rogoff input:** not in this repo (the differences below).

## Every session-set value, with its reason

| Value | Setting | Reason |
|---|---|---|
| The dual percentiles' short window | five years, beside the full history (`st_r5_rates.lens`) | the metric-lens rule the housing block already uses |
| The excess CAPE yield's real rate | DFII10, the month's mean of daily closes | F3 names DFII10; Shiller's CAPE is a monthly average, so the rate is too |
| The mortgage spread's day | the PMMS release day's DGS10 close | PMMS is weekly; the same day avoids a stale 10-year |
| The real home price percentile | one point a year (the annual rows, then each year's mean of its months), the latest month ranked among them | so 1953 onward does not outweigh 1890–1952 twelve to one |
| The nominal-growth anchor's 10-year | the quarter's mean of daily closes | GDP is a quarterly flow, so the yield is matched to the quarter |
| The fair-value range | the lowest to the highest of the two CAGRs and the twin-deficit fit | the order's "fair-value range" from the anchors, no weighting |
| The proposal's evidence | PMMS falling over four releases at its 10th percentile, the outcome PMMS lower in 90 days | the store answers PMMS itself; the spread is read at report time and is not a stored key |

## Where the order and the code differ

1. **Item 64, "in the valuation quad of what's priced (it amends GTM-2)".** GTM-2's quad is not built: no builder exists, and no Baa yield is stored. So the excess CAPE yield prints in the Monthly's slow layers, beside the Valuation table that stands in for the quad.
2. **Item 69, "beside the Reinhart-Rogoff input".** That input is the Top & Bottom model's and is not in this repo, so the real home price prints on its own line in the slow layers.
3. **Item 69, "item 20's ledger line".** Item 20's Treasury reaction-function ledger is listed, not built (ST-R4.20a, 20b). So its first line, the 8 Jan 2026 intervention, waits in the dated-appendix queue.
4. **Item 69, the X account "to the X pilot's seed list" (F4).** The seed list is the chat-side digest's prompt on Drive, not a file in this repo. It is listed for the operator.
5. **Item 69, "seeded through the register's existing proposal path"** with F6's tag. The register has no tag field, so the tag is written into `proposed_by`, as the existing proposals carry theirs. The paste's rule ("no names of people in any committed file") keeps the handle out: the source is "an X account" tagged promoter.
6. **Item 70, the newsletter writer "goes into the voices register only as F4 allows".** **Not entered.** A voices entry names its voice, and this paste's rules forbid names of people in any committed file. The order's own text names the writer (filed verbatim). This needs the operator's ruling.
7. **Item 70, "the US macro r-g as a column in item 21's sovereign scorecard".** The scorecard is not built, so the column is "not built" and the r-g prints in the anchor line.
8. **F6, "confirms the date and terms against a primary FHFA or GSE release".** No FHFA release exists, and the GSE releases were not readable here (Part 0).
9. **"dual percentiles".** Five years and the full stored history, as `st_r5_rates.lens` reads them.

## The box commands, dry runs first (the operator's)

```
cd ~/chester-reports
# Shiller's pull now also reads Fig3-1.xls (shiller.real_home_price); a one-pull
# dry run is not built into the module, so check the page first:
.venv/bin/python -c "from altdata.sources import _publication as p, shiller as s; print(p.find_link(s.PAGE, s.HOUSING_LINK))"
.venv/bin/python -m altdata.sources.shiller
# The narrative proposal enters at the next seed (the register's own step):
.venv/bin/python -m altdata.narratives seed
# Then the Monthly's dry run (Ari's, as always), which prints the three items:
.venv/bin/python -m monthly_macro.run --dry-run
```

- **Run these inside the windows.** `altdata.sources.shiller` and `narratives seed` write.
- **Nothing else needs a first pull.** The mortgage rate, DFII10, DGS10 and nominal GDP are already pulled.

## Files shared with other branches

| Branch | Files |
|---|---|
| chain-4 | `CLAUDE.md`, `Makefile`, `config/narratives.yaml` (proposals; chain-4 adds two, so the pin becomes six at the merge), `docs/change-orders.md`, `docs/signal-triage-register.md` (index lines), `metrics_registry.yaml`, `monthly_macro/stack.py` (slow layers), `source_registry.yaml`, `tools/validate_narratives.py` (the proposals pin) |
| a54-relative-volume | `CLAUDE.md`, `Makefile`, `docs/change-orders.md`, `docs/signal-triage-register.md`, `metrics_registry.yaml` |
| a55-box-fixes | `CLAUDE.md`, `Makefile` |
| b51-registry-html | `CLAUDE.md`, `Makefile`, `metrics_registry.yaml` |
| b52-batch14-a2 | `CLAUDE.md`, `Makefile`, `docs/dated-appendix-queue.md` (both append at the end), `metrics_registry.yaml`, `monthly_macro/stack.py` (both add slow-layer sub-sections) |

## The CI rounds

| Round | Run | Result |
|---|---|---|
| A56 | (in the closing message) | |

## Needs you

1. **The X account (F4):** add it to the X pilot's seed list in the chat-side digest prompt, tagged promoter. The repo holds no copy of that list.
2. **The newsletter writer in the voices register:** this paste's rule forbids names of people in committed files, and a voices entry names its voice. Rule whether the entry is made (and how), or the voice stays out.
3. **F6's primary check:** no FHFA release on the purchases exists, and the GSE documents were not readable here. Accept the day's reporting and the director's confirmation as the citation, or name the release to cite.
4. **The session-set values** above: confirm or replace.
5. **The box commands** above, after the merge.
6. **The merge:** after chain-4, then main into this branch with a merge commit and a recount (the narratives pin, the gate count, both appendix appends).
