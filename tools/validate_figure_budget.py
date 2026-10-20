"""
Validation gate for the figure budget at the frame (T3.4, 10 Oct 2026).

Three dry runs cited 9 to 21 figures in the parent sections and the FOMC and
liquidity blocks against a cap of 8, through three retries. The frame now offers
no more figures than the paragraph may cite. FIXTURES, one per cadence, written
here -- no store, no network, no model:

  A  PARENTS, every cadence. A parent section's frame carries at most the
     cadence's `paragraph_figures` (read from config, never a literal), its
     largest moves first (relative to their level), each in the display form its
     table prints; every other series under `also_moved` by name only, with no
     number; it says the blocks beneath carry those numbers; the prompt tells
     the writer so. A listed section with no sub-sections is not a parent.
  B  BLOCKS (the Monthly). A prediction-market FOMC block and a liquidity block
     with more rows than the cap fit: the top rows by absolute change, the rest
     by name only; a small block keeps its table.
  C  SUMMARIES (the Monthly). Each summary frame carries the section's prose with
     its figures masked and "figures you may cite: these three" -- the top three
     by the parent's ordering; the read takes them across the edition; the audit
     scope is unchanged (the section's own slice, and for the read every
     section's).
  D  ORDINALS ONLY. No frame carries a raw percentile: a percentile key survives
     only as its `_ordinal`.
  E  THE RETRIES STAY. Three attempts, and the explicit retry line.
  G  THE TAPE'S LEVELS (T3.4b). The close's and the Weekly's tape frame keeps
     at most three levels -- the pin level on an expiry session, the 50-day,
     the dealer flip, the nearest wall -- each as listed with its status,
     counted inside the cap with the moves; the Monthly's tape is unchanged.
  F  THE CAP IS CONFIG. Changing a cadence's `paragraph_figures` changes the
     frame's budget.
  H  T3.4c (W-1.1 item 1.0, ruled 11 Oct 2026). On the 9 Oct fixture, relative
     to level ranks IG OAS -4 bp above CCC OAS +37 bp; the z of the week's change
     against the series' own trailing-year changes ranks CCC first. A weekly
     series falls back to relative-to-level and the frame says so. The Weekly's
     Plumbing, Positioning and What's priced take a cap of 8 from config, one
     figure for every sub-block that moved; the daily close keeps 6. The rest
     sit under "In the tables (do not enumerate)" and the frame bans the filler.
  I  T3.4c: the read, Mechanics, What doesn't fit and Ahead each get a budgeted
     frame -- a move defined for each, the 18 CPI contracts as families of one
     figure -- and the comparison vocabulary is in the read's and book's frames.

    python tools/validate_figure_budget.py
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from daily_cascade import cadence as cadence_mod  # noqa: E402
from daily_cascade import figure_budget as fb  # noqa: E402
from daily_cascade import readability  # noqa: E402
from daily_cascade import stack_prose as sp  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78


def ok(m: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {m}")


def bad(m: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {m}")


def check(c: bool, m: str) -> None:
    (ok if c else bad)(m)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def plumbing_fixture() -> dict:
    """A parent with three buckets and twenty series in mixed units, the shape of
    the dry runs' Plumbing (16 figures cited against 8)."""
    cols = ["Series", "Level or actual", "Month or prior", "As of"]
    yields = [["2-year", "3.80%", "−10 bp", "2026-09-30"],
              ["10-year", "4.25%", "+25 bp", "2026-09-30"],
              ["30-year", "4.60%", "+10 bp", "2026-09-30"],
              ["2s10s", "45 bp", "+35 bp", "2026-09-30"],
              ["High-yield OAS", "3.20%", "+20 bp", "2026-09-30"],
              ["Investment-grade OAS", "0.90%", "+2 bp", "2026-09-30"]]
    liq = [["Net liquidity (Fed balance sheet less TGA and RRP)", "$5.80tn", "−$100bn", "2026-09-30"],
           ["Bank reserves", "$2.95tn", "+$37bn", "2026-09-30"],
           ["RRP", "$0.21tn", "−$11bn", "2026-09-30"],
           ["SOFR", "4.33%", "+3 bp", "2026-09-30"],
           ["IORB", "4.40%", "0 bp", "2026-09-30"],
           ["SOFR less IORB (funding pressure when above zero)", "-7 bp", "+3 bp", "2026-09-30"]]
    metals = [["Copper, front future ($/lb; a growth gauge)", "$4.600", "+2.22%", "2026-09-30"],
              ["Gold, front future", "$2,650.0", "+6.10%", "2026-09-30"],
              ["Silver", "$31.20", "+9.40%", "2026-09-30"],
              ["Gold over copper (rises when growth fears rise)", "576", "+3.80%", "2026-09-30"],
              ["Platinum", "$980", "—", "—"]]
    glob = [["USD/JPY (yen per dollar)", "148.00", "+2.07%", "2026-09-30"],
            ["Bund 10-year", "2.40%", "+12 bp", "2026-09-30"],
            ["JGB 10-year", "1.10%", "+8 bp", "2026-09-30"]]
    subs = [{"title": t, "table": {"columns": cols, "rows": r},
             "data": {"level_percentile_5y": 97.6, "level_percentile_5y_ordinal": "98th"},
             "prose": {"words": "60 to 100"}, "phase": f"block:plumbing:{k}"}
            for t, r, k in (("Yields & spreads", yields, "yields"), ("Liquidity", liq, "liquidity"),
                            ("Metals", metals, "metals"), ("Global rates", glob, "global"))]
    return {"id": "plumbing", "title": "Plumbing & rates", "depth": "deep",
            "items": [{"key": "plumb:x", "text": "10-year 4.25%, +25 bp on the month.",
                       "priority": 1}],
            "table": None, "subsections": subs,
            "data": {"series": [{"series": "10-year", "level_percentile_5y": 99.2,
                                 "level_percentile_5y_ordinal": "99th"}]}}


