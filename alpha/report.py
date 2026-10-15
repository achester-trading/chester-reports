"""
The monthly Lab report (X-2.8), mailed with the Monthly.

    python -m alpha.report [YYYY-MM] [--ledger PATH]     # print it

One Markdown page from alpha.db, read-only, for the month:

  1. the engines and their posteriors (the latest edge_posterior of each);
  2. the loop's events, counted by kind, with every governor transition, kill,
     re-fit decision and operator event listed;
  3. promotions and retirements;
  4. the failures register's additions: every hypothesis that failed this
     month, with the metric that failed it;
  5. the cost calibration: modelled against stored spreads, per engine and
     class, at the month's last record;
  6. the lab's P&L and drawdown against the governor (the lab's -15% halt; each
     engine's -10% halve and -20% stop).

The Monthly attaches it through ONE hook in monthly_macro/run.py
(monthly_attachment), which never raises: a lab that cannot be read costs the
Monthly nothing. Re-sending an archived Monthly rebuilds this page from the
ledger as it stands then, dated with its as-of.
"""

from __future__ import annotations

import calendar
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Optional

from . import config as acfg
from . import lab_line

GOVERNOR_KINDS = ("halve", "stop", "restore", "lab_halt", "lab_resume", "kill")
REFIT_KINDS = ("refit_accepted", "refit_rejected", "refit_out_of_range")


def _month_bounds(month: str) -> tuple[str, str]:
    y, m = int(month[:4]), int(month[5:7])
    last = calendar.monthrange(y, m)[1]
    return f"{y:04d}-{m:02d}-01", f"{y:04d}-{m:02d}-{last:02d}"


def _pct(x: Optional[float], d: int = 2) -> str:
    return "–" if x is None else f"{x * 100:+.{d}f}%"


