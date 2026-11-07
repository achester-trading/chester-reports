"""
Validation gate for T3.5: the Monthly's frames take the Weekly's budget
discipline. Monthly dry run #4 (main 785fa19, the box, 11 Oct 2026) withheld
blocks in five classes; each is rebuilt here, on its own fixture, with no store
and no network -- the writer is scripted.

  A  A COUNT CARRIES ITS NOUN. Payrolls' +29 thousand displays "+29,000 jobs" and
     a CFTC change "+125,623 contracts"; the bare-delta rule passes exactly that
     form with no display beside it (a summary's or parent's cited figure), and
     still refuses the integer alone -- at a sentence's end and before a comma
     too, which it used to miss. A series with no noun keeps the plain integer,
     accepted as its own display as before.
  B  THE BLOCK'S FRAME IS A WEEKLY PARENT'S. Yields & spreads, FOMC pricing and
     Prediction markets: the rest, past the cap: the figures it may cite under
     `figures_you_may_cite` (inside the cap), the table with every other row's
     figures masked, those rows' names under "In the tables (do not enumerate)",
     the frame note and the filler rule in the prompt. A draft citing a masked
     figure is withheld, and the retry names that figure and lists the allowed
     ones; the corrected draft publishes. A filler draft is withheld.
  C  THE ORDINAL THE TABLE PRINTS. The three theme blocks -- digital (75th),
     energy (89th, its 20-day change named), metals (86th) -- publish a draft
     that copies the table's ordinal, and the audit still refuses an ordinal the
     table does not print.
  D  NO STORE KEY AS A NAME. The theme families' series carry labels, so a
     summary naming one is not withheld as an internal id.
  E  A VOICE'S VIEW IS ATTRIBUTED. Lane's "driven by" -- paraphrased, in single
     quotes or double -- prints in the voices block; the same words in our own
     prose are still a motive fault.
  F  B84, THE BARE DELTAS OF THE 28 OCT DRY RUN. China's gold carries "ounces";
     the bare-delta retry quotes the frame's display for each bare figure
     ("write '+29,000 jobs'"); the CFTC level carries "−964,293 contracts", the
     dry run's bare draft is withheld naming it, and the corrected draft
     publishes. Each dry-run sentence still fails as written.

    python tools/validate_monthly_frames.py
"""

from __future__ import annotations

GATE_KIND = "code"   # S1: a gate declares itself; tools/gate_list.py reads it

import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from altdata import labels, numeral_audit as na  # noqa: E402
from daily_cascade import figure_budget as fb  # noqa: E402
from daily_cascade import stack_prose as sp  # noqa: E402
from monthly_macro import prose as pr  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = 0
FAIL = 0
LINE = "=" * 78


def check(c, m: str) -> None:
    global PASS, FAIL
    if c:
        PASS += 1
        print(f"  PASS  {m}")
    else:
        FAIL += 1
        print(f"  FAIL  {m}")


class Resp:
    def __init__(self, t):
        self.content = [types.SimpleNamespace(type="text", text=t)]
        self.model = "fixture-model"
        self.stop_reason = "end_turn"


def client(calls: list, script: dict):
    """`script`: a marker in the system prompt -> replies served in turn (the
    last repeats)."""
    served: dict = {}

    def create(**k):
        calls.append(k["system"])
        for mark, replies in script.items():
            if mark in k["system"]:
                n = served.get(mark, 0)
                served[mark] = n + 1
                return Resp(replies[min(n, len(replies) - 1)])
        return Resp("The block was quiet over the month.")
    return types.SimpleNamespace(messages=types.SimpleNamespace(create=create))


def block(sid: str, stitle: str, title: str, phase: str, cols: list, rows: list,
          data=None) -> dict:
    ss = {"title": title, "phase": phase, "prose": {"words": "60 to 100"},
          "table": {"columns": cols, "rows": rows}}
    if data is not None:
        ss["data"] = data
    return {"id": sid, "title": stitle, "depth": "deep", "subsections": [ss]}


def edition(*sections) -> dict:
    return {"month": "September 2026", "session": "2026-09-30", "cadence": "monthly",
            "sections": list(sections)}


def write(ed: dict, script: dict, calls: list) -> dict:
    return pr.write_all({}, client=client(calls, script), ed=ed,
                        secs=pr.block_plan(ed))


