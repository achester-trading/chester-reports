# alpha-lab-4: session notes (Parts 0 to 3)

**st-t5-render final tip: ef9014c** (frozen; nothing failed, so no fix was pushed to
it).

Branch `alpha-lab-4` from st-t5-render's tip `ef9014c`. Session B, 19 Oct 2026.
It builds on st-t5-render and merges after chain-2, in the third chain. Parts 1,
2 and 3 are all on this branch; no sibling `crypto-tranche-c` was made.

**Part 4 was not run.** `git fetch origin chain-2` (once, about 01:25 ET) found no
`chain-2` branch on origin, so `docs/briefs/chain-2-stitch-notes.md` could not be
read and `library-st-l` was not created. Re-issue Part 4 once session A's stitch
reads "STITCH COMPLETE".

Nothing merged, deployed or run on the box. No unit was touched. Session A's
branches, Monday's chain and chester-meme were not touched (session A's tip was
only read, for the trial merge below).

## CI

| Run | Commit | Result |
|---|---|---|
| st-t5-render 39179600814 | 5d2cfbf | 108/108 jobs green |
| st-t5-render 39179648039 | 5f2a786 | 108/108 jobs green |
| st-t5-render 39179786190 | ef9014c (the tip) | 108/108 jobs green |
| alpha-lab-4 39200893253 | 06f73a3 (ruling 1) | green |
| alpha-lab-4 39202017168 | d701c83 (engine 6) | green |
| alpha-lab-4 | 18f472e, 2278874, fe4c429, this notes commit | see the last section |

Gates run locally, one at a time (the ones written or changed here):

| Gate | Result |
|---|---|
| `validate_st_t5_prl` | 62/0 |
| `validate_alpha_lab_4` (new) | 35/0 |
| `validate_alpha` | 257/0 |
| `validate_audit_3a` | 86/0 |
| `validate_crypto_sources` | 106/0 |
| `validate_digital_addendum` | 94/0 |
| `check_registry` | OK |
| `check_library` | 0 failures, 0 warnings |

## Part 0: st-t5-render's CI, and ruling 1

- **st-t5-render** is green on all three runs, so it was not touched. Its final tip is
  `ef9014c`.