def render(ledger, month: str, as_of: Optional[str] = None) -> str:
    from .ledger import LAB                                     # noqa: PLC0415
    first, last = _month_bounds(month)
    t0, t1 = f"{first}T00:00:00", f"{last}T23:59:59.999999"
    con = acfg.constitution()
    out = [f"# Alpha Lab, the month of {dt.date.fromisoformat(first):%B %Y}", "",
           f"From alpha.db, read-only{', as of ' + as_of if as_of else ''}. A machine's "
           f"book in ledger-paper: evidence for the sitting, never an instruction to it.",
           "", f"**{lab_line.weekly_line(as_of or t1 + '+00:00', ledger.path)}**", ""]
    # 1. engines and posteriors
    out += ["## 1. Engines and their posteriors", ""]
    engines = ledger.engines()
    if not engines:
        out += ["No engine registered.", ""]
    else:
        out += ["| Engine | Family | Status | n graded | Win rate (posterior) | "
                "Expectancy (posterior) | Prior strength |",
                "|---|---|---|---:|---:|---:|---:|"]
        for e in engines:
            p = ledger.one("SELECT * FROM edge_posterior WHERE engine_id=? AND day<=? "
                           "ORDER BY day DESC LIMIT 1", (e["id"], last))
            if p:
                out.append(f"| {e['id']} | {e['family']} | {e['status']} | {p['n']} | "
                           f"{p['win_mean'] * 100:.1f}% | {_pct(p['exp_mean'], 3)} | "
                           f"{p['prior_strength']:.0f} |")
            else:
                out.append(f"| {e['id']} | {e['family']} | {e['status']} | 0 | – | – | – |")
        out.append("")
    # 2. the loop's events
    evs = ledger.q("SELECT * FROM loop_events WHERE written_at>=? AND written_at<=? "
                   "ORDER BY id", (t0, t1))
    out += ["## 2. The loop's events", ""]
    if not evs:
        out += ["None this month.", ""]
    else:
        counts: dict[str, int] = {}
        for e in evs:
            counts[e["kind"]] = counts.get(e["kind"], 0) + 1
        out += ["| Kind | Count |", "|---|---:|"] + \
            [f"| {k} | {v} |" for k, v in sorted(counts.items())] + [""]
        notable = [e for e in evs if e["kind"] in GOVERNOR_KINDS + REFIT_KINDS
                   or e["source"] == "operator"]
        if notable:
            out += ["Every governor transition, kill, re-fit decision and operator event:",
                    "", "| When | Kind | Engine | Source | Detail |", "|---|---|---|---|---|"]
            for e in notable:
                det = (e["after"] or "")[:160].replace("|", "/")
                out.append(f"| {e['written_at'][:16]} | {e['kind']} | {e['engine'] or ''} | "
                           f"{e['source']} | {det} |")
            out.append("")
    # 3. promotions and retirements
    out += ["## 3. Promotions and retirements", ""]
    pr = [e for e in evs if e["kind"] in ("promotion", "kill")]
    if not pr:
        out += ["None this month.", ""]
    else:
        out += ["| When | Engine | Change | Source |", "|---|---|---|---|"]
        for e in pr:
            what = "promoted to paper at min_size" if e["kind"] == "promotion" else "retired"
            out.append(f"| {e['written_at'][:10]} | {e['engine']} | {what} | {e['source']} |")
        out.append("")
    # 4. the failures register's additions
    out += ["## 4. The failures register's additions", ""]
    failed = ledger.q("SELECT * FROM hypotheses WHERE status='failed' AND written_at>=? "
                      "AND written_at<=? ORDER BY id", (t0, t1))
    if not failed:
        out += ["None this month.", ""]
    else:
        out += ["| Id | Title | Family | Source | Why it failed |", "|---|---|---|---|---|"]
        for h in failed:
            out.append(f"| {h['id']} | {h['title']} | {h['family']} | {h['source']} | "
                       f"{(h['status_reason'] or '').replace('|', '/')} |")
        out.append("")
    # 5. cost calibration
    out += ["## 5. The cost calibration", ""]
    cc = ledger.q("SELECT c.* FROM cost_calibration c JOIN (SELECT engine_id, cost_class, "
                  "MAX(day) AS d FROM cost_calibration WHERE day<=? GROUP BY engine_id, "
                  "cost_class) m ON c.engine_id=m.engine_id AND c.cost_class=m.cost_class "
                  "AND c.day=m.d ORDER BY c.engine_id", (last,))
    if not cc:
        out += ["No fill against a stored quote yet: nothing to calibrate against.", ""]
    else:
        out += ["| Engine | Class | n | Modelled spread (bps) | Stored spread (bps) | Ratio |",
                "|---|---|---:|---:|---:|---:|"]
        def f(v: Optional[float], d: int = 1) -> str:
            return "–" if v is None else f"{v:.{d}f}"
        for c in cc:
            out.append(f"| {c['engine_id']} | {c['cost_class']} | {c['n']} | "
                       f"{f(c['modelled_bps'])} | {f(c['stored_bps'])} | "
                       f"{f(c['ratio'], 2)} |")
        out.append("")
    # 6. P&L and drawdown against the governor
    g = con["governor"]
    out += ["## 6. The lab's P&L and drawdown against the governor", ""]
    rows = ledger.q("SELECT * FROM equity WHERE engine_id=? AND day>=? AND day<=? "
                    "ORDER BY day", (LAB, first, last))
    before = ledger.one("SELECT equity FROM equity WHERE engine_id=? AND day<? ORDER BY "
                        "day DESC LIMIT 1", (LAB, first))
    if not rows:
        out += ["No equity recorded this month.", ""]
    else:
        start = float(before["equity"]) if before else float(rows[0]["equity"])
        end = float(rows[-1]["equity"])
        worst = min(float(r["drawdown"]) for r in rows)
        out += [f"- Lab equity {start:,.0f} -> {end:,.0f} lab dollars "
                f"({_pct(end / start - 1 if start else None)} on the month).",
                f"- Deepest drawdown from the high-water mark: {worst * 100:.1f}%, against "
                f"the lab's halt at {g['portfolio']['stop_at'] * 100:.0f}%.", ""]
        out += [f"| Engine | Deepest drawdown | Halve at {g['engine']['halve_at'] * 100:.0f}% "
                f"| Stop at {g['engine']['stop_at'] * 100:.0f}% |", "|---|---:|---|---|"]
        for e in engines:
            r = ledger.one("SELECT MIN(drawdown) AS dd FROM equity WHERE engine_id=? AND "
                           "day>=? AND day<=?", (e["id"], first, last))
            if r and r["dd"] is not None:
                dd = float(r["dd"])
                out.append(f"| {e['id']} | {dd * 100:.1f}% | "
                           f"{'reached' if dd <= g['engine']['halve_at'] else 'clear'} | "
                           f"{'reached' if dd <= g['engine']['stop_at'] else 'clear'} |")
        out.append("")
    return "\n".join(out)


def monthly_attachment(stamp: str, path: Optional[str | Path] = None
                       ) -> Optional[tuple[str, str, str]]:
    """(filename, markdown, "markdown") for the Monthly's email, or None. Never
    raises: the Monthly is never the lab's casualty."""
    try:
        p = Path(path or acfg.ledger_path())
        if not p.is_file():
            return None
        from altdata import session                             # noqa: PLC0415
        from .ledger import Ledger                              # noqa: PLC0415
        lg = Ledger(p, read_only=True)
        try:
            month = str(stamp)[:7]
            return (f"alpha_lab_report_{month}.md",
                    render(lg, month, session.utc_iso()), "markdown")
        finally:
            lg.close()
    except Exception:                                         # noqa: BLE001
        return None


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    from .ledger import Ledger                                  # noqa: PLC0415
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m alpha.report")
    ap.add_argument("month", nargs="?", default=dt.date.today().strftime("%Y-%m"))
    ap.add_argument("--ledger")
    a = ap.parse_args(argv)
    with Ledger(a.ledger, read_only=True) as lg:
        print(render(lg, a.month))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
