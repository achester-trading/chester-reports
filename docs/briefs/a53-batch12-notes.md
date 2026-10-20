# a53-batch12: signal triage Batch 12, items 59 and 60 (session A, 20 Oct 2026)

**Base and boundaries.** Built on `a52-doctrine-2-pack` after A52's closing message (A52's tip `c6320fc`), so one pull request carries both.
- **The specification** is `docs/change-order-signal-triage-batch-12-2026-10-20.md`. It is filed verbatim (`f66786b`, before any code) and indexed in `docs/change-orders.md` and the signal-triage register's header, beside Batch 11.
- **Precedence:** its section 0 (F1–F6) governs. Where the order and the code differ, the code wins (section 6 below).
- **Branch only.** Pushed, nothing merged, nothing deployed, nothing run on the box, no unit enabled or started.
- **Read only:** b48-scoreboard. chester-meme was not opened.
- **Timing:** item 59's classifier and item 60's implied-growth print are 1 Nov Monthly candidates, so this branch must merge before the Monthly's last dry run on 28 Oct. Item 60's print is a listed gap (F3), so only the classifier and the panel can land.

## 1. The order's section 5 checks (F6), run before building on 20 Oct 2026

| # | Check | Result |
|---|---|---|
| 1 | Free history depth: the SOFR percentiles, financial CP, H.8 small-bank deposits | **Passes.**<br>• SOFR and its 99th percentile on FRED (`SOFR`, `SOFR99`) from 2018-04-03, also on the NY Fed's keyless API with every percentile (robots.txt answers nothing to block);<br>• financial CP (`DCPF3M`) from 1997-01-02;<br>• H.8 small-bank deposits (`DPSSCBW027SBOG`) from 1973-01-03 and large-bank (`DPSLCBW027SBOG`) from 1985-04-03;<br>• IORB from 2021-07-29, with IOER from 2008-10-09 to 2021-07-28 for the spread's history. |
| 2 | Z.1's FHLB advances on FRED, and its lag | **Passes.** `BOGZ1FL403069330Q` ("FHLB Advances; Asset, Level"), millions, quarterly from 1945, dated the quarter's first day. The newest print on 20 Oct is Q2 2026 (2026-04-01), so the lag is one quarter: Z.1 is published about ten weeks after the quarter-end. The ledger counts it from 75 days after the quarter-end. |
| 3 | A keyless forward-EPS series with vintages (Yardeni), its terms and robots.txt | **Fails the standing rule.**<br>• robots.txt allows `/` but disallows `/api`, and the chart pages read their data from it;<br>• the copyright clause (`/copyright`) says no material "may be downloaded, transmitted … reproduced or in any other way used … without the explicit written consent".<br>So F3's gap branch applies: implied forward growth and the realised forecast error are listed gaps, the flag does not print, and the ledger waits for a source. |
| 4 | The FDIC Quarterly Banking Profile's unrealised losses, keyless | **Passes.** `api.fdic.gov/banks/financials`, keyless (its robots.txt answers 404, no rules). One call a quarter aggregated by `REPDTE` sums AFS and HTM securities at fair value and amortised cost over every insured institution. A new writer, `altdata/sources/fdic_qbp.py`. |
| 5 | KRE's implied vol from a free chain | **Served, not built.** Yahoo serves KRE's chain free (20 expiries, an implied-vol column), but KRE is not in the capture universe (13 Yahoo names; Batch 13 counts 17 with the Massive chains). Adding a name is the universe's ruling, so it is listed for you. |

**Two more sources were checked for the panel:**
- **The OFR FSI: passes.** `www.financialresearch.gov/financial-stress-index/data/fsi.csv`, keyless, daily from 2000. robots.txt disallows four unrelated paths. A new writer, `altdata/sources/ofr_fsi.py`.
- **ICI's weekly money-market fund assets: fails.** `www.ici.org/mm_summary_data_<year>.xls` answers HTTP 403 to every client that names itself, robots.txt included: the repo's generic and browser-like agents both. A writer never passes for a browser (the AAII rule), so ICI is a listed gap.
  - Its parser, `altdata/sources/ici_mmf.py`, is kept unscheduled on no roster, as LBMA's is. Its key is registered as "NOT AVAILABLE".
  - **In its place:** FRED's weekly retail money funds (`WRMFNS`, from 1980) through the existing writer, labelled "retail" wherever it prints.

## 2. Item 59: the bank-stress panel, the flags and the classifier

### The panel (ST-R6.59a)

