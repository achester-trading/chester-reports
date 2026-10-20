# a47-chain3: session A's third chain (19 Oct 2026)

**This branch builds on chain-2 and merges in the third chain.** It was branched from chain-2's tip `e0a8cc0` after Part 0's push. chain-2 has since gained one commit, `ab27c07` (the STITCH COMPLETE line, notes only), and that tip is merged in before the last push.

Branch only. I pushed this branch and nothing else, ran nothing on the box, and enabled or started no unit. Nothing is merged to main.

## The items

### 1. Ruling 4 of 19 Oct, on the opening-setup report

**The pre-market line** sits under the gauge in the 07:00 anchor's "Prior close — dealer surface" block.
- **What it reads:** ES's newest overnight bar for the session, put into SPY's terms.
- **The basis is the 23-hour chart's own** (W7, `daily_cascade/charts.py`): SPY's 09:30 open over ES's 09:30 open, applied ES to SPY. The line calls W7's `es_overnight` and `es_at_open`; there is no new conversion method.
- **The basis session:** at 07:00 the day's own 09:30 has not happened, so the line uses the newest session before it that carries both opens, and names that session.
- **"Not available"** prints when ES has no overnight bar, or when no session carries both opens, each with its reason.
- **Sources:** the bars the 06:45 job stores (`es` and `spy`, 5-minute), read as of the cutoff. Nothing is fetched.
- **Budget:** one line; nothing displaced (`config/opening_setup.yaml`).
- **Code:** `opening_setup.premarket`, `premarket_from_store`, the payload's `opening_premarket`.

**SPX and SPCX.** Both join OS-9 (the largest OI builds) and OS-10 (the most-active table) from the vendor's 16:31 chains.
- In OS-9, their chance-in-the-money cell reads "awaiting the solver gate".
- In OS-10, their IV and IV-rank cells read the same.
- Their chains are never sent to the solver (`builds_for(..., gated=True)`).
- Each table's note says so.

**The tags' history thresholds** stand as written:
- they are labelled "session-set, reviewed at the 25 Oct 2026 dry run" in `config/opening_setup.yaml` (`oi_builds.tags.label`);
- the OI-build table's note prints that label.

**Fixtures** (`validate_opening_setup` group G, 54/0):

| Input | Expected | Result |
|---|---|---|
| Basis session Fri 16 Oct: SPY 09:30 open 660.00, ES 09:30 open 6,650.00. Mon 19 Oct: ES's 06:55 ET bar closes 6,700.00 | SPY about 6,700 × 660 / 6,650 = **664.96**, worked by hand | The line prints it |
| No overnight bar | "Pre-market (ES): not available (ES has no overnight bar)." | Prints that |
| The same bars through a bars store | The same line | Prints it |
| A 06:00 ET cutoff | The 06:55 bar is not read | Not read |
| SPX's OS-9 cell, beside a solved name's 45% | "awaiting the solver gate" | Prints that |
| SPX's two OS-10 IV cells | "awaiting the solver gate" | Print that |

The old ruling-3 check (no pre-market line) is replaced; its comment says so.

### 2. The Monthly v2 fallback writer's one revision

`monthly_macro/prose.py` (`write_all`, which also writes the stacked Monthly's and the Quarterly's sections) now runs the stack's retry: one revision, withheld on the second failure with both reasons kept.
- `ATTEMPTS = audit_retry.ATTEMPTS` (2).
- `retry_prompt` builds on `audit_retry.revision_note`, so the revision carries the rule, the failing span and the draft.
- Its own vocabulary, figure-cap and figure lines sit beside the rule.
- Each attempt is logged by `audit_retry.log_attempt`.
- The too-long retry is now the one revision rather than a possible third call.

