# Audit #4 — 14–15 October 2026 — agenda

| | |
|---|---|
| Status | Drafted 9 Oct 2026 for the sitting. Items 1–2 were placed here by earlier rulings; everything else is what the four ruled-but-unplaced orders, the Enterprise Layer's §4 and the Reader's Guide's Appendix D put on this sitting's business. Rulings are taken in chat, one item at a time, and recorded in `docs/briefs/audit-4-minutes.md`. |
| Owner | Ari Chester |
| Shape | Two sittings of at most two hours (Wed 14, Thu 15 Oct); the week's review sitting under the attention budget. Freeze Tue 13 Oct 23:30 ET; the box runs on 8fa972e; code on branches continues. |
| What a "yes" costs | Shown per item in session hours, and in Part VII against the calendar at the 2× pace (40–50 session-hours a week, two sessions in parallel). |

**The test applied to every build item, item by item:** *would this have changed or graded a decision in the last 90 days, and does it have a date on which it will be tested?* Yes to either → build. No to both → a LOG row with its reopen condition. Finer resolution of something the store already measures → conditional, with a named trigger.

---

## Part I — Standing items (Enterprise Layer §4, EL-7)

| # | Item | What is needed at the sitting | Recommendation |
|---|---|---|---|
| I.1 | **§1 of the Enterprise Layer order updated to the repository at 14 Oct** (the table of what the two specs asked for, what exists, what the order adds) | A read-only session produces it as §1 of `docs/chester-reports-audit-4.md` before the freeze (~1 h, Tue 13 Oct, docs commit) | Paste follows this agenda; the sitting reads it, does not write it |
| I.2 | **The simplification question, verbatim:** *if we rebuilt today, what would we remove, combine, automate, simplify or add?* | Ari's answer, recorded; 15 minutes | Three candidates to put against it: the Alternative Asset report layer (`altdata/report/`, seven of thirteen modules do not import — fold or delete at the redesign); the Monthly v2 fallback renderer once the stacked edition has run three times clean; the Saturday crypto scan once Thread D's Weekly block prints (MW-9) |
| I.3 | **System-metrics block, first reading.** EL-6 is not built (after 6b), so the first reading is by hand from the heartbeat, the incidents file and the deploy log | Numbers compiled before the sitting (I bring them): days up since the 7 Oct reboot; feeds current / declared (the 9 Oct line: official 96/96, external 52/5x, one stale — AAII, operator drop); incidents INC-1…INC-9 with the one open; sessions-hours this fortnight; model cost | Record as the baseline row EL-6 will reproduce |
| I.4 | **DTH-1 scope re-examined "with 6b's first captures in hand"** | 6b builds the week of 20 Oct; there are no captures yet | **Defer to Doctrine #2 (7–8 Nov)** with 6b's first week stored; the first engine stays the dealer-positioning / 0DTE engine as ruled on 2 Oct (Doctrine item 5) |
| I.5 | **Amendment number confirmed; the architecture Part written** | Enterprise Layer = **Post-Freeze Amendment #5** (confirm); a library session writes the Part (EL-7, 1 h) after the sitting | Confirm |

---

## Part II — Rulings carried to this sitting

1. **Re-engagement of Book A into the Overheat band (Doctrine item 1c).** The macro dial changed expansion → overheating on 1 Oct; the 10th session is 14 Oct. Under the crossing rule Book A is in Transition (60–70%, hedged, cross-book net-beta cap 85%) until this sitting rules. *Needed:* the 13 Oct close's dial line (Ari pastes it Tuesday evening). *Rule:* if the dial still reads overheating, re-engage into the Overheat band (net-beta cap 75%, the Doctrine's Overheat rules); if it has reverted or reads mixed, nothing to rule and Transition stands. Applied by the D-2-style config session (`regime_mapping`, 15 min).

2. **Scenario set #1** — the first scenario register (five scenarios, weights, signposts), ruled before the 23 Oct dry run; the Monthly's scenario block and the prediction-market disagreement (20 points) have nothing to compare against until it exists. *Needed:* a draft of the five, which I bring Monday 12 Oct from the regime object, the tail register and the narrative register. *Sitting:* ≤ 30 minutes, weights summing to 100, one signpost per scenario with its series. Applied as the first `monthly_macro` rows in the probability ledger (session, 1 h; a register write under Ari's own line).

