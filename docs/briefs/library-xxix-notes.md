# Library XXIX — Real Assets and Risk Transfer, Draft 1 — notes

*Session B (B77), 26 Oct 2026.*
- **Branch:** `library-xxix`, from `origin/main` at `41803980`.
- **Source of the spec:** the XXIX section of `docs/briefs/phase-4-briefs-xxx-xxix.md` (on `origin/b66-phase-4-briefs`), with its six emphasis decisions ruled 25 Oct 2026 as recommended.
- **Scope:** docs only. The paste is `docs/pastes/B77.md`.
- **The paper:** `docs/whitepapers/real-assets-and-risk-transfer-whitepaper.md`.

## Word count

13,718 by the library's own count (whitespace split, `check_library` check 11),
against the paste's "about 12,000". Needs-you 1.

| Part | Words |
|---|---|
| Masthead, reader's note, prerequisites | 676 |
| Part I — Real Estate (chapters 1–4) | 5,983 |
| Part II — Infrastructure and Agriculture (5–6) | 1,478 |
| Part III — Risk Transfer (7–8) | 2,381 |
| Part IV — Tactical Applications, Wiring, Environments (9–11) | 1,812 |
| Appendix A — Assumptions and falsifiers | 876 |
| Appendix B — Dated | 512 |

## How the rulings landed

| Ruling | Target | Written | Where |
|---|---|---|---|
| (1a) Housing | ~4,500 | 3,765 | Chapters 1–2 |
| (1a) CRE | ~2,500 | 2,212 | Chapter 3 (1,606) and Chapter 4, REITs (606) |
| (1a) Infrastructure | ~1,000 | 857 | Chapter 5 |
| (2a) ILS and the reinsurance cycle | ~2,000 | 1,940 | Chapter 7 (1,104) and Chapter 8 less 8.3 (836) |
| (3a) Insurers as allocators | a section | 435 | Section 8.3 |
| (4a) Agriculture | ~500 | 614 | Chapter 6, "Agriculture, in brief" |
| (5a) Private funds and appraisal smoothing | a section | in 1,606 | Section 3.4 |
| (6a) Reference shelf | — | — | The masthead's series placement; the guide row |

- **ILS and reinsurance against the 2,000 ruling: 1,940 words.** Chapter 7 teaches what the investor is paid for, where the low-correlation claim fails (2005, 2011, 2017–18; prices falling in 2008 and March 2020), capacity, and triggers and model risk. Chapter 8, less 8.3, teaches the capital loop, a loss year's repricing, the January 2023 renewal, and what the store does not hold. Chapter 7.3 says the market is small and that no book here holds it. The Twenty-Five's M7 is cited as a slow scenario with no stored series. It is not called the framework's home turf, and the operator's profession is not mentioned.
- **Agriculture** is its own short chapter (6), following the brief's numbering, not a section inside Chapter 5. It has no sub-sections.
- **Chapter numbering.** Section 8.3 holds insurers as allocators, so the brief's chapters 10–12 become 9–11.

## Readings

- **XXVII could not be read from this session.** Reads of `origin/library-xxvii` were refused by the session's permissions, as for B74. The 2007 top is not narrated anywhere. Chapter 1.4 gives the channel and cites *Debt Cycles* and *Tops and Bottoms* for the episode, by short name and without chapter titles. Needs-you 3.
- **XXX was read** (`origin/library-xxx`). The LDI spiral is not told. Section 8.3 names the gilt episode once, as the source of liability-matching demand, and cites *Market Structure and Cascades* for the spiral and *Debt Cycles* for the fiscal side. Section 3.4's redemption mechanism is told for appraised vehicles only; XXX's 7.5 covers fund redemptions in general.
- **Where the housing measures print** was checked against the code (`daily_cascade/rates_transmission_block.py`):
  - the close prints the applications line on the release Wednesday;
  - the Weekly and the Monthly print one "Rates transmission" sub-section, with the housing block and items 68 and 69;
  - item 66 prints in the Monthly's Plumbing & rates (`daily_cascade/transmission_block.py`).