# --- the dry run's blocks ------------------------------------------------------
YIELDS = [("2-year", "3.62%", "−14 bp"), ("5-year", "3.71%", "−9 bp"),
          ("10-year", "4.12%", "+6 bp"), ("30-year", "4.71%", "+11 bp"),
          ("2s10s", "50 bp", "+20 bp"), ("High-yield OAS", "3.05%", "+18 bp"),
          ("Investment-grade OAS", "0.82%", "+3 bp"), ("CCC OAS", "10.58%", "+51 bp")]
FOMC = [("FOMC 28 Oct: implied rate", "4.13%", "−9 bp"),
        ("FOMC 9 Dec: implied rate", "3.96%", "−12 bp"),
        ("FOMC 27 Jan: implied rate", "3.85%", "−10 bp"),
        ("FOMC 17 Mar: implied rate", "3.74%", "−8 bp"),
        ("FOMC 28 Apr: implied rate", "3.66%", "−7 bp"),
        ("FOMC 16 Jun: implied rate", "3.58%", "−6 bp")]
PM_REST = [("Recession in 2026", "33%", "+4 pts"), ("CPI above 3% in October", "9%", "−2 pts"),
           ("Government shutdown by 1 Nov", "41%", "+12 pts"),
           ("Senate control 2026", "58%", "+1 pts"), ("House control 2026", "62%", "−3 pts"),
           ("Gold above $3,000 by year end", "27%", "+6 pts")]


def yields_block() -> dict:
    return block("plumbing", "Plumbing & rates", "Yields & spreads", "block:plumbing:yields",
                 ["Series", "Level or actual", "Month or prior", "As of"],
                 [[n, lv, ch, "2026-09-30"] for n, lv, ch in YIELDS])


def group_a() -> None:
    print(f"\n{LINE}\nA. A COUNT CARRIES ITS NOUN; THE GATE PASSES THAT FORM\n{LINE}")
    pay = na.change_display(29.0, "K", "fred.nfp")
    cftc = na.change_display(125623.0, "count", "cftc.noncomm_net")
    check(pay == "+29,000 jobs" and cftc == "+125,623 contracts"
          and na.change_display(-7.0, "N", "fred.claims_4wk") == "−7 claims"
          and na.change_display(-1500.0, "K", "fred.nfp") == "−1.5 million",
          f"the display carries the noun: {pay}, {cftc}; at ±1,000 thousand the "
          f"scale word returns")
    check(na.change_display(29.0, "K") == "+29,000"
          and na.change_display(29.0, "K", "calc.surprise_vs_naive.nfp") == "+29,000 jobs",
          "a series with no noun keeps the integer; a derived payroll series takes "
          "its source's noun")
    txt = "Payrolls rose +29,000 jobs and speculators added +125,623 contracts."
    check(not na.bare_deltas(txt),
          "the noun form passes the bare-delta rule with no display beside it -- "
          "the summary's and the parent's cited figure (dry run #4: payrolls twice, "
          "CFTC once)")
    check(na.bare_deltas("Payrolls rose +29,000.") == ["+29,000"]
          and na.bare_deltas("Payrolls rose +29,000, the most since May.") == ["+29,000"]
          and na.bare_deltas("Specs added 125,623 in the month") == ["added 125,623"],
          "the integer alone is still refused -- at a sentence's end and before a "
          "comma, which the rule used to miss")
    check(not na.bare_deltas("Claims rose +29,000 in the week.",
                             na.accepted_deltas({"change_display": "+29,000"})),
          "a nounless display is still accepted as its own form (T3.4a)")
    # Through the writer: the noun form publishes, the bare form is withheld
    # naming the display to copy.
    sec = block("plumbing", "Plumbing & rates", "Macro: employment, income, GDP",
                "block:plumbing:macro", ["Series", "Latest", "The month"],
                [["Nonfarm payrolls", "159.04 million", pay]])
    calls: list = []
    ok = write(edition(sec), {"THE BLOCK: Macro": [
        f"Payrolls rose {pay} to 159.04 million over the month."]}, calls)
    bad = write(edition(sec), {"THE BLOCK: Macro": [
        "Payrolls rose +29,000 to 159.04 million over the month."]}, [])
    r_ok, r_bad = ok["block:plumbing:macro"], bad["block:plumbing:macro"]
    check(r_ok["published"], f"a block copying \"{pay}\" publishes ({r_ok.get('reason')})")
    check(not r_bad["published"] and "unit or scale" in str(r_bad.get("first_reason")
                                                            or r_bad.get("reason")),
          f"the bare integer is withheld, naming the display to copy "
          f"({str(r_bad.get('first_reason') or r_bad.get('reason'))[:90]})")
    check("+29,000 jobs" in pr.DISPLAY_RULE and "+42,984 contracts" in pr.DISPLAY_RULE,
          "and the frame's display rule shows the noun form")


