# B109 notes: the names gate, and the sweep of main

Paste B109 (`docs/pastes/B109.md`), 2 Nov 2026. Branch `b109-names-gate`, from
origin/main at `422ea697`. These notes carry no name, and neither does any commit
message. Every hit below is a count, never the word.

## The gate (`tools/validate_names.py`, GATE_KIND "code")

**What it scans.**
- Every tracked file (`git ls-files`), `docs/pastes/` included.
- It skips binaries: known extensions, or a NUL byte in the first 8 KiB.
- It reads the working tree and never git history.

**What a hit is.**
- Each denylist entry is matched as a whole word, case-insensitively.
- A hit fails the gate and is printed as `file:line`, with the name masked as `***`.

**Where the list comes from.** The list is never committed:
1. the environment variable `CHESTER_NAMES_DENYLIST` (comma-separated); else
2. the file named by `CHESTER_NAMES_FILE` (one per line, or comma-separated).

The default file name, `.chester-names`, is gitignored.

**What it never counts.**
- The repository's and the organisation's names, in a path, a URL or alone: any
  token containing "chester", and every URL. A denylist entry "chester" is ignored,
  with a message.
- The measure names Sahm, Brier, CAPE, Taylor, Wu-Xia and ACM. They are removed
  from the line before the denylist is matched.
- Git history.

**Without the list.** It runs its self-test (11 checks on fixture names, none of them
real), prints "names gate: no denylist; skipped" and exits 0. CI and a fresh laptop
never fail for want of the list.

**The wiring.**
- **The Makefile:** one line, after `validate_secrets.py`.
- **CI:** the gate joins the matrix from the Makefile, as every gate does.
- **Secrets:** the Gates workflow read no secrets before; only `monthly-report.yml`
  does. The gate's step now carries
  `CHESTER_NAMES_DENYLIST: ${{ matrix.gate == 'tools/validate_names.py' && secrets.CHESTER_NAMES_DENYLIST || '' }}`,
  so the secret reaches that one job and no other.
- **What the operator sets:** a repository secret named `CHESTER_NAMES_DENYLIST`.
  Until it is set, the job runs the self-test and skips the scan.

**The counts.** CLAUDE.md now says 136 code gates (133 Python, three shell). There
is no stitch tool for the count on main, so it was edited by hand once;
`validate_audit_3a` gives 88/0.

## Setting the list

- **The laptop, for one PowerShell session:**
  `$env:CHESTER_NAMES_DENYLIST = "<name>"`.
  Alternatively, keep the names in `.chester-names` at the checkout's root (it is
  gitignored) and set `$env:CHESTER_NAMES_FILE = ".chester-names"`.
- **The box:** one line in the environment the gates run under. For example, add
  `CHESTER_NAMES_DENYLIST=<name>` to the box's `.env`, which no file in the repo
  holds, or an `Environment=` line in a drop-in for the unit that runs
  `make validate`.

## The sweep of main

The operator's first name was the only entry. It came from the paste's own first
line and was passed on the command line only.

**The counts:**

| Stage | Hits | Files |
|---|---|---|
| Before | 414 | 170 |
| After | 33 | 20 |

**The replacements:**
- **What changed:** 396 replacements in 163 files, prose forms only. A possessive
  became "the operator's"; the bare name became "the operator", or "The operator"
  at a sentence's start; the two upper-case docstring forms became "THE OPERATOR".
- **A follow-up fix:** the sweep left "the operator" before the surname in 27 files
  (the owner, signatory and "Prepared for" lines). Those now read "the operator".
- **Rebuilt:** the HTML editions of the swept papers and the Master Guide.

**What was left, and why: the 33 remaining hits.**
- **19: the box's login, inside `/home/<login>/` paths.** These are in
  `.claude/settings.json`'s deny rules (4), `deploy/systemd/README.md` (2),
  `tools/validate_deploy.py` (7, the deny tests), `tools/validate_morning_anchor.py`
  (2), and three notes (4). Changing them would break the deny list and the tests
  that hold it.
- **3: the login in commands.** These are `docs/runbooks/restore.md`'s
  `adduser`, `usermod` and `loginctl` lines, and `docs/briefs/a61b-box-sheet.md`'s
  "user …". They are the box's account, not prose.
- **7: comments in `deploy/systemd/*.service`.** The self-deploy compares the whole
  `deploy/systemd/` tree. A changed unit is copied, and a running one is flagged
  "restart pending" (A-4). A comment-only change would raise that on seven units,
  the Gateway's among them. The units were left; the README's prose was changed.
- **3: `docs/ledgers/`, two pre-registrations and a dated ledger.** They are never
  edited, and the sweep's edits there were reverted.
