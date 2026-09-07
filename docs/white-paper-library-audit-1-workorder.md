# White Paper Library — Audit 1 Work Order

**For:** Claude Code, in `chester-reports` on main (audited at `930da6f`, 6 Sep 2026)
**Companion:** `docs/white-paper-library-audit-1.md` (the findings; IDs A1–A11, B1–B6 below refer to it)

## How to execute

- Work through Sections 1–10 in order. **One commit per section**, message prefixed `library-audit-1/S<n>:`.
- Line numbers below are from the audited commit and will drift; **match on the quoted strings**, not the line numbers. If a quoted string is not found exactly once, stop and ask before editing.
- Section 1 renames files. Every later section uses the **new** filenames.
- After Section 10 exists, run `make library-check` at the end of every section and keep it green.
- Do not touch: numeric market levels in any paper (see D7); anything under `reports/`, `snapshots/`, `state/`, `register/`, `data_store/`; the appendix of the guide.
- Anything marked **REVIEW** is left for Ari to read before merge — commit it, flag it in the final summary, do not merge-squash it into other sections.

## Decisions (already made — apply, don't revisit)

| ID | Decision |
|---|---|
| D1 | Inside a paper's body, other papers are cited **by name only**. That includes title-form references ("White Paper I") — convert them. Mastheads keep their own numeral and may name their neighbours' numerals. |
| D2 | **The masthead owns the version string; the guide copies it.** One-time exception now: five mastheads are behind the guide (S3) — bump them to the guide's label. After that, never edit a version in the guide without the masthead. |
| D3 | The library refers to the Daily Cascade by its architecture version, **v2**. Report build numbers (v12) live in code and commit messages, not in papers. |
| D4 | Rule citations. Outside the Doctrine, its rules are cited as **`Doctrine Rule N`** (a phrase containing "Doctrine" within the same sentence — "the Doctrine's Rule 6" is compliant). Section-local rules cited from another paper carry the owner's prefix: **`DC 2.7.1`** (Daily Cascade), **`DH 18.1`** (Dealer's Hand). Inside the owning paper, unprefixed dotted IDs stay as they are. Bare `Rule N` outside the Doctrine is not allowed. |
| D5 | HTML-canonical papers (figures live only in the HTML edition): **V Currencies, XIII Dealer's Hand, XIV Technical Indicators, XXII Options as Expression, XXIII Evidence and Inference, XXIV Earnings** — plus the guide. XX and XXI are Markdown-only. Built HTML editions belong in `docs/html/`. |
| D6 | Filenames: `docs/whitepapers/<slug>-whitepaper.md`, hyphens only, slug from the paper's title, **no version or draft number in the filename**. Superseded editions go to `docs/whitepapers/archive/`. |
| D7 | Quoted market levels are **not** retro-aligned. New convention: any quoted level names its series and as-of date; spread levels are ICE BofA OAS via FRED (`BAMLH0A0HYM2`, `BAMLC0A0CM`, `BAMLH0A3HYC`) unless stated otherwise. |
| D8 | Series numerals are **stable accession IDs**; they are no longer claimed to be reading order. Reading order is what the guide's tables show. Never renumber. |
| D9 | The guide's six missing one-page entries are drafted by Claude Code in the existing template and flagged **REVIEW**. |

---

## Section 1 — Housekeeping, paths, and renames (A3, A9)

1. `git rm docs/options-expression-whitepaper.md` (the 6,148-word early draft; the 15,412-word current paper is in `docs/whitepapers/`).
2. `git rm docs/whitepaper` (1-byte stray).
3. `mkdir docs/whitepapers/archive` and `git mv docs/whitepapers/paper-building-and-validating-a-systematic-book-draft1.md docs/whitepapers/archive/systematic-book-draft1-2026-08-31.md`. Add a one-line `archive/README.md`: "Superseded editions, kept for the record. Not part of the library roster."
4. Rename with `git mv` (history must follow):

