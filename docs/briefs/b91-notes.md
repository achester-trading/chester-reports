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