- **1: a paste header.** `docs/pastes/A78.md` is the only paste on main whose first
  line is the standing "From <name> - run this" header: 1 of the 6 paste files
  main carries. Every later paste was committed with the header stripped (D38).
  Whether the header changes is the operator's call, and it was not changed.

**For the operator's ruling:**
- Whether the gate should exclude a `/home/<login>/` path segment and the login in
  commands. They are an account name, not prose, and the exclusion would make the
  gate pass with the list set.
- Whether the seven unit-file comments change in a window where the operator
  restarts the units anyway.
- Whether A78's header changes.

Until then, with the list set, the gate fails on these 33 lines and names each.

## Gates (one at a time)

| Gate | Tally |
|---|---|
| validate_names, no list | 11/0, "names gate: no denylist; skipped", exit 0 |
| validate_names, the list in the variable | 11/1: 33 hits in 20 files, as above |
| validate_names, the list in a file (`CHESTER_NAMES_FILE`) | the same 33 hits |
| check_registry | OK |
| check_library | 27 papers, 0 failures, 0 warnings (HTML rebuilt) |
| check_master_guide | VALIDATION PASSED |
| validate_audit_3a (the count) | 88/0 |
| validate_gates, validate_deploy, validate_secrets | PASSED |
| Gates for the swept code and text | digital_addendum 94/0, security_master 102/0, secondary_notes 88/0, systemd_units 166/0, by_hand_audit 17/0, a55_box_fixes 31/0, lenses 49/0, derived 52/0, crypto_sources 117/0, official_sources 340/0 |
| validate_st_t5_render | Appendix F's check passes. The gate crashes in group D, which is main's known date drift; B101 pinned it on its own branch |

## The sweep, by file (before and after)

