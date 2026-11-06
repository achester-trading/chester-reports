"""
ST-R6.65a -- the 10-year speed flag's attribution against what followed
(signal-triage Batch 14, item 65, written as 58; ruling 1; a57-batch14-b1). A
dated ledger, report only.

    python tools/calibration/st_r6_65a_speed_attribution.py [--box] [--out DIR] [--date D]

THE PRE-REGISTRATION is docs/ledgers/speed-attribution-preregistration-2026-10.md,
committed alone before this script and never edited (tools/validate_batch14_b1.py
holds its SHA-256). This script applies it and changes nothing in it:

  the flag       SR-35 as config/move_screen.yaml states it: the 10-year's 10- and
                 21-session changes, each a z against the same horizon's changes
                 on the sessions before (their start within 7,305 days), at 2.0
  an episode     a flag day with no flag day in the 21 sessions before it
  the leg        altdata/speed_attribution.attribute(): KW and ACM, each read
                 only with an observation on the day (F5), the premium share
                 against one half; the leg every model read agrees on
  the outcome    the 10-year's change to the 20th session after; continued when
                 non-zero with the move's sign
  PASS           each group (term premium, expected short rates) >= 15 episodes,
                 the continuation shares >= 0.15 apart, the same sign in each
                 half; INSUFFICIENT under 15 in either group; FAIL otherwise

Public sources only: it opens no store and reads no vendor value and no by-hand key.
study(data, mode) is arithmetic over plain series, so a gate can hand it a fixture.
"""

from __future__ import annotations

import datetime as dt
import math
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                           # noqa: E402

ITEM = "ST-R6.65a"
TITLE = "The 10-year speed flag's attribution against the next 20 sessions (item 65)"
PREREG = "docs/ledgers/speed-attribution-preregistration-2026-10.md"
SIGMA, HISTORY_DAYS, MIN_OBS = 2.0, 7305, 30
HORIZONS = (10, 21)
RUN_GAP = 21
FORWARD = (5, 20)
SAMPLE_FROM = "1990-01-02"
MIN_GROUP, MIN_GAP = 15, 0.15
PREMIUM, PATH = "the term premium", "expected short rates"
PASS_RULE = ("the pre-registration's (docs/ledgers/speed-attribution-preregistration-"
             "2026-10.md): each group -- the episodes the term premium carried, those "
             "expected short rates carried -- holds at least 15, their 20-session "
             "continuation shares differ by at least 0.15, and the difference has the "
             "same sign in each half split at the median episode date; INSUFFICIENT "
             "under 15 in either group")