- **Ruling 1 (G-26 closed as a listed gap)** is `alpha-lab-4`'s first commit,
  `06f73a3`:
  - `config/prl.yaml`'s `explorer` entry stays undeclared and gains its `status:
    listed gap`, its reason (no robots file: both `/robots.txt` and
    `/robots.txt?network=mainnet` 404 with the app's HTML; no published API; no terms
    covering automated access) and `ruled: 2026-10-18`.
  - The fetcher's docstring and its "not declared" reason say the same.
  - The height stays ESTIMATED from Appendix E's anchor, and D3 prints ESTIMATED.
  - The dated note is appended to the signal-triage register
    (`docs/change-order-signal-triage-2026-09-25.md`, "Register note -- 18 Oct 2026"),
    marked as a rule-31 draft.
  - If Pearl publishes an API with terms, its declaration is one line.

## Part 1: X-3.3, engine 6, extremes reversion

`alpha/engines/reversion.py`, registered as `reversion` in `config/alpha_engines.yaml`
(family `reversion`).

- **The trap, avoided.** The engine never reads the move screen's "false flag k/N",
  which is in-sample. It identifies a print on day t only against that series'
  trailing changes **as known at t's nightly decision** (17:40 ET):
  - the window is 1,826 calendar days, at least 500 changes, population sd, with
    today's change excluded;
  - a day whose vintage was revised, or that became knowable after a later day, takes
    the exact vintage-by-vintage path.

  The gate plants a shock that the whole-window statistics call a 6.1-sigma print but
  that had only 299 trailing changes on its day, and proves it is never counted.
- **Pre-registered** in `config/alpha_reversion.yaml`'s `spec`, whose sha256
  (`91100c55...a3a26e`) the roster's E-6 quotes
  (`alpha/research/roster-2026-10-19-x3-3.yaml`). The spec fixes:
  - **the bucket:** the series and the sign of its print;
  - **the data gate:** 30 completed prints in the formation sample (the bucket's first
    30 completed prints, in completion order), else "awaiting (n=k of 30)" and no
    trade;
  - **the reversal measure:** the share at least half reversed at 1, 5, 10 and 20
    sessions;
  - **the horizon rule:** the highest formation share, ties to the shorter, frozen;
  - **the instruments:** the basket's tradeable symbols with a cost class, as the
    trend engine filters them;
  - **the costs:** the cost model's round trip, plus borrow, roll and funding;
  - **the exit:** the horizon. The cost model sets no stop, so there is none;
  - **the family:** `reversion`.

  The engine refuses (`SpecChanged`) a spec that no longer hashes to its manifest.
- **The trade.**
  - It fades only prints identified after the bucket's formation completed, and only
    where the frozen share is at least 0.5.
  - It enters at the next session's open where an open is stored, else at its close.
  - Formation prints are never traded.
- **The harness.** It runs through the workbench like engines 4 and 5. Its coverage
  waits ("insufficient history") until the open buckets hold 100 trades after a
  60-trade fit, and nothing is counted while it waits.
- **Gates (group A):**
  - at n=29 the bucket prints "awaiting (n=29 of 30)" and trades nothing; at n=30 it
    opens at horizon 5 and trades at it;
  - five later prints that reverse at 1 session leave it at 5;
  - an in-sample-only print is never counted;
  - a changed spec is refused;
  - costs reproduce 23 bp by hand (2 x (1.5 + 5 + 5) at $2,000 of capital), and a
    short adds 50 bp a year of borrow;
  - registered by manifest, the harness waits and counts only the registration's one;
  - `python -m alpha.engines.reversion lines` (the dry run) leaves the store's hash
    unchanged.

## Part 2: X-3.5, the grammar search

`alpha/search.py` with `config/alpha_search.yaml`.

- **The family (`search-v1`)** is 4 signal families x 20 conditioning options x 3
  horizons x 8 instruments x 2 exits = **3,840 candidates**, each a grammar-v1 rule
  backtested by `rules.backtest`.
  - The signal families are 63-day trend, 20-day dip, 20-day spike and the 252-day
    95th percentile.
  - The horizons are 5, 10 and 20 sessions.
  - The instruments are SPY, QQQ, IWM, TLT, GLD, HYG, XLE and BTC-USD.
  - The exits are time only, or a 3% stop.
- **The conditioning options** are "none", or one value of:
  - the dials: the stored object's macro dial, 9 states;
  - the volatility regime: the vol dial, 4 states;
  - positioning: the CFTC S&P 500 net's two-year z, in 3 bands;
  - the funding regime: calc.funding_agg's 7-observation mean, on, between or off.

  A conditioned candidate is its base rule's trades taken in that state, as the
  grammar's own conditioning split reads them.
- **The dealer regime is pending.** It is declared with the reason "joins when the 6b
  keys are on this line, at the third chain's stitch"; `plan` and the Lab report
  print it as skipped.
- **The order of a run:**
  1. The manifest is written through `alpha/manifest.py` before the first backtest. It
     fixes the family's sha256, the 3,840, the split, the deflation and the survivor
     rule.
  2. The family's variant count is raised by 3,840 (`Ledger.bump_variant(by=)`), and
     every candidate is deflated by that N.
  3. Formation runs the walk-forward (fit 1, test 10, the embargo, the constitution's
     hold-out months never fitted) against the constitution's gate. The holdout is the
     last 12 whole months before the run's month.
  4. The survivor list is frozen and hashed (`survivors.json`).
  5. Only then is the holdout backtested. Its pre-registered rule is at least 10
     holdout trades with a mean net of costs above 0.
  6. Survivors of both are registered: source `systematic`, channel `search` (new,
     source systematic only), at the manifest's instant.
- **What is written:** the hypothesis register only, plus the lab's own loop events and
  research files. The inbox now refuses a Drive file that claims the importer's or the
  search's channel.
- **The caps (my defaults, session-set):**
  - 400 candidates and 600 s a step, inside the weekly unit's 20-minute timeout;
  - a step resumes from `alpha/research/search/<run>/progress.json` (gitignored);
  - a resumed run refuses a changed family (`FamilyChanged`).

  At 400 a step, a run takes about ten weekly steps.
- **Schedule:** the weekly loop's last step.
  - A run begins in the first week of each month, and an unfinished one resumes on
    any week. There is no new timer.
  - The Lab report gains "## 10. The grammar search" (tested, survivors, N, the
    pending variable).
  - Each monthly run re-counts its 3,840 in the family's N, since every re-test is a
    trial.
- **Gates (group B):**
  - a 12-candidate fixture family is counted whole before the first test;
  - the manifest fixes the count and the split, and refuses a changed family;
  - the candidate and wall-clock caps stop a step, and the next resumes;
  - no formation backtest reaches the holdout, which is backtested only after the
    freeze;
  - TLT passes formation, fails the holdout (5 trades, need 10) and is not written;
    GLD passes both and is registered `systematic`, and the harness's manifest check
    accepts it;
  - nothing else is written (no engine row, no promotion);
  - the pending variable is skipped with its reason;
  - the Lab report prints the line.

## Part 3: CD-12, the long-term-holder supply share

**Not tracked.** What I verified on 19 Oct 2026:

- **Robots:** `bitcoin-data.com/robots.txt` and `api.bitcoin-data.com/robots.txt` both
  404, so the REP excludes nothing.
- **Endpoints:** the OpenAPI spec (`api.bitcoin-data.com/v3/api-docs`) serves
  `/v1/long-term-hodler-supply-btc`, `/v1/short-term-hodler-supply-btc` and
  `/v1/supply-current`. One request answered without a token, with headers of 10 an
  hour and 15 a day.
- **Terms** (charts.bgeometrics.com/terms.html, "Last updated: October 14, 2026"):
  - "The BGeometrics Bitcoin Data API is available with a free API key";
  - "To use the API, obtain a key at bitcoin-data.com";
  - "Free tier: 8 requests per hour · 15 requests per day";
  - "Free-tier access is intended for personal projects, research, and evaluation".

So it is not keyless within its terms, and nothing is pulled:

- `source_registry.yaml` `bitcoin_data` is not_yet_sourced, with those lines quoted.
- `btcdata.lth_supply_share` is registered `tracked: false`.
- SR-29 prints "not tracked (btcdata.lth_supply_share): bitcoin-data.com's terms ... so
  it is not keyless; no by-hand line (rule 30)" in the Monthly's network-health block
  and in the addendum's on-chain cell.
- No fetcher was written, and D-8's by-hand fallback is not kept (rule 30).
- `validate_crypto_sources` holds it.

**CD-11 (Dune) is not built:** it needs `DUNE_API_KEY` in `.env`.

## Box commands (for Ari; inside a window; dry run first)

```bash
cd ~/chester-reports