def tape_fixture() -> dict:
    cols = ["Market", "Close, 2026-09-30", "Move", "Year to date", "Level, 5y percentile"]
    rows = [["S&P 500", "5,250.00", "+5.00%", "+12.2%", "100th"],
            ["Nasdaq 100 (QQQ)", "490.00", "+2.08%", "+15.0%", "99th"],
            ["Russell 2000 (IWM)", "102.00", "+2.00%", "-1.9%", "40th"],
            ["2-year Treasury", "3.80%", "−10 bp", "—", "61st"],
            ["10-year Treasury", "4.25%", "+25 bp", "—", "88th"],
            ["High-yield OAS", "3.20%", "+20 bp", "—", "12th"],
            ["Dollar index", "104.20", "+1.10%", "+2.0%", "70th"],
            ["Gold", "2,650.00", "+6.10%", "+28.0%", "100th"],
            ["WTI crude", "71.00", "−8.00%", "-4.0%", "30th"],
            ["Bitcoin", "64,000", "+11.00%", "+48.0%", "90th"]]
    ytd = [[i + 1, n, p, "+1.0%", y, "—"] for i, (n, p, y) in enumerate(
        [("REITs", "XLRE", "+12.50%"), ("U.S. large cap", "SPY", "+12.22%"),
         ("Cash", "3-month T-bill", "+3.08%")])]
    return {"id": "tape", "title": "The tape", "depth": "light", "items": [],
            "table": {"columns": cols, "rows": rows},
            "subsections": [{"title": "Across assets, year to date",
                             "table": {"columns": ["Rank", "Asset class", "Proxy", "The month",
                                                   "Year to date", "Twelve months"],
                                       "rows": ytd}}],
            "data": {"moves": [{"market": "S&P 500", "level_percentile_5y": 99.96,
                                "level_percentile_5y_ordinal": "100th"}],
                     # The level list's flat rows and statuses (altdata/levels.py).
                     "levels": [{"symbol": "SPY", "name": "SPY", "last": 5250.0,
                                 "ma_20d": 5190.4, "ma_50d": 5100.5, "ma_200d": 4900.2,
                                 "gamma_flip": 5180.0, "call_wall": 5300.0,
                                 "put_wall": 5000.0, "max_pain": 5225.0}],
                     "level_status": {"spy": [
                         {"label": "50-day average", "value": 5100.5, "status": "held"},
                         {"label": "gamma flip", "value": 5180.0, "status": "held"},
                         {"label": "call wall", "value": 5300.0, "status": "untested"},
                         {"label": "max pain", "value": 5225.0, "status": None}]}}}


def pm_block_fixture() -> tuple[dict, dict]:
    """The FOMC prediction-market block: twelve contracts (21 figures in the dry
    run), each with two venues and a change in points."""
    cols = ["Item", "Kalshi", "Polymarket", "Week change", "Note"]
    changes = [+1.0, -12.0, +4.0, +0.5, -3.0, +22.0, -0.2, +7.0, -9.0, +2.0, +15.0, -1.5]
    rows, contracts = [], []
    for i, c in enumerate(changes):
        name = f"FOMC December: outcome {chr(65 + i)}"
        signed = f"{c:+.1f} pts".replace("-", "−")
        rows.append([name, f"{40 + i}%", f"{41 + i}%", signed, ""])
        contracts.append({"contract": name, "kalshi": 40 + i, "change": c,
                          "change_signed": signed, "kalshi_display": f"{40 + i}%"})
    ss = {"title": "Prediction markets: the FOMC", "phase": "block:priced:pm_fomc",
          "prose": {"words": "60 to 100"}, "table": {"columns": cols, "rows": rows},
          "data": {"contracts": contracts}}
    sec = {"id": "priced", "title": "What's priced", "depth": "deep", "items": [],
           "table": None, "subsections": [ss]}
    return sec, ss


def ed_of(sections: list, cadence: str) -> dict:
    return {"session": "2026-09-30", "month": "September 2026", "cadence": cadence,
            "sections": sections}


def figures_in(frame) -> set:
    found = set()

    def walk(o, key=None):
        if key in fb.NAME_KEYS:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)
        elif isinstance(o, str):
            found.update(readability.figures(o))
    walk(frame)
    return found


def raw_percentile_keys(o) -> list:
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            if "percentile" in str(k).lower() and not str(k).endswith("_ordinal"):
                out.append(k)
            out += raw_percentile_keys(v)
    elif isinstance(o, list):
        for v in o:
            out += raw_percentile_keys(v)
    return out


