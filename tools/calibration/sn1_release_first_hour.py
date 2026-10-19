"""
SN-1: the release-day first hour -- continue or fade (the secondary-notes order,
section 4.1, ruled 19 Oct 2026). Report-only.

THE PRE-REGISTRATION IS docs/ledgers/release-first-hour-preregistration-2026-10.md,
committed before this script and never edited (its SHA-256 is pinned by
tools/validate_secondary_notes.py). This script applies it and may not change it.

WHAT THE FIRST EDITION READS (laptop, public sources):
  - the release dates from FRED's public release calendar, its keyless page
    (fred.stlouisfed.org/releases/calendar; the API route fred/release/dates wants
    a key the laptop does not hold), for the seven FRED releases the calendar
    schedules at 08:30 (the refunding is not a FRED release: its days are not read);
  - Yahoo's HOURLY bars for ES=F and ^TNX, about two years (the one yfinance
    import): "the last bar before 08:30" is the 07:00-08:00 bar's close, "the end
    of the first hour" the 09:00-10:00 bar's, "the 16:00 close" the 15:00-16:00
    bar's. So the edition reads 08:00 to 10:00 against 10:00 to 16:00.
It never opens the observation store, and the naive-surprise split is "not
computed (the naive expectation is the store's)".

    python tools/calibration/sn1_release_first_hour.py [--box] [--out DIR] [--date D]
"""

from __future__ import annotations

import argparse
import datetime as dt
import math
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import st7_common as C                                          # noqa: E402

ITEM = "SN-1"
TITLE = "The release-day first hour: continue or fade (secondary notes, 4.1)"
PREREG = "docs/ledgers/release-first-hour-preregistration-2026-10.md"
MIN_DAYS, Q = 20, 0.10
# The releases in the order the pre-registration lists them; a day with several
# counts once, under its highest tier, and within a tier under the first listed.
RELEASES = (("CPI", 1, "Consumer Price Index"), ("PCE", 1, "Personal Income and Outlays"),
            ("payrolls", 1, "Employment Situation"), ("GDP", 1, "Gross Domestic Product"),
            ("PPI", 2, "Producer Price Index"),
            ("retail sales", 2, "Advance Monthly Sales for Retail and Food Services"),
            ("jobless claims", 2, "Unemployment Insurance Weekly Claims Report"))
INSTRUMENTS = (("ES=F", "ES", "%"), ("^TNX", "10-year yield", "bp"))
PASS_RULE = ("A cell (release type x instrument, in one sample) passes when its "
             "continuation share's Wilson 95% interval excludes 50% with 20 scored days "
             "at least, after Benjamini-Hochberg at q = 0.10 across every cell of that "
             "sample with 20 days or more; PASS when one cell or more passes, "
             "INSUFFICIENT when no cell reaches 20 days, FAIL otherwise.")


# FRED's release ids for the eight releases, each checked against the page's own
# name when it is read (a renumbered release is named, never guessed).
RELEASE_IDS = {"CPI": 10, "PCE": 54, "payrolls": 50, "GDP": 53, "PPI": 46,
               "retail sales": 9, "jobless claims": 180}
CAL_URL = "https://fred.stlouisfed.org/releases/calendar?rid={rid}&y={y}"
MONTHS = ("January|February|March|April|May|June|July|August|September|October|"
          "November|December")


