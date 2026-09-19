"""
The grader -- Phase 3's closing link, and the reason the register exists.

Every metric in this system is `trigger_eligible: false` and will stay that way
until something measures whether its decisions worked. That is this module. The
register has recorded decisions since the point-in-time work landed; nothing has
ever scored one.

-----------------------------------------------------------------------------
EVERY RECORD IS GRADED, INCLUDING THE ONES NOT TAKEN
-----------------------------------------------------------------------------
Taken, declined and draft alike. This is the whole methodological point and it is
the part a naive grader gets wrong by only scoring fills.

    TAKEN     the obvious case.
    DECLINED  a decision the operator passed on. Grading it is the only way to
              measure the operator's own filter: if declined decisions
              systematically outperform taken ones, the filter is inverted, and
              nothing else in the system could reveal that.
    DRAFT     recorded and never promoted -- usually DECISION_BLOCKED, which is
              the system abstaining. Grading those measures the COST OF
              ABSTENTION: a blocked decision that would have won is the price of
              the freshness gate, and that price should be known rather than
              assumed acceptable.

Evidence and Inference's shadow-outcome argument is the justification: grading
what you did not do multiplies the effective sample, and for a book making a few
decisions a week that multiple is the difference between a measurable edge and a
decade of waiting.

-----------------------------------------------------------------------------
STORED PRICES ONLY, AS-OF THE HORIZON DATE. NEVER FETCHED.
-----------------------------------------------------------------------------
A grader that fetched would be re-deciding history with today's data, which is
look-ahead in its purest form. So every price comes from data/pin_log.csv -- the
settled closes this system recorded at the time -- and the grade row stores the
observations it read, so the grade replays exactly the way a decision packet does.

WHAT THAT COSTS, STATED PLAINLY. The stored series is one settled close per
session, so:

    * the MAX ADVERSE EXCURSION is measured on CLOSES, not on intraday lows. A
      position stopped out intraday and recovered by the close is invisible here,
      so the MAE is a LOWER BOUND on the real one. Called mae_close for that
      reason rather than mae.
    * the INVALIDATION TOUCH is a settled-close test, which is what the register's
      own invalidations say ("settled close below put wall 760"). Here the stored
      data and the declared rule agree exactly, which is why this one is not a
      compromise.

-----------------------------------------------------------------------------
A HORIZON THAT HAS NOT ELAPSED GETS NO ROW
-----------------------------------------------------------------------------
Not a partial row, not a provisional grade, not a row with nulls. A half-graded
decision is the most dangerous object this module could produce: it would be
counted by every cut in cuts.py, weighted equally with a settled one, and it would
drag expectancy toward whatever the market happened to be doing on the day the
grader ran. The horizon windows are the architecture's (Part 7's table) and a
decision is graded at the FAR edge of its window, which is also its time stop --
grading at the near edge would call a thesis wrong while its window was still open.

    intraday    1 session
    swing       3 weeks     (the Doctrine's Book B time stop)
    positional  3 months
    strategic   12 months
    structural  18 months    -- "1 yr+" has no far edge; see HORIZON_SESSIONS
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import logging
import re
import sqlite3
from pathlib import Path
from typing import Any, Optional

from . import observations, session

log = logging.getLogger("altdata.grader")

REPO = Path(__file__).resolve().parent.parent

# The far edge of each window in Part 7's table (architecture, "Thirteen
# documents stay thirteen documents"), in CALENDAR DAYS. Calendar rather than
# sessions because the windows are stated in weeks and months, and converting to
# sessions would invent a precision the table does not have.
#
# `structural` is "1 yr+", which has no far edge. 18 months is a declared choice
# and not a measurement: an unbounded horizon cannot be graded at all, and a
# decision nobody ever scores is a decision that teaches nothing. Stated here so
# it is visible and arguable rather than buried in an offset.
HORIZON_DAYS = {
    "intraday": 1,
    "swing": 21,
    "positional": 92,
    "strategic": 365,
    "structural": 548,
}

# Part 7's owner column, for the cut by owning report. Kept here beside the
# windows because they come from the same table and would drift if separated.
HORIZON_OWNER = {
    "intraday": "Daily Cascade",
    "swing": "Weekend Synthesis",
    "positional": "Top & Bottom",
    "strategic": "Monthly Macro",
    "structural": "Disruptive Themes",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS grades (
    -- IMMUTABLE, and keyed so a re-grade is a NEW row rather than an edit. Part
    -- 7's rule for decisions applies with more force to their grades: a grade
    -- that can be rewritten is not evidence of anything, and the interesting
    -- case is precisely a grade that CHANGED when the method did.
    decision_id   TEXT NOT NULL,
    horizon       TEXT NOT NULL,
    graded_at     TEXT NOT NULL,

    -- What was graded, copied so a cut needs no join and a later change to the
    -- decision cannot retroactively alter the grade's meaning.
    instrument    TEXT,
    direction     TEXT,
    status        TEXT,
    operator_action TEXT,
    thesis_state  TEXT,
    decision_time TEXT,
    horizon_date  TEXT NOT NULL,

    -- The prices, and where each came from.
    reference_price  REAL,
    reference_date   TEXT,
    horizon_price    REAL,
    horizon_price_date TEXT,

    -- The outcome, in the decision's own direction.
    return_pct    REAL,
    return_points REAL,
    -- On CLOSES only. A lower bound on the true excursion; see the docstring.
    mae_close_pct REAL,
    mae_close_date TEXT,

    -- The invalidation, tested the way the register states it: settled close.
    invalidation_text  TEXT,
    invalidation_level REAL,
    invalidation_hit   INTEGER,
    invalidation_date  TEXT,

    -- R, against the DECLARED dollars at risk. NULL when the decision did not
    -- declare enough to compute one -- never a guess.
    risk_per_unit   REAL,
    units           REAL,
    dollars_at_risk REAL,
    -- TWO R's, BECAUSE THEY ANSWER DIFFERENT QUESTIONS and collapsing them would
    -- destroy the one distinction Part 7 grades on.
    --
    --   r_multiple        the THESIS outcome: held to the horizon regardless.
    --   r_multiple_ruled  what a RULE-FOLLOWING operator actually got: -1R when
    --                     the invalidation was touched before the horizon,
    --                     otherwise the same as r_multiple.
    --
    -- The synthetic case that forced this: a long entered at 700 with its
    -- invalidation at 685 closes at 680 on day three and recovers to 735 by the
    -- horizon. The thesis earned +2.33R. The operator who followed his own rule
    -- earned -1R. Reporting only the first says the system is profitable and the
    -- rules are costing money; reporting only the second says the thesis was
    -- wrong when it was right and early. Expectancy must be computed on the
    -- ruled column -- that is the money -- while the gap between the two is the
    -- measurable cost of the invalidation's placement.
    r_multiple      REAL,
    r_multiple_ruled REAL,
    r_basis         TEXT,

    -- The regime variable available today.
    spy_gamma_sign TEXT,

    -- The observations the grade read, so it replays.
    observations_json TEXT NOT NULL,
    price_source   TEXT NOT NULL,
    method_version TEXT NOT NULL,
    PRIMARY KEY (decision_id, horizon, graded_at)
);

CREATE INDEX IF NOT EXISTS grades_by_decision ON grades (decision_id, graded_at);
CREATE INDEX IF NOT EXISTS grades_by_status   ON grades (status, horizon);

CREATE TRIGGER IF NOT EXISTS grades_immutable_update
BEFORE UPDATE ON grades
BEGIN SELECT RAISE(ABORT, 'a grade is immutable; re-grade writes a new row'); END;

CREATE TRIGGER IF NOT EXISTS grades_immutable_delete
BEFORE DELETE ON grades
BEGIN SELECT RAISE(ABORT, 'a grade is immutable; it is the evidence'); END;
"""

