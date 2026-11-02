# A84 notes: the feed summary and four publication-lag families

Branch `a84-feed-summary-and-allowances`, branched from origin/main at
`9fd6bd40` (the A61b merge). Branch-only; it merges after the 1 Nov Monthly.
Laptop session, 28 Oct 2026. Nothing was run on the box.

## Part 1: the summary printer

`altdata/feeds.py`'s `pull` printer gives bars, prediction_markets and fed_funds
their own lines, built only from what each pull already returns. No pull, return
value or exit code changes. Against stubbed returns in the box's shapes it prints:

```
  bars    10 instruments, 0 short
  prediction_markets 84 markets, 604 written, 0 errors
  fed_funds 14 served, 0 failed
```

"short" uses the same test `pull_bars` logs (an error, or no final bar). No gate
runs `feeds pull` through the printer (checked: `tools/validate_feed*.py`,
`validate_feeds_scheduled.py`), so no fixture case was added and no gate was
added.

## Part 2: the four families

**The laptop store's vintage clock (step 2) could not be read.** `data/chester.db`
on the laptop holds no `em.*` and no `clevfed.*` rows, and its FRED rows are all
`fred:csv_migrated` (each stamped with the migration instant, not a vintage), the
newest from May 2026. ALFRED would have given the vintages, but the laptop's FRED
key was not read in this session. D below therefore comes from the publishers'
own calendars and, for the IMF and the World Bank, from the newest period and
publication stamp in their own responses, read once on 28 Oct 2026 through the
writers' request builders (read-only, nothing stored). Sessions are counted by
`derived.sessions_between`, the store check's own counter.

### fred_monthly_release: outcome (c), lag left at 22 (max_lag 25)

- **D, BEA** (bea.gov/news/schedule, read 28 Oct 2026): "Personal Income and
  Outlays, September 2026" on 29 Oct 2026, 21 sessions after 30 Sep. October's is
  25 Nov and November's 23 Dec. This is the normal cycle, not a delay.
- **D, BLS** (bls.gov/schedule/2026/10_sched.htm and 11_sched.htm, read 28 Oct
  2026): JOLTS for August was released 29 Sep (20 sessions after 31 Aug), and for
  September on 3 Nov (24 sessions after 30 Sep).
- **The family's own arithmetic** (lag = D + 10, months dated the 1st):
  - PCE: D 21, so lag 31. On the box, fred.pce at 1 Aug was 62 sessions old on
    28 Oct, the day before the next print.
  - JOLTS: D 24, so lag 34. job_openings at 1 Aug will be 65 sessions old on
    2 Nov.
  - With a holiday's slack the family needs about 35.
  - The 22 in the file is short of its own arithmetic. Its reason ("one to six
    weeks ... 32 plus 22") does not follow from the header's D + 10 either: six
    weeks is D = 30, so lag 40.
- **35 is above max_lag 25**, so nothing is set. **Needs you.**

### em_monthly: outcome (c) for the ITG leg, (b) for two keys; lag left at 45 (max_lag 50)

- **How the keys are dated.** Every `em.*` monthly key is dated at the month's
  END, not the 1st (`imf_em.py`: "observed_at is the month-end"). So the
  arithmetic is lag = D + 21 - 32 = D - 11, not D + 10.
- **What the IMF states.** Its dataset pages (data.imf.org, IMF.STA:ITG and
  IMF.STA:IL, read 28 Oct 2026) state no schedule, and the release calendar
  renders only in a browser. D is therefore read from the IMF's own responses of
  28 Oct 2026, whose publication stamps are the same morning.
- **IL (reserves).** Ten countries are at August or September 2026, so D is about
  4 to 8 weeks and well inside 45. **CHN is at June 2026** while its peers are at
  Aug-Sep. That is **(b)**: the IMF's China row is late this cycle (SAFE's own
  monthly reserves are current). em.ifs.reserves_usd.chn stays stale, which is
  the honest reading.
- **CPI.** Most countries are at August or September 2026, IND at July. **ARE is
  at December 2025**: **(b)**, the UAE CPI series has stopped updating at the
  IMF. em.cpi.yoy.are stays stale.
