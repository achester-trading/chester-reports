"""
The system-metrics block (EL-6; the Enterprise Layer change order section 3.7):
the Monthly's detail table, and the Quarterly's opening table, computed by code.

    from altdata import system_metrics as sm
    d = sm.block("2026-10-01", "2026-10-31", sm.gather("2026-10-01", "2026-10-31", ...))

FIVE FIGURES, EACH WITH ITS WINDOW AND ITS SOURCE, NOTHING FETCHED:
  uptime            the share of `verdict=ok` lines in the heartbeat log over the
                    window (~/logs/heartbeat_check-YYYY-MM.log, one line per
                    check, verdict first -- scripts/check_heartbeat_cron.sh)
  feed completeness fresh over expected by feed family, from the freshness
                    roster (altdata/feeds.freshness) as of the window's end
  incidents         the count and the dated list from docs/incidents.md, parsed
                    from its entry lines ("- **INC-n YYYY-MM-DD** -- ...")
  model cost        tokens per report from the model_calls table (AUD-2's
                    meter: the response's usage fields per call, no prompt
                    text), "recorded from" its first call where the window
                    begins earlier
  withheld drafts   the count from the withheld-drafts log
                    (altdata/withheld_log.py, from 17 Oct 2026)

A source that does not exist prints "not recorded", never zero. The Audit #4
baseline (taken by hand, the agenda's I.3) prints beside a figure where the
agenda recorded one, as "baseline, by hand, Audit #4"; elsewhere nothing.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
INCIDENTS = REPO / "docs" / "incidents.md"
NOT_RECORDED = "not recorded"
ENTRY = re.compile(r"^- \*\*(INC-\d+) (\d{4}-\d{2}-\d{2})\*\* — (.*)$")


def _d(x: str) -> dt.date:
    return dt.date.fromisoformat(str(x)[:10])


def window_label(first: str, last: str) -> str:
    a, b = _d(first), _d(last)
    if a.year == b.year and a.month == b.month:
        return f"{a.day}–{b.day} {b:%b %Y}"
    return f"{a.day} {a:%b} – {b.day} {b:%b %Y}"


# ---------------------------------------------------------------------------
# The five readings, each from text or rows already read
# ---------------------------------------------------------------------------
def uptime(lines: Optional[list[str]], first: str, last: str) -> dict:
    """{ok, total, share} over the heartbeat lines dated in the window; None
    lines (no log) is not recorded."""
    if lines is None:
        return {"recorded": False}
    a, b = _d(first), _d(last)
    checks = [ln for ln in lines if " verdict=" in ln
              and len(ln) >= 10 and re.match(r"\d{4}-\d{2}-\d{2}", ln)
              and a <= _d(ln[:10]) <= b]
    ok = sum(1 for ln in checks if " verdict=ok " in ln + " ")
    return {"recorded": bool(checks), "ok": ok, "total": len(checks),
            "share": (ok / len(checks)) if checks else None}


def feeds(fresh: Optional[dict]) -> dict:
    """Fresh over expected by family, from a feeds.freshness() result."""
    if not fresh or not fresh.get("feeds"):
        return {"recorded": False}
    fam = {n: {"fresh": f.get("fresh", 0), "expected": f.get("expected", 0),
               "stale": f.get("stale", 0), "pending": f.get("pending", 0)}
           for n, f in fresh["feeds"].items()}
    return {"recorded": True, "families": fam,
            "fresh": sum(v["fresh"] for v in fam.values()),
            "expected": sum(v["expected"] for v in fam.values()),
            "as_of": fresh.get("session")}


def _clause(text: str) -> str:
    t = re.sub(r"[*`]", "", text).strip()
    m = re.search(r"[.:;](\s|$)", t)
    t = t[:m.start()] if m else t
    return t[:140].rstrip()


def incidents(md: Optional[str], first: str, last: str) -> dict:
    """The incidents dated in the window: [(id, date, first clause)]."""
    if md is None:
        return {"recorded": False}
    a, b = _d(first), _d(last)
    rows = []
    for ln in md.splitlines():
        m = ENTRY.match(ln.strip())
        if m and a <= _d(m.group(2)) <= b:
            rows.append((m.group(1), m.group(2), _clause(m.group(3))))
    return {"recorded": True, "count": len(rows), "entries": rows}


def model_cost(rows: Optional[list], first_call: Optional[str]) -> dict:
    """Tokens per report from model_calls rows (report, input, output, called_at).
    None rows (no table) is not recorded."""
    if rows is None:
        return {"recorded": False}
    by: dict[str, list[int]] = {}
    for rep, i, o, _at in rows:
        t = by.setdefault(str(rep), [0, 0, 0])
        t[0] += 1
        t[1] += int(i or 0)
        t[2] += int(o or 0)
    return {"recorded": True, "by_report": by, "first_call": first_call,
            "calls": sum(v[0] for v in by.values()),
            "input": sum(v[1] for v in by.values()),
            "output": sum(v[2] for v in by.values())}


def withheld(lines: Optional[list[str]], first: str, last: str) -> dict:
    """Distinct withheld drafts (report, edition, section) in the window, from
    the log's JSON lines. None lines (no log) is not recorded."""
    if lines is None:
        return {"recorded": False}
    a, b = _d(first), _d(last)
    seen, start = set(), None
    for ln in lines:
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        at = str(r.get("at") or "")[:10]
        if not at:
            continue
        start = at if start is None or at < start else start
        if a <= _d(at) <= b:
            seen.add((r.get("report"), r.get("edition"), r.get("section")))
    return {"recorded": True, "count": len(seen), "first": start}


