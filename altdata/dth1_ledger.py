"""
DTH-1, the day-trading layer's box pieces (ruling D41, 27 Oct 2026; A92).

    python -m altdata.dth1_ledger [--ending YYYY-MM-DD] [--path CSV]

Two things, both read-only:

- THE CHECKLIST: the rules block the 07:00 anchor prints after the ES read,
  worded in config/dth1.yaml and switched off there. Rules only: no prices, no
  sizes, no orders (D41: those print on the chat-side card alone).
- THE LEDGER READER: the operator's manual ledger, copied from a private Drive
  folder into the box's inbox (~/chester-data/inbox/dth1/) by the nightly sweep,
  read by header name and reduced to AGGREGATES for the Weekly's book section:
  trades this week and to date, the share with no rule broken, mean and median
  R per trade, the win rate, the largest loss in R and promotions to Book C.

THE PRIVACY RULE (the repo is public). Nothing here prints a currency, a price,
a size or a single trade's row: only counts and R-multiples. The ledger is never
read from the repo, and the reader writes nothing to the store. A row marked for
verification, or with a blank result, waits for the broker statement: counted
and named as "k rows awaiting the statement", never filled or scored. A missing
column is named, never guessed.
"""

from __future__ import annotations

import csv
import datetime as dt
import html
import re
import statistics
from pathlib import Path
from typing import Any, Optional

import yaml

CONFIG = Path(__file__).resolve().parent.parent / "config" / "dth1.yaml"
NOT_STORED = "DTH-1 ledger not stored"
TITLE = "DTH-1 (manual)"


def config(path: Optional[Path] = None) -> dict:
    return yaml.safe_load(Path(path or CONFIG).read_text(encoding="utf-8")) or {}


# ---------------------------------------------------------------------------
# The checklist (the 07:00 anchor)
# ---------------------------------------------------------------------------
def checklist(cfg: Optional[dict] = None) -> dict:
    """{enabled, title, lines}: the block as config words it; disabled, no lines."""
    c = (cfg or config()).get("checklist") or {}
    if not c.get("enabled"):
        return {"enabled": False, "title": c.get("title") or "", "lines": []}
    lines = [str(r) for r in c.get("rules") or []]
    if c.get("promotion"):
        lines.append(" ".join(str(c["promotion"]).split()))
    return {"enabled": True, "title": str(c.get("title") or ""), "lines": lines,
            "footer": str(c.get("footer") or "")}


def checklist_html(block: Optional[dict]) -> str:
    if not block or not block.get("enabled"):
        return ""
    items = "".join(f"<li>{html.escape(x)}</li>" for x in block["lines"])
    foot = (f'<p style="margin:4px 0 0 0;color:#555;font-size:12px">'
            f'{html.escape(block["footer"])}</p>' if block.get("footer") else "")
    return (f'<h2 style="font-size:16px;margin:18px 0 6px 0">'
            f'{html.escape(block["title"])}</h2>'
            f'<ul style="margin:0;padding-left:18px">{items}</ul>{foot}')


def checklist_text(block: Optional[dict]) -> list[str]:
    if not block or not block.get("enabled"):
        return []
    return [block["title"]] + [f"  - {x}" for x in block["lines"]]


# ---------------------------------------------------------------------------
# The ledger reader (the Weekly)
# ---------------------------------------------------------------------------
def _key(h: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(h or "").strip().lower()).strip("_")


def _date(s: str) -> Optional[dt.date]:
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d %b %Y"):
        try:
            return dt.datetime.strptime(s[:10] if fmt == "%Y-%m-%d" else s, fmt).date()
        except ValueError:
            continue
    return None


def _r(s: str) -> Optional[float]:
    s = (s or "").strip().replace("−", "-").rstrip("Rr").strip()
    try:
        return float(s)
    except ValueError:
        return None


