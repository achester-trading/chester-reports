# a57-batch14-b1: signal triage Batch 14, Part B1, items 65 and 71 (session A, 23 Oct 2026)

**What it is.** Part B1 of the Batch 14 order (ruled 20 Oct 2026 with filing amendments F1 to F8), its build pulled forward to this weekend on 23 Oct:
- **Item 65** (written as 58): one big AI trade;
- **Item 71** (written as 64): top-of-book depth, the fragility panel.

Section 0 governs, and items are cited by their filed numbers.

**THIS BRANCH MERGES AFTER THE 1 NOV MONTHLY, whatever its CI says.**

**Base.** `a57-batch14-b1` was cut from **chain-4's tip, `4b096bb`** ("chain-4: STITCH COMPLETE 65b242c", CI green). It carries the dealer store, 6b and the scoreboard that item 71 reads; main does not yet.
- **Its own checkout:** `../chester-a57`. A peer session was on chain-4 in `../chester-reports-t3`, so the main checkout was not switched.
- **When chain-5 is on main:** main merges into this branch with a merge commit, the gates are recounted, and the branch is pushed.
- **Branch only:** pushed, not merged, not deployed, nothing run on the box, no unit enabled or started.
- **Read only:** a56-batch14-a1 and b52-batch14-a2. b55-batch14-b2 and chain-5 were not on origin when checked (23 Oct, about 19:45 ET). chester-meme was not opened.
- **The specification** is `docs/change-order-signal-triage-batch-14-2026-10-20.md`, read from `origin/a56-batch14-a1`, where session A filed it. Where it and the code differ, the code wins; every difference is listed below.

## The commits

| Commit | What |
|---|---|
| `81b717f` | Parts 1 and 2: items 65 and 71, their registration, the voices entry |
| `40d7d46` | Part 3 (a): the two pre-registrations, committed alone before any scoring code. Item 65's model labels lost their eponyms in the same commit (config only) |
| `90214a2` | Part 3 (b): the two scoring scripts and their laptop first editions; the Master Guide's Table 7a and its HTML |
| (this commit) | Part 4: the gate, CLAUDE.md, these notes |

## Part 0: the source checks (section 5 and F7, run 23 Oct 2026 from the laptop, before building)