# Bumped when the grading METHOD changes, so two grades of one decision are
# comparable only if this matches. Without it a methodology change silently
# mixes two populations in every cut.
METHOD_VERSION = "grader-v1"

_NUM = re.compile(r"(\d[\d,]*(?:\.\d+)?)")
_UNITS = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(share|contract|unit)", re.I)


def _f(v: Any) -> Optional[float]:
    try:
        f = float(str(v).replace(",", ""))
        return None if f != f else f
    except (TypeError, ValueError):
        return None


def level_from(text: Optional[str]) -> Optional[float]:
    """The numeric level in an invalidation sentence, or None.

    The register stores invalidation as PROSE by design -- the mechanism matters,
    not just the number -- so the level is parsed out for the arithmetic and the
    sentence is kept verbatim on the grade row. No number means no invalidation
    test and no R-multiple, reported as such rather than defaulted to zero.
    """
    m = _NUM.search(str(text or ""))
    return _f(m.group(1)) if m else None


def units_from(size: Optional[str]) -> Optional[float]:
    """Units out of a free-text size ("100 shares" -> 100.0)."""
    m = _UNITS.search(str(size or ""))
    if m:
        return _f(m.group(1))
    m = _NUM.search(str(size or ""))
    return _f(m.group(1)) if m else None


