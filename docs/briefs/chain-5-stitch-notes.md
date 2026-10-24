STITCH PENDING (CI round 1 not yet read)

# chain-5: the fifth chain stitched into one branch (session B, 23 Oct 2026)

**What it is.** One branch, `chain-5`, carrying every finished branch on top of main after chain-3's merge, so it merges as ONE pull request (chain-5 into main) on the evening of Friday 23 Oct. The secondary notes' `live_from` (Monday 26 Oct) and the Monthly's last dry run (Wednesday 28 Oct) then both read everything on main. It carries:
- `chain-4` whole (a50-dealer-store, b48-scoreboard, a52-doctrine-2-pack, its five fixes; never merged to main on its own);
- `a54-relative-volume` (Batch 13 item 61);
- `a55-box-fixes` (A55 and its round 2, the FOMC history);
- `b51-registry-html` (the store check and the HTML editions);
- `a56-batch14-a1` (Batch 14 filed; items 64, 69, 70);
- `b52-batch14-a2` (items 63, 66).

On top of those it adds two fixes where the lines met, the recount, the Master Guide refreshed to "as built", and one box sheet (`docs/briefs/chain-5-box-sheet.md`).

**How it was made.** The method of `friday-stitching-notes.md` ("How it was done") and `chain-4-stitch-notes.md`:
- merges only, one `--no-ff` merge commit per tip, in the paste's order, each with the message "Merge <branch> into chain-5 (fifth chain, 23 Oct)"; no rebase, squash or force-push, and nothing merged to main;
- conflicts resolved by keeping both sides;
- `metrics_registry.yaml` spliced, not hunk-resolved (below);
- the gate count recounted once, at the end, from the merged Makefile;
- after each merge, the method's gates, one at a time, and every gate a conflicted file feeds. `validate_monthly_stack` and everything that renders a PDF were left to CI, as the paste's memory rule asks.

**Branch-only.** I pushed `chain-5` and nothing else, ran nothing on the box, and enabled, started or restarted no unit. I read session A's branches (`a54-relative-volume`, `a55-box-fixes`, `a56-batch14-a1`) and merged them; I pushed to none of them, nor to chain-4, b51 or b52. chester-meme was not opened.

## The order, as merged

**Base:** main at `f9ec9e3` ("Merge pull request #40 from achester-trading/chain-3"); main has not moved since chain-3's merge. Every ref was fetched at 19:26 ET on 23 Oct and fetched again at 20:10 ET; no tip moved between the two. Every branch was cut from `f9ec9e3`, so each merge's base is main's tip.

