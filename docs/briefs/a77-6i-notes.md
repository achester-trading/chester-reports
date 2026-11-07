# A77 notes: 6i tranches 6i-1, 6i-2 and 6i-5

**Session A, 26 Oct 2026, branch `a77-6i-tranches-1-2-5`.** The paste is `docs/pastes/A77.md`. The rulings are those of 25 Oct 2026 on `docs/briefs/6i-spec-draft-2026-10-25.md`, all eight decisions accepted as the brief recommended them.

**Base:** `origin/s1-stitch-refactor` at `6ed16538`. The 6i brief is not on that base: it sits on `b63-6i-brief` and the branches after it. It was carried over unchanged in the first commit so its path resolves; the identical file merges cleanly with `b63-6i-brief`.

Code and config only, branch-only. This branch merges after the 1 Nov Monthly. No box, no units, no `.env`, no register write.

---

## 6i-1: the rows switched

The brief's appendix lists 40 W rows. Of those, **37 are switched** and **3 stay**.

**The 37 switched.** Each now names its stored key(s), and the brief's reason string is gone. The rows are checked one by one by `tools/validate_quarterly_rows_6i.py`. Changes by chapter:

- **Currency:** the EM dollar index (`fred.dxy_em`) and stablecoin supply (`llama.stable_total`). The stablecoin-dollarisation analysis now prints its series. The `stablecoins_dollar` test is measured on its second clause.
- **EM:** the EM dollar index, and the copper-gold analysis, which reads the correlation layer's `corr.copper_gold__10y.60d` and `.252d`.
- **China:** SAFE against the IMF IFS gold reading, as `ratio_pct`, which is exactly the 1% cross-check. Property starts reads `nbs.re_starts_ytd`.
- **Crypto structure:**
  - LLaMA stable total and LTH share.
  - OI-weighted funding, BTC, split into `calc.funding_agg` and `calc.oi_mcap`.
  - DVOL.
  - Hashrate. Miner reserves stays as its own absent row.
  - The treasury companies, split into net purchases and MSTR's mNAV.
- **Crypto analyses and tests:**
  - `stable_bills` prints `llama.stable_total`.
  - `sol_pmf` reads Solana's TVL, `llama.chain_tvl` with instrument Solana, against BTC.
  - `stablecoin_infra` is measured on supply. A contraction prints "not measured" until "price stability" has a reading.
- **Crypto coin pages:**
  - BTC: supply and derivatives.
  - ETH: market and derivatives.
  - SOL: economics, usage and market.
  - PRL: definition (SM00118), supply, market and derivatives.
- **Crypto gauges:** stablecoin supply (a by-issuer remainder row is added) and memecoin froth (`calc.froth_z`, solana:new_pools; unscored until 90 days are stored).
- **Real estate:** Case-Shiller national. It is the nominal index; the real year-on-year read against CPI is not computed, and the label says so.
- **International equities:** HEFA/EFA and BTP less Bund.
- **Thailand:** four rows on `thai.*`. Each keeps `namespace: thailand`, and none of the keys is trigger-eligible.

**Six rows keep part of their reason:** what they still do not hold. Examples are CME positioning, the SOL DEX volume (`llama.dex_volume` covers all chains), S3 for PRL, and D5's retired source. Two remainder rows are new: miner reserves, and stablecoin supply by issuer. The rows carrying a reason go from 230 to 201.

**The 3 that stay:**
- **USD/THB in the currency pairs**, on the operator's ruling (AQ-3 part 1, Needs you 2), as the appendix says.
- **SOL's and ZEC's derivatives.** The brief read them as W, but `hl.funding`, `fut.funding_okx`, `calc.oi_mcap` and `calc.funding_agg` exist for BTC and ETH only, and Farside's flows for BTC and ETH only. The code wins over the brief.

**Code.** `monthly_macro/quarterly_items.py` gains two things:
- a measurable leg now passes its `instrument` (in `quarters_negative`, `change_below` and `change_above`);
- a coin field may carry an `instruments:` map from key to instrument, so `keys` stays a list of registry keys.

**Gates moved.** `validate_quarterly_stack`'s coin-page check asserted ETH's market field as "not yet". It now asserts the key.

## 6i-2: the harness core

`altdata/tb_harness.py`, `config/tb_episodes.yaml`, `docs/ledgers/tb-harness-2026-10-26.md` and its episodes CSV.

### The thirteen, with sources

