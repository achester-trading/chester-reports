# Change Orders and Pending Work — Consolidated as of Thursday 10 September 2026

*Everything ruled, written, or discovered since Audit #3 on Sunday 6 September, in one place. Four sections: rulings already made (no action needed except that the sessions read them), documents waiting to be uploaded, builds waiting to be pasted, and the two-track plan for running paper editing in parallel with the report buildout.*

---

## 1. Rulings already made (Sunday 6 – Wednesday 9 September)

| # | Ruling | Where recorded |
|---|---|---|
| R1 | Audit #3 accepted in full, with three exceptions to Section G: **29.5 privacy-coin theme kept**; **29.4 MOC absorption and 29.7 meme lifecycle: defer the build, start the forward-only logging now**; **Thailand becomes a standalone quarterly report** (spec written), removed from the pillars | Audit §G, Appendix; `thailand-monitor-spec.md` |
| R2 | The daily cadence: **07:00 anchor · 09:15 · 10:30 · 12:30 (alert only) · 15:00 · 16:45 anchor · 21:45 · Sunday 05:00 anchor · Sunday 21:45.** Three anchors always publish; conditionals publish on exception; the LLM is called only when a gate opens; the day is reconstructable from the two weekday anchors | Audit §I; Daily Cascade paper v2 Part 0 |
| R3 | **No word counts.** Zero budget for repetition, unlimited for insight, insight first | Audit §I |
| R4 | **The news and narrative scan is a first-class function** — ingested not fetched, a narrative register with graded stories, the 07:00 block where the LLM earns its cost | Audit §F, §H, §I; Daily Cascade v2 §0.4 |
| R5 | Phase 6 itemized at ~91 hours (6a–6m); grand total ~136 hours. Removed-items appendix logs seventeen retirements with revival conditions | Audit §N, Appendix |
| R6 | Execution order **Phase 0 → 1 → 3 → 2 → 4 → 5 → 6** — delivery first, the shadow grader immediately after, the state object once there is something to read it | Audit §N |
| R7 | Repository pass folded into the audit as §M.0; data-integrity and software-quality scores lowered honestly | Audit §A, §M.0 |
| R8 | **Phase 0 complete** — ten commits: DB in the backup + rclone off-box, WAL + busy_timeout, dual-write logging + heartbeat verdict, the revived-bug dedupe, three validators into CI, EnvironmentFile on units, render guards, Monthly `schedule:` block, dead shim deleted, `make validate` + fail-fast:false | Repo @ 930da6f and after |
| R9 | The store has two copies: Google Drive remote `gdrive:chester-backups`, first sweep 75 objects, copy-only semantics validated | VPS; validate_backup 23/0 |
| R10 | Watchdog: `After=` only (no `BindsTo=`, no `Wants=`); a deliberate stop must stick; the `is-active` guard is the mechanism | Repo 30bc12b |
| R11 | Architecture 32.3 amended: `reports/` is gitignored and swept by the off-box backup, not committed | Repo 30bc12b |
| R12 | The deploy key on the box is a recovery path, not a license; four Part 25 exceptions recorded in commit messages (two justified, one not, one justified) | TODO.md; commits 7faaf64, 2e58f87, b168dfe, 6520861 |
| R13 | Close report at 16:45 (was 16:30) — also separates it from the 16:30 IBKR sync | Repo f98fec4 |
| R14 | Monthly's `schedule:` block proven on 1 October before cron-job.org is deleted | Calendar |
| R15 | Daily Cascade paper rewritten as **v2.0** by transformation: Draft 1's 24 section chapters and dependency map retained verbatim; Part 0 (the v2 architecture) added; temporal chain, failure modes, and backlog rewritten | `daily-cascade-whitepaper.md/.html` |
| R16 | The close report gains a **narrative paragraph** gated by the numeral audit (D3); the 9 September paragraph is the coverage and style spec | `narrative-template-close.md` |

---

## 2. Documents waiting to be uploaded to the repository

*All in this chat's outputs. Upload replaces the same-named file. Nothing here has been uploaded since Sunday's batch.*

