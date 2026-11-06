# Post-Freeze Amendment #3: AI trajectory and governance monitoring — RECORD (approved in chat 13 Sep 2026; original not committed)

| | |
|---|---|
| What this file is | A **record**, not the order. It says what the repository holds of the amendment and where. It is not a reconstruction of the order's text, and nothing here is ruled by being written down. |
| The order | Approved in chat on 13 September 2026, with two workstreams: **A**, the sub-factor I-b inputs including consensus drift; **B**, Internal Order as Factor VI, a Monthly Internal Order panel, and the internal-order cycle as a coequal lens in Paper XXVII. It was to be encoded as the next free architecture Part, with its ten-item work order placed at Audit #4. **Its original file was never committed**, and no architecture Part encodes it. |
| Filed | 24 October 2026 by session A (A70), from a search of every branch on origin (main, chain-7 and the library branches) |
| Wanted | The original file from the 13 Sep chat, to be filed verbatim beside this record when found (needs-you below) |

## 1. What the search found

The search covered `git grep` across `origin/main`, `origin/chain-7`, `origin/library`, `origin/library-xxvii`, `origin/library-draft-3`, `origin/library-st-l` and this branch, for "Amendment #3", "amendment-3", "AI trajectory", "Internal Order", "Factor VI", "consensus drift" and "I-b".

- **No order file.** No `docs/change-order-*amendment-3*` exists on any branch, and no order dated 13 September is filed. `docs/change-orders.md` lists none before 25 September.
- **No architecture Part.** `docs/chester-reports-architecture-v3.md` ends at Part 32.
  - Its Part 29 (line 4656) is headed "Change Order #3: Eight Tactical Additions (post-freeze amendment #3)", "Principal-directed, 5 Sep 2026". It is a different order, with the same number. Its eight additions do not mention AI trajectory, governance or the internal order.
  - **There are therefore two orders called "amendment #3":** Part 29 (5 Sep, in the architecture document) and this one (13 Sep, in chat). The library-xxvii notes (`origin/library-xxvii:docs/briefs/library-xxvii-notes.md`, line 35) found the same.
- **How the later amendments are numbered, so the gap shows.**
  - Post-freeze amendment #4 is the signal-triage order. `docs/change-order-signal-triage-2026-09-25.md`, line 13, supersedes "`post-freeze-amendment-4-signal-triage-batch-1.md` (19 Sep standalone …)"; `docs/briefs/audit-4-agenda.md`, line 45: "batch 3 = Batch 3 of Amendment #4 (confirmed)".
  - The Enterprise Layer is #5 (`audit-4-agenda.md`, line 22: "Enterprise Layer = **Post-Freeze Amendment #5** (confirm)").
  - The Alternative Assets Quarterly is #6, provisional (`audit-4-agenda.md`, line 140).

## 2. The two workstreams, as the repository's own documents describe them

### Workstream A: the sub-factor I-b inputs, including consensus drift

- `docs/change-order-signal-triage-2026-09-25.md`, line 1082: "**19 Sep batch Part C (by reference; register SR-11).** Consensus drift — sixth I-b input "consensus drift" (unscored prose line), Foundations evidence log, ESPAI point-in-time fixture, LEAP as a source (≈6.5 h). Its interim bimonthly scan continues (§1.12)."
- The same order, line 262: "| 11 | — | *Reserved:* Consensus drift (19 Sep batch Part C) | Backlog | — | Appendix C |". Line 422: "### SR-11 *Reserved* — Consensus drift — 19 Sep batch Part C".
- `docs/signal-triage-register.md`, line 265: "This number is held so the consensus-drift item keeps its place if it is ever scheduled; it has no ruling, rights or build slot until then."
- `docs/master-guide.md`, line 149, the chat-side task: "| AI-risk consensus-drift scan | the 20th of even months, 13:00 UTC (09:00 ET until 1 Nov, 08:00 ET after) | one line for Disruptive Themes | Disruptive Themes (human-gated) | none (a read) | active |".
- `docs/change-order-jpm-gtm-2026-10-03.md`, line 34: "| GTM-20 | AI adoption and capability markers (Census BTOS; METR) | **LOG**, semi-annual | sourced figure | scans ingest; Factor I-b | 0 |".
- `docs/reading/watchlist.json`, line 9: `"ai": "AI trajectory (Factor I / I-b)"`, the reading shelf's group for the AI publications (lines 53–54: Stanford HAI's AI Index, the State of AI Report).

