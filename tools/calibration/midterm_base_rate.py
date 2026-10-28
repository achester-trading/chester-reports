"""
The midterm base-rate table (signal-triage Batch 16, items 80(b) and 90; paste
A78, 26 Oct 2026). COMPUTED, never typed: every midterm year since 1950, nothing
omitted, from the store's S&P 500 closes and its recession flag, so a re-run
reproduces the table and the chat's approximate figures (V11) are replaced by it.

    python tools/calibration/midterm_base_rate.py --db PATH [--box] [--out DIR] [--date D]

writes docs/ledgers/midterm-base-rate-<date>.md and midterm-base-rate-<date>.csv.

FROM THE STORE ONLY, as the paste rules: yfinance.mkt_gspc (daily closes from
1927) and fred.usrec (NBER's monthly flag), each the store's newest vintage of
each period, read through altdata.ledgers.sources. A key the store does not hold
is printed "not stored" in its column, never fetched from elsewhere; the box's
re-run writes a new dated ledger and never edits this one.

THE COMPUTATION is the text of COMPUTATION below, printed at the ledger's head
with its SHA-256; tools/validate_batch16_midterm.py holds the hash, the 19 rows
and the headline line the Weekly's Ahead copies (config/weekly_ahead.yaml
`register_event_rows`), so the config cannot drift from the ledger.

No pass rule: the order grants base-rate rights and states no gate, so the
verdict is NO GATE IN THE ORDER, as the ST-R ledgers say it.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import datetime as dt
import hashlib
import io
import statistics
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

LEDGER_DIR = REPO / "docs" / "ledgers"
STEM = "midterm-base-rate"
SPX_KEY = "yfinance.mkt_gspc"
REC_KEY = "fred.usrec"
FIRST_YEAR = 1950
HORIZONS = (1, 3, 6, 12)
NOT_STORED = "not stored"
NO_GATE = ("NO GATE IN THE ORDER -- base rate recorded. Items 80(b) and 90 grant "
           "base-rate rights and state no pass rule; none is supplied here.")
BEGIN, END = "<!-- computation:begin -->", "<!-- computation:end -->"

COMPUTATION = """\
THE SAMPLE. Every US midterm year from 1950 to the last one completed: 1950,
1954, ..., 2022, nineteen years, none omitted. The other years are every
calendar year from 1950 to the last complete year that is not a midterm year.

THE CLOSES. The store's S&P 500 daily closes (yfinance.mkt_gspc), price only,
the newest vintage of each session.

ELECTION DAY. The first Tuesday after the first Monday in November (2 U.S.C. 7).
The election-day close is the close of the last session on or before election
day (the exchange was shut on election day in the early years of the sample).

THE YEAR'S DRAWDOWN. Over the calendar year's sessions, the largest fall from a
running peak to a later close, peak and trough both inside the year, as a
negative percent of the peak.

THE YEAR'S LOW. The trough of the year's drawdown: the close at which that
largest fall ended (the first, if two are equal). It is not always the year's
lowest close -- in a rising year that is an early-January session -- so the
lowest close's date is carried in the CSV beside it, for reference only.
Against election day: SESSIONS is the count of sessions from the low to the
election-day close (positive when the low came first); DAYS is election day
less the low's date, in calendar days.

FORWARD RETURNS. From the low's close and from the election-day close, the
price return to the close of the last session on or before the same day of the
month 1, 3, 6 and 12 months later (the month's last day when that day does not
exist); blank when that date is after the last stored close.

THE RECESSION FLAG. yes when fred.usrec is 1 in any month of the calendar year,
no when it is 0 in all twelve, "not stored" when the store holds fewer than
twelve months of it for that year.

