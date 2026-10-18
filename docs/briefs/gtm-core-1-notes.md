# gtm-core-1 — the J.P. Morgan Guide batch, part 1 (session A, 17 Oct 2026)

**What it builds on, and the merge order.** `gtm-core-1` was cut from the tip of `el-4-6`. It therefore carries:
- 6b (parts 1 to 3);
- item 52;
- the Enterprise Layer's EL-4 to EL-6, with this paste's step 0 on top.

It merges **after `el-4-6`, in the second stitched chain**. It is branch-only: pushed, not merged, not deployed, nothing run on the box, and no unit enabled or started.

The work is the GTM change order (`docs/change-order-jpm-gtm-2026-10-03.md`, ruled 3 Oct 2026) for the seven adopted items that compute from data the store holds or FRED serves: GTM-1, 7, 8, 9, 13, 15 and 21. Part 2 takes GTM-3, 4, 10 and 12.

---

## Step 0

### el-4-6's CI

| Run | Commit | Result |
|---|---|---|
| 39070454969 | `6501795` | **failed**, one check of mine: 265 passed and 1 failed in `validate_monthly_stack`. EL-6's system-metrics table is a fifth detail table, and the gate listed four. |
| 39070524418 | `a629f1d` | **failed**, the same one check |
| 39086764981 | `8f82653` (the gate fix, the User-Agent rule, rulings 4 and 5) | **green** |

`el-4-6`'s notes record all three.

**A push hold-up, resolved.** GitHub began refusing pushes that would publish a private address (GH007). This repo's local `user.email` still overrode the new global no-reply address. You removed the override. I then re-authored my two unpushed commits with the no-reply address and pushed `el-4-6` as a plain fast-forward: `a629f1d` to `8f82653`. Nothing on origin was rewritten.

### The User-Agent rule (ruling 2)

- **One generic identity.** `altdata/sources/user_agent.py` holds it.
  - `generic()` is `chester-reports/1.0 (+https://github.com/achester-trading/chester-reports)`.
  - `browser_like()` is the same in the `Mozilla/5.0 (compatible; …)` shape. Some hosts refuse a bare product token.
  - `is_sec_host()` and `for_url()` route sec.gov and its subdomains to `edgar.user_agent()`, and every other host to the generic string.
- **Every non-SEC caller moved to it:**
  - `_base` (the default for every `http_get_*`);
  - `listings`;
  - the `borrow`, `shielded` and `vxcurve` loggers;
  - CFETS, iShares, SAFE and prediction markets;
  - the voices scan, first.
- **The voices scan.** Its `Fetcher` routes by host. It refuses an SEC URL before any request when `CHESTER_SEC_CONTACT` is unset, so EDGAR never sees an anonymous or generic agent. Its 13F pull alone reads the SEC form. The scan no longer depends on the SEC contact for any other source.
- **`edgar.py` keeps the SEC form**, for sec.gov only. `fundamentals.py` reads it for EDGAR submissions (data.sec.gov).
- **The gate:** `tools/validate_secrets.py` group **J**. Session B's `audit-leftovers-1` adds its own group I to the file, so this one is lettered J to keep the stitch to the call list alone. It checks:
  - **production code:** no User-Agent literal carries an `@` or `mailto`; no production file writes one by hand outside the two homes; no non-SEC caller imports edgar's;
  - **shell scripts, units and YAML:** no User-Agent carries an address;
  - **fixtures both ways:** sec.gov and data.sec.gov get the contact form; federalreserve.gov and a sec.gov look-alike get the generic string; no contact means None;
  - **a planted file** with all three faults is caught.

  It passed 54/0, and `validate_voices` passed 72/0.
- **BLS probe.** On 25 Sep, bls.gov returned 403 to a User-Agent containing a URL. On 17 Oct I probed again from the laptop:
  - api.bls.gov returned 200 for both the bare token and the new string;
  - www.bls.gov/feed returned 403 for every form, the bare token included.

  So the old finding could not be re-tested from here. Watch the first box run's news feeds (needs-you 6).

### The two EL-6 answers, applied on `el-4-6` (rulings 4 and 5)