| From | To |
|---|---|
| `disruptive_themes_whitepaper.md` | `disruptive-themes-whitepaper.md` |
| `tail_scenarios_whitepaper_II.md` | `tail-scenarios-whitepaper.md` |
| `monthly_macro_whitepaper.md` | `monthly-macro-whitepaper.md` |
| `rates_liquidity_whitepaper.md` | `rates-liquidity-whitepaper.md` |
| `currency-white-paper.md` | `currencies-whitepaper.md` |
| `credit-white-paper.md` | `credit-whitepaper.md` |
| `energy-white-paper.md` | `energy-whitepaper.md` |
| `metals-white-paper.md` | `metals-whitepaper.md` |
| `crypto-white-paper.md` | `digital-assets-whitepaper.md` |
| `volatility-white-paper.md` | `volatility-whitepaper.md` |
| `equities-white-paper.md` | `equities-whitepaper.md` |
| `technical-indicators-white-paper.md` | `technical-indicators-whitepaper.md` |
| `paper-portfolio-construction-across-regimes-draft1.md` | `portfolio-construction-whitepaper.md` |

   Already conforming, leave as is: base-rates, daily-cascade, dealers-hand, earnings, evidence-inference, international-equities, operating-doctrine, options-expression, positioning-and-flows, systematic-book. Reserved for when Ari commits it: `tops-and-bottoms-whitepaper.md`.

5. `git grep -n` every old filename across the whole repo (known hits: `CLAUDE.md`, `TODO.md`) and update. In `CLAUDE.md`, the line naming `docs/options-expression-whitepaper.md` as XXII becomes `docs/whitepapers/options-expression-whitepaper.md`.
6. Replace the empty `docs/whitepapers/readme.md` with three lines: what the folder is, "the library guide (`docs/white-paper-library-guide.md`) is canonical for the roster and numerals", and a pointer to `archive/`.

---

## Section 2 — Numeral sweep (A1, D1)

Replace the stale numeral with the name. Where the numeral is inside a bold table cell, keep the bold on the name.

**credit-whitepaper.md**
- `*Rates & Liquidity* (X) owns the price of money` → `*The Rate and Liquidity Machine* owns the price of money`
- `Top & Bottom (V) implements the regional-bank stress indicators` → `*Tops and Bottoms* implements` (if context means the *report*, use `the Top & Bottom report` — read the sentence)
- `the currency paper (VIII) flags` → `the *Currencies* paper flags`
- Common-bus table rows: `**Credit (XI)**` → `**Credit**`; `**Currencies (VIII)**` → `**Currencies**`; `**Metals (VII)**` → `**Metals**`; `**Volatility (XIII)**` → `**Volatility**`; `**Energy (XII)**` → `**Energy**`
- `Credit vol (XIII), MOVE, the funding measures (X).` → `Credit vol (the *Volatility* paper), MOVE, the funding measures (*The Rate and Liquidity Machine*).`
- `CDX implied vol (XIII).` → `CDX implied vol (*Volatility*).`; `Cross-currency basis and SOFR–IORB (X, VIII).` → `… (*The Rate and Liquidity Machine*, *Currencies*).`

**energy-whitepaper.md** — two occurrences of `the currency paper (VIII)` → `the *Currencies* paper`

**volatility-whitepaper.md**
- two occurrences of `*The Dealer's Hand* (IX) and the Daily Cascade paper (V)` → `*The Dealer's Hand* and the Daily Cascade paper`
- two occurrences of `the *Credit* paper (XI)` → `the *Credit* paper`
- `*The Dealer's Hand* (IX)` (standalone) → `*The Dealer's Hand*`
- `the CFTC yen position (VIII)` → `the CFTC yen position (see *Currencies*)`
- `(dealers long gamma, per IX)` → `(dealers long gamma, per *The Dealer's Hand*)`

**daily-cascade-whitepaper.md** — `Companion IX, *The Dealer's Hand*, derives` → `*The Dealer's Hand* derives`

**technical-indicators-whitepaper.md** — colophon: `the Dealer's Hand (IX) for hedging-derived levels; the Daily Cascade paper (V) for the block structure and candlestick display discipline; the Monthly manual (III) for` → drop all three parentheticals.

**positioning-and-flows-whitepaper.md** — `*Equities* (Companion XV) treats buybacks` → `*Equities* treats buybacks`

**tail-scenarios-whitepaper.md** — body text only (keep the H1 `WHITE PAPER II` and the masthead lines): `White Paper I's` → `the *Foundations* paper's`; `White Paper I` → `the *Foundations* paper`. Expect ~20 replacements. Read each; where the sentence already says "the Foundations paper", don't double it.

**disruptive-themes-whitepaper.md** — the `White Paper II` sentence is rewritten in Section 6; leave it here.

Verify: `git grep -nE "\(([IVX]{1,5})\)" docs/whitepapers` returns only masthead lines and non-paper uses (Factor II, Part V, Phase 2 etc.). The Section 10 check automates this.

