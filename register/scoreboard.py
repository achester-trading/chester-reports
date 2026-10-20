"""
The Card's scoreboard -- measurement only (b48-scoreboard; ruled 19 Oct 2026, the
four decisions sent at 23:35 ET: "accept all"). Rows 5, 12 and 13 of the Master
Guide's Table 8; Doctrine #2 (7-8 Nov) may still amend how they are used.

    from register import scoreboard
    scoreboard.expectancy_13w(as_of)     # the score, by book and by regime
    scoreboard.benchmarks_4q(as_of)      # the active books against A alone and a 60/40
    scoreboard.weekly_top(as_of)         # heat, net exposure, the score, rule breaks

    python -m register.scoreboard show [--as-of ISO] [--db PATH]

-----------------------------------------------------------------------------
WHAT THE DOCTRINE ASKS, AND WHAT THIS READS FOR EACH
-----------------------------------------------------------------------------
"The score is rolling thirteen-week expectancy by book and by regime, and the
count of rules broken, which should be zero. The active books (B, C, D) are
benchmarked, over four quarters, against Book A alone and against a static
60/40" (the Card; Doctrine Rule 22). Section 6.5 puts heat, net exposure, the
thirteen-week expectancy and the rule-break count "at the top of the weekly
reflection report, above anything about the market".

    the score       the grader's rows (altdata/grader.py), RULED R -- the unit the
                    register grades in -- for graded paper decisions the operator
                    took, graded inside the thirteen weeks to the as-of. The book
                    is the decision's own `book` column; the regime is the stamp
                    the order gate stored at entry (`gate_detail.regime.regime`),
                    never recomputed (the one-regime rule).
    heat, net beta  register/heat.view() over the open decisions: the register's
                    own heat calculator, with its stored betas. Not a second one.
    rule breaks     the register's `rule_breaks` table, by session.
    the benchmarks  realised P&L of closed decisions (register/pnl.realised(),
                    from the decision's fields and the executions table) as a
                    share of the declared capital, against Book Z's stored 60/40
                    marks over the same window. Percentages only, never dollars.

Reads only. Every database is opened `mode=ro`; nothing here writes the register,
the grades, the trade ledgers or the store, computes a regime, or enters a
composite or the market-state object. What cannot be computed prints "not built"
with its reason.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "config" / "scoreboard.yaml"
ACTIVE_BOOKS = ("B", "C", "D")
NO_STAMP = "(no regime stamp at entry)"
NOT_STAMPED = "not stamped"
ABSENT_AT_ENTRY = "(dial absent at entry)"
# The two dials the order gate stamps at entry from B49 (20 Oct 2026), by the key
# in gate_detail.regime. The volatile-day flag joins once a50-dealer-store is on
# main.
DIALS = (("vol", "vol_state"), ("gamma", "gamma_state"))
NO_BOOK = "(no book recorded)"


def load_config(path: Optional[Path] = None) -> dict:
    import yaml  # noqa: PLC0415
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _ro(path: Optional[str]) -> Optional[sqlite3.Connection]:
    """The database read-only, or None when it does not exist (never created)."""
    from altdata import observations  # noqa: PLC0415
    p = Path(path or observations.DEFAULT_DB)
    if not p.exists():
        return None
    conn = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _has(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (table,)).fetchone() is not None


def _day(ts: Any) -> str:
    return str(ts or "")[:10]


def _window(as_of: str, days: int) -> tuple[str, str]:
    end = dt.date.fromisoformat(as_of[:10])
    return (end - dt.timedelta(days=days)).isoformat(), end.isoformat()


def _plural(n: int, word: str) -> str:
    """'1 open decision', '3 open decisions' -- the reports print no '(s)'."""
    return f"{n} {word}" + ("" if n == 1 else "s")


def _date(iso: str) -> str:
    """'2026-10-01' -> '1 Oct 2026': a printed line carries no ISO date."""
    d = dt.date.fromisoformat(str(iso)[:10])
    return f"{d.day} {d:%b} {d.year}"


def _now() -> str:
    from altdata import session  # noqa: PLC0415
    return session.utc_iso()


# ---------------------------------------------------------------------------
# The regime stamp, as the order gate stored it at entry
# ---------------------------------------------------------------------------
def regime_stamp(decision: dict) -> str:
    """The Doctrine regime the decision was taken under, read from the stored
    gate detail. Never recomputed: a decision is judged under the regime it was
    decided in, and recomputing would let a later object restate it."""
    raw = decision.get("gate_detail")
    if not raw:
        return NO_STAMP
    try:
        gd = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (ValueError, TypeError):
        return NO_STAMP
    reg = (gd.get("regime") or {}).get("regime")
    return str(reg) if reg else NO_STAMP


def _gate_regime(decision: dict) -> Optional[dict]:
    raw = decision.get("gate_detail")
    if not raw:
        return None
    try:
        gd = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (ValueError, TypeError):
        return None
    return gd.get("regime") or {}


def dial_stamp(decision: dict, key: str) -> str:
    """One dial's state as stamped at entry. A decision entered before the stamp
    existed carries no such key and prints "not stamped"; one stamped while the
    dial was absent says so. Never read from today's object."""
    reg = _gate_regime(decision)
    if reg is None or key not in reg:
        return NOT_STAMPED
    return str(reg[key]) if reg[key] else ABSENT_AT_ENTRY