| Step | Branch | Tip merged | Its own CI | Merge commit | Files resolved |
|---|---|---|---|---|---|
| 1 | chain-4 | `4b096bb` (STITCH COMPLETE) | green, run 39541999251, 138/138 | `f07bd65` | none: main is chain-4's base, so the merge's tree is chain-4's |
| 2 | a54-relative-volume | `751902a` (A54's notes' CI table) | green, run 39523934033 (and 39522896623, 136/136) | `ec75fae` | CLAUDE.md, Makefile, `docs/change-orders.md`, the signal-triage register's header, `docs/html/master-guide.html` |
| 3 | a55-box-fixes | `b377748` (round 2, the FOMC history) | green, run 39547686881 on its tip | `4a59d1b` | CLAUDE.md, Makefile |
| 4 | b51-registry-html | `fc00a8b` (b51's notes' CI table) | green, run 39545588415 (and 39543993552, 136/136) | `c6f5c72` | CLAUDE.md, Makefile, `docs/html/master-guide.html` |
| 5 | a56-batch14-a1 | `a5a25a1` (Parts 1–4 and the notes) | **green, run 39550357046, but never written into a56's notes** (its CI table reads "(in the closing message)") | `458c80c` | CLAUDE.md, Makefile, `config/narratives.yaml`, the signal-triage register's header, `tools/validate_narratives.py`; and `docs/change-orders.md`'s row order |
| 6 | b52-batch14-a2 | `c5c6105` (B52's notes) | **red, never green**: runs 39547867174 and 39548006767 failed on `validate_numeral_audit` and `validate_enforce` (fix 1) | `57dd60c` | CLAUDE.md, Makefile, `config/security_master.yaml`, the architecture document, `docs/dated-appendix-queue.md`, `docs/html/master-guide.html`, `docs/master-guide.md`, `metrics_registry.yaml`, `monthly_macro/stack.py`, `tools/validate_audit_3a.py`, `tools/validate_prices.py` |

b52's notes record their CI table as "—": its two runs were never read back into the branch. chain-5's CI is the test of all six.

## Every conflict and its resolution

| Step | File | Where the lines met | Resolution |
|---|---|---|---|
| 2, 3, 4, 5, 6 | CLAUDE.md | the gate-count line: chain-4's 128 against each branch's 126 (all counted on main's 125) | Kept chain-4's line each time; recounted once at the end (133) |
| 2, 3, 4, 5, 6 | Makefile | each branch's one gate line at the same anchor, after `validate_batch12` | Every line kept, in merge order: `validate_batch13`, `validate_a55_box_fixes`, `validate_b51_registry_html`, `validate_batch14_a1`, `validate_batch14_a2` |
| 2 | `docs/change-orders.md` | Batch 12's row (chain-4) and Batch 13's (a54) | Both, 12 then 13 |
| 2, 5 | the signal-triage register's header | the "Batch orders" cell: chain-4 added Batch 12, a54 Batch 13, a56 Batch 14, each as the cell's last "and [n]" | One cell: "… [11] (…), [12] (…), [13] (…) and [14] (…)", each link with its own parenthesis as its branch wrote it |
| 5 | `docs/change-orders.md` | merged clean, but a56 put Batch 14's row after Batch 11 (main's last) | Moved after Batch 13's, so the index stays in date order. Row text unchanged |
| 5 | `config/narratives.yaml` | chain-4's two proposals (a53's pair) and a56's `gse_mbs_purchase_floor`, at the same anchor | All three kept, chain-4's then a56's |
| 5 | `tools/validate_narratives.py` | the committed-proposals pin: five (chain-4) and four (a56) | **Six**, with both histories in its comment, as a56's notes asked ("chain-4 adds two, so the pin becomes six"); 103/0 |
| 6 | CLAUDE.md | the layout's basket line: 116 (KRE) and 123 (b52's eight) | **124**; and b51's paragraph and b52's paragraph, both kept |
| 6 | `config/security_master.yaml` | `next_id` 205 and 213; SM00204 (KRE) and SM00205–SM00212 (b52's eight) | `next_id` **213**; every entry kept. b52 had left SM00204 to KRE, so no id collided |
| 6 | the architecture document | its store box: 116 symbols (a53) and 123 (b52) | 277 FRED and **124** symbols, naming chain-5 and b52's eight |
| 6 | `metrics_registry.yaml` | the basket blocks' `expected_members`: 116/123 (`market_closes` and the bulk basket) and 86/93 (the volume shares) | **The splice:** b52 adds no block, only these three counts, so no field could interleave. Each line is chain-4's with the union count, **124, 94 and 124**, and b52's clause put first. The duplicate-key sweep found nothing |
| 6 | `tools/validate_prices.py` | the symbol pin (116, 123) and the volume-unit pin (96, 103) | **124** and **104**, both clauses kept; 101/0 |
| 6 | `tools/validate_audit_3a.py` | `NEW_BLOCK_MEMBERS`: KRE's four members and the eight symbols' 32 | All kept |
| 6 | `monthly_macro/stack.py` | Plumbing: a53's bank-stress sub-section and b52's loosening leg; the slow layers: a56's Batch 14 sub-section and b52's capex-chain exhibit | All four hooks kept, chain-4's or a56's first, then b52's |
| 6 | `docs/master-guide.md` | Table 7a: ST-R6.59c (chain-4) and ST-R6.66c (b52) | Both rows |
| 6 | `docs/dated-appendix-queue.md` | a56's three entries and b52's one, both appended at the end | All four, a56's then b52's |
| 2, 4, 6 | `docs/html/master-guide.html` | the build output | Never hunk-resolved: rebuilt from the merged `.md` with the merged builder inside each merge commit, and again in Part 4 |

**The files the paste expected to meet, and what happened to each.**

| File | Result |
|---|---|
| `config/publication_lags.yaml` against a56's and b52's new keys | No textual conflict (only b51 touches it). Read against the new keys: fix 2 |
| The dated appendix queue | Step 6, above |
| The claims file (`config/claims.yaml`) | Merged clean: only a55 changed it (the FOMC history) |
| The Master Guide | Steps 2, 4 and 6 (the HTML), step 6 (Table 7a); refreshed in Part 4 |
| `docs/change-orders.md`, the register's header | Steps 2 and 5, above |
| The other HTML editions | b51 rebuilt all 28 with its new builder, and they merged clean. After step 4 every edition was rebuilt once more with the merged builder (`bash scripts/make.sh html`): **no file changed**, so every edition was current |

## The fixes, by commit

| Fix | Commit | What changed |
|---|---|---|
| 1 | `52c54a2` | **b52's two red gates** (its own CI, runs 39547867174 and 39548006767). `altdata/transmission.py` `net_lines` wrote its band ordinals by hand (`{lo:.0f}th`), which `validate_numeral_audit`'s source check refuses; they now go through `numeral_audit.ordinal()`, the one ordinal helper, so "20th" and "80th" print as before (172/0). `validate_enforce`'s "a name the store does not carry has no beta" fixture used AMD as its outside-the-basket name, and b52 put AMD in the basket; it now uses INTC, with the history in its comment (49/0). Neither is a change of rule |
| 2 | `86589f7` | **The publication lags where the new keys meet b51's rule.** b51's notes asked that, once chain-4 sat beside the file, H.8's weekly deposits and H.4.1's two credit lines gain a family, and the paste asks the same for a56's and b52's new keys. Two families are added, each session-set with its reason (below). H.4.1's lines are Wednesday levels released the next day, so the weekly allowance holds them and no family is added. b52's eight proxies are daily closes, and b52's notes say the daily allowance holds them. CLAUDE.md's b51 paragraph names both families. `validate_b51_registry_html` 0 failures, `validate_derived` 0 failures |
| The recount | `33d6b39` | CLAUDE.md: **one hundred and thirty-three code gates (one hundred and thirty Python, three shell)** and eight data gates (below) |
| Part 4 | `d002357` | The Master Guide, as built on chain-5 (below) |

### Fix 2, the two lag families

| Family | Matches | Source | Its real publication lag | Cadence allowance | Lag added | Allowance | Bound |
|---|---|---|---|---|---|---|---|
| `fred_h8_weekly` | `DPSSCBW027SBOG`, `DPSLCBW027SBOG` (`fred.h8_dep_small`, `fred.h8_dep_large`, chain-4's a53) | Fed H.8, through FRED | Dated the week's Wednesday, released the Friday of the following week. Just before the next release the newest week is sixteen days old, about 12 sessions | 8 (weekly) | 5 (4, and one for a holiday) | 13 | 6 |
| `shiller_housing` | `shiller.real_home_price` (a56) | Shiller's `Fig3-1.xls`, after the S&P CoreLogic Case-Shiller national index | Published on the last Tuesday of the month, two months after it; the 6 Oct 2026 file carried July 2026 (a56's Part 0). A month dated its first day is about three months old when the sheet updates and about four before the next, near 88 sessions | 32 (monthly) | 56 | 88 | 60 |

- **H.8's lag is not b51's estimate.** b51's notes said "about 7 sessions over the weekly allowance". From the release calendar the worst case is 12 sessions against the weekly allowance's 8, so the lag is 4, plus one for a holiday. A lag is the source's delay, never a number chosen to clear a key. Confirm or replace it (needs-you 7).
- **Checked by computing the allowance** (`derived.staleness_allowance_of` over the resolved registry):
  - `fred.h8_dep_small` and `fred.h8_dep_large` read 13 ("… plus 5 sessions' publication lag (fred_h8_weekly)");
  - `shiller.real_home_price` reads 88;
  - `fred.dw_primary_credit` and `fred.fed_other_credit` read 8, unchanged;
  - `fred.fhlb_advances` and `fred.hh_equity_share` already read 180, through `z1_quarterly`.

## Part 4: the Master Guide, as built on chain-5

Commit `d002357`. As of 23 October 2026, "as built on chain-5".
- **Landing next:** every item chain-5 carries reads as built, each with where it is described, and no branch waits. The table has six rows: chain-4 whole, a54, a55, b51, a56 and b52.
- **Counts (Part 0 and Part 5):** **twenty-four gated verdicts (1 passed, 14 failed, 9 insufficient; 12 accruing)**.
  - ST-R6.66c's FAIL (n 65) joins the failed, as b52's needs-you 5 asked of the next chain refresh.
  - OS-12c's INSUFFICIENT (n 0) joins the insufficient. a54's ledger is pre-registered with a pass rule, so it counts as gated.
- **Table 7b** gains three rows:
  - ST-R6.66c and the net-transmission line (failed, report only);
  - OS-12b, the relative-volume flag (insufficient);
  - Batch 14's report-only readings (untested), with their listed gaps.
- **The cards:**
  - the anchor: OS-9's "volume flag yesterday";
  - the close: the relative-volume detail table and the next close's OI-build line;
  - the Weekly: the week's flag counts and OS-12c's ledger to date;
  - the Monthly: Batch 14's lines in plumbing and rates, what's priced and the slow layers.
- **Part 4.1:**
  - the FRED history's windows;
  - the FOMC history and its monthly audit;
  - the BLS feeds' contact;
  - Shiller's housing sheet;
  - the store check's clock and lags.
- **Part 4.2:** 124 symbols, and the flat-file volume (OS-12d).
- **Part 0:** the basket is 124.
- **The calendar's 28 October row:** chain-5 on main before it.
- **Tables 1, 2 and 9 are unchanged.** No timer and no chat task changed after chain-4, and no paper was added, renumbered or resized.
- **Figures 2 and 5:** regenerated, no change.
- **The HTML edition:** rebuilt.
- **Checks:** `check_master_guide` 0/0; `check_library` 27 papers, 0/0.

## The counts, recomputed once

From the merged Makefile at the end: **one hundred and thirty-three code gates (one hundred and thirty Python, three shell) and eight data gates.**
- **Python:** `PY_VALIDATORS` lists 129, plus the smoke test.
- **Shell:** `SH_VALIDATORS` lists three. `DATA_GATES` lists eight.
- **The eight new gates** on main's 125:
  - chain-4's `validate_a50_dealer_store`, `validate_b48_scoreboard` and `validate_batch12`;
  - a54's `validate_batch13`;
  - a55's `validate_a55_box_fixes`;
  - b51's `validate_b51_registry_html`;
  - a56's `validate_batch14_a1`;
  - b52's `validate_batch14_a2`.

CLAUDE.md's count line (`33d6b39`) is the only place that prints the count, and `validate_audit_3a` holds it (0 failures after the recount).

The other counts that met:
- **The basket: 124 symbols.** That is main's 115, plus KRE (chain-4's a53), plus b52's eight.
  - Volume units are 104 and the volume-shares block 94.
  - The counts appear in CLAUDE.md, the architecture document, `metrics_registry.yaml`, `validate_prices` and the Guide.
  - b52's notes predicted exactly these unions.
