# The box sheet for the second chain (for Ari)

**What this is.** Every box step the second chain's notes ask for, de-duplicated and ordered, for the evening the second chain merges to main (planned: Tuesday 20 Oct, after Monday's six). It is compiled from the box-command sections of the 47 notes files the chain carries that main does not. It leaves out what Monday's sheet already covers:
- the store registry check's first run, the quality check, `feeds pull --only official`;
- the FRED compaction, the Security Master listings and export;
- the Alpha Lab's directories, timers and roster registration;
- the volume profile, the IB Gateway restart;
- the FRED history backfill's first run, and `backfill_prices --years 5` for the whole basket.

**Read this first.**
- **Times are Eastern.** Every step runs inside a window: weekdays 09:05–15:40 or 17:20–23:30, never 16:00–17:20; weekends are open, clear of Sunday 05:00. The merge evening's window is 17:20–23:30.
- **Every step is typed at the box prompt in the checkout** (`cd ~/chester-reports`) unless it says "from the laptop". Units are user units (`systemctl --user`). Logs are `~/logs/<name>-YYYY-MM.log`.
- **A dry run first** wherever one exists. It fetches and parses and writes nothing.
- **"Paste back"** means: send the output to a session if it differs from what is expected here.
- **⚑ marks a step that needs a decision from you.**
- Nothing here was run by a session, and no unit was enabled or started by one.

## Timers: what the self-deploy enables, and what is yours

The self-deploy (every 30 minutes inside the windows) copies the unit files and enables the timers in its declared list.

**It enables one new timer:** `chester-prices-saturday.timer`, Monday's, already on that sheet.

**You enable these six.** They are not in the declared list on purpose, because each starts a new daily data line:

| Timer | When it runs | Step |
|---|---|---|
| `chester-vendor-chains.timer` | Mon–Fri 16:31 | A2 |
| `chester-dealer-0945.timer` | 09:45 | A3 |
| `chester-dealer-1230.timer` | 12:30 | A3 |
| `chester-flashalpha.timer` | 16:25 | A4 |
| `chester-restore-test.timer` | weekly | C5 |
| `chester-meme-ingest.timer` | daily | B12 |

`chester-quarterly.timer` ships disabled and stays disabled. `ibgateway.service` and its restart timer stay held behind the witnessed clean start.

---

## A. The same evening as the merge: anything whose absence loses data

A chain capture not taken at its minute cannot be taken later, so these come first.

**A1. Confirm the merge has reached the box.**
```
git pull --ff-only && git log -1 --oneline
systemctl --user list-unit-files 'chester-vendor-chains*' 'chester-dealer-*' 'chester-flashalpha*' 'chester-restore-test*' 'chester-meme-ingest*'
```
- **Expect** the merge commit's line, then the unit files listed (they arrive with the self-deploy within 30 minutes of the merge).
- **If a file is missing**, wait one self-deploy tick, or run `bash scripts/deploy.sh` from the laptop.
- Cannot wait: A2 to A4 need the files.

**A2. The 16:31 vendor chains: SPX and SPCX, captured after their 15-minute delay.** First.
```
systemctl --user daemon-reload
systemctl --user enable --now chester-vendor-chains.timer
systemctl --user list-timers 'chester-vendor-chains*' 'chester-eod*'
```
- **Expect** the vendor-chains timer's next run at 16:31 on the next weekday, beside the EOD timer.
- **After its first run** (the next weekday, after 16:31):
  ```
  tail -n 30 ~/logs/dealer_capture-$(date +%Y-%m).log
  ls data/chains/$(date +%F)/ | grep -E "SPX|SPCX|_vendor_completeness"
  ```
  Expect SPX and SPCX chain files and `_vendor_completeness.json`. The EOD pass's own log now says it skips the vendor universe.
- **Cannot wait:** each day without it is a day of SPX chains lost.
- **Paste back** the log tail if no SPX file appears.

