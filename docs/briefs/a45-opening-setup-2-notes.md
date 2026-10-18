# a45-opening-setup-2: session notes

**Branch:** `a45-opening-setup-2`, from the tip of `a44-opening-setup` (`9f0ee8e`), on my own line.

**Merge order: it merges after a44-opening-setup in the second stitched chain** (st-t3-calib, a43-render, a44-opening-setup, a45-opening-setup-2). It carries a44's commits, so merging it first would bring a44 in unreviewed.

Branch-only. I merged nothing, deployed nothing and ran nothing on the box. Every box step below is for the operator.

---

## Part 0

### a44's CI, read once

| Commit | Run | Result |
|---|---|---|
| `5594468` (a44 part 0) | 39175949352 | **success** |
| `e62c828` (a44 part 1) | 39176741863 | **success** |
| `9f0ee8e` (a44 notes) | 39176831103 | queued at my one read |

None of mine failed, so there was nothing to fix. The numbers are also in a44's notes, which this branch updates: a45 merges after a44, so the edit lands in order and a44's tip did not move.

### The rulings, as applied

- **Ruling 1.** OS-10's most-active table now says "of 17 captured names". The count comes from the universe the table actually read, not a hard-coded 17.
- **Ruling 2.** The three vol-regime lenses print every day as three short lines beside the gauge in the 07:00 anchor's mechanics block (`opening_setup.vol_lines`):
  - VIX against 20-day realised;
  - term-structure stress (VIX3M/VIX and VIX6M/VIX);
  - the short-term spike (VIX9D/VIX).

  Each line carries its level, its 1-year and 5-year percentiles with n, and its as-of date. They come from item 52's own lens functions in `altdata/vol_event.py`, so nothing is computed twice. An absent input prints "awaiting" on its own line. Item 52's full ten-lens table stays event-day only.
  - **Displaces:** nothing. They are three short lines under the gauge; the dealer-surface table and the ST-10 block keep their budgets (`config/opening_setup.yaml` `vol_lines.displaces`).
- **Ruling 3.** The gauge centres on the last close, as it already did. **No pre-market line prints.** 6b part 3's ES conversion (`altdata/dealer_es.py`, 45c) carries SPY's levels to ES through the same-minute ratio; nothing runs from ES to SPY. Printing "ES pre-market implies SPY about \<x\>" would need new code, so it prints nothing. It is listed under Needs you, and gate E holds that no such line is printed.
- **Ruling 4.** "Front month" stands: the nearest third Friday at least 7 days out.
- **Ruling 5.** The backfill-names command is on Thursday's box sheet below. Until it runs, each OS-10 rank prints "one reading" with its window.
- **Ruling 6.** The drafts list is unchanged.

**Fixtures:** `tools/validate_opening_setup.py` group E.
- **Ruling 2:** a synthetic 300-session VIX/SPX/term series. All three lines print with their percentile, n and as-of, and each passes the numeral audit; a VIX-only store makes the term and spike lines say "awaiting".
- **Ruling 1:** a 17-name fixture prints "of 17 captured names".
- **Ruling 3:** no ES-to-SPY function exists, and no pre-market line is in the anchor's payload or render.

---

## Part 1: the opening setup, second half

All four elements are report-only: no score, no weight, and no side inferred. Every rank prints its window and n. Each reads our own captures and the store; nothing reads the vendor.

### New stored keys

`altdata/chain_metrics.record_names` writes five new keys per captured name each session, source `chain_capture`. Each key is in the registry, the display labels and the catalogue line (AUD-3a units).

| Key | Units | What |
|---|---|---|
| `chain.skew_25d_put` | `vol_pct` | Front-month put IV at −25 delta less ATM IV, in vol points. Delta is Black-Scholes, from the engine's `bs_greeks` on each put's solved IV, interpolated linearly in delta. |
| `chain.iv_minus_rv20` | `vol_pct` | Front ATM IV less 20-session close-to-close realised vol, in vol points. |
| `chain.front_expiry` | `label` | The expiry those two used, with its method. |
| `chain.put_share_volume` | `percent_share` | Puts' share of the session's options volume. |
| `chain.put_share_oi_build` | `percent_share` | Puts' share of the day's positive OI build between the two most recent captures. A fall in OI is not a build. |

