"""
SR-24 -- the Livingston 1965-80 base-rate note (signal-triage Tranche H: "Livingston
1965-80 base-rate note (SR-24)"; library-st-l, 19 Oct 2026). A dated ledger, not a
by-hand line.

    python tools/calibration/sr24_livingston.py [--box] [--out DIR] [--date D]

WHAT IT ASKS. SR-24's register entry defines the de-anchoring flag and says no
validation is possible on market data, so its only history is the surveys. The
1965-80 episode is the one time US inflation expectations came unmoored, and this
note records, from the Philadelphia Fed's published Livingston Survey, how the
survey's 12-month CPI forecast behaved through it: how often realised inflation
ran above the forecast, by how much, and whether the forecast lagged realised
inflation (adaptive) rather than led it. A control window, 1984-2019, is computed
the same way so the 1965-80 figures have something to be read against.

THE SOURCE. The Philadelphia Fed's Livingston Survey historical data,
MedianGrowthRate.xlsx, worksheet CPI (robots.txt disallows only /404, /502,
/api/, /error and search pages; the page carries the Bank's copyright and no
separate reuse terms; read once a run, never stored in the observation store).
The survey runs each June and December. Per the survey's documentation:
  G_BP_To_12M  the median forecast's annualised growth from the last monthly value
               known when the questionnaire went out (BP, two months before the
               survey month: April or October) to the month 12 months beyond the
               survey month -- fourteen months, annualised by 12/14;
  the CPI      not seasonally adjusted before the December 2004 survey.
Realised inflation is CPIAUCNS (FRED graph CSV, not seasonally adjusted, never
revised) over the same fourteen months, annualised the same way.

THE MEASURES, fixed by this first edition:
  error        realised less forecast, pp, per survey;
  under-share  the share of surveys whose realised inflation exceeded the forecast;
  lag          forecast less the trailing twelve-month realised inflation at BP
               (CPIAUCNS, BP over BP-12), pp: negative means the survey expected
               less than what had just happened.
Each window prints its n, the medians and the shares; no pass rule (the order adopts
a base-rate note and states no gate).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                           # noqa: E402

ITEM = "SR-24"
URL = ("https://www.philadelphiafed.org/-/media/FRBP/Assets/Surveys-And-Data/"
       "livingston-survey/historical-data/MedianGrowthRate.xlsx")
WINDOWS = (("1965-80, the de-anchoring", "1965-06", "1980-12"),
           ("1984-2019, the control", "1984-06", "2019-12"))
NO_GATE = ("NO GATE IN THE ORDER -- base rate recorded. Tranche H asks for a "
           "base-rate note and states no pass rule; none is supplied here.")


def excel_month(serial: float) -> str:
    import datetime as dt
    d = dt.date(1899, 12, 30) + dt.timedelta(days=int(serial))
    return f"{d.year:04d}-{d.month:02d}"


def parse_cpi(data: bytes) -> dict[str, float]:
    """{survey month: G_BP_To_12M} from the workbook's CPI sheet."""
    from altdata.sources import _publication as P
    rows = P.read_xlsx(data)["CPI"]
    hdr = [str(x) for x in rows[0]]
    i = hdr.index("G_BP_To_12M")
    out = {}
    for r in rows[1:]:
        if not r or not isinstance(r[0], (int, float)) or len(r) <= i:
            continue
        v = r[i]
        if isinstance(v, (int, float)):
            out[excel_month(r[0])] = float(v)
    return out


def load_public() -> dict:
    from altdata.ledgers import sources as S
    from altdata.sources._base import http_get_bytes
    return {"forecast": parse_cpi(http_get_bytes(URL, timeout=120)),
            "cpi": S.fred("CPIAUCNS")}


def _sh(v: Optional[float]) -> str:
    return "n/a" if v is None else f"{100.0 * v:.0f}%"


def realised(cpi: C.Monthly, survey: str) -> Optional[float]:
    bp, end = C.madd(survey, -2), C.madd(survey, 12)
    if bp not in cpi or end not in cpi or not cpi[bp]:
        return None
    return 100.0 * ((cpi[end] / cpi[bp]) ** (12.0 / 14.0) - 1.0)


def trailing(cpi: C.Monthly, survey: str) -> Optional[float]:
    bp = C.madd(survey, -2)
    a = C.madd(bp, -12)
    return None if bp not in cpi or a not in cpi or not cpi[a] \
        else 100.0 * (cpi[bp] / cpi[a] - 1.0)