# ---------------------------------------------------------------------------
# The score: rolling thirteen-week expectancy, by book and by regime
# ---------------------------------------------------------------------------
def _taken(grade: dict) -> bool:
    return str(grade.get("operator_action") or "").upper() in ("TAKE", "MODIFY")


def _latest_per_decision(grades: list[dict]) -> list[dict]:
    """One grade per decision: its latest. A re-grade is a new row (the grades
    are immutable), and counting both would weigh one decision twice."""
    by: dict[str, dict] = {}
    for g in grades:
        k = str(g.get("decision_id"))
        if k not in by or str(g.get("graded_at")) > str(by[k].get("graded_at")):
            by[k] = g
    return list(by.values())


def _cell(values: list[float], min_n: int) -> dict:
    sys.path.insert(0, str(REPO / "tools"))
    import cuts  # noqa: PLC0415
    iv = cuts.interval(values)
    iv["accruing"] = iv["n"] < min_n
    return iv


def cell_text(iv: dict, min_n: int) -> str:
    """n and the interval first, then the point (Evidence and Inference, ch. 1)."""
    if iv["n"] < min_n:
        return f"accruing (n={iv['n']})"
    if iv.get("lo") is None:
        return f"n={iv['n']}, no interval, mean {iv['mean']:+.2f}R"
    return (f"n={iv['n']}, {iv['lo']:+.2f} to {iv['hi']:+.2f}R, "
            f"mean {iv['mean']:+.2f}R")


