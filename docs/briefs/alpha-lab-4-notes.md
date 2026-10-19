# alpha-lab-4: session notes (Parts 0 to 3)

**alpha-lab-4 final tip: the commit that adds these notes, on top of 541a298** (the last
code commit). b45-chain3 merges this tip, in the third chain.

# Second paste of 19 Oct 2026 (session B): Parts 0 and 1

Nothing merged to main, deployed or run on the box. No unit was touched. chester-meme
and session A's branches (chain-2, library-draft-3, a47-chain3) were not written.

## CI, second paste

| Run | Commit | Result |
|---|---|---|
| 39203678583, and the three before it | 18f472e, 2278874, fe4c429, cae2fb8 | 109/109 jobs green each: nothing to fix |
| 39287961485 | db92738 (CD-12) | **1 failure:** `validate_numeral_audit`. The rate guard's message wrote "16th" by hand. Fixed in 541a298 ("would make 16 in a day") |
| 39292353888 | 541a298 (Part 1) | see the closing report |

Gates run locally, one at a time (written or changed here):

| Gate | Result |
|---|---|
| `validate_alpha_lab_4` | 65/0 (groups C and D new) |
| `validate_alpha` | 257/0 |
| `validate_alpha_lab_3` | pass |
| `validate_alpha_proposer` | pass |
| `validate_crypto_sources` | 117/0 (group O new) |
| `validate_digital_addendum` | 94/0 |
| `validate_numeral_audit` | pass |
| `validate_audit_3a` | 86/0 |
| `check_registry` | OK |

**The gates that run the nightly loop** (`validate_alpha` and `validate_alpha_lab_3`)
set `CHESTER_UNIT_STARTED=0`, so the loop's new last step, the search, skips with its
reason. Without that, each simulated first-week night ran a 600 s search step on the
fixture store; one local run passed forty minutes before I stopped it. The search
itself is held by `validate_alpha_lab_4` groups B to D.

## Part 0

### Ruling 1: the three rule-31 drafts (8cb0ff5)

- **The G-26 note** in the signal-triage change order is now labelled "*Accepted as
  drafted (rule 31), 19 Oct 2026:*".
- **SR-29's line** is written under SR-29 in `docs/signal-triage-register.md`, ending
  with ruling 2's sentence. It is labelled accepted as amended.
- **The lab line** is `docs/alpha-lab.md` section 11, labelled accepted as amended. Its
  search clause is brought to ruling 5: the coverage rule, the variables expected to
  pass, the dealer regime pending on its history, and the nightly cadence. The loops
  table names the search as the nightly loop's last step.

### Ruling 5: the search (4b6a08a)

- **(a) Coverage.** `search.coverage()` runs at a run's start, before the manifest.
  - **What "history" means:** the first day any value of the variable was knowable,
    the earliest over its rows of max(observed day, available_at's ET date). A series
    backfilled today without vintages therefore starts today.
  - **The rule:** a variable joins only if that day is at least
    `coverage.min_years_before_holdout` (5) years before the holdout's first day.
  - **The manifest** records each variable's key, first date, required date, verdict
    and line.
  - **A variable that fails** is pending with "history from <date>". Its options are
    not candidates, and N (`bump_variant`) counts only what the run tests.
  - **Expected on the box:**
    - positioning passes: the CFTC net, each report reconstructed at its Friday
      release, from 2006 or so;
    - the macro and volatility dials fail: the market-state object's stored vintages
      are each available when computed, which is September 2026 even for the
      backfill;
    - funding fails: `calc.funding_agg` starts in October 2026.

    So the first run should test 768 candidates (4 x (1 + 3) x 3 x 8 x 2), not 3,840.
    `python -m alpha.search coverage` prints the answer read-only before any run.
- **(b) The dealer regime** stays `pending`. Its line is its history,
  `exposure.net_gex` (SPY): "dealer: pending -- history from <date> (needs <date>); the
  dealer regime is not in search-v1". It does not join at the stitch.
- **(c) The cadence.**
  - **Where it runs:** `search.nightly()` is the nightly loop's last step (after
    promote). The weekly loop no longer steps the search.
  - **The budget:** the unit's 1,200 s, less 180 s spare, less what the unit has spent,
    capped at 600 s. `scripts/run_alpha_nightly.sh` exports `CHESTER_UNIT_STARTED`
    before its pull. Under 120 s the step skips, prints why and writes a
    `search_skipped` event.
  - **When a run begins:** only in a month's first week (day 7 or earlier), and only
    when no run is unfinished. The CLI `run` obeys the same rule.
  - **One lock:** `files.lock` on `search/.lock` (flock on the box, msvcrt on Windows;
    released when the process dies). A second step while one holds it does nothing and
    says so.
  - **The Lab report's line** names the variables that passed and the ones that failed
    or are pending, each with its history line.
