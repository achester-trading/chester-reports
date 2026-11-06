"""
Decision quality -- is the system getting better? (Learning Loop v2, LL-1; B73.)

    python -m altdata.decision_quality line   [--as-of ISO] [--db PATH]
    python -m altdata.decision_quality tables [--as-of ISO] [--db PATH]
    python -m altdata.decision_quality pack   [--as-of ISO] [--db PATH]

The brief's section 2.1 (docs/briefs/learning-loop-v2-brief-2026-10-25.md,
decision 1, ruled 25 Oct 2026). Three things, every one a pure function of the
stored rows, computed at read, never stored and never written by a model (R-4):

  1. MURPHY'S DECOMPOSITION of the Brier score over the probability ledger's
     resolved rows, by source family and horizon bucket. The ledger's own
     docstring names it as owed ("Brier conflates calibration with resolution");
     this is the payment. Ten bins of width 0.1 on the stated probability:

         BS  = (1/N) sum_i (p_i - o_i)^2
         REL = (1/N) sum_k n_k (fbar_k - obar_k)^2      reliability, lower is better
         RES = (1/N) sum_k n_k (obar_k - obar)^2        resolution, higher is better
         UNC = obar (1 - obar)                          uncertainty, the sample's own
         BS  = REL - RES + UNC + W

     W is the within-bin term (the forecasts' spread inside a bin, and its
     covariance with the outcomes). It is zero when every forecast in a bin is
     equal, and it is printed rather than hidden, so the three terms always add
     up to the printed Brier. Below 100 resolved rows a cell prints
     "accruing (n=k of 100)" and no figure: ten bins of ten is the least that
     says anything about reliability.

  2. THE COUNTERFACTUAL LEDGER, per book, from the stored grades (altdata/
     grader.py), one grade per decision (its latest):
       taken     the operator's TAKE or MODIFY (register/scoreboard._taken);
       declined  the operator's DECLINE, or a declined status -- the filter;
       draft     a draft never acted on -- the cost of abstention;
     each with n, the mean ruled R and the mean return in the decision's own
     direction. And THE STACK'S IMPLIED STANCE against Book Z: every resolved
     Weekly stance row (source weekly_stance, daily_cascade/precis.py) read as
     long SPY above 0.5 and cash below it, its week's return from Book Z's own
     marks (paper.benchmark), beside the cash, SPY and 60/40 ledgers over the
     same weeks.

  3. THE ONE LINE: the system Brier with its decomposition, and the system
     expectancy in ruled R, each over the last 13 and 52 weeks against the
     window of the same length before it, each with its n.

Report only. Nothing here enters a composite, a dial, a band, a packet or the
market-state object (metrics_registry.yaml market_state_barred), and nothing
reads it but the Monthly's Lab report hook and the Doctrine pack's command.
Dry-run sources (the "dryrun." namespace) are never counted.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parent.parent

FLOOR = 100            # resolved rows a cell before a decomposition prints
BINS = 10              # ten bins of width 0.1
DRY = "dryrun."
STANCE_SOURCE = "weekly_stance"
# Horizon buckets, in calendar days from emission to the horizon date. Declared,
# not fitted: a week, a month, a quarter, longer.
BUCKETS = (("1-7d", 7), ("8-31d", 31), ("32-92d", 92), (">92d", None))
WINDOWS = (13, 52)     # weeks, for the trend
METHOD = "decision-quality-v1"


# ---------------------------------------------------------------------------
# Reading the stored rows (read-only; a missing database is "nothing stored")
# ---------------------------------------------------------------------------
def _ro(db: Optional[str]) -> Optional[sqlite3.Connection]:
    from . import observations                                  # noqa: PLC0415
    p = Path(db or observations.DEFAULT_DB)
    if not p.exists():
        return None
    conn = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _has(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (table,)).fetchone() is not None


def _now() -> str:
    from . import session                                       # noqa: PLC0415
    return session.utc_iso()


def resolved_rows(as_of: str, db: Optional[str] = None) -> list[dict]:
    """The ledger's rows resolved by `as_of`, live sources only."""
    conn = _ro(db)
    if conn is None:
        return []
    try:
        if not _has(conn, "probabilities"):
            return []
        return [dict(r) for r in conn.execute(
            "SELECT * FROM probabilities WHERE outcome IS NOT NULL "
            "AND resolved_at IS NOT NULL AND resolved_at <= ? "
            "AND substr(source, 1, ?) <> ? ORDER BY resolved_at",
            (as_of, len(DRY), DRY))]
    finally:
        conn.close()


