# GTM batch, part 1 — fixtures and their hand figures

These are synthetic, not market data. `tools/validate_gtm.py` seeds a temporary
store from them and holds every table to the figures below. The figures were
worked by hand before the code ran.

## GTM-9, `ath_closes.csv` (12 sessions, 30 Dec 2025 to 15 Jan 2026)

| Day | Close | All-time high? | Floor? | Another within 5 sessions? |
|---|---|---|---|---|
| 30 Dec | 100 | first close, no | — | — |
| 31 Dec | 101 | yes | yes: the lowest later close is 97, above 95.95 | yes (2 Jan) |
| 2 Jan | 102 | yes | yes: 97 is above 96.90 | yes (6 Jan) |
| 5 Jan | 99 | no | | |
| 6 Jan | 103 | yes | no: 97 is below 97.85 | yes (7 Jan) |
| 7 Jan | 104 | yes | no: 97 is below 98.80 | yes (12 Jan, 3 sessions on) |
| 8 Jan | 97 | no | | |
| 9 Jan | 98 | no | | |
| 12 Jan | 105 | yes | yes: 103 is above 99.75 | yes (13 Jan) |
| 13 Jan | 106 | yes | yes: 103 is above 100.70 | no (only 2 sessions follow) |
| 14 Jan | 104 | no | | |
| 15 Jan | 103 | no | | |

- **Whole series:** 6 all-time highs in 12 sessions, so 50% of sessions. 4 floors, so 66.67%. 5 followed by another within a week, so 83.33%.
- **Year to date at 15 Jan 2026:** 5 all-time highs (2, 6, 7, 12 and 13 Jan) in 10 sessions, so 50%.

## GTM-8, `sentiment_monthly.csv` and `spx_month_end.csv`

- **Sentiment:** 80 in every month from 2000-01 to 2004-12, except 100 in 2001-06 and 50 in 2002-12.
- **Turning points**, with a 12-month window and a 15-point swing:
  - one peak, 2001-06;
  - one trough, 2002-12.
  - 2004 has no turning point. Its window runs past the data.
- **The S&P 500:** 1,000 to 2001-12, then 900 to 2002-11, 800 in 2002-12, 850 to 2003-11, and 1,000 from 2003-12.
- **The peak:** 1,000 to 900 over the next 12 months, so −10.00%. n = 1.
- **The trough:** 800 to 1,000, so +25.00%. n = 1.
  - It is 20% below the prior 12-month high of 1,000, so 1 of 1 troughs came at a price low.
- **The current reading:** 80, at the 98.33rd percentile of 60 readings (59 are at or below 80). The S&P 500 is 0.0% from its high.

## GTM-13

`shy_ytd.csv` gives the year-to-date total return. It runs from the 31 Dec close of 100 through 101, then 99 with a 0.50 dividend, then 102:

    (101 / 100) × ((99 + 0.5) / 101) × (102 / 99) − 1 = 0.995 × 1.030303 − 1 = +2.5152%

`fi_series.csv` gives the correlations. The 10-year is 4.00 + 0.05·sin(i), on business days from 1 Dec 2025 to 30 Jan 2026.
- TLT's daily return is exactly −0.165 × the change in the 10-year (in percent), so the correlation to the 10-year's change is −1.00.
- SPY's daily return is exactly twice TLT's, so TLT's correlation to SPY is +1.00.

The duration rows come from `config/instrument_reference.yaml`:
- **TLT (16.5 years):** +16.5% under −100 bp, −16.5% under +100 bp.
- **SHY (1.9 years):** ±1.9%.
- **AGG:** carries no duration, so it prints "no duration in the reference".
- **TIPS, munis and MBS:** have no proxy, so they print "no proxy".

## GTM-15, `tariff.csv`

| Quarter | Customs (bn, SAAR) | Imports (three months, mn) | Annual imports (bn) | Rate |
|---|---|---|---|---|
| 2025 Q4 | 200 | 750,000 | 3,000 | 6.6667% |
| 2026 Q1 | 300 | 750,000 | 3,000 | 10.0000% |
| 2026 Q2 | 400 | 810,000 | 3,240 | 12.3457% |

The latest reading is 12.35%, at the 100th percentile of 3 (both windows).

## GTM-21, `dsr.csv`

TDSP:
- 13.0 in 2005 Q1;
- 11.0, 11.2, 11.1 and 11.3 across the four quarters of 2024.

The latest reading is 11.3 (2024 Q4):
- **five years:** the 2024 quarters only, n = 4, so the 100th percentile;
- **full history:** n = 5, with 4 at or below 11.3, so the 80th percentile.

## GTM-7 (built in the gate)

The monthly series cover 1998-01 to 2003-12:
- The dividend is zero.
- The price compounds at 2 × the bond's total return + 0.1% a month, so every 24-month correlation is +1.00.
- CPI compounds at 0.5% a month, so inflation on the year is 1.005¹² − 1 = 6.1678%.

The bond is a par bond bought at last month's yield and priced at this month's, plus a month's coupon. A 5% coupon priced at 6% returns:

    0.05/0.06 × (1 − 1.03⁻²⁰) + 1.03⁻²⁰ − 1 + 0.05/12 = −7.022%