**A3. The 09:45 and 12:30 dealer captures.**
```
systemctl --user enable --now chester-dealer-0945.timer chester-dealer-1230.timer
systemctl --user list-timers 'chester-dealer-*'
```
- **Expect** both timers with their next runs.
- **After the next session's runs:**
  ```
  tail -n 40 ~/logs/dealer_capture-$(date +%Y-%m).log
  .venv/bin/python -m daily_cascade.dealer_block show --date $(date +%F)
  ls ~/chester-data/outbox/midday/
  ```
  Expect 09:45 and 12:30 capture lines and the day's block. The midday outbox is empty unless a 12:30 gate opened.
- **Optional, before enabling:** one capture by hand, which writes a real capture: `.venv/bin/python -m altdata.dealer_capture run --slot 0945 --symbols SPY`.
- Cannot wait (intraday captures are a market at an instant).

**A4. The 16:25 vendor writer.**
```
.venv/bin/python -m altdata.secrets FLASHALPHA_API_KEY FLASHALPHA_BASE_URL SMTP_USER SMTP_PASSWORD
systemctl --user enable --now chester-flashalpha.timer
systemctl --user list-timers 'chester-flashalpha*'
```
- **Expect** "set" beside each name (the command prints set or missing, never a value), then the timer's next run at 16:25.
- **After its first run:**
  ```
  journalctl --user -u chester-flashalpha.service -n 60 --no-pager
  cat ~/.chester/flashalpha_calls.json
  .venv/bin/python tools/validate_vendor_divergence.py
  ```
  Expect a summary of stored and absent fields, a day's count of at most 60, and the divergence data gate's verdict. "expected move: not served" is the expected answer if the path returns 403 or 404.
- Cannot wait.
- **Paste back** the journal if the count passes 60 or a name reads "missing".

**C1 to C4 below should also be done this evening, before 02:30.** Until they are, the nightly backup exits `no_crypt` and the heartbeat reads `backup=failed:no_crypt`. One night without the encrypted backup is accepted, no more.

---

## B. First pulls and backfills, each dry run first

These fill history. None loses data by waiting a day: the scheduled pulls bring each series' current rows on their own. They can run the same evening after A, or the next evening. Run them one at a time.

**B1. The two new VIX tenors, and the 16 Oct volatility event's seed.**
```
.venv/bin/python tools/backfill_prices.py --period max --symbols ^VIX9D,^VIX6M --dry-run
.venv/bin/python tools/backfill_prices.py --period max --symbols ^VIX9D,^VIX6M
.venv/bin/python -m altdata.vol_event show --date 2026-10-16
.venv/bin/python -m altdata.vol_event seed --date 2026-10-16
```
- **Expect** row counts per symbol in the dry run, then the same written.
- `show` prints 16 Oct's read, including the three daily lens lines' inputs. `seed` writes the ledger's first row; it is a one-off, not a recurring line.
- **Paste back** `show` if it says a lens is "awaiting" for VIX9D or VIX6M after the backfill.

**B2. The other new basket symbols** (five years; COR1M and COR3M return one row each because Yahoo serves no history).
```
.venv/bin/python tools/backfill_prices.py --years 5 --symbols TIP,MUB,MBB,^DSPX,^COR1M,^COR3M,ZN=F,TLT --dry-run
.venv/bin/python tools/backfill_prices.py --years 5 --symbols TIP,MUB,MBB,^DSPX,^COR1M,^COR3M,ZN=F,TLT
.venv/bin/python -m altdata.sources.cboe_indices
```
- **Read the dry run's TLT lines before writing:** TLT's closes are stored already, and only its open, high and low should be added.
- `cboe_indices` writes COR1M and COR3M from 2006 and DSPX from 2014.
- **Paste back** the TLT lines if they show closes being written.

**B3. The FRED series at their first publication (ALFRED).** Three groups. Each runs as a dry run, then without `--dry-run`. A series already stored is skipped, so the overlaps between groups write nothing twice.