- **`FRED_PULL_SERIES`: 277**, unchanged since chain-4. a56 and b52 add no FRED series; their FRED inputs were already pulled.
- **The Security Master:** `next_id` 213 (KRE SM00204; SM00205–SM00212).
- **The narratives' committed proposals:** six.

## The gates

Run locally after each merge, one at a time, as the method lists them. Every exit is the gate's own; "pass" is the gate's own VALIDATION PASSED with exit 0.

| After | Gates | Result |
|---|---|---|
| 1 (chain-4) | none: the merge's tree is chain-4's tip's exactly (`git diff origin/chain-4 HEAD` empty), which CI ran green in 138/138 jobs | — |
| 2 (a54) | `validate_batch13`, `check_registry`, `validate_prices`, `validate_gates`, `validate_config_refs`, `validate_weekly_stack`, `validate_audit_fixes` 103/0, `validate_audit_3a`, `check_master_guide`, `check_library` (27, 0/0); the duplicate-key sweep (87 files, 0) | all pass except `validate_audit_3a` 87/1: the count line only (128 printed, 129 in the code), expected until the recount |
| 3 (a55) | `validate_a55_box_fixes`, `validate_fred_history`, `validate_secrets`, `validate_secondary_notes`, `validate_alpha_lab_3` (the gates its files feed), the method's seven less the Monthly stack; the sweep (87, 0) | all pass |
| 4 (b51) | `validate_b51_registry_html`, `validate_derived`, `validate_lenses`, the method's seven less the Monthly stack, `check_master_guide`, `check_library`, `validate_batch13`, `validate_a55_box_fixes`; the sweep (88, 0) | all pass |
| 5 (a56) | `validate_batch14_a1`, `validate_narratives` (its conflict), `validate_st_r5_rates`, `validate_st_r4_t1`, `validate_official_sources`, `validate_b51_registry_html`, the method's seven less the Monthly stack, `check_library`; the sweep (88, 0) | all pass |
| 6 (b52) | `validate_batch14_a2`, `validate_batch14_a1`, `validate_security_master`, `validate_prices`, `validate_audit_3a`, `validate_batch12`, `validate_voices`, `validate_numeral_audit`, `validate_enforce`, the method's seven less the Monthly stack, `check_master_guide`, `check_library`; the sweep (90, 0) | all pass except `validate_audit_3a` (the count line: 128 printed, 133 in the code) and **`validate_numeral_audit` 171/1 and `validate_enforce` 48/1, b52's own two red gates** (fix 1) |
| Fix 1 | `validate_enforce`, `validate_numeral_audit`, `validate_batch14_a2` | pass |
| Fix 2 | `validate_b51_registry_html`, `validate_derived`, `validate_batch12`, `validate_batch14_a1`, `validate_config_refs`; the sweep (90, 0) | pass |
| The recount | `validate_audit_3a` | pass |
| Part 4 | `check_master_guide`, `check_library` | pass |

