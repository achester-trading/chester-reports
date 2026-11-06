"""
Institutional gold-ETF ownership from SEC EDGAR's Form 13F data sets (signal-triage
Batch 15 item 72, written as 65; ST-R6.72a; ruled 20 Oct 2026, filed 23 Oct 2026
with filing amendments G1-G6; a58-batch15-1).

    python -m altdata.gold_13f fetch [--files N] [--dry-run]   # the box: SEC zips to the inbox
    python -m altdata.gold_13f load ZIP [ZIP ...] [--dry-run]   # count and store the quarters
    python -m altdata.gold_13f show [--as-of ISO]               # the line, from the store

THE LINE, under Factor V beside item 38's gold/equity ratio (the Monthly's slow
layers): per calendar quarter, the number of 13F filers holding GLD, IAU and either,
the value they report, and the change from the prior quarter.

THE DATA (source check 1, docs/briefs/a58-batch15-1-notes.md). Each data set is a zip
of tab-separated tables; three are read, by column NAME, and a file whose headers
lack a column is refused, not half-read:
  SUBMISSION   ACCESSION_NUMBER, FILING_DATE, SUBMISSIONTYPE, CIK, PERIODOFREPORT
  COVERPAGE    ACCESSION_NUMBER, ISAMENDMENT, AMENDMENTTYPE
  INFOTABLE    ACCESSION_NUMBER, CUSIP, VALUE, SSHPRNAMT, SSHPRNAMTTYPE, PUTCALL
A filer's quarter is its latest original or RESTATEMENT report plus the NEW HOLDINGS
amendments filed after it. Share positions only (no options). VALUE is dollars for
filings from 3 Jan 2023 and thousands before; the filing date decides.

A QUARTER IS WRITTEN ONLY WHEN THE FILES READ COVER IT: filings from the day after
its end through its 45-day deadline. A later load that adds late filers restates it
as a new vintage, never an overwrite.

ITEM 51's 13F pipeline is not built in this repo; this is the minimal reader of the
same data sets. The fetch identifies itself through altdata/sources/edgar.py's
CHESTER_SEC_CONTACT User-Agent and does nothing without it.

REPORT ONLY. Nothing here enters a composite, a flag or the market-state object.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable, Optional

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "gold_13f.yaml"
SOURCE = "sec_13f"
TITLE = "Institutional gold-ETF ownership (13F)"
BOTH = "BOTH"
TABLES = {
    "SUBMISSION": ("ACCESSION_NUMBER", "FILING_DATE", "SUBMISSIONTYPE", "CIK",
                   "PERIODOFREPORT"),
    "COVERPAGE": ("ACCESSION_NUMBER", "ISAMENDMENT", "AMENDMENTTYPE"),
    "INFOTABLE": ("ACCESSION_NUMBER", "CUSIP", "VALUE", "SSHPRNAMT", "SSHPRNAMTTYPE",
                  "PUTCALL"),
}
_MONTHS = {m: i for i, m in enumerate(
    ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"), 1)}


def config(path: Optional[Path] = None) -> dict:
    import yaml                                                 # noqa: PLC0415
    return yaml.safe_load((path or CONFIG).read_text(encoding="utf-8"))


class LayoutError(ValueError):
    """A data set whose tables or headers are not the documented layout."""


def parse_date(s: str) -> str:
    """'30-JUN-2026' (the data sets' form) or '2026-06-30' to ISO."""
    s = (s or "").strip()
    if len(s) == 10 and s[4] == "-":
        return dt.date.fromisoformat(s).isoformat()
    d, m, y = s.split("-")
    return dt.date(int(y), _MONTHS[m.upper()[:3]], int(d)).isoformat()


# ---------------------------------------------------------------------------
# Reading one data set
# ---------------------------------------------------------------------------
def _member(z: zipfile.ZipFile, table: str) -> str:
    for n in z.namelist():
        if Path(n).name.upper() == f"{table}.TSV":
            return n
    raise LayoutError(f"{table}.tsv is not in the data set")


def read_table(z: zipfile.ZipFile, table: str) -> Iterable[dict]:
    with z.open(_member(z, table)) as fh:
        rd = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8", errors="replace"),
                            delimiter="\t", quoting=csv.QUOTE_NONE)
        missing = [c for c in TABLES[table] if c not in (rd.fieldnames or [])]
        if missing:
            raise LayoutError(f"{table}.tsv lacks {', '.join(missing)}")
        yield from rd


