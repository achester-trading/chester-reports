# a43-render: the rulings on ST-8 and ST-9, the Massive capture clock, the FlashAlpha writer's configuration and conventions, and ST-10's rendering rows (session A, 18 Oct 2026)

**What it builds on.** The branch starts at the tip of `st-t3-calib` (`a6d192a`, its CI fix), on session A's own line. It therefore carries ST-7, ST-8, ST-9 and ST-5, and everything under them.

**Merge order.** It merges after `st-t3-calib`, in the second stitched chain: gtm-core-1, gtm-core-2, st-t1-rest, st-t2-rates, st-t3-calib, then a43-render.

**What was done.** I pushed only. Nothing was merged or deployed, nothing ran on the box, and no unit was enabled or started. Every box step is printed below for the operator.

**Commits:**

| Commit | What |
|---|---|
| `a6d192a` (on st-t3-calib) | st-t3-calib's CI fix, and its notes' CI rows |
| `7e28171` | `3b0da9a` cherry-picked (validate_alpha's fixture clock; the gate's hunk only) |
| `9a23d5e` | Part 0, steps 1–2: the rulings |
| `3bb18df` | Part 0, step 3: M-3 |
| `0388608` | Part 0, steps 4–5: F-1 to F-4 |
| `f6bfc9a` | Part 1: ST-10 |
| `869663b` | The CI fixes after Part 0's runs |
| this commit | These notes, and the technical appendix's our-GEX row aligned with weekly-fixes-9 |

---

## Part 0

### Step 1: CI

**st-t3-calib's runs, read once.** All five runs failed on `validate_alpha` (the clock fault).

