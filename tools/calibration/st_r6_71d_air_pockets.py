"""
ST-R6.71d -- the air pockets against the fragility panel (signal-triage Batch 14,
item 71, written as 64; ruling 4; a57-batch14-b1). A dated ledger, report only.

    python tools/calibration/st_r6_71d_air_pockets.py [--box] [--out DIR] [--date D]

THE PRE-REGISTRATION is docs/ledgers/air-pocket-preregistration-2026-10.md,
committed alone before this script and never edited (tools/validate_batch14_b1.py
holds its SHA-256). This script applies it and changes nothing in it:

  the depth arm     SPY's Amihud measure (altdata/fragility.daily_depth, the
                    20-session mean with 15 present) at its 90th percentile or
                    above, ranked on the five calendar years to the session
  the flow arm      |the leveraged-ETF estimate| (fragility.rebalance_series over
                    ProShares' seven, the prior NAV within 5 days) above its 90th;
                    dealer gamma has no history and is left out, labelled
  the flag          both arms on
  the air pockets   in Feb 2018, Aug 2024 and Apr 2025, the first session with an
                    SPY close-to-close fall of 2.5% or more; the five before it
  the outcome       a fall of 2.5% or more within the next five sessions
  PASS              the flag on before at least two of the three pockets, and the
                    flag-on sessions followed by a fall at least twice as often as
                    the flag-off ones; INSUFFICIENT under 20 flag-on sessions

Public sources only: it opens no store and reads no vendor value and no by-hand key.
study(data, mode) is arithmetic over plain series, so a gate can hand it a fixture.
"""

from __future__ import annotations

import bisect
import datetime as dt
import math
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                           # noqa: E402

ITEM = "ST-R6.71d"
TITLE = "The air pockets against the fragility panel (item 71)"
PREREG = "docs/ledgers/air-pocket-preregistration-2026-10.md"
POCKET_MONTHS = ("2018-02", "2024-08", "2025-04")
FALL = -0.025
BEFORE, AHEAD = 5, 5
ARM_PCT, YEARS = 90.0, 5
SAMPLE_FROM = "2015-01-02"
MIN_ON = 20
MARGIN_PUBLISHED_DAYS = 25
PASS_RULE = ("the pre-registration's (docs/ledgers/air-pocket-preregistration-2026-10.md): "
             "with at least 20 flag-on sessions (else INSUFFICIENT), the flag -- SPY's "
             "Amihud measure at or above its 90th percentile of five years, standing in "
             "for depth, and the leveraged-ETF rebalance estimate above its 90th -- is on "
             "in at least one of the five sessions before at least two of the three air "
             "pockets, and the share of flag-on sessions followed within five sessions by "
             "an SPY fall of 2.5% or more is at least twice the flag-off share")