def read(path: Optional[str] = None, ending: Optional[dt.date] = None,
         cfg: Optional[dict] = None) -> dict:
    """The ledger's aggregates as of the week ending `ending` (a Sunday or any
    day; the week is the seven days ending on it). Never a row."""
    c = cfg or config()
    lc = c.get("ledger") or {}
    p = Path(path or lc.get("path") or "").expanduser()
    if not p.is_file():
        return {"state": "not_stored", "path": str(p)}
    with p.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return {"state": "not_stored", "path": str(p)}
    head = [_key(h) for h in rows[0]]
    col: dict[str, Optional[int]] = {}
    for field, names in (lc.get("columns") or {}).items():
        col[field] = next((head.index(_key(n)) for n in names if _key(n) in head), None)
    missing = [f for f in lc.get("required") or [] if col.get(f) is None]
    if missing:
        return {"state": "missing_columns", "missing": missing}
    truthy = {str(t).lower() for t in lc.get("truthy") or []}
    waiting = {str(w).lower() for w in lc.get("awaiting_words") or []}

    def cell(r: list, f: str) -> str:
        i = col.get(f)
        return r[i].strip() if i is not None and i < len(r) else ""

    ending = ending or dt.date.today()
    start = ending - dt.timedelta(days=6)
    done, awaiting, undated = [], 0, 0
    for r in rows[1:]:
        if not any(x.strip() for x in r):
            continue
        res = _r(cell(r, "result_r"))
        if res is None or cell(r, "status").lower() in waiting:
            awaiting += 1
            continue
        d = _date(cell(r, "date"))
        if d is None:
            undated += 1
            continue
        if d > ending:
            continue
        done.append((d, res, cell(r, "rule_broken").lower() in truthy,
                     cell(r, "promoted").lower() in truthy))
    rs = [x[1] for x in done]
    n = len(done)
    clean = sum(1 for x in done if not x[2])
    return {
        "state": "ok", "ending": ending.isoformat(),
        "week_n": sum(1 for x in done if start <= x[0] <= ending), "total_n": n,
        "clean_n": clean, "clean_share": (clean / n) if n else None,
        "mean_r": statistics.fmean(rs) if rs else None,
        "median_r": statistics.median(rs) if rs else None,
        "wins": sum(1 for v in rs if v > 0),
        "win_rate": (sum(1 for v in rs if v > 0) / n) if n else None,
        "largest_loss_r": min([v for v in rs if v < 0], default=None),
        "promotions": sum(1 for x in done if x[3]),
        "awaiting": awaiting, "undated": undated,
        "promotion_column": col.get("promoted") is not None,
    }


def _rr(v: Optional[float]) -> str:
    return "n/a" if v is None else f"{v:+.2f}R".replace("-", "−")


def weekly_lines(agg: dict) -> list[str]:
    """The Weekly's lines: aggregates only, counts and R."""
    st = agg.get("state")
    if st == "not_stored":
        return [f"{NOT_STORED}."]
    if st == "missing_columns":
        return [f"{TITLE}: the ledger has no column for "
                f"{', '.join(agg['missing'])}; nothing is scored until it does."]
    n = agg["total_n"]
    if not n:
        out = [f"{TITLE}: no scored trades yet."]
    else:
        out = [f"{TITLE}: {agg['week_n']} trade(s) this week, {n} to date; "
               f"no rule broken in {agg['clean_n']} of {n} "
               f"({100 * agg['clean_share']:.0f}%); R per trade mean "
               f"{_rr(agg['mean_r'])}, median {_rr(agg['median_r'])}; win rate "
               f"{100 * agg['win_rate']:.0f}% ({agg['wins']} of {n}); largest loss "
               f"{_rr(agg['largest_loss_r']) if agg['largest_loss_r'] is not None else 'none'}; "
               f"promotions to Book C: "
               f"{agg['promotions'] if agg['promotion_column'] else 'not tracked (no column)'}."]
    if agg.get("awaiting"):
        out.append(f"{agg['awaiting']} row(s) awaiting the statement.")
    if agg.get("undated"):
        out.append(f"{agg['undated']} row(s) without a readable date, not counted.")
    return out


def weekly_subsection(ending: Optional[str] = None, path: Optional[str] = None) -> dict:
    """The book section's subsection: a title and its lines."""
    end = dt.date.fromisoformat(ending[:10]) if ending else None
    try:
        agg = read(path, end)
    except Exception as exc:                                    # noqa: BLE001
        agg = {"state": "missing_columns", "missing": [f"a readable file ({type(exc).__name__})"]}
    return {"title": TITLE, "lines": weekly_lines(agg), "data": agg}


def _main(argv: Optional[list[str]] = None) -> int:
    import argparse                                             # noqa: PLC0415
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ending", default=None)
    ap.add_argument("--path", default=None)
    a = ap.parse_args(argv)
    for line in checklist_text(checklist()):
        print(line)
    print()
    for line in weekly_subsection(a.ending, a.path)["lines"]:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