| Commit | Run | Result |
|---|---|---|
| `ed1e533` (its notes) | 39152102354 | **failed**, 102 of 105 jobs green. Two mine-or-ruled failures: `validate_regime` L, mine (my group R pattern spelled the withdrawn cell's name), and `validate_alpha`. The third red job is the summary. |
| `493601f` | 39151947418 | **failed**: the same two |
| `3f64691` | 39151733576 | **failed**:<br>• `validate_regime` L<br>• `validate_st_t1_rest` and `validate_weekly_edits`, both fixed in `493601f`<br>• `validate_alpha` |

**The fix.**
- **`validate_regime` L** is fixed in `a6d192a` on st-t3-calib: the pattern drops the cell's names, which stay `validate_regime`'s own check. St-t3-calib's notes carry the numbers.
- **`3b0da9a`** (session B's fixture clock, the fix of record under ruling 8) is cherry-picked as `7e28171`. Its notes hunk did not apply: that file lives on lenses-group-b only. So only the gate's hunk was kept.
- **`validate_alpha`** now reads **257/0** locally, as expected.

### Step 2: the rulings

- **Ruling 1 (SR-1).** The panel prints a gate line beside the pair readings. It reads: HML PASS, n 6, +4.2% at 6 months and +17.9% at 12; IVE-IVW n 3 and IWD-IWF n 3, each "under its floor of six", at −4.6% and −4.3% at 52 weeks; display only; the rights question is the Doctrine monthly's.
  - The figures live in `config/style_regime.yaml` (`gate_reading`). The gate recomputes every one from the ledger's CSV.
  - The SR-1 draft carries ruling 1 in full.
- **Rulings 2 to 10.** No rename. SR-5, SR-2, SR-4, SR-13, SR-14, SR-8 and SR-22 stand as reported, and nothing else in the ledgers changed.
- **The two FRED source changes** are dated rule-31 notes in the register:
  - **SR-4:** IRLTLT01CNM156N returns 404, and so do the CNA and INTGSB ids.
  - **SR-8:** ICE BofA HY OAS is served from 2023-10-17 only, and Baa less the 10-year is the labelled long-history proxy.
- **The HY charts and lenses** say which series they read and from when:
  - the Weekly's W3 and the Monthly's M5 captions print "ICE BofA US High Yield OAS (FRED BAMLH0A0HYM2), stored from \<first day\>; FRED's own history now starts 2023-10-17";
  - the quality-tail lens names its series;
  - the technical appendix's OAS row says the same.
  - The wording is `altdata.labels.hy_source()`. No internal id prints, per the Weekly's id rule.

### Step 3: M-3, the Massive capture clock

| Change | Where |
|---|---|
| The 16:10 pass skips the vendor universe and logs "SPX, SPCX skipped -- captured at 16:31 ET by chester-vendor-chains". It writes no vendor section in its completeness record. | `run_eod.py` |
| **New unit** `chester-vendor-chains.service`/`.timer`, Mon–Fri 16:31 ET (the 16:16 data). It runs `run_dealer_capture.sh chains` → `altdata/vendor_chains.py`: the same `massive_chain.pull`, the same files, the same directory, and its own `_vendor_completeness.json`. Capture caps 10%/12%, OOM score 300, `Persistent=false`. Not in `DEPLOY_TIMERS`. | `deploy/systemd/`, `scripts/run_dealer_capture.sh`, `altdata/vendor_chains.py` |
| **The stamps.** Every vendor row and manifest carries `vendor_data_as_of`: "09:30 ET (15-minute delay)", "12:15 ET", or "16:16 ET". | `config.vendor_as_of`, `massive_chain`, `dealer_capture` |
| **The close's reader** merges the vendor record. Read before 16:31 it says "not yet captured at the read (chester-vendor-chains runs at 16:31 ET)", never "missing". | `chain_completeness.read_completeness` |

- Open interest is the prior settlement's whatever the clock, so nothing is backfilled.
- `validate_systemd_units` lists the unit (139/0).

### Steps 4 and 5: F-1 to F-4, the vendor writer, and the F-3 conventions

**F-1, the plan.**
- **The budget** is 60 requests a day. **The plan is 57, not the "about 49" in the paste:** 45 at 16:25, plus 6 at 09:45 and 6 at 12:30 (see Needs you).
- **At 16:25,** for SPY, QQQ, IWM, SPX and MSTR:
  - the **summary**: its exposure, volatility and macro blocks. The macro block holds VIX9D, VIX, VIX3M, VIX6M, the VX front month and its basis, VVIX, SKEW, MOVE, and Fear & Greed as `vendor.fear_greed`;
  - **levels**;
  - **max pain's** compact fields;
  - **expected move**;
  - **DEX, VEX and CHEX** by strike, as blobs.

  Also at 16:25: the surface for SPY and QQQ, and GEX by single expiry for the nearest five SPY and three SPX expiries. The expiries are read from the expected-move or max-pain response, never guessed.
- **At 09:45 and 12:30:** the summary and levels for SPY, QQQ and SPX, through the capture wrapper and never fatal. Intraday rows are stored on `SYMBOL@HHMM` instruments, so the 16:25 comparison never reads them.
- **Blobs** go to `data/vendor/flashalpha/<day>/`, which is gitignored.
- **19 new registry keys** under source `flashalpha`. No engine, flag, tell, dial or decision reads one; the gate greps for that.
- **The endpoint paths** come from the vendor's own documentation, read 18 Oct. **Expected move's path is not in the docs** and is marked unverified: the first box run's summary lists what answered.

**F-2.** A vendor ATM IV is compared only on the first listed expiry of 20 DTE or more, and only from 16:25 (`vendor.atm_iv_20dte`). The summary's front IV (on 16 Oct about three times the 20-day realized; vendor figures removed, 19 Oct 2026, under the standing rule) is stored, never compared.

**F-4.**
- `plan_ends: 2027-03-31`. From 1 April the writer makes no call and the Weekly's vendor row reads "vendor: plan ended".
- The Weekly's mechanics table gets one vendor row: flip, walls, max pain, regime, and net GEX in both units. (The 16 Oct values this line quoted are removed under Batch 11's D2: no vendor figure in a committed file.)
- **The two chat-side FlashAlpha tasks retire at chain-2's merge** (Batch 11's D7, 19 Oct 2026), not on 29 Oct: the 16:25 writer and its divergence gate are the check from then.
- The divergence gate now flags a flip more than **0.5%** of spot from ours (it was 1.0%) or a regime word that disagrees with our sign.

**F-3, the conventions.** They are in the Weekly's technical appendix (four rows) and the writer's notes:
- **The vendor's GEX** is Σ dealer position × gamma × OI × 100 × spot² × 0.01, in $ per 1%. Calls +, puts −, on prior-night settled OI and their own IV.
- **Ours** is the same sum on our OI and our IV: the report's net GEX per $1 move, × 0.01 × spot.
- **DEX:** theirs is the customer book (calls +); ours is the dealer position.
- **Walls:** theirs are the all-strike peaks; ours, from Thursday, are the OTM walls.

