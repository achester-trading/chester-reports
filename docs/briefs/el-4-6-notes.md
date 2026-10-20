# EL-4 to EL-6, with the 16 Oct Weekly's two readings and the rulings of 17 Oct (session A, 17 Oct 2026)

**Merge order: after `6b-dealer-3`, in the second stitched chain.** Branch `el-4-6` is cut from the tip of `6b-dealer-3`, with its step-0 fixes merged forward (`e02aefd`), so it carries 6b parts 1 to 3, item 52 and the st-r5 line, and merges after all of them.

Branch-only:
- nothing merged, deployed or run on the box;
- no unit enabled or started;
- session B's `weekly-fixes-7`, `digital-49-51b` and `audit-leftovers-1`, Monday's chain and chester-meme were not touched.

**The spec:**
- `docs/change-order-enterprise-layer-2026-09-27.md` sections 3.4, 3.5, 3.7 and 9;
- `docs/briefs/doctrine-monthly-2026-10-minutes.md` items 3, 4, 5 and 8, applied as ruled on 4 Oct, not as drafts;
- the seven rulings of 17 Oct on the part 2 and part 3 reports.

## Step 0

### The CI reads

Each run was read once. Every failure was this line's own; each is fixed on the branch where it failed and merged forward.

| Branch | Run | Result | Fix |
|---|---|---|---|
| `6b-dealer-2` | 39041337734 (`ebbe8fd`) | **green**, and 39041206588 (`549619d`) green | none needed; the notes record both (`26a156d`) |
| `vol-event-52` | 39041321537 (`1663521`) | **failed**, `validate_security_master`: the two new entries took SM00195 and SM00196, but `next_id` stayed at 195 | `5a67995` sets `next_id: 197`; recorded in its notes (`986c67a`) |
| `6b-dealer-3` | 39041492194 (`5b4b688`) | **failed**, three gates | see below |

The three `6b-dealer-3` failures and their fixes:
- **The inherited `next_id`.** Fixed by the merge from `vol-event-52`.
- **`validate_numeral_audit`.** T3's percentile wrote "th" by hand. It now goes through `numeral_audit.ordinal()` (`2b8c9fa`), and the vendor gate reads it the same way (`e02aefd`).
- **`validate_exec_bits`.** The vendor unit's ExecStart named the untracked `.venv/bin/python`. It now runs the tracked `scripts/run_flashalpha.sh` (mode 100755; logs to `~/logs/flashalpha-YYYY-MM.log` behind a lock).

The fixes' own runs are in the CI section at the end.

### The email check

`git log -p origin/main..<branch>` was read for `6b-dealer-1`, `6b-dealer-2`, `vol-event-52` and `6b-dealer-3`, then `el-4-6`.

**In committed files, commit messages and notes files, the count is 0** for the operator's address, and 0 for "mailto" among this line's changes.

**But `git log -p` is not 0, and I did not rewrite.** Every match (94 to 112 per branch) is the commits' git **author header**, the checkout's `user.email`.

The address was never written into any file or message; it is git's commit metadata. Every one of main's 676 commits carries the same header, so it is already public on main. Rewriting only these branches' authorship would not remove it.

That fix is the operator's to choose (needs-you 1):
- set the checkout's `user.email` to the GitHub no-reply address for future commits;
- and, if wanted, rewrite main's history, which is far larger than these branches.

**User-Agent strings.** No committed User-Agent, config or fixture names a person:
- the project's strings name `chester-reports` with a purpose ("research logging", "reference data; no trading");
- the voices scan's browser-like string takes its contact from the EDGAR contact in `.env` at run time;
- its fixture uses `ops@example.invalid`.

**What the earlier slip actually was.** It was one manual check request, not committed code.

One related finding, older than this line: CLAUDE.md says the voices scan identifies itself "with the EDGAR contact", which `altdata/sources/edgar.py` says is used for sec.gov only. On the box, that contact reaches every voices source. That is needs-you 2.

**The notes no longer name the operator.** The four notes files (`6b-dealer-1`, `-2`, `-3`, `vol-event-52`) said "Ari" in nine places; they now say "the operator" (`4cd0e9f`). This file names no person.

## The rulings of 17 Oct, applied