- **Brookfield (Standing rule 1).** No Brookfield-group name appears anywhere. Every listed example is an index, an ETF or a named episode:
  - indices: FTSE Nareit, NCREIF ODCE, Case-Shiller, Shiller's real index, the USDA's WASDE;
  - ETFs: the REIT ETF and the real-estate sector fund, by their store keys;
  - episodes: 2022, March 2023, the non-traded REIT gates of 2022–23, 2012, 2022 Ukraine, the loss years, the January 2023 renewal.

  No fund manager or insurer is named.
- **People named** are only authors of cited published work: Leamer (2007); Geltner (1993); Case and Shiller (1989); Working (1949); Froot (2001); Koijen and Yogo (2015). Shiller's name also appears in his index's name.

## The figure placeholders

The numbers and keys are the brief's. Each figure is a bold caption line, an
italic "Placeholder, drawn in a later edition" and its keys, with no image link.
They appear in order, 1 to 6.

| # | Figure | Keys | Placed in |
|---|---|---|---|
| 1 | Pending sales per household through two cycles | `redfin.pending_sales`, `fred.households` | 2.1 |
| 2 | The mortgage spread against the 10-year | `calc.mortgage_spread_10y_bp` | 2.2 |
| 3 | The real house price over a century | `shiller.real_home_price` (with `fred.case_shiller_national`) | 2.3 |
| 4 | CRE delinquency against the regional-bank episodes | `fred.cre_delinq` | 3.5 |
| 5 | REITs against the market | `calc.vnq_spy`, `calc.xlre_spy` | 4.3 |
| 6 | The reinsurance cycle as a loop (conceptual) | — | 8.1 |

## What the gate forced

`check_library` check 1 fails a paper that has no guide row. Two changes were made, as B62 and B74 made them:
- **The guide's placeholder row**, placed after Credit in the structural asset classes. XXX's row sits after Positioning & Flows, so the two cannot collide at merge. XXVII's row was not readable from here.
- **`"XXIX": "real-assets-and-risk-transfer"`** in `tools/check_library.py`'s REGISTRY, placed after the XXXIV entry. XXX's entry sits after XXV.

`check_master_guide` (a Makefile gate, so a CI gate) fails a roster paper with no group in the library map or no row in Table 9. That is "papers in the roster with no group". XXVII met the same failure in its CI round 1 and fixed it the same way, so this branch does it before the push:
- `tools/figures/master_guide.py` places XXIX in the "Asset classes" group, serving Books A and B. The edit is on the asset-classes list's last line and at the end of `BOOKS`, not on XXVII's big-frame line;
- Table 9 in `docs/master-guide.md` gains one row, after Credit, marked Draft 1, in review;
- Figure 5 (`docs/figures/master-guide/fig-05-library.svg`) is regenerated, and the Guide's HTML is rebuilt with its builder.

This is the minimum the gate requires. The Guide's fuller refresh (its As-of line, Landing next) stays for the merge. Figure 5 and `docs/html/master-guide.html` are generated, so they will conflict with XXVII's regenerated copies at merge. Whichever merges second regenerates them (needs-you 5).

**XXX's branch is red on this gate.** `library-xxx` CI runs 40414090959 and 40415162446 both failed. XXX added a guide row and nothing to the Master Guide, so the cause is presumably the same "no group" failure. The log could not be fetched (a stream error), so this is not confirmed. Nothing is changed on that branch from here.

