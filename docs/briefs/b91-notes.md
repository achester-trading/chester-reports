# B91 notes: Batch 19 filed (round 9, items 99–110); the EM shock-screen audit prepared

Paste B91 (`docs/pastes/B91.md`), 30 Oct 2026. Branch `b91-batch-19-filing`, base
`origin/b81-batch-18-overnight-session` at `6256a67c` (Batch 18 and SR-68 on it,
main merged in). The order as drafted is `docs/pastes/B91-attachment-round-9.md`
(names replaced by outlet and role, L5). Merges right after b81 next week.

## Part 1: the filing

- **The order:** `docs/change-order-signal-triage-batch-19-2026-10-29.md`. It has
  the header, a §0 holding L1 to L6, then the order in filed numbers.
- **L1:** written 98–109 are filed 99–110. The two tables (the numbering, and the
  earlier references by subject) are in §0.
  - Every reference resolves, so there is **no needs-you**.
  - Two resolve to a different number than written: the chat's "54" is the
    filed **60**, the earnings-estimate overshoot, as Batch 14's F-table and
    Batch 17's J1 found; and "Batch 5 item 10" is **item 10 of Batch 4**,
    SR-46, the EM shock screen.
  - SR-36 (the Treasury basis-trade proxy) is a ruled number with no register
    entry, like SR-35.
  - The sign-off's quoted rulings stay verbatim, in written numbers.
- **L2:** provisional **SR-69** (100, the premium sleeve), **SR-70** (102, the
  kill-switch board), **SR-71** (104, the global AI-complex panel) and **SR-72**
  (107, the intraday dealer read). Each is "provisional, placed by Audit #5". The
  amendments are recorded against 45, 60, 29, SR-12/30, `em_scorecard`, the
  Digital Assets chapter and 88(b), and `docs/alpha-lab-rules.md`.
- **The index line and the register's batch-orders cell are by hand**: S1's
  `tools/change_orders_index.py` is not on this base. When the chain-8 stitch
  brings it, `--check` will hold both.
- **Narrative register:** filed 103's claim, in `docs/narrative-register-pairs.md`.
- **Voices:** no voices register file exists in the repo. The voices are stored
  by the scan from `config/voices_sources.yaml`, and adding these outlets there
  would make the scanner read them, which no ruling asks for. So, as in
  Batch 17, the outlet rows are the order's §6 table (outlets and tags only), and
  the X-only accounts go to the X pilot's seed list chat-side.
- **L5's kept name:**
  - "Kakushadze & Serur", the authors of the cited book, kept as a citation
    (D31(3));
  - the hashtag "#TeamGraham" was replaced by "a LinkedIn author (unattributed)"
    on the operator's instruction of 30 Oct 2026.

  If it should go, it is a one-line change.
- **Gates,** one at a time: check_registry OK; check_library 27 papers, 0
  failures, 0 warnings; validate_official_sources 340 passed.

## Part 2: 105(a), the EM shock-screen audit, prepared

**The screen.** The EM layer of `altdata/move_screen.py` (SR-46 (b) to (d); config
`config/move_screen.yaml`, `em:`):
- It runs in the 16:45 close: `scripts/run_daily_close.sh` line 150,
  `python -m altdata.move_screen write`.
- It stores four keys, each with observed_at the session:
  - `screen.em`: one row a session, the basket's state;
  - `screen.em_contagion`: instrument `<country>:<shock date>`;
  - `screen.move`: one row per flagged series, instrument the series;
  - `screen.move_summary`.

**What it reads for Brazil:** two members and nothing else.
- `fred.usd_brl`: BRL per USD, FRED DEXBZUS, H.10. It posts a week of dailies
  each Monday, so it is read on its latest point no older than 7 days.
- `yfinance.mkt_ewz`: the iShares MSCI Brazil ETF.

**The DI curve and Brazil's local bonds are not tracked.** The store holds no
Brazilian yield curve, local-bond index or daily long rate. Brazil's only rate is
`em.bis.policy_rate.bra`, monthly. So the screen could not have seen October's
local-bond loss through rates; it could only see it through BRL and EWZ.

**The thresholds**, all session-set except the contagion rule, which is ruled:
- A member is flagged when its 1-day or 5-day change is past **2.5 sigma**,
  two-sided, against its own five-year history of such changes. That needs 500
  observations; FX moves by its log change, an ETF by its log change.
