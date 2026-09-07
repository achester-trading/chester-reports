# White Paper Library — Audit

**Scope:** Guide & structure hygiene · Cross-paper consistency
**Source:** `achester-trading/chester-reports` @ `930da6f` (main, 6 September 2026), read directly from GitHub
**Corpus:** 22 current papers + 1 superseded draft in `docs/whitepapers/` (~337,500 words in current papers), the library guide, and `CLAUDE.md`
**Not auditable from the repo:** *Tops and Bottoms* (X) — not in the tree or in git history; every HTML edition — none is tracked, so the figures in the HTML-canonical papers were not checked

Line numbers refer to the committed `.md` files. Severity: **High** = wrong information a reader would act on, or a breach of a rule the repo's own governance says must hold · **Medium** = inconsistencies that mislead or drift · **Low** = labels, naming, stale phrasing.

---

## Summary

| | High | Medium | Low |
|---|---|---|---|
| A. Guide & structure hygiene | 3 | 5 | 3 |
| B. Cross-paper consistency | 0 | 2 | 4 |

The load-bearing conventions are sound: the GEX sign convention, the four books and the $300,000 base, the sizing tiers and heat caps, the three regime dials, the confluence rule, and every "Rule N" citation of the Doctrine agree across papers. The problems are almost all at the seams — the numeral hazard the guide warned about was never fully cleaned up, the guide's own roster and format rules have drifted from the folder, and a handful of shared market facts disagree between papers written days apart.

---

## A. Guide & structure hygiene

### A1 · HIGH — Pre-guide numerals survive in five papers

The guide ("Cross-references and interdependencies") states the rule — *by name, never by numeral* — and says the find-and-replace "takes minutes." It was not completed. Every hit below carries a numeral from the chat-era assignment and is wrong against the guide.

| File | Line | Reads | Guide numeral / correct name |
|---|---|---|---|
| credit-white-paper.md | 21 | *Rates & Liquidity* (X) | IV — *The Rate and Liquidity Machine* |
| credit-white-paper.md | 319 | Top & Bottom (V) | X — *Tops and Bottoms* |
| credit-white-paper.md | 478 | the currency paper (VIII) | V — *Currencies* |
| credit-white-paper.md | 526 | **Credit (XI)** | VI |
| credit-white-paper.md | 527 | **Currencies (VIII)** | V |
| credit-white-paper.md | 528 | **Metals (VII)** | VIII |
| credit-white-paper.md | 529 | **Volatility (XIII)** | XI |
| credit-white-paper.md | 530 | **Energy (XII)** | VII |
| credit-white-paper.md | 559 | Credit vol (XIII) … funding measures (X) | XI *Volatility* … IV *Rates & Liquidity* |
| credit-white-paper.md | 747 | CDX implied vol (XIII) … (X, VIII) | XI … IV, V |
| energy-white-paper.md | 318 | the currency paper (VIII) | V |
| energy-white-paper.md | 326 | the currency paper (VIII) | V |
| volatility-white-paper.md | 151 | *The Dealer's Hand* (IX) and the Daily Cascade paper (V) | XIII … XII |
| volatility-white-paper.md | 198 | the *Credit* paper (XI) | VI |
| volatility-white-paper.md | 253 | the *Credit* paper (XI) | VI |
| volatility-white-paper.md | 446 | *The Dealer's Hand* (IX) | XIII |
| volatility-white-paper.md | 705 | the CFTC yen position (VIII) | V — *Currencies* |
| volatility-white-paper.md | 711 | *The Dealer's Hand* (IX) and the Daily Cascade paper (V) | XIII … XII |
| daily-cascade-whitepaper.md | 313 | Companion IX, *The Dealer's Hand* | XIII (survived into the v2.0 rewrite) |
| technical-indicators-white-paper.md | 250 | the Dealer's Hand (IX) … the Daily Cascade paper (V) … the Monthly manual (III) | XIII … XII … III (only the last is right) |

The common-bus table in Credit (L526–530) is the worst case: five rows, five wrong numerals, in the one table the guide singles out as linking each paper's long-yield exposure to the rates instrument.

Also present, correct but still numeral-form (the rule says by name): *Tail Scenarios* refers to "White Paper I" 20 times (its own series title — defensible), Positioning & Flows L212 "*Equities* (Companion XV)", Foundations L723 "White Paper II". Decide once whether title-form references are exempt.

**Fix:** name substitution per the table, then a repo check that fails on `<paper name> ([IVX]+)` outside mastheads.

### A2 · HIGH — *Tops and Bottoms* (X) is not in the repository

