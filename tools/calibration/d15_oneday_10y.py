"""
D15 -- the one-day 10-year trigger's attribution against what followed (rulings of
24 Oct 2026, D15; b59-trigger-sources). A dated ledger, report only.

    python tools/calibration/d15_oneday_10y.py [--box] [--out DIR] [--date D]

THE PRE-REGISTRATION is docs/ledgers/oneday-10y-preregistration-2026-10.md,
committed alone before this script and never edited (tools/validate_b59.py holds
its SHA-256). This script applies it and changes nothing in it:

  the trigger    the 10-year's one-day change (DGS10, bp) beyond the 97.5th
                 percentile of the absolute one-day changes on the stored days
                 before it within five years, either sign; at least 1,000 changes
                 (altdata/oneday_10y.trigger)
  an episode     a trigger day with no trigger day in the 5 sessions before it
  the leg        altdata/speed_attribution.attribute() over one session: KW and
                 ACM, each read only with an observation on the day (F5), the
                 premium share against one half; the leg every model read agrees on
  the outcome    the 10-year's change to the 5th session after; continued when
                 non-zero with the move's sign (the 20-session change printed beside)
  PASS           each group (term premium, expected short rates) >= 15 episodes,
                 the continuation shares >= 0.15 apart, the same sign in each
                 half; INSUFFICIENT under 15 in either group; FAIL otherwise

Public sources only: it opens no store and reads no vendor value and no by-hand key.
study(data, mode) is arithmetic over plain series, so a gate can hand it a fixture.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import st7_common as C                                           # noqa: E402

ITEM = "D15"
TITLE = "The 10-year one-day trigger's attribution against the next 5 sessions (D15)"
PREREG = "docs/ledgers/oneday-10y-preregistration-2026-10.md"
RUN_GAP = 5
FORWARD = (5, 20)
SAMPLE_FROM = "1990-01-02"
MIN_GROUP, MIN_GAP = 15, 0.15
PREMIUM, PATH = "the term premium", "expected short rates"
PASS_RULE = ("the pre-registration's (docs/ledgers/oneday-10y-preregistration-2026-10.md): "
             "each group -- the episodes the term premium carried, those expected short "
             "rates carried -- holds at least 15, their 5-session continuation shares "
             "differ by at least 0.15, and the difference has the same sign in each half "
             "split at the median episode date; INSUFFICIENT under 15 in either group")


def load_public() -> dict:
    import st_r6_65a_speed_attribution as A                      # noqa: PLC0415
    return A.load_public()


def triggers(y: list[tuple[str, float]], start: str) -> list[dict]:
    """Every session's trigger read from `start`: [{day, i, fired, change, thr, n}]."""
    from altdata import oneday_10y as od                         # noqa: PLC0415
    cfg = od.config()
    ch = od.one_day_changes(y)
    out = []
    for k, (d, _) in enumerate(ch):
        if d < start:
            continue
        tr = od.trigger(y, d, cfg, ch)
        if tr["state"] != "computed":
            continue
        out.append({"day": d, "i": k + 1, "fired": tr["fired"],
                    "change": tr["change_bp"], "thr": tr["threshold_bp"], "n": tr["n"]})
    return out


def episode_starts(reads: list[dict]) -> list[dict]:
    out, last = [], None
    for k, r in enumerate(reads):
        if not r["fired"]:
            continue
        if last is None or k - last > RUN_GAP:
            out.append(r)
        last = k
    return out


def study(data: dict, mode: str) -> dict:
    from altdata import speed_attribution as sa                  # noqa: PLC0415
    cfg = sa.config()
    y = sorted(data["yield"])
    days = [d for d, _ in y]
    series = {"yield": y, "kw": sorted(data["kw"]), "acm": sorted(data["acm"])}
    rows = []
    # The episode gap counts sessions, so the reads begin RUN_GAP sessions early.
    first = next((k for k, d in enumerate(days) if d >= SAMPLE_FROM), len(days))
    reads = triggers(y, days[max(1, first - RUN_GAP)] if days else SAMPLE_FROM)
    for r in episode_starts(reads):
        if r["day"] < SAMPLE_FROM or r["i"] + max(FORWARD) >= len(y):
            continue
        att = sa.attribute(series, r["day"], 1, cfg)
        read = [m for m in att["models"] if m["state"] == "computed"]
        legs = {m["carried"] for m in read}
        leg = ("unread" if not read else legs.pop() if len(legs) == 1 else "disagree")
        f5 = round((y[r["i"] + 5][1] - y[r["i"]][1]) * 100, 1)
        f20 = round((y[r["i"] + 20][1] - y[r["i"]][1]) * 100, 1)
        mv = att.get("move_bp") or 0.0
        by = {m["model"]: m for m in att["models"]}
        rows.append({"day": r["day"], "move_bp": mv, "threshold_bp": r["thr"],
                     "kw_share": (by.get("kw") or {}).get("premium_share"),
                     "kw_leg": (by.get("kw") or {}).get("carried") or (by.get("kw") or {}).get("state"),
                     "acm_share": (by.get("acm") or {}).get("premium_share"),
                     "acm_leg": (by.get("acm") or {}).get("carried") or (by.get("acm") or {}).get("state"),
                     "leg": leg, "y10_5s_bp": f5, "y10_20s_bp": f20,
                     "continued": bool(f5 and mv and (f5 > 0) == (mv > 0))})
    return verdict(rows, data, mode, days)


