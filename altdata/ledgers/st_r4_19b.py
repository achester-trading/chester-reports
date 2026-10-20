"""
ST-R4.19b -- the MOVE-VIX divergence flag's calibration ledger (Batch 5 item 19;
docs/change-order-signal-triage-batch-5-2026-10-09.md).

THE ORDER: "Two-tier cross-asset vol divergence flag (watch: MOVE z > +0.5 & VIX z
< +0.4; strong: MOVE z > +1.0 & VIX z < +0.4). Own calibration ledger replicating
the study: 1y rolling window, non-overlapping episodes, percentile ranks beside z.
Conditioner: discounted when the T&B bottom signal fired within the prior 12
months. Enters the T&B overlay intake queue (top-side input) only after the
ledger is written." Rights: "Flag now; overlay via the queue after the ledger."
It states NO pass rule.

THE STUDY BEING REPLICATED (Dashiell, Schwab, as the order records it): since
2000, 12 instances of the watch tier; the VIX higher within 1-3 months in 10 of
12; the S&P lower at 3 months in 9 of 12; at the strong tier every case
negative; misses in 2003 and 2009.

THE RULES ARE 19a's (st-r4-tranche-1b, config/batch5_tranche_1b.yaml): z of the
MOVE and of the VIX against their own last 252 common sessions, the day itself
included (derived.z_of, the sample standard deviation), percentile ranks beside
z (derived.percentile_of); the tiers with strict inequalities as written.

EPISODES, NON-OVERLAPPING. An episode starts on a day its tier holds and no
episode of that tier started in the 63 sessions before -- so no two episodes'
three-month outcomes overlap. Watch-tier episodes count days where the watch
condition holds (strong days included, since the strong condition implies it);
strong-tier episodes are counted on their own.

THE OUTCOMES, as the study words them: "the VIX higher within 1-3 months" is the
VIX above its start level at 21, 42 or 63 sessions after; "the S&P lower at 3
months" is the S&P's close 63 sessions after below its start. Both against
every day's rate, the unconditional base.

THE CONDITIONER: T&B is not built, so it is inactive here as in 19a; each
episode's year is printed so the study's two misses can be read against it.

POINT IN TIME: Yahoo's ^MOVE, ^VIX and ^GSPC closes are not revised.
"""

from __future__ import annotations

from . import NO_GATE, Series, align, mean

ITEM = "ST-R4.19b"
TITLE = "the MOVE-VIX divergence flag, replicated"
WINDOW = 252
SPACING = 63
CHECKPOINTS = (21, 42, 63)
WATCH, STRONG, VIX_BELOW = 0.5, 1.0, 0.4
STUDY = {"watch_n": 12, "vix_higher": 10, "spx_lower": 9}
RIGHTS = ("Flag now; overlay via the queue after the ledger (the order). The flag "
          "stays as built in 19a; the queue entry is ST-R4.19c, after 'T&B full' and "
          "the operator's queue ruling. This ledger grants nothing.")


def tier(move_z: float, vix_z: float) -> str | None:
    """19a's tiers, strict inequalities as written."""
    if vix_z >= VIX_BELOW:
        return None
    if move_z > STRONG:
        return "strong"
    if move_z > WATCH:
        return "watch"
    return None


def daily(move: Series, vix: Series, spx: Series, window: int = WINDOW) -> list[dict]:
    from .. import derived                                      # noqa: PLC0415
    rows = align(move, vix, spx)
    out = []
    for i in range(window - 1, len(rows)):
        w = rows[i - window + 1:i + 1]
        mv, vx = [r[1] for r in w], [r[2] for r in w]
        mz, vz = derived.z_of(mv, mv[-1]), derived.z_of(vx, vx[-1])
        if mz is None or vz is None:
            continue
        out.append({"date": rows[i][0], "i": i, "move": rows[i][1], "vix": rows[i][2],
                    "spx": rows[i][3], "move_z": mz, "vix_z": vz,
                    "move_pct": derived.percentile_of(mv, mv[-1]),
                    "vix_pct": derived.percentile_of(vx, vx[-1]),
                    "tier": tier(mz, vz)})
    return out


def outcome(rows: list[tuple], i: int) -> dict:
    """VIX higher at any checkpoint; S&P lower at 63; None past the data."""
    if i + max(CHECKPOINTS) >= len(rows):
        return {"vix_higher": None, "spx_lower": None, "spx_63_pct": None}
    v0, s0 = rows[i][2], rows[i][3]
    return {"vix_higher": any(rows[i + k][2] > v0 for k in CHECKPOINTS),
            "spx_lower": rows[i + 63][3] < s0,
            "spx_63_pct": round(100.0 * (rows[i + 63][3] / s0 - 1), 2)}


def episodes(days: list[dict], strong_only: bool, spacing: int = SPACING) -> list[dict]:
    out, last = [], None
    for d in days:
        live = d["tier"] == "strong" if strong_only else d["tier"] in ("watch", "strong")
        if live and (last is None or d["i"] - last >= spacing):
            out.append(d)
            last = d["i"]
    return out


