# SR-8 ledger -- the false-bottom audit: the bottom side, rally by rally

**Edition:** 2026-10-18, laptop run, public sources. A re-run against the box's store supersedes it (a new dated file).

| | |
|---|---|
| As of | S&P 500 2026-10-16; French CRSP 202608; FINRA margin 2026-09 |
| Window | 1973-74 1973-01-11 to 1974-10-03; 2000-02 2000-03-24 to 2002-10-09; 2007-09 2007-10-09 to 2009-03-09; 2022 2022-01-03 to 2022-10-12; Nasdaq 2000-03-10 to 2002-10-09 (count only) |
| n | 16 |
| Statistic | false bottoms per bear; each confirmation element's firing rate at the true bottoms against the false ones |
| Pass rule (as the order states it) | the register's: elements that discriminate enter the gate, those that don't are dropped. Pre-registered by this first edition: an element discriminates at >= 75% of >= 2 testable true bottoms and <= one third of >= 3 testable false ones; the audit PASSes with >= 2 discriminating (the gate asks two) |
| Verdict | **FAIL -- 1 element(s) discriminate (breadth_rsp_spy); 12 false bottoms and 4 true across the four bears (S&P 500); rule: >= 2 discriminate, each firing at >= 75% of testable true bottoms and <= one third of testable false ones** |
| Rights consequence | PASS: the gate specification above is what ST-11 wires at T&B full, and the Doctrine proposal goes to the monthly. FAIL or INSUFFICIENT: the specification stands as written, with its gaps, and the monthly decides. Book A rule A-2 changes nothing until then. Stated, not granted: the verdict reaches the register only as a rule-31 draft, and no right changes until the operator accepts it. |

## Sources and vintages

- Yahoo daily closes (altdata.import_yfinance): ^GSPC, ^IXIC, ^VIX, ^VIX3M, XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY, XLRE, XLC, RSP, SPY
- Kenneth French data library (no key; free for research use): 49_Industry_Portfolios_daily_CSV.zip, value-weighted daily returns; vintage CRSP 202608
- FRED graph CSV (no key): DBAA, DGS10, BAA, GS10 (ICE BofA HY OAS is served only from 2023-10, so it reaches no episode)
- FINRA margin statistics, margin-statistics.xlsx (no key), through altdata/sources/finra.py; Customer Margin Balances from 1997
- FINRA consolidated short interest API (anonymous) through altdata/loggers/borrow.py; SPY from 2017-12-29

## Results

**The replay** (S&P 500 closes; a candidate is a new bear low followed by a 10% rally before a lower close):

| Bear | Trough | Kind | Rally | Rally peak | Undercut | Below a falling 200-day |
|---|---|---|---|---|---|---|
| 1973-74 | 1973-08-22 | false | +10.8% | 1973-10-12 | 1973-11-20 | yes |
| 1973-74 | 1974-02-11 | false | +10.0% | 1974-03-13 | 1974-04-24 | yes |
| 1973-74 | 1974-10-03 | true | +53.5% | 1975-07-15 | - | yes |
| 2000-02 | 2000-04-14 | false | +12.1% | 2000-09-01 | 2000-10-12 | no |
| 2000-02 | 2001-04-04 | false | +19.0% | 2001-05-21 | 2001-09-07 | yes |
| 2000-02 | 2001-09-21 | false | +21.4% | 2002-01-04 | 2002-07-02 | yes |
| 2000-02 | 2002-07-23 | false | +20.7% | 2002-08-22 | 2002-10-07 | yes |
| 2000-02 | 2002-10-09 | true | +33.8% | 2003-09-18 | - | yes |
| 2007-09 | 2008-03-10 | false | +12.0% | 2008-05-19 | 2008-07-02 | yes |
| 2007-09 | 2008-10-10 | false | +11.6% | 2008-10-13 | 2008-10-22 | yes |
| 2007-09 | 2008-10-27 | false | +18.5% | 2008-11-04 | 2008-11-19 | yes |
| 2007-09 | 2008-11-20 | false | +24.2% | 2009-01-06 | 2009-02-23 | yes |
| 2007-09 | 2009-03-09 | true | +70.0% | 2010-01-19 | - | yes |
| 2022 | 2022-03-08 | false | +11.1% | 2022-03-29 | 2022-04-29 | no |
| 2022 | 2022-06-16 | false | +17.4% | 2022-08-16 | 2022-09-26 | yes |
| 2022 | 2022-10-12 | true | +28.3% | 2023-07-31 | - | yes |

