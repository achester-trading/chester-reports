# Change Order: the secondary notes (the 09:50 open note and the 21:30 evening note)

| | |
|---|---|
| File | `docs/change-order-secondary-notes-2026-10-19.md` |
| Status | **RULED 19 Oct 2026, 14:14 ET.** Ari: "Accept all", plus one addition for the Sunday edition (D7). Written up the same afternoon against chain-2 and a48-batch11. Section 8 lists four corrections to the 14:08 proposal that the code required. |
| What it changes | It adds two short, optional notes to the weekday cadence. The 07:00 anchor, the 12:30 alert and the 16:45 close remain the reports of record. |
| Why | Audit #3 (6 Sep 2026) and the Daily Cascade paper both specify conditional slots at 09:15 and 21:45, plus Sunday 21:45, and no unit schedules any of them. The Operating Doctrine gives a "1000 report" veto and confirmation rights over the 07:00 list. The Reader's Guide records that as open: "Book C still cites a 10:00 report, which no ruling addresses". This order builds two of those slots at new times, and the open note takes the 1000 report's role. |
| Built by | Session A (paste A49, branch `a49-secondary-notes`) on the third chain. Dry runs come before the first live editions in the week of 26 Oct. |

---

## 1. The open note: 09:50 ET, every trading day

**Purpose.** The open note covers what changed between the 07:00 anchor and the first fifteen minutes of the cash session. It is the Doctrine's 1000 report. It may confirm or cancel Book C's 07:00 list, and it may never add to that list.

**When.**
- **Start:** the run begins after the 09:45 own-engine dealer capture.
- **Delivery:** the note lands by 09:55, inside the 09:05–15:40 window.
- **The 10:30 cutoff:** the note lands before the Doctrine's 10:30 cutoff for Book C entries on volatile-protocol days. After 10:30, an entry needs the 1000 report's confirmation.

**Blocks.** Each block prints its as-of time.

1. **The 08:30 releases.** These are the tier-1 and tier-2 releases in `config/release_calendar.yaml` that are scheduled for 08:30 today:
   - tier 1: CPI, PCE, payrolls, GDP and the refunding;
   - tier 2: PPI, retail sales and jobless claims.

   On a day with none, the block is one line: "No 08:30 release". For each release:
   - **The first print**, in the form the calendar declares for it. FRED's daily pull runs at 16:10, so the note's own pre-step pulls only that release's series. The pull goes through the existing FRED writer, which is vintage-keyed and append-only.
   - **The surprise against the declared naive expectation** (`calc.surprise_vs_naive`), labelled "naive".
   - **"No consensus", with the gap named.** The system holds no consensus for any macro release: no free source serves one, and the surprise index stores none.
   - **Lens 24's "what moved the print" line,** where the release has one.

   If a print is not yet on FRED, the line reads "not yet stored" and names the release. The agency's press item still appears in block 4 with its time.
