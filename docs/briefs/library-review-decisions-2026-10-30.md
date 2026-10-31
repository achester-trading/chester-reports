# Library review: the decisions memo (the seven library PRs)

Paste B93 (`docs/pastes/B93.md`), 31 Oct 2026. On `b88-library-rehearsal` at
`927d03d9`, where all seven library branches are merged (B88). It is drawn from
each paper's draft and notes on that branch, and the passages each decision turns
on are quoted. **Nothing here is ruled, and no paper's body was edited.** D30:
each paper merges by its own PR after review.

**Already ruled, so not asked again.** D30 (24 Oct, `docs/briefs/rulings-2026-10-24-evening.md`)
ruled four of XXVII's items:
- "(1) review is Ari's; merges by its own PR after review";
- "(2) the debt-cycle branch rule goes to a later sitting (Doctrine #3, early Dec), not #2";
- "(4) keep ~24,600 words, cuts marked on review";
- "(5) Amendment #3 workstream B: original file to be filed if Ari has it, else a record (A70)".

Decisions 1 and 2 below therefore only confirm that the PR follows those rulings.
Decision 3 is what remains of (5).

## Summary

| # | Paper | Question (ten words) | Recommendation |
|---|---|---|---|
| 1 | XXVII | Length 24,647 against ~20,000: keep, move to companion, split? | Keep, as D30(4) ruled; cuts marked on review only |
| 2 | XXVII | Does 17.4's proposed rule need rewording before the PR? | No; it stays "a proposal", ruled at Doctrine #3 (D30(2)) |
| 3 | XXVII | Cite the missing 13 Sep order as pending, or wait? | Cite A70's record by name; merge XXVII after chain-8 lands |
| 4 | Phase 3a | Foundations' numbering gaps: renumber, note, or cross-reference? | Leave, with one reader's-note sentence pointing to Appendix B |
| 5 | Phase 3a | Companion appendix home: `companions/` folder or a gate exclusion? | Keep `docs/whitepapers/companions/`; no gate change |
| 6 | Phase 3a | Two dated passages left in the bodies: move or keep? | Keep for now; a Phase 3b at the papers' next edition |
| 7 | XXXI | The ten triggers' roll-up tiers: which rule assigns them? | Count fired mechanism families; CLEAR 0–1, WATCH 2, ALERT 3+ |
| 8 | XXXI | The gap-patch's unrecorded inputs: reconstruct, or state the gap? | State the gap; the manual stays as written |
| 9 | XXXII | The review calendar: spread across the year, or all-January? | Spread; corpus pass 16 Jan 2027; XXIX March, XXX July |
| 10 | E&I | The five drawn figures: accept as drawn? | Accept; each foot line cites its formula and chapter |
| 11 | XXX | Draw the four store figures from a box export first? | Yes: the export on Tue 3 Nov, drawn before XXX's PR |
| 12 | XXIX | Clear the eight "(to verify)" marks before the PR? | Yes, by B94 against the named public sources |
| — | all | The mechanical checklist (section 9) | Do at each PR; not a decision |

---

## 1–3. XXVII, Debt Cycles, Regimes, and Environments

**State.** 24,647 words, Parts I–VI, Chapters 1–23, Appendices A
(assumptions and falsifiers) and B (dated). Figures: 0 drawn and 6 placeholders,
listed in Appendix A(e) and `docs/figures/debt-cycles-regimes-environments/README.md`.
No "(to verify)" marks. Version 1.0 Draft 1, 24 October 2026.

### Decision 1: the length

> The brief (`docs/briefs/phase-2-briefs-xxv-xxvii.md`, line 78): "**Target:** ~20,000 words (raised from 18,000 for the full Part on long-cycle tops)".
>
> The notes, departure 2: "About 24,600 words against the brief's ~20,000. Part I runs long (5,460) because the internal-order lens and the four repression regimes each carry the full worked-example, instance and on-the-day triple. Trimming Part I to about 4,000 would bring the paper to about 23,000; the review decides."