def graded(as_of: str, db: Optional[str] = None) -> list[dict]:
    """One grade per decision (its latest graded by `as_of`), joined to the
    decision's book and status."""
    conn = _ro(db)
    if conn is None:
        return []
    try:
        if not _has(conn, "grades"):
            return []
        from . import grader                                    # noqa: PLC0415
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM grades WHERE method_version = ? AND graded_at <= ?",
            (grader.METHOD_VERSION, as_of))]
        decs = ({str(r["id"]): dict(r) for r in conn.execute(
            "SELECT id, book, status, operator_action FROM decisions")}
            if _has(conn, "decisions") else {})
    finally:
        conn.close()
    from register.scoreboard import _latest_per_decision        # noqa: PLC0415
    out = []
    for g in _latest_per_decision(rows):
        d = decs.get(str(g.get("decision_id"))) or {}
        g["book"] = d.get("book")
        g["decision_status"] = d.get("status")
        out.append(g)
    return out


# ---------------------------------------------------------------------------
# 1. Murphy's decomposition
# ---------------------------------------------------------------------------
def family(source: str) -> str:
    """The source family: the source up to its first colon (alt_asset:<family>
    is one family, the thesis register's)."""
    return str(source or "").split(":", 1)[0] or "(no source)"


def bucket(emitted_at: str, horizon_date: str) -> str:
    try:
        days = (dt.date.fromisoformat(str(horizon_date)[:10])
                - dt.date.fromisoformat(str(emitted_at)[:10])).days
    except ValueError:
        return "(no horizon)"
    for name, hi in BUCKETS:
        if hi is None or days <= hi:
            return name
    return BUCKETS[-1][0]


def _bin(p: float) -> int:
    return min(int(float(p) * BINS), BINS - 1)


def murphy(pairs: list[tuple[float, int]], floor: int = FLOOR) -> dict:
    """{n, brier, rel, res, unc, within, accruing, bins} over (p, outcome) pairs.

    The terms are computed at every n (the gate checks them on a small closed-
    form fixture); a reader prints them only at the floor (cell_text)."""
    n = len(pairs)
    out: dict[str, Any] = {"n": n, "floor": floor, "accruing": n < floor,
                           "brier": None, "rel": None, "res": None, "unc": None,
                           "within": None, "bins": []}
    if not n:
        return out
    obar = sum(o for _, o in pairs) / n
    bs = sum((p - o) ** 2 for p, o in pairs) / n
    by: dict[int, list[tuple[float, int]]] = {}
    for p, o in pairs:
        by.setdefault(_bin(p), []).append((p, o))
    rel = res = 0.0
    for k in sorted(by):
        xs = by[k]
        nk = len(xs)
        fk = sum(p for p, _ in xs) / nk
        ok = sum(o for _, o in xs) / nk
        rel += nk * (fk - ok) ** 2
        res += nk * (ok - obar) ** 2
        out["bins"].append({"bin": k, "lo": k / BINS, "hi": (k + 1) / BINS,
                            "n": nk, "forecast": fk, "observed": ok})
    rel, res = rel / n, res / n
    unc = obar * (1.0 - obar)
    out.update(brier=bs, rel=rel, res=res, unc=unc, within=bs - (rel - res + unc),
               base_rate=obar)
    return out


def cell_text(c: dict) -> str:
    if c["n"] < c.get("floor", FLOOR):
        return f"accruing (n={c['n']} of {c.get('floor', FLOOR)})"
    return (f"Brier {c['brier']:.4f} = REL {c['rel']:.4f} - RES {c['res']:.4f} "
            f"+ UNC {c['unc']:.4f} + W {c['within']:+.4f} (n={c['n']})")


def decomposition(rows: list[dict], floor: int = FLOOR) -> dict:
    """{(family, bucket): murphy cell} and the system cell over every row."""
    cells: dict[tuple[str, str], list[tuple[float, int]]] = {}
    for r in rows:
        k = (family(r["source"]), bucket(r["emitted_at"], r["horizon_date"]))
        cells.setdefault(k, []).append((float(r["probability"]), int(r["outcome"])))
    return {"cells": {k: murphy(v, floor) for k, v in sorted(cells.items())},
            "system": murphy([(float(r["probability"]), int(r["outcome"]))
                              for r in rows], floor)}