def group_b() -> None:
    print(f"\n{LINE}\nB. THE BLOCK'S FRAME IS A WEEKLY PARENT'S\n{LINE}")
    cap = pr.figure_cap()
    for sec in (yields_block(),
                block("priced", "What's priced", "FOMC pricing: the fed-funds path",
                      "block:priced:fomc", ["Item", "Level", "Month change"],
                      [list(r) for r in FOMC]),
                block("priced", "What's priced", "Prediction markets: the rest",
                      "block:priced:pm_rest", ["Item", "Kalshi", "Month change"],
                      [list(r) for r in PM_REST])):
        ss = sec["subsections"][0]
        fr = pr.block_slice(sec, ss, edition(sec))
        got = [r["series"] for r in fr.get("figures_you_may_cite") or []]
        named = fr.get(fb.IN_TABLES) or []
        rows = (fr.get("table") or {}).get("rows") or []
        masked = [r for r in rows if r[0] in named]
        check(got and fb.quantified_figures(fr) <= cap
              and set(got) | set(named) == {r[0] for r in ss["table"]["rows"]}
              and not set(got) & set(named),
              f"{ss['title']}: {len(got)} row(s) to cite in {fb.quantified_figures(fr)} "
              f"figures (cap {cap}); {len(named)} under '{fb.IN_TABLES}'")
        check(masked and all(c == fb.MASKED for r in masked for c in r[1:]
                             if c != "2026-09-30")
              and fr.get("columns") == ss["table"]["columns"],
              f"{ss['title']}: the table travels with every other row's figures "
              f"masked, and its column heads")
    sec = yields_block()
    ed = edition(sec)
    plan = pr.block_plan(ed)[0]
    check("YOUR FIGURES ARE IN YOUR DATA" in plan["system"]
          and "never convert one" in plan["system"]
          and sp.FILLER_RULE in plan["system"],
          "the prompt carries the frame note -- copy, never convert -- and the "
          "filler rule")
    fr = plan["slice"]
    first = fr["figures_you_may_cite"][0]
    masked_row = next(r for r in fr["table"]["rows"] if r[1] == fb.MASKED)
    orig = next(r for r in sec["subsections"][0]["table"]["rows"]
                if r[0] == masked_row[0])
    bad = (f"{first['series']} moved {first['Month or prior']} on the month, while "
           f"the {orig[0]} moved {orig[2]}.")
    good = f"{first['series']} moved {first['Month or prior']} on the month."
    calls: list = []
    res = write(ed, {"THE BLOCK: Yields": [bad, good]}, calls)["block:plumbing:yields"]
    check(res["published"] and res["attempts"] == 2,
          f"a draft citing a masked figure ({orig[2]}) is withheld; the second "
          f"publishes ({res['attempts']} attempts)")
    retry = calls[1] if len(calls) > 1 else ""
    check(orig[2].split()[0] in retry.split("could not find")[-1].split(";")[0]
          and "cite only these" in retry
          and first["Month or prior"] in retry.split("cite only these")[-1],
          "the retry names the refused figure and lists the allowed ones")
    fill = write(ed, {"THE BLOCK: Yields": [
        f"{first['series']} moved {first['Month or prior']}. The 5-year, the 30-year "
        f"and the 2s10s curve also moved."]}, [])["block:plumbing:yields"]
    check(not fill["published"] and "filler" in str(fill.get("first_reason")
                                                    or fill.get("reason")),
          "a filler sentence is withheld in a Monthly block")