- **Ruling 4, the withheld-drafts log.** Every edition now writes it (`withheld_log.REPORTS`):
  - the 07:00 anchor: its withheld narrative, the reason only, with the draft staying in the run log;
  - the 16:45 close, the Weekly, the Monthly and the Quarterly, as before;
  - the 12:30 alert slot, through `midday_gate.run`. The alert is unnarrated today, so nothing is written until a narrated alert's audit withholds a paragraph.

  `validate_system_metrics` group D holds all six writers.
- **Ruling 5, the Audit #4 baseline.**
  - **The main table's baseline column** prints the agenda's feeds line ("official 96/96; external 52 of 5x, one stale (AAII, the operator's drop); the 9 Oct line"), labelled "by hand, Audit #4, 14 Oct".
  - **A second table** gives the audit's measured figures of 14 Oct, each labelled:

    | Measure | Figure |
    |---|---|
    | Store rows | 2.33 million, 688,000 of them FRED |
    | Store growth | about 86,000 rows a weekday |
    | Disk free | 14 GB of 38 GB |
    | Backup zip | about 115 MB |
    | Drive backup folder | 7.6 GB |
    | Days up, session hours, model cost | not recorded |

  - **Removed:** incidents and withheld drafts also print "not recorded". The ruling names no incident figure, so the earlier "INC-1 to INC-9, one open" no longer prints (needs-you 9).

  `validate_system_metrics` passed 21/0.

---

## Part 1: the seven items

Every new series carries its `family` and `long_window`.

**Sourced figures.** A figure only the Guide has is never recomputed. `config/gtm.yaml` (`sourced`, 33 entries) declares each with:
- the scan's words, quoted exactly;
- the scan's section reference;
- its slide, which is null throughout because the scan recorded none per figure. That follows the 8 Oct narrowing of the scans ingest: the slide is stored when recorded, otherwise the section.

`altdata.scans ingest` stores them, as `GTM-n · <label>`, beside the 44 reference-table rows. The source is the scan's URL, as of 30 Sep 2026, read 3 Oct. A figure whose quote the scan does not contain is refused, and so is one without a section or an as-of. Reports read them back from the store and print the stored text verbatim.

**Modules.**
- `altdata/gtm.py` computes.
- `daily_cascade/gtm_block.py` lays out.
- `tools/base_rates.py` stores GTM-7, 8 and 9 as `baserate.*` tables. A table not yet stored is itself a recompute trigger, so the six existing tables are untouched and there is no method bump.
- `python -m altdata.gtm show | check` prints the tables and checks the declared figures.

**The laptop sanity run.** On 17 Oct I ran the same functions over public sources. These figures are a method check, not committed as figures. The sources were:
- Shiller's current sheet through the writer's own reader;
- FRED's public CSV;
- yfinance's ^GSPC.

They are in each item below.

### GTM-1, the inflection-points table (SR-37)

- **The historical rows** are the Guide's figures where the scan states them, and **"not in the scan"** otherwise. The scan states 6 of the 32 historical cells:
  - the 10-year at the four tops: 6.2%, 4.7%, 1.6% and 1.6% (§3);
  - the Mar 2000 multiple, 25x (§1);
  - the 12 Oct 2022 low, 3,577 (§6).

  The order expected eight full rows. The scan names the dates and gives these six figures, nothing more (needs-you 1). The Guide's own 30 Sep row is printed: 7,652, 19.0x, 1.4% and 5.29% (§6).
- **Today:** the level is ^GSPC's close and the 10-year is `fred.yield_10y`. The dividend yield is Shiller's stored trailing dividend over price, labelled with its month; no fundamentals writer stores one. The forward P/E prints **"not stored"**, because no writer stores forward earnings (needs-you 2).
- **Where it prints:** the Monthly's Slow layers, "Inflection points (the Top & Bottom standing exhibit)". A base-rate row, "the 10-year at the four prior tops (n=4)", joins "Base rates: Top & Bottom".

### GTM-7, the stock–bond correlation regime table (amends SR-9)