| Option | Cost |
|---|---|
| (a) Keep 24,647; mark cuts on review (D30(4)) | None now. The longest paper in the core track stays at about 1.2× its target |
| (b) Move Part III (the five tops, 4,202 words) to a companion appendix, as Phase 3a did for the Twenty-Five | The body falls to ~20,400. But Part III is the paper's argument, not dated material, and a companion is meant for the dated or the catalogued |
| (c) Split into two papers (the cycles; the environments) | A new numeral, a new guide row and new review rows. Every "Debt Cycles" citation already written into Foundations 4.1 and XXX would have to be resolved |

**Recommend (a)**, as ruled. A companion appendix is for material that dates or
catalogues, and Part III does neither.

### Decision 2: rule 17.4's wording

> Chapter 17.4: "**What follows is a proposal for the operator's ruling, not a rule, and it grants nothing.** The field is report-only for every reader and stays so whatever is ruled; the sizing consequence of the branch — that Book A's duration sleeve is a deflation hedge and the wrong instrument for the inflationary branch — is the Doctrine's to write."
>
> And its rule's fourth clause: "**Inflationary.** The breakeven rising or the real yield below zero, *and* gold rising while the real yield is flat or rising: the divergence is required, because negative real yields alone are also the ordinary state of an easing cycle."

| Option | Cost |
|---|---|
| (a) No change; the section stays a proposal and Doctrine #3 rules it (D30(2)) | None |
| (b) Before the PR, reword "proposal" to name the sitting: "for the operator's ruling at Doctrine #3" | One sentence in the body, which then dates the paper |
| (c) Remove the rule from the paper and hold it in a brief until ruled | The paper loses the section 6f's spec left to it |

**Recommend (a).** The text already says what it is. The sitting's date belongs
in the ruling, not in the paper.

### Decision 3: the missing 13 Sep order

> The notes, departure 5: "Amendment #3 workstream B's order is not in the repository. No file `docs/change-order-*amendment-3*` exists, and no "13 Sep" order is filed."
>
> A70's record (`docs/change-order-amendment-3-2026-09-13-record.md`, on `a70-amendment-3-record`, carried into chain-8 by B86b's merge of a71): "Approved in chat on 13 September 2026, with two workstreams: **A**, the sub-factor I-b inputs including consensus drift; **B**, Internal Order as Factor VI, a Monthly Internal Order panel, and the internal-order cycle as a coequal lens in Paper XXVII. … **Its original file was never committed**".

What it was meant to contain, for XXVII: "the internal-order cycle as a coequal
lens in Paper XXVII". The paper's §2.3 is built from what the repository says of
it: batch 5 item 18's Strauss & Howe line, GTM-11's panel, and batch 6 item 38.

| Option | Cost |
|---|---|
| (a) Cite it as pending: "Post-Freeze Amendment #3 (13 Sep 2026; its record, original not committed)" by name, and merge XXVII after chain-8, so the record exists on main when the citation does | One citation line at the PR; XXVII's PR waits for chain-8 (2 Nov) |
| (b) Wait for the original file | Unbounded: A70 searched every branch, and the original exists only if the operator has the chat |
| (c) Cite nothing; the lens stands on its published sources (Dalio, Strauss and Howe, Turchin) | The lens's mandate goes unstated, and the review cannot check it against the order |

**Recommend (a).** If the original turns up, it is filed beside the record and
the citation does not change.

## 4–6. Phase 3a, Foundations (I) and the Twenty-Five (II)

**State.**
- **Foundations:** 22,140 words, a timeless body of ~16,000 plus Appendices A and
  B; 5,720 words moved, in 16 sections. Version 1.1, 25 October 2026.
- **The Twenty-Five:** body 8,036 words (Parts 0–3) plus the companion appendix
  of 17,223 words; 17,053 moved, in 25 sections.
- No figures and no marks. Text moved, not rewritten.

### Decision 4: the numbering gaps

