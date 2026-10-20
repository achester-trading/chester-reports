STITCH IN PROGRESS: pushed, CI pending (this line becomes STITCH COMPLETE when CI is green)

# chain-3: the third chain stitched into one branch (session B, 19-20 Oct 2026)

**What it is.** One branch, `chain-3`, carrying the third chain on top of `master-guide`, so it merges as ONE pull request (chain-3 into main). It also carries the rulings of 19 Oct 15:59 ET ("accept all", decisions 1 to 19) that concern its branches (R1 to R17; R9 and R10 are session A's, on `a50-dealer-store`, and are not built here), and the Master Guide refreshed to "as built".

**All five branches are in.** `a49-secondary-notes` was final at `0d22352` (the commit that fills its notes' CI table green: run 39314100481, 131/131) when its step came, and was still `0d22352` when checked again before Part 4.

**How it was made.** `friday-stitching-notes.md` ("How it was done", with its Master Guide refresh line) and `chain-2-stitch-notes.md`:
- merges only, one `--no-ff` merge commit per tip, in the paste's order, each tip named; no rebase, squash or force-push, and nothing merged to main;
- conflicts resolved by keeping both sides;
- `metrics_registry.yaml` spliced, not hunk-resolved: at every merge that touched it, each side's additions sat at a different anchor and as whole blocks, so git's merge was already the splice (checked hunk by hunk below), and the duplicate-key sweep found nothing;
- the gate count recomputed once, at the end, from the merged Makefile;
- after each merge, the method's gates, one at a time.

Branch-only: I pushed `chain-3` and nothing else, ran nothing on the box, and enabled, started or restarted no unit. I read session A's branches (`a48-batch11`, `a49-secondary-notes`) and merged them; I pushed to neither.

## The order, as merged

**Base:** `master-guide` at `f1ccfb2`. `master-guide` had **not** merged to main when the stitch began (main was `de0c027`; `master-guide` is not its ancestor), so the base is `master-guide`'s tip, not main's. Every ref was fetched at 17:35 ET on 19 Oct.

| Step | Branch | Tip merged | Carries | Merge commit | Files resolved |
|---|---|---|---|---|---|
| 1 | library-draft-3 | `6a561e5` (its final tip; not yet an ancestor: one commit, its notes) | — | `c154180` | none (clean) |
| 2 | a48-batch11 | `c646aae` | a47-chain3 (`ebd10c7`) | `8536e54` | CLAUDE.md (the count line) |
| 3 | b45-chain3 | `3428513` | alpha-lab-4 (`393b9de`) | `3226edd` | CLAUDE.md (the count line) |
| 4 | library-st-l | `f471713` | — | `587567b` | none (clean) |
| 5 | a49-secondary-notes | `0d22352` (final) | a47-chain3, a48-batch11 | `00e1a8f` | CLAUDE.md (the count line) |

## Every conflict and its resolution

**Textual conflicts: one, three times.** CLAUDE.md's gate-count line, at steps 2, 3 and 5: each branch had added gates on its own count. Each time I kept the line as it stood and recomputed the count once at the end (below).

**The files the paste expected to meet, and what happened to each.** Git merged them without a conflict. I checked each against its merge base, because a clean textual merge can still lose a line or interleave a block:

| File | Where the lines met | Resolution |
|---|---|---|
| `metrics_registry.yaml` | Step 3: b45-chain3 added the four `btcdata.*` entries as one block at line 13,821; my side's additions (a47/a48's) sat at 3,855, 6,556 and the `families`, `series_kinds` and `reserved` maps. Step 5: a49 added at 3,855, `bulk_imports` and `reserved`; b45's block sat at 13,912 | Every addition is a whole block at its own anchor, so git's result is the splice. The duplicate-key sweep over the registries and `config/*.yaml` found nothing (82, then 85 files) |
| `config/catalogue_commands.yaml` | Steps 3 and 5 | Both sides' command lines kept, at their own anchors |
| `docs/signal-triage-register.md`'s header | Step 3 | b45's two lines and a48's one, all kept |
| `tools/validate_audit_3a.py`'s count plant | Step 5: a49 extended `NEW_KEY_BLOCKS`; my side changed group F | Both kept; the plant reads the recomputed count (88/0) |
| `Makefile` | Steps 2 to 5 | Every gate line kept: `validate_a47_chain3`, `validate_a48_batch11`, `validate_b45_chain3`, `validate_alpha_lab_4`, `validate_library_st_l`, `validate_secondary_notes` |
| `altdata/crypto_blocks.py`, `config/crypto_sources.yaml` | Step 3 | Both sides' functions and keys kept |
| `source_registry.yaml` | Step 5 | Both sides' sources kept, at their own anchors |
| `scripts/check_heartbeat_cron.sh` | Steps 4 and 5 | Both kept |
| `stack_render.py` and `readability.py`'s footer line; `docs/change-orders.md` (A49's index) | — | No other branch changed them against the base, so nothing met |