- **Method:** monthly total returns from Shiller's sheet. The equity leg is the S&P Composite, price plus dividend ÷ 12. The bond leg is a 10-year par bond bought at last month's GS10 and priced at this month's, plus a month's coupon. Each era is the average of the 24-month rolling correlations whose window ends in it, with CPI on the year. An era our history does not cover prints the Guide's figure, labelled. Shiller reaches 1871, so the store covers all three eras.
- **The regime word:** positive at or above +0.10, negative at or below −0.10, near zero between. Book A's rule table reads the word only (draft row A-6), and nothing automated does.
- **The laptop run:**

  | Era | Ours | The Guide |
  |---|---|---|
  | 1964–99 | **+0.30 / 4.86%** | +0.28 / 4.86% |
  | 2000–20 | **−0.27 / 2.13%** | −0.31 / 2.13% |
  | 2021 to Jun 2026 | **+0.12 / 4.39%** | +0.33 / 4.52% (2021–25) |

  The eras reconcile, and the inflation figures match to the hundredth. **The current 24-month correlation, to Jun 2026, is −0.29: negative.** The positive 2021–25 regime has turned in our data, while the Guide's era figure stops at 2025.
- **SR-9's amendment** is committed as drafted under rule 31.
- **Stored as** `baserate.stock_bond_eras`.

### GTM-8, the sentiment turning-point base rate (SR-40)

- **Our own turning points** of `fred.uoM_sent` (UMCSENT; quarterly before 1978). The rule, set by me:
  - strictly the extreme within 12 months either side, where a tie is neither;
  - turning points alternate;
  - a swing of at least 15 points.

  Each is followed by the S&P 500's next-12-month price return, from month-end ^GSPC closes, with n, mean and median.
- **The Guide's figures** print beside ours as sourced figures: 10 peaks at +4.8%, 9 troughs at +24.1% (§4).
- **The caveat** prints in the row in the order's words: "every sampled trough coincided with a price low; this one is at a high". The row also gives how many of our troughs came with the S&P 500 at least 10% below its 12-month high.
- **The disagreement entry** is a draft in `config/narratives.yaml` (`disagreements: gtm8_sentiment_trough_at_high`, status draft, read by no code until you accept it).
- **The laptop run, 1952-11 to 2026-08:**
  - troughs: **n=14, mean +22.4%**, median +22.2%;
  - peaks: **n=14, mean +0.6%**, median −1.6%;
  - 9 of the 14 troughs came at a price low;
  - the latest reading, 51.7 (Aug 2026), sits at the 1st percentile of 676, with the S&P 500 2.0% below its high.

  The Guide's 48.1 is September's; FRED's public CSV ended at August that day.
- **Stored as** `baserate.sentiment_turning_points`.

### GTM-9, the all-time-high base rates (SR-41)

- **From ^GSPC's daily closes.** An all-time high is a close above every prior close. **The floor definition is the scan's** (§4): never afterwards closed 5% or more below, to the end of the data. "Within a week" means another all-time high in the next five sessions.
- **What prints:** the 1988–2025 sample against the Guide's 27 / 7% / 31% / 80%, and this year.
- **The laptop run, 1988–2025:** 778 all-time highs in 9,572 sessions.

  | Measure | Ours | The Guide |
  |---|---|---|
  | Share of days | 8.1% | 7% |
  | Share that became floors | 35.1% | 31% |
  | Followed within a week | 80.1% | 80% |
  | This year, to 30 Sep | **27** | 27 |
  | This year, to 16 Oct | 28, in 199 sessions | — |

- **The Bull Rebuttal** reads the row as the order places it, with no new right. No gate code exists to wire it to.
- **Stored as** `baserate.all_time_highs`.

### GTM-13, the fixed-income scenario table (SR-45)

- **Rows**, one per sector with a stored proxy:

  | Sector | Proxy | Yield series |
  |---|---|---|
  | Treasury 2-year | SHY | 2-year CMT |
  | Treasury 10-year | IEF | 10-year CMT |
  | Treasury 30-year | TLT | 30-year CMT |
  | Aggregate | AGG | not stored |
  | Investment grade | LQD | not stored |
  | High yield | HYG | not stored |

  - **TIPS** prints the 10-year real yield (`fred.tips_10y`) and "no proxy".
  - **Munis and MBS** print "no proxy".
- **Columns:**
  - the year-to-date total return, from close and dividend;
  - duration from `config/instrument_reference.yaml`;
  - correlations to the 10-year's change in bp and to SPY, over 252 sessions;
  - the **price** return under −100 / +100 bp: −duration × change. The reference carries no convexity, so none is applied.

  AGG prints "no duration in the reference" (needs-you 3).