def study(d: dict, mode: str) -> dict:
    cpi = C.monthly_last(d["cpi"])
    fc = d["forecast"]
    rows = []
    for m in sorted(fc):
        r = realised(cpi, m)
        t = trailing(cpi, m)
        rows.append({"survey": m, "forecast_pct": round(fc[m], 2),
                     "realised_pct": None if r is None else round(r, 2),
                     "error_pp": None if r is None else round(r - fc[m], 2),
                     "trailing_12m_pct": None if t is None else round(t, 2),
                     "lag_pp": None if t is None else round(fc[m] - t, 2),
                     "completed": r is not None})
    body = ["| Window | Surveys | Median forecast | Median realised | Median error (pp) | "
            "Realised above forecast | Median lag to trailing (pp) | Forecast below "
            "trailing |", "|---|---|---|---|---|---|---|---|"]
    stats = {}
    for name, a, b in WINDOWS:
        w = [r for r in rows if a <= r["survey"] <= b and r["completed"]
             and r["lag_pp"] is not None]
        n = len(w)
        under = C.share([r["error_pp"] > 0 for r in w])
        below = C.share([r["lag_pp"] < 0 for r in w])
        stats[name] = {"n": n, "under": under, "below": below}
        body.append(
            f"| {name} | {n} | {C.f2(C.median([r['forecast_pct'] for r in w]), 2, '%')} | "
            f"{C.f2(C.median([r['realised_pct'] for r in w]), 2, '%')} | "
            f"{C.f2(C.median([r['error_pp'] for r in w]), 2)} | "
            f"{_sh(under)} | {C.f2(C.median([r['lag_pp'] for r in w]), 2)} | "
            f"{_sh(below)} |")
    a, b = WINDOWS[0][1], WINDOWS[0][2]
    body += ["", "The 1965-80 surveys, one by one:", "",
             "| Survey | Forecast (12m, annualised) | Realised | Error (pp) | Trailing 12m "
             "at BP | Lag (pp) |", "|---|---|---|---|---|---|"]
    for r in rows:
        if a <= r["survey"] <= b:
            body.append(f"| {r['survey']} | {r['forecast_pct']:.2f}% | "
                        f"{C.f2(r['realised_pct'], 2, '%')} | {C.f2(r['error_pp'], 2)} | "
                        f"{C.f2(r['trailing_12m_pct'], 2, '%')} | {C.f2(r['lag_pp'], 2)} |")
    done = [r for r in rows if r["completed"]]
    first = rows[0]["survey"] if rows else "n/a"
    s0 = stats[WINDOWS[0][0]]
    return {
        "item": ITEM, "title": "the Livingston 1965-80 base-rate note",
        "as_of": f"{done[-1]['survey'] if done else 'n/a'} (latest survey with its 12 "
                 f"months realised); CPIAUCNS to {max(cpi) if cpi else 'n/a'}",
        "window": f"{WINDOWS[0][1]} to {WINDOWS[0][2]} (the note); "
                  f"{WINDOWS[1][1]} to {WINDOWS[1][2]} (the control); surveys from {first}",
        "n": s0["n"],
        "statistic": "the Livingston median 12-month CPI forecast against realised CPI "
                     "inflation over the same fourteen months: the error, the share "
                     "realised above forecast, and the forecast's lag to trailing "
                     "inflation",
        "pass_rule": ("none in the order (Tranche H asks for a base-rate note). Fixed "
                      "by this first edition: the survey's G_BP_To_12M against "
                      "CPIAUCNS from BP (two months before the survey) to 12 months "
                      "after it, annualised by 12/14; the 1965-06 to 1980-12 surveys, "
                      "with 1984-06 to 2019-12 as the control"),
        "verdict": NO_GATE,
        "rights": ("None: SR-24 is a definition-only flag with no gate possible on "
                   "market data; this note is the base rate its register entry names "
                   "and it grants nothing. " + C.RIGHTS_NOTE),
        "sources": ["The Philadelphia Fed's Livingston Survey, MedianGrowthRate.xlsx, "
                    "worksheet CPI (G_BP_To_12M); robots.txt allows it",
                    "FRED graph CSV (no key): CPIAUCNS"],
        "source_mode": mode, "body": body, "episodes": rows,
        "caveats": ["The survey's CPI was not seasonally adjusted before December "
                    "2004; the control window crosses that change, and CPIAUCNS is "
                    "used throughout.",
                    "BP is the documentation's last value known when the "
                    "questionnaire was sent; in early surveys the panelists may "
                    "have known a slightly different month, which the documentation "
                    "flags for the pre-2004 history of every variable except CPI.",
                    "A median of panelists, not a market price: the survey records "
                    "what economists said, twice a year."]}


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study))