class PriceSeries:
    """Settled closes per symbol per session, from the pin log. Read once.

    The pin log is the system's own record of what it saw at the close, written
    by the EOD pass at the time. That is exactly the property a grader needs: it
    is not a price the grader fetched, it is the price the system acted on.
    """

    def __init__(self, path: Optional[str] = None) -> None:
        from . import config  # noqa: PLC0415
        self.path = Path(path or config.PIN_LOG_PATH)
        self.by_symbol: dict[str, list[tuple[str, float]]] = {}
        self.gamma: dict[tuple[str, str], Optional[float]] = {}
        if not self.path.exists():
            return
        with self.path.open(encoding="utf-8", newline="") as fp:
            for r in csv.DictReader(fp):
                sym, day, close = r.get("symbol"), r.get("date"), _f(r.get("close"))
                if not sym or not day or close is None:
                    continue
                self.by_symbol.setdefault(sym, []).append((day, close))
                self.gamma[(sym, day)] = _f(r.get("net_gex"))
        for rows in self.by_symbol.values():
            rows.sort()

    @property
    def source(self) -> str:
        return f"pin_log:{self.path.name}"

    def symbols(self) -> list[str]:
        return sorted(self.by_symbol)

    def at_or_before(self, sym: str, day: str) -> Optional[tuple[str, float]]:
        best = None
        for d, c in self.by_symbol.get(sym, []):
            if d <= day:
                best = (d, c)
            else:
                break
        return best

    def at_or_after(self, sym: str, day: str) -> Optional[tuple[str, float]]:
        for d, c in self.by_symbol.get(sym, []):
            if d >= day:
                return (d, c)
        return None

    def between(self, sym: str, start: str, end: str) -> list[tuple[str, float]]:
        return [(d, c) for d, c in self.by_symbol.get(sym, [])
                if start <= d <= end]

    def last_date(self, sym: str) -> Optional[str]:
        rows = self.by_symbol.get(sym) or []
        return rows[-1][0] if rows else None

    def gamma_sign(self, sym: str, day: str) -> Optional[str]:
        """SPY's gamma sign on a session, from the exposure engine's own row."""
        g = self.gamma.get((sym, day))
        if g is None:
            hit = self.at_or_before(sym, day)
            g = self.gamma.get((sym, hit[0])) if hit else None
        if g is None:
            return None
        return "positive" if g > 0 else ("negative" if g < 0 else "flat")


def horizon_date(decision_time: str, horizon: str) -> Optional[str]:
    days = HORIZON_DAYS.get(horizon)
    if days is None:
        return None
    try:
        d = dt.datetime.fromisoformat(str(decision_time).replace("Z", "+00:00"))
    except ValueError:
        return None
    return (d.date() + dt.timedelta(days=days)).isoformat()


