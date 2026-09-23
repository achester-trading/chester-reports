"""
The 26.7 expression check -- does the SHAPE of the trade match the edge?

26.13: every recommendation states edge type, horizon, catalyst, payoff,
invalidation, portfolio interaction, expression economics. 26.7 decomposes
error into forecast / timing / expression / sizing / execution / exit / process
and forbids downweighting a signal for an EXPRESSION loss. That rule only pays
if expression is recorded as its own dimension at decision time -- otherwise a
right thesis expressed wrongly comes back as a bad signal, and the system
unlearns something true.

This does not stop anything. Every finding is a WARNING with its mechanism
written out, because the mapping from edge to structure is judgement with
exceptions, and a hard gate on judgement is a gate that gets bypassed. What it
does is make the mismatch VISIBLE at the moment the decision is recorded, and
recorded alongside it, so that six months of outcomes can be asked a question
that is otherwise unanswerable: do our timing edges lose because the timing is
wrong, or because we keep expressing them in stock?

-----------------------------------------------------------------------------
WHY THESE RULES AND NOT A SCORE
-----------------------------------------------------------------------------

Each rule names a MECHANISM -- the specific way this shape fails to collect
this edge -- rather than scoring a fit. A score would be a number nobody can
argue with and nobody can check. A mechanism can be wrong, and being wrong in a
way somebody can see is the property worth having.

The rules are deliberately few. 26.17: prefer the simplest implementation that
satisfies the gate, never independently expand scope. These cover the shapes
this system can currently produce -- shares and single options -- and each one
earns its place by naming a loss that would otherwise be misattributed.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from altdata import session       # noqa: E402

# Rough horizon lengths in calendar days, used only to compare a horizon
# against an option's remaining life. Approximate by nature; the check they
# feed is "does this expire before the thesis resolves", which does not need
# precision to be right.
HORIZON_DAYS = {
    "intraday": 1,
    "swing": 21,            # Part 7's 1-3 weeks
    "positional": 90,
    "strategic": 365,
    "structural": 1095,
}

# Edges whose payoff is non-linear in the underlying by definition. Expressing
# them linearly does not reduce the edge, it removes it.
NONLINEAR_EDGES = ("convexity",)

# Edges whose value decays on a clock, so the expression needs a clock too.
DATED_EDGES = ("timing", "positioning")


def _days_to(expiry: Optional[str], asof: Optional[dt.date] = None) -> Optional[int]:
    """Calendar days to an option expiry, or None if there is not one.

    The reference date is the ET TRADING SESSION, via altdata.session, not
    date.today(). An expiry check run after 20:00 ET is already tomorrow in UTC
    and would report one day fewer -- which is precisely how a 1DTE contract
    reads as 0DTE and trips a rule it should not. This is the fourth place that
    bug family reached; it does not get a fifth.
    """
    if not expiry:
        return None
    raw = str(expiry).replace("-", "").strip()
    try:
        d = dt.datetime.strptime(raw, "%Y%m%d").date()
    except ValueError:
        return None
    return (d - (asof or session.session_date_obj())).days


# -----------------------------------------------------------------------------
# THE OPTIONS-PAPER RULES (Paste D piece 5). ALL WARNINGS, like everything else
# here, and the order says so explicitly: binding is Phase 5's job.
# -----------------------------------------------------------------------------
#
# WHEN AN IV PERCENTILE IS HIGH ENOUGH TO WARN. Declared, because the rule is
# Chapter 16.3's and its whole content is a threshold: implied volatility is
# HIGHEST AT THE TROUGH -- above eighty at the 2008 and 2020 lows, mid-thirties to
# high forties at 2011, 2018 and 2022 -- and a two-year at-the-money call costing
# 11% of spot at sixteen-vol costs about 24% at forty. The instinct buys volatility
# at its peak in order to buy direction, and pays for it twice: once in the premium
# and again when it collapses during the recovery, which it does within months of
# every trough on record.
#
# 80 rather than 90 or 95: the 2011, 2018 and 2022 lows sat in the mid-thirties to
# high forties, which is around the 80th percentile of the VIX's own distribution
# (baserate.vix_distribution puts p95 at ~33 over 1990-2026, so the mid-thirties
# are already past it on the index and the single-name equivalent is lower). A
# threshold set at 95 would have stayed quiet through three of the five troughs the
# rule exists for.
IV_PERCENTILE_WARN = 80.0

# The structures whose value is dominated by the volatility purchase, so that
# buying them at a high IV percentile is the error Chapter 16.3 names. A
# deep-in-the-money LEAP is deliberately NOT here: its price is dominated by
# intrinsic value and its extrinsic is a fraction, which is exactly why the chapter
# recommends it as the way to add at a trough.
VOL_BUYING_FAMILIES = (
    "long_straddle", "long_strangle", "reverse_iron_butterfly",
    "reverse_iron_condor", "protective_put", "synthetic_ppn",
)

# The families that are option structures -- the set the Chapter 15 comparison rule
# and the mandatory-family rule apply to. `outright` and the cash-equivalent
# wrappers are not structures whose expression needs defending.
OPTION_FAMILIES = tuple(f for f in (
    "long_straddle", "long_strangle", "long_butterfly", "iron_condor",
    "iron_butterfly", "reverse_iron_butterfly", "collar", "put_spread_collar",
    "put_backspread", "call_backspread", "risk_reversal",
    "broken_wing_butterfly", "reverse_iron_condor", "double_diagonal",
    "diagonal", "vertical_spread", "calendar_spread", "covered_call",
    "cash_secured_put", "protective_put", "buffered_fund", "synthetic_ppn",
    "dual_directional") )


def check(edge_type: str, horizon: str, sec_type: str = "STK",
          expiry: Optional[str] = None, structure: Optional[str] = None,
          asof: Optional[dt.date] = None,
          expression_family: Optional[str] = None,
          leverage_form: Optional[str] = None,
          notional: Optional[float] = None,
          allocation: Optional[float] = None,
          index_comparison: Optional[str] = None,
          iv_percentile: Optional[float] = None) -> list[dict]:
    """Every expression warning this shape earns. Empty list means none.

    `structure` is free text describing a multi-leg shape when there is one
    ("vertical", "risk reversal"); a single leg leaves it None. It is used only
    to tell defined-risk shapes from naked ones, which is the distinction the
    defined-risk rules turn on.
    """
    sec = (sec_type or "STK").upper()
    edge = (edge_type or "").lower()
    hz = (horizon or "").lower()
    dte = _days_to(expiry, asof)
    defined_risk = bool(structure) or sec == "OPT"
    out: list[dict] = []

    def flag(code, message, mechanism, suggestion):
        out.append({"code": code, "severity": "warning", "message": message,
                    "mechanism": mechanism, "suggestion": suggestion})

    # 1. A timing edge in shares. The user's own example, and the cleanest case.
    if edge == "timing" and sec == "STK":
        flag("timing_edge_in_shares",
             f"a timing edge on a {hz} horizon expressed in shares, with no "
             f"defined risk",
             "A timing edge is a claim about WHEN, and shares have no clock. "
             "Being right about the timing pays exactly what being right about "
             "the direction pays, so the edge is collected at zero premium -- "
             "while the adverse path is unbounded and the position survives "
             "being early only if the account does.",
             "a dated structure whose payoff concentrates in the window the "
             "edge names, with risk defined at entry")

    # 2. A carry edge with no time to accrue. The user's second example,
    #    generalised past 0DTE because 3DTE has the same problem.
    if edge == "carry" and sec == "OPT" and dte is not None and dte <= 7:
        flag("carry_edge_no_accrual",
             f"a carry edge expressed in a contract with {dte} day(s) to expiry",
             "Carry is earned per unit time, so its payoff is roughly linear in "
             "the holding period. Inside a week that accrual is small and is "
             "dominated by gamma and pin risk near the strike -- the position's "
             "P&L is then a bet on the terminal price, which is not the edge "
             "claimed.",
             "an expiry long enough that accrual dominates gamma, or a "
             "structure that isolates the carry directly")

    # 3. A convexity edge expressed linearly. Definitional.
    if edge in NONLINEAR_EDGES and sec == "STK":
        flag("convexity_edge_linear_expression",
             "a convexity edge expressed in shares",
             "Shares pay linearly in the underlying. A convexity edge is a "
             "claim that the payoff distribution is mispriced, not that the "
             "level is -- and a linear instrument collects none of that by "
             "construction. This is not a weak expression of the edge; it is a "
             "different trade.",
             "an option structure, where the convexity is the instrument")

    # 4. The expression expires before the thesis resolves.
    if sec == "OPT" and dte is not None and hz in HORIZON_DAYS:
        need = HORIZON_DAYS[hz]
        if dte < need:
            flag("expiry_before_horizon",
                 f"a {hz} horizon (~{need}d) expressed in a contract with "
                 f"{dte}d to expiry",
                 "The thesis is given roughly "
                 f"{need} days to work and the instrument has {dte}. The "
                 "position resolves on the calendar rather than on the thesis, "
                 "so a correct view that arrives late grades as a loss and "
                 "pollutes the forecast record with an expression failure.",
                 f"an expiry beyond the horizon, or a horizon honestly "
                 f"restated as {dte}d")

    # 5. A dealer-positioning edge held across the expiry that CREATES it.
    #    Part 7's weekend rule already says the weekend report must use
    #    POST-EXPIRY dealer state rather than Friday's expiring headline GEX;
    #    this is the same fact applied to a position rather than to a report.
    if edge == "positioning" and hz in ("swing", "positional", "strategic",
                                        "structural"):
        flag("positioning_edge_outlives_its_structure",
             f"a dealer-positioning edge held over a {hz} horizon",
             "The walls and flip levels that generate a positioning edge are "
             "made of open interest, and that open interest expires. Held past "
             "the expiry cycle that built it, the position is still on but the "
             "structure that justified it is gone -- and nothing in the "
             "position tells you the day that happened. This is the same fact "
             "as the weekend rule's insistence on POST-EXPIRY dealer state.",
             "size and date the expression to the expiry cycle that generates "
             "the level, and re-derive rather than hold through it")

    # 6. An information edge held long past the information being public.
    if edge == "information" and hz in ("strategic", "structural"):
        flag("information_edge_long_horizon",
             f"an information edge held over a {hz} horizon",
             "An information edge is the gap between what you know and what is "
             "priced, and it closes when the information becomes public. Over "
             f"a {hz} horizon the holding period is mostly AFTER that gap has "
             "closed, so most of the risk carried is not the edge -- it is "
             "whatever else moves the instrument in the meantime.",
             "a horizon matched to the information's diffusion, or an explicit "
             "second thesis for the period after it is priced")

    _options_paper_rules(flag, sec, expression_family, leverage_form,
                         notional, allocation, index_comparison,
                         iv_percentile)

    return out


def _options_paper_rules(flag, sec: str, expression_family: Optional[str],
                         leverage_form: Optional[str],
                         notional: Optional[float],
                         allocation: Optional[float],
                         index_comparison: Optional[str],
                         iv_percentile: Optional[float]) -> None:
    """The four rules from Options as Expression. Warnings, every one.

    Separated into its own function for one reason: these four are about what the
    decision RECORDED, while the rules above are about whether the shape collects
    the edge. Mixing them would make the module's own subject unclear, and the
    second set becomes binding at a different time -- Phase 5 -- from the first.
    """
    fam = (expression_family or "").lower() or None

    # 5. AN OPTIONS DECISION WITH NO FAMILY RECORDED. 26.7 forbids downweighting a
    #    signal for an expression loss, and that rule cannot be applied to a
    #    decision whose expression was never written down: the loss comes back as a
    #    bad signal and the system unlearns something true.
    if sec == "OPT" and not fam:
        flag("expression_family_unrecorded",
             "an options decision with no expression_family recorded",
             "26.7 decomposes error into forecast / timing / EXPRESSION / sizing, "
             "and forbids downweighting a signal for an expression loss. That rule "
             "is unapplicable to a decision whose expression was never recorded: "
             "the loss returns as evidence against the signal, and the system "
             "unlearns something true.",
             "name the structure from the register's closed vocabulary -- the "
             "point of a closed list is that six months of outcomes can be "
             "grouped by it")

    # 6. LEVERAGE WITH NO FORM RECORDED, when the notional exceeds the allocation.
    #    16.1: leverage is measured in RISK, never notional -- so the register's
    #    size is already right and this is not a sizing check. It is a check that
    #    the INSTRUMENT is named, because the forms differ in the one dimension
    #    risk cannot express: whether a margin call can arrive.
    if (notional is not None and allocation is not None and allocation > 0
            and notional > allocation and not (leverage_form or "").strip()):
        flag("leverage_form_unrecorded",
             f"notional {notional:,.0f} exceeds the allocation "
             f"{allocation:,.0f} with no leverage_form recorded",
             "Leverage is a multiplier on a decision already made, and the forms "
             "differ in what risk cannot say: a deep-in-the-money call with a "
             "defined worst case and a margin loan with a call risk are the same "
             "size in the register and are not the same decision. Without the form "
             "there is no way to ask later which kind of leverage cost the book "
             "money.",
             "name the form -- futures, LEAPS, call spread, short box, margin -- "
             "or `none` if the notional is levered by the structure itself")

    # 7. A STRUCTURE THAT DOES NOT STATE WHAT IT MUST BEAT. Chapter 15's rule, and
    #    Chapter 15.5's finding is the reason it bites: the 50/50 index-and-bills
    #    mix beats the buffered fund, the principal-protected note and the reverse
    #    iron butterfly on expected value in all four asset classes at twelve
    #    months. A structure is chosen over the index, so the comparison is the
    #    decision -- and an unstated comparison is usually an unmade one.
    if fam in OPTION_FAMILIES and not (index_comparison or "").strip():
        flag("index_comparison_unstated",
             f"a {fam} with no index-outright comparison stated",
             "Chapter 15 prices every structure against holding the index and "
             "against a 50/50 index-and-bills mix, and most structures lose to the "
             "mix on expected value at twelve months. The structure is being chosen "
             "OVER the index, so the comparison is the decision itself; unstated, "
             "it is usually unmade.",
             "state what this structure must beat and by how much -- 'beats "
             "outright below 4,900 and loses above 5,400' is a sentence the "
             "outcome can be checked against")

    # 8. BUYING LONG-DATED OPTIONALITY AT A HIGH IV PERCENTILE. Chapter 16.3.
    if (iv_percentile is not None and iv_percentile >= IV_PERCENTILE_WARN
            and fam in VOL_BUYING_FAMILIES):
        flag("long_vol_at_high_iv",
             f"buying {fam} with implied volatility at the "
             f"{iv_percentile:.0f}th percentile",
             "Implied volatility is HIGHEST AT THE TROUGH -- above eighty at the "
             "2008 and 2020 lows, mid-thirties to high forties at 2011, 2018 and "
             "2022. A two-year at-the-money call costing 11% of spot at sixteen-vol "
             "costs about 24% at forty. The instinct buys volatility at its peak in "
             "order to buy direction and pays for it twice: once in the premium, "
             "and again when it collapses during the recovery, which it does within "
             "months of every trough on record.",
             "a spread or a risk reversal, which sell the expensive leg -- or a "
             "deep-in-the-money LEAP, whose price is intrinsic value with the "
             "extrinsic a fraction, which is why the chapter names it as the way "
             "to add at a trough")


def summarise(warnings: list[dict]) -> str:
    """One line saying whether the shape was questioned, for a summary row."""
    if not warnings:
        return "expression: no mismatch flagged"
    return (f"expression: {len(warnings)} warning(s) -- "
            + ", ".join(w["code"] for w in warnings))


def format_warnings(warnings: list[dict], indent: str = "    ") -> str:
    """The printed form. Rationale always shown -- a code alone teaches nothing."""
    if not warnings:
        return f"{indent}no expression mismatch flagged for this shape"
    out = []
    for w in warnings:
        out.append(f"{indent}[{w['severity'].upper()}] {w['code']}")
        out.append(f"{indent}  {w['message']}")
        out.append(f"{indent}  why : {w['mechanism']}")
        out.append(f"{indent}  fix : {w['suggestion']}")
    return "\n".join(out)
