"""
THE LABOUR BLOCK (Batch 7 item 48, lenses 1-6; 6e-releases, 16 Oct 2026): the
employment lenses as two tables and code-written lines. The figures and the three
flags (lenses 2, 3 and 4) are altdata/releases.py's; nothing is computed here.

It is the Monthly's own section, "labour", after Plumbing & rates (filing note 6:
the block changes the stack's section list). Like the Reading chapter it is
declared at the Monthly's cadence only (config/reporting_stack.yaml), built after
assembly and placed by config order, so the close and the Weekly lay out the ten
sections as before. It asks for no paragraph: its claim is code-written from the
flags, so it adds no prose word to the 10,000-word budget, and it draws no chart.
The close carries the employment report's one-line read on its release day
(releases.release_day_lines), not this block.

    subsections(st, cutoff)              the block's sub-sections
    stack_section(st, cutoff, spec, prior)  the Monthly section around them
"""

from __future__ import annotations

from typing import Any, Optional

SECTION_ID = "labour"
TITLE_PAYROLLS = "Payrolls: the cyclical core, breadth and revisions"
TITLE_FLOWS = "Unemployment by flow, the leading pieces and wages"


def _n(v: Any, dp: int = 1, unit: str = "", signed: bool = True) -> str:
    if v is None:
        return "—"
    return f"{v:+,.{dp}f}{unit}" if signed else f"{v:,.{dp}f}{unit}"


def _flag(v: Optional[bool], withheld: Optional[str] = None) -> str:
    if v is True:
        return "FLAG"
    if v is False:
        return "no flag"
    return "withheld" if withheld else "—"


def subsections(st, cutoff: str, em: Optional[dict] = None) -> list[dict]:
    from altdata import releases                                 # noqa: PLC0415
    em = em or releases.employment(st, cutoff)
    mn = releases.month_name
    cy, dif, rv = em["cyclical"], em["diffusion"], em["revisions"]
    rows = []
    if cy.get("month"):
        rows.append(["1. Cyclical core payrolls (private ex education and health)",
                     f"{_n(cy['core_change_k'], 0, 'k')} in {mn(cy['month'])} "
                     f"(three-month average {_n(cy['core_3m_avg_k'], 0, 'k')}); headline "
                     f"{_n(cy['headline_change_k'], 0, 'k')}", "report only"])
    if dif.get("month"):
        rows.append(["2. Diffusion, share of states adding jobs, 1 and 3 months",
                     f"{_n(dif['one_month'], 1, signed=False)} and "
                     f"{_n(dif['three_month'], 1, signed=False)} ({mn(dif['month'])})",
                     _flag(dif.get("flag"), dif.get("withheld"))])
    last = (rv.get("releases") or [None])[-1]
    rows.append(["3. Two-month net revision to payrolls",
                 (f"{_n(last['net_revision'], 0, 'k')} at the {mn(last['month'])} release"
                  if last else "no release with a prior vintage stored"),
                 _flag(rv.get("flag"), rv.get("withheld"))])
    lines = []
    for name, x, rule in (
            ("Diffusion", dif, f"under {dif['threshold']:.0f} for "
                               f"{dif['months_needed']} consecutive months"),
            ("Revisions", rv, f"negative at each of the last {rv['releases_needed']} "
                              f"releases")):
        if x.get("flag") is None and x.get("withheld"):
            lines.append(f"{name}: the flag is withheld -- {x['withheld']}.")
        elif x.get("flag") is True:
            lines.append(f"{name}: FLAG ({rule}).")
    lines.append(f"Diffusion's source: {dif['source']}.")
    lines.append(f"Birth-death contribution: {rv['birth_death']}.")
    first = {"title": TITLE_PAYROLLS, "paragraph_wanted": False,
             "table": {"columns": ["Lens", "Reading", "Flag"], "rows": rows},
             "lines": lines, "data": {"cyclical": cy, "diffusion": dif, "revisions": rv}}
    pl, lead, wg = em["permanent_losers"], em["leading"], em["wages"]
    rows2 = []
    if pl.get("month"):
        rows2.append(["4. Permanent job losers, three-month average against a year earlier",
                      (f"{_n(pl.get('level_3m_avg_k'), 0, 'k', False)} against "
                       f"{_n(pl.get('year_earlier_k'), 0, 'k', False)}: "
                       f"{_n(pl.get('yoy_pct'), 2, '%')} ({mn(pl['month'])})"
                       if pl.get("yoy_pct") is not None else pl.get("withheld") or "—"),
                      _flag(pl.get("flag"), pl.get("withheld"))])
    lf, sahm, cl = em.get("lfpr_prime_age"), em.get("sahm"), em.get("claims") or {}
    if lf:
        rows2.append(["4. Prime-age participation (25-54)",
                      f"{_n(lf['level_pct'], 1, '%', False)}, "
                      f"{_n(lf['change_12m_pp'], 1, ' pp')} on the year ({mn(lf['month'])})",
                      "report only"])
    if sahm:
        rows2.append(["4. The Sahm rule", f"{_n(sahm['value_pp'], 2, ' pp', False)} "
                      f"({mn(sahm['month'])}; the rule's trigger is 0.50)", "report only"])
    if cl.get("initial_4wk") is not None:
        rows2.append(["4. Claims, four-week averages over 13 weeks",
                      f"initial {_n(cl['initial_change_pct'], 1, '%')}, continuing "
                      f"{_n(cl['continuing_change_pct'], 1, '%')} (to {cl['continuing_week']})"
                      + ("; continuing rising with initial flat: the hiring-freeze read"
                         if cl["hiring_freeze_read"] else ""), "report only"])
    for key, label, fmt in (
            ("temp_help", "5. Temporary help services",
             lambda x: f"{_n(x['change_3m_k'], 0, 'k')} over three months, "
                       f"{_n(x['yoy_pct'], 1, '%')} on the year"),
            ("agg_hours", "5. Aggregate weekly hours",
             lambda x: f"{_n(x['ann_3m_pct'], 1, '%')} annualised over three months, "
                       f"{_n(x['yoy_pct'], 1, '%')} on the year"),
            ("quits_rate", "5. JOLTS quits rate",
             lambda x: f"{_n(x['level_pct'], 1, '%', False)}, "
                       f"{_n(x['change_12m_pp'], 1, ' pp')} on the year"),
            ("openings_per_unemployed", "5. Openings per unemployed",
             lambda x: f"{_n(x['ratio'], 2, signed=False)}")):
        x = lead.get(key)
        if x:
            rows2.append([label, f"{fmt(x)} ({mn(x['month'])})", "report only"])
    if wg.get("eci"):
        rows2.append(["6. ECI, wages and salaries (private)",
                      f"{_n(wg['eci']['yoy_pct'], 1, '%')} on the year (quarter to "
                      f"{mn(wg['eci']['quarter_month'])})", "report only"])
    if wg.get("atlanta") or wg.get("ahe"):
        a, h = wg.get("atlanta") or {}, wg.get("ahe") or {}
        rows2.append(["6. Atlanta Fed wage tracker beside average hourly earnings",
                      f"tracker {_n(a.get('pct'), 1, '%', False)}; AHE "
                      f"{_n(h.get('yoy_pct'), 1, '%')} on the year, "
                      f"{_n(h.get('ann_3m_pct'), 1, '%')} annualised over three months",
                      "report only"])
    if wg.get("switcher_premium"):
        sp = wg["switcher_premium"]
        rows2.append(["6. The job-switcher premium (Atlanta Fed)",
                      f"switchers {_n(sp['switchers_pct'], 1, '%', False)} against "
                      f"stayers {_n(sp['stayers_pct'], 1, '%', False)}: "
                      f"{_n(sp['premium_pp'], 1, ' pp')} ({mn(sp['month'])})", "report only"])
    lines2 = []
    if pl.get("flag") is None and pl.get("withheld"):
        lines2.append(f"Permanent job losers: the flag is withheld -- {pl['withheld']}.")
    elif pl.get("flag") is True:
        lines2.append(f"Permanent job losers: FLAG (the three-month average up "
                      f"{pl['threshold_pct']:.0f}% or more on the year).")
    second = {"title": TITLE_FLOWS, "paragraph_wanted": False,
              "table": {"columns": ["Lens", "Reading", "Flag"], "rows": rows2},
              "lines": lines2, "data": {"permanent_losers": pl, "leading": lead,
                                        "wages": wg}}
    return [s for s in (first, second) if (s.get("table") or {}).get("rows")]