# ---------------------------------------------------------------------------
def group_a() -> dict:
    print(f"\n{LINE}\nA. PARENT SECTIONS, EVERY CADENCE\n{LINE}")
    counts = {}
    for cad_name in cadence_mod.NAMES:
        cad = cadence_mod.get(cad_name)
        check(set(cad["figure_budget_parents"]) == {"tape", "plumbing", "positioning",
                                                    "priced", "slow"},
              f"{cad_name}: the parents are config's five")
        for s in (plumbing_fixture(), tape_fixture()):
            # The section's cap (T3.4c): its override, else the cadence's.
            cap = sp.section_figure_cap(s["id"], cad_name)
            ed = ed_of([s], cad_name)
            frame = sp.section_slice(s, ed, cad_name)
            n = fb.quantified_figures(frame)
            counts[(cad_name, s["id"])] = n
            got = frame.get("figures_you_may_cite") or []
            check(0 < n <= cap and len(got) <= cap,
                  f"{cad_name} {s['id']}: the frame carries {n} figures, the cap is {cap}")
            cells = {str(c) for m in fb.section_moves(s) for c in (m.get("change"),
                                                                    m.get("level")) if c}
            named = frame[fb.IN_TABLES]
            check(set(named) <= {m["name"] for m in fb.section_moves(s)}
                  and not any(c in x for x in named for c in cells),
                  f"{cad_name} {s['id']}: 'In the tables (do not enumerate)' is names "
                  f"only ({len(named)})")
            allnames = {m["name"] for m in fb.section_moves(s)}
            check({g["series"] for g in got} | set(named) == allnames,
                  f"{cad_name} {s['id']}: every series the section covers is either "
                  f"quantified or named")
            check("table" not in frame and "subsections" not in frame and "data" not in frame
                  and "items" not in frame,
                  f"{cad_name} {s['id']}: no table, block, item or data numbers reach the frame")
            check("tables beneath this section print" in frame["blocks_carry"]
                  and "never write that they also moved" in frame["blocks_carry"],
                  f"{cad_name} {s['id']}: the frame says the tables beneath carry the numbers")
            prompt = sp.section_prompt(s, cad_name)
            check("figures_you_may_cite" in prompt
                  and "do not list them and do not quantify them" in prompt
                  and "In the tables (do not enumerate)" in prompt
                  and f"at most {cadence_mod.figure_word(cap).lower()}" in prompt,
                  f"{cad_name} {s['id']}: the prompt names the frame's figures and the cap")
    # Largest first, relative to level.
    s = tape_fixture()
    # On the Monthly: its tape carries no levels (T3.4b), so all its cap is moves.
    frame = sp.section_slice(s, ed_of([s], "monthly"), "monthly")
    order = [g["series"] for g in frame["figures_you_may_cite"]]
    check(order[:5] == ["Bitcoin", "WTI crude", "High-yield OAS", "Gold", "10-year Treasury"],
          f"ranked largest first relative to the level: Bitcoin +11%, WTI −8%, high yield "
          f"+20 bp on 3.20% (6.3%), gold +6.1%, the 10-year +25 bp on 4.25% (5.9%) "
          f"({order[:5]})")
    check(frame["figures_you_may_cite"][0]["change"] == "+11.00%",
          "each figure is the display form its table prints")
    slow = {"id": "slow", "title": "Slow layers", "depth": "deep", "items": [], "table": None,
            "subsections": [{"title": "Valuation", "table": {
                "columns": ["Series", "Latest (data as of)", "Long-run average (window)",
                            "Percentile (window)"],
                "rows": [[f"Valuation series {chr(65 + i)}", f"{20 + i}.5 (2026-09-01)",
                          "16.0 (full history)", "90th (5 years, n=59)"] for i in range(12)]}}]}
    sf = sp.section_slice(slow, ed_of([slow], "monthly"), "monthly")
    check(len(sf["figures_you_may_cite"]) == cadence_mod.figure_cap(cadence_mod.get("monthly"))
          and all("level" in f and "change" not in f for f in sf["figures_you_may_cite"])
          and len(sf[fb.IN_TABLES]) == 4,
          "a level table (the slow layers' valuation) offers its levels up to the cap, "
          "the rest by name")
    nonparent = {**tape_fixture(), "subsections": []}
    check(sp.section_slice(nonparent, ed_of([nonparent], "daily"), "daily").get("table"),
          "a listed section with no sub-sections is not a parent: it keeps its slice")
    other = {**plumbing_fixture(), "id": "narratives", "title": "Narratives"}
    check("table" in sp.section_slice(other, ed_of([other], "weekly"), "weekly")
          or "subsections" in sp.section_slice(other, ed_of([other], "weekly"), "weekly"),
          "a section neither a parent nor budgeted (T3.4c) keeps its slice")
    return counts


def group_b() -> None:
    print(f"\n{LINE}\nB. BLOCKS (the Monthly)\n{LINE}")
    from monthly_macro import prose
    cap = prose.figure_cap()
    sec, ss = pm_block_fixture()
    ed = ed_of([sec], "monthly")
    frame = prose.block_slice(sec, ss, ed)
    n = fb.quantified_figures(frame)
    kept = [r["series"] for r in frame["figures_you_may_cite"]]
    named = frame[fb.IN_TABLES]
    check(n <= cap, f"the FOMC prediction-market block: {n} figures, cap {cap} "
                    f"({len(ss['table']['rows'])} contracts)")
    check(kept[:2] == ["FOMC December: outcome F", "FOMC December: outcome K"],
          f"its rows by absolute change: +22, +15 first ({kept})")
    check(set(kept) | set(named) == {r[0] for r in ss["table"]["rows"]}
          and not set(kept) & set(named),
          f"the rest by name only, under '{fb.IN_TABLES}' ({len(named)})")
    check(all("change_signed" in r and "change" not in r
              for r in frame["figures_you_may_cite"]),
          "a kept row carries its data's signed form, never the raw change")
    pl = plumbing_fixture()
    liq = next(x for x in pl["subsections"] if x["title"] == "Liquidity")
    lf = prose.block_slice(pl, liq, ed_of([pl], "monthly"))
    check(fb.quantified_figures(lf) <= cap,
          f"the liquidity block: {fb.quantified_figures(lf)} figures, cap {cap}")
    check(lf.get("figures_you_may_cite")
          and lf["figures_you_may_cite"][0]["series"].startswith("Net liquidity"),
          "its largest absolute change first (net liquidity, −$100bn)")
    small = next(x for x in pl["subsections"] if x["title"] == "Global rates")
    sf = prose.block_slice(pl, small, ed_of([pl], "monthly"))
    check(sf.get("table") and fb.quantified_figures(sf) <= cap,
          "a block inside the cap keeps its table")
    check(not raw_percentile_keys(sf) and "98th" in str(sf),
          "and presents its percentile as the ordinal only")