| File | Before | After |
|---|---|---|
| `.claude/settings.json` | 4 | 4 |
| `CLAUDE.md` | 1 | 0 |
| `altdata/derived.py` | 2 | 0 |
| `altdata/figi.py` | 1 | 0 |
| `altdata/purge_synthetic.py` | 1 | 0 |
| `altdata/security_master.py` | 1 | 0 |
| `altdata/sm_draft.py` | 1 | 0 |
| `altdata/sources/blockscout.py` | 1 | 0 |
| `altdata/sources/fut.py` | 2 | 0 |
| `altdata/sources/spdji.py` | 1 | 0 |
| `altdata/st_r5_rates.py` | 1 | 0 |
| `config/basis_proxy.yaml` | 1 | 0 |
| `config/batch5_tranche_1b.yaml` | 1 | 0 |
| `config/crypto_sources.yaml` | 3 | 0 |
| `config/data_quality.yaml` | 1 | 0 |
| `config/digital_addendum.yaml` | 1 | 0 |
| `config/digital_asset_calendar.yaml` | 2 | 0 |
| `config/listing_exchanges.yaml` | 1 | 0 |
| `config/monthly_themes.yaml` | 2 | 0 |
| `config/narratives.yaml` | 1 | 0 |
| `config/prediction_markets.yaml` | 2 | 0 |
| `config/releases.yaml` | 1 | 0 |
| `config/reporting_stack.yaml` | 1 | 0 |
| `config/risk_limits.yaml` | 1 | 0 |
| `config/scoreboard.yaml` | 1 | 0 |
| `config/security_master.yaml` | 1 | 0 |
| `config/st_r5_rates.yaml` | 1 | 0 |
| `config/st_r5_t1_rest.yaml` | 1 | 0 |
| `config/tracked_entities.yaml` | 1 | 0 |
| `config/vol_event.yaml` | 1 | 0 |
| `daily_cascade/digital_addendum.py` | 3 | 0 |
| `deploy/systemd/README.md` | 8 | 2 |
| `deploy/systemd/chester-backup.service` | 1 | 1 |
| `deploy/systemd/chester-daily-close.service` | 1 | 1 |
| `deploy/systemd/chester-eod.service` | 1 | 1 |
| `deploy/systemd/chester-monthly.service` | 1 | 1 |
| `deploy/systemd/chester-voices.service` | 1 | 1 |
| `deploy/systemd/chester-weekly.service` | 1 | 1 |
| `deploy/systemd/ibgateway.service` | 1 | 1 |
| `docs/briefs/6e-digital-notes.md` | 7 | 0 |
| `docs/briefs/6e-family-assignments.md` | 1 | 0 |
| `docs/briefs/6e-lenses-notes.md` | 1 | 0 |
| `docs/briefs/6e-releases-notes.md` | 5 | 0 |
| `docs/briefs/6e-rest-notes.md` | 3 | 0 |
| `docs/briefs/a44-opening-setup-notes.md` | 1 | 0 |
| `docs/briefs/a47-chain3-notes.md` | 1 | 0 |
| `docs/briefs/a48-batch11-notes.md` | 2 | 0 |
| `docs/briefs/a49-secondary-notes-notes.md` | 6 | 0 |
| `docs/briefs/a50-dealer-store-notes.md` | 2 | 0 |
| `docs/briefs/a55-box-fixes-notes.md` | 2 | 0 |
| `docs/briefs/a56-batch14-a1-notes.md` | 1 | 0 |
| `docs/briefs/a61b-box-sheet.md` | 2 | 1 |
| `docs/briefs/alpha-lab-2-notes.md` | 7 | 0 |
| `docs/briefs/alpha-lab-3-notes.md` | 4 | 0 |
| `docs/briefs/alpha-lab-4-notes.md` | 2 | 0 |
| `docs/briefs/alpha-lab-brief-2026-10-12.md` | 1 | 0 |
| `docs/briefs/aud-1-notes.md` | 5 | 0 |
| `docs/briefs/aud-2-notes.md` | 4 | 1 |
| `docs/briefs/aud-3a-notes.md` | 3 | 0 |
| `docs/briefs/aud-3b-notes.md` | 8 | 2 |
| `docs/briefs/aud-3c-notes.md` | 2 | 0 |
| `docs/briefs/aud-3d-notes.md` | 1 | 0 |
| `docs/briefs/audit-4-agenda.md` | 7 | 0 |
| `docs/briefs/audit-leftovers-1-notes.md` | 3 | 0 |
| `docs/briefs/audit-leftovers-2-notes.md` | 1 | 0 |
| `docs/briefs/b45-chain3-notes.md` | 1 | 0 |
| `docs/briefs/b48-scoreboard-notes.md` | 3 | 0 |
| `docs/briefs/b52-batch14-a2-notes.md` | 2 | 0 |
| `docs/briefs/book-b-scanner-2-notes.md` | 1 | 0 |
| `docs/briefs/book-b-scanner-brief-2026-10-12.md` | 1 | 0 |
| `docs/briefs/chain-2-box-sheet.md` | 1 | 0 |
| `docs/briefs/chain-2-stitch-notes.md` | 1 | 0 |
| `docs/briefs/chain-3-box-sheet.md` | 3 | 0 |
| `docs/briefs/chain-4-box-sheet.md` | 5 | 0 |
| `docs/briefs/chain-5-box-sheet.md` | 3 | 0 |
| `docs/briefs/crypto-basket-brief-2026-10-12.md` | 1 | 0 |
| `docs/briefs/crypto-basket-notes.md` | 1 | 0 |
| `docs/briefs/crypto-tranche-a-1-notes.md` | 4 | 0 |
| `docs/briefs/crypto-tranche-a-2-notes.md` | 2 | 0 |
| `docs/briefs/dealer-positioning-brief-2026-10-09.md` | 1 | 0 |
| `docs/briefs/digital-49-51b-notes.md` | 2 | 0 |
| `docs/briefs/doctrine-2-proposals-st-l.md` | 1 | 0 |
| `docs/briefs/doctrine-monthly-2026-10-agenda.md` | 1 | 0 |
| `docs/briefs/doctrine-monthly-2026-10-minutes.md` | 7 | 0 |
| `docs/briefs/el-4-6-notes.md` | 1 | 0 |
| `docs/briefs/lenses-group-b-notes.md` | 5 | 0 |
| `docs/briefs/master-guide-notes.md` | 1 | 0 |
| `docs/briefs/meme-ingest-ledgers-1-notes.md` | 1 | 0 |
| `docs/briefs/meme-ingest-notes.md` | 1 | 0 |
| `docs/briefs/metric-lenses-brief-2026-10-01.md` | 2 | 0 |
| `docs/briefs/monthly-style-reference.md` | 1 | 0 |
| `docs/briefs/monthly-v2-brief-2026-10-01.md` | 6 | 0 |
| `docs/briefs/post-friday-fixes-notes.md` | 1 | 0 |
| `docs/briefs/reading-shelf-brief-2026-10-05.md` | 5 | 0 |
| `docs/briefs/reporting-stack-brief-2026-10-02.md` | 6 | 0 |
| `docs/briefs/rulings-2026-10-24-evening.md` | 1 | 0 |
| `docs/briefs/sm-schema-1-1-notes.md` | 1 | 0 |
| `docs/briefs/sr-38-inbox-notes.md` | 1 | 0 |
| `docs/briefs/st-r4-tranche-1-notes.md` | 3 | 0 |
| `docs/briefs/st-r4-tranche-1b-notes.md` | 5 | 0 |
| `docs/briefs/st-r5-audit-notes.md` | 9 | 0 |
| `docs/briefs/st-r5-fixes-notes.md` | 5 | 0 |
| `docs/briefs/st-r6-45-notes.md` | 3 | 0 |
| `docs/briefs/st-t5-prl-notes.md` | 3 | 0 |
| `docs/briefs/st-t5-render-notes.md` | 1 | 0 |
| `docs/briefs/t3-1-monthly-notes-brief-2026-10-09.md` | 2 | 0 |
| `docs/briefs/vp-1-notes.md` | 1 | 0 |
| `docs/briefs/w-1-1a-notes.md` | 2 | 0 |
| `docs/briefs/weekly-fixes-7-notes.md` | 2 | 0 |
| `docs/briefs/weekly-fixes-8-notes.md` | 2 | 0 |
| `docs/briefs/weekly-fixes-9-notes.md` | 1 | 0 |
| `docs/briefs/writer-fixes-1-notes.md` | 3 | 0 |
| `docs/change-order-alpha-lab-2026-10-12.md` | 1 | 0 |
| `docs/change-order-alternative-assets-quarterly-2026-10-10.md` | 1 | 0 |
| `docs/change-order-crypto-data-sources-2026-10-06.md` | 5 | 0 |
| `docs/change-order-enterprise-layer-2026-09-27.md` | 4 | 0 |
| `docs/change-order-jpm-gtm-2026-10-03.md` | 2 | 0 |
| `docs/change-order-reading-shelf-2026-10-08.md` | 2 | 0 |
| `docs/change-order-secondary-notes-2026-10-19.md` | 8 | 0 |
| `docs/change-order-signal-triage-2026-09-25.md` | 8 | 0 |
| `docs/change-order-signal-triage-batch-11-2026-10-19.md` | 5 | 0 |
| `docs/change-order-signal-triage-batch-13-2026-10-20.md` | 2 | 0 |
| `docs/change-order-signal-triage-batch-14-2026-10-20.md` | 1 | 0 |
| `docs/change-order-signal-triage-batch-16-2026-10-26.md` | 5 | 0 |
| `docs/change-order-signal-triage-batch-3-2026-10-02.md` | 1 | 0 |
| `docs/change-order-sm-schema-1-1-2026-10-16.md` | 3 | 0 |
| `docs/change-order-weekly-storyline-2026-10-11.md` | 1 | 0 |
| `docs/chester-reports-architecture-v3.md` | 5 | 0 |
| `docs/dated-appendix-queue.md` | 4 | 0 |
| `docs/figures/master-guide/fig-02-clock.svg` | 1 | 0 |
| `docs/html/master-guide.html` | 8 | 0 |
| `docs/html/monthly-macro-whitepaper.html` | 1 | 0 |
| `docs/html/rates-liquidity-whitepaper.html` | 1 | 0 |
| `docs/ledgers/after-hours-earnings-preregistration-2026-10.md` | 1 | 1 |
| `docs/ledgers/os-6-ledger-2026-10-19.md` | 1 | 1 |
| `docs/ledgers/release-first-hour-preregistration-2026-10.md` | 1 | 1 |
| `docs/master-guide.md` | 6 | 0 |
| `docs/master-guide/chat-tasks.yaml` | 10 | 0 |
| `docs/narrative-register-pairs.md` | 2 | 0 |
| `docs/pastes/A78-attachment-round-7.md` | 5 | 0 |
| `docs/pastes/A78.md` | 1 | 1 |
| `docs/runbooks/restore.md` | 3 | 2 |
| `docs/signal-triage-register.md` | 1 | 0 |
| `docs/warsh-matrix-lines.md` | 4 | 0 |
| `docs/white-paper-library-audit-1-workorder.md` | 6 | 0 |
| `docs/whitepapers/monthly-macro-whitepaper.md` | 1 | 0 |
| `docs/whitepapers/rates-liquidity-whitepaper.md` | 1 | 0 |
| `docs/workplan-v3-2026-10-02.md` | 5 | 0 |
| `docs/workplan-v5-2026-10-09.md` | 1 | 0 |
| `docs/workplan-v6-2026-10-10.md` | 1 | 0 |
| `docs/workplan-v7-2026-10-16.md` | 2 | 1 |
| `metrics_registry.yaml` | 1 | 0 |
| `monthly_macro/prose.py` | 3 | 0 |
| `monthly_macro/v2.py` | 3 | 0 |
| `scripts/rclone_crypt_env.sh` | 2 | 0 |
| `source_registry.yaml` | 1 | 0 |
| `tools/assign_families.py` | 2 | 0 |
| `tools/calibration/os6_positioning.py` | 2 | 0 |
| `tools/figures/master_guide.py` | 2 | 0 |
| `tools/massive_flatfiles_backfill.py` | 2 | 0 |
| `tools/seed_security_master.py` | 1 | 0 |
| `tools/validate_a55_box_fixes.py` | 1 | 0 |
| `tools/validate_alpha.py` | 1 | 0 |
| `tools/validate_by_hand_audit.py` | 2 | 0 |
| `tools/validate_deploy.py` | 7 | 7 |
| `tools/validate_digital_addendum.py` | 2 | 0 |
| `tools/validate_morning_anchor.py` | 2 | 2 |
| `tools/validate_secondary_notes.py` | 1 | 0 |
| `tools/validate_security_master.py` | 1 | 0 |
| `tools/validate_systemd_units.py` | 1 | 0 |