class GradeStore:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = Path(path or observations.DEFAULT_DB)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "GradeStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def already(self, decision_id: str, horizon: str) -> bool:
        """Has this decision been graded at this horizon under this method?"""
        return bool(self.conn.execute(
            "SELECT 1 FROM grades WHERE decision_id = ? AND horizon = ? "
            "  AND method_version = ? LIMIT 1",
            (decision_id, horizon, METHOD_VERSION)).fetchone())

    def write(self, grade: dict) -> None:
        cols = [k for k in grade if k != "_"]
        self.conn.execute(
            f"INSERT OR IGNORE INTO grades ({','.join(cols)}) "
            f"VALUES ({','.join('?' * len(cols))})", [grade[c] for c in cols])
        self.conn.commit()

    def all_grades(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM grades WHERE method_version = ? ORDER BY graded_at",
            (METHOD_VERSION,))]

    def since(self, when: Optional[str]) -> list[dict]:
        if not when:
            return self.all_grades()
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM grades WHERE method_version = ? AND graded_at > ? "
            "ORDER BY graded_at", (METHOD_VERSION, when))]


def grade_one(decision: dict, prices: PriceSeries, *,
              now: Optional[str] = None) -> dict:
    """Grade one decision, or say precisely why it cannot be graded.

    Returns {"graded": bool, "reason": str, "grade": dict|None}. Never raises: a
    grader that dies on one malformed decision grades none of the rest.
    """
    from register import instruments  # noqa: PLC0415

    did = decision["id"]
    horizon = decision.get("horizon")
    inst = decision.get("instrument") or ""
    sym = instruments.normalise(inst)
    today = (now or session.utc_iso())[:10]

    # The ENTRY, from the chain root -- see decisions_to_grade. Falls back to the
    # row's own time for a single-link chain, where they are the same thing.
    entry = (decision.get("entry_decision_time")
             or decision.get("decision_time") or decision.get("created_at"))
    hd = horizon_date(entry, horizon)
    if hd is None:
        return {"graded": False, "decision_id": did,
                "reason": f"no window declared for horizon {horizon!r}"}

    # THE GATE. An unelapsed horizon gets NO ROW. Two separate conditions, and
    # both matter: the date must have passed, AND the price series must actually
    # reach it. A series that stops short cannot grade a horizon inside it just
    # because the calendar has moved on.
    if hd > today:
        return {"graded": False, "decision_id": did,
                "reason": f"horizon {hd} has not elapsed (today {today})"}
    last = prices.last_date(sym)
    if last is None:
        return {"graded": False, "decision_id": did,
                "reason": f"no stored prices for {sym} at all"}
    if last < hd:
        return {"graded": False, "decision_id": did,
                "reason": (f"horizon {hd} elapsed but stored prices for {sym} "
                           f"stop at {last} -- grading it would use a price from "
                           f"before the horizon and call it the horizon price")}

    ref_day = (entry or "")[:10]
    ref = prices.at_or_before(sym, ref_day)
    if ref is None:
        return {"graded": False, "decision_id": did,
                "reason": f"no stored price for {sym} at or before {ref_day}"}
    hp = prices.at_or_after(sym, hd)
    if hp is None:
        return {"graded": False, "decision_id": did,
                "reason": f"no stored price for {sym} at or after {hd}"}

    ref_date, ref_price = ref
    hp_date, hp_price = hp
    direction = (decision.get("direction") or "").lower()
    sign = {"long": 1.0, "short": -1.0}.get(direction)
    if sign is None:
        # flat and hedge have no directional return. Graded for the path and the
        # invalidation, with the return left NULL rather than assigned a sign
        # the decision never claimed.
        sign = 0.0

    path = prices.between(sym, ref_date, hp_date)
    ret_points = (hp_price - ref_price) * sign if sign else None
    ret_pct = (100.0 * ret_points / ref_price
               if ret_points is not None and ref_price else None)

    # MAE on closes, in the decision's direction: the worst close against it.
    mae_pct = mae_date = None
    if sign and path:
        worst = min(path, key=lambda dc: (dc[1] - ref_price) * sign)
        adverse = (worst[1] - ref_price) * sign
        if adverse < 0:
            mae_pct = 100.0 * adverse / ref_price
            mae_date = worst[0]
        else:
            mae_pct, mae_date = 0.0, None

    # The invalidation, on settled closes, BEFORE the horizon -- which is what
    # the register's own wording says and what the stored data supports exactly.
    inv_text = decision.get("invalidation")
    inv_level = level_from(inv_text)
    inv_hit, inv_date = None, None
    if inv_level is not None and sign:
        for d, c in path:
            if d <= ref_date:
                continue
            breached = c < inv_level if sign > 0 else c > inv_level
            if breached:
                inv_hit, inv_date = 1, d
                break
        if inv_hit is None:
            inv_hit = 0

    # R, against the DECLARED dollars at risk. Risk per unit is the distance from
    # the reference price to the invalidation level -- the loss the decision
    # declared it was willing to take -- times the declared units. Anything
    # missing yields NULL and a basis that says which piece was absent, because
    # an invented denominator makes every R in every cut meaningless.
    units = units_from(decision.get("size"))
    risk_per_unit = dollars_at_risk = r_multiple = r_multiple_ruled = None
    if inv_level is None:
        r_basis = "no numeric level in the invalidation"
    elif not sign:
        r_basis = f"direction {direction!r} has no signed risk"
    else:
        risk_per_unit = (ref_price - inv_level) * sign
        if risk_per_unit <= 0:
            r_basis = (f"the invalidation level {inv_level} is not adverse to a "
                       f"{direction} at {ref_price} -- risk per unit would be "
                       f"{risk_per_unit:+.4f}")
            risk_per_unit = None
        elif units is None:
            r_basis = f"no units parsed from size {decision.get('size')!r}"
        else:
            dollars_at_risk = risk_per_unit * units
            r_multiple = (ret_points * units) / dollars_at_risk
            # The ruled R: an operator who honours his own invalidation is out at
            # -1R the day it is touched, whatever the price does afterwards.
            r_multiple_ruled = -1.0 if inv_hit else r_multiple
            r_basis = (f"({ref_price} - {inv_level}) x {units} units "
                       f"= {dollars_at_risk:.2f} at risk")

    obs = {
        "reference": {"symbol": sym, "date": ref_date, "close": ref_price},
        "horizon": {"symbol": sym, "date": hp_date, "close": hp_price},
        "path_closes": [{"date": d, "close": c} for d, c in path],
        "gamma_row": {"symbol": sym, "date": ref_date},
    }

    return {"graded": True, "decision_id": did, "reason": "", "grade": {
        "decision_id": did,
        "horizon": horizon,
        "graded_at": now or session.utc_iso(),
        "instrument": inst,
        "direction": direction,
        "status": decision.get("status"),
        "operator_action": decision.get("operator_action"),
        "thesis_state": decision.get("thesis_state"),
        "decision_time": entry,
        "horizon_date": hd,
        "reference_price": ref_price,
        "reference_date": ref_date,
        "horizon_price": hp_price,
        "horizon_price_date": hp_date,
        "return_pct": ret_pct,
        "return_points": ret_points,
        "mae_close_pct": mae_pct,
        "mae_close_date": mae_date,
        "invalidation_text": inv_text,
        "invalidation_level": inv_level,
        "invalidation_hit": inv_hit,
        "invalidation_date": inv_date,
        "risk_per_unit": risk_per_unit,
        "units": units,
        "dollars_at_risk": dollars_at_risk,
        "r_multiple": r_multiple,
        "r_multiple_ruled": r_multiple_ruled,
        "r_basis": r_basis,
        "spy_gamma_sign": prices.gamma_sign("SPY", ref_date),
        "observations_json": json.dumps(obs, sort_keys=True),
        "price_source": prices.source,
        "method_version": METHOD_VERSION,
    }}