- **Gates (group C):**
  - a variable at four years is pending with its date, and its options are not
    counted (N = 4, not 13);
  - one at six years joins;
  - a series stored in 2024 for observations from 2010 starts in 2024;
  - the dealer's line is its captures' first date;
  - the budget grid leaves 3 minutes at every point, and the env start is read;
  - under 120 s the step skips and prints why;
  - an unfinished run is resumed, never restarted, and no new run begins while it is
    unfinished or outside the first week;
  - the search is nightly's last step and not the weekly loop's;
  - while another process holds the lock, a step does nothing.

### Ruling 2: CD-12, bitcoin-data.com (db92738, fixed in 541a298)

- **The terms, re-read 19 Oct 2026** (last updated 14 Oct 2026). They are quoted in
  `source_registry.yaml` `bitcoin_data`, now `status: built`:
  - **on storing:** no clause, so nothing forbids the store;
  - **on redistributing:** "BGeometrics data must not be provided to third parties
    through an API, data feed or any other machine-readable access". Nothing here
    offers any: the chester-meme export carries no btcdata key, and the backups are
    your own encrypted copies;
  - **on publishing:** "Personal and non-commercial publishing does not require the
    add-on", with BGeometrics credited. The Monthly's line credits it;
  - **on the key:** one key per registered user, so the key lives on the box alone.
- **The fetcher,** `altdata/sources/btcdata.py`:
  - **what it writes:** `btcdata.lth_supply`, `btcdata.sth_supply`,
    `btcdata.supply_current`, and `btcdata.lth_supply_share`, which it computes (LTH
    over current x 100, on the days both are read);
  - **point in time:** `available_at` is the pull instant (ingest_instant);
  - **the key** is sent as `Authorization: Bearer`, never in a URL, and is redacted
    from errors;
  - **the guard:** every request is counted in `~/.chester/btcdata_requests.json`
    before it is sent. It refuses the 9th in a rolling hour and the 16th in a rolling
    day (the terms' 8 an hour, which is stricter than the API's own 10), with no retry;
  - **the budget it spends:** one request per series, so 3 a day. The first run reads
    the free tier's four years (about 1,460 days) in one page per series (size 2,000),
    so it also spends 3, unless the API pages shorter;
  - **without the key** it fetches nothing and returns `NOT_TRACKED` with "not tracked
    (btcdata.lth_supply_share): no key in .env (BITCOIN_DATA_API_KEY)";
  - **`budget`** prints the requests spent, and whether the key is present (never its
    value).
- **Where it runs:** a step of the crypto basket's 17:25 run (`step btcdata` after
  treasury), which loads .env. No new timer. It is not on `feeds.EXTERNAL_WRITERS`,
  which would pull a second time and spend the budget twice.
- **The readers:**
  - **the Monthly's network-health block** prints SR-29 as a triple-form row once a
    share is stored, with "read the 3-month change with price context, not the level;
    source: BGeometrics (bitcoin-data.com)";
  - **with no row,** it prints "not tracked ... no key in .env
    (BITCOIN_DATA_API_KEY)", or "awaiting the first pull" once the key is present;
  - **the addendum's on-chain cell** reads the same through
    `crypto_blocks.sr29_absent()`.
- **The response's field names were not confirmed:** the spec declares no schema, and
  I sent no further unauthenticated request. The parser takes the day from `d` and the
  row's one numeric value field, and **refuses a row with two** rather than guessing.
  The first dry run on the box shows the real shape.
- **Registry and catalogue:** the four keys are registered (units `count` and
  `percent_share`, families `quantity` and `ratio`, long window 4y); the catalogue has
  the command's line.
- **Gates (validate_crypto_sources group O):**
  - a fixture response parses, and a two-field row is refused;
  - the share is computed by hand;
  - the first run's three requests start 2022-10-17;
  - the 9th request in an hour and the 16th in a day are refused, and a second guard
    reads the first's count;
  - a refused request is not sent;
  - with no key nothing is fetched;
  - the HTTP call is never reached;
  - the key goes in the header, with no retry and no address in the User-Agent.

  Both gates set the key to empty in the environment, so the laptop's .env cannot
  change their verdict.
