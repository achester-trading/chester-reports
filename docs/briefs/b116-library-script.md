# B116: the library PRs, rehearsed a second time (for Thursday 5 Nov 2026)

Paste B116 (`docs/pastes/B116.md`), 2 Nov 2026.

**The branch.** `b116-library-rehearsal-2` is a throwaway: it is never merged, and
it is deleted after the real PRs. No existing branch was touched.

**The base.** `origin/a105-merge-week-rehearsal-2` at `b8023fba`: the merge week
as rehearsed through A106.

**Step 0, added.** The paste says the base already carries B110's Appendix C in
chain-8's copy of Foundations. It did not: `faac8c48` (B110) came after A105 took
chain-8 at `4e6814df`, so Foundations on the base still read A, B. Chain-8 at its
tip carries only B110's two commits beyond the base, so step 0 merges
`origin/b86-chain-8-assembly` (`faac8c48`), as the real week will when chain-8
merges at its tip. It merged without conflict, and Foundations then read A, C.

**The branch names.** `docs/briefs/b88-notes.md` does not exist on
`origin/b88-library-rehearsal`; the names come from `b88-library-notes.md`. The
order is the paste's (D48 and B93's memo). It differs from B88's in one place:
XXIX now merges before XXX, and XXX is last.

## The order, with each branch's tip

