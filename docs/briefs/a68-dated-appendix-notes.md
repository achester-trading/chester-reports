# A68: the dated-appendix queue applied to the papers' dated appendices (24 Oct 2026, overnight)

Docs only and branch-only. Appendices only: no word of any paper's body changed. Each paper's diff is additions inside a dated appendix and nothing else. Where a paper ends on its closing footer ("---" then "*End of white paper.*", or Equities' version line), the new appendix sits before the footer.

## Base

`a68-dated-appendix` branches from `origin/a67-doctrine-2-pack` at its tip, `c0a628dc`.

## What moved where

`docs/dated-appendix-queue.md` held 14 entry sections. Eight moved; six stay under "Open items: no home", each with its reason added as a new line beneath it (the queue's rule: entries are added, never rewritten).

**Each new appendix** carries the library gate's form: "## Appendix X — Dated: Records from the signal-triage orders (as of 24 October 2026)". Each entry is dated in its `###` heading (none later than the as-of) and keeps its wording as queued, with its batch item named.

| Paper (short name) | Appendix | Entries | From |
|---|---|---|---|
| The Rate and Liquidity Machine | B (new) | 3 | Batch 5 item 24 (the stock-bond flag's 5.25% crossing, 16 Oct); Batch 14 item 64 (the 10-year and real 10-year highs, 21 Oct); Batch 14 item 70 (the 10-year at 8%, 19 Oct) |
| Equities | D (new) | 1 | Batch 14 item 63 (the capex chain's reference weights, August 2026) |
| Positioning and Flows | B (new) | 1 | Batch 15 item 74 (the prime-brokerage short book, 22 Oct) |
| Disruptive Themes | B (new) | 3 | Batch 5 item 23 (power construction against data centers; manufacturing construction, 9 Oct); Batch 15 item 76 (AI names' CDS levels and AI borrowing, 20 Oct, **unverified**) |
| Base Rates | C (the Book A rule table), one row | 1 | Batch 5 item 24: queued as "A-6", entered as **A-8** |

**Counts:** 9 entries applied across 5 papers. Rates 3, Equities 1, Positioning 1, Disruptive Themes 3, Base Rates 1.

**Commits:** one per paper, each with its rebuilt HTML edition (`74aa850b`, `3091ca49`, `3624d43b`, `28e2160a`, `a07a6949`), then the queue and these notes.

### Placed by the register entry, not by a paper the queue named

- **The stock-bond flag line (Batch 5 item 24).** The queue named no paper and suggested XXVII, which is not written. It amends SR-9, and SR-9's home is the Rate and Liquidity Machine (`docs/signal-triage-register.md`, SR-9 "Home").
- **The CDS levels and AI borrowing (Batch 15 item 76).** They amend SR-16, whose home is "Disruptive Themes Factor I evidence log".
  - They go in Disruptive Themes' new Appendix B, not Appendix A. Appendix A's entries take a fixed form (a mechanism-scan item, a narrative-register proposal, the operator's confirmation), and these records have none of it.
- **The 10-year records (items 64 and 70).** No paper was named. They are placed by their series: DGS10 and DFII10, and the 10-year attribution, are the Rate and Liquidity Machine's.
- **The XII notes (Batch 5 item 23).** The order's "XII" is not the library's XII, which is the Daily Cascade paper. The queue says "the home is Ari's to name" and that the thesis is argued in Factor I, so they are in Disruptive Themes, Factor I's paper. **The operator may name another home.**

### The rule-table row

Base Rates' Appendix C says "Rows are added with their date and never renumbered". A-6 (the stock-bond regime word) and A-7 (the duration scenario modifier) were taken on 17 Oct. So the queued "A-6" is entered as **A-8**, dated 24 Oct 2026 and noting "drafted 9 Oct 2026 as 'A-6'", for the operator's accept-all.

### Verify items

No queued entry carries an auto-discard date: no order since Batch 3 rules one for these records. Item 76's two records are "not verified against a primary source", so they go in headed **unverified** with "no auto-discard date was ruled by the order", rather than as "unverified, auto-discard <date>" rows.

## Left in the queue ("Open items: no home")

| Entry | Why no paper takes it |
|---|---|
| The long-bond cycle chart (Batch 5 item 18) | the queue names XXVII, which is reserved and not written |
| The sovereign fragility scorecard's layout (Batch 5 item 21) | a by-hand data line's layout, not a dated record; not live without the operator's yes (ruling (b) of 16 Oct) |
| The "what's driving 5.3%" pair (Batch 5 item 26) | its home is `docs/narrative-register-pairs.md`, a register file; the pair's body has not landed there yet (only its heading and Batch 6 item 35's bear side) |
| The housing intervention (Batch 14 item 69) | its home is item 20's ledger, which is not built |
| NAR's pending sales (Batch 14 item 68) | its home is item 36's ledger at its next edition |
| The AI-lab S-1 record (Batch 15 item 75) | its home is the AI-lab financials ledger, which already carries the figures as a provisional row (D21) |

## Body changes refused (needing a ruling)

1. **Batch 14 item 63.** The order adopts BNP Paribas's weights "as a standing reference table … in the Equities paper's AI-rings section". Placing it in that section is a body edit, so it is refused. The entry is in Equities' dated Appendix D as the paper's citation instead; the section itself waits for a ruling or the paper's next revision.

No other entry's wording asks for a body change.

## Gates

- `check_library`: 27 papers, 0 failures, 0 warnings.
  - Before the HTML rebuild, it failed with [10] on the five editions, so each touched paper's edition was rebuilt with `tools/build_paper_html.py`.
- `validate_readability`: 67/0. It covers the stacked reports, not the appendices; run as asked.

## CI

| Run | On | Result |
|---|---|---|
| read once after the push | the A68 tip | see the report |