- **CD-11 (Dune)** stays unbuilt (ruling 3).

## Part 1: grammar v2's state condition (541a298)

- **`alpha-lab-rules/v2`** is v1 plus a rule-level `when` list. Each item is one of:
  - `state`: a path in the stored market-state object;
  - `zscore`: a registered key, with an optional instrument, a window, `min_rows` and
    the crowded_long and crowded_short bands;
  - `mean_band`: a key with a window and its on and off bands.

  Every item must read a value **knowable at the decision** and take one of its
  values. A missing value means no trade, with the skip reason "when: no value
  knowable at the decision".
- **One reader.** `rules.when_value()` reads all three kinds. `Data.state_vintage()`
  returns the value and its availability, and never reads a vintage stored after the
  decision. `Data.series(key, instrument)` reads an instrument's rows. The search's
  `Conditions.value()` calls `rules.when_value()` and has no arithmetic of its own.
- **The backtest** applies `when_ok()` after the trigger, and its availability raises
  the trade's `available_at`. **The grammar engine** applies it before a live signal.
- **v1 is unchanged.** A v1 rule may not carry `when`. The registered translations
  (H-002, H-004, H-005) backtest to identical trades as v1 and as v2 without `when`.
- **The search's family is on v2** (`config/alpha_search.yaml` grammar
  `alpha-lab-rules/v2`), before its first run.
  - A conditioned candidate is `rule_of()`: the base rule plus one `when` item. It is
    **backtested as that rule**, so its trades are its own and not the base rule's
    filtered after the fact.
  - The caps are checked per candidate.
  - A conditioned survivor registers its v2 `rule_dsl` with `needs_code: false`.
  - The manifest names the grammar, and the family's hash covers it.
  - **needs_code remains for nothing in search-v1:** all its kinds are v2 kinds.
- **The proposer stays on v1.** Its prompt names v1 only. A v2 `rule_dsl` from it is
  kept as text with "the proposer writes alpha-lab-rules/v1 only".
- **Documentation:** `docs/alpha-lab-rules.md` gains section 14, and CLAUDE.md's
  search paragraph names v2.
- **Gates (group D):**
  - a v2 rule on a fixture state trades only where the state was knowable and matched,
    and each trade's `available_at` covers it;
  - a session whose object was stored the next day never trades, and nor does one whose
    later revision says "calm";
  - SP500's z is computed from SP500's rows alone, against a hand z, while NASDAQ100
    reads differently;
  - v1 may not carry `when`, and an unregistered `when` key is refused;
  - the translations replay identically;
  - a conditioned candidate's formation trades in the search equal an independent
    backtest of its v2 rule, trade for trade, and differ from the filtered base;
  - `Conditions` calls `when_value`;
  - a conditioned survivor's rule compiles;
  - the manifest's hash differs with the grammar;
  - the proposer stays on v1.

## Box commands (for Ari; inside a window; dry run first)

```bash
cd ~/chester-reports

# The search: coverage first (read-only), then a scratch dry run as of a first-week
# day; the first real step is the nightly loop's own, in November's first week
.venv/bin/python -m alpha.search coverage
ALPHA_RESEARCH_DIR=/tmp/search-dry .venv/bin/python -m alpha.search \
  --ledger /tmp/search-dry.db run --as-of 2026-11-02T22:00:00+00:00 \
  --max-candidates 8 --max-seconds 120 2>&1 | tee ~/logs/search_dryrun.log

# bitcoin-data.com, once BITCOIN_DATA_API_KEY is in .env: the budget (no request),
# then one pull by hand before the basket's run does it (3 requests of the 15)
.venv/bin/python -m altdata.sources.btcdata budget
.venv/bin/python -m altdata.sources.btcdata 2>&1 | tee ~/logs/btcdata_first_pull.log
```

E-6 is registered after the third chain merges (b45-chain3's notes carry the
command).

## Needs you (second paste)

- **The key:** register bitcoin-data.com's free key and add it to .env as
  `BITCOIN_DATA_API_KEY`. The first pull's log shows the response's real field names;
  if the parser refuses a row, the fix is one line.
- **The search's expected first count is 768** (positioning alone joins). Coverage on
  the box decides. Say if you want the dials' history re-thought before November.
- **No new rule-31 draft on this branch:** ruling 1's three are now written in as
  accepted.

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