def read_zip(path: Path, cfg: dict) -> dict:
    """{"filings": {accession: {...}}, "holdings": {accession: {symbol: [value, shares]}},
    "first_filed", "last_filed"} -- only the funds' share rows are kept."""
    cusip_to = {c.upper(): f["symbol"] for f in cfg["funds"] for c in f["cusips"]}
    types = set(cfg["submission_types"])
    dollars_from = cfg["dollars_from_filing_date"]
    filings: dict[str, dict] = {}
    dates: list[str] = []
    with zipfile.ZipFile(path) as z:
        for r in read_table(z, "SUBMISSION"):
            filed = parse_date(r["FILING_DATE"])
            dates.append(filed)
            if r["SUBMISSIONTYPE"].strip() not in types:
                continue
            filings[r["ACCESSION_NUMBER"].strip()] = {
                "cik": r["CIK"].strip().lstrip("0"), "filed": filed,
                "period": parse_date(r["PERIODOFREPORT"]), "amendment": None}
        for r in read_table(z, "COVERPAGE"):
            f = filings.get(r["ACCESSION_NUMBER"].strip())
            if f and (r["ISAMENDMENT"] or "").strip().upper() in ("Y", "TRUE", "1"):
                f["amendment"] = (r["AMENDMENTTYPE"] or "").strip().upper() or "RESTATEMENT"
        holdings: dict[str, dict[str, list[float]]] = {}
        for r in read_table(z, "INFOTABLE"):
            acc = r["ACCESSION_NUMBER"].strip()
            sym = cusip_to.get((r["CUSIP"] or "").strip().upper())
            if not sym or acc not in filings:
                continue
            if (r["PUTCALL"] or "").strip() or (r["SSHPRNAMTTYPE"] or "").strip().upper() != cfg["share_type"]:
                continue
            value = float(r["VALUE"] or 0)
            if filings[acc]["filed"] < dollars_from:
                value *= 1000.0
            h = holdings.setdefault(acc, {}).setdefault(sym, [0.0, 0.0])
            h[0] += value
            h[1] += float(r["SSHPRNAMT"] or 0)
    return {"filings": filings, "holdings": holdings,
            "first_filed": min(dates) if dates else None,
            "last_filed": max(dates) if dates else None}


def merge(parts: list[dict]) -> dict:
    out: dict[str, Any] = {"filings": {}, "holdings": {}, "first_filed": None, "last_filed": None}
    for p in parts:
        out["filings"].update(p["filings"])
        out["holdings"].update(p["holdings"])
        for k, fn in (("first_filed", min), ("last_filed", max)):
            if p[k]:
                out[k] = p[k] if out[k] is None else fn(out[k], p[k])
    return out


# ---------------------------------------------------------------------------
# The count
# ---------------------------------------------------------------------------
def filer_quarter(filings: list[tuple[str, dict]]) -> list[str]:
    """The accessions that make one filer's quarter: the latest original or
    RESTATEMENT report, then each NEW HOLDINGS amendment filed after it."""
    base = [(f["filed"], a) for a, f in filings if f["amendment"] in (None, "RESTATEMENT")]
    if not base:
        return []
    b_day, b_acc = max(base)
    adds = [a for a, f in filings if f["amendment"] == "NEW HOLDINGS" and f["filed"] >= b_day]
    return [b_acc] + sorted(adds)


def complete(period: str, first_filed: Optional[str], last_filed: Optional[str],
             deadline_days: int) -> bool:
    if not first_filed or not last_filed:
        return False
    end = dt.date.fromisoformat(period)
    return (first_filed <= (end + dt.timedelta(days=1)).isoformat()
            and last_filed >= (end + dt.timedelta(days=deadline_days)).isoformat())


