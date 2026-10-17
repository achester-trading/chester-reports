# 6b part 3: T3, the Weekly and Monthly wiring, figure 5, the FlashAlpha vendor writer, dealer levels in ES, the memory caps (session A, 17 Oct 2026)

**Merge order: after `6b-dealer-1`, `6b-dealer-2` and `vol-event-52`, in the second stitched chain.** Branch `6b-dealer-3` is cut from the tip of `vol-event-52` (`cd8bd07`), with `vol-event-52`'s CI fixes merged in (`1663521`), so it carries parts 1 and 2, item 52 and the st-r5 line, and merges after them. Branch-only: nothing merged, deployed or run on the box, and no unit enabled or started. Session B's crypto-tranche-a branches, Monday's chain and chester-meme were not touched.

**The spec** is the dealer-positioning brief v2, sections 2 (T3), 3 (figure 5), 5.6 (the vendor line) and 8, with the rulings of 16 Oct (the vendor writer is part 3; the two chat-side FlashAlpha tasks retire once it is live; the MSTR/MSCI watch reads from the store) and 17 Oct (the box stays at 4 GB, so the caps follow the machine), and item 45's ST-R6.45c.

## Step 0: the CI reads

Each was read once; every failure was this line's own and is fixed.

| Branch | Run | Result | Fixed in |
|---|---|---|---|
| `6b-dealer-2` (`345f1d3`) | 39039815290 | **failed**, `validate_audit_2`: the chart-dir helper landed between the Monthly's `@model_meter.metered` decorator and `produce()` | `549619d` (6b-dealer-2), recorded in its notes (`ebbe8fd`) |
| `vol-event-52` (`cd8bd07`) | 39039856971 | **failed**: `validate_prices` (the basket is 108, not 106); `validate_security_master` (^VIX9D and ^VIX6M had no master entry); `validate_audit_3a` (CLAUDE.md's 106; the new block members; the count self-test at the one-word "ninety"); `validate_audit_2` (the decorator, inherited) | `1663521` (vol-event-52), recorded in its notes; `validate_audit_3a` 85/0 and `validate_prices` 101/0 locally |

The fixes' own runs are recorded in the CI section at the end.

## 1. T3, the horizon matrix

`daily_cascade/dealer_block.t3`, per horizon window:
- the gamma sign with net-to-gross, gated at 0.10;
- the magnitude ($/1%) against the series' own five-year percentile, with its n. The series is `dealer.window_gamma`, written by the close for each settled capture (instrument `<symbol>:<window>`), so the percentile builds from the merge on and says "no stored history yet" until then;
- the nearest major level (the OTM walls and the zero-gamma level) and its distance;
- the implied one-day range: spot × IV × √(1/252), with SPY's own ATM 30-day IV, else the VIX labelled proxy.

**The close** prints T3 as lines in Mechanics, stamped "Every level here is inferred, not observed; OI as of prior close". **The Weekly** prints it as a table. Both end on **"registered hypotheses: 6, none promoted"**, with no synthesis sentence until the registration promotes one.

## 2. The Weekly and the Monthly, and figure 5

**The Weekly** (`daily_cascade/dealer_weekly.py`, called from `weekly_stack.mechanics_week` when the payload names `computed_dir`; gate payloads do not):
- T3 as a table;
- **T2 per horizon**: each window's OTM walls, zero-gamma level and peak-gamma strike;
- **the registered hypotheses' running evidence**: `dealer_scorecard.from_store` over every stored row, k/n with Wilson intervals, base rate and baseline, or the floor's line;
- **the vendor line** (below);
- **the facts of the three sentences plus the fourth**. The fourth is the week against the Monday read: the regime Monday's morning profile read and where the week closed against Monday's zero-gamma level and OTM walls, from the scorecard rows only. `FOURTH_NOTE` asks the existing narrative step for it, behind its audits.

**The Monthly:** Mechanics gains "Registered hypotheses (the scorecard)" beside the retrospective, and M12 carries figures 4 and 5.

**Figure 5** (`tools/dealer_charts.draw_scorecard`): each registered hypothesis's k/n bar with its Wilson interval, the base rate (–) and the baseline (×). A hypothesis under the printing floor draws no bar and says "under 20 scored".
- **Its place:** it prints inside the W12 panel (figures 2, 1, 3, 5) and the M12 panel (2, 1, 3, 4, 5), so it costs no chart slot. Each budget stands, and nothing further is displaced beyond what part 2 recorded.

## 3. The FlashAlpha vendor writer

**`altdata/sources/flashalpha.py`**, run by `chester-flashalpha.service`/`.timer` at **16:25 ET** on weekdays: after the 16:10 capture, before the 16:45 close.
- **Symbols:** SPY, QQQ, IWM and MSTR (all in the engine's universe), two calls each:
  - the levels endpoint `/v1/exposure/levels/{symbol}`, the one `tools/cross_check.py` has read since 4 Sep;
  - the probe's registered `/v1/exposure/gex/{symbol}`.
- **Stored point in time** (observed on the session, available at the response's capture instant), instrument = the symbol:
  - `dealer.vendor_gex_per_1pct`, compared with our `dollar_gamma_per_1pct`;
  - `dealer.vendor_dex_raw`, compared with the engine's new raw-signed `exposure.dex_raw_notional` (Σ Δ·OI·100·S, each contract's own delta, the definition the 9 Oct ledger established);
  - `dealer.vendor_vex`, **stored with its flag, unreconciled**, never compared;
  - `dealer.vendor_gamma_flip`, `dealer.vendor_call_wall`, `dealer.vendor_put_wall` and `dealer.vendor_spot`.

  A field the response does not carry is absent.
- **The key** is `FLASHALPHA_API_KEY`, read through `altdata.secrets` by its existing name with `FLASHALPHA_BASE_URL`. It is never printed: errors pass through `secrets.redact`, and the summary says only `key_configured`. No key configured, no call.
- **The quota:** a session-set daily budget of **30 calls** (the Basic plan allows 250 a day, shared with the chat; eight a day is the writer's need), counted in `~/.chester/flashalpha_calls.json`. Past it, no call is made, and the run says so.
- **What I could not verify from here.**
  - The summary endpoint answers **403, "requires the Growth plan"** (read once through the FlashAlpha connector on 17 Oct).
  - A second connector read, of the levels endpoint, was refused by the session's permission check, and I did not retry it.
  - **So the GEX endpoint's field names are unverified.** The parser reads the names listed in `config/flashalpha.yaml` and stores only what it finds; the first box run's summary lists what was absent (needs-you 2).
  - The levels response's shape is the one `cross_check.py` already parses.
- **The divergence data gate** `tools/validate_vendor_divergence.py` (`GATE_KIND = "data"`, in `DATA_GATES`) reads the newest session both sides hold for SPY and flags each pair past its session-set threshold, with its reason. A gap is a question, never a correction. It skips in CI and says NOT VALIDATED without a store.
- **The vendor line** in the Weekly's Mechanics (`flashalpha.vendor_line`) reads the stored series and never fetches.
- **The source policy.** `source_registry.yaml`'s `flashalpha` entry moves from `allowed_reports: []` to `[weekly_tactical]`, with its note amended: the line prints only as a gap against our own figure (needs-you 3).

**The two chat-side tasks this retires, and when.** **The Wednesday pull** (the chat pulls FlashAlpha's levels and summary for the cross-check) and **the Thursday reconcile** (the chat reconciles them against the stored chain) retire once the writer is live: from the first week it stores five sessions for SPY and the divergence gate has read them (needs-you 1). **The MSTR/MSCI event watch** (Batch 8 section 5, filing note 7) reads its FlashAlpha figures from the store from the writer's first run. Its line to read is:

```
dealer.vendor_gamma_flip / _call_wall / _put_wall / _gex_per_1pct / _dex_raw, instrument MSTR, observed on the session
```

Only its message stays chat-side.

## 4. ST-R6.45c: dealer levels in ES

**`altdata/dealer_es.py`:**
- **The method.** Each engine level (the zero-gamma level, the OTM walls, the peak-gamma strike, max pain) is carried to ES through **one same-minute ratio**: the ES front month's 5-minute bar ending 16:00 ET over SPY's spot in the settled profile.
  - It uses SPY's levels because the engine's SPX Greeks are still deferred behind the solver gate.
  - The ratio carries the SPX/SPY scale and the front month's basis in one number. It is front month only, with the contract the ES block records each morning named beside it.
- **The error band:** two standard deviations of the ratio's daily relative change over the prior 20 sessions, applied to each level in points. Under five changes stored it says it is not yet computable.
- **Printed once:** the method and the band print once per edition (`note`).
- **The row** is `Dealer levels in ES (ESZ6): zero-gamma …(±…); OTM call wall …; … Inferred, not observed.`

**The ES block itself is session B's** (`altdata/es_block.py` on `st-r6-es-block`), not in this line, and this paste does not name that branch. So this branch carries the conversion, its fixture and the function the row calls, but **does not edit the block**. At stitching, the block's dealer field replaces its constant `DEALER_PENDING` ("dealer levels in ES: after the 6b engine") with the call below, and its own gate's two checks on that constant move to the row's shape. That is needs-you 4, for whichever session stitches the two. Read-only against the block's config; nothing else in it changes.

```
dealer_es.convert(profile, dealer_es.es_at(es_bars, day), dealer_es.ratio_history(es_bars, spy_closes, prior_sessions), contract)["row"]
```

## 5. The memory caps follow the machine

**Every capped unit now carries percentages of physical memory.** Each percentage equals AUD-2's absolute 8 GB figure, which is kept in that unit's comment. `deploy/systemd/README.md` section 13 has the table.

| Unit | MemoryHigh / MemoryMax | at 4 GB (the box) | at 8 GB (AUD-2) |
|---|---|---|---|
| chester-eod, chester-daily-close | 20% / 25% | 0.8G / 1.0G | 1.6G / 2G |
| chester-weekly, chester-monthly | 25% / 31% | 1.0G / 1.24G | 2G / 2.48G |
| chester-voices, chester-restore-drill | 10% / 12% | 0.4G / 0.48G | 0.8G / 0.96G |
| chester-backup | 15% / 19% | 0.6G / 0.76G | 1.2G / 1.52G |
| chester-dealer-0945, -1230 (part 2) | 10% / 12% | 0.4G / 0.48G | 0.8G / 0.96G |
| chester-flashalpha (this part) | 4% / 5% | 0.16G / 0.2G | 0.32G / 0.4G |

The six heavy units' caps sum to 5.72G at 4 GB and 11.44G at 8 GB, inside 1.5 times either machine.

**`tools/validate_systemd_units.py` holds the rule:**
- every cap is a percentage, and an absolute cap on any unit fails;
- MemoryHigh sits under MemoryMax;
- the caps' sum is checked at 4 GB and at 8 GB;
- each 8 GB equivalent matches AUD-2's within a rounding step (backup is 19%, not 18%, for that reason).

It runs self-tests for an absolute cap brought back, a percentage off the 8 GB case, and the vendor unit at the wrong minute: 134/0.

**The 4 GB figures are tight for the Weekly and the Monthly:** 1.24G at MemoryMax for ten or twelve charts and the PDF. That is needs-you 5.

## 6. Registry, catalogue, units, the count

- **Metrics:**
  - `exposure.dex_raw_notional` (usd);
  - `dealer.window_gamma` (usd_per_1pct, source daily_close);
  - the seven `dealer.vendor_*` keys (source `flashalpha`; usd_per_1pct, usd, usd_per_volpt, price).
- **The catalogue** gains `altdata.sources.flashalpha`.
- `check_registry` OK.
- **CLAUDE.md:** the dealer paragraph gains part 3 and the caps rule. The count line is recounted to **ninety-one code gates (eighty-eight Python, three shell) and seven data gates**. The Makefile counts 91 / 88 / 7, and the count gate `validate_audit_3a` holds the data-gate count too: 85/0.

## Gates

Run locally, one at a time, only those this branch writes or changes:

| Gate | Result | What it holds |
|---|---|---|
| `tools/validate_dealer_vendor.py` (new; Makefile) | **28/0** | A T3 against the windows by hand (the percentile of 40 stored values, the implied range 680 × 15% × √(1/252)), the no-promotion line, T2 per horizon, the stored window rows. B figure 5 from a fixture ledger (14/24 with its Wilson interval; a hypothesis under the floor draws no bar), inside W12 and M12 under the cap. C the writer on stored fixtures (`tests/fixtures/dealer_block/flashalpha_levels.json`, `_gex.json`, both synthetic): seven rows point in time, an absent field absent, a run of eight calls and 28 rows read back, the budget refusing past it, a redacted error, no key no call, **the key in no output**. D the divergence: GEX past and inside 0.50, DEX past and inside 0.15, the flip in percent of spot, VEX never compared, the vendor line. E ES: the flip × the same-minute ratio by hand, the band by hand, the row and note, no ES price, the 16:00 bar, the band not yet computable |
| `tools/validate_dealer_block.py` | **112/0** | group H: Mechanics now carries T3 between T2 and the summary, and every table holding a figure is stamped; group K: W12 and M12 carry figure 5 |
| `tools/validate_systemd_units.py` | **134/0** | the caps rule at 4 and 8 GB, the vendor unit, and the self-tests |
| `tools/validate_audit_3a.py` | **85/0** | the count line (91 / 88 / 7), after the merge from `vol-event-52` |
| `tools/check_registry.py` | **OK** | |

`tools/validate_vendor_divergence.py` is a data gate: CI skips it, and it runs on the box. Every other gate, and those that render a PDF, are left to CI.

## Box commands, for Ari

Inside a window (weekdays 09:05–15:40 or 17:20–23:30 ET), **after Thursday's merge**. The self-deploy copies the unit files within 30 minutes of the merge reaching main, including the nine whose caps moved to percentages. Those are oneshots, so no restart should be pending; if the heartbeat names `restart_pending`, the restart is yours.

```
cd ~/chester-reports
git log -1 --oneline
.venv/bin/python -m altdata.secrets FLASHALPHA_API_KEY FLASHALPHA_BASE_URL   # set/missing only, never values
systemctl --user list-unit-files 'chester-dealer-*' 'chester-flashalpha*'
systemctl --user enable --now chester-dealer-0945.timer chester-dealer-1230.timer chester-flashalpha.timer
systemctl --user list-timers 'chester-dealer-*' 'chester-flashalpha*'
systemctl --user show chester-weekly.service -p MemoryMax -p MemoryHigh      # the 4 GB caps, resolved
```

**The first captures and readings to read**, on the next session after enabling:

```
tail -n 40 ~/logs/dealer_capture-$(date +%Y-%m).log                     # 09:45 and 12:30
.venv/bin/python -m daily_cascade.dealer_block show --date $(date +%F)
journalctl --user -u chester-flashalpha.service -n 40 --no-pager          # 16:25: the summary lists stored and absent fields
.venv/bin/python tools/validate_vendor_divergence.py                     # the data gate, after 16:25
```

## Session-set thresholds and budgets

| Setting | Value | Reason |
|---|---|---|
| vendor symbols | SPY, QQQ, IWM, MSTR | the close's three, and MSTR for the event watch |
| daily call budget | 30 | Basic's 250 a day is shared with the chat; the writer needs 8 |
| GEX divergence | 0.50 relative | 15 minutes on a steep profile moves the headline by tens of percent (ledger 9 Oct) |
| DEX divergence | 0.15 relative | reconciled to 1% on the same inputs; room for the 15-minute gap |
| flip, walls | 1.0%, 1.5% of spot | about two SPY strikes near 680 for the walls |
| T3 percentile window | 1,260 stored sessions (five years) | the series' own five-year window, as ruled; its n prints |
| ES band | 2σ of the ratio's daily change over 20 sessions | the ratio's own variation; five changes before it prints |
| caps | the percentages above | AUD-2's 8 GB figures as fractions of the machine |

## Files shared with the open branches

Trial merges (`git merge-tree`, nothing committed) against `6e-releases`, `6e-digital`, `6e-rest`, `6e-metric-lenses`, `crypto-tranche-a-1`, `crypto-tranche-a-2`, `st-r4-tranche-1b`, `st-r6-es-block`, `aud-3b-security-master` (Monday's chain), `post-friday-fixes` and `docs-batch-9`, compared with the same merges from `vol-event-52`:
- **This branch adds no conflict with any of them.**
- **Session B's branches share these files with this one:**
  - `CLAUDE.md` (the count line: recount at stitching);
  - `metrics_registry.yaml` and `source_registry.yaml` (the `flashalpha` entry's `allowed_reports`);
  - `daily_cascade/stack.py`, `weekly_stack.py` and `stack_prose.py`;
  - `deploy/systemd/*.service` (the caps, on the same lines Monday's chain's `aud-2` set);
  - `deploy/systemd/README.md` section 13.
- **`st-r6-es-block`** shares no file. Its `altdata/es_block.py` takes the one-line stitch above.

## Needs you

1. **When the chat-side FlashAlpha tasks retire.** I propose the Wednesday pull and the Thursday reconcile retire from the first week the writer stores five sessions for SPY and the divergence gate has read them. Confirm, or name the date.
2. **The GEX endpoint's field names are unverified.**
   - The summary endpoint needs the Growth plan, and a second connector read was refused by this session's permission check. The writer stores what it finds, and the first 16:25 run's summary lists the absent fields.
   - If GEX, DEX and VEX come back absent, the choices are a plan with the summary endpoint, or the vendor line reading levels only.
3. **`flashalpha` may now reach the Weekly**, as a cross-check line against our own figures, per the brief's section 5.6. It was `allowed_reports: []`. Confirm the policy change.
4. **The ES block's dealer row is a one-line stitch** in session B's `altdata/es_block.py`, plus its gate's two checks on the pending constant. Say which session makes it when the two branches meet.
5. **The 4 GB caps:** the Weekly and the Monthly at 1.24G MemoryMax, the close and the EOD pass at 1.0G. They follow the percentages AUD-2 chose for 8 GB; a 4 GB box may need the reports a larger share and the backup a smaller one. The first Weekly after the merge (Sunday 05:00) is the test, and its log shows whether it hit the ceiling.
6. **The SPY 5-to-15-minute recompute** (part 2's listed item) stays listed: at 4 GB the captures, the close and the EOD pass already share the headroom.

## CI

| Branch | Commit | Run | Result |
|---|---|---|---|
| `6b-dealer-2` | `549619d` / `ebbe8fd` | recorded at the next read | |
| `vol-event-52` | `1663521` | recorded at the next read | |
| `6b-dealer-3` | this commit | recorded at the next read | |
