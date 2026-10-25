# The Reporting System: A Reader's Guide

## What Each Report Is, Where Its Numbers Come From, What It May Say, and How It Learns

**Companion white paper — chester-reports library**
**Series placement:** Companion **XXXIII** — System shelf, after *The Operating Doctrine* and *Building and Validating a Systematic Book*, per the library guide. Cross-references in this paper are by name.
**Version:** Draft 4 — 24 October 2026 (Draft 3, 19 October 2026; Draft 2, 9 October 2026; Draft 1, 6 October 2026, described the Monthly before it joined the stack)
**Status:** Draft 4 — 24 October 2026; as built on chain-7 and a61b-feed-repair, ahead of their merges (a61b 27 Oct; chain-7 after the 1 Nov Monthly). "Built" means the contents of the seventh stitched chain (`chain-7`, which carries the third to sixth chains, the four post-Monthly branches, 6f, the one-day trigger, the new sources and the reading budgets) and of the feed repair (`a61b-feed-repair`, which merges on 27 October). Where the two differ, the paper says which. A capability on a branch that merges later is listed as not built (Appendix E). The paper describes the system as that code stands on the day of writing, says plainly what is specified but not built, and keeps every timer, threshold, budget and source count in the dated Appendix A. Appendix D records what became of each place where Draft 1 found the commissioning brief disagreeing with the code, and of each item Drafts 2 and 3 called not built. Reread after the first stacked Monthly (1 November 2026), after the Doctrine #2 sitting (7–8 November) and at Audit #5.

**Errata.** Draft 3's own errata of 19 October (decision 17) are applied: the LBMA gold price is not a source, the Monthly's chart cap is twelve, its reading target is fifty-five minutes, and the chat-side tasks are recorded in the Master Guide. Draft 4 corrects these further slips in Draft 3:
- §2.3 placed the national statistics offices' CPIs, the Banque de France's yield, the Census Bureau's construction spending, Cboe's indices and the SEC's filings among the official writers; the feed roster files them as external tables.
- §4.6 named the Monthly's charts M1 to M13; the set is M0 to M13, M0 being three months of SPY's daily candles in The tape.
- §4.9 and Appendix A called W11 the second positioning panel; W11 is the standing decomposition in What's priced, and the Weekly's dealer panel enters fifth, not fourth.
- §6.3 said the repository records no Monthly signal scan; the scheduled-tasks record defines it, as Appendix D's item 16 said.
- §6.5 announced two further scheduled tasks and named one.
- §6.5 said the MSTR/MSCI watch reads Strategy's mNAV from the store; the chat-side task records the index review's notices to Drive, and no reader in the repository reads its file. The digital-assets addendum reads mNAV from the store.
- Appendix D, item 4, said nothing writes an observed knowable time; the ALFRED backfill does (15 October).
- Appendix D, item 12, called the Monthly's timer enabled by hand; it has been on the deploy's list since 9 October, as Draft 3's own second table said.
- Appendix D's second table said the broker sync's comment still says 17:00; it says 17:30 since the third chain.
- Appendix E listed the PRL explorer's endpoint as unbuilt; it was closed as a listed gap on 18 October. It also listed two intake-queue entries waiting for "T&B full"; the queue holds one.

---

### Reader's note