The inflation and labour lenses (70 series):
```
.venv/bin/python -m altdata.fred_history backfill --series fed_target_upper,fed_target_lower,effr,estr,sonia,mts_deficit,mts_receipts,mts_outlays,fed_interest_payments,fed_current_receipts,fed_debt_total,nonfin_corp_debt,korea_exports,cpi_shelter,cpi_rent,cpi_oer,cpi_services,cpi_core_goods,cpi_used_cars,ppi_final_demand,ppi_intermediate,ppi_unprocessed,import_prices,import_prices_ex_fuel,atl_wage_tracker,cpi_energy,cpi_food,cpi_core_services,cpi_commodities,cpi_median,cpi_trimmed_mean,cpi_airline_fares,cpi_transport_services,ppi_truck_freight,payrolls_private,payrolls_edu_health,unemployed_level,claims_initial,claims_continuing,permanent_job_losers,lfpr_prime_age,temp_help,agg_weekly_hours,eci_total,eci_wages,atl_wage_switchers,atl_wage_stayers,diffusion_states_1m,diffusion_states_3m,ecb_assets,cpi_c_food_home,cpi_c_food_away,cpi_c_alcohol,cpi_c_gasoline,cpi_c_electricity,cpi_c_utility_gas,cpi_c_apparel,cpi_c_new_vehicles,cpi_c_vehicle_parts,cpi_c_medical_goods,cpi_c_tobacco,cpi_c_household,cpi_c_personal_care,cpi_c_lodging,cpi_c_water_trash,cpi_c_professional_med,cpi_c_hospital,cpi_c_vehicle_repair,cpi_c_tuition,cpi_c_video_audio --dry-run | tail -40
```