# ---------------------------------------------------------------------------
# Reading the sources (read-only; nothing fetched)
# ---------------------------------------------------------------------------
def _months(first: str, last: str) -> list[str]:
    a, b = _d(first).replace(day=1), _d(last)
    out = []
    while a <= b:
        out.append(f"{a:%Y-%m}")
        a = (a + dt.timedelta(days=32)).replace(day=1)
    return out


def heartbeat_lines(first: str, last: str, log_dir: Optional[str] = None) -> Optional[list[str]]:
    d = Path(log_dir or os.environ.get("CHESTER_LOG_DIR") or Path.home() / "logs")
    files = [d / f"heartbeat_check-{m}.log" for m in _months(first, last)]
    files = [f for f in files if f.exists()]
    if not files:
        return None
    out: list[str] = []
    for f in files:
        out += f.read_text(encoding="utf-8", errors="replace").splitlines()
    return out


def model_rows(db_path: Optional[str], first: str, last: str) -> tuple[Optional[list], Optional[str]]:
    """(rows in the ET window, the table's first call) -- (None, None) with no table."""
    import sqlite3                                              # noqa: PLC0415
    from . import model_meter, observations                     # noqa: PLC0415
    path = Path(db_path or observations.DEFAULT_DB)
    if not path.exists():
        return None, None
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                            "name='model_calls'").fetchone():
            return None, None
        firstc = conn.execute("SELECT MIN(called_at) FROM model_calls").fetchone()[0]
    finally:
        conn.close()
    rows = model_meter._rows(db_path, *model_meter._et_bounds(_d(first), _d(last)))  # noqa: SLF001
    return list(rows), firstc


