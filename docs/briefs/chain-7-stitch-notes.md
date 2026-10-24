STITCH: pushed; CI recorded below.

# chain-7: the post-Monthly branches since chain-6, stitched into one (session B, 24 Oct 2026)

**What it is.** One branch, `chain-7`, carrying everything built since chain-6 for after the 1 Nov Monthly, so the post-Monthly merge is ONE pull request with every conflict already resolved:
- a63-6f-calibration (6f tranche 2), which carries a62-6f-build (6f tranches 1, 3 and 5, with a60-6f-spec), a61-rulings-1024 (the rulings of 24 Oct) and chain-6;
- b60-reading-budgets (D19/D20), which carries b59-trigger-sources (D15, D26) and chain-6.

**chain-7 MUST NOT merge before the 1 Nov Monthly.** a61b-feed-repair is NOT in chain-7: it merges to main on Tue 27 Oct by itself, and chain-7 takes main after that (a later step, not tonight).

**How it was made.** chain-6's method:
- merges only, one `--no-ff` merge commit per tip, in the paste's order, each "Merge <branch> into chain-7 (seventh chain, 24 Oct)";
- no rebase, no squash, no force-push;
- each conflict resolved once, as the union where the sides add different things;
- the Master Guide's HTML rebuilt with its builder, never hunk-resolved;
- the gate count recounted from the merged Makefile;
- then ONE commit stripping people's names (D28).

**Branch-only.** I pushed `chain-7` and nothing else. No pull request, no merge anywhere, nothing on the box, no unit, no register write, no `.env`. Its own worktree is `../chester-chain7`; session A's `../chester-a57` and `../chester-a61b` were not touched.

## The order, as merged

**Base:** `origin/chain-6` at `69cc88d`. Every ref was fetched before the first merge, again immediately before each merge, and again before the final push.