| Episode | Dates | Source | Session-set |
|---|---|---|---|
| top_2000 | 2000-03-24 | Tops and Bottoms §6; Part 23 (v8 moves 2000 to OVEREXTENDED) | no |
| top_2007 | 2007-10-09 | §7 ("the composite missed this top") | no |
| top_2022 | 2022-01-03 | §9; Part 23 ("2007/2022-type tops") | no |
| bottom_1990 | 1990-10-11 | §5 | yes: class (see below) |
| bottom_2002 | 2002-10-09 | §6 | yes: class |
| bottom_2009 | 2009-03-09 | §7 | yes: class |
| bottom_2011 | 2011-10-03 | §10 ("The October 2011 low scored as a bottom") | yes: the day (the paper says October 2011) |
| bottom_2020 | 2020-03-23 | §8 | yes: class |
| bottom_2022 | 2022-10-12 | §9 ("missed the 2022 bottom") | no |
| control_1998 | 1998-07-17, 1998-10-08 | §10; §11's control class | yes: choice and days |
| control_2015 | 2015-05-21, 2016-02-11 | §10 | yes: choice and days |
| control_2018 | 2018-09-20, 2018-12-24 | §10 ("used December 24, 2018 as a control") | no |
| control_2024 | 2024-07-16, 2024-08-05 | §10; Part 23 ("known false-fire Aug 2024") | yes: choice and the high's day |

**What the session set, and why:**
- **The six bottoms.** The papers fix two of them: 2011 is a hit and 2022 a miss. The other four are session-set. They are the post-1990 bear lows whose signature §11 reads, 1990 being the first bear low with a VIX.
- **The four controls.** §11 names five control-type events: 1994, 1998, 2015, 2018 and 2024. 1994 is the one left out ("maximum drawdown was under 9%", a time correction before the HY series begins).
- **Every date was checked against the store.** All 17 decision dates agree with the store's own S&P 500 closing extremes; the ledger prints the check beside each.
- **The extended set's dates.** The eight bears' dates are the paper's own. The near-misses' days, and the pre-1970 days, are session-set. The 1937 top is the store's high of 10 Mar 1937; the 6 Mar session is not stored.

### The overlays, the thresholds and their sources

Every threshold is the architecture's Part 23, "The three parallel overlays", and each overlay fires at 3 or more. Session-set, with the reason in the config:

- **ERP** is 100/CAPE less Shiller's 10-year rate. Part 23 names ERP ≤ 1.5% and does not define it.
- **SOFR−IORB** is the mean over five common sessions.
- **|TGAΔ|** is over four weeks.
- **NetLiq** is year on year only; Part 23's "accel" is not read.
- **Shiller's months are lagged three.** The workbook has no vintages, and `publication_lags.yaml` states no lag for it (A64). So CAPE values are the current vintage, not first prints, and the ledger says so.
- **Max reading ages:** 10, 21 and 125 days.
- **"Differs" from the hand-keyed value** means beyond 10%.

