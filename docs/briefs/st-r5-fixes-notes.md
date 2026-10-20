# st-r5-fixes — session notes (session A, 16 Oct 2026)

**What this branch builds on.** It is cut from the tip of `st-r5-t1-rest` (`4e79c4d`), so it carries `st-r5-rates`, `st-r5-index` and `st-r5-t1-rest`. **It merges after all three, in this order:** the chain, then `st-r5-rates`, then `st-r5-index`, then `st-r5-t1-rest`, then this branch.

It is branch-only. Nothing was merged or deployed, and nothing ran on the box. Session B's `st-r4-tranche-1b` and `6e-rest`, and every branch on the Friday list, are untouched.

**Part 0.** The Batch 7 change order is on `docs-batch-7` as `7b4f821`: "docs: Batch 7 change order, signal-triage round 6 part 2 (items 46-48), filed 16 Oct 2026". It is the Downloads file, byte for byte with LF endings, and its SHA-256 over LF is `173ce39d…7b01e`, as given. The branch is pushed and not merged.

**Before Part 1.** `st-r5-t1-rest`'s rerun, 38970297889 on `d2506d1`, was green, and its notes record that (`4e79c4d`). `sm-schema-1-1`'s run, 38970887891 on `6c8c666`, was green too. That branch is not named here, so its notes do not yet record it.

## The rulings of 16 October this branch applies

| | Ruling | Applied as |
|---|---|---|
| (a) | WAL and the busy timeout satisfy D1c for an append-only writer in the scheduled pulls; the write-lock helper is a separate item | The four held writers are lifted (1). Japan's CPI reader (5) is born unheld. |
| (b) | No recurring by-hand line survives without Ari's yes | Three keys dropped, plus the ACWI key (2, 3). `manual.global_pmi` and the AAII keys stay. |
| (c) | Judgment drafts are committed as drafted and listed for Ari's accept-all; the register's confirm step stays Ari's | Six drafts committed (6). |
| (d) | The blocklist may be strengthened, never weakened | `normalise()` reads the ACT dollar form (4). Nothing else in the register changes. |

## Each change and its fixture

### 1. The four held writers, lifted

- **Writers:** `altdata/sources/redfin.py`, `mba.py`, `sp500_members.py` and `wgc_stock.py`.
- **Change in each:** `HELD_FOR_D1C = False`, and the docstring's hold paragraph replaced by the ruling. The flag stays, so the hold can come back by one edit.
- **Roster:** all four are on `altdata/feeds.py` `EXTERNAL_WRITERS`, with a comment naming the ruling. The external pull (`feeds pull`) runs them, and their keys join the external freshness roster.
- **Registry:** all four sources in `source_registry.yaml` go from `held` to `live`, with a caveat recording the ruling. The "held for D1c" wording is gone from the metric descriptions and catalogue lines.
- **One fix made on lifting.** `sp500_members.produce()` decided between a first pull of two years and a later pull of ten days by whether ANY close was stored. The feeds pull passes no store, so every pull would have read two years for 500 names. It now asks the store which members it holds:
  - two years for a member not yet held, which covers the first pull and every member added to the index since;
  - ten days for the rest.
- **The fixtures.** The two gates' "held" groups became "lifted" groups (`validate_st_r5_rates` B, `validate_st_r5_t1_rest` B). Each now checks that:
  - the writer is not held, is on `EXTERNAL_WRITERS`, and its keys are on `feeds.external_keys()`;
  - each pull fetches its fixture files and writes in a temporary store: Redfin 17 rows, MBA 2, SPY 412 weights plus closes, WGC 1;
  - a second pull of the same files writes nothing;
  - SPY's closes are asked for two years for the 410 unheld members and ten days for the 2 already held.
- The Census hold on `st-r4-tranche-1` is session B's and is untouched.

### 2. The MBA line (item 37) without a hand-entered level

- **Key dropped:** `manual.mba_purchase_index`.
- **What the line prints:**
  - the year-on-year change (NSA), with its percentile, real window and n, as before;
  - the week's SA change;
  - a **chained index**: 100 at the first stored week, then each later week times (1 + its SA weekly change). It prints with its own percentile, real window and n, for example: "Chained from the weekly changes since 2026-09-18 (100 = that week): 97.5, the 25th percentile of its stored history since 2026-09-18 (n=4; …)".
- **Gaps.** A gap of more than 10 days between stored weeks breaks the chain and restarts it (`max_gap_days`, session-set, reason in the config). A missed week's change is unknown, so compounding past it would print a wrong level.
- **The 2023-low reference floor is removed. Why:** a floor is a published level, and the chain has an arbitrary base, so the two cannot be compared.
  - The order's "~127" was read off a chart of the MBA's own index level.
  - That level is member-only: the press release prints changes only (verify item 3, `st-r5-rates`).
  - No free series carries it, and the by-hand level that could have sat against the floor is dropped by ruling (b).
  - So there is no free level to set a floor against, and printing ~127 next to a chained 97.5 would invite a comparison that means nothing.