| File | Destination | Note |
|---|---|---|
| `daily-cascade-whitepaper.md` + `.html` | `docs/whitepapers/` | **v2.0 — replaces Draft 1** |
| `options-expression-whitepaper.md` + `.html` | `docs/whitepapers/` | Draft 1.4 — Chapter 8 rebuilt (12 structures, figures), Chapter 15 scenario matrix, Chapter 16 leverage |
| `base-rates-whitepaper.md` + `.html` | `docs/whitepapers/` | Draft 1.1 — executive summary and takeaway blocks |
| `international-equities-whitepaper.md` + `.html` | `docs/whitepapers/` | Draft 1.1 — record, correlation, China part, ten-year view |
| `positioning-and-flows-whitepaper.md` + `.html` | `docs/whitepapers/` | Draft 1.2 — Tables A–D and the owner→mandate→mechanism diagram |
| `evidence-inference-whitepaper.md` + `.html` | `docs/whitepapers/` | XXIII, new (HTML figures regenerated 10 Sep) |
| `earnings-whitepaper.md` + `.html` | `docs/whitepapers/` | XXIV, new |
| `white-paper-library-guide.md` + `.html` | `docs/` | Contents up front, executive summary at the back, format note that survives re-upload |
| `chester-reports-audit-3.md` + `.html` | `docs/` | Complete, with §M.0 and the appendix |
| `chester-reports-architecture-v3.md` | `docs/` | Parts 31 and 32 — **verify whether Sunday's upload included them**; if not, upload |
| `chester-reports-master-schedule.md` | `docs/` | Track D restated; Part 31 hours |
| `thailand-monitor-spec.md` | `docs/` | Standalone report spec, Phase 6m |
| `narrative-template-close.md` | `docs/` | Required before the D3 build |
| `structure-comparison-scenarios.csv` · `tools-structure_compare.py` | `tools/` (as `structure_compare.py`) and `docs/` | Part 31's recomputable comparison; the session places the tool |
| `whitepaper-figures.zip` | `docs/whitepapers/figures/<paper>/` | **39 SVG files — see §4** |
| ~~`daily-cascade-v2-amendment.md`~~ · ~~`remaining-papers-design.md`~~ | — | Superseded by the papers themselves; do not upload |

---

## 3. Builds waiting to be pasted

### Laptop — in this order, one session each

