# Change order — Signal triage Batch 12 (items 59–60): bank stress and the earnings-estimate overshoot

| | |
|---|---|
| File | `docs/change-order-signal-triage-batch-12-2026-10-20.md` |
| Status | **RULED 20 Oct 2026 in chat** (items "Yes", "Yes"). Filed 20 Oct 2026 with filing amendments F1 to F6 (§0), ruled 20 Oct 2026 ("accept all"). |
| Encoding | Batch 12 of Post-Freeze Amendment #4. It was written as "round 6, Part 5, items 53–54, Batch 11", but Batch 11 and items 53–58 were already used by the order of 19 Oct (`change-order-signal-triage-batch-11-2026-10-19.md`). Batch 10 was never used. Items 53 and 54 are therefore filed as **59** and **60**; their work IDs keep the round-6 prefix (ST-R6.59a–d, ST-R6.60a–c). |
| Precedence | Below Part 26 and the 25 Sep integrated signal-triage order. It follows that order's integration rules: R28 sub-states, one system of record, T&B overlay intake one at a time, Track D preconditions, and validation gates as offline calibration studies with dated ledgers. |
| Built by | Session A (paste A53), after A52, on `a52-doctrine-2-pack`. The 1 Nov Monthly candidates are item 59's classifier and item 60's implied-growth print, so the build must merge before the Monthly's last dry run on 28 Oct. |

---

## 0. Filing amendments (ruled 20 Oct 2026, "accept all")

- **F1, the numbering.** Batch 12; items 59 and 60; work IDs ST-R6.59a–d and ST-R6.60a–c. Every "53" and "54" below reads as 59 and 60.
- **F2, no by-hand lines.** The 16 Oct standing rule on sources says friction means a keyless alternative or a listed gap. The S&P DJI by-hand workbook was withdrawn on 17 Oct under it. So this order adds no recurring by-hand line, and each of the following is a **listed gap**:
  - bank CDS and AT1 spreads;
  - CMBS office delinquency;
  - FHLB advances between quarters from press reports;
  - the neocloud credit line.

  Two consequences:
  - The classifier's third arm ("either flag plus a CDS/AT1 move") prints "not tracked".
  - FHLB advances come from the Fed's Financial Accounts (Z.1, quarterly, through the existing FRED writer), in place of the Office of Finance plus press reports.

  The SR-16 neocloud line is listed as a gap, beside the hyperscaler credit anchors.
- **F3, item 60's forward-EPS legs.** The S&P DJI estimates file was withdrawn on 17 Oct (`spdji` retired: "not tracked (source withdrawn)"), so implied forward growth and the realised forecast error have no stored source.
  - The session first probes Yardeni's public series, reading its terms and robots.txt first.
  - If it can be read keylessly and simply, both series, the flag and the ledger are built from it, labelled with the source.
  - If not, both series are listed gaps, the flag does not print, and the base-rate ledger waits for a source.

  The P/E dispersion line and the narrative pair are built either way.
- **F4, the dispersion line's peak.** The forward-P/E log (the consensus logger) starts in 2026, and no keyless source serves earlier forward P/E. The line therefore prints each name's forward P/E against its peak since logging began, labelled with that date. Beside it goes each name's **trailing** P/E against its 2025 peak, where stored prices and reported EPS allow, labelled "trailing".
- **F5, the 12:30 alert.** The bank-stress gate opens only on the session a flag turns on, not on every session it stays on. The slot sends at most one message a session.
- **F6, the source checks (§5).** The session runs each check before building, and records the result in its notes. Anything that fails the standing rule on sources becomes a listed gap.

---

## 1. Purpose and scope

Two items were ruled on 20 Oct 2026. Item 59 adds a bank-stress panel and a classifier that tells a sector correction from a banking crisis; it comes from an operator question prompted by a short X post. Item 60 amends items 29 and 40 with implied forward growth and a realised forecast-error series, and adds a neocloud credit watch line to SR-16 (a listed gap under F2). Nothing here changes the frozen architecture, and no composite weights change.

## 2. Entries

### 59 · Bank-stress panel and correction-vs-crisis classifier (ThenPath post; operator design question) — BRIEF

**Source.** @ThenPathMarkets on X, 19 Oct 2026: "Bank stocks falling is one thing. A banking crisis is another. The real signals to watch are deposit outflows, credit deterioration, and funding stress." The operator then asked what other ways there are to measure bank stress. Tag: commentator.

**Thought process.** Equity drawdowns are the loudest bank-stress signal, but neither the earliest nor the decisive one. A useful panel separates the signals by how fast they move and what they measure:
- **Market-based (daily, earliest):** CDS, bank bond spreads including AT1s, regional against money-centre equity, and bank equity implied vol.
- **Funding:** SOFR–IORB and SOFR's 99th percentile, financial CP over bills, FRA–OIS, FHLB advances (the quiet first stop in 2023), the discount window and emergency facilities on H.4.1, standing repo take-up, and the cross-currency basis.
- **Deposits (weekly):** H.8 deposits at large against small banks, money-market fund assets as the other side of a flight, and the uninsured share and deposit beta from call reports.
- **Credit and balance sheet:** SLOOS, charge-offs and delinquencies (CRE and cards first), unrealised AFS/HTM losses (the 2023 mechanism, live at a 5.3% 10-year), CMBS office delinquency, and bank lending to non-banks.
- **Composites:** STLFSI, the KC Fed FSI, the NFCI sub-indices and the OFR FSI.