The paste names "the companion appendix's numbering gaps". The companion itself
has none: it holds the 25 scenarios in family order, each under its own number.
**The gaps are in Foundations' body**, where the moved sections kept their
numbers. Body against Appendix B, from the headings:

| Chapter | In the body | Moved to Appendix B |
|---|---|---|
| 1 | 1.1, 1.2, 1.6, 1.7 | 1.3, 1.4, 1.5 |
| 2 | 2.1, 2.2, 2.6, 2.7 | 2.3, 2.4, 2.5 |
| 3 | 3.1, 3.2, 3.5, 3.7, 3.8 | 3.3, 3.4, 3.6 |
| 4 | 4.1 (heading kept, with the pointer), 4.2, 4.6, 4.7 | 4.1 (the original 101), 4.3, 4.4, 4.5 |
| 5 | 5.1, 5.2, 5.6, 5.7 | 5.3, 5.4, 5.5 |
| 6–8 | complete | — |

> Notes: "**Section numbers are not renumbered.** Foundations' chapters now run 1.1, 1.2, 1.6, 1.7 (and similarly in each chapter). Renumbering would be a rewrite and would break the in-paper references (the moved 3.4 cites §3.5)."
>
> Foundations 4.1, as kept: "this paper's original 101 is kept, unchanged, in Appendix B."

"4.1" appears twice, once in the body and once in Appendix B. That is by design:
the body keeps the heading with its pointer.

| Option | Cost |
|---|---|
| (a) Renumber the body and Appendix B | A rewrite of ~35 headings and every in-paper reference (the moved 3.4 cites §3.5); breaks external citations of Foundations' section numbers |
| (b) Leave, with one sentence in the reader's note: moved sections keep their numbers and are in Appendix B | One sentence; nothing breaks |
| (c) Cross-reference: a stub heading at each gap ("1.3–1.5: in Appendix B") | Five stubs; the reader sees the move where it happened. Adds headings the gate counts |

**Recommend (b).** It is the cheapest honest fix. (c) is a fair alternative if
the operator prefers to see the move in place.

### Decision 5: the companion appendix's home

> Notes, needs-you 1: "Keep `docs/whitepapers/companions/`, or have a later code paste teach the library gate a companion file in `docs/whitepapers/` (an exclusion by name)?"

| Option | Cost |
|---|---|
| (a) Keep `docs/whitepapers/companions/` | None; the gate passes today |
| (b) Move it beside the papers and teach the gate an exclusion | A gate change for one file, and a rule every future companion must remember |

**Recommend (a).**

### Decision 6: the two dated passages still in the bodies

> Notes, needs-you 4: "Foundations' 8.2, "The named pathways, with current state", and the Twenty-Five's Part 2 build queue and re-specification log. Move them in a Phase 3b, or keep them as the operations the body owns?"

| Option | Cost |
|---|---|
| (a) Keep them in the bodies now; move them in a Phase 3b at each paper's next edition | The bodies keep two dated passages until then |
| (b) Move them before the PR | Reopens a reviewed restructure, and a second Phase 3a paste |

**Recommend (a).**

## 7–8. XXXI, The Top & Bottom Report Manual

**State.** 8,107 words, Parts I–IX, sections 1–27, Appendices A (where the
specification and the code differ), B (dated values) and C (assumptions and
falsifiers). No figures and no marks. Version 1.0, 24 October 2026.

### Decision 7: the ten triggers' roll-up tiers

> §8: "The triggers roll up into one status, **CLEAR**, **WATCH** or **ALERT**. With six triggers the tiers were zero or one fired, two, and three or more. Whether the tiers were scaled for ten, or held, is recorded in the specification as not confirmed against the engine. This manual therefore states no roll-up threshold for the ten-trigger set. A build in this repository must declare one in configuration, with its reason, and the Doctrine monthly must ratify it."

