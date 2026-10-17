# Post-Friday fixes (session A, 17 Oct 2026)

Branch `post-friday-fixes`, cut from `origin/main` at `1148c66` after the Friday merges (the 25 branches, the EL pair among them). Branch-only: nothing merged, deployed or run on the box. **It merges first on Monday, before the chain** (`docs/briefs/stitching-week-19-notes.md` on `aud-3b-security-master` carries the order).

The Friday stitching notes (`docs/briefs/friday-stitching-notes.md`, "Should be ruled before Friday", items 1 to 3) listed three things, each ruled "merge as is and fix afterwards". These are the fixes.

## 1. The filler rule exempts code-written tagged lines

**The finding.** SR-43/49's anchors line, as `altdata/rates_anchors.line` writes it, closes on the descriptive tag: "… ACM term premium 1.03% (as of 2026-10-09). (descriptive; unvalidated, n=0)". The sentence splitter reads the tag as its own sentence, and at three words with one figure (`n=0`) the bare-figure rule called it filler.

**The fix** (`daily_cascade/stack_prose.py`):
- `CODE_TAG` matches the tag at the end of a line, any `n`, with or without a closing full stop; `code_tagged(text)` tests it.
- `filler_faults(text, names, code_written=False)`: a line is exempt only when **both** hold: the caller says it is code-written, and it ends on the tag.
- A model's paragraph is never exempt. The two prose paths (`stack_prose.write`, `monthly_macro/prose.py`) call without `code_written`, so a model that copied the tag onto a filler paragraph is still withheld.
- No printed line changed. SR-43/49's line is as it was.

**The fixture**, group F of `tools/validate_no_filler.py` (the rule's own gate), builds the anchors line through `rates_anchors.line` and holds:
- read as prose, its tag is a bare figure (the Friday finding, reproduced);
- code-written and tagged: exempt;
- any `n`, and a full stop after the tag: exempt;
- a code-written line without the tag: still read;
- the tag mid-line: no exemption;
- a model's filler paragraph ending on the tag: withheld.

Batch 3's gate still checks only its own sub-sections, as the Friday stitching left it.

## 2. AQ-8a's official gold leg reads the IMF IFS writer's series

**Before.** The two-bid decomposition's official leg read China's reported holdings (`safe.gold_reserves_oz`), and `imf.ifs_official_gold_oz` sat registered `not_yet_sourced`, printed in the metals block's not-tracked list. Meanwhile `imf-ifs-gold`'s writer (`altdata/sources/imf_ifs.py`, live since Friday) writes the aggregate its own docstring names as this leg.

**After.**
- **`config/attribution.yaml` `two_bid.official`:**
  - the key is `imf.ifs.gold_net_purchases_oz.total`, central banks' net gold purchases in ounces, summed across the configured countries that reported the month and the one before;
  - `kind: flow`;
  - `count_key: imf.ifs.gold_net_purchases_count.total`;
  - its labels;
  - the `not_yet_sourced` list is gone.
- **`altdata/paper_bid.two_bid_state`:**
  - for a flow, the official change over `official_months` (3) is the **sum** of those months' net purchases;
  - `kind: level` keeps the old difference of a holding;
  - the state carries `official_label`, and `official_countries`, the count behind the latest month;
  - "accumulating / flat / selling" read the sign as before.
- **The waiting line** names the leg from the config ("central banks' net gold purchases (IMF IFS)"), not "China's reported holdings".
- **`monthly_macro/stack.gold_two_bid`'s triple row:** "Central banks' net gold purchases, IMF IFS (troy ounces)". IMF IFS leaves the not-tracked list.
- **`metrics_registry.yaml` `imf.ifs_official_gold_oz`:** `superseded`, `superseded_by: imf.ifs.gold_net_purchases_oz.total`, the same pattern as the `wgc.*` names. Kept as a name so references resolve; never written.
- **SAFE's holdings stay where they were:** China's line in the Quarterly's China chapter and the 1% cross-check against IFS (`tools/validate_imf_china.py`).

**The fixture follows**, in `tools/validate_attribution.py`:
- group A: the leg's key, kind and count key; the superseded entry;
- group H: the waiting line names IMF IFS;
- group H, **fragile rally:** three months of zero net purchases with the paper leg at its highs, while China's SAFE holdings rose, which shows the leg no longer reads SAFE;
- group H, **durable base:** +100k, +200k, +300k oz over three months is +600,000 oz, by hand;
- group H, **selling:** net sales read selling, and neither state;
- group I: IMF IFS is no longer in the not-tracked list; GLD tonnage still is.

**One thing to know.** The aggregate grows as late reporters land: most within two months, the euro members and China in three. So the latest month's sum can understate until they do. The state reads the latest vintage as of the cutoff, and the count beside it says how many countries it covers.

## 3. The Ahead classes: unchanged, as ruled

Ruled as set: `boj_decision` tier 2; `treasury_buyback`, `jgb_auction` and `weekly_release` tier 3, each with its channel line and amplifiers. Nothing in the Ahead classes changes on this branch.

## Gates

Run locally, one at a time, only the two this branch changes:
- `validate_no_filler` **26/0** (group F new);
- `validate_attribution` **85/0**.

Every other gate is left to CI.

## CI

| Commit | Run | Result |
|---|---|---|
| (first push) | recorded in the stitching notes | |
