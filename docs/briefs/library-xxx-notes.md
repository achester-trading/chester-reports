# Library XXX — Market Structure and Cascades, Draft 1 — notes

*Session B (B74), 26 Oct 2026.*
- **Branch:** `library-xxx`, from `origin/main` at `41803980`.
- **Source of the spec:** the XXX section of `docs/briefs/phase-4-briefs-xxx-xxix.md` (on `origin/b66-phase-4-briefs`), with its six emphasis decisions ruled 25 Oct 2026 as recommended.
- **Scope:** docs only. The paste is `docs/pastes/B74.md`.
- **The paper:** `docs/whitepapers/market-structure-and-cascades-whitepaper.md`.

## Word count

16,895 by the library's own count (whitespace split, `check_library` check 11),
against the paste's 14,000–16,000 and the brief's ~15,000. It runs about 900 over;
needs-you 1.

| Part | Words |
|---|---|
| Masthead, reader's note, prerequisites | 573 |
| Part I — How a Trade Becomes a Price (chapters 1–5) | 4,170 |
| Part II — Cascades as One Subject (6–10) | 2,984 |
| Part III — The Cases (11–18) | 4,201 |
| Part IV — The Fragility Read, as Measured (19–20) | 1,656 |
| Part V — Tactical Applications, Wiring, Environments (21–23) | 1,863 |
| Appendix A — Assumptions and falsifiers | 810 |
| Appendix B — The dated appendix | 638 |

## How the rulings landed

- **(1c) The cases.**
  - In full: February 2018 (Chapter 14) and March 2020 (Chapter 15).
  - Medium length: 2021 (16) and 2022 (17).
  - Mechanism chapters cited to their histories: 1987 (11), 1998 (12) and 2010 (13).
  - Short instances: August 2024 and April 2025, together as a new Chapter 18 at the end of Part III, because the air-pocket ledger scores them. The brief listed seven case chapters; adding the eighth moves Parts IV and V on by one, to chapters 19–20 and 21–23.
- **(2a)** Only the Systematic Book's 3.5 moved (below).
- **(3a)** The fragility read is Part IV, two chapters.
- **(4a)** Clearing, collateral and margin is Chapter 4.
- **(5a)** Non-US structure is section 1.4.
- **(6a)** Zero-day options get one paragraph in 7.4, cited to *The Dealer's Hand* and *Volatility*.

## What moved from the Systematic Book

- **The section:** 3.5, "Microstructure the book actually uses", 347 words.
- **Where it went:** XXX's section 5.4, "The microstructure the book's execution actually uses", headed with a line saying it moved there on 26 Oct 2026.
- **Light edits for its new home:**
  - the opening sentence, which named the papers carrying the theory, is replaced by the move note;
  - "this paper" becomes "the Systematic Book" where it meant the old home;
  - the chain vendor's tier name and the date of the real-time subscription are left out;
  - the spread arithmetic is labelled illustrative.
- **The reference line left in the Systematic Book, under the kept 3.5 heading** (the heading stays so 3.1–3.6 stay consecutive):
  > Moved to *Market Structure and Cascades* on 26 October 2026 (its section 5.4, "The microstructure the book's execution actually uses"): the closing auction, the options spread as a cost and the delayed chain, as this book's execution layer consumes them.
- **The Systematic Book's HTML edition** is rebuilt: check 10 failed until it was.

## The fragility chain's verdicts, as printed

The two ledgers are on their own branches (`a57-batch14-b1`, `b56-batch15-2`),
not on main. The paper therefore cites them by ID and links no path.

- **ST-R6.71d (item 71, the air pockets): FAIL.** The flag was on before 0 of 3 air pockets, against the rule's 2. The fall-after share was 31.1% flag on against 6.4% flag off, with the ledger's own note that both arms rise with volatility. n is 2,965 sessions. In each event the flow arm fired and the depth arm did not. Chapter 19.2 prints it, Appendix B.1 its figures.
- **ST-R6.74b (item 74, extreme ES net shorts): INSUFFICIENT, n 0.** No ES rows were stored at the edition. Chapter 19.4 prints it.
- Both cite ruling D9 of 24 Oct. Neither is upgraded into a finding.

## The figure placeholders

The numbers and keys are the brief's. Each figure is a bold caption line with an
italic "Placeholder, drawn in a later edition" and its keys, with no image link,
so `check_library` check 4 sees figures 1–7 and check 8 has nothing to resolve.

| # | Figure | Keys | Placed in |
|---|---|---|---|
| 1 | Forced flow against depth | `levetf.aum`, `yfinance.mkt_spy` (computed by the fragility module) | 19.1 |
| 2 | Margin debt through the cases | `finra.margin_debit` | 19.1 |
| 3 | Leveraged funds' net in ES against the squeeze cases | `cftc.tff_lev_money_net_oi` | Chapter 10 |
| 4 | Dealer gamma and the session's range | `exposure.net_gex`, `yfinance.mkt_spy` | 7.4 |
| 5 | The VIX through the seven cases | `fred.vix` | Part III's opening |
| 6 | The stock–bond correlation's sign | `calc.corr_spy_tlt_60d` | 9.1 |
| 7 | The cascade as a loop (conceptual) | — | 6.1 |

