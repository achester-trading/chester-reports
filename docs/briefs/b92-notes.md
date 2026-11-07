# B92 notes: Batch 20 filed (round 10, items 111–114); V1 answered from the code

Paste B92 (`docs/pastes/B92.md`), 30 Oct 2026. Branch `b92-batch-20-filing`, base
`origin/b91-batch-19-filing` at `c8fbe39a`. The order as drafted is
`docs/pastes/B92-attachment-round-10.md` (names replaced by outlet and role, M3).
Merges right after B91's branch next week.

## Part 1: the filing

- **The order:** `docs/change-order-signal-triage-batch-20-2026-10-29.md`. It has
  the header, a §0 holding M1 to M5, then the order as written, with V1's row
  closed.
- **M1:** Batch 20 and items 111–114 are free on this base. Nothing is
  renumbered.
- **M2:** every reference resolves (the table is in §0). Two resolve to a
  different number than written:
  - the order's **"93"**, "the central-bank balance-sheet proxy", is **filed
    92**, Batch 17's global-liquidity-momentum proxy. Filed 93 is the
    negative-beta share.
  - the order's **"SR-29 (BTP–Bund, OAT–Bund)"** is **SR-30**, EU sovereign
    stress. SR-29 is Bitcoin long-term-holder supply.

  Both are recorded in M2 and on SR-74 and SR-75. The order's text keeps them as
  written, as B91 kept "54".
- **SR rows:** provisional **SR-73** (111(a), the insider buy/sell ratio),
  **SR-74** (111(b), the BIS GLI) and **SR-75** (111(c), TARGET2), each
  "provisional, placed by Audit #5". The amendments are recorded against 88(b)
  (112), item 31 (113) and Pillar 5 (111(d), conditional).
- **The index line and the register's cell are by hand**: S1's tool is not on
  this base.
- **Voices:** as in B91, no voices register file exists, and
  `config/voices_sources.yaml` is the scanner's own list. So the outlet rows are
  the order's §6 table: outlets and tags only, BofA Global Research kept as an
  institution, and the X accounts for the X pilot's seed list chat-side.
- **M4:** the four sources are candidates, each checked when built. Nothing was
  fetched.
- **M5:** no by-hand line.

## Part 2: V1, Pillar 5H, from the code

**Not built: neither by hand nor by a writer.**
- No module or config names "5H". It is in `docs/master-narrative.md` only: line
  72 ("eight sub-clusters (5A through 5H), the last of which tracks quarterly 13F
  smart-money positioning") and line 102 ("Cluster 5H 13F filings — `fetch_13f.py`
  quarterly per Phase 4 of the build plan"). No `fetch_13f.py` exists in the repo.
- The built Pillar 5, "Investor Sentiment & Positioning", is
  `config/pillars.yaml:135-151`. It reads the volatility dimension (VIX and
  realized vol) and lists the positioning half under `not_yet_sourced`, which
  needs "BofA Bull & Bear, NAAIM exposure index, 13F aggregation", because "none
  has a fetcher".
- The one 13F reader is the voices scan's `pull_13f`
  (`altdata/sources/voices_scan.py:769`, called at `:921`). It stores 13F-HR
  filings only for the firms of stored voices (`config/voices_sources.yaml:404`,
  `filers_13f`, names only, CIKs resolved at run time). The Monthly prints them
  beside a voice in section 4 (`monthly_macro/stack.py:1227`;
  `monthly_macro/v2.py:953`). There is no named-fund cluster (the narrative's
  Berkshire, Loeb and others) and no 50-fund aggregate.
- No inbox file holds one either: the by-hand inboxes are AAII, the PMI headline
  and item 47's line (CLAUDE.md, rule 3).

**What it means for 111(d).** Its condition was "applies only if 5H is still by
hand". The answer is "not built", so the condition fails by its letter, but its
purpose, automating the 13F smart-money cluster that nothing produces, would
still be served. **Needs-you:** does 111(d) apply? If it does, it builds a new
13F aggregate. That would reuse `pull_13f`'s EDGAR path and name rule rather than
a second fetcher, and it creates no by-hand line.

Recorded in the order's V1 row ("Closed by B92 ...").

## Gates

Run one at a time, foreground: check_registry, check_library,
validate_official_sources. Tallies in the report.