| Step | Branch | Tip | Merge commit |
|---|---|---|---|
| 0 | `b86-chain-8-assembly` (B110) | `faac8c48` | `474184f6` |
| 1 | `library-xxvii` | `360c13c4` | `fc3c662e` |
| 2 | `library-phase-3a` | `de217862` | `72487add` |
| 3 | `library-xxxi` | `d6fd9181` | `5cc836f0` |
| 4 | `library-xxxii` | `1d412b95` | `a5e2d622` |
| 5 | `library-ei-figures` | `6e6aa1cd` | `872bf170` |
| 6 | `library-xxix` (B94's cleared marks) | `c148862b` | `589c8132` |
| 7 | `library-xxx` | `50e26cf1` | `2454bfb0` |

## Each merge: conflicts and resolutions

**Generated files.** Every Fig 5 and `docs/html/` conflict was resolved the same
way: our side was taken and then regenerated from the merged sources.
- `python tools/figures/master_guide.py`;
- `python tools/build_paper_html.py` for each paper and the Guide;
- `python tools/appendix_queue_index.py --write`.

After every merge, `master_guide.py --check` was clean, and the queue index
matched its 7 entry files.

| Step | File | Hunk | Resolution (side) |
|---|---|---|---|
| 1 | `docs/html/master-guide.html` | generated | regenerated |
| 2 | `docs/whitepapers/disruptive-themes-whitepaper.md` | **the end-of-file append (the 2 Nov rule)**. The base section is empty; ours holds A68's Appendix C (42 lines), theirs the library's Appendix B (187 lines) | **theirs, then ours.** The result is library-phase-3a's file byte for byte, with A68's Appendix C appended |
| 2 | `docs/white-paper-library-guide.md` | the Macro rows: ours adds XXVII's row, theirs restructures I and II | ours' new row (XXVII), then theirs (I and II at v1.1) |
| 2 | `docs/html/disruptive-themes-whitepaper.html` | generated | regenerated |
| 3 | `docs/master-guide.md` | the System table | ours (XXXIII's Draft 4 row, from B102 and B103), then theirs' new row (XXXI) |
| 3 | `docs/white-paper-library-guide.md` | the System rows | ours (XXXIII at Draft 4), then XXXI's row |
| 3 | `tools/figures/master_guide.py` | `GROUPS`' big frame and `BOOKS` | both, by line: XXVII and XXXI in the big frame and in `BOOKS` |
| 3 | Fig 5, the Guide's HTML | generated | regenerated |
| 4 | `docs/master-guide.md` | the System table | ours (XXXIII, XXXI), then XXXII's row |
| 4 | `docs/white-paper-library-guide.md` | the System rows | ours (XXXIII, XXXI), then XXXII's row |
| 4 | `tools/check_library.py` | the numeral registry | both: XXXI's entry, then XXXII's |
| 4 | `tools/figures/master_guide.py` | `GROUPS` and `BOOKS` | both, by hand: XXXII joins the evidence group and `BOOKS` as ABCD, and the big frame is ours |
| 4 | Fig 5, the Guide's HTML | generated | regenerated |
| 5 | `docs/white-paper-library-guide.md` | the evidence and System rows | by line: theirs' XXIII row ("5 computed figures"; ours equalled the base there), then ours' XXXIII, XXXI and XXXII rows |
| 5 | the Guide's HTML | generated | regenerated |
| 6 | Fig 5, the Guide's HTML | generated | regenerated; `master_guide.py` merged without conflict |
| 7 | `tools/check_library.py` | the numeral registry | both: XXVII's entry, then XXX's |
| 7 | `tools/figures/master_guide.py` | `BOOKS` | both: XXIX, then XXX |
| 7 | Fig 5, the Guide's and the Systematic Book's HTML | generated | regenerated. XXX's own §3.5 move in the Systematic Book (accepted 26 Oct) merged without conflict |

**Foundations' three headings, after step 2 and at the end:**

```
558: ## Appendix A — Dated: Evidence log, Factor I and Factor V (as of 19 October 2026)
573: ## Appendix B — Dated: the dispatches, the 2028 and 2036 horizons, and Factor IV's debt-cycle 101 (as of 29 August 2026)
760: ## Appendix C — Dated: Records from the signal-triage orders (as of 24 October 2026)
```

**Aborted: none.** No conflict fell inside a paper's body, apart from the ruled
Foundations hunk.

## The gates after each merge

| Step | check_library (papers, failures, warnings) | check_master_guide | check_registry | The paper's own gates |
|---|---|---|---|---|
| 1 | 28 / 0 / 1: "guide claims 451,000 words, measured 477,725" | PASSED | OK | none |
| 2 | 28 / 0 / 0 | PASSED | OK | the gates that read Foundations: validate_batch15_1 71/0, validate_alt_asset_scan 50/0, validate_library_st_l 17/0 |
| 3 | 29 / 0 / 0 | PASSED | OK | none |
| 4 | 30 / 0 / 3, all check 15: XXVII and XXXI have no structural-review row; "25 older papers have no Assumptions and Falsifiers appendix (owed at review, decision 52)" | PASSED | OK | none |
| 5 | 30 / 0 / 3, the same | PASSED | OK | none |
| 6 | 31 / 0 / 5: "guide claims 451,000 words, measured 487,513", and check 15 adds XXIX | PASSED | OK | none |
| 7 | **32 / 0 / 6**: "guide claims 451,000 words, measured 504,151", and check 15 adds XXX | PASSED | OK | none |

**What clears the six warnings at the real PRs.** These are B88's script steps 6 and 7:
- **Each PR adds its paper's structural-review register row** once XXXII is on
  main: XXVII, XXXI, XXIX and XXX.
- **The last PR (XXX) refreshes the guide's header**: the paper count, the as-of
  date and the word total. The total is not a stitch count (`stitch_counts --check`:
  62 counts, 0 disagree).
- **The 25 older papers' appendix** is owed at each paper's review (decision 52),
  not at a PR.

**The final state.** `git diff --stat b8023fba` gives 59 files changed, +13,049 and
−2,632, including step 0. The papers account for 10 files, +4,445 and −1,405. The
queue index matches its 7 entry files.

## What XXX still needs

**The figures export (D48(11)), a box step before XXX's real PR,** for the operator
on the box on **Tuesday 3 Nov, in the evening, after 17:20 ET**. It is read-only
(`mode=ro`): it writes CSVs under `~/library-xxx-export/` and touches no unit. The
command is quoted from section 11 of
`docs/briefs/library-review-decisions-2026-10-30.md` on `b88-library-rehearsal`:

```
cd ~/chester-reports && mkdir -p ~/library-xxx-export && .venv/bin/python - <<'EOF'
import csv, os, sqlite3
db = os.environ.get("CHESTER_DB") or "data/chester.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
keys = ["exposure.net_gex", "yfinance.mkt_spy", "yfinance.mkt_spy_high",
        "yfinance.mkt_spy_low", "yfinance.mkt_spy_volume",
        "cftc.tff_lev_money_net_oi", "levetf.aum", "finra.margin_debit"]
out = os.path.expanduser("~/library-xxx-export")
for k in keys:
    rows = con.execute(
        "SELECT substr(observed_at,1,10), COALESCE(instrument,''), value_num, available_at "
        "FROM observations WHERE registry_key=? AND value_num IS NOT NULL "
        "ORDER BY instrument, observed_at, available_at", (k,)).fetchall()
    last = {}
    for day, inst, v, av in rows:
        last[(inst, day)] = (v, av)
    with open(f"{out}/{k}.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["instrument", "day", "value", "available_at"])
        for (inst, day), (v, av) in sorted(last.items()):
            w.writerow([inst, day, v, av])
    print(k, len(last), "rows", min((d for _, d in last), default="-"), "to",
          max((d for _, d in last), default="-"))
EOF
```

**After the export:**
1. The CSVs reach the laptop by the usual copy (the Drive inbox).
2. A drawing paste draws Figures 2, 4, 6 and 7 with `tools/figures/market_structure.py`,
   captioned "box store, as of 3 Nov 2026", on `library-xxx` before its PR.

## Box steps per paper

| Paper | Box step |
|---|---|
| XXVII, phase 3a (I and II), XXXI, XXXII, E&I, XXIX | none |
| XXX | the export above (D48(11)), read-only, 3 Nov after 17:20 ET |

## CI

`b116-library-rehearsal-2` was pushed after merge 3 (`5cc836f0`), after merge 6
(`589c8132`) and with this script. CI is read once at the end; the run id is in the
report.