- In stress terms, BRL rising and EWZ falling are stress.
- **Idiosyncratic:** one country alone flagged. It prints as a candidate for the
  narrative register; the write is the operator's.
- **Systemic:** at least 80% of the live members moving the same way, with the
  basket's median 5-day stress z at 1.0 or more.
- **The contagion rule (ruled):** a single-country shock earns a Weekly or
  Monthly line only if, within 5 sessions, it passes to the basket (a systemic
  day) or to EM spreads (EM corporate or high-yield OAS widening at 2 sigma over
  5 days). Until then it is a close line only.

### (1) The box commands, read-only

Run as the operator on the box, from the checkout. They open the store with
`mode=ro`, write nothing and touch no unit.

```
cd ~/chester-reports && .venv/bin/python - <<'EOF'
import json, os, sqlite3
db = os.environ.get("CHESTER_DB") or "data/chester.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
q = ("SELECT substr(observed_at,1,10), instrument, value_text FROM observations "
     "WHERE registry_key=? AND observed_at >= '2026-10-01' AND observed_at < '2026-11-01' "
     "ORDER BY observed_at, available_at")
print("== screen.em: the basket each October session")
for day, inst, v in con.execute(q, ("screen.em",)):
    d = json.loads(v)
    print(day, d.get("state"), "flagged:", d.get("countries_flagged"),
          "median z5:", d.get("median_stress_z5"), "co-move:", d.get("co_movement"))
print("== screen.em_contagion: single-country shocks")
for day, inst, v in con.execute(q, ("screen.em_contagion",)):
    print(day, inst, v)
print("== screen.move: Brazil's members flagged")
for day, inst, v in con.execute(q, ("screen.move",)):
    if inst in ("fred.usd_brl", "yfinance.mkt_ewz"):
        d = json.loads(v)
        print(day, inst, "z1:", d.get("z1"), "z5:", d.get("z5"), "max|z|:", d.get("max_abs_z"))
print("== the Brazil keys' October values (newest vintage of each day)")
for key in ("fred.usd_brl", "yfinance.mkt_ewz"):
    rows = con.execute(
        "SELECT substr(observed_at,1,10), value_num FROM observations "
        "WHERE registry_key=? AND observed_at >= '2026-09-24' AND observed_at < '2026-11-01' "
        "ORDER BY observed_at, available_at", (key,)).fetchall()
    last = {}
    for day, val in rows:
        last[day] = val
    print(key, len(last), "days")
    for day in sorted(last):
        print("  ", day, last[day])
EOF
```

The z-scores of Brazil's two members on any one October session, computed in
memory as the screen computes them. This writes nothing, but it reads the store
as of now rather than as of that day:

```
cd ~/chester-reports && .venv/bin/python -m altdata.move_screen compute --day 2026-10-DD
```

### (2) What each answer means

- **Fired.** `screen.em` shows Brazil in `countries_flagged` on an October
  session, or `screen.move` holds a row for `fred.usd_brl` or `yfinance.mkt_ewz`.
  The screen did its job on the legs it reads. The miss, if the Weekly said
  nothing, is the contagion rule: a Brazil-only shock that did not pass to the
  basket or to EM spreads within 5 sessions is a close line only (ruled). The
  question for the operator is then whether a single-country shock past some
  larger size, for example 3.5 sigma or two shocks in 10 sessions, should earn
  a Weekly line without contagion.
- **Did not fire.** No Brazil flag in October. Either BRL and EWZ never moved 2.5
  sigma over 1 or 5 days, or `fred.usd_brl`'s weekly posting left it older than
  the 7-day allowance on the days that mattered. The `== the Brazil keys'
  October values` block shows which. The local-bond loss of roughly 18 points
  (GBI-EM Brazil, +25% to +7% year to date) came through rates, which the screen
  does not read.

### The threshold arithmetic, a proposal only

The amendment waits for the operator's reading of the box output.