Every other gate was left to CI: `validate_monthly_stack`, everything that renders a PDF, and the heartbeat's shell gates. Gates ran with `PYTHONIOENCODING=utf-8`, the laptop's cp1252 console quirk noted at chain-4. No gate was killed and no low-memory warning appeared.

## The CI rounds

| Round | Run | On | Result |
|---|---|---|---|
| 1 | 40043217809 | `33d6b39` (the merges, fixes 1 and 2, the recount) | (pending) |

## What stayed out, and why

- **Nothing of the six branches.** All six are in, at the tips named.
- **Session A's and B's needs-you items not ruled in this paste** are listed below, unchanged. This paste applies only the fixes above.
- **The paths with the operator's Windows user folder** in older notes (b52's notes name the order's Downloads path, as several earlier notes do). They are paths, not a person's name in prose, so they were left alone; say if they should be scrubbed.
- **a56's and b52's CI tables** stay as their branches left them. This file records both runs (above).

## Needs you

1. **The box sheet,** `docs/briefs/chain-5-box-sheet.md`, for the merge evening and the weekend. It carries chain-4's sheet in full, T1 first (enable the evening note's timer once the fixed unit is copied), then a55's, b51's, a56's, b52's and a54's steps, dry runs first.
2. **The pull request** (base main, compare chain-5): open it once CI is green, merge it before 23:30 ET. It replaces chain-4's.
3. **b51's four open items**, as b51 wrote them:
   1. "**The registry check's re-run** on the box after the merge (the command above). Paste back the stale list. Each key still stale is either a family to add with its real lag, or a stopped writer to fix; neither is an allowance to widen."
   2. "**The synthetic rows:** quarantine them (a registry line, nothing deleted) or remove them (`altdata.purge_synthetic`, dry run then apply with a new backup, yours on the box)."
   3. "**`calc.infl_vol`:** leave it unwritten until a 24-month window clears October 2025 (November 2027), or rule a bridge for a missing print. For example, a two-month change annualised over its own span, counted as one observation. That is a change to SR-9's regime variable and its pinned gap rule."
   4. "**The publication lags:** confirm or replace each session-set value in the table."