- **The Guide's year-to-date figures** print beside ours as a sourced column, read off the stored figure's text.
- **Where it prints:** Plumbing & rates, in the Weekly and the Monthly. Book A's draft row A-7 reads it as a modifier.

### GTM-15, the effective tariff rate (SR-47)

- **Series:** **B235RC1Q027SBEA** (customs-duties receipts, billions, SAAR, quarterly) over 4 × the quarter's **BOPGIMP** (goods imports, millions, monthly SA). It prints with five-year and full-history percentiles.
- **It is quarterly, not monthly.** FRED has no monthly customs-receipts series; the receipts series is quarterly only (needs-you 4). The NIPA receipts are not the Census imports-for-consumption basis, so ours and the Guide's differ by construction.
- **Sourced comparison:** the Guide's 10.6% and the statutory peaks, 30.0% on 8 Apr 2025 and 15.9% including IEEPA on 20 Feb 2026 (§6).
- **The laptop run:** 2026 Q2 is **8.2%**, after 11.2% in 2025 Q4 and 9.4% in 2026 Q1. That is the 80th percentile of 20 quarters over five years and the 97th of 138 since 1992.
- **Placement:** the Monthly's Plumbing & rates, as the inflation modifier. There is no separate inflation-lens section; the 6e lenses print in the existing tables. Family `quantity`, long window `full`.

### GTM-21, the debt-service ratio (SR-5's modifier)

- **Series:** **TDSP**, with the splits **CDSP** and **MDSP**, all quarterly. On FRED today they start in **Q1 2005**, so "full history" means 2005 onward.
- **Printed** with dual percentiles in Plumbing & rates, in the Monthly's "Household debt service (SR-5's modifier)".
- **The Guide's figures** print labelled: its delinquency flows (cards 8.7%, auto 7.9%, student 7.8%, mortgage 4.0%) and the DSR at 11.1% against 15.8% at 4Q07. The scan does not name the flows' quarter, so the Guide's data date is printed.
- **There is no SR-5 row to print in.** `calc.cc_z` is not built, so the modifier has its own sub-section, and SR-5's amendment says so.
- **The laptop run:** TDSP is **11.11%** (2026 Q2), against the Guide's 11.1%. That is the 70th percentile of 20 over five years and the 22nd of 86 since 2005.
- **SR-5's amendment** is committed as drafted under rule 31.

### Fixtures and the gate

`tests/fixtures/gtm/` holds the fixtures, with every hand figure written out in its `README.md`.

`tools/validate_gtm.py` passed 42/0. It checks:
- **Sourced figures:** the declared figures pass; fixture faults are refused (no section, no quote, a quote not in the scan, a value outside its quote, an undated scan); the ingest is idempotent and point in time; printed cells are the stored text.
- **The hand figures:**
  - GTM-7: the par-bond return of −7.022%; correlation +1.00 on a linear fixture; inflation 6.1678%; an era not reached prints the Guide's figure, labelled; the regime-word bands.
  - GTM-8: −10% and +25% with n=1 each, the caveat in the row.
  - GTM-9: 6 / 50% / 4 floors / 5 repeats; 5 this year.
  - GTM-13: SHY's year to date +2.5152%; TLT's correlations −1.00 and +1.00; ±16.5% and ±1.9%; AGG "no duration"; three sectors "no proxy".
  - GTM-15: 12.3457%. GTM-21: TDSP at the 100th of 4 and the 80th of 5.
- **Absent inputs:** "not stored" or "not in the scan" in every cell on an empty store, never a blank or a zero; the base-rate rows carry n.
- **The register:** SR-5 and SR-9 keep their keys; the numbering is mechanical; the drafts are marked.
- **Placement:** the Weekly and Monthly placement holds; zero words and no charts added; at most six columns in the Weekly.
- **Nothing live:** no network, model, order or register import; no read of a default store path; the five FRED series registered with family and long_window.

**Gates extended:**

| Gate | Result | Change |
|---|---|---|
| `validate_base_rates` | 76/0 | ten tables; synthetic Shiller and sentiment series seeded |
| `validate_monthly_stack` | 266/0 | the GTM rows sit outside the generic sourced-figures table; the five rows the GTM tables print are excluded from it |
| `validate_audit_3a` | 85/0 | the new block members declared |
| `validate_st_r5_t1_rest` | 103/0 | FRED counts 57 / 159 |
| `validate_narratives` | 99/0 | — |
| `check_library` | 0 failures | the Base Rates HTML rebuilt |
| `check_registry` | OK | — |