| Series | Store key | Source |
|---|---|---|
| SOFR less IORB (IOER before 29 Jul 2021) | from `fred.sofr`, `fred.iorb`, `fred.ioer` | FRED |
| SOFR's 99th percentile less IORB | `fred.sofr_p99` | FRED (the NY Fed's distribution) |
| 90-day AA financial CP less the 3-month bill | `fred.fin_cp_3m` less `fred.tbill_3m` | FRED |
| Discount window: primary credit | `fred.dw_primary_credit` | FRED (H.4.1, `WLCFLPCL`) |
| Other credit extensions (any emergency facility) | `fred.fed_other_credit` | FRED (H.4.1, `WLCFOCEL`) |
| FHLB advances | `fred.fhlb_advances` | FRED (Z.1; F2) |
| H.8 deposits, small and large domestic banks | `fred.h8_dep_small`, `fred.h8_dep_large` | FRED (H.8) |
| Retail money-fund assets (ICI's place) | `fred.mmf_retail` | FRED (`WRMFNS`) |
| KRE against XLF, 20 sessions | `yfinance.mkt_kre` (new) over `yfinance.mkt_xlf` | yfinance |
| SLOOS, C&I tightening (large; small) | `fred.sloos_ci_large`, `fred.sloos_ci_small` (already held) | FRED |
| Unrealised securities gains (losses), AFS and HTM | `fdic.unrealised_total` (and `_afs`, `_htm`) | FDIC BankFind |
| STLFSI | `fred.stlfsi` | FRED (`STLFSI4`) |
| OFR FSI (and its funding and credit categories) | `ofr.fsi`, `ofr.fsi_funding`, `ofr.fsi_credit` | OFR |

**Dual percentiles.** Each series prints the five-year window and its family's long window, each with its n (`st_r5_rates.lens`). The long windows are stated per family in `config/bank_stress.yaml`, and each is the whole stored history:
- funding rates: SOFR from 2018, financial CP from 1997;
- facilities from 2002;
- FHLB from 1945;
- deposits from 1973 and 1985;
- money funds from 1980;
- bank equity (KRE) from 2006;
- SLOOS from 1990;
- the FDIC's aggregate from the quarters stored;
- composites: STLFSI from 1993, the OFR FSI from 2000.

The quantities' registry entries carry `long_window: full`, since the family default gives a quantity none.

### Registration

| What | Details |
|---|---|
| FRED legs | `FRED_BANK_STRESS_SERIES` (10) in `altdata/config.py`, block `fred_bank_stress` in `metrics_registry.yaml`, in `NEW_KEY_BLOCKS` |
| `FRED_PULL_SERIES` | 266 → 276 (CLAUDE.md, the architecture document's store box, `validate_st_r5_t1_rest`) |
| KRE | in `yfinance_source.SYMBOLS` (115 → 116; CLAUDE.md, the architecture document, `validate_prices`, the `market_closes` and `market_actions` blocks); volume (95 → 96 units; the volume-shares block 85 → 86); `NEW_BLOCK_MEMBERS`; Security Master `SM00204` (`next_id` 205; name, currency, exchange and multiplier null and listed as unverified until a listings file confirms them) |
| New writers | `ofr_fsi` and `fdic_qbp` on `OFFICIAL_WRITERS` (31 → 33; CLAUDE.md and the architecture document), each with its source in `source_registry.yaml`, its keys in the metrics registry and its line in `config/catalogue_commands.yaml`; `ici_mmf` parked (status retired) |

### The flags and the classifier (ST-R6.59b), exactly as item 59 rules

- **Funding stress:** any two of SOFR less IORB, the financial CP spread, primary credit and FHLB advances above their 95th percentile.
  - It reads the five-year window's figure (session-set, below).
  - It needs two members read, else "not read".
  - The percentile is the stack's rule (ties count "at or below"), so a member flat for five years would read 100. None of the four is flat in its history; this is recorded, not changed.
- **Deposit flight:** small-bank H.8 deposits down while money funds are up, both over 4 weeks.
- **The classifier:** it prints only when KRE is down more than 10% over 20 sessions (exactly −10.0% stays dormant).
  - The states: correction (neither flag on), funding watch (one), banking stress (both).
  - Its third arm, "either flag plus a CDS/AT1 move", prints "not tracked" (F2).
  - KRE is the equity leg: BKX is not in the basket.

### Placement

- **The close:**
  - Plumbing & rates: one item beside item 34's cluster (`plumb:bank_stress`), priority 1 when a flag is on.
  - The read: the classifier's line, only when it prints.
- **The Weekly:** a "Bank stress" sub-section in Plumbing & rates, one line.
- **The Monthly:** Plumbing & rates, after the rates-transmission cluster. It carries the full panel table, both flags, the classifier, the unrealised losses beside the 10-year (cross-item note 1), the long windows and the listed gaps.
- **The Monthly's own gates** (`validate_monthly_stack` and the rest) are left to CI.

### The 12:30 gate (F5)

- **Registration:** `midday_gate._bank_stress`, placed before `_crypto_leverage`. `validate_dealer_block`'s pinned list is updated.
- **When it opens:** only on the session a flag turns on, meaning on at 12:30 and off as of the prior session's 17:00 ET. It closes on a session the flag stays on.
- **The line:** one code-written line.
- **One message a session:** the slot's once-a-session mail marker holds the cap.
- **No store:** the gate stays closed and never creates one.

### The ledger (ST-R6.59c)

1. **The pre-registration,** `docs/ledgers/bank-stress-preregistration-2026-10.md`, was committed alone first (`893b6e5`, SHA-256 `011f7d25…9192`, LF bytes, held by the gate) and is never edited.
2. **The scoring script,** `tools/calibration/st_r6_59c_bank_stress.py`, uses public sources only and opens no store.
3. **The laptop first edition,** `docs/ledgers/st-r6.59c-ledger-2026-10-20.md`, with its episodes CSV:

**FAIL, n 18.**
- **Crises:** caught 2 of 2 (2007-08-03 and 2023-03-08, both banking stress).
- **Corrections:** 6 of 16 stayed correction, where the rule needs two-thirds. Ten corrections reached funding watch, among them 2015-08, 2016-01, 2016-06, 2018-10, 2020-02, 2024-12 and 2025-10.
- **Median forward S&P 500 at +252 sessions:** correction −5.4% (n 6), funding watch +19.4% (n 10), banking stress +7.8% (n 2).
- **High yield:** the leg is "not served" before FRED's recent window.
- **Read:** the funding flag over-fires on stress that stayed a correction. Nothing is granted, and the T&B intake waits regardless.

### The T&B intake queue (ST-R6.59d)

Listed, not added: it waits for a passing ledger and "T&B full".

## 3. Item 60: the earnings-estimate overshoot

- **Implied forward growth, the realised forecast error, the flag and the ledger: listed gaps (F3).**
  - `altdata/eps_overshoot.py` holds both of F3's branches. `config/eps_overshoot.yaml` names no source today, so item 29's r−g print carries the gap line and the flag does not print.
  - The built branch is held on a fixture by the gate: naming a keyless source with vintages and its two keys switches it on.
  - The 2000/2007/2019 ledger waits for that source.
- **The P/E dispersion line (F4):** `altdata/pe_dispersion.py`, printed in the Monthly's "What's carrying the index" sub-section, the one M11 sits in. It lists each hyperscaler (GOOG folded into GOOGL):
  - forward P/E against its peak since logging began, with that date;
  - trailing P/E (stored close over the last four reported quarters' EPS from the earnings events) against its 2025 peak, labelled "trailing";
  - each leg with its reason where it cannot be computed.
- **SR-16:** the neocloud / AI-infrastructure credit line prints "NOT TRACKED (item 60, F2 …)" beside the hyperscaler anchors (`daily_cascade/absorption_block.py`).
- **The narrative pair,** `ai_excess_orderly_flush` and `estimates_overshoot_reckoning`, is seeded through `config/narratives.yaml`'s `proposals:`, the register's existing proposal path. Each enters as PROPOSED at the next seed, with QQQ as its evidence rule. Confirming or rejecting them is yours.

## 4. Every listed gap

- Bank CDS and AT1 spreads (F2): the classifier's third arm prints "not tracked".
- CMBS office delinquency (F2).
- FHLB advances between quarters from press reports (F2): Z.1 quarterly instead.
- The neocloud credit line (F2, SR-16).
- Implied forward growth, the realised forecast error, the overshoot flag and its ledger (F3: Yardeni fails the source rule; S&P DJI withdrawn).
- ICI's weekly money-fund assets: the client is refused; FRED's retail series stands in.
- KRE's implied vol: served, but KRE is not in the capture universe.
- The high-yield leg of the ledger before FRED's recent window: "not served".
- BKX: not in the basket; KRE is the equity leg.

## 5. Every session-set value, with its reason

| Value | Setting | Reason |
|---|---|---|
| The funding flag's percentile window | the five-year figure | the level is judged against the regime the store spans now, not against 1997 or 1945; where the store holds less than five years, the window it covers |
| The 12:30 gate's prior cutoff | the prior session's 17:00 ET | after every daily writer's close pass, so "turned on today" means since the last full read |
| The ledger's cluster gap | 60 sessions | one episode per stress, not one per session; pre-registered |
| The ledger's lags | the next session for a daily series; the first Friday after the reference date for a weekly one; 75 days after the quarter-end for Z.1 | the publication lags, pre-registered; H.8's real lag is longer, so its leg is read a little early (stated in the ledger) |
| The FDIC writer's default reach | the last 8 quarters a run | revisions; `--since` reaches the history |

## 6. Where the order and the code differ

1. **ICI:** FRED's retail series in ICI's place (section 1).
2. **"KRE or BKX":** KRE only.
3. **"The classifier line in the read":** printed in the close's read. The Monthly's read section takes no store, so in the Monthly the classifier prints inside the full panel.
4. **"The dispersion line on item 40's Monthly chart":** printed as lines in M11's sub-section, not drawn on the chart image.
5. **The NY Fed's SOFR distribution:** read through FRED's `SOFR99`, the existing writer, not a new NY Fed writer.
6. **H.4.1's discount window and emergency facilities:** through FRED (`WLCFLPCL`, `WLCFOCEL`), not by extending the H.4.1 writer, which reads FIMA repo only.
7. **The 12:30 gate:** reads the store at 12:30. Its inputs are daily and weekly series, so a flag turns on at the first read after a new print.

## 7. The box commands, dry runs first (the operator's)

```
cd ~/chester-reports
# the new FRED legs arrive with the next 16:10 pull; their first-print history (ALFRED):
.venv/bin/python -m altdata.fred_history backfill --series fin_cp_3m,sofr_p99,ioer,dw_primary_credit,fed_other_credit,fhlb_advances,h8_dep_small,h8_dep_large,mmf_retail,stlfsi --dry-run
#   then the same without --dry-run
# KRE's history:
.venv/bin/python tools/backfill_prices.py --symbols KRE --period max --dry-run
#   then the same without --dry-run
# the two new writers (each writes its whole history on the first pull):
.venv/bin/python -m altdata.sources.ofr_fsi
.venv/bin/python -m altdata.sources.fdic_qbp --since 2007-03-31
# the read, once they are in:
.venv/bin/python -m altdata.bank_stress show
```

The two writers have no dry-run flag, so they are listed after the dry runs. Each is append-only, and a re-run writes nothing new. The narrative pair enters at the register's next seed.

The flags are read from each module's argument parser (`--series` takes registered keys, comma-separated). None of these commands was run here.

## 8. The gate and the checks

- **The gate:** `tools/validate_batch12.py`, a new gate, 57 checks, groups A–J, synthetic fixtures only.
- **Changed and run locally:**
  - `validate_batch12` 57/0;
  - `validate_dealer_block` 134/0 (the GATES list);
  - `validate_st_r5_t1_rest` 103/0 (276);
  - `validate_prices` 101/0 (116 symbols, 96 volume units);
  - `validate_audit_3a` 88/0;
  - `validate_security_master` 102/0;
  - `check_registry` OK;
  - `check_master_guide` 0/0 (Table 7a gains the pre-registration and the ledger);
  - `check_library` 0/0.
- **The count:** 126 code gates (123 Python, three shell); CLAUDE.md updated.
- **The Master Guide's Part 5 counts** ("twenty-one gated signals … twelve failed") are not updated here. They are the chain refresh's, and ST-R6.59c's FAIL makes them 22 and 13.

## 9. Files shared with chain-3 and b48-scoreboard

- **chain-3:** this branch is cut from chain-3's tip, so every file shares its base. Session B's chain-4 takes this branch at A53's final tip.
- **b48-scoreboard:** both branches change these files:
  - `CLAUDE.md`;
  - `Makefile`;
  - `daily_cascade/weekly_stack.py` (here, one sub-section in Plumbing & rates);
  - `monthly_macro/stack.py` (here, one sub-section in Plumbing & rates);
  - `docs/master-guide.md` and `docs/html/master-guide.html` (here, Table 7a's two rows);
  - `docs/signal-triage-register.md` (here, the header's Batch 12 link).

## 10. The CI rounds

| Round | Run | Result |
|---|---|---|
| A53 | 39495721438 | failed 3 of 135:<br>• `validate_numeral_audit`: an ordinal suffix written by hand, `bank_stress.py:223`; now `numeral_audit.ordinal`;<br>• `validate_narratives`: the proposals pinned at three, now five with the pair;<br>• `validate_stack_cadence`: the Weekly's one-line status also printed at the Monthly's cadence, carrying "4 weeks"; now added at "weekly" only, since the Monthly prints the full panel |
| A53 round 1 | (below) | the three fixed; run locally: numeral audit 172/0, narratives 103/0, stack cadence 99/0, Batch 12 57/0 |

## 11. Needs you

1. **KRE's implied vol:** add KRE to the capture universe (a universe ruling), or keep it a gap.
2. **ICI:** keep the retail series in its place, or name another keyless total.
3. **The session-set values** in section 5: confirm or replace.
4. **The ledger's FAIL** (n 18): no right was asked; it reaches the register only as a rule-31 draft (for the operator's accept-all).
5. **The narrative pair:** confirm or reject after the next seed (`python -m altdata.narratives confirm <id>` is yours).
6. **The box commands** in section 7, dry runs first, inside the windows.
7. **The merge:** before the Monthly's last dry run on 28 Oct, with this branch at chain-4.