1. **The chart displacements stand as built.** No change; reviewed at the 25 Oct dry run.
2. **The 12:30 alert is mailed.** `daily_cascade/midday_gate.mail_alert`:
   - the existing SMTP path (`daily_cascade/deliver.send_html`, the heartbeat's and the Weekly's credentials);
   - subject `12:30 alert: <the trigger line>`, at most one message a session;
   - a `.mailed` marker beside the outbox copy, written before the send, so a crash cannot send twice;
   - the outbox JSON is kept, and carries the mail state but never the recipient;
   - a send failure is recorded, never raised; no other channel.
   - `validate_dealer_block` group N: one send, a second run that session sends nothing, a raising send is `send_failed`. The gate's fake send means no test can reach a mail server.
3. **FlashAlpha is a cross-check source entry.**
   - The vendor line opens "FlashAlpha (vendor) … beside the engine's own figures", never in place of them.
   - The freshness roster gains a `vendor` family. It carries only the levels endpoint's four fields (flip, walls, spot), which `cross_check.py` has read since 4 Sep. The GEX endpoint's names are unverified, so an absent GEX field is a listed gap, never a stale feed.
   - The family stays pending until the writer's first run records an attempt.
   - The catalogue line carries the 30-call daily budget.
4. **The chat-side tasks retire after the first clean week.** Live after Thursday's merge. If `validate_vendor_divergence` is clean through Wed 28 Oct, the operator deletes both scheduled tasks on **Thu 29 Oct**: the Wednesday FlashAlpha pull and the Thursday reconcile. The chat carries the reminder.
5. **The caps stand as percentages.** The first Weekly under them is 25 Oct. A unit killed at its cap gets a one-line percentage fix.
6. **The ^VIX9D and ^VIX6M master entries stand** as mechanical index entries, identifiers unverified. Monday's OpenFIGI run tries them, and they stay without a FIGI if none exists.
7. **The descriptive flags take the pre-registration's definitions from 17 Oct.** See Part 0.

## Part 0: the 16 Oct Weekly's two readings

### 1. Wednesday 14 Oct: the flip was crossed in the overnight gap, not in the session

I cannot read the box's stored captures from here. So I read SPY's 5-minute bars for 13–16 Oct from Yahoo on the laptop: a read, nothing stored. Their range matches the Weekly's figures exactly (9.64 on 14 Oct).

| 14 Oct | Value |
|---|---|
| Prior close (13 Oct) | 778.04 |
| Morning flip | 777.25 |
| Open | 774.92 |
| Cash high | **776.35** |
| Low | 766.71 |
| Close | 769.61 |

**The code was right.** `stack_close.scorecard_row` tests `lo <= flip <= hi` on the session's 5-minute bars, never the close. The cash high stayed 0.90 below the flip, so `flip_crossed` was False and "amplified" (flip crossed and range ≥ 1.2× implied) was correctly unset.

**What changed:**
- **A descriptive flag, "gapped through the flip"** (not pre-registered). It is set when the prior close sits on one side of the morning flip and the whole session on the other. `weekly_sections.flags_for` computes it; the Weekly's flag column and table note print it; the glossary says so.
- **No earlier session's flag changes.** Nothing was wrong with the crossing test, and the new flag is added, not substituted. Which past sessions it would mark is a box read: those whose stored card has the prior close and the session on opposite sides of `flip_morning`.
- **Ruling 7 changes 14 Oct's question going forward.** Under the pre-registration's H2, "amplified" is a regime session in negative gamma with range ≥ 1.2× implied; the flip plays no part. From 19 Oct a session like 14 Oct would be amplified if its morning net-to-gross cleared 0.10 with negative net GEX. 14 Oct itself keeps the definition it was printed under.

### 2. Friday 16 Oct: the IV gap is real, not a capture fault

Again read from here, not from the box. On Saturday, yfinance's SPY chain carries Friday's final quotes, the state the 16:10 capture saw. I ran the repo's own solver path (`chain_metrics.atm_iv_30d`) over it, with days to expiry from Friday:

- **The capture was fresh.** Quotes up to 16:14 ET, with tight spreads (the 765 calls and puts for 13 Nov at 12.17/12.26 and 12.07/12.19).
- **The interpolation picked the right expiries.** 13 Nov (28 days) and 20 Nov (35 days), variance-interpolated. Result: **14.44%** against the Weekly's 14.5.
- **The solver's reading is consistent.** Every expiry from 7 to 45 days reads 14.0–14.5. A hand check: the 28-day straddle (24.4) over 0.8 × spot × √T gives 14.4%.
- **The difference is the VIX's construction.** The same chain under the VIX's own model-free method (the 28- and 35-day strips, variance-interpolated to 30 days) gives **19.5**, against the VIX's 19.98 (Cboe's published close; a vendor-served figure replaced, 19 Oct 2026, under the standing rule). The VIX prices the whole strip, the put wing included. On a falling day with a steep skew it sits well above the at-the-money figure without either being wrong.

**The implied ranges, and whether the flags change.** On the 771.71 prior close:

| IV used | Implied range | Actual range 12.61 is |
|---|---|---|
| SPY's own 14.44 | 7.02 | 1.80× |
| The VIX's 19.98 | 9.71 | 1.30× |

Both clear 1.2. **No flag on 16 Oct turns on which figure is used.**

**What changed:**
- **The IV's capture time.** No fault was found. But the close reads the session's *last* stored chain, and if the 16:10 capture were missing, that would be a midday one. The close now stores the chain's capture instant on the card (`atm_iv_capture_at`). A chain captured before 16:00 ET prints its time beside the IV ("SPY IV 14.5 captured 12:31 ET").
- **The glossary.** The IV check's entry now says why the two can differ.

**Fixtures:** `validate_dealer_block` group O.

## Part 1

### EL-4: the Doctrine sections (a library item)

**Part X**, "Change, Attention and the Intraday Rung", is new in the Doctrine's body, before the appendices. Nothing in Parts I to IX moved.

- **10.1 The change ladder.**
  - The order's five tiers, with tier 2's N = 20 graded outcomes within the regime and the unconditional base rate beside the conditional.
  - The cadence clause: the cadence of the tier being entered, so tier 3 only after a quarter at tier 2, and tier 4 only after a year at tier 3.
  - Every change order from now carries its tier and the date it entered.