The 29 series for the PPI and GDP lenses (GDPNow's path needs its vintages):
```
.venv/bin/python -m altdata.fred_history backfill --series ppi_fd_core_ex_trade,ppi_trade_services,ppi_stage1,ppi_stage2,ppi_stage3,ppi_stage4,ppi_portfolio_mgmt,ppi_airline_passenger,ppi_hospitals,ppi_physicians,gdp_real_growth,final_sales_pdp,gdp_contrib_pce,gdp_contrib_nonres,gdp_contrib_residential,gdp_contrib_inventories,gdp_contrib_net_exports,gdp_contrib_government,gdp_deflator,gdi_nominal,inv_info_equipment,inv_software,inv_nonres_structures,inv_residential_real,corp_profits_after_tax,real_disp_income,real_income_ex_transfers,saving_rate,gdpnow --dry-run | tail -40
```

The fiscal, sentiment, policy-dot and contribution series (15):
```
.venv/bin/python -m altdata.fred_history backfill --series customs_duties,goods_imports,dsr_household,dsr_consumer,dsr_mortgage,uoM_sent,fed_defense,fy_net_interest,fy_net_outlays,fy_deficit,fy_deficit_gdp,sep_median_ff,contrib_info_equipment,contrib_software,nfp --dry-run | tail -40
```

- **Expect** per series: the vintages found and the rows that would be written.
- **`nfp`** is listed because the revisions lens reads PAYEMS's vintages. If Monday's FRED history run already took it, it writes nothing.
- **Paste back** any series reported "no vintages" or "refused".

**B4. The other FRED first pulls, and the series computed from the store.**
```
.venv/bin/python -m altdata.sources.fred
.venv/bin/python -m altdata.market_features compute --from 2000-01-01 --dry-run | tail -20
.venv/bin/python -m altdata.market_features compute --from 2000-01-01
.venv/bin/python -m altdata.absorption compute --dry-run
.venv/bin/python -m altdata.absorption compute
.venv/bin/python -m altdata.funding_currency compute --dry-run
.venv/bin/python -m altdata.funding_currency compute
```
- **Expect** OK with the rows written for the FRED pull, then each compute's row counts.
- Run `market_features` after B3, so the CPI lead composite and the since-FOMC attribution cut read the full history.

**B5. The names backfill for the opening setup** (from the chains already on disk; idempotent).
```
.venv/bin/python -m altdata.chain_metrics backfill-names --days 60 --dry-run
.venv/bin/python -m altdata.chain_metrics backfill-names --days 60
```
- **Expect** per day, the names read and the rows written: options volume, front-month IV, 25-delta put skew, IV against realised, the front expiry, and the two put shares.
- **Until it runs,** the most-active table's ranks print "one reading".

**B6. The crypto data layer's first pulls and backfills** (no key needed; the backfills take about 15 minutes in all).
```
.venv/bin/python -m altdata.sources.hl backfill --dry-run
.venv/bin/python -m altdata.sources.fut backfill --dry-run
.venv/bin/python -m altdata.sources.mempool backfill --dry-run
.venv/bin/python -m altdata.sources.deribit backfill --dry-run
.venv/bin/python -m altdata.sources.farside backfill --dry-run
.venv/bin/python -m altdata.sources.hl backfill
.venv/bin/python -m altdata.sources.fut backfill
.venv/bin/python -m altdata.sources.mempool backfill
.venv/bin/python -m altdata.sources.deribit backfill
.venv/bin/python -m altdata.sources.farside backfill
.venv/bin/python -m altdata.sources.llama pull --only watch
.venv/bin/python -m altdata.sources.llama pull --only coins
.venv/bin/python -m altdata.sources.fng
.venv/bin/python -m altdata.sources.blockscout
.venv/bin/python -m altdata.sources.gt
.venv/bin/python -m altdata.sources.paprika
.venv/bin/python -m altdata.sources.treasury
.venv/bin/python -m altdata.sources.crypto_derived
```
- **Expect** each to print OK with its rows.
- `gt` writes the fallback source's rows only (robots.txt refuses the first source).
- `treasury` reads the share count only if `CHESTER_SEC_CONTACT` is set.
- `crypto_derived` runs last because it reads what the others wrote.
- **⚑ Farside:** if its dry run prints a 403 or a changed header, the box is behind Cloudflare. Do not retry; paste it back, and it becomes a listed gap.

**B7. The PRL and the mechanism scan: dry runs.** CoinGecko is retired under its terms, so there is no CoinGecko step.
```
.venv/bin/python -m altdata.prl daily --dry-run | head -80
.venv/bin/python -m altdata.prl daily
.venv/bin/python -m altdata.sources.pearl_explorer --dry-run
.venv/bin/python -m altdata.prl weekly --dry-run --force
.venv/bin/python -m altdata.mechanism_scan run --dry-run --force
```
- **Expect** `prl daily` to print every figure with its trace: D1, D2 and the reward ESTIMATED; D3 and D5 absent. The explorer reports "estimated" or PENDING with its reason. The scan's dry run reads the feeds and DefiLlama, with no model call and no write.
- **⚑ The explorer:** if the box can reach it, read its `robots.txt` and terms (`curl -sS https://explorer.pearlresearch.ai/robots.txt | head -40`) and paste them back. A session declares an endpoint only after that.
- **⚑ The mechanism-watch drafts:** after the first real scan, review them (`.venv/bin/python -m altdata.mechanism_watch review`). Promote and reject are yours, with `--confirm`.

**B8. The other new writers' first pulls**, each its whole history on the first run. After that each rides the scheduled pull. `sp500_members` is the longest (about 500 names), so it runs last.
```
.venv/bin/python -m altdata.sources.ons_cpi
.venv/bin/python -m altdata.sources.statcan_cpi
.venv/bin/python -m altdata.sources.bdf_webstat
.venv/bin/python -m altdata.sources.bundesbank
.venv/bin/python -m altdata.sources.bis_cbpol
.venv/bin/python -m altdata.sources.ecb_irs
.venv/bin/python -m altdata.sources.census_vip
.venv/bin/python -m altdata.sources.rent_indices
.venv/bin/python -m altdata.sources.clevfed_rules
.venv/bin/python -m altdata.sources.redfin
.venv/bin/python -m altdata.sources.mba
.venv/bin/python -m altdata.sources.wgc_stock
.venv/bin/python -m altdata.sources.stat_jp_cpi
.venv/bin/python -m altdata.sources.fiscaldata
.venv/bin/python -m altdata.sources.edgar_xbrl
.venv/bin/python -m altdata.sources.sp500_members
```
- **Expect** OK with its rows for each. STALE carries its reason.
- `edgar_xbrl` prints PENDING and fetches nothing unless `CHESTER_SEC_CONTACT` is set.
- MBA's chain starts from the first stored week, so it grows by one each Wednesday.
- **After the Webstat pull, optionally confirm OAT-Bund's crisis line from the store** (expect 208.1):
  ```
  .venv/bin/python -c "from altdata import batch3, observations; st = observations.ObservationStore(); print(batch3.crisis_level_daily(st, '2026-12-31', {'fr': 'bdf.oat_tec10', 'de': 'bbk.bund_10y'}))"
  ```
- **Paste back** a STALE line, or a crisis line other than 208.1.

**B9. The scan's figures and the base-rate tables** (both idempotent; the Monthly's run does them too).
```
.venv/bin/python -m altdata.scans ingest
.venv/bin/python tools/base_rates.py compute
```
Expect the GTM rows ingested and three new tables stored.

