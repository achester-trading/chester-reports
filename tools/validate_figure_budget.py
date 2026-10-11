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
        cap = cadence_mod.figure_cap(cad)
        check(set(cad["figure_budget_parents"]) == {"tape", "plumbing", "positioning",
                                                    "priced", "slow"},
              f"{cad_name}: the parents are config's five")
        for s in (plumbing_fixture(), tape_fixture()):
            ed = ed_of([s], cad_name)
            frame = sp.section_slice(s, ed, cad_name)
            n = fb.quantified_figures(frame)
            counts[(cad_name, s["id"])] = n
            got = frame.get("figures_you_may_cite") or []
            check(0 < n <= cap and len(got) <= cap,
                  f"{cad_name} {s['id']}: the frame carries {n} figures, the cap is {cap}")
            cells = {str(c) for m in fb.section_moves(s) for c in (m.get("change"),
                                                                    m.get("level")) if c}
            check(set(frame["also_moved"]) <= {m["name"] for m in fb.section_moves(s)}
                  and not any(c in x for x in frame["also_moved"] for c in cells),
                  f"{cad_name} {s['id']}: also_moved is names only ({len(frame['also_moved'])})")
            allnames = {m["name"] for m in fb.section_moves(s)}
            check({g["series"] for g in got} | set(frame["also_moved"]) == allnames,
                  f"{cad_name} {s['id']}: every series the section covers is either "
                  f"quantified or named")
            check("table" not in frame and "subsections" not in frame and "data" not in frame
                  and "items" not in frame,
                  f"{cad_name} {s['id']}: no table, block, item or data numbers reach the frame")
            check("blocks beneath this section carry" in frame["blocks_carry"],
                  f"{cad_name} {s['id']}: the frame says the blocks beneath carry the numbers")
            prompt = sp.section_prompt(s, cad_name)
            check("figures_you_may_cite" in prompt and "name it, do not quantify it" in prompt
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
          and len(sf["also_moved"]) == 4,
          "a level table (the slow layers' valuation) offers its levels up to the cap, "
          "the rest by name")
    nonparent = {**tape_fixture(), "subsections": []}
    check(sp.section_slice(nonparent, ed_of([nonparent], "daily"), "daily").get("table"),
          "a listed section with no sub-sections is not a parent: it keeps its slice")
    other = {**plumbing_fixture(), "id": "mechanics", "title": "Mechanics"}
    check("table" in sp.section_slice(other, ed_of([other], "weekly"), "weekly")
          or "subsections" in sp.section_slice(other, ed_of([other], "weekly"), "weekly"),
          "a section not in the parent list keeps its slice")
    return counts


def group_b() -> None:
    print(f"\n{LINE}\nB. BLOCKS (the Monthly)\n{LINE}")
    from monthly_macro import prose
    cap = prose.figure_cap()
    sec, ss = pm_block_fixture()
    ed = ed_of([sec], "monthly")
    frame = prose.block_slice(sec, ss, ed)
    n = fb.quantified_figures(frame)
    kept = [r["series"] for r in frame["rows"]]
    check(n <= cap, f"the FOMC prediction-market block: {n} figures, cap {cap} "
                    f"({len(ss['table']['rows'])} contracts)")
    check(kept[:2] == ["FOMC December: outcome F", "FOMC December: outcome K"],
          f"its rows by absolute change: +22, +15 first ({kept})")
    check(set(kept) | set(frame["also_moved"]) == {r[0] for r in ss["table"]["rows"]}
          and not set(kept) & set(frame["also_moved"]),
          f"the rest by name only ({len(frame['also_moved'])})")
    check(all("change_signed" in r and "change" not in r for r in frame["rows"]),
          "a kept row carries its data's signed form, never the raw change")
    pl = plumbing_fixture()
    liq = next(x for x in pl["subsections"] if x["title"] == "Liquidity")
    lf = prose.block_slice(pl, liq, ed_of([pl], "monthly"))
    check(fb.quantified_figures(lf) <= cap,
          f"the liquidity block: {fb.quantified_figures(lf)} figures, cap {cap}")
    check(lf.get("rows") and lf["rows"][0]["series"].startswith("Net liquidity"),
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
    check(prose.ATTEMPTS == 3, "three attempts for every Monthly section")
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


def main() -> int:
    print(f"{LINE}\nTHE FIGURE BUDGET AT THE FRAME (T3.4)\n{LINE}")
    counts = group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    group_f()
    group_g()
    print("\nFixture parent frames, figures carried: "
          + ", ".join(f"{c} {s} {n}" for (c, s), n in sorted(counts.items())))
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