THEMES = {
    "digital": (["Bitcoin (BTC-USD)", "61,240.00 (2026-09-30)", "+4.10 percent",
                 "38,900.00 (full history since 2015-01-01, n=2,830)",
                 "75th (5 years, n=1,258)"], "75th"),
    "energy": (["The oil fund (USO)", "78.20 (2026-09-30)", "−3.40 percent",
                "64.10 (full history since 2015-01-01, n=2,700)",
                "89th (5 years, n=1,258)"], "89th"),
    "metals": (["The gold fund (GLD)", "240.00 (2026-09-30)", "+2.20 percent",
                "170.00 (full history since 2015-01-01, n=2,700)",
                "86th (5 years, n=1,258)"], "86th"),
}
THEME_COLS = ["Series", "Latest (data as of)", "20-day change",
              "Long-run average (window)", "Percentile (window)"]


def group_c() -> None:
    print(f"\n{LINE}\nC. THE ORDINAL THE TABLE PRINTS (the three theme blocks)\n{LINE}")
    for fam, (row, ordn) in THEMES.items():
        sec = block("slow", "Slow layers", f"Themes: {fam}", f"block:slow:{fam}",
                    THEME_COLS, [row], {"family": fam, "rows": [
                        {"series": row[0], "latest": float(row[1].split()[0]
                                                            .replace(",", "")),
                         "percentile": float(ordn[:-2]) + 0.2,
                         "percentile_ordinal": ordn}]})
        name = row[0][:1].lower() + row[0][1:]
        good = (f"{row[0]} sits at the {ordn} percentile of five years, its 20-day "
                f"change {row[2].split()[0]} percent.")
        res = write(edition(sec), {f"THE BLOCK: Themes: {fam}": [good]}, [])
        r = res[f"block:slow:{fam}"]
        check(r["published"],
              f"Themes: {fam} -- \"{ordn}\" copied from the table publishes "
              f"({r.get('reason')})")
        n = int(ordn[:-2]) - 1
        wrong = f"{row[0]} sits at the {n}{na.ordinal_suffix(n)} percentile."
        a = na.audit(wrong, na.with_signed(pr.block_slice(sec, sec["subsections"][0],
                                                          edition(sec))))
        check(not a.passed, f"Themes: {fam} -- an ordinal the table does not print "
                            f"({n}{na.ordinal_suffix(n)}) is still refused; "
                            f"named {name!r}")
    check(na.stored_ordinals({"rows": [["x", "86th (5 years, n=59)", "the 2nd session",
                                        "75th percentile"]]}) == {"86th", "75th"},
          "the audit reads an ordinal a cell prints, not one in running text")


def group_d() -> None:
    print(f"\n{LINE}\nD. NO STORE KEY AS A NAME\n{LINE}")
    # Every series the families declare, read from payload.ALT_FAMILIES rather
    # than copied, so a key added there needs its label here.
    from monthly_macro import payload as pl
    keys = [m for f in pl.ALT_FAMILIES.values() for m in f.get("metrics") or []]
    labs = {k: labels.metric(k) for k in keys}
    check(all(v and "." not in v and "mkt_" not in v and v != labels.plain(k)
              for k, v in labs.items()),
          f"every theme series has a label ({labs['yfinance.mkt_gld']}, "
          f"{labs['yfinance.mkt_uso']}, ...)")
    txt = "The gold fund (GLD) printed 240.00, at the 86th percentile."
    check(not sp.id_faults(txt) and sp.id_faults("yfinance.mkt_gld printed 240.00."),
          "a summary naming the label passes the id rule; the store key does not "
          "(summary:slow and block:slow:metals, withheld on the fixture before)")


def group_e() -> None:
    print(f"\n{LINE}\nE. A VOICE'S VIEW IS ATTRIBUTED\n{LINE}")
    from daily_cascade import voices_block as vb, stack as stack_mod
    cfg = stack_mod.config()
    for v in ("Lane said euro-area inflation was driven by energy.",
              "Lane: services inflation is 'driven by wages' and will ease.",
              'Lane said the rise was "driven by energy".'):
        check(vb.printed_view({"view": v}) == v, f"the view prints: {v}")
    check(any(f.startswith("motive") for f in sp.style_faults(
              "Euro-area inflation was driven by energy.", cfg)),
          "the same words in our own prose are still a motive fault")
    check(not any(f.startswith("motive") for f in sp.style_faults(
              "Lane called it 'driven by wages'.", cfg))
          and any(f.startswith("motive") for f in sp.style_faults(
              "Lane's view was driven by wages.", cfg)),
          "single quotes strike the quotation; an apostrophe does not")