def release_days(start: str, end: str) -> tuple[dict[str, str], dict]:
    """{day: release type} from FRED's public release calendar, and a report.

    THE CALENDAR'S PAGE, NOT ITS API: the API wants a key and the laptop holds
    none (rule 30: friction is a gap, not a key). fred.stlouisfed.org/robots.txt
    allows /releases/calendar to every agent with a one-second crawl delay, which
    is kept. The page names its release; a page that does not is reported."""
    import re                                                   # noqa: PLC0415
    import time                                                 # noqa: PLC0415
    import urllib.request                                       # noqa: PLC0415
    from altdata.sources import user_agent                      # noqa: PLC0415
    ua = user_agent.generic()
    days: dict[str, str] = {}
    rep = {}
    for label, tier, name in sorted(RELEASES, key=lambda x: x[1]):
        rid, got = RELEASE_IDS[label], set()
        for y in range(int(start[:4]), int(end[:4]) + 1):
            try:
                req = urllib.request.Request(CAL_URL.format(rid=rid, y=y),
                                             headers={"User-Agent": ua})
                html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
            except Exception as exc:                            # noqa: BLE001
                rep[label] = f"page {y} failed: {type(exc).__name__}"
                continue
            finally:
                time.sleep(1.0)
            if name.split()[0].lower() not in html.lower():
                rep[label] = f"the page for release id {rid} does not name {name!r}"
                continue
            for m in re.findall(rf"(?:{MONTHS})\s+\d{{1,2}},\s+20\d\d", html):
                d = dt.datetime.strptime(re.sub(r"\s+", " ", m), "%B %d, %Y").date().isoformat()
                if start <= d <= end:
                    got.add(d)
        rep.setdefault(label, f"{len(got)} dates (release id {rid})")
        for d in sorted(got):
            days.setdefault(d, label)       # tier order: the first label kept wins
    return days, rep


def hourly(sym: str) -> dict[str, dict[str, float]]:
    """{ET date: {"HH:MM" bar start: close}} from Yahoo's hourly bars."""
    from altdata import import_yfinance                         # noqa: PLC0415
    yf = import_yfinance()
    h = yf.Ticker(sym).history(period="730d", interval="1h", prepost=True)
    out: dict[str, dict[str, float]] = {}
    for idx, r in h.iterrows():
        t = idx.tz_convert("America/New_York")
        c = float(r["Close"])
        if c == c:
            out.setdefault(t.date().isoformat(), {})[t.strftime("%H:%M")] = c
    return out


def load() -> dict:
    today = dt.date.today()
    start = (today - dt.timedelta(days=730)).isoformat()
    days, rep = release_days(start, today.isoformat())
    bars = {sym: hourly(sym) for sym, _, _ in INSTRUMENTS}
    return {"days": days, "report": rep, "bars": bars, "start": start,
            "retrieved": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}


def binom_p(k: int, n: int) -> float:
    """The exact two-sided binomial p-value against one half."""
    if n == 0:
        return 1.0
    pk = math.comb(n, k) / 2 ** n
    return min(1.0, sum(math.comb(n, i) / 2 ** n for i in range(n + 1)
                        if math.comb(n, i) / 2 ** n <= pk * (1 + 1e-9)))


def bh(ps: list[float], q: float) -> list[bool]:
    m = len(ps)
    order = sorted(range(m), key=lambda i: ps[i])
    k = 0
    for rank, i in enumerate(order, 1):
        if ps[i] <= rank / m * q:
            k = rank
    keep = set(order[:k])
    return [i in keep for i in range(m)]


def score(day_bars: dict[str, float], unit: str) -> tuple[Optional[str], dict]:
    """("continues" | "fades" | None, the moves)."""
    a, b, c = day_bars.get("07:00"), day_bars.get("09:00"), day_bars.get("15:00")
    if a is None or b is None or c is None:
        return None, {"why": "a bar missing at either end"}
    k = 100.0 if unit == "bp" else None
    m1 = (b - a) * k if k else 100.0 * (b / a - 1.0)
    m2 = (c - b) * k if k else 100.0 * (c / b - 1.0)
    if m1 == 0:
        return None, {"why": "m1 is zero", "m1": 0.0, "m2": round(m2, 4)}
    return ("continues" if (m1 > 0) == (m2 > 0) and m2 != 0 else "fades"), \
        {"m1": round(m1, 4), "m2": round(m2, 4)}