def claim(em: dict) -> str:
    fired = [n for n, v in (em.get("flags") or {}).items() if v is True]
    names = {"diffusion": "diffusion under 50 for three months",
             "revisions": "persistent negative payroll revisions",
             "permanent_losers": "permanent job losers rising on the year"}
    if fired:
        return "Labour flags this month: " + "; ".join(names[f] for f in fired) + "."
    held = [n for n, v in (em.get("flags") or {}).items() if v is None]
    tail = (f" ({', '.join(names[h] for h in held)}: withheld, a vintage short)"
            if held else "")
    return f"No labour flag fired this month{tail}."


def stack_section(st, cutoff: str, spec: dict, prior: Optional[dict]) -> dict:
    """The Monthly's labour section in the shape every renderer reads (the
    Reading chapter's form: built after assembly, no paragraph)."""
    from altdata import releases                                 # noqa: PLC0415
    from daily_cascade.stack import _fp, item                    # noqa: PLC0415
    em = releases.employment(st, cutoff)
    subs = subsections(st, cutoff, em)
    items = []
    for ss in subs:
        for row in ss["table"]["rows"]:
            it = item(f"labour:{row[0]}", str(row[0]), 3, tuple(row))
            it["show"] = False
            items.append(it)
    pr = {x["id"]: x for x in (prior or {}).get("sections") or []}.get(SECTION_ID) or {}
    pmarks = {i["key"]: i["fingerprint"] for i in pr.get("items") or []}
    for it in items:
        it["changed"] = bool(prior) and pmarks.get(it["key"]) != it["fingerprint"]
    lines = [] if subs else ["No employment series is stored for the month."]
    return {"id": SECTION_ID, "title": spec.get("title") or "Labour",
            "subtitle": spec.get("monthly_subtitle") or spec.get("subtitle"),
            "depth": spec.get("monthly") or "medium", "depth_reason": None,
            "items": items, "print_items": False, "table": None,
            "subsections": subs, "data": {"labour": {"flags": em.get("flags")}},
            "not_tracked": [], "legend": None, "notes": lines,
            "fingerprint": _fp([(i["key"], i["fingerprint"]) for i in items]),
            "collapsed": False, "unchanged_since": None, "prior_claim": None,
            "claim": claim(em), "paragraphs": [], "trimmed": False, "period": "month",
            "phase_a": [], "prose_wanted": False, "empty": False}