How the eras resolve:
- An era from 2000 to 2001 is covered, at +1.00.
- An era from 1990 to 1995 is not reached, so it prints the Guide's figure, labelled.

# Part 2 (gtm-core-2, 17 Oct 2026)

Every value below is synthetic. Each hand figure is plain arithmetic on the file, and `tools/validate_gtm.py` groups K to Q hold the code to it.

## GTM-3, `holdings_multiples.csv`

Two holdings days, 15 and 16 Oct 2026, with the same fourteen lines. Each line carries a weight (% of SPY), a trailing P/E and a forward P/E. GOOG counts with GOOGL, so the ten largest issuers are NVDA, MSFT, AAPL, AMZN, Alphabet, META, AVGO, TSLA, BRK-B and JPM. ORCL (1.2), LLY and XOM fall outside.

The index:
- the S&P 500 closes at 5,940 on 15 Oct and 6,000 on 16 Oct;
- Shiller's trailing earnings are 240 for June 2026;
- S&P DJI's forward twelve-month operating EPS is 300 (1 Oct).

So on 16 Oct the index's trailing P/E is 25 and its forward P/E is 20.0 (19.8 on 15 Oct).

The 16 Oct figures:
- **Cap share:** 8 + 7 + 6 + 4 + 4 + 3 + 2.5 + 2 + 1.5 + 1.4 = **39.4%**.
- **Earnings share:** the sum of w/PE is 0.0117714 (weights as fractions), and 100 × 0.0117714 × 25 = **29.4286%**.
- **Forward P/E, the top 10:** the sum of w/fPE is 0.0141797, and 0.394 / 0.0141797 = **27.7861x**.
- **The other 490:** 0.606 / (1/20 − 0.0141797) = **16.9178x** (16.6826x on 15 Oct).
- **Own averages over the two days:**
  - the index: 19.9x, so 20.0 is **100.50%** of it;
  - the other 490: 16.8002x, so **100.70%**;
  - the top 10: the same on both days, so **100%**.

Drop BRK-B's forward P/E and the top 10's and the other 490's forward P/E are not computed. The cell names BRK-B, and the Guide's 20.9x prints beside it.

## GTM-4, `holdings_multiples.csv` and `hyperscaler_closes.csv`

The hyperscalers on 16 Oct are AMZN 4, GOOGL 2, GOOG 2, META 3, MSFT 7 and ORCL 1.2, so the bucket's weight is **19.2%**.

Year to date, from the 31 Dec 2025 close, the members return +10%, +10%, +10%, −10%, +5% and +50%.
- Each starting weight is w / (1 + r), and they sum to 18.0727.
- The market-weighted return is 1.12727 / 18.0727 = **+6.2374%**.

The NTM P/E is 19.2 / Σ(w / fPE), where the forward P/Es are 30, 20, 20, 24, 30 and 25: 19.2 / 0.739667 = **25.9576x**.

Drop ORCL's forward P/E and the bucket's NTM P/E prints the Guide's 22.2x, labelled. The four GICS buckets have no members and print the Guide's figures.

## GTM-4's bridge, `xbrl_frames.json`

The shape of EDGAR's frames, with synthetic values.

CY2023, in USD bn:
- **Operating cash flow:** 80 + 100 + 70 + 110 + 20 = **380**. Microsoft's year to June 2024 and Oracle's to May 2024 sit in CY2023.
- **Capex:** Amazon 50 (PaymentsToAcquireProductiveAssets), Alphabet 30, Meta 28, Microsoft 40, Oracle 7, so **155**. Alphabet's 999 under the second tag is ignored, because the first tag wins.
- **Cash flow less capex:** **225**.
- A non-hyperscaler CIK is ignored.

CY2024:
- **Operating cash flow:** **470**.
- **Capex:** Meta has no capex tag, so the year prints **"not stored (META)"** and no difference.

## GTM-10, `sector_corr.csv`

Six sessions of one ETF and DGS10:
- the ETF's returns are −1%, +1%, −1%, 0% and −1%;
- the 10-year's changes are +10, −5, +15, −5 and +10 bp.

Their correlation is −0.30 / √(0.00032 × 350) = **−0.8964**. With a window of 5 and 90% coverage, 4 pairs are needed and 5 are held. A window of 10 needs 9, so it is **"not reached (5 of 10)"**.

## GTM-15 monthly, `mts_customs.json`

Gross customs, against BOPGIMP of 240,000, 252,000 and 250,000 million:
- **July to September:** 24.0, 25.2 and 27.0 bn, so **10.0%, 10.0% and 10.8%**.
- **Three months to September:** 76.2 / 742 = **10.2695%**.
- **Refunds in September:** 20bn.
- The Excise Taxes line is skipped.

## GTM-12 (built in the gate)

National accounts, $bn SAAR:
- **Interest payments:** 1,000 in 2025 Q2 and 1,100 in 2026 Q2, against current expenditures of 6,800 and 7,000. The shares are 14.7059% and **15.7143%**, the latter the 100th of 2.

The budget, $ mn, FY2025:
- **Net interest outlays:** 1,000,000 against net outlays of 7,000,000, so **14.2857%**.
- **The deficit:** FYFSD −1,800,000 prints **$1,800bn** and **25.7143%** of net outlays.
- **The deficit to GDP:** FYFSGDA188S −5.9 prints **5.9% of GDP**.
