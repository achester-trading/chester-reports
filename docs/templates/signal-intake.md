# Signal Intake Template

Every proposed signal — a chart, a post, a paper, a chat question — is written on
this template before it can enter the [Signal Triage Register](../signal-triage-register.md).
The six fields and four rules come from §1.1 and §1.3–1.6 of the
[signal-triage change order](../change-order-signal-triage-2026-09-25.md), signed
2026-09-26. File the result as the register's next free SR number; numbers are
never reused.

Copy everything below the line into the register as a new `### SR-n` entry.

---

### SR-n <Item> (<source>, <date>) — Thread <R / X / E / A / C / D>

**1. Home.** Report(s); book — A allocation / B swing / C tactical / D no fixed
horizon; owning paper.

**2. Mechanism.** The edge or read; source and evidence; which existing pillar,
overlay, market-state dimension or input already covers it. If one already
covers it, say so — the proposal is then a member or an evidence line, not a new
signal.

**3. Data.** Source, cost, cadence, `available_at`, first-print availability.
**Where it lives** — source module (`altdata/sources/<name>.py`, or a
`manual_input` key) and registry key (`fred.*`, `calc.*`, …).

**4. Signal rights requested.** One of: narrow flag / composite input /
confidence modifier / base rate only / none.

**5. Validation.** Episodes; statistic; pass condition; falsifier; review date.
Gates run offline under `tools/calibration/` and write a dated ledger to
[`docs/ledgers/`](../ledgers/README.md).

**6. Disposition.** Adopt / defer / reject, with the reason.

---

## Checklist — the four intake rules

Tick each before filing. An unticked box is a reason to defer, not to file.

- [ ] **Third-party rule (§1.3).** The chart's or post's own conclusion is
      recorded in Mechanism, and nothing in Rights depends on it. Rights come
      only from the mechanized version passing its gate.
- [ ] **Point-in-time rule (§1.4).** Every new feed named in Data carries
      `available_at`. Revised macro series are taken as first-print vintages
      where ALFRED offers them; a signal that survives only on revised data is
      logged and gets no rights. Surveys, reports and papers are keyed on
      publication date, never fieldwork date. Manual inputs carry the date the
      operator entered them.
- [ ] **Projection rule (§1.5).** If the source carries a projected, estimated or
      scenario segment, the entry records the date its actual data ends, the
      projection's stated assumption, and the label
      `PROJECTION (data to <date>; assumes <…>)`. A projection never becomes a
      print and never inherits the post's language. Fixture: SR-18.
- [ ] **Definition rule (§1.6).** The construction is written down — numerator,
      denominator, window, source. Without it the entry is filed as
      `DEFERRED — definition required` and goes no further. Fixture: SR-19.

## Also check before filing

- [ ] **Rights boundary (§1.7).** The rights requested are REPORT_OK-class: the
      item cannot raise DECISION_BLOCKED, produce a Decision Packet, enter the
      Monthly or Top & Bottom composite, or change a Disruptive Themes factor,
      scenario or theme text.
- [ ] **One regime (§1.10).** The item computes no regime, cell, tag or state of
      its own. A regime-like read is proposed as a member, sub-state or
      contradiction row of the market-state object (`docs/market-state.md`).
- [ ] **Not already rejected (§12).** The item does not re-propose anything in the
      register's explicit-rejections list.