**Gates.** `validate_monthly_stack` pins three attempts in six places (at lines 1624, 1952, 2006, 2029, 2478 and 2590, about 17 lines later than weekly-fixes-9's notes give them).
- All six now read two, and two checks are added: the revision carries the span and the draft, and the cap line sits before the draft.
- `validate_figure_budget` E reads two, and `validate_monthly`'s comment follows.
- `validate_monthly_stack` renders, so it is CI's.
- `validate_figure_budget` ran locally, 123/0.
- `validate_a47_chain3` F checks the retry on a fixture: two calls, the second with the rule, the span and the draft.

### 3. CD-9's daily part: the crypto paragraph, and the 12:30 line

**THE PRECONDITION DOES NOT HOLD AS RECORDED, so the paragraph is built behind a switch, OFF.**
- The order wires the paragraph only after Track D's D4/D6.
- `TODO.md` shows D4 and D6 both open.
- a43-render's notes do not mention the precondition. ST-10's signal lines are wired into the 07:00 anchor unconditionally: there is no switch, and nothing records D4/D6 as met.
- `docs/briefs/audit-4-agenda.md` still lists this item as conditional on D4/D6.
- So I built it, gated it, and shipped `config/crypto_sources.yaml` `blocks.daily.enabled: false`. Your yes turns it on.

**The paragraph** (`altdata/crypto_blocks.daily_paragraph`): six computed lines read from the store by key. There are no model words, so the narrative audits have nothing to audit.

| Line | What it prints | Source |
|---|---|---|
| 1, 2 | BTC's and ETH's T-1 ETF flows, with the streak and the 5-day sum's percentile since January 2024; "STALE, last good <date>" past four days | S-2: `farside.*_total`, `calc.etf_streak`, `calc.etf_5d_pct` |
| 3 | OI-weighted perp funding, BTC and ETH, annualised; "z-score from 15 Dec 2026" (ruling 5 of 17 Oct) | S-3: `calc.funding_agg` |
| 4 | Perp open interest, BTC + ETH, and its change on the day | S-3: `calc.oi_usd` |
| 5 | The DVOL band, BTC and ETH | S-4: `deribit.dvol_*`, `calc.dvol_pct_full`; the existing session-set band |
| 6 | Fear & Greed as one word | `fng.value` |

- **Fear & Greed's words are session-set:** panic up to 24, fear to 44, neutral to 55, greed to 75, euphoria above. The publisher's own classification is not stored.
- **No flag is read** (`crypto_blocks` never names a `calc.flag_*` key). The fixture stores a flag set "on", and it prints nowhere.
- **Left out, as the paste says:**
  - BTC dominance came from CoinGecko's `/global`, which is retired.
  - The order's 21:45 ETF refresh has no unit, because no 21:45 report run exists. None is added.

**Where it prints:**
- **The 07:00 anchor:** under the overnight table. The anchor has no Positioning section, and this is the nearest flows block.
- **The 16:45 close:** a Positioning & flows sub-section of data lines, through one hook in `stack.build`, only while the switch is on.

**Budgets.**
- The close's 1,000-word budget counts prose only (`stack.section_words`). The paragraph is lines, so it displaces nothing there, and the fixture shows the section's count unchanged with it.
- In the anchor, six lines are the cap (config `max_lines: 6`), each under 40 words on the fixture.
- **What it displaces:** nothing in either report.

**The 12:30 line** (`daily_cascade/crypto_gate.py`, registered last in `midday_gate.GATES`):
- It returns closed, opening no store and reading no flag, until `config/crypto_sources.yaml` `blocks.midday_leverage` names a ledger whose verdict is PASS (`admitted_by` / `admitted_verdict`, the `style_regime.yaml` form). A closed slot prints and writes nothing.
- Once admitted, it reads the newest stored S-3 flag knowable at 12:30 ET: the prior session's at the latest, because the day's own flag is computed after the close.
- No intraday funding or open-interest series exists, so "trips intraday" can only mean that newest stored reading. Read it that way.
- **Gates:** `validate_dealer_block`'s registry pin now lists the fifth gate. `validate_a47_chain3` E covers four cases: closed with no store opened; the slot writing nothing; opening with a fixture PASS ledger; staying closed on a FAIL ledger or on a day whose flag is not yet knowable.

### 4. The S-2 and S-3 calibration ledgers

Both are written in the ST-7 form (`tools/calibration/st7_common.py`, `altdata.ledgers.write_ledger`), from public sources only, and labelled "laptop run, public sources". Each states the rights it would grant and grants none.

**S-2** (`tools/calibration/s2_etf_flows.py`; `docs/ledgers/s-2-ledger-2026-10-19.md` and its CSV): **FAIL.**
- 22 completed non-overlapping episodes: 9 high, 13 low.
- The 20-day mean return was +4.5% after a high and −2.4% after a low: an asymmetry of +6.8% at a Welch t of +1.14.
- The order's rule is "a non-zero asymmetry at 20 days across ≥ 8 non-overlapping episodes". The first edition pre-registers the terms it leaves open:
  - a point-in-time percentile;
  - entry at the close of the day after the flow date;
  - calendar-day horizons;
  - 20-day spacing between episodes;
  - |t| ≥ 2.0, with at least 3 episodes in each tail.
- **Farside answered the laptop this time.** It refused on 17 Oct (crypto-tranche-a-2's gap); today's all-data page came back whole. Rows dated the retrieval day are left out as not final.

**S-3** (`tools/calibration/s3_leverage.py`; `docs/ledgers/s-3-ledger-2026-10-19.md` and its CSV): **FAIL.**
- The order's anatomy check, as stated: all four windows were evaluable and **none was caught**. The largest one-day declines were:
  - 5 Aug 2024, −7.1%;
  - 24 Feb 2025, −5.0%;
  - 10 Oct 2025, −7.0%;
  - 22 May 2026, −2.6%.
- 2 firing episodes over 963 evaluable days, both false positives (0.8 a year).
- **Pre-registered:**
  - Hyperliquid's BTC funding is the one public funding history covering all four windows;
  - OKX's open interest in coins stands for OI over market cap, since BTC's supply moves under 0.5% in 90 days. OKX served three years of history, more than crypto-tranche-a-1's notes expected;
  - "the drawdown's largest day" is the month's largest one-day decline;
  - the lead is 10 days;
  - a false positive is a firing with no 10% decline within 10 days.
- **A caveat for you:** "the May 2026 rush" is read by the same rule as the unwinds. If the order meant a rally, a ruling should say so before the box re-run (the pass rule is registered by this edition).

**What the verdicts mean:**
- Neither flag prints.
- `crypto_derived` keeps storing both with gate status "not passed".
- The 12:30 line stays closed.
- Nothing is promoted or admitted, and `validate_a47_chain3` G holds that nothing names an admitting ledger.

### 5. Ruling 6: the monthly restore drill retired

- **Removed:** `chester-restore-drill.service` and `.timer`, `scripts/run_restore_drill.sh`, and the drill's `box-config.allow` entry.
- **Kept:** `tools/restore_drill.py`. The weekly test runs it through the crypt remote.
- **The gates:**
  - `validate_audit_2` holds that the drill is gone and that `chester-restore-test` is the one restore check (26/0);
  - `validate_systemd_units` scores and caps the test in the drill's place (152/0; the five checks it lost are exactly the drill's own unit checks).
- **The docs:** `docs/runbooks/restore.md`, README sections 10 and 13, `rclone_crypt_env.sh`, `run_restore_test.sh` and CLAUDE.md point at the test.
- There was no "drop-in step" for the drill on chain-2's box sheet to retire. The sheet already says the drill is never enabled. aud-2's notes, which carried its drop-in commands, are history and are left as written.

### 6. Registry, catalogue, units and the count

- **No new store key:** the pre-market line and the crypto paragraph are display reads of existing keys, and the 12:30 gate reads an existing flag. So the registry and catalogue need nothing.
- **One new gate**, `tools/validate_a47_chain3.py`, is added to the Makefile.
- **CLAUDE.md's count line** now reads one hundred and nineteen code gates (one hundred and sixteen Python, three shell) and eight data gates, recounted with `scripts/make.sh list`. `validate_audit_3a` (88/0) and `validate_gates` (32/0) hold it.

## Gates run locally, one at a time

| Gate | Result |
|---|---|
| validate_opening_setup | 54/0 |
| validate_a47_chain3 | 42/0 |
| validate_figure_budget | 123/0 |
| validate_audit_2 | 26/0 |
| validate_systemd_units | 152/0 |
| validate_gates | 32/0 |
| validate_audit_3a | 88/0 |

The rest are CI's, including:
- `validate_monthly_stack` and `validate_monthly`, which render;
- `validate_dealer_block`;
- `validate_crypto_sources`, whose grep gate the new modules respect: neither imports a crypto writer, and `crypto_blocks` names no flag key.

CI: see the table at the end.

## Box commands for Ari, after the third chain merges (each dry run first)

1. **The drill's unit files, if the self-deploy copied them.** It copies unit files, and chain-2 shipped the drill's.
   ```
   ls ~/.config/systemd/user/chester-restore-drill* 2>/dev/null
   systemctl --user is-enabled chester-restore-drill.timer   # expect "disabled" (never enabled)
   ```
   If the files are there:
   ```
   rm ~/.config/systemd/user/chester-restore-drill.service ~/.config/systemd/user/chester-restore-drill.timer
   systemctl --user daemon-reload
   ```
2. **The S-2 and S-3 ledgers' box editions.** These are the same public sources, labelled a box run, and each writes a new dated file outside the checkout.
   ```
   mkdir -p ~/chester-data/ledgers
   .venv/bin/python tools/calibration/s2_etf_flows.py --box --out ~/chester-data/ledgers
   .venv/bin/python tools/calibration/s3_leverage.py --box --out ~/chester-data/ledgers
   ```
   Then, from the laptop, `scp 'vps:~/chester-data/ledgers/s-[23]-*' docs/ledgers/` and tell a session to commit them. The pass rules are registered by today's editions; a re-run applies them.
3. **The pre-market line:** read it in the next 07:00 anchor's dry run (yours, as always), under the gauge.
4. **The crypto paragraph:** nothing until you turn the switch on (Needs you 1).

## Files shared with session B

- **alpha-lab-4 (CD-12):** touches `CLAUDE.md`, `Makefile`, `altdata/crypto_blocks.py` and `config/crypto_sources.yaml`.
  - In `crypto_blocks.py`, my change is a new daily section and a docstring paragraph.
  - In the yaml, it is `blocks.daily` and `blocks.midday_leverage`.
  - In the Makefile, it is one line after `validate_opening_setup.py`.
  - In CLAUDE.md, it is the count line and the restore paragraph.
  - Whichever merges second recounts the count line.
- **library-st-l and b45-chain3:** not on the remote when I checked, so no overlap is known. These branch files may meet session B's work: `daily_cascade/opening_setup.py`, `morning_payload.py`, `morning_render.py`, `stack.py`, `midday_gate.py`, `monthly_macro/prose.py`, `deploy/systemd/`, `tools/validate_monthly_stack.py`, `validate_opening_setup.py`, `validate_dealer_block.py`, `validate_systemd_units.py` and `validate_audit_2.py`.

## Needs you

1. **The crypto paragraph's switch.** It is off because nothing records D4/D6 as met. Turn it on if you rule that the anchor and the stacked close meet the precondition, as ST-10's unconditional wiring already assumes. One config line: `blocks.daily.enabled: true`.
2. **S-3's "May 2026 rush"**: an unwind like the others, or a rally? It decides before the box re-run.
3. **Fear & Greed's five words** (session-set): accept, or name others.
4. **S-2 and S-3 verdicts, both FAIL:** for your accept-all as rule-31 drafts. No register entry was written by this branch.

## CI

| Run | Commit | Result |
|---|---|---|
| 39291070089 | `a2f1461` (items 1 to 6, merged with chain-2's `ab27c07`) | **success: 129 of 129 jobs** |