def load_public() -> dict:
    from altdata.ledgers import sources as S                    # noqa: PLC0415
    from altdata.sources import acm                             # noqa: PLC0415
    from altdata.sources._base import http_get_response         # noqa: PLC0415
    import xlrd                                                 # noqa: PLC0415
    data, _ = http_get_response(acm.URL, timeout=180)
    sheet = xlrd.open_workbook(file_contents=data).sheet_by_name(acm.SHEET)
    table = [sheet.row_values(r) for r in range(sheet.nrows)]
    acm_tp = sorted((r["observed_at"], float(r["value"]))
                    for r in acm.rows_from_table(table, "n/a", "observed")
                    if r["registry_key"] == "acm.term_premium_10y")
    return {"yield": S.fred("DGS10"), "kw": S.fred("THREEFYTP10"), "acm": acm_tp,
            "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def flags(y: list[tuple[str, float]]) -> list[dict]:
    """Every session's SR-35 read: [{day, i, z: {h: z}, fired, lead}], from the
    first session with MIN_OBS observations. Prefix sums over each horizon's
    changes reproduce move_screen.screen_points' window (changes ending before the
    day, starting within HISTORY_DAYS of it; population standard deviation)."""
    days = [d for d, _ in y]
    vals = [v for _, v in y]
    dates = [dt.date.fromisoformat(d) for d in days]
    pre = {}
    for h in HORIZONS:
        s1, s2 = [0.0], [0.0]
        for i in range(len(vals)):
            c = vals[i] - vals[i - h] if i >= h else 0.0
            s1.append(s1[-1] + c)
            s2.append(s2[-1] + c * c)
        pre[h] = (s1, s2)
    out, k0 = [], 0
    for n in range(MIN_OBS - 1, len(vals)):
        lo = dates[n] - dt.timedelta(days=HISTORY_DAYS)
        while dates[k0] < lo:
            k0 += 1
        zs = {}
        for h in HORIZONS:
            a, b = max(h, k0 + h), n            # changes ending at i in [a, n - 1]
            m = b - a
            if m < 2 or n < h:
                zs[h] = None
                continue
            s1, s2 = pre[h]
            mu = (s1[b] - s1[a]) / m
            var = (s2[b] - s2[a]) / m - mu * mu
            sd = math.sqrt(var) if var > 1e-18 else 0.0
            # Rounded as the screen rounds it before comparing it with sigma.
            zs[h] = None if sd == 0 else round(((vals[n] - vals[n - h]) - mu) / sd, 2)
        live = {h: z for h, z in zs.items() if z is not None}
        fired = any(abs(z) >= SIGMA for z in live.values())
        lead = max(live, key=lambda h: abs(live[h])) if live else None
        out.append({"day": days[n], "i": n, "z": zs, "fired": fired, "lead": lead})
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
    for r in episode_starts(flags(y)):
        if r["day"] < SAMPLE_FROM or r["i"] + max(FORWARD) >= len(y):
            continue
        h, z = r["lead"], r["z"][r["lead"]]
        att = sa.attribute(series, r["day"], h, cfg)
        read = [m for m in att["models"] if m["state"] == "computed"]
        legs = {m["carried"] for m in read}
        leg = ("unread" if not read else legs.pop() if len(legs) == 1 else "disagree")
        f5 = round((y[r["i"] + 5][1] - y[r["i"]][1]) * 100, 1)
        f20 = round((y[r["i"] + 20][1] - y[r["i"]][1]) * 100, 1)
        mv = att.get("move_bp") or 0.0
        by = {m["model"]: m for m in att["models"]}
        rows.append({"day": r["day"], "horizon": h, "z": round(z, 2), "move_bp": mv,
                     "kw_share": (by.get("kw") or {}).get("premium_share"),
                     "kw_leg": (by.get("kw") or {}).get("carried") or (by.get("kw") or {}).get("state"),
                     "acm_share": (by.get("acm") or {}).get("premium_share"),
                     "acm_leg": (by.get("acm") or {}).get("carried") or (by.get("acm") or {}).get("state"),
                     "leg": leg, "y10_5s_bp": f5, "y10_20s_bp": f20,
                     "continued": bool(f20 and mv and (f20 > 0) == (mv > 0))})
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
            f"- Continuation over 20 sessions: term premium {pp(sp)}, expected short "
            f"rates {pp(sh)}; difference {'—' if d_all is None else f'{d_all:+.2f}'}.",
            f"- By half (split at {grp[half - 1]['day'] if grp else '—'}): "
            f"{'—' if d1 is None else f'{d1:+.2f}'} and {'—' if d2 is None else f'{d2:+.2f}'}.",
            "", "| Day | Lead | z | Move | KW share | ACM share | Leg | +5 sessions | "
            "+20 sessions | Continued |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        body.append(f"| {r['day']} | {r['horizon']} | {r['z']:+.2f} | {r['move_bp']:+.0f} bp "
                    f"| {pp(r['kw_share'])} | {pp(r['acm_share'])} | {r['leg']} | "
                    f"{r['y10_5s_bp']:+.0f} bp | {r['y10_20s_bp']:+.0f} bp | "
                    f"{'yes' if r['continued'] else 'no'} |")
    last = lambda s: s[-1][0] if s else "—"                     # noqa: E731
    return {"item": ITEM, "title": TITLE,
            "as_of": (f"DGS10 to {last(data['yield'])}; THREEFYTP10 to {last(data['kw'])}; "
                      f"ACM to {last(data['acm'])}"),
            "window": f"episodes from {SAMPLE_FROM} to {days[-1 - max(FORWARD)] if len(days) > max(FORWARD) else '—'}, each with 20 sessions after",
            "n": len(grp),
            "statistic": ("the 10-year's 20-session continuation share after the speed "
                          "flag's episodes the term premium carried, against those "
                          "expected short rates carried (KW and ACM, F5)"),
            "pass_rule": PASS_RULE, "verdict": v,
            "rights": ("None. The speed flag keeps its rights and the attribution stays "
                       "a report whatever the verdict (F5). " + C.RIGHTS_NOTE),
            "sources": ["FRED graph CSV (no key): DGS10, THREEFYTP10, current vintages",
                        "the New York Fed's ACM workbook (ACMTermPremium.xls, sheet "
                        "'ACM Daily', ACMTP10), current vintage",
                        f"retrieved {data.get('retrieved', '—')}",
                        f"pre-registration: {PREREG}"],
            "source_mode": mode, "body": body, "episodes": rows,
            "caveats": ["Current vintages: both models are re-estimated, so a historical "
                        "share is not the one a reader saw that day. The live ledger "
                        "(rates.speed_event_ledger) records each day's own read.",
                        "The two models decompose the same yields: their agreeing is not "
                        "two independent witnesses.",
                        "The flag is computed on the full DGS10 history from 1962, so its "
                        "window is full from 1990 on."]}


if __name__ == "__main__":
    sys.exit(C.cli(ITEM, load_public, study))