**B10. The Alpha Lab's tells, base rates and roster** (writes to the lab's own database only).
```
.venv/bin/python -m alpha.tells import --dry-run
.venv/bin/python -m alpha.tells import
.venv/bin/python -m alpha.event_rates compute
.venv/bin/python -m alpha.manifest register alpha/research/roster-2026-10-17-x3.yaml
```
Expect the tells it registers, then the base rates with their n. On Sunday the lab line reads "not yet live · tells N (...)".

**B11. ⚑ The committed narrative proposals.**
```
.venv/bin/python -m altdata.narratives seed
```
- Three proposals enter as proposed; the close's seed would do the same.
- **Confirming or rejecting each is yours alone:** `python -m altdata.narratives confirm <id>` or `reject <id>`.

**B12. The meme ingest, and the X pilot's inboxes.**
```
mkdir -p ~/chester-data/inbox/x-triage ~/chester-data/inbox/x-digest
.venv/bin/python -m altdata.meme_ingest --dry-run
.venv/bin/python -m altdata.meme_ingest
.venv/bin/python -m altdata.meme_ingest status
systemctl --user enable --now chester-meme-ingest.timer
.venv/bin/python -m daily_cascade.digital_addendum render --week-ending 2026-10-23 --no-narrative
```
- `CHESTER_MEME_DROP` in `.env` is optional: the default is `~/chester-meme/drop`.
- **Expect** the ingest's draft count. The next 16:45 close and 07:00 anchor print the meme line. The digital page renders to `reports/dryrun/` and sends nothing.

---

## C. The encrypted-backup migration (do C1 to C4 the merge evening, before 02:30)

**Values never go anywhere but `.env` and your password manager:**
- generate the password and salt (32 random characters each);
- put both in the password manager **first**;
- add the names below to `.env` by hand.

A session never reads `.env`.

**C1. ⚑ The backup account's consent** (a browser step).
- On the box: `rclone config` → new remote, type `drive`, your own client ID and secret, scope `drive`.
- Then on the laptop: `rclone authorize "drive" …`, signed in as the **separate backup account**.
- Prove it: `rclone lsd <backup remote name>:`.

**C2. ⚑ The read-only inbox remote** on your main account: the same steps, scope `drive.readonly`. It reads AAII's row, GLD's archive and the X pilot's files. Prove it with `rclone lsd <name>:`.

**C3. ⚑ The outbox remote** on your main account: scope `drive.file`, which lets it create and write only its own files.
```
rclone lsd <outbox remote name>: && rclone mkdir <outbox remote name>:chester-vendor-checks/lab-outbox
```
Do not reuse the crypt remote.