Each was run once, locally. Every other gate is CI's.

---

## The register numbers used

The order says the adopted items take new numbers continuing from the register's last. The Audit #4 agenda (item 5) proposed **SR-37 … SR-47** for the GTM batch, in the order the change order's table lists the adopted items, and did not write them. The register's last heading was SR-34, with SR-35 and SR-36 assigned elsewhere. So I assigned them mechanically in that order:

| Item | Number | Status |
|---|---|---|
| GTM-1 | SR-37 | built |
| GTM-3 | SR-38 | part 2 |
| GTM-4 | SR-39 | part 2 |
| GTM-8 | SR-40 | built |
| GTM-9 | SR-41 | built |
| GTM-10 | SR-42 | part 2 |
| GTM-11 | SR-43 | Amendment #3 workstream B |
| GTM-12 | SR-44 | part 2 |
| GTM-13 | SR-45 | built |
| GTM-14 | SR-46 | pulled into T3 |
| GTM-15 | SR-47 | built |
| GTM-7 | SR-9 | amended, keeps its key |
| GTM-21 | SR-5 | amended, keeps its key |

The five built items have register entries, and the rest are reserved in one entry. The collision with the Round 4 draft's working numbers is needs-you 5.

---

## What the tables displace

**Nothing, at either cadence.** Every GTM sub-section is tables and lines. Each asks no paragraph (`paragraph_wanted: False`) and draws no chart, so `stack.section_words` counts zero words. The budgets stand: the Weekly at 3,500 words and 10 charts, the Monthly at 10,000 and 12.
- **The Weekly** gains one sub-section in Plumbing & rates: GTM-13's two tables, six and five columns.
- **The Monthly** gains:
  - three sub-sections in Plumbing (GTM-13, 15 and 21);
  - four in Slow layers (GTM-1, 7, 8 and 9);
  - three rows in "Base rates: Top & Bottom".
- **The Monthly's generic "Sourced figures" table loses five reference-table rows.** The GTM tables now print them, so each fact prints once: stock–bond correlation, ATHs, tariffs, consumer, and fixed-income returns year to date. 39 rows print there instead of 44.

The reading time rises by the tables' scan time only.

---

## Box commands, for the operator

Run these inside a window (weekdays 17:20–23:30 ET) after Thursday's merge. I ran none of them.

```bash
cd ~/chester-reports && git pull --ff-only

# 1. The five new FRED series, first pull (the live pull's 1,500 days):
.venv/bin/python -m altdata.feeds pull --only fred

# 2. Their full history from ALFRED, first publication (TDSP from 2005, customs
#    from 1992, BOPGIMP from 1992), and Michigan sentiment's (from 1952, which
#    GTM-8 needs if the store holds only the live pull's four years):
.venv/bin/python -m altdata.fred_history backfill --series customs_duties,goods_imports,dsr_household,dsr_consumer,dsr_mortgage,uoM_sent --dry-run
.venv/bin/python -m altdata.fred_history backfill --series customs_duties,goods_imports,dsr_household,dsr_consumer,dsr_mortgage,uoM_sent

# 3. The scan's figures, with the 33 GTM rows (idempotent; the Monthly's run
#    does this too):
.venv/bin/python -m altdata.scans ingest

# 4. The three new base-rate tables (the overnight pass's maybe-recompute
#    stores them anyway, since they are not yet stored):
.venv/bin/python tools/base_rates.py compute

# 5. The first read: every table as of now, text only, read-only.
.venv/bin/python -m altdata.gtm show
```

**The first render to read.** The Weekly of Sunday 26 Oct, at 05:00, gives GTM-13 in Plumbing & rates. The 1 Nov Monthly gives the rest; its dry run is yours to run, as always: `python -m monthly_macro.run --dry-run`. If ^GSPC, Shiller, `fred.yield_10y` or the bond ETFs are not stored, the tables print "not stored" in the affected cells, never a blank.

---

## Files shared with the open branches

These come from dry-run merges (`git merge-tree`) of `gtm-core-1` against session B's branches. Nothing was merged.