def study(d: dict, mode: str, today: Optional[str] = None) -> dict:
    from altdata.dealer_scorecard import wilson                 # noqa: PLC0415
    today = today or dt.date.today().isoformat()
    eps, cells = [], {}
    for day, label in sorted(d["days"].items()):
        for sym, name, unit in INSTRUMENTS:
            out, mv = score((d["bars"].get(sym) or {}).get(day) or {}, unit)
            eps.append({"day": day, "release": label, "instrument": sym, "outcome": out or "",
                        "m1": mv.get("m1", ""), "m2": mv.get("m2", ""),
                        "not_scored": mv.get("why", "")})
            c = cells.setdefault((label, sym), {"k": 0, "n": 0, "unscored": 0})
            if out is None:
                c["unscored"] += 1
            else:
                c["n"] += 1
                c["k"] += out == "continues"
    judged = [(key, c) for key, c in cells.items() if c["n"] >= MIN_DAYS]
    rej = bh([binom_p(c["k"], c["n"]) for _, c in judged], Q) if judged else []
    passes = 0
    body = [f"- {len(d['days'])} release days read from FRED's calendar since "
            f"{d['start']}: " + "; ".join(f"{k} {v}" for k, v in d["report"].items()) + ".",
            "- The treasury refunding is not a FRED release: its days are not read.",
            "- Hourly bars, Yahoo: the 07:00-08:00, 09:00-10:00 and 15:00-16:00 bars "
            "(ET), so this edition reads 08:00 to 10:00 against 10:00 to 16:00.",
            "- Benjamini-Hochberg is applied to each cell's exact two-sided binomial "
            "p-value against one half; a cell passes when it is rejected AND its Wilson "
            "95% interval excludes 50%.",
            "- The naive-surprise split: not computed (the naive expectation is the "
            "store's; the box edition adds it).", "",
            "| Release | Instrument | Scored days | Continues | Share | Wilson 95% | "
            "Not scored | BH |", "|---|---|---|---|---|---|---|---|"]
    jkeys = [key for key, _ in judged]
    for (label, sym), c in sorted(cells.items()):
        ci = wilson(c["k"], c["n"]) if c["n"] else None
        bhv = "-"
        if (label, sym) in jkeys:
            r = rej[jkeys.index((label, sym))]
            ok = r and ci is not None and (ci[1] < 0.5 or ci[0] > 0.5)
            passes += bool(ok)
            bhv = "pass" if ok else "no"
        body.append(f"| {label} | {sym} | {c['n']} | {c['k']} | "
                    f"{(c['k'] / c['n'] * 100 if c['n'] else 0):.0f}% | "
                    f"{f'{ci[0] * 100:.0f}-{ci[1] * 100:.0f}%' if ci else 'n/a'} | "
                    f"{c['unscored']} | {bhv} |")
    n = sum(c["n"] for c in cells.values())
    if not judged:
        verdict = f"{C.INSUFFICIENT} (no cell reaches {MIN_DAYS} scored days)"
    elif passes:
        verdict = f"{C.PASS} ({passes} of {len(judged)} cells with 20 days or more pass)"
    else:
        verdict = f"{C.FAIL} (none of {len(judged)} cells with 20 days or more passes)"
    return {"item": ITEM, "title": TITLE, "as_of": today,
            "window": f"release days {d['start']} to {today} (Yahoo's hourly history)",
            "n": n, "statistic": "the share of release days on which the first hour's "
                                 "move continued to the close, by release type and "
                                 "instrument",
            "pass_rule": PASS_RULE, "verdict": verdict,
            "rights": ("None. A PASS is reported and reaches the register only as a "
                       "rule-31 draft; it grants no reading, flag, dial or decision. "
                       + C.RIGHTS_NOTE),
            "sources": [f"The pre-registration, {PREREG}",
                        "FRED's public release calendar, its keyless page "
                        "(fred.stlouisfed.org/releases/calendar), retrieved "
                        f"{d['retrieved']}",
                        "Yahoo Finance hourly bars for ES=F and ^TNX (the one yfinance "
                        f"import), retrieved {d['retrieved']}"],
            "source_mode": mode, "body": body, "episodes": eps,
            "caveats": [
                "^TNX: Yahoo's hourly bars for the yield index start at 08:20 ET and are "
                "aligned at twenty past the hour, so the registered 07:00-08:00 bar never "
                "exists and every ^TNX day is not scored in this sample. The registration "
                "is not changed; the open note's own 5-minute readings "
                "(calc.release_first_hour) are the sample that can score the 10-year.",
                "A release date is FRED's; the print is assumed at 08:30 ET, as the "
                "release calendar schedules it.",
                "Two samples are never pooled: this is the first edition's; the note's own "
                "readings accrue from the first live open note."]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SN-1, the release-day first hour")
    ap.add_argument("--box", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--date")
    a = ap.parse_args(argv)
    r = study(load(), C.BOX if a.box else C.LAPTOP)
    C.publish(r, a.out, a.date or dt.date.today().isoformat())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