Kept to the brief's numbering, the figures appear in the order 7, 4, 6, 3, 5, 1, 2.
The drawing paste may renumber them by appearance (needs-you 3).

## What the gate forced

- **`check_library` check 1** fails a paper with no guide row and no REGISTRY entry. Two changes, as for XXVII (B62):
  - **the guide's placeholder row**, placed after Positioning & Flows rather than after XXV, so it cannot conflict with XXVII's row at merge;
  - **`"XXX": "market-structure-and-cascades"`** in `tools/check_library.py`'s REGISTRY.
- **Check 5:** the ledger's "Rule 1" and "Rule 2" were reworded as "the first condition" and "the second condition".
- **Check 10:** the Systematic Book's HTML edition was rebuilt.
- **The one warning, check 11:** the guide's header claims 426,000 words against 460,238 measured. It was inside the 5% band on main and this paper pushes it out. The header is not this paste's to edit; its total is refreshed when the guide's full entries are written.
- `check_master_guide` passes unchanged, so the Master Guide was not forced.
- The readability gate does not cover whitepapers.
- **No HTML edition** of XXX is built. `docs/html/` is build output, and `make html` writes it at merge.

## The guide row, drafted (not written into the guide)

**At-a-glance row:**

| | **XXX** | Market Structure and Cascades | Market Structure | Positioning & Flows; the close's and the Weekly's Mechanics; the fragility panel (item 71) and the squeeze line (item 74) | v1.0 Draft 1 · ~16,900 words, 7 figure placeholders | How a trade becomes a price and how forced flow turns a move into a cascade: **liquidity is a flow intermediaries supply when it pays, and a cascade is forced flow exceeding it**. Covers venues and the closing auction (non-US structure in brief), who supplies liquidity and why each stops, ETFs as the price when the basket does not trade, clearing, margin and haircuts as one procyclical mechanism, and depth and impact (Kyle, Amihud). Part II covers endogenous risk, the five forced flows and their timing, liquidity spirals, correlation breakdown and squeezes. The cases run 1987 to 2022, with February 2018 and March 2020 in full. Part IV is the system's fragility read with its ledgers' verdicts as filed (item 71 FAIL; item 74 INSUFFICIENT at n 0) and what the measures cannot see. |

**One-page entry, drafted for the guide's per-paper section.** *XXX. Market
Structure and Cascades.* The library's home for microstructure and the cascade
mechanism. It absorbs the Systematic Book's 3.5 and cites *The Dealer's Hand*
for options mechanics, *Volatility* for vol targeting and February 2018,
*Rates & Liquidity* for the Treasury market, *Debt Cycles* for the gilts' fiscal
side and the environments, and *Tops and Bottoms* for the episodes. Read it after
the options sequence, with *Positioning & Flows* and *Technical Indicators*. It
assumes *Price, Time, and Edge*'s participants and forcing mechanisms.

## Checks run

- `check_library`: 28 papers, 0 failures, 1 warning (check 11, above).
- `check_master_guide`: 12 passed.
- The house standard's cross-reference audit, by script: every "Chapter N" and "N.M" resolves to the heading it names; 23 chapters, consecutive; figures 1–7 present.
- No Brookfield-group instrument appears anywhere.
- The only people named are authors of cited published work: Kyle; Amihud; Danielsson and Shin; Grossman; Lowenstein; Kirilenko, Kyle, Samadi and Tuzun; Haddad, Moreira and Muir; Duffie; Brunnermeier and Pedersen; Longin and Solnik; Cheng and Madhavan.

## Needs you

1. **Length.** 16,895 words against about 14,000–16,000. The overrun is spread across Parts I and III. Accept, or name the cut: the 1987–2010 mechanism chapters could each lose a paragraph, saving about 600 words.
2. **XXVII was not readable from this session.** Reads of `origin/library-xxvii` were refused by the session's permissions, so its coverage came from the brief's description. 1987 is taken as mechanism only, the gilts as collateral mechanics only, and the VRP and the environments are cited to *Debt Cycles* by short name, with no chapter titles. A pass against XXVII's text before merge would confirm nothing is repeated.
3. **Figure order.** Keep the brief's numbers (appearing 7, 4, 6, 3, 5, 1, 2), or renumber by appearance in the drawing paste?
4. **The new Chapter 18** (the two short instances as their own chapter). Accept, or fold it into Chapter 19?
5. **The Systematic Book's light edits** in the moved 3.5 (above). Accept, or restore the original wording verbatim?

## Ruled (26 Oct 2026)

- **XXVII, checked from the chat against its text on `library-xxvii`: no repetition.** XXVII treats 1987, 1998, the gilts and 2022 only as instances in its regime definitions; XXX carries the mechanisms. Needs-you 2 is closed.
- **Chapter 18, the two short instances (August 2024 and April 2025): accepted** as its own chapter at the end of Part III; Parts IV and V stay at chapters 19–23.
- Also ruled, with no change to the paper: the length (16,895 words) is accepted with no cuts before review; the figures are renumbered by order of appearance in the figure paste, not now; and the moved 3.5's light edit is accepted, keeping "illustrative" on its arithmetic.
