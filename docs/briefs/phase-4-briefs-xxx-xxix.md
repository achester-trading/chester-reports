# Commissioning briefs — Phase 4 papers (XXX, XXIX) and the XXXII check

These briefs are the handoff from Audit 2 (`docs/white-paper-library-audit-2.md`) to the writing sessions for two Markets-shelf papers of its Phase 4: XXX Market Structure and Cascades and XXIX Real Assets and Risk Transfer. They also record the check on XXXII, the Annual Structural Review, and add its brief because the paper is absent. Each paper's writing session reads the audit's Parts 0, 1 and 4 and the relevant roster row, then this brief, then the papers under "must cite". The **emphasis decisions** below are proposals; the operator rules them before writing begins, as for Phase 2.

Written 25 Oct 2026 by session B (B66) on branch `b66-phase-4-briefs` from `origin/b65-learning-loop-v2` (`a4e3b2e`). Docs only. No paper is written here.

## House standards (apply to all three)

The Phase 2 brief's house standards apply unchanged (`docs/briefs/phase-2-briefs-xxv-xxvii.md`, "House standards"):
- the shelf and voice;
- the presentation standard of 7 Sep 2026: confidence carried as an italic closing clause, prose before tables, conceptual figures labelled;
- cross-references by short name, never numeral;
- the required closing chapters (Tactical Applications at seven horizons with the nine fields, Wiring, Environments, the Assumptions & Falsifiers appendix);
- the prerequisites note;
- one worked example, one historical instance and one "on the day" per mechanism;
- the masthead format;
- validation before delivery.

Three additions for Phase 4:
- **Describe what is measured as measured.** Where the register or a ledger already measures a mechanism, the paper describes the measure by its item number and states the ledger's verdict as filed. It never re-derives a figure the store holds, and it never upgrades a ledger's FAIL or INSUFFICIENT into a finding.
- **No Brookfield-group instrument**, anywhere, as an example, a case or a figure (Standing rule 1). This binds XXIX's infrastructure, real-estate and insurance chapters hardest, because the group is large in all three. A chapter that needs a listed example uses an index, an ETF or a named episode instead.
- **XXVII is not yet on main.** Debt Cycles, Regimes, and Environments is Draft 1 on branch `library-xxvii`. Both papers cite it by short name ("Debt Cycles") and by chapter title, never by chapter number, until it merges.

---

## XXX — Market Structure and Cascades

**Slug:** `market-structure-and-cascades` · **Numeral:** XXX · **Shelf:** Markets · **Target:** ~15,000 words · **Reading-plan position:** 8 (with Positioning and Flows, Events and Expectations and Technical Indicators; after the options sequence of position 7) · **Version:** 1.0

**Purpose.** Layer 3.1 and 3.5 of the audit's curriculum as one subject. Its probes found them "fragmented" and "barely named":
- microstructure: "ETF creation/redemption, clearing/collateral, HFT/automated liquidity thin";
- cascades: "correlation breakdown 4, path dependence 1, endogenous risk 5" hits across the corpus.

It explains how a trade becomes a price, who stands in the middle and why they step away, and how leverage, margin and mechanical flows turn a price move into a regime. It absorbs the market content of the Systematic Book's Part III (decision 2), which then references it.

**Organizing claim.** Liquidity is not a stock that markets hold but a flow that intermediaries supply when it pays and withdraw when it does not. A cascade is what happens when the flow that must trade (margin calls, rebalancing, hedging, redemptions) exceeds the flow that is willing to. The size of a move is therefore set less by the news than by the ratio of forced flow to depth, and that ratio is measurable before the move.

**Parts and chapters.**

*Part I — How a trade becomes a price.*
1. **Venues and auctions:** the continuous book, the opening and closing auctions, dark venues; why the close is the day's largest trade. Non-US structure in brief: Europe's fragmentation, Asia's sessions (decision 5).
2. **Who supplies liquidity:** bank dealers, non-bank market makers, automated liquidity; what each is paid for and what makes each stop. Price, Time, and Edge's participant ecology is cited, not restated.
3. **ETFs:** creation and redemption, authorised participants, the premium and discount; what an ETF does to its underlying in calm and in stress.
4. **Settlement, clearing, collateral and margin:** the clearing house as the shock absorber that charges for it; procyclical margin; who must post, and when.
5. **Depth and impact:** price impact per unit of flow (Kyle's lambda, Amihud's measure); why volume and depth diverge.

