# Change order — Signal-triage round 6, Part 3 (items 49–51): the digital-assets batch

**File:** `docs/change-order-signal-triage-batch-8-2026-10-17.md`
**Status:** RULED 2026-10-17 in chat; **FILED 2026-10-17** by the filing chat (08:20 ET). Commits on `docs-batch-8` from main, after Batch 7. Two scheduled watches and one pilot already running (see §5).
**Encoding:** Batch 8 of Post-Freeze Amendment #4. Round 6 Part 1 (item 45) was folded into Batch 6 at filing on 15 Oct (`docs/change-order-signal-triage-batch-6-2026-10-15.md`, items 30–45); round 6 Part 2 (items 46–48) is Batch 7, filed 16 Oct (`docs/change-order-signal-triage-batch-7-2026-10-16.md`, on `docs-batch-7`). Both were filed before this order arrived, so there was nothing to fold into; this file is round 6 Part 3 and takes the next batch number. Decided by the filing chat, 17 Oct 2026.
**Precedence:** below Part 26 and the 25 Sep integrated signal-triage order; follows its integration rules (R28 sub-states, one system of record, Track D preconditions, validation gates as offline calibration studies with dated ledgers). Item 50 follows the Prediction Market Intelligence rights template (post-freeze amendment #1): discovery / attention-shock / disagreement rights only, confidence-modification deferred pending a calibration archive. Item 51 gives the 7 Sep 2026 ruling (Alternative Asset report folded into the Monthly) its shape.
**Workplan ruling carried in this order (§6):** the crypto data-sources order of 6 Oct 2026 (`docs/change-order-crypto-data-sources-2026-10-06.md`, Batch 4, Tranche A ≈19h, previously "later") is pulled forward so that item 51's Phase 2 panels can follow its Phase 1; the filing chat places it in §6 against Workplan v7's calendar and v5's 8 Nov finish and states what it displaces.

---

## 1. Purpose and scope

Three items ruled 17 Oct 2026, all in the digital-assets thread (Thread D): an event entry with a tradeable date (49), a new input layer (50) and a new output chapter (51). Together they are the batch that makes crypto a first-class part of the reporting stack rather than a set of register entries. Nothing here changes the frozen architecture; no composite weights change; rights are narrow and stated per item.

## 2. Entry conventions

As Batches 5–8: **Source** · **Read** · **Thought process** · **Stack today** · **Ruling** · **Rights** · **Placement** · **Work**. Items 50 and 51 are brief-style entries.

## 3. Entries

### 49 · MSCI exclusion of Strategy (MSTR) and the bitcoin demand channel (unattributed secondary analysis; verified against reporting 17 Oct 2026)

**Source.** A pasted analysis with citations stripped, reading as a model summary. Tag: unattributed secondary. Verified the same day against The Block (15 Oct 2026), CoinDesk and earlier reporting of the JPMorgan estimate.
**Read.** MSCI adopted (announced 15 Oct 2026) a "non-operating company" methodology effective with its November 2026 Index Review: an operating-assets screen and five financial ratios, replacing the interim digital-asset-holdings restriction. Strategy, Metaplanet and Yellow Cake failed the screen in MSCI's May 2026 simulation. Review announcement expected 11 Nov 2026 after the US close; changes expected effective at the close of the last business day of November (30 Nov — to verify on MSCI's calendar). JPMorgan (Nov 2025) estimated ~$2.8bn of passive MSTR selling, up to ~$11.6bn if other providers follow. Strategy held ~848,000 BTC as of 4 Oct 2026. The analysis: direct effect on BTC minimal (funds sell MSTR, not coins — MSTR −4 to −10% on the day vs BTC ~−1%); the indirect channel is Strategy's financing machine — equity, preferreds and converts issued at a premium to holdings (mNAV) fund its BTC purchases, and a compressed premium slows or stops the largest corporate buyer. First X digest (17 Oct) adds: MSTR −11% on 16 Oct vs BTC under −2%; Strategy conditionally declared daily STRC dividends at 12% for November, subject to a shareholder vote on 28 Oct.
**Thought process.** The analysis is right on the main point and misses one. Its "no path to forced BTC sales" is too strong: preferred dividends and convert maturities are paid in cash, and when the premium is gone equity issuance closes, so the obligations schedule is the only mechanism by which BTC could actually hit the market — public, and now dated (28 Oct vote, daily November payments). The wider frame is reflexivity: premium → issuance → BTC buying → BTC up → premium, and the loop runs in reverse. The best base rate is GBTC's premium-to-discount in 2021–22 and the forced unwinds around it. The decisive open question is MSCI's two-consecutive-period rule for existing constituents: if Strategy's FY2024 and FY2025 filings already count, deletion lands 11 Nov; if the clock starts now, 11 Nov is a reprieve — and last cycle's reprieve followed a 51% drawdown from the October high. For Book D this is a textbook forced-flow setup, whose flow lands at the effective-date close, not on 11 Nov. Options at posting (FlashAlpha, 16 Oct close, spot $135.24): ATM IV 77.8% between HV20 67.8% and HV60 84.5%; expected move ±20.1% to 13 Nov and ±24.2% to 27 Nov; the forward vol for the week spanning 11 Nov (~68%) sits below the front weeks (75–80%) — no event premium is priced; the window spanning the effective date (~70%) carries a slight bump. Dealer map: flip ~$141 (flagged sensitive), put wall $125, call wall $160, max pain $146; skew unavailable on the Basic tier.
**Stack today.** Thread D: ETF flows (Farside), SR-29 LTH scorecard, froth gauge, DVOL; no mNAV series, no corporate-treasury flow line, no index-event entries for crypto proxies, no Treasury-company obligations schedule.
**Ruling.**
1. mNAV premium series, daily — MSTR market cap over BTC holdings value, extended to the top treasury companies from the public aggregator — watch line 1.2, flag 1.0 (issuance-funded accumulation stops).
2. Corporate-treasury net BTC purchases, monthly from filings and the aggregator, printed beside ETF flows as a "who is buying" demand decomposition.
3. Strategy obligations schedule — preferred dividends (STRC daily at 12% from November if the 28 Oct vote passes; STRK, STRF, STRD) and convert maturities — by hand from filings, reviewed quarterly, as the only forced-sale channel.
4. Index-event entries in the ahead block: 28 Oct STRC vote; 11 Nov MSCI list; the effective date; the next review dates of FTSE Russell, S&P DJI and Nasdaq as the broad-exclusion scenario watch. PM layer discovery rights on any MSCI/MSTR market.
5. Base-rate note in the Digital Assets paper's dated appendix: GBTC premium-to-discount 2021–22 as the analogue, the reflexive loop written out, and this event's outcome appended after 1 Dec.
6. Narrative register: "treasury-company unwind," with intensity; a Book D paper-only template for the effective-date flow setup (pre-position into the effective date; reversal leg after it; exit rule at the effective-date close), logged to the register as a draft, never auto-generated.
7. Event preparation, by hand before 11 Nov: the two-period rule as applied to Strategy from MSCI's published methodology; passive ownership in days of volume; short interest and borrow; options term structure across both dates; Strategy's own issuance and buyback behaviour.
**Rights.** Flag (mNAV) only; no composite weight.
**Placement.** Positioning & flows (crypto); ahead; narratives; Digital Assets appendix; Book D template.
**Work.** ST-R6.49a mNAV series — 2h (rides Batch 4's treasury-company source). ST-R6.49b treasury net-purchase line — 1.5h. ST-R6.49c index-event entries — 0.5h. Obligations schedule, base-rate note, Book D template, event preparation — by hand ≈4h before 11 Nov. Two scheduled tasks already running (§5).

### 50 · Social attention layer — X via Grok (operator design question) — BRIEF

**Origin.** The operator asked whether the system can follow social media, X in particular, critically filtered, as a source on new crypto developments, using his Grok account to scan X and write a digest to Google Drive for the system to read.
**Thought process.** X is closed to everything the system can use unattended: web fetch meets the login wall, the X API is $200/month for a trickle and $5,000 for real access, browser automation from the laptop is not a daily unattended job. Grok has native X search, so it is the only practical door. The design question is the division of labour: Grok retrieves, the framework filters. A Grok-written summary would put the critical filter on Grok's framing; a structured retrieval digest (post URL, handle, time, claim as stated, figures, engagement, theme tag, linked source) keeps the filtering where the framework already does it — the intake template, the voices register with incentive tags, the narrative register with intensity, "no stored source, not printed." Grok is itself a source with an incentive (X's own model, engagement-leaning); it is treated as a search engine, never as an analyst. "Top influencer" accounts are the amplification layer and are not a target; a seed list of originators (data providers, security alert accounts, officials and companies, protocol teams, named analysts and journalists, each with an incentive tag) plus discovery by search is the design, and new accounts earn their way onto the list through the voices ledger.
**Stack today.** All scheduled scans (Saturday PRL/new-mechanism scan, Monthly signal scan, consensus-drift scan, publication watch) are web-only and therefore blind to X; the Phase B voices register has no social inputs; the narrative register has no attention measure.
**Ruling.**
*Tranche 0 — pilot, running from 17 Oct 2026.* (a) A Grok automation "chester-x-digest-daily" runs at 6:00 AM ET every day, X post search only (x_keyword_search, x_semantic_search, x_thread_fetch), two passes — a ~60-handle seed list retrieved by `from:` queries, then discovery across seven scope areas (mechanisms incl. PRL; flows; treasury companies incl. MSTR/MSCI; regulation; incidents; privacy/ZEC; macro-crypto) — at least 300 posts reviewed, up to 40 reported, written as `x-digest-YYYY-MM-DD.md` with seven fixed sections (run, attention map, items, disagreements, checkable claims, incidents, accounts, carry-over) to Drive folder `chester-x-digest`. First file passed its structural test on 17 Oct (seven sections, ~280 posts reviewed with X query operators listed, 34 items all with x.com status URLs); prompt v2 issued the same day (seed list, Farside daily totals, two-sided disagreements, original-party-over-aggregator rule, follower counts in the accounts section). (b) A reader scheduled task "X digest reader — daily triage" at 6:50 AM ET reads the newest digest, keeps two ledgers in `chester-vendor-checks/x-triage/` (`x-attention-ledger.csv`: theme, volume class, shock flag against a five-day baseline; `x-voices-ledger.csv`: handle, role, incentive tag, track record), grades digest quality, prints watch-list hits (treasury companies, PRL and mechanisms, ZEC, incidents, ETF totals), verifies up to three checkable claims against a primary source, proposes at most three intake candidates, and sends a ≤230-word message. The operator rules on candidates in chat.
*Tranche 1 — production, ruled after two weeks of reader output (≈31 Oct).* The retrieval moves to the VPS: a cron job calls the xAI API's X search with the same prompt, writes the JSON into the point-in-time store with `available_at` and a copy to Drive; the triage runs in the box's narrative step. One system of record. Cost to verify before the ruling (≈$25 per thousand sources at launch; ≈$40/month at the pilot's scan depth). Estimated build ≈12h.
*Rights.* Discovery, attention-shock and disagreement only, on the PM-layer template; a calibration ledger of attention shocks against subsequent price moves (≥60 days, ≥20 shocks) before any modifier right is proposed. Section 6's accounts feed the Phase B voices register with incentive tags; nothing from the digest prints without a stored source.
**Placement.** Narratives (daily close crypto block, Sunday anchor, Monthly attention map); Saturday mechanism scan (its first X-visible input); Phase B voices; item 51's section 6.
**Work.** Tranche 0 — done by hand 17 Oct (Grok prompt v1 and v2; reader task). ST-R6.50a Tranche 1 API ingestion + store writer (D1c precondition applies) — 8h. ST-R6.50b triage in the narrative step, ledgers migrated from Drive — 4h. ST-R6.50c attention-shock calibration ledger — 3h, after 60 days of rows.

### 51 · Digital Assets chapter — Weekly addendum and Monthly chapter (operator design question) — BRIEF

**Origin.** The operator asked whether crypto's importance warrants a separate weekly report as an addendum to the Sunday Weekly or the Monthly.
**Thought process.** Yes to the focus, no to a sixth report. The 7 Sep 2026 ruling folded the Alternative Asset report into the Monthly to stop report sprawl; the attention budget (two ruling sittings a week, one review sitting ≤2h) has no room for another publication cycle; and the data a standalone report needs (Batch 4 Tranche A; the X layer) is not yet built, so a separate report now would be narrative-heavy — the noise problem in a different wrapper. A fixed chapter rendered as its own page off the Sunday Weekly reads as an addendum (five minutes, phone-readable) and can be promoted to a report later without re-plumbing. Timing fits: the crypto week closes Sunday 00:00 UTC, so the Sunday 05:00 anchor captures the full week including Saturday.
**Ruling.**
*Weekly addendum (own page linked from the Sunday Weekly; ten-section stack in miniature, crypto only):* 1 the read — desk voice, weekly bars for BTC, ETH, SOL, ZEC read against the daily and monthly bars; 2 tape — prices, ranges, realised vol, DVOL, funding, basis, open interest, liquidations; 3 flows — ETF daily totals for the week, exchange net flows, stablecoin supply change, treasury-company purchases (item 49's "who is buying"); 4 mechanics — Deribit skew and term structure, MSTR mNAV and options through the event window, crypto GEX when EL-12 reaches it; 5 on-chain — SR-29 LTH scorecard, froth gauge, exchange balances; 6 narratives and attention — the week's X attention map from the seven digests (themes, shocks, disagreement pairs, new voices) and the Saturday mechanism scan's output incl. PRL; 7 incidents and regulation — digests' section 5, regulatory calendar; 8 ahead — dated events (28 Oct STRC vote, 11 Nov MSCI, 15 Nov VanEck JitoSOL decision, Deribit month-end expiries, FOMC); 9 the book — Book D crypto exposures and, from mid-November, the paper engine's view. One dated line per week into the Digital Assets paper's appendix.
*Monthly chapter (the Alt Asset fold-in's shape):* slow layers — halving-cycle base rate (SR-31), Factor V links (stablecoins, official gold bid); treasury-company sector table with the mNAV distribution; ETF holder data from 13Fs quarterly; mining economics (hashrate, hashprice); mechanism-watch register status (MW-7 promote/demote); the month's attention map; the white-paper appendix update. First edition 1 Dec 2026.
*Phases.* Phase 1 — chapter template and narrative step assembled from what already flows (reader messages, Saturday scan, Farside, and from 2 Nov the MSTR watch), first edition the Weekly of 1 Nov 2026. Phase 2 — automated panels on Batch 4 Tranche A (pulled forward by this order, §6). Reading target: 5 minutes for the addendum, 10 for the Monthly chapter; charts within existing budgets.
**Rights.** Report only. Nothing in the chapter has decision rights beyond what its inputs already hold.
**Placement.** Sunday Weekly (own page); Monthly (chapter after narratives, before ahead, beside Reading).
**Work.** ST-R6.51a Weekly addendum template + narrative-step prompt, Phase 1 — 6h (before 1 Nov). ST-R6.51b Phase 2 panel wiring on Tranche A — 4h (after Tranche A). ST-R6.51c Monthly chapter — 5h (before 1 Dec).

## 4. Cross-item rulings

1. **One thread, three layers.** 50 is the input layer, 49 the first event it serves, 51 the output they land in. The reader's watch-list hits (50) feed 49's event block and 51's section 6; 49's mNAV, obligations and event entries print in 51's sections 3, 4 and 8.
2. **Rights discipline.** 50 inherits the PM-layer template (amendment #1); its calibration ledger is the gate to anything beyond discovery. 49's only flag is mNAV. 51 adds no rights of its own.
3. **Ledgers on Drive during the pilot, in the store afterwards.** `mstr-msci-watch.csv`, `x-attention-ledger.csv` and `x-voices-ledger.csv` live under `chester-vendor-checks/` until 50's Tranche 1 migrates them to the VPS store; the Drive copies remain as backup (same pattern as the FlashAlpha and AAII files).
4. **Base-rate closure.** The 1 Dec post-effective read closes item 49's base-rate entry (GBTC analogue plus this event) in the Digital Assets appendix and in XX Base Rates.

## 5. Already running (created 17 Oct 2026, cloud-only, automatic approval)

- **MSTR / MSCI event watch — daily to effective date** — weekdays 2–30 Nov, 7:10 AM ET (Thanksgiving skipped): FlashAlpha implied moves and event-week forward vol (quota-guarded, ≤3 calls), MSTR/BTC/IBIT, mNAV with the 1.2 / 1.0 lines, Strategy filings, MSCI and other-provider news, short interest and days-of-volume, prediction markets; ledger `chester-vendor-checks/mstr-msci-watch/mstr-msci-watch.csv`; ≤220-word message by push and email. The 12 Nov run leads with the announcement result.
- **MSTR / MSCI post-effective read — 1 Dec** — one run, 7:10 AM ET: effective-date close vs the day after, closing-auction volume, the reversal check, mNAV across the window; closes the base-rate ledger.
- **Grok automation `chester-x-digest-daily`** — 6:00 AM ET daily, prompt v2, Drive folder `chester-x-digest`.
- **X digest reader — daily triage** — 6:50 AM ET daily, push only.

Note for the audit: three existing scheduled tasks failed on 14–15 Oct on usage limits (FlashAlpha Wednesday pull, Thursday reconcile, AAII read); the same limit would stop the November watch. To be resolved before 2 Nov.

## 6. Work order and workplan ruling

**Workplan ruling (operator, 17 Oct 2026):** Batch 4 Tranche A (crypto data sources, ≈19h, previously "later") is pulled forward. The audit places it against Workplan v5's 8 Nov finish and states what it displaces; item 51 Phase 1 does not wait for it.

**Now, before 1 Nov (~10.5h sessions + ~4h by hand):** ST-R6.51a (6), ST-R6.49c (0.5), 49's by-hand preparation (obligations schedule, two-period-rule check, days-of-volume, Book D template, base-rate note) ≈4h; ST-R6.49a (2) and ST-R6.49b (1.5) ride Tranche A if it lands in time, otherwise by hand for the watch.
**With Tranche A:** ST-R6.51b (4).
**After the pilot (~31 Oct), on the operator's ruling:** ST-R6.50a (8), ST-R6.50b (4); ST-R6.50c (3) after 60 days of rows.
**Before 1 Dec:** ST-R6.51c (5).
**Total:** ≈33.5h of sessions plus ≈4h by hand, plus Tranche A's ≈19h already ruled.

**Placement (the filing chat, 17 Oct 2026), against Workplan v7 and the 8 Nov finish.** Workplan v7 (adopted 16 Oct) already carried Batch 4 Tranche A on session B's nights of Mon 19 → Tue 20 and Tue 20 → Wed 21; both sessions ran a day ahead of v7 on 16–17 Oct, so the pull-forward is absorbed by moving it one night earlier and placing this order's items around it:

| Night (session B) | Work | Hours (est.) |
|---|---|---|
| Sat 17 → Sun 18 | Batch 8 filed on `docs-batch-8`; **ST-R6.51a** (the Weekly addendum, Phase 1: template and narrative-step prompt, assembled from what already flows) and **ST-R6.49c** (the index-event entries in ahead) | ≈7 |
| Sun 18 → Mon 19 | Batch 4 Tranche A, part 1 (CD-1, CD-2, CD-5, per the crypto order's Appendix B) | ≈9 |
| Mon 19 → Tue 20 | Tranche A, part 2 (CD-3, CD-4, CD-7, CD-8, CD-9's Weekly and Monthly parts, CD-10); **ST-R6.51b** (Phase 2 panels on Tranche A); **ST-R6.49a** and **49b** (mNAV, treasury net purchases) | ≈17.5 |
| Tue 20 → Wed 21 | The spill from the night before, then the audit leftovers (moved from v7's Wed → Thu) | — |
| Thu 22 | The second stitched chain merges with 51a, Tranche A and 51b aboard; the Weekly of **25 Oct** renders the addendum as a dry-run page if verify item 5 allows, and the Weekly of **1 Nov** is the first edition, as ruled | |

**What it displaces.** Batch 7's Group B (ST-R6.48d and 48e, the PPI and GDP lenses, 8h), which v7 left unscheduled "after Group A", is placed in the week of 2 Nov, after the Monthly. The Tranche 2 ledgers (Batches 5 and 6, week of 26 Oct) keep their week. The item that slips past the 8 Nov finish if Tranche A or the ledgers run long is the Quarterly Structural specification and the 6i brief (week of 2 Nov); they are specifications, not code, and nothing before 1 Nov depends on them. Item 50's Tranche 1 (12h) is placed by the ~31 Oct ruling; the week of 2 Nov is full, so the realistic slot is the week of 9 Nov unless the pilot shows the Drive path failing, which that ruling should weigh. Item 51's Phase 1 does not wait for any of this.

## 7. Verify items

1. MSCI's two-consecutive-period rule as applied to Strategy's FY2024–25 filings (49) — the decisive item.
2. The November 2026 review's effective date on MSCI's calendar (49).
3. xAI API X-search pricing and terms before the Tranche 1 ruling (50).
4. Seed-list handles Grok cannot find on its first v2 run (50).
5. Whether the Sunday 05:00 anchor's build can carry a second rendered page without a change to the publish gate (51).

## 8. Register, voices and sources

**Register:** items 49–51 with round numbers; SR numbers at the next Doctrine sitting, after Batches 5 to 7. 49 also amends the ahead block's event calendar; 50 is recorded as a new input layer under Thread D with PM-template rights; 51 is recorded as the shape of the 7 Sep Alt Asset fold-in.
**Voices:** the X voices ledger (50) is the intake path; no individual voices added by this order.
**New sources:** Strategy dashboard and filings (mNAV, obligations); public treasury-company aggregator; MSCI index review calendar; Grok X digest (Drive); xAI API (Tranche 1, to verify); Deribit DVOL/skew (already in Batch 4).

## 9. Decisions and sign-off

- 49 — ruled 2026-10-17 ("Yes, accept. Because this is coming up November 11, I have to be ready to trade it"); watches and options read requested and delivered the same day ("Yes, do both").
- 50 — design accepted 2026-10-17 ("Yes, I can do that" with Grok connected); Grok prompt v1 and v2 issued and the reader task created the same day.
- 51 — ruled 2026-10-17 ("Yes, I accept your recommendations, and yes, pull forward"), including the Tranche A pull-forward.

Signed: A. Chester, 2026-10-17 (chat rulings as recorded above).
Filing: filed as Batch 8 (see Encoding); commits on `docs-batch-8` after Batch 7; Tranche A and §6 placed by the filing chat below; register entries at the next Doctrine sitting.

## 10. Filing notes (17 Oct 2026, the integration review)

These notes record what the filing review found in the repo at main `1148c66` (after the 25 Friday merges) and on the open branches. They are not rulings. Each one is for the build session to confirm.

1. **The crypto basket is live.** `crypto-basket` merged on 16 Oct (Friday row 19): it stores prices and report lines for BTC, ETH, SOL and ZEC and the twelve-name long-shot basket, with its unit on the box (`chester-crypto-basket.timer`). Item 51's section 2 (the tape) reads it from the start; DVOL, funding, basis, open interest, liquidations and the ETF flows arrive with Tranche A (CD-2, CD-3, CD-4), so until then those cells print "awaiting Tranche A", never a guess.
2. **Farside is referenced, not written.** The report code names Farside in three places but no writer exists; CD-4 builds it. Item 49's "who is buying" decomposition and 51's section 3 read it after Tranche A part 2.
3. **The Drive ledgers reach the box through the sweep.** The pilot's files (`chester-x-digest/x-digest-YYYY-MM-DD.md`, `chester-vendor-checks/x-triage/x-attention-ledger.csv` and `x-voices-ledger.csv`, and from 2 Nov `chester-vendor-checks/mstr-msci-watch/mstr-msci-watch.csv`) are Drive files; the box reads them only after the rclone sweep copies them into `~/chester-data/inbox/`, as it does for the S&P DJI and FlashAlpha files. ST-R6.51a adds the two new Drive folders to the sweep's map and reads the inbox copies, point in time (`available_at` = the sweep's copy time). The reader's push messages are not readable by the box; the ledgers are the record.
4. **MSTR is already a watched name** (`altdata/config.py`), so its price and chain reach the store; mNAV (ST-R6.49a) also needs Strategy's BTC holdings and share count, from Strategy's dashboard or filings and the public treasury-company aggregator. Those are read keyless and within robots or are listed gaps; under the operator's standing rule of 16 Oct no registration is pursued for them. The obligations schedule (49.3) and the event preparation (49.7) are by hand and were ruled explicitly here, which is what the 16 Oct by-hand rule requires.
5. **Verify item 5 is the first thing 51a settles.** The Sunday anchor's publish gate, the Weekly's 10-chart and 3,500-word budgets and the archive layout are per report; the addendum is a second rendered page with budgets of its own (session-set, listed). If the gate cannot carry a second page without change, 51a changes the gate with a fixture and says so.
6. **D1c was lifted on 16 Oct** for append-only writers in the scheduled pulls, so Tranche A's writers (CD-1 to CD-7, all marked "depends on D1c" in the crypto order) build unheld. CD-11 (Dune, a key) and CD-12 stay in Tranche C; nothing here pulls them forward.
7. **The usage-limit failures (§5 note) have a path.** The FlashAlpha Wednesday pull and Thursday reconcile retire when 6b part 3's box-side vendor writer lands (week of 26 Oct, Workplan v7); the AAII read already rides the box's sweep (AUD-1, merging 19 Oct). That leaves the November MSTR/MSCI watch, which should read its FlashAlpha figures from the box's store once the vendor writer is live, keeping only its message chat-side. The 6b part 3 paste carries that line.
8. **Item 50's Tranche 1 needs a paid key** (the xAI API, ≈$40 a month at the pilot's depth per §3). Under the 16 Oct standing rule that is the operator's explicit decision at the ~31 Oct ruling, not a default.
9. **Paper only stands.** Item 49's Book D template is a paper setup logged to the register as a draft, as the order says; sessions never place orders, and nothing in this batch opens an order path.
10. **Only the Weekly addendum is due for 1 Nov.** The Monthly chapter (ST-R6.51c) is due before 1 Dec and is not in the 1 Nov Monthly, whose content freezes on Thu 29 Oct at 23:30.