- **ITG (imports).** The newest period for ANY country on 28 Oct is July 2026
  (BRA, CHN, IND, KOR, SAU, TWN), so the dataflow runs about three months behind.
  IDN, MEX, MYS, POL and THA are at June.
  - For the leaders, July was not out by the time the box's 28 Oct check read it,
    so D is about 62 sessions (31 Jul to 28 Oct).
  - That gives lag D - 11 = 51, plus slack 53. **That is above max_lag 50**, and
    the five laggards need more still: June at 30 Jun is already 84 sessions old.
  - So: **(c)**, nothing set. **Needs you.**
  - The national offices publish imports within four to six weeks, so the delay
    is the IMF's, not theirs.
- **The family is mixed.** Its other legs (IL, CPI, BIS policy rates) would need
  only about 30 by the same arithmetic. The family carries 45 for all of them.
  Splitting it would be a new family, which this paste does not allow.
- **What stays stale.** The five em.itg.imports_usd keys and, through
  inheritance, their em.lens.reserves_import_months.* keys stay stale.

### em_quarterly: outcome (a), lag 65 -> 53 (max_lag 70 unchanged)

- **D** comes from the World Bank's "2026 QEDS Submission and Publication
  Calendar" (the PDF linked as "Publication calendar" on
  worldbank.org/en/programs/debt-statistics/qeds, read 28 Oct 2026). It sets two
  publication rounds a quarter:

  | Quarter | First round | Second round |
  |---|---|---|
  | 2025Q3 | 16 Jan 2026 | 30 Jan 2026 |
  | 2025Q4 | 16 Apr 2026 | 30 Apr 2026 |
  | 2026Q1 | 17 Jul 2026 | 31 Jul 2026 |
  | 2026Q2 | 16 Oct 2026 | 30 Oct 2026 |

- **The family's only keys** are em.qeds.* and the em.lens.ext_debt_gdp / reserves_st_debt
  lenses built on them (44 keys). `wb_qeds.py` dates a quarter at its END.
  - Before the next quarter's second round, the newest is 147 sessions old
    (31 Mar to 29 Oct). That is 95 + 52, and with a holiday's slack, 53.
  - The 65 assumed first-day dating and "about a quarter after", which matches
    neither the dating nor the calendar.
  - Lowering it is the correction, with the citation in its `reason`. It clears
    no key.
- **What the World Bank's API showed on 28 Oct** (lastupdated 2026-10-16): ten
  countries at 2026Q2, **CHN at 2025Q4**. CHN missed both 2026Q1 rounds and
  2026Q2's first. **(b)**: em.qeds.*.chn and em.lens.*.chn stay stale, now 207
  sessions against 148.

### clevfed_rules: outcome (c), lag left at 7 (max_lag 9)

- **D.** The indicator page
  (clevelandfed.org/indicators-and-data/simple-monetary-policy-rules, read 28 Oct
  2026) says "Last updated September 4, 2026", "Next update November 20, 2026",
  and its table starts at "2026.3". No frequency is stated.
- **What the file actually carries.** The chart data
  (`-/media/files/webcharts/policyrules/chartdata.csv`, read 28 Oct 2026) dates
  its first row **6/1/2026**, and the writer stores that date
  (`observed_at = path[0][0]`). That is why the box reads 2026-06-01.
- **Why the lag is short.** The family's reason counted from 1 Jul, which is
  where its arithmetic went wrong.
  - Counted from the stored date, the newest is 120 sessions old before the
    20 Nov update (1 Jun to 19 Nov), against the quarterly allowance's 95. So the
    lag would be 25, and about 27 with slack.
  - That is above max_lag 9. **(c)**, nothing set. **Needs you.**
  - D itself, from the stored observation to its publication, is 67 sessions
    (1 Jun to 4 Sep).

## Step 4: what stays stale, and the box count

**Box ages on 28 Oct against this branch's allowances:**

| Keys | Age (sessions) | Allowed | Verdict |
|---|---|---|---|
| fred.pce, saving_rate, real_disp_income and their calc.* | 62 | 54 | stale, unchanged |
| fred.job_openings, hires_total, quits_rate, layoffs and their calc.* | 62 | 54 | stale, unchanged |
| em.itg.imports_usd.{idn,mex,mys,pol,tha}, em.lens.reserves_import_months.* | 84 | 77 | stale, unchanged |
| em.ifs.reserves_usd.chn | 84 | 77 | stale, unchanged (b) |
| em.cpi.yoy.are | 207 | 77 | stale, unchanged (b) |
| em.qeds.*.chn, em.lens.*.chn | 207 | 148 (was 160) | stale, unchanged (b) |
| em.qeds.* and em.lens.* (other ten countries, 2026Q2) | 84 | 148 | fresh, unchanged |
| clevfed.rules_* | 104 | 102 | stale, unchanged |