- **Wednesday-only in the close stays** (`mba_prints_on`, unchanged).
- **The fixture (`validate_st_r5_rates` F).** Five weekly changes: +5.0 three weeks before a gap, then +2.0, +1.5, −1.0 and −3.0. The chain restarts after the 21-day gap, and the gate checks it against the hand computation:

  | Week | Index |
  |---|---|
  | first after the gap | 100 |
  | next | × 1.015 = 101.5 |
  | next | × 0.99 = 100.485 |
  | latest | × 0.97 = 97.47045 |

  One week alone is the base; no weeks is no chain.

### 3. Three more keys dropped

- **`manual.nar_phsi`.** The housing block (item 36) reads Redfin alone and labels it "Redfin, single-source". The NAR line is gone.
- **`manual.euro_ccc_oas`.** The quality tail's European leg (item 41) prints euro high yield from FRED, labelled "the proxy for euro CCC, which has no free series". The "Euro CCC: by hand" line is gone.
- **`manual.msci_acwi_mcap_usd_bn`.** The gold/equity ratio (item 38) has no free denominator.
  - `config/st_r5_t1_rest.yaml` sets `cap_key: null`, with the reason.
  - The line prints "Gold against world equities — not tracked: no free source for world equity capitalisation.", in the Monthly's Slow layers and beside the allocation block.
  - The by-hand audit, queued, looks for a free source. Setting `cap_key` to a stored key in USD bn brings the ratio back, and the gate proves that path on a fixture key.
  - The WGC writer still runs, so the numerator is stored when a denominator arrives.
- **Gone everywhere.** The four dropped keys are out of:
  - `metrics_registry.yaml`: metric entries, families and long windows;
  - therefore the catalogue (`catalogue.resolved()`) and `tools/manual_input.py`, whose key list is the registry's `source: manual_input` entries;
  - both configs and all code.
- **Fixtures.** Both gates hold that no `.py` or `.yaml` outside `docs/` names any of the four (`check_dropped`). `manual.global_pmi` and the AAII keys stay.

### 4. The register's `normalise()`: the ACT preferred form

- **The change.** `register/instruments.py` strips a dollar sign and one to three series letters, with an optional dotted tail, after the listing qualifier and before the option and dotted rules. `BPY$A` → BPY and `BN$A` → BN, the same root as `BN.PR.A`.
- **What it never strips:** the root's own letters. `BEPC$A` stays BEPC, not BEP.
- **Nothing else** in `register/instruments.py` or the blocklist changes.
- **The fixture (`validate_register` B).** The register refuses each of these:
  - `BPY$A`, `BN$A`, `bn$a`;
  - `BN$A@NYSE.USD` (qualified);
  - `BPY.PR.A` (dotted);
  - an option on BPY in Polygon form and in OCC form with padding.

  The BN options were already there. `normalise` maps each form to its root, and `ABR$D` (unrestricted) resolves to ABR and stays clear. The blocked-attempt count goes from 14 to 21. Run locally: **191 passed, 0 failed**.

### 5. Japan's CPI (item 39's gap; needs-you 5 of the t1-rest notes)

**Built**, keyless and within robots: `altdata/sources/stat_jp_cpi.py`.
- **Source.** The Statistics Bureau's own national CPI files, `https://www.stat.go.jp/data/cpi/<BASE>/csv/zmi<BASE>aa.csv`, linked from its CPI page:
  - the 2025 base from January 2025, and the 2020 base from January 2020;
  - both run to August 2026; Last-Modified is 17 Sep 2026 23:31 GMT.
  - `www.stat.go.jp/robots.txt` disallows only `/library/opac/`.
  - It is not e-Stat's API, so no application id is needed.
- **How it reads the file.** Shift-JIS; columns are found by item code (row 3), never by position. It reads three codes:

  | Key | Code | Series | Role |
  |---|---|---|---|
  | `jp.cpi_yoy` | 0001 | all items | the headline leg |
  | `jp.cpi_core_yoy` | 0178 | less fresh food and energy | closest to the US core; the real differential's core leg |
  | `jp.cpi_less_fresh_yoy` | 0161 | less fresh food | the Bank of Japan's core, stored beside it |