1. **If BRL's or EWZ's largest October |z| is z\*:** a Brazil-only sigma of z\*
   would have fired. Lowering the screen-wide sigma below 2.5 widens every
   series' false-flag rate (the screen prints each one's k/N). So the narrower
   proposal is a **per-member sigma** in `config/move_screen.yaml` for Brazil
   (one line), set at the larger of z\* and the level that keeps Brazil's own
   false-flag share at or below the screen's current median share. The
   false-flag share at each candidate sigma is read from the same history:
   `compute` prints it.
2. **If the move came through rates (the likely case, by the order's own
   read):** no sigma on BRL or EWZ fixes it. The fix is a Brazilian rate leg.
   - A DI-curve point or a local-bond index from a source that passes the
     16 Oct rule, as 105(b) already asks for the `em_scorecard`.
   - FRED's monthly OECD long-term yield for Brazil is too slow for a screen.
   - Until a daily leg exists, the screen's Brazil coverage is FX and equity
     only, and the notes and the Weekly should say so as a listed gap.
3. **If the H.10 lag hid it:** `member_max_lag_days` (7) is the binding line. A
   faster BRL source would need the 16 Oct check, and a yfinance symbol would
   need D33's exception.

**Change nothing** until the operator has read the output. The box read changes
nothing and is allowed during the freeze (L6).

## Part 3: 105(a), the reading and the proposal (B105, 1 Nov 2026)

### The reading

The operator ran Part 2's read-only command on the box on 1 Nov 2026, at 22:05 ET,
against the store as it stood then. Nothing was written. The output is recorded
here verbatim.

```
== screen.em: the basket each October session
2026-10-19 mixed flagged: ['India', 'Indonesia'] median z5: 0.11 co-move: 0.56
2026-10-20 mixed flagged: ['India', 'Indonesia'] median z5: 0.11 co-move: 0.6
2026-10-21 mixed flagged: ['India', 'Indonesia'] median z5: 0.14 co-move: 0.55
2026-10-22 mixed flagged: ['India', 'Indonesia', 'Taiwan'] median z5: 0.53 co-move: 0.6
2026-10-23 idiosyncratic flagged: ['India'] median z5: -0.07 co-move: 0.55
2026-10-26 mixed flagged: ['Brazil', 'Indonesia'] median z5: 0.42 co-move: 0.67
2026-10-27 idiosyncratic flagged: ['Brazil'] median z5: 0.18 co-move: 0.55
2026-10-28 idiosyncratic flagged: ['Brazil'] median z5: 0.35 co-move: 0.65
2026-10-29 mixed flagged: ['Brazil', 'Indonesia'] median z5: 0.1 co-move: 0.5
2026-10-30 mixed flagged: ['Brazil', 'Korea', 'Taiwan'] median z5: 0.41 co-move: 0.6
== screen.em_contagion: single-country shocks (one row per run day and shock; fields country, shock_date, status, passed_on, passed_to, window_end, window_sessions 5)
run 2026-10-19: Brazil shocks dated 10-05, 10-06, 10-08, 10-09, 10-12, all status lapsed (window_end 10-12, 10-13, 10-15, 10-16, 10-19), passed_to null; India 10-13, 10-14, 10-15 watching
run 2026-10-20: Brazil 10-06, 10-08, 10-09, 10-12 lapsed; India 10-13 lapsed (window_end 10-20), 10-14 and 10-15 watching
run 2026-10-21: Brazil 10-07, 10-08, 10-09 lapsed; Korea 10-14 lapsed (window_end 10-21)
run 2026-10-22: Brazil 10-08, 10-09 lapsed; Korea 10-14 lapsed
run 2026-10-23: Brazil 10-09 lapsed; India 10-23 watching; Korea 10-14 lapsed
run 2026-10-26: Indonesia 10-20 and 10-21 passed (passed_on 2026-10-22, passed_to "EM spreads"); Korea 10-14 lapsed. No Brazil row.
run 2026-10-27: Brazil 10-27 watching (window_end null); Indonesia 10-20 passed (window_end 10-27), 10-21 passed; Korea 10-14 lapsed
run 2026-10-28: Brazil 10-27 watching, Brazil 10-28 watching; Indonesia 10-20 and 10-21 passed (window_end 10-27, 10-28); Korea 10-14 lapsed
run 2026-10-29: Brazil 10-27 and 10-28 watching; Indonesia 10-20 and 10-21 passed
run 2026-10-30: Brazil 10-27 and 10-28 watching; Indonesia 10-20 and 10-21 passed
== screen.move: Brazil's members flagged
2026-10-26 yfinance.mkt_ewz z1: -12.38 z5: -4.98 max|z|: 12.38
2026-10-27 yfinance.mkt_ewz z1: 0.23 z5: -5.39 max|z|: 5.39
2026-10-28 yfinance.mkt_ewz z1: -1.06 z5: -5.56 max|z|: 5.56
2026-10-29 yfinance.mkt_ewz z1: -0.77 z5: -5.46 max|z|: 5.46
2026-10-30 yfinance.mkt_ewz z1: -1.1 z5: -6.27 max|z|: 6.27
(no fred.usd_brl row was flagged in October)
== the Brazil keys' October values (newest vintage of each day)
fred.usd_brl, 21 days, last value dated 2026-10-23: 09-24 5.1953, 09-25 5.1921, 09-28 5.2198, 09-29 5.2323, 09-30 5.1818, 10-01 5.2329, 10-02 5.2222, 10-05 4.9879, 10-06 4.9739, 10-07 4.9983, 10-08 5.0067, 10-09 4.979, 10-13 4.9965, 10-14 5.0378, 10-15 5.0499, 10-16 5.0864, 10-19 5.0574, 10-20 5.0082, 10-21 5.0303, 10-22 5.043, 10-23 5.041
yfinance.mkt_ewz, 27 days, last value dated 2026-10-30: 09-24 36.91, 09-25 36.82, 09-28 36.21, 09-29 36.47, 09-30 37.25, 10-01 37.14, 10-02 38.19, 10-05 42.98, 10-06 43.00, 10-07 42.37, 10-08 42.59, 10-09 43.54, 10-12 43.54, 10-13 42.87, 10-14 42.60, 10-15 41.58, 10-16 41.83, 10-19 41.93, 10-20 42.94, 10-21 42.51, 10-22 41.85, 10-23 42.59, 10-26 34.15, 10-27 34.30, 10-28 33.62, 10-29 33.14, 10-30 32.46
```

