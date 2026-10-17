# 6b part 2: the dealer charts, the three sentences, the scorecard's pre-registration, the 09:45 and 12:30 captures (session A, 17 Oct 2026)

**Merge order: after `6b-dealer-1`, in the second stitched chain.** Branch `6b-dealer-2` is cut from the tip of `6b-dealer-1` (`65fa5ef`), so it carries part 1 and the st-r5 line beneath it, and merges after them. `vol-event-52` (Batch 9 item 52) is cut from this branch's tip and merges after it. Branch-only: nothing merged, deployed or run on the box, and no unit enabled or started. Session B's crypto-tranche-a branches, Monday's chain, `post-friday-fixes` and chester-meme were not touched.

**The spec** is `docs/briefs/dealer-positioning-brief-2026-10-09.md` (v2), ratified 16 Oct 2026, sections 3 to 5 and 8, with the rulings of 17 Oct on the part 1 report.

## Part 0 of the paste

1. **`6b-dealer-1`'s CI:**
   - `d7c1593`: run 39033223933, **green**;
   - the earlier `e9b7fc9`: run 39033119597, failed one check, the inherited `validate_secrets` refusal.
   - Both are recorded in its notes (`65fa5ef`).
2. **`st-r5-audit` repaired.** The fix `d7c1593` is cherry-picked as `c60c458`, without the 6b notes it also touched. That branch's notes record the failed run and the repair. `validate_by_hand_audit` 17/0. CI: see the section at the end.
3. **Batch 9 filed.** The file's SHA-256 over LF matched `07030e02…7fd1`. It is on branch `docs-batch-9` from `origin/main` (`e20df42`) as `docs/change-order-signal-triage-batch-9-2026-10-17.md`. The committed blob hashes to the same value. Docs only; Ari merges it with Monday's chain.

## The rulings of 17 Oct, as applied

| # | Ruling | Applied |
|---|---|---|
| 1 | Horizon windows sum whole listing buckets, as built | no change |
| 2 | "Expiry session" is the monthly third Friday (the pinned hypothesis, the forced-flow setup) | `dealer_block.expiry_sessions: monthly`; `scorecard_row`'s `is_expiry_session` is the third Friday (`carried_0dte` keeps the capture's own fact); the registration records the choice |
| 3 | The close's summary targets the next session | no change |
| 4 | The setup thresholds stand | no change |
| 5 | The Weekly's put wall moves to the OTM wall | `weekly_sections.flags_for` reads the morning OTM walls, call and put; a card with only the all-strike walls is None |
| 6 | SPY full, QQQ and IWM one line | no change |
| 7 | st-r5-audit repaired | Part 0, above |

## 1. The charts (brief section 3)

**`tools/dealer_charts.py`'s `draw_*` functions** now take an `ax`. Given one, they draw into it and return what they drew, so a chart reconciles with the tables; without one, they write the PNG as the CLI always did. `daily_cascade/charts.py` imports them in `dealer_chart(cid, profile, …)`.

**Changes inside `dealer_charts.py`:**
- **Figure 1** marks the OTM call wall and the OTM put gamma wall as the walls (audit F5). The all-strike peaks are no longer drawn as walls.
- **Figure 2** reads the profile the engine now stores (`gamma_profile`), and falls back to re-pricing from the chain CSV for older captures.
- **Figure 3's left panel** is the exclusive bands' call- and put-gamma masses (0DTE, 1–7, 8–45, > 45), with a settled 0DTE band labelled "settled, excluded". The right panel is the hedge rolling off by expiry, magnitude only (F3).
- **Figure 4** is the hedge book by horizon, a cumulative size.
- **Every figure's stamp** carries the capture time, settled or intraday, and "OI as of prior close".
- **The profile's footnote** no longer says "amplify"/"dampen"; it reads "leans with the move" / "leans against it".
- **The style dict (`RC`)** is applied by the CLI and inside `charts.py`'s `rc_context`, never at import, so it no longer restyles the report's other charts.

