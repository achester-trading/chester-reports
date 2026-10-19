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
     engine's -10% halve and -20% stop);
  7. the tells imported as hypotheses, counted by source (X-3.6);
  8. the system's own event base rates, each row with n and its window (X-3.1);
  9. the paper book's crypto rows: venue, leg sizes, funding accrued (X-3.2);
 10. the grammar search's line: tested, survivors, the deflation, and the
     variables that passed and failed coverage, each with its history's first
     date (X-3.5; ruling 5(a) of 19 Oct 2026).

The Monthly attaches it through ONE hook in monthly_macro/run.py
(monthly_attachment), which never raises: a lab that cannot be read costs the
Monthly nothing. Re-sending an archived Monthly rebuilds this page from the
ledger as it stands then, dated with its as-of.

THE QUARTERLY'S LAB PAGE (X-3.7; lenses-group-b, 18 Oct 2026), quarter_page():
the lab's quarter, the engines, the loop's contribution (alpha/loops/quarterly.py's
counterfactuals and the adjustment it made, if any), the failures register and
the gate-ladder standing. It prints "no quarter closed yet" until the lab has run
through a whole calendar quarter. The Quarterly attaches it through the same
hook (quarterly_attachment), which never raises. Its prose lines are held to the
Quarterly's medium depth (config/reporting_stack.yaml depth_words_quarterly);
tables count no words, and it draws no chart.
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
    out += tranche_3(ledger, last)
    return "\n".join(out)


def _has(ledger, table: str) -> bool:
    return bool(ledger.one("SELECT 1 AS x FROM sqlite_master WHERE type='table' AND "
                           "name=?", (table,)))


def tranche_3(ledger, last: str) -> list[str]:
    """X-3's rows: the tells imported by source (X-3.6), the system's own event
    base rates with n and the window (X-3.1), and the paper book's crypto rows
    (X-3.2). Each section prints only what alpha.db holds."""
    from . import event_rates, tells                            # noqa: PLC0415
    out = ["## 7. The tells imported as hypotheses", ""]
    c = tells.counts(ledger) if _has(ledger, "hypotheses") else {}
    if not sum(c.values() or [0]):
        out += ["None imported yet (python -m alpha.tells import).", ""]
    else:
        out += ["| Source | Hypotheses |", "|---|---:|"] + \
            [f"| {k} | {c[k]} |" for k in tells.KINDS] + \
            [f"| all | {sum(c.values())} |", "",
             "Each is a question -- does the tell predict at its horizon after costs? -- "
             "registered needs_code; the fortnightly loop tests them on its own cadence.",
             ""]
    out += ["## 8. The system's own event base rates", ""]
    rates = event_rates.latest(ledger) if _has(ledger, "event_base_rates") else []
    if not rates:
        out += ["Not yet computed (python -m alpha.event_rates compute).", ""]
    else:
        out += [f"Computed {rates[0]['computed_on']}, from the store, read-only. A naive "
                f"surprise is actual less a declared naive expectation, not a consensus "
                f"surprise.", ""] + event_rates.table(rates) + [""]
    out += ["## 9. The paper book's crypto rows", ""]
    rows = ledger.q("SELECT * FROM carry_book WHERE opened_day<=? ORDER BY id",
                    (last,)) if _has(ledger, "carry_book") else []
    if not rows:
        out += ["None: engine 5 has not traded (it waits for its history window and the "
                "gate).", ""]
    else:
        out += ["| Coin | Venue | Opened | Spot qty | Perp qty | Funding accrued | "
                "Status | Net P&L |", "|---|---|---|---:|---:|---:|---|---:|"]
        for r in rows:
            net = "–" if r["net_pnl"] is None else f"{r['net_pnl']:,.2f}"
            out.append(f"| {r['coin']} | {r['venue']} | {r['opened_day']} | "
                       f"{r['spot_qty']:.6f} | {r['perp_qty']:.6f} | "
                       f"{r['funding_accrued']:,.2f} | {r['status']} | {net} |")
        out += ["", f"The basis: {rows[-1]['basis_note']}", ""]
    out += search_lines(ledger, last)
    return out