The ten, as §7 lists them:
1. A mega-cap technology IPO filing (the first of two named filings).
2. A second mega-cap AI IPO filing.
3. Consumer prices breaching a stated rate (B.6: 4%).
4. The high-yield spread crossing a stated level (B.6: OAS above 350 bp).
5. The share of index members above their 200-day average falling below half,
   while the index is near its highs.
6. The bank research desk's bull-and-bear indicator above its sell threshold
   (B.6: 8.0).
7. The 2-year to 10-year curve un-inverting after a period of inversion.
8. The curve re-inverting, on either the three-month or the two-year leg.
9. Credit-spread acceleration (the thirty-day rate of widening).
10. Private-credit bifurcation (private stressed while public spreads stay
    tight).

**The proposed rule: count mechanism families, not triggers.** The ten fall into
six families: issuance (1, 2), inflation (3), credit (4, 9, 10), breadth (5),
sentiment (6) and the curve (7, 8). Correlated triggers inside a family fire
together, so counting them twice double-counts one mechanism. A family counts as
fired when any member is TRIGGERED.

| Status | Rule | Why |
|---|---|---|
| CLEAR | 0 or 1 family fired | The six-trigger tiers, held: with six triggers each was its own family, so "families fired" is exactly what the old count measured |
| WATCH | 2 families fired | |
| ALERT | 3 or more families fired | |
| Not read | A trigger the system cannot read prints "not read" and its family counts as unread. The status prints with "k of 6 families read", and **ALERT is withheld while fewer than four families are read** | §7: "a trigger the system cannot read is printed as not read, never assumed clear" |

| Option | Cost |
|---|---|
| (a) The family count above | Six families to declare in config, each with its reason. The thresholds are the old ones, so nothing is re-calibrated |
| (b) Held trigger counts (0–1 / 2 / 3+ of ten) | More ALERTs: credit alone (4, 9 and 10 in one widening) reaches ALERT |
| (c) Scaled proportionally (0–1 / 2–3 / 4+ of ten) | Fewer ALERTs; the scaling is arithmetic, not mechanism, and still double-counts credit and the curve |

**Recommend (a)**, declared in config at the T&B build and ratified by a Doctrine
monthly (D38 item 53 puts the tiers there). The manual's §8 is unchanged until
then, and the PR states no tier.

### Decision 8: the gap-patch's inputs

> Notes, needs-you 3: "The gap-patch's full input list. The repo records only its house-price input, so the manual does not reconstruct the rest."

| Option | Cost |
|---|---|
| (a) State the gap; the manual stays as written | None. The build declares the inputs |
| (b) Reconstruct the inputs from the master narrative | Invents a specification the repository does not hold |

**Recommend (a).**

## 9. XXXII, The Annual Structural Review

**State.** 4,324 words, Parts I–VIII, sections 1–16, Appendices A (the register
at seeding) and B (assumptions and falsifiers). No figures and no marks. Version
1.0, 24 October 2026. It brings the register file and check 15, adopted by B78
under decision 52.

### Decision 9: the review calendar

> §10: "Audit 2 scheduled the whole review in January. This protocol keeps January for the corpus and spreads the papers across the year, for two reasons. A review of thirty papers in one month would be thirty shallow reviews, because the attention budget allows one sitting of two hours a week, and three or four papers fit a sitting. And a library reviewed all at once ages all at once; one reviewed across the year always has a part that is fresh."

The calendar as drafted gives no month to XXIX or XXX, which were written after
it.

**Proposed dates for the first cycle (2027):**

| When | What | Why that date |
|---|---|---|
| Doctrine #2, 7–8 Nov 2026 | The calendar ruled: spread, or all-January | Check 15's warnings start counting from the merge |
| Sat 16 Jan 2027 | **The corpus pass**: the dated-figure recomputation and the health check for every paper, the corpus questionnaire, the ranking | The Saturday after the Alternative Assets Quarterly's first edition (9 Jan 2027). The recomputation then reads the Quarterly's figures fresh, and the pass does not compete with the Quarterly's own review |
| February | Tops and Bottoms, Base Rates, Evidence and Inference (as drafted); plus any paper the corpus pass finds broken | The oldest paper (May 2026) inside thirteen months |
| March | The Monthly manual, Rates and Liquidity, Credit, **plus XXIX, Real Assets** | XXIX cites Credit and the rates transmission; a sitting holds four |
| April to June | As drafted | |
| July | Volatility, the Dealer's Hand, Options as Expression, **plus XXX, Market Structure and Cascades** | XXX cites all three; four in a sitting |
| August to December | As drafted. XXVII in September and XXXI in November, as the draft already places them | |

