"""
Batch 22 item 122, O-3: the earnings-quality flag's margin, calibrated under the
rule pre-registered at the head of
docs/ledgers/earnings-quality-calibration-2026-11.md (A134, 7 Nov 2026).

    python tools/calibration/earnings_quality.py            # pull, run, write
    python tools/calibration/earnings_quality.py --dry-run  # print, write nothing

The calibration rule (tools/calibration/README.md): full history from the public
sources directly -- FRED's keyless fredgraph CSV for CPATAX and A463RC1Q027SBEA,
Shiller's ie_data.xls through altdata/sources/shiller.py's own parser -- never
the observation store. load_public() fetches; study() is arithmetic over plain
series (altdata/earnings_quality.calibrate), so the gate hands it a fixture.

The run checks the head's rule against config/earnings_quality.yaml's
`calibration.rule_sha256` and refuses on a mismatch; it fills the Result below
the head's marker once and never edits the head. A re-run against later data is
a new dated file with the head unchanged.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from altdata import earnings_quality as eq                      # noqa: E402
from altdata import session                                     # noqa: E402

MARKER = "<!-- RESULT BELOW. The head above is pre-registered and never edited. -->"
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"


def head_rule(text: str) -> str:
    return next(ln[2:] for ln in text.splitlines() if ln.startswith("> "))


def load_public() -> dict:
    from altdata.sources import _publication as pub             # noqa: PLC0415
    from altdata.sources import shiller                         # noqa: PLC0415
    from altdata.sources._base import http_get_response         # noqa: PLC0415
    import xlrd                                                  # noqa: PLC0415
    out = {}
    for name, fid in (("nipa", "CPATAX"), ("nonfin", "A463RC1Q027SBEA")):
        data, _ = http_get_response(FRED_CSV.format(fid), timeout=60)
        rows = list(csv.reader(io.StringIO(data.decode("utf-8"))))
        out[name] = {eq.quarter_of(r[0]): float(r[1]) for r in rows[1:]
                     if r and r[0][:1].isdigit() and r[1] not in ("", ".")}
    url = pub.find_link(shiller.PAGE, shiller.LINK)
    data, _ = http_get_response(url, timeout=120)
    sheet = xlrd.open_workbook(file_contents=data).sheet_by_name("Data")
    rows = shiller.rows_from_table([sheet.row_values(r) for r in range(sheet.nrows)],
                                   "1970-01-01T00:00:00Z", "x")
    out["eps"] = {r["observed_at"][:7]: float(r["value"]) for r in rows
                  if r["registry_key"] == "shiller.sp_earnings"}
    out["sources"] = {"nipa": FRED_CSV.format("CPATAX"),
                      "nonfin": FRED_CSV.format("A463RC1Q027SBEA"), "eps": url}
    return out


def study(data: dict, cfg: dict) -> dict:
    rows = eq.growth_rows(data["nipa"], data["eps"], data.get("nonfin"))
    rows = {q: r for q, r in rows.items() if r["gap"] is not None}
    return {"rows": rows, **eq.calibrate(rows, cfg)}


def _yn(b: bool) -> str:
    return "yes" if b else "no"


def result_md(res: dict, cfg: dict, data: dict, stamp: str) -> str:
    c = res["chosen"] or {}
    q0, q1 = res["quarters"]
    lines = ["", "## Result", "",
             f"**Edition:** laptop run, {stamp}, public sources (FRED fredgraph CSV; "
             f"Shiller's ie_data.xls), never the observation store. Quarters scored "
             f"{q0} to {q1} (the gap needs both growth rates; the fire needs the quarter "
             f"before). EPS is Shiller's trailing twelve months as reported, read at "
             f"the quarter's last month; NIPA is the latest vintage, so the read is "
             f"not point in time.", ""]
    if res["ambiguous"]:
        lines += [f"**Verdict: AMBIGUOUS. The margin is {res['margin']:.0f} points (O-3's "
                  f"default).** Why: {res['why']}.", ""]
    else:
        lines += [f"**Verdict: the margin is {res['margin']:.0f} points**, the one "
                  f"admissible margin with the fewest false-positive episodes.", ""]
    lines += [f"At {res['margin']:.0f} points: 1999-2000 {_yn(c.get('hits', {}).get('1999-2000', False))}, "
              f"2006-07 {_yn(c.get('hits', {}).get('2006-07', False))}; "
              f"**{c.get('false_positives', 0)} false-positive episodes since 1990** "
              f"({', '.join(a if a == b else f'{a} to {b}' for a, b in c.get('fp_episodes', [])) or 'none'}); "
              f"{c.get('episodes', 0)} episodes in all, {c.get('fired_quarters', 0)} fired quarters.", "",
              f"Admissible margins (fire in both targets): "
              f"{', '.join(str(m) for m in res['admissible']) or 'none'}.", "",
              "| Margin (pts) | 1999-2000 | 2006-07 | Admissible | Episodes | False positives | Fired quarters |",
              "|---|---|---|---|---|---|---|"]
    for t in res["table"]:
        lines.append(f"| {t['margin']} | {_yn(t['hits']['1999-2000'])} | {_yn(t['hits']['2006-07'])} | "
                     f"{_yn(t['admissible'])} | {t['episodes']} | {t['false_positives']} | "
                     f"{t['fired_quarters']} |")
    nf = res["nonfin"]
    lines += ["", f"**Beside it, never selecting:** BEA's domestic nonfinancial profits at "
              f"{res['margin']:.0f} points: 1999-2000 {_yn(nf['hits']['1999-2000'])}, 2006-07 "
              f"{_yn(nf['hits']['2006-07'])}, {nf['false_positives']} false-positive episodes "
              f"({len(nf['episodes'])} in all).", "",
              "**Reading the false positives.** Most fire in the first quarters of a "
              "recovery, when reported EPS rebounds off write-down-depressed troughs "
              "faster than NIPA profits, which exclude those write-downs: a known "
              "property of as-reported EPS against NIPA, and one an operating-EPS "
              "series would soften. The flag is a report line; it decides nothing.", "",
              "| Source | URL |", "|---|---|"]
    for k, u in data.get("sources", {}).items():
        lines.append(f"| {k} | {u} |")
    lines += ["", "The per-quarter growth rates and gaps are in "
              "`earnings-quality-calibration-2026-11.csv` beside this file.", ""]
    return "\n".join(lines)


def write_csv(path: Path, rows: dict) -> None:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["quarter", "nipa_yoy_pct", "eps_yoy_pct", "gap_pts", "nonfin_yoy_pct",
                "gap_nonfin_pts"])
    f = lambda v: "" if v is None else f"{v:.3f}"               # noqa: E731
    for q in sorted(rows):
        r = rows[q]
        w.writerow([q, f(r["nipa_yoy"]), f(r["eps_yoy"]), f(r["gap"]),
                    f(r.get("nonfin_yoy")), f(r.get("gap_nonfin"))])
    path.write_text(buf.getvalue(), encoding="utf-8", newline="\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    cfg = eq.config()
    ledger = REPO / cfg["calibration"]["ledger"]
    text = ledger.read_text(encoding="utf-8")
    if eq.rule_sha256(head_rule(text)) != cfg["calibration"]["rule_sha256"]:
        print("REFUSED: the ledger head's rule does not hash to config's rule_sha256")
        return 2
    if "## Result" in text.split(MARKER, 1)[-1]:
        print("REFUSED: the Result is already written; a re-run is a new dated file")
        return 2
    data = load_public()
    res = study(data, cfg)
    stamp = session.utc_iso(timespec="minutes").replace("+00:00", " UTC")
    md = result_md(res, cfg, data, stamp)
    print(md)
    if a.dry_run:
        return 0
    ledger.write_text(text.rstrip("\n") + "\n" + md, encoding="utf-8", newline="\n")
    write_csv(ledger.with_suffix(".csv"), res["rows"])
    print(f"wrote {ledger.relative_to(REPO)} and its CSV")
    return 0


if __name__ == "__main__":
    sys.exit(main())
