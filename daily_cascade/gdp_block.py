"""
THE GDP BLOCK (Batch 7 item 48, lenses 15-20: ST-R6.48e; lenses-group-b, 18 Oct
2026): the GDP lenses as tables and code-written lines in the Monthly's Slow
layers (the order's placement). The figures are altdata/releases_b.py's; nothing
is computed here.

Two sub-sections: "the quarter" (lenses 15-17: final sales to private domestic
purchasers and the contributions, the investment split, GDI less GDP) and
"income, profits and the nowcast" (lenses 18-20). Every table row carries the
lens form: its two percentiles with their n and the 30-point disagreement. No
paragraph is asked for and no chart drawn, so the block adds no prose word to
the Monthly's 10,000 and none of its 12 charts; tables count no words
(stack.section_words). It displaces nothing.

The close carries GDP's one-line read on its release day (releases.
release_day_lines), not this block.
"""

from __future__ import annotations

from typing import Any, Optional

TITLE_QUARTER = "GDP: the private core, the investment split and GDI"
TITLE_INCOME = "GDP: income and saving, profits, and the nowcast path"
NOTE = ("Report-only (the order's flags are lenses 2-4). Each percentile ranks the "
        "figure against its own history; the long window is the release family's.")


def _n(v: Any, dp: int = 1) -> str:
    return "—" if v is None else f"{v:+,.{dp}f}"


def _row(lens_no: str, name: str, period: str, reading: str, lens: dict) -> list[str]:
    from altdata import releases_b                               # noqa: PLC0415
    return [lens_no, name, period, reading] + releases_b.lens_cells(lens)


def quarter_panel(gd: dict) -> dict:
    from altdata import releases_b as rb                         # noqa: PLC0415
    rows, missing, lines = [], [], []
    core = gd["core"]
    q = rb.quarter_name
    gr, fs = core["real_growth"], core["final_sales"]
    for lens_no, x, reading in (
            ("15", gr, f"{_n(gr.get('value'))}% annualised"),
            ("15", fs, f"{_n(fs.get('qq_ann_pct'))}% annualised, {_n(fs.get('yoy_pct'))}% "
                       f"on the year")):
        if x.get("month"):
            rows.append(_row(lens_no, x["name"], q(x["month"]), reading, x["lens"]))
        else:
            missing.append(f"{x['name']}: {rb.printable(x['reason'])}")
    for x in core["contributions"]:
        if x.get("month"):
            rows.append(_row("15", f"Contribution: {x['name']}", q(x["month"]),
                             f"{_n(x['value'], 2)} pp", x["lens"]))
        else:
            missing.append(f"{x['name']}: {rb.printable(x['reason'])}")
    if core.get("sum_pp") is not None:
        lines.append(f"The six contributions sum to {_n(core['sum_pp'], 2)} pp against real "
                     f"growth of {_n(gr.get('value'), 2)}%; the residual "
                     f"{_n(core['residual_pp'], 2)} pp is rounding and the chain's "
                     f"non-additivity.")
    df = core["deflator"]
    if df.get("month"):
        rows.append(_row("15", "GDP deflator", q(df["month"]),
                         f"{_n(df.get('qq_ann_pct'))}% annualised", df["lens"]))
    inv = gd["investment"]
    ai = inv["ai_related"]
    if ai.get("month"):
        rows.append(_row("16", "AI-related: information processing equipment and "
                         "software (nominal)", q(ai["month"]),
                         f"${ai['level_bn']:,.0f}bn; {_n(ai.get('yoy_pct'))}% on the year",
                         ai["lens"]))
    else:
        missing.append(f"AI-related investment: {rb.printable(ai['reason'])}")
    sx = inv["structures"]
    if sx.get("month"):
        if sx.get("ex_dc_bn") is not None:
            reading = (f"${sx['ex_dc_bn']:,.0f}bn ex data centers "
                       f"({_n(sx.get('ex_dc_yoy_pct'))}% on the year)")
        else:
            reading = (f"${sx['level_bn']:,.0f}bn with data centers "
                       f"({_n(sx.get('yoy_pct'))}% on the year)")
            missing.append(f"structures ex data centers: {rb.printable(sx.get('ex_dc_reason'))}")
        rows.append(_row("16", "Nonresidential structures", q(sx["month"]), reading,
                         sx["lens"]))
        if sx.get("ex_dc_bn") is not None:
            lines.append(f"Data-center construction (Census, a spending series, not "
                         f"NIPA's concept: an approximation) ${sx['dc_bn']:,.0f}bn at an "
                         f"annual rate in {q(sx['month'])}.")
    else:
        missing.append(f"nonresidential structures: {rb.printable(sx['reason'])}")
    rs = inv["residential"]
    if rs.get("month"):
        rows.append(_row("16", "Real residential investment", q(rs["month"]),
                         f"{_n(rs.get('qq_ann_pct'))}% annualised", rs["lens"]))
    else:
        missing.append(f"residential investment: {rb.printable(rs['reason'])}")
    gg = gd["gdi_gap"]
    if gg.get("quarter"):
        rows.append(_row("17", "GDI less GDP, % of GDP", q(gg["quarter"]),
                         f"{_n(gg['gap_pct_gdp'], 2)}% ({_n(gg.get('change_4q_pp'), 2)} pp "
                         f"on four quarters)", gg["lens"]))
    else:
        missing.append(f"GDI less GDP: {rb.printable(gg['reason'])}")
    if missing:
        lines.append("Not read: " + "; ".join(missing) + ".")
    sub = {"title": TITLE_QUARTER, "paragraph_wanted": False, "lines": lines,
           "data": {"gdp_lenses_quarter": {k: gd[k] for k in ("core", "investment",
                                                             "gdi_gap")}}}
    if rows:
        from altdata import releases_b                           # noqa: PLC0415
        sub["table"] = {"columns": ["Lens", "Figure", "Period", "Reading"]
                        + releases_b.LENS_COLUMNS, "rows": rows}
        sub["table_note"] = NOTE
    return sub