The guide gives it a full one-page entry (~16,000 words est., 38 pages, "three formats from one source"), five papers cite it by name (Base Rates ×4, Earnings ×3, Equities ×2, Positioning & Flows, Systematic Book), and the dependency table lists it as the source of the composite's top-side language and XVII's sizing-by-regime. There is no file under any name in the working tree or in `git log --all`. It was produced as docx → pdf → HTML and the markdown source was never committed.

**Fix:** commit the source `.md` (or a docx → md conversion) as `docs/whitepapers/tops-and-bottoms-whitepaper.md`; until then, mark the guide entry "not in repo."

### A3 · HIGH — *Options as Expression* exists twice, and CLAUDE.md points at the stale copy

| Path | Words | Chapters | Content |
|---|---|---|---|
| `docs/options-expression-whitepaper.md` | 6,148 | 17 | early draft — no Ch 15 scenario matrix, no Ch 16 leverage |
| `docs/whitepapers/options-expression-whitepaper.md` | 15,412 | 19 | matches the guide's Draft 1.4 description |

`CLAUDE.md` line 35 names the root path as the canonical XXII file. Both were committed 6 September via "Add files via upload." A Claude Code session that follows CLAUDE.md will read the wrong paper.

**Fix:** delete the root copy; change CLAUDE.md L35 to `docs/whitepapers/options-expression-whitepaper.md`.

### A4 · MEDIUM — Three sources disagree on which papers are HTML-canonical

| Source | Papers declared HTML-canonical (figures live only in HTML) |
|---|---|
| Guide, formats note (L14) | XIII, XXII, XXIII, XXIV, **XX, XXI** |
| CLAUDE.md (L33–43) | guide, XIII, XXII, XXIII, XXIV; "every other paper is Markdown only" |
| The papers themselves | XIII, XXII, XXIII, XXIV say so in their mastheads. **XX and XXI do not** — neither has a figure placeholder (tables only, 113 and 107 table rows). **Currencies (V)** L374: "The HTML edition embeds charts throughout this Part" (the eight FX figures). **Technicals (XIV)** carries five figure placeholders. The guide's XII entry says "md + html". |

CLAUDE.md wins by its own rule, so the guide's note is wrong about XX and XXI — but CLAUDE.md is silent on V and XIV, which do depend on an HTML edition for their figures. Two related gaps: no `.html` is tracked anywhere in the repo, so the "canonical for reading" editions live outside version control; and the `fx_charts.py` module described for regenerating the currency charts is not in `altdata/`.

**Fix:** one list, maintained in CLAUDE.md and mirrored in the guide's note: XIII, XXII, XXIII, XXIV, plus a decision on V and XIV. Consider tracking the HTML editions (e.g. `docs/html/`, built from the `.md`) so the canonical reading copies survive a laptop.

### A5 · MEDIUM — The guide's roster is internally inconsistent

- **Header (L3):** "Nineteen companion documents … roughly 307,000 words." The roster has 24 numerals; the folder holds ~337,500 words of current papers.
- **One-page summaries** run I–XVI, XVIII, XIX. The guide promises "one page per paper"; **XVII, XX, XXI, XXII, XXIII, XXIV have none** — they exist only as at-a-glance rows.
- **XXIV Earnings** is filed under *Micro & execution* in the at-a-glance table (L76) but under *Market structure* in the Contents table (L45) and in its own masthead.
- **Ordering** differs between Contents (…XVIII, XIX, XXIII) and at-a-glance (…XVIII, XXIII, XIX).
- **XVI** is "Draft 1.2" (at-a-glance), "Draft 1" (dependency table), and "Draft 1 editions" (In draft and planned).
- **Sizes:** XIII "not yet measured" (19,371); II ~21,300 (24,562); VI ~15,400 (18,128 — the guide never absorbed the §29 addition).

### A6 · MEDIUM — The guide's numbering rule contradicts its numbering

L87: numerals are "assigned here in reading order from the top down." XX–XXIV were appended afterwards and sit out of reading order (XX between X and XI; XXII after XIV; XXI and XXIV inside market structure; XXIII before XIX). Renumbering is rightly forbidden — the last renumbering broke every in-text reference (A1). So the sentence, not the numbers, should change: numerals are stable series IDs assigned in order of accession; reading order is what the tables show.

### A7 · MEDIUM — Missing part headings in two papers

- **Daily Cascade (XII):** Parts 0, I, III, IV, V, VI. There is no Part II — Chapters 1–8 sit under Part I (L156) and Part III begins at Chapter 9 (L813). "Part II" appears nowhere in the file.
- **Tail Scenarios (II):** the Contents (L22) promises "Part 1 — The Families" and the body refers to Part 1 (L1458, L1530, L1552), but no `# PART 1` heading exists; the seven family sections follow Part 0 unheaded. Parts 0, 2, 3 are present.

### A8 · MEDIUM — Version labels drift between masthead, colophon, and guide