Other results:
- **The one warning is check 11.** The guide's header claims 426,000 words against 457,098 measured on this branch. The header is not this paste's to edit.
- **No HTML edition of the paper** is built. `make html` writes it at merge.
- `check_master_guide`: 0 failures, 0 warnings after the changes above (run with the venv's interpreter; the system Python has no `yaml`).

## The guide row, drafted (only the placeholder is written into the guide)

**At-a-glance row:**

| | **XXIX** | Real Assets and Risk Transfer | Real Assets | The Quarterly's real-estate and agriculture chapters; the Weekly's and the Monthly's Rates transmission sub-section (items 36, 37, 68, 69) and item 66 in Plumbing & rates; the tail watch's catastrophe-capital and insurance-retreat entries | v1.0 Draft 1 · ~13,700 words, 6 figure placeholders | **A real asset is a claim on a physical service whose price is set mostly by its financing.** The paper covers housing as an asset and as the rate cycle's lead channel: the payment, the lock-in effect, turnover before prices, the builders and the mortgage machine. It reads the housing block in order, as measured (items 36, 37, 68, 69; the wealth-effect ledger FAIL at n 65). Commercial property follows: four property types, the maturity wall, the banks, and appraisal smoothing as the cause of private-fund redemption runs. Then REITs as the front-runner, infrastructure as long-duration credit, and agriculture's stocks-to-use convexity, in brief. Part III is catastrophe bonds and the reinsurance cycle at the market's weight, with insurers as allocators of the capital behind them. |

**One-page entry, drafted for the guide's per-paper section.** *XXIX. Real Assets
and Risk Transfer.* The library's home for real estate, infrastructure,
agriculture and insurance-linked risk transfer, on the reference shelf outside the
core track. Consult it beside *Credit*, which carries CRE credit, private credit
and the banks. It cites:
- *Debt Cycles* for the environments and the 2007 top;
- *Market Structure and Cascades* for the LDI spiral;
- *Energy* for the power build;
- *Metals* for gold, the other real asset;
- *Currencies* for real assets as a debasement hedge;
- *the Twenty-Five* for the catastrophe-capital tail and M7.

It is the owning paper the Quarterly's real-estate and agriculture chapters were
reserved for.

## Checks run

- `check_library`: 0 failures, 1 warning (check 11, above). `check_master_guide`: 0 failures, 0 warnings.
- The cross-reference audit, by script: every "Chapter N" and "N.M" resolves to the heading it names. There are 11 chapters, consecutive, and figures 1–6.
- A scan of the body for levels and probabilities outside the worked examples found none. Every dated figure is in Appendix B. That includes the register's own tripwire thresholds, which are quoted in Appendix A(d).

## Needs you

1. **Length.** The paper is 13,718 words against about 12,000. The ruled weights sum to about 10,500 (housing 4,500, CRE 2,500, infrastructure 1,000, ILS and reinsurance 2,000, agriculture 500), before about 3,900 words of required closing chapters, appendices and masthead, so both targets cannot be met. Housing came in under its ruling (3,765 against 4,500) and the total came in over its target. Your options:
   - accept it as written;
   - add about 700 words to housing (towards 14,400);
   - trim elsewhere toward 12,000.
2. **Appendix B's market figures were written from the published sources as I know them, not fetched this session.** That covers the 2022 mortgage-rate path, the 2022 REIT and ODCE returns, 2017's insured losses, and the catastrophe-bond and reinsurance-capital sizes. Each names its source. Check them against those sources before the paper leaves Draft 1, or rule that the annual review does it.
3. **XXVII was not readable from this session.** A pass against its text would confirm two things before merge: that Chapter 1.4's "channel only" treatment of the mid-2000s does not repeat it, and that the citations to *Debt Cycles* would be better by chapter title. The brief asks for chapter titles; none is given here.
4. **Agriculture** is written as its own short chapter, Chapter 6, following the brief's numbering, rather than as a section inside another chapter. Accept it, or fold it into Part II as section 5.5?
5. **Three library branches now touch the Master Guide's generated files** (Figure 5 and its HTML), and XXX's branch is red for want of the same change, as far as can be told without its log. Whoever merges the second and third branches regenerates both files. Do you want XXX fixed now, in its own paste, or at its merge? Separately, the Quarterly's chapters still say "no owning paper": `config/quarterly_chapters.yaml` sets `paper: null` for `real_estate` and `agriculture`. Pointing them at this paper is a config change for the merge paste, not this one.