### What it shows, from the code

All citations are to `altdata/move_screen.py` and `config/move_screen.yaml` on this
branch. The rules, as the code holds them:
- **A member is flagged** (`screen_points`) when the larger of |z1| and |z5| is at
  or past `sigma` (2.5). Each z is the session's log change against the same
  horizon's changes over the trailing `history_days` (1,826), and needs
  `min_observations` (500).
- **A country is flagged** (`classify`) when any of its members is flagged. The
  flag is two-sided, in either direction.
- **The session's state** (`classify`):
  - **systemic:** `co_movement_share` 0.8 and |median stress z5| at least
    `systemic_median_z` 1.0;
  - **idiosyncratic:** exactly one country flagged;
  - **mixed:** two or more flagged;
  - **quiet:** none.
- **A shock** (`contagion_states`) is opened only on an **idiosyncratic** session,
  for its one country, dated that session. It passes if, within
  `contagion_sessions` (5), a session is systemic or an EM spread's z5 is at least
  `spread_sigma` (2.0). It lapses when the five sessions close without either.

The z-scales quoted below for October before the 19th are approximate. They are
not stored: `screen.move` rows begin on 19 Oct. They use the scale implied by
EWZ's stored z1 of 26 Oct (a log change of -22.09% at z1 -12.38, so about 1.78% a
day, the mean taken as zero). On that scale the stored z1s of 27–30 Oct are
reproduced within 0.06. The exact figure for any day is
`python -m altdata.move_screen compute --day 2026-10-DD`.

**1. The two Brazil episodes, the thresholds met and the member that carried each.**

*5–12 Oct.* On 5 Oct USD/BRL fell from 5.2222 to 4.9879 (a log change of -4.59%,
the real stronger) and EWZ rose from 38.19 to 42.98 (+11.82%, about +6.6 on the
scale above). Both are relief moves. The flag is two-sided, so a relief move
crosses 2.5 as a stress move does.
- **5 Oct:** the 1-day horizon. EWZ certainly crossed; FX's z is not stored.
- **6–9 Oct:** the 5-day horizon. Both members' 5-day windows still contain 5 Oct.
- **12 Oct can only have been the FX leg.** FRED has no 12 Oct point (the US
  holiday), so the FX member was read on its 9 Oct point inside the 7-day
  allowance, and its 5-day change from 2 Oct (-4.77%) still holds the jump. EWZ's
  1-day change on 12 Oct was 0, and its 5-day change from 5 Oct +1.29% (about 0.4
  on the scale).