This paper is for the operator: the one person who reads every report, takes every decision and rules on every change. It is meant to be read once from start to finish, on a phone or at a desk, and then consulted when a report prints something unfamiliar. Read whole, it takes about an hour and a half (some 23,400 words at the reports' own pace of 250 words a minute). It answers four questions about every report the system produces: what the report is, where its numbers come from, what it may and may not say, and how the system learns from what it said.

The other papers on this shelf describe one machine each. The Daily Cascade paper is the field guide to the daily sections; the Monthly manual covers the macro pillars; the Systematic Book paper describes the register and the broker connection as they were built; the Operating Doctrine says what the operator is to do. This paper sits above them and explains how the pieces fit: how a number travels from a public website into the store, from the store into one shared description of the market, from that description into a report, from the report into a decision, and from the decision into a graded record that eventually changes the rules. Figure 1 draws that path; the ten Parts walk it.

Three conventions run through the paper. First, nothing here is a market view. The paper describes machinery; the reports carry the readings. Second, the body is timeless. Anything that will change with the next configuration edit, such as a timer, a threshold, a word budget or the number of sources, sits in Appendix A with the date it was true. Third, where a capability is specified but not yet built, the paper says so in the sentence that describes it. A guide that describes the intended system as if it were running is the most dangerous kind of documentation, because it is the kind a reader trusts.

**Prerequisites.** None beyond the Operating Doctrine's first three Parts, which explain the books and the dials. The Dealer's Hand teaches the options mechanics behind the dealer-positioning figures; Base Rates and Evidence and Inference teach the statistics behind the grading. This paper uses their results and does not re-derive them.

![Figure 1 — The reporting system's data flow: feeds, the store, the market-state object, the reports, the register, the ledger, grading and the Doctrine](../figures/reporting-system/fig-01.svg)

*Figure 1 — How a number becomes a lesson. Each stage reads only from the stage above it; the left-hand bands name who acts at each stage. The dashed return path is the only way the system changes itself: graded evidence, ratified at a sitting, comes back as configuration. On the right are the two side layers: the Alpha Lab, which reads the store and reaches the register only as evidence the operator may table, and chester-meme, which reads the Security Master's export and writes packets that enter the register only as drafts the operator confirms. Below them, Draft 4 adds stage 4's weekday touches: the anchor, the open note at 09:50, the 12:30 slot, the close with its event area, and the evening note at 21:30.*

---

## Part I — What the System Is For

### 1.1 One regime, one store, one register

The system exists to replace the operator's news consumption with something narrower and more honest. A financial news feed is written to be read, not to be right. It explains every move after the fact, names a cause for every wiggle, and never returns to check whether last week's explanation held up. The reports are built on the opposite principle. They say what moved and by how much, state what the system's own rules make of it, and keep a record that allows every forward-looking statement to be graded later.

Three single points of truth make this possible. There is **one store**: every number any report prints was first written to a single database, together with the time it became knowable, so that any figure can be traced and any past report can be replayed as it would have looked at the time. There is **one regime**: a single object, computed once per session, describes the state of the market in a fixed vocabulary, and every report reads that object rather than forming its own opinion. And there is **one register**: every decision the operator takes, declines or abstains from is written once, in a fixed format, and never edited.

The three are deliberately separate. The store holds facts, the regime object holds a description of those facts, and the register holds what the operator decided to do about them. None of them can write into another. A report can read all three, but it can write only to the ledger of its own forecasts and to the archive of its own editions.

**Five layers.** Around those three sit five layers, and the rest of the paper takes them in turn.
1. **The reporting stack:** the anchor at 07:00, the close at 16:45, the Weekly on Sunday, the Monthly on the 1st and the Quarterly once a quarter, with an alert-only slot at 12:30 and two short secondary notes, the open note at 09:50 and the evening note at 21:30, which check in between the reports of record (Part IV).
2. **The data and architecture layer:** one store with its clocks, marks and ids, the Security Master and the encrypted backup (Part II).
3. **The decision layer:** the register, the books, the gate at entry and reconciliation (Part VII).
4. **The Alpha Lab:** a paper research layer with its own database and book (Part VIII).
5. **chester-meme:** a separate repository on the same box that scans memecoin names and writes decision packets for the operator to confirm (Part VI).

### 1.2 The organising principle

The system's organising principle was ruled in October 2026 as the seventh of the Enterprise Layer rulings, and its first sentence carries the design: *code establishes facts and measures outcomes.* The rest of the ruling follows from it. Books decide within their horizons. Research proposes and never promotes. The operator governs, and the operator's attention is the budget everything else spends.

In practice this principle splits the work of every report into three layers, and the split is the most important thing to understand about how the reports are made.

**Code establishes facts.** Every number on the page, including every level, percentile, change, count and flag, is computed by deterministic code from the store. The language model never computes a figure. When a report says that the 20-day average "held", that is a status computed by a declared rule, not a reading of a chart.

**The model copies.** A language model writes the connecting prose: the claim lines, the paragraphs, the explanations of what a table shows. It sees only a small payload of already-computed figures, and every number it writes is audited against that payload before the paragraph can print. If the audit fails, the paragraph is withheld and the reader sees why.

**Code measures outcomes.** Every forward-looking statement, whether an outlook, a scenario weight or a decision, is written to a ledger before its outcome is known and graded by code when it resolves. Nobody, including the operator, grades by hand.

### 1.3 What the reports replace, and what they do not

The reports replace the habit of scanning headlines to find out what happened. They do not replace judgment. Each one stops at the edge of a decision: it can say that a gap between two markets has been unusually wide for six sessions, but it cannot say what to do about it. That boundary is enforced in two places. The prose rules forbid the model from offering motives, recommendations or views (Part V). The register is the only place a decision can be written, and only the operator writes to it (Part VII).

The same boundary applies to the research the system does on its own schedule. The scans (Part VI) read public sources, compare them with what the system already holds and propose changes, but none of them can change anything. Every proposal goes to a ruling in chat, and only ratified rulings change the configuration.

The two newest layers sit outside the boundary in the same way. **The Alpha Lab is not a book and holds no decision right.** It writes no candidate, packet, dial, band, tell or narrative; it does not read the Monthly to decide; and its results reach a sitting only as evidence the operator chooses to table. **chester-meme is not a book either.** Its packets enter the register as Book D drafts, and nothing it writes becomes a decision until the operator confirms it.

---

## Part II — The Data the System Holds

### 2.1 The store and its three clocks

Every number the system uses lives in one SQLite database as an *observation*: a value, the series it belongs to, the source it came from, and three timestamps. The three timestamps are the foundation of everything else, so they are worth stating carefully.

**When it happened** (`observed_at`) is the period the value describes. August's payrolls describe August.

**When it was knowable** (`available_at`) is the first moment the system could have known the value. August's payrolls become knowable when they are released in early September.

**When it was written** (`ingested_at`) is when the system actually wrote it down.

A single date is not enough because economic data is revised. The first print of a payroll number is often changed in the following months, and a store that overwrites the old value with the new one destroys the information a backtest needs: what was known on the day. The store therefore never overwrites. A revision arrives as a new row with a later *knowable* time, and history accumulates instead of being replaced.

### 2.2 The point-in-time rule and the vintage rule

Two rules govern how the store is read and how its history is filled.

**The point-in-time rule.** Every read of the store asks for the latest value that was knowable at a stated cutoff, filtering on *when it was knowable* and never on *when it happened*. Leakage, the error of using information that did not yet exist, is about when something was known. A report written for a past date sees exactly what it would have seen on that date. This is why a dry run of an old Weekly can be trusted: it is the old Weekly, minus only the data that arrived later.

**The vintage rule.** History that was collected late has to be stamped with *some* knowable time, and the rule is strict about which. A daily closing price is knowable shortly after the close and is never revised except by a stock split, so when the system backfills years of prices it may *reconstruct* the knowable time as the close plus a declared delay. Those rows are flagged as reconstructed. A revisable series, such as payrolls or GDP, may not be reconstructed this way, because stamping the third revision as "known at the first release" would hand a backtest a number that did not exist for months. Revisable series get true historical vintages or nothing. The backfill tool reads each series' declared revision policy and refuses any that is not reconstructable.

Every row also records *how* its knowable time was set: observed from a true vintage source, taken as the moment of ingestion (what every live pull does, which is an honest upper bound), or reconstructed. One consequence is visible in the reports. A series first ingested today has no knowable history before today, so a week-on-week change prints "no prior" until a week of history exists, unless an honest backfill reconstructs it.

Intraday bars live in their own table in the same database, with the same three clocks: a bar's start time, the moment it was knowable, and the moment it was written. A backfilled bar is stamped as knowable at its close plus the feed's delay. A bar fetched before it closed is dropped, because it was a bar in progress rather than a bar.

### 2.3 The feed families

The feeds are grouped into families. Each family has its own puller, its own schedule and its own definition of stale. A heartbeat check reads each series against its declared freshness allowance every morning and raises a "feed stale" verdict when any family falls behind.

**Prices.** Daily closes, and for the tape set opens, highs and lows, for several dozen market symbols: the major index funds, the eleven sector funds, bond, credit and commodity funds, the dollar index, the main currency pairs, the Treasury yield indices, front-month gold, oil and copper futures, Bitcoin, and the volatility indices. Since Draft 3 the basket also carries the capex chain's proxies (the semiconductor, memory, grid, networking, cooling, construction and lithography names the AI capex chain reads), a regional-bank fund, an AI fund against its total-return benchmark, and a hedge-fund replication proxy read beside the CFTC's positioning. These are the raw material of the trend, breadth and volatility readings and of every chart. A separate *bars* feed pulls five-minute bars for the tape set, plus the S&P 500 e-mini future across its nearly 24-hour session, so that the overnight move can be drawn beside the cash session. Since the 14 October audit, a Saturday pull corrects the week's prices, and every price and FRED pull is followed by a check for bad prints (§2.6).

**FRED.** The St. Louis Fed's database supplies the bulk of the macro series: rates and yields, credit spreads, inflation expectations, labour-market data, the Fed's balance sheet and its liabilities, the components behind the inflation, labour, PPI and GDP lenses, and a set of signal series pulled and watched. FRED deprecates series without notice; a series that goes quiet surfaces as stale rather than breaking a run. Deep history is written from ALFRED at each value's first publication, so a backtest sees what was known on the day (§2.2). The pull is incremental: each run asks only for what it does not already hold.

**The official writers.** A set of small writers reads specific official sources directly: the New York Fed's term-premium model, the San Francisco Fed's term-structure model, the Fed Board's TIPS decomposition and its inflation-expectations index, the New York Fed's consumer survey, TreasuryDirect's auction results, the Treasury's debt statistics, the TIC capital-flow data, China's SAFE reserve and balance-of-payments data, Japan's Ministry of Finance bond yields, the CFETS yuan fixing, the CFTC's Commitments of Traders, and the EIA's weekly petroleum report. The family also holds the Bundesbank's ten-year yield, the BIS's policy rates, the ECB's long-term rates and the Treasury's fiscal data, and since Draft 3 the Office of Financial Research's stress index and the FDIC's quarterly banking profile. Each writer declares its keys. If one fails, it marks itself stale and keeps the last good vintage, so one outage never takes down another source.

**External tables.** Slower or less official sources: the University of Michigan's long-run inflation expectations, the Tuck data library's industry and value-factor returns, a university data library's industry multiples, the shillerdata.com workbook's CAPE inputs and, since Draft 3, its long real home-price series, the World Bank's commodity indices, FINRA's margin statistics, the AAII sentiment survey, leveraged-ETF assets (the ProShares funds, the Dow and Russell pairs among them), the national statistics offices' CPI releases, the Banque de France's ten-year yield, the Census Bureau's construction spending, Cboe's correlation and dispersion indices, the SEC's XBRL frames for the hyperscalers' filed cash flow and capex, Redfin's and Zillow's housing series, and a set of company fundamentals stamped by their filing dates. The LBMA gold price is not among them: its writer was retired from the roster, its parser kept, and the themes read the COMEX front future under its own name. The SEC's quarterly 13F data sets are read by a loader the operator runs on the box; nothing schedules it.

**Loggers.** Forward-only collectors for things nobody archives: retail trading activity in the most-traded names, analyst consensus estimates, short volume and short interest, retail chatter on social forums (including the WallStreetBets feed) measured as mention counts, the Zcash market, the VIX futures curve, Nasdaq Trader's daily symbol directories and, dormant until a data entitlement is confirmed, the closing-auction imbalance. Loggers exist because these series cannot be backfilled: a day not logged is a day lost.

**Prediction markets.** Odds from Kalshi and Polymarket on a declared watch list. Their rights are narrow by ruling: discovery, an attention flag when a probability moves sharply in a day, and a disagreement flag when the venues differ materially from the futures market or from a scenario weight. They never change a scenario weight, a narrative, a theme or a book, and they are never a trigger. A gate stands in front of any larger role. Only after a long archive of live (not backfilled) snapshots, a minimum number of qualifying shocks, a study showing the venues lead the assets after costs, and two Monthly calibration reviews may anyone propose letting them modify confidence. That study is not built.

**Fed funds futures.** The CBOT contracts for the next several meetings, converted into the market's implied path for the policy rate. When too few meetings are priced, the path prints as "not yet tracked".

**The crypto data layer.** Keyless public sources read once a day after the US close: perpetual funding and open interest from Hyperliquid, OKX and Deribit; Deribit's implied-volatility index (DVOL); stablecoin supply and the watch names' fees from DefiLlama, with a labelled break where a protocol merges into another; the Fear & Greed index; Bitcoin's hashrate, difficulty and fees; Ethereum's network figures; the froth gauge's new pools; and the total market cap from CoinPaprika. CoinGecko is retired, because its terms bar storing its data, and Bybit is switched off by a country block. The spot bitcoin and ether ETF flows were read from Farside until its site refused automated reads; on the feed repair the source is declared refused and the flow lines print that gap (§2.7). The flags these series could raise are stored with their gate status "not passed" and print nowhere until their ledgers pass (§9.9).

**The option chain capture.** Every evening the system captures the full option chains for the major index funds and a set of large single names, and stores them raw. From each chain it computes the dealer-positioning figures the Dealer's Hand derives: net gamma exposure and its dollar value per 1% move, delta, vanna and charm exposure, the gamma flip, the call and put walls, the strike of peak absolute gamma, and max pain. These rest on a stated convention about which side dealers are on, which the reports name every time they print a dealer figure. The four exposures are treated as one piece of evidence, never four. The capture also yields two figures of the market's own: SPY's at-the-money implied volatility at thirty days, solved by the system's own solver from the option mid prices, and SPY's put/call volume ratio. A missed night is gone; option chains cannot be fetched after the fact.

The capture now runs three times a session: at 09:45 and 12:30 for the intraday read, and at 16:10 for the settled one. Seventeen names come from Yahoo. SPX and SPCX come from a second vendor, Massive, captured at 16:31 because its data is delayed fifteen minutes; their greeks wait behind the implied-volatility solver's gate, which they have not passed. Beside the chains, **a vendor's cross-check** (FlashAlpha) is pulled at 16:25 and stored under its own keys as a labelled comparison. No vendor value enters a flag, a tell, a dial or a decision; a data gate on the box measures how far the vendor's figures diverge from ours (Appendix A).

**The voices scan.** A morning scan of declared public sources (central banks and finance ministries first, then the large asset managers' published views, then news) that records who said what, when, on which subject and in which direction, with a URL for every row. It is described fully in Part VI.

**The events feed.** Release calendars, the session calendar, official news feeds, earnings dates and filings, which tell the reports what is scheduled and what has happened.

**Attention and event sources** (since Draft 3). Three report-only writers run inside the crypto basket's evening pass, each pre-registered as an Alpha Lab hypothesis before its first print: GDELT's raw event files, counted per story; NOAA's population-weighted heating and cooling degree days; and a watch of model releases on the Hugging Face hub. On Saturdays the same pass reads the U.S. cyber agency's known-exploited list and NIST's vulnerability feed, and each day DefiLlama's protocol counts. None of these reaches a dial, a band or a decision.

### 2.4 Which report reads what

The families matter to a reader because each report draws on a different subset. The table summarises it; Appendix A gives the counts.

| Family | Representative series | Cadence | Read by |
|---|---|---|---|
| Prices | SPY, the VIX, the 10-year yield index | Daily, after the close; corrected next morning | The state object, every report |
| Bars | SPY and the tape set at 5 minutes; ES across 23 hours | Daily, after the close | The close's charts; the Weekly's two-week chart |
| FRED | HY spread, 10-year yield, net liquidity | Daily pull; series at their own frequencies | The state object, every report |
| Official writers | Term premium, auctions, TIC, CFTC, JGBs | Daily pull; each at its source's frequency | The close and the Weekly (Plumbing, Positioning); the Monthly |
| External tables | Michigan expectations, AAII, Shiller | Daily pull; mostly monthly sources | The Weekly and the Monthly |
| Loggers | Retail activity, short volume, VIX futures | Daily, forward-only | The close, the Weekly, the state object (VIX curve) |
| Prediction markets | Watched probabilities | Twice daily | The close and the Weekly (What's priced); the Monthly's gate count |
| Fed funds futures | The implied policy path | Daily | The close and the Weekly (What's priced) |
| Option chains | Gamma, walls, flip, max pain; SPY's own IV and put/call | Every evening | The close (Mechanics), the Weekly, the dealer scorecard |
| Voices | Who said what, sourced | Weekday mornings | Narratives in the close, the Weekly and the Monthly |
| Crypto data layer | Funding, open interest, DVOL; the ETF flows' refusal printed as a gap | Daily, after the close | The Weekly's crypto flows block, the addendum, the Monthly's crypto rows |
| Attention and event sources | GDELT's event counts, degree days, model releases, the exploited-vulnerability list | Daily after the close; the cyber lists on Saturdays | The Monthly's slow layers, the addendum; report only |
| Intraday captures | The 09:45 and 12:30 chains | Weekdays | The 12:30 slot, the close's dealer block, the state vector |
| Vendor cross-check | FlashAlpha's exposures and levels | Weekdays 16:25 | The Weekly's labelled comparison; never a flag |

Several sources are pulled and watched for freshness but read by no report yet. They are there because a series cannot be given a history retroactively once its first months have passed unrecorded.

**What the 12:30 slot reads.** Only stored inputs: the session's 12:30 chain capture, the morning's dealer profile (the prior session's settled capture), the VIX's history for the volatility gate, and the 12:30 quotes the funding hooks need. It fetches nothing of its own beyond the capture, and it calls no model.

### 2.5 The Security Master

Every instrument the system names has one identity, kept in one reviewed file and served by one module. An instrument's id is stable and never reused. Beside it sit its asset class, currency, multiplier, exchange, its identifiers under each scheme (the store's key, the broker's id, the option root and others), its aliases and an active window. **An identifier names an instrument only inside its window**, so a reused ticker resolves to the right issuer on each date. A lookup returns exactly one instrument or refuses. A fact neither the repository nor a stored source holds is left empty and listed as unverified, never guessed. New ids are allocated from one declared next id on every branch, and when two branches allocate the same id the stitch that joins them renumbers the collision once (ruled 24 October), so an id, once merged, is never reused.

A morning job keeps Nasdaq Trader's daily symbol directories as reference data and rebuilds the ticker history from them. It then writes **a read-only export**: one security per composite FIGI, with its ticker history. This is the interface chester-meme reads, and nothing in chester-reports reads it back. Indices carry no FIGI and are outside the export. The restricted names are computed into the master from the tracked-entities list at load, never written by hand.

### 2.6 Marks, ids and tiers

The 14 October audit added four guards to the store.
- **The store refuses to forget.** Triggers refuse any update or delete of an observation. The one maintenance path is the compaction tool, and it is audited. Every scheduled writer opens the store through one function, so a writer that bypasses it fails its gate.
- **Every row names its source.** Each row carries a registered source id. A check lists any stored source string that is not registered, and any stored key the registry does not know.
- **Tiers decide ties.** Where two sources hold the same series, the as-of read honours the source's tier.
- **A bad print is marked, never corrected.** After each price and FRED pull, a check lists three things:
  - an outlier: a new print past a declared number of standard deviations of its recent changes;
  - a revision: a FRED value restated for the same date, listed and never flagged;
  - a cross-source gap: the Treasury yield indices against FRED's yields, and the VIX against FRED's copy, past each pair's measured tolerance.

  The close prints the day's marks in its warnings table. A mark never blocks a report and never changes a value.

### 2.7 Declared statuses, publication lags and the store check

**A source can be declared, not only read.** The source and metric registries carry a status beside each entry, and the readers obey it:
- **refused**: the source refuses automated reads (a robots rule, a terms clause, or an HTTP refusal on a polite request). The writer asks for nothing and its lines print "not tracked: <source> refuses automated reads since <date>". Nothing is scraped around a refusal, and a refused source is re-checked only when a session is told to.
- **superseded**: a key replaced by another, named beside it; a superseded key may still be pulled, but no report reads it.
- **gap**: a key with no admissible source, printed as a gap with its reason.
- **while held**: a key that exists only while a position does.

On the feed repair these statuses are read by one function, and the store check lists declared keys apart from stale ones, so a declared gap never reads as a broken feed.

**A lag is the publisher's, never a guess.** A series' age is counted from its observation date, so a source that publishes late looks stale while it is working. A table of publication-lag families adds each publisher's documented delay, with a holiday's slack and a stated bound, to the series' own allowance. A key matches the first family whose pattern fits it. On the feed repair, a computed series inherits the largest lag among its declared inputs. Where a publisher states no delay, no family is written and the source is listed instead.

**"Dead?"** The store check reads the live store read-only and lists stored keys the registry does not know, registered keys with no rows, and stale keys by their own allowance. A key past three times its allowance is marked "dead?" whatever its lag says, so a lag can never hide a source that has stopped.

**The synthetic rows.** Until late September the smoke test wrote synthetic rows into the live store. A purge tool removes them in one audited transaction, after a fresh, integrity-checked backup; it is the operator's to run.

### 2.8 Backups and the restore test

The nightly backup copies the database snapshot and the store's trees **encrypted**, through an rclone crypt remote on a separate Google account used only for backups. The sweep never syncs or deletes; retention is pruned on both sides. The report archive is in the sweep. Without its encryption settings the sweep exits rather than copying in the clear.

Every Sunday a **restore test** pulls the newest snapshot back through the encrypted remote into a private directory. It checks the snapshot's integrity, compares its row count with the count the sweep recorded when it wrote it, and writes a status the morning heartbeat reads. A failed test, or none within eight days, turns the heartbeat's backup field red. The weekly test superseded the monthly restore drill of 14 October, which read the old plaintext remote; the drill is never enabled.

Two other paths are kept apart from the encrypted remote. The inbound files the operator drops in Drive (the AAII row, the GLD archive, the X pilot's files, the Alpha Lab's inbox) are read through a read-only remote. The Alpha Lab's verdicts go out through a third remote that can write only its own files, to a top-level Drive folder of its own, `chester-lab-outbox`.

---

## Part III — The Market-State Object

### 3.1 One description of the market

Once a session, after the close, the system computes one object that describes the market in a fixed vocabulary. Every report reads it; nothing else computes a regime. The object is stored like any other observation, with its own knowable time, so a report written for a past date reads the object as it stood then.

The machinery that computes it holds no market knowledge of its own. Every dimension, member series, threshold and polarity is declared in one configuration file, and each line carries a short "because" that says why the rule points the way it does. Changing the description of the market therefore means changing a declared rule, through the same ratification path as any other rule, rather than editing code.

### 3.2 The dimensions

The object describes the market along a declared set of dimensions: the eight it began with, five added in its second version (6f), and two declared and absent. Each has three states, and each reads an ordered list of member series. The first member is the *primary*: it alone sets the state, by asking where today's value sits in its own five-year history. Roughly, the top third of that history gives the first state, the middle third the second and the bottom third the third, with the direction reversed where a high reading means the opposite thing. The other members are *evidence*. A member in the same band as the state is listed as supporting; a member in a different band is listed as contradicting. This is deliberately not a composite score. A composite would average away exactly the disagreements a reader most needs to see, so the object reports the primary's state and lists the disagreement beside it.

When nothing disagrees, the object says "none found" as a positive claim rather than leaving the field empty. When a dimension cannot be computed, it says why: no series, no fresh series, or no registry entry. Freshness is judged against each series' own reporting rhythm (a weekly series is allowed more sessions than a daily one), and a dimension whose primary is older than a declared multiple of that allowance goes absent rather than reporting a stale state.

| Dimension | States | Primary (what sets the state) | Evidence members |
|---|---|---|---|
| Growth | expanding / slowing / contracting | Four-week jobless claims (inverted) | Permits, job openings, hours, the Sahm rule |
| Inflation | rising / stable / falling | 10-year breakeven | 5y5y breakeven, sticky core CPI, oil |
| Rates | high / mid / low | 10-year yield | 2- and 30-year yields, mortgage rate, the 2s10s curve |
| Liquidity | ample / neutral / tight | Net liquidity | Reverse repo, bank reserves, the Fed's balance sheet, financial conditions |
| Credit | easy / neutral / stressed | High-yield spread (inverted) | BB, CCC and investment-grade spreads |
| Trend | up / flat / down | SPY against its 200-day average | SPY against its 50-day; the 20-day's slope |
| Breadth | broad / mixed / narrow | Share of sector funds above their 50-day | Share above the 200-day; equal- against cap-weight |
| Volatility | elevated / normal / subdued | The VIX, same day | FRED's VIX series; SPY's 20-day realized volatility; Cboe's SKEW, which never makes a tail verdict |
| Positioning | crowded / neutral / light | Margin debt's twelve-month change | Leveraged money's Treasury-futures positioning; a leveraged fund's assets |
| Sentiment | euphoric / neutral / fearful | The AAII bull-bear spread | SPY's put/call volume (inverted); Michigan's sentiment |
| Valuation | rich / fair / cheap | The CAPE, ranked over its full history, with a five-year read beside it | Households' equity share |
| Funding stress | stressed / watch / calm | SOFR against the Fed's reserve rate, on absolute bands | The commercial-paper-to-bill spread; the St. Louis Fed's stress index; the Fed's repo facility for foreign official holders |
| Policy | tightening priced / on hold / easing priced | The 2-year yield against effective fed funds, on absolute bands | The market's gap to the Fed's path; the real policy rate |

Two notes belong with the table. Growth has no daily series, so its state moves with the weekly claims data and lags the market. Breadth is measured across the eleven sector funds, not across every stock, and so understates how narrow a market led by a few large names can be. The object says both things in its own text.

**The five added dimensions are report-only.** No dial, band, packet or engine reads them; they describe. Where a series has a natural zero (a funding spread, the policy gap), its states sit on fixed bands rather than on percentiles, because "above zero" means something a percentile cannot say.

**Two dimensions are declared and absent.** *Earnings* (upgrading, flat, downgrading) waits for a public, keyless index forward-earnings series with history, and then for a year of it. *Geopolitical* (elevated, normal, quiet) waits for a source-checked risk index with a long history and a ruling that admits it. Each prints absent with that reason. A *tail* dimension is not declared at all: the Twenty-Five forbids a single tail index, so the tails are kept as families (§3.11).

**No sub-states.** The object holds its dimensions, the per-horizon reads, the tail families and the debt-cycle branch (§3.9 to §3.11), and nothing finer.
- **The rates driver is withdrawn.** It was a four-cell reading of why yields moved, and it failed its calibration gate twice in late September. A return needs a new pre-registration and a new rules version. What prints instead is each term-structure model's path-and-premium split, dated, with a flag for whether the models agree; it decides nothing.
- **The inflation driver is a read beside the object.** It was ruled as an inflation sub-state, but it prints as a report-only line in the Monthly, outside the object, which carries no driver on inflation.

### 3.3 The three dials

Three dials condense the dimensions into the vocabulary the Operating Doctrine uses.

**The macro dial** is a declared lookup over two dimensions, growth and inflation, not a model. Expanding growth with rising inflation reads *overheating*; expanding with falling inflation reads *goldilocks*; slowing with rising reads *late cycle*; contracting with rising reads *stagflation*; and so on through nine named outcomes, with *mixed* as the catch-all when the inputs exist but fit no named case. If an input is absent, the dial is absent, not "mixed".

**The volatility dial** reads the VIX against fixed bands (subdued, normal, elevated, crisis), with two companion readings: realized volatility against implied, and the VIX term structure. The term structure is being measured two ways in parallel for a declared trial period, the VIX futures curve against the VIX3M-to-VIX ratio, and the object publishes the one ruled to be published while the other is graded beside it.

**The gamma dial** is the sign of SPY's dollar gamma from the evening's chain capture: positive, negative or flat. It is read from the exposure computation, never recomputed, with no threshold and no smoothing.

### 3.4 Persistence

A state that flickers is worse than useless, because it forces the reader to judge whether a change is real. The object therefore applies a persistence rule. A new raw state must hold for a declared number of consecutive sessions before the published state moves. Until then, the object publishes the old state and says so in plain words: the new state, how many of the required sessions it has held, and that the old state stands until it does. The reports call this *pending*. A recompute of the same session is a revision, not a new reading: the later computation wins, and the earlier one stays in the store as a vintage.

### 3.5 The contradiction table

The dimensions describe each market on its own terms. The contradiction table asks whether markets that usually agree have stopped agreeing. It holds a declared list of pairs, including price against breadth, equities against high-yield credit, the long bond against high yield, implied volatility against realized, growth against cyclical stocks, the gamma dial against the trend, and each active story against the data. Each pair has a plain-language description of what each side is saying and what would close the gap.

**The gap z-score, for a reader.** For a pair of series, the system takes each series over the same five-year window and expresses each day's value as a z-score: how many standard deviations it sits from its own five-year average. It subtracts one from the other, with the signs arranged so that normal agreement is the baseline. That daily difference is the *gap*. The question is then how unusual today's gap is compared with the gap's own five-year history, so the gap is itself turned into a z-score. A gap z of 2 means the two markets are further apart than they have been on roughly 95% of days in five years. It is a statement about the relationship, not about either market's level: both can be unremarkable on their own and still disagree unusually. The two series are aligned on common dates first, a slower series being read as of the faster one's dates, and a pair with too few common dates prints no magnitude rather than an unreliable one.

A pair *opens* when its gap z has been at or beyond the declared threshold for the persistence number of sessions, and the date of the first session of that run is kept as its "since". Since the object's second version the close is symmetric: an open pair closes only after the condition has failed for the same number of sessions, showing *closing* in between and keeping its "since". Some pairs, such as gamma against trend, are state mismatches with no magnitude at all, and a reserved pair for prediction markets prints absent until its own gate opens.

### 3.6 Exceptions

An exception is something the reports must surface even when no state moved. There are two kinds. A **contradiction exception** is an open pair that has stayed open for a declared number of sessions; the plain-language label is "a gap between two markets held past five sessions". An **extreme exception** is any member series at a five-year extreme, meaning a percentile at the very top or bottom of its history, reported even when its dimension's state did not change, unless the reading is itself stale. Exceptions are listed contradictions first, and they are report-only: they inform; they do not alert and they do not trigger. The Weekly prints its open exceptions in three tiers, each with its resolution path, catalyst and invalidation:
1. a *potential leading indicator*;
2. a *contemporaneous contradiction*;
3. an *extreme without a trade*.

### 3.7 From dials to the Doctrine's regimes

The Operating Doctrine sizes Book A by regime, and its regimes (Expansion, Overheat, Tightening, Contraction and Transition) are not the dial's words. A ratified mapping translates them. Expansion and goldilocks map to Expansion. Late cycle and overheating map to Overheat. Stagflation and the disinflationary slowdown map to Tightening. Contraction and the deflationary bust map to Contraction. Mixed maps to Transition. Each Doctrine regime carries a band for Book A's net equity exposure (Appendix A).

**Transition** has no band of its own; it is computed. When the macro dial has changed state within a declared number of sessions, the regime is Transition, and its band is the lower half of the band the dial is leaving, hedged. Transition applies at once, by code. The move *into* the new regime's band, re-engagement, is never applied by code: the operator rules on it at a sitting. The asymmetry is deliberate. Cutting exposure when the description of the market changes is cheap and reversible. Adding it back is a judgment.

The mapping and the bands live with the risk limits, not with the object. The object describes the market; the Doctrine's regimes are a use the book makes of that description.

### 3.8 Why no report recomputes regime

Every report reads the object through one reader that reads and never computes. The close is the object's only writer. The reason is simple and absolute. A report that computed its own regime could disagree with the close's, and then the system would hold two regimes and no way to say which one a decision was taken under. The grading in Part IX depends on every decision being attributable to one description of the market at one moment. A second regime anywhere would break it.

### 3.9 Per-horizon reads

The trend dimension is read three times, once at each book's horizon: the 20-day average's slope for the days of Book C, SPY against its 50-day average for the weeks of Book B, and SPY against its 200-day average for the months of Book A, which is the trend dimension's own primary. Each read has the dimension's bands and persistence. The three are stored side by side and never collapsed into one, because the organising principle says the object holds the view per horizon. On this chain nothing that acts reads them, and no report prints them; the register's weekly alignment stamp, which will read the weekly one, is on a later branch (Appendix E).

### 3.10 Calibration

The object's states are now graded as states. For each dial, the published state on a session and the published state a declared number of sessions later make one pair, both read from stored objects and never recomputed with today's code; the horizons are the three books', in sessions. The share of pairs from a state that end in each other state is a transition probability, counted and not modelled. A row prints a probability only once its state has a declared minimum of independent starts (starts far enough apart not to overlap). Until then it prints "uncalibrated (n = k of 30)", never a number and never an empty field. A calibrated row's probabilities are smoothed by adding one half to each count, so none is zero or one.

Only the dials' rows reach the probability ledger, and only once calibrated: each evening the close writes them and resolves the rows that have come due. The dimensions' transition table prints in the Monthly and is never ledgered. The close prints one line of the dials' rows, and the Weekly and the Monthly a table. The first read on the box will be uncalibrated everywhere, because the stored history under the current method is short; that is the expected state, not a fault. A read never uses an object computed after its own cutoff.

### 3.11 Tail families and the debt-cycle branch

**The tail families** are the Twenty-Five's seven mechanism families, one row each and never summed. A family's state is *watch* when one of its first-mover series is at a five-year extreme, *quiet* when all are read and none is, and *not read* when none is stored. Every family's probability is "none": the prediction-market rights are discovery only, their calibration gate is not met, and no ruling grants more. The Monthly prints the table in Slow layers, and the Weekly one line.

**The debt-cycle branch** carries its observables (the deficit's share of output, the real 10-year yield, the 10-year breakeven and gold), each as a level with its percentile, and a state of "none", because the diagnostic that would set it belongs to a paper not yet written. It prints in the Monthly's Slow layers only.

### 3.12 What the object may not read

Some series are barred from the object by name. A registry field marks each barred key with the order and rule that barred it, and a gate refuses any barred key as a dimension member, a dial leg or a horizon read. A bar can be narrow, applying to one instrument of a key and not another. It exists so that a series admitted to the store for one report, a vendor's or a by-hand figure for example, can never become part of the one description of the market by accident.

---

## Part IV — The Reports and the Ten-Section Stack

### 4.1 The stack

The daily close, the Weekly and the Monthly are built on one skeleton, the *stack*: ten sections in a fixed order. The same section answers the same question in every edition, so a reader learns where to look once. The three share one set of section builders, one renderer, one prose writer and one paragraph guard; what differs between them is configuration, read by cadence: the period noun, the depth of each section, the word allowance per depth and the prompts. The Monthly adds two chapters of its own (§4.6).

Each section answers one question.

1. **The read** — the handful of lines that matter. In the Weekly, also the week day by day. It never collapses.
2. **The tape** — where prices went and the levels they met, across timeframes, with volume.
3. **Mechanics** — how dealer hedging shaped the moves: the dealer positioning, the volatility regime and its term structure.
4. **What doesn't fit** — where markets disagree with each other: the open contradictions, the exceptions, the divergences.
5. **Plumbing & rates** — yields, auctions, term premium, liquidity and credit.
6. **Positioning & flows** — who holds what and how it changed, and which sectors lead.
7. **What's priced** — what markets and surveys expect, as distinct from how they are positioned: breakevens, consensus, the policy-rate path, prediction markets and, in season, earnings against consensus.
8. **Narratives** — the stories the market is telling and who is telling them, with sourced voices.
9. **Ahead** — what is scheduled and what is being watched, with any outlook printed as a ledgered base rate.
10. **The book** — the operator's decisions, the rules broken, the benchmarks and the attention spent.

| # | Section | The question it answers |
|---|---|---|
| 1 | The read | What matters, in a few lines |
| 2 | The tape | Where prices went, and the levels they met |
| 3 | Mechanics | How dealer hedging shaped the moves |
| 4 | What doesn't fit | Where markets disagree with each other |
| 5 | Plumbing & rates | Rates, the curve, liquidity, credit |
| 6 | Positioning & flows | Who holds what, and how it changed |
| 7 | What's priced | What markets and surveys expect |
| 8 | Narratives | The stories, and who is telling them |
| 9 | Ahead | What is scheduled, and what we are watching |
| 10 | The book | Our decisions, our rules, our attention |

### 4.2 Depth, and the triggers that deepen it

Not every section deserves the same space every day. Each section has a *depth* per cadence: **deep** (paragraphs, a table and possibly a chart), **medium** (one paragraph and a table), **light** (two to four lines), **short**, or a single **line**. The daily close runs the read, the tape, mechanics, what doesn't fit and ahead deep; plumbing and what's priced light; positioning light; narratives as a line; and the book short. The Weekly deepens positioning and gives every section at least a medium treatment. The Monthly runs the read, mechanics, what doesn't fit, plumbing, what's priced, narratives and ahead deep; positioning and the book medium; and the tape light, with the long frame added (§4.6). The depths are declared in configuration, with the word allowance for each depth (Appendix A).

Two sections can be *deepened by computation* rather than by habit. Plumbing goes deep on the daily close when a top-tier release (an FOMC statement or minutes, CPI, the PCE report, payrolls, GDP or the Treasury's quarterly refunding) falls in this session or the next, when a 10- or 30-year auction does, or when a rate or spread moves by more than a declared amount in one session. What's priced goes deep, daily or weekly, when a breakeven, the implied rate for one of the next few FOMC meetings, or a watched prediction-market probability moves by more than its declared threshold. When a trigger fires, the section header says why, and the chart allowance rises by one. The Weekly counts how many sessions each trigger fired on, so that a trigger firing every day or never can be recalibrated at the Doctrine monthly.

### 4.3 The three reading rules

Three rules make a stacked report quick to read.

**Every section opens with a claim line**: one bold sentence that says what the section found. It is written by the model and audited like any other prose.

**Change marks.** A small diamond (◆) appears beside any item whose value differs from the previous edition of the same cadence. A daily mark compares with yesterday's close and a Weekly mark with last week's Weekly, never with a daily. The mark is placed by code, comparing fingerprints of the stored values; the model never places one. With no prior edition, the header says nothing is marked.

**Odds live in the ledger.** A probability may print only if it was first written to the probability ledger (Part IX), and only in the form "the base rate for … is X% (n = …)". There is no other way for a number that looks like a forecast to reach the page.

Two further conventions follow from these rules. A section whose items and table are identical to the prior edition *collapses* to its claim line and "(unchanged since <date>)", so the reader's attention goes where something changed. The read never collapses. And a figure the system does not yet hold is never narrated as missing; it appears once, as a "Not yet tracked" footnote at the foot of its section, so the reader can see the gap without the prose dwelling on it.

### 4.4 The daily close

The close runs each weekday after the cash session, once the evening's prices, bars and option chains are in. It is the system's anchor in three ways. It is the only writer of the market-state object: it computes the object before building the report, and a failure there degrades the report rather than stopping it. It writes the session's base-rate outlooks to the probability ledger *before* it prints them, and resolves those that have come due. And it stores the session's dealer scorecard row, the evening's dealer positioning with SPY's own implied volatility and put/call ratio, from which the Weekly's flags and the Monthly's retrospective are computed.

The close carries up to three charts. The first is SPY's session in five-minute candles with its volume-weighted average price and the dealer levels. It is omitted, with the reason, if too few bars arrived. The second is a few months of daily candles with the moving averages and the week's range. The third is chosen by rule: an open contradiction's gap over recent sessions if one is open; otherwise, if plumbing went deep, the yield curve over the same span; otherwise nothing. It writes its edition to an archive (the payload, the stack, the rendered page) and reports its health to the dashboard.

Since Draft 2 the close has gained:
- **the dealer block:** the session's positioning from the three captures, its quality panel, the horizon matrix, a dealer chart, and three fixed sentences per capture held by the flag-word audit (§5.2);
- **the ES block:** the e-mini future's levels on three timeframes;
- **the state-vector line** (§8.3);
- **the event area** in Mechanics, each block printing only on its trigger (§4.7);
- **the calibration line**: the dials' transition rows, "uncalibrated" until they calibrate (§3.10);
- **a line counting chester-meme's drafts;**
- **the day's data-quality marks** in its warnings (§2.6).

### 4.5 The Weekly

The Weekly runs early on Sunday and reads the week ending on Friday. It assembles the same ten sections at Weekly depth, and every change it reports is the week's. Its prior edition is last week's Weekly, so its change marks mean "since last Sunday".

The Weekly is where the slower data lives. Positioning & flows carries speculative futures positioning, short interest, retail activity and capital flows, and a sector table with one-week, one-month and three-month returns. What's priced adds, in earnings season, the universe names that reported against their stored consensus. Earnings season is determined from the stored earnings dates rather than from the calendar. Ahead carries the graded calls: each forecasting source's running Brier score against the coin. The book carries the benchmarks, the rule-break counts, the attention counts and the expiry of any Transition. A "Changed since last Weekly" block sits under the header, computed from the dials, exceptions, rule breaks, triggers and voices. The header line carries an estimated reading time: prose words at a steady reading pace, plus a short allowance per chart.

The Weekly carries a fixed chart set: SPY over six months and two years; the yield curve and the high-yield spread over one and ten years; speculative positioning as z-scores; the week's sector and style returns; any open contradictions; SPY over 23-hour sessions with the overnight future scaled to SPY by each session's opening basis and the dealer levels drawn; six markets with their averages; positioning and sentiment gauges; prediction-market odds beside the futures path; and the dealer panel. The dealer panel takes a place in the cap and sets another chart aside (Appendix A). It prints the glossary once, at the end.

Since Draft 2 the Weekly opens on **a précis**: the week's tension, six verdicts with their grounds, what would change our mind, what changed in the outlook, and a stance with its sample size. Under it sit a "changed since last Weekly" box and a terms box. Each section opener leads with its finding and ends on a Takeaway. Inside the sections it adds:
- the ES panel and the dealer panels;
- the most-active names by options volume, with their implied volatility against its own stored history;
- the setup profiles and the single-name put share, labelled with no side;
- the crypto flows block;
- the GTM tables;
- the Alpha Lab's one line.

A second PDF, **the digital-assets addendum**, travels with the Weekly's email from its first edition on 1 November (dry run 25 October): nine sections in miniature, built from what already flows and from the crypto data layer.

### 4.6 The Monthly

The Monthly runs on the first of the month, reads the month that ended the day before, and is the longest report. It is a stacked report: the same ten sections as the close and the Weekly, built by the Weekly's own builders over the month's window and assembled by the one function every cadence uses, at Monthly depth. Its prior edition is last month's Monthly, so its change marks mean "since last Monthly", and a "Changed since last Monthly" block sits under the header. It carries two chapters the other cadences do not: **Reading**, placed between Narratives and Ahead, and **Slow layers**, an eleventh section after The book. After Slow layers come the **detail tables**: the regime (the dials and the dimensions; the open contradictions and exceptions are What doesn't fit's), the scenario record (only the weights Ahead does not already print), the register's month, and the appendix.

**The storyline, reconciled.** The Monthly's previous form was a storyline in six parts (Monthly v2's first phase). Each of its parts now prints once, inside the section that answers its question. *The month in markets* gives its scorecard to The tape and its prose to The read. *The month in one page*, five takeaways, is a sub-section of The read. *Looking back*, organised by theme, becomes sub-sections of Narratives, each theme with its prose, its series and its CONSENSUS and NEW developments; the DISSENT and CORRECTION developments go to What doesn't fit, and its computed "what changed" is the header's block. *Voices* are Narratives' sub-sections. *Looking ahead* two to three months is Ahead: the calendar, the scenario set with each weight beside its Brier score and "what would change our mind", and the month's graded calls. **Where our read lands** is The book's, and is still built by code and bounded by rule: the system's read is what the scenario weights and the books already hold, and nothing beyond them. A gate holds the edition to every storyline fact printed once and none lost.

The themes are declared, each mapped to the state object's dimensions and, where one exists, to a story. They are liquidity and plumbing, fiscal dominance and the dollar, the Fed's path, the credit cycle, equity positioning, sentiment, and geopolitics and reserve currency. A tag carries rules: CONSENSUS needs at least two high-tier sources, DISSENT names its source, and CORRECTION cites the earlier statement it corrects.

**The tape, with the long frame.** The tape is light at Monthly depth but carries two things the other cadences do not. The first is the long frame: a 40-week average on weekly closes and 10- and 20-month averages on monthly closes, printed as levels and never as signals; a cross counts only after the monthly close. The second is the cross-asset year to date, a ranked column of asset classes by total return from the prior year's last close to the month-end close, each read through a fund the store already holds, with dividends added on their ex-dates and not reinvested and cash accrued at the three-month bill rate. A class with no proxy, or no year-start close, says why.

**Mechanics: the dealer retrospective.** Mechanics goes deep on the Monthly, and what it carries is a retrospective of the month against dealer positioning. It reads the month's stored dealer scorecard rows, one per session, written by the close; it recomputes nothing. Each session is flagged by the Weekly's own rule, so a session is *pinned* in the Monthly exactly when it was pinned in its Weekly. The flags are pinned (the close near max pain), held (a wall touched and the close inside it), amplified (the flip crossed and the range well beyond the implied one), and an implied-volatility check (SPY's own at-the-money volatility against the VIX). The month's counts and hit rates are taken over the sessions on which each flag could be computed. **The twenty-session rule:** below a declared floor of scored sessions, set in configuration (Appendix A), the counts are not printed as rates, the section says "insufficient sessions (n = …)", and the model is not asked for prose. When prose is written, a flag-word audit holds it to the per-session table: a sentence that says pinned, held or amplified must name a session whose flag is set, or carry that flag's own count for the month.

**Slow layers.** The eleventh section holds what moves too slowly for a Weekly: valuation, base rates (the Top & Bottom record and the bear-rally base rate), tails, and themes (the alternative assets). Its figures print in **triple form**: the latest value, its long-run average and its percentile, each with its data-as-of date and its window. Until the metric lenses are built, the average is taken over the store's full history and the percentile over five years where the store holds them; a shorter history prints its own start and sample size. The equity risk premium and the dividend yield wait for the lenses and say so. Slow layers also prints the newest edition of each scan's reference table from the store, with its source line. The scans' tables are ingested as sourced figures, each with a URL, the scan's own section reference and an as-of date, and an advice row is refused and named.

**Reading.** The Reading chapter is built from the committed reading register and watchlist with no model call. It lists the month's read and listed editions in the watchlist's group order. Each is a hyperlinked title line naming the publisher, the publication date, the data-as-of date where it differs and the scan, followed by the stored summary for a deep or skim item and the one-liner for a list item. An item with no URL is not printed and is counted in the footnote; a pending item never prints; a shelf entry the daily voices scan already stored is printed once and named. The month's window runs from the prior month-end to this one, so consecutive Monthlies tile. Then comes the coming month's due list. The summaries are stored text: escaped, never polished, trimmed or audited, outside the prose budget and inside the reading time.

**Charts M0–M13.** The Monthly draws its own set with the Weekly's chart primitives, from the store at edition time: three months of SPY's daily candles with its 50- and 200-day averages, which prints first in The tape (M0); SPY over three years in weekly candles (M1) and over ten years in monthly candles with the drawdown from the high (M2), each drawing only the levels the tape's prose is given; the dealer retrospective (M3); the 10-year yield with its term premium (M4); twenty years of the high-yield spread with its percentiles (M5); speculative positioning as z-scores (M6); breakevens and the implied policy path at month start against month end (M7); the scenario weights and their Brier scores by edition (M8); and Book Z against the account's value (M9), whose caption says that the books are not yet marked one by one; the fed funds futures' implied path at month start against month end (M10); what is carrying the index, the S&P 500 against its earnings and its multiple (M11); the dealer panel, when the month's settled profiles exist (M12); and a watched mechanism's supply against its design (M13), the first set aside when the cap binds. Each chart sits in the section or sub-section it illustrates, inside the chart cap, and counts toward the reading time.

**What the Monthly gained since Draft 2.**
- The Factor lines and the Rate machine summary.
- The dealer retrospective with its figures.
- The PPI and GDP lenses, and a surprise index that standardises each release by its own history:
  - its FOMC leg is market-implied: the decision less what fed funds futures priced at the prior close;
  - no other release's consensus is stored, so those legs print "no consensus".
- The GTM tables and the crypto rows.
- The Lab report, attached from the Alpha Lab.
- The **system-metrics block**: uptime, feed completeness, incidents, model calls and withheld drafts, printed only as recorded.

The chart set is capped at twelve (Appendix A).

**Budget, prose and fallback.** Each section's prose is one audited model call, with the one revision of §5.3. The word budget is a target, not a cap: nothing is cut or withheld for length, and an edition over its target prints one line at its foot saying how long it runs against the target. A fault in the stacked edition does not stop the Monthly: it degrades to the storyline render. A dry run builds with the model and reads the prior Monthly from the real archive, so its change marks are real, but writes only to a dry-run folder: no fetch, no scans ingest, no snapshot and no dashboard state, and, if asked, one email under a "[DRY RUN]" subject. The scenario weights are read from the probability ledger and are never written by the Monthly; until a scenario register is ruled, the block says the ledger holds none.

### 4.7 The anchor, the two notes, the 12:30 slot and the close

The weekday runs on five touches: the anchor at 07:00, the open note at 09:50, the alert-only slot at 12:30, the close at 16:45 and the evening note at 21:30. The anchor and the close are the reports of record; the two notes and the slot check in between them, and none of the three in between has a right the reports of record do not give it.

**The anchor.** A morning anchor runs before the open. It reads the previous session's state object without recomputing it and opens on a **What changed** block: states moved, extremes set or cleared, dials moved, contradictions opened, closed or persisting, coverage changed, every magnitude stamped with its percentile and the levels moved behind it. A quiet session prints "nothing changed" as a positive statement. The anchor is not stacked. Since Draft 2 it carries:
- the ES block;
- the volatility-event block on the morning after an event;
- the volatile-day flag: each of its arms with its reading and as-of, the gap provisional until the open note settles it, printed and never applied;
- the signal lines: the auction, the FOMC-week gap, the yen flag and the rally inside a bear, each only on its trigger;
- the meme-drafts line;
- **the opening setup**, under the prior close's dealer surface:
  - the expected-movement gauge;
  - three daily volatility lines (the VIX against realised volatility, the term structure's stress, and the short end's spike);
  - "Largest OI builds, side unknown", with each build's estimated premium, its chance in the money and its context tags;
  - two put-volume proxies, for SPY and SPX, each labelled no side.

None of these says who opened a position, because the chains cannot tell. The gauge opens on a pre-market line from the e-mini's overnight print, and SPX's and SPCX's cells read "awaiting the solver gate" until their greeks pass it.

**The open note** runs at 09:50 on weekdays, after the 08:30 releases and the first twenty minutes of trading. It fetches first, into the store only: five-minute bars from 08:00, a targeted pull of the morning's releases, news and a short voices pass. It then reads, in order, the 08:30 releases and the market's reaction, the open against the anchor's expected-movement gauge, the news since 07:00, Book C, and what the close will check; the volatile-day flag prints completed, with the gap settled from the 09:30 open. It may confirm or cancel Book C's 07:00 drafts and never add one; while no 07:00 setup list is built it says so. It asks the model for a paragraph only when its gate opens (a top-tier release, a gap or an early range beyond the gauge, the close's volatility trigger, or the flag), and the paragraph has a hard word cap: past it, the paragraph is withheld, never trimmed.

**The evening note** runs at 21:30 from Sunday to Thursday. It fetches the futures, Asia, currencies, crypto, the yuan's fixing, news, earnings and after-hours moves into the store, then prints the futures since the close (on Sunday, the open against Friday), the after-hours earnings, Asia, currencies, crypto, the news and tonight's Book D drafts. It has no rights. On a quiet weekday it prints one line, that there is nothing to do tonight and the anchor will re-read it all; it asks for a paragraph only when a market has moved past its declared threshold, and always on Sunday. The meme ingest runs a quarter of an hour before it, so tonight's drafts are in.

**Both notes** start as dry runs, mailed under a "[DRY RUN]" subject until the date declared in configuration, write their edition and payload to the archive, append to the withheld-drafts log, and report a fault as a heartbeat warning rather than a failure. Each makes at most one model call and one revision, inside the meter, and none when its gate is shut. Their timers are the operator's to enable (Appendix A).

**The 12:30 slot** is alert-only. After the 12:30 capture it evaluates a list of gates:
- the dealer flip crossed by a confirmed margin;
- the VIX rising past the event threshold (upward only);
- the yen-unwind tell;
- the yuan devaluation tell's tracked legs.

When every gate stays closed, the slot writes nothing and sends nothing. When one opens, it writes the open gates' trigger lines, code-written, to the outbox and mails them once, under the subject "12:30 alert". No model is called.

**The event area.** The close's Mechanics carries a set of event blocks, each printing only on its own trigger, each report-only, and each repeated at depth in the Weekly's and the Monthly's Mechanics:
- **the volatility event:** a one-day or five-day move in the VIX past its thresholds, a crossing of the volatility dial's band, or compression, with a nine-lens attribution and a base rate from stored history; the anchor reprints it the morning after;
- **the rates speed flag's attribution:** when the 10-year moves unusually fast over two weeks or a month, the term-structure models' split of the move into path and premium;
- **the one-day 10-year move:** when the day's absolute change in the 10-year is beyond its declared five-year percentile, either way, the attribution runs, under a ledger pre-registered for it; it reads "not read" while the history is too short;
- **the gold event:** a large one-day or five-day move in gold, with the legs that usually explain it (the real yield, the dollar, oil);
- **the developed-market drawdown screen:** an index's drawdown over ten or twenty sessions past its five-year percentile, for the indices a keyless daily source serves; the others print "not tracked".

None of these is a state of the object, and none reaches a dial, a band or a decision.

The stacked close does not open on that block. Its state table and its contradiction table print at the **end** of the edition as detail tables, after The book and before the glossary, read from the stored object the close's payload carries and never recomputed. The order is deliberate: the ten sections say what the session did, and the tables are there for the reader who wants the object itself. Only the pre-stack form of the close, kept as a fallback, opens on What changed.

### 4.8 The reports that are specified but not built

**The Alternative Assets Quarterly is built and not yet running.** It is the fourth cadence of the same stack. The ten sections over the previous quarter make its front matter, and eleven family chapters make its slow layers, every item tiered as lead or reference. Its timer ships disabled, to be enabled by the operator after its December dry run, and its first edition is planned for the second Saturday of January 2027.

Four reports appear in the architecture and are not built.

**The Quarterly Structural** is planned as the quarter-end report on structural positioning, the tail budget and the states of the long-horizon themes: the Disruptive Themes factor states, the tail families, a rewrite of the library guide's executive summary and a review of the international sleeve, opening on a table of system metrics. It has a place in the work plan and no specification document yet.

**Disruptive Themes** has a reserved dashboard identity and has been re-cadenced from monthly to quarterly, folded into the Quarterly Structural.

**Top & Bottom** is no longer planned as a standalone report. It becomes a state variable, a verdict and a composite printed inside the Monthly and the Weekly. The Monthly already carries its place, under Slow layers' base rates, which prints that the harness is not built until it is.

**The Thailand quarterly** is a short, isolated monitor of a personal exposure, with alerts on the currency, the central bank and payment dates. It sits outside the dials and the register by design, can never trigger anything, and is deferred to the end of the roadmap.

### 4.9 The chart-and-prose rule

Charts and prose describe the same market, so they must describe the same levels. (Each report's chart cap is in Appendix A, with what the dealer charts displace when they enter: in the Weekly the prediction-market chart, and the standing decomposition too when a contradiction chart is open and no trigger fired; in the Monthly the scenario chart; in the close the second daily chart.) Before a report is assembled, the system computes one **level list** for the edition. Each level (prior close, session range, the moving averages, the week's range, the 52-week extremes, the dealer levels) carries its value, source, as-of time and a status: *held*, *broke* or *untested*, set by a declared rule. The prose may name only levels on the list, and may say "held" or "broke" only where the list says so. A chart may draw only levels on the list. A gate holds both to the one object. Charts carry no verdicts. A chart that cannot be drawn prints "chart unavailable" with the reason. The email carries each chart as a small image; the archive keeps it as a scalable file.

### 4.10 What each report writes

| Report | Runs | Reads | Writes | Prose budget | Charts |
|---|---|---|---|---|---|
| Daily close | Weekday evenings | Store, object, register, ledger | The object; outlooks; the dealer scorecard row; chain readings; archive; dashboard state | Smallest | Up to 3 |
| Morning anchor | Weekday mornings | The prior object; overnight moves; events | Archive; dashboard state | Short | None |
| Open note | Weekdays, 09:50 | The morning's releases, bars and news; the anchor's gauge; Book C's drafts | Store (its own fetch); archive; one mail; heartbeat | A hard cap, paragraph only on its gate | One |
| Evening note | Sunday to Thursday, 21:30 | Futures, Asia, currencies, crypto, after-hours moves, news; tonight's Book D drafts | Store (its own fetch); archive; one mail; heartbeat | A hard cap, paragraph only on its gate (always on Sunday) | One |
| Weekly | Sunday morning | Store, object, register, ledger, voices | Archive; dashboard state | Middle | Fixed set |
| Monthly | The 1st | Store, object, register, ledger, voices, scans, the reading register | Scan figures to the store; snapshot; archive; dashboard state | Largest | M0–M13, capped |
| Digital Assets addendum | With the Sunday Weekly, from 1 November | The crypto data layer, the store, the X digest's ledgers | A second PDF with the Weekly's mail | A target, as the Weekly's | Up to two |
| 12:30 slot | Weekdays | The 12:30 capture, the morning profile, stored quotes | An alert file and one mail, only when a gate opens | None | None |
| Alternative Assets Quarterly | Second Saturday of the quarter (disabled) | As the Monthly, over the quarter | Archive; dashboard state | No word budget | Up to 40 |
| Quarterly Structural | Quarter-end | — | — | Not built | — |
| Thailand quarterly | Quarterly | — | — | Not built | — |

Every edition, the 12:30 alert included when it opens, also appends to **the withheld-drafts log**: one line per withheld paragraph with its section and the audit's reason, never the draft, which stays in the run log. The system-metrics block counts it. The volatility event keeps **an event ledger** of its own, seeded with 16 October 2026.

---

## Part V — How the Prose Is Made Honest

### 5.1 Code computes, the model copies

The model that writes the prose is given a small structured payload and nothing else: no store access, no raw chain, no internet. Every figure in that payload was computed by code, rounded to the precision the report prints, and given ready-made companion forms: an ordinal for every percentile ("52nd"), a signed form for every change ("−6.75%", "+12 bp"), and a display form for every large or scaled figure ("$5.87tn", "+29k"). The instruction is to copy these, never to derive. A figure the model was not shown is a figure it would have to invent, and the audits exist to catch exactly that.

The prose is never in the decision path. It writes nothing to the register. Its job is to make the computed page readable, and a page whose prose is withheld is still a complete report.

### 5.2 The audits

Every paragraph passes a series of checks before it can print. Each was added because a real paragraph failed in a way the earlier checks missed.

**The numeral audit** requires every number in the prose to exist in the payload, to within the precision it was written at: "762.45" must match a payload value that rounds to exactly that, so a transposed digit fails. Identifiers that contain digits, dates the payload carries, and small counts spelled as words are not treated as figures, and declared names such as "the 30-year yield" are masked first. Magnitude words are part of the number, so "770 billion" cannot pass against a price of 770. The audit is explicit about its limits: it is not a hallucination detector. A model can still put a true number in a false sentence, which is why the other audits exist.

**The type audit** asks whether a number is the *right kind* of number. Each payload figure carries a type from its field: a count, days, a price, a percentile, a percent, a z-score, basis points, dollars or a ratio. A unit word in the prose that contradicts the type fails: "13-day-old" against a count of 13 rows, or "51st percent" against a percentile. A figure inside a table cell takes the unit written beside it in the cell.

**The ordinal check** fails a malformed ordinal ("96.1th", "52th") and requires a percentile's ordinal to be one of the stored ones, so a model that truncates 51.7 to "51st" is caught.

**The signed check** fails an unsigned magnitude of a negative move. "Gold fell 6.75%" is withheld in favour of the stored signed form.

**The scaled-display check** fails a large figure the model has rescaled itself. A scaled figure is copied, never rescaled.

**The label audit** checks that a number printed beside a named level is the value stored under that name, for the instrument the sentence is about. It was added after a close called max pain "the put wall".

**The tape rules** apply to the stacked reports. They refuse internal vocabulary and registry identifiers in prose. They refuse motive phrases ("because", "driven by", "on fears of", "as investors"). They refuse intensity words ("plunged", "soared") in a sentence that carries no figure. They refuse a "held" or "broke" that disagrees with the level list. The policy words *hike*, *cut* and *hold* are reserved for the FOMC decision and the policy-rate path. A book-against-benchmark figure must say "excess" or "relative to". A probability may appear only as a ledgered base rate or as a prediction market's own price.

**The series binding** (since Draft 2). A figure is bound to the series named nearest it in its sentence, the one named before it winning. The bound series' row must hold that figure under a field whose unit agrees. A true number under the wrong name now fails: "5.52% is bound to XLK but belongs to QQQ". So does a z-score read as a share: "1.6 is its four-week z, not a share of open interest".

**The flag-word audit.** *Pinned*, *held*, *amplified* and *dampened* may describe a session only where that session's scorecard flag is set. *Held* counts only beside a dealer level. The close has no session flags, so there it withholds all four. "Gapped through the flip" is a descriptive flag the Weekly computes; it is not one of the audited words.

**The time-word audit.** A sentence about the book's performance that says "week" needs the week's window in the book's data.

**Signed zeros.** No "−0" in prose or in a table; it prints "0" or "unch".

**The resolved contract.** A prediction-market contract past its decision date, or past a published release month, prints "resolved: Yes" or "resolved: No", or drops when the market gives no outcome.

**The filler rule** refuses a paragraph that names series without saying anything about them. It exempts code-written lines that end on their own "descriptive; unvalidated" tag, and a Takeaway listing series whose paragraph's other sentences carry the figures. It never exempts a model's paragraph.

**No internal names.** No file path, branch name, exception or symbol string may reach a reader's edition. This is held by a gate on the rendered Weekly and a renderer that rewrites such strings, not by a runtime audit of the prose.

**The plain-language rule** gives every contradiction pair, story, exception kind, state word and sector a set of plain words, declared in one file. The prose may describe these things only in those words, and no internal identifier may reach a rendered edition.

The Monthly adds its own list of banned internal terms and refuses bullet-list fragments, and every report refuses markdown it cannot render.

| Audit | It refuses | Added after |
|---|---|---|
| Numeral | A number not in the payload, at its written precision | The first audited close |
| Type | A unit that contradicts the figure's kind | "Thirteen-day-old" from a row count |
| Ordinal | A malformed or truncated ordinal | "51st" for 51.7 |
| Signed | An unsigned negative move | "Gold fell 6.75%" |
| Scaled display | A figure rescaled by the model | Rescaled liquidity figures |
| Label | A level's number under another level's name | Max pain called the put wall |
| Tape rules | Motives, intensity without a figure, policy words, ids, wrong held/broke, unledgered odds | The first stacked closes |
| Plain language | An internal name or id in a rendered edition | The first stacked Weekly |
| Series binding | A true figure bound to the wrong series, or a z read as a share | Two Weekly drafts of 18 October |
| Flag words | Pinned, held, amplified or dampened without the session's flag | The dealer block |
| Time words, signed zeros, resolved contracts | A week the book's data lacks; "−0"; a resolved contract printed as live | Dry run 7 of the Weekly |

### 5.3 Withhold with a reason, and the one revision

A paragraph that fails is never rewritten by code and never "fixed" quietly. It is **withheld**, and the reader sees a short note saying which audit failed and on which figure. The tables and items of a section print even when its prose is withheld, so the reader loses the commentary, not the facts. An outage reads differently from a refusal: "model call failed" is never confused with "audit failed". The rejected text is kept out of the edition so that it cannot be published by accident.

A section the audit withholds gets **one revision**, in the stacked sections, the Weekly's précis, the close's paragraph, the anchor's, the two secondary notes and the Monthly's storyline fallback. The model is told three things:
- the rule the draft broke, in the rule's own words;
- the failing span: the sentence holding each refused figure or quoted fragment, or "the draft as a whole" when the fault is its length or shape;
- the draft itself, with the instruction to revise exactly that span and change nothing else.

If the revision fails, the section is withheld, with both reasons kept. Only an audit's refusal is revised. A fault is not: a failed API call, a malformed payload, a prompt past its guard or a reply that ran away. The voices block makes one attempt only.

**Length is no longer an audit.** Since the ruling of 24 October that budgets are targets, the paragraph guard cuts nothing: a long reply is marked over its target and prints whole. What remains is a runaway guard, a character ceiling well above any honest paragraph, which withholds a reply that has plainly run away rather than one that is merely long. The figure cap per paragraph and the withholding of a repeated sentence stand. The audits of §5.2 are unchanged since Draft 3.

### 5.4 No stored source, not printed

A view attributed to a named person or institution may print only if the system holds a stored row for it with a URL, a publication date, the moment it was retrieved and a source tier. The rule is enforced when a voice is written, not when it is printed: a row missing any of the four is refused, and stored voices cannot be edited or deleted. A voice whose extracted view fails the style or policy rules still prints its name, source and status, with the view itself withheld and the reason given.

### 5.5 Attributions, not causes

Financial prose's oldest habit is the after-the-fact cause: stocks fell *on fears of*, yields rose *as investors*. The reports do not do this. A press outlet's explanation of a move is that outlet's attribution, and the prose must say so: "CNBC attributed the fall to …", never the cause stated as fact. The system names a cause of its own only when a stored event coincides, and then only as coincidence: "on the day of the CPI release". Co-movement is reported; motive is not. The same discipline applies to the overnight block, where a move is assigned to a time window (Tokyo hours, European hours) on the stated understanding that a window is not a cause.

---

## Part VI — The Scans

### 6.1 What a scan is

A scan is research the system does on a schedule, reading sources outside the store and comparing them with what the system already holds. Every scan ends in the same place: a file of findings and a short summary, from which the operator rules in chat on what, if anything, to adopt. Adopted items become a change-order batch with numbered entries. No scan has decision rights. A third party's conclusion never inherits rights because a scan found it. Rights come only from a gate the system's own evidence has passed. The principle is part of the organising ruling: research proposes and never promotes.

### 6.2 The daily voices and news scan

The voices register is live. The Weekly prints each voice with a status, a source and a horizon, and lists the sources the scan could not read, each with its reason.

Each weekday morning, before the overnight fetch, a scan reads a declared list of public sources in priority order: officials first (central banks, finance ministries), then the published views of large asset managers, then news. It obeys each site's robots.txt, re-read on every run. It identifies itself honestly and does not run at all without a contact address configured. It reads only public pages: no paywalls, no email, no personal sources.

For each new item, the scan makes one model call, under a daily cap, to extract who said it, on which declared subject, in which direction (bullish, bearish or neutral) and over what horizon, with a short quote. The article itself is held in memory only and never stored. A source the scan cannot read is recorded as unreachable with its reason, and the reports print "unreachable" for it rather than presenting its last view as current.

**Status is computed, never declared.** Comparing each voice's new entry with its earlier ones gives one of four statuses. NEW means no earlier entry from this voice. REITERATED means the same subject and the same direction. INFLECTED means the same subject and a different direction. SILENT means an entry in the prior window and none in this one, which becomes UNREACHABLE when the source itself could not be read. The model supplies a direction; code decides what changed.

**The register names the outlet.** A source entry names the firm, the publication or the feed, never a person, under a standing ruling of 24 October; a view from one person's newsletter is entered as its outlet. The rule governs the declared source list and is applied by the session that adds a source; it is not a check in code.

The scan also feeds the **four stories** the system tracks: that AI capital spending keeps growing, that deficits drive long-term rates, that the yen carry trade unwinds, and the midterm-year pattern. Each story has declared evidence that counts for or against it (earnings, inflation surprises, currency and bond moves, headlines matched by declared patterns) and a declared outcome against which it is eventually graded. Evidence rows are written directly. A story's state (emerging, consensus, contested, fading) moves only by declared rules, and a new story the model proposes waits behind the operator's confirmation.

### 6.3 The signal intake and its register

Any proposal to add a signal, from any scan or any reading, enters through one intake template with six fields: where it would live, its mechanism, its data, the rights requested, how it would be validated, and its disposition. Every proposal gets a numbered entry in the signal-triage register (SR-1, SR-2, …), and numbers are never reused. The rights a signal may request run from none, through "base rate only" and a narrow flag, up to a confidence modifier or a composite input. Everything enters at the lowest class: nothing from the intake can block a decision, produce a packet, enter a composite or change a theme until its gate is passed.

Since Draft 2 the register has grown from Batch 5 to Batch 15: items 16 to 78 are filed (Batch 10 was never used), and most of their first tranches are built:
- the index cluster and the allocation block;
- the labour, CPI, PPI and GDP lenses and the surprise index;
- the ES block;
- the digital-assets items;
- the volatility event;
- the opening setup's amendments, the bank-stress panel, relative options volume, the capex chain, the cross-house capital-market assumptions, the fragility and gold-event panels, and the cyber and protocol lines.

Items 16 to 78 carry their batch numbers as ids; their register numbers are assigned at a Doctrine sitting, not at filing. What is built is report-only: nothing from these batches has been promoted to a right. The calibration ledgers that would grant rights are in §9.9; on 19 October the operator accepted their first gate statuses as drafted, and none passed into a right.

A **Monthly signal scan** on the 25th feeds this register: a chat-side task writes a scan file of candidates for the operator to rule on. Its time, output and the decision that created it are in the scheduled-tasks record; its prompt is outside the repository. Its first run is due on 25 October 2026.

### 6.4 The quarterly read of the Guide to the Markets

Once a quarter, shortly after J.P. Morgan publishes its Guide to the Markets, a scheduled task reads the new edition and compares it with a reference table kept from the previous read. It records the deltas, notes what does not fit the system's own description of the market, writes any candidates in the intake template, adds a voices entry for the Guide, and refreshes the reference table. A short chat summary follows, then rulings, then that month's change-order batch. The Guide's recommendations never print. What may be adopted from it is narrow: a base-rate row, a modifier, a sourced figure or a voices entry. The task's prompt lives outside the repository.

The read of 6 October produced **the GTM batch**: eleven adopted items. Each is computed from the system's own data where that data exists. Where it does not, the item is stored as a sourced figure with its slide reference.

### 6.5 The crypto mechanism scan, the PRL read, the X digest and the consensus-drift scan

**The crypto mechanism scan** is now in the repository. It runs on Saturdays inside the crypto basket's run and draws on two sources: a news query group and DefiLlama's recently added list. It then:
1. removes duplicates against the Security Master and the register;
2. applies a rule-based pre-filter;
3. makes one gated model call;
4. writes drafts only, to **the mechanism watch**.

Promoting a watch candidate or rejecting one is the operator's write, denied to every session with its verb whole (§7.8). The read-only review stays open. The chat-side Saturday task it replaces is slated to retire once the watch has run cleanly for several weeks.

**The PRL read** follows one digital-asset thesis by computed figures:
- the token's supply from its emission formula;
- the overhang, against DefiLlama's market cap and supply;
- emission against volume, from Yahoo's price and volume;
- an idle-GPU flag;
- a thesis status with its trace.

The supply gap is ESTIMATED until the chain's explorer can be read; that explorer is a listed gap until an endpoint within its robots.txt and terms is found. Venue concentration is not tracked. CoinGecko, the original source, is retired under its terms.

**The X digest** is a chat-side pilot since 17 October, built as three files on Drive:
- a daily digest file, written by a scheduled task from a seed list of handles and topics;
- an attention ledger and a voices ledger, kept by a triage task that reads the digest each morning.

The box's nightly sweep copies all three into its inbox, and the digital-assets addendum reads them; nothing else in the repository does. The seed list is the chat-side task's own prompt, not a file in the repository, and accounts that publish only on X are added to it in one batch a month (a standing ruling of 24 October). The digest's rights are attention only: an X post never earns measurement rights by its volume, and candidates go to the intake for a ruling. The xAI path on the box is a decision, not a build.

**The MSTR/MSCI event watch** runs on weekdays from 2 to 30 November, with a post-effective read on 1 December. It records the index review's notices to a Drive file and sends a short push; no reader in the repository reads that file, and the addendum reads Strategy's mNAV from the store.

A **consensus-drift scan** every second month follows how expert opinion on the long-horizon AI risks is moving, under a reserved register entry with no rights yet. Its prompt is outside the repository, and Appendix A marks it "schedule per the scheduled task".

### 6.6 The reading shelf

A twice-monthly **publication watch**, not named in the commissioning brief, checks a declared shelf of publications (chartbooks, central-bank stability reviews, plumbing and positioning research) for new editions. It reads them to a declared depth and writes a scan file with summaries, candidates and voices entries. It feeds the Monthly's Reading chapter (§4.6): every shelf edition published in the month, linked, with its stored summary and nothing of the system's own stance. Since 24 October it also checks the capital-market-assumption publications of six houses. Each new edition is committed as a scan file of a fixed shape (an edition line, the read date and source, and a reference table of the houses' assumptions with a URL per row), which the scans ingest stores as sourced figures for the Monthly's cross-house table. No such edition was stored at the time of writing, so each house prints "no edition stored". It has no decision rights either. The other scans' reference tables reach the Monthly by a second route, the scans ingest, which stores each table's figures with their sources for Slow layers to print.

| Scan | Cadence | Reads | May propose | In the repo |
|---|---|---|---|---|
| Voices and news | Weekday mornings | Declared public sources | Voices rows; story evidence; new stories (behind confirmation) | Yes |
| Signal intake | As proposals arrive | Any source | SR entries in the register | Template and register |
| Guide to the Markets | Quarterly | The Guide | Base-rate rows, modifiers, sourced figures, voices | Change order and scan file; prompt outside |
| Crypto mechanisms | Saturdays | Declared mechanism sources | Watch-level notes | Change order; prompt outside |
| Consensus drift | Every second month | Expert-opinion sources | Reserved entry, no rights | Change order; prompt outside |
| Reading shelf | Twice monthly | The declared shelf | Candidates, voices, Reading chapter entries | Brief and watchlist |
| Mechanism scan | Saturdays | News queries, DefiLlama | Mechanism-watch drafts (the operator promotes) | Yes |
| X digest | Daily (pilot) | A seed list of X handles | Attention and voices ledger rows; candidates for a ruling | Order, the sweep and the addendum's reader; prompt outside |
| Monthly signal scan | The 25th | Declared sources | Candidates for the register, for a ruling | Scheduled-tasks record; prompt outside |

### 6.7 chester-meme

chester-meme is a separate, private repository with its own user-mode units on the same box. It scans memecoin names twice a day and writes decision packets, to the schema of 11 October, into a drop directory.

The interface between the two repositories is files only:
- chester-meme reads chester-reports' Security Master through the one-way export (§2.5), which carries the restricted names;
- chester-reports reads chester-meme's drop directory and never writes into chester-meme.

**The ingest** runs at 21:15, before the evening note reads tonight's drafts, and again inside the 06:45 overnight pass, so a packet written after the evening scan is in before the anchor. In order, it:
1. checks the manifest's schema version and checksum;
2. treats a packet already seen as a no-op;
3. refuses a restricted packet, and a Brookfield-related name a second time, by a database trigger;
4. logs a packet that fails the schema and never repairs it;
5. writes one Book D draft per packet, keyed by its packet id.

A draft is never a decision. The close and the anchor print one line counting the drafts, and confirming or rejecting each is the operator's.

---

## Part VII — The Register and the Books

### 7.1 A decision, not a trade

The register's unit is a *decision*, not a trade. A decision names an instrument, a direction (long, short, flat or hedge), a thesis, the kind of edge claimed, a horizon, a size and, always, an invalidation: the condition under which the thesis is wrong. It carries a status (draft, active, closed or declined), the operator's action (take, decline or modify) and, separately, the thesis's own health (intact, strained or invalidated). These are different questions. A decision can be active and strained at the same time, and the register keeps both answers.

A decision that the operator declines, or abstains from, is still a decision and is still recorded. An abstention is a position, and the grading in Part IX measures it like any other.

### 7.2 The Decision Packet and supersession

Each decision is written with a **Decision Packet**: a record, built at the moment of writing rather than reconstructed later, of everything the decision was made with. It holds the run that produced the report, the cutoff time of the data, the code version, a fingerprint of the data used, the versions of the metric and source registries and, where a broker preview was run, the expected costs. The packet is **immutable**: a database trigger refuses any attempt to edit or delete it, and the same is true of the record of rule breaks.

Decisions are never edited. A change, whether a new status, a close or a correction, is made by **supersession**: a new decision is written, and the old one gains a single pointer to its successor, the one change it ever accepts. A superseded decision is frozen. The register refuses to supersede a decision that has already been superseded, because a chain with two live heads is not a chain. The reason is the grading trail. If decisions could be edited, a decision could be made to look right after the fact, and the record the system is graded against would be worthless.

### 7.3 The gate at entry

When the operator records a decision, a sequence of checks runs before anything is written. Each was added because a weaker form failed.

**Currency first.** A foreign listing's currency is read from its symbol, and a mismatch between the listing and the declared currency is refused unless explicitly overridden. This check runs even in a dry run, so it is seen before it matters.

**The restricted list.** No recommendation touching a Brookfield-related security may be written. The check runs twice: once in code, before any other validation, which logs the attempt, and once as a database trigger that refuses the row from any writer at all. It is a standing invariant of the system, not a preference.

**The expression currency.** A non-dollar listing must declare its currency exposure. One rule judges every write against the listing's own currency, a close included. An empty currency is stored as unknown, never as dollars (§7.7).

**Signal freshness.** Each signal a decision cites is checked against its own declared half-life. If any is stale or missing, the decision is still recorded, because an abstention is a decision, but held at draft with the reason stated, and it cannot be promoted in place. The report may still publish; the recommendation may not. This is the state called DECISION_BLOCKED.

**The expression check** compares the chosen instrument with the thesis. On a draft it warns; on an active decision it binds.

**The packet rule.** An active decision must name its book, at least one falsifier, an invalidation and a counter-thesis: the cheapest way the conclusion could be wrong. This is the first version of the Red Team (Part IX), enforced at write time.

**The order gate.** Last, the system reads the cross-book view of the open decisions and asks whether the new one would worsen a declared limit: net beta, sector concentration, interest-rate duration or volatility exposure. The outcome is deterministic. It approves if no limit is worsened. It delays if an input is missing. It asks for a restructure if the volatility limit is worsened. It resizes if a useful fraction of the request fits. It asks for a hedge if net beta is worsened. It rejects if sector or duration is worsened and no useful size fits. Anything short of approval holds the decision at draft unless the operator records an override with a reason, and the override is kept.

**The stamps at entry.** The gate's record of each decision carries the regime it was taken under, read from the stored object and never recomputed: the macro dial's state, the Doctrine regime with its band and cap, and the mapping's version; since Draft 3, the volatility and gamma dials' states with the session they were read from; and the volatile-day flag as the day's live edition printed it, with whether its gap had settled. The decision row itself carries its alignment, the packet's direction against the sign of the trend dimension, recorded once and carried through every supersession. A decision taken before a stamp existed reads "not stamped" in every cut, never a reconstructed value. A second alignment against the weekly per-horizon read is built on a later branch (Appendix E).

The limits are few and declared (Appendix A). Several of the Operating Doctrine's other numbers, namely the per-position risk tiers, the books' loss stops, the kill-switch ladder and the cap on total open risk across the shorter books, are measured and reported but not yet refused by the gate. The Doctrine states them as rules for the operator. The code enforces the four limits above.

### 7.4 The books

**The Book B scanner** draws its candidates from every stored daily price series with enough history, less the index levels it excludes, so a symbol joins its universe by being stored, the capex chain's proxies included (ruled 24 October); its output is graded paper.

The Operating Doctrine defines four books by horizon, and the register knows exactly those four. **Book A** (Allocation) holds the long-horizon exposure, managed inside a band set by the regime (Part III). **Book B** (Swing) holds positions of weeks. **Book C** (Tactical) holds positions of days. **Book D** (Opportunistic) holds rare, small, pre-defined opportunities. Each has its own risk per position and its own loss limits, set by the Doctrine.

**Book D's drafts from chester-meme** (§6.7) enter as drafts keyed by their packet id and wait for the operator's confirmation. A packet the weekly attention budget deferred is recorded as an abstention with the reason `attention_budget`, and it is graded like any other abstention (§9.7).

Beside them sits **Book Z**, which is not a book in the register but a set of three benchmark ledgers: **cash** (Treasury bills accruing interest, the "no trade" book), **SPY** held without trading, and a **60/40** of SPY and an aggregate bond fund rebalanced monthly. Each starts at 100 on a fixed date, is marked once per session and never recomputed. Book Z answers the question every book must face: would doing nothing, or doing the obvious thing, have done better? A figure comparing a book with Book Z must say "excess" or "relative to"; it may not present a book's return as if it stood alone.

| Book | Horizon | What it holds | How it is bounded |
|---|---|---|---|
| A — Allocation | Months | Strategic exposure | A regime band for net beta; Transition by rule |
| B — Swing | Weeks | Positions on a thesis | Per-position risk; a monthly stop |
| C — Tactical | Days | Short positions on a setup | Per-position risk; daily, weekly and monthly stops |
| D — Opportunistic | Event-bound | Rare, pre-defined opportunities | A small cap per position and in total |
| Z — Benchmarks | Every session | Cash, SPY, 60/40 | Not traded; marked and never revised |

### 7.5 Rule breaks

A rule break is a recorded departure from the system's rules, found by code. Some come from reconciling what the broker shows against the register: an execution with no registered decision, an execution against a decision not accepted, the wrong side, more than the registered size, the wrong instrument type, the wrong currency. Others come from the Doctrine's position rules: Book A below its regime floor, a Book B position held long enough to have become something else, a position past its time stop. Each break is written once, with a key that makes a second sighting of the same break a no-op, and the close and the Weekly count them. The Doctrine's target for this count is zero.

### 7.6 Reconciliation against Portfolio Truth

Nothing in the system places an order. The broker connection is read-only, enforced by the broker's own server setting rather than by a client flag, and the code contains no order-placing path at all. A validator checks that absence on every run. Because orders are placed by hand, the check that matters happens after the fact: **reconciliation**. Through the trading day, the system reads the account (the *Portfolio Truth*, a complete snapshot of holdings each time) and requires every fill to match an accepted decision in instrument, side, size and type. A fill that does not match becomes a rule break. Where no snapshot precedes a chain's first fill, the side and size are stated as not judged rather than guessed.

### 7.7 The heat view, P&L and currency

The **heat view** sums the open decisions across all four books on four measures: beta-adjusted exposure, sector concentration by look-through weights, interest-rate duration in dollars per point, and volatility exposure. Its purpose is to catch the case where four separate decisions in four books are really one trade. It feeds the order gate and prints in the close and the Weekly. The name has two meanings in the library, so it is worth stating precisely: the Doctrine's *heat* is total open risk to invalidation across the shorter books. That figure is a rule for the operator, while the heat view is a factor view and does not compute it.

**Realised P&L** is computed from stored fields only: the exit price, the average cost from the last Portfolio Truth before the exit, the quantity and, for a foreign listing, the exchange rate at the exit. It is never typed by hand, and a missing input leaves the P&L absent rather than estimated. Exchange rates come from stored series, never from an assumed parity.

Two incidents shaped the **currency rules**, and both are in Appendix B. The first (INC-6) was a position in SPY listed in Mexico, held in pesos. Its loss came mostly from the peso and from the listing's basis, and only slightly from SPY itself. Its lesson was written into the rules: *a foreign listing is a currency position*. Every non-dollar listing must now declare its currency exposure, and an activation that names no currency on either side is refused. The second (INC-8) was a fallback in the code that filled an empty currency with "USD", which recorded a peso close as dollars. Its lesson: *a fallback that invents a value is worse than an empty field*. An unknown currency is now stored as unknown, one rule judges every write, and corrections are new rows.

### 7.8 The operator's writes

Some commands write the record the system is graded against, so they stay the operator's. The repository's permission file denies each of them to every unattended session, with the verb whole:
- recording a decision or changing its status;
- rejecting a chester-meme draft;
- importing into the register, or retiring the laptop's old register;
- confirming or rejecting a proposed narrative;
- promoting or rejecting a mechanism-watch candidate (added 19 October);
- retiring an Alpha Lab engine by ruling;
- lifting the lab's drawdown halt.

A session prints such a command for the operator to run; it never runs it. Schema changes to the register follow the same rule: a migration is written with a dry run and applied by the operator from the box sheet. The reason is the grading trail of §7.2: a grader that could write the decisions it grades would be marking its own homework.

---

## Part VIII — The Intraday Layer

### 8.1 Tactics, not a book

The question of day trading was ruled on, and the ruling is narrow. The base rate for individual day traders is close to one-sided. In large studies only a very small fraction are reliably profitable after costs, and the system does not assume it is the exception. The intraday layer is therefore **not a fifth book**. It is an expression-and-timing layer for Books B and C, used to time the entry and exit of decisions those books have already approved. Most of the familiar intraday patterns (opening ranges, VWAP plays, most gap trades) enter only as execution tactics in that role.

### 8.2 At most two paper engines

Beside the tactics layer, the ruling allows **at most two paper engines**: systems that generate their own intraday trades on paper to test a mechanism. The first, when built, is a dealer-positioning engine for zero-day options, the mechanism the Dealer's Hand derives. The second is a scheduled-event engine, after an offline study of how markets react to surprises.

Before an engine's first trade it must register four things: a paragraph stating its mechanism, the unconditional base rate set beside the edge it claims, a target sample size and a kill criterion. The kill criterion is fixed by ruling and not chosen per engine. An engine is retired when, after at least forty graded paper trades, its expectancy after modelled costs is zero or worse, or its Brier score is worse than the unconditional base rate's. It is never resized before that sample exists.

An engine's trades are **ledger entries graded against stored bars**. They are never orders and never Decision Packets. They carry the engine's identity, they do not draw on the operator's attention budget, and the operator reviews the engine, not its individual trades. The dealer engine carries further conditions: a base rate from a minimum run of stored close verdicts, and defined-risk structures only.

### 8.3 The state vector

The state vector is built. Eighteen numbers are stored per capture, at 09:45, 12:30 and 16:10. It is printed as one line in the close and one row per session in the Weekly. No engine reads it until the first engine is registered.

The engines and the tactics layer will read this one intraday **state vector**, built from measurable variables only: the opening gap and how much of it has filled; the opening range and whether it has broken; the price against VWAP; breadth, measured on the sector funds; realized against implied volatility; the VIX term structure; dealer positioning; how near the next scheduled event is; volume against its twenty-session average; and whether the session agrees with the trend dimension. It carries no narrative labels, and no engine reads it until an engine is registered.

### 8.4 What is built

**Built:**
- the intraday captures at 09:45 and 12:30 (the operator enables their timers);
- the state vector;
- the 12:30 alert-only slot (§4.7);
- the dealer block's horizon matrix in the close and the Weekly;
- the vendor writer's labelled cross-check at 16:25;
- the order gate, the heat view and reconciliation, which the layer will use.

**Not built:** the conversion of the dealer levels to the e-mini future is written and gated but not wired into a report (the ES block says it waits). No engine of this layer is registered. The register's engine identities still hold only the reports and the operator. The Doctrine's two paper engines are registered later, once twenty scorecard sessions exist (EL-12). The Daily Cascade paper's description of intraday slots should be read as that plan, not as running reports.

### 8.5 The Alpha Lab is not this layer

The Alpha Lab is a separate paper research layer, and its engines are not the Doctrine's two paper engines.

**What it has:**
- its own database;
- **a hypothesis register** in which every hypothesis is registered, with a manifest, before its first test. The harness refuses a hypothesis edited or registered after its run, and keeps failures so their duplicates are screened out;
- a point-in-time harness, walk-forward and cost frameworks, and a deflated-Sharpe gate;
- an allocator and a governor, which halts the lab at a declared drawdown that only the operator can lift;
- a paper book and ledger of its own.

**What reads it, and what it reads.** It opens the observation store read-only, imports no order, broker or network path, and is held to that by gates. Three reports read it, each through one hook: the Weekly's line, the close's line and the Monthly's Lab report. Its results reach a sitting only as evidence the operator tables.

**Its loops**, on their own timers:
- a nightly loop that fills, marks, grades, governs and learns;
- a daily proposer that makes the one model call;
- a weekly loop that walks forward, re-fits within bounds, rebalances, and writes the agenda and the verdicts. The verdicts go to Drive's `chester-lab-outbox`.

A quarterly meta-loop runs inside the weekly one. It measures whether the quarter's loop changes earned their keep, and tightens the re-fit bounds when they did not.

**Its engines:**
- engine 1, the volatility risk premium (a data gap);
- engine 2, the trend engines;
- engine 3, prediction markets against futures;
- engine 4, the scheduled events, whose base rates print "awaiting" where an input is not stored;
- engine 5, crypto carry, which runs nothing until its ninety-two-week window is met;
- engine 6, the reversion of extremes, which prints "awaiting (n = k of 30)" until its formation sample exists;
- engine 7, the intraday dealer regimes: buckets of symbol, the 09:45 gamma regime and the sign of the opening move, read from the stored captures after the close. It is a research engine that queues no signal, and registering it is the operator's command on the box;
- promoted rules from the grammar.

**The grammar search** enumerates candidate rules from a declared grammar, under a cap on candidates and on time per step, as the nightly loop's last step; a new search starts only in a month's first week. A candidate it finds is registered like any other hypothesis before its test. Since Draft 3 all three are built. Engine 7 is not the intraday layer's dealer engine: it is evidence the lab may report, and the layer's engines stay unregistered (§8.4).

---

## Part IX — How the System Learns

### 9.1 The probability ledger

Every probability the system states is written to the **probability ledger** before its outcome is known, with its resolution criterion declared at the same moment. When the outcome arrives, code resolves the entry and scores it with the **Brier score**: the square of the difference between the probability and the outcome (1 if it happened, 0 if not), averaged over many forecasts. Lower is better. A forecaster who always says 50% scores 0.25, so 0.25 is the coin, and any source above it is doing worse than a coin. The Weekly prints each forecasting source's running Brier score beside the coin, with its sample size. A set of scenario weights must sum to one, and an incoherent set is reported as incoherent rather than quietly normalised.

### 9.2 Base rates as the baseline

The first forecasts the reports make are deliberately humble: **base-rate outlooks**. Each is the empirical frequency of a declared rule over SPY's stored history, such as how often the week's low has held, or how often SPY stays above its 20-day average for the next session, with its sample size, clamped short of certainty. These are written to the ledger before printing and resolved from the same stored prices. They are the baseline every richer forecast must beat. A view that cannot outscore the base rate has not earned a place in the reports, and the same standard appears in the kill criterion of every intraday engine. The tables of the Base Rates paper are stored the same way, as denominators that can never act as signals.

### 9.3 Graded calls and the grader

The **grader** grades every recorded decision from stored prices only: taken, declined and draft alike. Grading the declined and draft decisions is what turns "doing nothing" into something measurable. It shows what the operator's filter cost and what it saved. Missed opportunities are graded only against setups that were flagged and declined, never against hindsight. Evaluation stays in code: no model writes counterfactual attribution.

### 9.4 The dealer scorecard

Each session the close stores the dealer row: the evening's positioning and levels, SPY's own implied volatility and put/call ratio, and the session's actual range. From these rows the Weekly computes flags per session. *Pinned* means the close finished very near max pain. *Held* means a wall contained the session's extreme and the close. *Amplified* means the flip was crossed and the realized range far exceeded the implied. A check flag marks SPY's own implied volatility diverging from the VIX. A flag is absent when an input is missing; it is never guessed. The prose may say "pinned", "held" or "amplified" about a session only where that session's flag says so. Over a month, these rows become the Monthly's dealer retrospective, which prints "insufficient sessions" until there are enough.

**The scorecard is pre-registered** in a ledger dated 17 October 2026 that is never edited:
- five hypotheses;
- a formation sample of 120 eligible sessions, then a test sample of 120;
- Benjamini–Hochberg across the family;
- Wilson intervals and printing floors;
- a demotion rule.

A flag's rate prints only above its floor, is no decision below 120 eligible sessions, and is demoted when its interval keeps including the base rate (Appendix A).

### 9.5 The change ladder

Rules change only through a ladder of five tiers, from the most local to the most fundamental: tactical, regime, relationship, structural, and durable principle. Each step up requires evidence: a declared minimum of graded cases (twenty graded outcomes within the regime at the second tier), and no more than one tier per review cadence, the cadence of the tier being entered. The Operating Doctrine states the ladder as ruled on 4 October, with the attention budget and the intraday rung beside it. The ladder exists to stop the most common failure of a learning system: one vivid outcome changing a deep rule.

### 9.6 The Red Team

The **Red Team's** objective is to find the cheapest way a conclusion could be wrong, at a stated cost in review time. Its first version is the packet rule in Part VII: no active decision without a falsifier, an invalidation and a counter-thesis, enforced at write time. A second version, a blinded review pass, is gated on the cost-measurement stage of the broker gates and on a minimum number of graded packets.

### 9.7 The attention budget

The operator's attention is the budget everything else spends, and it is measured. The ruled budget is **seven packets approved a week and one sitting of at most two hours a week**. A packet deferred for want of attention is recorded as an abstention with that reason, so the cost of the budget is itself graded. The Weekly prints **three counts**: packets against seven, sitting hours against two, and rulings taken in chat, which are measured but not capped until a sitting sets a cap from a month's data. A log of every sitting and ruling, with the minutes it took, feeds them. The attention budget is a rule, not a target: the reading budgets of Part X became targets on 24 October, and the attention budget did not.

### 9.8 Incidents and the sittings where values are ratified

An **incident** is a failure that reached production or nearly did: a unit that silently did not run, a prompt silently truncated, a currency invented by a fallback. Each is logged with what happened, the fix, the gate that now holds the fix, and a one-line lesson. The lessons that bear on the operator's rules are carried into the Operating Doctrine's dated appendix, so the Doctrine records not only what the rules are but what taught them.

The Monthly and the Quarterly open their system read on **the system-metrics block**:
- uptime, from the heartbeat log;
- feed completeness, from the roster;
- incidents, from the incident log;
- model calls and tokens, never dollars, from the meter every model call passes through;
- withheld drafts, from their log.

Each figure prints as recorded, or "not recorded".

Values, meaning thresholds, mappings, budgets and limits, are ratified at sittings, never between them. The **Doctrine monthly** is the regular sitting: it takes a numbered agenda, rules item by item, and records minutes with the time of each ruling. The **Audits** are the larger, rarer sittings that review the whole system, set its roadmap and rule on the questions the monthly sitting defers. Between sittings, the configuration stands as last ratified, and anything marked "proposed" in it waits for the next one.

| Instrument | What it measures | Baseline it must beat |
|---|---|---|
| Probability ledger | Every stated probability, scored by Brier | The coin, 0.25 |
| Base-rate outlooks | Simple empirical frequencies | They are the baseline |
| Grader | Every decision: taken, declined, draft | Book Z and the declined alternative |
| Dealer scorecard | Whether dealer levels behaved as positioned | The session's implied range |
| Change ladder | Whether a rule may move, and how far | A minimum graded N per tier |
| Red Team | The cheapest way a decision is wrong | A falsifier stated in advance |
| Attention budget | What the operator's time was spent on | Seven packets, two hours |
| Incident log | Failures, fixes and lessons | Zero repeats |
| Calibration ledgers | Whether a proposed signal earns a right | Its pass rule, registered before the run |
| State calibration | How often each dial's state gives way to each other, at each book's horizon | The unconditional count; nothing prints before thirty independent starts |

### 9.9 Calibration ledgers

A signal earns a right only through **a calibration ledger**: a dated file that gives:
- its as-of date, window and sample size;
- the statistic, and the pass rule as the order states it;
- a verdict (PASS, FAIL or INSUFFICIENT);
- the right the verdict would grant, stated and not granted.

A CSV of its episodes sits beside it. **The pass rule is pre-registered.** It is the order's where the order states one; otherwise the first edition writes it, and every later run must apply it unchanged.

The first editions run on the laptop from public sources, are labelled so, and never open the store. The box's re-runs write new dated files that supersede them, and none is ever edited.

A verdict reaches the register only as a draft under rule 31, and no right changes until the operator accepts it. On 19 October the operator accepted the gate statuses of the ST-7 and ST-8 ledgers as drafted, the register statuses unchanged, and put the false-bottom audit's proposed Doctrine rule on the agenda of the 7–8 November sitting.

| Study | Verdict | What a PASS would have granted |
|---|---|---|
| SR-1 growth against value | PASS | The style panel's modifier, on the box re-run's confirmation |
| SR-2 yen carry | FAIL | The unwind flag's thresholds; they stay session-set |
| SR-4 the yuan's fixing, SR-5 consumer credit, SR-12 bond allocation, SR-13 tech against defensives, SR-14 EM against DM | INSUFFICIENT | Each its modifier or flag |
| SR-15 cross-asset valuation, SR-21, SR-22, SR-23 (the rates studies) | FAIL | Each its modifier; SR-22 keeps a stress flag only |
| SR-8 false bottoms (ST-9's audit) | FAIL (one element discriminates) | A Doctrine rule, now only a proposal on the November agenda |
| Net liquidity against the S&P, MOVE against VIX | No gate in the order; base rates recorded | Nothing |
| The concentration and drawdown-gap ledgers | INSUFFICIENT on a three-year constituent history | Nothing |

**Since Draft 3.** The ledgers filed from 19 October, with what the operator has done with each:

| Study | Verdict | Status |
|---|---|---|
| The opening setup's positioning components (OS-6) | FAIL | Accepted as drafted, 19 Oct |
| The open-interest builds against their outcome (OS-9) | INSUFFICIENT, n 0 | Accepted as drafted, 19 Oct |
| The hiking-cycle table; SR-20; SR-24 | No gate; base rates recorded | Accepted as drafted, 19 Oct |
| The crypto alerts (S-2, S-3); the release-day first hour and after-hours earnings (SN-1, SN-2) | FAIL | Accepted as drafted, 20 Oct |
| The wealth effect's December test (ST-R6.66c) | FAIL | Accepted as drafted, 24 Oct |
| The speed flag's attribution (ST-R6.65a) | INSUFFICIENT | Accepted as drafted, 24 Oct |
| The fragility panel's air pockets (ST-R6.71d) | FAIL | Accepted as drafted, 24 Oct |
| The squeeze-risk flag (ST-R6.74b) | INSUFFICIENT, n 0 | Accepted as drafted, 24 Oct |
| The bank-stress classifier (ST-R6.59c) | FAIL | Pending, on the Doctrine #2 agenda |
| Relative options volume (OS-12c) | INSUFFICIENT, n 0 | Pending |
| The one-day 10-year move's attribution | INSUFFICIENT | Pending |

Further register lines with no gate in their order, and two with an insufficient sample, wait as drafts for the same sitting. Several studies are pre-registered and accruing, with no verdict yet: the bank-stress and relative-volume tests, the wealth effect, the air pockets, the speed attribution, the short extremes and the one-day move.

Nothing has been promoted.

### 9.10 The state object graded as a state

The calibration of §3.10 is the newest of the instruments. It asks a narrower question than the ledgers: not whether a signal earns a right, but how often the object's own description gives way to another, at each book's horizon. Its counts are read from stored objects only, its pass condition (thirty independent starts) is fixed before any count is read, and until a row meets it the reports print "uncalibrated". The dials' calibrated rows are scored in the probability ledger like any other forecast, so the object's description of the market is itself graded against the coin.

**What is still missing.** The Enterprise Layer's lessons register is specified and not built: its gate is the first Quarterly Structural with at least five lessons to file, and until then the lessons live in the Operating Doctrine's dated appendix (§9.8). A brief for the next version of the learning loop is drafted on a later branch for a ruling (Appendix E).
---

## Part X — Reading the Reports

### 10.1 Targets

Each cadence has a reading target and a word budget (Appendix A). Both are targets, not caps: the ruling of 24 October put depth before brevity, so nothing is cut or withheld for length, and an edition over its target prints one line at its foot saying how long it runs against the target. Only prose counts toward the words; tables and code-written lines do not, because they are the facts the prose serves. The chart caps still bind, and a firing trigger raises a report's cap by one. The model is never asked to summarise to fit. The two secondary notes are the exception: their word caps are hard, and a paragraph past one is withheld rather than trimmed. The Weekly and the Monthly print their estimated reading time in the header against their targets. The Monthly's count includes the stored summaries of its Reading chapter, which are outside the word budget but not outside the reader's time.

### 10.2 How to read a stacked report

Read the claim lines first. Ten bold sentences give the whole edition in under a minute. Then look for the diamonds. A ◆ marks what changed since the last edition of the same cadence, and an unchanged section has already collapsed to one line, so attention goes where something moved. Read What doesn't fit next, whatever the claim lines say, because it is the one section built to show where the system's own picture is under strain. Footnotes marked "Not yet tracked" are the honest edge of the system's knowledge. They do not need reading every day, but they are where the gaps are. A note saying a paragraph was withheld is a working audit, not a broken report. The figures in that section's table still stand.

The words in the reports have fixed meanings, listed in the glossary at the end of each stacked report. In the close, the state and contradiction tables sit just above it (§4.7). *Pending* means a reading has crossed its line but not for long enough to count. *Open* means a gap has been wide for at least two sessions. An *exception* is a gap open five sessions or more, or a reading at a five-year extreme. "Outside 10–90%" means a reading in the outer fifth of its history. A *base rate* is how often something has happened, with its sample size. *Brier* is the forecast score, where 0.25 is the coin.

### 10.3 A reading order for a busy week

When time is short, the system is designed to degrade gracefully. On a weekday, the close's claim lines and its What doesn't fit take two minutes; the morning anchor's What changed block takes one. On Sunday, start with the Weekly's précis. Then its "Changed since last Weekly" block, The read and The book take five minutes and cover the decisions that need attention. The digital-assets addendum comes last, as its own PDF. A 12:30 mail arrives only when a gate opened; it is one trigger line, and the close says what came of it. The Monthly's read, with its *month in one page*, and its book, with *where our read lands*, take ten. Everything else can wait for a quieter week, because the system's record is written to be read late. Every figure is dated, every forecast is in the ledger, and nothing a report said is lost by not being read on the day.

| If there is time for | Read |
|---|---|
| 1 minute, weekday | The anchor's What changed |
| 2 minutes, weekday | The close's claim lines and What doesn't fit |
| 1 minute, 09:50 or 21:30 | The open note or the evening note: one line on a quiet day |
| 5 minutes, Sunday | The Weekly's précis, Changed since last Weekly, The read, The book; the addendum last |
| 10 minutes, the 1st | The Monthly's read (the one page) and its book (where our read lands) |
| On a 12:30 mail | The alert's trigger line, then the close at 16:45 |
| A sitting | The Weekly whole; the ledger's Brier table; open rule breaks |

---

## Appendix A — Dated: Timers, Gates, Windows, Thresholds, Budgets, Sources, Charts (as of 24 October 2026)

*Everything in this appendix is as of 24 October 2026, read from the seventh stitched chain (`chain-7`, commit `62c19b41`) and the feed repair (`a61b-feed-repair`, commit `0d954d0f`) on the day of writing. The sources are the systemd units in `deploy/systemd/`, the deploy's timer list in `scripts/deploy_remote.sh`, the `Makefile`, `CLAUDE.md`, `config/reporting_stack.yaml`, `config/risk_limits.yaml`, `config/market_state.yaml`, `config/vol_event.yaml`, `config/data_quality.yaml`, `config/metric_lenses.yaml`, `config/publication_lags.yaml`, `config/flashalpha.yaml`, `config/digital_addendum.yaml`, `source_registry.yaml`, the dealer pre-registration ledger and the feed modules. Where the feed repair changes a value, the value after its merge is given and the change named. All times are U.S. Eastern. Whether each timer is enabled on the production box is not recorded in the repository; the box sheets list the ones the operator enables.*

**Timers the deploy enables.** The deploy and the box's self-deploy enable a declared list of fourteen timers and copy every other unit without enabling it.

| Unit | When | What it runs |
|---|---|---|
| Voices and news scan | Weekdays 06:15 | The voices scan, then the voice seeds |
| Overnight fetch | Weekdays 06:45 | Correction pass; Japan and China writers; events; the loggers; the ES and tape bars; the listings and the Security Master export; the meme ingest's second chance |
| Morning anchor | Weekdays 07:00 | The anchor |
| Heartbeat | Daily 08:30 | Health check; verdict and exit code |
| Broker sync | Weekdays every 30 minutes, 09:00–17:30 | Portfolio Truth; reconciliation (its install section is held back in the unit file) |
| Closing-auction sampler | Weekdays 15:49 | Auction imbalance |
| End-of-day pull | Weekdays 16:10 | Every feed but the loggers; option chains and exposures; the derived features; the volume profile; the one-day 10-year ledger's resolution |
| Daily close | Weekdays 16:45 | The object; the calibration rows; the close |
| Crypto basket | Daily 17:25 | The crypto basket and data layer; GDELT, the degree days and the model-release watch; on Saturdays the cyber lists; each day the protocol counts |
| Backup | Daily 02:30 | The encrypted sweep |
| Saturday prices | Saturdays 06:00 | The week's price corrections |
| Weekly | Sundays 05:00 | The Weekly and the digital-assets addendum |
| Monthly | The 1st, 07:30 | The scans ingest; the Monthly |
| Self-deploy | Every 30 minutes inside the windows | Unit copy, daemon reload, the declared timers, the drift check; never a restart |

**Timers the operator enables** (copied by the deploy, enabled by hand; the box sheets give the steps).

| Unit | When | What it runs |
|---|---|---|
| Dealer captures | Weekdays 09:45 and 12:30 | Intraday chain captures; the 12:30 alert slot |
| Open note | Weekdays 09:50 | The open note, after its own fetch |
| Vendor writer | Weekdays 16:25 | The FlashAlpha cross-check |
| Vendor chains | Weekdays 16:31 | SPX and SPCX from Massive, after its 15-minute delay |
| Alpha Lab, nightly | Weekdays 17:40 | Fill, mark, grade, govern, learn; the grammar search last |
| Alpha Lab, proposer | Weekdays 18:10 | The one model call that proposes hypotheses |
| Meme ingest | Sunday to Friday 21:15 | chester-meme's packets as Book D drafts (the overnight pass repeats it before 07:00) |
| Evening note | Sunday to Thursday 21:30 | The evening note, after its own fetch |
| Alpha Lab, weekly | Sundays 06:00 | Walk-forward, re-fit, rebalance, the agenda, the verdicts |
| Restore test | Sundays 10:15 | Restores the newest encrypted snapshot and checks it against the sweep's count |
| Quarterly | The second Saturday of January, April, July and October, 06:00 | The Alternative Assets Quarterly; ships disabled; first edition 9 January 2027 |
| Broker gateway restart and watchdog | Held back | Enabled only after a witnessed clean start |

The monthly restore drill's units are deleted; its tool remains.

**The calendar.** The feed repair merges on Tuesday 27 October inside the windows. The Monthly's dry runs are 23 and 28 October; the deploy freeze runs from 29 October 23:30, and no Weekly edit is made from 29 October to 1 November; the first stacked Monthly and the first digital-assets addendum are on 1 November 2026. The seventh chain merges after that Monthly. The two notes are live from 26 October; until then each run is a dry run. Doctrine #2 sits on 7–8 November; Audit #5 is the week of 23 November.

**Gates.** `make validate` runs every gate: on the seventh chain, 139 code gates (136 Python, 3 shell) and 8 data gates, with no network and no box; the feed repair adds one code gate, so 140 after its merge. A code gate seeds a store of its own and never reads the live one. A data gate reports on the box's real history, does not set the exit code, and prints NOT VALIDATED where there is no store. The list lives in the `Makefile`, and CI reads it from there.

**Operating windows.** Deploys and other box writes: weekdays 09:05–15:40 and 17:20–23:30, never 16:00–17:20; weekends open, clear of Sunday 05:00. A merge to main is a box write: every box wrapper pulls main before it starts, and unit files follow at the next self-deploy. A session never runs unit commands, privilege escalation or register writes.

**The stack's budgets** (targets, never caps, ruled 24 October 2026; an edition over its target prints one line at its foot).

| Report | Prose words | Charts | Reading target |
|---|---|---|---|
| Daily close | 2,250 | 3 | 10 minutes |
| Weekly | 7,900 | 10 | 35 minutes |
| Monthly | 10,000 | 12 | 55 minutes |
| Quarterly | no word budget | 40 | 90 minutes |
| Digital-assets addendum | about 1,500 | 2 (none drawn in its first phase) | 7 minutes |
| Open note | 250, a hard cap | 1 | 2 minutes |
| Evening note | 150, a hard cap (Sunday 400) | 1 | 1 minute (Sunday 3) |

Reading time is prose words ÷ 250 plus 20 seconds per chart. A firing trigger adds one chart. The runaway guard withholds a reply past twice its section's ceiling, and never past 7,000 characters. The dealer retrospective's floor: 20 scored sessions. The evening note asks for a paragraph on a weekday only when the e-mini or Nasdaq future moves past 0.75%, dollar-yen past 1.0% or an Asian index past 1.5%; always on Sunday.

**Charts and what the dealer charts displace.**
- **The close:** C1 SPY's session, C2 sixty daily candles, C3 by rule, and D2 the dealer chart after C1 and any C3. With C3 drawn and no trigger, C2 is set aside.
- **The Weekly:** W1 SPY six months; W2 two years; W3 the curve and the high-yield spread; W4 speculative positioning; W5 sector and style returns; W6 open contradictions (only when one is open); W7 SPY over 23-hour sessions with the overnight future; W8 six markets; W9 positioning and sentiment gauges; W10 prediction-market odds; W11 the standing decomposition, in What's priced; W12 the dealer panel. W12 enters fifth and sets W10 aside, and W11 too when W6 is open and no trigger fires.
- **The Monthly:** M0 to M13, fourteen charts, M12 only when the month's dealer profiles exist; capped at twelve. Set aside first are M13, then M8 (which does not render until scenario set #1 exists), then M9, then M12.

**Thresholds.**

| Threshold | Value | Where |
|---|---|---|
| The market-state object | Rules v2.0, method 11; persistence 2 sessions; a five-year window; bands 66 and 33; contradictions open at a gap z of 2.0 held 2 sessions and close after 2 failing; exceptions at 5; extremes at the 5th and 95th percentiles; the VIX bands 14, 20 and 30 | `market_state.yaml` |
| The five added dimensions | Funding stress on absolute bands (stressed at 10 bp and above, watch at 0 and above); policy at +25 and −25 bp; valuation ranked over its full history beside five years | `market_state.yaml` |
| Per-horizon reads | 5, 20 and 63 sessions (Books C, B, A); bands 66 and 33; persistence 2 | `market_state.yaml` |
| Calibration | 30 independent starts per row; horizons 5, 20 and 63 sessions; add-half smoothing | `altdata/state_calibration.py` |
| Dealer regime word | Prints only at net-to-gross ≥ 0.10 (ruled) | `reporting_stack.yaml`, `dealer_block` |
| Walls | The out-of-the-money walls; the all-strike peaks print as peaks | the dealer engine |
| Volatility event | A one-day VIX change of 15% or 3 points either way; a five-day log change past its 95th percentile on a 20-year window; a crossing of the volatility dial's band; compression within 5% of the 126-session low, held 3 sessions | `vol_event.yaml` |
| The 12:30 volatility gate | Upward only: +15% or +3 points | `vol_event.yaml`, `midday` |
| The volatile-day flag | The overnight range past 1.5 times the 20-session average true range (at least 15 sessions), a gap of 1% or more, the VIX arm, a negative gamma dial, a tier-1 calendar event | `vol_event.yaml`, `volatile_day` |
| The one-day 10-year move | The day's absolute change past the 97.5th percentile of five years of changes, either way; "not read" below 1,000 changes | `oneday_10y.yaml` |
| The gold event | A one-day move of 2.5%, or a five-day move past its five-year 95th percentile | `gold_event.yaml` |
| The developed-market drawdown screen | Ten- and twenty-session drawdowns past their five-year 95th percentile | `dm_drawdown.yaml` |
| Relative options volume | 1.5 times (provisional; reviewed after 19 November) | the relative-volume config |
| Outlier marks | 6 standard deviations of the last 60 changes, every family (session-set) | `data_quality.yaml` |
| Cross-source tolerances | VIX against VIXCLS: 0.01 (measured 15 October over 1,029 days); ^TNX against DGS10 and ^TYX against DGS30: not yet measured | `data_quality.yaml` |
| Correction and bear | −10% and −20% from the 52-week high | `altdata/derived.py` |
| Credit widening | HY, BB, CCC +100 bp and IG +40 bp in three months (ruled 4 October); AA +25, BBB +50, EM corporate +75, EM high yield +150 (session-set) | `metric_lenses.yaml` |
| Lens disagreement | 30 points between the five-year and the long-window percentile | `altdata/derived.py` |
| The store check's "dead?" | Past three times a key's own allowance | `tools/check_store_registry.py` |

**Publication-lag families.** Fifteen on the seventh chain (among them the H.10 rates, the EIA's spot prices, the term-premium models, Z.1, TIC, the IMF, the emerging-market monthly and quarterly releases, the World Bank's pink sheet, China's statistics bureau, H.8's weekly deposits, NOAA's degree days, the Shiller housing sheet, and FRED's quarterly and monthly releases); the feed repair adds twelve (the national CPIs, the ECB's swap rates, Redfin, the New York Fed's consumer survey, the Census construction data, H.6's money funds, the bitcoin difficulty, the EIA's rig counts and the Cleveland Fed's policy rules), so 27 after its merge. Each states its publisher's documented delay, its slack and its bound. Listed with no family because their publishers state no delay: the Tuck data library and the shillerdata.com workbook's earnings and dividends.

**The dealer scorecard's pre-registration** (`docs/ledgers/dealer-scorecard-preregistration-2026-10.md`, dated 17 October 2026, never edited). A rate prints only from 20 scored sessions, and is no decision below 120 eligible sessions. 120 formation sessions, then 120 test sessions. Benjamini–Hochberg at q = 0.10 across the six tests. A flag is demoted when a rolling 120-session interval includes its base rate for two consecutive months.

**Calibration ledgers.** Every ledger's pass rule is the order's where the order states one, else the first edition's; a box re-run applies it and may not change it. First editions run on the laptop from public sources and are labelled so; the box's re-runs write new dated files.

**The vendor writer** (`config/flashalpha.yaml`). The plan ends 31 March 2027. Symbols: SPY, QQQ, IWM, SPX and MSTR. A daily call budget of 60, planned at 57: 45 at 16:25, 6 at 09:45 and 6 at 12:30. The expected-move path prints "expected move: not served" on a 403 or 404. Its implied volatility is compared only on the first expiry of 20 days or more, from the 16:25 capture. The divergence data gate's tolerances: GEX 50% relative, DEX 15%, the flip 0.5% of spot, the walls 1.5%, the regime word compared as a word.

**Risk limits and attention.** As Draft 2 (`risk-limits-v1`): capital base $300,000; net beta at the regime band's top plus 15 points; sector at most 30%; volatility exposure at most 0.5% of capital per vol point; duration at most 5% per 100 bp; Book A bands Expansion 60–80%, Overheat 40–60%, Tightening and Contraction 20–40%; Transition for 10 sessions. Attention: 7 packets a week and one sitting of at most 2 hours, a rule; the third count uncapped.

**Prose and audits.** One call per section, with one revision for a section the audit withholds (the rule broken, the failing span and the draft go back with it) in the stack, the précis, the close, the anchor, the two notes and the Monthly's storyline fallback. Voices scan: at most 60 model calls a day, 10 days' lookback, a 15-minute budget; the open note's voices pass 120 seconds, inside the same cap.

**Sources.**

| Family | Count |
|---|---|
| Price symbols | 127 (124 on the feed repair's base; 127 after its merge) |
| FRED series pulled | 283: the Monthly's 59, 65 signal series, and the smaller lists (FX scan 18, SLOOS 5, AQ-3 7, SR-43 12, Thailand 1, 6e 25, release lenses 45, Group B 29, the bank-stress legs 10, households 1, retail sales 1, the PPI and Z.1 lines of Batch 14 4, the Nikkei 225 1) |
| Official writers | 33 |
| External writers | 37 (the feed repair's two refused writers stay listed and request nothing) |
| Loggers | 7 |
| Option chains | the 17 captured names by Yahoo; SPX and SPCX by Massive at 16:31, their greeks behind the solver gate |
| Prediction markets | 2 venues |
| Voices sources | 22 declared; 17 enabled on the seventh chain, 16 after the feed repair disables one |
| Publication-lag families | 15; 27 after the feed repair |

**Keys held** (names only): FRED, Anthropic, the dashboard token, SMTP, Nasdaq Data Link, Massive (and its flat-files pair, read by one backfill tool only), FlashAlpha, OpenFIGI, the bitcoin-data service's free key, the backup's encryption passphrase, and the SEC contact address. **Keys not pursued** under the standing rule of 16 October on sources: Webstat (its keyless TEC 10 export is read instead), the Bank of Korea's ECOS, the Bank of Thailand's API (its keyless table is read instead) and Etherscan. **Pending decisions:** the xAI path (item 50, Tranche 1) and the December vendor month.

**Sources that refuse, or that the system declines.**
- **Declared refused on the feed repair (24 October):** MBA (an HTTP 403 on its robots.txt); Apartment List (403; Zillow is read alone); Farside (403 through a Cloudflare challenge). Each prints "not tracked: … refuses automated reads since 2026-10-24".
- **Disabled on the feed repair:** Yahoo Finance's voices index (its feed answers 404). Its two candidate replacements were checked and refused: Yahoo's per-ticker headline feed by its robots.txt and terms, and CNBC's markets feed by its owner's terms.
- **Listed gaps:** WGC's files, which need a login and whose terms forbid scraping (the central-bank leg reads the IMF's IFS instead); DTCC's per-name CDS volumes, a subscription product whose terms forbid automated extraction.
- **Disabled in the voices list:** CNBC (403), Goldman's insights (403), Morgan Stanley and Nuveen (time out).
- **Withdrawn or retired:** S&P DJI's EPS workbook, printed "not tracked (source withdrawn)"; CoinGecko, its terms bar storing its data; the LBMA writer; the Google News story queries, by their robots.txt.
- **Other:** Bybit is switched off by a country block. State Street's GLD archive is refused to the API host by robots, so the operator drops it once. GeckoTerminal's site robots disallow crawling, and its documented API is read under its own terms.

**Superseded keys** (declared on the feed repair): IOER by IORB (still pulled, read by nothing); the overnight 10-year index fields by the daily index; the LBMA price by the COMEX front future. On the seventh chain, WGC's keys are superseded by the IMF's.

**Scans outside the repository.** Recorded in the Master Guide's record of the chat-side tasks (`docs/master-guide/chat-tasks.yaml`, the Guide's Table 2), updated 20 October:
- the Guide to the Markets read (the 6th of January, April, July and October);
- the Monthly signal scan (the 25th, 06:57; first run due 25 October 2026);
- the Saturday crypto mechanism scan (retiring);
- the AI-risk consensus-drift scan (the 20th of even months);
- the reading-shelf publication watch (the 12th and the 27th), with the six houses' capital-market-assumption files since 24 October;
- the AAII weekly read (Thursdays);
- the MSTR/MSCI event watch (weekdays 2–30 November, and 1 December);
- the FlashAlpha tasks (retiring);
- the X digest (daily 06:00) and its triage (06:50), a pilot since 17 October, with accounts that publish only on X added in a monthly batch;
- the Saturday brief, which writes the Alpha Lab's inbox;
- the Alternative Assets Quarterly's scan (planned for January 2027).

---

## Appendix B — The Incident Log to Date (as of 24 October 2026)

*From `docs/incidents.md`. No incident has been logged since INC-9, on any branch.*

| Id | Date | What happened | Fix and lesson |
|---|---|---|---|
| INC-1 | 27 Sep 2026 | The off-box backup never ran under its unit | Unit corrected; the heartbeat gained a backup field |
| INC-2 | 27 Sep 2026 | Narrative prompts silently truncated; every close for four days and the first Weekly were written from a partial brief | Whole templates now reach the model, with a gate that proves it |
| INC-3 | 29 Sep 2026 | The backup stalled on a cloud-storage quota error until its unit timed out | Stall limits, a per-tree cap, a clean kill record |
| INC-4 | 30 Sep 2026 | The overnight fetch timed out three mornings running while the heartbeat said healthy | Fetch first, an early pull, a shorter limit; the heartbeat now reads each unit's own result |
| INC-5 | 1 Oct 2026 | The implied-volatility solver missed its accuracy bound on the index chain | A finding, not a fault: the index stays out of the solved-volatility path |
| INC-6 | 1 Oct 2026 | A peso-listed SPY short was held on a draft decision and closed at a loss of about $8,950, mostly from the currency and the listing's basis | *A foreign listing is a currency position*: structured exit fields, an FX series, a currency gate |
| INC-7 | 1 Oct 2026 | Closed positions persisted in Portfolio Truth for a week | Each sync is now the whole book; absent holdings are written as zero |
| INC-8 | 2 Oct 2026 | A fallback recorded a peso close as dollars | *A fallback that invents a value is worse than an empty field*: unknown stays unknown; one rule judges every write |
| INC-9 | 6 Oct 2026 | From 30 September to 6 October the loggers ran nowhere: the end-of-day pull skipped them as "run in the overnight pass", and the overnight pass's early set skipped them too. Six sessions of point-in-time captures were lost and cannot be backfilled. Found by this paper's first draft | *A feed is not scheduled until a gate says so*: the overnight fetch runs the loggers; a gate fails any commit in which a feed has no runner that does not skip it |

---

## Appendix C — Assumptions and Falsifiers

**Mechanisms this paper assumes.**

1. *One regime prevents contradictory decisions.* Falsified if two reports print different regimes for the same session, which a gate checks by construction, or if a decision cannot be attributed to the object it was taken under.
2. *Auditing figures against a payload keeps prose honest about numbers.* Falsified by any printed paragraph containing a figure not in its payload, or a true figure under a false name. The label audit exists because the second happened once.
3. *Point-in-time reads make past editions reproducible.* Falsified if a dry run of a past edition prints a figure that was not knowable at its cutoff. The rule that a `--week-ending` dry run reads at the scheduled run time exists because one did.
4. *Grading in code against a coin and a base rate distinguishes skill from luck over time.* Falsified only slowly. Evidence and Inference shows how long a sample must be before a Brier difference means anything, and this paper claims no result yet.
5. *Supersession preserves the grading trail.* Falsified by any edit to a stored packet or decision, which the database refuses.
6. *The dealer flags describe something real.* Falsified by the pre-registration's own demotion rule: a flag is demoted when a rolling 120-session interval includes its base rate for two consecutive months, and no flag's rate is a decision before 120 eligible sessions.
7. *The Alpha Lab's engines carry an edge.* Falsified engine by engine by the lab's kill rule: after its minimum number of signals, an engine's expectancy after modelled costs at or below zero, or a realised Sharpe below half the deflated Sharpe it was validated with, retires it. The loop retires by that rule alone; a retirement by ruling is the operator's.
8. *A pass rule fixed before the run keeps the calibration ledgers honest.* Falsified by any later edition that changes a registered rule, which the ledger writer refuses.

**Regularities with dates.** The Brier coin of 0.25 is arithmetic, not a regularity. The thresholds in Appendix A were set by ruling, not estimated, and are falsified in the operational sense if a trigger fires every session or never over a month. That is the test the Doctrine monthly applies.

**Standing-register items touching this paper.** The intraday layer's engines (Part VIII) are unregistered. The stacked Monthly is built and has not yet published: its first edition, on 1 November 2026, is the one to read against §4.6. The object's calibration has no calibrated row yet (§3.10). The Alternative Assets Quarterly is built with its timer disabled. The Quarterly Structural, Disruptive Themes, the Top & Bottom harness and the Thailand quarterly are unbuilt. The prediction-market confidence gate is unbuilt by design.

**Dated figures in this paper.** Every count, threshold, time and limit in the body is described rather than stated; the values are in Appendix A, as of 24 October 2026, from the configuration files named there.

---

## Appendix D — Where the Brief Disagreed with the Code, and What Drafts 2 and 3 Called Unbuilt: Dispositions (as of 24 October 2026)

*Draft 1 of this paper was commissioned by a brief, and in writing it twenty-five places were found where the brief, or the repository's own documents, disagreed with the code. Draft 1 followed the code and left each item for a ruling; they were listed when it was merged on 6 October. This appendix records what became of each. "Fixed" names the change that fixed it: D-2 (the corrections to the repository's own documents, 7 October), L-1 (the loggers' schedule and the small items with it, 6 October), T2.6 and T2.7 (the stack's cadences and the shared renderer, 8 October), T3 (the stacked Monthly, 8 October) and LIB-2 (this draft and its two companions, 9 October). "Ruled for Audit #4" means a ruling has placed it on that sitting's business. "Open" means nothing has yet been decided or changed.*

**The data**

| # | Draft 1 found | Disposition |
|---|---|---|
| 1 | No H.4.1 writer: the balance-sheet legs come through FRED; the brief's list of official writers omits the New York Fed's consumer survey and the Fed Board's inflation-expectations index | **Fixed (D-2).** Both briefs carry a dated correction |
| 2 | WallStreetBets is a feed inside the borrow-and-mentions logger, not a logger of its own; the retail-activity logger is dormant without its key; the shielded-share logger has no reachable source | **Fixed (D-2)** for WallStreetBets. The dormant logger and the missing source are facts about the feeds, not disagreements, and stand |
| 3 | The loggers had no scheduled run | **Fixed (L-1).** Recorded as INC-9 (Appendix B); the overnight fetch runs them and a gate holds every feed to a runner |
| 4 | The brief names two kinds of knowable time; the code has three (observed, ingest instant, reconstructed), and nothing yet wrote the first | **Fixed (AUD-3d, 15 October).** The ALFRED backfill writes each FRED value as observed at its vintage's first publication. The brief is unchanged |
| 5 | The contradiction table has eight pairs, not seven | **Fixed (D-2)** |
| 6 | A contradiction closes on the first session it fails, though the documents said it closes over two | **Fixed (6f, on the seventh chain).** The close is symmetric: two failing sessions, as two open it, with *closing* between (§3.5) |
| 7 | The stacked close does not open on the What changed block | **Fixed (D-2, T2.6).** D-2 corrected the documents; T2.6 built the state and contradiction tables at the end of the close (§4.7) |
| 8 | The state-object document was stale in places | **Fixed (D-2)** |

**The reports**

| # | Draft 1 found | Disposition |
|---|---|---|
| 9 | The Monthly was not on the stack; it had no depth column and its charts existed only in the brief | **Fixed (T3, on T2.6 and T2.7).** §4.6 describes it as built; the depth column, Slow layers, Reading and M1–M9 are in configuration and code |
| 10 | The Quarterly Structural, Disruptive Themes, Top & Bottom and the Thailand quarterly are not built | **Open,** and described as not built (§4.8). The Quarterly Structural still has no specification document |
| 11 | Reading targets were documented, not configured | **Fixed (T3).** The three targets are in configuration; the Weekly and the Monthly print against them |
| 12 | The deploy did not enable the Weekly, Monthly, voices and auction timers | **Fixed.** L-1 put the Weekly, voices and auction timers on the deploy's list, and A-4 the Monthly's on 9 October (Draft 3 said "open" here in error) |
| 13 | The Weekly sent no dashboard state record | **Fixed (L-1).** It reports under its own key, and not on a dry run |

**Prose and scans**

| # | Draft 1 found | Disposition |
|---|---|---|
| 14 | The one retry existed only in the stacked prose | **Fixed (T2.6, T3).** T2.6 stopped the stacked prose from retrying a failed call, so only an audit's refusal is retried; T3 gave the Monthly's section writer the same retry. The morning anchor and the voices block make one attempt, as §5.3 says |
| 15 | No single plain-language audit; the brief's audit list omitted real checks | **Fixed (D-2).** The brief records that its list is superseded by §5.2 |
| 16 | The Monthly signal scan had no definition in the repository | **Fixed in part (L-1):** the scheduled-tasks record defines its time, its output and the decision that created it. **Open:** the rights the brief gave it, a voices entry included, are not ruled |
| 17 | "AI-risk" appeared nowhere in the repository | **Fixed (L-1).** The scheduled-tasks record names the AI-risk consensus-drift scan. The Saturday crypto scan remains interim until it retires |

**The register and learning**

| # | Draft 1 found | Disposition |
|---|---|---|
| 18 | Book Z is three benchmark ledgers, not a register book, and the Doctrine names only a 60/40 benchmark | **Fixed in part:** the scoreboard computes the Doctrine's benchmarks, Book A alone and the 60/40, as measurement; their use is on the Doctrine #2 agenda |
| 19 | The entry gate enforces four limits only; the per-position tiers, the book loss stops, the kill-switch ladder and the heat cap are reported but not refused, and the Systematic Book paper says an over-tier position would be refused | **Open** |
| 20 | "Heat" means a factor view in the code and open risk to invalidation in the Doctrine; the second is not computed | **Open** |
| 21 | Reconciliation's comments say hourly against a 30-minute timer, and an empty currency was read as dollars | **Fixed in part (L-1):** an empty currency is refused with a reason, never read as dollars. **Open:** reconciliation's comments still say hourly; the timer's own comment says 17:30 since the third chain |
| 22 | The intraday layer: "never orders" comes from the Doctrine minutes while the Enterprise Layer's tactics item may place paper bracket orders; the state vector is defined only in a change order; none of it is built | **Open,** and described as unbuilt (Part VIII). The intraday scope is on Audit #4's list from the Enterprise Layer change order; the bracket-order question is not |
| 23 | The Operating Doctrine was behind the 2 October rulings | **Fixed (LIB-2).** Its dated appendix carries the rulings and the incidents, and its body changed where it contradicted a ruling. **Open:** Book C still cites a 10:00 report; the Doctrine #2 pack drafts the 09:50 open note in its place |
| 24 | The Daily Cascade paper's Part 0 described as live what is not built | **Fixed (LIB-2).** Part 0 opens on a dated note marking the intraday slots and the drafted setups as plan, and describes the stacked close as it runs |
| 25 | The voices scan's time was stale in three places; the deploy windows were not in the repository | **Fixed (L-1).** All three say 06:15; the windows are in `CLAUDE.md` (Appendix A) |

Of the twenty-five, seventeen are fixed, four are fixed in part and four are open. (Draft 4 re-tested items 4, 6, 12, 18 and 21 against the code; the others stand as Draft 2 recorded them.)

**What Draft 2 called not built, and what became of each (as of 19 October 2026)**

| Draft 2 said not built | Disposition |
|---|---|
| The intraday layer: no captures, no state vector, no engine | **Built in part.** The 09:45 and 12:30 captures, the state vector and the 12:30 alert slot are built (§8.4). No engine of the layer is registered |
| The Quarterly Structural | **Open.** Still no specification document |
| Disruptive Themes | **Open,** folded into the Quarterly Structural |
| Top & Bottom as a harness | **Open.** The Monthly still prints its place as not built |
| The Thailand quarterly | **Open,** deferred to the end of the roadmap |
| A quarterly report of any kind | **Built:** the Alternative Assets Quarterly, its timer disabled until January 2027 (§4.8) |
| The prediction-market confidence gate | **Open by design** |
| The Monthly's timer enabled by hand | **Fixed.** It is on the deploy's list |
| The broker sync's comments saying hourly | **Fixed in part.** The timer runs every 30 minutes to 17:30, and its comment says so since the third chain; reconciliation's comments still say hourly |

**What Draft 3 called not built, and what became of each (as of 24 October 2026)**

| Draft 3 said not built | Disposition |
|---|---|
| The gauge's pre-market line; SPX's and SPCX's "awaiting the solver gate" | **Built** (third chain; §4.7) |
| The Monthly storyline writer's one revision | **Built** (third chain; §5.3) |
| The crypto daily paragraph and its 12:30 leverage line | **Built behind a switch that is off** (third chain) |
| The S-2 and S-3 calibration ledgers | **Built;** both FAIL, accepted 20 October (§9.9) |
| The retirement of the monthly restore drill's units | **Done** (third chain); the tool remains |
| Engine 6, the grammar search and their appendices | **Built** (third chain; §8.5) |
| Engine 7, and version 2 of the hypothesis grammar | **Built;** engine 7's registration is the operator's; one condition of the grammar's version 2 is not built |
| 6f | **Built** on the seventh chain: the five dimensions, the horizons, the calibration, the tail families, the debt-cycle branch and the bar (Part III); the weekly alignment stamp on a later branch |
| The December vendor month | **Still a plan;** the Doctrine #2 pack drafts a start on 1 December |
| The vendor's e-mail alerts | **Outside the system,** as ruled |
| Crypto Tranche C | **Not built** |
| The Quarterly Structural, and the 6i brief | **Not built;** the 6i brief is a draft on a later branch |
| Item 50 Tranche 1 | **Not built;** a decision around 31 October |
| The Enterprise Layer's EL-8 to EL-13 | **Not built;** a learning-loop brief on a later branch proposes work toward them |
| G-6; a trade tape | **Not built** |
| The Opening Setup's remaining rulings | **Not ruled;** the 0700 list and the 09:50 note are on the Doctrine #2 agenda |
| The intake-queue entries waiting for "T&B full" | **One entry,** GTM-3 (Draft 3 said two) |
| The rates driver | **Still withdrawn** |
| The conversion of dealer levels to the e-mini | **Still not wired** into a report |
| The PRL explorer's endpoint | **Closed** as a listed gap on 18 October (Draft 3 listed it in error) |
| A stored macro consensus | **Not built** |

---

## Appendix E — What Draft 4 Says Is Not Built (as of 24 October 2026)

*So that the next draft can be checked against it. "Not built" means on neither the seventh stitched chain nor the feed repair; an item on a branch that merges later says so.*

**On branches that merge after the seventh chain.**
- **The weekly alignment stamp** (6f tranche 4): the register's second alignment, against the weekly per-horizon read, written by the decision tool at entry, its migration the operator's; and the Quarterly's split of graded packets by both alignments.
- **The capex-guidance reader:** the hyperscalers' capex guidance from their own 10-Q and 10-K filings, each figure stored beside its filing's sentence, read by the capex chain's line, item 26's revisions and the Quarterly's question.
- **The Doctrine #2 pack's refresh and the dated-appendix moves** (documents only).
- **The 6i brief** (a draft), and **a learning-loop brief** (a draft for a ruling).

**Specified, not built.**
- **Crypto Tranche C:** the long-term-holder series waits on a free key, and the Dune queries are unbuilt.
- The Quarterly Structural.
- **Item 50 Tranche 1:** the X digest's API path on the box, a decision around 31 October.
- The Enterprise Layer's EL-8 to EL-13: the lessons register (EL-10) and the Doctrine's two paper engines (EL-12) among them.
- **G-6.**
- **A trade tape.**
- The Opening Setup's remaining rulings: the 0700 list, and the open note as the Doctrine's 1000 report.
- The intake-queue entry that waits for "T&B full".
- The rates driver, withdrawn on 30 September and not reinstated.
- The conversion of dealer levels to the e-mini, written and gated but not wired into a report.
- A stored macro consensus, which the surprise index's non-FOMC legs need.
- The earnings and geopolitical dimensions, each waiting for its source (§3.2).
- A probability for any tail family, which waits for the prediction-market gate and a ruling.
- The debt-cycle branch's state, which waits for the paper that will define it.
- A reader for the MSTR/MSCI watch's Drive file.
- The December vendor month, a plan.