### Workstream B: Internal Order as Factor VI, the Monthly panel, and XXVII's lens

- `docs/workplan-v3-2026-10-02.md`, line 44: "| Amendment #3 §7 work order (AI trajectory and governance; Internal Order) | Audit #4, 14–15 Oct |".
- `docs/change-order-jpm-gtm-2026-10-03.md`:
  - line 25: "| GTM-11 | K-shape panel (labor vs profits share; net worth by cohort; income vs spending by quintile) | **ADOPT, placed with Amendment #3 workstream B** (the Internal Order panel), built once | modifier | Amendment #3 WS-B | 4 |";
  - line 49: "GTM-11 travels with Amendment #3 workstream B (~4 h)".
- `docs/signal-triage-register.md`, line 750: "GTM-11 (SR-55) comes with Amendment #3 workstream B". `docs/briefs/gtm-core-1-notes.md`, line 45, and `gtm-core-2-notes.md`, line 66: "SR-55 … reserved: Amendment #3 workstream B".
- `docs/briefs/reporting-stack-brief-2026-10-02.md`, line 31: the Monthly's Slow layers carry "CAPE/ERP, base rates, the 25 tail scenarios, Disruptive Themes, Internal Order".
- `docs/reading/watchlist.json`, line 10: `"internal-order": "Internal Order (Factor VI)"`, the shelf group for the trust and governance publications (lines 56–60: the Edelman Trust Barometer, Gallup's confidence in institutions, V-Dem's Democracy Report, the Global Peace Index, Pew's trust in government).
- `docs/change-order-signal-triage-batch-5-2026-10-09.md`, line 53: "XXVII carries the long cycle and Workstream B added Strauss & Howe".
- `docs/change-order-signal-triage-batch-6-2026-10-15.md`, line 110 (item 38): "its peaks line up with the regimes Factor V and the Internal Order workstream watch".

## 3. What is built, what is specified, and what is neither

| Piece | State | Where |
|---|---|---|
| A: the consensus-drift input (SR-11, 19 Sep Part C) | **Neither built nor scheduled.** SR-11 is reserved with no ruling, rights or slot. The interim chat-side scan runs every second month, outside the repository | `signal-triage-register.md:265`; `master-guide.md:149` |
| A: an I-b block in the Monthly | **Built in part** on chain-7 (b59): "Factor I-b: open model releases (Hugging Face)", a report-only block, pre-registered as an Alpha Lab hypothesis (D26). It is not the I-b inputs as the amendment names them | `altdata/sources/hf_releases.py:57`, `:325`; `daily_cascade/b59_block.py:16` |
| A: GTM-20, AI adoption and capability markers | **Specified** as a semi-annual logged sourced figure through the scans ingest; no figure stored | `change-order-jpm-gtm-2026-10-03.md:34` |
| A: the reading shelf's AI group | **Built** as shelf entries (the publication watch reads them) | `docs/reading/watchlist.json:9, 53–54` |
| B: Internal Order as Factor VI | **Specified** only as a reading-shelf group and a Slow-layers name; no factor code, config or registry entry exists | `watchlist.json:10, 56–60`; `reporting-stack-brief-2026-10-02.md:31` |
| B: the Monthly Internal Order panel (with GTM-11, SR-55) | **Not built.** SR-55 is reserved; the K-shape line prints as a listed gap in the transmission block | `signal-triage-register.md:750`; `altdata/transmission.py:184`, `:215` |
| B: the internal-order cycle as a coequal lens in XXVII | **Drafted** on `origin/library-xxvii` (session B, B62, 24–25 Oct), §2.3 of XXVII's Draft 1, built from the references above because the order was not found; not merged | `origin/library-xxvii:docs/briefs/library-xxvii-notes.md:35–40` |
| The ten-item work order (§7) | **Not recorded in the repository.** The work plan placed it at Audit #4, but Audit #4's agenda carries no line for it | `workplan-v3-2026-10-02.md:44`; `docs/briefs/audit-4-agenda.md` (no entry) |

## 4. Needs you

1. **The original file.** Please paste the 13 Sep 2026 order from the chat. It will be filed verbatim beside this record as `docs/change-order-amendment-3-2026-09-13.md`, with its ten-item work order, and the index row will point to it.
2. **The number.** Two orders are called "amendment #3": the architecture's Part 29 (5 Sep, eight tactical additions) and this one (13 Sep). Say which keeps the number when the original is filed, or whether this one is renumbered.