# ---------------------------------------------------------------------------
# 2. The counterfactual ledger
# ---------------------------------------------------------------------------
def cls(g: dict) -> Optional[str]:
    """taken, declined or draft -- the three the brief names; None otherwise."""
    from register.scoreboard import _taken                      # noqa: PLC0415
    if _taken(g):
        return "taken"
    act = str(g.get("operator_action") or "").upper()
    st = str(g.get("decision_status") or g.get("status") or "").lower()
    if act == "DECLINE" or st == "declined":
        return "declined"
    if st == "draft":
        return "draft"
    return None


def _mean(xs: list[float]) -> Optional[float]:
    return sum(xs) / len(xs) if xs else None


def counterfactual(grades: list[dict], min_n: int) -> dict:
    """book -> class -> {n, n_r, mean_r, mean_return_pct, accruing}."""
    by: dict[str, dict[str, list[dict]]] = {}
    for g in grades:
        c = cls(g)
        if c is None:
            continue
        by.setdefault(g.get("book") or "(no book recorded)", {}) \
          .setdefault(c, []).append(g)
    out: dict[str, dict] = {}
    for book in sorted(by):
        out[book] = {}
        for c in ("taken", "declined", "draft"):
            xs = by[book].get(c, [])
            rs = [float(g["r_multiple_ruled"]) for g in xs
                  if isinstance(g.get("r_multiple_ruled"), (int, float))]
            ps = [float(g["return_pct"]) for g in xs
                  if isinstance(g.get("return_pct"), (int, float))]
            out[book][c] = {"n": len(xs), "n_r": len(rs), "mean_r": _mean(rs),
                            "mean_return_pct": _mean(ps),
                            "accruing": len(xs) < min_n}
    return out


def _cf_text(c: dict, min_n: int) -> str:
    if c["n"] < min_n:
        return f"accruing (n={c['n']})"
    r = "no R" if c["mean_r"] is None else f"{c['mean_r']:+.2f}R (n={c['n_r']})"
    p = ("" if c["mean_return_pct"] is None
         else f", {c['mean_return_pct']:+.2f}% a decision")
    return f"n={c['n']}, {r}{p}"


def book_z_marks(as_of: str, db: Optional[str] = None
                 ) -> Optional[dict[str, list[tuple[str, float]]]]:
    """ledger -> [(session, value)] of Book Z's marks knowable at `as_of`, by
    the store's own as-of join, over a read-only connection (opening the store
    writable would switch its journal and write beside it). None: no store."""
    from . import benchmark, observations                       # noqa: PLC0415
    conn = _ro(db)
    if conn is None:
        return None
    try:
        if not _has(conn, "observations"):
            return {}
        cutoff = observations.canonical_instant(as_of)
        out: dict[str, list[tuple[str, float]]] = {}
        for ld in benchmark.LEDGERS:
            rows = observations.prefer_tier([dict(r) for r in conn.execute(
                observations.AS_OF_SQL, {"key": benchmark.KEY, "instrument": ld,
                                         "as_of": cutoff})], benchmark.KEY)
            vals = []
            for r in rows:
                try:
                    vals.append((str(r["observed_at"])[:10],
                                 float(json.loads(r["value_text"])["value"])))
                except (TypeError, ValueError, KeyError):
                    continue
            out[ld] = sorted(vals)
        return out
    finally:
        conn.close()


def stance_vs_book_z(rows: list[dict], as_of: str, db: Optional[str] = None,
                     marks=None) -> dict:
    """The stack's implied stance (the Weekly's resolved stance rows) against
    Book Z's three ledgers over the same weeks.

    `marks(ledger, day)` returns the ledger's value on or before `day` knowable
    at `as_of`; by default it reads paper.benchmark from the store."""
    if marks is None:
        series = book_z_marks(as_of, db)
        if series is None:
            return {"n": 0, "absent_reason": "no store"}

        def marks(ledger: str, day: str) -> Optional[float]:
            best = None
            for d, v in series.get(ledger, []):
                if d <= day:
                    best = v
            return best

    weeks, missing = [], 0
    for r in rows:
        if r["source"] != STANCE_SOURCE or float(r["probability"]) == 0.5:
            continue
        d0, d1 = str(r["emitted_at"])[:10], str(r["horizon_date"])[:10]
        rets = {}
        for ld in ("cash", "spy", "sixty_forty"):
            a, b = marks(ld, d0), marks(ld, d1)
            rets[ld] = (100.0 * (b / a - 1.0)) if a and b else None
        if None in rets.values():
            missing += 1
            continue
        long_ = float(r["probability"]) > 0.5
        weeks.append({"week": d0, "stance": "long SPY" if long_ else "cash",
                      "stance_pct": rets["spy"] if long_ else rets["cash"],
                      **{f"{k}_pct": v for k, v in rets.items()}})
    out: dict[str, Any] = {"n": len(weeks), "unmarked": missing, "weeks": weeks}
    for k in ("stance", "cash", "spy", "sixty_forty"):
        out[f"{k}_mean_pct"] = _mean([w[f"{k}_pct"] for w in weeks])
    return out