def group_c() -> None:
    print(f"\n{LINE}\nC. SUMMARY PARAGRAPHS (the Monthly)\n{LINE}")
    from monthly_macro import prose
    n = prose.summary_figures()
    tape = tape_fixture()
    tape["claim"] = "Equities rose 5.00% and gold 6.10% on the month."
    tape["paragraphs"] = ["Bitcoin led with +11.00% and WTI fell 8.00%; the 10-year rose 25 bp "
                          "to 4.25% over the 10-year's 30-day range."]
    pl = plumbing_fixture()
    pl["claim"] = "The curve steepened 35 bp."
    read = {"id": "read", "title": "The read", "depth": "deep", "items": [],
            "claim": "The month was a 5.00% rally.", "paragraphs": ["It ran 4 weeks."],
            "subsections": [], "table": None}
    ed = ed_of([read, tape, pl], "monthly")
    plan = {x["key"]: x for x in prose.summary_plan(ed)}
    for key, x in plan.items():
        q = fb.quantified_figures(x["slice"])
        cite = x["slice"].get("figures_you_may_cite") or []
        check(q <= n and len(cite) <= n,
              f"{key}: the frame carries {q} figures, the summary cap is {n}")
        check("FIGURES YOU MAY CITE: these" in x["system"],
              f"{key}: the frame says which figures it may cite")
    t = plan["summary:tape"]
    check([c["series"] for c in t["slice"]["figures_you_may_cite"]]
          == ["Bitcoin", "WTI crude", "High-yield OAS"],
          "the tape's three are its top three by the parent's ordering")
    check("[figure]" in t["slice"]["claim"] and "5.00%" not in str(t["slice"])
          and "10-year's 30-day" in t["slice"]["paragraphs"][0],
          "the section's prose is carried with its figures masked, names kept")
    check(t["audit_extra"]["section_summarised"]["paragraphs"] == tape["paragraphs"],
          "the audit scope is unchanged: the section's own printed slice")
    r = plan["summary:read"]
    check(len(r["slice"]["figures_you_may_cite"]) == n
          and {"The tape", "Plumbing & rates"} <= {x["section"] for x in
                                                   r["audit_extra"]["sections_summarised"]},
          "the read cites the edition's top three, and is audited against every section")


def group_d() -> None:
    print(f"\n{LINE}\nD. ORDINALS ONLY\n{LINE}")
    from monthly_macro import prose
    pl, tape = plumbing_fixture(), tape_fixture()
    sec, ss = pm_block_fixture()
    ed = ed_of([tape, pl, sec], "monthly")
    frames = [x["slice"] for x in prose.stack_plan(ed) + prose.block_plan(ed)
              + prose.summary_plan(ed)]
    for c in ("daily", "weekly"):
        frames += [sp.section_slice(s, ed_of([s], c), c) for s in (pl, tape)]
    bad_keys = [k for f in frames for k in raw_percentile_keys(f)]
    check(frames and not bad_keys,
          f"no frame of {len(frames)} carries a raw percentile ({bad_keys[:3]})")


def group_e() -> None:
    print(f"\n{LINE}\nE. THE RETRIES STAY\n{LINE}")
    from monthly_macro import prose
    check(prose.ATTEMPTS == 2, "the draft and one revision for every Monthly "
          "section (the stack's retry, the a47 chain; T3.3's three retired)")
    check(prose.CAP_RETRY == "your draft cited {n} figures; the cap is {m}; remove "
                             "figures, keep the reading",
          "the explicit retry line is unchanged")


def group_g() -> None:
    print(f"\n{LINE}\nG. THE TAPE KEEPS ITS LEVELS (T3.4b): the close and the Weekly\n{LINE}")
    for cad_name in ("daily", "weekly"):
        cap = cadence_mod.figure_cap(cadence_mod.get(cad_name))
        s = tape_fixture()
        ed = {**ed_of([s], cad_name), "session": "2026-10-07"}       # a Wednesday
        f = sp.section_slice(s, ed, cad_name)
        lv = f.get("levels_you_may_cite") or []
        moves = f.get("figures_you_may_cite") or []
        check([x["level"] for x in lv] == ["50-day average", "gamma flip", "call wall"]
              and [x.get("ma_50d") or x.get("gamma_flip") or x.get("call_wall") for x in lv]
              == [5100.5, 5180.0, 5300.0],
              f"{cad_name}: the 50-day, the flip and the nearest wall, exactly as listed "
              f"({[(x['level'], x.get('status')) for x in lv]})")
        check(lv[0]["status"] == "held" and lv[2]["status"] == "untested",
              f"{cad_name}: each level carries its status for the held/broke rule")
        check(len(lv) <= 3 and len(lv) + len(moves) <= cap
              and fb.quantified_figures(f) <= cap,
              f"{cad_name}: {len(lv)} levels and {len(moves)} moves, "
              f"{fb.quantified_figures(f)} figures inside the cap of {cap}")
        exp = sp.section_slice(s, {**ed, "session": "2026-10-16"}, cad_name)  # 3rd Friday
        el = exp.get("levels_you_may_cite") or []
        check(len(el) == 3 and "pin level" in el[0]["level"] and el[0].get("max_pain") == 5225.0,
              f"{cad_name}: on an expiry session the pin level comes first, still three")
        prompt = sp.section_prompt(s, cad_name)
        check("levels_you_may_cite" in prompt and "count inside the same cap" in prompt,
              f"{cad_name}: the prompt offers the levels and counts them in the cap")
    s = tape_fixture()
    mf = sp.section_slice(s, ed_of([s], "monthly"), "monthly")
    check("levels_you_may_cite" not in mf
          and len(mf["figures_you_may_cite"]) == cadence_mod.figure_cap(cadence_mod.get("monthly")),
          "the Monthly's tape is unchanged: no levels, the cap's worth of moves")
    check("levels_you_may_cite" not in sp.section_slice(plumbing_fixture(),
                                                        ed_of([plumbing_fixture()], "weekly"),
                                                        "weekly"),
          "only the tape carries levels")