---

## Section 3 — Mastheads (A8, D2)

Add the numeral, in the existing "Series placement" sentence pattern, where it is missing:
- `base-rates-whitepaper.md` → Companion **XX**
- `options-expression-whitepaper.md` → Companion **XXII**
- `evidence-inference-whitepaper.md` → Companion **XXIII**
- `earnings-whitepaper.md` → Companion **XXIV**

Replace "(numeral assigned by the library guide on commit; …)" with "— per the library guide, which is canonical for numerals; cross-references in this paper are by name" in each.

One-time version sync, guide → masthead:
- `dealers-hand-whitepaper.md` masthead `Companion XIII · Version 1.0 · August 30, 2026` → `Companion XIII · Version 1.1 · August 30, 2026, extended September 5, 2026` (the colophon already says 1.1 — leave it)
- `base-rates-whitepaper.md` `Version: 1.0` → `Version: 1.1`
- `international-equities-whitepaper.md` `Version: 1.0` → `Version: 1.1`
- `options-expression-whitepaper.md` `Version: 1.0` → `Version: 1.4`
- `positioning-and-flows-whitepaper.md` `Version: 1.0 — Draft, 6 September 2026` → `Version: 1.2 — Draft, 6 September 2026`

Leave Version 1.0 in `systematic-book-whitepaper.md`, `evidence-inference`, `earnings` (guide says Draft 1 — same edition).

---

## Section 4 — Headings and figure numbers (A7, A10)