# ---------------------------------------------------------------------------
# 3. The one line, and the trend windows
# ---------------------------------------------------------------------------
def window(as_of: str, weeks: int, back: int = 0) -> tuple[str, str]:
    """(start, end] as dates: `weeks` weeks ending `back` windows before as_of."""
    end = dt.date.fromisoformat(as_of[:10]) - dt.timedelta(days=7 * weeks * back)
    return (end - dt.timedelta(days=7 * weeks)).isoformat(), end.isoformat()


def _in(ts: Any, w: tuple[str, str]) -> bool:
    d = str(ts or "")[:10]
    return w[0] < d <= w[1]


def trend(rows: list[dict], grades: list[dict], as_of: str, min_n: int,
          floor: int = FLOOR) -> dict:
    out: dict[str, Any] = {}
    taken = [g for g in grades if cls(g) == "taken"
             and isinstance(g.get("r_multiple_ruled"), (int, float))]
    for w in WINDOWS:
        for back, tag in ((0, "now"), (1, "before")):
            win = window(as_of, w, back)
            pr = [(float(r["probability"]), int(r["outcome"])) for r in rows
                  if _in(r["resolved_at"], win)]
            rs = [float(g["r_multiple_ruled"]) for g in taken
                  if _in(g["graded_at"], win)]
            out[f"{w}w_{tag}"] = {"window": win, "brier": murphy(pr, floor),
                                  "r": {"n": len(rs), "mean": _mean(rs),
                                        "accruing": len(rs) < min_n}}
    return out


def _b(c: dict) -> str:
    if c["n"] < c["floor"]:
        return f"accruing (n={c['n']} of {c['floor']})"
    return (f"{c['brier']:.4f} (REL {c['rel']:.4f}, RES {c['res']:.4f}, "
            f"UNC {c['unc']:.4f}; n={c['n']})")


def _r(c: dict, min_n: int) -> str:
    if c["n"] < min_n:
        return f"accruing (n={c['n']} of {min_n})"
    return f"{c['mean']:+.2f}R (n={c['n']})"


def _min_n() -> int:
    try:
        from register import scoreboard                         # noqa: PLC0415
        return int((scoreboard.load_config().get("score") or {}).get("min_n", 10))
    except Exception:                                         # noqa: BLE001
        return 10


def build(as_of: Optional[str] = None, db: Optional[str] = None,
          floor: int = FLOOR, min_n: Optional[int] = None, marks=None) -> dict:
    """Everything, as of an instant. Pure over the stored rows."""
    as_of = as_of or _now()
    min_n = _min_n() if min_n is None else min_n
    rows = resolved_rows(as_of, db)
    grades = graded(as_of, db)
    return {"as_of": as_of, "method": METHOD, "floor": floor, "min_n": min_n,
            "rows": len(rows), "grades": len(grades),
            "decomposition": decomposition(rows, floor),
            "counterfactual": counterfactual(grades, min_n),
            "stance": stance_vs_book_z(rows, as_of, db, marks),
            "trend": trend(rows, grades, as_of, min_n, floor)}


def line(b: dict) -> str:
    t, m = b["trend"], b["min_n"]
    parts = []
    for w in WINDOWS:
        parts.append(f"system Brier, last {w} weeks {_b(t[f'{w}w_now']['brier'])}"
                     f" against {_b(t[f'{w}w_before']['brier'])} the {w} before")
    for w in WINDOWS:
        parts.append(f"expectancy (ruled R, taken), last {w} weeks "
                     f"{_r(t[f'{w}w_now']['r'], m)} against "
                     f"{_r(t[f'{w}w_before']['r'], m)} the {w} before")
    return (f"Is it getting better (as of {b['as_of'][:10]}; computed from the "
            f"stored grades, never written by a model): " + "; ".join(parts) + ".")


