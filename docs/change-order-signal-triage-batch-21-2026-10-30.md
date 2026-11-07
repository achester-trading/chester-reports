# Change order — Signal triage Batch 21 (item 115): round 11

| | |
|---|---|
| File | `docs/change-order-signal-triage-batch-21-2026-10-30.md` |
| Status | **RULED in chat** 30 Oct 2026, 08:06 ET ("Yes"; §7, the sign-off); recorded as D47 (`docs/briefs/rulings-2026-10-28-31.md`). Filed 31 Oct 2026 by paste B95 with filing amendments N1 to N3 (§0). The order as drafted in the triage chat is kept at `docs/pastes/B95-attachment-round-11.md`; it names no person. |
| Encoding | Batch 21 of Post-Freeze Amendment #4, item 115 as written (N1: free on this base; Batch 20 ends at 114). Register number provisional, SR-76, placed by Audit #5. |
| Precedence | Below Part 26, the Enterprise Layer order and the dated change-orders edition; equal to the other Amendment #4 batches. The amendment governs its parent item from filing. |
| Supersedes | Nothing. |
| Totals | ≈ 2.5 h of sessions · no by-hand work (the Grok automation and the chat-side triage run themselves). The triage chat's estimate. |
| Built by | Nothing yet. Tranche B after 8 Nov, placed by Audit #5. |

---

## 0. Filing amendments (paste B95, 31 Oct 2026; accepted 30 Oct 2026, D47)

- **N1, the check.** Batch 21 and item 115 are free on this base (`b95-batch-21-filing`, from `b92-batch-20-filing` at `30c16e1c`): no batch order, register row or index line holds them, and no remote branch files a Batch 21. Nothing is renumbered; the work ID is ST-R11.115.

- **N2, references.** Each earlier reference resolved **by subject**. The order's text keeps its words; this table governs.

  | Written | Resolves to | Subject, and where it is filed |
  |---|---|---|
  | item 50 | 50 | The social attention layer, X via Grok (Batch 8, `change-order-signal-triage-batch-8-2026-10-17.md`; ST-R6.50a–c). Its rights stand: discovery, attention-shock and disagreement only, never measurement. 115 amends it with an evening run and an evening-note block |
  | the 21:30 evening note | the evening note | `daily_cascade/evening_note.py`, ruled by `change-order-secondary-notes-2026-10-19.md`: every line code-written, prose only when its gate opens (150 words, 400 on Sunday), no rights, live from 26 Oct 2026 |
  | the nightly sweep; `~/chester-data/inbox/x-triage/` | `scripts/rclone_sync.sh`, the X pilot's section | Today the sweep copies only `x-attention-ledger.csv` and `x-voices-ledger.csv` from `chester-vendor-checks/x-triage`, and `x-digest-YYYY-MM-DD.md` from `chester-x-digest`. Neither pattern matches `x-triage-evening-YYYY-MM-DD.md` or `x-digest-evening-YYYY-MM-DD.md`, so 115(a) is new work in the sweep (V1) |
  | "the numeral audit treats every figure in the block as quoted" | the verbatim rule | The audit (`altdata/numeral_audit.py`) has no "quoted" class today. The precedent is the Monthly's Reading entry: a stored summary printed verbatim, escaped, never polished, audited or trimmed (`stack_render`). 115(b) prints the triage text the same way, outside the model's prose and outside the audit's allowed set; the gate (d) holds that no figure from it reaches that set |
  | the rumour ledger | the shared rumour ledger, chat-side | Kept on Drive by the triage tasks; Audit #5 reads its base rates. Not a ledger of the system's own (115(c)) |

  Every reference resolves.