2. **The reaction,** on release days only. Each instrument's move runs from its last bar before 08:30 to its last bar before 09:45:
   - ES;
   - the 10-year: the yield (^TNX) where its bars cover 08:25, and the note future (ZN=F);
   - the 2-year note future (ZT=F), where Yahoo serves it; otherwise "not tracked";
   - the dollar index;
   - VIX, where its bars cover the window; otherwise from 09:30, labelled.

   No intraday attribution is attempted: the rates attribution lens is daily (its models' 20 and 60 observations), and no new lens is built. The reaction is the market's own verdict on the print, which matters all the more because no consensus exists.
3. **The open.**
   - **The gap:** SPY's 09:30 open against the prior close.
   - **The first fifteen minutes:** their high-low range.
   - **Against the gauge:** both the gap and the range are set against the gauge's implied one-session move. This is the figure the 07:00 anchor printed, from `opening_setup.gauge_from_store`.
   - **Against the levels:** where SPY sits against the flip and the walls, both from the 07:00 anchor's profile and from the 09:45 capture. These are our own engine's levels; no vendor value is read or printed. The sign convention is stated once.
   - **If the 09:45 capture is late:** the note waits a bounded time, then prints "09:45 capture pending".
4. **News since 07:00.** Two sources, both published after 07:00 by the source's own stated time:
   - the agencies' press items (Fed, BLS, BEA) from the events ingest's news source;
   - the voices scan's items, from a short pass before the note. The pass runs inside the scan's existing daily cap of 60 model calls, so no new budget is needed.

   At most five items, each with its outlet and time. The rule is "no stored source, not printed".
5. **Book C.** Each 07:00 Book C draft is confirmed or cancelled, with the reason the rules give. Until the 07:00 anchor carries Book C drafts, the block prints "No Book C drafts: the 07:00 setup list is not built". It never adds a draft.
6. **What the close will check.** One line naming the levels and the release reactions that the 16:45 close re-reads.

**Reading target.** Two minutes.

**Prose budget.**
- **When prose is written:** at most 250 words, written by the model only when the gate opens. The gate opens on any of:
  - a tier-1 08:30 release;
  - a gap or a first-fifteen-minute range beyond the gauge's implied one-session move;
  - a volatile-day trigger printed by the 07:00 anchor (the vol rule's line in `altdata/vol_event.py`, which is printed and never applied).
- **Otherwise:** no prose, and every line is code-written.
- **Charts:** at most one, ES since 08:25 on release days.

---

## 2. The evening note: 21:30 ET, Sunday to Thursday

**Purpose.** The evening note covers what has happened since the 16:45 close: after-hours earnings, US futures, Asia's open, currencies, crypto and news. It prepares tomorrow's 07:00 anchor. It has **no rights over any book**. Its default line is "Nothing to do tonight; the 07:00 anchor re-reads all of this."

**When.**

| Event | Until 1 Nov (EDT) | From 1 Nov (EST) |
|---|---|---|
| Tokyo and Seoul open | 20:00 ET | 19:00 ET |
| Hong Kong and Shanghai open | 21:30 ET | 20:30 ET |
| PBoC fix published | 21:15 ET | 20:15 ET |

- **Hong Kong and Shanghai before 1 Nov:** they open at the note's own time, so until 1 Nov the note may see only their first delayed bars, or none, and it says so.
- **Which evenings:** the note runs on an evening before a session. The session guard reads the next day, so a Friday-night note never runs.
- **Window:** 21:30 is inside the 17:20–23:30 window.

**Blocks (weekdays).** Each block prints its as-of time.

1. **US futures.** ES, NQ and RTY, each from the 16:00 ET cash close and from its last trade before the 17:00 halt. RTY=F is added as a keyless Yahoo symbol and registered.
   - ES is set against the ES block's levels for tomorrow, as the 16:45 close printed them.
   - ES's move in percent is set against the gauge's implied one-session move.
   - Dealer levels are not printed in ES terms until ST-R6.45c is built (it waits on 6b), as the ES block's own prompt already says.
2. **After-hours earnings.** This covers each captured name whose stored release time today is after the close:
   - reported EPS against the analyst mean (yfinance), once yfinance serves it; the earnings ingest re-runs before the note;
   - the after-hours move, from yfinance's pre- and post-market bars where served, set against the implied move the Ahead rows use (`daily_cascade.ahead.implied_move`). That implied move is event-only where an expiry before the report exists, and otherwise the full straddle, labelled.

   Where no after-hours price is served, the line says so. It is never a recommendation.
3. **Asia's open.** The Nikkei 225 (already fetched), the Hang Seng, the Shanghai Composite and the KOSPI (added and registered). Each is set against its prior close, with its as-of time.
4. **Currencies.**
   - dollar-yen;
   - dollar-yuan offshore, from the CNH hourly bars;
   - the PBoC fix for the next Beijing date, where published, against the prior onshore close;
   - the yen-unwind and devaluation hooks, evaluated as the 12:30 slot evaluates them (`daily_cascade/funding_hooks.py`). They are descriptive only; no new flag.
5. **Crypto since 16:45.**
   - BTC and ETH.
   - Aggregate perp funding (`calc.funding_agg`), as last stored.
   - The crypto data-sources order's evening ETF-flow refresh, which never had a run to live in, lives here. While Farside is a listed gap, the line reads "ETF flows: gap".
6. **News since 16:45.** As the open note's block 4, from 16:45.
7. **Book D.** Tonight's drafts from the meme ingest (moved to 21:15, section 5): their count and names. They are decided at 07:00; this block only reads them.

**The Sunday edition (D7)** keeps the blocks above and adds two.

- **The futures open against Friday.** This covers ES, NQ, RTY and the 10-year future (ZN=F):
  - **Friday's reference prices:** each future's 16:00 ET price and its last trade before Friday's 17:00 halt.
  - **The opening move:** from those prices to the first bar after the 18:00 reopen.
  - **The path since:** the high, the low and the latest.
  - **Against the gauge:** each move in percent, against the gauge's implied one- and five-session moves as of Friday's close.
  - **Against the levels:** ES against the ES block's levels from Friday's close.
  - **The currency gap:** dollar-yen's weekend gap goes beside the futures, from Friday's New York close to Sunday's open.
- **The weekend's news, in two parts:**
  - **First, what is new since the 05:00 Weekly** (Sunday 05:00 to 21:30).
  - **Then Friday 16:45 to Sunday 05:00.**

  Today, nothing ingests news between Friday's 16:10 pass and this note's own pass. The voices scan runs on weekdays only, and the events ingest runs at 06:45 and 16:10 on weekdays. So the Weekly cannot see the weekend at all, and the note's pass is the weekend's first. Items are split by each source's stated publication time, which is printed beside the item. The store's ingest time is stated once for the block.

  Each item says whether the futures open is consistent with it, as a description and never a cause ("attributions, not causes").

  Session A measures whether any feed's window rolls before Sunday evening. If one does, the notes propose a Saturday news pull, for Ari's yes.

**Reading target.** One minute on weekdays, three on Sundays.

**Prose budget.**
- **Weekdays:** at most 150 words, only when the gate opens. The gate opens on any of:
  - an earnings night for a captured name;
  - ES or NQ beyond 0.75% from the 16:00 close;
  - dollar-yen beyond 1%;
  - an Asia index beyond 1.5% from its prior close;
  - a yen or devaluation hook reading as tripped.

  These thresholds are starting values. They are session-set in config with their reasons and listed for Ari, not measured. Otherwise there is no prose.
- **Sundays:** the gate is always open, because the weekend is a long window. At most 400 words.
- **Charts:** at most one. On Sundays, ES since the 18:00 reopen; on weekdays, ES since 16:00 when the gate is open.

---

## 3. Rules common to both notes

- **They are secondary, while Book C is inactive.** Skipping a note loses nothing today, because the 07:00 anchor and the 16:45 close re-read everything material. One honest exception comes later. The Doctrine makes the 1000 touch mandatory on volatile-protocol days, and it forbids Book C entries after 10:30 without the 1000 report's confirmation. Book C is not active: Gate C has not passed, and no drafts exist. Once Book C activates, the open note is mandatory on those days under the Doctrine as written. Doctrine #2 decides whether that stands.
- **What neither note does:**
  - create a packet, a candidate, a flag or a tell;
  - write to the decision register or place an order;
  - enter the market-state object;
  - compute a regime (the one-regime rule): each note reads the stamp the 07:00 anchor or the close printed.

  The open note's only right is to confirm or cancel Book C's 07:00 drafts. The evening note has none.
- **The subject line carries the verdict.** It is code-written from the note's own payload and passes the numeral audit. For example:
  - "Open note: CPI +0.4% m/m; 10-year +9bp since 08:29; open inside the expected move"
  - "Evening note: quiet"
  - "Sunday night: ES +0.3% vs Friday; two items since the Weekly"
- **The same machinery as the anchors:**
  - **The split:** a fetch step writes to the store, and the payload is built from the store. Reports never fetch.
  - **Prose:** written through `narrative.generate()` under the model meter, with the numeral audit and binding, the one-revision retry, and the withheld-with-reason behaviour.
  - **Budgets** live in `config/reporting_stack.yaml`.
  - **Output:** the archive (with `dryrun/` for dry runs) and the anchors' mail path, `daily_cascade/deliver.py`.
- **As-of times are printed for every block.** Each source's delay is stated once per note.
- **Sources: keyless and existing only.**
  - No vendor value is ever printed or read. The vendor's 09:45 and 12:30 slots stay in the store for the divergence gate.
  - No new by-hand line (rule 30), no SpotGamma material, and no figure from any third-party paid report.
- **Holidays and half days:** the session guard decides. The open note runs on session days. The evening note runs when the next day is a session, so a half-day session's evening note runs as usual.
- **The heartbeat** names a missed or failed note as a warning, never as a failure.

---

## 4. The two ledgers

Both are pre-registered before any scoring code is written. Both are report-only: they grant nothing and build no composite.

1. **The release-day first hour.** On each tier-1 and tier-2 08:30 release day, for ES and the 10-year:
   - **The measure:** the move from the last bar before 08:30 to 09:45, against the move from 09:45 to the 16:00 close. The result is the share that continues, by release type and by the sign of the naive surprise.
   - **The pass rule** is pre-registered.
   - **Two samples, read apart:**
     - the first edition, from Yahoo's hourly bars (about two years): 08:00 to 10:00 against 10:00 to 16:00, labelled with its bar size;
     - then the open note's own stored readings, under the registered definition.
2. **After-hours earnings.** For each captured name that reports after the close, the question is continuation or fade.
   - **The first edition** uses five years of daily bars as a labelled proxy: the close to the next open, against the next open to the next close.
   - **Then the note's own readings accrue:** from 16:00 to 21:30, against the next session. The two samples are read apart.

---

## 5. The meme ingest's time

chester-reports' own notes say that chester-meme's 19:30 evening scan finishes by about 19:45, and that the contract reads after 20:15 (`scripts/run_meme_ingest.sh`, `altdata/meme_ingest.py`).

- **The move:** the ingest moves from 21:45 to 21:15, after the contract's time and still inside the window, so the evening note can show tonight's Book D drafts.
- **Taking effect:** the timer is printed and never enabled by a deploy, so the change takes effect when Ari reloads and restarts it.
- **If it is not safe:** if session A finds a reason in chester-reports' code that makes the move unsafe, the ingest stays at 21:45, and the note says "Book D drafts arrive at 21:45".

Session A does not open chester-meme's repository.

---

## 6. Placement

- **Session A, paste A49:** branch `a49-secondary-notes`, from a48-batch11's final tip, on the third chain.
- **Timers:** `chester-open-note.timer` (Mon–Fri) and `chester-evening-note.timer` (Sun–Thu).
  - Neither is in `DEPLOY_TIMERS`.
  - Ari enables both by hand after the merge, like every new daily line.
  - The units follow AUD-2's conventions (memory caps as shares of the 4 GB box, the OOM order, a start timeout) and the state-directory rule chain-2 set.
- **Dry runs:** `live_from: 2026-10-26` in config. Before that date every run is a dry run: archived under `dryrun/` and mailed with "[DRY RUN]" in the subject so Ari can read it.
  - If the third chain merges after Thursday 22 Oct, the merge sheet moves `live_from` later. At least two weekday dry runs of each note and one Sunday dry run must come first.
- **The Master Guide** (session B's `master-guide` branch) shows both notes as secondary, "ruled, not built", until this branch merges. Its list of Doctrine gaps drops the 1000 report as unruled. Whichever branch merges second carries the rows the Guide's gate needs.
- **Doctrine #2 (7–8 Nov):**
  - the Doctrine's 1000 report becomes the open note's text, by Ari's ruling;
  - the mandatory-touch question in section 3;
  - the Doctrine also names the 1000 report as a Book D touch. The open note carries no Book D block, so this is listed for that ruling.

  This order does not edit the Doctrine.

---

## 7. Decisions, as ruled 19 Oct 2026, 14:14 ET

- **D1:** the 09:50 open note, every trading day. It takes the Doctrine's 1000-report role: it confirms or cancels, and never adds.
- **D2:** the 21:30 evening note, Sunday to Thursday, with no rights over any book.
- **D3:** code-written lines every time. Model prose only when a release, an earnings night or a gate calls for it, and always on Sundays. A verdict in each subject line.
- **D4:** the two pre-registered ledgers in section 4.
- **D5:** the meme ingest moves earlier where the export time allows (section 5: 21:15).
- **D6:** session A builds both after A48, with dry runs before the first live editions in the week of 26 Oct. The Master Guide shows them as secondary notes.
- **D7 (Ari's addition):** the Sunday edition studies the Sunday futures open and its first movement against Friday's close. It adds a summary of the weekend's market-moving news, with what is new since the 05:00 Weekly first and separate.

---

## 8. Corrections to the 14:08 proposal, found while writing this order against the code

1. **"The print against consensus" cannot be built.** No free source serves a macro consensus, and the surprise index stores none, so the note prints "no consensus" with the gap named. It shows the print, its naive surprise (labelled) and the market's reaction instead. Earnings do have a consensus, the analyst mean, and the evening note uses it.
2. **Dealer levels in ES terms are not built** (ST-R6.45c waits on 6b). The futures blocks therefore read the ES block's own levels, plus percent moves against the gauge.
3. **The futures reference prices are the 16:00 cash close and the last trade before the 17:00 halt,** not a "17:00 settle". ES settles at 16:00 ET.
4. **The weekend has no news ingest at all.** So "since the Weekly" means everything since Friday's 16:10 pass. The Sunday note's split by publication time is what separates the morning from the day.