def group_f() -> None:
    print(f"\n{LINE}\nF. THE CAP IS CONFIG\n{LINE}")
    from altdata import bars as bars_mod
    cfg = copy.deepcopy(bars_mod.load_config())
    cfg["cadences"]["weekly"]["paragraph_figures"] = 3
    cad = cadence_mod.get("weekly", cfg)
    s = tape_fixture()
    frame = fb.parent_frame(s, ed_of([s], "weekly"), cadence_mod.figure_cap(cad), "week")
    check(fb.quantified_figures(frame) == 3,
          "a cadence's paragraph_figures of 3 gives a three-figure frame")
    src = (REPO / "daily_cascade" / "figure_budget.py").read_text(encoding="utf-8")
    check("paragraph_figures" in src and not any(f"cap = {n}" in src or f"cap={n}" in src
                                                 for n in (3, 6, 8)),
          "the module carries no literal cap")


# ---------------------------------------------------------------------------
# T3.4c -- THE SECOND PASS (W-1.1 item 1.0, ruled 11 Oct 2026)
# ---------------------------------------------------------------------------
class FakeStore:
    """The store's two readers the move annotation calls, over fixed series."""

    def __init__(self, series: dict):
        self.series = series

    def as_of(self, key, cutoff=None, instrument=None):
        return [{"observed_at": d, "value_num": v}
                for d, v in self.series.get((key, instrument), [])
                if cutoff is None or d <= str(cutoff)[:10]]


def _walk(seed: int, start: float, daily_sd: float, end_day: str, days: int,
          last_week_change: float, weekly: bool = False) -> list:
    """A deterministic random walk ending on `end_day`, its last week's change
    forced to `last_week_change` (in the level's own unit)."""
    import datetime as dt
    import random
    rnd = random.Random(seed)
    end = dt.date.fromisoformat(end_day)
    dates = []
    d = end - dt.timedelta(days=days)
    while d <= end:
        if (d.weekday() == 4) if weekly else (d.weekday() < 5):
            dates.append(d.isoformat())
        d += dt.timedelta(days=1)
    v, out = start, []
    for day in dates:
        v += rnd.gauss(0, daily_sd)
        out.append([day, v])
    week_ago = (end - dt.timedelta(days=7)).isoformat()
    base = [v for day, v in out if day <= week_ago][-1]
    out[-1][1] = base + last_week_change
    return [tuple(x) for x in out]


DAY = "2026-10-09"


def oct9_plumbing() -> tuple[dict, FakeStore]:
    """The 9 Oct Weekly's Plumbing, as its table printed it, and a store whose
    histories give each row the spread of weekly changes a real series has: IG
    OAS moves a few bp a week, CCC OAS tens of bp."""
    cols = ["Series", "Level or actual", "Week or prior", "As of"]
    rows = [["2-year", "3.580%", "+3 bp", DAY], ["10-year", "4.120%", "+6 bp", DAY],
            ["High-yield OAS", "3.05%", "+12 bp", DAY],
            ["Net liquidity (Fed balance sheet less TGA and RRP)", "$5.84tn", "−$45bn",
             "2026-10-08"],
            ["Bank reserves (H.4.1)", "$2.95tn", "−$30bn", "2026-10-08"],
            ["Investment-grade OAS", "0.80%", "−4 bp", DAY],
            ["CCC OAS", "9.60%", "+37 bp", DAY],
            ["Copper, front future ($/lb; a growth gauge)", "$4.610", "+1.20%", DAY]]
    fx = {"title": "Global rates and FX", "table": {
        "columns": ["Series", "Level", "Week", "As of"],
        "rows": [["USD/JPY (yen per dollar)", "148.20", "+0.80%", DAY]]}}
    s = {"id": "plumbing", "title": "Plumbing & rates", "depth": "medium", "items": [],
         "table": {"columns": cols, "rows": rows}, "subsections": [fx], "data": {}}
    st = FakeStore({
        ("fred.yield_2y", None): _walk(1, 3.6, 0.04, DAY, 420, 0.03),
        ("fred.yield_10y", None): _walk(2, 4.1, 0.05, DAY, 420, 0.06),
        ("fred.hy_oas", None): _walk(3, 3.0, 0.03, DAY, 420, 0.12),
        ("calc.net_liquidity", None): _walk(4, 5.9e12, 3e10, DAY, 420, -4.5e10, True),
        ("fred.bank_reserves", None): _walk(5, 2.95e6, 2e4, DAY, 420, -3e4, True),
        ("fred.ig_oas", None): _walk(6, 0.80, 0.012, DAY, 420, -0.04),
        ("fred.ccc_oas", None): _walk(7, 9.2, 0.05, DAY, 420, 0.37),
        ("yfinance.mkt_copper_front", None): _walk(8, 4.5, 0.06, DAY, 420, 0.055),
        ("yfinance.mkt_usdjpy", None): _walk(9, 147.0, 0.7, DAY, 420, 1.18)})
    return s, st


def oct9_positioning() -> tuple[dict, FakeStore]:
    """Positioning with six sectors moving hard and the CFTC contracts at
    extremes: the 9 Oct frame spent all six figures on the sectors."""
    from altdata import labels
    secs = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU"]
    moves = ["+4.10%", "−3.20%", "+5.60%", "−2.90%", "+3.40%", "−3.80%", "+0.20%", "+0.10%"]
    srows = [[labels.sector(t), m, "—", "—"] for t, m in zip(secs, moves)]
    cftc = [["S&P 500 futures", "-250,000", "−42,984", "-2.6", "2026-10-06"],
            ["10-year note futures", "-900,000", "+77,476", "-2.9", "2026-10-06"]]
    s = {"id": "positioning", "title": "Positioning & flows", "depth": "deep", "items": [],
         "table": None, "data": {},
         "subsections": [
             {"title": "Sector rotation and leadership",
              "table": {"columns": ["Sector or pair", "Week", "One month", "Three months"],
                        "rows": srows}},
             {"title": "Speculative positioning (CFTC)",
              "table": {"columns": ["Contract", "Net speculative contracts", "Change",
                                    "z, two years", "As of"], "rows": cftc}},
             {"title": "Short interest",
              "table": {"columns": ["Series", "Level", "Change", "Settlement"],
                        "rows": [["SPY days to cover", "1.40", "+0.02", "2026-09-30"]]}}]}
    series = {}
    for n, (t, m) in enumerate(zip(secs, moves)):
        pct = float(m.replace("−", "-").rstrip("%"))
        series[(f"yfinance.mkt_{t.lower()}", None)] = _walk(20 + n, 100.0, 1.4, DAY, 420,
                                                           pct)
    for n, (inst, chg) in enumerate((("SP500", -42984), ("UST10Y", 77476))):
        series[("cftc.noncomm_net", inst)] = _walk(40 + n, -200000, 15000, DAY, 420,
                                                   chg, True)
    return s, FakeStore(series)


