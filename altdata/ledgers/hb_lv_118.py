"""
Item 118's divergence ledger (signal-triage Batch 22, the order's 100; A128, 6 Nov
2026): the backtest the flag's rights wait on, through the event-study utility
(altdata/event_study.py, Batch 16 item 91(a)).

    python -m altdata.ledgers run hb-lv-divergence [--source public|store]

PRE-REGISTERED before this code: docs/ledgers/hb-lv-divergence-preregistration-
2026-11.md, whose SHA-256 config/crowding.yaml and tools/validate_item_116.py hold.

THE EVENT is the flag, in its one definition (altdata/hb_lv.flag): the S&P 500 up
0.5% or more on the session while SPHB/SPLV is down 2% or more. THE MEASURES are
the S&P 500's +1, +5 and +20 session returns, beside the same figures over every
session of the window (the base rate). The first row is 4 Nov 2026, the order's
day, written only when V-100a holds in the series (the S&P up at least 0.5% that
day). No pass rule is stated, so none is set. Nothing here grants a right.
"""

from __future__ import annotations

from .. import event_study as es
from . import NO_GATE, fmt

ITEM = "hb-lv-divergence"
TITLE = ("Item 118's high-beta / low-vol divergence: the S&P 500 up 0.5% while "
         "SPHB/SPLV falls 2%, and the S&P's next 1, 5 and 20 sessions")
PREREG = "docs/ledgers/hb-lv-divergence-preregistration-2026-11.md"
PASS_RULE = ("none stated -- the order names no pass rule (\"the flag earns rights only "
             "after an event-study backtest\"); this first edition is that backtest "
             "and sets none (pre-registered: " + PREREG + ")")
RIGHTS = ("None: the ledger grants nothing. The flag prints with \"no rights until the "
          "backtest\"; this backtest enters no composite, flag table, the T&B intake "
          "queue or the market-state object.")
HORIZONS = (1, 5, 20)
FIRST_ROW = "2026-11-04"
OVERLAP = 20

SERIES_PUBLIC = {"spx": ("yahoo", "^GSPC"), "sphb": ("yahoo", "SPHB"),
                 "splv": ("yahoo", "SPLV")}
SERIES_STORE = {"spx": "yfinance.mkt_gspc", "sphb": "yfinance.mkt_sphb",
                "splv": "yfinance.mkt_splv"}


def flags(spx: list, sphb: list, splv: list) -> dict:
    """{session: (S&P change %, ratio change %, fired)} on the sessions the ratio
    and the index both carry, from the ETFs' first common session."""
    from ..hb_lv import flag                                    # noqa: PLC0415
    ratio = es.ratio(sphb, splv)
    rchg = dict(es.daily_change(ratio))
    first = ratio[0][0] if ratio else "9999"
    schg = {d: v for d, v in es.daily_change(spx) if d >= first}
    out = {}
    for d in sorted(set(rchg) & set(schg)):
        s, r = 100.0 * schg[d], 100.0 * rchg[d]
        out[d] = (s, r, bool(flag(s, r)))
    return out


def _p(v, pending: bool = False):
    if v is None and pending:
        return "pending"
    return fmt(None if v is None else 100.0 * v, 2, pct=True)


def _share(v):
    return "n/a" if v is None else f"{100.0 * v:.0f}%"