# Engine 6: the dry run is read-only (each bucket's state from the live store)
.venv/bin/python -m alpha.engines.reversion lines 2>&1 | tee ~/logs/reversion_lines_dryrun.log
# then register its hypothesis BY MANIFEST (a box write; before any backtest)
.venv/bin/python -m alpha.manifest register alpha/research/roster-2026-10-19-x3-3.yaml

# The grammar search: the plan (no store, no write), then a capped dry run into
# scratch files only, then the first real step (or leave it to the weekly loop's
# first-week step)
.venv/bin/python -m alpha.search plan
ALPHA_RESEARCH_DIR=/tmp/search-dry .venv/bin/python -m alpha.search \
  --ledger /tmp/search-dry.db run --max-candidates 8 --max-seconds 120 \
  2>&1 | tee ~/logs/search_dryrun.log
.venv/bin/python -m alpha.search run 2>&1 | tee ~/logs/search_first_step.log
```

There is no LTH pull: the series is not tracked.

## Files shared with the open branches

- **The trial merge** (`git merge-tree`) of `alpha-lab-4` against session A's newest
  tip `a45-opening-setup-2` shows **no conflict beyond those st-t5-render already
  has** with it (CLAUDE.md, Makefile, metrics_registry.yaml,
  tools/validate_audit_3a.py, among others), which chain-2's stitch resolves.
- The files here that other lines also touch:
  - **CLAUDE.md:** the count line, the engine 6 and search paragraphs, and the CD-12
    paragraph;
  - **Makefile:** one gate line;
  - **metrics_registry.yaml and source_registry.yaml:** one entry each;
  - **tools/validate_audit_3a.py:** its count plant now reads digits;
  - **tools/validate_alpha.py:** the engine list.
- **The count line** now reads "100 code gates (97 Python": chain-2's count plus this
  gate. The plant in `validate_audit_3a` group F now also matches digits, because "a
  hundred" is no one- or two-word number the parser reads. At the third chain's
  stitch, recount it as chain-2's code gates plus one.

## Needs you

Every rule-31 draft below is for your accept-all.

1. **Rule-31 draft, already in the file:** the G-26 register note at the end of
   `docs/change-order-signal-triage-2026-09-25.md`. Accept, or say what to change.
2. **Rule-31 draft register line for SR-29** (I wrote none into
   `docs/signal-triage-register.md`): "SR-29 (19 Oct 2026, CD-12): not tracked.
   bitcoin-data.com serves the LTH and STH supply, but its terms make the API a
   free-key service, so it is not keyless; D-8's by-hand fallback is superseded by
   rule 30. A free key in .env would make it one fetcher."
3. **Rule-31 draft register line for the lab** (for `docs/alpha-lab.md` or the
   order's section 5): "X-3.3 engine 6 built (alpha-lab-4, 19 Oct 2026): spec sha256
   91100c55...a3a26e, hypothesis E-6 to be registered by manifest. X-3.5 the grammar
   search built: family search-v1, 3,840 candidates, the dealer regime pending until
   6b's keys join at the third chain's stitch."
4. **bitcoin-data.com's free key.** Registering it takes an email, and it is limited
   to 8 an hour and 15 a day for "personal projects, research, and evaluation". Yes
   (a key in `.env`, then one fetcher), or keep SR-29 not tracked?
5. **Dune (CD-11):** `DUNE_API_KEY` in `.env`, or leave it unbuilt?
6. **Engine 6's session-set choices, before you register E-6** (registration freezes
   them):
   - the minimum reversal share of 0.5 at the frozen horizon;
   - the formation sample as the first 30 completed prints;
   - the move screen's window, minimum and pstdev;
   - the next-open-else-next-close entry;
   - no stop beyond the horizon.
7. **The search's family, before its first run** (its manifest freezes each run): the
   four signal families, the eight instruments, the 3% stop, the 12-month holdout, the
   10-trade holdout minimum, and the caps (400 candidates, 600 s).
8. **Conditioned survivors register `needs_code`.** Grammar v1 has no trigger on a
   market-state value or on an instrument-keyed series, such as the CFTC net by
   market. A survivor with a conditioning option therefore registers as text, queued
   for the research sitting, while an unconditioned survivor registers its rule. A
   grammar v2 `state` condition would close this; it is not built.
9. **Part 4** (ST-L's appendices and Tranche H): re-issue once chain-2 reads "STITCH
   COMPLETE".
10. **From st-t5-render**, still open as you said: G-29's grade scale, the feed terms,
    the deny-list entries for `alpha.mechanism_watch promote/reject --confirm`, the
    part's reads, G-6, and the explorer (now closed as a gap by ruling 1).

## CI for the rest of this branch

Read once after the notes commit. The numbers are in the session's closing report.