| Paper | Masthead | Colophon / guide |
|---|---|---|
| Dealer's Hand (XIII) | "Version 1.0 · August 30, 2026" (L5) | colophon "Version 1.1 · extended September 5" (L1114); guide v1.1 |
| Options as Expression (XXII) | "Version: 1.0" | guide "Draft 1.4" |
| Base Rates (XX) | "Version: 1.0" | guide "Draft 1.1" |
| International Equities (XXI) | "Version: 1.0" | guide "Draft 1.1" |
| Positioning & Flows (XVI) | "1.0 — Draft, 6 September" | guide "Draft 1.2" |

And four mastheads still read "numeral assigned by the library guide on commit" with no numeral: Base Rates (XX), Options as Expression (XXII), Evidence & Inference (XXIII), Earnings (XXIV). The guide says mastheads are relabelled on commit; these were committed unlabelled.

### A9 · LOW — Superseded and stray files; four filename conventions

- `docs/whitepapers/paper-building-and-validating-a-systematic-book-draft1.md` (5,416 words, 31 Aug) is superseded by `systematic-book-whitepaper.md` (XIX, 6 Sep). Both are present.
- `docs/whitepaper` — a 1-byte stray file. `docs/whitepapers/readme.md` — empty.
- Filenames follow four patterns (`-white-paper.md`, `-whitepaper.md`, `_whitepaper.md`, `paper-…-draft1.md`), and two don't match their titles (`crypto-` for *Digital Assets*, `currency-` for *Currencies*). Standardizing is safe now — there are zero file links in the docs — and gets harder once the claims registry references paths.

### A10 · LOW — Figure numbering

Evidence & Inference figures are numbered 1, 2, 3, 5, 6 — no Figure 4. Options as Expression numbers Figures 1–10 plus "Figure set 8a/8b"; the guide claims 27 computed figures — verify the count against the HTML.

### A11 · LOW — Stale guide text

- "In draft and planned": "emerging markets and China … remain lower-priority candidates" — XXI now carries a full China part and EM chapter.
- XII entry (L74): "the four-vote confluence rule" — the papers state it as **three of the four daily clusters** (Daily Cascade L1169, Positioning & Flows L411).

### Checked and clean