**"Not existent" dates:**
- **Exists from:** VIX 1990-01-02 (the paper); HY and IG OAS 1996-12-31; SOFR 2018-04-02; IORB 2021-07-29; net liquidity 2002-12-18 (WALCL); forward P/E 1995-01-01 (the paper's "mid-1990s").
- **No start fixed here:** reserves, RRP and TGA. Before the store holds them they read "not stored", never "not existent".

**The credit leg** reads `fred.hy_oas` where the store holds it. Before that, it prints "pending 6i-3: Baa less the 10-year".

### The ledger's pass rule

The rule is quoted in full at the ledger's head and in `config/tb_episodes.yaml`. Its SHA-256, over the whitespace-normalised text, is `937503cbe9ba98051c0888a6e8214e48b20d31967a2c6d5adc245168913c250a`.

In short, it asks two questions:
1. **REPRODUCED or NOT REPRODUCIBLE ON THIS BUILD**, against tops 0/3, bottoms 4/6, controls 4/4.
2. **The overlays' record:** PASS needs all three tops and all four controls read, with at least 2 of 3 tops called and at least 3 of 4 controls refused. INSUFFICIENT if any is unread; FAIL otherwise.

### The laptop verdict

**INSUFFICIENT.** All 3 tops and all 4 controls are unread. The answer to the ledger's own question is **NOT REPRODUCIBLE ON THIS BUILD**, because the overlays do not score bottoms.

The laptop's store is partial. Its FRED rows were all first knowable on 2026-05-30 (the migration instant), it holds no Shiller rows, and it holds no SPY holdings. Only VIX reads at any of the thirteen's dates; it agrees with the paper's 22.5 at the 2000 top (23.31).

The box's run supersedes this edition.

### Where the ledger convention and the paste meet

`docs/ledgers/README.md` says a calibration ledger "never reads the observation store as-of", because the store's history began on 30 May 2026. The paste asks for a point-in-time harness over the store, run on the box. AUD-3d's ALFRED backfill now gives FRED rows their first vintage, which is what makes that sound. The ledger states its source as the store.

## 6i-5: Themes Stage 1

**Where it sits.** `daily_cascade/themes_block.py` builds the section from `config/themes_panels.yaml`. It joins the Alternative Assets Quarterly through `config/stack_hooks/quarterly-slow-themes-panels.yaml`, after the eleven family chapters, at a new anchor `family_chapters`. `monthly_macro/quarterly.py` now runs `stack_hooks.run("quarterly", "slow", "family_chapters", ...)` after `build_chapters`.

**What it is.** It is a reference-tier section, deliberately not a chapter: a chapter gets a model-written summary paragraph, and Stage 1 calls no model. The Monthly and the Weekly never run the hook.

**The panels.** There are 4 panels and 36 rows, all Factor I inputs, all unscored. **28 rows read stored keys; 8 are declared GAP cells.** A stored key with nothing by the cutoff also prints GAP, naming the key, its instrument and the date.

| Panel | Rows | Declared GAPs |
|---|---|---|
| The real economy (items 22, 23) | 7 | 0 |
| Capex and the chain (items 26, 63) | 17 | 1: capex guidance |
| Unit economics and the labs (items 47, 75) | 5 | 5: item 47's four sub-parts; the lab ledger is a file, not a series |
| Bottlenecks, credit, concentration (items 65, 76) | 7 | 2: the AI credit watch; DTCC protection demand |

**Numbering.** Batch 14's written items 56 and 58 were filed as 63 and 65 (its F1). The rows cite the filed numbers.

**Not built here.** No Factor V panel. No other refresh input outside the brief's list was added.

## Box commands (for chain-8's box sheet)

The harness opens the store read-only and writes only its ledger. On the box, write the ledger outside the checkout, so `git pull --ff-only` stays clean:

```
cd ~/chester-reports && .venv/bin/python -m altdata.tb_harness ledger --edition box --dry-run | head -60
cd ~/chester-reports && .venv/bin/python -m altdata.tb_harness ledger --edition box --out-dir ~/chester-data/outbox/tb-harness
```

The ledger is then copied back by a session paste on a branch. The box edition is a new dated file; the laptop's is never edited.

To see one date's three overlays, read-only:

```
cd ~/chester-reports && .venv/bin/python -m altdata.tb_harness show --date 2026-10-23
```

## Gates and the count

The three new gates each declare `GATE_KIND = "code"`:

- `tools/validate_quarterly_rows_6i.py`: 21 passed.
- `tools/validate_tb_harness.py`: 32 passed.
- `tools/validate_themes_panels.py`: 19 passed.

`tools/stitch_counts.py --write` moved CLAUDE.md's two gate counts, and nothing else disagreed:
- code gates: one hundred and forty-two → one hundred and forty-five;
- Python gates: one hundred and thirty-nine → one hundred and forty-two.

Run locally: validate_stack_hooks 15/0, check_registry OK, check_library 0 failures and 0 warnings, validate_quarterly_gates 95/0, validate_by_hand_audit 17/0, validate_alt_asset_scan 50/0. validate_quarterly_stack: its first run failed one check (ETH's market field, now moved to the key, as the paste directs). The reruns of validate_quarterly_stack and validate_monthly_stack over the final tree were stopped by the laptop for low memory before they finished, so their verdict is CI's (below).

## Needs you

1. **`config/stack_hooks/_anchors.yaml` was edited.** The paste allows new files only under `config/stack_hooks/`. The Quarterly had no anchor, and a hook cannot join a stack without one, so one anchor (`quarterly: slow: family_chapters`, four lines, append-only) was added. Accept it, or name another place.
2. **The thirteen's reconstruction.** Six of the thirteen classes or dates are session-set (the table above). The ones that matter most are the four bottoms the papers do not fix (1990, 2002, 2009, 2020), and leaving 1994 out of the controls. Accept, or name the 3 Sep list if a copy exists.
3. **The pass rule.** Its second half was written here, because no order stated one: PASS needs at least 2 of 3 tops called and at least 3 of 4 controls refused, with every top and control read. It is registered by its SHA-256. Changing it means a new registration and a new dated ledger.
4. **Three W rows the brief miscounted.** SOL's and ZEC's derivatives stay not tracked (their keys are BTC and ETH only), and USD/THB stays on your ruling. So 37 rows are switched, not 40.
5. **The house-price row prints the nominal Case-Shiller index.** The appendix said "against `fred.cpi`", but no real year-on-year key exists, and computing one in the chapter would be a new derived kind. The label says so. Either add a derived kind later (6i-7) or accept the nominal row.
