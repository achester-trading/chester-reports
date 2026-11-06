# Change order — Signal triage Batch 25 (items 128–132): round 8 continued

| | |
|---|---|
| File | `docs/change-order-signal-triage-batch-25-2026-11-06.md` (drafted as `docs/change-order-signal-triage-batch-17b-2026-11-06.md`; that name is recorded here and not used) |
| Status | **RULED in chat** 6 Nov 2026, 07:58 ET ("Accept"; the order's §8); its decisions O-108a and O-111a ruled and the filing accepted 6 Nov 2026, 08:38 ET, recorded as D62 (`docs/briefs/rulings-2026-11-06.md`). Filed 6 Nov 2026 by paste B129 with filing amendments S1 to S6 (§0). The order as drafted in the triage chat is kept at `docs/pastes/B129-attachment-round-8-continued.md`, people's names replaced as the note under §0 says. |
| Encoding | Batch 25 of Post-Freeze Amendment #4, items 128–132 (S1: the order's chat items 107–111). No register number: every item is recorded against its parent (S3). |
| Precedence | Below Part 26, the Enterprise Layer order and the dated change-orders edition; equal to the other Amendment #4 batches. Amendments govern their parent items from filing. |
| Supersedes | Nothing. |
| Totals | ≈ 14 h of sessions · no by-hand work. The triage chat's estimates. |
| Built by | Nothing yet. 131 and 132's code half in the weekend queue of 7–8 Nov after A126; 128 and 130 with Batch 22's Tranche B; 129 inside item 10's build; Audit #5 confirms (S6). |

---

## 0. Filing amendments S1–S6 (paste B129; ruled 6 Nov 2026, 08:38 ET, D62)

- **S1, encoding.** Batch 25 of Amendment #4, its own file, not a section 4b of Batch 22. The order's chat items 107, 108, 109, 110, 111 are items 128, 129, 130, 131, 132; every "107" to "111" in the body reads so; its references to "item 105", "item 106", "item 98", "item 97", "item 10" and "item 101" are the filed items 123, 124, 116, 97, 10 and 119. Next free triage item after this batch: 133.

- **S2, V-107a resolved at filing.** FINRA margin debt is already stored (`finra.margin_debit`, the existing writer) and read by item 71's fragility panel (`altdata/fragility.py`: level, and share of Z.1 market value). Item 128 is therefore an AMENDMENT to item 71, not a new entry: it adds free credit balances and net margin (debit less free credit), the 3- and 12-month changes, the monthly positioning & flows print, the "deleveraging" flag (two-month decline of 10% or more) and the XX base-rate row through the event-study utility. No new register number; no second margin series.

- **S3, register.** Batch 25 adds no provisional SR row. Every item is recorded against its parent:
  - 128 amends item 71 (fragility panel);
  - 129 amends item 10 (the EM shock screen's spec, before its build; the amendment on `origin/a112-em-shock-screen-amendment` is D2-90's, this one adds the AI-chain sub-panel beside it);
  - 130 is XX base-rate rows (the first-month-drawdown conditional distribution) and a Weekly "AI ring drawdown" table, recorded against the Equities frame (item 31's concentration block) with no number;
  - 131 amends the credit dimension's print (the bifurcation line; it reads A126's honest-span helper, so it is built after Tranche 0);
  - 132 is a narrative-register entry type (dated public call) and an attention input to item 97, recorded against items 97 and 50.

- **S4, decisions.** O-108a and O-111a accepted at their proposed defaults (all four indices down 2% or more in one 24-hour cycle, or any one halted; 10,000 views or 100 reposts at capture, dated claims within 30 days), each reviewed after a quarter and a month respectively.

- **S5, sources.** 129's and 130's index and single-name prices (the SOX, KOSPI, TAIEX, Nikkei; the AI-ring names; Samsung and SK Hynix by local ticker) are read through the price layer the price migration leaves in place, with yfinance's retirement (22 Dec 2026 – 8 Jan 2027) noted: a name with no post-retirement source prints "gap" from that date (16 Oct rule). The Nikkei 225 is already FRED's (item 73).

- **S6, placement.** 131 and 132's code half (the entry type and the Capitulation Count input) in the weekend queue of 7–8 Nov after A126; 132's triage-task half (the X-digest triage prompt's extraction of viral dated calls) is the chat's, not a session's; 128 and 130 with Batch 22's Tranche B; 129 rides item 10's build. Audit #5 confirms.

**Names** (D5, D38, the standing rule: no person's name in committed files). The two X accounts of 129–130 and 132 are "account T" (with its paid community, "The Assembly", and an earlier handle) and "account G"; 131's LinkedIn source is "a LinkedIn commentator", and the strategist who liked the post "a strategist already in the voices register"; the principal quoted in 131 is "SpaceX's chief executive" (Batch 21's N3: principals print as role and institution); Janus Henderson's author is "its credit portfolio manager"; the ruler is "the operator". The one link whose address carries a name stays chat-side. Institutions and companies stay. Everything else is verbatim.

---

The order as drafted follows, its body unedited; §0 governs where they differ.

---

# Change Order — Signal Triage, Round 8 (continued): Items 107–111

**File:** `docs/change-order-signal-triage-batch-17b-2026-11-06.md`
**Status:** RULED 2026-11-06, 07:58 ET ("Accept"). Filing pending.
**Encoding:** Addendum to the round-8 batch. Files beside `change-order-signal-triage-batch-17-2026-11-05.md` (items 92–105) and `change-order-tail-days-item-106-2026-11-06.md` (item 106), or merges into the batch-17 file as §4b at the workplan chat's choice; takes the same batch number.
**Precedence:** Below Architecture Part 26 and the governing text of Amendment #4; equal in rank to the other Amendment #4 batches. Binds Claude Code sessions once filed.
**Prepared:** 6 Nov 2026, from ten screenshots posted at 07:53 (X and LinkedIn), triaged in chat at 07:56.

---

## 1. Summary

Five sources, posted the evening of 5 Nov and the morning of 6 Nov, after the S&P's −4.36% session. Three tell the same story (the AI chain unwinding from Seoul to Santa Clara) three ways; two carry data the stack does not yet hold. One new entry (107), three amendments (108, 109, 110) and one register mechanism (111). Rights stay at report lines, flags, base-rate rows and register entries; no composite weight changes, no regime state or tag (R28).

| Item | What | Type | Rights | Prints in | Hours |
|---|---|---|---|---|---|
| 107 | Margin debt / broker-dealer leverage | New entry + flag + base-rate row | Report line; flag | Positioning & flows (monthly) | ~4h |
| 108 | AI supply-chain transmission panel | Amendment to the EM shock screen (round 4, item 10) | Report line; existing EM-shock flag | Weekly equities | ~4h |
| 109 | Two analog base rates; AI-ring drawdown table | XX rows + Weekly table | Base-rate rows; report line | XX; Weekly | ~3h |
| 110 | HY bifurcation line | Amendment to the credit dimension; seeds item 105 row 6 | Report line | Plumbing & rates | ~1h |
| 111 | Dated public-call entry type | Narrative-register mechanism; attention input | Register rows; input to item 97 | Narratives | ~2h |

Work order: about 14h of sessions; no recurring by-hand step.

Two factual corrections surfaced in the triage and are recorded here so they do not propagate: "HY yields ~16%" (109's source) is false as an index figure — the box's own store had HY OAS at 332bp on 4 Nov; the figure is at best a CCC yield. And the same account gave Korea's drawdown as 44% in one post and 48% in another.

---

## 2. Entries

### 107 — Margin debt / broker-dealer leverage

**Source and incentive tags.** Alpine Macro, LinkedIn: a research shop's marketing post, with a chart of broker-dealer margin loans and receivables against the Nasdaq 100 (2018–2026) and the comment that the 5 Nov selloff "has triggered a wave of margin calls and forced liquidations", plus "rumors of a hedge fund shutting down". Research-shop incentive: sell the subscription; the chart is data, the rumour is not.

**Read.** Margin loans climbed with the Nasdaq 100 to a record (about $750bn on Alpine's series, up from about $600bn in early 2025) and have begun to turn down with the index.

**Thought process.** Leverage behind the tape is the one mechanical seller for which the stack has no proxy at all. The tail-days coverage map (study §4, 5 Nov) lists "positioning extremes — no prime-broker leverage proxy"; item 106b estimates vol-control, CTA and risk-parity flows but not margin. FINRA publishes margin debit balances monthly, keyless, with about a three-week lag; the Federal Reserve's Z.1 broker-dealer series is the quarterly cross-check. Margin-debt peaks sat beside the 2000, 2007 and 2021 tops, and two-month declines of 10% or more have marked the forced-deleveraging phase of every episode since 2000 (memory; the backtest below confirms or corrects it). The level is a condition; the rate of decline is the tell. The closure rumour is attention data, not a fact.

**Ruling (accepted).**
- New register entry unless the round-7 crowding-unwind gauge already carries FINRA margin debt, in which case this becomes an amendment to that gauge (V-107a).
- Series: FINRA debit balances in margin accounts (monthly) and free credit balances; Z.1 broker-dealer margin loans (quarterly) as cross-check. Printed in positioning & flows at the monthly update: level as a share of total market cap (Z.1 or Wilshire), 3-month and 12-month change, and net margin (debit less free credit).
- A "deleveraging" flag on a two-month decline of 10% or more, with a base-rate row in XX built through the round-7 event-study utility (forward 1-, 3- and 6-month index returns and drawdowns after each flag since 1990).
- The hedge-fund-closure rumour goes to the X-digest triage as unverified; no row until a named fund and a primary source exist.

**Rights.** Report line and flag; base-rate row. **Hours.** ~4h.

---

### 108 — AI supply-chain transmission panel

**Source and incentive tags.** An X account ("account T"), its Asia post, and a second X account ("account G"), translated from Chinese. Both are engagement accounts; Account T funnels readers to a paid community ("The Assembly" — the same operation the May 2026 chat looked at under an earlier handle) and disclosed a large short. Figures are repackaged from the wires; cite primary reporting.

**Read.** Korea down 44% (account T's grid) or 48% (account T's Asia post) from its peak, with a circuit-breaker halt; Samsung and SK Hynix more than half of KOSPI; TSMC about 41% of Taiwan; $1.2tn erased across Asia in a day; Taiwan's largest point drop; Japan −7% in a session; memory names (Micron, Samsung, SK Hynix, SanDisk) lost $700bn in two weeks; Goldman prime data cited for hedge funds selling in five days all the AI stock bought since early 2025.

**What checks.** Context from the search: Samsung and SK Hynix together account for more than half of KOSPI's market capitalisation and about 70% of its 2026 gains (Goldman data as cited); 2026 had already produced at least eight KOSPI circuit breakers by late July, including a 10.84% session and the first back-to-back halts on record; Korea introduced 2x single-stock levered ETFs on Samsung and SK Hynix this year. The 6 Nov halt, the 44%/48% figures, Japan's −7% and Taiwan's record point drop are unverified here (V-108a).

**Thought process.** The AI chain is four markets trading as one position — SOX, KOSPI, TAIEX, Nikkei — with Korea the most concentrated and the most levered (retail margin, single-stock levered ETFs, a KOSPI levered-ETF complex that JPMorgan put at $50bn of net assets in June, $26bn by early November, "roughly 75% of the deleveraging complete"). The EM shock screen (round 4, item 10; Batch 5, spec not yet built) catches EM shocks in general; it does not know that these four indices share one driver, nor how concentrated each is. The Equities paper's "semiconductor fulcrum" is the frame; this panel is its daily measurement.

**Ruling (accepted).** Amend item 10's spec before it is built, with an "AI chain" sub-panel:
- the four indices' 1-day and 20-day returns and drawdowns from their 2026 highs (yfinance: ^SOX, ^KS11, ^TWII, ^N225; keyless);
- top-two constituent weights for Korea and Taiwan from the iShares EWY and EWT holdings files (keyless CSV, refreshed with the monthly update; no by-hand step);
- a circuit-breaker and sidecar ledger written by the daily news scan (date, index, trigger level, halt length);
- Korea levered-ETF net assets where a public figure exists (press citations of JPMorgan or Morgan Stanley), else "gap".
Prints in the Weekly's equities section; fires the existing EM-shock flag; the transmission read (US semis → Asia → US futures) is one line in the daily close's "what doesn't fit" when the four move together by more than a set threshold (O-108a).

**Rights.** Report line; the existing EM-shock flag. **Hours.** ~4h.

---

### 109 — Two analog base rates and an AI-ring drawdown table

**Source and incentive tags.** Account G: a "Cisco 2000 vs Nvidia now" analog chart (Nvidia −23% from record, Intel −62%, Oracle −65%, Nasdaq −11%, "Intel + Oracle already ¾ of their 2000–02 decline") and the claim that "the Nasdaq fell 11% in the first month; in 2000 and 2008 it also dropped 10% in the first month, and in both cases the eventual bottom was more than 50% lower." Engagement account; "this account will track… share this with those who put retirement savings into tech stocks."

**Read and checks.** The replay confirms the Nasdaq Composite −11.9% from its 6 Oct closing high at the 5 Nov close. The single-stock drawdowns are claims, not checked (V-109a). "2000 and 2008" is n = 2 with the 2018, 2020, 2022 and 2025 first-month declines left out. "HY yields ~16%, a crisis level seen only twice" is wrong as an index figure: HY OAS was 332bp on 4 Nov in the box's store; the number is at best a CCC yield (CCC OAS 13.45% per 110's source, plus the Treasury yield). "Largest sector rotation into staples since February 2001" has no stated measure; logged.

**Thought process.** The framework's answer to an analog is a base rate with the full sample, and the stack does not yet have the specific one this post invites. Drawdowns by AI ring are already the Equities paper's frame (Mag 7 as one trade, semiconductor fulcrum, AI rings) and item 105's cash-cycle scorecard covers the financing side; a standing drawdown table is the cheap daily companion. The 2000–02 analog belongs in the table as a reference column, labelled as such, never as a path.

**Ruling (accepted).**
- (a) An XX base-rate row: the distribution of eventual drawdown (and time to the low) conditional on a decline of 10% or more in the first 21 sessions off an all-time high — Nasdaq Composite since 1971, S&P 500 since 1950 — computed in the study tool and refreshed by the Annual Structural Review. Printed beside any "2000 and 2008" narrative when the register carries one.
- (b) A Weekly "AI ring drawdown" table: NVDA; the hyperscalers; memory (MU, SNDK, and Samsung and SK Hynix via their local tickers); the listed neoclouds (CRWV, NBIS, IREN); ORCL; SPCX — drawdown from peak, 20-day change, and a 2000–02 analog column (Cisco, Intel, Oracle, Nasdaq) labelled "reference". Source: yfinance, keyless.
- The analog chart and the rotation claim are logged, not entered.

**Rights.** Base-rate rows; report line. **Hours.** ~3h.

---

### 110 — HY bifurcation line

**Source and incentive tags.** A LinkedIn commentator (former lecturer; doom-leaning commentary; liked by a strategist already in the voices register), quoting SpaceX's chief executive's 25 Oct post on X and credit figures from the wires; Janus Henderson, "Looking under the hood: differentiating between CCC high yield bonds", 15 Oct 2026 (asset manager; a long-credit incentive, and the only one of the three with mechanics).

**Read.** The commentator: CCC OAS 13.45%, highest since 2020; distressed exchanges rising; CCC telecom, cable, transport and media widening while retail, utilities, energy and food tightened in October; "everyone is going to be afraid to lend to each other like 1929"; "there aren't enough dollars to service corporate, private and government debt." SpaceX's chief executive (verified, 25 Oct): debt markets have almost entirely shut off money for any company without substantial revenue independent of AI data centers; SpaceX closed $40bn of mostly callable debt for GPUs arriving in 1H 2027 on its investment-grade rating and Starlink and launch revenue; the 200+ neoclouds face "guppy-level death and consolidation"; SpaceX will not buy any. SpaceX's own CDS reached a record 266bp the week before. Janus (15 Oct): CCC spreads at about 1,000bp are wide only in recessions and crises; the CCC/HY ratio at 3.25–3.4x is the widest on record; the widening is concentrated in cable/satellite (CSC Holdings) and wirelines (Altice) — sector-specific secular decline, not cycle stress; about 20% of the CCC index traded below $60 in early October; CCC is 8.6% of the HY index; the performing CCC cohort trades normally.

**Thought process.** The stack already computes CCC OAS and CCC−BB daily (`fred.ccc_oas`, `calc.ccc_bb_oas_bp`, from June 2026) and the credit dimension reads HY level and acceleration. What it does not print is the separation Janus draws: cycle stress (HY and Baa−10y moving) against idiosyncratic distress (CCC moving alone). On 4 Nov the cycle series were quiet (HY OAS 332bp; Baa−10y 152bp, +6bp over 20 observations; October EBP −0.27) while CCC was at a post-2020 high. That combination is the house read and should be visible on one line. The chief executive's post is the first direct observation for item 105's "private-credit window" row and for the Factor I Bull Rebuttal; the commentator's "1929" line is a narrative to carry with its rebuttal, not a signal.

**Ruling (accepted).**
- Amend the credit dimension with one "bifurcation" line in plumbing & rates: the CCC/HY OAS ratio with its percentile under an honest span label (106i.2), CCC−BB 20-day change, and a one-clause composition note (sector concentration, share of the CCC index below $60 when a source prints it). Printed beside HY OAS and Baa−10y so the cycle series and the idiosyncratic series sit on one line.
- The SpaceX chief executive's 25 Oct post seeds item 105 row 6 (private-credit window) and enters the principals feed (item 50); SpaceX CDS joins row 6's tells beside Oracle's spread and CoreWeave's yields.
- Narrative register: "afraid to lend to each other like 1929" as a doom narrative with Janus's rebuttal (sector-specific, performing cohort normal) beside it; the neocloud shakeout as a Factor I thread with SpaceX's chief executive tagged as a competitor (SpaceX rents compute) and a talker-of-book.
- Distressed-exchange and liability-management counts have no keyless source: gap, read from the Fed FSR and the rating agencies' monthly notes on the reading shelf; no by-hand feed.

**Rights.** Report line. **Hours.** ~1h.

---

### 111 — Dated public-call entry type

**Source and incentive tags.** Account T, "The next 15 days, day by day — my stock market prediction", posted the evening of 5 Nov with a 15-cell calendar graphic and "I'm short this market. A lot." Membership funnel plus a disclosed position: talking his book twice over.

**Read.** Day 1 (5 Nov, "happened"): Nasdaq 100 −6.4%, Korea halted, Japan and Taiwan in bear markets. Then: the jobs report (6 Nov), weekend margin calls, futures red Sunday, Asia second wave, CPI Tuesday 10 Nov ("the last one was 3.7%"), "the Fed already raised rates in September" and a Fed president saying more hikes are needed, Nasdaq −20% by day 7, hedge funds' biggest October selloff in ten years, S&P −10%, bitcoin under $70,000, Nvidia reports 17 Nov, Big Tech spending up to $828bn on AI this year with four of the five biggest spenders burning cash, monthly options expiry 20 Nov as the day "correction becomes CRASH", chips −38% from the top, Korea −44%. "When this is over, 2008 and the dot-com crash will look small."

**Thought process.** The calendar is already in "ahead" (jobs, CPI, Nvidia, opex), and item 101 prices the event moves; nothing in the sequence is new information. What is new is the object itself: a dated, falsifiable, viral forecast with a disclosed position, which is attention data with a built-in scorecard. The narrative register grades narratives but has no row type for a dated public call, and the Capitulation Count (round 8, item 97) has no input for the volume of viral crash calls. Factual checks that matter to the stack rather than to the call: "the Fed raised in September" is the Warsh-matrix stance to confirm (V-111a); Nvidia's reporting date (V-111b); "$828bn" against item 105's capex-guidance row (V-111c); the 44%/48% inconsistency (108).

**Ruling (accepted).**
- A "dated public call" entry type in the narrative register: claims with dates, the forecaster's incentive tags (position disclosed, product sold), engagement at capture, and a score at each dated claim's expiry (hit, miss, unresolved). account T's grid is row one, with 20 Nov as its expiry.
- The X-digest triage task (the Claude side, not the Grok automation prompt, which is at its 8,000-character limit) extracts viral dated calls above an engagement threshold (O-111a) from the existing digests and writes the rows.
- A "viral crash-call count" (rows captured per day, both directions) as an input to the Capitulation Count if it is not already there (V-111d); a mirror "viral melt-up-call count" so the input is two-sided.

**Rights.** Register rows; attention input. No forecast right, no scenario or theme change. **Hours.** ~2h.

---

## 3. Cross-item notes

- **107 and 106b.** Margin debt is the slow, monthly leverage read; 106b's vol-control, CTA and risk-parity estimates are the daily ones. Both print in positioning & flows; the flag in 107 and the forced-flow line in 106b should share one "deleveraging" vocabulary.
- **108 and item 10.** 108 amends item 10's spec; Audit #5 places item 10's build with the amendment in it, so 108 adds no separate tranche.
- **108 and item 98.** Korea's single-stock levered ETFs and the KOSPI levered-ETF complex are the same mechanism as item 98's US roster; 98's roster stays US-only, and 108 carries the Korean figure as a context line.
- **109 and 105.** The AI-ring drawdown table is the price side of 105's cash-cycle scorecard; the two print adjacent in the Weekly's equities section when 105 lands.
- **110, 105 and 106d.** 110's bifurcation line is the daily read; 105 row 6 is the quarterly one; 106d's policy-put triggers use the cycle series (HY, Baa−10y), not CCC, so an idiosyncratic CCC move cannot fire them. That separation is deliberate.
- **111 and item 97.** The crash-call count feeds the Capitulation Count as an attention input; it carries no direction.
- **111 and item 101.** When a dated call names a scheduled event, 101's ledger row for that event links to the call, so the scorecard and the event-vol ledger reconcile at expiry.

---

## 4. Verify items

| ID | Check | Due |
|---|---|---|
| V-107a | Whether the crowding-unwind gauge (round 7) already carries FINRA margin debt; the definition of Alpine's "margin loans & receivables" series against FINRA's debit balances | At filing |
| V-107b | FINRA margin statistics are reachable keyless from the box (the monthly page or its CSV) | At build |
| V-108a | The 6 Nov KOSPI halt (trigger level, halt length); Korea's drawdown from its 2026 high (44% vs 48%); Japan −7% and Taiwan's record point drop; current Korea levered-ETF net assets | Sunday 8 Nov Weekly |
| V-108b | EWY and EWT holdings CSVs download keyless and carry weights | At build |
| V-109a | NVDA, INTC, ORCL, SPCX drawdowns from peak on 5 Nov (the chart's −23%, −62%, −65%, −40%) | At build |
| V-110a | CCC OAS 13.45% on the box's `fred.ccc_oas` and the CCC/HY ratio; the share of CCC below $60 if any public source updates it | Daily close, 6 Nov |
| V-110b | SpaceX CDS level (the 266bp record was the week of 19 Oct) | At 105 build |
| V-111a | Fed stance: whether a September 2026 hike is in the Warsh scenario matrix as recorded | At filing |
| V-111b | Nvidia's Q3 FY27 reporting date (the post says 17 Nov) | At filing |
| V-111c | "$828bn" Big Tech AI capex for 2026 against item 105's capex-guidance row | At 105 build |
| V-111d | Whether the Capitulation Count (item 97) already carries a social-attention input | At filing |

---

## 5. Work order and placement

| Work | Item | Sessions | By hand |
|---|---|---|---|
| 107.1 FINRA and Z.1 series into the store; positioning line; deleveraging flag; XX base-rate row | 107 | ~4h | — |
| 108.1 AI-chain sub-panel added to item 10's spec; built with item 10 | 108 | ~4h (inside item 10's build) | — |
| 109.1 XX first-month-drawdown row (study tool); Weekly AI-ring table | 109 | ~3h | — |
| 110.1 Bifurcation line in the credit dimension; 105 row-6 seed; register entries | 110 | ~1h | — |
| 111.1 Dated-call entry type; X-digest triage extraction; Capitulation Count input | 111 | ~2h | — |
| **Total** | | **~14h** | **none** |

Placement: 110 and 111 with batch-17 Tranche A (cheap, and the credit read is wanted now); 107 and 109 with Tranche B (Monthly-facing); 108 rides item 10. Audit #5 (week of 23 Nov) confirms.

---

## 6. Decisions at filing

- **O-108a, the transmission threshold.** Proposed default: all four indices down 2% or more in the same 24-hour cycle (Asia session plus the prior US close), or any one of them halted. Review after one quarter.
- **O-111a, the engagement threshold for capture.** Proposed default: 10,000 views or 100 reposts at the time the digest captures it, dated claims within 30 days. Review after one month of rows.

---

## 7. Register, voices and sources

**Voices for the Phase B register.** Alpine Macro (research shop; already a voice from batch 1). Janus Henderson, its credit portfolio manager (asset manager, long-credit incentive; new voice, credit mechanics). SpaceX's chief executive (principal; competitor to the neoclouds via SpaceX's compute business; talks his book — captured through item 50's principals feed, not as a voice).
**Logged, not voices.** Account T / The Assembly (membership funnel, disclosed short); account G (engagement account); the LinkedIn commentator (LinkedIn commentary); the strategist's like (already a voice; a like is not a view).
**Narrative register.** "Lend to each other like 1929" (doom; rebuttal: Janus, sector-specific CCC distress, cycle series quiet). "Cisco 2000 = Nvidia 2026" (analog; rebuttal: the XX first-month-drawdown row). account T's 15-day call (dated public call, row one of the new type; expiry 20 Nov).

**Sources.**
- Janus Henderson, "Looking under the hood: differentiating between CCC high yield bonds", 15 Oct 2026: https://www.janushenderson.com/en-ch/investor/article/looking-under-the-hood-differentiating-between-ccc-high-yield-bonds/
- The SpaceX chief executive's 25 Oct post, as reported: a trading-news report (link kept chat-side, names §0); https://www.taipeitimes.com/News/biz/archives/2026/10/27/2003866661 ; SpaceX CDS record: https://www.communicationstoday.co.in/?p=426593
- KOSPI concentration and circuit breakers in 2026: https://www.kucoin.com/news/flash/kospi-plummets-8-37-at-open-triggering-circuit-breaker-as-samsung-and-sk-hynix-drive-sell-off ; https://askfuzz.ai/discover/news/global/china-markets-rise-on-ai-optimism-tech-stocks-surge ; https://www.indmoney.com/blog/us-stocks/kospi-crash-skhynix-skhy-samsung-stock-analysis
- KOSPI levered-ETF unwind (JPMorgan, Morgan Stanley), from the 5 Nov triage: https://finance.biggo.com/news/691aa43a-d37a-4512-8f61-f0d4438eda4f
- Box data cited: `fred.hy_oas` 332bp on 4 Nov 2026 and Baa−10y 152bp (tail-days replay, `docs/studies/tail-days-2016-2026-data.md`).
- Screenshots in chat (6 Nov, 07:53): Alpine Macro margin-loans chart; account T's 15-day grid and Asia post; account G's thread and Cisco/Nvidia chart; the LinkedIn commentator's post with the embedded "Today's Markets" panel (DJIA −2.62% at 51,956).

---

## 8. Sign-off

The rulings given in chat constitute the signature: items 107–111 as proposed, "Accept", 6 Nov 2026, 07:58 ET. O-108a and O-111a carry their proposed defaults unless the operator says otherwise at filing.

Filed: [commit hash] on [date].