| Option | Cost |
|---|---|
| (a) Spread, as drafted, with the dates above | Two or three papers a month, every month |
| (b) All in January (Audit 2) | Thirty papers in four or five sittings: shallow, and the library ages at once |

**Recommend (a).** The register's `review_month` becomes 3 for XXIX and 7 for XXX.

## 10. Evidence and Inference, its five figures

**State.** 4,225 words, Parts I–IV, Chapters 1–16, and the card. Figures: 5
drawn (`tools/figures/evidence_inference.py`), none placeholder. No marks.
Version 1.0.1, 26 October 2026, "Chapter 14 sentence per Figure 4".

> Masthead: "Its five computed figures are drawn from the paper's own formulas (24 October 2026)." Figure index: "Conceptual figures: no figure in them is data."

Each figure, and its foot line's citation (read from the SVG):
1. **Figure 1:** a true 0.2R edge's 95% interval narrowing with √n. Cited:
   "Interval = 0.2 ± 2/√n, the per-decision spread taken as 1R (Chapter 1)".
2. **Figure 2:** a Sharpe of 1.0 and its error bar by years of data. Cited:
   "SE = √((1 + S²/2)/T) with S = 1 (Chapter 2)".
3. **Figure 3:** one process at a true 60% hit rate under three priors. Cited:
   "Posterior mean (a + wins)/(a + b + n) … (Chapter 9)".
4. **Figure 4:** the fraction of full Kelly against the edge's error bar. Cited:
   "s/m = 1/(0.2√n) … (Chapter 14)".
5. **Figure 5:** a 0.2R edge decaying from week 40, first excluded at week 65.
   Cited: "Illustrative: 200 decisions a year (SE 0.14R on 13 weeks) … (Chapter 15)".

Each data block is cited: every figure states its formula and chapter in its
foot, and none draws data.

### Decision 10