def group_f() -> None:
    print(f"\n{LINE}\nF. B84: THE BARE DELTAS OF THE 28 OCT DRY RUN\n{LINE}")
    from monthly_macro import stack as stk
    # summary:narratives -- official gold in ounces, stored as a plain count.
    gold = na.change_display(740000.0, "count", "safe.gold_reserves_oz")
    check(gold == "+740,000 ounces"
          and na.change_display(740000.0, "count",
                                "imf.ifs.gold_reserves_oz.chn") == "+740,000 ounces",
          f"China's official gold carries its noun ({gold})")
    drafted = ("China's official gold holdings (SAFE) rose +740,000, speculators "
               "added +118,738 contracts to net yen futures positioning (CFTC).")
    check(na.bare_deltas(drafted) == ["+740,000"]
          and not na.bare_deltas(drafted.replace("+740,000", gold)),
          "the dry run's sentence is still withheld; the same sentence with the "
          "display copied publishes")
    # month_in_markets -- the retry names the form to copy.
    hint = pr.bare_hint(["+29,000"], [{"rows": [{"metric": "fred.nfp",
                                                 "change_display": "+29,000 jobs",
                                                 "latest_level_display":
                                                     "159.04 million"}]}])
    check("write '+29,000 jobs' for +29,000" in hint,
          f"the bare-delta retry quotes the frame's display for the figure ({hint})")
    check("noun or scale" in pr.bare_hint(["+29,000"], [{"rows": []}]),
          "with no display in the frame, the retry says to add the noun or scale")
    sec = block("plumbing", "Plumbing & rates", "Macro: employment, income, GDP",
                "block:plumbing:macro", ["Series", "Latest", "The month"],
                [["Nonfarm payrolls", "159.04 million", "+29,000 jobs"]])
    bad = write(edition(sec), {"THE BLOCK: Macro": [
        "Payrolls rose +29,000 to 159.04 million over the month."]}, [])
    r = bad["block:plumbing:macro"]
    why = str(r.get("first_reason") or r.get("reason"))
    check(not r["published"] and "write '+29,000 jobs'" in why,
          f"month_in_markets' sentence is withheld, the retry quoting '+29,000 jobs' "
          f"({why[-70:]})")
    # block:positioning:cftc -- the level carries its display, the bare level
    # still fails.
    disp = stk.count_level_display(-964293.0, "cftc.noncomm_net")
    check(disp == "−964,293 contracts"
          and stk.count_level_display(-964293.0, "aaii.bull_bear_spread") is None,
          f"the CFTC level has a display with its noun ({disp}); a series with no "
          f"noun gets none")
    hist = {"history": [{"group": "cftc", "series": "CFTC 10-year note",
                         "latest": -964293.0, "latest_level_display": disp,
                         "as_of": "2026-10-20"}]}
    cftc = block("positioning", "Positioning & flows", "Speculative positioning (CFTC)",
                 "block:positioning:cftc", ["Contract", "Net", "Change"],
                 [["10-year note", "−964,293", "−125,318 contracts"]], data=hist)
    drafts = ["Positioning split along the curve into October. Net speculative "
              "contracts in 10-year note futures stood at -964,293 as of 2026-10-20, "
              "a change of −125,318 contracts on the month.",
              f"Positioning split along the curve into October. Net speculative "
              f"contracts in 10-year note futures stood at {disp} as of 2026-10-20, "
              f"a change of −125,318 contracts on the month."]
    calls: list = []
    res = write(edition(cftc), {"THE BLOCK: Speculative": drafts}, calls)
    r = res["block:positioning:cftc"]
    check(r["published"] and r.get("attempts") == 2 and disp in (r.get("text") or "")
          and len(calls) == 2 and f"write '{disp}'" in calls[1],
          f"the dry run's CFTC draft is withheld and the retry names '{disp}'; the "
          f"draft that copies it publishes ({r.get('attempts')} attempts)")


class _FakeStore:
    """A store of {key: [(observed_at, value, available_at)]}: as_of and
    latest_as_of, point in time, nothing else."""

    def __init__(self, rows: dict):
        self.rows = rows

    def as_of(self, key, as_of=None, instrument=None, **_kw):
        cut = str(as_of or "9999")
        return [{"observed_at": o, "value_num": v, "available_at": a}
                for o, v, a in sorted(self.rows.get(key, [])) if a <= cut]

    def latest_as_of(self, key, cut, instrument=None):
        r = self.as_of(key, cut)
        return r[-1] if r else None