Even if the box had not yet pulled the 16 Oct QEDS release, its non-China keys
would sit at 31 Mar (146 sessions) under 148: still fresh.

**Expected box count: 138 (range 138 to 138).** The branch's one change lowers
an allowance that no box key sits between (148 to 160). The count will move only
with the publishers:

- PCE on 29 Oct clears fred.pce, saving_rate and real_disp_income and their calc.*
  keys;
- JOLTS on 3 Nov clears the four JOLTS keys and theirs;
- the Cleveland Fed's update on 20 Nov clears clevfed.rules_*.

## Needs you (ruled 28 Oct 2026 as D42; applied by A86, below)

1. **fred_monthly_release.** BEA's and BLS's 2026 calendars put D at 21 (PCE) and
   24 (JOLTS) sessions, so the file's arithmetic gives lag 31 to 34, 35 with
   slack, against max_lag 25. Options:
   - raise max_lag to about 36 and the lag to 35, citing the two calendars;
   - or split the slowest releases (PCE and personal income, JOLTS) into a
     family of their own.

   Until then, about 7 FRED keys and their derived calc.* keys show stale for the
   last week or so of each cycle.
2. **em_monthly, the IMF's ITG leg.** The dataflow's newest is July (about 3
   months; 62 sessions after 31 Jul at least) for its leaders and June for five,
   so lag would be about 53 (and more for the laggards) against max_lag 50.
   Options:
   - accept these keys reading stale as the IMF's delay;
   - or split ITG into its own family with its own bound (and IL/CPI/BIS, which
     need about 30, into theirs).
3. **clevfed_rules.** The CSV dates its first row 6/1/2026, not 1 Jul. Counted
   from the stored date the lag is about 27 against max_lag 9. Options:
   - raise max_lag to about 28 and the lag to 27;
   - or ask for a writer change that dates the starting row by the quarter it
     names. The page calls it 2026.3; read as Q2 ending 30 Jun, the lag would be
     about 5 and inside 9.

   Either is outside this paste's shared files.
4. **(b), named for the record.** These keys stay stale because the publishers
   are late, and that is the honest reading:
   - em.ifs.reserves_usd.chn (IMF IL, June against peers' Aug-Sep);
   - em.cpi.yoy.are (IMF CPI, December 2025);
   - em.qeds.*.chn and em.lens.*.chn (World Bank QEDS, 2025Q4, missing three
     rounds).

## Gates (one at a time, foreground, laptop)

- `tools/validate_b51_registry_html.py`: 25 passed, 0 failed.
- `tools/validate_feed_repair.py`: 50 passed, 0 failed.
- `tools/check_registry.py`: OK.

## CI

CI queued, run 40788050524 (Gates, on 757cfc21), read once on 28 Oct 2026; not waited on.

## A86: the rulings applied (D42, 28 Oct 2026, 19:45 ET)

Paste committed as `docs/pastes/A86.md`, on this branch at 803a0b96.

| Family | Ruling | Lag | max_lag | Allowance |
|---|---|---|---|---|
| fred_monthly_release | D42.1 | 22 -> 35 | 25 -> 36 | 54 -> 67 |
| em_monthly_itg (new) | D42.2 | 53 | 58 | 85 |
| em_monthly | D42.2 | 45, unchanged | 50, unchanged | 77 |
| clevfed_rules | D42.3 | 7 -> 27 | 9 -> 30 | 102 -> 122 |
| em_quarterly | (A84, outcome a) | 53 | 70 | 148 |

**How each was applied:**

- **D42.1.** One family. The reason states the arithmetic: JOLTS's D = 24
  (3 Nov), plus 10, plus one session's slack = 35, with BEA's 29 Oct and BLS's
  29 Sep dates cited. It also says that this is the publishers' delay, not a
  number chosen to clear keys.
- **D42.2, the inheritance check.** The em.lens.reserves_import_months.* entries
  declare no `inputs` (the resolved registry shows none), so the inheritance
  rule cannot carry the imports' lag to them. The new family therefore matches
  `em.itg.*` and `em.lens.reserves_import_months.*` explicitly: 11 + 11 = 22
  keys. It sits before em_monthly, because the first match wins. em_monthly keeps
  the other 56 keys (BIS policy rates, IMF CPI, IMF reserves and their lenses).
- **D42.3.** The writer's dating is unchanged. The reason cites the page's
  schedule (read 28 Oct) and the 6/1/2026 row date, against which the newest is
  120 sessions old before the 20 Nov update.

### D42.4: genuinely stale, publisher delays, no change (for Audit #5's list)

| Key(s) | Newest observation | Publisher | Family, allowance | Age on 28 Oct |
|---|---|---|---|---|
| em.ifs.reserves_usd.chn | 2026-06-30 | IMF IL (peers at Aug-Sep 2026) | em_monthly, 77 | 84 |
| em.cpi.yoy.are | 2025-12-31 | IMF CPI (the UAE series has stopped) | em_monthly, 77 | 207 |
| em.qeds.ext_debt_usd.chn, em.qeds.st_debt_usd.chn | 2025-12-31 | World Bank QEDS (missed 2026Q1's two rounds and 2026Q2's first) | em_quarterly, 148 | 207 |
| em.lens.ext_debt_gdp.chn, em.lens.reserves_st_debt.chn | 2025-12-31 | built on China's QEDS | em_quarterly, 148 | 207 |

### Which keys stop being stale, and the box count

**The laptop store cannot show it.** It holds no em.* or clevfed.* rows, and its
FRED rows end in May. So the keys are counted from the box's own listing of
28 Oct, and the registry's resolved allowances under this branch.

**Under this branch's lags, on 29 Oct (age 85 for a month-end key at 30 Jun, 63
for a first-day key at 1 Aug):**