**The one-strike reconciliation** is the first entry of `docs/ledgers/vendor-divergence-notes.md`. I reached the vendor through the FlashAlpha connector: two requests, SPY's 23 Oct GEX and its summary. It covers SPY 770, 23 Oct expiry, on the 16 Oct settlement's OI. (Vendor figures removed, 19 Oct 2026, under the standing rule: the spot, OI, GEX and implied gammas the vendor served are not kept here; the committed fixture is synthetic.)

| | Their GEX | Gamma that implies | IV that implies |
|---|---|---|---|
| Call | positive | under Black-Scholes' peak | a high IV, far above ours |
| Put | negative, larger | above Black-Scholes' peak for the tenor | none |

- **The two legs' implied gammas differ by a multiple, at one strike and one expiry.** Black-Scholes gives a call and a put one gamma at one IV.
- With one IV of 12–20% on both legs, the strike nets positive where the vendor's net is negative: the sign flips.
- **So the vendor's larger GEX is the gamma term,** from the vendor's own per-contract IVs on a front expiry. It is not the multiplier or the spot term (the same on both sides, as on 9 Oct) or the OI set (both read the prior settlement). The expiries covered are a residual question for the box.
- **Our side is marked for the box.** `tools/vendor_reconcile.py --chain` reads our 16 Oct capture.

---

## Part 1: ST-10's rendering rows

**The 07:00 anchor** gets a "Signal lines" block (`daily_cascade/signal_lines.py`, `config/st10_lines.yaml`):
- **The budget:** at most 4 lines of 60 words each.
- **A day nothing triggers prints nothing:** no heading, no "none".
- **The numerals:** every line carries its values and its name constants, and passes the numeral audit.