| Branch | Conflicts `gtm-core-1` adds | Conflicts it inherits from `el-4-6` |
|---|---|---|
| `weekly-fixes-7` (`5ed85f7`) | **none** | `CLAUDE.md`, `tools/validate_batch3_a.py` |
| `writer-fixes-1` (`4cad29b`) | **none** | the same two |
| `audit-leftovers-1` (`717a076`) | **none** | 17 files from the 6b chain's base. Step 0 added one of them, `tools/validate_secrets.py`, where both sides append a group: the stitch keeps both, I (theirs) and J (mine). |

Files both sides edit, where git merges cleanly:
- `daily_cascade/weekly_stack.py` and `monthly_macro/stack.py` (my one-line GTM hooks);
- `metrics_registry.yaml`, `altdata/config.py`, `config/catalogue_commands.yaml` and `Makefile` (one added line each);
- `docs/signal-triage-register.md` (mine adds entries before "Explicit rejections"; theirs edits elsewhere);
- the UA callers `altdata/loggers/{borrow,shielded,vxcurve}.py` and `altdata/sources/{cfets,ishares_trusts,prediction_markets,safe}.py`.

---

## What part 2 takes

- **GTM-3**, the concentration twin, through the T&B overlay intake queue, one at a time.
- **GTM-4**, the AI five-bucket decomposition and the hyperscaler cash-flow bridge, with its by-hand bucket definitions.
- **GTM-10**, the sector correlation row computed, and the rest as quarterly sourced figures.
- **GTM-12**, federal finances: what the Factor IV panel lacks, with the CBO path by hand at each update.

---

## Needs you

1. **GTM-1's historical rows are mostly empty.** The scan states 6 of 32 cells, and every other cell prints "not in the scan". Two ways to fill them:
   - amend the quarterly task's prompt so the 6 Jan read copies the inflection-points slide into its reference table;
   - give a one-time yes to transcribe slide 4 from the public PDF into a dated scan addendum. That is a by-hand figure, so rule 30 makes it yours.
2. **Forward P/E today** is "not stored": no writer has forward earnings. That stays a listed gap unless you name a public source (rule 30; ruled 16 Oct on sources).
3. **GTM-13's missing rows:**
   - AGG has no duration in `config/instrument_reference.yaml`; add one at the next Quarterly Structural refresh, as the file's rule says.
   - TIPS, munis and MBS have no proxy in the yfinance basket. Adding TIP, MUB and MBB is a writer change (no by-hand line). Say yes and it goes in part 2.
4. **GTM-15 is quarterly.** FRED has no monthly customs series. Treasury's Fiscal Data API (the Monthly Treasury Statement, keyless and public) has monthly customs receipts. Shall part 2 add it?
5. **A register-number collision.** SR-37 to SR-47 go to the GTM batch, as the agenda proposed. But the Round 4 draft's working numbers are still in code and notes (SR-43 for the OECD-yields fetcher, SR-45 constituent breadth, SR-46 the EM rules). The agenda's move of those to SR-52 … SR-64 is not written. Rule which set renumbers; until then, the reserved-numbers entry names the clash.
6. **The BLS feeds after the merge.** The new default User-Agent contains the repository URL, and BLS refused such strings on 25 Sep. Check that the first box run's news pull still reads bls.gov's feeds. If not, the fix is a host override in `user_agent.for_url`, not a person's address.
7. **Drafts for your accept-all (rule 31):**
   - SR-5's GTM-21 amendment and SR-9's GTM-7 amendment;
   - the SR-37, 40, 41, 45 and 47 entries and the reserved-numbers entry;
   - Book A rows A-6 (the regime word) and A-7 (the duration modifier) in Base Rates Appendix C;
   - the GTM-8 disagreement entry in `config/narratives.yaml`.
8. **A finding, not an ask.** Our 24-month stock–bond correlation reads **−0.29 (negative) to Jun 2026**, while the Guide's 2021–25 era is +0.33. A-6 would read "negative" today. I flag it because SR-9's rule A-1 and the Guide's framing both assume the positive regime persists.
9. **Ruling 5 and the incidents line.** I read "nothing else" literally, so the Audit #4 baseline no longer prints "INC-1 to INC-9, one open", which the agenda did record. Restore it if you meant it kept.
