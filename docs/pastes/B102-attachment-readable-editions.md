=== ATTACHMENT === change-order-readable-editions-2026-11-01.md (file this text, names stripped as D38 rules, as docs/change-order-readable-editions-2026-11-01.md; the copy beside the paste goes to docs/pastes/B102-attachment-readable-editions.md)

# Change order — the readable editions (the Letters, the cards and the pushes)

| | |
|---|---|
| **File** | `docs/change-order-readable-editions-2026-11-01.md` (filed by B102) |
| **Status** | RULED 1 Nov 2026 12:11 ET ("accept all", D50–D56 as recommended); filing by B102. D51 applied the same minute (the Monthly Letter task now runs on Opus). D56 pending the operator's Grok work (steps given in chat 1 Nov). |
| **Origin** | The operator (1 Nov): "I've created some scheduled text overlays on top of the regular reporting, to make reading them much easier. Make sure these changes are fully considered in our master architecture and how this reporting works." |
| **Precedence** | Below Part 26 and the Enterprise Layer order; beside the Weekly readability order (W10, 30 Oct); amends the Master Guide's Tables 2 and 4 and Part 7, `docs/master-guide/chat-tasks.yaml`, `docs/scheduled-tasks.md`; the Reporting System paper only through its dated appendix at its reread |
| **Totals** | ≈ 1.5 h of session B (B102, docs only) · ≈ 1 h added to session A (A95 Part 6, A103) · 10 minutes of the operator's Drive and scheduler work |

REPORT_OK-class throughout: nothing here has decision rights, changes a flag, a weight, a store key or a unit.

## 1. What exists (as of 1 Nov 2026, 11:00 ET)

Everything below runs chat-side, in the scheduler, on Opus unless stated. None of it is in the repo's record yet: `docs/master-guide/chat-tasks.yaml` was last updated 20 Oct on every branch, so Table 2 and Figure 2 of the Master Guide are three weeks behind.