**A branch copy with old text.** `library-st-l` still carries the merge base's `docs/briefs/a43-render-notes.md`, with a vendor figure that a48's D2 had removed. The branch never changed the file, so the merge kept HEAD's redacted text; I checked it after step 4.

## The rulings as applied (19 Oct 2026, 15:59 ET), by commit

Each is its own commit on chain-3. R9 and R10 are session A's, on `a50-dealer-store`, and are not built here.

| R | Concerns | Commit | What changed |
|---|---|---|---|
| R1 | a48-batch11 (its needs-you 1) | `21f5f77` | `.claude/settings.json`'s Bash deny gains the five literal names in its `Bash(*NAME*)` form; `tools/validate_deploy.py`'s MUST_DENY gains a shape for each (19 secret shapes denied; 154/0); CLAUDE.md's deny table names them. **The settings edit is a laptop permission change and was presented for your approval at the laptop** |
| R2 | a48-batch11 (its needs-you 2: D2 reaches back) | `32d8baa` | "No vendor figure in any committed file", treated file by file; no history rewritten. **Fixtures:** the SPY summary and the 770-strike single-expiry GEX take synthetic values labelled synthetic, in the same shape (spot 750; call gamma under the Black-Scholes peak and put gamma above it; net negative; more call OI than put); the expected-move fixture's spot made synthetic. **Gates:** `validate_a43_render`'s and `validate_dealer_vendor`'s constants recomputed with the assertions unchanged in shape; `validate_opening_setup`'s vendor spot (761.10 to 750.00) and `validate_dealer_block`'s vendor VIX (19.99 to Cboe's published 19.98) replaced. **Docstrings and prose:** `tools/vendor_reconcile.py` loses its figures (and gains `--vendor PATH`, so the box run reads the real response from outside the checkout); `config/flashalpha.yaml`, the registry's prose, `tools/exposure_compute.py`, `tools/cross_check.py`, `TODO.md`. **Ledgers:** `vendor-divergence-notes.md`'s Entry 1 keeps its dates, its agreement words and its verdict, with the dated line "vendor figures removed, 19 Oct 2026, under the standing rule"; both `gex-scale-flashalpha-*` ledgers the same way (in the 9 Oct per-strike table the vendor columns and the two ratio columns are dropped, since with ours they would give the vendor's back; the agreement statistics stay). **Briefs:** `a43-render-notes.md`, `a48-batch11-notes.md`, `a44-opening-setup-notes.md`, `dealer-positioning-audit-2026-10-09.md`, `el-4-6-notes.md`. The full list, and the four files left for you, are under "What stayed out" |
| R3 | a48-batch11 (H6) | `5cf05fa` | Accepted as drafted; recorded in a new section of the signal-triage register, "Rule-31 acceptances outside the SR entries" (the register records rule-31 acceptances as dated lines under its entries; Batch 11's studies have no SR entry) |
| R4 | a48-batch11 (OS-9) | `ec19f6d` | SPX in OS-9's index floor, accepted; the register |
| R5 | a48-batch11 (OS-6) | `a77fc40` | OS-6's FAIL, display only, no rights; the register |
| R6 | a48-batch11 (D4) | `4c00e0f` | D4's agreement tolerances, accepted; the register |
| R7 | b45-chain3 (its needs-you 1) | `8c0b91a` (code), `201ac5f` (record) | The posting templates accepted. **The addition:** `altdata/mechanism_watch.base_rate()` and its clause, wherever a posted story's grade prints (the register's rendered view, in the entries list and the candidate's Grade cell; the Monthly's entries list in `monthly_macro/prl_part.py`): the share of 182-day windows in the stored history in which the linked instrument closed higher, with the window and n, read point in time as of the grade (`posted_at`). No key was added (computed at render, read-only). The fixture is `validate_b45_chain3` group C, on six synthetic closes counted by hand (29/0); `validate_st_t5_render` 46/0. On the fixture it prints: "base rate: NVDA closed higher over 182 days in 75% of 4 windows (starts 2025-01-01 to 2025-07-01; as of 2026-01-15)" |
| R8 | b45-chain3 (engine 7) | `62db9d1` | The seven session-set choices accepted as frozen in its spec; the register. Registering E-7 stays your box command (box sheet B4) |
| R11 | library-st-l | `4d80026` | Accepted as drafted: the twelve appendices and the Digital Assets paragraph, the Warsh matrix's 2.1.5 entry, the five Doctrine #2 proposals, the three ledgers (the cycle table in the acceptances section; SR-20 and SR-24 under their entries) |
| R12 | alpha-lab-4 (the search) | `fa6a883` | No rethink of the dials' history before November; the box's coverage decides. Recorded in the register |
| R13 | master-guide | `0fbdbc7` | The trading track and the library map's grouping, marked accepted |
| R14 | master-guide | `8efa8b8` | Table 8 is the agenda for Doctrine #2 (7-8 Nov), none of its rows ruled; row 3's direction stays the order's |
| R15 | master-guide | `a71e75f` | "planned" accepted as a status word (Table 2 and `chat-tasks.yaml`'s header; `check_master_guide` has no vocabulary list) |
| R16 | master-guide | `98f54cf` | `tools/build_paper_html.py` gains an optional font (`--font`, or `FONT_BY_SOURCE` for an edition that always carries one); the default is unchanged. **Proof:** `earnings-whitepaper.html` rebuilt and compared with the committed edition: git reports no change, and the normalised sha256 is `5175c17d…` on both. The Master Guide's edition uses `Aptos, "Segoe UI", Calibri, Arial, sans-serif` |
| R17 | master-guide (its "not mine to fix" list) | `cd2ba6d` | The nine stale lines, below |

### R17, line by line

| File | Old | New |
|---|---|---|
| CLAUDE.md, the report table | Monthly Macro "**Built** — the only implemented pipeline"; Disruptive Themes, Top & Bottom, Alternative Asset and Daily Cascade "Not yet built" | Monthly Macro "**Built** — the stacked Monthly"; Disruptive Themes "Not built — re-cadenced to the Quarterly Structural, itself not built"; Top & Bottom "Not built — no writer stores `top_bottom.composite` or `.verdict`"; Alternative Asset "**Built, disabled** — the Alternative Assets Quarterly"; Daily Cascade "**Built** — the 07:00 anchor, the 12:30 alert, the 16:45 close, the 09:50 open note and the 21:30 evening note" |
| CLAUDE.md, GeckoTerminal | "reads nothing while GeckoTerminal's robots.txt disallows its API" | "reads GeckoTerminal's documented API under its own published terms (ruling 4 of 17 Oct 2026: robots.txt governs crawlers of pages, not that API)" |
| The Reader's Guide, 10.1 | "forty for the Monthly" | "fifty-five for the Monthly" (config: `reading_targets_minutes.monthly: 55`) |
| The Reader's Guide, 4.6 | "The chart set runs to thirteen" | "The chart set is capped at twelve" (config: `monthly: {words: 10000, charts: 12}`) |
| The Reader's Guide, 2.3 | "…the World Bank's commodity indices, the LBMA gold price, FINRA's…" | the LBMA gold price removed from the list, and one sentence: it is held unlicensed and switched off, its parser kept but unscheduled, and the themes read the COMEX front future |
| The Reader's Guide, the scheduled-tasks claim (it is in Appendix A, not the body's Part 8) | "Defined in `docs/scheduled-tasks.md`:" | "Recorded in the Master Guide's record of the chat-side tasks (`docs/master-guide/chat-tasks.yaml`, the Guide's Table 2); `docs/scheduled-tasks.md` defines those it lists, and not the X digest, its reader triage or the Saturday brief:" |
| The Reader's Guide, its masthead | — | A dated **Errata** line under its Version line (where the paper records its drafts), naming the four corrections and decision 17. Its HTML edition is rebuilt |
| `altdata/sources/yfinance_source.py` | "40 symbols:" | "the basket in config (config/security_master.yaml resolves it, and this map is its seed):" |
| `deploy/systemd/chester-ibkr-sync.timer` | "Bounded to 09:00-17:00 deliberately." | "Bounded to 09:00-17:30 deliberately (09..17:00/30 fires every half hour through 17:30)." A comment only; the schedule is unchanged |
| `docs/alpha-lab.md` | "Four engines are registered … `trend_ts`, `trend_xs`, `pm_futures` and `vrp_dealer`." | "Eleven engines are registered (`config/alpha_engines.yaml`) …", the eleven named |

## Part 3: the Master Guide, as built on chain-3

Commit `e59cb81`. The Guide is "as built on chain-3", as of 20 October 2026, and Landing next holds only what is still on its own branch:
- **Tables 1 and 2:** the open and evening notes carry their unit schedules (Mon-Fri 09:50; Sun-Thu 21:30), enabled by hand; the meme ingest at 21:15; the restore drill removed and noted retired; both FlashAlpha chat tasks retired under D7.
- **Table 4, the cards and Table 6:** the secondary notes' two cards read "built: dry runs until `live_from` 2026-10-26; timers enabled by hand", and their Table 1 rows are required; the anchor's card gains the pre-market line, SPX and SPCX in OS-9, H6 and the crypto paragraph behind its switch (off).
- **Part 4:** Batch 11, D4's flat files, R2's reach-back, the mechanism posting with its base rate, CD-12, engines 6 and 7, grammar v2 and the search.
- **Part 5 and Tables 7a and 7b:** the thirteen new ledgers, each with the verdict it records. The headline counts move from 15 gated verdicts (1 passed, 7 failed, 7 insufficient; 11 accruing) to **21 (1 passed, 12 failed, 8 insufficient; 12 accruing)**: S-2, S-3, OS-6, SN-1 and SN-2 FAIL; OS-9 INSUFFICIENT; H6 accruing.
- **Parts 6 to 9:** the checklist lists both notes; Table 8's rows 3, 15 and 17 say what is built, none ruled; Part 9 names the twelve papers with dated appendices.
- **Landing next:** `a50-dealer-store` only (session A's; R9, R10), labelled, worded from its commit subjects.
- **Figures** 2 (the clock) and 5 regenerated by `tools/figures/master_guide.py`.
- **The HTML edition** rebuilt with R16: its body font is `Aptos, "Segoe UI", Calibri, Arial, sans-serif`.
- `check_master_guide` passes (self-test 12/0; the Guide 0/0); `check_library` 27 papers, 0/0.

Table 8's rows 5, 12 and 13 (heat, net exposure, the 13-week expectancy, Book A alone) still read not built: they are `b48-scoreboard`'s, queued after this stitch.

## The counts, recomputed once

From the merged Makefile at the end: **one hundred and twenty-five code gates (one hundred and twenty-two Python, three shell) and eight data gates**. The six new gates are `validate_a47_chain3`, `validate_a48_batch11`, `validate_b45_chain3`, `validate_alpha_lab_4`, `validate_library_st_l` and `validate_secondary_notes`, on master-guide's 119. CLAUDE.md's count line (commit `d2f506a`) is the only place that prints it, and `validate_audit_3a` holds it (88/0). The branches' other counts (series lists, writers, the basket) did not meet: no two branches changed the same count.

## The gates

Run locally after each merge, one at a time, as the method lists them. Every exit is the gate's own.

| After | Gates | Result |
|---|---|---|
| 2 (a48) | `validate_a47_chain3`, `validate_a48_batch11`, `check_registry`, `validate_prices`, `validate_gates`, `validate_config_refs`, `validate_weekly_stack`, `validate_monthly_stack`, `validate_audit_fixes`; the duplicate-key sweep | all pass |
| 3 (b45) | `validate_b45_chain3`, `validate_alpha_lab_4`, `validate_crypto_sources`, `validate_digital_addendum` (the conflicted crypto files feed them), the method's seven, `validate_audit_3a`; the sweep | all pass except `validate_audit_3a` 87/1: the count line only (119 printed, 123 in the code), expected until the recount |
| 4 (library-st-l) | `validate_library_st_l`, `check_library` (27 papers, 0/0), the method's seven | all pass |
| 5 (a49) | `validate_secondary_notes`, `check_master_guide`, `validate_audit_3a`, `validate_systemd_units`, `validate_deploy`, the method's seven; the sweep | all pass except: `validate_audit_3a` (the count, fixed in `d2f506a`, 88/0), and `check_master_guide`, which fails by design once a49's unit files exist (its rows and cards "ruled, not built" become required, meme-ingest is now 21:15, the drill is retired, thirteen new ledgers are not in Table 7, the clock figure is stale). Part 3 is the fix |
| The rulings | `validate_deploy` 154/0 (R1); `validate_b45_chain3` 29/0, `validate_st_t5_render` 46/0, `check_registry`, `validate_config_refs` 103/0 (R7); `check_library` 0/0 (R17) ; `validate_a43_render` 46/0, `validate_dealer_vendor` 28/0, `validate_opening_setup` 61/0, `validate_dealer_block` 134/0 (R2); `check_master_guide` 0/0 (Part 3) | pass |

Every other gate, and anything that renders a PDF, was left to CI.

## The CI rounds

Round 1: pending.

## What stayed out, and why

- **`a50-dealer-store`** (session A's, with R9 and R10): it is still on its own branch. The Guide's Landing next lists it, labelled.
- **`b48-scoreboard`** (the Card's scoreboard, ruled after this paste): it branches from this stitch's final tip and merges on its own after chain-3.
- **R9 and R10:** session A's, on `a50-dealer-store`; not built here.
- **R2, four files left for you,** because each is a white paper's body (which this paste does not let me edit beyond R17) or your own ruling text or a pinned pre-registration:
  1. `docs/whitepapers/volatility-whitepaper.md` (about line 766) and its HTML: the batch-9 worked example's FlashAlpha macro-block values. Proposed: Cboe's published values, named as such, with a line in the paper's change record.
  2. `docs/whitepapers/systematic-book-whitepaper.md` (about line 307): "both walls matching the vendor exactly" gives the vendor's walls by equality. Proposed: drop "exactly" or the parenthetical.
  3. `docs/change-order-signal-triage-batch-9-2026-10-17.md` line 22: the worked example quotes the vendor's macro block, its fear-and-greed reading and a flip near 7,767. It is your ruling's text. Proposed: a dated note under the example, the ruling's words left alone.
  4. `tests/fixtures/alpha/inbox/hypotheses-2026-10-14.yaml` (lines 13 and 41-42): vendor expected-move and IV figures in a pre-registration marked "never edited", its hash pinned in eight places. Proposed: a superseding batch with the figures in words, registered as superseding.
- **R2, checked and left alone:** the values in `tools/validate_vol_event.py` and `docs/briefs/vol-event-52-notes.md`, and the batch-9 order's 19.98, match Cboe's free daily files; subscription prices in the architecture document, the master schedule, two papers, TODO and `probe_massive.py`; FactSet figures via JPM's free Guide, Inovestor via a public post, LSEG via Topdown Charts (your call whether these count); `tools/structure_compare.py`'s chain IV, which is Yahoo's.
- **Drafts not in R1 to R17:** a47's S-2 and S-3 FAIL verdicts and a49's SN-1 and SN-2 FAIL verdicts, each a rule-31 draft, are not among the rulings this paste applies, so no acceptance is recorded for them.

## Needs you

1. **Approve the settings edit at the laptop** (R1): `.claude/settings.json`'s five new deny entries.
2. **The box sheet:** `docs/briefs/chain-3-box-sheet.md`, for the merge evening.
3. **`live_from`** stays 26 Oct only if chain-3 merges by Thursday 22 Oct; otherwise a session moves it later first (a49's rule).
4. **R2's four files** above: a ruling on each.
5. **The rule-31 drafts this paste did not cover:** S-2 and S-3 (a47), SN-1 and SN-2 (a49), all FAIL; a47's Fear & Greed words and S-3's "May 2026 rush" (decide before D1's box re-run); a49's session-set values and the PPI and retail-sales forms.
6. **The keys for B7 and B8:** `BITCOIN_DATA_API_KEY`, and the two flat-file names, in `.env` by hand.
7. **E-6 and E-7's registrations** (box sheet B3 and B4) are yours, and freeze their choices.