def count(data: dict, cfg: dict) -> dict:
    """{quarter end: {"complete": bool, "funds": {GLD|IAU|BOTH: {holders, value_usd}}}}."""
    by: dict[tuple[str, str], list[tuple[str, dict]]] = {}
    for acc, f in data["filings"].items():
        by.setdefault((f["cik"], f["period"]), []).append((acc, f))
    syms = [f["symbol"] for f in cfg["funds"]]
    out: dict[str, dict] = {}
    for (cik, period), fl in by.items():
        held: dict[str, float] = {}
        for acc in filer_quarter(fl):
            for sym, (value, _shares) in (data["holdings"].get(acc) or {}).items():
                held[sym] = held.get(sym, 0.0) + value
        if not held:
            continue
        q = out.setdefault(period, {"funds": {s: {"holders": 0, "value_usd": 0.0}
                                              for s in syms + [BOTH]}})
        for sym, v in held.items():
            q["funds"][sym]["holders"] += 1
            q["funds"][sym]["value_usd"] += v
        q["funds"][BOTH]["holders"] += 1
        q["funds"][BOTH]["value_usd"] += sum(held.values())
    for period, q in out.items():
        q["complete"] = complete(period, data["first_filed"], data["last_filed"],
                                 int(cfg["deadline_days"]))
    return dict(sorted(out.items()))


def rows(counted: dict, cfg: dict, now: str) -> list[dict]:
    """Store rows for the complete quarters only."""
    out = []
    for period, q in counted.items():
        if not q["complete"]:
            continue
        for sym, v in q["funds"].items():
            for key, val in ((cfg["keys"]["holders"], v["holders"]),
                             (cfg["keys"]["value"], round(v["value_usd"], 0))):
                out.append({"registry_key": key, "instrument": sym, "observed_at": period,
                            "available_at": now, "value": val, "source": SOURCE})
    return out