3. **Book B's setups and the Friday-close scanner.** `config/setups.yaml` holds thirteen families (A 2, B 3, C 3, D 5) plus `unclassified`, each with its Doctrine passage. The Weekly prints "0 drafts" because nothing writes them. *Rule (a):* ratify the thirteen as the list (or name the family that is missing). *Rule (b):* commission the scanner — reads Friday's close, writes Book B candidates to the register as drafts with level, invalidation, time stop, falsifiers and the gate's pre-check (~10 h). *Placement:* week of 20 Oct beside 6b and 6e, so the 25 Oct Weekly is the first with candidates. The seven-a-week budget counts approvals, not drafts.

4. **Symmetric two-session close for contradictions (rules v1.13).** In the code a contradiction closes on the first session its condition fails; the documents say two. Ruled for this sitting (Reader's Guide item 6). *Rule:* bump `config/market_state.yaml` to v1.13 with a two-session close, method unchanged; the change ledgered with its first month's effect on the contradiction count. Applied in the 6e session (1 h).

5. **Register numbers after SR-36, in filing order** (the filing lines of 6 Oct bind this). Proposed assignment, to be written into the three files and `docs/signal-triage-register.md` by the post-audit filing session (~2 h):

| Order | Entries that take new numbers | Numbers | Amendments to existing entries |
|---|---|---|---|
| GTM batch (ruled 3 Oct) | GTM-1, 3, 4, 8, 9, 10, 11, 12, 13, 14, 15 | **SR-37 … SR-47** | SR-9 (GTM-7), SR-16 (GTM-16), SR-5 (GTM-21) |
| Crypto Thread D (ruled 6 Oct) | S-2, S-3, S-4, S-5 | **SR-48 … SR-51** | SR-20 (S-1 stablecoin rows), SR-29 (computed with fallback) |
| Batch 4 (draft, 6 Oct) | its SR-37…SR-49 | **SR-52 … SR-64** (same order) | SR-30 (OAT > BTP marker), batch-2 oil entry |

Encoding: batch 3 = Batch 3 of Amendment #4 (confirmed); crypto = Batch 4; the 6 Oct draft = **Batch 5** (its §8 decision 1); the GTM order = **Batch 6** of Amendment #4, so no file renumbers its own batch. SR-30's crisis tier: set at the ST-B3-03 build from the series' own November-2011 weekly-close peak (≈ 190 bp), printed as "crisis (2011 peak)" until the ST-B3-09 ledger confirms it. SR-30's data source for the series itself (the entry cites a chart): the Bundesbank and Banque de France open-data APIs, daily, free, official, to a weekly close; FRED's OECD monthly long rates as the backfill and cross-check. The two r2 base-rate rows: levels verified by the session that files the by-hand rows, against the sources the rows cite.

6. **The Reader's Guide's open items** (Appendix D; six open, four fixed in part). Item 12 (the Monthly's timer enabled by hand) was closed by A-4 on 9 Oct — record it.

| # | Open item | Rule |
|---|---|---|
| 16 | The Monthly signal scan's rights are not ruled (the brief gave it a voices entry) | The scan has **no rights**: it proposes; adopted items become that month's batch; a voices line from it enters the Phase B register only with a stored source, like any other |
| 18 | Book Z is three benchmark ledgers; the Doctrine names only 60/40 | The Doctrine names the three (cash, SPY, 60/40); library session, 30 min |
| 19 | The entry gate refuses four limits; per-position tiers, book loss stops, the kill-switch ladder and the heat cap are reported, not refused | **Tiers and book loss stops become refusals** (the gate extension, ~3 h, inside EL-1's scope); the kill-switch ladder and the heat cap stay reported until heat is computed (item 20) |
| 20 | "Heat" is a factor view in the code and open risk to invalidation in the Doctrine; the second is not computed | Rename the code's view *factor exposure*; compute heat as the Doctrine defines it from each packet's invalidation level (EL-1 makes the level a required field; ~3 h with item 19) |
| 21 | Reconciliation's comments say hourly against a 30-minute timer | LOG: fixed by the next session that touches the file |
| 22 | "Never orders" (Doctrine) against the Enterprise Layer's paper bracket orders (EL-13) | **Never orders stands for the engines** (ledger entries graded against stored bars, ruled 2 Oct). EL-13's bracket-order wording is amended to "paper orders through the order gate only, and only after Gate 1.5"; EL-13 is gated anyway. No order path of any kind before the Gate 3 ruling |
| 23 | Book C cites a 10:00 report that does not exist | The Doctrine cites the 10:30 slot; library session, 15 min |
| 4, 10 | Observed times unwritten; the Quarterly Structural has no specification | Open; nothing to rule. The Quarterly Structural's specification is a brief for after 6b |

---

## Part III — The four orders, sorted

Ruled-but-unplaced work on 6 Oct: GTM 24 h, batch 3 51 h, crypto 25 h, batch 4 ≈ 38.5 h, plus the Enterprise Layer's Tranche A (20–30 h) and the signal-triage order's Tranche 1 (≈ 33 h), which **go first regardless** — they are the grader and the ledgers that make the rest gradeable, and their place in the order of work is already ruled. What follows sorts the four orders. Hours are the files' own.

### Category 1 — build (a yes commits the hours; ranked)

| Rank | Item | Hours | Why it passes the test | Lands (Part VII) |
|---|---|---|---|---|
| 1 | **Store-wide move screen** — every daily series in the store, 1-day and 5-day change against its own five-year history, past 2.5σ prints one line in *What doesn't fit* with the false-flag base rate beside it. Subsumes SR-35 (ST-B3-01), SR-46(a) and the prediction-market shock flag | **3** | Would have caught the Brazil move; general where the entries are bespoke | Week of 20 Oct |
| 2 | SR-36 Treasury basis-trade proxy: the CFTC TFF series and tiers (ST-B3-12) + its calibration ledger (ST-B3-14) | 3 + 3 | Names the fragility that turns a vol shock into a liquidity break; the fetcher exists; tested at every Friday print | 23 Nov block |
| 3 | SR-43 and SR-49: 10y inflation anchor, twin-deficit fit with the WEO/OECD fetcher, selloff shape axis on `rates.driver` (ST4-08, 09, 15) | 7 | Adjudicates the four-voice disagreement instead of narrating it | 23 Nov block |
| 4 | SR-37 and SR-38: AI FCF-transfer panel and return attribution (ST4-01, 02) | 8 | Test dates: the late-October hyperscaler prints and the 28 Oct FOMC | **Decision 8:** pull ahead to the week of 20 Oct if a session has room (Part VII says it does), else first in the 23 Nov block and tested on the stored prints |
| 5 | SR-46(b–d): EM dispersion, EM spreads, the contagion rule, on top of the move screen; the EM calendar seed by hand | 3 (+1 by hand) | Approved 6 Oct; the Brazil miss | Week of 20 Oct, with the screen |
| 6 | Crypto Tranche A as ruled (D-3…D-8): `llama` (S-1), Farside (S-2), Hyperliquid + Bybit + OKX (S-3), DVOL (S-4), GeckoTerminal froth (S-5, D-5 "build now so history accrues"), mempool/Etherscan/global/F&G, the derived series, the Weekly and Monthly blocks, validators, Dune (D-6), bitcoin-data (D-8) | 27.5 by the rows (the file's own total says 23–25) | The private-dollar leg and the leverage read, which nothing in the stack sees; all free | 23 Nov block; the daily paragraph (CD-9's 4 h) waits for D4/D6 |
| 7 | GTM core: GTM-4 cash-flow bridge, GTM-1 inflection table, GTM-8 and GTM-9 base rates, GTM-13 rate scenarios, GTM-7 (amends SR-9), GTM-15 tariff rate and GTM-21 DSR (two cheap FRED series) | 19 (6 + 2 + 2 + 2 + 3 + 2 + 1.5 + 0.5) | Mechanism gaps with free data; the base-rate rows have dates | 23 Nov block |
| 8 | Batch 3 Tranche A, as ruled 6 Oct: SR-6 tenor lens, SR-30 OAT–Bund, SR-33 buybacks, SR-34 MoF/FIMA, the hyperscaler differential (after its batch-2 parent), SR-32's oil update, the 30y JGB line | 19 | Already ruled "build now"; each carries a dated test (French budget votes, buybacks to 4 Nov, BoJ 30 Oct, EIA weekly, Aramco Q3). Its "1 Nov Monthly" target cannot hold with 6b and 6e in front; **the target moves to the 1 Dec Monthly** | 23 Nov block |
| | **Total** | **≈ 90 h** (≈ 60 h of the new items as estimated on 6 Oct, 19 h of batch 3's already-ruled Tranche A, 3 h of the screen, and the crypto rows above the file's own total) | | ≈ two weeks at the 2× pace |

### Category 2 — conditional (the hours are estimated; the build is a one-line decision when the trigger fires; reviewed at Doctrine #2 and Audit #5)

| Item | Hours | Trigger |
|---|---|---|
| SR-45 constituent breadth + RSP/SPY (ST4-11) | 4.5 | The first Weekly where *What doesn't fit* or a reader notes narrowness the sector breadth missed (the Reader's Guide already says it understates it — likely the first to fire) |
| SR-42 copper COT (ST4-07) | 2 | A metals thesis on the book, with the SR-36 fetcher built |
| SR-48 diesel (ST4-14) | 1 | A sitting asks for it |
| SR-41 reflexive flag (ST4-05) and buyback efficacy line (ST4-06) | 4.25 | SR-36's unwind-watch exists (ST-B3-15, after D4/D6); buybacks series built (ST-B3-04) |
| SR-40 MOVE-leads-liquidity early state (ST4-04); the lagging-leg proxy study | 3 + 3 | Its slot in the one-at-a-time T&B overlay queue; the proxy only if the MOVE leg earns a ledger |
| SR-39 yield-peak / shakeout conditional (ST4-03) | 3 | A top-signal reading from the T&B (the conditional is a bottom test) |
| Batch 3 Tranche B: the SR-32 family and parser, the SR-30 and SR-32 ledgers, the chain cross-check, the SR-29 LTH study, the SR-36 unwind-watch rule (ST-B3-07…11, 15) | 25 | Its own ruling ("backtest before panel"): each after its Tranche-A series has a quarter of history |
| GTM-3 concentration twin (queue), GTM-10 sector correlation, GTM-12 federal finances | 7 | GTM-3 at its queue slot; the others when a sitting asks |
| Crypto daily paragraph and the 12:30 line (CD-9 part B) | 4 | D4/D6 |
| OCC daily options volume (batch-4 decision 7b) | 1.5 | Only if 6b's OPRA feed does not already carry it — expected redundant |
| **Total** | **≈ 58 h** | none committed today |

### Category 3 — LOG rows and by-hand items (zero build hours; each row carries its reopen condition so the next circulating chart is diffed against it)

- **LOG as proposed:** GTM-5, 16, 17, 18, 19, 20, 22, 23 (sourced figures through the scans ingest); batch 4's "seen, no entry" items 8 and 14, Market Vane, pattern annotations; crypto DS-5, 10, 25, 27, 31, 36.
- **By hand, adopt (cheap, once):** the §4.4 intake rule (a level claim carries its percentile among comparable dates); the EM calendar seed; the SR-44 and 1994 base-rate rows; the OAT > BTP marker; the Book C intervention-bounce rule; batch 3's base-rate rows and voices entries; crypto's unlock schedules and the two `.env` keys. ≈ 8 h of Ari's time in all, spread over a month.
- **Drop:** SR-47, the private AI-financing ledger (batch-4 decision 6) — a by-hand register with a quarterly entry forever, for a modifier that needs four quarters before it has rights. The Factor I revenue-leg log (§4.5, one line a quarter) covers the question.

---

## Part IV — Batch 4's ten §8 decisions (the file is a draft until these are taken)

| # | Decision | Recommendation |
|---|---|---|
| 1 | Encoding | Batch 5 of Amendment #4 |
| 2 | SR-37 data | Trailing FCF from filings now, labelled; forward consensus when a free source exists |
| 3 | SR-41 thresholds | **Own levels** from 20-year percentiles, with Visseau's round numbers printed as the sourced reference — the system's convention |
| 4 | SR-43 interim | Carry the 5.8%-vs-5.3% as a sourced figure under the intake rule until the fetcher is built |
| 5 | SR-45 build | Accept the labelled survivorship build as the specification; **placement conditional** (Category 2) |
| 6 | SR-47 | Drop (Part III) |
| 7 | Recap housekeeping | SPR series + draw-streak lens, yes (0.5 h, with the oil update); OCC volume conditional on 6b |
| 8 | Placement | Default, with the ST4-01/02 pull-ahead taken as its own yes/no against Part VII |
| 9 | SR-40 lagging leg | Leave the proxy open |
| 10 | The rest | As proposed in §5 |

---

## Part V — Small items that need one word each

| Item | Hours | Recommendation |
|---|---|---|
| **FlashAlpha cross-check rewire** (ledger of 9 Oct): compare their GEX with `dollar_gamma_per_1pct` and their DEX with a raw-signed DEX the engine does not yet print; VEX keeps its flag | 1 | Yes, in 6b |
| **Box-side vendor writer**: the box calls FlashAlpha's REST at 16:25 with a key in `.env`, stores `dealer.vendor_*` beside ours, a data gate flags divergence; retires the two chat-side scheduled tasks | 3 | Yes, in 6b; the key is Ari's to create and place |
| **Dealer charts as a tool** (`tools/dealer_charts.py`: per-strike, gamma profile, buckets and release, DEX horizon) feeding the Monthly's dealer retrospective | 2 | Yes, in 6b |
| **The "other" expiry bucket**: later-week Fridays and month-ends sit in "other" (29% of SPY |GEX| on 8 Oct) because the engine buckets by DTE window | 1 | LOG; rename or split when the retrospective's first month shows it matters |
| **Workplan v4** (the 2× calendar ruled 6 Oct) exists only in chat | 1 | File it at the post-audit filing session with the dates this sitting confirms |
| **Audit #5** | — | Mid-December, after the Category 1 block; its brief carries the simplification question and the first EL-6 block |

---

## Part VI — Attention log

The sitting counts as the week's review sitting (≤ 2 h; record the hours). Packets approved this week: 0 of 7 (nothing drafts them yet — Part II item 3). Rulings taken in chat this week, for the Weekly's third count: the FlashAlpha connector and its two scheduled tasks; lbma.py kept; the ledger. Doctrine #2 (7–8 Nov) sets the cap from a month's data.

---

## Part VII — Where the "yes" column lands (2× pace, two sessions, 40–50 h a week)

| Week | Session work | Sittings and anchors |
|---|---|---|
| Wed 14 – Thu 15 Oct | Freeze (box only); sessions read-only. The §1 table (I.1) committed Tue before 23:30 | **Audit #4**, two sittings |
| Fri 16 – Sun 18 Oct | Post-audit filing session (~2 h): numbers, §8 rulings into the batch-4 file, Workplan v4, minutes. 6b brief read. The cloud-sessions decision (the box already self-deploys code) | Sun 18 Oct Weekly (T2.8 notes) |
| Mon 19 Oct – Sun 1 Nov | **6b** (A, ~12 h; feeds bought that week) and **6e with the lenses + v1.13** (B, ~20 h); the Book B scanner (~10 h); the move screen + EM (b–d) (~6 h); SR-37/38 if pulled ahead (~8 h). ≈ 56 h against ≈ 90 h of capacity; Monthly dry runs Fri 23 and Wed 28; **freeze Thu 29 23:30** | Sun 25 Oct Weekly — first with candidates; **Sun 1 Nov Monthly** |
| Mon 2 – Sun 8 Nov | 6b finish and deploy; the dealer engine registered (EL-12 registration only); 6f; Quarterly Structural + 6i brief | Tue 3 Nov midterms graded; **Doctrine #2 Sat 7 – Sun 8 Nov** (DTH-1 scope, the Category 2 triggers, the attention cap) |
| Mon 9 – Sun 15 Nov | **Enterprise Layer Tranche A** (EL-1…EL-6, 20–30 h), with items 19 and 20 inside EL-1 | |
| Mon 16 – Sun 22 Nov | **Signal-triage Tranche 1** (ST-0…ST-6, ≈ 33 h nominal; ST-0, ST-1, ST-2 and ST-3's attribution block shipped in late September, so ≈ 15 h remain — ST-4, ST-6, ST-3's remainder — after the session reconciles what exists) | |
| Mon 23 Nov – Sun 6 Dec | **Category 1 block** (≈ 80 h after the week-of-20-Oct items): SR-36, SR-43/49, crypto Tranche A, GTM core, batch 3 Tranche A, SR-37/38 if not pulled ahead | **Sun 1 Dec Monthly** — first with batch 3's standalone series |
| Mon 7 – ~Tue 15 Dec | Slack for slippage; 6m Thailand; library track resumes | **Audit #5** mid-December |

If a week runs short, the Category 1 block slips, never the two anchors (1 Nov Monthly, Audit #5's brief).

---

## Before the sitting

| Who | What | By |
|---|---|---|
| Ari | Sunday's Weekly read → T2.8 notes; the Monthly dry-run notes → T3.1; Saturday's AAII drop; Tuesday evening, paste the 13 Oct close's dial line | Tue 13 Oct |
| Claude (chat) | Scenario set #1 draft (Part II.2); the system-metrics numbers (I.3); the §1-table paste for a read-only session (I.1) | Mon 12 – Tue 13 Oct |
| Session A or B | Commit the §1 table as `docs/chester-reports-audit-4.md` §1, docs only, before the 23:30 freeze | Tue 13 Oct |