- **0 broken internal links or anchors** across all 36 files in `docs/`.
- **Chapter and section sequences intact** in every paper (Credit §1–40, Energy §1–40, Metals §1–38, Volatility §1–42, Currencies §1–33, Digital Assets §1–27, Equities §1–36; chapters I 1–8, III 1–11, XII 1–24, XIII 1–21, XIV 1–8, XX 1–16, XXI 1–17, XXII 1–19, XXIII 1–16, XXIV 1–20). The "Part V / V-B" and "III / III-B" pairs in Credit, Energy, Metals, Volatility, Rates are a deliberate house convention, not gaps.
- Doctrine's **29 rules** present and numbered 1–29; the guide's description of §9.2 (the behavioral paper's fields) is accurate.

---

## B. Cross-paper consistency

### B1 · MEDIUM — Gold's August 2026 move is stated two ways

| Paper | Line | Claim |
|---|---|---|
| Foundations (I), anchored 29 Aug | 423, 447 | "Gold rose 14% in August to ~$4,650" |
| Metals (VIII), late Aug | 29 | "rallied roughly 10–11% during August to trade near $4,400" |
| Currencies (V) | 29 | "trades near $4,400" |

Same month, same fact, three days apart at most. One of them is wrong; the Metals paper owns gold, so it should win unless the Foundations number was the later print.

### B2 · MEDIUM — HY OAS "current level" differs by 67bp across three papers

| Paper | Line | Level |
|---|---|---|
| Rates & Liquidity (IV), anchored 30 Aug | 42 | ~251bp, "fifth percentile of the five-year range" |
| Credit (VI), forecast table | 655 | 269bp, "richest decile" |
| Daily Cascade (XII) | 844 | 318bp "vs the 380bp watch threshold: comfortable" — no date attached |

Possibly different series (ICE BofA vs Bloomberg) or different dates; none of the three says which. State the series and as-of date wherever a level is quoted, then align.

### B3 · LOW — Two version schemes for the Daily Cascade

The Daily Cascade paper's masthead says "Companion to the Daily Cascade **v2**" (the cadence architecture), while Tail Scenarios L173 routes to "Daily Cascade (**v12**)" and the paper itself uses "v12" for the report build (L1031, L1046). Both are true, but a reader meets two version numbers for one report with no sentence explaining that they count different things.

### B4 · LOW — Stale forward references to papers that now exist

- Foundations L723: "One paper remains owed under this series: White Paper II" — II shipped the same day.
- Doctrine L401 and L834: "Positioning & Flows … when written" — XVI exists (6 Sep).
- Doctrine L904: "*Portfolio Construction Across Regimes* when written" — XVII Draft 1 exists (31 Aug).
- Technicals L7 and L250: "the shortest paper in the library" — no longer true (XXIII 4,026 words, XXIV 4,240, XVII 4,481, vs XIV 6,244).

### B5 · LOW — "Doubles the sample"

Base Rates L44 (and the guide's XX entry): extending the record to 1907 "doubles the sample." Eight post-1970 bears plus the five named pre-1970 episodes is thirteen — a 60% extension, not a doubling. Say "extends the sample to thirteen."

### B6 · LOW — Rule namespace collision

The Doctrine's Rules 1–29 are the governing set. The Daily Cascade (Rule 2.7.1, 4.7.3, 9.1, 10.1…) and the Dealer's Hand (Rule 18.1, 20.1, 21.1) use "Rule N.N" for section-local rules, so "Rule 21" means game-film review in the Doctrine and the cluster-divergence rules of Chapter 21 in the Daily Cascade. Cross-paper citations currently rely on context. A prefix convention ("Doctrine Rule 16", "DC 2.7.1", "DH 18.1") removes the ambiguity, and matters more once the claims registry keys on rule IDs.

### Checked and consistent

- **GEX sign convention** — positive GEX = dealers long gamma = suppression; negative = short gamma = amplification — identical in XII, XIII, III, XI, XVI, XVIII, XIX, XXII.
- **Four books (A–D), $300,000 base**, and the sizing tiers: Book B 0.75%/$2,250 standard, 1.5% exceptional; Book C 0.35%/$1,050; Book D 0.25%/$750, no exceptional tier; heat 6%/$18,000 across B–D; Book B 4%/$12,000 open risk; net beta ≤ Book A ceiling + 15 points — agree between the Doctrine and the Systematic Book, and are cited correctly by XVI, XXII, XXIII.
- **Every Doctrine "Rule N" citation** in other papers (Rules 5, 6, 10, 11, 12, 13, 15, 16, 24, 25) matches the rule's actual content.
- **Three regime dials** (Macro / Vol / Gamma) with Transition and Flip-zone states; flip-zone width is deferred to a declared band in both XVIII and XIX rather than hard-coded — consistent.
- **Confluence rule** = three of four daily clusters (XII, XVI). **13-episode** T&B calibration (I, XIX draft). **Warsh** as Fed chair throughout; no residual Powell-as-current references.
- **Shared levels** agree within date drift: fed funds 3.50–3.75%, core inflation 3.4%, 10y 4.67–4.72%, 30y 5.19–5.21% close / 5.33% intraweek high, Brent $88–89, BTC ~$78–79k, CCC–BB 855bp, PPI 6.5%, CAPE ~40–41.

---

## C. Remediation plan

**Mechanical — one Claude Code session, no judgment calls**

1. Numeral sweep (A1): 20 lines across five files, then a repo check that fails on `<paper name> ([IVX]+)` outside the masthead.
2. Delete `docs/options-expression-whitepaper.md`; point CLAUDE.md L35 at the `whitepapers/` path (A3). Delete `docs/whitepaper`; delete or move the systematic-book draft1 to an `archive/` folder; fill or remove `docs/whitepapers/readme.md` (A9).
3. Mastheads (A8): add XX, XXII, XXIII, XXIV; set Dealer's Hand to v1.1; sync the other four version labels to the guide (or the guide to them — pick a direction and state it in CLAUDE.md).
4. Add the missing Part II heading in the Daily Cascade paper and `# PART 1 — THE FAMILIES` in Tail Scenarios (A7). Renumber Evidence & Inference's figures 1–5 (A10).
5. Guide (A5, A6, A11): header count and word total; six missing one-page entries; XXIV's layer; one label for XVI; measured sizes for II, VI, XIII; rewrite the "reading order" sentence; refresh "In draft and planned"; "four-vote" → "three-of-four cluster."
6. Formats (A4): one HTML-canonical list in CLAUDE.md, mirrored in the guide, with a decision on V and XIV; commit `fx_charts.py`; consider tracking the HTML editions.
7. Stale forward references (B4) and "doubles" (B5): six one-line edits.

**Needs you**

8. Commit *Tops and Bottoms* (A2) — you hold the only source.
9. Resolve gold (B1) and HY OAS (B2) at the source, then align the papers; add series + as-of date to every quoted level going forward.
10. Choose the Daily Cascade version label (B3) and the rule-prefix convention (B6).
11. Optional: filename standardization (A9) — cheapest now.

**Not covered by this audit:** content accuracy, argument quality, currency of the September appendix, and anything inside the untracked HTML editions.