| # | Check | Result |
|---|---|---|
| 1 | FRED's ids for BLS's PPI industry lines, and their history | **Passes.** Keyless graph CSV, all three NSA indexes, monthly to Sep 2026: <br>• `PCU334418334418`, printed circuit assembly (electronic assembly) manufacturing, Dec 2003 = 100, from 2003-12; +125.9% on the year to Sep 2026; <br>• `PCU334112334112`, computer storage device manufacturing, from 1992-12; +87.3%; <br>• `PCU334413334413`, semiconductor and related device manufacturing, from 1967-01; -2.2%. <br>The order's "+130%" and "+84%" are close to the August prints. `PCU33441333441312` (a sub-line) ends in 2015 and is not used |
| 2 | A free, keyless "Broad AI" proxy pair whose holdings are public | **Passes, as a proxy:** AIQ (an AI-and-technology ETF) against SPXT (the S&P 500 without its information-technology sector). <br>• **Prices:** Yahoo, through the basket: AIQ monthly from 2018-05, SPXT from 2015-10. <br>• **Holdings:** both issuers publish them. Global X's robots.txt disallows only `/api/`, and its full-holdings CSV for 21 Oct 2026 held no Brookfield name. ProShares' robots.txt disallows `/funds/`, so its holdings are public but not read. SPXT is an S&P 500 subset, which holds no Brookfield name. <br>• **The caveat, printed with it:** the technology sector is not the AI enablers (the communication and consumer names among them stay in SPXT), and AIQ is not the index the post cites. The cited index's name is never used |
| 8 | Whether any free source serves ES level-1 size | **Fails: not tracked.** <br>• The bars store holds OHLCV only; Yahoo serves no level-1 size history. <br>• The CME's level-1 feed through the broker is a paid market-data subscription this system does not hold: `source_registry.yaml` lists OPRA, CFE and Cboe index entitlements, no CME. <br>• So the Amihud measure stands in for depth in the flag, labelled |
| 9 | The major 2x and 3x index ETFs, where each issuer publishes daily AUM, and the existing writer's coverage | **The writer covers seven; the rest are listed gaps.** <br>• **Covered** (`altdata/sources/proshares.py`, ProShares' keyless NAV history file with AUM): TQQQ, SQQQ, QLD, UPRO, SPXU, SSO, SDS. <br>• **Not covered, Direxion:** SPXL, SPXS, TNA, TZA. No NAV or AUM history file; the holdings file carries only today's shares outstanding (the writer's check of 26 Sep 2026). <br>• **Not covered, ProShares:** QID, UDOW, SDOW, URTY, SRTY. The same keyless file serves them (HTTP 200 for QID, UDOW and URTY on 23 Oct), but the writer's `FUNDS` do not list them; extending it is the operator's call (needs-you) |
| 5 | (A56's, reused) The 5.33% to 5.08% one-day move against DGS10 | **Does not match** (`docs/briefs/a56-batch14-a1-notes.md`). No DGS10 close reached 5.33% in 2026, and no session from September fell 25 bp; the largest mid-October fall was 9 bp, 15 Oct. It may be an intraday range. The attribution is built for the speed flag as it stands, not for that day |
| F4 | Carson Group's public blog | **Passes.** <br>• **robots.txt** (www.carsongroup.com) disallows nothing for any agent and asks a 10-second crawl delay. <br>• **The feed** `/feed/` served ten dated items (newest 23 Oct 2026) without a login. <br>• **Terms of use:** personal, non-commercial use. The scan stores the URL, the dates and a one-line paraphrase, never the text. Listed for the operator's confirmation (needs-you) |

## Part 1: item 65

**The speed-flag attribution (ST-R6.65a; `altdata/speed_attribution.py`, `config/speed_attribution.yaml`).**
- **The trigger** is SR-35, the move screen's 10-year companion: the two-week or one-month change at 2 sigma on a twenty-year window. The stored screen is read; with none stored it is computed in memory, as the reports read it. The lead horizon is the larger |z|.
- **The split.** Over the lead horizon, each term-structure model's change in the 10-year term premium against the 10-year's change, in bp; the remainder is expected short rates. A model says the term premium carried the move when its premium share exceeds one half (rates_attribution's definition, not a threshold).
- **The verdict** names the leg the models read agree on, or says they disagree.
- **The models:** KW (FRED `THREEFYTP10`) and ACM (the New York Fed's `ACMTP10`). DKW splits the real yield and is not read.
- **F5.** A model is read only when its observation on the flag day is stored. With none, the attribution prints "awaiting the term-structure models' inputs for D", naming how far each is stored; with one, it prints the one and names the other as awaiting.
- **Where it prints:** the close's Mechanics, right after item 52's volatility-event block when both fire (section 3's cross-item note), with one line in Plumbing & rates (the order's placement).
- **The ledger:**
  - the close stores `rates.speed_event_ledger` on a flag day, never on a dry run;
  - `python -m altdata.speed_attribution resolve` runs in the EOD pass after item 52's resolve, warn-only;
  - it writes the attribution once the inputs land, and the 10-year's 5- and 20-session outcomes, each as a new vintage.
- **No new right:** the speed flag's rights stand.

**The AI-bottleneck PPI line (ST-R6.65b).** The three FRED ids from check 1 (`fred.ppi_pcb_assembly`, `_storage_devices`, `_semiconductors`) are pulled by the existing FRED writer.
- Each is read on the year (NSA) with dual percentiles: five years and the full history, each with its n.
- A line not stored prints "not read".
- It is a panel of item 46's inflation block, Monthly only (monthly, as ruled): `inflation_block.PANELS` `ai_ppi`.

**Broad AI against the S&P without the AI enablers (ST-R6.65c).** AIQ against SPXT, labelled "proxy" in its title and on every line (F2).
- Each leg's return since 3 Jan 2023, and the one-year relative return with dual percentiles.
- It prints in the Weekly's and the Monthly's Mechanics, right after item 31's concentration table and GTM-3's twin.
- With less than 200 sessions of either leg stored, it prints absent with its reason (the backfill).

**The AI-credit watch** (CoreWeave, Oracle, SpaceX) is a listed gap (F2): one "NOT TRACKED" line beside SR-16's neocloud line in Factor I (`absorption_block.AI_CREDIT_LINE`). There is no by-hand path.

**The voices entry (F4).** Carson Group's own blog, through its RSS feed (`config/voices_sources.yaml` `carson_group`), tier 2 in `config/source_tiers.yaml`.
- **Its kind** is `buy_side`, and the ruled tag "credible" rides in its note.
- **The firm is the default voice.** The paste's rule forbids names of people in committed files, so the person the order names is not written; the scan names the author from the post at run time.
- **The crawl delay.** The scan had one pause for every host. A source's new `pause_seconds` sets its host's longer pause (`Fetcher.host_pause`, in `altdata/sources/voices_scan.py`), so the 10-second crawl delay is obeyed.

## Part 2: item 71, the fragility panel (`altdata/fragility.py`, `config/fragility.yaml`)

| Line | How |
|---|---|
| **SPY's Amihud illiquidity** | The absolute close-to-close log return, in bp, per $1bn of dollar volume (close x shares), from the stored daily bars (`yfinance.mkt_spy`, `_volume`). A 20-session mean with dual percentiles |
| **Range per unit of volume** | (high - low) over the prior close, in bp, per $1bn; 20-session mean; dual percentiles |
| **ES top-of-book depth** | "NOT TRACKED" (check 8) |
| **FINRA margin debt** | `finra.margin_debit`, the existing writer, monthly: a level with its change on the year |
| **Its share of market capitalisation** | Margin debt over Z.1's all-sector corporate equities at market value (`fred.z1_equities_mv`, FRED `BOGZ1LM893064105Q`, MILLIONS, scaled to dollars). Between Z.1 releases the quarter is marked to SPX, labelled "marked". **Why this series:** it is the whole US equity market, financials included, as margin accounts hold it. The nonfinancial-only line (`NCBEILQ027S`) leaves the banks and insurers out |
| **The leveraged-ETF close rebalance** | AUM x L x (L - 1) x the day's return, summed over the seven covered funds. Each fund uses the prior session's AUM (`levetf.aum`) on its index proxy's close-to-close return (QQQ, SPY). L(L - 1) is positive for an inverse fund, so every fund trades with the move. Each uncovered fund is listed on the panel |
| **Dealer gamma** | 6b's stored print, never recomputed: `dealer.window_gamma` at `SPY:all`, $ per 1%, as the close wrote it, with its sign |
| **The forced-flow estimate** | The rebalance's size, plus negative dealer gamma's hedging: |gamma $ per 1%| x |the day's move, %|, only when gamma is negative and stored for the day |
| **The fragility flag** | The depth arm AND the forced-flow arm, both ranked on the five-year window. <br>• **Depth arm:** while depth is not tracked, the Amihud stand-in at or above its 90th percentile, labelled "the Amihud measure, standing in for depth". <br>• **Forced-flow arm:** above its 90th. <br>• Either arm unread prints "not read". **Flag rights only**, said on the line |
| **The "liquidity" lens** (F5) | A report-only row, "Liquidity (report only)", after item 52's ten lenses (`vol_event.with_liquidity`). The ledger's `attribution` keeps its ten; the row rides under `report_only` |
| **Item 45's levels read** | The flag's line, appended to the close's ES block ("Liquidity: The fragility flag is ...") |

**Where it prints:**
- **the close:** Mechanics, when SPY volume is stored, otherwise nothing;
- **the Weekly and the Monthly:** Mechanics, after the concentration twin.

All of it is tables and code-written lines, so it adds no prose word.

## Part 3: the two ledgers

| Ledger | Pre-registration (SHA-256 over the LF bytes) | First edition (laptop, public sources) |
|---|---|---|
| **ST-R6.65a**, the speed flag's attribution against the next 20 sessions | `docs/ledgers/speed-attribution-preregistration-2026-10.md`, `922fdd2d696f7ab5ffb5426e51fb8dc77c54cd8f2422b5ccaa4f9bced6ad3628` | **INSUFFICIENT, n 28.** The term premium carried 14 episodes and expected short rates 14; the rule needs 15 in each. <br>• 20-session continuation 0.57 against 0.36 (+0.21); halves +0.42 and +0.00. <br>• 47 episodes since 1990, 19 of them the models disagree on. <br>• Sources: FRED `DGS10`, `THREEFYTP10`; the New York Fed's ACM workbook |
| **ST-R6.71d**, the air pockets against the fragility panel | `docs/ledgers/air-pocket-preregistration-2026-10.md`, `dd999eb51a1f7165a479478de4f86ce6b8b03d01bf4f4b9c38bbd60a00772e08` | **FAIL, n 2965** (sessions 2015-01-02 to 2026-10-16). <br>• **The three pockets** (2018-02-05, 2024-08-05, 2025-04-03): the flag was off in the five sessions before each (rule: on before two). The depth arm never reached its 90th; the leveraged-ETF arm was on in one to three of the five sessions before each. <br>• **The base rate:** a 2.5% fall within five sessions after 31.1% of flag-on sessions (135) against 6.4% of flag-off; that part of the rule held. <br>• **For context:** 27.4% after the top volatility decile, so most of the lift is volatility clustering. <br>• **Sources:** Yahoo SPY bars, QQQ and ^GSPC; ProShares' NAV files; FINRA's workbook; FRED `BOGZ1LM893064105Q` |

- **Rights:** neither verdict grants anything. Item 65 adds no right (F5); item 71's flag keeps a flag's rights, and any T&B or Book C modifier is the operator's ruling.
- **The register:** each verdict reaches it only as a rule-31 draft.
- **The Master Guide's Table 7a** gains the four files, and its HTML is rebuilt with the builder. The headline counts are left to the next chain refresh (needs-you).

## Part 4: the gate

- **The gate:** `tools/validate_batch14_b1.py`, a new gate, 67 checks, groups A to H. Synthetic fixtures only: no network, no live store, no model.
  - **(A)** the attribution's trigger and silence; the split by hand for both models; agree, disagree, "awaiting" and partial; the ledger row; resolve's new vintage with the 20-session outcome by hand; the close's placement, its Plumbing line and the row it stores; the EOD resolve.
  - **(B)** the PPI line's change and dual percentiles by hand; a line not read; the Monthly-only panel; the proxy's relative return by hand; its label, and its absence on short history; the AI-credit gap line.
  - **(C)** Amihud, range, the mean's rule, margin share (millions to dollars, marked), the rebalance (an inverse fund included) and dealer hedging only when negative, each by hand; "not tracked"; every uncovered fund listed; dealer gamma as stored; silent with no volume.
  - **(D)** the flag's two arms, on, off and not read; the stand-in label; the ruled thresholds.
  - **(E)** the lens row, the ledger's ten, nothing on a quiet session, the close's hook; the levels-read line.
  - **(F)** the four FRED ids and the millions unit; AIQ and SPXT through the Security Master; every new key, the source and the commands registered; no Brookfield instrument; the voices entry and the honoured crawl delay.
  - **(G)** both pre-registrations' SHA-256; the scripts open no store; the ledger's flag reproduces `move_screen.screen_points`' z on a fixture; each rule's INSUFFICIENT, PASS and FAIL on fixtures; the percentile's window; both first editions as printed.
  - **(H)** no vendor value or by-hand key read; no write beyond the ledger rows; no composite, market-state object, register or order path; no person's name, handle or the cited index's house in the new files.
- **Changed or written, and run locally, one at a time:**
  - `validate_batch14_b1` 67/0;
  - `validate_audit_3a` 88/0 (two counts, the new block, the new members);
  - `validate_prices` 101/0;
  - `check_registry` OK;
  - `check_master_guide` 0/0;
  - `check_library` 0/0.
- **Left to CI:** every other gate, the stack renders among them (the close, the Weekly and the Monthly gained hooks), and `validate_voices`, `validate_vol_event` and `validate_security_master` against the changed files.
- **The count:** 129 code gates (126 Python, three shell), on chain-4's base. chain-5, a56 and b52 add gates, so the recount at the merge from main sets it.

## Every listed gap

1. **ES top-of-book depth** (item 71): no free level-1 source (check 8). The Amihud measure stands in, labelled.
2. **The leveraged ETFs the writer does not cover** (check 9): SPXL, SPXS, TNA and TZA (Direxion, no AUM history), and QID, UDOW, SDOW, URTY and SRTY (ProShares, served but not in `FUNDS`).
3. **The AI-credit watch** (item 65, F2): CoreWeave, Oracle and SpaceX CDS and spreads; no keyless source, no by-hand line.
4. **Dealer gamma's history before 6b's store:** the air-pocket ledger's flow arm is the leveraged-ETF estimate alone. The live flag adds dealer gamma where stored.
5. **The cited index pair itself:** a proxy stands in, labelled (F2).

## Every session-set value, with its reason

| Value | Setting | Reason |
|---|---|---|
| The speed flag's models | KW and ACM; DKW not read | the nominal 10-year's split; DKW splits the real yield |
| "Carried" | premium share above one half | rates_attribution's definition of a lean; not tuned |
| A model's start tolerance | 4 calendar days before the start session | a long weekend; a model on Treasury days |
| The ledger's outcomes | the 10-year's change over 5 and 20 sessions, bp | item 52's forward sessions; continuation is the question |
| The episode rule (ledger) | a flag day with no flag in the 21 sessions before | one episode per run; the longer horizon |
| The ledger's groups | at least 15 each, shares 0.15 apart, the same sign by half | a modest, stable difference, not a fit to one era |
| The PPI line's form | on the year, dual percentiles | the indexes are NSA |
| The proxy pair | AIQ against SPXT | check 2: public holdings, keyless prices, no Brookfield name |
| The proxy's base and window | 3 Jan 2023; one year of sessions, at least 200 | the order's "since 2023"; a year's relative return |
| The depth measures | 20-session means, at least 15 present, bp per $1bn | Amihud's measure is a window mean; one session is noise |
| The margin capitalisation | Z.1 all sectors at market value, marked to SPX | the whole market as margin accounts hold it; b52's marking rule |
| The prior AUM's age | at most 5 calendar days | a long weekend and a holiday |
| Dealer gamma | `SPY:all`, as stored; hedging only when negative | 6b's all-expiry print; only short gamma is forced flow |
| The flag's window | five years, of the dual percentiles | the shorter window; the full history prints beside it |
| The air-pocket rule | the first session of the month with a fall of 2.5% or more; the five before; a fall within five sessions after | August 2024's SPY fall was 2.91%, so 3% would miss it |
| The air-pocket sample | from 2 Jan 2015; at least 20 flag-on sessions | five years of the leveraged funds' history |
| The air-pocket margin month | the latest month ending 25 or more days before | FINRA publishes about three weeks after the month |
| The voices crawl delay | `pause_seconds: 10` for Carson Group | its robots.txt asks it |

## Each new key, its source and its real publication lag (for b51's `config/publication_lags.yaml`)

| Key | Source | Cadence | Publication | Lag to add |
|---|---|---|---|---|
| `fred.ppi_pcb_assembly`, `fred.ppi_storage_devices`, `fred.ppi_semiconductors` | BLS PPI by industry, through FRED | monthly, dated the 1st | BLS releases PPI about two weeks after the month (FRED the same day), so the newest observation is about six weeks old at release | **none new**: b51's `fred_monthly_release` family (`fred_ids: ["*"]`, 22 sessions) covers it |
| `fred.z1_equities_mv` | Z.1, through FRED | quarterly, dated the quarter's first day | about ten weeks after the quarter | **none new**: b51's `z1_quarterly` (`BOGZ1*`, 85 sessions) covers it |
| `yfinance.mkt_aiq`, `yfinance.mkt_spxt` (and their `_volume`, `_dividend`, `_split`) | Yahoo, through the basket | daily | the close | none |
| `rates.speed_event_ledger` | this system, the close and the EOD resolve | event | written the flag day; later vintages as the inputs land | none (an event ledger, no staleness) |

## The box commands (the operator's; inside the windows; dry runs first; after the merge, which is after the 1 Nov Monthly)

```
cd ~/chester-reports
# AIQ and SPXT's history (the proxy reads nothing until it lands):
.venv/bin/python tools/backfill_prices.py --symbols AIQ,SPXT --years 8 --dry-run
.venv/bin/python tools/backfill_prices.py --symbols AIQ,SPXT --years 8
# The four FRED series: nothing to run. The 16:10 pull takes each new series'
# full history at its next run (altdata/sources/fred.py).
# The reads, once they are in (read-only):
.venv/bin/python -m altdata.ai_trade show
.venv/bin/python -m altdata.fragility show
.venv/bin/python -m altdata.speed_attribution show
.venv/bin/python -m altdata.speed_attribution resolve --dry-run
# The ledgers' box editions, written OUTSIDE the checkout (public sources, the
# registered rules; the ACM workbook needs xlrd, which the ACM writer already needs):
mkdir -p ~/chester-data/ledgers
.venv/bin/python tools/calibration/st_r6_65a_speed_attribution.py --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/st_r6_71d_air_pockets.py --box --out ~/chester-data/ledgers
```

- **Expect:**
  - the backfill's dry run prints the rows it would write;
  - `ai_trade show` prints the PPI line, the proxy line (or its reason) and the AI-credit gap;
  - `fragility show` prints the panel's rows and the flag's line;
  - `speed_attribution show` prints "the speed flag did not fire" on a quiet day;
  - the box editions print INSUFFICIENT n 28 and FAIL n 2965, the same public sources moved on by the days since.
- **Bring the box editions back** with `scp 'vps:~/chester-data/ledgers/st-r6.6*' 'vps:~/chester-data/ledgers/st-r6.7*' docs/ledgers/`, and ask a session to commit them.
- **The voices scan** reads Carson Group's feed at its next 06:15 run; nothing to run by hand.
- **The EOD pass** runs `speed_attribution resolve` from the next pull of main after the merge; no unit changes.
- **The Monthly's dry run** stays Ari's, as always.

## Files shared with other branches

| Branch | Files |
|---|---|
| a56-batch14-a1 | `CLAUDE.md`, `Makefile`, `metrics_registry.yaml`, `monthly_macro/stack.py` (a56 adds a slow-layer sub-section; this branch adds two lines in Mechanics), `source_registry.yaml` |
| b52-batch14-a2 | `CLAUDE.md`, `Makefile`, `altdata/sources/yfinance_source.py` (both add symbols: the basket is 116 + 8 + 2 = **126** at the union, volume units 106, the shares block 96), `config/catalogue_commands.yaml`, `config/security_master.yaml` (b52 takes SM00205 to SM00212, this branch SM00213 and SM00214; `next_id` **215**), `config/source_tiers.yaml` and `config/voices_sources.yaml` (both add a desk), `docs/chester-reports-architecture-v3.md` (126 symbols), `docs/master-guide.md` and its HTML (Table 7a rows from both; rebuild the HTML with the builder, never hunk-resolve), `metrics_registry.yaml` (the basket blocks' counts, 126 and 96), `monthly_macro/stack.py`, `tools/validate_audit_3a.py` (both members' lines), `tools/validate_prices.py` (126 and 106) |
| b55-batch14-b2 | not on origin when checked: expect `CLAUDE.md`, `Makefile`, `metrics_registry.yaml` and the Master Guide's Table 7a at least |
| chain-5 | not on origin when checked: it will carry a56 and b52 (the rows above), so the merge from main resolves them once |

`daily_cascade/stack.py`, `stack_close.py`, `weekly_stack.py`, `altdata/vol_event.py`, `altdata/sources/voices_scan.py`, `inflation_block.py`, `absorption_block.py` and `scripts/run_eod_cron.sh` are changed here and by neither a56 nor b52.

## Where the order and the code differ

1. **F5, "a report-only column in item 52's attribution table".** The table's lenses are rows, so "liquidity" is a report-only row after the ten; in the ledger it rides under `report_only`, so the ten graded lenses are unchanged.
2. **Item 65's placement, "Plumbing & rates (attribution event)", and section 3, "print adjacent in mechanics".** The sub-section prints in Mechanics after item 52's block, with one line in Plumbing & rates.
3. **"The speed flag catches it"** (a 25 bp one-day fall). SR-35 is a two-week and one-month speed flag; a one-day move is the move screen's 1-day row on the 10-year. As ruled, the attribution runs on SR-35's days only. A56's check 5 found no such day on DGS10 in any case.
4. **"The output names whether expected short rates or the term premium carried the move."** It does, by the models present on the day. DKW (the real split) is not read, and with no model stored it prints "awaiting" (F5).
5. **The 07:00 anchor** prints item 52's block; the speed attribution is the close's only, and its ledger is the record.
6. **"The concentration cluster (items 30, 31, 44)".** The proxy prints after item 31's table and GTM-3's twin in Mechanics; item 30's allocation block is in Positioning & flows and is left alone.
7. **"[The strategist] (Carson Group) goes into the voices register."** The firm's public blog is entered (F4); the person is not named (this paste's rule). The ruled tag "credible" is in the note; the kind is `buy_side`.
8. **The voices scan's pause** was one setting for every host. Obeying the crawl delay needed a per-source `pause_seconds` (a small change to `voices_scan.py`).
9. **"ES top-of-book depth from item 45's store"**: not tracked (check 8); the Amihud measure stands in.
10. **The forced-flow estimate** is the ruled formula on the day's return, so it is largest on large-move days, and the flag reads a fragile book on the day of the move rather than before it. The air-pocket ledger records what that means: off before all three pockets.
11. **"Dealer gamma from 6b"** is the close's stored all-expiry $ per 1% for SPY. Its history is short, so the ledger's flow arm leaves it out, labelled.
12. **The PPI line "in item 46's pipeline", monthly**: the inflation block's panel at the Monthly only. The Weekly does not print it.
13. **The speed-flag ledger's rule and the air-pocket rule** are not stated in the order. Each was written in its pre-registration before any scoring code (the 17 Oct ruling's form).

## The CI rounds

| Round | Run | On | Result |
|---|---|---|---|
| 1 | 40041135514 | `6bdc628` | **134 of 138 gates green; 4 failed, each this branch's**: <br>• `validate_numeral_audit`: two ordinal suffixes written by hand in `fragility.py`'s flag line, now `ordinal()`. <br>• `validate_weekly_edits`: the proxy's absent reason printed its store keys in the Weekly, now the symbols only. <br>• `validate_st_r5_t1_rest`: pinned FRED_PULL_SERIES at 277, now 281. <br>• `validate_6e_rest`: pinned five inflation panels, now six. <br>Locally after the fix: 172/0, 34/0, 103/0, and `validate_batch14_b1` 67/0 |
| 2 | (in the closing message) | | |

## Needs you

1. **The merge: after the 1 Nov Monthly, whatever CI says.** First chain-5 onto main, then main into this branch with a merge commit and a recount: the basket to 126, `next_id` 215, Table 7a, the gate count.
2. **The box commands** above, after the merge: the backfill (dry run first), the reads, the two box editions outside the checkout.
3. **Two verdicts** for your accept-all, as rule-31 drafts: ST-R6.65a INSUFFICIENT (n 28) and ST-R6.71d FAIL (n 2965). Nothing prints differently or gains a right from either.
4. **The voices entry (F4):** Carson Group's blog. Its terms allow personal, non-commercial use; confirm the scan's use (URL, dates, a one-line paraphrase), or set it `enabled: false`. The person the order names is not written in any file; rule whether that stands.
5. **The leveraged-ETF writer:** add QID, UDOW, SDOW, URTY and SRTY to `proshares.FUNDS` (the same keyless file), or leave them listed gaps.
6. **The session-set values** above: confirm or replace. Above all, the proxy pair, the flag's five-year window and the ledgers' rules.
7. **The Master Guide's Part 5 counts:** this branch adds one INSUFFICIENT and one FAIL to the gated signals. That is the next chain refresh's; this branch adds the Table 7a rows only.
8. **The 1-day 10-year move:** whether a one-day screen flag on the 10-year should also trigger the attribution (a new ruling; not built).