| Overlay | Sits on | When (ET) | Writes | Since |
|---|---|---|---|---|
| **The Weekly Letter** (task "Weekly Letter — Sunday") | the Weekly (Sunday 05:10 email) | Sunday 06:12 | a private page with 10–18 charts and the PDF attached; the text edition `chester-letters/weekly-letter-YYYY-MM-DD.html`; a row on the Letters index; an email with the four links; a push | 25 Oct; delivery form settled 1 Nov 10:40 |
| **The Monthly Letter** (task "Monthly Letter — 1st of the month", model Fable) | the Monthly (the 1st, 07:40 email) | the 1st, 10:43 | the same four things, `monthly-letter-YYYY-MM.html` | created 1 Nov 10:50; the October 2026 edition (17 charts) written by hand the same morning; first scheduled run 1 Dec |
| **The Letters index** (a private page, not a task) | both Letters | on each publish | one row per edition (kind, period, one line, regime, tension, gamma, book, Brier, charts, links) in the page's own store | 1 Nov |
| **The ES day-trading card** (DTH-1's manual edition) | the 07:00 anchor, the 09:50 open note, the 12:30 alert; the day's X triage | weekdays 08:15 and 15:15 | `chester-cards/card-YYYY-MM-DD-am.html` / `-pm.html`, an email, a push | 27 Oct |
| **The ES Sunday map** | the Weekly and the Weekly Letter | Sunday 18:48 | `chester-cards/map-YYYY-MM-DD.html`, an email, a push | 27 Oct |
| **The X triage, morning** | the two Grok morning digests (06:00 A, crypto; 06:15 B, equity-vol and macro), each ending with a Principals section from 2 Nov (folded into the two prompts under Grok's 8,000-character limit; role tags applied by the triage) | daily 07:17 (was 06:50 in the register) | `x-triage/x-triage-YYYY-MM-DD.md`, the four ledgers, a push | redesigned 24 Oct |
| **The X triage, evening** | the Grok evening digest (17:40, E v2) — **blocked: the operator's Grok plan allows two automations, both taken by the morning runs**; the triage task is paused until a third slot exists | Sunday–Friday 18:05 (paused 1 Nov) | `x-triage/x-triage-evening-YYYY-MM-DD.md`, chapter-E ledger rows, a push | 30 Oct (item 115 carries the box piece) |

## 2. The contract (what "how this reporting works" gains)

Six lines, to be written into the Master Guide (Part 2, after the secondary notes) by B102 and into the Reporting System paper's dated appendix at its reread:

1. **The edition is the record; a Letter is a reading of it.** Every figure in a Letter appears in the edition it reads, copied with its unit and as-of date; the edition's own validation status applies to each; the only arithmetic allowed is a difference between two printed figures, said to be one. The charts are drawn from the edition's own tables.
2. **No rights.** A Letter never says buy, sell, long, short, add, trim, overweight or underweight. Nothing in the repo, the store, the inbox, a ledger or a flag reads a Letter, a card or a map. The ES cards and the map are the operator's private DTH-1 tool: Claude writes them and places no orders; the system never reads a card.
3. **Provenance runs one way: store → edition → Letter.** The Letter's footer names the edition it read. A Letter that finds no edition pushes "no edition found" and stops; the operator fires it again once the edition arrives. A Letter never delays, retries or repairs an edition, and the box's heartbeat does not know the Letters exist.
4. **What the Letters find, the box fixes.** Each Letter prompt carries the edition's known self-contradictions ("known patterns", found while writing). That list is a defect feed, not a patch: each entry is filed in `docs/briefs/letter-findings.md`, fixed in the edition by a session, then retired from the prompt. A Letter says where the edition contradicts itself and does not chart the disputed figure; it never papers over it.
5. **The repo's rules hold in the Letters.** No person's name (institutions and outlets only, even where the edition prints names), no Brookfield-complex instrument, no secrets, no email addresses. The Letters live in Drive and on private pages, never in the repo; the register (Table 2, `chat-tasks.yaml`) is the repo's whole record of them, with no prompt and no figure committed.
6. **Reading order.** Sunday: the Weekly Letter first (about fifteen minutes), then the Weekly for the book, the scorecard and the post-mortems. The 1st: the Monthly Letter first, then the Monthly's read and its book for the sitting. The editions' configured reading targets (20 and 55 minutes) stand as the reference reader's, not the first read's. This replaces §10.3's Sunday line in the Reporting System paper, which records it in its dated appendix at the reread its own status line calls for "after the first stacked Monthly".

## 3. What the review found that needs action

| # | Finding | Effect | Fix |
|---|---|---|---|
| F1 | **Grok has been writing into a second Drive folder named `chester-x-digest`** (created 29 Oct 10:10 UTC, at the Drive root) since the 29 Oct run; the original folder (its Drive id is not recorded here: folders are named by path only) has had nothing since 29 Oct. | The box's sweep (`scripts/rclone_sync.sh`) lists the folder **by name**; with two of the same name rclone warns "duplicate directory" and reads one of them, usually the older. The inbox has probably had no new X digest since 29 Oct. The evening triage prompt reads the original folder by id. | **Operator, 2 minutes, today:** move the files from the new folder into the original, delete the empty duplicate, and re-select the original folder in each Grok automation. Then I re-point nothing; the triage prompts stay as they are. |
| F2 | The Monthly Letter task runs on **Fable**; every other recurring task is on Opus (the operator's standing rule). | Cost and the rule. The Weekly Letter handles a 500,000-character edition on Opus. | Switch the model to Opus (one scheduler edit, which I make on a yes). |
| F3 | **Two homes for the DTH-1 ledger.** The cards read `chester-cards/dth1-manual-ledger.csv` (status, entry, stop, contracts, risk, rule broken); A92's box reader expects `chester-vendor-checks/dth1/dth1-manual-ledger.csv` (Date, Result R, Rule broken). | The operator would keep two files, or the anchor's checklist reads nothing. | One file, in `chester-cards/`, with the cards' columns; A92's sweep path and its reader change before A92 merges (an A92 addendum, about 20 minutes, after A95). |
| F4 | The Letters' "known patterns" are **edition defects**: seven in the 1 Nov Monthly, seven in the 30 Oct Weekly (listed in A95 Part 6 and A103). | Left in the prompts they are patched over each week instead of fixed once. | A95 gains Part 6 (the Monthly's seven); A103 takes the Weekly's seven; `docs/briefs/letter-findings.md` is the running file. |
| F5 | The MSTR/MSCI watch's schedule covers November only; its "post-effective read on 1 Dec" (in the register and the prompt) is not scheduled, and the prompt tells any December run to stand down. | No 1 Dec read. | A one-shot for 1 Dec 07:10 with a prompt that allows that date; late November, not now. |
| F6 | The register's rows for the X pilot, the FlashAlpha tasks, the AAII layout and the UTC-held tasks are stale (06:50 → 07:17; two Grok files, A and B, each with a Principals section; the FlashAlpha pair deleted at chain-2; AAII writes `aaii/weekly/YYYY-MM-DD.csv` since 24 Oct; daylight saving ended today). | Table 2 and Figure 2 disagree with the scheduler; `tools/check_master_guide.py` holds Table 2 to the file, not the file to the scheduler. | B102. |

## 4. Decisions (recommendation in bold)

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D50 | Record the readable editions as a layer of the reporting system with the six-line contract above, in the Master Guide (Part 2 subsection, Tables 2 and 4, the week at a glance, Part 7's Sunday and first-weekend checklists), `chat-tasks.yaml`, `docs/scheduled-tasks.md`, and one dated paragraph in the architecture v3's Part 4; the Reporting System paper only at its reread. | yes / narrower (register only) | **yes** (B102) |
| D51 | The Monthly Letter task's model. | Opus / keep Fable | **Opus**, the standing rule; if the first Opus run on 1 Dec truncates the 215,000-character edition, revisit |
| D52 | The DTH-1 ledger's single home and columns. | `chester-cards/` with the cards' columns, A92 adapts / `chester-vendor-checks/dth1/` with A92's columns, the cards adapt | **`chester-cards/`, the cards' columns**; A92 addendum after A95 |
| D53 | The Letters' known patterns become a repo defect list and session work (A95 Part 6, A103), retired from the prompts as fixed. | yes / leave in the prompts | **yes** |
| D54 | The nightly sweep also copies `chester-letters/` and `chester-cards/` into the inbox as an archive (no reader; `rclone copy`, never sync; the inbox is outside the repo and inside the encrypted backup). | yes, in the A92 addendum / no | **yes** — the Letters and cards are otherwise only in Drive and on pages |
| D55 | After a97 (W10) merges, the Weekly Letter prompt reads the edition's "What to see" lines as the first source for each chart's takeaway. | yes / no | **yes** (a chat-side prompt edit I make after the merge) |
| D56 | The Grok evening automation: the operator creates it from `grok-evening-automation-prompt.md` (E v2) once a third Grok automation slot exists (the plan allows two; "task limit usage reached" on 1 Nov); the 18:05 triage stays paused until then; a midday run (D57, proposed 1 Nov) waits on the same slot. | plan change for a third slot / swap a morning run / hold | **accepted 1 Nov as "create this week"; now blocked on the slot — the operator decides on the plan** |

## 5. Sign-off

| Date / time (ET) | Items | Ruling as stated |
|---|---|---|
| 1 Nov 2026, 12:11 | D50–D56 | "accept all" (the Grok evening automation, D56, to be created by the operator after the duplicate-folder fix F1) |