SPX and SPCX are captured only through the vendor's chains (`massive_universe`). They now get the two put shares; their IV stays behind the solver gate, as for every other reader. The CLAUDE.md count line is unchanged: this branch adds no new gate, only two groups in an existing one.

### OS-8: setup profiles (the Weekly's Mechanics)

- **Prints:** in `dealer_weekly.mechanics`, after OS-10's most-active table. One four-row table titled "Setup profiles (front month)":
  - the flattest and the steepest 25-delta put skew;
  - the highest and the lowest IV against 20-day realised.

  Each row gives the name, the figure in vol points, its rank and percentile over the name's own stored history (window and n), and the front-month expiry used. It covers the 17 captured names, SPY, QQQ and IWM among them.
- **Displaces:** nothing. One table, no chart and no paragraph; the section's word count is unchanged.
- **Sources:** the two new keys and `chain.front_expiry`.
- **Fixture:** group F builds three names with 12 sessions each. The profile picks and the rank line ("rank 100, 100th percentile (… n=12)") are checked against hand values.

### OS-9: "Largest OI builds, side unknown" (the 07:00 anchor)

- **Prints:** in the anchor's mechanics block, under the vol-regime lines. Up to eight rows, from each name's two most recent captures (`chain_metrics.previous_capture`). Each row gives:
  - name, expiry, strike, type and the OI change;
  - **estimated premium** = mid at the later capture × OI change × 100;
  - **chance in the money** = Black-Scholes N(d2) for a call and N(−d2) for a put, on our solver's IV, using the house risk-free rate;
  - DTE;
  - the context tags.
- **Spreads:** two equal-size builds on the same name and expiry print as one line marked "spread (legs equal)", with both strikes, both types and "+n each".
- **The note** says OI is each capture's prior settlement, so a build is yesterday's, and that who opened the position is not known.
- **Context tags,** from our data only (`config/opening_setup.yaml` `oi_builds.tags`):

  | Tag | Fires when |
  |---|---|
  | EARNINGS | a report within 14 days, from the event store's calendar as of the cutoff |
  | 1M HIGH / 1M LOW | the close within 1% of its 21-session extreme |
  | MOMENTUM / SELLOFF | an 8% move over 5 sessions |
  | HIGH SKEW | the name's `chain.skew_25d_put` in the top decile of its stored history |
  | CHEAP VOL / VOL CRUSH | `chain.iv_minus_rv20` in the bottom or top decile of its stored history |

  A decile needs ten stored readings; below that the tag stays silent.
- **Displaces:** nothing. The table is capped at eight rows; the gauge, the dealer-surface table and the ST-10 block keep their budgets.
- **Fixtures (group F):**
  - **Hand figures:** a 105 call on 100 at 20% IV, 30 days, 4%: N(d2) = 0.2056, and the put is 1 less it. A build from 4,000 to 5,000 at a 2.40/2.60 market: premium $250,000.
  - **Table:** a ten-build chain capture pair prints eight rows, the largest first, with the two equal +500 legs merged into one "spread (legs equal)" line.
  - **Tags:** each fires on a fixture built for it and stays silent on a neutral one (the report 20 days out); nine readings give no decile.
  - **Wording:** no side word appears in the table or its note.

### OS-4: index put-volume proxy (the anchor)

- **Prints:** one line each for SPY and SPX, under the OI-build table. Each gives puts' share of the session's volume and puts' share of the day's OI build, each with its percentile, window and n, and ends "put volume and OI build, no side". A name with nothing stored says so.
- **Displaces:** nothing; two lines.
- **Fixture:** ten SPY sessions. The exact line is matched against a hand string, the numeral audit passes, and SPX reads "not stored".

### OS-5: single-name proxy (the Weekly's Mechanics)

- **Prints:** after the setup profiles. One line gives the equal-weighted z across the captured single names, each name's last put share of volume against its own history, with the window and n range, labelled "put volume and OI build, no side". A table follows of the three highest and three lowest names, each with its share, z, window and n.
- **Its reach:** it feeds nothing but its own rows. It reaches the Concentration & Complacency overlay only through the intake queue after a ledger, which is not this paste.
- **Displaces:** nothing. One line and a six-row table, no chart and no paragraph.
- **Fixture:** four names with six sessions each, checked against the z by hand and the order A, D, C, B.

