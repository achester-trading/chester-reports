"""
Calibration ledgers: Batch 6 Tranche 2, part 1 (meme-ingest-ledgers-1, 17 Oct
2026) -- ST-R5.30b, 32b, 35b, 36b and 43b
(docs/change-order-signal-triage-batch-6-2026-10-15.md).

    python -m altdata.ledgers run <item> [--source public|store] [--out DIR]
    python -m altdata.ledgers run all --source public

THE FORM is the integrated order's (docs/change-order-signal-triage-2026-09-25.md
§1.10; docs/ledgers/README.md): one dated file per study,
docs/ledgers/<item>-ledger-<date>.md, stating its data source and vintage, its
as-of, window and n, the statistic the order names, the pass rule AS THE ORDER
STATES IT and the verdict that rule gives -- never a verdict by judgment -- with a
CSV of the episodes beside it. A rerun writes a new dated file; an old one is
never edited.

THE SOURCES. Each study is arithmetic over named series, and two providers fill
them:
  public  the sources themselves, full history, through the writers' own readers
          where one exists (Shiller's reader, BIS's table, Redfin's data-center
          file, Yahoo through altdata.import_yfinance) and FRED's public graph CSV
          for FRED series. This is §1.10's offline rule ("scripts pull full
          history directly"), and the laptop's first edition uses it.
  store   the box's observation store, the newest vintage of each mapped key.
          NOT an as-of replay: the store's as-of history begins 30 May 2026
          (§1.10), so a store run reads the same values as a public run, from
          whatever the writers have stored. A key the store lacks is named and
          the study refuses to run rather than run short.

NOTHING HERE GRANTS A RIGHT. Each ledger states its rights consequence in one
line, as the order words it, and enters no composite, flag table or queue.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import math
import os
from pathlib import Path
from typing import Callable, Iterable, Optional, Sequence

REPO = Path(__file__).resolve().parent.parent.parent
LEDGER_DIR = REPO / "docs" / "ledgers"
NO_GATE = ("NO GATE IN THE ORDER -- base rate recorded. The order names this "
           "study but states no pass rule; none is supplied here, by judgment or "
           "otherwise. A gate, if one is wanted, is the operator's to pre-register.")

Series = list[tuple[str, float]]          # [(ISO date, value)], ascending


# ---------------------------------------------------------------------------
# Statistics -- small, explicit, and each reproduced by hand in the gate
# ---------------------------------------------------------------------------
def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def ols(x: Sequence[float], y: Sequence[float]) -> dict:
    """y = a + b x by least squares: a, b, r2, n, the residuals."""
    n = len(x)
    if n < 3 or n != len(y):
        raise ValueError(f"ols needs >= 3 paired points, got {n}")
    mx, my = mean(x), mean(y)
    sxx = sum((xi - mx) ** 2 for xi in x)
    sxy = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    b = sxy / sxx
    a = my - b * mx
    res = [yi - (a + b * xi) for xi, yi in zip(x, y)]
    syy = sum((yi - my) ** 2 for yi in y)
    r2 = 1.0 - sum(r * r for r in res) / syy if syy else 0.0
    return {"a": a, "b": b, "r2": r2, "n": n, "residuals": res}


def corr(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    n = len(x)
    if n < 3:
        return None
    mx, my = mean(x), mean(y)
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    if not sx or not sy:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def percentile_rank(history: Sequence[float], value: float) -> float:
    """Share of `history` at or below `value`, in percent (the stack's rule)."""
    if not history:
        raise ValueError("an empty history has no percentile")
    return 100.0 * sum(1 for h in history if h <= value) / len(history)


def quantile(xs: Sequence[float], q: float) -> float:
    """The q-quantile (0..1), linear between order statistics."""
    s = sorted(xs)
    if not s:
        raise ValueError("an empty sample has no quantile")
    pos = q * (len(s) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def align(*series: Series) -> list[tuple]:
    """(date, v1, v2, ...) on the dates every series carries."""
    maps = [dict(s) for s in series]
    common = sorted(set(maps[0]).intersection(*maps[1:]))
    return [(d, *[m[d] for m in maps]) for d in common]


def month_key(d: str) -> str:
    return str(d)[:7]


def to_monthly_last(s: Series) -> Series:
    """The last observation of each month, dated the month's first day."""
    out: dict[str, float] = {}
    for d, v in s:
        out[month_key(d) + "-01"] = v
    return sorted(out.items())


def to_quarterly_mean(s: Series) -> Series:
    """The quarter's mean, dated the quarter's first day."""
    acc: dict[str, list[float]] = {}
    for d, v in s:
        y, m = int(d[:4]), int(d[5:7])
        q = f"{y}-{(m - 1) // 3 * 3 + 1:02d}-01"
        acc.setdefault(q, []).append(v)
    return sorted((q, mean(vs)) for q, vs in acc.items())


def yoy(s: Series, lag: int) -> Series:
    """Percent change on the observation `lag` places earlier."""
    return [(s[i][0], 100.0 * (s[i][1] / s[i - lag][1] - 1.0))
            for i in range(lag, len(s)) if s[i - lag][1]]


def episodes(flags: Sequence[tuple[str, bool]], merge_gap: int = 0) -> list[tuple[str, str]]:
    """Contiguous runs of True as (start, end); runs separated by at most
    `merge_gap` False observations are one episode."""
    out: list[list] = []
    gap = 0
    for d, on in flags:
        if on:
            if out and gap <= merge_gap and out[-1][2]:
                out[-1][1] = d
            else:
                out.append([d, d, True])
            gap = 0
        else:
            gap += 1
            if out and gap > merge_gap:
                out[-1][2] = False
    return [(a, b) for a, b, _ in out]


# ---------------------------------------------------------------------------
# The ledger file
# ---------------------------------------------------------------------------
REQUIRED = ("item", "title", "as_of", "window", "n", "statistic", "pass_rule",
            "verdict", "rights", "sources", "source_mode")


def ledger_faults(r: dict) -> list[str]:
    """A ledger without its as-of, window or n (or the other required fields)
    is not a ledger."""
    out = [f"missing {k}" for k in REQUIRED if r.get(k) in (None, "", [])]
    if r.get("n") is not None and not isinstance(r["n"], int):
        out.append("n is not an integer")
    return out


def render(r: dict, run_date: str) -> str:
    lines = [f"# {r['item']} ledger -- {r['title']}",
             "",
             f"**Edition:** {run_date}, {r['source_mode']}. "
             + ("A re-run against the box's store supersedes it (a new dated file)."
                if r["source_mode"].startswith("laptop") else ""),
             "",
             "| | |", "|---|---|",
             f"| As of | {r['as_of']} |",
             f"| Window | {r['window']} |",
             f"| n | {r['n']} |",
             f"| Statistic | {r['statistic']} |",
             f"| Pass rule (as the order states it) | {r['pass_rule']} |",
             f"| Verdict | **{r['verdict']}** |",
             f"| Rights consequence | {r['rights']} |",
             "",
             "## Sources and vintages", ""]
    lines += [f"- {s}" for s in r["sources"]]
    lines += ["", "## Results", ""]
    lines += list(r.get("body") or [])
    if r.get("caveats"):
        lines += ["", "## Caveats", ""] + [f"- {c}" for c in r["caveats"]]
    if r.get("csv_name"):
        lines += ["", f"The episodes are in `{r['csv_name']}`, beside this file."]
    return "\n".join(lines) + "\n"


def write_ledger(r: dict, out_dir: Optional[Path] = None,
                 run_date: Optional[str] = None) -> tuple[Path, Optional[Path]]:
    faults = ledger_faults(r)
    if faults:
        raise ValueError(f"{r.get('item')}: not a ledger: {faults}")
    run_date = run_date or dt.date.today().isoformat()
    out_dir = Path(out_dir or LEDGER_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{r['item'].lower()}-ledger-{run_date}"
    csv_path = None
    if r.get("episodes"):
        csv_path = out_dir / f"{stem}-episodes.csv"
        r["csv_name"] = csv_path.name
        cols = list(r["episodes"][0].keys())
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(r["episodes"])
        csv_path.write_text(buf.getvalue(), encoding="utf-8", newline="\n")
    md = out_dir / f"{stem}.md"
    md.write_text(render(r, run_date), encoding="utf-8", newline="\n")
    return md, csv_path


def ordinal(x: float) -> str:
    """12 -> "12th", 2 -> "2nd", 101 -> "101st" (a percentile, rounded)."""
    n = int(round(x))
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def fmt(v: Optional[float], nd: int = 2, pct: bool = False) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    return f"{v:+.{nd}f}{'%' if pct else ''}" if pct else f"{v:.{nd}f}"