- None passed to the basket or to EM spreads, so all lapsed (`contagion_states`).
- These shocks were relief moves, which the contagion rule reads as "shocks" all
  the same. The rule tests passing, not direction.

*26–30 Oct.* EWZ fell from 42.59 to 34.15 on 26 Oct, z1 -12.38: the 1-day horizon,
in stress terms (an ETF falling). From 27 to 30 Oct it stayed flagged on the
5-day horizon alone: z5 between -5.39 and -6.27, with |z1| at most 1.1. **The
equity leg carried all of it.** FX was never flagged in October, and on those
sessions it was read on its 23 Oct point (Answer 3).

**2. Why no shock is dated 26 Oct. This is the design, and it leaves a gap.**

It is not a one-day lag. The contagion screen needs neither two members, nor the
FX leg, nor a z5 crossing, nor the previous session's data. `contagion_states`
opens a shock only on a session whose state is **idiosyncratic**, meaning exactly
one country flagged. On 26 Oct Indonesia was flagged beside Brazil, so the state
was **mixed**, and a mixed session opens no shock for any country. The 27 and 28
Oct sessions were Brazil alone, so the shocks are dated 27 and 28 Oct. The 29 and
30 Oct sessions were mixed again, and opened nothing.

**It is a design gap.** The rule as filed concerns "a single-country shock", and
the code reads that as "the only country flagged that day". A large shock that
coincides with an unrelated flag elsewhere is never tracked. That is what happened
to Brazil's 12-sigma day.

The proposal, for the operator only:
- **Open a shock for each flagged country on a mixed session too**, keeping
  "systemic" as the state that passes it.
- **Or open one on any session where a member's |z1| passes a larger bar**
  (option (a) below).

**A second finding: the past sessions' states are not point in time.**
- `write` is called with no cutoff, so `contagion` reclassifies the past ten
  sessions from the store as of the run. That includes rows published after
  those sessions, such as H.10's weekly batch.
- So a session's state can differ from what its own close stored and printed:
  - `screen.em` stored 20 and 21 Oct as *mixed* (India and Indonesia), but the
    26 Oct run's contagion treats both as Indonesia-alone shocks;
  - Brazil 7 Oct first appears on the 21 Oct run;
  - Brazil 12 Oct disappears after the 20 Oct run.
- The proposal, for the operator only: classify each past session as of that
  session's own close (its 16:45 cutoff), or read the stored `screen.em` row, so a
  shock's history is what the close knew. Nothing is changed here.

**3. The FX leg's lag.**
- **The store's allowance:** `fred.usd_brl` is FRED's DEXBZUS from the H.10
  release (`altdata/config.py`), in the `fred_h10` family of
  `config/publication_lags.yaml` (the publication-lag families):
  `lag_sessions: 6`, `max_lag: 7`. The reason given: H.10 posts the previous
  week's dailies on Monday afternoon.
- **How the screen reads it:** through `st.as_of(key, cutoff)` (`_points`), so a
  row counts only once its **available_at** is at or before the cutoff.
  `daily_points` then dates it by its **observed_at**.
- **The freshness test** in `em_member_moves` (`member_max_lag_days`, 7) is
  measured on the observed_at date.
- **So on 26 Oct** the FX leg was the 23 Oct rate, posted the week before. The 26
  Oct move could not reach the FX leg until H.10's next posting, after 1 Nov's
  read, which still ends at 23 Oct.

**4. The first live session.**
- **The first stored `screen.em` row is 19 Oct 2026.** The EM layer's code entered
  the repository on 11 Oct (`dbffddec`, C1).
- **The shocks dated 5–12 Oct were never seen live.** They were computed on the
  19 Oct run by `contagion`'s look-back over ten past sessions, from history.
- **No ledger row or note recorded the first live session.** It is recorded here:
  the first live session of `screen.em` and `screen.em_contagion` is **19 Oct
  2026**, per the reading.

