# library-draft-3: the Reader's Guide, Draft 3 (session A, 19 Oct 2026)

**What this branch is.** Draft 3 of Companion XXXIII, *The Reporting System: A Reader's Guide*. It is on `library-draft-3`, branched from chain-2's tip `ab27c07`, and merges right after chain-2.
- **Specification:** sections 3 to 6 of the update file of 18 October (`readers-guide-draft-3-update-2026-10-18.md`), with the 19 Oct paste's overrides.
- **"As built"** means chain-2's contents, not main's, dated today.
- Every claim was checked against chain-2's code and config. Where the code differs from the update file, the paper says what the code does, and the difference is listed below.
- Branch only: nothing merged, nothing deployed, nothing on the box.

## What changed

- **`docs/whitepapers/reporting-system-whitepaper.md`:** Draft 3, about 23,400 words (Draft 2 had about 17,650).
  - **The masthead:** Draft 3, 19 October 2026; "built" defined as chain-2; the reread line updated.
  - **Part I:** the five layers, and what the Alpha Lab and chester-meme are not.
  - **Part II:**
    - the feed families refreshed: FRED's lenses and ALFRED; the new official writers; the crypto data layer; the three captures; the 17 names, plus SPX and SPCX at 16:31; the vendor cross-check;
    - the 12:30 slot's reads;
    - new §2.5 the Security Master, §2.6 marks, ids and tiers, §2.7 backups and the restore test.
  - **Part III:** no sub-states (the rates driver withdrawn; the inflation driver a read beside the object); the Weekly's three exception tiers.
  - **Part IV:**
    - the close, the Weekly (the précis, the addendum as a second PDF), the Monthly (the lenses, the surprise index, the system metrics, M1–M13);
    - the anchor's opening setup and the 12:30 slot;
    - §4.8 rewritten: the Alternative Assets Quarterly is built and disabled;
    - chart displacement;
    - the withheld-drafts log and the event ledger.
  - **Part V:** the series binding, flag words, time words, signed zeros, resolved contracts, the filler rule's exemptions, no internal names; §5.3 rewritten as the one revision, with the rule, the span and the draft.
  - **Part VI:** the voices register live; Batches 5 to 9; the GTM batch; the mechanism scan in the repository; the PRL read; the X digest; the MSTR/MSCI watch; new §6.7 chester-meme.
  - **Part VII:** the expression-currency rule, Book D's drafts and the `attention_budget` abstention; new §7.8 the operator's writes (the deny list).
  - **Part VIII:** the state vector built; §8.4 what is built; new §8.5 the Alpha Lab, with the meta-loop.
  - **Part IX:** the dealer pre-registration, the change ladder as ruled, the system-metrics block, new §9.9 calibration ledgers with the verdicts and the acceptances of 19 Oct.
  - **Part X:** the précis first, the addendum last, the 12:30 mail.
  - **The appendices:**
    - Appendix A refreshed from config at this commit;
    - Appendix B dated;
    - Appendix C three falsifiers added (the dealer demotion rule, the lab's kill rule, the registered pass rule);
    - Appendix D gains Draft 2's unbuilt items;
    - new Appendix E, what Draft 3 says is not built.
  - **Kept word for word:** §4.3's title and its ledger sentence, which `config/alpha_tells.yaml` quotes (`validate_alpha_lab_3` B, 65/0); and the title and path the Weekly's footer prints.
- **`docs/figures/reporting-system/fig-01.svg`:** redrawn with the two side boxes.
  - The Alpha Lab reads the store, and its evidence reaches the register only as something the operator tables.
  - chester-meme reads the export, and its drafts are confirmed by the operator.
  - The SVG parses. No renderer is installed on the laptop, so the layout was checked by coordinates only: **look at it once** (Needs you 1).
- **`docs/white-paper-library-guide.md`:** XXXIII's at-a-glance row, its cross-reference row and its entry now say Draft 3, about 23,400 words, five appendices. The other papers the update file's section 5 names already carry their own guide edits from the branches chain-2 merged, so no other row was touched. `readme.md` carries no roster and is unchanged.
- **`docs/html/reporting-system-whitepaper.html`:** rebuilt (`tools/build_paper_html.py`).

## The reading-time estimate

Recomputed: about 23,400 words at the reports' 250 words a minute, about 94 minutes. The Reader's note says "about an hour and a half".

## Gates

| Gate | Result |
|---|---|
| `tools/check_library.py` (`make library-check`), once at the end | 27 papers, 0 failures, 0 warnings |
| `tools/validate_alpha_lab_3.py` (the tells quote this paper) | 65/0 |
| The Weekly's footer link | Unchanged: `READERS_GUIDE` and `READERS_GUIDE_PATH` (`daily_cascade/readability.py`) still match the title and the path |

CI: below.

## Every difference between the update file and the code (chain-2)

| # | The update file says | The code says (what Draft 3 prints) |
|---|---|---|
| 1 | Ninety-five code gates; data gates 7 | 118 code gates (115 Python, 3 shell) and 8 data gates |
| 2 | Feeds: 106 symbols, FRED 129, official 30, external 15, loggers 5 | 115 symbols, FRED 266 pulled (65 signal), official 31, external 37, loggers 7 |
| 3 | IBKR sync 09:00 to 17:00 every 30 minutes | 09:00 to 17:30 (the expression fires at 17:30; the unit's own comment still says 17:00). Its `[Install]` section is commented out although it is in DEPLOY_TIMERS |
| 4 | Meme scans 06:30 and 19:30 [verify] | chester-meme's own schedule is not in this repository. chester-reports' ingest runs at 21:45 (Sun–Fri) and again in the 06:45 overnight pass |
| 5 | The FlashAlpha budget is 30 calls a day | A daily budget of 60, planned at 57; SPX added; the plan ends 31 Mar 2027 |
| 6 | The regime threshold in a dealer config | `config/reporting_stack.yaml` (`dealer_block.net_to_gross_min: 0.10`); there is no `config/dealer*.yaml` |
| 7 | Cross-source tolerances for ^TNX/DGS10 and ^VIX/VIXCLS "measured the week of 19 Oct" | VIX/VIXCLS measured 15 Oct (0.01); ^TNX/DGS10 and ^TYX/DGS30 not yet measured (`tolerance: null`) |
| 8 | Correction, bear and lens disagreement in config | Code constants in `altdata/derived.py` (−10%, −20%, 30 points). The credit-widening thresholds are config (`metric_lenses.yaml`) |
| 9 | Monthly reading target 40 minutes (implied by Draft 2) | 55 minutes (raised); Quarterly 90; the addendum 5 minutes and 1,100 words |
| 10 | Monthly charts M1–M9 | Thirteen planned (M1–M13); M13, then M8, set aside first |
| 11 | Sources refusing the box include Yahoo Finance news (404) | Yahoo Finance news is an active tier-3 voices source; no refusal is recorded |
| 12 | GeckoTerminal's robots refuse | Its documented API is read under its own terms (ruling 4 of 17 Oct); only crawling of the site is disallowed |
| 13 | Webstat, Bank of Korea, Bank of Thailand "dropped" | Only their keys are not pursued. Webstat's keyless TEC 10 export and the Bank of Thailand's keyless table are read; Korea is a listed gap. `docs/workplan-v7-2026-10-16.md` still says "Needed" for Webstat and Korea (stale) |
| 14 | 3.2: an `inflation.driver` sub-state | The market-state object carries no sub-state. The inflation driver prints as a report-only read beside it (`altdata/st_r5_t1_rest.py`) |
| 15 | The audits include "gapped through the flip" among the flag words | Not an audited word. It is a descriptive Weekly flag; the audit covers pinned, held, amplified and dampened |
| 16 | A "no-internal-names gate" as an audit | A Weekly validator check plus the renderer's `reader_safe` rewrite; no runtime prose audit calls `internal_name_faults` |
| 17 | The conversion of dealer levels to ES through the ES block's roll record (built) | `altdata/dealer_es.py` is written and gated, but no report calls it. The ES block still prints its pending line. Listed in Appendix E |
| 18 | ST-5, ST-7, ST-8, ST-9, ST-10 "each ledger's verdict" | ST-5 and ST-10 are build sessions with no ledger. ST-7, ST-8 and ST-9 produced the SR-numbered ledgers; §9.9 prints their verdicts |
| 19 | Engines 6 and 7 and the grammar search "follow" | Engine 6 and the grammar search (`alpha/search.py`) are absent on chain-2; both in Appendix E |
| 20 | The surprise index (built) | Built, but only its FOMC leg is market-implied. No other release's consensus is stored ("no consensus"; payrolls a gap) |
| 21 | 5.3: the anchor makes one attempt (Draft 2) | The anchor's paragraph, the close's, the précis and the stacked sections all take the one revision. The Monthly storyline writer still runs up to three attempts on chain-2 (its own docstring says "ONE RETRY"); its fix is on `a47-chain3` |
| 22 | The restore drill (Draft 2's AUD-2) | Superseded by the weekly test (ruling 6) and never enabled. Its units are still on chain-2; they retire on `a47-chain3`. README section 13 on chain-2 still describes the drill |
| 23 | CLAUDE.md's Environment line | Out of date: it lists FRED, Anthropic and the dashboard token. The code also reads SMTP, Nasdaq Data Link, Massive, FlashAlpha, OpenFIGI and the SEC contact (Appendix A lists the names) |
| 24 | `daily_cascade/audit_retry.py`'s docstring says the withheld-drafts log is "not built here" | The log exists (`altdata/withheld_log.py`) and every edition writes it. The docstring is stale (the code is right) |

None of these is a claim the paper prints. Each row is a place where the paper follows the code.

## Needs you

1. **Figure 1:** the new side boxes were drawn by coordinates, without a render. Open `docs/html/reporting-system-whitepaper.html` once and check that the labels clear the arrows.
2. **Accept-all under rule 31.** Draft 3 is committed as a draft. It grants no right.
3. **Stale documents found while checking, for a later session:**
   - CLAUDE.md's Environment line (row 23);
   - `docs/workplan-v7-2026-10-16.md`'s key table (row 13);
   - `chester-ibkr-sync.timer`'s comment (row 3);
   - `audit_retry.py`'s docstring (row 24);
   - README section 13 (row 22, fixed on `a47-chain3`).

   None was changed here, by the paste's rule: edit no other paper, and only XXXIII's rows of the guide.
4. **No paper XXXV yet.** The guide and Draft 3 cite the Alpha Lab's brief of 12 October and its change order.

## CI

CI-TABLE
