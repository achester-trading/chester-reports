# AI-lab financials ledger (ST-R6.75a)

*Signal-triage Batch 15, item 75 (written as 68). Template written 23 Oct 2026 by
session B. Report only.*

**Disclosure.** Item 75 concerns Anthropic, the company that builds Claude, which
drafted the order this ledger comes from (and, here, this template). The ledger
records only figures disclosed in a filing, or reported as disclosed in one, and
the measures the framework computes from them. It takes no view on the company.

**What it is.** One row per frontier lab and reporting period, from public
disclosures: the S-1 and its amendments, then 10-Qs and 10-Ks, and the same for
any other lab that files. The figures in a row are entered as published, each row
with its source and URL; **the ratios are computed by code**
(`altdata/ai_lab_ledger.py`), never typed here.

**Status of entries (G3; ruling D21 of 24 Oct 2026).**
- **Entries come from filings only.** A session makes each entry from a filed
  document -- the S-1 and its amendments, a 10-Q, a 10-K, or an equivalent public
  filing -- cited by its URL, about once a quarter (about an hour a quarter).
  **Press reports are never a source for an entry.** The operator's explicit yes
  for the quarterly rows is ruling D21 (rule 30); no row is added on the day of
  the ruling.
- **The first entry is a dated record, marked provisional.** Anthropic's S-1 was
  not public on EDGAR when this template was written (public reporting to 22 Oct
  2026; the session had no SEC contact configured, so EDGAR itself was not
  read). Its figures are the draft prospectus as the Wall Street Journal reported
  it, relayed by the source in its row. It stays a provisional dated record until
  the S-1 is on EDGAR, and is then replaced by a row from the filing.

**The fields** (the order's list). Entered: revenue for the period and for the
same period a year earlier; compute and infrastructure spending; net loss; the
non-cash charges related to financing instruments; forward commitments;
trailing-twelve-month revenue; the top-two-customer share of revenue. Computed:

| Measure | Computed as |
|---|---|
| Revenue growth | revenue ÷ revenue a year earlier − 1 |
| Compute and infrastructure share of revenue | compute and infrastructure ÷ revenue |
| Cash burn excluding non-cash financing charges | net loss − non-cash financing charges (a loss measure, not a cash-flow statement figure; labelled so) |
| Forward commitments ÷ TTM revenue | forward commitments ÷ trailing-twelve-month revenue; not computed when TTM revenue is not in the entry |
| Top-two-customer concentration | as entered |

A blank cell is "not in the entry", never zero.

## Entries

| Lab | Period | Period end | Reported | Status | Revenue ($bn) | Revenue a year earlier ($bn) | Compute and infrastructure ($bn) | Net loss ($bn) | Non-cash financing charges ($bn) | Forward commitments ($bn) | TTM revenue ($bn) | Top-two customers (% of revenue) | Source | URL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Anthropic | H1 2026 | 2026-06-30 | 2026-10-20 | provisional | 16.3 | 1.1 | 9 | 80.7 | 72 | 450 | | 20 | The draft S-1 as the Wall Street Journal reported it, relayed by Investing.com (20 Oct 2026); compute "nearly $9 billion", charges "$72 billion", commitments "roughly $450 billion in cloud compute agreements over the next decade", two customers "approximately 20%"; TTM revenue not reported | https://www.investing.com/news/stock-market-news/anthropic-revenue-hits-163-billion-as-preliminary-s1-outlines-ipo-risks--wsj-4960928 |

*Not entered: the order's source post adds "up to $86bn of Nvidia chip rental";
the relayed report does not carry it, and a figure without its source is not
entered.*