**5. The DI curve and Brazil's local bonds: not stored, a listed gap.**
- `metrics_registry.yaml` holds no DI-curve key, no local-bond index and no daily
  Brazilian rate.
- Brazil's rate keys are monthly: `em.bis.policy_rate.bra`, and the lenses built on
  it, `em.lens.real_policy_rate.bra` among them.
- `config/move_screen.yaml` lists only `fred.usd_brl` and `yfinance.mkt_ewz` for
  Brazil, so the screen cannot fire on rates.
- This is a listed gap under the 16 Oct rule. Option (c) below names a candidate.

### The amendment, drafted for the operator (rule 31: options and a recommendation; the operator rules)

**(a) Same-day firing from the equity leg.**
- *Options:*
  - (i) a member's |z1| at or past a stated bar opens its country's shock on that
    session, whatever the session's state (systemic excepted, which is contagion
    already), with the FX leg joining when H.10 posts;
  - (ii) open a shock for every flagged country on a mixed session (Answer 2);
  - (iii) the dating stays as built.
- *The arithmetic for 26 Oct:* EWZ's z1 was -12.38, so any bar from 2.5 to 12.38
  opens Brazil on 26 Oct, one session before the 27 Oct shock that the build
  opened.
- *What October's other Brazil moves would do under (i):*
  - EWZ's only other |z1| past 2.5 was 5 Oct (about 6.6 on the scale above, a
    relief move), already a shock as built.
  - Every other October session is below 1.6.
  - FX's 1-day z's are not stored. Its largest October 1-day move was 5 Oct
    (-4.59%), the same session.
  - So for Brazil, (i) adds **one** firing in October (26 Oct) at any bar between
    2.5 and 6.6, and **one** at any bar up to 12.38.
- *What option (ii) would add:* it would open shocks on the seven mixed sessions
  (19, 20, 21, 22, 26, 29 and 30 Oct): 16 country-shocks, of which Brazil's are 26,
  29 and 30 Oct.
- *Limits of the count:* the other countries' z1s are not in the reading, so their
  extra firings under (i) are not counted here. `compute --day` gives them.
- *Recommended:* **(i) at a bar of 4 on the 1-day horizon**, which separates the
  two Brazil events from everything else in October with room on both sides.
  Also, as a separate ruling, **classify past sessions as of their own close**
  (Answer 2's second finding). That keeps a shock's history what the close knew,
  and changes no threshold.

**(b) The FX leg's source.**
- *Candidate:* the Brazilian central bank's SGS time-series service, which publishes
  the daily PTAX USD/BRL rate the same day through a public JSON API that asks for
  no key.
- *How it would enter:* as a candidate family under A96's `config/price_sources.yaml`
  switch (on `a96-price-migration-fred`, not on this branch), for the 16 Oct check
  (robots, terms, availability) when it is built.
- *Not now:* nothing is fetched now, and the series id is to be confirmed at that
  check. FRED's DEXBZUS stays the reference until the switch. No yfinance symbol
  (D33).
- *Recommended:* **accept as a candidate for the check.** It removes the up-to-7-day
  lag that kept the FX leg out of 26 Oct.

**(c) Brazil's local rates as a third member.**
- *Candidate:* the same SGS service's policy-rate series and a DI-pre swap tenor,
  named as a listed gap with that candidate, for the operator to accept or leave.
- *Rule 30 is not touched:* nothing by hand.
- *Consistency:* the same candidate would serve 105(b)'s EM local bonds for the
  `em_scorecard`.
- *Recommended:* **list it with the named candidate, and check it at the same 16 Oct
  check as (b).** The October loss the order describes came through rates, which no
  sigma on FX or equity can see.

**(d) Rights.**
- Nothing changes a flag, a dial, a weight or a decision. The screen is report-only
  (Batch 4 item 10, SR-46's rights): the idiosyncratic line is a candidate for the
  narrative register, and the write is the operator's.
- That holds after any of (a) to (c).
- *Recommended:* **confirm.**

**The Doctrine #2 pack:** B104 has pushed Part 12 on `b96-doctrine-2-pack-refresh`,
so the amendment is added there as **D2-90**, options only.

**Change nothing in code or config** until the operator rules. The register's
105(a) line records "read 1 Nov 2026; amendment drafted in b91-notes.md Part 3,
pending the operator's ruling".
