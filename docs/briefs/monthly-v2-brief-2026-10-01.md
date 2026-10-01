# Brief — Monthly v2: a storyline, a look back and ahead, and a voices register

| | |
|---|---|
| Status | **Ruled 2026-10-01 14:45 ET** — Ari: "yes, to both" (adopt Monthly v2, Phase A for the 1 Nov edition; build the voices register, Phase B, with "no stored source, not printed" from day one) |
| Owner | Ari Chester |
| Binding on | Claude Code sessions building the Monthly |
| Precedence | Below Part 26, the current change-orders edition, and Amendments #4–#5. Consistent with the 4b ruling that the regime is read from the state object, never written fresh. |
| Reference | The pre-rebuild Monthly's "Institutional Desk Commentary" and Themes A–F (May 2026 edition), supplied by Ari as the model for tone and structure |

## Why

The halved Monthly (4b, 23 Sep) made every sentence traceable and every number audited, and in doing so lost the thread a reader needs to absorb the month. The older edition read well but could not be checked: its own header said "confidence capped — interpretations of public statements", its figures carried no stored source, and a voice's "inflection" was asserted rather than computed. v2 keeps the 4b discipline and restores the storyline.

## The document, in order

1. **The month in one page.** Five numbered takeaways, then one narrative paragraph that the rest of the document follows. Every section below opens with one sentence tying it back to that paragraph.
2. **Looking back, by theme.** Themes: Liquidity & Plumbing · Fiscal Dominance & Dollar · Fed Policy Path · Credit Cycle · Equity Positioning & Sentiment · Geopolitics & Reserve Currency. Each maps to the state object's dimensions and to the narrative register's stories (AI capex durability, fiscal dominance, midterm cycle, yen carry). Each item carries one tag — **CONSENSUS / NEW / DISSENT / CORRECTION** (CORRECTION = we or a source said otherwise last month) — and a dated source (store key, claim id, or event id). Closes with **What changed from last month**, a list computed from the store, never written by hand.
3. **Voices** (Phase B). Sell-side desks · buy-side managers · independent strategists. One row per voice: current view (one line), source and date, status **REITERATED / NEW / INFLECTED / SILENT**, computed against that voice's stored entry from the prior month. Then **Consensus vs contrarian**: where consensus sits, who dissents, and whether the dissent is backed by positioning (13F, flows) or only words.
4. **Looking ahead, 2–3 months.** The forward calendar from the events table (FOMC, CPI, payrolls, the 3 Nov midterms, earnings that matter). The scenarios with weights and each weight's Brier beside it. For each scenario: **what would change our mind** — an observable, dated signpost.
5. **Where our read lands.** Our position against consensus, stated through the scenario weights and the books, not free prose. One paragraph.
6. The existing sections (regime from the object, Top & Bottom, alternative assets, the register's month, appendix) follow, each opened by its tie-back sentence.

## Rules

- **No stored source, not printed.** Every named voice, quoted figure and attributed view is backed by a stored record (source, URL, published date, retrieved_at, tier). A view the scan did not retrieve does not appear, however well known.
- **Status is computed.** NEW / INFLECTED / REITERATED / SILENT compare this month's stored entry with last month's; the model may describe an inflection, never declare one.
- **Tags are checked.** CONSENSUS needs ≥ 2 tier-1–2 sources; DISSENT names its source; CORRECTION cites the prior statement it corrects.
- **Same audits.** Numeral, label/type, state and citation audits on every paragraph; a failing paragraph is withheld with its reason, as now.
- **Our read is bounded.** "Where our read lands" may only restate positions the scenario weights and books already hold.
- **Positioning claims** (13F, cash levels, put books) come from SEC EDGAR or a tier-1–2 report, dated to the filing period.

## Build

**Phase A — for the 1 Nov edition (~6 h).** Sections 1, 2, 4, 5 and the tie-back sentences, from data the system already holds (store, events, claims, narrative register, scenarios). Section 3 prints "Voices register not yet built" until Phase B lands. Gate: a fixture month renders all sections; a theme item without a source is refused; "What changed" is computed.

**Phase B — the voices register (~10 h).** A `voices` table (voice, affiliation, kind, view, source_url, published_at, retrieved_at, tier, horizon); the monthly news scan extended to strategist and desk commentary from tier-1–2 outlets; status computation; 13F via SEC EDGAR (dormant until `CHESTER_SEC_CONTACT` is in the box's `.env` — Ari's step). Gate: a voice with no source is refused; status is reproducible from stored rows.

## Not in scope

Paywalled research the box cannot retrieve; social-media sentiment beyond the existing ApeWisdom logger; any change to how the regime is computed.