def group_h() -> None:
    from daily_cascade import weekly_stack as ws
    print(f"\n{LINE}\nH. T3.4c: RANKED BY z, ALLOCATED BY SUB-BLOCK, NO FILLER\n{LINE}")
    s, st = oct9_plumbing()
    # Before: relative to level -- IG's -4 bp on 0.80% (5.0%) outranks CCC's +37 bp
    # on 9.60% (3.9%), which is how Plumbing read "no stress".
    rel = [m["name"] for m in fb.ranked(fb.section_moves(s), "relative")]
    check(rel.index("Investment-grade OAS") < rel.index("CCC OAS"),
          "the bug, reproduced: relative to level ranks IG OAS -4 bp above CCC OAS +37 bp")
    ws.annotate_moves({"plumbing": s}, st, DAY + "T21:00:00+00:00")
    z = s["data"]["_move_z"]
    check(z["ccc oas"]["basis"] == "z" and z["investment-grade oas"]["basis"] == "z"
          and z["ccc oas"]["n"] >= 60,
          f"CCC and IG carry a z over {z['ccc oas']['n']} trailing-year weekly changes")
    order = [m["name"] for m in fb.ranked(fb.section_moves(s), "z")]
    check(order.index("CCC OAS") < order.index("Investment-grade OAS"),
          f"by z, CCC OAS +37 bp (z {z['ccc oas']['z']:+.1f}) outranks IG OAS -4 bp "
          f"(z {z['investment-grade oas']['z']:+.1f})")
    check(order[0] == "CCC OAS", f"and leads Plumbing ({order[:3]})")
    check(z["bank reserves (h.4.1)"]["basis"] == "relative"
          and "fewer than 60" in z["bank reserves (h.4.1)"]["reason"],
          "a weekly series (52 changes a year) falls back to relative-to-level, and says why")
    cap, per_block = fb.section_cap("plumbing", cadence_mod.get("weekly"))
    check(cap == 8 and per_block, "the Weekly's Plumbing: a cap of 8, one figure per "
                                  "sub-block first (config figure_budget_sections)")
    check(fb.section_cap("plumbing", cadence_mod.get("daily")) == (6, False),
          "the daily close keeps 6")
    frame = sp.section_slice(s, {"session": DAY, "sections": [s]}, "weekly")
    cited = [g["series"] for g in frame["figures_you_may_cite"]]
    check(fb.quantified_figures(frame) <= 8 and "CCC OAS" in cited,
          f"the Weekly's Plumbing frame: {fb.quantified_figures(frame)} figures, CCC "
          f"cited ({cited})")
    blocks = s["data"]["_row_block"]
    moved = {blocks[m["name"].lower()] for m in fb.section_moves(s) if m.get("moved")}
    got_blocks = {blocks[c.lower()] for c in cited}
    check(moved <= got_blocks, f"every sub-block that moved has a figure: {sorted(moved)} "
                               f"in {sorted(got_blocks)}")
    check("for want of 60 such changes" in (frame.get("ranking") or "")
          and "Bank reserves (H.4.1)" in frame["ranking"],
          "the frame says which rows were ranked relative to their level")
    check(fb.IN_TABLES in frame and "also_moved" not in frame,
          "the rest sit under 'In the tables (do not enumerate)'")
    prompt = sp.section_prompt({**s, "depth": "medium"}, "weekly")
    check("cite at most EIGHT figures" in prompt and "at most eight" in prompt,
          "the prompt states the section's cap of eight")
    check("also moved" in prompt and "moved alongside" in prompt
          and "moved through the week" in prompt and "Never write a sentence" in prompt,
          "the frame bans 'X, Y and Z also moved' and its kin")
    # Positioning: the COT extremes get a figure the sectors used to take.
    p, pst = oct9_positioning()
    old, _ = fb.take(fb.section_moves(p), 6, "relative")
    check(all(m["where"].startswith("Sector") for m in old),
          "the bug, reproduced: at a cap of 6 by relative size, all six went to sectors")
    ws.annotate_moves({"positioning": p}, pst, DAY + "T21:00:00+00:00")
    pf = sp.section_slice(p, {"session": DAY, "sections": [p]}, "weekly")
    wh = [g["where"] for g in pf["figures_you_may_cite"]]
    check(any(w.startswith("Speculative") for w in wh)
          and any(w.startswith("Short") for w in wh)
          and fb.quantified_figures(pf) <= 8,
          f"with the cap of 8 by sub-block, the CFTC and short-interest blocks each have "
          f"a figure ({wh})")
    # The other cadences are unchanged.
    dfr = sp.section_slice(s, {"session": DAY, "sections": [s]}, "daily")
    check(fb.quantified_figures(dfr) <= 6, "the daily close's Plumbing frame stays at 6")