### Gates

`tools/validate_opening_setup.py` now has groups A–F and passes 43/0 locally.
- **E** covers Part 0. **F** covers Part 1:
  - the hand figures (the chance in the money, the premium, the put shares, realised vol, the IV at −25 delta);
  - the spread rule;
  - every tag fired and silent;
  - the profiles, the index lines and the single-name z by hand;
  - the budgets: no chart and no words added to the Weekly, eight rows in the anchor, every element's displacement declared;
  - no score, weight or side word;
  - the hooks.
- **Group D's standing checks still hold:** no vendor key read by the new code, no new by-hand key, no network or model import, and neither of B's Weekly builders touched.
- **No live store, no fetch, no model:** every fixture is a temporary store or a temporary capture directory, and the solver is faked to a fixed 20% IV for the hand figures.
- `check_registry` passes. Everything else is CI's.

### CI for this branch

| Commit | Run | Result |
|---|---|---|
| `3c18a3a` (part 0) | 39177488304 | queued at my one read |
| `eccd28b` (part 1) | | not read yet |
| these notes | | not read yet |

---

## What waits for a tape

Our captures are end-of-day chains: prices and open interest, with no trade prints. So these wait:

- **Side classification.** Who bought and who sold needs trade-by-trade prints against the quote. Until then the OI table says "side unknown" and the put measures say "no side".
- **The scan footprint.** Sweeps, blocks and repeat prints across strikes need intraday prints.
- **Sector flows.** Aggregating premium by sector needs the same tape and a wider capture than the 17 names.

---

## Box commands, for the operator

Run these inside a window, after Thursday's merge (22 Oct): weekdays 09:05–15:40 or 17:20–23:30 ET, never 16:00–17:20. I ran none of them.

```bash
cd ~/chester-reports && git pull --ff-only

# a44's names backfill (ruling 5). After a45 it also writes the five new keys
# per name: skew, IV against realised, front expiry, both put shares.
.venv/bin/python -m altdata.chain_metrics backfill-names --days 60 --dry-run
.venv/bin/python -m altdata.chain_metrics backfill-names --days 60
```

- **The first anchor with the OI-build table and the index lines is Friday 23 Oct at 07:00.** It needs two sessions of captures on disk, which the box already has. The tags that need a decile stay silent until a name has ten stored readings; after the backfill that is immediate.
- **The first Weekly with the setup profiles and the single-name table is Sunday 25 Oct.** Its dry run is yours.

---

## Files shared with the open branches

Trial merges of a45's tip against each of B's branches (`git merge-tree`, read-only) give **exactly the same conflict list as a44's tip does.** a45 adds no new conflict.

- **weekly-fixes-9 and weekly-fixes-8:** they share `config/catalogue_commands.yaml`, `config/display_labels.yaml` and `metrics_registry.yaml` with this branch. The changes are an appended registry block, appended labels and one widened catalogue sentence, and all three auto-merge.
- **lenses-group-b:** it shares `config/catalogue_commands.yaml`, `daily_cascade/morning_payload.py`, `daily_cascade/morning_render.py` and `metrics_registry.yaml`. My hooks are three lines beside a44's gauge hook, and they auto-merge.
- **The Weekly builders:** I did not touch `weekly_stack.py` or `weekly_sections.py`. The Weekly's two new tables enter through `dealer_weekly.mechanics`, my module. There is no ST-13 branch on origin at my read.

---

## Needs you

1. **The pre-market line (ruling 3) needs an ES-to-SPY conversion.** The inverse of `dealer_es`'s ratio is small, but it is new code, so nothing prints. Say if you want it.
2. **OS-9's premium uses the later capture's mid,** or the last price where there is no two-sided quote. It prints "n/a" where neither exists.
3. **OS-9's universe is the 17 captured names,** the same as OS-10's (a44's needs-you 1). SPX gets OS-4's lines through the vendor's chains, but no IV until the solver gate admits it.
4. **The HIGH SKEW, CHEAP VOL and VOL CRUSH deciles are over our own stored history, and need ten readings.** That is session-set (`decile_n_min`).
5. **The drafts for your accept-all** are unchanged: the six ST-8 gate statuses, the SR-21, SR-22 and two FRED notes, and the Doctrine rule proposal.