| Step | Branch | Tip merged | Its own CI at merge time | Merge commit | Files resolved |
|---|---|---|---|---|---|
| 1 | a63-6f-calibration | `02f89b0` (carries a62 `5e3f6f5`, a61 `4a663a3`, a60 `755d8aa`) | a62's round 2 green (40119480977); a63's round-1 run in progress | `eceabdc` | none: a clean merge (chain-6 is its base) |
| 2 | b60-reading-budgets | `dc085db` (carries b59 `dca64bc`) | green, run 40121026725 at `67fdd3e` (tip notes-only) | `8ab7606` | `daily_cascade/stack.py`, `daily_cascade/weekly_stack.py`, `monthly_macro/stack.py`, `docs/html/master-guide.html`; CLAUDE.md's count by hand (below) |
| 1b | a62-6f-build, again | `00cafef` (A62's notes: CI round 2 green; it moved after step 1 and a63 does not carry it) | green, 40119480977 | `8e7e6af` | none: notes only |
| 1c | a63-6f-calibration, again | `7eabc08` (A63's CI round-1 fix `aeea2bd` and its notes; it moved during the stitch) | queued when merged (40132149062) | `53adb24` | none: `daily_cascade/state_v2_block.py` and a63's notes, clean |
| strip | — | — | — | `80a1793` | D28 (below) |

Steps 1b and 1c landed in the order 1b, 1c: a command-chaining slip ran a62's merge first. They touch different files, so the order changes nothing.

## Every conflict and its resolution

| File | How |
|---|---|
| `daily_cascade/stack.py` | the close's extras: a63's dial-transition line (`state_v2_block.close_extras`), then b59's one-day 10-year flag line (`b59_block.close_extras`), both kept |
| `daily_cascade/weekly_stack.py` | Mechanics: b59's block stays INSIDE `if sessions:` (it reads the first and last session), after a58's events; then a62's tail-families line and a63's transition table, at the outer level |
| `monthly_macro/stack.py` | the slow layers: a62's tail families and debt-cycle branch, a63's transitions with the dimensions' unledgered table, then b59's `place_slow` (GDELT and the model releases, placed after the Factor lines by its own rule); every sub-section kept |
| `docs/html/master-guide.html` | rebuilt with `tools/build_paper_html.py docs/master-guide.md`; the `.md` merged cleanly (a62's and b60's rows) |
| CLAUDE.md (merged cleanly, recounted) | the worded gate count: a63's `validate_6f_calibration` and b59's `validate_b59` each add one gate to chain-6's 137, so it is **one hundred and thirty-nine code gates (one hundred and thirty-six Python, three shell)**, recounted by listing the Makefile; `validate_audit_3a` reads the same (88/0) |
| `Makefile`, `metrics_registry.yaml`, `source_registry.yaml`, `config/catalogue_commands.yaml`, `tools/validate_weekly_stack.py`, `tools/validate_batch15_2.py` | merged cleanly as unions (both sides added different lines); checked: `check_registry` OK |

**No Security Master collision.** a61 took SM00215 (QAI) and SM00216-SM00220 (the five ProShares funds), `next_id` 221. b59 and b60 add no instrument, so nothing is renumbered.

**Not in chain-7:** a61b-feed-repair (merges to main by itself on 27 Oct).

## The final counts

| Count | Value | From |
|---|---|---|
| Code gates | **139** (136 Python, 3 shell), 8 data gates | chain-6's 137, plus a63's `validate_6f_calibration` and b59's `validate_b59`; a60, a61, a62 and b60 add none |
| `FRED_PULL_SERIES` | **283** | unchanged from chain-6 (no branch adds a FRED series; a62's `calc.cp_bill_bp` is derived from two FRED legs already pulled) |
| Symbols (`yfinance_source.SYMBOLS`) | **127** | chain-6's 126 + a61's QAI |
| Security Master `next_id` | **221** | a61's SM00215-SM00220; 220 instruments |

## The names stripped (D28; one commit, `80a1793`)

**Scope, as D28 rules it.** People's names come out of code comments, docstrings,
config comments and registry text. Not touched: filed change orders, rulings logs,
ledgers of record, white papers and everything else under `docs/`; test fixtures;
and the gates' own name guards. The guards are regexes that check a name is
ABSENT (`validate_st_t5_render.NAME_RX`, `validate_batch15_1.PEOPLE` and its
`\bAri\b` check, the people patterns in `validate_batch14_a1`, `_b2` and
`validate_batch15_2`); they must keep the names they look for.

**The operator's name: 65 lines in 46 files, each "Ari" made "the operator".**

| Where | Lines |
|---|---|
| `altdata/` | `derived.py` (2, the "listed for" lines of the family check), `figi.py`, `purge_synthetic.py`, `security_master.py`, `sm_draft.py` (the draft's header line), `sources/blockscout.py`, `sources/fut.py` (2), `sources/spdji.py`, `st_r5_rates.py` |
| `config/` comments | `basis_proxy`, `batch5_tranche_1b`, `crypto_sources` (2), `data_quality`, `digital_addendum`, `digital_asset_calendar`, `listing_exchanges`, `monthly_themes` (2), `narratives`, `prediction_markets` (2), `releases`, `reporting_stack`, `risk_limits`, `scoreboard`, `security_master`, `st_r5_rates`, `st_r5_t1_rest`, `tracked_entities`, `vol_event` |
| config text | `crypto_sources.yaml` `eth_supply_burn`'s gap reason; `digital_asset_calendar.yaml`'s MSCI event `source` |
| registry text | `metrics_registry.yaml:18105` (the families comment, and the line `tools/assign_families.py` writes for it); `source_registry.yaml:2551` |
| `daily_cascade/digital_addendum.py` | the appendix line's docstring and its two printed strings: "a draft for the operator's accept-all" |
| `monthly_macro/` | `prose.py` (3), `v2.py` (3) |
| `scripts/rclone_crypt_env.sh` | 2 comments |
| `tools/` | `assign_families.py` (2), `calibration/os6_positioning.py` (the docstring and the ledger's printed line), `figures/master_guide.py` (2, and "his touches" made "the operator's touches"), `massive_flatfiles_backfill.py` (2), `seed_security_master.py`, `validate_a55_box_fixes.py`, the check messages of `validate_alpha`, `validate_by_hand_audit`, `validate_secondary_notes`, `validate_security_master` and `validate_systemd_units` (a comment), and `validate_digital_addendum`'s pin of the appendix line, which follows the printed string |

Kept: `validate_by_hand_audit.py:197`'s pinned quotation `"weights stay Ari's" in text`.
It checks the Warsh-matrix document under `docs/`, a filed text, which keeps its words.

**Other people's names: 9 lines.**

| File | Was | Now |
|---|---|---|
| `altdata/ledgers/st_r4_19b.py:13` | "(Dashiell, Schwab, as the order records it)" | "(Schwab's, as the order records it)" |
| `config/batch5_tranche_1b.yaml:65` | "re-read from Dashiell's post" | "re-read from the Schwab post" |
| `altdata/sources/fed_calendar.py:13` | an example title naming a Fed governor | "Speech - Governor <name>" |
| `altdata/sources/shiller.py:2`, `config/catalogue_commands.yaml:591` | "Robert Shiller's stock market data" | "Shiller's online stock market data (Yale)" |
| `source_registry.yaml:2462` | "Aswath Damodaran -- industry datasets (NYU Stern)" | "Damodaran Online -- industry datasets (NYU Stern)" |
| `config/narratives.yaml:421-423` (a story's `proposed_by`) | four strategists named beside their firms | the firms only: "(BlackRock Investment Institute, and a second desk)", "(TAAI; BofA)" |
| `config/rates_anchors.yaml:46` | "Courtial's fit excluded China" | "The twin-deficit fit excluded China" |

**Kept, and why (listed for you, needs-you 3):**
- **Eponymous datasets, models and statistics.** They name a source or a method, not
  a person's view: the Wilson interval, ACM (Adrian, Crump and Moench, 2013, the
  model's citation), the Sahm rule, Amihud, the Warsh matrix (a library term),
  Ken French's data library, Damodaran's and Shiller's datasets (their source ids
  and store keys `damodaran.*` and `shiller.*`), and Yardeni Research's feed.
- **`config/rates_anchors.yaml`'s `voice:` fields** (three named strategists, lines
  106-108). They are data that prints, beside the anchor each one tests, and
  `validate_rates_anchors` pins them. Changing what prints is a rendering change,
  not a comment.
- **`config/crypto_basket.yaml:374`, VVV's thesis** (it names the founder). The thesis is a verbatim quotation of the filed basket document, which `validate_crypto_basket` holds word for word. The strip changed it, and CI round 1 caught it; it is restored in the round-1 fix. Filed text stays verbatim.
- **`altdata/report/`**, the vendored Alternative Asset content (officials, founders
  and analysts in its narrative prose). It is content, not a pipeline, and nothing
  imports it.
- **`tests/fixtures/`** (fixture people such as "Jane Fixture").

## The gates run locally on the stitched tree

| Gate | Result | Why it was run |
|---|---|---|
| `validate_b59` | 83/0 | the three stack conflicts (b59's hooks) |
| `validate_6f_calibration` | 15/0 (again after step 1c: passed) | the three stack conflicts (a63's hooks) |
| `validate_stack` | 84/0 | `daily_cascade/stack.py` |
| `validate_weekly_stack` | 83/0 | `daily_cascade/weekly_stack.py` |
| `validate_stack_cadence` | 104/0 | the stack at every cadence |
| `validate_audit_3a` | 88/0 | CLAUDE.md's count (again after the strip: 88/0) |
| `check_registry` | OK | the registries' clean unions; the strip's registry text |
| `check_master_guide`, `check_library` | 0/0; 0 failures, 0 warnings | the guide's rebuilt HTML |
| `validate_narratives` | 103/0 | the strip (`config/narratives.yaml`) |
| `validate_by_hand_audit` | 17/0 | the strip (its kept quotation) |
| `validate_rates_anchors` | 23/0 | the strip (`config/rates_anchors.yaml`) |
| `validate_ledgers_b6`, `validate_st_r4_t1b` | 41/0, 61/0 | the strip (`st_r4_19b`, `batch5_tranche_1b`) |
| `validate_security_master` | 102/0 | the strip (its comments, its message) |
| `validate_st_t5_render` | 46/0 | its name guard, after the strip |
| `validate_digital_addendum` | 98/0 | the strip (the appendix line and its pin) |
| `validate_secondary_notes` | 88/0 | the strip (a message) |
| `validate_batch15_1` | 69/1 | its name guard passes. The one failure is local only, as in chain-6: the Batch 15 order is held at its SHA-256, the laptop's checkout converts it to CRLF, and CI reads the LF bytes |

The Monthly's and the Weekly's full gates (`validate_monthly_stack`, `validate_monthly`, `validate_weekly_complete`) and everything else are left to CI.

## The CI rounds

| Round | Run | On | Result |
|---|---|---|---|
| 1 | 40132670483 | `bd6a307` | **Red, one gate:** `validate_crypto_basket` (92/1). The strip had edited VVV's thesis, a verbatim quotation of the filed basket document. Fixed in the next commit by restoring the line; 93/0 locally. Every other job passed |
| 2 | recorded once read | | |

## The box sheet

`docs/briefs/chain-7-box-sheet.md`: chain-6's sheet in full (Part I, steps 1-8), then the later branches' box commands in the order they run (Part II, steps 9-15). Part II covers:
- what arrives by itself;
- QAI's backfill (dry run first) and the ProShares pull (a61);
- a62's read-only tranche-0 checks, then its object printed but not stored, then the re-backfill under method-11, which offers no dry run;
- a63's first calibration read, `python -m altdata.state_calibration show` (read-only, after the re-backfill);
- b59's hypothesis registration, then its GDELT, NOAA and Hugging Face pulls and histories (dry runs first) and its reads;
- D15's box edition, written outside the checkout.

Each step carries its expected output.

## Needs you (at most five)

1. **The post-Monthly pull request:** yes or no to opening chain-7 into main after the 1 Nov Monthly, once a61b has merged (27 Oct), chain-7 has taken main and its CI is green?
2. **The box sheet:** yes or no to running it in its order after that merge, Part II's re-backfill (step 11) before the first calibration read (step 12)?
3. **D28's line:** keep the eponyms as they are (datasets, models and statistics named for a person: Wilson, ACM, Sahm, Amihud, the Warsh matrix, Ken French, Damodaran, Shiller, Yardeni)? And should the three strategists' names that print as `config/rates_anchors.yaml`'s `voice:` fields become outlets (as D5 ruled for the voices)? That is a rendering change, with its gate.
4. **`altdata/report/`**, the vendored Alternative Asset content, names officials, founders and analysts in its prose. Leave it as content, or strip it too?
5. **chain-7 taking main after a61b:** a62's notes list a61b's files as shared (`member_overrides` beside `market_state_barred`, and both `resolve_registry` blocks). Yes or no to resolving them as unions when chain-7 takes main?