def mechanics_fixture() -> dict:
    prof = {"columns": ["Session", "Gamma regime", "Net GEX", "DEX", "Flip",
                        "Call / put wall"],
            "rows": [["Mon 5 Oct", "positive", "+2.10bn", "+0.40bn", "655.00", "670 / 640"],
                     ["Tue 6 Oct", "positive", "+1.20bn", "+0.20bn", "656.00", "670 / 640"],
                     ["Wed 7 Oct", "negative", "-0.80bn", "-0.10bn", "660.00", "670 / 645"],
                     ["Thu 8 Oct", "negative", "-1.40bn", "-0.30bn", "662.00", "675 / 645"],
                     ["Fri 9 Oct", "positive", "+0.90bn", "+0.10bn", "661.00", "675 / 650"]]}
    rng = {"columns": ["Session", "Max pain", "Implied range", "Actual range",
                       "Close vs flip", "Flags"],
           "rows": [["Mon 5 Oct", "660.00", "7.10 (VIX as proxy)", "5.20", "above", "none"],
                    ["Tue 6 Oct", "660.00", "7.00 (VIX as proxy)", "6.10", "above", "pinned"],
                    ["Wed 7 Oct", "660.00", "7.40 (VIX as proxy)", "11.90", "below",
                     "amplified"],
                    ["Thu 8 Oct", "665.00", "7.60 (VIX as proxy)", "9.80", "below", "none"],
                    ["Fri 9 Oct", "665.00", "7.20 (VIX as proxy)", "4.10", "above",
                     "call wall held"]]}
    vol = {"columns": ["Measure", "Level", "Context", "Week"],
           "rows": [["VIX", "17.40", "62th percentile, five years", "+2.1 pts"],
                    ["VIX3M over VIX (term structure, published)", "1.08", "contango", "—"],
                    ["SPY 20-day realized against the VIX", "13.2 vs 17.4",
                     "implied above realized by 4.2 points", "+1.8 pts"],
                    ["Daily move priced, and realized", "1.10% priced", "0.83% realized",
                     "—"],
                    ["MOVE (Treasury volatility)", "98.0", "2026-10-09", "+6.0 pts"],
                    ["SKEW (tail-risk pricing)", "141.0", "2026-10-09", "−3.0 pts"]]}
    return {"id": "mechanics", "title": "Mechanics", "depth": "medium",
            "items": [{"key": "mech:dials", "text": "At the week's end: dealer gamma "
                       "positive.", "show": True}],
            "table": prof, "subsections": [{"title": "Ranges and flags", "table": rng},
                                           {"title": "Volatility", "table": vol}],
            "data": {"_move_z": {"vix": {"z": 1.1}, "move (treasury volatility)": {"z": 2.2},
                                 "skew (tail-risk pricing)": {"z": -0.4},
                                 "spy 20-day realized against the vix": {"z": 0.9}}}}


def misfit_fixture() -> dict:
    return {"id": "misfit", "title": "What doesn't fit", "depth": "deep", "items": [],
            "table": None, "subsections": [],
            "data": {"gaps": [
                {"gap": "equities against credit", "sides": "the index at highs, the "
                 "bottom of high yield widening", "z": 2.4, "sessions_open": 8,
                 "closes_when": "CCC spreads narrow"},
                {"gap": "the long bond against breakevens", "sides": "yields up, "
                 "inflation pricing flat", "z": -2.1, "sessions_open": 3,
                 "closes_when": "breakevens rise"}],
                "extremes": [
                    {"name": "RRP balance", "percentile": 1.0,
                     "percentile_ordinal": "1st", "side": "the low tail"},
                    {"name": "the 30-year yield", "percentile": 96.0,
                     "percentile_ordinal": "96th", "side": "the high tail"},
                    {"name": "copper over gold", "percentile": 94.0,
                     "percentile_ordinal": "94th", "side": "the high tail"}],
                "venue_disagreements": {"fed_funds": [
                    {"meeting": "2026-10-28", "venue": "kalshi", "side": "cut",
                     "venue_probability": 0.78, "fed_funds_implied": 0.61,
                     "gap_points": 17.0, "threshold_points": 15}]},
                "exceptions_open_now": ["RRP balance at a five-year extreme"]}}


def ahead_fixture() -> tuple[dict, dict]:
    cal = [{"date": "2026-10-14", "time": "08:30", "event": "Consumer Price Index",
            "tier": 1, "consensus": "prior 0.3% m/m"},
           {"date": "2026-10-15", "time": "13:00", "event": "30-year bond auction",
            "tier": 1, "consensus": "prior 30-year: high yield 4.712%, bid-to-cover "
                                    "2.38 (2026-09-11); tail not stored"},
           {"date": "2026-10-16", "time": "16:00", "event": "Monthly option expiry",
            "tier": 2, "consensus": "—"}]
    strikes = [f"{x:.1f}%" for x in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)]
    for n, kind in enumerate(("m/m", "y/y", "m/m core")):
        for k, x in enumerate(strikes):
            cal.append({"date": "2026-10-14", "time": "08:30",
                        "event": f"Prediction market resolves: Will CPI {kind} be "
                                 f"above {x} in September?",
                        "tier": 3, "consensus": f"last {90 - 15 * k - n}%"})
    ahead = {"id": "ahead", "title": "Ahead", "depth": "deep", "items": [],
             "table": None, "subsections": [],
             "data": {"calendar": cal, "watching": ["equities against credit"],
                      "graded_calls": {"rows": [
                          {"source": "daily_close_outlook", "n": 14, "mean_brier": 0.2113,
                           "vs_coin": -0.0387, "base_rate": True}]}}}
    priced = {"id": "priced", "title": "What's priced", "depth": "medium", "items": [],
              "table": None, "data": {},
              "subsections": [{"title": "Rates priced", "table": {
                  "columns": ["Measure", "Level", "Priced or change", "As of"],
                  "rows": [["FOMC 2026-10-28: implied rate after", "3.88%",
                            "61% of a 25 bp cut", DAY]]}}]}
    return ahead, priced