def search_lines(ledger, last: str) -> list[str]:
    """X-3.5: the grammar search's line for the month -- tested, survivors, the
    deflation -- from its latest progress event, and the variables it skipped."""
    out = ["## 10. The grammar search", ""]
    r = ledger.one("SELECT after FROM loop_events WHERE kind='search_progress' AND "
                   "substr(as_of,1,10)>=? AND substr(as_of,1,10)<=? ORDER BY id DESC "
                   "LIMIT 1", (last[:7] + "-01", last)) if _has(ledger, "loop_events") \
        else None
    if not r:
        return out + ["No search step this month (a run begins in the first week of "
                      "a month, as the nightly loop's last step, once the previous run "
                      "is complete).", ""]
    s = json.loads(r["after"])
    out += [f"- {s['line']}."]
    cov = s.get("coverage") or []
    if cov:
        ok = [c.split(":")[0] for c in cov if ": joined" in c]
        out += [f"- Coverage (at least five years of point-in-time history before the "
                f"holdout): passed {', '.join(ok) or 'none'}; failed or pending "
                f"{', '.join(c.split(':')[0] for c in cov if ': joined' not in c) or 'none'}."]
        out += [f"  - {c}." for c in cov]
    out += [f"- {p}." for p in s.get("pending") or []]
    return out + [""]


# ---------------------------------------------------------------------------
# THE QUARTERLY'S LAB PAGE (X-3.7)
# ---------------------------------------------------------------------------
NO_QUARTER = "No quarter closed yet"
LADDER = (("ledger-paper", "where the lab lives now"),
          ("broker-paper", "through the order gate, after Gate 1.5"),
          ("live", "after Gate 3, not before 2027"))


def _money(x: Optional[float]) -> str:
    return "–" if x is None else f"{x:+,.0f}"


def ladder_lines(ledger, last: str) -> list[str]:
    """The gate-ladder standing: the rung, and how many engines have reached
    their minimum sample (the evidence the Gate 1.5 question waits on)."""
    eng = [e for e in ledger.engines() if e["status"] in ("live", "halved")]
    at_min = 0
    for e in eng:
        n = ledger.one("SELECT COUNT(*) AS n FROM grades WHERE engine_id=? AND day<=?",
                       (e["id"], last))["n"]
        if n >= acfg.min_signals(e["horizon"]):
            at_min += 1
    return [f"- Rung: {LADDER[0][0]}, {LADDER[0][1]}. Next: {LADDER[1][0]}, "
            f"{LADDER[1][1]}; then {LADDER[2][0]}, {LADDER[2][1]}. Each rung is the "
            f"operator's ruling, never the lab's.",
            f"- Engines in paper at their minimum sample: {at_min} of {len(eng)}."]