1. **Daily Cascade — insert the dropped Part II.** The Part I intro reads "*Sections §05–§07 … Everything in Parts II and III either confirms or contradicts what these three establish.*" So Part I is Chapters 1–3 and Part II is Chapters 4–8 (§08–§12). Insert a `# PART II — …` heading immediately before `## CHAPTER 4 — §08 VOL SURFACE & SKEW`, plus a two-line italic intro in the style of Part I's. Title it from the paper's own block vocabulary for §08–§12 (the guide calls this the Confirmation block; use the paper's term if Part 0 or Chapter 22 names it differently). Do not renumber Parts III–VI.
2. **Tail Scenarios — insert the promised Part 1.** Insert `# PART 1 — THE FAMILIES` immediately before `# FAMILY A — FUNDING, DURATION AND PLUMBING`. The Contents already lists it.
3. **Evidence and Inference — figures 1, 2, 3, 5, 6 → 1–5.** Renumber in the `.md` (labels, placeholders, and in-text references). Flag in the final summary that the HTML edition must be regenerated to match, since it is canonical and untracked.

---

## Section 5 — Rule citation convention (B6, D4)

1. **dealers-hand-whitepaper.md**: references to the Daily Cascade's rules — `why Rule 2.7.1 gates strategy` → `why DC 2.7.1 gates strategy`; `(Daily Cascade Rule 4.7.3)` → `(DC 4.7.3)`; `the cluster-confluence rule (Daily Cascade 21.2)` → `the cluster-confluence rule (DC 21.2)`. Grep the file for every other `Rule \d+\.\d+` that refers to the Daily Cascade rather than to the Dealer's Hand's own rules and prefix it. The Dealer's Hand's own `Rule 18.1`, `Rule 20.1`, `Rule 21.1` stay.
2. **systematic-book-whitepaper.md**: bare Doctrine citations — `Rule 25 of the doctrine` (compliant, leave); `(Rule 5 and the semi-automation contract` → `(Doctrine Rule 5 and …`; `Rule 13 says no trade` → `Doctrine Rule 13 says`; `Rule 11 says the thesis` → `Doctrine Rule 11 says`; `(Rule 16: 6% total open risk` → `(Doctrine Rule 16: …`. Check every remaining `Rule \d+\b` (no dot) in the file and prefix any that lacks "Doctrine"/"doctrine" in the same sentence.
3. Same check in `base-rates`, `evidence-inference`, `international-equities`, `options-expression`, `positioning-and-flows`, `earnings`, `portfolio-construction`: they mostly already say "The Doctrine's Rule N" — leave those; prefix any bare one.
4. Any cross-paper citation of a Daily Cascade dotted rule from `operating-doctrine`, `systematic-book`, `positioning-and-flows`, `technical-indicators` gets the `DC` prefix (e.g. `Daily Cascade 21.2` → `DC 21.2`). Inside `daily-cascade-whitepaper.md` nothing changes.

---

## Section 6 — Version labels and stale text (B3, B4, B5, A11, D3)

- `tail-scenarios-whitepaper.md`: `**Primary: Daily Cascade (v12), daily.**` → `**Primary: Daily Cascade, daily.**`
- `daily-cascade-whitepaper.md`: the two historical mentions — `because v12 made it load-bearing` → `because the v12 report build made it load-bearing`; `The v12 design renders` → `The v12 build renders`. (Historical fact about a build; allowed once it is called a build.)
- `disruptive-themes-whitepaper.md`: the paragraph beginning `One paper remains owed under this series: **White Paper II — the 25 tail scenarios**` → rewrite to past tense: "The companion on the twenty-five tail scenarios — *The Twenty-Five* — was built from the full table in the Monthly report rather than the five delta rows carried here, with the same treatment per scenario." Keep the rest of the paragraph if it still reads true; delete what doesn't.
- `operating-doctrine-whitepaper.md`: `*Positioning & Flows** (the paper to be written next) will, when written, own` → `*Positioning & Flows* owns`; `The Positioning & Flows paper, when written, will introduce new signal families` → `The Positioning & Flows paper introduces new signal families` (fix the verbs in the rest of that sentence); `draw on *Portfolio Construction Across Regimes* when written, and on` → `draw on *Portfolio Construction Across Regimes* (Draft 1; empirical edition to follow), and on`.
- `technical-indicators-whitepaper.md`: both `the shortest paper in the library` → `among the shortest papers in the library`.
- `base-rates-whitepaper.md`: `Extending to 1907 doubles the sample and adds` → `Extending to 1907 takes the sample from eight bears to thirteen and adds`.
- Guide: `the six-cluster dependency map and the four-vote confluence rule` → `the six-cluster dependency map and the three-of-four-cluster confluence rule`.
- Guide, "In draft and planned": delete `emerging markets and China, and` from the deferred-candidates sentence (XXI now covers them); change `**XVI and XIX — Draft 1 editions exist**` to match the mastheads after Section 3 (`XVI Draft 1.2 and XIX Draft 1`).

---

## Section 7 — Formats, levels, numbering conventions (A4, A6, D5, D7, D8)

1. **CLAUDE.md** — rewrite the "Five of those documents exist in two formats" paragraph to this list and nothing else: the guide, V `currencies-whitepaper.md`, XIII `dealers-hand-whitepaper.md`, XIV `technical-indicators-whitepaper.md`, XXII `options-expression-whitepaper.md`, XXIII `evidence-inference-whitepaper.md`, XXIV `earnings-whitepaper.md`. Keep the "HTML canonical for reading, Markdown canonical for editing, regenerate from the .md, never the reverse" rule verbatim. Replace "no `.html` is tracked in this repo" with: "Built HTML editions live in `docs/html/`, one per HTML-canonical paper, named `<slug>-whitepaper.html`; `make library-check` warns when one is missing."
2. **CLAUDE.md** — add, after the numerals paragraph, a short block titled **Library conventions** containing D1, D3, D4, D6, D7, D8 in one line each (copy the wording from the Decisions table).
3. **Guide, formats note** (the blockquote at the top): list the same six papers; remove Base Rates (XX) and International Equities (XXI).
4. **Guide**: `*Numerals are the canonical series IDs, assigned here in reading order from the top down — the macro and disruptive layer first, then the structural asset classes, then market timing, then the micro and execution layer.` → `*Numerals are the canonical series IDs. They were first assigned in reading order and are now stable accession numbers — later papers took the next free numeral wherever they sit — so reading order is what the tables above show, not the numeral sequence. Numerals are never reassigned.`
5. Create `docs/html/README.md`: what belongs here (the six built editions), the naming rule, "regenerate from the .md; an HTML that disagrees with its .md is stale." Ari drops the files in; the check only warns.
6. Note for the final summary (not an edit): `fx_charts.py`, described for regenerating the Currencies charts, is not in `altdata/`; Ari has it in `altdata.zip` from the 3 September session.

---

## Section 8 — Guide roster reconciliation (A5)

Work from measured facts (`wc -w` on each file, rounded to the nearest 50), not from memory.

1. Header sentence: replace `Nineteen companion documents as of 6 September 2026 — sixteen full papers, one doctrine, and two Draft-1 editions … roughly 307,000 words` with the true count: twenty-four numerals in the roster, twenty-three papers in the repo (X *Tops and Bottoms* is on the roster but not yet committed — say so in one parenthesis), the measured word total of the committed papers, dated today.
2. At-a-glance table, "Size" column: measured word count for **every** paper (II, VI, XIII are the ones known wrong; do all), and the version string **copied from each masthead** after Section 3.
3. Move the **XXIV Earnings** row from the Micro & execution block to the Market structure block (after XXI) so it matches the Contents table and the paper's masthead.
4. Make the at-a-glance row order identical to the Contents table order (Contents is canonical): …XVI, XVII, XVIII, XIX, XXIII.
5. Dependency table: `XVI Positioning & Flows *(Draft 1)*` → `*(Draft 1.2)*`; `XIX Systematic Book *(Draft 1, as-built)*` unchanged.
6. Update the Contents table's `(#anchors)` if any heading text changed. Run the link check (Section 10) — it must still report zero broken anchors.

---

## Section 9 — Six missing one-page entries (D9) — REVIEW

Add `## XVII.`, `## XX.`, `## XXI.`, `## XXII.`, `## XXIII.`, `## XXIV.` sections in numeral order among the existing ones (XVII after XVI; XX–XXIV after XIX), each in the exact template the existing entries use (title line, **Companion to · size**, **What it contains.**, **Main takeaways** as 3–4 bullets, **How to use it**). Source material: the at-a-glance description, the paper's own Reader's note and closing/colophon, and its Contents. Do not invent claims the paper doesn't make; where the paper is a Draft, say what triggers its next edition. Flag the commit **REVIEW**.

---

## Section 10 — The gate: `tools/check_library.py` + `make library-check`

Add the check to the repo's existing gate list and CI matrix, following the pattern of the current `Makefile` targets. Exit non-zero on any **fail**; print **warn** items but don't fail on them.

Checks (all scoped to `docs/whitepapers/*.md` excluding `archive/`, `readme.md`; "masthead" = everything before the first `---` line):

| # | Check | Level |
|---|---|---|
| 1 | Every guide numeral in the at-a-glance table has a file whose masthead carries that numeral; every file has a guide row. (X is allowed to be absent until `tops-and-bottoms-whitepaper.md` exists → warn, not fail.) | fail |
| 2 | No roman-numeral paper reference in any body: regex `(paper|Paper|Companion|White Paper)\s+[IVX]{1,5}\b` and `[A-Za-z*'’&]+\s\([IVX]{1,5}\)` outside mastheads, with an allowlist for `Part`, `Chapter`, `Factor`, `Scenario`, `Phase`, `Gate`, `Tier`, `Book`, `Family`, `Era`, `Lens`, `Type`, `Class`, `Quadrant`, `Ring`, `Pillar` and the H1 `WHITE PAPER II`. | fail |
| 3 | Part / Chapter / numbered-section sequences are consecutive within each paper (A/B suffixes like `V-B`, `III-B` allowed). | fail |
| 4 | Figure numbers within a paper are consecutive from 1 (`Figure set 8a/8b` counts as 8). | fail |
| 5 | Outside `operating-doctrine`, every `Rule \d+\b` (no dot) has "Doctrine" or "doctrine" within the same sentence; every cross-paper dotted rule citation carries `DC ` or `DH `. | fail |
| 6 | Filenames match `^[a-z0-9-]+-whitepaper\.md$`. | fail |
| 7 | Every path named in `CLAUDE.md` exists. | fail |
| 8 | Internal `[text](#anchor)` and `[text](path)` links resolve across `docs/`. | fail |
| 9 | Masthead version string equals the guide's at-a-glance version string for that numeral. | fail |
| 10 | For each HTML-canonical paper (D5 list), `docs/html/<slug>-whitepaper.html` exists. | warn |
| 11 | Guide header word total is within 5% of the measured sum. | warn |
| 12 | Body contains "when written", "remains owed", "to be written next" — stale forward references. | warn |

Wire it: `make library-check` target; add it to the `make gates` list (or whatever the aggregate target is called) and to the CI matrix. Run it once at the end and paste the output into the final summary.

---

## Final summary to Ari (Claude Code writes this at the end)

1. Commits made, one line each.
2. `make library-check` output.
3. Items needing Ari: commit `tops-and-bottoms-whitepaper.md`; drop the six HTML editions into `docs/html/`; regenerate the Evidence and Inference HTML with figures renumbered; add `fx_charts.py` from `altdata.zip`; review Section 9's six guide entries.
4. Anything the work order said that didn't match the files, and what was done instead.