def expectancy_13w(as_of: Optional[str] = None, db_path: Optional[str] = None,
                   cfg: Optional[dict] = None) -> dict:
    """The score. ONE function: the Weekly's top and the Monthly's register month
    both read it, so the two cannot print different figures."""
    cfg = cfg or load_config()
    sc = cfg.get("score") or {}
    weeks, min_n = int(sc.get("weeks", 13)), int(sc.get("min_n", 10))
    as_of = as_of or _now()
    start, end = _window(as_of, 7 * weeks)
    out: dict[str, Any] = {"window": [start, end], "weeks": weeks, "min_n": min_n,
                           "unit": "R (ruled)", "overall": None, "by_book": {},
                           "by_regime": {}, "by_book_regime": {},
                           **{f"by_{d}": {} for d, _ in DIALS}}
    conn = _ro(db_path)
    if conn is None or not _has(conn, "grades") or not _has(conn, "decisions"):
        out["not_built"] = "no grades table on the store yet"
        return out
    try:
        from altdata import grader  # noqa: PLC0415
        grades = [dict(r) for r in conn.execute(
            "SELECT * FROM grades WHERE method_version = ? AND substr(graded_at,1,10) > ? "
            "AND substr(graded_at,1,10) <= ? AND graded_at <= ?",
            (grader.METHOD_VERSION, start, end, as_of))]
        decs = {str(r["id"]): dict(r) for r in conn.execute(
            "SELECT id, book, gate_detail FROM decisions")}
    finally:
        conn.close()
    rows = []
    for g in _latest_per_decision([g for g in grades if _taken(g)]):
        r = g.get("r_multiple_ruled")
        if not isinstance(r, (int, float)):
            continue
        d = decs.get(str(g.get("decision_id"))) or {}
        rows.append({"r": float(r), "book": d.get("book") or NO_BOOK,
                     "regime": regime_stamp(d),
                     **{dial: dial_stamp(d, key) for dial, key in DIALS}})
    out["overall"] = _cell([x["r"] for x in rows], min_n)
    for key, field in (("by_book", "book"), ("by_regime", "regime"),
                       *((f"by_{d}", d) for d, _ in DIALS)):
        groups: dict[str, list[float]] = {}
        for x in rows:
            groups.setdefault(x[field], []).append(x["r"])
        out[key] = {k: _cell(v, min_n) for k, v in sorted(groups.items())}
    pairs: dict[str, list[float]] = {}
    for x in rows:
        pairs.setdefault(f"{x['book']} | {x['regime']}", []).append(x["r"])
    out["by_book_regime"] = {k: _cell(v, min_n) for k, v in sorted(pairs.items())}
    return out


def dial_line(e: dict, dial: str) -> str:
    """The cut by one stamped dial, for the Monthly's register month."""
    name = {"vol": "volatility", "gamma": "gamma"}[dial]
    cells = e.get(f"by_{dial}") or {}
    return (f"By the {name} dial at entry: "
            + ("; ".join(f"{k}: {cell_text(v, e['min_n'])}" for k, v in cells.items())
               or "none graded") + ".")


def expectancy_line(e: dict) -> str:
    if e.get("not_built"):
        return f"Thirteen-week expectancy: not built ({e['not_built']})."
    m = e["min_n"]
    books = "; ".join(f"Book {k}: {cell_text(v, m)}" if k != NO_BOOK
                      else f"{k}: {cell_text(v, m)}"
                      for k, v in e["by_book"].items()) or "no book graded"
    return (f"Thirteen-week expectancy ({_date(e['window'][0])} to "
            f"{_date(e['window'][1])}, "
            f"ruled R, interval first): all books {cell_text(e['overall'], m)}; "
            f"{books}.")


# ---------------------------------------------------------------------------
# The benchmarks over four quarters
# ---------------------------------------------------------------------------
def _book_return(decisions: list[dict], book_set: tuple, start: str, end: str,
                 capital: float, store: Any) -> dict:
    """Realised P&L of the books' decisions closed in the window, as a share of
    capital; or not built, naming what is missing. A decision open in the window
    has no mark the register can make, so the book's figure is withheld rather
    than printed on its closed decisions alone."""
    from register import pnl  # noqa: PLC0415
    mine = [d for d in decisions if d.get("book") in book_set
            and str(d.get("operator_action") or "").upper() in ("TAKE", "MODIFY")
            and not d.get("superseded_by")]
    if not mine:
        return {"pct": None, "n": 0,
                "not_built": f"no taken decision in Book {'/'.join(book_set)} "
                             f"on the register"}
    open_ = [d for d in mine if d.get("status") == "active"]
    if open_:
        return {"pct": None, "n": len(mine),
                "not_built": (f"{_plural(len(open_), 'open decision')} held, and "
                              f"the register stores no entry fill per decision, so "
                              f"an open position cannot be marked from it")}
    closed = [d for d in mine if d.get("status") == "closed"
              and start < _day(d.get("exit_time") or d.get("outcome_at")
                               or d.get("decision_time")) <= end]
    total, missing = 0.0, []
    for d in closed:
        r = pnl.realised(d, store)
        if r.get("pnl_usd") is None:
            missing.append(f"{d.get('id')}: {r.get('missing') or 'no P&L'}")
            continue
        total += float(r["pnl_usd"])
    if missing:
        return {"pct": None, "n": len(closed),
                "not_built": "realised P&L missing for " + "; ".join(missing[:3])}
    return {"pct": round(100.0 * total / capital, 2) if capital else None,
            "n": len(closed)}


