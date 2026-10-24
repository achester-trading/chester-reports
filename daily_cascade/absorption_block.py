"""
The Monthly's signal-triage blocks -- ST-6 (docs/change-order-signal-triage-2026-
09-25.md section 7; st-t1-rest, 18 Oct 2026).

    rate_machine(st, now)          Plumbing & rates: the Rate machine summary
    duration_absorption(st, now)   Plumbing & rates: Duration Absorption (<= 18 lines)
    cheap_unloved(st, now)         Slow layers: Cheap-and-Unloved (<= 10 lines)
    factor_lines(st, now)          Slow layers: Factor I, III, IV and V lines
    china_status(st, now)          Slow layers: the China panel's status lines
    subsections(st, now, where)    the sub-sections for "plumbing" or "slow"

Every line reads the store as of the cutoff and fetches nothing. A line whose
input is stored prints its value and its as-of; one whose input is not stored
prints "NOT AVAILABLE" with the key and its source named; one rule 30 removed the
input of prints "NOT TRACKED" with the manual key it named. Every block is lines
and asks no paragraph, so none adds a word to the Monthly's budget or a chart to
its cap. Every flag here is display and modifier only; the withdrawn rates driver
cell (ruled 30 Sep 2026) is said to be withdrawn, never computed.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from altdata.numeral_audit import ordinal

log = logging.getLogger(__name__)

NA = "NOT AVAILABLE"
NT = "NOT TRACKED"
# SR-16's amendment (signal-triage Batch 12, item 60.5; a53, 20 Oct 2026): the
# neocloud / AI-infrastructure credit watch line, a listed gap under F2 -- the bond
# prices of the neoclouds and their peers have no keyless source, and no by-hand
# line is added.
NEOCLOUD_LINE = ("Neocloud / AI-infrastructure credit (the neoclouds' bonds and "
                 "peers): NOT TRACKED (item 60, F2: no keyless source; a listed gap "
                 "beside the hyperscaler anchors)")
# Batch 14 item 65 (a57, 23 Oct 2026; F2): the AI-credit watch (CoreWeave, Oracle,
# SpaceX), a listed gap beside it -- config/ai_trade.yaml's line, no by-hand path.
AI_CREDIT_LINE = ("AI credit (the CDS and bond spreads of CoreWeave, Oracle and "
                  "SpaceX): NOT TRACKED (item 65, F2: no keyless source; a listed gap "
                  "beside SR-16's neocloud line, no by-hand line)")
CAPS = {"Duration Absorption": 18, "Cheap-and-Unloved": 10}
RATE_TITLE = "Rate machine summary"
DA_TITLE = "Duration Absorption"
CU_TITLE = "Cheap-and-Unloved"
FACTOR_TITLE = "Factor lines (I, III, IV, V)"
CHINA_TITLE = "China panel: input status"
DRIVER_WITHDRAWN = ("the rates driver cell: withdrawn by the ruling of 30 Sep 2026 "
                    "(its gate failed twice; docs/ledgers/rates-driver-2026-09*.md), "
                    "so no cell prints; the attribution block reads the models instead")
# SR-21's gate FAILed (docs/ledgers/sr-21-ledger-2026-10-18.md) and the ruling of
# 18 Oct holds its features to descriptive: they print, and modify nothing.
SR21_DESCRIPTIVE = "descriptive only (SR-21's gate failed; ruling of 18 Oct)"


def latest(st, key: str, now: str, inst: Optional[str] = None
           ) -> Optional[tuple[str, float]]:
    """(day, value) of the newest observation knowable at now, or None."""
    if st is None:
        return None
    try:
        r = st.latest_as_of(key, now, inst)
    except Exception:                                           # noqa: BLE001
        return None
    if not r or r.get("value_num") is None:
        return None
    return str(r["observed_at"])[:10], float(r["value_num"])


def ago(st, key: str, now: str, months: int, inst: Optional[str] = None
        ) -> Optional[tuple[str, float]]:
    """The observation about `months` months before the latest one."""
    try:
        rows = st.as_of(key, now, inst)
    except Exception:                                           # noqa: BLE001
        return None
    pts = sorted((str(r["observed_at"])[:10], float(r["value_num"])) for r in rows
                 if r.get("value_num") is not None)
    if not pts:
        return None
    y, m = int(pts[-1][0][:4]), int(pts[-1][0][5:7]) - months
    target = f"{y + (m - 1) // 12:04d}-{(m - 1) % 12 + 1:02d}"
    hit = [p for p in pts if p[0][:7] <= target]
    return hit[-1] if hit else None


def na(label: str, key: str, source: str) -> str:
    return f"{label}: {NA} ({key}; {source})"


def nt(label: str, key: str) -> str:
    from altdata import absorption                              # noqa: PLC0415
    return f"{label}: {NT} (rule 30; the order's input {absorption.NOT_TRACKED.get(key, key)})"


def line(st, now: str, label: str, key: str, fmt: Callable[[float], str],
         source: str, inst: Optional[str] = None) -> str:
    x = latest(st, key, now, inst)
    return f"{label}: {fmt(x[1])} (as of {x[0]})" if x else na(label, key, source)


def bn(v: float) -> str:
    return f"${v / 1e9:,.0f}bn"


def pct(v: float) -> str:
    return f"{v:.1f}%"


def bp(v: float) -> str:
    return f"{v:+.0f} bp"


def flag(v: float) -> str:
    return "ON" if v >= 0.5 else "off"


# ---------------------------------------------------------------------------
def rate_machine(st, now: str) -> list[str]:
    out = [f"Driver: {DRIVER_WITHDRAWN}."]
    if st is None:
        # Never open a default store a caller did not name (a code gate's rule).
        out.append(na("Attribution", "calc.attr_*", "altdata/rates_attribution.py"))
    try:
        if st is None:
            raise LookupError("no store")
        from altdata import rates_attribution as ra             # noqa: PLC0415
        b = ra.build(now, store=st)
        ag = ((b.get("windows") or {}).get("20") or {}).get("agreement") or {}
        out.append(f"Attribution, 20 observations: {ag.get('text') or 'not assessable'} "
                   f"(altdata/rates_attribution.py; descriptive).")
    except LookupError:
        pass
    except Exception:                                           # noqa: BLE001
        out.append(na("Attribution", "calc.attr_*", "altdata/rates_attribution.py"))
    d = latest(st, "calc.deanchor", now)
    rp = latest(st, "calc.be5y5y_range_pos", now)
    out.append(f"DEANCHOR: {flag(d[1])} (as of {d[0]}); the 5y5y at its "
               f"{ordinal(rp[1])} percentile since 2010" if d and rp else
               na("DEANCHOR", "calc.deanchor", "FRED T5YIFR, Fed Board CIE, UMich"))
    g = latest(st, "calc.fed_mkt_gap_12m", now)
    c = latest(st, "calc.cred_stress", now)
    out.append((f"CRED_STRESS: {flag(c[1])} on the 12-month leg (gap {bp(g[1])}, as of "
                f"{g[0]}); the next-meeting leg {NT} (rule 30; "
                f"by-hand key fed_signalled_direction, dropped 16 Oct)" if g and c else
                na("CRED_STRESS", "calc.fed_mkt_gap_12m",
                   "fed funds futures (fedfunds.futures_price) and FRED FEDTARMD"))
               + f"; {SR21_DESCRIPTIVE}")
    out.append(line(st, now, "Venues against the futures, next meeting",
                    "calc.pm_disagree_fed", lambda v: f"{v:+.0f} points",
                    "prediction markets and fed funds futures") + f"; {SR21_DESCRIPTIVE}")
    return out


def duration_absorption(st, now: str) -> list[str]:
    out = ["Supply:",
           line(st, now, "  Net supply, 12 months (issuance less the Fed's Treasuries)",
                "calc.net_supply_12m_gdp", lambda v: f"{v:.2f}% of GDP",
                "MSPD (fiscaldata), FRED TREAST and GDP"),
           line(st, now, "  The same in dollars", "calc.net_supply_12m", bn,
                "MSPD (fiscaldata), FRED TREAST"),
           f"  {nt('Projection, 12 months', 'calc.net_supply_proj_12m')}",
           f"  {nt('AI share of long IG issuance', 'calc.ai_long_share')}",
           "Absorbers:"]
    s0, s1 = latest(st, "fred.soma_treasuries", now), ago(st, "fred.soma_treasuries", now, 12)
    out.append(f"  The Fed's Treasuries, 12 months: {bn((s0[1] - s1[1]) * 1e6)} (as of "
               f"{s0[0]})" if s0 and s1 else
               "  " + na("The Fed's Treasuries", "fred.soma_treasuries", "FRED TREAST"))
    o, p = latest(st, "calc.tic_official_12m", now), latest(st, "calc.tic_private_12m", now)
    out.append(f"  Foreign holders, 12 months: official {bn(o[1])}, private {bn(p[1])} "
               f"(as of {o[0]})" if o and p else
               "  " + na("Foreign holders", "calc.tic_official_12m", "TIC Major Foreign Holders"))
    t, os_, cs = (latest(st, k, now) for k in ("calc.foreign_ust_share_lt",
                                               "calc.tic_official_share",
                                               "calc.tic_custodial_share"))
    out.append(f"  Treasuries' share of net foreign long-term buying {pct(t[1])}; "
               f"official {pct(os_[1])} and custodial {pct(cs[1])} of holdings (as of "
               f"{t[0]})" if t and os_ and cs else
               "  " + na("Foreign composition", "calc.foreign_ust_share_lt",
                         "TIC flows and Major Foreign Holders"))
    ch = latest(st, "tic.holdings_by_country", now, "China, Mainland")
    out.append(f"  China (TIC row, an upper bound: Euroclear custody, G-9): {bn(ch[1])} "
               f"(as of {ch[0]})" if ch else
               "  " + na("China", "tic.holdings_by_country", "TIC Major Foreign Holders"))
    out.append("  " + line(st, now, "Japan's holdings, read through the hedged carry a "
                           "Japanese buyer earns on 10-year Treasuries",
                           "calc.jp_hedged_carry", lambda v: f"{v:+.2f}%",
                           "calc; FRED DGS10, DTB3, OECD Japan 3-month (ST-5)"))
    out.append("  " + line(st, now, "Domestic price-sensitive residual, 12 months",
                           "calc.priv_residual_12m", bn, "MSPD, TREAST, TIC"))
    out.append("Price:")
    tps = []
    for lab, key in (("ACM", "acm.term_premium_10y"), ("Kim-Wright", "fred.term_premium_kw"),
                     ("SF Fed", "sffed.term_premium_10y"), ("DKW real", "dkw.real_term_premium_10y")):
        x = latest(st, key, now)
        tps.append(f"{lab} {x[1]:+.2f}% ({x[0]})" if x else f"{lab} {NA} ({key})")
    out.append("  Ten-year term premia: " + "; ".join(tps))
    out.append("  " + line(st, now, "BBB less AA OAS", "calc.aa_bbb_oas_diff", bp,
                           "FRED BAMLC0A4CBBB, BAMLC0A2CAA"))
    out.append("Read:")
    out.append(f"  {DRIVER_WITHDRAWN[0].upper() + DRIVER_WITHDRAWN[1:]}.")
    out.append("  " + abs_stress_line(st, now) + "; "
               + line(st, now, "ABS_FRAGILITY (display only)", "calc.abs_fragility",
                      flag, "TIC"))
    return out[:CAPS[DA_TITLE]]


def abs_stress_line(st, now: str) -> str:
    """ABS_STRESS over the coupon tenors' newest auctions: ON if any is, with its
    firing base rate beside it and its modifier effect suspended (ruling 3 of
    18 Oct 2026)."""
    from altdata import absorption                              # noqa: PLC0415
    tail = (f"; {absorption.abs_stress_base_rate()} (SR-22 ledger); "
            f"{absorption.ABS_STRESS_SUSPENDED}")
    try:
        insts = st.instruments("calc.abs_stress")
    except Exception:                                           # noqa: BLE001
        insts = []
    xs = [x for x in (latest(st, "calc.abs_stress", now, i) for i in insts) if x]
    if not xs:
        return na("ABS_STRESS", "calc.abs_stress", "TreasuryDirect auctions") + tail
    newest = max(d for d, _ in xs)
    return (f"ABS_STRESS: {'ON' if any(v >= 0.5 for _, v in xs) else 'off'} across "
            f"{len(xs)} coupon tenors (newest {newest}; ST-7's gate FAILed: stress flag "
            f"only){tail}")


def cheap_unloved(st, now: str) -> list[str]:
    out = [na("Bond allocation", "calc.bond_alloc", "Fed Z.1; ST-8"),
           na("Bond/cash split", "calc.bond_cash_split", "Fed Z.1; ST-8"),
           "Valuation strip: " + "; ".join(
               f"{a} {NA} (calc.val_z_{a}; ST-8)" for a in ("gold", "spx", "ust", "cmdty")),
           na("Commodities over gold", "calc.cmdty_gold_ratio", "ST-8"),
           "A-3's conditions:",
           "  bond allocation in its bottom decile: not determinable (calc.bond_alloc)",
           "  Treasuries z <= -0.5: not determinable (calc.val_z_ust)",
           "  " + abs_stress_line(st, now),
           "  the driver = term_premium: not determinable (the cell is withdrawn)",
           "Gold's z carries zero rebalancing weight while Factor V is active."]
    return out[:CAPS[CU_TITLE]]


def factor_lines(st, now: str) -> list[str]:
    return [
        "Factor I (funding):",
        "  " + line(st, now, "Hyperscalers' cash flow over capex", "calc.self_fund_ratio",
                    lambda v: f"{v:.2f}x", "EDGAR XBRL frames"),
        "  " + line(st, now, "Their net debt, year on year", "calc.hs_netdebt_12m", bn,
                    "EDGAR XBRL instant frames"),
        "  " + line(st, now, "BBB less AA OAS", "calc.aa_bbb_oas_diff", bp, "FRED ICE BofA"),
        f"  {nt('AI share of long IG issuance', 'calc.ai_long_share')}",
        f"  {NEOCLOUD_LINE}",
        f"  {AI_CREDIT_LINE}",
        "  " + line(st, now, "Memory line: Micron inventory days", "calc.mu_inv_days",
                    lambda v: f"{v:.0f} days", "EDGAR company concepts"),
        "Factor III: " + na("the oil buffer", "calc.oil_buffer_state",
                            "EIA weekly stocks; not built"),
        "Factor IV:",
        *funding_lines(st, now),
        "  " + na("US against the rest of the world", "calc.em_rel",
                  "ST-8, display only until its gate"),
        "  " + line(st, now, "External financing: Treasuries' share of net foreign "
                    "long-term buying", "calc.foreign_ust_share_lt", pct, "TIC flows"),
        "Factor V: " + line(st, now, "central-bank gold, 12 months", "calc.cb_gold_12m",
                            lambda v: f"{v:,.0f} t", "IMF IFS")
        + "; " + line(st, now, "foreign official Treasuries, 12 months",
                      "calc.tic_official_12m", bn, "TIC"),
    ]


def funding_lines(st, now: str) -> list[str]:
    """ST-5's Factor IV lines: the yen stack, the yuan, the two tells and the two
    candidate contradiction rows (G-10). Each line is populated with its as-of or
    marked NOT AVAILABLE / NOT TRACKED with its key and source."""
    from altdata import funding_currency as fc                  # noqa: PLC0415
    fd, f60 = latest(st, "calc.jp_front_diff", now), latest(st, "calc.jp_front_diff_60d", now)
    rv = latest(st, "calc.usdjpy_rvol_20d", now)
    uw = latest(st, "calc.jpy_unwind", now)
    out = [
        "  " + (f"Yen front differential (US 2-year less the JGB 2-year): {bp(fd[1])}, "
                f"{bp(f60[1])} over 60 sessions (as of {fd[0]})" if fd and f60 else
                na("Yen front differential", "calc.jp_front_diff",
                   "calc; FRED DGS2 and MoF JGB 2-year")),
        "  " + line(st, now, "Yen positioning (CFTC net non-commercial, z over three "
                    "years)", "calc.jpy_pos_z", lambda v: f"{v:+.2f}", "calc; CFTC COT"),
        "  " + line(st, now, "Hedged carry for a Japanese buyer of 10-year Treasuries",
                    "calc.jp_hedged_carry", lambda v: f"{v:+.2f}%",
                    "calc; FRED DGS10, DTB3, OECD Japan 3-month"),
        "  " + (f"Yen unwind tell: {flag(uw[1])} (as of {uw[0]}; USDJPY 20-session vol "
                f"{rv[1]:.1f}%)" if uw and rv else
                na("Yen unwind tell", "calc.jpy_unwind", "calc; USDJPY closes")),
        "  " + line(st, now, "Yuan fix against the previous onshore close",
                    "calc.cny_fix_dev", bp, "calc; CFETS fix and CNY=X"),
    ]
    out.append("  " + deval_line(st, now))
    try:
        cands = fc.candidate_rows(st, now) if st is not None else []
    except Exception:                                           # noqa: BLE001
        log.warning("candidate contradiction rows faulted", exc_info=True)
        cands = []
    for c in cands or [{"id": p["id"], "legs": p["legs"], "magnitude": None}
                       for p in fc.config()["candidate_contradictions"]["pairs"]]:
        lab = f"Candidate row {c['id']} (G-10: declared, not in the table)"
        out.append("  " + (f"{lab}: gap z {c['magnitude']:+.2f} over {c['n']} dates "
                           f"(as of {c['last']})" if c.get("magnitude") is not None else
                           na(lab, " and ".join(c["legs"]), "contradictions.gap_z")))
    return out


def deval_line(st, now: str) -> str:
    """SR-4's tell as ruling 6 of 18 Oct prints it: "2 of 3 legs tracked", each
    leg's state, the untracked leg's key named, and no verdict word while a leg is
    not tracked (funding_currency.verdict_allowed)."""
    from altdata import funding_currency as fc                  # noqa: PLC0415
    cfg = fc.config()
    n, total = fc.legs_tracked(cfg), fc.LEGS_TOTAL
    try:
        lg = fc.deval_legs(st, now, cfg) if st is not None else None
    except Exception:                                           # noqa: BLE001
        log.warning("devaluation tell legs faulted", exc_info=True)
        lg = None
    third = (f"leg 3, state banks selling dollars: {NT} (rule 30; by-hand key "
             f"{fc.THIRD_LEG_KEY}, dropped 16 Oct)")
    head = f"Devaluation tell: {n} of {total} legs tracked"
    if lg is None:
        return (na(head, "calc.deval_tell",
                   "calc; its legs from the CFETS fix, CNH and CNY=X") + f"; {third}")
    y = cfg["yuan"]

    def held(v: bool) -> str:
        return "held" if v else "not held"
    body = (f"{head} (as of {lg['day']}): leg 1, the fix's lean gone: "
            f"{held(lg['leg1'])} (5-observation mean {bp(lg['lean_bp'])}, held at or "
            f"above {bp(y['lean_gone_bp'])}); leg 2, the CNH-CNY gap wide and widening: "
            f"{held(lg['leg2'])} ({bp(lg['gap_bp'])}, {bp(lg['widen_bp'])} over "
            f"{y['gap_widen_obs']} observations; held at {bp(y['gap_weak_bp'])} and "
            f"{bp(y['gap_widen_bp'])}); {third}")
    if not fc.verdict_allowed(cfg):
        return body + "; no verdict prints while a leg is not tracked (ruling of 18 Oct)"
    return body + f"; the tell: {flag(1.0 if lg['leg1'] and lg['leg2'] else 0.0)}"


def china_status(st, now: str) -> list[str]:
    def st_line(label: str, key: str, source: str, inst: Optional[str] = None) -> str:
        x = latest(st, key, now, inst)
        return f"{label}: stored, as of {x[0]}" if x else na(label, key, source)
    return ["The panel's assembly is deferred (Appendix C); its inputs:",
            st_line("SAFE reserves", "safe.official_reserves_total", "SAFE"),
            st_line("International investment position", "safe.iip_net", "SAFE"),
            st_line("TIC China row", "tic.holdings_by_country", "TIC", "China, Mainland"),
            st_line("CNY fix", "cfets.cny_fix", "CFETS"),
            st_line("CGB 10-year", "cfets.cgb_10y", "CFETS"),
            st_line("US-China 10-year spread", "calc.uscn_10y_spread",
                    "calc; FRED DGS10 and CFETS (ST-5)"),
            st_line("Offshore yuan", "cnh.usdcnh", "CNH close"),
            st_line("CNH-CNY gap (the order's calc.cnh_cny_gap)", "calc.cnh_cny_bp",
                    "calc; CNH and CNY=X closes")]


def _sub(title: str, lines: list[str], note: str) -> dict:
    return {"title": title, "lines": lines, "paragraph_wanted": False,
            "not_tracked": [], "table_note": note,
            "data": {"lines": len(lines), "cap": CAPS.get(title)}}


def subsections(st, now: str, where: str) -> list[dict]:
    """The ST-6 sub-sections for the Monthly's Plumbing & rates ("plumbing") or
    Slow layers ("slow"). Never raises: a fault costs these lines only."""
    note = ("Lines read from the store as of the cutoff; nothing fetched. NOT "
            "AVAILABLE names the key and its source; NOT TRACKED names the manual key "
            "rule 30 removed. Display and modifier only (signal-triage ST-6).")
    try:
        if where == "plumbing":
            return [_sub(RATE_TITLE, rate_machine(st, now), note),
                    _sub(DA_TITLE, duration_absorption(st, now), note)]
        out = [_sub(CU_TITLE, cheap_unloved(st, now), note),
               _sub(FACTOR_TITLE, factor_lines(st, now), note),
               _sub(CHINA_TITLE, china_status(st, now), note)]
    except Exception:                                           # noqa: BLE001
        log.warning("the ST-6 blocks faulted", exc_info=True)
        return []
    # SR-1's style-regime panel, rendered because its gate passed (ST-8); a fault
    # costs its lines only.
    try:
        from daily_cascade import style_block                   # noqa: PLC0415
        out.insert(2, style_block.subsection(st, now))
    except Exception:                                           # noqa: BLE001
        log.warning("the style-regime panel faulted", exc_info=True)
    return out


def lines(st, now: Optional[str]) -> list[str]:
    from altdata import session                                 # noqa: PLC0415
    now = now or session.utc_iso(timespec="microseconds")
    out = []
    for where in ("plumbing", "slow"):
        for s in subsections(st, now, where):
            out += [f"== {s['title']}"] + s["lines"]
    return out