def summarise(eps: list[dict], rows: list[tuple]) -> dict:
    oc = [outcome(rows, e["i"]) for e in eps]
    done = [o for o in oc if o["vix_higher"] is not None]
    return {"n": len(eps), "complete": len(done),
            "vix_higher": sum(o["vix_higher"] for o in done),
            "spx_lower": sum(o["spx_lower"] for o in done),
            "spx_mean": mean([o["spx_63_pct"] for o in done]) if done else None,
            "outcomes": oc}


def study(series: dict) -> dict:
    rows = align(series["move"], series["vix"], series["spx"])
    days = daily(series["move"], series["vix"], series["spx"])
    w_eps, s_eps = episodes(days, False), episodes(days, True)
    w, s = summarise(w_eps, rows), summarise(s_eps, rows)
    base = [outcome(rows, d["i"]) for d in days]
    base = [o for o in base if o["vix_higher"] is not None]
    b_vix = 100.0 * sum(o["vix_higher"] for o in base) / len(base)
    b_spx = 100.0 * sum(o["spx_lower"] for o in base) / len(base)
    now = days[-1]

    def pct(k, n):
        return "n/a" if not n else f"{k} of {n} ({100.0 * k / n:.0f}%)"
    body = [
        f"**Now ({now['date']}):** MOVE z {now['move_z']:+.2f} (percentile "
        f"{now['move_pct']:.0f}), VIX z {now['vix_z']:+.2f} (percentile "
        f"{now['vix_pct']:.0f}); tier: **{now['tier'] or 'none'}**. The conditioner is "
        f"inactive: T&B is not built.",
        "",
        "| | Episodes (complete) | VIX higher at 1, 2 or 3 months | S&P lower at 3 months | S&P at 3 months (mean) |",
        "|---|---|---|---|---|",
        f"| Watch tier (strong included) | {w['n']} ({w['complete']}) | "
        f"{pct(w['vix_higher'], w['complete'])} | {pct(w['spx_lower'], w['complete'])} | "
        + ("n/a" if w["spx_mean"] is None else f"{w['spx_mean']:+.2f}%") + " |",
        f"| Strong tier | {s['n']} ({s['complete']}) | {pct(s['vix_higher'], s['complete'])} | "
        f"{pct(s['spx_lower'], s['complete'])} | "
        + ("n/a" if s["spx_mean"] is None else f"{s['spx_mean']:+.2f}%") + " |",
        f"| Every day (the base) | {len(base):,} days | {b_vix:.0f}% | {b_spx:.0f}% | |",
        f"| The study, as the order records it | {STUDY['watch_n']} | "
        f"{STUDY['vix_higher']} of 12 | {STUDY['spx_lower']} of 12 | strong: every case negative |",
        "",
        f"The replication's window starts {days[0]['date']}: Yahoo's ^MOVE begins "
        f"{rows[0][0]}, and the first z needs {WINDOW} sessions. The study counts from "
        f"2000, so its earliest instances are outside this window.",
    ]
    ep_rows = []
    for tier_name, eps, sm in (("watch", w_eps, w), ("strong", s_eps, s)):
        for e, o in zip(eps, sm["outcomes"]):
            ep_rows.append({"tier": tier_name, "start": e["date"], "year": e["date"][:4],
                            "move": round(e["move"], 2), "move_z": e["move_z"],
                            "move_pct": e["move_pct"], "vix": round(e["vix"], 2),
                            "vix_z": e["vix_z"], "vix_pct": e["vix_pct"],
                            "day_tier": e["tier"], "vix_higher_1_3m": o["vix_higher"],
                            "spx_lower_3m": o["spx_lower"], "spx_3m_pct": o["spx_63_pct"],
                            "conditioner": "inactive (T&B not built)"})
    return {"item": ITEM, "title": TITLE, "as_of": now["date"],
            "window": f"{days[0]['date']} to {now['date']} (a {WINDOW}-session z from "
                      f"{rows[0][0]})",
            "n": w["complete"],
            "statistic": "non-overlapping watch- and strong-tier episodes: the share with "
                         "the VIX higher within 1-3 months and the S&P lower at 3 months, "
                         "against every day's, beside the study's 10/12 and 9/12",
            "pass_rule": "none stated (item 19: 'own calibration ledger replicating the "
                         "study'; the queue entry follows once the ledger is written)",
            "verdict": NO_GATE, "rights": RIGHTS, "body": body, "episodes": ep_rows,
            "result": {"watch": {k: v for k, v in w.items() if k != "outcomes"},
                       "strong": {k: v for k, v in s.items() if k != "outcomes"},
                       "base_vix_pct": b_vix, "base_spx_pct": b_spx, "now": now["tier"]},
            "caveats": [
                "Small n, as the order warns: the episodes are counted, not tested.",
                "The z window includes the day itself (19a's rule); the study's own window "
                "was not stated (verify item 3: the ruling's one year is used).",
                "The conditioner cannot be applied: T&B's bottom signal does not exist yet.",
            ]}


SERIES_PUBLIC = {"move": ("yahoo", "^MOVE"), "vix": ("yahoo", "^VIX"),
                 "spx": ("yahoo", "^GSPC")}
SERIES_STORE = {"move": "yfinance.mkt_move", "vix": "yfinance.mkt_vix",
                "spx": "yfinance.mkt_gspc"}