def benchmarks_4q(as_of: Optional[str] = None, db_path: Optional[str] = None,
                  cfg: Optional[dict] = None) -> dict:
    cfg = cfg or load_config()
    days = int((cfg.get("benchmarks") or {}).get("window_days", 365))
    as_of = as_of or _now()
    start, end = _window(as_of, days)
    out: dict[str, Any] = {"window": [start, end], "active": None, "book_a": None,
                           "sixty_forty": None}
    from register import heat  # noqa: PLC0415
    capital = float((heat.load_limits().get("capital_usd") or {}).get("value") or 0)
    conn = _ro(db_path)
    decisions = []
    if conn is not None and _has(conn, "decisions"):
        try:
            decisions = [dict(r) for r in conn.execute("SELECT * FROM decisions")]
        finally:
            conn.close()
    from altdata import benchmark, observations  # noqa: PLC0415
    with observations.ObservationStore(db_path) as st:
        out["active"] = _book_return(decisions, ACTIVE_BOOKS, start, end, capital, st)
        out["book_a"] = _book_return(decisions, ("A",), start, end, capital, st)
        m1 = (benchmark.latest(as_of, st) or {}).get("sixty_forty")
        if not m1:
            out["sixty_forty"] = {"pct": None, "not_built": "no Book Z mark is stored"}
        else:
            s0 = max(start, str(m1.get("start") or start))
            m0 = benchmark._mark_on_or_before(st, "sixty_forty", s0, as_of)
            if not m0:
                m0 = {"value": 100.0, "session": m1.get("start")}
            out["sixty_forty"] = {
                "pct": round(100.0 * (m1["value"] / m0["value"] - 1.0), 2),
                "from": m0.get("session") or s0, "through": m1.get("session")}
    return out


def benchmarks_line(b: dict) -> str:
    def f(x: dict, name: str) -> str:
        if not x or x.get("pct") is None:
            return f"{name} not built ({(x or {}).get('not_built') or 'no figure'})"
        return f"{name} {x['pct']:+.2f}%"
    six = b.get("sixty_forty") or {}
    span = (f", Book Z marked {_date(six['from'])} to {_date(six['through'])}"
            if six.get("pct") is not None and six.get("from") and six.get("through")
            else "")
    return (f"Four quarters ({_date(b['window'][0])} to {_date(b['window'][1])}{span}), "
            f"as a share "
            f"of capital: {f(b['active'], 'the active books (B, C, D)')}; "
            f"{f(b['book_a'], 'Book A alone')}; {f(six, 'the static 60/40')}.")


# ---------------------------------------------------------------------------
# The Weekly's top
# ---------------------------------------------------------------------------
def rule_breaks(as_of: str, week_start: str, db_path: Optional[str] = None) -> dict:
    conn = _ro(db_path)
    if conn is None or not _has(conn, "rule_breaks"):
        return {"week": None, "total": None,
                "not_built": "no rule_breaks table on the register yet"}
    try:
        week = conn.execute("SELECT COUNT(*) FROM rule_breaks WHERE session > ? AND "
                            "session <= ?", (week_start, as_of[:10])).fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM rule_breaks WHERE session <= ?",
                             (as_of[:10],)).fetchone()[0]
    finally:
        conn.close()
    return {"week": int(week), "total": int(total)}