**The engine** (`tools/exposure_compute.py`) stores:
- `gamma_profile`: 81 hypothetical spots across ±8%, net GEX at each, sticky strike;
- `overall.net_gex_up_1pct` and `net_gex_down_1pct`, the asymmetry for sentence 1 and figure 2;
- `oi_vintage: prior_close` on every capture.

This adds 0.15 s per capture on the fixture chain.

**Where each chart prints, and what it displaces.** Each report's cap is unchanged.

| Chart | Report, section | Figures | Displaces |
|---|---|---|---|
| D2 | the close, Mechanics | 2 (the close's one dealer chart) | nothing on most days. The plan is C1, D2, C2 under the cap of 3. On a day with C3 (an open contradiction or deep Plumbing) and no fired trigger, **C2** is set aside; a fired trigger lifts the cap to 4 and all print |
| W12 | the Weekly, Mechanics, after W7 | 2, 1, 3, as one panel | **W10** (the probability path), the last in the Weekly's ten. With W6 open and no trigger, W11 too |
| M12 | the Monthly, Mechanics | 2, 1, 3, 4, as one panel | **M8** when all thirteen render (it is first in the drop order and does not render until scenario set #1 exists). Otherwise nothing |
| figure 1 in the 09:45 slot | — | — | **waits:** there is no 09:45 report; the 09:45 capture exists from this branch (below) |
| figure 5 | — | — | part 3 |

**The dealer charts enter a plan only when the edition reads the computed profiles.** The payload's `computed_dir` is set by the close's, the Weekly's and the Monthly's payload builders. Every gate's synthetic edition keeps its plan exactly as before, so `validate_weekly_edits`, `validate_st_r5_index` and `validate_monthly_stack`'s plan checks hold unchanged.

## 2. The three fixed sentences (brief section 4)

**No new model path.** The close's Mechanics data carries `dealer_sentences`, the facts of the three sentences, each figure as the tables print it:
1. the gated regime, net-to-gross, the zero-gamma level and its distance, and net GEX at spot, +1% and −1%;
2. the two OTM walls, the peak-gamma strike and the expiry that carries it, the next expiry and the size rolling off at it;
3. the setups for the target session, each with its invalidating level, or "no setup".

**The frame.** When that block is present, `stack_prose.section_prompt` appends `DEALER_SENTENCES_NOTE`: three sentences, in order, citing only those figures. The numeral audit checks them as it checks every paragraph.

**The flag-word audit**, extended to "dampened":
- **`dealer_block.flag_word_faults`** allows "pinned", "held", "amplified" and "dampened" only in a sentence that names a session (ISO date, "14 Oct", or a weekday of the week) whose flag for that word is True.
- **The close** carries no scored session at prose time (its flags are computed after its prose), so any flag word in its Mechanics paragraph is withheld and retried.
- **The Weekly** reads its scored sessions (`dealer_week`).
- **The Monthly's** `dealer.flag_word_faults` gains "dampened" and its count.
- **The Weekly's flags** gain `dampened`: a regime session (the morning net-to-gross at the gate) in positive gamma whose range came in at or under 0.8 × implied, otherwise None.

## 3. The pre-registration and the rate printer (brief section 5)

**The registration:** `docs/ledgers/dealer-scorecard-preregistration-2026-10.md`, dated 17 Oct 2026, never edited. Its SHA-256 over LF is `7f3e1f24…b2717`, recorded in `tools/validate_dealer_block.py`. A change is a new registration.

**What it registers:** the brief's five hypotheses as six tests:
- H1 dampened;
- H2 amplified;
- H3a call wall held and H3b put wall held;
- H4 pinned, on the monthly third Friday only, with max pain as the control;
- H5 flip crossing.

For each it records the mechanism, eligibility, outcome, window, base rate and price-action baseline. It also records the 120/120 formation and test split, the promotion rule (the test interval excludes both the base rate and the baseline after Benjamini–Hochberg at 0.10, with the formation estimate on the same side) and the demotion rule.

**The config** (`config/reporting_stack.yaml` `dealer_scorecard`) mirrors it, and the gate holds the two to each other.

**`altdata/dealer_scorecard.py`:**
- **It scores the stored rows.** An ineligible session is None, never False, and an outcome needing later sessions is None until they are stored.
- **The rate printer** (`rate`, `rate_line`, `rates_table`) prints k/n, a **Wilson 95%** interval, the base rate and the baseline each with its n, and sessions and episodes.
- **The floors:** under **20** scored sessions only the count of scored sessions prints; under **120** eligible sessions every line ends "no rate is a decision".
- **The formation and test position** is reported. None is promoted, so nothing grants a reading in T3. Wiring the printer into the Weekly and the Monthly is part 3's.

**The Weekly's descriptive flags** (`weekly_sections.flags_for`, also read by the Monthly's retrospective):
- **The walls are the morning OTM walls** (ruling 5).
- **A wall the session never approached is None**, not False.
- **"dampened" is added.**
- **"pinned"** (the close within 0.25% of max pain, any session) **and "amplified"** (the flip crossed and the range at or over 1.2 × implied) **keep their existing definitions**, so the Monthly's counts don't move under its gate. The registered H4 and H2 are separate tests. That is needs-you 1.

**Base rates and baselines, in brief** (the registration has the exact definitions):

| Test | Base rate | Baseline |
|---|---|---|
| H1, H2 | the range threshold met, over all sessions | persistence: met again the session after it was met |
| H3a, H3b | the close at least 0.25% back from the session's extreme | the nearest $5 round number above / below the prior close, the same approach and outcome |
| H4 | the close within 0.25% of the morning peak strike, any day | the close within 0.25% of the nearest $5 round number, on the eligible sessions |
| H5 | next-three realised vol above prior-ten, over all sessions | the same on sessions whose range contained the 20-session moving average |

## 4. The capture units

**`altdata/dealer_capture.py`** (`python -m altdata.dealer_capture run --slot 0945|1230`):
- It snapshots the options universe from **Yahoo** and SPX and SPCX from **Massive** (ingestion only; their Greeks stay deferred, as at 16:10).
- It computes the engine's exposure JSON from **each snapshot it just wrote**, beside the 16:10 profiles. `newest_chains`, which the 16:10 pass uses, would pick the snapshot closest to the settlement time instead.
- OI is stamped `prior_close`, and nothing is appended to the release ladder.
- The 12:30 slot then runs the gates.

**`daily_cascade/midday_gate.py`**, the 12:30 alert-only slot:
- **A registry of gates**, each a pure function of the stored 12:30 capture and the morning profile.
- **The one gate here, `dealer_flip_cross`:** by 12:30 spot is at least 0.10% (the continuation setup's confirmation) through the morning zero-gamma level, and both captures' regimes pass the net-to-gross gate. That is a regime transition, which the cadence document's Alerts row names.
- **When every gate is closed**, it writes nothing and calls nothing.
- **When one opens**, it writes the alert: the open gates' code-written lines, as JSON, in `~/chester-data/outbox/midday/` or `$CHESTER_ALERT_DIR`.
- **No model is called**, and how the alert reaches Ari is needs-you 4. Item 52's VIX gate is added to the registry on `vol-event-52`.

**The units**, in `deploy/systemd`:
- `chester-dealer-0945.service`/`.timer` and `chester-dealer-1230.service`/`.timer`, via `scripts/run_dealer_capture.sh <slot>`. That wrapper does the pull, the calendar guard, its own lock, status and heartbeat files, and exits 0 on a non-session day.
- **They follow aud-2's conventions:**
  - `EnvironmentFile=-…/.env` (Massive's key);
  - the sandbox, and `ReadWritePaths` including `-%h/chester-data` for the outbox;
  - `MemoryHigh=0.8G`, `MemoryMax=1G`;
  - `OOMScoreAdjust=300`: a capture, like the EOD pass, cannot be fetched again;
  - `Persistent=false`, Mon–Fri at the minute in America/New_York.
- **Their timers are not in `DEPLOY_TIMERS`.** The self-deploy copies the files but enabling them is Ari's.
- **`tools/validate_systemd_units.py`** checks them as a capture set outside the 8 GB sum (they run when no heavy unit does), with self-tests for a missing cap, a score level with the reports, a catch-up timer and a wrong minute.

**The SPY recompute every 5 to 15 minutes: listed, not built.** On 17 Oct the box stays at 4 GB, while aud-2's caps were written for 8 GB. A recompute loop beside the two captures, the close and the EOD pass would need its own cap inside a budget that has to be recomputed first (part 3's memory-cap item). It is part 3's to place, after the caps follow the machine.

## 5. Registry, catalogue, units

- **New metrics:** `exposure.net_gex_up_1pct`, `exposure.net_gex_down_1pct` (`usd_per_point`).
- **`non_metrics`:** `gamma_profile` (a container), `band_pct`, `spots` and `oi_vintage`.
- **The registry gate** reads inside `gamma_profile`: 122 exposure fields emitted, 0 unregistered.
- **The catalogue** gains `altdata.dealer_capture` (domain options).
- **No new store key:** the captures write the engine's JSON, as the 16:10 pass does.
- **CLAUDE.md:** the dealer paragraph gains part 2. The count line is recounted: **eighty-nine code gates (eighty-six Python, three shell), six data gates**, unchanged, since this part adds no gate file.

## Gates

Run locally, one at a time, only those this branch writes or changes:

| Gate | Result | Part 2's groups |
|---|---|---|
| `tools/validate_dealer_block.py` | **112/0** | K the three charts render (under 150 KB, legible at 400 px), reconcile with T1, the bands, the ladder and the hedge book, are stamped, say why when unavailable, carry no direction or flag word, and hold the plans and budgets. L the sentences' facts are the tables' figures; the close's frame asks for them; the flag-word audit at the close, the Weekly and the Monthly, "dampened" included. M the registration's hash and its mirror in config; Wilson for 7/20 by hand (0.181 to 0.567); the third Friday; eligibility None; the floors; six registered, none promoted; the Weekly's dampened flag. N a 09:45 capture from its own snapshot, nothing on the ladder; the 12:30 gate opens on a crossing and stays closed 0.07% through, under the gate and with no capture, writing nothing and calling no model |
| `tools/validate_systemd_units.py` | **126/0** | the capture units' caps, OOM order, sandbox, wrapper, calendar, and their absence from `DEPLOY_TIMERS`; four self-tests |
| `tools/validate_weekly_edits.py` | **91/0** | the flags fixture carries the OTM walls; a card with only the all-strike walls, and a wall never approached, are None |
| `tools/check_registry.py` | **OK** | 122 fields |

Left to CI: every other gate, and those that render a PDF (`validate_stack`, `validate_monthly_stack`). `validate_monthly_stack`'s retrospective now sees "held" as None on its cards (they carry no OTM walls) and a "dampened" row in its summary table. Its pinned and amplified counts are unchanged.

## Box commands, for Ari

Inside a window (weekdays 09:05–15:40 or 17:20–23:30 ET), **after Thursday's merge**. The self-deploy copies the four unit files within 30 minutes of the merge reaching main.

```
cd ~/chester-reports
git log -1 --oneline
systemctl --user list-unit-files 'chester-dealer-*'      # the four files are there
systemctl --user enable --now chester-dealer-0945.timer chester-dealer-1230.timer
systemctl --user list-timers 'chester-dealer-*'
```

**The first captures**, on the next session after enabling:

```
tail -n 40 ~/logs/dealer_capture-$(date +%Y-%m).log
ls data/computed/$(date +%F)/SPY_*_exposure.json
.venv/bin/python -m daily_cascade.dealer_block show --date $(date +%F)
ls ~/chester-data/outbox/midday/           # empty unless a 12:30 gate opened
```

**Optional, before enabling: one capture by hand** (inside the window; it writes a real capture and its profiles):

```
.venv/bin/python -m altdata.dealer_capture run --slot 0945 --symbols SPY
```

Nothing restarts. No running unit changes. The 16:10 EOD pass is untouched.

## Files shared with the open branches

Trial merges (`git merge-tree`, nothing committed) of this branch against `6e-releases`, `6e-digital`, `6e-rest`, `6e-metric-lenses`, `crypto-tranche-a-1`, `crypto-tranche-a-2`, `st-r4-tranche-1b`, `st-r6-es-block`, `aud-3b-security-master` (Monday's chain) and `post-friday-fixes`, compared with the same merges from `6b-dealer-1`'s tip: **this branch adds no conflict with any of them.**

The files it touches that other open branches also touch:
- `CLAUDE.md`;
- `config/reporting_stack.yaml` (the `dealer_scorecard` block, `expiry_sessions`);
- `metrics_registry.yaml`;
- `daily_cascade/stack.py` and `daily_cascade/stack_close.py` (the 6e branches, `st-r4-tranche-1b`, `st-r6-es-block`);
- `daily_cascade/weekly_stack.py` and `weekly_sections.py`;
- `monthly_macro/stack.py`, `charts.py` and `dealer.py`;
- `daily_cascade/stack_prose.py` (`post-friday-fixes`' filler rule, in other hunks).

All merge cleanly in the trials.

## What part 3 takes next

- T3, the horizon matrix, with "registered hypotheses: n, none promoted".
- The Weekly's T2 per horizon and its fourth sentence.
- The Monthly's dealer retrospective with figures 4 and 5.
- Figure 5, the scorecard chart, fed by `dealer_scorecard.rates_table`.
- The FlashAlpha vendor line and writer.
- ES conversion (ST-R6.45c).
- The memory caps following the machine, then the SPY recompute's place.

## Needs you

1. **The descriptive flags against the registered tests.** The Weekly's "pinned" (max pain, any session) and "amplified" (flip crossed) keep their definitions; the registered H4 (peak strike, third Friday) and H2 (regime-negative) are separate. Moving the descriptive flags onto the registered definitions now would change the Monthly's counts and its gate. Say if they should move now, or after the formation window.
2. **What each dealer chart displaces:** C2 on some closes, W10 every Weekly (and W11 with W6), M8 in the Monthly. The alternatives are a larger cap, or a dealer chart that replaces a different chart (W7 shares Mechanics with W12).
3. **The 12:30 gate's one dealer trigger:** spot 0.10% through the morning zero-gamma level, both regimes gated. Keep, retune, or drop it in favour of item 52's VIX gate alone.
4. **How the 12:30 alert reaches you.** It is a JSON file in `~/chester-data/outbox/midday/`; no email, no push. Say which channel, under the "no alert beyond the slot's own" rule.
5. **The capture units' caps** (0.8G/1G, OOM 300) are session-set and sit outside the 8 GB sum. Part 3 recomputes every cap for the 4 GB box.
6. **The SPY 5-to-15-minute recompute** is listed, not built (memory): part 3 or later.

## CI

| Branch | Commit | Run | Result |
|---|---|---|---|
| `6b-dealer-1` | `d7c1593` | 39033223933 | green (recorded in its notes) |
| `st-r5-audit` | `c60c458` (the repair) | 39036555800 | **green**: every branch in the second chain is green on its own |
| `docs-batch-9` | `e20df42` | 39036581128 | **green** |
| `6b-dealer-2` | `ada7cb2` | 39038449525 | **failed**, three gates, all this branch's own (below) |
| `6b-dealer-2` | the fix commit | recorded at the next read | |

**The first run's three failures, and the fix:**
- **`validate_weekly_stack` and `validate_weekly_opener`:** the flag-word audit read "held" as the flag word in ordinary prose. The fixtures' generic paragraph says "the relationships that held at the start of the week held at its end". So the Weekly's Mechanics was withheld and retried, adding model calls (11 against 9) and spoiling the opener's retry count. **Fix:** "held" is the flag word only in a sentence about a dealer level (a wall, the flip, a strike, max pain). Pinned, amplified and dampened always count. `validate_dealer_block` group L gains the plain-English case.
- **`validate_monthly_stack`:** the Monthly's real payload builder now sets `computed_dir`, so M12 entered the gate's plan with no profile to draw.
  - **Fix:** a dealer chart enters a plan only when a settled SPY profile exists under the directory (`dealer_block.chart_dir`), for D2, W12 and M12 alike.
  - **A bug the fix also caught:** the Weekly never set `dealer_computed_dir` on its edition, so W12 could not have printed. It now does, from the payload.