def load_public() -> dict:
    from altdata import fragility, import_yfinance               # noqa: PLC0415
    from altdata.ledgers import sources as S                     # noqa: PLC0415
    from altdata.sources import _publication as pub, finra, proshares  # noqa: PLC0415
    from altdata.sources._base import http_get_response          # noqa: PLC0415
    yf = import_yfinance()
    h = yf.Ticker("SPY").history(period="max", interval="1d", auto_adjust=False)
    bars = {k: [] for k in ("close", "high", "low", "volume")}
    for i, row in h.iterrows():
        d = i.strftime("%Y-%m-%d")
        for k, col in (("close", "Close"), ("high", "High"), ("low", "Low"),
                       ("volume", "Volume")):
            v = float(row[col])
            if v == v:
                bars[k].append((d, v))
    cfg = fragility.config()
    aum = {}
    for f in cfg["leveraged_etfs"]["covered"]:
        data, _ = http_get_response(proshares.URL.format(ticker=f["ticker"]), timeout=90)
        aum[f["ticker"]] = sorted(
            (r["observed_at"], float(r["value"]))
            for r in proshares.rows_from_csv(data.decode("utf-8", "replace"), f["ticker"],
                                             "n/a", "observed")
            if r["registry_key"] == "levetf.aum")
    xl, _ = http_get_response(pub.find_link(finra.PAGE, finra.LINK), timeout=90)
    debit = sorted((r["observed_at"][:10], float(r["value"]))
                   for r in finra.rows_from_table(pub.read_xlsx(xl)[finra.SHEET], "n/a",
                                                  "observed")
                   if r["registry_key"] == "finra.margin_debit")
    return {"bars": bars, "qqq": S.yahoo("QQQ"), "aum": aum, "debit": debit,
            "mv": S.fred("BOGZ1LM893064105Q"), "spx": S.yahoo("^GSPC"),
            "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def years_back(day: str, n: int) -> str:
    d = dt.date.fromisoformat(day)
    try:
        return d.replace(year=d.year - n).isoformat()
    except ValueError:
        return d.replace(year=d.year - n, day=28).isoformat()


def pct_series(pts: list[tuple[str, float]]) -> dict[str, float]:
    """Each point's percentile among the points within five calendar years before
    it, itself included, counting values at or below it (st_r5_rates.lens' window
    and derived.percentile_of's definition)."""
    days = [d for d, _ in pts]
    vals = [v for _, v in pts]
    out = {}
    for i, d in enumerate(days):
        lo = bisect.bisect_right(days, years_back(d, YEARS))
        w = vals[lo:i + 1]
        out[d] = 100.0 * sum(1 for x in w if x <= vals[i]) / len(w)
    return out


def realised_20(close: list[tuple[str, float]]) -> list[tuple[str, float]]:
    r = [(close[i][0], math.log(close[i][1] / close[i - 1][1]))
         for i in range(1, len(close)) if close[i - 1][1] and close[i][1]]
    out = []
    for i in range(19, len(r)):
        w = [x for _, x in r[i - 19:i + 1]]
        m = sum(w) / 20
        out.append((r[i][0], math.sqrt(sum((x - m) ** 2 for x in w) / 19 * 252) * 100))
    return out


def study(data: dict, mode: str) -> dict:
    from altdata import fragility                               # noqa: PLC0415
    cfg = fragility.config()
    bars = data["bars"]
    close = sorted(bars["close"])
    days = [d for d, _ in close]
    ret = {close[i][0]: close[i][1] / close[i - 1][1] - 1.0
           for i in range(1, len(close)) if close[i - 1][1]}
    dep = fragility.daily_depth(close, bars["high"], bars["low"], bars["volume"])
    am = fragility.rolling_mean([(d, a) for d, a, _ in dep], int(cfg["mean_sessions"]),
                                int(cfg["min_sessions_in_mean"]))
    am_by, am_p = dict(am), pct_series(am)
    proxies = {"yfinance.mkt_spy": close, "yfinance.mkt_qqq": sorted(data["qqq"])}
    reb = fragility.rebalance_series(data["aum"], proxies, cfg["leveraged_etfs"]["covered"],
                                     int(cfg["leveraged_etfs"]["aum_max_age_days"]))
    reb_by = {d: v for d, v, _ in reb}
    reb_p = pct_series([(d, abs(v)) for d, v, _ in reb])
    vol_p = pct_series(realised_20(close))

    def arms(d):
        a = None if d not in am_p else am_p[d] >= ARM_PCT
        f = None if d not in reb_p else reb_p[d] > ARM_PCT
        return a, f, (None if a is None or f is None else (a and f))

    idx = {d: i for i, d in enumerate(days)}
    rows = []
    for i, d in enumerate(days):
        if d < SAMPLE_FROM or i + AHEAD >= len(days):
            continue
        a, f, on = arms(d)
        if on is None:
            continue
        fell = any(ret.get(days[i + k], 0.0) <= FALL for k in range(1, AHEAD + 1))
        rows.append({"day": d, "amihud_bp_per_bn": round(am_by[d], 3),
                     "amihud_pct": round(am_p[d], 1), "rebalance_usd": round(reb_by[d]),
                     "rebalance_pct": round(reb_p[d], 1), "depth_arm": a, "flow_arm": f,
                     "flag": on, "vol_top_decile": (vol_p.get(d) or 0) >= ARM_PCT,
                     "fall_within_5": fell})
    on = [r for r in rows if r["flag"]]
    off = [r for r in rows if not r["flag"]]
    vt = [r for r in rows if r["vol_top_decile"]]

    def rate(rs):
        return sum(1 for r in rs if r["fall_within_5"]) / len(rs) if rs else None
    r_on, r_off, r_vol = rate(on), rate(off), rate(vt)
    # The three air pockets and the five sessions before each.
    share = fragility.margin_share_series(sorted(data["debit"]), sorted(data["mv"]),
                                          sorted(data["spx"]), 1e6)
    pockets = []
    for ym in POCKET_MONTHS:
        d0 = next((d for d in days if d[:7] == ym and ret.get(d, 0.0) <= FALL), None)
        if not d0:
            pockets.append({"month": ym, "day": None, "before": [], "flag_before": False})
            continue
        i0 = idx[d0]
        before = []
        for d in days[max(0, i0 - BEFORE):i0]:
            a, f, fl = arms(d)
            before.append({"day": d, "amihud": am_by.get(d), "amihud_pct": am_p.get(d),
                           "rebalance": reb_by.get(d), "rebalance_pct": reb_p.get(d),
                           "depth_arm": a, "flow_arm": f, "flag": fl})
        cut = (dt.date.fromisoformat(d0)
               - dt.timedelta(days=MARGIN_PUBLISHED_DAYS)).isoformat()
        ms = next((s for s in reversed(share) if s[0] <= cut), None)
        pockets.append({"month": ym, "day": d0, "fall_pct": round(ret[d0] * 100, 2),
                        "before": before, "flag_before": any(b["flag"] for b in before),
                        "margin": ms})
    caught = sum(1 for p in pockets if p["flag_before"])
    if len(on) < MIN_ON:
        v = (f"{C.INSUFFICIENT} ({len(on)} flag-on sessions; the rule needs {MIN_ON}); "
             f"the flag was on before {caught} of the three air pockets")
    elif caught >= 2 and r_on is not None and r_off is not None and r_on >= 2 * r_off:
        v = (f"{C.PASS} -- on before {caught} of 3 air pockets; a fall within five "
             f"sessions after {r_on:.1%} of flag-on sessions against {r_off:.1%} of "
             f"flag-off")
    else:
        v = (f"{C.FAIL} -- on before {caught} of 3 air pockets (rule: 2); a fall within "
             f"five sessions after {'—' if r_on is None else f'{r_on:.1%}'} of flag-on "
             f"sessions against {'—' if r_off is None else f'{r_off:.1%}'} of flag-off "
             f"(rule: at least twice)")

    def yn(x):
        return "—" if x is None else ("on" if x else "off")

    def num(x, f):
        return "—" if x is None else f.format(x)
    body = [f"- Sessions in the sample: {len(rows)}; flag on {len(on)} (followed by a fall "
            f"{sum(r['fall_within_5'] for r in on)}), off {len(off)} (followed by a fall "
            f"{sum(r['fall_within_5'] for r in off)}).",
            f"- A fall of 2.5% or more within five sessions: flag on "
            f"{'—' if r_on is None else f'{r_on:.1%}'}, flag off "
            f"{'—' if r_off is None else f'{r_off:.1%}'}.",
            f"- For context, outside the rule: after sessions with SPY's 20-session "
            f"realised volatility at its 90th percentile or above ({len(vt)}), "
            f"{'—' if r_vol is None else f'{r_vol:.1%}'}. Both arms rise with "
            f"volatility, so part of any lift is volatility clustering.",
            "- Dealer gamma is left out (no history before 6b's store): the flow arm is "
            "the leveraged-ETF estimate alone.", ""]
    for p in pockets:
        if not p["day"]:
            body.append(f"**{p['month']}**: no session with a fall of 2.5% or more.")
            continue
        m = p.get("margin")
        body += [f"**{p['month']}: {p['day']}** (SPY {p['fall_pct']:+.2f}%). The flag was "
                 f"{'on' if p['flag_before'] else 'off'} in the five sessions before. Margin "
                 f"debt's share of Z.1 equity market value: "
                 + (f"{m[1]:.2f}% ({m[0][:7]}{', marked' if m[2] else ''})" if m else "—")
                 + ".", "",
                 "| Session | Amihud, bp per $1bn | Percentile | Rebalance estimate | "
                 "Percentile | Depth arm | Flow arm | Flag |",
                 "|---|---|---|---|---|---|---|---|"]
        for b in p["before"]:
            body.append("| " + " | ".join([
                b["day"], num(b["amihud"], "{:.2f}"), num(b["amihud_pct"], "{:.0f}"),
                num(None if b["rebalance"] is None else b["rebalance"] / 1e9, "${:+.2f}bn"),
                num(b["rebalance_pct"], "{:.0f}"), yn(b["depth_arm"]), yn(b["flow_arm"]),
                yn(b["flag"])]) + " |")
        body.append("")
    last = lambda s: s[-1][0] if s else "—"                     # noqa: E731
    return {"item": ITEM, "title": TITLE,
            "as_of": (f"SPY to {last(close)}; ProShares NAV to "
                      f"{max((last(v) for v in data['aum'].values()), default='—')}; FINRA "
                      f"to {last(data['debit'])[:7] if data['debit'] else '—'}; Z.1 to "
                      f"{last(data['mv'])}"),
            "window": (f"sessions from {SAMPLE_FROM} to "
                       f"{rows[-1]['day'] if rows else '—'}, each with five sessions after; "
                       f"each percentile over the five calendar years to its session"),
            "n": len(rows),
            "statistic": ("the fragility flag (the Amihud stand-in and the leveraged-ETF "
                          "arm) before the three air pockets, and the share of sessions "
                          "followed within five by an SPY fall of 2.5% or more, flag on "
                          "against flag off"),
            "pass_rule": PASS_RULE, "verdict": v,
            "rights": ("Would grant nothing by itself: the flag keeps a flag's rights, and "
                       "any T&B or Book C modifier is the operator's ruling after this "
                       "ledger (item 71). " + C.RIGHTS_NOTE),
            "sources": ["Yahoo daily bars (through altdata.import_yfinance): SPY open, high, "
                        "low, close and volume, unadjusted; QQQ and ^GSPC closes",
                        "ProShares' keyless NAV history files (accounts.profunds.com): TQQQ, "
                        "SQQQ, QLD, UPRO, SPXU, SSO, SDS, through the writer's parser",
                        "FINRA's margin statistics workbook (finra.margin_debit, through the "
                        "writer's parser); FRED graph CSV: BOGZ1LM893064105Q",
                        f"retrieved {data.get('retrieved', '—')}",
                        f"pre-registration: {PREREG}"],
            "source_mode": mode, "body": body, "episodes": rows,
            "caveats": ["The Amihud measure stands in for depth, which is not tracked: the "
                        "verdict is about the stand-in.",
                        "Each air pocket's margin share uses the latest FINRA month ending "
                        f"{MARGIN_PUBLISHED_DAYS} or more days before it (FINRA publishes "
                        "about three weeks after the month) and the Z.1 quarter at or before "
                        "that month, marked to SPX; it is printed, not scored.",
                        "Three air pockets are a record of three readings, not a sample; the "
                        "base rate is the second question."]}


if __name__ == "__main__":
    sys.exit(C.cli(ITEM, load_public, study))
