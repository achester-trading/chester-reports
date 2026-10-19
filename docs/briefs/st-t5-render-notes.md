# st-t5-render: ST-14 and ST-15, the Monthly's PRL part and the emerging scan (session notes, 18 Oct 2026)

**This branch, `st-t5-render`, is cut from the tip of `st-t5-prl` (after its Part
0, `76299ef`), session B's own line in the second stitched chain.** It merges
after `st-t5-prl`, in the second chain (Thursday's).

Branch only: pushed, not merged, not deployed, nothing run on the box. No unit
was enabled, started or reconfigured. Session A's branches, Monday's chain and
line, and chester-meme were not touched (`a45-opening-setup-2` was read only,
for the trial merge below).

| Part | Commit |
|---|---|
| Part 0: the rulings on `st-t5-prl` | `76299ef` (on `st-t5-prl`) |
| ST-14 and ST-15, and their gate | `5d2cfbf` |
| The figure renamed M13 (after the trial merge) | `5f2a786` |
| st-t5-prl's CI line (cherry-picked from `st-t5-prl`) | `4262502` |
| These notes | the commit after |

## Part 0: the CI and the rulings on ST-13

The details are in `st-t5-prl-notes.md`. In short:

**The CI.** The build (`7c81ed1`) and its notes (`dd10f77`) failed
`validate_config_refs` (105 of 107 jobs).
- `crypto.watch` read as an unregistered metric id, because `crypto` is a
  registered namespace.
- The fix is in the gate: an `asset_class` field's value is vocabulary, not an
  id.
- The rulings commit, `76299ef`, is **success, 107 of 107 jobs**.

**The rulings:**
1. **CoinGecko stays retired.**
   - The fetcher and its switch are removed; the terms line is kept under the
     retired source; the order's register says MW-4's clause is superseded,
     dated 18 Oct 2026.
   - PRL now reads Yahoo's price and 24h volume at the basket's symbol (D4 from
     that volume) and DefiLlama's cap and circulating supply.
   - D5 prints "not tracked (source retired)" with its key named.
   - D3 is the formula against the explorer's supply, ESTIMATED until the
     explorer reads.
2. **The explorer:** no robots or terms line was pasted, so it stays undeclared
   and the height ESTIMATED.
3. **Scheduling, no new timer:** `altdata.prl weekly` (Saturdays) and
   `altdata.prl daily` are one line each in the basket's 17:25 run, after its
   writes, and on the freshness roster `prl`. The explorer reports PENDING (no
   allowance running) until it reads.
4. **SM00118 stands.** A gate proves the basket still resolves `PRL41876-USD` to
   `yfinance.crypto_prl` through it.

## Part 1: ST-14, the Monthly's Digital Asset Mechanism Watch part

`monthly_macro/prl_part.py`. It sits in the slow layers inside the
digital-assets material, after the crypto data layer's tables
(`prl_part.AFTER_TITLES`), in its own `try`, so a fault costs only the part.

**What it prints**, the order's 2.7.6 in order:

1. **The thesis status with its rule trace, and what moved.** The status reads
   as "an informational label by the rule of 2.7.5 with no decision rights",
   never as a recommendation. Below it: the status at the prior month's cutoff,
   and the idle-GPU flag (D6, Factor I attention, no scoring effect).
2. **The S1-S8 table:** baseline (the order's 19 Sep 2026 figures) / prior month
   / now / change.
   - **S3:** "not tracked (source retired): calc.prl_venue_conc".
   - **S4:** the explorer's difficulty, or "not stored: the explorer has not
     read (G-26)"; the pool share is NOT AVAILABLE (G-27).
   - **S5:** the overhang and the gap, each ESTIMATED where the height was.
   - **S6:** D4 and Yahoo's price.
   - **S1, S2, S7, S8:** "not read: a narrative signpost".
3. **The supply figure, M13** (realized against designed supply, the overhang
   on the right axis). It is drawn only once the explorer has stored a height
   and a supply. Until then there is no figure, and one line: "Supply figure:
   not drawn -- the explorer has not read (G-26) ...".
4. **The month's candidates and status changes**, from the mechanism-watch
   register (Part 2).
5. **The month's drafted narrative-register entries** (2.7.6's form), each
   marked draft.

**It reads, it does not compute.** Every figure is a stored row read as of the
cutoff: the `calc.prl_*` rows, the explorer's `pearl.chain_*` rows and the
basket's PRL price. Only a change between two stored values is derived here.
The basket's price and the explorer's rows are read beside the `calc.prl_*`
rows, because S4 and S6 need them and no `calc.prl_*` row carries them
(needs-you 4).

**The validators the row names**, as runtime guards and in the gate:
- **The Security Master guard:** coingecko_id "pearl-2", name "Pearl", class
  crypto.watch. On failure the part prints its refusal and nothing else.
- **The supply check:** the explorer's supply must sit within 2% of the formula
  at its height, else a CHECK line.
- **available_at:** a row without its available_at is a fault.
- **STALE never empty:** the last good values print with their dates and STALE.

The Daily grep gate is unchanged: the part lives in `monthly_macro`, and no
`daily_cascade` module names PRL or Pearl.

**The budget, and what the part displaces:**
- **Words:** none against the Monthly's 10,000. It prints tables and
  code-written lines, no paragraph, and no model call.
- **Charts:** M13 is planned twelfth, under the cap of 12 (11 planned plus M13).
  It is first in `DROP_ORDER`, so when the cap binds it is the first set aside.
  On session A's line, which plans M11 and M12, M13 makes a thirteenth, and the
  cap then sets it aside unless a trigger lifts it.
- **Displaced:** nothing.

`validate_monthly_stack`'s pins now read twelve planned, M13 last, first set
aside, and not drawn on its fixture (left to CI: it renders).

**The Surveillance-tab watch instrument (G-6)** is not built: the Alternative
Asset dashboard is not on this line, and G-6 (the fold) is open (needs-you 5).

**Fixtures** (`tools/validate_st_t5_render.py` A-C):
- the guard, holding and failing;
- the thesis as a label;
- S1-S8 with not tracked, ESTIMATED and NOT AVAILABLE;
- S6 against the prior month;
- the explorer read, with its supply at +0.40%, and a 5% CHECK;
- STALE, and an empty store, the table still printing;
- M13 drawn from a fixture explorer series (a PNG, no PDF);
- the part present, and absent with the Monthly unharmed;
- no words against the budget.

## Part 2: ST-15, the emerging-mechanism scan

`altdata/mechanism_scan.py`, the register `altdata/mechanism_watch.py`, and the
feeds in `altdata/sources/news.py` (`mechanism_items`).

### The query group (G-28)

`config/story_queries.yaml` gains a top-level `mechanism_watch` group beside
`queries`, with its own cadence (weekly), window (14 days), cap (60 items) and
`max_candidates` (20). Every existing reader takes `queries` only, so the
second group is safe in the same file.

The search engines stay retired: Google's and Bing's robots refuse their search
paths. So the order's 2.7.7 query set is declared as **terms that filter the
items of declared public feeds**. Each feed is read only where its robots.txt
allows the path, checked at every run, and only the title, the link and the
date are kept, never the body.

### The sources and their lines

All read 18 Oct 2026, by the session, while building; no gate fetches.

| Feed | URL | robots | terms |
|---|---|---|---|
| IACR ePrint | eprint.iacr.org/rss/rss.xml | no rule matches /rss/ | the publisher's RSS syndication; title, link, date kept |
| arXiv cs.CR | rss.arxiv.org/rss/cs.CR | no robots.txt (404) | as above. **export.arxiv.org's robots disallows everything, so its API is not used** |
| CoinDesk | coindesk.com/arc/outboundfeeds/rss/ | no rule matches | as above |
| The Block | theblock.co/rss.xml | no rule matches | as above |
| Blockworks | blockworks.co/feed | Allow: / | as above |
| Tom's Hardware | tomshardware.com/feeds/all | no rule matches | as above |
| Hashrate Index | hashrateindex.com/blog/rss/ | no rule matches | as above |

**The two non-RSS legs (MW-5):**
- **Recently added:** DefiLlama's open, keyless `api.llama.fi/protocols`, which
  publishes no robots.txt. Its terms line is the one the crypto basket already
  reads under. It keeps protocols listed in the last 14 days in the declared
  categories (Chain, Decentralized AI, Mining Pools, Gamified Mining).
  CoinGecko's recently-added list is not read: CoinGecko is retired.
- **The hashrate trackers: a listed gap, not a key.** hashrate.no's coin list is
  an HTML page with no feed or API, and Kryptex's listing path returned 404. The
  standing rule of 16 Oct applies; Hashrate Index's blog is read as a feed.

### The steps

1. **Collect:** the feeds' matching items and the recently-added protocols.
2. **Dedupe** against the Security Master (its names, aliases and CoinGecko ids,
   so Pearl and pearl-2) and the register (any status, so a rejected candidate is
   never surfaced again).
3. **The rule pre-filter** (2.7.7):
   - drop the exclusion classes by keyword (memecoins, forks, rebrands,
     restaking, L2s and rollups, GPU or compute marketplaces), unless on the
     override list;
   - keep only a candidate with a materiality-bar (iii) hit detectable by rule:
     a tier-1 exchange named, a market cap above $50M, a serious outlet's
     domain, a hashrate tracker's;
   - each hit is recorded with the candidate.
4. **The gate.** The model is called only when at least one candidate survives,
   once, with at most 20, through the one metered client (`model_meter`, report
   `mechanism_watch`).
   - Its prompt is **Appendix F verbatim**. It is read from the order at run time
     (`docs/change-order-signal-triage-2026-09-25.md`), not copied into code,
     because the appendix names a person and no committed file of this branch
     may. The bracketed list is substituted.
   - The gate holds the loaded text equal to the appendix's quoted block.
5. **Drafts only (rule 31).** Each qualifying candidate becomes a CANDIDATE row
   with `draft` set, at the grade "awaiting G-29". Each also gets a drafted
   narrative-register entry: factor I or V, at most 60 words. A candidate that
   fails is written nowhere; its criterion is listed in the run's report.

**The register** (`altdata/mechanism_watch.py`) holds the 2.7.7 schema in the
store's database:
- `mechanism_watch` and `mechanism_watch_status` (every change, who and why);
- `mechanism_watch_entries`, the drafted narrative-register entries.

**Why entries are held here:** the narrative register's grade scale is not in
the repo, and G-29 asks for it to be confirmed before anything is written at
its lowest grade. So the entries are held as drafts here and posted nowhere
(needs-you 1).

**The CLI:**
- `review` and `render` read only.
- `promote` (to WATCH) and `reject` print what they would do, and write only with
  `--confirm`, the operator's flag.
- PROMOTED (core coverage, MW-7) is a ruling, not a command.
- `promote` prints the Security Master entry to add, and does not write that
  file, which is the operator's.

**`make mechanism-register`** renders `docs/mechanism-watch-register.md` from the
store's table. A rendered view, never edited by hand; none is committed from an
empty laptop store.

**The schedule:** a step of the basket's 17:25 run that runs on Saturdays and
skips itself otherwise; no new timer.

**The budget:** at most one model call a week. The input is capped at 20
candidates (the prompt runs about 3,000 characters plus the list), and the
output at 4,000 tokens; the meter counts it.

**Fixtures** (D-E):
- **Feeds:** the fixture feed under the declared terms, with the window and no
  body; a feed refused by robots skipped with its rule.
- **Recently added:** DefiLlama's leg, by window and category.
- **Pre-filter:** Pearl dropped as covered, a memecoin as excluded, Lumen kept
  on its Kraken hit, a paper with no hit dropped, the $180M cap a hit.
- **The gate:** closed means no call; a dry run builds the prompt with no call
  and no write; open means one call, Appendix F verbatim with the list
  substituted, one CANDIDATE draft at the pending grade and one drafted entry
  (factor I, at most 60 words), the failing candidate listed, not written.
- **The part:** it prints the register's month.
- **The CLI:** nothing without `--confirm`, the change logged with it, PROMOTED
  refused, a rejected name never re-added, a 61-word entry refused, the
  rendered view.

## The gates, locally, one at a time

| Gate | Result |
|---|---|
| `tools/validate_st_t5_render.py` (new, in the Makefile) | **46 passed, 0 failed** |
| `tools/validate_st_t5_prl.py` (Part 0) | **61 passed, 0 failed** |
| `tools/validate_config_refs.py` (the CI fix; the new config group) | **79 passed, 0 failed** |
| `tools/validate_crypto_basket.py`, `validate_crypto_sources.py`, `validate_backups.py` | **93/0, 105/0, 28/0** |
| `tools/validate_audit_3a.py`, `validate_lenses.py` | **86/0, 49/0** |
| `tools/check_registry.py`, `tools/check_library.py` | OK; 0 failures, 0 warnings |

**Left to CI:** `validate_monthly_stack` (the M13 pins; it renders), the heartbeat
and freshness gates (the new roster), and everything else. No gate reads the
live store, fetches or calls a model; nothing rendered a PDF. CLAUDE.md reads
ninety-nine code gates (ninety-six Python), recounted from the Makefile.

## CI

Read once, with `gh run list --branch st-t5-render --limit 3`. Both runs were
queued when read; the numbers are in the session's closing report.

## Box commands, for Ari

Run these inside a window, after Thursday's merge, dry run first. Nothing here
was run.

1. **The first D-series compute:**
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.prl daily --dry-run | head -80'`
   then without `--dry-run`. After the merge the basket's 17:25 run does it
   daily by itself.
2. **The explorer read** (it reports PENDING until an endpoint is declared):
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.prl weekly --dry-run --force'`
3. **The first scan run.** The dry run reads the feeds and DefiLlama, dedupes,
   pre-filters and sizes the prompt, with no model call and no write:
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.mechanism_scan run --dry-run --force'`

   The real run (`run --force`, or the Saturday basket run) makes the one gated
   call only when a candidate survives, and writes drafts only. Review them with
   `ssh vps 'cd ~/chester-reports && .venv/bin/python -m altdata.mechanism_watch review'`.
   `promote` and `reject` are yours, with `--confirm`.
4. **The first Monthly with the part** is your dry run, as always. Read the part
   after the digital-assets material in the slow layers. It shows ESTIMATED
   heights and no figure until the explorer reads.

## Files shared with the open branches

**Session A's line** (`a45-opening-setup-2`, `a44-opening-setup`) also edits:
- `CLAUDE.md`, `Makefile`;
- `config/catalogue_commands.yaml`;
- `monthly_macro/charts.py`, `monthly_macro/stack.py`;
- `tools/validate_monthly_stack.py`.

A trial merge (`git merge-tree`, which writes nothing) shows **two conflicts
this branch adds**, both because session A's line plans its own M11 and M12:

| File | Resolution at the stitch |
|---|---|
| `monthly_macro/charts.py` | `ORDER` = session A's + `"M13"`; keep A's `ALL = ORDER + ("M12",)`; `DROP_ORDER` = `("M13",)` + A's; `PLACE` carries A's `"M12"` and this branch's `"M13"`. The docstring rows: both |
| `tools/validate_monthly_stack.py` | Take session A's cap and count checks, extended: with all thirteen drawn at a cap of 11, M13 then M8 are set aside; M13 is not drawn on the fixture, so it is never in `bad`. Keep this branch's ORDER pin with "M13 last" |

This is why the figure is M13: the first draft named it M11, which session A's
line already uses (Batch 6 item 40), and the rename is `5f2a786`.

The other shared files merge clean:
- `monthly_macro/stack.py`: the part's insert sits after the crypto data layer's
  block, a separate hunk;
- `CLAUDE.md` and `Makefile`: the count line and one gate line, recounted at the
  stitch;
- `config/catalogue_commands.yaml`: two lines before `altdata.sources.fng`.

Untouched: chester-meme, `.env`, the units, the registers, the trade ledgers and
`.claude/settings.json` (needs-you 3).

## Needs you

1. **G-29, the narrative register's grade scale.** None is in the repo, so the
   scan's entries are drafts in `mechanism_watch_entries` at "awaiting G-29", and
   nothing is posted to any narrative register. Rule the scale and where Factor I
   and V entries live (the story register in `altdata/narratives.py` is not a
   graded entry log), and a later session posts them.
2. **The feeds' terms.** Each feed is the publisher's own RSS, and only the
   title, link and date are kept, as the voices scan does. No site's terms page
   was read beyond that. Say if any should be dropped.
3. **The deny list.** `altdata.mechanism_watch promote ... --confirm` and
   `reject ... --confirm` are operator writes, like `altdata.narratives confirm`.
   I could not read `.claude/settings.json` (the read was refused) and did not
   edit it. The two belong on its deny list, with `tools/validate_deploy.py`
   group J if it holds the list.
4. **The part's reads.** The row says the part reads only `calc.prl_*` rows and
   the Security Master entry. It also reads the explorer's `pearl.chain_*` rows
   and the basket's PRL price, still stored rows and nothing computed, because S4
   and S6 need them and no calc row carries them. Say if they should be copied
   into `calc.prl_*` keys instead.
5. **G-6, the Surveillance-tab watch instrument:** not built. The dashboard is
   not on this line and the fold is open.
6. **The explorer:** still undeclared. When you paste a permitting robots line
   and the terms allow it, the endpoint goes in `config/prl.yaml`.