*Part II — Cascades as one subject.*
6. **Endogenous risk and feedback loops:** a price move that changes the participants' constraints and so produces the next move.
7. **Forced flows:**
   - margin;
   - volatility targeting (cite Volatility);
   - leveraged-ETF close rebalancing;
   - dealer gamma (cite the Dealer's Hand, Part I; no fourth options 101);
   - redemptions.
8. **Liquidity spirals:** funding liquidity and market liquidity reinforcing each other (Brunnermeier and Pedersen).
9. **Correlation breakdown and path dependence:** why diversification fails exactly when it is needed; why the order of moves matters.
10. **Short squeezes:** crowded shorts, borrow and recall, the forced buyer.

*Part III — The cases* (weighting per decision 1).
11. **1987:** portfolio insurance as a forced seller into futures. The episode is Tops and Bottoms'; the mechanism is this paper's.
12. **1998:** LTCM; leverage, crowded relative value and the dealers' own books.
13. **2010:** the flash crash; automated liquidity withdrawing within minutes.
14. **February 2018:** the short-volatility products and the vol-control sellers.
15. **March 2020:** the dash for cash; Treasuries and bond ETFs under stress (cite The Rate and Liquidity Machine for the Treasury market).
16. **2021, GameStop:** the forced buyer, and clearing deposits as the constraint that stopped buying.
17. **2022, the gilts:** the LDI collateral spiral. The fiscal side is Debt Cycles'; the collateral mechanics are this paper's.

*Part IV — The fragility read, as measured* (decision 3).
18. **Forced flow against depth:** the fragility panel and the squeeze line as the system measures them, with each ledger's verdict as filed.
19. **What the measures cannot see:** top-of-book depth is a listed gap, and the stand-in is a stand-in.

*Part V — Closing.*
20. Tactical Applications.
21. Wiring.
22. Environments.
- Appendix A: Assumptions & Falsifiers.
- Appendix B: dated material.

**Worked examples (one per mechanism).**

| Mechanism | Worked example (numbers) | Historical instance | On the day |
|---|---|---|---|
| The closing auction | an imbalance against the auction's size, and the price concession it buys | an index rebalance close | the imbalance publications into the close |
| ETF arbitrage | a bond ETF's discount against its NAV when the underlying does not trade | March 2020 | the discount opening while the bonds were not quoted |
| Margin procyclicality | a margin rate stepped up on a volatility rise, and the cash call it makes | 2021 clearing deposits; 2022 gilt collateral calls | the broker restrictions; the central bank's intervention |
| Leveraged-ETF rebalancing | AUM × L × (L − 1) × the day's return, the formula item 71 uses | February 2018 | the close's one-sided flow |
| Vol targeting | exposure cut in proportion to realised volatility | February 2018 (cite Volatility) | the second day's selling |
| Liquidity spiral | a margin call forcing a sale that widens the next margin | 1998 | the dealers' own positions |
| Automated withdrawal | depth falling to a fraction within minutes | 6 May 2010 | the stub quotes |
| The squeeze | short interest against float, borrow cost, the recall | January 2021 | the cost of borrow and the halts |
| Correlation breakdown | a stock–bond correlation flip and what it does to a 60/40 | 2022 (cite Debt Cycles' environments) | the joint drawdown |

Every number in a worked example is illustrative and labelled so, or cites its source and as-of date (the gate's rule).

**Must cite (by short name):**
- Price, Time, and Edge: participants, the horizon ladder, the six questions;
- the Dealer's Hand: Part I, the single options-mechanics 101; and dealer gamma;
- Volatility: vol targeting, the VRP's unwinds, February 2018;
- the Systematic Book: Part III, for the broker and execution mechanics that stay there;
- Options as Expression;
- Positioning and Flows: the mechanical holders' calendar, without duplicating its map;
- Tops and Bottoms: 1987, 1998, 2018, 2020 as episodes;
- The Rate and Liquidity Machine: the 2019 repo and March 2020 Treasury market;
- Debt Cycles: the gilts' fiscal side, and the environments;
- the Twenty-Five: the tail families a cascade sits in.

**Must not:**
- teach options mechanics again;
- re-narrate an episode Tops and Bottoms already tells (cite it, and give the mechanism);
- tell the gilts as a fiscal story;
- carry any level, share or probability in the timeless body;
- name a vendor's proprietary depth figure as a measured series;
- use any Brookfield-group instrument.

**What the register and the ledgers already measure (describe, do not re-derive).**

A note on numbering first. The paste names "items 64, 67, 71 and 74". Under the filing tables, two of those numbers are the same items written another way:
- Batch 14's F1 files the order's 64 (top-of-book depth) as **item 71**;
- Batch 15 files the order's 67 (the squeeze) as **item 74** (the pre-registration's "item 74 (written as 67)").

Filed items 64 (the real 10-year against the cyclically adjusted earnings yield) and 67 (PEG and LTEG) are not market structure. So the fragility chain is two filed items with their ledgers:

| Item | What is measured | Where | Ledger and verdict as filed |
|---|---|---|---|
| 71 (written 64) | the liquidity-fragility panel: SPY's Amihud measure as the depth stand-in (top-of-book depth is a listed gap), FINRA margin debt, the leveraged-ETF rebalance estimate, dealer gamma; the fragility flag; the tenth "liquidity" lens in item 52 | `altdata/fragility.py`; Mechanics | ST-R6.71d, the air pockets of February 2018, August 2024 and April 2025 (`docs/ledgers/air-pocket-preregistration-2026-10.md`): **FAIL** (ruling D9, 24 Oct) |
| 74 (written 67) | the hedge-fund positioning line: CFTC TFF leveraged-fund nets in ES and NQ, FINRA short interest; the squeeze-risk flag | `altdata/hf_positioning.py`; Positioning & flows | ST-R6.74b, extreme net shorts and the 20-session outcome (`docs/ledgers/short-extremes-preregistration-2026-10.md`): **INSUFFICIENT, n 0** (D9) |
| 45 | the three-timeframe ES read, its levels and lean, scored daily | `altdata/es_block.py` | the `es_ledger` table |
| 52 | the volatility-event flag and its lenses | `altdata/vol_event.py` | `vol.event_ledger`; no modifier right before 30 events |
| 61 (OS-12) | relative options volume, "volume, no side" | `daily_cascade/relative_volume.py` | OS-12c pre-registered |
| the dealer items (6b) | the exposure captures, the regime word at net-to-gross ≥ 0.10, the scorecard | `altdata/dealer_store.py`, `altdata/dealer_scorecard.py` | the dealer scorecard's pre-registration; "insufficient sessions" below 20 |

**Figures (with the store keys each draws from).**

| # | Figure | Keys |
|---|---|---|
| 1 | Forced flow against depth: the leveraged-ETF rebalance estimate and SPY's Amihud stand-in, the three air pockets marked | `levetf.aum`, `yfinance.mkt_spy` (the estimate and the measure are computed by `altdata/fragility.py`, not stored as keys) |
| 2 | Margin debt through the cases | `finra.margin_debit` |
| 3 | Leveraged funds' net in ES against the squeeze cases | `cftc.tff_lev_money_net_oi` |
| 4 | Dealer gamma and the session's range | `exposure.net_gex`, `yfinance.mkt_spy` |
| 5 | The volatility index through the seven cases | `fred.vix` |
| 6 | The stock–bond correlation's sign through regimes | `calc.corr_spy_tlt_60d` |
| 7 | The cascade as a loop: a conceptual diagram, no series | — |

**EMPHASIS DECISIONS for Ari (XXX).**

1. **The cases: equal weight, or weighted to what the ledgers measure.**
   - Options: (a) all seven at equal length; (b) full chapters for the cases the store and the ledgers can measure, and short mechanism chapters for the rest; (c) (b), plus August 2024 and April 2025 as short instances, because the air-pocket ledger already scores them.
   - **Recommend (c).** A paper that teaches "measurable before the move" should spend its length where the system's own measures can be shown. Those cases are February 2018 and March 2020 in full (leveraged-ETF AUM, margin debt, CFTC and the VIX reach them), and 2021 and 2022 at medium length. The pre-store cases (1987, 1998, 2010) stay as mechanism chapters, cited to their published histories. The two recent air pockets cost a page each, and they keep the paper honest about a FAIL verdict.
2. **How much of the Systematic Book's Part III moves.**
   - Options: (a) only 3.5, "Microstructure the book actually uses"; (b) all of Part III; (c) none, cited.
   - **Recommend (a).** Part III's other sections (3.1–3.4, 3.6) are the broker connection, Portfolio Truth, brackets, the session rule and the opportunistic book's execution rules. Those are System content about this operator's machine, and they belong where they are. Only 3.5 is market content. It moves, and the Systematic Book keeps a one-line reference.
3. **Whether the fragility chain gets its own Part.**
   - Options: (a) its own Part IV, two chapters; (b) a section inside chapter 7; (c) Appendix B only.
   - **Recommend (a).** Items 71 and 74 are the system's only direct measures of the paper's organising claim, and their verdicts (FAIL, and INSUFFICIENT at n 0) are exactly what a reader should see stated plainly beside the mechanism. As a section it would read as a footnote. In the appendix it would be dated material, which a verdict is not.
4. **Clearing, collateral and margin: a chapter or a section.**
   - Options: (a) a full chapter (chapter 4); (b) a section of chapter 7.
   - **Recommend (a).** Two of the seven cases (2021 and 2022) turn on a margin call rather than on a price. The audit's probe found clearing and collateral "thin" across the whole corpus.
5. **Non-US market structure.**
   - Options: (a) a section in chapter 1 (fragmentation, sessions); (b) a chapter; (c) out of scope.
   - **Recommend (a).** The audit lists non-US structure as a missing perspective, but the book trades US instruments. A section names what differs without a chapter of detail the book will not use.
6. **0DTE and the intraday dealer flow.**
   - Options: (a) cited to the Dealer's Hand, with one paragraph in chapter 7; (b) a chapter here.
   - **Recommend (a).** The Dealer's Hand and Volatility already carry it at depth. A chapter here would be the fourth treatment the audit warned against.

---

## XXIX — Real Assets and Risk Transfer

**Slug:** `real-assets-and-risk-transfer` · **Numeral:** XXIX · **Shelf:** Markets · **Target:** ~12,000 words · **Reading-plan position:** 6, as a reference paper beside Credit, Equities and Volatility (the audit's core track does not list it; decision 6 asks whether it joins) · **Version:** 1.0

**Purpose.** Audit 2's probe 2.8 found real assets and insurance-linked securities "absent as a subject; cat bonds/ILS 11 hits, all in Tail", and probe 2.11 found private real assets absent. This paper is the library's home for:
- real estate (residential, commercial, REITs, and the housing channel's macro feedback);
- infrastructure;
- agriculture (short);
- insurance-linked risk transfer, at the weight the market gives it. Decision 2 of 7 Sep: "Insurance-linked risk transfer at the weight the market gives it, not the weight the operator's profession gives it; do not overstate its relevance."

**Organizing claim.** A real asset is a claim on a physical service whose price is set mostly by the cost and availability of the financing behind it. Housing and commercial property therefore move with the rate and credit cycle more than with their own supply. Infrastructure trades as long-duration, inflation-linked credit. Insurance-linked risk transfer is the one asset in the paper whose returns come from an event risk that the financial cycle does not drive. That makes it a diversifier in principle and a small, capacity-constrained market in practice.

**Parts and chapters.**

*Part I — Real estate.*
1. **Housing as an asset and as a channel:** the mortgage rate → affordability → turnover → prices → the wealth effect and construction. Why housing leads the cycle and why turnover moves before prices.
2. **Reading the housing cycle:** pending sales, purchase applications, months of supply, the mortgage spread, the real price level; per household, not raw (items 36, 37, 68, 69, as measured).
3. **Commercial real estate:** office, retail, industrial and data centres. CRE loans and the regional banks, appraisal lag and the extension-or-foreclose choice; private real-estate funds and redemption gates. Credit is cited for CRE credit and private credit.
4. **REITs:** the listed proxy, what it front-runs and what it misprices; REITs against the market.

*Part II — Infrastructure and agriculture.*
5. **Infrastructure:** regulated and contracted returns, inflation linkage, duration; why it trades as credit; the power and data-centre build as demand (cite Energy).
6. **Agriculture,** a section (decision 4): stocks-to-use, the crop calendar, weather; cite the Quarterly's agriculture chapter for the series.

*Part III — Risk transfer.*
7. **Insurance-linked securities and catastrophe bonds:** what the investor is paid for; the low-correlation claim and where it fails (2005, 2011, 2017–18 as loss years); capacity.
8. **The reinsurance cycle:** capital, losses and price; hard and soft markets; trapped capital; how a loss year reprices the next renewal.
9. **Insurers as allocators,** a section of chapter 8 (decision 3): liability-driven demand for duration, credit and private credit; the link to the housing and municipal markets the Twenty-Five's M7 gestures at. Price, Time, and Edge is cited for the holders' ecology.

*Part IV — Closing.*
10. Tactical Applications.
11. Wiring.
12. Environments.
- Appendix A: Assumptions & Falsifiers, including the standing register's "insured catastrophe losses vs. capital" tripwire.
- Appendix B: dated material.

**Worked examples (one per mechanism).**

| Mechanism | Worked example (numbers) | Historical instance | On the day |
|---|---|---|---|
| Affordability and turnover | a payment on a median home at two mortgage rates | 2022's rate rise | pending sales falling before prices |
| Housing as a lead | permits and pending sales ahead of the cycle | 2006–07 (cite Debt Cycles' 2007 chapter for the top; this paper gives the channel) | turnover's peak |
| CRE appraisal lag | a private mark against the listed REIT's implied value | 2022–23 | redemption gates on non-traded funds |
| CRE and banks | CRE loans as a share of a regional bank's book | 2023 (cite Credit) | the deposit flight |
| REITs as front-runner | the REIT index against private marks | 2022 | the listed drawdown preceding the appraisals |
| Infrastructure as credit | a contracted cash flow's value at two discount rates | 2022 | the long-duration selloff |
| Catastrophe bond pricing | expected loss, spread and the multiple | a loss year (2017–18) | the post-event secondary market |
| Reinsurance repricing | capital against losses into the next renewal | the 2023 renewal | the January renewals |
| Insurer allocation | a liability's duration matched by assets | the gilt episode's LDI demand (cite XXX and Debt Cycles) | — |

**Must cite (by short name):**
- Credit: CRE, private credit, the banks;
- Tops and Bottoms: housing inputs to the episodes;
- the Twenty-Five: tail M7, the insurance retreat;
- Currencies: real assets as a currency exposure;
- Metals: gold as the other real asset;
- Energy: the power build;
- Price, Time, and Edge: holders;
- Debt Cycles: the environments, and 2007's top;
- Market Structure and Cascades: the LDI spiral;
- the Quarterly's real-estate and agriculture chapters (by chapter title).

**Must not:**
- overstate risk transfer's relevance (decision 2);
- re-narrate 2007's housing top (Debt Cycles and Tops and Bottoms own it);
- carry any level or probability in the timeless body;
- use any Brookfield-group instrument, fund or affiliate as an example (Standing rule 1). Brookfield is a large manager in real estate, infrastructure, renewables and insurance, so every listed example in Parts I to III is an index, an ETF or a named episode.

**What the register and the ledgers already measure (describe, do not re-derive).**

| Item | What is measured | Keys or module |
|---|---|---|
| 36 | US pending home sales; NAR's index dropped under rule 30, Redfin's kept | `redfin.pending_sales`, `redfin.months_of_supply`, `redfin.inventory` |
| 37 | MBA purchase applications (an amendment to 36) | `mba.purchase_sa_wow`, `mba.purchase_nsa_yoy` |
| 68 | pending sales per household, single-source | `fred.households` with `redfin.pending_sales` |
| 69 | the housing footprint: the PMMS spread, GSE holdings where keyless, the real Case-Shiller percentile | `calc.mortgage_spread_10y_bp`, `shiller.real_home_price`, `fred.case_shiller_national`; `altdata/batch14_a1.py` |
| AQ-3 | the Quarterly's real-estate rows | `fred.cre_delinq`, `calc.xlre_spy`, `calc.vnq_spy` |
| 66 | the wealth-effect impulse (housing's partner channel) | `altdata/transmission.py`; ST-R6.66c **FAIL, n 65** (D9) |

**Figures (with the store keys each draws from).**

| # | Figure | Keys |
|---|---|---|
| 1 | Pending sales per household through two cycles | `redfin.pending_sales`, `fred.households` |
| 2 | The mortgage spread against the 10-year | `calc.mortgage_spread_10y_bp` |
| 3 | The real house price over a century | `shiller.real_home_price` |
| 4 | CRE delinquency against the regional-bank episodes | `fred.cre_delinq` |
| 5 | REITs against the market | `calc.vnq_spy`, `calc.xlre_spy` |
| 6 | The reinsurance cycle as a loop: capital, losses, price; conceptual, no series (no ILS or reinsurance price index is stored) | — |

**EMPHASIS DECISIONS for Ari (XXIX).**

1. **The weight of housing against CRE and infrastructure.**
   - Options: (a) housing about 4,500 words, CRE 2,500, infrastructure 1,000; (b) equal thirds; (c) CRE first.
   - **Recommend (a).** Housing is the channel the system measures (items 36, 37, 68, 69, 66) and the one that feeds the macro cycle. CRE is narrower, mostly a bank-credit story that Credit already carries in part. Infrastructure is a duration-and-credit trade the reader can learn in a chapter.
2. **The length of the ILS and reinsurance-cycle chapters under decision 2.**
   - Options: (a) about 2,000 words across chapters 7 and 8; (b) about 3,500; (c) one section, about 1,000.
   - **Recommend (a).** The catastrophe-bond and ILS market is small against the asset classes around it, and the book cannot easily hold it. Decision 2 asks for the weight the market gives it. Two thousand words teach the mechanism (event risk priced off the financial cycle) and the cycle's repricing without making the paper about the operator's profession. A single section would not carry the cycle.
3. **Insurers as allocators: a chapter or a section.**
   - Options: (a) a section of chapter 8; (b) its own chapter.
   - **Recommend (a).** Price, Time, and Edge owns the holders' ecology. What this paper adds is the liability-matching mechanism and its link to housing, credit and LDI, which fits a section. A chapter would repeat the holders' map.
4. **Agriculture: a section or a reference.**
   - Options: (a) a short section (about 500 words) with a reference to the Quarterly's chapter; (b) a reference only.
   - **Recommend (a).** The audit found agriculture "absent (9 passing hits)" across the corpus, and the Quarterly's agriculture chapter has rows but no mechanism prose. Five hundred words on stocks-to-use and the crop calendar give the reader the frame. A reference alone leaves the subject absent.
5. **Private real-estate funds and appraisal smoothing.**
   - Options: (a) a section of chapter 3; (b) out of scope.
   - **Recommend (a).** Marks that lag the listed market are the same mechanism as private credit's unanchored marks, which Credit and the Quarterly's credit chapter already flag. Teaching it once in the real-estate setting connects the two.
6. **Whether XXIX joins the core track.**
   - Options: (a) reference shelf, outside the core track; (b) core track at position 6.
   - **Recommend (a).** The core track is the 230,000 words a reader reads in order. The housing channel is already taught in macro terms by Macro Dynamics and The Rate and Liquidity Machine, so XXIX is consulted rather than read in sequence. The guide's reading plan names it beside Credit.

---

## XXXII — The Annual Structural Review: the check, and the brief

**The check (25 Oct 2026).**
- **The paper is absent.** `docs/whitepapers/` holds no Annual Structural Review, and `tools/check_library.py`'s REGISTRY carries no XXXII. Its comment reads: "XXVI-XXXII are reserved by Audit 2's approved roster (Markets XXVI-XXX, the Top & Bottom manual XXXI, the Annual Structural Review XXXII)".
- **The thirteen-month warning is absent.** Audit 2 §5.2 asks: "`library-check` warns when any paper's last-reviewed date is more than thirteen months old, and fails when a paper's appendix (b) is missing." `check_library.py` has no last-reviewed check and no appendix (b) check. No masthead carries a last-reviewed field for one to read.
- **A related numeral fact.** Audit 2's decision 4 placed the behavioural paper at XXXIII, but XXXIII is now the Reporting System. The REGISTRY's comment says that was "the next free numeral", and XXXIV is Emerging Markets. When the behavioural paper is written, it takes the next free numeral, XXXV, and the guide's roster should say so.

**The brief.**

**Slug:** `annual-structural-review` · **Numeral:** XXXII · **Shelf:** System · **Target:** ~5,000 words · **Version:** 1.0

**Purpose.** Audit 2's Part 5 as a protocol with a log: the mechanism by which the timeless papers are checked against the world once a year and whenever a tripwire fires.

**Parts.**
1. **The four instruments,** as Audit 2 §5.1 specifies them:
   - the Assumptions & Falsifiers appendix in every Markets paper;
   - the dated-figure recomputation (`make annual-review`);
   - the relationship health check (holding / weakening / broken / re-attached);
   - the structural scan on a fixed questionnaire.
2. **The standing register as a file:** `docs/annual-review/standing-register.yaml`, one entry per change in §5.3's table. Each entry has the change, the papers touched, the measurable tripwire (a registry key where one exists, else "no series: a named gap"), the threshold and the status. The library gate reads it and fails an entry without a tripwire.
3. **The questionnaire,** verbatim from §5.1 Instrument 4: the ten adversarial questions; the three forced inputs (the mutation scan, the size scan, the register's anomalies); the per-paper reaffirm / amend / rewrite / retire.
4. **The calendar:**
   - annual, in January, the week after the January Monthly;
   - off-cycle within the month on a tripwire, with Doctrine Rule 20 preserved: "the tripwire opens the question; the monthly session decides";
   - the log, `docs/annual-review/log-<year>.md`, dated and never edited.
5. **What the review is not** (§5.4): not a re-forecast; an unedited paper is a recorded decision.

**EMPHASIS DECISIONS for Ari (XXXII).**

1. **When to write it.**
   - Options: (a) Draft 1 before the first review, in December 2026; (b) after the first review, written from its log.
   - **Recommend (a).** The first review needs the protocol and the register file to exist. A protocol written after the fact describes what was done, not what should be.
2. **The standing register's format.**
   - Options: (a) a YAML file the gate reads; (b) a table in the paper.
   - **Recommend (a).** Audit 2 asked for a register "each paper's appendix (d) can point at". A file a gate reads cannot drift from the papers that cite it, as a table in prose can.
3. **The thirteen-month warning.**
   - Options: (a) add a `Last reviewed:` line to every masthead, seeded with each paper's current version date, and the warning in check_library; (b) the warning silent until the first review stamps each paper.
   - **Recommend (a).** Seeded dates make the warning live from the first merge, and the first review then replaces them with real review dates. Option (b) leaves the gate checking nothing for a year.
4. **The appendix (b) failure.**
   - Options: (a) fail only papers written from now on; (b) fail every Markets paper now.
   - **Recommend (a).** Most papers predate the standard. Failing them all at once would block every library merge until twenty papers are edited.

---

## Notes

**Departures and readings.**
- **The fragility chain's numbers.** The paste lists items 64, 67, 71 and 74; under the filing tables these are two items. Batch 14's F1 files the order's 64 as **71**; Batch 15 files its 67 as **74**. Filed 64 (the real 10-year against Shiller's excess CAPE yield) and filed 67 (PEG and LTEG, listed gaps) are not market structure. The brief cites the filed numbers and names the written ones once.
- **XXVII's coverage, so the new papers do not repeat it** (read from `docs/whitepapers/debt-cycles-regimes-environments-whitepaper.md` on `library-xxvii`; `docs/briefs/library-xxvii-notes.md` is on that branch only):
  - XXVII gives 1987 as an environment instance and the 2022 gilts as a fiscal crisis;
  - it narrates 2007's mortgage-credit top;
  - it treats the VRP's crash behaviour across environments.

  XXX takes the mechanisms of 1987 and the gilts and cites XXVII for the rest. XXIX takes the housing channel and cites XXVII for the 2007 top.
- **The behavioural paper's numeral** (XXXIII in Audit 2's decision 4) is now taken by the Reporting System; it would take XXXV.

**The guide's word total, read from a tool (a proposal for the next merge; nothing built).** The header's "roughly 426,000 words" is hand-written. B62 measured 468,027 on `library-xxvii`, and check 11 only warns when the two differ by more than 5%.

The one-line change: give `check_11_wordcount` a `--write-total` mode that replaces the number matched by `roughly ([\d,]+) words` with the measured total, rounded to the thousand. The stitcher runs it at each merge, as the cloud-sessions brief's `stitch_counts.py` does for CLAUDE.md's counts. The guide's sentence then stays as written, and the number in it is the tool's.

**Validation.** Section numbering here is sequential; the library gate was run on this branch before the push (below).