def weekly_top(as_of: Optional[str] = None, db_path: Optional[str] = None,
               cfg: Optional[dict] = None) -> dict:
    """Heat, net exposure, the thirteen-week expectancy and the rule-break count:
    the four figures 6.5 puts above anything about the market."""
    cfg = cfg or load_config()
    as_of = as_of or _now()
    week_start = _window(as_of, 7)[0]
    out: dict[str, Any] = {"as_of": as_of}
    conn = _ro(db_path)
    open_ = []
    if conn is not None and _has(conn, "decisions"):
        try:
            open_ = [dict(r) for r in conn.execute(
                "SELECT * FROM decisions WHERE status = 'active' AND superseded_by "
                "IS NULL ORDER BY created_at")]
        finally:
            conn.close()
    from altdata import observations  # noqa: PLC0415
    from register import heat  # noqa: PLC0415
    try:
        with observations.ObservationStore(db_path) as st:
            v = heat.view(open_, st, as_of=as_of)
        lim = heat.load_limits()
        hcap = ((lim.get("limits") or {}).get("heat_max_pct") or {}).get("value")
        out["heat"] = {"pct": v.get("heat_pct"), "cap_pct": hcap, "open": len(open_),
                       "missing": v.get("missing") or []}
        out["net_exposure"] = {"pct": v.get("net_beta_pct"),
                               "cap_pct": (v.get("regime") or {}).get("cap_pct"),
                               "regime": (v.get("regime") or {}).get("regime"),
                               "missing": v.get("missing") or []}
    except Exception as exc:                                    # noqa: BLE001
        why = f"the heat view faulted ({type(exc).__name__}: {exc})"
        out["heat"] = {"pct": None, "not_built": why}
        out["net_exposure"] = {"pct": None, "not_built": why}
    out["expectancy"] = expectancy_13w(as_of, db_path, cfg)
    out["rule_breaks"] = rule_breaks(as_of, week_start, db_path)
    out["lines"] = top_lines(out)
    return out


def _pct_line(name: str, x: dict, what: str) -> str:
    if x.get("pct") is None:
        return f"{name}: not built ({x.get('not_built') or 'no figure'})."
    cap = (f" (cap {x['cap_pct']:g}%)" if isinstance(x.get("cap_pct"), (int, float))
           else "")
    gap = (f"; inputs missing: {'; '.join(x['missing'][:3])}"
           if x.get("missing") else "")
    return f"{name}: {x['pct']:.2f}% of capital{cap}, {what}{gap}."


def top_lines(t: dict) -> list[str]:
    h, n, rb = t["heat"], t["net_exposure"], t["rule_breaks"]
    lines = [
        _pct_line("Heat", h, f"open risk to invalidation across Books B, C and D "
                             f"({_plural(h.get('open', 0), 'open decision')})"),
        _pct_line("Net exposure", n, "Book A's net beta plus the beta-equivalent of "
                                     "Books B, C and D, from stored betas"
                  + (f", {n['regime']} band" if n.get("regime") else "")),
        expectancy_line(t["expectancy"]),
        (f"Rule breaks: not built ({rb['not_built']})." if rb.get("not_built") else
         f"Rule breaks: {rb['week']} this week; {rb['total']} on the register to "
         f"date (the Doctrine's target is zero)."),
    ]
    return lines


def _main(argv: list[str]) -> int:
    import argparse  # noqa: PLC0415
    ap = argparse.ArgumentParser(prog="python -m register.scoreboard")
    ap.add_argument("cmd", choices=("show",))
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--db", default=None)
    a = ap.parse_args(argv)
    t = weekly_top(a.as_of, a.db)
    for ln in t["lines"]:
        print(ln)
    print(benchmarks_line(benchmarks_4q(a.as_of, a.db)))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