4. **a55's alias note**, as a55 wrote it: "**The alias address:** put it in `.env` as `CHESTER_SEC_CONTACT` (the one key; the senders are listed above). Name only, never in a file."
5. **a55's other items:**
   - `altdata/releases.py`'s BLS release files may answer with the contact. Move them to the contact host in a later order, or not.
   - The 23 Mar 2020 notation vote: in or out.
6. **a56's items:**
   - the X account for the X pilot's seed list (tagged promoter);
   - the newsletter writer in the voices register, which the no-names rule keeps out;
   - F6's primary check, which has no FHFA release;
   - the session-set values;
   - the proposal `gse_mbs_purchase_floor`: confirm or reject after the seed.
7. **Fix 2's two lags** (`fred_h8_weekly` 5, `shiller_housing` 56): confirm or replace, with b51's table.
8. **b52's items:**
   - ST-R6.66c's FAIL (n 65), a rule-31 draft for your accept-all;
   - the session-set values (the proxies, and the between-release mark that stands in for ICI);
   - the Book B scanner's universe, which takes in the eight proxies once backfilled;
   - the JDI Research feed: confirm, or `enabled: false`.
9. **a54's items:**
   - the session-set values, with the threshold reviewed after 30 days (from 2026-11-19);
   - OS-12c's box edition, once 20 capture sessions a name are stored.
10. **chain-4's open items** (its notes' needs-you 3 to 6) stand as written there:
    - fix 4's archive file;
    - A51's values;
    - a53's KRE implied vol, ICI, values, FAIL and narrative pair;
    - a52's pack before 7 November.
