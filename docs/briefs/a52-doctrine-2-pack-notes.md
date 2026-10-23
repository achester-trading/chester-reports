# a52-doctrine-2-pack: the Doctrine #2 preparation pack (session A, 20 Oct 2026)

**Base and boundaries.** This branch is cut from chain-3's final tip, `4f004a4` ("chain-3: STITCH COMPLETE c454830"). It merges on its own, after chain-3.
- **Branch only.** This branch is pushed and nothing else. Nothing ran on the box, no unit was enabled or started, and nothing was merged.
- **What was only read.** a50-dealer-store's and b48-scoreboard's notes were read from origin, and neither branch was pushed to. chester-meme was not opened.
- **The order.** The Doctrine #2 preparation pack, ruled 20 Oct 2026 ("accept all", decision 13 of that morning's list). It is docs only.
- **Corrections from the operator, 20 Oct.**
  - The Doctrine does make the 1000 touch mandatory: 6.5, line 448, "On volatile-protocol days the 1000 touch is mandatory and the close touch is the last look of the day." It is quoted verbatim in T8-16, beside 4.3 and 5.5.
  - "Rule 31" is this project's convention for drafts, not a Doctrine rule (the Doctrine's numbered rules end at 29). Every draft is labelled "rule-31 draft (for the operator's accept-all)".

## What was written

| File | What |
|---|---|
| `docs/briefs/doctrine-2-pack-2026-11.md` | The pack, in three parts plus the opening page: the summary page (the ten decisions, the rest grouped, the blocks, the reading time); Part A, the Master Guide's Table 8 (17 items); Part B, the items outside Table 8; Part C, the fifteen setup drafts |
| `docs/master-guide.md` | One line in Part 8, linking to the pack |
| `docs/html/master-guide.html` | Rebuilt from the `.md` (`tools/build_paper_html.py`), the edition being build output |

**Size.** About 8,600 words, so about 37 minutes at 230 words a minute. The summary page takes about 4 minutes and Part C about 10.

**Not edited:** the Doctrine, `config/setups.yaml`, every white paper's body, and every config file.

**The library check needed no registration.** `tools/check_library.py` resolves every link under `docs/` and registers no brief.

| Check | Result |
|---|---|
| `tools/check_master_guide.py` | 0 failures, 0 warnings |
| `tools/check_library.py` | 27 papers, 0 failures, 0 warnings |

## Every source read