| Line | Trigger | What it displaces |
|---|---|---|
| Auction (SR-22) | A coupon auction in the session's upcoming-auctions calendar | Nothing: it appears only on auction days. It carries ABS_STRESS with its base rate and its modifier suspended. |
| FOMC-week gap (SR-21/23) | An FOMC week (the Fed's calendar) or a refunding week (the first Wednesday of Feb/May/Aug/Nov) | Nothing: twelve weeks a year. Descriptive only. |
| Yen flag (SR-2) | `calc.jpy_unwind` = 1 at the prior close | Nothing: the tell is off most sessions. Display only, with ST-5's thresholds session-set. |
| Rally inside a bear (SR-8) | SPY at least 20% off its 252-session high, below a falling 200-day, and at least 10% off its low; the newest close within a week | Nothing: it appears only inside a bear. "A mechanism, not a signal": the audit failed. |

**The 12:30 hooks** (`daily_cascade/funding_hooks.py`, in `midday_gate.GATES`) are alert-only and open only on their triggers:
- **The yen unwind** reads the 12:30 USDJPY quote against the close 5 sessions back, with the prior close's vol at ST-5's 1.5× its median.
- **The devaluation hook** reads today's CFETS fix and the 12:30 CNH and CNY quotes, through ST-5's own `tell_legs`. Its line prints "2 of 3 legs tracked, both held", each leg, leg 3 NOT TRACKED, and no verdict word.
- **When every gate is closed** the slot writes nothing and calls no model, and no model is called either way.
- The capture's quotes gain JPY=X, CNH=X and CNY=X.

**The Sunday line and the Books** go in the Weekly, through `dealer_weekly.mechanics`, my module. `weekly_stack.py` and `weekly_sections.py` are untouched. They print:
- one line: the rates driver (withdrawn), ABS_STRESS with its base rate, and CRED_STRESS (descriptive);
- Book A: A-1, A-2 and A-3, each met, unmet or not determinable;
- Book B: SR-1 style (display, no flag word), SR-5's RS tell (not live), the devaluation tell (2 of 3 legs, no verdict), and the EM flag (display only).

On an empty store, no internal id prints.

**The Daily grep gate:** no daily output or daily-path module contains "PRL" or "Pearl".

**Not here:** the Sunday Mechanism Watch block (MW-10) and the PRL information line, which wait for Tranche 5.

---

## Gates

**`tools/validate_a43_render.py`, groups A–D: 44/0 locally.**
- **A, the rulings:** the panel's figures recomputed from the CSV, the FRED notes, and the HY captions.
- **B, M-3:**
  - the stamps;
  - `run_eod` run with fake fetchers: it skips the vendor universe, logs it, and calls no Massive fetch;
  - the 16:31 record;
  - the 09:45 stamp, and each row's stamp;
  - the units, and their absence from `DEPLOY_TIMERS`;
  - the close's reader pending before 16:31 and reading after.
- **C, F-1 to F-4:**
  - the budget holds at 60 on a fixture day (6, 6 and 45, then a rerun stopped after 3);
  - SPX is on the list;
  - GEX by expiry from the listed expiries;
  - the IV rule (15.2 is compared, not the 1-DTE 120);
  - `plan_ends`;
  - the vendor row in both units;
  - the 0.5% flip and the regime check;
  - the conventions in place;
  - the reconciliation by hand;
  - no engine reads a vendor key.
- **D, ST-10:**
  - the four lines within budget, each passing the numeral audit;
  - a quiet day prints nothing;
  - the weeks' rules;
  - each hook opening on its trigger and staying closed otherwise;
  - the devaluation hook printing no verdict word;
  - a closed slot writing nothing;
  - no model or network import;
  - the Sunday line, with no id leaking;
  - the PRL/Pearl grep;
  - nothing entering a composite;
  - no by-hand key;
  - neither Weekly builder touched.

**Also changed:**
- `validate_dealer_vendor` (28/0): writer v2's counts, and the 0.5% flip.
- `validate_systemd_units` (139/0): the new unit.
- `validate_st_t1_rest` (34/0) and `validate_st_t3_calib` (88/0): the ledger line, and the SR-8 entry re-pinned with its note.
- `validate_alpha` (257/0): the cherry-pick.
- The catalogue gains `altdata.vendor_chains`.
- CLAUDE.md now counts ninety-seven code gates.

Everything else is CI's.

### CI for this branch

| Commit | Run | Result |
|---|---|---|
| `9a23d5e` | 39157969571 | **failed**: `validate_weekly_edits`, the id rule (my HY caption printed `fred.hy_oas`); fixed in `869663b` |
| `3bb18df` | 39158359122 | **failed**: the same, and `validate_audit_3a` (the catalogue lacked `altdata.vendor_chains`); fixed in `869663b` |
| `0388608` (F-1 to F-4) | 39159386065 | **failed**: the same two, already fixed in `869663b` |
| `f6bfc9a` (Part 1) | 39160062209 | **failed**, mine: `validate_official_sources` (funding_hooks imported a writer, cfets), `validate_vol_event` and `validate_dealer_block` (both pinned the two-gate 12:30 registry), `validate_st_t2_rates` L (st10_lines.yaml named an ST-5 key), `validate_st_t3_calib` A (signal_lines reads calc.abs_stress); plus the two `869663b` fixed |
| `869663b` | 39160241459 | **failed**: the five above |
| `f165f12` (these notes) | 39160398717 | **failed**: the five above |
| the CI-fix commit after these notes | read on a44-opening-setup | All five fixed: funding_hooks reads the gap through `funding_currency.offshore_gap_bp`; the two registry checks read the four gates; the yaml names no key; signal_lines is a listed display reader of ABS_STRESS. Both branches' Weekly-builder checks are scoped to their own ranges. Locally: vol_event 45/0, dealer_block 133/0, st_t2_rates 71/0, st_t3_calib 88/0, a43_render 44/0. |

---

## Box commands, for the operator

Run these inside a window, after Thursday's merge (22 Oct): weekdays 09:05–15:40 or 17:20–23:30 ET, never 16:00–17:20; weekends are open, clear of Sunday 05:00. I ran none of them. Unit commands are yours.

```bash
cd ~/chester-reports && git pull --ff-only
bash scripts/deploy_remote.sh        # or the laptop's scripts/deploy.sh: copies the new unit files

# M-3: the 16:31 vendor chains. Enable once the EOD pass's log shows the skip line:
systemctl --user daemon-reload
systemctl --user enable --now chester-vendor-chains.timer
systemctl --user list-timers 'chester-vendor-chains*' 'chester-eod*'
# The first 16:31 run, read afterwards:
tail -n 30 ~/logs/dealer_capture-$(date +%Y-%m).log
ls data/chains/$(date +%F)/ | grep -E "SPX|SPCX|_vendor_completeness"

# The vendor writer's first run with the new config (16:25 the day after the merge),
# then its summary: what answered, what was absent (expected move's path is unverified):
journalctl --user -u chester-flashalpha.service -n 60 --no-pager
cat ~/.chester/flashalpha_calls.json        # the day's count, at most 60
.venv/bin/python tools/validate_vendor_divergence.py

# F-3's reconciliation, our side (the 16 Oct SPY capture):
.venv/bin/python tools/vendor_reconcile.py --chain data/chains/2026-10-16/SPY_<stamp>.csv
```

**The first anchor with the new lines is the next 07:00 after the merge:** `chester-morning-anchor`, as it stands. The block prints only on a trigger. The first 12:30 with the hooks is the capture's next slot.

**The first Weekly with the Sunday line is Sunday 25 Oct**, 05:00. Its dry run is yours.

---

## Files shared with the open branches

**weekly-fixes-9 (session B), above all.**
- **Shared files:** `CLAUDE.md`, `Makefile`, `altdata/chain_completeness.py`, `altdata/labels.py`, `altdata/sources/massive_chain.py`, `config/catalogue_commands.yaml`, `config/reporting_stack.yaml`, `daily_cascade/charts.py`, `deploy/systemd/README.md`, `metrics_registry.yaml`, `run_eod.py`, `tools/validate_alpha.py` and `tools/validate_systemd_units.py`.
- **A read-only trial merge finds one conflict that st-t3-calib's tip did not have: `config/reporting_stack.yaml`, in the technical appendix.**
  - B rewrites the Net GEX, DEX and Implied-move rows, and adds a Numeral-audit row.
  - I edit the Credit-spread row and add four vendor rows after Brier.
  - **The stitch keeps both.** My "Our GEX in the vendor's terms" row was aligned with B's corrected Net GEX unit ("per $1 move, times 0.01 × spot") in this commit, so the two read the same either way.
- `tools/validate_alpha.py` is B's `3b0da9a`, cherry-picked unchanged. The stitch takes it once.

**weekly-fixes-8:** the same conflict, the same resolution.

**lenses-group-b:** sixteen shared files, and no new conflict. They include `morning_payload.py` and `morning_render.py`, each with a one-line hook of mine.

**What I left alone.** I did not touch:
- `weekly_stack.py` or `weekly_sections.py` (the Weekly builders B is fixing);
- any of B's branches;
- Monday's chain;
- chester-meme.

---

## Needs you

1. **The vendor plan is 57 requests a day, not about 49.** That is 45 at 16:25 as specified, plus 6 at 09:45 and 6 at 12:30. It fits the 60. To reach 49, the fields could drop to 16:25 only for IWM and MSTR. That's your ruling; I changed nothing to get there.
2. **Expected move's endpoint path is not in the vendor's documentation.** It is configured as `/v1/exposure/expected-move/{symbol}`, unverified. If the first box run shows it absent, the 20-DTE IV (F-2) and the GEX expiries fall back to the max-pain response's expiries. Then the 20-DTE IV is absent until a path is confirmed.
3. **The reconciliation's conclusion is the vendor's per-contract IV.** It can be restated with our side once the box run gives our 770 gamma. If the expiries covered turn out to carry the rest of the gap, the entry's addendum says so.
4. **The rally-inside-bear line's live rule** (20% drawdown, 10% off the low, a falling 200-day) is the audit's candidate definition read live. It is session-set and displays only. Since the audit failed, whether the line should print at all before the Doctrine monthly is yours.
5. **The Sunday line sits in the Weekly's Mechanics section**, through the hook session A owns. Section 7 places it in the Sunday anchor, which is the Weekly. A first-page position would mean editing `weekly_stack.py`, which B is fixing this week.
6. **The drafts for your accept-all (rule 31):** the six ST-8 gate statuses (SR-1's now carrying ruling 1), the SR-21 and SR-22 dated notes, the two FRED source notes (SR-4, SR-8), and the Doctrine rule proposal in the false-bottom audit.
7. **Enabling `chester-vendor-chains.timer` is yours** (above). Until it runs, the close says the vendor chains are pending, and SPX and SPCX OI is not captured that day. So it wants enabling on the first day after the merge.