THE COMPARISON. The mean and the median of the year's drawdown over the
nineteen midterm years and over the other years, each with its n. The
headline also counts the lows that came before election day and those in
August to October, and the years higher twelve months after election day,
beside the other years' count from the same day (the first Tuesday after the
first Monday in November), so the market's drift is not read as the cycle's.
"""


def computation_sha256(text: str = COMPUTATION) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------
def election_day(year: int) -> dt.date:
    """The first Tuesday after the first Monday in November."""
    d = dt.date(year, 11, 1)
    first_monday = d + dt.timedelta(days=(0 - d.weekday()) % 7)
    return first_monday + dt.timedelta(days=1)


def add_months(d: dt.date, k: int) -> dt.date:
    y, m = divmod(d.month - 1 + k, 12)
    y, m = d.year + y, m + 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def midterm_years(last_complete: int) -> list[int]:
    return [y for y in range(FIRST_YEAR, last_complete + 1) if y % 4 == 2]


# ---------------------------------------------------------------------------
# The arithmetic, over plain series (a gate hands it a fixture)
# ---------------------------------------------------------------------------
Daily = list[tuple[str, float]]


class Closes:
    def __init__(self, s: Daily) -> None:
        s = sorted(s)
        self.days = [dt.date.fromisoformat(d[:10]) for d, _ in s]
        self.px = [float(v) for _, v in s]

    def on_or_before(self, d: dt.date) -> Optional[int]:
        lo, hi = 0, len(self.days) - 1
        if not self.days or self.days[0] > d:
            return None
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.days[mid] <= d:
                lo = mid
            else:
                hi = mid - 1
        return lo

    def year(self, y: int) -> list[int]:
        return [i for i, d in enumerate(self.days) if d.year == y]

    def fwd(self, i: int, k: int) -> Optional[float]:
        t = add_months(self.days[i], k)
        if t > self.days[-1]:
            return None
        j = self.on_or_before(t)
        return 100.0 * (self.px[j] / self.px[i] - 1.0)


def drawdown(c: Closes, idx: list[int]) -> tuple[float, int, int]:
    """(the largest peak-to-trough fall in percent, peak index, trough index)."""
    best, peak, at = 0.0, idx[0], (idx[0], idx[0])
    for i in idx:
        if c.px[i] > c.px[peak]:
            peak = i
        dd = 100.0 * (c.px[i] / c.px[peak] - 1.0)
        if dd < best:
            best, at = dd, (peak, i)
    return best, at[0], at[1]


def recession(usrec: Optional[Daily], y: int) -> str:
    if not usrec:
        return NOT_STORED
    months = {d[:7]: v for d, v in usrec if d.startswith(str(y))}
    if len(months) < 12:
        return NOT_STORED
    return "yes" if any(v >= 0.5 for v in months.values()) else "no"


def _r(v: Optional[float], nd: int = 2) -> Optional[float]:
    return None if v is None else round(v, nd)


def study(spx: Daily, usrec: Optional[Daily]) -> dict:
    c = Closes(spx)
    last = c.days[-1]
    last_complete = last.year - 1 if last < dt.date(last.year, 12, 31) else last.year
    years = midterm_years(last_complete)
    rows = []
    for y in years:
        idx = c.year(y)
        dd, pk, tr = drawdown(c, idx)
        lo = tr
        lowest = min(idx, key=lambda i: (c.px[i], i))
        ed = election_day(y)
        e = c.on_or_before(ed)
        row = {"year": y, "election_day": ed.isoformat(),
               "election_close_date": c.days[e].isoformat(),
               "drawdown_pct": _r(dd), "peak_date": c.days[pk].isoformat(),
               "trough_date": c.days[tr].isoformat(),
               "low_date": c.days[lo].isoformat(), "low_close": _r(c.px[lo]),
               "lowest_close_date": c.days[lowest].isoformat(),
               "low_to_election_sessions": e - lo,
               "low_to_election_days": (ed - c.days[lo]).days}
        for k in HORIZONS:
            row[f"from_low_{k}m_pct"] = _r(c.fwd(lo, k))
        for k in HORIZONS:
            row[f"from_election_{k}m_pct"] = _r(c.fwd(e, k))
        row["recession"] = recession(usrec, y)
        rows.append(row)
    others = []
    for y in range(FIRST_YEAR, last_complete + 1):
        if y % 4 == 2:
            continue
        idx = c.year(y)
        if idx:
            e = c.on_or_before(election_day(y))
            others.append({"year": y, "drawdown_pct": _r(drawdown(c, idx)[0]),
                           "from_election_day_12m_pct": _r(c.fwd(e, 12))})
    # 2026 to date, for the V11 comparison only (not in the sample).
    ytd_idx = [i for i in c.year(last.year)]
    ytd = drawdown(c, ytd_idx)[0] if ytd_idx and last.year % 4 == 2 else None
    since_1980 = [o["drawdown_pct"] for o in others if o["year"] >= 1980] + \
        [r["drawdown_pct"] for r in rows if r["year"] >= 1980]
    return {"rows": rows, "others": others, "as_of": last.isoformat(),
            "first": c.days[0].isoformat(), "last_complete": last_complete,
            "ytd": {"year": last.year, "through": last.isoformat(),
                    "drawdown_pct": _r(ytd)} if ytd is not None else None,
            "all_years_since_1980_mean": _r(statistics.mean(since_1980))
            if since_1980 else None,
            "recession_stored": bool(usrec)}


# ---------------------------------------------------------------------------
# The figures the ledger and the Ahead row print
# ---------------------------------------------------------------------------
def _num(v) -> Optional[float]:
    if v in (None, ""):
        return None
    return float(v)


def summary(rows: list[dict], others: list[dict]) -> dict:
    md = [_num(r["drawdown_pct"]) for r in rows]
    od = [_num(o["drawdown_pct"]) for o in others]
    before = [r for r in rows if int(r["low_to_election_sessions"]) > 0]
    aug_oct = [r for r in rows if str(r["low_date"])[5:7] in ("08", "09", "10")]
    e12 = [_num(r["from_election_12m_pct"]) for r in rows
           if _num(r["from_election_12m_pct"]) is not None]
    l12 = [_num(r["from_low_12m_pct"]) for r in rows
           if _num(r["from_low_12m_pct"]) is not None]
    o12 = [_num(o.get("from_election_day_12m_pct")) for o in others
           if _num(o.get("from_election_day_12m_pct")) is not None]
    return {"n": len(rows), "n_other": len(others),
            "mid_mean": statistics.mean(md), "mid_median": statistics.median(md),
            "oth_mean": statistics.mean(od), "oth_median": statistics.median(od),
            "low_before": len(before), "low_aug_oct": len(aug_oct),
            "low_days_median": statistics.median(
                [int(r["low_to_election_days"]) for r in rows]),
            "e12_n": len(e12), "e12_up": sum(1 for v in e12 if v > 0),
            "e12_median": statistics.median(e12) if e12 else None,
            "e3_median": statistics.median(
                [_num(r["from_election_3m_pct"]) for r in rows
                 if _num(r["from_election_3m_pct"]) is not None]),
            "o12_n": len(o12), "o12_up": sum(1 for v in o12 if v > 0),
            "l12_n": len(l12), "l12_up": sum(1 for v in l12 if v > 0),
            "l12_mean": statistics.mean(l12) if l12 else None}


def pc(v: Optional[float], nd: int = 1, sign: bool = True) -> str:
    if v is None:
        return "—"
    s = f"{v:+.{nd}f}%" if sign else f"{v:.{nd}f}%"
    return s.replace("-", "−")


def headline(rows: list[dict], others: list[dict], edition: str) -> str:
    """The base-rate line the Weekly's Ahead prints beside the midterm row."""
    s = summary(rows, others)
    return (f"Base rate, the {s['n']} midterm years since {FIRST_YEAR} (ledger "
            f"{edition}): the year's drawdown, median {pc(s['mid_median'])} "
            f"(mean {pc(s['mid_mean'])}), against {pc(s['oth_median'])} "
            f"(mean {pc(s['oth_mean'])}) in the {s['n_other']} other years; the "
            f"year's low came before election day in {s['low_before']} of "
            f"{s['n']}, {s['low_aug_oct']} of them in August to October; from "
            f"election day the S&P 500 was higher 12 months later in "
            f"{s['e12_up']} of {s['e12_n']}, median {pc(s['e12_median'])}, against "
            f"{s['o12_up']} of {s['o12_n']} other years from the same day; n = "
            f"{s['n']}.")


