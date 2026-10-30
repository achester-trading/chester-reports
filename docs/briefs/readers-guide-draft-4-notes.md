# readers-guide-draft-4: the Reader's Guide, Draft 4 (session A, A69, 24 Oct 2026)

**What this branch is.** Draft 4 of Companion XXXIII, *The Reporting System: A Reader's Guide*. It is on `a69-readers-guide-4`, branched from `origin/a68-dated-appendix` at `f6abeca3`.
- **The base** carries chain-7 (`62c19b41`) and the 24 Oct rulings, plus three later branches: a65, a66, and the docs-only a67/a68.
- **The feed repair** (`origin/a61b-feed-repair`, `0d954d0f`) is not in the base. It was read by name with `git show`.
- **"Built"** means on chain-7 or a61b, as the brief rules. a65's weekly alignment stamp and a66's capex-guidance reader are on later branches, so the paper puts them in Appendix E.
- Branch only: nothing merged, nothing deployed, nothing on the box.

**A68's CI at A69's start.** Run `40148995333` (on `f6abeca3`) was queued and was not waited on. Whichever paste next touches `a68-dated-appendix` reads it.

## Method

Draft 3's method was followed. The brief names its files as `readers-guide-draft-3-update-2026-10-18.md` and `readers-guide-draft-3-notes.md`; neither exists on any branch. Draft 3's notes are `docs/briefs/library-draft-3-notes.md`, and that file was used.

**How the claims were checked.** Every claim about what exists was checked against the code and config on the branch, and on a61b where it changes them. Three read-only sweeps covered the data layer, the reports and regime, and the scans, learning and appendices. Each cited file and line.

**The rules applied:**
- Where a notes file and the code disagree, the paper follows the code, and the difference is listed below.
- The body stays timeless: every timer, threshold, budget, count and source is in Appendix A, dated 24 October 2026.
- No market view anywhere.
- No names of people. The three references Draft 3 made by a person's name now name the library or workbook ("the Tuck data library", "a university data library", "the shillerdata.com workbook").

## The commits, one per Part

| # | Commit | What |
|---|---|---|
| 1 | `276cf7ea` | The status line ("Draft 4 — 24 October 2026; as built on chain-7 and a61b-feed-repair, ahead of their merges (a61b 27 Oct; chain-7 after the 1 Nov Monthly)") and the errata block |
| 2 | `7767a4ac` | Part I: §1.1's cadences name the two secondary notes |
| 3 | `941099a2` | Part II: the feed families as the registries read them; new §2.7, declared statuses, publication lags and inheritance, "dead?", the purge (backups move to §2.8) |
| 4 | `37491866` | Part III: the object v2 (five dimensions, two absent, SKEW, the symmetric close); new §3.9 horizons, §3.10 calibration, §3.11 tail families and the debt-cycle branch, §3.12 the bar |
| 5 | `3e421003` | Part IV: §4.7 as "The anchor, the two notes, the 12:30 slot and the close", with the event area; §4.10's table; the budgets as targets (§4.6, §10.1); M0–M13; the Quarterly |
| 6 | `833ca747` | Part V: the audits unchanged; the storyline writer's one revision merged; length no longer an audit |
| 7 | `3a703885` | Part VI: the X digest's three files and reader, the seed-list batch, the outlet rule, the CMA files, the Monthly signal scan, the MSTR watch, the ingest at 21:15 |
| 8 | `a25c62d1` | Part VII: the stamps at entry, the Security Master's id rule, the Book B scanner's universe, the operator's writes |
| 9 | `6ffd6c6d` | Part VIII: engines 6 and 7 and the grammar search built |
| 10 | `d6d5add7` | Part IX: the verdicts since Draft 3, the pending drafts, new §9.10 calibration, the lessons register missing |
| 11 | `ead4b42e` | Appendix A rebuilt; B refreshed; D with Draft 3's not-built items' fates; E rewritten; Part X's busy-week table |
| 12 | `157f0ec4` | Figure 1 with stage 4's weekday touches; the caption and index |
| 13 | `2e7ab173` | The library guide's XXXIII rows in place and the library total; the masthead's reading time; the Master Guide's Table 9 row; both HTML editions rebuilt |

Part X is not in the brief's list. Its two sentences on trimming were false once D20 made budgets targets, so §10.1 is fixed in commit 5 and the busy-week table in commit 11.

## Word count and reading time

- About 29,000 words (28,977 by `wc`; Draft 3 was 23,526 by the same count).
- About two hours at 250 words a minute; the Reader's note says so.
- The library guide's total moves from "roughly 426,000" to "roughly 451,000". `check_library` measured 450,627 and warned past ±5% once Draft 4 was in.

## The errata (Draft 3's slips, now in the paper's errata block)

1. §2.3 put five external writers among the official ones.
2. §4.6 said M1–M13; the set is M0–M13.
3. §4.9 and Appendix A misnamed W11 and placed W12 fourth.
4. §6.3 said the signal scan is unrecorded.
5. §6.5's "two further tasks" named one.
6. §6.5's MSTR watch was described as reading mNAV.
7. Appendix D, item 4: "nothing writes observed".
8. Appendix D, item 12: the Monthly timer "by hand".
9. Appendix D's second table: the broker-sync comment "17:00".
10. Appendix E: the PRL endpoint (closed 18 Oct) and "two" intake entries (one).

Draft 3's own errata of 19 Oct are recorded as applied.

## Every difference found between a notes file, the brief and the code

The paper follows the code in each.