- **10.2 The attention budget.**
  - Seven packet approvals a week; one sitting a week of at most two hours (the Doctrine monthly and the audit sittings count as their weeks').
  - A deferred packet is an abstention with reason `attention_budget`, graded like any other.
  - The Weekly's three counts (approved / 7, sitting hours / 2, rulings in chat, the third measured, not capped, until Doctrine #2).
  - **The register already knows the reason.** `register/store.py` `ABSTENTION_REASONS = ("attention_budget", "operator_judgment")`, refused otherwise at write; `tools/decide.py` offers it; `validate_weekly_stack` gates it. Nothing added.
- **10.3 The intraday rung.**
  - Books A to D, no fifth book; intraday a tactics layer for B and C plus at most two paper engines.
  - What an engine carries before its first trade, and the fixed kill criterion (N ≥ 40).
  - The dealer engine's three conditions, then the scheduled-event engine after the surprise-reaction study.

**Appendix D**, as of 17 Oct:
- D.2 now quotes item 8's three entries **verbatim from the minutes, citing them, as ruled and not as drafts**: INC-6 now with `expression_currency`, INC-7, and the first graded decisions with `gate_outcome = pre-gate`.
- D.1 records that Part X now states items 3 to 5 in the body.

**The edition:** the masthead moves to v1.2. The guide's row and table carry v1.2 and about 29,200 words. `docs/html/operating-doctrine-whitepaper.html` is rebuilt.

**The library gate, check 14** (`tools/check_library.py` `dated_appendix_faults`), on every paper's "— Dated:" appendix:
- the heading carries "(… as of D Month YYYY)";
- no entry heading is dated after it (a scheduled date in the text, such as the Reporting System paper's next Monthly, is allowed);
- an entry about lessons carries no figures (dates, INC ids, items, sections, rules and parts excepted);
- where the paper quotes the Doctrine monthly's item-8 entries, each is the minutes' sentence verbatim;
- the Doctrine's named abstention reason is in the register's enum.

`check_library`: 0 failures. Its fixtures are in `validate_system_metrics` group F: a figure in a lesson entry, a missing as-of, a later entry, and a reworded ruled entry each fail.

### EL-5: 6b's state vector

`altdata/state_vector.py` computes **eighteen measured variables per capture, numbers and None only**:
- the gap and its fill;
- the opening range (30 minutes), its break (+1/0/−1) and the VWAP relation;
- breadth, the sector-ETF proxy above its 50-day average;
- realised against implied vol (SPY's own IV, no VIX stand-in);
- both VIX legs: VIX3M/VIX the champion, VIX9D/VIX the challenger;
- dealer: flip distance, GEX sign and net-to-gross;
- hours to the next scheduled release, from the events table;
- volume against the prior 20 sessions' to the same clock;
- trend alignment (+1/0/−1 against the market-state trend dimension).

**How it is computed and stored:**
- Each store is read as of the capture's instant, and the bars are cut at it.
- The close computes every SPY capture of the session (16:10 now; 09:45 and 12:30 once part 2's units run).
- It stores each present field as `state.<field>`, instrument `SPY:<slot>`, observed on the session and available when written.
- A missing input is None, never a guess.

**Where it prints:**
- The close: one compact line per capture in Mechanics ("State vector, SPY").
- The Weekly: a six-column row per session ("State vector by session, SPY (16:10)"), read from the store.
- `python -m altdata.state_vector show --date D` prints a stored vector.

**Registry:**
- all eighteen keys, with units;
- `hours` joins the units vocabulary, its change raw;
- the catalogue line.

**No engine reads it.** `validate_dealer_block` group P fails any import of it from `alpha/` or `alpha_proposer/`, and a planted import in a fixture engine fails.

**Fixtures (group P):** every leg by hand on fixture bars and a fixture capture; an intraday capture before the range completes; nothing stored (all None); a label field, a string value and a boolean each fail; the stored rows; the close's line; the Weekly's row.

### EL-6: the system-metrics block

`altdata/system_metrics.py` reports five figures, each with its window and source, nothing fetched:

| Figure | Source |
|---|---|
| Uptime | the share of `verdict=ok` lines in `~/logs/heartbeat_check-YYYY-MM.log` |
| Feed completeness | fresh over expected by family, from `feeds.freshness` as of the edition |
| Incidents | the count and dated list, parsed from `docs/incidents.md`'s entry lines |
| Model cost | tokens per report from `model_calls` |
| Withheld drafts | the count from the withheld-drafts log |

**Model cost:** the pipeline already records usage. AUD-2's meter writes each response's usage per call, with no prompt text, from 14 Oct, and the block says "recorded from 14 Oct 2026" for October. Nothing was added.

**Withheld drafts** (ruling 4 of 17 Oct applied in the GTM paste's step 0: every edition writes the log -- the anchor, the close, the Weekly, the Monthly, the Quarterly and the 12:30 slot when it opens; the run logs unchanged; `withheld_log.REPORTS`, gated in `validate_system_metrics` group D). Before that: there was no such log; a withheld paragraph lived only on its section in the archived edition and as a line in a run log. `altdata/withheld_log.py` now appends one JSON line per withheld section or sub-section when the close, the Weekly, the Monthly or the Quarterly archives its edition. It records the reason, never the draft, at `<archive dir>/withheld_drafts.jsonl`. Before it exists the block prints "not recorded". The 07:00 anchor's withheld draft is still only in its run log (needs-you 4).

**"Not recorded"** prints wherever a source does not exist, never zero.

**The Audit #4 baseline, as ruled (ruling 5 of 17 Oct, applied in the GTM paste's step 0).** The main table's baseline column prints the agenda's feeds line (official 96/96; external 52 of 5x, one stale -- AAII, the operator's drop; the 9 Oct line), labelled "by hand, Audit #4, 14 Oct", and "not recorded" beside uptime, model cost, incidents and withheld drafts (the ruling names no incident figure, so the incident list no longer prints). A second table lists the audit's measured figures of 14 Oct, each labelled: the store at 2.33 million rows, 688,000 of them FRED; growth about 86,000 a weekday; 14 GB of 38 GB free; a backup zip about 115 MB; the Drive backup folder 7.6 GB; days up, session hours and model cost "not recorded".

Superseded: the baseline first printed in its own column as "Baseline, by hand, Audit #4", only where the agenda's I.3 recorded a figure:
- feeds: "official 96/96 (9 Oct)" (its external figure is written "52/5x" and is not transcribed);
- incidents: "INC-1 to INC-9, one open".

Uptime, model cost and withheld drafts were not recorded there, so nothing prints beside them. The transcription is `config/reporting_stack.yaml` `system_metrics.baseline_audit_4`.

**Where it prints:**
- **The Monthly's last detail table**, after the appendix.
- **The Quarterly's opening table**, after the summary and before section 1. It is the same function over the quarter, and `stack_render` prints `ed["opening"]` in the page and the Markdown.
- `python -m altdata.system_metrics show --month YYYY-MM` prints it on the box, read-only.

**What it displaces in the Monthly's budget: nothing.** The budget counts prose only (`stack.section_words`: claims and paragraphs; tables and lines are data), and the block draws no chart. Group E holds that `edition_words` and the chart count are unchanged with the block appended.

**Fixtures:** `tests/fixtures/system_metrics/` holds a heartbeat log (as `.txt`; `*.log` is gitignored), an incidents file and a withheld log. `tools/validate_system_metrics.py` (new, in the Makefile):

| Group | What it holds |
|---|---|
| A | the five figures by hand (uptime 5 of 7; the fixture month's incidents 3; model tokens by report; withheld 2 with a duplicate counted once) |
| B | every source absent gives "not recorded" |
| C | the baseline where recorded, and only there |
| D | `gather()` on fixture files and a temporary `model_calls` table, never the live store; the log written and read back |
| E | the budget, and the Quarterly's opening |
| F | the dated appendix |

### Registry, catalogue, units, the count

- **Metrics:** the eighteen `state.*` keys; `hours` in the units vocabulary.
- **The catalogue:** `altdata.state_vector`, `altdata.system_metrics`, and the FlashAlpha line with its budget.
- `check_registry` OK.
- **CLAUDE.md:** a paragraph on EL-4 to EL-6, and the count line recounted to **ninety-two code gates (eighty-nine Python, three shell) and seven data gates**. The Makefile counts 92 / 89 / 7, and `validate_audit_3a` holds them: 85/0.

## Gates run locally

One at a time, only those written or changed here:

| Gate | Result |
|---|---|
| `tools/validate_dealer_block.py` (groups N, O, P) | **133/0** |
| `tools/validate_system_metrics.py` (new) | **18/0** |
| `tools/validate_dealer_vendor.py` | **28/0** |
| `tools/validate_systemd_units.py` | **134/0** |
| `tools/validate_audit_3a.py` | **85/0** |
| `tools/validate_security_master.py` (on `vol-event-52`) | passed |
| `tools/check_library.py` | 0 failures, 0 warnings |
| `tools/check_registry.py` | OK |

Left to CI: every other gate, and everything that renders a PDF. That includes:
- `validate_numeral_audit` and `validate_exec_bits` for step 0's fixes;
- `validate_weekly_stack` and `validate_monthly_stack`, which now meet the flag definitions, the state-vector sub-section and the metrics detail table.

## Box commands, for the operator

Inside a window (weekdays 09:05–15:40 or 17:20–23:30 ET), **after Thursday's merge**. The self-deploy copies the unit files within 30 minutes of the merge reaching main.

```
cd ~/chester-reports
git log -1 --oneline
.venv/bin/python -m altdata.secrets FLASHALPHA_API_KEY FLASHALPHA_BASE_URL SMTP_USER SMTP_PASSWORD   # set/missing only
systemctl --user list-unit-files 'chester-dealer-*' 'chester-flashalpha*'
systemctl --user enable --now chester-dealer-0945.timer chester-dealer-1230.timer chester-flashalpha.timer
systemctl --user list-timers 'chester-dealer-*' 'chester-flashalpha*'
```

**The first captures and readings, on the next session after enabling:**

```
tail -n 40 ~/logs/dealer_capture-$(date +%Y-%m).log                     # 09:45 and 12:30
ls ~/chester-data/outbox/midday/                                         # a 12:30 alert and its .mailed marker, only if a gate opened
tail -n 40 ~/logs/flashalpha-$(date +%Y-%m).log                          # 16:25: stored and absent fields
.venv/bin/python tools/validate_vendor_divergence.py                     # after 16:25
.venv/bin/python -m altdata.state_vector show --date $(date +%F)         # after the 16:45 close: the 16:10 vector
.venv/bin/python -m altdata.state_vector show --date $(date +%F) --slot 0945
```

**The first metrics block:**
- Any day: `.venv/bin/python -m altdata.system_metrics show --month 2026-10`, read-only.
- In the Monthly of 1 Nov, as its last detail table.

**The FlashAlpha tasks:** on Thu 29 Oct, if the divergence gate was clean through Wed 28 Oct, delete the two chat-side FlashAlpha scheduled tasks (ruling 4).

## Files shared with the open branches

Trial merges (`git merge-tree`, nothing committed) against `digital-49-51b`, `st-r6-es-block`, `crypto-tranche-a-2`, `aud-3b-security-master`, `post-friday-fixes`, `docs-batch-9` and `6e-metric-lenses`, compared with the same merges from `6b-dealer-3`: **this branch adds no conflict.** Every conflict listed there is `6b-dealer-3`'s or older (CLAUDE.md's count line above all).

**Session B's `weekly-fixes-7` and `audit-leftovers-1` are not on origin yet**, so they could not be trial-merged. This branch changes these files they are likely to share:
- `daily_cascade/weekly_sections.py`: `flags_for`, the flags' definitions, "gapped through the flip", the IV capture time, the dealer table's note;
- `daily_cascade/dealer_weekly.py`: the state-vector table in the Weekly's Mechanics;
- `daily_cascade/weekly_stack.py`: `save_edition` logs withheld drafts;
- `monthly_macro/stack.py`: the system-metrics detail table in `produce`, `save_edition`;
- `monthly_macro/dealer.py`: the retrospective counts from 17 Oct;
- `config/display_labels.yaml` (the glossary), `config/reporting_stack.yaml`, `metrics_registry.yaml`, `CLAUDE.md`.

## Needs you

1. **The address in the commits' author header.** No file or message carries it, but every commit's git author header does, on main as on these branches. Two choices:
   - set the checkout's `user.email` to the GitHub no-reply address for future commits;
   - and, if wanted, rewrite main's history.

   Rewriting these branches alone would not remove it, so I did not force-push.
2. **The voices scan's User-Agent carries the EDGAR contact to every voices source.** That is a person's address if `.env` holds one. CLAUDE.md describes it; `edgar.py` says the contact is for sec.gov only. Should the voices scan carry a generic contact line instead? That is a change to PB-1's design, not made here.
3. **14 Oct and "gapped through the flip".** Confirm the descriptive flag. Under ruling 7, "amplified" no longer needs the flip from 19 Oct, so 14 Oct's kind of session will flag "amplified" if it is a negative-gamma regime session.
4. **The 07:00 anchor's withheld drafts are not in the new log.** Its withheld draft stays only in its run log: the anchor's narrative step has no archive directory in scope, and its gates would write to `reports/`. Add it, or leave the count to the stacked editions?
5. **The baseline row is thin.** The agenda recorded only the 9 Oct feeds line and the incident list; the external figure is written "52/5x". If the by-hand numbers brought to Audit #4 survive, give them, and they print beside the computed month.
6. **The state vector's intraday captures** compute only after the close, at 16:45, from bars cut at each capture's time. The bars are pulled at 16:10, so a 09:45 vector cannot be computed at 09:45.
7. **The Weekly prints the state vector as its own six-column table,** not as columns of the dealer table, which is at six already (the mobile rule).

## CI

| Branch | Commit | Run | Result |
|---|---|---|---|
| `6b-dealer-2` | `26a156d` (notes) | 39067988621 | **green** |
| `vol-event-52` | `5a67995` (`next_id: 197`) | 39067887066 | **green** |
| `vol-event-52` | `986c67a` (notes) | 39067993434 | **green** |
| `6b-dealer-3` | `4cd0e9f` (step 0's fixes, before the vendor gate's) | 39068044387 | **failed**, one check: `validate_dealer_vendor` still expected the hand-written "2th" -- fixed in `e02aefd` |
| `6b-dealer-3` | `e02aefd` | 39068814694 | **green** |
| `el-4-6` | `6501795` | 39070454969 | **failed**, one check (265 passed, 1 failed in `validate_monthly_stack`): the Monthly's detail tables gained EL-6's `system_metrics` after the appendix and the gate still listed four |
| `el-4-6` | `a629f1d` (notes) | 39070524418 | **failed**, the same one check; every other gate green |
| `el-4-6` | `8f82653` (step 0 of the GTM paste: the gate fix, the User-Agent rule, rulings 4 and 5) | 39086764981 | **green** |