| Option | Cost |
|---|---|
| (a) Accept as drawn; the operator looks at the five once (Figure 2's preview was seen in B78) | One look |
| (b) Redraw any that read badly | A layout paste per figure |

**Recommend (a).** Figure 5 is also the line D43's edge-decay pause rests on, so
it is worth the look.

## 11. XXX, Market Structure and Cascades: the four store figures

**State.** 16,945 words, Parts I–V, Chapters 1–23, Appendices A and B. Figures: 3
drawn (1 the cascade loop, conceptual; 3 the stock–bond correlation; 5 the VIX
through the cases; 3 and 5 from the laptop's store) and 4 placeholders. No marks.
Version 1.0 Draft 1, 26 October 2026. It also moves the Systematic Book's §3.5,
the edit accepted 26 Oct.

The four, quoted:
- **Figure 2** (Chapter 7, line 264): "Dealer gamma and the session's range. *Placeholder, drawn at merge from the box's store: the stored net gamma exposure (`exposure.net_gex`) against SPY's daily range (`yfinance.mkt_spy`), from the captures' first stored session.*"
- **Figure 4** (Chapter 10, line 359): "Leveraged funds' net in ES against the squeeze cases. *Placeholder, drawn at merge from the box's store: CFTC Traders in Financial Futures, leveraged funds' net in the E-mini S&P 500 as a share of open interest (`cftc.tff_lev_money_net_oi`), with the squeeze cases marked.*"
- **Figure 6** (Chapter 19, line 596): "Forced flow against depth. *Placeholder … Keys: `levetf.aum` and `yfinance.mkt_spy`; the estimate and the measure are computed by the fragility module, not stored as keys.*"
- **Figure 7** (Chapter 19, line 598): "Margin debt through the cases. *Placeholder, drawn at merge from the box's store: FINRA margin debit balances (`finra.margin_debit`), with the cases marked.*"

**The export, for the operator on the box on Tuesday 3 Nov in the evening**
(after 17:20 ET, outside the EOD window). It is read-only (`mode=ro`): it writes
only CSVs under `~/library-xxx-export/`, outside the checkout, and touches no
unit. Each key's every instrument is exported with the newest vintage per day.
SPY's range needs its `_high`, `_low` and `_volume` members, which
`alpha/store.py`'s `daily_bars` reads the same way.

```
cd ~/chester-reports && mkdir -p ~/library-xxx-export && .venv/bin/python - <<'EOF'
import csv, os, sqlite3
db = os.environ.get("CHESTER_DB") or "data/chester.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
keys = ["exposure.net_gex", "yfinance.mkt_spy", "yfinance.mkt_spy_high",
        "yfinance.mkt_spy_low", "yfinance.mkt_spy_volume",
        "cftc.tff_lev_money_net_oi", "levetf.aum", "finra.margin_debit"]
out = os.path.expanduser("~/library-xxx-export")
for k in keys:
    rows = con.execute(
        "SELECT substr(observed_at,1,10), COALESCE(instrument,''), value_num, available_at "
        "FROM observations WHERE registry_key=? AND value_num IS NOT NULL "
        "ORDER BY instrument, observed_at, available_at", (k,)).fetchall()
    last = {}
    for day, inst, v, av in rows:
        last[(inst, day)] = (v, av)
    with open(f"{out}/{k}.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["instrument", "day", "value", "available_at"])
        for (inst, day), (v, av) in sorted(last.items()):
            w.writerow([inst, day, v, av])
    print(k, len(last), "rows", min((d for _, d in last), default="-"), "to",
          max((d for _, d in last), default="-"))
EOF
```

The printed counts and first dates say at once whether a figure can be drawn: for
example, how many sessions of `exposure.net_gex` the captures hold. The CSVs reach
the laptop by the operator's usual copy (the Drive inbox), and a session draws
from them with `tools/figures/market_structure.py`, captioned "box store, as of
3 Nov 2026".

### Decision 11

| Option | Cost |
|---|---|
| (a) Export on 3 Nov, draw the four before XXX's PR | One box command and one drawing paste (about 45 minutes) |
| (b) Merge with the four placeholders; draw in a later edition | The paper merges with 3 of 7 figures; the placeholders say so |
| (c) Drop any figure whose series is too short (`exposure.net_gex` began with the October captures) | That figure's chapter loses its exhibit |

**Recommend (a)**, falling back to (c) for any key the export shows under
60 sessions. Figure 2 is the likely one.

## 12. XXIX, Real Assets and Risk Transfer: the eight marks

**State.** 13,759 words (13,718 accepted, ruled 26 Oct), Parts I–IV, Chapters
1–11, Appendices A (assumptions and falsifiers) and B (dated figures). Figures: 0
drawn and 6 placeholders, "drawn in a later edition". **8 "(to verify)" marks**,
all in Appendix B. Version 1.0 Draft 1, 26 October 2026.

The marks, quoted, with the public source that would clear each. B94 clears
them; this memo only lists them.

| # | Where | The claim, quoted | Clearing source (public) |
|---|---|---|---|
| 1 | B.2, 2022 mortgage rates | "The 30-year fixed rate rose from about 3.1% in early January to about 7.1% in late October and early November 2022" | Freddie Mac PMMS weekly history (freddiemac.com/pmms; FRED `MORTGAGE30US`) |
| 2 | B.2, 2022 listed against private | "The FTSE Nareit All Equity REITs index returned about −25% in 2022; the NCREIF ODCE index returned about +7%" | Nareit's published index returns (reit.com); NCREIF's ODCE year-end release (ncreif.org) |
| 3 | B.2, 2017 loss year | "Insured natural-catastrophe losses of roughly $140 billion, a record at the time" | Swiss Re Institute, sigma (No. 1/2018), the public summary |
| 4 | B.2, 2005 loss year | "The Gulf hurricanes of 2005 were then the costliest insured catastrophe season on record" | Swiss Re Institute, sigma (No. 2/2006), the public summary |
| 5 | B.2, March 2023 | "Three US regional banks failed in March and early May 2023" | The FDIC's failed-bank list (fdic.gov) |
| 6 | B.3, cat bonds | "roughly $50 billion outstanding, against global reinsurance capital of roughly $700 billion, of which alternative (capital-market) capital is roughly $100 billion" | Artemis's catastrophe-bond market report; Aon's Reinsurance Market Dynamics / capital report |
| 7 | B.3, CRE debt | "US commercial real-estate debt is commonly reported at about $5 trillion outstanding, with banks the largest holders" | Federal Reserve Z.1 (the commercial-mortgage tables); MBA's quarterly CRE debt release |
| 8 | B.3, the housing stock | "the share of outstanding mortgages carrying a rate below the prevailing new-loan rate remained large through 2026" | FHFA's National Mortgage Database rate distribution; ICE Mortgage Monitor's public summary |

### Decision 12

| Option | Cost |
|---|---|
| (a) B94 clears all eight before XXIX's PR (ruled 26 Oct: "They are verified before merge") | One paste, already issued |
| (b) Merge with the marks | Contradicts the 26 Oct ruling |

**Recommend (a).**

## 13. The mechanical checklist, per PR

These are not decisions; each PR does them.

- [ ] **Merge and regenerate:**
  - merge the branch;
  - `python tools/figures/master_guide.py`;
  - `python tools/build_paper_html.py docs/master-guide.md`. `bash scripts/make.sh html` does not build the Guide, and check 10 fails without it;
  - `bash scripts/make.sh html` for the paper's own edition.
- [ ] **Run the gates:** `tools/check_library.py`, then `tools/check_master_guide.py`.
- [ ] **The structural-review register rows** (`docs/reading/structural-review-register.yaml`) that check 15 asks for, one per new paper, in its flow style:
  - XXVII: `{numeral: XXVII, slug: debt-cycles-regimes-environments, version: "1.0 Draft 1", version_date: 2026-10-24, last_reviewed: null, review_month: 9, status: never reviewed, log: null}`
  - XXXI: `{numeral: XXXI, slug: tb-report-manual, version: "1.0", version_date: 2026-10-24, last_reviewed: null, review_month: 11, status: never reviewed, log: null}`
  - XXX: `{numeral: XXX, slug: market-structure-and-cascades, version: "1.0 Draft 1", version_date: 2026-10-26, last_reviewed: null, review_month: 7, status: never reviewed, log: null}` (7 if decision 9 is (a))
  - XXIX: `{numeral: XXIX, slug: real-assets-and-risk-transfer, version: "1.0 Draft 1", version_date: 2026-10-26, last_reviewed: null, review_month: 3, status: never reviewed, log: null}` (3 if decision 9 is (a))
  - Version updates for papers whose version moved: I and II to "1.1", `2026-10-25` (Phase 3a); Evidence and Inference to "1.0.1", `2026-10-26`. The register's own header says "a new version moves `version` and `version_date`, not `last_reviewed`".
- [ ] **The library guide's header**, once, in the last PR (XXIX):
  - the paper count: 27 → 32 on the roster, by the gate's own count;
  - the as-of date;
  - "roughly 426,000 words" → the measured total by check 11's method (494,334 on the rehearsal branch, so "roughly 494,000").
- [ ] **The dated-appendix queue's XXVII entries** (B.3–B.5): struck when XXVII merges (XXVII notes, departure 8).
- [ ] **The guide's drafted entries:** XXVII's at-a-glance row and one-page entry, written into the guide at its merge (D30(3)).