- **The seven named FRED keys.** fred.pce, job_openings, hires_total,
  quits_rate, layoffs, saving_rate and real_disp_income (63 against 67), and the
  11 calc.* keys that declare them as inputs:
  - calc.naive_expectation.{pce, job_openings, hires_total, quits_rate, layoffs};
  - calc.surprise_vs_naive of the same five;
  - calc.yoy_pce.

  That is 18 keys. Any other of the box's 27 stale fred.* keys that is monthly
  and between 55 and 67 sessions old clears too. The box's listing named only
  these seven, so the upper bound is uncertain.
- **The imports leg.** em.itg.imports_usd.{idn, mex, mys, pol, tha} and their
  em.lens.reserves_import_months.* (85 against 85, fresh on 29 Oct only): 10
  keys, 11 if China's lens is dated June.
  - **Caution:** these turn stale again on 30 Oct (86 against 85) unless the IMF
    posts July for those five.
- **The Cleveland Fed.** clevfed.rules_* (105 against 122): 4 keys.

**Estimates:**

- **Cleared under the branch:** 32 to 33 known keys, up to about 45 if the other
  fred.* and calc.* keys on the box's list are monthly releases in the same
  window.
- **Still stale:** the six D42.4 keys, and everything not in these four
  families.

**The box count, by scenario:**

- **What the box actually runs tomorrow (main's lags, this branch is
  branch-only).** After tonight's evening note and tomorrow's 16:10 run:
  **134 to 140**. That is 138 plus or minus the keys aging across their
  allowance by one session.
- **The 29 Oct PCE release, counted separately, on main.** If the 16:10 pull
  stores September's PCE, it clears fred.pce, saving_rate and real_disp_income
  and calc.naive_expectation.pce, calc.surprise_vs_naive.pce and calc.yoy_pce:
  6 keys, so **128 to 134**.
- **Once this branch merges (after 1 Nov), from the same 29 Oct state:**
  **95 to 106**. That is 138 less 32 to 45, plus the day's aging.
  - The PCE release changes nothing in this count, because the PCE keys are
    already inside 67.
  - From 30 Oct the 10 to 11 imports keys may return.

### Gates (A86, one at a time, foreground, laptop)

**Results:**

- `tools/validate_b51_registry_html.py`: 25 passed, 0 failed.
- `tools/validate_feed_repair.py`: 50 passed, 0 failed.
- `tools/check_registry.py`: OK.

**Two gates pinned the old values, and their pins were moved to the ruled
values.** Each rule is unchanged; each pin is the config's number copied into the
gate. These files are outside the paste's shared files, and are flagged for the
operator:

- **`validate_b51_registry_html.py`.** fred.cpi's allowance changes from 32 + 22
  to 32 + 35.
- **`validate_feed_repair.py`.** The core-PCE and yoy/r_real allowances change
  from 54 to 67, and clevfed.rules_start's from 95 + 7 to 95 + 27.

**Kept on the config side instead.** That gate's check that the Cleveland Fed's
reason quotes "read 24 Oct 2026" is held by the config. The reason now says
"first read 24 Oct 2026, re-read 28 Oct 2026", which is true: A64 read it first.