- **N3, names** (D5, D38, D47; the standing rule: no person's name in committed files). The order names no person. The fixed seed list of principals (founders, chief executives and officials whose posts move markets) added on 30 Oct stays **chat-side**: it is never committed. The box block prints a source as role and institution, or as a handle type ("an X aggregator account"), never the person; the gate (d) refuses a person's name. The ruler is "the operator". Everything else is verbatim.

---

REPORT_OK-class: no path to DECISION_BLOCKED, no composite or T&B weight change, no regime tag. X items keep the rights item 50 gave them: attention and rumour-tracking only, never measurement.

---

## 1. Rulings at a glance

| Item | Short name | Ruled | Kind | Sessions |
|---|---|---|---|---|
| 115 | The evening X read: a Grok evening run (17:40 ET), a chat-side triage (18:05 ET), an "X after hours" block in the 21:30 evening note | "Yes" 30 Oct, 08:06 | AMEND item 50 | 2.5 h |

---

## 2. Entry

### 115 · The evening X read — AMEND item 50

**Origin.** The operator's request (30 Oct): news and rumours that break after the close should reach the evening report the same day, not the next morning.

**What exists from 30 Oct (chat-side, outside the repo).**
- A Grok automation at 17:40 ET, daily except Saturday. It searches X for posts since 06:00 ET and writes `x-digest-evening-YYYY-MM-DD.md` to the Drive folder `chester-x-digest` (format "E v1").
- A chat-side scheduled task at 18:05 ET. It triages that digest (incentive tags, a credibility read per rumour, up to four primary-source checks), adds chapter-E rows to the shared rumour ledger, and writes `x-triage-evening-YYYY-MM-DD.md` to `chester-vendor-checks/x-triage`, with the headings Quality / What broke / Rumours / Verification / Voices / Ruling. It also pushes a summary to the operator.

**Decision (the box piece).**
- **(a) Inbox.** The nightly sweep pulls the day's `x-triage-evening-YYYY-MM-DD.md` into `~/chester-data/inbox/x-triage/`, the same way the AAII file arrives. A pull at about 18:30 ET (or inside the evening note's own run) is needed so the 21:30 note sees it the same day: the build states which, and adds no new unit unless it must.
- **(b) The block.** An "X after hours" block in the 21:30 evening note (Sun–Thu):
  - up to five "What broke" lines, each with its posted time in ET, the outlet or handle type, and its incentive tag;
  - the rumours, each labelled *unverified*, *confirmed* or *denied*, with the primary source when resolved;
  - one line of verification results.
  - Text is copied from the triage file. The note's model never paraphrases it into a market claim, and the numeral audit treats every figure in the block as quoted, not as the system's measure.
  - No file: "X evening read not available". A file older than today prints nothing.
- **(c) Rights.** The block is report-only. It changes no regime, flag, score or decision. A rumour never enters a ledger of the system's own, other than the rumour ledger, whose base rates are what Audit #5 reads.
- **(d) Gate.** A fixtures-only gate:
  - the block renders from a synthetic triage file;
  - a stale or absent file prints the stated line;
  - no figure in the block reaches the numeral audit's allowed set as a measure;
  - no person's name passes (handles only, as in the file).
- **Hours:** 2.5. **Placement:** Tranche B, after 8 Nov; Audit #5 places it.

---

## 3. Cross-item notes

1. **Item 50's pilot gains an evening pass.** The morning digest (06:00 ET) and its reader task are unchanged. 115 adds the evening digest and triage, and the evening note becomes the first box report to print the X layer's text the same day.
2. **The evening note's rights do not change.** It has none, and the block adds none (115(c)).

## 4. Work order

| Tranche | When | Work | Sessions |
|---|---|---|---|
| **B** | After 8 Nov; Audit #5 (week of 23 Nov) places | 115(a) the sweep's evening pull · 115(b) the "X after hours" block · 115(d) the gate | 2.5 h |

## 5. Verify items

| # | Item | What | Closes on |
|---|---|---|---|
| V1 | 115(a) | The sweep's patterns do not match the evening files today (N2). Which pull reaches the 21:30 note the same day: an 18:30 ET sweep pass or the evening note's own fetch (`altdata.note_fetch evening`)? | The build states it; no new unit unless it must |
| V2 | 115(b) | The triage file's headings (Quality / What broke / Rumours / Verification / Voices / Ruling) are stable enough to parse by name | A synthetic file in the gate, and the first real file read by name, never by position |

## 6. Registers

**Signal-triage register.** One new entry, provisional SR-76 (115, the evening X read). Amendment: item 50 (115).

**Voices.** None new. Accounts the evening run surfaces go to the X pilot's seed list chat-side (N3).

## 7. Sign-off

| Date / time (ET) | Item | Ruling as stated |
|---|---|---|
| 30 Oct 2026, 08:06 | 115 (the evening scan and the evening-note block) | "Yes" |

Open at filing: the SR and batch numbers (audit); V1–V2.