def tables_md(b: dict) -> list[str]:
    m = b["min_n"]
    out = ["### The Brier decomposition, by source family and horizon", "",
           f"Resolved ledger rows: {b['rows']}. A cell prints below "
           f"{b['floor']} resolved rows as accruing. REL is reliability (lower is "
           f"better), RES resolution (higher is better), UNC the sample's own "
           f"uncertainty; W the within-bin term, so the four add to the Brier.", "",
           "| Family | Horizon | n | Decomposition |", "|---|---|---:|---|"]
    cells = b["decomposition"]["cells"]
    if not cells:
        out.append("| (none) | | 0 | no resolved row is stored |")
    for (fam, hb), c in cells.items():
        out.append(f"| {fam} | {hb} | {c['n']} | {cell_text(c)} |")
    s = b["decomposition"]["system"]
    out += [f"| all | all | {s['n']} | {cell_text(s)} |", "",
            "### The counterfactual ledger, by book", "",
            f"One grade per decision, its latest. A cell prints below {m} graded "
            f"decisions as accruing. Declined is the operator's filter; draft is "
            f"the cost of abstention.", "",
            "| Book | Taken | Declined | Draft |", "|---|---|---|---|"]
    cf = b["counterfactual"]
    if not cf:
        out.append("| (none) | no graded decision is stored | | |")
    for book, cs in cf.items():
        out.append(f"| {book} | " + " | ".join(_cf_text(cs[c], m) for c in
                                               ("taken", "declined", "draft")) + " |")
    st = b["stance"]
    out += ["", "### The stack's implied stance against Book Z", ""]
    if not st.get("n"):
        why = st.get("absent_reason") or (
            f"no resolved Weekly stance row with Book Z marks at both ends"
            + (f" ({st['unmarked']} unmarked)" if st.get("unmarked") else ""))
        out.append(f"Not built: {why}.")
    else:
        def p(x: Optional[float]) -> str:
            return "–" if x is None else f"{x:+.2f}%"
        out += ["| Weeks | The stance | Cash | SPY | 60/40 |", "|---:|---:|---:|---:|---:|",
                f"| {st['n']} | {p(st['stance_mean_pct'])} | {p(st['cash_mean_pct'])} | "
                f"{p(st['spy_mean_pct'])} | {p(st['sixty_forty_mean_pct'])} |", "",
                "Mean weekly return; the stance is long SPY above 0.5 and cash "
                "below it, read from Book Z's own marks."]
    return out + [""]


def lab_section(as_of: Optional[str] = None, db: Optional[str] = None) -> str:
    """The Monthly's Lab report section: the line and the tables."""
    b = build(as_of, db)
    return "\n".join(["## Decision quality (Learning Loop v2, LL-1)", "",
                      f"**{line(b)}**", ""] + tables_md(b))


def with_lab_report(lab: Optional[tuple[str, str, str]], stamp: str,
                    db: Optional[str] = None) -> Optional[tuple[str, str, str]]:
    """The Monthly's hook: the Lab report attachment with this section appended.
    With no Lab report there is nothing to append to, and the edition gains no
    attachment of its own: B73 Part 2 prints the section IN the Lab report, and a
    third attachment broke the Monthly's two-attachment edition (B80). Never
    raises: the Monthly is never this section's casualty."""
    if not lab:
        return lab
    try:
        sec = lab_section(None, db)
    except Exception:                                         # noqa: BLE001
        return lab
    name, md, kind = lab
    return (name, md.rstrip() + "\n\n" + sec, kind)


def pack_md(as_of: Optional[str] = None, db: Optional[str] = None) -> str:
    """The Doctrine sitting pack's section, laid out as the pack's items are."""
    b = build(as_of, db)
    return "\n".join([
        "## Decision quality: is it getting better (LL-1)", "",
        f"**As built.** `altdata/decision_quality.py` ({METHOD}), as of "
        f"{b['as_of'][:10]}: computed at read from the stored ledger and grades. "
        f"Report only; no right, no rung.", "",
        f"**The line.** {line(b)}", ""] + tables_md(b))


def _main(argv: list[str]) -> int:
    import argparse                                             # noqa: PLC0415
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m altdata.decision_quality")
    ap.add_argument("what", choices=("line", "tables", "pack", "json"))
    ap.add_argument("--as-of")
    ap.add_argument("--db")
    a = ap.parse_args(argv)
    if a.what == "pack":
        print(pack_md(a.as_of, a.db))
        return 0
    b = build(a.as_of, a.db)
    if a.what == "line":
        print(line(b))
    elif a.what == "tables":
        print("\n".join(tables_md(b)))
    else:
        b["decomposition"]["cells"] = {f"{k[0]}|{k[1]}": v for k, v in
                                       b["decomposition"]["cells"].items()}
        print(json.dumps(b, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