def group_g() -> None:
    """A95 PART 6: THE SEVEN PLACES THE 1 NOV EDITION CONTRADICTED ITSELF (the
    Monthly Letter's M1-M7). Each pair of prints now reads one source or carries
    its own label, and each case is checked here, the Monthly's consistency
    gate, rather than in a new one."""
    import datetime as dt
    import inspect
    import yaml
    print(f"\n{LINE}\nG. A95 PART 6: THE EDITION AGAINST ITSELF (M1-M7)\n{LINE}")
    from daily_cascade import weekly_stack as ws
    from monthly_macro import stack as ms, v2
    # M1 -- the summary carries section 4's counts and may not deny them.
    mis = {"id": "misfit", "title": "What doesn't fit", "subsections": [],
           "data": {"exceptions_open_now": ["a", "b", "c", "d", "e", "f", "g"],
                    "open_contradictions": [{"id": "equity_credit"}],
                    "gaps": [{"gap": "equities against high-yield credit"}],
                    "extremes": []}}
    fr = pr.summary_frame(mis, {"sections": [mis]})
    deny = "No contradiction is open at month end, and the record is quiet."
    check(fr.get("open_now", {}).get("exceptions_open_now") == "seven"
          and fr["open_now"].get("open_contradictions") == "one"
          and pr.misfit_count_faults(deny, mis)
          and not pr.misfit_count_faults("One contradiction is open, with seven "
                                         "exceptions beside it.", mis)
          and not pr.misfit_count_faults(deny, {"data": {}}),
          f"M1: the summary's frame carries section 4's counts "
          f"({fr.get('open_now')}); 'no contradiction' against one open is withheld")
    sec = {"key": "summary:misfit", "sid": "misfit", "slice": {}}
    check(any("section 4 counts" in f for f in pr._stack_faults(deny, sec,
                                                                {"sections": [mis]}, None)),
          "M1: the summary paragraph's own checks carry it")
    # M2 -- one month change for a spread: the yields table reads v2's prior.
    st = _FakeStore({"fred.hy_oas": [
        ("2026-08-31", 3.20, "2026-09-01T13:00:00+00:00"),
        ("2026-09-29", 3.10, "2026-09-30T13:00:00+00:00"),
        ("2026-09-30", 3.12, "2026-10-01T13:00:00+00:00"),
        ("2026-10-30", 3.26, "2026-10-31T13:00:00+00:00")]})
    now, then = "2026-11-01T12:36:16+00:00", "2026-09-30T23:59:59+00:00"
    old = ws.change_over(st, "fred.hy_oas", now, then)
    new = ws.change_over(st, "fred.hy_oas", now, then, month_aligned=True)
    vm = v2.metric_month(st, {"metric": "fred.hy_oas", "label": "HY"}, now,
                         dt.date(2026, 10, 31))
    check(old and new and old["change"] == 16.0 and new["change"] == 14.0
          and vm.get("change_bps") == new["change"]
          and new["prior_observed_at"] == "2026-09-30",
          f"M2: the yields table's month change is the themes' (+{new and new['change']} "
          f"bp from 30 Sep, = metric_month's {vm.get('change_bps')}); the prior "
          f"knowable at the month-end cutoff gave +{old and old['change']} bp from 29 Sep")
    check("month_aligned=True" in inspect.getsource(ms.plumbing_section),
          "M2: the Monthly's Plumbing reads the month-aligned change")
    # M3 -- the header names what it counts.
    ln = ms.forecast_count_line([{"ledger_source": "daily_close_outlook"},
                                 {"ledger_source": "narrative_register"}])
    ln1 = ms.forecast_count_line([{"ledger_source": "monthly_macro"},
                                  {"ledger_source": "daily_close_outlook"}])
    check("probability ledger" in ln and "none of them a scenario weight" in ln
          and "1 of them scenario weight" in ln1,
          f"M3: the header counts the ledger and says how many are scenario weights "
          f"('{ln}'), so it cannot contradict 'No probability has been emitted'")
    # M4 -- one Book Z sentence in the read's paragraph and the book section.
    bz = {"line": "vs cash +0.66% / SPY −0.55% / 60-40 −0.48% since 2026-09-01",
          "book_line": "since 2026-09-05: the book +0.10% (Portfolio Truth NAV); "
                       "cash +0.62%, SPY −0.40%, 60-40 −0.31%; excess vs cash / SPY / "
                       "60-40: −0.52 / +0.50 / +0.41 pts"}
    p = {"register_month": {"books_vs_benchmark": bz}, "our_read": {}}
    book = ms.book_section(p)
    zline = next(s for s in book["subsections"] if s["title"] == "Against Book Z")["lines"][0]
    sl = pr.our_read_slice(p)
    only = v2.book_z_sentence({"line": bz["line"]})
    check(zline == v2.book_z_sentence(bz) == f"Against Book Z, {bz['book_line']}."
          and sl["book_against_book_z"] == bz["book_line"]
          and "not an excess" in only and not only.startswith("Against Book Z"),
          "M4: the read and the book section print one Against-Book-Z sentence, the "
          "Weekly's excess line; Book Z's own ledgers are labelled returns, not excesses")
    # M5 -- the gap's age is read from the stored objects, as the Weekly's is.
    src = inspect.getsource(ms.misfit_section)
    check("state_dates(ws.stored_objects(st, now))" in src and "dates=dates" in src,
          "M5: the Monthly's gap table takes its dates from the stored objects, as "
          "the Weekly's does (weekly_stack.build)")
    # M6 -- a release's year on year by date, across a month never published.
    days = [f"{y}-{m:02d}-01" for y, m in
            [(2024, 9)] + [(2024, m) for m in (10, 11, 12)] + [(2025, m) for m in range(1, 13)]
            + [(2026, m) for m in range(1, 10)] if not (y == 2025 and m == 10)]
    vals = [100.0 + i for i in range(len(days))]
    pos, dat = ws.headline_form(vals, "yoy"), ws.headline_form(vals, "yoy", days)
    i26, i25 = days.index("2026-09-01"), days.index("2025-09-01")
    want = 100.0 * (vals[i26] / vals[i25] - 1.0)
    nov = ws.headline_form(vals[:days.index("2025-11-01") + 1], "mom",
                           days[:days.index("2025-11-01") + 1])
    check(abs(dat[0] - want) < 1e-9 and abs(pos[0] - want) > 0.1
          and (nov is None or nov[0] is None),
          f"M6: CPI's year on year compares the same month a year back by date "
          f"({dat[0]:.2f}% against {pos[0]:.2f}% by position across the missing "
          f"October 2025); a month on month against an unpublished month is n/a")
    # M7 -- one label, one series: FRED's VIX is not printed as the tape's VIX.
    th = yaml.safe_load((REPO / "config" / "monthly_themes.yaml").read_text(encoding="utf-8"))
    labs: dict = {}
    for r in th.get("scorecard") or []:
        labs.setdefault(r["label"], set()).add(r["metric"])
    for t in (th.get("themes") or {}).values():
        for r in t.get("metrics") or []:
            labs.setdefault(r["label"], set()).add(r["metric"])
    rs = yaml.safe_load((REPO / "config" / "reporting_stack.yaml").read_text(encoding="utf-8"))
    tape = set(ws.PLUMB_ROW_KEYS)

    def walk(o):
        if isinstance(o, dict):
            if o.get("label") and o.get("bars"):
                tape.add(str(o["label"]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(rs)
    clash = sorted(lb for lb, ks in labs.items()
                   if lb in tape and any(k.startswith("fred.") for k in ks))
    two = sorted(lb for lb, ks in labs.items() if len(ks) > 1)
    check(not clash and not two and any("VIXCLS" in lb for lb in labs),
          f"M7: no label prints two series -- FRED's VIXCLS has its own name beside "
          f"the tape's VIX (clashes {clash}, labels over two keys {two})")


def main() -> int:
    print(f"{LINE}\nT3.5 -- THE MONTHLY'S FRAMES TAKE THE WEEKLY'S BUDGET DISCIPLINE\n{LINE}")
    group_a()
    group_b()
    group_c()
    group_d()
    group_e()
    group_f()
    group_g()
    print(f"\n{LINE}\n{PASS} passed, {FAIL} failed\n{LINE}")
    print("VALIDATION PASSED" if not FAIL else "VALIDATION FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