| # | The notes file or the brief says | The code says |
|---|---|---|
| 1 | a58 notes (:229) ask for a lag of about 75 days for `sec13f.*` | No lag family matches `sec13f.*` on chain-7, HEAD or a61b; the keys take the plain quarterly allowance |
| 2 | a57 notes (:79, :127): QID, UDOW, SDOW, URTY and SRTY are not in FUNDS | a61 (D13) added all five: FUNDS and `config/fragility.yaml` hold twelve on chain-7 (the notes were right when written) |
| 3 | b52 notes (:52): symbols 115 → 123 | Its own merge table says 124 (KRE); the code holds 124 on chain-5 and 127 on chain-7 |
| 4 | a61b notes, item 6d: AERO "gap (held)" | The code and the same file's A64 section follow the merged parent `aero` with a labelled break |
| 5 | a61b notes: "ten families added" | Twelve: A64 added the EIA rigs and the Cleveland Fed rules |
| 6 | `daily_cascade/volatile_day.py`'s docstring: "all four of Doctrine 5.5's arms" | It lists and codes five |
| 7 | `config/market_state.yaml`'s header: "THE EIGHT DIMENSIONS" | Fifteen declared, thirteen computed |
| 8 | The chain-7 and a62 notes cite D28 | D28's text is filed only on a61b (`rulings-2026-10-24-pm.md`), not on chain-7 |
| 9 | b60 notes' line cites | `target_line` is at `stack.py:1281`, the addendum's line at `digital_addendum.py:941` (not :932) |
| 10 | The brief: the X digest's "v4 three-file design" | No "v4" anywhere in the repository; the three files (the digest, the attention ledger, the voices ledger) and the addendum's reader exist |
| 11 | The brief: "the Monthly signal scan's first run on 25 Oct" | Scheduled for 25 Oct, 06:57; not yet run at writing, and no task id is recorded |
| 12 | The brief: "the Book B scanner's universe additions" | No configuration change: the universe is every stored daily price series with enough history, so the capex proxies joined by being stored (D11) |
| 13 | The brief: "the superseded keys (LBMA, overnight TNX, IOER)" | Declared superseded on a61b only. IOER is still pulled; chain-7's only superseded keys are WGC's |
| 14 | The brief lists WGC among the refusals | chain-7 declares WGC `not_yet_sourced` (a login), not `refused`; only MBA and Farside carry `refused`, on a61b. Apartment List is refused on its key |
| 15 | The brief lists DTCC among the refusals | No DTCC source id, module or key exists; it is a listed gap in text, and a gate asserts no key exists |
| 16 | The brief: "the Learning Loop v2 brief … if B65 has landed" | It exists only on `origin/b65-learning-loop-v2`, not in this base: Appendix E, as a draft |
| 17 | The brief: alignment_weekly (a65) and the capex-guidance reader (a66) "if pushed" / "where built" | Both pushed, but on later branches: Appendix E, by the brief's own definition of built |
| 18 | The brief: the event area as "vol, rates, gold, DM indices, the one-day 10-year trigger" | All print in the close's Mechanics (and the Weekly's and Monthly's); only the volatility event reprints in the anchor. The "rates" item is the 10-year speed flag's attribution (item 65) |
| 19 | Draft 3: the meme ingest at 21:45 | 21:15 since a49, so the evening note sees tonight's drafts |
| 20 | D5: the voices register names the outlet, never the person | The source list follows it (applied by a session). The extraction prompt still stores a speaker's name in a voice row when one is named; no check enforces D5 in code |
| 21 | a61b declares `crypto.total_market_cap_usd` a gap ("no keyless source serves the total") | CoinPaprika is live on both branches with `paprika.total_mcap_usd`; the two read oddly together |
| 22 | Draft 3: the budgets as caps with trimming | `trim_to_budget` is false everywhere and the trimming function is deleted; a foot line reports the overrun (D20). The two notes' caps stay hard |
| 23 | `register/reconcile.py`'s comments: hourly | The sync runs every 30 minutes (Draft 1's item 21, still open) |

## Gates

| Gate | Result |
|---|---|
| `tools/check_library.py`, at the end | 27 papers, 0 failures, 0 warnings |
| `tools/check_master_guide.py` | 0 failures, 0 warnings |
| `tools/validate_readability.py` (the footer's title and path) | 67/0 |
| `tools/validate_alpha_lab_3.py` (the tells quote §4.3) | 65/0 |
| `docs/figures/reporting-system/fig-01.svg` | parses |

## Needs you (at most five)

1. **Figure 1's new box** ("The day's touches") was placed by coordinates without a render. Open `docs/html/reporting-system-whitepaper.html` once.
2. **Accept-all under rule 31.** Draft 4 is committed as a draft and grants no right; Draft 3's acceptance is still pending in the Doctrine #2 pack.
3. **D5 and the voice rows** (difference 20). Should the outlet rule reach the stored voice rows, which can carry a speaker's name, or only the source list as now?
4. **The total market cap** (difference 21). a61b declares it a gap while CoinPaprika serves it. Say which stands before the merge on 27 Oct.
5. **Stale documents found while checking, for a later session.** Draft 4 changes no other file:
   - `config/market_state.yaml`'s header (7);
   - `volatile_day.py`'s docstring (6);
   - `reconcile.py`'s "hourly" (23);
   - a58's 13F lag request (1).

## CI

| Run | Commit | Result |
|---|---|---|
| 40151163517 | `3dc8c79e` | **CI queued, run 40151163517** (not waited on; the next paste that touches this branch reads it once) |