**C4. `.env`, by name** (the values are yours):
- `CHESTER_RCLONE_BACKUP_REMOTE`
- `CHESTER_RCLONE_CRYPT_PASSWORD`
- `CHESTER_RCLONE_CRYPT_SALT`
- `CHESTER_RCLONE_INBOX_REMOTE`
- `CHESTER_RCLONE_OUTBOX_REMOTE`
- optionally `CHESTER_MEME_DROP`

Then the first encrypted backup, by hand:
```
scripts/rclone_sync.sh; echo "exit=$?"; cat ~/.chester/rclone_sync_status ~/.chester/backup_snapshot
```
- **Expect** `exit=0`, `state=ok`, and a record with the observations count. The backup account's Drive folder should hold only encrypted names.
- **Paste back** any `exit` other than 0.

**C5. The first restore test, then its weekly timer.**
```
scripts/run_restore_test.sh; cat ~/.chester/restore_test_status
systemctl --user daemon-reload && systemctl --user enable --now chester-restore-test.timer
```
Expect `state=restore_ok`. Can wait a day after C4, no longer.

**C6. The append-only trigger migration** (idempotent, safe at any time; every writer already inserts only).
```
.venv/bin/python -m altdata.observations install-triggers
.venv/bin/python -m altdata.observations triggers
```
Expect the triggers listed (`triggers` exits 3 if they are not in).

**C7. ⚑ Revoke the old full-scope token, last.**
- **Wait for both:** C5 has passed, and one night's sweep log shows `lab-outbox` written through its own remote.
- **Revoke:** the main account's Security page → third-party access → the rclone client. Revoking before C2 and C3 would stop the inbound files and the lab outbox.
- **Then:**
  - remove the `chester-backup.service.d/remote.conf` drop-in;
  - delete the old plaintext folder `gdrive:chester-backups` after a retention period you choose. Eight weeks is the natural point, when nothing in it is newer than the encrypted 14 daily and 8 weekly snapshots.

---

## D. The ledger re-runs (box editions, written outside the checkout)

**Why outside the checkout:** each writes a new dated file to `~/chester-data/ledgers`, so no run dirties the tree that `git pull --ff-only` needs clean. Each supersedes its laptop first edition, and none is ever edited. None loses anything by waiting; run them after B3 and B4, so the store runs read the full history.

```
mkdir -p ~/chester-data/ledgers
# ST-7 (five studies)
.venv/bin/python tools/calibration/sr12_bond_alloc.py --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr15_valuation.py  --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr21_divergence.py --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr22_auctions.py   --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr23_net_supply.py --box --out ~/chester-data/ledgers
# ST-8 (four studies, and SR-5 on ALFRED's first prints with the box's FRED key)
.venv/bin/python tools/calibration/sr01_sr13_style.py --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr14_em_dollar.py  --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr02_yen_unwind.py --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr04_cny_fix.py    --box --out ~/chester-data/ledgers
.venv/bin/python tools/calibration/sr05_consumer_credit.py --box --alfred --out ~/chester-data/ledgers
# ST-9, the false-bottom audit
.venv/bin/python tools/calibration/sr08_false_bottoms.py --box --out ~/chester-data/ledgers
# 31b and 44b (the store's constituents)
.venv/bin/python -m altdata.ledgers.st_r5_31b --source store --out ~/chester-data/ledgers
.venv/bin/python -m altdata.ledgers.st_r5_44b --source store --out ~/chester-data/ledgers
# 17b and 19b (the store), and Batch 6's five (public sources, until their writers exist)
.venv/bin/python -m altdata.ledgers run 17b --source store --out ~/chester-data/ledgers
.venv/bin/python -m altdata.ledgers run 19b --source store --out ~/chester-data/ledgers
.venv/bin/python -m altdata.ledgers run all --source public --out ~/chester-data/ledgers
```

- **Expect** each to print its verdict line and the path it wrote.
  - SR-22 runs once: its box edition carries the labelled variant and the base rates.
  - SR-4 takes about four minutes.
  - A store run whose history the store lacks refuses, and names the key.