def income_panel(gd: dict) -> dict:
    from altdata import releases, releases_b as rb               # noqa: PLC0415
    rows, missing, lines = [], [], []
    pf = gd["profits"]
    if pf.get("quarter"):
        rows.append(_row("18", "NIPA profits after tax", rb.quarter_name(pf["quarter"]),
                         f"{_n(pf.get('profits_yoy_pct'))}% on the year", pf["lens"]))
        if pf.get("divergence_pp") is not None:
            lines.append(f"Macro against micro earnings: NIPA profits "
                         f"{_n(pf['profits_yoy_pct'])}% on the year against the S&P 500's "
                         f"trailing EPS {_n(pf['eps_yoy_pct'])}% "
                         f"({releases.month_name(pf['eps_month'])}), a gap of "
                         f"{_n(pf['divergence_pp'])} pp.")
        elif pf.get("eps_reason"):
            missing.append(f"S&P EPS: {rb.printable(pf['eps_reason'])}")
    else:
        missing.append(f"NIPA profits: {rb.printable(pf['reason'])}")
    inc = gd["income"]
    for tag in ("disp_income", "ex_transfers"):
        x = inc[tag]
        if x.get("month"):
            rows.append(_row("19", x["name"], releases.month_name(x["month"]),
                             f"{_n(x.get('yoy_pct'))}% on the year, "
                             f"{_n(x.get('ann_3m_pct'))}% annualised over three months",
                             x["lens"]))
        else:
            missing.append(f"{x['name']}: {rb.printable(x['reason'])}")
    sv = inc["saving_rate"]
    if sv.get("month"):
        rows.append(_row("19", "The saving rate", releases.month_name(sv["month"]),
                         f"{sv['value']:.1f}% ({_n(sv.get('change_12m_pp'))} pp on the "
                         f"year)", sv["lens"]))
    else:
        missing.append(f"the saving rate: {rb.printable(sv['reason'])}")
    missing.append(inc["k_shape_gap"])
    nc = gd["nowcast"]
    if nc.get("state") == "read":
        lines.append(f"GDPNow for {rb.quarter_name(nc['quarter'])}: {nc['updates']} "
                     f"update(s) knowable, from {_n(nc['first'])}% to {_n(nc['latest'])}% "
                     f"({_n(nc['change_pp'])} pp).")
        pr = nc.get("print")
        if pr:
            rows.append(_row("20", "First print less GDPNow's last", rb.quarter_name(
                pr["quarter"]), f"{_n(pr['first_print'])}% against {_n(pr['last_nowcast'])}%"
                f": {_n(pr['miss_pp'], 2)} pp", nc["lens"]))
        else:
            missing.append(f"the print against the nowcast: {rb.printable(nc.get('print_reason'))}")
    else:
        missing.append(f"GDPNow: {rb.printable(nc.get('reason'))}")
    missing.append(nc["nyfed_gap"])
    lines.append("Not read: " + "; ".join(missing) + ".")
    sub = {"title": TITLE_INCOME, "paragraph_wanted": False, "lines": lines,
           "data": {"gdp_lenses_income": {k: gd[k] for k in ("profits", "income",
                                                            "nowcast")}}}
    if rows:
        sub["table"] = {"columns": ["Lens", "Figure", "Period", "Reading"]
                        + rb.LENS_COLUMNS, "rows": rows}
        sub["table_note"] = NOTE
    return sub


def subsections(st, cutoff: str, cfg: Optional[dict] = None) -> list[dict]:
    """The GDP block's two sub-sections for the Monthly's Slow layers."""
    from altdata import releases_b                               # noqa: PLC0415
    gd = releases_b.gdp_lenses(st, cutoff, cfg)
    return [quarter_panel(gd), income_panel(gd)]