- **The year-on-year change** is computed from the index within one base file and never chained across bases. Where both files hold a month, the newer base decides.
- **Tried on the real files from the laptop:** 68 months per key, January 2021 to August 2026. August 2026 reads all items 1.89%, core 1.93%, less fresh food 1.73%.
- **The panel.** Japan's row in `config/st_r5_t1_rest.yaml` reads `core_yoy` and `headline_yoy`. A small code change lets a country's core leg be a stored change on the year (`core_yoy`); it also fixes the leg guard, which tested a field that never existed. The US–JP real differential now prints.
- **Registered:** the three keys (percent_return, delta pp, a family and a long window), the source (tier A0, live), the catalogue command under `japan`, and the external roster.
- **The fixture (`validate_st_r5_t1_rest` B, G and J).** Two miniature Shift-JIS files, one per base, checked by hand for:
  - Aug 2026 from the 2025 base and Aug 2025 from the 2020 base;
  - no month without its year-earlier month in the same file;
  - a file missing a code is refused;
  - a robots disallow stops the fetch;
  - on its fixture files the pull writes 60 rows.

  The panel gets Japan real on core and headline, and US less JP of +80 bp by hand. Without Japan's CPI it is a gap, Japan named. The Currencies read prints the US–JP line.
- **The UK and Canada stay listed gaps** for the by-hand audit, and the config names the free sources:
  - **UK:** the Office for National Statistics' CPI time series (the MM23 dataset).
  - **Canada:** Statistics Canada's table 18-10-0004-01, the monthly CPI.

  Both are keyless downloads; neither is built here.

### 6. Drafts committed, for Ari's accept-all

| # | Draft | File and line | Source notes |
|---|---|---|---|
| 1 | Book A rule A-4, long-horizon expected return (item 30) | `docs/whitepapers/base-rates-whitepaper.md`, the new Appendix C, line 558 | `st-r5-index` |
| 2 | Book A rule A-5, oil-shock hedge sleeve (item 32) | same appendix, line 559 | `st-r5-t1-rest` |
| 3 | The peak-concentration table and its caveats (item 31) | `docs/whitepapers/equities-whitepaper.md`, new §B.1 in Appendix B, lines 359–372 | `st-r5-t1-rest` |
| 4 | The gold/equity base-rate note (item 38) | `docs/whitepapers/metals-whitepaper.md`, new Appendix E, lines 982–986 | `st-r5-t1-rest` |
| 5 | "Collision course", the bear side of what_driving_5_3 (item 35) | `docs/narrative-register-pairs.md`, lines 13–21 | `st-r5-index` |
| 6 | Disagreement pair "more hikes" against "the market does the tightening" (item 42) | `docs/narrative-register-pairs.md`, lines 23–33 | `st-r5-t1-rest` |

**About the homes:**
- **The rule table** goes in Base Rates because the Signal Triage order (§2.4) has Base Rates hold it until Portfolio Construction does. Appendix C copies A-1 to A-3 from that order so the table is whole, and adds mine with their dates.
- **No narrative-register entry.** The register's code (`altdata/narratives.py`) holds stories, and its confirm step is for proposed stories. A disagreement pair is not a story (it has no implied outcome to grade), so it cannot be a pending entry there. Both pair drafts live in `docs/narrative-register-pairs.md`, a new file that says so.
- **The gold note** goes to Metals, because XXVII, the numeral the draft named, is reserved for a Phase 2 paper that does not exist yet. Its last sentence changes with ruling (b): "The stack's monthly proxy divides by MSCI ACWI's capitalisation" is now "The stack does not track the ratio: there is no free source…".
- **Agreed with session B:**
  - Its item-24 rule is A-6, in the same appendix.
  - Its item-26 pair body becomes a section of `docs/narrative-register-pairs.md`.
  - Its side-B story `capital_competition` is a pending proposal in `config/narratives.yaml` on its branch, written through a new `proposals:` block, so the confirm is Ari's. This branch touches no narratives file.

**Not committed, and why:**
- **Item 42's Warsh-matrix line.** No Warsh matrix exists in the repository to hold it: the 25 Sep order names "Warsh matrix variables" as library work, unbuilt. The text is in the t1-rest notes' drafts. Needs-you 3. (Since moved to `docs/warsh-matrix-lines.md` on `st-r5-audit`.)
- **Item 39's sovereign-scorecard column.** It rides item 21's quarterly scorecard, session B's and unbuilt here.
- **Item 43's PMI.** It is a monthly by-hand entry, not a draft.

### 7. Items 31 and 32, ruled; no code changes