# ---------------------------------------------------------------------------
# The ledger
# ---------------------------------------------------------------------------
V11 = [  # the order's chat figures (item 90's thought process), as written
    ("1974's drawdown", "−35%", lambda r, o, x: _yr(r, 1974)),
    ("2022's drawdown", "−27%", lambda r, o, x: _yr(r, 2022)),
    ("1986's drawdown", "≈ −9%", lambda r, o, x: _yr(r, 1986)),
    ("2006's drawdown", "≈ −8%", lambda r, o, x: _yr(r, 2006)),
    ("2014's drawdown", "≈ −7%", lambda r, o, x: _yr(r, 2014)),
    ("Midterm-year drawdown since 1950", "≈ 17–19%",
     lambda r, o, x: f"mean {pc(x['mid_mean'])}, median {pc(x['mid_median'])}"),
    ("All years' intra-year decline since 1980 (the order cites JPM's Guide)",
     "≈ 14%", lambda r, o, x: f"mean {pc(x['all80'])} (closes; JPM's figure is "
     "its own measure)"),
    ("Where the midterm-year lows fell", "usually late summer to October",
     lambda r, o, x: f"{x['low_aug_oct']} of {x['n']} in August to October"),
    ("12 months after the midterm-year low", "higher every time since 1950, ≈ +30% "
     "on average", lambda r, o, x: f"higher in {x['l12_up']} of {x['l12_n']}, "
     f"mean {pc(x['l12_mean'])}"),
    ("2026's drawdown to date", "−9% through 30 Sep (JPM 4Q GTM)",
     lambda r, o, x: (f"{pc(x['ytd']['drawdown_pct'])} through "
                      f"{x['ytd']['through']} (the store's last close)")
     if x.get("ytd") else "—"),
]


