"""
ST-R5.43b -- the policy-diffusion index's lead ledger (Batch 6 item 43; docs/
change-order-signal-triage-batch-6-2026-10-15.md).

THE ORDER: "Global policy diffusion index from BIS policy rates (net share of
central banks whose last move was a cut, monthly), printed with the global PMI
headline (by hand) and the OECD CLI at the lead ... Calibration ledger on the lead
before modifier rights." The read: easing breadth "leads the global
manufacturing PMI by ~8 months" (Topdown's fit). Rights: "Report only until the
ledger; modifier after." It states NO pass rule for the lead.

THE INDEX: every central bank in the BIS policy-rate table (WS_CBPOL, monthly,
end of period). A bank's last move at month m is the sign of its most recent
change on or before m: +1 a cut, -1 a hike; a bank that has never moved in the
data does not count. The index is (cuts - hikes) / (banks with a last move),
from the first month 20 banks have one.

THE LEAD: the correlation of the index at month t with the OECD composite
leading indicator (amplitude adjusted, G20) at t + k, k = 0..18 months, on the
months both carry: the best k and its correlation, and the correlation at the
order's 8. Robustness: the G7 CLI (the API serves no OECD-area aggregate under DF_CLI; checked 17 Oct 2026). The global PMI is S&P Global's and by
hand: not stored, so not in this ledger (named, never imitated).
"""

from __future__ import annotations

from . import NO_GATE, Series, corr, month_key

ITEM = "ST-R5.43b"
TITLE = "the global policy-diffusion index's lead on the OECD CLI"
MIN_BANKS = 20
MAX_LEAD = 18
ORDER_LEAD = 8
RIGHTS = ("Report only until the ledger; modifier after (the order). With no pass "
          "rule stated for the lead, the index stays report only: this ledger "
          "grants no modifier.")


def diffusion(rates: dict[str, Series], min_banks: int = MIN_BANKS) -> Series:
    """The net share of banks whose last move was a cut, monthly."""
    last_move: dict[str, dict[str, int]] = {}
    for cb, s in rates.items():
        move, prev, out = 0, None, {}
        for d, v in s:
            if prev is not None and v != prev:
                move = 1 if v < prev else -1
            prev = v
            if move:
                out[month_key(d)] = move
        last_move[cb] = out
    months = sorted({m for o in last_move.values() for m in o})
    series, state = [], {cb: 0 for cb in rates}
    for m in months:
        for cb, o in last_move.items():
            if m in o:
                state[cb] = o[m]
        moved = [v for v in state.values() if v]
        if len(moved) >= min_banks:
            series.append((m + "-01", (sum(1 for v in moved if v > 0)
                                        - sum(1 for v in moved if v < 0)) / len(moved)))
    return series


def lead_profile(index: Series, cli: Series, max_lead: int = MAX_LEAD) -> list[tuple]:
    """[(k, corr, n)]: the index at t against the CLI at t + k months."""
    ci = {month_key(d): v for d, v in cli}
    keys = [month_key(d) for d, _ in index]
    iv = dict((month_key(d), v) for d, v in index)

    def shift(m: str, k: int) -> str:
        y, mo = int(m[:4]), int(m[5:7]) - 1 + k
        return f"{y + mo // 12}-{mo % 12 + 1:02d}"
    out = []
    for k in range(max_lead + 1):
        pairs = [(iv[m], ci[shift(m, k)]) for m in keys if shift(m, k) in ci]
        c = corr([a for a, _ in pairs], [b for _, b in pairs])
        out.append((k, c, len(pairs)))
    return out


def study(series: dict) -> dict:
    idx = diffusion(series["bis"])
    prof = lead_profile(idx, series["cli"])
    prof_o = lead_profile(idx, series["cli_oecd"])
    valid = [p for p in prof if p[1] is not None]
    best = max(valid, key=lambda p: p[1])
    at8 = next(p for p in prof if p[0] == ORDER_LEAD)
    best_o = max((p for p in prof_o if p[1] is not None), key=lambda p: p[1])
    at8_o = next(p for p in prof_o if p[0] == ORDER_LEAD)
    now_d, now_v = idx[-1]
    body = [f"The index runs {idx[0][0][:7]} to {now_d[:7]} ({len(idx)} months, from "
            f"the first month {MIN_BANKS} banks had a last move; "
            f"{len(series['bis'])} banks in the table). **Now: {now_v:+.2f}** (net share "
            f"of banks whose last move was a cut).",
            "",
            f"**Against the G20 CLI:** the best lead is **{best[0]} months** "
            f"(r {best[1]:+.2f}, n {best[2]}); at the order's {ORDER_LEAD} months, "
            f"r {at8[1]:+.2f} (n {at8[2]}).",
            f"Robustness, the G7 CLI: best lead {best_o[0]} months (r "
            f"{best_o[1]:+.2f}), at {ORDER_LEAD} months r {at8_o[1]:+.2f}.",
            "",
            "| Lead (months) | r, G20 CLI | n | r, G7 CLI |", "|---|---|---|---|"]
    for (k, c, n), (_, co, _) in zip(prof, prof_o):
        body.append(f"| {k} | {'n/a' if c is None else f'{c:+.3f}'} | {n} | "
                    f"{'n/a' if co is None else f'{co:+.3f}'} |")
    body += ["", "The global PMI headline (S&P Global, by hand) is not stored; the "
                 "order's own comparison with it is not in this ledger."]
    episodes = [{"lead_months": k, "corr_g20_cli": None if c is None else round(c, 4),
                 "n": n, "corr_g7_cli": None if co is None else round(co, 4)}
                for (k, c, n), (_, co, _) in zip(prof, prof_o)]
    return {"item": ITEM, "title": TITLE, "as_of": now_d[:7],
            "window": f"{idx[0][0][:7]} to {now_d[:7]} (index); the CLI from "
                      f"{series['cli'][0][0][:7]}",
            "n": at8[2],
            "statistic": "cross-correlation of the diffusion index with the OECD CLI "
                         "0-18 months later; the best lead and the value at 8",
            "pass_rule": "none stated (item 43: 'calibration ledger on the lead before "
                         "modifier rights'; it does not say what the lead must show)",
            "verdict": NO_GATE, "rights": RIGHTS, "body": body, "episodes": episodes,
            "result": {"best_lead": best[0], "best_r": best[1], "r_at_8": at8[1],
                       "now": now_v, "months": len(idx)},
            "caveats": [
                "Monthly levels are autocorrelated: the correlations describe, they do "
                "not test.",
                "The OECD CLI is a cross-check the order names, not the PMI itself.",
                "The BIS table's coverage changes over time; the index's denominator is "
                "the banks with a last move that month.",
            ]}


SERIES_PUBLIC = {"bis": ("bis", None), "cli": ("oecd_cli", "G20"),
                 "cli_oecd": ("oecd_cli", "G7")}
SERIES_STORE = {"bis": None, "cli": None, "cli_oecd": None}