- **Then, from the laptop:**
  ```
  scp 'vps:~/chester-data/ledgers/*' docs/ledgers/
  ```
  and tell a session to commit them.
- **⚑ If SR-1's box edition does not PASS,** the style panel and its thresholds come out. A session removes them on that ledger.
- **Paste back** any run that fails.

---

## E. Read-only checks (any hour; they write nothing)

**E1. The dealer block on 16 Oct, from the stored captures:**
```
.venv/bin/python -m daily_cascade.dealer_block show --date 2026-10-16
```

**E2. The vendor reconciliation on our 16 Oct capture:**
```
ls data/chains/2026-10-16/SPY_*.csv
.venv/bin/python tools/vendor_reconcile.py --chain data/chains/2026-10-16/SPY_<stamp>.csv
```
Use the stamp the `ls` prints. Expect our gamma and the vendor's in the same terms, strike by strike. Paste back the summary.

**E3. The store registry check, again, after B:**
```
.venv/bin/python -m tools.check_store_registry --db data/chester.db
```
Expect no stored key the registry does not know, and the new keys present. Paste back any unregistered key.

**E4. What the new blocks read, before the first renders:**
```
.venv/bin/python -m altdata.releases show | head -200
.venv/bin/python -m altdata.releases_b show | head -200
.venv/bin/python -m altdata.surprise_index show | head -80
.venv/bin/python -m altdata.macro_6e show | head -120
.venv/bin/python -m altdata.batch5 verify
.venv/bin/python -m altdata.batch5b show | head -150
.venv/bin/python -m altdata.st_r5_rates show
.venv/bin/python -m altdata.st_r5_index show
.venv/bin/python -m altdata.st_r5_t1_rest show
.venv/bin/python -m altdata.gtm show
.venv/bin/python -m altdata.gtm_equities show
.venv/bin/python -m altdata.absorption show
.venv/bin/python -m altdata.funding_currency show
.venv/bin/python -m altdata.es_block show --slot close | head -60
.venv/bin/python -m altdata.system_metrics show --month 2026-10
.venv/bin/python -m altdata.state_vector show --date $(date +%F)
.venv/bin/python -m alpha.tells list
.venv/bin/python -m alpha.event_rates show
.venv/bin/python -m altdata.sources.treasury show
```

**E5. The first renders to read** (the dry runs are yours, as always):
- **The next 07:00 anchor:** the gauge, the three volatility lines, "Largest OI builds, side unknown" and the two put-volume lines. No pre-market line prints.
- **The next 16:45 close:** the ES block, the meme line, the 12:30 hooks.
- **The Weekly of Sunday 25 Oct:** the most-active table, the setup profiles, the single-name put share, the Sunday line, GTM-13 and the ES panel.
- **The Monthly of 1 Nov** (`python -m monthly_macro.run --dry-run`): the PPI and GDP panels, the style panel, the Factor IV lines, the PRL part, and the metrics block last.

**E6. ⚑ The chat-side FlashAlpha tasks:** on Thu 29 Oct, if the divergence gate was clean through Wed 28 Oct, delete the two scheduled FlashAlpha tasks (ruling 4 of 17 Oct).

---

## The one pull request

**chain-2 into main, after Monday's six:** aud-3b-security-master, weekly-fixes-8, weekly-fixes-9, docs-batch-7, -8 and -9.
- Open it Tuesday afternoon if its CI is green, and merge it inside Tuesday's evening window (17:20–23:30), as **a merge commit**, never squash or rebase, so each branch's history survives.
- **It merges cleanly whether or not every Monday PR has landed,** because it carries Monday's line itself.

**If GitHub asks to update the branch** (main moved after chain-2's last commit):
- choose **"Update with merge commit"**, never rebase, or ask a session to merge main into chain-2;
- wait for that commit's CI to go green before merging.

If the update shows a conflict, stop and hand it to a session. Do not resolve it in the browser.