def quarter_page(ledger, as_of: str, quarter: Optional[str] = None, store=None,
                 engines: Optional[dict] = None) -> str:
    """The Quarterly's lab page, from alpha.db read-only (and the store, read-only,
    for the re-fit counterfactuals)."""
    from altdata import session                                 # noqa: PLC0415
    from .ledger import LAB                                     # noqa: PLC0415
    from .loops import quarterly as ql                          # noqa: PLC0415
    q = quarter or ql.last_closed(ledger, as_of)
    if not q:
        first = ledger.one("SELECT MIN(as_of) AS a FROM loop_events")["a"]
        return "\n".join([
            "# Alpha Lab, the quarter", "",
            f"{NO_QUARTER}: the lab has not yet run through a whole calendar quarter "
            f"(its first loop event: {str(first)[:10] if first else 'none'}).", "",
            "## The gate-ladder standing", "",
            *ladder_lines(ledger, session.session_date(as_of)), ""])
    first, last = ql.bounds(q)
    out = [f"# Alpha Lab, the quarter ({q[-2:]} {q[:4]})", "",
           f"From alpha.db, read-only, as of {as_of[:10]}. A machine's book in "
           f"ledger-paper: evidence for the sitting, never an instruction to it.", ""]
    # 1. the lab's quarter
    out += ["## 1. The lab's quarter", ""]
    rows = ledger.q("SELECT * FROM equity WHERE engine_id=? AND day>=? AND day<=? "
                    "ORDER BY day", (LAB, first, last))
    before = ledger.one("SELECT equity FROM equity WHERE engine_id=? AND day<? ORDER BY "
                        "day DESC LIMIT 1", (LAB, first))
    if rows:
        start = float(before["equity"]) if before else float(rows[0]["equity"])
        end = float(rows[-1]["equity"])
        worst = min(float(r["drawdown"]) for r in rows)
        out += [f"- Lab equity {start:,.0f} -> {end:,.0f} lab dollars "
                f"({_pct(end / start - 1 if start else None)} on the quarter); deepest "
                f"drawdown {worst * 100:.1f}%.", ""]
    else:
        out += ["- No equity recorded this quarter.", ""]
    # 2. the engines
    from . import book                                          # noqa: PLC0415
    out += ["## 2. The engines", "", "| Engine | Family | Status | P&L on the quarter |",
            "|---|---|---|---:|"]
    prev = (dt.date.fromisoformat(first) - dt.timedelta(days=1)).isoformat()
    for e in ledger.engines():
        pnl = book.cum_pnl(ledger, e["id"], last) - book.cum_pnl(ledger, e["id"], prev)
        out.append(f"| {e['id']} | {e['family']} | {e['status']} | {_money(pnl)} |")
    out.append("")
    # 3. the loop's contribution
    rv = ql.review(ledger, store, q, engines if engines is not None else {})
    out += ["## 3. The loop's contribution", ""]
    counted = [c for c in rv["changes"] if c.get("computable")]
    if counted:
        out += ["| When | Change | Engine | Against the counterfactual |",
                "|---|---|---|---:|"]
        for c in counted:
            out.append(f"| {c['day']} | {c['kind']} | {c['engine'] or 'all'} | "
                       f"{_money(c['contribution'])} |")
        out.append("")
    out.append(f"- Net: {_money(rv['net_contribution'])} lab dollars from "
               f"{len(counted)} change(s), each against what the lab would have "
               f"earned without it, from the same stored prices.")
    if rv["uncounted"]:
        out.append(f"- Not computable, not counted: {len(rv['uncounted'])}.")
    adj = ledger.q("SELECT after FROM loop_events WHERE kind=? ORDER BY id",
                   (ql.KIND,))
    mine = [json.loads(a["after"]) for a in adj if json.loads(a["after"]).get("reviewed") == q]
    if mine:
        out.append(f"- Negative, so for {mine[-1]['applies_to']} the re-fit bounds "
                   f"were narrowed and the cadence slowed to every "
                   f"{mine[-1]['refit_every_weeks']} weeks (a loop event of its own).")
    elif rv["net_contribution"] < 0:
        out.append("- Negative: the weekly loop narrows the bounds and slows the "
                   "cadence at its next run.")
    else:
        out.append("- Not negative: nothing changes.")
    out.append("")
    # 4. the failures register
    out += ["## 4. The failures register", ""]
    t0, t1 = f"{first}T00:00:00", f"{last}T23:59:59.999999"
    failed = ledger.q("SELECT * FROM hypotheses WHERE status='failed' AND written_at>=? "
                      "AND written_at<=? ORDER BY id", (t0, t1))
    total = ledger.one("SELECT COUNT(*) AS n FROM hypotheses WHERE status='failed' AND "
                       "written_at<=?", (t1,))["n"]
    out.append(f"- {len(failed)} failed this quarter; {total} on the register in all.")
    if failed:
        out += ["", "| Id | Title | Family | Why it failed |", "|---|---|---|---|"]
        for h in failed:
            out.append(f"| {h['id']} | {h['title']} | {h['family']} | "
                       f"{(h['status_reason'] or '').replace('|', '/')} |")
    out.append("")
    # 5. the gate ladder
    out += ["## 5. The gate-ladder standing", "", *ladder_lines(ledger, last), ""]
    return "\n".join(out)


def page_prose_words(md: str) -> int:
    """The page's prose: every line that is not a heading or a table row."""
    return sum(len(ln.split()) for ln in md.splitlines()
               if ln.strip() and not ln.startswith(("#", "|")))


def quarterly_attachment(stamp: str, path: Optional[str | Path] = None
                         ) -> Optional[tuple[str, str, str]]:
    """(filename, markdown, "markdown") for the Quarterly's email, or None. Never
    raises: the Quarterly is never the lab's casualty."""
    try:
        p = Path(path or acfg.ledger_path())
        if not p.is_file():
            return None
        from altdata import session                             # noqa: PLC0415
        from .ledger import Ledger                              # noqa: PLC0415
        from .loops.weekly import _loaded                       # noqa: PLC0415
        from .store import ReadOnlyStore                        # noqa: PLC0415
        lg = Ledger(p, read_only=True)
        try:
            st = None
            try:
                st = ReadOnlyStore()
            except Exception:                                   # noqa: BLE001
                pass
            md = quarter_page(lg, session.utc_iso(), store=st, engines=_loaded(lg))
            if st is not None:
                st.close()
            return (f"alpha_lab_quarter_{str(stamp)[:10]}.md", md, "markdown")
        finally:
            lg.close()
    except Exception:                                         # noqa: BLE001
        return None


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