**L1 — Morning anchor + two small fixes** *(not yet built; Monday's session did not happen)*
> Pull. Three things, separate commits. (1) `make validate`: a validator that fails to execute — non-zero exit for any reason including a parse error — is a failed validator; prove it with a seeded syntax error. (2) Gateway intent as a file: a deliberate stop writes ~/state/gateway.stopped_by_operator; the watchdog restarts the Gateway in every other not-active case including IBKR's scheduled closedown; remove the marker on start; document the order-placement procedure as touch → stop → place → remove; validator cases for both branches. (3) Phase 1, the 07:00 morning anchor, data-only edition, on the D4c pattern: a 06:45 ET weekday timer fetching ES=F, NQ=F, ^VIX, DX-Y.NYB, ^TNX, JPY=X, ^N225, ^STOXX50E, ^FTSE, BTC-USD into the store as observations with fetched_at and available_at; a 07:00 ET render reading ONLY the store — the overnight block with level, change since prior US settlement, and a first-pass attribution (Tokyo, Europe so far, futures outside both); the prior close's exposure state; yesterday's pin verdicts; portfolio positions and NAV; every unsourced block absent with the reason. deliver(), archive before send with the archive path printed in the footer, state row, heartbeat treats a missed 07:00 as non-healthy, no LLM, CI no-prose check extended. Push.

**L2 — Close-report fixes from three days of reading it**
> Pull. Four fixes to the close report, separate commits. (1) Footer: print the archive path (known before send); drop the delivery field. (2) Portfolio block: beside each position print the decision id, fill price and commission from the execution record, invalidation level from the register, and distance to invalidation in points and percent; red when negative. (3) Add DEX to the FlashAlpha cross-check with a definitional audit — sign convention, which contracts, moneyness and vintage filters — and print DEX with a "definition unreconciled" flag until the audit closes; note that FlashAlpha's per-strike table showed a strike of 8000 on SPY, so it is not the reference. (4) A line in the Dealer's Hand paper (docs) recording the observed pattern: 0DTE inclusion pulls the flip toward spot; the settled ex-0DTE flip sits higher; the intraday flip governs the session and the settled one the overnight structure — with the Tuesday (2 bps) and Wednesday (0.35%) figures. Push.

**L3 — D3 numeral audit + the close narrative** *(requires `narrative-template-close.md` in docs/)*
> Build D3 and the close narrative together. (1) altdata/numeral_audit.py: given prose and a payload, extract every numeral from the prose (integers, decimals, percentages, $ amounts with k/mm/bn suffixes) and match each to a payload value within formatting tolerance; return pass/fail with the unmatched numerals. Validator with seeded failures: an invented number, a transposed digit, a stale prior-day value. (2) The close narrative block: a pinned Sonnet model, version recorded on the artifact, writes ONE paragraph over a structured payload — the SPY row with deltas vs prior session, each open position from the register with fill, invalidation level and distance in points and percent, the pin log tally to date, the FlashAlpha cross-check when a row exists. Coverage order and style per docs/narrative-template-close.md. (3) The audit gates the block: pass → prose ships above the tables; fail → data-only edition with a one-line "narrative withheld: numeral audit failed on N figures" and the failure logged. (4) The CI no-prose check applies to the payload and render modules only, and asserts the narrative module cannot be imported by the payload path. Push.

**L4 — Papers as a buildable artifact** — **DONE, 19 September 2026, not as written.** *(enabled the parallel track; see §4)*
> Add docs/whitepapers/figures/<paper>/ from the uploaded zip. Build tools/render_paper.py: Markdown → HTML using the house stylesheet, replacing each figure caption of the form `*[Figure X — …; rendered in the HTML edition]*` or `*[Figure set X — …]*` with the matching SVG from figures/<paper>/ in order of appearance; the mapping is by ordinal within the paper. Add a CI step that regenerates every .html from its .md and fails on a diff, so a stale HTML fails the build. Commit the .html editions. Update CLAUDE.md: HTML is now generated, not uploaded — edit the .md, run the renderer.

> **Closed as already delivered.** Every part of this order exists, in a better
> form, from the `library-figures` work of 6–7 September (`ce8fa65` lifted the
> figures out of the stale HTML; `0659ca4` retired the HTML-canonical rule in
> all three places). What differs from the order as written:
>
> - **Figures live at `docs/figures/<slug>/fig-NN.svg`**, not
>   `docs/whitepapers/figures/<paper>/`, each directory carrying an `index.md`
>   mapping number → caption → file. 39 figures became committed files and the
>   papers reference them with ordinary Markdown image links, so the
>   placeholder captions this order wanted a renderer to substitute are gone
>   from the `.md` entirely — there is nothing left to substitute.
> - **The renderer is `tools/build_paper_html.py`** (`make html`), not
>   `tools/render_paper.py`. It embeds the figures inline and stamps each
>   edition with the SHA-256 of the `.md` it was built from.
> - **The stale-HTML gate is a hash, not a diff.** `check_library.py`
>   check_10 recomputes that stamp, which is strictly better than regenerating
>   and diffing: git does not record mtimes, so a fresh clone's timestamps are
>   noise. It *warned* on a stale edition until 19 September and now **fails**,
>   which is the one respect in which this order was not yet satisfied and the
>   only code this closure required.
> - **`CLAUDE.md` already says HTML is generated, not uploaded**, and carries
>   the upload discipline the retired rule kept failing to teach.
>
> The 19 September docs batch was assembled from a local copy predating all of
> this and would have reverted it: its papers still carry the
> `*[Figure N — rendered in the HTML edition]*` placeholders and its guide
> restores the retired rule. Only its five genuinely new files were taken. See
> §2 — treat this order as the reason that batch is the last one of its kind.


**L5 — P2-1 package structure** *(own session, after the above)*
> tools/__init__.py; import as tools.x; delete the 34 sys.path inserts; altdata stops importing upward from tools; one altdata/secrets.py for the .env parser and redact(); one altdata/selection.py for the newest-file rule. Prove nothing changes with `make validate` before and after.

### VPS — after each laptop push
> Pull, redeploy every unit from deploy/systemd/, daemon-reload, drift check clean, enable any new timers, confirm the roster.

### Calendar
- **Tonight, 16:45:** SPY settled close vs 760 decides decision fae90045. Below → exit Friday open, `decide.py set-status fae90045 invalidated`.
- **Sunday 05:00** — no Weekly yet; the first is Phase 4.
- **1 October 06:00 UTC** — the Monthly fires from GitHub; delete cron-job.org that day if it does.

---

## 4. The two parallel tracks

**Track A — Report buildout** (laptop sessions L1 → L2 → L3 → L5; VPS deploys between). Phase 1 completes with L1 and L3; the shadow grader (Phase 3) follows; the state object (Phase 2) after.

**Track B — White paper audit and editing.** The blocker has been that the HTML editions — canonical for reading, figures included — exist only as files uploaded from this chat, so every edit had to round-trip here and every re-upload risked erasing something. **L4 removes the blocker:** the 39 figures become committed SVG files, the HTML becomes a generated artifact, and editing a paper means editing its `.md` in the repository and letting the renderer and CI produce the `.html`. From then on:

- Paper edits happen in the `.md`, on the laptop, by a session or by hand. No uploads.
- Figures are files; a paper that needs a new figure gets an SVG committed beside the others.
- The guide's format note stops mattering, because nothing overwrites anything.
- This chat remains useful for *drafting* new content, delivered as `.md` to be committed — not as HTML to be uploaded.

**Order of operations for the next session:** upload §2 in one batch → paste L1 → VPS deploy → paste L4 (short, unblocks Track B) → paste L2 → paste L3 → VPS deploy. From L4 onward, Track B runs whenever you have paper time, independent of Track A.
