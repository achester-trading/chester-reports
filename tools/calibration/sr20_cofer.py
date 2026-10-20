"""
SR-20 -- the reserve scorecard's first entry, from IMF COFER (signal-triage
Tranche H: "SR-20 scorecard first entry (USD share, constant-FX share, gold share,
holder split with SR-27 tags)"; library-st-l, 19 Oct 2026). A dated ledger, not a
by-hand line.

    python tools/calibration/sr20_cofer.py [--box] [--out DIR] [--date D]

THE SOURCE. The IMF's COFER dataflow (IMF.STA/COFER) through the repo's IMF SDMX
3.0 module (altdata/sources/_imf_sdmx.py): one anonymous request for the world
aggregate (G001), every currency, quarterly -- keyless, and within the IMF's
terms as source_registry.yaml quotes them (a narrow API query, never a bulk
download; "Source: International Monetary Fund"). The response's own
publication instant is the entry's as-of.

WHAT THE ENTRY CARRIES, by the register's list:
  USD share         the dollar's share of ALLOCATED reserves (CI_USD, SHRO_PT),
                    its latest quarter, its change on four quarters, its range
                    since 1999 and the quarter of its high -- read, never judged
                    (SR-20's ruling rejects the level as a signal);
  the other currencies' shares, and the allocated total in dollars;
  constant-FX share NOT TRACKED: no free series publishes it (it is a
                    calculation in the ECB's and the IMF's reports);
  gold share        NOT TRACKED here: COFER excludes gold, and a share of total
                    reserves including gold needs official gold at market value,
                    which this entry does not read;
  holder split      NOT TRACKED: SR-27's tags are not built.

No pass rule: a scorecard entry with no rights (SR-20's ruling).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                           # noqa: E402

ITEM = "SR-20"
FLOW, KEY = "IMF.STA/COFER/+", "G001.*.*.*.Q"
NAMES = {"CI_USD": "US dollar", "CI_EUR": "euro", "CI_JPY": "yen",
         "CI_GBP": "sterling", "CI_CNY": "renminbi", "CI_CAD": "Canadian dollar",
         "CI_AUD": "Australian dollar", "CI_CHF": "Swiss franc",
         "CI_OTHC": "other currencies"}
NO_GATE = ("NO GATE IN THE ORDER -- scorecard entry recorded. SR-20 is a scorecard "
           "with no rights and the order states no pass rule.")


def load_public() -> dict:
    from altdata.sources import _imf_sdmx as I
    return I.fetch(FLOW, KEY)


def series(d: dict, ind: str, cur: str, tr: str) -> dict[str, float]:
    for s in d.get("series") or []:
        x = s["dims"]
        if (x.get("INDICATOR"), x.get("FXR_CURRENCY"), x.get("TYPE_OF_TRANSFORMATION")) \
                == (ind, cur, tr):
            return {k: float(v) for k, v in s["obs"].items() if v is not None}
    return {}


def _q(p: str, k: int) -> str:
    y, q = int(p[:4]), int(p[-1])
    t = y * 4 + (q - 1) + k
    return f"{t // 4}-Q{t % 4 + 1}"


def study(d: dict, mode: str) -> dict:
    usd = series(d, "AFXRA", "CI_USD", "SHRO_PT")
    if not usd:
        raise ValueError("COFER: no USD share in the response")
    qs = sorted(usd)
    last = qs[-1]
    prev = _q(last, -4)
    hi = max(qs, key=lambda q: usd[q])
    lo = min(qs, key=lambda q: usd[q])
    alloc = series(d, "AFXRA", "CI_T", "NV_USD")
    body = [f"The dollar's share of allocated reserves, {last}: **{usd[last]:.2f}%** "
            f"({'n/a' if prev not in usd else f'{usd[last] - usd[prev]:+.2f} pp on four quarters'}); "
            f"its range since {qs[0]}: {usd[lo]:.2f}% ({lo}) to {usd[hi]:.2f}% ({hi}).",
            "",
            "| Currency | Share of allocated reserves, " + last + " | Four quarters earlier |",
            "|---|---|---|"]
    for code, name in NAMES.items():
        s = series(d, "AFXRA", code, "SHRO_PT")
        if last in s:
            body.append(f"| {name} | {s[last]:.2f}% | "
                        f"{'n/a' if prev not in s else f'{s[prev]:.2f}%'} |")
    body += ["",
             f"Allocated reserves, {last}: "
             f"{'n/a' if last not in alloc else f'${alloc[last] / 1e12:,.2f}tn'}.",
             "",
             "Not tracked in this entry, each with its reason:",
             "",
             "- **Constant-FX share:** no free series publishes it; it is a calculation "
             "in the ECB's and the IMF's reports.",
             "- **Gold share:** COFER excludes gold; a share of total reserves "
             "including gold needs official gold at market value, not read here.",
             "- **Holder split with SR-27's tags:** the tags are not built.",
             "",
             "Source: International Monetary Fund."]
    rows = [{"quarter": q, "usd_share_pct": round(usd[q], 4)} for q in qs]
    return {
        "item": ITEM, "title": "the reserve scorecard's first entry, from IMF COFER",
        "as_of": f"{last} (COFER published {str(d.get('published') or 'n/a')[:10]})",
        "window": f"{qs[0]} to {last}",
        "n": len(qs),
        "statistic": "the dollar's share of allocated reserves (COFER), each "
                     "currency's share and the allocated total; read, never judged",
        "pass_rule": "none in the order: SR-20 is a scorecard with no rights",
        "verdict": NO_GATE,
        "rights": ("None (SR-20's ruling: a scorecard, the level rejected as a signal "
                   "either way). " + C.RIGHTS_NOTE),
        "sources": ["IMF COFER (IMF.STA/COFER), SDMX 3.0, anonymous, one request "
                    "through altdata/sources/_imf_sdmx.py; Source: International "
                    "Monetary Fund"],
        "source_mode": mode, "body": body, "episodes": rows,
        "caveats": ["Shares are of ALLOCATED reserves; the unallocated part is "
                    "excluded, as COFER defines the shares.",
                    "The share moves with exchange rates: a weaker dollar lowers it "
                    "mechanically (SR-20's mechanism)."]}


if __name__ == "__main__":
    raise SystemExit(C.cli(ITEM, load_public, study))