The question that matters is ThenPath's: is this a sector correction or a banking crisis? If equity falls while funding and deposits stay calm, it is a correction, usually a rates or earnings story. If equity falls alongside funding and deposit stress, it is a banking problem, and the 2023 and 2008 base rates apply. This has the same shape as item 28's idiosyncratic-vs-systemic classifier.

**Stack today.**
- NFCI is in from item 34.
- HY and quality-tail spreads are in from item 41.
- SLOOS is a list item on the reading shelf.
- XI Credit carries the bifurcation thread.
- There is no bank-specific funding, deposit or balance-sheet panel, and no classifier.

**Ruling** (as amended at filing).
1. **A bank-stress panel** of about ten free series, each with dual percentiles (five years, plus a long window per family):
   - SOFR–IORB and SOFR's 99th percentile (NY Fed);
   - financial CP minus the 3-month bill (FRED);
   - discount-window primary credit and any emergency facility (H.4.1, weekly);
   - FHLB advances (the Fed's Z.1, quarterly, through FRED; F2);
   - H.8 deposits at large against small domestic banks (weekly);
   - ICI money-market fund assets (weekly);
   - KRE against XLF relative performance, plus KRE implied vol where free;
   - SLOOS net tightening, promoted from a reading-shelf list item to a series;
   - unrealised securities losses (FDIC Quarterly Banking Profile), if keyless (F6);
   - STLFSI and the OFR FSI as composites.

   Bank CDS, AT1 spreads and CMBS office delinquency are listed gaps (F2).
2. **The funding-stress flag:** any two of SOFR–IORB, the financial CP spread, discount-window use and FHLB advances above their 95th percentile.
3. **The deposit-flight flag:** small-bank H.8 deposits falling while money-market fund assets rise, both over 4 weeks.
4. **The correction-vs-crisis classifier,** printed whenever bank equity (KRE or BKX) is down more than 10% over 20 sessions:
   - *correction:* neither flag on;
   - *funding watch:* one flag on;
   - *banking stress:* both flags on. The CDS/AT1 arm prints "not tracked" (F2).
5. **A base-rate ledger** covering 2007–08, March 2023, and the bank-equity drawdowns that stayed corrections: the path of each panel series, and the forward 3- and 12-month SPX and HY outcomes.
6. **A T&B overlay intake-queue entry** (the Liquidity & Funding Stress family), after the ledger is written, one at a time, as ruled.

**Rights.** Flags and the classifier only. T&B rights come only through the queue, after the ledger.

**Placement.**
- Plumbing & rates: a new bank-stress block beside the item-34 rates-transmission cluster.
- The read: the classifier also prints there.
- The Weekly carries a one-line panel status, and the Monthly the full panel.
- The 12:30 alert's gate is extended, opening on the session either flag turns on (F5).

**Work.**

| Task | Description | Hours |
|---|---|---|
| ST-R6.59a | Panel ingestion: FRED (including Z.1 and H.8), the NY Fed, H.4.1, ICI | 3 |
| ST-R6.59b | Flags and classifier | 2 |
| ST-R6.59c | Base-rate ledger | 2.5 |
| ST-R6.59d | Queue entry (after the ledger and "T&B full") | 0.5 |

### 60 · Earnings estimates overshoot before every crash (Dan Runkevicius; Yardeni chart) — AMENDMENT to items 29 and 40; AMENDMENT to SR-16

**Source.** Runkevicius on LinkedIn, about 16 Oct 2026, with a Yardeni Research chart from LSEG I/B/E/S data. Tag: commentator, already in the voices register.

**Read.**
- The chart plots S&P 500 forward operating EPS pushed 52 weeks ahead against actual trailing four-quarter EPS.
- Analysts overshot actuals into 2001, 2008 and 2020, and the bigger the crash, the bigger the overshoot. The steepening line now reads either as a growth cycle or as a reckoning.
- On AI, Runkevicius notes that hyperscaler forward P/Es are 15–65% below their 2025 peaks, and that Nvidia trades at about half its 2025 multiple.
- He adds that CoreWeave is being repriced toward junk, and that companies are guiding to ROI on capex.

**Thought process.** "Not a single one" means three episodes chosen with hindsight. The gap on the chart today is not itself an error: forward EPS normally sits above trailing EPS in an expansion, and the chart's gap is about 28% implied growth over roughly fifteen months. Two measures turn the chart into signals:
- **Implied forward growth:** forward EPS (pushed ahead) divided by trailing actual EPS, minus 1, ranked against its own history. About 28% is high for a mature expansion; levels like this have normally come out of recessions (2010, 2021), not late in a cycle.
- **Realised forecast error:** forward EPS one year earlier against actual EPS now. When it turns negative, the reckoning is showing up in the data rather than being forecast.

This closes the loop on four earlier items: the revisions turn (29) leads, the forecast error confirms, the price–ULC gap (35) is the mechanism, and the decomposition chart (40) shows how it plays out in price. Hyperscaler multiple compression is item 33's "cyclical at peak margins" point now appearing in the data. CoreWeave trading toward junk is the first credit-market sign of capex-cycle stress, and belongs with SR-16's hyperscaler and AI-credit absorption entry.

**Stack today.**
- Item 29 has r−g and the revisions-turn flag.
- Item 40 has the standing decomposition chart; its forward leg was withdrawn on 17 Oct with the S&P DJI source.
- Item 33 has the AI Big 10 normalized-margin multiple.
- SR-16 has hyperscaler debt issuance and credit anchors.
- There is no implied-growth percentile, no realised-error series, and no neocloud credit line.

**Ruling** (as amended at filing).
1. **Implied forward growth,** added to item 29's r−g print with dual percentiles, from a keyless forward-EPS source if F3's probe finds one; otherwise a listed gap.
2. **The realised forecast-error series,** quarterly, from the same source, with a base-rate ledger of errors around the 2000, 2007 and 2019 peaks (F3).
3. **The flag:** the realised error turning negative while item 29's revisions-turn flag is also on (F3).
4. **The hyperscaler forward-P/E dispersion line,** added to item 40's Monthly chart: each name's multiple against its peak, as F4 sets it.
5. **The SR-16 amendment:** a neocloud/AI-infrastructure credit watch line (CoreWeave bonds and peers), a listed gap under F2, beside the hyperscaler credit anchors.
6. **A narrative-register pair,** seeded through the register's existing proposal path for the operator's confirm or reject:
   - "AI excess flushed in an orderly way", Runkevicius's bull reading;
   - "estimates overshoot into a reckoning", the chart's bear reading.

   The forecast-error series adjudicates between them once it exists.

**Rights.** Flag only. The SR-16 line is report-only.

**Placement.** What's priced (items 29 and 40); positioning & flows and credit (SR-16); narratives.

**Work.**

| Task | Description | Hours |
|---|---|---|
| ST-R6.60a | Implied growth and the forecast-error series (F3) | 1.5 |
| ST-R6.60b | Flag and ledger | 1 |
| ST-R6.60c | P/E dispersion line on item 40 (F4) | 0.5 |

## 3. Cross-item notes

- Item 59's unrealised-securities-loss line ties to `rates.driver`: the higher the long end, the larger the losses. The Monthly prints them together.
- Item 60 links items 29, 33, 35 and 40 into one earnings chain: revisions lead, the forecast error confirms, the price–ULC gap is the mechanism, and the decomposition chart shows the outcome in price.
- Both items feed the top side of T&B only through ledgers, and each enters the intake queue one at a time, behind items 19, 30, 31 and 44.

## 4. Work order

- **Now:** ST-R6.59a, 59b, 60a, 60b and 60c, about 8 hours of the order's estimate. Session A builds them in paste A53 in about 2 hours.
- **Ledgers:** ST-R6.59c, 2.5 hours.
- **After the ledger and "T&B full":** ST-R6.59d, 0.5 hours.
- **By hand:** none (F2).

## 5. Verify items (F6: before building)

1. Free history depth for the SOFR percentiles, financial CP and H.8 small-bank deposits.
2. Z.1's FHLB advances series on FRED, and its lag.
3. A keyless forward-EPS series with vintages (Yardeni's public series, its terms and robots.txt), or a listed gap (F3).
4. The FDIC Quarterly Banking Profile's unrealised losses as a keyless series, or a listed gap.
5. KRE's implied vol from a free chain, or a listed gap.

## 6. Register, voices and sources

**Register:**
- Items 59–60 carry round numbers; SR numbers are assigned at the next Doctrine sitting.
- Item 60 is recorded as an amendment to items 29 and 40 and to SR-16.
- SLOOS is promoted from a reading-shelf list item to a series.

**Voices:** ThenPath (commentator, new). Runkevicius is already in the register. Yardeni Research is the chart's source.

**New sources, each subject to F6:**
- the NY Fed's SOFR distribution;
- FRED: financial CP, Z.1's FHLB advances, H.8, STLFSI and SLOOS;
- the Fed's H.4.1 (the existing writer);
- ICI money-market fund assets;
- the FDIC Quarterly Banking Profile;
- the OFR FSI;
- Yardeni's public earnings series (F3).

## 7. Decisions and sign-off

- 59 (filed from round-6 item 53): ruled 20 Oct 2026 ("Yes").
- 60 (filed from round-6 item 54): ruled 20 Oct 2026 ("Yes").
- Filing amendments F1 to F6: ruled 20 Oct 2026 ("accept all").

Signed: A. Chester, 20 Oct 2026 (chat rulings as recorded above).