def gather(first: str, last: str, *, st=None, cutoff: Optional[str] = None,
           db_path: Optional[str] = None, log_dir: Optional[str] = None,
           archive_dir: Optional[str] = None,
           incidents_path: Optional[Path] = None) -> dict:
    """Every source read, as the block takes them. A source that faults or does
    not exist is None (not recorded)."""
    from . import withheld_log                                  # noqa: PLC0415
    out: dict[str, Any] = {}
    try:
        out["heartbeat"] = heartbeat_lines(first, last, log_dir)
    except OSError:
        out["heartbeat"] = None
    try:
        from . import feeds as feeds_mod                        # noqa: PLC0415
        out["freshness"] = feeds_mod.freshness(as_of=cutoff, store=st) if st is not None else None
    except Exception:                                           # noqa: BLE001
        out["freshness"] = None
    p = incidents_path or INCIDENTS
    out["incidents"] = p.read_text(encoding="utf-8") if p.exists() else None
    try:
        out["model_rows"], out["first_call"] = model_rows(db_path, first, last)
    except Exception:                                           # noqa: BLE001
        out["model_rows"], out["first_call"] = None, None
    out["withheld"] = withheld_log.read(archive_dir)
    return out


# ---------------------------------------------------------------------------
# The block
# ---------------------------------------------------------------------------
def _n(x: int) -> str:
    return f"{x:,}"


def block(first: str, last: str, src: dict, baseline: Optional[dict] = None,
          title: Optional[str] = None) -> dict:
    """The detail block: one table of the five figures (each with its window and
    source, and the Audit #4 baseline where recorded), the families' table, the
    tokens by report, and the dated incident list."""
    win = window_label(first, last)
    bl = baseline or {}
    up = uptime(src.get("heartbeat"), first, last)
    fd = feeds(src.get("freshness"))
    inc = incidents(src.get("incidents"), first, last)
    mc = model_cost(src.get("model_rows"), src.get("first_call"))
    wh = withheld(src.get("withheld"), first, last)
    rows = []
    rows.append(["Uptime",
                 (f"{100 * up['share']:.1f}% ({up['ok']} of {up['total']} checks "
                  f"verdict=ok)" if up.get("recorded") else NOT_RECORDED),
                 win, "the heartbeat log, verdict=ok lines", bl.get("uptime") or "—"])
    rows.append(["Feed completeness",
                 (f"{_n(fd['fresh'])} of {_n(fd['expected'])} fresh "
                  f"({100 * fd['fresh'] / fd['expected']:.1f}%)"
                  if fd.get("recorded") and fd["expected"] else NOT_RECORDED),
                 (f"at the {_d(fd['as_of']).day} {_d(fd['as_of']):%b} close"
                  if fd.get("as_of") else f"at {_d(last).day} {_d(last):%b}"),
                 "the freshness roster, by family", bl.get("feeds") or "—"])
    rows.append(["Incidents",
                 (f"{inc['count']}" + (f" ({inc['entries'][0][0]} to {inc['entries'][-1][0]})"
                                       if inc["count"] > 1 else
                                       f" ({inc['entries'][0][0]})" if inc["count"] else "")
                  if inc.get("recorded") else NOT_RECORDED),
                 win, "docs/incidents.md, its dated entry lines",
                 bl.get("incidents") or "—"])
    if mc.get("recorded") and mc["calls"]:
        fc = mc.get("first_call")
        mwin = (f"{window_label(fc, last)} (recorded from {_d(fc).day} {_d(fc):%b %Y})"
                if fc and _d(fc) > _d(first) else win)
        rows.append(["Model cost", f"{_n(mc['input'])} input / {_n(mc['output'])} output "
                     f"tokens, {_n(mc['calls'])} calls", mwin,
                     "model_calls (each response's usage; no prompt text)",
                     bl.get("model_cost") or "—"])
    else:
        rows.append(["Model cost", NOT_RECORDED if not mc.get("recorded") else "0 calls",
                     win, "model_calls (each response's usage; no prompt text)",
                     bl.get("model_cost") or "—"])
    if wh.get("recorded"):
        ws = wh.get("first")
        wwin = (f"{window_label(ws, last)} (recorded from {_d(ws).day} {_d(ws):%b %Y})"
                if ws and _d(ws) > _d(first) else win)
        rows.append(["Withheld drafts", str(wh["count"]), wwin, "the withheld-drafts log",
                     bl.get("withheld") or "—"])
    else:
        rows.append(["Withheld drafts", NOT_RECORDED, win, "the withheld-drafts log",
                     bl.get("withheld") or "—"])
    lab = bl.get("label")
    if lab:
        for r in rows:
            if r[4] not in ("—", NOT_RECORDED):
                r[4] = f"{r[4]} ({lab})"
    tables = [{"columns": ["Metric", title or "The period", "Window", "Source",
                           "Baseline, by hand, Audit #4"], "rows": rows}]
    # RULING 5 OF 17 OCT 2026: the audit's measured figures, each with its label;
    # what was not recorded says so.
    if bl.get("measured"):
        tables.append({"columns": ["Audit #4 baseline", "Figure", "Label"],
                       "rows": [[m, f, "" if f == NOT_RECORDED else (lab or "by hand")]
                                for m, f in bl["measured"]]})
    if fd.get("recorded"):
        tables.append({"columns": ["Feed family", "Fresh", "Expected", "Stale", "Pending"],
                       "rows": [[n, v["fresh"], v["expected"], v["stale"], v["pending"]]
                                for n, v in sorted(fd["families"].items())]})
    if mc.get("recorded") and mc["calls"]:
        tables.append({"columns": ["Report", "Calls", "Input tokens", "Output tokens"],
                       "rows": [[r, _n(v[0]), _n(v[1]), _n(v[2])]
                                for r, v in sorted(mc["by_report"].items())]})
    lines = [f"{i} {d} — {c}." for i, d, c in (inc.get("entries") or [])]
    return {"id": "system_metrics",
            "title": f"System metrics, {title}" if title else "System metrics",
            "tables": tables, "lines": lines,
            "data": {"uptime": up, "feeds": {k: v for k, v in fd.items() if k != "families"},
                     "incidents": {"count": inc.get("count"), "recorded": inc.get("recorded")},
                     "model_cost": {k: v for k, v in mc.items() if k != "by_report"},
                     "withheld": wh}}


