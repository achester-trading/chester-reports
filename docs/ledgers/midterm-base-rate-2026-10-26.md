# Midterm base-rate ledger -- the midterm-year table, computed from the store

**Edition:** 2026-10-26, laptop run, the laptop's store. A re-run against the box's store supersedes it (a new dated file); this file is never edited.

**The computation is pre-registered** below, with its SHA-256; a re-run applies it and may not change it.

| | |
|---|---|
| As of | 2026-09-21 (the store's last S&P 500 close) |
| Window | 1927-12-30 to 2026-09-21; midterm years 1950 to 2022, other years 1950 to 2025 |
| n | 19 (midterm years); 57 other years |
| Statistic | each midterm year's drawdown, the low's place against election day, forward returns from the low and from election day, the recession flag; the drawdown's mean and median against the other years |
| Pass rule (as the order states it) | none in the order (items 80(b) and 90 grant base-rate rights) |
| Verdict | **NO GATE IN THE ORDER -- base rate recorded. Items 80(b) and 90 grant base-rate rights and state no pass rule; none is supplied here.** |
| Rights consequence | Base-rate rights only (90): the table and its headline print beside the 3 Nov 2026 row in the Weekly's Ahead and in the Base Rates paper's dated appendix, never as a forecast and never as a trigger. |
| Computation SHA-256 | `8c8fa32c97ad458c2c9047269775d125896228b8c8ec01cc066168fc3349b9df` |
| CSV SHA-256 | `805487eced3eaf215b0ba6ecd48876e1d28fc054f04e0fdbf74ce7eb67fb7a64` (midterm-base-rate-2026-10-26.csv) |

## The computation, pre-registered

<!-- computation:begin -->
```text
THE SAMPLE. Every US midterm year from 1950 to the last one completed: 1950,
1954, ..., 2022, nineteen years, none omitted. The other years are every
calendar year from 1950 to the last complete year that is not a midterm year.

THE CLOSES. The store's S&P 500 daily closes (yfinance.mkt_gspc), price only,
the newest vintage of each session.

ELECTION DAY. The first Tuesday after the first Monday in November (2 U.S.C. 7).
The election-day close is the close of the last session on or before election
day (the exchange was shut on election day in the early years of the sample).

THE YEAR'S DRAWDOWN. Over the calendar year's sessions, the largest fall from a
running peak to a later close, peak and trough both inside the year, as a
negative percent of the peak.

THE YEAR'S LOW. The trough of the year's drawdown: the close at which that
largest fall ended (the first, if two are equal). It is not always the year's
lowest close -- in a rising year that is an early-January session -- so the
lowest close's date is carried in the CSV beside it, for reference only.
Against election day: SESSIONS is the count of sessions from the low to the
election-day close (positive when the low came first); DAYS is election day
less the low's date, in calendar days.

FORWARD RETURNS. From the low's close and from the election-day close, the
price return to the close of the last session on or before the same day of the
month 1, 3, 6 and 12 months later (the month's last day when that day does not
exist); blank when that date is after the last stored close.

THE RECESSION FLAG. yes when fred.usrec is 1 in any month of the calendar year,
no when it is 0 in all twelve, "not stored" when the store holds fewer than
twelve months of it for that year.

THE COMPARISON. The mean and the median of the year's drawdown over the
nineteen midterm years and over the other years, each with its n. The
headline also counts the lows that came before election day and those in
August to October, and the years higher twelve months after election day,
beside the other years' count from the same day (the first Tuesday after the
first Monday in November), so the market's drift is not read as the cycle's.
```
<!-- computation:end -->

## Sources and vintages

- The observation store's yfinance.mkt_gspc: daily closes, first stored 1927-12-30, last 2026-09-21
- The observation store's fred.usrec: not stored

## Results

| Year | Election day | Drawdown | Peak → trough | Low | Low to election (sessions / days) | From the low +1m / +3m / +6m / +12m | From election day +1m / +3m / +6m / +12m | Recession |
|---|---|---|---|---|---|---|---|---|
| 1950 | 1950-11-07 | −14.0% | 1950-06-12 → 1950-07-17 | 1950-07-17 | 78 / 113 | +11.2% / +19.2% / +29.2% / +31.4% | +0.5% / +14.3% / +17.6% / +17.9% | not stored |
| 1954 | 1954-11-02 | −4.4% | 1954-08-20 → 1954-08-31 | 1954-08-31 | 43 / 63 | +8.3% / +14.8% / +23.2% / +44.8% | +6.9% / +15.5% / +19.4% / +33.0% | not stored |
| 1958 | 1958-11-04 | −4.4% | 1958-02-04 → 1958-02-25 | 1958-02-25 | 175 / 252 | +4.5% / +8.0% / +17.6% / +36.0% | +1.9% / +7.2% / +11.8% / +11.3% | not stored |
| 1962 | 1962-11-06 | −26.4% | 1962-01-03 → 1962-06-26 | 1962-06-26 | 92 / 133 | +8.5% / +7.3% / +20.4% / +32.7% | +6.9% / +13.3% / +20.0% / +25.9% | not stored |
| 1966 | 1966-11-08 | −22.2% | 1966-02-09 → 1966-10-07 | 1966-10-07 | 21 / 32 | +10.3% / +12.3% / +22.1% / +32.9% | +1.2% / +7.7% / +17.0% / +13.3% | not stored |
| 1970 | 1970-11-03 | −25.9% | 1970-01-05 → 1970-05-26 | 1970-05-26 | 113 / 161 | +6.0% / +17.2% / +22.8% / +43.7% | +5.6% / +14.7% / +22.6% / +12.7% | not stored |
| 1974 | 1974-11-05 | −37.6% | 1974-01-03 → 1974-10-03 | 1974-10-03 | 23 / 33 | +18.6% / +13.5% / +30.9% / +38.0% | −12.0% / +5.1% / +19.9% / +18.7% | not stored |
| 1978 | 1978-11-07 | −13.6% | 1978-09-12 → 1978-11-14 | 1978-11-14 | -5 / -7 | +3.8% / +6.9% / +6.0% / +11.8% | +3.4% / +3.5% / +5.5% / +6.4% | not stored |
| 1982 | 1982-11-02 | −16.6% | 1982-01-04 → 1982-08-12 | 1982-08-12 | 57 / 82 | +18.1% / +36.2% / +44.2% / +58.3% | +1.0% / +4.2% / +17.9% / +19.9% | not stored |
| 1986 | 1986-11-04 | −9.4% | 1986-09-04 → 1986-09-29 | 1986-09-29 | 26 / 36 | +4.8% / +6.4% / +28.8% / +39.9% | +2.8% / +13.6% / +17.5% / +1.1% | not stored |
| 1990 | 1990-11-06 | −19.9% | 1990-07-16 → 1990-10-11 | 1990-10-11 | 18 / 26 | +6.2% / +6.7% / +27.8% / +29.1% | +5.6% / +14.9% / +22.0% / +25.1% | not stored |
| 1994 | 1994-11-08 | −8.9% | 1994-02-02 → 1994-04-04 | 1994-04-04 | 152 / 218 | +2.9% / +1.7% / +3.6% / +15.1% | −4.3% / +3.3% / +12.5% / +27.1% | not stored |
| 1998 | 1998-11-03 | −19.3% | 1998-07-17 → 1998-08-31 | 1998-08-31 | 45 / 64 | +6.2% / +21.6% / +29.4% / +37.9% | +3.5% / +14.5% / +21.9% / +22.0% | not stored |
| 2002 | 2002-11-05 | −33.8% | 2002-01-04 → 2002-10-09 | 2002-10-09 | 19 / 27 | +15.2% / +19.4% / +11.5% / +33.7% | −1.0% / −7.8% / +1.2% / +14.9% | not stored |
| 2006 | 2006-11-07 | −7.7% | 2006-05-05 → 2006-06-13 | 2006-06-13 | 103 / 147 | +1.5% / +7.7% / +15.5% / +23.9% | +1.8% / +4.9% / +9.2% / +6.7% | not stored |
| 2010 | 2010-11-02 | −16.0% | 2010-04-23 → 2010-07-02 | 2010-07-02 | 85 / 123 | +10.1% / +12.1% / +23.0% / +31.0% | +2.3% / +9.2% / +14.1% / +3.7% | not stored |
| 2014 | 2014-11-04 | −7.4% | 2014-09-18 → 2014-10-15 | 2014-10-15 | 14 / 20 | +9.5% / +7.0% / +13.1% / +8.7% | +3.0% / +1.5% / +5.1% / +4.5% | not stored |
| 2018 | 2018-11-06 | −19.8% | 2018-09-20 → 2018-12-24 | 2018-12-24 | -32 / -48 | +12.4% / +19.1% / +25.3% / +37.1% | −2.2% / −0.9% / +6.4% / +11.7% | not stored |
| 2022 | 2022-11-08 | −25.4% | 2022-01-03 → 2022-10-12 | 2022-10-12 | 19 / 27 | +11.6% / +11.3% / +14.4% / +21.6% | +3.5% / +7.6% / +8.1% / +14.5% | not stored |

| The year's drawdown | n | Mean | Median |
|---|---|---|---|
| Midterm years | 19 | −17.5% | −16.6% |
| Other years | 57 | −12.4% | −9.9% |

The low against election day: before it in 17 of 19 years, 10 of them in August to October; the median low came 63 calendar days before election day. From election day: median +7.6% at 3 months; higher at 12 months in 19 of 19, median +14.5%. From the low: higher at 12 months in 19 of 19, mean +32.0%.

**The headline the Weekly's Ahead prints** (copied into `config/weekly_ahead.yaml`, held to this file by `tools/validate_batch16_midterm.py`):

> Base rate, the 19 midterm years since 1950 (ledger 2026-10-26): the year's drawdown, median −16.6% (mean −17.5%), against −9.9% (mean −12.4%) in the 57 other years; the year's low came before election day in 17 of 19, 10 of them in August to October; from election day the S&P 500 was higher 12 months later in 19 of 19, median +14.5%, against 39 of 56 other years from the same day; n = 19.

## The order's chat figures against this ledger (V11)

The order's figures were approximate; this ledger replaces them. Both, where they differ:

| Figure | The order (chat) | This ledger |
|---|---|---|
| 1974's drawdown | −35% | −37.6% |
| 2022's drawdown | −27% | −25.4% |
| 1986's drawdown | ≈ −9% | −9.4% |
| 2006's drawdown | ≈ −8% | −7.7% |
| 2014's drawdown | ≈ −7% | −7.4% |
| Midterm-year drawdown since 1950 | ≈ 17–19% | mean −17.5%, median −16.6% |
| All years' intra-year decline since 1980 (the order cites JPM's Guide) | ≈ 14% | mean −14.1% (closes; JPM's figure is its own measure) |
| Where the midterm-year lows fell | usually late summer to October | 10 of 19 in August to October |
| 12 months after the midterm-year low | higher every time since 1950, ≈ +30% on average | higher in 19 of 19, mean +32.0% |
| 2026's drawdown to date | −9% through 30 Sep (JPM 4Q GTM) | −9.1% through 2026-09-21 (the store's last close) |

## Caveats

- The S&P 500 is its price, not its total return; the drawdown is on closes, so an intraday low below the year's lowest close is not seen.
- USREC is NBER's dating, published long after the fact: the recession column is a historical label, not something knowable on election day. fred.usrec is not in this store, so the recession column reads "not stored"; the box's re-run fills it.
- Returns FROM THE LOW are hindsight: the low is known only after it. The order asks for them and they are printed; the Weekly's Ahead quotes only the election-day form, a date known in advance, as the Base Rates paper's ex-ante table does (`baserate.midterm_from_election`, tools/base_rates.py Table 7, with its all-years and every-session comparators and a binomial p).
- Nineteen years is a small sample, and the years are not independent draws: a base rate to read beside the row, not a forecast.

The rows are in `midterm-base-rate-2026-10-26.csv`, beside this file.