- **Item 32 stays report-only.** Its pre-registration (the t1-rest notes' table) opens after the 32b ledger.
- **Item 31's peak-band flag stays as built.** The overlay's 25% input is revisited at 31b.

## Gates run locally (one at a time, only those written or changed here)

| Gate | Result |
|---|---|
| `validate_st_r5_rates` (B lifted, E, F chain, G proxy, I drops) | 72/0 |
| `validate_st_r5_t1_rest` (B lifted and Japan's reader, G, H not tracked, J, K drops) | 89/0 |
| `validate_register` (the dollar form) | 191/0 |
| `check_registry` | OK |

Every other gate is left to CI, including the blocklist gates (`validate_alpha_no_orders`, `validate_security_master` on its branch), `validate_official_sources` and `validate_aq3_series` (they walk `EXTERNAL_WRITERS`), `check_library` (three papers and a new docs file), and anything that renders a PDF.

## CI

| Run | Commit | Result |
|---|---|---|
| 38974652897 | `ce6cf33` | **Failed, 93 of 95 jobs green.** The one failing gate is `check_library`, failure [10]: the built HTML editions of Base Rates, Equities and Metals were built from the papers before this branch's appendices. The second failed job is `gates-passed`, which only reports that a gate failed. This branch caused it. |
| (the fix's push) | the next commit | The three editions are rebuilt with `tools/build_paper_html.py`; no paper text changes. Its result is recorded in `docs/briefs/st-r5-audit-notes.md`, step 0, because the next branch's first push carries this commit too. |

## Box commands (Ari's, inside a window: weekdays 09:05–15:40 or 17:20–23:30 ET, never 16:00–17:20, clear of Sunday 05:00)

These run only after this branch is merged to main; the box's next wrapper pulls main. Each is one writer's first pull into the live store, one at a time, read-only otherwise:

```
cd ~/chester-reports && git log -1 --oneline      # main carries st-r5-fixes
~/chester-reports/.venv/bin/python -m altdata.sources.redfin
~/chester-reports/.venv/bin/python -m altdata.sources.mba
~/chester-reports/.venv/bin/python -m altdata.sources.wgc_stock
~/chester-reports/.venv/bin/python -m altdata.sources.stat_jp_cpi
~/chester-reports/.venv/bin/python -m altdata.sources.sp500_members    # about 500 names x two years from Yahoo: the longest; run it last
~/chester-reports/.venv/bin/python -m altdata.catalogue show jp.cpi_core_yoy
```

- **Each prints its summary.** OK and the rows written is a success. STALE carries its reason.
- **MBA's chain starts from the first stored week.** It is one week long on day one and grows by one each Wednesday.
- **No unit changes.** The writers ride the existing external pull.

## Files shared with the open branches

| Branch | Shared files |
|---|---|
| `st-r4-tranche-1`, `st-r4-tranche-1b` (session B) | `metrics_registry.yaml`, `source_registry.yaml`, `config/catalogue_commands.yaml` — additive, separate blocks |
| `6e-metric-lenses` (session B) | `metrics_registry.yaml` |
| `st-r6-es-block` | `config/catalogue_commands.yaml` |

- **Session B's branches, at stitching:**
  - B's queue file `docs/dated-appendix-queue.md` moves into this branch's Base Rates Appendix C and `docs/narrative-register-pairs.md`.
  - B's `config/narratives.yaml`, `altdata/narratives.py` and `tools/validate_narratives.py` are not touched here.
- `6e-rest` is not on origin yet.
- `docs-batch-7` and `sm-schema-1-1` share nothing with this branch.

## The sm-schema-1-1 branch (recorded here, since no notes file names it otherwise in this line)

- **What it is.** Chester-meme's change order for the Security Master export's schema 1.1, cut from `origin/aud-3b-security-master` (`2fb1048`), so it merges after AUD-3b. The export writes `schema_version` "1.1" and two new fields per security: `restricted` (boolean, from the Brookfield blocklist through `register/instruments.py`) and `restricted_reason` (the tier and root, or the name match). It also applies the 16 Oct ruling on the new-listing start date in `altdata/ticker_history.py`, and adds CLAUDE.md's rule that a session never writes into the chester-meme folder.
- **Tip.** `6c8c666`.
- **CI.** Run 38970887891, green.
- **Its own notes.** `docs/briefs/sm-schema-1-1-notes.md`, on that branch, which predates the CI result and does not record it.

## Needs you

1. **Accept-all on the six drafts above** (ruling (c)).
2. **The box commands**, after the merge, inside a window.
3. **The Warsh-matrix line (item 42) has no home.** No matrix exists in the repo. Say where it should live, or whether the library session builds the matrix first.
4. **World equity capitalisation.** The gold/equity ratio stays "not tracked" until the by-hand audit finds a free source.
5. **UK and Canadian CPI.** Both are listed gaps, with ONS and Statistics Canada named as the free sources. Say if you want either built.
6. **The narrative register has no disagreement-pair kind.** The pairs are a document, adjudicated by hand monthly. Building a pair kind, with its own confirm step, would be a separate item.