False bottoms by bear: 1973-74 2; 2000-02 4; 2007-09 4; 2022 2. Nasdaq Composite 2000-02, the same rule: 8 false bottoms (2000-04-14 +19%, 2000-05-23 +35%, 2000-10-12 +13%, 2000-11-30 +16%, 2001-01-02 +25%, 2001-04-04 +41%, 2001-09-21 +45%, 2002-08-05 +18%).

**The scores** (each element read at the trough plus 30 sessions, or before an undercut):

| Element | Register's item | Key | True bottoms firing | False bottoms firing | Not testable before | Word |
|---|---|---|---|---|---|---|
| breadth_industries | breadth thrust | French 49 industries, the breadth-thrust form (proxy) | 4 of 4 | 5 of 12 | testable throughout | **DOES NOT DISCRIMINATE** |
| breadth_sectors | breadth thrust | calc.breadth_sector_above_50d's arithmetic | 2 of 3 | 2 of 10 | 2000-04-14 | **DOES NOT DISCRIMINATE** |
| breadth_rsp_spy | breadth thrust | calc.breadth_rsp_over_spy | 2 of 2 | 2 of 6 | 2008-03-10 | **DISCRIMINATES** |
| new_leadership | leadership by new groups | French 49 industries (proxy) | 2 of 4 | 3 of 12 | testable throughout | **DOES NOT DISCRIMINATE** |
| credit_tightening | HY spreads tightening | Moody's Baa less the 10-year (proxy) | 3 of 4 | 7 of 12 | testable throughout | **DOES NOT DISCRIMINATE** |
| vix_contango | VIX term structure in contango | calc.vix3m_over_vix | 2 of 2 | 4 of 6 | 2008-03-10 | **DOES NOT DISCRIMINATE** |
| retest | a successful retest | S&P 500 closes | 4 of 4 | 7 of 12 | testable throughout | **DOES NOT DISCRIMINATE** |
| margin_spent | fuel: margin debt | finra.margin_debit | 2 of 3 | 2 of 10 | 2000-04-14 | **DOES NOT DISCRIMINATE** |
| short_fuel | fuel: short interest | finra.short_interest_days_to_cover (SPY) | 0 of 1 | 0 of 2 | 2022-03-08 | **NOT TESTABLE** |
| time_prior | the time prior | months since the bear's peak | 2 of 4 | 2 of 12 | testable throughout | **DOES NOT DISCRIMINATE** |
| leveraged_etf_aum | fuel: leveraged-ETF AUM | none | - | - | never (a gap) | **LISTED GAP** |

**Each candidate's reads:**

