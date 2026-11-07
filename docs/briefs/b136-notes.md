# B136: item 123, the AI infrastructure cash-cycle scorecard (6 Nov 2026)

Paste B136 (`docs/pastes/B136.md`). Batch 22 item 123 (the order's 105), section
0's O-4 and V-105a to V-105d, on `origin/b129-five-filings`. Its rights are Factor
I input lines and a flag. There is no composite change.

**The base.** `origin/main` at `ee04ba21`. `b136-item-123-cash-cycle` is a new
branch from it.

## What was built

- **The facts.** `altdata/sources/edgar_xbrl.py` gains two keyless readers, on
  the contact and pacing it already uses.
  - **Company facts.** For AMZN, GOOGL, MSFT, META, ORCL, CRWV and NBIS:
    remaining performance obligations, operating and finance lease liabilities,
    finance-lease principal payments, operating cash flow and capex. They are
    stored as `edgar.cc_<ticker>_<field>`.
  - **Each periodic filing's own XBRL instance**, for the cloud segment as
    reported. SEC's company-facts API carries no dimensional fact, so AWS's,
    Google Cloud's and Microsoft's segment figures exist only there. They are
    stored as `edgar.seg_<ticker>_revenue` and `_operating_income`.
  - Every fact sits at its filing's acceptance instant.
  - Both ride the daily `edgar_xbrl` pull (`config/cash_cycle.yaml` `facts.enabled`).
    A filer is read again only after a new 10-Q or 10-K is accepted, so the pull
    reads submissions daily and the large files quarterly.
- **The keys.** 48, registered as the bulk import `edgar_cash_cycle`, barred from
  the market-state object and trigger-ineligible.
- **The scorecard.** `altdata/cash_cycle.py`, with `config/cash_cycle.yaml`
  declaring each row's formula and sources. It holds the eight rows and the
  treadmill flag, and reads the store only.
- **The prints.** A Factor I sub-panel:
  - in the Monthly's slow layers, through
    `config/stack_hooks/monthly-slow-cash-cycle.yaml`, right after the AI capex
    chain;
  - in the Disruptive Themes refresh (`themes_block`).

  The Weekly prints nothing.
- **Row 6, folded into SR-16** (V-105c): the private-credit window's line sits in
  SR-16's Factor I lines (`daily_cascade/absorption_block.py`), after the
  AI-credit line, and in the panel.
- **The narrative register.** Two PROPOSED entries through the committed-proposal
  seed path:
  - `ai_capex_j_curve`, the sell-side J-curve as the bull case, carrying its
    incentive tag (sell-side, a semiconductor and hardware franchise);
  - `ai_capex_treadmill`, the treadmill and counterparty-credit reading, as the
    house Bull Rebuttal for Factor I.

  `validate_narratives` counts nine committed proposals; this branch is from
  main, where it counted seven. Confirming or rejecting them is the operator's.

## Tags found and missing per company (the live dry read of 6 Nov, nothing stored)

| Company | Found | Missing |
|---|---|---|
| AMZN | OCF; capex (PaymentsToAcquireProductiveAssets); operating and finance lease liabilities; finance-lease principal; AWS segment revenue and operating income (instances) | RPO: the tag stops in 2020, and the $578bn is in the 10-Q's text, a dated record; PP&E useful life |
| GOOGL | RPO; OCF; capex; both lease liabilities; finance-lease principal; Google Cloud revenue, and its operating income (tagged with the consolidation-items qualifier, ASU 2023-07) | PP&E useful life |
| MSFT | RPO; OCF; capex; both lease liabilities; finance-lease principal; its cloud segment as now reported (`AgentsAndInfraMember`) | Intelligent Cloud as a current member: the segment was redefined, so only two quarters exist under the new definition and the four-quarter margin prints "insufficient"; PP&E useful life |
| META | OCF; capex; both lease liabilities; finance-lease principal | RPO (never tagged); no cloud segment; PP&E useful life |
| ORCL | RPO; OCF; capex; both lease liabilities; finance-lease principal | PP&E useful life (min and max last tagged 2012); its cloud segment is not read (the order names AWS, Google Cloud and Azure) |
| CRWV | RPO; OCF; capex; both lease liabilities (to 30 Jun 2026) | finance-lease principal in four consecutive quarters, so FCF after leases is marked |
| NBIS | RPO; lease liabilities (annual, to 31 Dec 2025) | quarterly flows (an annual filer) |

**From that read, Q3 2026:**

| | AWS | Google Cloud |
|---|---|---|
| Revenue growth on the year | +39.3% | +102.6% |
| Operating margin | 38.6% | 36.2% |

The order quotes 38.7% for AWS and 36.2% for Google Cloud.

**Backlog, against the order's figures.** Alphabet's RPO is $567.7bn against the
thread's $560.8bn, and Microsoft's total RPO is $683.0bn against its $677bn
commercial figure. The differences are definitions, as the order says.

## V-105a: a keyless GPU rental price series (searched once)

Candidates exist:
- **Ornn's Compute Price Index (OCPI).** Its free tier, with no key, gives the
  latest settled value and three months of daily history. Transacted prices.
- **gpu.ai's GPU Cloud Price Index.** A public no-auth JSON API. List prices.

Neither terms nor robots were read, and no writer exists. The 16 Oct rule reads a
source only after a source check, so row 7 prints "gap" naming both until the
operator rules one.

## V-105d: the 3 Nov chat's figures against the filings

| Figure | Finding |
|---|---|
| AWS backlog $578bn | **Confirmed, with a definition.** The Q3 10-Q (accepted 30 Oct): commitments not yet recognized "primarily related to AWS", contracts over one year, "approximately $578 billion as of September 30, 2026". It is Amazon's total, not AWS alone. Filed as a dated record. |
| Google Cloud's incremental margin about 48¢ | **Confirmed on the quarter.** The segment facts give (11.12 − 3.59) / (30.71 − 15.16) = 48.4¢ per added dollar. The four-quarter figure the scorecard prints is about 53¢. |
| 2027 capex "meaningfully more" than about $220bn | **Not in the filed release.** The Q3 release (Exhibit 99.1, 29 Oct) says "We continue to expect 2026 cash capital expenditures to be approximately $220 billion"; the 2027 phrase is not there. It was presumably said on the call, which is not filed. The 2026 guide is filed as a dated record; no 2027 record is filed. |

## The paths that print a placeholder, by design

- **The financing ledger (O-4).** "No confirmed rows". No `docs/scans/signal-scan-*.md`
  file exists yet. A scan's "Financing" section is read as proposed, one row a
  line ending in its URL. A row is confirmed only when a sitting's ruling names
  it in `financing_confirmed`.
  - Amending the scan's prompt to propose rows is item 123.2, the operator's
    chat's, and the line format above is what that prompt fills.
- **The private-credit window.**
  - Oracle's spread is NOT TRACKED: no store key, and no keyless single-name
    spread source.
  - CoreWeave's yields, data-center ABS and CMBS spreads and SpaceX CDS each
    print "no dated record filed". No primary record was found at the build, and
    none is typed by hand.
- **Useful lives.** Cross-referenced to Batch 16 item 83(b) (register row 61),
  whose quarterly read is a listed gap (H3). No filer tags server useful life.
- **The treadmill flag** uses actual capex on the year: the guide is a dated
  record, not a quarterly series, and the line says so.
  - On the live read: AMZN off, GOOGL off, MSFT insufficient (two quarters under
    its segment as reported).

## The gates

| Gate | Result |
|---|---|
| `validate_item_123` (new; clock pinned) | 31 passed, 0 failed |
| `validate_gtm` | 77 passed, 0 failed |
| `validate_st_t1_rest` (SR-16's panel) | 34 passed, 0 failed |
| `validate_themes_panels` | 19 passed, 0 failed |
| `validate_monthly_stack` (in full) | 268 passed, 0 failed |
| `check_registry` | OK |
| `validate_gates` | 32 passed, 0 failed |
| `check_library` | 27 papers, 0 failures, 0 warnings |

Run as well: `validate_narratives` 103/0, `validate_audit_3a` 88/0,
`validate_tb_harness_fpr` 47/0, `validate_secrets` 58/0, `validate_batch14_a2`
40/0, `validate_feed_repair` 59/0 and `validate_price_sources` 65/0.

**Outside the paste's file list:**
- `tools/validate_audit_3a.py`: one name in its list of bulk-import blocks;
- `config/catalogue_commands.yaml`: one line;
- CLAUDE.md's gate count, 167 to 168;
- the Monthly's hook file.

**For chain-13's merge.** B134 and B135 each move CLAUDE.md's count to 168 too,
so the final count after all three is 170 code gates (167 Python). Likewise
`validate_narratives`' count of committed proposals: eight after B133 and nine
after this one, so ten after both.

## CI

Read once after the push.

**B142.** CI run 42328165216 was red on `validate_batch14_b2`: "the proposals
pin is seven". The pin is now nine (this branch's `ai_capex_j_curve` and
`ai_capex_treadmill`); chain-13's stitch sets it to ten.
