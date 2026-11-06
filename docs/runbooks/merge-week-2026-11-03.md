# The merge-week sheet — Tue 3 Nov (17:20–23:30 ET) and Wed 4 Nov 2026

*Filed by session B (B121, 2 Nov 2026) from the sheet the operator was handed on
2 Nov. The sheet was written on 2 Nov from A105's and A106's scripts
(`docs/briefs/a105-merge-week-script.md`, on `a105-merge-week-rehearsal-2`). The
chains are the real merges' vehicle, as chain-7 and chain-8 were. Its text is kept
as written. Three things changed:*
- *the laptop's checkout path is "<the laptop's checkout>";*
- *each chain paste is named by its id, with its file under `docs/pastes/`;*
- *an empty Outcome section was added at the end.*

*"You" is the operator. "Me" is the planning chat that wrote the sheet, which
receives the run ids and the needs-you.*

**The chain pastes:**

| Step | Paste | Its file |
|---|---|---|
| 1 | A107, chain-9's assembly (`a107-chain-9-assembly-paste.txt`) | `docs/pastes/A107.md` |
| 7 | A108, chain-8 refreshed to main (`a108-chain-8-refresh-paste.txt`) | `docs/pastes/A108.md` |
| 12 | B112, chain-10's assembly (`b112-chain-10-assembly-paste.txt`) | `docs/pastes/B112.md` |
| 15 | A109, chain-11's assembly (`a109-chain-11-assembly-paste.txt`) | `docs/pastes/A109.md` |
| 18 | B113, chain-12's docs assembly (`b113-chain-12-docs-assembly-paste.txt`) | `docs/pastes/B113.md` |
| 21 | B114, the names sweep of merged main (`b114-names-sweep-merged-main-paste.txt`) | `docs/pastes/B114.md` |

*Each paste is committed by its session on the branch it builds, so each file
reaches main with its chain.*

---

**What this is.** The real merges, run the way the repo already merges big work: each tranche is assembled by a session into a chain branch (exactly as A105/A106 rehearsed, resolutions replayed from their scripts), you open one PR per chain, read its CI once, merge it, and deploy at the three points marked. Five chains: **chain-9** (the small PR), **chain-8** (already assembled, refreshed to main), **chain-10** (filing and data, twelve branches), **chain-11** (the builds, ten branches with step 17a), **chain-12** (the docs tranche, four branches). Then B114's names sweep as the week's last PR, and the library PRs after that.

**Why chains and not 27 PRs.** CI is about 35–45 minutes a run plus queue (B107), so one run per branch would take the week. The rehearsal already proved the merged tree green end to end (run 41393587121); the chains carry the same merge commits, so each chain's CI is the check on exactly what lands.