def decisions_to_grade(db_path: Optional[str] = None) -> list[dict]:
    """Every register record -- taken, declined and draft alike.

    ONE ROW PER CHAIN, and the chain's live head is the row. Grading each link
    would count one position three times in every cut: the SPY long is four rows
    (a draft, its promotion, the INVALIDATED marking, the re-designation) and it
    is one decision about one position.

    THE ENTRY TIME COMES FROM THE CHAIN'S ROOT, NOT THE HEAD. This is the part
    that is easy to get wrong and silently wrecks every number downstream. A
    supersession stamps `decision_time` with the moment of the SUPERSESSION, so
    the head of the SPY chain carries 19 September -- the day its instrument was
    re-designated -- while the position was actually entered on the 5th. Grading
    from the head's timestamp would take the reference price from a fortnight
    after entry, measure the return from there, and report a fourteen-day-old
    position as a fresh one. So the root's decision_time is walked back to and
    used as the entry, while the head supplies the status, the thesis state and
    the invalidation as they finally stood.
    """
    from register import store as reg_store  # noqa: PLC0415
    conn = sqlite3.connect(db_path or reg_store.DEFAULT_DB)
    conn.row_factory = sqlite3.Row
    try:
        try:
            rows = [dict(r) for r in conn.execute("SELECT * FROM decisions")]
        except sqlite3.OperationalError:
            return []
    finally:
        conn.close()

    by_id = {r["id"]: r for r in rows}
    # successor -> predecessor, from the pointer the older row carries.
    pred = {r["superseded_by"]: r["id"] for r in rows if r.get("superseded_by")}

    out = []
    for head in (r for r in rows if not r.get("superseded_by")):
        root = head
        seen = {root["id"]}
        while pred.get(root["id"]) and pred[root["id"]] not in seen:
            root = by_id[pred[root["id"]]]
            seen.add(root["id"])
        graded = dict(head)
        graded["entry_decision_time"] = (root.get("decision_time")
                                         or root.get("created_at"))
        graded["chain_root_id"] = root["id"]
        graded["chain_length"] = len(seen)
        out.append(graded)
    return sorted(out, key=lambda r: r.get("entry_decision_time") or "")