def _yr(rows, y) -> str:
    r = next((r for r in rows if int(r["year"]) == y), None)
    return pc(_num(r["drawdown_pct"])) if r else "—"


def csv_text(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def render(r: dict, edition: str, mode: str, csv_name: str, csv_sha: str) -> str:
    rows, others = r["rows"], r["others"]
    s = summary(rows, others)
    x = {**s, "all80": r["all_years_since_1980_mean"], "ytd": r["ytd"]}
    rec_note = ("" if r["recession_stored"] else
                f" {REC_KEY} is not in this store, so the recession column reads "
                f"\"{NOT_STORED}\"; the box's re-run fills it.")
    L = [f"# Midterm base-rate ledger -- the midterm-year table, computed from the "
         f"store",
         "",
         f"**Edition:** {edition}, {mode}. "
         + ("A re-run against the box's store supersedes it (a new dated file); this "
            "file is never edited." if mode.startswith("laptop") else
            "This file is never edited."),
         "",
         "**The computation is pre-registered** below, with its SHA-256; a re-run "
         "applies it and may not change it.",
         "",
         "| | |", "|---|---|",
         f"| As of | {r['as_of']} (the store's last S&P 500 close) |",
         f"| Window | {r['first']} to {r['as_of']}; midterm years {FIRST_YEAR} to "
         f"{rows[-1]['year']}, other years {FIRST_YEAR} to {r['last_complete']} |",
         f"| n | {s['n']} (midterm years); {s['n_other']} other years |",
         "| Statistic | each midterm year's drawdown, the low's place against election "
         "day, forward returns from the low and from election day, the recession "
         "flag; the drawdown's mean and median against the other years |",
         "| Pass rule (as the order states it) | none in the order (items 80(b) and "
         "90 grant base-rate rights) |",
         f"| Verdict | **{NO_GATE}** |",
         "| Rights consequence | Base-rate rights only (90): the table and its "
         "headline print beside the 3 Nov 2026 row in the Weekly's Ahead and in the "
         "Base Rates paper's dated appendix, never as a forecast and never as a "
         "trigger. |",
         f"| Computation SHA-256 | `{computation_sha256()}` |",
         f"| CSV SHA-256 | `{csv_sha}` ({csv_name}) |",
         "",
         "## The computation, pre-registered",
         "",
         BEGIN,
         "```text",
         COMPUTATION.rstrip("\n"),
         "```",
         END,
         "",
         "## Sources and vintages",
         "",
         f"- The observation store's {SPX_KEY}: daily closes, first stored "
         f"{r['first']}, last {r['as_of']}",
         f"- The observation store's {REC_KEY}: "
         + ("monthly, NBER's dating" if r["recession_stored"] else NOT_STORED),
         "",
         "## Results",
         "",
         "| Year | Election day | Drawdown | Peak → trough | Low | Low to election "
         "(sessions / days) | From the low +1m / +3m / +6m / +12m | From election day "
         "+1m / +3m / +6m / +12m | Recession |",
         "|---|---|---|---|---|---|---|---|---|"]
    for w in rows:
        fl = " / ".join(pc(_num(w[f"from_low_{k}m_pct"])) for k in HORIZONS)
        fe = " / ".join(pc(_num(w[f"from_election_{k}m_pct"])) for k in HORIZONS)
        L.append(f"| {w['year']} | {w['election_day']} | {pc(_num(w['drawdown_pct']))} "
                 f"| {w['peak_date']} → {w['trough_date']} | {w['low_date']} | "
                 f"{w['low_to_election_sessions']} / {w['low_to_election_days']} | "
                 f"{fl} | {fe} | {w['recession']} |")
    L += ["",
          "| The year's drawdown | n | Mean | Median |",
          "|---|---|---|---|",
          f"| Midterm years | {s['n']} | {pc(s['mid_mean'])} | {pc(s['mid_median'])} |",
          f"| Other years | {s['n_other']} | {pc(s['oth_mean'])} | "
          f"{pc(s['oth_median'])} |",
          "",
          f"The low against election day: before it in {s['low_before']} of {s['n']} "
          f"years, {s['low_aug_oct']} of them in August to October; the median low "
          f"came {s['low_days_median']:g} calendar days before election day. From "
          f"election day: median {pc(s['e3_median'])} at 3 months; higher at 12 "
          f"months in {s['e12_up']} of {s['e12_n']}, median {pc(s['e12_median'])}. "
          f"From the low: higher at 12 months in {s['l12_up']} of {s['l12_n']}, mean "
          f"{pc(s['l12_mean'])}.",
          "",
          "**The headline the Weekly's Ahead prints** (copied into "
          "`config/weekly_ahead.yaml`, held to this file by "
          "`tools/validate_batch16_midterm.py`):",
          "",
          f"> {headline(rows, others, edition)}",
          "",
          "## The order's chat figures against this ledger (V11)",
          "",
          "The order's figures were approximate; this ledger replaces them. Both, "
          "where they differ:",
          "",
          "| Figure | The order (chat) | This ledger |",
          "|---|---|---|"]
    for name, chat, f in V11:
        L.append(f"| {name} | {chat} | {f(rows, others, x)} |")
    L += ["",
          "## Caveats",
          "",
          "- The S&P 500 is its price, not its total return; the drawdown is on "
          "closes, so an intraday low below the year's lowest close is not seen.",
          "- USREC is NBER's dating, published long after the fact: the recession "
          "column is a historical label, not something knowable on election day."
          + rec_note,
          "- Returns FROM THE LOW are hindsight: the low is known only after it. "
          "The order asks for them and they are printed; the Weekly's Ahead quotes "
          "only the election-day form, a date known in advance, as the Base Rates "
          "paper's ex-ante table does (`baserate.midterm_from_election`, "
          "tools/base_rates.py Table 7, with its all-years and every-session "
          "comparators and a binomial p).",
          "- Nineteen years is a small sample, and the years are not independent "
          "draws: a base rate to read beside the row, not a forecast.",
          "",
          f"The rows are in `{csv_name}`, beside this file."]
    return "\n".join(L) + "\n"


def load_store(db: Optional[str]) -> tuple[Daily, Optional[Daily]]:
    from altdata.ledgers import sources as S                    # noqa: PLC0415
    spx = S.store(SPX_KEY, db=db)
    try:
        rec = S.store(REC_KEY, db=db)
    except LookupError:
        rec = None
    return spx, rec


def publish(r: dict, out: Path, edition: str, mode: str) -> tuple[Path, Path]:
    out.mkdir(parents=True, exist_ok=True)
    md, cv = out / f"{STEM}-{edition}.md", out / f"{STEM}-{edition}.csv"
    if md.exists():
        raise SystemExit(f"{md} exists: a dated ledger is never edited; re-run with "
                         f"another --date")
    text = csv_text(r["rows"])
    cv.write_text(text, encoding="utf-8", newline="\n")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    md.write_text(render(r, edition, mode, cv.name, sha), encoding="utf-8",
                  newline="\n")
    return md, cv


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="the midterm base-rate ledger (Batch 16)")
    ap.add_argument("--db", help="the observation store (default the package's)")
    ap.add_argument("--box", action="store_true", help="label the edition a box run")
    ap.add_argument("--out", help="ledger directory (default docs/ledgers)")
    ap.add_argument("--date", help="edition date (default today)")
    a = ap.parse_args(argv)
    spx, rec = load_store(a.db)
    r = study(spx, rec)
    edition = a.date or dt.date.today().isoformat()
    mode = "box run, the box's store" if a.box else "laptop run, the laptop's store"
    md, cv = publish(r, Path(a.out) if a.out else LEDGER_DIR, edition, mode)
    print(f"midterm base rate: n {len(r['rows'])}; as of {r['as_of']}")
    print(f"  wrote {md.name} and {cv.name}")
    print("  " + headline(r["rows"], r["others"], edition))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
