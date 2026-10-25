# A75: Tuesday's merge night, prepared (session A, 24 Oct 2026, evening)

**What it is.** Tuesday 27 Oct evening, the operator merges `a61b-feed-repair` alone, runs its box sheet, and chain-7 then takes main (D29.1, D31.5). Tonight prepared all three so Tuesday is commands only. No ruling was needed. Branch-only: nothing merged, no pull request opened, the box not touched, no unit, no `.env`, no secret.

## 1. The rulings filed

`docs/briefs/rulings-2026-10-24-evening.md`, D30–D34 with D29.4's closure, copied from the attached file byte for byte (`cmp` identical). One commit, `297e0d92`, on `a61b-feed-repair`, so they reach main on Tuesday.

**The wealth ledger's box edition.** b52's notes name the command (`tools/calibration/st_r6_66c_wealth_effect.py --box --out ~/chester-data/ledgers`, checked against `st7_common.cli`). The copy back is `scp` from the laptop into `docs/ledgers/`. Both are in the box sheet as step M9. No content is invented: the files are committed by a session after the copy.

## 2. The box sheet

`docs/briefs/a61b-box-sheet.md` (`efe02994`), in the house shape of `chain-5-box-sheet.md`. It has **twelve steps**: B1–B2 before the merge, then M1–M10 after it, each with its command, what to expect and when to stop.

| Step | What |
|---|---|
| B1 | the ET clock and last night's backup (the 24 Oct heartbeat read `backup=failed:partial`); stop if not `ok` |
| B2 ⚑ | the EOD log's 12-minute-cap lines; if the cap was hit, D29.2's `fed_funds` line is committed before the merge |
| M1 | the merge on the box; the FRED and yfinance counts (277, 124) |
| M2 | `bash scripts/deploy.sh` from the laptop; exit 0 expected (a61b changes no unit) |
| M3 | MBA and Farside print REFUSED and ask nothing |
| M4 | AERO's labelled break from 21 Oct, dry run first (D29.3) |
| M5 | one FRED series through the repaired fetch |
| M6 | StatCan, rents (Zillow alone), the voices scan's T. Rowe Price |
| M7 | the feed re-run, under the same 12-minute cap |
| M8 | the store check: **about 100 stale, range 80 to 130**; above 130, stop and paste the list |
| M9 | the wealth ledger's box edition, and the copy back |
| M10 | the heartbeat: `feed_stale` (exit 11) should clear |

**Corrected from the notes against the code** (six, tabled at the sheet's end):
- the store is `data/chester.db`, not `~/chester-data/chester.db`;
- the logs are `~/logs/run_eod-YYYY-MM.log`;
- the voices scan's flags belong to its `run` subcommand;
- `edgar_xbrl` has no dry run, so it is left to the 16:10 pass;
- the backup log is daily, `rclone_sync-YYYY-MM-DD.log`;
- the evening note's log step is dropped.

**Not verified:** the exact stale count, which only the box's store gives; and whether DefiLlama's `aero` answers.

## 3. The chain-7 stitch

`chain-7-main` from `a61b-feed-repair` at `efe02994`, with `origin/chain-7` (`62c19b41`) merged in. **Five conflicted files, resolved in one merge commit** (`8ca0836b`), as D31.5 rules:

| File | Resolution |
|---|---|
| `metrics_registry.yaml` | both sections kept: a61b's `member_overrides`, then chain-7's `market_state_barred` |
| `altdata/derived.py` (two hunks) | both `resolve_registry` blocks kept, the member overrides first and the market-state bar after, so an override cannot unset a bar; `DECLARED_STATUSES`/`declared_status()` and `market_state_barred()` both kept |
| `CLAUDE.md` | the gate count from the merged Makefile: **140 code gates (137 Python, 3 shell)**, eight data gates |
| `docs/attention-log.md` | both 24 Oct rows, D1–D27 first; a61b's "D1–D27 are indexed on chain-6" now reads "are the row above" |
| `tools/validate_crypto_sources.py` | chain-7's retired 12-line cap (D19/D20) with a61b's refused Farside render, because Farside is refused once a61b is on main |

**The Security Master renumbering (D28.3)** came in unchanged from chain-7: no conflict touched `config/security_master.yaml`, and `validate_security_master` passes.

**The names (D28, D31.3).** chain-7 had already stripped names from code comments and registry text in its own commit (`80a17937`). D31.3 rules that the analysts' names in `config/rates_anchors.yaml`'s `voice:` fields become outlets. One commit (`27aa84b2`) does it for the two whose outlet is filed in the batch-4 order: "Maxence Visseau" becomes "Arkevium" (§4, line 116), and "Jeremy Courtial (SocGen idea)" becomes "Société Générale (an idea, via a post)" (line 148, "on an idea from Société Générale"). `validate_rates_anchors` keys on the labels and follows them. **"Charles Diebel" is held:** the order cites the post without an outlet, and none was supplied from memory (needs you 2).

**Gates run locally on the stitch:**

| Gate | Result |
|---|---|
| `check_registry` | OK |
| `check_library` | 27 papers, 0 failures, 0 warnings |
| `validate_audit_3a` | 88/0 (the count) |
| `validate_feed_repair` (a61b) | passed |
| `validate_crypto_sources`, `validate_security_master`, `validate_regime`, `validate_digital_addendum` | passed |
| chain-7's added gates: `validate_6f_calibration`, `validate_batch14_b1`, `_b2`, `validate_batch15_2`, `validate_b59` | passed |
| `validate_batch15_1` | 69/1 on the laptop only. The Batch 15 order's hash, from the Windows CRLF checkout (281 lines, 281 bytes); stripped of CRs it hashes to the pin, and the file is byte-identical to chain-7's in git. It passes on Linux CI |
| `validate_rates_anchors`, `validate_no_filler`, `validate_lenses` (after the names) | 23/0, 32/0, passed |

**CI:** queued, run 40154912529 (at `27aa84b2`).

## 4. The figure previews

The five Evidence and Inference SVGs from `origin/library-ei-figures` were rendered to PNG by headless Edge, at twice scale, into `C:\Users\arich\projects\figure-previews\` (not in the repo). The render shows real layout faults for the branch's next paste:
- the foot lines of Figures 1, 3, 4 and 5 run past the right edge;
- Figure 1's n 150 and n 200 labels overlap;
- Figure 3's weak-prior label sits on its curve;
- Figure 5's legend is clipped;
- each axis title touches its foot line.

The curves and the numbers read as intended.

## CI

| Branch | Tip | Run |
|---|---|---|
| `a61b-feed-repair` | this notes commit | read once after the push (the report) |
| `chain-7-main` | `27aa84b2` | **CI queued, run 40154912529** |

## Needs you (at most five)

1. **Tuesday:** merge `a61b-feed-repair` alone inside 17:20–23:30 ET, then the box sheet in its order. Yes / no.
2. **Charles Diebel's `voice:` field:** name his outlet, or label the line by the post ("a rates strategist's post, 6 Oct 2026")? Until then his name stays in `config/rates_anchors.yaml` on `chain-7-main`.
3. **The figure faults:** fix them on `library-ei-figures` in its next paste (layout only, no number changes). Yes / no.
4. **The attention log:** D30–D34 have no row yet. Add one on `chain-7-main` before its pull request? Yes / no.