## B111 (2 Nov 2026): the ruled exclusions

Ruling (f) of 2 Nov 2026, from the needs-you above:
- the gate excludes the box's login in home paths and in account commands;
- it allowlists the three never-edited ledgers by path;
- the seven unit-file comments and A78's paste header are swept in the merge-week
  deploy window, not now.

This was built on this branch (continued from `04439228`); the paste is on
`b100-hygiene` (`docs/pastes/B111.md`).

**An account, not prose.** These words are removed from a line before the denylist
is matched; the rule is stated in the gate's header:
- **a home-path segment:** `/home/<login>`, `/Users/<login>`, `C:\Users\<login>`;
- **an address:** `<login>@host`, including `ssh <login>@host`;
- **an account command,** with its arguments up to the next shell separator:
  `chown`, `chgrp`, `su`, `sudo -u`, `adduser`, `useradd`, `usermod`, `userdel`,
  `passwd`, and `loginctl enable-linger` or `disable-linger`;
- **the box sheet's form,** "user `<login>`".

The same word in prose is still a hit.

**The path allowlist.** It is read from the same place as the list: an
`allow:<path>` entry in `CHESTER_NAMES_DENYLIST` or the names file, or
`CHESTER_NAMES_ALLOW_PATHS` (comma-separated). One repository secret can therefore
carry both. The scan prints "allowlisted: n files" and each path, and marks an
allowed path that is not tracked.