**Rules for the day.** Sessions assemble and push; they never open or merge a PR, and never touch the box. You do the three things below in PowerShell and the box steps on the box. Deploys only inside the windows: Tue 17:20–23:30, Wed 09:05–15:40 and 17:20–23:30; never 16:00–17:20; and not within ten minutes of 21:30 (the evening note's timer, if enabled). If a chain's CI is red on anything other than what its notes predict, stop and send me the run id: nothing merges on a red that isn't explained.

**The three PowerShell moves** (always from the main checkout):

```
cd <the laptop's checkout>
git fetch origin
```

- **Open:** `gh pr create --base main --head <chain> --title "<title>" --body "<body>"` → prints the PR's URL; the number at its end is `<n>` below.
- **Read CI:** `gh pr checks <n>` → one line per job, "pass" or "fail"; or `gh run list --branch <chain> --limit 1` → `completed success`. If it says `queued` or `in_progress`, wait and run it again; don't use `--watch` (it drops).
- **Merge:** `gh pr merge <n> --merge` → `✓ Merged pull request #<n>`. If it refuses because checks are required and you've read them green yourself: `gh pr merge <n> --merge --admin`. Then `git checkout main` and `git pull` so the laptop's main is current.

**Deploy** (from the same folder): `& "C:\Program Files\Git\bin\bash.exe" scripts/deploy.sh; echo "exit $LASTEXITCODE"` → ends `exit 0`.

---

## Tuesday evening

**Step 1 — 17:20, session A: paste `a107-chain-9-assembly-paste.txt`** (15–25 min). It builds chain-9 from main: A91's fixture fix, the LF pin, the date-drift pins (B101, B101b, B106) and B97's slow-gate groups. It reports the CI run id.

**Step 2 — session B, same time: the XXX figures export** can wait; instead keep session B idle until step 8. (If you want to use the time: B114's input isn't ready, and B112 needs chain-8 on main. Nothing for B yet.)

**Step 3 — when A107 reports: open chain-9's PR.**
```
gh pr create --base main --head chain-9 --title "chain-9: A91 fixture fix, LF pin, date-drift pins, slow-gate groups" --body "Assembled by A107 as rehearsed (A105 steps 0a-0c, A106 22a). Carries A91's validate_audit_fixes change, b85-gitattributes-lf, b101-date-drift-gates (B101, B101b, B106) and b97-slow-gates. Expected CI: green."
```
*You should see:* `https://github.com/achester-trading/chester-reports/pull/<n>`.

**Step 4 — read CI** (`gh pr checks <n>`; about 30–45 minutes after A107's push). *Expected:* every line `pass`. This is the chain that turns the date-drift gates and `validate_audit_fixes` green, so nothing should be red.

**Step 5 — merge it:** `gh pr merge <n> --merge`, then `git checkout main` and `git pull`. *You should see:* `✓ Merged`, then `Fast-forward` (or a merge) with the files updated.

**Step 6 — the laptop's LF re-checkout, once** (the pin only affects files checked out after it; your checkout has about 133 CRLF files that would otherwise show as modified):
```
& "C:\Program Files\Git\bin\bash.exe" -c "git ls-files --eol | grep 'w/crlf' | grep 'attr/.*eol=lf' | awk '{print `$NF}' > lf.txt && wc -l < lf.txt && xargs -d '\n' rm -f -- < lf.txt && xargs -d '\n' git checkout -- < lf.txt && echo done"
```
*You should see:* a number near 133, then `done`. Then `git status --short` → nothing (a clean tree). Delete `lf.txt` afterwards (`del lf.txt`).

**Step 7 — session A: paste `a108-chain-8-refresh-paste.txt`** (15–20 min). It merges the new main into chain-8 so its PR is clean. Tell it chain-9 is on main (its first check).

**Step 8 — when A108 reports: open chain-8's PR.**
```
gh pr create --base main --head b86-chain-8-assembly --title "chain-8: the nine-member assembly (B86), refreshed to main" --body "Assembled by B86, rehearsed by A99/A105, refreshed by A108. Members: s1-stitch-refactor, b70, a80, b75, b76, a81, b58, a71, a79. Expected CI: green."
```
**Step 9 — read CI** (30–45 min). *Expected:* all pass. **Step 10 — merge**, `git pull`.

**Step 11 — first deploy** (about 19:30; the box gets chain-8). `& "C:\Program Files\Git\bin\bash.exe" scripts/deploy.sh; echo "exit $LASTEXITCODE"` → `exit 0`. Chain-8's own box steps are in `docs/briefs/b86-notes.md` on main after this merge; most are "none until the next run". Nothing else on the box tonight.

**Step 12 — both sessions at once:** session B pastes `b112-chain-10-assembly-paste.txt` (45–60 min; tell it chain-8 is on main). Session A waits: chain-11 must start from main *after* chain-10 (its branches touch the same registers), so A109 is step 15.

**Step 13 — when B112 reports: open chain-10's PR**, read CI, merge, `git pull`.
```
gh pr create --base main --head chain-10 --title "chain-10: filing and data branches (a90, b95-cboe-held, a84, b81, b82, b85, b87, b89, b90, b91, b92, b95-batch-21)" --body "Assembled by B112 as rehearsed (A105 steps 2-13). Carries A90, the Cboe hold (held_since 2026-11-03), A84, Batches 18-21 with B105 and B108, the crypto keys, B87, B89, B90. Expected CI: green."
```
If B112 reports an aborted branch, the PR still goes ahead for what merged; the aborted branch becomes its own PR after a session resolves it (send me the needs-you).

**Step 14 — second deploy** (about 21:45 if CI cooperates; else first thing Wednesday 09:05). After it, no command: the Cboe hold takes effect at the 06:45 run (its log should show both Cboe readers HELD and fetching nothing); the feed summary prints at the next heartbeat.

**Step 15 — session A: paste `a109-chain-11-assembly-paste.txt`** (60–90 min; tell it chain-10 is on main). It does step 17a on a96 as ruled (merge main into a96, commit fbd43be8's change, prove `validate_price_sources`), then assembles a92 (with A92b), a93, a94, a96 (with A102, and A104's fallbacks if they landed today), a97, a95, a103, a98, b98, b99.

If it reports after 23:00, stop for the night: its PR is Wednesday's first move.

---

## Wednesday

**Step 16 — 09:05: open chain-11's PR**, read CI, merge, `git pull`.
```
gh pr create --base main --head chain-11 --title "chain-11: the builds (a92+A92b, a93, a94, a96+A102 with 17a, a97, a95, a103, a98, b98, b99)" --body "Assembled by A109 as rehearsed (A105 steps 14-21 with 17a, A106 22b-22c). Step 17a committed on a96 first. Expected CI: green; 166 code gates after chain-12."
```
**Step 17 — third deploy** (inside 09:05–15:40). Then the box steps, in this order, each inside a window:

- **a92 / A92b — the DTH-1 ledger's home (Drive, not the box):** keep `dth1-manual-ledger.csv` in `chester-cards/` with the header `date, time_et, instrument, side, entry, stop, target, contracts, risk_usd, exit, result_r, result_usd, status, rule_broken, notes` (the old spellings also read). Nothing to run. After the next nightly sweep its log should show `dth1 ok`, the letters and cards archive counts, the AAII weekly count, and `chester-x-digest folders: 1` — if it says 2, the Drive duplicate is still there.
- **b82 — AAII history**, on the box, only if the sweep's log shows the weekly folder arrived and the history is behind: `cd ~/chester-reports && .venv/bin/python -m altdata.sources.aaii --history` → prints the rows unioned, ending with the latest week.
- **b85 — DVOL backfill (optional, ~2 min):** `.venv/bin/python -m altdata.sources.deribit backfill --dry-run` (prints what it would write) then without `--dry-run`.
- **a94 — Gemini:** add `GEMINI_API_KEY=<the key>` to the box's `.env` yourself (never in chat), then `.venv/bin/python -m altdata.forecasters status` → `gemini-a` listed with its model id; the budgets stay zero until a paste sets them.
- **a98 — the paper executor, dry:** only with the paper Gateway running on 4002: `.venv/bin/python -m paper_exec status` → `enabled: false, dry_run: true` and the account id masked. Nothing more this week.
- **a93 — IBKR bars:** nothing until the subscription; **a96 — the FRED parallel run:** nothing until a paste moves a family; **A104's EDGAR dry runs:** done on the laptop on 2 Nov (one listed gap, ORCL's cost of goods sold; the writers stay off) — no box step.
- **Disk:** `df -h /` once; if use is above 75%, send me the number and `du -sh ~/backups ~/chester-data` — retention is the lever, not deletion by hand.

**Step 18 — session B: paste `b113-chain-12-docs-assembly-paste.txt`** (45–60 min; tell it chain-11 is on main).

**Step 19 — open chain-12's PR**, read CI, merge, `git pull`.
```
gh pr create --base main --head chain-12 --title "chain-12: docs tranche (b96+B104, b100+B107+B111, b102+B103, b109+B111 part 4)" --body "Assembled by B113 as rehearsed (A105 steps 22-25). Carries the Doctrine #2 pack through Part 12, the CI cache and docs-only filter, the chat-tasks register and the Reporting System paper's Appendix F, the names gate (list unset). Expected CI: the first run is the cache miss; green."
```
**Step 20 — fourth deploy** (the last of the week; inside a window). The seven unit-file comments B109 left are swept in this deploy's restart only if B114 has merged first — it hasn't, so they wait for the next deploy. No box step for chain-12 beyond the restart.

**Step 21 — session B: paste `b114-names-sweep-merged-main-paste.txt`** (30–45 min; tell it chain-12 is on main). Open its PR, read CI (green: the list is unset), merge. **Only then** set the repository secret: `gh secret set CHESTER_NAMES_DENYLIST` and type your first name when prompted (it never goes in a file); and on the box add `CHESTER_NAMES_DENYLIST=<name>` to `.env`. From the next push, `validate_names` scans for real.

**Step 22 — after everything is on main:** delete the two rehearsal branches (`git push origin --delete a99-merge-week-rehearsal a105-merge-week-rehearsal-2`), and tell me. I then write the library week: b88 refreshed to main with B110's Appendix C split, the XXX figures export (Tue/Wed after 17:20, read-only, before XXX's PR), and the seven library PRs in the ruled order (XXVII, phase-3a, XXXI, XXXII, E&I, XXIX, XXX).

---

## If something breaks

- **A chain's CI is red on a gate its notes don't predict:** don't merge; send me the run id and the job name. The rehearsal's tree was green, so a surprise means a branch moved after the rehearsal (A104's fallbacks are the one expected mover) or the queue hit a timeout (re-run the single job: `gh run rerun <run id> --failed`).
- **A session reports an aborted branch:** the chain merges without it; the branch gets its own refresh paste and PR.
- **A deploy ends non-zero:** send me its last 30 lines; nothing is rolled back by hand.
- **Running out of evening:** every step leaves main in a working state; the order resumes next window.

---

## Outcome

*For the session that closes the week to fill, one line per chain. Empty until then.*

| Chain | PR | Merge commit | CI run (result) | Deploy (time ET) |
|---|---|---|---|---|
| chain-9 | | | | |
| chain-8 | | | | |
| chain-10 | | | | |
| chain-11 | | | | |
| chain-12 | | | | |
| B114, the names sweep | | | | |