def study(series: dict) -> dict:
    spx, sphb, splv = series["spx"], series["sphb"], series["splv"]
    fl = flags(spx, sphb, splv)
    evs = [d for d, (_, _, f) in fl.items() if f]
    res = es.study(spx, evs, HORIZONS)
    first = min(fl) if fl else None
    base = es.base_rate(spx, HORIZONS, first=first or "")
    as_of = max(fl) if fl else spx[-1][0]
    pos = {d: i for i, (d, _) in enumerate(spx)}
    overl, prev = set(), None
    for d in evs:
        if prev is not None and pos[d] - pos[prev] <= OVERLAP:
            overl.add(d)
        prev = d
    v100 = fl.get(FIRST_ROW)
    if v100 is None:
        v100_line = (f"V-100a: {FIRST_ROW} is not in the series yet; the order's first row "
                     f"is not written.")
    elif v100[2]:
        v100_line = (f"V-100a holds: on {FIRST_ROW} the S&P 500 closed {v100[0]:+.2f}% "
                     f"(at least +0.5%) and SPHB/SPLV {v100[1]:+.2f}% (at most -2%); the "
                     f"order's first row is the backtest's own event for that session.")
    else:
        v100_line = (f"V-100a fails: on {FIRST_ROW} the S&P 500 closed {v100[0]:+.2f}% and "
                     f"SPHB/SPLV {v100[1]:+.2f}%; the flag did not fire, so the order's "
                     f"first row is NOT written.")
    episodes = []
    for r in res["rows"]:
        d = r["event"]
        s, rr, _ = fl[d]
        episodes.append({"session": d, "spx_chg_pct": round(s, 4),
                         "ratio_chg_pct": round(rr, 4),
                         "mark": ("the order's day (V-100a checked)" if d == FIRST_ROW
                                  else "backtest event"),
                         "overlaps_prior_event": d in overl,
                         **{f"spx_fwd_{h}": r[h] for h in HORIZONS}})
    body = [v100_line, "",
            f"**{len(evs)} events** from {first} to {as_of} ({len(fl)} sessions screened); "
            f"{len(overl)} fall within {OVERLAP} sessions of the event before them, so "
            f"their forward windows share days.", "",
            "| Horizon | Events: n | Mean | Median | Share negative | All sessions: n | "
            "Mean | Median | Share negative |",
            "|---|---|---|---|---|---|---|---|---|"]
    for h in HORIZONS:
        a, b = res["average"][h], base[h]
        body.append(f"| +{h} | {a['n']} | {_p(a['mean'])} | {_p(a['median'])} | "
                    f"{_share(a['share_negative'])} | {b['n']} | {_p(b['mean'])} | "
                    f"{_p(b['median'])} | {_share(b['share_negative'])} |")
    pend = {h: res["pending"][h] for h in HORIZONS if res["pending"][h]}
    if pend:
        body += ["", "Pending (window not closed, not counted): "
                 + ", ".join(f"+{h}: {n}" for h, n in pend.items()) + "."]
    body += ["", "The most recent events:", "",
             "| Session | S&P 500 | SPHB/SPLV | +1 | +5 | +20 | Marked |",
             "|---|---|---|---|---|---|---|"]
    for e in episodes[-12:]:
        body.append(f"| {e['session']} | {e['spx_chg_pct']:+.2f}% | {e['ratio_chg_pct']:+.2f}% "
                    f"| {_p(e['spx_fwd_1'], True)} | {_p(e['spx_fwd_5'], True)} "
                    f"| {_p(e['spx_fwd_20'], True)} "
                    f"| {e['mark']}{' (overlaps)' if e['overlaps_prior_event'] else ''} |")
    head = res["average"][5]
    return {"item": ITEM, "title": TITLE, "as_of": as_of,
            "window": f"{first} (SPHB's and SPLV's first common session) to {as_of}",
            "n": len(evs),
            "statistic": ("the S&P 500's +1, +5 and +20 session returns after each event: "
                          "n, mean, median, share negative, beside the same over every "
                          "session of the window"),
            "pass_rule": PASS_RULE, "verdict": NO_GATE, "rights": RIGHTS,
            "body": body, "episodes": episodes,
            "headline": {"n": len(evs), "fwd5_mean": head["mean"],
                         "fwd5_share_negative": head["share_negative"],
                         "base5_mean": base[5]["mean"],
                         "base5_share_negative": base[5]["share_negative"]},
            "v100a": None if v100 is None else {"spx_chg_pct": v100[0],
                                                "ratio_chg_pct": v100[1],
                                                "holds": v100[2]},
            "caveats": ["SPHB and SPLV are ETFs standing in for the S&P 500 High Beta and "
                        "Low Volatility indices; their fees and tracking enter the ratio.",
                        "Overlapping events share forward days, so the events' n overstates "
                        "the independent observations."]}