def group_i() -> None:
    print(f"\n{LINE}\nI. T3.4c: THE READ, MECHANICS, WHAT DOESN'T FIT AND AHEAD\n{LINE}")
    cap = sp.section_figure_cap("mechanics", "weekly")
    mech = mechanics_fixture()
    ed = {"session": DAY, "sections": [mech]}
    mf = sp.section_slice(mech, ed, "weekly")
    n = fb.quantified_figures(mf)
    cited = [c["series"] for c in mf["figures_you_may_cite"]]
    check(n <= cap and "table" not in mf and "subsections" not in mf,
          f"Mechanics: {n} figures against a cap of {cap} (the 9 Oct run cited 12)")
    check(cited[0] == "Daily move priced, and realized"
          and cited[1] == "SPY range, Wed 7 Oct",
          f"the daily move priced and realized first, then the session whose range most "
          f"exceeded the implied ({cited})")
    check([r["to"] for r in mf.get("gamma_regime_changes") or []]
          == ["negative", "positive"]
          and any(f["flags"] == "amplified" for f in mf.get("flagged_sessions") or []),
          "gamma-regime changes and the flags are named, never quantified")
    mis = misfit_fixture()
    xf = sp.section_slice(mis, {"session": DAY, "sections": [mis]}, "weekly")
    xc = [c["series"] for c in xf["figures_you_may_cite"]]
    check(fb.quantified_figures(xf) <= sp.section_figure_cap("misfit", "weekly"),
          f"What doesn't fit: {fb.quantified_figures(xf)} figures (the 9 Oct run cited 7)")
    check(xc[:3] == ["equities against credit", "RRP balance",
                     "Kalshi, FOMC 2026-10-28, cut"],
          f"ranked on one scale: the gap at z 2.4, the 1st percentile (z 2.33), the "
          f"disagreement 17 points over a 15-point line (2.27) ({xc})")
    check(all("gap_open_sessions" in c for c in xf["figures_you_may_cite"]
              if c["series"].startswith(("equities", "the long bond"))),
          "a gap's age is offered as the gap's, by that name")
    ahead, priced = ahead_fixture()
    ed = {"session": DAY, "sections": [priced, ahead]}
    af = sp.section_slice(ahead, ed, "weekly")
    ac = af["figures_you_may_cite"]
    check(fb.quantified_figures(af) <= sp.section_figure_cap("ahead", "weekly"),
          f"Ahead: {fb.quantified_figures(af)} figures (the 9 Oct run cited 7)")
    check(ac[0]["series"].startswith("FOMC 2026-10-28")
          and ac[0].get("implied_rate_pct") == "3.88%"
          and ac[0].get("move_probability_pct") == "61%"
          and ac[0].get("move_increment_bp") == "25 bp"
          and ac[0].get("direction") == "cut",
          "the next FOMC meeting and its pricing first, each figure under a key that "
          "names its unit (W-1.1a item 1)")
    fams = af.get("contract_families") or []
    cpi = [c for c in ac if "Prediction market resolves" in c["series"]]
    check(fams and all(f["outcomes"] == 6 for f in fams)
          and len({fb.contract_family(c["series"]) for c in cpi}) == len(cpi),
          f"18 CPI contracts are {len(fams)} families: at most one figure each, the "
          f"modal outcome, the rest counted by name")
    # The read: the five lines' figures across the edition.
    s, st = oct9_plumbing()
    from daily_cascade import weekly_stack as ws
    ws.annotate_moves({"plumbing": s}, st, DAY + "T21:00:00+00:00")
    s["claim"] = "Credit split: CCC OAS rose 37 bp while IG tightened 4 bp."
    read = {"id": "read", "title": "The read", "depth": "deep", "items": [
        {"key": "read:attr:0", "text": "Thu 8 Oct: Reuters, on the move in oil: "
         "“Oil prices rose 3% on supply worries.” (https://example.com/a)"}],
            "table": {"columns": ["Day", "SPY", "10-year", "Tier-1 release (actual, prior)",
                                  "Fed speech or auction", "Most-cited story (source)"],
                      "rows": [["Mon 5 Oct", "+0.20%", "+1 bp", "—", "—", "—"],
                               ["Wed 7 Oct", "−1.10%", "+4 bp", "—", "—", "—"]]}}
    ed = {"session": DAY, "sections": [read, mechanics_fixture(), misfit_fixture(), s,
                                        priced, ahead]}
    rf = fb.read_frame(ed, sp.read_figure_cap("weekly"), "week")
    rc = [c["series"] for c in rf["figures_you_may_cite"]]
    check(fb.quantified_figures(rf) <= sp.read_figure_cap("weekly"),
          f"The read: {fb.quantified_figures(rf)} figures against {sp.read_figure_cap('weekly')} "
          f"(the 9 Oct run cited 15)")
    check("CCC OAS" in rc and "37" not in str(rf["sections"]),
          f"the top move of each section in turn, claims masked ({rc})")
    check("3%" not in str(rf["press_attributions"]) and "http" not in
          str(rf["press_attributions"]),
          "a press attribution carries no figure and no URL into the frame")
    rp = sp.read_prompt("weekly")
    check("YOUR FIGURES ARE IN YOUR DATA" in rp and "EXCESS" in rp
          and "alongside" in rp and "on the back of" in rp,
          "the read's prompt: its frame, the comparison vocabulary and the connectors")
    book = {"id": "book", "title": "The book", "depth": "medium", "items": []}
    check("COMPARISONS:" in sp.section_prompt(book, "weekly")
          and "relative to" in sp.section_prompt(book, "weekly"),
          "the book's prompt carries the comparison vocabulary (T3.4a's pattern)")
    f = sp.excess_faults("The book returned +1.2% against cash at +0.1%.")
    check(f and "the rule:" in f[0] and "EXCESS" in f[0],
          "an excess fault names the sentence and quotes the rule for the retry")


def main() -> int:
    print(f"{LINE}\nTHE FIGURE BUDGET AT THE FRAME (T3.4)\n{LINE}")
    counts = group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    group_f()
    group_g()
    group_h()
    group_i()
    print("\nFixture parent frames, figures carried: "
          + ", ".join(f"{c} {s} {n}" for (c, s), n in sorted(counts.items())))
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