def run(db_path: Optional[str] = None, *, now: Optional[str] = None,
        pin_log: Optional[str] = None, dry_run: bool = False) -> dict:
    """Grade everything gradeable. Returns what happened, per decision."""
    prices = PriceSeries(pin_log)
    rows = decisions_to_grade(db_path)
    graded, skipped = [], []
    with GradeStore(db_path) as store:
        for d in rows:
            if store.already(d["id"], d.get("horizon") or ""):
                skipped.append({"decision_id": d["id"],
                                "reason": "already graded at this horizon "
                                          "under " + METHOD_VERSION})
                continue
            res = grade_one(d, prices, now=now)
            if not res["graded"]:
                skipped.append(res)
                continue
            if not dry_run:
                store.write(res["grade"])
            graded.append(res["grade"])
    return {"considered": len(rows), "graded": graded, "skipped": skipped,
            "price_source": prices.source, "symbols": prices.symbols(),
            "method_version": METHOD_VERSION, "dry_run": dry_run}


def main() -> int:
    import argparse  # noqa: PLC0415
    import sys       # noqa: PLC0415
    ap = argparse.ArgumentParser(description="Grade the register")
    ap.add_argument("--db", default=None)
    ap.add_argument("--pin-log", default=None)
    ap.add_argument("--as-of", default=None,
                    help="grade as if it were this instant (testing)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    res = run(args.db, now=args.as_of, pin_log=args.pin_log,
              dry_run=args.dry_run)
    line = "=" * 78
    print(f"{line}\nGrading the register -- {res['method_version']}\n{line}")
    print(f"  price source : {res['price_source']}  "
          f"({len(res['symbols'])} symbols)")
    print(f"  considered   : {res['considered']} live decision(s)")
    print(f"  graded       : {len(res['graded'])}"
          + ("  (dry run -- nothing written)" if res["dry_run"] else ""))
    for g in res["graded"]:
        r = g["r_multiple"]
        print(f"    {g['decision_id'][:8]} {g['instrument']:16} "
              f"{g['status']:8} {g['horizon']:10} "
              f"ret {g['return_pct'] if g['return_pct'] is None else round(g['return_pct'], 2)}%"
              f"  R {'n/a' if r is None else round(r, 2)}"
              f"  inval_hit {g['invalidation_hit']}")
    if res["skipped"]:
        print(f"  not graded   : {len(res['skipped'])}")
        for s in res["skipped"]:
            print(f"    {s['decision_id'][:8]}  {s['reason']}")
    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