def baseline(cfg: Optional[dict] = None) -> dict:
    """The Audit #4 baseline row (by hand; docs/briefs/audit-4-agenda.md I.3), as
    transcribed into config/reporting_stack.yaml `system_metrics`."""
    if cfg is None:
        from altdata import bars as bars_mod                    # noqa: PLC0415
        cfg = bars_mod.load_config()
    return dict(((cfg.get("system_metrics") or {}).get("baseline_audit_4")) or {})


def _main(argv: list[str]) -> int:
    """`show --month YYYY-MM [--db PATH] [--archive-dir DIR]`: the block over one
    month, printed as text. Read-only; nothing fetched."""
    import argparse                                             # noqa: PLC0415
    from altdata import observations, session                   # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m altdata.system_metrics")
    ap.add_argument("cmd", choices=["show"])
    ap.add_argument("--month", required=True)
    ap.add_argument("--db", default=None)
    ap.add_argument("--archive-dir", default=None)
    a = ap.parse_args(argv)
    y, m = (int(x) for x in a.month.split("-"))
    first = dt.date(y, m, 1)
    last = dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)
    with observations.ObservationStore(a.db) as st:
        src = gather(first.isoformat(), last.isoformat(), st=st, cutoff=session.utc_iso(),
                     db_path=a.db, archive_dir=a.archive_dir)
    b = block(first.isoformat(), last.isoformat(), src, baseline(), title=f"{first:%B %Y}")
    print(b["title"])
    for t in b["tables"]:
        print(" | ".join(str(c) for c in t["columns"]))
        for r in t["rows"]:
            print(" | ".join(str(c) for c in r))
        print()
    for ln in b["lines"]:
        print(ln)
    return 0


if __name__ == "__main__":
    import sys                                                  # noqa: PLC0415
    sys.exit(_main(sys.argv[1:]))