def _share(rs: list[dict]) -> Optional[float]:
    return sum(1 for r in rs if r["continued"]) / len(rs) if rs else None


def verdict(rows: list[dict], data: dict, mode: str, days: list[str]) -> dict:
    grp = [r for r in rows if r["leg"] in (PREMIUM, PATH)]
    prem = [r for r in grp if r["leg"] == PREMIUM]
    path = [r for r in grp if r["leg"] == PATH]
    sp, sh = _share(prem), _share(path)
    half = (len(grp) + 1) // 2
    early, late = grp[:half], grp[half:]

    def diff(rs):
        a = _share([r for r in rs if r["leg"] == PREMIUM])
        b = _share([r for r in rs if r["leg"] == PATH])
        return None if a is None or b is None else a - b
    d_all = None if sp is None or sh is None else sp - sh
    d1, d2 = diff(early), diff(late)

    def pp(v):
        return "—" if v is None else f"{v:.2f}"
    if len(prem) < MIN_GROUP or len(path) < MIN_GROUP:
        v = (f"{C.INSUFFICIENT} (term premium {len(prem)}, expected short rates "
             f"{len(path)} episodes; the rule needs {MIN_GROUP} in each)")
    elif (abs(d_all) >= MIN_GAP and d1 is not None and d2 is not None
          and d1 != 0 and d2 != 0 and (d1 > 0) == (d2 > 0) == (d_all > 0)):
        v = (f"{C.PASS} -- continuation {pp(sp)} (term premium, k "
             f"{sum(r['continued'] for r in prem)} of {len(prem)}) against {pp(sh)} "
             f"(expected short rates, k {sum(r['continued'] for r in path)} of "
             f"{len(path)}); halves {d1:+.2f} and {d2:+.2f}")
    else:
        v = (f"{C.FAIL} -- continuation {pp(sp)} (term premium, {len(prem)}) against "
             f"{pp(sh)} (expected short rates, {len(path)}), difference "
             f"{'—' if d_all is None else f'{d_all:+.2f}'} (rule >= {MIN_GAP:.2f} apart); "
             f"halves {'—' if d1 is None else f'{d1:+.2f}'} and "
             f"{'—' if d2 is None else f'{d2:+.2f}'} (rule: the same sign)")
    dis = sum(1 for r in rows if r["leg"] == "disagree")
    unr = sum(1 for r in rows if r["leg"] == "unread")
    body = [f"- Episodes in the sample: {len(rows)}; grouped {len(grp)} (term premium "
            f"{len(prem)}, expected short rates {len(path)}); models disagree {dis}; "
            f"unread {unr}.",
            f"- Continuation over 5 sessions: term premium {pp(sp)}, expected short "
            f"rates {pp(sh)}; difference {'—' if d_all is None else f'{d_all:+.2f}'}.",
            f"- By half (split at {grp[half - 1]['day'] if grp else '—'}): "
            f"{'—' if d1 is None else f'{d1:+.2f}'} and {'—' if d2 is None else f'{d2:+.2f}'}.",
            "", "| Day | Move | Threshold | KW share | ACM share | Leg | +5 sessions | "
            "+20 sessions | Continued |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        body.append(f"| {r['day']} | {r['move_bp']:+.0f} bp | {r['threshold_bp']:.1f} bp "
                    f"| {pp(r['kw_share'])} | {pp(r['acm_share'])} | {r['leg']} | "
                    f"{r['y10_5s_bp']:+.0f} bp | {r['y10_20s_bp']:+.0f} bp | "
                    f"{'yes' if r['continued'] else 'no'} |")
    last = lambda s: s[-1][0] if s else "—"                     # noqa: E731
    return {"item": ITEM, "title": TITLE,
            "as_of": (f"DGS10 to {last(data['yield'])}; THREEFYTP10 to {last(data['kw'])}; "
                      f"ACM to {last(data['acm'])}"),
            "window": f"episodes from {SAMPLE_FROM} to {days[-1 - max(FORWARD)] if len(days) > max(FORWARD) else '—'}, each with 20 sessions after",
            "n": len(grp),
            "statistic": ("the 10-year's 5-session continuation share after the one-day "
                          "trigger's episodes the term premium carried, against those "
                          "expected short rates carried (KW and ACM, F5)"),
            "pass_rule": PASS_RULE, "verdict": v,
            "rights": ("None. The trigger runs a report whatever the verdict (D15). "
                       + C.RIGHTS_NOTE),
            "sources": ["FRED graph CSV (no key): DGS10, THREEFYTP10, current vintages",
                        "the New York Fed's ACM workbook (ACMTermPremium.xls, sheet "
                        "'ACM Daily', ACMTP10), current vintage",
                        f"retrieved {data.get('retrieved', '—')}",
                        f"pre-registration: {PREREG}"],
            "source_mode": mode, "body": body, "episodes": rows,
            "caveats": ["Current vintages: both models are re-estimated, so a historical "
                        "share is not the one a reader saw that day. The live ledger "
                        "(rates.oneday_event_ledger) records each day's own read.",
                        "The two models decompose the same yields: their agreeing is not "
                        "two independent witnesses.",
                        "KW publishes THREEFYTP10 on its own calendar, so a one-day split "
                        "is read only where both the day and the day before are stored "
                        "(within 4 days); a one-day premium change is small and noisy "
                        "against the models' daily fit."]}


if __name__ == "__main__":
    sys.exit(C.cli(ITEM, load_public, study))