| Source | What was taken |
|---|---|
| `docs/master-guide.md` | Part 8's Table 8 (all 17 rows); Part 5's counts; Table 7a's ledgers; Table 7b's statuses and its evidence words; the glossary; Part 9's paper roster |
| `docs/whitepapers/operating-doctrine-whitepaper.md` (read, not edited) | The Card; 2.1; 4.1–4.4; 5.2, 5.3, 5.5; 6.2, 6.4, 6.5 (line 448); 9.1; 9.5 (Gate C); Doctrine Rule 9; Appendix B; Appendix E's rule-31 usage |
| `docs/briefs/doctrine-2-proposals-st-l.md` | Tranche H's five proposals, P1–P5 |
| `docs/change-order-signal-triage-2026-09-25.md` | Tranche H's list (the Doctrine items are P1–P5); SR-1's rights |
| `docs/signal-triage-register.md` | SR-1 (rights, home, gate status, the 18 Oct ruling); SR-13; SR-8's status line |
| `docs/ledgers/*.md` | Each cited ledger's verdict, n and as-of (sr-1, sr-4, sr-5, sr-12, sr-13, sr-22 r2, false-bottom-audit, sn-1, sn-2, os-6, os-9, the dealer-scorecard pre-registrations, rates-driver r2, st-r5.30b) |
| `docs/change-order-secondary-notes-2026-10-19.md`; `docs/briefs/a49-secondary-notes-notes.md` | The three Doctrine #2 items: the 1000 report's text, the mandatory touch, the Book D touch |
| origin/b48-scoreboard: `docs/briefs/b48-scoreboard-notes.md` | Marking open positions; risk-adjusted and after-tax comparison; long against short; `min_n` 10; the regime stamp at entry |
| origin/a50-dealer-store: `docs/briefs/a50-dealer-store-notes.md`, `daily_cascade/volatile_day.py` | The flag's four arms, its rights clause ("printed, never applied"), its two session-set values; engine 7's bars |
| `docs/workplan-v5-2026-10-09.md`, `-v6-2026-10-10.md`, `-v7-2026-10-16.md` | The Doctrine #2 line (v5, line 22): DTH-1 scope, Category 2 triggers, the attention cap, the chart cap of 12 |
| `docs/briefs/dth-1-spec-2026-09-27.md`; `docs/change-order-enterprise-layer-2026-09-27.md`; `docs/briefs/audit-4-agenda.md` | DTH-1 (R-2, section 4 item 4, Audit #4 item I.4); Category 2's list |
| `docs/briefs/doctrine-monthly-2026-10-agenda.md`, `-minutes.md`; `docs/attention-log.md` | The attention cap (item 4b); trigger recalibration (item 10); the 2 Oct budgets |
| `config/reporting_stack.yaml` (read) | The Monthly's chart cap of 12 and its header on trigger recalibration |
| `config/setups.yaml` (read, not edited) | The fifteen stubs, the field definitions, the fixed kill criterion |
| `docs/briefs/el-1-notes.md` | The stub completion and the kill-criterion question |
| `config/alpha_events.yaml`, `config/claims.yaml`, `tools/base_rates.py` (read) | The base-rate id schemes (`baserate.<table>`, `claim:<id>`) and the event base rates |
| The library papers cited in Part C | The Dealer's Hand (5.1, 5.2, 7.3, 7.5, 10.2); Options as Expression (8.3, 15.7, 16.5); Volatility (ch. 29); Price, Time, and Edge (8.3, ch. 15, ch. 18, ch. 20); Technical Indicators (ch. 5, ch. 6); Earnings (ch. 9); Base Rates (ch. 4, ch. 6, Appendices C and D); Positioning & Flows (2.9, 2.13, 4.5, 6.4, 7.5, 9.4); the Daily Cascade paper (DC 2.7.2, DC 5.7.2, 8.2) |
| The rest of `docs/` and `config/` | Searched for "Doctrine #2" (32 files); each mention is folded in or listed below |

## Every item found outside Table 8

| Pack item | Source |
|---|---|
| V-1, the flag's automatic actions | a50-dealer-store notes (A51) and `daily_cascade/volatile_day.py`; Doctrine 5.5 |
| V-2, the regime stamp at entry | b48-scoreboard notes (Needs you #3); Doctrine 6.4, Appendix B |
| V-3, the flag's session-set values | a50-dealer-store notes (A51 needs you) |
| R-1, SR-1's rights | `docs/signal-triage-register.md` (SR-1); the Master Guide's calendar ("Doctrine #2: SR-1's rights") |
| H-1 to H-5, Tranche H's five proposals | `docs/briefs/doctrine-2-proposals-st-l.md`; `docs/ledgers/false-bottom-audit-2026.md` (lines 97–104) |
| B-1 to B-4, the scoreboard's items | b48-scoreboard notes |
| W-1, DTH-1's scope | the workplan (v5); `docs/briefs/audit-4-agenda.md` (I.4); the Enterprise Layer order (section 4, item 4); `docs/briefs/book-b-scanner-brief-2026-10-12.md` |
| W-2, the Category 2 triggers | the workplan (v5); `docs/briefs/audit-4-agenda.md` (Category 2) |
| W-3, the attention cap | the workplan (v5); the October minutes (item 4b); `docs/attention-log.md` |
| W-4, the chart cap of 12 | the workplan (v5); `config/reporting_stack.yaml` |
| W-5, trigger recalibration | the October minutes (item 10); `config/reporting_stack.yaml` (header) |
| O-1, the 1Q27 theses | `docs/change-order-alternative-assets-quarterly-2026-10-10.md`; `docs/briefs/aq-6-thesis-register-notes.md` |
| O-2, the EM resolution criteria | `docs/briefs/aq-14-em-paper-notes.md` |
| O-3, the crypto basket in Book A | `docs/briefs/crypto-basket-brief-2026-10-12.md` |
| O-4, the "and climbing" leg | `config/book_b_scanner.yaml`; `docs/briefs/book-b-scanner-2-notes.md`; workplan v7 |
| O-5, the packet template | `docs/change-order-weekly-storyline-2026-10-11.md` |
| O-6, the Alpha Lab's place | `docs/change-order-alpha-lab-2026-10-12.md` |
| O-7, the dealer engine's later enhancements | `docs/briefs/dealer-positioning-audit-2026-10-09.md`; `docs/briefs/dealer-positioning-brief-2026-10-09.md` |
| S-1, the setup stubs and the kill criterion | `docs/briefs/el-1-notes.md`; `config/setups.yaml` |

**Folded into Table 8 rather than listed apart:**
- the secondary notes' three items (T8-3, T8-16, T8-17);
- the Master Guide's Part 2 and Part 7 mentions of the mandatory touch (T8-16);
- the chain-3 stitch notes' R14 (Table 8 is the agenda).

**Pointers only (no new item):**
- the chain-2 and chain-3 stitch notes;
- `docs/briefs/library-st-l-notes.md`;
- the register's line accepting the five proposals onto the agenda;
- the Master Guide's calendar;
- the workplans' date lines;
- the October minutes' order of work.

There are no mentions in the white papers' bodies, and the `docs/html/` mentions mirror the Master Guide.

## For session B: three inconsistencies found and not edited

The operator asked that these be listed here, for session B, and that the files not be edited.
1. **The Master Guide's glossary** says the dealer scorecard has "six pre-registered tests" (the scorecard entry). Part 5 counts seven (H1, H2, H3a, H3b, H4, H5, H6).
2. **SR-8's status.** The Master Guide (Part 5 and Table 7b) shows SR-8 as failed by its ledger (false-bottom-audit-2026.md, FAIL, n 16). The register's status line still reads "ADOPTED — audit pending" (`docs/signal-triage-register.md`, SR-8).
3. **`b_style_regime_pair`'s comment** in `config/setups.yaml`, "SR-1's ledger (Base Rates) is not yet stored", is out of date: sr-1-ledger-2026-10-18.md exists (PASS, n 6).

## Needs you

1. **Read the pack before 7 November.** Its summary page is the agenda's first page.
2. **Rule on the ten decisions one by one.** Each changes what a book may do.
3. **Rule on the blocks** in the pack's block table: the renames, the dormant markings, the measurement accepts, the reading rules, the calibration and the deferrals to Audit #5.
4. **Complete the fifteen setup entries** in `config/setups.yaml` at the session, from Part C's drafts. This branch does not edit the file.
5. **For the merge sheet:** this branch merges on its own after chain-3. It is docs only, and it shares `docs/master-guide.md` and `docs/html/master-guide.html` with any later Master Guide refresh.