| Trough | Kind | breadth_industries | breadth_sectors | breadth_rsp_spy | new_leadership | credit_tightening | vix_contango | retest | margin_spent | short_fuel | time_prior |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1973-08-22 | false | yes | n/t | n/t | yes | no | n/t | no | n/t | n/t | no |
| 1974-02-11 | false | yes | n/t | n/t | no | yes | n/t | no | n/t | n/t | no |
| 1974-10-03 | true | yes | n/t | n/t | yes | no | n/t | yes | n/t | n/t | yes |
| 2000-04-14 | false | no | no | n/t | yes | yes | n/t | yes | no | n/t | no |
| 2001-04-04 | false | no | yes | n/t | no | yes | n/t | no | yes | n/t | no |
| 2001-09-21 | false | yes | no | n/t | no | yes | n/t | yes | yes | n/t | yes |
| 2002-07-23 | false | no | no | n/t | yes | no | n/t | yes | no | n/t | yes |
| 2002-10-09 | true | yes | yes | n/t | no | yes | n/t | yes | no | n/t | yes |
| 2008-03-10 | false | no | no | no | no | yes | yes | no | no | n/t | no |
| 2008-10-10 | false | no | no | no | no | no | no | yes | no | n/t | no |
| 2008-10-27 | false | no | no | no | no | no | no | yes | no | n/t | no |
| 2008-11-20 | false | yes | yes | yes | no | yes | yes | yes | no | n/t | no |
| 2009-03-09 | true | yes | no | yes | yes | yes | yes | yes | yes | n/t | no |
| 2022-03-08 | false | yes | no | yes | no | yes | yes | no | no | no | no |
| 2022-06-16 | false | no | no | no | no | no | yes | yes | no | no | no |
| 2022-10-12 | true | yes | yes | yes | no | yes | yes | yes | yes | no | no |

## The gate specification

- **State:** the T&B top side has fired and the S&P 500 is below a falling 200-day (the 200-session mean under its value 20 sessions earlier).
- **Then:** the bottom threshold rises (its level is T&B's, set at T&B full) and two of the confirmation set are required, read at the trough plus 30 sessions.
- **The set (elements that discriminate):** breadth_rsp_spy.
- **Dropped (do not discriminate):** breadth_industries, breadth_sectors, new_leadership, credit_tightening, vix_contango, retest, margin_spent, time_prior.
- **Not testable on our n:** short_fuel; and leveraged-ETF AUM: no keyless history known (issuer daily files carry today's holdings, not a history); a listed gap, no key pursued.
- **Two of the set cannot bind**: fewer than two elements discriminate, so the register's 'two of the confirmation set' has no set to count; the Doctrine monthly decides what stands in its place.
- **Wiring:** none. The stub (config/tb_false_bottom_gate.yaml) is read by no module until T&B full (ST-11).

## The Doctrine rule proposal

**A proposal for the Doctrine monthly of 7-8 Nov, drafted under rule 31. It grants nothing, and its number is the monthly's to assign. Accepted onto the Doctrine #2 agenda, 19 Oct 2026; a proposal until the sitting rules.**

> *In a declared bear regime a rally is a mechanism, not a signal. Book A re-entry requires the bottom composite plus confirmation from the audited set, in a number the monthly sets (breadth_rsp_spy), read in the rally's first six weeks. Size on the assumption that a bear rally and a new bull are indistinguishable in real time.*

The register's candidate text is kept, with the change the audit supplies: 'confirmation' names the audited set rather than the register's five, because elements that did not discriminate are dropped.
The audit found 1 element(s) that discriminate, so the register's 'two of the confirmation set' has no second member: whether the raised threshold stands alone, or the one element with it, is the monthly's decision, not this ledger's.

**Sourced comparison, not episodes of ours:** the register's cited chart (Nasdaq 2000-02, 19 Sep 2026): five rallies of 12-45% inside a 78% decline, each a bottom in real time; and the Tops & Bottoms paper (docs/whitepapers/tops-and-bottoms-whitepaper.md): fewer than one in five NYSE issues above their 200-day at the 1974 low; the 1929-30 rally of +46% the archetype.

## Caveats

- Each element is read with what was published by its read date; the French file is restated with each CRSP update.
- The S&P 500 and French's industries are price and total-return series respectively; the replay is on the index's closes.
- Four true bottoms is the register's own n; no element can score better than 4 of 4 there, and a 1974 or 2002 read is often not testable on the held keys.

The episodes are in `false-bottom-audit-2026-episodes.csv`, beside this file.
