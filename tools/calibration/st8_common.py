"""
What the ST-8 studies add to ST-7's shared arithmetic (signal-triage order row
ST-8; st-t3-calib, 18 Oct 2026): total-return closes from Yahoo, Kenneth French's
files through the writer's own parser, weekly and monthly resampling, the
first-of-a-run episode rule, and the CLI with the ST-8 label.

The calibration rule (tools/calibration/README.md) holds: every study pulls full
history from the public sources directly, and none opens the observation store
or reads the market-state object. Each study is split in two -- load_public()
fetches, study(data, mode) is arithmetic over plain series -- so a gate can hand
study() a fixture and reproduce a hand figure.

A laptop edition says what n its public sources allow. A long sample it borrows
from a scan, an order or a register's cited chart is labelled a SOURCED
COMPARISON, never counted as an episode of ours (the paste of 18 Oct).
"""

from __future__ import annotations

import bisect
import datetime as dt
import math
import sys
from pathlib import Path
from typing import Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
from st7_common import (BOX, FAIL, INSUFFICIENT, LAPTOP, PASS, REPO,  # noqa: E402,F401
                        RIGHTS_NOTE, Daily, Monthly, compound, f2, madd, median,
                        months, monthly_last, pct, publish, sh, share)

# The trend z and weekly resampling are SR-1's rule's, defined once for the study
# and the Monthly's panel.
from altdata.style_regime import trend_z, weekly_last          # noqa: E402,F401

SOURCED = "sourced comparison (not an episode of ours)"
CONFIG_NOTE = ("Thresholds enter config only on a pass, with this ledger named beside "
               "them; on a fail or an insufficient n they stay where they are.")


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
def yahoo_tr(symbol: str) -> Daily:
    """Daily closes adjusted for splits and distributions (a total-return
    series), the whole history, through the one yfinance import."""
    from altdata import import_yfinance                          # noqa: PLC0415
    yf = import_yfinance()
    h = yf.Ticker(symbol).history(period="max", interval="1d", auto_adjust=True)
    out = [(i.strftime("%Y-%m-%d"), float(c)) for i, c in zip(h.index, h["Close"])
           if c == c]
    if not out:
        raise ValueError(f"Yahoo {symbol}: no closes")
    return out


def yahoo_close(symbol: str, start: Optional[str] = None) -> Daily:
    """Unadjusted daily closes (a price, a rate or a futures settlement)."""
    from altdata import import_yfinance                          # noqa: PLC0415
    yf = import_yfinance()
    t = yf.Ticker(symbol)
    h = (t.history(start=start, interval="1d", auto_adjust=False) if start
         else t.history(period="max", interval="1d", auto_adjust=False))
    return [(i.strftime("%Y-%m-%d"), float(c)) for i, c in zip(h.index, h["Close"])
            if c == c]


def french_text(which: str) -> tuple[str, str]:
    """(the unzipped file's text, its CRSP vintage) for "factors" or
    "industries", through altdata.sources.french's own fetch and unzip."""
    from altdata.sources import french                          # noqa: PLC0415
    from altdata.sources._base import http_get_response         # noqa: PLC0415
    url = french.FACTORS if which == "factors" else french.INDUSTRIES
    data, _ = http_get_response(url, timeout=120)
    text = french._unzip(data)                                  # noqa: SLF001
    return text, french.crsp_vintage(text) or "vintage line not found"


def french_sections(text: str) -> dict[str, list[list[str]]]:
    from altdata.sources import french                          # noqa: PLC0415
    return french._sections(text)                               # noqa: SLF001


def french_monthly(rows: list[list[str]]) -> dict[str, Monthly]:
    """{column: {"YYYY-MM": value}} from one YYYYMM section (missing skipped)."""
    head, out = rows[0], {}
    for cells in rows[1:]:
        if len(cells[0]) != 6 or not cells[0].isdigit():
            continue
        m = f"{cells[0][:4]}-{cells[0][4:]}"
        for j, name in enumerate(head[1:], start=1):
            try:
                v = float(cells[j])
            except (ValueError, IndexError):
                continue
            if v in (-99.99, -999.0):
                continue
            out.setdefault(name, {})[m] = v
    return out


def french_annual(rows: list[list[str]]) -> dict[str, dict[int, float]]:
    head, out = rows[0], {}
    for cells in rows[1:]:
        if len(cells[0]) != 4 or not cells[0].isdigit():
            continue
        for j, name in enumerate(head[1:], start=1):
            try:
                v = float(cells[j])
            except (ValueError, IndexError):
                continue
            if v in (-99.99, -999.0):
                continue
            out.setdefault(name, {})[int(cells[0])] = v
    return out


# ---------------------------------------------------------------------------
# Resampling and windows
# ---------------------------------------------------------------------------
def on_or_before(s: Daily, day: str) -> Optional[int]:
    j = bisect.bisect_right([d for d, _ in s], day) - 1
    return j if j >= 0 else None


def first_of_runs(dates: Sequence[str], gap_days: int) -> list[str]:
    """Non-overlapping episodes: a date starts one unless it falls within
    `gap_days` of the previous START (so an episode's horizon is never shared)."""
    out: list[str] = []
    for d in sorted(dates):
        if not out or (dt.date.fromisoformat(d)
                       - dt.date.fromisoformat(out[-1])).days > gap_days:
            out.append(d)
    return out


def mean(xs: Sequence[float]) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def asymmetry(xs: Sequence[float]) -> Optional[float]:
    """Mean gain on the winners over the mean loss on the losers (absolute)."""
    w = [x for x in xs if x is not None and x > 0]
    lo = [-x for x in xs if x is not None and x < 0]
    return (sum(w) / len(w)) / (sum(lo) / len(lo)) if w and lo else None


# ---------------------------------------------------------------------------
def cli(item: str, load, study, argv=None, extra=None) -> int:
    """`python tools/calibration/<script>.py [--box] [--out DIR] [--date D]`.
    A study may write more than one ledger: study() returns a list of them."""
    import argparse
    ap = argparse.ArgumentParser(description=f"{item} calibration study (ST-8)")
    ap.add_argument("--box", action="store_true",
                    help="label the edition a box run (same public sources)")
    ap.add_argument("--out", help="ledger directory (default docs/ledgers)")
    ap.add_argument("--date", help="edition date (default today)")
    if extra:
        extra(ap)
    a = ap.parse_args(argv)
    data = load(a) if extra else load()
    rs = study(data, BOX if a.box else LAPTOP)
    for r in (rs if isinstance(rs, list) else [rs]):
        publish(r, a.out, a.date or dt.date.today().isoformat())
    return 0