**The seed for the operator**, appended to the secret's value as three entries:

```
allow:docs/ledgers/after-hours-earnings-preregistration-2026-10.md
allow:docs/ledgers/os-6-ledger-2026-10-19.md
allow:docs/ledgers/release-first-hour-preregistration-2026-10.md
```

**Swept in the merge-week deploy window (left as found).** Eight lines, each the
same comment or header, quoted masked:

| File | Line | The line, masked |
|---|---|---|
| `deploy/systemd/chester-backup.service` | 82 | `# again; a day's chains cannot be fetched again; the Gateway needs ***'s supervised` |
| `deploy/systemd/chester-daily-close.service` | 68 | the same comment |
| `deploy/systemd/chester-eod.service` | 85 | the same comment |
| `deploy/systemd/chester-monthly.service` | 54 | the same comment |
| `deploy/systemd/chester-voices.service` | 39 | the same comment |
| `deploy/systemd/chester-weekly.service` | 57 | the same comment |
| `deploy/systemd/ibgateway.service` | 90 | `# chains cannot be fetched again; the Gateway needs ***'s supervised login. So the` |
| `docs/pastes/A78.md` | 1 | `From *** - run this (session A): A78, ...` (the standing header) |

The sweep for the units is "the Gateway needs the operator's supervised", in a
window where the operator restarts those units anyway. Every unit file whose
comment changes is flagged restart pending by the self-deploy.

**Re-run, with the operator's first name set locally as the list (never written)
and the seed above:**
- allowlisted: 3 files;
- **8 hits in 8 files, every one of them the eight lines above; 0 outside them**
  (33 before B111);
- the same result with the list in a file (`CHESTER_NAMES_FILE`, `allow:` lines).

Until the window sweep, the gate fails on those eight lines whenever the list is
set. In CI it skips until the secret is set.

| Gate | Tally |
|---|---|
| validate_names, no list (the self-test) | 15/0, "names gate: no denylist; skipped", exit 0 (4 new checks: the account forms, prose still a hit, `allow:` entries are paths, no allowlist set) |
| validate_names, the list and the seed | 15/1: the 8 lines above |
| validate_alpha | 257/0 |