# ---------------------------------------------------------------------------
# The line
# ---------------------------------------------------------------------------
def read(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    """The latest stored quarter against the one before, per fund."""
    from . import st_r5_rates                                   # noqa: PLC0415
    cfg = cfg or config()
    funds = [f["symbol"] for f in cfg["funds"]] + [BOTH]
    per = {}
    for sym in funds:
        h = st_r5_rates._pts(st, cfg["keys"]["holders"], cutoff, sym)
        v = dict(st_r5_rates._pts(st, cfg["keys"]["value"], cutoff, sym))
        per[sym] = [(d, int(n), v.get(d)) for d, n in h]
    if not per[BOTH]:
        return {"state": "absent", "reason": "no quarter loaded from the 13F data sets yet",
                "cfg": cfg}
    q = per[BOTH][-1][0]
    out = {"state": "read", "quarter": q, "funds": {}, "cfg": cfg}
    for sym in funds:
        cur = next((x for x in per[sym] if x[0] == q), None)
        prev = next((x for x in reversed(per[sym]) if x[0] < q), None)
        out["funds"][sym] = {
            "holders": cur[1] if cur else None, "value_usd": cur[2] if cur else None,
            "prior_quarter": prev[0] if prev else None,
            "d_holders": (cur[1] - prev[1]) if cur and prev else None,
            "d_value_usd": (cur[2] - prev[2]) if cur and prev and cur[2] is not None
                           and prev[2] is not None else None}
    return out


def _quarter(day: str) -> str:
    d = dt.date.fromisoformat(day)
    return f"Q{(d.month - 1) // 3 + 1} {d.year}"


def _bn(v: Optional[float]) -> str:
    return "—" if v is None else f"${v / 1e9:,.1f}bn"


def lines(r: dict) -> list[str]:
    cfg = r["cfg"]
    out = []
    if r["state"] != "read":
        out.append(f"Institutional gold-ETF ownership (13F): {r['reason']}.")
    else:
        parts = []
        for f in cfg["funds"] + [{"symbol": BOTH, "label": "either"}]:
            x = r["funds"][f["symbol"]]
            if x["holders"] is None:
                continue
            ch = ("" if x["d_holders"] is None else
                  f", {x['d_holders']:+,d} filers and "
                  + ("—" if x["d_value_usd"] is None else
                     f"{'+' if x['d_value_usd'] >= 0 else '-'}{_bn(abs(x['d_value_usd']))}")
                  + f" on {_quarter(x['prior_quarter'])}")
            name = f["symbol"] if f["symbol"] != BOTH else "either fund"
            parts.append(f"{name} {x['holders']:,d} filers ({_bn(x['value_usd'])}{ch})")
        out.append(f"Institutional gold-ETF ownership (13F), {_quarter(r['quarter'])}: "
                   + "; ".join(parts) + ".")
    out.append(" ".join(str(cfg["caveat"]).split()))
    return out


def subsection(st, cutoff: str, cfg: Optional[dict] = None) -> dict:
    r = read(st, cutoff, cfg)
    cfg = r["cfg"]
    return {"title": TITLE, "paragraph_wanted": False, "lines": lines(r),
            "not_tracked": [" ".join(str(cfg["wgc_flows_gap"]).split())],
            "data": {"gold_13f": {k: r.get(k) for k in ("state", "quarter", "funds")}}}


# ---------------------------------------------------------------------------
# The box's fetch (SEC fair access, through edgar.py's contact)
# ---------------------------------------------------------------------------
def zip_links(html: str) -> list[str]:
    import re                                                   # noqa: PLC0415
    seen, out = set(), []
    for m in re.finditer(r'href="([^"]+_form13f\.zip)"', html):
        u = m.group(1)
        u = u if u.startswith("http") else "https://www.sec.gov" + u
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def fetch(n_files: int, dry_run: bool, cfg: dict) -> int:
    import time                                                 # noqa: PLC0415
    from .sources import edgar                                  # noqa: PLC0415
    from .sources._base import http_get_response, http_get_text  # noqa: PLC0415
    from .sources.aaii import robots_verdict                    # noqa: PLC0415
    ua = edgar.user_agent()
    if not ua:
        print(f"refused: {edgar.CONTACT_VAR} is not set, and the SEC's fair-access policy "
              "needs a contact in the User-Agent (altdata/sources/edgar.py)")
        return 2
    headers = {"User-Agent": ua}
    robots = http_get_text(cfg["robots_url"], headers=headers)
    links = zip_links(http_get_text(cfg["data_sets_page"], headers=headers))[:n_files]
    inbox = Path(cfg["inbox"]).expanduser()
    for u in links:
        ok, rule = robots_verdict(robots, u, ua)
        if not ok:
            print(f"refused by robots.txt ({rule}): {u}")
            continue
        dest = inbox / u.rsplit("/", 1)[-1]
        if dest.exists():
            print(f"have {dest.name}")
            continue
        if dry_run:
            print(f"would fetch {u}")
            continue
        body, _ = http_get_response(u, headers=headers, timeout=300)
        inbox.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)
        print(f"fetched {dest.name} ({len(body) / 1e6:.0f} MB)")
        time.sleep(float(cfg.get("pause_seconds") or 2))
    return 0


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from . import observations, session                         # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.gold_13f")
    ap.add_argument("cmd", choices=["fetch", "load", "show"])
    ap.add_argument("zips", nargs="*")
    ap.add_argument("--files", type=int, default=9)
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    cfg = config()
    now = session.utc_iso()
    if a.cmd == "fetch":
        return fetch(a.files, a.dry_run, cfg)
    if a.cmd == "load":
        if not a.zips:
            print("load needs one or more data-set zips")
            return 2
        counted = count(merge([read_zip(Path(p), cfg) for p in a.zips]), cfg)
        for period, q in counted.items():
            b = q["funds"][BOTH]
            print(f"{period}: {b['holders']:,d} filers, {_bn(b['value_usd'])}"
                  + ("" if q["complete"] else "  (partial in these files: not written)"))
        rs = rows(counted, cfg, now)
        if rs and not a.dry_run:
            with observations.ObservationStore() as st:
                st.write_many(rs)
        print(f"rows {'that would be ' if a.dry_run else ''}written: {len(rs)}")
        return 0
    with observations.ObservationStore() as st:
        for ln in lines(read(st, a.as_of or now, cfg)):
            print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
